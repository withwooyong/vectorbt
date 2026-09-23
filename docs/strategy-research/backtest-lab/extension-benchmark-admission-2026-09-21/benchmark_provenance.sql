\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
SET LOCAL lock_timeout = '3s';

WITH benchmark AS MATERIALIZED (
    SELECT b.benchmark_code, b.trading_date, b.open_value, b.high_value,
           b.low_value, b.close_value, b.source_record_id,
           r.entity_kind, r.natural_key, r.record_data, r.published_at,
           r.available_at, r.available_precision, p.payload_id,
           p.payload_sha256, p.captured_at, q.source_code, q.endpoint,
           q.response_status, q.capture_kind, q.historical_capture,
           s.source_name, s.authority_kind, s.base_url
    FROM kiwoom.benchmark_daily b
    LEFT JOIN kiwoom.source_record r USING (source_record_id)
    LEFT JOIN kiwoom.source_payload p USING (payload_id)
    LEFT JOIN kiwoom.source_request q USING (request_id)
    LEFT JOIN kiwoom.source_system s USING (source_code)
    WHERE b.trading_date BETWEEN '2014-01-01' AND '2023-12-31'
), groups AS (
    SELECT benchmark_code, source_code, endpoint, source_name,
           authority_kind, base_url, response_status, capture_kind,
           historical_capture, entity_kind, available_precision,
           count(*) AS rows, count(DISTINCT trading_date) AS distinct_dates,
           count(DISTINCT source_record_id) AS distinct_source_records,
           min(trading_date) AS first_date, max(trading_date) AS last_date,
           min(close_value) AS min_close, max(close_value) AS max_close,
           min(available_at) AS first_available_at,
           max(available_at) AS last_available_at,
           min(captured_at) AS first_captured_at,
           max(captured_at) AS last_captured_at,
           count(*) FILTER (WHERE source_record_id IS NULL OR payload_id IS NULL
                           OR payload_sha256 IS NULL OR source_code IS NULL)
               AS missing_lineage,
           count(*) FILTER (WHERE published_at IS NULL) AS missing_published_at,
           count(*) FILTER (WHERE available_at IS NULL) AS missing_available_at,
           count(*) FILTER (WHERE LEAST(open_value, high_value, low_value, close_value) <= 0
                           OR open_value IS NULL OR high_value IS NULL
                           OR low_value IS NULL OR close_value IS NULL) AS invalid_prices,
           count(*) FILTER (WHERE high_value < GREATEST(open_value, close_value, low_value)
                           OR low_value > LEAST(open_value, close_value, high_value)) AS invalid_ohlc,
           count(*) FILTER (WHERE open_value IS DISTINCT FROM (record_data->>'OPNPRC_IDX')::numeric
                           OR high_value IS DISTINCT FROM (record_data->>'HGPRC_IDX')::numeric
                           OR low_value IS DISTINCT FROM (record_data->>'LWPRC_IDX')::numeric
                           OR close_value IS DISTINCT FROM (record_data->>'CLSPRC_IDX')::numeric)
               AS source_ohlc_mismatches,
           count(*) FILTER (WHERE natural_key->>'date' IS DISTINCT FROM
                               to_char(trading_date, 'YYYY-MM-DD')
                           OR record_data->>'BAS_DD' IS DISTINCT FROM
                               to_char(trading_date, 'YYYYMMDD')
                           OR natural_key->>'index_name' IS DISTINCT FROM
                               CASE benchmark_code WHEN 'KOSPI' THEN '코스피'
                                                   WHEN 'KOSDAQ' THEN '코스닥' END)
               AS source_identity_mismatches
    FROM benchmark
    GROUP BY benchmark_code, source_code, endpoint, source_name,
             authority_kind, base_url, response_status, capture_kind,
             historical_capture, entity_kind, available_precision
), expected AS (
    SELECT c.trading_date, v.benchmark_code
    FROM kiwoom.market_calendar c
    CROSS JOIN (VALUES ('KOSPI'), ('KOSDAQ')) v(benchmark_code)
    WHERE c.market = 'KRX' AND c.is_open
      AND c.trading_date BETWEEN '2014-01-01' AND '2023-12-31'
), missing AS (
    SELECT benchmark_code, trading_date FROM expected
    EXCEPT SELECT benchmark_code, trading_date FROM benchmark
), extra AS (
    SELECT benchmark_code, trading_date FROM benchmark
    EXCEPT SELECT benchmark_code, trading_date FROM expected
), samples AS (
    SELECT benchmark_code, trading_date, close_value, source_record_id,
           payload_sha256, source_code, endpoint,
           row_number() OVER (PARTITION BY benchmark_code ORDER BY trading_date) AS first_n,
           row_number() OVER (PARTITION BY benchmark_code ORDER BY trading_date DESC) AS last_n
    FROM benchmark
)
SELECT jsonb_build_object(
    'revision', (SELECT jsonb_build_object('revision_id', revision_id,
        'status', status, 'period_start', period_start, 'period_end', period_end,
        'content_sha256', content_sha256)
        FROM kiwoom.dataset_revision
        WHERE revision_id = '0eeed564-0b89-587c-b8f9-d8eea981bb9e'),
    'benchmark_member', (SELECT jsonb_build_object('row_count', row_count,
        'content_sha256', content_sha256, 'min_valid_date', min_valid_date,
        'max_valid_date', max_valid_date)
        FROM kiwoom.dataset_revision_member
        WHERE revision_id = '0eeed564-0b89-587c-b8f9-d8eea981bb9e'
          AND member_kind = 'BENCHMARK'),
    'groups', (SELECT jsonb_agg(to_jsonb(g) ORDER BY benchmark_code) FROM groups g),
    'calendar_open_sessions', (SELECT count(*) FROM kiwoom.market_calendar
        WHERE market = 'KRX' AND is_open
          AND trading_date BETWEEN '2014-01-01' AND '2023-12-31'),
    'missing_calendar_pairs', (SELECT count(*) FROM missing),
    'extra_noncalendar_pairs', (SELECT count(*) FROM extra),
    'benchmark_rows', (SELECT jsonb_agg(jsonb_build_object(
        'benchmark_code', benchmark_code, 'trading_date', trading_date,
        'source_record_id', source_record_id, 'open_value', open_value,
        'high_value', high_value, 'low_value', low_value,
        'close_value', close_value, 'payload_sha256', payload_sha256)
        ORDER BY benchmark_code, trading_date) FROM benchmark),
    'samples', (SELECT jsonb_agg(to_jsonb(s) - 'first_n' - 'last_n'
                                  ORDER BY benchmark_code, trading_date)
                FROM samples s WHERE first_n = 1 OR last_n = 1)
)::text;

ROLLBACK;
