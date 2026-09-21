\set ON_ERROR_STOP on
-- Core table audit: price reads are restricted to the approved development period.
-- Current stock metadata is diagnostic only, not historical point-in-time truth.
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '90s';
SET LOCAL lock_timeout = '3s';

SELECT json_build_object('check', 'context', 'data', json_build_object(
    'observed_at', now(), 'database', current_database(),
    'read_only', current_setting('transaction_read_only'),
    'isolation', current_setting('transaction_isolation'),
    'date_from', '2015-01-02', 'date_to', '2023-12-31',
    'scope', 'All vendors and adjustment states; current stock metadata; raw response count only'));

SELECT json_build_object('check','core_tables','data',coalesce(json_agg(t),'[]'::json)) FROM (
    SELECT table_name FROM information_schema.tables
    WHERE table_schema='kiwoom' AND table_type='BASE TABLE' ORDER BY table_name
) t;

SELECT json_build_object('check', 'core_columns', 'data', coalesce(json_agg(t), '[]'::json))
FROM (
    SELECT table_name, column_name, data_type, udt_name, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'kiwoom' AND table_name IN ('stock', 'stock_price_krx')
    ORDER BY table_name, ordinal_position
) t;

SELECT json_build_object('check', 'core_constraints', 'data', coalesce(json_agg(t), '[]'::json))
FROM (
    SELECT c.relname AS table_name, con.conname, con.contype, con.convalidated,
           pg_get_constraintdef(con.oid) AS definition
    FROM pg_constraint con JOIN pg_class c ON c.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'kiwoom' AND c.relname IN ('stock', 'stock_price_krx')
    ORDER BY c.relname, con.conname
) t;

SELECT json_build_object('check', 'core_indexes', 'data', coalesce(json_agg(t), '[]'::json))
FROM (
    SELECT tablename, indexname, indexdef FROM pg_indexes
    WHERE schemaname = 'kiwoom' AND tablename IN ('stock', 'stock_price_krx')
    ORDER BY tablename, indexname
) t;

-- GROUPING distinguishes actual NULL dimension values from aggregate totals.
WITH profile AS (
    SELECT grouping(data_vendor, adjusted, extract(year FROM trading_date)::int) AS grouping_mask,
           data_vendor, adjusted, extract(year FROM trading_date)::int AS year,
           count(*) AS rows, count(DISTINCT stock_id) AS stock_ids,
           min(trading_date) AS first_date, max(trading_date) AS last_date,
           count(*) FILTER (WHERE stock_id IS NULL) AS null_stock_id,
           count(*) FILTER (WHERE data_vendor IS NULL OR btrim(data_vendor) = '') AS missing_vendor,
           count(*) FILTER (WHERE adjusted IS NULL) AS null_adjusted,
           count(*) FILTER (WHERE open_price IS NULL) AS null_open,
           count(*) FILTER (WHERE high_price IS NULL) AS null_high,
           count(*) FILTER (WHERE low_price IS NULL) AS null_low,
           count(*) FILTER (WHERE close_price IS NULL) AS null_close,
           count(*) FILTER (WHERE open_price <= 0 OR high_price <= 0 OR low_price <= 0
                                      OR close_price <= 0) AS nonpositive_ohlc,
           count(*) FILTER (WHERE close_price = 0) AS zero_close,
           count(*) FILTER (WHERE high_price < greatest(open_price, close_price, low_price)
                            OR low_price > least(open_price, close_price, high_price)) AS inconsistent_ohlc,
           count(*) FILTER (WHERE high_price < close_price AND trade_volume > 0) AS high_below_close_positive_volume,
           count(*) FILTER (WHERE open_price = 0 AND high_price = 0 AND low_price = 0
                            AND close_price > 0 AND trade_volume = 0) AS zero_ohl_positive_close_zero_volume,
           count(*) FILTER (WHERE trade_volume IS NULL) AS null_volume,
           count(*) FILTER (WHERE trade_volume < 0) AS negative_volume,
           count(*) FILTER (WHERE trade_volume = 0) AS zero_volume,
           count(*) FILTER (WHERE trade_amount IS NULL) AS null_amount,
           count(*) FILTER (WHERE trade_amount < 0) AS negative_amount,
           count(*) FILTER (WHERE extract(isodow FROM trading_date) IN (6, 7)) AS weekend_rows,
           count(*) FILTER (WHERE open_price::text IN ('NaN', 'Infinity', '-Infinity')
                            OR high_price::text IN ('NaN', 'Infinity', '-Infinity')
                            OR low_price::text IN ('NaN', 'Infinity', '-Infinity')
                            OR close_price::text IN ('NaN', 'Infinity', '-Infinity')
                            OR trade_volume::text IN ('NaN', 'Infinity', '-Infinity')
                            OR trade_amount::text IN ('NaN', 'Infinity', '-Infinity')) AS nonfinite_rows
    FROM kiwoom.stock_price_krx
    WHERE trading_date BETWEEN DATE '2015-01-02' AND DATE '2023-12-31'
    GROUP BY GROUPING SETS ((), (data_vendor, adjusted),
                           (data_vendor, adjusted, extract(year FROM trading_date)::int))
)
SELECT json_build_object('check', 'price_profile_before_join', 'data', json_agg(t))
FROM (SELECT * FROM profile ORDER BY grouping_mask DESC, data_vendor, adjusted, year) t;

WITH duplicates AS (
    SELECT stock_id, trading_date, adjusted, count(*) AS rows
    FROM kiwoom.stock_price_krx
    WHERE trading_date BETWEEN DATE '2015-01-02' AND DATE '2023-12-31'
    GROUP BY stock_id, trading_date, adjusted HAVING count(*) > 1
)
SELECT json_build_object('check', 'price_natural_key_duplicates', 'data', json_build_object(
    'key', 'stock_id,trading_date,adjusted', 'duplicate_groups', count(*),
    'excess_rows', coalesce(sum(rows - 1), 0))) FROM duplicates;

SELECT json_build_object('check', 'stock_current_metadata', 'data', row_to_json(t)) FROM (
    SELECT count(*) AS rows,
           count(*) FILTER (WHERE stock_code IS NULL OR btrim(stock_code) = '') AS missing_code,
           count(*) FILTER (WHERE stock_code <> btrim(stock_code)) AS padded_code,
           count(*) FILTER (WHERE stock_name IS NULL OR btrim(stock_name) = '') AS missing_name,
           count(*) FILTER (WHERE market_code IS NULL OR btrim(market_code) = '') AS missing_market,
           count(*) FILTER (WHERE listed_date IS NULL) AS missing_listed_date,
           count(*) FILTER (WHERE delisted_date IS NULL) AS missing_delisted_date,
           count(*) FILTER (WHERE is_active IS NULL) AS missing_active,
           count(*) FILTER (WHERE NOT is_active AND delisted_date IS NULL) AS inactive_without_delisted_date,
           count(*) FILTER (WHERE delisted_date < listed_date) AS inverted_listing_dates,
           'Current metadata only; missing delisted date is expected for active stocks' AS interpretation
    FROM kiwoom.stock
) t;

SELECT json_build_object('check', 'stock_code_duplicates', 'data', coalesce(json_agg(t), '[]'::json)) FROM (
    SELECT btrim(stock_code) AS normalized_code, count(*) AS rows,
           count(DISTINCT stock_code) AS distinct_raw_codes
    FROM kiwoom.stock GROUP BY btrim(stock_code) HAVING count(*) > 1
    ORDER BY rows DESC, normalized_code
) t;

-- Per-stock aggregates share one scan for orphan, current dates and top anomalies.
WITH per_stock AS MATERIALIZED (
    SELECT p.stock_id, p.data_vendor, p.adjusted, count(*) AS rows,
           min(p.trading_date) AS first_date, max(p.trading_date) AS last_date,
           count(*) FILTER (WHERE s.id IS NULL) AS orphan_rows,
           count(*) FILTER (WHERE p.trading_date < s.listed_date) AS before_current_listing,
           count(*) FILTER (WHERE p.trading_date > s.delisted_date) AS after_current_delisting,
           count(*) FILTER (WHERE p.open_price IS NULL OR p.high_price IS NULL OR p.low_price IS NULL
                            OR p.close_price IS NULL OR p.trade_volume IS NULL
                            OR p.open_price <= 0 OR p.high_price <= 0 OR p.low_price <= 0
                            OR p.close_price <= 0 OR p.trade_volume < 0
                            OR p.high_price < greatest(p.open_price, p.close_price, p.low_price)
                            OR p.low_price > least(p.open_price, p.close_price, p.high_price)
                            OR p.open_price::text IN ('NaN', 'Infinity', '-Infinity')
                            OR p.high_price::text IN ('NaN', 'Infinity', '-Infinity')
                            OR p.low_price::text IN ('NaN', 'Infinity', '-Infinity')
                            OR p.close_price::text IN ('NaN', 'Infinity', '-Infinity')
                            OR p.trade_volume::text IN ('NaN', 'Infinity', '-Infinity')) AS invalid_ohlcv_rows
    FROM kiwoom.stock_price_krx p LEFT JOIN kiwoom.stock s ON s.id = p.stock_id
    WHERE p.trading_date BETWEEN DATE '2015-01-02' AND DATE '2023-12-31'
    GROUP BY p.stock_id, p.data_vendor, p.adjusted
)
SELECT json_build_object('check', 'price_stock_relationships', 'data', json_build_object(
    'summary', (SELECT row_to_json(t) FROM (
        SELECT coalesce(sum(rows), 0) AS joined_rows,
               coalesce(sum(orphan_rows), 0) AS orphan_rows,
               coalesce(sum(before_current_listing), 0) AS before_current_listing,
               coalesce(sum(after_current_delisting), 0) AS after_current_delisting,
               coalesce(sum(invalid_ohlcv_rows), 0) AS invalid_ohlcv_rows,
               count(DISTINCT stock_id) FILTER(WHERE invalid_ohlcv_rows>0) AS invalid_ohlcv_stock_ids
        FROM per_stock
    ) t),
    'top_10_invalid_stock_vendor_groups', (SELECT coalesce(json_agg(t), '[]'::json) FROM (
        SELECT p.*, s.stock_code FROM per_stock p LEFT JOIN kiwoom.stock s ON s.id = p.stock_id
        WHERE p.invalid_ohlcv_rows > 0
        ORDER BY p.invalid_ohlcv_rows DESC, p.stock_id, p.data_vendor, p.adjusted LIMIT 10
    ) t),
    'mixed_vendor_stock_adjustment_groups', (SELECT count(*) FROM (
        SELECT stock_id, adjusted FROM per_stock GROUP BY stock_id, adjusted
        HAVING count(*) > 1
    ) t),
    'interpretation', 'Listing date comparisons use current metadata; no historical validity claim'));

WITH duplicates AS (
    SELECT s.stock_code, p.trading_date, p.adjusted, count(*) AS rows,
           count(DISTINCT p.stock_id) AS stock_ids
    FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id = p.stock_id
    WHERE p.trading_date BETWEEN DATE '2015-01-02' AND DATE '2023-12-31'
    GROUP BY s.stock_code, p.trading_date, p.adjusted HAVING count(*) > 1
)
SELECT json_build_object('check', 'price_code_date_duplicates', 'data', json_build_object(
    'key', 'stock_code,trading_date,adjusted', 'duplicate_groups', count(*),
    'excess_rows', coalesce(sum(rows - 1), 0),
    'cross_stock_id_groups', count(*) FILTER (WHERE stock_ids > 1))) FROM duplicates;

-- Only internal absent dates relative to the observed panel are candidates.
-- No exchange calendar, listing-universe or suspension truth is inferred.
WITH observed AS MATERIALIZED (
    SELECT DISTINCT stock_id, adjusted, trading_date FROM kiwoom.stock_price_krx
    WHERE trading_date BETWEEN DATE '2015-01-02' AND DATE '2023-12-31'
), calendar AS (
    SELECT adjusted, trading_date,
           row_number() OVER (PARTITION BY adjusted ORDER BY trading_date) AS day_number
    FROM (SELECT DISTINCT adjusted, trading_date FROM observed) d
), bounds AS (
    SELECT o.stock_id, o.adjusted, min(o.trading_date) AS first_date, max(o.trading_date) AS last_date,
           count(*) AS observed_dates, max(c.day_number) - min(c.day_number) + 1 - count(*) AS gap_candidates
    FROM observed o JOIN calendar c ON o.trading_date = c.trading_date
         AND o.adjusted IS NOT DISTINCT FROM c.adjusted
    GROUP BY o.stock_id, o.adjusted
)
SELECT json_build_object('check', 'observed_calendar_internal_gap_candidates', 'data', json_build_object(
    'stock_adjustment_groups', (SELECT count(*) FROM bounds),
    'groups_with_gaps', (SELECT count(*) FROM bounds WHERE gap_candidates > 0),
    'missing_observed_panel_dates', (SELECT coalesce(sum(gap_candidates), 0) FROM bounds),
    'top_10', (SELECT coalesce(json_agg(t), '[]'::json) FROM (
        SELECT b.*, s.stock_code FROM bounds b LEFT JOIN kiwoom.stock s ON s.id = b.stock_id
        WHERE b.gap_candidates > 0 ORDER BY b.gap_candidates DESC, b.stock_id, b.adjusted LIMIT 10
    ) t),
    'interpretation', 'Internal gaps against observed dates per adjustment state; not an official trading calendar; suspensions may explain gaps'));

-- Counts only: no raw response body or held-out price data is selected.
SELECT json_build_object('check', 'raw_response_ka10081_count', 'data', json_build_object(
    'rows', count(*), 'scope', 'Metadata count across saved responses; response bodies not read'))
FROM kiwoom.raw_response WHERE api_id = 'ka10081';
SELECT json_build_object('check','audit_complete','data',true);
COMMIT;
