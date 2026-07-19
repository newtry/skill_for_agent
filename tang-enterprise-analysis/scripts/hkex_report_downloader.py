#!/usr/bin/env python3
"""Download HKEX listed-company annual reports from HKEXnews.

The public title-search page currently uses a JSONP security lookup followed by
an HTML form POST. Endpoint changes raise explicit errors instead of returning
an empty result that could be mistaken for "no filings".
"""

import argparse
import json
import os
import re
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urljoin

import requests


class HKEXError(RuntimeError):
    """Raised when HKEX lookup, search, or download responses are invalid."""


class _PdfLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href and re.search(r"\.pdf(?:$|\?)", href, re.IGNORECASE):
            self._href = href
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            title = re.sub(r"\s+", " ", " ".join(self._text)).strip()
            self.links.append((self._href, title))
            self._href = None
            self._text = []


class HKEXReportDownloader:
    BASE_URL = "https://www1.hkexnews.hk"
    TITLE_SEARCH_URL = f"{BASE_URL}/search/titlesearch.xhtml?lang=en"
    PREFIX_URL = f"{BASE_URL}/search/prefix.do"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/124 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        "Referer": TITLE_SEARCH_URL,
    }

    def __init__(self, download_dir="./hkex_reports", session=None):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.session = session or requests.Session()
        self.session.headers.update(self.HEADERS)
        self._initialized = False

    @staticmethod
    def normalize_code(stock_code):
        value = re.sub(r"\D", "", str(stock_code))
        if not value or len(value) > 5:
            raise ValueError("港股代码必须是1至5位数字")
        return value.zfill(5)

    def _initialize_session(self):
        if self._initialized:
            return
        response = self.session.get(self.TITLE_SEARCH_URL, timeout=30)
        response.raise_for_status()
        if "Listed Company Information Title Search" not in response.text:
            raise HKEXError("港交所标题检索页返回结构异常")
        self._initialized = True

    def lookup_stock(self, stock_code):
        """Resolve a five-digit stock code to HKEX's internal stockId."""
        code = self.normalize_code(stock_code)
        self._initialize_session()
        response = self.session.get(
            self.PREFIX_URL,
            params={
                "lang": "EN",
                "type": "A",
                "name": code,
                "market": "SEHK",
                "callback": "callback",
            },
            timeout=30,
        )
        response.raise_for_status()
        match = re.fullmatch(r"\s*callback\((.*)\);\s*", response.text, re.DOTALL)
        if not match:
            raise HKEXError("港交所股票代码接口返回的JSONP结构异常")
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise HKEXError("港交所股票代码接口返回无效JSON") from exc
        candidates = payload.get("stockInfo")
        if not isinstance(candidates, list):
            raise HKEXError("港交所股票代码接口缺少stockInfo")
        exact = [item for item in candidates if item.get("code") == code]
        if not exact:
            return None
        item = exact[0]
        if not isinstance(item.get("stockId"), int):
            raise HKEXError("港交所股票记录缺少有效stockId")
        return {
            "stock_id": item["stockId"],
            "code": code,
            "name": item.get("name") or code,
        }

    @staticmethod
    def _format_date(value):
        if isinstance(value, datetime):
            value = value.date()
        if isinstance(value, date):
            return value.strftime("%Y%m%d")
        text = re.sub(r"\D", "", str(value))
        if len(text) != 8:
            raise ValueError("日期必须为YYYYMMDD或date对象")
        datetime.strptime(text, "%Y%m%d")
        return text

    def search_announcements(
        self,
        stock_code,
        from_date,
        to_date,
        title_keyword="annual report",
    ):
        """Search HKEXnews and return structured PDF announcement records."""
        stock = self.lookup_stock(stock_code)
        if stock is None:
            return []
        start = self._format_date(from_date)
        end = self._format_date(to_date)
        if start > end:
            raise ValueError("开始日期不能晚于结束日期")
        response = self.session.post(
            self.TITLE_SEARCH_URL,
            data={
                "lang": "EN",
                "category": "0",
                "market": "SEHK",
                "searchType": "0",
                "documentType": "-1",
                "t1code": "-2",
                "t2Gcode": "-2",
                "t2code": "-2",
                "stockId": str(stock["stock_id"]),
                "from": start,
                "to": end,
                "title": title_keyword,
            },
            timeout=60,
        )
        response.raise_for_status()
        if "Total records found" not in response.text:
            raise HKEXError("港交所标题检索结果结构异常")
        parser = _PdfLinkParser()
        parser.feed(response.text)
        results = []
        seen = set()
        for href, title in parser.links:
            url = urljoin(self.BASE_URL, href)
            if url in seen:
                continue
            seen.add(url)
            path_match = re.search(
                r"/sehk/(\d{4})/(\d{4})/(\d+)\.pdf", href, re.IGNORECASE
            )
            published_at = None
            if path_match:
                published_at = f"{path_match.group(1)}-{path_match.group(2)[:2]}-{path_match.group(2)[2:]}"
            year_match = re.search(r"(?:annual report\s*)?(20\d{2})", title, re.I)
            results.append(
                {
                    **stock,
                    "title": title,
                    "report_year": int(year_match.group(1)) if year_match else None,
                    "published_at": published_at,
                    "url": url,
                }
            )
        return results

    def search_annual_reports(self, stock_code, years):
        years = sorted({int(year) for year in years})
        if not years:
            raise ValueError("至少提供一个报告年份")
        start = date(min(years) + 1, 1, 1)
        end_year = max(years) + 1
        end = min(date(end_year, 12, 31), date.today())
        records = self.search_announcements(
            stock_code, start, end, title_keyword="annual report"
        )
        matches = [record for record in records if record["report_year"] in years]
        selected = []
        for year in years:
            year_records = [record for record in matches if record["report_year"] == year]
            if not year_records:
                continue

            def preference(record):
                normalized = re.sub(r"\s+", " ", record["title"]).strip().casefold()
                exact = bool(
                    re.fullmatch(
                        rf"(?:annual report(?: and accounts)? {year}|"
                        rf"{year} annual report(?: and accounts)?)",
                        normalized,
                    )
                )
                penalty = sum(
                    phrase in normalized
                    for phrase in ("form 20-f", "employee share", "summary")
                )
                return (
                    exact,
                    -penalty,
                    self._remote_pdf_size(record["url"]),
                    -len(normalized),
                )

            selected.append(max(year_records, key=preference))
        return selected

    def _remote_pdf_size(self, url):
        try:
            response = self.session.head(
                url, timeout=30, allow_redirects=True
            )
            response.raise_for_status()
            if "pdf" not in response.headers.get("Content-Type", "").lower():
                return 0
            return int(response.headers.get("Content-Length", 0))
        except (requests.RequestException, TypeError, ValueError):
            return 0

    @staticmethod
    def _safe_filename(value):
        return re.sub(r"[<>:\"/\\|?*]+", "_", value).strip(" .")

    def _download_pdf(self, url, filepath):
        response = self.session.get(url, timeout=180, stream=True)
        response.raise_for_status()
        chunks = response.iter_content(chunk_size=64 * 1024)
        first_chunk = next(chunks, b"")
        content_type = response.headers.get("Content-Type", "").lower()
        if not first_chunk.startswith(b"%PDF") and "pdf" not in content_type:
            raise HKEXError(f"下载内容不是PDF: {url}")
        temporary = filepath.with_suffix(filepath.suffix + ".part")
        try:
            with temporary.open("wb") as handle:
                handle.write(first_chunk)
                for chunk in chunks:
                    if chunk:
                        handle.write(chunk)
            os.replace(temporary, filepath)
        finally:
            if temporary.exists():
                temporary.unlink()

    def download_annual_reports(self, stock_code, years, output_dir=None):
        output = Path(output_dir) if output_dir else self.download_dir
        output.mkdir(parents=True, exist_ok=True)
        downloaded = []
        for record in self.search_annual_reports(stock_code, years):
            filename = self._safe_filename(
                f"{record['code']}_{record['name']}_{record['report_year']}_annual_report.pdf"
            )
            filepath = output / filename
            if not filepath.exists():
                self._download_pdf(record["url"], filepath)
            downloaded.append({**record, "path": str(filepath)})
        return downloaded


def _parse_years(value: str) -> List[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def main():
    parser = argparse.ArgumentParser(description="Download annual reports from HKEXnews")
    parser.add_argument("stock", help="HKEX stock code, for example 00700")
    parser.add_argument(
        "--years",
        type=_parse_years,
        default=[date.today().year - 1],
        help="Comma-separated report years",
    )
    parser.add_argument("--output-dir", default="./hkex_reports")
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args()

    downloader = HKEXReportDownloader(args.output_dir)
    if args.list_only:
        records = downloader.search_annual_reports(args.stock, args.years)
    else:
        records = downloader.download_annual_reports(args.stock, args.years)
    print(json.dumps(records, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
