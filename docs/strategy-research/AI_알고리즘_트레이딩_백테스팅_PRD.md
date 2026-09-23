# AI 알고리즘 트레이딩 백테스팅 프로젝트 PRD

> 문서 상태: Draft v1.0
>
> 작성 기준일: 2026-09-23
>
> 대상 시장: 한국 주식 일봉 기반 KOSPI·KOSDAQ Long 중심
>
> 기준 대화: 「OHLCV 지표 정리」의 브레인스토밍 순서와 결론
>
> 문서 목적: 설명 가능한 룰 기반 전략을 검증하고, AI의 추가 기여도를 분리 측정한 뒤 3개월 모의투자와 제한적 실전 전환까지 이어지는 제품·연구 요구사항을 정의한다.

## 1. 핵심 요약

이 프로젝트의 목표는 단순한 주가 예측 모델이 아니라 **AI-assisted systematic trading engine**을 만드는 것이다. OHLCV 데이터로 설명 가능한 네 가지 기준 전략을 먼저 구현하고, 시장 국면(Market Regime)에 따라 전략을 선택한 뒤 AI를 진입 필터·종목 순위·포지션 크기 보조에 단계적으로 적용한다.

개발과 검증은 다음 순서를 지켜야 한다.

```text
데이터 승인
→ OHLCV·기술지표
→ 시장 Regime·Breadth
→ 룰 기반 후보 생성
→ 현실적 체결 백테스트
→ AI 진입 필터·랭킹·사이징
→ Ablation Test
→ Walk-forward OOS 검증
→ 3개월 모의투자
→ 제한적 실전 전환
```

핵심 원칙은 다음과 같다.

1. AI가 처음부터 매수·매도를 직접 결정하지 않는다.
2. 룰 기반 전략 성과와 AI의 증분 효과를 분리한다.
3. 신호일 종가로 계산한 정보는 원칙적으로 다음 거래일 시가 이후에만 체결한다.
4. 수수료·세금·슬리피지·유동성·거래정지·가격제한·상장폐지 종목을 반영한다.
5. 데이터 계보와 가격 조정 의미가 승인되지 않으면 실제 수익률과 최종 전략 선정을 실행하지 않는다.
6. Regime은 정답 라벨이 아니라 전략 성과를 개선하는지 검증해야 하는 가설이다.
7. 최종 실전 전환은 수익률 하나가 아니라 위험·안정성·체결 괴리·운영 신뢰성을 함께 통과해야 한다.

### 1.1 범위와 한계

- v1은 일봉 OHLCV와 파생 기술지표를 사용한다.
- 기본 포지션은 Long이며, Bear 구간은 현금 비중 확대를 기본으로 한다. 공매도는 별도 데이터·대차·체결 계약이 마련될 때까지 범위 밖이다.
- 지표 임계값은 브레인스토밍에서 정한 초기값이며 최종 최적값이 아니다.
- 아래의 실전 전환 수치 중 대화에서 확정되지 않은 값은 `[제안]`으로 표시하며, 사전 등록 후 변경 이력을 남겨야 한다.
- 기존 KRX 연구 환경에 적용할 경우 2024-01-01 이후 잠금 구간은 별도 승인 전까지 학습·탐색·전략 선택에 사용하지 않는다.

## 2. 문제 정의와 목표

### 2.1 해결하려는 문제

OHLCV로부터 반복 가능하고 설명 가능한 매수·매도 조건을 만들고, 어떤 시장 환경에서 어떤 전략이 유효한지 검증하며, AI가 룰 기반 기준선보다 실제로 성과를 개선하는지 미래정보 없이 측정해야 한다.

### 2.2 제품 목표

- Trend Pullback, Breakout, Mean Reversion, Momentum 네 전략을 독립적으로 실행할 수 있다.
- 시장 지수와 전체 종목 Breadth를 이용해 Market Regime을 산출한다.
- 신호·주문·체결·포지션·현금·비용을 재현 가능한 원장으로 기록한다.
- 동일한 데이터와 설정으로 동일 결과를 재생산한다.
- Rule Only부터 AI Dynamic Position Sizing까지 단계별 기여도를 비교한다.
- Walk-forward OOS 성과를 통과한 후보만 3개월 모의투자로 승격한다.
- 모의투자 결과가 사전 정의한 게이트를 통과한 경우에만 제한적 실전 승인을 요청한다.

### 2.3 비목표

- 당일 종가를 본 뒤 동일 종가에 체결된 것으로 가정하는 백테스트
- 검증되지 않은 데이터의 결측·이상치를 임의 보정해 수익률을 산출하는 작업
- 한 번의 전체기간 최적화로 최종 전략을 선택하는 작업
- 딥러닝 모델을 먼저 도입하거나 AI의 높은 정확도만으로 실전 투입을 결정하는 작업
- 미승인 공매도, 레버리지, 파생상품, 분봉·틱 초단타

## 3. 사용자와 주요 사용 시나리오

| 사용자 | 필요 | 성공 상태 |
|---|---|---|
| 전략 연구자 | 전략·지표·Regime 가설을 비교 | 동일 조건의 실험 결과와 차이를 재현 가능 |
| ML 연구자 | 라벨·피처·모델의 증분 효과 검증 | 누수 없는 OOS 성과와 설명 가능성 확보 |
| 운영자 | 모의·실전 주문과 장애 관리 | 주문·체결·포지션 원장 일치 및 Kill Switch 작동 |
| 의사결정자 | 실전 전환 여부 판단 | 사전 정의된 게이트와 근거가 한 보고서에 표시 |

## 4. 전체 시스템 구조

```text
원천 OHLCV·종목 마스터·기업행사·거래 캘린더
                    ↓
         데이터 품질·계보 승인 게이트
                    ↓
       정규화 OHLCV / Universe Snapshot
                    ↓
     기술지표·종목 Feature·시장 Feature·Breadth
                    ↓
             Market Regime v1
                    ↓
       룰 기반 전략별 Candidate Generator
                    ↓
        AI Filter / Ranking / Sizing(선택)
                    ↓
        Risk Manager / Portfolio Allocator
                    ↓
       Order Simulator 또는 Paper Broker
                    ↓
    Signal·Order·Fill·Position·Cost Ledger
                    ↓
        평가·Ablation·Walk-forward Report
```

## 5. 데이터 요구사항과 승인 게이트

### 5.1 필수 데이터

| 데이터 | 최소 필드 | 용도 |
|---|---|---|
| 종목 일봉 | 거래일, 종목 ID, O/H/L/C, 거래량 | 신호·피처·체결 시뮬레이션 |
| 시장 지수 일봉 | 거래일, 시장 ID, O/H/L/C, 거래량 | 시장 Regime |
| 종목 마스터 이력 | 영구 ID, 종목코드, 시장, 상장·폐지일, 상태 | 생존편향 방지 |
| 기업행사 | 분할·병합·배당·권리락 등과 적용일 | 가격·수량·수익률 의미 검증 |
| 거래 캘린더 | 거래일, 휴장일, 세션 정보 | 보유기간·다음 거래일 계산 |
| 비용표 | 효력일, 수수료, 세금, 기타 비용 | 당시 기준 순성과 계산 |
| 유동성 정보 | 거래대금, 거래량, 가능 시 호가 관련 통계 | 체결 한도·슬리피지 |

### 5.2 데이터 승인 조건

`DATA_ADMITTED`는 다음 조건을 모두 충족할 때만 부여한다.

- 원천 출처, 취득 시각, 원본 파일 또는 응답 해시, 데이터셋 버전을 기록한다.
- 원시가격·수정가격의 정의, 조정계수, 기업행사 연결 관계가 확인된다.
- OHLC 관계(`Low ≤ Open/Close ≤ High`), 음수, 중복키, 결측, 비거래일을 검사한다.
- 상장폐지·거래정지·종목코드 변경을 포함한 당시 Universe를 재구성할 수 있다.
- 가격·거래량 단위와 거래량 조정 의미가 확인된다.
- 캘린더와 비용표가 평가일 기준으로 버전 관리된다.
- 이상값을 임의 삭제·전일값 대체하지 않고 원인·처리 정책·영향 종목을 기록한다.
- 입력 데이터·피처·코드·설정의 해시를 실험에 고정한다.

승인 전 허용 범위는 파서·지표·원장에 대한 합성 데이터 테스트까지다. 실제 데이터 슬롯은 `BLOCKED`, 최종 선택은 `NO_SELECTION`으로 유지한다.

### 5.3 Universe 정책

- 각 거래일 당시 거래 가능했던 보통주를 기본 Universe로 구성한다.
- ETF·ETN·스팩·우선주·리츠 포함 여부는 Universe 버전에 명시한다.
- `[제안]` 최소 상장 이력 120거래일, 최소 가격, 최소 20일 평균 거래대금을 설정하되 값은 사전 등록한다.
- 상장폐지 종목을 사후 제거하지 않는다.
- 거래정지일은 가격 전진 채움으로 정상 거래일처럼 만들지 않는다.

## 6. OHLCV 기반 지표 선정

지표는 중복을 줄이기 위해 역할별로 선정한다. 모든 rolling 지표는 현재 시점까지 공개된 데이터만 사용하며, 최소 관측 길이를 충족하지 않으면 `null`로 둔다.

| 역할 | 핵심 지표 | 용도 |
|---|---|---|
| 추세 | SMA20/60/120, EMA20/60, EMA slope | 방향·배열·눌림 판단 |
| 추세 강도 | ADX14, +DI, -DI | 추세와 횡보 구분 |
| 모멘텀 | RSI14, 1/5/20/60일 수익률, MACD histogram | 회복·과매도·랭킹 |
| 변동성 | ATR14, ATR/Close, BB Width·percentile | 손절·사이징·변동성 Regime |
| 거래량 | Volume MA20, Volume Ratio, Z-score, OBV slope | 돌파 확인·유동성 |
| 가격 위치 | BB %B, 20/60/252일 고가·저가 거리 | 돌파·평균회귀·모멘텀 |
| 캔들 | body·upper/lower shadow ratio | 선택적 확인 피처 |

### 6.1 핵심 트레이딩 지표 v1

- `volume_ratio_t = volume_t / mean(volume[t-20:t-1])`로 정의해 현재 거래량을 분모에서 제외한다.
- `atr_pct = ATR14 / Close`로 종목 간 변동성을 정규화한다.
- 모든 신고가 조건은 현재 봉을 제외한 과거 창을 기준으로 한다.
- `distance_20d_high = Close / max(High[t-20:t-1]) - 1`처럼 기준 창을 명시한다.
- 종가 기반 신호는 `t` 장 종료 후 확정되고 주문은 원칙적으로 `t+1` 시가에 제출한다.

## 7. 룰 기반 기준 전략

각 Entry와 Exit는 분리된 ID를 가지며, 전략의 성과가 진입·청산·Regime·사이징 중 어디서 발생했는지 추적해야 한다.

### 7.1 Strategy A — Trend Pullback

목적은 장기 상승 추세 종목이 EMA20 부근까지 조정된 뒤 모멘텀을 회복할 때 진입하는 것이다.

**사전 필터**

```text
Close > SMA120
SMA20 > SMA60 > SMA120
ADX14 > 20
EMA20 > EMA60
```

**진입 신호**

```text
Low <= EMA20 × 1.01
RSI14가 40~60 구간에서 전일 대비 상승
Close > Open
Volume > VolumeMA20
선택 확인: Close > PreviousHigh
```

**청산 후보**

- 초기 손절: 진입가 - 2 ATR
- 목표가: 진입가 + 4 ATR
- 추세 이탈: 종가 < EMA20
- 모멘텀 이탈: RSI가 75 초과 후 70 아래로 하락
- Time Stop: 20거래일

### 7.2 Strategy B — Breakout

목적은 상승 추세에서 거래량이 동반된 20일 고가 돌파를 추종하는 것이다.

**진입 신호**

```text
Close_t > max(High[t-20:t-1])
Volume_t / mean(Volume[t-20:t-1]) > 1.5
ADX14 > 20
55 <= RSI14 <= 75
Close > EMA20 > EMA60
```

**청산 후보**

- 초기 손절: 진입가 - 2 ATR
- ATR 목표가: 진입가 + 4 ATR
- Trailing Stop: 최고 종가 - 2.5 ATR
- 추세 이탈: 종가 < EMA20
- Time Stop: 20거래일 이내 목표 미도달

### 7.3 Strategy C — Mean Reversion

목적은 장기 하락 추세의 낙하를 추격하지 않고, 횡보 또는 장기 상승 구조 안의 단기 과매도 반등을 포착하는 것이다.

**진입 신호**

```text
RSI14 < 30
Close < Bollinger Lower Band
BB %B < 0
Volume > VolumeMA20
```

**비교할 필터 버전**

- C0: 장기 추세 필터 없음
- C1: `Close > SMA120`인 종목만 허용
- 시장 기본 조건: Sideways 또는 Weak Bull

**청산 후보**

- 종가가 Bollinger Middle 이상
- RSI14 > 50
- 진입가 - 1.5 ATR 또는 -2 ATR 손절
- `[제안]` 10거래일 Time Stop

### 7.4 Strategy D — Momentum Ranking

목적은 Universe의 상대 강도를 점수화하고 상위 종목만 보유하는 것이다.

```text
Momentum Score =
20일 수익률       25%
60일 수익률       20%
RSI14             10%
ADX14             10%
Volume Ratio      15%
EMA20 Slope       10%
52주 신고가 거리  10%
```

- 상위 10~20개를 후보로 선정한다.
- `EMA20 > EMA60`, `Close > EMA20`, `Volume Ratio > 1`일 때만 진입한다.
- `[제안]` 주 1회 또는 월 1회 리밸런싱을 독립 실험으로 비교한다.
- 점수 계산 전 피처를 횡단면 percentile 또는 robust z-score로 정규화한다.

## 8. 매수·매도·포지션 사이징

### 8.1 공통 주문 규칙

- 일봉 종가로 확정한 신호는 다음 거래일 시가 주문이 기본이다.
- 시장가 매수는 `next_open + slippage`, 매도는 `next_open - slippage`로 보수적으로 처리한다.
- 다음 날 시가가 손절가를 넘어 갭 하락하면 손절가가 아니라 실제 다음 체결 가능 가격을 사용한다.
- 한 봉에서 익절과 손절이 모두 닿고 순서를 알 수 없으면 보수적 우선순위 또는 더 낮은 주기 데이터 정책을 사전 정의한다.
- 거래정지·가격제한·거래량 부족 시 미체결 또는 부분체결을 기록한다.

### 8.2 Exit 실험 세트

| ID | 규칙 |
|---|---|
| E1 | -5% 손절 / +10% 익절 |
| E2 | -2 ATR 손절 / +4 ATR 익절 |
| E3 | 종가 EMA20 이탈 |
| E4 | 2 ATR trailing stop |
| E5 | 최고 종가 - 2.5 ATR |
| E6 | 20거래일 Time Stop |
| E7 | RSI 75 초과 후 70 하향 돌파 |
| E8 | AI Exit — v1 최종 선택 대상이 아닌 탐색 슬롯 |

### 8.3 Position Sizing

기본 수량은 손절 거리 기반으로 계산한다.

```text
risk_budget = current_equity × risk_per_trade
stop_distance = abs(entry_price - initial_stop_price)
raw_quantity = floor(risk_budget / stop_distance)
final_quantity = min(raw_quantity, 종목 한도, 유동성 한도, 현금 한도)
```

초기 비교값은 다음과 같다.

- 1회 거래 위험: 계좌의 0.5%, 0.75%, 1.0%
- 종목당 평가금액: 계좌의 최대 10%
- 동시 보유: 최대 10종목
- 동일 섹터: 최대 30%
- `[제안]` 주문 수량: 최근 20일 평균 거래량의 1% 이하
- `[제안]` Bear·High Vol에서는 위험예산을 50% 이하로 축소

모든 한도 충돌은 가장 보수적인 수량을 선택하며, 1주 미만은 주문하지 않는다.

## 9. Market Regime 정의와 OHLCV 탐지

Regime은 `방향 × 추세 강도 × 변동성`으로 구성한다. 분류 자체의 정확도가 아니라 적용 전후 OOS 성과 개선 여부로 가치가 결정된다.

### 9.1 방향·강도 5분류

| Regime | Trend Score | 주요 조건 | 기본 전략 |
|---|---:|---|---|
| Strong Bull | +4~+5 | 상승 배열, +DI 우위, 강한 ADX | Trend, Breakout, Momentum |
| Weak Bull | +2~+3 | 상승 방향이나 강도 약함 | Pullback, Momentum |
| Sideways | -1~+1 | 방향 혼재, 낮은 ADX | Mean Reversion |
| Weak Bear | -2~-3 | 하락 방향이나 강도 약함 | Long 축소·현금 |
| Strong Bear | -4~-5 | 하락 배열, -DI 우위, 강한 ADX | 현금; 공매도는 별도 범위 |

Trend Score v1은 다음 다섯 쌍을 사용한다.

```text
Close > SMA120       +1 / 반대 -1
EMA20 > EMA60        +1 / 반대 -1
EMA60 > SMA120       +1 / 반대 -1
EMA20 slope > 0      +1 / 반대 -1
+DI > -DI            +1 / 반대 -1
```

ADX 해석 초기값은 `<15 무추세`, `15~20 약함`, `20~25 형성`, `>25 강함`, `>40 매우 강함`이다.

### 9.2 변동성 3분류

현재 `ATR14 / Close`의 과거 120거래일 percentile을 사용한다.

| Volatility | Percentile |
|---|---:|
| Low | < 30 |
| Normal | 30~70 |
| High | > 70 |

BB Width percentile은 보조 검증값으로 사용한다. Sideways + Low Vol 후보는 `ADX < 20`, BB Width 120일 percentile < 30, `abs(EMA20/EMA60 - 1) < 2%`를 초기 조건으로 한다.

### 9.3 상태 안정화

- 하루 단위 전환을 줄이기 위해 `[제안]` 새 상태가 2거래일 연속 관측되어야 전환한다.
- 급락 보호 조건은 지연 없이 별도 Risk Override로 작동할 수 있다.
- 원시 점수와 최종 상태를 모두 저장해 임계값 효과를 분석한다.

### 9.4 Regime–전략 매트릭스

| 시장 Regime | Trend Pullback | Breakout | Mean Reversion | Momentum | 기본 총 위험예산 |
|---|---:|---:|---:|---:|---:|
| Strong Bull | ON | ON | 제한 | ON | 100% |
| Weak Bull | ON | 제한 | ON | ON | 75~100% |
| Sideways | OFF | OFF 또는 실험 | ON | 제한 | 50~75% |
| Weak Bear | OFF | OFF | 제한적 실험 | 상대강도만 실험 | 0~25% |
| Strong Bear | OFF | OFF | OFF | OFF | 0% |

각 ON/OFF와 위험예산 수치는 실험 파라미터이며, Regime 미적용 대조군과 반드시 비교한다.

## 10. 시장과 개별 종목의 분리

시장 Regime은 KOSPI·KOSDAQ 지수 OHLCV와 Breadth로 계산하고, 종목 추세는 각 종목 OHLCV로 별도 계산한다.

| 시장 | 종목 | 해석 |
|---|---|---|
| Bull | Bull | Long 우선 환경 |
| Bull | Bear | 종목 고유 약세 가능성; 제외 |
| Bear | Bull | 상대강도 후보이나 비중 축소 |
| Bear | Bear | Long 진입 억제 |

- KOSPI 종목에는 KOSPI Regime, KOSDAQ 종목에는 KOSDAQ Regime을 기본 연결한다.
- 전체 시장 공통 충격은 별도 `global_risk_override`로 관리할 수 있다.
- 시장 지표와 종목 지표를 같은 이름으로 덮어쓰지 않고 `market_*`, `stock_*` prefix를 사용한다.

## 11. Market Breadth

Breadth는 지수 상승이 시장 전반에 퍼졌는지 검증하는 보조 상태 변수다.

필수 값은 다음과 같다.

- 전체 거래 가능 종목 중 `Close > SMA20/60/120` 비율
- `RSI14 > 50` 비율
- 20일 신고가 종목 수와 신저가 종목 수
- `new_high_low_ratio = new_high_count / max(new_low_count, 1)`
- 상승 종목 수 / 하락 종목 수
- 선택적으로 상승 거래량 / 하락 거래량

모든 비율의 분모는 해당 날짜의 point-in-time Universe이며, 정지·결측 종목 처리 정책을 기록한다. Breadth의 증분 효과는 `지수 Regime만 사용` 대 `지수 + Breadth`로 비교한다.

## 12. 백테스트 함정과 현실적 체결 규칙

### 12.1 반드시 차단할 편향

| 위험 | 차단 요구사항 |
|---|---|
| Look-ahead bias | 피처·라벨·Universe·기업행사의 실제 가용 시점을 보존 |
| Survivorship bias | 상장폐지와 당시 상장 종목 포함 |
| Selection bias | 가설·지표·임계값·평가기간을 사전 등록 |
| Data snooping | 탐색 횟수와 전체 후보 수 기록, 잠금 구간 미열람 |
| Leakage | 라벨 종료구간과 학습 구간이 겹치지 않도록 purge·embargo |
| Corporate-action error | 가격·수량·현금흐름 조정 규칙과 기업행사 원장 연결 |
| Unrealistic fill | 주문 시점, 갭, 가격제한, 부분체결, 유동성 한도 반영 |

### 12.2 비용과 체결 모델

- 매수·매도 수수료와 매도세 등은 효력일 기준으로 적용한다.
- 슬리피지는 최소 `0, 5, 10, 20 bps` 민감도 분석을 제공하되 0 bps는 운영 판단에 사용하지 않는다.
- `[제안]` 기본 체결가격은 다음 시가에 방향별 슬리피지를 더한 값이다.
- 체결 수량은 가용 현금, 목표 수량, 유동성 참여 한도 중 최소값이다.
- 미체결 주문의 유지·취소 규칙을 명시하며 기본은 당일 취소다.
- 동일 봉 내 TP·SL 충돌은 보수적 순서로 처리하고 충돌 횟수를 보고한다.
- 배당을 수익에 포함할 경우 배당락·지급일·세후 현금흐름 정책을 명시한다.

### 12.3 재현성

각 실행은 다음을 저장한다.

- experiment ID, run ID, 생성 시각
- 코드 commit/hash, 환경·라이브러리 lock hash
- 데이터셋·Universe·피처·비용·전략 config hash
- 난수 seed와 모델 artifact hash
- signal/order/fill/position/cash/cost ledger
- 실패 상태와 traceback, 재시도 번호

## 13. 평가 지표

### 13.1 포트폴리오 지표

- 총수익률, CAGR, 월·연도별 수익률
- MDD, 회복기간, Calmar
- Sharpe, Sortino, 하방편차
- 변동성, 시장 Beta, 선택적으로 Alpha
- Turnover, Exposure, 현금 비중, 평균 보유기간

### 13.2 거래 지표

- 거래 수, 승률, 평균 이익·손실, Payoff Ratio
- Profit Factor, 거래당 Expectancy
- 최대 연속 손실, 손익 분포, tail loss
- 전략·Regime·시장·연도·섹터별 기여도

### 13.3 실행 품질 지표

- 신호 대비 주문·체결 비율
- 예상 체결가 대비 실제 체결가의 bps 괴리
- 미체결·부분체결·가격제한·정지 건수
- 모의투자와 백테스트의 포지션·현금 원장 불일치 건수

### 13.4 ML 지표

- ROC-AUC보다 PR-AUC, Precision@K, Recall@K, Brier Score, calibration curve를 우선한다.
- 확률 구간별 실제 barrier 성공률을 보고한다.
- 최종 판단은 분류 정확도가 아니라 비용 차감 후 포트폴리오 OOS 성과로 한다.

## 14. AI 적용 단계

AI는 룰 기반 Candidate Generator 뒤에서 단계적으로 적용한다.

1. **Rule Only**: AI 없는 기준선
2. **+ Market Regime**: 전략 ON/OFF·위험예산
3. **+ AI Entry Filter**: 거래 성공 확률이 임계값 이상인 후보만 통과
4. **+ AI Ranking**: 예상 효용 또는 상승 확률로 후보 우선순위 결정
5. **+ Dynamic Position Sizing**: 확률·불확실성·상관관계를 반영하되 하드 리스크 한도 유지
6. **AI Exit**: 별도 연구 트랙으로 두며 v1 운영 후보 선정에는 사용하지 않음

모델은 하드 리스크 제한, Universe, 체결 가능성, Regime OFF를 우회할 수 없다.

## 15. Triple Barrier 유사 라벨링

### 15.1 기본 정의

Candidate가 발생한 시점의 실제 예정 체결가를 기준으로 한다.

```text
상단 barrier: +5%
하단 barrier: -3%
수직 barrier: 10거래일

상단에 먼저 도달 → 1
하단에 먼저 도달 → 0
둘 다 미도달 → Neutral
```

### 15.2 필수 규칙

- barrier는 raw signal close가 아니라 체결 모델이 산출한 entry price 기준이다.
- 갭으로 barrier를 넘은 경우 barrier 가격이 아니라 관측 가능한 체결가격을 기록한다.
- 동일 일봉에 상·하단이 모두 닿으면 순서를 알 수 없으므로 `ambiguous`로 분리하거나 보수적으로 0 처리한다.
- Neutral은 제거, 별도 클래스, 수익률 회귀 중 어떤 정책인지 실험 ID에 명시한다.
- 학습 샘플의 미래 10일 구간이 검증 샘플과 겹치면 purge하고 fold 사이에 embargo를 둔다.
- +5/-3/10은 초기 가설이며 ATR 기반 동적 barrier와 별도 실험으로 비교한다.

## 16. 모델 후보와 학습 요구사항

### 16.1 모델 순서

| 단계 | 모델 | 목적 |
|---|---|---|
| M0 | Logistic Regression | 선형·해석 가능한 기준선 |
| M1 | Random Forest | 비선형 기준선 |
| M2 | LightGBM 또는 XGBoost | 표형 OHLCV 주력 후보 |
| M3 | LSTM, TCN | 시계열 순서 모델 비교 |
| M4 | Transformer, PatchTST, TFT | M2를 안정적으로 이길 근거가 있을 때만 |

### 16.2 피처 후보

초기 30~50개로 제한하며 다음 그룹을 포함한다.

- return_1/5/20/60
- ema20_distance, ema20_ema60_ratio, ema20_slope
- rsi14, rsi_delta, macd_hist, macd_hist_slope
- adx, plus_di, minus_di
- atr_pct, bb_width, bb_percent_b
- volume_ratio, volume_zscore, obv_slope
- distance_20d_high/low, distance_252d_high
- body_ratio, upper_shadow_ratio, lower_shadow_ratio
- market regime score, volatility regime, Breadth
- 시장 대비 20/60일 상대수익률

### 16.3 학습 제약

- 전처리·결측 처리·스케일링은 각 학습 fold에서만 fit한다.
- 종목 ID 자체에 과도하게 의존하지 않도록 unseen-period 및 선택적으로 unseen-symbol 검증을 둔다.
- class weight·sampling은 학습 구간에만 적용한다.
- threshold는 validation 구간에서 포트폴리오 효용 기준으로 선택하고 test/OOS에서 고정한다.
- SHAP 또는 계수·permutation importance로 주요 피처와 방향을 보고한다.

## 17. Ablation Test

AI가 아니라 어떤 구성요소가 성과를 만들었는지 밝히는 것이 목적이다.

| 단계 | 구성 | 비교 질문 |
|---|---|---|
| A0 | Buy & Hold 또는 현금 포함 단순 벤치마크 | 전략이 시장 대비 가치가 있는가 |
| A1 | Rule Only | 룰 자체의 성과는 무엇인가 |
| A2 | A1 + Market Regime | Regime이 OOS 위험조정 성과를 개선하는가 |
| A3 | A2 + Breadth | Breadth가 지수 Regime에 증분 가치가 있는가 |
| A4 | A3 + AI Entry Filter | AI 필터가 거래 품질을 높이는가 |
| A5 | A4 + AI Ranking | 제한된 슬롯에서 AI 순위가 유효한가 |
| A6 | A5 + Dynamic Sizing | 성과 개선이 과도한 위험 확대가 아닌가 |

모든 단계는 동일한 Universe·기간·체결·비용·Exit를 사용한다. 한 번에 하나의 축만 변경하며, 거래 수 감소로 인한 착시를 함께 보고한다.

## 18. Walk-forward 검증

### 18.1 기본 방식

`[제안]` 최소 구조는 다음과 같다.

```text
Train 3년 → Validation 1년 → Test 6개월
6개월씩 전진하며 반복
```

데이터 길이에 따라 창은 조정할 수 있으나 사전 등록 후 고정한다. 각 fold에서 피처 처리, 모델 학습, hyperparameter 선택, threshold 결정까지 새로 수행한다.

### 18.2 검증 요구사항

- Purged time-series split과 label horizon 이상의 embargo 적용
- Bull/Sideways/Bear와 Low/Normal/High Vol 구간 포함 여부 표시
- fold별 성과와 통합 OOS 성과를 모두 보고
- 특정 1개 fold가 총성과의 대부분을 차지하는지 확인
- 비용·슬리피지 2배, 진입 1일 지연, 임계값 근방 변화에 대한 스트레스 테스트
- 모델·전략 선택 후 최종 잠금 구간은 단 한 번만 평가
- 잠금 구간 열람 사실과 승인자를 감사 로그에 기록

## 19. 실험 매트릭스

무제한 grid search를 금지하고 단계별 후보 수를 제한한다.

### 19.1 v1 필수 매트릭스

| 축 | 값 |
|---|---|
| Entry | Trend Pullback, Breakout, Mean Reversion C0/C1, Momentum |
| Exit | E1~E7; E8은 별도 탐색 |
| Regime | OFF, Index Only, Index + Breadth |
| Position Risk | 0.5%, 0.75%, 1.0% |
| Slippage | 5, 10, 20 bps |
| AI | None, Logistic, RF, LightGBM/XGBoost |
| Barrier | 고정 +5/-3/10, ATR 기반 후보 |
| Validation | Walk-forward folds, 최종 locked holdout |

### 19.2 실행 순서와 후보 축소

1. Rule Only에서 Entry × Exit를 검증한다.
2. 각 Entry별 사전 정의 기준을 통과한 Exit 최대 2개만 Regime 실험으로 승격한다.
3. Regime 실험 통과 후보만 Breadth와 AI 실험으로 승격한다.
4. AI 모델은 M0→M1→M2 순으로 기준선을 이길 때만 다음 단계로 간다.
5. 실험 총수, 탈락 이유, 변경된 가설을 registry에 남긴다.

## 20. 3개월 모의투자

### 20.1 시작 조건

- 데이터와 체결 계약이 `DATA_ADMITTED` 상태다.
- 최종 전략·모델·threshold·비용·Universe가 동결됐다.
- Walk-forward OOS와 스트레스 테스트가 승인됐다.
- 주문 전 점검, 중복주문 방지, Kill Switch, 재시작 복구가 테스트됐다.
- 백테스트 원장과 모의주문 원장을 같은 계산기로 대조할 수 있다.

### 20.2 운영 방식

- 최소 3개월 또는 `[제안]` 60거래일 중 더 긴 기간을 관찰한다.
- 전략 신호가 적다면 최소 거래 수 조건을 함께 적용하고 기간 연장을 허용한다.
- 매일 데이터 완결성, 신호, 주문, 체결, 포지션, 현금, 비용을 대사한다.
- 매주 예상 대비 체결 괴리와 장애를 검토하고, 매월 성과·리스크·Regime별 결과를 보고한다.
- 모델·전략·threshold 변경은 원칙적으로 금지한다. 치명적 결함 수정 시 새 모의투자 버전과 관찰 기간을 시작한다.

### 20.3 모의투자 합격 기준 `[제안]`

- 중대 원장 불일치 0건, 미해결 주문 장애 0건
- 실제 주문 가능 시점 위반 0건
- 실현 MDD가 사전 한도의 100% 이하
- 체결가 괴리 중앙값과 95 percentile이 사전 설정 범위 이내
- 비용 차감 Expectancy와 Profit Factor가 양수·1 초과이며 신뢰구간을 함께 제시
- 백테스트 기대범위 대비 실현 성과가 통계적·운영상 허용 범위 내
- 특정 한 종목 또는 한 거래가 전체 이익의 과도한 비중을 차지하지 않음

단, 3개월은 통계적으로 짧을 수 있으므로 통과가 곧 수익성 확정은 아니다. 거래 수와 Regime 커버리지가 부족하면 기간을 연장한다.

## 21. 실전 전환 게이트

실전 승인은 아래 모든 게이트를 통과한 뒤 사람이 결정한다.

| Gate | 조건 |
|---|---|
| G0 데이터 | 계보·조정·Universe·캘린더·비용·버전 승인 |
| G1 구현 | 단위·통합·합성 원장 재생 테스트 통과 |
| G2 연구 | 룰 기준선·Ablation·Walk-forward OOS 통과 |
| G3 견고성 | 비용·지연·파라미터·Regime 스트레스 통과 |
| G4 모의투자 | 3개월과 최소 거래 수·운영 기준 통과 |
| G5 운영 | 모니터링·알림·Kill Switch·복구 훈련 통과 |
| G6 승인 | 전략·리스크·운영 책임자의 명시적 승인 |

실전은 `[제안]` 총자본의 5~10% 또는 모의계좌의 10% 이하로 시작하고, 일일 손실·누적 손실·체결 괴리·데이터 지연 한도를 넘으면 자동 중단한다. 증액은 고정된 평가 주기와 동일 게이트 재검토를 거쳐야 한다.

## 22. 기능 요구사항

| ID | 요구사항 | 우선순위 |
|---|---|---:|
| FR-001 | 버전이 있는 OHLCV·시장지수·Universe·기업행사를 적재한다. | Must |
| FR-002 | 데이터 품질·계보 검사와 승인 상태를 출력한다. | Must |
| FR-003 | 기술지표를 미래정보 없이 계산한다. | Must |
| FR-004 | 시장과 종목 피처를 분리해 생성한다. | Must |
| FR-005 | Regime 방향·강도·변동성·Breadth를 산출한다. | Must |
| FR-006 | 네 기준 전략의 Entry를 독립 모듈로 실행한다. | Must |
| FR-007 | E1~E7 Exit를 Entry와 독립 조합한다. | Must |
| FR-008 | ATR 위험 기반 사이징과 포트폴리오 한도를 적용한다. | Must |
| FR-009 | 다음 시가, 갭, 비용, 슬리피지, 부분·미체결을 시뮬레이션한다. | Must |
| FR-010 | 신호·주문·체결·현금·포지션 원장을 저장한다. | Must |
| FR-011 | Triple Barrier 유사 라벨을 생성한다. | Must |
| FR-012 | 시간순 ML 학습·추론 pipeline을 실행한다. | Must |
| FR-013 | Ablation과 Walk-forward 보고서를 생성한다. | Must |
| FR-014 | 실험 registry와 artifact hash를 관리한다. | Must |
| FR-015 | 모의 브로커 주문·체결·대사를 지원한다. | Must |
| FR-016 | 리스크 한도와 Kill Switch를 제공한다. | Must |
| FR-017 | 전략·Regime·기간·종목별 성과를 조회한다. | Should |
| FR-018 | 모델 설명과 확률 calibration을 보고한다. | Should |

## 23. 비기능 요구사항

| ID | 요구사항 |
|---|---|
| NFR-001 재현성 | 동일 입력·코드·설정·seed 실행의 핵심 ledger와 지표가 동일해야 한다. |
| NFR-002 감사성 | 모든 성과 값에서 원천 데이터 버전과 체결 행까지 추적할 수 있어야 한다. |
| NFR-003 성능 | `[제안]` 전체 Universe 10년 일봉 기준 단일 룰 백테스트를 개발 환경에서 10분 이내 수행한다. |
| NFR-004 신뢰성 | 중단 후 중복 주문 없이 재개하고 마지막 확정 원장 상태를 복구한다. |
| NFR-005 보안 | API Key와 계좌정보를 코드·로그·artifact에 저장하지 않는다. |
| NFR-006 관측성 | 데이터 지연, 신호 수, 주문·체결 실패, PnL, 노출, 한도 위반을 모니터링한다. |
| NFR-007 테스트성 | 지표·신호·체결·비용·원장에 결정론적 fixture와 경계값 테스트를 둔다. |
| NFR-008 변경관리 | 전략·데이터·모델 변경은 새 버전과 새 experiment ID를 요구한다. |
| NFR-009 실패 안전 | 데이터 이상·시간 역전·원장 불일치 시 신규 주문을 차단한다. |

## 24. 논리 데이터 스키마

### 24.1 `price_bar_daily`

| 필드 | 형식 | 설명 |
|---|---|---|
| trade_date | date | 거래일 |
| instrument_id | string | 영구 종목 ID |
| market | enum | KOSPI/KOSDAQ 등 |
| open/high/low/close | decimal | 가격 |
| volume | decimal | 거래량 |
| value | decimal nullable | 거래대금 |
| price_type | enum | raw/adjusted |
| adjustment_factor | decimal nullable | 조정계수 |
| source_id | string | 원천·응답 참조 |
| dataset_version | string | 데이터셋 버전 |
| available_at | timestamp | 시스템이 알 수 있었던 시점 |

기본키: `(trade_date, instrument_id, price_type, dataset_version)`

### 24.2 `instrument_master_history`

`instrument_id`, `ticker`, `name`, `market`, `security_type`, `effective_from/to`, `listed_date`, `delisted_date`, `trade_status`, `source_id`를 가진다.

### 24.3 `corporate_action`

`action_id`, `instrument_id`, `action_type`, `ex_date`, `record_date`, `pay_date`, `price_factor`, `quantity_factor`, `cash_amount`, `source_id`, `evidence_status`를 가진다.

### 24.4 `feature_snapshot`

`asof_date`, `instrument_id`, `feature_set_version`, `available_at`, 지표 값, `input_hash`를 가진다. 시장 피처는 `instrument_id` 대신 `market_id`를 사용하거나 별도 테이블로 분리한다.

### 24.5 `market_regime`

`asof_date`, `market_id`, `trend_score`, `direction_regime`, `volatility_regime`, `breadth_version`, `raw_state`, `effective_state`, `config_hash`를 가진다.

### 24.6 `experiment_run`

`experiment_id`, `run_id`, `hypothesis`, `strategy_version`, `model_version`, `data_version`, `universe_version`, `cost_version`, `code_hash`, `config_hash`, `seed`, `fold_id`, `status`, `blocked_reason`, `started_at`, `finished_at`을 가진다.

### 24.7 거래 원장

- `signal`: signal_id, asof timestamp, strategy, side, score, reason, feature hash
- `order`: order_id, signal_id, submit timestamp, type, limit, quantity, status
- `fill`: fill_id, order_id, timestamp, price, quantity, fee, tax, slippage
- `position_snapshot`: timestamp, instrument, quantity, average cost, market value, unrealized PnL
- `cash_ledger`: timestamp, event type, amount, balance, related fill/action

모든 행은 run ID와 paper/live 환경을 명시한다.

### 24.8 `ml_label`

`sample_id`, `signal_id`, `entry_time`, `entry_price`, `upper/lower/vertical_barrier`, `first_touch`, `label`, `realized_return`, `ambiguous`, `label_config_hash`를 가진다.

## 25. 개발 단계와 Acceptance Criteria

### Phase 0 — 가설·계약·데이터 승인

**산출물:** strategy spec, data contract, cost contract, experiment registry, 잠금 정책

**Acceptance Criteria**

- [ ] 네 전략의 Entry·Exit가 수식과 시점으로 모호함 없이 정의된다.
- [ ] 모든 rolling window가 현재 봉 포함 여부를 명시한다.
- [ ] 데이터 출처·해시·가격 의미·Universe·기업행사·캘린더·비용이 검증된다.
- [ ] 미충족 항목이 있으면 실제 수익률 실행이 `BLOCKED` 된다.
- [ ] 평가기간·잠금 구간·실험 후보 수가 사전 등록된다.

### Phase 1 — 지표·Regime·Breadth 엔진

**Acceptance Criteria**

- [ ] 고정 fixture에서 SMA/EMA/RSI/ADX/ATR/BB/Volume Ratio가 독립 계산과 일치한다.
- [ ] 첫 20/60/120일 warm-up에서 잘못된 값이 생성되지 않는다.
- [ ] 시장 피처와 종목 피처가 분리된다.
- [ ] Regime Score 경계값과 상태 안정화 테스트가 통과한다.
- [ ] Breadth 분모가 point-in-time Universe와 일치한다.

### Phase 2 — 룰 전략·포트폴리오 백테스터

**Acceptance Criteria**

- [ ] 네 Entry와 E1~E7을 독립 조합할 수 있다.
- [ ] 종가 신호가 같은 종가에 체결되지 않는다.
- [ ] 갭, 동일 봉 TP/SL 충돌, 정지, 가격제한, 부분체결 fixture가 통과한다.
- [ ] 사이징이 위험·종목·섹터·현금·유동성 한도를 모두 지킨다.
- [ ] 거래 원장을 독립 재생한 현금·포지션·PnL이 엔진 결과와 일치한다.
- [ ] 비용 0이 아닌 기본 시나리오가 모든 운영 보고서에 포함된다.

### Phase 3 — 기준선·Regime Ablation

**Acceptance Criteria**

- [ ] A0~A3 결과가 동일 데이터·비용·기간으로 비교된다.
- [ ] 전략별 전체기간과 Regime별 성과가 표시된다.
- [ ] Regime 적용 전후 CAGR, MDD, Sharpe, 거래 수, Exposure 차이를 보고한다.
- [ ] 성과가 특정 종목·연도·Regime 한 곳에 집중되는지 표시한다.
- [ ] 통과하지 못한 후보는 이유와 함께 registry에서 종료된다.

### Phase 4 — 라벨·AI 모델

**Acceptance Criteria**

- [ ] +5/-3/10 라벨의 first-touch와 ambiguous 처리가 fixture로 검증된다.
- [ ] purge·embargo 후 학습/검증 샘플의 label horizon이 겹치지 않는다.
- [ ] Logistic 기준선부터 순서대로 비교한다.
- [ ] Calibration, Precision@K, feature importance, 비용 차감 포트폴리오 성과를 보고한다.
- [ ] AI 적용 단계가 Rule Only보다 나빠지면 다음 복잡도 모델로 자동 승격하지 않는다.

### Phase 5 — Walk-forward·최종 선택

**Acceptance Criteria**

- [ ] 모든 fold가 독립 전처리·학습·threshold 선택을 수행한다.
- [ ] fold별 및 통합 OOS 지표가 생성된다.
- [ ] 비용 2배·진입 지연·파라미터 변화 스트레스 결과가 허용 범위 내다.
- [ ] 최종 잠금 구간은 승인 후 1회만 열리고 접근 로그가 남는다.
- [ ] 최종 후보가 없을 수 있으며 그 경우 `NO_SELECTION`으로 종료한다.

### Phase 6 — 3개월 모의투자

**Acceptance Criteria**

- [ ] 동결된 전략·모델·설정만 실행된다.
- [ ] 매일 주문·체결·포지션·현금 대사가 완료된다.
- [ ] 중복 주문, 미래정보 사용, 중대 원장 불일치가 0건이다.
- [ ] 사전 정의한 MDD·슬리피지·장애·기대값 기준을 통과한다.
- [ ] 표본·Regime 커버리지가 부족하면 합격 대신 관찰 기간을 연장한다.

### Phase 7 — 제한적 실전과 증액

**Acceptance Criteria**

- [ ] G0~G6 승인 기록이 존재한다.
- [ ] Kill Switch와 장애 복구 훈련이 완료된다.
- [ ] 초기 자본 한도와 일·누적 손실 한도가 시스템에 강제된다.
- [ ] 모의 대비 실전 체결 괴리와 성과를 일·주 단위로 감시한다.
- [ ] 한도 위반 또는 데이터 이상 시 신규 주문이 자동 중지된다.

## 26. 테스트 요구사항

- 지표: 짧은 history, 상수 가격, 0 거래량, 급등락, 결측 경계
- 전략: 임계값 바로 아래·같음·바로 위
- 체결: 갭, 가격제한, 정지, 부분체결, 현금 부족, 동시 TP/SL
- 회계: 매수·매도·세금·수수료·분할·배당 후 원장 보존
- ML: 시간 역전, scaler 누수, label overlap, threshold 고정 여부
- 복구: 프로세스 중단·재실행 시 주문 idempotency
- Property test: 보유 수량·현금 음수 금지, 원장 합계 보존, 미래 timestamp 참조 금지

## 27. 리스크와 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| 데이터 의미 불명 | 허위 수익률 | 승인 전 수익률 차단, 원본·해시·기업행사 연결 |
| 과최적화 | OOS 붕괴 | 후보 제한, 사전 등록, Walk-forward, 잠금 구간 |
| Regime whipsaw | 잦은 전환·비용 증가 | 점수화, 지속 조건, 미적용 대조군 |
| 낮은 유동성 | 체결 불가 | 거래대금 필터, 참여율 한도, 슬리피지 스트레스 |
| 짧은 모의기간 | 잘못된 확신 | 최소 거래 수·Regime 커버리지, 필요 시 연장 |
| AI 복잡도 | 설명·재현 어려움 | 선형→트리→딥러닝 순서, Ablation과 해석 보고 |
| 운영 장애 | 중복주문·손실 | idempotency, 대사, Kill Switch, 장애 훈련 |

## 28. 미확정 의사결정

아래 항목은 구현 전에 결정하고 버전으로 고정해야 한다.

1. 정확한 Universe와 유동성·가격 필터
2. 데이터 공급원, raw/adjusted 가격 정책, 배당 포함 여부
3. 수수료·세금·슬리피지·가격제한·부분체결 상세 모델
4. Regime 상태 지속일과 Risk Override
5. Momentum 리밸런싱 주기와 보유 종목 수
6. Triple Barrier의 Neutral·ambiguous 처리
7. Walk-forward 창 길이와 최종 잠금 기간
8. 모의·실전 MDD, 슬리피지, 장애, 최소 거래 수 기준
9. 실전 초기 자본, 일일·누적 손실, 증액 규칙

## 29. Definition of Done

프로젝트 v1은 다음 상태에서 완료된다.

- 데이터가 승인되고 네 룰 기반 전략이 현실적 체결 계약으로 재현된다.
- Regime과 Breadth의 증분 효과가 OOS에서 측정된다.
- AI Filter·Ranking·Sizing의 기여가 Ablation으로 분리된다.
- Walk-forward와 잠금 평가에서 승인된 후보가 존재하거나, 후보 없음이 정직하게 기록된다.
- 3개월 모의투자에서 성과·체결·운영 게이트를 통과한다.
- 제한적 실전의 리스크 한도, 모니터링, Kill Switch, 승인 책임이 준비된다.
- 어떤 단계에서도 데이터 또는 성능 게이트가 실패하면 실전 투입 대신 `BLOCKED` 또는 `NO_SELECTION`으로 종료할 수 있다.
