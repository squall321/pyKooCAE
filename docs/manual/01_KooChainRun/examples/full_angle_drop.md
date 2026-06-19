# 예제: 전각도 낙하 (DROP)

## 1. 목적/개요

전각도 낙하(Full Angle Drop)는 제품을 구면상의 여러 방향(N방향)으로 회전시켜
각각 자유낙하시키는 DOE(Design of Experiments) 시뮬레이션입니다. 워런티 낙하
테스트처럼 "어느 각도로 떨어져도 안전한가"를 한 번의 워크플로우로 검증합니다.

전체 흐름은 `scenario.json`(사용자 정의) → `prepare`(runner_config.json + 헬퍼
스크립트 생성) → `submit`(각 각도를 Slurm 잡으로 제출) → `sphere_report`(모든
각도 결과를 구면 통합 리포트로 후처리)의 4단계입니다.

각 각도(DOE)마다 다음이 노드에서 순차 실행됩니다.
KooMeshModifier(모델 회전 + 바닥판 + contact 생성) → LS-DYNA(낙하 해석) →
deep_report(단일 시뮬 후처리). 모든 각도가 끝나면 `afterany` 의존 잡으로
sphere_report가 한 번 실행되어 Mollweide 구면 분포 + 파트별 통계를 만듭니다.

근거 문서: `docs/FullAngleDrop_HPC_Workflow.md` (전체 HPC 워크플로우)
실제 예제: `Examples/HWWarrantyDropTest/Tests/Test_001~010/`

## 2. 입력 옵션·인자 (표)

### 2.1 `scenarios[].angle_source` — 각도 생성기

| source_type | 의미 | 주요 키 | 생성 개수 |
|---|---|---|---|
| `fibonacci_lattice` | 구면 균등 분포 N방향 (표준 전각도) | `num_directions`(=`num_points` 별칭) | N (예: 10, 100) |
| `cuboid_geometry` | 직육면체 면/모서리/꼭짓점 | `include_faces`/`include_edges`/`include_corners` | 26 (F6+E12+C8) |
| `pitching_sweep` | Pitch 스윕 | `pitch_min`/`pitch_max`/`pitch_step` | 범위/스텝 |
| `rolling_sweep` | Roll 스윕 | `roll_min`/`roll_max`/`roll_step` | 범위/스텝 |
| `case_txt_file` | 사용자 각도 파일 | `case_txt_file` | 파일 내용 |

- `num_directions`는 `num_points`의 별칭으로 둘 다 허용됩니다 (CumulativeDesigner.py:522).
- `cuboid_geometry`는 면 6 + 모서리 12 + 꼭짓점 8 = 26방향이며 각 플래그로 부분 선택 가능 (AngleSourceParser.py:132-157).

### 2.2 `simulation_params` — 낙하 해석 파라미터

| 키 | 의미 | 예시 |
|---|---|---|
| `height` | 낙하 높이 (mm), 자유낙하 속도 환산 | `1500` |
| `tFinal` | 시뮬 종료 시간 (s) | `0.005` |
| `dt` | timestep (s) | `1e-06` |
| `density` / `youngs_modulus` / `poisson_ratio` | 바닥판 재질 | `7850` / `2e11` / `0.3` |
| `drop_surface.type` | 바닥판 타입 | `Plane`/`PlaneGraded`/`RigidWall`/`PlanewithRoughness` |
| `drop_surface.size` / `mesh` | 바닥판 크기·메쉬 [x,y,z] | `[300,300,20]` / `[30,30,2]` |
| `drop_surface.deformable_to_rigid` | 바닥판 강체화 | `false` |

- 바닥판 타입별 `DropSurface` 카드 직렬화는 StepConfigBuilder.py:51-70 참조.

### 2.3 `scenarios[].cumulative`

| 키 | 의미 | 전각도 DROP 표준값 |
|---|---|---|
| `num_steps` | 누적 step 수 | `1` |
| `mode_sequence` | step별 모드 | `["DROP"]` |
| `base_angle_index` / `angle_mixing.strategy` | 각도 인덱스/혼합 전략 | `0` / `"same_angle"` |

### 2.4 `submit` CLI 인자 (KooChainRun:86-140)

| 인자 | 기본값 | 의미 |
|---|---|---|
| `config` | (필수) | runner_config.json 경로 |
| `--mode` | `cumulative` | `cumulative`(DOE당 1잡) / `large-scale`(array job) |
| `--nodes` | `2` | 사용 노드 수 |
| `--jobs-per-node` | `4` | 노드당 동시 잡 수 |
| `--ncpu-per-job` | env.ncpu | 잡당 CPU 수 |
| `--partition` | `normal` | Slurm 파티션 |
| `--memory` | env.memory | 잡당 메모리 |
| `--time-limit` | `24:00:00` | 잡당 시간 제한 |
| `--sequential` | off | 노드당 1잡, 잡 안에서 여러 DOE 순차 실행 |

### 2.5 `postprocess` — KooD3plotReader 후처리 (선택)

| 키 | 기본값 | 의미 |
|---|---|---|
| `enabled` | `false` | 마스터 토글. false면 sh만 생성, 자동 실행 X |
| `auto_deep` | `true` | 각 시뮬 직후 deep_report 실행 |
| `auto_sphere` | `true` | 모든 시뮬 끝나면 `afterany` 의존 잡으로 sphere |
| `sif_path` | — | compute node `SmartTwinPostprocessor.sif` 경로 |
| `yield_stress_mpa` | `350` | sphere 안전계수 기준 (PostprocessShellGenerator.py:159) |

`enabled`/`auto_sphere`/`auto_impact` 검사 위치: KooChainRun:838, 852, 858.

## 3. 사용 예제

### 3.1 scenario.json (Fibonacci 100방향)

`Examples/HWWarrantyDropTest/Tests/Test_005_Fibonacci_100/scenario.json`에서 발췌:

```json
{
  "project_name": "Test_005_Fibonacci_100",
  "environment": {
    "koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "apptainer_sif": "/opt/apptainers/SmartTwinPreprocessor.sif",
    "apptainer_bind": "/data:/data",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif",
    "lsdyna_apptainer_env": {
      "LSTC_FILE": "/opt/ls-dyna_license/LSTC_FILE",
      "LSTC_LICENSE_SERVER": "10.179.100.25",
      "FI_PROVIDER": "tcp", "I_MPI_FABRICS": "ofi",
      "LD_LIBRARY_PATH": "/opt/openmpi/lib"
    },
    "apptainer_tmpdir": "/data/tmp",
    "ncpu": 1,
    "koochainrun_path": "/data/SmartTwinPreprocessor/bin/KooChainRun",
    "time_limit": "168:00:00"
  },
  "simulation_params": {
    "height": 1500, "tFinal": 0.005, "dt": 1e-06,
    "density": 7850, "youngs_modulus": 200000000000, "poisson_ratio": 0.3,
    "drop_surface": {
      "type": "Plane", "size": [300, 300, 20], "mesh": [30, 30, 2],
      "deformable_to_rigid": false
    }
  },
  "scenarios": [
    {
      "scenario_name": "Fibonacci_Lattice_100_Directions",
      "template": "MinimumModel.k",
      "angle_source": {
        "source_type": "fibonacci_lattice",
        "fibonacci_lattice": { "num_directions": 100 }
      },
      "cumulative": {
        "num_steps": 1,
        "mode_sequence": ["DROP"],
        "base_angle_index": 0,
        "angle_mixing": { "strategy": "same_angle" }
      }
    }
  ]
}
```

> 참고: 위 실제 테스트 파일에는 `postprocess` 블록이 없습니다(후처리 미사용).
> 후처리를 켜려면 아래 블록을 scenario.json에 추가합니다
> (`docs/FullAngleDrop_HPC_Workflow.md` §3.1 예시 발췌):

```json
"postprocess": {
  "enabled": true,
  "auto_deep": true,
  "auto_sphere": true,
  "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
  "yield_stress_mpa": 350
}
```

### 3.2 26방향(cuboid) 변형

`Tests/Test_001_Full26_1Step/scenario.json` 발췌 — `angle_source`만 교체:

```json
"angle_source": {
  "source_type": "cuboid_geometry",
  "cuboid_geometry": {
    "include_faces": true,
    "include_edges": true,
    "include_corners": true
  }
}
```

### 3.3 CLI 실행 흐름

`docs/FullAngleDrop_HPC_Workflow.md` §3.3 발췌:

```bash
# 1. 작업 디렉토리 + 모델 준비
mkdir -p /data/koopark/MyTest
cp MinimumModel.k /data/koopark/MyTest/

# 2. prepare: scenario.json → runner_config.json + 헬퍼 sh (+ sphere_report.sh)
cd /data/koopark/MyTest
KooChainRun prepare scenario.json

# 3. submit: 모든 각도 Slurm 잡 제출 (+ auto_sphere 시 sphere 의존 잡 자동 제출)
KooChainRun submit runner_config.json

# 4. 진행 확인
squeue -u $USER
KooChainRun status

# 5. 후처리 수동 trigger (auto 미사용/일부 fail 시)
KooChainRun postprocess runner_config.json --all      # deep 모두 + sphere
KooChainRun postprocess runner_config.json --deep     # deep만
KooChainRun postprocess runner_config.json --sphere   # sphere만
```

### 3.4 생성되는 KooMeshModifier 입력 (step_config) — DROP 카드

각 각도마다 자동 생성되는 `step_config` 블록 (StepConfigBuilder.py:146-174):

```
*Inputfile
<model_file>
*RunDirectoryMode,True,<output_dir>
*Info,<project>,Step1
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,<roll>
EulerPitching,<pitch>
EulerYawing,<yaw>
Height,<height>
OffsetDistance,<offset>
Density,<density>
YoungsModulus,<E>
PoissonRatio,<nu>
tFinal,<tFinal>
dt,<dt>
DropSurface,Plane,300,300,20,30,30,2
**EndDropAttitude
*End
```

실제 다각도 직렬화 형태(여러 각도를 한 카드에 콤마로 나열)는
`Examples/alldropangles/drop_attitude.txt`에서 확인할 수 있습니다 (예:
`EulerRolling,108.40,-96.70,-76.59,...`).

## 4. 동작 원리 (코드 근거)

1. **각도 생성** — `scenarios[].angle_source.source_type`에 따라 분기.
   - fibonacci: 황금각(≈137.508°) 기반 구면 균등 분포 점 생성 후 오일러
     각도(roll/pitch/yaw)로 변환 (AngleSourceParser.py:179-207). `roll = lat-90`,
     `pitch = -lon`, `yaw = 0`.
   - cuboid: 면/모서리/꼭짓점 26개 고정 매핑 (AngleSourceParser.py:132-157).
   - `num_directions`는 `num_points` 별칭으로 매핑 (CumulativeDesigner.py:522).
   - 디스패치: AngleSourceParser.py:293-330 (`parse_angle_source`).

2. **prepare** — scenario.json 로드 후 `CumulativeDesigner.parse_user_config()`로
   runner_config.json 생성, output_dir/slurm_scripts 미리 생성, rerun/stop/
   diagnose/copy.sh 헬퍼 생성 (KooChainRun:347-414, _generate_helper_scripts:417-433).
   `postprocess`가 있으면 항상 `sphere_report.sh`(+impact)도 생성
   (CumulativeDesigner.py:875-889).

3. **DROP step_config 생성** — `mode == "DROP"`일 때
   `build_drop_attitude_config(...)` 호출하여 `DROP_ATTITUDE` 카드 작성
   (CumulativeScenarioRunner.py:1175-1194 → StepConfigBuilder.py:146-174).
   `drop_surface.type`에 따라 `DropSurface` 라인 직렬화 (StepConfigBuilder.py:51-70).

4. **submit** — `--mode cumulative`(기본)는 DOE당 Slurm 잡 제출. submit 종료 후
   `_maybe_submit_sphere_after`가 호출되어 종합 리포트 잡을 처리
   (KooChainRun:816-822). DROP 시나리오는 sphere, IMPACT는 impact로 라우팅
   (`report_mode_from_runner_config`, KooChainRun:850-862).

5. **sphere 의존 잡** — `postprocess.enabled` && `auto_sphere`일 때만 진행
   (KooChainRun:838, 858). jobs.json의 모든 job_id를 모아
   `--dependency=afterany:<id>:<id>...`로 sphere sbatch 제출
   (KooChainRun:880-906). 일부 잡이 fail해도 `afterany`이므로 sphere는 진행됩니다.

6. **sphere_report 내부** — `Run_*/Output/{mes0000,d3hsp,*.log}`에서
   `N o r m a l    t e r m i n a t i o n` 매칭으로 정상 종료 시뮬만 필터,
   deep_report 결과를 `analysis_results/<Run_*>`로 symlink한 뒤
   `apptainer exec ... python3 -m koo_sphere_report --test-dir ... --yield-stress`
   실행 (PostprocessShellGenerator.py:185-227). 정상 종료+deep 완료 시뮬이
   0개면 skip (PostprocessShellGenerator.py:211-217).

## 5. 주의사항·한계

- **postprocess는 기본 비활성**: `enabled`(기본 `false`)를 명시적으로 켜지 않으면
  prepare 시 sh만 만들고 자동 실행은 하지 않습니다 (KooChainRun:838). 실제
  Test_001~010 scenario.json에는 postprocess 블록이 없습니다.
- **sphere는 deep_report 선행 필수**: deep_report가 끝난 시뮬만 sphere 입력으로
  쓰이며, 0개면 sphere skip → "KooChainRun postprocess --deep 먼저 실행" 힌트
  출력 (PostprocessShellGenerator.py:211-216).
- **라이선스 서버 IP**: `lsdyna_apptainer_env.LSTC_LICENSE_SERVER`가 실제 head node
  IP여야 합니다. 실제 테스트 파일은 `10.179.100.25`이나 워크플로우 문서 예시는
  `192.168.122.1`로 환경마다 다릅니다 — **확인 필요**(배포 환경에 맞게 일괄 수정).
- **SIF는 compute node 로컬 디스크**: `/opt/apptainers/`는 NFS가 아니라 노드별
  로컬이므로 누락 시 노드별 배포 필요 (FullAngleDrop_HPC_Workflow.md §1).
- **APPTAINER_TMPDIR**: host env var로 export됨(`--env` 아님). 테스트 디렉토리는
  NFS(`/data/...`)여야 compute node가 볼 수 있음. Test_010은 `apptainer_tmpdir`이
  `/tmp`로 되어 있는데(scenario.json:21) 이는 컴퓨트 노드가 못 보는 경로일 수
  있음 — **확인 필요**.
- **동시 실행 한계**: 동시 실행 수 = 노드 수 × 노드당 동시 잡 수. 큰 모델은
  `ncpu`를 올려야 하나 클러스터 용량 한계가 있음 (FullAngleDrop_HPC_Workflow.md §3.4).

## 6. 개발 현황

**구현됨.**

근거:
- 전각도 DROP 워크플로우(angle_source → prepare → submit → sphere)가 실제 CLI
  스크립트(`KooChainRun`)와 Runner 모듈에 모두 존재하며 file:line으로 확인됨
  (AngleSourceParser.py, CumulativeDesigner.py, StepConfigBuilder.py,
  CumulativeScenarioRunner.py, PostprocessShellGenerator.py, KooChainRun).
- 실제 e2e 예제 디렉토리 Test_001~010이 존재하고 각각 scenario.json +
  runner_config.json + 헬퍼 스크립트(run.sh/rerun.sh/stop.sh/diagnose.sh)가
  생성되어 있음. Test_005/Test_010에는 jobs.json(제출 기록)도 존재.
- 후처리(sphere_report) 자동 연결은 구현되어 있으나, 제공된 예제
  scenario.json들은 postprocess 블록을 포함하지 않아 후처리 자동 실행
  부분의 e2e 산출물(sphere_report.html)은 예제 디렉토리에서 직접 확인되지
  않음 — **부분 확인**(코드 경로는 검증, 예제 산출물 미확인).
