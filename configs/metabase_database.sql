-- =============================================================================
-- POSTGRESQL SERVING DATA MART DDL: OLIST E-COMMERCE LAKEHOUSE
-- =============================================================================

-- 1. DIMENSION: CUSTOMERS
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id VARCHAR(64) PRIMARY KEY,
    customer_unique_id VARCHAR(64) NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city VARCHAR(128),
    customer_state VARCHAR(8)
);
CREATE INDEX IF NOT EXISTS idx_dim_cust_state ON dim_customers(customer_state);

-- 2. DIMENSION: SELLERS
CREATE TABLE IF NOT EXISTS dim_sellers (
    seller_id VARCHAR(64) PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city VARCHAR(128),
    seller_state VARCHAR(8)
);
CREATE INDEX IF NOT EXISTS idx_dim_seller_state ON dim_sellers(seller_state);

-- 3. DIMENSION: PRODUCTS
CREATE TABLE IF NOT EXISTS dim_products (
    product_id VARCHAR(64) PRIMARY KEY,
    category_name VARCHAR(128),
    product_weight_g NUMERIC(10,2),
    product_photos_qty INTEGER
);
CREATE INDEX IF NOT EXISTS idx_dim_prod_cat ON dim_products(category_name);

-- 4. DIMENSION: DATES
CREATE TABLE IF NOT EXISTS dim_dates (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(32) NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(32) NOT NULL,
    is_weekend INTEGER NOT NULL
);

-- 5. FACT: ORDERS
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    order_status VARCHAR(32),
    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    purchase_date_key INTEGER,
    order_item_count INTEGER DEFAULT 0,
    total_price NUMERIC(12,2) DEFAULT 0.00,
    total_freight NUMERIC(12,2) DEFAULT 0.00,
    total_payment_value NUMERIC(12,2) DEFAULT 0.00,
    total_order_value NUMERIC(12,2) DEFAULT 0.00,
    max_installments INTEGER DEFAULT 1,
    primary_payment_type VARCHAR(32),
    review_score NUMERIC(3,2),
    actual_delivery_days NUMERIC(8,2),
    estimated_delivery_days NUMERIC(8,2),
    delivery_delay_days NUMERIC(8,2),
    is_delayed INTEGER DEFAULT 0,
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id)
);
CREATE INDEX IF NOT EXISTS idx_fact_orders_cust ON fact_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_orders_date ON fact_orders(purchase_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_orders_delayed ON fact_orders(is_delayed);

-- 6. BUSINESS MART: RFM SEGMENTS
CREATE TABLE IF NOT EXISTS agg_rfm_segments (
    customer_unique_id VARCHAR(64) PRIMARY KEY,
    recency INTEGER NOT NULL,
    frequency INTEGER NOT NULL,
    monetary NUMERIC(12,2) NOT NULL,
    customer_city VARCHAR(128),
    customer_state VARCHAR(8),
    r_score INTEGER NOT NULL,
    f_score INTEGER NOT NULL,
    m_score INTEGER NOT NULL,
    rfm_score VARCHAR(8) NOT NULL,
    customer_segment VARCHAR(64) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rfm_segment ON agg_rfm_segments(customer_segment);

-- 7. BUSINESS MART: MONTHLY EXECUTIVE KPIS
CREATE TABLE IF NOT EXISTS agg_monthly_executive_kpi (
    year_month VARCHAR(8) PRIMARY KEY,
    total_orders INTEGER NOT NULL,
    total_gmv NUMERIC(14,2) NOT NULL,
    avg_order_value NUMERIC(10,2) NOT NULL,
    total_delayed_orders INTEGER NOT NULL,
    avg_review_score NUMERIC(4,2),
    avg_delivery_days NUMERIC(6,2),
    sla_breach_rate_pct NUMERIC(5,2)
);

-- 8. BUSINESS MART: LOGISTICS SANKEY FLOW
CREATE TABLE IF NOT EXISTS agg_logistics_sankey_flow (
    source VARCHAR(128) NOT NULL,
    target VARCHAR(128) NOT NULL,
    volume INTEGER NOT NULL,
    total_gmv NUMERIC(14,2) NOT NULL
);
