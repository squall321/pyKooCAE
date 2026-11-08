# scenario.json 레퍼런스

## 1. 목적 / 개요

`scenario.json` 은 사용자가 작성하는 친화적 시나리오 정의 파일이다. `KooChainRun prepare scenario.json` 이 이 파일을 읽어 Runner 가 소비하는 상세 설정(`runner_config.json`)으로 변환한다.

`prepare` 단계는 최상위 `mode` 값에 따라 세 갈래로 분기한다 (KooChainRun:376-389).

- `mode` 미지정(기본) → **cumulative** 포맷. `CumulativeDesigner` 가 `cumulative.mode_sequence` 에 따라 DROP / IMPACT / VIBRATION / THERM 시나리오를 처리한다 (KooChainRun:389).
- `mode == "part_validation"` → `PartValidationWorkflow.prepare_part_validation` (KooChainRun:377-378).
- `mode == "drop_weight_impact"` → `DropWeightImpactWorkflow.prepare_drop_weight_impact` (KooChainRun:383-385). 이는 **별도 스키마**(아래 7장)를 사용한다.

본 문서는 cumulative 포맷의 전체 스키마(최상위 키 + `cumulative.mode_sequence` 별 필드)를 정식 레퍼런스로 다루고, drop_weight_impact 포맷은 7장에서 보조로 정리한다.

cumulative 포맷의 최상위 키:

| 키 | 형식 | 필수 | 설명 | 코드 근거 |
|---|---|---|---|---|
| `project_name` | string | 권장 | 프로젝트 이름 (기본 `"CumulativeProject"`) | CumulativeDesigner.py:114 |
| `base_dir` | string | 권장 | 출력 기준 디렉터리 (기본 `os.getcwd()`) | CumulativeDesigner.py:115 |
| `environment` | object | 권장 | 실행 환경 (경로·Apptainer·라이선스·자원) | CumulativeDesigner.py:126 |
| `simulation_params` | object | 모드별 | 해석 파라미터 (DROP/IMPACT/THERM 공통·전용) | CumulativeDesigner.py:144 |
| `postprocess` | object | 선택 | 후처리 자동 실행 옵션 (KooD3plotReader 파이프라인) | CumulativeDesigner.py:147 |
| `scenarios` | array | 필수 | 시나리오 목록 (각 항목 = 1 시나리오) | CumulativeDesigner.py:136-141 |

단위계 주의: 예제 파일 주석상 솔버 단위계는 `[tonne, mm, s, MPa]` (ton-mm-s) 이며, KooMeshModifier 는 사용자 입력값을 변환 없이 그대로 deck 에 기록하므로 `scenario.json` 입력 단위를 model.k(deck) 단위계와 반드시 일치시켜야 한다 (Examples/scenario_examples/drop_attitude_example.json:2).

---

## 2. 입력 옵션 · 인자 (표)

### 2-1. `environment` (실행 환경)

`environment` 객체는 그대로 `runner_config.json` 에 복사되어 (CumulativeDesigner.py:825) `ApptainerWrapper` 와 LS-DYNA 실행부, `SlurmSubmitter` 가 소비한다.

| 필드 | 형식 | 기본값 | 소비처 / 의미 | 코드 근거 |
|---|---|---|---|---|
| `koomeshmodifier_path` | string | 자동 탐색(`find_koomeshmodifier()`) | KooMeshModifier 실행 파일 경로 | CumulativeDesigner.py:129-131 / CumulativeScenarioRunner.py:387 |
| `lsdyna_path` | string | `/opt/lsdyna/bin/ls-dyna` (Designer) / `/opt/lsdyna/lsdyna` (Runner) | LS-DYNA 솔버 경로 | CumulativeDesigner.py:132-133 / CumulativeScenarioRunner.py:226 |
| `koochainrun_path` | string | — | KooChainRun 자기 자신 경로 (보조 스크립트 생성용) | 예제 공통(drop_attitude_example.json:28) |
| `mpi_path` | string | `mpirun` | MPI 런처 경로 | CumulativeScenarioRunner.py:227 |
| `ncpu` | int | 32(Submitter) | 잡당 CPU(=OMP/MKL 스레드, `-np`) | SlurmSubmitter.py:51, 197, 205-206 |
| `memory` | string | `64G`(Submitter) | Slurm `--mem` (헤드/잡 메모리) | SlurmSubmitter.py:52, 198 |
| `lsdyna_memory` | string | `2000m` (없으면 `memory`) | LS-DYNA `memory=` 값 | CumulativeScenarioRunner.py:229 |
| `time_limit` | string | — | 예제상 `"01:00:00"`. Submitter 자체 계산값과 별개(주의) | 예제(drop_attitude_example.json:29) / SlurmSubmitter.py:54 |
| `partition` | string | `normal` | Slurm 파티션 (CLI `--partition` override 가능) | SlurmSubmitter.py:47, 194 |
| `apptainer_sif` | string | `None` | KooMeshModifier(전처리)용 SIF. 미지정 시 비-Apptainer 직접 실행 | CumulativeScenarioRunner.py:115, 135 |
| `apptainer_bind` | string | `/data:/data` | 전처리 SIF 바인드 마운트 | CumulativeScenarioRunner.py:116, 136 |
| `apptainer_env` | object | `{}` | 전처리 SIF 컨테이너 내부 env | CumulativeScenarioRunner.py:120, 137 |
| `lsdyna_apptainer_sif` | string | `None` | LS-DYNA용 SIF | CumulativeScenarioRunner.py:117, 131 |
| `lsdyna_apptainer_bind` | string | `/data:/data` | LS-DYNA SIF 바인드 마운트 | CumulativeScenarioRunner.py:118, 132 |
| `lsdyna_apptainer_env` | object | `{}` | LS-DYNA SIF 컨테이너 내부 env (라이선스 등) | CumulativeScenarioRunner.py:119, 133 |
| `apptainer_tmpdir` | string | `/opt/tmp` | APPTAINER_TMPDIR 기준 경로. 잡별 `apptainer_job_<id>` 하위 생성 | CumulativeScenarioRunner.py:124-126, 145 |
| `nodes_per_job` | int | 1 | 잡당 노드 수 | CumulativeScenarioRunner.py:121 |
| `timeout_per_step_seconds` | int | 604800 | step wall-clock 타임아웃(초). **발산(NaN·dt붕괴) 케이스의 최종 안전망** — 기본 7일은 사실상 무한이라 발산 시나리오는 반드시 짧게(예 낙하 1스텝 실 walltime의 2~3배) 설정 권장. 초과 시 kill+failed 후 러너가 다음 스텝 진행 | CumulativeDesigner.py:819 |
| `timeout_koomeshmodifier_seconds` | int | 604800 | KooMeshModifier 타임아웃 | CumulativeDesigner.py:820 |
| `timeout_dynain_seconds` | int | 604800 | dynain 생성 타임아웃 | CumulativeDesigner.py:821 |
| `schedule` | bool / object | `true` | v134 — 사전 해석 ENDTIM 표가 있으면 DOE 실행 순서(긴 것부터)·`--sequential` 칸 수를 정한다. 아래 절 | Runner/DoeSchedule.py |

#### `environment.schedule` (v134 — DOE 실행 순서·칸 수)

사전 해석(`simulation_params.endtime_presim` 또는 `angle_source.impact_conditions`)이 각도별 ENDTIM 표(`scenario.doe_endtim`)를 만들면 submit 이 다음처럼 한다. 표가 없거나 `"schedule": false`(또는 `{"enabled": false}`)면 예전과 같다(바이트 동일). DOE 번호·표·Run 이름은 바꾸지 않고 제출 순서와 칸 배정만 바꾼다.

- **비용(초).** DOE 마다 `overhead_seconds + seconds_per_ms × Σ_스텝(ENDTIM + DR 켠 둘째 스텝부터 tFinal)` 이다. 표에 없는 스텝은 tFinal 이고, 표 메타 `time_unit` 으로 ms 로 바꾼다. 가정값이라 '보정 안 됨' 이다.
- **기본 제출.** 비용이 큰 DOE 부터 sbatch 한다. 노드당 1잡(`exclusive`)이라 빈 노드를 Slurm 이 차례로 채운다. 피보나치 각도는 이미 길고 짧은 것이 섞여 있어 효과가 작다(2만 방향 0~0.5%). 긴 잡이 끝 무렵에 몰리는 경우를 막는다.
- **`--sequential`.** 칸 수 = 무릎 대수(상한 안에서 완료 시각이 `(1 + knee_tolerance)`·상한일 때 완료 이하가 되는 가장 작은 칸 수)다. 상한은 `--nodes`·`licenses ÷ licenses_per_job`·`max_concurrent`·DOE 수 가운데 가장 작은 값이다. 긴 것부터 가장 덜 찬 칸에 넣는다. 라운드로빈보다 2만 방향 칸 100 에서 4%, 100 방향 칸 10~50 에서 19~38% 짧았다.
- **rerun.** 같은 순서이고, `--sequential` rerun 도 같은 칸 배정이다.
- **기록.** `slurm_scripts/schedule.json` 에 비용·순서·칸·상한·무릎·대수별 예상 완료 시각·가정을 남긴다. prepare 는 표가 있으면 미리보기 한 줄을 찍는다.
- **D2R.** `drop_surface.deformable_to_rigid` 로 카드가 실제로 생기면 비용은 ENDTIM 비례 그대로 두고 'D2R 켬(보정 안 됨)' 만 적는다. KCR D2R 은 비행 중 강체·접촉 중 변형체라 실제는 더 짧을 수 있다.
- impact_conditions 의 심각도 순서·`progressive` 피보나치 순서는 켜져 있으면 덮어쓴다. 그 순서가 필요하면 끈다.

| 키 | 기본값 | 뜻 |
|---|---|---|
| `enabled` | `true` | `false` 면 예전 동작 |
| `licenses` | `null` | LS-DYNA 동시 라이선스 수. 칸 상한 = `licenses ÷ licenses_per_job` |
| `licenses_per_job` | `1` | 잡 하나가 쓰는 라이선스 수 |
| `max_concurrent` | `null` | 그 밖의 동시 실행 상한 |
| `overhead_seconds` | `300` | 잡당 고정비(KMM·Apptainer 기동·stagger 평균·리포트) |
| `seconds_per_ms` | `20` | 해석 1 ms 당 시간. 보정 안 됨 — Test_005(1 MPP)는 226 s/ms 였다 |
| `knee_tolerance` | `0.05` | 무릎 판정 여유 |

#### 라이선스 관련 env (`lsdyna_apptainer_env` 내부)

LS-DYNA 라이선스는 SIF 컨테이너 내부 환경변수로 전달된다. 예제에서 다음 키가 사용된다.

| env 키 | 예제값 | 의미 | 코드 근거 |
|---|---|---|---|
| `LSTC_FILE` | `/opt/ls-dyna_license/LSTC_FILE` | 라이선스 파일 경로 | 예제(impact_example.json:22) |
| `LSTC_LICENSE_SERVER` | `192.168.122.1` / `10.228.132.74` | 라이선스 서버 IP (헤드노드 IP — `localhost` 금지) | 예제(impact_example.json:23) |
| `FI_PROVIDER` | `tcp` | OpenMPI/libfabric 프로바이더 | 예제(impact_example.json:24) |
| `I_MPI_FABRICS` | `ofi` | MPI fabric | 예제(impact_example.json:25) |
| `LD_LIBRARY_PATH` | `/opt/openmpi/lib` | 컨테이너 내 라이브러리 경로 | 예제(impact_example.json:26) |

> 주의: `lsdyna_apptainer_env` 의 키/값은 코드에서 enum 검증 없이 `env_vars` 로 그대로 Apptainer 에 전달된다 (CumulativeScenarioRunner.py:133). 위 키 목록은 예제 파일에서 발췌한 것으로, 코드가 강제하는 고정 스키마는 아니다.

### 2-2. `scenarios[]` 공통 필드

| 필드 | 형식 | 기본값 | 설명 | 코드 근거 |
|---|---|---|---|---|
| `scenario_name` | string | `"UnnamedScenario"` | 시나리오 이름 (`scenario_id = <name>_S<steps>`) | CumulativeDesigner.py:168, 250/401/494 |
| `template` | string | `""` | 입력 모델 `.k` 경로 (scenario.json 기준 상대경로 → 절대경로 변환). 첫 시나리오 값만 사용 | CumulativeDesigner.py:171-177 |
| `cumulative` | object | `{}` | 누적 설정 (아래) | CumulativeDesigner.py:180 |
| `angle_source` | object | (DROP 전용) | 낙하 자세 각도 소스 | CumulativeDesigner.py:266 |
| `tolerance` | object | (DROP 선택) | 각도 공차 DOE | CumulativeDesigner.py:270-273 |
| `position_source` | object | (IMPACT 전용) | 충격 위치 소스 | CumulativeDesigner.py:366 |
| `vibration_source` | object | (VIBRATION 전용) | 진동 가진 소스 | CumulativeDesigner.py:446 |
| `thermal_conditions` | array | (THERM 선택) | 열 조건 리스트(= DOE 수). 없으면 단일 DOE `"THERM"` | CumulativeDesigner.py:225-227 |
| `batch_koomeshmodifier` | bool | `false` | 1-step 시나리오에서 헤드노드 일괄 전처리 | CumulativeDesigner.py:655, 815 |

### 2-3. `cumulative` 서브블록

| 필드 | 형식 | 기본값 | 설명 | 코드 근거 |
|---|---|---|---|---|
| `num_steps` | int | 1 | 누적 step 수 | CumulativeDesigner.py:181 |
| `mode_sequence` | array of string | `["DROP"] * num_steps` | step별 모드. `DROP`/`IMPACT`/`VIB`/`VIBRATION`/`THERM`/`REMAP`. 부족하면 마지막 모드로 채움 | CumulativeDesigner.py:610-625 |
| `base_angle_index` | int | 0 | (DROP) 믹싱 기준 각도 인덱스 | CumulativeDesigner.py:280 |
| `angle_mixing` | object | `{}` | (DROP) 누적 step 간 각도 조합 전략 | CumulativeDesigner.py:279, 627-642 |
| `step_params` | object | `{}` | (REMAP 등 러너 전용 스텝) step 번호(문자열 키)→params. 예 `{"2": {"op":"matdb","config":{...}}}`. 미지정 스텝은 `{}` | CumulativeDesigner.py:697-709 |

`mode_sequence` 값 → 처리 분기 (CumulativeDesigner.py:185-211):

- `VIBRATION` 또는 `VIB` 가 포함되면 → `_process_vibration_scenario`
- `THERM` 포함 → `_process_thermal_scenario`
- `IMPACT` 포함 → `_process_impact_scenario`
- 그 외 → `_process_drop_scenario` (DROP)

`SimulationMode` enum 정의: `DROP`, `IMPACT`, `THERM`, `VIB`, `VIBRATION`, `REMAP` (TemplateManager.py:30-37). `VIBRATION` 은 long alias 로 `VIB` 와 별개 멤버이며 둘 다 진동 분기로 처리된다 (CumulativeDesigner.py:192-194).

**REMAP (KooRemapper 변환 스텝)**: LS-DYNA 를 실행하지 않는 러너 전용 스텝. 전용 `_process` 분기가 없고, 함께 쓰인 모드(보통 DROP)의 프로세서를 그대로 타고 지나간다(각도·템플릿은 러너가 REMAP 에서 무시). 실행 파라미터는 `cumulative.step_params["<step번호>"]` 로 전달한다.

- `op` (필수): KooRemapper 서브커맨드(예 `matdb`, `map`). 누락 시 러너가 `params.op missing` 으로 graceful failed.
- `config` (선택): YAML ops 설정 객체. 러너가 `model`/`output`(=`Remap_dti.k`) 을 자동 주입하므로 사용자는 넣지 않는다. `matdb` 는 `database` 미지정 시 기본 DB 사용.
- `argv` (선택, `config` 없을 때만): positional 인자. 입력=`input.k`, 출력은 반드시 `*_dti.k` 로 직접 명시해야 다음 스텝이 이어받는다.
- 예: `["DROP","REMAP","DROP"]` → step1 낙하 → step2 REMAP(dti 재작성) → step3 누적낙하. 입력/출력 dti 핸드오프는 러너의 `*_dti.k` glob 이 담당한다.
- ⚠️ REMAP-only 시퀀스(예 `["REMAP"]`)는 DROP 프로세서를 경유해 `angle_source` 기본값(cuboid 26방향)만큼 DOE 가 생성된다. 단일 변환만 원하면 DROP 과 혼합하거나 `angle_source` 를 단일 방향으로 지정한다.

### 2-4. DROP 모드 필드

#### `angle_source` (CumulativeDesigner.py:503-569)

| `source_type` | 서브 객체 | 주요 필드 (기본값) | 코드 근거 |
|---|---|---|---|
| `cuboid_geometry`(기본) | `cuboid_geometry` | `include_faces`(true), `include_edges`(true), `include_corners`(true) | CumulativeDesigner.py:508-517 |
| `fibonacci_lattice` | `fibonacci_lattice` | `num_points` 또는 별칭 `num_directions`(26) | CumulativeDesigner.py:519-528 |
| `pitching_sweep` | `pitching_sweep` | `pitch_min`(-90), `pitch_max`(90), `pitch_step`(10), `roll_fixed`(0), `yaw_fixed`(0) | CumulativeDesigner.py:530-541 |
| `rolling_sweep` | `rolling_sweep` | `roll_min`(-180), `roll_max`(170), `roll_step`(10), `pitch_fixed`(0), `yaw_fixed`(0) | CumulativeDesigner.py:543-554 |
| `case_txt_file` | `case_txt_file` | `file_path`, `selected_indices` | CumulativeDesigner.py:556-564 |
| `impact_conditions` | `impact_conditions` | `num_directions`(20000), `count`(100), `impacts`([1,2]), `severity_fraction`(0.5), `table` 등 — 아래 | Runner/ImpactConditions.py |

(enum: AngleSourceParser.py:23-29. `impact_conditions` 는 enum 이 아니라 CumulativeDesigner 가 따로 처리한다)

#### `angle_source.impact_conditions` — 충돌 직전 상태에서 고른 대표 충격 조건 DOE (Runner/ImpactConditions.py)

수만 각도 낙하의 1·2차 충돌마다 자세·선속도·각속도를 강체 사전 해석으로 뽑고, 그 가운데 대표 몇 개만 FEM 초기 조건으로 짧게 돌린다. 각 대표가 "어느 낙하 각도의 몇 차 충돌" 을 맡는지는 메타데이터로 남기고, 결과는 `harvest --impact-map` 으로 원래 각도에 되돌려 붙인다.

```json
"angle_source": {"source_type": "impact_conditions",
  "impact_conditions": {"num_directions": 20000, "restitution": [0.1, 0.3, 0.5], "friction": 0.5, "gravity": true,
                        "margin_ms": 1.0, "workers": 8,
                        "count": 100, "impacts": [1, 2], "severity_fraction": 0.5, "severity_min_distance": 0.2,
                        "table": null}}
```

| 필드 | 기본값 | 의미 |
|---|---|---|
| `num_directions` | 20000 | 사전 해석 방향 수(실제 낙하 방향 균일 피보나치) |
| `restitution` / `friction` | [0.1, 0.3, 0.5] / 0.5 | 사전 해석 반발계수 목록 · 마찰계수 |
| `gravity` | true | 사전 해석 중력. 충격 조건은 실제 상태를 뽑으려고 켠다(종료 시간 표 `endtime_presim` 은 끔이 기본). 끄면(v133) 종료 시간 표와 같은 규칙으로 2차 묶음 뒤에도 이어 돌려 k ≥ 3 충돌 줄이 더 생긴다(k=1·2 줄과 `endtim_k` 는 같다) — `impacts` 에 3 이상을 넣으면 후보가 달라진다 |
| `margin_ms` / `workers` | 1.0 / 8 | 충돌 묶음 끝 뒤 여유 · 프로세스 수 |
| `exclude_parts` | [] | 쓸 수 없다(비어 있지 않으면 멈춘다) — FEM 의 KMM DROP_ATTITUDE 강체 회전 중심(기기 무게중심)이 그 파트를 빼지 못한다. 템플릿에서 지운다. 병진 SPC 가 파트 절점의 10% 이상인 파트(바닥판 등)와 병진이 묶인 `*MAT_RIGID` 파트는 양쪽(사전 해석·FEM 회전 중심) 모두 같은 규칙으로 자동으로 빠진다. 10% 미만이면 기기 파트로 넣고 `SPC_ON_DEVICE_PART` 경고를 남기며, 뺄 파트가 기기 파트와 절점을 나누면 KMM 이 종료 코드 1 로 멈춘다 |
| `presim_timeout_seconds` | 21600 | 사전 해석 KMM 시간 제한(초, 6 시간 — 러너 KMM 의 `timeout_koomeshmodifier_seconds` 와 따로). 넘으면 KMM 프로세스 묶음째 멈추고 prepare 가 멈춘다 |
| `count` | 100 | 대표 수 = DOE 수 |
| `impacts` | [1, 2] | 후보 충돌 차수 |
| `severity_fraction` | 0.5 | 심각도(J_over_mv0·vn_contact/v0) 상위로 고를 몫 |
| `severity_min_distance` | 0.2 | 심각도 몫의 비최대 억제 거리(특징 f 공간). 0.2 ≈ 자세 11° 또는 속도·각속도 0.2·v0 차이. 0 이면 끈다 |
| `table` | null | 이미 만든 `<base>_impacts.csv`(옆에 `<base>_rigidbody.json` — 그 `presim.params.exclude_parts` 가 `[]` 여야 하고 기록이 없으면 멈춘다). 주면 사전 해석을 건너뛴다(KMM 버전 확인은 한다 — 헤드 노드에서 그 KMM 이 돌아야 한다) |

동작은 다음과 같다.
1. prepare 가 템플릿에 KMM `RIGID_DROP_ENDTIME`(`Fibonacci,<num_directions>`, `PresimGravity`=gravity)을 돌린다. 방식은 `endtime_presim` 과 같다(표 줄을 읽을 KMM·apptainer 감싸기, 작업 폴더 `<output_dir>/impact_conditions/presim/` 를 KMM 둘째 인자로, 시간 제한 `presim_timeout_seconds`). 산출 `<base>_impacts.csv`(덱 단위)와 `<base>_rigidbody.json`(바운딩 박스)을 읽는다. 표(BOM 이 붙어도 된다)의 메타 `height`·`v0`·`gravity` 가 이 낙하·옵션과 다르면, 메타 `units` 가 mm-kg-ms·mm-g-ms 인데 `simulation_params.gravity` 가 없으면 멈춘다(`endtime_presim` 3 과 같다).
2. 후보는 k ∈ `impacts` 인 줄이다. 자세·속도·각속도가 같은 줄은 한 상태로 묶는다(1차 충돌 직전 상태는 e 와 무관하다).
3. 특징 f = [nx, ny, nz, vn_contact/v0, |(vx,vy)|/v0, (RotMat(att)·w)·L/v0] 이다(무차원, L = 바운딩 박스 대각선의 절반). 심각도는 J_over_mv0 × vn_contact/v0 다(충격량 × 접촉점 접근 속도 — 충격 에너지 m_eff·vn² 대용, 사용자 결정 11-07). 1차 충돌은 vn 이 모두 v0 라도 접촉 형태·유효 질량(J)으로 갈리고, 센 2차 슬랩다운이 위로 온다. 같은 상태로 묶인 줄들(1차 충돌은 e 마다 J 가 다르다)은 그 가운데 최대를 쓰고, 그 줄이 조건의 출처(e·J)가 된다. ceil(count·severity_fraction) 개는 심각도 순위를 내려가며 고른다. 이때 이미 고른 심각도 상태와 f 거리가 `severity_min_distance` 보다 가까운 상태는 건너뛴다(비최대 억제, 사용자 결정 11-07 — 실측 2만 방향에서 거의 같은 모서리 슬랩다운 50 개가 몫을 다 먹었다). 심각도가 0.1% 안으로 같은 묶음은 최원점 차례로 돌고(같은 값이 많을 때 파일 순서로 자르면 한쪽 방향에 몰린다), 여기에도 거리 조건이 걸린다. 순위가 다 떨어지면 남은 몫은 덮기로 가고 prepare 가 경고한다. 나머지는 이미 고른 점에서 시작하는 f 공간 최원점 샘플링으로 고른다. 그 밖의 같은 값은 파일에서 먼저 나온 상태가 먼저다. 모든 후보는 가장 가까운 대표에 묶는다.
4. 대표 하나가 DOE 하나(1 스텝 DROP, 이름 `IC001`…)다. 자세 roll/pitch/yaw = 충돌 순간 자세(att), `InitialVelocityX/Y/Z` = v, `RigidAngularVelocityX/Y/Z` = w(둘 다 바닥 좌표, 덱 단위 — KMM 이 `*INITIAL_VELOCITY_GENERATION` 으로 쓴다, `InitialAngularVelocity*` 줄은 쓰지 않는다), `Height,0`, `EndTimeTable` = `impact_conditions/endtime.csv`(같은 상태 줄들의 endtim_k 최대, 메타 time_unit). 누적 러너·`--mode large-scale`·`batch_koomeshmodifier`(DOE 목록) 세 경로 모두 같다.
5. `impact_conditions/index.json` 에 format·source(덱·impacts·사전 해석 값)·features(정의·L·정규화·고르기 수·severity_min_distance·심각도 몫)·conditions(DOE → 대표 줄·묶인 수·심각도 값·심각도 순위 또는 coverage·가장 가까운 다른 대표까지 거리)·assignments((원래 각도, e, k) → DOE·거리·낙하 방향 dx/dy/dz)를 남긴다. runner_config 에는 `scenario.doe_impact_meta`(보기용)·`doe_impact_state`(러너 입력)·`endtime_tables`·`doe_endtim` 이 들어간다.
6. 결과는 `KooChainRun harvest --impact-map <테스트 폴더>` 로 모은다(`per_angle_risk.csv`·`per_angle_risk_summary.csv`). DOE 마다 파트를 하나 고른다 — 항복강도가 있으면(`--yield`·`--yield-by-part` 또는 result.json 의 stress_limit) σ/항복 비가 가장 큰 파트, 없으면 최대 응력 파트이고 `peak_stress` 칸은 그 파트의 응력이다. 원래 각도 요약도 같은 기준(비, 없으면 응력)으로 e·충돌 차수 가운데 지배 줄을 고른다. Run 은 `step_config.txt` 의 자세·`InitialVelocity`·`RigidAngularVelocity` 가 index.json 대표와 같은 것만 쓴다(다시 prepare 한 뒤 남은 지난 Run 은 빼고 수를 찍는다). 같은 DOE 가 여럿이면 status completed 가 먼저, 그다음 폴더 이름이 늦은 Run 이다. 전각도 sphere 리포트(postprocess `auto_sphere`·`--sphere`)는 돌리지 않는다 — DOE 가 낙하 각도가 아니라 대표 충돌 상태다(`--sphere` 를 직접 주면 멈춘다). DOE 별 deep report 는 그대로다.

1 스텝 DROP 시나리오(첫 시나리오)에서만 쓴다. `tolerance`·`part_doe`·`simulation_params.endtime_presim`·`exclude_parts` 와 함께 쓰면 prepare 가 `[IMPACT_CONDITIONS_FAILED]` 로 멈춘다. KMM 실패(3 = 덱 요소 소실, `<base>_rigidbody.json` warnings 를 볼 것), 산출 없음, 칸 빠짐, 후보 없음, 표 메타 `height`·`v0` 가 이 낙하와 다름(`table` 도), 러너 KMM 이 `EndTimeTable`·`RigidAngularVelocityX` 를 모름(`--help DROP_ATTITUDE` 로 확인, v131 이하 — `endtime_presim` 의 버전 확인과 같다), `table` 옆 rigidbody.json 의 사전 해석이 ExcludePart 로 돌았음도 같다. 표의 endtim(1~2 ms)이 `tFinal` 보다 짧으면 시간 제한은 그대로다. 대표들의 낙하 방향이 0.01° 안으로 같으면 KMM 은 그들 가운데 endtim 최대를 쓴다(prepare 가 경고한다).

#### `tolerance` (선택, CumulativeDesigner.py:571-608)

| 필드 | 형식 | 기본값 | 설명 |
|---|---|---|---|
| `roll` / `pitch` / `yaw` | object | — | `{ "tolerance": v }` 또는 `{ "min": a, "max": b }` |
| `doe_type` | string | `lhs` | `lhs` / `grid` / `random` (ToleranceDOEGenerator.py:36-38) |
| `doe_count` | int | 10 | DOE 샘플 수 |

#### `angle_mixing` (CumulativeDesigner.py:627-642)

| 필드 | 형식 | 기본값 | 값 |
|---|---|---|---|
| `strategy` | string | `same_angle` | `same_angle`/`cyclic`/`random`/`opposite`/`custom_mapping` (AngleMixingStrategy.py:32-36) |
| `cyclic_offset` | int | 1 | (cyclic 전략) |
| `random_seed` | int | `None` | (random 전략) |
| `custom_mapping` | object | `None` | (custom_mapping 전략) `{step_idx: angle_idx}` |

#### DROP용 `simulation_params` (StepConfigBuilder.build_drop_attitude_config:42-128)

| 필드 | 기본값 | 단위/의미 |
|---|---|---|
| `tFinal` | 0.005 | s, 해석 종료 시간 |
| `dt` | 1e-6 | s, 시간 간격 |
| `density` | 7.85e-9 | tonne/mm³ (바닥판 deformable 시) |
| `youngs_modulus` | 2.0e5 | MPa (바닥판 deformable 시) |
| `poisson_ratio` | 0.3 | (바닥판) |
| `height` | 1500 | mm, 낙하 높이 |
| `offset_distance` | 0.05 | mm |
| `drop_surface` | `{}` | 바닥면 정의 (아래) |
| `drop_contact` | `{}` | `DropContact.<key>,<val>` 로 직렬화 (StepConfigBuilder.py:128-131) |
| `robust_contact` | false | SINGLE_SURFACE 치환 (StepConfigBuilder.py:80, 101-103) |
| `non_reflecting_boundary` | false | 바닥판 비반사 경계 (StepConfigBuilder.py:108) |
| `rigidify_small_dt_threshold` | 0.0 | 작은 dt 요소 강체화 (StepConfigBuilder.py:111) |
| `dynamic_relaxation` | false | 누적(num_steps≥2) 스텝 간 DR 안정화. `true`(간단형) 또는 `{enabled, nrcyck, drtol, drfctr, drterm}` 객체형. `_dti.k` 에 `*CONTROL_DYNAMIC_RELAXATION`(IDRFLG=1) 주입 → 다음 낙하 deck 이 이월받아 본 해석 전 DR phase 수행. 기본 `drtol=0.01`(잔류응력 릴리즈용 완화), `drterm=tFinal`(bounded DR — 미수렴이어도 예산 소진 후 transient 진입). 주의: drtol<0.0005 는 카드 고정폭(10.3f)에 잘림 (StepConfigBuilder.py:78-100) |
| `dtmin` | 1e-10 (비-DR) / 0.01 (DR 자동) | `*CONTROL_TERMINATION` DTMIN. LS-DYNA 는 '초기 dt 의 **DTMIN 배**로 떨어지면 종료'. 미지정 시: **`dynamic_relaxation` 켜진 DR/누적 체인은 0.01 자동주입**(발산-취약, StepConfigBuilder.py:171-181), 비-DR 은 기존 1e-10 유지(회귀 0). 명시값은 항상 우선. **DROP/IMPACT/THERM 모두 배선됨**(공용 헬퍼 `build_dtmin_line`; THERM 은 구조 pass만 — ICPower 열해석 pass1 은 explicit dt 없어 제외; IMPACT 는 `impact.dtmin` override 도 허용). VIBRATION 은 CONTROL_TERMINATION 미배선이라 dtmin 미지원. ⚠️ **주의**: erosion(ERODE=1) 발산은 요소 삭제로 dt 가 임계 바로 위에서 맴돌아 DTMIN 이 안 걸릴 수 있음(실측: 0.001·0.01 모두 자동종료 실패, wall-clock 이 잡음) → DTMIN 은 보조수단, **`timeout_per_step_seconds` 가 발산 최종 안전망** |

`drop_surface.type` 값별 추가 필드 (StepConfigBuilder.py:51-73): `RigidWall` / `Plane`(`size`,`mesh`) / `PlaneGraded`(`size`,`mesh`,`num_outer_layers`,`ratio`) / 거칠기 옵션(`roughness_mode`,`r_max`,`shape_factor`,`shape_factor2`) / `deformable_to_rigid`(false).

#### `simulation_params.endtime_presim` — 자세별 종료 시간 사전 해석 (선택, Runner/EndTimePresim.py)

모든 자세에 `tFinal` 하나를 쓰는 대신, `prepare` 가 KMM `RIGID_DROP_ENDTIME`(강체 낙하 사전 해석)을 돌려 자세마다 종료 시간(`endtim`)을 정한다. 중력 끔(기본)이면 1차 충돌 뒤 접근 속도가 `strong_contact`·v0 이상인 마지막 재접촉 묶음의 끝 + `margin_ms` 이고(v133), 그런 묶음이 없으면 1차 충돌 끝 + `margin_ms` 다. 중력 켬이면 1차 뒤 첫 재접촉 묶음 끝 + `margin_ms`(v132 규칙)다. 키가 없거나 `enabled` 가 false 이면 runner_config·스텝 설정은 예전과 바이트까지 같다.

```json
"endtime_presim": {"enabled": true, "table": null, "restitution": [0.1, 0.3, 0.5],
                   "friction": 0.5, "gravity": false, "strong_contact": 0.2, "margin_ms": 1.0,
                   "exclude_parts": [], "workers": 8, "presim_timeout_seconds": 21600}
```

| 필드 | 기본값 | 의미 |
|---|---|---|
| `enabled` | false | 켜면 prepare 가 사전 해석을 돌린다 (`true` 만 써도 기본값으로 켠다) |
| `table` | null | 이미 만든 `<base>_endtime.csv` (scenario.json 기준 상대 또는 절대). 주면 사전 해석을 건너뛴다 |
| `restitution` | [0.1, 0.3, 0.5] | 반발계수 목록. 가장 긴 종료 시간을 쓴다 |
| `friction` | 0.5 | 바닥 마찰계수 |
| `gravity` | false | 사전 해석 중력. 낙하 덱에는 중력이 없어(초기 속도만) 기본은 끔이다. 끄면 접근 속도가 `strong_contact`·v0 이상인 마지막 재접촉 묶음 끝까지 본다. 켜면 리포트와 같은 조건(재착지는 뺀다)이고 1차 뒤 첫 재접촉 묶음 끝까지 본다(v132 규칙, `strong_contact` 는 쓰지 않는다) |
| `strong_contact` | 0.2 | 중력 끔 규칙의 문턱(접근 속도 ÷ v0, 0 보다 큰 실수). 묶음은 1 ms 간격으로 나누고 묶음 세기는 묶음 안 최대 접근 속도다. 낮추면 약한 늦은 스침까지 기다려 `endtim` 이 길어지고, 높이면 짧아진다. 기본 0.2 — 0.3 이면 사전 해석 마찰이 FEM 과 어긋날 때(0.5 표·실제 0.2) 1차 충돌만큼 센 재접촉을 놓쳐 0.2 로 낮췄다. KMM 옵션 파일에 `PresimStrongContact,<값>` 줄로 넘긴다(v133 이상 KMM). `gravity` 가 true 이면 쓰지 않고 경고만 한다. KCR v133 이상에서만 읽는다(v132 KCR 은 모르는 키로 무시하고 KMM 기본값(v133 0.2)을 쓴다) |
| `margin_ms` | 1.0 | 종료 시간을 정한 묶음(중력 끔은 마지막 강한 재접촉, 켬은 첫 재접촉, 없으면 1차 충돌) 끝 뒤 여유(ms) |
| `exclude_parts` | [] | 사전 해석에서 뺄 PID(받침·고정구 등). 병진 SPC 가 파트 절점의 10% 이상인 파트(바닥판 등)와 병진이 묶인 `*MAT_RIGID` 파트는 KMM 이 자동으로 뺀다. 10% 미만이면 기기 파트로 넣고 `SPC_ON_DEVICE_PART` 경고를 남기고, 뺄 파트가 기기 파트와 절점을 나누면 종료 코드 1 이다 |
| `workers` | 8 | 사전 해석 프로세스 수 |
| `presim_timeout_seconds` | 21600 | 사전 해석 KMM 시간 제한(초, 6 시간 — 러너 KMM 의 `timeout_koomeshmodifier_seconds` 와 따로). 넘으면 KMM 프로세스 묶음(apptainer·작업자)째 멈추고 prepare 가 멈춘다 |

모르는 하위 키는 경고만 하고 무시한다.

동작은 다음과 같다.
1. DOE 의 **DROP 스텝** 자세(roll, pitch, yaw)를 값으로 중복 없이 모은다. 열(THERM) 스텝의 0/0/0 은 빠진다. 이를 `<output_dir>/endtime_presim/1/angles.csv` 에 쓴다.
2. 같은 폴더에 KMM 옵션 파일 `rigid_drop_endtime.txt` 를 쓰고 표 줄을 읽을 KMM 으로 돌린다. 중력 끔이면 블록의 `PresimGravity,0` 다음 줄이 `PresimStrongContact,<strong_contact>` 다(중력 켬은 이 줄이 없어 v132 와 같다). 실행 파일은 러너와 같은 `environment.koomeshmodifier_path`(`batch_koomeshmodifier` 면 그 헤드 노드 KMM — SIF 가 없고 `/opt/` 경로면 `koochainrun_path` 옆 호스트 KMM), 컨테이너는 `apptainer_sif` 가 있으면 감싼다. apptainer 임시 폴더는 `environment.apptainer_tmpdir`(없으면 시스템 임시 폴더) 아래 이번 실행 것을 쓰고 끝나면 지운다. 시간 제한은 `presim_timeout_seconds`(기본 6 시간)이고, 넘으면 KMM 프로세스 묶음째 멈춘다. `*Inputfile` 은 러너 1 스텝과 같은 템플릿 절대 경로라서 `*INCLUDE` 가 그대로 풀린다. 작업 폴더는 KMM 둘째 인자로 넘긴다. KMM 출력은 `kmm_stdout.log` 에 남는다.
3. 작업 폴더의 `<base>_endtime.csv` 를 읽는다. 모든 자세가 있고 `endtim > 0` 이어야 한다. 표 메타 `height`·`v0`(√(2gh), 메타 `units` 기준, `simulation_params.gravity` 가 있으면 그 g)가 이 시나리오 낙하와 상대 1e-3 넘게 다르면 멈춘다(`table` 지름길도 같다). 메타 `gravity`(0/1)가 이 옵션 `gravity` 와 다르면 멈춘다. 메타 `units` 가 mm-kg-ms·mm-g-ms 인데 `simulation_params.gravity` 가 없으면 멈춘다 — FEM 의 KMM DROP_ATTITUDE 는 그 단위의 g 를 재질 밀도로 알아내지 못하고 9810(mm-t-s 값) 또는 9.81 을 쓴다(그 단위의 g 는 0.00981). 메타 `deck` 이 템플릿과 다르거나 `t_sep_ms` 메타가 없으면 경고만 한다. 메타 `endtime_rule` 이 없으면(v132 표 — 1차 뒤 첫 재접촉 규칙이라 꼭짓점마다 갈라져 오는 슬랩다운의 더 센 뒷부분을 놓칠 수 있다) 경고한다(메타 `gravity` 가 1 인 표는 v133 도 같은 규칙이라 경고하지 않는다). `endtime_rule=last_strong`(중력 끔) 표의 메타 `strong_contact` 가 이 옵션 `strong_contact` 와 1e-9 넘게 다르면 멈추고, `first_recontact`(중력 켬) 표는 `strong_contact` 를 보지 않는다(`table` 지름길도 같다). 엑셀이 붙이는 BOM 은 떼고 읽는다. 표에 `reach`(첫 접촉점에서 바닥 위 접촉점까지 가장 먼 거리)가 있으면 최대값을 찍고, 메시 바닥판 한 변의 절반보다 길면 경고한다(`drop_surface.size` 를 한 변 2·reach 이상으로 — RigidWall 은 무관). `n_unresolved > 0` 인 각도(중력 끔 사전 해석이 끝을 보지 못하고 시간 상한 — v133 은 이벤트 상한도 — 에서 멈춰 endtim 이 짧을 수 있는 각도) 수도 경고한다.
4. runner_config 에 `scenario.endtime_tables`(표 절대 경로)와 `scenario.doe_endtim`(`{doe: {step: endtim}}`, 보기용)을 남긴다.
5. 모든 DROP 스텝 설정(누적 러너·`--mode large-scale`·`batch_koomeshmodifier`)의 DropAttitude 블록에 `EndTimeTable,<표 절대 경로>` 줄이 들어간다. KMM 은 자세마다 낙하 방향이 0.01° 안인 줄의 `endtim` 을 ENDTIM 으로 쓴다(`tFinal` 줄은 남는다).
6. endtim 이 `tFinal` 보다 길면 시간 제한을 늘린다. 스텝 배율 r = ceil(그 스텝 endtim ÷ tFinal)(1 이상, 표에 없는 스텝은 1)이고 DOE 배율 F = Σ 스텝 (r + DR 이 켜진 2 스텝부터 1) 이다 — r 이 모두 1 이면 예전 step/DR 배율과 같다. submit(누적)과 rerun 의 DOE `time_limit` 은 F 의 최대 배, `--sequential` 은 슬롯마다 DOE 의 F 합의 최대 배, `--mode large-scale` 배열은 그 배열 DOE 의 r 최대 배, 러너의 스텝 `timeout_per_step_seconds` 와 deep report(`deep_timeout_seconds`·`deep_time_limit`)는 그 스텝의 r 배다. `time_limit` 은 Slurm 형식(`HH:MM:SS`·`D-HH:MM:SS`·`D-HH`·`MM` …)을 읽고, 파티션 최대에서 자르며 모자라면 🔴 경고를 찍는다. prepare·submit 이 늘린 값을 찍는다.

**러너 KMM 버전 확인.** 표를 쓰기 전에(사전 해석·`table` 지름길 모두) prepare 가 표 줄을 읽을 KMM 에 `--help DROP_ATTITUDE` 를 물어 `EndTimeTable` 이 있는지 본다. 러너와 같은 실행 파일(`environment.koomeshmodifier_path`, `batch_koomeshmodifier` 면 그 헤드 노드 KMM)이고 `apptainer_sif` 가 있으면 같은 apptainer 감싸기다. 그래서 `table` 을 줘도 헤드 노드에서 그 KMM(또는 SIF)이 돌아야 한다. 노드에서도 본다 — 누적 러너는 스텝 설정에 `EndTimeTable`·`RigidAngularVelocity` 줄이 있는데 KMM 출력에 `[EndTimeTable]`·`[RigidAngularVelocity]` 표식이 없으면 그 스텝을 실패로 두고(`[KMM version skew]` 로그), `--mode large-scale` 배열 스크립트도 KMM 출력을 `kmm_drop_attitude.log` 에 남겨 같은 표식을 grep 한다. 없으면(v131 이하) `(KMM version skew)` 로 멈춘다 — 옛 KMM 은 `EndTimeTable,<경로>` 줄을 다른 키로 잘못 읽는다(경로에 height 가 들면 Height=0, tfinal·density·dropsurface 를 덮고, runid 가 들면 죽는다). `apptainer_sif` 를 v132 이상 SIF 로(SIF 없이 쓰면 `koomeshmodifier_path` 를 v132 이상으로) 바꾼다. 중력 끔 사전 해석은 돌리기 전에 같은 KMM 에 `--help RIGID_DROP_ENDTIME` 도 물어 `PresimStrongContact` 가 있는지 본다. 없으면(v132 이하 — 그 줄에서 종료 코드 1) `(KMM too old for strong_contact)` 로 멈추니 v133 이상 SIF(또는 KMM)로 바꾼다. `table` 지름길·중력 켬은 그 줄을 쓰지 않아 묻지 않는다. 결과는 prepare 마다 (실행 파일, SIF, 모드) 하나에 한 번만 묻는다.

KMM 실패(종료 코드≠0·시간 초과), 표 없음, 빠진 자세, `endtim ≤ 0`, `table` 파일 없음, 표의 낙하 조건이 다름, 표 `strong_contact` 가 옵션과 다름, 러너 KMM 이 너무 옛것이면 prepare 가 `[ENDTIME_PRESIM_FAILED]` 와 이유를 찍고 종료 코드 1 로 멈춘다. KMM 종료 코드 3 은 덱을 읽으며 요소를 버렸다는 뜻이다(예: `*PART_INERTIA` 파트) — 질량특성·껍질이 모자랄 수 있으니 `<base>_rigidbody.json` 의 warnings 를 보고, 받아들일 수 있으면 검토한 표를 `table` 로 준다. 조용히 `tFinal` 로 돌아가지 않는다. `table` 의 자세는 낙하 방향 d = Rz(-yaw)·Ry(-pitch)·Rx(-roll)·(0,0,-1) 로 찾는다. 같은 방향이면 오일러 표기가 달라도 된다.

한계가 둘 있다.
- 누적 2 스텝부터는 앞 스텝의 변형된 `_dti.k` 에서 시작하지만, 사전 해석은 원래 템플릿의 강체 형상으로 한다(근사).
- KMM 의 단위계 판정(`Units`)·시간 간격(`PresimDt`)·최대 시간(`PresimTMax`)은 KCR 에서 넘기지 않는다(KMM 기본값). 판정이 안 되는 덱은 KMM 을 직접 돌려 만든 표를 `table` 로 준다.

### 2-5. IMPACT 모드 필드

#### `position_source` (ImpactPositionSource.parse_position_source:195-)

| `source_type` | 서브 객체 | 필드 | 코드 근거 |
|---|---|---|---|
| `grid_nxm`(기본) | `grid_nxm` | `nx`(5), `ny`(5), `bbox`[xmin,ymin,xmax,ymax] | ImpactPositionSource.py:87-126, 230-232 |
| `grid_spacing` | `grid_spacing` | `spacing_x`, `spacing_y`, `bbox` | ImpactPositionSource.py:128-, 234- |
| `manual` | (config) | (수동 좌표 목록) | ImpactPositionSource.py:171-193 |

> `bbox` 미지정 시 `template` 모델 `.k` 의 bounding box 에서 자동 계산된다 (ImpactPositionSource.py:218-227, CumulativeDesigner.py:367).

#### IMPACT용 `simulation_params.impact` / `.wall` (CumulativeScenarioRunner.py:1200-1280)

`simulation_params.impact`:

| 필드 | 기본값 | 의미 |
|---|---|---|
| `type` | `Sphere` | `Sphere` 또는 `cylinder` |
| `dimension` | 0.008 | 충격자 치수 (Sphere). cylinder 는 `cylinder_stages` 로 대체 |
| `height` | 0.5 | 낙하 높이 |
| `mesh_size` | (미지정) | 요소 크기. 없으면 KMM 이 정한다 — 치수/0.001 이 100 분할을 넘으면 치수/8(mm 모델), 아니면 0.001 |
| `dimension_damper` | (미지정) | 댐퍼 치수 `[폭,높이,오프셋]`. 없으면 KMM 이 모델 단위계(재질 밀도)로 정한다 — ton-mm-s 1.0 mm, SI 0.001 m |
| `density` | 7.85e-9 | 충격자 밀도 |
| `youngs_modulus` | 2.01e5 | 충격자 E |
| `poisson_ratio` | 0.3 | 충격자 ν |
| `tFinal` | 0.001 | s |
| `dt` | 1e-6 | s |
| `offset_distance` | 1e-5 | mm |
| `cylinder_stages` | — | 다단 실린더(아래) |

`cylinder_stages` (type=cylinder 시, CumulativeScenarioRunner.py:1212-1244): 2단 `[front, back]` 또는 3단 `[front, mid, back]`. 각 stage 필드 — `role`, `diameter`, `outer_diameter`(front 필렛, 기본=diameter), `height`, `density`, `youngs_modulus`, `poisson`.

`simulation_params.wall` (CumulativeScenarioRunner.py:1269-1274):

| 필드 | 기본값 | 의미 |
|---|---|---|
| `density` | 1.0e-9 | 바닥판 밀도 |
| `youngs_modulus` | 1.0e4 | 바닥판 E |
| `poisson_ratio` | 0.3 | 바닥판 ν |
| `num_x` / `num_y` / `num_z` | 10 / 10 / 10 | 바닥판 메시 분할 수 |

### 2-6. VIBRATION 모드 필드

#### `vibration_source` (VibrationSource.parse_vibration_source:147-)

공통 필드 — `source_type`(필수), `direction`(`X`/`Y`/`Z`, VibrationSource.py:188-214), `load_type`(`Force`/`Acceleration`, 기본 `Force`), `relative_mode`(기본 `Explicit`), `base_curve`.

`base_curve` 는 `kind` discriminated union: P1 은 `inline` 만 구현 — `{ "kind": "inline", "points": [[t, v], ...] }` (≥2점, VibrationSource.py:238-252).

`source_type` 별 핵심 입력:

| `source_type` | 핵심 입력 | DOE 수 | 코드 근거 |
|---|---|---|---|
| `explicit_factors` | `explicit_factors`: `[[pid, factor], ...]` 또는 `{"part_factors": {pid: factor}}`, 선택 `case_name`(기본 `VIB_EXPLICIT`) | 1 | VibrationSource.py:324-417 |
| `per_cap` | `per_cap`: `{"cap_pids": [...], "amplitude": 1.0}` | len(cap_pids) | VibrationSource.py:424-505 |
| `circuit_group` | `circuit_group.circuits`: `{name: {"parts": [...], "amplitude": v}}` | 회로 수 | VibrationSource.py:507-594 |

#### VIBRATION용 `simulation_params.vibration` (CumulativeScenarioRunner.py:1346-1385)

대부분의 진동 인자(direction/load_type/relative_mode/load_curve/part_factors)는 `vibration_source` 파싱 결과(`doe_vibrations` 카탈로그)에서 가져온다. `simulation_params.vibration` 은 전역 fallback 으로만 사용되며 우선순위는 `params(step별) > doe_vibrations > vibration` 이다 (CumulativeScenarioRunner.py:1360-1367).

### 2-7. THERM 모드 필드

`thermal_conditions` (scenarios[] 레벨, CumulativeDesigner.py:225-227): 문자열 리스트. 각 원소가 1 DOE 가 되며 `condition`(=angle_name) 으로 보존. 비어 있으면 단일 DOE `"THERM"`.

`simulation_params.thermal` (CumulativeScenarioRunner.py:1286-1325), 우선순위 `params > thermal > default`:

| 필드 | 기본값 | 의미 |
|---|---|---|
| `thermal_type` | `UniformChamber` | 열 적용 방식 |
| `base_temp_C` (별칭 `initial_temp_C`) | 25 | 기준 온도(℃) |
| `target_temp_C` | 85 | 목표 온도(℃) |
| `ramp_time_s` | 1.0e-3 | 승온 시간(s) |
| `dt` | 1.0e-6 | s |
| `default_cte_1_K` | 1.7e-5 | 기본 열팽창계수(1/K) |
| `part_cte` | `{}` | `{pid: cte}` 파트별 CTE 오버라이드 |

### 2-8. `postprocess` (선택, PostprocessShellGenerator.py)

| 필드 | 기본값 | 의미 | 코드 근거 |
|---|---|---|---|
| `enabled` | false | 후처리 셸 자동 실행 여부 (셸 자체는 항상 생성) | PostprocessShellGenerator.py:13-14 |
| `sif_path` | `/opt/apptainers/...`(DEFAULT_SIF_PATH) | SmartTwinPostprocessor.sif 경로 | PostprocessShellGenerator.py:75, 157, 255 |
| `auto_deep` | false | per-job deep_report 자동 실행 | PostprocessShellGenerator.py:14 |
| `auto_deep_mode` | — | deep 실행 방식 (예: `inline`) | 예제(impact_cylinder_8pi.json:79) |
| `auto_sphere` | false | sphere 종합 리포트 자동 실행 | PostprocessShellGenerator.py:14 |
| `auto_impact` | — | impact 종합 리포트 자동 실행 | 예제(impact_cylinder_8pi.json:81) |
| `delete_d3plot_after_deep` | false | deep 성공 후 d3plot 삭제(디스크 절약) | PostprocessShellGenerator.py:93-95 |
| `deep_extra_args` | — | koo_deep_report 명령에 추가 인자 | PostprocessShellGenerator.py:18 |
| `sphere_extra_args` | — | koo_sphere_report 추가 인자 | PostprocessShellGenerator.py:19 |
| `impact_extra_args` | — | koo_impact_report 추가 인자 | PostprocessShellGenerator.py:20 |

---

## 3. 사용 예제

아래 예제는 실제 `Examples/` 파일에서 발췌(가공 최소화)한 것이다.

### 3-1. DROP — Fibonacci lattice 단일 step

(Examples/scenario_examples/drop_attitude_example.json, simulation_params·scenarios 발췌)

```json
"simulation_params": {
  "height": 1500,
  "tFinal": 0.005,
  "dt": 1e-06,
  "density": 7.85e-09,
  "youngs_modulus": 2.0e5,
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
    "scenario_name": "DropAttitude_Fibonacci_10",
    "template": "MinimumModel.k",
    "angle_source": {
      "source_type": "fibonacci_lattice",
      "fibonacci_lattice": { "num_directions": 10 }
    },
    "cumulative": {
      "num_steps": 1,
      "mode_sequence": ["DROP"],
      "base_angle_index": 0,
      "angle_mixing": { "strategy": "same_angle" }
    }
  }
]
```

### 3-2. IMPACT — grid 위치 + Sphere 충격자

(Examples/scenario_examples/impact_example.json 발췌)

```json
"simulation_params": {
  "impact": {
    "type": "Sphere",
    "dimension": 8,
    "height": 500,
    "mesh_size": 1,
    "dimension_damper": [1, 1, 1],
    "density": 7.85e-09,
    "youngs_modulus": 2.01e5,
    "poisson_ratio": 0.3,
    "tFinal": 0.001,
    "dt": 1e-06,
    "offset_distance": 0.01
  },
  "wall": {
    "density": 1.0e-09,
    "youngs_modulus": 1.0e4,
    "poisson_ratio": 0.3
  }
},
"scenarios": [
  {
    "scenario_name": "Impact_Grid_3x3",
    "template": "MinimumModel.k",
    "position_source": {
      "source_type": "grid_nxm",
      "grid_nxm": { "nx": 3, "ny": 3, "bbox": [-40, -40, 40, 40] }
    },
    "cumulative": { "num_steps": 1, "mode_sequence": ["IMPACT"] }
  }
]
```

### 3-3. IMPACT — 3단 실린더 충격추 + postprocess

(Examples/scenario_examples/impact_cylinder_8pi.json — impact.cylinder_stages + postprocess 발췌)

```json
"impact": {
  "type": "cylinder",
  "height": 200,
  "mesh_size": 2,
  "tFinal": 0.001,
  "dt": 1e-06,
  "offset_distance": 0.01,
  "cylinder_stages": [
    { "role": "front", "diameter": 8,  "outer_diameter": 20, "height": 6,
      "density": 1.18e-09, "youngs_modulus": 100.0,    "poisson": 0.49 },
    { "role": "mid",   "diameter": 20, "height": 14,
      "density": 6.57e-09, "youngs_modulus": 207000.0, "poisson": 0.3  },
    { "role": "back",  "diameter": 44.5, "height": 38.003,
      "density": 6.57e-09, "youngs_modulus": 207000.0, "poisson": 0.3  }
  ]
},
"postprocess": {
  "enabled": true,
  "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
  "auto_deep": true,
  "auto_deep_mode": "inline",
  "delete_d3plot_after_deep": true,
  "auto_impact": true
}
```

### 3-4. VIBRATION — circuit_group (회로별 일괄 가진)

(Examples/scenario_examples/vibration_example.json 발췌)

```json
"vibration_source": {
  "source_type": "circuit_group",
  "direction": "Z",
  "load_type": "Force",
  "relative_mode": "Explicit",
  "base_curve": {
    "kind": "inline",
    "points": [[0, 0], [0.0005, 500], [0.001, 0]]
  },
  "circuit_group": {
    "circuits": {
      "C1_power":  {"parts": [4, 5],   "amplitude": 1.0},
      "C2_signal": {"parts": [9, 10],  "amplitude": 0.5},
      "C3_motor":  {"parts": [18],     "amplitude": 2.0}
    }
  }
},
"cumulative": { "num_steps": 1, "mode_sequence": ["VIBRATION"] }
```

### 3-5. 변환 실행 (CLI)

```bash
KooChainRun prepare scenario.json
KooChainRun prepare scenario.json -o /data/koopark/myrun/runner_config.json
```

---

## 4. 동작 원리 (코드 근거)

1. `prepare` 진입 시 `user_config.get("mode")` 로 분기: `part_validation`(KooChainRun:377) / `drop_weight_impact`(KooChainRun:383) / 그 외 cumulative(KooChainRun:389).
2. cumulative 경로에서 `CumulativeDesigner(user_config, scenario_dir=...).parse_user_config()` 가 최상위 키를 읽는다 — `environment`(CumulativeDesigner.py:126), `scenarios`(:136), `simulation_params`(:144), `postprocess`(:147).
3. 각 시나리오는 `_process_scenario` 에서 `cumulative.mode_sequence` 를 파싱(`_parse_mode_sequence`, :610-625)하여 모드 집합을 판별하고 분기한다 (:185-211). 우선순위는 VIBRATION → THERM → IMPACT → DROP.
4. 모드별 처리:
   - DROP: `angle_source`→각도 목록, `tolerance`→DOE 확장, `angle_mixing`→step 간 각도 조합 (`_process_drop_scenario`, :258-).
   - IMPACT: `position_source`→충격 위치 목록(`parse_position_source`), 각 위치 1 DOE (`_process_impact_scenario`, :355-408). bbox 미지정 시 모델 bbox 자동 계산 (:367).
   - VIBRATION: `vibration_source`→`VibrationLoadSpec`, `doe_factors_list` 길이만큼 DOE (`_process_vibration_scenario`, :410-501).
   - THERM: `thermal_conditions` 개수만큼 DOE (`_process_thermal_scenario`, :213-256).
5. `save_runner_config` 가 결과를 `runner_config.json` 으로 직렬화한다. `environment`/`simulation_params`/`postprocess` 는 조건부로 그대로 복사되고(:825-829), VIBRATION 은 `doe_vibrations` 카탈로그가 추가된다(:776-793).
6. 실행 단계에서 `CumulativeScenarioRunner` 가 step 별 KooMeshModifier 입력(`config_content`)을 모드 분기로 생성한다 — DROP(:1175-1194), IMPACT(:1196-1280), THERM(:1282-1327), VIBRATION(:1329-). 이때 `simulation_params.*` 의 기본값이 적용된다.
7. `ApptainerWrapper` 가 `environment` 의 SIF/bind/env/tmpdir 를 읽어 KooMeshModifier·LS-DYNA 명령을 Apptainer 로 래핑한다 (CumulativeScenarioRunner.py:113-145).

---

## 5. 주의사항 · 한계

- **단위 일관성**: 모든 dimensional 입력(치수, height, mesh_size, density, youngs_modulus, base_curve.points 등)은 deck(model.k) 단위계와 반드시 일치해야 한다. KooMeshModifier 는 무변환으로 그대로 카드에 기록한다 (Examples 주석: drop_attitude_example.json:2, impact_example.json:2).
- **라이선스 서버**: `LSTC_LICENSE_SERVER` 에 `localhost` 지정 금지. 컴퓨트 노드에서 sbatch 실행 시 localhost = 컴퓨트 노드가 되어 라이선스 획득에 실패한다. 헤드노드 IP 를 명시할 것 (MEMORY.md 기재 / 예제 IP 사용).
- **두 가지 스키마 공존**: 최상위 `mode == "drop_weight_impact"` 인 파일(예: Examples/drop_weight_impact/scenario.json)은 본 cumulative 스키마와 **다른 키 구조**(`model_file`, `output_dir`, `simulation_params.impactor`, `simulation_params.locations` 등)를 사용한다. 7장 참조.
- **VIBRATION P1/P2 범위**: `base_curve.kind` 는 현재 `inline` 만 구현(`csv` 등은 hook 예약, VibrationSource.py:254-). `load_type` 은 `Force`/`Acceleration` 만 허용 (VibrationSource.py:357-360).
- **혼합 mode_sequence**: VIBRATION 이 포함된 시퀀스는 다른 모드보다 먼저 분기되며, 혼합 시퀀스(VIB + 타 모드) 정책은 코드 주석상 P2 결정 사항으로 표기되어 있다 (CumulativeDesigner.py:198-199). **확인 필요** — 혼합 시퀀스 실제 동작.
- **`time_limit` 필드**: `environment.time_limit`(예제값 `"01:00:00"`)이 SlurmSubmitter 의 시간 계산(`timeout*2`, SlurmSubmitter.py:54)과 어떻게 결합/우선되는지는 본 조사 범위에서 직접 코드 경로를 확인하지 못함 — **확인 필요**.

---

## 6. 개발 현황

**부분구현**.

- 구현됨: cumulative 포맷 전체(DROP/IMPACT/THERM 모드 전처리), VIBRATION `explicit_factors`/`per_cap`/`circuit_group`, `postprocess` 셸 생성/자동 실행, `environment` Apptainer·라이선스 전달. (근거: CumulativeDesigner.py 의 `_process_*` 메서드, VibrationSource.py 의 등록된 3개 resolver, CumulativeScenarioRunner.py 의 모드 분기, PostprocessShellGenerator.py)
- 계획/hook 예약: `base_curve.kind` 의 `csv`/analytic/library (VibrationSource.py:254-, 602-605), `cap_combination` resolver(:596-600), VolumeProportional 진동 모드(CumulativeScenarioRunner.py:1340, 1383). 혼합 mode_sequence 정책(CumulativeDesigner.py:198-199).

---

## 7. 부록 — `mode: drop_weight_impact` 별도 스키마

최상위 `mode == "drop_weight_impact"` 이면 cumulative 와 다른 워크플로우(`DropWeightImpactWorkflow.prepare_drop_weight_impact`)로 처리된다 (KooChainRun:383-385). 아래는 Examples/drop_weight_impact/scenario.json 에서 발췌한 최상위/주요 키이다.

| 키 | 의미 |
|---|---|
| `project_name` | 프로젝트 이름 |
| `mode` | `"drop_weight_impact"` (필수 분기 키) |
| `model_file` | 입력 모델 `.k` (상대경로) |
| `output_dir` | 출력 디렉터리 |
| `simulation_params.tFinal` / `.dt` | 해석 시간/간격 |
| `simulation_params.impactor` | `type`(`Sphere`/`Cylinder`), `radius`, `height`, `density`, `youngs_modulus`, `poisson_ratio` |
| `simulation_params.locations` | `mode`(`grid`/`list`/`lhs`/`part_center`), `x_count`/`y_count` 또는 `spacing`, `margin`, `pids`/`layers`(part_center) |
| `simulation_params.generation_mode` | `DampingSpring`(기본)/`OutsideRigidPart`/`OutsideRigidElement` |
| `simulation_params.boundary_distance` | 충격점 강체화 반경(mm, 0=비활성) |
| `simulation_params.offset_distance` | 충격자-모델 간격(mm) |
| `simulation_params.wall` | 바닥판 물성(`youngs_modulus`, `poisson_ratio`, `density`) |
| `environment` | `koomeshmodifier_path`, `koochainrun_path`, `ncpu`, `memory`, `partition`, `sif_path`, `solver_command` 등 |

> 본 부록의 필드 의미는 예제 파일(scenario.json:1-65, scenario_part_center.json:1-38)의 `_comment` 주석 기준이다. drop_weight_impact 워크플로우의 정식 필드 스키마는 `Runner/DropWeightImpactWorkflow.py` 별도 문서에서 다룬다 — 본 문서 범위 밖.
