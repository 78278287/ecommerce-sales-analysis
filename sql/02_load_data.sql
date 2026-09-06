-- =====================================================================
-- 电商销售数据分析 · 数据导入脚本
-- 两种方式二选一：
--   A. 命令行 LOAD DATA INFILE（本脚本，快，需要 FILE 权限）
--   B. Python 脚本 scripts/etl_load.py（pandas + SQLAlchemy，跨平台）
--
-- 注意：请把下面路径改成你机器上 CSV 的实际绝对路径。
-- =====================================================================

USE ecommerce;

-- 关闭外键检查，避免导入顺序报错
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE order_items;
TRUNCATE TABLE orders;
TRUNCATE TABLE customers;
TRUNCATE TABLE products;
TRUNCATE TABLE date_dim;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. 客户
LOAD DATA INFILE 'D:/git/data/raw/customers.csv'
INTO TABLE customers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(customer_id, customer_name, gender, age, province, city, register_date, channel, vip_level);

-- 2. 产品
LOAD DATA INFILE 'D:/git/data/raw/products.csv'
INTO TABLE products
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(product_id, product_name, category, sub_category, brand, unit_cost, unit_price, supplier, is_active);

-- 3. 订单
LOAD DATA INFILE 'D:/git/data/raw/orders.csv'
INTO TABLE orders
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(order_id, customer_id, order_time, order_status, payment_method, discount_amount, delivery_days);

-- 4. 订单明细
LOAD DATA INFILE 'D:/git/data/raw/order_items.csv'
INTO TABLE order_items
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(order_item_id, order_id, product_id, quantity, unit_price, discount_rate, subtotal);

-- 5. 日期维度
LOAD DATA INFILE 'D:/git/data/raw/date_dim.csv'
INTO TABLE date_dim
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(date, year, quarter, month, day, weekday, is_weekend, month_name);

-- 导入后校验
SELECT 'customers' AS tbl, COUNT(*) AS cnt FROM customers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'date_dim', COUNT(*) FROM date_dim;
