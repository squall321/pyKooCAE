# KooAutomatedModeller: PBA 생성

## 1. 목적 / 개요

`PBA` 모드는 ODB++ 전자 CAD 데이터(`.zip` / `.tgz`)와 텍스트 정의 파일(`*.txt`)을 입력받아, PCB(인쇄기판) 형상과 그 위에 실장된 컴포넌트(패키지 본체 + 솔더) 형상을 자동 생성하고 STEP(`.step` / `.stp`) CAD 파일로 내보내는 기능이다. PBA는 "Printed Board Assembly"(인쇄기판조립)를 의미한다.

진입점은 `GeneratePBA(fileName, displayMode)` 함수이며, 명령행 첫 인자 `mode == "PBA"` 일 때 호출된다.

- 근거: `occProject/Generators/KooAutomatedModeller.py:795-796` — `elif mode == "PBA": GeneratePBA(fileName, displayMode)`
- 함수 정의: `occProject/Generators/KooAutomatedModeller.py:229-252`
- 출력 동작 요약 (근거 `:230`): `print("Generate PBA as Step File")` — STEP 파일로 내보내는 모드임을 코드가 명시.

처리 체인 (근거 `:237-250`):
1. `odbManager.ImportModellingOptions(curPath, fileName)` — 텍스트 정의 파일 파싱
2. `shapeList = odbManager.ImportPBA()` — PCB + 컴포넌트 형상 생성
3. `odbManager.ExportShapes(exportFileName)` — 통합 STEP 출력

## 2. 입력 옵션 · 인자 (표)

### 2-1. 명령행 인자 (sys.argv)

명령행 파싱 근거: `KooAutomatedModeller.py:774-796`.

| 위치 | 변수 | 의미 | 값 예시 |
|------|------|------|---------|
| `argv[1]` | `mode` | 모드 토큰 (정확히 `"PBA"` 일치) | `PBA` |
| `argv[2]` | `fileName` | ODB++ 정의 텍스트 파일명 | `ECADfilesforPBA_P3_Export.txt` |
| `argv[3]` | (작업 디렉터리) | `"none"` 이면 무시, 아니면 `os.chdir`로 이동 | `none` 또는 하위 폴더명 |
| `argv[4]` | `displayMode` | `"false"`면 `False`, 그 외 `True` | `false` |

- 근거: `:774-788` — `mode = sys.argv[1]`, `fileName = sys.argv[2]`, `argv[3]` 작업디렉터리 처리, `argv[4]` displayMode 처리.
- 주의: `GeneratePBA` 내부에서 `displayMode`는 받기만 하고 분기에 사용되지 않는다. 화면 표시는 `update_shape`가 `QT_QPA_PLATFORM == "offscreen"`이면 건너뛰고, `start_display()`는 무조건 호출된다 (근거: `:241-245`, `:254-256`). → displayMode 인자의 실효성은 "확인 필요".

### 2-2. 텍스트 정의 파일 `*ODB` 블록 키워드

PBA 입력 파일은 `*ODB ... *End` 블록으로 구성되며 `ImportModellingOptions`가 파싱한다 (근거: `ODBCADManager.py:289-372`). 한 줄은 `키워드,값[,값...]` 형식(`split(',')`).

| 키워드 | 의미 | 단위 변환 / 처리 | 근거 (ODBCADManager.py) |
|--------|------|------------------|-------------------------|
| `ODBFile` | ODB++ 데이터 파일명(`.zip`/`.tgz`) | 리스트 누적 `self.ODBFile.append` | `:300-302` |
| `ZLocation` | PCB 적층 Z 기준 위치 | `float` 그대로 | `:313-315` |
| `Thickness` | 레이어별 두께(콤마 다중값) | 각 값 ×1000 (m→mm 추정) | `:324-330` |
| `ThicknessSolderPaste` | 솔더 페이스트 두께 | ×1000 | `:316-319` |
| `ThicknessSolderMask` | 솔더 마스크 두께 | ×1000 | `:320-323` |
| `BoundaryBox` | 상세 처리 영역 (xmin,ymin,xmax,ymax) | 각 값 ×1000, `detailOption=True` | `:304-312` |
| `MinimumSize` | 최소 형상 크기 임계값 | ×1000 | `:335-338` |
| `DetailPAD` | 상세 PAD 이름(예: `ALL`) | `detailPADName[값]=1` | `:331-334` |
| `UndefinedUnitAmps` | 미정의 단위 amp 값(기본 25.4) | `float` | `:339-342` |
| `ExportPackage` | 패키지 별도 STEP 출력 여부/폴더 | `true`→옵션 on, 3번째 값=폴더명(기본 `PackageExported`) | `:343-356` |
| `SkipLayer` | 건너뛸 레이어명 | 리스트 누적 | `:360-362` |
| `PKG` | 사용자 지정 패키지 매핑 | `udPKGName[값1]=값2` (3토큰 필요) | `:363-367` |

- 블록 종료: `*` 로 시작하는 줄(예: `*End`)에서 `break` (근거: `:298-299`).
- 주석: `#` 로 시작하는 줄은 무시 (근거: `:109-110`).

## 3. 사용 예제

### 3-1. CLI 명령 (소스 주석 발췌)

소스 내 실제 호출 예시 (근거: `KooAutomatedModeller.py:630-632`):

```
sys.argv.append("KooAutomatedModeller")
sys.argv.append("PBA")
sys.argv.append("ECADfilesforPBA_P3_Export.txt")
```

명령행으로 환산하면:

```bash
python3 KooAutomatedModeller.py PBA ECADfilesforPBA_P3_Export.txt
```

또 다른 주석 예시(근거 `:704-707`): `PBA ECADfilesforPBA_P3_PrescribedPKG.txt`.

### 3-2. 입력 텍스트 파일 예시 (`*ODB` 블록)

`Examples/ODB/ECADfilesforPBA_P3_Export.txt` (실제 파일 전체):

```
*ODB
ODBFile,P3_EUR_REV03.zip
ZLocation,0.0000
Thickness,2.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,6.5e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5,3.1e-5,2.5e-5
MinimumSize,0.005
ExportPackage,True,PackageExported
*End
```

상세(BoundaryBox + 솔더 + DetailPAD) 예시 — `Examples/ODB/ECADfilesforPBA_P3_Export_detail.txt` (실제 파일 전체):

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

## 4. 동작 원리 (코드 근거 file:line)

`GeneratePBA` 본체 흐름 (근거: `KooAutomatedModeller.py:229-252`):

1. `ODBCADManager()` 인스턴스 생성 후 현재 작업 경로/파일 경로 계산 (`:231-235`).
2. `ImportModellingOptions(curPath, fileName)` — `*ODB` 블록 파싱하여 `self.ODBFile`, 두께, BoundaryBox, ExportPackage 옵션 등 설정 (`:237`, 파서 본체 `ODBCADManager.py:96-372`).
3. `shapeList = ImportPBA()` (`:238`).
4. `update_shape`를 스레드로 띄우고 `start_display()` 호출 (`:241-245`).
5. STEP 파일명 = 입력 `.txt` → `_total.step` 치환 후 `ExportShapes` (`:248-250`):
   - `exportFileName = curFilePath.replace(".txt","_total.step")`

`ImportPBA()` 내부 (근거: `ODBCADManager.py:629-725`):

- `exportPKGOption == True`이면 출력 폴더(`exportPKGFolderName`) 생성 (`:633-636`).
- `ODBFile` 목록 순회 (`:640`):
  - `.tgz` 입력이면 압축 해제 후 `.zip` 재패키징 (`:643-654`).
  - `ImportPCBDetail()`로 PCB 형상 생성·누적 (`:659-661`, 정의 `:540`).
  - `ImportODBZipforPackage(ith, fileName)`로 ODB++ zip 내 `eda/data`·`steps/components` 항목을 추출하여 패키지 정보 임포트 (`:665`, 본체 `:727-`).
  - 각 `ComponentManager.Generate(...)`로 컴포넌트 형상 생성, 본체(`bodyList`)·솔더(`solderList`)·전체(`addedList`) 분리 누적 (`:671-679`).
  - 본체/솔더를 각각 `_PKG.stp` / `_S.stp` STEP로 추가 출력 (`:703-721`).
- 누적 `shapeList`를 `self.shapeList`에 저장 후 반환 (`:724-725`).

`ExportShapes(fileName)` — 모든 형상을 `TopoDS_Compound`로 묶어 `STEPControl_Writer`로 단일 STEP 출력 (근거: `ODBCADManager.py:854-896`). 리스트/`TopoDS_Compound`/단일 shape를 구분해 처리하며, `TopoDS_Compound`는 내부 `TopAbs_SOLID`만 추출 (`:875-883`).

### 출력 CAD 파일 정리

| 출력 | 조건 | 근거 |
|------|------|------|
| `<입력명>_total.step` | 항상 (GeneratePBA 마지막) | `KooAutomatedModeller.py:248-250` |
| `<입력명>_PKG.stp` | 패키지 본체 형상 존재 시 | `ODBCADManager.py:705-712` |
| `<입력명>_S.stp` | 솔더 형상 존재 시 | `ODBCADManager.py:714-721` |
| `<exportPKGFolderName>/...` | `ExportPackage,True` 일 때 | `ODBCADManager.py:633-636,666-667,675-676` |

## 5. 주의사항 · 한계

- **모드 토큰은 정확히 `PBA`** 여야 한다. `PKG`/`PCB`/`ArrayPCB`/`CAPACITOR|CAP`/`LSDYNADOE`와 별개 분기이며 대소문자/철자 불일치 시 어떤 분기에도 매칭되지 않는다 (근거: `KooAutomatedModeller.py:789-799`).
- **인자 부족 시 동작**: `len(sys.argv) < 3`이면 소스에 하드코딩된 디버그 `sys.argv` 블록으로 분기한다(대부분 주석 처리됨). 정상 CLI 사용에는 `PBA <txt>` 두 인자가 필수 (근거: `:391`, `:774-775`).
- **displayMode 인자 무효 가능성**: `GeneratePBA`는 `displayMode`를 받지만 화면 표시 분기에 쓰지 않으며 `start_display()`를 무조건 호출한다. 헤드리스 환경에서는 `QT_QPA_PLATFORM=offscreen` 설정이 `update_shape`의 형상 디스플레이를 우회한다 (근거: `:241-256`). → 실제 GUI 억제 여부는 "확인 필요".
- **단위 변환**: `Thickness`, `BoundaryBox`, `MinimumSize` 등은 파싱 시 ×1000 처리된다(입력은 m, 내부는 mm로 추정). 단위 의미는 코드 주석에 명시가 없어 "확인 필요" (근거: `ODBCADManager.py:306-336`).
- **`ODBFile` 입력 존재 필요**: `.zip`(또는 `.tgz`)로 지정한 ODB++ 데이터 파일(예: `P3_EUR_REV03.zip`)이 작업 디렉터리에 실제로 있어야 하며, 예제 txt만으로는 재현 불가. 해당 ODB++ 데이터 파일은 저장소에서 확인되지 않음 → "확인 필요".
- **IP/라이선스 게이트**: `__main__` 진입부에 등록 IP 화이트리스트 검사와 라이선스 만료일(`2027-12-31`) 검사가 있어, 비등록 IP에서는 `exit(0)`로 즉시 종료된다 (근거: `KooAutomatedModeller.py:340-386`).

## 6. 개발 현황

**구현됨 (부분 검증)**

- 근거 코드: `GeneratePBA` 정의·분기(`KooAutomatedModeller.py:229-252`, `:795-796`), `ImportPBA`/`ExportShapes` 구현(`ODBCADManager.py:629-725`, `:854-896`), `*ODB` 블록 파서(`ODBCADManager.py:289-372`).
- 입력 예제 존재: `Examples/ODB/ECADfilesforPBA_P3_Export.txt`, `..._Export_detail.txt` 등 실제 `*ODB` 정의 파일 확인.
- 미확인 요소(전체 e2e 실행 미검증): 입력 ODB++ 데이터(`*.zip`) 실파일과 `_total.step`/`_PKG.stp`/`_S.stp` 산출물 존재를 저장소에서 확인하지 못함. `displayMode` 인자 실효성 및 단위 변환 의미도 "확인 필요".
