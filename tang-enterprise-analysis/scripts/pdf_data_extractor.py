#!/usr/bin/env python3
"""
PDF年报数据提取工具
从A股上市公司年报/季报PDF中自动提取关键财务数据
"""

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


class PDFReportExtractor:
    """PDF年报候选数据提取器。

    输出必须对照原始报表复核，不应直接进入估值模型。
    """

    UNIT_SCALES = {
        "元": 1,
        "千元": 1_000,
        "万元": 10_000,
        "百万元": 1_000_000,
    }

    def __init__(self, pdf_path, max_pages=None):
        self.pdf_path = pdf_path
        self.filename = os.path.basename(pdf_path)
        self.text = ""
        self.tables = []
        self.sources = {}
        self.warnings = []
        self._load_pdf(max_pages=max_pages)

    def _load_pdf(self, max_pages=None):
        """加载PDF并提取文本"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                if max_pages is not None and i >= max_pages:
                    break
                page_text = page.extract_text()
                if page_text:
                    self.text += page_text + "\n"

                tables = page.extract_tables()
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
        return re.sub(r"\s+", "", str(value or ""))

    @staticmethod
    def _parse_number(value):
        text = str(value or "").strip().replace(",", "").replace(" ", "")
        if not text or text in {"-", "—", "--", "不适用"}:
            return None
        negative = text.startswith("(") and text.endswith(")")
        if negative:
            text = text[1:-1]
        text = text.replace("￥", "").replace("¥", "")
        try:
            number = float(text)
            return -number if negative else number
        except ValueError:
            return None

    def _table_unit(self, record):
        context = record["page_text"] + " " + str(record["data"][:3])
        matches = re.findall(
            r"单位\s*[：:]\s*(?:人民币)?\s*(百万元|万元|千元|元)",
            context,
        )
        if matches:
            unit = matches[-1]
            return unit, self.UNIT_SCALES[unit], "high"
        warning = f"第{record['page']}页未识别金额单位，暂按元换算，必须人工复核"
        if warning not in self.warnings:
            self.warnings.append(warning)
        return "未识别（暂按元）", 1, "low"

    @staticmethod
    def _match_key(item_name, keys):
        normalized = re.sub(r"^[（(]?\d+[）).、]?", "", item_name)
        exact = [key for key in keys if normalized == key]
        if exact:
            return exact[0]
        matches = [key for key in keys if key in normalized]
        return max(matches, key=len) if matches else None

    def _row_value(self, row):
        candidates = []
        for cell in row[1:5]:
            number = self._parse_number(cell)
            if number is not None:
                candidates.append(number)
        if not candidates:
            return None
        if (
            len(candidates) >= 2
            and abs(candidates[0]) < 1000
            and abs(candidates[1]) > max(abs(candidates[0]) * 100, 1000)
        ):
            return candidates[1]
        return candidates[0]

    def _extract_statement(self, statement, keys, title, signatures):
        data = {key: None for key in keys}
        self.sources[statement] = {}
        for record in self.tables:
            table = record["data"]
            context = self._normalize(record["page_text"] + str(table))
            if title not in context or not any(sig in context for sig in signatures):
                continue
            unit, scale, confidence = self._table_unit(record)
            for row in table:
                if not row or len(row) < 2:
                    continue
                item_name = self._normalize(row[0])
                key = self._match_key(item_name, keys)
                if key is None or data[key] is not None:
                    continue
                value = self._row_value(row)
                if value is None:
                    continue
                data[key] = value * scale / 100_000_000
                self.sources[statement][key] = {
                    "page": record["page"],
                    "unit": unit,
                    "period_column": "首个可识别本期数，需复核表头",
                    "confidence": confidence,
                }
        return data

    def extract_composite_balance_sheet(self):
        """
        提取合并资产负债表数据
        返回单位：亿元
        """
        keys = [
            "货币资金", "应收账款", "应收票据", "存货", "流动资产合计",
            "资产总计", "短期借款", "长期借款", "流动负债合计",
            "负债合计", "所有者权益合计", "其他应收款", "商誉",
            "合同负债", "股东权益合计", "归属于母公司股东权益合计",
        ]
        return self._extract_statement(
            "资产负债表", keys, "合并资产负债表", ["资产总计", "货币资金"]
        )
    
    def extract_composite_income_statement(self):
        """
        提取合并利润表数据
        返回单位：亿元
        """
        keys = [
            "营业收入", "营业成本", "毛利润", "销售费用", "管理费用",
            "研发费用", "财务费用", "营业利润", "利润总额", "净利润",
            "归属于母公司所有者的净利润", "扣除非经常性损益后的净利润",
            "利息费用",
        ]
        data = self._extract_statement(
            "利润表", keys, "合并利润表", ["营业收入", "营业利润"]
        )
        if data["营业收入"] is not None and data["营业成本"] is not None:
            data["毛利润"] = data["营业收入"] - data["营业成本"]
        return data
    
    def extract_composite_cash_flow(self):
        """
        提取合并现金流量表数据
        返回单位：亿元
        """
        keys = [
            "经营活动产生的现金流量净额", "投资活动产生的现金流量净额",
            "筹资活动产生的现金流量净额", "销售商品、提供劳务收到的现金",
            "购建固定资产、无形资产和其他长期资产支付的现金",
            "分配股利、利润或偿付利息支付的现金",
        ]
        return self._extract_statement(
            "现金流量表", keys, "合并现金流量表", ["经营活动", "现金流量"]
        )
    
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
        segments = self.extract_business_segments()
        
        return {
            "资产负债表": balance,
            "利润表": income,
            "现金流量表": cashflow,
            "业务分部": segments,
            "提取元数据": {
                "source_file": self.filename,
                "sources": self.sources,
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
        
        year_match = re.search(r"(\d{4})年", filename)
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
