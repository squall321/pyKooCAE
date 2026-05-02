# VIBRATION_LOAD 모드 예제

다중 파트에 동기화된 진동 하중을 적용하는 모드.

## 동작 원리

- **공통 시간 곡선** (`*DEFINE_CURVE`) 1개 + 파트별 다른 amplitude
- 파트별 amplitude 결정 방식:
  - **Explicit**: 사용자가 파트별 상대값 직접 입력
  - **VolumeProportional**: 기준 파트 대비 부피 비율 자동 계산
- 입력 곡선의 의미:
  - **Force**: 사용자 곡선 = 파트 합력 [N]. SF = relative_factor / part_mass (시스템이 자동 변환)
  - **Acceleration**: 사용자 곡선 = 가속도 [length/time²]. SF = relative_factor (mass 무관)

생성되는 LS-DYNA 카드:
```
*DEFINE_CURVE_TITLE   ← 공통 시간 곡선 1개
*SET_PART_LIST_TITLE  ← 파트당 1개 (단일 PID 포함)
*LOAD_BODY_PARTS_<dir>← 파트당 1개 (PSID + LCID + SF)
```

## 사용법

KooMeshModifier 옵션 파일(`step_config.txt`) 작성 후 실행:

```bash
KooMeshModifier vibration_explicit.txt /path/to/model_dir
```

## 예제 1: Explicit 모드 (vibration_explicit.txt)

파트 1, 2, 3에 각각 1.0 / 0.5 / 1.5 상대 강도 적용:

```
*Inputfile
MinimumModel.k
*Info,VibTest,DV1
*Description,Vibration load (explicit factor)
*Creator,user,user@example.com,CAE,Team
*Mode
VIBRATION_LOAD,1
**VibrationLoad,1
Direction,Z                    # X | Y | Z
LoadType,Force                 # Force (default) | Acceleration
RelativeMode,Explicit          # Explicit | VolumeProportional
LoadCurve                      # 시간-하중 데이터 (블록)
0.0, 0.0
0.001, 100.0
0.002, 200.0
0.003, 100.0
0.004, 0.0
EndLoadCurve
PartFactors                    # PID, relative_factor (블록)
1, 1.0
2, 0.5
3, 1.5
EndPartFactors
**EndVibrationLoad
*End
```

**결과:**
- 시간 0.0~0.004s 동안 PID 1에 합력 100→200→100→0 N
- PID 2는 같은 패턴 × 0.5 (50→100→50→0 N)
- PID 3는 같은 패턴 × 1.5

## 예제 2: VolumeProportional 모드 (vibration_volume.txt)

파트 부피에 비례한 합력 (기준 파트 = PID 1):

```
*Inputfile
MinimumModel.k
*Info,VibTest,DV1
*Description,Vibration load (volume proportional)
*Creator,user,user@example.com,CAE,Team
*Mode
VIBRATION_LOAD,1
**VibrationLoad,1
Direction,X
LoadType,Force
RelativeMode,VolumeProportional
ReferencePart,1                # 기준 PID (생략 시 첫 파트 자동 + warning)
LoadCurve
0.0, 0.0
0.005, 1000.0
0.01, 0.0
EndLoadCurve
PartList                       # 적용 파트 목록
1, 2, 3, 4, 5
EndPartList
**EndVibrationLoad
*End
```

**결과:**
- 기준 파트 PID 1 합력: 사용자 곡선 그대로 (max 1000N)
- 다른 파트 합력: vol_i / vol_1 비율로 자동 (큰 파트 = 큰 합력)
- 모든 density 동일 시 → 모든 파트가 같은 가속도 가짐

## 옵션 레퍼런스

| 옵션 | 값 | 설명 |
|---|---|---|
| `Direction` | `X` / `Y` / `Z` | 가진 방향 (단일 축) |
| `LoadType` | `Force` (default) / `Acceleration` | 입력 곡선의 단위 |
| `RelativeMode` | `Explicit` / `VolumeProportional` | 파트별 amplitude 결정 방식 |
| `ReferencePart` | PID (정수) | VolumeProportional 시 기준 파트. 생략 시 첫 파트 |
| `LoadCurve` ~ `EndLoadCurve` | `t, value` 쌍 | 시간 곡선 데이터 (최소 2 points) |
| `PartFactors` ~ `EndPartFactors` | `pid, factor` 쌍 | Explicit 모드 전용 |
| `PartList` ~ `EndPartList` | 콤마 구분 PID | VolumeProportional 모드 전용 |

## 동작 검증

실행 시 출력 예시:
```
[VIBRATION_LOAD] Direction=Z, LoadType=Force, Mode=Explicit, Targets=[1, 2, 3]
  LoadCurve: t=[0.0, 0.004], max |force|=2.0000e+02
  PID 1: volume=1.9169e+04, mass=5.3097e-05
  PID 2: volume=2.8800e+02, mass=7.9776e-07
  PID 3: volume=1.0788e+03, mass=1.9850e-06
  → *DEFINE_CURVE LCID=1 (5 points)
  → PSID=1 (PID=1), SF=1.8833e+04, rel=1.000, mass=5.3097e-05
  → PSID=2 (PID=2), SF=6.2675e+05, rel=0.500, mass=7.9776e-07
  → PSID=3 (PID=3), SF=7.5567e+05, rel=1.500, mass=1.9850e-06
```

## 제한사항

- **Beam/Discrete 요소 무시**: mass/volume 계산에서 제외 (Solid + Shell만)
- **단일 축**: 다축 동시 진동은 모드를 여러 번 호출 (LCID/PSID 자동 증가)
- **mass = 0 경고**: density=0이거나 MAT 누락 시 Force 모드에서 SF 무한대 위험. 출력 시 [WARN] 표시
- **새 SET_PART_LIST 생성**: 기존 PSID와 충돌 없이 maxSID + 1부터 자동 할당

## 다른 모드와 조합

같은 step_config 파일에서 다른 모드와 함께 사용 가능:
```
*Mode
DROP_ATTITUDE,1
VIBRATION_LOAD,2
**DropAttitude,1
...
**EndDropAttitude
**VibrationLoad,2
...
**EndVibrationLoad
*End
```

이 경우 DROP_ATTITUDE → VIBRATION_LOAD 순으로 적용. 출력 파일 1개에 두 모드 결과 통합.
