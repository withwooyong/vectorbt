\set ON_ERROR_STOP on
\pset format unaligned
\pset tuples_only on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='30s';
WITH ranked AS (
 SELECT s.stock_code,p.trading_date,p.close_price,p.trade_volume,
 row_number() OVER (PARTITION BY p.stock_id ORDER BY p.trading_date DESC) AS rn
 FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
 WHERE s.stock_code IN ('005930','000660','069500') AND p.adjusted
 AND p.trading_date<='2026-09-10'::date
)
SELECT json_build_object('observed_at',now(),'read_only',current_setting('transaction_read_only'),
'rows',json_agg(r ORDER BY stock_code,trading_date))
FROM (SELECT stock_code,trading_date,close_price,trade_volume FROM ranked WHERE rn<=60) r;
COMMIT;
