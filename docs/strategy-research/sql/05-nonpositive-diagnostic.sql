\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
SET LOCAL lock_timeout = '3s';
SELECT now() AS observed_at, current_setting('transaction_read_only');
SELECT count(*) AS bad_rows, count(DISTINCT stock_id) AS stocks,
min(trading_date),max(trading_date),
count(*) FILTER (WHERE open_price=0 AND high_price=0 AND low_price=0 AND close_price>0) AS zero_ohl_positive_close,
count(*) FILTER (WHERE close_price<=0) AS nonpositive_close,
count(*) FILTER (WHERE trade_volume=0) AS zero_volume,
count(*) FILTER (WHERE open_price<0 OR high_price<0 OR low_price<0 OR close_price<0) AS negative_price
FROM kiwoom.stock_price_krx WHERE adjusted AND
(open_price<=0 OR high_price<=0 OR low_price<=0 OR close_price<=0);
SELECT s.stock_code,count(*) AS bad_rows,min(p.trading_date),max(p.trading_date)
FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
WHERE p.adjusted AND (open_price<=0 OR high_price<=0 OR low_price<=0 OR close_price<=0)
GROUP BY 1 ORDER BY 2 DESC,1 LIMIT 10;
SELECT count(*) AS negative_amount FROM kiwoom.stock_price_krx WHERE trade_amount<0;
COMMIT;
