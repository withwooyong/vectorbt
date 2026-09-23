# 시장 200일선 실험의 벤치마크 원천 확인

**판단: 봉인된 v3 KOSPI·KOSDAQ 대표지수는 KRX Open API에서 받은 실제 지수 관측값으로 확인됐다.** 2014-01-02~2023-12-28의 두 지수 각 2,459개 값은 KRX 개장일과 정확히 일치하고, 원천 레코드의 시가·고가·저가·종가와 저장값이 모두 일치한다. 따라서 이번 2015~2023년 후향적 시장 200일 이동평균 실험의 전일 종가 입력으로 사용할 수 있다. 다만 자료는 2026년에 재수집됐으므로 당시 보관된 원응답이나 과거 개정본의 부재까지 증명하지 않는다.

이 디렉터리에는 결과 [evidence.json](evidence.json), 읽기 전용 [SQL](benchmark_provenance.sql), 재실행 [검증 스크립트](verify_benchmark.py)를 둔다. 증거의 `PASS_RETROSPECTIVE`는 벤치마크 원천·범위·수치 검사에 관한 판단이며, 전체 전략 입력이나 실제 매매의 승인을 뜻하지 않는다.

## 판단 근거

| 확인 항목 | 결과 |
| --- | --- |
| 봉인 revision | `2014-2023-v3`, `e95066aa…13c2`; BENCHMARK member 4,918행, `138e3bcc…e96b` |
| 공식 원천 | `KRX_OPEN_API`, `authority_kind=PRIMARY`, KOSPI `idx/kospi_dd_trd`, KOSDAQ `idx/kosdaq_dd_trd`; 응답 상태 전수 200 |
| 기간·달력 | 각 2,459개 개장일, 2014-01-02~2023-12-28; 개장일 누락·추가 0쌍 |
| 수치·연결 | 로컬 원본·정형·운영 DB의 4,918행을 날짜·지수·원천 ID·OHLC로 전수 대조했고 결정적 SHA-256이 일치한다. 운영 DB의 payload SHA 4,918개도 봉인된 로컬 payload member에 모두 존재한다. 비양수 가격·OHLC 순서 오류·원천 OHLC 불일치·식별자 불일치·원천 연결 누락은 모두 0건 |
| 보존 한계 | 전수 `capture_kind=new_observation`, `historical_capture=false`; `published_at` 없음, `available_at`은 2026년 수집 시각 |

신호는 **당일 지수 종가를 그다음 개장일의 신규 매수 판단에만** 사용한다. 위 보존 한계 때문에 이 결과는 공식 지수의 후향적 실험 근거이며, 과거 시점의 원본 응답 보유를 주장하는 근거가 아니다.

## 재현

저장소 루트에서 기존 SSH `home` 설정과 읽기 권한이 있을 때 다음을 실행한다. 스크립트는 로컬 원본·정형 Parquet 및 manifest 해시를 확인하고, 운영 DB에 `REPEATABLE READ READ ONLY` 트랜잭션을 보내 **4,918행을 전수 비교**한 뒤 `ROLLBACK`한다. SQL은 원천 payload 본문을 읽지 않고 각 행의 SHA-256만 반환한다. 인증정보와 원문 payload는 출력하지 않는다.

```powershell
.venv\Scripts\python.exe -X utf8 docs/strategy-research/backtest-lab/extension-benchmark-admission-2026-09-21/verify_benchmark.py `
  --snapshot C:\Users\aeby\vscode\stock\vectorbt-data\krx-v3-20260921-implementation `
  --typed C:\Users\aeby\vscode\stock\vectorbt-data\krx-v3-20260921-tables `
  --out docs/strategy-research/backtest-lab/extension-benchmark-admission-2026-09-21/evidence.json
```

검사 실패 시 스크립트는 예외를 내고 새 증거를 기록하지 않는다. 이 실행에서 생성한 `evidence.json`의 SHA-256은 `57e4f80d8b3e06689cca9ebb8d86a8ba285a22856bc82b52345c4494f38cf5ad`이다. 로컬·운영 DB 공통 행의 SHA-256은 `0dfc4cb9ce6e1bbc075544458d46a7c60e39b1ae4ad1bcb382195803a04cc460`이다. 운영 DB가 바뀌면 다시 확인하고 기존 증거를 현재 상태로 간주하지 않는다.
