# KooMeshModifier 입력 .k 블록 문법

> 근거 코드: `occProject/Generators/KooMeshModifier.py` — 파서 진입점 `ImportOption()` (KooMeshModifier.py:154), 모드 등록 `*Mode` 블록 (KooMeshModifier.py:234-340), 모드별 `**<mode>` 옵션 블록 파서 (KooMeshModifier.py:341-2425), 디스패치 `GenerateModifiedFile()` (KooMeshModifier.py:2781).

---

## 1. 목적 / 개요

KooMeshModifier 는 LS-DYNA `.k` 모델 파일을 입력으로 받아, 별도의 **옵션 파일** 안에 기술된 커스텀 블록(모드 트리거 + 옵션 라인)에 따라 모델을 변형/생성하는 도구이다.

중요한 구분:

- **옵션 파일(실제로는 `.txt`)** — `*Inputfile`, `*Mode`, `**<mode>` 블록 등 KooMeshModifier 전용 키워드를 담는 제어 파일. CLI 인자로 직접 전달되며, 이 문서의 주제이다.
  - 근거: CLI 진입에서 `optionName = sys.argv[1]` 을 받아 `simGenerator.ImportOption(optionName)` 로 파싱한다 (KooMeshModifier.py:3143, 3161). 로그 파일명도 `optionName.replace(".txt", ".log")` 로 만든다 (KooMeshModifier.py:3150) — 실제 옵션 파일이 `.txt` 임을 전제.
- **입력 `.k`** — 옵션 파일의 `*Inputfile` 다음 줄에 적힌 실제 LS-DYNA 모델 (예: `MinimumModel.k`). 표준 LS-DYNA 카드로만 구성되며 커스텀 블록을 포함하지 않는다.
  - 근거: `*inputfile` 분기에서 다음 한 줄을 읽어 `self.inputFileName` 에 저장 (KooMeshModifier.py:163-166).

즉 "KooMeshModifier 가 읽는 커스텀 블록 문법"은 사실상 **옵션 파일(.txt) 문법**이며, 본 문서는 그 블록 문법(공통 표기법 + `*Mode` 트리거 + `**<mode>` 옵션 블록)을 코드 파서 기준으로 설명한다.

> 확인 필요: 제목은 "입력 .k 블록 문법"이나 코드상 옵션 파일은 `.txt` 확장자로 다루어진다(로그 파일명 변환 로직). 옵션 파일을 `.k` 로 넘겨도 파싱은 라인 기반이라 동작하지만, 로그 파일명 치환은 동작하지 않는다. 운영 표준 확장자는 코드 근거상 `.txt` 이다.

전체 실행 흐름 (KooMeshModifier.py:3157-3167):
`ImportOption()` (옵션 파싱) → `ImportBaseFile()` (입력 .k 로드) → `GenerateMetaData()` → `GenerateModifiedFile()` (등록된 모드 순차 실행).

---

## 2. 입력 옵션 · 인자 (표)

### 2.1 공통 표기법 (파서 규약)

모든 블록은 라인 단위로 `f.readline()` 후 `line.strip()` 으로 처리되며, 토큰은 **콤마(`,`) 구분**이다. 키워드 매칭은 **대소문자 무시** (`line.lower()` / `svector[0].lower()`).

| 규약 | 의미 | 코드 근거 |
|---|---|---|
| `*` 1개 접두 | 헤더/제어 키워드 (`*Inputfile`, `*Mode`, `*Info` 등) | KooMeshModifier.py:161-205 |
| `**` 2개 접두 | 모드별 옵션 블록 시작 (`**DropAttitude,<id>`) | KooMeshModifier.py:341-2425 |
| `**End...` | 옵션 블록 종료 마커 (내부적으로 `"**end" in line` 검사) | KooMeshModifier.py:351, 381, 466 등 |
| `,` | 토큰 구분자 (`line.split(",")`) | KooMeshModifier.py:242 등 전역 |
| `$` 로 시작 | 주석 (다수 블록에서 skip) | KooMeshModifier.py:355, 385, 470 등 |
| `#` 로 시작 | 주석 (다수 블록에서 skip) | KooMeshModifier.py:353, 383, 468 등 |
| 빈 줄 | 다수 블록에서 종료 또는 skip 처리 | KooMeshModifier.py:240, 349, 464 등 |

주의: 주석/빈 줄 처리는 **블록마다 다르다**. 예를 들어 `**DropAttitude` / `**Transform` 등 일부 블록은 빈 줄을 만나면 블록을 종료(`if not line: break`)하지만, `**VibrationLoad` / `**ThermalLoad` / `**MergeK` 같은 신형 블록은 빈 줄·`$` 를 skip 하고 `**End` 까지 계속 읽는다 (KooMeshModifier.py:2254 vs 2304). 안전하게는 블록 끝에 `**End<...>` 마커를 항상 넣는다.

### 2.2 헤더 / 제어 키워드 (`*`)

`ImportOption()` 의 최상위 분기에서 처리된다.

| 키워드 | 인자 형식 | 동작 | 코드 근거 |
|---|---|---|---|
| `*Inputfile` | 다음 줄에 파일명 | 입력 `.k` 파일명 지정 | KooMeshModifier.py:163-166 |
| `*InputObjFile` | 다음 줄에 파일명 | OBJ 입력 파일명 지정 | KooMeshModifier.py:167-170 |
| `*Step` | 다음 줄에 정수 | `advancedModification.step` 설정 | KooMeshModifier.py:171-174 |
| `*RunDirectoryMode` | `True/False[,결과경로,메타경로]` | run-디렉토리 모드 + 경로 | KooMeshModifier.py:175-184 |
| `*Info` | `,name,revision` | 모델명 / stage 메타데이터 | KooMeshModifier.py:185-190 |
| `*Description` | `,설명` | description 메타데이터 | KooMeshModifier.py:191-194 |
| `*Creator` | `,name[,email,group,team]` | 작성자 메타데이터 | KooMeshModifier.py:195-204 |
| `*PreserveIncludes` | 다음 줄들에 패턴(글롭/절대경로) | include 보존 패턴 등록, `*` 또는 빈 줄에서 종료 | KooMeshModifier.py:205-233 |
| `*Mode` | (블록) | 실행할 모드 등록 블록 시작 | KooMeshModifier.py:234-340 |
| `*End` | — | 파싱 종료 | KooMeshModifier.py:161-162 |

### 2.3 `*Mode` 블록 — 모드 트리거 키워드

`*Mode` 를 만나면 하위 줄을 읽어 `<MODE_KEYWORD>,<modeID>` 형식으로 모드를 등록한다. `*` 가 포함된 줄을 만나면 블록 종료(KooMeshModifier.py:238-239). 각 줄은 `svector = line.split(",")`, `svector[0]` 이 키워드, `svector[1]` 이 정수 modeID 다 (KooMeshModifier.py:242-245). 매칭 안 되면 `print("Invalid mode"); exit()` (KooMeshModifier.py:337-339).

등록 가능한 모드 트리거 키워드 (각각 대응 `**<mode>` 옵션 블록을 가짐). 근거: KooMeshModifier.py:243-336.

| 트리거 키워드 (대소문자 무시) | 등록 modeList 값 | 대응 옵션 블록 헤더 |
|---|---|---|
| `part_validation_split` | PART_VALIDATION_SPLIT | `**PartValidationSplit` |
| `elastic_to_rigid` | ELASTIC_TO_RIGID | `**ElasticToRigid` |
| `material_exchange` | MATERIAL_EXCHANGE | `**MaterialExchange` |
| `part_location_doe` | PART_LOCATION_DOE | `**PartLocationDOE` |
| `remesh_tetra` | REMESH_TETRA | `**RemeshTetra` |
| `rigidify_small_dt` | RIGIDIFY_SMALL_DT | `**RigidifySmallDT` (오타 호환: `**RigifySmallDT`) |
| `eroding_min_dt` | ERODING_MIN_DT | `**ErodingMinDT` |
| `part_exchange` | PART_EXCHANGE | `**PartExchange` |
| `part_morphing` | PART_MORPHING | `**PartMorphing` |
| `weak_coupling` | WEAK_COUPLING | (전용 블록 — 확인 필요) |
| `defeature_mesh` | DEFEATURE_MESH | `**DefeatureMesh` |
| `drop_attitude` | DROP_ATTITUDE | `**DropAttitude` (파서 매칭은 `*dropattitude`) |
| `translation_doe` | TRANSLATION_DOE | `**Translation_DOE` |
| `transform` | TRANSFORM | `**Transform` |
| `drop_weight_impact_test` | DROP_WEIGHT_IMPACT_TEST | `**DropWeightImpactTest` |
| `constrained_nodal_rigidbody_to_beam` | CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM | `**ConstrainedNodalRigidbodyToBeam` |
| `convert_cnrb_to_solid` | CONVERT_CNRB_TO_SOLID | `**ConvertCNRBtoSolid` |
| `warped_part` | WARPED_PART | `**WarpedPart` |
| `warped_to_initial_stress_part` | WARPED_TO_INITIAL_STRESS_PART | `**WarpedToInitialStressPart` |
| `dimensional_tolerance` | DIMENSIONAL_TOLERANCE | `**DimensionalTolerance` |
| `cohesive_between_conformal_meshes` | COHESIVE_BETWEEN_CONFORMAL_MESHES | `**CohesiveBetweenConformalMeshes` |
| `dynain_to_initial` | DYNAIN_TO_INITIAL | `**DynainToInitial` |
| `contact_auto_decomposition` | CONTACT_AUTO_DECOMPOSITION | `**ContactAutoDecomposition` |
| `simulation_automation` | SIMULATION_AUTOMATION | `**SimulationAutomation` |
| `remove_duplicate_tied_contacts` | REMOVE_DUPLICATE_TIED_CONTACTS | `**Remove_Duplicate_Tied_Contacts` |
| `fem_to_iga` | FEM_TO_IGA | `**FemToIGA` |
| `decompose_k` | DECOMPOSE_K | `**DecomposeK` |
| `vibration_load` | VIBRATION_LOAD | `**VibrationLoad` |
| `thermal_load` | THERMAL_LOAD | `**ThermalLoad` |
| `import_merge_k` | IMPORT_MERGE_K | `**ImportMergeK` |
| `merge_k` | MERGE_K | `**MergeK` |

> 매칭 순서 주의: `import_merge_k` 를 `merge_k` 보다 먼저 검사한다 (substring 충돌 방지, KooMeshModifier.py:330-336).

### 2.4 `**<mode>` 옵션 블록 — 파서 헤더 목록

`**<mode>,<modeID>` 헤더로 시작하며 `curOptions` 딕셔너리(또는 리스트)를 채워 `self.modeIDOption[curModeID]` 에 저장한다. 헤더 분기 위치 (근거: `grep elif "**"` 결과):

| 옵션 블록 헤더 (소문자 매칭) | 코드 위치 |
|---|---|
| `**remove_duplicate_tied_contacts` | KooMeshModifier.py:341 |
| `**simulationautomation` | KooMeshModifier.py:371 |
| `**contactautodecomposition` | KooMeshModifier.py:393 |
| `**dynaintoinitial` | KooMeshModifier.py:447 |
| `**cohesivebetweenconformalmeshes` | KooMeshModifier.py:514 |
| `**dimensionaltolerance` | KooMeshModifier.py:610 |
| `**warpedtoinitialstresspart` | KooMeshModifier.py:661 |
| `**warpedpart` | KooMeshModifier.py:720 |
| `**constrainednodalrigidbodytobeam` | KooMeshModifier.py:776 |
| `**convertcnrbtosolid` | KooMeshModifier.py:821 |
| `**partmorphing` | KooMeshModifier.py:875 |
| `**dropweightimpacttest` | KooMeshModifier.py:1040 |
| `**translation_doe` | KooMeshModifier.py:1254 |
| `**transform` | KooMeshModifier.py:1297 |
| `**elastictorigid` | KooMeshModifier.py:1329 |
| `*dropattitude` | KooMeshModifier.py:1347 |
| `**defeaturemesh` | KooMeshModifier.py:1616 |
| `**materialexchange` | KooMeshModifier.py:1645 |
| `**partlocationdoe` | KooMeshModifier.py:1696 |
| `**erodingmindt` | KooMeshModifier.py:1779 |
| `**rigifysmalldt` / `**rigidifysmalldt` | KooMeshModifier.py:1800 |
| `**remeshtetra` | KooMeshModifier.py:1831 |
| `**partvalidationsplit` | KooMeshModifier.py:1870 |
| `**partexchange` | KooMeshModifier.py:1907 |
| `**femtoiga` | KooMeshModifier.py:2125 |
| `**decomposek` | KooMeshModifier.py:2176 |
| `**vibrationload` | KooMeshModifier.py:2234 |
| `**thermalload` | KooMeshModifier.py:2315 |
| `**importmergek` | KooMeshModifier.py:2381 |
| `**mergek` | KooMeshModifier.py:2402 |

> 주의 (불일치): `DROP_ATTITUDE` 의 옵션 블록 매칭은 다른 모드와 달리 단일 `*` 인 `*dropattitude` 로 검사된다 (KooMeshModifier.py:1347). 다만 `**` 로 시작하는 줄도 `"*dropattitude" in line.lower()` 검사를 통과하므로 예제처럼 `**DropAttitude,1` 로 적어도 매칭된다 (실제 예제 동작 확인됨, 아래 3.1).

### 2.5 대표 블록별 옵션 라인

#### `**DropAttitude` (낙하 자세 DOE) — KooMeshModifier.py:1347-1476

| 옵션 라인 | 형식 | 의미 | 근거 |
|---|---|---|---|
| `runid` | `runid,id1,id2,...` | 생성할 run id 목록 | 1363-1366 |
| `EulerRolling` / `EulerPitching` / `EulerYawing` | `key,v1,v2,...` | 오일러 각 리스트 | 1367-1387 |
| `Height` | `Height,h1,h2,...` | 낙하 높이 리스트 | 1388-1394 |
| `InitialVelocityX/Y/Z` | `key,v1,...` | 초기 병진 속도 리스트 | 1395-1415 |
| `InitialAngularVelocityX/Y/Z` | `key,v1,...` | 초기 각속도 리스트 | 1416-1436 |
| `OffsetDistance` | `OffsetDistance,d` | 바닥 오프셋 (생략시 1e-9) | 1437-1443 |
| `Density` / `YoungsModulus` / `PoissonRatio` | `key,value` | 바닥판 물성 | 1444-1455 |
| `tFinal` / `dt` | `key,value` | 종료시간 / 출력 dt | 1456-1463 |
| `DropSurface` | `DropSurface,Plane,xL,yL,zL,nx,ny,nz` 또는 `DropSurface,RigidWall` | 바닥면 정의 | 1464-1476 |

#### `**Transform` (좌표 변환) — KooMeshModifier.py:1297-1327
`curOptions` 가 **리스트**이며 변환 항목을 누적한다.

| 옵션 라인 | 형식 | 근거 |
|---|---|---|
| `Translation` | `Translation,dx,dy,dz` | 1308-1310 |
| `VectorToVectorRotation` | `...,ax,ay,az,bx,by,bz` | 1311-1313 |
| `VectorRotation` | `VectorRotation,x,y,z` | 1314-1316 |
| `Rotation` | `Rotation,rx,ry,rz` | 1317-1319 |
| `Scale` | `Scale,sx,sy,sz` | 1320-1322 |
| `Mirror` | `Mirror,plane` | 1323-1325 |

#### `**DynainToInitial` — KooMeshModifier.py:447-512

| 옵션 라인 | 형식 / 기본값 | 근거 |
|---|---|---|
| `*DynainPath` | 경로 (기본 `dynain`) | 472-474 |
| `*IncludeStress` | `True/False` (기본 True) | 475-480 |
| `*RemoveDynamicRelaxation` | `True/False` (기본 True) | 481-486 |
| `*DynamicRelaxation` | `True/False` (기본 False) | 487-492 |
| `*MovetoOriginbyNode` | `,node1,node2,...` | 493-495 |
| `*MovetoOriginAutomatic` | `True/False` | 496-501 |
| `*RemovePartbyName` | `,name1,...` | 502-504 |
| `*RemovePartbyID` | `,id1,...` | 505-507 |
| `*RemoveContactbyID` | `,id1,...` | 508-510 |

#### `**VibrationLoad` — KooMeshModifier.py:2234-2313
단일 라인 옵션 + 멀티라인 서브블록(`LoadCurve`...`EndLoadCurve`, `PartFactors`...`EndPartFactors`, `PartList`...`EndPartList`).

| 옵션 | 형식 / 기본값 | 근거 |
|---|---|---|
| `Direction` | `Direction,X/Y/Z` (기본 Z) | 2300-2301 |
| `LoadType` | `LoadType,Force/Acceleration` (기본 Force) | 2302-2303 |
| `RelativeMode` | `RelativeMode,Explicit/...` (기본 Explicit) | 2304-2305 |
| `ReferencePart` | `ReferencePart,pid` | 2306-2310 |
| `LoadCurve` 블록 | 각 줄 `time,value` | 2267, 2274-2281 |
| `PartFactors` 블록 | 각 줄 `pid,factor` | 2269, 2282-2289 |
| `PartList` 블록 | `pid,pid,...` | 2271, 2290-2298 |

#### `**ThermalLoad` — KooMeshModifier.py:2315-2379

| 옵션 | 형식 / 기본값 | 근거 |
|---|---|---|
| `ThermalType` | (기본 `UniformChamber`) | 2365-2366 |
| `BaseTempC` | float (기본 25.0) | 2367-2368 |
| `TargetTempC` | float (기본 85.0) | 2369-2370 |
| `RampTimeS` | float (기본 1e-3) | 2371-2372 |
| `DT` | float (기본 1e-6) | 2373-2374 |
| `DefaultCTE` | float (기본 1.7e-5) | 2375-2376 |
| `TempCurve` 블록 | `time,temp` (…`EndTempCurve`) | 2345, 2349-2356 |
| `PartCTE` 블록 | `pid,cte` (…`EndPartCTE`) | 2347, 2357-2364 |

#### `**MergeK` — KooMeshModifier.py:2402-2425

| 옵션 | 형식 | 근거 |
|---|---|---|
| `OutputFile` | `OutputFile,name.k` | 2417-2418 |
| `ForceInlineIGA` | `True/False` | 2419-2420 |
| `ForceInlinePreserved` | `True/False` | 2421-2422 |

> 그 외 블록(`**ContactAutoDecomposition`, `**SimulationAutomation`, `**CohesiveBetweenConformalMeshes`, `**PartMorphing`, `**DropWeightImpactTest` 등)은 동일한 `key,value` / 서브블록 패턴을 따른다. 상세 옵션은 각 블록의 해당 코드 위치(2.4 표)를 참조.

---

## 3. 사용 예제 (Examples 발췌, 가공 최소)

### 3.1 DROP_ATTITUDE (낙하 자세)
출처: `Examples/alldropangles/drop_attitude.txt` (전문)

```text
*Inputfile
MinimumModel.k
*RunDirectoryMode,True,Data/Results,Data/Metadata
*Info,M1,DV1
*Description,This test is for all angle drop simulation
*Creator,koo.park,koo.park@samsung.com,CAE,HE
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,108.40071741034467,-96.70843214185096,-76.59377879667808,-125.61536660977404,-56.374472229421784
EulerPitching,-42.36402149151405,89.103109042852,118.03981116648316,-55.28417846337655,-31.482711446670237
EulerYawing,-31.743116623073632,-24.386690831421987,-95.7845750744738,35.8382994586413,-137.50294620672634
Height,1500,1500,1500,1500,1500
InitialVelocityX,0,0,0,0,0
InitialVelocityY,0,0,0,0,0
InitialVelocityZ,0,0,0,0,0
InitialAngularVelocityX,0,0,0,0,0
InitialAngularVelocityY,0,0,0,0,0
InitialAngularVelocityZ,0,0,0,0,0
OffsetDistance,0.1
Density,2700
YoungsModulus,70000000000
PoissonRatio,0.3
tFinal,0.001
dt,0.000001
**EndDropAttitude
*End
```

### 3.2 DYNAIN_TO_INITIAL
출처: `Examples/alldropangles/DynainToInitial.txt` (전문)

```text
*Inputfile
MinimumModel_001_DA_EX_108.401_EY_-42.364_...k
*Mode
DYNAIN_TO_INITIAL,1
**DynainToInitial,1
*DynainPath,dynain
*IncludeStress,True
*RemoveDynamicRelaxation,True
*MovetoOriginAutomatic,True
*RemovePartbyID,23
**EndDynainToInitial
*End
```

### 3.3 VIBRATION_LOAD (가속도 입력)
출처: `Examples/vibration_load/vibration_acceleration.txt` (전문)

```text
*Inputfile
MinimumModel.k
*Info,VibTest,DV1
*Description,Vibration load (acceleration input) - Y-axis sine pulse
*Creator,user,user@example.com,CAE,Team
*Mode
VIBRATION_LOAD,1
**VibrationLoad,1
Direction,Y
LoadType,Acceleration
RelativeMode,Explicit
LoadCurve
0.0, 0.0
0.0005, 9810.0
0.001, 0.0
0.0015, -9810.0
0.002, 0.0
EndLoadCurve
PartFactors
1, 1.0
2, 1.0
3, 1.0
EndPartFactors
**EndVibrationLoad
*End
```

### 3.4 SIMULATION_AUTOMATION
출처: `Examples/alldropangles/simulation_automation.txt` (전문)

```text
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

### 3.5 CLI 실행
근거: KooMeshModifier.py:3142-3147 (인자 처리), 3161 (`ImportOption`).

```bash
# argv[1] = 옵션 파일, argv[2](선택) = 작업 디렉토리
KooMeshModifier drop_attitude.txt /path/to/workdir
# argv[2] 생략 시 현재 디렉토리 사용 (os.path.curdir)
KooMeshModifier drop_attitude.txt
```
로그는 `<옵션파일>.log` 로 작업 디렉토리에 기록된다 (KooMeshModifier.py:3150-3153).

---

## 4. 동작 원리 (코드 근거)

1. **진입**: CLI 가 `optionName`(argv[1])과 `curDir`(argv[2] 또는 현재 dir)를 결정하고 (KooMeshModifier.py:3142-3147) `KooMeshModifier()` 인스턴스를 만들어 `ImportOption(optionName)` 을 호출 (KooMeshModifier.py:3157-3161).
2. **옵션 파싱**: `ImportOption()` 은 파일을 열어 한 줄씩 읽으며 (`f.readline()`), `*end` 가 나올 때까지 `while True` 루프를 돈다 (KooMeshModifier.py:154-162). 최상위 분기에서 `*` 헤더들을 처리하고, `*mode` 분기에서 내부 루프로 모드를 등록 (`self.modeList.append(...)`, `self.modeIDList.append(int(svector[1]))`) 한다 (KooMeshModifier.py:234-340).
3. **옵션 블록**: 이후 `**<mode>` 헤더를 만나면 해당 `elif` 분기가 `curModeID = int(svector[1])` 를 읽고 (KooMeshModifier.py:342-343 등), 내부 `while True` 루프에서 `**end` 까지 옵션 라인을 파싱해 `self.modeIDOption[curModeID] = curOptions` 로 저장한다 (예: KooMeshModifier.py:369, 391, 512, 2313, 2379, 2425). 각 블록 처리 후 최상위 루프 끝에서 `line = f.readline()` 으로 다음 줄을 읽어 진행한다 (KooMeshModifier.py:2427-2433).
4. **숫자 파싱**: 좌표/속도 등은 `KooDynaFloat()` / `KooDynaInt()` 로 변환된다 (예: TRANSFORM, KooMeshModifier.py:1310; DROP_ATTITUDE, KooMeshModifier.py:1371). VibrationLoad/ThermalLoad 는 표준 `float()` 사용 (KooMeshModifier.py:2278, 2368).
5. **디스패치/실행**: `GenerateModifiedFile()` 이 `for i in range(len(self.modeList))` 로 등록 순서대로 모드를 실행한다. `mode` 문자열에 따라 대응 `Generate<Mode>(modeid)` 를 호출하고 출력 파일명 접미사(`additionalword`)를 누적한다 (KooMeshModifier.py:2781-2814 …). 각 `Generate*` 는 `self.modeIDOption[modeid]` 를 꺼내 `advancedModification` 의 실제 변형 함수에 위임한다 (예: `GenerateVibrationLoad` → `advancedModification.VibrationLoad(...)`, KooMeshModifier.py:2447-2451).

---

## 5. 주의사항 · 한계

- **확장자**: 옵션 파일은 코드상 `.txt` 를 전제로 한다(로그 파일명 치환 KooMeshModifier.py:3150). 본 매뉴얼 제목의 "입력 .k"는 `*Inputfile` 이 가리키는 모델 `.k` 와 구분해야 한다.
- **모드 매칭은 substring 기반**: `if "<keyword>" in svector[0].lower()` 방식이라 부분 문자열 충돌 위험이 있다. 코드가 명시적으로 `import_merge_k` 를 `merge_k` 보다 먼저 검사하는 이유 (KooMeshModifier.py:330-336). 새 키워드 추가 시 충돌 주의.
- **잘못된 모드**: `*Mode` 블록에서 알 수 없는 키워드를 만나면 `print("Invalid mode"); exit()` 로 프로세스가 즉시 종료된다 (KooMeshModifier.py:337-339).
- **빈 줄/주석 처리 비일관성**: 구형 블록(`**DropAttitude`, `**Transform`)은 빈 줄에서 블록을 닫고, 신형 블록(`**VibrationLoad`, `**ThermalLoad`, `**MergeK`)은 빈 줄을 skip 한다 (KooMeshModifier.py:1359-1360 vs 2254). 멀티라인 LoadCurve 등에 빈 줄을 넣을 때 구형/신형 구분 필요. 항상 `**End<...>` 마커를 명시할 것.
- **DropAttitude 헤더 매칭의 단일 `*`**: 다른 블록과 달리 `*dropattitude` 로 검사되므로 (KooMeshModifier.py:1347), 헤더 철자에 다른 `*<something>` 키워드 substring 이 섞이지 않도록 주의.
- **modeID 무결성**: `svector[1]` 을 `int()` 로 강제 변환하므로 modeID 누락/비정수 시 예외 발생 (KooMeshModifier.py:245 등).
- **옵션 파일과 .k 동일 디렉토리 가정**: `ImportOption()` 이 `os.path.join(self.curDir, fileName)` 으로 경로를 구성한다 (KooMeshModifier.py:155).

---

## 6. 개발 현황

**구현됨**

근거:
- 옵션 파서 `ImportOption()` 및 `*Mode` / `**<mode>` 블록 분기 30종이 코드에 존재하고 (KooMeshModifier.py:234-2425), 디스패치 `GenerateModifiedFile()` 가 이를 실행한다 (KooMeshModifier.py:2781~).
- 실제 동작하는 입력 예제가 리포지토리에 존재: `Examples/alldropangles/drop_attitude.txt`, `Examples/alldropangles/DynainToInitial.txt`, `Examples/alldropangles/simulation_automation.txt`, `Examples/vibration_load/vibration_acceleration.txt` (및 `vibration_volume.txt`, `vibration_explicit.txt`).
- 최근 커밋 이력(`THERMAL_LOAD`, `VIBRATION_LOAD`, IMPACT 관련 e2e PASS)이 신형 블록의 동작 검증을 시사.

**부분 / 확인 필요**

- `WEAK_COUPLING` 트리거는 `*Mode` 에 등록되나 (KooMeshModifier.py:270-272) 전용 `**weakcoupling` 옵션 블록 헤더는 `grep elif "**"` 결과에 없음 — 옵션 블록 없이 디스패치만 되는지 **확인 필요**.
- 옵션 파일 표준 확장자(`.txt` vs `.k`) — 코드는 `.txt` 전제, 제목은 `.k`. 운영 컨벤션 **확인 필요**.
- 각 `**<mode>` 블록의 전체 옵션 라인은 대표 블록만 표로 정리함. 나머지 블록의 세부 옵션은 2.4 표의 코드 위치에서 직접 확인 필요.
