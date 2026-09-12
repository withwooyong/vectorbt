\set ON_ERROR_STOP on
-- Fixed completed session; values are proposed calculations, not HTS parity.
\set as_of '2026-09-10'
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
SET LOCAL lock_timeout = '3s';
SELECT now() AS observed_at, current_setting('transaction_read_only'), :'as_of' AS as_of;
-- Current three-code sample, including one ETF. Do not remove invalid bars
-- before computing windows: doing so silently changes the meaning of a bar.
WITH bars AS (
 SELECT s.stock_code,p.*,
 lag(trade_volume) OVER w AS previous_volume,
 lag(trading_date) OVER w AS previous_date,
 count(close_price) OVER w60 AS count60,
 min(close_price) OVER w60 AS min60,
 sum(close_price::numeric) OVER w60 AS sum60,
 count(close_price) OVER w20 AS count20,
 min(close_price) OVER w20 AS min20,
 max(close_price) OVER w20 AS prior20_max
 FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
 WHERE s.stock_code IN ('005930','000660','069500') AND p.adjusted
 AND p.trading_date<=:'as_of'::date
 WINDOW w AS (PARTITION BY stock_id ORDER BY trading_date),
 w60 AS (PARTITION BY stock_id ORDER BY trading_date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW),
 w20 AS (PARTITION BY stock_id ORDER BY trading_date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING)
)
SELECT stock_code,trading_date,previous_date,close_price,previous_volume,count60,
round(sum60/60,6) AS sma60,count20,prior20_max,
CASE WHEN previous_volume>=0 THEN previous_volume>=100000 END AS volume_condition,
CASE WHEN count60=60 AND min60>0 THEN close_price::numeric*60>sum60 END AS sma_condition,
CASE WHEN count20=20 AND min20>0 AND close_price>0 THEN close_price>prior20_max END AS high_condition
FROM bars WHERE trading_date=:'as_of'::date ORDER BY stock_code;
COMMIT;
