#!/usr/bin/env python3
"""
财务比率分析工具
基于唐朝投资思想，实现企业财务比率的自动化计算
支持盈利能力、偿债能力、运营能力、成长能力分析
"""


def calculate_profitability_ratios(revenue, gross_profit, net_profit, total_assets, equity):
    """
    计算盈利能力比率
    
    Args:
        revenue (float): 营业收入
        gross_profit (float): 毛利润
        net_profit (float): 净利润（扣除非经常性损益后）
        total_assets (float): 总资产
        equity (float): 所有者权益
    
    Returns:
        dict: 盈利能力比率
    """
    gross_margin = gross_profit / revenue if revenue > 0 else 0
    net_margin = net_profit / revenue if revenue > 0 else 0
    roa = net_profit / total_assets if total_assets > 0 else 0
    roe = net_profit / equity if equity > 0 else 0
    
    return {
        "毛利率": gross_margin,
        "净利率": net_margin,
        "总资产收益率（ROA）": roa,
        "净资产收益率（ROE）": roe
    }


def calculate_solvency_ratios(total_assets, total_liabilities, current_assets, current_liabilities, 
                           cash_equivalents, short_term_debt, ebit, interest_expense):
    """
    计算偿债能力比率
    
    Args:
        total_assets (float): 总资产
        total_liabilities (float): 总负债
        current_assets (float): 流动资产
        current_liabilities (float): 流动负债
        cash_equivalents (float): 货币资金
        short_term_debt (float): 短期债务
        ebit (float): 息税前利润
        interest_expense (float): 利息费用
    
    Returns:
        dict: 偿债能力比率
    """
    debt_to_asset = total_liabilities / total_assets if total_assets > 0 else 0
    current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
    quick_ratio = cash_equivalents / current_liabilities if current_liabilities > 0 else 0
    cash_to_short_debt = cash_equivalents / short_term_debt if short_term_debt > 0 else 0
    interest_coverage = ebit / interest_expense if interest_expense > 0 else 0
    
    return {
        "资产负债率": debt_to_asset,
        "流动比率": current_ratio,
        "速动比率": quick_ratio,
        "现金短债比": cash_to_short_debt,
        "利息保障倍数": interest_coverage
    }


def calculate_operation_ratios(revenue, accounts_receivable, inventory, total_assets):
    """
    计算运营能力比率
    
    Args:
        revenue (float): 营业收入
        accounts_receivable (float): 应收账款
        inventory (float): 存货
        total_assets (float): 总资产
    
    Returns:
        dict: 运营能力比率
    """
    ar_turnover = revenue / accounts_receivable if accounts_receivable > 0 else 0
    ar_turnover_days = 365 / ar_turnover if ar_turnover > 0 else 0
    inventory_turnover = revenue / inventory if inventory > 0 else 0
    inventory_turnover_days = 365 / inventory_turnover if inventory_turnover > 0 else 0
    asset_turnover = revenue / total_assets if total_assets > 0 else 0
    
    return {
        "应收账款周转率": ar_turnover,
        "应收账款周转天数": ar_turnover_days,
        "存货周转率": inventory_turnover,
        "存货周转天数": inventory_turnover_days,
        "总资产周转率": asset_turnover
    }


def calculate_growth_ratios(current_revenue, previous_revenue, current_net_profit, previous_net_profit, 
                          current_total_assets, previous_total_assets, current_equity, previous_equity):
    """
    计算成长能力比率
    
    Args:
        current_revenue (float): 当前期营业收入
        previous_revenue (float): 上期营业收入
        current_net_profit (float): 当前期净利润
        previous_net_profit (float): 上期净利润
        current_total_assets (float): 当前期总资产
        previous_total_assets (float): 上期总资产
        current_equity (float): 当前期所有者权益
        previous_equity (float): 上期所有者权益
    
    Returns:
        dict: 成长能力比率
    """
    revenue_growth = (current_revenue - previous_revenue) / previous_revenue if previous_revenue > 0 else 0
    net_profit_growth = (current_net_profit - previous_net_profit) / previous_net_profit if previous_net_profit > 0 else 0
    asset_growth = (current_total_assets - previous_total_assets) / previous_total_assets if previous_total_assets > 0 else 0
    equity_growth = (current_equity - previous_equity) / previous_equity if previous_equity > 0 else 0
    
    return {
        "营业收入增长率": revenue_growth,
        "净利润增长率": net_profit_growth,
        "总资产增长率": asset_growth,
        "所有者权益增长率": equity_growth
    }


def calculate_cash_flow_ratios(operating_cash_flow, net_profit, capex, total_debt):
    """
    计算现金流比率
    
    Args:
        operating_cash_flow (float): 经营活动现金流净额
        net_profit (float): 净利润
        capex (float): 资本开支
        total_debt (float): 总负债
    
    Returns:
        dict: 现金流比率
    """
    operating_cash_flow_to_net_profit = operating_cash_flow / net_profit if net_profit > 0 else 0
    free_cash_flow = operating_cash_flow - capex
    free_cash_flow_to_net_profit = free_cash_flow / net_profit if net_profit > 0 else 0
    cash_flow_coverage = operating_cash_flow / total_debt if total_debt > 0 else 0
    
    return {
        "经营活动现金流与净利润比率": operating_cash_flow_to_net_profit,
        "自由现金流": free_cash_flow,
        "自由现金流与净利润比率": free_cash_flow_to_net_profit,
        "现金流覆盖率": cash_flow_coverage
    }


def analyze_financial_health(profitability_ratios, solvency_ratios, operation_ratios, growth_ratios, cash_flow_ratios):
    """
    分析企业财务健康状况
    
    Args:
        profitability_ratios (dict): 盈利能力比率
        solvency_ratios (dict): 偿债能力比率
        operation_ratios (dict): 运营能力比率
        growth_ratios (dict): 成长能力比率
        cash_flow_ratios (dict): 现金流比率
    
    Returns:
        dict: 财务健康状况分析
    """
    score = 0
    
    roe = profitability_ratios.get("净资产收益率（ROE）", 0)
    net_margin = profitability_ratios.get("净利率", 0)
    
    if roe > 0.2:
        score += 15
    elif roe > 0.15:
        score += 12
    elif roe > 0.1:
        score += 9
    elif roe > 0.05:
        score += 6
    
    if net_margin > 0.2:
        score += 15
    elif net_margin > 0.15:
        score += 12
    elif net_margin > 0.1:
        score += 9
    elif net_margin > 0.05:
        score += 6
    
    debt_to_asset = solvency_ratios.get("资产负债率", 0)
    current_ratio = solvency_ratios.get("流动比率", 0)
    cash_to_short_debt = solvency_ratios.get("现金短债比", 0)
    
    if debt_to_asset < 0.5:
        score += 10
    elif debt_to_asset < 0.6:
        score += 8
    elif debt_to_asset < 0.7:
        score += 6
    
    if current_ratio > 1.5:
        score += 8
    elif current_ratio > 1.2:
        score += 6
    elif current_ratio > 1:
        score += 4
    
    if cash_to_short_debt > 1:
        score += 7
    elif cash_to_short_debt > 0.8:
        score += 5
    elif cash_to_short_debt > 0.5:
        score += 3
    
    ar_turnover_days = operation_ratios.get("应收账款周转天数", 0)
    inventory_turnover_days = operation_ratios.get("存货周转天数", 0)
    
    if ar_turnover_days < 30:
        score += 10
    elif ar_turnover_days < 60:
        score += 8
    elif ar_turnover_days < 90:
        score += 6
    
    if inventory_turnover_days < 60:
        score += 10
    elif inventory_turnover_days < 90:
        score += 8
    elif inventory_turnover_days < 120:
        score += 6
    
    revenue_growth = growth_ratios.get("营业收入增长率", 0)
    net_profit_growth = growth_ratios.get("净利润增长率", 0)
    
    if revenue_growth > 0.2:
        score += 8
    elif revenue_growth > 0.1:
        score += 6
    elif revenue_growth > 0.05:
        score += 4
    
    if net_profit_growth > 0.2:
        score += 7
    elif net_profit_growth > 0.1:
        score += 5
    elif net_profit_growth > 0.05:
        score += 3
    
    operating_cash_flow_to_net_profit = cash_flow_ratios.get("经营活动现金流与净利润比率", 0)
    free_cash_flow = cash_flow_ratios.get("自由现金流", 0)
    
    if operating_cash_flow_to_net_profit > 1:
        score += 5
    elif operating_cash_flow_to_net_profit > 0.8:
        score += 4
    elif operating_cash_flow_to_net_profit > 0.5:
        score += 3
    
    if free_cash_flow > 0:
        score += 5
    elif free_cash_flow > -100000000:
        score += 3
    
    if score >= 90:
        health_status = "优秀"
    elif score >= 80:
        health_status = "良好"
    elif score >= 70:
        health_status = "一般"
    elif score >= 60:
        health_status = "较差"
    else:
        health_status = "差"
    
    return {
        "财务健康评分": score,
        "财务健康状况": health_status
    }


def print_financial_ratios(ratios, title):
    """
    打印财务比率
    
    Args:
        ratios (dict): 财务比率
        title (str): 标题
    """
    print(f"\n===== {title} =====")
    for key, value in ratios.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
    print("====================\n")


if __name__ == "__main__":
    """
    示例用法
    """
    print("示例1：贵州茅台财务比率分析")
    
    maotai_data = {
        "revenue": 1241.0,
        "gross_profit": 1120.0,
        "net_profit": 750.0,
        "total_assets": 2500.0,
        "equity": 2000.0,
        "total_liabilities": 500.0,
        "current_assets": 1800.0,
        "current_liabilities": 300.0,
        "cash_equivalents": 1500.0,
        "short_term_debt": 0.0,
        "ebit": 850.0,
        "interest_expense": 0.0,
        "accounts_receivable": 10.0,
        "inventory": 300.0,
        "operating_cash_flow": 800.0,
        "capex": 50.0,
        "total_debt": 0.0,
        "previous_revenue": 1100.0,
        "previous_net_profit": 680.0,
        "previous_total_assets": 2200.0,
        "previous_equity": 1800.0
    }
    
    maotai_profitability = calculate_profitability_ratios(
        maotai_data["revenue"],
        maotai_data["gross_profit"],
        maotai_data["net_profit"],
        maotai_data["total_assets"],
        maotai_data["equity"]
    )
    
    maotai_solvency = calculate_solvency_ratios(
        maotai_data["total_assets"],
        maotai_data["total_liabilities"],
        maotai_data["current_assets"],
        maotai_data["current_liabilities"],
        maotai_data["cash_equivalents"],
        maotai_data["short_term_debt"],
        maotai_data["ebit"],
        maotai_data["interest_expense"]
    )
    
    maotai_operation = calculate_operation_ratios(
        maotai_data["revenue"],
        maotai_data["accounts_receivable"],
        maotai_data["inventory"],
        maotai_data["total_assets"]
    )
    
    maotai_growth = calculate_growth_ratios(
        maotai_data["revenue"],
        maotai_data["previous_revenue"],
        maotai_data["net_profit"],
        maotai_data["previous_net_profit"],
        maotai_data["total_assets"],
        maotai_data["previous_total_assets"],
        maotai_data["equity"],
        maotai_data["previous_equity"]
    )
    
    maotai_cash_flow = calculate_cash_flow_ratios(
        maotai_data["operating_cash_flow"],
        maotai_data["net_profit"],
        maotai_data["capex"],
        maotai_data["total_debt"]
    )
    
    print_financial_ratios(maotai_profitability, "盈利能力比率")
    print_financial_ratios(maotai_solvency, "偿债能力比率")
    print_financial_ratios(maotai_operation, "运营能力比率")
    print_financial_ratios(maotai_growth, "成长能力比率")
    print_financial_ratios(maotai_cash_flow, "现金流比率")
    
    maotai_health = analyze_financial_health(
        maotai_profitability,
        maotai_solvency,
        maotai_operation,
        maotai_growth,
        maotai_cash_flow
    )
    
    print("===== 财务健康状况分析 =====")
    for key, value in maotai_health.items():
        print(f"{key}: {value}")
    print("============================\n")