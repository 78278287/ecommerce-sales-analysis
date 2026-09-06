# 数据清洗报告

| 表 | 清洗动作 | 影响行数 |
|---|---|---|
| customers | province/city 缺失填充为'未知'、姓名去空格 | 2000 |
| orders | 删除重复订单 70 条 | 70 |
| orders | payment/status 统一口径，负优惠归零，配送异常(19)→中位数4 | 19 |
| order_items | 删孤儿 5、quantity<=0 22、重复 55 | 82 |

## 清洗后数据规模

| 表 | 行数 |
|---|---|
| customers | 2000 |
| products | 90 |
| orders | 4678 |
| order_items | 10894 |
| date_dim | 1096 |