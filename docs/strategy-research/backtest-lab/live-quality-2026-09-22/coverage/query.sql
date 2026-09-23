\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='180s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object('observed_at',now(),'read_only',current_setting('transaction_read_only'),'isolation',current_setting('transaction_isolation'),'scope','2014-01-01..2023-12-31 historical common-stock calendar coverage'));
SELECT json_build_object('check','coverage_by_year','data',json_agg(x)) FROM (
 WITH expected AS (
 SELECT DISTINCT u.stock_id,c.trading_date,a.adjusted
 FROM kiwoom.backtest_universe_v2 u JOIN kiwoom.market_calendar c ON c.market='KRX' AND c.is_open
 AND c.trading_date BETWEEN greatest(u.valid_from,DATE '2014-01-01') AND least(coalesce(u.valid_to,DATE '9999-12-31'),DATE '2023-12-31')
 CROSS JOIN (VALUES(false),(true)) a(adjusted)
 WHERE u.security_type='COMMON_STOCK' AND u.market IN ('KOSPI','KOSDAQ')
 ), actual AS (
 SELECT stock_id,trading_date,adjusted,count(*) n FROM kiwoom.backtest_price_v2
 WHERE trading_date BETWEEN '2014-01-01' AND '2023-12-31' GROUP BY 1,2,3)
 SELECT extract(year FROM e.trading_date) year,e.adjusted,count(*) expected_keys,
 count(*) FILTER(WHERE p.stock_id IS NULL) missing_keys,count(*) FILTER(WHERE p.n>1) duplicate_keys
 FROM expected e LEFT JOIN actual p USING(stock_id,trading_date,adjusted) GROUP BY 1,2 ORDER BY 1,2
) x;
SELECT json_build_object('check','audit_complete','data',true);
ROLLBACK;
