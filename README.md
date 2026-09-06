# 电商销售数据分析（E-commerce Sales Data Analysis）

一个端到端的电商数据分析项目，覆盖 **数据生成 → 数据清洗(EDA) → 数据建模 → SQL 分析 → Python 分析 → Excel 报表 → Power BI 可视化** 全流程，可作为数据分析师岗位的简历项目。

## 技术栈

`Python` · `MySQL` · `Excel` · `Power BI`

---

## 1. 项目解决什么问题

电商企业积累了大量订单、客户、产品数据，但数据分散、存在质量问题、缺乏结构化的分析视角。本项目解决以下问题：

- **数据清洗**：处理真实业务中常见的脏数据（缺失值、重复、异常值、口径不一致、孤儿记录）。
- **数据建模**：将多张业务表整理为规范的**星型数据模型**，便于后续分析。
- **经营诊断**：回答「整体经营状况如何」「哪些品类/产品/渠道/区域贡献收入」「增长趋势怎样」。
- **客户运营**：通过 **RFM 分层**识别高价值客户、流失客户，指导精细化运营。
- **提效复用**：把重复的分析流程固化为可复现的脚本（Python/SQL/Excel），实现常态化监控。

> 数据为模拟生成（固定随机种子，可复现），用于展示分析思路与工具使用，不涉及真实业务数据。

## 2. 主要功能

| 功能 | 说明 | 对应文件 |
|---|---|---|
| 数据生成 | 生成 2 年（2024–2025）电商模拟数据（含真实脏数据）| `scripts/generate_data.py` |
| 数据清洗 | EDA + 清洗：去重、缺失填充、异常处理、口径统一、删孤儿 | `scripts/data_quality.py` |
| 数据建模 | 建库建表，星型模型（2 事实表 + 3 维度表）| `sql/01_create_tables.sql` |
| 数据入库 | 两种方式导入 MySQL：`LOAD DATA INFILE` 或 Python 脚本 | `sql/02_load_data.sql`、`scripts/etl_load.py` |
| SQL 分析 | 10 组分析查询：趋势、品类、产品、地域、RFM、复购、渠道、滞销、漏斗 | `sql/03_analysis_queries.sql` |
| Python 分析 | 计算月度趋势/同比环比、品类汇总、产品 TOP10、地域、RFM 分层、复购率、渠道、滞销、KPI | `scripts/analysis.py` |
| Excel 报表 | 生成带原生图表、样式、KPI 卡片的 `.xlsx`（7 个工作表）| `scripts/excel_report.py` |
| Power BI 可视化 | 数据模型说明、20+ DAX 度量、可视化搭建指南 | `powerbi/` |

## 3. 安装方法

### 环境要求

- Python 3.8+
- （可选）MySQL 5.7+ / 8.0+，仅「MySQL 分析」部分需要
- （可选）Power BI Desktop，仅「Power BI 可视化」部分需要

### 安装依赖

```bash
pip install -r requirements.txt
```

依赖清单：`pandas`、`numpy`、`openpyxl`、`matplotlib`、`SQLAlchemy`、`PyMySQL`。

## 4. 使用方法

核心分析流程**只需 Python**，无需数据库即可跑通：

```bash
# 1. 生成模拟数据（含脏数据）→ data/raw/
python scripts/generate_data.py

# 2. 数据清洗（EDA + 清洗）→ data/processed/cleaned/
python scripts/data_quality.py

# 3. 运行核心分析 → data/processed/
python scripts/analysis.py

# 4. 生成 Excel 报表 → excel/电商销售分析报告.xlsx
python scripts/excel_report.py
```

### 可选：MySQL 分析

```bash
# 方式 A：Python 脚本入库（推荐，跨平台）
python scripts/etl_load.py --host localhost --user root --password 你的密码

# 方式 B：命令行导入（需 FILE 权限，并改 sql/02_load_data.sql 里的路径）
```

执行顺序：`sql/01_create_tables.sql`（建表）→ 入库 → `sql/03_analysis_queries.sql`（分析查询）。

### 可选：Power BI 可视化

按 `powerbi/` 目录下三份文档操作：`数据模型.md` → `DAX度量.md` → `可视化搭建指南.md`。

## 5. 输入输出示例

### 5.1 输入

`scripts/generate_data.py` 无输入，自动产出 `data/raw/` 下 5 个 CSV（含脏数据）：

| 文件 | 记录数 | 关键字段 |
|---|---|---|
| `customers.csv` | 2,000 | customer_id, customer_name, gender, age, province, city, vip_level … |
| `products.csv` | 90 | product_id, product_name, category, unit_cost, unit_price … |
| `orders.csv` | 4,748 | order_id, customer_id, order_time, order_status, discount_amount … |
| `order_items.csv` | 10,976 | order_item_id, order_id, product_id, quantity, unit_price, subtotal … |
| `date_dim.csv` | 1,096 | date, year, quarter, month, is_weekend … |

### 5.2 数据清洗输出

`scripts/data_quality.py` 输出 EDA 报告，并清洗出 `data/processed/cleaned/`：

```
订单表重复 order_id        : 70
订单状态取值不一致         : ['完成', '已发货', '已取消', '已完成', ...]
负优惠金额                 : 24
配送天数异常(>30)          : 19
客户 province 缺失         : 60
明细孤儿记录(order不存在)  : 5
明细 quantity<=0           : 22
```

### 5.3 分析输出

`scripts/analysis.py` 打印 KPI 并在 `data/processed/` 生成 8 个结果 CSV：

```
========== 核心 KPI ==========
metric       value
  总GMV 13576665.27
已完成订单数     3839.00
 购买客户数     1110.00
   客单价     3536.51
复购率(%)       38.22
```

| 文件 | 内容 | 字段 |
|---|---|---|
| `kpi_summary.csv` | 核心 KPI | metric, value |
| `monthly_trend.csv` | 月度趋势/同比环比 | ym, order_cnt, gmv, avg_order_value, mom_pct, yoy_pct |
| `category_summary.csv` | 品类汇总 | category, order_cnt, sold_qty, revenue, cost, gross_profit, margin_pct, revenue_share_pct |
| `product_top10.csv` | 畅销产品 | product_id, product_name, category, sold_qty, revenue, cost, margin_pct |
| `region_summary.csv` | 地域汇总 | province, order_cnt, buyer_cnt, revenue |
| `rfm_segments.csv` | 客户 RFM 分层 | segment, cnt, avg_monetary, pct |
| `channel_summary.csv` | 渠道汇总 | channel, order_cnt, revenue, avg_order_value |
| `slow_moving.csv` | 滞销产品 | product_id, product_name, category, unit_price, unit_cost |

### 5.4 Excel 报表

`scripts/excel_report.py` 生成 `excel/电商销售分析报告.xlsx`，包含 7 个工作表（6 张原生图表）：

`概览`（KPI 卡）· `月度趋势`（折线图）· `品类分析` · `地域分析` · `RFM分层` · `渠道分析` · `产品TOP10`（条形图）。

## 目录结构

```
├── data/
│   ├── raw/          # 原始数据（含脏数据）
│   └── processed/    # 清洗后数据 + 分析结果
├── sql/              # 建表 / 导入 / 分析 SQL
├── scripts/          # Python 脚本（生成 / 清洗 / ETL / 分析 / Excel）
├── excel/            # Excel 报表交付物
├── powerbi/          # 数据模型 / DAX / 可视化指南
└── docs/             # 项目说明 + 分析报告
```

## 核心结论速览

| 指标 | 数值 |
|---|---|
| 两年总 GMV | 1,357.7 万元 |
| 客单价 | 3,536.51 元 |
| 复购率 | 38.22% |
| 2025 同比增速 | +16.2% |

完整分析见 [`docs/分析报告.md`](docs/分析报告.md)，项目技术细节见 [`docs/项目说明.md`](docs/项目说明.md)。
