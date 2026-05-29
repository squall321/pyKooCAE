# 진동 하중 Massive Scenario 자동화 — KooChainRun 솔루션

KooChainRun에 VIBRATION_LOAD mode를 통합하여 캡/코일/회로 단위 진동 시뮬을 massive scenario로 자동화하는 솔루션 설계 + 구현 문서.

**핵심 원칙**: **Zero-Hardcode** — 모든 magic value, 기본값, 그룹 정의, curve 출처, DOE 패턴을 scenario/external config로 커버. 새 모드/source 추가 시 코드 1줄 등록만으로 가능한 구조.

## 문서 구조 (작성 완료)

| 파일 | 크기 | 내용 |
|---|---|---|
| [README.md](README.md) | 2.8KB | 이 파일 (인덱스 + 빠른 시작) |
| [PLAN.md](PLAN.md) | 7.3KB | 전체 개요 + 7 zero-hardcode 결정 요약 + 요구사항 매트릭스 |
| [DESIGN.md](DESIGN.md) | 22KB | 아키텍처 5 레이어 + Registry 패턴 + JSON Schema + 회귀 보장 |
| [PHASES.md](PHASES.md) | 19KB | P1~P6 단계별 구현 + 파일별 LOC + 검증 기준 |
| [EXAMPLES.md](EXAMPLES.md) | 21KB | 시나리오 3개 (캡/회로/조합) + curve library + amplitude 분배 |
| [DECISIONS_OPEN.md](DECISIONS_OPEN.md) | 8.3KB | **사용자 확정 필요 (Q1~Q9 + Zero-Hardcode A~G)** ⭐ |
| `IMPLEMENTATION.md` | 미작성 | P1~P6 구현 진행 로그 (구현 시작 시 작성) |
| `KOOMESHMODIFIER_BUDDY.md` | 미작성 | P5에서 KooMeshModifier 측 변경 (별도 PR) |

## 빠른 시작

### 1. **DECISIONS_OPEN.md** 답변 (시작 전 필수)
- Q1~Q9: 캡 인식 방법, 회로 정의 위치, DOE 패턴 우선순위 등
- Zero-Hardcode A~G: 7 채택안 confirm

답변 받으면 즉시 P1 구현 시작.

### 2. P1 구현 (인프라 + 최소 통합)
- `Runner/VibrationSource.py` (Registry + Decorator) 신규
- `Runner/StepConfigBuilder.build_vibration_load_block()` 추가
- `Runner/TemplateManager.py` SimulationMode.VIBRATION 등록
- 단위 테스트 + 회귀 검증 (Test_005 byte-level diff 0)

### 3. P2 구현 (회로 일괄 — ⭐ 사용자 핵심 요구)
- `@register_vibration_source("circuit_group")` 1줄 등록
- 평탄화 로직 + Example B 시뮬레이션 동작

### 4+ Phase 진행
PHASES.md 참조.

## 작업 흐름 원칙 (Karpathy)

| 원칙 | 적용 |
|---|---|
| Think before coding | 모든 설계 결정 코드 전 명문화 (이 docs 폴더 자체) |
| Simplicity first | YAGNI — 외부 components.yaml ref는 hook만 예약, 미구현 |
| Surgical changes | 기존 DROP/IMPACT/THERM 분기 무수정, elif 추가만 |
| Goal-driven | P1+P2 완료 시 "회로별 일괄 진동" 시나리오 동작 = 사용자 핵심 요구 충족 |

## 참고 자료 (이 repo)

- `Examples/vibration_load/` — KooMeshModifier VIBRATION_LOAD 원본 (3 예제 + README)
- `Examples/postprocess_pipeline/POSTPROCESS_OPTIONS.md` — 유사 reference 문서 패턴
- `docs/FullAngleDrop_HPC_Workflow.md` — DROP attitude HPC 자동화 reference
- `Runner/AngleSourceParser.py` — angle_source 패턴 (vibration_source 설계 모델)
- `Runner/ImpactPositionSource.py` — position_source 패턴

## 워크플로우 결과 (분석 출처)

| 트랜스크립트 | 내용 | 토큰 |
|---|---|---|
| `wv22n56yk.output` | 1차 분석: 5 lens (능력/통합패턴/도메인/DWI ref/사용자의도) + 3 verify (node지원/수정파일/회로메타) + synthesize | 566K |
| `wwjdjsl2e.output` | 2차 정밀화: 5 hardcode audit + 7 결정 design + 2 호환성 verify + synthesize | 408K |
| `w5aw9d1xn.output` | 3차 문서화: 5 md 동시 작성 | 305K |
