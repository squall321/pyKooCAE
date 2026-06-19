# KooMeshModifier 모드: DROP_WEIGHT_IMPACT_TEST

## 1. 목적 / 개요

`DROP_WEIGHT_IMPACT_TEST` 는 기존 모델(시편)에 **충격추(impactor) + 바닥판(wall)** 지오메트리를 자동으로 생성·결합하여
낙하/충격 시험(drop weight impact test) 해석용 LS-DYNA 입력 모델을 만드는 KooMeshModifier 모드입니다.

주요 동작:
- 충격추(Sphere / Cylinder)를 OCC 모듈로 생성 후 테트라 메시화하여 신규 파트로 추가
- 바닥판(Wall, 강체) 박스 메시 생성 + 구속(PRESCRIBED_MOTION_RIGID 고정)
- 충격추-시편, 바닥판-시편 간 자동 접촉(`CONTACT_AUTOMATIC_SURFACE_TO_SURFACE`) 생성
- 자유낙하 높이(Height) → 초기 속도 v=√(2gh) 환산 후 `INITIAL_VELOCITY_GENERATION` 부여
- `CONTROL_TERMINATION` / `CONTROL_TIMESTEP` 등 explicit 제어 카드 세팅
- 충격 위치(LocationX/Y) 리스트만큼 DOE(여러 변형 모델) 생성

세 가지 생성 방식(`GenerationMode`)이 있으며 dispatch 분기에서 분리됩니다
(`occProject/Generators/KooMeshModifier.py:2484-2489`):
- **DampingSpring** (기본) → `DropWeightImpactTest()` — 주 경로. Sphere/Cylinder, 3단 실린더, FastDOE 지원
- **OutsideRigidElement / OutsideRigidPart** → `DropWeightImpactTestwithPartialRigid()` — 충격점 외곽 부분 강체화
- **Part** → `DropWeightImpactTestbyPart()` — 파트별 + LocationMode(예: 3X3) 격자 충격

> 입력 트리거: `drop_weight_impact_test` (modeList 등록, `KooMeshModifier.py:285-287`),
> 입력 블록 키워드 `**DropWeightImpactTest` (파싱, `KooMeshModifier.py:1040`).

## 2. 입력 옵션 · 인자

KooMeshModifier 입력 `.k`(텍스트) 블록은 `**DropWeightImpactTest,<modeid>` ~ `**EndDropWeightImpactTest` 사이에
`키,값[,값…]` 줄로 기술합니다. 파싱은 `KooMeshModifier.py:1040-1252`, 기본값/소비는 `KooDynaAdvancedModification.py:3596-3752`.

| 키워드 | 의미 | 기본값 | 근거(file:line) |
|---|---|---|---|
| `GenerationMode` | 생성 방식: `DampingSpring`/`OutsideRigidElement`/`OutsideRigidPart`/`Part` | `DampingSpring` | KooMeshModifier.py:1050, 1066-1068 |
| `Type` | 충격추 형상: `Sphere` / `Cylinder` | `Sphere` | KooMeshModifier.py:1214-1217 / AdvMod:3705-3708 |
| `Dimension` | 형상 치수. Sphere=`[radius]`. Cylinder 2단=`[r,outerR,hFront,hBack,backR]`(5값), 3단=`[r,outerR,hFront,midR,hMid,backR,hBack]`(7값) | `[0.008]` | KooMeshModifier.py:1225-1241 / AdvMod:4069-4096 |
| `DimensionDamper` | 댐퍼(beam) 단면 `[width, height, offset]` | `[0.001,0.001,0.001]` | KooMeshModifier.py:1218-1224 / AdvMod:3720-3726 |
| `MeshSize` | 충격추 테트라 메시 크기 | `0.001` | KooMeshModifier.py:1248-1251 / AdvMod:3715-3718 |
| `LocationX` / `LocationY` | 충격 위치 X/Y 좌표 리스트(DOE) | `[0.0]` | KooMeshModifier.py:1164-1177 / AdvMod:3610-3617 |
| `Height` | 낙하 높이 리스트(위치와 1:1) | `[0.5]` | KooMeshModifier.py:1178-1184 / AdvMod:3743-3746 |
| `InitialVelocityX/Y/Z` | 추가 초기 속도 리스트 | `[0.0]` | KooMeshModifier.py:1185-1205 / AdvMod:3728-3741 |
| `tFinal` | 해석 종료 시간(CONTROL_TERMINATION) | `0.0` | KooMeshModifier.py:1206-1209 / AdvMod:3598-3601 |
| `dt` | 출력 시간 간격(DATABASE) | `1.0e-6` | KooMeshModifier.py:1210-1213 / AdvMod:3602-3605 |
| `OffsetDistance` | 충격추-시편 초기 간격 | `1e-9`(파서) / `1e-11`(소비측 fallback) | KooMeshModifier.py:1069-1075 / AdvMod:3748-3751 |
| `BoundaryDistance` | 응력파 흡수/강체화 경계 거리(0=비활성) | `0.0` | KooMeshModifier.py:1080-1083 / AdvMod:3606-3609 |
| `StressWaveVelocity` + `DistanceMargin` | BoundaryDistance=0 일 때 `stressWaveDistance = v·tFinal·margin` 로 자동 산출 | `0.0` | KooMeshModifier.py:1062-1079 / AdvMod:3811-3816 |
| `MaterialIDImpactor` / `…ImpactorFront` / `…ImpactorMid` / `…Damper` / `…Wall` | 기존 모델의 재질 ID 재사용(0=신규 생성) | `0` | KooMeshModifier.py:1120-1137 / AdvMod:3622-3640 |
| `YoungModulus*` / `PoissonRatio*` / `Density*` (Impactor/ImpactorFront/ImpactorMid/Damper/Wall) | 신규 재질 물성 | E≈2.07e11, ν=0.3, ρ=7800(impactor) / Wall·Damper ρ=1000 등 | KooMeshModifier.py:1084-1155 / AdvMod:3643-3702 |
| `WallNumX/Y/Z` | 바닥판 박스 요소 분할 수 | `10` | KooMeshModifier.py:1242-1247 / AdvMod:3756-3758 |
| `PartIDs` | (Part 모드) 충격 대상 파트 ID 리스트 | `[]` | KooMeshModifier.py:1156-1159 |
| `LocationMode` | (Part 모드) 격자 패턴(예: `3X3`) | `[]` | KooMeshModifier.py:1160-1163 / AdvMod:4487-4488 |

> 참고: 예제 `.txt` 에는 `YoungModulus`/`Density`/`PoissonRatio`(접미사 없는 형태)도 보이지만,
> 파서가 처리하는 키는 위 표의 접미사 포함 키(`YoungsModulusImpactor` 등)입니다 — `KooMeshModifier.py:1084-1155`.
> 접미사 없는 줄은 `*impactor` 등 부분일치로 매칭되거나 무시될 수 있어 **확인 필요**.

### scenario.json 경유(KooChainRun) 키
KooChainRun 의 `mode: "drop_weight_impact"` / `mode_sequence: ["IMPACT"]` 시나리오는 위 `.k` 블록으로 변환되어 사용됩니다.
주요 매핑: `simulation_params.impact.{type,height,mesh_size,tFinal,dt,offset_distance,cylinder_stages}`,
`simulation_params.wall.{density,youngs_modulus,poisson,num_x/y/z}`, `locations`(grid/list/lhs), `generation_mode`, `boundary_distance`.
(예제: `Examples/drop_weight_impact/scenario.json`, `Examples/scenario_examples/impact_cylinder_8pi.json`)
> scenario→`.k` 변환 코드 자체는 본 모드 범위 밖(KooChainRun/Designer)이라 매핑 세부는 **확인 필요**.

## 3. 사용 예제

### 3-1. 구(Sphere) — KooMeshModifier 입력 `.k` 블록
출처: `occProject/Generators/dist/Examples/5.SimulationModify/DropWeightImpactTest.txt`
```
*Inputfile
MultiscaleTest_1_unitfeature.k
*Mode
DROP_WEIGHT_IMPACT_TEST,1
**DropWeightImpactTest,1
BoundaryDistance,0.0
LocationX,0.02,0.01
LocationY,0.00,0.01
InitialVelocityX,0.00,0.00
InitialVelocityY,0.00,0.00
InitialVelocityZ,0.00,0.00
Height,0.5,0.5
tFinal,0.001
YoungModulusDamper,70e9
PoissonRatioDamper,0.3
Density,2700
YoungModulus,201e9
DensityDamper,7800
PoissonRatio,0.3
Type,Sphere
DimensionDamper,0.0001,0.0001,0.01
Dimension,0.008
MeshSize,0.001
**EndDropWeightImpactTest
*End
```

### 3-2. 실린더(2단) 블록
출처: `…/DropWeightImpactTestCylinder.txt`
```
**DropWeightImpactTest,1
BoundaryDistance,0.01
OffsetDistance,0.00001
Type,Cylinder
Dimension,0.008,0.01,0.005,0.02,0.012
MeshSize,0.002
...
```

### 3-3. Part 모드(LocationMode 격자) 블록
출처: `…/DropWeightImpactTestbyPart.txt`
```
**DropWeightImpactTest,1
GenerationMode,Part
PartIDs,1
LocationMode,3X3
Height,0.5
tFinal,0.001
Type,Sphere
Dimension,0.008
MeshSize,0.001
OffsetDistance,0.00001
**EndDropWeightImpactTest
```

### 3-4. scenario.json (KooChainRun, 8파이 3단 실린더)
출처: `Examples/scenario_examples/impact_cylinder_8pi.json` (발췌)
```json
"simulation_params": {
  "impact": {
    "type": "cylinder", "height": 200, "mesh_size": 2,
    "tFinal": 0.001, "dt": 1e-06, "offset_distance": 0.01,
    "cylinder_stages": [
      {"role": "front", "diameter": 8,  "outer_diameter": 20, "height": 6,  "density": 1.18e-09, "youngs_modulus": 100.0,    "poisson": 0.49},
      {"role": "mid",   "diameter": 20, "height": 14, "density": 6.57e-09, "youngs_modulus": 207000.0, "poisson": 0.3},
      {"role": "back",  "diameter": 44.5, "height": 38.003, "density": 6.57e-09, "youngs_modulus": 207000.0, "poisson": 0.3}
    ]
  },
  "wall": {"density": 1e-09, "youngs_modulus": 10000.0, "poisson": 0.3, "num_x": 20, "num_y": 20, "num_z": 4}
}
```

## 4. 동작 원리 (코드 근거)

1. **입력 트리거·파싱**
   - modeList 등록: `KooMeshModifier.py:285-287` (`drop_weight_impact_test` → `DROP_WEIGHT_IMPACT_TEST`).
   - 블록 파싱: `KooMeshModifier.py:1040-1252` — 기본값 세팅 후 `키,값` 줄을 소문자 부분일치로 분기 파싱, `self.modeIDOption[curModeID]` 에 저장.

2. **dispatch**
   - `GenerateModifiedFile` 루프에서 `mode == "DROP_WEIGHT_IMPACT_TEST"` → `GenerateDropWeightImpactTest()` 호출, suffix `_dwit` 부여 (`KooMeshModifier.py:2828-2830`).
   - `GenerateDropWeightImpactTest()` 가 `curOption["Mode"]` 로 3분기 (`KooMeshModifier.py:2484-2489`).

3. **모델 생성 (DampingSpring 주 경로, `KooDynaAdvancedModification.py:3596`~)**
   - 모든 기존 파트로 PartSet + `INTERFACE_SPRINGBACK_LSDYNA` 생성 (`:3804-3808`).
   - explicit 제어 카드 세팅: `SetControlandDatabaseExplicit(tfinal, dt)` → CONTROL_TERMINATION(ENDTIM), TIMESTEP(TSSFAC=0.7), HOURGLASS(IHQ=5) (`:3820`, 정의 `:1873-1892`).
   - 충격추/댐퍼/바닥판 신규 파트 생성. 실린더는 front/(mid)/back 파트 분리 (`:3826-3879`). Wall 은 `CreateRigidMaterial` 강체 (`:3876`).
   - Wall 3방향 `BOUNDARY_PRESCRIBED_MOTION_RIGID` 로 고정 (`:3899-3901`).
   - 위치 리스트 `locX` 루프 (`:3920`~): 자유낙하 속도 `velocity_z = Vz - √(2·g·h)`, `g=9810`(h>100, mm 단위 추정) 또는 `9.81` (`:3925-3928`).
   - 충격추 지오메트리 생성: Sphere=`CreateSphereImpactModule` 후 `GenerateTetraMeshfromShapes` (`:4060-4068`); Cylinder=`CreateCylinderwithMassImpactModule` 후 front/mid/back 각각 메시화 (`:4069-4096`).
   - 바닥판 박스: `CreateImpactBox(wallLocation, …, numX,numY,numZ)` (`:4107`).
   - 접촉: 바닥판↔객체 + 충격추↔객체 `CONTACT_AUTOMATIC_SURFACE_TO_SURFACE` 생성, OptCardA/B 세팅(SOFT 등) (`:4110-4124`). 실린더 다단은 단 간 `CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET` (`:4133-4141`).
   - 초기속도: `INITIAL_VELOCITY_GENERATION` 을 impactor(및 front/mid) 파트에 부여 (`:4113-4129`).
   - 메타데이터(`metaData["impactor"|"specimen"|"scenario_mode"]`) 기록 (`:4144-4324`).

4. **출력**
   - `runDirectoryMode` 시: `Run_<run_id>/` 폴더 + `Output/` + `DynamicRelaxation/` 생성, 모델은 `DropWeightImpactTestSet.k`(또는 입력 파일명)로 write (`:4326-4363`).
   - 누적 해석용 `DynamicRelaxation/dynaintoinitial.txt` 자동 생성(`DYNAIN_TO_INITIAL` 모드, IncludeStress/RemoveDynamicRelaxation/MovetoOriginAutomatic, impactor 파트 제거) (`:4365-4383`).
   - DOE 완료 표식 `.done` 파일 생성 (`:4387-4389`).
   - 비 runDirectoryMode + 위치 다수 시: `_MODE_DS_(CYL|SPH)_…_LOCX_…_LOCY_…_VX_…_H_…` suffix 단일 파일 출력 (`:4391-4410`).

5. **FastDOE**
   - 위치 다수(`len(locX)>1`) + `stressWaveDistance==0.0` 이면 베이스 모델을 캐시(`_CacheBaseKeyword`)해 반복 write 가속 (`:3903-3918`, write `:4360-4363`).

## 5. 주의사항 · 한계

- **3단 실린더(7값 Dimension)는 `GenerationMode=Part`(byPart) 미지원** — `NotImplementedError` 발생. DampingSpring 또는 OutsideRigidElement 사용 권장 (`KooDynaAdvancedModification.py:4412-4419`).
- **단위계 자동 추정**: 낙하속도 환산 시 `Height>100` 이면 mm(g=9810), 이하면 m(g=9.81)로 추정 — 단위계가 섞이면 의도치 않은 속도가 될 수 있음 (`:3925-3928`).
- `LocationX/Y`, `Height`, `InitialVelocityX/Y/Z` 는 인덱스 매칭 리스트이므로 길이가 일치해야 함(파서가 길이 검증은 하지 않음 — `KooMeshModifier.py:1164-1205`).
- `OffsetDistance` 기본값이 파서(`1e-9`)와 소비측 fallback(`1e-11`)에서 다름 — 명시 지정 권장 (`KooMeshModifier.py:1052` vs `AdvMod:3751`).
- 접미사 없는 물성 키(`YoungModulus`,`Density` 등)의 실제 매핑은 부분일치 의존이라 **확인 필요**(2절 참고).
- scenario.json → `.k` 변환(KooChainRun/Designer)은 본 모드 코드 밖이며, 키 매핑 세부는 별도 확인 필요.

## 6. 개발 현황

**구현됨 (부분 한계 있음)**

근거:
- modeList 등록 + dispatch + 3개 핸들러 메서드 실재: `KooMeshModifier.py:285-287, 2484-2489, 2828-2830`; `KooDynaAdvancedModification.py:3185, 3596, 4412`.
- Sphere/Cylinder(2·3단), 위치 DOE, 자동 접촉, 초기속도, 제어카드, Run 폴더/dynaintoinitial 출력까지 코드로 확인됨.
- 실제 입력 예제(`dist/Examples/5.SimulationModify/*.txt`)와 운영 scenario.json(`Examples/scenario_examples/impact_cylinder_8pi.json`, `15pi.json`, `Examples/drop_weight_impact/scenario.json`) 존재.

한계(부분구현 성격):
- 3단 실린더의 Part(byPart) 경로 미지원(명시적 NotImplementedError).
- OutsideRigidElement/OutsideRigidPart, byPart 경로 세부 동작은 본 문서에서 주 경로 위주로만 검증(해당 메서드 전체 정밀 검토는 별도 필요 — **확인 필요**).
