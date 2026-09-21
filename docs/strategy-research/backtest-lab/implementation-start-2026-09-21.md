# 백테스트 첫 구현: 전략과 입력 준비

목적은 봉인된 v3 자료로 기본 56개와 넓은 청산 조건의 별도 56개를 비교하는 방법과 현재 실행 상태를 설명하는 것이다. 입력 준비, 날짜별 시장 규칙, 현금·기업행사 장부, 독립 계산 검증, 실자료 배치와 보고 명령을 구현했다. **실제 2,464개 실행과 저장 장부 재검증, 보고서·그림 및 독립 검토를 완료했다. 성공 2,023개·차단 441개다.** 원본·반복 계산용 표의 전수 값 대조와 공통 1,076종목의 입력 준비를 마쳤다. 최종 결과는 [결과 보고서](results-v3-2026-09-21/README.md)에 기록한다. 범위는 2014년 준비기간과 2015-06-15~2023-12-31 정규장 KOSPI·KOSDAQ 보통주이며 2024년 이후 가격은 잠근다.

## 이번에 정한 비교 방법

기존 12개 매수 조건에 거래량을 확인하는 돌파 조건 2개를 추가한다. 새 조건은 20일 또는 60일 고점을 돌파하면서, 당일 거래량이 직전 20일 평균의 1.5배 이상인 경우다. 평균을 계산할 때 당일 거래량은 넣지 않는다.

각 매수 조건을 아래 네 청산 조건과 조합한다. 기본 실험과 넓은 청산 실험은 각각 56개이며, 결과와 전략 선정도 따로 관리한다. 추가 후보는 사용자가 확장 비교에 동의한 뒤 결과를 보기 전에 정했다. 수익성이 검증된 값이 아니다.

| 조건 | 기본 실험: 손절 / 익절 | 별도 넓은 청산 실험: 손절 / 익절 |
| --- | --- | --- |
| 고정 비율 A | −3% / +6% | −8% / +16% |
| 고정 비율 B | −5% / +10% | −10% / +20% |
| 변동성 A | −1.5 ATR / +3 ATR | −3 ATR / +6 ATR |
| 변동성 B | −2 ATR / +4 ATR | −4 ATR / +8 ATR |

ATR은 최근 14일 가격 변동폭을 나타내는 지표다. 모든 가격은 **매수 신호가 나온 날의 종가**를 기준으로 정한다. 다음 날 실제 매수가와 호가 단위 반올림 때문에 실제 손익 비율은 달라질 수 있다. 하루에 손절·익절에 모두 닿으면 손절을 우선하며, 최대 달력 한 달 보유 규칙을 유지한다.

1억 원으로 최대 20종목을 보유하며 **같은 업종에 투자하는 금액을 제한하지 않는다**. 다른 기존 자금 규칙은 유지한다. 전체 투자금의 최대 80%를 투자하고, 거래 한 건의 계획 손실을 계좌 평가액의 0.5% 이내로 제한한다. 따라서 손절 폭이 넓어지면 매수 수량이 줄어들 수 있다. 이것이 실제 손실을 보장된 범위에 묶는다는 뜻은 아니다. 시가 급락과 비용은 별도로 반영해야 한다.

## v3 입력부터 보고까지의 실행 명령

기존 `config`, `plan`, `run`은 이전 48개 계약을 유지한다. `config56 → prepare56`은 기본·넓은 청산 실험의 설정과 계획만 고정한다. `prepare-v3 → certify-v3 → run-v3 → report-v3`는 검증된 v3 입력을 사용해 계산하고 보고하는 별도 경로다. `run-v3`는 기본 네 청산과 넓은 네 청산을 별도로 실행한다. 날짜별 수수료·매도세 적용 대조군과 정액 bp 비용 스트레스도 구별해 저장하며 두 비용 모델을 합산하지 않는다.

아래는 저장소 루트 PowerShell의 명령 형식이다. 각 출력은 새 디렉터리여야 하며, 이미 완료된 원본 추출·표 변환은 다시 수행할 필요가 없다. 실제 경로와 진행 상태는 [작업 WBS](real-backtest-v3-execution-wbs-2026-09-21.md)에서 확인한다.

```powershell
$source = 'C:/path/to/new-v3-source'
$tables = 'C:/path/to/new-v3-tables'
$prepared = 'C:/path/to/new-v3-prepared'
$evidence = 'C:/path/to/new-v3-evidence'
$batch = 'C:/path/to/new-v3-batch'
$report = 'C:/path/to/new-v3-report'
.venv/Scripts/python.exe -X utf8 -m research.krx_lab snapshot-v3 --out $source
.venv/Scripts/python.exe -X utf8 -m research.krx_lab verify-snapshot-v3 --snapshot $source
.venv/Scripts/python.exe -X utf8 -m research.krx_lab materialize-v3 --source $source --out $tables
.venv/Scripts/python.exe -X utf8 -m research.krx_lab verify-tables-v3 --source $source --out $tables

.venv/Scripts/python.exe -X utf8 -m research.krx_lab config56 --snapshot $source --out .local/basic56.json
.venv/Scripts/python.exe -X utf8 -m research.krx_lab config56 --snapshot $source --out .local/wide56.json --wide-exits
.venv/Scripts/python.exe -X utf8 -m research.krx_lab prepare56 --config .local/basic56.json --out .local/basic56-plan
.venv/Scripts/python.exe -X utf8 -m research.krx_lab prepare56 --config .local/wide56.json --out .local/wide56-plan

.venv/Scripts/python.exe -X utf8 -m research.krx_lab prepare-v3 --source $source --tables $tables --out $prepared
.venv/Scripts/python.exe -X utf8 -m research.krx_lab certify-v3 --out $evidence
.venv/Scripts/python.exe -X utf8 -m research.krx_lab run-v3 --prepared $prepared --evidence $evidence --out $batch
.venv/Scripts/python.exe -X utf8 -m research.krx_lab report-v3 --batch $batch --out $report
```

`snapshot-v3`는 운영 DB를 읽기 전용으로 조회한다. 가격·달력·기업행사 등 11개 자료 묶음을 한 시점에서 읽고 원본 봉인 해시와 대조한다. PostgreSQL이 만든 JSON 문자열을 그대로 Parquet에 보존하므로 일반 가격표보다 크다. `materialize-v3`는 반복 계산용 열 형식 표를 별도 디렉터리에 만들고, `verify-tables-v3`는 원본과 모든 값을 대조한다. 실패한 추출·변환은 해당 상태로 남기며 같은 경로에 덮어쓰지 않는다.

설정·계획 명령은 `PREPARED_NOT_EXECUTABLE`로 저장한다. `prepare-v3`는 공통 종목군·신호를 준비하되 자료·실행 증거 검사를 건너뛴 수익률 실행 권한을 주지 않는다. `certify-v3`는 현재 코드의 독립 계산 테스트를 기록한다. `run-v3`는 먼저 소규모 실자료 실행과 현금·보유 원장 재생을 확인하고, 통과할 때만 전체 계획으로 진행한다. 점검용 `--limit`는 일부 슬롯만 실행해 나머지를 미실행으로 남긴다. `report-v3`는 저장된 배치 결과를 읽는다.

두 실험을 별도 작업으로 실행할 때는 아래 형식을 쓴다. 각각 1,232개를 마친 뒤에만 합칠 수 있다. 합치기 도구는 입력·코드·실행 번호·파일과 저장된 장부·지표를 다시 검증하며, 실패한 결과를 덮어쓰거나 지우지 않는다.

```powershell
$basicBatch = 'C:/path/to/new-basic-batch'
$wideBatch = 'C:/path/to/new-wide-batch'
$combinedBatch = 'C:/path/to/new-combined-batch'
.venv/Scripts/python.exe -X utf8 -m research.krx_lab run-v3 --prepared $prepared --evidence $evidence --out $basicBatch --family basic
.venv/Scripts/python.exe -X utf8 -m research.krx_lab run-v3 --prepared $prepared --evidence $evidence --out $wideBatch --family wide
.venv/Scripts/python.exe -X utf8 -m scripts.research.merge_v3_batches --basic $basicBatch --wide $wideBatch --out $combinedBatch
.venv/Scripts/python.exe -X utf8 -m research.krx_lab report-v3 --batch $combinedBatch --out $report
.venv/Scripts/python.exe -X utf8 -m scripts.research.chart_v3_comparison --batch $combinedBatch --out C:/path/to/new-charts
```

## 검증과 완료 범위

관련 테스트는 기존 신호 불변성, 미래 가격을 사용하지 않는 계산, 당일 거래량을 뺀 평균, 업종 제한 해제, 넓은 손절에 따른 수량 감소, 스냅샷 변조·추출 실패, 기존 파일 보존을 확인한다. v3 테스트는 날짜별 호가·세금·결제, 주문 불가 봉, 미해결 보유 사건 차단과 원장 재생을 검증한다. 독립 검토자는 원본 봉인 SQL과 해시 규칙을 대조했다. 최종 실행 건수와 실제 추출 결과는 [작업 WBS](real-backtest-v3-execution-wbs-2026-09-21.md)에 기록한다.

입력·독립 계산 검증과 소규모 실자료·원장 대조는 완료했다. 전체 배치·저장 장부 재검증·보고서·그림·최종 독립 검토까지 완료했다. 연구 회귀는 530개 통과했다. 전체 실행에서는 `--family basic`과 `--family wide`로 실험을 나눠 각각 작업자 하나씩 실행할 수 있다. 각 실험은 1,232개이며, 최종 비교는 양쪽의 입력·코드·파일·장부를 대조한 뒤 합친 결과로 한다. 보유 중 원가격 평가나 기업행사를 확정할 수 없으면 해당 실행은 `BLOCKED`가 되고 수익률을 내지 않는다.
