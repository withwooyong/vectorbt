\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='60s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object('observed_at',now(),'database',current_database(),'read_only',current_setting('transaction_read_only')));
SELECT json_build_object('check','traded_nonpositive_by_stock','data',coalesce(json_agg(t),'[]'::json)) FROM (
 SELECT s.stock_code,count(*) AS rows,min(p.trading_date) AS first_date,max(p.trading_date) AS last_date,count(*) FILTER (WHERE p.close_price<=0) AS nonpositive_close,
 count(*) FILTER (WHERE p.volume>0) AS positive_volume_rows
 FROM public.stock_price p JOIN public.stock s ON s.id=p.stock_id
 WHERE p.trading_date BETWEEN '2015-01-02' AND '2023-12-31' AND p.price_state='TRADED'
 AND (p.open_price<=0 OR p.high_price<=0 OR p.low_price<=0 OR p.close_price<=0)
 GROUP BY s.stock_code ORDER BY count(*) DESC,s.stock_code) t;
SELECT json_build_object('check','audit_complete','data',true);
COMMIT;
