# 가격 오류의 로컬 생성 경로와 원문 계보 판정

이 문서는 2015~2023 가격 감사에서 발견한 `KIWOOM 102950`의 종가 0과 `KRX` 라벨 행의 OHLC 역전이 어느 코드 경계에서 생기거나 통과했는지 판정한다. **현재 확인한 KRX 라벨 수정주가 코드 경로는 pykrx 1.2.8을 거쳐 Naver 차트 XML로 이어지며, 로컬 정수 변환은 1~2원 역전을 만들지 않는다. 매퍼는 OHLC 관계를 검사하지 않아 들어온 역전과 OHL 0을 저장할 수 있다.** 키움 0/1 가격도 현재 파서가 그대로 보존하지만, 두 경로 모두 당시 원문과 실행 manifest가 없어 과거 오류 전체가 같은 소스·코드에서 왔다고 확정할 수 없다.

범위는 현재·감사 시점 코드, 로컬/서버 설치 라이브러리 소스, 2015~2023 고정 표본, Git 실행 기록이다. 네트워크 재수집·DB 쓰기·2024년 이후 가격·전략 성과는 조사하지 않았다. 새 조회는 과거 응답의 대체물이 아니며, 아래 원인 판정은 보관된 원문이 있는 경우에만 확정 단계로 올릴 수 있다. 구조화 근거는 [price-code-evidence.json](price-code-evidence.json)에 있다.

## 핵심 판정

| 질문 | 판정 | 근거와 의미 |
| --- | --- | --- |
| `data_vendor='KRX'`는 실제 OHLCV 상류가 KRX라는 뜻인가 | **아니다** | 현재 애플리케이션은 pykrx 공개 함수를 `adjusted=True`로 호출하고, pykrx 1.2.8은 이 분기를 Naver 차트로 보낸다. 이 값은 적재 경로 라벨이다. |
| 현재 확인한 변환 경로가 `032980`의 고가 10,428·종가 10,430 역전을 만들 수 있나 | **현재 확인한 경로에서는 아니다** | Naver XML 파서는 여섯 필드를 `np.int64`로 바꾸고, 일봉 재표본화는 no-op이며, 애플리케이션은 다시 `int()`만 한다. 정수 10,428과 10,430의 순서는 보존된다. |
| KRX 라벨 이상 행이 왜 저장됐나 | **코드상 확정** | 매퍼는 `close_price <= 0`만 건너뛴다. `high < close`, `open/high/low == 0`, 양수 거래량 관계를 검사하지 않고 저장소도 날짜 sentinel 외에는 검증하지 않는다. |
| KRX OHL 0은 NaN→0 변환 때문인가 | **현재 원문 부재로 미확정** | 클라이언트에는 NaN을 0으로 바꾸는 경로가 있지만, pykrx의 Naver 일봉 파서는 XML 문자열을 바로 `np.int64`로 바꾼다. 성공적으로 반환된 현재 경로에서는 파싱 가능한 0이 이미 Naver XML 경계에 있어야 한다. 당시 XML byte가 없어 단정하지 않는다. |
| `102950`의 0/1 가격은 로컬 파서가 만들었나 | **현재 파서의 소수 절삭 가설만 배제, 상류 원인은 미확정** | 키움 파서는 `"0"→0`, `"1"→1`, `"0.4"→None`으로 처리한다. 소수를 0으로 절삭하는 코드는 없다. 다만 당시 `ka10081` 응답이 0건 보관되어 요청 응답과 DB를 직접 대조할 수 없다. |
| 당시 실행 코드를 행과 연결할 수 있나 | **불가** | 원 실행 로그는 복구했지만 실행 ID, 코드/라이브러리 해시 manifest, 원문 해시가 없다. 현재 서버 소스 일치는 당시 실행 이미지 증거가 아니다. |

## 현재 KRX 라벨 수정주가 코드 경로는 Naver로 이어진다

현재 코드 호출 순서는 다음과 같다. 경로명에 `krx`가 들어가지만 이 수정주가 OHLCV 경로의 실제 상류는 Naver다. 당시 실행 manifest가 없으므로 과거 전체 KRX 라벨 행의 원 XML 소스를 이 코드만으로 확정하지 않는다.

1. `src/backend_kiwoom/app/adapter/out/krx/client.py:148-177`이 `pykrx.stock.get_market_ohlcv_by_date(..., adjusted=True)`를 호출한다.
2. pykrx 1.2.8 `pykrx/stock/stock_api.py:195-252`는 `adjusted=True`일 때 `naver.get_market_ohlcv_by_date`로 분기한다. `adjusted=False`만 KRX 경로를 호출한다.
3. `pykrx/website/naver/core.py:4-25`는 `http://fchart.stock.naver.com/sise.nhn`에 `symbol`, `timeframe=day`, `count`, `requestType=0`을 전달한다.
4. `pykrx/website/naver/wrap.py:12-34`는 XML `item@data`를 `날짜|시가|고가|저가|종가|거래량` 순서로 나누고 DataFrame 전체를 `np.int64`로 변환한다.
5. 일봉 기본값 `freq='d'`에서는 `pykrx/stock/stock_api.py:42-56`이 재표본화하지 않는다. 앱 클라이언트의 `_int_or_zero`도 이미 정수인 값을 동일한 정수로 바꾼다.
6. `src/backend_kiwoom/app/adapter/out/krx/mapper.py:27-73`은 종가가 양수이면 OHLC 관계와 거래량을 검사하지 않고 `adjusted=True`로 만든다.
7. `src/backend_kiwoom/app/application/service/delisted_ingestion_service.py:331-366`이 이를 `data_vendor='KRX'`로 `StockPriceRepository.upsert_many`에 넘긴다. 저장소 `stock_price.py:55-137`은 날짜 sentinel만 제외하고 가격을 그대로 upsert한다.

서버와 로컬의 설치 pykrx 핵심 파일 SHA-256은 일치한다. `stock_api.py`는 `4c1523da5302ad79bb0c6d9d098a5b4e03af6744df484a0c508f71167d560c01`, `naver/wrap.py`는 `67501e8ca4ff4314dbb6f6bcf5ba2217a6da6eee146e70fbdbddfa26c11268dd`, `naver/core.py`는 `2f33e37e44f1de93e07b90ccc0586f693fcf16612ee9d281d47e65edc20f9357`다. 잠금 파일은 pykrx 1.2.8 wheel 해시 `e6d6e206d81575fedfa6a6bcea2d3843ea880f24bc79c1059121829975a9bd70`을 고정한다.

앱 핵심 파일도 서버의 LF byte 해시와 로컬 파일을 LF로 정규화한 해시가 일치한다. `client.py`는 `3b711de2...`, `mapper.py`는 `74bc038c...`, `chart.py`는 `9050c4a9...`, `backfill_delisted.py`는 `25fdac54...`다. 로컬 Git HEAD와 서버 저장소 HEAD는 모두 `771936bfd47099647e1ad9410576d6f4043c5b8f`였으나, 실행 중 컨테이너 이미지와 당시 2026-09-12 실행을 이 HEAD에 연결하는 manifest는 없다.

### 고정 표본으로 확인한 값 보존

[DB 표본](evidence/samples/results.json)의 `032980` 2015-01-06 값은 O=10,066, H=10,428, L=9,958, C=10,430, V=193,371이다. Naver wrapper와 앱 변환을 같은 순서로 적용한 순수 변환 재현에서도 H=10,428, C=10,430이고 `high < close`가 그대로 참이다. 2015-02-25와 2015-03-19도 각각 H/C가 9,724/9,726, 8,700/8,702다. 동일한 정수 캐스팅은 두 값을 뒤집을 수 없다.

같은 종목의 2015-09-04 O/H/L=0, C=5,374, V=0도 종가가 양수이므로 현재 매퍼를 통과한다. 이 재현은 **저장 가능 원인**을 확정하지만, 당시 Naver가 왜 이 값을 반환했는지 또는 Naver의 수정주가 반올림 정책이 무엇인지는 확정하지 않는다. 원 XML과 공급자 조정 정의가 필요하다.

## 키움 0/1 가격은 현재 코드에서 그대로 보존된다

`src/backend_kiwoom/app/adapter/out/kiwoom/chart.py:51-97`은 `ka10081` 문자열을 `stkinfo._to_int`로 넘긴다. `stkinfo.py:428-458`은 쉼표와 부호를 제거한 뒤 Python `int`를 적용한다. 순수 변환 결과는 `"0"→0`, `"1"→1`, `"+001"→1`, `"-0"→0`, `"0.4"→None`이다. 따라서 소수 수정가격이 이 함수의 절삭 때문에 0이 됐다는 설명은 성립하지 않는다.

`chart.py:367-475`는 `adjusted=True`일 때 요청 body에 `upd_stkpc_tp="1"`을 넣는다. [DB 표본](evidence/samples/results.json)에서는 `102950`의 2,214행 전체가 같은 `fetched_at=2026-09-10 21:29:04.568666 KST`이고, 1,201개 종가 0의 마지막 날짜는 2019-11-29이며 최초 양수 종가는 2019-09-20이다. 0과 1이 양수 거래량과 교차해 나타나는 패턴은 수정 정밀도 조사 단서지만 원인 증명은 아니다.

`RawResponse` 모델은 `api_id`, 요청/응답 JSON과 해시 필드를 갖지만(`models/raw_response.py:18-34`), 현재 키움 차트 호출에서 이를 쓰는 저장 호출은 찾지 못했다. 실DB의 `api_id='ka10081'`도 0건이다. 운영 품질 코드에는 90일 뒤 원문을 hard delete하는 경로(`repositories/quality.py:192-235`)가 있어, 설령 향후 이 테이블을 연결해도 장기 백테스트 계보에는 별도 불변 보관이 필요하다.

## 실행 기록은 요약만 있고 재현 manifest는 없다

Git 커밋 `4323ac1e98d4852a9f2ed290805dc70d9e2d89bb`은 2026-09-12 22:19~09-13 01:38 KST에 `backfill_delisted.py`가 후보 535, 적재 530종목, 612,607행, 실패 0, `EXIT=0`으로 끝났다고 기록한다. 실행 계획의 `docker exec ... sh -c "... > /tmp/backfill_delisted.log"`는 컨테이너 내부 경로에 쓴다. 실제 `kiwoom-app:/tmp/backfill_delisted.log`는 79,783 byte이며 SHA-256은 `b915261fd75c63ea96dc0dba25a412d0c13647800431f538f38dc083072c4da9`, 수정 시각은 2026-09-13 01:38:34 KST다. [원 로그 전체 보존본](evidence/container-log-archive/container_backfill_log_full.stdout.txt)과 [수집 receipt](evidence/container-log-archive/receipt.json), [메타·앞뒤 요약](evidence/container-original-log/container_backfill_log.stdout.txt)을 남겼다. 최종 요약도 후보 535, 적재 530종목, 612,607행, 시세 없음·코드 충돌·상장주식수 누락·실패 모두 0으로 Git 기록과 일치한다.

이 612,607행은 전체 운영 배치의 실행 집계일 뿐 2015~2023 가격 표본 집계가 아니다. 로그의 2024년 이후 정보는 전체 배치 건수와 상폐일 메타 수준이며, 개별 가격 봉을 조회하거나 분석하지 않았다. 호스트 `/tmp` 확인에서 `NOT_FOUND`가 나온 기록은 잘못된 namespace 탐색 이력으로 보존했으며, 실제 로그 위치는 컨테이너 내부다.

CLI는 집계와 실패 목록을 stdout으로 쓰지만(`scripts/backfill_delisted.py:102-117`), 원 로그에는 실행 ID, Git commit/blob, 이미지 digest, pykrx wheel/source hash, 요청 범위별 원문 hash가 없다. 해당 manifest 키 검색도 일치 0건이었고 원 공급자 응답 payload도 없다. 현재 코드 blob은 감사 당시 로컬 `63c1e275...`, 서버 `69747e6c...`, 현재 HEAD에서 같지만 이 사실만으로 과거 실행 이미지와 행을 연결할 수 없다. 원 로그는 이번 조사에서 보존했지만 당시 만들어진 JSON receipt·manifest는 아니다.

## 수정은 원문 보존, 출처 분리, 격리 검사를 함께 해야 한다

수정 대상과 완료 조건은 다음과 같다. 기존 행을 제자리에서 고치지 않고 새 revision에 재수집·검증해야 한다.

| 수정 대상 | 필요한 변경 | 완료 조건 |
| --- | --- | --- |
| `app/adapter/out/krx/client.py` | `data_vendor`와 실제 `upstream_source`를 분리하고 `PYKRX_NAVER_ADJUSTED`를 명시한다. NaN/비유한 값을 0이 아닌 결측으로 보존한다. pykrx DataFrame API 아래에서 원 XML을 잃으므로 직접 원문 캡처 계층 또는 공급자 원문 export가 필요하다. | 요청 인자·취득 시각·pykrx 버전·상류 URL/종류·원 XML SHA-256·원 필드/dtype이 한 fetch receipt에 연결된다. |
| `app/adapter/out/krx/mapper.py` | `low <= min(open, close) <= max(open, close) <= high`, 비음수 거래량, 유한값을 검사하고 실패 행을 사유 코드와 함께 격리한다. 거래정지 표현은 일반 OHLC 봉과 분리한다. | `032980` 3개 역전 표본과 OHL 0/C 양수 표본이 정상 가격으로 upsert되지 않고 원문+사유를 가진다. |
| `app/application/service/delisted_ingestion_service.py`, `scripts/backfill_delisted.py` | 실행 ID와 immutable manifest를 만들고 코드 blob·이미지 digest·의존성 lock·입력 범위·건수·격리 건수·원문/산출물 hash를 기록한다. | 종료 코드와 receipt가 일치하고, 행 또는 배치에서 실행 manifest를 역참조할 수 있다. 이상 행이 있으면 데이터 인수는 실패한다. |
| `persistence/models/stock_price.py`, 새 migration, `repositories/stock_price.py` | `data_vendor` 하나로 출처를 표현하지 말고 실제 공급원·조정 종류·revision·ingestion_run_id를 저장한다. 저장 직전에도 OHLC 불변식을 방어한다. | `KRX`라는 라벨만으로 Naver 값을 KRX 원천으로 오인할 수 없고 기존 revision은 보존된다. |
| `kiwoom/_client.py`, `kiwoom/chart.py`, 원문 archive | `ka10081` 요청·페이지별 원 응답과 해시, `upd_stkpc_tp`, 코드/파서 hash를 보존한다. 90일 운영 retention과 연구용 불변 archive를 분리한다. | `102950` 지정일의 원 문자열→정규화→DB 값이 한 manifest에서 재현된다. |

필수 회귀 테스트는 `test_krx_client_nan.py`의 NaN→0 기대를 결측 보존으로 바꾸고, `test_krx_mapper.py`에 `032980`의 세 역전 행과 OHL 0/C 양수 행 격리를 추가하는 것이다. 저장소 테스트에는 잘못된 OHLC가 직접 들어와도 거부되는 방어를, CLI/서비스 테스트에는 manifest 필수 필드·해시 검증·격리 건수에 따른 인수 실패를 추가한다. 키움 테스트에는 `"0"`, `"1"`, `"0.4"` 변환과 원 응답 hash 연결을 고정한다.

## 남은 증거와 해석 한계

- 과거 Naver XML과 `ka10081` 원 응답이 없다. 현재 또는 새로 받은 응답은 공급자 소급 정정 때문에 과거 응답을 대체하지 않는다.
- Naver 수정주가의 기업행사별 계수, OHLC 필드별 반올림, 거래정지 표기 계약이 없다. 1~2원 역전의 최종 생성 규칙은 공급자 자료로 확인해야 한다.
- 완료 커밋은 집계 기록일 뿐 실행 로그·manifest가 아니다. 현재 실행 컨테이너 소스 해시도 당시 2026-09-12 실행 이미지의 불변 증거가 아니다.
- `data_vendor='KRX'`는 현재 데이터의 적재 경로 분류로만 사용해야 한다. 출처가 수정된 새 revision을 만들기 전 기존 라벨을 과거 행별 원천 증거로 해석하면 안 된다.

조사 중 앱 import, 수집 API 호출, 원문 재조회, DB 쓰기, 재수집은 하지 않았다. 순수 변환은 고정 문자열/XML에 설치 코드와 같은 필드 분할·정수 변환·매퍼 조건만 적용했다.
