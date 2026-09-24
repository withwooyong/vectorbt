# R1. `backtest_execution_rule_v2` 의 SELL_TAX 2014년 공백과 경계 기준을 원천에서 고쳐 달라

목적: PRD v1 백테스트가 2014~2023 전 구간에서 매도 세율을 조회할 수 있게 원천 규칙 테이블을 수정한다. 대상은 ted-startup, 작성자는 vectorbt 리포다. 이 문서를 외부에 전송하지 않았다. 전체 데이터 인수는 현재 `BLOCKED` 다.

## 1. 배경

이 리포는 `research/krx_lab/v3_snapshot.py:34` 의 필터(`effective_from<='2023-12-31' AND effective_to>='2014-01-01'`)로 `kiwoom.backtest_execution_rule_v2` 를 스냅샷해 `<리포 루트>/../vectorbt-data/krx-v3-20260921-prepared-r2/rules.parquet`(15행, SHA-256 `232be3a5…a498c`)를 만들었다. 소비자 `V3MarketRules`(`research/krx_lab/v3_market.py:79-82`)는 해당 일자에 매칭되는 효력 구간이 0개면 예외를 던진다.

## 2. 발견한 결함 두 가지

| 결함 | 내용 | 영향 |
| --- | --- | --- |
| 공백 | SELL_TAX 행이 2015-01-01 부터 시작해 2014-01-01~2014-12-31 이 비어 있다 | 2014년 매도 조회 490건(245개장일×2시장)이 실패한다 |
| 경계 기준 불일치 | 법령은 「양도분」(결제일, T+2) 기준인데 소비자는 체결일로 조회한다(`research/krx_lab/v3_execution.py:369`). 원천은 법령 시행일(2019-06-03·2021-01-01·2023-01-01)을 그대로 경계로 쓴다 | 경계 직전 2개 개장일×2시장×3회=12건에 옛 세율이 적용된다 |

세율 값 자체는 원천과 법령 원문(law.go.kr, 2026-09-24 재확인)이 모두 일치한다. 원문 근거는 `../README.md` 「B2b 효력일별 비용표」 절 표를 아래로 옮긴다.

| 시행본(대통령령) | 시행일 | KOSPI 거래세 | KOSDAQ 거래세 | 부칙 적용례 |
| --- | --- | --- | --- | --- |
| [제24697호](https://www.law.go.kr/법령/증권거래세법시행령/(24697,20130827)) | 2013-08-29 | 1,000분의 1.5 | 1,000분의 3 | 없음 |
| [제27843호](https://www.law.go.kr/법령/증권거래세법시행령/(27843,20170207)) | 2017-04-01 | 1,000분의 1.5 | 1,000분의 3 | 코넥스 분리만 있다 |
| [제29788호](https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=208731) | 2019-06-03 | 1천분의 1 | 1천분의 2.5 | 시행 이후 양도분부터 |
| [제31290호](https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=225167) | 2021-01-01 | 1만분의 8 | 1만분의 23 | 시행 이후 양도분부터 |
| [제33209호](https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=269487) | 2023-01-01 | 1만분의 5 | 1만분의 20 | 없음(2025 시행본 제5조 단서로 확인) |

표가 말하는 것: 세율 값에는 오류가 없고, 고칠 것은 적용 구간(공백·경계)뿐이다.

## 3. 요청 내용

| 묶음 | 확보할 자료 | 성공 조건 |
| --- | --- | --- |
| 공백 채움 | 2014-01-01 부터 시작하는 SELL_TAX 행(KOSPI 거래세 0.15%+농특세 0.15%, KOSDAQ 0.30%, 시행본 제24697호 근거) | 2014-01-01 이 포함된 SELL_TAX 구간이 KOSPI·KOSDAQ 각 1개 이상 존재 |
| 경계 재계산 | 경계를 체결일 기준으로 저장: 2019-05-30, 2020-12-29, 2022-12-28. 계산 규칙은 「T+2 결제일이 법령 시행일 이상인 첫 개장일」 | 세 경계 모두 위 날짜와 일치. 대안으로 법령 시행일을 유지하고 별도 필드로 기준을 구분하는 방식도 가능하나, 그 경우 이 리포의 소비 코드(`v3_execution.py`)를 바꿔야 하므로 경계 자체를 체결일 기준으로 저장하는 방식을 권장한다 |
| 부가 필드 | 가능하면 `rule_value` 에 `effective_basis`(예: `TRADE_DATE`) · `settlement_effective_from`(원 법령 시행일) · `law_reference`(시행령 번호) 를 함께 저장 | 세 필드가 SELL_TAX 8행 모두에 존재 |
| 농특세 1차 근거 | 농어촌특별세 0.15% 의 원문 세율 표(law.go.kr 제5조)가 이미지라 이 리포는 1차 확인에 실패했다. 원천 쪽에 1차 근거 `source_url` 요청 | `source_url` 이 텍스트로 추출 가능한 조문 페이지를 가리킴 |

이 요청은 2014~2023 SELL_TAX 에 한정한다. 2024-01-01 이후 SELL_TAX 행과 SELL_TAX 이외 규칙(COMMISSION·PRICE_LIMIT·TICK_SIZE·SETTLEMENT)은 이 리포가 원문 미재확인 상태이므로 요청 범위가 아니다.

## 4. 납품 후 검증

1. 이 리포에서 원천을 다시 스냅샷한 SELL_TAX 8행이 기대값 `<리포 루트>/../vectorbt-data/krx-prd-v1-b2b-20260924/rules.parquet`(SHA-256 `e6bd9595…a697c`)의 SELL_TAX 8행과 시장·`effective_from`·`effective_to`·세율이 같은지 대조한다. **이 기대값은 원천을 대체하지 않는 대조용 로컬 계산이며**, 첨부 [`r1-expected-sell-tax.json`](r1-expected-sell-tax.json) 에 8행 전부를 실었다.
2. 2014~2023 개장일×시장×규칙 4종 조회 19,672건에서 실패 0건을 확인한다.
3. 기존 대비 세율이 바뀌는 개장일×시장이 502건(공백 490+경계 이동 12)인지 확인한다.
4. 검증 도구는 `../rules_effective_date_table.py` 와 그 출력 `../rules-effective-date-table.json` 이다. 재현 명령: `.venv/Scripts/python -X utf8 docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/rules_effective_date_table.py --prepared-dir <새 스냅샷 디렉터리> --out-data-dir <새 출력 디렉터리> --out <새 JSON>`(리포 루트 기준). 기본값은 기존 봉인 스냅샷과 기존 출력이라 납품 검증에는 세 인자를 모두 바꿔야 한다. 이 스크립트는 입력 표를 「기존 표」 자리에 두고 법령 상수로 만든 기대 표와 비교하므로, 납품본이 맞으면 `validation.old_table_probe.failure_count` 가 0 이고 세율이 바뀐 개장일×시장도 0건이어야 한다.

첨부: [`r1-expected-sell-tax.json`](r1-expected-sell-tax.json) — 기대 SELL_TAX 8행(시장·효력일·세율·`effective_basis`·`law_reference`·`source_url`). `<리포 루트>/../vectorbt-data/krx-prd-v1-b2b-20260924/rules.parquet` 에서 읽어 생성했다.
