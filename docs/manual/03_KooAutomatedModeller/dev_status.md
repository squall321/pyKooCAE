# KooAutomatedModeller 개발 현황

> 근거 소스: `occProject/Generators/KooAutomatedModeller.py` (801줄, mtime 2026-02-02)
> 보조 모듈: `occProject/Generators/KooODBCADManager/` (`ODBCADManager.py` / `PackageGenerator.py` / `PackageLayer.py` / `Capacitor.py`)
> 빌드: `occProject/Generators/build_automatedmodeller_python3{10,12,13}.sh`, `build_all_python3{10,12,13}.sh`, `build_without_automatedmodeller.sh`

---

## 1. 목적 / 개요

KooAutomatedModeller(KAM)는 전자 패키지·PCB·PBA·커패시터의 CAD 형상을 텍스트 정의 파일로부터 자동 생성하고, 선택적으로 FEA 솔버용 메쉬를 내보내는 **CLI 진입점**이다. 파일 헤더의 자기 설명(근거: `KooAutomatedModeller.py:1-9`):

> "Converts ODB++ PCB package definitions into STEP CAD geometry, then generates FEA-ready meshes in multiple solver formats (LS-DYNA .k, Nastran .bdf, ANSYS .cdb, ABAQUS .inp, OBJ)."

진입점은 `sys.argv[1]`의 **모드 토큰**으로 분기된다 (근거: `KooAutomatedModeller.py:774, 789-800`):

| 모드 토큰 | 처리 함수 | 함수 정의 위치 | 비고 |
|---|---|---|---|
| `CAPACITOR` / `CAP` | `GenerateCapacitor` | `:192-213` | `CapacitorManager` 위임 |
| `PCB` | `GeneratePCB` | `:215-225` | `ODBCADManager.ImportPCBs()` |
| `ArrayPCB` | `GenerateArrayPCB` | `:265-275` | `ODBCADManager.ImportArrayPCBs()` |
| `PBA` | `GeneratePBA` | `:229-252` | `ODBCADManager.ImportPBA()` + STEP export |
| `PKG` | `GeneratePackage` | `:118-190` | `PackageUserdefined` (적층 정의) — 메쉬/STEP export |
| `LSDYNADOE` | (분기만 `pass`) | `:799-800` | 미구현 스텁 (`GenerateDOEforLSDYNA`는 `:107-108`에서 print만) |
| `AIRMESH` | `GenerateAirMesh` | `KooAirMesh/` 패키지 위임 | 구현 완료(2026-07, 커밋 8d4a5a4·02bb694) — STEP 공기영역 tet 메시+STL, 회귀 29체크, [generators/airmesh.md](generators/airmesh.md) |

KAM 자체는 얇은 디스패처이며, 실제 형상·메쉬 생성 로직은 모두 `KooODBCADManager` 모듈에 위임된다.

---

## 2. 입력 옵션 · 인자 (표)

### 2-1. CLI 위치 인자

명령 형식: `python KooAutomatedModeller.py <mode> <fileName> [workdir] [displayMode]`

| 위치 | 변수 | 의미 | 근거 |
|---|---|---|---|
| `argv[1]` | `mode` | 생성기 모드 (1절 표) | `KooAutomatedModeller.py:774` |
| `argv[2]` | `fileName` | 정의 텍스트 파일명 (cwd 기준 상대) | `:775` |
| `argv[3]` | `workdir` | 작업 디렉터리. `none`이면 무시, 그 외엔 `os.chdir(cwd/workdir)` | `:776-782` |
| `argv[4]` | `displayMode` | `false`면 비표시, 그 외면 GUI 표시. 기본 `False` | `:783-788` |

- 인자가 3개 미만(`len(sys.argv)<3`)이면 소스에 하드코딩된 디버그용 예시 argv로 대체된다 (근거: `:391-773`, 대부분 주석 처리). 정상 사용 시 모드+파일명을 반드시 넘겨야 한다.
- 헤드리스 환경에서는 `QT_QPA_PLATFORM=offscreen`이 강제되고 GUI 함수가 더미로 치환된다 (근거: `:48, 82-99`). `displayMode=True`를 줘도 offscreen에서는 창이 뜨지 않는다 (`update_shape` offscreen 조기 반환 `:254-256`).

### 2-2. PKG 정의 파일 키워드 (`*Layer` 블록)

`PackageUserdefined.ImportPackage`가 파싱하는 콤마 구분 키워드 (근거: `PackageGenerator.py:153, 300-345`).

| 키워드 | 인자 | 의미 | 근거 (PackageGenerator.py) |
|---|---|---|---|
| `*Layer,<name>` | 레이어명 | 새 적층 레이어 시작 | `:153` |
| `Location` | x,y[,z] | 레이어 위치 | `:295-298` |
| `Length` | xLen,yLen[,matID] | 평면 치수(+재질ID) | `:300-313` |
| `Thickness` | t | 두께(누적 z) | `:340-345` |
| `Cylinder` | x,y,r | 원통 피처(솔더볼 등) | `aptest.txt` |
| `MeshGenerationType` | Solid/Shell, 메쉬타입 | 메쉬 생성 활성화 + 형식 지정 (`meshGenerationMode=True`) | `:315-323` (cf. `PackageLayer.py:177-178`) |
| `MeshSizeInPlane` | size | 면내 메쉬 크기 | `:328-331` |
| `NumberofElementinThickness` | n | 두께 방향 요소 수 | `:332-335` |
| `MeshPath` | 경로 | 메쉬 출력 디렉터리 | `:324-327` |
| `ConformalBufferThickness` | t | Conformal 메쉬 버퍼 두께 | `:336-339` |

> 메쉬 키워드가 하나라도 있으면 해당 레이어의 `meshGenerationMode`가 켜져 메쉬 export 경로로, 없으면 STEP export 경로로 분기된다 (근거: `KooAutomatedModeller.py:149, 185`).

---

## 3. 사용 예제

### 3-1. STEP 형상 생성 (메쉬 키워드 없음 → STEP 출력)

`Examples/automatedmodeller/run.sh` (실제 파일 전문):

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
PYKOOCAE_ROOT="$(cd "$SCRIPT_DIR/../../" && pwd)"
GENERATOR="$PYKOOCAE_ROOT/occProject/Generators/KooAutomatedModeller.py"
python3 "$GENERATOR" PKG aptest.txt
```

입력 `aptest.txt`(발췌, 메쉬 키워드 없음 → `aptest.step` 생성):

```
*Layer,PCB
Location,0,0,0
Length,30.0,30.0
Thickness,0.512
*Layer,SolderJoint
Location,0,0
Length,14.0,16.4
Thickness,0.12
Cylinder,-6.65,7.875,0.11
...   (솔더볼 Cylinder 다수)
```

### 3-2. LS-DYNA 메쉬 생성 (Conformal Hexa)

입력 `aptest_conformal_small.txt`(발췌, 메쉬 키워드 포함 → `.k` 생성):

```
*Layer,PCB
Location,0,0,0
Length,10.0,10.0
Thickness,0.5
MeshGenerationType,Solid,ConformalHexa
MeshSizeInPlane,0.5
NumberofElementinThickness,3
MeshPath,./conformal_mesh_output
*Layer,SolderJoint
Location,0,0
Length,6.0,6.0
Thickness,0.12
MeshGenerationType,Solid,ConformalHexa
MeshSizeInPlane,0.3
NumberofElementinThickness,2
MeshPath,./conformal_mesh_output
Cylinder,-2.0,2.0,0.11
...
```

실행: `python3 KooAutomatedModeller.py PKG aptest_conformal_small.txt`

---

## 4. 동작 원리 (코드 근거)

### 4-1. CLI 분기

`__main__`에서 `mode = sys.argv[1]`, `fileName = sys.argv[2]`을 읽고 (`KooAutomatedModeller.py:774-775`), `argv[3]` 작업 디렉터리·`argv[4]` 표시모드를 처리한 뒤 (`:776-788`), `if/elif` 체인으로 모드별 함수를 호출한다 (`:789-800`).

### 4-2. PKG 경로 (`GeneratePackage`, `:118-190`)

1. `PackageUserdefined()` 생성 후 `package.ImportPackage(inputFilePath)`로 정의 파싱 (`:127-131`, 파서 본체 `PackageGenerator.py:153~`).
2. `package.GenerateShapeList()`로 OCC 형상 리스트 생성 (`:132`, 본체 `PackageGenerator.py:2765~`).
3. **메쉬 모드 분기** — `package.layerList[0].meshGenerationMode`로 판정 (`:149, 185`):
   - `True`: `CreatePartsforPackage` → `CombineNodeManager` → `CreateNodeSetsforPackage` → `CreateDefine` → `CreateContact` → `CreateBoundary` → `CreateSegmentSetsforPackage` → `CreateLoad` → `ExportDynaMesh(dynaFileName)` 순서로 LS-DYNA `.k` 생성 (`:157-172`; 함수 정의 `PackageGenerator.py:1736 / 2514 / 1943 / 2293 / 2356 / 2267 / 2018 / 2101 / 2616`).
   - `False`: `package.ExportPackage()`로 STEP 출력 (`:185-188`; `PackageGenerator.py:3226`).
4. Nastran/ANSYS/ABAQUS/OBJ export는 코드에 존재하나 **전부 주석 처리**되어 있어 현재 출력되지 않는다 (`:167-183`).

### 4-3. 메쉬 키워드 → 모드 전환

`ImportPackage`가 `MeshGenerationType` 등 메쉬 키워드를 만나면 `layer.SetMeshGenerationType(...)`를 호출하고 (`PackageGenerator.py:315-323`), 이 setter가 `self.meshGenerationMode = True`로 설정한다 (근거: `PackageLayer.py:177-178`). 따라서 메쉬 키워드 존재 여부가 STEP/메쉬 출력을 가른다.

### 4-4. PBA/PCB/ArrayPCB 경로

`ODBCADManager.ImportModellingOptions(...)` 후 각각 `ImportPBA` / `ImportPCBs` / `ImportArrayPCBs`를 호출한다 (근거: `:237-238, 223-224, 273-274`). PBA는 추가로 `_total.step` 파일을 export한다 (`:248-250`).

### 4-5. 메쉬 백엔드

메쉬 생성은 gmsh 기반 `KooMeshManagerGMSH`에 위임된다 (근거: `PackageLayer.py:70-73` import, `:429~` 다수 호출). gmsh 바이너리는 빌드 시 `Library/gmsh-4.14.1-Linux64/`로 복사되며 subprocess로 호출된다 (근거: `build_all_python312.sh:167-173`).

---

## 5. 주의사항 · 한계

- **라이선스/IP 게이트**: 실행 시 로컬 IP가 하드코딩 화이트리스트(`registered_ips`, `:340-345`)에 없으면 `exit(0)`로 즉시 종료된다 (근거: `:351-357`). 또한 시스템 시각이 `threshold_date = 2027-12-31`을 넘으면 종료된다 (`:366, 378-381`). 신규 환경/IP에서는 화이트리스트 등록이 선결 조건.
- **Qt re-exec**: Linux에서 `LD_LIBRARY_PATH`(PyQt5 번들 Qt + `Library/OCC`)를 설정한 뒤 `os.execv`로 자기 자신을 재실행한다 (근거: `:22-46`). cwd에 `Library/OCC`가 있어야 OCC 로드가 안정적이다.
- **다중 포맷 export 미동작**: Nastran/ANSYS/ABAQUS/OBJ export는 주석 처리 상태로 현재 LS-DYNA `.k`와 STEP만 실제 출력된다 (근거: `:167-183`).
- **모드 토큰 대소문자**: 비교는 정확 일치(`PKG`, `PBA`, `PCB`, `ArrayPCB`, `CAPACITOR`/`CAP`, `LSDYNADOE`)다 (근거: `:789-800`). 소스 주석의 `LSDynaDOE` 표기(`:691`)는 실제 분기 토큰 `LSDYNADOE`(`:799`)와 다르므로 호출 시 대문자 사용.
- **별도 SIF 없음**: Apptainer `.def`/`.sif` 전용 빌드는 확인되지 않음. KAM은 Nuitka standalone 바이너리로만 배포된다(6절). (확인 필요: 통합 SIF에 KAM이 포함되는지 여부는 별도 컨테이너 정의에서 확인.)

---

## 6. 개발 현황

| 기능 | 분류 | 근거 |
|---|---|---|
| PKG → STEP 형상 생성 | **구현됨** | `GeneratePackage`/`ExportPackage` (`:118-190`), `aptest.step` 산출물 존재 (`Examples/automatedmodeller/`) |
| PKG → LS-DYNA `.k` 메쉬 export | **구현됨** | `ExportDynaMesh` 호출 (`:171-172`), `aptest_conformal_*.k` 산출물(48MB~1GB) 존재 |
| Conformal Hexa 메쉬 | **구현됨** | `MeshGenerationType,Solid,ConformalHexa` 파싱(`PackageGenerator.py:315-323`) + `ConformalBufferThickness`(`:336-339`), `aptest_conformal_small.txt` 예제 |
| PBA / PCB / ArrayPCB 생성 | **구현됨** | `GeneratePBA`/`GeneratePCB`/`GenerateArrayPCB` (`:229-275`) + `ODBCADManager` 위임 |
| Capacitor 생성 | **구현됨** | `GenerateCapacitor` (`:192-213`), `CapacitorManager` |
| Nastran/ANSYS/ABAQUS/OBJ export | **부분구현** | 코드 경로 존재하나 전부 주석 처리(`:167-183`) — 빌드에 미반영 |
| LSDYNADOE 생성 | **계획** (스텁) | 분기 `pass`(`:799-800`), `GenerateDOEforLSDYNA` print만(`:107-108`) |
| 빌드: Nuitka standalone 바이너리 | **구현됨** | `build_automatedmodeller_python3{10,12,13}.sh`, `build_all_python312.sh:85-102` (→ `lib/KooAutomatedModeller/KooAutomatedModeller.bin` + `bin/` 심볼릭링크) |
| 빌드: KAM 제외 옵션 | **구현됨** | `build_without_automatedmodeller.sh` (기존 KAM 바이너리 백업/보존) |
| 빌드: Windows `.exe` | **구현됨** | `build_automatedmodeller_windows.bat` (Nuitka `--windows-console-mode=disable`) |
| 배포: 전용 Apptainer SIF/`.def` | **미확인** | KAM 전용 컨테이너 정의 미발견 (5절 주의사항 참조) |

**관련 git 이력** (KooAutomatedModeller.py 기준): `08ce963`(2026-01-28, occProject 소스 추가) → `94b8f89`(OC/arc 키워드) → `56245e0`(SkipLayer, solder-separated PKG/S STEP export) → `52c528f`(2026-02-01, **PKG mesh export 추가** + SP solid block fix) → `13f01c4`(2026-02-04, KooChainRun 리네임 + apptainer env/bind config). PKG 메쉬 export는 2026-02-01 커밋에서 정식 추가됨.
