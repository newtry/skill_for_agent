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
    """PDF年报数据提取器"""
    
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.filename = os.path.basename(pdf_path)
        self.text = ""
        self.tables = []
        self._load_pdf()
    
    def _load_pdf(self, max_pages=80):
        """加载PDF并提取文本"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                if i >= max_pages:
                    break
                page_text = page.extract_text()
                if page_text:
                    self.text += page_text + "\n"
                
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        self.tables.append(table)
        
        self.text = self.text.replace("\n", " ")
    
    def extract_composite_balance_sheet(self):
        """
        提取合并资产负债表数据
        返回单位：亿元
        """
        data = {
            "货币资金": 0,
            "应收账款": 0,
            "应收票据": 0,
            "存货": 0,
            "流动资产合计": 0,
            "资产总计": 0,
            "短期借款": 0,
            "长期借款": 0,
            "流动负债合计": 0,
            "负债合计": 0,
            "所有者权益合计": 0,
            "其他应收款": 0,
            "商誉": 0,
            "合同负债": 0,
            "股东权益合计": 0,
            "归属于母公司股东权益合计": 0
        }
        
        unit_scale = 100000000
        
        for table in self.tables:
            if not table or len(table) < 2:
                continue
            
            table_str = str(table).replace(" ", "")
            if "资产总计" not in table_str and "货币资金" not in table_str:
                continue
            
            for row in table:
                if not row or len(row) < 2:
                    continue
                
                item_name = str(row[0]) if row[0] else ""
                item_name = re.sub(r"\s+", "", item_name)
                
                for i in range(1, min(5, len(row))):
                    value_str = str(row[i]) if row[i] else ""
                    value_str = value_str.replace(",", "").replace(" ", "")
                    
                    try:
                        value = float(value_str)
                        
                        value_yi = value / 100000000
                        
                        for key in data.keys():
                            key_clean = key.replace(" ", "")
                            if key_clean in item_name or item_name in key_clean:
                                if value_yi > 0:
                                    data[key] = max(data[key], value_yi)
                                elif value_yi != 0:
                                    data[key] = value_yi
                                break
                    except:
                        continue
        
        return data
    
    def extract_composite_income_statement(self):
        """
        提取合并利润表数据
        返回单位：亿元
        """
        data = {
            "营业收入": 0,
            "营业成本": 0,
            "毛利润": 0,
            "销售费用": 0,
            "管理费用": 0,
            "研发费用": 0,
            "财务费用": 0,
            "营业利润": 0,
            "利润总额": 0,
            "净利润": 0,
            "归属于母公司所有者的净利润": 0,
            "扣除非经常性损益后的净利润": 0,
            "利息费用": 0
        }
        
        unit_scale = 100000000
        
        for table in self.tables:
            if not table or len(table) < 2:
                continue
            
            table_str = str(table).replace(" ", "")
            if "营业收入" not in table_str and "营业利润" not in table_str:
                continue
            
            for row in table:
                if not row or len(row) < 2:
                    continue
                
                item_name = str(row[0]) if row[0] else ""
                item_name = re.sub(r"\s+", "", item_name)
                
                for i in range(1, min(5, len(row))):
                    value_str = str(row[i]) if row[i] else ""
                    value_str = value_str.replace(",", "").replace(" ", "")
                    
                    try:
                        value = float(value_str)
                        value_yi = value / 100000000
                        
                        for key in data.keys():
                            key_clean = key.replace(" ", "")
                            if key_clean in item_name:
                                if value_yi > 0:
                                    data[key] = max(data[key], value_yi)
                                elif value_yi != 0:
                                    data[key] = value_yi
                                break
                    except:
                        continue
        
        if data["营业收入"] > 0 and data["营业成本"] > 0:
            data["毛利润"] = data["营业收入"] - data["营业成本"]
        
        return data
    
    def extract_composite_cash_flow(self):
        """
        提取合并现金流量表数据
        返回单位：亿元
        """
        data = {
            "经营活动产生的现金流量净额": 0,
            "投资活动产生的现金流量净额": 0,
            "筹资活动产生的现金流量净额": 0,
            "销售商品、提供劳务收到的现金": 0,
            "购建固定资产、无形资产和其他长期资产支付的现金": 0,
            "分配股利、利润或偿付利息支付的现金": 0
        }
        
        unit_scale = 100000000
        
        for table in self.tables:
            if not table or len(table) < 2:
                continue
            
            table_str = str(table).replace(" ", "")
            if "经营活动" not in table_str and "现金流量" not in table_str:
                continue
            
            for row in table:
                if not row or len(row) < 2:
                    continue
                
                item_name = str(row[0]) if row[0] else ""
                item_name = re.sub(r"\s+", "", item_name)
                
                for i in range(1, min(5, len(row))):
                    value_str = str(row[i]) if row[i] else ""
                    value_str = value_str.replace(",", "").replace(" ", "")
                    
                    try:
                        value = float(value_str)
                        value_yi = value / 100000000
                        
                        for key in data.keys():
                            key_clean = key.replace(" ", "")
                            if key_clean in item_name:
                                if abs(value_yi) > abs(data[key]):
                                    data[key] = value_yi
                                break
                    except:
                        continue
        
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
        
        for table in self.tables:
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
            "业务分部": segments
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
        
        equity = balance.get("所有者权益合计", 0) or balance.get("股东权益合计", 0) or balance.get("归属于母公司股东权益合计", 0) or (balance.get("资产总计", 0) - balance.get("负债合计", 0))
        
        formatted[year] = {
            "revenue": income.get("营业收入", 0),
            "gross_profit": income.get("毛利润", 0) or (income.get("营业收入", 0) - income.get("营业成本", 0)),
            "net_profit": income.get("归属于母公司所有者的净利润", 0) or income.get("净利润", 0),
            "net_profit_koufei": income.get("扣除非经常性损益后的净利润", 0) or income.get("净利润", 0),
            "total_assets": balance.get("资产总计", 0),
            "equity": equity,
            "total_liabilities": balance.get("负债合计", 0),
            "current_assets": balance.get("流动资产合计", 0),
            "current_liabilities": balance.get("流动负债合计", 0),
            "cash_equivalents": balance.get("货币资金", 0),
            "short_term_debt": balance.get("短期借款", 0),
            "long_term_debt": balance.get("长期借款", 0),
            "accounts_receivable": balance.get("应收账款", 0) or 0.01,
            "inventory": balance.get("存货", 0),
            "operating_cash_flow": cashflow.get("经营活动产生的现金流量净额", 0),
            "capex": abs(cashflow.get("购建固定资产、无形资产和其他长期资产支付的现金", 0)),
            "sales_cash": cashflow.get("销售商品、提供劳务收到的现金", 0),
            "other_receivables": balance.get("其他应收款", 0),
            "goodwill": balance.get("商誉", 0),
            "ebit": income.get("营业利润", 0) + abs(income.get("利息费用", 0)),
            "interest_expense": abs(income.get("利息费用", 0)) or 0.01,
            "segments": data.get("业务分部", {"按产品": [], "按渠道": [], "按地区": []})
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
        print(f"  营业收入：{data['revenue']:.2f}亿元")
        print(f"  净利润：{data['net_profit']:.2f}亿元")
        print(f"  ROE：{data['net_profit']/data['equity']*100:.2f}%" if data['equity'] > 0 else "  ROE：N/A")
        print(f"  经营现金流：{data['operating_cash_flow']:.2f}亿元")
