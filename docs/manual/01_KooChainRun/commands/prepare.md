# KooChainRun prepare

## 1. 목적 / 개요

`KooChainRun prepare` 는 사용자가 작성한 친화적 시나리오 파일(`scenario.json`)을 Runner 가 소비하는 상세 설정 파일(`runner_config.json`)로 변환하는 커맨드이다.

서브파서 정의상 help 는 "Generate runner configuration from scenario", description 는 "Convert user-friendly scenario.json to detailed runner_config.json" 이다 (KooChainRun:63-67).

전체 워크플로우(prepare → submit → status/collect)의 첫 단계로서, 본 커맨드는 다음을 수행한다.

- `scenario.json` 로드 및 `mode` 값에 따른 워크플로우 분기 (cumulative / part_validation / drop_weight_impact)
- 일반(cumulative) 모드에서는 `CumulativeDesigner` 를 통해 `runner_config.json` 생성
- 출력 디렉터리(`output/`)와 `slurm_scripts/` 디렉터리 사전 생성 (NFS 전파 시간 확보 목적)
- 보조 스크립트(`rerun.sh`, `stop.sh`, `diagnose.sh`, `copy.sh`) 자동 생성

---

## 2. 입력 옵션 · 인자 (표)

| 인자 / 옵션 | 형식 | 필수 여부 | 기본값 | 설명 | 코드 근거 |
|---|---|---|---|---|---|
| `scenario` | 위치 인자 (positional) | 필수 | 없음 | `scenario.json` 파일 경로 | KooChainRun:68-71 |
| `-o`, `--output` | 옵션 (값 1개) | 선택 | `None` → scenario 와 같은 디렉터리의 `runner_config.json` | 출력 `runner_config.json` 경로 | KooChainRun:72-76 |

서브파서 등록:

```text
prepare_parser = subparsers.add_parser(
    'prepare',
    help='Generate runner configuration from scenario',
    description='Convert user-friendly scenario.json to detailed runner_config.json'
)
prepare_parser.add_argument(
    'scenario',
    help='Path to scenario.json file'
)
prepare_parser.add_argument(
    '-o', '--output',
    help='Output runner_config.json path (default: same directory as scenario)',
    default=None
)
```
(KooChainRun:63-76)

> 참고: `--output` 미지정 시 출력 경로는 `scenario_path.parent / "runner_config.json"` 로 결정된다 (KooChainRun:359-362).

---

## 3. 사용 예제

### 3-1. CLI 명령

`Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/scenario.json` 을 변환하는 가장 단순한 형태:

```bash
# scenario.json 과 같은 디렉터리에 runner_config.json 생성
KooChainRun prepare scenario.json

# 출력 경로 명시
KooChainRun prepare scenario.json -o /data/koopark/myrun/runner_config.json
```

실행 시 출력되는 안내 메시지(KooChainRun:364-368):

```text
================================================================================
KooChainRun - Prepare Configuration
================================================================================
Scenario: <절대경로>/scenario.json
Output:   <절대경로>/runner_config.json
```

### 3-2. 입력 scenario.json (cumulative 모드)

`Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/scenario.json` 발췌(실제 파일, 가공 없음):

```json
{
  "project_name": "Test_001_Full26_1Step",
  "environment": {
    "koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "mpi_path": "mpirun",
    "memory": "2G",
    "lsdyna_memory": "2000m",
    "apptainer_sif": "/opt/apptainers/SmartTwinPreprocessor.sif",
    "apptainer_bind": "/data:/data",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif",
    "apptainer_tmpdir": "/data/tmp",
    "nodes_per_job": 1,
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
      "scenario_name": "Full_26_Directions_Single_Drop",
      "template": "MinimumModel.k",
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
        "angle_mixing": {"strategy": "same_angle"}
      }
    }
  ]
}
```

### 3-3. 입력 scenario.json (drop_weight_impact 모드 — `mode` 키로 분기)

`Examples/drop_weight_impact/scenario.json` 발췌(실제 파일, 일부 주석 생략):

```json
{
  "project_name": "BallDropTest",
  "mode": "drop_weight_impact",
  "model_file": "../MinimumModel.k",
  "output_dir": "dwi_output",
  "simulation_params": {
    "tFinal": 0.001,
    "dt": 0.000001,
    "impactor": {
      "type": "Sphere",
      "radius": 5.0,
      "height": 100,
      "density": 7850,
      "youngs_modulus": 2.0e11,
      "poisson_ratio": 0.3
    },
    "locations": {
      "mode": "grid"
    }
  }
}
```

이 경우 `cmd_prepare` 는 `mode == "drop_weight_impact"` 를 감지하여 전용 워크플로우(`prepare_drop_weight_impact`)로 분기한다 (KooChainRun:383-386).

---

## 4. 동작 원리 (코드 근거)

`cmd_prepare(args)` 함수는 KooChainRun:347-414 에 정의되어 있으며, 디스패치는 KooChainRun:324-325 (`if args.command == 'prepare': cmd_prepare(args)`) 에서 이루어진다.

1. **경로 확정 및 존재 확인** — `scenario` 인자를 절대경로로 변환한다 (KooChainRun:352). 파일이 없으면 에러 메시지 출력 후 `sys.exit(1)` (KooChainRun:354-356).

2. **출력 경로 결정** — `--output` 이 주어지면 그 경로를, 아니면 `scenario_path.parent / "runner_config.json"` 을 사용한다 (KooChainRun:359-362).

3. **시나리오 로드** — `scenario.json` 을 UTF-8 로 읽어 `user_config` 딕셔너리로 적재한다 (KooChainRun:372-374).

4. **모드 분기** — `user_config["mode"]` 값에 따라 전용 워크플로우로 위임하고 즉시 `return` 한다.
   - `"part_validation"` → `Runner.PartValidationWorkflow.prepare_part_validation(...)` (KooChainRun:377-380; 함수 정의 PartValidationWorkflow.py:19)
   - `"drop_weight_impact"` → `Runner.DropWeightImpactWorkflow.prepare_drop_weight_impact(...)` (KooChainRun:383-386; 함수 정의 DropWeightImpactWorkflow.py:21)
   - `mode` 가 없거나 위 두 값이 아니면 일반(cumulative) 경로로 진행한다.

5. **cumulative 경로 — runner_config 생성** — `CumulativeDesigner(user_config, scenario_dir=...)` 를 생성하고 `parse_user_config()` 로 `RunnerConfig` 객체를 만든 뒤 `save_runner_config(...)` 로 `runner_config.json` 을 기록한다 (KooChainRun:389-393).
   - `parse_user_config` 는 `environment` 기본값(실행 파일 경로 등) 보정, `scenarios`/`simulation_params`/`postprocess` 파싱을 수행한다 (CumulativeDesigner.py:118-156).
   - `save_runner_config` 는 `CumulativeScenarioRunner` 가 기대하는 스키마(project / scenario / execution / environment / scenarios)로 출력한다 (CumulativeDesigner.py:667-676).

6. **출력 디렉터리 사전 생성** — 저장된 `runner_config.json` 을 다시 읽어 `project.output_dir` 을 얻고, 그 하위에 `slurm_scripts/` 를 미리 생성한다. 주석상 목적은 "NFS 전파 시간 확보" 이다 (KooChainRun:395-402).

7. **보조 스크립트 자동 생성** — `_generate_helper_scripts(script_dir, user_config)` 를 호출한다 (KooChainRun:407-408). 이 함수는 다음을 시나리오 디렉터리에 생성하고 실행 권한을 부여한다 (KooChainRun:417-433).
   - `rerun.sh` → `KooChainRun rerun "$SCRIPT_DIR"`
   - `stop.sh` → `KooChainRun stop` + `kill_dyna.sh`
   - `diagnose.sh` → `KooChainRun diagnose "$SCRIPT_DIR"`
   - 각 스크립트는 `scenario.json` 의 `environment.koochainrun_path` 를 읽어 실행기 경로를 결정한다 (KooChainRun:425-429).
   - 추가로 `copy.sh`(로컬 scratch → NFS Output 동기화)를 생성하며, scratch 베이스는 `environment.apptainer_tmpdir`(기본 `/opt/tmp`)에서 가져온다 (KooChainRun:435-451).

8. **예외 처리** — 위 과정에서 예외가 발생하면 에러 메시지와 traceback 을 출력하고 `sys.exit(1)` (KooChainRun:410-414).

---

## 5. 주의사항 · 한계

- **입력 파일 미존재 시 즉시 종료** — `scenario` 경로가 없으면 `❌ Error: Scenario file not found` 출력 후 종료 코드 1 로 종료한다 (KooChainRun:354-356).
- **모드별 출력 구조가 다름** — `mode` 가 `part_validation` 또는 `drop_weight_impact` 인 경우 본 함수의 일반 경로(CumulativeDesigner)는 실행되지 않고 전용 워크플로우로 위임되므로, 생성물 구조와 의미는 각 워크플로우 모듈을 따른다 (KooChainRun:377-386). 본 문서는 prepare 커맨드의 분기 동작까지만 다룬다.
- **보조 스크립트는 `koochainrun_path` 에 의존** — `rerun.sh`/`stop.sh`/`diagnose.sh` 헤더가 `scenario.json` 의 `environment.koochainrun_path` 키를 직접 파싱한다 (KooChainRun:428). 해당 키가 없으면 보조 스크립트 실행 시 실행기 경로를 찾지 못한다.
- **output_dir 미설정 시 디렉터리 사전 생성 생략** — `runner_config.json` 의 `project.output_dir` 이 비어 있으면 `slurm_scripts/` 사전 생성을 건너뛴다 (KooChainRun:398-402).
- **출력 경로 디렉터리 기준의 부수 효과** — 6단계의 `output/`·`slurm_scripts/` 사전 생성은 `runner_config.json` 내부 `project.output_dir` 값을 기준으로 하며, 7단계 보조 스크립트는 `scenario.json` 이 위치한 디렉터리(`scenario_path.parent`)에 생성된다 (KooChainRun:407). 두 경로가 다를 수 있음에 유의.

---

## 6. 개발 현황

**구현됨.**

근거:
- `prepare` 서브파서 및 인자(`scenario`, `-o/--output`)가 정의되어 있다 (KooChainRun:63-76).
- 디스패처가 `prepare` 를 `cmd_prepare` 로 연결한다 (KooChainRun:324-325).
- `cmd_prepare` 본문이 경로 처리, 모드 분기, runner_config 생성, 디렉터리/보조 스크립트 생성까지 완결적으로 구현되어 있다 (KooChainRun:347-414).
- 분기 대상 함수가 실제로 존재한다: `prepare_part_validation`(PartValidationWorkflow.py:19), `prepare_drop_weight_impact`(DropWeightImpactWorkflow.py:21).
- 의존 메서드 `parse_user_config`(CumulativeDesigner.py:118), `save_runner_config`(CumulativeDesigner.py:667) 가 존재한다.
- 실제 입력 예시 파일들이 저장소에 존재한다: `Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/scenario.json`, `Examples/drop_weight_impact/scenario.json`.
