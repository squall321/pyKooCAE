# KooMeshModifier 모드: PART_VALIDATION_SPLIT

## 1. 목적 / 개요

`PART_VALIDATION_SPLIT`은 원본 LS-DYNA 모델을 **파트별 개별 `.k` 파일**로 분할하여, 각 파트를 독립적으로 0도 자유낙하시키는 **파트별 낙하 검증 모델**을 자동 생성하는 모드이다.

전각도(full-angle) 낙하 해석에 들어가기 전에, 각 파트가 단독으로 해석을 정상 종료할 수 있는지(= 메시 품질에 문제가 없는지) 사전 점검하는 것이 목적이다. 특정 파트가 해석 중 터지면(FAIL) 그 파트의 메시 품질(찌그러진 요소, 퇴화 요소 등)을 확인할 단서가 된다.

- 분할 대상: 요소 수가 충분하고, 비강체(non-RIGID) 재료를 가진 파트
- 각 파트 모델에는 바닥판(quad shell), 0도 낙하 초기속도, 접촉, 중력, CONTROL 카드가 자동 부착됨
- 분할과 함께 `validation_manifest.json`, `scenario.json`, `run.sh`(Slurm array job)가 생성됨

이 모드는 KooChainRun의 `mode: "part_validation"` 워크플로우(prepare → submit → collect)의 분할 단계(prepare)에서 호출된다.

근거:
- 모드 본체 docstring: `occProject/Generators/KooCAEManager/KooPartValidator.py:1-9, 18-34`
- 워크플로우 설명: `Runner/PartValidationWorkflow.py:7`
- 예제 설명: `Examples/part_validation/README.txt:5-8`

## 2. 입력 옵션 / 인자 (표)

옵션은 `modeIDOption[modeid]` dict로 전달되며, KooChainRun이 KooMeshModifier 입력(step_config `.k`)에 기록한다. 실제 동작에서 소비되는 옵션은 다음과 같다.

| 옵션 키 (dict) | 입력 `.k` 키워드 | 의미 | 기본값 | 근거 (file:line) |
|---|---|---|---|---|
| `output_dir` | `*OutputDir` | 분할 결과 출력 디렉토리 | `<curDir>/validation_split` | `KooMeshModifier.py:2558`; `PartValidationWorkflow.py:240` |
| `height` | `*Height` | 낙하 높이 (mm) | `100.0` | `KooPartValidator.py:40`; `PartValidationWorkflow.py:237` |
| `tFinal` | `*tFinal` | 해석 종료 시간 (s) | `0.0005` | `KooPartValidator.py:41`; `PartValidationWorkflow.py:238` |
| `dt` | `*Dt` | DATABASE/D3PLOT 출력 간격 (s) | `0.00001` | `KooPartValidator.py:42`; `PartValidationWorkflow.py:239` |
| `min_elements` | `*MinElements` | 이 개수 미만 요소 파트는 skip | `1` (워크플로우 기본), `1` (분할 함수 기본) | `KooPartValidator.py:44`; `PartValidationWorkflow.py:241` |
| `except_pids` | `*ExceptPID` | 제외할 PID 리스트 | `[]` | `KooPartValidator.py:43`; `PartValidationWorkflow.py:244` |
| `floor_size` | (없음) | 바닥판 크기 `[x, y, z]` | 자동 (bbox 2배) | docstring `KooPartValidator.py:28` — **확인 필요**: 코드 본문에서 `option`의 `floor_size`를 읽는 부분이 없고, 바닥판 크기는 항상 bbox 기반으로 자동 계산됨 (`KooPartValidator.py:127-129`). docstring과 구현이 불일치 |
| `environment` | (scenario 경유) | Slurm/솔버 환경 (run.sh 생성용) | `{}` | `KooPartValidator.py:180, 213` |

> 참고: `scenario.json` 레벨의 필드명(`simulation_params.height` 등)과 환경 필드는 `Examples/part_validation/README.txt:45-66`에 정리되어 있다. KooChainRun이 이를 위 표의 dict 옵션으로 변환한다.

## 3. 사용 예제

### 3-1. scenario.json (KooChainRun 워크플로우)

`Examples/part_validation/scenario.json` 발췌:

```json
{
    "project_name": "PartValidation_Example",
    "mode": "part_validation",
    "description": "파트별 낙하 검증 시뮬레이션 — 각 파트를 독립적으로 0도 낙하시켜 해석 가능 여부 사전 확인",

    "model_file": "../HWWarrantyDropTest/Tests/Test_001/model.k",
    "output_dir": "validation_output",

    "simulation_params": {
        "height": 100,
        "tFinal": 0.0005,
        "dt": 0.00001
    },

    "environment": {
        "sif_path": "/data/SmartTwinPreprocessor/containers/lsdyna.sif",
        "solver_command": "ls-dyna",
        "koomeshmodifier_path": "/data/SmartTwinPreprocessor/bin/KooMeshModifier",
        "ncpu": 4,
        "memory": "4G",
        "partition": "normal"
    },

    "min_elements": 10,
    "except_pids": []
}
```

CLI 흐름 (`Examples/part_validation/README.txt:94-105`):

```bash
cd Examples/part_validation
KooChainRun prepare scenario.json     # 분할 + runner_config + run.sh 생성
KooChainRun submit  runner_config.json  # Slurm 병렬 실행
KooChainRun collect runner_config.json  # PASS/FAIL 리포트 수집
```

### 3-2. KooMeshModifier 입력 `.k` 모드 블록

KooChainRun이 KooMeshModifier에 전달하기 위해 생성하는 step_config 블록 (`Runner/PartValidationWorkflow.py:231-246`):

```
*Inputfile
<model_file>
*Mode
PART_VALIDATION_SPLIT,1
**PartValidationSplit,1
*Height,100.0
*tFinal,0.0005
*Dt,1e-05
*OutputDir,<output_dir>
*MinElements,1
*End
```

- `*Mode` 블록의 `PART_VALIDATION_SPLIT,<modeid>` 첫 토큰으로 모드가, 둘째 토큰으로 모드 ID가 등록된다 (`KooMeshModifier.py:243-245`).
- `except_pids`가 있으면 `*ExceptPID,<p1>,<p2>,...` 라인이 추가된다 (`PartValidationWorkflow.py:243-244`).

## 4. 동작 원리 (코드 근거)

### 입력 트리거 / dispatch
- `*Mode` 블록 파싱에서 `part_validation_split` 토큰을 만나면 `modeList`에 `"PART_VALIDATION_SPLIT"`, `modeIDList`에 모드 ID를 등록한다: `KooMeshModifier.py:243-245`.
- 모드 실행 dispatch: `elif mode == "PART_VALIDATION_SPLIT": self.GeneratePartValidationSplit(modeid)` (`KooMeshModifier.py:2804-2806`). 출력 파일명 접미사로 `_pvsplit`이 붙는다.
- `GeneratePartValidationSplit`은 옵션에서 `output_dir`를 꺼내 `advancedModification.PartValidationSplit(curOption, output_dir)`를 호출한다 (`KooMeshModifier.py:2556-2559`).
- `PartValidationSplit`은 `KooPartValidator.split_parts_for_validation(...)`로 위임한다 (`KooDynaAdvancedModification.py:5181-5184`).

### 파트 분할 / skip 규칙 (`split_parts_for_validation`)
대상 선정 로직 (`KooPartValidator.py:82-117`):
- `except_pids`에 포함된 PID → skip (`:83-85`)
- 요소가 없거나 `min_elements` 미만 → skip (`:88-90`)
- 재료가 없거나 재료 이름에 `RIGID` 포함 → skip (`:93-100`)
- 파트 노드가 3개 미만 → skip (`:109-111`)
- 통과한 파트는 노드 좌표로 bounding box를 계산하고 (`:113-117`), `Part_<pid:06d>.k`로 출력 (`:120-138`)

Tied 접촉 정보는 모델 전체에서 수집되어 manifest의 `tied_contacts`에 기록된다 (`:54-66`, `:75`). (개별 파트 모델 자체에는 tied 접촉을 적용하지 않고 정보만 남김)

### 개별 파트 모델 생성 (`_write_single_part_model`, `KooPartValidator.py:279-496`)
각 파트 `.k`에 다음이 자동 작성된다.
- **CONTROL 카드**: `*CONTROL_TERMINATION`(tFinal) `:295-296`, `*CONTROL_TIMESTEP`(TSSFAC=0.67, ERODE=1) `:298-299`, `*CONTROL_HOURGLASS` `:301-302`, `*CONTROL_BULK_VISCOSITY` `:304-305`, `*CONTROL_CONTACT`(SOFT=2) `:307-308`, `*CONTROL_ENERGY` `:310-311`
- **DATABASE**: GLSTAT / MATSUM / RCFORC / BINARY_D3PLOT, 모두 출력 간격 `dt` `:313-317`
- **재료/섹션**: 원본 파트의 재료·섹션을 그대로 출력 `:319-325`
- **바닥판(Floor)**: 고유 ID `99000000 + pid` 기반의 `*MAT_ELASTIC`(강철 물성) + `*SECTION_SHELL` `:329-342`. 10×10 quad shell 메시를 파트 bbox 중심 아래 `bbox_min[2] - height` 위치에 생성하고 (`:404-438`), 바닥판 노드를 `*BOUNDARY_SPC_SET`으로 전 자유도 구속 `:440-453`. 바닥판 크기는 파트 bbox의 2배(최소 10mm) `:127-129`
- **요소 출력**: 첫 요소 타입으로 shell/solid 판별. shell은 `*ELEMENT_SHELL`(TRI3는 4번째 노드 중복) `:362-381`, solid는 `*ELEMENT_SOLID`(TETRA4/TETRA10/wedge6/hexa8 degenerate 처리) `:382-401`
- **초기속도**: 0도 자유낙하 Z속도 `vz = -sqrt(2 * g * height)`, `g = 9810 mm/s²`. 파트 노드셋에 `*INITIAL_VELOCITY` 적용 `:455-475`
- **접촉**: `*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE` (파트 노드셋 ↔ 바닥판 파트). OptCardA에 SOFT=2, DEPTH=35 설정 `:477-484`
- **중력**: `*LOAD_BODY_Z` (`g`) `:486-488`

### 부가 산출물 생성
- `validation_manifest.json`: 파트별 파일/요소수/노드수/bbox/노드 ID 범위 + tied 정보 `:140-159`
- `scenario.json`: `mode: "part_validation"` 검증 시나리오 `:161-166, 190-208`
- `run.sh`: Slurm array job(`--array=1-<total_parts>`), 파트별 LS-DYNA 실행 후 `status.txt`에 PASS/FAIL 기록 `:168-171, 211-276`

## 5. 주의사항 / 한계

- **강체(RIGID) 및 소형 파트는 자동 제외**된다 (`KooPartValidator.py:88-100, 109-111`). `min_elements` 미만, 노드 3개 미만, 재료 없음 파트도 skip.
- **바닥판 재료가 강철 고정값**으로 하드코딩되어 있다: `RHO=7.85E-09`, `E=2.0E+05`, `PR=0.3` (`KooPartValidator.py:336`). 단위계는 mm-ton-s-N(중력 9810 mm/s²)을 전제로 한다 (`:456`). 다른 단위계 모델에서는 부적절할 수 있다 — **확인 필요**.
- `floor_size` 옵션은 docstring에만 언급되며 실제 코드에서 읽지 않는다. 바닥판 크기는 항상 bbox 2배로 자동 계산된다 (`KooPartValidator.py:127-129`).
- 개별 파트 모델은 원본의 **tied 접촉/연결 관계를 적용하지 않는다**. tied 정보는 manifest에 기록만 되며, 검증은 각 파트를 단독으로 본다.
- 요소 출력 시 첫 요소 타입으로 shell/solid를 일괄 판별하므로, 한 파트에 shell·solid가 혼재하면 의도와 다르게 처리될 수 있다 (`KooPartValidator.py:362-401`) — **확인 필요**.
- 결과 해석 기준: PASS = 정상 종료(메시 문제 없음), FAIL = 비정상 종료(메시 품질 확인 필요). 모든 파트 PASS 시 전각도 낙하 진행 권장 (`Examples/part_validation/README.txt:83-88`).

## 6. 개발 현황

**구현됨.**

근거:
- 모드 등록·dispatch가 KooMeshModifier 본체에 존재: `KooMeshModifier.py:243-245, 2804-2806, 2556-2559`
- 분할 로직 전체 구현: `KooPartValidator.py:18-496` (파트 분할, 개별 모델 생성, manifest/scenario/run.sh 생성)
- KooChainRun prepare/submit/collect 워크플로우 구현: `Runner/PartValidationWorkflow.py`
- 동작 가능한 예제 제공: `Examples/part_validation/` (`scenario.json`, `README.txt`, `verify_tied_exclusion.py`)

단, `floor_size` 옵션은 docstring에만 있고 미구현(부분 불일치)이며, 바닥판 재료·단위계 가정은 고정값으로 일반화 여부는 확인 필요.
