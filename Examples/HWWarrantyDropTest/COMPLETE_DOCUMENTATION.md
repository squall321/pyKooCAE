# HW Warranty Drop Test - 완전 문서

**프로젝트**: KooChainRun
**버전**: 1.0.0
**작성일**: 2026-01-23

---

## 문서 구성

이 프로젝트는 다음 문서들로 구성됩니다:

### 1. 사용자 가이드
**위치**: `USER_GUIDE.md`

**내용**:
- 낙하 시나리오 유형 (6면, 26방향, 피칭/롤링 스윕, 피보나치)
- 연속 낙하 (Cumulative Drop) 개념 및 실행 흐름
- 리소스 사용 정책 (노드, 코어, Array Job)
- Apptainer 컨테이너 구성
- 실행 가이드 및 문제 해결

**대상**: CAE 엔지니어, 일반 사용자

### 2. 테스트 시나리오 모음
**위치**: `Tests/README.md`

**내용**:
- Test_001 ~ Test_005 상세 설명
- 각 테스트의 목적, 조건, 실행 시간
- 리소스 요구사항 비교표
- 실행 패턴 (순차 vs 병렬)

**대상**: 테스트 실행자

### 3. Apptainer 통합 가이드
**위치**: `APPTAINER_GUIDE.md`

**내용**:
- 컨테이너 분리 전략
- KooMeshModifier vs LS-DYNA 컨테이너
- 바인드 마운트 설정
- scenario.json 설정 방법

**대상**: 시스템 관리자, 고급 사용자

### 4. Job Template (대시보드 통합)
**위치**: `TEMPLATE_README.md`, `hw_warranty_droptest.yaml`

**내용**:
- 웹 UI를 통한 작업 제출
- 파일 업로드 방식
- 대시보드 배포 방법

**대상**: 대시보드 사용자

### 5. KooChainRun CLI
**위치**: `../../README_KooChainRun.md`

**내용**:
- KooChainRun 명령어 상세 가이드
- prepare, submit, status, collect 사용법
- 전체 워크플로 설명

**대상**: CLI 사용자

### 6. 빠른 시작 가이드
**위치**: `../../QUICK_START_GUIDE.md`

**내용**:
- 5분 안에 첫 실행
- 간단한 예시
- 핵심 개념 요약

**대상**: 신규 사용자

---

## 전체 디렉토리 구조

```
/opt/pyKooCAE/
├── KooChainRun                              # CLI 실행 파일
├── README_KooChainRun.md              # CLI 가이드
├── QUICK_START_GUIDE.md               # 빠른 시작
├── CONTEXT_UPDATE.md                  # 개발 컨텍스트
│
├── Runner/
│   ├── CumulativeDesigner.py          # scenario → runner_config 변환
│   ├── LargeScaleDOEManager.py        # 대규모 DOE 관리 (Slurm 제출)
│   ├── AngleSourceParser.py           # 각도 소스 파싱
│   ├── AngleMixingStrategy.py         # 각도 믹싱 전략
│   ├── ToleranceDOEGenerator.py       # DOE 생성
│   └── TemplateManager.py             # 템플릿 선택
│
└── Examples/HWWarrantyDropTest/
    ├── USER_GUIDE.md                  # 사용자 메인 가이드 ✨
    ├── APPTAINER_GUIDE.md             # Apptainer 설정
    ├── TEMPLATE_README.md             # 대시보드 가이드
    ├── SETUP_COMPLETE.md              # 설치 완료 요약
    ├── hw_warranty_droptest.yaml      # Job Template
    │
    └── Tests/
        ├── README.md                  # 테스트 시나리오 모음 ✨
        │
        ├── Test_001_Full26_1Step/
        │   ├── scenario.json          # 26방향 1회 낙하
        │   ├── run.sh
        │   └── README.md
        │
        ├── Test_002_Full26_3Step/
        │   ├── scenario.json          # 26방향 3회 연속 낙하
        │   └── run.sh
        │
        ├── Test_003_6Faces_Cyclic/
        │   ├── scenario.json          # 6면 3회 Cyclic
        │   └── run.sh
        │
        ├── Test_004_Pitching_Sweep/
        │   ├── scenario.json          # Pitch -40°~+40°
        │   └── run.sh
        │
        └── Test_005_Fibonacci_100/
            ├── scenario.json          # 100방향 균일분포
            └── run.sh
```

---

## 실행 흐름 전체 개요

### 입력 → 출력

```
scenario.json
    ↓ (KooChainRun prepare)
runner_config.json
    ↓ (KooChainRun submit)
Slurm Array Jobs (제출)
    ↓
컴퓨트 노드 실행
    ├─ metadata.json 읽기
    ├─ KooMeshModifier (Apptainer)
    ├─ LS-DYNA (Apptainer)
    └─ .lock 파일 생성
    ↓
결과 디렉토리
    └─ /data/<project>/runid_XXXXX/StepNNN/
        ├─ d3plot01, d3plot02, ...
        ├─ dynain
        └─ messag
```

### 단계별 상세

#### 1. scenario.json 작성
```json
{
  "project_name": "MyProject",
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "apptainer_sif": "/opt/apptainers/KooSimulation313.sif",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_*.sif"
  },
  "scenarios": [
    {
      "scenario_name": "MyScenario",
      "template": "/data/templates/model.k",
      "angle_source": {
        "source_type": "cuboid_geometry",
        "cuboid_geometry": {
          "include_faces": true,
          "include_edges": true,
          "include_corners": true
        }
      },
      "cumulative": {
        "num_steps": 3,
        "mode_sequence": ["DROP", "DROP", "DROP"],
        "angle_mixing": {
          "strategy": "same_angle"
        }
      }
    }
  ]
}
```

#### 2. runner_config.json 생성
```bash
/opt/pyKooCAE/KooChainRun prepare scenario.json -o runner_config.json
```

**출력**:
- 26개 각도 생성 (cuboid_geometry)
- 3 Steps × 26 케이스 = 78개 step 설정
- 각 step에 angle, template, doe_index 할당

#### 3. Slurm 작업 제출
```bash
/opt/pyKooCAE/KooChainRun submit runner_config.json \
    --nodes 2 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
```

**동작**:
1. runid 디렉토리 생성 (26개)
2. metadata.json 작성 (각 Step별)
3. Slurm 스크립트 생성
4. Array Job 제출 (Step 1: --array=1-26%8)
5. Step 2, 3 제출 (의존성: afterok)

#### 4. 컴퓨트 노드 실행

**Step 1** (각 케이스):
```bash
# metadata.json 읽기
TEMPLATE=$(jq -r .template metadata.json)
ROLL=$(jq -r .angle.roll metadata.json)
PITCH=$(jq -r .angle.pitch metadata.json)
YAW=$(jq -r .angle.yaw metadata.json)

# KooMeshModifier: 메쉬 회전
apptainer exec KooSimulation313.sif \
    /opt/KooMeshModifier/run.sh --input=input.txt

# LS-DYNA: 낙하 시뮬레이션
apptainer exec LSDynaBasic_*.sif \
    mpirun -np 16 lsdyna i=rotated.k ncpu=16

# 완료 마크
touch Step001.lock
```

**Step 2** (각 케이스):
```bash
# DYNAIN_TO_INITIAL: Step 1 dynain → Initial.k
apptainer exec KooSimulation313.sif \
    /opt/KooMeshModifier/run.sh --input=dynaintoinitial.txt

# KooMeshModifier: Initial.k 회전
apptainer exec KooSimulation313.sif \
    /opt/KooMeshModifier/run.sh --input=input.txt

# LS-DYNA: 2차 낙하
apptainer exec LSDynaBasic_*.sif \
    mpirun -np 16 lsdyna i=rotated.k ncpu=16

# 완료 마크
touch Step002.lock
```

#### 5. 진행 상황 확인
```bash
# Slurm 큐
squeue -u $USER

# 완료 케이스 수
find /data/MyProject -name "*.lock" | wc -l

# 상세 진행률
KooChainRun status
```

#### 6. 결과 수집
```bash
KooChainRun collect runner_config.json results/
```

---

## 핵심 알고리즘 설명

### 1. Cuboid Geometry (26방향)

육면체의 기하학적 대칭성을 이용한 방향 생성.

**원리**:
```
Face (6개): ±X, ±Y, ±Z 축
Edge (12개): 면과 면의 교선 (45° 조합)
Corner (8개): 세 면의 교점 (3차원 대각선)
```

**예시**:
```
Face:
  F1_Top    = (Roll=0°,   Pitch=0°,   Yaw=0°)
  F2_Bottom = (Roll=180°, Pitch=0°,   Yaw=0°)

Edge:
  E1_Top_Front = (Roll=45°, Pitch=0°, Yaw=0°)
  E2_Top_Back  = (Roll=-45°, Pitch=0°, Yaw=0°)

Corner:
  C1_Top_Front_Left = (Roll=35.264°, Pitch=45°, Yaw=0°)   # 꼭짓점 각 asin(1/√3)
```

### 2. Fibonacci Lattice (균일분포)

황금비를 이용한 구형 표면 균일분포 알고리즘.

**원리**:
```python
phi = (1 + sqrt(5)) / 2  # 황금비 ≈ 1.618
N = 100  # 방향 개수

for i in range(N):
    # 방위각 (황금각)
    theta = 2 * pi * i / phi

    # 높이 (균일 분포)
    z = 1 - (2*i + 1) / N

    # 반지름
    r = sqrt(1 - z*z)

    # 직교좌표
    x = r * cos(theta)
    y = r * sin(theta)

    # (x,y,z) → (roll, pitch, yaw) 변환
```

**장점**:
- 극점 집중 없음 (격자 패턴 대비)
- 개수 자유 조정 (10, 100, 1000 등)
- 수학적으로 증명된 최적 분포

**비교**:
```
Grid Pattern (위도/경도 격자):
  - 극점에 점이 몰림
  - 적도 부근 희소

Fibonacci Lattice:
  - 구면 전체 균일
  - 나선형 배치
```

### 3. Array Job 병렬 실행

Slurm의 Array Job을 이용한 효율적 병렬화.

**원리**:
```bash
# 전통적 방식 (비효율)
for i in {1..26}; do
    sbatch case_${i}.sh  # 26번 스케줄러 호출
done

# Array Job 방식 (효율)
sbatch --array=1-26%8 batch.sh  # 1번 호출, 8개씩 자동 실행
```

**동작**:
```
Slurm 스케줄러:
  Job Array 123456
    ├─ Task 1  (Running)  ─┐
    ├─ Task 2  (Running)   │
    ├─ Task 3  (Running)   ├─ Round 1 (8개 동시)
    ├─ Task 4  (Running)   │
    ├─ Task 5  (Running)   │
    ├─ Task 6  (Running)   │
    ├─ Task 7  (Running)   │
    ├─ Task 8  (Running)  ─┘
    ├─ Task 9  (Pending)  ─┐
    ├─ Task 10 (Pending)   ├─ Round 2 (대기)
    ...                     │
    └─ Task 26 (Pending)  ─┘
```

**장점**:
- 스케줄러 부하 최소화
- 자동 큐잉 (완료되면 다음 자동 시작)
- 단일 Job ID로 관리 용이

### 4. Step 간 의존성 (afterok)

Step 2는 Step 1의 dynain 파일이 필요하므로 의존성 설정.

**원리**:
```bash
# Step 1 제출
JOB1=$(sbatch --array=1-26%8 step1.sh | awk '{print $4}')
# 출력: Submitted batch job 123456

# Step 2 제출 (Step 1 완료 대기)
JOB2=$(sbatch --array=1-26%8 --dependency=afterok:123456 step2.sh | awk '{print $4}')
# 123456의 모든 Task(1-26)가 성공(exit 0)해야 시작

# Step 3 제출
JOB3=$(sbatch --array=1-26%8 --dependency=afterok:$JOB2 step3.sh)
```

**타임라인**:
```
Time ─────────────────────────────────────────────────▶

Step 1: [■■■■■■■■■■■■] (12시간)
         ↓ (모든 Task 완료 확인)
Step 2:                   [■■■■■■■■■■■■] (12시간)
                           ↓ (모든 Task 완료 확인)
Step 3:                                     [■■■■■■■■■■■■] (12시간)
```

**vs 파이프라인 방식** (잘못된 접근):
```
# 각 DOE를 독립적으로 Step 1→2→3 실행
runid_00001: Step1 → Step2 → Step3
runid_00002:   Step1 → Step2 → Step3
...

문제:
- runid_00026이 Step 1 완료되기 전까지 Step 2 시작 불가
- 리소스 낭비 (일부 노드만 사용)
```

### 5. Apptainer 컨테이너 실행

**원리**:
```bash
apptainer exec \
  --bind /data:/data \
  /opt/apptainers/KooSimulation313.sif \
  /opt/KooMeshModifier/run.sh --input=input.txt
```

**동작**:
1. SIF 이미지 마운트
2. `/data`, `/shared` 바인드 (호스트 → 컨테이너)
3. 컨테이너 내부에서 `/opt/KooMeshModifier/run.sh` 실행
4. 결과는 바인드된 `/data`에 저장 (호스트에서 접근 가능)

**장점**:
- 의존성 격리 (호스트 환경 독립)
- 재현성 보장
- 버전 관리 용이

---

## 리소스 사용 정책 상세

### 노드 및 코어 할당 전략

#### 기본 리소스 단위
```
1 Node = 128 CPU cores
```

#### 할당 공식
```
concurrent_jobs = nodes × jobs_per_node
total_cpus = concurrent_jobs × ncpu_per_job
```

#### 예시 1: 소규모 (26 케이스)
```
nodes = 2
jobs_per_node = 4
ncpu_per_job = 16

concurrent = 2 × 4 = 8
total_cpus = 8 × 16 = 128 코어 (노드 1개 분량)
```

**실행**:
- Round 1: 케이스 1-8 (8개 동시)
- Round 2: 케이스 9-16
- Round 3: 케이스 17-24
- Round 4: 케이스 25-26 (2개만, 6개 유휴)

**효율**: 89% (24/26 케이스가 풀 로드)

#### 예시 2: 중규모 (100 케이스)
```
nodes = 4
jobs_per_node = 8
ncpu_per_job = 16

concurrent = 4 × 8 = 32
total_cpus = 32 × 16 = 512 코어 (노드 4개)
```

**실행**:
- Round 1-3: 32개씩 (96 케이스)
- Round 4: 4개 (28개 유휴)

**효율**: 96%

#### 예시 3: 대규모 (1000 케이스)
```
nodes = 10
jobs_per_node = 10
ncpu_per_job = 16

concurrent = 10 × 10 = 100
total_cpus = 100 × 16 = 1600 코어 (노드 12.5개)
```

**실행**:
- 10 Rounds (100개씩)

**효율**: 100%

### 전용 노드 vs 공유 노드

**전용 노드** (300대):
```bash
#SBATCH --partition=exclusive
#SBATCH --exclusive
```
- 노드 독점 사용
- 성능 일관성 보장
- 대규모 작업에 적합

**공유 노드** (46대):
```bash
#SBATCH --partition=shared
```
- 다른 사용자와 공유
- 소규모 테스트에 적합
- 대기 시간 짧음

### 메모리 할당

**기본값**: 64GB/Job
```bash
#SBATCH --mem=64G
```

**계산**:
- LS-DYNA 메모리: ~50GB (케이스 복잡도에 따라)
- KooMeshModifier: ~5GB
- 여유 공간: ~9GB

**대규모 모델**:
```bash
#SBATCH --mem=128G
```

### 시간 제한

**기본값**: 7200초 (2시간)
```bash
#SBATCH --time=02:00:00
```

**계산**:
- KooMeshModifier: 5분
- LS-DYNA: 1-3시간 (모델 크기에 따라)
- 여유 시간: 충분

**대규모 모델**:
```bash
#SBATCH --time=06:00:00
```

---

## 예상 실행 시간 상세

### 케이스당 시간 분해

**Step 1** (DROP_FIRST):
```
1. metadata.json 읽기: 1초
2. input.txt 생성: 1초
3. KooMeshModifier (회전): 5분
4. LS-DYNA 실행: 2.5시간
5. 완료 마크: 1초
─────────────────────────
총: 약 2.5시간
```

**Step 2+** (DROP_CUMULATIVE):
```
1. DYNAIN_TO_INITIAL: 10분
2. KooMeshModifier (회전): 5분
3. LS-DYNA 실행: 2.5시간
4. 완료 마크: 1초
─────────────────────────
총: 약 2.75시간
```

### 시나리오별 총 시간

#### Test_001 (26 케이스, 1 Step)
```
케이스당: 2.5시간
동시 실행: 8개
Rounds: 4회 (8+8+8+2)

총 시간 = 2.5h × 4 rounds = 10시간
+ 스케줄링 오버헤드 (~2시간)
= 약 12시간
```

#### Test_002 (26 케이스, 3 Steps)
```
Step 1: 2.5h × 4 rounds = 10h
Step 2: 2.75h × 4 rounds = 11h
Step 3: 2.75h × 4 rounds = 11h

총 시간 = 10 + 11 + 11 + 오버헤드 = 약 34-36시간
```

#### Test_005 (100 케이스, 1 Step)
```
케이스당: 2.5시간
동시 실행: 32개
Rounds: 4회 (32+32+32+4)

총 시간 = 2.5h × 4 rounds = 10시간
+ 오버헤드 = 약 12시간
```

### 병렬 효율

**이상적 경우** (100% 효율):
```
100 케이스, 100 동시 실행
총 시간 = 2.5시간 (1 round)
```

**실제 경우** (Test_005):
```
100 케이스, 32 동시 실행
총 시간 = 2.5h × 4 = 10시간

병렬 효율 = (100 × 2.5h) / (32 × 10h) = 78%
```

**마지막 Round의 비효율**:
```
Round 4: 4 케이스만 실행, 28개 슬롯 유휴
유휴율 = 28 / 32 = 87.5%
```

---

## 자주 묻는 질문 (FAQ)

### Q1. 26방향과 100방향 중 어떤 걸 써야 하나?

**26방향 (Cuboid)**:
- 기하학적으로 의미 있는 방향
- 해석 용이 (Top, Bottom, Front 등)
- 빠른 실행 (~12시간)
- **권장**: 기본 보증 테스트

**100방향 (Fibonacci)**:
- 전방향 균일 샘플링
- 통계적 분석에 적합
- 극한 케이스 탐색
- **권장**: 상세 분석, 연구 목적

### Q2. 연속 낙하를 몇 번까지 해야 하나?

**1회**: 단일 낙하 테스트
**2-3회**: 반복 낙하 내구성 (일반적)
**5회 이상**: 극한 내구성 테스트

**예시**:
- 스마트폰 보증: 1.5m 높이 1회
- 군용 장비: 1.2m 높이 26방향 5회

### Q3. 실행 시간을 줄이려면?

**방법 1**: 노드 증가
```bash
--nodes 10 --jobs-per-node 10  # 동시 100개
```

**방법 2**: 모델 간소화
- 메쉬 크기 증가 (요소 수 감소)
- 시뮬레이션 시간 단축

**방법 3**: 방향 개수 감소
- 26방향 → 6면만

### Q4. 디스크 공간이 부족하면?

**방법 1**: d3plot 압축
```bash
find /data -name "d3plot*" -exec gzip {} \;
```

**방법 2**: 중간 파일 삭제
```bash
# 회전된 .k 파일 (재생성 가능)
find /data -name "*_rotated.k" -delete
```

**방법 3**: 아카이빙
```bash
tar -czf Test_001_results.tar.gz /data/Test_001
rm -rf /data/Test_001
```

### Q5. 작업이 실패하면?

**확인 1**: Slurm 로그
```bash
cat slurm-*.out
```

**확인 2**: LS-DYNA 로그
```bash
cat messag
```

**재실행**:
실패한 케이스만 scenario.json에서 해당 각도만 남기고 재제출.

---

## 문의 및 지원

**프로젝트 위치**: `/opt/pyKooCAE`
**문서 위치**: `/opt/pyKooCAE/Examples/HWWarrantyDropTest/`

**주요 문서**:
- `USER_GUIDE.md`: 사용자 메인 가이드
- `Tests/README.md`: 테스트 시나리오 모음
- `APPTAINER_GUIDE.md`: 컨테이너 설정
- `../../README_KooChainRun.md`: CLI 가이드

**버전**: 1.0.0
**최종 수정**: 2026-01-23
