# 노드 점유율 모니터링 사용 예시

**작성일**: 2026-01-23
**버전**: 1.0

---

## 🎯 개요

NodeOccupancyMonitor는 Slurm 클러스터의 노드 점유율을 실시간으로 모니터링하고 자원 사용량을 분석하는 도구입니다.

---

## 🚀 기본 사용법

### 1. 실시간 모니터링

```bash
# 기본 모니터링 (60초 간격)
python3 Runner/NodeOccupancyMonitor.py monitor

# 간격 설정 (30초)
python3 Runner/NodeOccupancyMonitor.py monitor --interval=30

# 프로젝트 필터링
python3 Runner/NodeOccupancyMonitor.py monitor --project=DirectInput_Test

# 최대 10회 체크
python3 Runner/NodeOccupancyMonitor.py monitor --max-iterations=10
```

**출력 예시**:

```
========================================
노드 점유율 실시간 모니터링 시작
체크 간격: 60초
========================================

====================================================================================================
현재 시각: 2026-01-23 14:30:00
총 Job 수: 3 | 총 노드: 10 | 총 CPU: 320
상태: {'RUNNING': 2, 'PENDING': 1}
====================================================================================================
Job ID       이름                             상태        시간          노드    CPU    메모리      파티션
----------------------------------------------------------------------------------------------------
12345        Test_CustomMesh_S001            RUNNING     00:45:30     2      64     64G        normal
12346        Test_CustomMesh_S002            RUNNING     00:15:20     4      128    128G       normal
12347        Test_CustomMesh_S003            PENDING     00:00:00     4      128    128G       normal
====================================================================================================

다음 체크: 60초 후... (Ctrl+C로 중단)
```

---

### 2. 히스토리 저장

```bash
# 모니터링 + 히스토리 저장
python3 Runner/NodeOccupancyMonitor.py monitor \
    --interval=60 \
    --save=monitoring_history.json
```

**히스토리 파일 형식** (`monitoring_history.json`):

```json
[
  {
    "timestamp": "2026-01-23T14:30:00",
    "jobs": [
      {
        "job_id": "12345",
        "name": "Test_CustomMesh_S001",
        "state": "RUNNING",
        "nodes": 2,
        "cpus": 64,
        "memory": "64G",
        "partition": "normal"
      }
    ]
  },
  {
    "timestamp": "2026-01-23T14:31:00",
    "jobs": [...]
  }
]
```

---

### 3. 시각화 (matplotlib 필요)

```bash
# 모니터링 + 플롯 생성
python3 Runner/NodeOccupancyMonitor.py monitor \
    --interval=60 \
    --max-iterations=20 \
    --plot=node_occupancy.png
```

**생성되는 플롯**:
- 상단: 시간에 따른 노드 수 변화
- 하단: 시간에 따른 CPU 수 변화

**matplotlib 설치**:

```bash
pip install matplotlib
```

---

### 4. 자원 사용량 분석

```bash
# Job 메타데이터 분석
python3 Runner/NodeOccupancyMonitor.py analyze \
    /data/DirectInput_Test/Test_CustomMesh_20260123_140000/metadata.json
```

**출력 예시**:

```
========================================
Step별 자원 사용량 요약
========================================

Step   노드    CPU/노드    총 CPU     실행 시간     CPU-시간
------------------------------------------------------------
1      2      32         64         02:00:00     128.0
2      4      32         128        04:00:00     512.0
3      4      32         128        06:00:00     768.0
------------------------------------------------------------
총합                                               1408.0
============================================================

총 CPU-시간: 1408.0 CPU-hours
병렬 효율성: 73.3% (최대 CPU 대비)
```

**설명**:
- **총 CPU-시간**: 모든 Step의 CPU-시간 합계
- **병렬 효율성**: 최대 CPU 수 기준 효율성 (낮을수록 병렬화 여지 있음)

---

## 📊 실전 사용 시나리오

### 시나리오 1: 장시간 실행 모니터링

**목표**: 12시간 실행 예상, 1시간마다 체크

```bash
python3 Runner/NodeOccupancyMonitor.py monitor \
    --interval=3600 \
    --project=LargeScale_Project \
    --save=monitoring_12h.json \
    --plot=monitoring_12h.png
```

**활용**:
- 히스토리 파일로 전체 실행 기록 보존
- 플롯으로 자원 사용 패턴 시각화
- 병목 구간 식별

---

### 시나리오 2: 자원 최적화 분석

**목표**: Step별 자원 사용량 분석하여 최적화

```bash
# 1. 현재 설정 분석
python3 Runner/NodeOccupancyMonitor.py analyze current_config.json

# 출력:
# Step 1: 64 CPU × 2h = 128 CPU-hours
# Step 2: 128 CPU × 4h = 512 CPU-hours
# Step 3: 128 CPU × 6h = 768 CPU-hours
# 병렬 효율성: 73.3%

# 2. 개선 사항 도출
# - Step 2-3이 CPU를 많이 사용 → 노드 수 증가 고려
# - Step 1은 빨리 완료됨 → 노드 수 감소 가능
```

**개선된 설정**:

```json
{
  "step_resources": {
    "1": {"nnodes": 1, "ncpus_per_node": 32},  // 64 → 32 CPU
    "2": {"nnodes": 6, "ncpus_per_node": 32},  // 128 → 192 CPU
    "3": {"nnodes": 6, "ncpus_per_node": 32}   // 128 → 192 CPU
  }
}
```

**결과**:
- Step 1: 32 CPU × 2h = 64 CPU-hours (절반)
- Step 2: 192 CPU × 2.7h = 518 CPU-hours (시간 단축)
- Step 3: 192 CPU × 4h = 768 CPU-hours (시간 단축)
- 총 소요 시간: 12h → 8.7h (27% 단축)

---

### 시나리오 3: 클러스터 전체 상황 파악

**목표**: 현재 실행 중인 모든 Job 확인

```bash
# 프로젝트 필터 없이 전체 조회
python3 Runner/NodeOccupancyMonitor.py monitor --max-iterations=1
```

**출력**:

```
총 Job 수: 15 | 총 노드: 45 | 총 CPU: 1440
상태: {'RUNNING': 8, 'PENDING': 5, 'COMPLETING': 2}
```

**활용**:
- 클러스터 전체 부하 확인
- 자원 경쟁 상황 파악
- Job 제출 타이밍 조정

---

## 🔧 고급 활용

### 1. 자동화 스크립트

**자동 모니터링 + 알림** (`auto_monitor.sh`):

```bash
#!/bin/bash

# 모니터링 시작
python3 Runner/NodeOccupancyMonitor.py monitor \
    --interval=300 \
    --project=MyProject \
    --save=monitor_$(date +%Y%m%d_%H%M%S).json

# 완료 후 이메일 알림
if [ $? -eq 0 ]; then
    echo "모니터링 완료" | mail -s "Job 완료" user@example.com
fi
```

**사용**:

```bash
nohup ./auto_monitor.sh > monitor.log 2>&1 &
```

---

### 2. 병렬 효율성 최적화

**목표**: 병렬 효율성 80% 이상 달성

**분석**:

```bash
python3 Runner/NodeOccupancyMonitor.py analyze config.json
```

**출력**:

```
병렬 효율성: 65.2%  ← 개선 필요
```

**개선 전략**:

1. **Step 간 균형 맞추기**:
   - CPU 수가 비슷하도록 조정
   - 실행 시간이 비슷하도록 조정

2. **노드 수 최적화**:
   - 너무 적으면: 병렬 효율성 낮음
   - 너무 많으면: 통신 오버헤드

3. **Walltime 정확하게 설정**:
   - 과대 설정은 자원 낭비
   - 과소 설정은 Job 실패

---

### 3. 비용 분석

**목표**: CPU-시간 기준 비용 계산

**가정**:
- 비용: $0.10 / CPU-hour

```bash
# 분석
python3 Runner/NodeOccupancyMonitor.py analyze config.json

# 출력:
# 총 CPU-시간: 1408.0 CPU-hours

# 비용 계산
echo "1408.0 * 0.10" | bc
# → $140.80
```

---

## 📈 모니터링 데이터 활용

### 1. 히스토리 분석 (Python)

```python
import json
import matplotlib.pyplot as plt
from datetime import datetime

# 히스토리 로드
with open('monitoring_history.json', 'r') as f:
    history = json.load(f)

# 노드 수 추출
timestamps = [datetime.fromisoformat(h['timestamp']) for h in history]
node_counts = [sum(j['nodes'] for j in h['jobs']) for h in history]

# 플롯
plt.plot(timestamps, node_counts)
plt.xlabel('시간')
plt.ylabel('노드 수')
plt.title('노드 점유율 변화')
plt.savefig('node_occupancy_custom.png')
```

---

### 2. 통계 분석 (pandas)

```python
import pandas as pd
import json

# 히스토리 로드
with open('monitoring_history.json', 'r') as f:
    history = json.load(f)

# DataFrame 생성
data = []
for h in history:
    for job in h['jobs']:
        data.append({
            'timestamp': h['timestamp'],
            'job_id': job['job_id'],
            'nodes': job['nodes'],
            'cpus': job['cpus']
        })

df = pd.DataFrame(data)

# 통계
print(df.groupby('job_id').agg({
    'nodes': 'mean',
    'cpus': 'mean'
}))
```

---

## 🚨 주의사항

### 1. squeue 권한

**증상**: `squeue` 명령 실패

**해결**:
```bash
# 권한 확인
which squeue
# → /usr/bin/squeue

# 실행 권한 확인
ls -l /usr/bin/squeue
```

---

### 2. 모니터링 간격

**권장**:
- **짧은 실행** (< 1시간): 10-30초
- **중간 실행** (1-6시간): 60초
- **긴 실행** (> 6시간): 300-600초

**이유**:
- 너무 짧으면 squeue 부하 증가
- 너무 길면 상태 변화 놓칠 수 있음

---

### 3. 히스토리 파일 크기

**예상**:
- 1회 체크: ~1-2 KB
- 1시간 (60회): ~60-120 KB
- 12시간 (720회): ~720 KB - 1.4 MB

**관리**:
```bash
# 압축
gzip monitoring_history.json

# 삭제 (오래된 파일)
find . -name "monitor_*.json" -mtime +30 -delete
```

---

## 📞 문의

**작성자**: koo.park
**이메일**: koo.park@samsung.com
**부서**: CAE, HE

---

**버전**: 1.0
**작성일**: 2026-01-23
**대상**: 노드 점유율 모니터링 사용자
