# KooMeshModifier 모드: VIBRATION_LOAD

## 1. 목적 / 개요

다중 파트에 **동기화된 진동(가진) 하중**을 적용하는 KooMeshModifier 모드입니다.

- 공통 시간 곡선(`*DEFINE_CURVE`) **1개**를 만들고, 파트마다 서로 다른 amplitude(scale factor, SF)를 부여합니다.
- 파트별 amplitude 결정 방식은 두 가지입니다.
  - **Explicit**: 사용자가 파트별 상대값을 직접 입력
  - **VolumeProportional**: 기준 파트 대비 부피 비율로 자동 계산
- 입력 곡선의 의미(단위)는 `LoadType`으로 선택합니다.
  - **Force**: 곡선 = 파트 합력 → 내부적으로 `SF = relative_factor / part_mass` 로 변환 (가속도 곡선화)
  - **Acceleration**: 곡선 = 가속도 그대로 → `SF = relative_factor` (mass 무관)

생성되는 LS-DYNA 카드 (파트 N개 기준):

```
*DEFINE_CURVE                       ← 공통 시간 곡선 1개
*SET_PART (단일 PID)                ← 파트당 1개
*LOAD_BODY_GENERALIZED_SET_PART     ← 파트당 1개 (PSID + LCID + AX/AY/AZ=SF)
```

근거: `occProject/Generators/KooCAEManager/KooVibrationLoad.py:1-16` 모듈 docstring, `:105-137` 카드 생성 루프.

## 2. 입력 옵션 · 인자

KooMeshModifier 옵션(step_config) 파일의 `**VibrationLoad,<modeID>` 블록에서 파싱됩니다.

| 옵션 | 값 / 형식 | 기본값 | 설명 |
|---|---|---|---|
| `Direction` | `X` / `Y` / `Z` | `Z` | 가진 방향 (단일 축). X→AX, Y→AY, Z→AZ에 SF 배치 |
| `LoadType` | `Force` / `Acceleration` | `Force` | 입력 곡선의 단위 의미 |
| `RelativeMode` | `Explicit` / `VolumeProportional` | `Explicit` | 파트별 amplitude 결정 방식 |
| `ReferencePart` | PID(정수) | (없음) | VolumeProportional 시 기준 파트. 생략 시 PartList 첫 파트 + warning |
| `LoadCurve` … `EndLoadCurve` | 줄당 `t, value` | (필수) | 시간 곡선 데이터. 최소 2 points 필요 |
| `PartFactors` … `EndPartFactors` | 줄당 `pid, factor` | (Explicit 필수) | Explicit 모드 파트별 상대값 |
| `PartList` … `EndPartList` | 콤마 구분 PID 목록 | (VolumeProportional 필수) | VolumeProportional 적용 파트 목록 |

근거:
- 파싱 기본값 dict: `occProject/Generators/KooMeshModifier.py:2238-2245`
- 단일 라인 옵션(`Direction`/`LoadType`/`RelativeMode`/`ReferencePart`): `KooMeshModifier.py:2300-2310`
- 멀티라인 블록(`LoadCurve`/`PartFactors`/`PartList` 및 `End*` 종료 마커): `KooMeshModifier.py:2260-2298`
- 알 수 없는 옵션 라인은 `Warning: unknown VibrationLoad option line` 출력 후 무시: `KooMeshModifier.py:2311-2312`

**유효성 검사 (apply_vibration_load):**
- `Direction`이 X/Y/Z가 아니면 ValueError (`KooVibrationLoad.py:33-34`)
- `LoadCurve` 없음 또는 2점 미만이면 ValueError (`:38-39`)
- Explicit인데 `PartFactors` 없으면 ValueError (`:44-45`)
- VolumeProportional인데 `PartList` 없으면 ValueError (`:49-50`)
- `ReferencePart`가 PartList에 없으면 ValueError (`:57-58`)
- `RelativeMode`가 둘 중 하나가 아니면 ValueError (`:59-60`)

## 3. 사용 예제

### 예제 1: Explicit / Force (Examples/vibration_load/README.md 발췌)

파트 1, 2, 3에 각각 1.0 / 0.5 / 1.5 상대 강도, Z축 합력 진동:

```
*Inputfile
MinimumModel.k
*Info,VibTest,DV1
*Description,Vibration load (explicit factor)
*Creator,user,user@example.com,CAE,Team
*Mode
VIBRATION_LOAD,1
**VibrationLoad,1
Direction,Z
LoadType,Force
RelativeMode,Explicit
LoadCurve
0.0, 0.0
0.001, 100.0
0.002, 200.0
0.003, 100.0
0.004, 0.0
EndLoadCurve
PartFactors
1, 1.0
2, 0.5
3, 1.5
EndPartFactors
**EndVibrationLoad
*End
```

실행:

```bash
KooMeshModifier vibration_explicit.txt /path/to/model_dir
```

### 예제 2: Acceleration / Explicit (Examples/vibration_load/vibration_acceleration.txt 발췌)

Y축 사인 펄스 가속도(±9810 = 1g, mm/ms² 단위계 가정)를 파트 1,2,3에 동일 적용:

```
*Mode
VIBRATION_LOAD,1
**VibrationLoad,1
Direction,Y
LoadType,Acceleration
RelativeMode,Explicit
LoadCurve
0.0, 0.0
0.0005, 9810.0
0.001, 0.0
0.0015, -9810.0
0.002, 0.0
EndLoadCurve
PartFactors
1, 1.0
2, 1.0
3, 1.0
EndPartFactors
**EndVibrationLoad
*End
```

### 예제 3: VolumeProportional (Examples/vibration_load/README.md 발췌)

부피 비례 합력 (기준 PID 1):

```
**VibrationLoad,1
Direction,X
LoadType,Force
RelativeMode,VolumeProportional
ReferencePart,1
LoadCurve
0.0, 0.0
0.005, 1000.0
0.01, 0.0
EndLoadCurve
PartList
1, 2, 3, 4, 5
EndPartList
**EndVibrationLoad
*End
```

예제 파일 위치: `Examples/vibration_load/` (`vibration_explicit.txt`, `vibration_acceleration.txt`, `vibration_volume.txt`, `README.md`).

## 4. 동작 원리 (코드 근거)

1. **모드 등록 (입력 트리거)**: `*Mode` 섹션에서 `vibration_load` 문자열을 만나면 `modeList`에 `"VIBRATION_LOAD"` 추가 — `KooMeshModifier.py:324-326`.

2. **옵션 파싱**: `**vibrationload` 블록을 만나면 기본값 dict 생성 후 한 줄씩 파싱하여 `self.modeIDOption[curModeID]`에 저장 — `KooMeshModifier.py:2234-2313`. `LoadCurve`는 `[t, value]` 쌍 리스트, `PartFactors`는 `{pid: factor}` dict, `PartList`는 PID 리스트로 누적됩니다 (`:2274-2298`).

3. **디스패치**: 처리 루프에서 `elif mode == "VIBRATION_LOAD":` → `self.GenerateVibrationLoad(modeid)` 호출, `self._skip_default_write = True` 설정으로 공용 WriteModifiedFile을 건너뜀 — `KooMeshModifier.py:2873-2875`.

4. **Generate 위임**: `GenerateVibrationLoad`는 입력 파일 경로(확장자 제거)와 옵션을 `self.advancedModification.VibrationLoad(curOption, filePath)`로 전달 — `KooMeshModifier.py:2447-2451`.

5. **카드 적용 + 출력 (KooDynaAdvancedModification.VibrationLoad)** — `KooDynaAdvancedModification.py:5072-5122`:
   - ① `from KooCAEManager.KooVibrationLoad import apply_vibration_load` → 메모리 모델에 진동 카드 적용 (`:5079-5080`).
   - ② `runDirectoryMode == True` 이면 `GenerateRunID()`로 `Run_<id>/` 폴더 + `Output/` 생성, `VibrationSet` 파일로 write, `.done` 파일 생성 (KooChainRun polling용) — `:5087-5119` (DropAttitude 패턴 답습).
   - ② 비활성(standalone) 이면 입력 파일 옆에 `_vib.k`로 write — `:5120-5122`.

6. **apply_vibration_load 핵심 로직** — `KooVibrationLoad.py:18-137`:
   - 대상 파트 결정: Explicit→`PartFactors.keys()`, VolumeProportional→`PartList` (`:42-58`).
   - 파트별 mass/volume 계산: `_compute_part_mass_volume` (Solid+Shell만, Beam/Discrete 무시) — `:69-78`, 정의 `:143~`.
   - relative_factor: Explicit→입력값 그대로, VolumeProportional→`volume_i / volume_ref` (`:81-87`).
   - SF 계산: Force→`SF_i = relative_factor_i / mass_i` (mass=0이면 SF=0), Acceleration→`SF_i = relative_factor_i` (`:95-103`).
   - `*DEFINE_CURVE` 1개 생성: `defineManager.CreateDefineCurvewithID(LCID, A1=시간, O1=값)` — `:105-117`.
   - 파트마다 단일 PID `*SET_PART` 생성(`_alloc_psid`/`_create_single_part_set`) 후 `loadManager.CreateLoadBodyParts(direction, psid, lcid, sf, drlcid=0, drsf=1.0)` 호출 — `:119-137`.

7. **카드 emit**: `CreateLoadBodyParts`는 `KooLoadBodyParts` 객체를 `bodyLoads`에 추가 — `KooLoad.py:858-862`. write 시 `*LOAD_BODY_GENERALIZED_SET_PART` 카드로 출력되며, direction에 따라 SF가 AX/AY/AZ 중 하나에 배치되고 나머지는 0 — `KooLoad.py:141-176`. (정식 `*LOAD_BODY_PARTS`는 deck당 1회 제약이라 다중 part set 가능한 generalized 카드로 emit — `KooLoad.py:126-129`.)

**실행 출력 예시** (README.md):
```
[VIBRATION_LOAD] Direction=Z, LoadType=Force, Mode=Explicit, Targets=[1, 2, 3]
  LoadCurve: t=[0.0, 0.004], max |force|=2.0000e+02
  PID 1: volume=1.9169e+04, mass=5.3097e-05
  → *DEFINE_CURVE LCID=1 (5 points)
  → PSID=1 (PID=1), SF=1.8833e+04, rel=1.000, mass=5.3097e-05
```

## 5. 주의사항 · 한계

- **Beam/Discrete 요소 무시**: mass/volume 계산이 Solid+Shell만 대상이라 Beam/Discrete 전용 파트는 volume=0으로 처리되어 무시될 수 있음 (`KooVibrationLoad.py:74-75`).
- **mass=0 위험**: density=0 또는 MAT 누락 시 Force 모드에서 SF가 비정상이 될 수 있어 코드는 `mass>0`일 때만 나눗셈, 아니면 SF=0으로 처리하고 `[WARN]` 출력 (`:76-77`, `:99-101`).
- **단일 축**: 한 블록은 한 방향(X/Y/Z)만 가진. 다축 동시 진동은 모드를 여러 번 호출해야 함 (LCID/PSID는 자동 증가).
- **단위계 사용자 책임**: Force/Acceleration 곡선 값의 단위는 모델 단위계와 일치해야 함 (코드가 단위 변환을 하지 않음). 예제의 9810은 mm/ms² 단위계 1g 가정값.
- **VolumeProportional 기준 파트 부피=0**: `ReferencePart` 부피가 0이면 ValueError (`:84-86`).
- **새 ID 자동 할당**: LCID/PSID는 기존 최대 ID + 1 부터 할당 (`_alloc_lcid`/`_alloc_psid`).
- **출력 처리**: 이 모드는 공용 WriteModifiedFile을 건너뛰고 자체 write를 수행함 (`KooMeshModifier.py:2875`). runDirectoryMode면 `Run_<id>/VibrationSet(.k)` + `.done`, 아니면 `<입력>_vib.k`.

## 6. 개발 현황

**구현됨** — 입력 파싱(`KooMeshModifier.py:324-326, 2234-2313`), 디스패치(`:2873-2875`), Generate 위임(`:2447-2451`), 카드 적용/출력(`KooDynaAdvancedModification.py:5072-5122`), 핵심 로직(`KooVibrationLoad.py:18-137`), emit(`KooLoad.py:858-862, 141-176`)이 모두 존재하고, `Examples/vibration_load/`에 3개 실행 예제 + README가 갖춰져 있음.

참고(확인 필요): git 로그상 KooChainRun 진동 워크플로우 연동(`mode: vibration`) 흔적이 있으나, KooChainRun 소스 레벨의 진동 모드 연동 코드는 본 조사 범위(KooMeshModifier 측)에서 직접 확인하지 못함. KooChainRun 연동 부분은 별도 확인 필요.
