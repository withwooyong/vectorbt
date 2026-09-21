# 데이터 보완 대기 중 소프트웨어 개발 결과

사용자가 선택한 D0~D7은 **합성 입력 기반 계좌·인수 검사·상태 고정·복구·보고 기능을 구현하고 검증하는 작업**이다. **이번 개발은 검증 완료 8/8·가중 진행률 100%이며 범위 내 남은 작업과 차단 요인은 없다.** 관련 회귀 184개가 통과했고, 코드 독립 재검토에서 Critical 0·Major 0을 확인했다. 실제 데이터 품질 향상이나 전략 수익성을 검증한 결과는 아니다. 데이터 수집·정정은 ted-startup 담당이며, 실제 자료 인수와 후속 33슬롯 실행 연결은 남아 있다.

작업별 담당·가중치·완료 상태는 [개발 WBS](parallel-development-wbs-2026-09-14.md), 전체 연구 잔여 범위는 [주 WBS](wbs.md)를 따른다. 먼저 아래 기능과 검증을 확인하고, 지원 한계를 읽은 뒤 다음 작업을 선택하면 된다.

## 구현한 기능과 확인한 동작

| 작업 | 결과 | 확인한 동작 |
| --- | --- | --- |
| D0 계약 | 납품·계좌·후보 증거·실행 훅과 공통 손계산 fixture | 버전·필수 필드·시간 순서·합성/실자료 구분 |
| D1 계좌 엔진 | 원가격, 분할·병합·단주·배당·상폐 정산, 날짜별 비용·호가 | 현금·미수금·수량·원가 보존, 휴장일 지급, 미지원 사건 거절 |
| D2 인수 검사 | 출처 파일·해시·revision·달력·종목 이력 대조 | 가격과 달력이 함께 누락된 경우도 검출, 실제 인수 등급 승격 금지 |
| D3 상태 고정 | 합성 freeze/finalize와 해시 연결 기록 | 다른 후보·다른 데이터의 결과 거절, 최종 참조 파일 변조 재검사, 잠금 접근 차단 |
| D4 운영 | 같은 프로세스 RSS/디스크 감시와 협력 중단 | 자원 초과 사유 보존, 관측 최대값 기록, 중단 attempt 보존 |
| D5 보고 | 독립 HTML 자산·낙폭·월별 손익·현금흐름·출처 정보 | 비용 중복 합산 방지, 청산 후 과거 보유 표시 방지, 장부 ID 추적 |
| D6 통합 | CLI·runner·독립 장부 재생·저장·재개 연결 | 실제 하위 프로세스 종료 후 저장/rename/registry 전후 6개 경계 복구 |
| D7 검증 | 전체 회귀·독립 검토·문서·브라우저 확인 | 검토 지적 수정 후 재검증, 지원 범위와 잔여 작업 기록 |

엔진·상태 설계에는 Astra high, 인수·운영·보고에는 Terra medium/high를 배정하고 메인이 공통 파일 통합을 맡았다. 별도 Astra high 검토자가 구현을 검토했다. D0 최초 검토만 세션 thread 한도로 기존 Astra medium 에이전트를 재사용했으며, 실제 배정은 개발 WBS에 기록했다.

## 실행한 검증과 재현 방법

기존 `.venv`를 사용했다. `tests/research` 전체 **184 passed, 33.90s**, Ruff **All checks passed**를 확인했다. 테스트 범위는 연구 패키지이며 vectorbt 전체·Rust·문서 사이트 빌드는 실행하지 않았다. 해당 엔진 및 공개 API를 변경하지 않았기 때문이다.

```powershell
.venv/Scripts/python.exe -X utf8 -m pytest tests/research -q
ruff check research/krx_lab tests/research --output-format concise
git diff --check
.venv/Scripts/python.exe -X utf8 -m research.krx_lab inspect-delivery --delivery tests/research/fixtures/contracts_v1/delivery.json
```

합성 납품 실행과 손계산 보고서를 별도로 생성했다. 독립 재생은 전이 4개·일말 평가 4개에서 일치했다. 짧은 납품 예제에는 만기일까지의 달력이 없어서 `EXPIRY_CALENDAR_UNAVAILABLE` 문제가 남는다. `SUCCEEDED`는 실행 성공이며, 문제가 남은 결과를 후보 선정이나 finalize에 사용하지 않는다.

로컬 예제 위치는 `C:/Users/aeby/AppData/Local/vectorbt-research/parallel-development-20260914-gi_knmmp/`다. `engine-run/result/detail-report.html`은 엔진 실행 결과, `hand-calculated/detail-report.html`은 별도 손계산 장부 보고서, `report.png`는 Chrome headless 1440×2200 화면이다. 화면에서 한글·차트·표·합성 표시를 확인했다. 이 임시 경로는 저장소에 포함하지 않으며 정답 입력은 `tests/research/fixtures/contracts_v1/`에 보존했다. 손계산 최종값은 현금 517 + 보유 평가 480 = 자산 997, 수수료 1·세금 2다.

독립 검토에서 출처 시점·달력 누락, 비용과 지급 연결, 고정 후보와 최종 장부 연결, 최종 참조 파일 변조, 청산 후 잔존 보유 표시를 보강했다. 메인이 수정하고 별도 검토자가 재확인했다.

## 지원 한계와 남은 작업

- 납품 파일의 실제 내용 대조는 `synthetic-source-v1` JSON만 지원한다. 실제 납품 스키마 어댑터와 재납품 인수는 별도 작업이다.
- 합성 엔진은 단일 시장, 종목별 하루 한 행사, 개장일 행사 효력, 정수 1주 단위, 슬리피지 0, 거래 결제 지연 0을 지원한다. 실제 역사 시장 모형의 검증이나 일반화된 결제 엔진이 아니다.
- `run-delivery`는 새 디렉터리에서 실행하는 일회 검사다. 이 경로는 기존 배치 `run/resume`의 재개 기능과 별개이며, `after_registry_commit` 훅을 제공하지 않는다.
- RSS/디스크 임계치는 협력 중단 기준이다. OS 강제 상한·다중 호스트·자식 강제 종료는 지원하지 않는다.
- 합성 freeze/finalize는 증거 연결과 상태 전이 검증이다. 로컬 전체 해시 이력에 대한 외부 공증이나 실제 후보 선정은 제공하지 않는다.
- `allocation`, `realistic-costs`, `ambiguity`, `controls`, `holdout`의 후속 33슬롯 실행 연결과 현실 비용 근거가 남아 있다. 실제 데이터와 2024년 이후 잠금 가격은 이번 작업에서 열람하지 않았다.

## 다음 작업 선택

1. **추천: 후속 33슬롯의 합성 실행 연결을 별도 WBS로 개발한다.** 데이터 보완 대기 중 진행할 수 있고, 단계별 입력·선행 조건·차단 기준을 먼저 고정한 뒤 병렬 구현할 수 있다. 실제 holdout 접근은 선행 검증 전까지 차단한다.
2. **ted-startup 새 revision이 준비되면 납품 어댑터와 읽기 전용 인수 검사를 진행한다.** 실제 스키마 대응, 원가격·행사·달력·종목 이력을 검증하고 부족한 항목을 ted-startup 작업으로 전달한다.

commit·push는 실행하지 않았다. 이번 개발 묶음의 검증과 전체 전략 연구 완료는 구분한다.
