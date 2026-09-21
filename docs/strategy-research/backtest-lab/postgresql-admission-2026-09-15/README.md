# PostgreSQL 재인수 결과: 운영 정정 완료와 연구 인수는 별도 기준이다

2026-09-15 17:01 KST home PostgreSQL을 읽기 전용으로 재검사했다. **운영 정정 완료 안내를 확인했지만, 2015~2023 연구 입력 인수는 `BLOCKED`다.** 수정주가의 거래 행에 가격 0 이하가 699행 남아 있으며 납품 revision·원문 해시·역사 입력의 연결도 확인되지 않았다. 이번 산출물은 인수 진단이며 실제 수익률 실행·전략 선정·2024년 이후 가격 열람은 하지 않았다.

## 핵심 차단 요인과 완료 범위

ted-startup 최신 HANDOFF는 signal 이관 구간의 수정주가 정정 7,927행 완료와 미설명 4행을 보고한다. vectorbt의 연구 입력은 `kiwoom.stock_price_krx`의 **모든 공급자, 2015-01-02~2023-12-31 수정주가**이므로 다른 모집단이다. 운영 완료 기록 자체를 부정하는 결과로 해석하지 않는다.

아래 표는 거래 가능한 것으로 표시된 수정주가 중 실행에 부적합한 가격을 비교한다. 상태 이름만으로 가격 품질을 통과시키면 안 된다.

| 공급자·종목 | 거래 행의 가격 0 이하 | 관측 | 판단 |
| --- | ---: | --- | --- |
| KIWOOM `102950` | 695 | 2015-01-20~2019-11-28, 종가 0, 거래량 양수 | 원문·단위·조정 정밀도와 저장값 대조 필요 |
| KRX `015540`, `016385`, `053870`, `141070` | 4 | 각 1행, 종가 양수, 일부 OHL 0 | 원가격·공식 상태 근거와 적용 정책 필요 |
| 합계 | **699** | 수정주가 `TRADED` 행 | 실제 실행 인수 차단 |

- 수정주가 총 6,109,214행이며, `TRADED`는 5,897,591행이다. 가격 0 이하 699행을 종목 전체 제외·전일 값 채움으로 우회하지 않는다.
- 원가격은 현재 KRX 544,241행이고 `TRADED` 중 가격 0 이하 13행이 있다. KIWOOM 원가격은 이번 기간별 집계에 나타나지 않는다. 모든 수정주가에 원가격이 연결됐다는 증거는 아니다.
- `HALTED`·`NO_TRADE`의 0 가격·OHLC 역전은 거래 행 오류와 분리했다. 상태별 공식 근거 검증 전에는 자동 삭제하거나 정상 자료로 인수하지 않는다.
- DB 테이블 목록에는 `trading_halt`가 추가돼 있다. 하지만 기업행사·공식 거래일·역사 종목 정체성·조정계수·납품 revision의 계약 연결은 이번 조사에서 확인하지 못했다. 다른 DB·외부 파일에 없다고 단정하지 않는다.
- 탐색 에이전트는 ted-startup의 전달 형식이 운영 문서·CLI 로그·SQL 검증임을 확인했다. 계약 v1의 dataset_id/revision과 SHA-256 파일 manifest는 해당 최신 산출물에서 확인되지 않았다.

## 다음 작업과 담당 경계

**권장:** ted-startup에서 699개 수정주가 영향 키의 원문·단위·조정 정의 및 근거 있는 정정/분류를 새 revision으로 납품하고, 기존 [재납품 명세](../remediation-discovery-2026-09-14/delivery-spec.md)의 역사 입력과 파일 계보를 함께 연결한다. 여기서는 자료 수집·적재·정정을 실행하지 않았으며 외부 메시지도 전송하지 않았다.

납품이 준비되면 실제 형식용 읽기 전용 어댑터를 구현한다. 기존 `admission.py`의 내용 검사는 `synthetic-source-v1`에 한정되므로 실제 자료를 합성으로 표시해 통과시키지 않는다. 699행 해소만으로 인수 완료를 선언하지 않고 공식 상태·거래일·기업행사·현실 비용과 잠금 정책을 확인한다. 그 후 2015~2023 개발·검증 실행을 진행하고 후보·정책을 고정한 다음 최종 구간을 검토한다.

## 재현 명령과 근거

기존 감사 runner에 선택적 `--sql` 입력을 추가해 재사용했다. 입력 SQL은 검토된 읽기 전용 SQL이어야 하며, 이번 두 SQL은 가격 조건을 2015~2023으로 제한한다. 기존 출력 경로는 덮어쓸 수 없고 실패 시 stderr·영수증을 남긴다. 출력은 SQL 사본·stdout/stderr·결과 JSON·SHA-256 영수증이다. SQL 임의 입력을 허용하는 기능 자체가 기간 조건을 자동 증명하지는 않는다.

```powershell
.venv/Scripts/python.exe -X utf8 docs/strategy-research/backtest-lab/table-audit-2026-09-13/run_audit.py core --sql docs/strategy-research/backtest-lab/postgresql-admission-2026-09-15/core.sql --out "$env:LOCALAPPDATA/vectorbt-research/admission-core-new"
.venv/Scripts/python.exe -X utf8 docs/strategy-research/backtest-lab/table-audit-2026-09-13/run_audit.py core --sql docs/strategy-research/backtest-lab/postgresql-admission-2026-09-15/affected.sql --out "$env:LOCALAPPDATA/vectorbt-research/admission-affected-new"
.venv/Scripts/python.exe -X utf8 -m pytest docs/strategy-research/backtest-lab/table-audit-2026-09-13/test_run_audit.py -q
```

- [전수 집계](evidence/core/results.json), [집계 영수증](evidence/core/receipt.json): 읽기 전용 확인, 6검사 완료, 7.984초.
- [영향 종목·전체 키](evidence/affected/results.json), [영향 키 영수증](evidence/affected/receipt.json): 4검사 완료, 2.042초. 첫 집계의 예시 100행 제한과 달리 전체 영향 키를 보존한다.
- 기존 runner 회귀: **9 passed**. 실제 DB 조회 성공은 원천 정확성 증명이 아니다. 전체 연구 테스트·제품 테스트·Rust·사이트 빌드는 인수 진단 범위 밖이다.
- 독립 검토 Sol high: **Critical 0 / Major 0**. 수치·전체 키 중복 없음·기간·stdout/JSON·해시를 확인하고 9회귀를 재현했다. 기존 감사 runner는 미추적 파일이어서 HEAD diff 검토는 불가능했으며 현재 코드와 산출물을 검토했다. 메인은 Ruff·공백·로컬 링크 6개 검사를 통과했다.
- ted-startup 근거: `C:/Users/aeby/vscode/ted-startup/HANDOFF.md`, `docs/superpowers/specs/2026-09-14-price-data-quality-design.md`, `docs/superpowers/plans/2026-09-13-backtest-period-extension-verification.md`.
