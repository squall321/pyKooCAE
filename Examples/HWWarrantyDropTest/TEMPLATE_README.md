# Job Template 사용 가이드 - HW Warranty Drop Test

**작성일**: 2026-01-23
**목적**: 대시보드를 통한 KooChainRun 작업 제출

---

## 개요

이 디렉토리는 HPC 대시보드에서 HW Warranty Drop Test를 실행하기 위한 Job Template을 포함합니다.

### 포함된 템플릿

1. **hw_warranty_droptest.yaml** - 전체 Drop Test 워크플로우
   - 다중 방향 낙하 시뮬레이션 (26방향 또는 사용자 정의)
   - 다중 스텝 연속 낙하 (손상 누적)
   - Slurm 병렬 실행
   - KooChainRun 자동화

---

## 사용 방법

### 1. **템플릿 배포**

템플릿을 대시보드 템플릿 디렉토리에 복사:

```bash
# 템플릿 매니저 디렉토리로 복사
cp hw_warranty_droptest.yaml /shared/templates/simulation/

# 또는 프로젝트 소스에 복사
cp hw_warranty_droptest.yaml \
   /path/to/app/job_template_manager/src/resources/templates/simulation/
```

### 2. **템플릿 스캔 및 등록**

대시보드 API를 통해 템플릿 스캔:

```bash
curl -X POST http://localhost:5010/api/jobs/templates/scan
```

### 3. **템플릿 확인**

등록된 템플릿 확인:

```bash
# 전체 템플릿 목록
curl http://localhost:5010/api/v2/templates

# HW Drop Test 템플릿 조회
curl http://localhost:5010/api/v2/templates/hw-warranty-droptest
```

---

## 대시보드에서 작업 제출

### Step 1: 템플릿 선택

1. 대시보드 웹 UI 접속
2. **Jobs** → **New Job** 메뉴 선택
3. 카테고리: **Simulation**
4. 템플릿 선택: **HW Warranty Drop Test (KooChainRun)**

### Step 2: 입력 파일 업로드

필수 파일 2개를 업로드:

#### **Scenario JSON File** (`scenario_json`)
- KooChainRun 시나리오 설정 파일
- 예시: [Test_001_Full26_1Step/scenario.json](Tests/Test_001_Full26_1Step/scenario.json)

**주의**: 템플릿 경로는 자동으로 설정되므로 `scenario.json`에서 `template` 필드는 무시됩니다.

#### **Base Model K File** (`template_k`)
- LS-DYNA 베이스 모델 파일 (.k)
- 예시: `MinimumModel.k`

### Step 3: 리소스 설정 (선택)

환경변수로 리소스 구성 조정 가능:

```bash
KOOCR_NODES=2              # 사용할 노드 수 (기본값: 2)
KOOCR_JOBS_PER_NODE=4      # 노드당 동시 작업 수 (기본값: 4)
KOOCR_NCPU_PER_JOB=16      # 작업당 CPU 코어 수 (기본값: 16)
```

**기본 설정**:
- 노드: 2개
- 노드당 Job: 4개
- Job당 CPU: 16코어
- **동시 실행**: 8개 케이스
- **총 CPU 사용**: 128 코어 (2 nodes × 4 jobs × 16 CPUs)

### Step 4: 작업 제출 및 모니터링

1. **Submit Job** 버튼 클릭
2. 작업 ID 확인
3. **Job Status** 페이지에서 진행 상황 확인

---

## scenario.json 예시

### **예시 1: 26방향 1회 낙하**

```json
{
  "project_name": "Test_26Dir_1Step",
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "apptainer_sif": "/opt/apptainers/KooSimulation313.sif",
    "apptainer_bind": "/data:/data,/shared:/shared",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_ifort2022_impilatest_mpp_s.sif",
    "lsdyna_apptainer_bind": "/data:/data,/shared:/shared"
  },
  "scenarios": [
    {
      "scenario_name": "Full_26_Directions_Single_Drop",
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
        "num_steps": 1,
        "mode_sequence": ["DROP"],
        "base_angle_index": 0,
        "angle_mixing": {
          "strategy": "same_angle"
        }
      }
    }
  ]
}
```

**실행 결과**:
- **26개 케이스** (Face 6 + Edge 12 + Corner 8)
- **1회 낙하**만 시뮬레이션
- **동일 각도** 전략 (각 케이스는 고정된 방향)

---

### **예시 2: 6방향 3회 연속 낙하**

```json
{
  "project_name": "Test_6Dir_3Step",
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "apptainer_sif": "/opt/apptainers/KooSimulation313.sif",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_ifort2022_impilatest_mpp_s.sif"
  },
  "scenarios": [
    {
      "scenario_name": "6_Faces_3_Consecutive_Drops",
      "template": "/data/templates/model.k",
      "angle_source": {
        "source_type": "cuboid_geometry",
        "cuboid_geometry": {
          "include_faces": true,
          "include_edges": false,
          "include_corners": false
        }
      },
      "cumulative": {
        "num_steps": 3,
        "mode_sequence": ["DROP", "DROP", "DROP"],
        "base_angle_index": 0,
        "angle_mixing": {
          "strategy": "cyclic"
        }
      }
    }
  ]
}
```

**실행 결과**:
- **6개 케이스** (Face만)
- **3회 연속 낙하** (누적 손상)
- **Cyclic 전략**: Step 1 → Step 2 → Step 3 (순환 각도)

---

### **예시 3: 100방향 균일 분포 1회 낙하**

```json
{
  "project_name": "Test_100Dir_Uniform",
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "apptainer_sif": "/opt/apptainers/KooSimulation313.sif",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_ifort2022_impilatest_mpp_s.sif"
  },
  "scenarios": [
    {
      "scenario_name": "100_Uniform_Directions",
      "template": "/data/templates/model.k",
      "angle_source": {
        "source_type": "fibonacci_lattice",
        "fibonacci_lattice": {
          "num_directions": 100
        }
      },
      "cumulative": {
        "num_steps": 1,
        "mode_sequence": ["DROP"],
        "base_angle_index": 0,
        "angle_mixing": {
          "strategy": "same_angle"
        }
      }
    }
  ]
}
```

**실행 결과**:
- **100개 케이스** (Fibonacci lattice 균일 분포)
- **1회 낙하**
- 구형 표면에 균등 분포된 방향

---

## 실행 후 결과 확인

### 작업 디렉토리 구조

```
/data/HWWarrantyDropTest_<JOB_ID>/
├── scenario.json                      # 사용된 시나리오 설정
├── runner_config.json                 # 생성된 실행 설정
├── templates/
│   └── base_model.k                   # 업로드된 베이스 모델
│
├── runid_00001/                       # 케이스 1
│   ├── metadata.json
│   └── Step001/
│       ├── metadata.json
│       ├── MinimumModel_rotated.k
│       ├── d3plot01, d3plot02, ...
│       ├── dynain
│       └── Step001.lock
│
├── runid_00002/                       # 케이스 2
│   └── Step001/
│
... (N개 케이스)
│
├── results/                           # 수집된 결과
│   ├── runid_00001/
│   ├── runid_00002/
│   └── ...
│
└── job_summary.txt                    # 작업 요약
```

### 결과 다운로드

대시보드 또는 명령줄에서 결과 다운로드:

```bash
# 작업 디렉토리 찾기
JOB_ID=<your_slurm_job_id>
WORK_DIR="/data/HWWarrantyDropTest_${JOB_ID}"

# 전체 결과 압축
cd "$WORK_DIR"
tar -czf results_${JOB_ID}.tar.gz results/

# 특정 케이스만
tar -czf case_001.tar.gz runid_00001/

# 요약 확인
cat job_summary.txt
```

---

## 리소스 계산 가이드

### 시나리오별 권장 설정

| 케이스 수 | 스텝 수 | 노드 | 노드당 Job | Job당 CPU | 동시 실행 | 예상 시간* |
|----------|---------|------|-----------|----------|----------|-----------|
| 26       | 1       | 2    | 4         | 16       | 8        | ~10시간   |
| 26       | 3       | 2    | 4         | 16       | 8        | ~30시간   |
| 100      | 1       | 4    | 8         | 16       | 32       | ~10시간   |
| 100      | 3       | 4    | 8         | 16       | 32       | ~30시간   |
| 1000     | 1       | 10   | 10        | 16       | 100      | ~30시간   |

*LS-DYNA 케이스당 2-3시간 가정

### 리소스 계산 공식

```
동시 실행 = 노드 수 × 노드당 Job 수
총 CPU 사용 = 동시 실행 × Job당 CPU
총 Rounds = ⌈케이스 수 / 동시 실행⌉
예상 시간 = 총 Rounds × (케이스당 시간) × 스텝 수
```

**예시**: 26 케이스, 3 스텝, 8 동시 실행
```
총 Rounds = ⌈26 / 8⌉ = 4 rounds
예상 시간 = 4 × 3시간 × 3 스텝 = ~36시간
```

---

## 문제 해결

### 문제 1: 템플릿이 대시보드에 표시되지 않음

**원인**: 템플릿 스캔이 안 됨 또는 YAML 문법 오류

**해결**:
```bash
# YAML 문법 확인
python3 -c "import yaml; yaml.safe_load(open('hw_warranty_droptest.yaml'))"

# 템플릿 재스캔
curl -X POST http://localhost:5010/api/jobs/templates/scan

# 템플릿 목록 확인
curl http://localhost:5010/api/v2/templates | grep hw-warranty
```

---

### 문제 2: 작업 제출 후 즉시 실패

**원인**: scenario.json 파싱 오류 또는 입력 파일 경로 문제

**해결**:
```bash
# Slurm 로그 확인
WORK_DIR="/data/HWWarrantyDropTest_<JOB_ID>"
cat $WORK_DIR/slurm-*.out

# scenario.json 검증
python3 -c "import json; json.load(open('scenario.json'))"
```

---

### 문제 3: 일부 케이스만 실패

**원인**: 개별 케이스 실행 중 오류

**해결**:
```bash
# 실패한 케이스 찾기
find /data/HWWarrantyDropTest_<JOB_ID> -type d -name "runid_*" \
  ! -path "*/Step001/*.lock" -print

# 개별 케이스 로그 확인
cat /data/HWWarrantyDropTest_<JOB_ID>/runid_00001/Step001/slurm-*.out
```

---

## 추가 자료

- [KooChainRun 사용 가이드](../../README_KooChainRun.md)
- [Apptainer 통합 가이드](APPTAINER_GUIDE.md)
- [시나리오 작성 가이드](../../docs/SCENARIO_GUIDE.md)
- [Job Template 작성 가이드](TemplateGuide.md)

---

**작성자**: Koo Engineering
**최종 수정**: 2026-01-23
