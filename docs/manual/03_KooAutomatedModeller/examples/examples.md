# KooAutomatedModeller 예제

> 근거 디렉터리: `Examples/automatedmodeller/`
> 실행 스크립트: `Examples/automatedmodeller/run.sh`
> 생성기: `occProject/Generators/KooAutomatedModeller.py`
> 파서: `occProject/Generators/KooODBCADManager/PackageGenerator.py`, `KooODBCADManager/PackageLayer.py`
> 키워드 전체 표는 상위 [README.md](../README.md) 참조. 본 문서는 `automatedmodeller` 예제 세트(특히 ConformalHexa 적층 메쉬)에 한정한다.

## 1. 목적 / 개요

`Examples/automatedmodeller/`는 `KooAutomatedModeller`(KAM)의 **PKG 모드**(텍스트 적층 정의 → CAD 형상 → 메쉬)를 검증하는 예제 모음이다. 입력은 `*Layer` 블록으로 구성된 `.txt` 정의 파일이며, 솔더볼(Cylinder)·다이(Box) 등의 피처를 가진 다층 전자 패키지를 정의한다.

대표 예제는 두 갈래다.

- **`aptest.txt`** — `run.sh`가 직접 호출하는 기본 예제. PCB + SolderJoint 2개 레이어, 솔더볼은 `Cylinder` 2131개 (근거: `aptest.txt`; `Cylinder` 줄 수 grep 결과 2131). 출력은 `aptest.step`(STEP CAD)이다 — `MeshGenerationType` 키워드가 없으므로 메쉬가 아닌 STEP만 생성된다 (근거: `KooAutomatedModeller.py:185-188`).
- **`aptest_conformal_*.txt`** — `MeshGenerationType,Solid,ConformalHexa` 를 지정한 **컨포멀 헥사 메쉬** 예제. 각 레이어를 통합 conformal 메쉬로 만들고 LS-DYNA `.k`를 출력한다. 규모별로 `small`(PCB+SolderJoint, 6x6 영역 25볼), `buffer`(버퍼 두께 추가), `full`(6레이어 적층, Box 피처 포함), `fixed`/`fixed_coarse`(전체 BGA, MeshSizeInPlane만 다름)로 나뉜다.

> 확인 필요: `run.sh`는 `aptest.txt`(STEP 출력)만 실행한다. ConformalHexa `.txt`들은 별도 실행해야 하며(아래 4-2), 산출물 예시(`conformal_*_output/`, `conformal_examples/*.k`)는 이미 디렉터리에 동봉되어 있다.

## 2. 입력 옵션 · 인자 (표)

### 2-1. CLI 위치 인자 (`run.sh` 기준)

명령 형식: `python KooAutomatedModeller.py <mode> <fileName> [workdir] [displayMode]` (근거: `KooAutomatedModeller.py:774-788`).

| 위치 | 값(예제) | 의미 | 근거 |
|---|---|---|---|
| `argv[1]` | `PKG` | PKG 모드 → `GeneratePackage` 호출 | `run.sh:8`; `KooAutomatedModeller.py:797-798` |
| `argv[2]` | `aptest.txt` | 적층 정의 텍스트 파일(cwd 기준) | `run.sh:8`; `KooAutomatedModeller.py:775` |
| `argv[3]` | (미지정) | 작업 디렉터리. 생략 시 cwd 유지 | `KooAutomatedModeller.py:776-782` |
| `argv[4]` | (미지정) | displayMode. 생략 시 `False` | `KooAutomatedModeller.py:783-788` |

`run.sh`는 스크립트 위치 기준으로 cwd를 옮기고(`cd "$SCRIPT_DIR"`) 프로젝트 루트의 생성기를 절대경로로 호출한다 (근거: `run.sh:2-8`).

### 2-2. 예제 `.txt`에서 사용하는 `*Layer` 키워드

`aptest_conformal_*.txt`가 실제로 사용하는 키워드만 발췌. 파싱은 `ImportPackage`의 `layerGenMode == "Defined"` 분기에서 수행된다 (근거: `PackageGenerator.py:526-833`). 전체 키워드 목록은 README 참조.

| 키워드 | 인자 | 의미 | 근거(file:line) |
|---|---|---|---|
| `*Layer,<name>` | 레이어명 | 새 적층 레이어 시작 (`Defined` 모드) | `PackageGenerator.py:218-233` |
| `Location` | x,y[,z] | 레이어 원점. z 생략 시 누적 z 사용 | `PackageGenerator.py:539-549` |
| `Length` | xLen,yLen[,matID] | 평면 외곽 치수(및 재질ID) | `PackageGenerator.py:550-564` |
| `Thickness` | t | 두께(누적 z에 더함) | `PackageGenerator.py:594-599` |
| `MeshGenerationType` | `Solid`/`Shell`, `ConformalHexa` | 메쉬 생성 활성화 + (생성타입, 메쉬타입) | `PackageGenerator.py:565-573` |
| `MeshSizeInPlane` | size | 면내 메쉬 크기 | `PackageGenerator.py:578-581` |
| `NumberofElementinThickness` | n | 두께 방향 요소 수 | `PackageGenerator.py:586-589` |
| `ConformalBufferThickness` | t | 인접 층 사이 버퍼(Tetra) 두께 | `PackageGenerator.py:590-593`; `PackageLayer.py:206-207` |
| `MeshPath` | 경로 | 메쉬 출력 디렉터리 | `PackageGenerator.py:574-577` |
| `Cylinder` | x,y,r[,Shell\|Solid\|Composite][,matID] | 원통 피처(솔더볼) | `PackageGenerator.py:791-833` |
| `Box` | x,y,xLength,yLength[,Shell\|Solid\|Composite[,…]] | 직사각 피처 | `PackageGenerator.py:869-881` |

> `MeshGenerationType`의 두 번째 인자(메쉬타입)가 없으면 `Defined` 분기 기본값은 `Hexa`다 (근거: `PackageGenerator.py:567-570`). 예제는 모두 명시적으로 `ConformalHexa`를 준다.
>
> `Box` 인자는 코드상 `x, y, xLength, yLength` 순서다(꼭짓점 좌표 2쌍이 아님; 근거: `PackageGenerator.py:878-881`). 예제 `Box,-4.9,-2.28,3.5,4.56`은 원점(-4.9,-2.28)에서 가로 3.5·세로 4.56 사각형을 의미한다.

## 3. 사용 예제 (입력 발췌)

### 3-1. `aptest_conformal_small.txt` (PCB + SolderJoint, 25볼) — 발췌

원문 그대로 (근거: `Examples/automatedmodeller/aptest_conformal_small.txt:1-19`):

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
Cylinder,-1.0,2.0,0.11
...(SolderJoint 레이어에 Cylinder 25개)
```

### 3-2. `aptest_conformal_buffer.txt` — 버퍼 두께 추가

`small`과 거의 동일하나 PCB 레이어에 `ConformalBufferThickness,0.05`가 추가되어 인접 층 사이 Tetra 버퍼를 둔다 (근거: `aptest_conformal_buffer.txt:8`).

```
*Layer,PCB
Location,0,0,0
Length,10.0,10.0
Thickness,0.5
MeshGenerationType,Solid,ConformalHexa
MeshSizeInPlane,0.3
NumberofElementinThickness,3
ConformalBufferThickness,0.05
MeshPath,./conformal_buffer_output
*Layer,SolderJoint
...
```

### 3-3. `aptest_conformal_full.txt` — 6레이어 적층 + Box 피처

PCB / Subcore / EMCDIE / ISUB / DRAMSUB / DRAMEMC 6개 레이어. Subcore 레이어가 `Box` 2개로 다이 컷을 정의한다 (근거: `aptest_conformal_full.txt:10-20`):

```
*Layer,Subcore
Location,0,0
Length,14.0,16.4
Thickness,0.113
MeshGenerationType,Solid,ConformalHexa
MeshSizeInPlane,0.5
NumberofElementinThickness,2
ConformalBufferThickness,0.05
MeshPath,./conformal_full_output
Box,-4.9,-2.28,3.5,4.56
Box,1.75,-1.58,3.15,6.3
```

### 3-4. CLI 실행 (`run.sh`)

`run.sh` 전문 (근거: `Examples/automatedmodeller/run.sh:1-8`):

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYKOOCAE_ROOT="$(cd "$SCRIPT_DIR/../../" && pwd)"
GENERATOR="$PYKOOCAE_ROOT/occProject/Generators/KooAutomatedModeller.py"

python3 "$GENERATOR" PKG aptest.txt
```

## 4. 동작 원리 (코드 근거)

### 4-1. PKG 모드 전체 흐름

1. `mode = sys.argv[1]`, `fileName = sys.argv[2]` 파싱 (근거: `KooAutomatedModeller.py:774-775`).
2. `mode == "PKG"` → `GeneratePackage(fileName, displayMode)` (근거: `KooAutomatedModeller.py:797-798`).
3. `PackageUserdefined()` 생성 후 `package.ImportPackage(inputFilePath)`로 `.txt`를 파싱 (근거: `KooAutomatedModeller.py:127-131`).
4. `package.GenerateShapeList()`로 형상 생성 (근거: `KooAutomatedModeller.py:132`; 정의 `PackageGenerator.py:2765`).
5. 분기:
   - `meshGenerationMode == True` → `CreatePartsforPackage` → `ExportDynaMesh(<name>.k)` 로 LS-DYNA `.k` 출력 (근거: `KooAutomatedModeller.py:149-173`). NASTRAN/ANSYS/ABAQUS/OBJ 내보내기는 주석 처리되어 비활성 (근거: `KooAutomatedModeller.py:167-183`).
   - `meshGenerationMode == False` → `ExportPackage()` 로 STEP `.step` 출력 (근거: `KooAutomatedModeller.py:185-188`).

`meshGenerationMode`는 `MeshGenerationType`/`MeshSizeInPlane`/`MeshType` 등 메쉬 키워드를 만나면 `True`가 된다 (근거: `PackageLayer.py:177-204`). 따라서 `aptest.txt`(메쉬 키워드 없음) → STEP, `aptest_conformal_*.txt`(`MeshGenerationType` 있음) → `.k`.

### 4-2. ConformalHexa 처리

- `MeshGenerationType,Solid,ConformalHexa` 파싱 시 `SetMeshGenerationType("Solid")` + `SetMeshType("ConformalHexa")` 호출 (근거: `PackageGenerator.py:565-573`).
- `meshType == "ConformalHexa"`인 레이어는 개별 메쉬를 건너뛰고 형상만 만든 뒤(근거: `PackageLayer.py:389-391`, `598-600`), `GenerateShapeList`에서 통합 conformal 메쉬로 처리된다.
- 인접 레이어의 `Cylinder` footprint를 현재 레이어로 전달해 conformal 접합을 맞춘다 (근거: `PackageGenerator.py:2844-2860`). 생성된 conformal 메쉬 shape는 `layer.conformalMeshList`에 모여 `shapeList`에 추가된다 (근거: `PackageGenerator.py:2897-2899`).
- `ConformalBufferThickness`가 있으면 인접 ConformalHexa 층 사이에 Tetra 버퍼를 만들고 경계 노드를 merge한다 (근거: `PackageGenerator.py:2938-2968`, 버퍼 노드 merge `2625-2627`).

산출물 예시는 `conformal_*_output/` 디렉터리에 레이어별 `*_ConformalMesh.{msh,stl,geo}`와 `*_topface.brep`/`*_bottomface.brep`(gmsh 중간 산물)로 남아 있고, 최종 LS-DYNA `.k`는 `conformal_examples/aptest_conformal_*.k` 로 동봉되어 있다.

## 5. 주의사항 · 한계

- **IP 화이트리스트 + 라이선스 기한**: 실행 시 로컬 IP가 등록 목록에 없으면 `Access denied` 후 `exit(0)`로 종료된다 (근거: `KooAutomatedModeller.py:340-357`). 또한 현재 날짜가 `2027-12-31`을 넘으면 종료된다 (근거: `KooAutomatedModeller.py:366,378-381`). 등록되지 않은 환경에서는 예제가 실행되지 않을 수 있다 — 확인 필요.
- **OCC/Qt 라이브러리 경로 의존**: 리눅스에서는 `LD_LIBRARY_PATH`에 PyQt5 번들 Qt와 `<cwd>/Library/OCC`를 추가하고 자기 자신을 re-exec한다 (근거: `KooAutomatedModeller.py:22-60`). 즉 cwd에 `Library/OCC`가 있어야 OCC 로딩이 안정적이다 — 확인 필요(예제 디렉터리에는 `Library/OCC`가 없음).
- **헤드리스**: `QT_QPA_PLATFORM=offscreen` 강제로 GUI는 더미 처리되어 `displayMode=True`여도 창이 뜨지 않는다 (근거: `KooAutomatedModeller.py:48,82-99`, `254-256`).
- **출력 형식 제약**: 현재 PKG 메쉬 출력은 LS-DYNA `.k`만 활성. NASTRAN/ANSYS/ABAQUS/OBJ는 소스에서 주석 처리됨 (근거: `KooAutomatedModeller.py:167-183`).
- **대용량 산출물**: ConformalHexa 전체 BGA(`aptest_conformal_fixed.k`)는 ~950MB에 달한다(디렉터리 `ls` 기준). `MeshSizeInPlane`/`NumberofElementinThickness` 설정에 따라 산출물 크기가 급증한다.
- **보조 스크립트 불일치**: `check_cylinders.py`는 `KooAutomatedModeller` 를 클래스(`ReadInputFile`/`SetMode`/`packageGenerator`)로 임포트하지만, 현재 `KooAutomatedModeller.py`는 함수 기반이라 해당 클래스/메서드가 없다 (근거: `check_cylinders.py` vs `KooAutomatedModeller.py` 전체). 이 헬퍼는 현 버전과 맞지 않음 — 확인 필요.

## 6. 개발 현황

**부분구현.**

- 구현됨: PKG 모드의 STEP 생성(`ExportPackage`), LS-DYNA `.k` 생성(`ExportDynaMesh`), ConformalHexa 통합 메쉬 + ConformalBufferThickness 버퍼. `Cylinder`/`Box`/적층 키워드 파싱 (근거: `KooAutomatedModeller.py:149-188`; `PackageGenerator.py:526-833,2844-2899,2938-2968`). 산출물(`.k`, `*_ConformalMesh.*`)이 예제 디렉터리에 실제로 존재해 동작이 확인됨.
- 미구현/비활성: PKG 메쉬의 NASTRAN/ANSYS/ABAQUS/OBJ 내보내기는 주석 처리 (근거: `KooAutomatedModeller.py:167-183`).
- 확인 필요: ① IP 화이트리스트/라이선스 게이트로 임의 환경에서의 재현 여부, ② cwd `Library/OCC` 의존(예제 디렉터리에 부재), ③ `check_cylinders.py` 헬퍼가 현 함수 기반 API와 불일치.
