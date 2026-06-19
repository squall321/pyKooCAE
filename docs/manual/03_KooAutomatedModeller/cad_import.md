# CAD/ECAD Import

> 근거 파일
> - 진입점/디스패치: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/occProject/Generators/KooAutomatedModeller.py`
>   - `ImportCADManager()` L110–L115 / CLI 진입점 L774–L800
>   - `GeneratePBA()` L229–L240 / `GeneratePackage()` L118–L190
> - 입력 파서/로더: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/occProject/Generators/KooODBCADManager/ODBCADManager.py`
>   - `ImportModellingOptions()` L96–L381 / `load_package()` L822–L827 / `load_component()` L829–L840 / `ImportPBA()` L629–
> - 입력 예제(ECAD txt): `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/ODB/ECADfilesforPBA_P3_Export*.txt`

---

## 1. 목적 / 개요

KooAutomatedModeller(KAM)의 CAD/ECAD Import 기능은 **ODB++ PCB 패키지 정의(ECAD)를 읽어
STEP CAD 형상 또는 FEA용 메시로 변환**하기 위한 입력 단계다. 모듈 docstring은
"Converts ODB++ PCB package definitions into STEP CAD geometry, then generates FEA-ready
meshes in multiple solver formats (LS-DYNA .k, Nastran .bdf, ANSYS .cdb, ABAQUS .inp, OBJ)"
라고 정의한다(KooAutomatedModeller.py:2–6).

Import 경로는 두 가지로 나뉜다.

1. **ECAD 옵션 파일(.txt) 기반 (실사용 경로).**
   CLI 진입점(L774–L800)은 `mode` 인자에 따라 `GeneratePBA()`/`GeneratePackage()` 등을
   호출하고, 이들은 `ODBCADManager.ImportModellingOptions()`(L96)로 옵션 txt 를 파싱한 뒤
   `*ODB` 블록에 지정된 ODB++ zip 파일을 읽는다. `Examples/automatedmodeller/run.sh`,
   `Examples/ODB/ECADfilesfor*.txt` 가 이 경로의 입력 형식이다.

2. **`ImportCADManager()` 헬퍼 (패키지+컴포넌트 직접 로드).**
   `path`, 패키지 파일명, 컴포넌트 파일명 리스트를 받아 `ODBCADManager`에 패키지/컴포넌트를
   적재해 반환하는 함수다(L110–L115). 단, 이 함수는 모듈 내부 어디에서도 호출되지 않는다
   (grep 결과 정의부 1건만 존재) → 자세한 위치는 §6 참조.

---

## 2. 입력 옵션 · 인자

### 2.1 `ImportCADManager()` 함수 인자 (KooAutomatedModeller.py:110)

| 인자 | 타입 | 의미 | 처리 근거 |
|---|---|---|---|
| `path` | str | 패키지·컴포넌트 파일이 위치한 디렉터리 | `load_package`/`load_component`에 그대로 전달 (L112–L114) |
| `pkgFileName` | str | 패키지 정의 파일명 | `cadMan.load_package(path, pkgFileName)` (L112) → `ImportPackagesfromODB()` |
| `compFileNameList` | list[str] | 컴포넌트 정의 파일명 목록 | 루프로 `cadMan.load_component(path, aCompFileName)` 호출 (L113–L114) |
| 반환값 | `ODBCADManager` | 패키지/컴포넌트가 적재된 매니저 객체 | `return cadMan` (L115) |

> `load_package()`는 파일명이 빈 문자열이면 `None`을 반환하고(ODBCADManager.py:823–824),
> `load_component()`도 빈 문자열이면 무시한다(L830–L831). `load_component()`는 컴포넌트가
> 0개이면 해당 파일을 건너뛴다(L838–L839).

### 2.2 CLI 인자 (KooAutomatedModeller.py:774–800)

| 위치 | 인자 | 의미 |
|---|---|---|
| `sys.argv[1]` | `mode` | 동작 모드. `CAPACITOR`/`CAP`, `PCB`, `ArrayPCB`, `PBA`, `PKG`, `LSDYNADOE` (L789–L800) |
| `sys.argv[2]` | `fileName` | 옵션 txt 파일명 (예: `ECADfilesforPBA_P3_Export.txt`) |
| `sys.argv[3]` | workdir | (선택) `none`이면 무시, 아니면 해당 하위 디렉터리로 `os.chdir` (L776–L782) |
| `sys.argv[4]` | displayMode | (선택) `false`면 비표시, 그 외 표시 (L784–L788) |

ECAD(ODB++)를 입력으로 쓰는 모드는 `PBA`(`GeneratePBA`, L796)다. `PBA` 모드는 옵션 txt 의
`*ODB` 블록을 읽어 ODB++ zip을 처리한다.

### 2.3 ECAD 옵션 txt 의 `*ODB` 블록 키 (ImportModellingOptions, ODBCADManager.py:289–372)

`*ODB` … `*End` 사이에 `키,값1,값2,...` (콤마 구분) 형식으로 작성한다. 인식되는 키:

| 키 | 인자 | 의미 | 근거(line) |
|---|---|---|---|
| `ODBFile` | 파일명 | 입력 ODB++ 아카이브(.zip/.tgz) | L300–L303 |
| `ZLocation` | float | 해당 ODB의 Z 위치 | L313–L315 |
| `Thickness` | float… | 레이어별 두께 목록(입력값 ×1000 으로 mm 환산) | L324–L330 |
| `ThicknessSolderPaste` | float | 솔더 페이스트 두께 (×1000) | L316–L319 |
| `ThicknessSolderMask` | float | 솔더 마스크 두께 (×1000) | L320–L323 |
| `BoundaryBox` | xmin,ymin,xmax,ymax | 상세화 영역 박스 지정 시 `detailOption=True` (값 ×1000) | L304–L312 |
| `MinimumSize` | float | 최소 형상/메시 크기 (×1000) | L335–L338 |
| `DetailPAD` | 이름 | 상세 모델링할 PAD 이름(`ALL` 가능) | L331–L334 |
| `UndefinedUnitAmps` | float | 단위 미정의 시 amp 값 | L339–L342 |
| `ExportPackage` | true/false[,폴더명] | 패키지 STEP 내보내기 여부 및 출력 폴더(기본 `PackageExported`) | L343–L356 |
| `SkipLayer` | 레이어명 | 처리에서 제외할 레이어 | L360–L362 |
| `PKG` | 인스턴스명,정의txt | 지정 패키지를 사용자 정의 txt로 대체 | L363–L367 |

> 그 외 블록: `*ArrayPCB`(L111), `*PCB`(L172), `*Packages`(L233), `*ComponentTop`(L255),
> `*ComponentBottom`(L272) 도 동일 파서가 인식한다. `#`로 시작하는 줄은 주석으로 무시(L109)되고,
> `*`로 시작하는 줄이 블록 종료/전환 경계다.

---

## 3. 사용 예제

### 3.1 PBA 모드 — ODB++ 입력 (실제 예제 발췌)

CLI 호출 (`Examples/automatedmodeller/run.sh` 의 모드만 PBA로 치환한 형태, 진입점 L774–L796):

```bash
python3 occProject/Generators/KooAutomatedModeller.py PBA ECADfilesforPBA_P3_Export.txt
```

옵션 txt 입력 (`Examples/ODB/ECADfilesforPBA_P3_Export.txt`, 전체):

```
*ODB
ODBFile,P3_EUR_REV03.zip
ZLocation,0.0000
Thickness,2.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,6.5e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,2.5e-5
MinimumSize,0.005
ExportPackage,True,PackageExported
*End
```

### 3.2 상세 영역(BoundaryBox) 지정 (`Examples/ODB/ECADfilesforPBA_P3_Export_detail.txt`, 전체)

```
*ODB
ODBFile,P3_EUR_REV03.zip
ZLocation,0.0000
Thickness,2.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,6.5e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,2.5e-5
ThicknessSolderPaste,1.5e-5
ThicknessSolderMask,1.5e-5
ExportPackage,True,PackageExported
BoundaryBox,0.025,0.005,0.03,0.01
MinimumSize,0.00
DetailPAD,ALL
*End
```

### 3.3 사용자 정의 패키지 대체 (`PKG` 키, `dist/PBA/ECADfilesforPBA_P3_PrescribedPKG.txt`, 전체)

```
*ODB
ODBFile,P3_EUR_REV03.zip
ZLocation,0.0000
Thickness,2.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,6.5e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,2.5e-5
MinimumSize,0.005
PKG,bga401f_W700L788_SB02_L,PackageInfoSimplePositionChange.txt
*End
```

### 3.4 `ImportCADManager()` 직접 호출 (함수 시그니처 기준, KooAutomatedModeller.py:110)

```python
cadMan = ImportCADManager(
    path,                                   # 파일 디렉터리
    "package.txt",                          # 패키지 정의 파일
    ["componenttop.txt", "componentbottom.txt"],  # 컴포넌트 파일 목록
)
```

> 위 호출 형태는 함수 시그니처(L110)와 `load_package`/`load_component`(L822–L840)에서 도출한 것이다.
> 실제 호출 코드는 리포지토리에 존재하지 않으므로(§6) 예시로만 제시한다.

---

## 4. 동작 원리 (코드 근거)

1. **CLI 분기**: `mode = sys.argv[1]`, `fileName = sys.argv[2]` 로 받아
   `mode == "PBA"` 면 `GeneratePBA(fileName, displayMode)` 호출
   (KooAutomatedModeller.py:774–796).
2. **옵션 파싱**: `GeneratePBA()`는 `ODBCADManager`를 만들고
   `odbManager.ImportModellingOptions(curPath, fileName)` 로 옵션 txt 를 읽은 뒤
   `odbManager.ImportPBA()` 를 호출한다(L229–L238).
3. **txt 파서**: `ImportModellingOptions()`는 줄 단위로 읽으며 `*ODB`/`*PCB`/`*Packages`/
   `*ComponentTop`/`*ComponentBottom`/`*ArrayPCB` 블록을 식별하고, 각 블록 내부에서
   `키,값` 줄을 콤마 분리(`svector = sline.split(',')`)해 매니저 멤버에 저장한다
   (ODBCADManager.py:100–381). `#` 시작 줄은 무시(L109), `*` 시작 줄이 블록 경계(L121 등).
4. **ODB++ 적재**: `ImportPBA()`는 `self.ODBFile` 목록을 순회하며 파일을 처리한다.
   `.tgz` 입력이면 `ExtractTGZ` → 내부 z파일 추출 → 재압축(.zip)으로 정규화하고
   (ODBCADManager.py:643–654), `ImportODBZipforPackage()` 로 ODB++ zip 을 읽는다(L665).
   `ExportPackage` 가 켜져 있으면 `exportPKGFolderName` 폴더를 만들고
   `ExportPackage(...)` 로 STEP을 내보낸다(L633–L636, L666–L667).
5. **`ImportCADManager()` 경로**: `ODBCADManager()` 생성 후
   `load_package()`(→ `packageManager.ImportPackagesfromODB(stream)`, L826–L827)와
   `load_component()`(→ `ComponentManager.ImportComponentfromODB(stream)`, L833–L837)로
   파일 스트림을 직접 파싱한다.

단위 환산: `Thickness`, `BoundaryBox`, `MinimumSize`, 솔더 두께 등은 파서에서 입력값에
`×1000` 또는 `×1000.0` 을 곱한다(예: L151, L306–L309, L328, L336) → 입력은 m 단위(예 `2.5e-5`),
내부 처리는 mm 단위로 보인다(확인 필요: 단위 정의 주석 없음).

---

## 5. 주의사항 · 한계

- **콤마 구분 + 키워드 prefix 매칭**: 파서는 `sline.find("키") == 0` 로 줄 시작을 검사하므로
  (예: ODBCADManager.py:300) 키 이름 앞에 공백/오타가 있으면 인식되지 않는다.
  `Thickness` 검사가 `ThicknessSolderPaste`/`ThicknessSolderMask` 보다 뒤에 위치해(L316/L320 → L324)
  prefix 충돌을 피하도록 순서가 잡혀 있다.
- **`ODBFile` 다중 지정**: `self.ODBFile.append(...)`(L301) 로 리스트에 누적되며
  `ImportPBA()`가 순회 처리한다(L640). 여러 ODB 입력을 한 옵션 파일에 나열 가능.
- **`ExportPackage` 인자 부족 시**: 값 개수가 2 미만이면 경고 후 건너뛴다(L344–L346).
  폴더명을 생략하면 기본값 `PackageExported`(L353–L354).
- **`PKG` 인자 부족 시**: 인자 3개 미만이면 경고 후 무시(L364–L366).
- **단위 가정**: 두께/크기 입력은 m 단위로 작성하고 내부에서 ×1000 환산된다(§4). 단위 명시 문서/주석은
  코드에 없음 → 정확한 단위계는 확인 필요.
- **ODB++ 파서 본체**: `ImportODBZipforPackage`/`ImportPackagesfromODB`/`ImportComponentfromODB` 의
  내부 구현은 본 문서 범위 밖(ODB++ 포맷 해석부)이며 별도 확인 필요.

---

## 6. 개발 현황

**부분구현.**

- **ECAD 옵션 txt 기반 PBA Import 경로: 구현됨.**
  CLI 디스패치(L774–L800) → `GeneratePBA`(L229–L240) → `ImportModellingOptions`(L96–L381) →
  `ImportPBA`(L629–) 가 모두 존재하고, `Examples/ODB/ECADfilesfor*.txt` 와
  실행된 출력물(`*_total.step`, `*_mesh.k` 등 동일 폴더)이 함께 존재한다.
- **`ImportCADManager()` 함수: 정의만 존재(미연결).**
  본체는 구현되어 있으나(L110–L115), `grep -rn "ImportCADManager"`
  (dist 제외) 결과 정의부 1건 외 호출처가 없다. 즉 패키지+컴포넌트를 직접 받는
  이 진입점은 CLI/다른 모듈에서 연결되어 있지 않다 → 라이브러리 API로만 호출 가능.
- **다중 솔버 export**: docstring은 Nastran/ANSYS/ABAQUS/OBJ 출력을 명시하나
  `GeneratePackage()`에서 LS-DYNA(.k) 외 export 호출은 주석 처리되어 있다
  (KooAutomatedModeller.py:167–168, 175–183) → 해당 포맷은 비활성(부분구현).
