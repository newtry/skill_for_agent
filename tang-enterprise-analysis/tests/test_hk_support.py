import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    path = SKILL_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pdf_extractor = load_module("hk_pdf_data_extractor", "scripts/pdf_data_extractor.py")
hkex = load_module("hkex_report_downloader", "scripts/hkex_report_downloader.py")


class FakeResponse:
    def __init__(self, text="", headers=None, chunks=None, status_code=200):
        self.text = text
        self.headers = headers or {}
        self._chunks = chunks or []
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size):
        del chunk_size
        return iter(self._chunks)


class SearchSession:
    def __init__(self):
        self.headers = {}
        self.sizes = {
            "https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0408/2025040800001.pdf": 100,
            "https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0408/2025040800002.pdf": 200,
        }

    def get(self, url, **kwargs):
        del kwargs
        if url == hkex.HKEXReportDownloader.TITLE_SEARCH_URL:
            return FakeResponse("Listed Company Information Title Search")
        if url == hkex.HKEXReportDownloader.PREFIX_URL:
            payload = {
                "stockInfo": [
                    {"stockId": 1234, "code": "00700", "name": "TENCENT"}
                ]
            }
            return FakeResponse(f"callback({json.dumps(payload)});")
        raise AssertionError(url)

    def post(self, url, data, **kwargs):
        del data, kwargs
        self.last_post_url = url
        return FakeResponse(
            """
            Total records found: 2
            <a href="/listedco/listconews/sehk/2025/0408/2025040800001.pdf">Annual Report 2024</a>
            <a href="/listedco/listconews/sehk/2025/0408/2025040800002.pdf">2024 Annual Report</a>
            """
        )

    def head(self, url, **kwargs):
        del kwargs
        return FakeResponse(
            headers={
                "Content-Type": "application/pdf",
                "Content-Length": str(self.sizes[url]),
            }
        )


class DownloadSession:
    def __init__(self):
        self.headers = {}

    def get(self, url, **kwargs):
        del url, kwargs
        return FakeResponse(
            headers={"Content-Type": "application/pdf"},
            chunks=[b"%PDF-1.7\n", b"annual-report"],
        )


class HKEXDownloaderTests(unittest.TestCase):
    def test_dynamic_lookup_and_full_report_selection(self):
        downloader = hkex.HKEXReportDownloader(
            download_dir=tempfile.gettempdir(), session=SearchSession()
        )
        records = downloader.search_annual_reports("700", [2024])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["code"], "00700")
        self.assertEqual(records[0]["name"], "TENCENT")
        self.assertEqual(records[0]["report_year"], 2024)
        self.assertEqual(records[0]["published_at"], "2025-04-08")
        self.assertTrue(records[0]["url"].endswith("2025040800002.pdf"))

    def test_download_validates_pdf_and_writes_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.pdf"
            downloader = hkex.HKEXReportDownloader(
                download_dir=directory, session=DownloadSession()
            )
            downloader._download_pdf("https://example.test/report.pdf", output)
            self.assertEqual(output.read_bytes(), b"%PDF-1.7\nannual-report")
            self.assertFalse(output.with_suffix(".pdf.part").exists())

    def test_stock_code_validation(self):
        self.assertEqual(hkex.HKEXReportDownloader.normalize_code("5"), "00005")
        with self.assertRaises(ValueError):
            hkex.HKEXReportDownloader.normalize_code("not-a-code")

    @unittest.skipUnless(
        os.environ.get("HKEX_LIVE_TEST") == "1",
        "set HKEX_LIVE_TEST=1 to query HKEXnews",
    )
    def test_live_2024_report_lookup(self):
        expected = {
            "00700": "2025040800667.pdf",
            "03690": "2025042800235.pdf",
            "00005": "2025021900181.pdf",
        }
        with tempfile.TemporaryDirectory() as directory:
            downloader = hkex.HKEXReportDownloader(directory)
            for code, filename in expected.items():
                with self.subTest(code=code):
                    records = downloader.search_annual_reports(code, [2024])
                    self.assertEqual(len(records), 1)
                    self.assertTrue(records[0]["url"].endswith(filename))


class HKAnnualReportExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_path = SKILL_ROOT / "tests/fixtures/hk_annual_report_extracts.json"
        cls.fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))

    def extract_fixture(self, name):
        fixture = self.fixtures[name]
        extractor = pdf_extractor.PDFReportExtractor.__new__(
            pdf_extractor.PDFReportExtractor
        )
        extractor.filename = f"{name}.pdf"
        extractor.default_currency = fixture["reporting_currency"]
        extractor.detected_currencies = set()
        extractor.text = " ".join(record["page_text"] for record in fixture["records"])
        extractor.tables = fixture["records"]
        extractor.sources = {}
        extractor.warnings = []
        return extractor.extract_all_data()

    def test_tencent_rmb_millions_and_share_count(self):
        data = self.extract_fixture("tencent_2024")
        self.assertAlmostEqual(data["利润表"]["营业收入"], 6602.57)
        self.assertAlmostEqual(data["利润表"]["营业成本"], 3110.11)
        self.assertAlmostEqual(data["利润表"]["毛利润"], 3492.46)
        self.assertAlmostEqual(
            data["现金流量表"]["经营活动产生的现金流量净额"], 2585.21
        )
        self.assertEqual(data["股份口径"]["加权平均股份"], 9_269_000_000)
        self.assertEqual(data["股份口径"]["稀释加权平均股份"], 9_408_000_000)
        self.assertEqual(
            data["提取元数据"]["sources"]["利润表"]["营业收入"]["kind"],
            "calculated",
        )

    def test_meituan_rmb_thousands_and_split_note_cells(self):
        data = self.extract_fixture("meituan_2024")
        self.assertAlmostEqual(data["利润表"]["营业收入"], 3375.91576)
        self.assertAlmostEqual(data["利润表"]["营业成本"], 2078.06982)
        self.assertAlmostEqual(data["利润表"]["毛利润"], 1297.84594)
        self.assertAlmostEqual(
            data["现金流量表"]["经营活动产生的现金流量净额"], 571.46784
        )
        self.assertEqual(data["股份口径"]["加权平均股份"], 6_125_058_000)
        self.assertEqual(data["股份口径"]["稀释加权平均股份"], 6_225_689_000)

    def test_hsbc_usd_bank_fields_and_eps_share_columns(self):
        data = self.extract_fixture("hsbc_2024")
        self.assertAlmostEqual(data["金融企业指标"]["净利息收入"], 327.33)
        self.assertAlmostEqual(data["资产负债表"]["资产总计"], 30170.48)
        self.assertAlmostEqual(data["金融企业指标"]["客户贷款"], 9306.58)
        self.assertAlmostEqual(data["金融企业指标"]["客户存款"], 16549.55)
        self.assertAlmostEqual(
            data["现金流量表"]["经营活动产生的现金流量净额"], 653.05
        )
        self.assertEqual(data["股份口径"]["加权平均股份"], 18_357_000_000)
        self.assertEqual(data["股份口径"]["稀释加权平均股份"], 18_485_000_000)
        self.assertIn("USD", data["提取元数据"]["reporting_currencies"])

    def test_hkd_amount_and_period_end_share_normalization(self):
        extractor = pdf_extractor.PDFReportExtractor.__new__(
            pdf_extractor.PDFReportExtractor
        )
        extractor.filename = "hkd_fixture.pdf"
        extractor.default_currency = None
        extractor.detected_currencies = set()
        extractor.text = ""
        extractor.tables = [
            {
                "page": 10,
                "page_text": (
                    "Consolidated Income Statement. HK$ million. "
                    "Revenue. Profit before tax."
                ),
                "data": [["Revenue", "", "12,345", "11,000"]],
            },
            {
                "page": 80,
                "page_text": "Number of issued shares (thousands)",
                "data": [["Number of issued shares", "2,500,000"]],
            },
        ]
        extractor.sources = {}
        extractor.warnings = []

        data = extractor.extract_all_data()
        self.assertAlmostEqual(data["利润表"]["营业收入"], 123.45)
        self.assertEqual(data["股份口径"]["期末已发行股份"], 2_500_000_000)
        revenue_source = data["提取元数据"]["sources"]["利润表"]["营业收入"]
        self.assertEqual(revenue_source["currency"], "HKD")
        self.assertEqual(revenue_source["normalized_unit"], "1e8 HKD")
        self.assertEqual(
            data["提取元数据"]["sources"]["股份口径"]["期末已发行股份"][
                "normalized_unit"
            ],
            "shares",
        )

    def test_fixtures_are_traceable_to_hkex(self):
        for name, fixture in self.fixtures.items():
            with self.subTest(name=name):
                self.assertRegex(
                    fixture["source_url"],
                    r"^https://www1\.hkexnews\.hk/.+\.pdf$",
                )

    def test_pdf_loader_falls_back_when_default_table_has_only_numbers(self):
        class Page:
            def extract_text(self):
                return (
                    "Consolidated Income Statement. Note RMB*Million. "
                    "Revenues. Gross profit. Profit before income tax."
                )

            def extract_tables(self, settings=None):
                if settings is None:
                    return [[
                        ["2024"],
                        ["RMB*Million"],
                        ["660,257"],
                        ["(311,011)"],
                    ]]
                return [[
                    ["Revenues", "", "660,257", "609,015"],
                    ["Cost of revenues", "7", "(311,011)", "(315,906)"],
                    ["Gross profit", "", "349,246", "293,109"],
                ]]

        class PDF:
            pages = [Page()]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                del exc_type, exc, traceback

        with mock.patch.object(pdf_extractor.pdfplumber, "open", return_value=PDF()):
            extractor = pdf_extractor.PDFReportExtractor(
                "fixture.pdf", reporting_currency="CNY"
            )
        data = extractor.extract_composite_income_statement()
        self.assertAlmostEqual(data["营业收入"], 6602.57)
        self.assertAlmostEqual(data["营业成本"], 3110.11)


if __name__ == "__main__":
    unittest.main()
