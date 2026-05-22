# 전각도 낙하 시뮬레이션 HPC 워크플로우 종합 가이드

KooChainRun 기반 다각도(N방향) 낙하 시뮬을 HPC(Slurm) 환경에서 실행하고 후처리까지 자동화하는 전체 흐름.

## 1. HPC 환경 구성

### Slurm 클러스터
```
PARTITION   TIMELIMIT      NODES   CPUs   MEMORY   NODELIST
normal*     7-00:00:00     2       4      4 GB     node[001-002]   ← 시뮬 실행
viz         60-00:00:00    2       6      3.5 GB+  viz-node[001-002]
gpu         7-00:00:00     1       8      32 GB    smarttwincluster
```

- `normal` partition이 default — KooChainRun submit 시 사용.
- node당 4 CPU + 4 GB RAM (테스트 클러스터). 시뮬 1개당 1 CPU + ~2 GB.
- 헤드 노드(이 셸): SSH 접속 + Slurm 클라이언트만 (시뮬 실행 X).

### Compute Node `/opt/apptainers/` (각 노드 로컬 디스크)

| SIF | 크기 | 용도 |
|---|---|---|
| `SmartTwinPreprocessor.sif` | 1.4 GB | KooMeshModifier 실행 환경 (OCC, vtk, trimesh, gmsh 등) |
| `SmartTwinPostprocessor.sif` | 800 MB | KooD3plotReader 실행 환경 (deep_report + sphere_report) |
| `LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif` | 970 MB | LS-DYNA MPP single precision |
| `LSDynaBasic_aocc420_ompi4.0.5_mpp_d.sif` | 1.4 GB | LS-DYNA MPP double precision |
| `LSDynaBasic_ifort2022_impilatest_mpp_s/d.sif` | 1.4/1.4 GB | LS-DYNA + Intel MPI |
| `AnsysStructures2025R2.sif` | 12 GB | Ansys (별도 워크플로우) |
| `KooSimulationPython313.sif` | 470 MB | Python 시뮬 헬퍼 |

**중요:**
- 각 노드의 `/opt/apptainers/`는 **로컬 디스크** (NFS 아님). 노드별 inode 다름. SIF 변경 시 각 노드에 ssh + sudo cp 필요
- 신규 SIF 추가는 `/home/koopark/claude/KooSlurmInstallAutomationRefactory/apptainer/deploy_compute_images.sh` 사용 가능
- 단일 SIF 빠른 배포: `ssh node00X "sudo cp /data/.../X.sif /opt/apptainers/"` (sudo NOPASSWD OK)
- 헤드 노드에는 `/opt/apptainers/`에 SIF 일부만 있음 (postprocess 수동 실행 시 헤드 노드도 필요)

### `/data/` 디렉토리 (공유 NFS, 모든 노드에서 동일)

```
/data/
├── SmartTwinPreprocessor/           ← 배포된 KooMeshModifier + KooChainRun 바이너리
│   ├── bin/KooChainRun              ← Nuitka 컴파일된 CLI (KooChainRun.bin symlink)
│   ├── bin/KooMeshModifier
│   └── lib/                         ← 각종 .so 등
├── SmartTwinPostprocessor/
│   ├── SmartTwinPostprocessor.sif   ← Postprocessor SIF (compute node /opt에도 배포 필요)
│   └── SmartTwinPostProcessorGUI.sif
├── tmp/                             ← apptainer 임시 디렉토리 (APPTAINER_TMPDIR)
├── koopark/                         ← 사용자 작업 디렉토리 (시나리오 + 결과)
│   ├── Test_*                       ← 각 테스트별 폴더
│   └── ...
├── ls-dyna_license/                 ← LSTC 라이선스 파일 (compute node에서 사용)
└── ...
```

## 2. 핵심 구성 요소

### KooMeshModifier (전처리)
- 입력: `MinimumModel.k` (LS-DYNA mesh) + `step_config.txt` (모드/옵션)
- 동작: 모델 회전(각도 적용), contact 자동 생성, 바닥판 추가, 기타 modification 모드 적용
- 출력: `Run_<run_id>/DropSet.k` (시뮬 input), `Run_<run_id>/Output/` (LS-DYNA 결과 stage-out 대상)
- 실행: 항상 `SmartTwinPreprocessor.sif` 안에서 (PythonOCC, gmsh 등 필요)

### KooChainRun (워크플로우 CLI)
- subcommands: `prepare`, `submit`, `status`, `run`, `collect`, `stop`, `rerun`, `diagnose`, `postprocess`
- 입력: `scenario.json` (사용자 정의) → `runner_config.json` (내부 표준)
- 출력: `runner_config.json` + `output/Run_*/` + `jobs.json` + helper scripts (`rerun.sh`, `stop.sh` 등)

### LS-DYNA
- compute node `/opt/apptainers/LSDynaBasic_*.sif` 안에서 실행
- 라이선스: `LSTC_LICENSE_SERVER=192.168.122.1` (현재 IP, 변경 시 모든 scenario.json 수정 필요)
- 라이선스 파일: `LSTC_FILE=/opt/ls-dyna_license/LSTC_FILE` (compute node)

### KooD3plotReader (후처리)
- `koo_deep_report`: 단일 시뮬 → HTML + JSON + section view 영상
- `koo_sphere_report`: 다각도 통합 → Mollweide + per-part 통계
- 항상 `SmartTwinPostprocessor.sif` 안에서

## 3. 전각도 낙하 워크플로우

### 3.1 시나리오 파일 (`scenario.json`)

핵심 옵션 구조:
```json
{
  "project_name": "MyTest",
  "base_dir": "/data/koopark/MyTest",
  "environment": {
    "koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "mpi_path": "mpirun",
    "memory": "2G",
    "lsdyna_memory": "2000m",
    "apptainer_sif": "/opt/apptainers/SmartTwinPreprocessor.sif",
    "apptainer_bind": "/data:/data,/shared:/shared",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif",
    "lsdyna_apptainer_bind": "/data:/data,/shared:/shared",
    "lsdyna_apptainer_env": {
      "LSTC_FILE": "/opt/ls-dyna_license/LSTC_FILE",
      "LSTC_LICENSE_SERVER": "192.168.122.1",
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
    "time_limit": "168:00:00"
  },
  "simulation_params": {
    "height": 1500,
    "tFinal": 0.005,
    "dt": 1e-06,
    "density": 7850,
    "youngs_modulus": 200000000000,
    "poisson_ratio": 0.3,
    "drop_surface": {
      "type": "Plane",
      "size": [300, 300, 20],
      "mesh": [30, 30, 2],
      "deformable_to_rigid": false
    }
  },
  "scenarios": [
    {
      "scenario_name": "Fibonacci_100_Directions",
      "template": "MinimumModel.k",
      "angle_source": {
        "source_type": "fibonacci_lattice",
        "fibonacci_lattice": {"num_directions": 100}
      },
      "cumulative": {
        "num_steps": 1,
        "mode_sequence": ["DROP"],
        "base_angle_index": 0,
        "angle_mixing": {"strategy": "same_angle"}
      }
    }
  ],
  "postprocess": {
    "enabled": true,
    "auto_deep": true,
    "auto_sphere": true,
    "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
    "yield_stress_mpa": 350,
    "section_view_axes": ["z"],
    "section_view_fields": ["von_mises"],
    "section_view_mode": "section",
    "ua_threads": 8,
    "sv_threads": 8,
    "deep_timeout_seconds": 7200,
    "sphere_memory": "32G",
    "sphere_time_limit": "04:00:00"
  }
}
```

### 3.2 옵션 의미

**환경 (`environment`):**
- `koomeshmodifier_path` / `lsdyna_path`: SIF 안 절대경로 (sif 안 마운트 기준)
- `apptainer_sif`: KooMeshModifier 실행용 SIF (compute node 로컬)
- `lsdyna_apptainer_sif`: LS-DYNA SIF (single vs double precision 선택)
- `apptainer_bind`: SIF 안에서 보이는 호스트 경로 마운트
- `apptainer_tmpdir`: `APPTAINER_TMPDIR` (host env var로 export됨, NOT `--env`)
- `lsdyna_apptainer_env.LSTC_LICENSE_SERVER`: 현재 `192.168.122.1`. 변경 시 모든 scenario에서 일괄 수정 필요

**시뮬 (`simulation_params`):**
- `height`: 낙하 높이 (mm) — 자유낙하 속도 계산용
- `tFinal`: 시뮬 종료 시간 (s) — 보통 5~10 ms
- `dt`: 명시 timestep (s, 보통 자동 조절)
- `drop_surface`: 바닥판 타입 (`Plane` / `PlaneGraded` / `RigidWall` / `PlanewithRoughness`)

**시나리오 (`scenarios[].angle_source`):**
- `fibonacci_lattice`: 구면 균등 분포 N방향 — 표준 전각도 낙하
- `regular_grid`: 정규 grid
- `manual`: 사용자 명시 (roll/pitch/yaw 직접)
- `same_angle`: 한 각도만 반복 (test/debug)

**후처리 (`postprocess`):**
- `enabled` (default `false`): 마스터 토글. false면 sh만 생성, 자동 실행 X
- `auto_deep` (default `true`): 각 시뮬 직후 같은 노드에서 deep_report 실행
- `auto_sphere` (default `true`): 모든 시뮬 끝나면 Slurm dependent job(`afterany`)으로 sphere
- `sif_path`: compute node 절대경로 (`/opt/apptainers/SmartTwinPostprocessor.sif`)
- `yield_stress_mpa`: sphere의 안전계수 계산 기준
- `section_view_axes`/`fields`/`mode`: deep_report 단면뷰 옵션

### 3.3 실행 명령

```bash
# 1. 작업 디렉토리 + 모델 준비
mkdir -p /data/koopark/MyTest
cp /path/to/MinimumModel.k /data/koopark/MyTest/

# 2. scenario.json 작성 (위 예시 참고)
vi /data/koopark/MyTest/scenario.json

# 3. prepare: scenario.json → runner_config.json + helper sh + (postprocess 있으면) sphere_report.sh
cd /data/koopark/MyTest
KooChainRun prepare scenario.json

# 4. submit: 모든 각도 Slurm job 제출 + (postprocess.auto_sphere=true 시) sphere dependent job 자동 제출
KooChainRun submit runner_config.json

# 5. 진행 상황
squeue -u $USER
KooChainRun status

# 6. 후처리 수동 trigger (auto 안 켰거나 일부 fail 시)
KooChainRun postprocess runner_config.json --all     # deep + sphere 모두
KooChainRun postprocess runner_config.json --deep    # deep만
KooChainRun postprocess runner_config.json --sphere  # sphere만

# 7. 결과 위치
# output/Run_*/Output/d3plot       LS-DYNA 결과
# output/Run_*/Output/report/      deep_report HTML + JSON + renders
# output/sphere_report.html        통합 sphere_report
# output/sphere_normal_term.txt    정상 종료 시뮬 목록
```

### 3.4 잡 특성 (Slurm 분석 시 참고)

| 단계 | CPU | RAM | 시간 | 노드 |
|---|---|---|---|---|
| KooMeshModifier (각도별 1회) | 1 | ~1 GB | ~10s | normal |
| LS-DYNA MPP (1 case) | 1 (`ncpu=1`) | `lsdyna_memory=2000m` | 5-30분 (모델 따라) | normal |
| dynain → stage-out | 1 | minimal | ~1s | normal |
| `deep_report` (auto, LS-DYNA 직후) | `sv_threads`+`ua_threads` | ~2-4 GB | 1-3분 (소형 모델) | normal (LS-DYNA와 같은 노드) |
| `sphere_report` (dependent job) | `sphere_ncpu` | `sphere_memory` | 30s-2분 | normal |

**병렬 패턴:**
- 162개 fibonacci 시 동시 실행 = node 수 × node당 동시 job (normal: 2 nodes × ~4 CPU = 8 동시)
- 큰 모델은 `ncpu=4` 또는 8로 늘려야 (단 cluster 용량 한계)
- sphere job은 `--dependency=afterany`이므로 일부 fail도 정상 진행

**파일 흐름:**
```
[head node]                           [compute node]
scenario.json                         /opt/apptainers/*.sif
   ↓ prepare                            ↓
runner_config.json                    apptainer exec
   ↓ submit                              ↓
slurm sbatch ─────────────►            KooMeshModifier(SIF) → DropSet.k
                                         ↓
                                       LS-DYNA(SIF) → d3plot
                                         ↓
                                       deep_report(SIF) → report/
                                         ↓
                                       [stage-out → /data/output/Run_*/Output/]

[모든 job 끝나면]
sphere_report dependent job ──────►   apptainer exec sphere_report(SIF)
                                         ↓
                                       /data/output/sphere_report.html
```

## 4. 트러블슈팅

### 시뮬 5초 만에 fail (MPI_ABORT errorcode 1)
- **원인 1:** `LSTC_LICENSE_SERVER` IP 변경됨
  - 확인: `scenario.json`에서 IP 검색
  - 현재 정상: `192.168.122.1`
- **원인 2:** 라이선스 만료 / 서버 다운
  - 확인: `ssh node001 "ssh -p 31010 192.168.122.1 echo ok"` (포트 확인 필요)

### sphere_report "SIF not found"
- compute node `/opt/apptainers/SmartTwinPostprocessor.sif` 없음
- 배포: `ssh node00X "sudo cp /data/SmartTwinPostprocessor/SmartTwinPostprocessor.sif /opt/apptainers/"`
- head node에도 필요 (수동 trigger 시)

### sphere_report "정상 종료 시뮬 0개"
- LS-DYNA 로그 위치 확인: `Run_*/Output/mes0000` 안에 `N o r m a l    t e r m i n a t i o n` 매칭
- 시뮬이 시간 초과 / divergence로 끝났을 가능성

### sphere_report "No analysis_results"
- deep_report 먼저 완료해야 — `KooChainRun postprocess --deep` 실행 후 `--sphere`

### Apptainer 시작 10분+ 걸림
- `squashfuse` 없는 노드 — `apt install libfuse2 squashfuse`
- 또는 `APPTAINER_TMPDIR=/data/tmp` 설정 (host env var, NOT `--env`)

### deep_report.sh 누락 (시뮬 fail 후 후처리 시도)
- KooChainRun postprocess --deep이 fallback으로 자동 생성 (v1.4.0+)
- d3plot이 `Run_*/Output/`에 있어야 함

## 5. 디렉토리 명명 규약

- **`Run_<YYYYMMDD>_<HHMMSS>_<hash6>/`**: 각 시뮬 케이스 (KooMeshModifier가 생성)
- **`output/`**: 모든 Run_* 폴더의 부모
- **`output/Run_*/Output/`**: LS-DYNA 결과 (d3plot, mes0000, d3hsp 등)
- **`output/Run_*/Output/report/`**: deep_report 결과 (HTML, result.json, renders)
- **`output/Run_*/DropSet.k`**: 시뮬 input (KooMeshModifier 결과)
- **`output/Run_*/DropSet.json`**: 메타데이터 (각도, 파트 정보 등)
- **`output/Run_*/deep_report.sh`**: 후처리 sh (자동 생성)
- **`output/Run_*/deep_report.log`**: 후처리 실행 로그
- **`output/sphere_report.sh`**: 통합 후처리 sh (prepare 시 생성)
- **`output/sphere_report.sbatch`**: dependent Slurm sbatch (submit 시 생성)
- **`output/sphere_report.html`**: 통합 결과
- **`output/sphere_normal_term.txt`**: 정상 종료 시뮬 목록
- **`analysis_results/Run_*/`** (sphere_report.sh가 만듦): deep_report 결과 symlink (sphere 입력용)
- **`jobs.json`**: Slurm job ID 목록 (KooChainRun status/stop/rerun이 사용)

## 6. 버전

| 버전 | 주요 추가 |
|---|---|
| v1.0~1.1 | 기본 KooChainRun, DROP_ATTITUDE |
| v1.2.0 | PreserveIncludes + DECOMPOSE_K + MERGE_K + IMPORT_MERGE_K |
| v1.3.0 | VIBRATION_LOAD 모드 + 빌드 incremental cache |
| v1.4.0 | KooD3plotReader 후처리 통합 (deep_report + sphere_report auto) |

## 7. 참고 문서

- `Examples/HWWarrantyDropTest/Tests/Test_005_Fibonacci_100/` — 표준 162방향 예시
- `Examples/postprocess_pipeline/` — 후처리 옵션 활성/비활성 예시
- `Examples/vibration_load/` — 진동 하중 모드
- `KooD3plotReader/docs/Reports_Usage.md` — 후처리 도구 상세 사용법
