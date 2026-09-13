# 국내 주식 일괄 전략 연구 도구

48개 기술전략의 TP/SL·최대 달력 1개월·공동 1억 원 계좌를 계산하고 실행·장부·선정 사유를 저장하는 **연구 핵심 구현**이다. 현재 실제 PostgreSQL 자료는 가격·상태 인수 실패로 수익률 실행이 차단된다. 합성 자료의 엔진 검증을 투자 성과로 해석하지 않는다.

[현재 결과·실행 안내](../../docs/strategy-research/backtest-lab/implementation-and-results-2026-09-13.md), [전체 명세](../../docs/strategy-research/backtest-lab/technical-spec.md), [남은 작업](../../docs/strategy-research/backtest-lab/wbs.md)을 따른다. 이 패키지는 저장소 루트에서 실행하며 vectorbt 공개 배포 API를 변경하지 않는다.

```powershell
uv pip install --python .venv -r research/krx_lab/requirements.txt
.venv/Scripts/python.exe -X utf8 -m research.krx_lab --help
.venv/Scripts/python.exe -X utf8 -m pytest tests/research -q
```

`snapshot → config → plan → run → report/select`가 기본 순서다. `resume`은 같은 코드·설정·입력에서만 재개한다. `diagnose`는 실제 자료의 지표 준비와 신호 빈도만 조사한다. `freeze/finalize`와 실제 투자 후보 승격은 원가격·기업행사·현실 비용·후속 단계 구현 전까지 차단한다. 증권사 주문·뉴스 AI 호출 기능은 없다.
