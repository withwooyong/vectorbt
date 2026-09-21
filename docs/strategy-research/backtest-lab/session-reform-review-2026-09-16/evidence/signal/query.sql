\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='90s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object('observed_at',now(),'database',current_database(),'read_only',current_setting('transaction_read_only'),'scope','latest row counts only; 2015-2023 price quality'));
SELECT json_build_object('check','schema_revision','data',version_num) FROM public.alembic_version;
SELECT json_build_object('check','current_coverage','data',coalesce(json_agg(t),'[]'::json)) FROM (SELECT trading_date,count(*) AS rows,count(DISTINCT stock_id) AS stocks,max(created_at) AS last_created FROM public.stock_price WHERE trading_date BETWEEN '2026-09-07' AND '2026-09-16' GROUP BY trading_date ORDER BY trading_date) t;
SELECT json_build_object('check','historical_quality','data',coalesce(json_agg(t),'[]'::json)) FROM (
 SELECT price_state,count(*) AS rows,count(DISTINCT stock_id) AS stocks,
 count(*) FILTER (WHERE open_price<=0 OR high_price<=0 OR low_price<=0 OR close_price<=0) AS nonpositive_ohlc,
 count(*) FILTER (WHERE high_price<greatest(open_price,close_price,low_price) OR low_price>least(open_price,close_price,high_price)) AS inconsistent_ohlc,
 count(*) FILTER (WHERE volume<0) AS negative_volume
 FROM public.stock_price WHERE trading_date BETWEEN '2015-01-02' AND '2023-12-31' GROUP BY price_state ORDER BY price_state) t;
SELECT json_build_object('check','phantom_copy_counts','data',coalesce(json_agg(t),'[]'::json)) FROM (
 SELECT s.stock_code,count(*) AS rows FROM public.stock_price p JOIN public.stock s ON s.id=p.stock_id
 JOIN (VALUES ('013890',date '2019-10-30'),('036220',date '2024-03-13'),('037030',date '2018-06-07'),('042000',date '2018-02-08'),('047920',date '2015-12-21'),('053580',date '2019-01-25'),('062970',date '2019-12-26'),('085620',date '2015-07-08'),('089590',date '2015-11-06'),('092190',date '2020-03-06'),('096250',date '2025-01-24'),('244920',date '2020-11-20')) AS v(code,listed_date) ON v.code=s.stock_code
 WHERE p.trading_date BETWEEN '2015-01-02' AND '2023-12-31' AND p.trading_date<v.listed_date GROUP BY s.stock_code ORDER BY s.stock_code) t;
SELECT json_build_object('check','tables','data',coalesce(json_agg(t),'[]'::json)) FROM (SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name) t;
SELECT json_build_object('check','audit_complete','data',true);
COMMIT;
