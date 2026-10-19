CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    month date PRIMARY KEY, year integer NOT NULL, quarter integer NOT NULL, month_number integer NOT NULL
);
CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_id integer PRIMARY KEY, product text NOT NULL UNIQUE, category text NOT NULL, launch_date date NOT NULL
);
CREATE TABLE IF NOT EXISTS warehouse.dim_region (
    region_id integer PRIMARY KEY, territory text NOT NULL UNIQUE, country text NOT NULL
);
CREATE TABLE IF NOT EXISTS warehouse.dim_rep (
    rep_id integer PRIMARY KEY, rep_name text NOT NULL, region_id integer NOT NULL REFERENCES warehouse.dim_region
);
CREATE TABLE IF NOT EXISTS warehouse.dim_channel (
    channel_id integer PRIMARY KEY, channel text NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS warehouse.fact_sales (
    month date REFERENCES warehouse.dim_date, product_id integer REFERENCES warehouse.dim_product,
    region_id integer REFERENCES warehouse.dim_region, rep_id integer REFERENCES warehouse.dim_rep,
    channel_id integer REFERENCES warehouse.dim_channel, units integer NOT NULL CHECK (units >= 0),
    revenue numeric(16,2) NOT NULL CHECK (revenue >= 0), promotion boolean NOT NULL,
    PRIMARY KEY (month, product_id, region_id, rep_id, channel_id)
);
CREATE TABLE IF NOT EXISTS warehouse.fact_targets (
    month date REFERENCES warehouse.dim_date, product_id integer REFERENCES warehouse.dim_product,
    region_id integer REFERENCES warehouse.dim_region, channel_id integer REFERENCES warehouse.dim_channel,
    target numeric(16,2) NOT NULL CHECK (target >= 0),
    PRIMARY KEY (month, product_id, region_id, channel_id)
);
CREATE TABLE IF NOT EXISTS app.etl_runs (
    run_id uuid PRIMARY KEY, started_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz,
    status text NOT NULL, seed integer NOT NULL, data_version text, accepted integer DEFAULT 0,
    rejected integer DEFAULT 0, error text
);
CREATE TABLE IF NOT EXISTS app.dq_results (
    run_id uuid REFERENCES app.etl_runs, check_name text, passed boolean NOT NULL, details jsonb NOT NULL,
    PRIMARY KEY (run_id, check_name)
);
CREATE TABLE IF NOT EXISTS app.metadata (key text PRIMARY KEY, value jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS app.sessions (
    session_id uuid PRIMARY KEY, context jsonb NOT NULL DEFAULT '{}', updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS app.runs (
    run_id uuid PRIMARY KEY, session_id uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
    question text NOT NULL, response jsonb NOT NULL, latency_ms integer NOT NULL
);
CREATE TABLE IF NOT EXISTS app.feedback (
    run_id uuid REFERENCES app.runs, session_id uuid NOT NULL, vote integer CHECK (vote IN (-1,1)),
    created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (run_id, session_id)
);
CREATE TABLE IF NOT EXISTS app.briefs (
    brief_id uuid PRIMARY KEY, session_id uuid NOT NULL, title text NOT NULL, content jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.request_budgets (
    bucket text NOT NULL, window_start timestamptz NOT NULL, used integer NOT NULL CHECK(used > 0),
    PRIMARY KEY(bucket, window_start)
);
CREATE INDEX IF NOT EXISTS runs_session_time ON app.runs(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS briefs_session_time ON app.briefs(session_id, created_at DESC);

-- Aggregate BEFORE joining targets: targets have no rep dimension.
CREATE OR REPLACE VIEW analytics.v_sales_monthly AS
WITH sales AS (
    SELECT month, product_id, region_id, channel_id, sum(revenue) AS revenue, sum(units) AS units,
           bool_or(promotion) AS promotion
    FROM warehouse.fact_sales GROUP BY month, product_id, region_id, channel_id
)
SELECT s.month::text AS month, p.product, p.category, r.country, r.territory, c.channel,
       s.revenue, s.units, t.target, s.promotion
FROM sales s
JOIN warehouse.fact_targets t USING (month, product_id, region_id, channel_id)
JOIN warehouse.dim_product p USING (product_id)
JOIN warehouse.dim_region r USING (region_id)
JOIN warehouse.dim_channel c USING (channel_id);

CREATE OR REPLACE VIEW analytics.v_performance AS
SELECT *, revenue - target AS gap,
       revenue / nullif(target, 0) * 100 AS attainment,
       lag(revenue, 12) OVER (PARTITION BY product, territory, channel ORDER BY month) AS prior_year_revenue
FROM analytics.v_sales_monthly;

REVOKE ALL ON SCHEMA warehouse, analytics, app FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA analytics TO ciq_reader, ciq_app;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO ciq_reader, ciq_app;
GRANT USAGE ON SCHEMA app TO ciq_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA app TO ciq_app;
ALTER ROLE ciq_reader SET default_transaction_read_only = on;
ALTER ROLE ciq_reader SET statement_timeout = '3000ms';
ALTER ROLE ciq_reader SET search_path = analytics;

