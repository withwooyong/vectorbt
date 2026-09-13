# 국내주식 기술전략 연구·자동주문용 오픈소스 비교

이 문서는 2015-01-02 이후 PostgreSQL 국내주식 데이터로 기술전략을 연구하고, 뉴스·정치·국제정세를 종목별 보조 판단에 결합한 뒤 자동 모의투자와 실전투자로 진행할 때 **현재 vectorbt를 유지할지 다른 오픈소스로 옮길지** 답한다. 2026-09-13에 각 프로젝트의 공식 GitHub README, 라이선스, 릴리스와 최근 커밋을 확인했다.

**현재 판단은 연구 엔진으로 vectorbt를 유지하고, 주문 브로커는 아직 정하지 않는 것이다.** 주문 계층은 기존 키움 데이터·조건검색과의 연속성이 있는 키움 REST API와, 공식 예제·통합 범위가 넓은 한국투자증권 `open-trading-api`를 각각 작은 모의시험으로 비교한다. LEAN이나 NautilusTrader로 전면 전환하면 이벤트 기반 체결·실시간 운용은 강해지지만, 현재 PostgreSQL 데이터와 벡터화된 전략 비교를 다시 구현하는 비용이 크고 한국 주식·국내 증권사 연결이 완성되어 있지도 않다. 데이터 도구인 FinanceDataReader와 pykrx는 검산·보완에 유용하지만 연구 엔진이나 주문 엔진의 대체재가 아니다.

이 판단은 수익성이나 실전투자 적합성을 뜻하지 않는다. **후속 2026-09-13 14:12 KST에는 SSH·DB 연결이 정상이며 8,789,127행·5,011종목을 확인했다. 종가 0인 1,201행이 유지되고 가격 조정 계보는 미확정이다.** [현재 집계](evidence/db-current-status-2026-09-13.json) 과거 종목 이력, 기업행사, HTS 조건 일치도 게이트로 남아 있으며 도구를 바꿔도 해결되지 않는다. 뉴스·정치·국제정세 역시 별도 시점 정합 데이터와 평가 절차가 필요하다. 모의투자에서 체결·복구·중복주문·비용을 검증하기 전에는 실전 주문으로 넘어가지 않는다.

## 결론과 선택 기준

선택은 “기능이 가장 많은 프로젝트”가 아니라 현재 단계에서 해결해야 할 병목을 기준으로 한다.

| 현재 병목 | 우선 선택 | 이유 |
| --- | --- | --- |
| 많은 기술조건·파라미터의 빠른 비교 | **vectorbt 유지** | pandas/NumPy 배열과 벡터화된 포트폴리오 계산이 현재 데이터·연구 명세에 가장 직접적이다. |
| 국내주식 모의·실전 주문 | **키움 REST와 한국투자 공식 예제를 비교한 뒤 별도 어댑터 선택** | 키움은 기존 조건검색·데이터 연속성이 있고, 한국투자는 공식 예제와 통합 범위가 넓다. |
| 주문 이벤트·부분체결·재연결까지 같은 엔진에서 정밀 재현 | **LEAN 또는 NautilusTrader를 작은 시험으로 비교** | 둘 다 이벤트 기반 백테스트와 라이브 운용을 핵심으로 설계했다. |
| KRX 데이터의 독립 검산·상장폐지 목록 보조 | **FinanceDataReader/pykrx 제한 사용** | 국내 데이터 접근은 직접 지원하지만 스크래핑과 제공처 정책 변화에 민감하다. |
| 뉴스·정치·국제정세 결합 | **엔진 밖의 별도 증거 파이프라인** | 후보 중 국내 종목별 뉴스 수집·시점 보존·출처 검증·신호화를 완성형으로 제공하는 프로젝트는 확인하지 못했다. |

전환 판단은 다음 순서로 한다.

1. 연구 속도가 병목이면 vectorbt를 유지한다.
2. 모의주문 연결만 부족하면 연구 코드와 주문 코드를 분리하고 키움 REST·한국투자 어댑터를 같은 주문 계약으로 비교한다.
3. 부분체결, 주문장, 여러 실시간 피드와 장애 복구의 동일 엔진 재현이 필수가 되면 LEAN과 NautilusTrader를 시험한다.
4. 전체 전환은 동일한 고정 데이터·신호·비용으로 vectorbt 결과와 주문 장부가 일치한 뒤 결정한다.
5. GitHub 별 수는 채택 근거나 성과 증거로 쓰지 않는다. 최근 커밋과 릴리스도 유지보수 신호일 뿐 안정성·수익성 보장이 아니다.

## 후보 전체 비교

“국내주식 직접 지원”은 README나 공식 통합 목록에 KRX 또는 국내 증권사 연결이 명시된 경우만 표시했다. 범용 REST/WebSocket 확장 가능성은 직접 지원으로 세지 않았다. 최근 커밋 날짜는 기본 브랜치의 GitHub 커밋 기록을 UTC 기준으로 확인했다.

| 후보 | 연구/백테스트 강점 | 주문 강점 | 국내주식 연결 | 뉴스·대체데이터 | 라이선스 | 유지보수 신호 | 이 목적의 판단 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vectorbt OSS | 대규모 파라미터·다자산 벡터화 비교 | 라이브 브로커 계층은 핵심 범위가 아님 | PostgreSQL→pandas 어댑터 필요 | 사용자 정의 데이터 결합 필요 | Apache-2.0 + Commons Clause | v1.1.0, 2026-08-02 최근 커밋 | **연구 엔진 유지** |
| backtesting.py | 작고 명확한 이벤트형 전략 API·최적화 | 라이브 주문 기능 없음 | DataFrame 어댑터 필요 | 사용자 구현 | AGPL-3.0 | 2026-08-05 최근 커밋, GitHub Release 미사용 | 소규모 독립 교차검산용 |
| NautilusTrader | 결정론적 이벤트 기반·상세 시장 이벤트 | 백테스트와 라이브 코드 공유, 어댑터 구조 | 공식 KRX/KIS 어댑터 없음 | 사용자 정의 데이터 가능, 뉴스 완제품 아님 | LGPL-3.0-only | v2.0.0rc4 사전 릴리스, 2026-09-13 최근 커밋 | 체결 정밀도가 병목일 때 시험 |
| LEAN | 이벤트 기반 다자산·커스텀 데이터 | 라이브 브로커 플러그인 구조 | 공식 저장소에서 KRX/KIS 연결 확인 못함 | 대체데이터 구조가 가장 강함, 실제 피드 별도 | Apache-2.0 | 2026-09-11 최근 커밋, GitHub 최신 릴리스 표시는 2017년 | 종합 엔진 전환 후보 |
| vn.py | CTA·포트폴리오 백테스트와 데이터베이스 모듈 | 게이트웨이·모의계좌·실시간 운용 | 중국 중심, 공식 KIS 게이트웨이 없음 | 사용자 모듈 필요 | MIT | 4.4.0, 2026-08-06 최근 커밋 | KRX 목적에는 어댑터 비용 큼 |
| backtrader | 익숙한 이벤트형 전략·브로커 시뮬레이션 | 일부 오래된 브로커 연결 | KRX/KIS 직접 지원 없음 | 사용자 피드 필요 | GPL-3.0 | 2023-04-19 최근 커밋, GitHub Release 미사용 | 신규 기반으로 선택하지 않음 |
| FinanceDataReader / pykrx | KRX 가격·목록 검산과 보완 | 없음 | **데이터는 직접 지원** | 뉴스 기능 없음 | MIT / pyproject에 MIT | 2026-05-13 / 2026-05-04 최근 커밋 | 보조 데이터 도구 |
| 한국투자 `open-trading-api` | 예제·전략 빌더·LEAN 기반 백테스터 포함 | **국내주식 모의·실전 API 예제** | **직접 지원** | LLM 예제는 있으나 뉴스 증거 파이프라인은 아님 | 저장소 루트 라이선스 미표시 | 2026-08-26 최근 커밋, GitHub Release 미사용 | **공식 예제 범위가 넓은 우선 비교 후보** |

라이선스는 배포·서비스 방식에 영향을 줄 수 있으므로 실제 사용 전에 법률 검토가 필요하다. 특히 vectorbt OSS의 Commons Clause, backtesting.py의 AGPL, GPL/LGPL의 결합·배포 조건을 단순한 “무료 사용 가능”으로 축약하면 안 된다. 한국투자 저장소는 공개되어 있지만 루트 LICENSE나 `pyproject.toml`의 라이선스 선언을 확인하지 못했으므로 오픈소스 라이선스가 부여되었다고 단정하지 않는다.

## 전환 비용은 코드 이식보다 의미 이식이 크다

엔진을 바꾸면 이동평균 식만 다시 쓰는 것으로 끝나지 않는다. 같은 전략이라고 주장하려면 아래 의미가 보존되어야 한다.

| 이식 대상 | 확인할 차이 | 통과 증거 |
| --- | --- | --- |
| 데이터 | 시간대, 거래일, 결측·정지봉, 조정 OHLCV, 종목코드 변경 | 동일 스냅샷 해시와 행별 입력 비교 |
| 지표 | 창의 최소 기간, NaN, 현재 봉 포함, 교차의 등호 | 신호 불일치 0 또는 종목·날짜별 설명 |
| 계좌 | 현금 공유, 후보 초과 순서, 정수주, 중복 진입 | 일별 현금·수량·평가액 대사 |
| 체결 | 다음 시가, 지정가, 부분체결, 가격제한, 거래정지 | 주문·체결 이벤트 장부 대사 |
| 비용 | 수수료, 세금, 슬리피지의 적용 시점과 반올림 | 거래별 비용 분해 일치 |
| 기업행사 | 분할·병합·배당·상장폐지의 가격과 수량 처리 | 행사 전후 포지션·현금 검산 |
| 뉴스 | 공개시각, 수집지연, 종목 연결, 기사 수정 | 당시 이용 가능 입력의 재생 |

따라서 후보의 최소 시험은 같은 고정 표본을 사용한다.

- 종목: 정상 거래, 거래정지, 기업행사, 상장폐지 사례를 각각 포함한다.
- 기간: 지표 준비 구간과 주문 발생 구간을 분리한다.
- 전략: 이동평균 교차 하나와 10거래일 보유 규칙만 사용한다.
- 결과: 신호, 주문 의도, 접수, 체결, 거절, 현금, 포지션을 CSV 또는 Parquet 장부로 남긴다.
- 판정: 총수익률만 맞는 것은 실패이며, 첫 불일치 이벤트와 원인을 설명해야 한다.

현재 예상 전환 비용은 backtesting.py가 낮음, LEAN이 높음, NautilusTrader가 높음, vn.py가 높음이다. backtesting.py는 기능 범위가 작아 교차검산 이식이 쉽고, 나머지 세 엔진은 시장·브로커 모델을 제대로 구현해야 장점이 생긴다. 이 평가는 코드량의 실측치가 아니라 현재 요구와 공식 지원 범위를 비교한 해석이다.

## 깊이 검토 1: vectorbt OSS를 연구 엔진으로 유지

vectorbt OSS는 현재 목적의 첫 단계인 기술전략 연구에 가장 잘 맞는다. 공식 README는 여러 구성과 자산을 NumPy 배열에 배치해 대규모 전략 실험을 수행하고, 포트폴리오·거래·낙폭 분석을 제공한다고 설명한다. 현재 PostgreSQL 일봉을 pandas 객체로 변환하는 경로와 기존 실험 명세를 그대로 활용할 수 있다. [공식 README](https://github.com/polakowo/vectorbt/blob/master/README.md)

다만 주문 실행 플랫폼으로 보아서는 안 된다. `Portfolio` 시뮬레이션은 연구용 주문 모델이며 증권사 세션, 토큰 갱신, 주문 정정·취소, 부분체결, 재연결과 실계좌 대사를 대신하지 않는다. 뉴스·정치·국제정세도 시간축에 맞춘 사용자 데이터로 투입해야 한다.

공식 README는 현재 저장소를 VectorBT PRO의 **오픈소스 커뮤니티 에디션**이라고 명시한다. 여기서 확인한 기능은 OSS 저장소 기준이며 PRO 기능을 포함한다고 해석하지 않았다. 라이선스는 Apache 2.0에 Commons Clause가 추가되어, 주된 가치가 이 소프트웨어인 제품·서비스 판매를 제한한다. [LICENSE.md](https://github.com/polakowo/vectorbt/blob/master/LICENSE.md)

유지보수 신호는 양호하다. 공식 릴리스 페이지에서 v1.1.0이 2026-07-05 게시되었고 Python 3.14, pandas 3, NumPy 2.4+, Rust 엔진 패키징 개선을 명시한다. 기본 브랜치 최근 커밋은 2026-08-02로 확인했다. 이는 현재 호환성 신호이며 계산 정확성이나 장래 유지보수를 보장하지 않는다. [릴리스](https://github.com/polakowo/vectorbt/releases) · [커밋](https://github.com/polakowo/vectorbt/commits/master/)

전환 비용이 가장 낮은 구조는 다음과 같다.

- 연구: PostgreSQL 스냅샷 → 정규화된 pandas 입력 → vectorbt 신호·포트폴리오 결과
- 판단: 기술 신호와 시점이 고정된 뉴스 보조점수를 별도 정책에서 결합
- 주문: 승인된 목표 포지션만 선택된 키움 또는 한국투자 어댑터에 전달
- 대사: 의도한 주문, 접수, 체결, 거절, 잔고를 독립 장부로 보존

## 깊이 검토 2: 한국투자 `open-trading-api`는 우선 비교 후보

한국투자증권의 공식 저장소는 국내주식 시세·주문·잔고 예제와 REST/WebSocket 인증 흐름을 제공하고, `svr="vps"`와 `svr="prod"`로 모의·실전 환경을 구분한다. 모의와 실전 앱키를 각각 준비하도록 안내한다. 공식 예제와 통합 범위가 넓어 우선 비교할 가치가 있지만, 사용자의 브로커는 미정이며 이 조사로 한국투자증권을 선정하지 않는다. [공식 README](https://github.com/koreainvestment/open-trading-api/blob/main/README.md)

이 저장소는 완성된 거래 시스템이라기보다 지속적으로 바뀔 수 있는 샘플 코드 모음이라고 스스로 설명한다. 따라서 예제 함수를 전략 코드에서 직접 호출하지 말고 다음 계약을 가진 어댑터로 감싼다.

- 입력: 전략 버전, 신호 기준시각, 종목코드, 목표 수량·가격, 모의/실전 구분, 멱등키
- 출력: API 요청 ID, 증권사 주문번호, 접수·거절·부분체결·완전체결 상태, 원문 응답 해시
- 보호: 실전 자격증명과 모의 자격증명 분리, 기본값은 모의, 중복주문 차단, 거래일·장 상태 확인
- 복구: 재시작 후 미체결 주문과 실제 잔고를 먼저 조회하고 새 주문 생성 전 대사

README에는 전략 빌더와 Docker 기반 LEAN 백테스터도 포함되어 있다. 이는 비교 시험에는 유용하지만, 기존 vectorbt 연구를 즉시 대체해야 한다는 근거는 아니다. 동일한 `.kis.yaml` 표현 범위가 기존 전략 명세, 과거 종목 이력, 가격 조정과 뉴스 시점 규칙을 모두 담는지 먼저 확인해야 한다.

Windows에서는 Python 3.11 이상과 `uv sync` 경로를 안내하며, LEAN 백테스터에는 Docker Desktop과 Node.js가 추가로 필요하다. 주문 예제만 사용하는 경우에도 API 호출 제한, 토큰, WebSocket 재연결과 모의/실전 차이를 직접 검증해야 한다.

기본 브랜치 최근 커밋은 2026-08-26이며 GitHub Release는 사용하지 않는다. 공개 저장소에 루트 LICENSE가 없고 패키지 메타데이터에도 라이선스가 표시되지 않아, 코드 재배포·수정 배포 가능 범위는 한국투자증권에 별도 확인해야 한다. [커밋](https://github.com/koreainvestment/open-trading-api/commits/main/)

### 주문 브로커 비교에는 키움 REST 유지안도 포함한다

키움의 공식 REST API 저장소는 OAuth·REST·WebSocket 런타임, 국내주식 주문과 조건검색 예제, 운영·모의 환경을 제공한다. 기존 PostgreSQL 데이터와 영웅문 조건검색 연구가 키움 계보에 있으므로 종목코드·조건 결과·데이터 원천을 대조하기 쉽다는 장점이 있다. [공식 README](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/main/README.md) · [공식 API 가이드](https://openapi.kiwoom.com/guide/apiguide)

그러나 기존 데이터 수집 경로가 실주문 어댑터를 대신하지 않는다. 주문번호, 정정·취소, 부분체결, 재연결, 실제 잔고 대사는 한국투자 후보와 같은 격리된 계약으로 구현해야 한다. 공식 주문 예제와 API 가이드에는 모의 환경이 표시되지만, 이 전략의 주문 유형·조건검색·실시간 체결이 모의 환경에서 운영과 같은 의미로 지원되는지는 계정 기반 시험으로 확인해야 한다. [공식 주문 예제](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/main/examples/%EA%B5%AD%EB%82%B4%EC%A3%BC%EC%8B%9D/%EC%A3%BC%EB%AC%B8)

키움 공식 저장소는 2026-09-01 최근 커밋이 있고 GitHub Release를 사용하지 않는다. LICENSE는 키움 OpenAPI 이용 목적에 한정된 비독점적·양도 불가능 권한을 부여하고 수정·배포 등을 제한하므로 일반 오픈소스 라이선스로 분류하지 않는다. [LICENSE.md](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/main/LICENSE.md) · [커밋](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/commits/main/)

브로커 비교의 판정값은 기능 개수가 아니다. 동일한 모의 주문 시나리오에서 조건·종목 매핑 일치, 인증과 호출 제한, 주문 상태의 완전성, 장애 후 대사, Windows 무인 운영, 사용 조건을 평가한다. 두 후보 모두 통과하지 못하면 브로커 선정을 보류한다.

## 깊이 검토 3: LEAN은 종합 엔진 전환 후보

LEAN은 이벤트 기반 백테스트, 연구, 최적화와 라이브 운용을 하나의 플랫폼으로 제공한다. 공식 README는 대체데이터와 라이브 거래, 교체 가능한 모듈 구조를 명시하며, CLI에서 Docker 기반 `research`, `backtest`, `optimize`, `live` 작업을 지원한다. [공식 README](https://github.com/QuantConnect/Lean/blob/master/readme.md)

뉴스 결합 관점에서는 후보 중 구조가 가장 가깝다. 커스텀·대체데이터를 시간축 이벤트로 처리할 수 있어 기사 공개시각과 기술 신호의 결합을 이벤트 모델 안에 넣기 쉽다. 그러나 실제 뉴스 데이터의 수집권·과거 시점·정정·종목 매핑은 별도 문제다. QuantConnect 클라우드 데이터셋이나 서비스 기능을 LEAN 오픈소스 저장소의 내장 무료 데이터로 간주하지 않는다.

국내주식에서는 전환 비용이 크다. 공식 LEAN 저장소에서 한국 거래소 달력, 종목 속성, 가격 단위, 기업행사, 한국투자 브로커 연결을 완성형으로 확인하지 못했다. PostgreSQL 데이터를 LEAN 형식과 `Security` 모델에 연결하고, KRX 거래시간·수수료·세금·가격제한·주문 상태를 구현해야 한다. Python 전략도 실제 런타임은 C# 엔진 모델을 따른다.

Windows 설치는 공식 README의 Visual Studio 경로 또는 LEAN CLI/Docker 경로를 따른다. Docker는 재현성에 유리하지만 현재 Python 환경보다 운영 요소가 늘어난다.

라이선스는 Apache-2.0이다. 기본 브랜치는 2026-09-11까지 커밋이 확인되지만, GitHub Releases의 최신 표시는 v2.4.0.1(2017-08-08)이다. 즉 릴리스 페이지가 현재 개발 속도를 대표하지 않으므로 커밋·CI·패키지 배포를 함께 봐야 한다. [LICENSE](https://github.com/QuantConnect/Lean/blob/master/LICENSE) · [릴리스](https://github.com/QuantConnect/Lean/releases) · [커밋](https://github.com/QuantConnect/Lean/commits/master/)

LEAN 시험은 “전면 이전”이 아니라 2~3개 종목, 한 전략, 한 달 주문 장부로 제한한다. vectorbt와 신호 시점, 체결 규칙, 비용, 현금 및 포지션이 일치할 때만 확대한다.

## 깊이 검토 4: NautilusTrader는 체결·라이브 일관성 후보

NautilusTrader는 Rust 코어와 Python 제어면을 사용한 결정론적 이벤트 기반 엔진이다. 공식 README는 동일한 전략·실행 알고리즘을 백테스트와 라이브에서 사용하고, 호가·체결·봉·주문장·사용자 정의 데이터를 처리한다고 설명한다. 주문 이벤트와 장애 복구를 연구의 중심으로 옮길 때 강점이 있다. [공식 README](https://github.com/nautechsystems/nautilus_trader)

공식 통합 목록에는 여러 암호화폐 거래소와 Interactive Brokers 등이 있으나 KRX나 한국투자증권 어댑터는 확인하지 못했다. 범용 REST/WebSocket 어댑터를 만들 수 있다는 설명은 국내 주문이 바로 된다는 뜻이 아니다. KIS 어댑터를 새로 만들면 인증, 조회·주문 제한, TR 응답, 실시간 체결, 한국 종목 식별자와 거래 규칙을 모두 매핑해야 한다.

뉴스는 사용자 정의 데이터로 전달할 수 있지만, 국내 기사 수집과 사건·종목 연결 기능은 공식 README에서 완제품으로 확인하지 못했다. 뉴스 모델의 과거시점 재생, 지연, 정정도 사용자가 구현해야 한다.

Windows x86_64와 Python 3.12~3.14용 설치가 공식 표에 있고 Docker도 지원한다. Rust 코어가 있어 단순 Python 라이브러리보다 빌드·디버깅·배포 학습비용이 높다.

라이선스는 LGPL-3.0-only다. 2026-09-13 최근 커밋과 활발한 릴리스가 확인되지만, 최신 GitHub 릴리스 v2.0.0rc4는 2026-09-02의 **사전 릴리스**다. 안정 버전으로 잘못 표시하지 않는다. [LICENSE](https://github.com/nautechsystems/nautilus_trader/blob/develop/LICENSE) · [릴리스](https://github.com/nautechsystems/nautilus_trader/releases) · [커밋](https://github.com/nautechsystems/nautilus_trader/commits/develop/)

NautilusTrader는 틱·호가와 부분체결을 확보하고 “연구와 실시간 실행의 의미 차이”가 실제 병목이 된 뒤 검토한다. 현재 일봉 기술전략 비교 단계에서는 선행 투자 비용이 더 크다.

## 깊이 검토 5: backtesting.py는 작은 교차검산 도구

backtesting.py는 DataFrame OHLCV와 `Strategy` 클래스로 빠르게 단일 전략을 작성하고 최적화·시각화하기 쉽다. API가 작아 vectorbt 결과의 독립 회귀 사례를 만드는 데 유용하다. [공식 README](https://github.com/kernc/backtesting.py)

반면 대규모 다종목 공동계좌, 실시간 브로커 연결, 국내 시장 규칙, 뉴스 피드는 핵심 기능이 아니다. 현재 6개 후보를 여러 종목·기간·비용으로 비교하는 주 연구 엔진으로 옮기면 vectorbt의 배열 계산을 이벤트 루프로 다시 작성해야 한다.

Windows에서는 `pip install backtesting`으로 간단히 설치할 수 있다. 변경 이력에는 Windows 멀티프로세스 최적화 문제와 `if __name__ == '__main__'` 처리 관련 수정이 명시되어 있어 병렬 최적화 시험이 필요하다. [CHANGELOG](https://github.com/kernc/backtesting.py/blob/master/CHANGELOG.md)

라이선스는 AGPL-3.0이다. 2026-08-05 최근 커밋이 있으나 GitHub Releases는 사용하지 않고 CHANGELOG로 버전을 관리한다. 네트워크 서비스나 배포 형태에 미치는 AGPL 의무를 검토해야 한다. [LICENSE.md](https://github.com/kernc/backtesting.py/blob/master/LICENSE.md) · [커밋](https://github.com/kernc/backtesting.py/commits/master/)

권장 용도는 전체 이전이 아니라 삼성전자 등 고정 표본과 단일 전략의 진입·청산 가격을 독립 재계산하는 것이다.

## 보조 검토: vn.py

vn.py(VeighNa)는 이벤트 엔진, CTA·포트폴리오 백테스트, 실시간 게이트웨이, 로컬 모의계좌와 PostgreSQL 데이터베이스 모듈을 제공한다. Windows 11/Server 2022 이상과 Python 3.10~3.13을 안내하고 전용 Windows 배포판도 제공한다. [공식 영문 README](https://github.com/vnpy/vnpy/blob/master/README_ENG.md)

그러나 공식 게이트웨이 목록은 중국 시장과 글로벌 브로커 중심이며 KRX·한국투자증권 연결을 확인하지 못했다. 여기서 “Domestic securities”는 문맥상 중국 A주를 뜻하므로 한국 국내주식 지원으로 해석하면 안 된다. 한국어 자료와 KIS 어댑터를 직접 유지해야 하므로 현재 목적에서는 LEAN이나 NautilusTrader보다 우선할 이유가 약하다.

MIT 라이선스, 4.4.0 릴리스(2026-05-14), 2026-08-06 최근 커밋을 확인했다. 유지보수는 활발하지만 지역 생태계 불일치가 핵심 제한이다. [LICENSE](https://github.com/vnpy/vnpy/blob/master/LICENSE) · [릴리스](https://github.com/vnpy/vnpy/releases) · [커밋](https://github.com/vnpy/vnpy/commits/master/)

## 보조 검토: backtrader

backtrader는 순수 Python 이벤트 기반 백테스트, 브로커 시뮬레이션, 데이터 피드와 과거의 IB/Oanda 연결을 제공한다. 설치는 단순하지만 README의 일부 라이브 연결은 오래된 외부 패키지에 의존한다. [공식 README](https://github.com/mementum/backtrader)

GPL-3.0 라이선스이며 GitHub Releases를 사용하지 않는다. 기본 브랜치 최근 커밋은 2023-04-19로 확인되어 다른 주요 후보보다 유지보수 불확실성이 크다. 성숙도와 인기만으로 신규 자동투자 기반을 선택하기 어렵다. [LICENSE](https://github.com/mementum/backtrader/blob/master/LICENSE) · [커밋](https://github.com/mementum/backtrader/commits/master/)

현재 vectorbt 전략을 옮길 이점은 작고, 과거 backtrader 전략 자산을 재사용해야 하는 경우에만 후보로 남긴다.

## 보조 검토: FinanceDataReader와 pykrx

FinanceDataReader는 KRX 종목·지수·상장폐지·관리종목 목록과 개별 가격을 제공한다. 특히 `KRX-DELISTING`은 현재 PostgreSQL 마스터의 생존편향을 점검할 보조 자료가 될 수 있다. [공식 README](https://github.com/FinanceData/FinanceDataReader)

pykrx는 KRX와 네이버에서 주식·채권 정보를 스크래핑한다. README는 공식 데이터와 차이가 있을 수 있고 참고용으로 사용하며 제공처 약관을 준수하라고 경고한다. 2026년 KRX 로그인 정책 대응으로 `KRX_ID`와 `KRX_PW`가 필요한 기능도 있다. [공식 README](https://github.com/sharebook-kr/pykrx/blob/master/README.md)

두 도구 모두 연구·주문 엔진이 아니며 PostgreSQL 원본의 진실을 자동 보장하지 않는다. 재배포권, 호출 제한, 과거 시점의 종목 목록과 정정 이력을 별도로 확인해야 한다. 전체 백필 원천으로 무비판 채택하지 않고 오류 표본과 기업행사·상장폐지 검산에 제한한다.

FinanceDataReader는 MIT, 2026-05-13 최근 커밋이며 GitHub Release를 사용하지 않는다. pykrx는 별도 LICENSE 파일을 찾지 못했지만 `pyproject.toml`에 MIT가 선언되어 있고, v1.2.8이 2026-05-04 릴리스되었으며 같은 날 최근 커밋이 있다. [FDR LICENSE](https://github.com/FinanceData/FinanceDataReader/blob/master/LICENSE.txt) · [FDR 커밋](https://github.com/FinanceData/FinanceDataReader/commits/master/) · [pykrx pyproject](https://github.com/sharebook-kr/pykrx/blob/master/pyproject.toml) · [pykrx 릴리스](https://github.com/sharebook-kr/pykrx/releases)

## 뉴스·정치·국제정세 결합은 별도 검증 문제다

뉴스를 추가하면 기술전략이 자동으로 개선된다고 가정하지 않는다. 보조 판단은 기술 신호를 덮어쓰는 자유문장보다 재현 가능한 입력과 정책으로 만든다.

최소 데이터 계약은 다음과 같다.

- 기사 ID, 원출처 URL, 최초 공개시각과 수집시각, 수정시각, 언어, 제목·본문 해시
- 종목코드·기업·산업·국가·사건 연결과 각 연결의 근거 및 신뢰도
- 거래일 마감 시점에 실제로 알 수 있었던 기사 버전
- 중복·재배포 기사 묶음, 출처 등급, 정정·삭제 기록
- 모델·프롬프트·분류 버전, 입력 해시, 출력 점수와 실패 사유

정치·국제정세는 한 종목에 직접 연결되지 않는 경우가 많다. 먼저 사건→국가/산업/원자재/환율→종목의 명시적 연결표를 만들고, 연결되지 않은 사건은 억지로 종목 점수로 바꾸지 않는다. LLM 설명은 근거 추적을 돕는 보조 산출물이며 미래 수익 예측의 증거가 아니다.

평가는 기술전략 단독 기준선과 같은 체결·비용 조건에서 비교한다. 기사 공개 전 사용 금지, 장중 공개기사는 다음 실행 가능 시점부터 적용, 잠금 구간과 장애 시 `기술전략만` 또는 `신규주문 중지` 정책을 사전 고정한다. 뉴스가 빠진 날을 중립 점수로 조용히 대체하지 않고 결측으로 기록한다.

## 권장 도입 순서와 전환 게이트

첫 단계는 엔진 교체가 아니라 데이터와 연구 결과의 신뢰성 회복이다.

1. 2026-09-13 SSH 연결 시간 초과 원인을 확인하고 PostgreSQL을 다시 측정한다. 9월 12일의 0원 봉·가격 조정 계보 관측을 최신 상태로 단정하지 않는다.
2. 최신 PostgreSQL 스냅샷에서 0원 봉, 가격 조정 계보, 과거 종목 이력, 기업행사와 HTS 조건 일치 게이트를 통과한다.
3. vectorbt로 고정된 6개 기술전략의 시간 분리·비용·하루 지연 결과를 생성하고 주문 의도 장부 형식을 확정한다.
4. 키움 REST와 한국투자 어댑터를 별도 시험 프로세스로 만들고 조회 전용 → 모의 주문 → 모의 체결 대사 순서로 비교한다.
5. 뉴스 파이프라인은 기술전략 기준선을 고정한 뒤 추가하고, 공개시각 기준의 OOS(out-of-sample, 표본 외) 개선을 검증한다.
6. 주문 이벤트 재현이 선택한 연구+주문 구조의 실제 병목으로 확인되면 LEAN과 NautilusTrader에 동일 최소 사례를 이식한다.
7. 장기간 모의운용에서 재시작, 네트워크 단절, 토큰 만료, 부분체결, 중복신호, 장 마감, 잔고 불일치를 주입해 복구를 검증한다.
8. 실전 전환은 브로커와 자본·손실한도·주문한도·중지 조건을 사용자가 명시적으로 확정한 뒤 별도 승인한다.

전면 전환 게이트는 세 가지다. 새 엔진이 같은 입력에서 신호·주문·현금·포지션을 설명 가능하게 재현해야 하고, KRX와 선택 브로커 어댑터의 유지 책임을 감당할 수 있어야 하며, 그 비용보다 부분체결·실시간 일관성 개선이 커야 한다. 하나라도 입증되지 않으면 vectorbt 연구와 격리된 주문 어댑터 구조를 유지한다.

## 확인 범위와 한계

확인 기준일은 2026-09-13이다. 각 공식 GitHub 저장소의 기본 브랜치 README, 라이선스 파일 또는 패키지 메타데이터, Releases, 최신 커밋을 확인했다. 날짜는 보이는 기록만 사용했고 미래 릴리스를 추정하지 않았다. 커밋 SHA·날짜, 릴리스 태그·날짜·사전 릴리스 여부, 보관 상태, 라이선스 판정과 재조회 URL은 [GitHub 근거 스냅샷](evidence/open-source-snapshot-2026-09-13.json)에 요약했다.

실제 설치, 샘플 실행, PostgreSQL 연동, 브로커 계정 연결, API 호출과 주문은 수행하지 않았다. README에 없는 비공식 플러그인과 유료·클라우드 기능은 포괄 조사하지 않았으며, “직접 지원 없음”은 확인한 공식 저장소와 통합 목록 범위의 판단이다.

유지보수 날짜는 기능 적합성의 보조 신호다. 별 수, 포크 수, 릴리스 수는 전략 성과·보안·장기 지원의 증거로 사용하지 않았다. 라이선스 설명은 기술 비교를 위한 요약이며 법률 의견이 아니다.
