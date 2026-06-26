#!/usr/bin/env python3
"""
自由现金流折现计算器
基于唐朝投资思想，实现企业内在价值的自动化计算
支持稳定成长型、周期性、成长型企业的估值
"""

import math


def calculate_fcf(operating_cash_flow, capex=0):
    """
    计算自由现金流（FCF）
    
    自由现金流 = 经营活动现金流量净额 - 资本开支
    
    注意：分红是对股东的回报，不应从自由现金流中扣除。
    分红是自由现金流的使用方式之一，而不是经营的必要支出。
    
    Args:
        operating_cash_flow (float): 经营活动现金流量净额
        capex (float): 资本开支（购建固定资产、无形资产支付的现金）
    
    Returns:
        float: 自由现金流
    """
    return operating_cash_flow - capex


def calculate_intrinsic_value(fcf, growth_rate, years, perpetual_growth_rate, discount_rate):
    """
    计算企业内在价值
    
    Args:
        fcf (float): 基准年自由现金流
        growth_rate (float): 预测期增长率
        years (int): 预测期年限
        perpetual_growth_rate (float): 永续增长率
        discount_rate (float): 折现率
    
    Returns:
        float: 企业内在价值
    """
    # 计算预测期现值
    forecast_value = 0
    for i in range(1, years + 1):
        # 第i年的自由现金流
        year_fcf = fcf * (1 + growth_rate) ** i
        # 折现到基准年
        present_value = year_fcf / (1 + discount_rate) ** i
        forecast_value += present_value
    
    # 计算永续期现值
    # 预测期最后一年的自由现金流
    final_year_fcf = fcf * (1 + growth_rate) ** years
    # 永续期第一年的自由现金流
    perpetual_fcf = final_year_fcf * (1 + perpetual_growth_rate)
    # 永续期价值（使用戈登增长模型）
    perpetual_value = perpetual_fcf / (discount_rate - perpetual_growth_rate)
    # 折现到基准年
    perpetual_present_value = perpetual_value / (1 + discount_rate) ** years
    
    # 内在价值 = 预测期现值 + 永续期现值
    intrinsic_value = forecast_value + perpetual_present_value
    
    return intrinsic_value


def calculate_share_intrinsic_value(intrinsic_value, shares_outstanding):
    """
    计算每股内在价值
    
    Args:
        intrinsic_value (float): 企业内在价值
        shares_outstanding (float): 总股本
    
    Returns:
        float: 每股内在价值
    """
    return intrinsic_value / shares_outstanding


def calculate_buy_price(share_intrinsic_value, margin=0.5):
    """
    计算买入价格（内在价值的50%）
    
    Args:
        share_intrinsic_value (float): 每股内在价值
        margin (float): 安全边际比例（默认0.5，即50%）
    
    Returns:
        float: 买入价格
    """
    return share_intrinsic_value * margin


def calculate_sell_price(share_intrinsic_value, margin=1.5):
    """
    计算卖出价格（内在价值的150%）
    
    Args:
        share_intrinsic_value (float): 每股内在价值
        margin (float): 高估卖出比例（默认1.5，即150%）
    
    Returns:
        float: 卖出价格
    """
    return share_intrinsic_value * margin


def valuate_stable_growth_company(operating_cash_flow, capex=0, years=10, growth_rate=0.1, 
                               perpetual_growth_rate=0.03, discount_rate=0.1, shares_outstanding=1,
                               buy_margin=0.5, sell_margin=1.5):
    """
    估值稳定成长型企业（如茅台）
    
    Args:
        operating_cash_flow (float): 经营活动现金流量净额
        capex (float): 资本开支（默认0）
        years (int): 预测期年限（默认10）
        growth_rate (float): 预测期增长率（默认0.1，10%）
        perpetual_growth_rate (float): 永续增长率（默认0.03，3%）
        discount_rate (float): 折现率（默认0.1，10%）
        shares_outstanding (float): 总股本（默认1）
        buy_margin (float): 买入安全边际（默认0.5，即50%）
        sell_margin (float): 卖出高估比例（默认1.5，即150%）
    
    Returns:
        dict: 估值结果
    """
    fcf = calculate_fcf(operating_cash_flow, capex)
    
    intrinsic_value = calculate_intrinsic_value(fcf, growth_rate, years, 
                                             perpetual_growth_rate, discount_rate)
    
    share_intrinsic_value = calculate_share_intrinsic_value(intrinsic_value, shares_outstanding)
    
    buy_price = calculate_buy_price(share_intrinsic_value, buy_margin)
    sell_price = calculate_sell_price(share_intrinsic_value, sell_margin)
    
    return {
        "企业类型": "稳定成长型",
        "基准年经营现金流": operating_cash_flow,
        "资本开支": capex,
        "基准年自由现金流": fcf,
        "预测期年限": years,
        "预测期增长率": growth_rate,
        "永续增长率": perpetual_growth_rate,
        "折现率": discount_rate,
        "总股本": shares_outstanding,
        "企业内在价值": intrinsic_value,
        "每股内在价值": share_intrinsic_value,
        "买入价格": buy_price,
        "卖出价格": sell_price
    }


def valuate_cyclical_company(operating_cash_flow, capex=0, years=7, growth_rate=0.05, 
                            perpetual_growth_rate=0.03, discount_rate=0.1, shares_outstanding=1):
    """
    估值周期性企业（如银行）
    
    Args:
        operating_cash_flow (float): 经营活动现金流量净额
        capex (float): 资本开支（默认0）
        years (int): 预测期年限（默认7）
        growth_rate (float): 预测期增长率（默认0.05，5%）
        perpetual_growth_rate (float): 永续增长率（默认0.03，3%）
        discount_rate (float): 折现率（默认0.1，10%）
        shares_outstanding (float): 总股本（默认1）
    
    Returns:
        dict: 估值结果
    """
    fcf = calculate_fcf(operating_cash_flow, capex)
    
    intrinsic_value = calculate_intrinsic_value(fcf, growth_rate, years, 
                                             perpetual_growth_rate, discount_rate)
    
    share_intrinsic_value = calculate_share_intrinsic_value(intrinsic_value, shares_outstanding)
    
    buy_price = calculate_buy_price(share_intrinsic_value)
    sell_price = calculate_sell_price(share_intrinsic_value)
    
    return {
        "企业类型": "周期性企业",
        "基准年经营现金流": operating_cash_flow,
        "资本开支": capex,
        "基准年自由现金流": fcf,
        "预测期年限": years,
        "预测期增长率": growth_rate,
        "永续增长率": perpetual_growth_rate,
        "折现率": discount_rate,
        "总股本": shares_outstanding,
        "企业内在价值": intrinsic_value,
        "每股内在价值": share_intrinsic_value,
        "买入价格": buy_price,
        "卖出价格": sell_price
    }


def valuate_growth_company(operating_cash_flow, capex=0, years=8, growth_rate=0.15, 
                          perpetual_growth_rate=0.04, discount_rate=0.12, shares_outstanding=1):
    """
    估值成长型企业（如腾讯、宁德时代）
    
    Args:
        operating_cash_flow (float): 经营活动现金流量净额
        capex (float): 资本开支（默认0）
        years (int): 预测期年限（默认8）
        growth_rate (float): 预测期增长率（默认0.15，15%）
        perpetual_growth_rate (float): 永续增长率（默认0.04，4%）
        discount_rate (float): 折现率（默认0.12，12%，风险较高）
        shares_outstanding (float): 总股本（默认1）
    
    Returns:
        dict: 估值结果
    """
    fcf = calculate_fcf(operating_cash_flow, capex)
    
    intrinsic_value = calculate_intrinsic_value(fcf, growth_rate, years, 
                                             perpetual_growth_rate, discount_rate)
    
    share_intrinsic_value = calculate_share_intrinsic_value(intrinsic_value, shares_outstanding)
    
    buy_price = calculate_buy_price(share_intrinsic_value)
    sell_price = calculate_sell_price(share_intrinsic_value)
    
    return {
        "企业类型": "成长型企业",
        "基准年经营现金流": operating_cash_flow,
        "资本开支": capex,
        "基准年自由现金流": fcf,
        "预测期年限": years,
        "预测期增长率": growth_rate,
        "永续增长率": perpetual_growth_rate,
        "折现率": discount_rate,
        "总股本": shares_outstanding,
        "企业内在价值": intrinsic_value,
        "每股内在价值": share_intrinsic_value,
        "买入价格": buy_price,
        "卖出价格": sell_price
    }


def print_valuation_result(result):
    """
    打印估值结果
    
    Args:
        result (dict): 估值结果
    """
    print("\n===== 估值结果 =====")
    for key, value in result.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
    print("====================\n")


if __name__ == "__main__":
    """
    示例用法
    """
    # 示例1：茅台估值
    print("示例1：贵州茅台估值")
    maotai_result = valuate_stable_growth_company(
        operating_cash_flow=92464000000,  # 924.64亿元
        capex=4679000000,  # 46.79亿元
        years=10,
        growth_rate=0.1,
        perpetual_growth_rate=0.03,
        discount_rate=0.1,
        shares_outstanding=1256000000  # 12.56亿股
    )
    print_valuation_result(maotai_result)
    
    # 示例2：腾讯估值
    print("示例2：腾讯控股估值")
    tencent_result = valuate_growth_company(
        operating_cash_flow=200000000000,  # 2000亿元
        capex=30000000000,  # 300亿元
        years=8,
        growth_rate=0.15,
        perpetual_growth_rate=0.04,
        discount_rate=0.12,
        shares_outstanding=9190000000  # 91.9亿股
    )
    print_valuation_result(tencent_result)
    
    # 示例3：招商银行估值
    print("示例3：招商银行估值")
    cmb_result = valuate_cyclical_company(
        operating_cash_flow=150000000000,  # 1500亿元
        capex=20000000000,  # 200亿元
        years=7,
        growth_rate=0.08,
        perpetual_growth_rate=0.03,
        discount_rate=0.1,
        shares_outstanding=25220000000  # 252.2亿股
    )
    print_valuation_result(cmb_result)
