# Changelog

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/).

## [Unreleased]

### Added
- (new features)

### Changed
- (modifications to existing features)

### Fixed
- (bug fixes)

### Removed
- (removed features)

---

## [2026-09-10] Session Summary

### Added
- Claude Code 용 프로젝트 가이드 `CLAUDE.md` 를 한글로 추가. 빌드·테스트·벤치마크·문서 명령, 서브패키지 계층, `nb`/`dispatch`/`accessors` 3층 구조, Numba-Rust 엔진 해석 규칙, 테스트 픽스처 주의점을 담음 (`e44510a`)
- 세션 인수인계 문서 `CHANGELOG.md` · `HANDOFF.md` 추가 (`c57b8fc`)

### Changed
- `CLAUDE.md` 를 실측 결과로 보정. 가상환경 안내, plotly 7 비호환(`scattermapbox` 제거)과 `plotly<7` 우회, Rust 엔진 설치 경로 두 가지(PyPI 휠 / 로컬 빌드)와 휠이 master 보다 오래된 문제, 벤치마크 출력 위치, 엔진 버전 불일치 동작, `vbt.px` · `vbt.ohlcv` 액세서 예외, conftest 의 skip 정규식, 엔진 테스트 예상 결과 수치를 반영 (`2d6d8da`)
