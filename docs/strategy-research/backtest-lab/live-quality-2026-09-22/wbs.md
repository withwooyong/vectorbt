# 운영 DB 최신 품질 재점검 WBS

목적: 로컬 자료 점검으로 제한했던 이전 답변을 운영 DB의 현재 조회로 보완한다. 백테스트 역사 구간의 현재 품질과 최신 수집 메타데이터를 구분하며, 2024년 이후 가격값·수익률은 조회하지 않는다. DB는 읽기 전용이며 수집·정정은 하지 않는다.

진행률: **100%**, 완료 **3/3**. 남은 요청 작업 없음. 차단 없음. 전체 시장 인수와 최신 전체 수집 완료 확정은 이번 제한된 감사의 결론이 아니다.

| ID | 산출물 | 담당 | 선행 | 완료 기준 | 가중치 | 상태 |
| --- | --- | --- | --- | --- | ---: | --- |
| W1 | 현재 운영 DB SQL·결과·영수증 | 메인 | 없음 | 읽기 전용·조회시점·완료 확인 | 45 | 완료 |
| W2 | 이전 상태 비교·한국어 보고서·열람용 HTML | 메인 | W1 | 사실·제한·읽을 문서 연결 | 35 | 완료 |
| W3 | 독립 검토·링크 검증 | 검토 에이전트+메인 | W2 | 근거 일치·누락 확인 | 20 | 완료 |

기존 읽기 전용 감사 실행기를 재사용한다. 기존 실행기 영수증의 고정 scope 문자열보다 각 SQL context의 실제 scope를 우선하며 이 차이를 보고서에 명시한다. 기존 사용자 파일과 다른 진행 작업은 수정하지 않는다.

- 5개 감사 완료: data, metadata, current, coverage-r2, lineage. 모두 READ ONLY·REPEATABLE READ와 완료표식 확인. coverage 최초 SQL 별칭 구문 오류는 수정 후 새 evidence 경로에서 재실행했다.
- 독립 검토: 5개 SQL·증거 해시, 이전과의 비교, 누락집계, 가격member 실제 내용 해시 및 보고서 수치·한계 PASS. 중요 미해결 지적 0건.
- HTML 3개 생성 및 로컬 링크 23개 존재 확인, 횟수표 데이터433행+헤더 확인. 정적 검사·git diff --check 통과.
- Orca 로컬 문서 탭 생성 요청은 성공했으나 snapshot 확인은 `runtime_unavailable: The Orca runtime closed the connection before responding`로 실패했다. 브라우저 화면 검증 성공을 주장하지 않으며, 존재 확인한 절대경로의 HTML 링크로 전달한다.
- 렌더 재실행: `.venv/Scripts/python.exe docs/strategy-research/backtest-lab/live-quality-2026-09-22/render_reading.py`. 입력은 README와 기존 해석/횟수 Markdown, 출력은 report.html/results.html/counts.html이다. 로컬 출력만 갱신하고 외부 전송하지 않는다.
