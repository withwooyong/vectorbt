\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
SET LOCAL lock_timeout = '3s';
SELECT now() AS observed_at, current_setting('transaction_read_only');
SELECT market_code, market_name, is_active, count(*) AS stocks,
count(*) FILTER (WHERE listed_date IS NULL) AS missing_listed_date
FROM kiwoom.stock GROUP BY 1,2,3 ORDER BY 1,2,3;
SELECT adjusted, min(trading_date), max(trading_date), count(*) AS rows,
count(DISTINCT stock_id) AS stocks,
count(*) FILTER (WHERE open_price IS NULL OR high_price IS NULL OR low_price IS NULL OR close_price IS NULL) AS null_ohlc,
count(*) FILTER (WHERE open_price <= 0 OR high_price <= 0 OR low_price <= 0 OR close_price <= 0) AS nonpositive_ohlc,
count(*) FILTER (WHERE high_price < greatest(open_price,close_price,low_price) OR low_price > least(open_price,close_price,high_price)) AS invalid_ohlc,
count(*) FILTER (WHERE trade_volume IS NULL) AS null_volume,
count(*) FILTER (WHERE trade_volume < 0) AS negative_volume,
count(*) FILTER (WHERE trade_volume = 0) AS zero_volume,
count(*) FILTER (WHERE trade_amount IS NULL) AS null_amount
FROM kiwoom.stock_price_krx GROUP BY adjusted ORDER BY adjusted;
SELECT extract(year FROM p.trading_date)::int AS year, s.market_code,
count(*) AS rows, count(DISTINCT p.stock_id) AS stocks,
min(p.trading_date), max(p.trading_date)
FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id = p.stock_id
WHERE p.adjusted GROUP BY 1,2 ORDER BY 1,2;
SELECT s.market_code, count(DISTINCT p.stock_id) AS stocks,
min(p.trading_date), max(p.trading_date), count(*) AS rows
FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
WHERE p.adjusted AND NOT s.is_active GROUP BY 1 ORDER BY 1;
SELECT count(*) AS before_current_listed_date
FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
WHERE p.adjusted AND p.trading_date < s.listed_date;
SELECT count(*) AS orphan_prices FROM kiwoom.stock_price_krx p
LEFT JOIN kiwoom.stock s ON s.id=p.stock_id WHERE s.id IS NULL;
SELECT s.stock_code, s.market_code, s.listed_date,
min(p.trading_date), max(p.trading_date), count(*) AS rows
FROM kiwoom.stock s JOIN kiwoom.stock_price_krx p ON p.stock_id=s.id
WHERE p.adjusted AND s.stock_code IN ('005930','000660','069500')
GROUP BY 1,2,3 ORDER BY 1;
SELECT table_name, column_name, data_type FROM information_schema.columns
WHERE table_schema='kiwoom' AND
(column_name ~* 'delist|adjust|split|dividend|valid_from|valid_to|market|security|instrument|effective|status'
OR table_name='sector')
ORDER BY table_name, ordinal_position;
COMMIT;
