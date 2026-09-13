\set ON_ERROR_STOP on
-- psql -q 사용: 트랜잭션 상태 메시지를 CSV에 섞지 않는다.
-- 필수 psql 변수: stock_code, start_date, end_date. 원본의 0/NULL 행도 보존한다.
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
SET LOCAL lock_timeout = '3s';
COPY (
    SELECT p.trading_date::date AS date,
           p.open_price AS open, p.high_price AS high,
           p.low_price AS low, p.close_price AS close,
           p.trade_volume AS volume
    FROM kiwoom.stock_price_krx p
    JOIN kiwoom.stock s ON s.id = p.stock_id
    WHERE s.stock_code = :'stock_code'
      AND p.adjusted
      AND p.trading_date >= :'start_date'::date
      AND p.trading_date <= :'end_date'::date
    ORDER BY p.trading_date
) TO STDOUT WITH (FORMAT CSV, HEADER TRUE, ENCODING 'UTF8');
COMMIT;
