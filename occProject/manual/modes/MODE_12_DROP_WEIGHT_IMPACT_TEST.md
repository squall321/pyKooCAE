# DROP_WEIGHT_IMPACT_TEST 모드 상세 분석

## 1. 개요

**목적**: 낙하 추(Drop Weight) 충격 시험을 위한 LS-DYNA 모델을 자동 생성. 임팩터(충격체), 댐퍼, 벽면을 자동으로 생성하고 필요한 접촉 및 경계조건을 설정

**파일 위치**:
- 파서: `KooMeshModifier.py` (라인 586-672)
- 실행: `KooDynaAdvancedModification.py` (라인 2350-3187)

**출력 접미사**: `_dwit`

**세 가지 생성 모드**:
1. `DropWeightImpactTest()` - 기본 댐핑 스프링 모드 (라인 2718-3187)
2. `DropWeightImpactTestwithPartialRigid()` - 부분 강체 모드 (라인 2350-2716)
3. `DropWeightImpactTestbyPart()` - 파트 기반 모드 (라인 3189+)

---

## 2. DROP_ATTITUDE와의 차이점

| 구분 | DROP_ATTITUDE | DROP_WEIGHT_IMPACT_TEST |
|------|---------------|------------------------|
| 충격 방향 | 모델이 바닥으로 낙하 | 임팩터가 모델로 낙하 |
| 모델 상태 | 모델에 초기 속도 부여 | 모델은 고정, 임팩터에 속도 부여 |
| 주요 용도 | 휴대폰 낙하 등 | 펀치/해머 충격 시험 |
| 경계조건 | 바닥면 고정 | 모델 하부 고정 또는 댐핑 |

```
DROP_ATTITUDE                    DROP_WEIGHT_IMPACT_TEST
    ▼ (모델 낙하)                    │
  ┌───┐                           ┌─●─┐ (임팩터)
  │   │                           │   │
  │   │  ← 속도                     ▼ (임팩터 낙하)
  └───┘                           ┌───┐
  ═════ (바닥)                     │   │ ← 피시험체 (고정)
                                  └───┘
                                  ═════ (벽)
```

---

## 3. 함수 호출 흐름

```
KooMeshModifier.ImportOption()
    │
    ├── **DropWeightImpactTest 블록 파싱
    │       └── modeIDOption[modeid] 에 옵션 저장
    │
    └── GenerateDropWeightImpactTest(modeid)
            │
            ├── GenerationMode 확인
            │
            ├── [DampingSpring 모드]
            │   └── advancedModification.DropWeightImpactTest()
            │
            ├── [OutsideRigidPart/OutsideRigidElement 모드]
            │   └── advancedModification.DropWeightImpactTestwithPartialRigid()
            │
            └── [Part 모드]
                └── advancedModification.DropWeightImpactTestbyPart()
```

---

## 4. 설정 파일 옵션 상세

### 4.1 전체 옵션 목록

| 옵션명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| **시뮬레이션 설정** |
| TFinal | float | 종료 시간 | 0.0 |
| DT | float | 출력 시간 간격 | 1.0e-6 |
| **경계 설정** |
| BoundaryDistance | float | 경계 거리 (응력파 영역) | 0.0 |
| StressWaveVelocity | float | 응력파 속도 | - |
| DistanceMargin | float | 거리 여유 계수 | - |
| **위치 설정** |
| LocationX | List[float] | X 충격 위치들 | [0.0] |
| LocationY | List[float] | Y 충격 위치들 | [0.0] |
| LocationMode | string | 위치 모드 | - |
| **임팩터 설정** |
| Type | string | 형상 (Sphere/Cylinder/Box) | "Sphere" |
| Dimension | List[float] | 치수 | [0.008] |
| MeshSize | float | 임팩터 메시 크기 | 0.001 |
| **댐퍼 설정** |
| DimensionDamper | List[float] | 댐퍼 치수 [폭, 높이, 길이] | [0.001,0.001,0.001] |
| **초기 조건** |
| InitialVelocityX | List[float] | X방향 속도들 | [0.0] |
| InitialVelocityY | List[float] | Y방향 속도들 | [0.0] |
| InitialVelocityZ | List[float] | Z방향 속도들 | [0.0] |
| Height | List[float] | 낙하 높이들 | [0.5] |
| OffsetDistance | float | 충격점 오프셋 | 1e-11 |
| **재료 설정** |
| YoungsModulusImpactorFront | float | 임팩터 전면 영률 | 2.07e11 |
| PoissonRatioImpactorFront | float | 임팩터 전면 포아송비 | 0.3 |
| DensityImpactorFront | float | 임팩터 전면 밀도 | 7800.0 |
| YoungsModulusDamper | float | 댐퍼 영률 | 1.0e10 |
| PoissonRatioDamper | float | 댐퍼 포아송비 | 0.3 |
| DensityDamper | float | 댐퍼 밀도 | 1000.0 |
| YoungsModulusWall | float | 벽 영률 | 1.0e10 |
| PoissonRatioWall | float | 벽 포아송비 | 0.3 |
| DensityWall | float | 벽 밀도 | 1000.0 |
| YoungsModulusImpactor | float | 임팩터 영률 | 2.07e11 |
| PoissonRatioImpactor | float | 임팩터 포아송비 | 0.3 |
| DensityImpactor | float | 임팩터 밀도 | 7800.0 |
| MaterialIDImpactorFront | int | 임팩터 전면 재료 ID | 0 |
| MaterialIDDamper | int | 댐퍼 재료 ID | 0 |
| MaterialIDImpactor | int | 임팩터 재료 ID | 0 |
| MaterialIDWall | int | 벽 재료 ID | 0 |
| **생성 모드** |
| GenerationMode | string | 생성 모드 | "DampingSpring" |
| PartIDs | List[int] | 대상 파트 ID들 | - |

### 4.2 임팩터 타입별 Dimension 형식

**Sphere (구)**:
```
Dimension,<반지름>
```

**Cylinder (원통)**:
```
Dimension,<전면반지름>,<외경>,<전면높이>,<후면높이>,<후면반지름>
```

**Box (박스)**:
```
Dimension,<X크기>,<Y크기>,<Z크기>
```

### 4.3 GenerationMode 옵션

| 모드 | 설명 | 경계 처리 |
|------|------|----------|
| DampingSpring | 댐핑 스프링 경계 | 빔 요소로 경계 댐핑 |
| OutsideRigidPart | 외부 강체 파트 | 경계 영역을 강체 파트로 |
| OutsideRigidElement | 외부 강체 요소 | 경계 요소를 강체로 |
| Part | 파트 기반 | 전체 파트 기반 처리 |

---

## 5. 핵심 알고리즘 분석

### 5.1 응력파 경계 거리 계산 (라인 2906-2911)

```python
if stressWaveDistance == 0.0:
    if "StressWaveVelocity" in option:
        stressWaveVelocity = option["StressWaveVelocity"]
        if "DistanceMargin" in option:
            distanceMargin = option["DistanceMargin"]
            # 응력파가 도달하는 거리 = 속도 × 시간 × 여유
            stressWaveDistance = stressWaveVelocity * tfinal * distanceMargin
```

**목적**: 충격이 전파되는 영역만 상세 해석하고, 나머지는 경계조건 처리

### 5.2 파트 생성 구조 (라인 2919-2961)

```python
# 1. 임팩터 전면 파트 (Cylinder 전용)
if impactorType.lower() == "cylinder":
    materialImpactorFront = matMan.CreateElasticMaterial(...)
    sectionImpactorFront = secMan.CreateSolidSection(...)
    impactFrontPart = KooPart(...)

# 2. 댐퍼 파트 (빔 요소)
materialBeam = matMan.CreateElasticMaterial("DamperMaterial", ...)
sectionBeam = secMan.CreateBeamSection("DamperSection")
beamPart = KooPart(...)

# 3. 임팩터 파트
materialImpactor = matMan.CreateElasticMaterial("ImpactorMaterial", ...)
sectionImpactor = secMan.CreateSolidSection("ImpactorSection", 1)
impactorPart = KooPart(...)

# 4. 벽 파트 (강체)
materialWall = matMan.CreateRigidMaterial("WallMaterial", ...)
sectionWall = secMan.CreateSolidSection("WallSection", 1)
wallPart = KooPart(...)
```

### 5.3 경계 요소 제거 및 댐핑 빔 생성 (라인 3051-3114)

```python
# 충격 영역 외부 요소 제거
for pid in self.dynaImporter.partManager.parts:
    part = self.dynaImporter.partManager.parts[pid]
    elemMan = part.elementManager

    # 충격점에서 stressWaveDistance 밖의 요소 제거
    addBDNodes, removedElems, removedNodes = elemMan.RemoveOuterElement(
        impactPoint[0], impactPoint[1], impactPoint[2],
        stressWaveDistance
    )
    removedElemList[pid] = removedElems
    removedNodeList[pid] = removedNodes
    boundaryNodes.extend(addBDNodes)

# 경계 노드에 댐핑 빔 요소 생성
for node in boundaryNodes:
    # 방사 방향 계산
    dirR = (node.x - impactPoint[0], node.y - impactPoint[1], node.z - impactPoint[2])
    normDir = (dirR[0]**2 + dirR[1]**2 + dirR[2]**2)**0.5
    dirR = (dirR[0]/normDir, dirR[1]/normDir, dirR[2]/normDir)

    # 외부 노드 생성 (댐핑 끝점)
    node2 = nodeMan.CreateNode(
        node.x + dirR[0] * offsetDampingDistance,
        node.y + dirR[1] * offsetDampingDistance,
        node.z + dirR[2] * offsetDampingDistance
    )

    # 중간 노드 생성 (2차 빔용)
    node3 = nodeMan.CreateNode(...)

    # 2차 빔 요소 생성
    beamElem = beamElemMan.CreateLineQuadraticElement(node, node2, node3)
```

**다이어그램**:
```
                    충격점
                      ●
                     /|\
                    / | \
                   /  |  \
                  /   |   \
     stressWaveDistance
                /     |     \
               /      |      \
              ●───────●───────●  경계 노드
              |       |       |
              ≋       ≋       ≋  댐핑 빔
              |       |       |
              ○───────○───────○  고정 노드
```

### 5.4 임팩터 형상 생성 (라인 3118-3140)

```python
if impactorType.lower() == "sphere":
    radius = dimension[0]
    impactLoc = [locX[i], locY[i], zMax + radius + offset_distance]

    # 모듈 매니저로 구 형상 생성
    simodule = self.moduleManager.CreateSphereImpactModule("Impact Ball", radius, impactLoc)
    simodule.SetMeshSize(meshSize)
    simodule.GenerateShape()

    # 테트라 메시 생성
    impactorPart.GenerateTetraMeshfromShapes(simodule.shapes, meshSize, meshSize, 3)

elif impactorType.lower() == "cylinder":
    radius = dimension[0]
    outerRadius = dimension[1]
    height1 = dimension[2]
    height2 = dimension[3]
    backRadius = dimension[4]

    # 실린더+질량 모듈 생성
    simodule = self.moduleManager.CreateCylinderwithMassImpactModule(
        "Impact Cylinder", radius, outerRadius, height1, height2, impactLoc, zDir, backRadius
    )
    simodule.SetMeshSize(meshSize)
    simodule.GenerateShape()

    # 후면 메시
    impactorPart.GenerateTetraMeshfromShapes(simodule.shapesBack, ...)
    # 전면 메시
    impactFrontPart.GenerateTetraMeshfromShapes(simodule.shapesFront, ...)
```

### 5.5 접촉 조건 생성 (라인 3152-3169)

```python
# 벽과 전체 객체 접촉
MSID = wallPart.id
SSID = 0  # 전체
contactWalltoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(
    SSID, MSID, SSTYP=5, MSTYP=3, ...
)
contactWalltoObjects.SetOptCardA(2)  # 소프트 제약

# 임팩터와 전체 객체 접촉
if impactorType.lower() == "sphere":
    MSID = impactorPart.id
    contactImpactortoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(...)

elif impactorType.lower() == "cylinder":
    MSID = impactFrontPart.id
    contactImpactortoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(...)

    # 임팩터 전면-후면 타이드 접촉
    tiedContactImpactortoFront = self.dynaImporter.contactManager.CreateContactTiedSurfacetoSurfaceOffset(
        SSID=impactFrontPart.id, MSID=impactorPart.id, ...
    )
```

### 5.6 초기 속도 및 경계조건 (라인 2975-2983, 3156)

```python
# 속도 곡선 정의 (0으로 유지)
A1 = [0.0, tfinal]
O1 = [0.0, 0.0]
curve = self.dynaImporter.defineManager.CreateDefineCurve(0, 1.0, 1.0, 0.0, 0.0, 0, 0, A1, O1)

# 벽 강체 모션 (완전 고정)
self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 1, 2, curve.lcid)  # X
self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 2, 2, curve.lcid)  # Y
self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 3, 2, curve.lcid)  # Z

# 임팩터 초기 속도
velocity = [Vx, Vy, Vz - 9.81 * height]  # 자유낙하 속도 추가
initV = self.dynaImporter.initialManager.CreateInitialVelocityGeneration(
    impactorPart.id, 2, 0, velocity[0], velocity[1], velocity[2]
)
```

---

## 6. 생성되는 모델 구조

### 6.1 Sphere 임팩터

```
           ┌─────┐
           │  ●  │  임팩터 (구)
           │     │
           └──┬──┘
              ▼ 속도
           ═══════  충격점
         ╔═══════════╗
         ║ 피시험체   ║
         ║   ≋≋≋     ║  댐핑 경계
         ╚═══════════╝
           ═══════════  벽 (강체)
```

### 6.2 Cylinder 임팩터

```
         ┌─────────┐  임팩터 후면 (질량)
         │  ████   │
         └────┬────┘
              │  타이드 접촉
         ┌────┴────┐  임팩터 전면 (충격)
         │    ○    │
         └────┬────┘
              ▼
         ═══════════
```

---

## 7. 사용 예시

### 7.1 구형 임팩터 기본 설정

```
*Inputfile
specimen.k
*Mode
DROP_WEIGHT_IMPACT_TEST,1
**DropWeightImpactTest,1
GenerationMode,DampingSpring
Type,Sphere
Dimension,5.0
Height,50.0
InitialVelocityZ,-5000
MeshSize,1.0
TFinal,0.002
DT,1.0e-7
YoungsModulusImpactor,2.1e5
DensityImpactor,7.8e-9
PoissonRatioImpactor,0.3
**EndDropWeightImpactTest
*End
```

### 7.2 원통형 임팩터

```
**DropWeightImpactTest,1
GenerationMode,DampingSpring
Type,Cylinder
Dimension,3.0,5.0,10.0,20.0,8.0
LocationX,0.0,10.0,20.0
LocationY,0.0,0.0,0.0
Height,100.0,100.0,100.0
InitialVelocityZ,-3000,-3000,-3000
MeshSize,0.5
**EndDropWeightImpactTest
```

### 7.3 경계 거리 지정

```
**DropWeightImpactTest,1
StressWaveVelocity,5000
DistanceMargin,1.5
TFinal,0.001
...
**EndDropWeightImpactTest
```
계산: BoundaryDistance = 5000 × 0.001 × 1.5 = 7.5

### 7.4 재료 ID 직접 지정

```
**DropWeightImpactTest,1
MaterialIDImpactor,100
MaterialIDWall,101
...
**EndDropWeightImpactTest
```

---

## 8. 생성되는 LS-DYNA 키워드

| 키워드 | 개수 | 설명 |
|--------|------|------|
| *PART | 3-4 | 임팩터, (전면), 댐퍼, 벽 |
| *SECTION_SOLID | 2-3 | 임팩터, (전면), 벽 |
| *SECTION_BEAM | 1 | 댐퍼 빔 |
| *MAT_ELASTIC | 2-3 | 임팩터, (전면), 댐퍼 |
| *MAT_RIGID | 1 | 벽 |
| *ELEMENT_SOLID | 다수 | 임팩터, 벽 요소 |
| *ELEMENT_BEAM | 다수 | 댐핑 빔 |
| *NODE | 다수 | 임팩터, 벽, 댐핑 노드 |
| *SET_NODE | 2 | 내부 노드, 고정 노드 |
| *BOUNDARY_SPC_SET | 1 | 댐핑 끝 고정 |
| *BOUNDARY_PRESCRIBED_MOTION_RIGID | 3 | 벽 고정 |
| *CONTACT_AUTOMATIC_SURFACE_TO_SURFACE | 2 | 벽-객체, 임팩터-객체 |
| *CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET | 0-1 | 실린더 전면-후면 |
| *INITIAL_VELOCITY_GENERATION | 1-2 | 임팩터 속도 |
| *DEFINE_CURVE | 1 | 경계 모션 곡선 |
| *SET_PART | 1 | 동적 이완 세트 |
| *INTERFACE_SPRINGBACK_LSDYNA | 1 | 스프링백 |

---

## 9. 다중 위치 DOE

여러 충격 위치를 지정하면 각각에 대해 별도 파일 생성:

```
LocationX,0.0,10.0,20.0
LocationY,5.0,5.0,5.0
Height,50.0,50.0,50.0
```

출력 파일명:
```
specimen_MODE_DS_SPH_5.000e+00_LOCX_0.000e+00_LOCY_5.000e+00_VX_0.000e+00_VY_0.000e+00_VZ_-3.132e+03_H_5.000e+01.k
specimen_MODE_DS_SPH_5.000e+00_LOCX_1.000e+01_LOCY_5.000e+00_...
specimen_MODE_DS_SPH_5.000e+00_LOCX_2.000e+01_LOCY_5.000e+00_...
```

---

## 10. 주의사항

1. **메시 크기**: MeshSize는 임팩터 메시에 적용됨. 피시험체 메시 크기와 비교하여 적절히 설정
2. **경계 거리**: BoundaryDistance가 너무 작으면 응력파 반사, 너무 크면 불필요한 계산
3. **메모리**: 다중 위치 DOE 시 이전 임팩터/벽이 제거되고 재생성됨
4. **단위**: 높이와 재료 상수 단위 일관성 확인 필요
5. **실린더 임팩터**: 전면-후면 타이드 접촉이 자동 생성됨

---

## 11. DROP_ATTITUDE vs DROP_WEIGHT_IMPACT_TEST 선택 가이드

| 상황 | 권장 모드 |
|------|----------|
| 제품 낙하 시험 | DROP_ATTITUDE |
| 펀치/해머 충격 | DROP_WEIGHT_IMPACT_TEST |
| 다양한 낙하 각도 | DROP_ATTITUDE |
| 특정 위치 국부 충격 | DROP_WEIGHT_IMPACT_TEST |
| 자유 낙하 | DROP_ATTITUDE |
| 고정된 피시험체 | DROP_WEIGHT_IMPACT_TEST |
