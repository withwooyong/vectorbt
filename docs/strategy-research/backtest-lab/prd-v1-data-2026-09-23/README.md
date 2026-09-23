# B1·B2 데이터 정리 결과

기준 문서: [PRD v1 실행 계획](../prd-v1-plan-2026-09-23.md)
작성일: 2026-09-23

재실행 명령(리포 루트 기준):

```
.venv/Scripts/python -X utf8 docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/universe_diagnosis.py \
    --prepared-dir ../vectorbt-data/krx-v3-20260921-prepared-r2 \
    --tables-dir ../vectorbt-data/krx-v3-20260921-tables \
    --out docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/universe-diagnosis.json
```

실행 시간은 5.1초([`universe-diagnosis.json`](universe-diagnosis.json)의 `runtime_seconds`)이고, `date_cutoff.saw_rows_on_or_after_cutoff` 가 `false` 이므로 2024-01-01 이후 행은 집계에 들어가지 않았다.

## B1 Universe 진단 결과

로컬 Parquet 8개 테이블에는 `security_type`·2014년 이전 상장일·상장폐지 플래그·일별 거래상태가 없다. 이 필드는 PostgreSQL 뷰 `backtest_universe_v2` 에서만 가져온다(`research/krx_lab/v3_inputs.py:23,133`, `research/krx_lab/v3_snapshot.py:27`). 따라서 PRD §5.3 기준 일별 Universe 는 현재 로컬 자료로 계산할 수 없다.

| 항목 | 수치 |
| --- | --- |
| 원가 종목 수 | 2,787종목 |
| 수정가 종목 수 | 2,312종목 |
| cohort 종목 수 | 1,076종목 |
| 원가 기준 누락 종목 | 1,711종목 |
| 1차 사유: 수정가 부재(데이터 결함) | 475종목 |
| 1차 사유: 250봉 부족(이전 전략 자격) | 52종목 |
| 1차 사유: 이슈 기록 없음(원인 미확인) | 1,184종목 |

표가 말하는 것: 누락 1,711종목 중 사유가 밝혀진 것은 527종목뿐이고, 나머지 1,184종목은 `universe-diagnosis.json` 에도 원인 코드가 없다.

이슈 귀속에는 한계가 있다. `issues.parquet` 2,304행 중 종목에 매핑되는 것은 781행(34%)뿐이다. 나머지 1,523행(미설명 수정계수 1,061건·수정 OHLC 순서 위반 284건·기업행사 부분 160건 등)은 `affected_scope` 가 날짜·사건 단위 라벨이라 종목에 귀속할 수 없다. 그래서 위 1,184종목의 원인이 이 1,523행 안에 섞여 있을 수 있다.

상장폐지는 직접 플래그가 없다. 데이터 종료일보다 90일 이상 앞서 원가가 끊긴 종목이 284개이지만, 이 신호만으로는 상장폐지와 데이터 절단(수집 중단)을 구분하지 못한다.

원가 OHLC≤0 135,717행 중 거래량 0 으로 설명되는 행은 135,699건, 설명되지 않는 행은 18건이다. 이 수치는 `postgresql-readiness-2026-09-21/README.md` 의 PostgreSQL 보고서 수치와 일치한다.

참고 근사치(PRD 비준수, 의사결정에 쓰지 말 것): 원가 관측 종목 수는 연 평균 2014년 1,727종목에서 2023년 2,433종목으로 늘었다. 이 수치는 상장·상장폐지를 반영하지 않은 연도별 단순 관측 카운트다.

## B2 비용·거래 규칙 효력일 이력

| 항목 | 시장 | 효력일(양도분 기준) | 값 | 출처 | 신뢰도 |
| --- | --- | --- | --- | --- | --- |
| 증권거래세 | KOSPI | ~2019-06-02 | 0.15% | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 증권거래세 | KOSPI | 2019-06-03 | 0.10% | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 증권거래세 | KOSPI | 2021-01-01 | 0.08% | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 증권거래세 | KOSPI | 2023-01-01 | 0.05% | [세무사신문](https://webzine.kacta.or.kr/news/articleView.html?idxno=24018) | 2차 |
| 증권거래세 | KOSPI | 2024-01-01 | 0.03% | [김앤장 인사이트](https://www.kimchang.com/ko/insights/detail.kc?sch_section=4&idx=26868) | 2차 |
| 증권거래세 | KOSPI | 2025-01-01 | 0% | [한국세정신문](https://taxtimes.co.kr/news/article.html?no=272624) | 2차 |
| 증권거래세 | KOSPI | 2026-01-01 | 0.05% | [부산일보](https://www.busan.com/view/busan/view.php?code=2025120110150624521) | 2차 |
| 증권거래세 | KOSDAQ | ~2019-06-02 | 0.30% | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 증권거래세 | KOSDAQ | 2019-06-03 | 0.25%(추정) | 아래 교차 확인 참고 | 2차 |
| 증권거래세 | KOSDAQ | 2021-01-01 | 0.23%(추정) | 아래 교차 확인 참고 | 2차 |
| 증권거래세 | KOSDAQ | 2023-01-01 | 0.20% | [세무사신문](https://webzine.kacta.or.kr/news/articleView.html?idxno=24018) | 2차 |
| 증권거래세 | KOSDAQ | 2024-01-01 | 0.18% | [김앤장 인사이트](https://www.kimchang.com/ko/insights/detail.kc?sch_section=4&idx=26868) | 2차 |
| 증권거래세 | KOSDAQ | 2025-01-01 | 0.15% | [한국세정신문](https://taxtimes.co.kr/news/article.html?no=272624) | 2차 |
| 증권거래세 | KOSDAQ | 2026-01-01 | 0.20% | [부산일보](https://www.busan.com/view/busan/view.php?code=2025120110150624521) | 2차 |
| 농어촌특별세 | KOSPI | 전 기간(변경 이력 미확인) | 매도분 0.15% | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 농어촌특별세 | KOSDAQ | 해당 없음 | 부과 안 됨 | [법령 개정이력](https://www.law.go.kr/LSW/lsRvsDocListP.do?lsId=005028&chrClsCd=010102) | 2차 |
| 가격제한폭 | KOSPI·KOSDAQ 공통 | 2015-06-15 | ±15% → ±30% | [한국일보](https://www.hankookilbo.com/news/article/201506150972717505) | 2차 |
| 호가가격단위 | KOSPI·KOSDAQ 통일 | 2023-01-25 | 1천~2천원 미만 5→1원, 1만~2만원 미만 50→10원, 10만~20만원 미만 500→100원(2014~2022 변경 여부 미확인) | [이투데이](https://m.ekn.kr/view.php?key=20230117010003826) | 2차 |
| 위탁수수료(참고) | 공통 | 확인 필요 | 비대면 약 0.011~0.018%, 거래소·예탁원 유관기관수수료가 양방향 별도 부과 | [미래에셋증권](https://securities.miraeasset.com/imf/200/imf606.do) | 2차 |

표가 말하는 것: 2014~2023 구간의 증권거래세율은 하락 추세로 확정되며, 위 값 그대로 PRD 백테스트 기간(2014~2023)의 비용표에 쓸 수 있다. 2024년 이후 행은 참고용이며 이 리포의 백테스트 범위 밖이다.

교차 확인 요점: KOSPI(거래세+농특세) 합계와 KOSDAQ 세율이 2014~2023 모든 구간에서 같다(0.30% → 0.25% → 0.23% → 0.20%). 이것이 KOSDAQ 추정값 두 개(2019-06-03, 2021-01-01)를 뒷받침한다.

한계: 법령 조문 원문은 열람에 실패했고, 세율은 개정이력 목록과 언론 교차 확인에 의존한다.
