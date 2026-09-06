# DAX 度量集合

> 全部度量建议放在 `order_items` 表下（或单独建一个「度量表」）。
> 前提：已按 `数据模型.md` 建立关系，并在 `order_items` 中准备好了 `unit_cost` 列。

## 1. 基础度量

```dax
-- 销售额
销售额 = SUM(order_items[subtotal])

-- 销量
销量 = SUM(order_items[quantity])

-- 订单数（去重）
订单数 = DISTINCTCOUNT(orders[order_id])

-- 购买客户数（去重）
客户数 = DISTINCTCOUNT(orders[customer_id])

-- 客单价
客单价 = DIVIDE([销售额], [订单数])

-- 成本（成本 × 数量）
成本 = SUMX(order_items, order_items[unit_cost] * order_items[quantity])

-- 毛利
毛利 = [销售额] - [成本]

-- 毛利率
毛利率 = DIVIDE([毛利], [销售额])
```

## 2. 时间智能

```dax
-- 同比销售额（去年同期）
销售额_去年同期 = CALCULATE([销售额], SAMEPERIODLASTYEAR(date_dim[date]))

-- 同比增速
同比增速 = DIVIDE([销售额] - [销售额_去年同期], [销售额_去年同期])

-- 环比销售额（上月）
销售额_上月 = CALCULATE([销售额], DATEADD(date_dim[date], -1, MONTH))

-- 环比增速
环比增速 = DIVIDE([销售额] - [销售额_上月], [销售额_上月])

-- 年初至今累计（YTD）
销售额_YTD = TOTALYTD([销售额], date_dim[date])

-- 移动平均（近 30 天）
销售额_30日移动平均 =
    CALCULATE(
        [销售额],
        DATESINPERIOD(date_dim[date], LASTDATE(date_dim[date]), -30, DAY)
    ) / 30
```

## 3. 客户 / 复购

```dax
-- 复购客户数（下单 >= 2 次）
复购客户数 =
    COUNTROWS(
        FILTER(
            VALUES(orders[customer_id]),
            [订单数] >= 2
        )
    )

-- 复购率
复购率 = DIVIDE([复购客户数], [客户数])

-- 人均消费（ARPU）
ARPU = DIVIDE([销售额], [客户数])
```

## 4. 帕累托 / 贡献度

```dax
-- 品类销售占比
品类销售占比 = DIVIDE([销售额], CALCULATE([销售额], ALL(products[category])))

-- 累计占比（帕累托分析用）
累计占比 =
    VAR cur = [销售额]
    VAR total = CALCULATE([销售额], ALLSELECTED(products))
    VAR cum = CALCULATE(
        [销售额],
        FILTER(
            ALLSELECTED(products),
            [销售额] >= cur
        )
    )
    RETURN DIVIDE(cum, total)
```

## 5. RFM 度量（配合计算列）

在 `orders` 表（或合并后的明细表）先建计算列：

```dax
-- 计算列：最近一次下单距 2025-12-31 的天数（R）
R = DATEDIFF(CALCULATE(MAX(orders[order_time]), ALLEXCEPT(orders, orders[customer_id])), DATE(2025,12,31), DAY)

-- 计算列：下单次数（F）
F = CALCULATE(DISTINCTCOUNT(orders[order_id]), ALLEXCEPT(orders, orders[customer_id]))

-- 计算列：累计消费（M）
M = CALCULATE(SUM(order_items[subtotal]), ALLEXCEPT(orders, orders[customer_id]))
```

再按阈值用 `SWITCH(TRUE(), ...)` 把客户划分到「重要价值 / 潜力 / 唤回 / 流失」分层。
