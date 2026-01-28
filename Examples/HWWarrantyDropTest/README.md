# HW Warranty Drop Test Automation System

**작성일**: 2026-01-23
**목적**: 대규모 낙하 시뮬레이션 자동화 시스템

---

## 시스템 개요

이 시스템은 **시나리오 기반 대규모 낙하 시뮬레이션**을 자동화합니다.

```
Scenario JSON 작성
    ↓
Configuration 생성 (KooDynaAutomaticSimulationScriptGenerator)
    ↓
대규모 병렬 실행 (LargeScaleDOEManager)
    ↓
누적 낙하 자동 처리 (KooMeshModifier → LS-DYNA → DYNAIN_TO_INITIAL)
```

---

## 주요 기능

### 1. Scenario 기반 설정
- **scenarios JSON**: GUI 친화적인 시나리오 정의 형식
- 전각도, MBD, 누적 낙하 등 다양한 analysisType 지원
- LHS, Fibonacci 등 각도 소스 자동 생성

### 2. 대규모 병렬 실행
- Slurm Array Job을 통한 수천 개 케이스 동시 실행
- runid 기반 독립적인 DOE 관리
- Lock 파일 기반 진행 상황 추적

### 3. 누적 낙하 자동화
- Step별 순차 실행 (1차 낙하 → 2차 낙하 → ...)
- DYNAIN_TO_INITIAL 자동 처리
- 각도 믹싱 전략 (same_angle, cyclic, random, opposite, custom)

### 4. DOE 확장
- Tolerance 기반 DOE 생성 (LHS, Grid, Random)
- Base 각도 + 작은 변화 → 다중 케이스

### 5. 커스텀 파라미터
- Height, InitialVelocity, InitialAngularVelocity 등
- case_txt_file로 직접 정의 가능

### 6. Direct Input 지원
- Node 모니터링 (변위, 속도, 가속도, 접촉력 등)
- 사용자 정의 *PARAMETER, *DEFINE_CURVE 등

---

## Quick Start

### 1. Scenario JSON 작성

```json
[
  {
    "id": "test_001",
    "name": "전각도 1차 낙하",
    "analysisType": "fullAngle",
    "params": {
      "faTotal": 100,
      "includeFace6": true,
      "includeEdge12": true,
      "includeCorner8": true,
      "angleSource": "lhs",
      "heightMode": "const",
      "heightConst": 1.5,
      "surface": "steelPlate"
    }
  }
]
```

### 2. Configuration 생성

```python
from occProject.Generators.KooCAEManager.KooDynaAutomaticSimulationScriptGenerator import KooDynaAutomaticSimulationScriptGenerator
import json

with open("scenarios.json", "r") as f:
    scenarios = json.load(f)

metadata = {
    "model_name": "TestModel",
    "stage": "DV1",
    "created_by": {
        "name": "koo.park",
        "email": "koo.park@samsung.com",
        "group": "CAE",
        "team": "HE"
    }
}

generator = KooDynaAutomaticSimulationScriptGenerator(scenarios, metadata)
generator.generate_for_all(output_dir="./configs")
```

### 3. 실행

```bash
python LargeScaleDOEManager.py \
    --config configs/runner_config_test_001.json \
    --nodes 10 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
```

**자원 계산**:
- 10 nodes × 4 jobs/node = **40개 동시 실행**
- 각 job은 16 CPU 사용
- 노드당: 4 × 16 = 64 CPU 사용 (128 코어 중 50% 활용)

---

## 핵심 모듈

### KooDynaAutomaticSimulationScriptGenerator.py
- **위치**: `occProject/Generators/KooCAEManager/`
- **기능**: scenarios JSON 파싱 및 runner_config.json 생성
- **출력**: runner_config.json, simulation_index.json

### LargeScaleDOEManager.py
- **위치**: `Examples/HWWarrantyDropTest/`
- **기능**: 대규모 병렬 실행 및 누적 낙하 자동화
- **특징**: Slurm Array Job, runid 관리, Lock 파일 추적

### CumulativeDesigner.py
- **위치**: `Examples/HWWarrantyDropTest/`
- **기능**: 사용자 정의 JSON → runner_config.json 변환 (대체 방법)
- **특징**: 각도 믹싱, DOE 확장

---

## 지원되는 Analysis Types

| Type | 설명 | 용도 |
|------|------|------|
| `fullAngle` | 전각도 (Face/Edge/Corner) | 표준 낙하 시험 |
| `fullAngleMBD` | MBD 기반 전각도 | MBD 연동 |
| `fullAngleCumulative` | 전각도 누적 낙하 | 기존 방식 |
| `multiRepeatCumulative` | 다중 반복 누적 | 특정 방향 반복 |
| `partialImpact` | 부분 충격 | 특정 부위만 |
| `mixedCumulative` | 복합 조건 누적 | DROP + THERM + VIB 등 |

---

## 각도 믹싱 전략

누적 낙하 시 각 Step에서 다른 각도를 사용하는 전략:

| 전략 | 설명 | 예시 |
|------|------|------|
| `same_angle` | 모든 Step 동일 각도 | 각도1 → 각도1 → 각도1 |
| `cyclic` | 순환 (DOE 내) | 각도1 → 각도2 → 각도3 |
| `random` | 랜덤 선택 | 각도1 → 각도4 → 각도2 |
| `opposite` | 반대 방향 | 각도1 → 반대 → 반대 |
| `custom_mapping` | 사용자 정의 | [1,3,2] |

자세한 내용: [docs/ANGLE_MIXING_STRATEGIES_GUIDE.md](docs/ANGLE_MIXING_STRATEGIES_GUIDE.md)

---

## 디렉토리 구조

```
Examples/HWWarrantyDropTest/
├── README.md                           # 이 파일
├── QUICK_START_GUIDE.md                # 빠른 시작 가이드
├── COMPLETE_SYSTEM_OVERVIEW.md         # 전체 시스템 개요
├── SIMULATION_AUTOMATION_WORKFLOW.md   # 워크플로우 상세
│
├── LargeScaleDOEManager.py             # 메인 실행 스크립트
├── CumulativeDesigner.py               # 설정 변환 스크립트
│
├── runner_config.json                  # 실행 설정 예제
├── MinimumModel.k                      # 베이스 모델 예제
│
└── docs/                               # 상세 문서
    ├── ANGLE_MIXING_STRATEGIES_GUIDE.md
    ├── WORKFLOW_VERIFICATION_REPORT.md
    ├── DIRECT_INPUT_WORKFLOW_GUIDE.md
    ├── NODE_MONITORING_EXAMPLES.md
    ├── CustomScenarios/                # 커스텀 시나리오 예제
    └── ...
```

---

## 실행 예제

### 예제 1: 단순 전각도 100 케이스

```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 5 \
    --jobs-per-node 8 \
    --ncpu-per-job 16
```

**동시 실행**: 5 × 8 = 40개

### 예제 2: Fibonacci 1000 × DOE 5 × 3 Steps

```json
{
  "params": {
    "faTotal": 1000,
    "angleSource": "lhs",
    "tolerance": {
      "mode": "enabled",
      "faceTolerance": 3.0
    },
    "cumulative": {
      "num_steps": 3,
      "angle_mixing": {
        "strategy": "cyclic",
        "cyclic_offset": 1
      }
    }
  }
}
```

총 **15,000 Jobs** (1000 × 5 × 3)

### 예제 3: 커스텀 파라미터 (높이, 속도)

```json
{
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt_file": {
      "file_path": "docs/CustomScenarios/custom_height_variation.txt"
    }
  }
}
```

---

## 진행 상황 확인

### Lock 파일로 진행 상황 추적

```bash
# 전체 완료 개수
find RUNDIR -name "Step*.lock" | wc -l

# 특정 runid 확인
ls RUNDIR/runid_00001/Step*/Step*.lock
```

### Slurm 작업 상태

```bash
# 실행 중인 작업
squeue -u $USER

# 완료된 작업
sacct -j <JOBID> --format=JobID,State,ExitCode
```

---

## 문서 가이드

### 빠른 시작
- [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - 빠른 시작 가이드
- [RESOURCE_PLANNING_GUIDE.md](RESOURCE_PLANNING_GUIDE.md) - HPC 자원 계획 및 설정

### 전체 시스템
- [COMPLETE_SYSTEM_OVERVIEW.md](COMPLETE_SYSTEM_OVERVIEW.md) - 전체 시스템 아키텍처
- [SIMULATION_AUTOMATION_WORKFLOW.md](SIMULATION_AUTOMATION_WORKFLOW.md) - 워크플로우 상세

### 기능별 상세 문서
- [docs/ANGLE_MIXING_STRATEGIES_GUIDE.md](docs/ANGLE_MIXING_STRATEGIES_GUIDE.md) - 각도 믹싱 전략
- [docs/DIRECT_INPUT_WORKFLOW_GUIDE.md](docs/DIRECT_INPUT_WORKFLOW_GUIDE.md) - Direct Input 기능
- [docs/NODE_MONITORING_EXAMPLES.md](docs/NODE_MONITORING_EXAMPLES.md) - Node 모니터링
- [docs/CustomScenarios/README.md](docs/CustomScenarios/README.md) - 커스텀 시나리오 예제
- [docs/WORKFLOW_VERIFICATION_REPORT.md](docs/WORKFLOW_VERIFICATION_REPORT.md) - 검증 보고서

---

## 주요 특징

### 확장성
- 수천 개 케이스 동시 실행 가능
- Slurm Array Job 활용 HPC 환경 최적화

### 유연성
- 다양한 각도 소스 (Fibonacci, LHS, MBD, Custom)
- DOE 확장 (Tolerance 기반)
- 커스텀 파라미터 지원

### 자동화
- KooMeshModifier → LS-DYNA → DYNAIN_TO_INITIAL 자동 연결
- Lock 파일 기반 진행 상황 추적
- runid 기반 독립적인 DOE 관리

### 추적 가능성
- simulation_index.json으로 runid → 각도 매핑
- 메타데이터 자동 저장
- Lock 파일로 실시간 진행 상황 확인

---

## 시스템 요구사항

- Python 3.7+
- Slurm (선택, 로컬 실행 모드 지원)
- KooMeshModifier
- LS-DYNA (MPI 버전 권장)

---

## 라이선스 및 연락처

**작성자**: koo.park
**이메일**: koo.park@samsung.com
**그룹**: CAE
**팀**: HE

**버전**: 2.0
**최종 수정**: 2026-01-23
