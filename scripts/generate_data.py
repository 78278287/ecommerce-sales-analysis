# -*- coding: utf-8 -*-
"""
生成模拟电商销售数据（含真实的数据质量问题）。

产出 data/raw/ 下的 5 张 CSV：
  customers.csv   客户维度表
  products.csv    产品维度表
  orders.csv      订单事实表
  order_items.csv 订单明细事实表
  date_dim.csv    日期维度表（用于 Power BI 时间智能）

数据特点（刻意贴近真实业务，而非"理想干净数据"）：
  * 产品销量服从重尾分布 —— 少数爆款 + 大量长尾/死库存（~30% SKU 近零动销）
  * 客户活跃度服从重尾分布 —— 少量高频客户 + 大量一次性客户（复购率约 30%）
  * 注入数据质量问题：缺失值、重复记录、异常值、脏格式、孤儿明细

所有随机性基于固定种子（SEED=42），可复现。
运行方式：python scripts/generate_data.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

SEED = 42
rng = np.random.default_rng(SEED)

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


# ---------------------------------------------------------------------------
# 基础素材
# ---------------------------------------------------------------------------
SURNAMES = list("王李张刘陈杨赵黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段雷钱汤尹黎易常武乔贺赖龚文")
GIVEN_CHARS = list("伟芳娜敏静丽强磊军洋勇艳杰娟涛明超霞平刚桂英华玉兰建国志斌宇浩晨雪梅雨欣佳琪子涵浩然梓萱晨曦俊杰宇航诗涵嘉怡志强雨桐梦琪浩然思远鹏飞晓婷雅琴海燕博文子墨一诺欣妍雨泽天佑佳怡嘉懿")


def random_name(n):
    """生成 n 个中文姓名（单姓 + 1~2 字名）。"""
    names = []
    for _ in range(n):
        ln = rng.choice(SURNAMES)
        gl = int(rng.choice([1, 2]))
        fn = "".join(rng.choice(GIVEN_CHARS, size=gl, replace=False))
        names.append(ln + fn)
    return names


# 品类 -> 子品类 -> 产品（品牌, 成本, 售价）
CATALOG = {
    "手机数码": {
        "手机": ("华为", 3200, 4599),
        "耳机": ("漫步者", 180, 399),
        "平板电脑": ("小米", 1500, 2299),
        "充电宝": ("小米", 60, 129),
        "智能手表": ("华为", 800, 1499),
    },
    "家用电器": {
        "冰箱": ("美的", 2200, 3599),
        "洗衣机": ("海尔", 1600, 2699),
        "空调": ("格力", 2100, 3299),
        "电饭煲": ("苏泊尔", 180, 329),
        "吸尘器": ("戴森", 1400, 2599),
    },
    "服饰鞋包": {
        "T恤": ("优衣库", 45, 129),
        "牛仔裤": ("李维斯", 120, 299),
        "运动鞋": ("耐克", 320, 699),
        "双肩包": ("新秀丽", 180, 459),
        "羽绒服": ("波司登", 520, 1099),
    },
    "美妆个护": {
        "面膜": ("自然堂", 35, 99),
        "口红": ("兰蔻", 130, 320),
        "洗发水": ("海飞丝", 28, 68),
        "香水": ("香奈儿", 380, 880),
        "洗面奶": ("欧莱雅", 45, 118),
    },
    "食品饮料": {
        "坚果礼盒": ("三只松鼠", 55, 128),
        "咖啡": ("雀巢", 45, 98),
        "茶叶": ("八马", 120, 268),
        "巧克力": ("德芙", 22, 55),
        "牛奶": ("蒙牛", 38, 79),
    },
    "母婴玩具": {
        "奶粉": ("飞鹤", 180, 328),
        "纸尿裤": ("帮宝适", 65, 139),
        "积木": ("乐高", 220, 499),
        "毛绒玩具": ("迪士尼", 80, 199),
        "婴儿推车": ("好孩子", 380, 799),
    },
}

PROVINCE_CITIES = {
    "广东": [("广州", 0.35), ("深圳", 0.35), ("东莞", 0.15), ("佛山", 0.15)],
    "江苏": [("南京", 0.4), ("苏州", 0.35), ("无锡", 0.25)],
    "浙江": [("杭州", 0.45), ("宁波", 0.3), ("温州", 0.25)],
    "上海": [("上海", 1.0)],
    "北京": [("北京", 1.0)],
    "四川": [("成都", 0.6), ("绵阳", 0.4)],
    "湖北": [("武汉", 0.7), ("宜昌", 0.3)],
    "山东": [("济南", 0.4), ("青岛", 0.35), ("烟台", 0.25)],
    "福建": [("厦门", 0.4), ("福州", 0.35), ("泉州", 0.25)],
    "河南": [("郑州", 0.55), ("洛阳", 0.45)],
    "湖南": [("长沙", 0.6), ("株洲", 0.4)],
    "陕西": [("西安", 0.75), ("咸阳", 0.25)],
    "重庆": [("重庆", 1.0)],
    "辽宁": [("沈阳", 0.5), ("大连", 0.5)],
    "安徽": [("合肥", 0.6), ("芜湖", 0.4)],
}
PROVINCES = list(PROVINCE_CITIES.keys())
PROVINCE_WEIGHTS = np.array([3.5, 2.8, 2.6, 2.2, 2.0, 1.8, 1.6, 1.6, 1.3, 1.3, 1.2, 1.2, 1.0, 1.0, 0.9])
PROVINCE_WEIGHTS = PROVINCE_WEIGHTS / PROVINCE_WEIGHTS.sum()

CHANNELS = ["天猫", "京东", "抖音", "拼多多", "小程序"]
CHANNEL_WEIGHTS = np.array([0.28, 0.25, 0.20, 0.17, 0.10])

VIP_LEVELS = ["普通会员", "银卡会员", "金卡会员", "钻石会员"]
VIP_WEIGHTS = np.array([0.55, 0.25, 0.14, 0.06])


# ---------------------------------------------------------------------------
# 产品维度表
# ---------------------------------------------------------------------------
def gen_products():
    rows = []
    pid = 0
    for cat, subs in CATALOG.items():
        for sub, (brand, cost, price) in subs.items():
            # 同一子品类生成 3 个 SKU，价格/成本带浮动
            for sku in range(1, 4):
                pid += 1
                cost_f = cost * rng.uniform(0.92, 1.05)
                price_f = price * rng.uniform(0.95, 1.12)
                rows.append({
                    "product_id": f"P{pid:04d}",
                    "product_name": f"{brand} {sub} {['经典款', '升级款', '尊享款'][sku-1]}",
                    "category": cat,
                    "sub_category": sub,
                    "brand": brand,
                    "unit_cost": round(cost_f, 2),
                    "unit_price": round(price_f, 2),
                    "supplier": f"{brand}官方旗舰店",
                    "is_active": int(rng.random() > 0.04),  # 4% 下架
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 客户维度表
# ---------------------------------------------------------------------------
def gen_customers(n=2000):
    provinces = rng.choice(PROVINCES, size=n, p=PROVINCE_WEIGHTS)
    cities = []
    for p in provinces:
        opts = PROVINCE_CITIES[p]
        cs = [c for c, _ in opts]
        ws = [w for _, w in opts]
        cities.append(rng.choice(cs, p=np.array(ws) / sum(ws)))

    register_dates = pd.to_datetime(
        rng.integers(0, 720, size=n), unit="D", origin="2024-01-01"
    ).strftime("%Y-%m-%d")

    return pd.DataFrame({
        "customer_id": [f"C{i:05d}" for i in range(1, n + 1)],
        "customer_name": random_name(n),
        "gender": rng.choice(["男", "女"], size=n, p=[0.47, 0.53]),
        "age": rng.integers(18, 61, size=n),
        "province": provinces,
        "city": cities,
        "register_date": register_dates,
        "channel": rng.choice(CHANNELS, size=n, p=CHANNEL_WEIGHTS),
        "vip_level": rng.choice(VIP_LEVELS, size=n, p=VIP_WEIGHTS),
    })


# ---------------------------------------------------------------------------
# 客户下单次数（显式重尾分布）
# ---------------------------------------------------------------------------
def customer_order_counts(n_customers, rng):
    """为每个客户分配下单次数。

    分布：38% 从不购买 / 42% 仅 1 次 / 13% 2~5 次 / 5% 6~20 次 / 2% 21~60 次。
    这样约 60% 的客户会下单，其中约 1/3 会复购（复购率 ~30%），贴近真实电商。
    """
    counts = np.zeros(n_customers, dtype=int)
    for i in range(n_customers):
        u = rng.random()
        if u < 0.38:
            c = 0
        elif u < 0.80:
            c = 1
        elif u < 0.93:
            c = int(rng.integers(2, 6))
        elif u < 0.98:
            c = int(rng.integers(6, 21))
        else:
            c = int(rng.integers(21, 61))
        counts[i] = c
    return counts


# ---------------------------------------------------------------------------
# 订单 + 明细
# ---------------------------------------------------------------------------
def gen_orders(customers, products):
    n_products = len(products)
    n_customers = len(customers)

    # 产品热度：重尾分布。少数爆款走量，~30% 为死库存（近零动销）。
    popularity = rng.pareto(2.5, size=n_products)
    dead = rng.random(n_products) < 0.30
    popularity[dead] *= 0.005
    pop_prob = popularity / popularity.sum()

    # 客户下单次数：控制复购率，订单总数由次数求和决定。
    order_counts = customer_order_counts(n_customers, rng)
    n = int(order_counts.sum())

    # 1) 订单日期：按 趋势 × 促销 × 周末 加权抽样
    dates = pd.date_range("2024-01-01", "2025-12-31")
    month_idx = np.arange(len(dates)) // 30
    trend = 1 + 0.20 * (month_idx / 23.0)
    seasonal = 1 + 0.25 * np.sin((month_idx - 2) * 2 * np.pi / 12)
    promo = np.ones(len(dates))
    for i, d in enumerate(dates):
        if d.month == 6 and 1 <= d.day <= 20:
            promo[i] = 1.9
        elif d.month == 11 and 1 <= d.day <= 12:
            promo[i] = 2.4
        elif d.month == 12 and d.day >= 10:
            promo[i] = 1.5
    weekend = np.where(dates.dayofweek >= 5, 1.25, 1.0)

    day_weights = trend * seasonal * promo * weekend
    day_prob = day_weights / day_weights.sum()
    order_dates = rng.choice(dates, size=n, p=day_prob)

    hours = rng.integers(0, 24, size=n)
    minutes = rng.integers(0, 60, size=n)
    seconds = rng.integers(0, 60, size=n)
    order_times = pd.to_datetime(order_dates) + pd.to_timedelta(
        hours * 3600 + minutes * 60 + seconds, unit="s"
    )

    # 每客户按其下单次数重复后打乱，作为订单的客户归属
    customer_ids = np.repeat(customers["customer_id"].values, order_counts)
    rng.shuffle(customer_ids)

    status = rng.choice(
        ["已完成", "已发货", "待发货", "已取消", "已退款"],
        size=n, p=[0.82, 0.06, 0.05, 0.04, 0.03],
    )
    payment = rng.choice(
        ["微信支付", "支付宝", "银行卡", "货到付款"],
        size=n, p=[0.40, 0.38, 0.15, 0.07],
    )

    orders = pd.DataFrame({
        "order_id": [f"O{i:06d}" for i in range(1, n + 1)],
        "customer_id": customer_ids,
        "order_time": order_times.strftime("%Y-%m-%d %H:%M:%S"),
        "order_status": status,
        "payment_method": payment,
        "discount_amount": np.round(rng.uniform(0, 80, size=n), 2),
        "delivery_days": np.clip(rng.poisson(3, size=n) + rng.integers(1, 3, size=n), 1, 7),
    })

    # 2) 订单明细：每单 1~4 件不同商品，按产品热度加权
    items = []
    item_id = 0
    for oid, status_i in zip(orders["order_id"], orders["order_status"]):
        if status_i in ("已取消", "已退款"):
            continue
        k = int(rng.integers(1, 5))
        chosen = rng.choice(products["product_id"], size=k, replace=False, p=pop_prob)
        for pid in chosen:
            item_id += 1
            p = products[products["product_id"] == pid].iloc[0]
            # 件数按价格分层：高价商品通常只买 1~2 件，低价快消品可买多件
            if p["unit_price"] >= 2000:
                qty = int(rng.integers(1, 3))
            elif p["unit_price"] >= 300:
                qty = int(rng.integers(1, 4))
            else:
                qty = int(rng.integers(1, 6))
            price = round(p["unit_price"] * rng.uniform(0.85, 1.0), 2)
            disc = rng.choice([0, 0.05, 0.10, 0.15, 0.20], p=[0.6, 0.15, 0.12, 0.08, 0.05])
            items.append({
                "order_item_id": item_id,
                "order_id": oid,
                "product_id": pid,
                "quantity": qty,
                "unit_price": price,
                "discount_rate": disc,
                "subtotal": round(qty * price * (1 - disc), 2),
            })

    return orders, pd.DataFrame(items)


# ---------------------------------------------------------------------------
# 日期维度表
# ---------------------------------------------------------------------------
def gen_date_dim():
    dates = pd.date_range("2024-01-01", "2026-12-31")
    df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d")})
    df["year"] = dates.year
    df["quarter"] = dates.quarter
    df["month"] = dates.month
    df["day"] = dates.day
    df["weekday"] = dates.dayofweek + 1
    df["is_weekend"] = (dates.dayofweek >= 5).astype(int)
    df["month_name"] = dates.strftime("%Y-%m")
    return df


# ---------------------------------------------------------------------------
# 注入数据质量问题（让原始数据更真实）
# ---------------------------------------------------------------------------
def inject_data_issues(customers, orders, items):
    """向干净数据注入：缺失值 / 重复 / 异常值 / 脏格式 / 孤儿明细。"""
    # 1) 缺失值
    customers.loc[customers.sample(frac=0.03, random_state=1).index, "province"] = np.nan
    customers.loc[customers.sample(frac=0.05, random_state=2).index, "city"] = np.nan
    orders.loc[orders.sample(frac=0.02, random_state=3).index, "payment_method"] = np.nan

    # 2) 重复记录
    dup_orders = orders.sample(frac=0.015, random_state=4)
    orders = pd.concat([orders, dup_orders], ignore_index=True)
    dup_items = items.sample(frac=0.005, random_state=5)
    items = pd.concat([items, dup_items], ignore_index=True)

    # 3) 异常值
    idx = orders.sample(frac=0.004, random_state=6).index
    orders.loc[idx, "delivery_days"] = rng.integers(30, 100, size=len(idx))
    idx2 = orders.sample(frac=0.005, random_state=7).index
    orders.loc[idx2, "discount_amount"] = -rng.uniform(1, 50, size=len(idx2)).round(2)
    idx3 = items.sample(frac=0.002, random_state=8).index
    items.loc[idx3, "quantity"] = 0

    # 4) 脏格式（尾部空格 / 同义词）
    idx4 = customers.sample(frac=0.02, random_state=9).index
    customers.loc[idx4, "customer_name"] = customers.loc[idx4, "customer_name"] + " "
    idx5 = orders.sample(frac=0.01, random_state=10).index
    orders.loc[idx5, "order_status"] = "完成"  # 与"已完成"口径不一致

    # 5) 孤儿明细（order_id 在订单表中不存在）
    orphan = pd.DataFrame({
        "order_item_id": range(1, 6),
        "order_id": ["O999999", "O999998", "O999997", "O999996", "O999995"],
        "product_id": ["P0001"] * 5,
        "quantity": [1] * 5,
        "unit_price": [100.0] * 5,
        "discount_rate": [0.0] * 5,
        "subtotal": [100.0] * 5,
    })
    items = pd.concat([items, orphan], ignore_index=True)

    return customers, orders, items


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print("生成产品表 ...")
    products = gen_products()
    print("生成客户表 ...")
    customers = gen_customers()
    print("生成订单/明细 ...")
    orders, items = gen_orders(customers, products)
    print("生成日期维度 ...")
    date_dim = gen_date_dim()

    print("注入数据质量问题 ...")
    customers, orders, items = inject_data_issues(customers, orders, items)

    products.to_csv(RAW_DIR / "products.csv", index=False, encoding="utf-8")
    customers.to_csv(RAW_DIR / "customers.csv", index=False, encoding="utf-8")
    orders.to_csv(RAW_DIR / "orders.csv", index=False, encoding="utf-8")
    items.to_csv(RAW_DIR / "order_items.csv", index=False, encoding="utf-8")
    date_dim.to_csv(RAW_DIR / "date_dim.csv", index=False, encoding="utf-8")

    # 控制台复购率粗查（供调参参考）
    buyers = orders[orders.order_status == "已完成"].groupby("customer_id").order_id.nunique()
    rep = (buyers >= 2).mean() * 100 if len(buyers) else 0
    sold = set(items.order_id)
    print("完成。数据规模：")
    print(f"  产品 {len(products)} 行")
    print(f"  客户 {len(customers)} 行")
    print(f"  订单 {len(orders)} 行（含重复/脏数据）")
    print(f"  订单明细 {len(items)} 行")
    print(f"  日期维度 {len(date_dim)} 行")
    print(f"  [参考] 已完成订单复购率 ≈ {rep:.1f}%")


if __name__ == "__main__":
    main()
