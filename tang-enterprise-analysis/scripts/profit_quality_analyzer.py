#!/usr/bin/env python3
"""
利润质量分析器
基于唐朝《手把手教你读财报》的核心思想
用于判断公司财报中利润是否为真、利润是否可持续等

核心方法：
1. 利润真实性判断：经营现金流与净利润对比、现金流检验
2. 利润可持续性判断：扣非净利润占比、主营业务占比
3. 排除地雷：应收账款异常、存货异常、现金流异常等
"""


def analyze_profit_authenticity(revenue, net_profit, operating_cash_flow, 
                               cash_from_sales, accounts_receivable, 
                               previous_accounts_receivable=None,
                               inventory=None, previous_inventory=None):
    """
    分析利润的真实性（利润是否为真）
    
    唐朝的核心观点：利润必须由经营活动产生的现金支撑
    
    Args:
        revenue (float): 营业收入（元）
        net_profit (float): 净利润（元）
        operating_cash_flow (float): 经营活动现金流净额（元）
        cash_from_sales (float): 销售商品、提供劳务收到的现金（元）
        accounts_receivable (float): 应收账款余额（元）
        previous_accounts_receivable (float, optional): 上期应收账款余额（元）
        inventory (float, optional): 存货余额（元）
        previous_inventory (float, optional): 上期存货余额（元）
    
    Returns:
        dict: 利润真实性分析结果
    """
    result = {
        "评分": 0,
        "评级": "",
        "风险点": [],
        "正面信号": [],
        "详细指标": {}
    }
    
    max_score = 100
    
    # 1. 经营现金流净额 vs 净利润（最重要的指标，权重30分）
    # 理想情况：经营现金流 > 净利润的1.2倍
    ocf_to_profit_ratio = operating_cash_flow / net_profit if net_profit > 0 else 0
    result["详细指标"]["经营现金流/净利润"] = ocf_to_profit_ratio
    
    if ocf_to_profit_ratio >= 1.2:
        result["评分"] += 30
        result["正面信号"].append("经营现金流净额远超净利润，利润质量优秀")
    elif ocf_to_profit_ratio >= 1.0:
        result["评分"] += 25
        result["正面信号"].append("经营现金流净额大于净利润，利润质量良好")
    elif ocf_to_profit_ratio >= 0.8:
        result["评分"] += 18
        result["正面信号"].append("经营现金流净额接近净利润，利润质量尚可")
    elif ocf_to_profit_ratio >= 0.5:
        result["评分"] += 10
        result["风险点"].append("经营现金流净额低于净利润，需要关注")
    elif ocf_to_profit_ratio > 0:
        result["评分"] += 5
        result["风险点"].append("经营现金流净额远低于净利润，利润可能有水分")
    else:
        result["风险点"].append("经营现金流为负，利润真实性存疑！")
    
    # 2. 销售商品收到的现金 vs 营业收入（权重20分）
    # 理想情况：销售现金 > 营业收入的1.1倍（含增值税）
    cash_to_revenue_ratio = cash_from_sales / revenue if revenue > 0 else 0
    result["详细指标"]["销售商品现金/营业收入"] = cash_to_revenue_ratio
    
    if cash_to_revenue_ratio >= 1.1:
        result["评分"] += 20
        result["正面信号"].append("销售商品收到的现金远超营业收入，营业收入真实可靠")
    elif cash_to_revenue_ratio >= 1.0:
        result["评分"] += 16
        result["正面信号"].append("销售商品收到的现金大于营业收入，营业收入质量好")
    elif cash_to_revenue_ratio >= 0.9:
        result["评分"] += 12
        result["正面信号"].append("销售商品收到的现金接近营业收入，营业收入质量尚可")
    elif cash_to_revenue_ratio >= 0.8:
        result["评分"] += 6
        result["风险点"].append("销售商品收到的现金低于营业收入，需要关注")
    else:
        result["风险点"].append("销售商品收到的现金远低于营业收入，收入质量差！")
    
    # 3. 应收账款变化情况（权重20分）
    # 警惕：应收账款大幅增加且增幅超过营收增幅
    if previous_accounts_receivable and previous_accounts_receivable > 0:
        ar_growth = (accounts_receivable - previous_accounts_receivable) / previous_accounts_receivable
        revenue_growth = (revenue - (revenue * 0.9)) / (revenue * 0.9) if revenue > 0 else 0
        result["详细指标"]["应收账款增长率"] = ar_growth
        
        # 应收账款占营业收入比例
        ar_to_revenue = accounts_receivable / revenue if revenue > 0 else 0
        result["详细指标"]["应收账款/营业收入"] = ar_to_revenue
        
        if ar_to_revenue < 0.1:
            result["评分"] += 20
            result["正面信号"].append("应收账款占营业收入比例低，收入质量高")
        elif ar_to_revenue < 0.2:
            result["评分"] += 15
            result["正面信号"].append("应收账款占营业收入比例合理")
        elif ar_to_revenue < 0.3:
            result["评分"] += 10
            result["风险点"].append("应收账款占营业收入比例较高")
        else:
            result["风险点"].append(f"应收账款占营业收入比例高达{ar_to_revenue*100:.1f}%，需要警惕！")
        
        if ar_growth > 0.3:
            result["风险点"].append(f"应收账款大幅增长{ar_growth*100:.1f}%，可能存在放宽信用政策情况")
        elif ar_growth < 0:
            result["正面信号"].append("应收账款下降，回款情况改善")
    else:
        ar_to_revenue = accounts_receivable / revenue if revenue > 0 else 0
        result["详细指标"]["应收账款/营业收入"] = ar_to_revenue
        
        if ar_to_revenue < 0.15:
            result["评分"] += 20
            result["正面信号"].append("应收账款占营业收入比例低")
        elif ar_to_revenue < 0.25:
            result["评分"] += 15
        elif ar_to_revenue < 0.35:
            result["评分"] += 10
        else:
            result["风险点"].append(f"应收账款占营业收入比例{ar_to_revenue*100:.1f}%，偏高")
    
    # 4. 存货变化情况（权重15分）
    if inventory and previous_inventory and previous_inventory > 0:
        inventory_growth = (inventory - previous_inventory) / previous_inventory
        result["详细指标"]["存货增长率"] = inventory_growth
        
        # 存货周转率相关
        inventory_to_revenue = inventory / revenue if revenue > 0 else 0
        result["详细指标"]["存货/营业收入"] = inventory_to_revenue
        
        if inventory_growth < 0:
            result["评分"] += 15
            result["正面信号"].append("存货下降，去库存效果好")
        elif inventory_growth < 0.1:
            result["评分"] += 12
            result["正面信号"].append("存货小幅增长，正常")
        elif inventory_growth < 0.2:
            result["评分"] += 8
        else:
            result["风险点"].append(f"存货大幅增长{inventory_growth*100:.1f}%，可能存在滞销或跌价风险")
    elif inventory:
        inventory_to_revenue = inventory / revenue if revenue > 0 else 0
        result["详细指标"]["存货/营业收入"] = inventory_to_revenue
        
        if inventory_to_revenue < 0.2:
            result["评分"] += 15
        elif inventory_to_revenue < 0.4:
            result["评分"] += 10
        else:
            result["风险点"].append("存货占营业收入比例较高")
    
    # 5. 经营现金流净额正负判断（权重15分）
    if operating_cash_flow > 0:
        result["评分"] += 15
        result["正面信号"].append("经营活动现金流为正，自身造血能力强")
    else:
        result["风险点"].append("经营活动现金流为负，需要外部输血！")
    
    # 评级
    if result["评分"] >= 80:
        result["评级"] = "优秀"
    elif result["评分"] >= 60:
        result["评级"] = "良好"
    elif result["评分"] >= 40:
        result["评级"] = "一般"
    elif result["评分"] >= 20:
        result["评级"] = "较差"
    else:
        result["评级"] = "差"
    
    return result


def analyze_profit_sustainability(gross_profit, revenue, net_profit, 
                                 deducted_profit,  # 扣非净利润
                                 main_business_revenue,  # 主营业务收入
                                 previous_net_profit=None,
                                 previous_deducted_profit=None):
    """
    分析利润的可持续性
    
    唐朝的核心观点：利润必须来自主营业务，必须扣非后仍盈利
    
    Args:
        gross_profit (float): 毛利润
        revenue (float): 营业收入
        net_profit (float): 净利润
        deducted_profit (float): 扣除非经常性损益后的净利润
        main_business_revenue (float): 主营业务收入
        previous_net_profit (float, optional): 上期净利润
        previous_deducted_profit (float, optional): 上期扣非净利润
    
    Returns:
        dict: 利润可持续性分析结果
    """
    result = {
        "评分": 0,
        "评级": "",
        "风险点": [],
        "正面信号": [],
        "详细指标": {}
    }
    
    max_score = 100
    
    # 1. 毛利率及稳定性（权重30分）
    gross_margin = gross_profit / revenue if revenue > 0 else 0
    result["详细指标"]["毛利率"] = gross_margin
    
    if gross_margin >= 0.4:
        result["评分"] += 30
        result["正面信号"].append(f"毛利率{gross_margin*100:.1f}%，盈利能力强")
    elif gross_margin >= 0.3:
        result["评分"] += 24
        result["正面信号"].append(f"毛利率{gross_margin*100:.1f}%，盈利能力良好")
    elif gross_margin >= 0.2:
        result["评分"] += 18
        result["正面信号"].append(f"毛利率{gross_margin*100:.1f}%，盈利能力一般")
    elif gross_margin >= 0.1:
        result["评分"] += 10
        result["风险点"].append(f"毛利率{gross_margin*100:.1f}%，盈利能力较弱")
    else:
        result["风险点"].append(f"毛利率{gross_margin*100:.1f}%，盈利能力差")
    
    # 2. 扣非净利润占比（权重30分）
    # 唐朝强调：必须关注扣非净利润，排除一次性收益
    deducted_ratio = deducted_profit / net_profit if net_profit > 0 else 0
    result["详细指标"]["扣非净利润/净利润"] = deducted_ratio
    
    if deducted_ratio >= 0.9:
        result["评分"] += 30
        result["正面信号"].append("扣非净利润接近净利润，利润质量高，无明显非经常性损益")
    elif deducted_ratio >= 0.8:
        result["评分"] += 24
        result["正面信号"].append("扣非净利润占比高，利润主要来自主营业务")
    elif deducted_ratio >= 0.6:
        result["评分"] += 18
        result["风险点"].append("扣非净利润占比一般，存在一定非经常性损益")
    elif deducted_ratio >= 0.4:
        result["评分"] += 10
        result["风险点"].append("扣非净利润占比低，大量利润来自非经常性项目")
    else:
        result["风险点"].append("扣非净利润占比很低，利润可持续性差！")
    
    # 3. 主营业务收入占比（权重20分）
    main_business_ratio = main_business_revenue / revenue if revenue > 0 else 0
    result["详细指标"]["主营业务收入/营业收入"] = main_business_ratio
    
    if main_business_ratio >= 0.95:
        result["评分"] += 20
        result["正面信号"].append("主营业务突出，收入来源集中可靠")
    elif main_business_ratio >= 0.85:
        result["评分"] += 16
        result["正面信号"].append("主营业务占比高，收入结构合理")
    elif main_business_ratio >= 0.7:
        result["评分"] += 12
        result["风险点"].append("存在一定其他业务收入，需关注")
    else:
        result["风险点"].append("主营业务占比低，收入来源分散")
    
    # 4. 净利润稳定性（权重20分）
    if previous_net_profit and previous_net_profit > 0:
        profit_change = (net_profit - previous_net_profit) / previous_net_profit
        result["详细指标"]["净利润增长率"] = profit_change
        
        if abs(profit_change) < 0.1:
            result["评分"] += 20
            result["正面信号"].append("净利润稳定")
        elif abs(profit_change) < 0.2:
            result["评分"] += 16
            result["正面信号"].append("净利润小幅变化")
        elif profit_change > 0:
            result["评分"] += 12
            result["正面信号"].append(f"净利润增长{profit_change*100:.1f}%")
        else:
            result["评分"] += 6
            result["风险点"].append(f"净利润下降{abs(profit_change)*100:.1f}%")
    else:
        # 没有历史数据，根据净利润绝对数评分
        if net_profit > 0:
            result["评分"] += 15
            result["正面信号"].append("盈利")
        else:
            result["风险点"].append("亏损状态")
    
    # 5. 扣非净利润与净利润趋势一致性（额外检查）
    if previous_deducted_profit and previous_deducted_profit > 0:
        deducted_change = (deducted_profit - previous_deducted_profit) / previous_deducted_profit
        if previous_net_profit and previous_net_profit > 0:
            profit_change = (net_profit - previous_net_profit) / previous_net_profit
            if abs(deducted_change - profit_change) > 0.2:
                result["风险点"].append("扣非净利润与净利润变化趋势不一致，需警惕利润调节")
    
    # 评级
    if result["评分"] >= 80:
        result["评级"] = "优秀（可持续性强）"
    elif result["评分"] >= 60:
        result["评级"] = "良好"
    elif result["评分"] >= 40:
        result["评级"] = "一般"
    elif result["评分"] >= 20:
        result["评级"] = "较差"
    else:
        result["评级"] = "差（可持续性弱）"
    
    return result


def scan_for_red_flags(revenue, net_profit, accounts_receivable, inventory, 
                       other_receivables, other_payables, 
                       goodwill, intangible_assets,
                       total_assets, operating_cash_flow,
                       previous_revenue=None, previous_assets=None):
    """
    扫描财报地雷（唐朝排雷方法）
    
    Args:
        revenue (float): 营业收入
        net_profit (float): 净利润
        accounts_receivable (float): 应收账款
        inventory (float): 存货
        other_receivables (float): 其他应收款（地雷高发区）
        other_payables (float): 其他应付款
        goodwill (float): 商誉（减值风险）
        intangible_assets (float): 无形资产
        total_assets (float): 总资产
        operating_cash_flow (float): 经营现金流
        previous_revenue (float, optional): 上期营业收入
        previous_assets (float, optional): 上期总资产
    
    Returns:
        dict: 地雷扫描结果
    """
    red_flags = []
    yellow_flags = []
    green_flags = []
    
    # 1. 其他应收款异常（唐朝重点提醒）
    # 其他应收款是垃圾筐，容易藏污纳垢
    or_ratio = other_receivables / total_assets if total_assets > 0 else 0
    if or_ratio > 0.1:
        red_flags.append(f"其他应收款占总资产比例过高({or_ratio*100:.1f}%)，可能存在关联方占用资金或坏账")
    elif or_ratio > 0.05:
        yellow_flags.append(f"其他应收款占比{or_ratio*100:.1f}%，需要关注")
    else:
        green_flags.append("其他应收款占比合理")
    
    # 其他应收款 vs 净利润
    if net_profit > 0 and other_receivables > net_profit * 0.5:
        red_flags.append("其他应收款金额过大，超过净利润的50%")
    
    # 2. 商誉减值风险
    goodwill_ratio = goodwill / total_assets if total_assets > 0 else 0
    if goodwill_ratio > 0.3:
        red_flags.append(f"商誉占总资产比例过高({goodwill_ratio*100:.1f}%)，存在大额减值风险")
    elif goodwill_ratio > 0.15:
        yellow_flags.append(f"商誉占比{goodwill_ratio*100:.1f}%，需关注减值风险")
    
    # 3. 应收账款异常
    if previous_revenue and previous_revenue > 0:
        revenue_growth = (revenue - previous_revenue) / previous_revenue
        if accounts_receivable > 0 and previous_revenue > 0:
            ar_ratio = accounts_receivable / revenue
            previous_ar_ratio = accounts_receivable * 0.8 / previous_revenue  # 假设上期应收账款
            if ar_ratio > previous_ar_ratio * 1.3:
                red_flags.append("应收账款增幅远超营收增幅，可能放宽信用政策或虚构收入")
    
    # 4. 经营现金流与净利润背离
    if net_profit > 0 and operating_cash_flow < 0:
        red_flags.append("盈利但经营现金流为负，典型的纸面富贵！")
    elif net_profit > 0 and operating_cash_flow / net_profit < 0.5:
        yellow_flags.append("经营现金流远低于净利润，需要深入分析原因")
    
    # 5. 存货异常
    inventory_ratio = inventory / revenue if revenue > 0 else 0
    if inventory_ratio > 0.5:
        yellow_flags.append(f"存货占营业收入比例高({inventory_ratio*100:.1f}%)，可能存在滞销")
    
    # 6. 无形资产异常（注意是否是真无形资产）
    ia_ratio = intangible_assets / total_assets if total_assets > 0 else 0
    if ia_ratio > 0.4:
        yellow_flags.append(f"无形资产占比高({ia_ratio*100:.1f}%)，需评估是否为真无形资产")
    
    # 7. 其他应付款异常
    op_ratio = other_payables / total_assets if total_assets > 0 else 0
    if op_ratio > 0.2:
        yellow_flags.append(f"其他应付款占比{op_ratio*100:.1f}%，需关注是否为关联方借款")
    
    # 8. 资产大幅变化
    if previous_assets and previous_assets > 0:
        asset_change = (total_assets - previous_assets) / previous_assets
        if abs(asset_change) > 0.5:
            yellow_flags.append(f"总资产大幅变动({asset_change*100:+.1f}%)，需了解原因")
    
    return {
        "红色警报": red_flags,
        "黄色警告": yellow_flags,
        "绿色信号": green_flags,
        "警报级别": "严重" if len(red_flags) >= 2 else "需关注" if len(red_flags) > 0 or len(yellow_flags) >= 3 else "正常"
    }


def comprehensive_profit_quality_analysis(company_name, 
                                          revenue, gross_profit, net_profit, 
                                          deducted_profit, main_business_revenue,
                                          operating_cash_flow, cash_from_sales,
                                          accounts_receivable, inventory,
                                          other_receivables, other_payables,
                                          goodwill, intangible_assets, total_assets,
                                          previous_accounts_receivable=None,
                                          previous_inventory=None,
                                          previous_net_profit=None,
                                          previous_deducted_profit=None):
    """
    综合利润质量分析（唐朝方法完整实现）
    
    Returns:
        dict: 综合分析结果
    """
    # 利润真实性分析
    authenticity = analyze_profit_authenticity(
        revenue=revenue,
        net_profit=net_profit,
        operating_cash_flow=operating_cash_flow,
        cash_from_sales=cash_from_sales,
        accounts_receivable=accounts_receivable,
        previous_accounts_receivable=previous_accounts_receivable,
        inventory=inventory,
        previous_inventory=previous_inventory
    )
    
    # 利润可持续性分析
    sustainability = analyze_profit_sustainability(
        gross_profit=gross_profit,
        revenue=revenue,
        net_profit=net_profit,
        deducted_profit=deducted_profit,
        main_business_revenue=main_business_revenue,
        previous_net_profit=previous_net_profit,
        previous_deducted_profit=previous_deducted_profit
    )
    
    # 地雷扫描
    red_flags = scan_for_red_flags(
        revenue=revenue,
        net_profit=net_profit,
        accounts_receivable=accounts_receivable,
        inventory=inventory,
        other_receivables=other_receivables,
        other_payables=other_payables,
        goodwill=goodwill,
        intangible_assets=intangible_assets,
        total_assets=total_assets,
        operating_cash_flow=operating_cash_flow
    )
    
    # 综合评分
    final_score = authenticity["评分"] * 0.5 + sustainability["评分"] * 0.5
    if final_score >= 80:
        final_rating = "优秀"
    elif final_score >= 60:
        final_rating = "良好"
    elif final_score >= 40:
        final_rating = "一般"
    else:
        final_rating = "差"
    
    return {
        "公司名称": company_name,
        "利润真实性分析": authenticity,
        "利润可持续性分析": sustainability,
        "地雷扫描": red_flags,
        "综合评分": final_score,
        "综合评级": final_rating,
        "投资建议": generate_investment_advice(authenticity, sustainability, red_flags)
    }


def generate_investment_advice(authenticity, sustainability, red_flags):
    """
    生成投资建议
    """
    advice = []
    
    if authenticity["评分"] >= 80 and sustainability["评分"] >= 80:
        advice.append("利润真实性和可持续性双优，是值得关注的好公司！")
    elif authenticity["评分"] < 40:
        advice.append("利润真实性存疑，建议谨慎回避")
    elif sustainability["评分"] < 40:
        advice.append("利润可持续性弱，不适合长期投资")
    
    if red_flags["警报级别"] == "严重":
        advice.append("发现多个红色警报，建议深入调研或回避")
    elif len(red_flags["红色警报"]) > 0:
        advice.append("存在红色警报信号，需要仔细阅读财报附注")
    
    if len(authenticity["正面信号"]) > len(authenticity["风险点"]):
        advice.append("利润真实性方面正面信号多于负面")
    
    if "经营现金流净额远超净利润" in str(authenticity["正面信号"]):
        advice.append("经营现金流充沛，是好公司的特征")
    
    if "扣非净利润接近净利润" in str(sustainability["正面信号"]):
        advice.append("利润主要来自主营业务，盈利质量高")
    
    if not advice:
        advice.append("建议进一步深入分析财报，特别是附注部分")
    
    return advice


def print_profit_quality_report(analysis_result):
    """
    打印利润质量分析报告
    """
    print("\n" + "="*70)
    print(f"利润质量分析报告 - {analysis_result['公司名称']}")
    print("="*70)
    
    # 综合评级
    print(f"\n【综合评级】：{analysis_result['综合评级']}")
    print(f"【综合评分】：{analysis_result['综合评分']:.1f}/100")
    
    # 利润真实性
    auth = analysis_result['利润真实性分析']
    print(f"\n--- 利润真实性分析 ---")
    print(f"评级：{auth['评级']}，评分：{auth['评分']}/100")
    
    if auth['正面信号']:
        print("\n【正面信号】：")
        for signal in auth['正面信号']:
            print(f"  ✓ {signal}")
    
    if auth['风险点']:
        print("\n【风险点】：")
        for risk in auth['风险点']:
            print(f"  ! {risk}")
    
    print("\n详细指标：")
    for key, value in auth['详细指标'].items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # 利润可持续性
    sust = analysis_result['利润可持续性分析']
    print(f"\n--- 利润可持续性分析 ---")
    print(f"评级：{sust['评级']}，评分：{sust['评分']}/100")
    
    if sust['正面信号']:
        print("\n【正面信号】：")
        for signal in sust['正面信号']:
            print(f"  ✓ {signal}")
    
    if sust['风险点']:
        print("\n【风险点】：")
        for risk in sust['风险点']:
            print(f"  ! {risk}")
    
    # 地雷扫描
    flags = analysis_result['地雷扫描']
    print(f"\n--- 地雷扫描 ---")
    print(f"警报级别：{flags['警报级别']}")
    
    if flags['红色警报']:
        print("\n【红色警报】⚠️")
        for flag in flags['红色警报']:
            print(f"  🔴 {flag}")
    
    if flags['黄色警告']:
        print("\n【黄色警告】⚠️")
        for flag in flags['黄色警告']:
            print(f"  🟡 {flag}")
    
    if flags['绿色信号']:
        print("\n【绿色信号】✅")
        for flag in flags['绿色信号']:
            print(f"  🟢 {flag}")
    
    # 投资建议
    print(f"\n--- 投资建议 ---")
    for advice in analysis_result['投资建议']:
        print(f"  💡 {advice}")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    """
    使用示例：分析几家典型公司
    """
    
    # 示例1：贵州茅台（好公司的典范）
    print("示例1：贵州茅台利润质量分析")
    maotai_result = comprehensive_profit_quality_analysis(
        company_name="贵州茅台(600519)",
        revenue=1241e8,  # 1241亿
        gross_profit=1120e8,  # 1120亿
        net_profit=750e8,  # 750亿
        deducted_profit=740e8,  # 扣非740亿
        main_business_revenue=1230e8,  # 主营业务1230亿
        operating_cash_flow=800e8,  # 经营现金流800亿
        cash_from_sales=1400e8,  # 销售现金1400亿
        accounts_receivable=10e8,  # 应收账款10亿（极少）
        inventory=300e8,  # 存货300亿
        other_receivables=5e8,  # 其他应收款很少
        other_payables=50e8,
        goodwill=0,  # 几乎无商誉
        intangible_assets=10e8,
        total_assets=2500e8,
        previous_accounts_receivable=9e8,
        previous_inventory=280e8,
        previous_net_profit=690e8,
        previous_deducted_profit=680e8
    )
    print_profit_quality_report(maotai_result)
    
    # 示例2：某问题公司（虚构数据演示地雷）
    print("\n" + "="*70)
    print("示例2：某问题公司分析（虚构数据演示地雷）")
    print("="*70)
    
    problem_company = comprehensive_profit_quality_analysis(
        company_name="某问题公司",
        revenue=100e8,
        gross_profit=15e8,  # 毛利率低
        net_profit=5e8,
        deducted_profit=1e8,  # 扣非净利润很低
        main_business_revenue=60e8,  # 主营业务占比低
        operating_cash_flow=-10e8,  # 经营现金流负！
        cash_from_sales=70e8,  # 销售现金远低于营收
        accounts_receivable=50e8,  # 应收账款很高
        inventory=60e8,  # 存货很高
        other_receivables=30e8,  # 其他应收款很高
        other_payables=40e8,
        goodwill=80e8,  # 商誉很高
        intangible_assets=50e8,
        total_assets=200e8
    )
    print_profit_quality_report(problem_company)
