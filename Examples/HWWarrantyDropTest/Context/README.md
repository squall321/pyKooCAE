# Context 폴더 소개

이 폴더는 **누적 낙하 자동화 프로젝트**의 대화 히스토리와 컨텍스트를 버전별로 관리합니다.

## 목적

- 새 대화 세션에서 프로젝트를 이어갈 때 필요한 컨텍스트 제공
- 프로젝트 진행 상황을 버전별로 추적
- 주요 결정사항과 기술적 발견사항 기록

## 파일 구조

```
Context/
├── README.md                           (본 파일)
├── CumulativeDrop_Context_v1.0.md     (초기 구현)
├── CumulativeDrop_Context_v2.0.md     (DROP MODE V2 설계)
├── CumulativeDrop_Context_v2.1.md     (워크플로 검증 및 계획 업데이트)
└── CumulativeDrop_Context_v3.0.md     (Simulation Automation 통합, HPC 자원 제어)
```

## 사용 방법

### 새 대화에서 프로젝트 이어가기

1. 가장 최신 버전의 Context 파일을 읽기
2. "Quick Start" 섹션의 핵심 파일들 확인
3. "Current Status" 섹션에서 현재 진행 상황 파악
4. "Next Steps" 섹션에서 다음 작업 확인

### Context 파일에 포함되는 내용

- **프로젝트 개요**: 목적, 배경
- **아키텍처**: 시스템 구조, 주요 컴포넌트
- **핵심 파일 목록**: 읽어야 할 파일들과 위치
- **주요 결정사항**: 중요한 설계 결정과 이유
- **기술적 발견사항**: 코드 조사에서 발견한 사실들
- **현재 상태**: 구현 완료된 것과 남은 작업
- **다음 단계**: 우선순위가 높은 작업들

## 버전 히스토리

| 버전 | 날짜 | 주요 내용 | 파일 |
|------|------|----------|------|
| v1.0 | 2026-01-22 | Phase 1-4 구현 (Single/Mixed Cumulative) | CumulativeDrop_Context_v1.0.md |
| v2.0 | 2026-01-22 | DROP MODE V2 설계 (Fibonacci, Tolerance, Templates) | CumulativeDrop_Context_v2.0.md |
| v2.1 | 2026-01-22 | 워크플로 검증, DROP_MODE_V2_PLAN 업데이트 | CumulativeDrop_Context_v2.1.md |
| v3.0 | 2026-01-23 | Simulation Automation 통합, HPC 자원 제어, 문서 정리 | CumulativeDrop_Context_v3.0.md |

## 최신 버전

**Current**: v3.0 (2026-01-23)
**File**: [CumulativeDrop_Context_v3.0.md](CumulativeDrop_Context_v3.0.md)

**주요 업데이트**:
- ✅ Simulation Automation 워크플로우 명확화 (scenarios JSON → runner_config.json)
- ✅ HPC 자원 제어 개선 (--nodes, --jobs-per-node, --ncpu-per-job)
- ✅ Slurm Array Job 동시 실행 제한 (--array=1-5000%40)
- ✅ 문서 정리 (메인 4개 + docs/ 상세 문서)
- ✅ 자원 계획 가이드 추가 (128코어 346노드 환경)

## v3.0 주요 변경사항

### 1. Simulation Automation 워크플로우 통합

**이해한 내용**:
```
scenarios JSON (GUI/수동 작성)
    ↓
KooDynaAutomaticSimulationScriptGenerator (파싱)
    ↓
runner_config.json (실행 설정)
    ↓
LargeScaleDOEManager (대규모 실행)
```

### 2. HPC 자원 제어

**변경 전**:
```bash
python LargeScaleDOEManager.py runner_config.json
# Slurm이 알아서 스케줄링
```

**변경 후**:
```bash
python LargeScaleDOEManager.py runner_config.json \
    --nodes 10 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
# 10 × 4 = 40개 동시 실행 (명시적 제어)
# Slurm: --array=1-5000%40
```

### 3. 문서 구조

**메인 폴더** (4개):
- README.md
- QUICK_START_GUIDE.md
- COMPLETE_SYSTEM_OVERVIEW.md
- SIMULATION_AUTOMATION_WORKFLOW.md

**docs/** (상세):
- ANGLE_MIXING_STRATEGIES_GUIDE.md
- DIRECT_INPUT_WORKFLOW_GUIDE.md
- NODE_MONITORING_EXAMPLES.md
- WORKFLOW_VERIFICATION_REPORT.md
- CustomScenarios/

**신규**:
- RESOURCE_PLANNING_GUIDE.md (자원 계획 및 최적화)

---

**관리**: Claude Code (Sonnet 4.5)
**프로젝트**: 누적 낙하 자동화 (Cumulative Drop Automation)
**상태**: 프로덕션 준비 완료
