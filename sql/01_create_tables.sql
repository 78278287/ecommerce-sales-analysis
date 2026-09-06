-- =====================================================================
-- 电商销售数据分析 · 建库建表脚本
-- 数据库：ecommerce
-- 字符集：utf8mb4（兼容中文）
-- 执行环境：MySQL 5.7+ / 8.0+
-- =====================================================================

CREATE DATABASE IF NOT EXISTS ecommerce
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_general_ci;

USE ecommerce;

-- ---------------------------------------------------------------------
-- 1. 客户维度表
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customer_id     VARCHAR(10)   NOT NULL COMMENT '客户ID',
    customer_name   VARCHAR(50)   NOT NULL COMMENT '客户姓名',
    gender          VARCHAR(4)    DEFAULT NULL COMMENT '性别',
    age             TINYINT       DEFAULT NULL COMMENT '年龄',
    province        VARCHAR(20)   DEFAULT NULL COMMENT '省份',
    city            VARCHAR(20)   DEFAULT NULL COMMENT '城市',
    register_date   DATE          NOT NULL COMMENT '注册日期',
    channel         VARCHAR(20)   DEFAULT NULL COMMENT '注册渠道',
    vip_level       VARCHAR(20)   DEFAULT NULL COMMENT '会员等级',
    PRIMARY KEY (customer_id),
    KEY idx_city (city),
    KEY idx_province (province),
    KEY idx_vip (vip_level)
) ENGINE = InnoDB COMMENT = '客户维度表';

-- ---------------------------------------------------------------------
-- 2. 产品维度表
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS products;
CREATE TABLE products (
    product_id      VARCHAR(10)   NOT NULL COMMENT '产品ID',
    product_name    VARCHAR(100)  NOT NULL COMMENT '产品名称',
    category        VARCHAR(20)   NOT NULL COMMENT '一级品类',
    sub_category    VARCHAR(20)   NOT NULL COMMENT '二级品类',
    brand           VARCHAR(40)   DEFAULT NULL COMMENT '品牌',
    unit_cost       DECIMAL(10,2) NOT NULL COMMENT '单位成本',
    unit_price      DECIMAL(10,2) NOT NULL COMMENT '单位售价',
    supplier        VARCHAR(60)   DEFAULT NULL COMMENT '供应商',
    is_active       TINYINT       DEFAULT 1 COMMENT '是否在售 1=是 0=否',
    PRIMARY KEY (product_id),
    KEY idx_category (category),
    KEY idx_sub_category (sub_category),
    KEY idx_brand (brand)
) ENGINE = InnoDB COMMENT = '产品维度表';

-- ---------------------------------------------------------------------
-- 3. 订单事实表
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    order_id        VARCHAR(10)   NOT NULL COMMENT '订单ID',
    customer_id     VARCHAR(10)   NOT NULL COMMENT '客户ID',
    order_time      DATETIME      NOT NULL COMMENT '下单时间',
    order_status    VARCHAR(10)   NOT NULL COMMENT '订单状态',
    payment_method  VARCHAR(20)   DEFAULT NULL COMMENT '支付方式',
    discount_amount DECIMAL(10,2) DEFAULT 0 COMMENT '整单优惠金额',
    delivery_days   TINYINT       DEFAULT NULL COMMENT '配送天数',
    PRIMARY KEY (order_id),
    KEY idx_customer (customer_id),
    KEY idx_order_time (order_time),
    KEY idx_status (order_status),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
        REFERENCES customers (customer_id)
) ENGINE = InnoDB COMMENT = '订单事实表';

-- ---------------------------------------------------------------------
-- 4. 订单明细事实表
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS order_items;
CREATE TABLE order_items (
    order_item_id   INT           NOT NULL COMMENT '明细ID',
    order_id        VARCHAR(10)   NOT NULL COMMENT '订单ID',
    product_id      VARCHAR(10)   NOT NULL COMMENT '产品ID',
    quantity        INT           NOT NULL COMMENT '购买数量',
    unit_price      DECIMAL(10,2) NOT NULL COMMENT '成交单价',
    discount_rate   DECIMAL(4,2)  DEFAULT 0 COMMENT '折扣率',
    subtotal        DECIMAL(10,2) NOT NULL COMMENT '小计金额',
    PRIMARY KEY (order_item_id),
    KEY idx_order (order_id),
    KEY idx_product (product_id),
    CONSTRAINT fk_items_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id),
    CONSTRAINT fk_items_product FOREIGN KEY (product_id)
        REFERENCES products (product_id)
) ENGINE = InnoDB COMMENT = '订单明细事实表';

-- ---------------------------------------------------------------------
-- 5. 日期维度表（Power BI 时间智能 / 环比同比）
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS date_dim;
CREATE TABLE date_dim (
    date            DATE          NOT NULL COMMENT '日期',
    year            SMALLINT      NOT NULL COMMENT '年',
    quarter         TINYINT       NOT NULL COMMENT '季度',
    month           TINYINT       NOT NULL COMMENT '月',
    day             TINYINT       NOT NULL COMMENT '日',
    weekday         TINYINT       NOT NULL COMMENT '星期 1=周一',
    is_weekend      TINYINT       NOT NULL COMMENT '是否周末 1=是',
    month_name      VARCHAR(7)    NOT NULL COMMENT '年月 YYYY-MM',
    PRIMARY KEY (date)
) ENGINE = InnoDB COMMENT = '日期维度表';
