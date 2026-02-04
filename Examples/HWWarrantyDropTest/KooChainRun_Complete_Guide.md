# KooChainRun 시스템 완전 가이드

**Hardware Warranty Drop Test Automation**

---

**작성일**: 2026-01-29
**버전**: 1.0
**작성자**: CAE팀

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [KooChainRun 소개](#2-koochainrun-소개)
3. [시스템 아키텍처](#3-시스템-아키텍처)
4. [핵심 개념](#4-핵심-개념)
5. [각도 생성 알고리즘](#5-각도-생성-알고리즘)
6. [누적 낙하 시스템](#6-누적-낙하-시스템)
7. [Slurm 병렬 실행](#7-slurm-병렬-실행)
8. [사용 방법](#8-사용-방법)
9. [테스트 시나리오](#9-테스트-시나리오)
10. [디렉토리 구조](#10-디렉토리-구조)
11. [실행 예제](#11-실행-예제)
12. [문제 해결](#12-문제-해결)

---

## 1. 시스템 개요

### 1.1 목적

하드웨어 제품의 낙하 테스트 자동화를 위한 대규모 CAE 시뮬레이션 시스템입니다. 다양한 낙하 각도와 조건에서 제품의 내구성을 평가하여 보증 기준을 확립합니다.

### 1.2 주요 기능

- **다양한 낙하 각도 자동 생성**: Cuboid geometry, Fibonacci lattice, Pitch/Roll sweep
- **누적 낙하 시뮬레이션**: 변형 상태에서 연속 낙하 테스트
- **대규모 병렬 실행**: Slurm Array Job을 통한 수백 개 케이스 동시 실행
- **자동화된 워크플로**: KooMeshModifier → LS-DYNA 순차 실행
- **컨테이너 기반 실행**: Apptainer를 통한 환경 격리

### 1.3 적용 분야

- 스마트폰, 태블릿 낙하 테스트
- 노트북, 웨어러블 디바이스 내구성 평가
- 전자제품 보증 기준 수립
- 제품 설계 최적화

---

## 2. KooChainRun 소개

### 2.1 KooChainRun이란?

KooChainRun (KooChainRun)은 순차적 CAE 분석 워크플로를 자동화하는 CLI 도구입니다.

```
KooChainRun - KooChainRun CLI Tool
├── prepare  : scenario.json → runner_config.json 생성
└── submit   : Slurm Job 제출 및 실행
```

### 2.2 주요 명령어

#### prepare 명령

scenario.json (사용자 친화적 설정)을 runner_config.json (실행 설정)으로 변환합니다.

```bash
KooChainRun prepare scenario.json -o runner_config.json
```

**입력**: scenario.json
- 어떤 각도로 낙하할 것인가?
- 몇 회 연속 낙하할 것인가?
- 각도 믹싱 전략은?

**출력**: runner_config.json
- 각 runid별 정확한 각도
- 각 Step별 실행 모드
- 전체 실행 계획

#### submit 명령

runner_config.json을 읽어 Slurm Array Job을 제출하고 시뮬레이션을 실행합니다.

```bash
KooChainRun submit runner_config.json --nodes 2 --jobs-per-node 8
```

**동작**:
1. runid 디렉토리 사전 생성
2. metadata.json 저장
3. Slurm Array Job 제출
4. Step별 dependency 설정

### 2.3 워크플로

```
scenario.json
    ↓ (KooChainRun prepare)
runner_config.json
    ↓ (KooChainRun submit)
Slurm Array Jobs
    ↓
runid_00001/Step001/
runid_00002/Step001/
...
    ↓ (Step 1 완료 후)
runid_00001/Step002/
runid_00002/Step002/
...
```

---

## 3. 시스템 아키텍처

### 3.1 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     KooChainRun (KooChainRun)                     │
│  ┌─────────────┐              ┌──────────────────────┐     │
│  │  scenario   │──prepare────▶│  runner_config.json  │     │
│  │   .json     │              └──────────────────────┘     │
│  └─────────────┘                        │                   │
│                                          │ submit            │
│                                          ▼                   │
│                              ┌───────────────────────┐      │
│                              │   Slurm Controller    │      │
│                              └───────────────────────┘      │
└──────────────────────────────────────┬───────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
            ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
            │ Compute Node │   │ Compute Node │   │ Compute Node │
            │              │   │              │   │              │
            │ Array Job 1-8│   │ Array Job 9-16│   │Array Job 17-24│
            └──────────────┘   └──────────────┘   └──────────────┘
                    │                  │                  │
                    └──────────────────┴──────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
        ┌───────────────────────┐          ┌───────────────────────┐
        │  KooMeshModifier      │          │     LS-DYNA          │
        │  (Apptainer)          │──────▶   │  (Apptainer)         │
        │                       │          │                       │
        │ - 모델 회전           │          │ - 낙하 시뮬레이션    │
        │ - 각도 적용           │          │ - 충격 해석          │
        │ - K 파일 생성         │          │ - 결과 출력          │
        └───────────────────────┘          └───────────────────────┘
```

### 3.2 컴포넌트 설명

#### CumulativeDesigner
scenario.json을 읽어 runner_config.json을 생성하는 핵심 모듈

**역할**:
- 각도 소스 파싱 (cuboid, fibonacci, sweep)
- 누적 낙하 Step 시퀀스 생성
- 각도 믹싱 전략 적용
- DOE 확장 (tolerance 적용)

#### LargeScaleDOEManager
runner_config.json을 읽어 Slurm Job을 제출하고 실행을 관리

**역할**:
- runid 디렉토리 사전 생성
- metadata.json 저장
- Slurm Array Job 제출
- Step-by-Step 실행 관리

#### KooMeshModifier
LS-DYNA 모델을 회전하고 각도를 적용

**역할**:
- metadata.json에서 각도 읽기
- 모델 회전 (Roll, Pitch, Yaw)
- 경계 조건 적용
- K 파일 생성

#### LS-DYNA
실제 낙하 시뮬레이션 수행

**역할**:
- 명시적 동적 해석
- 충격 하중 계산
- 변형 및 응력 결과 출력
- DYNAIN 파일 생성 (Step 2+ 전달용)

### 3.3 데이터 흐름

```
scenario.json (사용자 작성)
    ↓
[CumulativeDesigner]
    ↓
runner_config.json (실행 설정)
    ↓
[LargeScaleDOEManager]
    ↓
runid_XXXXX/metadata.json (각도 정보)
    ↓
[Slurm Array Job]
    ↓
┌─────────────────────────────────────────┐
│ Step 1: DROP_FIRST                      │
│   KooMeshModifier → Step001.k           │
│   LS-DYNA → d3plot, dynain              │
└─────────────────────────────────────────┘
    ↓ (Step 1 완료 후)
┌─────────────────────────────────────────┐
│ Step 2: DROP_CUMULATIVE                 │
│   DYNAIN_TO_INITIAL → initial.k         │
│   KooMeshModifier → Step002.k           │
│   LS-DYNA → d3plot, dynain              │
└─────────────────────────────────────────┘
    ↓ (Step 2 완료 후)
┌─────────────────────────────────────────┐
│ Step 3: DROP_CUMULATIVE                 │
│   ...                                    │
└─────────────────────────────────────────┘
```

---

## 4. 핵심 개념

### 4.1 runid (Run ID)

각 독립적인 DOE 케이스를 식별하는 고유 ID입니다.

**형식**: `runid_00001`, `runid_00002`, ...

**특징**:
- 각 runid는 독립적으로 실행
- 하나의 runid는 1개 이상의 Step을 가질 수 있음
- runid 디렉토리는 사전 생성됨

**예시**:
```
/data/Test_001_Full26_1Step/
├── runid_00001/  (F1_Back, Roll=0°)
├── runid_00002/  (F2_Front, Roll=180°)
├── runid_00003/  (F3_Right, Pitch=-90°)
...
```

### 4.2 Step (단계)

하나의 runid 내에서 순차적으로 실행되는 시뮬레이션 단계입니다.

**Step 1**: 첫 낙하 (DROP_FIRST)
- 초기 상태에서 낙하
- 변형 없는 원본 모델 사용

**Step 2+**: 누적 낙하 (DROP_CUMULATIVE)
- 이전 Step의 변형 상태에서 낙하
- dynain → initial 변환 후 사용

**예시**:
```
runid_00001/
├── Step001/  (DROP_FIRST)
│   ├── Step001.k
│   ├── d3plot
│   └── dynain
├── Step002/  (DROP_CUMULATIVE)
│   ├── initial.k  (← Step001/dynain 변환)
│   ├── Step002.k
│   └── dynain
└── Step003/  (DROP_CUMULATIVE)
    └── ...
```

### 4.3 metadata.json

각 runid의 각도 정보와 Step 시퀀스를 저장하는 메타데이터 파일입니다.

**위치**: `runid_XXXXX/metadata.json`

**내용**:
```json
{
  "runid": "runid_00001",
  "doe_index": 0,
  "scenario_name": "Full_26_Directions_Single_Drop",
  "total_steps": 1,
  "base_angle": {
    "name": "F1_Back",
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
  },
  "steps": [
    {
      "step_number": 1,
      "mode": "DROP",
      "template": "DROP_FIRST",
      "angle": {
        "name": "F1_Back",
        "roll": 0.0,
        "pitch": 0.0,
        "yaw": 0.0
      },
      "input_file": "Step001.k",
      "dynain_source": null
    }
  ]
}
```

**활용**:
- KooMeshModifier가 각도 정보를 읽어 모델 회전
- Slurm 스크립트가 Step 정보를 읽어 실행 결정
- 결과 분석 시 각도 확인

### 4.4 doe_index

전체 DOE 케이스 중 이 runid의 인덱스입니다.

**범위**: 0부터 시작 (runid_00001 = doe_index 0)

**용도**:
- Slurm Array Job의 task ID 매핑
- 전체 DOE에서의 순서 식별

### 4.5 템플릿 타입

시뮬레이션 모드에 따른 템플릿 분류입니다.

**DROP_FIRST**: 첫 낙하
- 초기 상태 모델 사용
- dynain_source = null

**DROP_CUMULATIVE**: 누적 낙하
- 이전 Step의 변형 상태 사용
- dynain_source = "Step00X/dynain"

**DYNAIN_TO_INITIAL**: 변형 상태 → 초기 조건 변환
- Step 2+ 실행 전 자동 수행
- dynain 파일을 initial.k로 변환

---

## 5. 각도 생성 알고리즘

### 5.1 Cuboid Geometry

직육면체의 면, 모서리, 꼭짓점 방향으로 낙하 각도를 생성합니다.

#### 구성 요소

**Face (6개)**: 6개 면
```
F1_Back:   Roll=0°,    Pitch=0°     (뒷면)
F2_Front:  Roll=180°,  Pitch=0°     (앞면)
F3_Right:  Roll=0°,    Pitch=-90°   (오른쪽)
F4_Left:   Roll=0°,    Pitch=90°    (왼쪽)
F5_Top:    Roll=90°,   Pitch=0°     (위)
F6_Bottom: Roll=-90°,  Pitch=0°     (아래)
```

**Edge (12개)**: 12개 모서리
```
E01_Back_Right:  Roll=0°,   Pitch=-45°
E02_Back_Left:   Roll=0°,   Pitch=45°
E03_Front_Right: Roll=180°, Pitch=-45°
...
```

**Corner (8개)**: 8개 꼭짓점
```
C1_Back_Right_Top:    Roll=45°,  Pitch=-45°
C2_Back_Right_Bottom: Roll=-45°, Pitch=-45°
C3_Back_Left_Top:     Roll=45°,  Pitch=45°
...
```

#### 사용 예시

```json
{
  "angle_source": {
    "source_type": "cuboid_geometry",
    "cuboid_geometry": {
      "include_faces": true,
      "include_edges": true,
      "include_corners": true
    }
  }
}
```

**결과**: 26방향 (6 + 12 + 8)

### 5.2 Fibonacci Lattice

황금비를 이용하여 구형 표면에 균일 분포된 방향을 생성합니다.

#### 알고리즘

```python
φ = (1 + √5) / 2  # 황금비

for i in range(N):
    y = 1 - (2 * i) / (N - 1)
    radius = √(1 - y²)
    θ = 2π * i / φ

    x = radius * cos(θ)
    z = radius * sin(θ)

    # (x, y, z) → (Roll, Pitch, Yaw) 변환
```

#### 장점

- 격자 패턴보다 극점 집중 없음
- 방향 개수를 자유롭게 조정 가능
- 거의 완벽한 균일 분포

#### 사용 예시

```json
{
  "angle_source": {
    "source_type": "fibonacci_lattice",
    "fibonacci_lattice": {
      "num_directions": 100
    }
  }
}
```

**결과**: 100방향 균일분포

### 5.3 Pitching Sweep

Pitch 각도를 지정 범위에서 일정 간격으로 스윕합니다.

#### 사용 예시

```json
{
  "angle_source": {
    "source_type": "pitching_sweep",
    "pitching_sweep": {
      "pitch_start": -40,
      "pitch_end": 40,
      "pitch_step": 1,
      "roll": 0,
      "yaw": 0
    }
  }
}
```

**결과**: Pitch -40° ~ +40° (1° 간격, 81개)

#### 활용

- 전후 낙하 각도 민감도 분석
- 디스플레이 각도별 충격 평가
- 특정 방향 집중 테스트

### 5.4 Rolling Sweep

Roll 각도를 지정 범위에서 일정 간격으로 스윕합니다.

#### 사용 예시

```json
{
  "angle_source": {
    "source_type": "rolling_sweep",
    "rolling_sweep": {
      "roll_start": 0,
      "roll_end": 360,
      "roll_step": 10,
      "pitch": 0,
      "yaw": 0
    }
  }
}
```

**결과**: Roll 0° ~ 360° (10° 간격, 36개)

---

## 6. 누적 낙하 시스템

### 6.1 누적 낙하란?

하나의 제품이 변형된 상태에서 연속적으로 낙하하는 시뮬레이션입니다.

**현실 시나리오**:
1. 제품이 바닥에 떨어짐 (첫 낙하)
2. 변형된 상태로 다시 떨어짐 (2차 낙하)
3. 더 변형된 상태로 또 떨어짐 (3차 낙하)

### 6.2 Step-by-Step 실행

#### Step 1: DROP_FIRST

```
초기 모델 (변형 없음)
    ↓ KooMeshModifier
Step001.k (회전된 모델)
    ↓ LS-DYNA
d3plot (결과), dynain (변형 상태)
```

#### Step 2: DROP_CUMULATIVE

```
Step001/dynain (변형 상태)
    ↓ DYNAIN_TO_INITIAL
initial.k (변형된 초기 조건)
    ↓ KooMeshModifier
Step002.k (회전 + 변형)
    ↓ LS-DYNA
d3plot (결과), dynain (누적 변형)
```

#### Step 3: DROP_CUMULATIVE

```
Step002/dynain (누적 변형 상태)
    ↓ DYNAIN_TO_INITIAL
initial.k
    ↓ KooMeshModifier
Step003.k
    ↓ LS-DYNA
d3plot (최종 결과)
```

### 6.3 각도 믹싱 전략

각 Step마다 어떤 각도로 낙하할 것인지 결정하는 전략입니다.

#### same_angle (동일 각도)

모든 Step에서 동일한 각도로 낙하합니다.

```
runid_00001 (F1_Back):
  Step 1: F1_Back  (Roll=0°)
  Step 2: F1_Back  (Roll=0°)
  Step 3: F1_Back  (Roll=0°)
```

**용도**: 동일 방향 반복 낙하 내구성 평가

#### cyclic (순환)

각 Step마다 다음 각도로 순환합니다.

```
runid_00001 (F1_Back 시작):
  Step 1: F1_Back   (Roll=0°)
  Step 2: F2_Front  (Roll=180°)
  Step 3: F3_Right  (Pitch=-90°)

runid_00002 (F2_Front 시작):
  Step 1: F2_Front  (Roll=180°)
  Step 2: F3_Right  (Pitch=-90°)
  Step 3: F4_Left   (Pitch=90°)
```

**용도**: 다양한 방향 순차 낙하 검증

#### random (무작위)

각 Step마다 무작위 각도로 낙하합니다.

```json
{
  "angle_mixing": {
    "strategy": "random",
    "random_seed": 42
  }
}
```

**용도**: 예측 불가능한 낙하 패턴 시뮬레이션

#### opposite (반대 방향)

Step 2에서 반대 방향으로 낙하합니다.

```
runid_00001 (F1_Back):
  Step 1: F1_Back   (Roll=0°)
  Step 2: F2_Front  (Roll=180°, 반대 방향)
```

**용도**: 양방향 충격 평가

### 6.4 DYNAIN_TO_INITIAL

Step 2+ 실행 전 자동으로 수행되는 변환 작업입니다.

**입력**: `StepN/dynain` (LS-DYNA 변형 상태 파일)
**출력**: `Step(N+1)/initial.k` (초기 조건 파일)

**과정**:
1. dynain 파일에서 노드 좌표 읽기
2. 변형된 좌표를 초기 조건으로 설정
3. K 파일 형식으로 저장

---

## 7. Slurm 병렬 실행

### 7.1 Slurm Array Job

수백 개의 독립적인 케이스를 동시에 실행하는 메커니즘입니다.

#### 기본 개념

```bash
sbatch --array=1-26%8 job_script.sh
```

**의미**:
- `1-26`: Task ID 1부터 26까지 (26개 케이스)
- `%8`: 동시에 최대 8개만 실행

#### Task ID → runid 매핑

```bash
TASK_ID=$SLURM_ARRAY_TASK_ID
RUNID=$(printf "runid_%05d" $TASK_ID)

# TASK_ID=1  → runid_00001
# TASK_ID=2  → runid_00002
# ...
# TASK_ID=26 → runid_00026
```

### 7.2 Step별 Dependency

각 Step은 이전 Step이 완료된 후에만 실행됩니다.

#### Slurm Dependency 설정

```bash
# Step 1 제출
JOB1=$(sbatch --array=1-26%8 step1.sh | awk '{print $4}')

# Step 2 제출 (Step 1 완료 후)
JOB2=$(sbatch --dependency=afterok:$JOB1 --array=1-26%8 step2.sh | awk '{print $4}')

# Step 3 제출 (Step 2 완료 후)
JOB3=$(sbatch --dependency=afterok:$JOB2 --array=1-26%8 step3.sh | awk '{print $4}')
```

**동작**:
1. 모든 runid의 Step 1 실행
2. 모든 Step 1 완료 확인
3. 모든 runid의 Step 2 실행
4. 모든 Step 2 완료 확인
5. 모든 runid의 Step 3 실행

### 7.3 리소스 할당

#### 노드 기반 할당

```bash
KooChainRun submit runner_config.json \
  --nodes 4 \
  --jobs-per-node 8 \
  --ncpu-per-job 16
```

**의미**:
- 총 노드: 4개
- 노드당 동시 실행: 8개
- 총 동시 실행: 32개 (4 × 8)
- Job당 CPU: 16개

#### 계산 예시

**케이스 수**: 100개
**동시 실행**: 32개
**예상 Rounds**: ⌈100 / 32⌉ = 4회

**예상 시간**:
- 1 케이스 실행 시간: 3시간
- 총 시간: 3시간 × 4 rounds = 12시간

### 7.4 실행 모니터링

#### Slurm 큐 확인

```bash
squeue -u $USER
```

**출력**:
```
JOBID  ARRAY              NAME       ST  TIME  NODELIST
12345  1-26%8             Step001    R   1:30  node[01-02]
12346  _[9-26%8]          Step001    PD  0:00  (Resources)
```

**상태**:
- `R` (Running): 실행 중
- `PD` (Pending): 대기 중
- `CG` (Completing): 종료 중

#### 완료 확인

```bash
# Lock 파일 개수 확인
find /data/Test_001 -name "Step001.lock" | wc -l

# 전체 케이스 대비 진행률
echo "$(find /data/Test_001 -name 'Step001.lock' | wc -l) / 26 완료"
```

---

## 8. 사용 방법

### 8.1 scenario.json 작성

#### 기본 구조

```json
{
  "project_name": "Test_001_Full26_1Step",
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "apptainer_sif": "/opt/apptainers/KooSimulation313.sif",
    "apptainer_bind": "/data:/data,/shared:/shared",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_ifort2022_impilatest_mpp_s.sif",
    "lsdyna_apptainer_bind": "/data:/data,/shared:/shared"
  },
  "scenarios": [
    {
      "scenario_name": "Full_26_Directions_Single_Drop",
      "template": "MinimumModel.k",
      "angle_source": {
        "source_type": "cuboid_geometry",
        "cuboid_geometry": {
          "include_faces": true,
          "include_edges": true,
          "include_corners": true
        }
      },
      "cumulative": {
        "num_steps": 1,
        "mode_sequence": ["DROP"]
      }
    }
  ]
}
```

#### 필드 설명

**project_name**: 프로젝트 이름 (디렉토리 이름으로 사용)

**environment**: 실행 환경 설정
- `koomeshmodifier_path`: KooMeshModifier 실행 경로
- `lsdyna_path`: LS-DYNA 실행 파일 경로
- `apptainer_sif`: Apptainer 이미지 (KooMeshModifier용)
- `lsdyna_apptainer_sif`: Apptainer 이미지 (LS-DYNA용)

**scenario_name**: 시나리오 이름

**template**: 베이스 모델 파일 경로

**angle_source**: 각도 생성 방법 (cuboid_geometry, fibonacci_lattice, 등)

**cumulative**: 누적 낙하 설정
- `num_steps`: 총 Step 수
- `mode_sequence`: 각 Step의 실행 모드
- `angle_mixing`: 각도 믹싱 전략

### 8.2 실행 단계

#### 1단계: runner_config.json 생성

```bash
cd /opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step
KooChainRun prepare scenario.json -o runner_config.json
```

**출력**:
```
================================================================================
KooChainRun - Prepare Configuration
================================================================================
Scenario: .../scenario.json
Output:   .../runner_config.json

✅ runner_config.json 생성 완료
✅ Successfully generated: .../runner_config.json
```

#### 2단계: Slurm Job 제출

```bash
KooChainRun submit runner_config.json \
  --nodes 2 \
  --jobs-per-node 8 \
  --ncpu-per-job 16
```

**또는 run.sh 사용**:

```bash
bash run.sh
```

run.sh 내용:
```bash
#!/bin/bash
set -e

KOOCR="/opt/pyKooCAE/KooChainRun"

echo "Step 1: runner_config.json 생성 중..."
"$KOOCR" prepare scenario.json -o runner_config.json

echo "Step 2: KooChainRun으로 작업 제출 중..."
"$KOOCR" submit runner_config.json \
    --nodes 2 \
    --jobs-per-node 8 \
    --ncpu-per-job 16

echo "✅ 실행 완료"
```

#### 3단계: 진행 상황 모니터링

```bash
# Slurm 큐 확인
squeue -u $USER

# 완료 케이스 수 확인
find /data/Test_001_Full26_1Step -name "*.lock" | wc -l
```

#### 4단계: 결과 수집

```bash
KooChainRun collect runner_config.json results/
```

---

## 9. 테스트 시나리오

### 9.1 Test_001: 26방향 1회 낙하

**목적**: 전방향 취약점 탐색 및 완전 보증 테스트

**조건**:
- 각도 소스: cuboid_geometry (Face 6 + Edge 12 + Corner 8)
- 총 케이스: 26개
- 연속 낙하: 1회
- 각도 믹싱: same_angle

**리소스**:
- 노드: 2개
- 동시 실행: 8개 (노드당 4개)
- 예상 시간: 12시간
- 디스크: ~130GB

**scenario.json**:
```json
{
  "project_name": "Test_001_Full26_1Step",
  "scenarios": [{
    "scenario_name": "Full_26_Directions_Single_Drop",
    "template": "MinimumModel.k",
    "angle_source": {
      "source_type": "cuboid_geometry",
      "cuboid_geometry": {
        "include_faces": true,
        "include_edges": true,
        "include_corners": true
      }
    },
    "cumulative": {
      "num_steps": 1,
      "mode_sequence": ["DROP"]
    }
  }]
}
```

**실행**:
```bash
cd Test_001_Full26_1Step
bash run.sh
```

---

### 9.2 Test_002: 26방향 3회 연속 낙하

**목적**: 반복 낙하 내구성 및 누적 손상 평가

**조건**:
- 각도 소스: cuboid_geometry (26방향)
- 총 케이스: 26개
- 연속 낙하: 3회
- 각도 믹싱: same_angle (동일 각도 반복)

**리소스**:
- 노드: 2개
- 동시 실행: 8개
- 예상 시간: 36시간 (3 Steps)
- 디스크: ~390GB

**특징**:
- Step 1: 첫 낙하 (DROP_FIRST)
- Step 2: 변형 상태에서 2차 낙하 (DYNAIN_TO_INITIAL + DROP_CUMULATIVE)
- Step 3: 변형 상태에서 3차 낙하

**scenario.json**:
```json
{
  "cumulative": {
    "num_steps": 3,
    "mode_sequence": ["DROP", "DROP", "DROP"],
    "angle_mixing": {
      "strategy": "same_angle"
    }
  }
}
```

**실행**:
```bash
cd Test_002_Full26_3Step
bash run.sh
```

---

### 9.3 Test_003: 6면 Cyclic 3회 낙하

**목적**: 다양한 방향 순차 낙하 및 빠른 연속 낙하 검증

**조건**:
- 각도 소스: cuboid_geometry (Face만)
- 총 케이스: 6개
- 연속 낙하: 3회
- 각도 믹싱: cyclic (순환)

**리소스**:
- 노드: 1개
- 동시 실행: 6개
- 예상 시간: 9시간
- 디스크: ~90GB

**Cyclic 예시**:
```
runid_00001 (F1_Back 시작):
  Step 1: F1_Back   (Roll=0°)
  Step 2: F2_Front  (Roll=180°)
  Step 3: F3_Right  (Pitch=-90°)

runid_00002 (F2_Front 시작):
  Step 1: F2_Front  (Roll=180°)
  Step 2: F3_Right  (Pitch=-90°)
  Step 3: F4_Left   (Pitch=90°)
```

**scenario.json**:
```json
{
  "angle_source": {
    "source_type": "cuboid_geometry",
    "cuboid_geometry": {
      "include_faces": true,
      "include_edges": false,
      "include_corners": false
    }
  },
  "cumulative": {
    "num_steps": 3,
    "mode_sequence": ["DROP", "DROP", "DROP"],
    "angle_mixing": {
      "strategy": "cyclic"
    }
  }
}
```

---

### 9.4 Test_004: Pitch 각도 스윕

**목적**: 전후 낙하 각도 민감도 및 디스플레이 각도별 충격 평가

**조건**:
- 각도 소스: pitching_sweep
- Pitch 범위: -40° ~ +40° (1° 간격)
- Roll: 0° (고정)
- Yaw: 0° (고정)
- 총 케이스: 81개

**리소스**:
- 노드: 3개
- 동시 실행: 15개 (노드당 5개)
- 예상 시간: 18시간
- 디스크: ~405GB

**각도 분포**:
```
Pitch = -40°: 뒤로 기울임
Pitch = 0°:   수평
Pitch = +40°: 앞으로 기울임
```

**scenario.json**:
```json
{
  "angle_source": {
    "source_type": "pitching_sweep",
    "pitching_sweep": {
      "pitch_start": -40,
      "pitch_end": 40,
      "pitch_step": 1,
      "roll": 0,
      "yaw": 0
    }
  }
}
```

---

### 9.5 Test_005: Fibonacci Lattice 100방향

**목적**: 전방향 균일 샘플링 및 통계적 낙하 평가

**조건**:
- 각도 소스: fibonacci_lattice
- 방향 수: 100개
- 연속 낙하: 1회

**리소스**:
- 노드: 4개
- 동시 실행: 32개 (노드당 8개)
- 예상 시간: 12시간
- 디스크: ~500GB

**알고리즘**: Fibonacci Spiral
- 구형 표면에 거의 완벽하게 균일 분포
- 격자 패턴(Grid)보다 극점 집중 없음
- 방향 개수를 자유롭게 조정 가능

**scenario.json**:
```json
{
  "angle_source": {
    "source_type": "fibonacci_lattice",
    "fibonacci_lattice": {
      "num_directions": 100
    }
  }
}
```

---

### 9.6 리소스 요구사항 비교

| 테스트 | 케이스 | Steps | 동시 실행 | Rounds | 예상 시간 | 디스크 |
|--------|--------|-------|----------|--------|----------|--------|
| Test_001 | 26 | 1 | 8 | 4 | 12h | ~130GB |
| Test_002 | 26 | 3 | 8 | 4×3 | 36h | ~390GB |
| Test_003 | 6 | 3 | 6 | 1×3 | 9h | ~90GB |
| Test_004 | 81 | 1 | 15 | 6 | 18h | ~405GB |
| Test_005 | 100 | 1 | 32 | 4 | 12h | ~500GB |

**디스크 계산**: 케이스당 5GB (d3plot 포함) × 케이스 수 × Steps

---

## 10. 디렉토리 구조

### 10.1 생성된 디렉토리 개요

```
/data/
├── Test_001_Full26_1Step/      (26 runids)
├── Test_002_Full26_3Step/      (26 runids)
├── Test_003_6Faces_Cyclic/     (6 runids)
├── Test_004_Pitching_Sweep/    (181 runids)
└── Test_005_Fibonacci_100/     (100 runids)

총 339개 runids, 403개 Step 디렉토리
```

### 10.2 runid 디렉토리 구조

#### 단일 Step (Test_001)

```
runid_00001/
├── metadata.json               # 각도 정보
└── Step001/
    ├── Step001.k               # LS-DYNA 입력 파일
    ├── messag                  # LS-DYNA 로그
    ├── d3plot                  # 결과 파일
    ├── dynain                  # 변형 상태 (Step 2+용)
    └── Step001.lock            # 완료 플래그
```

#### 다중 Step (Test_002)

```
runid_00001/
├── metadata.json
├── Step001/
│   ├── Step001.k
│   ├── messag
│   ├── d3plot
│   ├── dynain                  # → Step002로 전달
│   └── Step001.lock
├── Step002/
│   ├── initial.k               # dynain → initial 변환 결과
│   ├── Step002.k
│   ├── messag
│   ├── d3plot
│   ├── dynain                  # → Step003로 전달
│   └── Step002.lock
└── Step003/
    ├── initial.k
    ├── Step003.k
    ├── messag
    ├── d3plot
    └── Step003.lock
```

### 10.3 metadata.json 상세

#### 단일 Step 예시

```json
{
  "runid": "runid_00001",
  "doe_index": 0,
  "scenario_name": "Full_26_Directions_Single_Drop",
  "total_steps": 1,
  "base_angle": {
    "name": "F1_Back",
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
  },
  "steps": [
    {
      "step_number": 1,
      "mode": "DROP",
      "template": "DROP_FIRST",
      "angle": {
        "name": "F1_Back",
        "roll": 0.0,
        "pitch": 0.0,
        "yaw": 0.0
      },
      "input_file": "Step001.k",
      "dynain_source": null
    }
  ]
}
```

#### 다중 Step 예시 (Cyclic)

```json
{
  "runid": "runid_00001",
  "doe_index": 0,
  "scenario_name": "6_Faces_3_Drops_Cyclic",
  "total_steps": 3,
  "base_angle": {
    "name": "F1_Back",
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
  },
  "steps": [
    {
      "step_number": 1,
      "mode": "DROP",
      "template": "DROP_FIRST",
      "angle": {
        "name": "F1_Back",
        "roll": 0.0,
        "pitch": 0.0,
        "yaw": 0.0
      },
      "input_file": "Step001.k",
      "dynain_source": null
    },
    {
      "step_number": 2,
      "mode": "DROP",
      "template": "DROP_CUMULATIVE",
      "angle": {
        "name": "F2_Front",
        "roll": 180.0,
        "pitch": 0.0,
        "yaw": 0.0
      },
      "input_file": "Step002.k",
      "dynain_source": "Step001/dynain"
    },
    {
      "step_number": 3,
      "mode": "DROP",
      "template": "DROP_CUMULATIVE",
      "angle": {
        "name": "F3_Right",
        "roll": 0.0,
        "pitch": -90.0,
        "yaw": 0.0
      },
      "input_file": "Step003.k",
      "dynain_source": "Step002/dynain"
    }
  ]
}
```

**주목할 점**:
- Step 2와 Step 3는 각각 다른 각도 (Cyclic 믹싱)
- dynain_source가 이전 Step을 참조

---

## 11. 실행 예제

### 11.1 Test_001 실행 (26방향 1회 낙하)

#### 1단계: 디렉토리 준비

```bash
cd /opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step
ls
```

**출력**:
```
MinimumModel.k
README.md
runner_config.json
run.sh
scenario.json
```

#### 2단계: scenario.json 확인

```bash
cat scenario.json
```

#### 3단계: 실행

```bash
bash run.sh
```

**출력**:
```
==========================================
Test_001: Full 26 Directions Single Drop
==========================================
프로젝트 루트: /opt/pyKooCAE

Step 1: runner_config.json 생성 중...
✅ runner_config.json 생성 완료

실행 설정:
  - 총 케이스: 26개
  - 노드: 2개
  - 노드당 Job: 4개
  - 동시 실행: 8개
  - 예상 Rounds: 4회
  - 예상 시간: ~12시간

실행하시겠습니까? (y/n): y

KooChainRun으로 작업 제출 중...
Submitted batch job 12345

✅ 실행 완료

진행 상황 확인:
  squeue -u $USER
  find /data/Test_001_Full26_1Step -name '*.lock' | wc -l
```

#### 4단계: 모니터링

```bash
# Slurm 큐 확인
squeue -u $USER

# 완료 케이스 수 확인
find /data/Test_001_Full26_1Step -name "Step001.lock" | wc -l
```

#### 5단계: 결과 확인

```bash
# runid_00001 결과 확인
ls -lh /data/Test_001_Full26_1Step/runid_00001/Step001/

# d3plot 크기 확인
du -sh /data/Test_001_Full26_1Step/runid_00001/Step001/d3plot

# metadata 확인
cat /data/Test_001_Full26_1Step/runid_00001/metadata.json
```

---

### 11.2 Test_003 실행 (6면 Cyclic)

#### 실행

```bash
cd Test_003_6Faces_Cyclic
bash run.sh
```

#### Cyclic 각도 확인

```bash
# runid_00001의 각 Step 각도 확인
python3 << 'EOF'
import json

with open('/data/Test_003_6Faces_Cyclic/runid_00001/metadata.json', 'r') as f:
    data = json.load(f)

print(f"runid: {data['runid']}")
print(f"Total steps: {data['total_steps']}")
print()

for step in data['steps']:
    angle = step['angle']
    print(f"Step {step['step_number']}: {angle['name']:15s} "
          f"Roll={angle['roll']:6.1f}°, Pitch={angle['pitch']:6.1f}°")
EOF
```

**출력**:
```
runid: runid_00001
Total steps: 3

Step 1: F1_Back         Roll=   0.0°, Pitch=   0.0°
Step 2: F2_Front        Roll= 180.0°, Pitch=   0.0°
Step 3: F3_Right        Roll=   0.0°, Pitch= -90.0°
```

---

### 11.3 디렉토리만 생성 (시뮬레이션 없이)

시뮬레이션 실행 없이 디렉토리 구조만 생성하는 방법입니다.

#### 스크립트 사용

```bash
cd /opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests

# Test_001 디렉토리만 생성
python3 create_directories.py \
    Test_001_Full26_1Step/runner_config.json \
    /data/Test_001_Full26_1Step
```

**출력**:
```
================================================================================
실제 시뮬레이션 디렉토리 생성
================================================================================
프로젝트: Test_001_Full26_1Step
출력 디렉토리: /data/Test_001_Full26_1Step

시나리오: Full_26_Directions_Single_Drop
총 Step 수: 1
총 runid 개수: 26

  생성 완료: 10/26 runids
  생성 완료: 20/26 runids
  총 생성: 26 runids

✅ 디렉토리 생성 완료: /data/Test_001_Full26_1Step
```

#### 생성 확인

```bash
# runid 개수 확인
ls -d /data/Test_001_Full26_1Step/runid_* | wc -l

# 첫 runid 구조 확인
ls -la /data/Test_001_Full26_1Step/runid_00001/

# metadata.json 확인
cat /data/Test_001_Full26_1Step/runid_00001/metadata.json
```

---

## 12. 문제 해결

### 12.1 작업이 Pending 상태

#### 확인

```bash
squeue -u $USER
```

**출력**:
```
JOBID  ARRAY              NAME       ST  TIME  NODELIST(REASON)
12345  1-26%8             Step001    PD  0:00  (Resources)
```

#### 원인

- `Resources`: 리소스 부족 (노드가 모두 사용 중)
- `Priority`: 우선순위 낮음
- `Dependency`: 이전 Job 대기 중

#### 해결

- 다른 작업 완료 대기
- `--jobs-per-node` 값 감소
- `--nodes` 값 감소

---

### 12.2 일부 케이스 실패

#### 실패한 케이스 찾기

```bash
# Step001.lock이 없는 케이스 찾기
for runid in /data/Test_001/runid_*; do
    if [ ! -f "$runid/Step001/Step001.lock" ]; then
        echo "실패: $runid"
    fi
done
```

#### 로그 확인

```bash
# Slurm 출력
cat /data/Test_001/runid_00005/Step001/slurm-*.out

# LS-DYNA 로그
cat /data/Test_001/runid_00005/Step001/messag
```

#### 재실행

해당 케이스만 재실행하려면 Slurm task ID를 직접 지정:

```bash
sbatch --array=5 step1.sh
```

---

### 12.3 디스크 부족

#### 공간 확인

```bash
# 전체 디스크 사용량
du -sh /data/Test_*

# 테스트별 상세 확인
du -h --max-depth=1 /data/Test_001_Full26_1Step | sort -h
```

#### 압축

```bash
# d3plot 압축 (완료된 테스트만)
cd /data/Test_001_Full26_1Step
find . -name "d3plot*" -exec gzip {} \;

# 압축률 확인
du -sh /data/Test_001_Full26_1Step
```

#### 정리

불필요한 파일 삭제:

```bash
# messag 파일 삭제 (로그 확인 후)
find /data/Test_001 -name "messag" -delete

# 중간 파일 삭제
find /data/Test_001 -name "*.tmp" -delete
```

---

### 12.4 Apptainer 권한 문제

#### 증상

```
FATAL: container creation failed: mount /opt/apptainers->... error
```

#### 해결

Bind 경로 확인:

```bash
# scenario.json의 apptainer_bind 확인
grep "apptainer_bind" scenario.json
```

올바른 경로로 수정:

```json
{
  "environment": {
    "apptainer_bind": "/data:/data,/shared:/shared,/opt:/opt"
  }
}
```

---

### 12.5 DYNAIN_TO_INITIAL 실패

#### 증상

Step 2 실행 시 initial.k가 생성되지 않음

#### 확인

```bash
# Step001의 dynain 파일 존재 확인
ls -lh /data/Test_002/runid_00001/Step001/dynain

# dynain 파일 크기 확인 (0이면 문제)
du -h /data/Test_002/runid_00001/Step001/dynain
```

#### 해결

Step 1의 LS-DYNA 출력 설정 확인:

```bash
# messag에서 DYNAIN 출력 확인
grep "DYNAIN" /data/Test_002/runid_00001/Step001/messag
```

LS-DYNA K 파일에 `*DATABASE_DYNAIN` 추가:

```
*DATABASE_DYNAIN
$#      dt      lcdt      beam     npltc
    0.050         0         0         0
```

---

## 부록 A: 버그 수정 이력

### A.1 doe_index 중복 버그

**발견일**: 2026-01-29
**파일**: `Runner/CumulativeDesigner.py:152`

**문제**:
Tolerance가 없을 때 모든 케이스의 doe_index가 0으로 설정되어 runid가 중복 생성됨

**원인**:
```python
# BEFORE (잘못된 코드)
doe_angles = [(name, roll, pitch, yaw, 0) for name, roll, pitch, yaw in base_angles]
```

**해결**:
```python
# AFTER (수정된 코드)
doe_angles = [(name, roll, pitch, yaw, idx) for idx, (name, roll, pitch, yaw) in enumerate(base_angles)]
```

### A.2 Cyclic 각도 믹싱 버그

**발견일**: 2026-01-29
**파일**: `Runner/CumulativeDesigner.py:187`

**문제**:
Cyclic 전략 사용 시 모든 Step에서 동일 각도가 적용됨

**원인**:
`base_angles_for_mixing`이 단일 base_name 그룹만 포함하여 순환할 각도가 1개뿐

```python
# BEFORE (잘못된 코드)
base_angles_for_mixing = [(n, r, p, y) for n, r, p, y, _ in doe_list]
# doe_list는 같은 base_name만 포함 (예: F1_Back 1개)
```

**해결**:
모든 base 각도를 수집하여 cyclic에 사용

```python
# AFTER (수정된 코드)
all_base_angles = []
for base_name in sorted(doe_by_base.keys()):
    first_doe = doe_by_base[base_name][0]
    all_base_angles.append((first_doe[0], first_doe[1], first_doe[2], first_doe[3]))

# cyclic에 all_base_angles 사용
angle_sequence = generate_cumulative_angle_sequence(
    all_base_angles, num_steps, mixing_config, current_base_idx
)
```

### A.3 fibonacci_lattice 파라미터 호환성

**발견일**: 2026-01-29
**파일**: `Runner/CumulativeDesigner.py:252`

**문제**:
scenario.json에서 `num_directions` 사용 시 인식 안 됨 (내부적으로 `num_points` 사용)

**해결**:
`num_directions`를 `num_points`의 별칭으로 허용

```python
# AFTER
fib_cfg = angle_source_cfg.get("fibonacci_lattice", {})
num_pts = fib_cfg.get("num_points") or fib_cfg.get("num_directions", 26)
config = AngleSourceConfig(
    source_type=source_type,
    fibonacci_lattice=FibonacciLatticeConfig(num_points=num_pts)
)
```

---

## 부록 B: 참고 문서

### B.1 관련 문서

- [USER_GUIDE.md](USER_GUIDE.md): 사용자 가이드
- [COMPLETE_DOCUMENTATION.md](COMPLETE_DOCUMENTATION.md): 완전한 문서
- [Tests/README.md](Tests/README.md): 테스트 시나리오 모음
- [EXAMPLE_STRUCTURES.md](Tests/EXAMPLE_STRUCTURES.md): 디렉토리 구조 예제
- [DIRECTORIES_CREATED.md](Tests/DIRECTORIES_CREATED.md): 생성된 디렉토리 정보

### B.2 소스 코드

**핵심 모듈**:
- `Runner/CumulativeDesigner.py`: scenario.json → runner_config.json 변환
- `Runner/LargeScaleDOEManager.py`: Slurm Job 제출 및 실행 관리
- `Runner/AngleMixingStrategy.py`: 각도 믹싱 전략
- `Runner/AngleSourceParser.py`: 각도 소스 파싱

**CLI**:
- `KooChainRun`: 메인 CLI 진입점

### B.3 외부 참고

- **LS-DYNA 문서**: [www.lstc.com](http://www.lstc.com)
- **Slurm 문서**: [slurm.schedmd.com](https://slurm.schedmd.com)
- **Apptainer 문서**: [apptainer.org](https://apptainer.org)

---

**문서 버전**: 1.0
**최종 수정**: 2026-01-29
**작성자**: CAE팀

---

## 연락처

기술 지원이 필요하시면 CAE팀으로 연락 주시기 바랍니다.

---

**© 2026 CAE Team. All rights reserved.**
