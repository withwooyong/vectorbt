# 가격 원인·역사 자료 조사: 출처 분기와 실행 로그를 확인했다

**① 가격 원인 조사와 ② 역사 자료 확보 경로 조사를 병렬로 수행해, 현재 수집 코드의 출처 분기·가격 검사 누락을 확인하고 재납품 명세를 만들었다.** 가장 중요한 발견은 DB의 `KRX` 라벨과 달리 현재 pykrx 수정주가 호출의 실제 상류가 Naver라는 점이다. 기존 오류의 최종 생성 원인은 당시 시세 원문이 없어 미확정이다. 따라서 **데이터 인수는 `BLOCKED`를 유지**하며 실제 백테스트는 실행하지 않았다.

2026-09-14 KST에 조사했다. 가격 표본은 2015-01-02~2023-12-31로 제한했고 2024년 이후 가격은 조회하지 않았다. 공식 문서와 기존 코드, 읽기 전용 DB 표본·운영 로그를 확인했으며 원본 DB·수집 프로그램을 수정하거나 외부 API로 시세를 재수집하지 않았다. 운영 로그에는 전체 백필의 건수·마스터 날짜가 포함되며 가격 봉이나 전략 성과가 아니다.

먼저 핵심 발견에서 이번에 새로 확인한 것과 여전히 모르는 것을 구분한다. 다음 조치 표는 조사 결과를 구현·자료 보완으로 연결하며, [재납품 명세](delivery-spec.md)는 담당자가 받아야 할 필드와 완료 조건을 정한다. 자세한 근거는 [가격 조사](price-provenance.md)와 [역사 출처 조사](historical-sources.md), 진행 상태는 [WBS](wbs.md)에 있다.

## 1. 가격 조사에서는 현재 코드 경로와 검사 누락을 확인했다

| 이번 발견 | 확인한 사실 | 아직 확인하지 못한 것 |
| --- | --- | --- |
| `KRX` 라벨과 실제 공급 경로가 다름 | 배포 pykrx 1.2.8은 `adjusted=True` 일봉을 Naver fchart XML로 요청. 현재 앱은 이 적재 경로에 `KRX` 라벨을 기록 | 과거 각 배치의 실제 버전·요청·원 XML과 전체 행의 연결 |
| 로컬 정수 변환 가설의 범위를 좁힘 | 현재 경로는 XML 정수 필드→`np.int64`→Python `int`. 올바른 고가·종가 순서를 1~2원 역전시키지 않음 | 당시 상류의 값·조정·반올림 정책이 오류를 만든 정확한 과정 |
| 이상 행이 저장될 수 있는 코드 경로 | 매퍼가 종가 양수만으로 통과시켜 `high < close`, OHL 0/종가 양수도 저장 가능 | 각 OHL 0이 공식 비거래 표기인지 원천/적재 오류인지 |
| 키움 종가 0/1 경계 | `102950` 원문 대조용 25행 확보. 현재 파서는 `"0"→0`, `"1"→1`, 소수 문자열은 `None` | 과거 ka10081 응답 값과 조정 정의. 0원 원인 확정에는 원문 필요 |

KRX 라벨 표본 `032980`의 2015-01-06 고가는 10,428, 종가는 10,430이다. 2015-02-25와 2015-03-19도 2원 차이로 역전된다. 같은 값을 넣은 순수 변환 재현은 **현재 매퍼가 역전을 보존해 통과시킨다는 증거**이며, 당시 공급자가 그 값을 실제로 반환했다는 원문 증거는 아니다.

이번 고정 표본은 총 **34행**이다. KRX는 양수 거래량 역전·OHL 0 비거래 표현·그 외 거래량 0 역전의 세 유형에서 각 3행, KIWOOM은 종가 0↔양수 전환 전후 25행을 골랐다. [sample-request.json](sample-request.json)에 키·DB 값·수집 시각·행 hash와 필요한 원문을 담았다. 전수 대표성이나 오류 해결률을 주장하는 표본은 아니다.

## 2. 원 실행 로그는 복구했지만 시세 원문·실행 manifest는 확보하지 못했다

**`kiwoom-app:/tmp/backfill_delisted.log`를 찾아 79,783바이트 전체를 보존했다.** 호스트의 같은 `/tmp` 경로는 없었지만 컨테이너 내부에는 있었다. 앞으로 파일 부재는 실행 환경을 포함해 판단해야 한다.

- 원 로그 SHA-256: `b915261fd75c63ea96dc0dba25a412d0c13647800431f538f38dc083072c4da9`.
- 로그의 종목별 적재 530건을 합산하면 612,607행이며 종료 요약과 같다. `EXIT=0`도 기록됐다.
- `032980`, `099340`, `217620`의 적재 완료 기록은 DB 표본 수집 시각과 가까운 시각에 있다. 이것은 실행 연결 단서이며 각 원문 값·행 hash의 일치를 입증하지 않는다.
- 이 로그는 **전체 과거 백필 실행 범위**의 집계다. 2015~2023 감사의 KRX 544,241행과 범위가 다르므로 두 값을 오류로 비교하지 않는다.
- 로그에 실행 ID·commit·이미지·pykrx 버전·원문 hash manifest가 없고, DB의 ka10081 원 응답 보관도 0건이다. 현재 코드·설치 패키지가 같아도 과거 실행 환경이 입증된 것은 아니다.

근거: [원 로그 사본](evidence/container-log-archive/container_backfill_log_full.stdout.txt), [수집 영수증](evidence/container-log-archive/receipt.json), [컨테이너 파일 메타데이터](evidence/container-original-log/container_backfill_log.stdout.txt), [DB 고정 표본](evidence/samples/results.json). `/home/ted/backfill-phase*.log`는 별도 실행 기록 후보이므로 이 원 로그와 혼용하지 않았다.

## 3. 역사 자료는 재사용 경로가 있지만 전수 확보는 미확정이다

OpenDART는 공시목록·원문과 일부 구조화 기업행사의 유력한 경로다. 예를 들어 [공식 무상증자 개발가이드](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS005&apiId=2020024)는 최초접수일 기준 2015년 이후 제공을 명시한다. 다른 행사별 근거와 접근 결과는 [출처 조사](historical-sources.md)에 직접 URL로 연결했다.

| 확보 대상 | 이번 판단 | 기존 코드의 보완점 |
| --- | --- | --- |
| 일부 증자·감자·합병·분할합병 | OpenDART 공식 문서에서 2015년 이후 제공 경로 확인. 전 기업·전 사건 누락 없음은 미검증 | 구조화 필드와 원문·정정·효력일을 연결 |
| 일반 공시목록·원문·배당 | 기존 DART 클라이언트·파서 재사용 가능. 일반 공시/원문의 역사 하한·상폐 기업 전체 반환은 미확정 | 원문 ZIP을 불변 보관. 일별 잡을 기간·페이지·재개 단위 실행으로 확장 |
| 당시 종목·상폐·정지·코드 승계·업종 | KIND/KRX 후보 경로 확인. 2015~2023 전수 제공과 유효기간 복원은 미확정 | 현재 상장 종목 필터로 과거 상폐 종목을 제거하지 않도록 별도 역사 모집단 구성 |
| 공식 거래일 | 공식 연도 일정·휴장 근거 확보 필요. 시세 관측일은 대조용 | 가격 날짜의 합집합으로 공식 휴장 달력을 대체하지 않음 |

현재 `raw_payload`와 제목 분류만으로는 원문·기업행사 인수 계약을 만족하지 못한다. 효력일, 당시 알 수 있었던 시점, 정정 선후 연결, 영구 종목 ID와 코드 유효기간, 원문 SHA-256을 함께 보존해야 한다. 직전 감사의 기업행사·공시 대상 기간 0건은 **2026-09-13 관측**이며 이번에 그 테이블을 다시 집계한 것은 아니다.

## 4. 다음 구현은 원문 보존과 역사 수집 준비를 병렬로 진행한다

이번 요청의 조사·명세 범위를 넘어서는 후속 작업이며 아직 실행하지 않았다. 구체 수정 대상과 회귀 조건은 [가격 조사](price-provenance.md), 공급 필드·인수 조건은 [재납품 명세](delivery-spec.md)에 있다.

| 병렬 묶음 | 구현·자료 산출물 | 완료 조건 |
| --- | --- | --- |
| A — 수집 계보·품질 방어 | 실제 upstream과 DB 라벨 분리, 원 응답 archive, 실행 manifest, 비정상 행 격리 | 34개 표본의 원문→변환→결과를 재현하고 실패 이유를 보존. 원본 덮어쓰기 없음 |
| B — 역사 자료 배치 준비 | OpenDART 기간·페이지 분할, 원문 보존, 정정 연결, 상폐 종목을 포함한 코드 모집단과 미확정 KRX/KIND 범위 확인 | 제공 가능한 기간과 불가능한 영역을 실반환 근거로 확정. 효력일·인지 시점 분리 |
| 합류 — 새 납품 검증 | 새 revision·스냅샷에 기존 SQL·표본 대조·역사 계약 검사 적용 | 데이터 인수와 실제 실행 모형 검증을 모두 통과하기 전 수익률 실행 금지 |

## 5. 재현·검증 방법

새 파일만 생성하는 다음 도구를 남겼다. 이미 존재하는 출력 경로는 거부한다. 실행 위치는 저장소 루트이며, 예시의 `next` 경로가 이미 있으면 새 이름을 사용한다.

```powershell
# DB 표본을 다시 확인할 때만 실행
.venv/Scripts/python.exe -X utf8 docs/strategy-research/backtest-lab/remediation-discovery-2026-09-14/collect_samples.py --out "$env:LOCALAPPDATA/vectorbt-research/remediation-next/samples"

# 저장된 증거만 사용해 요청서를 재생성: 네트워크 호출 없음
.venv/Scripts/python.exe -X utf8 docs/strategy-research/backtest-lab/remediation-discovery-2026-09-14/build_sample_request.py --out "$env:LOCALAPPDATA/vectorbt-research/remediation-next/sample-request.json"

# 필요 항목만 서버에서 읽기 전용 확인
.venv/Scripts/python.exe -X utf8 docs/strategy-research/backtest-lab/remediation-discovery-2026-09-14/collect_server_metadata.py --only repository_state container_backfill_log --out "$env:LOCALAPPDATA/vectorbt-research/remediation-next/server"

.venv/Scripts/python.exe -X utf8 docs/strategy-research/backtest-lab/remediation-discovery-2026-09-14/test_tools.py -v
.venv/Scripts/python.exe -X utf8 docs/strategy-research/backtest-lab/remediation-discovery-2026-09-14/verify_discovery.py
ruff check docs/strategy-research/backtest-lab/remediation-discovery-2026-09-14
```

DB 표본 검사에는 읽기 전용 트랜잭션·문장/잠금 시간 제한·오류 즉시 중단을 적용했다. 수집 도구는 실패·시간 초과의 부분 stdout/stderr와 영수증을 보존하고, 요청서 생성기는 원 증거 hash·가격 기간·중복 키를 검사한다. 서버 메타데이터 검사는 명령별 결과를 기록하며 복합명령 앞부분의 실패가 가려지지 않도록 `&&`를 사용한다.

**검증 결과:** 오프라인 회귀 8개, `ruff check`, 표본·서버 증거 hash·원로그 530종목/612,607행 교차 합산·로컬 링크 검사는 통과했다. [검증 JSON](verification.json)의 PASS는 저장 증거 정합성 판정이며 데이터 인수는 `BLOCKED`다. 작성자와 별도 에이전트가 자동화와 최종 문서·대표 공식 가이드를 검토했고, 실패 전파 및 현재 코드/과거 원인 구분에 관한 지적을 반영했다.

확인한 것은 코드 경로, 자료 확보 경로, 표본·로그와 재현 가능한 명세다. 과거 시세 원문 복구·실제 재수집·DB 정정·기업행사 전수 인수·전체 제품 테스트·Rust·사이트 빌드·실제 성과 실행은 수행하지 않았다. 기존 감사·스냅샷·인수인계와 인접 저장소는 수정하지 않았다.
