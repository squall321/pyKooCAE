# Test_001: 전각도 26방향 1회 낙하

**작성일**: 2026-01-23
**목적**: KooChainRun 기본 동작 테스트

---

## 개요

가장 기본적인 테스트 시나리오:
- **26 방향** (Face 6 + Edge 12 + Corner 8)
- **1회 낙하** (Step 1만)
- **동일 각도** (same_angle 전략)

---

## 준비 사항

### 1. **베이스 .k 파일 준비**

템플릿 파일을 공유 스토리지에 배치:

```bash
# 예시 1: /data/templates/ 디렉토리 생성
mkdir -p /data/templates
cp MinimumModel.k /data/templates/

# 예시 2: 프로젝트별 디렉토리
mkdir -p /data/Test_001_Full26_1Step/templates
cp MinimumModel.k /data/Test_001_Full26_1Step/templates/
```

### 2. **scenario.json에 template 경로 설정**

```json
{
  "scenarios": [
    {
      "template": "/data/templates/MinimumModel.k",
      ...
    }
  ]
}
```

**중요**:
- 경로는 **절대 경로** 사용
- 모든 계산노드에서 **접근 가능**한 위치 (/data, /shared 등)

### 3. **Apptainer SIF 파일 경로 설정**

```json
{
  "environment": {
    "apptainer_sif": "/shared/containers/koomesh.sif",
    "lsdyna_apptainer_sif": "/shared/containers/lsdyna.sif"
  }
}
```

또는 Apptainer 없이 직접 실행:

```json
{
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/lsdyna/bin/ls-dyna"
  }
}
```

---

## 실행 방법

### **방법 1: run.sh 스크립트 사용** (추천)

```bash
cd /path/to/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step
bash run.sh
```

**실행 흐름**:
1. scenario.json → runner_config.json 생성
2. 실행 설정 확인
3. 사용자 확인 (y/n)
4. Slurm 작업 제출

### **방법 2: KooChainRun 직접 사용**

```bash
# 1. 설정 준비
KooChainRun prepare scenario.json

# 2. 작업 제출
KooChainRun submit runner_config.json \
    --nodes 2 \
    --jobs-per-node 4 \
    --ncpu-per-job 16

# 3. 진행 상황 확인
KooChainRun status

# 4. 결과 수집
KooChainRun collect runner_config.json results/
```

---

## 실행 리소스

| 항목 | 값 | 설명 |
|------|-----|------|
| **총 케이스** | 26 | Face 6 + Edge 12 + Corner 8 |
| **노드** | 2 | 사용할 노드 수 |
| **노드당 Job** | 4 | 각 노드에서 동시 실행 |
| **Job당 CPU** | 16 | LS-DYNA MPI 프로세스 수 |
| **동시 실행** | 8 | 2 nodes × 4 jobs = 8 |
| **예상 Rounds** | 4 | 26 케이스 ÷ 8 동시 = ~4 rounds |

**총 노드 CPU 사용**: 4 jobs × 16 CPUs = 64 CPUs/node (128코어 중 50%)

---

## 예상 실행 시간

| 단계 | 시간/케이스 | 설명 |
|------|------------|------|
| **KooMeshModifier** | 1-5분 | .k 파일 회전 |
| **LS-DYNA** | 2-3시간 | 낙하 시뮬레이션 |
| **총 시간** | ~8-10시간 | 26 케이스, 8개 동시 실행 |

**계산**:
- Round 1: 8 케이스 동시 (0-3시간)
- Round 2: 8 케이스 동시 (3-6시간)
- Round 3: 8 케이스 동시 (6-9시간)
- Round 4: 2 케이스 동시 (9-10시간)

---

## 생성되는 디렉토리 구조

```
/data/Test_001_Full26_1Step/
├── templates/                           # 베이스 파일 (수동 배치)
│   └── MinimumModel.k
│
├── runid_00001/                         # 케이스 1 (F1_Top)
│   ├── metadata.json
│   └── Step001/
│       ├── metadata.json                # 각도: roll=0, pitch=0, yaw=0
│       ├── input.txt                    # KooMeshModifier 입력
│       ├── MinimumModel_rotated.k       # 회전된 .k 파일
│       ├── d3plot01, d3plot02, ...      # LS-DYNA 결과
│       ├── dynain                       # 변형 상태
│       ├── messag                       # LS-DYNA 로그
│       └── .lock                        # 완료 표시
│
├── runid_00002/                         # 케이스 2 (F2_Bottom)
│   └── Step001/
│       └── metadata.json                # 각도: roll=180, pitch=0, yaw=0
│
├── runid_00003/                         # 케이스 3 (F3_Front)
│   └── Step001/
│       └── metadata.json                # 각도: roll=90, pitch=0, yaw=0
│
... (26개 케이스)
│
├── runid_00026/                         # 케이스 26 (C8_BBR)
│   └── Step001/
│       └── metadata.json                # 각도: roll=-135, pitch=-45, yaw=0
│
└── slurm_script_Step001.sh              # 생성된 Slurm 스크립트
```

---

## 26개 방향 상세

### **Faces (6개)**

| runid | 이름 | Roll | Pitch | Yaw |
|-------|------|------|-------|-----|
| 00001 | F1_Top | 0 | 0 | 0 |
| 00002 | F2_Bottom | 180 | 0 | 0 |
| 00003 | F3_Front | 90 | 0 | 0 |
| 00004 | F4_Back | -90 | 0 | 0 |
| 00005 | F5_Left | 0 | 90 | 0 |
| 00006 | F6_Right | 0 | -90 | 0 |

### **Edges (12개)**

| runid | 이름 | Roll | Pitch | Yaw |
|-------|------|------|-------|-----|
| 00007 | E1_Top_Front | 45 | 0 | 0 |
| 00008 | E2_Top_Back | -45 | 0 | 0 |
| 00009 | E3_Top_Left | 0 | 45 | 0 |
| 00010 | E4_Top_Right | 0 | -45 | 0 |
| 00011 | E5_Bottom_Front | 135 | 0 | 0 |
| 00012 | E6_Bottom_Back | -135 | 0 | 0 |
| 00013 | E7_Bottom_Left | 180 | 45 | 0 |
| 00014 | E8_Bottom_Right | 180 | -45 | 0 |
| 00015 | E9_Front_Left | 90 | 45 | 0 |
| 00016 | E10_Front_Right | 90 | -45 | 0 |
| 00017 | E11_Back_Left | -90 | 45 | 0 |
| 00018 | E12_Back_Right | -90 | -45 | 0 |

### **Corners (8개)**

| runid | 이름 | Roll | Pitch | Yaw |
|-------|------|------|-------|-----|
| 00019 | C1_TFL | 45 | 45 | 0 |
| 00020 | C2_TFR | 45 | -45 | 0 |
| 00021 | C3_TBL | -45 | 45 | 0 |
| 00022 | C4_TBR | -45 | -45 | 0 |
| 00023 | C5_BFL | 135 | 45 | 0 |
| 00024 | C6_BFR | 135 | -45 | 0 |
| 00025 | C7_BBL | -135 | 45 | 0 |
| 00026 | C8_BBR | -135 | -45 | 0 |

---

## 진행 상황 모니터링

### **Slurm 작업 확인**

```bash
# 현재 작업 상태
squeue -u $USER

# 출력 예시:
# JOBID    ARRAY          NAME         ST   TIME
# 123456   1-26%8         Test_001     R    0:15

# 완료된 케이스 수
find /data/Test_001_Full26_1Step -name ".lock" | wc -l
```

### **KooChainRun 상태 확인**

```bash
KooChainRun status runner_config.json
```

### **개별 케이스 로그**

```bash
# Slurm 출력 로그
cat /data/Test_001_Full26_1Step/runid_00001/Step001/slurm-*.out

# LS-DYNA 메시지
cat /data/Test_001_Full26_1Step/runid_00001/Step001/messag
```

---

## 문제 해결

### **문제 1: template 파일을 찾을 수 없음**

```
ERROR: Template file not found: /data/templates/MinimumModel.k
```

**해결**:
```bash
# 파일 존재 확인
ls -l /data/templates/MinimumModel.k

# 파일이 없으면 복사
mkdir -p /data/templates
cp MinimumModel.k /data/templates/
```

### **문제 2: Apptainer SIF를 찾을 수 없음**

```
ERROR: container not found: /path/to/koomesh.sif
```

**해결**:
```bash
# SIF 파일 확인
ls -l /shared/containers/koomesh.sif

# scenario.json에서 경로 수정
```

### **문제 3: 권한 오류**

```
Permission denied: /data/Test_001_Full26_1Step
```

**해결**:
```bash
# 디렉토리 권한 확인
ls -ld /data/Test_001_Full26_1Step

# 권한 수정
chmod 775 /data/Test_001_Full26_1Step
```

---

## 결과 수집

```bash
# 모든 케이스 완료 확인
find /data/Test_001_Full26_1Step -name ".lock" | wc -l
# 출력: 26 (모두 완료)

# 결과 수집
KooChainRun collect runner_config.json results/

# 결과 확인
ls results/
# runid_00001/  runid_00002/  ...  runid_00026/
```

---

## 추가 테스트

이 테스트가 성공하면 다음 테스트로 진행:

- **Test_002**: 3회 연속 낙하 (누적 손상)
- **Test_003**: 다른 각도 믹싱 전략 (cyclic, random)
- **Test_004**: 더 많은 방향 (fibonacci_lattice)

---

**작성자**: Koo Engineering
**최종 수정**: 2026-01-23
