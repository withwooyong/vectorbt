-- Current-schema checks. No external trading-calendar or historical-universe table is assumed.
-- Internal date gaps are diagnostic candidates, not proof of missing trading sessions.
\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
SET LOCAL lock_timeout = '3s';
SELECT now() AS observed_at, current_setting('transaction_read_only');
SELECT count(*) AS duplicate_keys FROM (
 SELECT stock_id,trading_date,adjusted FROM kiwoom.stock_price_krx
 GROUP BY 1,2,3 HAVING count(*)>1
) q;
WITH per_stock AS (
 SELECT stock_id,min(trading_date) AS first_date,max(trading_date) AS last_date,count(*) AS rows
 FROM kiwoom.stock_price_krx WHERE adjusted GROUP BY stock_id
)
SELECT s.market_name,count(*) AS with_prices,
count(*) FILTER (WHERE p.first_date<=DATE '2015-01-02') AS reaches_target_start,
count(*) FILTER (WHERE s.listed_date<DATE '2015-01-02') AS currently_old_listing,
count(*) FILTER (WHERE s.listed_date<DATE '2015-01-02' AND p.first_date>DATE '2015-01-02') AS old_listing_starts_late
FROM per_stock p JOIN kiwoom.stock s ON s.id=p.stock_id
GROUP BY 1 ORDER BY 1;
-- Coverage within observed spans against all observed KRX dates; this is only a proxy calendar.
WITH dates AS (
 SELECT DISTINCT trading_date FROM kiwoom.stock_price_krx WHERE adjusted
), bounds AS (
 SELECT stock_id,min(trading_date) AS first_date,max(trading_date) AS last_date,count(*) AS observed
 FROM kiwoom.stock_price_krx WHERE adjusted GROUP BY stock_id
), numbered AS (
 SELECT trading_date,row_number() OVER (ORDER BY trading_date) AS rn FROM dates
), gaps AS (
 SELECT b.stock_id,b.first_date,b.last_date,b.observed,e.rn-f.rn+1-b.observed AS absent_on_proxy_dates
 FROM bounds b JOIN numbered f ON f.trading_date=b.first_date JOIN numbered e ON e.trading_date=b.last_date
)
SELECT count(*) AS stocks,
count(*) FILTER (WHERE absent_on_proxy_dates>0) AS stocks_with_internal_gaps,
sum(absent_on_proxy_dates) AS internal_gap_candidates,
max(absent_on_proxy_dates) AS largest_gap_count
FROM gaps;
-- Exact regression sample for API/DB comparison.
SELECT stock_code, trading_date, open_price, high_price, low_price, close_price, trade_volume, trade_amount
FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
WHERE s.stock_code='005930' AND p.adjusted
AND trading_date BETWEEN DATE '2026-09-01' AND DATE '2026-09-10'
ORDER BY trading_date;
COMMIT;
