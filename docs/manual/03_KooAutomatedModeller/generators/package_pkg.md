# KooAutomatedModeller: PKG 패키지 생성

## 1. 목적 / 개요

`PKG` 모드는 텍스트 설정 파일(`.txt`)에 기술된 적층(Layer) 정의로부터 반도체 패키지(PKG)
형상을 생성하는 KooAutomatedModeller의 동작 모드이다. 입력 텍스트에 어떤 레이어를
어떤 순서/두께/크기로 쌓을지, 솔더 조인트·박스·실린더 등의 피처를 어디에 둘지 기술하면,
모드 설정에 따라 다음 둘 중 하나를 출력한다.

- **CAD 출력 (STEP)**: 메시 생성 모드가 꺼져 있으면 형상을 `.step` 파일로 내보낸다.
- **메시 출력 (LS-DYNA `.k`)**: 레이어에 메시 생성 옵션(`MeshGenerationType`)이 켜져 있으면
  LS-DYNA 키워드 메시(`.k`)를 내보낸다.

진입점은 `KooAutomatedModeller.py`의 `__main__` 분기로, `sys.argv`의 첫 인자가 `"PKG"`일 때
`GeneratePackage(fileName, displayMode)`가 호출된다 (KooAutomatedModeller.py:797-798).

> 참고: `GenerateDOEforLSDYNA`는 현재 본문이 출력문 한 줄(`print("Generate DOE for LSDYNA")`)만
> 있는 스텁이며, `LSDYNADOE` 모드 분기도 `pass`로 비어 있다 (KooAutomatedModeller.py:107-108, 799-800).
> 따라서 본 문서는 실제 동작하는 `PKG` 모드를 기준으로 기술한다.

## 2. 입력 옵션 · 인자 (표)

### 2-1. 명령행 인자 (`sys.argv`)

진입점은 위치 인자 기반이다 (KooAutomatedModeller.py:774-798).

| 위치 | 변수 | 의미 | 예시 |
|------|------|------|------|
| `argv[1]` | `mode` | 동작 모드. PKG 패키지는 `"PKG"` | `PKG` |
| `argv[2]` | `fileName` | 입력 텍스트 설정 파일 이름(현재 작업 디렉토리 기준) | `SE110060_COIL_ABCO_277_mesh.txt` |
| `argv[3]` | (작업 디렉토리) | `"none"`이면 무시. 그 외 값이면 `cwd/argv[3]`로 `os.chdir` | `none` 또는 `PackageExported` |
| `argv[4]` | `displayMode` | `"false"`면 비표시(헤드리스), 그 외면 GUI 표시 | `false` |

- `argv[3]`은 대소문자 무시하고 `none`이면 디렉토리 변경 없음, 아니면 현재 디렉토리 하위 `argv[3]`로 이동
  (KooAutomatedModeller.py:776-782).
- `argv[4]`가 없으면 `displayMode = False` (헤드리스) (KooAutomatedModeller.py:783-788).

### 2-2. 입력 텍스트 설정 파일의 주요 키워드

설정 파일은 `*`로 시작하는 최상위 디렉티브와, `*Layer` 블록 안의 키=값(콤마 구분) 라인으로 구성된다.
`#`로 시작하는 라인은 주석으로 건너뛴다 (PackageGenerator.py:169-171, 535-536).

#### 최상위 디렉티브 (`PackageGenerator.ImportPackage`)

| 디렉티브 | 인자 | 의미 | 근거(file:line) |
|----------|------|------|-----------------|
| `*Translation` | x, y, z | 패키지 원점 이동 | PackageGenerator.py:186-196 |
| `*Rotation` | 각도(int) | 회전 | PackageGenerator.py:197-202 |
| `*Mirror` | True/False | 미러링 | PackageGenerator.py:203-210 |
| `*IsTop` | True/False | 상/하 배치 | PackageGenerator.py:211-217 |
| `*Material` | (다음 줄에 파일명) | 재료 파일 임포트(설정 파일과 같은 폴더 기준) | PackageGenerator.py:177-185 |
| `*Layer` | name [, genMode] | 레이어 시작. genMode 미지정 시 `Defined` | PackageGenerator.py:218-234 |
| `*End` | - | 파싱 종료 | PackageGenerator.py:175-176 |

- `*Layer`의 3번째 인자(genMode)는 `Defined`(기본), `Warped`, `SolderJointWarped` 중 하나
  (PackageGenerator.py:221-233).

#### `*Layer` 블록 내 주요 키워드 (genMode=`Defined` 기준)

| 키워드 | 인자 | 의미 | 근거(file:line) |
|--------|------|------|-----------------|
| `Location` | x, y[, z] | 레이어 위치 (z 생략 시 누적 z 사용) | PackageGenerator.py:539-549 |
| `Length` | xLen, yLen[, matID] | 레이어 평면 크기 + 파트 생성 | PackageGenerator.py:550-564 |
| `Thickness` | t | 두께 (누적 z에 가산) | PackageGenerator.py:340-345 |
| `MaterialID` | id | 레이어 재료 ID | PackageGenerator.py:346-347 |
| `MeshGenerationType` | type[, meshType] | 메시 생성 켬(`Solid` 등) + 메시 형상(기본 `Hexa`/`Tetra`) | PackageGenerator.py:565-573 |
| `MeshPath` | path | 메시 출력 하위 경로 | PackageGenerator.py:574-577 |
| `MeshSizeInPlane` | size | 평면 메시 크기 | PackageGenerator.py:578-581 |
| `NumberofElementinXDirection` | n | X방향 요소 수 | PackageGenerator.py:582-583 |
| `NumberofElementinYDirection` | n | Y방향 요소 수 | PackageGenerator.py:584-585 |
| `NumberofElementinThickness` | n | 두께방향 요소 수 | PackageGenerator.py:332-335 |

> SolderJoint/Warped 레이어 전용 키워드(`SMD`, `NSMD`, `Box`, `SurfaceTension`, `Gravity`,
> `MisalignmentAngle`, `WarpageVariables` 등)는 별도 분기에서 파싱된다
> (PackageGenerator.py:236-410, 411-525). 위 표는 일반 `Defined` 레이어의 대표 키워드만 정리한 것이며,
> 전체 목록은 코드의 각 `elif svector[0] == ...` 분기를 참고할 것. (전수 정리는 **확인 필요**)

## 3. 사용 예제

### 3-1. 입력 텍스트 설정 — 메시 생성 예 (실제 Examples 발췌)

`/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/ODB/PackageExported/SE110060_COIL_ABCO_277_mesh.txt`
전체:

```
*Translation,19.21999966,14.21500078,0.3910000000000001
*Rotation,90
*Mirror,False
*IsTop,True
*Layer,SolderJoint
Location,0,0,0.0
Length,1.450e+00,8.000e-01
Thickness,3.000e-02
MeshGenerationType,Solid,Tetra
MeshPath,PackageMesh
MeshSizeInPlane,0.1
NumberofElementinThickness,5
MaterialID,1
MisalignmentAngle,0,0.0
SurfaceTension,480.0
Box,-6.250e-01,-3.000e-01,3.550e-01,6.000e-01
Box,2.700e-01,-3.000e-01,3.550e-01,6.000e-01
*Layer,Package
Location,0,0
Thickness,5.000e-01
Length,1.450e+00,8.000e-01
MeshGenerationType,Solid,Hexa
MeshPath,PackageMesh
MeshSizeInPlane,0.1
NumberofElementinXDirection,20
NumberofElementinYDirection,20
NumberofElementinThickness,3
MaterialID,2
*Material
Material.txt
*End
```

### 3-2. 입력 텍스트 설정 — STEP(CAD) 생성 예 (실제 Examples 발췌)

`/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/ODB/PackageExported/SB1005_IND_v4_286.txt`
전체 (메시 키워드 없음 → STEP 출력):

```
*Translation,34.16000026,1.54999944,0.3910000000000001
*Rotation,0
*Mirror,False
*IsTop,True
*Layer,SolderJoint
Location,0,0,0.0
Length,1.260e+00,6.500e-01
Thickness,3.000e-02
MisalignmentAngle,0,0.0
SurfaceTension,480.0
Box,-5.850e-01,-2.800e-01,4.100e-01,5.600e-01
Box,1.750e-01,-2.800e-01,4.100e-01,5.600e-01
*Layer,Package
Location,0,0
Thickness,5.000e-01
Length,1.260e+00,6.500e-01
*End
```

### 3-3. CLI 호출 (`sys.argv` 패턴)

코드 내부의 실제 호출 예 (KooAutomatedModeller.py:404-414, 612-638):

```
# argv = [실행파일, 모드, 입력파일]
KooAutomatedModeller PKG ECADfilesforPBA_P3_Export_detail_pcb_multiscale_mesh.txt
KooAutomatedModeller PKG PackageInfoBoxMeshCompositeMaterial.txt
KooAutomatedModeller PKG bga401f_W700L788_SB02_L_405.txt
```

작업 디렉토리/표시 모드까지 지정하는 4-인자 형태 (argv[3]=작업디렉토리, argv[4]=displayMode):

```
KooAutomatedModeller PKG SE110060_COIL_ABCO_277_mesh.txt none false
```

> 코드의 모든 PKG 예시는 `argv[1]="PKG"`, `argv[2]=입력 .txt` 형태이며, 입력 파일은
> 실행 시점의 현재 작업 디렉토리에서 찾는다 (PackageGenerator.py:120-125,
> `os.path.join(os.getcwd(), fileName)`).

## 4. 동작 원리 (코드 근거)

`PKG` 모드 처리 순서:

1. **진입점 분기** — `mode == "PKG"`이면 `GeneratePackage(fileName, displayMode)` 호출
   (KooAutomatedModeller.py:797-798).
2. **입력 경로 확인** — `inputFilePath = os.path.join(os.getcwd(), fileName)`; 파일 없으면
   `"File not exist"` 출력 후 반환 (KooAutomatedModeller.py:120-125).
3. **패키지 생성기 초기화 + 출력 파일명 결정** — `PackageUserdefined()` 생성,
   출력 STEP 이름은 입력 `.txt`의 확장자를 `.step`으로 치환
   (KooAutomatedModeller.py:127-131).
4. **설정 파일 파싱** — `package.ImportPackage(inputFilePath)`가 텍스트를 한 줄씩 읽어
   `*` 디렉티브와 `*Layer` 블록을 해석한다 (PackageGenerator.py:153-235 이하).
5. **형상 생성** — `package.GenerateShapeList()`로 레이어별 형상 리스트 생성
   (KooAutomatedModeller.py:132; PackageGenerator.py:2765).
6. **GUI 표시(선택)** — None이 아닌 형상이 있으면 `update_shape` 스레드로 표시하고,
   `displayMode == True`일 때만 `start_display()`로 블로킹 (KooAutomatedModeller.py:133-146).
   `update_shape`는 `QT_QPA_PLATFORM == "offscreen"`이면 즉시 반환하여 헤드리스를 지원한다
   (KooAutomatedModeller.py:254-263).
7. **출력 분기** — 첫 레이어의 `meshGenerationMode` 플래그로 결정 (KooAutomatedModeller.py:149-188):
   - **메시 모드 (`layerList[0].meshGenerationMode == True`)**: 파트/노드셋/접촉/경계/세그먼트셋/하중을
     순차 생성한 뒤 `ExportDynaMesh(dynaFileName)`로 `.k` 출력
     (KooAutomatedModeller.py:149-173). `.k`는 `*KEYWORD`로 시작하여 노드/파트 키워드를 기록한다
     (PackageGenerator.py:2616-2635). (Nastran/ANSYS/ABAQUS/OBJ 출력은 코드에 존재하나 주석 처리됨,
     KooAutomatedModeller.py:167-183.)
   - **CAD 모드 (`meshGenerationMode == False`)**: `ExportPackage()`로 모든 형상을
     `TopoDS_Compound`에 모아 `STEPControl_Writer`로 `.step` 출력
     (KooAutomatedModeller.py:185-188; PackageGenerator.py:3226-3249).

`meshGenerationMode`는 레이어 파싱 시 `MeshGenerationType` 키워드를 만나
`layer.SetMeshGenerationType(...)`가 호출되면 켜진다 (PackageGenerator.py:565-573,
레이어 클래스 기본값 `meshGenerationMode = False`는 KooImpactSimulationGenerator.py:71,
PackageWarpageLayer.py:86 참조).

## 5. 주의사항 · 한계

- **출력 형식은 입력에 따라 자동 결정**된다. `MeshGenerationType`이 하나라도 있으면 `.k`(메시),
  없으면 `.step`(CAD)로 갈린다. 첫 레이어(`layerList[0]`)의 플래그로 분기하므로
  레이어별로 메시/비메시를 섞으면 의도와 다른 출력이 날 수 있다 (KooAutomatedModeller.py:149, 185). (혼합 시 동작 **확인 필요**.)
- **입력 파일은 현재 작업 디렉토리 기준**으로 찾는다. 절대경로가 아니라면 실행 위치 또는
  `argv[3]` 작업 디렉토리 설정에 주의 (KooAutomatedModeller.py:120-125, 776-782).
- **헤드리스 실행** 시 `QT_QPA_PLATFORM=offscreen` 환경변수가 필요하다. 미설정 시
  `start_display()` 경로(GUI)로 들어가면 디스플레이가 없으면 실패할 수 있다
  (KooAutomatedModeller.py:255-256, 143-145).
- **라이선스/실행 게이트**: `__main__`에 IP 화이트리스트 검사와 만료일(2027-12-31) 검사가 있어
  등록되지 않은 IP에서는 즉시 종료한다 (KooAutomatedModeller.py:340-386). 자동화 환경에서
  실행 시 이 게이트를 통과해야 한다.
- **GenerateDOEforLSDYNA / LSDYNADOE 모드는 미구현 스텁**이다 (KooAutomatedModeller.py:107-108, 799-800).
- `Examples/automatedmodeller/check_cylinders.py`는 `from KooAutomatedModeller import KooAutomatedModeller`
  클래스 API(`SetMode`, `ReadInputFile`)를 가정하나, `KooAutomatedModeller.py`에는 해당 클래스/메서드가
  존재하지 않는다(`grep` 결과 무). 실제 진입점은 본 문서가 다루는 `sys.argv` CLI이며,
  해당 예제 스크립트의 동작 여부는 **확인 필요**.
- `*Material` 디렉티브의 재료 파일은 설정 파일과 같은 폴더에서 찾는다
  (PackageGenerator.py:181-183). 위 예제(3-1)는 동일 폴더의 `Material.txt`를 참조한다.

## 6. 개발 현황

**부분 구현.**

근거:
- **구현됨**: `PKG` 모드 진입점 분기(KooAutomatedModeller.py:797-798), 텍스트 설정 파서
  `ImportPackage`(PackageGenerator.py:153-), STEP 출력 `ExportPackage`(PackageGenerator.py:3226-3249),
  LS-DYNA 메시 출력 `ExportDynaMesh`(PackageGenerator.py:2616-), 그리고 실제 입력 예제 파일들
  (`Examples/ODB/PackageExported/*.txt`)이 모두 존재.
- **미구현/스텁**: 동일 파일의 DOE 관련 모드(`GenerateDOEforLSDYNA`, `LSDYNADOE`)는 스텁
  (KooAutomatedModeller.py:107-108, 799-800).
- **확인 필요**: Nastran/ANSYS/ABAQUS/OBJ 추가 출력은 코드에 있으나 주석 처리되어 비활성
  (KooAutomatedModeller.py:167-183); 레이어별 메시/비메시 혼합 동작; `check_cylinders.py`가
  가정한 클래스 API의 실존 여부.
