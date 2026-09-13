# 증권사 조건검색·AI 뉴스검토·자동주문 통합 기준

> **최신 요구 기준:** [Backtest Lab 설계 패키지](backtest-lab/README.md)가 우선한다. 최대 보유는 달력 1개월, 매수 전 익절·손절 가격 지정, 초기 1억 원·외부 입출금0·이익 재투자이며 별도 여유자금 1~2억 원은 제외한다. 기존 2~5일 중심 해석은 폐기했고 종목 수 확대와 매수금액 확대는 비교 후 결정한다. 현재 단계는 기술전략 일괄 연구 프로그램의 문서 설계다.

이 문서는 vectorbt로 검증한 기술전략을 키움 또는 한국투자증권의 사전 저장 조건식으로 운용하고, 종목이 포착되면 AI 뉴스검토 후 매수하며 체결 수량에 목표가 매도를 내는 흐름의 공식 지원 범위를 정리한다. 확인일은 2026-09-13이며 공식 API 문서와 공식 GitHub만 사용했다.

**현재 공식 자료만 보면 키움은 조건 목록→일반조회→실시간 등록→편입·이탈 푸시→해지 흐름을 직접 제공한다. 한국투자는 HTS에 저장한 조건의 목록·결과 REST 조회는 제공하지만 조건 편입·이탈 WebSocket 푸시는 확인되지 않았다.** 따라서 키움은 푸시 후보, 한국투자는 폴링 후보로 설계하되 실제 계정의 모의지원·호출제한·시장 범위를 검증한 뒤 증권사를 선택한다.

자동매매 승인은 아직 아니다. 조건식 의미 일치, AI 판단의 시점·실패 정책, 최대 20종목 동시성, 부분체결과 매도가능수량, 주문 유효기간을 모의계좌에서 검증해야 한다. 단타와 스윙도 동일 실행기로 섞지 않고 보유기간·주문정책·위험한도를 별도 전략 버전으로 둔다.

## 지원 확인과 계정 검증 필요 항목

| 항목 | 키움 REST API | 한국투자 KIS API | 상태 |
| --- | --- | --- | --- |
| 조건식 사전 설정 | 목록 API는 저장된 `seq`, `name`만 반환; 생성·서버저장 절차는 검토 자료에 없음 | eFriend Plus `[0110]`에서 등록 후 `사용자조건 서버저장` 필요 | 키움 절차 계정 검증 / KIS 공식 확인 |
| 조건 목록 | `ka10171`, WebSocket `CNSRLST` | REST `psearch-title`, `HHKST03900300` | 공식 확인 |
| 현재 결과 조회 | `ka10172`, `search_type=0`, 연속조회 지원 | REST `psearch-result`, 조건당 최대 100건 | 공식 확인 |
| 실시간 조건 등록 | `ka10173`, `search_type=1` | 해당 WebSocket 조건 API를 공식 샘플에서 확인 못함 | 키움 확인 / KIS 미확인 |
| 편입·이탈 푸시 | 필드 `843`: `I` 삽입, `D` 삭제 | 목록·결과 REST에는 편입·이탈 이벤트 없음 | 키움 확인 / KIS 미확인 |
| 실시간 해지 | `ka10174`, `CNSRCLR` + `seq` | 조건 푸시 자체가 미확인 | 키움 확인 / KIS 미확인 |
| 모의 조건검색 | 공식 문서에 모의 WebSocket과 KRX 한정 명시 | 공식 legacy 지원표의 조건 목록·결과는 모의 제공 칸이 비어 있음 | 키움 확인 / KIS 계정 재검증 |
| 모의 시세·현금주문 | 운영·모의 키를 별도 발급하고 MOCK 예제 제공 | 모의 REST·WebSocket 도메인, 현금주문 모의 TR 제공 | 공식 확인 |
| 조건검색 시장 | `stex_tp=K`, KRX | 결과 API에 시장 인자가 없고 HTS 조건 정의에 의존 | KRX 확인 / KIS 계정 검증 |
| 즉시 매도주문 시장 | `dmst_stex_tp`: KRX, NXT, SOR | `EXCG_ID_DVSN_CD`를 주문에 전달; 공식 예제에 SOR, 정정취소에 KRX/NXT/SOR | 공식 예제 확인, 계정 검증 |
| OCO | 국내주식 OCO를 확인하지 못함 | 국내주식 OCO를 확인하지 못함 | 미확정 |
| 주문 유효기간 | 검토한 즉시주문 예제에 GTC/일자 인자 없음 | 즉시 현금주문에 기간 인자 없음; 예약주문은 별도 API | 즉시주문 기간 미확정 |

“공식 확인”은 API가 존재한다는 뜻이다. 실제 계정 권한, 모의환경 응답, 호출 한도, 같은 조건의 HTS/API 종목 집합 일치는 아직 검증하지 않았다.

## 키움은 조건 편입·이탈 푸시가 명시돼 있다

키움 조건검색은 모두 `/api/dostk/websocket`을 사용한다. `ka10171`로 저장된 조건의 `seq`와 `name`을 받고, 일반 검색 `ka10172`는 `search_type=0`, 실시간 검색 `ka10173`은 `search_type=1`과 `stex_tp=K`를 사용한다. 검토한 REST 문서는 조건식 자체를 생성·수정하는 API나 HTS 저장 절차를 설명하지 않으므로, 기존 영웅문 조건의 서버 노출 여부를 계정에서 확인한다. [공식 API 가이드](https://openapi.kiwoom.com/guide/apiguide) · [공식 조건 예제 폴더](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/main/examples/%EA%B5%AD%EB%82%B4%EC%A3%BC%EC%8B%9D/%EC%A1%B0%EA%B1%B4%EA%B2%80%EC%83%89)

실시간 응답은 `trnm=REAL`이고 `9001` 종목코드와 `843` 삽입삭제 구분을 보낸다. `I`는 조건 편입, `D`는 이탈이다. 이는 결과 API를 반복 호출하는 폴링이 아니라 연결된 WebSocket으로 받는 푸시다. [실시간 등록 예제](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/main/examples/%EA%B5%AD%EB%82%B4%EC%A3%BC%EC%8B%9D/%EC%A1%B0%EA%B1%B4%EA%B2%80%EC%83%89/request_domestic_realtime_condition_search_async.py)

종료·재시작 때는 `ka10174`에 `CNSRCLR`과 같은 `seq`를 보내 해지한다. 연결 단절을 해지 성공으로 간주하지 않고 재접속 후 등록 상태를 다시 구성해야 한다. [실시간 해지 예제](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/main/examples/%EA%B5%AD%EB%82%B4%EC%A3%BC%EC%8B%9D/%EC%A1%B0%EA%B1%B4%EA%B2%80%EC%83%89/stop_domestic_realtime_condition_search.py)

공식 문서는 운영 `wss://api.kiwoom.com:10000`, 모의 `wss://mockapi.kiwoom.com:10000`을 표시하고 모의는 KRX만 지원한다고 명시한다. 실제 저장 조건의 목록·초기 결과·편입·이탈·해지가 모의계정에서 모두 동작하는지는 한 조건으로 실행 검증한다.

매도 주문 예제 `kt10001`은 보통 지정가, 시장가, 조건부지정가, IOC/FOK, 스톱지정가 등을 열거하고 `dmst_stex_tp`에 KRX/NXT/SOR를 받는다. 목표가 도달을 기다리게 하려면 매수 체결 후 **체결된 수량만큼 보통 지정가 매도**를 제출하는 방식이 공식 예제와 가장 직접적으로 연결된다. [공식 매도 예제](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/main/examples/%EA%B5%AD%EB%82%B4%EC%A3%BC%EC%8B%9D/%EC%A3%BC%EB%AC%B8/sell_domestic_stock.py)

## 한국투자는 조건 결과 REST 조회까지 확인된다

한국투자는 eFriend Plus `[0110]`에서 조건을 등록하고 `사용자조건 서버저장`을 해야 한다. `psearch-title`이 조건 `seq`를 반환하고, 그 값을 `psearch-result`에 넘긴다. API 결과는 조건당 100건으로 제한되며 `[0110]`의 `대상변경` 설정은 API에 적용되지 않는다고 공식 예제에 적혀 있다. [목록 예제](https://github.com/koreainvestment/open-trading-api/blob/main/examples_llm/domestic_stock/psearch_title/psearch_title.py) · [결과 예제](https://github.com/koreainvestment/open-trading-api/blob/main/examples_llm/domestic_stock/psearch_result/psearch_result.py)

100건 제한에 걸리면 일부 종목이 응답에서 사라져도 진짜 조건 이탈로 단정하지 않는다. 검색 범위를 좁히거나 포화 상태로 기록하고, 불완전한 집합 비교로 신규 주문·취소를 결정하지 않는다.

두 함수는 `/uapi/domestic-stock/v1/quotations/` 아래 REST 요청이다. 2026-09-13 기준 공식 국내주식 WebSocket 통합 파일에는 체결가·호가·체결통보 구독은 있으나 `psearch` 조건 구독 함수가 없다. 그러므로 조건 결과를 짧은 간격으로 다시 요청하는 것은 **폴링**이며 편입·이탈 푸시로 부르지 않는다. [공식 REST 함수 모음](https://github.com/koreainvestment/open-trading-api/blob/main/examples_user/domestic_stock/domestic_stock_functions.py) · [공식 WebSocket 함수 모음](https://github.com/koreainvestment/open-trading-api/blob/main/examples_user/domestic_stock/domestic_stock_functions_ws.py)

공식 legacy 지원표는 종목조건검색 목록·결과, 예약주문, 매도가능수량조회에 모의 제공 표시를 하지 않고, 현금주문과 기본시세에는 모의 제공을 표시한다. 최신 서비스가 달라졌을 수 있으므로 이를 현재 미지원의 확정 증거로 쓰지 않고 모의계정 호출로 재검증한다. [공식 모의지원 표](https://github.com/koreainvestment/open-trading-api/blob/main/legacy/README.md)

KIS 조건검색이 모의 도메인에서 거절되면 운영 조건/시세 계정과 모의주문 계정을 한 인증 객체에 섞지 않는다. 운영 측은 읽기 전용 신호 이벤트만 발행하고, 별도 프로세스의 모의 주문기가 허용 목록·모의 계좌번호·모의 TR ID를 다시 검사한 뒤 주문한다. 운영 주문 키는 이 단계에서 주문기에 제공하지 않는다.

KIS 현금주문은 실전·모의 매도 TR을 구분하고 지정가 `ORD_DVSN=00`, 주문수량·단가와 거래소 ID를 받는다. 공식 통합 예제는 SOR 주문을 사용하고 정정취소 예제는 KRX/NXT/SOR를 열거한다. 시장별 실제 주문 가능 여부와 모의 차이는 계정으로 확인한다. [현금주문 예제](https://github.com/koreainvestment/open-trading-api/blob/main/examples_llm/domestic_stock/order_cash/order_cash.py) · [정정취소 예제](https://github.com/koreainvestment/open-trading-api/blob/main/examples_llm/domestic_stock/order_rvsecncl/order_rvsecncl.py)

## 목표가 매도는 예약주문과 구분한다

매수 체결 직후 목표가격 지정가를 내는 것은 장중 **즉시 일반주문**이다. 한국투자의 `order-resv`는 15:40~다음 영업일 07:30에 접수해 다음 영업일로 보내는 별도 예약주문이며, 종료일을 넣으면 미체결 수량을 최대 30일 범위에서 반복 전송한다. 목표가 주문을 오래 유지하는 수단으로 임의 대체하지 않는다. [공식 예약주문 예제](https://github.com/koreainvestment/open-trading-api/blob/main/examples_llm/domestic_stock/order_resv/order_resv.py)

검토한 즉시 주문 예제에는 GTC 같은 유효기간 인자가 없다. 따라서 주문이 다음 세션까지 유지된다고 가정하지 않고 장 마감·재시작 때 미체결 조회와 취소·재주문 정책을 명시적으로 실행한다. 실제 유효기간은 선택 증권사 계정과 주문유형별 응답으로 확인한다.

두 공식 자료에서 국내주식 OCO를 확인하지 못했다. 목표가와 손절 주문을 동시에 내고 한쪽 체결 시 다른 쪽이 증권사에서 자동 취소된다고 가정하지 않는다. OCO가 계정 검증으로 확인되기 전에는 한 개의 활성 매도 주문과 상태기계로 정정·취소를 직렬 처리한다.

부분체결 때 전체 매수 주문량으로 목표가 매도를 내리지 않는다. 새 체결 누계에서 이미 보호주문한 수량을 뺀 증가분만 제출하고, 매도 전 실제 매도가능수량을 조회한다. KIS에는 `inquire-psbl-sell` API가 있으나 공식 legacy 표에서 모의 제공이 표시되지 않아 계정 검증 대상이다. [KIS 매도가능수량 예제](https://github.com/koreainvestment/open-trading-api/blob/main/examples_llm/domestic_stock/inquire_psbl_sell/inquire_psbl_sell.py)

## 최대 20종목 실행 흐름

최대 20종목은 보유 종목 수만 세면 초과할 수 있다. `보유 종목 ∪ 미체결 매수 종목 ∪ 주문을 위해 예약한 종목`의 고유 종목 수를 원자적으로 20 이하로 유지한다. 같은 종목의 중복 편입·폴링 결과에는 조건식·종목·신호 버전으로 만든 멱등키를 사용한다.

1. vectorbt 규칙과 증권사 조건식을 같은 기준시각의 종목 집합으로 대조한다. 설명되지 않은 차이가 있으면 자동주문을 열지 않는다.
2. 키움 푸시 또는 KIS 폴링에서 새 후보를 받아 현재 보유·미체결·당일 처리 이력과 중복 제거한다.
3. 빈 슬롯을 임시 예약하고 기사 공개시각, 출처, 종목 연결 근거를 고정해 AI 뉴스검토를 실행한다.
4. AI가 실패·시간초과·근거부족이면 신규 매수를 거절한다. 자유문장만으로 승인하지 않고 버전된 판정코드와 근거 ID를 남긴다.
5. 승인 후 매수가능금액, 종목 상태, 시장, 가격·수량 단위와 최대 노출을 다시 확인하고 모의 매수를 제출한다.
6. 체결통보와 체결조회로 수량을 대사하고 체결 증가분에만 목표가 지정가 매도를 제출한다.
7. 이탈 이벤트는 기본적으로 신규 후보 자격만 제거한다. 이미 체결된 포지션을 즉시 매도할지는 단타·스윙 전략별 사전 규칙으로 정한다.
8. 장 마감과 재시작 때 조건 등록, 미체결 주문, 체결 누계, 매도가능수량, 보유 종목과 20개 슬롯을 재구성한다.

## 모의시험 통과 기준

- 키움은 목록·초기 결과·`I/D` 푸시·해지를 모의 KRX 조건 하나로 재현한다.
- KIS는 `psearch-title/result`의 모의 호출 성공 여부, 안전한 폴링 간격과 100건 제한을 실측한다.
- 두 증권사 모두 KRX/NXT/SOR별 주문 가능 범위와 조건검색 시장 범위를 섞어 기록하지 않는다.
- 부분체결, 전량·일부 취소, 거절, 연결 단절, 재시작, 장 마감을 주입해 중복 매수와 초과 매도를 0건으로 만든다.
- 목표가 주문의 실제 유효기간, 예약주문 처리, 매도가능수량 조회, OCO 지원 여부는 계정 응답이나 공식 답변을 증거로 확정한다.
- 최대 20종목 제한은 동시에 도착한 21개 후보에서도 보유·미체결·예약의 합집합이 20을 넘지 않아야 한다.
- 단타와 스윙 각각 충분한 기간의 모의 장부가 비용·슬리피지·미체결을 포함해 재현된 뒤에만 실전 전환 결정을 요청한다.
