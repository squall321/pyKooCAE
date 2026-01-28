# 자원 계획 가이드

**작성일**: 2026-01-23
**목적**: HPC 클러스터 자원 계획 및 최적 설정

---

## 시스템 사양

**클러스터 구성**:
- 총 346개 노드
- 노드당 128 코어
- 46개 노드: 공유 (여러 사용자)
- 300개 노드: 전용 가능

---

## 자원 계산 방법

### 기본 공식

```
동시 실행 Job 수 = nodes × jobs_per_node
노드당 CPU 사용량 = jobs_per_node × ncpu_per_job
노드당 CPU 활용률 = (jobs_per_node × ncpu_per_job) / 128 × 100%
```

### 예시 1: 보수적 (50% 활용)

```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 10 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
```

**계산**:
- 동시 실행: 10 × 4 = **40개 Job**
- 노드당 CPU: 4 × 16 = 64 CPU
- 활용률: 64 / 128 = **50%**

**적합한 경우**:
- 공유 노드 사용
- 다른 사용자와 자원 공유
- 안정성 우선

### 예시 2: 최적 (100% 활용)

```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 20 \
    --jobs-per-node 8 \
    --ncpu-per-job 16
```

**계산**:
- 동시 실행: 20 × 8 = **160개 Job**
- 노드당 CPU: 8 × 16 = 128 CPU
- 활용률: 128 / 128 = **100%**

**적합한 경우**:
- 전용 노드 사용
- 최대 성능 필요
- 단일 사용자

### 예시 3: 대규모 (300개 노드)

```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 300 \
    --jobs-per-node 8 \
    --ncpu-per-job 16
```

**계산**:
- 동시 실행: 300 × 8 = **2,400개 Job**
- 10,000 runid × 3 Steps = 30,000 Jobs
- 예상 Rounds: 30,000 / 2,400 = **13 rounds**
- Job당 4시간 소요 시 → 총 52시간

---

## 시나리오별 권장 설정

### 시나리오 1: 소규모 테스트 (100 Jobs)

**목적**: 빠른 검증, 설정 테스트

```bash
--nodes 5 \
--jobs-per-node 4 \
--ncpu-per-job 16
```

**결과**:
- 동시 실행: 20개
- 100 Jobs ÷ 20 = 5 rounds
- Job당 30분 → 총 2.5시간

---

### 시나리오 2: 중규모 (1,000 Jobs)

**목적**: 일반적인 DOE 분석

```bash
--nodes 10 \
--jobs-per-node 8 \
--ncpu-per-job 16
```

**결과**:
- 동시 실행: 80개
- 1,000 Jobs ÷ 80 = 13 rounds
- Job당 2시간 → 총 26시간

---

### 시나리오 3: 대규모 (10,000 Jobs)

**목적**: Fibonacci 1000 × DOE 5 × 3 Steps

```bash
--nodes 50 \
--jobs-per-node 8 \
--ncpu-per-job 16
```

**결과**:
- 동시 실행: 400개
- 15,000 Jobs ÷ 400 = 38 rounds
- Job당 4시간 → 총 152시간 (6.3일)

---

### 시나리오 4: 극대규모 (100,000 Jobs)

**목적**: Fibonacci 10,000 × DOE 5 × 3 Steps

```bash
--nodes 300 \
--jobs-per-node 8 \
--ncpu-per-job 16
```

**결과**:
- 동시 실행: 2,400개
- 150,000 Jobs ÷ 2,400 = 63 rounds
- Job당 4시간 → 총 252시간 (10.5일)

---

## CPU당 작업 조정

### ncpu-per-job 선택 가이드

| ncpu-per-job | 노드당 최대 Jobs | 용도 |
|--------------|-----------------|------|
| 8 | 16 | 소형 모델, 빠른 해석 |
| 16 | 8 | 일반 모델 (권장) |
| 32 | 4 | 대형 모델 |
| 64 | 2 | 초대형 모델 |
| 128 | 1 | 극대형 모델 |

**LS-DYNA 성능 고려**:
- 8-16 CPU: 대부분의 낙하 시뮬레이션에 최적
- 32 CPU 이상: 큰 모델만 효율적
- 병렬 효율: 16 CPU 이상에서 감소

---

## 공유 vs 전용 노드 전략

### 공유 노드 (46개)

**권장 설정**:
```bash
--nodes 10 \
--jobs-per-node 4 \
--ncpu-per-job 16
```

**이유**:
- 50% 활용률로 다른 사용자 배려
- 안정적인 성능 보장
- 우선순위 문제 최소화

### 전용 노드 (300개)

**권장 설정**:
```bash
--nodes 100 \
--jobs-per-node 8 \
--ncpu-per-job 16
```

**이유**:
- 100% 활용률로 최대 성능
- 800개 동시 실행
- 빠른 완료 시간

---

## 실시간 모니터링

### Slurm 명령어

```bash
# 현재 실행 중인 작업 확인
squeue -u $USER

# Array Job 상세 정보
squeue -j <JOBID> --array

# 완료된 작업 통계
sacct -j <JOBID> --format=JobID,State,ExitCode,Elapsed

# 노드 사용률 확인
sinfo -N -l
```

### 진행 상황 확인

```bash
# 전체 완료 개수
find RUNDIR -name "Step*.lock" | wc -l

# Step별 완료 개수
find RUNDIR -name "Step001.lock" | wc -l
find RUNDIR -name "Step002.lock" | wc -l

# 완료율 계산
python -c "
import sys
from pathlib import Path
total = len(list(Path('RUNDIR').glob('runid_*')))
completed = len(list(Path('RUNDIR').glob('runid_*/Step001/.lock')))
print(f'Step 1: {completed}/{total} ({completed/total*100:.1f}%)')
"
```

---

## 예상 시간 계산

### 공식

```
총 시간 = (총 Jobs ÷ 동시 실행 수) × Job당 시간
```

### 예시

**시나리오**:
- Fibonacci 1000개 × DOE 5 × 3 Steps = 15,000 Jobs
- Job당 평균 시간: 2시간

**설정 1**: 40개 동시 실행
```
총 시간 = (15,000 ÷ 40) × 2h = 375 × 2h = 750시간 = 31.25일
```

**설정 2**: 160개 동시 실행
```
총 시간 = (15,000 ÷ 160) × 2h = 94 × 2h = 188시간 = 7.8일
```

**설정 3**: 800개 동시 실행
```
총 시간 = (15,000 ÷ 800) × 2h = 19 × 2h = 38시간 = 1.6일
```

---

## 비용 최적화

### HPC 비용 모델 (예시)

- CPU-hour 당 비용: $0.10
- 노드당 128 CPU
- 시간당 노드 비용: $12.80

### 예시 계산

**시나리오**: 15,000 Jobs, Job당 2시간

**설정 1** (40개 동시, 5 nodes):
```
총 시간: 750시간
노드 시간: 750h × 5 nodes = 3,750 node-hours
비용: 3,750 × $12.80 = $48,000
```

**설정 2** (160개 동시, 20 nodes):
```
총 시간: 188시간
노드 시간: 188h × 20 nodes = 3,760 node-hours
비용: 3,760 × $12.80 = $48,128
```

**결론**: 노드 수를 늘려도 **총 비용은 거의 동일**, 하지만 **완료 시간은 4배 빠름**

---

## 권장 설정 템플릿

### 빠른 테스트

```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 2 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
# 동시: 8개
```

### 일반 작업

```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 10 \
    --jobs-per-node 8 \
    --ncpu-per-job 16
# 동시: 80개
```

### 대규모 작업

```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 50 \
    --jobs-per-node 8 \
    --ncpu-per-job 16
# 동시: 400개
```

### 최대 성능

```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 300 \
    --jobs-per-node 8 \
    --ncpu-per-job 16
# 동시: 2,400개
```

---

## 체크리스트

실행 전 확인:

- [ ] 총 Job 수 확인 (runid 수 × Steps)
- [ ] Job당 예상 시간 추정
- [ ] 필요한 노드 수 계산
- [ ] 공유/전용 노드 확인
- [ ] 동시 실행 제한 설정
- [ ] 예상 완료 시간 계산
- [ ] 디스크 공간 확인 (Job당 ~1GB)
- [ ] Slurm 파티션 확인

---

## 문제 해결

### 문제 1: Job이 시작되지 않음

**원인**: 자원 부족
**해결**:
```bash
squeue -u $USER  # 대기 이유 확인
sinfo            # 노드 가용성 확인
```

### 문제 2: 일부 Job만 실행됨

**원인**: 동시 실행 제한
**확인**: Slurm 스크립트의 `--array=1-5000%40` 확인
**해결**: `%40`을 늘려서 재제출

### 문제 3: 노드 활용률 낮음

**원인**: `jobs-per-node` 또는 `ncpu-per-job` 설정 부족
**해결**:
```bash
# 현재: 4 jobs/node × 16 CPU = 64 CPU (50%)
# 변경: 8 jobs/node × 16 CPU = 128 CPU (100%)
--jobs-per-node 8
```

---

**작성자**: koo.park
**버전**: 1.0
**최종 수정**: 2026-01-23
