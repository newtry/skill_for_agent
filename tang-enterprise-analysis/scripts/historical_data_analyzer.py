#!/usr/bin/env python3
"""
多年历史数据对比分析器
用于分析企业多年财务数据趋势，识别变化和异常

功能：
1. 存储多年财务数据
2. 计算年度变化率和复合增长率
3. 趋势分析和异常识别
4. 生成对比分析报告
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json


class TrendDirection(Enum):
    """趋势方向"""
    UP = "上升"
    DOWN = "下降"
    STABLE = "稳定"
    VOLATILE = "波动"


class ChangeLevel(Enum):
    """变化程度"""
    EXCELLENT = "优秀"
    GOOD = "良好"
    NORMAL = "正常"
    WARNING = "警告"
    DANGER = "危险"


@dataclass
class YearlyData:
    """年度数据"""
    year: int
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    net_profit: Optional[float] = None
    deducted_profit: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    total_assets: Optional[float] = None
    net_assets: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    total_liabilities: Optional[float] = None
    
    @property
    def gross_margin(self) -> Optional[float]:
        """毛利率"""
        if self.revenue and self.gross_profit and self.revenue > 0:
            return self.gross_profit / self.revenue
        return None
    
    @property
    def net_margin(self) -> Optional[float]:
        """净利率"""
        if self.revenue and self.net_profit and self.revenue > 0:
            return self.net_profit / self.revenue
        return None
    
    @property
    def roe(self) -> Optional[float]:
        """ROE"""
        if self.net_profit and self.net_assets and self.net_assets > 0:
            return self.net_profit / self.net_assets
        return None
    
    @property
    def roa(self) -> Optional[float]:
        """ROA"""
        if self.net_profit and self.total_assets and self.total_assets > 0:
            return self.net_profit / self.total_assets
        return None
    
    @property
    def asset_turnover(self) -> Optional[float]:
        """资产周转率"""
        if self.revenue and self.total_assets and self.total_assets > 0:
            return self.revenue / self.total_assets
        return None
    
    @property
    def leverage_ratio(self) -> Optional[float]:
        """杠杆率"""
        if self.total_assets and self.net_assets and self.net_assets > 0:
            return self.total_assets / self.net_assets
        return None
    
    @property
    def cash_to_profit(self) -> Optional[float]:
        """现金流/净利润"""
        if self.operating_cash_flow and self.net_profit and self.net_profit > 0:
            return self.operating_cash_flow / self.net_profit
        return None
    
    @property
    def ar_to_revenue(self) -> Optional[float]:
        """应收账款/营收"""
        if self.accounts_receivable and self.revenue and self.revenue > 0:
            return self.accounts_receivable / self.revenue
        return None
    
    @property
    def inventory_to_revenue(self) -> Optional[float]:
        """存货/营收"""
        if self.inventory and self.revenue and self.revenue > 0:
            return self.inventory / self.revenue
        return None
    
    @property
    def liability_ratio(self) -> Optional[float]:
        """资产负债率"""
        if self.total_liabilities and self.total_assets and self.total_assets > 0:
            return self.total_liabilities / self.total_assets
        return None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'year': self.year,
            'revenue': self.revenue,
            'gross_profit': self.gross_profit,
            'net_profit': self.net_profit,
            'deducted_profit': self.deducted_profit,
            'operating_cash_flow': self.operating_cash_flow,
            'total_assets': self.total_assets,
            'net_assets': self.net_assets,
            'accounts_receivable': self.accounts_receivable,
            'inventory': self.inventory,
            'total_liabilities': self.total_liabilities,
            'gross_margin': self.gross_margin,
            'net_margin': self.net_margin,
            'roe': self.roe,
            'roa': self.roa,
            'asset_turnover': self.asset_turnover,
            'leverage_ratio': self.leverage_ratio,
            'cash_to_profit': self.cash_to_profit,
            'ar_to_revenue': self.ar_to_revenue,
            'inventory_to_revenue': self.inventory_to_revenue,
            'liability_ratio': self.liability_ratio
        }


@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    metric_name: str
    values: List[Tuple[int, float]]
    direction: TrendDirection
    cagr: Optional[float] = None
    avg_change_rate: Optional[float] = None
    volatility: Optional[float] = None
    anomalies: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'metric_name': self.metric_name,
            'values': self.values,
            'direction': self.direction.value,
            'cagr': self.cagr,
            'avg_change_rate': self.avg_change_rate,
            'volatility': self.volatility,
            'anomalies': self.anomalies
        }


class HistoricalDataAnalyzer:
    """
    多年历史数据对比分析器
    
    使用方法：
        analyzer = HistoricalDataAnalyzer("贵州茅台")
        
        # 添加年度数据
        analyzer.add_year_data(YearlyData(
            year=2023,
            revenue=1505.6,
            gross_profit=1382.3,
            net_profit=747.3,
            ...
        ))
        
        # 分析趋势
        trends = analyzer.analyze_trends()
        
        # 生成报告
        report = analyzer.generate_comparison_report()
    """
    
    def __init__(self, company_name: str):
        """
        初始化分析器
        
        Args:
            company_name: 公司名称
        """
        self.company_name = company_name
        self.yearly_data: Dict[int, YearlyData] = {}
    
    def add_year_data(self, data: YearlyData) -> None:
        """
        添加年度数据
        
        Args:
            data: 年度数据
        """
        self.yearly_data[data.year] = data
    
    def add_year_data_from_dict(self, data_dict: Dict) -> None:
        """
        从字典添加年度数据
        
        Args:
            data_dict: 数据字典
        """
        data = YearlyData(
            year=data_dict.get('year'),
            revenue=data_dict.get('revenue'),
            gross_profit=data_dict.get('gross_profit'),
            net_profit=data_dict.get('net_profit'),
            deducted_profit=data_dict.get('deducted_profit'),
            operating_cash_flow=data_dict.get('operating_cash_flow'),
            total_assets=data_dict.get('total_assets'),
            net_assets=data_dict.get('net_assets'),
            accounts_receivable=data_dict.get('accounts_receivable'),
            inventory=data_dict.get('inventory'),
            total_liabilities=data_dict.get('total_liabilities')
        )
        self.add_year_data(data)
    
    def get_sorted_years(self) -> List[int]:
        """
        获取排序后的年份列表
        """
        return sorted(self.yearly_data.keys())
    
    def calculate_cagr(self, values: List[float], years: int) -> Optional[float]:
        """
        计算复合增长率 (CAGR)
        
        Args:
            values: 数值列表
            years: 年数
            
        Returns:
            CAGR
        """
        if len(values) < 2 or years < 1:
            return None
        
        start_value = values[0]
        end_value = values[-1]
        
        if start_value <= 0 or end_value <= 0:
            return None
        
        return (end_value / start_value) ** (1 / years) - 1
    
    def calculate_change_rates(self, values: List[float]) -> List[float]:
        """
        计算年度变化率
        
        Args:
            values: 数值列表
            
        Returns:
            变化率列表
        """
        rates = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                rate = (values[i] - values[i-1]) / abs(values[i-1])
                rates.append(rate)
        return rates
    
    def calculate_volatility(self, values: List[float]) -> Optional[float]:
        """
        计算波动率（标准差/均值）
        
        Args:
            values: 数值列表
            
        Returns:
            波动率
        """
        if len(values) < 2:
            return None
        
        mean = sum(values) / len(values)
        if mean == 0:
            return None
        
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        return std_dev / abs(mean)
    
    def detect_anomalies(self, values: List[Tuple[int, float]], threshold: float = 0.3) -> List[Dict]:
        """
        检测异常变化
        
        Args:
            values: (年份, 数值) 列表
            threshold: 异常阈值（变化率超过此值为异常）
            
        Returns:
            异常列表
        """
        anomalies = []
        
        for i in range(1, len(values)):
            year, current = values[i]
            prev_year, prev_value = values[i-1]
            
            if prev_value != 0:
                change_rate = (current - prev_value) / abs(prev_value)
                
                if abs(change_rate) > threshold:
                    anomalies.append({
                        'year': year,
                        'prev_year': prev_year,
                        'change_rate': change_rate,
                        'prev_value': prev_value,
                        'current_value': current,
                        'type': '大幅增长' if change_rate > 0 else '大幅下降',
                        'severity': '高' if abs(change_rate) > 0.5 else '中'
                    })
        
        return anomalies
    
    def analyze_metric_trend(self, metric_name: str, get_value_func) -> Optional[TrendAnalysis]:
        """
        分析单个指标趋势
        
        Args:
            metric_name: 指标名称
            get_value_func: 获取值的函数
            
        Returns:
            趋势分析结果
        """
        years = self.get_sorted_years()
        if len(years) < 2:
            return None
        
        values = []
        for year in years:
            value = get_value_func(self.yearly_data[year])
            if value is not None:
                values.append((year, value))
        
        if len(values) < 2:
            return None
        
        numeric_values = [v[1] for v in values]
        
        change_rates = self.calculate_change_rates(numeric_values)
        avg_change_rate = sum(change_rates) / len(change_rates) if change_rates else None
        
        cagr = self.calculate_cagr(numeric_values, len(values) - 1)
        
        volatility = self.calculate_volatility(numeric_values)
        
        if volatility and volatility > 0.2:
            direction = TrendDirection.VOLATILE
        elif avg_change_rate and avg_change_rate > 0.05:
            direction = TrendDirection.UP
        elif avg_change_rate and avg_change_rate < -0.05:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.STABLE
        
        anomalies = self.detect_anomalies(values)
        
        return TrendAnalysis(
            metric_name=metric_name,
            values=values,
            direction=direction,
            cagr=cagr,
            avg_change_rate=avg_change_rate,
            volatility=volatility,
            anomalies=anomalies
        )
    
    def analyze_trends(self) -> Dict[str, TrendAnalysis]:
        """
        分析所有指标趋势
        
        Returns:
            趋势分析结果字典
        """
        metrics = {
            '营业收入': lambda d: d.revenue,
            '毛利润': lambda d: d.gross_profit,
            '净利润': lambda d: d.net_profit,
            '扣非净利润': lambda d: d.deducted_profit,
            '经营现金流': lambda d: d.operating_cash_flow,
            '总资产': lambda d: d.total_assets,
            '净资产': lambda d: d.net_assets,
            '毛利率': lambda d: d.gross_margin,
            '净利率': lambda d: d.net_margin,
            'ROE': lambda d: d.roe,
            'ROA': lambda d: d.roa,
            '资产周转率': lambda d: d.asset_turnover,
            '杠杆率': lambda d: d.leverage_ratio,
            '现金流/净利润': lambda d: d.cash_to_profit,
            '应收账款/营收': lambda d: d.ar_to_revenue,
            '存货/营收': lambda d: d.inventory_to_revenue,
            '资产负债率': lambda d: d.liability_ratio
        }
        
        trends = {}
        for metric_name, get_func in metrics.items():
            trend = self.analyze_metric_trend(metric_name, get_func)
            if trend:
                trends[metric_name] = trend
        
        return trends
    
    def evaluate_trend_quality(self, trend: TrendAnalysis) -> ChangeLevel:
        """
        评估趋势质量
        
        Args:
            trend: 趋势分析结果
            
        Returns:
            变化程度评级
        """
        metric_name = trend.metric_name
        
        good_up_metrics = ['营业收入', '净利润', '扣非净利润', '经营现金流', '净资产', 'ROE', 'ROA']
        good_down_metrics = ['应收账款/营收', '存货/营收', '资产负债率']
        stable_metrics = ['毛利率', '净利率', '现金流/净利润']
        
        if metric_name in good_up_metrics:
            if trend.direction == TrendDirection.UP and trend.cagr and trend.cagr > 0.1:
                return ChangeLevel.EXCELLENT
            elif trend.direction == TrendDirection.UP:
                return ChangeLevel.GOOD
            elif trend.direction == TrendDirection.STABLE:
                return ChangeLevel.NORMAL
            else:
                return ChangeLevel.WARNING
        
        elif metric_name in good_down_metrics:
            if trend.direction == TrendDirection.DOWN:
                return ChangeLevel.GOOD
            elif trend.direction == TrendDirection.STABLE:
                return ChangeLevel.NORMAL
            else:
                return ChangeLevel.WARNING
        
        elif metric_name in stable_metrics:
            if trend.direction == TrendDirection.STABLE:
                return ChangeLevel.EXCELLENT
            elif trend.volatility and trend.volatility < 0.1:
                return ChangeLevel.GOOD
            else:
                return ChangeLevel.NORMAL
        
        return ChangeLevel.NORMAL
    
    def generate_comparison_report(self) -> str:
        """
        生成对比分析报告
        
        Returns:
            报告文本
        """
        years = self.get_sorted_years()
        if len(years) < 2:
            return "数据不足，至少需要2年的数据才能进行对比分析"
        
        trends = self.analyze_trends()
        
        report_lines = [
            f"# {self.company_name} 多年历史数据对比分析报告",
            "",
            f"## 分析期间：{years[0]}年 - {years[-1]}年（共{len(years)}年）",
            "",
            "## 一、核心指标趋势分析",
            ""
        ]
        
        core_metrics = ['营业收入', '净利润', 'ROE', '毛利率', '经营现金流']
        
        for metric in core_metrics:
            if metric in trends:
                trend = trends[metric]
                quality = self.evaluate_trend_quality(trend)
                
                report_lines.append(f"### {metric}")
                report_lines.append("")
                report_lines.append(f"- **趋势方向**：{trend.direction.value}")
                
                if trend.cagr is not None:
                    report_lines.append(f"- **复合增长率(CAGR)**：{trend.cagr*100:.2f}%")
                
                if trend.avg_change_rate is not None:
                    report_lines.append(f"- **平均年变化率**：{trend.avg_change_rate*100:.2f}%")
                
                if trend.volatility is not None:
                    report_lines.append(f"- **波动率**：{trend.volatility*100:.2f}%")
                
                report_lines.append(f"- **质量评级**：{quality.value}")
                
                if trend.anomalies:
                    report_lines.append("")
                    report_lines.append("**异常变化**：")
                    for anomaly in trend.anomalies:
                        report_lines.append(f"  - {anomaly['year']}年：{anomaly['type']} {abs(anomaly['change_rate'])*100:.1f}%")
                
                report_lines.append("")
        
        report_lines.extend([
            "## 二、年度数据对比表",
            ""
        ])
        
        report_lines.append("| 年份 | 营业收入 | 净利润 | ROE | 毛利率 | 经营现金流 |")
        report_lines.append("|------|----------|--------|-----|--------|------------|")
        
        for year in years:
            data = self.yearly_data[year]
            revenue = f"{data.revenue:.2f}" if data.revenue else "-"
            net_profit = f"{data.net_profit:.2f}" if data.net_profit else "-"
            roe = f"{data.roe*100:.2f}%" if data.roe else "-"
            gross_margin = f"{data.gross_margin*100:.2f}%" if data.gross_margin else "-"
            ocf = f"{data.operating_cash_flow:.2f}" if data.operating_cash_flow else "-"
            
            report_lines.append(f"| {year} | {revenue} | {net_profit} | {roe} | {gross_margin} | {ocf} |")
        
        report_lines.append("")
        
        report_lines.extend([
            "## 三、唐朝三问验证（多年视角）",
            ""
        ])
        
        report_lines.append("### 1. 这个生意赚钱吗？")
        report_lines.append("")
        
        if 'ROE' in trends:
            roe_trend = trends['ROE']
            roe_values = [v[1] for v in roe_trend.values]
            avg_roe = sum(roe_values) / len(roe_values)
            min_roe = min(roe_values)
            
            if avg_roe >= 0.3:
                roe_eval = "顶级（平均ROE≥30%）"
            elif avg_roe >= 0.2:
                roe_eval = "优秀（平均ROE≥20%）"
            elif avg_roe >= 0.15:
                roe_eval = "良好（平均ROE≥15%）"
            else:
                roe_eval = "一般（平均ROE<15%）"
            
            report_lines.append(f"- 平均ROE：{avg_roe*100:.2f}% - {roe_eval}")
            report_lines.append(f"- 最低ROE：{min_roe*100:.2f}%")
            report_lines.append(f"- ROE稳定性：{'稳定' if roe_trend.volatility and roe_trend.volatility < 0.1 else '波动'}")
        
        report_lines.append("")
        report_lines.append("### 2. 赚的是真钱吗？")
        report_lines.append("")
        
        if '现金流/净利润' in trends:
            cash_trend = trends['现金流/净利润']
            cash_values = [v[1] for v in cash_trend.values]
            avg_cash_ratio = sum(cash_values) / len(cash_values)
            years_above_1 = sum(1 for v in cash_values if v >= 1)
            
            if avg_cash_ratio >= 1:
                cash_eval = "优秀（现金流充沛）"
            elif avg_cash_ratio >= 0.8:
                cash_eval = "良好"
            else:
                cash_eval = "警告（现金流不足）"
            
            report_lines.append(f"- 平均现金流/净利润：{avg_cash_ratio:.2f} - {cash_eval}")
            report_lines.append(f"- 现金流≥净利润的年数：{years_above_1}/{len(cash_values)}年")
        
        report_lines.append("")
        report_lines.append("### 3. 能持续赚钱吗？")
        report_lines.append("")
        
        sustainability_indicators = []
        
        if '毛利率' in trends:
            gm_trend = trends['毛利率']
            gm_values = [v[1] for v in gm_trend.values]
            avg_gm = sum(gm_values) / len(gm_values)
            sustainability_indicators.append(f"- 平均毛利率：{avg_gm*100:.2f}% {'（高盈利能力）' if avg_gm > 0.4 else ''}")
        
        if '营业收入' in trends:
            rev_trend = trends['营业收入']
            if rev_trend.direction == TrendDirection.UP:
                sustainability_indicators.append(f"- 营收趋势：持续增长（CAGR: {rev_trend.cagr*100:.2f}%）")
            else:
                sustainability_indicators.append(f"- 营收趋势：{rev_trend.direction.value}")
        
        report_lines.extend(sustainability_indicators)
        
        report_lines.append("")
        report_lines.extend([
            "## 四、风险提示",
            ""
        ])
        
        risk_count = 0
        
        for metric, trend in trends.items():
            if trend.anomalies:
                risk_count += 1
                for anomaly in trend.anomalies:
                    report_lines.append(f"- {metric}在{anomaly['year']}年出现{anomaly['type']}（{abs(anomaly['change_rate'])*100:.1f}%），需关注原因")
        
        if risk_count == 0:
            report_lines.append("- 未发现重大异常变化")
        
        report_lines.append("")
        report_lines.extend([
            "---",
            f"*报告生成时间：{self._get_current_time()}*"
        ])
        
        return "\n".join(report_lines)
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def export_data(self, filepath: str) -> None:
        """
        导出数据到JSON文件
        
        Args:
            filepath: 文件路径
        """
        data = {
            'company_name': self.company_name,
            'yearly_data': {str(year): data.to_dict() for year, data in self.yearly_data.items()}
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_data(self, filepath: str) -> None:
        """
        从JSON文件导入数据
        
        Args:
            filepath: 文件路径
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.company_name = data.get('company_name', self.company_name)
        
        for year_str, year_data in data.get('yearly_data', {}).items():
            self.add_year_data_from_dict(year_data)


def demo():
    """
    演示使用方法
    """
    analyzer = HistoricalDataAnalyzer("贵州茅台")
    
    analyzer.add_year_data(YearlyData(
        year=2019,
        revenue=854.3,
        gross_profit=781.2,
        net_profit=412.1,
        deducted_profit=410.5,
        operating_cash_flow=452.1,
        total_assets=1830.4,
        net_assets=1288.5,
        accounts_receivable=0.5,
        inventory=252.8,
        total_liabilities=541.9
    ))
    
    analyzer.add_year_data(YearlyData(
        year=2020,
        revenue=949.2,
        gross_profit=875.3,
        net_profit=466.9,
        deducted_profit=470.2,
        operating_cash_flow=516.7,
        total_assets=2138.5,
        net_assets=1482.3,
        accounts_receivable=0.3,
        inventory=288.7,
        total_liabilities=656.2
    ))
    
    analyzer.add_year_data(YearlyData(
        year=2021,
        revenue=1061.9,
        gross_profit=975.8,
        net_profit=524.6,
        deducted_profit=525.8,
        operating_cash_flow=640.3,
        total_assets=2551.7,
        net_assets=1752.1,
        accounts_receivable=0.2,
        inventory=333.5,
        total_liabilities=799.6
    ))
    
    analyzer.add_year_data(YearlyData(
        year=2022,
        revenue=1240.9,
        gross_profit=1145.2,
        net_profit=627.2,
        deducted_profit=628.5,
        operating_cash_flow=695.2,
        total_assets=2852.4,
        net_assets=2048.3,
        accounts_receivable=0.2,
        inventory=388.2,
        total_liabilities=804.1
    ))
    
    analyzer.add_year_data(YearlyData(
        year=2023,
        revenue=1505.6,
        gross_profit=1382.3,
        net_profit=747.3,
        deducted_profit=745.2,
        operating_cash_flow=801.5,
        total_assets=3185.6,
        net_assets=2345.7,
        accounts_receivable=0.3,
        inventory=442.8,
        total_liabilities=839.9
    ))
    
    report = analyzer.generate_comparison_report()
    print(report)
    
    analyzer.export_data("./maotai_historical_data.json")


if __name__ == "__main__":
    demo()
