\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
SET LOCAL lock_timeout = '3s';
SELECT json_build_object(
 'observed_at', now(), 'read_only', current_setting('transaction_read_only'),
 'database', current_database(), 'groups', json_agg(q)
)
FROM (
 SELECT adjusted, count(*) AS rows, count(DISTINCT stock_id) AS stocks,
 min(trading_date) AS first_date, max(trading_date) AS last_date,
 count(*) FILTER (WHERE close_price<=0) AS nonpositive_close,
 count(*) FILTER (WHERE open_price<=0 OR high_price<=0 OR low_price<=0 OR close_price<=0) AS nonpositive_ohlc,
 count(*) FILTER (WHERE open_price IS NULL OR high_price IS NULL OR low_price IS NULL OR close_price IS NULL) AS null_ohlc,
 count(*) FILTER (WHERE trade_volume=0) AS zero_volume
 FROM kiwoom.stock_price_krx GROUP BY adjusted ORDER BY adjusted
) q;
COMMIT;
