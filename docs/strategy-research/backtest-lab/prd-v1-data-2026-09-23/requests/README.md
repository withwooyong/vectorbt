# ted-startup 원천 수정·통지 요청 목록

이 디렉터리는 `../README.md`(PRD v1 데이터 정리)에서 이 리포(소비자)가 발견한 원천 결함을 ted-startup 에 넘기기 위한 작업요청서다. 이 리포는 요청서 작성만 했고, ted-startup 전달은 사용자가 한다. 이 문서를 외부에 전송하지 않았다. 전체 데이터 인수는 현재 `BLOCKED` 다.

| ID | 요청 | 원천 테이블 | 이 리포 쪽 근거 | 상태 |
| --- | --- | --- | --- | --- |
| R1 | 거래세 규칙 2014년 공백·경계 기준 수정 | `kiwoom.backtest_execution_rule_v2` | `../README.md` B2b 절, `../rules_effective_date_table.py` | 요청서 작성 완료 |
| R2 | 미귀속 이슈 1,523행에 종목·일 귀속 키 부여 | `kiwoom.backtest_admission_issue_v2` | `../README.md` B1 절, `../universe_diagnosis.py` | 요청서 작성 완료 |
| R3 | 상장·폐지·거래정지 원천 공백 통지(수정 요청 아님) | `kiwoom.stock`·`instrument_history`·`market_status_event`·`trading_halt` | `../README.md` B1b 절 | 요청서 작성 완료 |

표가 말하는 것: R1·R2 는 원천 값 자체의 수정을 요청하고, R3 는 원천에 없는 이력을 채워 달라는 통지이며 이 리포가 정답을 고르지 않는다.

각 요청서는 확보할 자료와 성공 조건을 표로 두고, 기계 판독 첨부(JSON/CSV)를 함께 둔다.
