-- =====================================================================
-- 电商销售数据分析 · 核心分析 SQL
-- 覆盖：整体趋势 / 品类 / 产品 / 地域 / 客户RFM / 复购 / 渠道 / 滞销
-- 执行前请先完成 01 建表 + 02 导入
-- =====================================================================

USE ecommerce;

-- ---------------------------------------------------------------------
-- 1. 月度销售趋势（GMV、订单量、客单价）
-- ---------------------------------------------------------------------
SELECT
    DATE_FORMAT(o.order_time, '%Y-%m')                    AS ym,
    COUNT(DISTINCT o.order_id)                            AS order_cnt,
    ROUND(SUM(oi.subtotal) - SUM(o.discount_amount), 2)   AS gmv,
    ROUND((SUM(oi.subtotal) - SUM(o.discount_amount))
          / COUNT(DISTINCT o.order_id), 2)                AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = '已完成'
GROUP BY DATE_FORMAT(o.order_time, '%Y-%m')
ORDER BY ym;

-- ---------------------------------------------------------------------
-- 2. 同比 / 环比（使用窗口函数 LAG）
-- ---------------------------------------------------------------------
WITH monthly AS (
    SELECT
        DATE_FORMAT(o.order_time, '%Y-%m')                  AS ym,
        ROUND(SUM(oi.subtotal) - SUM(o.discount_amount), 2) AS gmv
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = '已完成'
    GROUP BY DATE_FORMAT(o.order_time, '%Y-%m')
)
SELECT
    ym,
    gmv,
    ROUND(LAG(gmv, 1)  OVER (ORDER BY ym), 2) AS gmv_prev_month,
    ROUND(LAG(gmv, 12) OVER (ORDER BY ym), 2) AS gmv_prev_year,
    ROUND((gmv - LAG(gmv, 1)  OVER (ORDER BY ym))
          / LAG(gmv, 1)  OVER (ORDER BY ym) * 100, 2) AS mom_pct,
    ROUND((gmv - LAG(gmv, 12) OVER (ORDER BY ym))
          / LAG(gmv, 12) OVER (ORDER BY ym) * 100, 2) AS yoy_pct
FROM monthly
ORDER BY ym;

-- ---------------------------------------------------------------------
-- 3. 品类分析：销售额、销量、毛利率、占比
-- ---------------------------------------------------------------------
SELECT
    p.category,
    COUNT(DISTINCT oi.order_id)                    AS order_cnt,
    SUM(oi.quantity)                               AS sold_qty,
    ROUND(SUM(oi.subtotal), 2)                     AS revenue,
    ROUND(SUM(oi.subtotal) - SUM(p.unit_cost * oi.quantity), 2) AS gross_profit,
    ROUND((SUM(oi.subtotal) - SUM(p.unit_cost * oi.quantity))
          / SUM(oi.subtotal) * 100, 2)             AS margin_pct,
    ROUND(SUM(oi.subtotal) / (SELECT SUM(subtotal) FROM order_items oi2
                              JOIN orders o2 ON oi2.order_id = o2.order_id
                              WHERE o2.order_status = '已完成') * 100, 2) AS revenue_share_pct
FROM order_items oi
JOIN orders o   ON oi.order_id   = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = '已完成'
GROUP BY p.category
ORDER BY revenue DESC;

-- ---------------------------------------------------------------------
-- 4. 畅销 TOP 10 产品
-- ---------------------------------------------------------------------
SELECT
    p.product_name,
    p.category,
    SUM(oi.quantity)                 AS sold_qty,
    ROUND(SUM(oi.subtotal), 2)       AS revenue,
    ROUND((SUM(oi.subtotal) - SUM(p.unit_cost * oi.quantity))
          / SUM(oi.subtotal) * 100, 2) AS margin_pct
FROM order_items oi
JOIN orders o   ON oi.order_id   = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = '已完成'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;

-- ---------------------------------------------------------------------
-- 5. 地域分析：省份销售额 TOP
-- ---------------------------------------------------------------------
SELECT
    c.province,
    COUNT(DISTINCT o.order_id)              AS order_cnt,
    COUNT(DISTINCT o.customer_id)           AS buyer_cnt,
    ROUND(SUM(oi.subtotal), 2)              AS revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN customers c    ON o.customer_id = c.customer_id
WHERE o.order_status = '已完成'
GROUP BY c.province
ORDER BY revenue DESC;

-- ---------------------------------------------------------------------
-- 6. 客户 RFM 分层（基于近 1 年行为）
-- ---------------------------------------------------------------------
WITH rfm AS (
    SELECT
        o.customer_id,
        DATEDIFF('2025-12-31', MAX(o.order_time))   AS recency,
        COUNT(DISTINCT o.order_id)                  AS frequency,
        ROUND(SUM(oi.subtotal), 2)                  AS monetary
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = '已完成'
      AND o.order_time >= '2025-01-01'
    GROUP BY o.customer_id
),
scored AS (
    SELECT
        customer_id,
        NTILE(4) OVER (ORDER BY recency  DESC) AS r_score,  -- 越小越近
        NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,  -- 越大越频繁
        NTILE(4) OVER (ORDER BY monetary ASC)  AS m_score   -- 越大越值钱
    FROM rfm
)
SELECT
    CASE
        WHEN r_score = 4 AND f_score = 4 THEN '重要价值客户'
        WHEN r_score = 4 AND f_score <  4 THEN '新客户/潜力客户'
        WHEN r_score <  3 AND f_score >= 3 THEN '重要唤回客户'
        WHEN r_score <  3 AND f_score <  3 THEN '流失客户'
        ELSE '一般客户'
    END                 AS segment,
    COUNT(*)            AS cnt,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM scored
GROUP BY segment
ORDER BY cnt DESC;

-- ---------------------------------------------------------------------
-- 7. 复购率（一年内下单 >= 2 次的客户占比）
-- ---------------------------------------------------------------------
WITH yearly AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS order_cnt
    FROM orders
    WHERE order_status = '已完成'
      AND order_time >= '2025-01-01'
    GROUP BY customer_id
)
SELECT
    SUM(CASE WHEN order_cnt >= 2 THEN 1 ELSE 0 END) AS repurchase_customers,
    COUNT(*)                                        AS total_customers,
    ROUND(SUM(CASE WHEN order_cnt >= 2 THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                      AS repurchase_rate_pct
FROM yearly;

-- ---------------------------------------------------------------------
-- 8. 渠道分析（下单来源 & 客单价）
-- ---------------------------------------------------------------------
SELECT
    c.channel,
    COUNT(DISTINCT o.order_id)                     AS order_cnt,
    ROUND(SUM(oi.subtotal), 2)                     AS revenue,
    ROUND(SUM(oi.subtotal) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id   = oi.order_id
JOIN customers c    ON o.customer_id = c.customer_id
WHERE o.order_status = '已完成'
GROUP BY c.channel
ORDER BY revenue DESC;

-- ---------------------------------------------------------------------
-- 9. 滞销产品（近 90 天零销量的在售商品）
-- ---------------------------------------------------------------------
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.unit_price,
    p.unit_cost
FROM products p
LEFT JOIN order_items oi
    ON p.product_id = oi.product_id
   AND oi.order_id IN (
        SELECT order_id FROM orders
        WHERE order_status = '已完成'
          AND order_time >= '2025-10-01'
   )
WHERE p.is_active = 1
  AND oi.order_item_id IS NULL
ORDER BY p.unit_price DESC;

-- ---------------------------------------------------------------------
-- 10. 销售漏斗：订单状态分布
-- ---------------------------------------------------------------------
SELECT
    order_status,
    COUNT(*)                    AS cnt,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM orders
GROUP BY order_status
ORDER BY cnt DESC;
