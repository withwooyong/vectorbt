# 배정비율 104키 원문·매칭·산식 감사

이 문서는 현재 해시와 일치하는 계수 v2에서 **가격은 승인됐지만 배정비율 때문에 거래량은 미승인인 104키**를 저장 원문으로 전수 감사한다. 결론은 104키 모두 현행 미승인을 유지한다는 것이다. 46건은 원문 주식수로 계산한 실효 총주식 계수가 가격 역산값과 0.5% 안에서 맞지만 현행 직접 배정비율 정책과 다른 산식이고, 나머지도 원문 부족·후보 모호성·기준일 불일치·미해결 산식이 남는다. 아래 복구 후보는 다음 조사 입력이며 승인·원자료 정정·정책 변경이 아니다.

범위는 로컬에 보존된 DART 원공시 ZIP, 수집 manifest, 파싱 결과, KRX 기준가격 원문, v2 후보·감사 Parquet다. 네트워크/API/DB·백테스트는 사용하지 않았고 ted-startup은 수정하지 않았다. `factor-admission-v3` 잔여는 제외했다.

## 핵심 결과

- 전수성: **104 / 104**, 고유 `(stock_code, effective_date)` **104 / 104**.
- 현재 차단: `ALLOTMENT_RATIO_MISMATCH` 50건, `ALLOTMENT_RATIO_NOT_PARSED` 54건.
- 해시: 정책→파서→수집 manifest/원문→후보→v2 감사 체인과 104키 KRX 원문·저장 DART ZIP의 SHA-256 대조를 모두 통과했다.
- 원문 대조 범위: 완전 저장 원공시 53키, 복수 후보 중 일부 원문만 저장 2키, 해당 키 원문 미저장 49키.
- 실행 상태: 거래량 미승인 유지, `signal_admitted=false`, `real_execution_admitted=false`; 실행·성과 수치는 만들지 않았다.

원문 미저장은 공시가 없었다거나 수집에서 누락됐다는 뜻이 아니다. 저장된 120일 검색 결과와 정책 제목 필터만으로는 원인을 확정할 수 없다는 뜻이다.

## 원인 분류

| 원인 | 건수 | 판단과 다음 확인 |
| --- | ---: | --- |
| 직접·실효 비율 모두 가격 역산값과 불일치 (`DIRECT_AND_EFFECTIVE_RATIOS_BOTH_MISMATCH_PRICE_BACKCOMPUTATION`) | 4 | 직접 비율뿐 아니라 원문 총주식수 기반 계수도 0.5%를 넘는다. 기준가격 산식·anchor·복합행사를 별도 감사해야 함. |
| 적격주주 배정비율과 실효 총주식 비율 차이 (`ELIGIBLE_SHARE_RATIO_DIFFERS_FROM_TOTAL_ISSUED_EFFECTIVE_RATIO`) | 45 | 원공시의 신주/배당주식수 ÷ 전체 발행주식수 계수는 가격 역산값과 0.5% 안에서 맞는다. 자기주식 제외·단수주 절사와 정합적이지만 현행 정책 산식이 아니므로 차단 유지. |
| 유일 후보의 기준일 불일치 (`MATCHED_DISCLOSURE_RECORD_DATE_MISMATCH`) | 2 | 유일 제목 후보의 원문 기준일이 목표 effective date 허용 범위와 맞지 않아 다른 사건으로 판정됨. |
| 보통주 비율 없음·종류주식만 존재 (`ORDINARY_SHARE_RATIO_ABSENT_PREFERRED_ONLY`) | 1 | 원문 보통주 칸은 '-'이고 종류주식 0.15만 있다. 종류주식 값을 보통주에 대입하지 않음. |
| 원문 표 모순과 콤마 숫자 파서 절단 (`RAW_TABLE_RATIO_FIELD_INCONSISTENT_AND_PARSER_COMMA_TRUNCATION`) | 1 | 208340/2020-06-30은 1주당 표 칸이 신주 총수와 같은 6,910,809이고 서술은 1주당 1주다. 파서는 콤마 앞 6만 읽었다. 원문 내부 모순과 파서 문제를 함께 해결해야 함. |
| 정책 제목 후보 복수 (`SEARCH_RESULT_MULTIPLE_POLICY_TITLE_CANDIDATES`) | 9 | 원공시 제목 후보가 2건이라 수집기가 선택하지 않았다. 모든 후보 원문과 기준일을 확보하기 전 선택 금지. |
| 저장 검색결과에 정책 제목 후보 없음 (`SEARCH_RESULT_NO_POLICY_TITLE_CANDIDATE`) | 42 | 저장 검색 결과에서 비정정 정책 제목 후보가 0건이다. 원공시 부재/누락으로 단정하지 않고 검색·기업코드·명칭 범위를 재감사해야 함. |

## 산식 감사

현행 정책 비교는 `expected = 1 + DART 1주당 배정비율`, `back = anchor_close / KRX 공식 기준가격`, `gap = abs(expected - back) / back`이며 `gap <= 0.005`만 승인한다. 이 기준으로 50건이 불일치했다.

50건 중 일반형 45건은 공시의 1주당 배정비율이 배정 대상 주식에 적용된 값인 반면, `1 + 신주(또는 배당주식) 총수 / 행사 전 발행주식총수`는 가격 역산값과 0.5% 안에서 맞았다. 구형 서식인 060720/2015-03-12도 이 45건에 포함된다. 이는 자기주식 제외나 단수주 처리로 설명 가능한 복구 후보지만 현행 정책이 요구하는 직접 비교를 바꾸므로 자동 승격할 수 없다.

`208340/2020-06-30`은 별도 원인 1건이다. 원공시 표의 '1주당 신주배정 주식수'에 `6,910,809`가 들어가 신주 총수와 같고, 본문 서술은 1주당 1주다. 기존 파서는 콤마 숫자의 앞부분 `6`을 배정비율로 기록했다. 본문 1과 총주식 계수 2는 가격 역산 2와 맞지만 원문 표 자체가 모순이어서 원자료를 고쳐 덮어쓰지 않고 차단을 유지한다. 따라서 실효 총주식 계수가 0.5% 안에서 맞는 건수는 일반형 45건과 이 특이 1건을 합친 46건이며, 208340을 다시 더하지 않는다.

나머지 4건(`089030/2022-08-01`, `097780/2017-05-30`, `131970/2020-09-15`, `137400/2019-05-07`)은 원문 총주식수 계수도 0.5%를 넘었다. 저장 자료만으로 기준가격 차이를 확정 설명할 수 없어 KRX 산식·anchor·동시 기업행사 감사를 남긴다.

## 키별 판정

상세 수치·공시번호·원문 경로·SHA-256·필드·snippet은 `allotment-104-audit.json`에 있다.

| 키 | 종류 | 현재 차단 | 원인 | 원문 범위 | 복구 후보 |
| --- | --- | --- | --- | --- | --- |
| 000230/2018-12-27 | STOCK_DIVIDEND | ALLOTMENT_RATIO_NOT_PARSED | 정책 제목 후보 복수 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 001040/2018-12-27 | STOCK_DIVIDEND | ALLOTMENT_RATIO_NOT_PARSED | 보통주 비율 없음·종류주식만 존재 | COMPLETE_STORED_MATCHED_ORIGINAL | 확정 후보 없음 |
| 003000/2016-12-28 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 003000/2020-12-29 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 003690/2022-12-12 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 003690/2023-11-20 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 003850/2021-07-16 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 005420/2022-06-22 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 006620/2021-03-02 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 006740/2023-04-19 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 007820/2015-06-05 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 정책 제목 후보 복수 | PARTIAL_STORED_CANDIDATE_ORIGINALS | 있음(재심사 필요) |
| 011000/2021-12-03 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 016250/2020-12-29 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 016250/2021-12-29 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 016250/2022-12-28 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 016790/2023-07-26 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 025900/2018-12-27 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 028300/2020-06-05 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 033310/2021-09-13 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 037620/2015-11-09 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 049950/2018-12-27 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 049950/2022-12-28 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 053580/2021-05-04 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 053610/2019-07-05 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 054450/2018-03-26 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 054950/2021-03-30 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 060250/2021-11-25 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 060250/2021-12-29 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 060720/2015-03-12 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 064260/2016-06-16 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 067310/2021-12-16 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 078160/2019-03-29 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 078340/2015-08-10 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 078600/2016-12-14 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 080160/2017-06-21 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 083790/2018-07-10 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 084110/2016-12-28 | STOCK_DIVIDEND | ALLOTMENT_RATIO_NOT_PARSED | 정책 제목 후보 복수 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 084110/2017-12-27 | STOCK_DIVIDEND | ALLOTMENT_RATIO_NOT_PARSED | 정책 제목 후보 복수 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 084110/2018-12-27 | STOCK_DIVIDEND | ALLOTMENT_RATIO_NOT_PARSED | 정책 제목 후보 복수 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 084110/2019-12-27 | STOCK_DIVIDEND | ALLOTMENT_RATIO_NOT_PARSED | 정책 제목 후보 복수 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 084110/2020-12-29 | STOCK_DIVIDEND | ALLOTMENT_RATIO_NOT_PARSED | 정책 제목 후보 복수 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 084110/2021-12-29 | STOCK_DIVIDEND | ALLOTMENT_RATIO_NOT_PARSED | 정책 제목 후보 복수 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 084990/2019-08-13 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 085370/2017-03-02 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 086900/2020-10-22 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 089030/2022-08-01 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 직접·실효 비율 모두 가격 역산값과 불일치 | COMPLETE_STORED_MATCHED_ORIGINAL | 확정 후보 없음 |
| 089140/2016-11-03 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 089140/2021-06-18 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 092040/2023-12-13 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 094170/2017-12-27 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 094170/2018-06-12 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 094170/2018-12-27 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 094170/2020-12-29 | STOCK_DIVIDEND | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 095610/2016-04-14 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 유일 후보의 기준일 불일치 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 095700/2023-01-11 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 096530/2021-04-23 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 097780/2017-05-30 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 직접·실효 비율 모두 가격 역산값과 불일치 | COMPLETE_STORED_MATCHED_ORIGINAL | 확정 후보 없음 |
| 099320/2019-02-13 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 109610/2016-07-27 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 109610/2017-02-16 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 109610/2020-10-22 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 112040/2021-09-13 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 112610/2021-02-08 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 114120/2017-06-12 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 115180/2023-12-18 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 118990/2022-06-02 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 131970/2020-09-15 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 직접·실효 비율 모두 가격 역산값과 불일치 | COMPLETE_STORED_MATCHED_ORIGINAL | 확정 후보 없음 |
| 136510/2021-10-28 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 유일 후보의 기준일 불일치 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 137400/2019-05-07 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 직접·실효 비율 모두 가격 역산값과 불일치 | COMPLETE_STORED_MATCHED_ORIGINAL | 확정 후보 없음 |
| 138080/2017-07-14 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 138080/2019-12-26 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 139670/2020-01-21 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 145020/2020-07-08 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 149980/2023-02-03 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 161580/2018-05-30 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 171120/2019-01-31 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 175250/2021-12-06 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 175250/2022-12-14 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 179900/2018-11-08 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 185490/2021-06-28 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 194510/2015-11-05 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 205470/2023-03-24 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 208340/2020-06-30 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 원문 표 모순과 콤마 숫자 파서 절단 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 208340/2021-08-19 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 225530/2017-01-05 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 정책 제목 후보 복수 | PARTIAL_STORED_CANDIDATE_ORIGINALS | 있음(재심사 필요) |
| 226950/2020-12-03 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 241820/2023-09-14 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 245620/2021-03-17 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 247540/2022-06-27 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 260930/2021-03-25 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 263050/2022-07-12 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 263720/2017-11-29 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 267260/2017-11-17 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 267270/2017-11-14 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 289220/2021-12-20 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 290510/2020-10-29 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 294090/2022-01-17 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 298060/2023-09-15 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 299030/2021-03-22 | BONUS_ISSUE | ALLOTMENT_RATIO_MISMATCH | 적격주주 배정비율과 실효 총주식 비율 차이 | COMPLETE_STORED_MATCHED_ORIGINAL | 있음(재심사 필요) |
| 310210/2023-09-13 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 323990/2023-11-10 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 328130/2023-11-09 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 347860/2022-11-09 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |
| 377030/2022-04-18 | BONUS_ISSUE | ALLOTMENT_RATIO_NOT_PARSED | 저장 검색결과에 정책 제목 후보 없음 | NO_STORED_ORIGINAL_FOR_TARGET | 있음(재심사 필요) |

## 재실행과 한계

저장 원문이 그대로인 환경에서 새 출력 디렉터리에 JSON과 이 문서를 다시 만든다. 기존 출력이 있으면 기본적으로 거절한다.

```powershell
.venv\Scripts\python.exe -B scripts\research\audit_ohlcv20_allotment104.py --ted-root C:\Users\aeby\vscode\ted-startup --output-dir docs/strategy-research/backtest-lab/ohlcv20-factor-v2-intake-2026-09-23/allotment-new
```

스크립트는 104 고유키, v2의 733/643/539/539 집계, 모든 핵심·원문 해시를 검증하고 불일치하면 산출 전에 실패한다. 결과는 독립 승인 영수증이 아니며, 복구 후보를 적용하려면 ted-startup에서 원문 연결·정책·파서를 별도 검토하고 새 불변 revision으로 전달해야 한다.
