# Simulation Automation 전체 워크플로우

**작성일**: 2026-01-23
**목적**: scenarios JSON → runner_config.json → 대규모 병렬 실행 전체 워크플로우 설명

---

## 개요

전체 자동화 시스템은 **3단계**로 구성됩니다:

```
1. Scenario Definition (scenarios_*.json)
   - GUI 또는 수동으로 시나리오 정의
   - analysisType, angleSource, 누적 낙하 등 설정
   ↓
2. Configuration Generation (KooDynaAutomaticSimulationScriptGenerator.py)
   - scenarios JSON 파싱
   - runner_config.json + simulation_index.json 생성
   - runid 할당
   ↓
3. Automated Execution (LargeScaleDOEManager.py)
   - runner_config.json 읽기
   - runid별 디렉토리 생성
   - Slurm Array Job 제출
   - 순차 해석 실행 (KooMeshModifier → LS-DYNA → DYNAIN_TO_INITIAL → 반복)
   - Lock 파일로 진행 상황 추적
```

---

## Step 1: Scenario Definition (scenarios JSON)

### 입력 파일 형식

**파일명 예시**: `scenarios_2025-10-06T22-11-57-014Z.json`

```json
[
  {
    "id": "scn_001",
    "name": "전각도 1차 낙하 시뮬레이션",
    "analysisType": "fullAngle",
    "params": {
      "faTotal": 100,
      "includeFace6": true,
      "includeEdge12": true,
      "includeCorner8": true,
      "angleSource": "lhs",
      "heightMode": "const",
      "heightConst": 1.5,
      "surface": "steelPlate",
      "tolerance": {
        "mode": "disabled"
      }
    }
  },
  {
    "id": "scn_002",
    "name": "전각도 2차 누적 낙하",
    "analysisType": "fullAngle",
    "params": {
      "faTotal": 100,
      "angleSource": "usePrevResult",
      "angleSourceId": "scn_001",
      "heightMode": "const",
      "heightConst": 1.5,
      "surface": "steelPlate"
    }
  }
]
```

### 지원되는 analysisType

| Type | 설명 | 용도 |
|------|------|------|
| `fullAngle` | 전각도 (Face/Edge/Corner) | 표준 낙하 시험 |
| `fullAngleMBD` | MBD 기반 전각도 | MBD 시뮬레이션 결과 활용 |
| `fullAngleCumulative` | 전각도 누적 낙하 | 기존 방식 누적 낙하 |
| `multiRepeatCumulative` | 다중 반복 누적 낙하 | 특정 방향 반복 |
| `partialImpact` | 부분 충격 | 특정 부위만 |
| `mixedCumulative` | 복합 조건 누적 | DROP + THERM + VIB 등 |

### angleSource 옵션

| 옵션 | 설명 | 사용 시나리오 |
|------|------|--------------|
| `lhs` | Latin Hypercube Sampling | 1차 낙하, 통계적 샘플링 |
| `fromMBD` | MBD 시뮬레이션 결과 | MBD 연동 |
| `usePrevResult` | 이전 결과 참조 | 누적 낙하 (2차, 3차 등) |

### heightMode 옵션

| 모드 | 설명 | 파라미터 |
|------|------|----------|
| `const` | 고정 높이 | `heightConst: 1.5` (m) |
| `lhs` | LHS 샘플링 범위 | `heightMin: 0.5, heightMax: 1.5` (m) |

### surface 옵션

- `steelPlate` (강판)
- `pavingBlock` (보도블록)
- `concrete` (콘크리트)
- `wood` (나무)

---

## Step 2: Configuration Generation

### 실행 방법

```python
from occProject.Generators.KooCAEManager.KooDynaAutomaticSimulationScriptGenerator import KooDynaAutomaticSimulationScriptGenerator
import json

# scenarios JSON 로드
with open("scenarios_2025-10-06.json", "r") as f:
    scenarios = json.load(f)

# 메타데이터 정의
metadata = {
    "model_name": "GalaxyS25",
    "stage": "DV1",
    "created_by": {
        "name": "koo.park",
        "email": "koo.park@samsung.com",
        "group": "CAE",
        "team": "HE"
    }
}

# 생성기 초기화
generator = KooDynaAutomaticSimulationScriptGenerator(scenarios, metadata)

# runner_config.json 생성
output_files = generator.generate_for_all(output_dir="./")
print(f"생성된 파일: {output_files}")
```

### 생성되는 파일

1. **runner_config_scn_001.json**
   - LargeScaleDOEManager가 읽는 설정 파일
   - runid 목록
   - Step 시퀀스 정보
   - 각도 믹싱 전략

2. **simulation_index_scn_001.json**
   - 시뮬레이션 인덱스 (조회용)
   - runid → 각도 매핑
   - 메타데이터

### runner_config.json 구조 예시

```json
{
  "project_name": "GalaxyS25_scn_001",
  "scenarios": [
    {
      "scenario_name": "전각도_1차_낙하",
      "angle_source": {
        "source_type": "lhs",
        "lhs": {
          "num_samples": 100,
          "include_face6": true,
          "include_edge12": true,
          "include_corner8": true
        }
      },
      "cumulative": {
        "num_steps": 1,
        "mode_sequence": ["DROP"],
        "base_angle_index": 0,
        "angle_mixing": {
          "strategy": "same_angle"
        }
      }
    }
  ]
}
```

---

## Step 3: Automated Execution

### LargeScaleDOEManager 실행

```bash
python Examples/HWWarrantyDropTest/LargeScaleDOEManager.py \
    --config runner_config_scn_001.json \
    --base_model MinimumModel.k \
    --ncpu 16 \
    --memory 60000m \
    --partition normal \
    --time_limit 04:00:00
```

### 자동 생성되는 디렉토리 구조

```
RUNDIR/
├── runid_00001/
│   ├── Step001/
│   │   ├── drop_attitude.txt         # KooMeshModifier 입력
│   │   ├── MinimumModel_rotated.k    # KooMeshModifier 출력
│   │   ├── d3plot*, dynain           # LS-DYNA 출력
│   │   └── Step001.lock              # 완료 표시
│   ├── Step002/
│   │   ├── dynaintoinitial.txt       # DYNAIN_TO_INITIAL 입력
│   │   ├── Initial.k                 # DYNAIN_TO_INITIAL 출력
│   │   ├── drop_attitude.txt         # KooMeshModifier 입력
│   │   ├── MinimumModel_rotated.k    # KooMeshModifier 출력
│   │   ├── d3plot*, dynain           # LS-DYNA 출력
│   │   └── Step002.lock
│   └── Step003/
│       └── ...
├── runid_00002/
│   └── ...
└── runid_00100/
    └── ...
```

### 각 runid에서 실행되는 워크플로우

#### Step 1 (첫 낙하)

```bash
# 1. KooMeshModifier 실행 (DROP_ATTITUDE)
/opt/KooMeshModifier/run.sh --input="drop_attitude.txt"
# 출력: MinimumModel_rotated.k (EX_45_EY_30_H_1500.k 등)

# 2. 생성된 .k 파일 찾기
OUTPUT_K=$(find . -maxdepth 1 -name "*.k" -type f -printf "%T@ %p\n" | sort -rn | head -1 | cut -d" " -f2-)

# 3. LS-DYNA 실행
mpirun -np 16 /opt/lsdyna/bin/ls-dyna \
    i="$OUTPUT_K" \
    memory=60000m \
    ncpu=16
# 출력: dynain, d3plot*, messag, etc.

# 4. Lock 파일 생성
touch Step001.lock
```

#### Step 2+ (누적 낙하)

```bash
# 1. DYNAIN_TO_INITIAL 실행 (이전 dynain 변환)
PREV_DYNAIN="../Step001/dynain"
/opt/KooMeshModifier/run.sh --input="dynaintoinitial.txt"
# 출력: Initial.k

# 2. KooMeshModifier 실행 (DROP_ATTITUDE)
#    - Initial.k를 새로운 각도로 회전
/opt/KooMeshModifier/run.sh --input="drop_attitude.txt"
# 출력: MinimumModel_rotated.k (다른 각도)

# 3. 생성된 .k 파일 찾기
OUTPUT_K=$(find . -maxdepth 1 -name "*.k" -type f -printf "%T@ %p\n" | sort -rn | head -1 | cut -d" " -f2-)

# 4. LS-DYNA 실행
mpirun -np 16 /opt/lsdyna/bin/ls-dyna \
    i="$OUTPUT_K" \
    memory=60000m \
    ncpu=16
# 출력: dynain, d3plot*, messag, etc.

# 5. Lock 파일 생성
touch Step002.lock
```

### Slurm Array Job 관리

LargeScaleDOEManager는 모든 runid를 **Slurm Array Job**으로 제출합니다:

```bash
#!/bin/bash
#SBATCH --job-name=GalaxyS25_scn_001
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --time=04:00:00
#SBATCH --array=1-100  # 100개 DOE

# Array task ID → runid 매핑
RUNID=$(printf "runid_%05d" $SLURM_ARRAY_TASK_ID)
cd RUNDIR/$RUNID

# Step 1 실행
cd Step001
<워크플로우 실행>
cd ..

# Step 2 실행 (Step 1 완료 후)
while [ ! -f Step001/Step001.lock ]; do
    sleep 10
done
cd Step002
<워크플로우 실행>
cd ..

# Step 3 실행 (Step 2 완료 후)
while [ ! -f Step002/Step002.lock ]; do
    sleep 10
done
cd Step003
<워크플로우 실행>
```

---

## 각도 믹싱 전략

누적 낙하 시 **이전 Step과 다른 각도**를 사용하려면 `angle_mixing` 전략을 설정합니다.

### 지원되는 전략

| 전략 | 설명 | 예시 (DOE 5개, 3 Steps) |
|------|------|------------------------|
| `same_angle` | 모든 Step에서 동일 각도 | DOE1: Step1=각도1, Step2=각도1, Step3=각도1 |
| `cyclic` | 순환 (base_idx + offset) | DOE1: 각도1→각도2→각도3 |
| `random` | 랜덤 선택 | DOE1: 각도1→각도4→각도2 |
| `opposite` | 반대 방향 (180도 회전) | DOE1: 각도1→반대→반대 |
| `custom_mapping` | 사용자 정의 시퀀스 | DOE1: [1,3,2] |

자세한 내용은 [ANGLE_MIXING_STRATEGIES_GUIDE.md](ANGLE_MIXING_STRATEGIES_GUIDE.md) 참조.

---

## DOE 확장 (Tolerance)

Base 각도에서 **작은 변화**를 주어 추가 케이스를 생성합니다.

### Tolerance 설정 예시

```json
{
  "params": {
    "tolerance": {
      "mode": "enabled",
      "faceTolerance": 5.0,
      "edgeTolerance": 5.0,
      "cornerTolerance": 5.0
    }
  }
}
```

**결과**: Fibonacci 10개 → DOE 5개/각도 → 총 50개 케이스

### DOE 타입

| 타입 | 설명 |
|------|------|
| `lhs` | Latin Hypercube Sampling (추천) |
| `grid` | 균등 격자 |
| `random` | 완전 랜덤 |

---

## 실전 예시: Fibonacci 1000 × DOE 5 × 3 Steps

### Step 1: scenarios JSON 작성

```json
[
  {
    "id": "fib1000_doe5_3step",
    "name": "대규모 누적 낙하",
    "analysisType": "fullAngle",
    "params": {
      "faTotal": 1000,
      "includeFace6": true,
      "includeEdge12": true,
      "includeCorner8": true,
      "angleSource": "lhs",
      "heightMode": "const",
      "heightConst": 1.5,
      "surface": "steelPlate",
      "tolerance": {
        "mode": "enabled",
        "faceTolerance": 3.0,
        "edgeTolerance": 3.0,
        "cornerTolerance": 3.0
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
]
```

### Step 2: runner_config.json 생성

```python
generator = KooDynaAutomaticSimulationScriptGenerator(scenarios, metadata)
output_files = generator.generate_for_all(output_dir="./configs")
# 출력: configs/runner_config_fib1000_doe5_3step.json
```

### Step 3: 실행

```bash
python LargeScaleDOEManager.py \
    --config configs/runner_config_fib1000_doe5_3step.json \
    --nodes 20 \
    --jobs-per-node 8 \
    --ncpu-per-job 16
```

**자원 설정**:
- 20 nodes × 8 jobs/node = **160개 동시 실행**
- 5,000 runid ÷ 160 = 약 32 rounds
- 노드당 CPU: 8 × 16 = 128 CPU (100% 활용)

**결과**:
- 1000 Fibonacci 각도 × 5 DOE = 5,000 runid
- 각 runid에서 3 Steps 실행
- 총 **15,000 Jobs** (Slurm Array Job으로 병렬 실행)

---

## 진행 상황 추적

### Lock 파일

각 Step 완료 시 `.lock` 파일이 생성됩니다:

```bash
# 특정 runid의 진행 상황 확인
ls RUNDIR/runid_00001/Step*/Step*.lock

# 전체 진행 상황 통계
find RUNDIR -name "Step*.lock" | wc -l
```

### Slurm 작업 상태

```bash
# 실행 중인 Array Jobs 확인
squeue -u $USER

# 특정 작업 상세 정보
squeue -j <JOBID> --array

# 완료된 작업 확인
sacct -j <JOBID> --format=JobID,State,ExitCode
```

---

## 커스텀 파라미터 (Height, InitialVelocity 등)

scenarios JSON에서 지원하지 않는 **추가 파라미터**가 필요한 경우, **case_txt_file**을 직접 사용할 수 있습니다.

### 예시: 다양한 높이 + 초기 속도

**custom_cases.txt**:
```
# Height, InitialVelocity_X, InitialVelocity_Y, InitialVelocity_Z
EulerX,EulerY,EulerZ,Height,InitialVelocity_X,InitialVelocity_Y,InitialVelocity_Z
0,0,0,1000,5.0,0.0,0.0
0,0,0,1500,10.0,0.0,0.0
0,0,0,2000,15.0,0.0,0.0
```

**runner_config.json**:
```json
{
  "scenarios": [
    {
      "scenario_name": "Custom_Parameters",
      "angle_source": {
        "source_type": "case_txt_file",
        "case_txt_file": {
          "file_path": "custom_cases.txt"
        }
      },
      "cumulative": {
        "num_steps": 3,
        "mode_sequence": ["DROP", "DROP", "DROP"],
        "base_angle_index": 0,
        "angle_mixing": {
          "strategy": "same_angle"
        }
      }
    }
  ]
}
```

더 많은 예시는 [CustomScenarios/README.md](CustomScenarios/README.md) 참조.

---

## 전체 워크플로우 요약

### 1단계: 시나리오 정의
- GUI 또는 수동으로 `scenarios_*.json` 작성
- analysisType, angleSource, tolerance, cumulative 등 설정

### 2단계: 설정 생성
```python
from occProject.Generators.KooCAEManager.KooDynaAutomaticSimulationScriptGenerator import KooDynaAutomaticSimulationScriptGenerator

generator = KooDynaAutomaticSimulationScriptGenerator(scenarios, metadata)
generator.generate_for_all(output_dir="./configs")
```
- `runner_config_*.json` 생성
- `simulation_index_*.json` 생성

### 3단계: 자동 실행
```bash
python LargeScaleDOEManager.py \
    --config configs/runner_config_*.json \
    --nodes 10 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
```

**파라미터 설명**:
- `--nodes`: 사용할 노드 수 (기본: 1)
- `--jobs-per-node`: 노드당 동시 Job 수 (기본: 1)
- `--ncpu-per-job`: 각 Job의 CPU 수 (기본: 16)
- runid 디렉토리 생성
- Slurm Array Job 제출
- 각 runid에서 순차 해석:
  1. **KooMeshModifier** (DROP_ATTITUDE) → .k 생성
  2. **LS-DYNA** → dynain, d3plot 생성
  3. **DYNAIN_TO_INITIAL** (Step 2+) → Initial.k 생성
  4. **반복**

### 4단계: 결과 분석
- Lock 파일로 진행 상황 추적
- d3plot 파일로 결과 후처리
- dynain으로 변형 상태 확인

---

## 관련 문서

- [COMPLETE_SYSTEM_OVERVIEW.md](COMPLETE_SYSTEM_OVERVIEW.md) - 전체 시스템 개요
- [ANGLE_MIXING_STRATEGIES_GUIDE.md](ANGLE_MIXING_STRATEGIES_GUIDE.md) - 각도 믹싱 전략 상세
- [WORKFLOW_VERIFICATION_REPORT.md](WORKFLOW_VERIFICATION_REPORT.md) - 워크플로우 검증 보고서
- [CustomScenarios/README.md](CustomScenarios/README.md) - 커스텀 시나리오 예제
- [DIRECT_INPUT_WORKFLOW.md](DIRECT_INPUT_WORKFLOW.md) - Direct Input 기능

---

## 자주 묻는 질문 (FAQ)

### Q1: scenarios JSON과 runner_config.json의 차이는?

- **scenarios JSON**: 사람이 작성하는 **입력 형식** (GUI 친화적)
- **runner_config.json**: LargeScaleDOEManager가 읽는 **실행 설정** (runid 포함)

### Q2: 왜 2단계로 나뉘나요?

1. **Scenario Definition**: 비즈니스 로직 (어떤 시뮬레이션을 할지)
2. **Execution**: 기술 구현 (어떻게 병렬로 실행할지)

분리하면 GUI/API와 실행 엔진을 독립적으로 개발할 수 있습니다.

### Q3: runid는 언제 생성되나요?

`KooDynaAutomaticSimulationScriptGenerator.generate_runids_for_all()` 실행 시 자동 생성됩니다.

### Q4: 누적 낙하에서 각도를 어떻게 바꾸나요?

`angle_mixing` 전략을 설정하면 됩니다:
- `same_angle`: 동일 각도 반복
- `cyclic`: 순환 (DOE 내에서)
- `random`: 랜덤
- `opposite`: 반대 방향
- `custom_mapping`: 사용자 정의

### Q5: 커스텀 파라미터 (높이, 속도 등)는 어떻게 설정하나요?

`case_txt_file`을 사용하여 직접 정의할 수 있습니다. [CustomScenarios/README.md](CustomScenarios/README.md) 참조.

### Q6: Slurm이 없으면 어떻게 실행하나요?

LargeScaleDOEManager는 **로컬 실행 모드**도 지원합니다:
```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --base_model MinimumModel.k \
    --local  # Slurm 없이 순차 실행
```

---

**작성자**: koo.park
**버전**: 1.0
**최종 수정**: 2026-01-23
