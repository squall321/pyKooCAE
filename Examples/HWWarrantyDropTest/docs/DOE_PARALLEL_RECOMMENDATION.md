# DOE 병렬 처리 최적화 권장사항

**작성일**: 2026-01-23
**버전**: 1.0

---

## 🎯 핵심 질문에 대한 답변

### Q: "여러 스텝의 멀티 해석 후의 멀티 해석인 경우, 어떻게 병렬 제출하는게 최적인가?"

**A: 규모에 따라 다름** (결론부터)

| DOE 규모 | 권장 방식 | 이유 |
|---------|----------|------|
| **< 500 케이스** | **방식 A: Dependency Chain** ⭐⭐⭐⭐⭐ | Slurm 네이티브, 안정적, 간단 |
| **500~2,000 케이스** | **방식 B: Lock Polling** ⭐⭐⭐⭐ | 동적 관리, Slurm 부담 감소 |
| **> 2,000 케이스** | **방식 C: Array Job** ⭐⭐⭐⭐⭐ | Slurm 최적화, 관리 편리 |

---

## 📊 시나리오 분석

### 예시: Fibonacci 10 points × DOE 5 samples × 3 Steps

```
총 케이스: 10 × 5 = 50 DOE
총 Jobs: 50 DOE × 3 Steps = 150 Jobs

Step 1: 50 DOE 병렬 → dynain 50개 생성
Step 2: 50 DOE 병렬 → dynain 50개 생성 (Step 1 dynain 필요)
Step 3: 50 DOE 병렬 → 최종 결과 (Step 2 dynain 필요)
```

**핵심 제약**:
- Step 2는 **같은 DOE의 Step 1** 완료 후에만 실행 가능
- Step 3은 **같은 DOE의 Step 2** 완료 후에만 실행 가능

---

## 🔧 방식 A: Dependency Chain (권장, DOE < 500) ⭐

### 개념

```
DOE 1: [Step 1] → [Step 2 --dependency=afterok:Job1] → [Step 3 --dependency=afterok:Job2]
DOE 2: [Step 1] → [Step 2 --dependency=afterok:Job4] → [Step 3 --dependency=afterok:Job5]
DOE 3: [Step 1] → [Step 2 --dependency=afterok:Job7] → [Step 3 --dependency=afterok:Job8]
...
DOE 50: [Step 1] → [Step 2 --dependency=afterok:Job148] → [Step 3 --dependency=afterok:Job149]

총 150 Jobs (모두 한 번에 제출)
```

### 장점

✅ **Slurm 네이티브 기능**
- --dependency=afterok 사용
- Slurm이 자동으로 의존성 관리
- Lock 파일 불필요

✅ **안정적이고 간단**
- 모든 Job을 한 번에 제출
- 자동 스케줄링 (큐에서 대기)
- 재제출 불필요

✅ **진행 상황 추적**
```bash
squeue -u $USER  # 대기 중인 Job 확인
```

### 단점

⚠️ **Job ID 관리 필요**
- 150개 Job ID 추적 필요
- 스크립트에서 자동 관리 가능

⚠️ **Slurm 스케줄러 부담**
- 대규모 (수천 Job)시 스케줄러 부담 증가
- 하지만 500 이하는 문제없음

### 구현

```python
# DOEParallelOptimizer.py 사용
python3 Runner/DOEParallelOptimizer.py runner_config.json --method=dependency
```

**생성되는 구조**:
```bash
# 모든 Job 한 번에 제출
sbatch slurm_Scenario_DOE001_S001.sh
sbatch slurm_Scenario_DOE001_S002.sh --dependency=afterok:123456
sbatch slurm_Scenario_DOE001_S003.sh --dependency=afterok:123457
sbatch slurm_Scenario_DOE002_S001.sh
sbatch slurm_Scenario_DOE002_S002.sh --dependency=afterok:123459
...
```

---

## 🔧 방식 B: Lock File Polling (대안, DOE 500~2,000)

### 개념

```
1. Step 1 (DOE 1-50) 병렬 제출
2. 각 DOE Step 1 완료 시 Lock 파일 생성
   - .locks/Step001_DOE001.lock
   - .locks/Step001_DOE002.lock
   - ...
3. Poller Job: 50개 Lock 파일 대기
4. 모든 Lock 확인 후 Step 2 (DOE 1-50) 제출
5. 반복...
```

### 장점

✅ **진행 상황 추적 용이**
```bash
ls .locks/Step001_*.lock | wc -l
# → 현재 완료된 DOE 개수
```

✅ **동적 재제출 가능**
- 실패한 DOE만 재제출
- Lock 파일 없으면 다시 실행

✅ **Slurm 스케줄러 부담 적음**
- Step당 50개 Job만 제출
- 순차적 제출로 부담 감소

### 단점

⚠️ **Polling 오버헤드**
- Poller Job이 1분마다 체크
- 자원 소모 (미미하지만)

⚠️ **Lock 파일 관리 필요**
- 디스크 I/O 증가
- 파일 시스템 부담

⚠️ **복잡도 증가**
- Poller Job 로직 필요
- 디버깅 어려움

### 구현

```python
python3 Runner/DOEParallelOptimizer.py runner_config.json --method=lock
```

**동작 흐름**:
```bash
# Step 1: 50 DOE 제출
for i in {1..50}; do
  sbatch slurm_DOE${i}_S001.sh  # 완료 시 Lock 생성
done

# Poller Job 제출
sbatch poller_S001.sh  # Lock 50개 대기 → Step 2 자동 제출

# Step 2: Poller가 자동 제출
for i in {1..50}; do
  sbatch slurm_DOE${i}_S002.sh
done

# Poller Job 제출
sbatch poller_S002.sh  # → Step 3 자동 제출
```

---

## 🔧 방식 C: Array Job (최적, DOE > 2,000) ⭐⭐⭐

### 개념

```
# Step 1: Array Job (1-50)
sbatch --array=1-50 slurm_step1.sh

# Step 2: Array Job (1-50, dependency)
sbatch --array=1-50 --dependency=afterok:123456 slurm_step2.sh

# Step 3: Array Job (1-50, dependency)
sbatch --array=1-50 --dependency=afterok:123457 slurm_step3.sh

총 3개 Job (각각 50개 Task 포함)
```

### 장점

✅ **Slurm 최적화**
- Array Job은 Slurm 네이티브 기능
- 스케줄러 부담 최소화

✅ **관리 편리**
- 3개 Job ID만 관리 (150개 아님)
- 진행 상황 추적 쉬움

✅ **확장성**
- 수천~수만 케이스 가능
- Slurm 성능 저하 없음

### 단점

⚠️ **Array Task 간 의존성 제한**
- Array Job 전체에만 의존성 설정 가능
- 개별 Task 간 의존성 불가능
- **하지만 우리 경우는 문제없음!** (Step 전체 완료 후 다음 Step)

### 구현

```bash
#!/bin/bash
# slurm_step1_array.sh
#SBATCH --array=1-50
#SBATCH --job-name=Step1_Array

DOE_INDEX=$SLURM_ARRAY_TASK_ID

/opt/KooMeshModifier/run.sh \
  --step=1 \
  --doe-index=$DOE_INDEX
```

```bash
# 제출
JOB1=$(sbatch --parsable slurm_step1_array.sh)
JOB2=$(sbatch --parsable --dependency=afterok:$JOB1 slurm_step2_array.sh)
JOB3=$(sbatch --parsable --dependency=afterok:$JOB2 slurm_step3_array.sh)

echo "Step 1: $JOB1"
echo "Step 2: $JOB2 (depends on $JOB1)"
echo "Step 3: $JOB3 (depends on $JOB2)"
```

---

## 📊 성능 비교

### 시나리오: 50 DOE × 3 Steps = 150 Jobs

| 메트릭 | 방식 A (Dependency) | 방식 B (Lock) | 방식 C (Array) |
|--------|-------------------|--------------|---------------|
| **Job 개수** | 150개 | 50 + 2 Poller | 3개 (Array) |
| **Slurm 부담** | 중간 | 낮음 | 매우 낮음 |
| **관리 복잡도** | 낮음 | 높음 | 낮음 |
| **진행 추적** | squeue | Lock 파일 | squeue |
| **재실행** | 개별 Job | Lock 확인 | Array Task |
| **확장성** | ~500 | ~2,000 | **무한** |
| **권장도** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 💡 최종 권장사항

### 프로젝트 규모별

#### 소규모 (DOE < 100)
**방식 A: Dependency Chain** ⭐⭐⭐⭐⭐

```bash
python3 Runner/DOEParallelOptimizer.py runner_config.json --method=dependency
```

**이유**:
- 가장 간단하고 안정적
- Slurm 부담 없음
- Lock 파일 불필요

---

#### 중규모 (DOE 100~500)
**방식 A 또는 C** ⭐⭐⭐⭐⭐

```bash
# 방식 A (간단)
python3 Runner/DOEParallelOptimizer.py runner_config.json --method=dependency

# 또는 방식 C (확장성)
# Array Job 스크립트 작성
```

**이유**:
- 방식 A도 충분히 작동
- 방식 C는 확장성 고려 시

---

#### 대규모 (DOE > 500)
**방식 C: Array Job** ⭐⭐⭐⭐⭐

```bash
# Array Job 사용 (권장)
# Step별 Array Job 스크립트 작성
```

**이유**:
- Slurm 스케줄러 부담 최소화
- 관리 편리 (Job ID 3개만)
- 무한 확장 가능

---

## 🚀 실전 사용 예시

### Case 1: 소규모 프로젝트 (Cuboid 26 × DOE 5 = 130 Jobs)

**권장**: 방식 A (Dependency Chain)

```bash
# 1. runner_config.json 생성
python3 Runner/CumulativeDesigner.py user_config.json -o runner_config.json

# 2. DOE 병렬 제출 (Dependency)
python3 Runner/DOEParallelOptimizer.py runner_config.json --method=dependency

# 3. 진행 상황 확인
squeue -u $USER
```

**결과**:
- 130개 Job 한 번에 제출
- Slurm이 자동으로 의존성 관리
- 총 소요 시간: ~6시간 (Step당 2시간 가정)

---

### Case 2: 중규모 프로젝트 (Fibonacci 413 × DOE 10 = 12,390 Jobs)

**권장**: 방식 C (Array Job)

```bash
# 1. Array Job 스크립트 준비
# slurm_step1_array.sh (--array=1-4130)
# slurm_step2_array.sh (--array=1-4130)
# slurm_step3_array.sh (--array=1-4130)

# 2. 순차 제출
JOB1=$(sbatch --parsable slurm_step1_array.sh)
JOB2=$(sbatch --parsable --dependency=afterok:$JOB1 slurm_step2_array.sh)
JOB3=$(sbatch --parsable --dependency=afterok:$JOB2 slurm_step3_array.sh)

# 3. 진행 상황 확인
squeue -u $USER
scontrol show job $JOB1
```

**결과**:
- 3개 Job ID만 관리
- 4,130 Task × 3 Steps = 12,390 Task 자동 실행
- Slurm 스케줄러 부담 최소

---

### Case 3: 극대규모 프로젝트 (Fibonacci 41,253 × DOE 10 = 1,237,590 Jobs)

**권장**: 방식 C (Array Job) + 분할 실행

```bash
# 너무 크므로 분할 (Slurm 제한 고려)
# 예: 10,000 Task씩 분할

# Group 1: Array 1-10,000
JOB1_1=$(sbatch --parsable --array=1-10000 slurm_step1_array.sh)
JOB2_1=$(sbatch --parsable --array=1-10000 --dependency=afterok:$JOB1_1 slurm_step2_array.sh)

# Group 2: Array 10,001-20,000
JOB1_2=$(sbatch --parsable --array=10001-20000 slurm_step1_array.sh)
JOB2_2=$(sbatch --parsable --array=10001-20000 --dependency=afterok:$JOB1_2 slurm_step2_array.sh)

# ... (반복)
```

---

## 🔍 Lock 파일 vs Dependency - 실전 비교

| 상황 | Lock 파일 | Dependency | 권장 |
|------|----------|-----------|------|
| **진행 상황 추적** | ✅ 실시간 | ⚠️ squeue | Lock (편리) |
| **재실행** | ✅ Lock 삭제 후 재실행 | ⚠️ Job 재제출 | Lock (편리) |
| **Slurm 부담** | ✅ 적음 | ⚠️ 많음 (대규모) | Lock (대규모) |
| **안정성** | ⚠️ 파일 시스템 의존 | ✅ Slurm 네이티브 | Dependency |
| **간결성** | ⚠️ 복잡 | ✅ 간단 | Dependency |
| **확장성** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Dependency (Array) |

**최종 결론**: **Dependency 방식이 대부분의 경우 우수**

---

## 📝 체크리스트

### 프로젝트 시작 전 확인

- [ ] DOE 규모 확인 (< 500 or > 500)
- [ ] Slurm 파티션 확인 (시간 제한, 노드 수)
- [ ] Array Job 제한 확인 (`scontrol show config | grep MaxArraySize`)
- [ ] 디스크 용량 확인 (Lock 파일용)
- [ ] 네트워크 파일 시스템 성능 확인

### 실행 중 모니터링

```bash
# Job 상태 확인
squeue -u $USER

# 특정 Job 상세 정보
scontrol show job JOB_ID

# Array Job 진행 상황
sacct -j JOB_ID --format=JobID,State,ExitCode

# Lock 파일 확인 (Lock 방식)
ls .locks/ | wc -l
```

---

## 📞 문의

**작성자**: koo.park
**이메일**: koo.park@samsung.com
**부서**: CAE, HE

---

**버전**: 1.0
**작성일**: 2026-01-23
