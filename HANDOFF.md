# 다음 세션 인수인계: v3로 56개 전략 실행 준비

> 2026-09-21 KST 현재 판단은 [v3·56개 전략 핸드오프](docs/strategy-research/backtest-lab/handoff-v3-56-2026-09-21.md)를 우선한다. 아래 9월 15일 이전 기록의 ted-startup 납품 대기·업종 필수 차단 판단은 현재 작업 지시가 아니다. v3 데이터에 대한 추가 ted-startup 작업을 선행조건으로 만들지 말고, vectorbt의 실데이터 실행 구현과 검증을 진행한다. 56개 실자료 결과는 아직 없다. 사용자의 요청 없이 `AGENTS.md`를 수정하지 않는다.

---

# 이전 인수인계: PostgreSQL 재인수 진단

> 최신 갱신: 2026-09-15 KST. 아래 9월 14일 기록보다 이 단락을 우선한다.

사용자 안내로 납품 대기를 해제하고 home DB를 읽기 전용 재검사했다. **실제 연구 인수는 여전히 `BLOCKED`다.** 2015~2023 수정주가 `TRADED` 행에 가격 0 이하 699개(KIWOOM `102950` 695개 + KRX 4개)가 남아 있다. ted-startup의 signal 정정 완료와는 공급자·모집단이 다르다. 전체 영향 키와 납품 계보·역사 입력 보완 조건은 [새 인수 결과](docs/strategy-research/backtest-lab/postgresql-admission-2026-09-15/README.md), 진행 상태는 [새 WBS](docs/strategy-research/backtest-lab/postgresql-admission-wbs-2026-09-15.md)를 따른다.

다음 작업은 ted-startup에서 원문·단위·조정 정의 및 공식 상태 근거를 연결한 새 revision을 납품받고 실제 형식용 읽기 전용 어댑터를 검증하는 것이다. 이번에 수집·정정·실제 수익률·2024년 이후 가격 열람·푸시는 하지 않았다. 기존 미커밋 파일은 보존한다. 아래 모델 정책과 연구 잠금 기준은 유지한다.

---

# 이전 인수인계: ted-startup 납품 대기

> 갱신: 2026-09-14 KST · 작업 폴더: `C:/Users/aeby/vscode/stock/vectorbt`
> 브랜치: `master` · 현재 HEAD: `6015ecbd95aa5267afe2fed6f24451fd6609264f`

**현재 판단:** 합성 소프트웨어 D0~D7과 후속 33슬롯 개발은 완료했다. 실제 데이터 인수와 전략 선정은 미완료다. **사용자는 ted-startup 납품 형식이 준비될 때까지 개발을 대기하고, 모델을 변경한 뒤 다음 세션에서 재개하기로 했다.** 새 개발·에이전트·자동 감시를 시작하지 않는다. 데이터 수집·적재·정정은 모두 ted-startup 담당이다.

**보존 상태:** 이번 개발 변경은 로컬 미커밋 상태이며 push도 하지 않았다. 새 체크아웃에는 이 변경이 자동으로 따라오지 않으므로 **같은 작업 폴더에서 재개**한다. 기존 사용자 수정 `AGENTS.md`, 감사·재납품 문서 및 미추적 파일을 보존하고 reset/clean/일괄 덮어쓰기를 하지 않는다. 아래 이전 기록의 push 상태는 당시 기록이며 이번 미커밋 개발과 구분한다.

## 완료한 범위와 검증

| 범위 | 상태 | 근거 |
| --- | --- | --- |
| D0~D7 계약·계좌·인수 검사·상태 고정·복구·보고 | 8/8 · 100% 완료 | [개발 결과](docs/strategy-research/backtest-lab/implementation-results-2026-09-14.md), [개발 WBS](docs/strategy-research/backtest-lab/parallel-development-wbs-2026-09-14.md) |
| 후속 33슬롯 합성 실행 연결 | 6/6 · 100% 완료 | [결과·재현 명령](docs/strategy-research/backtest-lab/conditional-results-2026-09-14.md), [WBS](docs/strategy-research/backtest-lab/conditional-development-wbs-2026-09-14.md) |
| 실제 데이터 인수·실제 전략 선정 | 대기 / 차단 | ted-startup 납품 형식·새 revision 대기, [전체 WBS](docs/strategy-research/backtest-lab/wbs.md) |

- 최종 회귀: `.venv/Scripts/python.exe -X utf8 -m pytest tests/research -q` → **370 passed, 94.91초**. Ruff 통과. 독립 검토 Sol high: Critical 0·Major 0, 최초 Major 2개 수정 후 신규 검사186개 재확인.
- 후속 합성 실험은 선행26개와 합성 잠금7개를 분리해 **33/33 성공** 및 저장 장부 재검증을 통과했다. 고정된 정책·비용·데이터·주문 날짜·보고 지표 대조와 실패 로그 보존 회귀를 포함한다.
- [검증 JSON](docs/strategy-research/backtest-lab/conditional-verification-2026-09-14.json)의 코드 해시 `09a56d94e8fa31fdfdddc4b47e29e583715dd6f94c6011b71ecfdcae29a8f3c9`와 종료 시 현재 소스 해시가 일치했다. 이번 종료 준비에서는 문서만 변경하므로 전체 테스트를 반복하지 않았다.
- 임시 예제: `C:/Users/aeby/AppData/Local/Temp/krx-conditional-final-mzifva7i/experiment/conditional-report.html`. 임시 폴더는 정리될 수 있으므로 결과 문서의 fixture 명령으로 재현한다.
- 실제 DB·실자료 수익률·2024년 이후 잠금 가격은 이번 개발에서 열람하지 않았다. vectorbt 본체·Rust·사이트 빌드는 이번 변경의 검증 범위 밖이다.

## 다음 배정에 적용할 모델 정책

비용 절감을 위한 사용자 최종 결정이다. **Sol을 상위 모델로 두고 Luna·Terra를 함께 사용한다. Astra는 새로 배정하거나 자동 상향하지 않는다.** 모든 작업을 Sol로 통일한다는 중간 해석은 폐기한다.

| 담당 | 모델·추론 |
| --- | --- |
| 팀장 WBS·의존성·통합 | gpt-5.6-sol medium, 복잡한 최종 판단은 high |
| 파일 탐색·정형 문서·단순 반복 수정 | gpt-5.6-luna low/medium |
| 명세가 확정된 구현·테스트·보고서 | gpt-5.6-terra medium |
| 수치 계산·잠금·중단 복구·독립 최종 검토 | gpt-5.6-sol high |

실제 요청 모델과 실행 모델을 확인해 WBS에 기록한다. 구현자와 검토자를 분리한다. 현재 팀장 세션 모델을 자동으로 바꿨다고 가정하지 말고, 사용자가 변경한 다음 세션 설정을 확인한다. 이번 후속 문서는 Terra medium, 독립 검토는 Sol high로 실행했다.

## 재개 조건과 첫 작업

1. **현재는 대기한다.** ted-startup 납품 형식이 준비되었다는 사용자 안내 후 같은 폴더에서 이 문서와 `git status --short`를 확인한다. 미커밋 변경을 먼저 보존하고 실제 모델 설정을 확인한다.
2. 제공된 형식·파일 위치·dataset_id/revision·원문 출처·파일 해시를 [재납품 명세](docs/strategy-research/backtest-lab/remediation-discovery-2026-09-14/delivery-spec.md), [계약 v1](docs/strategy-research/backtest-lab/contracts-v1.md)과 대조한다.
3. 실제 납품 형식용 **읽기 전용 어댑터와 인수 검사**를 별도 WBS로 진행한다. 현재 내용 검사는 `synthetic-source-v1` JSON만 지원하므로 실제 파일을 합성으로 재표시해 실행하지 않는다. 부족한 수집·정정 항목은 ted-startup에서 처리하도록 먼저 알려준다.
4. 자료 인수만으로 실제 실행·선정·잠금을 해제하지 않는다. 역사 시장 프로필·현실 비용·정책 고정 등 선행 기준을 확인한다. 합성 엔진은 단일 시장·종목별 하루 한 행사·정수1주·슬리피지0·거래 결제 지연0 지원에 한정된다.

재개 메시지 예시:

> HANDOFF.md부터 읽어줘. 팀장은 gpt-5.6-sol medium이고, Luna·Terra·Sol 배정 정책을 적용해. ted-startup 납품 형식이 준비됐으니 기존 미커밋 변경을 보존하고 읽기 전용 어댑터·인수 검사부터 진행하자.

사용자에게 보고할 때는 완료/전체·검증 가중 진행률·남은 작업을 구분하고 **항상 다음 작업 선택지와 추천안을 제시**한다. 전체 프로젝트가 끝난 경우에만 전체 작업 완료라고 명시한다. 기본 설명은 한글이다.

## 이번 종료 준비 WBS

| ID | 산출물·담당 | 선행 | 완료 기준 | 가중치 | 상태 |
| --- | --- | --- | --- | --- | --- |
| H1 | 현황·검증 기록 대조 / 메인 | 없음 | Git·소스 해시·터미널 확인 | 1 | 완료 |
| H2 | 최신 핸드오프 / 메인 | H1 | 대기 조건·모델·재개 지점·미커밋 보존 기록 | 1 | 완료 |
| H3 | 문서·종료 안내 검증 / 메인 | H2 | 링크·diff·Orca 대기 메모 확인 | 1 | 완료 |

종료 준비 진행률: **3/3 · 100%**, 남은 종료 준비 없음. 링크·diff 검증을 완료했다. 새 에이전트나 워크트리를 시작하지 않는 문서 인수인계다. 전체 전략 연구는 ted-startup 납품 대기 상태다.

---

<details>
<summary>이전 기록: 2026-09-13 당시 상태 (최신 판단은 위 내용을 우선)</summary>

# 다음 세션 인수인계

> 갱신: 2026-09-13 KST
> 작업 폴더: `C:\Users\aeby\vscode\stock\vectorbt`
> 브랜치: `master` / 원격: `withwooyong/vectorbt`
> 이번 인수 커밋의 부모: `3c32d26`

**현재 판단:** 1억 원·최대 달력 1개월·사전 익절/손절·최대 20종목의 연구 핵심 프로그램을 구현했다. 합성 장부 검증은 통과했지만 **실제 DB 수익률 실행은 데이터 인수에서 BLOCKED, 최종 전략은 NO_SELECTION**이다. 9월 13일 저녁 원천 코드·품질 패턴·데이터 계약의 병렬 조사를 완료했다. 다음 작업은 [보완 목록](docs/strategy-research/backtest-lab/admission-audit-2026-09-13/README.md)에 따른 원천 자료 확보와 남은 어댑터 검증이다. 사용자 결정에 따라 미검증 자료의 탐색용 수익률도 실행하지 않는다.

**Orca 재개:** 등록 프로젝트 `vectorbt`의 경로는 현재 폴더와 같은 `C:\Users\aeby\vscode\stock\vectorbt`다(종료 시 CLI로 확인). 사용자가 Orca에서 직접 이어가는 인수인계이며, 새 에이전트나 별도 워크트리를 자동 시작하지 않았다. 별도 체크아웃을 사용하는 경우 최신 `origin/master`와 이 문서를 먼저 확인한다. `.venv`와 `%LOCALAPPDATA%`의 대량 스냅샷은 Git 산출물이 아니므로 별도 체크아웃에서 자동으로 생기지 않는다.

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

2026-09-13 저녁에 원천 코드·비정상 봉·데이터 계약을 세 에이전트로 병렬 조사했다. [통합 결과와 보완 목록](docs/strategy-research/backtest-lab/admission-audit-2026-09-13/README.md)을 먼저 확인한다. 읽기 전용 재집계는 기존 스냅샷과 같았으며, KRX 비정상 70,871행은 전부 고가<종가(거래량 양수 7,935행)였다. KIWOOM 1,201행의 종가 0과 구분했다. 이상 값을 허용하는 변환·저장 경로는 확인했으나 원천 응답과 조정 정의가 없어 인수 차단은 유지한다. 아래 3~5번의 초기 조사는 완료했고, 다음은 보고서의 우선 보완 묶음에 따라 수정/비수정 원문·원 DataFrame·실행 계보를 확보하는 일이다. 원본 수정·재수집·실제 수익률 실행은 하지 않았다.

1. `AGENTS.md`, 이 HANDOFF, 사용자 결정 JSON을 확인한다.
2. 홈서버 연결과 데이터 변경 여부를 읽기 전용으로 확인한다. 자동 재수집·DB 수정은 하지 않는다.
3. 관련 백필 프로젝트 `C:\Users\aeby\vscode\ted-startup`의 최신 HANDOFF·수집/변환 코드·완료 로그를 읽고 기존 가격 계보 조사와 대조한다. 원천 응답·실행 당시 코드/플래그·가격/거래량 단위·반올림·조정 기준을 확보한다.
4. 비정상 봉을 거래정지/정상 비거래/조정 정밀도/적재 오류 등으로 근거 있게 분류한다. 종목 통째 제외나 전일 가격 채움으로 인수 완료를 선언하지 않는다.
5. 여기서 처리할 수 있는 문제와 백필 담당에서 재납품할 자료를 구분해 **데이터 인수 보완 목록**을 만든다. 원가격·기업행사·상폐 정산·공식 거래일·역사 종목/업종/거래 상태·비용 자료를 포함한다.
6. 데이터 계약에 맞춰 남은 어댑터와 후속 단계 구현·검증을 마친 뒤 새 실험에서 2015~2023 실제 48개 전략을 비교한다. 후보·정책을 고정한 다음에만 최종 잠금 구간을 연다.

다음 세션 시작 문장:

```text
AGENTS.md, HANDOFF.md와 docs/strategy-research/backtest-lab/admission-audit-2026-09-13/README.md를 읽고 이어서 진행하자.
원천 코드·품질·계약 초기 조사는 완료됐으니 반복하지 말고, 보완 목록의 우선 묶음부터 진행해줘.
102950의 수정/비수정 원문과 KRX 고가<종가 표본의 원 DataFrame·dtype·실행 계보를 확보할 경로를 확인하고,
가격 의미가 확정된 계약부터 남은 데이터 인수·기업행사·현실 비용 어댑터를 구현·검증하자.
독립 작업은 적절한 모델의 agent로 병렬 진행해도 된다. 원본 DB 수정·재수집은 자동 실행하지 마.
데이터 검증 전 수익률 실행은 하지 말고 2024-01-01~2026-09-10 최종 검증 구간은 잠금 유지해.
```

## 5. 재확인 명령과 종료 상태

저장소 루트 PowerShell에서 실행한다. 코드·설정·데이터·의존성 버전이 바뀌면 기존 실험 resume 대신 새 plan을 만든다.

```powershell
.venv/Scripts/python.exe -X utf8 -m pytest tests/research docs/strategy-research/test_research_backtest.py -q
.venv/Scripts/python.exe -X utf8 docs/strategy-research/backtest-lab/verify_implementation.py
uv run --no-sync ruff check research/krx_lab tests/research
```

이번 종료 커밋 대상은 이 HANDOFF와 `admission-audit-2026-09-13/`의 보고서·SQL·JSON·감사 스크립트다. 연구 엔진·수집 코드·DB는 수정하지 않았다. 이전 핵심 구현은 `3c32d26`에 커밋·푸시돼 있었고, 종료 준비의 fetch에서 `HEAD...origin/master = 0 0`을 확인했다.

이번 검증은 품질·실행 차단 회귀 **13 passed**, 감사 스크립트 `ruff` 통과, 스냅샷 62개 파일 해시·집계 내부 불변식·DB 집계 교차 검산·문서 링크·공백 검사 통과다. 같은 검증을 이유 없이 재실행하지 않았다. 전체 제품 테스트·Rust 빌드·MkDocs 빌드는 이번 문서·감사 작업에서 실행하지 않았다. 홈서버 컨테이너 6개는 종료 준비 재조회에서도 모두 healthy였다.

이번 변경을 정상 커밋·push하고 최종 SHA·원격 동기화·작업 폴더·해당 SHA의 CI 여부를 종료 응답에서 실측해 보고한다. Tests 워크플로는 PR/수동 실행용으로 master push만으로 생성되지 않는다. 오래된 성공 run을 이번 변경의 검증으로 사용하지 않는다.

</details>
