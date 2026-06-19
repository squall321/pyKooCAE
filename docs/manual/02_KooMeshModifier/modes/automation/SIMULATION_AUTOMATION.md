# KooMeshModifier 모드: SIMULATION_AUTOMATION

## 1. 목적 / 개요

`SIMULATION_AUTOMATION`은 외부 시나리오 JSON 파일(웹 UI 등에서 export)을 입력으로 받아, 시나리오별로 **run_id를 생성**하고 **시뮬레이션 설정 dict를 파싱·구성**하는 KooMeshModifier 모드다. 즉, 다수의 낙하(drop)/충격/누적 해석 케이스를 한 시나리오 묶음으로 정의하고, 각 케이스에 대해 분석 타입(`analysisType`)별 파라미터를 표준 config 구조로 변환하는 것이 핵심 역할이다.

처리 흐름 (코드 근거):
- 입력 .k 블록 `**SimulationAutomation,<modeID>`에서 `JsonFile` 경로를 읽음 (근거: `occProject/Generators/KooMeshModifier.py:371-391`)
- 해당 JSON을 시나리오 dict 리스트로 로드 (근거: `KooMeshModifier.py:2591-2603`, `KooMeshModifier.py:113-152`)
- 시나리오마다 `analysisType`을 분기하여 dataclass config로 파싱하고 run_id를 생성 (근거: `KooDynaAutomaticSimulationScriptGenerator.py:760-777`, `:733-757`)

지원하는 `analysisType` (근거: `KooDynaAutomaticSimulationScriptGenerator.py:12`, `:455-472`):
`fullAngleMBD`, `fullAngle`, `fullAngleCumulative`, `multiRepeatCumulative`, `partialImpact`, `mixedCumulative`.

> 주의: 이 모드의 핵심 워크 함수 `generate_for_all()`은 파싱된 config dict의 **리스트를 반환만** 하며, 호출부(`SimulationAutomation()`)는 그 반환값을 변수에 받지 않고 버린다 (근거: `KooDynaAdvancedModification.py:6392-6394`). 따라서 시나리오별 결과를 파일로 직접 쓰는 것은 아니고, 부수효과로 **run_id 생성(콘솔 출력)** 과, 모드 처리 후 공통 경로의 **`<input>_sa.k` 표준 출력**만 디스크에 남는다 (근거: `KooMeshModifier.py:2858-2860` `_sa` 접미사 + `:2885-2888` `WriteModifiedFile`). `runner_config.json`/`simulation_index.json`을 쓰는 메서드(`save_runner_config`, `save_simulation_index`)는 클래스에 존재하나 `generate_for_all` 경로에서는 호출되지 않는다 — **확인 필요**(별도 호출 경로 존재 여부).

## 2. 입력 옵션 · 인자 (표)

### 2-1. 입력 .k 블록 옵션

블록 `**SimulationAutomation,<modeID>` (파서는 공백/언더스코어 없는 `**simulationautomation` 소문자 매칭, 근거: `KooMeshModifier.py:371`). 종료는 `**End...`(또는 `**end`), `#`/`$` 시작 줄은 무시 (근거: `KooMeshModifier.py:381-386`).

| 키워드 | 타입 | 필수 | 의미 | 근거 |
|---|---|---|---|---|
| `JsonFile` | str (경로) | 예 | 시나리오 JSON 파일명. `curDir` 기준 상대경로로 해석 | `KooMeshModifier.py:387-389`, `:2596` |
| (자동) `MetaData` | dict | — | `*Info`/`*Creator` 등에서 채워진 모델 메타데이터가 자동 주입됨 (블록 옵션 아님) | `KooMeshModifier.py:390`, `:185-204` |

블록 내에서 인식되는 옵션은 `JsonFile` 단 하나다 (근거: `KooMeshModifier.py:387-389`). 다른 옵션 키는 분기 없이 무시된다.

### 2-2. 시나리오 JSON 공통 필드

최상위는 시나리오 dict의 **리스트**여야 한다(아니면 `ValueError`) (근거: `KooMeshModifier.py:134-135`). 각 항목 필드 (근거: `KooMeshModifier.py:142-150`, `KooDynaAutomaticSimulationScriptGenerator.py:252-259`):

| 필드 | 타입 | 기본값 | 의미 |
|---|---|---|---|
| `id` | str | `""` | 시나리오 식별자 |
| `name` | str | `"Unnamed"` | 시나리오 이름 |
| `fileName` | str | (입력 .k로 덮어씀) | 대상 모델 .k. 입력 .k가 있으면 `fileName`이 입력 파일명으로 강제 치환됨 (근거: `KooMeshModifier.py:2599-2601`) |
| `objFileName` | str | `None` | OBJ 형상 파일(MBD 등) |
| `analysisType` | str | `"fullAngleMBD"` | 분석 타입(아래 분기) |
| `params` | dict | `{}` | 타입별 세부 파라미터 |

### 2-3. `analysisType`별 `params` (코드 근거)

공통 낙하 파라미터 `_parse_common_drop` (근거: `KooDynaAutomaticSimulationScriptGenerator.py:50-72`):

| params 키 | 기본값 | 의미 |
|---|---|---|
| `heightMode` | `"const"` | `"const"` 또는 `"lhs"`(LHS 샘플링) |
| `heightConst` | `1.0` | 고정 낙하 높이 |
| `heightMin` / `heightMax` | `0.5` / `1.5` | LHS 범위(LHS에서 min>max면 자동 스왑) |
| `surface` | `"steelPlate"` | 바닥면 종류(`steelPlate`/`pavingBlock`/`concrete`/`wood`) |
| `tolerance` | (없음) | `{mode, faceTolerance, edgeTolerance, cornerTolerance}`. `mode="disabled"`면 무시 (근거: `:75-93`) |

타입별 추가 키:

| analysisType | 주요 params 키 (기본값) | 근거 |
|---|---|---|
| `fullAngleMBD` | `mbdCount`(1000), `angleSource`("lhs"), `angleSourceId`, `angleSourceFileName` | `KooDynaAutomaticSimulationScriptGenerator.py:264-281` |
| `fullAngle` | `faTotal`(100), `includeFace6`(True), `includeEdge12`(True), `includeCorner8`(True), `angleSource`("lhs"), `angleSourceId` | `:283-303` |
| `fullAngleCumulative` | `cumRepeatCount`(3), `cumDOECount`(5), `cumDirectionsGrid`([DOE][repeat]) 또는 `cumDirections`(1D) | `:305-353` |
| `multiRepeatCumulative` | `multiRepeatCount`(예 24), `multiRepeatDirections`(1D 리스트) | `:166-181`, parse 메서드 |
| `partialImpact` | `piMode`("default"/"txt"), `piTxtName` | `:385-393` |
| `mixedCumulative` | `projectName`, `doeCount`(1), `steps`[ {mode, condition, params} ] | `:395-452` |

`mixedCumulative`의 `steps[].mode`는 `DROP`/`DWI`/`STAT`/`THERM`/`VIB`/`COMB` 중 하나이며 내부에서 full name으로 매핑된다 (근거: `:21-30`, `:423`).

## 3. 사용 예제

> 전용 예제 존재: `Examples/alldropangles/` (입력 .txt + 시나리오 JSON + 실행 로그). 아래는 해당 폴더에서 거의 가공 없이 발췌.

### 3-1. KooMeshModifier 입력 (.txt/.k 블록)

`Examples/alldropangles/simulation_automation.txt` 원문:

```
*InputFile
MinimumModel.k
*RunDirectoryMode,True,Data/Results,Data/Metadata
*Info,M1,DV1
*Description,This test is for all angle drop simulation
*Creator,koo.park,koo.park@samsung.com,CAE,HE
*Mode
SIMULATION_AUTOMATION,1
**SimulationAutomation,1
JsonFile,scenarios_2025-10-06T22-11-57-014Z.json
**EndSimulationAutomation
*End
```

### 3-2. 시나리오 JSON

`Examples/alldropangles/scenarios_2025-10-06T22-11-57-014Z.json` 원문(2개 시나리오, `fullAngle`):

```json
[
  {
    "id": "scn_1759788630909_0",
    "name": "전각도 1차 낙하 시뮬레이션",
    "analysisType": "fullAngle",
    "params": {
      "faTotal": 100,
      "includeFace6": true,
      "includeEdge12": true,
      "includeCorner8": true,
      "angleSource": "lhs",
      "heightMode": "const",
      "heightConst": 1,
      "heightMin": 0.5,
      "heightMax": 1.5,
      "surface": "steelPlate",
      "tolerance": { "mode": "disabled" }
    }
  },
  {
    "id": "scn_1759788672969_1",
    "name": "전각도 2차 낙하 시뮬레이션",
    "analysisType": "fullAngle",
    "params": {
      "faTotal": 100,
      "angleSource": "usePrevResult",
      "angleSourceId": "scn_1759788630909_0",
      "surface": "steelPlate",
      "tolerance": { "mode": "disabled" }
    }
  }
]
```

### 3-3. 코드 내 다중 타입 샘플

소스 `__main__` 데모(`mixedCumulative` 포함, 근거: `KooDynaAutomaticSimulationScriptGenerator.py:923-996`)에서 발췌한 `mixedCumulative` 케이스:

```json
{
  "id": "5",
  "name": "Case5 - MixedCumulative (Thermal + Drop)",
  "analysisType": "mixedCumulative",
  "fileName": "model4.k",
  "params": {
    "projectName": "GalaxyS25",
    "doeCount": 3,
    "steps": [
      {"mode": "THERM", "condition": "HOT85", "params": {"target_temp_C": 85, "hold_time_s": 1800}},
      {"mode": "DROP",  "condition": "F1",    "params": {"height_mm": 1500, "surface": "steelPlate"}}
    ]
  }
}
```

## 4. 동작 원리 (file:line 근거)

1. **모드 등록 (트리거)** — `*Mode` 섹션에서 `simulation_automation` 문자열을 만나면 modeList에 `SIMULATION_AUTOMATION` 추가 (근거: `KooMeshModifier.py:312-314`).
2. **옵션 블록 파싱** — `**simulationautomation`(언더스코어 없는 형태로 매칭) 블록에서 `JsonFile`만 읽어 `curOptions["JsonFile"]`에 저장하고, 모델 메타데이터를 `curOptions["MetaData"]`로 주입 (근거: `KooMeshModifier.py:371-391`).
3. **디스패치** — 메인 루프에서 `elif mode == "SIMULATION_AUTOMATION": self.GenerateSimulationAutomation(modeid); additionalword += "_sa"` (근거: `KooMeshModifier.py:2858-2860`).
4. **JSON 로드 + fileName 치환** — `GenerateSimulationAutomation`이 `JsonFile` 경로를 `curDir` 기준으로 결합해 `LoadScenariosJson`으로 로드하고, 입력 .k가 있으면 모든 시나리오의 `fileName`을 입력 파일명으로 치환한 뒤 `advancedModification.SimulationAutomation(...)` 호출 (근거: `KooMeshModifier.py:2591-2603`). `LoadScenariosJson`은 파일 부재 시 `FileNotFoundError`, 최상위가 리스트가 아니면 `ValueError`를 던지고 필드 기본값을 보정 (근거: `KooMeshModifier.py:113-152`).
5. **시나리오 처리** — `SimulationAutomation`은 `KooDynaAutomaticSimulationScriptGenerator(jsonOptionList, metaData)`를 만들고 `generate_for_all()` 호출 (근거: `KooDynaAdvancedModification.py:6392-6394`).
6. **run_id 생성** — `generate_for_all`이 먼저 `generate_runids_for_all()`을 돌려 시나리오 타입별로 run_id를 생성한다. 개수 규칙: `fullAngleMBD` 1개, `fullAngle` `faTotal`개, `fullAngleCumulative` `cumRepeatCount×cumDOECount`개, `multiRepeatCumulative` `multiRepeatCount`개, `partialImpact` 1개, `mixedCumulative` `doeCount×totalSteps`개 (근거: `KooDynaAutomaticSimulationScriptGenerator.py:733-757`). run_id 포맷은 `YYYYmmdd_HHMMSS_<md5 6자리>` (근거: `:238-243`).
7. **타입별 config 파싱** — `parse_scenario_by_type`로 분기하여 각 dataclass config로 변환하고, `script_*` 메서드가 config를 dict로 직렬화하여 리스트로 반환 (근거: `:455-472`, `:760-777`, `:475-731`).
8. **표준 출력 .k 쓰기** — 모드 루프 종료 후 `_skip_default_write`가 설정되지 않았으므로 공통 `WriteModifiedFile("_sa")`가 실행되어 `<input>_sa.k`가 생성된다 (근거: `KooMeshModifier.py:2883-2891`, `:2906-2932`). 실제 로그에서 `Generate Modified File`와 run_id 다량 출력 확인 (근거: `Examples/alldropangles/simulation_automation.log:138-179`).

## 5. 주의사항 · 한계

- **결과 dict가 디스크에 저장되지 않음**: `generate_for_all()`의 반환 리스트(시나리오별 파싱 config)는 호출부에서 받지 않아 버려진다 (근거: `KooDynaAdvancedModification.py:6392-6394`). 이 모드의 실질 산출물은 (a) 콘솔에 출력되는 run_id, (b) 공통 경로의 `<input>_sa.k` 뿐이다 — **확인 필요**: 다운스트림(예: CumulativeScenarioRunner)이 run_id/config를 어떻게 소비하는지는 별도 모듈.
- **블록 키워드 표기**: 모드 트리거는 `simulation_automation`(언더스코어)이지만, 옵션 블록 파서는 `**simulationautomation`(언더스코어 없는 소문자) 부분일치로 매칭한다 (근거: `KooMeshModifier.py:312`, `:371`). 예제 .txt는 `**SimulationAutomation`(CamelCase)을 쓰며 `.lower()` 비교로 통과한다.
- **인식 옵션은 `JsonFile` 1개**: 다른 옵션 줄은 분기 없이 조용히 무시된다 (근거: `KooMeshModifier.py:387-389`에 다른 elif 없음).
- **`fileName` 강제 치환**: 입력 .k(`*InputFile`)가 주어지면 JSON의 `fileName`은 무시되고 입력 파일명으로 덮어써진다 (근거: `KooMeshModifier.py:2599-2601`).
- **JSON 포맷 엄격성**: 최상위가 리스트가 아니면 즉시 `ValueError`, 파일 부재면 `FileNotFoundError` (근거: `KooMeshModifier.py:128-135`).
- **이전 구현 잔존**: `SimulationAutomationPrevious`(예전 분기·`print` 위주) 및 `backup/` 디렉터리의 구버전 제너레이터가 남아 있으나 현재 디스패치 경로는 `SimulationAutomation`(신버전)만 사용한다 (근거: `KooDynaAdvancedModification.py:6396-6437`).
- `mixedCumulative`의 `steps`가 비면 기본 3-step(F1/E1/C1 DROP)이 자동 생성된다 (근거: `KooDynaAutomaticSimulationScriptGenerator.py:434-439`).

## 6. 개발 현황

**부분구현.**

근거:
- 모드 등록·블록 파싱·디스패치·JSON 로드·run_id 생성·타입별 config 파싱은 모두 구현되어 동작하며, 전용 예제와 실행 로그로 검증된다 (근거: `KooMeshModifier.py:312-314,371-391,2858-2860,2591-2603`; `KooDynaAutomaticSimulationScriptGenerator.py:733-777`; `Examples/alldropangles/simulation_automation.log:138-179`).
- 그러나 `generate_for_all()`의 파싱 결과가 호출부에서 소비/저장되지 않아(반환값 버림), 시나리오→실제 잡 생성으로 이어지는 산출물 연결이 모드 내부에서 닫혀 있지 않다 (근거: `KooDynaAdvancedModification.py:6392-6394`). `runner_config.json`/`simulation_index.json` 저장 메서드는 존재하나 본 경로에서 호출되지 않는다 (근거: `KooDynaAutomaticSimulationScriptGenerator.py:870-917`은 `generate_for_all`에서 미호출) — 이 연결부는 **확인 필요**.
