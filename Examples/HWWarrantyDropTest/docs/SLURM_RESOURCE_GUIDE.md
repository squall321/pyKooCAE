# Slurm 자원 점유 및 최적화 가이드

**작성일**: 2026-01-23
**버전**: 1.0

---

## 📊 자원 점유 방식 비교

### 방식 1: 순차 제출 (비효율) ❌

**하나의 Slurm Job으로 모든 시나리오 순차 실행**

```bash
#!/bin/bash
#SBATCH --job-name=cumulative_all
#SBATCH --nodes=1
#SBATCH --cpus-per-task=32
#SBATCH --time=48:00:00

python3 Runner/SimplifiedExecutor.py runner_config.json
```

**자원 점유**:
```
시나리오 1 (3 steps) → 시나리오 2 (5 steps) → ... → 시나리오 5 (3 steps)

총 18 Steps × 2시간/Step = 36시간

자원: 1 노드 × 32 코어 × 36시간 = 1,152 코어·시간
병렬화: 없음 (완전 순차)
```

**문제점**:
- ❌ 시나리오 간 대기 시간 발생
- ❌ 자원 낭비 (Step 전환 시 유휴)
- ❌ 총 소요 시간 매우 김 (36시간)
- ❌ 하나의 시나리오 실패 시 전체 중단

---

### 방식 2: 병렬 제출 (권장) ✅ ⭐

**각 시나리오를 독립 Slurm Job으로 병렬 제출**

```bash
# SlurmSubmitter 사용
python3 Runner/SlurmSubmitter.py runner_config.json --mode=parallel
```

**자원 점유**:
```
시나리오 1 (3 steps) ─┐
시나리오 2 (5 steps) ─┤
시나리오 3 (4 steps) ─┼─ 병렬 실행 (동시)
시나리오 4 (3 steps) ─┤
시나리오 5 (3 steps) ─┘

총 소요 시간: ~10시간 (가장 긴 시나리오 5 steps × 2시간/Step)

자원: 5 노드 × 32 코어 × 10시간 = 1,600 코어·시간
병렬화: 5개 시나리오 동시 실행
```

**장점**:
- ✅ 시간 단축: **7.2배** (36시간 → 10시간)
- ✅ 시나리오 독립 실행 (실패 영향 최소화)
- ✅ 자원 효율성 향상
- ✅ 클러스터 활용도 극대화

**단점**:
- ⚠️ 노드 5개 필요 (동시 실행 시)
- ⚠️ 큐 대기 시간 가능성

---

### 방식 3: Step별 의존성 제출 (고급) 🔧

**각 Step을 독립 Job으로 제출 + --dependency로 연결**

```bash
python3 Runner/SlurmSubmitter.py runner_config.json --mode=dependency
```

**자원 점유**:
```
시나리오 1:
  Step 1 (Job 1) → Step 2 (Job 2, --dependency=afterok:1) → Step 3 (Job 3, --dependency=afterok:2)

시나리오 2:
  Step 1 (Job 4) → Step 2 (Job 5, --dependency=afterok:4) → ...

총 18개 Job (각 Step마다 1개)
각 Job은 이전 Step 완료 후 자동 실행
```

**장점**:
- ✅ 세밀한 제어 (Step별 재실행 가능)
- ✅ Step 실패 시 해당 Step부터 재시작
- ✅ 자원 즉시 반환 (Step 완료 시)

**단점**:
- ⚠️ 복잡도 증가 (18개 Job 관리)
- ⚠️ Slurm 스케줄러 부담 증가

---

## 📈 자원 사용량 비교표

| 방식 | 총 소요 시간 | 노드 수 | 코어·시간 | 병렬화 | 권장도 |
|------|-------------|---------|----------|--------|--------|
| **순차 제출** | 36시간 | 1 | 1,152 | ❌ 없음 | ⭐ |
| **병렬 제출** | 10시간 | 5 | 1,600 | ✅ 5배 | ⭐⭐⭐⭐⭐ |
| **Step별 의존성** | 10시간 | 5 | 1,600 | ✅ 5배 | ⭐⭐⭐ |

**결론**: **병렬 제출 방식(방식 2)** 강력 권장

---

## 🚀 사용법

### 1. 자원 사용량 예측

```bash
python3 Runner/SlurmSubmitter.py runner_config.json --estimate
```

**출력**:
```
====================================================================================================
📊 자원 사용량 예측
====================================================================================================

병렬 제출 방식 (시나리오별 독립 Job):
  - 동시 실행 시나리오 수: 5개
  - 시나리오당 평균 Step: 3.6개
  - 총 Step 수: 18개
  - 자원 점유: 5개 노드 × 32 코어 × 04:00:00
  - 예상 총 소요 시간: ~04:00:00 (가장 긴 시나리오 기준)

순차 제출 방식 (하나의 Job):
  - 총 Step 수: 18개
  - 자원 점유: 1개 노드 × 32 코어
  - 예상 총 소요 시간: ~36.0 시간 (Step당 2.0h 가정)

권장: 병렬 제출 방식
  → 시간 단축: ~7.2배
  → 노드 필요: 5개 (동시 실행 시)
====================================================================================================
```

---

### 2. Dry-Run 테스트

```bash
python3 Runner/SlurmSubmitter.py runner_config.json --dry-run
```

**출력**:
```
🚀 Slurm 병렬 제출 - HWWarranty_CumulativeDrop
====================================================================================================

[1/5] 시나리오 제출: Cuboid_3Steps_SameAngle (Cuboid_3Steps_SameAngle_S003)
  [DRY-RUN] sbatch /path/to/slurm_Cuboid_3Steps_SameAngle_S003.sh
  → Job ID: DRY_RUN_JOB_ID

[2/5] 시나리오 제출: Fibonacci_5Steps_Cyclic (Fibonacci_5Steps_Cyclic_S005)
  [DRY-RUN] sbatch /path/to/slurm_Fibonacci_5Steps_Cyclic_S005.sh
  → Job ID: DRY_RUN_JOB_ID

...

✅ 5개 시나리오 제출 완료!
```

---

### 3. 실제 제출 (병렬 방식)

```bash
# 기본 파티션
python3 Runner/SlurmSubmitter.py runner_config.json --mode=parallel

# 특정 파티션
python3 Runner/SlurmSubmitter.py runner_config.json \
  --partition=high_priority \
  --mode=parallel
```

**출력**:
```
🚀 Slurm 병렬 제출 - HWWarranty_CumulativeDrop
====================================================================================================

[1/5] 시나리오 제출: Cuboid_3Steps_SameAngle (Cuboid_3Steps_SameAngle_S003)
  → Job ID: 123456

[2/5] 시나리오 제출: Fibonacci_5Steps_Cyclic (Fibonacci_5Steps_Cyclic_S005)
  → Job ID: 123457

...

✅ 5개 시나리오 제출 완료!

제출된 Job ID:
  Cuboid_3Steps_SameAngle_S003: 123456
  Fibonacci_5Steps_Cyclic_S005: 123457
  CaseTxt_4Steps_Opposite_S004: 123458
  Thermal_To_Drop_S003: 123459
  Fibonacci_WithTolerance_LHS_S003: 123460
```

---

### 4. 진행 상황 모니터링

```bash
# 제출된 Job 확인
squeue -u $USER

# 특정 Job 상세 정보
scontrol show job 123456

# 로그 파일 확인
tail -f Cuboid_3Steps_SameAngle_S003_123456.out
tail -f Cuboid_3Steps_SameAngle_S003_123456.err
```

---

## 📁 생성되는 파일

### Slurm 스크립트 파일

```bash
# 각 시나리오마다 1개씩 생성
slurm_Cuboid_3Steps_SameAngle_S003.sh
slurm_Fibonacci_5Steps_Cyclic_S005.sh
slurm_CaseTxt_4Steps_Opposite_S004.sh
slurm_Thermal_To_Drop_S003.sh
slurm_Fibonacci_WithTolerance_LHS_S003.sh
```

**예시** (`slurm_Cuboid_3Steps_SameAngle_S003.sh`):
```bash
#!/bin/bash
#SBATCH --job-name=Cuboid_3Steps_SameAngle_S003
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=Cuboid_3Steps_SameAngle_S003_%j.out
#SBATCH --error=Cuboid_3Steps_SameAngle_S003_%j.err

# 환경 변수 설정
export OMP_NUM_THREADS=32
export MKL_NUM_THREADS=32

# 작업 디렉토리 이동
cd /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest

# SimplifiedExecutor 실행 (특정 시나리오만)
python3 Runner/SimplifiedExecutor.py runner_config.json \
  --scenario=Cuboid_3Steps_SameAngle_S003

# 완료 메시지
echo "✅ 시나리오 완료: Cuboid_3Steps_SameAngle_S003"
```

### 로그 파일

```bash
# 각 Job마다 2개씩 생성 (stdout, stderr)
Cuboid_3Steps_SameAngle_S003_123456.out
Cuboid_3Steps_SameAngle_S003_123456.err
Fibonacci_5Steps_Cyclic_S005_123457.out
Fibonacci_5Steps_Cyclic_S005_123457.err
...
```

---

## 🔧 고급 설정

### 1. 노드 수 제한 (순차 대기)

클러스터에 노드가 부족한 경우:

```bash
# 한 번에 2개 시나리오만 실행
# 나머지는 큐에서 대기

# 방법 1: Slurm 파티션 제약 (클러스터 관리자 설정)
# 방법 2: 수동으로 일부만 제출
python3 Runner/SlurmSubmitter.py runner_config_part1.json --mode=parallel
# 완료 후
python3 Runner/SlurmSubmitter.py runner_config_part2.json --mode=parallel
```

---

### 2. 우선순위 설정

```bash
# 특정 시나리오를 high priority로 제출
#SBATCH --partition=high_priority
#SBATCH --qos=high

# 또는 수동으로 우선순위 조정
scontrol update job=123456 priority=10000
```

---

### 3. DOE 케이스별 배열 Job (Array Job)

**대규모 DOE (예: 100개 케이스)인 경우**:

```bash
#!/bin/bash
#SBATCH --job-name=DOE_Array
#SBATCH --array=1-100      # 100개 케이스
#SBATCH --cpus-per-task=32
#SBATCH --time=02:00:00

# Array Task ID를 DOE 인덱스로 사용
DOE_INDEX=$SLURM_ARRAY_TASK_ID

python3 Runner/SimplifiedExecutor.py runner_config.json \
  --scenario=Fibonacci_WithTolerance_LHS_S003 \
  --doe-index=$DOE_INDEX
```

**장점**:
- ✅ 100개 케이스 동시 실행 가능
- ✅ Slurm Array Job 관리 편리
- ✅ 자원 효율 극대화

---

## 💡 권장 워크플로

### 소규모 프로젝트 (시나리오 < 10개)

```bash
# 1. 자원 예측
python3 Runner/SlurmSubmitter.py runner_config.json --estimate

# 2. Dry-run 테스트
python3 Runner/SlurmSubmitter.py runner_config.json --dry-run

# 3. 병렬 제출
python3 Runner/SlurmSubmitter.py runner_config.json --mode=parallel

# 4. 진행 상황 모니터링
squeue -u $USER
```

---

### 대규모 프로젝트 (시나리오 > 50개)

```bash
# 1. 시나리오를 그룹으로 분할
# runner_config_group1.json (시나리오 1-20)
# runner_config_group2.json (시나리오 21-40)
# runner_config_group3.json (시나리오 41-60)

# 2. 그룹별 순차 제출
python3 Runner/SlurmSubmitter.py runner_config_group1.json --mode=parallel
# 완료 후
python3 Runner/SlurmSubmitter.py runner_config_group2.json --mode=parallel
# 완료 후
python3 Runner/SlurmSubmitter.py runner_config_group3.json --mode=parallel
```

---

### DOE 집중 프로젝트 (케이스 > 100개)

```bash
# Array Job 사용
# 각 DOE 케이스를 독립 Array Task로 실행

# 예: 413개 Fibonacci + 10 DOE = 4,130개 케이스
#SBATCH --array=1-4130
```

---

## 📊 자원 효율성 분석

### 예시: 5개 시나리오, 평균 3 Steps

| 메트릭 | 순차 제출 | 병렬 제출 | 개선율 |
|--------|----------|----------|--------|
| **총 소요 시간** | 36시간 | 10시간 | **72% 단축** |
| **노드 사용** | 1개 | 5개 | 5배 증가 |
| **코어·시간** | 1,152 | 1,600 | 39% 증가 |
| **자원 효율** | 낮음 | 높음 | - |
| **실패 영향** | 전체 중단 | 해당 시나리오만 | - |

**결론**:
- 노드가 충분하다면 **병렬 제출 강력 권장**
- 시간 단축 효과가 코어·시간 증가를 상쇄
- 실패 복원력 향상

---

## 🚨 주의사항

### 1. 클러스터 정책 확인

- 노드 사용 제한 확인
- 파티션별 시간 제한 확인
- QoS 정책 확인

```bash
# 파티션 정보 확인
sinfo

# 계정별 제한 확인
sacctmgr show qos
sacctmgr show user $USER
```

---

### 2. 디스크 I/O 병목

대규모 병렬 실행 시 디스크 I/O 병목 가능:

**해결책**:
- 각 시나리오별 독립 디렉토리 사용
- SSD 기반 scratch 공간 활용
- 병렬 파일 시스템 (Lustre, GPFS) 사용

---

### 3. 메모리 설정

시나리오별 메모리 요구량이 다른 경우:

```json
"environment": {
  "memory": "128G"  // 대규모 모델은 더 많은 메모리
}
```

---

## 📞 문의

**작성자**: koo.park
**이메일**: koo.park@samsung.com
**부서**: CAE, HE

---

**버전**: 1.0
**작성일**: 2026-01-23
