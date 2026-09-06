# -*- coding: utf-8 -*-
"""
数据清洗与探索性分析（EDA）。

流程：
  1) 读取 data/raw 原始数据（含缺失、重复、异常、脏格式）
  2) 输出 EDA 报告：规模、类型、缺失率、重复数、描述统计、类别取值
  3) 清洗：
       - 客户：province/city 缺失填充"未知"，姓名去尾部空格
       - 订单：去重 order_id；payment_method 缺失填充"未知"；
               订单状态口径统一（"完成"→"已完成"）；负优惠金额归零；
               配送天数 > 30 视为异常，替换为中位数
       - 明细：删除孤儿明细（order_id 不存在）；删除 quantity<=0 记录；
               按 order_item_id 去重
  4) 保存清洗后数据到 data/processed/cleaned/，并写清洗报告

运行方式：python scripts/data_quality.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
CLEAN_DIR = BASE / "data" / "processed" / "cleaned"


def load():
    tables = {}
    for t in ["customers", "products", "orders", "order_items", "date_dim"]:
        tables[t] = pd.read_csv(RAW / f"{t}.csv", encoding="utf-8", keep_default_na=True)
    return tables


def eda_report(tables):
    """打印 EDA 报告。"""
    print("=" * 60)
    print("EDA 报告（原始数据）")
    print("=" * 60)
    for name, df in tables.items():
        miss = int(df.isna().sum().sum())
        dup = int(df.duplicated().sum())
        print(f"\n【{name}】 {df.shape[0]} 行 × {df.shape[1]} 列 | "
              f"缺失单元格 {miss} | 重复行 {dup}")
        if dup or miss:
            miss_cols = df.columns[df.isna().any()].tolist()
            if miss_cols:
                print(f"  缺失字段: {miss_cols}")

    # 关键脏数据检查
    print("\n" + "=" * 60)
    print("关键数据质量检查")
    print("=" * 60)
    orders = tables["orders"]
    items = tables["order_items"]
    customers = tables["customers"]
    print(f"  订单表重复 order_id        : {int(orders.order_id.duplicated().sum())}")
    print(f"  订单状态取值不一致         : {sorted(orders.order_status.dropna().unique())}")
    print(f"  负优惠金额                 : {int((orders.discount_amount < 0).sum())}")
    print(f"  配送天数异常(>30)          : {int((orders.delivery_days > 30).sum())}")
    print(f"  客户 province 缺失         : {int(customers.province.isna().sum())}")
    print(f"  客户 city 缺失             : {int(customers.city.isna().sum())}")
    print(f"  明细孤儿记录(order不存在)  : {int((~items.order_id.isin(orders.order_id)).sum())}")
    print(f"  明细 quantity<=0           : {int((items.quantity <= 0).sum())}")


def clean(tables):
    """清洗并返回清洗后的表 + 统计。"""
    stats = []  # (表, 动作, 影响行数)
    customers = tables["customers"].copy()
    products = tables["products"].copy()
    orders = tables["orders"].copy()
    items = tables["order_items"].copy()
    date_dim = tables["date_dim"].copy()

    # ---- 客户 ----
    n = len(customers)
    customers["province"] = customers["province"].fillna("未知")
    customers["city"] = customers["city"].fillna("未知")
    customers["customer_name"] = customers["customer_name"].str.strip()
    stats.append(("customers", "province/city 缺失填充为'未知'、姓名去空格", n))

    # ---- 订单 ----
    n = len(orders)
    orders = orders.drop_duplicates(subset="order_id", keep="first")
    stats.append(("orders", f"删除重复订单 {n - len(orders)} 条", n - len(orders)))

    n = len(orders)
    orders["payment_method"] = orders["payment_method"].fillna("未知")
    orders["order_status"] = orders["order_status"].str.strip().replace({"完成": "已完成"})
    orders.loc[orders["discount_amount"] < 0, "discount_amount"] = 0
    med = orders.loc[orders["delivery_days"] <= 30, "delivery_days"].median()
    n_out = int((orders["delivery_days"] > 30).sum())
    orders.loc[orders["delivery_days"] > 30, "delivery_days"] = med
    stats.append(("orders", f"payment/status 统一口径，负优惠归零，配送异常({n_out})→中位数{med:.0f}", n_out))

    # ---- 明细 ----
    n = len(items)
    valid_orders = set(orders["order_id"])
    items = items[items["order_id"].isin(valid_orders)]          # 删孤儿
    n_orphan = n - len(items)
    items = items[items["quantity"] > 0]                         # 删无效数量
    n_qty = n - n_orphan - len(items)
    items = items.drop_duplicates(subset="order_item_id", keep="first")
    n_dup = n - n_orphan - n_qty - len(items)
    stats.append(("order_items", f"删孤儿 {n_orphan}、quantity<=0 {n_qty}、重复 {n_dup}", n - len(items)))

    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": items,
        "date_dim": date_dim,
    }, stats


def write_report(stats, cleaned):
    """写清洗报告到 data/processed/data_quality_report.md。"""
    lines = ["# 数据清洗报告", ""]
    lines.append("| 表 | 清洗动作 | 影响行数 |")
    lines.append("|---|---|---|")
    for t, action, cnt in stats:
        lines.append(f"| {t} | {action} | {cnt} |")
    lines.append("")
    lines.append("## 清洗后数据规模")
    lines.append("")
    lines.append("| 表 | 行数 |")
    lines.append("|---|---|")
    for name, df in cleaned.items():
        lines.append(f"| {name} | {df.shape[0]} |")
    (BASE / "data" / "processed" / "data_quality_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    tables = load()
    eda_report(tables)

    print("\n" + "=" * 60)
    print("开始清洗 ...")
    print("=" * 60)
    cleaned, stats = clean(tables)
    for t, action, cnt in stats:
        print(f"  [{t}] {action}")

    for name, df in cleaned.items():
        df.to_csv(CLEAN_DIR / f"{name}.csv", index=False, encoding="utf-8")
    write_report(stats, cleaned)

    print(f"\n清洗完成，已保存到 data/processed/cleaned/")
    print("清洗报告：data/processed/data_quality_report.md")


if __name__ == "__main__":
    main()
