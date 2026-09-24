# B1·B1b·B2·B2b·B3·B4·B5 데이터 정리 결과

기준 문서: [PRD v1 실행 계획](../prd-v1-plan-2026-09-23.md)
작성일: 2026-09-23

재실행 명령(리포 루트 기준):

```
.venv/Scripts/python -X utf8 docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/universe_diagnosis.py \
    --prepared-dir ../vectorbt-data/krx-v3-20260921-prepared-r2 \
    --tables-dir ../vectorbt-data/krx-v3-20260921-tables \
    --out docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/universe-diagnosis.json
```

실행 시간은 5.1초([`universe-diagnosis.json`](universe-diagnosis.json)의 `runtime_seconds`)이고, `date_cutoff.saw_rows_on_or_after_cutoff` 가 `false` 이므로 2024-01-01 이후 행은 집계에 들어가지 않았다.

## B1 Universe 진단 결과

정정(B1b 작업 중 발견): 아래 `q3_security_type_field.field_found_in_offline_tables: false` 는 오류다. 로컬 `universe-*.parquet`(31,475행)에는 실제로 `security_type` 컬럼이 있고 대상 2,787종목 전부 `COMMON_STOCK` 이다. `universe_diagnosis.py:294` 의 `analyze_security_type_field` 가 이 값을 검사 없이 `False` 로 하드코딩해서 생긴 오류이며, 이 스크립트와 `universe-diagnosis.json` 은 이번 작업 범위가 아니라 고치지 않았다.

로컬 Parquet 8개 테이블에는 여전히 2014년 이전 상장일·상장폐지 플래그·일별 거래상태가 없다(이 문장은 유효하다). 이 필드는 PostgreSQL 뷰 `backtest_universe_v2` 에서만 가져온다(`research/krx_lab/v3_inputs.py:23,133`, `research/krx_lab/v3_snapshot.py:27`). 따라서 PRD §5.3 기준 일별 Universe 는 현재 로컬 자료로 계산할 수 없다. B1b 는 PostgreSQL 기반 테이블(`stock`·`instrument_history`·`market_status_event`·`trading_halt`)에서 상장일·상장폐지·거래정지를 읽기 전용으로 대조했다(아래 B1b 절).

| 항목 | 수치 |
| --- | --- |
| 원가 종목 수 | 2,787종목 |
| 수정가 종목 수 | 2,312종목 |
| cohort 종목 수 | 1,076종목 |
| 원가 기준 누락 종목 | 1,711종목 |
| 1차 사유: 수정가 부재(데이터 결함) | 475종목 |
| 1차 사유: 250봉 부족(이전 전략 자격) | 52종목 |
| 1차 사유: 이슈 기록 없음(원인 미확인) | 1,184종목 |

표가 말하는 것: 누락 1,711종목 중 사유가 밝혀진 것은 527종목뿐이고, 나머지 1,184종목은 `universe-diagnosis.json` 에도 원인 코드가 없다.

정정(B5): 1,184종목은 `cohort.json` 의 `exclusions` 에 모두 사유가 있다. 아래 「B5 Gate A 전수 검증」 절을 본다.

이슈 귀속에는 한계가 있다. `issues.parquet` 2,304행 중 종목에 매핑되는 것은 781행(34%)뿐이다. 나머지 1,523행(미설명 수정계수 1,061건·수정 OHLC 순서 위반 284건·기업행사 부분 160건 등)은 `affected_scope` 가 날짜·사건 단위 라벨이라 종목에 귀속할 수 없다. 그래서 위 1,184종목의 원인이 이 1,523행 안에 섞여 있을 수 있다.

상장폐지는 직접 플래그가 없다. 데이터 종료일보다 90일 이상 앞서 원가가 끊긴 종목이 284개이지만, 이 신호만으로는 상장폐지와 데이터 절단(수집 중단)을 구분하지 못한다.

원가 OHLC≤0 135,717행 중 거래량 0 으로 설명되는 행은 135,699건, 설명되지 않는 행은 18건이다. 이 수치는 `postgresql-readiness-2026-09-21/README.md` 의 PostgreSQL 보고서 수치와 일치한다.

참고 근사치(PRD 비준수, 의사결정에 쓰지 말 것): 원가 관측 종목 수는 연 평균 2014년 1,727종목에서 2023년 2,433종목으로 늘었다. 이 수치는 상장·상장폐지를 반영하지 않은 연도별 단순 관측 카운트다.

## B2 비용·거래 규칙 효력일 이력

| 항목 | 시장 | 효력일(양도분 기준) | 값 | 출처 | 신뢰도 |
| --- | --- | --- | --- | --- | --- |
| 증권거래세 | KOSPI | ~2019-06-02 | 0.15% | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 증권거래세 | KOSPI | 2019-06-03 | 0.10% | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 증권거래세 | KOSPI | 2021-01-01 | 0.08% | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 증권거래세 | KOSPI | 2023-01-01 | 0.05% | [세무사신문](https://webzine.kacta.or.kr/news/articleView.html?idxno=24018) | 2차 |
| 증권거래세 | KOSPI | 2024-01-01 | 0.03% | [김앤장 인사이트](https://www.kimchang.com/ko/insights/detail.kc?sch_section=4&idx=26868) | 2차 |
| 증권거래세 | KOSPI | 2025-01-01 | 0% | [한국세정신문](https://taxtimes.co.kr/news/article.html?no=272624) | 2차 |
| 증권거래세 | KOSPI | 2026-01-01 | 0.05% | [부산일보](https://www.busan.com/view/busan/view.php?code=2025120110150624521) | 2차 |
| 증권거래세 | KOSDAQ | ~2019-06-02 | 0.30% | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 증권거래세 | KOSDAQ | 2019-06-03 | 0.25%(추정) | 아래 교차 확인 참고 | 2차 |
| 증권거래세 | KOSDAQ | 2021-01-01 | 0.23%(추정) | 아래 교차 확인 참고 | 2차 |
| 증권거래세 | KOSDAQ | 2023-01-01 | 0.20% | [세무사신문](https://webzine.kacta.or.kr/news/articleView.html?idxno=24018) | 2차 |
| 증권거래세 | KOSDAQ | 2024-01-01 | 0.18% | [김앤장 인사이트](https://www.kimchang.com/ko/insights/detail.kc?sch_section=4&idx=26868) | 2차 |
| 증권거래세 | KOSDAQ | 2025-01-01 | 0.15% | [한국세정신문](https://taxtimes.co.kr/news/article.html?no=272624) | 2차 |
| 증권거래세 | KOSDAQ | 2026-01-01 | 0.20% | [부산일보](https://www.busan.com/view/busan/view.php?code=2025120110150624521) | 2차 |
| 농어촌특별세 | KOSPI | 전 기간(변경 이력 미확인) | 매도분 0.15% | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 농어촌특별세 | KOSDAQ | 해당 없음 | 부과 안 됨 | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 가격제한폭 | KOSPI·KOSDAQ 공통 | 2015-06-15 | ±15% → ±30% | [한국일보](https://www.hankookilbo.com/news/article/201506150972717505) | 2차 |
| 호가가격단위 | KOSPI·KOSDAQ 통일 | 2023-01-25 | 1천~2천원 미만 5→1원, 1만~2만원 미만 50→10원, 10만~20만원 미만 500→100원(2014~2022 변경 여부 미확인) | [이투데이](https://m.ekn.kr/view.php?key=20230117010003826) | 2차 |
| 위탁수수료(참고) | 공통 | 확인 필요 | 비대면 약 0.011~0.018%, 거래소·예탁원 유관기관수수료가 양방향 별도 부과 | [미래에셋증권](https://securities.miraeasset.com/imf/200/imf606.do) | 2차 |

표가 말하는 것: 2014~2023 구간의 증권거래세율은 하락 추세로 확정되며, 위 값 그대로 PRD 백테스트 기간(2014~2023)의 비용표에 쓸 수 있다. 2024년 이후 행은 참고용이며 이 리포의 백테스트 범위 밖이다.

교차 확인 요점: KOSPI(거래세+농특세) 합계와 KOSDAQ 세율이 2014~2023 모든 구간에서 같다(0.30% → 0.25% → 0.23% → 0.20%). 이것이 KOSDAQ 추정값 두 개(2019-06-03, 2021-01-01)를 뒷받침한다.

한계: 법령 조문 원문은 열람에 실패했고, 세율은 개정이력 목록과 언론 교차 확인에 의존한다. 증권거래세는 B2b 에서 원문으로 재확인했다(아래 절).

## B2b 효력일별 비용표

증권거래세법 시행령 제5조를 law.go.kr 원문(브라우저 열람, 2026-09-24)으로 재확인했다. 2014~2023 세율은 기존 `rules.parquet` 와 모두 같고, B2 의 KOSDAQ 추정값 0.25%·0.23% 도 원문으로 확정되었다.

| 시행본(대통령령) | 시행일 | KOSPI 거래세 | KOSDAQ 거래세 | 부칙 적용례 |
| --- | --- | --- | --- | --- |
| [제24697호](https://www.law.go.kr/법령/증권거래세법시행령/(24697,20130827)) | 2013-08-29 | 1,000분의 1.5 | 1,000분의 3 | 없음 |
| [제27843호](https://www.law.go.kr/법령/증권거래세법시행령/(27843,20170207)) | 2017-04-01 | 1,000분의 1.5 | 1,000분의 3 | 코넥스 분리만 있다 |
| [제29788호](https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=208731) | 2019-06-03 | 1천분의 1 | 1천분의 2.5 | 시행 이후 양도분부터 |
| [제31290호](https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=225167) | 2021-01-01 | 1만분의 8 | 1만분의 23 | 시행 이후 양도분부터 |
| [제33209호](https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=269487) | 2023-01-01 | 1만분의 5 | 1만분의 20 | 없음(2025 시행본의 제5조 단서로 확인) |

표가 말하는 것: 세율 값에는 오류가 없고, 고칠 것은 적용 구간뿐이다.

기존 표에서 두 가지 문제를 찾았다.

1. SELL_TAX 행이 2015-01-01 부터 시작해 2014년이 비어 있다. 소비자 `V3MarketRules` 는 효력 구간이 0개면 예외를 던지므로(`research/krx_lab/v3_market.py:79-82`) 2014년 매도는 실행이 실패한다.
2. 법령은 양도분(결제일, T+2) 기준인데 소비자는 체결일로 조회한다(`research/krx_lab/v3_execution.py:369`). 그래서 법령 시행일을 경계로 그대로 쓰면 경계 직전 2개 개장일에 옛 세율이 적용된다.

원천(`kiwoom.backtest_execution_rule_v2`) 수정은 ted-startup 에 [R1 요청](requests/r1-execution-rule-sell-tax.md)으로 넘겼고, `../vectorbt-data/krx-prd-v1-b2b-20260924/rules.parquet`(15행, SHA-256 `e6bd9595…a697c`)는 원천을 대체하지 않는 대조용 기대값이다. 기존 봉인 파일은 고치지 않았다. 이 기대값은 [`rules_effective_date_table.py`](rules_effective_date_table.py) 로 만들었고, SELL_TAX 경계는 캘린더에서 「T+2 결제일이 시행일 이상인 첫 개장일」 로 계산해 2019-05-30·2020-12-29·2022-12-28 이 되었다. 이 값은 금융투자협회·언론이 안내한 매매일 기준 시작일과 같다. `rule_value` 에는 `effective_basis=TRADE_DATE`·`settlement_effective_from`·`law_reference` 를 더했고, SELL_TAX 가 아닌 7행은 그대로 복사했다.

재실행 명령(리포 루트 기준): `.venv/Scripts/python -X utf8 docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/rules_effective_date_table.py` (인자는 스크립트의 `--help` 참고, 출력 디렉터리가 이미 있으면 실패한다).

| 검증([`rules-effective-date-table.json`](rules-effective-date-table.json)) | 기존 표 | 새 표 |
| --- | --- | --- |
| 개장일 × 시장 × 규칙 4종 조회 19,672건 중 실패 | 490건(2014년 SELL_TAX 전부) | 0건 |
| 세율이 바뀐 개장일 × 시장 | - | 502건 = 2014년 공백 490 + 경계 이동 12 |
| `effective_to` 최댓값 | 2023-12-31 | 2023-12-31 |
| `tests/research/test_v3_market.py` | - | 18 passed |

표가 말하는 것: 새 표는 2014~2023 전 개장일에서 조회가 성공하고, 세율이 바뀌는 날은 공백 채움과 경계 이동뿐이다.

한계: 농어촌특별세(KOSPI 0.15%)는 원문의 세율 표가 텍스트로 추출되지 않아 2차 확인으로 남았다. 제5조의 2014~2023 개정 표지는 2021-12-21 한 건이다. 수수료·가격제한폭·호가단위·결제 행은 원문으로 재확인하지 않았다. 새 표는 `READ_ONLY_DIAGNOSTIC_NOT_ADMITTED` 이며 실행 경로에 연결하지 않았다. 원천이 고쳐지기 전까지 실행 경로는 기존 봉인 표를 쓴다.

## B3 무상증자·주식배당 수량 정산

`CorporateActionBook`(`research/krx_lab/corporate_actions.py`)이 `BONUS_ISSUE`·`STOCK_DIVIDEND` 사건에서 신주를 정산한다. 합성 fixture 로만 검증했고 실제 자료로는 실행하지 않았다.

| 항목 | 규칙 |
| --- | --- |
| 입력 필드 | `allotment_ratio`(보유 1주당 신주 수 r), `allotment_ratio_admitted`, `fractional_policy` |
| 승인 게이트 | `allotment_ratio_admitted` 가 `True` 가 아니면 `UNADMITTED_ALLOTMENT_RATIO` 로 실패한다(계약 검증과 Book 생성 양쪽). |
| 수량 | 신주 = 보유 수량 × r. 단주는 `REJECT` 면 실패, `CASH_IN_LIEU` 면 버림 후 대금을 `pay_date` 에 지급한다. |
| 가격 | 보유·대기 계획의 가격 수준을 1 + r 로 나누고 `avg_volume20` 은 곱한다. |
| 원가 | 신주 원가는 0 이므로 총 원가는 그대로다. 단주를 현금으로 받으면 그 비율만큼 원가를 줄인다. |
| 세금 | 의제배당 과세는 모델링하지 않고 `DEEMED_DIVIDEND_TAX_ON_STOCK_ISSUES_NOT_MODELLED` 제한으로 남긴다. |

표가 말하는 것: 배정비율과 총주식 배수를 필드 이름으로 분리했고, 미승인 계수는 허용오차 없이 실패로 막는다.

- 배정비율을 SPLIT 의 `quantity_ratio`(총주식 배수)로 받지 않는 이유는 미승인 104키가 바로 이 두 개념의 혼동에서 나왔기 때문이다.
- 검증: `tests/research/test_corporate_actions.py` 41 passed, `tests/research` 전체 714 passed(2026-09-23).
- 한계: OHLCV20 탐색의 176건 제외는 `ohlcv20_exploratory.py` 의 무효화 규칙(`_AUDIT_CATEGORY`)에서 나온다. 이 경로는 `CorporateActionBook` 을 쓰지 않으므로, 연결 작업(B3b) 전에는 176건이 그대로 제외된다.

## B4 원가 OHLC≤0 대조

[`nonpositive_ohlc_reconciliation.py`](nonpositive_ohlc_reconciliation.py)가 원가 OHLC≤0 행을 거래상태(`status-00110.parquet`)·거래량과 대조한다. 결과는 [`nonpositive-ohlc-reconciliation.json`](nonpositive-ohlc-reconciliation.json)이고, 실행 시간은 12.2초, `saw_rows_on_or_after_cutoff` 는 `false` 다. 인자는 `universe_diagnosis.py` 와 같다.

| 분류 | 기준 | 행 수 |
| --- | --- | --- |
| STATUS_HALTED | 같은 종목·일에 HALTED·NO_BAR_HALTED 기록이 있다 | 280 |
| STATUS_PARTIAL_TRADING | PARTIAL_TRADING 기록이 있다 | 0 |
| ZERO_VOLUME_NO_STATUS | 상태 기록 없이 거래량이 0 이다(무거래) | 135,419 |
| UNEXPLAINED | 상태 기록이 없는데 거래량이 양수다 | 18 |

표가 말하는 것: 135,717행 전부가 시가·고가·저가만 0 이고 종가는 양수인 한 가지 형태이며, 정지·무거래로 설명되지 않는 행은 B1 과 같은 18건이다.

- 상태 테이블 역방향: 정지 280행은 모두 원가 OHLC≤0 행과 짝이 맞고, PARTIAL_TRADING 12행은 원가 OHLC 가 모두 양수다. 정지 기록 280행은 전부 KOSDAQ 이다.
- 휴장일에 걸린 행은 없다(개장일 목록에 없는 날짜를 휴장으로 판정).

설명되지 않는 18건(모두 시가·고가·저가 0, 종가 양수, 출처 `KRX_OPEN_API`):

| 종목 | 일자 | 시장 | 종가 | 거래량 | 체결 단가 | 전일 종가 | 익일 거래량 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 001000 | 2014-05-07 | KOSDAQ | 4,675 | 50 | 4,695 | 4,695 | 249 |
| 056340 | 2014-05-08 | KOSDAQ | 96 | 191 | 96 | 96 | 0 |
| 008830 | 2015-01-05 | KOSDAQ | 18,500 | 1 | 18,700 | 18,700 | 23 |
| 053870 | 2015-08-17 | KOSDAQ | 1,220 | 5,234 | 1,220 | 1,220 | 0 |
| 016380 | 2016-02-16 | KOSPI | 2,500 | 437 | 2,500 | 2,500 | 0 |
| 015540 | 2016-03-25 | KOSPI | 1,700 | 5,161 | 1,700 | 1,700 | 0 |
| 215100 | 2017-06-12 | KOSDAQ | 2,135 | 2 | 2,135 | 2,135 | 0 |
| 060570 | 2017-07-17 | KOSDAQ | 5,420 | 12,771 | 5,420 | 5,420 | 1,305,597 |
| 047810 | 2017-10-11 | KOSPI | 47,700 | 141 | 47,700 | 47,700 | 0 |
| 056730 | 2019-02-11 | KOSDAQ | 1,460 | 60,795 | 1,460 | 1,460 | 0 |
| 270520 | 2019-05-29 | KOSDAQ | 2,085 | 58,500 | 2,090 | 2,090 | 2 |
| 310200 | 2019-05-29 | KOSDAQ | 2,230 | 67,503 | 2,230 | 2,230 | 1 |
| 033790 | 2020-01-28 | KOSDAQ | 829 | 401 | 829 | 829 | 0 |
| 349720 | 2020-10-07 | KOSDAQ | 1,995 | 147,946 | 1,950 | 2,000 | 32 |
| 141070 | 2021-02-01 | KOSDAQ | 1,365 | 177 | 1,365 | 1,365 | 7,710,262 |
| 336570 | 2021-10-14 | KOSDAQ | 2,675 | 78 | 2,675 | 2,675 | 0 |
| 215090 | 2022-02-09 | KOSDAQ | 1,505 | 1,911 | 1,505 | 1,505 | 0 |
| 089530 | 2023-04-24 | KOSDAQ | 600 | 120 | 600 | 600 | 0 |

표가 말하는 것: 체결 단가(거래대금 ÷ 거래량)가 18건 중 17건에서 전일 종가와 정확히 같고, 11건은 다음 거래일 거래량이 0 이다.

- 가설(원천 미확인): 정규장 체결 없이 장전 시간외 종가매매(전일 종가로 체결)만 있었던 날로 보인다. 정지가 시작된 날이 많다는 점도 이 가설과 맞는다. 349720 은 체결 단가가 전일 종가와 달라 이 가설로 설명되지 않는다.
- 이슈 연결: `issues.parquet` 의 `RAW_NONPOSITIVE_PRICE_TRADED`(13건)는 종목 식별자가 비어 있어 날짜로만 대조할 수 있고, 날짜가 겹치는 것이 6건이다. 종목 단위 연결은 확정하지 못했다.
- 한계: 무거래 135,419행에는 정지 기록이 없는 정지일이 섞여 있을 수 있다. 정지 기록이 KOSDAQ 에만 있으므로, KOSPI 정지일은 전부 이 분류에 들어간다. 판별하려면 B1b 의 일별 거래상태가 필요하다.

## B1b 상장·폐지·거래정지 대조

[`listing_halt_reconciliation.py`](listing_halt_reconciliation.py)가 PostgreSQL 기반 테이블(`kiwoom.stock`·`instrument_history`·`market_status_event`·`trading_halt`, 대상 2,787종목)을 단일 읽기 전용 트랜잭션(`BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY ... ROLLBACK`)으로 추출해 로컬 자료·B1·B4 와 대조한다. 결과는 [`listing-halt-reconciliation.json`](listing-halt-reconciliation.json), 추출 결과는 `../vectorbt-data/krx-prd-v1-b1b-20260924/`(manifest.json 에 SQL 원문·해시·행 수)이다.

재실행 명령(리포 루트 기준):

```
.venv/Scripts/python -X utf8 docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/listing_halt_reconciliation.py \
    --extract-dir ../vectorbt-data/krx-prd-v1-b1b-20260924 \
    --prepared-dir ../vectorbt-data/krx-v3-20260921-prepared-r2 \
    --tables-dir ../vectorbt-data/krx-v3-20260921-tables \
    --out docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/listing-halt-reconciliation.json
```

`--mode extract`/`--mode analyze` 로 단계를 나눌 수 있다(디렉터리가 이미 있으면 extract 는 실패한다). analyze 실행 시간은 5.9~6.0초, `date_cutoff.saw_rows_on_or_after_cutoff` 는 `false` 다. 모든 추출 쿼리는 2023-12-31 이하로 제한했고, 그 이후 값(`delisted_date`·`last_trade_date`·`resume_date`·`official_delist_date`·`announced_at`·`disclosed_at`)은 SQL CASE 로 NULL 처리하고 `*_after_cutoff` 로만 표시했다(`stock.delisted_date` 176건이 이렇게 가려졌다).

### A. 상장일

| 항목 | 수치 |
| --- | --- |
| 대상 종목 | 2,787 |
| stock.listed_date 있음 | 2,364 |
| instrument_history 기준 있음 | 1,802 |
| 둘 다 있음 | 1,570 |
| 둘의 값이 다름 | 12 |
| instrument_history 내부 상장일 값이 여럿(내적 불일치) | 0 |
| 상장일이 첫 원가 거래일보다 늦은 모순 | 13 |
| 2014-01-02 이후 상장 | 884 |
| 2013년 하반기 상장(120거래일≈6개월 근사, 2014년 초 경계 후보) | 32 |

표가 말하는 것: `stock.listed_date` 와 `instrument_history` 최소 `listed_date` 가 다른 12종목은 전부 `stock.listed_date` 가 더 늦다(예: 003670 은 2019-05-29 대 2001-11-01). 시장 이전상장·재상장 등으로 `stock.listed_date` 가 원래 IPO 일이 아닐 수 있다는 뜻이며, 어느 쪽이 PRD 의 "상장일" 의미에 맞는지는 확인하지 못했다.

- 근사: 2013-07-01~2013-12-31 상장 32종목은 2014-01-02 이전 개장일 캘린더가 없어 "120거래일≈6개월" 로만 근사했고, 정확한 거래일 수 조건은 계산하지 못했다.
- 한계: 상장일이 첫 원가 거래일보다 늦은 13건은 데이터 결함인지 재상장/시장이전 때문인지 이번 대조로는 구분하지 못한다.

### B. 상장폐지

| 근거 | 종목 수(2023-12-31 이하) |
| --- | --- |
| stock.delisted_date | 266 |
| market_status_event status=DELISTED | 364 |
| trading_halt notice_type=DELIST | 188 |
| 합집합 | 398 |
| B1 근사(90일 이상 원가 절단) | 284 |
| ↳ 위 합집합에 근거 있음 | 254 |
| ↳ 근거 없음(수집 절단 후보) | 30 |

표가 말하는 것: B1 의 "90일 이상 앞서 원가가 끊긴 284종목" 은 이번 대조에서도 그대로 284개로 재현됐고, 그중 254개(89%)는 실제 폐지 근거(세 원천 중 하나)가 있다. 나머지 30개는 폐지 근거가 없는 순수 수집 절단 후보다.

- 마지막 원가 거래일 대비 MSE `last_trade_date` 차이(일, 음수=원가가 더 늦게 관측): 표본 186건, 중앙값 0일, 25백분위수 -41일, 최솟값 -3,093일(이상값 1건).
- 마지막 원가 거래일 대비 "1차 폐지 근거일"(세 원천 중 가장 이른 날짜) 차이: 표본 398건, 중앙값 -164일. 상장폐지 사유 발생 공시가 실제 상장폐지보다 훨씬 먼저(중앙값 164일) 나온다는 뜻으로, 원가는 그 사이 계속 관측된다.
- 한계: "1차 폐지 근거일" 은 최솟값(가장 이른 이벤트)을 쓰므로 관리종목 지정 등 예비 경고성 공시도 섞여 있어 실제 상장폐지일보다 훨씬 이를 수 있다.

### C. 거래정지

MSE 정지 구간(HALTED→다음 TRADING/DELISTED 전날, 개장일 기준, 끝이 없으면 2023-12-28 까지 열린 구간) 3,849개(그중 1,030개가 끝을 못 찾아 열려 있음), `trading_halt` 구간(halt_date~resume_date 전날, resume_date 없으면 halt_date 하루) 1,460개(확정 범위 117개). 상한값(원래 구간)과 보수 추정치(`MSE_INTERVAL_TRUNCATED`: 닫힌·열린 구간 모두 시작일 이후 첫 원가 거래량>0 날짜의 전날에서 자르고, 시작일 당일부터 거래량이 있으면 빈 구간으로 둔 것) 를 나란히 뒀다. 분류 기준(`halt_source_category`)은 상한값 그대로 두고, 보수 추정치는 `halt_source_category_truncated` 로 별도 집계했다.

| B4 ZERO_VOLUME_NO_STATUS(135,419행) 재분류 | 상한값(전체 / KOSPI / KOSDAQ) | 보수 추정치(전체 / KOSPI / KOSDAQ) |
| --- | --- | --- |
| MSE 정지 구간 안 | 104,067 / 0 / 104,067 | 53,007 / 0 / 53,007 |
| trading_halt 시작일만 일치 | 79 / 76 / 3 | 80 / 76 / 4 |
| 어느 쪽에도 없음 | 31,273 / 21,409 / 9,864 | 82,332 / 21,409 / 60,923 |

표가 말하는 것: 무거래 135,419행 중 "정지로 설명됨" 은 구간을 어떻게 잡느냐에 따라 77%(상한값 104,067)에서 39%(보수 추정치 53,007)까지 갈린다 — 그래도 B4 가 "정지 기록 없음" 으로 뭉뚱그린 행의 상당수는 실제로 정지 중이었다는 결론은 유지된다. KOSPI 는 두 추정치 모두 21,409행이 그대로 남는다(원천 자체가 KOSDAQ 편중).

- 원인: 상한값의 닫힌 구간에도 모순(구간 안인데 원가 거래량>0)이 80,488건 있는데, HALTED 의 의미(무상증자·개선기간 부여·상장폐지 사유 발생 등 실제 매매정지 공시) 문제가 아니라 해제 이벤트(TRADING 1,205건)가 정지 이벤트(HALTED 3,849건)보다 훨씬 적어 "다음 TRADING/DELISTED 전날" 규칙이 다른 정지의 해제일까지 구간을 이어 붙이기 때문으로 본다. 열린 구간(1,030개, 그중 925개는 재개로 보이는 첫 양수거래량 날짜가 있음)의 모순은 427,171건으로 훨씬 크다.
- 검증: B4 의 STATUS_HALTED 280행은 상한값·보수 추정치 모두 280/280 전부 구간 안에 들어간다(초기 구현은 44/280 이었는데, 같은 날 HALTED·TRADING 공시가 함께 나오는 경우 시작일 자체가 구간에서 빠지는 버그가 있어 "시작일은 항상 포함" 으로 고쳤다).
- 정지 사유 상위 10개 중 보수 추정치에서 0행으로 잘려나가는 것은 "무상증자"·"불성실공시법인 지정"(당일 재개형 형식적 공시로 추정)이고, "개선기간 부여"(8,135)·"상장폐지 사유 발생"(5,973)·"투자자 보호"(4,282)는 여러 날 이어지는 정지로 남는다.
- B4 의 UNEXPLAINED 18건 중 9건은 당일에 정지 사건(MSE HALTED 또는 trading_halt HALT)이 있었고, 다음 거래일에 정지 사건이 있는 건은 0건이다. 나머지 9건은 당일·다음 거래일 모두 정지 사건이 없어 여전히 설명되지 않는다.
- 한계: MSE HALTED 이벤트 3,849건 중 KOSPI 는 15건(0.4%), trading_halt HALT 1,460건 중 KOSPI 는 79건(5%)뿐이다. 두 원천 모두 정지 기록이 사실상 KOSDAQ 전용이라, **KOSPI 무거래일(위 표의 KOSPI 21,409행)이 실제 정지 때문인지는 상한값·보수 추정치 어느 쪽으로도 판별되지 않는다.**
- 한계: MSE `event_id` 로 미루어 볼 때 같은 종목·날짜에 사유가 다른 HALTED 공시가 여러 건 겹칠 수 있어(예: stock_id 93 은 2020-09-04 하루에 사유가 다른 HALTED 공시 12건), 정지 구간을 "가장 이른 HALTED~가장 가까운 다음 TRADING/DELISTED" 로 병합했다. 개별 사유별 구간은 구분하지 않았다.

### D. B1 원인 미확인 누락 1,184종목 교차 집계

`universe_diagnosis.py` 의 1차 사유 `NO_ADMISSION_ISSUE_RECORD` 전체 목록(1,184종목, `universe-diagnosis.json` 의 1,184와 일치)을 재계산해 교차 집계했다.

| 폐지 근거 | 상장 시점 | 정지 이력 | 종목 수 |
| --- | --- | --- | --- |
| 없음 | 2014-01-02 이전 | 없음 | 365 |
| 없음 | 2014-01-02 이전 | 있음 | 316 |
| 없음 | 2014-01-02 이후 | 없음 | 155 |
| 없음 | 2014-01-02 이후 | 있음 | 285 |
| 없음 | 상장일 정보 없음 | 있음 | 1 |
| 있음 | 2014-01-02 이전 | 없음 | 4 |
| 있음 | 2014-01-02 이후 | 없음 | 11 |
| 있음 | 2014-01-02 이후 | 있음 | 47 |

표가 말하는 것: 1,184종목 중 폐지 근거가 있는 것은 62건(5%)뿐이라, 나머지 1,122종목(95%)의 cohort 제외 사유는 상장폐지가 아니다. 정지 이력이 있는 종목이 649종목(55%)으로 절반을 넘어, 거래정지가 잦았던 종목이 cohort 에서 원인 불명으로 빠졌을 가능성을 시사하지만 인과관계는 확인하지 못했다.

- 한계: "정지 이력 있음" 은 대상 기간(≤2023-12-31) 어느 시점에든 HALTED/HALT 기록이 한 번이라도 있으면 참으로 두었다. 그 정지가 cohort 제외와 시점적으로 관련 있는지는 보지 않았다.
- 한계: `stock.listed_date` 와 `instrument_history` 가 다른 12종목(A 절)처럼, "상장 시점" 버킷이 실제 IPO 일과 다를 수 있는 종목이 섞여 있을 수 있다.

## B5 Gate A 전수 검증

재실행: `.venv/Scripts/python -X utf8 docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/gate_a_verification.py`(리포 루트 기준, 54.7초). 출력은 [`gate-a-verification.json`](gate-a-verification.json)과 종목별 [`gate-a-instruments.csv`](gate-a-instruments.csv)(2,787행)이며, 2024-01-01 이후 행은 어느 입력에서도 읽히지 않았다(`saw_rows_on_or_after_cutoff_by_source` 전부 `false`).

| 검사 | 결과 |
| --- | --- |
| member 봉인 | `verify_v3_snapshot` 로 11개 member 내용 해시를 다시 계산해 통과했다. 운영 DB 의 revision·member 봉인값([`gate-a-db-member-seal.txt`](gate-a-db-member-seal.txt), 2026-09-24 읽기 전용 조회)과 11/11 일치한다. |
| 가격쌍 완전성 | 개장일×보통주 유효기간 격자 5,099,694행 중 원가·수정가 쌍 4,574,759행, 원가만 524,935행, 수정가만 0행이다. 격자 밖 가격 행과 중복은 0건이다. |
| 원가만 있는 행 | 정지 207행과 무거래 64,496행으로 설명되고 460,232행은 미설명이다. 미설명 행은 전부 수정가가 아예 없는 475종목에 속하며, 합격 종목에는 0행이다. |
| OHLC 유효성 | 거래 행(`research/krx_lab/v3_inputs.py:205-223` 정의) 4,963,965행에서 수정가 OHLC 위반은 0건이다. 원가 위반 종목은 18종목으로 cohort·B4 와 같다. |
| 수정계수 | adjustment member 의 미설명 계수 1,061행(452종목) 중 대상 모집단에 드는 397종목이 cohort 의 397종목과 정확히 같다. |
| 종목별 대조 | 합격 1,076종목에서 독립 결함은 0건이고, 제외 1,711종목은 모두 사유가 재현되었다(재현 안 됨 0건). |

표가 말하는 것: 봉인 스냅샷과 cohort 는 독립 재계산과 전량 일치하므로, 현재 Gate A 데이터 수준 적격 종목은 기존 1,076종목 그대로다.

| `gate_a_status` | 종목 | 뜻 |
| --- | --- | --- |
| PASS | 1,076 | 가격쌍 완전, 결함·미지원 사건 없음 |
| EXCLUDED_DATA_DEFECT | 843 | 수정가 부재·미설명 계수·원가 OHLC 위반·기업행사 부분 반영 중 하나 이상 |
| EXCLUDED_UNSUPPORTED_EVENT | 771 | 데이터 결함은 없고 가격이 매겨지지 않은 사건(권리락·감자·분할·배당락 등)만 있음 |
| EXCLUDED_WARMUP_ONLY | 97 | 250 완전 세션 부족만 있음. PRD 기준(120거래일)을 채우는 종목은 38개다 |

표가 말하는 것: 「최종 종목」 은 Gate A 데이터 수준에서 1,076종목으로 확정되지만, PRD Universe 는 워밍업 기준(D5)과 미지원 사건 처리(B6·D4) 결정에 따라 늘어날 수 있다. 이번 검증은 cohort 를 다시 만들지 않았다.

**B1 정정.** B1 이 「원인 미확인」 으로 센 1,184종목은 모두 `cohort.json` 에 사유가 있다(사유 없음 0건). 주요 사유는 권리락 702·미설명 계수 295·분할 147·감자 133·배당락 130·워밍업 106종목이다(중복 허용). B1 은 `issues.parquet` 만 매핑하고 `cohort.json` 의 `exclusions` 를 보지 않았다. 이에 따라 [R2](requests/r2-issue-attribution.md)의 근거를 「제외 사유가 원천 이슈 행까지 추적되지 않는다」 로 고쳤고 요청 내용은 그대로다.

한계: 수정계수의 미설명 판정은 원천이 계산한 `explanation_status` 를 따른다. 이 리포에는 그 판정을 재계산할 허용오차 상수가 없어, 수정가/원가 비율 변화일과 사건의 대응은 대용치만 냈다(JSON `check4`). 구 PYKRX 원천쌍 전용 분기(`v3_scope.py` 의 `current_source_pair`)는 이 스냅샷에서 사유를 만들지 않아 재구현하지 않았다.

### B5 추가 검사(check8~12)와 Gate A 항목별 판정

재실행: 위 명령에 `--check10-mode analyze` 를 붙이면 DB 를 다시 조회하지 않는다(83.5초). 원문 표본 추출본과 SQL 은 `../vectorbt-data/krx-prd-v1-b5-20260924/`(`extract.sql`·`manifest.json`)에 있다.

| Gate A 항목 | 판정 | 근거 |
| --- | --- | --- |
| 1 PK·FK·원천 추적 | FAIL | admission_issue member 에 행 전체가 같은 중복이 75건 있다. 나머지 10개 member 는 중복 0건, 종목 참조 오류 0건이고, 가격 9,674,453행 전부가 payload 해시로 원천에 연결된다. |
| 2 기대 종목·일 격자 | PASS | 위 표와 같다. |
| 3 OHLCV·필드별 계수 | PASS(거래량 계수는 검증 불가) | 거래량의 결측·음수·비정수는 0건이다. adjustment member 에 거래량 계수 필드가 없어 계수 대조는 하지 못했다. |
| 4 유효기간 연속성 | FAIL | universe·identifier 는 개장일 기준 겹침·공백이 0건이다. 실행 규칙은 SELL_TAX 미포함 490개장일(R1 과 일치)과 TICK_SIZE 미포함 2,689개장일(신규, 원인 미조사)이 있다. |
| 5 고정 표본 원문 재현 | PASS | 가격 표본 210행이 원문 payload → 원천 행 → Parquet 까지 OHLC·거래량 모두 일치한다. |
| 6 이슈 처리 기록 | PASS | 이슈 2,304건과 처리 기록이 1:1 이고, 미해결 0건이다. |

표가 말하는 것: 가격 데이터 자체(항목 2·3·5)는 통과했고, FAIL 은 이슈 테이블 중복과 실행 규칙 적용 범위에서 나온다. 두 가지 모두 합격 1,076종목의 가격 값에는 영향을 주지 않는다.

거래량 참고 수치: 같은 날 원가·수정가 가운데 한쪽만 거래량이 0인 행은 100행(14종목)이고, 합격 종목에서는 27행(3종목)이다. 가격 비율과 거래량 비율이 따로 바뀐 날은 4,456행(267종목)이고, 합격 종목에서는 390행(82종목)이며 그중 사건이 있는 날은 10행뿐이다. 계수 규칙은 추정하지 않았다.

후속(요청서 미작성): TICK_SIZE 미포함 2,689개장일과 admission_issue 중복 75건은 원천 결함 후보다. 원인을 조사하지 않았으므로 아직 ted-startup 요청서로 넘기지 않았다.
