# 용어집 (Glossary)

## 1. 목적 / 개요

pyKooCAE 매뉴얼 전반에서 반복 사용되는 핵심 용어를 코드 근거와 함께 짧게 정의한다. 각 항목은 코드(`KooChainRun`, `Runner/`)의 주석·docstring·실제 동작에서 발췌했으며, 추측이 아닌 file:line 근거를 명시한다.

이 페이지는 정의 사전이다. 상세 사용법은 각 모듈 챕터(`01_KooChainRun`, `02_KooMeshModifier`, `03_KooAutomatedModeller`)를 참조한다.

## 2. 용어 정의 (표)

아래 표는 용어 → 짧은 정의 → 1차 근거(file:line) 순이다. 상세 설명·예제·동작 원리는 4장에서 다룬다.

| 용어 | 짧은 정의 | 1차 근거 (file:line) |
|---|---|---|
| **DOE** | Design of Experiments. 각도(또는 위치/조건) 산포 분석용 실험 샘플 집합. LHS / Grid / Random 3종. | `Runner/ToleranceDOEGenerator.py:4`, `:34-38` |
| **cumulative (누적 시뮬)** | 여러 step을 순차 실행하며 직전 step 결과(dynain)를 다음 step 초기상태로 누적 전달하는 모드. | `Runner/CumulativeDesigner.py:2-14`, `:104-105` |
| **dynain** | LS-DYNA가 `*INTERFACE_SPRINGBACK_LSDYNA` 로 출력하는 변형 후 상태(절점좌표/응력) 파일. 다음 step 초기화 입력. | `Runner/CumulativeScenarioRunner.py:343-345`, `KooDynaAdditional.py:266` |
| **scenario.json** | 사용자 친화 입력 파일. `prepare` 의 입력. | `KooChainRun:40-41`, `:63-76` |
| **runner_config.json** | scenario.json 을 변환해 만든 상세 실행 설정. Executor(Runner)의 입력. | `Runner/CumulativeDesigner.py:4-7`, `KooChainRun:50` |
| **alias 패턴** | run 식별용 별칭 문자열. `{project}_CUM{steps}_DOE{doe}_S{step}_{mode}_{condition}`. | `Runner/AliasManager.py:64-67`, `:33` |
| **deep / sphere / impact 리포트** | KooD3plotReader 후처리 3종: 단일 시뮬 / 전각도 DROP 통합 / 전위치 IMPACT 통합. | `Runner/PostprocessShellGenerator.py:4-9` |
| **tied contact** | 접촉면을 묶어 분리/관통을 막는 `*CONTACT_TIED_*` 카드. | `occProject/Generators/KooCAEManager/KooContact.py:460-466`, `Runner/StepConfigBuilder.py:121-125` |
| **ton-mm-s 단위계** | `[tonne, mm, s, MPa]` 일관 단위계. 솔버 deck 표준. | `Runner/StepConfigBuilder.py:40`, `Runner/DropWeightImpactWorkflow.py:482-485` |
| **SIF / apptainer** | Apptainer(Singularity) 컨테이너 이미지(`.sif`). 전처리/솔버/후처리 실행환경. | `Runner/CumulativeScenarioRunner.py:110-120`, `:128-156` |

## 3. 사용 예제

### 3.1 실제 scenario.json (발췌)

`Examples/scenario_examples/drop_attitude_example.json` 에서 핵심 블록을 발췌한다. scenario.json 한 파일 안에 단위계 주석, 환경(SIF/단위), 시뮬 파라미터, cumulative/DOE 설정이 모두 들어간다.

```json
{
  "_comment_unit_system": "Solver unit system: [tonne, mm, s, MPa]. ...",
  "_comment_steel_ref": "Steel reference (ton-mm-s): density=7.85e-9 tonne/mm³, youngs_modulus=2.0e5 MPa (200 GPa).",
  "project_name": "Example_DropAttitude_Single",
  "base_dir": "/data/koopark/Example_DropAttitude",
  "environment": {
    "apptainer_sif": "/opt/apptainers/SmartTwinPreprocessor.sif",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif"
  },
  "simulation_params": {
    "height": 1500, "tFinal": 0.005, "dt": 1e-06,
    "density": 7.85e-09, "youngs_modulus": 2.0e5, "poisson_ratio": 0.3
  },
  "scenarios": [{
    "scenario_name": "DropAttitude_Fibonacci_10",
    "angle_source": { "source_type": "fibonacci_lattice",
                      "fibonacci_lattice": { "num_directions": 10 } },
    "cumulative": { "num_steps": 1, "mode_sequence": ["DROP"] }
  }]
}
```

근거: `Examples/scenario_examples/drop_attitude_example.json:1-68`.

### 3.2 alias 예시

```
GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40
GalaxyS25_CUM006_DOE001_S003_DROP_F1
```

근거: `Runner/AliasManager.py:9`, `:32`.

### 3.3 CLI 워크플로우

```bash
# scenario.json → runner_config.json
KooChainRun prepare scenario.json

# Slurm 제출
KooChainRun submit runner_config.json --nodes 10 --jobs-per-node 4 --ncpu-per-job 16

# 상태 확인 / 결과 수집
KooChainRun status
KooChainRun collect runner_config.json results/
```

근거: `KooChainRun:39-50`.

## 4. 동작 원리 (코드 근거)

### DOE
DOE(Design of Experiments)는 기준 각도(roll/pitch/yaw)에 tolerance 범위를 주고 샘플을 뽑아 산포를 분석하기 위한 실험 집합이다. 타입은 `DOEType` Enum으로 LHS(Latin Hypercube, 권장), GRID(전체 조합), RANDOM 3종(`Runner/ToleranceDOEGenerator.py:34-38`). 기본값은 `doe_type=DOEType.LHS`, `doe_count=10`(`:65-66`). 샘플마다 `{base_name}_DOE{i+1:03d}` 이름이 붙는다(`:161-162`). DROP 외 모드에서는 DOE 수의 의미가 달라져, VIBRATION/THERM 모드는 conditions 리스트 개수가 곧 DOE 수다(`Runner/CumulativeDesigner.py:220-221`, `:224`).

### cumulative (누적 시뮬)
`CumulativeDesigner` 가 사용자 JSON을 받아 누적 step 시퀀스를 생성한다(`Runner/CumulativeDesigner.py:2-14`). 누적 모드/step 수는 `cumulative.num_steps` 로 지정한다(`:180-182`). 각 step은 직전 step의 dynain을 source로 받는다 — `dynain_source=f"Step{step_number-1:03d}/dynain" if step_number > 1 else None`(`:245`, `:340`, `:396`). 실행 시 step 사이에서 `DYNAIN_TO_INITIAL` 을 돌려 dynain을 다음 step 초기상태로 변환하되, 마지막 step에서는 생략한다(`Runner/CumulativeScenarioRunner.py:1109-1115`).

### dynain
LS-DYNA가 `*INTERFACE_SPRINGBACK_LSDYNA` 카드로 출력하는 변형 후 상태 파일이다(`occProject/Generators/KooCAEManager/KooDynaAdditional.py:266`). Runner는 솔버 종료 후 `Output/dynain` 생성을 폴링하며, 파일 크기가 두 번 측정에서 안정되면 완료로 본다(`Runner/CumulativeScenarioRunner.py:343-355`). 누적 step 사이에서는 `DYNAIN_TO_INITIAL`(KooMeshModifier 모드)로 dynain을 다음 step 입력으로 가공한다(`occProject/Generators/KooMeshModifier.py:2605-2609`, `:2852-2853`).

### scenario.json → runner_config.json
`KooChainRun prepare scenario.json` 이 사용자 친화 `scenario.json` 을 상세 실행 설정 `runner_config.json` 으로 변환한다(`KooChainRun:63-66`). 변환은 `CumulativeDesigner` 가 수행한다: 각도 소스 파싱 → Tolerance/DOE 적용 → 각도 믹싱 → 템플릿 선택 → runner_config.json 생성(`Runner/CumulativeDesigner.py:9-14`). 산출된 runner_config.json 은 `project`/`scenario`(steps, doe_angles, doe_count)/`execution`/`environment`/`simulation_params`/`postprocess` 섹션으로 직렬화된다(`Runner/CumulativeDesigner.py:795-833`). 이 파일을 Runner(Executor)가 읽어 실제 시뮬레이션을 순차 실행한다(`Runner/CumulativeScenarioRunner.py:3-6`).

### alias 패턴
누적 시나리오 run의 별칭은 `generate_alias_cumulative` 가 생성한다: `f"{project}_CUM{total_steps:03d}_DOE{doe_index:03d}_S{step:03d}_{mode}_{condition}"`(`Runner/AliasManager.py:64-67`). 역파싱은 정규식 `(.+)_CUM(\d{3})_DOE(\d{3})_S(\d{3})_([A-Z]+)_(.+)` 로 project/total_steps/doe_index/step/mode/condition 필드를 복원한다(`:33`, `:40-46`). 순차(SEQ) 모드는 DOE 필드 없이 `generate_alias_sequential` 을 쓴다(`:70-73`).

### deep / sphere / impact 리포트
KooD3plotReader 후처리 3종이다(`Runner/PostprocessShellGenerator.py:4-6`):
- **deep_report**: 단일 시뮬 d3plot → `koo_deep_report`. 각 `Run_*/report` 에 per-job 생성(`:4`, `:57`, `:120`).
- **sphere_report**: 전각도 DROP 통합 → `koo_sphere_report`. output_dir 에 생성(`:5`, `:134`, `:221`).
- **impact_report**: 전위치 부분충격(IMPACT) 통합 → `koo_impact_report`. output_dir 에 생성(`:6`, `:231`).

sphere vs impact 분기는 `report_mode_from_runner_config()` 가 판정한다: 모든 step mode 가 IMPACT → "IMPACT"(impact_report), 모두 DROP → "DROP"(sphere_report), mixed → 첫 step mode. 둘 다 동시에 돌지 않는다(`:300-323`). 자동 실행은 `enabled=true && auto_deep/auto_sphere=true` 일 때만 일어난다(`:14`).

### tied contact
접촉면 두 면을 묶어 분리/관통을 막는 `*CONTACT_TIED_*` 계열 카드다. KooContact가 `*CONTACT_TIED_SURFACE_TO_SURFACE_ID`, `*CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID` 등 여러 변종을 클래스로 제공한다(`occProject/Generators/KooCAEManager/KooContact.py:444-466`). Runner 쪽에서는 step deck 생성 시 `simulation_params.tied_options` 의 키/값을 `TiedOptions.{key},{val}` 라인으로 deck에 추가한다(`Runner/StepConfigBuilder.py:121-125`, `:171`).

### ton-mm-s 단위계
deck 전반에서 `[tonne, mm, s, MPa]` 단위계를 사용한다(`Runner/StepConfigBuilder.py:40`). 강철 기준값은 density = 7.85e-9 tonne/mm³, Young's modulus = 2.0e5 MPa(= 200 GPa)이다(`:41`, `:44-45`; `Runner/DropWeightImpactWorkflow.py:482-485`). 충격추/바닥판 기본값도 같은 단위계로 통일된다(`Runner/DropWeightImpactWorkflow.py:546-552`). KooMeshModifier는 사용자 입력값을 변환 없이 deck에 그대로 기입하므로, scenario.json 입력 단위는 반드시 deck 단위계와 일치해야 한다(`Examples/scenario_examples/drop_attitude_example.json:2`). thermal 모드는 ton-mm-s + double precision SIF 가 필수다(`Runner/CumulativeScenarioRunner.py:1285`).

### SIF / apptainer
실행은 Apptainer(구 Singularity) 컨테이너 이미지(`.sif`) 안에서 이뤄진다. `ApptainerWrapper` 가 명령을 `apptainer exec --bind ... --env ... <sif> <cmd>` 형태로 래핑한다(`Runner/CumulativeScenarioRunner.py:110-156`). SIF는 용도별로 분리된다: 전처리(KooMeshModifier 등) `apptainer_sif`, 솔버(LS-DYNA) `lsdyna_apptainer_sif`(`:115-118`). `APPTAINER_TMPDIR` 는 호스트 환경변수로 설정되며(노드 로컬 디스크, NFS 충돌 방지) job별 고유 디렉토리를 쓴다(`:122-126`, `:144-145`). scenario.json 의 `environment` 블록에서 각 SIF 경로/bind/env 를 지정한다(`Examples/scenario_examples/drop_attitude_example.json:14-26`).

## 5. 주의사항 · 한계

- **단위 일치 책임은 사용자에게 있다.** KooMeshModifier는 입력값을 변환하지 않고 deck에 그대로 기입한다. scenario.json 값은 ton-mm-s 와 일치해야 한다(`Examples/scenario_examples/drop_attitude_example.json:2`).
- **dynain 폴링은 크기 안정성 기반.** 파일이 존재해도 크기가 두 번 측정에서 같아야 완료로 인정하며, timeout(기본 604800초) 초과 시 실패 처리한다(`Runner/CumulativeScenarioRunner.py:349-362`, `:1093`).
- **sphere/impact 리포트는 배타적.** mixed mode 시나리오는 첫 step mode 기준으로 한쪽 리포트만 돈다(`Runner/PostprocessShellGenerator.py:307`, `:318-323`).
- **LSTC_LICENSE_SERVER=localhost 주의.** SIF 내부에 localhost로 박혀 있으면 compute node에서 라이선스 조회가 헤드노드가 아닌 자기 노드를 보게 되어 실패한다. `lsdyna_apptainer_env` 에 헤드노드 IP를 명시해야 한다(`Examples/scenario_examples/drop_attitude_example.json:19-25` 의 `LSTC_LICENSE_SERVER: "192.168.122.1"`).
- **빌드된 .sif 는 빌드 스크립트가 생성하지 않는다.** SIF는 별도 환경이며, pyKooCAE 빌드 산출물(바이너리)과 분리된다(`docs/manual/00_overview/install_build.md:13-15`).
- DOE 수의 의미가 모드별로 다르다(DROP=각도 샘플 수, THERM/VIBRATION=conditions 개수). 혼동 주의(`Runner/CumulativeDesigner.py:195`, `:220-221`).

## 6. 개발 현황

**구현됨.** 본 용어집에 정의된 모든 개념은 현재 코드베이스에서 동작하는 기능에 대응한다:
- DOE 생성기 `Runner/ToleranceDOEGenerator.py` (LHS/Grid/Random)
- cumulative Designer/Runner `Runner/CumulativeDesigner.py`, `Runner/CumulativeScenarioRunner.py`
- alias 생성/파싱 `Runner/AliasManager.py`
- deep/sphere/impact 리포트 셸 생성 `Runner/PostprocessShellGenerator.py`
- tied contact 카드 `occProject/Generators/KooCAEManager/KooContact.py`
- CLI prepare/submit/status/collect `KooChainRun`

근거: 위 4장의 file:line 인용 전체. 단, 일부 항목(robust_contact 의 SINGLE_SURFACE 교체 등 tied 면 제외 로직)은 KooMeshModifier 측 상세 구현으로 본 용어집 범위 밖이며, 해당 동작은 별도 모듈 문서에서 다룬다 — 본 페이지에서는 **확인 필요** 로 남긴다.
