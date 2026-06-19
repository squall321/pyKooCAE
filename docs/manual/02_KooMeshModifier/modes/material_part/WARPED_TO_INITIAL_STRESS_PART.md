# KooMeshModifier 모드: WARPED_TO_INITIAL_STRESS_PART

## 1. 목적/개요

`WARPED_TO_INITIAL_STRESS_PART` 모드는 PCB/플레이트류 솔리드 파트의 **뒤틀림(warpage) 형상**을 실제로 메쉬를 휘게 만드는 대신, 그 휨이 유발하는 **초기 응력장(initial stress)** 으로 변환하여 LS-DYNA 입력 카드(`*INITIAL_STRESS_SOLID`)로 기록하는 기능이다.

`WARPED_PART` 모드(`GenerateWarpedPart`)가 절점 좌표를 실제로 이동시켜 형상을 휘게 하는 것과 달리, 이 모드는 warpage 면의 **곡률(curvature)** 로부터 굽힘 응력 텐서를 계산하여 각 솔리드 요소에 초기 응력으로 부여한다. 따라서 메쉬 형상은 평면을 유지한 채, 해석 시작 시점에 warpage에 상응하는 내부 응력 상태를 갖게 된다. 변환된 응력 상태를 평형화하기 위해 `*CONTROL_DYNAMIC_RELAXATION` 카드도 자동으로 추가된다.

- 트리거(모드 등록): `KooMeshModifier.py:297-299` — `*Mode` 섹션에서 `warped_to_initial_stress_part` 키워드를 만나면 `modeList`에 `WARPED_TO_INITIAL_STRESS_PART` 등록
- 옵션 블록 파싱: `KooMeshModifier.py:661-718` — `**WarpedtoInitialStressPart` ~ `**EndWarpedtoInitialStressPart`
- 디스패치: `KooMeshModifier.py:2843-2845` → `GenerateWarpedtoInitialStressPart`
- 핵심 로직: `KooDynaAdvancedModification.py:5744-5818` (`WarpedtoInitialStressPart`)
- 요소별 응력 계산: `KooPart.py:372-477` (`WarpZdirectionParttoInitialStress`), 상/하면 분리는 `KooPart.py:479` (`WarpZdirectionPartfromTopBottomtoInitialStress`)

## 2. 입력 옵션·인자

입력은 KooMeshModifier 옵션 `.txt`(또는 `.k` 형태의 입력 정의 파일) 안에서 `**WarpedtoInitialStressPart,<모드ID>` ~ `**EndWarpedtoInitialStressPart` 블록으로 기술한다. 파싱 근거는 `KooMeshModifier.py:661-718`.

| 옵션 키워드 | 기본값 | 자료형 | 설명 | 근거 (file:line) |
|---|---|---|---|---|
| `**WarpedtoInitialStressPart,<ID>` | — | int | 블록 시작. `<ID>`는 모드 ID (`*Mode`의 `WARPED_TO_INITIAL_STRESS_PART,<ID>`와 매칭) | `KooMeshModifier.py:661-663` |
| `*UnitScale` | `mm` | str | warpage 값의 단위. `Microm`(마이크로미터) 처리 분기 존재 | `KooMeshModifier.py:665,686`; `KooWarpage.py:25-28` |
| `*AmplitudeTop` | `1.0` | float | 상면 warpage 진폭 배율. 곡률 보간기에 곱해짐 | `KooMeshModifier.py:666,689`; `KooPart.py:434` |
| `*AmplitudeBottom` | `0.0` | float | 하면 warpage 진폭 배율 (상/하면 분리 시 사용) | `KooMeshModifier.py:667,692` |
| `*Location` | `0.0,0.0,0.0` | float×3 | warpage 적용 기준 좌표 (xLoc,yLoc,zLoc) | `KooMeshModifier.py:668,695` |
| `*XLength` | `0.0` | float | warpage 적용 영역 X 길이. `0.0`이면 파트 바운딩박스로 자동 산정 | `KooMeshModifier.py:669,698`; `KooDynaAdvancedModification.py:5775-5778` |
| `*YLength` | `0.0` | float | warpage 적용 영역 Y 길이. `0.0`이면 자동 산정 | `KooMeshModifier.py:670,701` |
| `*Direction` | `0.0,0.0,1.0` | float×3 | warpage 적용 방향. **현재 Z방향(`0,0,1`)만 구현됨** | `KooMeshModifier.py:671,704`; `KooDynaAdvancedModification.py:5784,5802` |
| `*AdditionalThickness` | `0.0` | float | 추가 두께. 절점을 z방향으로 두께비율 만큼 변위시키는 데 사용 | `KooMeshModifier.py:672,713`; `KooPart.py:415-417` |
| `*WarpageFileTop` | `None` | str | 상면 warpage 데이터 파일명 (격자형 z값 배열) | `KooMeshModifier.py:673,707`; `warpage.dat` 예제 |
| `*WarpageFileBottom` | `None` | str | 하면 warpage 데이터 파일명. **지정 시 상/하면 분리 경로 실행** | `KooMeshModifier.py:674,710`; `KooDynaAdvancedModification.py:5780,5798` |
| `*PIDs` | `[]` | int 리스트 | 적용 대상 파트 ID 목록 (콤마 다중 지정 가능) | `KooMeshModifier.py:675,714-717` |
| `**EndWarpedtoInitialStressPart` | — | — | 블록 종료 | `KooMeshModifier.py:682-683` |

비고
- `*WarpageFileBottom` 미지정(`None`) → `WarpZdirectionParttoInitialStress`(상면 단독) 호출. 지정 시 → `WarpZdirectionPartfromTopBottomtoInitialStress`(상·하면) 호출 (`KooDynaAdvancedModification.py:5780-5803`).
- `*XLength`/`*YLength`가 0이면 대상 파트들의 합산 바운딩박스로 영역과 `*Location`을 재설정한다 (`KooDynaAdvancedModification.py:5775-5778`).

## 3. 사용 예제

전용 예제 디렉터리가 존재한다: `occProject/Generators/dist/Examples/5.SimulationModify/WarpedtoInitialStressPart/`. 이 디렉터리에는 입력 `.txt`, 모델 `PlateSolid.k`, warpage 데이터 `warpage.dat`, 실행 결과 `*_w2is_w2is.k` 등이 포함되어 있다.

### 예제 1 — 상면 단독 (WarpedtoInitialStressPart.txt)

발췌: `occProject/Generators/dist/Examples/5.SimulationModify/WarpedtoInitialStressPart/WarpedtoInitialStressPart.txt`

```
*Inputfile
PlateSolid.k
*Mode
WARPED_TO_INITIAL_STRESS_PART,1
**WarpedtoInitialStressPart,1
*UnitScale,Microm
*AmplitudeTop,1000.0
*AmplitudeBottom,0.0
*Location,0.0,0.0,0.0
*XLength,0.0
*YLength,0.0
*Direction,0.0,0.0,1.0
*AdditionalThickness,0.0
*WarpageFileTop,warpage.dat
*PIDs,1
**EndWarpedtoInitialStressPart
*End
```

### 예제 2 — 상·하면 분리 (WarpedtoInitialStressPartTopBottom.txt)

발췌: 같은 디렉터리 `WarpedtoInitialStressPartTopBottom.txt`. 차이는 `*WarpageFileBottom,warpage.dat`와 `*AmplitudeBottom,1000.0`이 추가되어 상/하면 분리 경로가 실행되는 점이다.

```
**WarpedtoInitialStressPart,1
*UnitScale,Microm
*AmplitudeTop,1000.0
*AmplitudeBottom,1000.0
...
*WarpageFileTop,warpage.dat
*WarpageFileBottom,warpage.dat
*PIDs,1
**EndWarpedtoInitialStressPart
```

### 예제 3 — 다중 파트(타이 모델) (WarpedtoInitialStressPartWarpedTied.txt)

발췌: 같은 디렉터리 `WarpedtoInitialStressPartWarpedTied.txt`. 두 개의 모드 블록(`,1`/`,2`)을 각각 다른 PID(1/2)와 부호 반대인 진폭(`+1000.0`/`-1000.0`)으로 적용한다.

```
*Mode
WARPED_TO_INITIAL_STRESS_PART,1
WARPED_TO_INITIAL_STRESS_PART,2
**WarpedtoInitialStressPart,1
...
*AmplitudeTop,1000.0
*PIDs,1
**EndWarpedtoInitialStressPart
**WarpedtoInitialStressPart,2
...
*AmplitudeTop,-1000.0
*PIDs,2
**EndWarpedtoInitialStressPart
```

### warpage.dat 형식

`warpage.dat`는 공백 구분 격자형 z값 2D 배열이다. 값 `9999`는 무효(마스크) 영역을 표현하는 것으로 보인다 (정확한 의미는 KooWarpage 파서 확인 필요).

```
0.043227271  0.084565303  ... 1.17804E-16
0.084565303  0.165434697  ... 2.30459E-16
0.122207426  0.2390738    9999  9999  9999  ...
```

(근거: `occProject/Generators/dist/Examples/5.SimulationModify/WarpedtoInitialStressPart/warpage.dat`)

## 4. 동작 원리 (코드 근거)

전체 흐름:

1. **모드 등록** — `*Mode`에서 `warped_to_initial_stress_part` 키워드 감지 시 모드 큐에 등록 (`KooMeshModifier.py:297-299`).
2. **옵션 파싱** — `**WarpedtoInitialStressPart,<ID>` 블록을 읽어 `modeIDOption[ID]` 딕셔너리로 저장 (`KooMeshModifier.py:661-718`).
3. **디스패치** — 모드 실행 루프에서 `GenerateWarpedtoInitialStressPart(modeid)` 호출, alias 접미어 `_w2is` 부여 (`KooMeshModifier.py:2843-2845`).
4. **위임** — `GenerateWarpedtoInitialStressPart`가 `advancedModification.WarpedtoInitialStressPart(curOption)` 호출 (`KooMeshModifier.py:2573-2575`).
5. **영역 산정** — 대상 PID들의 바운딩박스로 xmin~zmax 계산. `XLength`/`YLength`가 0이면 영역과 `Location`을 자동 설정 (`KooDynaAdvancedModification.py:5765-5778`).
6. **분기** — `WarpageFileBottom`이 `None`이면 상면 단독 `WarpZdirectionParttoInitialStress` 호출, 아니면 상·하면 `WarpZdirectionPartfromTopBottomtoInitialStress` 호출. 단, `Direction == (0,0,1)` 조건이 만족될 때만 실행 (`KooDynaAdvancedModification.py:5780-5803`).
7. **요소별 응력 계산** (`KooPart.py:372-477`):
   - warpage 면을 `KooWarpage`로 로드하고 단위 적용 (`KooPart.py:388-389`), z방향 보간기 생성 (`KooPart.py:406`).
   - `AdditionalThickness`에 비례해 절점을 z방향으로 변위 (`KooPart.py:415-417`).
   - warpage 곡률 보간기 생성(`AmplitudeTop` 곱) 후 각 요소 중심점에서 곡률 `dw²/dx²`, `dw²/dy²`, `dw²/dxy` 추출 (`KooPart.py:434-435`).
   - 재료 `E`, `nu`를 읽어 (`KooPart.py:439-440`) 각 솔리드 요소(tetra4/hexa8)에 대해 곡률 기반 굽힘 응력 텐서 계산 `GetStressfromDisplacementandCurvatureXYPlane` (`KooPart.py:459`).
   - 초기 응력 부호 반전(`stressTensor = -stressTensor`, `KooPart.py:460`).
   - 경계 요소(인접 요소 3개 초과)는 응력을 0.5배로 완화 (`KooPart.py:461-465`).
   - EID별 6개 응력성분 리스트(S11,S22,S33,S12,S13,S23) 반환 (`KooPart.py:466-477`).
8. **초기 응력 카드 생성** — 반환된 EID/응력 리스트로 `initialManager.CreateInitialStressSolid(...)` 호출 → `*INITIAL_STRESS_SOLID` 카드 생성. NINT=1, NHISV=0 등 부가 인자는 리스트 크기만큼 0/1로 채움 (`KooDynaAdvancedModification.py:5786-5797`; `KooInitial.py:461-465`).
9. **동적 완화 제어 추가** — `controlDynamicRelaxation`이 없으면 기본값으로 `*CONTROL_DYNAMIC_RELAXATION` 생성 (`KooDynaAdvancedModification.py:5817-5818`; 기본 인자는 `KooDynaControl.py:965`: NRCYCK=250, DRTOL=0.001, DRFCRT=0.995 등).
10. **출력 기록** — 모드 루프 종료 후 `WriteModifiedFile`로 수정 `.k` 작성. alias 접미어 `_w2is` 반영 (`KooMeshModifier.py:2845,2886-2888`). 예: `PlateSolid_w2is.k`, `PlateSolid_tied_w2is_w2is.k`.

출력 요약: 입력 `.k`에 (a) 각 솔리드 요소의 `*INITIAL_STRESS_SOLID` 카드와 (b) `*CONTROL_DYNAMIC_RELAXATION` 카드가 추가된 새 `.k` 파일.

## 5. 주의사항·한계

- **Z방향 전용**: `Direction`은 `(0,0,1)`일 때만 실제 처리된다. 그 외 방향은 분기 조건 미충족으로 아무 작업도 수행되지 않는다 (`KooDynaAdvancedModification.py:5784,5802`).
- **솔리드 요소 한정**: 응력 계산은 `tetra4`/`hexa8` 솔리드 요소에 대해서만 수행된다 (`KooPart.py:426,453`). 셸 등 다른 요소 타입은 건너뜀.
- **재료 E/nu 의존**: 대상 파트에 유효한 재료(E, nu 조회 가능)가 연결되어 있어야 한다 (`KooPart.py:439-440`). 미연결 시 동작은 확인 필요.
- **PID 존재 검사**: `PIDs`에 지정된 파트가 모델에 없으면 조용히 건너뛴다 (`KooDynaAdvancedModification.py:5781-5782`).
- **경계 요소 응력 완화**: 인접 요소 수가 3 초과인 경계 요소의 응력은 0.5배로 스케일된다. 코드 내 주석으로 다른 완화 규칙(boundary==1 → 0.5배)은 비활성화되어 있다 (`KooPart.py:461-465`).
- **단위계**: warpage 데이터 단위는 `UnitScale`로 제어하며 `Microm` 분기가 있다 (`KooWarpage.py:25-28`). 그 외 단위 문자열 처리는 확인 필요.
- **warpage.dat의 `9999` 값**: 무효/마스크 영역으로 추정되나 파서 동작은 확인 필요.
- **AmplitudeBottom 기본값 차이**: 옵션 파싱 기본값은 `0.0`(`KooMeshModifier.py:667`)이지만, 상·하면 분리 경로에서만 의미를 가진다.

## 6. 개발 현황

**구현됨 (부분구현 측면 포함)**

근거:
- 모드 등록·옵션 파싱·디스패치·핵심 로직이 모두 존재하고 서로 연결됨 (`KooMeshModifier.py:297-299, 661-718, 2843-2845, 2573-2575`; `KooDynaAdvancedModification.py:5744-5818`; `KooPart.py:372-477`).
- 동작하는 전용 예제 세트와 실행 산출물 존재: `occProject/Generators/dist/Examples/5.SimulationModify/WarpedtoInitialStressPart/`에 입력 `.txt` 3종(상면/상하면/타이), `PlateSolid*.k`, `warpage.dat`, LS-DYNA 실행 결과(`d3plot`, `*_w2is_w2is.k`, `messag`, `status.out` 등)가 포함됨.
- **부분구현 성격**: 적용 방향이 Z(`0,0,1`)로 한정되어 있어 임의 방향 warpage는 미지원 (`KooDynaAdvancedModification.py:5784,5802`).

확인 필요 항목: warpage.dat의 `9999` 마스크 의미, `Microm` 외 단위 문자열 처리, 재료 미연결 시의 거동.
