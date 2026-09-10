# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

vectorbt 는 pandas · NumPy · Numba 위에 구축된 벡터화 백테스팅 라이브러리다. 수천 개의 전략 설정을
NumPy 배열에 담아 한 번에 실행하며, 핫 패스는 Numba JIT 커널과 선택적 Rust 엔진(`vectorbt-rust`)이
가속한다. Python 3.11 ~ 3.14, pandas 3.x, NumPy 2.4+ 를 요구한다.

## 자주 쓰는 명령

```bash
# 개발 설치 (테스트 의존성 포함)
pip install -e ".[test]"

# Rust 엔진을 로컬에서 빌드 (rust 툴체인 + maturin 필요, 반드시 release 빌드)
pip install -e ".[test-rust]"
python -m maturin develop --manifest-path rust/Cargo.toml --release

# 전체 테스트 / 단일 파일 / 단일 테스트
pytest tests/
pytest tests/test_generic.py
pytest tests/test_generic.py::TestAccessors::test_rolling_std
pytest -n auto tests/                      # pytest-xdist 병렬 실행

# 엔진 디스패치(Numba ↔ Rust) 전용 테스트
pytest tests/test_engine.py

# Numba 와 Rust 커널의 결과 일치 확인 + 벤치마크
python benchmarks/bench_engine.py --rows 5000 --cols 50 --check
python benchmarks/bench_matrix.py          # BENCHMARKS*.md 재생성

# 문서 (docs/ 디렉터리에서 실행)
pip install -e ".[full,docs]"
python generate_api.py && python update_api_nav.py && mkdocs build --strict
```

코드 스타일은 `black` 기준 줄 길이 120 이다(`pyproject.toml`). 별도 lint 설정은 없고 `mypy.ini` 는
`ignore_missing_imports` 만 켜 둔 상태다.

CI(`.github/workflows/tests.yml`)는 3개 OS × Python 3.11 ~ 3.14 매트릭스에서 `test` 잡(Numba 만)과
`rust-engine` 잡(maturin 으로 로컬 빌드 후 동일 테스트)을 각각 돌린다.

## 아키텍처

### 계층 구조

서브패키지는 아래 순서로 의존한다. 상위 계층이 하위 계층을 import 하며, 역방향 import 는 없다.

```
utils        설정(Config/Configured), 데코레이터, 캐싱, 체크 유틸
  └ base     ArrayWrapper, 브로드캐스팅, reshape, 인덱싱 — pandas 메타데이터 처리
     └ generic   임의 시계열 공통 연산 (rolling, 매핑, Ranges/Drawdowns, 플로팅)
        ├ signals     엔트리/엑시트 신호 생성·결합, SignalFactory
        ├ returns     수익률 지표 (empyrical 계열)
        ├ indicators  IndicatorFactory 와 내장 지표(MA, RSI, BBANDS …)
        ├ labels      look-ahead 레이블 생성기
        ├ records     구조화 배열 기반 희소 이벤트 데이터 (Records, MappedArray)
        └ portfolio   Portfolio 시뮬레이션, 주문/거래/포지션 기록, 성과 지표
data         외부 데이터 소스 (yfinance, binance, ccxt, alpaca 등 — 선택 의존성)
messaging    Telegram 봇 연동
```

### 서브패키지 내부의 3층 구조

연산이 있는 서브패키지(generic · signals · returns · indicators · labels · records · portfolio)는
파일 역할이 고정되어 있다. 새 기능을 추가할 때 이 구분을 지켜야 한다.

| 파일 | 역할 | 규칙 |
| --- | --- | --- |
| `nb.py` | Numba `@njit` 커널. 순수 NumPy 배열만 받는다 | **참조 구현(reference)**. 여기서 `vectorbt_rust` 를 import 하면 안 된다 |
| `dispatch.py` | 엔진 중립 래퍼. `engine` 인자를 받아 Numba 또는 Rust 커널로 분기 | 모든 공개 API 는 `nb` 가 아니라 `dispatch` 를 호출한다 |
| `accessors.py` / `base.py` | pandas 액세서 또는 클래스(`Portfolio`, `Records`)로 사용자 API 노출 | `dispatch.*` 를 호출하고 결과를 `ArrayWrapper` 로 다시 pandas 객체에 감싼다 |
| `enums.py` | 구조화 dtype(`order_dt`, `trade_dt` …)과 열거형 | Numba 와 Rust 가 같은 레이아웃을 공유하므로 변경 시 양쪽을 맞춘다 |

### 엔진 해석 (`vectorbt/_engine.py`)

- `vbt.settings["engine"]` 은 `"auto"`(기본) · `"numba"` · `"rust"` 중 하나이며, 각 호출의 `engine=` 인자가 이를 덮어쓴다.
- `resolve_engine(engine, supports_rust)` 가 최종 엔진을 결정한다. `auto` 는 Rust 가 설치되어 있고
  major.minor 버전이 vectorbt 와 일치하며 해당 호출이 지원될 때만 Rust 를 고르고, 아니면 Numba 로 폴백한다.
  `rust` 를 명시했는데 불가능하면 이유가 담긴 예외를 던진다.
- `*_compatible_with_rust(...)` 계열 함수가 `RustSupport` 를 반환하며, `combine_rust_support` 로 여러
  조건을 합친다. dtype 변환이 필요하면 `prepare_array_for_rust` 로 float64 등으로 맞춘 뒤 넘긴다.
- **난수 함수는 예외다.** `resolve_random_engine` 은 `auto` 에서도 Numba 를 유지한다. 기존 NumPy/Numba
  난수 스트림을 보존하기 위해서이며, Rust 난수를 쓰려면 `engine="rust"` 를 명시해야 한다.
- 콜백을 받는 함수(사용자 정의 `apply_func` 등)는 `callback_unsupported_with_rust()` 로 항상 Numba 에 남긴다.
- Rust 가용성은 `_rust_status` 에 캐시된다. 테스트에서 설정을 바꿨으면 `clear_engine_cache()` 와
  `vbt.settings.reset()` 을 teardown 에서 호출한다.

### Rust 엔진 (`rust/`)

PyO3 + maturin 으로 빌드되는 별도 패키지 `vectorbt-rust` 다. `rust/src/{generic,signals,returns,
indicators,labels,records,portfolio}.rs` 가 Python 서브패키지와 1:1 로 대응하고 `lib.rs` 에서 서브모듈을 등록한다.
새 커널을 추가하는 순서는 `rust/README.md` 의 "New kernels" 절을 따른다. 요약하면 Numba 를 참조 구현으로 두고,
같은 인자 순서와 반환 형태로 Rust 를 구현하고, `dispatch.py` 래퍼를 추가하고, 패리티·폴백·명시적 오류·
메모리 레이아웃(C/F order) 테스트를 붙인 뒤 벤치마크 케이스를 등록한다.

### pandas 액세서 등록 (`vectorbt/root_accessors.py`)

`pd.Series.vbt` / `pd.DataFrame.vbt` 가 진입점이며, 하위 네임스페이스는 `@register_series_vbt_accessor("returns")`
같은 데코레이터로 붙는다(`vbt.signals`, `vbt.returns`, `vbt.ohlcv`, `vbt.px`). 액세서는 **캐시되지 않으므로**
`df.vbt` 를 두 번 호출하면 객체가 두 번 생성된다. 액세서 상속 계층은 `Base → Generic → Signals/Returns/OHLCV` 이므로
Generic 메서드는 하위 네임스페이스에서도 그대로 쓸 수 있다.

### 브로드캐스팅과 ArrayWrapper

vectorbt 의 핵심 관례는 "여러 파라미터 조합 = 여러 열" 이다. `vectorbt/base/reshape_fns.py` 의 `broadcast` 가
스칼라 · 1D · 2D 입력을 공통 2D 형태로 맞추고, `ArrayWrapper` 가 index · columns · freq 를 보관했다가 NumPy
결과를 다시 pandas 로 감싼다. Numba 커널은 항상 2D 배열(행 = 시간, 열 = 설정)을 가정하며 `_1d` 접미사 변형이
1D 를 처리한다. `flex_*` 계열 함수는 브로드캐스트 없이 스칼라/배열을 유연하게 읽는다.

### 전역 설정 (`vectorbt/_settings.py`)

`vbt.settings` 는 `SettingsConfig` 객체이며 최상위 키 `engine` 과 `numba` · `caching` · `broadcasting` · `array_wrapper` · `datetime` · `data` · `plotting` · `stats_builder` · `portfolio` · `messaging` 등 서브패키지별 섹션을 담는다.
대부분의 클래스는 `Configured` 를 상속해 생성 인자를 보관하므로 `.copy()` / `.replace()` /
pickle 이 동작한다.

## 테스트 관련 주의점

- `tests/conftest.py` 는 pandas 의 `assert_*_equal` 을 몽키패치해 datetime 단위(ns) · 문자열 dtype 차이를
  정규화한다. pandas 3 의 dtype 변화 때문이며, `rtol`/`atol` 이 있으면 정규화 없이 원래 오류를 그대로 낸다.
- 테스트 소스에 `engine="rust"` 문자열이 있으면 Rust 미설치 환경에서 자동으로 skip 된다. Rust 경로를 실제로
  검증하려면 로컬에서 `maturin develop --release` 를 먼저 실행해야 한다.
- `tests/utils.py` 의 `hash` 는 SHA-512 기반 결정적 해시이고, `record_arrays_close` 는 구조화 배열의
  필드별 근사 비교다.
- `.coveragerc` 는 플로팅 · 외부 데이터 소스 · Telegram 등 I/O 모듈을 커버리지에서 제외한다.

## 커밋 관례

리포의 기존 커밋은 영어이며 `fix(generic): ...` 형태의 conventional commit 접두어를 쓰는 경우가 있다.
전역 규칙(`~/.claude/CLAUDE.md`)은 한글 커밋 메시지를 요구하므로, 이 리포에서 커밋할 때는 어느 쪽을
따를지 사용자에게 확인한다.
