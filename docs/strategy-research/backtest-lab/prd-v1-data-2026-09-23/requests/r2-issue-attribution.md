# R2. 미귀속 이슈 1,523행에 종목·일 귀속 키를 붙여 달라

목적: 종목·일로 추적되지 않는 원천 이슈 행(미귀속 이슈)을 원천에서 귀속시켜, 소비자의 종목 제외 사유를 원천 이슈 행과 대조할 수 있게 해 달라고 요청한다. 대상은 ted-startup, 작성자는 vectorbt 리포다. 이 문서를 외부에 전송하지 않았다. 전체 데이터 인수는 현재 `BLOCKED` 다.

## 1. 배경

원천 테이블은 `kiwoom.backtest_admission_issue_v2` 다(`research/krx_lab/v3_snapshot.py:35`, 필터 `affected_from<='2023-12-31' AND affected_to>='2014-01-01'`). 이 리포는 이를 스냅샷한 `<리포 루트>/../vectorbt-data/krx-v3-20260921-prepared-r2/issues.parquet` 를 `mapped` 플래그(`instrument_id` 파싱 결과)로 재계산했다.

| 구분 | 건수 |
| --- | --- |
| 전체 | 2,304 |
| 종목 귀속됨(`mapped=True`, `instrument_id` 존재) | 781 (34%) |
| 미귀속(`mapped=False`, `instrument_id` 없음) | 1,523 (66%) |

`../README.md` 의 781/1,523 과 일치하며, 재계산 값과 차이는 없다. 2024-01-01 이후 `affected_from`/`affected_to` 를 갖는 행은 미귀속 1,523건 중 0건이라 제외 대상이 없다.

## 2. 미귀속 1,523행의 이슈 코드별 내역

| issue_code | 건수 | affected_scope 성격 |
| --- | --- | --- |
| UNEXPLAINED_VENDOR_FACTOR | 1,061 | 날짜·사건 단위(수정계수 원인 미상) |
| ADJUSTED_OHLC_ORDER_VIOLATION | 284 | 날짜·사건 단위(수정 OHLC 순서 위반) |
| CORPORATE_ACTION_PARTIAL | 160 | 날짜·사건 단위(기업행사 부분 반영) |
| RAW_NONPOSITIVE_PRICE_TRADED | 13 | 종목 식별자 없음(원가 OHLC≤0, B4 UNEXPLAINED 18건 중 날짜 겹침 6건) |
| ADJUSTED_NONPOSITIVE_PRICE_TRADED | 4 | 종목 식별자 없음 |
| POINT_IN_TIME_SECTOR_UNAVAILABLE | 1 | `KOSPI_KOSDAQ_COMMON_STOCK` 전역 라벨(종목 무관 정책 이슈) |
| 합계 | 1,523 | |

표가 말하는 것: 미귀속 행의 95%(1,505건)는 `affected_scope` 가 날짜·사건 단위 라벨이라 종목에 귀속되지 않는 세 코드(UNEXPLAINED_VENDOR_FACTOR·ADJUSTED_OHLC_ORDER_VIOLATION·CORPORATE_ACTION_PARTIAL)에 몰려 있다.

## 3. 왜 필요한가

소비자 쪽 제외 1,711종목은 모두 `cohort.json` 에 종목별 사유가 있다. 이 사유는 이 리포가 adjustment·corporate_action member 에서 다시 판정한 것이며, 원천 이슈 행에서 온 것이 아니다. Gate A 는 제외 범위가 원천 행까지 추적되기를 요구하는데(`backtest-data-requirements-2026-09-20.md` Gate A), 위 1,523행은 종목 키가 없어 소비자 사유와 행 단위로 맞댈 수 없다.

정정(2026-09-24): 이 절의 이전 판은 「1,184종목은 원인 코드가 없어 B5 가 막힌다」 고 썼다. 이는 B1 이 `issues.parquet` 만 보고 `cohort.json` 의 사유를 보지 않은 탓이며, 요청 내용(§4)은 바뀌지 않는다.

## 4. 요청 내용

| 묶음 | 확보할 자료 | 성공 조건 |
| --- | --- | --- |
| 귀속 키 부여 | 미귀속 1,523행 각각에 `(stock_id 또는 종목코드, trading_date)` 수준의 귀속 키를 원천에서 붙여 재납품 | 재납품본에서 귀속 불가 행이 0건이거나, 남은 행에 사유 코드가 붙어 있음 |
| 기존 귀속 보존 | 이미 귀속된 781행의 `instrument_id`·귀속 결과는 그대로 유지 | 재납품본의 781행이 기존과 동일 |
| 귀속 불가 사유 | 정말 종목에 귀속할 수 없는 행(예: POINT_IN_TIME_SECTOR_UNAVAILABLE 같은 전역 정책 이슈)은 사유 코드를 명시 | 사유 코드 필드가 비어 있지 않음 |

## 5. 납품 후 검증

1. 재납품 `issues.parquet` 에서 `mapped=False` 이면서 사유 코드도 없는 행이 0건인지 확인한다.
2. 기존 781행의 `instrument_id`·`issue_code` 조합이 바뀌지 않았는지 대조한다.
3. 새로 귀속된 행을 `cohort.json` 의 종목별 제외 사유와 교차해, 원천 이슈와 소비자 사유가 종목 단위로 일치하는지 확인한다.

첨부: [`r2-unattributed-issues.csv`](r2-unattributed-issues.csv) — 미귀속 1,523행 전부(`issue_code`·`affected_scope`·`affected_from`·`affected_to`·`decision`·`severity`·`signal_blocking`·`details` 원래 열과 행 식별용 `row_hash`, SHA-256 앞 16자).
