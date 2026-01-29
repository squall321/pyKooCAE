# KooMeshModifier 사용 매뉴얼

`KooMeshModifier.py`는 LS-DYNA 모델을 옵션 파일 기반으로 수정하고 새로운 키워드 파일을 생성하는 도구입니다. 아래 설명은 실행 방법, 옵션 파일 작성 규칙, 모드별 옵션과 예제(`occProject/Generators/dist/Examples/5.SimulationModify`의 `.txt`들)을 매칭해 정리했습니다. 테스트 실행은 생략하고 사용법만 다룹니다.

## 실행 방법
- 기본: `python occProject/Generators/KooMeshModifier.py <옵션파일경로> [작업디렉터리]`
- 옵션 파일이 있는 디렉터리에 로그(`<옵션파일명>.log`)와 수정 결과(`입력.k`에 모드별 접미사 `_etor`, `_mex`, `_pld` 등 추가)가 생성됩니다.
- 실행 전 `Library/OCC`가 `LD_LIBRARY_PATH`(Linux) 또는 DLL 경로(Windows)에 잡히도록 현재 스크립트가 자동 설정합니다.

## 옵션 파일 작성 체크리스트
1) 필수 헤더  
   - `*Inputfile <기준.k>`  
   - (필요 시) `*InputObjFile <기준.obj>`
2) 메타 정보(선택)  
   - `*Info,<모델명>,<Revision>`  
   - `*Description,<text>`  
   - `*Creator,<name>,<email>,<group>,<team>`
3) 실행 제어(선택)  
   - `*Step,<정수>`  
   - `RunDirectoryMode,<true|false>,<runDir>,<metaDir>`
4) 모드 선언  
   - `*Mode` 다음 줄들에 `MODE_NAME,ID` 나열
5) 모드 상세 블록  
   - 각 ID마다 `**<ModeKeyword>,<ID>` ~ `**End<ModeKeyword>` 사이에 옵션 기입  
   - 주석은 `#` 또는 `$` 사용
6) 다중 모드 적용  
   - 하나의 옵션 파일에 여러 모드를 순서대로 적을 수 있으며, 적용된 순서대로 결과 파일 이름에 접미사(`_etor`, `_mex`, `_pld` 등)가 붙습니다.

옵션 파일 뼈대 예:
```
*Inputfile
Impact_1_00000001.k
*Mode
ELASTIC_TO_RIGID,1
PART_EXCHANGE,2
**ElastictoRigid,1
...옵션...
**EndElastictoRigid
**PartExchange,2
...옵션...
**EndPartExchange
*End
```

## 모드별 요약 및 예제 파일
모드 이름은 `*Mode`에 쓰는 상수, 블록 헤더는 `**` 뒤에 붙는 키워드입니다.

- **ELASTIC_TO_RIGID** (`**ElastictoRigid`)  
  - 주요 옵션: `*PIDExcept,<pid...>`로 강체 변환에서 제외할 파트 지정.  
  - 예제: `occProject/Generators/dist/Examples/5.SimulationModify/ElasticToRigidOption.txt`(MODE 1, 제외 PID 5). `ElasticToRigid_Test.txt`도 동일 형식.

- **MATERIAL_EXCHANGE** (`**MaterialExchange`)  
  - 주요 옵션: `*VarList,<변수명>,값1,값2,...`; `*MIDxx,*MAT_xxx` 블록에서 변수명으로 값을 치환하며 여러 재료 케이스 생성.  
  - 예제: `.../MaterialExchange.txt`(E 탄성계수 치환).

- **PART_LOCATION_DOE** (`**PartLocationDOE`)  
  - 주요 옵션: `*PIDs`, `*MaskPID`, `*ObstaclePID`, 격자 간격 `*dx,*dy,*dz`, 샘플 수 `*nx,*ny,*nz`, 팽창 계수 `*Dilation`, 샘플링 방법 `*Sampling,<LatinHypercube|Random|Grid>,N`.  
  - 예제: `.../PartLocationDOE/PartLocationDOE.txt`.

- **ERODING_MIN_DT** (`**ErodingMinDT`)  
  - 주요 옵션: `*DT,<시간스텝>`으로 요소 삭제 최소 시간스텝 지정.  
  - 예제: `.../Eroding_Dtmin/Eroding_Dtmin.txt`.

- **PART_EXCHANGE** (`**PartExchange`)  
  - 용도: 파트 재구성/리메시/두께·재료 교체.  
  - 대표 옵션: `*PID` 또는 `*PIDs` 대상 지정, `*ConvertHexato,<Shell|TShell|Solid...>,(<Xdir>),<TolAngle>`; `*UnstructuredtoStructured,NX,NY,NZ`; `*LayerThickness` 다층 두께; `*MID/*EOS/*HGID/*THK/*NUME` 등 키워드 블록으로 재료/방정식/두께/요소수 정의; `*Layup`으로 적층 시트 정의.  
  - 예제들:  
    - 기본 TShell 변환: `.../SolidtoTShell.txt` (PID 1을 TShell로 변환).  
    - 복합재/적층: `.../SolidtoSolidComposite_PS.txt`, `.../SolidtoSolidComposite_PA2.txt`.  
    - 허용 슬랙·보강: `.../ConnectorGeneration/SolidtoSolidwithSlack.txt`, `.../ConnectorGeneration/SolidStructuredZSlack.txt`.  
    - 구조화 메쉬: `.../UnstructuredtoStructured.txt`, `.../UnstructuredtoStructuredLayered.txt`.  
    - 다른 예: `PS_Solid_to_TShell.txt`, `SolidtoShellComplexShell.txt`, `ElasticToRigidOption.txt`(Elastic→Rigid 후 Part 교체 결합 예).

- **PART_MORPHING** (`**PartMorphing`)  
  - 주요 옵션: `*UnitScale`, `*MeshSize`(재메시 여부), `*MorphBox`/`*MorphPIDBox` 등으로 목표 PID, 위치/길이, X/Z 방향 벡터, 변형 거리(±), 영향 반경, 각도, 박스 분할 수 지정.  
  - 예제: `.../Morph/PartMorph.txt`(리메시 포함), `PartMorphNoReMesh.txt`, `PartMorphNoReMeshPIDBox.txt`, `PartMorphTest.txt`.

- **WEAK_COUPLING** (`**WeakCoupling`)  
  - 코드상 옵션: `FilePath`, `Mode`(`NodeSet`/`SegmentSet`), `SetID`, `BoundaryBox`로 국부 영역 접합.  
  - 현재 예제 폴더에 전용 설정 파일은 없음(제공된 `WeakCoupling*.txt`는 Drop Attitude 내용).

- **DEFEATURE_MESH** (`**DefeatureMesh_MESH`)  
  - 주요 옵션: `*PIDS` 대상, `*MinLength`로 소특징 제거 기준 길이 설정.  
  - 예제: `.../Defeature.txt`.

- **DROP_ATTITUDE** (`**DropAttitude`)  
  - 주요 옵션: 오일러 각 `EulerRolling/Pitching/Yawing`, 낙하 높이 `Height`, 선형/각속도 `InitialVelocity*`, `InitialAngularVelocity*`, 재료물성(밀도/Young/Poisson), `OffsetDistance`, 해석 시간 `tFinal`, `dt`, 충돌면 `DropSurface`(평면/거칠기 포함).  
  - 예제: 기본 `.../DropAttitude.txt`; 변형된 경사/곡면/거칠기 버전 `DropAttitudeCurve.txt`, `DropAttitudeCorner.txt`, `DropAttitudeRoughness.txt`, `DropAttitudeRoughnessSin.txt`, 거시 스케일 `DropAttitudeMacroscale.txt`, 동적이완 케이스 `DynamicRelaxation/drop_attitude.txt`.

- **TRANSFORM** (`**Transform`)  
  - 주요 옵션: `Translation`, `Rotation`, `VectorRotation`, `VectortoVectorRotation`, `Scale`, `Mirror(<평면>)` 순차 적용.  
  - 예제: `.../Transform.txt`.

- **DROP_WEIGHT_IMPACT_TEST** (`**DropWeightImpactTest`)  
  - 주요 옵션: 경계 거리/여유 `BoundaryDistance/DistanceMargin`, 감쇠 모드 `GenerationMode`(`DampingSpring`/`OutsideRigidElement`/`OutsideRigidPart`/`Part`), `OffsetDistance`, 위치 배열 `LocationX/Y`, 속도 `InitialVelocity*`, 높이 `Height`, 재료 물성(벽/임팩터/댐퍼), 시험 체적 `Type`(`Sphere`/`Cylinder`/`Box`) 및 `Dimension`, 그물망 크기 `MeshSize`, 최종시간 `tFinal`, 시간증분 `dt`.  
  - 예제: 기본 `.../DropWeightImpactTest.txt`; 실린더 `DropWeightImpactTestCylinder.txt`; 외부 강체/요소 활용 `DropWeightImpactTest_OutsideRigidElements.txt`; 파트 기반 `DropWeightImpactTestbyPart.txt`.

- **CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM** (`**ConstrainedNodalRigidbodytoBeam`)  
  - 주요 옵션: `*PID,ALL` 또는 특정 PID, 재료 상수 `*E,*PR,*RHO`, 단면 폭/높이.  
  - 예제: `.../ConstrainedNodalRigidBodytoBeam/ConstrainedNodalRigidbodytoBeam.txt`.

- **WARPED_PART** (`**WarpedPart`)  
  - 주요 옵션: 단위 `*UnitScale(mm/Microm 등)`, 위/아래 변형 진폭 `*AmplitudeTop/Bottom`, 기준 위치/크기/방향, `*WarpageFileTop/Bottom`, 대상 `*PIDs`.  
  - 예제: `.../WarpedPart/WarpedPart.txt`(양면 warpage).

- **WARPED_TO_INITIAL_STRESS_PART** (`**WarpedtoInitialStressPart`)  
  - 주요 옵션: WarpedPart와 동일 항목 + `*AdditionalThickness`로 초기 응력 반영 두께 보정.  
  - 예제: `.../WarpedtoInitialStressPart/WarpedtoInitialStressPart.txt`; 상하 warpage 분리 `WarpedtoInitialStressPartTopBottom.txt`; 타이 적용 `WarpedtoInitialStressPartWarpedTied.txt`.

- **DIMENSIONAL_TOLERANCE** (`**DimensionalTolerance`)  
  - 주요 옵션: `*PartDimTolerance,<LIST|NORM|LHS>[,<샘플수>]`; LIST 모드에서 `PID,방향(X/Y/Z),tol...`을 줄마다 기입. NORM/LHS는 통계 파라미터 기반 샘플링.  
  - 예제: `.../DimensionalTolerance/DimensionalTolerance.txt`(LIST), `DimensionalTolerance_norm_dist.txt`, `DimensionalTolerance_LHS.txt`.

- **COHESIVE_BETWEEN_CONFORMAL_MESHES** (`**CohesiveBetweenConformalMeshes`)  
  - 주요 옵션: 계면 재료 상수(`RO,EN,ET,GIC,GIIC,XMU,T,S,UND,UTD,GAMMA` 등)와 접합 쌍 `Pair,<PartA>,<PartB>,<Thickness>`.  
  - 예제: `.../CohesiveBetweenConformalMeshes/CohesiveBetweenConformalMeshes.txt`.

- **DYNAIN_TO_INITIAL** (`**DynainToInitial`)  
  - 주요 옵션: `*DynainPath`, `*IncludeStress`, `*RemoveDynamicRelaxation`, `*DynamicRelaxation` 플래그, 원점 이동 `*MovetoOriginbyNode` 또는 `*MovetoOriginAutomatic`, 제거 대상 `*RemovePartbyName/ID`, `*RemoveContactbyID`.  
  - 예제: `.../DynaintoInitial/DynainToInitial.txt`; 동적이완 결과 적용 예 `DynamicRelaxation/DynainToInitial.txt`, `DynainToInitial_dti.txt`.

- **CONTACT_AUTO_DECOMPOSITION** (`**ContactAutoDecomposition`)  
  - 주요 옵션: 탐색 여유 `*SearchMarginX/Y/Z`, 대상 접촉 키워드 블록을 `*ContactKeyword` 아래 그대로 삽입.  
  - 예제: `.../ContactAutoDecomposition/ContactAutoDecomposition.txt`.

- **SIMULATION_AUTOMATION** (`**SimulationAutomation`)
  - 주요 옵션: `JsonFile,<scenario.json>`로 다수 시나리오 로딩, `MetaData`는 상단 `*Info/*Description/*Creator` 값 자동 전달. 입력 파일명을 옵션에서 지정하면 각 시나리오의 `fileName`을 덮어씀.
  - 현재 배포 예제 파일은 없지만 JSON 스키마는 `LoadScenariosJson` 기준(`id,name,fileName,objFileName,analysisType,params` 필드)으로 작성.

- **FEM_TO_IGA** (`**FEMtoIGA`) ⭐ NEW
  - 용도: FEM 솔리드 파트를 IGA (Isogeometric Analysis) 포맷으로 일괄 변환.
  - 주요 옵션: `*IGA,<PID>,<IGAID>,<File>[,rr[,rs[,rt[,ratio[,ir]]]]]` 한 줄에 하나의 IGA 파트 정의.
  - 필수 파라미터:
    - `PID`: 원본 FEM Part ID
    - `IGAID`: 생성될 IGA Part ID (PID=VID=SID=PATCHID=RID로 모두 동일하게 사용)
    - `File`: 출력 파일명 (IGA 키워드 저장 경로, 예: `iga_part1.k`)
  - 선택 파라미터 (디폴트 값 제공):
    - `rr`: r-방향(ξ) 요소 크기 비율 (기본값: 0.6, 범위: 0.0~1.0, 작을수록 조밀)
    - `rs`: s-방향(η) 요소 크기 비율 (기본값: 0.6)
    - `rt`: t-방향(ζ) 요소 크기 비율 (기본값: 0.6, 두께 방향)
    - `ratio`: Bounding Box 확장 비율 (기본값: 1.1 = 10% 확장, 1.2 = 20% 확장)
    - `ir`: Integration Rule (기본값: 0 = Reduced Gauss, 1 = Full Gauss)
  - 주의: 대괄호 `[...]`는 선택 파라미터를 의미. 중간 파라미터는 건너뛸 수 없음 (예: `ratio`만 바꾸려면 `rr,rs,rt`도 명시)
  - 생성 파일: 메인 모델에 `*INCLUDE` 문 추가 + 개별 IGA 키워드 파일 (11개 블록: *KEYWORD, PARAMETER_LOCAL, PARAMETER_EXPRESSION_LOCAL, IGA_DEV_STABILIZATION, PART, SECTION_IGA_SOLID, IGA_DEV_VOLUME_XYZ, IGA_SOLID, IGA_3D_NURBS_XYZ, IGA_REFINE_SOLID, *END)
  - 예제: `occProject/Generators/dist/Examples/5.SimulationModify/FEMtoIGA/`
  - 출력 접미사: `_iga`

## 결과 파일/로그
- 변환 후 `WriteModifiedFile`이 `입력파일명+접미사.k`로 저장합니다(`WriteNastranModifiedFile`/`WriteAbaqusModifiedFile`은 코드에 있으나 기본 실행 흐름에서는 호출하지 않음).
- 로그는 옵션 파일과 같은 폴더에 생성되니 실패 시 메시지를 먼저 확인하세요.

## 예제 옵션 파일 원문 & 항목 설명
실제 옵션 파일 원문을 그대로 넣고, `ImportOption` 파서 기준으로 각 항목 의미를 붙였습니다. 순서는 주요 모드별 대표 예제로 구성했습니다.

### ElasticToRigidOption.txt
경로: `occProject/Generators/dist/Examples/5.SimulationModify/ElasticToRigidOption.txt`
```
*Inputfile
Impact_1_00000001.k
*Mode
ELASTIC_TO_RIGID,1
PART_EXCHANGE,2
**ElastictoRigid,1
*PIDExcept,5
**EndElastictoRigid
**PartExchange,2
*PID,5
*SECTION_SOLID_TITLE
ImpactBallSection
$$   SECID    ELFORM       AET    COHOFF   GASKETT
       SID         1      
*MAT_ELASTIC_TITLE
Steel
$$     MID        RO         E        PR        DA        DB         K
       MID 1.100e+03 2.413e+09 3.700e-01               
**EndPartExchange
*End
```
- `*Mode` 선언 두 개: 1번은 ELASTIC_TO_RIGID, 2번은 PART_EXCHANGE.
- `**ElastictoRigid,1` 블록: `*PIDExcept,5` → PID 5는 강체 변환에서 제외.
- `**PartExchange,2` 블록: PID 5를 대상으로 새 Section/MAT 정의로 교체. Section/Material 블록은 그대로 LS-DYNA 키워드로 읽혀 `AddSectionfromDyna`, `AddMaterialfromDyna`로 등록.

### MaterialExchange.txt
경로: `.../MaterialExchange.txt`
```
*Inputfile
Impact_1_00000001.k
*Mode
MATERIAL_EXCHANGE,1
**MaterialExchange,1
*VarList,E01,2.0e9,3.0e9,4.0e9
*MID01,*MAT_ELASTIC_TITLE
Steel
$$     MID        RO         E        PR        DA        DB         K
         1 1.100e+03       E01 3.700e-01       
**EndMaterialExchange
*End
```
- `*VarList`에서 변수 `E01`를 3개 값으로 정의 → 여러 재료 케이스 생성.
- `*MID01` 블록 내부에서 `E01`이 탄성계수 자리에서 치환되어 반복 생성.

### PartLocationDOE/PartLocationDOE.txt
```
*Inputfile
Impact_1_00000001.k
*Mode
PART_LOCATION_DOE,1
**PartLocationDOE,1
*PIDs,1
*dx,0.0005
*dy,0.0005
*nx,10
*ny,10
*MaskPID,2
*Dilation,1
*Sampling,LatinHypercube,100
**EndPartLocationDOE
*End
```
- `*PIDs` 대상 파트 이동 DOE.
- `*dx,*dy` 격자 간격, `*nx,*ny` 샘플 수.
- `*MaskPID` 회피 마스크, `*Dilation` 팽창 보정.
- `*Sampling` LHS 방식, 100 샘플.

### Eroding_Dtmin/Eroding_Dtmin.txt
```
*Inputfile
Impact_1_00000001.k
*Mode
ERODING_MIN_DT,1
**ErodingMinDT,1
*DT,1.0e-8
**EndErodingMinDT
*End
```
- 요소 삭제 최소 시간스텝 `DT`를 1e-8로 설정.

### SolidtoTShell.txt
```
*Inputfile
Impact_1_00000001.k
*Mode
PART_EXCHANGE,1
**PartExchange,1
*PID,1
*ConvertHexato,TShell,(0,0,1),5.0
**EndPartExchange
*End
```
- PID 1을 대상.
- Hexa → TShell 변환, 기준 방향 `(0,0,1)`, 허용 각도 5.0.

### Morph/PartMorph.txt
```
*Inputfile
Impact_1_00000001.k
*Mode
PART_MORPHING,1
**PartMorphing,1
*UnitScale,1
#Morph,Part ID,Shape,ShapeKeyword,ShapeKeyword,XDirection,ZDirection,Push(+) or Pull(-) Value,EffectRadius
*MorphBox,1,(0.0,0.0,0.0),(0.00020,0.00020,0.10),(1,0,0),(0,0,-1),0.00001,0.0002,5.0
**EndPartMorphing
*End
```
- 단위 스케일 1.
- `MorphBox`로 PID 1에 상자 변형: 위치/크기, X/Z 방향, Pull(+)/Push(-) 거리, 영향 반경, 각도(5.0) 지정. MeshSize 미지정 → 기본값, 리메시 수행.

### Defeature.txt
```
*Inputfile
Impact_1_00000001.k
*Mode
DEFEATURE_MESH,1
**DefeatureMesh_MESH,1
*PIDS,5
*MinLength,5.0E-5
**EndDefeatureMesh
*End
```
- PID 5 대상, 소특징 길이 5e-5 이하를 제거.

### DropAttitude.txt
```
*Inputfile
Impact_1_00000001.k
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,0,70
EulerPitching,0,40
EulerYawing,0,1.0
Height,1.50,1.50
InitialVelocityX,0.0,0.0
InitialVelocityY,0.0,1.0
InitialVelocityZ,0.0,0.0
InitialAngularVelocityX,0.0,0.0
InitialAngularVelocityY,0.0,100.0
InitialAngularVelocityZ,0.0,0.0
OffsetDistance,0.1
Density,2700
YoungsModulus,70e9
PoissonRatio,0.3
tFinal,1.0E-3
dt,1.0e-6
**EndDropAttitude
*End
```
- 오일러 각, 높이, 초기 속도/각속도, 물성, 해석 시간/증분 설정. OffsetDistance는 지면과 간격.

### Transform.txt
```
*Inputfile
MultiscaleTest_1_unitfeature.k
*Mode
TRANSFORM,1
**Transform,1
Translation,0.0,0.0,0.0
Rotation,0.0,0.0,0.0
Mirror,YZ
Scale,1.0,1.0,1.0
VectorRotation,1.0,0.0,0.0
VectortoVectorRotation,1.0,0,0,1.0,0.0,0.0
**EndTransform
*End
```
- 순차 변환: 병진 → 회전(오일러) → 대칭면(YZ) → 스케일 → 벡터 회전 → 벡터-벡터 회전.

### DropWeightImpactTest.txt
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
- 낙하 위치 2개, 높이 0.5, 감쇠/임팩터 물성 지정.
- 타입 Sphere, 반경 0.008; 감쇠체 치수/메시 크기 0.001.

### ConstrainedNodalRigidbodytoBeam/ConstrainedNodalRigidbodytoBeam.txt
```
*Inputfile
Connector.k 
*Mode
CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM,1
**ConstrainedNodalRigidbodytoBeam,1
*PID,ALL
*E,1.0e7
*PR,0.3
*RHO,7.8e-9
*Width,1.0
*Height,1.0
**EndConstrainedNodalRigidbodytoBeam
*End
```
- 모든 PID를 빔으로 대체하여 CNRB 생성. 재료탄성, 밀도, 단면 폭/높이 지정.

### WarpedPart/WarpedPart.txt
```
*Inputfile
Impact_1_00000001.k
*Mode
WARPED_PART,1
**WarpedPart,1
*UnitScale,Microm
*AmplitudeTop,0.1
*AmplitudeBottom,0.0
*Location,0.0,0.0,0.0
*XLength,0.0
*YLength,0.0
*Direction,0.0,0.0,1.0
*WarpageFileTop,warpage.dat
*WarpageFileBottom,warpage.dat
*PIDs,1,2,3,4
**EndWarpedPart
*End
```
- warpage.dat 상하를 동일하게 적용, Microm 단위, 대상 PID 1~4.

### WarpedtoInitialStressPart/WarpedtoInitialStressPart.txt
```
*Inputfile
PlateSolid.k
*Mode
WARPED_TO_INITIAL_STRESS_PART,1
**WarpedtoInitialStressPart,1
*UnitScale,Microm
*AmplitudeTop,1000.0
*AmplitudeBottom,0.0
*Location,0.0,0.0,0.0
*XLength,0.0
*YLength,0.0
*Direction,0.0,0.0,1.0
*AdditionalThickness,0.0
*WarpageFileTop,warpage.dat
*PIDs,1
**EndWarpedtoInitialStressPart
*End
```
- WarpedPart와 동일 옵션 + 추가 두께 보정. PID 1에 초기 응력 반영.

### DimensionalTolerance/DimensionalTolerance.txt
```
*Inputfile
PlateSolid.k
*Mode
DIMENSIONAL_TOLERANCE,1
**DimensionalTolerance,1
*PartDimTolerance,LIST
#PID,Direction,tolerance 1, tolerance, 2... 
1,Z,0.00,-0.3,0.05
1,X,0.1,0.000,0.05
#*PartDimTolerance,LHS,100
#PID,Direction,min,max,
#*PartDimTolerance,NORM
#PID,Direction,avg,std,repeat
#*PartDimTolerance,WEIBULL
#PID,Direction,wp1,wp2,repeat  
**EndWarpedtoInitialStressPart
*End
```
- LIST 모드: PID 1, Z방향은 3개 샘플값(0, -0.3, 0.05), X방향은 3개 샘플값.
- 주석된 줄은 LHS/NORM/WEIBULL 예시.

### CohesiveBetweenConformalMeshes/CohesiveBetweenConformalMeshes.txt
```
*Inputfile
Impact_1_00000001.k
*Mode
COHESIVE_BETWEEN_CONFORMAL_MESHES,1
**CohesiveBetweenConformalMeshes,1
RO,2.3e-9
ROFlag,0
INTFAIL,0.0
EN,1000.0
ET,100.0
GIC,10.0
GIIC,10.0
XMU,1.0
T,100.0
S,100.0
UND,10.0
UTD,10.0
GAMMA,1.0
Pair,1,2,0.00015
**EndCohesiveBetweenConformalMeshes
*End
```
- 접합 재료 상수 일괄 입력.
- `Pair,1,2,0.00015`: Part 1-2 사이 두께 0.00015 cohesive 생성.

### DynaintoInitial/DynainToInitial.txt
```
*Inputfile
PlateSolid_DimensionalTolerance_1.k
*Mode
DYNAIN_TO_INITIAL,1
**DynainToInitial,1
*DynainPath,dynain
*IncludeStress,True
*RemoveDynamicRelaxation,True
*MovetoOriginbyNode,2,5,6
*RemovePartbyName,Impactor
*RemovePartbyID,1
**EndDynainToInitial
*End
```
- dynain 파일 읽어 초기 상태로 변환. 응력 포함, DR 제거.
- 원점 이동 기준 노드 2,5,6. 이름/ID로 파트 제거.

### ContactAutoDecomposition/ContactAutoDecomposition.txt
```
*Inputfile
MinimumModel.k
*Mode
CONTACT_AUTO_DECOMPOSITION,1
**ContactAutoDecomposition,1
*SearchMarginX,1.5
*SearchMarginY,1.5
*SearchMarginZ,1.5
*ContactKeyword
*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID
$       ID                                                               heading
       CID                                                      Body Interaction
$     ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         0         0         5         0         0         0         0         0
$       fs        fd        dc        vc       vdc    penchk        bt        dt
         0         0         0         0        10         0         0         0
$      sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
         0         0         0         0         0         0         0         0
$     soft   softscl    lcidab    maxpar     sbopt     depth     bsort    frcfrq
         2         0         0         0         3         5         0         0
$   penmax    tkhopt    shlthk     snlog      isym     i2d3d    sldthk    sldstf
         0         0         0         0         0         0         0         0
**EndContactAutoDecomposition
*End
```
- 탐색 margin X/Y/Z 기본 1.5.
- `*ContactKeyword` 이하의 키워드는 그대로 파싱되어 분할/검색 대상 접촉 정의로 사용.

### FEMtoIGA_Test.txt ⭐ NEW
경로: `tests/iga_tests/FEMtoIGA_Test.txt`
```
*Inputfile
model.k

*Info,TestModel,v1.0
*Description,FEM to IGA conversion test - MODE 22

*Mode
FEM_TO_IGA,22

**FEMtoIGA,22
# Test 1: Minimal options (디폴트 사용)
*IGA,5,100,iga_part_5.k

# Test 2: Custom element size
*IGA,7,101,iga_part_7.k,0.4,0.4,0.3

# Test 3: All options specified
*IGA,10,102,iga_part_10.k,0.5,0.5,0.4,1.2,1

**EndFEMtoIGA

*End
```
- `*IGA` 한 줄에 하나의 IGA 파트 정의
- Test 1: 최소 옵션 (PID=5 → IGAID=100, 나머지 디폴트)
- Test 2: 요소 크기만 커스텀 (rr=0.4, rs=0.4, rt=0.3)
- Test 3: 모든 옵션 지정 (ratio=1.2 = 20% bbox 확장, ir=1 = Full Gauss)
- 생성 파일:
  - `model_iga.k` (FEM + `*INCLUDE` 문)
  - `iga_part_5.k` (IGA 키워드 9개 블록)
  - `iga_part_7.k` (IGA 키워드 9개 블록)
  - `iga_part_10.k` (IGA 키워드 9개 블록)
- 파라미터 디폴트:
  - rr, rs, rt = 0.6
  - ratio (bbox_offset_ratio) = 1.1 (10% 확장)
  - ir (integration_rule) = 0 (reduced Gauss)
