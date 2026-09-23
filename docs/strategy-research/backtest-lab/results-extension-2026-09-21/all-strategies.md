# 전략별 성과와 실제 매수·매도 횟수

매수·매도는 주문 제출이 아닌 실제 체결 건수다. 미청산 보유 때문에 두 수가 다를 수 있다. BLOCKED 행의 횟수는 중단 전 부분 기록이며 완결 성과와 비교하지 않는다. 수익률은 비용 차감·현금배당 제외다. 연도별 계좌는 독립이고 continuous는 4년 연속 누적수익률이다. 개발기간은 별도다.

| 전략군 | 매수 조건 | 청산 기준 | 최대개월 | 기간 | 상태 | 수익률 | 최대낙폭 | 매수체결 | 매도체결 | 종료거래 | 평균보유일 | 미청산종목 | 횟수범위 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| basic | CROSS_5_20 | PCT_3_6 | 1 | development | SUCCEEDED | -44.75% | 47.00% | 4973 | 4957 | 4957 | 4.3 | 16 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -14.91% | 15.78% | 1170 | 1156 | 1156 | 3.01 | 14 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -10.63% | 13.68% | 1216 | 1200 | 1200 | 3.84 | 16 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 1 | year_2022 | BLOCKED | — | — | 288 | 272 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -19.17% | 21.96% | 1119 | 1106 | 1106 | 4.34 | 13 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 2648 | 2632 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | PCT_3_6 | 3 | development | SUCCEEDED | -43.57% | 45.68% | 4864 | 4848 | 4848 | 4.45 | 16 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -15.30% | 15.86% | 1153 | 1137 | 1137 | 3.01 | 16 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -10.42% | 13.15% | 1194 | 1177 | 1177 | 3.95 | 17 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 3 | year_2022 | BLOCKED | — | — | 284 | 268 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -16.94% | 19.78% | 1090 | 1076 | 1076 | 4.43 | 14 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 2599 | 2583 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | PCT_3_6 | 6 | development | SUCCEEDED | -43.51% | 45.63% | 4861 | 4845 | 4845 | 4.45 | 16 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -15.30% | 15.86% | 1153 | 1137 | 1137 | 3.01 | 16 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -10.42% | 13.15% | 1194 | 1177 | 1177 | 3.95 | 17 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 6 | year_2022 | BLOCKED | — | — | 284 | 268 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -16.94% | 19.78% | 1090 | 1076 | 1076 | 4.43 | 14 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_3_6 | 6 | continuous_2020_2023 | BLOCKED | — | — | 2599 | 2583 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | PCT_5_10 | 1 | development | SUCCEEDED | -19.79% | 27.00% | 2818 | 2799 | 2799 | 9.8 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 6.42% | 8.61% | 718 | 698 | 698 | 6.66 | 20 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | 0.37% | 8.68% | 695 | 676 | 676 | 8.46 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -21.56% | 21.74% | 708 | 694 | 694 | 7.95 | 14 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -6.91% | 12.24% | 647 | 627 | 627 | 9.51 | 20 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -22.26% | 34.09% | 2739 | 2719 | 2719 | 8.31 | 20 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 3 | development | BLOCKED | — | — | 516 | 497 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 7.45% | 8.61% | 678 | 659 | 659 | 6.83 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | -2.98% | 9.40% | 605 | 586 | 586 | 9.85 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -21.40% | 21.58% | 638 | 625 | 625 | 8.89 | 13 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -3.13% | 10.19% | 543 | 523 | 523 | 11.12 | 20 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -17.50% | 30.64% | 2436 | 2416 | 2416 | 9.41 | 20 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 6 | development | BLOCKED | — | — | 519 | 500 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 7.66% | 8.61% | 676 | 657 | 657 | 6.82 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | -2.91% | 9.33% | 604 | 585 | 585 | 9.86 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -20.42% | 20.60% | 621 | 607 | 607 | 9.19 | 14 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -2.33% | 9.14% | 535 | 515 | 515 | 11.05 | 20 | FULL_WINDOW |
| basic | CROSS_5_20 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -16.00% | 29.24% | 2408 | 2388 | 2388 | 9.49 | 20 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 744 | 729 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 14.83% | 16.29% | 538 | 520 | 520 | 10.34 | 18 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_1_5_3 | 1 | year_2021 | SUCCEEDED | -0.02% | 11.40% | 589 | 570 | 570 | 10.32 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -32.98% | 33.13% | 561 | 548 | 548 | 10.75 | 13 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_1_5_3 | 1 | year_2023 | BLOCKED | — | — | 464 | 447 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_1_5_3 | 1 | continuous_2020_2023 | BLOCKED | — | — | 2120 | 2103 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 632 | 614 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 13.10% | 16.29% | 472 | 453 | 453 | 11.74 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_1_5_3 | 3 | year_2021 | SUCCEEDED | 1.69% | 12.51% | 524 | 505 | 505 | 11.61 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -26.89% | 28.35% | 488 | 474 | 474 | 12.31 | 14 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_1_5_3 | 3 | year_2023 | BLOCKED | — | — | 397 | 380 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_1_5_3 | 3 | continuous_2020_2023 | BLOCKED | — | — | 1830 | 1813 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 613 | 595 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | 14.21% | 16.29% | 468 | 450 | 450 | 11.84 | 18 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_1_5_3 | 6 | year_2021 | SUCCEEDED | 1.74% | 12.52% | 522 | 503 | 503 | 11.66 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -26.78% | 28.24% | 487 | 473 | 473 | 12.33 | 14 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_1_5_3 | 6 | year_2023 | BLOCKED | — | — | 395 | 378 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_1_5_3 | 6 | continuous_2020_2023 | BLOCKED | — | — | 1803 | 1786 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_2_4 | 1 | development | BLOCKED | — | — | 198 | 179 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 9.91% | 17.95% | 413 | 393 | 393 | 14.96 | 20 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_2_4 | 1 | year_2021 | SUCCEEDED | -3.45% | 16.14% | 431 | 412 | 412 | 15.62 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -26.02% | 26.20% | 405 | 387 | 387 | 16.21 | 18 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_2_4 | 1 | year_2023 | BLOCKED | — | — | 342 | 326 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_2_4 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1551 | 1535 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_2_4 | 3 | development | BLOCKED | — | — | 140 | 122 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 7.78% | 17.55% | 298 | 278 | 278 | 20.74 | 20 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | 6.76% | 15.47% | 335 | 316 | 316 | 19.41 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -17.50% | 19.83% | 305 | 286 | 286 | 21.31 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_2_4 | 3 | year_2023 | BLOCKED | — | — | 260 | 245 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_2_4 | 3 | continuous_2020_2023 | BLOCKED | — | — | 1135 | 1120 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_2_4 | 6 | development | BLOCKED | — | — | 139 | 119 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 9.33% | 17.55% | 276 | 256 | 256 | 20.93 | 20 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | 6.36% | 15.35% | 317 | 298 | 298 | 19.98 | 19 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -18.17% | 19.54% | 284 | 266 | 266 | 22.93 | 18 | FULL_WINDOW |
| basic | CROSS_5_20 | ATR_2_4 | 6 | year_2023 | BLOCKED | — | — | 254 | 239 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_5_20 | ATR_2_4 | 6 | continuous_2020_2023 | BLOCKED | — | — | 1059 | 1044 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | PCT_3_6 | 1 | development | SUCCEEDED | -37.99% | 41.00% | 4710 | 4693 | 4693 | 4.36 | 17 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -9.45% | 12.13% | 1124 | 1109 | 1109 | 2.83 | 15 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -7.34% | 11.95% | 1211 | 1201 | 1201 | 3.7 | 10 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -18.01% | 18.07% | 1120 | 1113 | 1113 | 3.48 | 7 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -8.01% | 14.83% | 1159 | 1140 | 1140 | 4.01 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -37.73% | 39.59% | 4596 | 4577 | 4577 | 3.58 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 3 | development | SUCCEEDED | -35.78% | 39.11% | 4597 | 4580 | 4580 | 4.55 | 17 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -9.09% | 12.04% | 1113 | 1098 | 1098 | 2.86 | 15 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -6.05% | 11.41% | 1187 | 1176 | 1176 | 3.83 | 11 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -17.86% | 17.92% | 1089 | 1082 | 1082 | 3.68 | 7 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -6.13% | 14.02% | 1097 | 1080 | 1080 | 4.36 | 17 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -35.18% | 37.77% | 4453 | 4436 | 4436 | 3.77 | 17 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 6 | development | SUCCEEDED | -35.85% | 39.02% | 4592 | 4575 | 4575 | 4.55 | 17 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -9.09% | 12.04% | 1113 | 1098 | 1098 | 2.86 | 15 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -6.05% | 11.41% | 1187 | 1176 | 1176 | 3.83 | 11 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -17.64% | 17.70% | 1087 | 1080 | 1080 | 3.72 | 7 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -6.22% | 14.02% | 1096 | 1079 | 1079 | 4.28 | 17 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -35.07% | 37.60% | 4450 | 4433 | 4433 | 3.76 | 17 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 1 | development | BLOCKED | — | — | 1165 | 1145 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 4.45% | 9.57% | 717 | 702 | 702 | 6.55 | 15 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | 0.96% | 13.06% | 676 | 657 | 657 | 8.7 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 1 | year_2022 | BLOCKED | — | — | 165 | 146 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -10.01% | 15.58% | 594 | 575 | 575 | 10.49 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1532 | 1513 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | PCT_5_10 | 3 | development | BLOCKED | — | — | 1018 | 999 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 5.82% | 9.56% | 654 | 638 | 638 | 7.0 | 16 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | 1.99% | 12.31% | 605 | 587 | 587 | 9.78 | 18 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -16.62% | 19.00% | 586 | 578 | 578 | 9.51 | 8 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | 1.22% | 6.56% | 470 | 451 | 451 | 13.0 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -4.93% | 23.74% | 2255 | 2236 | 2236 | 10.08 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 6 | development | BLOCKED | — | — | 998 | 978 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 5.22% | 9.56% | 647 | 630 | 630 | 6.95 | 17 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | 2.53% | 11.77% | 600 | 582 | 582 | 9.89 | 18 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -16.07% | 18.84% | 588 | 580 | 580 | 9.43 | 8 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | 1.65% | 6.20% | 458 | 439 | 439 | 13.23 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -4.47% | 23.23% | 2232 | 2213 | 2213 | 10.16 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 1012 | 994 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 6.19% | 13.54% | 575 | 555 | 555 | 9.4 | 20 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 1 | year_2021 | SUCCEEDED | 10.36% | 12.72% | 583 | 567 | 567 | 10.7 | 16 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 1 | year_2022 | BLOCKED | — | — | 129 | 111 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -5.37% | 12.11% | 543 | 524 | 524 | 11.61 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1268 | 1250 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 858 | 841 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 5.02% | 13.54% | 478 | 459 | 459 | 11.88 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 3 | year_2021 | SUCCEEDED | 9.60% | 11.28% | 506 | 490 | 490 | 12.35 | 16 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -26.77% | 26.82% | 459 | 446 | 446 | 12.28 | 13 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | 0.79% | 10.10% | 429 | 410 | 410 | 14.37 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 3 | continuous_2020_2023 | SUCCEEDED | -16.73% | 34.01% | 1834 | 1815 | 1815 | 13.22 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 844 | 826 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | 4.18% | 13.54% | 448 | 429 | 429 | 12.93 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 6 | year_2021 | SUCCEEDED | 8.77% | 11.18% | 500 | 484 | 484 | 12.54 | 16 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -27.30% | 27.36% | 453 | 440 | 440 | 12.52 | 13 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -1.99% | 11.07% | 421 | 402 | 402 | 14.1 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_1_5_3 | 6 | continuous_2020_2023 | SUCCEEDED | -16.64% | 35.25% | 1779 | 1760 | 1760 | 13.58 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 1 | development | BLOCKED | — | — | 208 | 188 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 5.96% | 15.49% | 417 | 399 | 399 | 14.31 | 18 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 1 | year_2021 | SUCCEEDED | 5.36% | 17.03% | 441 | 426 | 426 | 15.13 | 15 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -27.08% | 27.38% | 418 | 405 | 405 | 14.75 | 13 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -0.33% | 11.44% | 410 | 390 | 390 | 16.48 | 20 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 1 | continuous_2020_2023 | SUCCEEDED | -16.36% | 38.48% | 1659 | 1639 | 1639 | 15.38 | 20 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 3 | development | BLOCKED | — | — | 524 | 505 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 9.25% | 15.69% | 314 | 296 | 296 | 20.12 | 18 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | 7.31% | 17.38% | 349 | 331 | 331 | 18.8 | 18 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -26.20% | 26.26% | 286 | 272 | 272 | 20.54 | 14 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -0.12% | 9.62% | 269 | 249 | 249 | 24.04 | 20 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 3 | continuous_2020_2023 | BLOCKED | — | — | 1136 | 1119 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | CROSS_10_20 | ATR_2_4 | 6 | development | SUCCEEDED | -25.35% | 31.96% | 1181 | 1162 | 1162 | 26.08 | 19 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 4.20% | 15.69% | 277 | 259 | 259 | 22.27 | 18 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | 5.75% | 18.75% | 333 | 315 | 315 | 19.8 | 18 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -26.98% | 27.04% | 264 | 250 | 250 | 23.1 | 14 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | 1.63% | 9.93% | 269 | 249 | 249 | 23.16 | 20 | FULL_WINDOW |
| basic | CROSS_10_20 | ATR_2_4 | 6 | continuous_2020_2023 | SUCCEEDED | -16.16% | 35.37% | 1064 | 1044 | 1044 | 24.45 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 1 | development | SUCCEEDED | -90.26% | 90.34% | 7228 | 7208 | 7208 | 2.96 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -38.68% | 39.86% | 2209 | 2197 | 2197 | 1.51 | 12 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -31.61% | 32.09% | 1749 | 1736 | 1736 | 2.62 | 13 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -30.22% | 30.22% | 1585 | 1575 | 1575 | 2.67 | 10 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -30.53% | 32.50% | 1646 | 1633 | 1633 | 2.81 | 13 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -82.55% | 82.65% | 7169 | 7156 | 7156 | 2.36 | 13 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 3 | development | SUCCEEDED | -89.49% | 89.60% | 7051 | 7031 | 7031 | 3.06 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -38.42% | 39.60% | 2201 | 2189 | 2189 | 1.51 | 12 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -32.19% | 32.67% | 1726 | 1713 | 1713 | 2.67 | 13 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -29.67% | 29.67% | 1540 | 1531 | 1531 | 2.8 | 9 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -29.95% | 31.87% | 1571 | 1556 | 1556 | 2.9 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -82.15% | 82.25% | 7016 | 7001 | 7001 | 2.42 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 6 | development | SUCCEEDED | -89.40% | 89.51% | 7039 | 7019 | 7019 | 3.07 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -38.42% | 39.60% | 2201 | 2189 | 2189 | 1.51 | 12 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -32.19% | 32.67% | 1726 | 1713 | 1713 | 2.67 | 13 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -29.94% | 29.94% | 1525 | 1516 | 1516 | 2.85 | 9 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -29.95% | 31.87% | 1571 | 1556 | 1556 | 2.9 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -82.19% | 82.29% | 7001 | 6986 | 6986 | 2.43 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 1 | development | SUCCEEDED | -64.30% | 65.85% | 3634 | 3615 | 3615 | 7.61 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 2.06% | 12.13% | 1149 | 1130 | 1130 | 4.42 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | -16.77% | 21.05% | 923 | 906 | 906 | 6.43 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -38.08% | 38.54% | 902 | 886 | 886 | 6.16 | 16 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -17.73% | 23.32% | 842 | 823 | 823 | 7.17 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -55.63% | 58.06% | 3771 | 3752 | 3752 | 6.07 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 3 | development | SUCCEEDED | -60.71% | 62.83% | 3207 | 3189 | 3189 | 8.75 | 18 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | -1.51% | 11.94% | 1089 | 1070 | 1070 | 4.57 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | -18.11% | 20.93% | 808 | 791 | 791 | 7.37 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -35.34% | 37.43% | 786 | 772 | 772 | 7.08 | 14 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -10.03% | 17.24% | 665 | 646 | 646 | 9.33 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -52.74% | 54.74% | 3306 | 3287 | 3287 | 7.05 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 6 | development | SUCCEEDED | -60.05% | 62.03% | 3129 | 3110 | 3110 | 8.98 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | -1.51% | 11.94% | 1089 | 1070 | 1070 | 4.57 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | -17.89% | 20.71% | 797 | 780 | 780 | 7.49 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -34.78% | 36.96% | 777 | 763 | 763 | 7.09 | 14 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -9.60% | 16.71% | 650 | 631 | 631 | 9.13 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -51.14% | 53.23% | 3265 | 3246 | 3246 | 7.07 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 830 | 813 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 0.80% | 17.24% | 708 | 691 | 691 | 8.51 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_1_5_3 | 1 | year_2021 | SUCCEEDED | -17.55% | 26.18% | 703 | 685 | 685 | 8.88 | 18 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -37.12% | 37.37% | 679 | 662 | 662 | 9.06 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_1_5_3 | 1 | year_2023 | BLOCKED | — | — | 575 | 561 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_1_5_3 | 1 | continuous_2020_2023 | BLOCKED | — | — | 2622 | 2608 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 700 | 684 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 10.20% | 16.81% | 596 | 577 | 577 | 9.98 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_1_5_3 | 3 | year_2021 | SUCCEEDED | -13.15% | 24.13% | 631 | 613 | 613 | 9.87 | 18 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -38.46% | 38.71% | 555 | 538 | 538 | 11.15 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_1_5_3 | 3 | year_2023 | BLOCKED | — | — | 503 | 488 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_1_5_3 | 3 | continuous_2020_2023 | BLOCKED | — | — | 2230 | 2215 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 697 | 681 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | 9.28% | 16.81% | 591 | 572 | 572 | 9.57 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_1_5_3 | 6 | year_2021 | SUCCEEDED | -12.54% | 24.12% | 631 | 613 | 613 | 9.87 | 18 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -39.86% | 40.10% | 555 | 538 | 538 | 10.95 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_1_5_3 | 6 | year_2023 | BLOCKED | — | — | 503 | 488 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_1_5_3 | 6 | continuous_2020_2023 | BLOCKED | — | — | 2206 | 2191 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_2_4 | 1 | development | BLOCKED | — | — | 214 | 197 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | -7.18% | 21.57% | 501 | 481 | 481 | 12.87 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_2_4 | 1 | year_2021 | SUCCEEDED | -7.62% | 19.36% | 492 | 473 | 473 | 13.81 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_2_4 | 1 | year_2022 | BLOCKED | — | — | 180 | 162 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -7.86% | 19.20% | 472 | 452 | 452 | 14.32 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_2_4 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1134 | 1116 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_2_4 | 3 | development | BLOCKED | — | — | 151 | 133 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | -1.05% | 22.20% | 366 | 347 | 347 | 17.22 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | -17.10% | 26.23% | 368 | 349 | 349 | 18.07 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_2_4 | 3 | year_2022 | BLOCKED | — | — | 151 | 133 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -3.19% | 14.59% | 358 | 339 | 339 | 18.56 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_2_4 | 3 | continuous_2020_2023 | BLOCKED | — | — | 837 | 819 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_2_4 | 6 | development | BLOCKED | — | — | 150 | 132 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | -8.79% | 22.20% | 327 | 308 | 308 | 18.56 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | -10.78% | 21.09% | 346 | 327 | 327 | 19.42 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_2_4 | 6 | year_2022 | BLOCKED | — | — | 142 | 124 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | 1.39% | 12.83% | 322 | 303 | 303 | 20.27 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20 | ATR_2_4 | 6 | continuous_2020_2023 | BLOCKED | — | — | 749 | 731 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | PCT_3_6 | 1 | development | SUCCEEDED | -92.79% | 92.80% | 7281 | 7263 | 7263 | 2.45 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -40.03% | 41.24% | 2169 | 2158 | 2158 | 1.29 | 11 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -41.26% | 41.99% | 2048 | 2035 | 2035 | 1.83 | 13 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -35.07% | 35.07% | 1571 | 1561 | 1561 | 2.09 | 10 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -37.12% | 37.69% | 1802 | 1789 | 1789 | 2.24 | 13 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -87.45% | 87.50% | 7564 | 7551 | 7551 | 1.86 | 13 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 3 | development | SUCCEEDED | -92.34% | 92.34% | 7157 | 7139 | 7139 | 2.53 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -40.03% | 41.24% | 2169 | 2158 | 2158 | 1.29 | 11 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -41.07% | 41.74% | 2034 | 2022 | 2022 | 1.86 | 12 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -35.07% | 35.07% | 1547 | 1538 | 1538 | 2.18 | 9 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -38.08% | 38.54% | 1782 | 1768 | 1768 | 2.24 | 14 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -87.60% | 87.63% | 7507 | 7493 | 7493 | 1.88 | 14 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 6 | development | SUCCEEDED | -92.32% | 92.33% | 7157 | 7139 | 7139 | 2.53 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -40.03% | 41.24% | 2169 | 2158 | 2158 | 1.29 | 11 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -41.07% | 41.74% | 2034 | 2022 | 2022 | 1.86 | 12 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -34.32% | 34.32% | 1535 | 1526 | 1526 | 2.21 | 9 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -38.08% | 38.54% | 1782 | 1768 | 1768 | 2.24 | 14 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -87.39% | 87.41% | 7495 | 7481 | 7481 | 1.89 | 14 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 1 | development | SUCCEEDED | -73.91% | 74.68% | 3970 | 3951 | 3951 | 6.43 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | -4.62% | 13.55% | 1212 | 1194 | 1194 | 3.8 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | -20.96% | 24.33% | 1094 | 1075 | 1075 | 5.06 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -33.77% | 33.77% | 960 | 945 | 945 | 5.02 | 15 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -25.25% | 29.42% | 953 | 935 | 935 | 5.95 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -63.37% | 63.64% | 4168 | 4150 | 4150 | 5.03 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 3 | development | SUCCEEDED | -69.75% | 70.77% | 3528 | 3510 | 3510 | 7.41 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | -4.64% | 13.28% | 1174 | 1156 | 1156 | 3.97 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | -22.00% | 25.32% | 937 | 918 | 918 | 5.96 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -29.95% | 29.95% | 867 | 850 | 850 | 5.39 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -19.62% | 24.32% | 807 | 789 | 789 | 6.95 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -58.07% | 58.48% | 3713 | 3695 | 3695 | 5.75 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 6 | development | SUCCEEDED | -70.18% | 71.23% | 3475 | 3457 | 3457 | 7.53 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | -4.64% | 13.28% | 1174 | 1156 | 1156 | 3.97 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | -21.16% | 24.50% | 930 | 911 | 911 | 6.02 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -29.31% | 29.31% | 859 | 842 | 842 | 5.46 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -19.11% | 23.67% | 810 | 792 | 792 | 6.52 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -57.52% | 57.94% | 3716 | 3698 | 3698 | 5.66 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 863 | 843 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | -0.36% | 18.17% | 683 | 665 | 665 | 8.72 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_1_5_3 | 1 | year_2021 | BLOCKED | — | — | 180 | 166 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -48.16% | 48.16% | 659 | 642 | 642 | 8.88 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -26.48% | 31.53% | 675 | 656 | 656 | 9.14 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_1_5_3 | 1 | continuous_2020_2023 | BLOCKED | — | — | 854 | 840 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 752 | 732 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 6.42% | 16.72% | 577 | 559 | 559 | 10.48 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_1_5_3 | 3 | year_2021 | BLOCKED | — | — | 157 | 139 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -43.72% | 43.72% | 580 | 562 | 562 | 10.05 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -18.90% | 27.19% | 580 | 561 | 561 | 10.27 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_1_5_3 | 3 | continuous_2020_2023 | BLOCKED | — | — | 710 | 692 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 751 | 731 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | 5.45% | 16.72% | 565 | 547 | 547 | 9.95 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_1_5_3 | 6 | year_2021 | BLOCKED | — | — | 157 | 139 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -43.79% | 43.79% | 579 | 561 | 561 | 10.07 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -18.63% | 27.19% | 579 | 559 | 559 | 10.14 | 20 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_1_5_3 | 6 | continuous_2020_2023 | BLOCKED | — | — | 692 | 674 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_2_4 | 1 | development | BLOCKED | — | — | 229 | 210 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 1.62% | 18.18% | 478 | 458 | 458 | 13.52 | 20 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_2_4 | 1 | year_2021 | BLOCKED | — | — | 124 | 109 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_2_4 | 1 | year_2022 | BLOCKED | — | — | 199 | 181 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -8.39% | 18.78% | 476 | 458 | 458 | 14.07 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_2_4 | 1 | continuous_2020_2023 | BLOCKED | — | — | 590 | 576 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_2_4 | 3 | development | BLOCKED | — | — | 1018 | 999 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 15.37% | 15.20% | 329 | 310 | 310 | 19.43 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | -14.70% | 27.25% | 372 | 354 | 354 | 17.85 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_2_4 | 3 | year_2022 | BLOCKED | — | — | 159 | 141 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -11.34% | 23.56% | 333 | 314 | 314 | 19.44 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_2_4 | 3 | continuous_2020_2023 | BLOCKED | — | — | 798 | 780 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_2_4 | 6 | development | BLOCKED | — | — | 992 | 973 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 7.45% | 15.20% | 302 | 283 | 283 | 19.82 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | -12.43% | 26.50% | 367 | 349 | 349 | 18.1 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_2_4 | 6 | year_2022 | BLOCKED | — | — | 152 | 134 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -10.54% | 23.54% | 324 | 304 | 304 | 19.73 | 20 | FULL_WINDOW |
| basic | BREAKOUT_60 | ATR_2_4 | 6 | continuous_2020_2023 | BLOCKED | — | — | 743 | 725 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 1 | development | SUCCEEDED | -66.82% | 68.73% | 7847 | 7831 | 7831 | 2.68 | 16 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -14.60% | 16.43% | 1892 | 1879 | 1879 | 2.13 | 13 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 1 | year_2021 | BLOCKED | — | — | 497 | 484 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -30.99% | 31.42% | 1901 | 1891 | 1891 | 2.07 | 10 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -27.48% | 30.00% | 1959 | 1941 | 1941 | 2.31 | 18 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 2370 | 2357 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 3 | development | SUCCEEDED | -65.79% | 67.83% | 7763 | 7747 | 7747 | 2.71 | 16 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -13.36% | 15.15% | 1869 | 1856 | 1856 | 2.12 | 13 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 3 | year_2021 | BLOCKED | — | — | 490 | 477 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -31.20% | 31.63% | 1901 | 1891 | 1891 | 2.07 | 10 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -27.32% | 29.96% | 1943 | 1925 | 1925 | 2.33 | 18 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 2330 | 2317 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 6 | development | SUCCEEDED | -65.79% | 67.83% | 7763 | 7747 | 7747 | 2.71 | 16 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -13.36% | 15.15% | 1869 | 1856 | 1856 | 2.12 | 13 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 6 | year_2021 | BLOCKED | — | — | 490 | 477 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -31.20% | 31.63% | 1901 | 1891 | 1891 | 2.07 | 10 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -27.32% | 29.96% | 1943 | 1925 | 1925 | 2.33 | 18 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_3_6 | 6 | continuous_2020_2023 | BLOCKED | — | — | 2330 | 2317 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 1 | development | BLOCKED | — | — | 896 | 878 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | -1.77% | 15.35% | 977 | 959 | 959 | 5.71 | 18 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | 9.44% | 14.61% | 936 | 917 | 917 | 6.35 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -21.99% | 22.62% | 1056 | 1041 | 1041 | 5.39 | 15 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -9.56% | 18.44% | 947 | 928 | 928 | 6.26 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -25.60% | 38.72% | 3863 | 3844 | 3844 | 6.05 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 3 | development | BLOCKED | — | — | 853 | 835 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 3.59% | 14.96% | 923 | 905 | 905 | 5.96 | 18 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 3 | year_2021 | BLOCKED | — | — | 228 | 212 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -20.90% | 21.54% | 1015 | 1000 | 1000 | 5.54 | 15 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -13.54% | 18.44% | 847 | 828 | 828 | 6.84 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 3 | continuous_2020_2023 | BLOCKED | — | — | 1116 | 1100 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 6 | development | BLOCKED | — | — | 853 | 835 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 3.64% | 14.96% | 918 | 900 | 900 | 5.9 | 18 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 6 | year_2021 | BLOCKED | — | — | 228 | 212 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -21.07% | 21.71% | 1011 | 996 | 996 | 5.57 | 15 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -13.54% | 18.44% | 847 | 828 | 828 | 6.84 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | PCT_5_10 | 6 | continuous_2020_2023 | BLOCKED | — | — | 1110 | 1094 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 1596 | 1576 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 5.18% | 22.03% | 434 | 414 | 414 | 15.75 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 1 | year_2021 | SUCCEEDED | 5.76% | 20.29% | 446 | 427 | 427 | 15.47 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -26.68% | 27.06% | 479 | 463 | 463 | 14.14 | 16 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -12.68% | 21.85% | 419 | 399 | 399 | 16.3 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 1 | continuous_2020_2023 | SUCCEEDED | -31.63% | 47.10% | 1725 | 1705 | 1705 | 15.76 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 1088 | 1068 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 1.95% | 25.18% | 289 | 269 | 269 | 22.42 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 3 | year_2021 | BLOCKED | — | — | 106 | 88 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -16.86% | 21.44% | 368 | 354 | 354 | 17.68 | 14 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -5.54% | 22.31% | 283 | 263 | 263 | 23.01 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 3 | continuous_2020_2023 | BLOCKED | — | — | 361 | 343 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 244 | 225 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | -1.92% | 25.18% | 264 | 244 | 244 | 22.85 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 6 | year_2021 | BLOCKED | — | — | 104 | 86 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -22.26% | 24.86% | 345 | 332 | 332 | 18.83 | 13 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -1.31% | 19.28% | 279 | 259 | 259 | 22.14 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_1_5_3 | 6 | continuous_2020_2023 | BLOCKED | — | — | 330 | 312 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 1 | development | BLOCKED | — | — | 1252 | 1234 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 12.54% | 16.26% | 344 | 324 | 324 | 20.81 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 1 | year_2021 | SUCCEEDED | 12.60% | 14.06% | 351 | 331 | 331 | 20.31 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -24.58% | 24.89% | 383 | 365 | 365 | 18.25 | 18 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -3.57% | 15.68% | 320 | 301 | 301 | 22.43 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 1 | continuous_2020_2023 | SUCCEEDED | -12.70% | 35.93% | 1360 | 1341 | 1341 | 20.64 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 3 | development | SUCCEEDED | -19.84% | 33.47% | 870 | 851 | 851 | 36.92 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 7.80% | 23.00% | 202 | 183 | 183 | 34.47 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | 3.10% | 18.41% | 221 | 201 | 201 | 31.53 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -20.17% | 20.49% | 236 | 219 | 219 | 28.98 | 17 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -8.17% | 18.17% | 178 | 158 | 158 | 38.34 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 3 | continuous_2020_2023 | BLOCKED | — | — | 263 | 243 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 6 | development | SUCCEEDED | -13.92% | 27.70% | 747 | 727 | 727 | 42.63 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | -0.62% | 23.00% | 161 | 141 | 141 | 39.03 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | 4.55% | 16.98% | 207 | 187 | 187 | 33.39 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -26.62% | 26.92% | 208 | 193 | 193 | 31.89 | 15 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -5.00% | 16.76% | 160 | 140 | 140 | 41.27 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_3 | ATR_2_4 | 6 | continuous_2020_2023 | BLOCKED | — | — | 197 | 178 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 1 | development | SUCCEEDED | -70.34% | 71.79% | 7870 | 7861 | 7861 | 2.2 | 9 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -18.47% | 20.19% | 1936 | 1923 | 1923 | 1.87 | 13 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 1 | year_2021 | BLOCKED | — | — | 504 | 490 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -25.15% | 25.81% | 1802 | 1790 | 1790 | 1.75 | 12 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -23.61% | 28.68% | 2079 | 2064 | 2064 | 1.9 | 15 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 2438 | 2424 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 3 | development | SUCCEEDED | -69.86% | 71.32% | 7840 | 7831 | 7831 | 2.21 | 9 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -18.88% | 20.34% | 1925 | 1911 | 1911 | 1.86 | 14 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 3 | year_2021 | BLOCKED | — | — | 500 | 485 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -25.15% | 25.81% | 1802 | 1790 | 1790 | 1.75 | 12 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -23.87% | 29.06% | 2073 | 2058 | 2058 | 1.91 | 15 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 2421 | 2406 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 6 | development | SUCCEEDED | -69.86% | 71.32% | 7840 | 7831 | 7831 | 2.21 | 9 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -18.88% | 20.34% | 1925 | 1911 | 1911 | 1.86 | 14 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 6 | year_2021 | BLOCKED | — | — | 500 | 485 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -25.15% | 25.81% | 1802 | 1790 | 1790 | 1.75 | 12 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -23.87% | 29.06% | 2073 | 2058 | 2058 | 1.91 | 15 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_3_6 | 6 | continuous_2020_2023 | BLOCKED | — | — | 2421 | 2406 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 1 | development | BLOCKED | — | — | 3511 | 3494 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 2.52% | 14.52% | 1040 | 1024 | 1024 | 5.09 | 16 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 1 | year_2021 | BLOCKED | — | — | 237 | 221 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -23.98% | 24.47% | 1095 | 1079 | 1079 | 4.68 | 16 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -12.17% | 23.21% | 1063 | 1046 | 1046 | 5.33 | 17 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1268 | 1252 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 3 | development | BLOCKED | — | — | 3344 | 3325 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 2.32% | 14.90% | 993 | 977 | 977 | 5.36 | 16 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 3 | year_2021 | BLOCKED | — | — | 218 | 201 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -23.22% | 23.71% | 1075 | 1059 | 1059 | 4.75 | 16 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -11.36% | 21.83% | 1014 | 997 | 997 | 5.65 | 17 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 3 | continuous_2020_2023 | BLOCKED | — | — | 1191 | 1174 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 6 | development | BLOCKED | — | — | 3331 | 3312 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 2.27% | 14.90% | 992 | 976 | 976 | 5.27 | 16 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 6 | year_2021 | BLOCKED | — | — | 218 | 201 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -23.22% | 23.71% | 1075 | 1059 | 1059 | 4.75 | 16 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -11.36% | 21.83% | 1014 | 997 | 997 | 5.65 | 17 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | PCT_5_10 | 6 | continuous_2020_2023 | BLOCKED | — | — | 1194 | 1177 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 1523 | 1503 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 12.77% | 20.89% | 406 | 386 | 386 | 16.72 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 1 | year_2021 | SUCCEEDED | 3.91% | 21.47% | 445 | 427 | 427 | 15.43 | 18 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -29.76% | 30.36% | 458 | 441 | 441 | 14.92 | 17 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -10.13% | 21.43% | 404 | 384 | 384 | 17.2 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 1 | continuous_2020_2023 | SUCCEEDED | -16.70% | 42.48% | 1667 | 1647 | 1647 | 16.36 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 1025 | 1006 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 3.65% | 24.79% | 253 | 233 | 233 | 25.9 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 3 | year_2021 | BLOCKED | — | — | 85 | 65 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -14.48% | 18.92% | 340 | 322 | 322 | 19.35 | 18 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -8.80% | 17.76% | 266 | 246 | 246 | 25.22 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 3 | continuous_2020_2023 | BLOCKED | — | — | 314 | 295 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 936 | 916 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | -4.21% | 24.79% | 228 | 208 | 208 | 25.83 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 6 | year_2021 | BLOCKED | — | — | 85 | 65 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -12.24% | 17.04% | 310 | 293 | 293 | 21.32 | 17 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -2.68% | 14.78% | 249 | 229 | 229 | 24.37 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_1_5_3 | 6 | continuous_2020_2023 | BLOCKED | — | — | 284 | 264 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 1 | development | BLOCKED | — | — | 1224 | 1206 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 11.39% | 17.50% | 329 | 309 | 309 | 21.78 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 1 | year_2021 | SUCCEEDED | 0.54% | 21.10% | 333 | 316 | 316 | 21.54 | 17 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -25.71% | 26.01% | 355 | 335 | 335 | 19.77 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | 0.39% | 14.27% | 318 | 298 | 298 | 22.6 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 1 | continuous_2020_2023 | SUCCEEDED | -26.58% | 44.26% | 1305 | 1285 | 1285 | 21.6 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 3 | development | SUCCEEDED | -12.45% | 28.12% | 825 | 805 | 805 | 38.76 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 6.33% | 20.39% | 197 | 178 | 178 | 35.85 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 3 | year_2021 | BLOCKED | — | — | 66 | 46 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -23.76% | 24.13% | 216 | 197 | 197 | 32.93 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 3 | year_2023 | BLOCKED | — | — | 129 | 109 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 3 | continuous_2020_2023 | SUCCEEDED | -17.50% | 40.43% | 742 | 722 | 722 | 37.66 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 6 | development | SUCCEEDED | -5.85% | 26.10% | 707 | 687 | 687 | 44.76 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 1.07% | 20.39% | 151 | 132 | 132 | 43.02 | 19 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 6 | year_2021 | BLOCKED | — | — | 63 | 43 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -26.52% | 26.82% | 185 | 168 | 168 | 36.77 | 17 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | 3.64% | 14.91% | 149 | 129 | 129 | 45.1 | 20 | FULL_WINDOW |
| basic | TREND_PULLBACK_5 | ATR_2_4 | 6 | continuous_2020_2023 | BLOCKED | — | — | 194 | 177 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | RSI_REENTRY_30 | PCT_3_6 | 1 | development | SUCCEEDED | -0.13% | 0.14% | 6 | 6 | 6 | 2.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | 0.07% | 0.03% | 7 | 7 | 7 | 3.29 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -0.08% | 0.08% | 2 | 2 | 2 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -0.04% | 0.04% | 1 | 1 | 1 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -0.04% | 0.14% | 10 | 10 | 10 | 2.3 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 3 | development | SUCCEEDED | -0.13% | 0.14% | 6 | 6 | 6 | 2.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | 0.07% | 0.03% | 7 | 7 | 7 | 3.29 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -0.08% | 0.08% | 2 | 2 | 2 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -0.04% | 0.04% | 1 | 1 | 1 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -0.04% | 0.14% | 10 | 10 | 10 | 2.3 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 6 | development | SUCCEEDED | -0.13% | 0.14% | 6 | 6 | 6 | 2.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | 0.07% | 0.03% | 7 | 7 | 7 | 3.29 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -0.08% | 0.08% | 2 | 2 | 2 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -0.04% | 0.04% | 1 | 1 | 1 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -0.04% | 0.14% | 10 | 10 | 10 | 2.3 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 1 | development | SUCCEEDED | -0.38% | 0.45% | 6 | 6 | 6 | 3.5 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 0.12% | 0.05% | 8 | 8 | 8 | 7.38 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -0.18% | 0.18% | 2 | 2 | 2 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -0.12% | 0.19% | 1 | 1 | 1 | 1.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -0.17% | 0.33% | 11 | 11 | 11 | 5.45 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 3 | development | SUCCEEDED | -0.38% | 0.45% | 6 | 6 | 6 | 3.5 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 0.09% | 0.10% | 8 | 8 | 8 | 11.62 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -0.18% | 0.18% | 2 | 2 | 2 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -0.12% | 0.19% | 1 | 1 | 1 | 1.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -0.20% | 0.40% | 11 | 11 | 11 | 8.55 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 6 | development | SUCCEEDED | -0.38% | 0.45% | 6 | 6 | 6 | 3.5 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 0.09% | 0.10% | 8 | 8 | 8 | 11.62 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -0.18% | 0.18% | 2 | 2 | 2 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -0.12% | 0.19% | 1 | 1 | 1 | 1.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -0.20% | 0.40% | 11 | 11 | 11 | 8.55 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 1 | development | SUCCEEDED | -0.68% | 0.77% | 6 | 6 | 6 | 5.33 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | -0.52% | 0.53% | 13 | 13 | 13 | 8.54 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 1 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -0.33% | 0.33% | 2 | 2 | 2 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -0.19% | 0.26% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 1 | continuous_2020_2023 | SUCCEEDED | -1.04% | 1.04% | 16 | 16 | 16 | 7.12 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 3 | development | SUCCEEDED | -0.68% | 0.77% | 6 | 6 | 6 | 5.33 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | -0.55% | 0.55% | 13 | 13 | 13 | 11.15 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 3 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -0.33% | 0.33% | 2 | 2 | 2 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -0.19% | 0.26% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 3 | continuous_2020_2023 | SUCCEEDED | -1.06% | 1.06% | 16 | 16 | 16 | 9.25 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 6 | development | SUCCEEDED | -0.68% | 0.77% | 6 | 6 | 6 | 5.33 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | -0.55% | 0.55% | 13 | 13 | 13 | 11.15 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 6 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -0.33% | 0.33% | 2 | 2 | 2 | 0.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -0.19% | 0.26% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_1_5_3 | 6 | continuous_2020_2023 | SUCCEEDED | -1.06% | 1.06% | 16 | 16 | 16 | 9.25 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 1 | development | SUCCEEDED | -0.70% | 0.98% | 6 | 6 | 6 | 9.17 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 1.23% | 0.69% | 14 | 14 | 14 | 19.71 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 1 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -0.46% | 0.46% | 4 | 4 | 4 | 1.75 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -0.28% | 0.35% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 1 | continuous_2020_2023 | SUCCEEDED | 0.48% | 0.86% | 19 | 19 | 19 | 15.05 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 3 | development | SUCCEEDED | -0.80% | 0.98% | 6 | 6 | 6 | 19.67 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 1.00% | 0.69% | 14 | 14 | 14 | 40.36 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -0.46% | 0.46% | 4 | 4 | 4 | 1.75 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -0.28% | 0.35% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 3 | continuous_2020_2023 | SUCCEEDED | 0.25% | 1.16% | 19 | 19 | 19 | 30.26 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 6 | development | SUCCEEDED | -0.61% | 0.98% | 6 | 5 | 5 | 5.2 | 1 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 0.97% | 0.69% | 14 | 14 | 14 | 59.86 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -0.46% | 0.46% | 4 | 4 | 4 | 1.75 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -0.28% | 0.35% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_30 | ATR_2_4 | 6 | continuous_2020_2023 | SUCCEEDED | 0.22% | 1.19% | 19 | 19 | 19 | 44.63 | 0 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 1 | development | SUCCEEDED | -18.27% | 18.27% | 794 | 793 | 793 | 4.24 | 1 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -0.44% | 2.18% | 192 | 184 | 184 | 2.91 | 8 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -3.43% | 4.73% | 237 | 236 | 236 | 4.92 | 1 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -5.51% | 5.51% | 176 | 170 | 170 | 2.93 | 6 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | 0.22% | 1.90% | 196 | 191 | 191 | 4.35 | 5 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -8.70% | 9.46% | 801 | 796 | 796 | 3.99 | 5 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 3 | development | SUCCEEDED | -17.87% | 17.87% | 794 | 793 | 793 | 4.59 | 1 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -0.44% | 2.18% | 192 | 184 | 184 | 2.91 | 8 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -3.59% | 4.89% | 237 | 236 | 236 | 5.07 | 1 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -5.33% | 5.33% | 176 | 170 | 170 | 3.15 | 6 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | 0.27% | 1.72% | 196 | 191 | 191 | 4.83 | 5 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -8.61% | 9.41% | 801 | 796 | 796 | 4.19 | 5 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 6 | development | SUCCEEDED | -17.98% | 17.98% | 794 | 793 | 793 | 4.62 | 1 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -0.44% | 2.18% | 192 | 184 | 184 | 2.91 | 8 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -3.59% | 4.89% | 237 | 236 | 236 | 5.07 | 1 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -5.33% | 5.33% | 176 | 170 | 170 | 3.15 | 6 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | 0.27% | 1.72% | 196 | 191 | 191 | 4.83 | 5 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -8.61% | 9.41% | 801 | 796 | 796 | 4.19 | 5 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 1 | development | SUCCEEDED | -19.66% | 20.59% | 796 | 794 | 794 | 9.52 | 2 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 3.16% | 4.34% | 192 | 179 | 179 | 7.23 | 13 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | 0.32% | 3.91% | 245 | 243 | 243 | 9.49 | 2 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -7.03% | 7.85% | 191 | 182 | 182 | 6.45 | 9 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -0.22% | 4.15% | 187 | 182 | 182 | 10.22 | 5 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -3.26% | 9.61% | 814 | 809 | 809 | 8.58 | 5 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 3 | development | SUCCEEDED | -17.73% | 18.73% | 792 | 787 | 787 | 11.33 | 5 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 3.38% | 4.34% | 192 | 178 | 178 | 7.71 | 14 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | 1.14% | 4.12% | 244 | 241 | 241 | 11.38 | 3 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -7.44% | 8.44% | 190 | 181 | 181 | 6.99 | 9 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -0.67% | 4.23% | 184 | 178 | 178 | 12.83 | 6 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -2.80% | 10.79% | 809 | 803 | 803 | 10.12 | 6 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 6 | development | SUCCEEDED | -17.85% | 18.84% | 791 | 786 | 786 | 11.82 | 5 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 3.78% | 4.34% | 192 | 178 | 178 | 7.87 | 14 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | 1.14% | 4.12% | 244 | 241 | 241 | 11.38 | 3 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -7.12% | 8.12% | 190 | 181 | 181 | 7.5 | 9 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -0.58% | 4.18% | 184 | 177 | 177 | 12.59 | 7 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -2.00% | 10.39% | 809 | 802 | 802 | 10.22 | 7 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 1 | development | SUCCEEDED | -20.07% | 23.30% | 754 | 751 | 751 | 14.3 | 3 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 4.22% | 8.56% | 177 | 164 | 164 | 13.8 | 13 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 1 | year_2021 | SUCCEEDED | -2.07% | 9.07% | 234 | 229 | 229 | 13.45 | 5 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -15.12% | 15.64% | 192 | 182 | 182 | 10.16 | 10 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -3.81% | 6.39% | 183 | 176 | 176 | 13.18 | 7 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 1 | continuous_2020_2023 | SUCCEEDED | -15.52% | 24.24% | 784 | 777 | 777 | 12.88 | 7 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 3 | development | SUCCEEDED | -24.98% | 28.50% | 748 | 739 | 739 | 18.22 | 9 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 9.23% | 8.39% | 176 | 161 | 161 | 17.71 | 15 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 3 | year_2021 | SUCCEEDED | 2.44% | 8.63% | 223 | 217 | 217 | 17.12 | 6 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -16.28% | 16.79% | 188 | 178 | 178 | 12.01 | 10 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -6.46% | 9.10% | 182 | 173 | 173 | 16.06 | 9 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 3 | continuous_2020_2023 | SUCCEEDED | -13.24% | 28.64% | 767 | 758 | 758 | 16.32 | 9 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 6 | development | SUCCEEDED | -24.90% | 28.42% | 747 | 738 | 738 | 18.72 | 9 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | 9.32% | 8.39% | 176 | 160 | 160 | 17.25 | 16 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 6 | year_2021 | SUCCEEDED | 4.25% | 8.07% | 218 | 212 | 212 | 18.08 | 6 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -16.41% | 16.92% | 188 | 176 | 176 | 11.12 | 12 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -6.52% | 9.16% | 182 | 173 | 173 | 16.21 | 9 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_1_5_3 | 6 | continuous_2020_2023 | SUCCEEDED | -12.10% | 28.41% | 762 | 753 | 753 | 16.77 | 9 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 1 | development | SUCCEEDED | -15.58% | 20.90% | 714 | 710 | 710 | 19.02 | 4 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 2.08% | 9.95% | 168 | 153 | 153 | 17.17 | 15 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 1 | year_2021 | SUCCEEDED | 0.51% | 7.85% | 212 | 204 | 204 | 18.39 | 8 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -15.39% | 15.81% | 177 | 163 | 163 | 14.39 | 14 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -2.93% | 5.94% | 180 | 172 | 172 | 17.62 | 8 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 1 | continuous_2020_2023 | SUCCEEDED | -14.85% | 22.62% | 732 | 724 | 724 | 17.13 | 8 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 3 | development | SUCCEEDED | -26.45% | 31.03% | 672 | 658 | 658 | 29.25 | 14 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 6.44% | 10.10% | 152 | 132 | 132 | 25.2 | 20 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | 5.31% | 8.00% | 176 | 163 | 163 | 29.13 | 13 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -16.94% | 17.35% | 167 | 154 | 154 | 19.96 | 13 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -3.16% | 7.88% | 170 | 158 | 158 | 25.86 | 12 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 3 | continuous_2020_2023 | SUCCEEDED | -13.64% | 28.28% | 658 | 646 | 646 | 26.09 | 12 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 6 | development | SUCCEEDED | -30.83% | 34.67% | 640 | 624 | 624 | 32.66 | 16 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 6.85% | 10.10% | 147 | 127 | 127 | 23.09 | 20 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | 6.56% | 7.93% | 154 | 141 | 141 | 35.06 | 13 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -17.34% | 17.74% | 164 | 149 | 149 | 19.64 | 15 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -3.43% | 7.97% | 168 | 153 | 153 | 25.74 | 15 | FULL_WINDOW |
| basic | RSI_REENTRY_40 | ATR_2_4 | 6 | continuous_2020_2023 | SUCCEEDED | -11.34% | 28.05% | 623 | 608 | 608 | 28.79 | 15 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 1 | development | SUCCEEDED | -28.05% | 30.42% | 2608 | 2596 | 2596 | 4.23 | 12 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -3.43% | 7.79% | 615 | 602 | 602 | 3.18 | 13 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 1 | year_2021 | BLOCKED | — | — | 553 | 534 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -17.36% | 17.61% | 535 | 527 | 527 | 3.23 | 8 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -3.73% | 7.52% | 595 | 578 | 578 | 4.14 | 17 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1165 | 1146 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 3 | development | SUCCEEDED | -27.75% | 30.14% | 2586 | 2574 | 2574 | 4.39 | 12 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -3.43% | 7.79% | 615 | 602 | 602 | 3.18 | 13 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 3 | year_2021 | BLOCKED | — | — | 544 | 524 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -17.16% | 17.42% | 533 | 525 | 525 | 3.35 | 8 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -3.56% | 7.08% | 591 | 574 | 574 | 4.37 | 17 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 1156 | 1136 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 6 | development | SUCCEEDED | -27.86% | 30.25% | 2586 | 2574 | 2574 | 4.4 | 12 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -3.43% | 7.79% | 615 | 602 | 602 | 3.18 | 13 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 6 | year_2021 | BLOCKED | — | — | 544 | 524 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -17.16% | 17.42% | 533 | 525 | 525 | 3.35 | 8 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -3.56% | 7.08% | 591 | 574 | 574 | 4.37 | 17 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_3_6 | 6 | continuous_2020_2023 | BLOCKED | — | — | 1156 | 1136 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 1 | development | BLOCKED | — | — | 1701 | 1686 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 8.85% | 7.90% | 480 | 462 | 462 | 7.16 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 1 | year_2021 | BLOCKED | — | — | 172 | 153 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -20.13% | 20.39% | 427 | 413 | 413 | 7.3 | 14 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -3.37% | 10.21% | 474 | 456 | 456 | 9.32 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 1 | continuous_2020_2023 | BLOCKED | — | — | 638 | 619 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 3 | development | BLOCKED | — | — | 1554 | 1537 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 8.82% | 8.03% | 465 | 447 | 447 | 7.3 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 3 | year_2021 | BLOCKED | — | — | 159 | 141 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -19.61% | 19.88% | 416 | 402 | 402 | 7.88 | 14 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -6.46% | 12.18% | 439 | 421 | 421 | 11.05 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 3 | continuous_2020_2023 | BLOCKED | — | — | 610 | 591 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 6 | development | BLOCKED | — | — | 1516 | 1499 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 8.66% | 8.03% | 463 | 445 | 445 | 7.1 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 6 | year_2021 | BLOCKED | — | — | 159 | 140 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -19.37% | 19.64% | 414 | 400 | 400 | 8.06 | 14 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -6.46% | 12.18% | 439 | 421 | 421 | 11.05 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | PCT_5_10 | 6 | continuous_2020_2023 | BLOCKED | — | — | 601 | 582 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 516 | 498 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 5.61% | 14.58% | 371 | 353 | 353 | 12.37 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 1 | year_2021 | BLOCKED | — | — | 100 | 81 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -20.34% | 20.61% | 370 | 355 | 355 | 12.0 | 15 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -4.14% | 14.28% | 399 | 379 | 379 | 14.04 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 1 | continuous_2020_2023 | BLOCKED | — | — | 455 | 436 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 436 | 417 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 14.65% | 14.47% | 314 | 296 | 296 | 15.07 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 3 | year_2021 | BLOCKED | — | — | 88 | 69 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -24.02% | 24.43% | 323 | 308 | 308 | 15.6 | 15 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -0.48% | 12.99% | 339 | 319 | 319 | 17.81 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 3 | continuous_2020_2023 | BLOCKED | — | — | 387 | 368 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 1160 | 1141 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | 14.24% | 14.47% | 313 | 295 | 295 | 15.2 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 6 | year_2021 | BLOCKED | — | — | 88 | 69 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -24.09% | 24.50% | 316 | 302 | 302 | 15.74 | 14 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -0.91% | 12.90% | 337 | 317 | 317 | 18.0 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_1_5_3 | 6 | continuous_2020_2023 | BLOCKED | — | — | 385 | 366 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 1 | development | BLOCKED | — | — | 418 | 401 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | -4.43% | 17.57% | 310 | 292 | 292 | 16.18 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 1 | year_2021 | BLOCKED | — | — | 115 | 97 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -22.32% | 22.58% | 306 | 291 | 291 | 16.41 | 15 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -1.34% | 11.73% | 330 | 310 | 310 | 19.05 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 1 | continuous_2020_2023 | BLOCKED | — | — | 407 | 389 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 3 | development | BLOCKED | — | — | 285 | 267 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 2.86% | 17.53% | 240 | 222 | 222 | 21.08 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 3 | year_2021 | BLOCKED | — | — | 92 | 74 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -27.51% | 27.75% | 235 | 216 | 216 | 24.47 | 19 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -5.39% | 15.83% | 229 | 209 | 209 | 28.91 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 3 | continuous_2020_2023 | BLOCKED | — | — | 305 | 287 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 6 | development | BLOCKED | — | — | 258 | 240 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 0.18% | 17.53% | 222 | 203 | 203 | 21.15 | 19 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 6 | year_2021 | BLOCKED | — | — | 91 | 73 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -27.95% | 28.19% | 219 | 201 | 201 | 25.34 | 18 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -3.43% | 14.76% | 206 | 186 | 186 | 30.9 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_1_5 | ATR_2_4 | 6 | continuous_2020_2023 | BLOCKED | — | — | 282 | 264 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 1 | development | SUCCEEDED | -6.44% | 9.03% | 1110 | 1107 | 1107 | 4.28 | 3 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | 0.63% | 3.99% | 271 | 255 | 255 | 3.41 | 16 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -3.42% | 6.21% | 304 | 304 | 304 | 4.61 | 0 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -6.09% | 6.13% | 249 | 241 | 241 | 4.16 | 8 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -1.27% | 2.25% | 239 | 230 | 230 | 3.84 | 9 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -9.52% | 13.49% | 1059 | 1050 | 1050 | 4.2 | 9 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 3 | development | SUCCEEDED | -5.86% | 8.34% | 1107 | 1104 | 1104 | 4.55 | 3 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | 0.59% | 3.99% | 270 | 254 | 254 | 3.31 | 16 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -3.37% | 6.16% | 303 | 303 | 303 | 4.72 | 0 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -5.91% | 5.95% | 249 | 241 | 241 | 4.32 | 8 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -1.36% | 2.25% | 239 | 230 | 230 | 3.9 | 9 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -9.48% | 13.35% | 1057 | 1048 | 1048 | 4.28 | 9 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 6 | development | SUCCEEDED | -5.97% | 8.45% | 1107 | 1104 | 1104 | 4.56 | 3 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | 0.59% | 3.99% | 270 | 254 | 254 | 3.31 | 16 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -3.37% | 6.16% | 303 | 303 | 303 | 4.72 | 0 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -5.91% | 5.95% | 249 | 241 | 241 | 4.32 | 8 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -1.36% | 2.25% | 239 | 230 | 230 | 3.9 | 9 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -9.48% | 13.35% | 1057 | 1048 | 1048 | 4.28 | 9 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 1 | development | SUCCEEDED | -9.45% | 17.58% | 1059 | 1053 | 1053 | 10.02 | 6 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 10.35% | 3.69% | 253 | 234 | 234 | 7.07 | 19 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | 0.98% | 5.54% | 269 | 268 | 268 | 9.83 | 1 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -11.85% | 12.55% | 236 | 224 | 224 | 8.84 | 12 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | 2.54% | 3.06% | 232 | 219 | 219 | 9.76 | 13 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | 1.02% | 16.48% | 982 | 969 | 969 | 9.2 | 13 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 3 | development | SUCCEEDED | -7.76% | 16.31% | 1039 | 1029 | 1029 | 11.54 | 10 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 10.26% | 3.69% | 244 | 224 | 224 | 6.58 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | 2.93% | 4.72% | 250 | 248 | 248 | 13.02 | 2 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -12.14% | 12.71% | 234 | 222 | 222 | 9.67 | 12 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | 2.17% | 2.73% | 229 | 216 | 216 | 11.62 | 13 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | 2.30% | 16.14% | 950 | 937 | 937 | 10.98 | 13 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 6 | development | SUCCEEDED | -6.82% | 16.06% | 1035 | 1025 | 1025 | 11.92 | 10 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 10.26% | 3.69% | 244 | 224 | 224 | 6.58 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | 2.99% | 4.67% | 250 | 248 | 248 | 13.21 | 2 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -11.87% | 12.45% | 234 | 222 | 222 | 9.82 | 12 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | 2.17% | 2.73% | 229 | 216 | 216 | 11.62 | 13 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | 2.72% | 15.84% | 950 | 937 | 937 | 11.07 | 13 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 311 | 303 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 7.66% | 10.61% | 225 | 205 | 205 | 13.39 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 1 | year_2021 | SUCCEEDED | -3.13% | 8.83% | 241 | 238 | 238 | 14.51 | 3 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -15.84% | 15.99% | 226 | 214 | 214 | 12.17 | 12 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -1.92% | 7.05% | 221 | 207 | 207 | 14.42 | 14 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 1 | continuous_2020_2023 | SUCCEEDED | -11.93% | 24.36% | 903 | 889 | 889 | 13.98 | 14 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 291 | 278 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 8.78% | 11.13% | 213 | 193 | 193 | 17.15 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 3 | year_2021 | SUCCEEDED | 6.10% | 6.96% | 210 | 205 | 205 | 20.6 | 5 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -13.77% | 15.22% | 212 | 201 | 201 | 14.46 | 11 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -7.37% | 11.04% | 220 | 204 | 204 | 16.87 | 16 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 3 | continuous_2020_2023 | SUCCEEDED | -9.77% | 28.37% | 846 | 830 | 830 | 18.0 | 16 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 290 | 275 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | 10.31% | 11.13% | 207 | 188 | 188 | 16.64 | 19 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 6 | year_2021 | SUCCEEDED | 5.95% | 7.21% | 205 | 200 | 200 | 21.27 | 5 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -13.25% | 14.71% | 209 | 197 | 197 | 14.74 | 12 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -7.37% | 11.04% | 220 | 204 | 204 | 16.87 | 16 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_1_5_3 | 6 | continuous_2020_2023 | SUCCEEDED | -8.26% | 27.53% | 828 | 812 | 812 | 18.72 | 16 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 1 | development | BLOCKED | — | — | 279 | 270 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 2.21% | 13.40% | 201 | 181 | 181 | 17.13 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 1 | year_2021 | SUCCEEDED | -4.20% | 8.50% | 215 | 211 | 211 | 19.39 | 4 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -15.74% | 15.88% | 196 | 181 | 181 | 17.68 | 15 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | 2.19% | 7.73% | 214 | 200 | 200 | 18.48 | 14 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 1 | continuous_2020_2023 | SUCCEEDED | -14.13% | 23.57% | 815 | 801 | 801 | 18.53 | 14 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 3 | development | BLOCKED | — | — | 236 | 220 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 5.43% | 13.56% | 179 | 159 | 159 | 24.84 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | -3.47% | 11.26% | 161 | 154 | 154 | 33.42 | 7 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -12.16% | 15.53% | 182 | 163 | 163 | 22.75 | 19 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -8.47% | 13.47% | 198 | 181 | 181 | 27.13 | 17 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 3 | continuous_2020_2023 | SUCCEEDED | -18.29% | 29.68% | 708 | 691 | 691 | 27.88 | 17 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 6 | development | BLOCKED | — | — | 217 | 199 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 5.13% | 13.56% | 169 | 149 | 149 | 24.53 | 20 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | -3.26% | 11.90% | 153 | 145 | 145 | 35.52 | 8 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -11.58% | 14.79% | 173 | 154 | 154 | 24.53 | 19 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -8.05% | 13.24% | 194 | 175 | 175 | 27.55 | 19 | FULL_WINDOW |
| basic | BOLLINGER_REENTRY_2 | ATR_2_4 | 6 | continuous_2020_2023 | SUCCEEDED | -16.15% | 28.80% | 668 | 649 | 649 | 30.45 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 1 | development | BLOCKED | — | — | 3216 | 3204 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -16.62% | 17.85% | 1224 | 1209 | 1209 | 2.4 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -9.16% | 13.22% | 1276 | 1257 | 1257 | 3.16 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -20.57% | 20.64% | 970 | 964 | 964 | 3.0 | 6 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -22.50% | 25.17% | 1121 | 1109 | 1109 | 3.55 | 12 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -54.63% | 54.91% | 4559 | 4547 | 4547 | 3.1 | 12 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 3 | development | BLOCKED | — | — | 3186 | 3174 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -16.70% | 17.85% | 1218 | 1202 | 1202 | 2.34 | 16 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -8.64% | 13.34% | 1253 | 1234 | 1234 | 3.3 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -20.40% | 20.48% | 959 | 953 | 953 | 3.17 | 6 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -21.40% | 24.23% | 1064 | 1049 | 1049 | 3.69 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -53.59% | 53.93% | 4458 | 4443 | 4443 | 3.22 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 6 | development | BLOCKED | — | — | 3186 | 3174 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -16.70% | 17.85% | 1218 | 1202 | 1202 | 2.34 | 16 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -8.64% | 13.34% | 1253 | 1234 | 1234 | 3.3 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -19.94% | 20.02% | 955 | 949 | 949 | 3.25 | 6 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -21.40% | 24.23% | 1064 | 1049 | 1049 | 3.69 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -53.35% | 53.69% | 4454 | 4439 | 4439 | 3.24 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 1 | development | BLOCKED | — | — | 2042 | 2023 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 11.49% | 7.09% | 745 | 726 | 726 | 5.97 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | 11.67% | 6.52% | 742 | 723 | 723 | 7.52 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -21.17% | 21.27% | 701 | 686 | 686 | 6.83 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -14.70% | 19.11% | 715 | 697 | 697 | 7.49 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -12.46% | 34.61% | 2865 | 2847 | 2847 | 7.17 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 3 | development | BLOCKED | — | — | 1800 | 1781 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 10.24% | 7.28% | 695 | 676 | 676 | 6.2 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | 10.33% | 6.56% | 674 | 655 | 655 | 8.51 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -19.94% | 20.05% | 653 | 640 | 640 | 7.46 | 13 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -11.09% | 15.76% | 599 | 581 | 581 | 8.77 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -8.84% | 30.36% | 2563 | 2545 | 2545 | 8.11 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 6 | development | BLOCKED | — | — | 1778 | 1758 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 10.19% | 7.28% | 683 | 664 | 664 | 6.27 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | 10.33% | 6.56% | 674 | 655 | 655 | 8.51 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -19.48% | 19.59% | 644 | 631 | 631 | 7.65 | 13 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -9.42% | 13.95% | 585 | 567 | 567 | 8.63 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -5.59% | 28.46% | 2526 | 2508 | 2508 | 8.19 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 1624 | 1607 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 14.25% | 9.16% | 534 | 517 | 517 | 10.29 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 1 | year_2021 | BLOCKED | — | — | 155 | 138 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -22.51% | 22.66% | 564 | 550 | 550 | 10.29 | 14 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -21.47% | 25.16% | 571 | 555 | 555 | 10.29 | 16 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 1 | continuous_2020_2023 | BLOCKED | — | — | 678 | 661 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 1413 | 1397 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 21.13% | 8.57% | 448 | 431 | 431 | 12.32 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 3 | year_2021 | BLOCKED | — | — | 149 | 132 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -16.56% | 17.05% | 459 | 445 | 445 | 12.17 | 14 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -20.75% | 24.12% | 477 | 460 | 460 | 12.38 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 3 | continuous_2020_2023 | BLOCKED | — | — | 579 | 562 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 1398 | 1381 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | 22.44% | 8.57% | 438 | 421 | 421 | 11.8 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 6 | year_2021 | SUCCEEDED | 4.30% | 14.61% | 542 | 524 | 524 | 11.15 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -16.72% | 17.21% | 459 | 445 | 445 | 12.17 | 14 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -20.77% | 24.14% | 475 | 458 | 458 | 12.45 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_1_5_3 | 6 | continuous_2020_2023 | BLOCKED | — | — | 561 | 544 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 1 | development | BLOCKED | — | — | 206 | 186 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 15.87% | 11.96% | 407 | 387 | 387 | 14.76 | 20 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 1 | year_2021 | BLOCKED | — | — | 119 | 100 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -23.00% | 23.21% | 408 | 391 | 391 | 15.46 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -11.93% | 17.07% | 425 | 410 | 410 | 15.17 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 1 | continuous_2020_2023 | BLOCKED | — | — | 517 | 498 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 3 | development | BLOCKED | — | — | 830 | 810 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 18.07% | 12.26% | 279 | 260 | 260 | 21.55 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | 7.58% | 13.81% | 341 | 321 | 321 | 19.06 | 20 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -17.80% | 19.69% | 302 | 284 | 284 | 20.1 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -14.37% | 19.69% | 313 | 294 | 294 | 20.22 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 3 | continuous_2020_2023 | SUCCEEDED | -2.74% | 33.27% | 1171 | 1152 | 1152 | 21.99 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 6 | development | BLOCKED | — | — | 769 | 749 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 14.68% | 12.26% | 267 | 248 | 248 | 21.9 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | 11.38% | 13.39% | 334 | 314 | 314 | 19.19 | 20 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -17.38% | 19.30% | 292 | 274 | 274 | 20.92 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -14.00% | 19.46% | 299 | 280 | 280 | 20.32 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA60 | ATR_2_4 | 6 | continuous_2020_2023 | SUCCEEDED | -1.87% | 32.63% | 1127 | 1108 | 1108 | 22.7 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 1 | development | BLOCKED | — | — | 3335 | 3325 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -15.59% | 17.23% | 1242 | 1227 | 1227 | 2.39 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -6.23% | 11.15% | 1253 | 1236 | 1236 | 3.2 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -20.26% | 20.40% | 926 | 919 | 919 | 2.9 | 7 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -21.36% | 24.91% | 1165 | 1154 | 1154 | 3.28 | 11 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -51.61% | 52.07% | 4563 | 4552 | 4552 | 3.0 | 11 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 3 | development | BLOCKED | — | — | 3289 | 3279 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -14.48% | 16.56% | 1227 | 1213 | 1213 | 2.4 | 14 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -7.30% | 11.73% | 1226 | 1209 | 1209 | 3.37 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -19.80% | 19.95% | 920 | 913 | 913 | 3.02 | 7 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -21.04% | 24.44% | 1129 | 1117 | 1117 | 3.31 | 12 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -50.76% | 51.13% | 4480 | 4468 | 4468 | 3.09 | 12 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 6 | development | BLOCKED | — | — | 3289 | 3279 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -14.48% | 16.56% | 1227 | 1213 | 1213 | 2.4 | 14 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -7.30% | 11.73% | 1226 | 1209 | 1209 | 3.37 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -19.57% | 19.71% | 920 | 913 | 913 | 3.1 | 7 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -21.04% | 24.44% | 1129 | 1117 | 1117 | 3.31 | 12 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -50.63% | 50.99% | 4480 | 4468 | 4468 | 3.11 | 12 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 1 | development | BLOCKED | — | — | 2110 | 2092 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 11.65% | 7.02% | 764 | 747 | 747 | 5.76 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | 4.58% | 6.76% | 735 | 716 | 716 | 7.49 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -21.89% | 22.06% | 703 | 688 | 688 | 6.49 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -15.11% | 19.60% | 719 | 700 | 700 | 7.58 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -20.81% | 37.50% | 2879 | 2860 | 2860 | 7.06 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 3 | development | BLOCKED | — | — | 1900 | 1882 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 6.83% | 7.22% | 730 | 711 | 711 | 5.76 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | 3.85% | 6.36% | 667 | 648 | 648 | 8.48 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -23.22% | 23.38% | 672 | 658 | 658 | 6.96 | 14 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -12.14% | 17.30% | 630 | 611 | 611 | 8.65 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -23.93% | 37.23% | 2647 | 2628 | 2628 | 7.81 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 6 | development | BLOCKED | — | — | 1881 | 1863 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 5.78% | 7.22% | 721 | 702 | 702 | 5.72 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | 3.84% | 6.36% | 666 | 647 | 647 | 8.49 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -22.11% | 22.28% | 668 | 654 | 654 | 7.06 | 14 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -12.60% | 16.90% | 623 | 604 | 604 | 8.26 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -23.69% | 36.00% | 2623 | 2604 | 2604 | 7.79 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 1370 | 1350 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 9.96% | 12.24% | 539 | 523 | 523 | 10.58 | 16 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 1 | year_2021 | BLOCKED | — | — | 159 | 142 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -26.68% | 26.84% | 562 | 547 | 547 | 10.1 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -26.37% | 29.20% | 563 | 550 | 550 | 10.49 | 13 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 1 | continuous_2020_2023 | BLOCKED | — | — | 685 | 669 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 1176 | 1157 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 25.78% | 11.86% | 435 | 418 | 418 | 13.2 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 3 | year_2021 | BLOCKED | — | — | 149 | 133 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -19.19% | 20.43% | 474 | 459 | 459 | 11.83 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -18.03% | 23.34% | 502 | 486 | 486 | 11.75 | 16 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 3 | continuous_2020_2023 | BLOCKED | — | — | 569 | 553 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 1162 | 1143 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | 23.71% | 11.86% | 420 | 403 | 403 | 13.07 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 6 | year_2021 | SUCCEEDED | 3.15% | 14.34% | 542 | 524 | 524 | 11.34 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -19.31% | 20.54% | 474 | 459 | 459 | 11.83 | 15 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -18.21% | 23.51% | 501 | 485 | 485 | 11.78 | 16 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_1_5_3 | 6 | continuous_2020_2023 | SUCCEEDED | -10.88% | 40.14% | 1881 | 1865 | 1865 | 12.81 | 16 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 1 | development | BLOCKED | — | — | 214 | 194 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 15.78% | 13.83% | 415 | 395 | 395 | 15.1 | 20 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 1 | year_2021 | BLOCKED | — | — | 117 | 99 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -23.66% | 24.61% | 406 | 388 | 388 | 15.43 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -14.37% | 20.81% | 422 | 405 | 405 | 15.16 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 1 | continuous_2020_2023 | BLOCKED | — | — | 525 | 507 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 3 | development | BLOCKED | — | — | 155 | 139 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 23.74% | 14.36% | 285 | 266 | 266 | 22.35 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | 0.77% | 19.95% | 341 | 321 | 321 | 19.13 | 20 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -19.38% | 22.53% | 288 | 270 | 270 | 21.33 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -6.53% | 15.20% | 334 | 318 | 318 | 18.92 | 16 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 3 | continuous_2020_2023 | SUCCEEDED | -7.07% | 38.55% | 1198 | 1182 | 1182 | 21.67 | 16 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 6 | development | BLOCKED | — | — | 152 | 132 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 18.60% | 14.36% | 259 | 240 | 240 | 24.06 | 19 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | 7.29% | 16.32% | 331 | 311 | 311 | 19.78 | 20 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -20.23% | 23.36% | 275 | 257 | 257 | 22.47 | 18 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -7.93% | 16.60% | 322 | 305 | 305 | 19.13 | 17 | FULL_WINDOW |
| basic | MACD_CROSS_SMA120 | ATR_2_4 | 6 | continuous_2020_2023 | SUCCEEDED | -7.62% | 37.04% | 1118 | 1101 | 1101 | 23.18 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 1 | development | BLOCKED | — | — | 767 | 754 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -40.14% | 41.30% | 2182 | 2172 | 2172 | 1.38 | 10 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -39.33% | 40.12% | 2004 | 1989 | 1989 | 2.05 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -33.97% | 34.01% | 1673 | 1665 | 1665 | 2.22 | 8 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -35.97% | 37.50% | 1835 | 1820 | 1820 | 2.22 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -87.24% | 87.40% | 7650 | 7635 | 7635 | 1.98 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 3 | development | BLOCKED | — | — | 751 | 738 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -39.75% | 40.97% | 2171 | 2160 | 2160 | 1.37 | 11 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -40.70% | 41.43% | 1977 | 1962 | 1962 | 2.1 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -34.15% | 34.20% | 1657 | 1649 | 1649 | 2.26 | 8 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -35.29% | 36.79% | 1793 | 1778 | 1778 | 2.28 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -87.25% | 87.41% | 7545 | 7530 | 7530 | 2.02 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 6 | development | BLOCKED | — | — | 751 | 738 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -39.75% | 40.97% | 2171 | 2160 | 2160 | 1.37 | 11 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -40.70% | 41.43% | 1977 | 1962 | 1962 | 2.1 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -34.15% | 34.20% | 1657 | 1649 | 1649 | 2.26 | 8 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -35.29% | 36.79% | 1793 | 1778 | 1778 | 2.28 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -87.25% | 87.41% | 7545 | 7530 | 7530 | 2.02 | 15 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 1 | development | SUCCEEDED | -62.48% | 63.91% | 3849 | 3829 | 3829 | 6.94 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | -10.85% | 14.57% | 1238 | 1220 | 1220 | 3.83 | 18 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | -19.18% | 22.11% | 973 | 957 | 957 | 5.97 | 16 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -40.40% | 40.71% | 990 | 973 | 973 | 5.3 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -17.79% | 22.66% | 924 | 904 | 904 | 6.28 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -68.16% | 68.56% | 4101 | 4081 | 4081 | 5.32 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 3 | development | SUCCEEDED | -56.22% | 57.33% | 3361 | 3341 | 3341 | 8.11 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | -8.41% | 14.46% | 1206 | 1189 | 1189 | 3.91 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | -21.19% | 23.86% | 874 | 857 | 857 | 6.62 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -41.18% | 41.49% | 902 | 886 | 886 | 5.8 | 16 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -11.69% | 17.11% | 792 | 772 | 772 | 7.56 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -65.19% | 65.74% | 3737 | 3717 | 3717 | 5.96 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 6 | development | SUCCEEDED | -56.87% | 57.98% | 3303 | 3283 | 3283 | 8.27 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | -8.41% | 14.46% | 1206 | 1189 | 1189 | 3.91 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | -19.87% | 22.57% | 857 | 840 | 840 | 6.79 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -40.86% | 41.17% | 892 | 876 | 876 | 5.88 | 16 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -11.48% | 17.12% | 776 | 756 | 756 | 7.39 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -63.79% | 64.47% | 3689 | 3669 | 3669 | 5.98 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 884 | 867 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | -2.13% | 15.64% | 729 | 712 | 712 | 8.18 | 17 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 1 | year_2021 | SUCCEEDED | -15.97% | 26.43% | 717 | 697 | 697 | 8.65 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -43.93% | 44.14% | 669 | 653 | 653 | 9.16 | 16 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 1 | year_2023 | BLOCKED | — | — | 582 | 569 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 1 | continuous_2020_2023 | BLOCKED | — | — | 2657 | 2644 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 780 | 763 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | -2.75% | 15.64% | 596 | 578 | 578 | 10.01 | 18 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 3 | year_2021 | SUCCEEDED | -19.14% | 24.80% | 661 | 641 | 641 | 9.39 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -40.48% | 40.71% | 565 | 549 | 549 | 10.81 | 16 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 3 | year_2023 | BLOCKED | — | — | 514 | 501 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 3 | continuous_2020_2023 | BLOCKED | — | — | 2280 | 2267 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 770 | 753 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | -1.87% | 15.64% | 569 | 551 | 551 | 10.19 | 18 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 6 | year_2021 | SUCCEEDED | -20.12% | 25.79% | 653 | 633 | 633 | 9.53 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -40.08% | 40.31% | 560 | 544 | 544 | 10.92 | 16 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 6 | year_2023 | BLOCKED | — | — | 514 | 501 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_1_5_3 | 6 | continuous_2020_2023 | BLOCKED | — | — | 2244 | 2231 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 1 | development | BLOCKED | — | — | 218 | 199 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | -11.51% | 22.65% | 501 | 482 | 482 | 12.95 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 1 | year_2021 | SUCCEEDED | -13.28% | 24.16% | 499 | 479 | 479 | 13.36 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 1 | year_2022 | BLOCKED | — | — | 200 | 182 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 1 | year_2023 | BLOCKED | — | — | 381 | 366 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1167 | 1149 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 3 | development | BLOCKED | — | — | 168 | 149 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | -9.46% | 22.93% | 378 | 359 | 359 | 16.48 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | -19.52% | 28.69% | 406 | 386 | 386 | 16.15 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 3 | year_2022 | BLOCKED | — | — | 160 | 143 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -7.21% | 20.78% | 329 | 309 | 309 | 19.94 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 3 | continuous_2020_2023 | BLOCKED | — | — | 884 | 867 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 6 | development | BLOCKED | — | — | 167 | 147 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | -7.96% | 22.93% | 313 | 294 | 294 | 19.14 | 19 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | -19.68% | 29.61% | 393 | 373 | 373 | 16.66 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 6 | year_2022 | BLOCKED | — | — | 154 | 136 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -9.83% | 23.15% | 322 | 302 | 302 | 20.01 | 20 | FULL_WINDOW |
| basic | BREAKOUT_20_RVOL_1_5 | ATR_2_4 | 6 | continuous_2020_2023 | BLOCKED | — | — | 788 | 770 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 1 | development | SUCCEEDED | -86.72% | 86.90% | 6524 | 6508 | 6508 | 2.31 | 16 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -38.12% | 39.68% | 2093 | 2083 | 2083 | 1.13 | 10 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -38.73% | 40.37% | 2035 | 2026 | 2026 | 1.58 | 9 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -30.53% | 30.53% | 1444 | 1436 | 1436 | 1.82 | 8 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -38.05% | 38.96% | 1847 | 1832 | 1832 | 1.77 | 15 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -86.27% | 86.35% | 7403 | 7388 | 7388 | 1.57 | 15 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 3 | development | SUCCEEDED | -86.51% | 86.70% | 6448 | 6432 | 6432 | 2.38 | 16 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -38.12% | 39.68% | 2093 | 2083 | 2083 | 1.13 | 10 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -38.58% | 40.23% | 2013 | 2004 | 2004 | 1.62 | 9 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -30.34% | 30.35% | 1442 | 1434 | 1434 | 1.84 | 8 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -36.85% | 37.83% | 1822 | 1807 | 1807 | 1.82 | 15 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -85.91% | 86.00% | 7354 | 7339 | 7339 | 1.6 | 15 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 6 | development | SUCCEEDED | -86.44% | 86.63% | 6447 | 6431 | 6431 | 2.38 | 16 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -38.12% | 39.68% | 2093 | 2083 | 2083 | 1.13 | 10 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -38.58% | 40.23% | 2013 | 2004 | 2004 | 1.62 | 9 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -30.34% | 30.35% | 1442 | 1434 | 1434 | 1.84 | 8 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -36.85% | 37.83% | 1822 | 1807 | 1807 | 1.82 | 15 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -85.91% | 86.00% | 7354 | 7339 | 7339 | 1.6 | 15 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 1 | development | SUCCEEDED | -67.35% | 68.20% | 3912 | 3894 | 3894 | 6.04 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | -12.81% | 18.44% | 1239 | 1222 | 1222 | 3.41 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | -24.17% | 28.75% | 1159 | 1141 | 1141 | 4.51 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -36.51% | 36.92% | 937 | 923 | 923 | 4.69 | 14 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -17.13% | 20.60% | 1033 | 1014 | 1014 | 5.06 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -67.46% | 67.84% | 4344 | 4325 | 4325 | 4.47 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 3 | development | SUCCEEDED | -67.75% | 68.42% | 3525 | 3506 | 3506 | 6.92 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | -12.48% | 18.12% | 1186 | 1168 | 1168 | 3.56 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | -22.65% | 26.98% | 1043 | 1026 | 1026 | 5.03 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -35.33% | 35.74% | 886 | 872 | 872 | 4.92 | 14 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -14.88% | 18.71% | 915 | 896 | 896 | 5.95 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -64.74% | 65.14% | 3981 | 3962 | 3962 | 5.05 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 6 | development | SUCCEEDED | -67.82% | 68.48% | 3488 | 3469 | 3469 | 7.01 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | -12.43% | 18.06% | 1185 | 1167 | 1167 | 3.56 | 18 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | -22.38% | 26.74% | 1040 | 1023 | 1023 | 5.05 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -34.43% | 34.85% | 879 | 865 | 865 | 4.97 | 14 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -16.57% | 20.25% | 911 | 892 | 892 | 5.76 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -64.86% | 65.23% | 3964 | 3945 | 3945 | 5.03 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 1 | development | BLOCKED | — | — | 43 | 24 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | -6.11% | 16.94% | 733 | 716 | 716 | 7.86 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 1 | year_2021 | BLOCKED | — | — | 184 | 168 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -45.62% | 45.79% | 678 | 661 | 661 | 8.13 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -29.43% | 34.52% | 714 | 694 | 694 | 8.37 | 20 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 1 | continuous_2020_2023 | BLOCKED | — | — | 900 | 884 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 3 | development | BLOCKED | — | — | 43 | 24 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | -9.61% | 16.82% | 593 | 576 | 576 | 9.95 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 3 | year_2021 | BLOCKED | — | — | 168 | 151 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -39.08% | 39.28% | 610 | 593 | 593 | 9.09 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -25.04% | 31.94% | 619 | 599 | 599 | 9.69 | 20 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 3 | continuous_2020_2023 | BLOCKED | — | — | 734 | 717 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 6 | development | BLOCKED | — | — | 43 | 24 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | -8.78% | 16.82% | 576 | 559 | 559 | 9.69 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 6 | year_2021 | BLOCKED | — | — | 168 | 151 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -39.13% | 39.33% | 609 | 592 | 592 | 9.1 | 17 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -24.92% | 31.92% | 618 | 598 | 598 | 9.55 | 20 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_1_5_3 | 6 | continuous_2020_2023 | BLOCKED | — | — | 710 | 693 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 1 | development | BLOCKED | — | — | 241 | 221 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | -9.95% | 21.90% | 490 | 470 | 470 | 13.08 | 20 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 1 | year_2021 | SUCCEEDED | -6.05% | 22.36% | 482 | 463 | 463 | 13.71 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 1 | year_2022 | BLOCKED | — | — | 204 | 186 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -8.06% | 20.98% | 485 | 465 | 465 | 13.64 | 20 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1146 | 1128 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 3 | development | BLOCKED | — | — | 181 | 161 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 4.01% | 17.13% | 345 | 326 | 326 | 18.44 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | -7.18% | 20.13% | 363 | 344 | 344 | 18.33 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 3 | year_2022 | BLOCKED | — | — | 172 | 154 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -15.83% | 26.12% | 355 | 335 | 335 | 18.35 | 20 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 3 | continuous_2020_2023 | BLOCKED | — | — | 818 | 800 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 6 | development | BLOCKED | — | — | 172 | 152 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 6.39% | 17.13% | 320 | 300 | 300 | 18.92 | 20 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | -6.74% | 19.84% | 359 | 340 | 340 | 18.57 | 19 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 6 | year_2022 | BLOCKED | — | — | 168 | 150 | — | — | — | PARTIAL_BEFORE_BLOCK |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -10.53% | 22.23% | 338 | 318 | 318 | 18.53 | 20 | FULL_WINDOW |
| basic | BREAKOUT_60_RVOL_1_5 | ATR_2_4 | 6 | continuous_2020_2023 | BLOCKED | — | — | 774 | 756 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_8_16 | 1 | development | BLOCKED | — | — | 1459 | 1441 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 13.06% | 12.43% | 484 | 465 | 465 | 11.9 | 19 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_8_16 | 1 | year_2021 | SUCCEEDED | 0.56% | 14.48% | 425 | 408 | 408 | 15.59 | 17 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -26.00% | 26.17% | 445 | 427 | 427 | 14.3 | 18 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_8_16 | 1 | year_2023 | BLOCKED | — | — | 342 | 326 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_8_16 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1665 | 1649 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_8_16 | 3 | development | BLOCKED | — | — | 250 | 230 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 17.45% | 12.39% | 413 | 394 | 394 | 13.16 | 19 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | 0.72% | 12.69% | 311 | 293 | 293 | 21.24 | 18 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -19.64% | 21.37% | 329 | 312 | 312 | 19.3 | 17 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_8_16 | 3 | year_2023 | BLOCKED | — | — | 242 | 224 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_8_16 | 3 | continuous_2020_2023 | BLOCKED | — | — | 1239 | 1221 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_8_16 | 6 | development | BLOCKED | — | — | 233 | 213 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 17.97% | 12.39% | 414 | 395 | 395 | 12.93 | 19 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | 2.39% | 11.66% | 295 | 277 | 277 | 22.55 | 18 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -19.68% | 20.63% | 296 | 277 | 277 | 20.93 | 19 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_8_16 | 6 | year_2023 | BLOCKED | — | — | 231 | 213 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_8_16 | 6 | continuous_2020_2023 | BLOCKED | — | — | 1172 | 1154 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_10_20 | 1 | development | BLOCKED | — | — | 184 | 165 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 12.59% | 16.26% | 381 | 361 | 361 | 16.01 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | -2.72% | 14.27% | 366 | 346 | 346 | 19.04 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -21.80% | 23.24% | 378 | 362 | 362 | 17.64 | 16 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_10_20 | 1 | year_2023 | BLOCKED | — | — | 298 | 282 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_10_20 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1398 | 1382 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_10_20 | 3 | development | SUCCEEDED | -23.31% | 28.81% | 890 | 870 | 870 | 35.69 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 9.62% | 16.98% | 283 | 263 | 263 | 20.22 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | -5.06% | 16.55% | 239 | 219 | 219 | 28.6 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -21.49% | 23.34% | 263 | 245 | 245 | 24.66 | 18 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_10_20 | 3 | year_2023 | BLOCKED | — | — | 188 | 170 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_10_20 | 3 | continuous_2020_2023 | BLOCKED | — | — | 915 | 898 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_10_20 | 6 | development | BLOCKED | — | — | 244 | 225 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 8.80% | 16.98% | 270 | 251 | 251 | 20.44 | 19 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | -4.94% | 16.47% | 214 | 194 | 194 | 30.91 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -19.64% | 22.90% | 238 | 219 | 219 | 26.74 | 19 | FULL_WINDOW |
| wide | CROSS_5_20 | PCT_10_20 | 6 | year_2023 | BLOCKED | — | — | 182 | 165 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | PCT_10_20 | 6 | continuous_2020_2023 | BLOCKED | — | — | 826 | 809 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_3_6 | 1 | development | BLOCKED | — | — | 157 | 137 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 2.55% | 15.71% | 320 | 300 | 300 | 20.56 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 9.74% | 11.40% | 320 | 300 | 300 | 22.49 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -17.77% | 22.78% | 323 | 306 | 306 | 21.78 | 17 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_3_6 | 1 | year_2023 | BLOCKED | — | — | 255 | 240 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1181 | 1166 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_3_6 | 3 | development | BLOCKED | — | — | 92 | 73 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 6.81% | 15.94% | 204 | 184 | 184 | 33.23 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | 10.82% | 10.61% | 192 | 172 | 172 | 36.5 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_3_6 | 3 | year_2022 | SUCCEEDED | -13.21% | 16.77% | 188 | 170 | 170 | 38.21 | 18 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_3_6 | 3 | year_2023 | BLOCKED | — | — | 140 | 122 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 680 | 662 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_3_6 | 6 | development | BLOCKED | — | — | 77 | 57 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 10.52% | 15.94% | 180 | 160 | 160 | 35.02 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 7.56% | 14.18% | 165 | 145 | 145 | 41.48 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -12.84% | 16.66% | 147 | 131 | 131 | 48.04 | 16 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_3_6 | 6 | year_2023 | BLOCKED | — | — | 125 | 107 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_3_6 | 6 | continuous_2020_2023 | BLOCKED | — | — | 573 | 555 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_4_8 | 1 | development | BLOCKED | — | — | 134 | 115 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | -0.73% | 13.08% | 280 | 260 | 260 | 24.1 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_4_8 | 1 | year_2021 | SUCCEEDED | 7.69% | 10.59% | 290 | 271 | 271 | 25.59 | 19 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -17.00% | 20.70% | 285 | 266 | 266 | 25.12 | 19 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_4_8 | 1 | year_2023 | BLOCKED | — | — | 215 | 199 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_4_8 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1046 | 1030 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_4_8 | 3 | development | BLOCKED | — | — | 70 | 51 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 3.61% | 10.75% | 149 | 130 | 130 | 45.95 | 19 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_4_8 | 3 | year_2021 | BLOCKED | — | — | 50 | 30 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -12.11% | 15.32% | 140 | 121 | 121 | 50.8 | 19 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_4_8 | 3 | year_2023 | BLOCKED | — | — | 99 | 80 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_4_8 | 3 | continuous_2020_2023 | BLOCKED | — | — | 190 | 170 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_4_8 | 6 | development | BLOCKED | — | — | 54 | 34 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 11.80% | 10.75% | 125 | 106 | 106 | 51.25 | 19 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_4_8 | 6 | year_2021 | BLOCKED | — | — | 46 | 26 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -11.19% | 13.87% | 101 | 81 | 81 | 75.16 | 20 | FULL_WINDOW |
| wide | CROSS_5_20 | ATR_4_8 | 6 | year_2023 | BLOCKED | — | — | 86 | 67 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_5_20 | ATR_4_8 | 6 | continuous_2020_2023 | BLOCKED | — | — | 153 | 133 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | PCT_8_16 | 1 | development | BLOCKED | — | — | 760 | 740 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 8.33% | 8.18% | 437 | 418 | 418 | 13.39 | 19 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 1 | year_2021 | SUCCEEDED | 6.45% | 12.35% | 440 | 420 | 420 | 15.11 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -16.21% | 20.82% | 457 | 441 | 441 | 13.33 | 16 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | -0.12% | 7.94% | 420 | 400 | 400 | 16.3 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 1 | continuous_2020_2023 | SUCCEEDED | -0.58% | 25.83% | 1708 | 1688 | 1688 | 14.93 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 3 | development | SUCCEEDED | -22.43% | 28.61% | 1230 | 1210 | 1210 | 24.91 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 14.66% | 8.60% | 355 | 336 | 336 | 16.83 | 19 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | 7.30% | 11.25% | 336 | 317 | 317 | 19.79 | 19 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -19.40% | 21.67% | 351 | 336 | 336 | 16.87 | 15 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | 5.87% | 6.68% | 255 | 235 | 235 | 26.2 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | 11.81% | 23.77% | 1229 | 1209 | 1209 | 21.0 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 6 | development | SUCCEEDED | -19.01% | 25.76% | 1111 | 1091 | 1091 | 27.13 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 15.49% | 8.60% | 346 | 327 | 327 | 16.2 | 19 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | 6.99% | 11.15% | 306 | 288 | 288 | 21.96 | 18 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -18.37% | 19.74% | 316 | 301 | 301 | 18.31 | 15 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | 10.17% | 5.00% | 232 | 212 | 212 | 25.84 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | 6.66% | 24.97% | 1132 | 1112 | 1112 | 22.27 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 1 | development | BLOCKED | — | — | 629 | 610 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 22.69% | 8.75% | 379 | 359 | 359 | 16.15 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | 2.44% | 14.70% | 361 | 344 | 344 | 19.16 | 17 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 1 | year_2022 | BLOCKED | — | — | 98 | 78 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | -0.57% | 8.33% | 348 | 328 | 328 | 20.12 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 1 | continuous_2020_2023 | BLOCKED | — | — | 814 | 794 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | PCT_10_20 | 3 | development | BLOCKED | — | — | 136 | 118 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 16.33% | 10.10% | 286 | 266 | 266 | 21.91 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | 5.54% | 13.23% | 225 | 205 | 205 | 31.0 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -26.38% | 28.79% | 267 | 250 | 250 | 23.15 | 17 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | 7.73% | 5.65% | 180 | 160 | 160 | 39.23 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | -5.50% | 34.40% | 927 | 907 | 907 | 28.86 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 6 | development | SUCCEEDED | -21.76% | 30.90% | 779 | 759 | 759 | 40.12 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 14.63% | 10.10% | 263 | 243 | 243 | 21.78 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | -0.64% | 16.94% | 203 | 183 | 183 | 34.38 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -23.37% | 27.19% | 249 | 234 | 234 | 25.06 | 15 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 6 | year_2023 | SUCCEEDED | 5.81% | 7.40% | 150 | 131 | 131 | 40.95 | 19 | FULL_WINDOW |
| wide | CROSS_10_20 | PCT_10_20 | 6 | continuous_2020_2023 | SUCCEEDED | -0.95% | 31.30% | 812 | 793 | 793 | 32.26 | 19 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 1 | development | BLOCKED | — | — | 148 | 129 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 7.26% | 12.89% | 304 | 284 | 284 | 21.05 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 6.28% | 11.18% | 326 | 310 | 310 | 21.77 | 16 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -28.67% | 30.60% | 320 | 302 | 302 | 20.84 | 18 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | -1.03% | 10.08% | 310 | 290 | 290 | 23.19 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -10.69% | 30.53% | 1230 | 1210 | 1210 | 22.1 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 3 | development | BLOCKED | — | — | 229 | 209 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 5.91% | 13.09% | 183 | 163 | 163 | 36.76 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | 4.36% | 13.49% | 188 | 168 | 168 | 36.58 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 3 | year_2022 | SUCCEEDED | -24.13% | 24.70% | 189 | 170 | 170 | 34.58 | 19 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | 7.96% | 5.89% | 160 | 140 | 140 | 44.76 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -1.21% | 28.46% | 683 | 663 | 663 | 40.64 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 6 | development | SUCCEEDED | -20.49% | 23.39% | 590 | 570 | 570 | 53.85 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 1.84% | 13.09% | 145 | 125 | 125 | 45.45 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | -1.60% | 16.01% | 167 | 147 | 147 | 40.69 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -19.04% | 23.98% | 164 | 146 | 146 | 41.64 | 18 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | 13.80% | 6.19% | 144 | 124 | 124 | 45.91 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -5.32% | 30.02% | 551 | 531 | 531 | 49.38 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 1 | development | SUCCEEDED | -8.80% | 15.91% | 1225 | 1205 | 1205 | 26.5 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 10.30% | 11.61% | 272 | 252 | 252 | 24.31 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 1 | year_2021 | SUCCEEDED | 21.70% | 6.44% | 279 | 263 | 263 | 26.14 | 16 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -22.08% | 23.23% | 277 | 257 | 257 | 25.61 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | -1.07% | 11.02% | 281 | 261 | 261 | 26.02 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 1 | continuous_2020_2023 | SUCCEEDED | -1.67% | 23.40% | 1078 | 1058 | 1058 | 25.83 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 3 | development | BLOCKED | — | — | 73 | 56 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 7.97% | 12.49% | 139 | 119 | 119 | 51.3 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 3 | year_2021 | SUCCEEDED | 0.82% | 15.18% | 150 | 130 | 130 | 48.74 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 3 | year_2022 | BLOCKED | — | — | 49 | 29 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | 5.10% | 4.98% | 135 | 115 | 115 | 53.8 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 3 | continuous_2020_2023 | SUCCEEDED | 2.56% | 20.86% | 515 | 495 | 495 | 55.43 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 6 | development | BLOCKED | — | — | 154 | 135 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 7.95% | 12.49% | 111 | 91 | 91 | 60.07 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | 1.19% | 12.94% | 120 | 100 | 100 | 58.53 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 6 | year_2022 | BLOCKED | — | — | 49 | 29 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | CROSS_10_20 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | 7.49% | 6.22% | 99 | 79 | 79 | 68.06 | 20 | FULL_WINDOW |
| wide | CROSS_10_20 | ATR_4_8 | 6 | continuous_2020_2023 | SUCCEEDED | 2.50% | 23.43% | 372 | 352 | 352 | 75.68 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 1 | development | SUCCEEDED | -40.47% | 44.06% | 2172 | 2152 | 2152 | 14.12 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 8.62% | 16.08% | 668 | 648 | 648 | 9.03 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 1 | year_2021 | SUCCEEDED | -10.23% | 17.82% | 529 | 510 | 510 | 12.53 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -29.29% | 30.60% | 558 | 543 | 543 | 11.29 | 15 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | -8.05% | 17.19% | 485 | 465 | 465 | 13.83 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 1 | continuous_2020_2023 | SUCCEEDED | -36.11% | 43.95% | 2208 | 2188 | 2188 | 11.72 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 3 | development | SUCCEEDED | -43.26% | 46.12% | 1532 | 1512 | 1512 | 20.14 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 10.21% | 15.85% | 555 | 536 | 536 | 10.61 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | -10.03% | 17.71% | 366 | 348 | 348 | 18.15 | 18 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -29.90% | 30.70% | 432 | 417 | 417 | 13.88 | 15 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | 1.35% | 11.59% | 313 | 293 | 293 | 20.95 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | -31.82% | 41.11% | 1632 | 1612 | 1612 | 15.93 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 6 | development | BLOCKED | — | — | 1108 | 1088 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 10.20% | 15.85% | 562 | 543 | 543 | 10.28 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | -9.81% | 16.53% | 354 | 337 | 337 | 18.75 | 17 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -28.20% | 29.70% | 416 | 400 | 400 | 14.03 | 16 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | 3.35% | 10.74% | 277 | 257 | 257 | 19.9 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | -31.65% | 40.87% | 1555 | 1535 | 1535 | 16.07 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 1 | development | BLOCKED | — | — | 222 | 202 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 17.55% | 16.72% | 507 | 487 | 487 | 12.63 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | 1.56% | 14.43% | 432 | 412 | 412 | 15.84 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -27.14% | 27.41% | 446 | 427 | 427 | 14.92 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | -6.11% | 13.60% | 398 | 378 | 378 | 17.24 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 1 | continuous_2020_2023 | SUCCEEDED | -24.69% | 44.55% | 1732 | 1712 | 1712 | 15.53 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 3 | development | BLOCKED | — | — | 162 | 142 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 10.77% | 13.94% | 386 | 367 | 367 | 15.95 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | -4.92% | 15.18% | 277 | 257 | 257 | 24.89 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -30.32% | 30.58% | 329 | 310 | 310 | 18.81 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | -7.61% | 13.87% | 228 | 208 | 208 | 29.48 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | -25.69% | 41.78% | 1153 | 1133 | 1133 | 23.26 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 6 | development | BLOCKED | — | — | 151 | 131 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 14.16% | 13.94% | 366 | 347 | 347 | 16.48 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | -5.15% | 18.21% | 250 | 230 | 230 | 26.93 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -25.45% | 27.31% | 308 | 288 | 288 | 19.93 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | PCT_10_20 | 6 | year_2023 | BLOCKED | — | — | 196 | 176 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | PCT_10_20 | 6 | continuous_2020_2023 | BLOCKED | — | — | 1030 | 1011 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | ATR_3_6 | 1 | development | BLOCKED | — | — | 158 | 138 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 3.37% | 17.49% | 343 | 323 | 323 | 20.26 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 9.17% | 12.32% | 335 | 315 | 315 | 21.64 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_3_6 | 1 | year_2022 | BLOCKED | — | — | 137 | 117 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | -2.48% | 13.06% | 326 | 306 | 306 | 22.19 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 771 | 751 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | ATR_3_6 | 3 | development | BLOCKED | — | — | 102 | 82 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 5.24% | 15.91% | 195 | 175 | 175 | 35.5 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | -2.91% | 18.29% | 206 | 186 | 186 | 33.68 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_3_6 | 3 | year_2022 | BLOCKED | — | — | 93 | 74 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | 3.54% | 7.47% | 169 | 149 | 149 | 41.28 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -25.04% | 41.23% | 713 | 693 | 693 | 39.15 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_3_6 | 6 | development | BLOCKED | — | — | 90 | 70 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 2.23% | 16.11% | 162 | 142 | 142 | 39.76 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 3.75% | 14.47% | 172 | 152 | 152 | 39.86 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -16.92% | 19.60% | 179 | 164 | 164 | 37.38 | 15 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | -0.47% | 10.27% | 134 | 115 | 115 | 47.01 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -10.90% | 33.30% | 590 | 571 | 571 | 46.84 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 1 | development | BLOCKED | — | — | 378 | 359 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 7.93% | 12.52% | 294 | 274 | 274 | 24.54 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 1 | year_2021 | SUCCEEDED | 6.34% | 10.24% | 288 | 268 | 268 | 25.75 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -13.99% | 15.77% | 289 | 269 | 269 | 25.58 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | 5.24% | 6.43% | 278 | 258 | 258 | 26.43 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1102 | 1083 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | ATR_4_8 | 3 | development | BLOCKED | — | — | 188 | 168 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 4.48% | 15.31% | 146 | 127 | 127 | 49.77 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 3 | year_2021 | SUCCEEDED | 7.91% | 10.27% | 143 | 124 | 124 | 50.52 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -14.96% | 18.99% | 150 | 130 | 130 | 49.7 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | -2.70% | 8.65% | 126 | 106 | 106 | 58.31 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 3 | continuous_2020_2023 | SUCCEEDED | -9.25% | 27.71% | 523 | 503 | 503 | 54.64 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 6 | development | BLOCKED | — | — | 88 | 68 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 8.65% | 15.31% | 110 | 90 | 90 | 62.28 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | 7.04% | 10.40% | 116 | 97 | 97 | 62.4 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -15.86% | 17.08% | 114 | 95 | 95 | 59.06 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | 2.66% | 5.42% | 99 | 79 | 79 | 70.66 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20 | ATR_4_8 | 6 | continuous_2020_2023 | SUCCEEDED | 6.04% | 19.59% | 387 | 367 | 367 | 73.72 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 1 | development | SUCCEEDED | -58.86% | 62.74% | 2348 | 2329 | 2329 | 12.58 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 1.67% | 16.88% | 711 | 693 | 693 | 8.04 | 18 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 1 | year_2021 | SUCCEEDED | -17.34% | 26.00% | 581 | 564 | 564 | 11.0 | 17 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -34.53% | 36.07% | 602 | 585 | 585 | 9.6 | 17 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | -8.30% | 17.19% | 567 | 547 | 547 | 11.5 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 1 | continuous_2020_2023 | SUCCEEDED | -48.87% | 54.61% | 2414 | 2394 | 2394 | 10.27 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 3 | development | SUCCEEDED | -42.40% | 49.25% | 1700 | 1680 | 1680 | 17.7 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 2.02% | 16.28% | 612 | 596 | 596 | 9.36 | 16 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | -15.92% | 24.04% | 440 | 422 | 422 | 14.4 | 18 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -33.37% | 35.22% | 488 | 470 | 470 | 11.18 | 18 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | -7.41% | 17.02% | 390 | 370 | 370 | 15.91 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | -42.03% | 48.57% | 1852 | 1832 | 1832 | 13.41 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 6 | development | SUCCEEDED | -38.06% | 44.76% | 1586 | 1566 | 1566 | 19.06 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 2.98% | 16.28% | 597 | 581 | 581 | 9.25 | 16 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | -14.40% | 23.06% | 427 | 409 | 409 | 14.9 | 18 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -32.98% | 34.82% | 465 | 446 | 446 | 11.85 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | -3.73% | 14.23% | 365 | 345 | 345 | 15.17 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | -36.84% | 44.19% | 1764 | 1744 | 1744 | 13.87 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 1 | development | BLOCKED | — | — | 65 | 51 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 13.00% | 11.94% | 538 | 518 | 518 | 11.47 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | -6.36% | 25.92% | 472 | 453 | 453 | 14.1 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -41.13% | 41.13% | 481 | 465 | 465 | 12.84 | 16 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | -4.42% | 14.66% | 458 | 438 | 438 | 14.53 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 1 | continuous_2020_2023 | SUCCEEDED | -36.73% | 54.34% | 1912 | 1892 | 1892 | 13.54 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 3 | development | BLOCKED | — | — | 65 | 51 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 12.52% | 12.69% | 407 | 387 | 387 | 14.75 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | -5.85% | 21.29% | 338 | 318 | 318 | 19.78 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -34.88% | 36.05% | 372 | 353 | 353 | 15.82 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | -4.89% | 13.52% | 293 | 273 | 273 | 21.66 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | -33.84% | 49.49% | 1308 | 1288 | 1288 | 19.8 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 6 | development | BLOCKED | — | — | 65 | 51 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 14.85% | 12.69% | 403 | 384 | 384 | 14.27 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | -1.26% | 20.77% | 307 | 287 | 287 | 21.85 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -30.00% | 32.20% | 342 | 324 | 324 | 17.67 | 18 | FULL_WINDOW |
| wide | BREAKOUT_60 | PCT_10_20 | 6 | year_2023 | BLOCKED | — | — | 233 | 215 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | PCT_10_20 | 6 | continuous_2020_2023 | BLOCKED | — | — | 1201 | 1182 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_3_6 | 1 | development | BLOCKED | — | — | 162 | 143 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 11.67% | 14.22% | 329 | 309 | 309 | 21.17 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 0.58% | 19.56% | 334 | 314 | 314 | 21.42 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_3_6 | 1 | year_2022 | BLOCKED | — | — | 133 | 113 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | 2.61% | 10.12% | 334 | 314 | 314 | 21.31 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 776 | 756 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_3_6 | 3 | development | BLOCKED | — | — | 107 | 87 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 5.22% | 17.77% | 177 | 157 | 157 | 38.97 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | -0.95% | 20.06% | 210 | 190 | 190 | 33.05 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_3_6 | 3 | year_2022 | BLOCKED | — | — | 87 | 68 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | -3.08% | 11.71% | 176 | 156 | 156 | 38.94 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 217 | 199 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_3_6 | 6 | development | BLOCKED | — | — | 89 | 69 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 8.05% | 17.77% | 151 | 131 | 131 | 40.64 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 1.72% | 20.05% | 195 | 175 | 175 | 34.74 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_3_6 | 6 | year_2022 | BLOCKED | — | — | 73 | 53 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | 2.18% | 7.79% | 146 | 126 | 126 | 44.46 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_3_6 | 6 | continuous_2020_2023 | BLOCKED | — | — | 355 | 335 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_4_8 | 1 | development | BLOCKED | — | — | 623 | 604 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 5.91% | 12.38% | 293 | 274 | 274 | 24.43 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 1 | year_2021 | SUCCEEDED | -0.53% | 14.75% | 287 | 267 | 267 | 25.66 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -20.19% | 21.17% | 281 | 262 | 262 | 25.83 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 1 | year_2023 | BLOCKED | — | — | 268 | 248 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_4_8 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1107 | 1087 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_4_8 | 3 | development | BLOCKED | — | — | 176 | 156 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 8.12% | 14.01% | 134 | 115 | 115 | 54.97 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 3 | year_2021 | SUCCEEDED | 3.14% | 12.41% | 147 | 127 | 127 | 49.57 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -17.24% | 17.90% | 144 | 126 | 126 | 48.39 | 18 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | 0.30% | 5.30% | 126 | 106 | 106 | 56.29 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 3 | continuous_2020_2023 | SUCCEEDED | -14.60% | 31.66% | 509 | 489 | 489 | 56.04 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 6 | development | BLOCKED | — | — | 62 | 43 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 10.10% | 14.01% | 102 | 82 | 82 | 63.23 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | 1.64% | 11.54% | 121 | 101 | 101 | 60.83 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -19.36% | 20.62% | 112 | 93 | 93 | 58.37 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | 2.04% | 6.14% | 99 | 79 | 79 | 71.16 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60 | ATR_4_8 | 6 | continuous_2020_2023 | SUCCEEDED | 4.45% | 23.84% | 369 | 349 | 349 | 77.27 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 1 | development | BLOCKED | — | — | 1888 | 1868 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 8.95% | 18.59% | 541 | 521 | 521 | 11.79 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 1 | year_2021 | BLOCKED | — | — | 151 | 133 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -13.74% | 15.36% | 609 | 594 | 594 | 10.69 | 15 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | -8.42% | 22.74% | 548 | 528 | 528 | 12.07 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 1 | continuous_2020_2023 | BLOCKED | — | — | 674 | 656 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 3 | development | BLOCKED | — | — | 1443 | 1423 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 10.84% | 18.59% | 455 | 435 | 435 | 13.63 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | 20.25% | 13.97% | 412 | 392 | 392 | 16.19 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -16.27% | 19.35% | 507 | 493 | 493 | 12.86 | 14 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | -3.69% | 18.22% | 409 | 389 | 389 | 15.62 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 3 | continuous_2020_2023 | BLOCKED | — | — | 551 | 534 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 6 | development | BLOCKED | — | — | 1376 | 1356 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 9.66% | 18.59% | 450 | 430 | 430 | 13.39 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | 21.98% | 14.22% | 406 | 386 | 386 | 16.44 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -15.30% | 19.19% | 482 | 468 | 468 | 13.58 | 14 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | -4.41% | 18.51% | 390 | 370 | 370 | 16.62 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_8_16 | 6 | continuous_2020_2023 | BLOCKED | — | — | 534 | 517 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 1 | development | BLOCKED | — | — | 1519 | 1499 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 8.75% | 20.38% | 443 | 423 | 423 | 15.12 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 1 | year_2021 | BLOCKED | — | — | 125 | 106 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -17.29% | 17.80% | 460 | 442 | 442 | 14.86 | 18 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | -2.63% | 19.54% | 431 | 412 | 412 | 15.81 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 1 | continuous_2020_2023 | SUCCEEDED | -15.14% | 38.30% | 1740 | 1721 | 1721 | 15.55 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 3 | development | BLOCKED | — | — | 985 | 965 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 1.74% | 21.51% | 336 | 316 | 316 | 18.68 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 3 | year_2021 | BLOCKED | — | — | 78 | 59 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 3 | year_2022 | BLOCKED | — | — | 218 | 199 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | -3.07% | 21.27% | 302 | 282 | 282 | 21.34 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 3 | continuous_2020_2023 | BLOCKED | — | — | 816 | 797 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 6 | development | BLOCKED | — | — | 485 | 467 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 0.65% | 21.51% | 312 | 292 | 292 | 19.61 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | -2.22% | 22.19% | 266 | 247 | 247 | 25.59 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 6 | year_2022 | BLOCKED | — | — | 200 | 181 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 6 | year_2023 | SUCCEEDED | 1.20% | 16.09% | 272 | 252 | 252 | 23.56 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | PCT_10_20 | 6 | continuous_2020_2023 | BLOCKED | — | — | 753 | 734 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 1 | development | BLOCKED | — | — | 521 | 502 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 1 | year_2020 | BLOCKED | — | — | 94 | 75 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 9.39% | 7.80% | 285 | 265 | 265 | 26.26 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -13.39% | 13.70% | 292 | 272 | 272 | 25.27 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | -4.52% | 11.85% | 276 | 256 | 256 | 26.68 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 94 | 75 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 3 | development | BLOCKED | — | — | 227 | 209 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 3 | year_2020 | BLOCKED | — | — | 74 | 55 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | 7.54% | 15.62% | 140 | 121 | 121 | 53.52 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 3 | year_2022 | SUCCEEDED | -11.47% | 15.56% | 147 | 127 | 127 | 52.46 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | 5.79% | 11.60% | 128 | 108 | 108 | 56.73 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 74 | 55 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 6 | development | BLOCKED | — | — | 305 | 285 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 6 | year_2020 | BLOCKED | — | — | 74 | 55 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 8.54% | 13.84% | 105 | 86 | 86 | 70.63 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 6 | year_2022 | BLOCKED | — | — | 72 | 52 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 6 | year_2023 | BLOCKED | — | — | 78 | 59 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_3_6 | 6 | continuous_2020_2023 | BLOCKED | — | — | 74 | 55 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 1 | development | BLOCKED | — | — | 72 | 60 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 11.00% | 13.05% | 267 | 247 | 247 | 27.91 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 1 | year_2021 | BLOCKED | — | — | 86 | 66 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -8.20% | 12.01% | 267 | 247 | 247 | 28.12 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | -8.58% | 13.57% | 261 | 241 | 241 | 28.88 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 1 | continuous_2020_2023 | SUCCEEDED | 6.97% | 13.96% | 1034 | 1014 | 1014 | 28.29 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 3 | development | BLOCKED | — | — | 108 | 89 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 5.48% | 14.66% | 126 | 106 | 106 | 60.9 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 3 | year_2021 | BLOCKED | — | — | 45 | 25 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -11.54% | 13.89% | 117 | 97 | 97 | 68.65 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | 4.59% | 5.43% | 105 | 85 | 85 | 74.12 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 3 | continuous_2020_2023 | SUCCEEDED | -2.20% | 20.86% | 424 | 404 | 404 | 69.14 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 6 | development | BLOCKED | — | — | 31 | 11 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 8.06% | 14.66% | 92 | 73 | 73 | 79.22 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | 11.97% | 9.46% | 84 | 65 | 65 | 94.58 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -13.50% | 13.91% | 82 | 62 | 62 | 93.63 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | 0.72% | 9.52% | 67 | 47 | 47 | 103.04 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_3 | ATR_4_8 | 6 | continuous_2020_2023 | SUCCEEDED | -7.69% | 27.30% | 279 | 259 | 259 | 103.7 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 1 | development | BLOCKED | — | — | 2025 | 2006 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 13.70% | 18.53% | 554 | 536 | 536 | 11.22 | 18 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 1 | year_2021 | BLOCKED | — | — | 130 | 113 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -16.66% | 23.77% | 627 | 610 | 610 | 10.17 | 17 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | -7.49% | 21.67% | 601 | 582 | 582 | 10.86 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 1 | continuous_2020_2023 | BLOCKED | — | — | 681 | 663 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 3 | development | BLOCKED | — | — | 1651 | 1632 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 7.89% | 17.43% | 484 | 465 | 465 | 12.15 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 3 | year_2021 | BLOCKED | — | — | 109 | 90 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -14.63% | 21.17% | 529 | 512 | 512 | 12.04 | 17 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | -10.83% | 27.27% | 464 | 445 | 445 | 14.13 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 3 | continuous_2020_2023 | BLOCKED | — | — | 576 | 558 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 6 | development | BLOCKED | — | — | 1621 | 1602 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 7.54% | 17.43% | 483 | 464 | 464 | 12.06 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 6 | year_2021 | BLOCKED | — | — | 109 | 91 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -15.78% | 21.37% | 519 | 502 | 502 | 12.31 | 17 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | -7.50% | 24.03% | 451 | 432 | 432 | 14.36 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_8_16 | 6 | continuous_2020_2023 | BLOCKED | — | — | 565 | 547 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 1 | development | BLOCKED | — | — | 1629 | 1610 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 7.22% | 23.16% | 449 | 430 | 430 | 14.54 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | -4.70% | 19.72% | 448 | 429 | 429 | 15.42 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -21.31% | 25.03% | 484 | 466 | 466 | 13.88 | 18 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | -11.35% | 26.30% | 469 | 449 | 449 | 14.43 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 1 | continuous_2020_2023 | SUCCEEDED | -27.82% | 45.14% | 1835 | 1815 | 1815 | 14.57 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 3 | development | BLOCKED | — | — | 1143 | 1124 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 1.24% | 22.58% | 345 | 326 | 326 | 18.17 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | 1.59% | 22.16% | 321 | 302 | 302 | 21.27 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 3 | year_2022 | BLOCKED | — | — | 241 | 221 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | 3.81% | 20.57% | 348 | 328 | 328 | 18.77 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 3 | continuous_2020_2023 | BLOCKED | — | — | 401 | 382 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 6 | development | BLOCKED | — | — | 1075 | 1055 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 2.38% | 22.58% | 334 | 314 | 314 | 17.63 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | 5.78% | 21.10% | 307 | 288 | 288 | 21.96 | 19 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 6 | year_2022 | BLOCKED | — | — | 224 | 205 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 6 | year_2023 | SUCCEEDED | 1.62% | 22.49% | 336 | 316 | 316 | 19.06 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | PCT_10_20 | 6 | continuous_2020_2023 | BLOCKED | — | — | 841 | 822 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 1 | development | BLOCKED | — | — | 73 | 55 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 1 | year_2020 | BLOCKED | — | — | 89 | 70 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 4.67% | 10.98% | 275 | 255 | 255 | 27.09 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -19.13% | 20.98% | 284 | 264 | 264 | 25.7 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | -2.29% | 12.25% | 269 | 249 | 249 | 27.57 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 89 | 70 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 3 | development | BLOCKED | — | — | 222 | 204 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 3 | year_2020 | BLOCKED | — | — | 65 | 46 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 3 | year_2021 | BLOCKED | — | — | 49 | 29 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 3 | year_2022 | BLOCKED | — | — | 85 | 65 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 3 | year_2023 | BLOCKED | — | — | 90 | 70 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 65 | 46 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 6 | development | BLOCKED | — | — | 299 | 279 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 6 | year_2020 | BLOCKED | — | — | 65 | 46 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 6 | year_2021 | BLOCKED | — | — | 44 | 24 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 6 | year_2022 | BLOCKED | — | — | 64 | 44 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | 4.16% | 5.31% | 82 | 62 | 62 | 83.55 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_3_6 | 6 | continuous_2020_2023 | BLOCKED | — | — | 65 | 46 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 1 | development | BLOCKED | — | — | 67 | 49 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 1 | year_2020 | BLOCKED | — | — | 80 | 61 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 1 | year_2021 | SUCCEEDED | 6.81% | 10.39% | 264 | 244 | 244 | 28.41 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -11.48% | 14.25% | 266 | 246 | 246 | 27.59 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | -3.75% | 10.55% | 259 | 239 | 239 | 28.93 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 1 | continuous_2020_2023 | BLOCKED | — | — | 80 | 61 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 3 | development | BLOCKED | — | — | 180 | 160 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 3 | year_2020 | BLOCKED | — | — | 55 | 35 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 3 | year_2021 | SUCCEEDED | 1.58% | 9.90% | 110 | 90 | 90 | 71.08 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -10.69% | 13.70% | 112 | 92 | 92 | 69.01 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | 4.59% | 5.26% | 106 | 86 | 86 | 76.0 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 3 | continuous_2020_2023 | BLOCKED | — | — | 55 | 35 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 6 | development | BLOCKED | — | — | 34 | 14 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 6 | year_2020 | BLOCKED | — | — | 55 | 35 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | 10.21% | 8.98% | 81 | 61 | 61 | 93.82 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 6 | year_2022 | BLOCKED | — | — | 52 | 32 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | 2.85% | 4.79% | 60 | 40 | 40 | 118.75 | 20 | FULL_WINDOW |
| wide | TREND_PULLBACK_5 | ATR_4_8 | 6 | continuous_2020_2023 | BLOCKED | — | — | 55 | 35 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | RSI_REENTRY_30 | PCT_8_16 | 1 | development | SUCCEEDED | -0.66% | 0.76% | 6 | 6 | 6 | 4.33 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | -0.17% | 0.49% | 13 | 13 | 13 | 17.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 1 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -0.37% | 0.37% | 4 | 4 | 4 | 7.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | -0.24% | 0.31% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 1 | continuous_2020_2023 | SUCCEEDED | -0.78% | 0.89% | 18 | 18 | 18 | 14.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 3 | development | SUCCEEDED | -0.66% | 0.76% | 6 | 6 | 6 | 4.33 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | -0.46% | 0.71% | 13 | 13 | 13 | 34.23 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -0.37% | 0.37% | 4 | 4 | 4 | 7.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | -0.24% | 0.31% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | -1.06% | 1.18% | 18 | 18 | 18 | 26.44 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 6 | development | SUCCEEDED | -0.66% | 0.76% | 6 | 6 | 6 | 4.33 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | -0.61% | 0.74% | 13 | 13 | 13 | 41.85 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -0.37% | 0.37% | 4 | 4 | 4 | 7.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | -0.24% | 0.31% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | -1.21% | 1.33% | 18 | 18 | 18 | 31.94 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 1 | development | SUCCEEDED | -0.80% | 0.93% | 6 | 6 | 6 | 9.67 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | -0.35% | 0.62% | 14 | 14 | 14 | 18.64 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -0.49% | 0.49% | 4 | 4 | 4 | 10.25 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | -0.32% | 0.39% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 1 | continuous_2020_2023 | SUCCEEDED | -1.16% | 1.17% | 19 | 19 | 19 | 16.05 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 3 | development | SUCCEEDED | -0.78% | 0.91% | 6 | 6 | 6 | 15.17 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | -0.61% | 0.80% | 14 | 14 | 14 | 39.43 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -0.49% | 0.49% | 4 | 4 | 4 | 10.25 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | -0.32% | 0.39% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | -1.41% | 1.43% | 19 | 19 | 19 | 31.37 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 6 | development | SUCCEEDED | -0.78% | 0.91% | 6 | 6 | 6 | 15.17 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | -0.64% | 0.80% | 14 | 14 | 14 | 58.93 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -0.49% | 0.49% | 4 | 4 | 4 | 10.25 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 6 | year_2023 | SUCCEEDED | -0.32% | 0.39% | 1 | 1 | 1 | 3.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | PCT_10_20 | 6 | continuous_2020_2023 | SUCCEEDED | -1.44% | 1.46% | 19 | 19 | 19 | 45.74 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 1 | development | SUCCEEDED | -0.44% | 0.73% | 6 | 6 | 6 | 22.33 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 2.41% | 0.86% | 14 | 14 | 14 | 25.5 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -0.68% | 0.68% | 4 | 4 | 4 | 13.5 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | -0.47% | 0.53% | 1 | 1 | 1 | 8.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | 1.24% | 1.47% | 19 | 19 | 19 | 22.05 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 3 | development | SUCCEEDED | -0.64% | 0.92% | 6 | 6 | 6 | 49.83 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 2.08% | 1.79% | 14 | 14 | 14 | 59.57 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 3 | year_2022 | SUCCEEDED | -0.68% | 0.68% | 4 | 4 | 4 | 13.5 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | -0.47% | 0.53% | 1 | 1 | 1 | 8.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | 0.92% | 2.59% | 19 | 19 | 19 | 47.16 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 6 | development | SUCCEEDED | -0.55% | 0.97% | 6 | 5 | 5 | 59.6 | 1 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 1.87% | 2.13% | 14 | 14 | 14 | 98.64 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -0.68% | 0.68% | 4 | 4 | 4 | 13.5 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | -0.47% | 0.53% | 1 | 1 | 1 | 8.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | 0.70% | 2.80% | 19 | 19 | 19 | 75.95 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 1 | development | SUCCEEDED | -0.31% | 0.63% | 6 | 6 | 6 | 22.67 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 1.21% | 0.82% | 14 | 14 | 14 | 26.64 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 1 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -0.47% | 0.47% | 4 | 4 | 4 | 17.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | -0.08% | 0.51% | 1 | 1 | 1 | 31.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 1 | continuous_2020_2023 | SUCCEEDED | 0.66% | 1.45% | 19 | 19 | 19 | 24.84 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 3 | development | SUCCEEDED | -0.60% | 0.92% | 6 | 6 | 6 | 57.0 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 1.23% | 1.85% | 14 | 14 | 14 | 68.14 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 3 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -0.36% | 0.36% | 4 | 4 | 4 | 32.25 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | -0.04% | 0.62% | 1 | 0 | 0 | — | 1 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 3 | continuous_2020_2023 | SUCCEEDED | 0.83% | 1.85% | 19 | 18 | 18 | 60.17 | 1 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 6 | development | SUCCEEDED | -0.52% | 0.94% | 6 | 5 | 5 | 77.0 | 1 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 0.54% | 2.09% | 14 | 14 | 14 | 126.79 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | 0.00% | -0.00% | 0 | 0 | 0 | — | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -0.34% | 1.24% | 4 | 4 | 4 | 55.25 | 0 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | -0.04% | 0.62% | 1 | 0 | 0 | — | 1 | FULL_WINDOW |
| wide | RSI_REENTRY_30 | ATR_4_8 | 6 | continuous_2020_2023 | SUCCEEDED | 0.15% | 2.43% | 19 | 18 | 18 | 110.89 | 1 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 1 | development | SUCCEEDED | -14.11% | 17.42% | 730 | 726 | 726 | 16.69 | 4 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 3.11% | 8.90% | 180 | 165 | 165 | 12.86 | 15 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 1 | year_2021 | SUCCEEDED | -3.03% | 8.45% | 208 | 200 | 200 | 17.25 | 8 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -12.92% | 13.65% | 173 | 160 | 160 | 12.55 | 13 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | 0.94% | 5.11% | 178 | 170 | 170 | 16.29 | 8 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 1 | continuous_2020_2023 | SUCCEEDED | -10.59% | 19.55% | 730 | 722 | 722 | 15.25 | 8 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 3 | development | SUCCEEDED | -10.08% | 17.30% | 685 | 669 | 669 | 25.53 | 16 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 5.76% | 9.01% | 180 | 164 | 164 | 16.58 | 16 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | 4.45% | 7.96% | 176 | 164 | 164 | 26.35 | 12 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -13.62% | 14.07% | 167 | 154 | 154 | 15.36 | 13 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | 0.94% | 6.20% | 164 | 151 | 151 | 23.38 | 13 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | -4.73% | 21.24% | 680 | 667 | 667 | 21.34 | 13 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 6 | development | SUCCEEDED | -10.84% | 19.39% | 663 | 646 | 646 | 28.01 | 17 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 6.46% | 9.01% | 180 | 163 | 163 | 16.37 | 17 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | 5.94% | 7.44% | 174 | 162 | 162 | 27.38 | 12 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -13.25% | 13.69% | 161 | 148 | 148 | 16.52 | 13 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | 0.35% | 6.51% | 164 | 149 | 149 | 24.0 | 15 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | -3.67% | 20.49% | 669 | 654 | 654 | 22.54 | 15 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 1 | development | SUCCEEDED | -17.47% | 21.34% | 703 | 698 | 698 | 19.88 | 5 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 6.32% | 11.67% | 169 | 153 | 153 | 16.87 | 16 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | -3.08% | 8.13% | 199 | 190 | 190 | 20.75 | 9 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -16.09% | 16.34% | 163 | 143 | 143 | 15.57 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | 0.42% | 5.79% | 166 | 155 | 155 | 20.25 | 11 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 1 | continuous_2020_2023 | SUCCEEDED | -11.97% | 22.41% | 687 | 676 | 676 | 18.73 | 11 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 3 | development | SUCCEEDED | -15.76% | 21.52% | 612 | 594 | 594 | 34.78 | 18 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 6.92% | 11.15% | 152 | 132 | 132 | 26.14 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | 7.08% | 7.83% | 146 | 133 | 133 | 37.26 | 13 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -14.64% | 14.89% | 152 | 132 | 132 | 21.97 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | -2.26% | 7.81% | 144 | 128 | 128 | 32.62 | 16 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | -6.19% | 24.53% | 584 | 568 | 568 | 30.36 | 16 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 6 | development | SUCCEEDED | -24.00% | 28.01% | 573 | 555 | 555 | 39.75 | 18 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 8.34% | 11.15% | 148 | 128 | 128 | 25.25 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | 8.55% | 8.23% | 135 | 121 | 121 | 42.73 | 14 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -14.63% | 14.89% | 145 | 125 | 125 | 23.09 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 6 | year_2023 | SUCCEEDED | -4.74% | 10.08% | 143 | 124 | 124 | 36.07 | 19 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | PCT_10_20 | 6 | continuous_2020_2023 | SUCCEEDED | -8.15% | 27.11% | 558 | 538 | 538 | 33.61 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 1 | development | SUCCEEDED | -9.76% | 16.49% | 673 | 669 | 669 | 24.74 | 4 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 3.87% | 10.92% | 156 | 140 | 140 | 22.34 | 16 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 0.21% | 8.23% | 184 | 175 | 175 | 24.34 | 9 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -13.42% | 13.73% | 149 | 132 | 132 | 22.73 | 17 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | -1.73% | 6.07% | 160 | 149 | 149 | 23.79 | 11 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -9.92% | 20.97% | 641 | 630 | 630 | 23.35 | 11 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 3 | development | SUCCEEDED | -19.13% | 22.06% | 517 | 501 | 501 | 50.57 | 16 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 11.38% | 11.03% | 124 | 104 | 104 | 38.89 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | 8.26% | 7.67% | 134 | 117 | 117 | 45.44 | 17 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 3 | year_2022 | SUCCEEDED | -4.82% | 9.39% | 123 | 106 | 106 | 43.59 | 17 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | -4.05% | 10.51% | 128 | 108 | 108 | 43.96 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | 1.62% | 19.94% | 500 | 480 | 480 | 44.57 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 6 | development | SUCCEEDED | -17.73% | 23.60% | 440 | 424 | 424 | 63.63 | 16 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 9.88% | 11.03% | 110 | 90 | 90 | 35.81 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 5.35% | 9.80% | 109 | 91 | 91 | 60.87 | 18 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -4.66% | 9.26% | 114 | 94 | 94 | 47.24 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | -3.30% | 9.48% | 120 | 100 | 100 | 50.03 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | 5.80% | 16.56% | 432 | 412 | 412 | 54.28 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 1 | development | BLOCKED | — | — | 66 | 47 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | RSI_REENTRY_40 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 2.91% | 8.36% | 142 | 124 | 124 | 25.12 | 18 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 1 | year_2021 | SUCCEEDED | -2.82% | 7.79% | 170 | 161 | 161 | 27.47 | 9 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -9.52% | 10.61% | 141 | 122 | 122 | 25.93 | 19 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | -0.79% | 5.50% | 156 | 145 | 145 | 26.89 | 11 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 1 | continuous_2020_2023 | SUCCEEDED | -6.54% | 16.83% | 597 | 586 | 586 | 26.4 | 11 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 3 | development | BLOCKED | — | — | 102 | 84 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | RSI_REENTRY_40 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 6.21% | 10.04% | 104 | 84 | 84 | 52.46 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 3 | year_2021 | SUCCEEDED | 0.71% | 11.21% | 119 | 99 | 99 | 56.47 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -4.06% | 9.03% | 101 | 87 | 87 | 62.34 | 14 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | 1.96% | 8.20% | 99 | 79 | 79 | 65.61 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 3 | continuous_2020_2023 | SUCCEEDED | 4.38% | 17.96% | 403 | 383 | 383 | 59.92 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 6 | development | BLOCKED | — | — | 37 | 17 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | RSI_REENTRY_40 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 4.83% | 10.49% | 86 | 66 | 66 | 52.79 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | 1.68% | 10.22% | 91 | 71 | 71 | 75.48 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -5.10% | 9.60% | 75 | 55 | 55 | 88.8 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | 4.48% | 8.88% | 81 | 61 | 61 | 81.16 | 20 | FULL_WINDOW |
| wide | RSI_REENTRY_40 | ATR_4_8 | 6 | continuous_2020_2023 | SUCCEEDED | 11.13% | 12.26% | 309 | 289 | 289 | 80.71 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 1 | development | SUCCEEDED | -17.35% | 26.22% | 1508 | 1488 | 1488 | 16.6 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 2.27% | 13.81% | 351 | 331 | 331 | 13.05 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 1 | year_2021 | BLOCKED | — | — | 82 | 65 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -18.81% | 19.08% | 318 | 301 | 301 | 13.61 | 17 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | 0.96% | 9.29% | 346 | 326 | 326 | 16.74 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 1 | continuous_2020_2023 | BLOCKED | — | — | 457 | 437 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 3 | development | SUCCEEDED | -14.43% | 25.93% | 1119 | 1099 | 1099 | 25.22 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 3.52% | 15.10% | 306 | 288 | 288 | 15.45 | 18 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | -3.57% | 21.26% | 273 | 253 | 253 | 23.04 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -19.73% | 20.00% | 287 | 273 | 273 | 16.62 | 14 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | 1.66% | 8.34% | 271 | 251 | 251 | 23.37 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | -14.79% | 33.21% | 1115 | 1095 | 1095 | 20.14 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 6 | development | SUCCEEDED | -16.10% | 27.22% | 1018 | 998 | 998 | 27.94 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 3.47% | 15.10% | 304 | 285 | 285 | 14.96 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | 2.11% | 19.51% | 262 | 242 | 242 | 24.01 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -19.88% | 20.15% | 275 | 260 | 260 | 17.54 | 15 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | 1.17% | 8.91% | 257 | 237 | 237 | 23.14 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | -14.83% | 32.26% | 1063 | 1043 | 1043 | 21.04 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 1 | development | SUCCEEDED | -16.98% | 26.85% | 1307 | 1287 | 1287 | 20.52 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 6.44% | 13.83% | 302 | 282 | 282 | 16.32 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 1 | year_2021 | BLOCKED | — | — | 69 | 52 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -18.15% | 18.51% | 287 | 269 | 269 | 16.87 | 18 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | 0.93% | 11.41% | 301 | 281 | 281 | 20.52 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 1 | continuous_2020_2023 | BLOCKED | — | — | 363 | 345 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 3 | development | SUCCEEDED | -10.31% | 25.16% | 871 | 851 | 851 | 34.34 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 7.56% | 15.64% | 228 | 208 | 208 | 23.05 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 3 | year_2021 | BLOCKED | — | — | 48 | 30 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -19.26% | 20.01% | 243 | 224 | 224 | 23.5 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | 0.04% | 13.10% | 194 | 174 | 174 | 34.35 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 3 | continuous_2020_2023 | BLOCKED | — | — | 260 | 241 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 6 | development | SUCCEEDED | -23.24% | 31.91% | 727 | 707 | 707 | 41.29 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 7.22% | 15.64% | 220 | 200 | 200 | 23.32 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 6 | year_2021 | BLOCKED | — | — | 48 | 30 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -19.10% | 19.85% | 228 | 210 | 210 | 24.46 | 18 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 6 | year_2023 | SUCCEEDED | 0.69% | 10.94% | 174 | 154 | 154 | 34.65 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | PCT_10_20 | 6 | continuous_2020_2023 | BLOCKED | — | — | 244 | 226 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 1 | development | BLOCKED | — | — | 344 | 324 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 6.44% | 11.93% | 251 | 231 | 231 | 21.7 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 1 | year_2021 | BLOCKED | — | — | 65 | 47 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -16.40% | 16.74% | 250 | 231 | 231 | 23.14 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | -0.34% | 10.61% | 266 | 246 | 246 | 25.5 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 302 | 284 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 3 | development | BLOCKED | — | — | 501 | 481 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | -0.59% | 14.26% | 147 | 127 | 127 | 38.76 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 3 | year_2021 | BLOCKED | — | — | 48 | 29 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 3 | year_2022 | SUCCEEDED | -17.45% | 18.83% | 156 | 136 | 136 | 43.14 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | -3.56% | 14.41% | 139 | 119 | 119 | 50.37 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 176 | 157 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 6 | development | BLOCKED | — | — | 381 | 361 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | -1.26% | 14.26% | 132 | 112 | 112 | 41.32 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 6 | year_2021 | BLOCKED | — | — | 48 | 29 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -20.89% | 22.10% | 127 | 108 | 108 | 51.73 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | 2.72% | 10.90% | 107 | 87 | 87 | 60.66 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_3_6 | 6 | continuous_2020_2023 | BLOCKED | — | — | 160 | 142 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 1 | development | BLOCKED | — | — | 237 | 218 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 2.75% | 11.42% | 223 | 203 | 203 | 24.71 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 1 | year_2021 | BLOCKED | — | — | 56 | 43 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -14.94% | 15.22% | 227 | 208 | 208 | 26.13 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | 2.50% | 7.90% | 245 | 225 | 225 | 27.77 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 1 | continuous_2020_2023 | BLOCKED | — | — | 270 | 251 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 3 | development | BLOCKED | — | — | 113 | 94 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 3.87% | 11.45% | 120 | 100 | 100 | 50.45 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 3 | year_2021 | BLOCKED | — | — | 51 | 31 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -15.14% | 17.34% | 122 | 104 | 104 | 61.2 | 18 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | -2.90% | 12.20% | 112 | 92 | 92 | 64.95 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 3 | continuous_2020_2023 | BLOCKED | — | — | 154 | 134 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 6 | development | BLOCKED | — | — | 268 | 248 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 1.37% | 12.09% | 106 | 86 | 86 | 55.45 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 6 | year_2021 | BLOCKED | — | — | 44 | 24 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -14.91% | 19.15% | 86 | 66 | 66 | 81.55 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | 2.65% | 8.07% | 86 | 66 | 66 | 77.61 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_1_5 | ATR_4_8 | 6 | continuous_2020_2023 | BLOCKED | — | — | 128 | 108 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 1 | development | SUCCEEDED | -4.39% | 17.35% | 920 | 911 | 911 | 17.6 | 9 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 7.46% | 11.65% | 228 | 209 | 209 | 13.4 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 1 | year_2021 | SUCCEEDED | 1.13% | 9.48% | 218 | 215 | 215 | 17.46 | 3 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -12.83% | 13.49% | 196 | 180 | 180 | 14.76 | 16 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | 2.87% | 5.98% | 210 | 190 | 190 | 17.48 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 1 | continuous_2020_2023 | SUCCEEDED | -1.49% | 20.35% | 842 | 822 | 822 | 16.15 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 3 | development | SUCCEEDED | -8.67% | 19.60% | 805 | 785 | 785 | 25.97 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 9.36% | 11.83% | 213 | 194 | 194 | 16.95 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | 10.26% | 6.82% | 175 | 171 | 171 | 28.04 | 4 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -13.71% | 14.37% | 181 | 164 | 164 | 17.71 | 17 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | -0.41% | 7.27% | 184 | 164 | 164 | 26.46 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | 6.40% | 19.19% | 741 | 721 | 721 | 23.08 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 6 | development | SUCCEEDED | -3.52% | 18.76% | 770 | 750 | 750 | 27.95 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 9.85% | 11.83% | 210 | 191 | 191 | 16.74 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | 9.35% | 8.42% | 169 | 164 | 164 | 30.38 | 5 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -13.10% | 13.74% | 177 | 160 | 160 | 18.04 | 17 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | -2.13% | 8.52% | 179 | 159 | 159 | 26.88 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | 5.77% | 20.86% | 720 | 700 | 700 | 24.35 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 1 | development | SUCCEEDED | -11.13% | 20.38% | 869 | 859 | 859 | 20.87 | 10 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 3.11% | 14.97% | 198 | 178 | 178 | 17.7 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | -1.91% | 9.76% | 197 | 194 | 194 | 21.02 | 3 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -14.96% | 15.90% | 177 | 158 | 158 | 18.46 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | 6.68% | 5.58% | 196 | 176 | 176 | 21.53 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 1 | continuous_2020_2023 | SUCCEEDED | -8.60% | 22.68% | 753 | 733 | 733 | 20.04 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 3 | development | BLOCKED | — | — | 576 | 560 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 4.15% | 15.53% | 164 | 144 | 144 | 27.91 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | 6.09% | 7.78% | 147 | 142 | 142 | 36.34 | 5 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -14.59% | 15.59% | 155 | 136 | 136 | 24.79 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | -0.09% | 9.82% | 156 | 136 | 136 | 36.33 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | -5.38% | 24.28% | 605 | 585 | 585 | 32.55 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 6 | development | BLOCKED | — | — | 529 | 511 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 6.47% | 15.53% | 161 | 141 | 141 | 27.38 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | 5.76% | 10.26% | 135 | 129 | 129 | 40.22 | 6 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -13.35% | 15.95% | 151 | 132 | 132 | 25.64 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 6 | year_2023 | SUCCEEDED | -0.77% | 9.10% | 144 | 124 | 124 | 39.81 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | PCT_10_20 | 6 | continuous_2020_2023 | SUCCEEDED | -1.63% | 21.65% | 560 | 540 | 540 | 36.18 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 1 | development | BLOCKED | — | — | 245 | 231 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 4.75% | 11.63% | 173 | 154 | 154 | 23.34 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 0.50% | 6.81% | 191 | 186 | 186 | 24.53 | 5 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -13.76% | 14.43% | 165 | 147 | 147 | 24.26 | 18 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | 6.86% | 7.48% | 190 | 171 | 171 | 25.23 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -2.87% | 19.10% | 705 | 686 | 686 | 24.67 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 3 | development | BLOCKED | — | — | 167 | 147 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 2.61% | 12.36% | 127 | 107 | 107 | 42.79 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | 6.10% | 7.46% | 127 | 114 | 114 | 47.84 | 13 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 3 | year_2022 | SUCCEEDED | -4.02% | 8.20% | 133 | 115 | 115 | 44.1 | 18 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | -9.04% | 14.11% | 128 | 108 | 108 | 51.48 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -6.62% | 18.34% | 497 | 477 | 477 | 47.66 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 6 | development | BLOCKED | — | — | 129 | 109 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 1.44% | 12.36% | 115 | 95 | 95 | 49.02 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 11.35% | 7.42% | 115 | 97 | 97 | 53.54 | 18 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -4.94% | 10.85% | 107 | 88 | 88 | 54.07 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | -9.06% | 14.24% | 110 | 90 | 90 | 57.89 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -5.79% | 18.95% | 403 | 383 | 383 | 60.19 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 1 | development | BLOCKED | — | — | 228 | 214 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 0.37% | 12.75% | 160 | 140 | 140 | 25.86 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 1 | year_2021 | SUCCEEDED | -0.16% | 6.23% | 176 | 171 | 171 | 27.52 | 5 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -13.27% | 14.29% | 157 | 138 | 138 | 26.95 | 19 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | 5.32% | 6.55% | 182 | 162 | 162 | 27.89 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 1 | continuous_2020_2023 | SUCCEEDED | -9.30% | 18.88% | 661 | 641 | 641 | 27.34 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 3 | development | BLOCKED | — | — | 107 | 87 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | -0.41% | 12.12% | 100 | 80 | 80 | 61.4 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 3 | year_2021 | SUCCEEDED | 7.22% | 6.39% | 112 | 96 | 96 | 60.44 | 16 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -5.74% | 11.89% | 113 | 93 | 93 | 57.66 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | -3.65% | 8.97% | 105 | 85 | 85 | 65.25 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 3 | continuous_2020_2023 | SUCCEEDED | -1.97% | 14.59% | 409 | 389 | 389 | 61.06 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 6 | development | BLOCKED | — | — | 70 | 50 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | -0.70% | 12.12% | 84 | 64 | 64 | 71.92 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | 3.11% | 7.88% | 90 | 70 | 70 | 78.83 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -6.30% | 12.99% | 80 | 60 | 60 | 81.98 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | -5.47% | 11.79% | 82 | 62 | 62 | 83.94 | 20 | FULL_WINDOW |
| wide | BOLLINGER_REENTRY_2 | ATR_4_8 | 6 | continuous_2020_2023 | SUCCEEDED | -11.59% | 20.36% | 287 | 267 | 267 | 90.23 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 1 | development | BLOCKED | — | — | 1341 | 1322 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 18.65% | 7.00% | 455 | 436 | 436 | 12.07 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 1 | year_2021 | BLOCKED | — | — | 126 | 107 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -20.68% | 20.86% | 468 | 453 | 453 | 12.9 | 15 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | -5.04% | 11.43% | 433 | 413 | 413 | 14.59 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 1 | continuous_2020_2023 | BLOCKED | — | — | 564 | 545 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 3 | development | BLOCKED | — | — | 705 | 685 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 20.70% | 6.97% | 383 | 365 | 365 | 13.81 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | 7.77% | 11.53% | 352 | 334 | 334 | 18.69 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -18.86% | 20.12% | 360 | 342 | 342 | 16.64 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | 0.37% | 8.83% | 306 | 286 | 286 | 20.42 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | 10.19% | 26.88% | 1358 | 1338 | 1338 | 18.33 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 6 | development | SUCCEEDED | -21.68% | 31.75% | 1295 | 1275 | 1275 | 23.01 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 21.08% | 6.97% | 377 | 359 | 359 | 13.9 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | 7.07% | 12.52% | 350 | 332 | 332 | 18.2 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -18.39% | 19.63% | 342 | 324 | 324 | 17.52 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | -0.68% | 10.70% | 296 | 276 | 276 | 20.12 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | 10.91% | 26.53% | 1277 | 1257 | 1257 | 19.36 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 1 | development | BLOCKED | — | — | 193 | 173 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 16.11% | 12.00% | 392 | 372 | 372 | 14.93 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 1 | year_2021 | BLOCKED | — | — | 99 | 79 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -20.59% | 22.23% | 393 | 376 | 376 | 16.13 | 17 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | -3.70% | 9.68% | 373 | 353 | 353 | 17.88 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 1 | continuous_2020_2023 | BLOCKED | — | — | 478 | 458 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 3 | development | SUCCEEDED | -30.69% | 39.10% | 1009 | 989 | 989 | 30.77 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 22.09% | 12.88% | 293 | 273 | 273 | 19.23 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 3 | year_2021 | BLOCKED | — | — | 64 | 44 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -19.71% | 21.89% | 284 | 267 | 267 | 21.61 | 17 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | -2.01% | 11.36% | 224 | 204 | 204 | 29.29 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | -3.03% | 35.77% | 1006 | 986 | 986 | 25.81 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 6 | development | SUCCEEDED | -26.36% | 35.11% | 883 | 863 | 863 | 35.0 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 17.58% | 12.88% | 278 | 258 | 258 | 18.88 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | -0.68% | 19.35% | 231 | 214 | 214 | 28.94 | 17 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -20.75% | 20.96% | 267 | 250 | 250 | 23.86 | 17 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 6 | year_2023 | BLOCKED | — | — | 174 | 156 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | PCT_10_20 | 6 | continuous_2020_2023 | BLOCKED | — | — | 860 | 842 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 1 | development | BLOCKED | — | — | 153 | 134 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 10.08% | 14.64% | 313 | 294 | 294 | 20.77 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 1 | year_2021 | BLOCKED | — | — | 87 | 67 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -12.72% | 15.09% | 297 | 280 | 280 | 23.21 | 17 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | 3.08% | 8.49% | 318 | 298 | 298 | 21.79 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 385 | 365 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 3 | development | BLOCKED | — | — | 480 | 461 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 12.60% | 14.30% | 190 | 170 | 170 | 34.1 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 3 | year_2021 | BLOCKED | — | — | 51 | 31 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 3 | year_2022 | SUCCEEDED | -6.41% | 9.88% | 173 | 156 | 156 | 39.2 | 17 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | 4.75% | 6.42% | 169 | 149 | 149 | 40.7 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | 0.35% | 21.70% | 668 | 648 | 648 | 41.06 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 6 | development | SUCCEEDED | -31.29% | 37.65% | 599 | 579 | 579 | 52.79 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 13.50% | 14.30% | 177 | 157 | 157 | 35.42 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 5.90% | 13.96% | 157 | 137 | 137 | 43.97 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -7.36% | 10.23% | 149 | 131 | 131 | 45.71 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | 11.63% | 4.93% | 144 | 124 | 124 | 44.44 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | 16.88% | 18.70% | 578 | 558 | 558 | 47.09 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 1 | development | SUCCEEDED | -31.04% | 36.17% | 1219 | 1199 | 1199 | 26.19 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 1.69% | 10.92% | 266 | 246 | 246 | 24.98 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 1 | year_2021 | BLOCKED | — | — | 66 | 46 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -9.80% | 12.87% | 270 | 250 | 250 | 26.19 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | -1.83% | 9.99% | 267 | 247 | 247 | 26.57 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 1 | continuous_2020_2023 | BLOCKED | — | — | 329 | 309 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 3 | development | BLOCKED | — | — | 353 | 333 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 13.84% | 9.51% | 134 | 115 | 115 | 50.56 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 3 | year_2021 | BLOCKED | — | — | 43 | 23 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -5.30% | 8.33% | 138 | 119 | 119 | 50.08 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | 8.39% | 3.58% | 122 | 102 | 102 | 60.2 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 3 | continuous_2020_2023 | BLOCKED | — | — | 161 | 141 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 6 | development | SUCCEEDED | -21.98% | 28.79% | 393 | 373 | 373 | 82.13 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 10.12% | 9.51% | 104 | 84 | 84 | 60.7 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | 4.78% | 9.75% | 95 | 75 | 75 | 77.29 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -9.07% | 9.94% | 103 | 84 | 84 | 65.93 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | 6.37% | 4.40% | 96 | 76 | 76 | 71.57 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA60 | ATR_4_8 | 6 | continuous_2020_2023 | BLOCKED | — | — | 122 | 102 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 1 | development | SUCCEEDED | -35.82% | 41.48% | 1944 | 1925 | 1925 | 14.93 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 16.86% | 9.37% | 464 | 445 | 445 | 11.93 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 1 | year_2021 | BLOCKED | — | — | 128 | 109 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -23.46% | 23.62% | 471 | 455 | 455 | 12.56 | 16 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | -12.02% | 18.71% | 444 | 424 | 424 | 14.33 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 1 | continuous_2020_2023 | BLOCKED | — | — | 576 | 557 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 3 | development | BLOCKED | — | — | 745 | 725 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 15.93% | 9.58% | 381 | 363 | 363 | 13.87 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | 3.02% | 15.33% | 348 | 331 | 331 | 19.0 | 17 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -21.16% | 21.94% | 384 | 366 | 366 | 15.51 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | -4.96% | 15.17% | 327 | 309 | 309 | 19.12 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | -13.62% | 38.75% | 1386 | 1368 | 1368 | 17.96 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 6 | development | BLOCKED | — | — | 702 | 682 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 17.49% | 9.58% | 391 | 373 | 373 | 13.66 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | 2.32% | 14.37% | 333 | 316 | 316 | 19.16 | 17 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -22.75% | 22.92% | 377 | 361 | 361 | 16.06 | 16 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | -1.33% | 11.93% | 302 | 283 | 283 | 19.66 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | -9.51% | 37.69% | 1350 | 1331 | 1331 | 18.24 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 1 | development | BLOCKED | — | — | 196 | 176 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 19.95% | 12.30% | 399 | 379 | 379 | 14.88 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 1 | year_2021 | BLOCKED | — | — | 98 | 79 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -28.93% | 29.09% | 398 | 380 | 380 | 15.84 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | -12.54% | 18.33% | 375 | 356 | 356 | 17.71 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 1 | continuous_2020_2023 | BLOCKED | — | — | 488 | 469 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 3 | development | BLOCKED | — | — | 147 | 128 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 20.09% | 12.13% | 294 | 274 | 274 | 19.48 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 3 | year_2021 | BLOCKED | — | — | 63 | 44 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -25.05% | 25.77% | 295 | 277 | 277 | 20.56 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | 4.82% | 9.31% | 222 | 202 | 202 | 29.98 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | -3.26% | 36.52% | 1027 | 1007 | 1007 | 25.29 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 6 | development | BLOCKED | — | — | 139 | 119 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 21.01% | 12.13% | 274 | 254 | 254 | 18.93 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | -1.56% | 20.70% | 243 | 225 | 225 | 27.75 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -25.09% | 25.26% | 286 | 268 | 268 | 21.7 | 18 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 6 | year_2023 | BLOCKED | — | — | 173 | 155 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | PCT_10_20 | 6 | continuous_2020_2023 | BLOCKED | — | — | 918 | 899 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 1 | development | BLOCKED | — | — | 156 | 137 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 4.63% | 15.25% | 315 | 296 | 296 | 21.28 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 1 | year_2021 | BLOCKED | — | — | 88 | 69 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -15.83% | 19.26% | 304 | 285 | 285 | 22.25 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | -2.13% | 10.18% | 313 | 293 | 293 | 21.94 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 391 | 372 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 3 | development | BLOCKED | — | — | 473 | 455 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 14.82% | 15.41% | 187 | 167 | 167 | 36.47 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 3 | year_2021 | BLOCKED | — | — | 56 | 37 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 3 | year_2022 | SUCCEEDED | -14.29% | 16.35% | 180 | 163 | 163 | 36.89 | 17 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | 6.43% | 6.72% | 168 | 148 | 148 | 40.5 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | 1.31% | 24.88% | 666 | 646 | 646 | 41.37 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 6 | development | SUCCEEDED | -29.57% | 33.12% | 581 | 561 | 561 | 55.0 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 4.76% | 15.41% | 153 | 133 | 133 | 41.68 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 6.00% | 15.59% | 152 | 132 | 132 | 45.47 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -13.59% | 17.44% | 148 | 131 | 131 | 44.31 | 17 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | -1.46% | 10.37% | 140 | 120 | 120 | 45.47 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -0.75% | 24.93% | 537 | 517 | 517 | 50.7 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 1 | development | BLOCKED | — | — | 686 | 666 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 2.66% | 11.98% | 277 | 257 | 257 | 24.62 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 1 | year_2021 | BLOCKED | — | — | 66 | 46 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -15.18% | 18.93% | 270 | 250 | 250 | 25.99 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | -2.48% | 9.67% | 266 | 246 | 246 | 26.56 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 1 | continuous_2020_2023 | BLOCKED | — | — | 339 | 319 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 3 | development | BLOCKED | — | — | 75 | 55 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 18.20% | 9.98% | 144 | 124 | 124 | 49.58 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 3 | year_2021 | BLOCKED | — | — | 43 | 23 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -13.57% | 16.94% | 144 | 125 | 125 | 46.08 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | 3.24% | 7.83% | 123 | 103 | 103 | 59.52 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 3 | continuous_2020_2023 | BLOCKED | — | — | 174 | 154 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 6 | development | BLOCKED | — | — | 236 | 216 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 15.47% | 9.98% | 117 | 97 | 97 | 58.98 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | 5.39% | 10.95% | 98 | 78 | 78 | 75.94 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -14.84% | 16.01% | 106 | 87 | 87 | 63.84 | 19 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | -0.66% | 8.77% | 98 | 78 | 78 | 73.05 | 20 | FULL_WINDOW |
| wide | MACD_CROSS_SMA120 | ATR_4_8 | 6 | continuous_2020_2023 | BLOCKED | — | — | 135 | 115 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 1 | development | BLOCKED | — | — | 908 | 890 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | -1.00% | 11.41% | 703 | 685 | 685 | 8.49 | 18 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 1 | year_2021 | SUCCEEDED | -12.20% | 19.02% | 548 | 530 | 530 | 11.9 | 18 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -30.29% | 30.71% | 597 | 582 | 582 | 10.25 | 15 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 1 | year_2023 | BLOCKED | — | — | 434 | 420 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 1 | continuous_2020_2023 | BLOCKED | — | — | 2251 | 2237 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 3 | development | SUCCEEDED | -38.22% | 42.78% | 1605 | 1585 | 1585 | 18.94 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 4.94% | 11.61% | 614 | 596 | 596 | 9.47 | 18 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | -12.78% | 18.69% | 400 | 383 | 383 | 16.31 | 17 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -29.14% | 30.71% | 453 | 438 | 438 | 13.11 | 15 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | -7.63% | 17.26% | 382 | 362 | 362 | 16.32 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | -40.88% | 48.57% | 1801 | 1781 | 1781 | 14.1 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 6 | development | BLOCKED | — | — | 1199 | 1179 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 3.71% | 11.61% | 599 | 580 | 580 | 9.42 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | -10.61% | 17.73% | 383 | 366 | 366 | 17.13 | 17 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -31.23% | 31.64% | 445 | 431 | 431 | 13.55 | 14 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | -4.60% | 17.02% | 367 | 347 | 347 | 15.38 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | -38.40% | 46.79% | 1703 | 1683 | 1683 | 14.64 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 1 | development | BLOCKED | — | — | 211 | 191 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 13.38% | 14.63% | 539 | 519 | 519 | 11.79 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | -6.68% | 21.29% | 448 | 428 | 428 | 15.18 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -31.88% | 32.19% | 479 | 463 | 463 | 13.63 | 16 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | 2.84% | 13.50% | 421 | 401 | 401 | 16.38 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 1 | continuous_2020_2023 | BLOCKED | — | — | 1778 | 1761 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 3 | development | BLOCKED | — | — | 150 | 132 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 6.16% | 13.81% | 415 | 395 | 395 | 14.56 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | -14.09% | 23.63% | 296 | 276 | 276 | 23.05 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -29.87% | 30.87% | 347 | 327 | 327 | 18.15 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | -2.78% | 13.46% | 265 | 245 | 245 | 25.02 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | -42.01% | 52.19% | 1250 | 1230 | 1230 | 21.25 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 6 | development | BLOCKED | — | — | 140 | 120 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 5.11% | 13.81% | 399 | 379 | 379 | 14.73 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | -10.96% | 22.61% | 268 | 248 | 248 | 25.17 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -28.98% | 30.39% | 329 | 309 | 309 | 18.65 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 6 | year_2023 | SUCCEEDED | -1.67% | 12.69% | 252 | 232 | 232 | 24.16 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | PCT_10_20 | 6 | continuous_2020_2023 | SUCCEEDED | -33.83% | 47.29% | 1147 | 1128 | 1128 | 22.84 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 1 | development | BLOCKED | — | — | 158 | 138 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 1.51% | 16.15% | 339 | 319 | 319 | 20.63 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 5.64% | 12.54% | 339 | 319 | 319 | 21.41 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 1 | year_2022 | BLOCKED | — | — | 141 | 121 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | 0.17% | 15.45% | 329 | 309 | 309 | 21.98 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -22.07% | 40.85% | 1310 | 1290 | 1290 | 21.48 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 3 | development | BLOCKED | — | — | 97 | 78 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 6.23% | 15.98% | 188 | 168 | 168 | 36.18 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | -1.42% | 12.46% | 204 | 184 | 184 | 33.87 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 3 | year_2022 | BLOCKED | — | — | 96 | 76 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | -5.38% | 14.88% | 178 | 158 | 158 | 39.29 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 453 | 434 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 6 | development | BLOCKED | — | — | 87 | 67 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 3.23% | 16.18% | 162 | 142 | 142 | 39.73 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 1.33% | 12.04% | 173 | 153 | 153 | 39.69 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -18.40% | 21.47% | 177 | 159 | 159 | 36.74 | 18 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | -2.87% | 12.14% | 151 | 133 | 133 | 44.68 | 18 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -13.33% | 32.69% | 598 | 580 | 580 | 46.58 | 18 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 1 | development | BLOCKED | — | — | 114 | 94 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 6.21% | 14.95% | 300 | 280 | 280 | 23.88 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 1 | year_2021 | BLOCKED | — | — | 82 | 62 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -21.73% | 22.42% | 285 | 266 | 266 | 25.82 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 1 | year_2023 | BLOCKED | — | — | 271 | 251 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 1 | continuous_2020_2023 | SUCCEEDED | -14.43% | 32.12% | 1135 | 1115 | 1115 | 25.15 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 3 | development | BLOCKED | — | — | 72 | 52 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 11.00% | 11.59% | 147 | 128 | 128 | 49.41 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 3 | year_2021 | SUCCEEDED | -2.96% | 15.06% | 149 | 130 | 130 | 48.49 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -17.58% | 20.37% | 151 | 132 | 132 | 48.66 | 19 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | -6.22% | 10.39% | 123 | 103 | 103 | 58.75 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 3 | continuous_2020_2023 | BLOCKED | — | — | 513 | 494 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 6 | development | BLOCKED | — | — | 66 | 46 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 7.60% | 11.59% | 119 | 99 | 99 | 55.58 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | -2.95% | 14.13% | 109 | 89 | 89 | 68.19 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -14.91% | 17.24% | 114 | 94 | 94 | 59.03 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | -2.40% | 8.73% | 102 | 82 | 82 | 70.68 | 20 | FULL_WINDOW |
| wide | BREAKOUT_20_RVOL_1_5 | ATR_4_8 | 6 | continuous_2020_2023 | SUCCEEDED | -4.47% | 27.92% | 409 | 389 | 389 | 70.2 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 1 | development | SUCCEEDED | -52.31% | 57.41% | 2375 | 2356 | 2356 | 11.94 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | -2.04% | 13.26% | 731 | 713 | 713 | 7.5 | 18 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 1 | year_2021 | SUCCEEDED | -5.25% | 23.57% | 596 | 578 | 578 | 10.51 | 18 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -37.94% | 38.65% | 596 | 580 | 580 | 9.03 | 16 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | -12.59% | 18.68% | 604 | 584 | 584 | 10.51 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 1 | continuous_2020_2023 | SUCCEEDED | -47.33% | 55.10% | 2480 | 2460 | 2460 | 9.63 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 3 | development | SUCCEEDED | -40.96% | 47.70% | 1776 | 1757 | 1757 | 16.44 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 1.45% | 12.96% | 648 | 632 | 632 | 8.47 | 16 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | -8.96% | 20.75% | 468 | 451 | 451 | 13.35 | 17 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -35.05% | 37.28% | 524 | 509 | 509 | 10.19 | 15 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | -0.69% | 15.83% | 442 | 422 | 422 | 13.87 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | -33.63% | 43.22% | 2015 | 1995 | 1995 | 11.98 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 6 | development | SUCCEEDED | -41.63% | 48.89% | 1642 | 1623 | 1623 | 17.92 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | -1.03% | 12.96% | 640 | 625 | 625 | 8.32 | 15 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | -12.97% | 22.10% | 468 | 451 | 451 | 13.19 | 17 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -33.54% | 35.48% | 506 | 492 | 492 | 10.74 | 14 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | 0.90% | 14.91% | 422 | 402 | 402 | 13.92 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | -39.96% | 46.54% | 1956 | 1936 | 1936 | 12.23 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 1 | development | BLOCKED | — | — | 35 | 15 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 4.62% | 14.68% | 566 | 546 | 546 | 10.53 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | -3.25% | 22.29% | 483 | 464 | 464 | 13.69 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -41.80% | 42.03% | 495 | 478 | 478 | 11.79 | 17 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | 0.49% | 12.53% | 505 | 485 | 485 | 13.11 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 1 | continuous_2020_2023 | SUCCEEDED | -43.90% | 56.29% | 2004 | 1984 | 1984 | 12.61 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 3 | development | BLOCKED | — | — | 35 | 15 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 15.60% | 14.60% | 438 | 418 | 418 | 13.37 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | -5.77% | 19.42% | 330 | 310 | 310 | 20.1 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -37.21% | 38.31% | 390 | 371 | 371 | 15.05 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | -3.25% | 11.57% | 330 | 310 | 310 | 19.47 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | -30.96% | 46.17% | 1425 | 1405 | 1405 | 17.97 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 6 | development | BLOCKED | — | — | 35 | 15 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 18.00% | 14.60% | 429 | 410 | 410 | 13.24 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | -4.40% | 18.89% | 304 | 285 | 285 | 21.93 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -33.71% | 35.12% | 367 | 348 | 348 | 16.28 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 6 | year_2023 | SUCCEEDED | -4.22% | 12.12% | 306 | 287 | 287 | 19.54 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | PCT_10_20 | 6 | continuous_2020_2023 | SUCCEEDED | -23.36% | 43.05% | 1358 | 1339 | 1339 | 18.52 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 1 | development | BLOCKED | — | — | 161 | 142 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 5.10% | 17.79% | 335 | 315 | 315 | 20.81 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | -1.43% | 21.56% | 330 | 310 | 310 | 21.47 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 1 | year_2022 | BLOCKED | — | — | 136 | 116 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 1 | year_2023 | BLOCKED | — | — | 311 | 291 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 1 | continuous_2020_2023 | BLOCKED | — | — | 771 | 751 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 3 | development | BLOCKED | — | — | 92 | 72 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 5.79% | 17.12% | 186 | 167 | 167 | 36.46 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | 2.57% | 15.61% | 205 | 185 | 185 | 33.67 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 3 | year_2022 | BLOCKED | — | — | 86 | 67 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | -4.75% | 14.28% | 188 | 168 | 168 | 36.96 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 234 | 215 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 6 | development | BLOCKED | — | — | 435 | 415 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 6.16% | 17.12% | 156 | 136 | 136 | 40.43 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | -0.35% | 17.75% | 185 | 165 | 165 | 38.47 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 6 | year_2022 | BLOCKED | — | — | 75 | 55 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | -7.91% | 14.91% | 157 | 137 | 137 | 42.77 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_3_6 | 6 | continuous_2020_2023 | BLOCKED | — | — | 365 | 345 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 1 | development | BLOCKED | — | — | 115 | 96 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | -1.95% | 13.95% | 294 | 275 | 275 | 24.08 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 1 | year_2021 | SUCCEEDED | 0.92% | 11.97% | 282 | 262 | 262 | 26.06 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -23.82% | 24.37% | 281 | 261 | 261 | 25.9 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 1 | year_2023 | BLOCKED | — | — | 268 | 248 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 1 | continuous_2020_2023 | BLOCKED | — | — | 677 | 657 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 3 | development | BLOCKED | — | — | 63 | 43 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 13.99% | 12.25% | 141 | 122 | 122 | 50.73 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 3 | year_2021 | SUCCEEDED | -1.27% | 10.96% | 152 | 132 | 132 | 48.58 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -21.32% | 23.50% | 145 | 126 | 126 | 48.63 | 19 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | -4.50% | 10.50% | 129 | 109 | 109 | 54.02 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 3 | continuous_2020_2023 | SUCCEEDED | -7.59% | 31.91% | 545 | 525 | 525 | 51.94 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 6 | development | BLOCKED | — | — | 67 | 47 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 12.39% | 12.25% | 108 | 88 | 88 | 59.88 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | -1.75% | 12.62% | 119 | 99 | 99 | 63.4 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -12.29% | 15.74% | 110 | 90 | 90 | 60.36 | 20 | FULL_WINDOW |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 6 | year_2023 | BLOCKED | — | — | 91 | 71 | — | — | — | PARTIAL_BEFORE_BLOCK |
| wide | BREAKOUT_60_RVOL_1_5 | ATR_4_8 | 6 | continuous_2020_2023 | SUCCEEDED | -9.87% | 31.72% | 396 | 376 | 376 | 71.99 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 492 | 474 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | -7.08% | 16.13% | 988 | 969 | 969 | 5.42 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -16.83% | 18.49% | 873 | 856 | 856 | 6.76 | 17 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 369 | 351 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 230 | 215 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 2183 | 2165 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 1 | development | SUCCEEDED | -72.06% | 72.06% | 4209 | 4191 | 4191 | 3.4 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -32.44% | 33.75% | 1918 | 1906 | 1906 | 1.63 | 12 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -31.09% | 31.85% | 1709 | 1692 | 1692 | 2.39 | 17 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -1.41% | 1.53% | 41 | 41 | 41 | 2.27 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -28.35% | 28.81% | 1312 | 1297 | 1297 | 2.78 | 15 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -69.13% | 69.29% | 4967 | 4952 | 4952 | 2.23 | 15 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 350 | 331 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 447 | 429 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 2.98% | 15.76% | 575 | 558 | 558 | 10.55 | 17 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 296 | 278 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 124 | 104 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 447 | 429 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 3 | development | SUCCEEDED | -72.35% | 72.35% | 4105 | 4087 | 4087 | 3.52 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -32.07% | 33.38% | 1910 | 1898 | 1898 | 1.64 | 12 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -31.16% | 31.92% | 1688 | 1671 | 1671 | 2.43 | 17 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -1.41% | 1.53% | 41 | 41 | 41 | 2.27 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -26.55% | 27.10% | 1240 | 1225 | 1225 | 2.97 | 15 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -67.98% | 68.16% | 4866 | 4851 | 4851 | 2.29 | 15 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 344 | 325 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 427 | 409 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 6 | year_2021 | SUCCEEDED | 1.20% | 16.41% | 538 | 519 | 519 | 11.12 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 6 | year_2022 | BLOCKED | — | — | 276 | 257 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 124 | 104 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3% + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 427 | 409 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 6 | development | SUCCEEDED | -72.18% | 72.18% | 4100 | 4082 | 4082 | 3.53 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -32.07% | 33.38% | 1910 | 1898 | 1898 | 1.64 | 12 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -31.16% | 31.92% | 1688 | 1671 | 1671 | 2.43 | 17 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -1.41% | 1.53% | 41 | 41 | 41 | 2.27 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -26.55% | 27.10% | 1240 | 1225 | 1225 | 2.97 | 15 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -67.98% | 68.16% | 4866 | 4851 | 4851 | 2.29 | 15 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 224 | 206 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | -0.73% | 12.67% | 632 | 613 | 613 | 9.59 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -13.25% | 17.57% | 561 | 541 | 541 | 11.74 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 272 | 253 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 159 | 140 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 1430 | 1411 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 1 | development | SUCCEEDED | -44.74% | 46.43% | 2224 | 2204 | 2204 | 8.29 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 3.83% | 7.26% | 995 | 976 | 976 | 4.66 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | -14.42% | 17.18% | 866 | 848 | 848 | 6.42 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -1.99% | 2.35% | 33 | 33 | 33 | 4.24 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -15.46% | 18.79% | 675 | 656 | 656 | 7.2 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -25.09% | 31.88% | 2538 | 2519 | 2519 | 6.09 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 203 | 185 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 272 | 253 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 2.89% | 16.26% | 407 | 387 | 387 | 15.97 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 211 | 191 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 89 | 69 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 272 | 253 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 3 | development | SUCCEEDED | -42.30% | 44.34% | 1966 | 1946 | 1946 | 9.65 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 0.84% | 7.08% | 938 | 919 | 919 | 4.84 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | -13.87% | 16.60% | 775 | 757 | 757 | 7.28 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -1.99% | 2.35% | 33 | 33 | 33 | 4.24 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -8.51% | 12.43% | 558 | 539 | 539 | 9.23 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -20.78% | 26.71% | 2276 | 2257 | 2257 | 6.95 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 196 | 176 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 261 | 242 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 6 | year_2021 | SUCCEEDED | 10.48% | 12.03% | 313 | 293 | 293 | 21.03 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 6 | year_2022 | SUCCEEDED | -37.15% | 38.47% | 503 | 488 | 488 | 12.07 | 15 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 89 | 69 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 5% + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 261 | 242 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 6 | development | SUCCEEDED | -40.75% | 42.85% | 1938 | 1918 | 1918 | 9.82 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 0.84% | 7.08% | 938 | 919 | 919 | 4.84 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | -13.58% | 16.31% | 764 | 746 | 746 | 7.4 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -1.99% | 2.35% | 33 | 33 | 33 | 4.24 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -9.36% | 13.13% | 552 | 532 | 532 | 9.06 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -20.44% | 26.28% | 2257 | 2237 | 2237 | 6.95 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 234 | 215 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | -7.35% | 19.99% | 474 | 454 | 454 | 13.77 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -15.50% | 21.73% | 475 | 456 | 456 | 14.33 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 212 | 192 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 130 | 110 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 1132 | 1112 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 1 | development | SUCCEEDED | -42.16% | 44.75% | 1906 | 1886 | 1886 | 10.15 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 1.19% | 10.96% | 622 | 605 | 605 | 8.69 | 17 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 1 | year_2021 | SUCCEEDED | -17.09% | 24.66% | 659 | 640 | 640 | 8.95 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -2.58% | 2.74% | 29 | 29 | 29 | 5.31 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -23.64% | 26.95% | 560 | 542 | 542 | 8.92 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 1 | continuous_2020_2023 | SUCCEEDED | -37.19% | 42.35% | 1836 | 1818 | 1818 | 9.13 | 18 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 162 | 142 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | year_2020 | SUCCEEDED | -6.45% | 23.18% | 303 | 283 | 283 | 22.13 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | -7.24% | 23.82% | 325 | 305 | 305 | 20.59 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 169 | 149 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 74 | 54 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 727 | 707 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 3 | development | SUCCEEDED | -30.75% | 34.21% | 1670 | 1650 | 1650 | 11.72 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 4.76% | 10.56% | 528 | 509 | 509 | 10.12 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 3 | year_2021 | SUCCEEDED | -10.91% | 21.16% | 595 | 576 | 576 | 10.02 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -2.58% | 2.74% | 29 | 29 | 29 | 5.31 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -17.58% | 21.06% | 496 | 478 | 478 | 9.93 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 3 | continuous_2020_2023 | SUCCEEDED | -25.74% | 34.62% | 1612 | 1594 | 1594 | 10.53 | 18 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 155 | 135 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | year_2020 | SUCCEEDED | 2.68% | 23.18% | 288 | 268 | 268 | 22.57 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | year_2021 | SUCCEEDED | 0.66% | 19.05% | 283 | 264 | 264 | 23.77 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | year_2022 | BLOCKED | — | — | 156 | 136 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 74 | 54 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 653 | 633 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 6 | development | SUCCEEDED | -31.04% | 34.50% | 1665 | 1645 | 1645 | 11.76 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | 3.08% | 10.56% | 525 | 506 | 506 | 9.86 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 6 | year_2021 | SUCCEEDED | -10.31% | 21.18% | 595 | 576 | 576 | 10.01 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -2.58% | 2.74% | 29 | 29 | 29 | 5.31 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -17.34% | 21.06% | 495 | 476 | 476 | 9.77 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_1_5_3 | 6 | continuous_2020_2023 | SUCCEEDED | -24.25% | 34.51% | 1605 | 1586 | 1586 | 10.51 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 184 | 165 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | -3.51% | 19.99% | 380 | 360 | 360 | 18.08 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -17.21% | 24.79% | 382 | 363 | 363 | 18.56 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 159 | 141 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 101 | 81 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 385 | 365 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 1 | development | SUCCEEDED | -39.13% | 42.02% | 1414 | 1394 | 1394 | 14.73 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 3.93% | 12.56% | 422 | 402 | 402 | 13.83 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 1 | year_2021 | SUCCEEDED | -1.61% | 15.72% | 458 | 438 | 438 | 13.91 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -3.76% | 3.86% | 26 | 26 | 26 | 7.0 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -12.55% | 20.75% | 393 | 374 | 374 | 13.98 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 1 | continuous_2020_2023 | SUCCEEDED | -12.26% | 25.22% | 1269 | 1250 | 1250 | 14.24 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 136 | 117 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 167 | 148 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 3.33% | 20.31% | 244 | 224 | 224 | 28.05 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 117 | 99 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 56 | 36 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 167 | 148 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 3 | development | SUCCEEDED | -36.93% | 40.28% | 1087 | 1067 | 1067 | 19.56 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | -0.46% | 12.86% | 334 | 315 | 315 | 17.09 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | -9.06% | 20.35% | 351 | 332 | 332 | 18.26 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -3.76% | 3.86% | 26 | 26 | 26 | 7.0 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -8.21% | 16.29% | 314 | 295 | 295 | 17.62 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 3 | continuous_2020_2023 | SUCCEEDED | -18.17% | 28.31% | 995 | 976 | 976 | 18.52 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 303 | 283 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | year_2020 | SUCCEEDED | -1.23% | 26.52% | 216 | 196 | 196 | 29.25 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | year_2021 | BLOCKED | — | — | 50 | 30 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | year_2022 | BLOCKED | — | — | 104 | 86 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 56 | 36 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 216 | 197 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 6 | development | SUCCEEDED | -30.65% | 34.33% | 1050 | 1030 | 1030 | 20.59 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | -1.76% | 12.86% | 308 | 289 | 289 | 16.98 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | -2.45% | 15.36% | 336 | 317 | 317 | 19.18 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -3.76% | 3.86% | 26 | 26 | 26 | 7.0 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -6.39% | 14.08% | 307 | 287 | 287 | 17.64 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_2_4 | 6 | continuous_2020_2023 | SUCCEEDED | -9.21% | 21.69% | 925 | 905 | 905 | 19.89 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 218 | 198 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | -3.21% | 20.70% | 482 | 462 | 462 | 13.47 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -5.44% | 13.00% | 412 | 392 | 392 | 16.92 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 183 | 163 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 111 | 92 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 1049 | 1029 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 1 | development | SUCCEEDED | -27.99% | 30.18% | 1417 | 1398 | 1398 | 14.74 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 3.33% | 12.68% | 532 | 512 | 512 | 10.52 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 1 | year_2021 | SUCCEEDED | -11.41% | 18.55% | 492 | 474 | 474 | 12.78 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -2.81% | 3.17% | 28 | 28 | 28 | 7.96 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | -9.96% | 14.70% | 402 | 382 | 382 | 13.84 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 1 | continuous_2020_2023 | SUCCEEDED | -19.12% | 25.31% | 1425 | 1405 | 1405 | 12.5 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 149 | 130 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 182 | 164 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 15.24% | 17.66% | 251 | 231 | 231 | 27.26 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 134 | 114 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 61 | 42 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 182 | 164 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 3 | development | SUCCEEDED | -21.43% | 25.13% | 1017 | 998 | 998 | 21.05 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 3.43% | 12.09% | 438 | 419 | 419 | 12.59 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | -6.33% | 15.06% | 358 | 341 | 341 | 18.11 | 17 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -2.81% | 3.17% | 28 | 28 | 28 | 7.96 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | -6.66% | 11.02% | 282 | 262 | 262 | 21.08 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | -9.79% | 20.03% | 1058 | 1038 | 1038 | 17.49 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 143 | 123 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 178 | 160 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 6 | year_2021 | SUCCEEDED | 19.01% | 15.08% | 230 | 210 | 210 | 30.09 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 6 | year_2022 | BLOCKED | — | — | 123 | 103 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 61 | 42 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 8% + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 178 | 160 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 6 | development | SUCCEEDED | -20.09% | 25.52% | 929 | 910 | 910 | 23.64 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 3.23% | 12.09% | 444 | 425 | 425 | 12.28 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | -7.08% | 13.82% | 344 | 327 | 327 | 18.85 | 17 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -2.81% | 3.17% | 28 | 28 | 28 | 7.96 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | -4.47% | 9.77% | 263 | 243 | 243 | 18.7 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | -9.74% | 17.39% | 1031 | 1011 | 1011 | 16.97 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 185 | 165 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | 12.61% | 18.49% | 410 | 390 | 390 | 16.42 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -6.20% | 15.46% | 363 | 343 | 343 | 19.79 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 1 | year_2022 | SUCCEEDED | -41.17% | 42.00% | 413 | 397 | 397 | 16.38 | 16 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 350 | 330 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 1492 | 1472 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 1 | development | SUCCEEDED | -29.62% | 34.44% | 1211 | 1191 | 1191 | 17.92 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 15.25% | 10.06% | 403 | 383 | 383 | 14.49 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | 0.21% | 16.44% | 414 | 395 | 395 | 15.85 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -3.04% | 3.18% | 24 | 24 | 24 | 12.88 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | -5.84% | 12.46% | 333 | 313 | 313 | 17.53 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 1 | continuous_2020_2023 | SUCCEEDED | 3.83% | 22.49% | 1146 | 1126 | 1126 | 16.19 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 133 | 113 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 156 | 138 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 9.24% | 17.55% | 219 | 199 | 199 | 32.11 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 3 | year_2022 | SUCCEEDED | -39.07% | 39.29% | 285 | 265 | 265 | 24.09 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 57 | 38 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 156 | 138 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 3 | development | SUCCEEDED | -10.51% | 20.60% | 761 | 741 | 741 | 29.56 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 14.02% | 9.53% | 306 | 287 | 287 | 18.7 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | -0.92% | 13.92% | 284 | 265 | 265 | 23.84 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -3.23% | 3.37% | 24 | 24 | 24 | 13.17 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | -4.73% | 12.50% | 177 | 157 | 157 | 35.16 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | 10.16% | 16.37% | 749 | 729 | 729 | 25.61 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 126 | 106 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 6 | year_2020 | SUCCEEDED | 6.12% | 20.63% | 225 | 205 | 205 | 28.39 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 6 | year_2021 | BLOCKED | — | — | 47 | 27 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 6 | year_2022 | SUCCEEDED | -33.53% | 35.39% | 258 | 238 | 238 | 26.56 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 57 | 38 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 10% + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 497 | 477 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 6 | development | SUCCEEDED | -6.54% | 19.26% | 674 | 654 | 654 | 34.63 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 15.03% | 9.53% | 297 | 278 | 278 | 18.65 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | -0.98% | 16.34% | 251 | 232 | 232 | 26.38 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -3.23% | 3.37% | 24 | 24 | 24 | 13.17 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 6 | year_2023 | BLOCKED | — | — | 142 | 128 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | PCT_10_20 | 6 | continuous_2020_2023 | BLOCKED | — | — | 661 | 647 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 423 | 403 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | 11.47% | 16.72% | 307 | 287 | 287 | 23.35 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | 1.48% | 13.29% | 307 | 287 | 287 | 24.24 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | year_2022 | SUCCEEDED | -27.70% | 29.86% | 327 | 313 | 313 | 21.97 | 14 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | year_2023 | SUCCEEDED | 2.44% | 12.56% | 302 | 282 | 282 | 24.39 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 312 | 294 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 1 | development | SUCCEEDED | -20.91% | 25.38% | 1021 | 1001 | 1001 | 21.97 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 6.38% | 9.18% | 297 | 277 | 277 | 21.19 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 7.41% | 13.46% | 317 | 297 | 297 | 21.91 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -3.67% | 4.03% | 20 | 20 | 20 | 15.65 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | -3.56% | 12.96% | 280 | 260 | 260 | 22.0 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | 12.62% | 15.79% | 882 | 862 | 862 | 22.14 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 158 | 138 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 98 | 78 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 6.37% | 18.20% | 184 | 164 | 164 | 39.38 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | year_2022 | SUCCEEDED | -27.34% | 27.89% | 211 | 195 | 195 | 34.69 | 16 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | year_2023 | SUCCEEDED | 6.32% | 16.41% | 178 | 158 | 158 | 41.24 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 98 | 78 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 3 | development | SUCCEEDED | -11.50% | 17.93% | 604 | 584 | 584 | 38.86 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 3 | year_2020 | BLOCKED | — | — | 111 | 91 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | 6.46% | 14.55% | 207 | 187 | 187 | 33.66 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 3 | year_2022 | SUCCEEDED | -3.84% | 4.18% | 20 | 20 | 20 | 19.05 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | -1.23% | 9.72% | 165 | 145 | 145 | 38.01 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 3 | continuous_2020_2023 | BLOCKED | — | — | 111 | 91 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 216 | 196 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 91 | 72 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | year_2021 | BLOCKED | — | — | 40 | 20 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | year_2022 | SUCCEEDED | -25.65% | 26.91% | 189 | 174 | 174 | 35.98 | 15 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 147 | 129 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 91 | 72 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 6 | development | BLOCKED | — | — | 191 | 171 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 6 | year_2020 | BLOCKED | — | — | 103 | 84 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 11.20% | 12.61% | 171 | 151 | 151 | 40.29 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -4.25% | 4.30% | 20 | 20 | 20 | 23.15 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | -3.23% | 10.55% | 149 | 130 | 130 | 39.82 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_3_6 | 6 | continuous_2020_2023 | BLOCKED | — | — | 103 | 84 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 99 | 87 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | 10.85% | 15.38% | 284 | 264 | 264 | 25.61 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | 9.37% | 7.89% | 288 | 268 | 268 | 26.14 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 116 | 96 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | year_2023 | SUCCEEDED | 5.15% | 8.27% | 280 | 260 | 260 | 26.55 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 287 | 269 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 1 | development | BLOCKED | — | — | 82 | 63 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | -0.71% | 11.34% | 255 | 235 | 235 | 25.44 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 1 | year_2021 | SUCCEEDED | 2.37% | 13.02% | 279 | 259 | 259 | 26.08 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -4.04% | 4.85% | 20 | 20 | 20 | 23.75 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | 3.79% | 6.74% | 238 | 218 | 218 | 26.62 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 1 | continuous_2020_2023 | SUCCEEDED | 1.46% | 13.85% | 770 | 750 | 750 | 25.91 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 142 | 122 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 91 | 71 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 10.57% | 14.46% | 166 | 146 | 146 | 44.51 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | year_2022 | SUCCEEDED | -24.00% | 24.31% | 191 | 172 | 172 | 39.59 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | year_2023 | SUCCEEDED | -3.92% | 18.08% | 171 | 151 | 151 | 43.26 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 91 | 71 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 3 | development | SUCCEEDED | -6.21% | 13.80% | 441 | 421 | 421 | 56.43 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 4.76% | 9.99% | 125 | 105 | 105 | 52.24 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 3 | year_2021 | SUCCEEDED | 7.45% | 11.24% | 146 | 127 | 127 | 50.51 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -3.22% | 5.00% | 20 | 20 | 20 | 38.9 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | 3.81% | 6.18% | 114 | 94 | 94 | 58.43 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 3 | continuous_2020_2023 | SUCCEEDED | 7.89% | 12.35% | 367 | 347 | 347 | 56.75 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 81 | 61 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 83 | 64 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | year_2021 | BLOCKED | — | — | 37 | 17 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | year_2022 | SUCCEEDED | -17.76% | 20.14% | 162 | 142 | 142 | 44.69 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | year_2023 | SUCCEEDED | -4.49% | 18.10% | 153 | 133 | 133 | 46.15 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_20 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 83 | 64 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 6 | development | BLOCKED | — | — | 132 | 112 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 4.79% | 9.99% | 108 | 88 | 88 | 55.8 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | 7.73% | 11.76% | 119 | 100 | 100 | 62.03 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -4.43% | 5.00% | 20 | 20 | 20 | 51.1 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | 2.39% | 5.84% | 94 | 74 | 74 | 69.89 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_20_MARKET200 | ATR_4_8 | 6 | continuous_2020_2023 | SUCCEEDED | 10.03% | 9.99% | 293 | 273 | 273 | 74.05 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 527 | 510 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | -10.79% | 20.59% | 1018 | 1000 | 1000 | 4.82 | 18 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -23.97% | 27.59% | 999 | 981 | 981 | 5.62 | 18 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 447 | 431 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 238 | 220 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 2410 | 2394 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 1 | development | SUCCEEDED | -73.35% | 73.35% | 4338 | 4321 | 4321 | 2.74 | 17 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 1 | year_2020 | SUCCEEDED | -32.58% | 33.90% | 1969 | 1958 | 1958 | 1.31 | 11 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 1 | year_2021 | SUCCEEDED | -36.20% | 37.06% | 1884 | 1870 | 1870 | 1.75 | 14 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 1 | year_2022 | SUCCEEDED | -1.93% | 2.13% | 47 | 47 | 47 | 1.11 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 1 | year_2023 | SUCCEEDED | -31.56% | 31.65% | 1445 | 1433 | 1433 | 2.14 | 12 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | -72.64% | 72.66% | 5323 | 5311 | 5311 | 1.72 | 12 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 379 | 360 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 418 | 402 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 1.11% | 15.04% | 656 | 636 | 636 | 9.04 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 363 | 345 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 139 | 120 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 418 | 402 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 3 | development | SUCCEEDED | -73.41% | 73.41% | 4272 | 4255 | 4255 | 2.81 | 17 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 3 | year_2020 | SUCCEEDED | -32.58% | 33.90% | 1969 | 1958 | 1958 | 1.31 | 11 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 3 | year_2021 | SUCCEEDED | -36.01% | 36.87% | 1869 | 1855 | 1855 | 1.77 | 14 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 3 | year_2022 | SUCCEEDED | -1.93% | 2.13% | 47 | 47 | 47 | 1.11 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 3 | year_2023 | SUCCEEDED | -31.59% | 31.83% | 1428 | 1415 | 1415 | 2.14 | 13 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | -72.53% | 72.60% | 5291 | 5278 | 5278 | 1.73 | 13 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 383 | 364 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 409 | 391 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 6 | year_2021 | SUCCEEDED | 9.94% | 11.24% | 595 | 575 | 575 | 9.92 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 6 | year_2022 | BLOCKED | — | — | 351 | 333 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 139 | 120 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3% + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 409 | 391 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 6 | development | SUCCEEDED | -73.41% | 73.41% | 4272 | 4255 | 4255 | 2.81 | 17 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 6 | year_2020 | SUCCEEDED | -32.58% | 33.90% | 1969 | 1958 | 1958 | 1.31 | 11 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 6 | year_2021 | SUCCEEDED | -36.01% | 36.87% | 1869 | 1855 | 1855 | 1.77 | 14 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 6 | year_2022 | SUCCEEDED | -1.93% | 2.13% | 47 | 47 | 47 | 1.11 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 6 | year_2023 | SUCCEEDED | -31.59% | 31.83% | 1428 | 1415 | 1415 | 2.14 | 13 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | -72.53% | 72.60% | 5291 | 5278 | 5278 | 1.73 | 13 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 340 | 323 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 1 | year_2020 | BLOCKED | — | — | 659 | 640 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -24.96% | 30.67% | 652 | 632 | 632 | 9.78 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 292 | 273 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 153 | 134 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 659 | 640 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 1 | development | SUCCEEDED | -48.62% | 50.36% | 2437 | 2417 | 2417 | 6.96 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 1 | year_2020 | SUCCEEDED | 3.06% | 8.59% | 1092 | 1074 | 1074 | 3.99 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 1 | year_2021 | SUCCEEDED | -16.06% | 20.77% | 1018 | 999 | 999 | 4.96 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 1 | year_2022 | SUCCEEDED | -2.51% | 3.20% | 42 | 42 | 42 | 2.1 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 1 | year_2023 | SUCCEEDED | -17.48% | 19.00% | 773 | 754 | 754 | 5.66 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 1 | continuous_2020_2023 | SUCCEEDED | -29.61% | 34.67% | 2891 | 2872 | 2872 | 4.86 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 248 | 230 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 301 | 282 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | -8.14% | 21.44% | 449 | 429 | 429 | 14.11 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 239 | 220 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 80 | 62 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 301 | 282 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 3 | development | SUCCEEDED | -46.66% | 48.99% | 2200 | 2180 | 2180 | 7.91 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 3 | year_2020 | SUCCEEDED | 3.74% | 7.87% | 1057 | 1039 | 1039 | 4.16 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 3 | year_2021 | SUCCEEDED | -19.26% | 23.75% | 885 | 865 | 865 | 5.82 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 3 | year_2022 | SUCCEEDED | -2.51% | 3.20% | 42 | 42 | 42 | 2.1 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 3 | year_2023 | SUCCEEDED | -15.79% | 18.54% | 702 | 683 | 683 | 6.62 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 3 | continuous_2020_2023 | SUCCEEDED | -29.38% | 36.11% | 2646 | 2627 | 2627 | 5.51 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 247 | 228 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 280 | 261 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 6 | year_2021 | SUCCEEDED | 4.53% | 11.65% | 388 | 368 | 368 | 16.08 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 6 | year_2022 | BLOCKED | — | — | 231 | 211 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 80 | 62 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 5% + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 280 | 261 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 6 | development | SUCCEEDED | -45.56% | 47.95% | 2179 | 2159 | 2159 | 8.02 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 6 | year_2020 | SUCCEEDED | 3.74% | 7.87% | 1057 | 1039 | 1039 | 4.16 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 6 | year_2021 | SUCCEEDED | -18.42% | 22.94% | 878 | 858 | 858 | 5.88 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 6 | year_2022 | SUCCEEDED | -2.51% | 3.20% | 42 | 42 | 42 | 2.1 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 6 | year_2023 | SUCCEEDED | -17.11% | 19.00% | 698 | 679 | 679 | 6.18 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_5_10 | 6 | continuous_2020_2023 | SUCCEEDED | -29.79% | 35.84% | 2635 | 2616 | 2616 | 5.42 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 247 | 229 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | -20.39% | 29.63% | 484 | 464 | 464 | 13.27 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -19.30% | 26.91% | 479 | 459 | 459 | 14.08 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 230 | 210 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 126 | 107 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 1165 | 1145 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 1 | development | SUCCEEDED | -39.17% | 42.87% | 1883 | 1865 | 1865 | 9.73 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 1 | year_2020 | SUCCEEDED | 17.46% | 10.14% | 596 | 578 | 578 | 8.97 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 1 | year_2021 | BLOCKED | — | — | 180 | 166 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 1 | year_2022 | SUCCEEDED | -8.83% | 8.83% | 34 | 34 | 34 | 4.91 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 1 | year_2023 | SUCCEEDED | -18.48% | 22.42% | 570 | 552 | 552 | 8.53 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 1 | continuous_2020_2023 | BLOCKED | — | — | 767 | 753 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 174 | 157 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 190 | 172 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | -5.89% | 21.26% | 314 | 294 | 294 | 20.91 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 179 | 160 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 74 | 54 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 190 | 172 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 3 | development | SUCCEEDED | -37.53% | 41.21% | 1689 | 1671 | 1671 | 10.98 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 3 | year_2020 | SUCCEEDED | 20.97% | 10.67% | 511 | 493 | 493 | 10.6 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 3 | year_2021 | BLOCKED | — | — | 157 | 139 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 3 | year_2022 | SUCCEEDED | -8.83% | 8.83% | 34 | 34 | 34 | 4.91 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 3 | year_2023 | SUCCEEDED | -18.33% | 22.05% | 504 | 486 | 486 | 9.6 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 3 | continuous_2020_2023 | BLOCKED | — | — | 644 | 626 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 221 | 202 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 174 | 155 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | year_2021 | SUCCEEDED | 13.91% | 13.76% | 259 | 239 | 239 | 25.4 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | year_2022 | BLOCKED | — | — | 172 | 152 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 74 | 54 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 1.5 ATR + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 174 | 155 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 6 | development | SUCCEEDED | -38.93% | 42.51% | 1675 | 1657 | 1657 | 11.08 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 6 | year_2020 | SUCCEEDED | 23.63% | 8.28% | 490 | 472 | 472 | 10.21 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 6 | year_2021 | BLOCKED | — | — | 157 | 139 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 6 | year_2022 | SUCCEEDED | -8.83% | 8.83% | 34 | 34 | 34 | 4.91 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 6 | year_2023 | SUCCEEDED | -18.02% | 22.04% | 503 | 485 | 485 | 9.44 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_1_5_3 | 6 | continuous_2020_2023 | BLOCKED | — | — | 617 | 599 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 187 | 169 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | -17.60% | 28.06% | 395 | 375 | 375 | 17.16 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -21.09% | 28.29% | 382 | 362 | 362 | 18.3 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 181 | 162 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 361 | 341 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 398 | 378 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 1 | development | SUCCEEDED | -31.09% | 33.06% | 1343 | 1324 | 1324 | 14.97 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 1 | year_2020 | SUCCEEDED | 14.45% | 11.48% | 405 | 385 | 385 | 14.54 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 1 | year_2021 | BLOCKED | — | — | 124 | 109 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 1 | year_2022 | SUCCEEDED | -7.31% | 7.31% | 25 | 25 | 25 | 9.04 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 1 | year_2023 | SUCCEEDED | -7.01% | 15.60% | 387 | 368 | 368 | 13.78 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 1 | continuous_2020_2023 | BLOCKED | — | — | 517 | 503 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 165 | 145 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | year_2020 | SUCCEEDED | 2.25% | 20.23% | 208 | 188 | 188 | 32.93 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | -6.72% | 30.97% | 248 | 228 | 228 | 27.23 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 139 | 121 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 55 | 35 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 209 | 189 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 3 | development | SUCCEEDED | -39.17% | 41.10% | 1052 | 1032 | 1032 | 19.9 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 3 | year_2020 | SUCCEEDED | 9.77% | 9.24% | 284 | 264 | 264 | 20.45 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 3 | year_2021 | SUCCEEDED | -3.21% | 18.76% | 346 | 327 | 327 | 18.29 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 3 | year_2022 | SUCCEEDED | -7.31% | 7.31% | 25 | 25 | 25 | 9.04 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 3 | year_2023 | SUCCEEDED | -9.60% | 18.44% | 304 | 285 | 285 | 18.32 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 3 | continuous_2020_2023 | SUCCEEDED | -6.50% | 22.39% | 909 | 890 | 890 | 20.32 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 163 | 143 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | year_2020 | SUCCEEDED | 3.66% | 20.23% | 182 | 162 | 162 | 34.42 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | year_2021 | BLOCKED | — | — | 47 | 27 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | year_2022 | BLOCKED | — | — | 130 | 112 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 55 | 35 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 2 ATR + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 476 | 458 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 6 | development | SUCCEEDED | -40.25% | 42.15% | 1047 | 1027 | 1027 | 20.03 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 6 | year_2020 | SUCCEEDED | 8.58% | 9.73% | 248 | 229 | 229 | 22.26 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 6 | year_2021 | SUCCEEDED | 0.50% | 16.96% | 342 | 323 | 323 | 18.46 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 6 | year_2022 | SUCCEEDED | -7.31% | 7.31% | 25 | 25 | 25 | 9.04 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 6 | year_2023 | SUCCEEDED | -11.21% | 20.13% | 295 | 276 | 276 | 18.14 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_2_4 | 6 | continuous_2020_2023 | SUCCEEDED | 1.61% | 20.68% | 856 | 837 | 837 | 21.53 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 246 | 227 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | -17.71% | 27.58% | 501 | 481 | 481 | 12.51 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -15.16% | 22.87% | 445 | 425 | 425 | 15.41 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 210 | 190 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 116 | 97 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 1115 | 1095 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 1 | development | SUCCEEDED | -28.75% | 32.48% | 1427 | 1408 | 1408 | 13.78 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 1 | year_2020 | SUCCEEDED | 13.52% | 8.15% | 591 | 573 | 573 | 9.14 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 1 | year_2021 | SUCCEEDED | -6.39% | 17.84% | 555 | 537 | 537 | 10.94 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 1 | year_2022 | SUCCEEDED | -4.43% | 4.58% | 34 | 34 | 34 | 5.79 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 1 | year_2023 | SUCCEEDED | -11.00% | 15.30% | 461 | 442 | 442 | 11.31 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 1 | continuous_2020_2023 | SUCCEEDED | -7.21% | 24.84% | 1602 | 1583 | 1583 | 10.62 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 166 | 147 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 209 | 191 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 7.95% | 18.70% | 270 | 250 | 250 | 24.88 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 167 | 147 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 64 | 45 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 209 | 191 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 3 | development | SUCCEEDED | -16.34% | 25.57% | 1052 | 1032 | 1032 | 19.25 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 3 | year_2020 | SUCCEEDED | 11.83% | 9.03% | 495 | 480 | 480 | 10.96 | 15 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 3 | year_2021 | SUCCEEDED | -3.42% | 14.03% | 426 | 409 | 409 | 14.45 | 17 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 3 | year_2022 | SUCCEEDED | -4.43% | 4.58% | 34 | 34 | 34 | 5.79 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 3 | year_2023 | SUCCEEDED | -6.82% | 13.01% | 336 | 317 | 317 | 16.72 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 3 | continuous_2020_2023 | SUCCEEDED | -0.54% | 18.47% | 1251 | 1232 | 1232 | 14.16 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 164 | 144 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 200 | 181 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 6 | year_2021 | SUCCEEDED | 16.34% | 17.42% | 227 | 207 | 207 | 29.61 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 6 | year_2022 | BLOCKED | — | — | 156 | 136 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 64 | 45 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 8% + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 200 | 181 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 6 | development | SUCCEEDED | -16.14% | 27.45% | 1019 | 999 | 999 | 20.08 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 6 | year_2020 | SUCCEEDED | 11.78% | 8.77% | 491 | 475 | 475 | 10.61 | 16 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 6 | year_2021 | SUCCEEDED | -0.42% | 11.80% | 409 | 392 | 392 | 15.17 | 17 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 6 | year_2022 | SUCCEEDED | -4.43% | 4.58% | 34 | 34 | 34 | 5.79 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 6 | year_2023 | SUCCEEDED | -6.29% | 12.12% | 310 | 291 | 291 | 16.86 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_8_16 | 6 | continuous_2020_2023 | SUCCEEDED | 2.72% | 14.75% | 1195 | 1176 | 1176 | 14.54 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 203 | 183 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | -7.02% | 22.97% | 424 | 404 | 404 | 15.4 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -22.69% | 30.67% | 384 | 364 | 364 | 18.26 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 1 | year_2022 | SUCCEEDED | -48.66% | 48.66% | 447 | 429 | 429 | 14.35 | 18 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 102 | 83 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | SUCCEEDED | -68.64% | 70.53% | 1599 | 1579 | 1579 | 16.77 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 1 | development | BLOCKED | — | — | 65 | 51 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 1 | year_2020 | SUCCEEDED | 21.34% | 12.10% | 439 | 419 | 419 | 13.08 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 1 | year_2021 | SUCCEEDED | 2.36% | 18.43% | 453 | 434 | 434 | 14.04 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 1 | year_2022 | SUCCEEDED | -5.23% | 5.23% | 29 | 29 | 29 | 7.62 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 1 | year_2023 | SUCCEEDED | -5.00% | 10.77% | 367 | 347 | 347 | 14.81 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 1 | continuous_2020_2023 | SUCCEEDED | 15.81% | 18.91% | 1258 | 1238 | 1238 | 14.15 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 136 | 117 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 172 | 154 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 4.25% | 22.28% | 241 | 221 | 221 | 28.6 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 3 | year_2022 | SUCCEEDED | -37.19% | 37.86% | 312 | 293 | 293 | 21.04 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 61 | 41 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 172 | 154 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 3 | development | BLOCKED | — | — | 65 | 51 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 3 | year_2020 | SUCCEEDED | 23.60% | 7.33% | 342 | 322 | 322 | 16.34 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 3 | year_2021 | SUCCEEDED | 1.55% | 17.44% | 330 | 311 | 311 | 19.6 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 3 | year_2022 | SUCCEEDED | -5.23% | 5.23% | 29 | 29 | 29 | 7.62 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 3 | year_2023 | SUCCEEDED | -3.86% | 10.94% | 243 | 223 | 223 | 23.94 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 3 | continuous_2020_2023 | SUCCEEDED | 13.12% | 18.72% | 876 | 856 | 856 | 21.11 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 134 | 114 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 167 | 150 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 6 | year_2021 | BLOCKED | — | — | 49 | 29 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 6 | year_2022 | SUCCEEDED | -31.99% | 35.43% | 284 | 266 | 266 | 22.25 | 18 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 61 | 41 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 10% + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 167 | 150 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 6 | development | BLOCKED | — | — | 65 | 51 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 6 | year_2020 | SUCCEEDED | 19.14% | 8.32% | 325 | 307 | 307 | 16.4 | 18 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 6 | year_2021 | SUCCEEDED | 6.97% | 16.24% | 295 | 276 | 276 | 21.89 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 6 | year_2022 | SUCCEEDED | -5.23% | 5.23% | 29 | 29 | 29 | 7.62 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 6 | year_2023 | BLOCKED | — | — | 196 | 186 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | PCT_10_20 | 6 | continuous_2020_2023 | BLOCKED | — | — | 798 | 788 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 154 | 135 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | -2.85% | 19.31% | 314 | 294 | 294 | 22.66 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -11.03% | 21.82% | 300 | 280 | 280 | 24.32 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | year_2022 | BLOCKED | — | — | 133 | 113 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | year_2023 | SUCCEEDED | -0.65% | 11.27% | 308 | 288 | 288 | 23.47 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 316 | 296 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 1 | development | BLOCKED | — | — | 346 | 326 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 1 | year_2020 | SUCCEEDED | 15.01% | 7.06% | 292 | 272 | 272 | 21.48 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 1 | year_2021 | SUCCEEDED | 7.42% | 15.09% | 319 | 300 | 300 | 21.62 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 1 | year_2022 | SUCCEEDED | -5.54% | 6.43% | 21 | 21 | 21 | 15.57 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 1 | year_2023 | SUCCEEDED | 7.04% | 8.32% | 282 | 262 | 262 | 20.94 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 1 | continuous_2020_2023 | SUCCEEDED | 28.55% | 14.44% | 895 | 875 | 875 | 21.44 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 131 | 113 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 95 | 75 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 3.17% | 17.78% | 188 | 168 | 168 | 38.55 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 89 | 70 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 178 | 158 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 95 | 75 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 3 | development | SUCCEEDED | -10.40% | 17.51% | 576 | 556 | 556 | 40.8 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 3 | year_2020 | SUCCEEDED | 12.39% | 8.59% | 169 | 149 | 149 | 35.81 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 3 | year_2021 | SUCCEEDED | 1.18% | 17.31% | 207 | 187 | 187 | 32.58 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 3 | year_2022 | SUCCEEDED | -6.85% | 7.14% | 21 | 21 | 21 | 19.48 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 3 | year_2023 | SUCCEEDED | -3.54% | 12.27% | 171 | 151 | 151 | 37.15 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 3 | continuous_2020_2023 | SUCCEEDED | 8.27% | 19.89% | 530 | 510 | 510 | 37.78 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 126 | 107 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 85 | 65 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | year_2021 | BLOCKED | — | — | 41 | 21 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | year_2022 | BLOCKED | — | — | 80 | 60 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | year_2023 | SUCCEEDED | -7.40% | 19.96% | 161 | 141 | 141 | 44.63 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 3 ATR + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 85 | 65 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 6 | development | BLOCKED | — | — | 171 | 153 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 6 | year_2020 | SUCCEEDED | 12.21% | 8.59% | 131 | 111 | 111 | 44.81 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 6 | year_2021 | SUCCEEDED | 5.07% | 15.45% | 189 | 169 | 169 | 34.73 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 6 | year_2022 | SUCCEEDED | -7.26% | 7.26% | 21 | 21 | 21 | 23.38 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 6 | year_2023 | SUCCEEDED | -3.64% | 11.04% | 153 | 133 | 133 | 37.78 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_3_6 | 6 | continuous_2020_2023 | SUCCEEDED | 6.89% | 21.85% | 447 | 427 | 427 | 44.28 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | development | BLOCKED | — | — | 136 | 117 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | year_2020 | SUCCEEDED | 0.28% | 15.96% | 288 | 268 | 268 | 25.04 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | year_2021 | SUCCEEDED | -5.39% | 17.19% | 282 | 262 | 262 | 26.42 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | year_2022 | SUCCEEDED | -25.84% | 26.69% | 290 | 271 | 271 | 24.97 | 19 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | year_2023 | BLOCKED | — | — | 268 | 248 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 1 | continuous_2020_2023 | BLOCKED | — | — | 290 | 271 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 1 | development | BLOCKED | — | — | 79 | 62 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 1 | year_2020 | SUCCEEDED | 5.60% | 7.72% | 250 | 231 | 231 | 25.97 | 19 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 1 | year_2021 | SUCCEEDED | 1.36% | 12.73% | 277 | 257 | 257 | 25.79 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 1 | year_2022 | SUCCEEDED | -4.67% | 5.93% | 20 | 20 | 20 | 24.4 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 1 | year_2023 | SUCCEEDED | 3.03% | 8.48% | 239 | 219 | 219 | 25.61 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 1 | continuous_2020_2023 | SUCCEEDED | 10.04% | 14.26% | 764 | 744 | 744 | 25.82 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | development | BLOCKED | — | — | 109 | 91 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | year_2020 | BLOCKED | — | — | 89 | 69 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | year_2021 | SUCCEEDED | 3.63% | 15.59% | 165 | 145 | 145 | 44.72 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | year_2022 | BLOCKED | — | — | 80 | 61 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | year_2023 | BLOCKED | — | — | 159 | 139 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 3 | continuous_2020_2023 | BLOCKED | — | — | 89 | 69 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 3 | development | BLOCKED | — | — | 255 | 235 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 3 | year_2020 | SUCCEEDED | 7.47% | 8.43% | 131 | 111 | 111 | 48.92 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 3 | year_2021 | SUCCEEDED | 1.78% | 13.42% | 145 | 125 | 125 | 50.06 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 3 | year_2022 | SUCCEEDED | -4.21% | 6.24% | 20 | 20 | 20 | 38.55 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 3 | year_2023 | SUCCEEDED | -3.05% | 7.87% | 127 | 107 | 107 | 51.04 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 3 | continuous_2020_2023 | SUCCEEDED | -7.57% | 21.81% | 382 | 362 | 362 | 54.19 | 20 | FULL_WINDOW |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | development | BLOCKED | — | — | 102 | 83 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | year_2020 | BLOCKED | — | — | 80 | 60 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | year_2021 | BLOCKED | — | — | 38 | 18 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | year_2022 | BLOCKED | — | — | 73 | 53 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | year_2023 | BLOCKED | — | — | 147 | 127 | — | — | — | PARTIAL_BEFORE_BLOCK |
| trend_exit | BREAKOUT_60 | 손절 4 ATR + LOW20(고정 익절 없음) | 6 | continuous_2020_2023 | BLOCKED | — | — | 80 | 60 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 6 | development | BLOCKED | — | — | 200 | 180 | — | — | — | PARTIAL_BEFORE_BLOCK |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 6 | year_2020 | SUCCEEDED | 5.01% | 8.43% | 98 | 78 | 78 | 67.44 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 6 | year_2021 | SUCCEEDED | -0.26% | 12.68% | 118 | 98 | 98 | 61.69 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 6 | year_2022 | SUCCEEDED | -4.77% | 6.24% | 20 | 20 | 20 | 46.75 | 0 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 6 | year_2023 | SUCCEEDED | -5.01% | 7.95% | 105 | 85 | 85 | 60.4 | 20 | FULL_WINDOW |
| market_filter | BREAKOUT_60_MARKET200 | ATR_4_8 | 6 | continuous_2020_2023 | SUCCEEDED | -1.80% | 20.73% | 300 | 280 | 280 | 71.13 | 20 | FULL_WINDOW |
| momentum | MOMENTUM_ENTRY | 월간 탈락(고정 손절·익절 없음) | 월간교체 | development | BLOCKED | — | — | 125 | 105 | — | — | — | PARTIAL_BEFORE_BLOCK |
| momentum | MOMENTUM_ENTRY | 월간 탈락(고정 손절·익절 없음) | 월간교체 | year_2020 | BLOCKED | — | — | 70 | 50 | — | — | — | PARTIAL_BEFORE_BLOCK |
| momentum | MOMENTUM_ENTRY | 월간 탈락(고정 손절·익절 없음) | 월간교체 | year_2021 | SUCCEEDED | -30.88% | 34.18% | 95 | 75 | 75 | 64.76 | 20 | FULL_WINDOW |
| momentum | MOMENTUM_ENTRY | 월간 탈락(고정 손절·익절 없음) | 월간교체 | year_2022 | BLOCKED | — | — | 34 | 14 | — | — | — | PARTIAL_BEFORE_BLOCK |
| momentum | MOMENTUM_ENTRY | 월간 탈락(고정 손절·익절 없음) | 월간교체 | year_2023 | SUCCEEDED | -3.78% | 30.25% | 67 | 49 | 49 | 83.47 | 18 | FULL_WINDOW |
| momentum | MOMENTUM_ENTRY | 월간 탈락(고정 손절·익절 없음) | 월간교체 | continuous_2020_2023 | BLOCKED | — | — | 70 | 50 | — | — | — | PARTIAL_BEFORE_BLOCK |
