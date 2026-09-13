# 국내주식 기술전략: 백테스트 실행부터 뉴스 결합 자동매매까지

> **2026-09-13 구현 후속:** 최대 1개월·TP/SL·공동 1억 계좌를 지원하는 새 연구 엔진과 실제 DB 실행 판정은 [최신 구현 안내](backtest-lab/implementation-and-results-2026-09-13.md)를 따른다. 아래 기존 예제는 단일종목 기초 검증용이다.
> **최신 요구 기준:** [Backtest Lab 설계 패키지](backtest-lab/README.md)가 우선한다. 최대 보유는 달력 1개월, 매수 전 익절·손절 가격 지정, 초기 1억 원·외부 입출금0·이익 재투자이며 별도 여유자금 1~2억 원은 제외한다. 기존 2~5일 중심 해석은 폐기했고 종목 수 확대와 매수금액 확대는 비교 후 결정한다. 현재 단계는 기술전략 일괄 연구 프로그램의 문서 설계다.

**2026-09-13 후속 갱신:** `ssh home`과 PostgreSQL 접속이 정상화됐다. 14:12 KST 읽기 전용 집계는 **8,789,127행·5,011종목, 2015-01-02~2026-09-10**이다. 종가 0인 1,201행과 가격 조정·거래 상태 확인 과제가 남아 있어 연결 성공을 데이터 인수 완료로 해석하지 않는다.

**사용자의 최종 방향:** 실시간 조건검색 → 기존 분석을 재활용한 AI 뉴스 검토 → 모의 매수 → 체결분에 목표가 매도, 최대 약 20종목·달력 1개월 이내의 스윙 순환매다. 월평균 1,000만 원 목표의 필요 투자금·도식·추가 설계는 [자동매매 구조와 자금 계획](capital-and-system-design.md)에 정리했다. 기존 6개 후보·10봉 청산 코드는 비교 기준선이며 이 목표 시스템 전체를 구현한 것은 아니다.

전체 시스템은 [구조·자금 계획](capital-and-system-design.md), 실제 실행은 이 문서 3~5절, AI·주문은 [프롬프트·분석 저장·주문 흐름](paper-live-news-roadmap.md), 증권사 선택은 [조건검색 지원 차이](broker-condition-integration.md) 순서로 읽는다.

**목적:** 2015-01-02부터 PostgreSQL에 적재한 국내주식 일봉으로 무엇을 실험하고, 어떤 명령으로 결과를 확인하며, 언제 자동 모의투자·실전투자로 넘어갈지 정한다. **권장안은 현재 vectorbt로 3개 전략군·6개 후보를 먼저 비교하고, 선정한 전략에 별도의 증권사 주문·위험관리 계층을 붙이는 것이다.** 뉴스 판단을 추가한 버전은 별도 전략으로 취급해 기술전략 단독 버전과 모의투자에서 비교한다.

이 문서는 2026-09-13 기준 실행 안내와 개발 설계다. 실제 종목의 수익성, HTS 조건 일치, 모의·실전 주문 성공을 검증한 보고서가 아니다. 제공한 실행 예제는 **독립 단일종목·조정가격 연구 모형**이다. 공동 계좌, 정수 주수, 기업행사, 거래정지·호가 체결까지 구현한 운용 엔진과 구분한다. 초기 투자금은 1억 원으로 확인됐으며 허용 손실·증권사·최종 종목은 미정이다.

**먼저 할 일:** 아래 3절의 환경 확인과 합성 데이터 실행으로 명령을 익힌다. 이어 4절에서 DB 가격 의미와 거래일을 확인한 뒤, 제한을 명시한 단일종목 연구를 실행한다. 본 성과 검증과 실전 전환은 7~9절의 조건을 충족한 후 별도로 결정한다.

## 1. 전체 흐름과 읽는 순서

전략 후보와 실행 범위를 먼저 이해하고 명령을 실행한 뒤, 결과 해석과 전환 조건을 읽으면 된다. 뉴스·주문 설계와 오픈소스 비교는 별도 문서로 분리했다.

| 순서 | 답하는 질문 | 읽을 내용 / 결과물 |
| --- | --- | --- |
| 1 | 무엇을 비교하는가 | 2절: 최초 6개 후보, 후속 전략군 |
| 2 | 지금 무엇을 실행하는가 | 3절: 환경·합성 데이터·회귀 검사 |
| 3 | PostgreSQL 데이터를 어떻게 쓰는가 | 4절: 읽기 전용 점검·단일종목 추출 |
| 4 | 어떤 명령으로 실험하는가 | 5절: 후보·비용·기간·체결 지연 비교 |
| 5 | 어떤 결과를 믿고 선택하는가 | 6~7절: 장부 확인·시간 분리·편향·선정 기준 |
| 6 | 자동매매까지 무엇을 더 만드는가 | 8~9절 및 [모의·실전·뉴스 설계](paper-live-news-roadmap.md) |
| 7 | 다른 오픈소스로 바꾸어야 하는가 | [GitHub 대안 비교](open-source-comparison-2026-09-13.md) |

기존 [실험 명세](experiment-spec.md)는 역사 유니버스와 공동 계좌를 포함한 본 연구의 기준이다. 아래 작은 실행 예제는 그중 신호 정의와 시간 지연을 확인하는 출발점이며 전체 명세를 구현한 프로그램이 아니다.

## 2. 먼저 비교할 전략과 나중에 추가할 전략

### 2.1 최초 6개 후보: 진입 신호만 바꾸고 나머지는 동일하게

추천 순서는 추세 교차 → 고점 돌파 → 상승 추세 중 되돌림이다. 추세 지속과 평균 회귀라는 서로 다른 가설을 먼저 비교하면, 유사한 지표 수십 개를 무작정 탐색하는 것보다 차이를 해석하기 쉽다. 아래 숫자는 연구 시작값이며 최적값이나 특정 종목의 매수 추천이 아니다.

`t`는 확정된 일봉, `C`는 종가, `V`는 거래량이다. `SMA_n`은 현재 봉을 포함한 n개 봉의 단순이동평균이다. 모든 후보에 `V(t-1) >= 100,000` 필터를 동일하게 적용한다. 가격이 다른 종목의 10만 주가 같은 유동성을 의미하지는 않는다.

| 전략 ID / 파라미터 | t 마감 후 매수 후보 조건 | 확인하려는 가설 | 주로 확인할 실패 양상 |
| --- | --- | --- | --- |
| T1 / 5 | 전봉 SMA5 < SMA20, 현재 SMA5 > SMA20 | 빠른 추세 전환 이후 상승 지속 | 횡보장에서 잦은 가짜 교차와 비용 |
| T1 / 10 | 전봉 SMA10 < SMA20, 현재 SMA10 > SMA20 | 더 느린 교차가 불필요한 매매를 줄이는가 | 신호가 늦어 수익 구간을 놓침 |
| T2 / 20 | C(t) > 직전 20봉 종가의 최댓값 | 단기 고점 돌파의 지속 | 돌파 다음 날 갭 상승·실패 |
| T2 / 60 | C(t) > 직전 60봉 종가의 최댓값 | 중기 돌파가 더 안정적인가 | 적은 거래 수, 강세장 집중 |
| T3 / 3 | C(t) > SMA60(t), 3봉 수익률 ≤ -3% | 상승 추세 내 단기 하락의 회복 | 하락 추세 전환을 눌림으로 오판 |
| T3 / 5 | C(t) > SMA60(t), 3봉 수익률 ≤ -5% | 깊은 되돌림의 보상이 더 큰가 | 급락 뉴스·장기 손실 위험 |

T1의 등호는 교차로 세지 않는다. T2의 최댓값에 당일 종가는 포함하지 않는다. T3의 3봉 수익률은 `C(t)/C(t-3)-1`이다. 키움 최고종가·교차 항목의 경계가 이 정의와 같은지는 [HTS 대조 준비](hts-comparison-ready-2026-09-12.md)로 별도 확인한다. HTS 조건검색을 쓰지 않는 Python 전용 연구는 정의를 고정해 진행할 수 있지만 HTS 호환으로 부르지 않는다.

**공통 매매:** 신호 다음 관측봉 시가 진입, 진입 뒤 10개 봉 간격이 지난 시가 청산, 보유 중 추가 매수 없음, 청산일 재진입 없음, 매수 포지션만 허용한다. 공식 거래일과 입력 봉이 일치할 때만 이를 다음 거래일·10거래일로 해석한다. 마지막 날 보유 포지션은 종가 평가하며 가상의 강제 매도를 넣지 않는다.

### 2.2 후속 후보: 첫 비교를 끝낸 다음 한 번에 하나씩

아래는 아직 실행 예제에 구현하지 않은 추가 연구안이다. 후보마다 거래량·추세·청산 조건을 동시에 최적화하면 어떤 요소가 효과를 냈는지 알기 어렵다.

| 추가 전략 | 사전 고정할 규칙의 예 | 필요한 추가 확인 |
| --- | --- | --- |
| RSI 되돌림 | 14봉 RSI < 30, 종가 > SMA120; RSI > 50의 다음 시가 또는 10봉 청산 | Wilder 평활/초기값, HTS 계산 차이; 단순평균 RSI와 혼용 금지 |
| 볼린저 밴드 회귀 | 20봉 평균-2×표준편차 아래 종가; 중심선 회복 다음 시가 청산 | 표준편차 ddof, 하락장에서의 누적 손실 |
| MACD 추세 | EMA12-EMA26이 EMA9 신호선 상향 교차 | EMA 초기화·충분한 준비 기간, SMA 전략 대비 추가 효과 |
| 거래량 확인 돌파 | T2 + 당일 거래량 > 직전 20봉 평균의 2배 | 확정 일봉만 사용, 조정 거래량·거래대금 단위 |
| 상대 모멘텀 순위 | 시점별 유니버스의 6/12개월 수익률 순위, 월간 교체 | 역사 유니버스·공동 자금·리밸런싱·상폐 자료 필수 |
| 시장 국면 필터 | 시장 지수 > 지수 SMA200일 때만 신규 진입 | 지수 데이터·배당 기준; 위험 감소와 현금 비중 효과 분리 |
| 변동성 기반 청산 | ATR 기반 보유 위험·청산 가격 | 일봉 내 손절/익절 선후는 알 수 없음; 장중 자료 또는 보수적 체결 모형 |

후속 전략은 기존 6개와 별도 실험 버전으로 등록한다. 차트에서 잘 맞는 값을 골라 같은 구간 성과를 검증 결과로 보고하지 않는다.

## 3. 바로 실행: 환경 확인과 합성 데이터

모든 명령은 **저장소 루트의 PowerShell**에서 실행한다. 이 저장소 자체에 국내주식용 `vectorbt backtest` CLI가 있는 것은 아니다. 이번에 첨부한 [research_backtest.py](research_backtest.py)가 아래 연구용 명령을 제공한다. 증권사 접속이나 주문 기능은 없다.

### 3.1 기존 가상환경을 먼저 재사용

```powershell
.venv\Scripts\python.exe -c "import sys, vectorbt, plotly; print(sys.version); print(vectorbt.__version__, plotly.__version__)"
.venv\Scripts\python.exe docs/strategy-research/research_backtest.py --help
```

이번 작업에서 기존 환경의 Python 3.14.6, vectorbt 1.1.0, Plotly 6.9.0 import를 확인했다. 이 버전은 확인 당시 설치 상태이며 저장소의 영구 고정 요구사항이 아니다. 새 환경이 필요할 때만 아래를 실행한다. 기존 `.venv`를 다시 생성하지 않는다.

```powershell
uv python install 3.11
uv venv --python 3.11
uv pip install --python .venv -e ".[test]" "plotly<7"
```

Plotly 상한은 기존 호환 문제 기록을 고려한 연구 환경 우회안이며 `pyproject.toml`은 수정하지 않았다. 새 설치·다른 Python 조합을 이번에 재검증한 것은 아니다. Rust는 최초 신호 검증의 필수조건이 아니며 예제는 Numba 엔진을 사용한다.

### 3.2 합성 데이터로 명령과 결과 파일 확인

```powershell
$researchRoot = Join-Path $env:LOCALAPPDATA 'vectorbt-research'
New-Item -ItemType Directory -Force -Path $researchRoot | Out-Null
$demoRun = Join-Path $researchRoot ('demo-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
.venv\Scripts\python.exe docs/strategy-research/research_backtest.py --demo --strategy all --cost-bps 30 --out $demoRun
if ($LASTEXITCODE -ne 0) { throw '합성 실행 실패' }
Get-Content -Encoding UTF8 (Join-Path $demoRun 'manifest.json')
Import-Csv (Join-Path $demoRun 'summary.csv') | Format-Table -AutoSize
```

이 결과는 가상의 가격으로 만든 프로그램 동작 확인이다. 실제 종목 추천·과거 수익·미래 기대수익의 근거가 아니다. 기본 실행은 61개 봉을 준비 자료로 사용한 뒤 모든 후보와 매수 후 보유 비교를 같은 날 시작한다. 출력은 저장소 밖에 두며 같은 실행 폴더를 재사용하지 않는다.

```powershell
.venv\Scripts\python.exe -m pytest docs/strategy-research/test_research_backtest.py -q
.venv\Scripts\python.exe -X utf8 docs/strategy-research/verify_evidence.py
.venv\Scripts\python.exe -X utf8 docs/strategy-research/verify_followup_evidence.py
```

첫 명령은 새 예제의 회귀 검사, 나머지는 **이미 저장된 과거 증거의 검산**이다. 마지막 두 명령이 PASS여도 현재 DB 품질이나 전략 수익성이 확인된 것은 아니다.

## 4. PostgreSQL: 재수집 없이 점검하고 한 종목부터 추출

### 4.1 현재 알려진 상태와 이번 확인의 한계

이전에는 SSH 시간 초과로 조회하지 못했지만, 전원이 켜진 뒤 **13:07 KST `ssh home` → `ted-server` → `kiwoom-db/kiwoom_db` 읽기 전용 조회가 성공**했다. 후속 14:12 KST 집계에서도 연결·조회가 정상이다. 현재 가격은 `adjusted=true` 8,789,127행·5,011종목이며 2015-01-02~2026-09-10이다. [현재 집계](evidence/db-current-status-2026-09-13.json)

접속과 데이터 인수는 다르다. 종가 0인 행은 1,201개, OHLC 중 하나 이상이 0 이하인 행은 89,239개·530종목, 거래량 0은 전체에서 332,193개다. 집합이 서로 겹치므로 합산하지 않는다. 비양수 OHLC 중 88,038개는 시가·고가·저가가 0이고 종가는 양수다. 정상 거래정지 표기인지 변환 문제인지 이 집계만으로 확정하지 않는다. 원본을 삭제하거나 0을 채워 통과시키지 않는다. [진단 원문](evidence/db-reconnected-2026-09-13.txt)

기존 9월 12일 8,202,637행은 과거 관측이다. 가격 조정 계보·기업행사·공식 달력·역사 유니버스 인수는 별도 확인이 필요하며 실제 수익률 실행은 아직 하지 않았다. 2026-09-10 이후 적재가 필요한지는 거래일·수집 완료 기록과 대조한다.

아래 상세 검사는 서버 가동 중 재현한다. 이번에는 `05-nonpositive-diagnostic.sql`과 [10-current-status.sql](sql/10-current-status.sql)의 실시간 조회를 수행했으며 아래 모든 검사를 재실행한 것은 아니다. 파일은 읽기 전용 트랜잭션과 조회 제한시간을 사용한다.

```powershell
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$auditDir = Join-Path $researchRoot ('audit-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $auditDir | Out-Null
foreach ($check in @('01-schema','02-data-audit','04-backfill-check','05-nonpositive-diagnostic','06-price-provenance')) {
    $auditText = Get-Content -Raw -Encoding UTF8 "docs/strategy-research/sql/$check.sql" |
        ssh -o BatchMode=yes -o ConnectTimeout=8 home "docker exec -i -e PGCLIENTENCODING=UTF8 kiwoom-db psql -X -v ON_ERROR_STOP=1 -U kiwoom -d kiwoom_db -P pager=off" 2>&1
    $auditCode = $LASTEXITCODE
    $auditText | Set-Content -Encoding UTF8 (Join-Path $auditDir "$check.txt")
    if ($auditCode -ne 0) { throw "검사 실패: $check ($auditCode)" }
}
```

통과 여부는 행 수만으로 결정하지 않는다. [인수 기준](backfill-contract.md)에 따라 중복·가격 관계·단위·조정 방식, 공식 거래일과 누락, 당시 상장·폐지·시장 분류를 구분한다. 0원·정지일을 SQL에서 조용히 제거하면 보유기간과 체결 가능성이 달라진다. 원본은 보존하고 원인·상태·처리 규칙을 남긴다.

### 4.2 단일종목 추출 명령

다음은 삼성전자 코드 `005930`을 이용한 **형식 예시**이며 종목 선정이나 매수 추천이 아니다. 먼저 스키마 조회에서 아래 컬럼과 `adjusted` 의미가 같은지 확인한다. 단일 코드가 복수 영구 종목 ID를 가리키는 경우 이 SQL 대신 기간별 ID 매핑을 사용해야 한다.

```powershell
$extractDir = Join-Path $researchRoot ('extract-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $extractDir | Out-Null
$csvPath = Join-Path $extractDir '005930-adjusted.csv'
$exportError = Join-Path $extractDir 'export.stderr.txt'
$csvLines = Get-Content -Raw -Encoding UTF8 docs/strategy-research/sql/09-export-single-stock.sql |
    ssh -o BatchMode=yes -o ConnectTimeout=8 home "docker exec -i -e PGCLIENTENCODING=UTF8 kiwoom-db psql -X -q -v ON_ERROR_STOP=1 -v stock_code=005930 -v start_date=2015-01-02 -v end_date=2026-09-10 -U kiwoom -d kiwoom_db" 2> $exportError
if ($LASTEXITCODE -ne 0) { throw '추출 실패: export.stderr.txt 확인' }
$csvLines | Set-Content -LiteralPath $csvPath -Encoding utf8
Get-FileHash -Algorithm SHA256 -LiteralPath $csvPath
```

`end_date`는 데이터 확정 여부를 확인한 마지막 거래일로 바꾼다. 위 날짜는 현재 집계의 마지막 날짜이며 전체 종목의 적재 완전성을 주장하지 않는다. 이 추출 SQL은 실제 DB에서 실행해 삼성전자 2,870행을 반환했으며 [추출 기록](evidence/db-export-verified-2026-09-13.json)에 남겼다. 추출 성공은 가격 의미의 검증과 다르고 수익률은 계산하지 않았다. 접속 실패 시 결과를 연구 입력으로 사용하지 않는다. SQL은 0·NULL·0거래량을 필터링하지 않는다.

입력 형식은 `date,open,high,low,close,volume`의 일자 오름차순 단일종목 데이터다. 종목코드·가격 종류는 파일명과 별도 추출 기록에 보존한다. 필요한 기록은 추출 시각, 종목·영구 ID, SQL 해시, 데이터 해시, 출처·수정주가 생성 방식, 배당 포함 여부, 거래일 검증 결과다. 비밀번호와 토큰은 기록하지 않는다.

**작은 실행 예제의 의도적 제한:** 중복 날짜, 결측·0 이하 OHLC, 가격 관계 위반, 0 이하 거래량 등 지원하지 않는 입력은 중단한다. 정상 거래정지도 이 예제로는 처리하지 못할 수 있다. 통과를 위해 행을 삭제하거나 가격을 채우지 말고, 상태 이력과 비체결·평가 처리를 지원하는 본 연구 실행기를 확장한다. CSV에 누락 거래일이 없는지는 외부 공식 달력으로 따로 검증해야 한다.

## 5. 실제 데이터 연구 명령과 실험 순서

### 5.1 첫 실행은 개발 구간의 6개 후보만

아래 명령은 4절의 가격 조정 의미·입력 점검을 마친 뒤 실행한다. `--price-semantics-reviewed`는 검토를 수행했다는 사용자의 명시적 표시이며 자동 인수 판정이나 HTS 일치 인증이 아니다. 실제 DB 성과 실행은 이번 문서 작성 중 수행하지 않았다.

```powershell
$runDir = Join-Path $researchRoot ('dev-six-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
.venv\Scripts\python.exe docs/strategy-research/research_backtest.py --input $csvPath --price-semantics-reviewed --strategy all --start 2016-01-01 --end 2019-12-31 --cost-bps 30 --delay 1 --out $runDir
if ($LASTEXITCODE -ne 0) { throw '연구 실행 실패' }
Import-Csv (Join-Path $runDir 'summary.csv') | Format-Table -AutoSize
```

2015년 입력은 지표 준비에 쓰고 첫 간단한 실행의 성과 시작을 2016년으로 잡았다. 원래 [실험 명세](experiment-spec.md)의 2015~2019 개발 구간 전체와는 다르므로 같은 결과라고 비교하지 않는다. 전체 구간 연구에서는 최소 61개 유효 봉 이후부터 정확한 성과 시작일을 정한다. `--start` 이전 입력을 잘라낸 CSV를 사용하면 준비 자료가 사라진다.

한 전략군만 재현하려면 `--strategy T1`, `T2`, `T3`로 바꾼다. 각 군의 두 후보는 모두 실행하며 수익이 좋은 파라미터만 남기지 않는다. 모든 비교에서 동일 CSV·기간·비용·체결 지연을 사용한다.

### 5.2 비용 민감도: 6개 후보 × 3개 시나리오

```powershell
foreach ($bps in @(10,30,50)) {
    $costRun = Join-Path $researchRoot ("cost-$bps-" + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
    .venv\Scripts\python.exe docs/strategy-research/research_backtest.py --input $csvPath --price-semantics-reviewed --strategy all --start 2016-01-01 --end 2019-12-31 --cost-bps $bps --delay 1 --out $costRun
    if ($LASTEXITCODE -ne 0) { throw "비용 시나리오 실패: $bps" }
}
```

1bp는 0.01%다. 편도 10/30/50bp는 수수료·세금·체결 불리함을 묶은 **가상의 총비용 시나리오**이며 실제 세율이나 증권사 요율이 아니다. 예제는 이를 `fees`에만 넣고 별도 슬리피지를 중복 적용하지 않는다. 본 운용 검증은 날짜별 매수·매도 수수료, 매도 세금, 슬리피지를 분리해야 한다.

### 5.3 체결이 하루 더 늦어지는 경우

```powershell
$delayRun = Join-Path $researchRoot ('delay2-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
.venv\Scripts\python.exe docs/strategy-research/research_backtest.py --input $csvPath --price-semantics-reviewed --strategy all --start 2016-01-01 --end 2019-12-31 --cost-bps 30 --delay 2 --out $delayRun
if ($LASTEXITCODE -ne 0) { throw '체결 지연 검사 실패' }
```

기준의 18개 후보·비용 조합에 지연 6개를 더하면 24개 전략 실행이다. 결과 파일의 `buyhold_` 접두사 컬럼은 같은 종목의 매수 후 보유 비교값이며 추가 전략 후보가 아니다. 하루 지연만으로 성과가 사라지는 후보는 주문 지연에 민감하다는 해석이며 유리한 실행만 골라 보고하지 않는다.

### 5.4 시간 분리 평가: 고정 후 다음 연도 확인

개발 구간에서 정의를 고정한 다음에만 아래를 실행한다. `--start/--end`는 평가 구간을 지정할 뿐 자동 학습·파라미터 선택·워크포워드 구현을 뜻하지 않는다.

```powershell
foreach ($year in @(2020,2021,2022,2023)) {
    $yearRun = Join-Path $researchRoot ("year-$year-" + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
    .venv\Scripts\python.exe docs/strategy-research/research_backtest.py --input $csvPath --price-semantics-reviewed --strategy all --start "$year-01-01" --end "$year-12-31" --cost-bps 30 --delay 1 --out $yearRun
    if ($LASTEXITCODE -ne 0) { throw "연도 평가 실패: $year" }
}
```

매년 새 독립 계좌로 시작하며 이전 구간 포지션을 이어받지 않는다. 평가 시작 전의 확정 신호가 지정된 지연 뒤 첫 평가일에 도달하면 첫날 신규 진입은 가능하며, 시작 전에 체결된 포지션을 가져오는 것은 아니다. 연도별 결과를 실제 연속 계좌처럼 합성하지 않는다. 후보 선택이 필요하면 평가 연도 직전까지의 자료만 이용해 기존 명세의 사전 선택 규칙을 적용하고 선택 기록을 따로 저장한다.

기존 명세의 2024-01-01~2026-09-09는 잠금 구간 제안이다. 이미 그 구간을 보고 규칙을 고쳤다면 더 이상 미사용 검증 자료가 아니다. 잠금 구간을 자동 반복문에 넣지 않았으며 전략·시도 기록을 고정하고 한 번 열어 평가한다. 이후 수정은 새 버전과 이후 전진 자료로 검증한다.

## 6. 결과 파일을 읽는 방법

**요약 수익률보다 먼저 주문 장부의 시간을 확인한다.** 동일 신호에 대해 데이터 → 신호 → 주문 → 평가를 재현할 수 있어야 전략 차이를 해석할 수 있다.

| 파일 | 확인할 내용 | 해석의 한계 |
| --- | --- | --- |
| `manifest.json` | 합성/실제 입력, 데이터·코드 해시, 버전, 조건·기간·비용·지연 | 해시 일치는 데이터 진실성이나 거래 가능성 증명이 아님 |
| `summary.csv` | 후보별 수익·CAGR·Sharpe·최대낙폭·거래 수·비용, 매수 후 보유 비교 | 0거래·작은 표본·미청산 포지션도 함께 확인 |
| `equity.csv` | 날짜별 정규화 자산과 낙폭 구간 | 종목별 독립 계좌이며 원화 실계좌 아님 |
| `orders.csv` | 시가 체결 시점·가격·수량·비용 | 체결 모형이 만든 장부이며 실제 증권사 체결이 아님 |

```powershell
Get-Content -Encoding UTF8 (Join-Path $runDir 'manifest.json')
Import-Csv (Join-Path $runDir 'summary.csv') | Format-List
Import-Csv (Join-Path $runDir 'orders.csv') | Select-Object -First 12 | Format-Table -AutoSize
```

대표 거래를 선택해 전일까지의 지표로 신호를 재계산하고, 당일 종가로 당일 시가에 매수하지 않았는지 확인한다. 진입 시가에서 10봉 뒤 시가 청산인지, 비용이 양방향으로 반영됐는지, 마지막 보유 포지션이 닫힌 거래 수에 섞이지 않았는지 확인한다. 공식 vectorbt 문서도 종가 기반 신호를 뒤로 이동하고 신호 이후 가격을 사용하도록 설명한다. [Portfolio API](https://vectorbt.dev/api/portfolio/base/)

지표 정의는 다음처럼 읽는다. 최종 수익률은 초기 가치 대비 기말 평가액 변화, CAGR은 실제 경과일 기준 연복리, Sharpe는 일별 수익률을 252거래일로 연환산한 위험 대비 수익 지표다. 최대낙폭은 **초기 가치 1도 포함**한 최고점 대비 하락이다. 연환산 수익률은 짧은 구간에서 과장될 수 있고 252일 가정은 입력 누락을 해결하지 않는다.

매수 후 보유 비교는 같은 종목·같은 기간의 첫 시가 매수와 기말 종가 평가, 동일 비용 가정으로 맞춘다. 시장 전체 대비 초과 성과는 별도로 KOSPI/KOSDAQ 또는 거래 가능한 기준상품, 같은 배당 기준으로 확인해야 한다. 단일종목의 분수 단위 연구 결과를 그대로 실제 원화 수익으로 환산하지 않는다.

## 7. 좋은 전략을 고르는 기준과 예제 다음의 개발

### 7.1 선정은 수익률 1위가 아니라 재현성과 견고함을 포함

권장 연구 통과 기준은 시간 분리 비용 차감 성과, 네 평가 연도 중 최소 세 해의 양의 수익, 높은 비용과 추가 지연에서도 유지되는 효과다. 이는 기존 명세의 제안이며 수익 보장이나 실전 승인 기준은 아니다. 독립 단일종목 예제만으로 전체 시장 기준을 통과했다고 판정하지 않는다.

함께 볼 항목은 거래 수, 연도·국면별 편차, 최대낙폭과 회복기간, 시장 노출과 현금 비중, 회전율, 한 종목·한 해의 기여 집중이다. 100건 미만이면 근거 부족 표시를 권장하지만 100건 이상이 통계적 유의성을 보장하지 않는다. 인접 파라미터가 모두 무너지고 한 값만 좋으면 과최적화를 의심한다. 시도한 후보·필터·비용 시나리오 전체를 보존한다.

종목을 최근 성과를 보고 선정한 다음 그 종목의 2015년 이후 성과를 제시하면 종목 선택 자체에 미래정보가 들어갈 수 있다. 현재 선정 단일종목 연구라는 범위를 표시하거나 당시 선택 가능한 종목 집합을 복원한다. 현재 시가총액·현재 상장 종목 목록으로 역사 유니버스를 대체하지 않는다.

### 7.2 본 연구 실행기에 추가할 사항

첨부 예제는 아래 기능을 제공하지 않는다. PostgreSQL 전체 종목을 한 번에 넣거나 종목별 자산을 더하는 방식으로 이를 대신하지 않는다.

| 추가 구현 | 필요한 이유 / 검증 방법 |
| --- | --- |
| 시점별 유니버스·공식 달력 | 상장·상폐·시장 이동·결측을 구분하고 기대 종목일 검산 |
| 기업행사와 원가격·정수 주수 | 분할·배당·합병·권리락의 현금/주식 수를 장부로 대조 |
| 공동 자금·최대 약 20종목·후보 배정 | 보유·미체결 매수 예약의 합집합 상한, 현금 부족, 후보 초과 검사. 기존 명세의 10종목은 과거 기준선 |
| 체결 가능성·참여율·정지 | 불가능한 청산의 연기, 미체결·잔존가치·평가 지연 기록 |
| 일자별 실제 비용 | 계좌 수수료 및 해당 연도 세금·호가 규칙 적용 |
| 전체 실험 등록과 구간 선택 | 데이터 manifest·시도 이력·잠금 구간 사용을 자동 기록 |
| 성과 보고 확대 | 시장 비교, 노출·회전율·회복기간·연도별/종목별 기여·거절 장부 |

과거 뉴스 자료 없이 오늘의 검색 결과를 2015년 투자 판단에 붙이는 것은 허용하지 않는다. 뉴스가 아직 없는 단계에서는 기술전략만 백테스트하고, 뉴스 추가 효과는 수집을 시작한 뒤 전진 검증한다.

## 8. 모의투자 → 뉴스 결합 → 실전투자의 단계

진행 순서는 **기술전략 선정 → 주문 없는 실시간 신호 기록 → 증권사 모의계좌 연결 → 뉴스 추가 버전과 병행 비교 → 제한된 실전**이다. 뉴스만 붙이면 백테스트에서 검증한 전략이 그대로 유지되는 것은 아니다. 종목 선택·진입 시간·가격·수량 중 하나라도 바뀌면 새 전략 버전이다.

| 단계 | 만들어야 할 결과물 | 다음 단계 판단 |
| --- | --- | --- |
| 연구 | 고정 신호·데이터·비용·시간 분리 결과 | 데이터와 체결 가정이 설명되고 기준 성과를 재현 |
| 무주문 관찰 | 확정 일봉 신호, 주문 예정안, 실제 이후 가격, 데이터 지연 기록 | 재시작·누락·신호 시간 일치 확인 |
| 기술전략 모의 | 주문·부분체결·취소·잔고 대조, 모의 성과 | 주문 장애 테스트 통과 및 사전에 정한 기간·거래 수 확보 |
| 뉴스 결합 모의 | 기술 단독 A / 기술+뉴스 B, 변경 사유·출처·시간·가격 버전 | 같은 비용·노출 조건에서 뉴스 추가 효과와 위험을 평가 |
| 실전 소규모 | 확정한 자금·손실 한도·킬스위치, 실제 체결 슬리피지 | 한도 내 운영과 모의 대비 차이를 확인한 뒤 확대 여부 별도 결정 |

**뉴스 역할:** 사용자 목표 시스템에서는 AI가 기존 분석과 최신 뉴스로 매수 승인·보류·거절 및 목표 범위 적절성을 검토한다. 위험 엔진은 AI 승인 후에도 가격·수량·한도를 검증하며, 기술 단독 버전을 비교 기준으로 보존한다. 기술적 청산과 강제 위험 청산을 긍정 기사 때문에 무효화하지 않는다. 가격은 검증된 호가·시장 규칙과 사전 가격 정책으로 산정하고 뉴스 모델의 임의 숫자를 바로 주문에 쓰지 않는다.

상세한 뉴스 시간 필드, 출처·상충 기사 처리, 매수·매도 가격 정책, 주문 상태 전이, 모의·실전 자격조건은 [모의·실전·뉴스 로드맵](paper-live-news-roadmap.md)에 정리했다. 그 문서의 프로그램 구성은 **추후 개발 설계**이며 현재 실행 가능한 주문 CLI가 아니다.

## 9. 오픈소스 선택과 다음 작업의 우선순위

도구의 유용성은 목적에 따라 다르다. 현재 저장소와 데이터 투자를 살려 대량 후보 비교는 vectorbt로 시작하는 편이 합리적이다. 이벤트 단위 체결 재현이나 실시간 주문 통합이 핵심이 되면 다른 엔진 또는 증권사 어댑터를 보완한다. 엔진을 교체해도 한국 시장 데이터 품질·뉴스 시점·증권사 주문 상태 문제는 별도로 해결해야 한다.

[GitHub 비교 문서](open-source-comparison-2026-09-13.md)는 공식 저장소·문서·라이선스를 기준으로 유지/보완/전환 판단을 제공한다. 별 수와 기능 목록을 실거래 수익성의 증거로 쓰지 않았으며 현재 로컬 Rust 확장과 upstream·유료 PRO의 기능도 구분해서 읽는다.

다음 작업은 아래 순서가 적절하다.

1. 정상 연결된 DB의 현재 가격 품질·조정 정의·공식 거래일 대조를 완료한다. 2015년부터의 재수집을 중복 수행하지 않는다.
2. 제한을 통과한 단일종목으로 6개 후보 명령을 재현하고 주문 장부를 확인한다.
3. 역사 유니버스·공동 계좌·기업행사·체결 모형을 추가해 기존 실험 명세의 본 연구를 구현한다.
4. 기간 분리 결과로 전략을 고정하고 증권사 및 모의투자 인수 기준을 결정한다.
5. 종목별 뉴스 기록과 기술 단독/뉴스 결합의 병행 모의투자를 구현한다.
6. 실전 자본·허용 낙폭·일일 손실·종목 비중·운영 가동시간을 확정한 뒤 실전 연결 여부를 결정한다.

## 10. 검증 기록과 근거

이 문서의 사실은 로컬 코드·실행 결과, 사용자의 적재 범위 설명, 기존 저장된 관측, 공개 공식 출처를 구분했다. 후속 작업에서 SSH·DB 연결과 가격 집계, 단일종목 추출을 실측했다. 종가 0인 1,201행은 여전히 관측됐으며 원인과 조정 계보를 해결한 것은 아니다. 자동매매 프로그램·계좌·주문은 생성하지 않았다.

- 로컬 API·설정: [portfolio/base.py](../../vectorbt/portfolio/base.py), [_engine.py](../../vectorbt/_engine.py), [pyproject.toml](../../pyproject.toml).
- 연구 규칙: [실험 명세](experiment-spec.md), [가격 원인 추적](price-provenance-review-2026-09-12.md), [백필 인수 기준](backfill-contract.md).
- 공개 API 설명: [vectorbt Portfolio](https://vectorbt.dev/api/portfolio/base/). 실제 실행 계약은 이 저장소의 코드와 회귀 결과를 우선한다.
- 추가 출처·라이선스·확인 한계: [오픈소스 비교](open-source-comparison-2026-09-13.md), [뉴스·주문 설계](paper-live-news-roadmap.md).

실행한 검사와 미실행 범위의 최종 목록은 [이번 작업 검증 기록](guide-validation-2026-09-13.md)을 따른다.
