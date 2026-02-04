# 테스트 시나리오 모음

각 테스트 디렉토리는 독립적으로 실행 가능하며, 다양한 낙하 조건을 시험합니다.

---

## Test_001_Full26_1Step

**목적**: 26방향 1회 낙하 (기본 검증)

**조건**:
- 각도 소스: cuboid_geometry (Face 6 + Edge 12 + Corner 8)
- 총 케이스: 26개
- 연속 낙하: 1회
- 각도 믹싱: same_angle

**실행 시간**: ~12시간 (노드 2개, 동시 8개)

**실행**:
```bash
cd Test_001_Full26_1Step
bash run.sh
```

**용도**:
- 전방향 취약점 탐색
- 완전 보증 테스트

---

## Test_002_Full26_3Step

**목적**: 26방향 3회 연속 낙하 (손상 누적)

**조건**:
- 각도 소스: cuboid_geometry (26방향)
- 총 케이스: 26개
- 연속 낙하: 3회
- 각도 믹싱: same_angle (동일 각도 반복)

**실행 시간**: ~36시간 (노드 2개, 동시 8개, 3 Steps)

**실행**:
```bash
cd Test_002_Full26_3Step
bash run.sh
```

**용도**:
- 반복 낙하 내구성
- 누적 손상 평가

**특징**:
- Step 1: 첫 낙하 (DROP_FIRST)
- Step 2: 변형 상태에서 2차 낙하 (DYNAIN_TO_INITIAL + DROP_CUMULATIVE)
- Step 3: 변형 상태에서 3차 낙하

---

## Test_003_6Faces_Cyclic

**목적**: 6면 3회 연속 낙하 (Cyclic 각도)

**조건**:
- 각도 소스: cuboid_geometry (Face만)
- 총 케이스: 6개
- 연속 낙하: 3회
- 각도 믹싱: cyclic (순환)

**실행 시간**: ~9시간 (노드 1개, 동시 6개, 3 Steps)

**실행**:
```bash
cd Test_003_6Faces_Cyclic
bash run.sh
```

**용도**:
- 다양한 방향 순차 낙하
- 빠른 연속 낙하 검증

**Cyclic 예시** (6면):
```
runid_00001 (Top 시작):
  Step 1: Top    (Roll=0°)
  Step 2: Bottom (Roll=180°)
  Step 3: Front  (Roll=90°)

runid_00002 (Bottom 시작):
  Step 1: Bottom (Roll=180°)
  Step 2: Front  (Roll=90°)
  Step 3: Back   (Roll=-90°)
```

---

## Test_004_Pitching_Sweep

**목적**: Pitch 각도 스윕 (-40° ~ +40°)

**조건**:
- 각도 소스: pitching_sweep
- Pitch 범위: -40° ~ +40° (1° 간격)
- Roll: 0° (고정)
- Yaw: 0° (고정)
- 총 케이스: 81개

**실행 시간**: ~18시간 (노드 3개, 동시 15개)

**실행**:
```bash
cd Test_004_Pitching_Sweep
bash run.sh
```

**용도**:
- 전후 낙하 각도 민감도
- 디스플레이 각도별 충격

**각도 분포**:
```
Pitch = -40°: 뒤로 기울임
Pitch = 0°:   수평
Pitch = +40°: 앞으로 기울임
```

---

## Test_005_Fibonacci_100

**목적**: 100방향 균일분포 (Fibonacci Lattice)

**조건**:
- 각도 소스: fibonacci_lattice
- 방향 수: 100개
- 연속 낙하: 1회

**실행 시간**: ~12시간 (노드 4개, 동시 32개)

**실행**:
```bash
cd Test_005_Fibonacci_100
bash run.sh
```

**용도**:
- 전방향 균일 샘플링
- 통계적 낙하 평가
- 극한 케이스 탐색

**알고리즘**: Fibonacci Spiral
- 구형 표면에 거의 완벽하게 균일 분포
- 격자 패턴(Grid)보다 극점 집중 없음
- 방향 개수를 자유롭게 조정 가능

---

## 리소스 요구사항 비교

| 테스트 | 케이스 | Steps | 동시 실행 | Rounds | 예상 시간 | 디스크 |
|--------|--------|-------|----------|--------|----------|--------|
| Test_001 | 26 | 1 | 8 | 4 | 12h | ~130GB |
| Test_002 | 26 | 3 | 8 | 4×3 | 36h | ~390GB |
| Test_003 | 6 | 3 | 6 | 1×3 | 9h | ~90GB |
| Test_004 | 81 | 1 | 15 | 6 | 18h | ~405GB |
| Test_005 | 100 | 1 | 32 | 4 | 12h | ~500GB |

**디스크 계산**: 케이스당 5GB (d3plot 포함) × 케이스 수 × Steps

---

## 실행 전 체크리스트

### 1. 베이스 모델 준비
```bash
# 템플릿 파일 위치 확인
ls -lh /data/templates/MinimumModel.k
```

파일이 없으면:
```bash
cp your_base_model.k /data/templates/MinimumModel.k
```

### 2. 디스크 공간 확인
```bash
df -h /data
```

필요 공간: 테스트별 디스크 요구사항 참조

### 3. Apptainer 이미지 확인
```bash
ls -lh /opt/apptainers/KooSimulation313.sif
ls -lh /opt/apptainers/LSDynaBasic_ifort2022_impilatest_mpp_s.sif
```

### 4. Slurm 노드 상태 확인
```bash
sinfo
```

Available 노드가 충분한지 확인.

---

## 실행 패턴

### 순차 실행 (권장)
작은 테스트부터 검증:
```bash
# 1. 소규모 테스트 (6 케이스)
cd Test_003_6Faces_Cyclic
bash run.sh

# 완료 확인 후
# 2. 중규모 테스트 (26 케이스)
cd ../Test_001_Full26_1Step
bash run.sh

# 완료 확인 후
# 3. 대규모 테스트 (100 케이스)
cd ../Test_005_Fibonacci_100
bash run.sh
```

### 병렬 실행 (고급)
서로 다른 테스트를 동시에:
```bash
# 터미널 1
cd Test_001_Full26_1Step
bash run.sh

# 터미널 2
cd Test_004_Pitching_Sweep
bash run.sh
```

리소스 충돌 주의 (총 동시 실행 수가 전체 노드를 초과하지 않도록).

---

## 결과 확인

### 진행 상황
```bash
# Slurm 큐
squeue -u $USER

# 완료 케이스 수
find /data/Test_001_Full26_1Step -name "*.lock" | wc -l
```

### 로그 확인
```bash
# Slurm 출력
ls -lt Test_001_Full26_1Step/*.out | head

# LS-DYNA 로그
cat /data/Test_001_Full26_1Step/runid_00001/Step001/messag
```

### 결과 수집
```bash
cd Test_001_Full26_1Step
/opt/pyKooCAE/KooChainRun collect runner_config.json results/
```

---

## 문제 해결

### 작업이 Pending 상태
```bash
squeue -u $USER
```

`NODELIST(REASON)` 컬럼 확인:
- `Resources`: 리소스 부족 (대기 중)
- `Priority`: 우선순위 낮음 (대기 중)
- `Dependency`: 이전 Job 대기 중

### 일부 케이스 실패
```bash
# 실패한 케이스 찾기
find /data/Test_001 -type d -name "Step001" ! -exec test -e {}/Step001.lock \; -print
```

해당 케이스 로그 확인:
```bash
cat /data/Test_001/runid_00005/Step001/slurm-*.out
cat /data/Test_001/runid_00005/Step001/messag
```

### 디스크 부족
```bash
# 공간 확인
du -sh /data/Test_*

# 압축 (완료된 테스트)
cd /data/Test_001_Full26_1Step
find . -name "d3plot*" -exec gzip {} \;
```

---

**작성**: CAE팀
**최종 수정**: 2026-01-23
