# KooAutomatedModeller 개요

> 근거 파일: `occProject/Generators/KooAutomatedModeller.py` (801줄)
> 보조 모듈: `occProject/Generators/KooODBCADManager/` (ODBCADManager / PackageGenerator / PackageLayer / Capacitor)

## 1. 목적 / 개요

`KooAutomatedModeller`(KAM)는 전자 패키지·PCB·PBA(인쇄기판조립)·커패시터의 CAD 형상을 텍스트 정의 파일로부터 자동 생성하고, 선택적으로 LS-DYNA 등 FEA 솔버용 메쉬를 내보내는 CLI 도구다. 파일 헤더의 자기 설명(근거: `KooAutomatedModeller.py:1-9`):

> "Converts ODB++ PCB package definitions into STEP CAD geometry, then generates FEA-ready meshes in multiple solver formats (LS-DYNA .k, Nastran .bdf, ANSYS .cdb, ABAQUS .inp, OBJ)."

동작은 `sys.argv[1]`의 **모드** 토큰으로 분기된다 (근거: `KooAutomatedModeller.py:774-800`):

| 모드 토큰 | 처리 함수 | 입력 종류 | 생성기 상세 |
|---|---|---|---|
| `PKG` | `GeneratePackage` (`KooAutomatedModeller.py:797-798`, 정의 118-190) | `*Layer` 적층 정의 `.txt` | [generators/PKG.md](generators/PKG.md) |
| `PBA` | `GeneratePBA` (`:795-796`, 정의 229-252) | ODB++ 기반 PBA 정의 `.txt` | [generators/PBA.md](generators/PBA.md) |
| `PCB` | `GeneratePCB` (`:791-792`, 정의 215-225) | ODB++ 기반 PCB 정의 `.txt` | [generators/PCB.md](generators/PCB.md) |
| `ArrayPCB` | `GenerateArrayPCB` (`:793-794`, 정의 265-275) | 패널(Array) PCB 정의 `.txt` | [generators/ArrayPCB.md](generators/ArrayPCB.md) |
| `CAPACITOR` / `CAP` | `GenerateCapacitor` (`:789-790`, 정의 192-213) | 커패시터 정의 `.txt` | [generators/Capacitor.md](generators/Capacitor.md) |
| `LSDYNADOE` | (분기만 존재, `pass`) — `GenerateDOEforLSDYNA`는 스텁 | DOE 정의 `.txt` | [generators/LSDynaDOE.md](generators/LSDynaDOE.md) |
| `AIRMESH` | `GenerateAirMesh` → `KooAirMesh` 패키지 (2026-07 신규) | 문제정의 `.json` + STEP | [generators/airmesh.md](generators/airmesh.md) |

보조 진입점 `ImportCADManager(path, pkgFileName, compFileNameList)`는 CLI 분기가 아니라 패키지 1개 + 컴포넌트 N개를 `ODBCADManager`로 로드하는 라이브러리 함수다 (근거: `KooAutomatedModeller.py:110-115`).

> 확인 필요: 모드 토큰 비교는 `LSDYNADOE`(대문자, `:799`)지만, 파일 내부 주석 예시는 `LSDynaDOE`(`:691`)로 표기되어 있다. 대소문자가 정확히 일치해야 분기되므로 실제 호출 시 `LSDYNADOE`를 사용해야 한다. 또한 이 분기는 `pass`이고 `GenerateDOEforLSDYNA`(`:107-108`)는 메시지만 출력하므로 DOE 생성은 미구현이다.

## 2. 입력 옵션 · 인자 (표)

### 2-1. CLI 위치 인자

명령 형식: `python KooAutomatedModeller.py <mode> <fileName> [workdir] [displayMode]`

| 위치 | 변수 | 의미 | 근거 |
|---|---|---|---|
| `argv[1]` | `mode` | 생성기 모드 (위 표) | `KooAutomatedModeller.py:774` |
| `argv[2]` | `fileName` | 정의 텍스트 파일명 (cwd 기준 상대) | `:775` |
| `argv[3]` | `workdir` | 작업 디렉터리. `none`이면 무시, 그 외엔 `os.chdir(cwd/workdir)` | `:776-782` |
| `argv[4]` | `displayMode` | `false`면 비표시, 그 외면 표시(GUI). 기본 `False` | `:783-788` |

인자가 3개 미만(`len(sys.argv)<3`)이면 소스에 하드코딩된 예시 argv로 대체된다 (근거: `KooAutomatedModeller.py:391-773`, 대부분 주석 처리되어 있고 디버그용). 정상 사용 시에는 모드와 파일명을 반드시 넘겨야 한다.

> 헤드리스 환경에서는 `QT_QPA_PLATFORM=offscreen`이 강제되어 GUI 표시는 더미로 대체된다 (근거: `KooAutomatedModeller.py:48`, 82-99). 즉 `displayMode=True`를 줘도 offscreen에서는 실제 창이 뜨지 않는다 (근거: `update_shape` 의 offscreen 조기 반환 `:254-256`).

### 2-2. PKG 정의 파일 키워드 (`*Layer` 블록)

`PackageUserdefined.ImportPackage`가 파싱하는 적층(layer) 정의. 한 줄은 콤마 구분이며 `*Layer,<이름>`으로 새 레이어 시작 (근거: `KooODBCADManager/PackageGenerator.py:153,300-344`).

| 키워드 | 인자 | 의미 | 근거 |
|---|---|---|---|
| `*Layer,<name>` | 레이어명 | 새 적층 레이어 시작 | `aptest.txt`; `PackageGenerator.py:153` |
| `Location` | x,y[,z] | 레이어 위치 | `aptest.txt:2` |
| `Length` | xLen,yLen[,materialID] | 평면 치수(및 재질ID) | `PackageGenerator.py:300-313` |
| `Thickness` | t | 두께(누적 z) | `PackageGenerator.py:340-344` |
| `Box` | x1,y1,x2,y2 | 직사각 피처(예: Subcore 컷) | `aptest.txt` |
| `Cylinder` | x,y,r | 원통 피처(솔더볼 등) | `aptest.txt` (SolderJoint 레이어에 2131개) |
| `MeshGenerationType` | Solid/Shell, 메쉬타입 | 메쉬 생성 활성화 + 형식 지정 | `PackageGenerator.py:315-323` |
| `MeshType` | Tetra/Hexa 등 | 요소 타입 (기본 `Tetra`) | `PackageGenerator.py:318-322` |
| `MeshSizeInPlane` | size | 면내 메쉬 크기 | `PackageGenerator.py:328-331` |
| `NumberofElementinThickness` | n | 두께 방향 요소 수 | `PackageGenerator.py:332-335` |
| `MeshPath` | 경로 | 메쉬 출력 디렉터리 | `PackageGenerator.py:324-327` |
| `ConformalBufferThickness` | t | 컨포멀 메쉬 버퍼 두께 | `PackageGenerator.py:336-339` |

핵심: `MeshGenerationType` / `MeshType` / `MeshSizeInPlane` 중 하나라도 존재하면 해당 레이어의 `meshGenerationMode=True`로 설정되어(근거: `PackageLayer.py:177-193`) 메쉬 내보내기 경로로 진입한다. 이 키워드가 전혀 없으면 STEP 형상만 내보낸다 (근거: `KooAutomatedModeller.py:149,185`).

### 2-3. PCB / PBA / ArrayPCB 정의 파일 키워드

ODB++ 기반 모드는 `ODBCADManager.ImportModellingOptions`로 `*PCB` / `*PBA` / `*ArrayPCB` 블록을 파싱한다 (근거: `ODBCADManager.py:96-372`).

| 블록 | 키워드 | 의미 | 근거 |
|---|---|---|---|
| `*PCB` / `*ArrayPCB` | `FileName` | 부품/PCB 정의 파일(ODB++ zip 등) | `ODBCADManager.py:185-188,124-127` |
| | `Location` | 배치 위치 | `:189-192,128-131` |
| | `Rotation` | 회전(정수) | `:193-196,132-135` |
| | `Mirror` | True/False 미러 | `:197-201,136-142` |
| | `Layup` | 적층 구성 | `:143-147` |
| | `Thickness` | 두께(×1000 스케일) | `:148-153` |
| `*ODB` | `ODBFile` 등 | ODB++ 원본 / BoundaryBox / ZLocation / DetailPAD / MinimumSize / SkipLayer | `:290-372` |

> 위 블록 키워드는 `ODBCADManager.py`의 파서에서 직접 발췌했다. 각 모드별 전체 키워드·기본값은 generators/ 하위 페이지로 분리한다(현재 골격만 존재).

## 3. 사용 예제

### 3-1. PKG 모드 — STEP 형상 생성 (실제 Examples)

`Examples/automatedmodeller/run.sh` (실제 파일 발췌):

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYKOOCAE_ROOT="$(cd "$SCRIPT_DIR/../../" && pwd)"
GENERATOR="$PYKOOCAE_ROOT/occProject/Generators/KooAutomatedModeller.py"

python3 "$GENERATOR" PKG aptest.txt
```

입력 정의 `Examples/automatedmodeller/aptest.txt` (발췌 — 적층 + 솔더볼 원통):

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
Cylinder,-6.3,7.875,0.11
...
*Layer,Subcore
Location,0,0
Length,14.0,16.4
Thickness,0.113
Box,-4.9,-2.28,3.5,4.56
Box,1.75,-1.58,3.15,6.3
```

`aptest.txt`에는 메쉬 키워드가 없으므로 결과는 STEP 형상(`aptest.step`)이다 (근거: `KooAutomatedModeller.py:128,185-188`).

### 3-2. PKG 모드 — 컨포멀 헥사 메쉬 + LS-DYNA `.k` 내보내기

`Examples/automatedmodeller/aptest_conformal_small.txt` (실제 파일 발췌):

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
```

`MeshGenerationType`가 있으므로 `meshGenerationMode=True` → LS-DYNA `.k` 내보내기 경로(파트/노드셋/접촉/경계/세그먼트셋 생성 후 `ExportDynaMesh`)로 진입한다 (근거: `KooAutomatedModeller.py:149-173`). 실제 결과는 `Examples/automatedmodeller/aptest_conformal_small.k` 와 `conformal_mesh_output/`(STL/MSH/GEO 등)에 존재한다.

실행:

```bash
python3 KooAutomatedModeller.py PKG aptest_conformal_small.txt
```

### 3-3. PBA / ArrayPCB 모드 (소스 주석 예시 발췌)

```bash
# PBA
python3 KooAutomatedModeller.py PBA ECADfilesforPBA_P3_Export.txt   # (KooAutomatedModeller.py:629-632)
# ArrayPCB
python3 KooAutomatedModeller.py ArrayPCB ECADNoWarpage.txt          # (KooAutomatedModeller.py:675-678)
```

## 4. 동작 원리 (코드 근거)

1. **부팅 / Qt·OCC 경로 설정**: Linux에서 PyQt5 번들 Qt와 `Library/OCC` 경로를 `LD_LIBRARY_PATH`에 주입한 뒤 자기 자신을 `os.execv`로 재실행한다 (근거: `KooAutomatedModeller.py:22-46`). 그 후 OCC 백엔드를 `pyqt5`로 로드 (`:78-79`).

2. **라이선스·접근 게이트**: `__main__`에서 라이선스 문구 출력 → 현재 IP가 `registered_ips`에 있는지 검사하고, 없으면 `exit(0)` (근거: `KooAutomatedModeller.py:316-357`). 또한 `threshold_date = datetime(2027,12,31)` 초과 시 종료 (근거: `:366,378-381`). 현재 시각은 웹 호출이 아니라 `datetime.now()`를 사용한다 (`:369-370`).

3. **모드 분기**: `mode=argv[1]`, `fileName=argv[2]`, 선택적 `workdir`(chdir), `displayMode` 처리 후 `if/elif`로 생성 함수 호출 (근거: `KooAutomatedModeller.py:774-800`).

4. **PKG 처리 흐름** (`GeneratePackage`, 근거: `KooAutomatedModeller.py:118-190`):
   - `PackageUserdefined()` 생성 → `ImportPackage(inputFilePath)` 로 `*Layer` 정의 파싱 (`PackageGenerator.py:153`).
   - `GenerateShapeList()` 로 OCC 형상 생성 (`PackageGenerator.py:2765`), offscreen이 아니면 `update_shape`로 표시 (`:254-263`).
   - `layerList[0].meshGenerationMode == True` 분기:
     - 메쉬 모드: `CreatePartsforPackage` → `CombineNodeManager` → `CreateNodeSetsforPackage` → `CreateDefine` → `CreateContact` → `CreateBoundary` → `CreateSegmentSetsforPackage` → `CreateLoad` → `ExportDynaMesh(dynaFileName)` (근거: `KooAutomatedModeller.py:157-173`; `PackageGenerator.py:2616`).
     - 형상 모드: `ExportPackage()` 로 STEP 저장 (근거: `:185-188`).
   - Nastran/ANSYS/ABAQUS/OBJ 내보내기 코드는 존재하나 **주석 처리**되어 있다 (근거: `KooAutomatedModeller.py:167-183`). 즉 실제 활성 출력은 LS-DYNA `.k`(및 STEP)뿐이다.

5. **PBA 처리 흐름** (`GeneratePBA`, 근거: `:229-252`): `ODBCADManager.ImportModellingOptions` → `ImportPBA()`(`ODBCADManager.py:629`) → `ExportShapes(<name>_total.step)`.

6. **PCB / ArrayPCB** (`GeneratePCB`/`GenerateArrayPCB`, 근거: `:215-225,265-275`): `ImportModellingOptions` 후 각각 `ImportPCBs()`(`ODBCADManager.py:456`) / `ImportArrayPCBs()`(`:387`) 호출.

7. **Capacitor** (`GenerateCapacitor`, 근거: `:192-213`): `CapacitorManager` → `SetFolderPath` → `ImportCapacitor` → `GenerateCapacitors` → `ExportShapes` → `ExportMeshes`.

## 5. 주의사항 · 한계

- **DOE 미구현**: `LSDYNADOE` 분기는 `pass`이고 `GenerateDOEforLSDYNA(fileName)`는 `print("Generate DOE for LSDYNA")`만 수행한다 (근거: `KooAutomatedModeller.py:107-108,799-800`). 제목의 "LS-DYNA용 DOE"는 이 도구 자체보다는 다운스트림(KooMeshModifier `*_DOE` 모드 등)에서 처리됨에 유의.
- **다중 솔버 출력 비활성**: 헤더 설명과 달리 Nastran/ANSYS/ABAQUS/OBJ 내보내기는 주석 처리 상태이며 현재 활성 출력은 LS-DYNA `.k`와 STEP뿐이다 (근거: `KooAutomatedModeller.py:167-183,150-154`).
- **IP·날짜 게이트**: 등록되지 않은 IP에서는 즉시 종료되고, 2027-12-31 이후엔 실행이 막힌다 (근거: `:340-357,366,378-381`). 서비스 컨테이너의 IP가 `registered_ips`에 포함되어야 한다.
- **헤드리스 GUI**: offscreen에서 표시 함수는 모두 더미이며 `displayMode=True`도 실제 창을 띄우지 못한다 (근거: `:48,82-99,254-256`).
- **인자 미지정 시 디버그 폴백**: `len(sys.argv)<3`이면 소스 하드코딩 argv로 동작이 바뀐다(대부분 주석이지만 일부 활성 라인 존재 `:610-773`). 자동화에서는 항상 명시적으로 모드+파일을 전달할 것.
- **재실행(re-exec)**: 첫 호출 시 `os.execv`로 프로세스를 한 번 재시작한다 (근거: `:22-46`). 환경변수 `_PYKOOCAE_QT_PATH_SET`로 중복 방지. 외부 래퍼가 PID를 추적한다면 유의.
- **모드 토큰 대소문자**: `PKG/PBA/PCB/ArrayPCB/CAPACITOR|CAP/LSDYNADOE`는 정확히 일치해야 한다 (근거: `:789-799`).

## 6. 개발 현황

**부분구현**.

- 구현됨: `PKG`(STEP 형상 + LS-DYNA `.k` 메쉬, 컨포멀 헥사 포함, 근거: `:118-188`, 실제 Examples `aptest*.k`/`aptest*.step` 존재), `PBA`/`PCB`/`ArrayPCB`/`Capacitor` 형상 생성 분기(근거: `:789-798`, `ODBCADManager.py:387,456,629`).
- 미구현/비활성: `LSDYNADOE`(스텁 `pass`, 근거: `:107-108,799-800`), Nastran/ANSYS/ABAQUS/OBJ 내보내기(주석, 근거: `:167-183`).
- 운영 제약: IP 화이트리스트 + 라이선스 만료일 게이트(근거: `:340-381`).

> 확인 필요: 각 생성기(PKG/PBA/PCB/ArrayPCB/Capacitor)별 전체 키워드·기본값·예제는 `generators/` 하위 페이지로 분리 예정이나 현재 디렉터리는 비어 있다(골격만 존재). 본 문서는 개요 + 코드 근거 수준까지만 다룬다.
