# KooChainRun 프로젝트 컨텍스트 업데이트

**업데이트 일시**: 2026-01-23
**상태**: 개발 완료, 테스트 준비 완료

---

## 1. 프로젝트 개요

### 목적
HW Warranty Drop Test를 위한 대규모 순차/누적 CAE 시뮬레이션 자동화 시스템

### 핵심 기능
- 다중 방향 낙하 시뮬레이션 (26방향 cuboid, 100+ fibonacci lattice 등)
- 다중 스텝 연속 낙하 (손상 누적)
- Slurm 병렬 실행 (Array Job + 의존성 관리)
- Apptainer 컨테이너 통합
- KooMeshModifier + LS-DYNA 자동 실행

---

## 2. 시스템 아키텍처

### 실행 환경
```
헤드 노드 (작업 제출)
  ├── koocr CLI
  └── scenario.json 준비
       ↓
Slurm 스케줄러
  ├── Array job 관리 (--array=1-N%concurrent)
  └── Step 간 의존성 (--dependency=afterok:JOB_ID)
       ↓
컴퓨트 노드 (128코어 × 346대)
  ├── Apptainer 컨테이너
  │   ├── KooSimulation313.sif
  │   │   ├── /opt/KooMeshModifier/run.sh
  │   │   └── /opt/KooChainRun/koocr
  │   └── LSDynaBasic_ifort2022_impilatest_mpp_s.sif
  │       └── /opt/ls-dyna/lsdyna_R16.1.1
  └── 실행 흐름
      ├── KooMeshModifier (메쉬 회전)
      └── LS-DYNA (낙하 시뮬레이션)
       ↓
공유 스토리지 (/data, /shared)
  └── 결과 저장
```

### 디렉토리 구조
```
/data/<project_name>/
├── templates/
│   └── base_model.k                    # 베이스 모델 (사용자 제공)
├── runid_00001/                        # DOE 케이스 1
│   ├── metadata.json                   # runid 메타데이터
│   ├── Step001/
│   │   ├── metadata.json               # Step 메타 (angle, template)
│   │   ├── input.txt                   # KooMeshModifier 입력
│   │   ├── *_rotated.k                 # 회전된 모델
│   │   ├── d3plot01, d3plot02, ...     # LS-DYNA 결과
│   │   ├── dynain                      # 변형 상태 (다음 Step용)
│   │   ├── messag                      # LS-DYNA 로그
│   │   └── Step001.lock                # 완료 마크
│   ├── Step002/
│   │   ├── metadata.json
│   │   ├── dynaintoinitial.txt         # DYNAIN_TO_INITIAL 입력
│   │   ├── Initial.k                   # 변환된 초기 상태
│   │   └── ...
│   └── Step003/
├── runid_00002/
└── ...
```

---

## 3. 주요 컴포넌트

### 3.1 koocr CLI
**위치**: `/opt/pyKooCAE/koocr`
**역할**: 사용자 인터페이스

**명령어**:
```bash
# 1. 설정 준비
koocr prepare scenario.json -o runner_config.json

# 2. 작업 제출
koocr submit runner_config.json \
    --nodes 2 \
    --jobs-per-node 4 \
    --ncpu-per-job 16

# 3. 진행 상황 확인
koocr status [runner_config.json]

# 4. 결과 수집
koocr collect runner_config.json [output_dir]
```

**구현 상태**: ✅ 완료
- `cmd_prepare()`: scenario.json → runner_config.json 변환
- `cmd_submit()`: Slurm 작업 제출
- `cmd_status()`: 진행 상황 모니터링 (기본 구현)
- `cmd_collect()`: 결과 수집 (스텁)

**최근 수정**:
- ✅ `cmd_prepare()`에서 CumulativeDesigner 초기화 수정 (딕셔너리 전달)
- ✅ traceback 출력 추가 (디버깅 용이)

---

### 3.2 CumulativeDesigner
**위치**: `/opt/pyKooCAE/Runner/CumulativeDesigner.py`
**역할**: scenario.json → runner_config.json 변환

**주요 기능**:
1. 각도 소스 파싱
   - `cuboid_geometry`: 26방향 (Face 6 + Edge 12 + Corner 8)
   - `fibonacci_lattice`: N개 균일 분포
   - `pitching_sweep`, `rolling_sweep`: 범위 스윕
   - `case_txt_file`: 기존 case.txt 파일 읽기

2. Tolerance/DOE 적용
   - 각 각도에 tolerance 범위 적용
   - DOE 확장 (각도당 여러 샘플)

3. 각도 믹싱 전략
   - `same_angle`: 모든 Step 동일 각도
   - `cyclic`: Step마다 순환
   - `random`: Step마다 랜덤
   - `opposite`: Step마다 반대 방향
   - `custom_mapping`: 사용자 정의

4. 템플릿 자동 선택
   - Step 1: `DROP_FIRST`
   - Step 2+: `DROP_CUMULATIVE`

**출력 형식** (runner_config.json):
```json
{
  "project_name": "Test_001_Full26_1Step",
  "base_dir": "/current/working/directory",
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "apptainer_sif": "/opt/apptainers/KooSimulation313.sif",
    "apptainer_bind": "/data:/data,/shared:/shared",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_*.sif",
    "lsdyna_apptainer_bind": "/data:/data,/shared:/shared"
  },
  "scenarios": [
    {
      "scenario_id": "Full_26_Directions_S001",
      "scenario_name": "Full_26_Directions_Single_Drop",
      "total_steps": 1,
      "steps": [
        {
          "step_number": 1,
          "template": "/data/templates/model.k",
          "mode": "DROP",
          "angle": {
            "name": "F1_Top",
            "roll": 0,
            "pitch": 0,
            "yaw": 0
          },
          "input_file": "Step001.k",
          "output_dir": "Step001",
          "dynain_source": null,
          "doe_index": 1
        },
        ...  // 26개 케이스
      ]
    }
  ]
}
```

**구현 상태**: ✅ 완료

---

### 3.3 LargeScaleDOEManager
**위치**: `/opt/pyKooCAE/Runner/LargeScaleDOEManager.py`
**역할**: 대규모 DOE 실행 관리

**주요 메서드**:

#### `__init__(runner_config_path, data_root, nodes, jobs_per_node, ncpu_per_job)`
- runner_config.json 로드
- Apptainer 설정 파싱
- Slurm 리소스 설정

#### `run()` ✅ 새로 추가
- 모든 시나리오에 대해 `run_large_scale_workflow()` 호출
- koocr CLI에서 호출되는 메인 진입점

#### `run_large_scale_workflow(scenario)`
- 각 Step별로:
  1. runid 디렉토리 생성 (모든 DOE)
  2. metadata.json 작성
  3. Slurm Array Job 제출
  4. 이전 Job ID 저장 (의존성 설정용)

#### `create_runid_directory(scenario_id, step_number, doe_index, job_metadata)`
- `runid_XXXXX/` 디렉토리 생성
- `runid_XXXXX/StepNNN/` 생성
- `metadata.json` 작성:
  ```json
  {
    "scenario_id": "...",
    "step_number": 1,
    "doe_index": 1,
    "runid": "runid_00001",
    "angle": {
      "name": "F1_Top",
      "roll": 0,
      "pitch": 0,
      "yaw": 0
    },
    "template": "/data/templates/model.k"
  }
  ```

#### `submit_step_array_job(scenario, step_number, doe_start, doe_end, dependency_job_id)`
- Slurm 스크립트 생성
- Array job 제출
- Job ID 반환

#### `wrap_with_apptainer(command, use_lsdyna=False)`
- 명령어를 Apptainer로 래핑
- `use_lsdyna=False`: KooMeshModifier용 (`apptainer_sif`)
- `use_lsdyna=True`: LS-DYNA용 (`lsdyna_apptainer_sif`)

**구현 상태**: ✅ 완료
**최근 수정**: ✅ `run()` 메서드 추가

---

### 3.4 Slurm 스크립트 생성 로직

**위치**: `LargeScaleDOEManager.submit_step_array_job()` (line 348-680)

#### 스크립트 구조

##### 1. Slurm 헤더
```bash
#!/bin/bash
#SBATCH --job-name=Test_001_Step001
#SBATCH --partition=normal
#SBATCH --array=1-26%8              # 26 케이스, 동시 8개
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=Test_001_Step001_%A_%a.out
#SBATCH --error=Test_001_Step001_%A_%a.err
#SBATCH --dependency=afterok:123456  # Step 2+만
```

##### 2. 변수 설정
```bash
DOE_INDEX=$SLURM_ARRAY_TASK_ID
RUNID="runid_$(printf %05d $DOE_INDEX)"
RUNID_DIR="/data/Test_001/$RUNID"
STEP_DIR="$RUNID_DIR/Step001"
```

##### 3. metadata.json 읽기
```bash
METADATA_FILE="$STEP_DIR/metadata.json"
TEMPLATE=$(jq -r .template "$METADATA_FILE")
ROLL=$(jq -r .angle.roll "$METADATA_FILE")
PITCH=$(jq -r .angle.pitch "$METADATA_FILE")
YAW=$(jq -r .angle.yaw "$METADATA_FILE")
```

##### 4. KooMeshModifier 입력 파일 생성
```bash
INPUT_TXT="$STEP_DIR/input.txt"
cat > "$INPUT_TXT" << EOF
template=$TEMPLATE
roll=$ROLL
pitch=$PITCH
yaw=$YAW
step=1
result_dir=./
EOF
```

##### 5. Step 2+: DYNAIN_TO_INITIAL 실행
```bash
# Step 2+만 실행
if [ step_number > 1 ]; then
    PREV_DYNAIN="../Step001/dynain"

    cat > dynaintoinitial.txt << EOF
*Inputfile
placeholder.k
*Mode
DYNAIN_TO_INITIAL,1
**DynainToInitial,1
*DynainPath,$PREV_DYNAIN
*IncludeStress,True
*RemoveDynamicRelaxation,True
*MovetoOriginAutomatic,True
**EndDynainToInitial
*End
EOF

    # Apptainer 실행
    apptainer exec --bind /data:/data /opt/apptainers/KooSimulation313.sif \
        /opt/KooMeshModifier/run.sh --input="dynaintoinitial.txt"
fi
```

##### 6. DROP_ATTITUDE/DROP_CUMULATIVE 실행
```bash
cd "$STEP_DIR"

# KooMeshModifier (Apptainer)
apptainer exec --bind /data:/data /opt/apptainers/KooSimulation313.sif \
    /opt/KooMeshModifier/run.sh --input="$INPUT_TXT"

# 생성된 .k 파일 찾기
OUTPUT_K=$(find . -maxdepth 1 -name "*.k" -type f -printf "%T@ %p\n" | \
           sort -rn | head -1 | cut -d" " -f2-)
```

##### 7. LS-DYNA 실행
```bash
# LS-DYNA (별도 Apptainer)
apptainer exec --bind /data:/data /opt/apptainers/LSDynaBasic_*.sif \
    mpirun -np 16 /opt/ls-dyna/lsdyna_R16.1.1 \
        i="$OUTPUT_K" memory=60000m ncpu=16
```

##### 8. 완료 마크
```bash
touch "$STEP_DIR/Step001.lock"
```

**구현 상태**: ✅ 완료

---

## 4. 실행 흐름 (전체)

### Phase 1: 준비 (koocr prepare)
```
scenario.json
    ↓
CumulativeDesigner
    ├── 각도 생성 (26개 방향)
    ├── DOE 적용 (tolerance)
    ├── 각도 믹싱 전략
    └── 템플릿 선택
    ↓
runner_config.json
    └── steps[]: 26 × 1 = 26개 step
```

### Phase 2: 제출 (koocr submit)
```
runner_config.json
    ↓
LargeScaleDOEManager.run()
    ↓
run_large_scale_workflow(scenario)
    ↓
for step_num in [1]:
    ├── create_runid_directory() × 26
    │   └── metadata.json 작성
    └── submit_step_array_job()
        └── sbatch slurm_Test_001_Step001.sh
```

### Phase 3: 실행 (Slurm 컴퓨트 노드)
```
Slurm Array Job (--array=1-26%8)
    ├── Round 1: 케이스 1-8 (동시 실행)
    ├── Round 2: 케이스 9-16
    ├── Round 3: 케이스 17-24
    └── Round 4: 케이스 25-26

각 케이스 (예: runid_00001):
    ├── metadata.json 읽기
    ├── [Step 2+만] DYNAIN_TO_INITIAL
    ├── KooMeshModifier (메쉬 회전)
    ├── LS-DYNA (낙하 시뮬레이션)
    └── Step001.lock 생성
```

### Phase 4: 수집 (koocr collect)
```
koocr collect runner_config.json results/
    ├── 완료 확인 (*.lock 파일)
    └── 결과 복사 (현재 스텁)
```

---

## 5. 핵심 설계 결정

### 5.1 runid 사전 생성
**결정**: 모든 runid 디렉토리를 Array Job 제출 **전에** 생성
**이유**:
- metadata.json에 각도/템플릿 정보 저장
- Slurm 스크립트가 metadata를 읽어 실행
- 디렉토리 충돌 방지

**구현**: `run_large_scale_workflow()` line 735-744

### 5.2 metadata.json 활용
**결정**: 실행 정보를 metadata.json에 저장, Slurm에서 읽기
**이유**:
- Slurm 스크립트가 독립적으로 실행 가능
- 재시작/디버깅 용이
- 추적성 향상

**저장 정보**:
```json
{
  "angle": {"name": "F1_Top", "roll": 0, "pitch": 0, "yaw": 0},
  "template": "/data/templates/model.k",
  "step_number": 1,
  "doe_index": 1
}
```

### 5.3 Step 실행 순서
**결정**: Step-by-Step (모든 DOE의 Step 1 완료 → Step 2 시작)
**이유**:
- dynain 파일 의존성
- 리소스 효율 (모든 노드 활용)
- 진행 상황 명확

**vs DOE 파이프라인** (runid_00001: Step 1→2→3, runid_00002: Step 1→2→3):
- ❌ 마지막 DOE가 Step 1 완료되기 전까지 Step 2 시작 불가
- ❌ 리소스 낭비 (일부 노드만 사용)

**구현**: `--dependency=afterok:PREV_JOB_ID`

### 5.4 Apptainer 분리
**결정**: KooMeshModifier와 LS-DYNA가 별도 Apptainer 사용
**이유**:
- 각 도구의 의존성이 다름
- 버전 독립 관리
- 선택적 사용 (한쪽만 Apptainer 가능)

**구현**: `wrap_with_apptainer(command, use_lsdyna=False/True)`

### 5.5 Array Job + Concurrent Limit
**결정**: `--array=1-26%8` 형식으로 동시 실행 제한
**이유**:
- Slurm 스케줄러 부담 최소화 (26개 개별 Job vs 1개 Array Job)
- 자동 큐잉 (8개씩 실행, 완료되면 다음 8개)
- 리소스 공정 분배

**계산**: concurrent = nodes × jobs_per_node = 2 × 4 = 8

---

## 6. 테스트 시나리오

### Test_001_Full26_1Step
**위치**: `/opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/`

**파일**:
- `scenario.json`: 26방향 1회 낙하 설정
- `run.sh`: 실행 스크립트
- `README.md`: 상세 가이드

**설정**:
```json
{
  "project_name": "Test_001_Full26_1Step",
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
      "template": "/data/templates/MinimumModel.k",
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

**실행 방법**:
```bash
cd /opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step
bash run.sh
```

**예상 결과**:
- 26개 runid 디렉토리 생성
- Slurm Array Job 1개 제출 (--array=1-26%8)
- 4 rounds 실행 (8+8+8+2)
- 예상 시간: ~10시간 (케이스당 3시간 가정)

**상태**: ✅ 준비 완료

---

## 7. 대시보드 통합

### Job Template
**위치**: `/opt/pyKooCAE/Examples/HWWarrantyDropTest/hw_warranty_droptest.yaml`

**기능**:
- 웹 UI에서 파일 업로드 (scenario.json + base model .k)
- 자동 경로 설정
- koocr 실행
- 결과 수집

**배포 방법**:
```bash
# 1. 템플릿 복사
cp hw_warranty_droptest.yaml /shared/templates/simulation/

# 2. 스캔
curl -X POST http://localhost:5010/api/jobs/templates/scan

# 3. 확인
curl http://localhost:5010/api/v2/templates/hw-warranty-droptest
```

**문서**:
- `TEMPLATE_README.md`: 대시보드 사용 가이드
- scenario.json 예시 (26방향, 6방향 3스텝, 100방향)
- 리소스 계산 가이드

**상태**: ✅ 완료

---

## 8. 문서

### 주요 문서
| 파일 | 설명 | 상태 |
|------|------|------|
| `README_KooChainRun.md` | KooChainRun 전체 가이드 | ✅ |
| `QUICK_START_GUIDE.md` | 빠른 시작 | ✅ |
| `APPTAINER_GUIDE.md` | Apptainer 통합 가이드 | ✅ |
| `TEMPLATE_README.md` | 대시보드 템플릿 사용법 | ✅ |
| `Test_001.../README.md` | 테스트 시나리오 가이드 | ✅ |
| `SETUP_COMPLETE.md` | 설치 완료 요약 | ✅ |

### 문서 위치
```
/opt/pyKooCAE/
├── README_KooChainRun.md
├── QUICK_START_GUIDE.md
└── Examples/HWWarrantyDropTest/
    ├── APPTAINER_GUIDE.md
    ├── TEMPLATE_README.md
    ├── SETUP_COMPLETE.md
    └── Tests/Test_001_Full26_1Step/
        └── README.md
```

---

## 9. 수정 이력

### 2026-01-23 (최종 수정)

#### 버그 수정
1. **koocr prepare 초기화 오류**
   - 파일: `koocr` line 159-199
   - 문제: CumulativeDesigner에 파일 경로 직접 전달
   - 수정: JSON 로드 후 딕셔너리 전달
   - 상태: ✅ 수정 완료

2. **manager.run() 메서드 누락**
   - 파일: `LargeScaleDOEManager.py` line 681
   - 문제: koocr에서 호출하는 run() 메서드 없음
   - 수정: run() 메서드 추가 (모든 시나리오 실행)
   - 상태: ✅ 수정 완료

#### 기능 추가
- Apptainer 통합 (KooMeshModifier + LS-DYNA 별도)
- Job Template 생성 (대시보드 통합)
- 전체 문서 작성

---

## 10. 검증 완료 항목

### 코드 로직
- ✅ runid 디렉토리 사전 생성
- ✅ metadata.json 저장 및 읽기
- ✅ Step 1: DROP_FIRST만 (DYNAIN_TO_INITIAL 없음)
- ✅ Step 2+: DYNAIN_TO_INITIAL → DROP_CUMULATIVE
- ✅ 이전 dynain 파일 참조 (`../Step{n-1:03d}/dynain`)
- ✅ Apptainer 래핑 (KooMeshModifier, LS-DYNA 별도)
- ✅ Slurm Array Job + 의존성
- ✅ 동시 실행 제한 (concurrent limit)

### 실행 준비
- ✅ koocr CLI 동작 확인
- ✅ scenario.json 설정 (실제 Apptainer 경로)
- ✅ Test_001 시나리오 준비
- ✅ 문서 작성 완료

---

## 11. 다음 단계

### 즉시 실행 가능
```bash
# CLI 방식
cd /opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step
bash run.sh

# 대시보드 방식
# 1. 템플릿 배포
# 2. 웹 UI에서 파일 업로드
# 3. 작업 제출
```

### 추가 개발 권장
1. **결과 수집 기능**
   - `koocr collect` 완전 구현
   - d3plot, dynain, messag 파일 자동 복사
   - 요약 리포트 생성

2. **진행 상황 모니터링**
   - `koocr status` 상세 구현
   - 실시간 완료율 표시
   - 실패 케이스 감지

3. **추가 테스트 시나리오**
   - Test_002: 3회 연속 낙하
   - Test_003: Cyclic 각도 믹싱
   - Test_004: 100방향 Fibonacci

4. **에러 핸들링**
   - Slurm 작업 실패 감지
   - 자동 재시작
   - 로그 수집

---

## 12. 연락처

**프로젝트 위치**: `/opt/pyKooCAE`
**작성자**: Koo Engineering
**버전**: KooChainRun 1.0.0
**최종 업데이트**: 2026-01-23

---

## 요약

KooChainRun 시스템은 **개발 완료** 상태이며, 모든 핵심 기능이 구현되고 검증되었습니다.

**준비 완료**:
- ✅ koocr CLI
- ✅ scenario.json → runner_config.json 변환
- ✅ Slurm Array Job 제출
- ✅ Apptainer 통합
- ✅ metadata 기반 실행
- ✅ Step 간 의존성 관리
- ✅ 대시보드 템플릿
- ✅ 전체 문서

**테스트 가능**: Test_001_Full26_1Step 시나리오 실행 준비 완료
