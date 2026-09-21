# 조건부 33슬롯 합성 실험: 사용 방법과 검증 결과

**목적과 현재 판단:** 이 문서는 `conditional_plan.py`, `conditional_execution.py`, `conditional_runner.py` 및 `conditional-plan`/`conditional-run`/`conditional-status` CLI로 만드는 후속 조건부 실험의 사용 범위와 결과 기록 기준을 정한다. 이 실험은 합성 입력의 실행·저장·재개·검증 경로만 다루며, 실제 시장 성과나 전략 선정의 근거가 아니다. 전체 회귀 370개가 통과했고 CLI에서 합성33개 실행 성공을 확인했다. **이번 개발은 6/6·100% 완료**이며 독립 재검토의 잔여 Critical 0·Major 0을 확인했다. 실제 데이터 인수와 전체 전략 연구는 미완료다.

## 핵심 요약

- 조건부 행렬은 **33개 = 배분 8 + 합성 holdout 4 + 통제 12 + 현실비용 5 + 모호성 4** 슬롯이다. 이 중 선행 실행 대상은 26개이고, 나머지 7개는 합성 holdout 의존 슬롯으로 처음에는 차단된다.
- 모든 합성 실행 입력 날짜는 2024년 이전이어야 하며, `development`, `validation_2020`, `validation_2021`, `validation_2022`, `validation_2023`, `holdout`의 여섯 구조적 기간 라벨을 정확히 사용한다. 라벨은 실제 연도별 검증 또는 실제 미사용 시장 구간을 뜻하지 않는다.
- 별도 experiment는 동결(`FROZEN`)된 합성 lifecycle, 그 lifecycle에 결속된 정확한 delivery 바이트, 코드 해시와 비용 프로필만 허용한다. 새 windows와 signals의 해시도 계획 시점에 잠기며, 이후 변경되면 실행·상태 확인에서 거절된다.
- 초기 현금은 **100,000,000원**이다. 비용은 이 합성 실험에서 상수 bps 또는 원래 합성 market profile을 쓰는 모의 가정일 뿐, 실제 체결 비용·시장 비용을 주장하지 않는다.

읽는 순서는 먼저 아래의 입력·게이트를 확인하고, 다음으로 재현 명령을 실행한 뒤, 마지막으로 상태 보고의 결과를 기록하는 것이다. 구현 작업의 소유권·진행률·독립 검토 기준은 [조건부 개발 WBS](conditional-development-wbs-2026-09-14.md)에, 전체 연구의 전제와 실제 데이터 차단 상태는 [Backtest Lab README](README.md)에 둔다.

## 무엇을 비교하고 무엇을 바꾸지 않는가

배분 단계는 `fixed20`과 `staged10_15_20` 정책을 비교한다. 그러나 비교 결과가 이미 동결된 정책을 자동 교체하거나 실제 후보 선정을 수행하지는 않는다. 모든 슬롯은 이 별도 experiment에서 새로 계산하며, 정확히 같은 동결 입력이라는 증거 없이 기존 primary run의 결과를 재사용하지 않는다.

각 슬롯은 기간, 비용, 지연, 정책, 통제 여부를 명시적으로 보존한다. `cash`와 `buy_hold` 통제는 전략 후보와 구별하고, 현실비용 슬롯은 원래 합성 market profile을 참조한다. 그 밖의 비용 bps는 합성 상수이므로 실제 수수료·세금·슬리피지의 검증값이나 비용 추정으로 해석할 수 없다.

## 실행 전제와 게이트

계획은 지정된 delivery 파일을 읽고 `source_kind=SYNTHETIC`인 경우에만 진행한다. 실제 자료로 표시된 입력은 신호를 읽기 전에 거절한다. lifecycle은 `FROZEN` 상태여야 하고, delivery 해시가 lifecycle의 데이터 결속과 같아야 하며, lifecycle에 결속된 코드 해시와 비용 프로필도 현재 입력과 일치해야 한다. signals의 모든 날짜와 여섯 windows의 시작·끝은 2024-01-01보다 앞서야 하고, windows는 순서대로 겹치지 않아야 한다.

계획 후 manifest는 delivery·signals·windows의 경로와 해시, lifecycle, 동결 해시, 코드 해시, benchmark, 33개 슬롯을 고정한다. 따라서 계획 뒤 파일을 수정하거나 코드를 바꾸면 정상 재개가 아니라 변경 감지 오류가 기대되는 동작이다. 합성 holdout 7개는 선행 26개의 성공 및 원장 검증 전까지 실행하지 않으며, `--include-synthetic-holdout`은 실제 holdout 접근 권한을 열지 않는다.

## 재현 가능한 합성 fixture 실행

아래 PowerShell 예시는 테스트 fixture가 반환한 경로를 그대로 사용한다. 새 빈 디렉터리를 지정해야 하며, fixture는 합성 delivery·signals·windows·FROZEN lifecycle을 만든다. 실제 데이터 수집이나 DB 접속을 수행하지 않는다.

```powershell
$inputs = .venv/Scripts/python.exe -X utf8 -c 'import json,tempfile; from pathlib import Path; from tests.research.conditional_fixtures import create_inputs; root=Path(tempfile.mkdtemp(prefix="krx-conditional-")); print(json.dumps({k:str(v) for k,v in create_inputs(root/"inputs").items()}))' | ConvertFrom-Json
$experiment = Join-Path (Split-Path $inputs.artifact_root -Parent) "experiment"

.venv/Scripts/python.exe -X utf8 -m research.krx_lab conditional-plan `
  --delivery $inputs.delivery --signals $inputs.signals --windows $inputs.windows `
  --lifecycle $inputs.lifecycle --out $experiment --benchmark-id $inputs.benchmark_id

# 선행 26개만 실행한다. holdout 의존 7개는 차단 상태로 남는다.
.venv/Scripts/python.exe -X utf8 -m research.krx_lab conditional-run --experiment $experiment --limit 26

# 선행 결과를 확인한 뒤에만 합성 holdout 의존 7개를 포함한다.
.venv/Scripts/python.exe -X utf8 -m research.krx_lab conditional-run `
  --experiment $experiment --include-synthetic-holdout

.venv/Scripts/python.exe -X utf8 -m research.krx_lab conditional-status --experiment $experiment
```

`conditional-status`는 저장된 입력 결속과 성공한 산출물을 다시 검증해 상태 보고를 작성한다. 실행 담당자는 이 명령의 `statuses`, 실패 사유, 원장 대조 결과를 기록하되, 단순 실행 성공을 실제 전략 선정·수익성·현실 비용 검증으로 승격하지 않는다.

## 결과 기록 범위와 한계

전체 `tests/research` 370개 통과(94.91초), 신규 통합 검사 28개 통과를 확인했다. 기본 실행 후 성공26·차단7, 명시 옵션 실행 후 성공33이며 재개 시 성공 건은 재계산하지 않는다. 선행 실패·산출물 손상 시 후속7개 차단, 저장/rename/registry 전후 6개 체크포인트 중단과 재개, 신호·실행 명세 변조 거절, 실제 입력 차단을 검사했다. 독립 검토의 지적에 따라 장부의 슬롯·정책·비용·데이터·주문 날짜와 저장 지표를 대조하고, 실패 manifest·traceback을 재시도 후에도 보존하도록 보강했다. 변조 회귀를 추가했고 Ruff도 통과했다. vectorbt 본체·Rust·사이트 빌드는 변경 범위 밖이므로 실행하지 않았다.

실행 모델의 시장·일별 이벤트 처리, 기업행사 장부, 비용 해석에는 기존 C1 엔진의 한계가 그대로 남는다. 이 실험은 한 합성 시장과 일 단위 이벤트를 사용하므로 실제 데이터 인수, 실제 holdout, 현실 체결 비용, 실전 주문 또는 수익률 주장을 대체하지 않는다. 데이터 수집은 계속 `ted-startup` 담당이며, 실제 holdout은 차단 상태이고, 이 문서 작성은 commit·push를 포함하지 않는다.

## 다음 작업 선택

1. **추천:** ted-startup 납품 형식이 준비되면 읽기 전용 어댑터와 인수 검사를 진행한다. 파일 스키마·원문 계보·달력·종목·기업행사의 부족한 항목은 ted-startup 작업으로 전달한다.
2. 데이터 보완이 더 필요하면, 이번 합성 실행의 정책 비교 결과를 검토하고 실제 적용 전에 필요한 시장 프로필 지원 범위를 별도 WBS로 정한다. 실자료 비용이나 선정 정책은 자동 변경하지 않는다.

## 검증 산출물

[기계 판독 검증 기록](conditional-verification-2026-09-14.json)에 입력 해시·코드 해시·실행 상태·로컬 산출물 위치를 남겼다. 최종 예제는 `C:/Users/aeby/AppData/Local/Temp/krx-conditional-final-mzifva7i/experiment/conditional-report.html`이며 상위 폴더의 `report.png`로 Chrome 1800×2400 화면을 확인했다. 표에서 합성 날짜·비용·지연·정책과 상세 장부 링크가 표시된다. 임시 경로는 정리될 수 있으므로 위 fixture 명령으로 다시 생성할 수 있다.
