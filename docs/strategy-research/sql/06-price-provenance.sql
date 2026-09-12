\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
SET LOCAL lock_timeout = '3s';
SELECT now() AS observed_at, current_setting('transaction_read_only');
SELECT column_name, data_type FROM information_schema.columns
WHERE table_schema='kiwoom' AND table_name='stock_price_krx' ORDER BY ordinal_position;
SELECT count(*) AS rows, count(DISTINCT stock_id) AS stocks,
min(trading_date), max(trading_date), count(*) FILTER (WHERE close_price<=0) AS nonpositive_close
FROM kiwoom.stock_price_krx;
SELECT stock_code, stock_name, state, is_active, listed_date,
to_jsonb(s)->>'delisted_date' AS delisted_date
FROM kiwoom.stock s WHERE stock_code='102950';
SELECT extract(year FROM p.trading_date)::int AS year, count(*) AS rows,
count(*) FILTER (WHERE close_price=0) AS zero_close,
count(*) FILTER (WHERE close_price=0 AND trade_volume>0) AS zero_close_positive_volume,
min(close_price),max(close_price),min(fetched_at),max(fetched_at),
min(to_jsonb(p)->>'data_vendor') AS data_vendor
FROM kiwoom.stock_price_krx p
WHERE stock_id=(SELECT id FROM kiwoom.stock WHERE stock_code='102950')
GROUP BY 1 ORDER BY 1;
SELECT trading_date,open_price,high_price,low_price,close_price,trade_volume,trade_amount,
created_at,fetched_at,updated_at FROM kiwoom.stock_price_krx
WHERE stock_id=(SELECT id FROM kiwoom.stock WHERE stock_code='102950')
AND (trading_date BETWEEN '2015-01-02' AND '2015-01-06'
 OR trading_date BETWEEN '2019-11-25' AND '2019-12-06') ORDER BY trading_date;
SELECT count(*) AS saved_ka10081_responses,min(fetched_at),max(fetched_at)
FROM kiwoom.raw_response WHERE api_id='ka10081';
COMMIT;
