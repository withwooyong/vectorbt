\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='60s';
SET LOCAL lock_timeout='3s';
SELECT json_build_object('check','context','data',json_build_object(
 'observed_at',now(),'database',current_database(),'read_only',current_setting('transaction_read_only')));

-- Only aggregate availability metadata outside the development period; no prices or event details.
SELECT json_build_object('check','event_availability','data',row_to_json(t)) FROM (
 SELECT count(*) AS total_rows,min(decision_date) AS first_decision_date,max(decision_date) AS last_decision_date,
 count(*) FILTER(WHERE decision_date BETWEEN '2015-01-02' AND '2023-12-31') AS development_decision_rows,
 count(*) FILTER(WHERE ex_date BETWEEN '2015-01-02' AND '2023-12-31') AS development_effective_rows
 FROM public.corporate_event
) t;

SELECT json_build_object('check','development_events','data',coalesce(json_agg(t ORDER BY event_type),'[]'::json)) FROM (
 SELECT event_type,count(*) AS rows,count(DISTINCT stock_code) AS symbols,
 min(decision_date) AS first_decision,max(decision_date) AS last_decision,
 count(*) FILTER(WHERE stock_code IS NULL OR btrim(stock_code)='') AS missing_stock_code,
 count(*) FILTER(WHERE ex_date IS NULL) AS missing_ex_date,
 count(*) FILTER(WHERE ratio IS NULL) AS missing_ratio,
 count(*) FILTER(WHERE per_share_amount IS NULL) AS missing_per_share_amount,
 count(*) FILTER(WHERE ex_date_source='NONE') AS no_ex_date_source,
 count(*) FILTER(WHERE ex_date_source='CONFLICT') AS conflicting_ex_date_source,
 count(*) FILTER(WHERE parse_status<>'PARSED') AS not_fully_parsed,
 count(*) FILTER(WHERE raw_payload IS NULL) AS missing_payload,
 count(*) FILTER(WHERE ratio<=0) AS nonpositive_ratio,
 count(*) FILTER(WHERE per_share_amount<0) AS negative_per_share_amount
 FROM public.corporate_event WHERE decision_date BETWEEN '2015-01-02' AND '2023-12-31'
 GROUP BY event_type
) t;

SELECT json_build_object('check','event_links','data',row_to_json(t)) FROM (
 SELECT count(*) AS rows,
 count(*) FILTER(WHERE d.rcept_no IS NULL) AS missing_disclosure,
 count(*) FILTER(WHERE s.id IS NULL) AS missing_current_stock,
 count(*) FILTER(WHERE m.stock_code IS NULL) AS missing_current_mapping,
 count(*) FILTER(WHERE m.corp_code<>e.corp_code) AS current_mapping_corp_mismatch,
 count(*) FILTER(WHERE d.stock_code<>e.stock_code) AS disclosure_stock_mismatch,
 count(*) FILTER(WHERE d.rcept_dt>e.ex_date) AS disclosure_after_ex_date
 FROM public.corporate_event e LEFT JOIN public.dart_disclosure d ON d.rcept_no=e.rcept_no
 LEFT JOIN public.stock s ON s.stock_code=e.stock_code
 LEFT JOIN public.dart_corp_mapping m ON m.stock_code=e.stock_code
 WHERE e.decision_date BETWEEN '2015-01-02' AND '2023-12-31'
) t;

SELECT json_build_object('check','event_duplicate_keys','data',row_to_json(t)) FROM (
 SELECT count(*) AS groups,coalesce(sum(n-1),0) AS extra_rows FROM (
  SELECT rcept_no,event_type,count(*) AS n FROM public.corporate_event
  WHERE decision_date BETWEEN '2015-01-02' AND '2023-12-31'
  GROUP BY rcept_no,event_type HAVING count(*)>1
 ) q
) t;

SELECT json_build_object('check','disclosure_availability','data',row_to_json(t)) FROM (
 SELECT count(*) AS total_rows,min(rcept_dt) AS first_receipt_date,max(rcept_dt) AS last_receipt_date,
 count(*) FILTER(WHERE rcept_dt BETWEEN '2015-01-02' AND '2023-12-31') AS development_rows
 FROM public.dart_disclosure
) t;

SELECT json_build_object('check','development_disclosures','data',row_to_json(t)) FROM (
 SELECT count(*) AS rows,count(DISTINCT stock_code) AS symbols,
 count(*) FILTER(WHERE stock_code IS NULL OR btrim(stock_code)='') AS missing_stock_code,
 count(*) FILTER(WHERE raw_payload IS NULL) AS missing_payload
 FROM public.dart_disclosure WHERE rcept_dt BETWEEN '2015-01-02' AND '2023-12-31'
) t;

-- These master tables contain current metadata; they do not establish historical eligibility.
SELECT json_build_object('check','current_stock','data',row_to_json(t)) FROM (
 SELECT count(*) AS rows,count(DISTINCT stock_code) AS distinct_codes,
 count(*) FILTER(WHERE stock_code IS NULL OR btrim(stock_code)='') AS missing_code,
 count(*) FILTER(WHERE stock_code !~ '^[0-9]{6}$') AS non_six_digit_code,
 count(*) FILTER(WHERE sector IS NULL OR btrim(sector)='') AS missing_sector,
 count(*) FILTER(WHERE is_active) AS active,
 count(*) FILTER(WHERE NOT is_active) AS inactive,
 count(*) FILTER(WHERE NOT is_active AND delisted_date IS NULL) AS inactive_missing_delisted_date,
 count(*) FILTER(WHERE is_active AND delisted_date IS NOT NULL) AS active_with_delisted_date
 FROM public.stock
) t;

SELECT json_build_object('check','current_mapping','data',row_to_json(t)) FROM (
 SELECT count(*) AS rows,count(DISTINCT stock_code) AS distinct_stock_codes,count(DISTINCT corp_code) AS distinct_corps,
 count(*) FILTER(WHERE stock_code IS NULL OR btrim(stock_code)='') AS missing_stock_code,
 count(*) FILTER(WHERE corp_code IS NULL OR btrim(corp_code)='') AS missing_corp_code
 FROM public.dart_corp_mapping
) t;

SELECT json_build_object('check','current_stock_mapping','data',row_to_json(t)) FROM (
 SELECT count(*) AS stock_rows,count(*) FILTER(WHERE m.stock_code IS NULL) AS stocks_without_mapping
 FROM public.stock s LEFT JOIN public.dart_corp_mapping m ON m.stock_code=s.stock_code
) t;

SELECT json_build_object('check','constraints','data',coalesce(json_agg(t ORDER BY table_name,constraint_name),'[]'::json))
FROM (SELECT c.relname AS table_name,con.conname AS constraint_name,con.contype AS type,
 pg_get_constraintdef(con.oid) AS definition,con.convalidated AS validated
 FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='public' AND c.relname IN ('stock','corporate_event','dart_disclosure','dart_corp_mapping')) t;
SELECT json_build_object('check','audit_complete','data',true);
COMMIT;
