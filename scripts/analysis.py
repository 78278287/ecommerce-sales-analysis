# -*- coding: utf-8 -*-
"""
核心数据分析：读取清洗后数据，产出各维度指标，保存到 data/processed。

输入：data/processed/cleaned/（由 scripts/data_quality.py 清洗生成）
产出结果 CSV（供 Excel 报表与 Power BI 使用）：
  monthly_trend.csv      月度销售趋势
  category_summary.csv   品类汇总
  product_top10.csv      畅销产品
  region_summary.csv     地域汇总
  rfm_segments.csv       客户 RFM 分层
  channel_summary.csv    渠道汇总
  slow_moving.csv        滞销产品
  kpi_summary.csv        核心 KPI

运行方式：python scripts/analysis.py（需先运行 data_quality.py）
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "processed" / "cleaned"   # 清洗后数据
OUT = BASE / "data" / "processed"

COMPLETED = "已完成"  # 只统计已完成订单


def load():
    customers = pd.read_csv(RAW / "customers.csv", encoding="utf-8")
    products = pd.read_csv(RAW / "products.csv", encoding="utf-8")
    orders = pd.read_csv(RAW / "orders.csv", encoding="utf-8")
    items = pd.read_csv(RAW / "order_items.csv", encoding="utf-8")
    orders["order_time"] = pd.to_datetime(orders["order_time"])
    return customers, products, orders, items


def monthly_trend(orders, items):
    """月度 GMV / 订单量 / 客单价 / 同比环比。"""
    done = orders[orders.order_status == COMPLETED]
    merged = items.merge(done[["order_id", "order_time"]], on="order_id")
    merged["gmv"] = merged.subtotal - 0  # 整单优惠在订单级，近似按明细分摊
    merged["ym"] = merged.order_time.dt.to_period("M")

    # 订单级优惠按订单分摊到明细
    disc = done[["order_id", "discount_amount"]].set_index("order_id")["discount_amount"]
    # 简化：GMV = 明细小计之和 - 订单优惠之和
    gmv_by_order = merged.groupby("order_id").subtotal.sum() - disc
    merged = merged.merge(gmv_by_order.rename("order_gmv"), on="order_id")

    monthly = (
        merged.drop_duplicates("order_id")
        .groupby("ym")
        .agg(order_cnt=("order_id", "nunique"), gmv=("order_gmv", "sum"))
    )
    monthly["avg_order_value"] = (monthly.gmv / monthly.order_cnt).round(2)
    monthly["gmv"] = monthly.gmv.round(2)
    monthly["mom_pct"] = monthly.gmv.pct_change().round(4) * 100
    monthly["yoy_pct"] = monthly.gmv.pct_change(12).round(4) * 100
    monthly = monthly.reset_index()
    monthly["ym"] = monthly.ym.astype(str)
    return monthly


def category_summary(orders, items, products):
    done = orders[orders.order_status == COMPLETED]
    m = items.merge(done[["order_id"]], on="order_id").merge(products, on="product_id")
    m["cost"] = m.unit_cost * m.quantity
    m["revenue"] = m.subtotal
    g = m.groupby("category").agg(
        order_cnt=("order_id", "nunique"),
        sold_qty=("quantity", "sum"),
        revenue=("revenue", "sum"),
        cost=("cost", "sum"),
    )
    g["gross_profit"] = (g.revenue - g.cost).round(2)
    g["margin_pct"] = (g.gross_profit / g.revenue * 100).round(2)
    g["revenue_share_pct"] = (g.revenue / g.revenue.sum() * 100).round(2)
    return g.sort_values("revenue", ascending=False).reset_index()


def product_top(orders, items, products, n=10):
    done = orders[orders.order_status == COMPLETED]
    m = items.merge(done[["order_id"]], on="order_id").merge(products, on="product_id")
    m["cost"] = m.unit_cost * m.quantity
    g = m.groupby(["product_id", "product_name", "category"]).agg(
        sold_qty=("quantity", "sum"),
        revenue=("subtotal", "sum"),
        cost=("cost", "sum"),
    )
    g["margin_pct"] = ((g.revenue - g.cost) / g.revenue * 100).round(2)
    return g.sort_values("revenue", ascending=False).head(n).reset_index()


def region_summary(orders, items, customers):
    done = orders[orders.order_status == COMPLETED]
    m = done.merge(items, on="order_id").merge(customers[["customer_id", "province", "city"]],
                                                on="customer_id")
    g = m.groupby("province").agg(
        order_cnt=("order_id", "nunique"),
        buyer_cnt=("customer_id", "nunique"),
        revenue=("subtotal", "sum"),
    ).sort_values("revenue", ascending=False)
    return g.reset_index()


def rfm(orders, items, customers):
    """近一年 RFM 分层，返回各分层统计。"""
    done = orders[orders.order_status == COMPLETED]
    recent = done[done.order_time >= "2025-01-01"]
    m = recent.merge(items, on="order_id")
    rfm = m.groupby("customer_id").agg(
        recency=("order_time", lambda s: (pd.Timestamp("2025-12-31") - s.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("subtotal", "sum"),
    ).reset_index()
    rfm["r_score"] = pd.qcut(rfm.recency, 4, labels=[4, 3, 2, 1])
    rfm["f_score"] = pd.qcut(rfm.frequency.rank(method="first"), 4, labels=[1, 2, 3, 4])
    rfm["m_score"] = pd.qcut(rfm.monetary.rank(method="first"), 4, labels=[1, 2, 3, 4])
    for c in ["r_score", "f_score", "m_score"]:
        rfm[c] = rfm[c].astype(int)

    def seg(row):
        r, f = row.r_score, row.f_score
        if r == 4 and f == 4:
            return "重要价值客户"
        if r == 4 and f < 4:
            return "新客户/潜力客户"
        if r < 3 and f >= 3:
            return "重要唤回客户"
        if r < 3 and f < 3:
            return "流失客户"
        return "一般客户"

    rfm["segment"] = rfm.apply(seg, axis=1)
    seg_stat = rfm.groupby("segment").agg(
        cnt=("customer_id", "size"),
        avg_monetary=("monetary", "mean"),
    ).sort_values("cnt", ascending=False)
    seg_stat["pct"] = (seg_stat.cnt / seg_stat.cnt.sum() * 100).round(2)
    seg_stat["avg_monetary"] = seg_stat.avg_monetary.round(2)
    return seg_stat.reset_index()


def repurchase_rate(orders):
    done = orders[orders.order_status == COMPLETED]
    yearly = done[done.order_time >= "2025-01-01"].groupby("customer_id").order_id.nunique()
    rep = (yearly >= 2).sum()
    total = len(yearly)
    return rep, total, round(rep / total * 100, 2)


def channel_summary(orders, items, customers):
    done = orders[orders.order_status == COMPLETED]
    m = done.merge(items, on="order_id").merge(customers[["customer_id", "channel"]],
                                               on="customer_id")
    g = m.groupby("channel").agg(
        order_cnt=("order_id", "nunique"),
        revenue=("subtotal", "sum"),
    ).sort_values("revenue", ascending=False)
    g["avg_order_value"] = (g.revenue / g.order_cnt).round(2)
    return g.reset_index()


def slow_moving(orders, items, products):
    recent_order_ids = orders[
        (orders.order_status == COMPLETED) & (orders.order_time >= "2025-10-01")
    ].order_id.unique()
    sold_products = items[items.order_id.isin(recent_order_ids)].product_id.unique()
    slow = products[(products.is_active == 1) & (~products.product_id.isin(sold_products))]
    return slow[["product_id", "product_name", "category", "unit_price", "unit_cost"]]


def kpi_summary(orders, items):
    done = orders[orders.order_status == COMPLETED]
    gmv = (items.merge(done[["order_id", "discount_amount"]], on="order_id")
                .groupby("order_id")
                .apply(lambda g: g.subtotal.sum() - g.discount_amount.iloc[0])
                .sum())
    order_cnt = done.order_id.nunique()
    buyer_cnt = done.customer_id.nunique()
    kpi = {
        "metric": ["总GMV", "已完成订单数", "购买客户数", "客单价", "复购率(%)"],
        "value": [
            round(gmv, 2),
            order_cnt,
            buyer_cnt,
            round(gmv / order_cnt, 2),
            repurchase_rate(orders)[2],
        ],
    }
    return pd.DataFrame(kpi)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    customers, products, orders, items = load()

    print("计算月度趋势 ...")
    mt = monthly_trend(orders, items)
    mt.to_csv(OUT / "monthly_trend.csv", index=False, encoding="utf-8-sig")

    print("计算品类汇总 ...")
    cat = category_summary(orders, items, products)
    cat.to_csv(OUT / "category_summary.csv", index=False, encoding="utf-8-sig")

    print("计算产品 TOP ...")
    top = product_top(orders, items, products)
    top.to_csv(OUT / "product_top10.csv", index=False, encoding="utf-8-sig")

    print("计算地域汇总 ...")
    reg = region_summary(orders, items, customers)
    reg.to_csv(OUT / "region_summary.csv", index=False, encoding="utf-8-sig")

    print("计算 RFM 分层 ...")
    rfm_seg = rfm(orders, items, customers)
    rfm_seg.to_csv(OUT / "rfm_segments.csv", index=False, encoding="utf-8-sig")

    print("计算渠道汇总 ...")
    ch = channel_summary(orders, items, customers)
    ch.to_csv(OUT / "channel_summary.csv", index=False, encoding="utf-8-sig")

    print("计算滞销产品 ...")
    slow = slow_moving(orders, items, products)
    slow.to_csv(OUT / "slow_moving.csv", index=False, encoding="utf-8-sig")

    print("计算 KPI ...")
    kpi = kpi_summary(orders, items)
    kpi.to_csv(OUT / "kpi_summary.csv", index=False, encoding="utf-8-sig")

    # ---- 控制台打印关键结论 ----
    print("\n========== 核心 KPI ==========")
    print(kpi.to_string(index=False))
    print("\n========== 品类汇总 ==========")
    print(cat.to_string(index=False))
    print("\n========== RFM 分层 ==========")
    print(rfm_seg.to_string(index=False))
    print("\n========== 渠道汇总 ==========")
    print(ch.to_string(index=False))
    print("\n完成。结果已写入 data/processed/")


if __name__ == "__main__":
    main()
