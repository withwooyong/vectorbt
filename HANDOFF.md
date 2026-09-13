# 다음 세션 인수인계

> 갱신: 2026-09-13 KST
> 작업 폴더: `C:\Users\aeby\vscode\stock\vectorbt`
> 브랜치: `master` / 원격: `withwooyong/vectorbt`
> 이번 인수 커밋의 부모: `4bb110d`

**현재 판단:** 1억 원·최대 달력 1개월·사전 익절/손절·최대 20종목의 연구 핵심 프로그램을 구현했다. 합성 장부 검증은 통과했지만 **실제 DB 수익률 실행은 데이터 인수에서 BLOCKED, 최종 전략은 NO_SELECTION**이다. 사용자 결정에 따라 미검증 자료의 탐색용 수익률도 실행하지 않는다. 다음 작업은 백필 원천·가격 조정·비정상 봉 원인 확인이며 전략 수익률 최적화가 아니다.

이 문서부터 읽고 [구현·실행 결과](docs/strategy-research/backtest-lab/implementation-and-results-2026-09-13.md), [WBS](docs/strategy-research/backtest-lab/wbs.md), [사용자 확정 결정](docs/strategy-research/backtest-lab/user-decisions-2026-09-13.json)을 확인한다. 전체 조사 문서를 처음부터 다시 읽을 필요는 없다. 이전 인수 기록은 [보관본](docs/strategy-research/handoff-before-lab-2026-09-13.md)에 있다.

## 1. 확정한 사용자 요구와 실행 경계

- 초기 투자금 1억 원, 외부 여유자금 1~2억 원은 계좌·수익률 분모에서 제외. 추가 입출금 없이 재투자한다.
- 보유기간은 최대 **달력 1개월**이다. 5일 또는 고정 20/21거래일로 바꾸지 않는다. 매수 전에 익절·손절 가격을 지정한다.
- 기본 최대 20종목. 고정 20개에서 매수금액 증가와 staged 10→15→20 정책을 비교하되 선정 전 정책을 임의 변경하지 않는다.
- **데이터 검증을 통과한 뒤 정식 비교·선정**한다. 탐색용 수익률 우회 실행을 원하지 않는다.
- 사용자는 **2024년~2026년 9월 자료를 과거 전략 선택·튜닝에 사용한 적 없다고 확인**했다. 이는 사용자 진술이며 독립 감사 결과는 아니다. `2024-01-01~2026-09-10`은 후보·정책 고정과 데이터/현실 비용 검증 전까지 잠금 유지한다.
- 사용자 확인은 별도 결정 JSON에 저장했다. 기존 실험은 코드/설정/데이터 해시를 보존하기 위해 소급 수정하지 않았다. 다음 실험에 이 결정을 반영해야 한다.
- 모의투자·AI 뉴스·증권사 검색식/주문은 후속 범위다. 현재 주문이나 뉴스 AI 호출은 없다. 월 1,000만 원 목표는 수익 보장이거나 위험 한도를 높이는 근거가 아니다.

## 2. 구현과 실제 검증 결과

`research/krx_lab/`에 12개 진입×4개 청산, 사전 가격 계획, 공동 현금·정수주·재투자, 날짜별 체결 순서, vectorbt 장부 재생, SQLite run/attempt, Parquet 장부, 지표·선정 게이트·보고서·CLI를 구현했다. 사용법은 [패키지 README](research/krx_lab/README.md)를 따른다. vectorbt 공개 API·Numba/Rust 제품 커널은 변경하지 않았다.

- 연구 53개 + 기존 단일종목 예제 11개 = **64개 테스트 통과**. 종료 준비에서도 같은 범위를 재검증한다.
- 합성 8종목으로 개발 48개 후보 및 한 후보의 검증 16조합, **64 run 성공**. 실제 성과가 아니다.
- 총 **14,680건 체결·54,716개 일말 장부**를 vectorbt Numba 공동 현금 재생과 대조했다. 새 실험 재실행의 64개 성과 지표도 일치했다.
- 실제 자료 실험은 기본 816슬롯 데이터 차단 + 후속 33슬롯 선행 조건 미충족 = **849슬롯 BLOCKED**. 수익률 849개를 계산한 것이 아니다.
- 실제 4,025종목의 신호 빈도 진단은 완료했다. 원본을 수정하지 않고 진단 사본에서만 비정상 봉을 결측 처리해 날짜 축을 유지했다. 신호 수는 거래 수·수익률이 아니다.
- `ruff`, `compileall`, 문서 링크 검사를 수행했다. 앞선 `git diff --check`는 추적 파일 검사였으며, 종료 시 새 파일까지 staged 검사하니 원본 프롬프트·DB 텍스트의 행끝 공백/빈 끝줄과 report.py의 행끝 공백 1건이 표시됐다. 원문 및 고정 실험의 소스 바이트 해시를 보존해 이번에는 그대로 커밋한다. 기능 오류나 테스트 실패를 숨기는 예외는 아니다. [기계 판독 검증](docs/strategy-research/backtest-lab/implementation-validation-2026-09-13.json)에 증거 경로가 있다.
- 새 연구 테스트가 일반 `pytest tests/`에도 수집되므로 `pyproject.toml`의 test extra에 pyarrow·psutil을 추가했다. 별도 연구 requirements와 같은 범위다.

**미완료:** 정식 EXECUTION_ELIGIBLE 데이터 인수, 역사 원가격/기업행사 정수주 정산, 현실 비용 어댑터, 후속 allocation/realistic-cost/holdout 단계 실행, freeze/finalize, 상세 NAV 대시보드. 현재 성과 배치는 합성 자료만 허용한다. 실제 자료는 추출·품질·신호 진단까지 지원한다. 데이터 파일을 새로 받는 것만으로 남은 소프트웨어가 자동 완성되는 것은 아니다.

## 3. DB와 로컬 산출물

`ssh home`으로 연결했고, DB는 Docker `kiwoom-db`의 `kiwoom_db`다. PostgreSQL은 읽기 전용으로 조회했으며 원본·서비스·백필 프로젝트에 쓰지 않았다. 종료 준비 시 `docker ps`로 caddy/frontend/backend/db 및 kiwoom-app/db **6개 모두 healthy**를 확인했다. 다음 세션에도 실행 상태는 재확인한다.

| 범위 | 결과 |
| --- | --- |
| 15:34 KST 전체 DB 관측 | 8,789,127행·5,011종목, 2015-01-02~2026-09-10, 전부 adjusted=true |
| 이번 스냅샷 | 6,109,214행·4,025종목, 2015-01-02~2023-12-31 요청; 실제 마지막 봉 2023-12-28 |
| 스냅샷 품질 | 키 중복 0, 비정상 OHLCV 72,072행·453종목, 거래량0 211,623행 |
| 공급자 라벨 | KIWOOM 5,564,973 / KRX 544,241행; 조정 정의 동일성 미확인 |
| 직접 차단 | INVALID_OHLCV, PRICE_SEMANTICS_UNVERIFIED, MIXED_VENDOR_ADJUSTMENT_UNVERIFIED |

종가0 1,201행인 `102950`의 원천·정밀도 문제는 이전 조사에서 미해결이다. `raw_response`의 ka10081 보관은 이번 재조회에서도 0건이었다. 상폐 시세 추가는 확인했지만 당시 거래 가능·종목 유형·상폐 보유 정산까지 검증됐다고 보지 않는다.

대량 자료는 Git에 넣지 않았다. `%LOCALAPPDATA%\vectorbt-research\` 아래 다음 디렉터리에 있다. 다른 컴퓨터에는 자동 전달되지 않으므로 재추출 또는 별도 이관이 필요하다.

| 디렉터리 | 용도 |
| --- | --- |
| `krx-lab-db-20260913-1542` | 성공한 실제 스냅샷·SQL·manifest·quality |
| `krx-lab-real-20260913-final` | 실제 데이터 차단 이력·report.html·selection.json |
| `krx-lab-synthetic-data-20260913` | 합성 자료 |
| `krx-lab-synthetic-20260913-final` | 합성 64건 성공, 752건 PLANNED, 후속33건 BLOCKED |
| `krx-lab-diagnostic-20260913-v2` | 실제 종목/연도/진입별 빈도 434,700행·진단 영수증 |

이름이 `-final`이 아닌 이전 실험 및 실패 추출 디렉터리는 이력 보존용이다. 기존 실험을 덮어쓰거나 실패 흔적을 삭제하지 않았다. 이전 스냅샷 품질 JSON의 first_date/last_date는 요청 범위 표기였으며 실제 관측 종료일은 검증 JSON의 별도 필드로 남겼다.

## 4. 다음 작업: 가격 원천·오류 원인 확인부터

1. `AGENTS.md`, 이 HANDOFF, 사용자 결정 JSON을 확인한다.
2. 홈서버 연결과 데이터 변경 여부를 읽기 전용으로 확인한다. 자동 재수집·DB 수정은 하지 않는다.
3. 관련 백필 프로젝트 `C:\Users\aeby\vscode\ted-startup`의 최신 HANDOFF·수집/변환 코드·완료 로그를 읽고 기존 가격 계보 조사와 대조한다. 원천 응답·실행 당시 코드/플래그·가격/거래량 단위·반올림·조정 기준을 확보한다.
4. 비정상 봉을 거래정지/정상 비거래/조정 정밀도/적재 오류 등으로 근거 있게 분류한다. 종목 통째 제외나 전일 가격 채움으로 인수 완료를 선언하지 않는다.
5. 여기서 처리할 수 있는 문제와 백필 담당에서 재납품할 자료를 구분해 **데이터 인수 보완 목록**을 만든다. 원가격·기업행사·상폐 정산·공식 거래일·역사 종목/업종/거래 상태·비용 자료를 포함한다.
6. 데이터 계약에 맞춰 남은 어댑터와 후속 단계 구현·검증을 마친 뒤 새 실험에서 2015~2023 실제 48개 전략을 비교한다. 후보·정책을 고정한 다음에만 최종 잠금 구간을 연다.

다음 세션 시작 문장:

```text
AGENTS.md와 HANDOFF.md를 읽고 데이터 인수 보완부터 진행하자.
백필 프로젝트와 홈서버를 읽기 전용으로 확인해서 가격 조정·비정상 OHLCV 원인을 분류하고,
여기서 처리할 항목과 추가로 받아야 하는 원천/역사 자료를 정리해줘.
데이터 검증 전 수익률 실행은 하지 말고 2024년 이후 최종 검증 구간은 잠금 유지해.
```

## 5. 재확인 명령과 종료 상태

저장소 루트 PowerShell에서 실행한다. 코드·설정·데이터·의존성 버전이 바뀌면 기존 실험 resume 대신 새 plan을 만든다.

```powershell
.venv/Scripts/python.exe -X utf8 -m pytest tests/research docs/strategy-research/test_research_backtest.py -q
.venv/Scripts/python.exe -X utf8 docs/strategy-research/backtest-lab/verify_implementation.py
uv run --no-sync ruff check research/krx_lab tests/research
```

커밋 대상은 이 HANDOFF, 이번 전략 연구 문서·프롬프트·소량 증거·단일종목 예제, research 패키지·연구 테스트, 테스트 의존성이다. 기존 프롬프트 원본은 내용 수정 없이 보존했다. 전체 제품 테스트·Rust 빌드·MkDocs 배포 빌드는 실행하지 않았다.

종료 전 fetch 결과 로컬이 origin/master보다 2커밋 앞섰고 원격에만 있는 커밋은 0이었다. 이번 인수 커밋과 선행 2커밋을 함께 정상 push한다. Tests 워크플로는 PR/수동 실행용으로 master push만으로 생성되지 않는다. 최종 커밋 SHA·push 성공·원격 동기화·작업 폴더·해당 SHA의 CI 여부는 종료 응답에서 실측해 보고한다. 오래된 성공 run을 이번 변경의 검증으로 사용하지 않는다.
