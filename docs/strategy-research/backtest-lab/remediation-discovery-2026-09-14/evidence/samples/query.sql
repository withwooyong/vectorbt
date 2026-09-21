\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='90s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object(
 'observed_at',now(),'database',current_database(),'read_only',current_setting('transaction_read_only'),
 'start','2015-01-02','end','2023-12-31'));

SELECT json_build_object('check','target_stock_current','data',coalesce(json_agg(t),'[]'::json)) FROM (
 SELECT id,stock_code,stock_name,listed_date,delisted_date,is_active,state FROM kiwoom.stock WHERE stock_code='102950'
) t;

SELECT json_build_object('check','kiwoom_zero_bounds','data',coalesce(json_agg(t),'[]'::json)) FROM (
 SELECT p.data_vendor,p.adjusted,count(*) AS rows,min(p.trading_date) AS first_date,max(p.trading_date) AS last_date,
 count(*) FILTER(WHERE close_price=0) AS zero_rows,
 min(p.trading_date) FILTER(WHERE close_price=0) AS first_zero,
 max(p.trading_date) FILTER(WHERE close_price=0) AS last_zero,
 min(p.trading_date) FILTER(WHERE close_price>0) AS first_positive,
 min(p.fetched_at) AS first_fetched,max(p.fetched_at) AS last_fetched
 FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id WHERE s.stock_code='102950'
 AND p.trading_date BETWEEN '2015-01-02' AND '2023-12-31' GROUP BY p.data_vendor,p.adjusted
) t;

WITH classified AS (
 SELECT p.*,CASE WHEN p.high_price<p.close_price AND p.trade_volume>0 THEN 'KRX_HIGH_LT_CLOSE_POS_VOLUME'
 WHEN p.high_price<p.close_price AND p.trade_volume=0
  AND p.open_price=0 AND p.high_price=0 AND p.low_price=0 THEN 'KRX_ZERO_OHL_ZERO_VOLUME'
 WHEN p.high_price<p.close_price AND p.trade_volume=0 THEN 'KRX_OTHER_HIGH_LT_CLOSE_ZERO_VOLUME' END AS anomaly
 FROM kiwoom.stock_price_krx p WHERE p.data_vendor='KRX' AND p.adjusted
 AND p.trading_date BETWEEN '2015-01-02' AND '2023-12-31'
)
SELECT json_build_object('check','krx_ingestion_cohorts','data',coalesce(json_agg(t),'[]'::json)) FROM (
 SELECT anomaly,fetched_at::date AS fetched_day,count(*) AS rows,count(DISTINCT stock_id) AS stocks,
 min(trading_date) AS first_date,max(trading_date) AS last_date,
 min(created_at) AS first_created,max(updated_at) AS last_updated
 FROM classified WHERE anomaly IS NOT NULL GROUP BY anomaly,fetched_at::date ORDER BY anomaly,fetched_day
) t;

WITH classified AS (
 SELECT p.*,CASE WHEN p.high_price<p.close_price AND p.trade_volume>0 THEN 'KRX_HIGH_LT_CLOSE_POS_VOLUME'
 WHEN p.high_price<p.close_price AND p.trade_volume=0
  AND p.open_price=0 AND p.high_price=0 AND p.low_price=0 THEN 'KRX_ZERO_OHL_ZERO_VOLUME'
 WHEN p.high_price<p.close_price AND p.trade_volume=0 THEN 'KRX_OTHER_HIGH_LT_CLOSE_ZERO_VOLUME' END AS anomaly
 FROM kiwoom.stock_price_krx p WHERE p.data_vendor='KRX' AND p.adjusted
 AND p.trading_date BETWEEN '2015-01-02' AND '2023-12-31'
), ranked AS (
 SELECT *,row_number() OVER(PARTITION BY anomaly ORDER BY stock_id,trading_date) AS sample_rank
 FROM classified WHERE anomaly IS NOT NULL
)
SELECT json_build_object('check','krx_fixed_samples','data',coalesce(json_agg(t),'[]'::json)) FROM (
 SELECT r.anomaly,r.sample_rank,s.stock_code,r.stock_id,r.trading_date,r.adjusted,r.data_vendor,
 r.open_price,r.high_price,r.low_price,r.close_price,r.trade_volume,r.trade_amount,
 r.fetched_at,r.created_at,r.updated_at FROM ranked r JOIN kiwoom.stock s ON s.id=r.stock_id
 WHERE r.sample_rank<=3 ORDER BY r.anomaly,r.sample_rank
) t;

WITH bars AS (
 SELECT p.*,lag(close_price) OVER(ORDER BY trading_date) AS previous_close
 FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
 WHERE s.stock_code='102950' AND p.adjusted AND p.trading_date BETWEEN '2015-01-02' AND '2023-12-31'
), anchors AS (
 SELECT trading_date FROM bars WHERE (close_price=0 AND previous_close>0) OR (close_price>0 AND previous_close=0)
 UNION SELECT min(trading_date) FROM bars
)
SELECT json_build_object('check','kiwoom_transition_samples','data',coalesce(json_agg(t),'[]'::json)) FROM (
 SELECT '102950' AS stock_code,stock_id,trading_date,adjusted,data_vendor,
 open_price,high_price,low_price,close_price,trade_volume,trade_amount,fetched_at,created_at,updated_at
 FROM bars b WHERE EXISTS(SELECT 1 FROM anchors a WHERE b.trading_date BETWEEN a.trading_date-3 AND a.trading_date+3)
 ORDER BY trading_date
) t;

SELECT json_build_object('check','raw_response_availability','data',json_build_object('ka10081_rows',count(*)))
FROM kiwoom.raw_response WHERE api_id='ka10081';
SELECT json_build_object('check','audit_complete','data',true);
COMMIT;
