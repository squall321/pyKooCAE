# KooChainRun 설치 및 설정 완료

**완료일**: 2026-01-23

---

## 완료된 작업

### 1. ✅ KooChainRun CLI 생성

**위치**: `/opt/pyKooCAE/KooChainRun`

**명령어**:
- `KooChainRun prepare` - scenario.json → runner_config.json 변환
- `KooChainRun submit` - Slurm 작업 제출
- `KooChainRun status` - 진행 상황 확인
- `KooChainRun collect` - 결과 수집

**사용 예시**:
```bash
KooChainRun prepare scenario.json -o runner_config.json
KooChainRun submit runner_config.json --nodes 2 --jobs-per-node 4 --ncpu-per-job 16
KooChainRun status
KooChainRun collect runner_config.json results/
```

---

### 2. ✅ Apptainer 통합

**지원되는 설정**:
- KooMeshModifier용 Apptainer: `KooSimulation313.sif`
- LS-DYNA용 Apptainer: `LSDynaBasic_ifort2022_impilatest_mpp_s.sif`
- 별도 바인드 마운트 설정 가능
- Apptainer 없이 직접 실행도 지원

**수정된 파일**:
- `Runner/LargeScaleDOEManager.py` - Apptainer wrapper 추가

**설정 예시** (scenario.json):
```json
{
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "apptainer_sif": "/opt/apptainers/KooSimulation313.sif",
    "apptainer_bind": "/data:/data,/shared:/shared",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_ifort2022_impilatest_mpp_s.sif",
    "lsdyna_apptainer_bind": "/data:/data,/shared:/shared"
  }
}
```

---

### 3. ✅ 테스트 시나리오 준비

**위치**: `Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/`

**포함 파일**:
- `scenario.json` - 26방향 1회 낙하 설정 (실제 Apptainer 경로 포함)
- `run.sh` - 실행 스크립트 (KooChainRun 명령 사용)
- `README.md` - 상세 실행 가이드

**실행 방법**:
```bash
cd Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step
bash run.sh
```

---

### 4. ✅ 대시보드 Job Template 생성

**위치**: `Examples/HWWarrantyDropTest/hw_warranty_droptest.yaml`

**기능**:
- 대시보드 웹 UI에서 작업 제출 가능
- scenario.json + base model .k 파일 업로드
- 자동 경로 설정 및 작업 제출
- 결과 자동 수집

**배포 방법**:
```bash
# 템플릿 복사
cp hw_warranty_droptest.yaml /shared/templates/simulation/

# 템플릿 스캔
curl -X POST http://localhost:5010/api/jobs/templates/scan

# 확인
curl http://localhost:5010/api/v2/templates/hw-warranty-droptest
```

---

### 5. ✅ 문서 작성

| 문서 | 위치 | 설명 |
|------|------|------|
| KooChainRun 가이드 | `README_KooChainRun.md` | CLI 전체 사용법 |
| Apptainer 가이드 | `Examples/HWWarrantyDropTest/APPTAINER_GUIDE.md` | 컨테이너 설정 |
| 템플릿 사용 가이드 | `Examples/HWWarrantyDropTest/TEMPLATE_README.md` | 대시보드 사용법 |
| Test_001 가이드 | `Examples/.../Test_001.../README.md` | 테스트 실행 가이드 |
| 빠른 시작 가이드 | `QUICK_START_GUIDE.md` | 업데이트됨 |

---

## 실행 아키텍처

### 시스템 구조

```
┌─────────────────────────────────────────────────────────┐
│                      헤드 노드                           │
│  - KooChainRun CLI                                            │
│  - scenario.json 준비                                   │
│  - Slurm 작업 제출                                      │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  Slurm 스케줄러                          │
│  - Array job 관리 (--array=1-N%concurrent)              │
│  - Step 간 의존성 (--dependency=afterok:JOB_ID)         │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────────┐ ┌──────────────┐ ┌──────────────┐
│  컴퓨트 노드 1 │ │ 컴퓨트 노드 2 │ │     ...      │
│               │ │              │ │              │
│ KooSimulation │ │ KooSimulation│ │              │
│ 313.sif       │ │ 313.sif      │ │              │
│   ↓           │ │   ↓          │ │              │
│ KooMesh       │ │ KooMesh      │ │              │
│ Modifier      │ │ Modifier     │ │              │
│               │ │              │ │              │
│ LSDynaBasic   │ │ LSDynaBasic  │ │              │
│ _*.sif        │ │ _*.sif       │ │              │
│   ↓           │ │   ↓          │ │              │
│ LS-DYNA       │ │ LS-DYNA      │ │              │
└───────┬───────┘ └──────┬───────┘ └──────────────┘
        │                │
        └────────┬───────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│              공유 스토리지 (/data, /shared)              │
│                                                         │
│  /data/<project_name>/                                 │
│  ├── templates/                                        │
│  │   └── base_model.k                                 │
│  ├── runid_00001/                                     │
│  │   └── Step001/                                     │
│  │       ├── metadata.json                            │
│  │       ├── *_rotated.k                              │
│  │       ├── d3plot*, dynain, messag                  │
│  │       └── Step001.lock                             │
│  ├── runid_00002/                                     │
│  └── ...                                              │
└─────────────────────────────────────────────────────────┘
```

---

### 실행 흐름

#### **단계 1: 준비 (헤드 노드)**
```bash
KooChainRun prepare scenario.json -o runner_config.json
```
1. scenario.json 파싱
2. 각도 생성 (cuboid_geometry, fibonacci_lattice 등)
3. runid_XXXXX 디렉토리 사전 생성
4. metadata.json 작성
5. runner_config.json 생성

#### **단계 2: 제출 (헤드 노드)**
```bash
KooChainRun submit runner_config.json --nodes 2 --jobs-per-node 4 --ncpu-per-job 16
```
1. Slurm 스크립트 생성
2. Array job 제출 (Step 1)
3. 의존성 설정 (Step 2 depends on Step 1, etc.)

#### **단계 3: 실행 (컴퓨트 노드)**

**각 케이스마다** (병렬 실행):
```bash
# KooMeshModifier (회전)
apptainer exec KooSimulation313.sif \
  /opt/KooMeshModifier/run.sh --input=input.txt

# LS-DYNA (시뮬레이션)
apptainer exec LSDynaBasic_*.sif \
  mpirun -np 16 /opt/ls-dyna/lsdyna_R16.1.1 i=rotated.k ncpu=16

# 완료 마크
touch Step001.lock
```

**다음 Step으로 이동** (의존성에 의해 자동):
```bash
# DYNAIN_TO_INITIAL (이전 Step의 dynain → Initial.k)
apptainer exec KooSimulation313.sif \
  /opt/KooMeshModifier/run.sh --input=dynaintoinitial.txt

# LS-DYNA (다음 Step 실행)
apptainer exec LSDynaBasic_*.sif \
  mpirun -np 16 /opt/ls-dyna/lsdyna_R16.1.1 i=Initial.k ncpu=16
```

#### **단계 4: 수집 (헤드 노드)**
```bash
KooChainRun collect runner_config.json results/
```
1. 완료된 케이스 확인 (*.lock 파일)
2. 결과 파일 복사/정리
3. 요약 생성

---

## 리소스 예시

### 테스트 시나리오: 26방향 1회 낙하

| 항목 | 값 |
|------|-----|
| **총 케이스** | 26 (Face 6 + Edge 12 + Corner 8) |
| **노드** | 2 |
| **노드당 Job** | 4 |
| **Job당 CPU** | 16 |
| **동시 실행** | 8 케이스 |
| **총 Rounds** | 4 (⌈26/8⌉) |
| **총 CPU 사용** | 128 코어 (2×4×16) |
| **예상 시간** | ~10시간 (케이스당 3시간 가정) |

**실행 타임라인**:
- Round 1: 케이스 1-8 (0-3시간)
- Round 2: 케이스 9-16 (3-6시간)
- Round 3: 케이스 17-24 (6-9시간)
- Round 4: 케이스 25-26 (9-10시간)

---

## 다음 단계

### 즉시 실행 가능

#### **방법 1: CLI 직접 사용**
```bash
cd /opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step
bash run.sh
```

#### **방법 2: 대시보드 사용**
1. 템플릿 배포:
   ```bash
   cp Examples/HWWarrantyDropTest/hw_warranty_droptest.yaml \
      /shared/templates/simulation/
   curl -X POST http://localhost:5010/api/jobs/templates/scan
   ```

2. 대시보드 접속 → Jobs → New Job
3. "HW Warranty Drop Test" 템플릿 선택
4. scenario.json + base_model.k 업로드
5. Submit

---

### 추가 테스트 시나리오

다음 테스트 케이스 작성 권장:

1. **Test_002_Full26_3Step** - 3회 연속 낙하 (누적 손상)
   - num_steps: 3
   - 각 Step 간 dynain 파일 전달 확인

2. **Test_003_6Faces_Cyclic** - 6방향 Cyclic 전략
   - include_faces: true, edges/corners: false
   - angle_mixing.strategy: "cyclic"

3. **Test_004_100Dir_Fibonacci** - 100방향 균일 분포
   - source_type: "fibonacci_lattice"
   - num_directions: 100

---

## 검증 체크리스트

### 실행 전 확인

- [ ] `/opt/pyKooCAE/KooChainRun` 실행 가능 (`chmod +x`)
- [ ] Apptainer SIF 파일 존재
  - [ ] `/opt/apptainers/KooSimulation313.sif`
  - [ ] `/opt/apptainers/LSDynaBasic_ifort2022_impilatest_mpp_s.sif`
- [ ] 베이스 모델 파일 준비 (`MinimumModel.k`)
- [ ] 공유 스토리지 마운트 확인 (`/data`, `/shared`)
- [ ] scenario.json 문법 확인
  ```bash
  python3 -c "import json; json.load(open('scenario.json'))"
  ```

### 실행 중 확인

- [ ] runner_config.json 생성 확인
- [ ] Slurm 작업 제출 확인 (`squeue -u $USER`)
- [ ] runid 디렉토리 생성 확인
- [ ] 첫 케이스 로그 확인 (KooMeshModifier + LS-DYNA)

### 실행 후 확인

- [ ] 완료 마크 확인 (`find -name "*.lock" | wc -l`)
- [ ] d3plot 파일 생성 확인
- [ ] dynain 파일 생성 확인 (다음 Step용)
- [ ] 결과 수집 확인

---

## 문제 해결 빠른 참조

| 문제 | 해결 |
|------|------|
| KooChainRun 명령을 찾을 수 없음 | `chmod +x /opt/pyKooCAE/KooChainRun` |
| Apptainer SIF 없음 | 경로 확인 또는 apptainer_sif 제거 (직접 실행) |
| 템플릿 파일 없음 | scenario.json의 template 경로 확인 |
| 작업 제출 실패 | Slurm 설정 확인 (`sinfo`, `squeue`) |
| 케이스 실행 실패 | 개별 로그 확인 (`runid_*/Step*/slurm-*.out`) |
| dynain 파일 없음 | LS-DYNA 정상 완료 확인 (`messag` 파일) |

---

## 문의 및 지원

**프로젝트 위치**: `/opt/pyKooCAE`

**주요 파일**:
- CLI: `KooChainRun`
- 코어 로직: `Runner/LargeScaleDOEManager.py`
- 각도 생성: `Angles/CumulativeDesigner.py`
- 문서: `README_KooChainRun.md`

**로그 위치**:
- Slurm 로그: `/data/<project>/runid_*/Step*/slurm-*.out`
- LS-DYNA 로그: `/data/<project>/runid_*/Step*/messag`

---

**작성자**: Koo Engineering
**완료일**: 2026-01-23
**시스템 버전**: KooChainRun 1.0.0
