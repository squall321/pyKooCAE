# KooMeshModifier 모드 레퍼런스 매뉴얼

## 목차
1. [개요](#1-개요)
2. [기본 사용법](#2-기본-사용법)
3. [모드 상세 설명](#3-모드-상세-설명)

---

## 1. 개요

KooMeshModifier는 LS-DYNA 모델의 자동화 수정을 위한 도구입니다. 총 **21개의 변환 모드**를 제공하며, 각 모드는 특정한 모델 수정 작업을 수행합니다.

### 지원 모드 목록

| 번호 | 모드명 | 출력 접미사 | 설명 |
|------|--------|------------|------|
| 1 | ELASTIC_TO_RIGID | _etor | 탄성 재료를 강체로 변환 |
| 2 | MATERIAL_EXCHANGE | _mex | 재료 속성 DOE 생성 |
| 3 | PART_LOCATION_DOE | _pld | 파트 위치 DOE 생성 |
| 4 | ERODING_MIN_DT | _emdt | 요소 침식 최소 시간 간격 설정 |
| 5 | PART_EXCHANGE | _pex | 파트 교체 및 메시 변환 |
| 6 | PART_MORPHING | _pm | 기하 형상 변형 (모핑) |
| 7 | WEAK_COUPLING | _wc | 약결합 영역 설정 |
| 8 | DEFEATURE_MESH | _def | 미세 기하 특징 제거 |
| 9 | DROP_ATTITUDE | _drop | 낙하 자세 시험 설정 |
| 10 | TRANSLATION_DOE | _trans | 이동 DOE 생성 |
| 11 | TRANSFORM | _trans | 기하 변환 (이동/회전/스케일) |
| 12 | DROP_WEIGHT_IMPACT_TEST | _dwit | 낙하 충격 시험 설정 |
| 13 | CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM | _crb | CNRB를 빔 요소로 변환 |
| 14 | WARPED_PART | _warp | 휨 변형 적용 |
| 15 | WARPED_TO_INITIAL_STRESS_PART | _w2is | 휨 변형을 초기 응력으로 변환 |
| 16 | DIMENSIONAL_TOLERANCE | _dt | 치수 공차 적용 |
| 17 | COHESIVE_BETWEEN_CONFORMAL_MESHES | _cbcm | 정합 메시 사이 코히시브 요소 삽입 |
| 18 | DYNAIN_TO_INITIAL | _dti | Dynain 결과를 초기 조건으로 로드 |
| 19 | CONTACT_AUTO_DECOMPOSITION | _cad | 접촉면 자동 분해 |
| 20 | SIMULATION_AUTOMATION | _sa | 시뮬레이션 자동화 |
| 21 | REMOVE_DUPLICATE_TIED_CONTACTS | _rdc | 중복 타이드 접촉 제거 |

---

## 2. 기본 사용법

### 2.1 설정 파일 구조

```
*Inputfile
<입력파일명.k>

*InputObjFile (선택사항)
<입력OBJ파일명.obj>

*Info,<모델명>,<단계>
*Description,<설명>
*Creator,<이름>,<이메일>,<그룹>,<팀>
*Step,<스텝번호>

RunDirectoryMode,<true|false>,<실행디렉토리>,<메타디렉토리>

*Mode
<모드명1>,<모드ID1>
<모드명2>,<모드ID2>
...

**<모드설정블록1>,<모드ID1>
<옵션들>
**End<모드설정블록1>

**<모드설정블록2>,<모드ID2>
<옵션들>
**End<모드설정블록2>

*End
```

### 2.2 실행 방법

```bash
# 방법 1: 현재 디렉토리에서 실행
python KooMeshModifier.py <옵션파일명.txt>

# 방법 2: 디렉토리 지정
python KooMeshModifier.py <옵션파일명.txt> <작업디렉토리>
```

---

## 3. 모드 상세 설명

### 3.1 ELASTIC_TO_RIGID (탄성→강체 변환)

**목적**: 탄성 재료를 가진 파트를 강체(Rigid Body)로 변환

**설정 블록**:
```
**ElastictoRigid,<모드ID>
*PIDExcept,<제외할PID1>,<제외할PID2>,...
**EndElastictoRigid
```

**옵션 설명**:
| 옵션 | 설명 |
|------|------|
| *PIDExcept | 강체 변환에서 제외할 파트 ID 목록 |

**사용 예시**:
```
*Inputfile
model.k
*Mode
ELASTIC_TO_RIGID,1
**ElastictoRigid,1
*PIDExcept,5,10,15
**EndElastictoRigid
*End
```

---

### 3.2 MATERIAL_EXCHANGE (재료 교체 DOE)

**목적**: 재료 속성을 변수화하여 여러 케이스의 시뮬레이션 파일 생성

**설정 블록**:
```
**MaterialExchange,<모드ID>
*VarList,<변수명>,<값1>,<값2>,<값3>,...
*MID01,<재료키워드명>
<재료 속성 데이터>
**EndMaterialExchange
```

**옵션 설명**:
| 옵션 | 설명 |
|------|------|
| *VarList | 변수명과 값 목록 정의 |
| *MID## | 재료 정의 (변수명으로 값 대체 가능) |

**사용 예시**:
```
**MaterialExchange,1
*VarList,E01,2.0e9,3.0e9,4.0e9
*MID01,*MAT_ELASTIC_TITLE
Material_Name
         1    7.0e-9       E01       0.3
**EndMaterialExchange
```

---

### 3.3 PART_LOCATION_DOE (파트 위치 DOE)

**목적**: 파트의 공간적 위치를 변화시켜 여러 케이스 생성

**설정 블록**:
```
**PartLocationDOE,<모드ID>
*PIDs,<PID1>,<PID2>,...
*MaskPID,<마스크PID>
*ObstaclePID,<장애물PID1>,<장애물PID2>,...
*DX,<X방향간격>
*DY,<Y방향간격>
*DZ,<Z방향간격>
*NX,<X방향개수>
*NY,<Y방향개수>
*NZ,<Z방향개수>
*Dilation,<팽창계수>
*Sampling,<방법>,<샘플수>
**EndPartLocationDOE
```

**샘플링 방법**:
- Grid: 정규 격자
- LHS: Latin Hypercube Sampling
- Random: 무작위 샘플링

**사용 예시**:
```
**PartLocationDOE,1
*PIDs,100,101
*DX,5.0
*DY,5.0
*NX,10
*NY,10
*Sampling,LHS,50
**EndPartLocationDOE
```

---

### 3.4 ERODING_MIN_DT (침식 최소 시간간격)

**목적**: 요소 삭제를 위한 최소 시간 간격 설정

**설정 블록**:
```
**ErodingMinDT,<모드ID>
*DT,<시간간격>
**EndErodingMinDT
```

**사용 예시**:
```
**ErodingMinDT,1
*DT,1.0e-9
**EndErodingMinDT
```

---

### 3.5 PART_EXCHANGE (파트 교체)

**목적**: 복잡한 파트 교체 - 메시 변환, 재료/섹션 업데이트, 레이어링

**설정 블록**:
```
**PartExchange,<모드ID>
*PID,<파트ID>
*PIDs,<PID1>,<PID2>,...
*ConvertHexaTo,<타입>,<벡터X>,<벡터Y>,<벡터Z>,<허용각도>
*UnstructuredtoStructured,<NX>,<NY>,<NZ>
*LayerThickness
<두께1>
<두께2>
...
*THK01,<두께값>
*NUME01,<요소수>
*MID01,<재료키워드>
<재료데이터>
*Layup
<레이업정의>
*PART_COMPOSITE
<파트컴포지트정의>
**EndPartExchange
```

**변환 타입** (*ConvertHexaTo):
- Shell: 쉘 요소로 변환
- TShell: TShell 요소로 변환
- Solid: 솔리드 요소로 변환
- SolidComp: 솔리드 복합재로 변환
- SolidwithSlack: 슬랙이 있는 솔리드
- SolidStructuredZSlack: Z방향 슬랙 구조 솔리드

**사용 예시**:
```
**PartExchange,1
*PID,100
*ConvertHexaTo,Shell,0.0,0.0,1.0,45.0
*MID01,*MAT_ELASTIC
         1    2.3e-9     70000       0.3
**EndPartExchange
```

---

### 3.6 PART_MORPHING (파트 모핑)

**목적**: 기하 형상의 국소적 변형 적용

**설정 블록**:
```
**PartMorphing,<모드ID>
UnitScale,<단위스케일>
MeshSize,<메시크기>
MorphBox,<PID>,<X위치>,<Y위치>,<Z위치>,<X길이>,<Y길이>,<Z길이>,<XdirX>,<XdirY>,<XdirZ>,<ZdirX>,<ZdirY>,<ZdirZ>,<푸시거리>,<영향반경>,<각도>
MorphPID,<PID>,<타겟PID>,<XdirX>,<XdirY>,<XdirZ>,<ZdirX>,<ZdirY>,<ZdirZ>,<푸시거리>,<영향반경>,<각도>,<numX>,<numY>
MorphFromPIDBox,<PID>,<타겟PID>,<XdirX>,<XdirY>,<XdirZ>,<ZdirX>,<ZdirY>,<ZdirZ>,<푸시거리>,<영향반경>,<각도>
**EndPartMorphing
```

**모핑 모드**:
- MorphBox: 직접 박스 영역 지정
- MorphPID: PID 기반 박스 자동 생성
- MorphFromPIDBox: PID 경계 박스 기반 모핑

**사용 예시**:
```
**PartMorphing,1
UnitScale,1.0
MeshSize,0.5
MorphBox,100,0,0,0,10,10,5,1,0,0,0,0,1,2.0,5.0,30
**EndPartMorphing
```

---

### 3.7 WEAK_COUPLING (약결합)

**목적**: 모델의 특정 영역에 약결합 조건 적용

**설정 블록**:
```
*WeakCoupling,<모드ID>
FilePath,<파일경로>
Set,<모드>,<세트ID>
BoundaryBox,<minX>,<maxX>,<minY>,<maxY>,<minZ>,<maxZ>
**EndWeakCoupling
```

**Set 모드**:
- NodeSet: 노드 세트 기반
- SegmentSet: 세그먼트 세트 기반

**사용 예시**:
```
*WeakCoupling,1
FilePath,coupling_data.txt
Set,NodeSet,100
BoundaryBox,-10,10,-10,10,0,5
**EndWeakCoupling
```

---

### 3.8 DEFEATURE_MESH (메시 디피처링)

**목적**: 지정된 최소 길이 이하의 기하 특징 제거

**설정 블록**:
```
**DefeatureMesh,<모드ID>
PIDs,<PID1>,<PID2>,...
PID,<단일PID>
MinLength,<최소길이>
**EndDefeatureMesh
```

**사용 예시**:
```
**DefeatureMesh,1
PIDs,100,101,102
MinLength,0.5
**EndDefeatureMesh
```

---

### 3.9 DROP_ATTITUDE (낙하 자세 시험)

**목적**: 다양한 낙하 자세와 조건으로 낙하 시험 설정

**설정 블록**:
```
*DropAttitude,<모드ID>
RunID,<ID1>,<ID2>,...
EulerRolling,<각도1>,<각도2>,...
EulerPitching,<각도1>,<각도2>,...
EulerYawing,<각도1>,<각도2>,...
Height,<높이1>,<높이2>,...
InitialVelocityX,<속도1>,<속도2>,...
InitialVelocityY,<속도1>,<속도2>,...
InitialVelocityZ,<속도1>,<속도2>,...
InitialAngularVelocityX,<각속도1>,...
InitialAngularVelocityY,<각속도1>,...
InitialAngularVelocityZ,<각속도1>,...
OffsetDistance,<오프셋거리>
Density,<밀도>
YoungsModulus,<영률>
PoissonRatio,<포아송비>
TFinal,<종료시간>
DT,<시간간격>
DropSurface,<타입>,<X길이>,<Y길이>,<Z길이>,<numX>,<numY>,<numZ>
**EndDropAttitude
```

**DropSurface 타입**:
- Plane: 평면
- PlanewithRoughness: 거칠기가 있는 평면
  - 거칠기 모드: XYRandom, XRandom, YRandom, XSin, YSin, XYSin

**사용 예시**:
```
*DropAttitude,1
EulerRolling,0,45,90
EulerPitching,0,30
Height,1.0
InitialVelocityZ,-3000
Density,7.8e-9
YoungsModulus,2.0e5
PoissonRatio,0.3
TFinal,0.001
DT,1.0e-7
DropSurface,Plane,100,100,10,20,20,2
**EndDropAttitude
```

---

### 3.10 TRANSLATION_DOE (이동 DOE)

**목적**: 파트의 이동 변위를 DOE로 생성

**설정 블록**:
```
**Translation_DOE,<모드ID>
TranslationX,<PID>,<X값1>,<X값2>,...
TranslationY,<PID>,<Y값1>,<Y값2>,...
TranslationZ,<PID>,<Z값1>,<Z값2>,...
**EndTranslation_DOE
```

**사용 예시**:
```
**Translation_DOE,1
TranslationX,100,0,5,10
TranslationY,100,0,2,4
**EndTranslation_DOE
```

---

### 3.11 TRANSFORM (기하 변환)

**목적**: 순차적인 기하 변환 적용 (이동, 회전, 스케일, 미러링)

**설정 블록**:
```
**Transform,<모드ID>
Translation,<X>,<Y>,<Z>
Rotation,<X각도>,<Y각도>,<Z각도>
Scale,<X비율>,<Y비율>,<Z비율>
Mirror,<축>
VectorRotation,<X>,<Y>,<Z>
VectorToVectorRotation,<fromX>,<fromY>,<fromZ>,<toX>,<toY>,<toZ>
**EndTransform
```

**변환 타입**:
- Translation: 이동
- Rotation: 오일러 각도 회전
- Scale: 스케일링
- Mirror: 미러링 (X, Y, Z 축)
- VectorRotation: 벡터 방향 회전
- VectorToVectorRotation: 벡터에서 벡터로 회전

**사용 예시**:
```
**Transform,1
Translation,10,0,0
Rotation,0,0,45
Scale,1.5,1.5,1.0
**EndTransform
```

---

### 3.12 DROP_WEIGHT_IMPACT_TEST (낙하 충격 시험)

**목적**: 낙하 추 충격 시험 설정 - 임팩터 기하, 댐퍼, 메시 크기

**설정 블록**:
```
**DropWeightImpactTest,<모드ID>
GenerationMode,<모드>
StressWaveVelocity,<응력파속도>
BoundaryDistance,<경계거리>
DistanceMargin,<거리여유>
OffsetDistance,<오프셋거리>
Type,<Sphere|Cylinder|Box>
Dimension,<치수들>
DimensionDamper,<댐퍼치수들>
LocationMode,<위치모드>
LocationX,<X좌표들>
LocationY,<Y좌표들>
Height,<높이들>
InitialVelocityX,<X속도들>
InitialVelocityY,<Y속도들>
InitialVelocityZ,<Z속도들>
MeshSize,<메시크기>
PartIDs,<PID1>,<PID2>,...
TFinal,<종료시간>
DT,<시간간격>
YoungsModulusWall,<벽 영률>
YoungsModulusImpactor,<임팩터 영률>
YoungsModulusDamper,<댐퍼 영률>
DensityWall,<벽 밀도>
DensityImpactor,<임팩터 밀도>
DensityDamper,<댐퍼 밀도>
PoissonRatioWall,<벽 포아송비>
PoissonRatioImpactor,<임팩터 포아송비>
**EndDropWeightImpactTest
```

**GenerationMode**:
- DampingSpring: 댐핑 스프링 모드
- OutsideRigidPart: 외부 강체 파트
- OutsideRigidElement: 외부 강체 요소
- Part: 파트 기반

**Type (임팩터 형상)**:
- Sphere: 구
- Cylinder: 원통
- Box: 박스

**사용 예시**:
```
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
**EndDropWeightImpactTest
```

---

### 3.13 CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM (CNRB→빔 변환)

**목적**: Constrained Nodal Rigid Body를 빔 요소로 변환

**설정 블록**:
```
**ConstrainedNodalRigidBodyToBeam,<모드ID>
*PID,<ALL|PID1,PID2,...>
*E,<영률>
*PR,<포아송비>
*RHO,<밀도>
*Width,<너비>
*Height,<높이>
**EndConstrainedNodalRigidBodyToBeam
```

**사용 예시**:
```
**ConstrainedNodalRigidBodyToBeam,1
*PID,ALL
*E,2.1e5
*PR,0.3
*RHO,7.8e-9
*Width,1.0
*Height,1.0
**EndConstrainedNodalRigidBodyToBeam
```

---

### 3.14 WARPED_PART (휨 변형 적용)

**목적**: 외부 파일의 휨/변형 필드를 파트에 적용

**설정 블록**:
```
**WarpedPart,<모드ID>
UnitScale,<단위스케일>
AmplitudeTop,<상단진폭>
AmplitudeBottom,<하단진폭>
Location,<X>,<Y>,<Z>
XLength,<X길이>
YLength,<Y길이>
Direction,<X>,<Y>,<Z>
WarpageFileTop,<상단휨파일>
WarpageFileBottom,<하단휨파일>
PID,<PID1>,<PID2>,...
**EndWarpedPart
```

**사용 예시**:
```
**WarpedPart,1
UnitScale,mm
AmplitudeTop,1.5
Location,0,0,0
XLength,100
YLength,100
Direction,0,0,1
WarpageFileTop,warpage_top.dat
PID,100,101
**EndWarpedPart
```

---

### 3.15 WARPED_TO_INITIAL_STRESS_PART (휨→초기응력 변환)

**목적**: 휨 변형을 초기 응력으로 변환 (동적 이완 활용)

**설정 블록**:
```
**WarpedtoInitialStressPart,<모드ID>
UnitScale,<단위스케일>
AmplitudeTop,<상단진폭>
AmplitudeBottom,<하단진폭>
Location,<X>,<Y>,<Z>
XLength,<X길이>
YLength,<Y길이>
Direction,<X>,<Y>,<Z>
AdditionalThickness,<추가두께>
WarpageFileTop,<상단휨파일>
WarpageFileBottom,<하단휨파일>
PID,<PID1>,<PID2>,...
**EndWarpedtoInitialStressPart
```

**사용 예시**:
```
**WarpedtoInitialStressPart,1
UnitScale,Microm
AmplitudeTop,100
AmplitudeBottom,-50
Location,0,0,0
XLength,50
YLength,50
Direction,0,0,1
WarpageFileTop,warpage_data.csv
PID,100
**EndWarpedtoInitialStressPart
```

---

### 3.16 DIMENSIONAL_TOLERANCE (치수 공차)

**목적**: 치수 변이를 샘플링하여 여러 케이스 생성

**설정 블록**:
```
**DimensionalTolerance,<모드ID>
PartDimTolerance,<모드>,<샘플수>
<PID>,<방향>,<옵션들>
...
**EndDimensionalTolerance
```

**샘플링 모드**:
- LIST: 명시적 값 목록
- NORM: 정규 분포
- LHS: Latin Hypercube Sampling
- WEIBULL: 와이블 분포

**방향**: X, Y, Z, -X, -Y, -Z

**사용 예시**:
```
**DimensionalTolerance,1
PartDimTolerance,NORM,30
100,Z,0.5,0.1
101,X,-0.2,0.05
**EndDimensionalTolerance
```

---

### 3.17 COHESIVE_BETWEEN_CONFORMAL_MESHES (코히시브 요소 삽입)

**목적**: 정합 메시 인터페이스 사이에 코히시브 요소 삽입

**설정 블록**:
```
**CohesiveBetweenConformalMeshes,<모드ID>
Pair,<PartA_ID>,<PartB_ID>,<두께>
RO,<밀도>
ROFlag,<밀도플래그>
INTFAIL,<파괴적분점수>
EN,<법선강성>
ET,<접선강성>
GIC,<모드I파괴에너지>
GIIC,<모드II파괴에너지>
XMU,<혼합모드지수>
T,<법선최대응력>
S,<접선최대응력>
UND,<법선극한변위>
UTD,<접선극한변위>
GAMMA,<추가지수>
**EndCohesiveBetweenConformalMeshes
```

**사용 예시**:
```
**CohesiveBetweenConformalMeshes,1
Pair,100,101,0.01
RO,1.2e-9
EN,1000.0
ET,500.0
GIC,0.5
GIIC,1.0
T,50.0
S,30.0
**EndCohesiveBetweenConformalMeshes
```

---

### 3.18 DYNAIN_TO_INITIAL (Dynain→초기조건)

**목적**: Dynain 결과 파일을 초기 조건으로 로드

**설정 블록**:
```
**DynainToInitial,<모드ID>
DynainPath,<dynain파일경로>
IncludeStress,<true|false>
RemoveDynamicRelaxation,<true|false>
DynamicRelaxation,<true|false>
MovetoOriginbyNode,<노드ID1>,<노드ID2>,...
MovetoOriginAutomatic,<true|false>
RemovePartByName,<파트명1>,<파트명2>,...
RemovePartByID,<PID1>,<PID2>,...
RemoveContactByID,<ContactID1>,<ContactID2>,...
**EndDynainToInitial
```

**사용 예시**:
```
**DynainToInitial,1
DynainPath,dynain
IncludeStress,true
RemoveDynamicRelaxation,true
MovetoOriginAutomatic,true
RemovePartByID,500,501
**EndDynainToInitial
```

---

### 3.19 CONTACT_AUTO_DECOMPOSITION (접촉 자동 분해)

**목적**: 접촉 표면의 자동 분할 및 도메인 분해

**설정 블록**:
```
**ContactAutoDecomposition,<모드ID>
SearchMarginX,<X여유>
SearchMarginY,<Y여유>
SearchMarginZ,<Z여유>
ContactKeyword
<접촉키워드정의>
...
**EndContactAutoDecomposition
```

**사용 예시**:
```
**ContactAutoDecomposition,1
SearchMarginX,1.5
SearchMarginY,1.5
SearchMarginZ,1.5
ContactKeyword
*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE
         1         2         3         4
**EndContactAutoDecomposition
```

---

### 3.20 SIMULATION_AUTOMATION (시뮬레이션 자동화)

**목적**: JSON 파일을 통한 다중 시나리오 일괄 실행

**설정 블록**:
```
**SimulationAutomation,<모드ID>
JsonFile,<시나리오JSON파일경로>
**EndSimulationAutomation
```

**JSON 파일 형식**:
```json
[
  {
    "id": 1,
    "name": "Scenario_1",
    "fileName": "model.k",
    "objFileName": "model.obj",
    "analysisType": "fullAngleMBD",
    "params": {
      "param1": "value1",
      "param2": "value2"
    }
  },
  ...
]
```

**사용 예시**:
```
**SimulationAutomation,1
JsonFile,scenarios.json
**EndSimulationAutomation
```

---

### 3.21 REMOVE_DUPLICATE_TIED_CONTACTS (중복 타이드 접촉 제거)

**목적**: 중복되는 타이드 접촉 정의 식별 및 제거

**설정 블록**:
```
**Remove_Duplicate_Tied_Contacts,<모드ID>
Remove_Duplicate_Tied_Contacts,<true|false>
**EndRemove_Duplicate_Tied_Contacts
```

**사용 예시**:
```
**Remove_Duplicate_Tied_Contacts,1
Remove_Duplicate_Tied_Contacts,true
**EndRemove_Duplicate_Tied_Contacts
```

---

## 4. 다중 모드 사용

여러 모드를 순차적으로 적용할 수 있습니다. 출력 파일명에는 각 모드의 접미사가 순서대로 추가됩니다.

**예시**:
```
*Inputfile
model.k
*Mode
ELASTIC_TO_RIGID,1
PART_EXCHANGE,2
TRANSFORM,3
**ElastictoRigid,1
*PIDExcept,5
**EndElastictoRigid
**PartExchange,2
*PID,100
*ConvertHexaTo,Shell,0,0,1,45
**EndPartExchange
**Transform,3
Translation,10,0,0
**EndTransform
*End
```

**출력 파일**: `model_etor_pex_trans.k`
