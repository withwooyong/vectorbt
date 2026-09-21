\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='90s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object('observed_at',now(),
 'database',current_database(),'read_only',current_setting('transaction_read_only'),
 'date_from','2015-01-02','date_to','2023-12-31'));
SELECT json_build_object('check','affected_symbols','data',coalesce(json_agg(t),'[]'::json))
FROM (SELECT p.adjusted,p.data_vendor,s.stock_code,p.stock_id,count(*) AS rows,
 min(p.trading_date) AS first_date,max(p.trading_date) AS last_date,
 count(*) FILTER (WHERE p.close_price=0) AS zero_close
 FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
 WHERE p.trading_date BETWEEN '2015-01-02' AND '2023-12-31' AND p.price_state='TRADED'
 AND (p.open_price<=0 OR p.high_price<=0 OR p.low_price<=0 OR p.close_price<=0)
 GROUP BY p.adjusted,p.data_vendor,s.stock_code,p.stock_id ORDER BY p.adjusted,p.data_vendor,s.stock_code) t;
SELECT json_build_object('check','affected_keys','data',coalesce(json_agg(t),'[]'::json))
FROM (SELECT s.stock_code,p.stock_id,p.trading_date,p.adjusted,p.data_vendor,p.price_state,
 p.open_price,p.high_price,p.low_price,p.close_price,p.trade_volume
 FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
 WHERE p.trading_date BETWEEN '2015-01-02' AND '2023-12-31' AND p.price_state='TRADED'
 AND (p.open_price<=0 OR p.high_price<=0 OR p.low_price<=0 OR p.close_price<=0)
 ORDER BY p.adjusted,p.data_vendor,p.stock_id,p.trading_date) t;
SELECT json_build_object('check','audit_complete','data',true);
COMMIT;
