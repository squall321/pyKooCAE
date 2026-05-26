# HW Warranty Drop Test 사용자 가이드

**작성**: 2026-01-23
**대상**: CAE 엔지니어, HPC 사용자

---

## 개요

제품 보증 낙하 시험을 위한 대규모 시뮬레이션 자동화 도구입니다. 수십~수백 개의 낙하 방향과 다중 낙하 시나리오를 병렬로 실행하며, Slurm 클러스터에서 효율적으로 리소스를 관리합니다.

**주요 기능**:
- 전방향 낙하 시뮬레이션 (6면, 26방향, 피보나치 균일분포)
- 연속 낙하 (손상 누적)
- 병렬 실행 (수백 개 케이스 동시 처리)
- 컨테이너 기반 실행 (Apptainer)

---

## 실행 환경

### 하드웨어
- 헤드 노드: 작업 제출, 결과 수집
- 컴퓨트 노드: 128코어 × 346대
  - 전용 노드: 300대
  - 공유 노드: 46대

### 소프트웨어
- Slurm 워크로드 매니저
- Apptainer 컨테이너
  - `KooSimulation313.sif`: KooMeshModifier 포함
  - `LSDynaBasic_ifort2022_impilatest_mpp_s.sif`: LS-DYNA R16.1

### 파일시스템
- `/data`: 실행 데이터, 결과 저장
- `/shared`: 템플릿 파일, 공유 리소스

---

## 낙하 시나리오 유형

### 1. 6면 낙하 (Cuboid Faces)

육면체의 6개 면 방향으로 낙하.

**적용 케이스**:
- 기본 보증 테스트
- 빠른 검증 (6개 케이스만 실행)

**각도 정의**:
```
Face 1: Top     (Roll=0,   Pitch=0,   Yaw=0)
Face 2: Bottom  (Roll=180, Pitch=0,   Yaw=0)
Face 3: Front   (Roll=90,  Pitch=0,   Yaw=0)
Face 4: Back    (Roll=-90, Pitch=0,   Yaw=0)
Face 5: Left    (Roll=0,   Pitch=90,  Yaw=0)
Face 6: Right   (Roll=0,   Pitch=-90, Yaw=0)
```

**scenario.json 설정**:
```json
{
  "angle_source": {
    "source_type": "cuboid_geometry",
    "cuboid_geometry": {
      "include_faces": true,
      "include_edges": false,
      "include_corners": false
    }
  }
}
```

**실행 시간**: 노드 2개 × 4 Job = 8 동시 실행 시 약 1 round (~3시간)

---

### 2. 26방향 낙하 (Cuboid Full)

육면체의 면 6개 + 모서리 12개 + 모서리 8개 = 총 26방향.

**적용 케이스**:
- 완전 보증 테스트
- 취약 방향 탐색

**각도 구성**:
- **Face 6개**: Top, Bottom, Front, Back, Left, Right
- **Edge 12개**: 예) Top-Front (Roll=45, Pitch=0, Yaw=0)
- **Corner 8개**: 예) Top-Front-Left (Roll=45, Pitch=45, Yaw=0)

**scenario.json 설정**:
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

**실행 시간**: 노드 2개 × 4 Job = 8 동시 실행 시 4 rounds (~12시간)

**방향 목록**:

| 타입 | 개수 | Roll | Pitch | Yaw | 설명 |
|------|------|------|-------|-----|------|
| Face | 6 | 0/±90/180 | 0/±90 | 0 | 6개 평면 |
| Edge | 12 | ±45 | 0/±45/±90 | 0/±45 | 12개 모서리 |
| Corner | 8 | ±45 | ±45 | ±45 | 8개 꼭지점 |

---

### 3. 피칭 스윕 (Pitching Sweep)

Pitch 각도를 일정 간격으로 스캔.

**적용 케이스**:
- 전후 낙하 각도 민감도 분석
- 디스플레이 각도별 충격 평가

**각도 범위**:
```
Pitch: -40° ~ +40° (1° 간격) = 81개 각도
Roll: 0° (고정)
Yaw: 0° (고정)
```

**scenario.json 설정**:
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

**실행 시간**: 81 케이스, 16 동시 실행 시 6 rounds (~18시간)

---

### 4. 롤링 스윕 (Rolling Sweep)

Roll 각도를 일정 간격으로 스캔.

**적용 케이스**:
- 좌우 낙하 각도 민감도
- 회전 상태 낙하 평가

**각도 범위**:
```
Roll: 0° ~ 360° (2° 간격) = 180개 각도
Pitch: 0° (고정)
Yaw: 0° (고정)
```

**scenario.json 설정**:
```json
{
  "angle_source": {
    "source_type": "rolling_sweep",
    "rolling_sweep": {
      "roll_start": 0,
      "roll_end": 360,
      "roll_step": 2,
      "pitch": 0,
      "yaw": 0
    }
  }
}
```

**실행 시간**: 180 케이스, 32 동시 실행 시 6 rounds (~18시간)

---

### 5. 피보나치 균일분포 (Fibonacci Lattice)

구형 표면에 균일하게 분포된 N개 방향.

**적용 케이스**:
- 전방향 균일 샘플링
- 통계적 낙하 테스트
- 극한 케이스 탐색

**알고리즘**:
피보나치 나선(Fibonacci Spiral)을 이용한 구면 균일분포 생성.

```python
# i = 0, 1, ..., N-1
phi = (1 + sqrt(5)) / 2  # 황금비
theta = 2π × i / phi     # 방위각
z = 1 - (2i + 1) / N     # 높이 (-1 ~ 1)
r = sqrt(1 - z²)         # 반지름

x = r × cos(theta)
y = r × sin(theta)
z = z

# (x, y, z) → (roll, pitch, yaw) 변환
```

**장점**:
- 구형 표면에 거의 완벽하게 균일 분포
- 방향 개수를 자유롭게 조정 가능 (10, 100, 1000개 등)

**scenario.json 설정**:
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

**예시**:
- 100개 방향: 32 동시 실행 시 4 rounds (~12시간)
- 1000개 방향: 100 동시 실행 시 10 rounds (~30시간)

---

## 연속 낙하 (Cumulative Drop)

### 개념

1차 낙하 후 변형된 상태에서 2차, 3차 낙하를 수행. 손상이 누적됩니다.

**실제 시나리오**:
- 운송 중 여러 번 떨어뜨림
- 사용 중 반복적 충격

### 실행 흐름

#### Step 1 (첫 낙하)
```
1. 베이스 모델 → 각도 회전 (KooMeshModifier)
2. 낙하 시뮬레이션 (LS-DYNA)
3. 변형 상태 저장 (dynain 파일)
```

#### Step 2 (2차 낙하)
```
1. Step 1 dynain → Initial.k 변환 (DYNAIN_TO_INITIAL)
2. Initial.k → 새 각도 회전 (KooMeshModifier)
3. 낙하 시뮬레이션 (LS-DYNA)
4. 변형 상태 저장
```

#### Step 3 (3차 낙하)
```
1. Step 2 dynain → Initial.k 변환
2. Initial.k → 새 각도 회전
3. 낙하 시뮬레이션
```

### 각도 믹싱 전략

각 Step마다 어떤 각도로 낙하시킬지 결정.

#### 1. same_angle (동일 각도)
모든 Step에서 같은 각도로 낙하.

```
Step 1: Roll=0°  (Top 낙하)
Step 2: Roll=0°  (Top 낙하)
Step 3: Roll=0°  (Top 낙하)
```

**용도**: 동일 방향 반복 낙하 테스트

#### 2. cyclic (순환)
각도를 순환하며 사용.

```
6방향 케이스:
Step 1: Top    (0°)
Step 2: Front  (90°)
Step 3: Bottom (180°)
Step 4: Back   (-90°)
```

**용도**: 다양한 방향 순차 낙하

#### 3. random (랜덤)
각 Step마다 랜덤 각도.

```
Step 1: Top-Front-Left
Step 2: Bottom-Right
Step 3: Back-Top
```

**용도**: 불규칙 낙하 시뮬레이션

#### 4. opposite (반대편)
이전 Step 반대 방향으로 낙하.

```
Step 1: Top    (Roll=0°)
Step 2: Bottom (Roll=180°)
Step 3: Top    (Roll=0°)
```

**용도**: 양방향 충격 테스트

### scenario.json 설정
```json
{
  "cumulative": {
    "num_steps": 3,
    "mode_sequence": ["DROP", "DROP", "DROP"],
    "base_angle_index": 0,
    "angle_mixing": {
      "strategy": "cyclic"
    }
  }
}
```

---

## 리소스 사용 정책

### 노드 및 코어 할당

#### 기본 설정
```bash
--nodes 2              # 사용 노드 수
--jobs-per-node 4      # 노드당 동시 Job 수
--ncpu-per-job 16      # Job당 CPU 코어
```

**동시 실행 계산**:
```
concurrent = nodes × jobs_per_node
           = 2 × 4 = 8 케이스

총 CPU = concurrent × ncpu_per_job
       = 8 × 16 = 128 코어
```

#### 리소스 최적화 전략

**소규모 테스트** (26 케이스):
```bash
--nodes 2 --jobs-per-node 4 --ncpu-per-job 16
동시 실행: 8개
Rounds: 4회 (8+8+8+2)
```

**중규모 테스트** (100 케이스):
```bash
--nodes 4 --jobs-per-node 8 --ncpu-per-job 16
동시 실행: 32개
Rounds: 4회 (32+32+32+4)
```

**대규모 테스트** (1000 케이스):
```bash
--nodes 10 --jobs-per-node 10 --ncpu-per-job 16
동시 실행: 100개
Rounds: 10회
```

### Slurm Array Job 활용

전통적 방식 (비효율):
```bash
# 26개 케이스 = 26개 개별 Job 제출
sbatch case_001.sh
sbatch case_002.sh
...
sbatch case_026.sh
```
- Slurm 스케줄러 부담 증가
- 큐잉 시간 증가
- 관리 복잡

Array Job 방식 (효율):
```bash
# 26개 케이스 = 1개 Array Job
sbatch --array=1-26%8 batch_script.sh
```
- 스케줄러 부담 최소화
- 자동 큐잉 (8개씩 실행, 완료되면 다음 8개)
- 단일 Job ID로 관리

**동시 실행 제한 (%concurrent)**:
```
--array=1-26%8
       ^^^^^ ^^^
       범위  동시실행제한
```

8개가 완료되면 자동으로 다음 8개 시작.

### Step 간 의존성 관리

Step 2는 Step 1이 **모두 완료**된 후 시작:
```bash
# Step 1 제출
JOB1=$(sbatch --array=1-26%8 step1.sh | awk '{print $4}')

# Step 2 제출 (Step 1에 의존)
JOB2=$(sbatch --array=1-26%8 --dependency=afterok:$JOB1 step2.sh | awk '{print $4}')

# Step 3 제출 (Step 2에 의존)
JOB3=$(sbatch --array=1-26%8 --dependency=afterok:$JOB2 step3.sh | awk '{print $4}')
```

**afterok**: 이전 Job의 모든 Array Task가 성공(exit 0)해야 다음 Job 시작.

---

## Apptainer 컨테이너 구성

### 컨테이너 분리 전략

KooMeshModifier와 LS-DYNA는 **별도 컨테이너**에서 실행.

**이유**:
- 의존성 충돌 방지 (라이브러리 버전 차이)
- 독립적 버전 관리
- 선택적 사용 (한쪽만 컨테이너 가능)

### KooMeshModifier 컨테이너

**이미지**: `KooSimulation313.sif`
**위치**: `/opt/apptainers/KooSimulation313.sif`
**내부 경로**: `/opt/KooMeshModifier/run.sh`

**실행 예시**:
```bash
apptainer exec \
  --bind /data:/data \
  /opt/apptainers/KooSimulation313.sif \
  /opt/KooMeshModifier/run.sh --input=input.txt
```

**바인드 마운트**:
- `/data:/data`: 실행 데이터, 결과 (KooChainRun 워크플로우는 /data만 사용)

### LS-DYNA 컨테이너

**이미지**: `LSDynaBasic_ifort2022_impilatest_mpp_s.sif`
**위치**: `/opt/apptainers/LSDynaBasic_ifort2022_impilatest_mpp_s.sif`
**내부 경로**: `/opt/ls-dyna/lsdyna_R16.1.1`

**실행 예시**:
```bash
apptainer exec \
  --bind /data:/data \
  /opt/apptainers/LSDynaBasic_ifort2022_impilatest_mpp_s.sif \
  mpirun -np 16 /opt/ls-dyna/lsdyna_R16.1.1 i=input.k ncpu=16
```

### scenario.json 설정

```json
{
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",

    "apptainer_sif": "/opt/apptainers/KooSimulation313.sif",
    "apptainer_bind": "/data:/data",

    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_ifort2022_impilatest_mpp_s.sif",
    "lsdyna_apptainer_bind": "/data:/data"
  }
}
```

**Apptainer 없이 실행**:
```json
{
  "environment": {
    "koomeshmodifier_path": "/usr/local/bin/koomeshmodifier",
    "lsdyna_path": "/usr/local/bin/lsdyna"
  }
}
```
`apptainer_sif` 필드를 제거하면 직접 실행.

---

## 실행 가이드

### 준비 사항

1. **베이스 모델 준비**:
   - LS-DYNA .k 파일
   - 공유 스토리지에 저장 (`/data/templates/model.k`)

2. **scenario.json 작성**:
   - 프로젝트명, 각도 소스, 연속 낙하 설정

3. **디스크 공간 확인**:
   ```bash
   df -h /data
   ```
   - 케이스당 약 5-10GB (d3plot 포함)
   - 100 케이스 = 약 500GB-1TB

### 실행 절차

#### 1. 테스트 디렉토리 이동
```bash
cd /opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step
```

#### 2. scenario.json 확인
```bash
cat scenario.json
```

#### 3. runner_config.json 생성
```bash
/opt/pyKooCAE/KooChainRun prepare scenario.json -o runner_config.json
```

**출력 예시**:
```
================================================================================
KooChainRun - Prepare Configuration
================================================================================
Scenario: /opt/pyKooCAE/.../scenario.json
Output:   /opt/pyKooCAE/.../runner_config.json

✅ runner_config.json 생성 완료
```

#### 4. 작업 제출
```bash
/opt/pyKooCAE/KooChainRun submit runner_config.json \
    --nodes 2 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
```

**출력 예시**:
```
================================================================================
KooChainRun - Submit Jobs
================================================================================
Config:         runner_config.json
Nodes:          2
Jobs per node:  4
CPUs per job:   16
Total parallel: 8

🚀 대규모 워크플로 시작 - Full_26_Directions_Single_Drop
════════════════════════════════════════════════════════════════════════════════

시나리오: Full_26_Directions_S001
총 DOE 수: 26
총 Step 수: 1

────────────────────────────────────────────────────────────────────────────────
Step 1 처리
────────────────────────────────────────────────────────────────────────────────

1️⃣  runid 디렉토리 생성 중...
✅ runid 디렉토리 생성 완료: 26개

2️⃣  Array Job 제출 중...
🚀 Array Job 제출: Full_26_Directions_S001_Step001
  DOE 범위: 1-26 (26개)
  자원 설정:
    - 노드: 2개
    - 노드당 Job: 4개
    - Job당 CPU: 16개
    - 동시 실행 제한: 8개
    - 예상 Rounds: 4회
────────────────────────────────────────────────────────────────────────────────

Submitted batch job 123456

✅ 모든 Array Job 제출 완료!
```

#### 5. 진행 상황 확인
```bash
# Slurm 큐 확인
squeue -u $USER

# 완료 케이스 수 확인
find /data/Test_001_Full26_1Step -name "Step001.lock" | wc -l
```

#### 6. 결과 수집
```bash
/opt/pyKooCAE/KooChainRun collect runner_config.json results/
```

### 실행 스크립트 사용

각 테스트 디렉토리의 `run.sh` 사용:
```bash
cd Tests/Test_001_Full26_1Step
bash run.sh
```

사용자 확인 후 자동 실행.

---

## 문제 해결

### 작업이 시작 안 됨

**확인 1**: Slurm 큐 확인
```bash
squeue -u $USER
```

**상태별 의미**:
- `PD` (Pending): 대기 중 (리소스 부족)
- `R` (Running): 실행 중
- `CG` (Completing): 완료 중

**확인 2**: 노드 상태
```bash
sinfo
```

### 일부 케이스 실패

**로그 확인**:
```bash
# Slurm 출력
cat /data/Test_001/.../slurm-123456_1.out

# LS-DYNA 로그
cat /data/Test_001/runid_00001/Step001/messag
```

**재실행**:
실패한 케이스만 재실행하려면 scenario.json에서 해당 각도만 남기고 다시 제출.

### 디스크 공간 부족

**확인**:
```bash
df -h /data
du -sh /data/Test_001*
```

**정리**:
```bash
# d3plot 압축
cd /data/Test_001
find . -name "d3plot*" -exec gzip {} \;

# 중간 파일 삭제
find . -name "*.k" -delete  # 회전된 .k 파일 (원본 유지)
```

---

## 예상 실행 시간

### 케이스당 시간 (가정)
- KooMeshModifier: 5분
- LS-DYNA: 2.5시간 (케이스 복잡도에 따라 다름)
- 총: 약 2.5-3시간/케이스

### 시나리오별 예상 시간

| 시나리오 | 케이스 수 | 동시 실행 | Rounds | 예상 시간 |
|---------|----------|----------|--------|----------|
| 6면 1회 | 6 | 8 | 1 | 3시간 |
| 26방향 1회 | 26 | 8 | 4 | 12시간 |
| 26방향 3회 | 26 | 8 | 4 | 36시간 (3 Steps) |
| 피칭 스윕 | 81 | 16 | 6 | 18시간 |
| 피보나치 100 | 100 | 32 | 4 | 12시간 |
| 피보나치 1000 | 1000 | 100 | 10 | 30시간 |

**최적화 팁**:
- 노드를 늘리면 동시 실행 증가, 시간 단축
- Step 수가 많으면 비례하여 시간 증가

---

## 결과 분석

### 디렉토리 구조
```
/data/Test_001_Full26_1Step/
├── runid_00001/
│   ├── metadata.json           # DOE 메타정보
│   └── Step001/
│       ├── metadata.json       # Step 메타정보 (각도 등)
│       ├── input.txt           # KooMeshModifier 입력
│       ├── model_rotated.k     # 회전된 모델
│       ├── d3plot01, d3plot02  # LS-DYNA 결과
│       ├── dynain              # 변형 상태 (다음 Step용)
│       ├── messag              # LS-DYNA 실행 로그
│       └── Step001.lock        # 완료 마크
├── runid_00002/
└── ...
```

### 주요 결과 파일

**d3plot**: 변위, 응력, 변형률 시계열
**dynain**: 최종 변형 상태
**messag**: 에러, 경고, 실행 시간

### 후처리

LS-PrePost로 d3plot 로드:
```bash
/opt/lsprepost/lsprepost d3plot01
```

Python으로 자동 분석:
```python
import lsprepost as lspp

# d3plot 로드
db = lspp.open("d3plot01")

# 최대 응력 추출
stress = db.read_stress()
max_stress = stress.max()
```

---

## 참고 문서

- `README_KooChainRun.md`: KooChainRun CLI 상세 가이드
- `APPTAINER_GUIDE.md`: Apptainer 설정
- `TEMPLATE_README.md`: 대시보드 사용법
- 각 테스트 디렉토리의 `README.md`: 시나리오별 설명

---

**문의**: CAE팀
**버전**: 1.0.0
**최종 수정**: 2026-01-23
