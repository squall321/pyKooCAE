# KooMeshModifier 모드: THERMAL_LOAD

## 1. 목적 / 개요

`THERMAL_LOAD`는 고온/저온 챔버 환경의 **균일 온도 열응력**(P1, T1 단계)을 자동으로 LS-DYNA 카드로 적용하는 KooMeshModifier 모드다. 열전달 해석 없이, 전체 노드에 균일한 온도장(ΔT)을 부여하고 파트별 열팽창계수(CTE)로 열변형/열응력을 explicit 구조해석으로 계산한다.

핵심 emit 카드 (근거: `occProject/Generators/KooCAEManager/KooThermalLoad.py:9-12`):
- `*DEFINE_CURVE` — 온도 램프 곡선
- `*LOAD_THERMAL_VARIABLE` — 전 노드 온도장 `T = tb + ts·f(t)`
- `*MAT_ADD_THERMAL_EXPANSION` — 파트별 CTE

현재 P1 범위에서는 `ThermalType=UniformChamber`(균일 챔버 온도)만 지원하며, IC 발열(`ICPower`, P2) 등은 미구현이다 (근거: `KooThermalLoad.py:32-35`). CTE 열응력은 double precision이 필요하므로 `*_mpp_d.sif`(double SIF) 사용이 전제다 (근거: `KooThermalLoad.py:6-7`, `KooDynaAdvancedModification.py:5128-5129`).

## 2. 입력 옵션 · 인자 (표)

입력 .k 블록 `**ThermalLoad,<modeID>`에서 파싱되는 옵션 (근거: `KooMeshModifier.py:2319-2378`). 기본값은 동 블록의 `curOptions` 딕셔너리에서 발췌.

| 키워드 | 타입 | 기본값 | 의미 | 근거 |
|---|---|---|---|---|
| `ThermalType` | str | `UniformChamber` | 열하중 유형. P1은 `UniformChamber`만 지원 | `KooMeshModifier.py:2320,2366`; `KooThermalLoad.py:32-35` |
| `BaseTempC` | float | `25.0` | 초기/기준 온도 [°C] (t=0) | `KooMeshModifier.py:2321,2368`; `KooThermalLoad.py:37` |
| `TargetTempC` | float | `85.0` | 목표 온도 [°C] | `KooMeshModifier.py:2322,2370`; `KooThermalLoad.py:38` |
| `RampTimeS` | float | `1.0e-3` | 램프 시간 [s] = 해석 종료시간(tFinal) | `KooMeshModifier.py:2323,2372`; `KooThermalLoad.py:39`; `KooDynaAdvancedModification.py:5136` |
| `DT` | float | `1.0e-6` | explicit 출력/타임스텝 인자 | `KooMeshModifier.py:2324,2373`; `KooDynaAdvancedModification.py:5137` |
| `DefaultCTE` | float | `1.7e-5` | 미지정 파트의 기본 열팽창계수 [1/K] (일반 금속 ~17e-6/K) | `KooMeshModifier.py:2327,2376`; `KooThermalLoad.py:57` |
| `TempCurve` ... `EndTempCurve` | block `[t, factor]` | `[]` (빈 값) | 온도 곡선 직접 입력. 2점 이상이면 Base/Target/Ramp 기반 자동 램프를 무시 | `KooMeshModifier.py:2325,2345-2356`; `KooThermalLoad.py:42-48` |
| `PartCTE` ... `EndPartCTE` | block `pid,cte` | `{}` (빈 값) | 파트별 CTE 지정 [1/K]. 미지정 파트는 `DefaultCTE` 적용 | `KooMeshModifier.py:2326,2347-2364`; `KooThermalLoad.py:83-87` |

블록 종료는 `**EndThermalLoad`(또는 `**end`)이며, `$`로 시작하는 줄은 주석으로 무시된다 (근거: `KooMeshModifier.py:2336-2339`). 알 수 없는 옵션 줄은 경고만 출력하고 무시한다 (근거: `KooMeshModifier.py:2377-2378`).

> 확인 필요: `DT` 옵션은 `KooDynaAdvancedModification.ThermalLoad`에서 `SetControlandDatabaseExplicit(tFinal, dt)`의 `dt` 인자로 전달되나, `apply_thermal_load`(KooThermalLoad.py)의 `option` 처리에는 `DT` 키가 없다. 즉 `DT`는 카드 emit이 아닌 control/database 설정에만 사용된다.

## 3. 사용 예제

### 3-1. KooMeshModifier 입력 .k 블록

자동화 러너(`CumulativeScenarioRunner`)가 생성하는 실제 입력 형식 (근거: `Runner/CumulativeScenarioRunner.py:1310-1327`). `*Mode` 섹션에 모드 등록 → `**ThermalLoad,<id>` 옵션 블록 순서:

```
*Inputfile
<model_file>
*RunDirectoryMode,True,<output_dir>
*Mode
THERMAL_LOAD,1
**ThermalLoad,1
ThermalType,UniformChamber
BaseTempC,25
TargetTempC,85
RampTimeS,0.001
DT,1e-06
DefaultCTE,1.7e-05
PartCTE
1,2.3e-05
2,1.7e-05
EndPartCTE
**EndThermalLoad
*End
```

`PartCTE` 블록은 옵션이 비어 있으면 생략된다 (근거: `CumulativeScenarioRunner.py:1305-1308`). 모드 등록 트리거는 `*Mode` 섹션의 `thermal_load`(대소문자 무관) 토큰이다 (근거: `KooMeshModifier.py:327-329`).

### 3-2. scenario.json 매핑 (러너 경유)

`mode == "THERM"` 분기가 위 .k 블록을 생성한다. 값 우선순위는 step별 `params` > `simulation_params.thermal` > 기본값의 3단계다 (근거: `CumulativeScenarioRunner.py:1286-1302`).

| scenario.json 키 | .k 블록 옵션 | 기본값 |
|---|---|---|
| `thermal_type` | `ThermalType` | `UniformChamber` |
| `base_temp_C` (또는 `initial_temp_C`) | `BaseTempC` | `25` |
| `target_temp_C` | `TargetTempC` | `85` |
| `ramp_time_s` | `RampTimeS` | `1.0e-3` |
| `dt` | `DT` | `1.0e-6` |
| `default_cte_1_K` | `DefaultCTE` | `1.7e-5` |
| `part_cte` ({pid: cte}) | `PartCTE` 블록 | `{}` |

> 확인 필요: `Examples/` 하위에 THERMAL_LOAD를 직접 사용한 완성 scenario.json/입력 .k 예제 파일은 grep으로 발견되지 않았다. 위 예제는 러너 생성 템플릿(`CumulativeScenarioRunner.py`) 기반이다.

## 4. 동작 원리 (코드 근거)

1. **모드 등록**: `*Mode` 섹션에서 `thermal_load` 토큰 → `modeList`에 `"THERMAL_LOAD"` 추가 (`KooMeshModifier.py:327-329`).
2. **옵션 파싱**: `**ThermalLoad,<id>` 블록을 읽어 `curOptions` 딕셔너리 구성, `TempCurve`/`PartCTE`는 서브 블록(`in_curve`/`in_cte` 플래그)으로 파싱 (`KooMeshModifier.py:2316-2379`).
3. **디스패치**: `elif mode == "THERMAL_LOAD":` → `self.GenerateThermalLoad(modeid)` 호출, `_skip_default_write = True`로 기본 write 우회 (`KooMeshModifier.py:2876-2878`).
4. **핸들러**: `GenerateThermalLoad`가 `advancedModification.ThermalLoad(curOption, filePath)` 위임 (`KooMeshModifier.py:2453-2457`).
5. **카드 적용** (`KooDynaAdvancedModification.py:5124-5133` → `KooThermalLoad.apply_thermal_load`):
   - `*DEFINE_CURVE`: `_alloc_lcid`로 기존 max+1 LCID 할당, `CreateDefineCurvewithID`로 램프 곡선(`A1=[0, ramp]`, `O1=[0, 1]`) 생성. `ts=ΔT=Target-Base`, `tb=Base` (`KooThermalLoad.py:62-70`, `49-54`).
   - `*LOAD_THERMAL_VARIABLE`: `CreateLoadThermalVariable(ts, tb, lcid, nsid=0)` — NSID=0 이므로 전 노드에 `T = tb + ts·f(t)` 적용 (`KooThermalLoad.py:72-75`; `KooLoad.py:864-868`).
   - `*MAT_ADD_THERMAL_EXPANSION`: 모델 내 모든 PID 순회, `PartCTE`에 있으면 지정값, 없으면 `DefaultCTE`로 `CreateAddThermalExpansionMaterial(pid, lcid=0, mult=cte)` 호출 (`KooThermalLoad.py:78-87`; `KooMaterial.py:1070-1074`).
6. **control/database**: `RampTimeS`(tFinal)·`DT`로 `SetControlandDatabaseExplicit(tFinal, dt)` 호출 → `*CONTROL_TERMINATION`/`*CONTROL_TIMESTEP`/`*CONTROL_HOURGLASS` 등 explicit 카드 보존/생성 (`KooDynaAdvancedModification.py:5136-5139`, `1873-1902`).
7. **출력 (RunDirectoryMode)**: `runDirectoryMode == True`일 때 `Run_<id>/` 폴더 생성, `ThermalSet.k` write + `Output/` 폴더 + `.done` 플래그 파일 작성 (VibrationLoad/DROP 결 답습) (`KooDynaAdvancedModification.py:5146-5177`). 비 RunDirectoryMode면 `<filePath>_therm.k`로 단순 write (`:5178-5179`).

## 5. 주의사항 · 한계

- **ThermalType 제약**: `UniformChamber` 외 값(예: `ICPower`)은 `NotImplementedError` 발생 — P2(IC 발열)는 미구현 (`KooThermalLoad.py:32-35`).
- **double precision SIF 필수**: 단정밀(single) 빌드는 thermal을 거부하므로 scenario.json `environment`의 LS-DYNA SIF는 `*_mpp_d.sif`여야 한다 (`KooThermalLoad.py:6-7`; `KooDynaAdvancedModification.py:5128-5129`).
- **explicit only**: implicit 경로는 MPP_d 빌드의 `MPI_Comm_dup` 결함으로 회피하고 explicit 구조해석을 사용 (`KooThermalLoad.py:6`).
- **균일 온도 가정**: 전 노드 동일 ΔT (NSID=0) — 비균일 발열 분포(T2/T3)는 본 모드 범위 밖 (`KooThermalLoad.py:72-75`; PLAN 문서 `docs/PLAN_ThermalStress_Automation.md:55-58`).
- **파트 존재 필수**: 모델에 파트가 없으면 `ValueError` (`KooThermalLoad.py:80-82`).
- **TempCurve 의미 모호**: 곡선이 factor(0~1)인지 절대온도인지 분기는 있으나, 코드상 `ts/tb`는 항상 `Target-Base`/`Base`로 환산되어 emit된다. 절대온도 곡선 입력 시 의도와 다를 수 있음 — 확인 필요 (`KooThermalLoad.py:42-54`).

## 6. 개발 현황

**구현됨.**

근거:
- dispatch 분기(`KooMeshModifier.py:2876`) + 핸들러(`:2453` `GenerateThermalLoad`) + 위임 메서드 본체(`KooDynaAdvancedModification.py:5124` `ThermalLoad`) + 실제 카드 emit(`KooThermalLoad.py:18` `apply_thermal_load`)가 모두 존재.
- 등록부 분기(`KooMeshModifier.py:327`)와 dispatch 양쪽에 모두 존재 ("구현됨" 1차 조건 충족, `docs/PLAN_ThermalStress_Automation.md:41-42` 기준).
- 매뉴얼 dev_status에도 "구현됨"으로 등재 — `THERMAL_LOAD | 구현됨 | A:5124 ThermalLoad(LOAD_THERMAL_VARIABLE+CTE). git 177e332. M:2876/2453` (`docs/manual/02_KooMeshModifier/dev_status.md:182`).
- 커밋 `177e332`("고온 열응력(THERMAL_LOAD) 자동화")로 도입, e2e PASS가 git 메시지에 명시된 모드로 분류됨 (`dev_status.md:201,210`).

단, P1(T1 균일온도)만 구현이고 P2/P3(IC 발열 2-pass, 열응력→낙하 누적)은 PLAN 단계로 남아 있다 (`docs/PLAN_ThermalStress_Automation.md:497-531`).
