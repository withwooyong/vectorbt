# Codex 팀 운영 설정 WBS

목적: vectorbt에 Astra 팀장과 작업별 팀원 모델·추론 강도, 컨텍스트 관리 규칙을 적용한다. 현재 판단: vectorbt 적용·설정 로드 검증·독립 검토를 완료했고 ted-startup에도 프로젝트별 지침을 보존하면서 적용할 수 있다. 범위: vectorbt 로컬 설정 적용 및 ted-startup 적용 가능성의 읽기 전용 검토. 한계: 실행 중인 세션의 모델 변경, 전역 설정 변경, ted-startup 수정, 커밋·푸시는 포함하지 않는다.

진행률: **100%** · 완료 **4/4** · 남은 작업: 요청 범위 내 없음 · 차단: 없음.

아래 표는 기존 WBS 템플릿의 의존성·담당·완료 기준을 유지한다. 진행률은 검증 완료한 가중치 합을 전체 가중치로 나눈 값이다.

| ID | 작업·산출물 | 담당·모델 | 선행 | 완료 기준 | 가중치 | 상태 |
| --- | --- | --- | --- | --- | --- | --- |
| W1 | 현재 설정·범위·공식 설정 확인 | 메인·Astra | 없음 | 기존 변경 및 지원 설정 확인 | 1 | 완료 |
| W2 | `.codex/config.toml`, `AGENTS.md` | 메인·Astra | W1 | 설정 작성 및 TOML·정합성 검사 | 2 | 완료 |
| W3 | ted-startup 적용 가능성 검토 | 팀원·Terra medium + 메인 | W1 | 지침·설정 근거 확인, 수정 없이 결론 기록 | 1 | 완료 |
| W4 | 독립 검토 및 최종 통합 | 검토 팀원·Sol high + 메인 | W2, W3 | 지적 해결, diff 및 설정 로드 검사 | 1 | 완료 |

## 판단과 검증 기록

- 선택·가정: 사용자가 승인한 추천안에 따라 Astra high를 팀장 기본값으로 설정한다. 팀원 기본값은 Sol medium이고, 작업별 모델·effort는 위임 시 명시한다. 동시 팀원은 최대 3명이며 실행 환경의 더 낮은 한도가 우선한다.
- 모델 가용성: 이 세션에서 제공되는 `gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`를 기준으로 한다. API 문서에 나오는 다른 모델을 자동 대체하지 않는다.
- 병렬 배정: 메인은 vectorbt 설정·지침·WBS를 소유한다. Terra는 ted-startup을 읽기 전용으로 검토한다. Sol은 작성된 결과를 독립 검토하며 파일을 수정하지 않는다.
- 기존 변경 보존: 작업 시작 시 존재한 `HANDOFF.md`, 연구 실행 코드 및 미추적 연구 산출물은 변경 범위 밖이다.
- 검증: 설치된 CLI는 `codex-cli 0.154.0`. `.venv/Scripts/python.exe`의 `tomllib`으로 TOML 파싱 및 모델·effort·팀원 수를 검사하여 통과했다. `git diff --check`도 통과했다. `codex --strict-config doctor --json`은 종료 코드 0, `config.load=ok`를 반환했다. 진단 전체에는 기존 환경 경고가 있으므로 전체 환경 정상으로 해석하지 않는다. 이 진단은 현재 대화의 실행 시 오버라이드를 검사하지 않는다.
- 실제 로드값: 별도 로컬 `codex app-server --stdio --strict-config` 프로세스의 `config/read`에 `cwd=C:\Users\aeby\vscode\stock\vectorbt`, `includeLayers=true`를 전달했다. 응답에서 Astra high, 팀원 기본 Sol medium, 팀원 한도 3, agents enabled를 확인했다. `origins.model_reasoning_effort`는 프로젝트 `.codex`를 가리켰다. 모델 호출·세션 생성 없이 설정만 읽고 검사 프로세스를 종료했다. 이는 현재 Orca 대화가 재설정되었다는 뜻은 아니다.
- 검사 방법 조정: `codex --strict-config features list`는 해당 하위 명령이 strict-config를 지원하지 않아 실패했고, 지원되는 `doctor` 명령으로 변경하여 검사했다. 설정·운영 문서 변경이므로 백테스트 전체 테스트와 사이트 빌드는 실행하지 않았다.
- 적용 한계: 프로젝트 설정은 신뢰된 프로젝트에서 로드된다. 호스트의 실행 시 오버라이드가 우선할 수 있으므로 파일 설정과 실제 세션의 모델·effort를 구분한다. 새 세션에서 실제 적용값을 확인한다.
- 범위 변경: 없음. ted-startup은 검토만 수행한다.
- 독립 검토: Sol high의 읽기 전용 검토에서 지적 사항 없음. 설정 키, fork와 모델 오버라이드 규칙, 작업 범위, ted-startup 근거, 진행률을 확인했다. 메인이 최종 변경 범위·문서 링크·세 파일의 공백 검사를 완료했다.

## ted-startup 최초 적용 전 검토 기록

**최초 검토에서는 적용 가능으로 판단했다.** 당시 ted-startup에는 `.codex/config.toml`이 없어 프로젝트 전용 설정과 Codex 운영 지침을 추가하도록 제안했다. 이후 사용자의 별도 적용 요청으로 ted-startup에도 적용·검증을 완료했다. 결과는 해당 저장소의 `docs/ops/codex-team-setup-wbs-2026-09-23.md`에 있다. 아래 근거와 작업 트리 수치는 최초 읽기 전용 검토 시점 기록이다.

프로젝트별로 보존해야 하는 경계는 다음과 같다. 경로는 `C:/Users/aeby/vscode/ted-startup` 기준이며 2026-09-23에 파일을 읽어 확인했다.

| 근거 | 적용 시 판단 |
| --- | --- |
| `AGENTS.md:3-11` | 기존 Codex 지침은 CLAUDE.md·WBS·HANDOFF 참조와 서비스별 구조를 안내한다. 여기에 모델 배분·컨텍스트 규칙을 보강하면 되며 vectorbt의 코드·수치 엔진 규칙은 복사하지 않는다. |
| `CLAUDE.md:38-45` | `agents/`, `pipeline/`, `/kickoff` 등은 과거 스캐폴딩이다. Codex 팀원 위임을 도입해도 이 체계를 재활성화하지 않는다. |
| `CLAUDE.md:82-109` | 상태 문서·WBS·인계의 팀장 소유 규칙을 유지한다. Claude 전용 스킬·hook의 동작을 Codex에서도 자동 보장된다고 간주하지 않는다. |
| `CLAUDE.md:9-15` | backend_py, backend_kiwoom, frontend 등 독립 트랙을 위임 경계로 삼을 수 있다. DB 스키마·공통 계약·배포 설정은 통합 담당이 조정한다. |

추천 배분은 복잡한 수집·DB·동시성 수정에 Sol high, 명확한 일반 구현·테스트에 Terra medium, 탐색·정형 점검에 Luna low/medium이다. 팀장은 Astra high로 결정과 검증을 통합한다. 실제 데이터 수집·정정은 ted-startup, 연구·전략 실행은 vectorbt라는 작업 경계를 유지한다. 모델 설정은 운영 데이터 수정이나 배포 권한을 추가하지 않는다.

검토 전후 ted-startup 작업 트리는 동일했다. 기존 수정 파일 4개와 미추적 evidence JSON 5개를 보존했다. 적용을 진행할 경우 프로젝트 설정과 Codex용 지침을 추가한 뒤 새 세션에서 모델·effort 적용값을 확인한다.

## 후속 작업: 완료 후 세션 전환 안내

목적: 검증된 작업을 끝낸 뒤 재개 정보를 남기고 clear와 다음 작업을 안내한다. 이 후속 작업은 위 설정 적용 4/4와 별도로 집계한다. 현재 **3/3 완료·100%**, 남은 작업과 차단 없음.

| ID | 산출물 | 담당 | 선행 | 완료 기준 | 가중치 | 상태 |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | 효과·제약 판단 | 메인 Astra | 없음 | 공식 동작과 조건부 이득 확인 | 1 | 완료 |
| S2 | 두 프로젝트 지침·재개 기록 | 메인 Astra + Terra medium | S1 | 안전한 종료 기준·시작 문장 반영 | 2 | 완료 |
| S3 | 독립 검토·문서 검사 | Sol high + 메인 | S2 | 충돌·누락 확인 및 최종 검사 | 1 | 완료 |

- 판단: 긴 대화의 무관한 입력을 줄일 수 있지만 인계·재조사 비용과 캐시 영향이 있어 절감률을 보장하지 않는다. 작업 중 초기화보다 검증된 작업 경계를 권한다.
- 범위: 두 프로젝트 `AGENTS.md`, 이 작업 WBS와 ted-startup의 기존 설정 WBS, 필요한 인계·상태 안내. 모델 설정·자동 압축·제품 코드는 변경하지 않는다.
- 재개 위치: `C:/Users/aeby/vscode/stock/vectorbt`, 브랜치 `research/ohlcv20-handoff-20260922`. ted-startup은 `C:/Users/aeby/vscode/ted-startup`, 브랜치 `research/ohlcv-admission-20260922`. 브랜치와 작업 트리는 재개 시 다시 확인한다.
- 작업 상태: 설정·운영 지침은 로컬 미커밋 상태다. vectorbt의 기존 연구 실행 코드·테스트·보고서 변경과 ted-startup의 수집·계수 스크립트·테스트·evidence 변경은 별도 작업이며 이 세션에서 검증하지 않았다. 병행 세션이 계속 수정할 수 있으므로 전체 작업 트리를 완료 상태로 간주하지 않는다.
- 검증: 두 저장소의 범위 한정 `git diff --check`, 작업 WBS 상대 링크·공백 검사가 통과했다. 제품 동작 변경이 없어 서비스·백테스트 테스트는 실행하지 않았다. Sol high 독립 검토의 지적 1건(완료된 설정 검토를 다음 작업으로 반복 추천)을 반영하여 실제 연구 재개 준비도 점검으로 교체했다. 다른 지적은 없다.
- 다음 작업 추천: 백테스트 재개 준비도를 읽기 전용으로 점검해 가장 먼저 해결할 연구 작업 1개를 정한다. ted-startup의 데이터 전달·정정 작업이 병행 중이므로 최신 전달 상태와 vectorbt 실행 의존성을 맞추는 것이 우선이다. 완료 기준은 확인한 근거·미확정 사항·첫 작업의 산출물과 검증 기준을 WBS로 정리하는 것이다.
- 재개 시작 문장: “vectorbt와 ted-startup의 AGENTS.md, 최신 연구 WBS·HANDOFF 및 git 상태를 확인해 백테스트 재개 준비도를 읽기 전용으로 점검해줘. 데이터 전달과 실행 의존성을 구분하고, 가장 먼저 할 연구 작업 1개를 근거·산출물·검증 기준과 함께 추천해줘. 운영 DB 변경·백테스트 실행·커밋·푸시는 하지 마.”

## 설정·세션 전환 근거

- [공식 CLI 명령 안내](https://learn.chatgpt.com/docs/developer-commands?surface=cli): `/clear`·`/new`는 새 대화, 화면 지우기는 기존 대화 유지.
- [공식 컨텍스트 관리 안내](https://learn.chatgpt.com/blog/mastering-codex-remote-for-engineering): 긴 대화의 집중도와 컨텍스트 관리.

- [공식 설정 문서](https://learn.chatgpt.com/docs/config-file/config-reference): 프로젝트 설정, 팀원 기본 모델·effort, 동시 팀원 수.
- [공식 서브에이전트 안내](https://learn.chatgpt.com/docs/agent-configuration/subagents): 작업 분할, 명시적 모델 선택, 컨텍스트 관리.
- 저장소 지침: [AGENTS.md](../../AGENTS.md), [WBS 템플릿](wbs-template.md).
