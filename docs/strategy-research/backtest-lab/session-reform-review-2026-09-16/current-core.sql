\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='90s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object('observed_at',now(),'database',current_database(),'read_only',current_setting('transaction_read_only'),'scope','latest counts/timestamps only; no 2024+ price values'));
SELECT json_build_object('check','current_daily_coverage','data',coalesce(json_agg(t),'[]'::json)) FROM (
 SELECT 'KRX' AS venue,trading_date,adjusted,count(*) AS rows,count(DISTINCT stock_id) AS stocks,min(fetched_at) AS first_fetch,max(fetched_at) AS last_fetch,
 count(*) FILTER (WHERE fetched_at AT TIME ZONE 'Asia/Seoul' < trading_date + time '20:00') AS fetched_before_20
 FROM kiwoom.stock_price_krx WHERE trading_date BETWEEN '2026-09-07' AND '2026-09-16' GROUP BY trading_date,adjusted
 UNION ALL SELECT 'NXT',trading_date,adjusted,count(*),count(DISTINCT stock_id),min(fetched_at),max(fetched_at),
 count(*) FILTER (WHERE fetched_at AT TIME ZONE 'Asia/Seoul' < trading_date + time '20:00')
 FROM kiwoom.stock_price_nxt WHERE trading_date BETWEEN '2026-09-07' AND '2026-09-16' GROUP BY trading_date,adjusted
 ORDER BY venue,trading_date,adjusted) t;
SELECT json_build_object('check','minute_session_coverage','data',coalesce(json_agg(t),'[]'::json)) FROM (
 SELECT exchange,tic_scope,adjusted,(bucket_at AT TIME ZONE 'Asia/Seoul')::date AS day,
 CASE WHEN (bucket_at AT TIME ZONE 'Asia/Seoul')::time < time '09:00' THEN 'pre_09'
 WHEN (bucket_at AT TIME ZONE 'Asia/Seoul')::time < time '15:30' THEN '09_1530'
 WHEN (bucket_at AT TIME ZONE 'Asia/Seoul')::time < time '16:00' THEN '1530_16'
 ELSE 'after_16' END AS session_band,
 count(*) AS rows,count(DISTINCT stock_id) AS stocks,min(bucket_at AT TIME ZONE 'Asia/Seoul') AS first_bucket,max(bucket_at AT TIME ZONE 'Asia/Seoul') AS last_bucket,max(fetched_at) AS last_fetch
 FROM kiwoom.stock_minute_price WHERE bucket_at >= timestamptz '2026-09-10 00:00:00+09' AND bucket_at < timestamptz '2026-09-17 00:00:00+09'
 GROUP BY exchange,tic_scope,adjusted,day,session_band ORDER BY day,exchange,tic_scope,session_band) t;
SELECT json_build_object('check','master_counts','data',json_build_object('stocks',count(*),'active',count(*) FILTER (WHERE is_active),'nxt_enabled',count(*) FILTER (WHERE nxt_enable),'phantom_stocks',count(*) FILTER (WHERE pre_listing_verdict='PHANTOM'))) FROM kiwoom.stock;
SELECT json_build_object('check','quarantine','data',json_build_object('rows',count(*),'stocks',count(DISTINCT stock_id))) FROM kiwoom.stock_price_krx_prelisting;
SELECT json_build_object('check','raw_response_api_counts','data',coalesce(json_agg(t),'[]'::json)) FROM (SELECT api_id,count(*) AS rows,max(fetched_at) AS last_fetch FROM kiwoom.raw_response GROUP BY api_id ORDER BY api_id) t;
SELECT json_build_object('check','tables','data',coalesce(json_agg(t),'[]'::json)) FROM (SELECT table_name FROM information_schema.tables WHERE table_schema='kiwoom' ORDER BY table_name) t;
SELECT json_build_object('check','audit_complete','data',true);
COMMIT;
