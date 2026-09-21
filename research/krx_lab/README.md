# 국내 주식 일괄 전략 연구 도구

48개 기술전략의 TP/SL·최대 달력 1개월·공동 1억 원 계좌를 계산하고 실행·장부·선정 사유를 저장하는 **연구 핵심 구현**이다. 현재 REAL 수익률 실행은 입력 검증·실제 체결 계약이 미완료여서 차단된다. 합성 자료의 엔진 검증을 투자 성과로 해석하지 않는다.

[현재 결과·실행 안내](../../docs/strategy-research/backtest-lab/implementation-and-results-2026-09-13.md), [전체 명세](../../docs/strategy-research/backtest-lab/technical-spec.md), [남은 작업](../../docs/strategy-research/backtest-lab/wbs.md)을 따른다. 이 패키지는 저장소 루트에서 실행하며 vectorbt 공개 배포 API를 변경하지 않는다.

```powershell
uv pip install --python .venv -r research/krx_lab/requirements.txt
.venv/Scripts/python.exe -X utf8 -m research.krx_lab --help
.venv/Scripts/python.exe -X utf8 -m pytest tests/research -q
```

`snapshot → config → plan → run → report/select`가 기본 순서다. `resume`은 같은 코드·설정·입력에서만 재개한다. `diagnose`는 실제 자료의 지표 준비와 신호 빈도만 조사한다. `freeze/finalize`는 해시로 연결된 합성 증거의 상태 검증에 사용할 수 있다. 실제 투자 후보 승격과 잠금 구간 접근은 계속 차단한다. 증권사 주문·뉴스 AI 호출 기능은 없다.


2026-09-14에는 데이터 전달 형식 검사, 합성 기업행사 장부, 후보 고정 증거, 자원 감시와 상세 HTML을 추가했다. [개발 결과와 한계](../../docs/strategy-research/backtest-lab/implementation-results-2026-09-14.md), [입력·장부·상태 계약](../../docs/strategy-research/backtest-lab/contracts-v1.md)을 함께 확인한다. 데이터 수집·정정은 ted-startup에서 담당한다.

```powershell
# 저장소 공통 합성 입력의 형식·원문 파일 대조
.venv/Scripts/python.exe -X utf8 -m research.krx_lab inspect-delivery --delivery tests/research/fixtures/contracts_v1/delivery.json
# 신규 경로와 신호 입력 형식은 아래 명령 및 test_integration.py 참고
.venv/Scripts/python.exe -X utf8 -m research.krx_lab run-delivery --help
.venv/Scripts/python.exe -X utf8 -m research.krx_lab freeze --help
.venv/Scripts/python.exe -X utf8 -m research.krx_lab finalize --help
```

`run-delivery`는 합성 입력과 원가격 단위 신호 JSON을 받아 새 출력 디렉터리에 장부·독립 대조·상세 보고를 저장하는 일회 실행이다. 이 경로의 중단 후에는 새 디렉터리로 다시 실행한다. 기존 `run/resume` 배치는 동일 실험에서 attempt 이력을 보존하며 재개한다. 코드가 바뀌면 기존 실험 해시를 고치지 말고 새 실험을 만든다.

기본 자원 감시는 RSS 2 GiB, 디스크 여유 512 MiB, 샘플 주기 0.25초이며 체크포인트에서 협력 중단한다. 관측 사이의 초과나 단일 연산의 최대 메모리를 OS 수준에서 보장하지 않는다. 실험 설정의 `resource_limits`와 Python API의 `ResourceLimits`로 조정할 수 있다. 현재 파일 내용 검사는 합성 JSON 스키마만 지원하며, 실제 데이터 사용 적격성 판단은 별도 작업이다. 후속 33슬롯의 합성 실행 연결은 아래 별도 경로를 사용한다.

후속 33슬롯은 별도 `conditional-plan → conditional-run → conditional-status` 경로로 합성 검증한다. [합성 후속 실행 안내](../../docs/strategy-research/backtest-lab/conditional-results-2026-09-14.md)의 입력 생성·명령과 한계를 따른다. 기본 실행은 선행 26개만 수행하고 나머지 합성 잠금 7개는 명시 옵션과 선행 결과 검증을 요구한다. 실제 잠금 데이터 접근 기능은 제공하지 않는다.

2026-09-18에 `inspect-real`을 추가했다. ted-startup이 전달한 REAL 형식 데이터의 C1 검사 결과와 근거 공백을 별도 JSON으로 기록한다. **결과는 항상 `BLOCKED`이며 수익률 실행을 열지 않는다.** 입력·출력 경로, 실패 처리와 실자료 실행까지의 단계는 [48개 전략과 실자료 전환 계획](../../docs/strategy-research/backtest-lab/strategy-catalog-and-real-data-plan-2026-09-18.md#6-현재-사용할-수-있는-vectorbt-입력-점검-명령)을 따른다.

실자료 도착 전 오프라인 준비용 Python 함수는 `real_signals.prepare_real_signals`, `real_profile.precheck_real_daily_profile`, `local_slice.load_snapshot_window`다. 앞의 두 함수는 REAL C1 고정 표본의 조정가격 신호와 시장 프로필 문제를 각각 확인하며, 마지막 함수는 해시 검증된 로컬 Parquet 스냅샷의 필요한 기간·종목·열을 읽는다. 모두 읽기 전용이며 REAL 주문·수익률 실행 권한을 주지 않는다. C1 인라인 가격의 전체 시장 규모 처리는 검증되지 않았으므로 [오프라인 준비 WBS](../../docs/strategy-research/backtest-lab/real-execution-offline-wbs-2026-09-18.md)의 범위를 확인한다.
