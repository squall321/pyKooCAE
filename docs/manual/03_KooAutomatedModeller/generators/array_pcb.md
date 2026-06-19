# KooAutomatedModeller: Array PCB 생성

## 1. 목적 / 개요

KooAutomatedModeller(KAM)의 **Array PCB 생성** 기능(`GenerateArrayPCB`)은 ECAD(ODB++) 기반 어레이(패널) PCB 정의를 읽어 STEP(CAD) 솔리드 형상으로 변환한다. 모듈 헤더에 그 목적이 명시되어 있다 — "Converts ODB++ PCB package definitions into STEP CAD geometry"(`occProject/Generators/KooAutomatedModeller.py:1-9`).

단위 PCB 1개를 생성하는 `GeneratePCB`(PCB 모드)와 달리, Array PCB 모드는 어레이(전체 패널) 윤곽에서 홀(구멍)을 잘라내고 브리지를 합쳐(boolean cut/fuse) 패널 형상을 만들고, 그 위에 단위 PCB 형상을 별도로 생성한다(`ArrayPCB.py:261-314`).

함수 본체는 매우 짧으며(`KooAutomatedModeller.py:265-275`), 실제 작업은 `ODBCADManager`의 두 메서드에 위임된다.

- `ImportModellingOptions(curPath, fileName)` — 텍스트 설정 파일 파싱
- `ImportArrayPCBs()` — 형상 생성 + STEP 저장

---

## 2. 입력 옵션 · 인자

### 2-1. CLI 인자 (sys.argv)

`occProject/Generators/KooAutomatedModeller.py:774-794` 의 디스패치 로직 기준.

| 위치 | 인자 | 의미 | 비고 |
|------|------|------|------|
| `sys.argv[1]` | mode | `"ArrayPCB"` | 대소문자 구분. `ArrayPCB`→`GenerateArrayPCB` (`:793-794`) |
| `sys.argv[2]` | fileName | 설정 텍스트 파일명(`.txt`) | 현재 작업 디렉터리(`os.getcwd()`) 기준 (`:269`) |
| `sys.argv[3]` | workdir | 작업 디렉터리 (선택) | `"none"`이면 무시, 아니면 해당 폴더로 `chdir` (`:776-782`) |
| `sys.argv[4]` | displayMode | (선택) | ArrayPCB 경로에는 전달되지 않음. `GenerateArrayPCB(fileName)`은 단일 인자 (`:794`) |

`GenerateArrayPCB`는 `fileName` 한 개만 받는다(`:265`, `:794`). 따라서 4번째 인자 `displayMode`는 ArrayPCB 모드에 영향을 주지 않으며, 시각화 여부는 `QT_QPA_PLATFORM` 환경변수로만 제어된다(`ODBCADManager.py:406-428`).

코드 내 주석 처리된 호출 예시(근거):
```python
sys.argv.append("ArrayPCB")
sys.argv.append("ECADNoWarpage.txt")
```
(`KooAutomatedModeller.py:676-678`, 워피지 미반영 / `:653-654`에는 `DieSample.txt` 예시도 주석으로 존재)

### 2-2. 설정 텍스트 파일의 `*ArrayPCB` 블록 옵션

`ODBCADManager.ImportModellingOptions`가 파싱한다. `*ArrayPCB` 블록은 `occProject/Generators/KooODBCADManager/ODBCADManager.py:111-171`. CSV(`,`) 구분이며, `*ArrayPCB` 다음 줄부터 `*`로 시작하는 다음 키워드를 만나기 전까지가 한 블록이다(`:121-123`).

| 키 | 형식 | 의미 | 근거 (file:line) |
|----|------|------|------------------|
| `FileName` | `FileName,ArrayFeature.txt` | 어레이 ECAD 피처 파일명 | `ODBCADManager.py:124-127` |
| `Location` | `Location,x,y,z` | 배치 위치 (float 목록) | `:128-131` |
| `Rotation` | `Rotation,deg` | 회전 각도 (int) | `:132-135` |
| `Mirror` | `Mirror,True\|False` | 미러 여부 (정확히 `True`일 때만 True) | `:136-142` |
| `Layup` | `Layup,L1,L2,...` | 적층 레이어 이름 목록 | `:143-147` |
| `Thickness` | `Thickness,t1,t2,...` | 레이어별 두께. **입력값에 `*1000` 자동 적용** | `:148-154` |
| `MaterialFileName` | `MaterialFileName,MAT_*.txt` | 재료 파일명 | `:155-158` |
| `PatternFeatures` | `PatternFeatures,<폴더경로>,<레이어명>` | 레이어별 패턴 피처 폴더 매핑(dict: `{레이어명: 폴더경로}`) | `:159-162` |
| `SymbolsFolder` | `SymbolsFolder,symbols` | 심볼 폴더 | `:163-166` |
| `Warpage` | `Warpage,None\|<파일>` | 워피지 파일. `None`이면 평면(flat) 생성 | `:167-170` |

- `#`로 시작하는 줄은 주석으로 무시된다(`:109-110`).
- 각 키는 리스트에 누적되므로, 한 파일에 `*ArrayPCB` 블록이 여러 개 있으면 `ImportArrayPCBs`의 인덱스 루프가 각각 순회·생성한다(`:390`).

---

## 3. 사용 예제

### 3-1. CLI 명령

코드 내 주석(`KooAutomatedModeller.py:676-678`)을 근거로 한 호출 형태:

```bash
python KooAutomatedModeller.py ArrayPCB ECADNoWarpage.txt
```

도움말 문자열에도 동일 형식이 명시되어 있다 — `'ArrayPCB 생성 : python KooAutomatedModeller.py ArrayPCB [fileName]'`(`:769`).

작업 디렉터리를 3번째 인자로 지정 가능(`:776-782`):

```bash
python KooAutomatedModeller.py ArrayPCB ECADFiles.txt myworkdir
```

### 3-2. 설정 텍스트 파일 예제 (`*ArrayPCB` 블록)

실제 예제 파일 `occProject/Generators/KooODBCADManager/ECADFiles.txt:1-18` 발췌 (가공 없음):

```
*ArrayPCB
FileName,ArrayFeature.txt
Location,0.0,0.0,0.0
Rotation,0.0
Mirror,False
Layup,CUPPGCOMP,PPGT2,CUPPG2,PPG23,CUPPG3,PPG34,CUPPG4,PPG45,CUPPG5,PPG56,CUPPG6,PPG67,CUPPG7,PPG78,CUPPGSOLD
Thickness,2.0E-05,3.0E-05,1.2E-05,2.5E-05,1.2E-05,2.5E-05,1.2E-05,5.0E-05,1.2E-05,2.5E-05,1.2E-05,2.5E-05,1.2E-05,3.0E-05,2.0E-05
MaterialFileName,MAT_EM370Z_T4_4c_D18.txt
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPGCOMP
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPG2
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPG3
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPG4
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPG5
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPG6
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPG7
PatternFeatures,.\steps\array\layers\comp.gbr\features,CUPPGSOLD
SymbolsFolder,symbols
Warpage,ArrayWarpage.txt
```

(위 예제는 `Warpage,ArrayWarpage.txt`이므로 워피지 반영 경로로 동작한다. 평면 생성을 원하면 `Warpage,None`으로 설정한다 — `ODBCADManager.py:430-433`.)

---

## 4. 동작 원리 (코드 근거)

### `GenerateArrayPCB(fileName)` (`KooAutomatedModeller.py:265-275`)

1. `ODBCADManager()` 인스턴스 생성, 현재 경로/파일 경로 출력 — `:267-271`
2. `odbManager.ImportModellingOptions(curPath, fileName)` — 설정 텍스트 파싱, `*ArrayPCB` 블록을 읽어 `PCBArrayFileList`, `PCBArrayLayupList`, … 등 리스트에 적재 — `:273`, 파서 본문 `ODBCADManager.py:111-171`, 리스트 초기화 `:41-50`
3. `odbManager.ImportArrayPCBs()` — 실제 형상 생성 + STEP 저장 — `:274`

### `ImportArrayPCBs()` (`ODBCADManager.py:387-453`)

각 어레이 항목(`PCBArrayFileList[i]`)에 대해 인덱스 루프(`:390`)로:

1. `load_arrayPCB(curPath, fileName)` → `pcbManager.ImportArrayPCBfromODB(stream)`로 어레이 피처 파일 로드 — `:392`, `:816-820`
   - `ImportArrayPCBfromODB`(`PCBManager.py:115-127`)는 `odbpImporter.ImportArrayFeature`로 단위/어레이/홀/브리지 폴리곤 4종을 읽어 `AddUnitPolygons`/`AddArrayPolygons`/`AddHolePolygons`/`AddBridgePolygons`로 적재
2. 로드된 객체에 설정 적용 — `:394-402`: `SetLayup` / `SetThickness` / `SetMaterialFile` / `SetPatternFeatures` / `SetSymbolsFolder` / `SetLocation` / `SetRotation` / `SetMirror` / `SetWarpageFile`
3. 형상 생성 분기 — `:430-433`
   - `Warpage == "None"` → `curPCB.Generate()` (평면 솔리드, `ArrayPCB.py:261-314`)
   - 그 외 → `curPCB.GenerateSolidwithWarpage()` (워피지 반영, `ArrayPCB.py:164`)
4. STEP 저장 — `:442-453`: 파일명 `ArrayPCB_<i>.stp`, `STEPControl_Writer`로 각 shape를 `STEPControl_AsIs`로 `Transfer` 후 `Write`. `status == 0`이면 "Error: can't write file." 출력

### `ArrayPCB.Generate()` 의 boolean 처리 (`ArrayPCB.py:261-314`)

- 두께 `thickness = TotalThickness()`로 각 폴리곤을 압출(`Polygon.Generate(thickness, ...)`)
- 대각선 길이(`DiagonalLength()`)가 가장 큰 어레이 폴리곤을 베이스(`shapeArray`)로, 나머지 작은 어레이 폴리곤은 잘라낼(cut) 형상으로 분류 — `:270-281`
- 베이스에서 작은 어레이 형상을 `BRepAlgoAPI_Cut`으로 차감 — `:293-297`
- 브리지 폴리곤은 `BRepAlgoAPI_Fuse`로 융합 — `:298-302`
- 단위 폴리곤은 각각 홀 폴리곤으로 `Cut` 처리 후 결과 리스트에 추가 — `:306-313`
- 반환: `[shapeArray] + 단위 형상들` (여러 shape의 리스트) — `:304-314`

### 시각화 / 오프스크린 처리

`QT_QPA_PLATFORM == "offscreen"`일 때 GUI 함수가 더미로 대체되어 헤드리스 실행을 지원한다 — `ODBCADManager.py:406-428`. (단, 실제 `DisplayShape`/`FitAll`/`start_display` 호출도 `offscreen` 분기 안에 있어 GUI 모드 분기 시 동작 경로 차이가 있을 수 있음 — `:435-440` 참고)

---

## 5. 주의사항 · 한계

- **출력 파일명이 고정 패턴**: `ArrayPCB_<인덱스>.stp`로 현재 작업 디렉터리에 저장된다(`ODBCADManager.py:444`). 입력 파일명이 출력명에 반영되지 않으므로, 같은 폴더에서 여러 입력을 돌리면 덮어쓰기 위험이 있다.
- **mode 문자열 대소문자 구분**: `"ArrayPCB"` 정확히 일치해야 한다(`KooAutomatedModeller.py:793`). PCB(`"PCB"`)/CAPACITOR(`"CAP"`)와 다른 단축형은 없다.
- **`displayMode` 무시**: ArrayPCB 경로는 4번째 인자를 받지 않는다(`:794`). 시각화는 `QT_QPA_PLATFORM` 환경변수로만 제어된다.
- **Thickness 단위 스케일**: 입력 두께에 `*1000`이 자동 적용된다(`ODBCADManager.py:151`). 입력/출력 단위계는 코드상 주석이 없어 사용자가 직접 확인해야 한다 (확인 필요).
- **PatternFeatures 경로 구분자**: 예제 파일은 Windows 경로 구분자(`.\steps\...`)를 사용한다(`ECADFiles.txt:9-16`). Linux 환경에서의 경로 처리 동작은 코드만으로 확정 불가 (확인 필요).
- **어레이 피처 파일(`ArrayFeature.txt`) 자체 포맷**: `odbpImporter.ImportArrayFeature`가 파싱하며(단위/어레이/홀/브리지 폴리곤 분리, `PCBManager.py:115-127`), 그 내부 포맷은 본 문서 범위 밖이다 (확인 필요).
- **e2e 실행 검증 미수행**: 본 매뉴얼 작성 시점에 `mode=ArrayPCB`의 실제 실행 로그·산출 STEP은 직접 검증하지 않았다. 전용 run 스크립트는 확인되지 않았고, CLI 형식은 코드 주석·도움말 문자열을 근거로 한다(`:676-678`, `:769`) (확인 필요).

---

## 6. 개발 현황

**구현됨**

근거:
- `GenerateArrayPCB` 함수가 정의·디스패치 연결되어 있음 — `KooAutomatedModeller.py:265-275`, `:793-794`, 도움말 문자열 `:769`
- 입력 파서(`ImportModellingOptions`의 `*ArrayPCB` 블록), 형상 생성(`ArrayPCB.Generate` / `GenerateSolidwithWarpage`, boolean cut/fuse 포함), STEP 출력(`STEPControl_Writer`)까지 전 경로가 코드로 존재 — `ODBCADManager.py:111-171`, `:387-453`, `ArrayPCB.py:261-314`
- 실제 입력 예제 파일(`*ArrayPCB` 블록 포함) 존재 — `occProject/Generators/KooODBCADManager/ECADFiles.txt:1-18`

단, 실제 e2e 실행 결과(산출 STEP)는 본 작성 범위에서 미검증 (확인 필요).
