# 파일 포맷 레퍼런스

## 1. 목적/개요

pyKooCAE의 누적 시뮬레이션 파이프라인은 사용자 입력(`scenario.json`)을 받아 실행 설정(`runner_config.json`)으로 변환하고, 실행 중 상태(`simulation_index.json`, `checkpoint.json`, `jobs.json`)를 기록하며, 해석 결과로 `dynain`과 후처리 리포트(`deep`/`sphere`/`impact` report)를 산출한다.

데이터 흐름 요약:

```
scenario.json  ──[CumulativeDesigner]──►  runner_config.json
runner_config.json  ──[CumulativeScenarioRunner]──►  simulation_index.json + checkpoint.json + (각 step) dynain
(Slurm 제출)  ──►  jobs.json
LS-DYNA d3plot  ──[koo_deep_report]──►  Run_*/report/   ──[koo_sphere/impact_report]──►  sphere_report.{html,json} / impact_report.{html,json}
```

각 파일의 역할/위치/생성 주체:

| 파일 | 역할 | 생성 위치 | 생성 주체 (file:line) |
|------|------|-----------|----------------------|
| `scenario.json` | 사용자 입력(시나리오 정의). 파이프라인 진입점 | 사용자가 작성 (보통 `base_dir`) | 사용자. `CumulativeDesigner.parse_user_config()` 가 읽음 — `CumulativeDesigner.py:117-156` |
| `runner_config.json` | Executor가 읽는 실행 설정 | `-o` 지정 경로 (보통 test_dir) | `CumulativeDesigner.save_runner_config()` — `CumulativeDesigner.py:667, 866-869` |
| `simulation_index.json` | 전체 run 진행/결과 인덱스 | `{output_dir}/simulation_index.json` | `CumulativeScenarioRunner` — `CumulativeScenarioRunner.py:557-575, 577-594` |
| `checkpoint.json` | 재개용 진행 체크포인트 | `{output_dir}/checkpoint.json` (DOE별 `checkpoint_doe_NNN.json`) | `CumulativeScenarioRunner` — `CumulativeScenarioRunner.py:442-450, 452-473` |
| `jobs.json` | Slurm 작업 ID/상태 추적 | `{test_dir}/jobs.json` | submit 워크플로우(LargeScaleDOEManager). `JobManager` 가 갱신 — `JobManager.py:26, 48-67` |
| `dynain` | LS-DYNA 스프링백 산출(다음 step 누적 입력) | `{output_dir}/Run_*/Output/dynain` | LS-DYNA. Runner가 대기/소비 — `CumulativeScenarioRunner.py:343-362, 916, 1162-1163` |
| deep report | per-job 단일 시뮬 리포트 | `{run_dir}/report/` (+ `deep_report.sh`, `deep_report.log`) | `koo_deep_report` (KooD3plotReader). 스크립트 생성 — `PostprocessShellGenerator.py:57, 102-131` |
| sphere report | 전각도 DROP 통합 리포트 | `{output_dir}/sphere_report.{html,json}` | `koo_sphere_report`. 스크립트 생성 — `PostprocessShellGenerator.py:134, 176-177, 221-225` |
| impact report | 전위치 IMPACT 통합 리포트 | `{output_dir}/impact_report.{html,json}` | `koo_impact_report`. 스크립트 생성 — `PostprocessShellGenerator.py:231, 274-275, 290-294` |

> 단위계 관련 입력 필드(`density`, `youngs_modulus`, `height` 등)는 [단위계 (ton-mm-s)](unit_system.md) 문서를 따른다. 본 문서는 파일 구조 자체를 다룬다.

---

## 2. 입력 옵션·인자 (표)

### 2-1. scenario.json (사용자 입력)

최상위 키 (`CumulativeDesigner.py:113-156`, 실측 `Examples/scenario_examples/*.json`):

| 키 | 타입 | 설명 | 근거 |
|----|------|------|------|
| `project_name` | str | 프로젝트명. alias prefix가 됨 | `CumulativeDesigner.py:114` |
| `base_dir` | str | 산출물 루트 디렉토리 | `CumulativeDesigner.py:115` |
| `environment` | obj | 실행 환경(경로/리소스). 아래 2-2 참조 | `CumulativeDesigner.py:127` |
| `simulation_params` | obj | 물성/낙하/바닥판 등 공통 시뮬 파라미터 (없으면 생략) | `CumulativeDesigner.py:142` |
| `postprocess` | obj | 후처리 자동 실행 옵션 (없으면 생략). 아래 2-4 | `CumulativeDesigner.py:145` |
| `scenarios` | list | 시나리오 목록 (각각 `scenario_name`, `template`, `angle_source`/`position_source`, `cumulative`) | `CumulativeDesigner.py:135-138` |

각 `scenarios[]` 항목 키 (실측):
- DROP 계열: `scenario_name`, `template`, `angle_source`, `cumulative` (`drop_attitude_example.json`)
- IMPACT 계열: `scenario_name`, `template`, `position_source`, `cumulative` (`impact_example.json`)

> `template`(모델 .k 경로)은 scenario.json 위치 기준 상대경로 → 절대경로로 변환된다 (`CumulativeDesigner.py:169-175`).

### 2-2. environment (scenario.json 내부)

실행 파일 경로 기본값은 미지정 시 자동 보강된다:

| 키 | 기본값/동작 | 근거 |
|----|------------|------|
| `koomeshmodifier_path` | 미지정 시 `find_koomeshmodifier()` 자동 탐색 | `CumulativeDesigner.py:131-133` |
| `lsdyna_path` | 미지정 시 `/opt/lsdyna/bin/ls-dyna` | `CumulativeDesigner.py:134-135` |
| `timeout_per_step_seconds` | 기본 604800 | `CumulativeDesigner.py:819` |
| `timeout_koomeshmodifier_seconds` | 기본 604800 | `CumulativeDesigner.py:820` |
| `timeout_dynain_seconds` | 기본 604800 | `CumulativeDesigner.py:821` |

기타 `environment` 키(`lsdyna_apptainer_sif`, `apptainer_bind`, `ncpu`, `memory`, `time_limit` 등)는 변환 없이 그대로 `runner_config.environment`로 전달된다 (`CumulativeDesigner.py:825`).

### 2-3. CumulativeDesigner CLI 인자

| 인자 | 기본값 | 설명 | 근거 |
|------|--------|------|------|
| `-o`, `--output` | `runner_config.json` | 출력 runner_config.json 경로 | `CumulativeDesigner.py:916` |

### 2-4. postprocess (scenario.json 내부)

| 키 | 타입 | 설명 | 근거 |
|----|------|------|------|
| `enabled` | bool | 후처리 자동 실행 마스터 스위치 | `impact_cylinder_8pi.json:76`, `PostprocessShellGenerator.py:14` |
| `sif_path` | str | SmartTwinPostprocessor.sif 경로 | `impact_cylinder_8pi.json:77`, `PostprocessShellGenerator.py:62` |
| `auto_deep` | bool | per-job deep_report 자동 실행 | `impact_cylinder_8pi.json:78` |
| `auto_deep_mode` | str | `inline`(잡 안 실행, 기본) / `sbatch` | `CumulativeScenarioRunner.py:681-682, 711-714` |
| `auto_sphere` | bool | DROP 통합 sphere_report 자동 실행 | `PostprocessShellGenerator.py:14` |
| `auto_impact` | bool | IMPACT 통합 impact_report 자동 실행 | `impact_cylinder_8pi.json:81` |
| `delete_d3plot_after_deep` | bool | deep 성공 후 d3plot 삭제(디스크 절약, 기본 OFF) | `PostprocessShellGenerator.py:93`, `impact_cylinder_8pi.json:80` |
| `deep_extra_args` | list/str | `koo_deep_report` 인자 pass-through | `PostprocessShellGenerator.py:69, 86` |
| `sphere_extra_args` | list/str | `koo_sphere_report` 인자 pass-through | `PostprocessShellGenerator.py:161` |
| `impact_extra_args` | list/str | `koo_impact_report` 인자 pass-through | `PostprocessShellGenerator.py:262` |
| `yield_stress_mpa` | float (sphere) | 항복응력. 기본 350 | `PostprocessShellGenerator.py:141, 159` |
| `impact_yield_stress` | float (impact) | 있으면 `--yield-stress` 부착, 없으면 per-part *MAT 사용 | `PostprocessShellGenerator.py:244, 257-260` |
| `section_view_axes`/`section_view_fields`/`section_view_mode`/`ua_threads`/`sv_threads` | (deep) | deep_report 단면뷰/스레드 옵션 | `PostprocessShellGenerator.py:64-68, 77-81` |

> DROP→sphere, IMPACT→impact 분기는 `report_mode_from_runner_config()` 가 step mode로 판정한다 (둘 다 돌지 않음) — `PostprocessShellGenerator.py:300-327`.

---

## 3. 사용 예제

### 3-1. scenario.json (DROP, `Examples/scenario_examples/drop_attitude_example.json:6-46` 발췌)

```json
{
  "project_name": "Example_DropAttitude_Single",
  "base_dir": "/data/koopark/Example_DropAttitude",
  "environment": {
    "koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "ncpu": 1,
    "koochainrun_path": "/data/SmartTwinPreprocessor/bin/KooChainRun"
  },
  "simulation_params": {
    "height": 1500,
    "tFinal": 0.005,
    "dt": 1e-06,
    "density": 7.85e-09,
    "youngs_modulus": 2.0e5,
    "poisson_ratio": 0.3,
    "drop_surface": { }
  }
}
```

### 3-2. postprocess 블록 (IMPACT, `Examples/scenario_examples/impact_cylinder_8pi.json:75-82` 발췌)

```json
"postprocess": {
  "enabled": true,
  "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
  "auto_deep": true,
  "auto_deep_mode": "inline",
  "delete_d3plot_after_deep": true,
  "auto_impact": true
}
```

### 3-3. runner_config.json (CumulativeDesigner 출력, `Examples/.../Test_010_Sequential_Quick/runner_config.json` 발췌)

```json
{
  "project": {
    "name": "Test_010_Sequential_Quick",
    "model_file": ".../MinimumModel.k",
    "output_dir": ".../output",
    "index_file": ".../output/simulation_index.json"
  },
  "scenario": {
    "id": "Sequential_Quick_10_S001",
    "name": "Sequential_Quick_10",
    "type": "cumulative",
    "total_steps": 1,
    "doe_count": 10,
    "steps": [ { "step": 1, "mode": "DROP", "condition": "P0001", "params": {} } ],
    "doe_angles": { "1": { "1": { "angle_name": "P0001", "roll": 0.0, "pitch": -0.0, "yaw": 0.0 } } }
  },
  "execution": {
    "checkpoint_file": ".../output/checkpoint.json",
    "timeout_per_step_seconds": 604800,
    "retry_on_failure": true,
    "max_retries": 2
  }
}
```

### 3-4. simulation_index.json (`Examples/.../Test_008_Fibonacci_100_v2/output/simulation_index.json` 발췌)

```json
{
  "project": "Test_008_Fibonacci_100_v2",
  "created": "2026-02-15T13:15:18.832919",
  "scenarios": [{
    "id": "Fibonacci_Lattice_100_Directions_S001",
    "total_steps": 1,
    "doe_count": 100,
    "total_runs": 100,
    "status": "in_progress",
    "mode_sequence": ["DROP"],
    "runs": {
      "Test_008_Fibonacci_100_v2_CUM001_DOE001_S001_DROP_P0001": {
        "run_id": "20260215_131522_3180cd",
        "status": "failed",
        "folder": "Run_20260215_131522_3180cd",
        "mode": "DROP",
        "condition": "P0001",
        "error": "LS-DYNA failed"
      }
    }
  }]
}
```

### 3-5. checkpoint.json (실측 발췌)

```json
{
  "scenario_id": "Fibonacci_Lattice_100_Directions_S001",
  "current_doe": 1,
  "current_step": 1,
  "completed_runs": [],
  "last_updated": "2026-02-15T13:15:24.401423",
  "failure_count": 1
}
```

### 3-6. jobs.json (`Examples/.../Test_010_Sequential_Quick/jobs.json` 발췌)

```json
{
  "project_name": "Test_010_Sequential_Quick",
  "config_path": ".../runner_config.json",
  "submitted_at": "2026-04-04T13:24:00.598293",
  "doe_count": 10,
  "scratch_run": false,
  "batch_koomeshmodifier": false,
  "jobs": {
    "1": {
      "job_id": "3127",
      "job_name": "Test_010_Sequential_Quick_SEQ000",
      "status": "submitted",
      "submitted_at": "2026-04-04T13:24:00.615640",
      "script_path": ".../output/slurm_scripts/run_seq_000.sh",
      "sequential_slot": 0
    }
  }
}
```

---

## 4. 동작 원리 (주요 필드 + 코드 근거)

### 4-1. runner_config.json

`save_runner_config()` 가 `scenario.json`을 4개 호환 섹션 + 원본 시나리오로 직렬화한다 (`CumulativeDesigner.py:794-867`):

| 섹션.필드 | 설명 | 근거 |
|-----------|------|------|
| `project.name` / `.model_file` / `.output_dir` / `.index_file` | 프로젝트 메타 + 인덱스 파일 경로 | `CumulativeDesigner.py:796-801` |
| `scenario.id` / `.name` / `.type` / `.total_steps` / `.doe_count` / `.steps` | 시나리오 정의. `type`은 `"cumulative"` 고정 | `CumulativeDesigner.py:802-808` |
| `scenario.doe_angles` | DROP DOE별 step별 `{angle_name, roll, pitch, yaw}` | `CumulativeDesigner.py:809`, 실측 runner_config |
| `scenario.doe_positions` | IMPACT DOE별 위치(있을 때만) | `CumulativeDesigner.py:810` |
| `scenario.doe_vibrations` | VIBRATION DOE 메타(있을 때만) | `CumulativeDesigner.py:811-813` |
| `scenario.batch_koomeshmodifier` | 1-step 일괄 생성 옵션 | `CumulativeDesigner.py:814-815` |
| `execution.checkpoint_file` / `.timeout_*` / `.retry_on_failure` / `.max_retries` | 실행 제어. `retry_on_failure=true`, `max_retries=2` 하드코딩 | `CumulativeDesigner.py:817-824` |
| `environment` | scenario.json environment 그대로 | `CumulativeDesigner.py:825` |
| `simulation_params` / `postprocess` | 있으면 그대로 추가 | `CumulativeDesigner.py:827-829` |
| `project_name` / `base_dir` / `scenarios` | LargeScaleDOEManager 등 타 Runner 호환용 원본 보존 | `CumulativeDesigner.py:830-863` |
| `scenarios[].steps[].{template, mode, angle, input_file, output_dir, dynain_source, doe_index}` | 원본 step 정의. `dynain_source`는 이전 step의 `Step00N/dynain` 상대경로(첫 step은 null) | `CumulativeDesigner.py:846-861`, 실측 runner_config |

> runner_config.json은 신/구 두 포맷이 존재한다. CumulativeDesigner 출력은 `project`/`scenario`/`execution` 섹션을 갖는 신포맷이고(`:794-834`), 일부 예제에는 `project_name`/`environment`/`scenarios`만 있는 구포맷도 남아 있다(`Examples/HWWarrantyDropTest/Tests/Test_001_*` 등). 동일 파일에 두 형태가 공존하므로 양쪽 호환된다.

### 4-2. simulation_index.json

- 초기화: `{project, created, scenarios:[{id, name, type, total_steps, doe_count, total_runs, status, mode_sequence, runs:{}}]}` — `CumulativeScenarioRunner.py:557-575`. `total_runs = doe_count × total_steps` (`:570`), `mode_sequence`는 step mode 배열(`:559`).
- `runs[alias]` 항목은 step 실행 중/완료/실패 시 `_update_index()`로 갱신된다 — `CumulativeScenarioRunner.py:606-643`.
  - running 진입: `{run_id, status:"running", folder:"Run_<id>", mode, condition, started_at, prev}` — `CumulativeScenarioRunner.py:933-939`
  - 완료: `{..., status:"completed", completed_at, prev}` — `CumulativeScenarioRunner.py:1118-1126`
  - 실패: `{..., status:"failed", error}` — `CumulativeScenarioRunner.py:941-946, 953-957`
- alias 키 형식: `{project}_CUM{total_steps:03d}_DOE{doe:03d}_S{step:03d}_{mode}_{condition}` — `CumulativeScenarioRunner.py:651-655`.
- `status` 집계(completed/partial_failed/in_progress)는 runs의 상태 카운트로 산정 — `CumulativeScenarioRunner.py:870-883`.
- 저장은 atomic write(임시파일→rename) + `.bak` 백업 + 파일 잠금(flock) — `CumulativeScenarioRunner.py:577-601`. 동시 쓰기 lost-update 방지를 위해 lock 내 re-read 후 머지 — `:607-643`.

### 4-3. checkpoint.json

- 필드: `{scenario_id, current_doe, current_step, completed_runs, last_updated, failure_count}` — `CumulativeScenarioRunner.py:443-450`.
- `_save_checkpoint(doe, step)`가 `current_doe`/`current_step`/`last_updated` 갱신 후 atomic write + `.bak` — `CumulativeScenarioRunner.py:452-473`.
- 완료된 step alias는 `completed_runs`에 append — `CumulativeScenarioRunner.py:1129`.
- `--doe N` 모드에서는 동시 write 경합을 피하려 DOE별 `checkpoint_doe_{N:03d}.json`을 따로 쓴다 — `CumulativeScenarioRunner.py:390-396`.
- 손상 시 `.bak` 복구, 없으면 초기화 — `CumulativeScenarioRunner.py:433-450`.

### 4-4. jobs.json

- 최상위: `{project_name, config_path, submitted_at, doe_count, scratch_run, batch_koomeshmodifier, jobs:{}}` (실측). `jobs[doe_key]`는 DOE 인덱스(문자열) → 작업 정보.
- `jobs[].{job_id, job_name, status, submitted_at, script_path, sequential_slot}` (실측). 순차 슬롯(`sequential_slot`)이 같은 여러 DOE가 동일 `job_id`를 공유할 수 있다(실측 Test_010).
- `JobManager`가 갱신: cancel 시 `status:"cancelled"` (`JobManager.py:273`), rerun 시 `{job_id, job_name, status:"resubmitted", submitted_at, script_path, prev_job_id}` 재기록 (`JobManager.py:441-448`).
- 로드/저장은 atomic write + `.bak` 복구 — `JobManager.py:29-67`.
- Slurm 상태는 `sacct`(실패 시 `squeue` fallback)로 조회해 `slurm_state`로 합산 표시 — `JobManager.py:76-103`. (이 `slurm_state`는 조회 시점 계산값으로 보통 파일에 영구 저장되지 않음)

> jobs.json의 최상위 메타(`project_name`/`config_path`/`scratch_run`/`sequential_slot`)는 submit 워크플로우(LargeScaleDOEManager)가 작성한다 — `LargeScaleDOEManager.py`에서 `scratch_run`/`sequential_slot` 사용 확인. JobManager는 읽기/부분 갱신만 한다(`JobManager.py:26, 245, 441`).

### 4-5. dynain

- LS-DYNA가 각 step 종료 시 `Run_*/Output/dynain`에 생성하는 표준 산출물(스프링백/상태전이 deck). Runner는 생성을 폴링 대기한다 — `CumulativeScenarioRunner.py:343-362` (`wait_for_dynain`, 파일 크기 안정화 확인 `:351-354`).
- 다음 step은 직전 step의 `dynain`을 `DYNAIN_TO_INITIAL` 변환(KooMeshModifier)으로 `DropSet_dti.k`에 흡수해 누적 입력으로 쓴다 — `CumulativeScenarioRunner.py:1109-1115`(마지막 step 제외 변환), `:1160-1168`(다음 step 모델로 `DropSet_dti.k` 사용, 없으면 원본 fallback).
- runner_config의 `scenarios[].steps[].dynain_source`는 step간 상대경로(`Step00N/dynain`)로 의존을 명시 — `CumulativeDesigner.py:858`.
- 타임아웃: `execution.timeout_dynain_seconds`(기본 604800) — `CumulativeScenarioRunner.py:1093-1094`.

> dynain 자체는 LS-DYNA가 정의하는 포맷이며 pyKooCAE가 만들지 않는다. 내부 카드 구조는 LS-DYNA 매뉴얼 소관(확인 필요: 본 코드베이스에서 dynain 카드를 직접 파싱/생성하는 부분은 발견되지 않음 — Runner는 존재/크기만 확인).

### 4-6. deep / sphere / impact report

세 리포트는 모두 SmartTwinPostprocessor.sif 안의 KooD3plotReader 모듈(`koo_deep_report`/`koo_sphere_report`/`koo_impact_report`)을 호출하는 자동 생성 셸 스크립트로 실행된다. pyKooCAE는 스크립트만 생성하고 리포트 본문은 외부 모듈이 만든다.

| 리포트 | 실행 모듈 | 산출물 | 근거 |
|--------|-----------|--------|------|
| deep (per-job) | `koo_deep_report "$RUN_DIR" -o "$RUN_DIR/report"` | `Run_*/report/` (내부 `result.json` 또는 `analysis_result.json` + `motion/` 등) | `PostprocessShellGenerator.py:102-131`, symlink 시 결과파일 확인 `:202` |
| sphere (DROP 통합) | `koo_sphere_report --test-dir "$TEST_DIR" -o ... --json ...` | `{output_dir}/sphere_report.html` + `sphere_report.json` (+ `sphere_normal_term.txt`) | `PostprocessShellGenerator.py:176-178, 221-225` |
| impact (IMPACT 통합) | `koo_impact_report --test-dir "$TEST_DIR" --format html json ...` | `{output_dir}/impact_report.html` + `impact_report.json` | `PostprocessShellGenerator.py:274-275, 290-294` |

동작 세부:
- deep_report.sh는 run_dir에 항상 생성되고, `postprocess.enabled && auto_deep`일 때만 자동 실행(`inline` 또는 `sbatch`) — `CumulativeScenarioRunner.py:678-714`.
- sphere_report는 사전에 normal-termination 필터(`Run_*/Output/{mes0000,d3hsp,*.log}` grep) + deep_report 완료(result.json 존재) Run만 `analysis_results/`로 symlink한 뒤 집계 — `PostprocessShellGenerator.py:185-209`. 정상 deep 완료 0개면 skip — `:211-217`.
- impact_report는 symlink dance 없이 로더가 각 Run을 직접 처리(깨진 Run 자체 skip), `koo_impact_report` 미포함 구버전 SIF면 경고 후 soft-skip — `PostprocessShellGenerator.py:234-238, 282-286`.

> 리포트 `*.html`/`*.json`의 내부 스키마(키 구조)는 KooD3plotReader(외부 패키지) 소관이라 본 코드베이스에서 확정할 수 없다. pyKooCAE 측 근거로 확인되는 것은 출력 파일명/위치/존재 여부(`result.json`/`analysis_result.json` 키 이름 사용 — `:202`)까지다 (그 이상은 확인 필요).

---

## 5. 주의사항·한계

- **scenario.json vs runner_config.json 혼동 금지**: 사용자는 `scenario.json`만 작성하고, `runner_config.json`은 CumulativeDesigner가 생성하는 파생물이다. runner_config를 직접 손대면 다음 변환에서 덮어쓰여진다.
- **runner_config.json 신/구 포맷 공존**: `project`/`scenario`/`execution` 섹션(신) 외에 `project_name`/`scenarios`만 있는 구포맷도 예제에 남아 있다. Executor 종류에 따라 읽는 키가 다르므로 어느 포맷인지 확인할 것.
- **상태 파일은 동시쓰기 보호되지만 NFS 의존**: simulation_index/checkpoint/jobs는 flock + atomic write + `.bak`로 보호된다(`CumulativeScenarioRunner.py:577-643`, `JobManager.py:48-67`). 단 컴퓨트 노드가 보는 NFS 경로에 있어야 한다(전역 메모리: 테스트 디렉토리는 항상 `/data/...`, `/tmp` 금지).
- **`--doe N` 모드 checkpoint 분리**: DOE 병렬 실행 시 `checkpoint_doe_NNN.json`이 별도로 생긴다(`:390-396`). 통합 checkpoint.json만 보고 진행률을 판단하면 안 된다.
- **`delete_d3plot_after_deep=true`는 복구 불가**: deep_report 성공 후 d3plot 영구 삭제(`PostprocessShellGenerator.py:93-99`). 첫 운영 전 1~2잡으로 검증 권장(`impact_cylinder_8pi.json:74` 주석).
- **dynain 미생성 시 fallback의 함정**: `DropSet_dti.k`가 없으면 원본 모델로 fallback해 누적이 끊긴 채 진행될 수 있다(결과 부정확) — `CumulativeScenarioRunner.py:1164-1168`. 경고만 뜨고 멈추지 않으므로 로그 확인 필요.
- **리포트는 SIF 버전 의존**: 구버전 SIF는 `koo_impact_report`가 없어 impact_report가 soft-skip된다(`PostprocessShellGenerator.py:282-286`). 리포트 파일 부재가 곧 해석 실패는 아니다.
- **dynain·리포트 내부 포맷은 외부 소관**: dynain은 LS-DYNA, report html/json은 KooD3plotReader가 정의한다. 본 문서는 pyKooCAE가 직접 생성/소비하는 경로·존재까지만 보증한다.

---

## 6. 개발 현황

**구현됨** (pyKooCAE가 직접 생성·소비하는 파일: scenario.json 파싱, runner_config.json/simulation_index.json/checkpoint.json/jobs.json 생성·갱신, dynain 대기·소비, 3종 report 셸 스크립트 생성·실행).

근거:
- runner_config.json 생성: `CumulativeDesigner.py:667-869` (+ 실측 `Examples/.../runner_config.json`).
- simulation_index.json 생성/갱신/잠금: `CumulativeScenarioRunner.py:557-643, 933-1126` (+ 실측 `.../Test_008.../output/simulation_index.json`).
- checkpoint.json: `CumulativeScenarioRunner.py:420-473` (+ 실측 checkpoint).
- jobs.json 갱신: `JobManager.py:29-67, 242-457` (+ 실측 `.../Test_010.../jobs.json`).
- dynain 대기/소비: `CumulativeScenarioRunner.py:343-362, 1092-1115, 1160-1168`.
- report 스크립트 생성: `PostprocessShellGenerator.py:57-327`; 자동 실행 wiring `CumulativeScenarioRunner.py:678-714`.

**부분구현/외부 의존 (확인 필요)**:
- jobs.json **최상위 메타 작성 주체**: `JobManager`는 읽기/부분 갱신만 하고, `project_name`/`config_path`/`scratch_run`/`sequential_slot`을 처음 쓰는 곳은 submit 워크플로우(LargeScaleDOEManager로 추정 — `scratch_run`/`sequential_slot` 사용 확인). 정확한 생성 라인은 본 조사 범위에서 단정하지 못함.
- **dynain 카드 구조** 및 **report html/json 내부 스키마**: 각각 LS-DYNA / KooD3plotReader(외부 패키지) 소관으로, 본 코드베이스에서는 파일 존재/경로/주요 결과파일명(`result.json`/`analysis_result.json`)까지만 확인 가능 (그 이상은 확인 필요).
