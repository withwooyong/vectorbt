# Session Handoff

> Last updated: 2026-09-10 18:54 (KST)
> Branch: `master`
> Latest commit: `2d6d8da` - CLAUDE.md 를 실측 결과로 보정: plotly 7 호환 · Rust 설치 경로 · 액세서 예외 · skip 기준

## Current Status

`polakowo/vectorbt` 포크(`origin` = `withwooyong/vectorbt`)의 한글 `CLAUDE.md` 를 실제 실행으로 검증해 보정하고
`origin/master` 에 푸시했다. upstream 코드는 건드리지 않았다. 리포 루트에 테스트용 `.venv` 가 생겼고(gitignore 대상),
이번 인수인계 커밋을 제외하면 작업 트리는 깨끗하다.

## Completed This Session

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | `.venv` 생성 후 `CLAUDE.md` 의 명령만으로 `pytest tests/test_engine.py` 실행. Numba 만: 7 passed · 87 skipped, PyPI Rust 휠: 93 passed · 1 failed | (환경만, 커밋 없음) | `.venv/` |
| 2 | `CLAUDE.md` 의 서술 전부를 코드와 대조하고 어긋난 4개 절 보정 | `2d6d8da` | `CLAUDE.md` |
| 3 | `origin/master` 푸시 (사용자 명시 승인) | — | — |
| 4 | 인수인계 문서 갱신 | (이번 커밋) | `CHANGELOG.md`, `HANDOFF.md` |

## In Progress / Pending

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | plotly 7 비호환 근본 수정 | 미착수, 승인 필요 | `vectorbt/templates/{light,dark}.json` 의 `scattermapbox` 를 `scattermap` 으로 바꾸거나 `pyproject.toml` 에 `plotly<7` 상한. upstream 코드 변경이므로 사용자가 방안을 골라야 한다 |
| 2 | Rust 로컬 빌드로 `test_rust_rolling_std_stability` 통과 확인 | 보류 | 이 PC 에 cargo 가 없다. Rust 소스를 고칠 계획이 생길 때만 의미가 있다 |
| 3 | Codex(`~/.codex/config.toml`) · Gemini CLI(`~/.gemini/settings.json`) 설정 가져오기 | 보류 | `/import` 로 스캔 후 `/import --yes=<digest>` 로 적용. 사용자가 선택하지 않았음 |

## Key Decisions Made

- **코드는 고치지 않고 문서만 고쳤다.** 사용자 지시가 "코드와 어긋나는 서술이 있으면 CLAUDE.md 를 고쳐라" 였으므로,
  plotly 7 비호환은 `CLAUDE.md` 에 우회법과 근본 수정 후보를 적고 결정은 사용자에게 넘겼다.
- **Rust 는 PyPI 휠로만 검증했다.** cargo 가 없어 로컬 빌드가 불가능했고, 휠로도 93개가 통과해 디스패치 서술은
  충분히 검증됐다고 판단했다. 실패 1개는 휠이 오래된 탓임을 커밋 f989752 의 변경 파일로 확인했다.
- **커밋 메시지는 한글.** 직전 세션 결정을 유지했다. 푸시는 사용자가 "1"(권장안 선택)로 명시 승인한 뒤에만 했다.
- **미추적 `AGENTS.md` 는 건드리지 않았다.** 다른 도구가 만든 파일이며 사용자가 지시하기 전에는 손대지 말라고 했다.

## Known Issues

- **plotly 7.0 에서 `import vectorbt` 실패.** `pyproject.toml` 이 `plotly>=4.12.0` 으로만 제한하는데 plotly 7 이
  `scattermapbox` 를 제거해 `_settings.py` 의 `register_template` 이 `ValueError` 로 죽는다. 새 환경은 반드시
  `pip install "plotly<7"` 이 필요하다. CI(`uv pip install`)도 같은 이유로 깨질 가능성이 높다.
- **PyPI `vectorbt-rust==1.1.0` 휠이 master 보다 오래됐다.** 커밋 f989752 가 `rust/src/generic.rs` 를 고쳤지만
  버전을 올리지 않아 휠과 소스가 같은 1.1.0 을 달고 있다. `test_rust_rolling_std_stability` 1개가 실패한다.
- README drift 검사가 `DEBUG` · `NUMBA_DISABLE_JIT` 를 다시 보고했다. 직전 세션과 같은 오탐(예제 앱 설정 ·
  Numba 표준 변수)이라 README 는 고치지 않았다.
- git 이 `CLAUDE.md` 에 LF → CRLF 경고를 낸다. Windows `autocrlf` 안내이며 내용에는 영향이 없다.

## Context for Next Session

- **사용자 의도**: 이 포크에서 Claude Code 로 작업할 기반 문서를 갖추는 것이 목표였고, 이번 세션은 그 문서가
  실제로 동작하는지 검증하는 단계였다. 검증은 끝났다.
- **환경**: 리포 루트 `.venv` (Python 3.14.6, `plotly<7` 고정, `vectorbt-rust` PyPI 휠 설치). 테스트는
  `.venv/Scripts/python -m pytest ...` 로 돌린다. 전역 Python 3.14 에는 numpy 조차 없다.
- **지킬 제약**: `master` 는 보호 브랜치이므로 푸시는 명시적 요청이 있을 때만 한다. upstream 코드(`vectorbt/`,
  `rust/`, `tests/`)를 고치는 일은 사용자 승인이 필요하다. `AGENTS.md` 는 지시 전에는 건드리지 않는다.
- **다음 세션 첫 작업 권장**: Pending 1(plotly 7 근본 수정). 두 방안을 비교해 권장안을 먼저 제시하고, 사용자가
  고른 뒤에 코드를 고친다. 고친 뒤 `plotly>=7` 환경에서 `import vectorbt` 와 `tests/test_engine.py` ·
  `tests/test_plotting.py` 를 통과시킨다.

## Files Modified This Session

```
CLAUDE.md     | 38 +++++++++++++++++++++++++++++++------- (2d6d8da)
CHANGELOG.md  | (이번 커밋)
HANDOFF.md    | (이번 커밋)
```
