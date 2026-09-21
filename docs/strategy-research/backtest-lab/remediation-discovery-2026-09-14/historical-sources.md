# 2015~2023 역사 기업행사·공시 확보 경로 조사

이 문서는 2015~2023 KRX 백테스트에 필요한 기업행사, 공시, 상장·거래 상태, 종목 식별자와 당시 분류를 어떤 공식 경로에서 다시 받을 수 있는지 판정한다. **구현상 바로 재사용할 수 있는 핵심은 OpenDART 공시목록·원문 클라이언트와 기존 `ted-startup` 파서이며, 이것만으로는 역사 유니버스와 거래정지 구간을 완성할 수 없다.** OpenDART의 일부 구조화 API는 공식 문서가 2015년 이후 제공을 명시하지만, KIND·KRX 화면과 키움 REST는 공개 문서만으로 2015~2023 전체 보존·완전성을 증명하지 못했다. 따라서 `public.corporate_event`와 `public.dart_disclosure`의 대상 기간 0건을 해소할 **후보 경로는 확인**, 백필 가능성 최종 판정은 `미확정`이다.

조사 기준일은 2026-09-14 KST다. 공개 개발가이드와 초기 화면만 열람했고, 인증키·계정·비밀은 조회하지 않았다. API 실데이터 호출, Excel 다운로드, DB 쓰기, 재수집, 2024년 이후 가격·성과 조회는 하지 않았다. `public.corporate_event`와 `public.dart_disclosure`의 대상 기간 0건은 [2026-09-13 테이블 감사](../table-audit-2026-09-13/README.md)의 스냅샷이며, 2026-09-14 재집계 결과가 아니다. 요구 필드는 [백필 인수 계약](../../backfill-contract.md)을 따른다. 이 문서의 `2015-01-01` 시작은 가격 행 시작일이 아니라 기업행사·공시·상장상태 메타데이터의 기간 경계다. 가격 감사의 시작일 `2015-01-02`와 의미가 다르다.

## 핵심 판정

| 영역 | 권장 1차 경로 | 2015~2023 제공 범위의 공식 증명 | 현재 판정 |
| --- | --- | --- | --- |
| 공시 원장·인지일·정정 표지 | OpenDART `list.json`, `document.xml` | 공시검색 일반 API의 최초 연도는 문서에 없음. 일부 구조화 API만 “2015년 이후” 명시 | **후보 확정, 전체 범위 미확정** |
| 유·무상증자·감자·합병·분할합병 | OpenDART 구조화 주요사항보고서 API + 원문 | 각 구조화 API는 2015년 이후 제공을 명시 | **2015~2023 경로 확인**. 전 종목·전 이벤트 완전성은 실제 인수검사 전 미확정 |
| 액면분할·주식병합·주식·현금배당 | OpenDART 공시검색·원문, KIND 배당 화면 | KIND 배당은 2010년부터 최근 사업연도까지 명시. 분할·병합 공시의 일반 검색 보존 시작일은 미표기 | **KIND 화면 명시 기간 확인**. 배당 행사원장 완전성과 분할·병합 전체 범위는 미확정 |
| 상장·상폐·날짜별 종목 집합 | KIND 상장종목현황·상장폐지현황, KRX Data Marketplace | 조회일자/기간 입력과 Excel 기능은 확인. 가능한 최초 조회일은 공개 화면에 없음 | **미확정** |
| 거래정지·재개 | KIND 공시검색의 시장조치/안내와 정지 화면, KRX 지정·거래정지 통계 | 현재 정지 화면에는 기간 입력이 보이지 않음. 공시로 구간을 완전 복원할 수 있다는 보장도 없음 | **미확정** |
| 코드 승계·영구 식별자 | KRX 표준코드·변경상장 자료, DART `corp_code` 보조 | DART 법인코드 ZIP은 현재 종목코드와 최종변경일만 제공하고 유효기간 이력은 제공하지 않음 | **미확정** |
| 당시 시장·상품·업종 | KRX 날짜별 종목 스냅샷·업종분류 자료 | KIND 상장종목현황은 조회일자 입력을 제공하나 반환 필드와 최초일은 이번 공개 문서에서 입증되지 않음 | **미확정** |
| 공식 거래일 | KRX 연도별 일정·공식 휴장/임시휴장 공지 + 전종목 시세 관측일 대조 | KRX 연도 일정 화면은 2015~2020, 2022~2023 선택을 노출했으나 이번 렌더링에서 2021을 확인하지 못함. 전종목 시세의 행 존재는 개장일 대조에는 유용하지만 행 부재만으로 공식 휴장일을 증명할 수 없음 | **2015~2023 전체는 미확정** |

이 판정은 “공식 문서가 기간 경로를 명시한다”와 “대상 기간 전체 행이 실제로 반환되고 완전하다”를 구분한다. 전자를 **문서상 기간 경로 확인**, URL·인증 또는 화면만 확인하고 역사 하한을 입증하지 못한 경우를 **후보/범위 미확정**으로 표기한다. 문서에 2015년 이후 제공이라고 적힌 API도 특정 회사·사건의 누락, 철회·정정 연결, 공시 전 효력 발생, 코드 변경을 자동 해결하지 않는다.

## 권장 수집 구조와 판단 기준

재납품은 세 층으로 분리해야 한다.

1. **인지 원장**은 OpenDART의 모든 제출본을 `last_reprt_at=N`으로 수집한다. `rcept_no`, `rcept_dt`, `report_nm`, `rm`, 원문 ZIP 해시를 보존한다. `last_reprt_at=Y`만 받으면 과거 시점에 없었던 최종 정정값을 소급 적용할 수 있다.
2. **효력 원장**은 구조화 API와 원문에서 결정일, 기준일, 권리락일, 상장예정일, 정지예정 구간, 비율·주당금액을 추출한다. 같은 값이 없거나 충돌하면 추정하지 않고 `unknown` 또는 `conflict`로 남긴다.
3. **시장 상태 원장**은 KRX/KIND의 날짜별 상장 종목, 상품 유형, 시장, 정지·재개, 상폐, 코드/표준코드 매핑과 거래일을 공급받아 공시 원장과 대조한다. 공개 화면의 과거 제공 범위가 확인되지 않았으므로, 공급자가 대상 기간을 실제 반환하는지 확인한 뒤에만 이 층을 PASS로 판정한다.

일봉 백테스트의 인지 시점은 OpenDART API가 제공하는 `rcept_dt`가 날짜뿐이라는 한계 때문에 별도 정책이 필요하다. 원문에 접수시각을 입증하는 필드가 없다면 `known_at_precision="date"`로 저장하고, 당일 종가 의사결정에는 사용하지 않는 보수적 규칙을 권장한다. 이는 공식 필드의 의미를 바꾸는 추정이 아니라 미래정보 사용을 피하기 위한 연구 정책이다.

## 경로별 공식 근거와 한계

### 1. OpenDART: 공시 원장과 일부 기업행사의 1차 경로

- [공시검색 개발가이드](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001)는 `list.json`의 `corp_code`, 접수일 범위, 공시유형, `last_reprt_at`, 페이지네이션과 결과의 `stock_code`, `report_nm`, `rcept_no`, `rcept_dt`, `rm`을 정의한다. 회사 미지정 검색은 한 번에 3개월 이내여야 하며, 페이지당 최대 100건이다. `last_reprt_at=N`은 정정보고서를 포함한 제출본 전체를 반환하고 `report_nm`의 정정 접두어와 `rm`의 `정`·`철` 표지를 제공한다.
- [공시서류 원본파일 개발가이드](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019003)는 `rcept_no`별 `document.xml` ZIP을 제공한다. 인증키가 필요하고 원문 자체의 기간 보존 시작일은 이 문서에 적혀 있지 않다.
- [법인 고유번호 개발가이드](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019018)는 현재 `corp_code`, 법인명, 6자리 `stock_code`, 기업개황 최종변경일 `modify_date`를 제공한다. 과거 코드의 유효 시작·종료일이나 코드 승계 관계는 없다.
- [무상증자](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS005&apiId=2020024), [유무상증자](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS005&apiId=2020025), [감자](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS005&apiId=2020026), [회사합병](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS005&apiId=2020050), [회사분할합병](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS005&apiId=2020052) 개발가이드는 `corp_code`와 최초접수일 범위를 요구하고 **2015년 이후 제공**을 명시한다. 배정 주식수·기준일·신주상장예정일·결정일, 감자비율·정지예정구간, 합병비율·상대회사 등 행사별 필드를 제공한다. 필드 변경 시점도 일부 명시하므로, 예를 들어 감자 정지예정구간은 2019-12-08 이전 단일 필드와 2019-12-09 이후 시작/종료 필드를 함께 정규화해야 한다.
- [배당에 관한 사항](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS002&apiId=2019005)은 사업연도 2015년 이후를 명시하지만 정기보고서 요약이다. 실제 배당 결정의 인지일·기준일·지급일을 모두 대신하지 못하므로 공시목록·원문과 결합해야 한다.

OpenDART의 2015년 명시는 해당 구조화 API의 제공 시작을 뜻한다. 액면분할·주식병합·현금배당 결정의 동일한 구조화 API 범위, DART 등록 전 상폐 법인의 현재 `corp_code` 매핑, 모든 정정의 선후 접수번호 연결은 이번 문서에서 확인되지 않았다. 따라서 공시목록에서 보고서명을 분류하고 원문을 받는 경로를 쓰되, 2015년 첫날과 2023년 마지막 날의 반환 및 연도별 건수 연속성을 실제 인수 단계에서 검증해야 한다.

### 2. KIND와 KRX: 시장 효력·유니버스 대조 후보

- [KIND 배당정보](https://kind.krx.co.kr/disclosureinfo/dividendinfo.do?method=searchDividendInfoMain)는 주식배당결정·정기주주총회 결과 공시를 기준으로 하며 **2010년도부터 최근 사업연도까지** 제공한다고 밝힌다. 현재 결산월을 표시하고 업종변경 기업은 변경 후 업종을 익년부터 반영한다는 주의가 있어 당시 업종 원장으로 그대로 쓰면 안 된다.
- [KIND 상장폐지현황](https://kind.krx.co.kr/investwarn/delcompany.do?method=searchDelCompanyMain)은 시장·회사·기간 입력과 Excel 내보내기를 제공한다. 공개 초기 화면에는 최초 제공일과 반환 컬럼 설명이 없어 2015~2023 전부 이용 가능하다는 증거는 아직 없다.
- [KIND 상장종목현황](https://kind.krx.co.kr/corpgeneral/listedIssueStatus.do?method=loadInitPage)은 `조회일자` 입력과 Excel 내보내기를 제공한다. 과거 날짜의 상품 유형·시장·업종·상장 상태까지 반환하는지, 최초 가능 날짜가 언제인지는 이번 비인증 문서 열람으로 확인되지 않았다.
- [KIND 매매거래정지종목](https://kind.krx.co.kr/investwarn/tradinghaltissue.do?method=searchTradingHaltIssueMain)은 현재 시장·종목 필터와 Excel 기능을 제공하지만 기간 입력은 보이지 않는다. 장기 역사 구간은 OpenDART 공시검색의 거래소공시 `I003`(시장조치/안내) 후보와 KRX 거래정지 통계를 함께 대조해야 하며, 시작·재개 쌍의 완전성은 미확정이다.
- [KRX Data Marketplace 전종목 시세](https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd?screenId=MDCSTAT015)는 날짜별 종목코드·시장구분·OHLCV·거래대금·상장주식수를 제공하는 공식 화면이다. [서비스 메뉴](https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd)는 전종목 기본정보·지정내역·상장회사 상세검색·업종분류 현황을 별도 항목으로 제공한다. 이번에는 데이터 요청이나 다운로드를 하지 않았으며, 각 화면의 역사 하한과 장기간 자동 취득 조건은 확인되지 않았다. 전종목 시세는 실제 행이 있는 날짜의 개장 관측을 대조할 수 있지만, 행이 없는 날짜가 주말·법정휴일·임시휴장·수집누락 중 무엇인지 단독 판정하지 못하므로 공식 휴장 달력을 대체할 수 없다.
- [KRX Open API 이용방법](https://openapi.krx.co.kr/contents/OPP/INFO/OPPINFO003.jsp)은 회원가입·인증키 신청, API별 활용신청, 관리자 승인을 요구한다. 비인증 공개 서비스 목록은 동적 콘텐츠가 비어 있어 대상 필드와 기간을 확인하지 못했다. 따라서 “공식 Open API니까 2015년 전체를 준다”고 가정할 수 없다.
- [KRX 연도별 일정](https://global.krx.co.kr/contents/GLB/05/0501/0501060000/GLB0501060000T3.jsp)은 과거 연도 선택과 다운로드를 제공하며 2015~2020, 2022~2023이 공개 렌더링에서 확인됐다. 2021 선택은 이번 렌더링에서 확인되지 않아 단독으로 대상 기간 공식 거래일 전체를 증명하지 못한다.

### 3. 키움 REST: 가격 대조 보조이며 역사 기업행사 원장은 아님

[키움 REST API 가이드](https://openapi.kiwoom.com/guide/apiguide)는 App Key·Secret으로 OAuth 토큰을 발급받는 인증 경로를 정의한다. 키움의 [공식 `ka10081` 일봉 예제](https://raw.githubusercontent.com/Kiwoom-Securities/Kiwoom-REST-API/main/examples/%EA%B5%AD%EB%82%B4%EC%A3%BC%EC%8B%9D/%EC%B0%A8%ED%8A%B8/get_domestic_stock_daily_chart.py)는 종목코드, 기준일자, 수정주가 구분과 연속조회로 일봉을 받고, 2018년 삼성전자 액면분할 예시로 기준일자에 따라 과거 수정가 적용이 달라질 수 있음을 설명한다.

이 경로는 수정 전·후 가격 대조에는 쓸 수 있지만 행사 유형, 효력일, 수량 계수, 정정 계보, 상폐 정산, 당시 업종을 제공하지 않는다. 공식 예시 하나가 2015~2023 모든 상폐 종목의 원·수정가 보존 범위를 증명하지도 않는다. 따라서 `ka10081`은 기업행사 원장의 대체재가 아니라 행사 계수와 가격 단절을 대조하는 보조 증거로만 둔다.

## `ted-startup`에서 재사용할 수 있는 것과 그대로 쓰면 안 되는 것

인접 저장소 `C:/Users/aeby/vscode/ted-startup/src/backend_py`에는 다음 구현이 이미 있다.

| 기존 구현 | 재사용 가능 부분 | 역사 백필 전 필수 보완 |
| --- | --- | --- |
| `app/adapter/out/external/dart_client.py` | `/list.json` 페이지네이션 메타, `/document.xml` ZIP, `/corpCode.xml` ZIP, 상태코드·크기 방어 | 기간 분할 실행 계획, 요청·응답 원문 해시와 실행 manifest, 구조화 기업행사 전용 API DTO |
| `app/application/service/dart_disclosure_service.py` | `last_reprt_at` 기본 전체 제출본 처리, 100건 페이지, `rcept_no` 검증, 일별 전체 시장 수집 | 현재 일별 잡을 2015~2023 재현 가능한 배치로 일반화. 연도/월별 기대·실제 페이지 및 중단 재개 영수증 필요 |
| `app/domain/dart/disclosure_classifier.py` | 정정 접두어를 제거한 10개 이벤트명 분류 | 접두어를 제거하기 전 `correction_type` 보존, 철회·후속 정정의 선후 `rcept_no` 연결, 미분류 보고서 검토 큐 |
| `app/domain/dart/document_parser.py` | ZIP 방어, `ex_date`, `record_date`, `ratio`, `new_share_count` best-effort 추출과 `PARSED/PARTIAL/FAILED` | 현재 파서는 비정형 원문 100%를 보장하지 않고 현금배당 금액·지급일·합병 승계 ID가 부족. 원문 바이트와 파서 버전·필드별 근거 위치 보존 필요 |
| `corporate_event` 모델 | 결정일, 효력 후보일, 기준일, 비율, 신주수, 주당금액, 출처 상태 | `known_at`, 정정 계보, 원문 SHA-256, 가격/수량 계수, 이벤트 영구 ID, 상폐·합병 정산 필드가 없음 |
| `scripts/sync_dart_corp_mapping.py` | 현재 DART 법인코드와 종목코드 매핑 파싱 | 기본 KRX 현재상장 교차필터가 과거 상폐 종목을 배제하므로 역사 백필에 사용 금지. 유효기간과 과거 코드 이력이 없음 |
| `app/adapter/out/external/krx_client.py`와 ex-date reconcile | 원·수정 종가 비율 step을 행사 후보와 대조 | 병렬 가격 조사가 배포된 `pykrx` 1.2.8의 `adjusted=True` 경로를 Naver fchart XML 호출로 확인했으므로 KRX 공식 API로 간주할 수 없음. 원 XML·과거 실행과 Naver의 수정주가 정의는 미확정이며, 가격 step도 사건 원인·효력일의 공식 증명이 아니므로 단독 채움 금지 |

특히 현재 `dart_disclosure.raw_payload`는 4KB 초과 시 축약되고 `corporate_event.raw_payload`도 추출값 중심이므로 **원문 보존 계약을 만족하지 않는다**. 기존 로직은 재사용하되, 원문 ZIP 자체나 불변 객체의 SHA-256과 저장 위치를 별도 manifest에 기록해야 한다.

## 재납품 필드 명세

다음은 테이블명이 아니라 공급자가 어떤 형식으로든 제공해야 하는 의미 계약이다.

| 묶음 | 필수 필드 | 판정 목적 |
| --- | --- | --- |
| 식별자 | `instrument_id`, `isin_or_standard_code`, `stock_code`, `corp_code`, `valid_from`, `valid_to`, `mapping_reason`, `source_url` | 코드 변경·재사용·합병 승계를 끊김 없이 연결 |
| 공시 제출본 | `rcept_no`, `corp_code`, `stock_code_as_filed`, `report_nm_raw`, `rcept_date`, `known_at`, `known_at_precision`, `correction_type`, `withdrawn`, `supersedes_rcept_no` | 당시 인지 가능한 버전만 선택 |
| 행사 | `event_id`, `event_type`, `decision_date`, `record_date`, `effective_date`, `ex_date`, `settlement_date`, `listing_date`, `price_factor`, `quantity_factor`, `cash_per_share`, `currency`, `rounding_rule` | 원가격·수량·현금 정산 재계산 |
| 상장·상태 | `instrument_id`, `market`, `product_type`, `industry_code`, `status`, `status_reason`, `valid_from`, `valid_to` | 당시 유니버스·상품·업종 복원 |
| 정지 구간 | `instrument_id`, `halt_start_at`, `resume_at`, `reason`, `announcement_id`, `source_url` | 결측·무거래·거래정지를 구분 |
| 거래일 | `market`, `session_date`, `is_open`, `session_type`, `open_at`, `close_at`, `source_url` | 기대 종목일의 공식 분모 생성 |
| 원문·계보 | `source_system`, `source_url`, `retrieved_at`, `source_published_at`, `raw_object_uri`, `raw_sha256`, `parser_version`, `row_payload_sha256` | 정정·소급 변경과 동일 납품 재현 |
| 실행 manifest | `run_id`, 요청 범위, 요청 파라미터(비밀 제외), 페이지/행 수, 최초·최종 일자, 실패·재시도, 파일 해시, 스키마 버전 | 부분수집·중복·누락 탐지 |

`effective_date`와 `known_at`은 합치지 않는다. 예를 들어 미래 권리락일이 먼저 공시되면 효력일 이전부터 알려진 사건이고, 정정공시가 나중에 제출되면 과거 효력일을 가진 새 버전이다. 최종값 하나만 저장하면 미래정보 사용 여부를 판정할 수 없다.

## 완료 검사와 인수 게이트

다음 검사를 모두 통과하기 전에는 역사자료 보완을 완료로 표시하지 않는다.

1. **범위 증명**: 소스별 요청 가능 최소일을 공식 문서 또는 실제 반환 검사 영수증으로 기록하고 2015-01-01~2023-12-31 각 연도에 성공 페이지가 있는지 확인한다. 0건인 연도·월은 원천의 `total_count=0` 또는 동등한 증거와 함께 남긴다.
2. **페이지 완전성**: 요청별 `total_count`, 수집 고유 `rcept_no`, 페이지 합계가 일치하고 회사 미지정 OpenDART 요청은 3개월 이하로 분할한다. 중단·재개 후 중복과 누락이 없어야 한다.
3. **정정 계보**: `last_reprt_at=N`으로 모든 제출본을 보존하고 `정`, `철`, 정정 접두어를 잃지 않는다. 각 체인의 최초본→정정본→철회/최종본을 연결하며 계보 불명은 완료율에서 제외한다.
4. **인지·효력 분리**: 모든 행사에 `known_at`과 `effective_date`를 별도로 둔다. 날짜 정밀도만 있는 인지값을 임의 시각으로 보간하지 않는다.
5. **원문 동일성**: 모든 공시 원문 ZIP 또는 허용된 불변 원문 객체에 SHA-256이 있고 파생 row가 `rcept_no`, 파서 버전, 원문 해시로 역추적된다. 재실행 시 같은 원문은 같은 파생 payload 해시를 만든다.
6. **행사 수학**: 분할·병합·증자·감자마다 가격 계수와 수량 계수의 방향·단위·적용 경계를 표본 원문과 대조한다. 현금배당은 주당금액·통화·지급/기준일을 별도 보존한다.
7. **역사 유니버스**: 각 공식 거래일에 당시 상장 종목 집합을 생성하고 상장 전·상폐 후 행이 없다. 상폐 종목과 현재 비활성 종목이 현재 마스터 필터 때문에 사라지지 않는다.
8. **상태 구간**: 거래정지 시작은 재개 또는 상폐와 연결하고 겹침·역전·열린 구간을 보고한다. 가격 0이나 거래량 0만으로 정지를 추정하지 않는다.
9. **코드·상품·업종**: 동일 코드의 유효기간 중복과 하나의 영구 ID에 대한 모순 매핑이 없다. 시장·상품·업종은 현재값을 과거 전체에 복제하지 않는다.
10. **교차 대조**: OpenDART 행사와 KIND/KRX 효력 정보, 원·수정 가격 단절을 사건별로 대조한다. 불일치는 자동 덮어쓰기하지 않고 `conflict`와 두 원문 해시를 보존한다.

## 접근 결과와 남은 미확정

조사한 공개 가이드·초기 화면은 2026-09-14에 HTTP 200으로 열렸다. API 데이터 엔드포인트는 모두 미호출이다. 구조화 접근 결과는 [historical-sources.json](historical-sources.json)에 있다.

확정할 수 있는 것은 다음 세 가지다.

- OpenDART의 무상·유무상증자, 감자, 합병, 분할합병 구조화 API와 정기보고서 배당 요약은 공식 문서상 2015년 이후를 제공한다.
- KIND 배당정보는 공식 화면상 2010년부터 최근 사업연도까지 제공한다.
- 기존 `ted-startup` OpenDART 클라이언트·분류기·본문 파서는 재사용 가능하지만, 일별 현재 수집·현재 상장 교차필터·축약 raw payload를 그대로 역사 백필 계약으로 사용할 수 없다.

미확정이며 공급자 확인이나 소규모 실제 반환 검사가 필요한 것은 다음이다.

- 일반 OpenDART 공시목록·원문이 대상 기업과 상폐 기업을 포함해 2015~2023 전부 반환하는지
- 액면분할·주식병합·현금/주식배당 결정의 전수와 정정 선후 `rcept_no` 연결을 자동 복원할 수 있는지
- KIND/KRX가 2015~2023 날짜별 상장 종목, 거래정지·재개, 상폐, 종목코드 승계, 당시 상품·업종을 완전하게 제공하는지
- KRX 공식 거래일의 2021년을 포함한 전 기간 기계판독 경로와 Open API의 정확한 서비스·필드·과거 하한
- 키움 `ka10081`이 대상 기간의 상폐 종목과 원·수정 가격을 모두 보존하는지
