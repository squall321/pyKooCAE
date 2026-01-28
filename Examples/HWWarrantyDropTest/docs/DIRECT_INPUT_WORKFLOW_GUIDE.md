# Direct Input Workflow 가이드

**작성일**: 2026-01-23
**버전**: 1.0
**대상**: 낙하 각도 정보 없이 직접 입력 파일로 시뮬레이션 실행

---

## 🎯 개요

### 기존 워크플로우 vs Direct Input 워크플로우

| 항목 | 기존 워크플로우 | Direct Input 워크플로우 |
|------|---------------|----------------------|
| **입력** | 각도 정보 (roll, pitch, yaw) | 직접 입력 파일 (.k) |
| **각도 생성** | ✅ Fibonacci, Cuboid 등 | ❌ 없음 |
| **DOE** | ✅ LHS, Grid, Random | ❌ 없음 |
| **KooMeshModifier** | ✅ 자동 실행 | ✅ 선택적 실행 |
| **LS-DYNA** | ❌ 별도 실행 | ✅ **자동 실행** |
| **사용 시나리오** | 대규모 DOE 자동화 | 사용자 정의 입력 + 시뮬레이션 |

---

## 🚀 핵심 기능

### 1. 입력 파일 기반 실행

**특징**:
- 각도 정보 없이 직접 입력 파일 사용
- 사용자가 준비한 메쉬 파일 (.k) 직접 사용
- KooMeshModifier 없이 LS-DYNA만 실행 가능

**장점**:
- ✅ 유연성: 사용자 정의 입력 파일 사용
- ✅ 간편성: 각도 계산/DOE 생성 불필요
- ✅ 통합성: KooMeshModifier + LS-DYNA 한번에 실행

---

### 2. 단계별 노드 점유율 및 자원 설정

**특징**:
- Step마다 다른 자원 요구사항 설정
- 노드 수, CPU 수, 메모리, 실행 시간 개별 설정
- Slurm 파티션 선택 가능

**예시**:

```json
{
  "step_resources": {
    "1": {
      "nnodes": 2,
      "ncpus_per_node": 32,
      "memory_per_node": "64G",
      "walltime": "02:00:00",
      "partition": "normal"
    },
    "2": {
      "nnodes": 4,
      "ncpus_per_node": 32,
      "memory_per_node": "128G",
      "walltime": "04:00:00",
      "partition": "large"
    }
  }
}
```

**설명**:
- Step 1: 2 노드 × 32 CPU = 64 CPU, 64GB 메모리, 2시간
- Step 2: 4 노드 × 32 CPU = 128 CPU, 128GB 메모리, 4시간

---

### 3. KooMeshModifier + LS-DYNA 통합 실행

**워크플로우**:

```
입력 파일 (.k)
    ↓
[KooMeshModifier] (선택적)
    ↓
dynain 생성
    ↓
[LS-DYNA 실행]
    ↓
d3plot, binout 등 결과
```

**선택적 실행**:
- `use_koomesh: true` → KooMeshModifier 실행
- `use_lsdyna: true` → LS-DYNA 실행
- 둘 다 `true`면 순차 실행

---

### 4. 노드 점유율 실시간 모니터링

**기능**:
- 실시간 Job 상태 확인
- 노드 수, CPU 수 추적
- 자동 완료 감지

**사용법**:

```bash
python3 Runner/DirectInputWorkflow.py \
    direct_input_config.json \
    --monitor
```

**출력 예시**:

```
========================================
노드 점유율 모니터링 시작
========================================

Job 12345: RUNNING | Nodes: 2 | CPUs: 64
Job 12346: PENDING | Nodes: N/A | CPUs: N/A
Job 12347: PENDING | Nodes: N/A | CPUs: N/A

다음 체크: 60초 후...

Job 12345: COMPLETED | Nodes: 2 | CPUs: 64
Job 12346: RUNNING | Nodes: 4 | CPUs: 128
Job 12347: PENDING | Nodes: N/A | CPUs: N/A

...

✅ 모든 Job 완료
```

---

## 📚 사용 방법

### Step 1: 설정 파일 작성

**파일명**: `direct_input_config.json`

```json
{
  "project_name": "DirectInput_Project",
  "job_name": "CustomMesh_Test",
  "num_steps": 3,
  "input_files": [
    "/data/inputs/step1.k",
    "/data/inputs/step2.k",
    "/data/inputs/step3.k"
  ],
  "use_koomesh": true,
  "use_lsdyna": true,
  "koomesh_params": {
    "template": "DROP_FIRST",
    "result_dir": "./"
  },
  "lsdyna_params": {
    "memory": 60000
  },
  "step_resources": {
    "1": {
      "nnodes": 2,
      "ncpus_per_node": 32,
      "memory_per_node": "64G",
      "walltime": "02:00:00",
      "partition": "normal"
    },
    "2": {
      "nnodes": 4,
      "ncpus_per_node": 32,
      "memory_per_node": "128G",
      "walltime": "04:00:00",
      "partition": "large"
    },
    "3": {
      "nnodes": 4,
      "ncpus_per_node": 32,
      "memory_per_node": "128G",
      "walltime": "06:00:00",
      "partition": "large"
    }
  }
}
```

**설명**:
- `project_name`: 프로젝트 이름 (디렉토리 생성)
- `job_name`: Job 이름
- `num_steps`: Step 수
- `input_files`: 입력 파일 경로 리스트 (Step 수만큼)
- `use_koomesh`: KooMeshModifier 사용 여부
- `use_lsdyna`: LS-DYNA 실행 여부
- `koomesh_params`: KooMeshModifier 추가 파라미터
- `lsdyna_params`: LS-DYNA 추가 파라미터 (memory 등)
- `step_resources`: Step별 자원 설정

---

### Step 2: Workflow 실행

#### 기본 실행

```bash
python3 Runner/DirectInputWorkflow.py direct_input_config.json
```

#### Dry-run (테스트)

```bash
python3 Runner/DirectInputWorkflow.py direct_input_config.json --dry-run
```

#### 모니터링 포함

```bash
python3 Runner/DirectInputWorkflow.py direct_input_config.json --monitor
```

#### 사용자 정의 데이터 루트

```bash
python3 Runner/DirectInputWorkflow.py \
    direct_input_config.json \
    --data-root=/scratch/myproject
```

---

### Step 3: 결과 확인

**디렉토리 구조**:

```
/data/DirectInput_Project/
└── CustomMesh_Test_20260123_103000/
    ├── metadata.json
    ├── input_001.k  ← 복사된 입력 파일
    ├── input_002.k
    ├── input_003.k
    ├── Step001/
    │   ├── slurm_12345.out
    │   ├── slurm_12345.err
    │   ├── dynain
    │   ├── d3plot01
    │   ├── d3plot02
    │   ├── binout
    │   └── .lock  ← 완료 표시
    ├── Step002/
    │   └── ...
    └── Step003/
        └── ...
```

**결과 파일**:
- `dynain`: KooMeshModifier 출력 (또는 입력 파일)
- `d3plot*`: LS-DYNA 결과 (포스트 프로세싱용)
- `binout`: LS-DYNA 이진 출력 (시계열 데이터)
- `.lock`: 완료 표시 (타임스탬프 포함)

---

## 🔍 사용 시나리오

### 시나리오 1: KooMeshModifier 없이 LS-DYNA만 실행

**사용 케이스**:
- 이미 준비된 dynain 파일이 있는 경우
- 메쉬 수정 없이 시뮬레이션만 실행

**설정**:

```json
{
  "use_koomesh": false,
  "use_lsdyna": true,
  "input_files": [
    "/data/inputs/dynain_step1",
    "/data/inputs/dynain_step2"
  ]
}
```

**주의**:
- 입력 파일이 `dynain` 형식이어야 함
- KooMeshModifier를 건너뛰고 바로 LS-DYNA 실행

---

### 시나리오 2: KooMeshModifier + LS-DYNA 통합 실행

**사용 케이스**:
- 사용자 정의 메쉬 수정 후 시뮬레이션
- 낙하 각도는 없지만 메쉬 변형이 필요한 경우

**설정**:

```json
{
  "use_koomesh": true,
  "use_lsdyna": true,
  "koomesh_params": {
    "template": "DROP_FIRST",
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
  },
  "lsdyna_params": {
    "memory": 80000
  }
}
```

**워크플로우**:
1. KooMeshModifier로 메쉬 수정 → `dynain` 생성
2. LS-DYNA로 시뮬레이션 → `d3plot*` 생성

---

### 시나리오 3: Step별 자원 요구사항 다른 경우

**사용 케이스**:
- Step 1: 간단한 전처리 (2 노드)
- Step 2-3: 복잡한 시뮬레이션 (4 노드, 더 긴 시간)

**설정**:

```json
{
  "step_resources": {
    "1": {
      "nnodes": 2,
      "ncpus_per_node": 32,
      "walltime": "01:00:00"
    },
    "2": {
      "nnodes": 4,
      "ncpus_per_node": 32,
      "walltime": "06:00:00"
    },
    "3": {
      "nnodes": 4,
      "ncpus_per_node": 32,
      "walltime": "08:00:00"
    }
  }
}
```

**장점**:
- 자원 효율성: 필요한 만큼만 사용
- 큐 대기 시간 단축: Step 1은 빨리 실행

---

## 📊 노드 점유율 이해

### 예시: Step별 자원 사용

| Step | 노드 수 | CPU/노드 | 총 CPU | 메모리 | 실행 시간 |
|------|---------|---------|--------|--------|-----------|
| 1 | 2 | 32 | 64 | 128 GB | 2시간 |
| 2 | 4 | 32 | 128 | 512 GB | 4시간 |
| 3 | 4 | 32 | 128 | 512 GB | 6시간 |

**총 자원 사용량**:
- **최대 노드**: 4개 (Step 2-3 동시 실행 시)
- **총 CPU-시간**: 64×2 + 128×4 + 128×6 = 1,408 CPU-시간
- **총 실행 시간**: 12시간 (순차 실행)

**Slurm 관리**:
- Step 1 완료 후 자동으로 2노드 해제
- Step 2 시작 시 4노드 할당
- `--dependency=afterok` 사용하여 순차 실행 보장

---

## 🔧 고급 설정

### 1. LS-DYNA 파라미터 커스터마이즈

```json
{
  "lsdyna_params": {
    "memory": 100000,
    "endtime": 0.01,
    "dt": 1e-7
  }
}
```

**Slurm 스크립트에서**:

```bash
mpirun -np 128 /opt/lsdyna/bin/ls-dyna \
    i=dynain \
    memory=100000m \
    endtime=0.01 \
    dt=1e-7
```

---

### 2. KooMeshModifier 파라미터 커스터마이즈

```json
{
  "koomesh_params": {
    "template": "CUSTOM_TEMPLATE",
    "scale": 1.5,
    "offset_x": 10.0
  }
}
```

**Slurm 스크립트에서**:

```bash
/opt/KooMeshModifier/run.sh \
    --template="CUSTOM_TEMPLATE" \
    --scale="1.5" \
    --offset_x="10.0" \
    --input="input.k" \
    --output-dir="./"
```

---

### 3. Slurm 파티션 전략

**소규모 클러스터**:

```json
{
  "step_resources": {
    "1": {"partition": "normal"},
    "2": {"partition": "normal"},
    "3": {"partition": "normal"}
  }
}
```

**대규모 클러스터 (파티션 분리)**:

```json
{
  "step_resources": {
    "1": {"partition": "short"},   // 빠른 실행
    "2": {"partition": "normal"},  // 일반 실행
    "3": {"partition": "long"}     // 긴 실행
  }
}
```

---

## 🚨 주의사항

### 1. 입력 파일 경로

**올바른 방법**:
```json
{
  "input_files": [
    "/data/inputs/step1.k",  // 절대 경로
    "/data/inputs/step2.k"
  ]
}
```

**잘못된 방법**:
```json
{
  "input_files": [
    "step1.k",  // 상대 경로 (권장하지 않음)
    "./inputs/step2.k"
  ]
}
```

---

### 2. LS-DYNA 실행 파일 경로

**기본값**: `/opt/lsdyna/bin/ls-dyna`

**커스터마이즈** (코드 수정 필요):

```python
# DirectInputWorkflow.py
self.lsdyna_bin = "/your/custom/path/ls-dyna"
```

---

### 3. 메모리 설정

**LS-DYNA 메모리**:
- `lsdyna_params.memory`: LS-DYNA가 사용할 메모리 (MB)
- `step_resources.memory_per_node`: Slurm이 할당할 노드 메모리

**예시**:

```json
{
  "lsdyna_params": {
    "memory": 60000  // LS-DYNA: 60GB
  },
  "step_resources": {
    "1": {
      "memory_per_node": "64G"  // Slurm: 64GB (여유분 4GB)
    }
  }
}
```

**권장**:
- LS-DYNA 메모리 < Slurm 메모리
- 여유분 최소 4-8GB 확보

---

## 📈 성능 최적화

### 1. CPU 수 최적화

**경험적 규칙**:
- 소규모 모델: 32-64 CPU
- 중규모 모델: 64-128 CPU
- 대규모 모델: 128-256 CPU

**스케일링 효율**:
- 32 → 64 CPU: ~1.8x 속도 향상
- 64 → 128 CPU: ~1.5x 속도 향상
- 128 → 256 CPU: ~1.3x 속도 향상 (diminishing returns)

---

### 2. 노드 수 vs CPU/노드

**케이스 1: 2 노드 × 32 CPU = 64 CPU**
- 장점: 노드 간 통신 적음
- 단점: 노드당 메모리 제한

**케이스 2: 4 노드 × 16 CPU = 64 CPU**
- 장점: 더 많은 총 메모리
- 단점: 노드 간 통신 증가

**권장**:
- 메모리 충분: 적은 노드 × 많은 CPU/노드
- 메모리 부족: 많은 노드 × 적은 CPU/노드

---

### 3. Walltime 설정

**과소 설정**:
- Job이 타임아웃으로 실패
- 재실행 필요 → 시간 낭비

**과대 설정**:
- 큐 대기 시간 증가
- 자원 낭비

**권장**:
1. 테스트 실행으로 실제 소요 시간 측정
2. 실제 시간 × 1.2-1.5 배로 설정

---

## 📞 문의

**작성자**: koo.park
**이메일**: koo.park@samsung.com
**부서**: CAE, HE

---

**버전**: 1.0
**작성일**: 2026-01-23
**대상**: Direct Input Workflow 사용자 가이드
