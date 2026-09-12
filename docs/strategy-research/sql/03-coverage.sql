\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
SET LOCAL lock_timeout = '3s';
SELECT now() AS observed_at;
SELECT extract(year FROM p.trading_date)::int AS year, s.market_name,
count(*) AS rows, count(DISTINCT p.stock_id) AS stocks
FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
WHERE p.adjusted AND s.market_code='0'
GROUP BY 1,2 ORDER BY 1,2;
WITH coverage AS (
 SELECT stock_id, min(trading_date) AS first_date, max(trading_date) AS last_date, count(*) AS n
 FROM kiwoom.stock_price_krx WHERE adjusted GROUP BY stock_id
)
SELECT n, count(*) AS stocks, min(first_date), max(first_date)
FROM coverage GROUP BY n ORDER BY stocks DESC, n DESC LIMIT 12;
SELECT s.stock_code, s.stock_name, s.market_name, s.listed_date,
min(p.trading_date) AS first_price, count(*) AS before_listing_rows
FROM kiwoom.stock s JOIN kiwoom.stock_price_krx p ON p.stock_id=s.id
WHERE p.adjusted AND p.trading_date<s.listed_date
GROUP BY 1,2,3,4 ORDER BY before_listing_rows DESC LIMIT 10;
SELECT trading_date, count(*) AS exchange_stock_rows,
count(*) FILTER (WHERE trade_volume=0) AS zero_volume
FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
WHERE p.adjusted AND s.market_code='0' AND s.market_name='거래소'
AND trading_date >= DATE '2026-09-01'
GROUP BY 1 ORDER BY 1;
SELECT s.stock_code, p.trading_date, p.open_price, p.high_price, p.low_price,
p.close_price, p.trade_volume, p.trade_amount
FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
WHERE s.stock_code='005930' AND p.adjusted AND p.trading_date=DATE '2026-09-01';
SELECT s.market_code, s.sector_code, s.sector_name,
min(p.trading_date), max(p.trading_date), count(*) AS rows
FROM kiwoom.sector s JOIN kiwoom.sector_price_daily p ON p.sector_id=s.id
WHERE s.sector_code IN ('001','101') GROUP BY 1,2,3 ORDER BY 1,2;
COMMIT;
