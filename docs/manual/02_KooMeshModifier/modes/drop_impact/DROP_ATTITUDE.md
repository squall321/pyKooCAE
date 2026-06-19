# KooMeshModifier 모드: DROP_ATTITUDE

## 1. 목적 / 개요

`DROP_ATTITUDE` 는 제품 모델(.k)을 임의의 낙하 자세(Euler 각도)로 회전시키고,
낙하 높이/초기속도/초기각속도로부터 초기조건(`*INITIAL_VELOCITY`)을 자동 생성하며,
낙하 충돌을 받을 **바닥판(Plane/PlaneGraded/PlanewithRoughness)** 또는
**RigidWall(`*RIGIDWALL_PLANAR_MOVING_FORCES`)** 을 자동으로 붙여 낙하 시험용
LS-DYNA 입력 데크를 만드는 모드다.

핵심 동작:

- Euler 각(Rolling/Pitching/Yawing)으로 회전 행렬을 만들어 충돌점(impact point)과 회전된 속도 벡터를 계산
- 낙하 높이 → 자유낙하 속도(`v = -sqrt(2gh)`)로 변환, 입력 초기속도와 합산
- 전체 노드에 `*INITIAL_VELOCITY` 부여 + `*INTERFACE_SPRINGBACK_LSDYNA`(Dynamic Relaxation) 추가
- 바닥판/RigidWall 생성 및 낙하 접촉(SINGLE_SURFACE / GENERAL / RigidWall) 자동 구성
- Euler 각 리스트가 여러 개면 한 번에 다수 방향(DOE) 데크를 생성 (Fibonacci lattice, 6-face drop 등)
- `RunDirectoryMode=True` 일 때 방향별 `Run_<id>/` 폴더에 `DropSet.k` + 다음 단계용 `dynaintoinitial.txt`(누적 낙하용 DYNAIN_TO_INITIAL 설정) 자동 생성

근거: 등록부 `KooMeshModifier.py:276-278`, dispatch `KooMeshModifier.py:2819-2821`,
구현 진입점 `KooMeshModifier.py:2471-2476`(→ `advancedModification.DropAttitude`),
본체 `KooDynaAdvancedModification.py:2035` 이후.

---

## 2. 입력 옵션 / 인자 (표)

입력 블록은 `**DropAttitude,<modeid>` 로 시작하고 `**EndDropAttitude` 로 끝난다.
각 옵션은 `키워드,값[,값...]` 형식(콤마 구분). 다수 값이 들어가는 옵션(EulerRolling 등)은
각 인덱스 `i`가 하나의 낙하 방향(DOE 케이스)이며, 리스트 길이는 서로 일치해야 한다.

파싱 근거: `KooMeshModifier.py:1347-1580`. 소비 근거: `KooDynaAdvancedModification.py:2037-2056`.

| 키워드 | 타입 | 기본값 | 설명 | 근거(line) |
|---|---|---|---|---|
| `EulerRolling` | float 리스트 | (필수) | X축 회전각(roll, deg). 케이스 수 결정 | 1367-1373 / 2037 |
| `EulerPitching` | float 리스트 | (필수) | Y축 회전각(pitch, deg) | 1374-1380 / 2038 |
| `EulerYawing` | float 리스트 | (필수) | Z축 회전각(yaw, deg) | 1381-1387 / 2039 |
| `Height` | float 리스트 | (필수) | 낙하 높이. `>100`이면 mm 단위(g=9810), `<=100`이면 m 단위(g=9.81)로 자유낙하 속도 계산 | 1388-1394 / 2231-2235 |
| `InitialVelocityX/Y/Z` | float 리스트 | (필수) | 초기 병진속도. 회전 후 자유낙하 속도와 합산 | 1395-1415 / 2228-2238 |
| `InitialAngularVelocityX/Y/Z` | float 리스트 | (필수) | 초기 각속도. 회전 적용됨 | 1416-1436 / 2240 |
| `runid` | int 리스트 | `[]` | RunDirectoryMode에서 방향별 Run 폴더 ID 지정(미지정 시 자동 생성) | 1363-1366 / 2978-2981 |
| `OffsetDistance` | float | `1e-9` | 충돌점과 바닥판 사이 초기 간격 | 1437-1443 / 2048,2251 |
| `Density` | float | (필수, 바닥판) | 바닥판 탄성재료 밀도. RigidWall이면 미사용 | 1444-1447 / 2049,2077 |
| `YoungsModulus` | float | (필수, 바닥판) | 바닥판 탄성계수 | 1448-1451 / 2050,2077 |
| `PoissonRatio` | float | (필수, 바닥판) | 바닥판 포아송비 | 1452-1455 / 2051,2077 |
| `tFinal` | float | `0.0` | 종료시간. `dt`와 함께 0이 아니면 CONTROL/DATABASE 자동 설정 | 1456-1459 / 2054,2058 |
| `dt` | float | `0.0` | 출력 시간간격(DATABASE) | 1460-1463 / 2053,2058 |
| `DropSurface` | 복합 | `Plane,0,0,0,10,10,10` | 바닥 종류. 아래 표 참조 | 1464-1506 / 2056,2100 |
| `DeformableToRigid` | bool | `False` | 충돌 후 모델 파트 D2R 전환 스위치(`*DEFORMABLE_TO_RIGID_AUTOMATIC` 쌍) 생성 | 1507-1509 / 2952-2963 |
| `NonReflectingBoundary` | bool | `False` | 바닥판 하면에 `*BOUNDARY_NON_REFLECTING` + 꼭짓점 최소 SPC | 1510-1512 / 2742-2756 |
| `IncludeWallInGeneral` | bool | `False` | 바닥판을 기존 `AUTOMATIC_GENERAL` 접촉에 포함(별도 접촉 미생성) | 1513-1515 / 2773-2800 |
| `RigidifySmallDtThreshold` | float | `0.0` | 임계 dt 이하 요소를 MAT_RIGID로 강체화 | 1516-1518 / 2256-2268 |
| `RigidifyMaxAspectRatio` | float | `0.0` | 종횡비 초과 요소 강체화 | 1519-1521 / 2257 |
| `RigidifyElementIDs` | int 리스트 | `None` | 수동 지정 요소 강체화 | 1522-1525 / 2258 |
| `RobustContact` | bool | `False` | 외부 segment에서 Tied 면 제외한 Segment Set 기반 SS로 교체(SOFT=2, DEPTH=3 강제) | 1529-1531 / 2334,2412-2415 |
| `RobustContactTolerance` | float | `0.1` | RobustContact Tied 면 판정 허용오차(mm) | 1526-1528 / 2443 |
| `EnsureSingleSurface` | bool | `False` | GENERAL/SS 모두 없을 때 전체 파트로 SINGLE_SURFACE 자동 생성 | 1532-1534 / 2388-2407 |
| `ConvertGeneralToSingleSurface` | bool | `True`(get 기본값) | GENERAL → SINGLE_SURFACE(SOFT=2) 변환 | 1535-1537 / 2271,2336 |
| `DecomposeGeneralContact` | bool | `False` | GENERAL → 개별 S2S pair로 분해 | 1538-1540 / 2272,2374 |
| `DecomposeContactMargin` | float | `1.5` | 분해 시 상대 margin | 1541-1543 / 2376 |
| `DecomposeContactAbsoluteMarginX/Y/Z` | float | `5.0/5.0/0.5` | 분해 시 절대 margin | 1544-1552 / 2377-2379 |
| `DropContact.<KEY>` | float/str | (옵션별) | 접촉 카드/제어 파라미터 직접 지정(SOFT, DEPTH, FS, FD, VDC, RWKSF, RW_SOFT, MeshScale 등) | 1553-1562 / 2274-2316 |
| `TiedOptions.<KEY>` | float/str/bool | (옵션별) | RobustContact 시 Tied 접촉 변환/파라미터(`ConvertToSegment`, `Tolerance`, `NormalAngleLimit`, SAST/SBST 등) | 1563-1578 / 2418-2435 |

### DropSurface 종류 (line 1464-1506)

| `DropSurface` 형식 | 의미 |
|---|---|
| `RigidWall` | 메시 없는 무한 강체 평면(`*RIGIDWALL_PLANAR_MOVING_FORCES`). 바닥판 재료/SPC 불필요 (2073, 2637-2660) |
| `Plane,xLen,yLen,zLen,numX,numY,numZ` | 균일 박스형 바닥판. 크기 0이면 모델 바운딩 박스×1.5 자동 (2100-2113, 2667-2669) |
| `PlaneGraded,innerX,innerY,zLen,numInnerX,numInnerY,numZ[,numOuterLayers=5][,ratio=1.5]` | 중심 균일 + 외곽 graded 바닥판. 크기/요소수 0이면 외곽면 요소 크기 기준 자동 매칭 (1479-1489, 2670-2736) |
| `PlanewithRoughness,xLen,yLen,zLen,numX,numY,numZ,roughnessMode,RMax,ShapeFactor[,ShapeFactor2]` | 거칠기 있는 바닥판. roughnessMode: Random/XRandom/YRandom/XSin/YSin/XYSin (1490-1506, 2737-2739) |

---

## 3. 사용 예제

### 3.1 6-Face Drop (Plane 바닥판, 6방향 동시 생성)

`Examples/6face_drop/drop_attitude_6face.txt` 발췌:

```
*Inputfile
MinimumModel.k
*RunDirectoryMode,True,Data/Results,Data/Metadata
*Info,Smartphone,6FaceDrop
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
$              F1(Back), F2(Front), F3(Right), F4(Left), F5(Top), F6(Bottom)
EulerRolling,        0,      180,         0,        0,      90,       -90
EulerPitching,       0,        0,       -90,       90,       0,         0
EulerYawing,         0,        0,         0,        0,       0,         0
Height,           1500,     1500,      1500,     1500,    1500,      1500
InitialVelocityX,    0,        0,         0,        0,       0,         0
InitialVelocityY,    0,        0,         0,        0,       0,         0
InitialVelocityZ,    0,        0,         0,        0,       0,         0
InitialAngularVelocityX,0,     0,         0,        0,       0,         0
InitialAngularVelocityY,0,     0,         0,        0,       0,         0
InitialAngularVelocityZ,0,     0,         0,        0,       0,         0
OffsetDistance,0.1
Density,2700
YoungsModulus,70000000000
PoissonRatio,0.3
tFinal,0.001
dt,0.000001
DropSurface,Plane,300,300,20,30,30,2
**EndDropAttitude
*End
```

### 3.2 동일 자세 + 이동 낙하(초기속도 스윕)

`Examples/HWWarrantyDropTest/docs/CustomScenarios/custom_initial_velocity.txt` 발췌:

```
*Inputfile
MinimumModel.k
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
$ Static_Drop,Moving_5mps,Moving_10mps,Moving_15mps
EulerRolling,0,0,0,0
EulerPitching,-90,-90,-90,-90
EulerYawing,0,0,0,0
Height,1500,1500,1500,1500
InitialVelocityX,0,5000,10000,15000
InitialVelocityY,0,0,0,0
InitialVelocityZ,0,0,0,0
**EndDropAttitude
*End
```

### 3.3 Fibonacci lattice 다방향 낙하

`Examples/alldropangles/drop_attitude.txt` 는 5방향 Fibonacci 각도를 한 블록에 나열한 예 (EulerRolling/Pitching/Yawing에 5개씩).

### 3.4 scenario.json 경유 (CumulativeDesigner → KooChainRun)

`Examples/scenario_examples/drop_attitude_example.json` 발췌 — scenario.json은
이후 KooMeshModifier 입력(.txt 블록)으로 변환된다:

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
    "cumulative": { "num_steps": 1, "mode_sequence": ["DROP"] }
  }
]
```

> 단위 주의: scenario.json의 density/youngs_modulus 등은 변환 없이 그대로 deck에 기록되므로
> 모델 .k 단위계(예: ton-mm-s)와 반드시 일치해야 한다 (예제 파일 `_comment_unit_system` 참조).

---

## 4. 동작 원리 (코드 근거)

1. **모드 등록 / dispatch**
   - 입력 `*Mode`의 `DROP_ATTITUDE,<id>` → `modeList`에 등록 (`KooMeshModifier.py:276-278`)
   - 실행 시 `GenerateDropAttitude(modeid)` 호출, 출력 접미사 `_drop` (`KooMeshModifier.py:2819-2821`)
   - `GenerateDropAttitude` 는 `advancedModification.DropAttitude(curOption, filePath)` 로 위임 (`KooMeshModifier.py:2471-2476`)

2. **제어/DATABASE 카드** — `dt!=0 and tFinal!=0` 이면 `SetControlandDatabaseExplicit(tFinal, dt)` 호출:
   CONTROL_TERMINATION/TIMESTEP/HOURGLASS 보강, DAMPING_PART_STIFFNESS coef<0.01 보정, DATABASE 출력 설정
   (`KooDynaAdvancedModification.py:2058-2059`, `1873-1912`).

3. **초기조건 / Dynamic Relaxation**
   - 전체 노드를 `AllNodes` node set으로 묶음 (`:2062-2066`)
   - 모델을 바운딩 박스 중심이 원점에 오도록 이동 (`:2079-2087`)
   - 전체 파트 대상 `*INTERFACE_SPRINGBACK_LSDYNA`(Dynamic Relaxation) 생성 (`:2132-2136`)

4. **자세/속도 계산 (방향 i 루프, `:2170` 이후)**
   - Euler 각의 부호 반전 후 라디안 변환, `R = Rz·Ry·Rx` 회전 행렬 구성 (`:2205-2215`)
   - 기본 축/평면 법선을 회전해 충돌 방향(z_direction) 산출 (`:2218-2220`)
   - 입력 초기속도 회전 + 높이 자유낙하 속도 합산 (`v=-sqrt(2gh)`, height>100→g=9810) (`:2228-2238`)
   - 각속도 회전 (`:2240`)
   - 충돌 방향 최원거리 노드 = impact point, `OffsetDistance` 만큼 띄움 (`:2244-2252`)
   - `*INITIAL_VELOCITY` 생성 (`:2253`)

5. **요소 강체화 (옵션)** — dt/aspect/수동 지정 요소를 `RigidifySmallDtElements` 로 MAT_RIGID화 (`:2256-2268`).

6. **접촉 처리**
   - GENERAL→SINGLE_SURFACE(SOFT=2) 변환 (`:2336-2373`), 또는 GENERAL→S2S 분해 (`:2374-2385`),
     또는 SS/GENERAL 부재 시 전체 파트 SS 자동 생성 (`:2388-2407`)
   - RobustContact 시 Tied 면 제외 Segment Set으로 SS 교체(SOFT=2/DEPTH=3) (`:2412` 이후)
   - DropContact.* 키로 접촉 OptCardA~D 파라미터 주입 (`:2274-2316`)

7. **바닥판 / RigidWall 생성**
   - RigidWall: `CreateRigidwallPlanarMovingForces`, part/접촉 skip (`:2637-2660`)
   - Plane/PlaneGraded/PlanewithRoughness: solid part 추가 후 `CreateImpactBox*` 로 바닥판 메시 생성, SPC 부여 (`:2662-2739`)
   - NonReflectingBoundary 시 전체 SPC 제거 → 바닥면 `*BOUNDARY_NON_REFLECTING` + 꼭짓점 3개 최소 SPC (`:2742-2756`)
   - 낙하 접촉(IncludeWallInGeneral / GENERAL 유지 / 외곽 파트 vs 바닥판 접촉) 구성 (`:2772-2901`)

8. **DeformableToRigid 쌍 스위치 (옵션)** — 접촉력 변화 기반 D2R/R2D 페어 스위치 생성 (`:2952-2963`).

9. **출력 (방향별)**
   - `RunDirectoryMode=True`: `Run_<id>/DropSet.k` + `Output/`, `DynamicRelaxation/dynaintoinitial.txt`(다음 누적 단계용 DYNAIN_TO_INITIAL 설정) + `.done` 마커 생성 (`:2976-3055`)
   - 비-RunDirectory + 다수 케이스: 각도/속도/높이가 인코딩된 접미사(`_NNN_DA_EX_..._H_..._VX_...`)로 별도 .k 저장 (`:3058-3077`)
   - `metaDirectoryPath` 지정 시 `outputPathList.txt` 에 생성 경로 누적 기록 (`:2137-2154`, `:3047-3055`)

> 다수 방향(`len(EulerRolling)>1`)일 때는 베이스 키워드를 캐시하는 Fast DOE 모드가 활성화되어
> 케이스마다 모델 재구성 없이 빠르게 데크를 찍어낸다 (`:2157-2173`, `_CacheBaseKeyword`/`_RestoreBaseState`).

---

## 5. 주의사항 / 한계

- **리스트 길이 일치**: `EulerRolling/Pitching/Yawing`, `Height`, `InitialVelocity*`,
  `InitialAngularVelocity*` 는 모두 동일 길이여야 한다. 인덱스로 직접 접근하므로 길이가 짧으면 `IndexError` 발생 가능
  (`:2188-2197` — get/기본값 처리 없음). **확인 필요**: 일부 옵션 누락 시 KeyError 가능성.
- **높이 단위 자동 판정**: `Height>100`이면 mm(g=9810), 이하이면 m(g=9.81)로 해석한다 (`:2231-2234`).
  즉 1.5m 낙하는 `1500`(mm)으로 적어야 하며 `1.5`로 적으면 m로 오인된다.
- **단위계 무변환**: Density/YoungsModulus/PoissonRatio/속도/높이 등은 변환 없이 deck에 그대로 기록되므로
  모델 .k 단위계와 반드시 일치시켜야 한다 (scenario 예제 `_comment_unit_system`).
- **바닥판 재료**: `DropSurface=RigidWall` 이 아니면 Density/YoungsModulus/PoissonRatio 가 바닥판 탄성재료로 사용된다.
  RigidWall이면 이 값들과 SPC/section/material 생성이 모두 생략된다 (`:2073-2077`, `:2637-2660`).
- **DeformableToRigid** 는 낙하 접촉 CID가 존재할 때만(`dropContactCID is not None`) 활성화된다.
  RigidWall이나 IncludeWallInGeneral 경로에서는 `dropContactCID=None` 이므로 D2R 스위치가 생성되지 않는다
  (`:2659-2660`, `:2800`, `:2952`).
- **출력 파일명 차이**: RunDirectoryMode 여부에 따라 출력 구조(`Run_<id>/DropSet.k` vs 접미사 인코딩 .k)가 완전히 다르다.
- `tFinal`/`dt` 둘 다 0이면 CONTROL/DATABASE 카드를 추가하지 않으므로 솔버 종료시간이 설정되지 않는다 (`:2058`).

---

## 6. 개발 현황

**구현됨** — 입력 파싱(`KooMeshModifier.py:1347-1580`), dispatch(`:276-278`, `:2819-2821`),
본체 로직(`KooDynaAdvancedModification.py:2035-3079`)이 모두 존재하며, 다수 실제 예제
(`Examples/6face_drop`, `Examples/alldropangles`, `Examples/HWWarrantyDropTest`,
`Examples/scenario_examples/drop_attitude_example.json`)가 동작 입력으로 제공된다.
RigidWall/Plane/PlaneGraded/PlanewithRoughness, RobustContact, DeformableToRigid,
NonReflectingBoundary, Fast DOE, RunDirectoryMode(누적 낙하용 dynaintoinitial.txt 자동 생성)까지 코드상 구현 확인됨.

**확인 필요**: 옵션 누락 시(예: InitialAngularVelocity* 미기재) KeyError/IndexError 처리 여부는
방어 코드가 보이지 않아 실제 실행 검증이 필요하다 (`:2044-2046`, `:2188-2197`).
