\set ON_ERROR_STOP on
BEGIN READ ONLY;
SET LOCAL statement_timeout = '45s';
SET LOCAL lock_timeout = '3s';
SELECT now() AS observed_at, current_database(), current_setting('transaction_read_only');
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'kiwoom' ORDER BY table_name;
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'kiwoom'
AND table_name IN ('stock', 'stock_price_krx', 'sector_price_daily')
ORDER BY table_name, ordinal_position;
SELECT tablename, indexname, indexdef FROM pg_indexes
WHERE schemaname = 'kiwoom' AND tablename IN ('stock', 'stock_price_krx');
COMMIT;
