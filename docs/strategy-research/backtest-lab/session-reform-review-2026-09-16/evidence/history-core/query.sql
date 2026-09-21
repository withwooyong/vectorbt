\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='90s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object(
 'observed_at',now(),'database',current_database(),'read_only',current_setting('transaction_read_only'),
 'date_from','2015-01-02','date_to','2023-12-31'));
SELECT json_build_object('check','tables','data',coalesce(json_agg(t),'[]'::json))
FROM (SELECT table_name FROM information_schema.tables WHERE table_schema='kiwoom' ORDER BY table_name) t;
SELECT json_build_object('check','reference_columns','data',coalesce(json_agg(t),'[]'::json))
FROM (SELECT table_name,column_name,data_type FROM information_schema.columns
 WHERE table_schema='kiwoom' AND table_name IN ('stock','trading_halt','raw_response','stock_price_krx')
 ORDER BY table_name,ordinal_position) t;
SELECT json_build_object('check','price_state_quality','data',coalesce(json_agg(t),'[]'::json))
FROM (SELECT adjusted,data_vendor,price_state,count(*) AS rows,count(DISTINCT stock_id) AS stock_ids,
 min(trading_date) AS first_date,max(trading_date) AS last_date,
 count(*) FILTER (WHERE open_price IS NULL OR high_price IS NULL OR low_price IS NULL OR close_price IS NULL OR trade_volume IS NULL) AS null_ohlcv,
 count(*) FILTER (WHERE open_price<=0 OR high_price<=0 OR low_price<=0 OR close_price<=0) AS nonpositive_ohlc,
 count(*) FILTER (WHERE high_price<greatest(open_price,close_price,low_price) OR low_price>least(open_price,close_price,high_price)) AS inconsistent_ohlc,
 count(*) FILTER (WHERE trade_volume<0) AS negative_volume,
 count(*) FILTER (WHERE trade_volume=0) AS zero_volume,
 count(*) FILTER (WHERE price_state='TRADED' AND trade_volume=0) AS traded_zero_volume,
 count(*) FILTER (WHERE price_state IN ('HALTED','NO_TRADE') AND trade_volume>0) AS nontraded_positive_volume
 FROM kiwoom.stock_price_krx WHERE trading_date BETWEEN '2015-01-02' AND '2023-12-31'
 GROUP BY adjusted,data_vendor,price_state ORDER BY adjusted,data_vendor,price_state) t;
SELECT json_build_object('check','unexplained_traded_keys','data',coalesce(json_agg(t),'[]'::json))
FROM (SELECT s.stock_code,p.stock_id,p.trading_date,p.adjusted,p.data_vendor,p.price_state,
 p.open_price,p.high_price,p.low_price,p.close_price,p.trade_volume
 FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
 WHERE p.trading_date BETWEEN '2015-01-02' AND '2023-12-31' AND p.price_state='TRADED'
 AND (p.open_price<=0 OR p.high_price<=0 OR p.low_price<=0 OR p.close_price<=0)
 ORDER BY p.stock_id,p.trading_date,p.adjusted LIMIT 100) t;
SELECT json_build_object('check','audit_complete','data',true);
COMMIT;
