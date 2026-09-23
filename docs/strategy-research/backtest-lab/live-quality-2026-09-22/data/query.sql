\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='180s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object('observed_at',now(),'read_only',current_setting('transaction_read_only'),'isolation',current_setting('transaction_isolation'),'scope','2014-01-01..2023-12-31'));
SELECT json_build_object('check','price_profile','data',json_agg(x)) FROM (
 SELECT adjusted,source_code,count(*) rows,count(DISTINCT stock_id) instruments,min(trading_date) first_date,max(trading_date) last_date,max(source_record_id) max_source_record_id,
 count(*) FILTER (WHERE open_price IS NULL OR high_price IS NULL OR low_price IS NULL OR close_price IS NULL) null_ohlc,
 count(*) FILTER (WHERE least(open_price,high_price,low_price,close_price)<=0) nonpositive_ohlc,
 count(*) FILTER (WHERE trade_volume>0 AND least(open_price,high_price,low_price,close_price)<=0) traded_nonpositive_ohlc,
 count(*) FILTER (WHERE high_price<greatest(open_price,close_price,low_price) OR low_price>least(open_price,close_price,high_price)) invalid_ohlc_order,
 count(*) FILTER (WHERE trade_volume=0) zero_volume,
 count(*) FILTER (WHERE payload_sha256 IS NULL OR source_record_id IS NULL) missing_lineage,
 count(*) FILTER (WHERE historical_capture) historical_capture_rows
 FROM kiwoom.backtest_price_v2 WHERE trading_date BETWEEN '2014-01-01' AND '2023-12-31' GROUP BY adjusted,source_code ORDER BY adjusted,source_code
) x;
SELECT json_build_object('check','calendar','data',json_agg(x)) FROM (SELECT market,count(*) rows,count(*) FILTER (WHERE is_open) open_days,min(trading_date) first_date,max(trading_date) last_date FROM kiwoom.market_calendar WHERE market='KRX' AND trading_date BETWEEN '2014-01-01' AND '2023-12-31' GROUP BY market) x;
SELECT json_build_object('check','universe','data',json_agg(x)) FROM (SELECT market,security_type,count(*) intervals,count(DISTINCT stock_id) instruments FROM kiwoom.backtest_universe_v2 WHERE security_type='COMMON_STOCK' AND valid_from<='2023-12-31' AND valid_to>='2014-01-01' GROUP BY 1,2 ORDER BY 1,2) x;
SELECT json_build_object('check','actions','data',json_agg(x)) FROM (SELECT event_type,resolution_status,count(*) rows FROM kiwoom.backtest_corporate_action_v2 WHERE effective_date BETWEEN '2014-01-01' AND '2023-12-31' GROUP BY 1,2 ORDER BY 1,2) x;
SELECT json_build_object('check','adjustments','data',json_agg(x)) FROM (SELECT explanation_status,count(*) rows FROM kiwoom.backtest_adjustment_v2 WHERE trading_date BETWEEN '2014-01-01' AND '2023-12-31' GROUP BY 1 ORDER BY 1) x;
SELECT json_build_object('check','status','data',json_agg(x)) FROM (SELECT daily_state,count(*) rows FROM kiwoom.backtest_status_v2 WHERE trading_date BETWEEN '2014-01-01' AND '2023-12-31' GROUP BY 1 ORDER BY 1) x;
SELECT json_build_object('check','rules','data',json_agg(x)) FROM (SELECT * FROM kiwoom.backtest_execution_rule_v2 WHERE effective_from<='2023-12-31' AND effective_to>='2014-01-01' ORDER BY rule_kind,market,effective_from) x;
SELECT json_build_object('check','audit_complete','data',true);
ROLLBACK;
