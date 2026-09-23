\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='180s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object('observed_at',now(),'read_only',current_setting('transaction_read_only'),'isolation',current_setting('transaction_isolation'),'scope','Request status/timestamps only; price content hash limited to 2014-2023'));
SELECT json_build_object('check','source_requests','data',json_agg(x)) FROM (
 SELECT q.source_code,q.endpoint,q.response_status,q.capture_kind,count(DISTINCT q.request_id) requests,
 max(q.requested_at) last_requested_at,max(p.captured_at) last_captured_at,
 count(DISTINCT q.request_id) FILTER(WHERE p.payload_id IS NULL) requests_without_payload
 FROM kiwoom.source_request q LEFT JOIN kiwoom.source_payload p USING(request_id)
 WHERE q.requested_at>=timestamptz '2026-09-19 00:00:00+09'
 GROUP BY 1,2,3,4 ORDER BY 1,2,3,4) x;
SELECT json_build_object('check','price_content_hash','data',row_to_json(x)) FROM (
 WITH daily AS (
 SELECT trading_date,encode(sha256(convert_to(string_agg(to_jsonb(p)::text,E'\n' ORDER BY stock_id,adjusted),'UTF8')),'hex') h,count(*) n
 FROM kiwoom.backtest_price_v2 p WHERE trading_date BETWEEN '2014-01-01' AND '2023-12-31' GROUP BY trading_date)
 SELECT sum(n) actual_rows,encode(sha256(convert_to(string_agg(h,E'\n' ORDER BY trading_date),'UTF8')),'hex') actual_content_sha256 FROM daily
) x;
SELECT json_build_object('check','audit_complete','data',true);
ROLLBACK;
