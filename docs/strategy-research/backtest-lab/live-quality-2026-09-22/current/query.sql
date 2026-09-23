\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='180s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object('observed_at',now(),'database',current_database(),'read_only',current_setting('transaction_read_only'),'isolation',current_setting('transaction_isolation'),'scope','Current collection dates/counts/timestamps and revision metadata only; no 2024+ price values'));
SELECT json_build_object('check','revisions','data',json_agg(x)) FROM (SELECT * FROM kiwoom.dataset_revision ORDER BY revision_label) x;
SELECT json_build_object('check','daily_collection','data',json_agg(x)) FROM (
 SELECT 'KRX' venue,trading_date,adjusted,count(*) rows,count(DISTINCT stock_id) instruments,min(fetched_at) first_fetch,max(fetched_at) last_fetch FROM kiwoom.stock_price_krx WHERE trading_date BETWEEN '2026-09-14' AND '2026-09-22' GROUP BY 1,2,3
 UNION ALL SELECT 'NXT',trading_date,adjusted,count(*),count(DISTINCT stock_id),min(fetched_at),max(fetched_at) FROM kiwoom.stock_price_nxt WHERE trading_date BETWEEN '2026-09-14' AND '2026-09-22' GROUP BY 1,2,3 ORDER BY 1,2,3) x;
SELECT json_build_object('check','source_columns','data',json_agg(x)) FROM (SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='kiwoom' AND (table_name IN ('source_request','source_record','source_payload','raw_response','minute_chart_job') OR table_name ILIKE '%job%') ORDER BY table_name,ordinal_position) x;
SELECT json_build_object('check','raw_response_recency','data',json_agg(x)) FROM (SELECT api_id,count(*) rows,max(fetched_at) last_fetch FROM kiwoom.raw_response WHERE fetched_at >= timestamptz '2026-09-14 00:00:00+09' GROUP BY api_id ORDER BY api_id) x;
SELECT json_build_object('check','audit_complete','data',true);
ROLLBACK;
