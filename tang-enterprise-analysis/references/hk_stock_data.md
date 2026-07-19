# 港股公告与财务口径

## 目录

1. 港交所公告下载
2. HKFRS字段映射
3. 币种与金额单位
4. 股份口径
5. 提取和复核流程

## 1. 港交所公告下载

使用 `scripts/hkex_report_downloader.py` 从港交所披露易检索年报。代码统一为五位数字；公司名称仅作为查询结果，不代替证券代码。

```bash
python scripts/hkex_report_downloader.py 00700 --years 2023,2024 --output-dir ./reports
python scripts/hkex_report_downloader.py 00005 --years 2024 --list-only
```

Python调用：

```python
from scripts.hkex_report_downloader import HKEXReportDownloader

downloader = HKEXReportDownloader("./reports")
records = downloader.download_annual_reports("03690", [2023, 2024])
```

下载器动态查询港交所内部 `stockId`，不维护静态公司表。搜索结果可能同时包含摘要、20-F、股份计划文件或年报包装公告；脚本优先选择标题匹配且远端PDF较完整的候选。最终仍须核对公司、报告年度、发布日期和报告标题。

## 2. HKFRS字段映射

`references/hkfrs_field_mapping.json` 保存中英文标准字段、常见英文别名、金融机构字段以及股份字段。提取器加载该文件，不在代码中重复维护字段表。

使用映射时遵守：

- 将 `revenue`、`cost of revenues`、`profit attributable to equity holders` 等映射到统一分析字段，但保留原始名称和页码。
- 银行的 `net interest income`、`loans and advances to customers`、`customer accounts` 进入金融企业字段，不据此套用普通企业DCF。
- 港股通常不披露A股口径的“扣非净利润”。缺失时保留 `null`，不得用调整后EBITDA或管理层自定义指标直接替代。
- 同一英文标签在不同行业可能含义不同。字段命中只是候选数据，必须对照报表标题、附注和会计政策。

## 3. 币种与金额单位

先识别年报的报告币种，再识别表内单位。报告币种不一定等于港股交易币种，例如人民币或美元记账的公司仍以港币交易。

提取器支持 `CNY`、`HKD`、`USD`、`GBP`，并识别 `RMB million`、`RMB'000`、`HK$ million`、`US$m`、`$m`、千、百万和十亿等常见写法。输出金额统一为：

```text
数值 × 原始单位倍率 ÷ 100,000,000 = 报告币种的1亿单位
```

不得仅因证券在香港交易就把财务报表金额标为港币。`$m` 无法独立判断美元或港币时，必须从年报会计政策确认报告币种，并通过 `reporting_currency` 显式传入。跨币种比较或把每股价值换算为港币时，单独记录汇率、汇率日期和换算公式；不要改写原始披露币种。

## 4. 股份口径

股份统一输出为绝对股数，不输出“千股”或“百万股”。例如 `9,269 million shares` 转换为 `9,269,000,000 shares`。

根据用途选择口径：

- 期末市值和资产负债表时点：使用估值日实际已发行股份，扣除库存股，并核对估值日至报告日的回购、发行、拆股和注销。
- 基本每股收益核验：使用本期基本加权平均股份。
- 稀释每股价值或保守估值：使用稀释加权平均股份，并检查期权、受限制股份、可转债和反稀释项目。
- 同股不同权公司：核对各类别股份的经济权利和转换条款，不只相加证券代码页面显示的股数。

不得把期末已发行股份、基本加权平均股份和稀释加权平均股份混为一个“总股本”。每股价值必须注明分子币种、分母口径和时点。

## 5. 提取和复核流程

1. 用港交所下载器取得年报并保留公告URL、发布日期和报告年度。
2. 从年报会计政策确认报告币种；遇到裸 `$m` 时显式传给提取器。
3. 调用 `PDFReportExtractor`，按需用 `page_numbers` 限定已核实的报表页。
4. 对照原页复核合并范围、本期列、金额单位、负数括号和股份单位。
5. 对收入、利润、经营现金流、总资产、金融机构核心字段和股份数做勾稽或交叉核验。
6. 将自动提取值保留为候选数据；单位、币种或本期列不确定时停止精确估值。

腾讯、美团和汇丰的离线提取回归样本位于 `tests/fixtures/hk_annual_report_extracts.json`。样本保留港交所原始URL和关键表格片段，用于验证人民币百万、人民币千元、美元百万、金融机构字段及基本/稀释股份口径，不替代完整年报复核。

测试默认只运行离线样本。需要验证港交所当前接口时，在运行 `tests/test_hk_support.py` 前设置 `HKEX_LIVE_TEST=1`；实时测试只查询公告元数据，不下载年报。
