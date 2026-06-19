# KooMeshModifier 모드: FEM_TO_IGA

## 1. 목적/개요

`FEM_TO_IGA` 모드는 기존 FEM(유한요소) 솔리드 파트를 **IGA(Isogeometric Analysis, 등기하해석) 솔리드 파트로 일괄 변환**하는 자동화 모드입니다. 사용자가 변환 대상 FEM Part ID 목록과 각 IGA 파라미터를 지정하면, KooMeshModifier가 파트별로:

- Material을 복제(`_IGA` 접미사)하고 새 ID를 할당
- `*SECTION_IGA_SOLID` 섹션을 생성
- 원본 파트의 노드 좌표로부터 bounding box를 계산
- LS-DYNA IGA 키워드 블록(`*IGA_SOLID`, `*IGA_3D_NURBS_XYZ`, `*IGA_REFINE_SOLID`, `*IGA_DEV_VOLUME_XYZ` 등)을 **별도 .k 파일**로 생성

하고, 메인 출력 파일에는 생성된 IGA 파일들을 `*INCLUDE` 문으로 연결합니다.

IGA 변환은 원본 FEM 솔리드의 테트메시를 그대로 임베딩하는 방식(`*IGA_DEV_VOLUME_XYZ` 의 `TETMSH = -1`, FE embedding)을 사용합니다 (`KooIGAPart.py:59`, `KooIGAPart.py:305`).

근거: `KooMeshModifier.py:318` (모드 등록), `KooMeshModifier.py:2861` (dispatch), `KooDynaAdvancedModification.py:6447` (`FEMtoIGA`), `KooPart.py:3079` (`CreateIGAPart`), `KooIGAPart.py:69` (`KooIGAPart` 클래스).

---

## 2. 입력 옵션·인자 (표)

입력 .k(옵션 파일) 안의 `**FEMtoIGA,<modeID>` 블록 내부에 `*IGA,...` 줄을 파트별로 한 줄씩 나열합니다. 각 `*IGA` 줄은 콤마로 구분되며, 앞 3개는 필수, 나머지는 선택(생략 시 디폴트)입니다.

`*IGA,<PID>,<IGAID>,<File>[,rr[,rs[,rt[,ratio[,ir]]]]]`

| 위치 | 인자 | 설명 | 필수 | 디폴트 | 코드 근거 |
|------|------|------|------|--------|-----------|
| 1 | `PID` (`source_pid`) | 원본 FEM Part ID | 필수 | - | `KooMeshModifier.py:2149` |
| 2 | `IGAID` (`iga_id`) | 생성할 IGA Part ID (PID=VID=SID=PATCHID=RID 공통 사용) | 필수 | - | `KooMeshModifier.py:2150` |
| 3 | `File` (`output_file`) | IGA 키워드 출력 파일명 (예: `iga_part5.k`) | 필수 | - | `KooMeshModifier.py:2151` |
| 4 | `rr` | element edge length (r 방향) | 선택 | `0.6` | `KooMeshModifier.py:2154` |
| 5 | `rs` | element edge length (s 방향) | 선택 | `0.6` | `KooMeshModifier.py:2155` |
| 6 | `rt` | element edge length (t 방향) | 선택 | `0.6` | `KooMeshModifier.py:2156` |
| 7 | `ratio` (`bbox_offset_ratio`) | bounding box 확장 비율 (1.0=확장 없음, 1.1=10% 확장) | 선택 | `1.1` | `KooMeshModifier.py:2157` |
| 8 | `ir` (`integration_rule`) | 적분 규칙 (0=reduced Gauss, 1=Full Gauss) | 선택 | `0` | `KooMeshModifier.py:2158`, `KooIGAPart.py:21` |

선택 인자는 위치 기반이므로 뒤쪽 인자를 쓰려면 앞쪽 인자를 모두 채워야 합니다.

### 코드 디폴트로만 노출되는 추가 옵션 (입력 .k 미노출 — 확인 필요)

`*IGA` 줄로는 위 8개만 지정 가능하며, 아래 파라미터는 `DEFAULT_OPTIONS`(`KooIGAPart.py:11~66`)의 고정 디폴트로만 적용됩니다. 현재 입력 .k 파서(`KooMeshModifier.py:2145~2169`)는 이 값들을 사용자로부터 받지 않습니다.

- `stabilization`: `styp=4`, `tollg=1.0e-3` (`KooIGAPart.py:24`)
- `nurbs_params`: `nr/ns/nt=2`, `pr/ps/pt=1`, `unir/unis/unit=1` (`KooIGAPart.py:35`)
- `iga_solid_params`: `nisr/niss/nist=1` (`KooIGAPart.py:42`)
- `refine_params`: `rtyp=2`, `hrtyp=2`, `itr/its/itt=2` (`KooIGAPart.py:49`)
- `volume_params`: `tetmsh=-1` (FE embedding 고정) (`KooIGAPart.py:59`)
- `part_name_template`: `'Nurbs-Solid_{source_name}'` (`KooIGAPart.py:65`)

---

## 3. 사용 예제

### 입력 옵션 .k 블록 (docs/fem_to_iga_mode.md 예제 발췌)

```
*Inputfile
model.k

*Mode
FEM_TO_IGA,22

**FEMtoIGA,22
# 최소 옵션 (나머지 디폴트)
*IGA,5,100,iga_part5.k

# 요소 크기 지정
*IGA,7,101,iga_part7.k,0.4,0.4,0.3

# 모든 옵션 지정
*IGA,10,102,iga_part10.k,0.5,0.5,0.4,1.2,1

**EndFEMtoIGA

*End
```

구조 설명 (코드 근거):
- `*Inputfile` 다음 줄에 변환 대상 LS-DYNA 모델 파일명을 적습니다 (`KooMeshModifier.py:163~166`).
- `*Mode` 블록에서 `FEM_TO_IGA,22` 형태로 모드와 modeID를 등록합니다 (`KooMeshModifier.py:234`, `:318~320`).
- `**FEMtoIGA,22` 블록의 modeID는 `*Mode`의 modeID와 일치해야 합니다 (`KooMeshModifier.py:2125~2127`).
- 블록은 `**EndFEMtoIGA`(코드상 `**end` 포함 여부로 종료 판정) 또는 EOF에서 종료됩니다 (`KooMeshModifier.py:2139`).
- `#` 또는 `$`로 시작하는 줄은 주석으로 무시됩니다 (`KooMeshModifier.py:2141~2143`).
- `*IGA` 이외의 (주석이 아닌) 줄을 만나면 `Invalid option in FEMtoIGA`를 출력하고 종료합니다 (`KooMeshModifier.py:2170~2172`).

> 참고: `*Mode` 줄의 modeID(예: `22`)는 사용자 지정 식별자이며 코드상 고정값이 아닙니다. 위 예제는 `docs/fem_to_iga_mode.md`의 표기를 그대로 옮긴 것입니다.

### 출력 결과

- 메인 출력 파일: `<input>_iga.k` (`additionalword += "_iga"`, `KooMeshModifier.py:2863`; 파일명 조립은 `KooMeshModifier.py:2906~2910`)
- IGA 파트 파일: 각 `*IGA` 줄의 `File` 이름으로 생성 (`KooIGAPart.WriteToFile`, `KooIGAPart.py:362~374`)
- 메인 파일 내부에 IGA include 문 자동 추가 (`KooMeshModifier.py:2916~2918`, `KooPart.WriteIGAIncludes` `KooPart.py:3218~3240`)
- IGA 파트 파일은 출력 폴더로 복사 (`KooMeshModifier.py:2944~2951`)

---

## 4. 동작 원리 (코드 근거)

1. **모드 등록** — 옵션 파일의 `*Mode` 블록에서 `fem_to_iga` 문자열을 만나면 `modeList`에 `"FEM_TO_IGA"`, `modeIDList`에 modeID를 추가
   - `KooMeshModifier.py:318-320`

2. **옵션 파싱** — `**femtoiga,<id>` 블록을 읽어 `*IGA` 줄마다 `iga_config` 딕셔너리를 만들고 `curOptions["IGAParts"]` 리스트에 누적, `self.modeIDOption[curModeID]`에 저장
   - `KooMeshModifier.py:2125-2174`

3. **dispatch** — 실행 단계에서 `mode == "FEM_TO_IGA"`이면 `GenerateFEMtoIGA(modeid)` 호출, `additionalword`에 `_iga` 누적
   - `KooMeshModifier.py:2861-2863`
   - `GenerateFEMtoIGA`는 `self.modeIDOption[modeid]`를 꺼내 `advancedModification.FEMtoIGA(curOption)` 호출: `KooMeshModifier.py:2611-2613`

4. **파트별 변환** — `FEMtoIGA`가 `IGAParts` 리스트를 순회. 먼저 `_check_pids_not_in_preserved_includes`로 보존 include 안의 PID를 변환 대상으로 삼지 않는지 검사한 뒤, 각 config에 대해 `partManager.CreateIGAPart(...)` → `iga_part.WriteToFile()` 수행. 실패 시 메시지 출력 후 `raise`
   - `KooDynaAdvancedModification.py:6447-6503`
   - 보존 include 검사: `KooTetraRemesher.py:18`

5. **IGA 파트 생성 (CreateIGAPart)** — 다음 순서로 처리
   - 원본 파트 존재 확인 (없으면 `ValueError`): `KooPart.py:3109-3110`
   - `iga_id` 미지정 시 `maxIGAID` 증가로 자동 할당, PID 중복 검사: `KooPart.py:3114-3123`
   - Material 복제(`CloneMaterial`, `_IGA` 접미사) → 새 material id: `KooPart.py:3131-3135`
   - `CreateIGASection`으로 `*SECTION_IGA_SOLID` 섹션 생성: `KooPart.py:3140-3144`, `KooSection.py:392`
   - `KooIGAPart` 인스턴스 생성 후 `self.igaParts[iga_pid]`에 등록, `igaIncludes`에 출력 파일 경로 추가: `KooPart.py:3146-3163`

6. **bounding box 계산** — 원본 파트의 모든 요소 노드 좌표에서 min/max를 구하고 중심 기준 `bbox_offset_ratio`만큼 확장
   - `KooIGAPart.CalculateBoundingBox`, `KooIGAPart.py:149-199`

7. **IGA 키워드 생성** — `GenerateIGAKeywords`가 다음 9개 블록을 순서대로 조립
   - `*PARAMETER_LOCAL` (Iid/Imid/Ifepid, bbox 코너, edge length, ir, stabilization): `KooIGAPart.py:239-265`
   - `*PARAMETER_EXPRESSION_LOCAL` (bbox±edge length): `KooIGAPart.py:267-276`
   - `*IGA_DEV_STABILIZATION`: `KooIGAPart.py:278-283`
   - `*PART`: `KooIGAPart.py:285-292`
   - `*SECTION_IGA_SOLID`: `KooIGAPart.py:294-299`
   - `*IGA_DEV_VOLUME_XYZ` (TETMSH=-1, FE solid PID 임베딩): `KooIGAPart.py:301-310`
   - `*IGA_SOLID`: `KooIGAPart.py:312-320`
   - `*IGA_3D_NURBS_XYZ` (8개 박스 코너 제어점): `KooIGAPart.py:322-348`
   - `*IGA_REFINE_SOLID`: `KooIGAPart.py:350-360`
   - 전체 순서: `KooIGAPart.py:201-237`

8. **파일 출력** — `WriteToFile`이 `*KEYWORD ... *END`로 IGA 키워드 파일 작성
   - `KooIGAPart.py:362-374`

9. **메인 파일에 include 연결 및 복사** — 메인 출력(`WriteModifiedFile`) 시 `igaParts`가 있으면 `WriteIGAIncludes`로 `*INCLUDE` 추가, 이후 IGA 파일을 출력 폴더로 복사
   - `KooMeshModifier.py:2916-2918`, `KooMeshModifier.py:2944-2951`, `KooPart.py:3218-3240`

---

## 5. 주의사항·한계

- **솔리드 임베딩 전제**: `*IGA_DEV_VOLUME_XYZ`의 `TETMSH = -1` 고정으로, 원본 FEM 솔리드 메시를 임베딩하는 방식입니다 (`KooIGAPart.py:59`, `:305`). 셸/빔 등 비솔리드 파트에 대한 동작은 코드상 명시되어 있지 않습니다 — **확인 필요**.
- **bounding box = 박스 코너만 사용**: NURBS 제어점이 bbox의 8개 코너로 구성되며(`KooIGAPart.py:338~346`), 곡면/복잡 형상의 정밀 재현이 아니라 박스형 NURBS 패치에 FEM 메시를 임베딩하는 방식입니다.
- **선택 인자는 위치 기반**: `ratio`(7번)만 바꾸려 해도 `rr/rs/rt`(4~6번)를 먼저 채워야 합니다 (`KooMeshModifier.py:2154~2157`).
- **PID 중복 / 원본 부재 시 오류**: `IGAID`가 기존 part 또는 igaParts와 겹치거나(`KooPart.py:3122-3123`), 원본 `PID`가 없으면(`KooPart.py:3109-3110`) `ValueError`로 중단됩니다.
- **Material 필수**: 원본 파트의 material ID가 MaterialManager에 없으면 `ValueError` (`KooPart.py:3126-3127`).
- **보존 include 충돌 검사**: `*PreserveIncludes`로 보존 지정된 include 안의 PID를 변환 대상으로 삼으면 `_check_pids_not_in_preserved_includes`에서 제지됩니다 (`KooDynaAdvancedModification.py:6472-6474`, `KooTetraRemesher.py:18`).
- **고정 디폴트 파라미터**: NURBS 차수/세분화/stabilization 등은 입력 .k에서 조정할 수 없고 코드 디폴트에 의존합니다(섹션 2 참조). 다른 형상/해상도가 필요하면 코드 수정이 필요할 수 있습니다 — **확인 필요**.
- **`**End` 종료 판정**: 블록 종료는 `**end` 문자열 포함 여부로 판정하므로(`KooMeshModifier.py:2139`), `**EndFEMtoIGA` 외에 `**end`를 포함하는 표기면 종료됩니다.

---

## 6. 개발 현황

**구현됨 (부분구현 요소 포함)**

근거:
- 모드 등록·파싱·dispatch·변환·키워드 생성·파일 출력·include 연결까지 전 경로가 코드에 구현되어 있음: `KooMeshModifier.py:318` / `:2125` / `:2861` / `:2611`, `KooDynaAdvancedModification.py:6447`, `KooPart.py:3079` / `:3218`, `KooIGAPart.py:201` / `:362`.
- 단, 입력 .k 인터페이스로 노출되는 옵션은 8개(PID/IGAID/File/rr/rs/rt/ratio/ir)로 제한되며, NURBS 차수·세분화·stabilization 등은 `KooIGAPart.DEFAULT_OPTIONS` 고정 디폴트에만 의존(`KooIGAPart.py:11~66`) → 이 측면에서 **부분구현**.
- `Examples/` 디렉토리에서 실제 `**FEMtoIGA` 입력 .k 예제 파일은 발견되지 않음(grep 무결과). 예제는 설계 문서 `docs/fem_to_iga_mode.md`의 코드 블록에만 존재 → 실모델 검증 자료는 **확인 필요**.
