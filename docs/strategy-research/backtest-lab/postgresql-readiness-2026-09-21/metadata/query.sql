\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='60s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object('observed_at',now(),'read_only',current_setting('transaction_read_only'),'isolation',current_setting('transaction_isolation'),'scope','2014-01-01..2023-12-31'));
SELECT json_build_object('check','revision','data',coalesce(json_agg(x),'[]'::json)) FROM (SELECT * FROM kiwoom.dataset_revision WHERE revision_label='2014-2023-v3') x;
SELECT json_build_object('check','members','data',json_agg(x)) FROM (SELECT * FROM kiwoom.dataset_revision_member WHERE revision_id='0eeed564-0b89-587c-b8f9-d8eea981bb9e' ORDER BY member_kind) x;
SELECT json_build_object('check','issues','data',json_agg(x)) FROM (SELECT issue_code,severity,decision,count(*) rows FROM kiwoom.backtest_admission_issue_v2 WHERE affected_from<='2023-12-31' AND affected_to>='2014-01-01' GROUP BY 1,2,3 ORDER BY 1,2,3) x;
SELECT json_build_object('check','columns','data',json_agg(x)) FROM (SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='kiwoom' AND table_name IN ('backtest_price_v2','backtest_status_v2','backtest_corporate_action_v2','backtest_adjustment_v2','backtest_execution_rule_v2') ORDER BY table_name,ordinal_position) x;
SELECT json_build_object('check','audit_complete','data',true);
ROLLBACK;
