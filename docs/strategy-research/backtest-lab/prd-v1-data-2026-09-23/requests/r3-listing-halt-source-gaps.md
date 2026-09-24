# R3. 상장·폐지·거래정지 원천 공백을 통지한다 (수정 요청 아님)

목적: B1b 대조에서 드러난 원천 공백을 ted-startup 에 알린다. 이 리포는 정답을 고르지 않는다. 대상은 ted-startup, 작성자는 vectorbt 리포다. 이 문서를 외부에 전송하지 않았다. 전체 데이터 인수는 현재 `BLOCKED` 다.

## 1. 배경

`../listing_halt_reconciliation.py` 가 `kiwoom.stock`·`instrument_history`·`market_status_event`·`trading_halt`(대상 2,787종목)를 읽기 전용 트랜잭션으로 대조했다(`../README.md` B1b 절, `../listing-halt-reconciliation.json`).

## 2. 발견한 공백

| 묶음 | 확보할 자료 | 성공 조건(원천 쪽 통지 사항) |
| --- | --- | --- |
| KOSPI 정지 원천 부재 | KOSPI 정지 원천이 사실상 없다(MSE HALTED KOSPI 15건뿐, KOSDAQ 3,834건). KOSPI 무거래 21,409행은 정지 여부를 판별할 원천이 없다 | KOSPI 정지·재개 이력을 다른 원천에서 보강할 수 있는지 확인 요청 |
| KOSDAQ 정지 해제 이벤트 부족 | KOSDAQ 정지 공시 3,834건 중 해제(TRADING) 이벤트가 훨씬 적어(전체 TRADING 1,205건) 구간 끝이 불확실하다(열린 구간 1,030개) | 해제 이벤트 누락분을 보강할 수 있는지 확인 요청 |
| 상장일 불일치 | `stock.listed_date` 와 `instrument_history` 최소 상장일이 다른 12종목(전부 `stock.listed_date` 가 더 늦음) | 어느 쪽이 PRD 「상장일」 의미에 맞는지 원천 쪽 근거 요청(이 리포는 선택하지 않음) |
| 폐지 근거 없는 절단 후보 | 데이터 종료일보다 90일 이상 일찍 끊겼는데 상장폐지 근거(3원천 합집합)가 없는 30종목 | 수집 절단인지 실제 폐지인지 원천 쪽 확인 요청 |

표가 말하는 것: 정지·해제 원천은 KOSDAQ 편중이라 KOSPI 무거래의 원인을 이 리포가 판별할 수 없고, 상장일·폐지 근거 불일치는 이 리포가 임의로 고르지 않고 원천에 되묻는다.

## 3. 목록

- 상장일 불일치 12종목: 첨부 `listed_date_mismatch_stock_and_instrument_history`.
- 폐지 근거 없는 30종목: 첨부 `delisting_no_source_evidence_gt90d_gap`.

## 4. 납품 후 검증

1. KOSPI 정지 이력이 보강되면 B4 의 KOSPI 무거래 21,409행을 재분류해 정지 설명 비율이 늘어나는지 확인한다.
2. 상장일 원천이 정해지면 12종목의 `effective_listed_date` 가 일관되게 계산되는지 확인한다.
3. 30종목에 폐지 근거 또는 "수집 절단 확정" 판정이 붙으면 B1 의 상장폐지 근사(284종목)가 갱신되는지 확인한다.

첨부: [`r3-listing-halt-gaps.json`](r3-listing-halt-gaps.json) — `../listing_halt_reconciliation.py` 를 `--mode analyze` 로 재계산해(DB 재접속 없음, 기존 읽기 전용 추출 `<리포 루트>/../vectorbt-data/krx-prd-v1-b1b-20260924` 재사용) 상장일 불일치 12종목 전체와 폐지 근거 없는 30종목 전체를 실었다. 재생성 방법: `../listing_halt_reconciliation.py` 의 `load_extracted`/`load_price_table` 을 이용해 `analyze_a_listing`/`analyze_b_delisting` 과 동일한 조건으로 재계산.
