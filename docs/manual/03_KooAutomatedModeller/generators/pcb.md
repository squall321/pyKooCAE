# KooAutomatedModeller: PCB 생성

## 1. 목적 / 개요

KooAutomatedModeller(KAM)의 PCB 생성 기능은 ECAD(ODB++) 기반 PCB 정의를 읽어 STEP(CAD) 형상으로 변환한다. 모듈 헤더에 그 목적이 명시되어 있다 — "Converts ODB++ PCB package definitions into STEP CAD geometry"(`occProject/Generators/KooAutomatedModeller.py:1-9`).

PCB 생성은 두 가지 모드로 제공된다.

- **PCB 모드** (`GeneratePCB`): 단일 PCB 보드를 STEP 솔리드로 생성. `occProject/Generators/KooAutomatedModeller.py:215-225`
- **ArrayPCB 모드** (`GenerateArrayPCB`): 어레이(패널) 형태의 PCB를 STEP 솔리드로 생성. `occProject/Generators/KooAutomatedModeller.py:265-275`

두 함수 모두 텍스트 설정 파일(`.txt`)을 입력으로 받아 `ODBCADManager`를 통해 ECAD 피처 파일을 적층(layup)·두께·위치·회전 정보와 결합하여 STEP 파일로 내보낸다.

---

## 2. 입력 옵션 · 인자

### 2-1. CLI 인자 (sys.argv)

`occProject/Generators/KooAutomatedModeller.py:774-794` 의 디스패치 로직 기준.

| 위치 | 인자 | 의미 | 비고 |
|------|------|------|------|
| `sys.argv[1]` | mode | `"PCB"` 또는 `"ArrayPCB"` | 대소문자 구분. `PCB`→`GeneratePCB`, `ArrayPCB`→`GenerateArrayPCB` |
| `sys.argv[2]` | fileName | 설정 텍스트 파일명(`.txt`) | 현재 작업 디렉터리 기준 (`os.getcwd()`) |
| `sys.argv[3]` | workdir | 작업 디렉터리 (선택) | `"none"`이면 무시, 아니면 해당 폴더로 `chdir` (`:776-782`) |
| `sys.argv[4]` | displayMode | `"false"`/그 외 (선택) | PCB/ArrayPCB 경로에서는 사용되지 않음 (PBA/PKG 모드용) |

주의: `displayMode` 인자는 `GeneratePBA`/`GeneratePackage`에만 전달되며, `GeneratePCB`/`GenerateArrayPCB` 호출 시그니처에는 들어가지 않는다(`:792-794`).

### 2-2. 설정 텍스트 파일 옵션

`ODBCADManager.ImportModellingOptions`가 파싱한다. `*PCB` 블록은 `occProject/Generators/KooODBCADManager/ODBCADManager.py:172-232`, `*ArrayPCB` 블록은 `:111-171`. 두 블록의 키는 동일하다(CSV, `,` 구분).

| 키 | 형식 | 의미 | 근거 (file:line) |
|----|------|------|------------------|
| `FileName` | `FileName,feature.txt` | ECAD 피처 파일명 (단위 PCB) | `ODBCADManager.py:185-188` / Array `:124-127` |
| `Location` | `Location,x,y,z` | 배치 위치 (float 3개) | `:189-192` / `:128-131` |
| `Rotation` | `Rotation,deg` | 회전 각도 (int) | `:193-196` / `:132-135` |
| `Mirror` | `Mirror,True\|False` | 미러 여부 | `:197-203` / `:136-142` |
| `Layup` | `Layup,L1,L2,...` | 적층 레이어 이름 목록 | `:204-208` / `:143-147` |
| `Thickness` | `Thickness,t1,t2,...` | 레이어별 두께. 입력값에 `*1000` 적용됨 | `:209-215` / `:148-154` |
| `MaterialFileName` | `MaterialFileName,MAT_*.txt` | 재료 파일명 | `:216-219` / `:155-158` |
| `PatternFeatures` | `PatternFeatures,<폴더경로>,<레이어명>` | 레이어별 패턴 피처 폴더 매핑 (dict) | `:220-223` / `:159-162` |
| `SymbolsFolder` | `SymbolsFolder,symbols` | 심볼 폴더 | `:224-227` / `:163-166` |
| `Warpage` | `Warpage,None\|<파일>` | 워피지 파일. `None`이면 평면 생성 | `:228-231` / `:167-170` |

`#`로 시작하는 줄은 주석 처리되어 무시된다(`ODBCADManager.py:109-110`). `*`로 시작하는 다음 키워드를 만나면 해당 블록이 종료된다(`:182-184` / `:121-123`).

`Thickness` 값에 `*1000` 스케일이 자동 적용되는 점에 유의한다 — 입력 단위(예: mm)가 내부 단위로 변환되는 것으로 보이나, 정확한 단위 정의는 본문에 명시되어 있지 않다 (확인 필요).

---

## 3. 사용 예제

### 3-1. CLI 명령

`Examples/automatedmodeller/run.sh:8` 의 실제 호출 패턴(이 예제는 PKG 모드)을 PCB 모드에 적용하면:

```bash
python3 occProject/Generators/KooAutomatedModeller.py PCB ECADNowarpage.txt
```

ArrayPCB 모드:

```bash
python3 occProject/Generators/KooAutomatedModeller.py ArrayPCB ECADNowarpage.txt
```

작업 디렉터리를 지정하려면 3번째 인자를 추가한다(`:776-782`):

```bash
python3 occProject/Generators/KooAutomatedModeller.py PCB feature.txt myworkdir
```

### 3-2. 설정 텍스트 파일 예제

실제 예제 파일 `occProject/Generators/dist/KooAutomatedModeller2/ECADNowarpage.txt` 발췌 (가공 없음):

```
*ArrayPCB
FileName,ArrayTestFeature.txt
Location,0.0,0.0,0.0
Rotation,0
Mirror,False
Layup,CUPPGCOMP,PPGT2,CUPPG2,PPG23,CUPPG3,PPG34,CUPPG4,PPG45,CUPPG5,PPG56,CUPPG6,PPG67,CUPPG7,PPG78,CUPPGSOLD
Thickness,2.0E-05,3.0E-05,1.2E-05,2.5E-05,1.2E-05,2.5E-05,1.2E-05,5.0E-05,1.2E-05,2.5E-05,1.2E-05,2.5E-05,1.2E-05,3.0E-05,2.0E-05
MaterialFileName,MAT_EM370Z_T4_4c_D18.txt
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPGCOMP
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPG2
SymbolsFolder,symbols
Warpage,None
*PCB
FileName,feature.txt
Location,0.0,0.0,0.0
Rotation,90
Mirror,True
Layup,CUPPGCOMP,PPGT2,CUPPG2,PPG23,CUPPG3,PPG34,CUPPG4,PPG45,CUPPG5,PPG56,CUPPG6,PPG67,CUPPG7,PPG78,CUPPGSOLD
Thickness,2.0E-05,3.0E-05,1.2E-05,2.5E-05,1.2E-05,2.5E-05,1.2E-05,5.0E-05,1.2E-05,2.5E-05,1.2E-05,2.5E-05,1.2E-05,3.0E-05,2.0E-05
MaterialFileName,MAT_EM370Z_T4_4c_D18.txt
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPGCOMP
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPG2
SymbolsFolder,symbols
Warpage,None
*Packages
FileName,package.txt
SolderThickness,CMP 1, 0.03
SolderThickness,CMP 2, 0.04
*ComponentTop
FileName,componenttop.txt
*ComponentBottom
FileName,componentbottom.txt
*End
```

(`*Packages`, `*ComponentTop`, `*ComponentBottom` 블록은 패키지/컴포넌트용이며 PCB 생성 자체에는 영향을 주지 않는다. 한 파일에 `*PCB`/`*ArrayPCB`가 여러 개 들어가면 리스트에 누적되어 각각 처리된다 — `ImportPCBs`/`ImportArrayPCBs`가 인덱스 루프로 순회.)

---

## 4. 동작 원리 (코드 근거)

### PCB 모드 (`GeneratePCB`)

1. `ODBCADManager()` 인스턴스 생성, 현재 경로 확인 — `KooAutomatedModeller.py:217-221`
2. `odbManager.ImportModellingOptions(curPath, fileName)` — 설정 텍스트 파싱, `*PCB` 블록을 읽어 `PCBFileList` 등 리스트에 적재 — `:223`, 파서 본문 `ODBCADManager.py:172-232`
3. `odbManager.ImportPCBs()` — 실제 형상 생성 — `:224`

`ImportPCBs`(`ODBCADManager.py:456-538`)의 동작:

- 각 PCB 항목에 대해 `load_PCB(curPath, fileName)`로 ECAD 피처 파일 로드 — `:461`, `load_PCB`는 `pcbManager.ImportPCBfromOCBTwo(stream)` 호출(`:809-814`)
- `ImportPCBfromOCBTwo`는 `CreatePCB()` 후 `ImportPCBFeature`로 폴리곤을 추가 — `PCBManager.py:106-113`
- 로드된 PCB에 `SetLayup`/`SetThickness`/`SetMaterialFile`/`SetPatternFeatures`/`SetSymbolsFolder`/`SetLocation`/`SetRotation`/`SetMirror`/`SetWarpageFile` 적용 — `:463-471` (Set 메서드는 `PCB.py:50-107`)
- `Warpage`가 `"None"`이면 `curPCB.Generate()`(평면 솔리드), 아니면 `curPCB.GenerateSolidwithSurface()` — `:502-505`
  - `PCB.Generate()`(`PCB.py:387-412`): 각 폴리곤을 2D 좌표→`gp_Pnt`→`BRepBuilderAPI_MakePolygon`→`MakeFace`→`BRepPrimAPI_MakePrism`(두께 = `TotalThickness()`)로 솔리드 압출
- STEP 저장: 파일명 `PCB_<i>.stp`, `STEPControl_Writer`로 각 shape를 `Transfer` 후 `Write` — `:519-534`

### ArrayPCB 모드 (`GenerateArrayPCB`)

구조는 동일하되 `ImportArrayPCBs`(`ODBCADManager.py:387-453`)를 호출:

- `load_arrayPCB` → `pcbManager.ImportArrayPCBfromODB(stream)` — `:816-820`, `PCBManager.py:115-127`. ArrayPCB는 단위/어레이/홀/브리지 폴리곤을 별도로 적재(`AddUnitPolygons`/`AddArrayPolygons`/`AddHolePolygons`/`AddBridgePolygons`)
- `Warpage`가 `"None"`이면 `curPCB.Generate()`(`ArrayPCB.py:261`), 아니면 `curPCB.GenerateSolidwithWarpage()`(`ArrayPCB.py:164`) — `ODBCADManager.py:430-433`
- STEP 저장: 파일명 `ArrayPCB_<i>.stp` — `:443-453`

### 시각화 / 오프스크린 처리

`QT_QPA_PLATFORM == "offscreen"`일 때 GUI 함수가 더미로 대체되어 헤드리스 실행을 지원한다 — `ODBCADManager.py:406-428`(Array), `:475-497`(PCB).

---

## 5. 주의사항 · 한계

- **출력 파일명이 고정 패턴**: PCB는 `PCB_<인덱스>.stp`, ArrayPCB는 `ArrayPCB_<인덱스>.stp`로 현재 작업 디렉터리에 저장된다(`ODBCADManager.py:520`, `:444`). 입력 파일명이 출력명에 반영되지 않으므로 여러 입력을 같은 폴더에서 돌리면 덮어쓰기 위험이 있다.
- **mode 문자열 대소문자 구분**: `"PCB"`, `"ArrayPCB"` 정확히 일치해야 한다(`KooAutomatedModeller.py:791-794`). (참고로 CAPACITOR만 `"CAP"` 단축형을 허용 — `:789`)
- **Thickness 단위 스케일**: 입력 두께에 `*1000`이 자동 적용된다(`ODBCADManager.py:151`, `:212`). 입력/출력 단위계는 코드상 주석이 없어 사용자가 직접 확인해야 한다 (확인 필요).
- **PatternFeatures 경로 구분자**: 예제 파일은 Windows 경로 구분자(`.\steps\...`)를 사용한다. Linux 환경에서의 경로 처리 동작은 코드만으로 확정 불가 (확인 필요).
- **ECAD 피처 파일 자체의 포맷**: `FileName`이 가리키는 `feature.txt`/`ArrayTestFeature.txt`의 내부 포맷은 `odbpImporter.ImportPCBFeature`/`ImportArrayFeature`가 파싱하며, 본 문서 범위 밖이다 (확인 필요).
- **`displayMode` 무시**: PCB/ArrayPCB 경로는 4번째 인자를 받지 않는다. 시각화는 `QT_QPA_PLATFORM` 환경변수로만 제어된다.

---

## 6. 개발 현황

**구현됨**

근거:
- `GeneratePCB`/`GenerateArrayPCB` 함수가 정의·디스패치 연결되어 있음 — `KooAutomatedModeller.py:215-225`, `:265-275`, `:791-794`
- 입력 파서(`ImportModellingOptions`의 `*PCB`/`*ArrayPCB` 블록), 형상 생성(`PCB.Generate`/`ArrayPCB.Generate`/`GenerateSolidwithWarpage`), STEP 출력(`STEPControl_Writer`)까지 전 경로가 코드로 존재 — `ODBCADManager.py:172-232`, `:387-538`, `PCB.py:387-412`
- 실제 입력 예제 파일 존재 — `occProject/Generators/dist/KooAutomatedModeller2/ECADNowarpage.txt`

단, 본 매뉴얼 작성 시점에 `mode=PCB`/`ArrayPCB`의 실제 e2e 실행 로그·산출 STEP은 직접 검증하지 않았다. CLI 호출 예제는 `run.sh`의 PKG 모드 패턴을 근거로 유추했다 (PCB/ArrayPCB 전용 run 스크립트는 확인되지 않음 — 확인 필요).
