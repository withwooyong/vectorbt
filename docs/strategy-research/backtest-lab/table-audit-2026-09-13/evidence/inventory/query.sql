\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='30s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object(
 'observed_at',now(),'database',current_database(),'read_only',current_setting('transaction_read_only')));
SELECT json_build_object('check','tables','data',coalesce(json_agg(t ORDER BY table_name),'[]'::json))
FROM (SELECT table_schema,table_name FROM information_schema.tables
 WHERE table_schema='public' AND table_type='BASE TABLE') t;
SELECT json_build_object('check','columns','data',coalesce(json_agg(t ORDER BY table_name,ordinal_position),'[]'::json))
FROM (SELECT table_name,column_name,data_type,is_nullable,ordinal_position FROM information_schema.columns
 WHERE table_schema='public' AND table_name IN ('stock','corporate_event','dart_disclosure','dart_corp_mapping')) t;
SELECT json_build_object('check','audit_complete','data',true);
COMMIT;
