# 전체 시스템 개요

**최종 업데이트**: 2026-01-23
**상태**: 프로덕션 준비 완료

---

## 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    1. Scenario Definition                   │
│           (scenarios JSON or Custom JSON)                   │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│              2. Configuration Generation                    │
│      KooDynaAutomaticSimulationScriptGenerator.py          │
│         or CumulativeDesigner.py                            │
│                                                             │
│  Input:  scenarios_*.json                                   │
│  Output: runner_config.json                                 │
│          simulation_index.json                              │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│              3. Large-Scale Execution                       │
│             LargeScaleDOEManager.py                         │
│                                                             │
│  - runid 디렉토리 생성                                        │
│  - Slurm Array Job 제출                                      │
│  - Lock 파일 기반 진행 추적                                    │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│          4. Sequential Analysis (Per runid)                 │
│                                                             │
│  Step 1:  KooMeshModifier → LS-DYNA                        │
│  Step 2:  DYNAIN_TO_INITIAL → KooMeshModifier → LS-DYNA   │
│  Step 3:  DYNAIN_TO_INITIAL → KooMeshModifier → LS-DYNA   │
│  ...                                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 핵심 모듈

### 1. KooDynaAutomaticSimulationScriptGenerator.py

**위치**: `occProject/Generators/KooCAEManager/`

**기능**: scenarios JSON → runner_config.json 변환

**지원 analysisType**:
- `fullAngle`: 전각도 (Face/Edge/Corner)
- `fullAngleMBD`: MBD 기반 전각도
- `fullAngleCumulative`: 전각도 누적 낙하
- `multiRepeatCumulative`: 다중 반복 누적
- `partialImpact`: 부분 충격
- `mixedCumulative`: 복합 조건 (DROP + THERM + VIB)

**입력 예시** (scenarios JSON):
```json
[
  {
    "id": "scn_001",
    "name": "전각도 1차 낙하",
    "analysisType": "fullAngle",
    "params": {
      "faTotal": 100,
      "angleSource": "lhs",
      "heightMode": "const",
      "heightConst": 1.5
    }
  }
]
```

**출력**:
- `runner_config_scn_001.json`
- `simulation_index_scn_001.json`

---

### 2. CumulativeDesigner.py

**위치**: `Examples/HWWarrantyDropTest/`

**기능**: 사용자 정의 JSON → runner_config.json 변환 (대체 방법)

**특징**:
- 각도 믹싱 전략 지원 (same_angle, cyclic, random, opposite, custom_mapping)
- DOE 확장 (Tolerance 기반)
- Fibonacci, LHS, case_txt_file 등 다양한 각도 소스

**입력 예시**:
```json
{
  "project_name": "MyProject",
  "scenarios": [{
    "scenario_name": "Test",
    "angle_source": {
      "source_type": "fibonacci_lattice",
      "fibonacci_lattice": {"num_points": 100}
    },
    "cumulative": {
      "num_steps": 3,
      "mode_sequence": ["DROP", "DROP", "DROP"],
      "base_angle_index": 0,
      "angle_mixing": {
        "strategy": "cyclic",
        "cyclic_offset": 1
      }
    }
  }]
}
```

**실행**:
```bash
python CumulativeDesigner.py input.json output_runner_config.json
```

---

### 3. LargeScaleDOEManager.py

**위치**: `Examples/HWWarrantyDropTest/`

**기능**: 대규모 병렬 실행 및 누적 낙하 자동화

**주요 기능**:
- runid 기반 독립적인 DOE 관리
- Slurm Array Job 자동 제출
- Lock 파일 기반 진행 상황 추적
- Step별 순차 실행 (KooMeshModifier → LS-DYNA → DYNAIN_TO_INITIAL)

**실행 예시**:
```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 10 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
```

**자원 설정**:
- `--nodes`: 사용할 노드 수
- `--jobs-per-node`: 노드당 동시 실행 Job 수
- `--ncpu-per-job`: 각 Job이 사용할 CPU 수

**계산**:
- 동시 실행: 10 nodes × 4 jobs/node = **40개**
- 노드당 CPU 사용: 4 jobs × 16 CPU = 64 CPU (128 코어 중 50%)

**생성 구조**:
```
RUNDIR/
├── runid_00001/
│   ├── Step001/
│   │   ├── drop_attitude.txt
│   │   ├── MinimumModel_rotated.k
│   │   ├── dynain, d3plot*
│   │   └── Step001.lock
│   ├── Step002/
│   │   ├── dynaintoinitial.txt
│   │   ├── Initial.k
│   │   ├── drop_attitude.txt
│   │   ├── MinimumModel_rotated.k
│   │   ├── dynain, d3plot*
│   │   └── Step002.lock
│   └── Step003/
│       └── ...
├── runid_00002/
└── ...
```

---

## 각도 소스 (Angle Source)

### 지원되는 소스 타입

| 소스 타입 | 설명 | 케이스 수 |
|----------|------|----------|
| `fibonacci_lattice` | Fibonacci Lattice 균등 분포 | 사용자 지정 |
| `lhs` | Latin Hypercube Sampling | 사용자 지정 |
| `full_angle_26` | 전각도 26개 (Face 6 + Edge 12 + Corner 8) | 26 |
| `case_txt_file` | 커스텀 txt 파일 | 파일에 따라 |

### 예시: Fibonacci Lattice

```json
{
  "angle_source": {
    "source_type": "fibonacci_lattice",
    "fibonacci_lattice": {
      "num_points": 1000
    }
  }
}
```

### 예시: Case Txt File (커스텀 파라미터)

```json
{
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt_file": {
      "file_path": "custom_angles.txt"
    }
  }
}
```

**custom_angles.txt**:
```
EulerX,EulerY,EulerZ,Height,InitialVelocity_X
0,0,0,1000,5.0
45,30,0,1500,10.0
90,60,0,2000,15.0
```

---

## DOE 확장 (Tolerance)

Base 각도에서 작은 변화를 주어 추가 케이스를 생성합니다.

### 설정 예시

```json
{
  "tolerance": {
    "roll": {
      "tolerance": 5.0
    },
    "pitch": {
      "tolerance": 5.0
    },
    "doe_type": "lhs",
    "doe_count": 5
  }
}
```

**결과**: Base 각도 100개 → DOE 5개/각도 → 총 500개 케이스

---

## 각도 믹싱 전략

누적 낙하 시 각 Step에서 다른 각도를 사용하는 전략입니다.

| 전략 | 설명 | 예시 (DOE 5개, 3 Steps) |
|------|------|------------------------|
| `same_angle` | 모든 Step 동일 각도 | DOE1: 각도1 → 각도1 → 각도1 |
| `cyclic` | 순환 (base_idx + offset) | DOE1: 각도1 → 각도2 → 각도3 |
| `random` | 랜덤 선택 | DOE1: 각도1 → 각도4 → 각도2 |
| `opposite` | 반대 방향 (180도 회전) | DOE1: 각도1 → 반대 → 반대 |
| `custom_mapping` | 사용자 정의 시퀀스 | DOE1: [1,3,2] |

### 설정 예시

```json
{
  "cumulative": {
    "num_steps": 3,
    "mode_sequence": ["DROP", "DROP", "DROP"],
    "base_angle_index": 0,
    "angle_mixing": {
      "strategy": "cyclic",
      "cyclic_offset": 1
    }
  }
}
```

자세한 내용: [docs/ANGLE_MIXING_STRATEGIES_GUIDE.md](docs/ANGLE_MIXING_STRATEGIES_GUIDE.md)

---

## 누적 낙하 워크플로우

### Step 1 (첫 낙하)

```
1. KooMeshModifier (DROP_ATTITUDE)
   - 입력: MinimumModel.k, drop_attitude.txt
   - 출력: MinimumModel_rotated.k (회전된 메시)

2. LS-DYNA 실행
   - 입력: MinimumModel_rotated.k
   - 출력: dynain, d3plot*, messag

3. Lock 파일 생성: Step001.lock
```

### Step 2+ (누적 낙하)

```
1. DYNAIN_TO_INITIAL
   - 입력: ../Step001/dynain
   - 출력: Initial.k (변형 상태)

2. KooMeshModifier (DROP_ATTITUDE)
   - 입력: Initial.k, drop_attitude.txt (새로운 각도)
   - 출력: MinimumModel_rotated.k (회전 + 변형)

3. LS-DYNA 실행
   - 입력: MinimumModel_rotated.k
   - 출력: dynain, d3plot*, messag

4. Lock 파일 생성: Step002.lock
```

---

## 실행 규모 예시

### 예시 1: 소규모 (150 Jobs)

- Fibonacci 10개
- DOE 5개/각도 (Tolerance ±3°)
- 3 Steps

**총 케이스**: 10 × 5 × 3 = **150 Jobs**

### 예시 2: 중규모 (15,000 Jobs)

- Fibonacci 1000개
- DOE 5개/각도
- 3 Steps

**총 케이스**: 1000 × 5 × 3 = **15,000 Jobs**

### 예시 3: 대규모 (150,000 Jobs)

- Fibonacci 10,000개
- DOE 5개/각도
- 3 Steps

**총 케이스**: 10,000 × 5 × 3 = **150,000 Jobs**

---

## Slurm 통합

### Array Job 제출

LargeScaleDOEManager는 모든 runid를 단일 Array Job으로 제출하며, **동시 실행 제한**을 설정합니다:

```bash
#!/bin/bash
#SBATCH --job-name=MyProject
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=04:00:00
#SBATCH --array=1-5000%40  # 5000개 DOE, 최대 40개 동시 실행

RUNID=$(printf "runid_%05d" $SLURM_ARRAY_TASK_ID)
cd RUNDIR/$RUNID

# Step 1 실행
cd Step001
<워크플로우 실행>
touch Step001.lock

# Step 2 실행 (Step 1 완료 대기)
while [ ! -f ../Step001/Step001.lock ]; do sleep 10; done
cd ../Step002
<워크플로우 실행>
touch Step002.lock

# Step 3 실행 (Step 2 완료 대기)
while [ ! -f ../Step002/Step002.lock ]; do sleep 10; done
cd ../Step003
<워크플로우 실행>
touch Step003.lock
```

### 진행 상황 추적

```bash
# 전체 완료 개수
find RUNDIR -name "Step*.lock" | wc -l

# 특정 Step 완료 개수
find RUNDIR -name "Step001.lock" | wc -l

# Slurm 작업 상태
squeue -u $USER
```

---

## Direct Input 지원

각도 없이 **직접 작성한 .k 파일**로 실행할 수 있습니다.

### 기능

- Node 모니터링 (변위, 속도, 가속도, 접촉력 등)
- 사용자 정의 *PARAMETER, *DEFINE_CURVE
- 커스텀 *DATABASE 설정

### 설정 예시

```json
{
  "direct_input": {
    "input_files": [
      "custom_model_1.k",
      "custom_model_2.k"
    ],
    "node_monitoring": {
      "nodes": [1000, 2000, 3000],
      "outputs": ["disp", "vel", "acc"]
    }
  }
}
```

자세한 내용: [docs/DIRECT_INPUT_WORKFLOW_GUIDE.md](docs/DIRECT_INPUT_WORKFLOW_GUIDE.md)

---

## 주요 출력 파일

### runner_config.json
- LargeScaleDOEManager 실행 설정
- 시나리오, 각도 소스, 누적 설정 포함

### simulation_index.json
- runid → 각도 매핑
- 메타데이터 (model_name, stage, created_by)

### Lock 파일
- Step 완료 표시
- 진행 상황 추적용

### LS-DYNA 출력
- `dynain`: 변형 상태 (다음 Step 입력)
- `d3plot*`: 후처리용 결과 파일
- `messag`: 로그

---

## 문서 가이드

### 메인 문서
- [README.md](README.md) - 시스템 소개 및 Quick Start
- [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - 빠른 시작
- [SIMULATION_AUTOMATION_WORKFLOW.md](SIMULATION_AUTOMATION_WORKFLOW.md) - 워크플로우 상세

### 기능별 상세 문서 (docs/)
- [ANGLE_MIXING_STRATEGIES_GUIDE.md](docs/ANGLE_MIXING_STRATEGIES_GUIDE.md) - 각도 믹싱
- [DIRECT_INPUT_WORKFLOW_GUIDE.md](docs/DIRECT_INPUT_WORKFLOW_GUIDE.md) - Direct Input
- [NODE_MONITORING_EXAMPLES.md](docs/NODE_MONITORING_EXAMPLES.md) - Node 모니터링
- [WORKFLOW_VERIFICATION_REPORT.md](docs/WORKFLOW_VERIFICATION_REPORT.md) - 검증 보고서
- [CustomScenarios/README.md](docs/CustomScenarios/README.md) - 커스텀 예제

---

## 시스템 요구사항

- Python 3.7+
- Slurm (선택, 로컬 실행 모드 지원)
- KooMeshModifier
- LS-DYNA (MPI 버전 권장)

---

## 기술 스택

- **Python**: 설정 생성, 워크플로우 관리
- **Bash**: Slurm 스크립트, 워크플로우 실행
- **JSON**: 설정 파일 형식
- **Slurm**: HPC 작업 스케줄링
- **KooMeshModifier**: 메시 회전, DYNAIN_TO_INITIAL
- **LS-DYNA**: 구조 해석 솔버

---

**작성자**: koo.park
**버전**: 2.0
**최종 수정**: 2026-01-23
