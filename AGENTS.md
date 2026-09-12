# 저장소 작업 지침

이 문서는 vectorbt 저장소에서 작업하는 에이전트가 구조, 개발 명령, 검증 기준을 빠르게 파악하기 위한 지침이다. 핵심 원칙은 기존 pandas API와 수치 계산 동작을 유지하면서 요청한 범위만 수정하는 것이다. 저장소 전체에 적용하며, 의존성 및 CI 명령이 변경되면 `pyproject.toml`과 `.github/workflows/`의 실제 설정을 우선 확인한다.

## 프로젝트 구조

vectorbt는 pandas·NumPy 배열로 여러 매매 전략을 동시에 백테스트하는 Python 라이브러리다. Numba의 JIT(실행 시점 컴파일) 커널과 선택적 Rust 엔진으로 계산을 가속한다. Python 지원 범위는 현재 3.11~3.14다.

| 경로 | 역할 |
| --- | --- |
| `vectorbt/base/` | 배열 브로드캐스팅, 인덱싱, pandas 메타데이터를 보존하는 `ArrayWrapper` |
| `vectorbt/generic/` | 롤링 계산 등 공통 시계열 연산과 액세서 |
| `vectorbt/indicators/`, `signals/`, `labels/`, `returns/` | 지표, 매매 신호, 학습용 레이블, 수익률 분석 |
| `vectorbt/portfolio/`, `records/` | 포트폴리오 시뮬레이션과 주문·거래 등 구조화 레코드 |
| `vectorbt/data/`, `utils/`, `messaging/` | 데이터 소스 연동, 공통 유틸리티, 메시징 |
| `vectorbt/_engine.py`, `vectorbt/_settings.py` | 엔진 선택과 전역 설정 |
| `rust/src/` | PyO3를 사용하는 선택적 확장 패키지 `vectorbt-rust` |
| `tests/` | 기능별 pytest 테스트와 엔진 비교 테스트 |
| `docs/`, `examples/`, `apps/`, `benchmarks/` | MkDocs 문서, 예제, 샘플 앱, 성능 측정 |

표에서 한 셀에 나열한 축약 디렉터리는 모두 `vectorbt/` 아래에 있다.

## 설치와 테스트

기본 명령은 저장소 루트에서 실행한다. CI는 `uv`를 사용하며 Linux·Windows·macOS와 Python 3.11~3.14 조합에서 Python 전용 환경과 Rust 설치 환경을 각각 검사한다.

```powershell
# 최초 환경 구성: Python 버전은 지원 범위 안에서 선택
uv python install 3.11
uv venv --python 3.11
uv pip install --python .venv -e ".[test]"

# 변경한 기능부터 검사한 뒤 필요한 범위로 확대
uv run --python .venv --no-sync pytest tests/test_generic.py
uv run --python .venv --no-sync pytest tests/test_engine.py
uv run --python .venv --no-sync pytest tests/
```

`uv`를 사용하지 않는 경우 활성화된 가상환경에서 `python -m pip install -e ".[test]"`와 `python -m pytest tests/`를 사용한다. 기존 개발환경이 있으면 먼저 확인하고 재사용한다.

Rust 변경은 Rust 툴체인을 준비하고 로컬 확장을 다시 빌드하여 검증한다.

```powershell
uv pip install --python .venv -e ".[test-rust]"
uv run --python .venv --no-sync python -m maturin develop --manifest-path rust/Cargo.toml --release
cargo test --manifest-path rust/Cargo.toml
uv run --python .venv --no-sync pytest tests/test_engine.py
uv run --python .venv --no-sync pytest tests/
```

Rust가 없거나 버전이 호환되지 않으면 관련 테스트가 건너뛰어질 수 있다. 테스트 통과와 Rust 경로의 실제 실행을 구분하여 보고한다. 성능 측정은 release 빌드를 사용하며 절차는 `rust/README.md`와 `benchmarks/README.md`를 따른다.

## 구현 및 검증 원칙

- 주변 코드의 명명, 타입 힌트, 독스트링, import 방식을 따른다. Python의 Black 설정은 줄 길이 120이며, 이를 이유로 무관한 파일 전체를 재정렬하지 않는다.
- `nb.py`는 NumPy 배열과 Numba 호환 타입을 처리하는 참조 커널이다. Rust 분기는 `dispatch.py`와 `_engine.py`의 기존 패턴을 사용하고 Numba 커널에 Rust 의존성을 넣지 않는다.
- 사용자 API를 수정할 때 브로드캐스팅, 반환 차원, index·columns·freq, 그룹화 동작을 보존한다. 일반적으로 행은 시간, 열은 자산 또는 파라미터 조합이며, `_1d` 함수 등 예외는 해당 함수의 계약을 따른다.
- `engine="auto"`는 지원되는 호출에서 호환 Rust 엔진을 선택하고 나머지는 Numba로 돌아간다. `engine="rust"`를 명시한 경우 지원 불가 사유를 오류로 전달하는 계약을 유지한다.
- 난수 연산의 `auto`는 기존 난수 스트림 보존을 위해 Numba를 유지한다. 콜백과 지원하지 않는 입력의 대체 실행 경로도 확인한다.
- Rust 커널 추가 시 Numba와 인자 순서·반환 형태를 맞추고 PyO3 등록, Python 디스패치, 결과 일치·대체 실행·명시적 오류 테스트를 함께 반영한다. 구조화 dtype 변경은 Python과 Rust의 필드 및 메모리 배치를 함께 확인한다.
- 계산 변경은 재현 가능한 회귀 사례로 검증한다. 관련된 NaN, 빈 배열, 경계 파라미터, dtype, C/F 메모리 배치, 수치 안정성을 검사하며 허용 오차를 무작정 늘려 실패를 숨기지 않는다.
- 전역 설정이나 엔진 캐시를 변경한 테스트는 기존 정리 패턴인 `vbt.settings.reset()`과 `_engine.clear_engine_cache()`를 참고하여 상태를 복원한다.
- `tests/conftest.py`는 pandas 비교 함수의 dtype·시간 단위를 정규화하고 Rust 테스트의 skip을 처리한다. 비교 실패를 조사할 때 이 동작을 고려한다.
- 동작 변경에는 관련 테스트를 추가하거나 수정한다. 문서만 바꾸는 경우 불필요한 전체 테스트 대신 내용, 경로, 명령의 정합성을 확인한다. 완료 보고에는 실제 실행한 검증과 미실행 항목을 구분한다.

## 문서 작성과 빌드

사용자 설명과 새 작업 지침은 기본적으로 한글로 작성한다. 기존 코드 식별자와 문서의 언어·템플릿은 요청 없이 일괄 번역하지 않는다.

Markdown을 새로 작성하거나 의미 있게 수정할 때는 목적·핵심 결론 또는 현재 판단·범위와 한계를 첫머리에 짧게 제시한다. 본문은 핵심 요약 → 전체 구조와 판단 기준 → 근거와 비교 → 세부 사례 → 방법론과 출처 순서로 구성한다. 긴 문서는 요약 다음에 각 절의 역할과 읽기 순서를 안내한다.

각 절과 문단은 핵심 의미부터 설명하고, 큰 표 앞에는 비교 대상과 읽어낼 점을 쓴다. 낯선 용어는 처음에 풀어 쓰고 사실·추정·권장안·미확정 사항을 구분한다. 짧은 문서에 불필요한 목차를 추가하지 않으며 기존 메타데이터와 기계 판독 형식을 보존한다. 요청과 무관한 문서는 재작성하지 않는다.

사이트 문서 또는 API 문서를 변경한 경우 다음은 CI 기준 빌드 절차다. API 생성 결과를 직접 고치기 전에 원본 독스트링과 생성 스크립트를 확인한다.

```powershell
# 저장소 루트에서 의존성 설치
uv pip install --python .venv -e ".[full,docs]"
Push-Location docs
try {
    uv run --python ../.venv --no-sync python generate_api.py
    uv run --python ../.venv --no-sync python update_api_nav.py
    uv run --python ../.venv --no-sync mkdocs build --strict
} finally {
    Pop-Location
}
```

## 변경 범위와 참고 자료

작업 전후 `git status --short`와 diff로 변경 범위를 확인한다. 사용자의 기존 수정과 추적되지 않은 파일을 보존하고, 의존성·생성물·버전·릴리스 설정은 작업에 필요한 경우에만 변경한다. 커밋과 PR은 하나의 관심사로 유지하고 변경 이유 및 검증 결과를 설명한다.

구체적인 근거는 `pyproject.toml`, `.github/workflows/tests.yml`, `.github/workflows/docs.yml`, `rust/README.md`, `docs/docs/getting-started/contributing.md`에서 확인한다. 라이선스 관련 변경은 루트 `LICENSE.md`와 별도 문서 라이선스인 `docs/LICENSE.md`를 각각 확인한다.
