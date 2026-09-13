\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='60s';
SET LOCAL lock_timeout='3s';
SELECT now() AS observed_at,current_setting('transaction_read_only');
SELECT data_vendor,adjusted,count(*) AS rows,count(DISTINCT stock_id) AS symbols,
 min(trading_date),max(trading_date),count(*) FILTER(WHERE close_price=0) AS zero_close,
 count(*) FILTER(WHERE open_price IS NULL OR high_price IS NULL OR low_price IS NULL
 OR close_price IS NULL OR trade_volume IS NULL OR open_price<=0 OR high_price<=0
 OR low_price<=0 OR close_price<=0 OR trade_volume<0
 OR high_price<greatest(open_price,close_price,low_price)
 OR low_price>least(open_price,close_price,high_price)) AS invalid_ohlcv
FROM kiwoom.stock_price_krx
WHERE trading_date BETWEEN '2015-01-02' AND '2023-12-31'
GROUP BY 1,2 ORDER BY 1,2;
SELECT count(*) AS saved_ka10081_responses FROM kiwoom.raw_response WHERE api_id='ka10081';
-- 아래 패턴 분해는 같은 세션의 별도 읽기 전용 트랜잭션에서도 재확인했다.
SELECT data_vendor,
 count(*) FILTER(WHERE high_price<close_price) AS high_below_close,
 count(*) FILTER(WHERE high_price<close_price AND trade_volume>0) AS high_below_close_positive_volume,
 count(*) FILTER(WHERE high_price<close_price AND trade_volume=0) AS high_below_close_zero_volume,
 count(*) FILTER(WHERE open_price=0 AND high_price=0 AND low_price=0 AND close_price>0 AND trade_volume=0)
 AS zero_ohl_positive_close_no_volume
FROM kiwoom.stock_price_krx WHERE adjusted
AND trading_date BETWEEN '2015-01-02' AND '2023-12-31' GROUP BY data_vendor ORDER BY data_vendor;
SELECT table_name FROM information_schema.tables
WHERE table_schema='kiwoom' AND table_type='BASE TABLE' ORDER BY table_name;
COMMIT;
