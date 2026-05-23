# KooChainRun Portable Quickstart — 다른 PC에서 LLM과 함께 잡 던지기

이 문서는 **다른 PC(같은 HPC 클러스터 셋업, IP만 다름)에서 LLM(Claude/GPT)의 도움을 받아 LS-DYNA 전각도 낙하 잡을 던지는 사람**을 위한 단일 가이드입니다. 이 한 문서만 LLM에 던지면 시나리오 작성과 트러블슈팅을 도와줍니다.

---

## 0. 전제 조건 체크리스트

새 PC가 다음을 갖췄는지 먼저 확인:

- [ ] Slurm 클러스터 (head node + compute node ≥ 1대)
- [ ] Apptainer (Singularity) 설치
- [ ] compute node `/opt/apptainers/`에 다음 SIF 존재:
  - `SmartTwinPreprocessor.sif` (KooMeshModifier 실행)
  - `LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif` (LS-DYNA single precision MPP)
  - `SmartTwinPostprocessor.sif` (후처리, KooD3plotReader)
- [ ] LSTC 라이센스 서버 IP (compute node에서 접근 가능)
- [ ] 공유 storage 마운트 (`/data/` 또는 `/shared/`)
- [ ] `sudo` 권한 (tar 풀 때 필요)

확인 명령:
```bash
sinfo                           # Slurm 노드 상태
ls /opt/apptainers/             # SIF 파일 목록 (head node)
ssh <compute_node> ls /opt/apptainers/   # compute node에서도 확인
scontrol show node | grep RealMemory  # 노드별 RAM
```

---

## 1. 한 번만 설치

다음 3개 파일을 다른 PC로 복사:

| 파일 | 출처 | 크기 |
|---|---|---|
| `SmartTwinPreprocessor_*.tar.gz` | `/data/SmartTwinPreprocessor/` | ~1.2 GB |
| `Examples/portable_bundle/` 폴더 전체 (시나리오 JSON 4종 + 이 QUICKSTART + README + HOW_TO_ASK_LLM) | 이 repo | < 100 KB |

설치 명령:
```bash
# 1. tar 풀기
sudo tar xzf SmartTwinPreprocessor_*.tar.gz -C /

# 또는 분리해서 설치한 경우:
sudo tar xzf SmartTwinPreprocessor_*.tar.gz -C /data/SmartTwinPreprocessor/
sudo tar xzf SmartTwinPreprocessor_*.tar.gz -C /opt/SmartTwinPreprocessor/

# 2. 동작 확인
/data/SmartTwinPreprocessor/bin/KooChainRun --version
# → KooChainRun 1.4.0  (출력되면 OK)
```

---

## 2. 시나리오 파일 — 새 PC에서 바꿔야 할 것 (3가지만)

`Examples/portable_bundle/`의 시나리오 JSON 중 하나를 선택하고, 다음 3가지만 본인 환경에 맞게 수정합니다.

### 2.1 필수 변경 3개

```json
{
  "base_dir": "/data/<your_user>/<your_project>",   // ← (1) 본인 작업 경로

  "environment": {
    "apptainer_bind": "/data:/data,/shared:/shared", // ← (2) 새 클러스터의 마운트 (보통 동일)
    "lsdyna_apptainer_bind": "/data:/data,/shared:/shared",

    "lsdyna_apptainer_env": {
      "LSTC_LICENSE_SERVER": "192.168.XXX.YYY"        // ← (3) 새 클러스터의 라이센스 서버 IP
    }
  }
}
```

이 3개만 바꾸면 잡이 떠집니다. 나머지(SIF 경로 등)는 셋업이 동일하면 그대로 OK.

### 2.2 자주 바꾸는 것 (선택)

| 키 | default | 변경 의도 |
|---|---|---|
| `project_name` | 시나리오마다 다름 | Slurm 잡 이름 prefix가 됨 |
| `simulation_params.tFinal` | `0.005` | 시뮬 종료 시간 (s). 빠른 검증은 `0.0005` |
| `simulation_params.height` | `1500` | 낙하 높이 (mm) |
| `scenarios[].angle_source.fibonacci_lattice.num_directions` | 시나리오마다 | 각도 수 (1/5/162 등) |
| `environment.ncpu` | `1` | 각 시뮬에 사용할 코어 수 |
| `environment.memory` | `2G` | 각 시뮬 sbatch RAM (compute node RAM 이내) |
| `environment.time_limit` | `01:00:00` | 시뮬 잡 timeout |

---

## 3. 잡 던지기 (3 단계)

```bash
# 1. 작업 디렉토리 + 모델 파일 + 시나리오 준비
mkdir -p /data/<user>/<project>
cd /data/<user>/<project>
cp /path/to/MinimumModel.k .                                  # 본인 .k 모델
cp /path/to/portable_bundle/02_fibonacci_5.json scenario.json
vi scenario.json                                              # 위 2.1 항목 수정

# 2. prepare → submit
/data/SmartTwinPreprocessor/bin/KooChainRun prepare scenario.json
/data/SmartTwinPreprocessor/bin/KooChainRun submit runner_config.json

# 3. 모니터링
squeue -u $USER                       # 잡 진행 상태
ls output/slurm_scripts/*.log         # Slurm stdout/err 로그
ls output/Run_*/Output/d3plot         # LS-DYNA 결과
ls output/sphere_report.html          # 후처리 결과 (자동 시)
```

**수동 후처리** (시뮬 끝났지만 자동 후처리가 fail/skip된 경우):
```bash
/data/SmartTwinPreprocessor/bin/KooChainRun postprocess runner_config.json --all      # deep + sphere
/data/SmartTwinPreprocessor/bin/KooChainRun postprocess runner_config.json --deep     # deep만
/data/SmartTwinPreprocessor/bin/KooChainRun postprocess runner_config.json --sphere   # sphere만
```

---

## 4. Scenario JSON 구조 레퍼런스 (LLM 참조용)

### 4.1 전체 구조

```json
{
  "project_name": "string",
  "base_dir": "absolute path",
  "environment": { ... },           // Slurm/Apptainer/LS-DYNA 환경
  "simulation_params": { ... },     // 물리 파라미터
  "scenarios": [ ... ],             // 시나리오 배열 (보통 1개)
  "postprocess": { ... }            // (선택) 후처리 옵션
}
```

### 4.2 `environment` 키 전체

```json
{
  "koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
  "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
  "mpi_path": "mpirun",
  "memory": "2G",                              // 시뮬 sbatch RAM
  "lsdyna_memory": "2000m",                    // LS-DYNA 내부 메모리
  "apptainer_sif": "/opt/apptainers/SmartTwinPreprocessor.sif",
  "apptainer_bind": "/data:/data,/shared:/shared",
  "apptainer_env": {},
  "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif",
  "lsdyna_apptainer_bind": "/data:/data,/shared:/shared",
  "lsdyna_apptainer_env": {
    "LSTC_FILE": "/opt/ls-dyna_license/LSTC_FILE",
    "LSTC_LICENSE_SERVER": "192.168.XXX.YYY",   // ← 변경 필수
    "FI_PROVIDER": "tcp",
    "I_MPI_FABRICS": "ofi",
    "LD_LIBRARY_PATH": "/opt/openmpi/lib"
  },
  "apptainer_tmpdir": "/data/tmp",
  "nodes_per_job": 1,
  "mpi_launcher": "mpirun",
  "mpi_enabled": true,
  "ncpu": 1,
  "koochainrun_path": "/data/SmartTwinPreprocessor/bin/KooChainRun",
  "time_limit": "01:00:00"
}
```

### 4.3 `simulation_params`

```json
{
  "height": 1500,                              // 낙하 높이 mm
  "tFinal": 0.005,                             // 종료 시간 s
  "dt": 1e-06,                                 // timestep s
  "density": 7850,                             // kg/m³
  "youngs_modulus": 200000000000,              // Pa
  "poisson_ratio": 0.3,
  "drop_surface": {
    "type": "Plane",                           // Plane / PlaneGraded / RigidWall / PlanewithRoughness
    "size": [300, 300, 20],                    // mm (X, Y, Z)
    "mesh": [30, 30, 2],                       // 요소 분할
    "deformable_to_rigid": false               // true면 시뮬 후 rigid로 변환
  }
}
```

### 4.4 `scenarios[]` (각도 소스 옵션)

```json
{
  "scenario_name": "string",
  "template": "MinimumModel.k",                // 작업 디렉토리의 .k 파일 이름
  "angle_source": {
    "source_type": "fibonacci_lattice",        // fibonacci_lattice / cuboid_geometry / pitching_sweep / rolling_sweep / case_txt_file
    "fibonacci_lattice": {"num_directions": 162},
    "cuboid_geometry": {"include_faces": true, "include_edges": true, "include_corners": true},   // cuboid_geometry일 때 (26방향)
    "pitching_sweep": {"step_deg": 10},                                                            // pitching_sweep일 때
    "rolling_sweep": {"step_deg": 10},                                                             // rolling_sweep일 때
    "case_txt_file": {"path": "angles.txt"}                                                        // case_txt_file일 때
  },
  "cumulative": {
    "num_steps": 1,                            // 누적 시뮬 단계 수 (보통 1)
    "mode_sequence": ["DROP"],                 // 각 단계 모드
    "base_angle_index": 0,
    "angle_mixing": {"strategy": "same_angle"}
  }
}
```

### 4.5 `postprocess` (선택, KooD3plotReader 통합)

```json
{
  "enabled": true,                             // 마스터 토글. false면 sh만 생성
  "auto_deep": true,                           // 시뮬 직후 deep_report 자동 실행
  "auto_deep_mode": "inline",                  // "inline" (default) | "separate_job"
  "auto_sphere": true,                         // 모든 시뮬 후 sphere dependent job
  "yield_stress_mpa": 350,                     // sphere 안전계수 계산용
  "section_view_axes": ["z"],                  // deep 단면뷰 축
  "section_view_fields": ["von_mises"],        // 시각화 필드
  "section_view_mode": "section",              // "section" | "section_3d" | "iso_surface"
  "ua_threads": 4,                             // unified_analyzer OpenMP threads
  "sv_threads": 4,                             // section view 동시 렌더
  "deep_timeout_seconds": 3600,                // deep 단일 케이스 timeout
  "sphere_memory": "16G",                      // sphere job sbatch RAM
  "sphere_time_limit": "04:00:00"
}
```

**Slurm Job ID 구조** (`auto_deep_mode`별):

| `auto_deep_mode` | 시뮬 + deep_report | sphere_report |
|---|---|---|
| `"inline"` (default) | **같은 Slurm Job ID** | 별도 잡 (afterany) |
| `"separate_job"` | 다른 Slurm Job ID | 별도 잡 (afterany) |

대부분 default(`inline`)면 충분. 시뮬 노드를 더 빨리 해방하려면 `separate_job`.

---

## 5. 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| 시뮬 5초 만에 fail (MPI_ABORT errorcode 1) | `LSTC_LICENSE_SERVER` IP 잘못됨 → 새 클러스터 IP 확인 |
| 시뮬 fail (signal 12) | SIF 안 `LSTC_LICENSE_SERVER=localhost`인 경우 → `lsdyna_apptainer_env`에서 명시 IP로 override |
| `squashfuse: not found` warning | compute node에 `apt install libfuse2` 필요 (없으면 sandbox 추출 10분+) |
| sbatch 거부 "Memory specification cannot be satisfied" | `memory` / `sphere_memory` / `deep_memory`가 compute node RAM 초과 → `scontrol show node`로 RAM 확인 후 줄이기 |
| sphere_report "No analysis_results" | deep_report 먼저 완료 필요 → `KooChainRun postprocess --deep` 실행 후 `--sphere` |
| sphere_report "정상 종료 시뮬 0개" | 모든 시뮬이 fail. `output/slurm_scripts/*.log`에서 LS-DYNA fail 원인 확인 |
| 후처리 sh 누락 (수동 실행 시) | KooChainRun postprocess가 자동 fallback으로 sh 재생성 (v1.4.0+) |
| `apptainer: command not found` | compute node에 apptainer 미설치 → `apt install apptainer` |
| jobs.json / runner_config.json 없음 | `prepare` 단계 안 돌림. `KooChainRun prepare scenario.json` 먼저 |

---

## 6. 결과 위치 (모든 시뮬 끝난 후)

```
<base_dir>/
├── scenario.json                       (입력)
├── runner_config.json                  (prepare 결과)
├── jobs.json                           (submit 후 잡 트래킹)
├── MinimumModel.k                      (입력 모델)
└── output/
    ├── Run_<timestamp>_<hash>/         (각 각도별 1개 폴더)
    │   ├── DropSet.k                   (회전된 모델)
    │   ├── DropSet.json                (각도 메타데이터)
    │   ├── Output/
    │   │   ├── d3plot, d3plot01, ...   (LS-DYNA 결과)
    │   │   ├── mes0000, d3hsp          (로그 - normal termination 검사 대상)
    │   │   └── report/                 (deep_report HTML + JSON + renders)
    │   └── deep_report.sh              (항상 생성, 수동 실행 가능)
    ├── slurm_scripts/                  (sbatch 파일 + .log)
    ├── sphere_report.sh                (항상 생성)
    ├── sphere_report.sbatch            (auto_sphere=true 시)
    ├── sphere_report.html              (sphere 결과)
    ├── sphere_report.json
    └── sphere_normal_term.txt          (정상 종료 케이스 목록)
```

핵심 결과물:
- **`output/sphere_report.html`** — 162방향 통합 시각화 (Mollweide projection, per-part 통계)
- **`output/Run_*/Output/report/`** — 각 각도별 deep_report (단면뷰 + 시간 이력)

---

## 7. LLM과 함께 사용하기

이 문서 자체를 LLM(Claude/GPT)에 던지고 다음과 같이 요청:

> "이 문서를 참고해서 50각도 fibonacci 낙하 시뮬 시나리오 만들어줘.
>  - base_dir: /data/myuser/test
>  - LSTC IP: 192.168.1.10
>  - 시뮬 시간 0.003s
>  - 후처리 자동 실행 (separate_job)"

LLM이 §4 reference를 읽고 즉시 정확한 JSON을 만들어줍니다.

수정 요청 예:
> "[붙여넣은 시나리오]에서 각도 수를 200개로 늘리고 ncpu를 4로 바꿔줘"

문제 해결 요청 예:
> "잡 던졌더니 sbatch가 'Memory specification cannot be satisfied'로 거부됐어. [scenario.json 붙여넣기]
>  새 클러스터 노드는 RAM 8GB래. 어떻게 고쳐?"
> → LLM이 §5 트러블슈팅 + §2.2 옵션 표 보고 `memory: 2G`로 수정 제안

---

## 8. 참고 문서

**같은 폴더 (portable_bundle/)**:
- `README.md` — 시나리오 4종 비교 표, 새 PC에서 변경할 3가지
- `HOW_TO_ASK_LLM.md` — LLM 요청 프롬프트 템플릿 6종
- `01_minimal_single_drop.json` ~ `04_fibonacci_162_separate_job.json` — 시나리오 예제

**더 자세한 정보가 필요할 때 (별도 repo 문서, 옵션)**:
- `docs/FullAngleDrop_HPC_Workflow.md` — 원본 HPC 워크플로우 (더 상세)
- `Examples/postprocess_pipeline/README.md` — 후처리 파이프라인 상세

---

**버전:** KooChainRun v1.4.0 (auto_deep_mode 지원)
**갱신일:** 2026-05-23
