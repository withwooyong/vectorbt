# 합성 개발 공통 계약 v1

이 문서는 D1~D6가 독립적으로 구현할 입력·계좌 장부·선정 증거·자원 훅을 고정한다. **계약 검증 통과는 형식 적합성만 뜻하며 실제 데이터 인수나 실제 시장 모형 검증이 아니다.** 버전은 `krx-lab-contracts-v1`이며 기존 `snapshot-v1`과 `simulate()` 출력 계약은 그대로 유지한다. 실자료 실행과 2024년 이후 가격 접근은 계속 차단한다.

구현 기준은 [contracts.py](../../../research/krx_lab/contracts.py), 소형 정답은 [공통 fixture](../../../tests/research/fixtures/contracts_v1/)다. 소비자는 아래 필드와 사건 순서를 먼저 읽고, 보존식으로 산출물을 대조한다. 기존 [재납품 명세](remediation-discovery-2026-09-14/delivery-spec.md)의 원문·변환 계보, 역사 시점, 새 revision 요구를 축소하지 않는다.

## 1. C1: 원가격·기업행사·역사 입력

`validate_delivery(mapping) -> dict`는 입력을 바꾸지 않고 검증한 복사본을 반환한다. `ContractError.code`가 실패 코드다. `schema_version`, `source_kind`(`SYNTHETIC` 또는 `REAL`)와 아래 묶음이 필요하다. 단위는 metadata의 currency, 수량은 주, 비율은 소수다. 날짜는 `YYYY-MM-DD`, 시각은 시간대를 포함한 ISO 8601이며 유효 시작·종료일 모두 포함한다. 미지정 종료는 `null`이다.

각 행의 구체적인 키를 고정한다. 원문 바이트·파일 해시 대조, 코드 기간 중복·달력 누락·당시 인지 가능성 대조는 D2가 추가로 수행한다.

| 묶음 | 필수 필드 |
| --- | --- |
| metadata | dataset_id, revision, previous_revision(null 가능), extracted_at, start, end, currency, price_basis=`raw`, adjustment_definition, files, real_data_admitted=`false`, holdout_prices_included=`false` |
| sources | source_id, source_url_or_document_id, published_at, time_precision(`timestamp/date/unknown`), captured_at, raw_file_sha256, historical_capture(`synthetic/original/new_observation/unavailable`) |
| prices | instrument_id, code, date, open/high/low/close, volume, turnover, price_factor, quantity_factor, adjusted_open/high/low/close, source_id |
| instruments | instrument_id(영구 ID), code, effective_from/to, market, product_type, sector, source_id |
| events | event_id, instrument_id, event_type, effective_date, announced_at, record_date, pay_date, correction_of, cancelled, source_id |
| statuses | status_id, instrument_id, effective_from/to, status(`TRADING/HALTED/DELISTED`), reason, last_trade_date, official_delist_date, source_id |
| calendar | market, date, is_open, opens_at, closes_at, reason, source_id |
| market_profiles | profile_id, market, effective_from/to, model=`SYNTHETIC_FIXED`, tick_size, lot_size, buy_fee_rate, sell_fee_rate, sell_tax_rate, slippage_bps, settlement_delay_days, rounding=`NONE`, source_id |

sources의 `unknown` 정밀도는 published_at=`null`과 unavailable_reason이 필요하다. 날짜만 알려진 시점을 장중 시각으로 만들어서는 안 된다. `announced_at`이 필요한 합성 행사에 시각을 공급할 수 없는 실제 입력은 실행에 사용하지 않는다. 실제 데이터와 합성 원문을 혼합해 실자료로 승격할 수 없다. metadata.files와 C2.files 항목은 `file, rows, schema, sha256`이며 상대 경로만 허용한다. 파일의 실제 존재·바이트 검증은 소비자가 담당한다.

합성 프로필의 조정 정의는 `adjusted_price = raw_price × price_factor`, `adjusted_quantity = raw_quantity × quantity_factor`이며 반올림하지 않는다. 신호는 조정가격을 선택할 수 있지만 체결과 보유수량은 원가격 기준이다. 시장 프로필은 사건일의 종목 이력에서 market을 찾은 뒤 해당 market의 유효 구간으로 해석한다. 중복·누락은 D2/D1에서 거절한다. 실제 한국 시장의 비용·호가·정산일에 관한 가정으로 해석하지 않는다.

현재 D1 실행 지원 범위는 `settlement_delay_days=0`, `lot_size=1`, `slippage_bps=0`이다. 다른 값은 계약의 숫자 형식 검사를 통과할 수 있어도 엔진이 명시적으로 거절한다. 매수·매도 현금은 즉시 결제하되 같은 날 장중 매도 현금을 과거 시가 주문에 소급 재사용하지 않는다. 기업행사 미수금은 별도의 pay_date에만 사용 가능한 현금으로 바뀐다. 매수 가능 현금은 settled cash에서 payables를 차감한 값이며, 현재 매수 보유만 지원하는 합성 엔진의 payables는 0이다.

### 합성 사건의 조건부 필드와 순서

모든 지원 사건은 효력일 시가 전에 적용하며, 인지 시각도 시가 전에 존재해야 한다. 현재 엔진은 단일 시장과 종목별 하루 한 행사만 지원하며, 행사 효력일은 개장일이어야 한다. 같은 종목의 같은 날 복수 행사는 순서 추정을 피하기 위해 거절한다. 권리수량은 사건 직전 보유수량(`PRE_EVENT_HOLDINGS`)이다. 날짜에 해당하는 지급은 사건 인식 후, 신규 주문 전 처리한다. 휴장일 pay_date에도 지급과 일말 평가를 기록하지만 거래는 생성하지 않는다. 향후 정보로 과거 신호·주문을 바꾸지 않는다.

| 유형 | 조건부 필드와 처리 |
| --- | --- |
| SPLIT / REVERSE_SPLIT | quantity_ratio(신주/구주), fractional_policy. `REJECT`는 단주 발생 거절; `CASH_IN_LIEU`는 fractional_cash_price와 pay_date 필수. 단주 원가 배분·정산은 사건 장부에 기록 |
| CASH_DIVIDEND | cash_per_share, withholding_rate, entitlement_policy=`PRE_EVENT_HOLDINGS`, record_date, pay_date. 권리 인식 시 순배당 미수금 증가, 지급 시 현금으로 이동 |
| DELIST_CASH | cash_per_share(정산 단가), withholding_rate, entitlement_policy=`PRE_EVENT_HOLDINGS`, record_date, pay_date. 보유 제거·미수 인식과 지급을 분리 |

미지원 유형·프로필·단주 정책은 명시적으로 실패한다. 정정·취소된 행사(`correction_of != null` 또는 `cancelled != false`)는 정정 연결을 해소한 새 revision이 필요하다. D0의 형식 검증은 지원 유형에 대한 실제 엔진 구현 완료를 보장하지 않는다.

인수 검사는 metadata 기간의 모든 달력 날짜(휴장일 포함)를 요구한다. 개장·폐장 시각의 현지 날짜는 해당 달력 날짜와 같아야 하며, 출처 시점은 published_at ≤ captured_at ≤ extracted_at 순서다. 현재 파일 내용 대조는 `synthetic-source-v1` JSON만 지원하며 미지원 스키마와 실제 자료는 인수 차단 상태로 남긴다.

## 2. C2: 현금과 미결제 자산을 분리한 장부

`validate_ledger(mapping) -> dict`는 형식과 일별 평가액 항등식을 검사한다. 최상위 키는 schema_version, source_kind, run_id, dataset_id, revision, currency, initial_cash, orders, fills, events, cashflows, positions, equity, issues, files다. 빈 거래도 각 배열을 제공한다.

| 행 | 필수 필드 |
| --- | --- |
| orders | order_id, date, instrument_id, side, quantity, status |
| fills | ledger_seq, fill_id, order_id, date, instrument_id, side, quantity, price, fee, tax |
| events | ledger_seq, event_id, date, instrument_id, event_type, quantity_delta, cost_basis_delta, cash_delta, receivable_delta, payable_delta, fee, tax |
| cashflows | ledger_seq, cashflow_id, date, instrument_id, event_id(null 가능), fill_id(null 가능), kind, cash_delta, receivable_delta, payable_delta, fee, tax |
| positions | date, instrument_id, quantity, mark_price, cost_basis(보유분 총원가), stale |
| equity | date, cash, receivables, payables, exposure, equity |

`cashflows`는 현금·미수·미지급 이동의 유일한 합산 원장이다. events/fills의 금액은 그 이동을 추적하는 설명이므로 다시 합산하지 않는다. fee/tax는 이미 순 cash_delta 또는 receivable_delta에 반영한 비용의 분류이며 별도 재공제하지 않는다. price는 슬리피지를 포함한 실제 체결가격이다. 사건 ID는 C1 events를, 주문·체결 ID는 C2 내부를, dataset_id/revision과 files는 원자료 및 실행 manifest를 추적한다. 지급 행은 원래 event_id를 재사용할 수 있다.

ledger_seq는 실행 전체의 0 이상 정수 순서다. 하나의 체결/사건과 그 현금 흐름은 같은 번호를 공유하며, 독립 재생은 번호순으로 수량 변경과 현금 이동을 각각 한 번 적용한다. 서로 다른 경제적 전이에 번호를 재사용하지 않는다. orders/fills/positions의 quantity와 events의 quantity_delta는 정수 주다. 단주 현금정산 과정의 이론상 분수는 별도 보조 필드로 남기고 정수 보유수량에 넣지 않는다. side는 `buy/sell`, 주문 status는 `PLANNED/FILLED/REJECTED/CANCELLED/PARTIALLY_FILLED`다. 같은 날 여러 행사의 순서를 안전하게 처리하지 못하는 엔진은 해당 입력을 거절한다.

- 현금 = initial_cash + 누적 cash_delta.
- 미수금/미지급금 = 각각 누적 receivable_delta/payable_delta.
- 평가액 = cash + receivables - payables + exposure.
- exposure = 당일 보유수량 × 평가가격의 종목별 합계. stale은 최근 관측가격 이월임을 표시한다.
- 보유수량 = 체결 수량의 부호 합계 + 기업행사 quantity_delta. 원가 이동은 현금 이동과 구분한다.

공통 정답은 초기 현금 1,000에서 10주를 50에 매수하고 수수료 1을 지불한다. 2:1 분할 후 20주, 주당 1의 배당에 합성 원천징수율 10%를 적용해 순미수금 18을 인식한다. 지급일 현금은 517, 미수금은 0, 24로 평가한 노출은 480, 평가액은 997이다. 이 수치는 엔진을 실행해 생성하지 않은 손계산 정답이다.

## 3. C3: 후보 고정 증거와 잠금 기록

`validate_lifecycle_evidence(mapping) -> dict`는 schema_version, source_kind, experiment_id, state, candidate_id, growth_policy, selection_policy, code_hash, data_hash, cost_profile_hash, validation_hash, prerequisites, holdout_access, attempts를 받는다. 해시 검증·저장 후 변조 탐지·선행 증거의 실제 충족 검사는 D3 책임이다.

상태 전이는 `DRAFT → FROZEN / NO_SELECTION / FAILED`, `FROZEN → FINALIZED / FAILED`다. `NO_SELECTION`과 `FINALIZED`는 종료 상태다. `FAILED → FAILED`는 같은 고정 후보의 재시도 기록만 허용하며, 새 후보로 대체하는 전이는 없다. 모듈 소비자는 성공적인 재실행이 필요하면 별도 실험과 계보를 만들어야 한다. 합성 FROZEN/FINALIZED는 합성 상태 모형 검증만 뜻한다.

prerequisites의 data_verified, candidate_policy_frozen, realistic_costs_verified, holdout_implementation_verified는 각각 bool이다. holdout_access의 각 행은 at, action, allowed, reason이며 attempts는 attempt_id, at, action, status, reason이다. 합성 증거의 allowed=`true`는 항상 거절한다. 실자료도 모든 선행 조건이 충족되지 않으면 허용 기록을 거절한다. 실제 잠금 해제 기능이나 후속 33슬롯의 실행 구현을 추가한 계약이 아니다.

최종 합성 결과는 고정 증거의 코드·데이터·비용 해시와 `execution_manifest`를 연결한다. 장부의 dataset_id/revision, strategy_id/growth_policy, run_id 및 ledger_hash도 고정 후보·실행과 일치해야 한다. 독립 장부 재생을 통과하고 미해결 issues가 없어야 finalize할 수 있다. 이후 읽기와 동일 시도 재실행에서도 최종 결과 및 참조 파일 바이트 해시를 다시 검사한다. 로컬 해시 이력은 실수·부분 변조 탐지이며 전체 이력의 적대적 재작성에 대한 외부 공증은 아니다.

## 4. C4: 실행 체크포인트와 협력 중단

`ResourceSample(elapsed_seconds, rss_bytes, peak_rss_bytes, disk_free_bytes)`는 초·바이트 단위를 쓴다. peak_rss_bytes는 관측 최대 RSS이며 OS가 보장한 상한이 아니다. `StopToken.request_stop(reason)`은 첫 사유를 보존하고 `raise_if_requested()`는 `CooperativeStop(reason)`을 발생시킨다.

`ExecutionHooks(checkpoint=None, stop_token=StopToken())`를 `hooks(stage, context=None)`로 호출한다. 콜백은 `(stage: str, context: Mapping) -> None`이며 오류를 숨기지 않는다. 체크포인트는 run_start, simulation_day, resource_exceeded, stop_requested, before_artifacts, after_artifacts, before_rename, after_rename, before_registry_commit, after_registry_commit, resume다. context의 run_id, attempt, directory, date는 해당 단계에서 소비자가 제공하는 부가 정보다.

훅은 동기적으로 동작하며 D4는 같은 프로세스의 RSS/디스크 샘플링과 협력 중단을 제공한다. OS 강제 할당 제한·자식 프로세스 강제 종료·다중 호스트 제어는 제공하지 않는다. 기존 배치 runner의 저장/rename/registry 전후 6개 경계에서 강제 종료와 재개를 검증했다. 신규 run-delivery는 새 디렉터리에서 한 번 실행하는 검사 경로이며 배치 resume이나 after_registry_commit 훅을 제공하지 않는다. 알 수 없는 stage는 UNKNOWN_HOOK_STAGE, 자원 초과는 D4가 정한 안정적 reason, 사용자 중단 기본 사유는 STOP_REQUESTED다. 부분 산출물은 성공 manifest와 검증이 끝나기 전에 완료로 승격하지 않는다.

## 5. 검증 범위

실행 명령은 `.venv/Scripts/python.exe -X utf8 -m pytest tests/research/test_contracts.py -q`다. fixture 변조·버전·필수 필드·미지원 유형·자료 승격·잠금 차단·장부 항등식·훅 예외 전파를 확인한다. D0의 자동 검사는 데이터 인수나 실제 수익성을 증명하지 않으며, 독립 검토와 D1~D7 통합 대조는 별도로 기록한다.

2026-09-14 D0 최초 담당 검증은 33개 통과였으며, 시각·날짜 보강을 포함한 최종 계약 검사는 35개 통과다. 독립 검토와 전체 통합 검증 상태는 [개발 WBS](parallel-development-wbs-2026-09-14.md)에서 관리한다. DB·네트워크·실제 가격을 사용하지 않았다.
