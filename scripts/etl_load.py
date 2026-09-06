# -*- coding: utf-8 -*-
"""
ETL：将 data/raw/*.csv 加载到 MySQL。

依赖：pandas、sqlalchemy、pymysql
用法：
    python scripts/etl_load.py --host localhost --user root --password 你的密码

默认连接参数可通过命令行或脚本顶部常量修改。
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

sys.stdout.reconfigure(encoding="utf-8")

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

TABLES = ["customers", "products", "orders", "order_items", "date_dim"]


def load(host, port, user, password, database="ecommerce"):
    engine = create_engine(
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    )
    for t in TABLES:
        df = pd.read_csv(RAW_DIR / f"{t}.csv", encoding="utf-8")
        # 覆盖写入（表结构由 01_create_tables.sql 先建好）
        df.to_sql(t, engine, if_exists="replace", index=False,
                  chunksize=1000, method="multi")
        print(f"  已写入 {t}: {len(df)} 行")
    print("ETL 完成。")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", default=3306, type=int)
    p.add_argument("--user", default="root")
    p.add_argument("--password", default="")
    args = p.parse_args()
    load(args.host, args.port, args.user, args.password)
