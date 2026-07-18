import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    path = SKILL_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


valuation = load_module("valuation_calculator", "scripts/valuation_calculator.py")
history = load_module("historical_data_analyzer", "scripts/historical_data_analyzer.py")
pdf_extractor = load_module("pdf_data_extractor", "scripts/pdf_data_extractor.py")


class ValuationTests(unittest.TestCase):
    def test_fcff_and_equity_bridge(self):
        fcff = valuation.calculate_fcff(100, 0.25, 10, 20, 5)
        self.assertEqual(fcff, 60)
        equity_value = valuation.bridge_enterprise_to_equity_value(
            1000,
            excess_cash=100,
            non_operating_investments=50,
            interest_bearing_debt=200,
            lease_liabilities=20,
            minority_interest=30,
        )
        self.assertEqual(equity_value, 900)

    def test_explicit_cash_flow_dcf_reports_terminal_share(self):
        result = valuation.calculate_dcf_from_cash_flows(
            [100, 105, 110], discount_rate=0.1, perpetual_growth_rate=0.02
        )
        self.assertGreater(result["企业价值"], 0)
        self.assertGreater(result["终值占比"], 0)
        self.assertLess(result["终值占比"], 1)

    def test_dcf_known_value(self):
        value = valuation.calculate_intrinsic_value(100, 0, 1, 0, 0.1)
        self.assertAlmostEqual(value, 1000.0)

    def test_invalid_terminal_assumptions_fail(self):
        for terminal_growth in (0.1, 0.11):
            with self.subTest(terminal_growth=terminal_growth):
                with self.assertRaisesRegex(ValueError, "折现率必须高于永续增长率"):
                    valuation.calculate_intrinsic_value(
                        100, 0.05, 5, terminal_growth, 0.1
                    )

    def test_invalid_years_and_shares_fail(self):
        with self.assertRaises(ValueError):
            valuation.calculate_intrinsic_value(100, 0.05, -1, 0.02, 0.1)
        with self.assertRaisesRegex(ValueError, "总股本必须大于0"):
            valuation.calculate_share_intrinsic_value(100, 0)

    def test_bank_uses_residual_income(self):
        result = valuation.valuate_bank_residual_income(
            book_value=1000,
            roe=0.13,
            cost_of_equity=0.10,
            years=5,
            payout_ratio=0.3,
            terminal_roe=0.11,
            shares_outstanding=100,
        )
        self.assertEqual(result["模型"], "简化剩余收益模型")
        self.assertGreater(result["股权价值"], 1000)
        self.assertAlmostEqual(
            result["每股内在价值"], result["股权价值"] / 100
        )

    def test_cyclical_model_excludes_financials(self):
        result = valuation.valuate_cyclical_company(100, 20, shares_outstanding=10)
        self.assertEqual(result["企业类型"], "周期型非金融企业")
        self.assertIn("不适用于银行", result["限制"])


class HistoricalTrendTests(unittest.TestCase):
    def test_steady_growth_is_not_volatile(self):
        analyzer = history.HistoricalDataAnalyzer("测试公司")
        for year, revenue in enumerate((100, 110, 121, 133.1, 146.41), start=2020):
            analyzer.add_year_data(
                history.YearlyData(year=year, revenue=revenue)
            )
        trend = analyzer.analyze_trends()["营业收入"]
        self.assertEqual(trend.direction, history.TrendDirection.UP)
        self.assertAlmostEqual(trend.volatility, 0.0)

    def test_export_creates_parent_directory(self):
        analyzer = history.HistoricalDataAnalyzer("测试公司")
        analyzer.add_year_data(history.YearlyData(year=2025, revenue=100))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "data.json"
            analyzer.export_data(str(output))
            self.assertTrue(output.exists())
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8"))["company_name"],
                "测试公司",
            )


class PdfExtractionTests(unittest.TestCase):
    def make_extractor(self, page_text, table):
        extractor = pdf_extractor.PDFReportExtractor.__new__(
            pdf_extractor.PDFReportExtractor
        )
        extractor.filename = "fixture.pdf"
        extractor.text = page_text
        extractor.tables = [{"page": 12, "page_text": page_text, "data": table}]
        extractor.sources = {}
        extractor.warnings = []
        return extractor

    def test_extracts_current_column_and_unit_with_source(self):
        extractor = self.make_extractor(
            "合并利润表 单位：人民币百万元",
            [
                ["项目", "附注", "2025年", "2024年"],
                ["营业收入", "五、1", "12,000", "10,000"],
                ["营业成本", "五、2", "7,000", "6,000"],
            ],
        )
        data = extractor.extract_composite_income_statement()
        self.assertEqual(data["营业收入"], 120.0)
        self.assertEqual(data["营业成本"], 70.0)
        self.assertEqual(data["毛利润"], 50.0)
        source = extractor.sources["利润表"]["营业收入"]
        self.assertEqual(source["page"], 12)
        self.assertEqual(source["confidence"], "high")

    def test_missing_value_stays_none(self):
        extractor = self.make_extractor(
            "合并资产负债表 单位：人民币元",
            [["项目", "2025年"], ["资产总计", "1,000"]],
        )
        data = extractor.extract_composite_balance_sheet()
        self.assertIsNone(data["货币资金"])

    def test_unknown_unit_is_low_confidence(self):
        extractor = self.make_extractor(
            "合并现金流量表",
            [["项目", "本期"], ["经营活动产生的现金流量净额", "100"]],
        )
        extractor.extract_composite_cash_flow()
        source = extractor.sources["现金流量表"]["经营活动产生的现金流量净额"]
        self.assertEqual(source["confidence"], "low")
        self.assertTrue(extractor.warnings)


class EvalSchemaTests(unittest.TestCase):
    def test_eval_suite_has_positive_and_negative_cases(self):
        data = json.loads(
            (SKILL_ROOT / "evals/evals.json").read_text(encoding="utf-8")
        )
        labels = [case["should_trigger"] for case in data["evals"]]
        self.assertGreaterEqual(labels.count(True), 8)
        self.assertGreaterEqual(labels.count(False), 4)
        self.assertEqual(len({case["id"] for case in data["evals"]}), len(labels))


class ReferenceQualityTests(unittest.TestCase):
    def setUp(self):
        self.references = SKILL_ROOT / "references"

    def test_reference_docs_are_routable_and_bounded(self):
        files = sorted(self.references.glob("*.md"))
        self.assertGreaterEqual(len(files), 8)
        total_lines = 0
        for path in files:
            content = path.read_text(encoding="utf-8")
            line_count = len(content.splitlines())
            total_lines += line_count
            self.assertIn("## 目录", content, path.name)
            self.assertLessEqual(line_count, 350, path.name)
        self.assertLessEqual(total_lines, 1800)

    def test_reference_links_resolve(self):
        markdown_files = [SKILL_ROOT / "SKILL.md", *self.references.glob("*.md")]
        for path in markdown_files:
            content = path.read_text(encoding="utf-8")
            for link in re.findall(r"\]\(([^)#]+\.md)(?:#[^)]+)?\)", content):
                target = path.parent / link
                self.assertTrue(target.exists(), f"{path.name}: {link}")

    def test_deprecated_rules_do_not_return(self):
        content = "\n".join(
            path.read_text(encoding="utf-8")
            for path in self.references.glob("*.md")
        )
        forbidden = (
            "FCF = 净利润 ×",
            "理论上最科学",
            "折现率是否不低于8%",
            "永续增长率是否在3%-5%之间",
            "核心持仓，仓位",
            "招商银行是银行股里最好的",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, content)

    def test_examples_are_synthetic(self):
        content = (self.references / "case_studies.md").read_text(encoding="utf-8")
        self.assertIn("全部为合成教学材料", content)
        for company in ("贵州茅台", "腾讯控股", "招商银行", "康美药业"):
            self.assertNotIn(company, content)


if __name__ == "__main__":
    unittest.main()
