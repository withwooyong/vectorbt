# Session Handoff

> Last updated: 2026-09-10 18:33 (KST)
> Branch: `master`
> Latest commit: `e44510a` - Claude Code 용 프로젝트 가이드 CLAUDE.md 추가

## Current Status

`polakowo/vectorbt` 를 포크한 리포(`origin` = `withwooyong/vectorbt`)에 Claude Code 용 한글 `CLAUDE.md` 를
작성해 커밋했다. 코드 변경은 없고 문서만 추가된 상태이며, 작업 트리는 깨끗하다.

## Completed This Session

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | 리포 구조 조사 후 한글 `CLAUDE.md` 작성 (명령 · 계층 구조 · 엔진 디스패치 · 테스트 주의점 · 커밋 관례 충돌) | `e44510a` | `CLAUDE.md` |
| 2 | 인수인계 문서 생성 | (이번 커밋) | `CHANGELOG.md`, `HANDOFF.md` |

## In Progress / Pending

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | `CLAUDE.md` 가 새 세션에서 자동으로 읽히는지, 설명만으로 `tests/test_engine.py` 를 실행할 수 있는지 검증 | 미착수 | 검증 중 코드와 어긋나는 서술이 있으면 `CLAUDE.md` 를 고친다 |
| 2 | Codex(`~/.codex/config.toml`) · Gemini CLI(`~/.gemini/settings.json`) 설정 가져오기 | 보류 | `/import` 로 스캔 후 `/import --yes=<digest>` 로 적용. 사용자가 선택하지 않았음 |

## Key Decisions Made

- **CLAUDE.md 는 한글로 작성한다.** 사용자가 `/init` 인자로 명시했다.
- **커밋 메시지 언어 충돌을 파일에 명시했다.** 리포 기존 커밋은 영어(일부 conventional commit 접두어)이고
  전역 규칙(`~/.claude/CLAUDE.md`)은 한글을 요구한다. 이번 세션은 전역 규칙을 따라 한글로 커밋했고,
  `CLAUDE.md` 에는 "커밋 시 사용자에게 확인" 으로 적어 두었다.
- **아키텍처 설명은 엔진 디스패치에 비중을 두었다.** `nb.py`(Numba 참조 구현) → `dispatch.py`(엔진 중립 래퍼)
  → `accessors.py`(pandas API) 구조와 `auto` 폴백 · 난수 함수 예외 · 콜백 함수 예외는 여러 파일을 읽어야만
  알 수 있어 문서화 가치가 가장 높다고 판단했다.
- **CLAUDE.md 에 적은 이름은 실제 코드와 대조했다.** 작성 중 예시 테스트 클래스 이름(`TestAccessors`)과
  `vbt.settings` 의 실제 최상위 섹션 이름을 확인해 두 군데를 바로잡았다.

## Known Issues

- 핸드오프 수집 스크립트의 README drift 검사가 `DEBUG` · `NUMBA_DISABLE_JIT` 를 "README 에 없는 환경변수" 로
  보고했다. 확인 결과 `DEBUG` 는 `apps/candlestick-patterns/app.py` 의 예제 Dash 앱 설정이고,
  `NUMBA_DISABLE_JIT` 는 Numba 표준 환경변수를 `vectorbt/utils/checks.py` 가 읽는 것이다. 라이브러리 README 에
  환경변수 표가 없고 두 변수 모두 라이브러리 설정이 아니므로 **오탐으로 판단해 README 를 고치지 않았다.**
- git 이 `CLAUDE.md` 커밋 시 LF → CRLF 경고를 냈다. Windows `autocrlf` 설정에 따른 안내이며 내용에는 영향이 없다.

## Context for Next Session

- **사용자 의도**: 이 포크 리포에서 Claude Code 로 작업하기 위한 기반 문서(`CLAUDE.md`)를 갖추는 것이 목표였다.
  코드 수정 요청은 없었다.
- **리포 특성**: upstream 은 `polakowo/vectorbt` 이고 `origin` 은 사용자 포크다. `origin/master` 는 upstream 과
  같은 커밋(`34b6d59`)에 있었고, 이번 세션 커밋들이 그 위에 쌓였다. 사용자가 이번 세션에서 `master` 푸시를
  명시적으로 요청했다.
- **지킬 제약**: `master` 는 보호 브랜치이므로 푸시는 사용자의 명시적 요청이 있을 때만 한다. upstream 코드
  (`vectorbt/`, `rust/`, `tests/`)는 이번 세션에서 건드리지 않았고, 건드릴 이유도 아직 없다.
- **다음 세션 첫 작업 권장**: 새 세션에서 `CLAUDE.md` 내용만으로 `pytest tests/test_engine.py` 를 실행해 보고,
  설명이 부족하거나 틀린 부분을 `CLAUDE.md` 에 반영한다.

## Files Modified This Session

```
CLAUDE.md     | 133 +++ (신규, e44510a)
CHANGELOG.md  |  (신규, 이번 커밋)
HANDOFF.md    |  (신규, 이번 커밋)
```
