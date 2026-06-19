# KooMeshModifier 모드: PART_EXCHANGE

> 근거 코드:
> - `occProject/Generators/KooMeshModifier.py`
> - `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py`
> - `occProject/Generators/KooCAEManager/KooMaterial.py`
> - `occProject/Generators/KooCAEManager/KooSection.py`

## 1. 목적/개요

`PART_EXCHANGE` 모드는 입력 .k 안의 특정 **파트(PID)** 에 대해 **섹션(*SECTION)·재료(*MAT)·EOS·HourGlass 등 카드를 교체**하고, 필요 시 해당 파트의 **요소 종류 자체를 변환**(Solid → Shell / TShell / SolidComposite / Slack 포함 Solid 등)하거나 **비정렬(unstructured) 메시를 정렬(structured) 격자 메시로 재구성**하는 복합 모드이다. 즉 "파트 단위로 물성·요소정식(element formulation)·메시 구조를 통째로 바꿔 끼우는" 용도이다.

핸들러 `GeneratePartExchange()` 는 다음 작업을 옵션 유무에 따라 선택적으로 수행한다 (KooMeshModifier.py:2626-2761).
- 지정 PID 의 `*SECTION` / `*MAT` 교체 (line 2684-2695)
- 입력에 나열된 `*MAT` / `*EOS` / `*HGID` 카드들을 신규 등록하고 ID 매핑 생성 (line 2698-2709)
- `*PART_COMPOSITE` 로의 변환 + 토큰(PID/THK/MID) 치환 (line 2712-2723)
- `*layup` 문자열의 토큰(THK/MID/EOS/HGID/NUME 등) 치환 후 레이어 리스트화 (line 2728-2750)
- `converthexato` 옵션이 있으면 요소정식 변환 호출 (line 2752-2754)
- `unstructuredtostructured` 옵션이 있으면 정렬 격자 변환 호출 (line 2755-2761)

> 참고: **전용 예제 파일 없음**. 본 문서는 코드 근거로만 작성됨. (Examples 디렉터리에 `partexchange` / `part_exchange` / `converthexato` 관련 입력·시나리오 파일 부재 확인.) 따라서 아래 사용 예제는 파서가 받는 형식을 코드에서 역산한 개념 예시이며, 실사용 검증 근거는 미확인이다.

## 2. 입력 옵션·인자 (표)

입력은 KooMeshModifier 제어 .k 의 두 블록으로 나뉜다.

### 2-1. `*mode` 블록 (모드 등록 트리거)

`*mode` 블록 안에 한 줄로 모드를 등록한다.

| 토큰 | 의미 | 근거 |
|------|------|------|
| `part_exchange` | 모드 식별자 (대소문자 무관, `svector[0]`) | KooMeshModifier.py:264 |
| `<modeID>` | 모드 ID (정수, `svector[1]`) | `**partexchange` 옵션 블록과 매칭되는 키 | KooMeshModifier.py:266 |

형식: `part_exchange,<modeID>`

### 2-2. `**partexchange,<modeID>` 옵션 블록

옵션 블록은 `**partexchange,<modeID>` 로 시작하고 `**end` 로 끝난다 (KooMeshModifier.py:1907-1923). 내부에 아래 하위 키워드들을 둔다. (파싱 본체: KooMeshModifier.py:1927-2123)

| 하위 키워드 | 형식 | 의미 | 근거 |
|-------------|------|------|------|
| `*pid,<PID>` | 정수 1개 | 교체/변환 대상 단일 파트 ID. `curOptions["PID"]` | line 1939-1942 |
| `*pids,<PID1>,<PID2>,...` | 정수 다수 (문자열로 보관) | 정렬격자 변환 대상 파트 ID 리스트. `curOptions["PIDS"]` | line 1933-1937 |
| `*converthexato,(<Type>,<vx>,<vy>,<vz>,<tolAngle>[,<zx>,<zy>,<zz>])` | 콤마 구분 (괄호 제거됨) | 요소정식 변환 옵션. `Type` ∈ Shell/TShell/Solid/SolidComp/SolidwithSlack/SolidStructuredZSlack. `Vector`=방향벡터, `ToleranceAngle`=면 판별 허용각. `solidwithslack` 일 때만 z방향 3성분(미지정 시 0,0,1) 추가 | line 1967-1993 |
| `*unstructuredtostructured,(<NX>,<NY>,<NZ>)` | 정수 3개 (괄호 제거됨) | 비정렬→정렬 격자 분할 수. `curOptions["UnstructuredtoStructured"]` | line 1943-1953 |
| `*layerthickness` (다음 줄들) | 줄당 실수 1개 | 정렬격자 변환 시 레이어별 두께 리스트. `*` 만나면 종료, `$` 줄 건너뜀 | line 1954-1966 |
| `*layup` (다음 줄들) | 문자열 블록 | 합성/레이업 정의 템플릿. 토큰(THK/MID/EOS/HGID/NUME, 및 `EOS`/`HGID`) 치환 대상. `*` 만나면 종료 | line 2037-2049 |
| `*thk<name>,<value>` | 실수 1개 | 두께 토큰 정의. `curOptions["THKs"][name]` (`KooDynaFloat`) | line 2050-2054 |
| `*nume<name>,<value>` | 정수 1개 | 적분점 수 등 정수 토큰. `curOptions["NUMEs"][name]` (`KooDynaInt`) | line 2055-2059 |
| `*mid<name>` (다음 줄들) | 카드 본문 | 재료 카드. 헤더 다음 줄부터 `*` 전까지 10폭×8 필드로 파싱. `curOptions["MIDs"][name]` | line 2060-2083 |
| `*eos<name>` (다음 줄들) | 카드 본문 | EOS 카드. 동일 방식. `curOptions["EOSs"][name]` | line 2060-2085 |
| `*hgid<name>` (다음 줄들) | 카드 본문 | HourGlass 카드. 동일 방식. `curOptions["HGIDs"][name]` | line 2060-2087 |
| `*numberofelements,<N>` | 정수 1개 | `curOptions["NumberofElements"]` | line 2033-2035 |
| `*desiredlengthratiosamples,<r1>,...` | 실수 다수 | 목표 길이비 샘플. `curOptions["DesiredLengthRatio"]["Samples"]` | line 1994-1999 |
| `*desiredlengthratiostatistics,<n>,<avg>,<std>,<min>,<max>` | 5개 | 목표 길이비 통계. 필드 수 < 6 이면 종료(exit) | line 2001-2016 |
| `*constraintpids,<PID1>,...` | 다수 | 구속 대상 파트. `curOptions["Constraints"]["PIDs"]` | line 2018-2024 |
| `*inplanerotation,<angle>,<location>` | 2개 | 면내 회전 항목 누적. `curOptions["InplaneRotation"]` | line 2026-2031 |
| 그 외 `*<keyword>` (다음 줄들) | 카드 본문 | 위에 안 걸린 `*` 카드는 일반 키워드로 통째 파싱(`*part_composite` 등 포함). 헤더에 `title`/`_id` 포함 시 분해 규칙 분기 | line 2091-2119 |
| `$` 로 시작하는 줄 | 주석 | 카드 본문 읽기 중 건너뜀 | line 2074-2075 등 |

> 일반 `*<keyword>` 처리 경로(line 2091-2119)에서 `*part_composite` 카드가 `curOptions["*part_composite"]` 로 저장되고, 핸들러에서 `partComp` 로 소비된다 (KooMeshModifier.py:2670-2671, 2712-2723).

핸들러가 옵션을 읽어가는 매핑(`GeneratePartExchange`, KooMeshModifier.py:2643-2671):
- `pids`→curPIDs, `pid`→curPID/part, `converthexato`→convertHexaToOption, `unstructuredtostructured`→convertUnstrToStrOption, `layerthickness`→layerThicknesList, `thk`→thks, `nume`→numes, `mids`→mats, `eos`→eoss, `hgid`→hgids, `layup`→layup, `*part_composite`→partComp.
- 또한 옵션 값이 리스트이고 첫 원소가 문자열이면 `*section`→`AddSectionfromDyna`, `*mat`→`AddMaterialfromDyna` 로 즉시 등록한다 (line 2672-2681).

## 3. 사용 예제

> 전용 예제 파일이 저장소에 없어, 아래는 **파서(KooMeshModifier.py:1907-2123)와 핸들러(2626-2761)에서 역산한 최소 형식 개념 예시**이다. 실제 입력 작성 시 카드 본문 칼럼 폭(10) 정렬과 괄호 표기에 주의할 것. 모든 필드/동작이 실모델에서 검증된 것은 아니다(확인 필요).

### 예시 A — 파트의 Solid 를 Shell 로 변환

```
*mode
part_exchange,1
*
**partexchange,1
*pid,5
*converthexato,(Shell,0.0,0.0,1.0,30.0)
**end
*end
```

- `*pid,5` : PID 5 를 대상으로 지정.
- `*converthexato,(Shell, ... ,30.0)` : 방향벡터 (0,0,1), 허용각 30° 로 Solid→Shell 변환 호출 (KooMeshModifier.py:2752-2754 → KooDynaAdvancedModification.py:988-998).

### 예시 B — 비정렬 메시를 정렬 격자(레이어 두께 지정)로 재구성

```
*mode
part_exchange,1
*
**partexchange,1
*pids,5,6,7
*unstructuredtostructured,(10,10,4)
*layerthickness
0.5
0.5
1.0
1.0
**end
*end
```

- `*pids,5,6,7` : 정렬격자 대상 파트들.
- `*unstructuredtostructured,(10,10,4)` : NX=10, NY=10, NZ=4 격자.
- `*layerthickness` 지정 시 `ConvertUnstructuredtoStructured` 가, 미지정 시 `ConvertUnstructuredtoStructuredPrev` 가 호출된다 (KooMeshModifier.py:2755-2761).

출력은 입력 파일명에 접미사 `_pex` 가 붙은 .k 로 기록된다 (디스패치에서 `additionalword += "_pex"`, KooMeshModifier.py:2807-2809; 실제 기록은 `WriteModifiedFile`, line 2906-2932).

## 4. 동작 원리 (코드 근거)

1. **모드 등록** — `*mode` 블록에서 `part_exchange` 토큰을 만나면 `modeList` 에 `"PART_EXCHANGE"`, `modeIDList` 에 모드 ID 추가
   - `KooMeshModifier.py:264-266`
2. **옵션 파싱** — `**partexchange,<modeID>` 블록을 읽어 `curOptions` (PID/PIDS/THKs/MIDs/EOSs/HGIDs/Layup/converthexato/UnstructuredtoStructured/LayerThickness 등)를 구성, `self.modeIDOption[curModeID]` 에 저장
   - `KooMeshModifier.py:1907-2123`
   - 카드 본문 줄 파싱: `parse_whole(line, [10,10,10,10,10,10,10,10])` (line 2079, 2112)
3. **디스패치** — `GenerateModifiedFile()` 루프에서 `mode == "PART_EXCHANGE"` 분기 → `GeneratePartExchange(modeid)` 호출, 파일명 접미사 `_pex` 누적
   - `KooMeshModifier.py:2807-2809`
4. **핸들러 본체** — `GeneratePartExchange(modeid)` (KooMeshModifier.py:2626-2761)
   - 옵션 → 변수 매핑 (line 2643-2671)
   - 대상 part 의 section/mat 교체 (line 2684-2695)
   - 입력에 나열된 `*MAT`/`*EOS`/`*HGID` 카드를 각각 `AddMaterialfromDyna` / `AddEOSfromDyna` / `SetAdditionalfromDyna` 로 등록하고 원래 토큰명→신규 ID 매핑 생성 (line 2698-2709)
     - `AddMaterialfromDyna` : `KooMaterial.py:1156`, `AddEOSfromDyna` : `KooMaterial.py:1112`
   - `*PART_COMPOSITE` 변환: partComp 본문의 `PID`/THK 토큰/MID 토큰을 실제 값으로 치환 후 `ConvertParttoPartComp(partComp)` 호출 (line 2712-2723) — `KooDynaAdvancedModification.py:1862`
   - `layup` 문자열 토큰 치환(THK/MID/EOS/HGID/NUME, 및 part 의 `EOS`/`HGID`) 후 줄 분해 → 4필드 미만 줄 제외하고 `layupList` 구성 (line 2728-2750)
   - `converthexato` 옵션이 있으면 `convertHexaToOption["PID"]=curPID` 설정 후 `ConvertHexato(option, layupList, curOption)` 호출 (line 2752-2754)
     - `ConvertHexato` (KooMeshModifier.py:2763-2769)는 입력 파일 경로(`.k` 제거)와 함께 `advancedModification.ConvertHexato` 로 위임 (KooDynaAdvancedModification.py:988-1008): `Type` 에 따라 `ConvertSolidtoShell`/`ConvertSolidtoTShell`/`ConvertSolidtoSolidComp`/`ConvertSolidtoSolidwithSlack`/`ConvertSolidtoStructuredSolidwithZSlack` 분기. `solid` 는 무변환(pass)
   - `unstructuredtostructured` 옵션이 있고 `curPIDs` 가 있으면, `LayerThickness` 유무에 따라 `ConvertUnstructuredtoStructuredPrev` 또는 `ConvertUnstructuredtoStructured` 호출 (line 2755-2761) — `KooDynaAdvancedModification.py:550`, `801`
5. **기본 출력** — `PART_EXCHANGE` 는 `_skip_default_write` 를 설정하지 않으므로, 변환 후 전체 모델이 기본 `WriteModifiedFile(additionalword)`(접미사 `_pex`)로 기록된다
   - `KooMeshModifier.py:2883-2891`, `2906-2932`

## 5. 주의사항·한계

- **하나의 모드 블록에서 여러 종류 변환이 조건부로 결합**된다(섹션/재료 교체 + part_composite + layup + converthexato + unstructuredtostructured). 의도치 않은 옵션 조합 시 동작이 복잡해질 수 있으므로 필요한 변환만 단일 목적으로 두는 것을 권장.
- **part 가 None 이면** (PID 미존재) 섹션/재료 교체는 건너뛰고 `"Invalid part ID"` 만 출력된다 (KooMeshModifier.py:2694-2695). 단 이후 `mats`/`eoss`/`hgids` 등록 루프는 그대로 실행되므로 부분 동작에 주의.
- **카드 본문은 10폭×8 고정폭 필드**로 파싱된다 (line 2079, 2112). `*MAT`/`*EOS`/`*HGID` 및 layup 토큰 치환은 토큰 문자열 일치에 의존하므로, 토큰 이름이 카드 필드와 정확히 매칭되도록 작성해야 한다. **확인 필요** (폭/공백 정렬은 사용자 입력 책임).
- **`*desiredlengthratiostatistics` 필드 수가 6 미만이면 `exit()`** 로 프로그램이 종료된다 (line 2003-2005). 입력 오류 시 즉시 중단됨.
- `converthexato` 의 `Type` 이 `solid` 면 변환이 일어나지 않는다(pass) (KooDynaAdvancedModification.py:999-1000).
- `ConvertSolidtoStructuredSolidwithZSlack` 본체는 격자 인덱싱/전치까지만 수행하고 후속 처리가 보이지 않는다 (KooDynaAdvancedModification.py:1010-1035) — **이 Type 의 완결성은 확인 필요**.
- 본 문서의 입력 형식 예시는 코드 역산이며 **실모델 검증 예제가 없으므로**, 실제 적용 전 소규모 모델로 동작 확인 권장.

## 6. 개발 현황

**구현됨 (단, 일부 하위 변환은 부분구현/확인 필요).**

근거: `*mode` 등록부(KooMeshModifier.py:264-266), 옵션 블록 파서(1907-2123), 디스패치 분기(2807-2809), 핸들러 본체(2626-2761), 위임 변환 메서드들(KooDynaAdvancedModification.py:550, 801, 988-1008, 1862; KooMaterial.py:1112, 1156; KooSection.py:407)이 모두 존재하며 호출 경로가 연결되어 있다.

다만 (1) `SolidStructuredZSlack` 변환 경로는 인덱싱 후 후속 처리가 미확인이고, (2) **전용 예제/시나리오 파일이 저장소에 없어 실사용 검증 근거가 미확인**이다. 본문 "확인 필요" 표기 항목 참조.
