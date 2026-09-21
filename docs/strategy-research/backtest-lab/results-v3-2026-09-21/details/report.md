# v3 56개 전략 실행 보고서

이 보고서는 기본 청산과 넓은 청산을 따로 비교한다. 이 결과는 확인 가능한 종목만 모은 과거 가격 실험이며 배당금은 넣지 않았다. 제외된 종목 때문에 전체 시장 성과와 다를 수 있고, 전략 선택이나 실제 매매 허가가 아니다.

[쉬운 요약과 비교 그림](../README.md)을 먼저 읽을 수 있다.

## 핵심 판단

- 실행 상태: **COMPLETE**; 시도/계획 **2464/2464** (기준 계획: flat stress 1,904 + 날짜별 실제비용 control 560 = 2,464, 각 실험의 사전 점검은 별도).
- 성공/차단/무거래: **2023/441/33**; 작은 사전 점검: **PASS**. 무거래 33개는 성공 2,023개에 포함된다.
- 검증 연도는 2020~2023의 독립적인 1억 원 창이다. 아래 평균은 하나의 연속 4년 백테스트가 아니다.
- 일부 또는 차단된 실행은 순위와 섞지 않았다. 상위 10개는 결과를 설명하기 위한 표이며 선택 결과가 아니다.

## 범위·입력·미해결

- 확인 가능한 종목 묶음: CLEAN_COHORT_RAW_PRICE_TRADING_RETURN_CASH_DIVIDENDS_EXCLUDED; 포함 종목 수: 1076; 제외: 1711 ([제외 종목 상세](excluded-symbols.json)).
- 입력·실행 확인 파일: 준비 입력 hash `62694d5e96c111618f93b23d6d6e05d3604e8e952ce8ba4ccd28c8fbdc3c9597`; 실행 확인은 batch 폴더의 `execution-admission.json`을 참조.
- 미해결 제한: RETROSPECTIVE_WHOLE_INSTRUMENT_EXCLUSION_BIAS; NOT_FULL_MARKET; CASH_DIVIDENDS_EXCLUDED; HISTORICAL_DATA_OBSERVED_IN_2026; STRATEGY_SELECTION_NOT_ADMITTED.
- 날짜별 비용 가정: Commission is the user-assumed 0.015% per side, truncated below 10 KRW.; Sell tax uses the source total rate without invented tax rounding.; Settlement is T+2 exchange business sessions; calendar resolution belongs to the caller.; Tick returns the legal price increment; fill price/limit rounding belongs to the caller..

## 기본·넓은 청산 대응 비교

동일 진입, 날짜별 v3 비용, delay=1, 네 검증 연도가 모두 성공한 경우만 비교한다. 작은 사전 점검이 통과하지 않으면 성과 표를 만들지 않는다.

| 진입 | 기본 | 넓은 | 기본 평균 | 넓은 평균 | 차이(%포인트) |
| --- | --- | --- | --- | --- | --- |
| BOLLINGER_REENTRY_2 | PCT_3_6 | PCT_8_16 | -2.54% | -0.34% | 2.20%p |
| BOLLINGER_REENTRY_2 | PCT_5_10 | PCT_10_20 | 0.51% | -1.77% | -2.28%p |
| BOLLINGER_REENTRY_2 | ATR_1_5_3 | ATR_3_6 | -3.31% | -0.41% | 2.90%p |
| BOLLINGER_REENTRY_2 | ATR_2_4 | ATR_4_8 | -3.89% | -1.93% | 1.95%p |
| BREAKOUT_20 | PCT_3_6 | PCT_8_16 | -32.76% | -9.74% | 23.02%p |
| BREAKOUT_20 | PCT_5_10 | PCT_10_20 | -17.63% | -3.54% | 14.10%p |
| BREAKOUT_20_RVOL_1_5 | PCT_5_10 | PCT_10_20 | -22.06% | -5.59% | 16.47%p |
| BREAKOUT_60 | PCT_3_6 | PCT_8_16 | -38.37% | -14.63% | 23.74%p |
| BREAKOUT_60 | PCT_5_10 | PCT_10_20 | -21.15% | -9.73% | 11.42%p |
| BREAKOUT_60_RVOL_1_5 | PCT_3_6 | PCT_8_16 | -36.36% | -14.45% | 21.90%p |
| BREAKOUT_60_RVOL_1_5 | PCT_5_10 | PCT_10_20 | -22.66% | -9.99% | 12.67%p |
| CROSS_10_20 | PCT_3_6 | PCT_8_16 | -10.70% | -0.39% | 10.31%p |
| CROSS_10_20 | ATR_2_4 | ATR_4_8 | -4.02% | 2.21% | 6.24%p |
| RSI_REENTRY_30 | PCT_3_6 | PCT_8_16 | -0.01% | -0.19% | -0.18%p |
| RSI_REENTRY_30 | PCT_5_10 | PCT_10_20 | -0.04% | -0.29% | -0.25%p |
| RSI_REENTRY_30 | ATR_1_5_3 | ATR_3_6 | -0.26% | 0.32% | 0.58%p |
| RSI_REENTRY_30 | ATR_2_4 | ATR_4_8 | 0.12% | 0.17% | 0.04%p |
| RSI_REENTRY_40 | PCT_3_6 | PCT_8_16 | -2.29% | -2.98% | -0.69%p |
| RSI_REENTRY_40 | PCT_5_10 | PCT_10_20 | -0.94% | -3.11% | -2.17%p |
| RSI_REENTRY_40 | ATR_1_5_3 | ATR_3_6 | -4.20% | -2.77% | 1.43%p |
| RSI_REENTRY_40 | ATR_2_4 | ATR_4_8 | -3.93% | -2.55% | 1.38%p |

## basic 상위 10개 설명표

완전한 네 독립 연도만 표시하며 선정 순위가 아니다.

| 진입 | 청산 | 평균 연도 수익 | 최악 MDD | 4년 거래 수 |
| --- | --- | --- | --- | --- |
| BOLLINGER_REENTRY_2 | PCT_5_10 | 0.51% | 12.55% | 945 |
| RSI_REENTRY_30 | ATR_2_4 | 0.12% | 0.69% | 19 |
| RSI_REENTRY_30 | PCT_3_6 | -0.01% | 0.08% | 10 |
| RSI_REENTRY_30 | PCT_5_10 | -0.04% | 0.19% | 11 |
| RSI_REENTRY_30 | ATR_1_5_3 | -0.26% | 0.53% | 16 |
| TREND_PULLBACK_3 | ATR_2_4 | -0.75% | 24.89% | 1321 |
| RSI_REENTRY_40 | PCT_5_10 | -0.94% | 7.85% | 786 |
| RSI_REENTRY_40 | PCT_3_6 | -2.29% | 5.51% | 781 |
| BOLLINGER_REENTRY_2 | PCT_3_6 | -2.54% | 6.21% | 1030 |
| MACD_CROSS_SMA60 | PCT_5_10 | -3.18% | 21.27% | 2832 |

## wide 상위 10개 설명표

완전한 네 독립 연도만 표시하며 선정 순위가 아니다.

| 진입 | 청산 | 평균 연도 수익 | 최악 MDD | 4년 거래 수 |
| --- | --- | --- | --- | --- |
| CROSS_10_20 | ATR_4_8 | 2.21% | 23.23% | 1033 |
| BREAKOUT_20 | ATR_4_8 | 1.38% | 15.77% | 1069 |
| RSI_REENTRY_30 | ATR_3_6 | 0.32% | 0.86% | 19 |
| RSI_REENTRY_30 | ATR_4_8 | 0.17% | 0.82% | 19 |
| RSI_REENTRY_30 | PCT_8_16 | -0.19% | 0.49% | 18 |
| RSI_REENTRY_30 | PCT_10_20 | -0.29% | 0.62% | 19 |
| BOLLINGER_REENTRY_2 | PCT_8_16 | -0.34% | 13.49% | 794 |
| CROSS_10_20 | PCT_8_16 | -0.39% | 20.82% | 1679 |
| BOLLINGER_REENTRY_2 | ATR_3_6 | -0.41% | 14.43% | 658 |
| BOLLINGER_REENTRY_2 | PCT_10_20 | -1.77% | 15.90% | 706 |

## 비용·지연 점검

아래는 고정 비용·지연을 바꾼 별도 점검의 성공 실행 평균이다. 성공한 실행 집합이 조건마다 다를 수 있어, 비용의 짝지은 효과나 전략 순위로 해석하지 않는다. 날짜별 비용 결과와도 섞지 않는다.

| 고정 비용(bp) | 지연(일) | 성공 실행 | 평균 수익 |
| --- | --- | --- | --- |
| 10 | 1 | 388 | -6.48% |
| 30 | 1 | 388 | -11.48% |
| 30 | 2 | 391 | -11.23% |
| 50 | 1 | 388 | -16.03% |

날짜별 비용 실행의 검증된 수수료/세금 합계는 각각 **211,638,640원 / 1,727,718,656원**이다. 같은 기간·전략을 여러 번 실행한 합계이므로 하나의 계좌 비용으로 해석하지 않는다.

## 차단·실패 요약

개별 실행 목록을 본문에 모두 넣지 않았다. 원본 실행별 사유는 batch의 `runs/<run-id>/result.json`과 `runs/<run-id>/artifacts.json`에서 확인한다.

| 사유 | 건수 |
| --- | --- |
| UNKNOWN_HELD_MARK:2023-10-20:694 | 58 |
| UNKNOWN_HELD_MARK:2021-04-06:1072 | 52 |
| UNKNOWN_HELD_MARK:2015-11-30:661 | 46 |
| UNKNOWN_HELD_MARK:2022-05-17:268 | 32 |
| UNKNOWN_HELD_MARK:2021-04-01:2756 | 31 |
| UNKNOWN_HELD_MARK:2021-04-14:1284 | 30 |
| UNKNOWN_HELD_MARK:2021-03-08:2926 | 27 |
| UNKNOWN_HELD_MARK:2016-10-20:848 | 24 |
| UNKNOWN_HELD_MARK:2019-03-22:2550 | 22 |
| UNKNOWN_HELD_MARK:2022-03-22:2774 | 18 |
| UNKNOWN_HELD_MARK:2020-04-07:3090 | 16 |
| UNKNOWN_HELD_MARK:2023-12-07:760 | 16 |
| UNKNOWN_HELD_MARK:2021-04-09:476 | 12 |
| UNKNOWN_HELD_MARK:2017-03-27:335 | 10 |
| UNKNOWN_HELD_MARK:2018-08-24:1284 | 10 |
| UNKNOWN_HELD_MARK:2015-09-17:351 | 6 |
| HELD_MARKET_CHANGED:2021-08-09:3467 | 4 |
| UNKNOWN_HELD_MARK:2015-06-25:829 | 4 |
| UNKNOWN_HELD_MARK:2015-11-04:583 | 4 |
| UNKNOWN_HELD_MARK:2017-12-14:269 | 4 |
| UNKNOWN_HELD_MARK:2015-07-10:3148 | 2 |
| UNKNOWN_HELD_MARK:2015-11-05:2531 | 2 |
| UNKNOWN_HELD_MARK:2016-04-25:1118 | 2 |
| UNKNOWN_HELD_MARK:2016-06-16:382 | 2 |
| UNKNOWN_HELD_MARK:2017-05-02:281 | 2 |
| UNKNOWN_HELD_MARK:2017-09-19:349 | 2 |
| UNKNOWN_HELD_MARK:2018-06-01:2911 | 2 |
| UNTRADEABLE_HELD_MARK:2015-07-14:397 | 2 |
| HELD_MARKET_CHANGED:2022-11-03:3344 | 1 |
