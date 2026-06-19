# KooAutomatedModeller: 커패시터 생성

## 1. 목적 / 개요

KooAutomatedModeller(KAM)의 커패시터 생성 기능은 텍스트 설정 파일(`.txt`)로 기술된 MLCC(Multi-Layer Ceramic Capacitor) 형상 정의를 읽어 STEP(CAD) 형상과 LS-DYNA 메시(`.k`)로 변환한다. KAM 모듈은 전반적으로 "ODB++ 패키지 정의를 STEP CAD로 변환하고 다중 솔버 포맷의 메시를 생성"하는 것을 목적으로 한다(`occProject/Generators/KooAutomatedModeller.py:1-9`).

진입점은 `GenerateCapacitor(fileName)` 함수다(`occProject/Generators/KooAutomatedModeller.py:192-213`). 이 함수는 `CapacitorManager`(`occProject/Generators/KooODBCADManager/Capacitor.py:2051`)를 생성하여 다음 순서로 동작한다.

1. `SetFolderPath` — 출력 폴더를 현재 작업 디렉터리로 설정 (`:202`)
2. `ImportCapacitor` — 설정 텍스트 파일 파싱 (`:204`)
3. `GenerateCapacitors` — OCC(OpenCASCADE) 형상 생성 (`:206`)
4. `ExportShapes` — STEP 파일 내보내기 (`:208`)
5. `ExportMeshes` — LS-DYNA `.k` 메시 내보내기 (`:210`)

하나의 설정 파일에 `*Capacitor` 블록을 여러 개 둘 수 있으며, 각 블록마다 독립된 커패시터가 생성된다(`Capacitor.py:2456-2459` 의 `for id in self.capacitors` 루프).

---

## 2. 입력 옵션 · 인자

### 2-1. CLI 인자 (sys.argv)

디스패치 로직 기준(`occProject/Generators/KooAutomatedModeller.py:774-790`).

| 위치 | 인자 | 의미 | 비고 |
|------|------|------|------|
| `sys.argv[1]` | mode | `"CAPACITOR"` 또는 `"CAP"` | 둘 다 `GenerateCapacitor` 호출 (`:789-790`) |
| `sys.argv[2]` | fileName | 설정 텍스트 파일명(`.txt`) | 현재 작업 디렉터리 기준 (`os.getcwd()`, `GenerateCapacitor`의 `:194-195`) |
| `sys.argv[3]` | workdir | 작업 디렉터리 (선택) | `"none"`이면 무시, 아니면 해당 폴더로 `chdir` (`:776-782`) |
| `sys.argv[4]` | displayMode | `"false"`/그 외 (선택) | 커패시터 경로에서는 사용되지 않음 (PBA/PKG 모드용) |

소스 내 실제 호출 예시(주석 처리된 예제 블록, `occProject/Generators/KooAutomatedModeller.py:718-723`):

```python
os.chdir(os.path.join(curDir,"occProject\\Generators\\dist\\Capacitor"))
sys.argv.clear()
sys.argv.append("KooAutomatedModeller.exe")
sys.argv.append("CAP")
#sys.argv.append("Cap1005.txt")
sys.argv.append("Cap0603Mesh.txt")
```

도움말 메시지에는 `python KooAutomatedModeller.py CAPACITOR [fileName]` 형태로 안내된다(`:767`).

### 2-2. 설정 텍스트 파일 구조

`CapacitorManager.ImportCapacitor`가 파싱한다(`occProject/Generators/KooODBCADManager/Capacitor.py:2072-2452`). 형식은 CSV(`,` 구분), `#`으로 시작하는 줄은 주석으로 무시(`:2078`, `:2203`).

파일 레벨 구조:

| 토큰 | 의미 | 근거 (file:line) |
|------|------|------------------|
| `*Capacitor[,name]` | 커패시터 블록 시작. 이름 선택 가능 | `:2111`, `:2191-2194` |
| `*End` | 전체 입력 종료 | `:2109-2110` |
| `**addscript[,LSDyna]` ... `**endscript` | LS-DYNA용 추가 스크립트 블록. `$` 줄은 무시 | `:2081-2103` |

`**addscript`의 옵션이 `LSDyna`가 아니면 "AddScript Option is not supported"를 출력한다(`:2099-2102`). 수집된 스크립트는 `ExportMeshes`에서 각 커패시터에 주입된다(`:2474` 의 `SetDynaScript`).

### 2-3. `*Capacitor` 블록 키 (위치 · 메시 · 재료)

각 블록은 `*Capacitor`와 다음 `*` 또는 빈 줄 전까지 키-값 줄을 읽는다(`:2195-2430`). 알 수 없는 키는 "Unknown Property"로 출력만 한다(`:2429-2430`).

| 키 | 형식 | 의미 | 근거 (file:line) |
|----|------|------|------------------|
| `Location` / `Translation` | `x,y,z` (float) | 배치 원점 | `:2205-2212` |
| `Rotation` | `deg` (int) | 회전 각도 | `:2213-2214` |
| `Mirror` | `True\|False` | 미러 여부 | `:2215-2219` |
| `IsTop` | `True\|False` | 상/하면 배치 | `:2220-2224` |
| `XSize` / `YSize` / `ZSize` | float | 칩 외형 치수. `YSize`만 주면 `ZSize`도 동일값 | `:2349-2356` |
| `MeshPath` | 경로 | gmsh 중간 파일 출력 경로 | `:2225-2226` |
| `MeshSize` | float | 기본 메시 크기(메시 생성 활성화) | `:2227-2229` |
| `MeshSizeSolder` | float | 솔더 메시 크기 | `:2230-2232` |
| `MeshSizeBody` | float | 세라믹 바디 메시 크기 | `:2233-2235` |
| `NumberofElementMLCC` | `nx,ny,nz` (int) | MLCC 바디 요소 분할 수 | `:2236-2240` |
| `MaterialID` | `<부위>,<id>` (int) | 부위별 재료 ID 지정 | `:2241-2258` |

`MaterialID`의 `<부위>` 값: `Pad`, `Terminal`, `Barrier`, `Finish`, `Solder`, `Dielectric`, `Electrode`, `CeramicBody` (`:2243-2258`). 미지정 시 기본값은 각각 1,2,3,4,5,6,7,8 (`:2172-2179`).

`MeshSize`/`MeshSizeSolder`/`MeshSizeBody`/`NumberofElementMLCC` 중 하나라도 있으면 `meshGenerationMode=True`로 설정된다(`:2228`, `:2231`, `:2234`, `:2237`).

### 2-4. MLCC 단면 형상 파라미터

세부 형상은 약어 키로 지정한다(`:2357-2428`). 약어 의미는 Evolver 스크립트 생성부 주석에 명시되어 있다(`Capacitor.py:845-879`). 모두 float(특별 표기 제외).

| 키 | 의미 | 근거 (file:line) |
|----|------|------------------|
| `lpw` / `lph` | 좌측 패드 폭 / 높이 (leftPadWidth/Height) | 파싱 `:2357-2360`, 의미 `:845-846` |
| `rpw` / `rph` | 우측 패드 폭 / 높이 | `:2361-2364`, `:849-850` |
| `piw` | 패드 간격 폭 (padIntervalWidth) | `:2365-2366`, `:848` |
| `pt` | 패드 두께 (padThickness) | `:2367-2368`, `:847` |
| `cbw` / `cbh` / `cbt` | 세라믹 바디 폭 / 높이 / 두께 | `:2369-2374`, `:851-853` |
| `ltw` / `ltt` | 좌측 터미널 폭 / 두께 | `:2375-2378`, `:854-855` |
| `rtw` / `rtt` | 우측 터미널 폭 / 두께 | `:2379-2382`, `:856-857` |
| `lbw` / `lbt` | 좌측 배리어 폭 / 두께 | `:2383-2386`, `:858-859` |
| `rbw` / `rbt` | 우측 배리어 폭 / 두께 | `:2387-2390`, `:860-861` |
| `lfw` / `lft` | 좌측 피니시 폭 / 두께 | `:2391-2394`, `:862-863` |
| `rfw` / `rft` | 우측 피니시 폭 / 두께 | `:2395-2398`, `:864-865` |
| `lst` / `lsv` | 좌측 솔더 두께 / 부피 | `:2399-2402`, `:866-867` |
| `rst` / `rsv` | 우측 솔더 두께 / 부피 | `:2403-2406`, `:868-869` |
| `tens` | 표면장력(Surface Evolver `TENS`) | `:2407-2408`, `:882` |
| `swr` | 솔더 폭 비율 (solderWidthRatio) | `:2409-2410`, `:877` |
| `str` | 솔더 두께 비율 (solderThicknessRatio) | `:2411-2412`, `:878` |
| `sbr` | 솔더 하단 폭 비율 (solderBottomWidthRatio) | `:2413-2414`, `:879` |
| `sg` | SG 값(Evolver `SG`) | `:2415-2416`, `:884` |
| `tilt` | 솔더 기울기 각도 | `:2417-2418`, `:885` |
| `Ndi` | 유전체 층 수 (int) | `:2419-2420`, 사용 `:542-544` |
| `tdi` | 유전체 두께 | `:2421-2422`, `:543-544` |
| `tel` | 전극 두께 | `:2423-2424`, `:525` |
| `epsilon` | 비유전율 | `:2425-2426`, `:541-544` |
| `ldi` | 유전체 마진(전극 미도달 폭) | `:2427-2428`, `:543` |

> `Ndi`/`tdi`/`tel`/`epsilon`/`ldi`는 내부 전극·유전체 적층 형상과 정전용량 계산에 쓰인다. 정전용량은 `C = epsilon0*epsilon*W*(Ndi*(L-ldi)/tdi + H/ldi)` 로 계산되어 출력된다(`Capacitor.py:541-548`).

### 2-5. 압전 재료 · 전압 키

| 키 | 형식 | 의미 | 근거 (file:line) |
|----|------|------|------------------|
| `dxx`,`dyy`,`dzz`,`dxy`,`dxz`,`dyz` | float | 유전(D) 행렬 성분(대칭) | `:2259-2273` |
| `px11`...`px23` | float | PX 압전 행렬 성분(대칭) | `:2274-2288` |
| `py11`...`py23` | float | PY 압전 행렬 성분(대칭) | `:2289-2303` |
| `pz11`...`pz23` | float | PZ 압전 행렬 성분(대칭) | `:2304-2318` |
| `LeftVoltageValue` / `RightVoltageValue` | float | 좌/우 인가 전압(상수) | `:2319-2322` |
| `LeftVoltageCurve` / `RightVoltageCurve` ... `End` | `time,voltage` 줄 반복 | 좌/우 전압-시간 곡선 | `:2323-2347` |

전압 곡선 블록은 `End`가 나올 때까지 `time,voltage` 쌍을 읽으며 `#`/`$` 줄은 무시한다(`:2330-2347`). 압전·전압 데이터는 각각 `SetPiezoelectricMaterial`, `SetVoltageValue`, `SetVoltageCurve`로 전달된다(`:2447`, `:2450-2451`).

---

## 3. 사용 예제

소스가 기본으로 임포트하는 실제 입력 파일(`Capacitor.py:2500`, 경로 `occProject/Generators/dist/Capacitor/Cap0603MeshSmallPiezoMaterialVoltage.txt`)에서 발췌. 0603 사이즈, 압전 재료, 좌측 전압 곡선을 포함한다.

```text
*Capacitor
Location,0.0,0.0,0.0
XSize,600
YSize,300
ZSize,300
Ndi,27
tdi,5
tel,6
epsilon,1660
ldi,170
swr,0.8
str,0.5
sbr,0.4
lsv,0.01
rsv,0.01
swr,0.6
str,0.7
sbr,0.6
MeshPath,.\PackageInfoCap
MeshSize,40
MeshSizeSolder,20
MeshSizeBody,20
NumberofElementMLCC,20,10,3
MaterialID,Pad,1
MaterialID,Terminal,1
MaterialID,Barrier,1
MaterialID,Finish,1
MaterialID,Solder,1
MaterialID,Dielectric,1
MaterialID,Electrode,1
MaterialID,CeramicBody,1
pz11,3.45e-11
pz22,3.45e-11
pz33,8.56e-11
py23,3.92e-10
px13,3.92e-10
dxx,2920
dyy,2920
dzz,168
LeftVoltageCurve
0.000,0.00
0.001,10.0
0.002,10.0
0.003,0.00
...(생략)...
0.021,0.00
LeftVoltageEnd
RightVoltageValue,0.0
*End
```

CLI 실행(소스 예제 블록 기반, `KooAutomatedModeller.py:718-723`):

```bash
python KooAutomatedModeller.py CAP Cap0603Mesh.txt
```

> 참고: 예제 파일에서 `swr`/`str`/`sbr`는 두 번 등장하며(0.8/0.6 등), 파서가 마지막 값으로 덮어쓰므로 최종적으로 `swr=0.6, str=0.7, sbr=0.6`이 적용된다(`SetProperties`는 단순 대입, `Capacitor.py:390-395`). 또한 곡선 종료 토큰은 코드상 `End` 부분 문자열로 판정되므로(`:2334`) `LeftVoltageEnd`도 종료로 인식된다.

---

## 4. 동작 원리

`GenerateCapacitor`(`KooAutomatedModeller.py:192-213`)의 5단계:

1. **입력 검증**: `os.path.join(os.getcwd(), fileName)` 경로가 없으면 "File not exist" 출력 후 반환(`:195-199`).
2. **파싱** `ImportCapacitor`(`Capacitor.py:2072-2452`): 줄 단위로 읽어 `*Capacitor` 블록마다 형상·메시·재료·전압 변수를 채우고, `AddCapacitorbySize`로 `Capacitor` 객체를 만들어 `self.capacitors` 딕셔너리에 누적한다(`:2433`, `:2061-2070`). 각 객체에 위치/메시/재료/압전/전압 설정을 적용(`:2434-2451`).
3. **형상 생성** `GenerateCapacitors`(`:2454-2459`): 각 커패시터에 `MakeMLCC(detailMode)`를 호출(`:2458`)하여 OCC 솔리드를 만든다.
4. **STEP 내보내기** `ExportShapes`(`:2463-2468`): 각 커패시터의 `WriteCapFile(...)` 호출(`:2467`). `WriteCapFile`은 좌/우 솔더(`MakeLeftSolder`/`MakeRightSolder`)와 MLCC 본체(`MakeMLCCShape`)를 컴파운드로 합치고(`:1432-1437`), `scaling_factor = 0.001`로 축소 변환 후(`:1440-1447`) STEP으로 기록한다(`:1450-1459`). `detailMode=True`면 `_cd.step`(유전체)·`_ce.step`(전극) 파일도 추가 출력한다(`:1461-1473`).
5. **메시 내보내기** `ExportMeshes`(`:2470-2482`): `SetDynaScript`로 `**addscript` 내용을 주입(`:2474`)하고 `GenerateMesh`로 gmsh 기반 메시를 생성(`:2475`), `ExportDynaMesh`로 `.k` 파일을 기록한다(`:2480`).

메시 생성 `GenerateMesh`(`Capacitor.py:1606-1622`)는 패드/피니시/배리어/터미널/솔더 메시를 순차 생성하고(`:1607-1611`), `detailMode=False`면 세라믹 바디를 통메시로(`:1612-1613`), `detailMode=True`면 전극-유전체 적층 메시를 생성한다(`:1621-1622`). 개별 부위는 `KooMeshManagerGMSH.mesh_shape`로 메시화된다(예: 패드 `:1630-1643`).

`GenerateCapacitor` 호출 경로에서는 `GenerateCapacitors`/`ExportShapes`/`ExportMeshes`를 모두 인자 없이 호출하므로 기본값 `detailMode=True`가 적용된다(`:2454`, `:2463`, `:2470`).

---

## 5. 출력물

| 출력 | 조건 | 파일명/근거 |
|------|------|-------------|
| STEP 형상 | 항상 | `<name>_detail.step` (detailMode=True 기본), `WriteCapFile` `:1452-1459` |
| 유전체 STEP | detailMode=True | `<name>_detail_cd.step` `:1461-1468` |
| 전극 STEP | detailMode=True | `<name>_detail_ce.step` `:1462,1469-1473` |
| LS-DYNA 메시 | 항상 | `<folderPath>\<name>_detail.k` `ExportMeshes` `:2476-2480` |
| gmsh 중간 파일 | 메시 생성 시 | `MeshPath`로 지정된 경로 |

출력 폴더는 `SetFolderPath`로 설정된 현재 작업 디렉터리다(`:2202`, `:2464`, `:2471`). 파일 경로는 Windows 구분자(`\\`)로 조립된다(`:2477-2479`).

---

## 6. 주의사항 · 한계

- **경로 구분자**: 출력 파일 경로가 `folderPath + "\\" + ...` 형태로 하드코딩되어 있다(`Capacitor.py:2477-2479`). Linux 환경에서의 동작은 **확인 필요**.
- **단위계**: `WriteCapFile`에서 STEP은 `scaling_factor=0.001`로 축소된다(`:1440`). 따라서 입력 치수(예: `XSize,600`)의 단위는 µm로 입력하고 STEP은 mm로 출력되는 것으로 보인다(정확한 단위 명시 주석은 코드에 없음 — **확인 필요**).
- **중복 키 덮어쓰기**: 동일 키를 여러 번 쓰면 마지막 값만 반영된다(`SetProperties` 단순 대입, `:390-395`). 예제 파일의 `swr/str/sbr` 중복이 이에 해당.
- **`**addscript` 옵션**: `LSDyna`만 지원하며 그 외는 무시된다(`:2099-2102`).
- **알 수 없는 키**: 오류 없이 "Unknown Property" 출력 후 무시(`:2429-2430`) — 오타 시 조용히 누락될 수 있음.
- **displayMode 인자**: 커패시터 경로에서는 사용되지 않는다. 단, `GUI`/`start_display`는 `__main__` 경로(`:2491-2517`)에서만 호출되며, `QT_QPA_PLATFORM=offscreen`이면 디스플레이를 건너뛴다(`:2514-2516`).
- **gmsh 의존**: 메시 생성은 `KooMeshManagerGMSH`(`:1630` 등)에 의존하므로 gmsh 바이너리(예: `dist/Capacitor/Library/gmsh-*`)가 필요하다.
- **압전/전압 데이터 활용 범위**: 압전 행렬·전압 곡선은 메시(`.k`) 카드 생성에 쓰이는 것으로 보이나, 정확히 어떤 LS-DYNA 카드로 출력되는지는 `ExportDynaMesh`(`:2007`) 내부 — 본 문서 범위에서 미확인(**확인 필요**).

---

## 7. 개발 현황

**구현됨.** 근거:
- 진입점 `GenerateCapacitor`가 KAM 메인 디스패치에 등록되어 `CAPACITOR`/`CAP` 모드로 호출된다(`KooAutomatedModeller.py:789-790`).
- 파서 `ImportCapacitor`(`Capacitor.py:2072-2452`), 형상 생성 `MakeMLCC`(`:755`), STEP 출력 `WriteCapFile`(`:1428`), 메시 출력 `GenerateMesh`/`ExportDynaMesh`(`:1606`, `:2007`)가 모두 구현되어 있다.
- 실제 예제 입력 파일이 배포 디렉터리에 포함되어 있다(`occProject/Generators/dist/Capacitor/Cap0603*.txt`, 6종).

단, 본 KAM 진입점(`GenerateCapacitor`)이 KooChainRun/scenario.json 등 상위 자동화 파이프라인과 연동되는지는 본 파일 범위에서 확인되지 않았다(**확인 필요**) — 소스 내 호출 예시는 주석 처리된 개발용 블록(`KooAutomatedModeller.py:718-723`)과 `Capacitor.py:__main__`(`:2491-2504`) 형태로만 존재한다.
