# 대규모 시스템 운영 가이드 (수백~만 개 해석)

**작성일**: 2026-01-23
**버전**: 1.0
**대상**: 수백 ~ 1만 개 이상 해석

---

## 🎯 시스템 설계 개요

### 핵심 아키텍처

```
사용자 JSON
    ↓
Designer → runner_config.json
    ↓
LargeScaleDOEManager
    ↓
┌─────────────────────────────────────────────────────────────┐
│ /data/jobs/                                                 │
│ ├── registry/     ← Job 메타데이터 등록                     │
│ │   └── Project/                                            │
│ │       ├── Scenario_S001_DOE00001.json                    │
│ │       ├── Scenario_S001_DOE00002.json                    │
│ │       └── ... (10,000개)                                 │
│ │                                                           │
│ ├── locks/        ← 완료 표시 (Lock 파일)                  │
│ │   └── Project/                                            │
│ │       ├── Scenario_S001_DOE00001.lock  ✅                │
│ │       ├── Scenario_S001_DOE00002.lock  ✅                │
│ │       └── ... (완료된 것만)                              │
│ │                                                           │
│ ├── work/         ← 실제 작업 디렉토리                      │
│ │   └── Scenario/                                           │
│ │       ├── Step001/DOE00001/ (dynain, d3plot...)         │
│ │       ├── Step001/DOE00002/                              │
│ │       └── ...                                            │
│ │                                                           │
│ └── results/      ← 수집된 최종 결과                        │
│     └── Scenario/                                           │
│         ├── Step001/DOE00001/ (복사본)                     │
│         └── ...                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 워크플로

### 1단계: Designer 실행 (JSON → runner_config.json)

```bash
python3 Runner/CumulativeDesigner.py \
  large_scale_config.json \
  -o runner_config.json
```

**예시 JSON** (Fibonacci 10,000 × DOE 10 × 3 Steps = 300,000 Jobs):
```json
{
  "project_name": "LargeScale_Fib10K",
  "scenarios": [
    {
      "scenario_name": "Fib10K_DOE10_3Steps",
      "angle_source": {
        "source_type": "fibonacci_lattice",
        "fibonacci_lattice": {
          "num_points": 10000
        }
      },
      "tolerance": {
        "roll": {"tolerance": 1.0},
        "pitch": {"tolerance": 1.0},
        "doe_type": "lhs",
        "doe_count": 10
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
    }
  ]
}
```

---

### 2단계: Registry 생성 + Array Job 제출

```bash
python3 Runner/LargeScaleDOEManager.py \
  runner_config.json \
  --data-root=/data
```

**실행 결과**:
```
================================================================================
🚀 대규모 워크플로 시작 - Fib10K_DOE10_3Steps
================================================================================

시나리오: Fib10K_DOE10_3Steps_S003
총 DOE 수: 100,000 (10,000 × 10)
총 Step 수: 3

────────────────────────────────────────────────────────────────────────────────
Step 1 처리
────────────────────────────────────────────────────────────────────────────────

1️⃣  Registry 생성 중...
✅ Registry 생성 완료: 100,000개

2️⃣  Array Job 제출 중...
────────────────────────────────────────────────────────────────────────────────
🚀 Array Job 제출: Fib10K_DOE10_3Steps_S003_S001_Array
  DOE 범위: 1-100000 (100,000개)
────────────────────────────────────────────────────────────────────────────────
✅ Job ID: 123456

────────────────────────────────────────────────────────────────────────────────
Step 2 처리
────────────────────────────────────────────────────────────────────────────────

1️⃣  Registry 생성 중...
✅ Registry 생성 완료: 100,000개

2️⃣  Array Job 제출 중...
────────────────────────────────────────────────────────────────────────────────
🚀 Array Job 제출: Fib10K_DOE10_3Steps_S003_S002_Array
  DOE 범위: 1-100000 (100,000개)
  의존성: 123456
────────────────────────────────────────────────────────────────────────────────
✅ Job ID: 123457

────────────────────────────────────────────────────────────────────────────────
Step 3 처리
────────────────────────────────────────────────────────────────────────────────

1️⃣  Registry 생성 중...
✅ Registry 생성 완료: 100,000개

2️⃣  Array Job 제출 중...
────────────────────────────────────────────────────────────────────────────────
🚀 Array Job 제출: Fib10K_DOE10_3Steps_S003_S003_Array
  DOE 범위: 1-100000 (100,000개)
  의존성: 123457
────────────────────────────────────────────────────────────────────────────────
✅ Job ID: 123458

================================================================================
✅ 모든 Array Job 제출 완료!
================================================================================

제출된 Job ID:
  최종 Job ID: 123458

진행 상황 모니터링:
  squeue -u $USER
  ls /data/jobs/locks/LargeScale_Fib10K | wc -l
```

---

### 3단계: 진행 상황 모니터링

#### 방법 1: Slurm 큐 확인

```bash
squeue -u $USER

# 출력 예시:
#   JOBID    PARTITION  NAME                    ST  TIME  NODES
#   123456   normal     Fib10K_..._S001_Array   R   2:30  100
#   123457   normal     Fib10K_..._S002_Array   PD  0:00  0
#   123458   normal     Fib10K_..._S003_Array   PD  0:00  0
```

**상태**:
- `R`: Running (실행 중)
- `PD`: Pending (대기 중, --dependency)

---

#### 방법 2: Lock 파일 카운트

```bash
# 실시간 진행률 확인
watch -n 10 'ls /data/jobs/locks/LargeScale_Fib10K/Fib10K*_S001_*.lock 2>/dev/null | wc -l'

# 출력: 45,672 / 100,000 (45.67%)
```

---

#### 방법 3: 통계 확인

```bash
python3 Runner/LargeScaleDOEManager.py \
  runner_config.json \
  --data-root=/data \
  --stats
```

**출력**:
```
================================================================================
📊 프로젝트 통계 - LargeScale_Fib10K
================================================================================

등록된 Job: 300,000개 (100,000 × 3 Steps)
완료된 Job: 145,672개
전체 진행률: 48.6%

디렉토리:
  Registry: /data/jobs/registry/LargeScale_Fib10K
  Locks: /data/jobs/locks/LargeScale_Fib10K
  Results: /data/jobs/results/LargeScale_Fib10K
================================================================================
```

---

### 4단계: Step 완료 대기 (옵션)

```bash
# Step 1 완료 대기
python3 Runner/LargeScaleDOEManager.py \
  runner_config.json \
  --data-root=/data \
  --wait=1
```

**출력**:
```
================================================================================
⏳ Step 1 완료 대기 중... (예상 DOE: 100,000)
================================================================================

  진행률: 45672/100000 (45.7%) - 2026-01-23 14:30:15
  진행률: 56891/100000 (56.9%) - 2026-01-23 14:31:15
  진행률: 68234/100000 (68.2%) - 2026-01-23 14:32:15
  ...
  진행률: 100000/100000 (100.0%) - 2026-01-23 15:45:00

✅ Step 1 완료! (총 100,000개 DOE)
```

---

### 5단계: 결과 수집

```bash
# Step 1 결과 수집 (/data → /results)
python3 Runner/LargeScaleDOEManager.py \
  runner_config.json \
  --data-root=/data \
  --collect=1
```

**출력**:
```
================================================================================
📦 결과 수집 시작 - Fib10K_DOE10_3Steps_S003 Step 1
================================================================================

총 Lock 파일: 100,000개

  DOE 00001: 3개 파일 복사 완료
  DOE 00002: 3개 파일 복사 완료
  DOE 00003: 3개 파일 복사 완료
  ...
  DOE 100000: 3개 파일 복사 완료

✅ 결과 수집 완료: /data/jobs/results/LargeScale_Fib10K/Fib10K_DOE10_3Steps_S003/Step001
================================================================================
```

**결과 구조**:
```
/data/jobs/results/LargeScale_Fib10K/
└── Fib10K_DOE10_3Steps_S003/
    ├── Step001/
    │   ├── DOE00001/
    │   │   ├── dynain
    │   │   ├── d3plot01
    │   │   └── d3plot02
    │   ├── DOE00002/
    │   └── ... (100,000개)
    ├── Step002/
    └── Step003/
```

---

## 📊 자원 관리

### Slurm Array Job 제한 확인

```bash
# MaxArraySize 확인
scontrol show config | grep MaxArraySize

# 출력 예시:
# MaxArraySize = 100000
```

**제한 초과 시**:
- Array Job을 분할 (예: 1-50000, 50001-100000)
- 또는 클러스터 관리자에게 제한 증가 요청

---

### 분할 제출 (Array > MaxArraySize)

```bash
# 100,000 DOE를 50,000씩 분할

# Batch 1 (1-50,000)
JOB1_1=$(sbatch --parsable --array=1-50000 step1_batch1.sh)

# Batch 2 (50,001-100,000)
JOB1_2=$(sbatch --parsable --array=50001-100000 step1_batch2.sh)

# Step 2는 두 Batch 모두 완료 후
JOB2=$(sbatch --parsable --dependency=afterok:$JOB1_1:$JOB1_2 step2.sh)
```

---

## 🔧 고급 기능

### 1. 실패한 DOE만 재실행

```bash
#!/bin/bash
# 실패한 DOE 찾기

SCENARIO_ID="Fib10K_DOE10_3Steps_S003"
STEP=1

# Registry - Lock 비교 (Lock 없는 것 = 실패)
for registry in /data/jobs/registry/LargeScale_Fib10K/${SCENARIO_ID}_S${STEP}_*.json; do
    registry_id=$(basename "$registry" .json)
    lock_file="/data/jobs/locks/LargeScale_Fib10K/${registry_id}.lock"

    if [ ! -f "$lock_file" ]; then
        echo "실패: $registry_id"
        # 재제출 로직
    fi
done
```

---

### 2. 진행률 대시보드

```bash
#!/bin/bash
# progress_monitor.sh

while true; do
    clear
    echo "======================================================================"
    echo "진행 상황 모니터링 - $(date)"
    echo "======================================================================"

    for step in 1 2 3; do
        total=$(ls /data/jobs/registry/LargeScale_Fib10K/*_S00${step}_*.json 2>/dev/null | wc -l)
        completed=$(ls /data/jobs/locks/LargeScale_Fib10K/*_S00${step}_*.lock 2>/dev/null | wc -l)
        progress=$(echo "scale=1; $completed * 100 / $total" | bc)

        echo "Step $step: $completed / $total ($progress%)"
    done

    echo "======================================================================"
    sleep 60
done
```

---

### 3. 자동 결과 수집 스크립트

```bash
#!/bin/bash
# auto_collect.sh

SCENARIO_ID="Fib10K_DOE10_3Steps_S003"

for step in 1 2 3; do
    echo "Step $step 완료 대기 중..."

    python3 Runner/LargeScaleDOEManager.py \
        runner_config.json \
        --data-root=/data \
        --wait=$step

    echo "Step $step 결과 수집 중..."

    python3 Runner/LargeScaleDOEManager.py \
        runner_config.json \
        --data-root=/data \
        --collect=$step

    echo "Step $step 완료!"
done

echo "모든 Step 완료 및 수집 완료!"
```

---

## 📈 성능 분석

### 예시: Fibonacci 10,000 × DOE 10 × 3 Steps

**총 해석 수**: 300,000개

| 메트릭 | 값 |
|--------|-----|
| **총 DOE** | 100,000개 (10,000 × 10) |
| **총 Step** | 3 |
| **총 Job** | 300,000개 |
| **Slurm Job** | **3개** (Array Job) |
| **Registry 파일** | 300,000개 JSON |
| **Lock 파일** | 300,000개 (완료 시) |
| **예상 디스크** | ~30 GB (Registry + Lock) |
| **예상 시간** | ~9시간 (Step당 3시간 가정) |

---

### 병렬 실행 시 자원

**클러스터 설정**:
- 노드당 32 코어
- 동시 실행 가능 노드: 100개

**계산**:
```
동시 실행 가능 DOE: 100 노드 × 32 코어 / 32 코어 = 100개
총 DOE: 100,000개

Step 1 소요 시간: 100,000 / 100 × 2시간 = 2,000시간? ❌

실제로는 Slurm이 자동 스케줄링:
  → 가용 노드에서 순차 실행
  → 예상: 3~6시간 (클러스터 크기 의존)
```

---

## 🔒 Lock 파일 상세

### Lock 파일 형식

```json
{
  "registry_id": "Fib10K_DOE10_3Steps_S003_S001_DOE00123",
  "completed_at": "2026-01-23T15:30:45",
  "exit_code": 0
}
```

### Lock 파일 활용

```bash
# 완료된 DOE 개수
ls /data/jobs/locks/LargeScale_Fib10K/*.lock | wc -l

# 특정 Step 완료 개수
ls /data/jobs/locks/LargeScale_Fib10K/*_S001_*.lock | wc -l

# 실패한 DOE 찾기 (Lock 없는 것)
comm -23 \
  <(ls /data/jobs/registry/LargeScale_Fib10K/*_S001_*.json | sed 's/.json//') \
  <(ls /data/jobs/locks/LargeScale_Fib10K/*_S001_*.lock | sed 's/.lock//')
```

---

## 🚨 문제 해결

### Q1: "MaxArraySize 초과" 오류

**원인**: Slurm Array Job 크기 제한 초과

**해결**:
```bash
# 방법 1: 분할 제출
--array=1-50000
--array=50001-100000

# 방법 2: 클러스터 관리자에게 제한 증가 요청
scontrol show config | grep MaxArraySize
```

---

### Q2: Registry 파일이 너무 많아서 느림

**원인**: 10만+ 파일로 인한 파일 시스템 부담

**해결**:
```bash
# 하위 디렉토리 분산 (해시 기반)
/data/jobs/registry/Project/
├── 00/
│   ├── Scenario_S001_DOE00001.json
│   └── ...
├── 01/
│   ├── Scenario_S001_DOE00100.json
│   └── ...
└── 99/
```

**구현** (LargeScaleDOEManager 수정):
```python
# DOE 인덱스 → 해시 디렉토리
hash_dir = f"{doe_index % 100:02d}"
registry_file = os.path.join(
    self.registry_dir,
    hash_dir,
    f"{registry_id}.json"
)
```

---

### Q3: Lock 파일 체크가 느림

**원인**: 10만+ glob 패턴 매칭

**해결**:
```bash
# 방법 1: 데이터베이스 사용 (SQLite)
# Registry + Lock 상태를 DB에 저장

# 방법 2: 카운터 파일 사용
/data/jobs/locks/Project/
├── .counter_S001  ← 완료 개수만 저장
└── ...

# Lock 생성 시 카운터 증가
flock /data/jobs/locks/Project/.counter_S001 \
  echo $(($(cat /data/jobs/locks/Project/.counter_S001) + 1)) > /data/jobs/locks/Project/.counter_S001
```

---

## 📞 문의

**작성자**: koo.park
**이메일**: koo.park@samsung.com
**부서**: CAE, HE

---

**버전**: 1.0
**작성일**: 2026-01-23
**대상**: 대규모 시스템 (수백~만 개 해석)
