#!/usr/bin/env python3
"""Extract candidate financial data from A-share and HKEX annual-report PDFs."""

import json
import os
import re
import glob
from datetime import datetime
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("请先安装: pip install pdfplumber")
    raise


MAPPING_PATH = Path(__file__).parent.parent / "references" / "hkfrs_field_mapping.json"
with MAPPING_PATH.open(encoding="utf-8") as mapping_file:
    FINANCIAL_FIELD_MAPPING = json.load(mapping_file)


class PDFReportExtractor:
    """PDF年报候选数据提取器。

    输出必须对照原始报表复核，不应直接进入估值模型。
    """

    UNIT_SCALES = {
        "元": 1,
        "千元": 1_000,
        "万元": 10_000,
        "百万元": 1_000_000,
        "thousand": 1_000,
        "million": 1_000_000,
        "billion": 1_000_000_000,
    }

    def __init__(
        self,
        pdf_path,
        max_pages=None,
        reporting_currency=None,
        page_numbers=None,
    ):
        self.pdf_path = pdf_path
        self.filename = os.path.basename(pdf_path)
        self.default_currency = reporting_currency
        self.detected_currencies = set()
        self.text = ""
        self.tables = []
        self.sources = {}
        self.warnings = []
        self._load_pdf(max_pages=max_pages, page_numbers=page_numbers)

    @classmethod
    def _page_needs_text_table(cls, page_text):
        normalized = cls._normalize(page_text)
        titles = []
        for config in FINANCIAL_FIELD_MAPPING["statements"].values():
            titles.extend(config["titles"])
        share_aliases = [
            alias
            for aliases in FINANCIAL_FIELD_MAPPING["shares"].values()
            for alias in aliases
        ]
        return any(cls._normalize(item) in normalized for item in [*titles, *share_aliases])

    @classmethod
    def _table_has_labels(cls, table):
        aliases = []
        for config in FINANCIAL_FIELD_MAPPING["statements"].values():
            for key, field_aliases in config["fields"].items():
                aliases.extend([key, *field_aliases])
        for key, field_aliases in FINANCIAL_FIELD_MAPPING["shares"].items():
            aliases.extend([key, *field_aliases])
        normalized_aliases = {
            cls._normalize(alias) for alias in aliases if len(cls._normalize(alias)) >= 4
        }
        for row in table:
            text = " ".join(str(cell or "") for cell in row)
            normalized = cls._normalize(text)
            has_number = any(cls._numbers_from_cell(cell) for cell in row)
            if has_number and any(alias in normalized for alias in normalized_aliases):
                return True
        return False

    def _load_pdf(self, max_pages=None, page_numbers=None):
        """加载PDF并提取文本"""
        selected_pages = set(page_numbers or [])
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                if max_pages is not None and i >= max_pages:
                    break
                if selected_pages and (i + 1) not in selected_pages:
                    continue
                page_text = page.extract_text()
                if page_text:
                    self.text += page_text + "\n"

                tables = page.extract_tables()
                if (
                    self._page_needs_text_table(page_text or "")
                    and not any(self._table_has_labels(table) for table in tables)
                ):
                    tables = page.extract_tables(
                        {
                            "vertical_strategy": "text",
                            "horizontal_strategy": "text",
                            "snap_tolerance": 5,
                            "join_tolerance": 5,
                        }
                    )
                for table in tables:
                    if table and len(table) > 1:
                        self.tables.append({
                            "page": i + 1,
                            "page_text": page_text or "",
                            "data": table,
                        })

        self.text = self.text.replace("\n", " ")

    @staticmethod
    def _normalize(value):
        text = str(value or "").casefold().replace("’", "'").replace("&", "and")
        return re.sub(r"[\s:：,，.。;；()（）\[\]{}\-_/]+", "", text)

    @staticmethod
    def _parse_number(value):
        text = str(value or "").strip()
        if not text or text in {"-", "—", "--", "不适用"}:
            return None
        negative = text.startswith("(") or text.endswith(")")
        if negative:
            text = text.strip("()")
        text = re.sub(
            r"(?i)(?:rmb|cny|hk\$|hkd|us\$|usd|gbp|£|￥|¥)", "", text
        )
        text = text.strip()
        if not re.fullmatch(
            r"-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", text
        ):
            return None
        text = text.replace(",", "")
        try:
            number = float(text)
            return -number if negative else number
        except ValueError:
            return None

    @classmethod
    def _numbers_from_cell(cls, value):
        direct = cls._parse_number(value)
        if direct is not None:
            return [direct]
        text = str(value or "")
        tokens = re.findall(
            r"\(?-?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?|\(?-?\d+(?:\.\d+)?\)?",
            text,
        )
        numbers = []
        for token in tokens:
            number = cls._parse_number(token)
            if number is not None:
                numbers.append(number)
        return numbers

    def _table_unit(self, record):
        context = record["page_text"] + " " + str(record["data"][:3])
        currency = self._detect_currency(context)
        chinese_matches = re.findall(
            r"单位\s*[：:]\s*(?:人民币)?\s*(百万元|万元|千元|元)",
            context,
        )
        unit = None
        scale = None
        if chinese_matches:
            unit = chinese_matches[-1]
            scale = self.UNIT_SCALES[unit]
            currency = currency or "CNY"
        else:
            currency_token = r"(?:rmb|cny|hk\$|hkd|us\s*\$|usd|gbp|£|\$)"
            unit_token = r"(billions?|bn|millions?|mn|m|thousands?|000s?|000)"
            separator = r"\s*['’＊*·]?\s*"
            english_patterns = (
                rf"(?i)(?:expressed|amounts?)?\s*in\s+"
                rf"(?:{currency_token}{separator})?{unit_token}",
                rf"(?i){currency_token}{separator}{unit_token}\b",
            )
            unit_match = None
            for pattern in english_patterns:
                matches = re.findall(pattern, context)
                if matches:
                    unit_match = matches[-1].casefold()
                    break
            if unit_match:
                if unit_match.startswith(("billion", "bn")):
                    unit, scale = "billion", self.UNIT_SCALES["billion"]
                elif unit_match.startswith(("million", "mn", "m")):
                    unit, scale = "million", self.UNIT_SCALES["million"]
                else:
                    unit, scale = "thousand", self.UNIT_SCALES["thousand"]

        currency = currency or getattr(self, "default_currency", None)
        if unit is not None:
            confidence = "high" if currency else "medium"
            if currency:
                if not hasattr(self, "detected_currencies"):
                    self.detected_currencies = set()
                self.detected_currencies.add(currency)
            else:
                self._add_warning(
                    f"第{record['page']}页识别到金额单位但未识别报告币种"
                )
            return unit, scale, currency or "UNKNOWN", confidence
        warning = f"第{record['page']}页未识别金额单位，暂按元换算，必须人工复核"
        self._add_warning(warning)
        return "未识别（暂按基本单位）", 1, currency or "UNKNOWN", "low"

    @staticmethod
    def _detect_currency(context):
        patterns = (
            ("CNY", r"(?i)人民币|\brmb\b|\bcny\b"),
            ("HKD", r"(?i)港币|港元|hk\$|\bhkd\b"),
            ("USD", r"(?i)美元|us\s*\$|\busd\b|u\.s\.\s*dollars?"),
            ("GBP", r"(?i)英镑|\bgbp\b|£"),
        )
        for currency, pattern in patterns:
            if re.search(pattern, context):
                return currency
        return None

    def _add_warning(self, warning):
        if warning not in self.warnings:
            self.warnings.append(warning)

    @classmethod
    def _match_key(cls, item_name, fields):
        normalized = re.sub(r"^\d+", "", cls._normalize(item_name))
        candidates = []
        for key, aliases in fields.items():
            for alias in [key, *aliases]:
                normalized_alias = cls._normalize(alias)
                if normalized == normalized_alias:
                    return key
                if len(normalized_alias) >= 4 and normalized_alias in normalized:
                    candidates.append((len(normalized_alias), key))
        return max(candidates)[1] if candidates else None

    def _row_value(self, row):
        candidates = []
        for cell in row:
            candidates.extend(self._numbers_from_cell(cell))
        if not candidates:
            return None
        while (
            len(candidates) >= 2
            and abs(candidates[0]) < 1000
            and max(abs(value) for value in candidates[1:])
            > max(abs(candidates[0]) * 100, 1000)
        ):
            candidates.pop(0)
        return candidates[0]

    def _extract_statement(self, statement):
        config = FINANCIAL_FIELD_MAPPING["statements"][statement]
        fields = config["fields"]
        titles = [self._normalize(title) for title in config["titles"]]
        signatures = [self._normalize(item) for item in config["signatures"]]
        data = {key: None for key in fields}
        self.sources[statement] = {}
        for record in self.tables:
            table = record["data"]
            context = self._normalize(record["page_text"] + str(table))
            if titles and not any(title in context for title in titles):
                continue
            if signatures and not any(sig in context for sig in signatures):
                continue
            unit, scale, currency, confidence = self._table_unit(record)
            for row in table:
                if not row or len(row) < 2:
                    continue
                item_name = " ".join(str(cell or "") for cell in row)
                key = self._match_key(item_name, fields)
                if key is None or data[key] is not None:
                    continue
                row_numbers = [
                    number
                    for cell in row
                    for number in self._numbers_from_cell(cell)
                ]
                if len(self._normalize(item_name)) > 100 and len(row_numbers) < 2:
                    continue
                value = self._row_value(row)
                if value is None:
                    continue
                normalized_value = value * scale / 100_000_000
                if key in {
                    "营业成本",
                    "销售费用",
                    "管理费用",
                    "研发费用",
                    "财务费用",
                    "利息费用",
                }:
                    normalized_value = abs(normalized_value)
                data[key] = normalized_value
                self.sources[statement][key] = {
                    "page": record["page"],
                    "source_unit": unit,
                    "currency": currency,
                    "normalized_unit": f"1e8 {currency}",
                    "period_column": "首个可识别本期数，需复核表头",
                    "confidence": confidence,
                }
        return data

    def extract_composite_balance_sheet(self):
        """
        提取合并资产负债表数据
        返回单位：报告币种的1亿元
        """
        return self._extract_statement("资产负债表")
    
    def extract_composite_income_statement(self):
        """
        提取合并利润表数据
        返回单位：报告币种的1亿元
        """
        data = self._extract_statement("利润表")
        if data["毛利润"] is None:
            if data["营业收入"] is not None and data["营业成本"] is not None:
                data["毛利润"] = data["营业收入"] - data["营业成本"]
                self.sources["利润表"]["毛利润"] = {
                    "kind": "calculated",
                    "formula": "营业收入 - 营业成本",
                    "normalized_unit": "1e8 reporting currency",
                    "confidence": "medium",
                }
        if data["营业收入"] is None:
            if data["毛利润"] is not None and data["营业成本"] is not None:
                data["营业收入"] = data["毛利润"] + data["营业成本"]
                self.sources["利润表"]["营业收入"] = {
                    "kind": "calculated",
                    "formula": "毛利润 + 营业成本",
                    "normalized_unit": "1e8 reporting currency",
                    "confidence": "medium",
                }
        return data
    
    def extract_composite_cash_flow(self):
        """
        提取合并现金流量表数据
        返回单位：报告币种的1亿元
        """
        return self._extract_statement("现金流量表")

    def extract_financial_institution_data(self):
        """Extract HKFRS bank/financial-institution line items when present."""
        return self._extract_statement("金融企业指标")

    @staticmethod
    def _share_scale(record):
        context = record["page_text"] + " " + str(record["data"][:3])
        if re.search(
            r"(?i)(?:million shares|shares\s+in\s+millions|"
            r"number\s+of\s+shares\s*\(?\s*millions?\s*\)?|\(millions?\))",
            context,
        ):
            return "million shares", 1_000_000, "high"
        if re.search(
            r"(?i)(?:thousand shares|shares\s+in\s+thousands|"
            r"number\s+of\s+shares\s*\(?\s*thousands?\s*\)?|"
            r"['’]000\s*shares|shares\s*['’]000|\(thousands?\))",
            context,
        ):
            return "thousand shares", 1_000, "high"
        return "shares", 1, "low"

    def extract_share_data(self):
        fields = FINANCIAL_FIELD_MAPPING["shares"]
        data = {key: None for key in fields}
        self.sources["股份口径"] = {}
        for record in self.tables:
            unit, scale, confidence = self._share_scale(record)
            for row in record["data"]:
                if not row or len(row) < 2:
                    continue
                row_text = " ".join(str(cell or "") for cell in row)
                key = self._match_key(row_text, fields)
                if key is None or data[key] is not None:
                    continue
                value = self._row_value(row)
                if value is None:
                    continue
                data[key] = value * scale
                self.sources["股份口径"][key] = {
                    "page": record["page"],
                    "source_unit": unit,
                    "normalized_unit": "shares",
                    "period_column": "首个可识别本期数，需复核表头",
                    "confidence": confidence,
                }

            context = self._normalize(record["page_text"])
            if "basicanddilutedearningspershare" in context:
                for row in record["data"]:
                    row_text = " ".join(str(cell or "") for cell in row)
                    normalized_row = self._normalize(row_text)
                    numbers = []
                    for cell in row:
                        numbers.extend(self._numbers_from_cell(cell))
                    if numbers and numbers[0] == 1:
                        numbers.pop(0)
                    if normalized_row.startswith("basic") and len(numbers) >= 2:
                        data["加权平均股份"] = numbers[1] * scale
                        self.sources["股份口径"]["加权平均股份"] = {
                            "page": record["page"],
                            "source_unit": unit,
                            "normalized_unit": "shares",
                            "period_column": "EPS表本期加权平均股份，需复核表头",
                            "confidence": confidence,
                        }
                    elif normalized_row.startswith("diluted") and len(numbers) >= 2:
                        data["稀释加权平均股份"] = numbers[1] * scale
                        self.sources["股份口径"]["稀释加权平均股份"] = {
                            "page": record["page"],
                            "source_unit": unit,
                            "normalized_unit": "shares",
                            "period_column": "EPS表本期稀释加权平均股份，需复核表头",
                            "confidence": confidence,
                        }

            text = re.sub(r"\s+", " ", record["page_text"])
            text_patterns = {
                "加权平均股份": (
                    r"weighted average number of ordinary shares"
                    r"(?: in issue| outstanding)"
                    r"(?:(?!diluted).){0,320}?"
                    r"\((million shares|millions?|thousands?|['’]000 shares)\)"
                    r"\s*([\d,]+)"
                ),
                "稀释加权平均股份": (
                    r"weighted average number of ordinary shares"
                    r"(?:(?!weighted average).){0,260}?"
                    r"(?:diluted eps|diluted earnings per share)"
                    r"\s*\((million shares|millions?|thousands?|['’]000 shares)\)"
                    r"\s*([\d,]+)"
                ),
            }
            for key, pattern in text_patterns.items():
                if data[key] is not None:
                    continue
                match = re.search(pattern, text, re.IGNORECASE)
                if not match:
                    continue
                unit_text = match.group(1).casefold()
                if unit_text.startswith("million"):
                    source_unit, text_scale = "million shares", 1_000_000
                else:
                    source_unit, text_scale = "thousand shares", 1_000
                value = self._parse_number(match.group(2))
                if value is None:
                    continue
                data[key] = value * text_scale
                self.sources["股份口径"][key] = {
                    "page": record["page"],
                    "source_unit": source_unit,
                    "normalized_unit": "shares",
                    "period_column": "同页文本中的首个本期数，需复核表头",
                    "confidence": "medium",
                }

            if "basicanddilutedearningspershare" in context:
                eps_patterns = {
                    "加权平均股份": r"\bbasic1?\s+([\d,]+)\s+([\d,]+)",
                    "稀释加权平均股份": r"\bdiluted1?\s+([\d,]+)\s+([\d,]+)",
                }
                for key, pattern in eps_patterns.items():
                    if data[key] is not None:
                        continue
                    match = re.search(pattern, text, re.IGNORECASE)
                    if not match:
                        continue
                    value = self._parse_number(match.group(2))
                    if value is None:
                        continue
                    data[key] = value * scale
                    self.sources["股份口径"][key] = {
                        "page": record["page"],
                        "source_unit": unit,
                        "normalized_unit": "shares",
                        "period_column": "EPS表本期加权平均股份，需复核表头",
                        "confidence": "medium",
                    }
        return data
    
    def extract_business_segments(self):
        """
        提取业务分部信息（按产品、渠道、地区）
        返回单位：亿元
        """
        segments = {
            "按产品": [],
            "按渠道": [],
            "按地区": []
        }
        
        for record in self.tables:
            table = record["data"]
            if not table or len(table) < 2:
                continue
            
            table_str = str(table)
            
            if "茅台酒" in table_str and "系列酒" in table_str:
                for row in table[1:]:
                    if not row or len(row) < 2:
                        continue
                    name = str(row[0]) if row[0] else ""
                    name = re.sub(r"\s+", "", name)
                    if name in ["茅台酒", "其他系列酒", "小计"]:
                        try:
                            revenue = float(str(row[1]).replace(",", "")) if row[1] else 0
                            cost = float(str(row[3]).replace(",", "")) if row[3] else 0
                            gross_margin = float(str(row[5]).replace("%", "")) if row[5] else 0
                            segments["按产品"].append({
                                "名称": name,
                                "营业收入": revenue / 10000 / 10000,
                                "营业成本": cost / 10000 / 10000,
                                "毛利率": gross_margin
                            })
                        except:
                            continue
            
            if "批发代理" in table_str and "直销" in table_str:
                if not segments["按渠道"]:
                    for row in table[1:]:
                        if not row or len(row) < 6:
                            continue
                        name = str(row[0]) if row[0] else ""
                        name = re.sub(r"\s+", "", name)
                        if name in ["批发代理", "直销", "小计"]:
                            try:
                                revenue = float(str(row[1]).replace(",", "")) if row[1] else 0
                                gross_margin_str = str(row[5]) if row[5] else "0"
                                gross_margin = float(gross_margin_str.replace("%", "")) if gross_margin_str else 0
                                if gross_margin > 50:
                                    cost = float(str(row[3]).replace(",", "")) if row[3] else 0
                                    segments["按渠道"].append({
                                        "名称": name,
                                        "营业收入": revenue / 10000 / 10000,
                                        "营业成本": cost / 10000 / 10000,
                                        "毛利率": gross_margin
                                    })
                            except:
                                continue
            
            if "国内" in table_str and "国外" in table_str and "小计" in table_str:
                for row in table[1:]:
                    if not row or len(row) < 2:
                        continue
                    name = str(row[0]) if row[0] else ""
                    name = re.sub(r"\s+", "", name)
                    if name in ["国内", "国外", "小计"]:
                        try:
                            revenue = float(str(row[1]).replace(",", "")) if row[1] else 0
                            cost = float(str(row[3]).replace(",", "")) if row[3] else 0
                            gross_margin = float(str(row[5]).replace("%", "")) if row[5] else 0
                            segments["按地区"].append({
                                "名称": name,
                                "营业收入": revenue / 10000 / 10000,
                                "营业成本": cost / 10000 / 10000,
                                "毛利率": gross_margin
                            })
                        except:
                            continue
        
        for key in segments:
            segments[key] = [s for s in segments[key] if s["名称"] != "小计"]
        
        return segments
    
    def extract_all_data(self):
        """提取所有数据"""
        balance = self.extract_composite_balance_sheet()
        income = self.extract_composite_income_statement()
        cashflow = self.extract_composite_cash_flow()
        financial_institution = self.extract_financial_institution_data()
        shares = self.extract_share_data()
        segments = self.extract_business_segments()
        
        return {
            "资产负债表": balance,
            "利润表": income,
            "现金流量表": cashflow,
            "金融企业指标": financial_institution,
            "股份口径": shares,
            "业务分部": segments,
            "提取元数据": {
                "source_file": self.filename,
                "sources": self.sources,
                "reporting_currencies": sorted(
                    getattr(self, "detected_currencies", set())
                ),
                "amount_unit": "1e8 reporting currency",
                "share_unit": "shares",
                "warnings": self.warnings,
                "status": "candidate_data_requires_manual_verification",
            },
        }


def find_reports(reports_dir, stock_name=None):
    """查找报告文件"""
    reports = []
    pattern = os.path.join(reports_dir, "*.pdf")
    
    for filepath in glob.glob(pattern):
        filename = os.path.basename(filepath)
        
        if stock_name and stock_name not in filename:
            continue
        
        year_match = re.search(r"(20\d{2})(?:年|_annual_report)", filename, re.I)
        if not year_match:
            year_match = re.search(r"(20\d{2})", filename)
        year = int(year_match.group(1)) if year_match else None
        
        report_type = "年度"
        if "半年度" in filename or "半年" in filename or "第2" in filename:
            report_type = "半年报"
        elif "季度" in filename or "第" in filename:
            if "第1" in filename or "一季度" in filename:
                report_type = "一季度"
            elif "第3" in filename or "三季度" in filename:
                report_type = "三季度"
        
        reports.append({
            "path": filepath,
            "filename": filename,
            "year": year,
            "type": report_type,
            "type_order": 0 if report_type == "年度" else (3 if "三季度" in report_type else (2 if "半年" in report_type else (1 if "一季度" in report_type else 0)))
        })
    
    reports.sort(key=lambda x: (x["year"] or 0, x["type_order"]), reverse=True)
    return reports


def load_company_financial_data(reports_dir, stock_name, max_years=5):
    """
    加载企业多年财务数据
    
    Args:
        reports_dir: 报告目录
        stock_name: 企业名称（如"贵州茅台"）
        max_years: 最多加载多少年数据
    
    Returns:
        dict: 按年份组织的财务数据
    """
    reports = find_reports(reports_dir, stock_name)
    
    annual_reports = [r for r in reports if r["type"] == "年度"]
    quarterly_reports = [r for r in reports if r["type"] != "年度"]
    
    financial_data = {}
    
    for report in annual_reports[:max_years]:
        year = report["year"]
        if not year:
            continue
        
        print(f"正在提取 {report['filename']} ...")
        
        try:
            extractor = PDFReportExtractor(report["path"])
            data = extractor.extract_all_data()
            financial_data[str(year)] = data
            print(f"  ✓ 完成 {year}年数据提取")
        except Exception as e:
            print(f"  ✗ {report['filename']} 提取失败: {e}")
    
    if quarterly_reports:
        latest_quarterly = quarterly_reports[0]
        print(f"正在提取最新季报 {latest_quarterly['filename']} ...")
        try:
            extractor = PDFReportExtractor(latest_quarterly["path"])
            data = extractor.extract_all_data()
            year_key = f"{latest_quarterly['year']}_{latest_quarterly['type']}"
            financial_data[year_key] = data
            print(f"  ✓ 完成最新季报数据提取")
        except Exception as e:
            print(f"  ✗ 季报提取失败: {e}")
    
    return financial_data


def format_financial_data(raw_data):
    """
    将原始数据格式化为分析工具可用的格式
    """
    formatted = {}
    
    for year, data in raw_data.items():
        if not isinstance(data, dict):
            continue
        
        balance = data.get("资产负债表", {})
        income = data.get("利润表", {})
        cashflow = data.get("现金流量表", {})
        financial_institution = data.get("金融企业指标", {})
        shares = data.get("股份口径", {})
        
        def first_present(*values):
            return next((value for value in values if value is not None), None)

        total_assets = balance.get("资产总计")
        total_liabilities = balance.get("负债合计")
        calculated_equity = None
        if total_assets is not None and total_liabilities is not None:
            calculated_equity = total_assets - total_liabilities
        equity = first_present(
            balance.get("所有者权益合计"),
            balance.get("股东权益合计"),
            balance.get("归属于母公司股东权益合计"),
            calculated_equity,
        )

        revenue = income.get("营业收入")
        cost = income.get("营业成本")
        calculated_gross_profit = None
        if revenue is not None and cost is not None:
            calculated_gross_profit = revenue - cost

        operating_profit = income.get("营业利润")
        interest_expense = income.get("利息费用")
        ebit = None
        if operating_profit is not None:
            ebit = operating_profit + abs(interest_expense or 0)

        capex_value = cashflow.get(
            "购建固定资产、无形资产和其他长期资产支付的现金"
        )
        
        formatted[year] = {
            "revenue": revenue,
            "gross_profit": first_present(income.get("毛利润"), calculated_gross_profit),
            "net_profit": first_present(
                income.get("归属于母公司所有者的净利润"),
                income.get("净利润"),
            ),
            "net_profit_koufei": first_present(
                income.get("扣除非经常性损益后的净利润"),
                income.get("归属于母公司所有者的净利润"),
                income.get("净利润"),
            ),
            "total_assets": total_assets,
            "equity": equity,
            "total_liabilities": total_liabilities,
            "current_assets": balance.get("流动资产合计"),
            "current_liabilities": balance.get("流动负债合计"),
            "cash_equivalents": balance.get("货币资金"),
            "short_term_debt": balance.get("短期借款"),
            "long_term_debt": balance.get("长期借款"),
            "accounts_receivable": balance.get("应收账款"),
            "inventory": balance.get("存货"),
            "operating_cash_flow": cashflow.get("经营活动产生的现金流量净额"),
            "capex": abs(capex_value) if capex_value is not None else None,
            "sales_cash": cashflow.get("销售商品、提供劳务收到的现金"),
            "other_receivables": balance.get("其他应收款"),
            "goodwill": balance.get("商誉"),
            "ebit": ebit,
            "interest_expense": abs(interest_expense) if interest_expense is not None else None,
            "shares_in_issue": shares.get("期末已发行股份"),
            "weighted_average_shares": shares.get("加权平均股份"),
            "diluted_weighted_average_shares": shares.get("稀释加权平均股份"),
            "financial_institution_metrics": financial_institution,
            "segments": data.get("业务分部", {"按产品": [], "按渠道": [], "按地区": []}),
            "extraction_metadata": data.get("提取元数据", {}),
        }
    
    return formatted


if __name__ == "__main__":
    import sys
    
    current_dir = Path(__file__).parent.parent
    
    if len(sys.argv) < 2:
        stock_name = "贵州茅台"
        reports_dir = current_dir / "reports"
    else:
        stock_name = sys.argv[1]
        reports_dir = sys.argv[2] if len(sys.argv) > 2 else current_dir / "reports"
    
    print("=" * 60)
    print(f"正在提取 {stock_name} 财务数据...")
    print("=" * 60)
    
    reports = find_reports(str(reports_dir), stock_name)
    print(f"找到 {len(reports)} 份报告文件")
    
    financial_data = load_company_financial_data(str(reports_dir), stock_name)
    
    print("\n" + "=" * 60)
    print("数据提取完成，开始格式化...")
    print("=" * 60)
    
    formatted = format_financial_data(financial_data)
    
    print(f"\n成功提取 {len(formatted)} 年/期数据:")
    for year, data in sorted(formatted.items()):
        print(f"\n{year}年关键数据：")
        def display(value):
            return f"{value:.2f}亿元" if value is not None else "N/A（需人工核验）"

        print(f"  营业收入：{display(data['revenue'])}")
        print(f"  净利润：{display(data['net_profit'])}")
        if data['net_profit'] is not None and data['equity'] is not None and data['equity'] > 0:
            print(f"  ROE：{data['net_profit']/data['equity']*100:.2f}%")
        else:
            print("  ROE：N/A")
        print(f"  经营现金流：{display(data['operating_cash_flow'])}")
