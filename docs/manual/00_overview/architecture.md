# pyKooCAE 아키텍처 개요

## 1. 목적 / 개요

pyKooCAE는 전자패키지/HW의 낙하·충격·진동·열 CAE 해석을 **자동 생성 → 대량 시뮬 → 후처리** 까지 일괄 처리하기 위한 3개 도구로 구성된다. 각 도구는 Nuitka로 컴파일된 단일 바이너리(`*.bin`)이며 `/data/SmartTwinPreprocessor/bin/`, `/opt/SmartTwinPreprocessor/bin/` 에 심볼릭 링크로 배포된다.

| 도구 | 약어 | 역할 | 근거 (file:line) |
|---|---|---|---|
| **KooChainRun** | KCR | Slurm 누적/DOE 시뮬레이션 오케스트레이션 CLI (`prepare`/`submit`/`run`/`status`/`collect`/`postprocess` 등) | `KooChainRun:1-9`, `KooChainRun:34-37` |
| **KooMeshModifier** | KMM | LS-DYNA `.k` 모델을 읽어 모드 기반 변형(낙하 자세, 충격추, 재료 교환 등)을 적용·재출력. SIF(SmartTwinPreprocessor) 내부에서 실행 | `occProject/Generators/KooMeshModifier.py:1-6` |
| **KooAutomatedModeller** | KAM | ODB++ PCB 패키지 정의 → STEP CAD 지오메트리 → 다중 솔버 포맷 메시(.k/.bdf/.cdb/.inp/.obj) 생성 | `occProject/Generators/KooAutomatedModeller.py:1-6` |

전체 데이터 흐름은 CAD(ODB++/STEP) → 메시(`.k`/`dynain`) → LS-DYNA → 후처리 리포트(deep/sphere/impact) 로 이어진다.

### 관계도 (텍스트 다이어그램)

```
 ┌──────────────────────┐
 │  KooAutomatedModeller│  ODB++ PKG 정의(.txt) → STEP CAD → 메시 익스포트
 │  (KAM)               │  .k / .bdf / .cdb / .inp / .obj
 └──────────┬───────────┘
            │  베이스 모델 (.k)  ※ 또는 외부 작성 .k
            ▼
 ┌───────────────────────────────────────────────────────────────┐
 │  KooChainRun (KCR) — Slurm 오케스트레이션 CLI                    │
 │                                                                │
 │  scenario.json                                                 │
 │     │ prepare  (CumulativeDesigner)                            │
 │     ▼                                                          │
 │  runner_config.json                                            │
 │     │ submit   (Slurm array/cumulative 잡 제출)                │
 │     ▼                                                          │
 │  run  (CumulativeScenarioRunner, 컴퓨트 노드에서 DOE 1개 실행) │
 │     │                                                          │
 │     ├─► KooMeshModifier  ──►  Run_<id>/DropSet.k  (SIF: 전처리) │
 │     │        (KMM)                                             │
 │     ├─► LS-DYNA          ──►  Output/dynain, d3plot (SIF: solver)│
 │     │                          │ dynain → 다음 step 입력        │
 │     │                          └─(누적 체이닝)                  │
 │     └─► 후처리 sh        ──►  deep / sphere / impact 리포트     │
 │              (KooD3plotReader, SIF: 후처리)                     │
 └───────────────────────────────────────────────────────────────┘
```

근거: KCR 파이프라인 `KooChainRun run` 설명 `KooChainRun:167-170` ("MeshModifier → LS-DYNA → dynain → next step"), 후처리 3종 `KooChainRun:303-318`, KMM 호출 `Runner/CumulativeScenarioRunner.py:1524-1535`, dynain 대기 `:343-362`, KAM 익스포트 포맷 `occProject/Generators/KooAutomatedModeller.py:150-155`.

## 2. 입력 옵션 · 인자 (표)

### 2.1 KooChainRun 서브커맨드

| 서브커맨드 | 입력 | 기능 | 근거 (file:line) |
|---|---|---|---|
| `prepare <scenario.json>` | `-o/--output` | scenario.json → runner_config.json 변환 | `KooChainRun:63-79` |
| `submit <config>` | `--mode {large-scale,cumulative}`, `--nodes`, `--jobs-per-node`, `--ncpu-per-job`, `--partition` | Slurm 잡 제출 (기본 cumulative) | `KooChainRun:81-128` |
| `run <config> --doe N` | `--resume`, `--skip-koomeshmodifier`, `--pregenerated-dir` | 단일 DOE 누적 파이프라인 실행 (컴퓨트 노드용) | `KooChainRun:164-196` |
| `status [config]` | `--watch` | 실행 상태 모니터링 | `KooChainRun:145-159` |
| `collect <config> [output_dir]` | — | 완료 결과 수집 | `KooChainRun:200-217` |
| `stop [test_dir]` | — | jobs.json의 Slurm 잡 전부 취소 | `KooChainRun:219-231` |
| `rerun [test_dir]` | `--dry-run`, `--force`, `--does`, `--exclude-nodes`, `--sequential`, `--nodes`, `--cleanup-stale` | 실패/미완료 DOE만 재실행 | `KooChainRun:234-285` |
| `diagnose [test_dir]` | — | 실패 DOE 원인 진단(라이선스/타임아웃/메모리) | `KooChainRun:288-300` |
| `postprocess <config>` | `--deep` / `--sphere` / `--impact` / `--all` (상호배타) | 후처리 sh 수동 trigger | `KooChainRun:303-318` |

### 2.2 KooMeshModifier 호출 인자

```
python KooMeshModifier.py <option_file_path> [working_directory]
```

| 위치 인자 | 의미 | 근거 (file:line) |
|---|---|---|
| `argv[1]` | 옵션 파일(.txt) 이름 | `occProject/Generators/KooMeshModifier.py:3142-3149` |
| `argv[2]` (선택) | 작업 디렉토리 (없으면 현재 디렉토리) | `occProject/Generators/KooMeshModifier.py:3147-3149` |

옵션 파일의 `*mode` 블록에서 변형 모드를 지정한다. 지원 모드 예: `DROP_ATTITUDE`, `DROP_WEIGHT_IMPACT_TEST`, `MATERIAL_EXCHANGE`, `PART_LOCATION_DOE`, `VIBRATION_LOAD`, `THERMAL_LOAD`, `DYNAIN_TO_INITIAL`, `REMESH_TETRA`, `CONVERT_CNRB_TO_SOLID` 등 (전체 목록 `occProject/Generators/KooMeshModifier.py:244-335`).

### 2.3 KooAutomatedModeller 호출 인자

```
python KooAutomatedModeller.py <package_definition_file> [--display]
```

근거: 사용법 `occProject/Generators/KooAutomatedModeller.py:9`. 실제 진입점은 `sys.argv` 로 모드 토큰(`PKG`/`PBA` 등)과 정의 파일명을 받는다 (`occProject/Generators/KooAutomatedModeller.py:316`, `:391-414`). `package.layerList[0].meshGenerationMode == True` 일 때 .bdf/.k/.cdb/.inp/.obj 를 동시 익스포트한다 (`:148-155`).

## 3. 사용 예제

### 3.1 KooChainRun 시나리오 (scenario.json, IMPACT — 3단 실린더 충격추)

`Examples/scenario_examples/impact_cylinder_8pi.json` 발췌 (가공 없음):

```json
{
  "project_name": "Impact_Cylinder8pi",
  "base_dir": "/data/koopark/Impact_Cylinder8pi",
  "environment": {
    "koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "apptainer_sif": "/opt/apptainers/SmartTwinPreprocessor.sif",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif",
    "koochainrun_path": "/data/SmartTwinPreprocessor/bin/KooChainRun"
  },
  "postprocess": {
    "enabled": true,
    "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
    "auto_deep": true,
    "auto_impact": true
  },
  "scenarios": [
    {
      "scenario_name": "Cyl8pi_grid14x10",
      "template": "NM4_DV1.k",
      "position_source": { "source_type": "grid_nxm",
        "grid_nxm": { "nx": 14, "ny": 10, "bbox": [-31.628, 114.045, 31.628, 155.068] } },
      "cumulative": { "num_steps": 1, "mode_sequence": ["IMPACT"] }
    }
  ]
}
```

이 시나리오는 전처리 SIF(`SmartTwinPreprocessor.sif`), 솔버 SIF(`LSDynaBasic_*.sif`), 후처리 SIF(`SmartTwinPostprocessor.sif`) 세 컨테이너를 모두 사용한다 (출처: `Examples/scenario_examples/impact_cylinder_8pi.json:7-82`).

전형적 CLI 흐름:

```
KooChainRun prepare scenario.json
KooChainRun submit runner_config.json --nodes 10 --jobs-per-node 4 --ncpu-per-job 16
KooChainRun status
KooChainRun collect runner_config.json results/
```

(출처: `KooChainRun:42-50`)

### 3.2 KooMeshModifier 입력 .k/옵션 블록 (DROP_ATTITUDE)

`Examples/alldropangles/drop_attitude.txt` 발췌 (가공 없음):

```
*Inputfile
MinimumModel.k
*RunDirectoryMode,True,Data/Results,Data/Metadata
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,108.40071741034467,-96.70843214185096,...
EulerPitching,-42.36402149151405,89.103109042852,...
Height,1500,1500,1500,1500,1500
OffsetDistance,0.1
Density,2700
YoungsModulus,70000000000
tFinal,0.001
dt,0.000001
**EndDropAttitude
*End
```

`*Inputfile` 로 베이스 `.k` 를 지정하고 `*Mode` 블록에서 `DROP_ATTITUDE` 모드를 선언, `RunDirectoryMode=True` 면 결과를 `Run_<id>/` 디렉토리로 출력한다 (출처: `Examples/alldropangles/drop_attitude.txt:1-27`).

## 4. 동작 원리 (코드 근거)

### 4.1 KooChainRun — 2단계 설계/실행 파이프라인

- **prepare**: scenario.json 을 로드해 `CumulativeDesigner` 로 runner_config.json 생성. `mode` 가 `part_validation`/`drop_weight_impact` 면 전용 워크플로우로 분기 (`KooChainRun:347-393`, 분기 `:376-386`).
- `CumulativeDesigner` 처리 단계: 각도 소스 파싱 → Tolerance/DOE → 각도 믹싱 → 템플릿 자동 선택 → runner_config.json 생성 (`Runner/CumulativeDesigner.py:1-19`).
- **submit**: `--mode cumulative` 는 DOE별 Slurm 잡(`KooChainRun run`)을 제출, `large-scale` 는 LargeScaleDOEManager array 잡 사용 (`KooChainRun:81-100`, 분기 `:816-817`).
- **run**: `CumulativeScenarioRunner` 가 단일 DOE 의 누적 파이프라인을 실행 (`KooChainRun:1941-1972`).

### 4.2 DOE 내부 파이프라인 (CumulativeScenarioRunner)

1. KooMeshModifier 실행 — `cmd = [koomesh_path, config_file]` 를 `ApptainerWrapper.wrap_command(...)` 로 SIF 래핑 후 실행, stdout 에서 `run_id` 파싱 (`Runner/CumulativeScenarioRunner.py:1524-1535`, `:1566-1571`). KMM 은 Nuitka 바이너리라 `python3` prefix 없이 직접 실행 (`:1531`).
2. LS-DYNA 실행 후 `Output/dynain` 생성 대기 — 파일 크기 안정화로 완료 판정 (`:343-362`).
3. 누적 체이닝 — 이전 step 의 `dynain` 을 다음 step 입력으로 사용 (`:916-921`, `:1161-1163`).

### 4.3 KooMeshModifier — 옵션→모드→변형→출력

`__main__` 에서 옵션 파일을 읽고 `ImportOption → ImportBaseFile → GenerateMetaData → GenerateModifiedFile` 순으로 실행 (`occProject/Generators/KooMeshModifier.py:3153-3175`). `*mode` 블록을 파싱해 `modeList` 를 채우고 (`:235-335`), 각 모드를 순차 적용한다 (`:2783-2784`). 실행 환경은 SIF 내부 `Library/OCC` LD_LIBRARY_PATH 설정에 의존 (`:21-33`).

### 4.4 KooAutomatedModeller — ODB++ → CAD → 메시

ODBCADManager/PackageGenerator 로 패키지 정의(.txt)를 STEP 으로 생성 후 (`:117-145`, `:150`), `meshGenerationMode` 가 켜져 있으면 파트/노드셋을 만들고 .bdf/.k/.cdb/.inp/.obj 다중 포맷으로 익스포트 (`:148-160`). Linux 에서는 PyQt5 번들 Qt / OCC 경로를 LD_LIBRARY_PATH 에 넣고 re-exec 한다 (`:20-46`).

### 4.5 후처리 — deep / sphere / impact 리포트

`PostprocessShellGenerator` 가 KooD3plotReader 기반 sh 를 생성한다: `deep_report.sh`(단일 시뮬 d3plot → koo_deep_report), `sphere_report.sh`(전각도 DROP 통합), `impact_report.sh`(전위치 부분충격 IMPACT 통합) (`Runner/PostprocessShellGenerator.py:1-6`). submit 후 시나리오 mode 에 따라 DROP→sphere, IMPACT→impact 를 자동 선택한다 (`KooChainRun:825-852`).

### 4.6 경로/SIF 해석

`PathResolver.find_koomeshmodifier()` 는 bin 상대경로 → `$KOO_PATH` → config → 기본값(`/opt/pyKooCAE/bin/KooMeshModifier` 등) 순으로 탐색 (`Runner/PathResolver.py:17-83`). SIF 는 runner_config 의 `apptainer_sif`(전처리), `lsdyna_apptainer_sif`(솔버) 로 지정되며 `ApptainerWrapper` 가 `apptainer exec` 로 래핑한다 (`Runner/CumulativeScenarioRunner.py:110-156`).

## 5. 주의사항 · 한계

- **3개 SIF 분리 필요**: 전처리(`SmartTwinPreprocessor.sif`), 솔버(`LSDynaBasic_*.sif`), 후처리(`SmartTwinPostprocessor.sif`) 가 각각 별도이며 scenario.json 의 `apptainer_sif`/`lsdyna_apptainer_sif`/`postprocess.sif_path` 로 지정해야 한다 (`Examples/scenario_examples/impact_cylinder_8pi.json:12-15`,`:77`). 현재 호스트에 존재 확인된 SIF 는 `/opt/apptainers/SmartTwinPostprocessor.sif` 뿐이며 `SmartTwinPreprocessor.sif`/`LSDynaBasic_*.sif` 의 실제 배치 경로는 **확인 필요**(설정 파일에는 `/opt/apptainers/` 로 명시).
- **KooMeshModifier 는 SIF 내부 실행 전제**: `Library/OCC` 등 외부 런타임 의존성 때문에 단독 호스트 실행 시 LD_LIBRARY_PATH 설정이 필요하다 (`occProject/Generators/KooMeshModifier.py:21-33`).
- **KooAutomatedModeller 는 IP/라이선스 게이트**: 등록된 IP 화이트리스트 및 만료일(2027-12-31) 체크가 있어 미등록 IP 에서는 종료된다 (`occProject/Generators/KooAutomatedModeller.py:342-389`). 또한 배포 빌드 스크립트에서 자동 배포되지 않는 경우가 있다 — 배포 범위는 `00_overview/install_build.md` 참조.
- **누적 체이닝은 dynain 의존**: step 간 연결은 LS-DYNA 가 정상 종료해 `dynain` 을 생성해야 성립한다. 미생성 시 다음 step 입력이 비어 실패 (`Runner/CumulativeScenarioRunner.py:343-362`,`:1092-1101`).
- **테스트 디렉토리는 NFS 필수**: Slurm 컴퓨트 노드가 접근 가능한 `/data/...` 경로를 써야 한다(프로젝트 메모리 규칙; scenario `base_dir` 예시 `/data/koopark/...`).

## 6. 개발 현황

**구현됨 (부분적으로 계획 모드 혼재).**

근거:
- KooChainRun 9개 서브커맨드 모두 핸들러 연결 (`KooChainRun:325-345`, prepare/submit/run/status/collect/stop/rerun/diagnose/postprocess).
- KooMeshModifier 30+ 모드 파싱 및 적용 루프 구현 (`occProject/Generators/KooMeshModifier.py:244-335`,`:2783-2784`).
- KooAutomatedModeller ODB++→STEP→다중포맷 익스포트 구현 (`occProject/Generators/KooAutomatedModeller.py:148-160`).
- 3개 바이너리 모두 `/data/SmartTwinPreprocessor/bin/`, `/opt/SmartTwinPreprocessor/bin/` 에 심볼릭 링크로 배포 확인됨 (`ls /data/SmartTwinPreprocessor/bin/`).
- **계획/미확인 요소**: `REMESH_TETRA` 등 일부 모드는 프로젝트 메모리상 진행 중 항목으로 표기되어 성숙도 **확인 필요**. 전처리/솔버 SIF 의 실제 호스트 경로도 **확인 필요**.
