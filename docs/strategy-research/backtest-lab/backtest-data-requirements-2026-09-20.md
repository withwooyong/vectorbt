# KRX 백테스팅 데이터 전체 요구사항

## 결론과 적용 범위

**목적:** 2015-06-15~2023-12-31 KOSPI·KOSDAQ 보통주의 48개 일봉 전략을 1억원 공동계좌로 검증할 때 필요한 데이터를 하나의 계약으로 고정한다. 신호 계산에는 평가일 이전 250개 공식 거래일이 필요하므로 수집 범위는 최소 2014-01-01부터 시작한다. 2024년 이후 자료는 별도 잠금 구간으로 관리한다. 이 평가 시작일은 이전 기술 명세의 2015-01-02 개발 시작일을 대체하며, 2015-06-14까지는 신호 준비에만 사용한다. 기간 설정과 dataset 계약 버전을 함께 갱신해야 한다.

**필수 원칙:** 원 응답과 원천 필드 행은 **반드시 PostgreSQL 테이블에 append-only로 적재**한다. JSON/파일 경로만 보관하거나 현재 값으로 덮어쓰면 통과하지 못한다. 정규화·조정·정정 데이터는 원본 행까지 역추적할 수 있어야 하며, vectorbt는 승인된 PostgreSQL revision을 SQL로 조인해 만든 불변 Parquet snapshot을 반복 사용한다. Parquet은 실행용 사본이며 원본이나 인수 근거를 대신하지 않는다.

**실행 판정:** 아래 필수 항목이 하나라도 없거나 설명되지 않은 종목·기간이 있으면 해당 범위는 `BLOCKED`다. 데이터 형식·완전성 인수와 실제 체결·원장 실행 허가는 별도 게이트로 판정한다.

## 1. PostgreSQL 저장 계약

아래는 논리 테이블이다. 실제 스키마명은 달라도 되지만 같은 정보와 관계를 보존해야 한다. 모든 PK는 변경되지 않는 surrogate key를 사용하고, 거래일·종목코드를 PK 대신 사용하지 않는다.

| 계층·권장 테이블 | 반드시 저장할 내용 | 핵심 제약 |
| --- | --- | --- |
| 원천 `source_system`, `ingestion_run`, `source_request` | 공급자·endpoint·API/문서 버전, 요청 파라미터, 페이지/연속조회 키, 수집 코드 commit·이미지·의존성·config, 실행 시작/종료·상태, 요청/응답 시각·HTTP 상태 | 인증키·토큰은 저장하지 않고 비밀 아닌 요청 조건은 재현 가능해야 함 |
| 원문 `source_payload`, `source_record` | 응답 원문 `bytea/text/jsonb`, MIME·encoding·압축, 원문 SHA-256, 응답 내 행 순번과 원천 필드, `published_at`, 검증된 `available_at/known_at`과 각각의 정밀도, `captured_at` | 둘 다 append-only. JSONB 한 덩어리만 저장하고 원천 행을 표로 풀지 않는 방식은 불가 |
| 종목 `instrument`, `instrument_identifier_history` | 영구 `instrument_id`, 종목코드·ISIN·시장·상품유형·보통주 여부, 상장·시장 이전·코드 승계, `effective_from/to` | 코드 재사용과 동일 기업의 코드 변경을 분리; 현재 마스터를 과거에 소급 금지 |
| 시점 분류 `universe_membership`, `sector_history` | 날짜별 투자 가능 여부와 제외 사유, 당시 업종·분류 체계·시장 | 생존 종목만 선택 금지; 업종 누락을 `UNKNOWN` 한 종목군으로 조용히 처리 금지 |
| 가격 `daily_price_observation` | 출처별 정규장 raw/adjusted OHLC, 거래량·대금, 기준가, 원천 가격상태, 단위·통화·세션, 조정 요청 모드 | `(instrument, date, session, basis, source, observation_revision)` 유일; 0/NULL을 전일값으로 채우거나 공급자끼리 자동 혼합 금지 |
| 조정 `adjustment_factor` | 가격 필드별·수량 계수, 적용일·기준일·조정 기준시점, 공급자 산식·반올림·허용오차, 연결 기업행사와 원천 | raw·adjusted 관측값을 독립 보존하고 문서화된 공급자 규칙으로 재현; 단일 종가계수를 O/H/L에 무조건 적용 금지 |
| 행사 `corporate_action`, `corporate_action_term` | 분할·병합·감자·증자·주식/현금배당·합병·회사분할·상폐, 발표/접수·기준·효력·지급일, 수량비율·주당현금·원천징수, 단주 정책·가격, successor `instrument_id`·전환비율, 동일일 순서, 정정·취소 | `event_id`, `correction_of`, 원문 연결 필수; 제목만으로 유형·수치 확정 금지 |
| 상태 `trading_status_interval`, `delisting_settlement` | 거래·정지·재개 시각, 부분일 상태, 사유, 마지막 거래일·공식 상폐일, 정리매매, 합병/상폐 현금정산·지급일 | 무거래·정지·결측을 구분; 보유 종목을 마지막 가격이나 0원으로 임의 청산 금지 |
| 달력 `exchange_session` | 시장·세션별 개장 여부, 개장/폐장 시각, 임시휴장·단축장·연초·수능일, 발표시각·근거 | 관측 가격 날짜의 합집합으로 달력을 만들지 않음; `Asia/Seoul` 시각 포함 |
| 시장규칙 `tick_rule_history`, `price_limit_history`, `settlement_rule_history` | 가격대별 호가단위, lot, 기준가 산식, 상·하한가, 규칙 시행기간, 결제 T+N·휴일 이연·가용 현금 규칙, VI/경매 등 일봉으로 판단 불가한 제한 | 단일 `tick_size=1`·즉시결제 기본값 금지; 주문가 반올림, 일봉 보수 체결, settled/unsettled cash를 날짜별 재현 |
| 비용 `account_profile`, `transaction_cost_history` | 투자자/계좌 세금 가정, broker·channel·account type·order method·tier·시장·상품·날짜·매수/매도별 수수료, 증권거래세·농특세·배당 원천징수, 최소/반올림 규칙, 슬리피지 모델과 근거 | 불변 `cost_profile_id`로 실행과 연결; 10/30/50bp 민감도와 실제 비용을 구분하고 값·산식·유효기간을 함께 저장 |
| 기준상품 `benchmark_price` | 비교 지수와 실제 매매 가능한 기준상품의 raw/adjusted 가격, 분배금·비용·거래 가능일 | 현금 기준선과 buy-and-hold 기준선을 동일 기간·비용 기준으로 비교 |
| 품질·revision `data_issue`, `dataset_revision`, `revision_member`, `revision_change` | 문제 키·심각도·근거·처리상태, dataset/revision·이전 revision, 포함 범위, SQL/코드·schema hash, 행 수, 변경 키와 사유 | revision 불변; 수정은 새 행·새 revision으로만 반영하고 기존 실험 입력 보존 |

모든 원천·정규화 이력에는 최소 `source_id/source_record_id`, `published_at`, 검증된 `available_at/known_at`과 각 정밀도, `effective_from/to`, `captured_at`, `system_valid_from/to`, `historical_capture(original/new_observation/unavailable)`, `created_at`을 둔다. `effective_*`는 시장에서 효력이 생긴 때, `available_at/known_at`은 당시 의사결정에 사용할 수 있었음이 증명된 때다. 현재 다시 받은 자료를 과거 원문으로 표시하지 않으며, 날짜만 알려진 발표시각에 임의 시간을 만들지 않는다. 시가 전 인지 여부가 불명확하면 다음 공식 거래일 이후부터 적용하거나 `BLOCKED`로 둔다.

canonical 유효구간은 `[from, to)` 반개구간으로 통일하고 끝이 없으면 `to=NULL`로 둔다. 기존 원천이나 C1 형식이 종료일 포함 방식이면 변환 규칙을 명시한다. surrogate PK 외에도 표의 논리키에 `UNIQUE`/배타 제약을 두어 같은 revision·유효구간의 중복과 겹침을 DB에서 차단한다.

원화 가격·현금·주수·거래량은 가능한 한 `BIGINT` 또는 정확한 `NUMERIC`, 비율·계수는 자릿수를 고정한 `NUMERIC`, 시각은 `TIMESTAMPTZ`, 거래일은 `DATE`로 저장한다. canonical 값을 부동소수점이나 JSONB 내부 값에만 의존하지 않는다. 대용량 원문·가격표는 공급자/기간별 partition과 논리키 index를 사용하고, schema migration·정기 백업·복구 시험으로 PostgreSQL에서 revision을 다시 만들 수 있어야 한다.

## 2. 전략과 포트폴리오가 실제로 소비하는 데이터

| 용도 | 필요한 입력 | 없을 때의 오류 |
| --- | --- | --- |
| 12개 진입 신호 | 조정 OHLCV, 연속 유효 250봉, 공식 거래일, 신호 확정시각 | 분할일 가짜 돌파·이평/RSI/MACD/ATR 왜곡, 미래정보 사용 |
| 4개 청산 규칙 | 신호일 조정 종가·ATR, 다음 세션 raw 시가, 일중 raw 고가/저가, 달력 한 달 만기 | 조정가격으로 정수주 체결, 갭·동봉 손절/익절·만기 오류 |
| 공동계좌 | raw 체결가·직전 20일 raw 거래량, 당시 universe·업종, 정수 lot, 수수료·세금·호가, 주문 가능 상태 | 1억원 현금·최대 20종목·업종 25%·유동성 0.1%·재투자 장부 오류 |
| 보유 중 사건 | 수량/가격 계수, 배당·단주·상폐 현금과 지급일, 정정·동일일 순서 | 주수·원가·현금·TP/SL 불보존, 사라진 포지션 발생 |
| 체결 가능성 | 상태, 기준가·상하한가·호가, 부분일 정지, 세션 | 잠긴 상한가 매수·하한가 매도, 정지일 허위 체결 |
| 비교·선정 | 실제 비용 프로필, 기준상품, 연도별 완전성·제외 영향 | 가상 비용을 현실 비용으로 오인하거나 편향된 전략 선정 |

신호는 완료된 `t`일 정보만 사용하고 주문은 `t+1`의 허용된 시가부터 가능하다. 공시·상태·행사는 `available_at/known_at`이 주문 결정 시각보다 늦으면 과거 판단에 사용하지 않는다. 종목 ID·활성 구간별로 지표를 새로 준비하며 코드가 같아도 다른 종목의 이력을 이어 붙이지 않는다.

현금배당을 조정가격 수익률과 현금흐름에 동시에 넣는 등 동일 경제효과를 이중 반영하지 않는다. 어떤 사건이 조정계열에 포함됐는지 `adjustment_definition`과 사건 연결로 판정한다.

## 3. PostgreSQL에서 Parquet으로 만드는 실행 snapshot

1. `dataset_revision`을 먼저 고정하고 `REPEATABLE READ, READ ONLY` 트랜잭션 또는 동등한 DB snapshot/cutoff에서만 추출한다.
2. 승인된 SQL view가 가격·종목 이력·universe·업종·상태·행사·달력·규칙·비용을 **시점 기준으로** 조인한다. 모든 이력은 `effective_from ≤ trading_date < effective_to`와 `available_at/known_at ≤ decision_at`을 함께 만족해야 하며, 정정 전후 system-valid 시점도 고정 cutoff에 맞춘다. 실행 중 운영 DB를 재조회하지 않는다.
3. 저장 위치는 저장소 밖 `<dataset>/<revision>/`이며 연도·시장 단위 Parquet와 `manifest.json`, `admission.json`, `issues.parquet`, `lineage.parquet`를 둔다. 각 실행 행은 `canonical_record_id`를 포함하고 lineage는 이를 하나 이상의 PostgreSQL `source_record_id`와 연결한다. vectorbt는 필요한 기간·종목·열만 읽는다.
4. manifest에는 DB server/database/schema version과 snapshot/cutoff, SQL 전문·hash, 추출 코드/config hash, 시작·종료·생성시각, 각 파일 schema·행 수·bytes·SHA-256, 원본 테이블별 최소/최대 ID·행 수, 이전 revision과 변경 요약을 기록한다.
5. 같은 revision은 재생성·덮어쓰기하지 않는다. 입력·SQL·코드가 달라지면 새 revision이며, Parquet hash가 다르면 기존 실행의 resume가 아니라 새 실험이다.

Parquet에 최소 포함할 실행 묶음은 `prices`, `instruments`, `universe`, `sectors`, `statuses`, `events`, `calendar`, `market_profiles`, `benchmarks`, `issues`, `lineage`다. 이를 참조하는 dataset revision·실험·감사 결과가 하나라도 존재하는 동안 PostgreSQL 원문·정규화·lineage 행을 삭제하지 않는다. 폐기는 명시적 보존정책과 참조 검사·백업·복구 시험을 거쳐야 하며, Parquet 삭제 여부와 무관하게 보존 중 revision을 재생성할 수 있어야 한다.

## 4. 인수와 실행 허가 기준

### Gate A — 데이터 인수

- 파일/DB 행 수·PK·FK·hash·revision 연결이 일치하고 원천 행까지 추적된다.
- 공식 개장일×당시 universe의 기대 종목일을 계산해 누락·중복·비거래·정지를 설명한다.
- `TRADING` 가격은 양수이고 `low ≤ open/close ≤ high`; raw/adjusted·필드별 계수·공급자 반올림·행사를 문서화된 허용오차로 전수 대조한다. 규칙이나 허용오차가 불명확한 불일치는 차단한다.
- 종목/코드/시장/업종/상태/시장규칙 유효기간은 겹치거나 설명 없이 끊기지 않는다.
- 고정 표본에서 원문→원천 행→정규화→Parquet 값을 독립 재현한다.
- 미확정 값과 제외 범위는 `data_issue`와 `admission.json`에 남고 조용히 삭제되지 않는다.

### Gate B — 실자료 실행 허가

- 실제 자료로 분할·병합·배당·단주·정지·상폐 정산의 주수·원가·현금·미수금 원장을 독립 계산과 대조한다.
- T+N 결제, 휴일 이연, settled/unsettled cash, 배당 원천징수, 합병·회사분할 successor 종목, 단주 현금정산과 지급일을 실제 자료로 대조한다.
- 다음 시가, 갭, 같은 봉 TP/SL, 상·하한가 잠김, 부분일 정지, 만기와 비용·호가 반올림을 사건별 정답과 대조한다.
- 일별 항등식 `equity = cash + receivables - payables + exposure`와 입출금 0을 전 기간 만족한다.
- 매 체결 뒤 현금·종목/업종 노출과 총노출을 다시 계산한다. 가격 상승으로 기존 보유가 총노출 80%·종목 5%·업종 25%를 넘으면 초과를 기록하되 강제매도하지 않는다. 신규 주문은 한도 초과를 만들거나 확대하지 않으며, 초과 상태에서는 허용 범위로 돌아올 때까지 신규진입을 차단한다. 최대 20종목은 항상 지킨다.
- 지원하지 않는 사건·상태·동일일 순서는 실패시키며 기본값으로 통과시키지 않는다.
- 데이터·코드·설정·비용 hash, 주문·체결·현금흐름·포지션, 실패·0거래, 중단/재개 결과를 저장한다.

Gate A만 통과하면 신호 빈도와 데이터 진단까지만 허용한다. 이는 이전 `EXPLORATORY_ADJUSTED` 수익률 허용보다 강화된 새 계약이며, 이 문서 적용 범위에서는 Gate B 전 실자료 수익률을 보고하지 않는다. Gate B까지 통과해야 실제 수익률과 48개 후보 비교를 허용한다. 현실 비용 검증과 사전 선정 규칙까지 통과하기 전에는 한 전략을 최종 선택하지 않는다.

## 5. 현재 r4 후보와 이 계약의 차이 — 2026-09-20 기준

현재 ted-startup의 [r4 사전 인수 점검](C:/Users/aeby/vscode/ted-startup/docs/data-delivery/ted-krx-daily-2015-2023/2026-09-20-r4-readiness-audit.md)은 일부 원문과 대조 결과를 전달 전용 파일에 보관하며 정식 r4도 발행되지 않았다고 기록한다. 이는 “모든 원본을 PostgreSQL 테이블에 보존한다”는 새 필수 조건을 충족하지 않는다. 해당 파일의 원문·원천 행·해시·계보를 위 PostgreSQL 테이블에 append-only로 적재하고 대사한 **새 revision**이 필요하다. 새로 적재해도 과거에 보관하지 않았던 원문은 `original`이 되지 않으며 `new_observation` 또는 `unavailable` 표지를 유지한다.

또한 최신 사전 점검의 거래 상태 293건, 실행 기업행사 505건, 가격계수 1,201건은 여전히 차단 사유다. DB에 넣었다는 사실만으로 문제가 해소되거나 실행 적격이 되지 않는다.

## 6. 범위 밖이거나 후속 전략용 데이터

현재 48개 롱 전략에는 공매도·대차·투자자별 수급·분봉·호가잔량·뉴스·재무·일반 공시 텍스트가 상시 필수 입력은 아니다. 기업행사·정지·상폐·정산을 판정하는 데 사용한 공시 원문은 필수 원천으로 PostgreSQL에 보존한다. 일봉 결과의 체결은 다음 시가·고가·저가와 공식 가격제한/상태를 이용한 **문서화된 보수 모형**이며 실제 장중 순서를 증명하지 않는다. 같은 봉 TP·SL, 부분일 정지, 상·하한가 잠김처럼 기준·낙관 경계의 차이가 결과를 바꾸면 해당 사례의 분봉·틱·호가/체결 자료를 추가 검증 입력으로 승격하고, 확보 전에는 그 결과를 `BLOCKED` 또는 불확실 경계로 남긴다. NXT·애프터마켓, 공시/재무, 숏스퀴즈 전략도 별도 원천·시점·세션 계약으로 추가한다.

## 완료 확인표

- [ ] 원 응답과 원천 행이 PostgreSQL 테이블에 있으며 정규화 행에서 역추적 가능하다.
- [ ] 2014 워밍업과 2015-06-15~2023-12-31 평가 범위의 보통주·가격·이력이 시점 기준으로 완결된다.
- [ ] 행사·상태·상폐·달력·업종·호가·가격제한·비용이 날짜별로 연결된다.
- [ ] 불변 revision을 SQL 조인으로 Parquet에 재생성하고 manifest hash로 검증할 수 있다.
- [ ] Gate A와 Gate B 증거가 분리되어 있으며 미해결 범위는 실행이 차단된다.
