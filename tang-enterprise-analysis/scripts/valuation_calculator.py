#!/usr/bin/env python3
"""估值计算工具。

普通企业使用现金流折现；银行可使用剩余收益或股利折现。
所有金额与股本必须使用兼容量纲。
"""

import math


def _number(name, value, *, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name}必须是数字")
    if not math.isfinite(value):
        raise ValueError(f"{name}必须是有限数值")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name}不能小于{minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name}不能大于{maximum}")
    return float(value)


def _years(value):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("预测期年限必须是正整数")
    return value


def _growth_rate(name, value):
    value = _number(name, value)
    if value <= -1:
        raise ValueError(f"{name}必须大于-100%")
    return value


def _discount_pair(discount_rate, perpetual_growth_rate):
    discount_rate = _number("折现率", discount_rate)
    perpetual_growth_rate = _growth_rate("永续增长率", perpetual_growth_rate)
    if discount_rate <= perpetual_growth_rate:
        raise ValueError("折现率必须高于永续增长率")
    return discount_rate, perpetual_growth_rate


def calculate_fcf(operating_cash_flow, capex=0):
    """计算简化自由现金流：经营现金流减资本开支。

    该近似只适用于非金融企业，且需要另外判断营运资金和增长性资本开支。
    """
    operating_cash_flow = _number("经营现金流", operating_cash_flow)
    capex = _number("资本开支", capex, minimum=0)
    return operating_cash_flow - capex


def calculate_intrinsic_value(
    fcf, growth_rate, years, perpetual_growth_rate, discount_rate
):
    """使用恒定预测期增长率计算普通企业现金流现值。"""
    fcf = _number("基准年自由现金流", fcf)
    growth_rate = _growth_rate("预测期增长率", growth_rate)
    years = _years(years)
    discount_rate, perpetual_growth_rate = _discount_pair(
        discount_rate, perpetual_growth_rate
    )

    forecast_value = sum(
        fcf * (1 + growth_rate) ** year / (1 + discount_rate) ** year
        for year in range(1, years + 1)
    )
    final_year_fcf = fcf * (1 + growth_rate) ** years
    terminal_value = (
        final_year_fcf
        * (1 + perpetual_growth_rate)
        / (discount_rate - perpetual_growth_rate)
    )
    return forecast_value + terminal_value / (1 + discount_rate) ** years


def calculate_share_intrinsic_value(intrinsic_value, shares_outstanding):
    """计算每股内在价值。"""
    intrinsic_value = _number("股权价值", intrinsic_value)
    shares_outstanding = _number("总股本", shares_outstanding, minimum=0)
    if shares_outstanding == 0:
        raise ValueError("总股本必须大于0")
    return intrinsic_value / shares_outstanding


def calculate_buy_price(share_intrinsic_value, margin=0.5):
    """按显式安全边际乘数计算价格参考，不代表通用买入规则。"""
    share_intrinsic_value = _number("每股内在价值", share_intrinsic_value)
    margin = _number("安全边际乘数", margin, minimum=0, maximum=1)
    if margin == 0:
        raise ValueError("安全边际乘数必须大于0")
    return share_intrinsic_value * margin


def calculate_sell_price(share_intrinsic_value, margin=1.5):
    """按显式高估乘数计算价格参考，不代表自动卖出指令。"""
    share_intrinsic_value = _number("每股内在价值", share_intrinsic_value)
    margin = _number("高估乘数", margin, minimum=0)
    if margin == 0:
        raise ValueError("高估乘数必须大于0")
    return share_intrinsic_value * margin


def _valuate_company(
    enterprise_type,
    operating_cash_flow,
    capex,
    years,
    growth_rate,
    perpetual_growth_rate,
    discount_rate,
    shares_outstanding,
    buy_margin,
    sell_margin,
):
    fcf = calculate_fcf(operating_cash_flow, capex)
    intrinsic_value = calculate_intrinsic_value(
        fcf, growth_rate, years, perpetual_growth_rate, discount_rate
    )
    share_value = calculate_share_intrinsic_value(
        intrinsic_value, shares_outstanding
    )
    return {
        "企业类型": enterprise_type,
        "模型": "简化自由现金流折现",
        "基准年经营现金流": operating_cash_flow,
        "资本开支": capex,
        "基准年自由现金流": fcf,
        "预测期年限": years,
        "预测期增长率": growth_rate,
        "永续增长率": perpetual_growth_rate,
        "折现率": discount_rate,
        "总股本": shares_outstanding,
        "企业内在价值": intrinsic_value,
        "每股内在价值": share_value,
        "安全边际价格参考": calculate_buy_price(share_value, buy_margin),
        "高估价格参考": calculate_sell_price(share_value, sell_margin),
        "限制": "不适用于银行、保险和券商；价格参考不是交易指令",
    }


def valuate_stable_growth_company(
    operating_cash_flow,
    capex=0,
    years=10,
    growth_rate=0.1,
    perpetual_growth_rate=0.03,
    discount_rate=0.1,
    shares_outstanding=1,
    buy_margin=0.5,
    sell_margin=1.5,
):
    """估值现金流相对稳定的普通非金融企业。"""
    return _valuate_company(
        "稳定成长型非金融企业",
        operating_cash_flow,
        capex,
        years,
        growth_rate,
        perpetual_growth_rate,
        discount_rate,
        shares_outstanding,
        buy_margin,
        sell_margin,
    )


def valuate_cyclical_company(
    operating_cash_flow,
    capex=0,
    years=7,
    growth_rate=0.05,
    perpetual_growth_rate=0.02,
    discount_rate=0.12,
    shares_outstanding=1,
    buy_margin=0.5,
    sell_margin=1.5,
):
    """估值使用周期中枢现金流的普通周期企业，不适用于金融企业。"""
    return _valuate_company(
        "周期型非金融企业",
        operating_cash_flow,
        capex,
        years,
        growth_rate,
        perpetual_growth_rate,
        discount_rate,
        shares_outstanding,
        buy_margin,
        sell_margin,
    )


def valuate_growth_company(
    operating_cash_flow,
    capex=0,
    years=8,
    growth_rate=0.15,
    perpetual_growth_rate=0.03,
    discount_rate=0.12,
    shares_outstanding=1,
    buy_margin=0.5,
    sell_margin=1.5,
):
    """估值现金流可预测的成长型普通非金融企业。"""
    return _valuate_company(
        "成长型非金融企业",
        operating_cash_flow,
        capex,
        years,
        growth_rate,
        perpetual_growth_rate,
        discount_rate,
        shares_outstanding,
        buy_margin,
        sell_margin,
    )


def valuate_bank_residual_income(
    book_value,
    roe,
    cost_of_equity,
    years=5,
    payout_ratio=0.3,
    terminal_roe=None,
    terminal_growth_rate=0.03,
    shares_outstanding=1,
):
    """使用简化剩余收益模型估算银行普通股价值。

    book_value为当前普通股净资产。模型假设预测期ROE和分红率恒定；
    实务中应按年度输入并结合资产质量、信用成本和监管资本复核。
    """
    book_value = _number("普通股净资产", book_value, minimum=0)
    if book_value == 0:
        raise ValueError("普通股净资产必须大于0")
    roe = _number("预测期ROE", roe)
    cost_of_equity = _number("股权成本", cost_of_equity, minimum=0)
    years = _years(years)
    payout_ratio = _number("分红率", payout_ratio, minimum=0, maximum=1)
    terminal_roe = roe if terminal_roe is None else _number("终值ROE", terminal_roe)
    cost_of_equity, terminal_growth_rate = _discount_pair(
        cost_of_equity, terminal_growth_rate
    )

    current_book = book_value
    residual_income_pv = 0.0
    for year in range(1, years + 1):
        earnings = current_book * roe
        residual_income = earnings - current_book * cost_of_equity
        residual_income_pv += residual_income / (1 + cost_of_equity) ** year
        current_book += earnings * (1 - payout_ratio)

    next_terminal_book = current_book * (1 + terminal_growth_rate)
    terminal_residual_income = next_terminal_book * (
        terminal_roe - cost_of_equity
    )
    terminal_value = terminal_residual_income / (
        cost_of_equity - terminal_growth_rate
    )
    equity_value = (
        book_value
        + residual_income_pv
        + terminal_value / (1 + cost_of_equity) ** years
    )
    share_value = calculate_share_intrinsic_value(equity_value, shares_outstanding)
    return {
        "企业类型": "银行",
        "模型": "简化剩余收益模型",
        "当前普通股净资产": book_value,
        "预测期ROE": roe,
        "终值ROE": terminal_roe,
        "股权成本": cost_of_equity,
        "分红率": payout_ratio,
        "预测期年限": years,
        "永续增长率": terminal_growth_rate,
        "股权价值": equity_value,
        "每股内在价值": share_value,
        "限制": "必须结合资产质量、信用成本和监管资本做情景分析",
    }


def calculate_dividend_discount_value(
    current_dividend,
    growth_rate,
    cost_of_equity,
    shares_outstanding=1,
):
    """计算稳定增长股利折现价值，仅适用于可持续分红。"""
    current_dividend = _number("当前年度股利", current_dividend, minimum=0)
    cost_of_equity, growth_rate = _discount_pair(cost_of_equity, growth_rate)
    equity_value = current_dividend * (1 + growth_rate) / (
        cost_of_equity - growth_rate
    )
    return {
        "模型": "稳定增长股利折现",
        "股权价值": equity_value,
        "每股内在价值": calculate_share_intrinsic_value(
            equity_value, shares_outstanding
        ),
        "限制": "仅适用于分红政策稳定且资本充足的金融企业",
    }


def print_valuation_result(result):
    """打印估值结果。"""
    print("\n===== 估值结果 =====")
    for key, value in result.items():
        print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
    print("====================\n")


if __name__ == "__main__":
    print("示例1：稳定成长型非金融企业")
    print_valuation_result(
        valuate_stable_growth_company(
            operating_cash_flow=100,
            capex=10,
            shares_outstanding=10,
        )
    )

    print("示例2：银行剩余收益模型")
    print_valuation_result(
        valuate_bank_residual_income(
            book_value=1000,
            roe=0.13,
            cost_of_equity=0.10,
            payout_ratio=0.3,
            terminal_roe=0.11,
            shares_outstanding=100,
        )
    )
