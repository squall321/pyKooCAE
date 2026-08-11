# DOE · 위치/각도 소스

## 1. 목적 / 개요

KooChainRun의 DOE(Design of Experiments)는 **무엇을 어디에/어떤 자세로 떨어뜨릴(또는 때릴)지**를
자동으로 펼쳐 시뮬레이션 케이스 목록을 만든다. 크게 두 갈래가 있다.

- **각도 소스 (Angle Source)** — 낙하 자세(Roll/Pitch/Yaw)를 생성한다.
  누적 낙하(DROP) 워크플로우(`CumulativeDesigner`)에서 `angle_source` 키로 쓰인다.
  - 코드: `Runner/AngleSourceParser.py` — `cuboid_geometry`, `fibonacci_lattice`,
    `pitching_sweep`, `rolling_sweep`, `case_txt_file`
  - 자세에 산포(tolerance)를 더해 LHS/Grid/Random DOE를 만드는 보조 단계:
    `Runner/ToleranceDOEGenerator.py`
  - 누적 Step마다 어떤 각도를 쓸지 정하는 믹싱 전략: `Runner/AngleMixingStrategy.py`

- **위치 소스 (Position Source)** — 충격/낙하 위치(X, Y)를 생성한다. 두 가지 구현이 공존한다.
  - **(A) `Runner/ImpactPositionSource.py`** — `position_source` 키.
    타입: `grid_nxm`, `grid_spacing`, `manual`. `CumulativeDesigner`가 사용
    (`Runner/CumulativeDesigner.py:366`).
  - **(B) `Runner/DropWeightImpactWorkflow.py`** — `simulation_params.locations` 키.
    모드: `grid`(+`spacing`), `list`, `part_center`, `lhs`.
    낙하추 충격(drop_weight_impact) 워크플로우 전용 (`_generate_impact_locations`, line 368).

> **주의 — 지시서의 항목명 대응**
> 지시서의 위치 소스 "grid_nxm, lhs, part_center, spacing"은 **두 시스템에 걸쳐 있다.**
> `grid_nxm`은 (A) 시스템, `lhs`/`part_center`/`spacing`은 (B) 시스템(`locations`)의 모드/옵션이다.
> 본 문서는 두 시스템을 명시적으로 구분해 기술한다.

---

## 2. 입력 옵션 · 인자

### 2-A. 각도 소스 (`angle_source`, `Runner/AngleSourceParser.py`)

공통: `angle_source.source_type` 으로 타입 선택. 미지정 시 `cuboid_geometry`
(`Runner/CumulativeDesigner.py:505`).

#### (1) `cuboid_geometry` — Face/Edge/Corner 26방향

| 키 | 기본값 | 설명 |
|---|---|---|
| `include_faces` | `true` | F1–F6 (6 면) 포함 |
| `include_edges` | `true` | E01–E12 (12 모서리) 포함 |
| `include_corners` | `true` | C1–C8 (8 꼭짓점) 포함 |
| `only` | `null` | **특정 자세만 선택.** 설정 시 위 세 플래그를 무시하고 나열 순서대로 방출 |

세 옵션 모두 true면 6+12+8 = **26방향**.

`only` 는 짧은 코드(`"C1"`, `"F5"`, `"E01"`)와 전체 이름(`"C1_Back_Right_Top"`)을 모두 받으며
대소문자를 가리지 않는다. 문자열 하나만 줘도 된다(`"only": "C1"`).
**알 수 없는 이름은 조용히 무시하지 않고 `ValueError`** 로 막고 사용 가능한 코드를 알려준다.

```json
"cuboid_geometry": { "only": ["C1", "F5"] }
```

특정 자세 주변을 집중 조사할 때 `tolerance`(2-B)와 함께 쓰는 것이 표준 사용법이다.

#### (2) `fibonacci_lattice` — 구면 균등 분포

| 키 | 기본값 | 설명 |
|---|---|---|
| `num_points` | 26 | 생성할 포인트(케이스) 수. `previous_stages` 사용 시 **최종 누적 총량** |
| `num_directions` | — | `num_points` 별칭. `num_points` 가 없거나 0일 때만 사용 |
| `sampling_space` | `"physical"` | 등간격을 잴 공간. `"latlon"` 이면 구 동작(아래 🔴) |
| `principal_directions` | `null` | 표준 자세를 반드시 포함. `faces`(6) / `faces_corners`(14) / `cuboid26`(26) |
| `previous_stages` | `null` | 단계별 확장. 이미 돌린 단계들의 **누적 개수**를 오름차순 배열로 |
| `progressive` | `false` | farthest-point 순서로 재정렬(부분 실행 시 편향 방지). `principal_directions` 설정 시 무의미 |
| `angle_spacing` | `null` | 정의만 있고 파서가 사용하지 않는 죽은 키. 개수는 `num_points` 로만 제어 |

##### 🔴 `sampling_space` — 기본값이 `physical` 이다 (2026-08-05 변경)

과거 기본이던 lat/lon 파라미터 공간 균등은 **실제 낙하 방향으로 환산하면 심하게 뒤틀린다.**
낙하 방향 이웃 각거리의 최대÷최소 실측값.

| N | `latlon` (구 기본) | `physical` (현 기본) |
|---|---|---|
| 20 | **∞** (같은 방향 중복 발생) | 1.1배 |
| 100 | **65.6배** | 1.1배 |
| 500 | **∞** (중복 발생) | 1.1배 |

방향 분포도 적도 부근(−30°~+30°)에 74%가 몰리고 극(위/아래 낙하)은 5%뿐이었다
(`physical` 은 51% / 13%). N=20 에서는 20개 중 1쌍이 완전히 같은 방향이 되었다.

> 구 동작 재현이 필요한 프로젝트(이미 돌린 결과와 각도를 맞춰야 하는 경우)만
> `"sampling_space": "latlon"` 을 **명시**한다. 신규 프로젝트에는 권장하지 않는다.

##### `principal_directions` — 표준 자세 + 빈틈 채우기

표준 낙하 자세를 먼저 배치하고(원래 이름·오일러각 보존), 나머지를
**정규 N세트에서 시드에 가장 가까운 점을 시드 개수만큼 제거한 나머지**로 채운다.

```text
principal_directions="cuboid26", num_points=100
  → 표준 26개(면6+모서리12+꼭짓점8) + (정규 100세트 − 최근접 26개) 74개 = 100개
```

채움 점이 정규 N세트의 **실제 위치**이므로 `previous_stages` 확장과 규칙이 일관된다.
설정 시 `sampling_space` 는 자동으로 `physical` 이 강제된다.
`num_points` 가 시드 개수보다 작으면 시드만 잘라서 반환한다.

##### `previous_stages` — 단계별 확장

작게 먼저 돌리고 나중에 채워 넣는 워크플로우. **이전 단계 목록만 선언하면**
그 위치를 결정론적으로 재현한 뒤 이번 N세트에서 그것들과 가까운 점을 정확히 제거하고
나머지 신규분만 방출한다. 어느 경로로 확장하든 누적 위치 집합이 항상 동일하다.

```json
{ "num_points": 1000, "previous_stages": [120, 500] }
```

→ 재현 누적 500개, **신규 500개만 방출**(`P0501`~`P1000`). 방출 수 = `num_points − previous_stages[-1]`.

검증: 양의 정수·엄격 오름차순·마지막 값 < `num_points`. 위반 시 `ValueError`.

품질 대가(실측): 누적 1000의 최소 간격 3.15°(정규 5.60° 대비 56%), 중앙 4.73°(정규 6.10°).
중복·뭉침은 0. 최고 균일도가 필요하면 단계를 쓰지 말고 목표 N을 한 번에 돌린다.

> 🔴 **실제로 돌린 단계를 하나도 빠뜨리면 안 된다.** `120 → 500` 을 돌려놓고
> `previous_stages: [500]` 이라고만 적으면 재현이 어긋나 1000개 중 4개가 1° 이내로 겹친다.
> 자동 검출이 불가능하므로 생성 시 찍히는 로그로 확인한다.
> `단계별 각도 생성: 이전 단계 [120] → 재현 누적 120개, 이번 신규 380개, 최종 누적 500개`
>
> 또한 단계마다 `sampling_space`/`principal_directions`/`progressive` 가 바뀌면 재현이 깨진다.
> **`num_points` 외의 설정은 모든 단계에서 동일해야 한다.**

#### (3) `pitching_sweep` — Pitch 스윕 (Roll 고정)

| 키 | 기본값 | 설명 |
|---|---|---|
| `pitch_min` | -90.0 | Pitch 최소(deg) |
| `pitch_max` | 90.0 | Pitch 최대(deg) |
| `pitch_step` | 10.0 | Pitch 간격(deg) |
| `roll_fixed` | 0.0 | Roll 고정값 |
| `yaw_fixed` | 0.0 | Yaw 고정값 |

`pitch_min`~`pitch_max`를 `pitch_step` 간격으로(끝값 포함) 생성 (`AngleSourceParser.py:210-233`).
기본값 기준 19개.

#### (4) `rolling_sweep` — Roll 스윕 (Pitch 고정)

| 키 | 기본값 | 설명 |
|---|---|---|
| `roll_min` | -180.0 | Roll 최소(deg) |
| `roll_max` | 170.0 | Roll 최대(deg) |
| `roll_step` | 10.0 | Roll 간격(deg) |
| `pitch_fixed` | 0.0 | Pitch 고정값 |
| `yaw_fixed` | 0.0 | Yaw 고정값 |

기본값 기준 36개 (`AngleSourceParser.py:236-259`).

#### (5) `case_txt_file` — 표준 Case txt 파일

| 키 | 기본값 | 설명 |
|---|---|---|
| `file_path` | (필수) | Case txt 파일 경로 |
| `selected_indices` | `None` | 0-based 인덱스 리스트로 부분 선택 (`AngleSourceParser.py:279-286`) |

txt 파일 포맷은 `*Mode`, `EulerRolling/Pitching/Yawing`, 콤마 구분 case 이름 등으로 구성
(`Runner/CaseTxtParser.py`, 예: `Examples/HWWarrantyDropTest/FullAngleDrop/26case_6F12E8C_cuboid.txt`).
동봉 파일 예: `fibonacci_10deg_413cases.txt`, `fibonacci_40deg_26cases.txt`,
`pitching_10deg_19cases.txt`, `rolling_10deg_36cases.txt` 등.

#### (6) `explicit` — 각도 직접 열거

전각도 낙하 결과에서 뽑은 **취약 각도만 다시 돌릴 때** 쓴다.

| 키 | 기본값 | 설명 |
|---|---|---|
| `angles` | — | `[{"name":..., "roll":..., "pitch":..., "yaw":...}, ...]` |
| `file` | — | JSON 파일 경로. 내용 `{"angles": [...]}`. `angles` 와 배타 |

- `roll`, `pitch` 는 필수. `yaw` 생략 시 0.0, `name` 생략 시 `A0001` 자동.
- `angles` 와 `file` 을 동시에 주면 어느 쪽이 유효한지 모호하므로 `ValueError`.
- 이름 중복도 `ValueError` (결과 디렉토리 충돌 방지).
- `file` 은 scenario.json 위치 기준 상대경로 허용.
- 파일은 `KooChainRun harvest` 가 만들어 준다 (§2-G).

```json
"angle_source": { "source_type": "explicit", "explicit": { "file": "risk_angles.json" } }
```

### 2-B. 각도 산포 DOE (`tolerance`, `Runner/ToleranceDOEGenerator.py`)

각도 소스로 만든 base 각도에 ±산포를 더해 DOE 샘플을 만든다.
`tolerance` 키가 있으면 적용 (`CumulativeDesigner.py:270-273`).

| 키 | 기본값 | 설명 |
|---|---|---|
| `roll` / `pitch` / `yaw` | 없음 | 각 축 산포. `{ "tolerance": 2.0 }`(±2°) 또는 `{ "min": -2, "max": 2 }` (비대칭) |
| `doe_type` | `"lhs"` | `lhs` / `grid` / `random` |
| `doe_count` | 10 | LHS/Random: **base 각도 1개당** 샘플 수. Grid: **축당 분할 수 → base 당 `doe_count³`** |
| `include_nominal` | `false` | base 각도 자체(무섭동)를 케이스로 **추가**. base 당 `doe_count + 1` |
| `seed` | 42 | 난수 시드. **미지정도 고정값** — 같은 scenario.json 은 항상 같은 산포를 낸다 |

세 축 모두 미설정이면 산포 없이 원본 그대로 반환한다.

`include_nominal` 은 산포 n 개에 **더해서** 1 개를 붙인다(n 을 깎지 않는다).
LHS 층화를 n 구간 그대로 두기 위해서다. 케이스 이름은 `{base}_DOE000_NOM`
이고 doe_index 는 그 base 그룹의 맨 앞에 온다.

> 🔴 **재현성 (2026-08-06 수정)**: 이전에는 시드 없이 전역 `random` 을 써서
> **같은 scenario.json 을 두 번 `prepare` 하면 다른 각도가 나왔다.** 결과 비교도
> 재실행도 불가능한 상태였다. 지금은 `seed` 미지정도 고정값(42)을 쓰는 로컬
> 난수기라 항상 같은 산포가 나온다. 다른 세트가 필요하면 `seed` 값을 바꾸면
> 되고, 그 값으로 다시 고정된다. `grid` 는 난수를 안 쓰므로 원래 결정적이었다.
> **v83 미만에서 `tolerance` 를 돌렸다면 각도가 그때그때 달랐다는 점에 유의할 것.**

**총 케이스 수 = base 각도 수 × (base 당 샘플 수).**
`only: ["C1","F5"]` + `doe_count: 10` → 20 케이스, 꼭짓점 8개 + `doe_count: 10` → 80 케이스.
`grid` 는 `doe_count: 3` 이 base 당 27개이므로 꼭짓점 8개면 216 케이스가 된다.

#### 특정 자세 집중 조사 (표준 사용법)

`cuboid_geometry.only` 로 기준 자세를 찍고 그 주변을 LHS 로 훑는다.

```json
"angle_source": {
  "source_type": "cuboid_geometry",
  "cuboid_geometry": { "only": ["C1"] }
},
"tolerance": {
  "roll":  { "tolerance": 5.0 },
  "pitch": { "tolerance": 5.0 },
  "yaw":   { "tolerance": 5.0 },
  "doe_type": "lhs",
  "doe_count": 20
}
```

→ C1 꼭짓점 ±5° 안에서 20 케이스. 실측 시 중심으로부터 실제 낙하 방향 편차는
0.3°~5.7°(평균 3.3°)로 고르게 퍼진다. **극(F5_Top) 기준에서도 왜곡이 없다** —
`tolerance` 는 기준 각도에 델타를 더하는 방식이라 2-A(2)의 lat/lon 쏠림 문제와 무관하다.

> 🔴 **과거 결함 (2026-08-05 수정)**: `doe_index` 를 base 각도마다 1부터 다시 매겨 충돌했고,
> `doe_count = len(set(doe_index))` 가 base 수만큼 축소되어 러너의 `range(1, doe_count+1)`
> 루프에서 **대부분의 케이스가 실행되지 않았다**(꼭짓점 8개 × 10 = 80 → `doe_count` 10 기록,
> 70개 유실). 에러 없이 조용히 줄어드는 형태였다.
> 현재는 base 를 관통하는 전역 통번호를 쓴다. **base 각도 2개 이상 + `tolerance`** 조합을
> 이 수정 이전 버전(v80 미만)에서 돌렸다면 케이스 수를 다시 확인할 것.

#### 6면 낙하 ± n° 산포 (정각도 포함)

정면 6방향 각각에 대해 주변 ±5° 를 LHS 로 훑되, **기준이 되는 정각도도 함께** 던진다.

```json
"angle_source": {
  "source_type": "cuboid_geometry",
  "cuboid_geometry": { "only": ["F1", "F2", "F3", "F4", "F5", "F6"] }
},
"tolerance": {
  "roll":  { "tolerance": 5.0 },
  "pitch": { "tolerance": 5.0 },
  "doe_type": "lhs",
  "doe_count": 10,
  "include_nominal": true
}
```

→ 면당 11 케이스(정각도 1 + LHS 10) × 6면 = **66 케이스**.
정각도는 `F1_Back_DOE000_NOM` 처럼 이름에 `_NOM` 이 붙고 값은 base 그대로다
(F1=0/0, F2=180/0, F3=0/-90, F4=0/90, F5=90/0, F6=-90/0).

`only` 를 바꾸면 그대로 다른 기준에도 쓸 수 있다 — 꼭짓점 8개, 26방향 전체,
또는 `angle_source.source_type="explicit"` 으로 물린 **harvest 취약각도 주변**
정밀 조사에도 동일하게 동작한다.

### 2-C. 각도 믹싱 전략 (`cumulative.angle_mixing`, `Runner/AngleMixingStrategy.py`)

누적 Step별로 base 각도 목록에서 어떤 각도를 쓸지 결정.
파싱: `CumulativeDesigner._parse_mixing_config` (`CumulativeDesigner.py:627-642`).

| 키 | 기본값 | 설명 |
|---|---|---|
| `strategy` | `"same_angle"` | `same_angle` / `cyclic` / `random` / `opposite` / `custom_mapping` (`MixingStrategy`, `AngleMixingStrategy.py:30-36`) |
| `cyclic_offset` | 1 | cyclic 전략: Step마다 인덱스 증가량 |
| `random_seed` | `None` | random 전략: 재현용 시드 |
| `custom_mapping` | `None` | custom_mapping 전략: `{Step(1-based): 각도인덱스(0-based)}` |

- `opposite`: Step 짝수마다 Roll+180°, Pitch 반전한 대칭 각도 사용 (`AngleMixingStrategy.py:144-200`)

### 2-D. 위치 소스 — 시스템 (A) `position_source` (`Runner/ImpactPositionSource.py`)

공통: `position_source.source_type` (기본 `grid_nxm`, `ImpactPositionSource.py:218`).
`bbox` 미지정 + `model_file` 있으면 .k의 `*NODE`에서 X-Y bbox 자동 계산
(`parse_bbox_from_k_file`, `ImpactPositionSource.py:24-76`, 220-228).

| 타입 | 키 | 기본값 | 설명 |
|---|---|---|---|
| `grid_nxm` | `nx` | 5 | X축 포인트 수 |
| | `ny` | 5 | Y축 포인트 수 |
| | `bbox` | (자동) | `[xmin, ymin, xmax, ymax]` |
| `grid_spacing` | `spacing_x` | (필수) | X 간격 |
| | `spacing_y` | (필수) | Y 간격 |
| | `bbox` | (자동) | `[xmin, ymin, xmax, ymax]` |
| `manual` | `positions` | (필수) | 항목은 `[x, y]` 또는 `{"name":..., "x":..., "y":...}` |
| | `file` | — | JSON 파일 경로. 내용 `{"positions": [...]}`. `positions` 와 배타 |

`manual` 항목에 `name` 을 주면 결과 디렉토리 이름에 그대로 쓰인다. 취약 위치를
재조사할 때 원래 위치명(`P_003_005`)을 유지할 수 있다. 이름이 겹치면 결과가
덮어써지므로 `ValueError` 로 막는다. 경로는 scenario.json 위치 기준 상대경로 허용.

### 2-E. 위치 소스 — 시스템 (B) `locations` (`Runner/DropWeightImpactWorkflow.py`)

낙하추 충격(drop_weight_impact) 전용. `simulation_params.locations.mode`로 모드 선택
(기본 `grid`, `DropWeightImpactWorkflow.py:370`).
`x_range`/`y_range` 미지정 시 모델 bbox × `margin`으로 자동 계산
(`DropWeightImpactWorkflow.py:377-389`).

| 모드 | 키 | 기본값 | 설명 |
|---|---|---|---|
| 공통 | `x_range` / `y_range` | (자동) | `[min, max]` |
| | `margin` | 0.9 | bbox 자동계산 시 축소 비율 |
| `grid` | `x_count` / `y_count` | 7 / 13 | 격자 분할 수 |
| | `spacing` | 0 | >0이면 `spacing`(mm)으로 `x_count`/`y_count` 자동 산정 (`line 400-404`) |
| `list` | `points` | `[]` | `[[x,y],...]` 명시 좌표 |
| `part_center` | `pids` (또는 `pid`) | `[]` | 대상 파트 ID. 각 파트 bbox 중심 기준 격자 |
| | `spacing` | 5.0 | 격자 간격(mm) |
| | `layers` | 2 | 중심에서 확장 단수 → 파트당 `(2·layers+1)²` 개 (`line 451`) |
| `lhs` | `n_samples` | 50 | Latin Hypercube 샘플 수 (scipy `qmc.LatinHypercube`, 없으면 `np.random` fallback) |

### 2-F. 파트 위치 변경 DOE (`part_doe`, `Runner/PartMoveDOE.py`)

특정 파트의 장착 위치를 흔드는 DOE 축. **조건 축(각도/위치)과 직교**하며 곱해진다.
`scenarios[N]` 안, `angle_source`/`position_source`/`tolerance` 와 형제.

```text
doe_count = (조건 수) × (파트이동 케이스 수)
condition = "{조건명}__{이동명}"        예: C1_Back_Right_Top__M0003
```

블록이 없거나 `enabled: false` 면 이동 축이 사라져 **기존 출력과 바이트 동일**하다.

| 키 | 기본값 | 설명 |
|---|---|---|
| `enabled` | `true` | 블록을 썼다면 쓰겠다는 뜻 |
| `apply_step` | `1` | 이동을 적용할 스텝 번호 |
| `sampling.method` | `lhs` | `lhs` \| `grid` \| `explicit` |
| `sampling.num_samples` | 10 | (`lhs`) 샘플 수 |
| `sampling.seed` | 42 | (`lhs`) 시드. **미지정도 고정값** — 같은 설정은 항상 같은 이동량 |
| `sampling.nx`/`ny`/`nz` | 1 | (`grid`) 축별 분할 수. 총 조합 = nx·ny·nz |
| `parts` | (필수) | (`lhs`/`grid`) `[{pid, dx, dy, dz}, ...]` |
| `cases` | (필수) | (`explicit`) `[{name, moves:[{pid,dx,dy,dz}]}, ...]` |
| `file` | — | 위 설정 전체를 담은 JSON 경로 |

- `dx`/`dy`/`dz` 는 `[최소, 최대]` 또는 스칼라(고정 이동). **생략하면 그 축은 0**.
- 좌표계는 모델 글로벌 XYZ, 단위는 모델 단위 그대로 (환산 없음).
- `grid` 는 전 파트가 같은 격자 인덱스를 공유한다. 파트마다 독립 격자를 쓰면
  조합수가 `(nx·ny·nz)^파트수` 로 폭발하기 때문이며, "여러 파트가 함께 어긋난다"는
  공차 해석 의미와도 맞다.
- 검증 실패는 조용히 넘어가지 않고 `ValueError`. PID 중복, 최소>최대, 전 축 생략,
  빈 `parts`/`cases`, 알 수 없는 `method` 모두 해당.

**🔴 `apply_step` 이 1인 이유.** 누적 step≥2 는 이전 스텝의 `*_dti.k`(이미 이동된
변형 형상)를 입력으로 쓴다. 매 스텝 적용하면 step N 에서 N배 이동한다.

**⚠️ `tolerance` 와 병용하면 3중 곱**이다 (조건 × 산포 × 이동).
26방향 × 10산포 × 20이동 = 5200 케이스. prepare 시 총 케이스 수가 로그로
찍히고 1000건 초과 시 경고한다.

### 2-G. 취약조건 수확 (`KooChainRun harvest`, `Runner/RiskHarvester.py`)

완료된 전각도 낙하/전위치 충격 결과에서 위험도 상위 조건을 뽑아, §2-A(6) 과
§2-D 가 물릴 JSON 을 만든다.

```bash
KooChainRun harvest <test_dir> --top 10 [--hot-only] [-o risk_angles.json]
```

| 인자 | 기본값 | 설명 |
|---|---|---|
| `test_dir` | `.` | 통합 리포트 또는 `result.json` 이 있는 디렉토리 |
| `-o` / `--out` | `test_dir/risk_<kind>.json` | 출력 경로 |
| `--top` | (전체) | 위험도 상위 N개 |
| `--hot-only` | off | 핫 판정된 조건만 |
| `--z-thr` | 1.5 | 핫 판정 z-score 임계 |
| `--yield-factor` | 1.0 | 핫 판정 yield 절대비 임계 |
| `--parts` | (전 파트) | 이 파트 기준으로만 위험도 계산 (`12,15`) |
| `--from-scenario` | — | scenario.json 의 `part_doe` 에서 파트 자동 추출 |

**🔴 파트이동 DOE 를 할 거면 `--parts` 를 쓰는 게 맞다.** 기본 동작은
`max_p`(전 파트 최대)라 **옮길 파트와 무관하게 뜨거운 조건**이 섞여 나온다.
옮길 파트로 필터하면 μ·s 도 그 파트 분포로 계산돼 선정이 정확해진다.

```bash
# 옮길 파트를 손으로 지정
KooChainRun harvest <dir> --parts 12,15 --top 10

# scenario.json 의 part_doe 에서 자동 추출 (손으로 PID 옮겨 적지 않음)
KooChainRun harvest <dir> --from-scenario scenario.json --top 10
```

지정한 파트가 리포트에 하나도 없으면 조용히 0건이 되지 않고 `ValueError` 로
막는다("위험한 조건이 없다"로 오독되는 것을 방지). 일부만 없으면 경고 후 제외.

**⚠️ 절대 기준(항복비)은 통합 리포트 경로에서 비작동이다.** `sphere_report.json`
과 `impact_report.json` 이 파트별 항복강도를 직렬화하지 않아 `a_p = 0` 이 되고
상대 기준(z-score)만 판정에 쓰인다. `result.json` 스캔 폴백 경로는 `stress_limit`
을 담고 있어 두 기준 모두 작동한다.

소스는 자동 판별한다.

1. `sphere_report.json` (전각도 낙하 통합) → `{"angles": [...]}`
2. `impact_report.json` (전위치 충격 통합) → `{"positions": [...]}`
3. 개별 `result.json` 스캔 (통합 리포트 부재 시 폴백, 각도 결과만)

위험도는 `AdaptiveOrientation.compute_risk` 를 그대로 쓴다
(per-part z-score 상대 + yield 절대비 병행).

**scenario.json 안에서 자동 해석(`from_run`)하지 않는 이유.** 수백 잡을 던지기
전에 뽑힌 조건을 사람이 확인해야 하고, 이전 run 디렉토리가 바뀌면 같은
scenario.json 이 다른 결과를 내 재현성이 깨진다. 파일로 분리하면 목록을 손으로
추가·제외할 수도 있다.

---

## 3. 사용 예제

### 3-1. 각도 소스 + 믹싱 (누적 낙하) — `Examples/HWWarrantyDropTest/example_user_config.json` 발췌

```json
{ "angle_source": { "source_type": "cuboid_geometry",
    "cuboid_geometry": { "include_faces": true, "include_edges": true, "include_corners": true } },
  "cumulative": { "num_steps": 3, "mode_sequence": ["DROP","DROP","DROP"],
    "base_angle_index": 0, "angle_mixing": { "strategy": "same_angle" } } }
```

```json
{ "angle_source": { "source_type": "fibonacci_lattice",
    "fibonacci_lattice": { "num_points": 26 } },
  "cumulative": { "num_steps": 5, "mode_sequence": ["DROP","DROP","DROP","DROP","DROP"],
    "base_angle_index": 0, "angle_mixing": { "strategy": "cyclic", "cyclic_offset": 1 } } }
```

```json
{ "angle_source": { "source_type": "case_txt_file",
    "case_txt_file": { "file_path": ".../FullAngleDrop/26case_6F12E8C_cuboid.txt" } },
  "cumulative": { "num_steps": 4, "mode_sequence": ["DROP","DROP","DROP","DROP"],
    "base_angle_index": 0, "angle_mixing": { "strategy": "opposite" } } }
```

### 3-2. 각도 산포 DOE (`tolerance`) — 코드 기준 스키마

```json
"tolerance": {
  "roll":  { "tolerance": 2.0 },
  "pitch": { "tolerance": 2.0 },
  "yaw":   { "min": -1.0, "max": 1.0 },
  "doe_type": "lhs",
  "doe_count": 10
}
```

### 3-3. 위치 소스 (B) — `Examples/drop_weight_impact/` 실제 파일 발췌

`scenario_grid_auto.json` (grid, 자동 범위):
```json
"locations": { "mode": "grid", "x_count": 5, "y_count": 5, "margin": 0.9 }
```

`scenario_grid_spacing.json` (간격 지정 grid):
```json
"locations": { "mode": "grid", "spacing": 10.0, "margin": 0.85 }
```

`scenario_lhs.json` (LHS 100개):
```json
"locations": { "mode": "lhs", "n_samples": 100, "margin": 0.9 }
```

`scenario_list.json` (수동 좌표):
```json
"locations": { "mode": "list",
  "points": [[0,0],[20,0],[-20,0],[0,50],[0,-50],[20,50],[-20,-50]] }
```

`scenario_part_center.json` (파트 중심 격자, pids=[4,5,6], 5×5/파트):
```json
"locations": { "mode": "part_center", "pids": [4,5,6], "spacing": 3.0, "layers": 2 }
```

### 3-4. 위치 소스 (A) — `position_source` (코드 docstring 기준)

```json
"position_source": {
  "source_type": "grid_nxm",
  "grid_nxm": { "nx": 3, "ny": 3, "bbox": [0,0,100,100] }
}
```

---

### 3-5. 취약조건 × 파트이동 DOE — 전체 워크플로우

1단계 — 전각도 낙하를 돌리고 후처리까지 끝낸다 (평소대로).

2단계 — 취약 각도를 뽑는다.

```bash
KooChainRun harvest /data/koopark/Test_FullAngle --top 10 -o risk_angles.json
```

```text
전체 각도 : 500건 (핫 23건)
선별     : 10건 (위험도 내림차순)
  [HOT] risk=  2.834  Run_147   roll= -60.00 pitch=  35.00  P2,P5
  ...
✅ 방출: risk_angles.json  (10건)
```

3단계 — 뽑힌 각도 × 파트이동으로 새 시나리오를 만든다.

```json
{
  "project": { "name": "RISK_PARTDOE", "model_file": "Model.k", "output_dir": "out" },
  "scenarios": [{
    "name": "RiskAngleXPartMove",
    "angle_source": {
      "source_type": "explicit",
      "explicit": { "file": "risk_angles.json" }
    },
    "part_doe": {
      "enabled": true,
      "apply_step": 1,
      "sampling": { "method": "lhs", "num_samples": 20, "seed": 42 },
      "parts": [
        { "pid": 12, "dx": [-0.5, 0.5], "dy": [-0.3, 0.3] },
        { "pid": 15, "dz": [-0.1, 0.1] }
      ]
    },
    "cumulative": { "num_steps": 1, "mode_sequence": ["DROP"] }
  }]
}
```

→ 10 각도 × 20 이동 = **200 케이스**. `condition` 은 `Run_147__M0007` 형태.

4단계 — 평소대로 돌린다.

```bash
KooChainRun prepare scenario.json && KooChainRun submit
```

전위치 부분충격도 동일하다. 2단계에서 `impact_report.json` 이 잡히면
`{"positions": [...]}` 가 나오고, 3단계에서 `angle_source` 대신
`position_source.manual.file` 에 물리면 된다.

생성되는 KMM 옵션 txt 는 다음과 같이 이동이 먼저 오고 낙하가 뒤따른다.

```text
*Mode
PART_TRANSLATE,1
DROP_ATTITUDE,2
**PartTranslate,1
Translate,12,0.3,-0.1,0.0
Translate,15,0.0,0.0,0.05
**EndPartTranslate
**DropAttitude,2
...
```

---

## 4. 동작 원리 (코드 근거)

### 각도 소스
- 디스패치: `parse_angle_source` (`AngleSourceParser.py:293-348`)가 `source_type`별 파서 호출.
- `cuboid_geometry`: 모듈 상수 `CUBOID_FACES`/`CUBOID_EDGES`/`CUBOID_CORNERS` 에
  (Roll,Pitch,Yaw) 하드코딩. `only` 가 있으면 짧은 코드/전체 이름을 대문자 키로 정규화해
  조회하고(미매칭은 `ValueError`) 그것만 반환, 없으면 포함 플래그에 따라 합침.
- `fibonacci_lattice`: 황금각(`golden_angle = π(3−√5)`)으로 구면 균등점 (x,y,z) 생성.
  - **`physical`(기본)**: `_physical_lattice` — 후보를 `_dir_to_euler` 로 정규형 Euler 로 바꾼다.
    거리는 항상 `_physical_drop_dir`(DropAttitude 회전으로 얻는 실제 낙하 방향) 사이 각거리로 잰다.
  - `latlon`(명시 시): 구 경로 — (x,y,z)를 위/경도 → Euler 로 직접 변환. 파라미터 공간 균등.
  - `principal_directions`: 표준 시드를 물리 방향 기준으로 중복 제거(1° 이내)한 뒤,
    정규 N세트에 `_remove_nearest` 를 적용해 시드 개수만큼 제거하고 남은 것으로 채운다.
  - `previous_stages`: `_staged_lattice` — 같은 설정에 `num_points` 만 바꿔 각 단계를 재현하며
    누적하고, 마지막에 이번 N세트에서 누적분 최근접을 제거해 신규분만 방출한다.
  - `_remove_nearest(cands, prev, k)`: `prev` 를 순서대로 훑으며 각자 가장 가까운 미제거 후보를
    하나씩 가져가 정확히 `k` 개를 제거한다. O(P·N) 시간 / **O(N) 메모리**.
    전역 그리디 매칭과 품질이 같음을 실측 확인(누적 500 기준 둘 다 최소 간격 4.59°)했고,
    메모리가 선형이라 큰 N 에서도 안전해 이쪽을 택했다.
  - 이름: 채움/일반 점은 `P0001…`, 표준 시드는 원래 이름(`F1_Back` 등)을 유지한다.
- `pitching_sweep`/`rolling_sweep`: `while` 루프로 min→max를 step 간격 누적, `+1e-6` 오차 허용으로
  끝값 포함 (`:227`, `:253`).
- `case_txt_file`: `CaseTxtParser.parse_case_txt_file`로 전체 파싱 후 `selected_indices`로 부분 선택
  (`:262-290`). 범위 초과 인덱스는 `ValueError`.

### 산포 DOE
- 진입점 `apply_tolerance_doe` (`ToleranceDOEGenerator.py:313-351`):
  산포 없으면 원본 반환, 있으면 `doe_type`별 분기.
- LHS: 각 변수를 `n_samples` 구간으로 나눠 구간별 1점씩 무작위 추출 후 셔플,
  [0,1]→실제 범위 매핑 (`:133-162`). `random` 모듈 사용(시드 미고정 → "확인 필요" 참고).
- Grid: 각 축을 `np.linspace(base+min, base+max, doe_count)`로 분할, 3중 곱집합 →
  base 당 `doe_count³`.
- 세 방식 모두 `doe_index` 를 **base 각도를 관통하는 전역 통번호**(`doe_seq`)로 매긴다.
  케이스 이름의 `_DOE###` 접미어는 base 내 순번을 유지한다(가독성).
  `CumulativeDesigner` 의 `doe_count = len(set(doe_index))` 가 총 케이스 수와 일치해야
  러너의 `range(1, doe_count+1)` 루프가 전부 실행한다.
- Random: 각 축 범위에서 `random.uniform` (`:246-310`).

### 믹싱
- `generate_cumulative_angle_sequence` (`AngleMixingStrategy.py:241-284`)가 전략별 분기.
- `cyclic`: `idx = (start + step*offset) % len` (`:104-108`).
- `opposite`: Roll+180°를 [-180,180]로 정규화, Pitch 부호 반전, 짝/홀 Step 교대 (`:182-200`).
- `custom_mapping`: 1-based Step→0-based 인덱스. 누락 Step은 `ValueError` (`:228-238`).

### 위치 — 시스템 (A)
- `parse_position_source` (`ImpactPositionSource.py:195-243`)가 `source_type` 분기.
- bbox 자동계산: `*NODE` 고정폭(X=8:24, Y=24:40)에서 X/Y min·max 스캔
  (`parse_bbox_from_k_file`, `:24-76`).
- `grid_nxm`: `nx==1`/`ny==1`이면 중앙값, 아니면 `min + i·(max-min)/(n-1)` (`:110-123`).
- `grid_spacing`: `while`로 spacing 누적, `+1e-9` 오차 허용 (`:152-167`).

### 위치 — 시스템 (B)
- `_generate_impact_locations` (`DropWeightImpactWorkflow.py:368-471`)가 `mode` 분기.
- bbox 자동: `_parse_bbox_from_kfile`로 6축 bbox, 중심±(반폭·margin) (`:377-389`).
- `grid`: `spacing>0`이면 `int((max-min)/spacing)+1`로 count 환산 후 `np.linspace` 곱집합
  (`:396-413`).
- `part_center`: `_parse_part_centers_from_kfile` (`:254-365`)로 `*ELEMENT_SOLID`(2줄 1세트)/
  `*ELEMENT_SHELL`에서 PID별 노드 수집 → bbox 중심. `-layers..layers` 격자, 좌표 중복 제거
  (`:437-453`).
- `lhs`: `scipy.stats.qmc.LatinHypercube(d=2)`; ImportError 시 `np.random.rand` fallback,
  [0,1]→`x_range/y_range` 매핑 (`:456-467`).
- 미지원 mode → 경고 후 `[0.0],[0.0]` 반환 (`:469-471`).

---

## 5. 주의사항 · 한계

- **두 위치 시스템은 호환되지 않는다.** `position_source`(A)는 누적 낙하 설계
  (`CumulativeDesigner`)에서, `locations`(B)는 낙하추 충격 워크플로우에서만 동작한다.
  키 이름·모드 이름이 다르므로 모드(`mode`)에 맞는 시스템을 써야 한다.
- **Grid DOE 폭증**: `tolerance.doe_type="grid"`는 `doe_count`가 축당 분할 수라
  **base 당** `doe_count³` 케이스가 된다(예: 5 → 125). base 각도가 여러 개면 그만큼 곱해진다.
  `lhs`/`random`은 base 당 `doe_count` 개.
- **각도 샘플링 기본 공간이 `physical` 로 바뀌었다(2026-08-05).** `sampling_space` 미지정
  프로젝트는 각도 집합이 이전과 달라진다. 과거 결과와 각도를 맞춰야 하면 `"latlon"` 을 명시할 것.
- **`previous_stages` 는 실제로 돌린 단계를 빠짐없이 적어야 한다.** 누락 시 재현이 어긋나
  중복 각도가 섞인다(자동 검출 불가, 생성 로그로만 확인).
- **LHS 재현성**: `ToleranceDOEGenerator`의 LHS/Random은 `random` 모듈을 시드 고정 없이 사용한다.
  매 실행 결과가 달라질 수 있음 — 재현 필요 시 "확인 필요"(외부에서 시드 설정 경로 미확인).
- **bbox 자동계산은 X-Y 평면 기준**(낙하/충격면이 XY). 모델 좌표계가 다르면 위치가 어긋날 수 있다.
- **`part_center`는 .k 파서가 고정폭/공백분리 양쪽을 시도**하지만, 비표준 포맷이나 PID 노드 미발견 시
  경고만 출력하고 해당 파트를 건너뛴다(`DropWeightImpactWorkflow.py:353,430`).
- **`fibonacci_lattice.angle_spacing`** dataclass 필드는 존재하나 파서가 사용하지 않는다.
  포인트 수는 `num_points`/`num_directions`로만 제어됨 — angle_spacing 동작은 "확인 필요".
- `pitching_sweep`/`rolling_sweep`/`grid_spacing`은 부동소수점 누적 합산이라 경계 근처 개수가
  step/spacing 값에 민감할 수 있다(코드에 `1e-6`/`1e-9` 허용오차 있음).

---

## 6. 개발 현황

**구현됨** (근거: 아래 파일에 파서/생성기 본체와 디스패처가 존재하고, `Examples/`에 실제 동작
scenario.json 파일이 동봉됨).

- 각도 소스 5종: `Runner/AngleSourceParser.py` (cuboid/fibonacci/pitching/rolling/case_txt) +
  스키마 매핑 `Runner/CumulativeDesigner.py`.
- 각도 소스 확장(2026-08): `cuboid_geometry.only`(특정 자세 선택),
  `fibonacci_lattice` 의 `sampling_space`(기본 physical) / `principal_directions`(표준 시드 +
  최근접 제거 채움) / `previous_stages`(단계별 확장).
- 산포 DOE 3종: `Runner/ToleranceDOEGenerator.py` (lhs/grid/random) +
  매핑 `CumulativeDesigner.py:571-608`.
- 믹싱 5종: `Runner/AngleMixingStrategy.py` + 매핑 `CumulativeDesigner.py:627-642`.
- 위치 (A) 3종: `Runner/ImpactPositionSource.py` (grid_nxm/grid_spacing/manual), 사용처
  `CumulativeDesigner.py:362-370`.
- 위치 (B) 4종: `Runner/DropWeightImpactWorkflow.py` (grid/list/part_center/lhs),
  실제 예제 `Examples/drop_weight_impact/scenario_{grid_auto,grid_spacing,lhs,list,part_center}.json`.

- 취약조건 열거(2026-08): `angle_source.source_type="explicit"`,
  `position_source.manual` 의 dict/`file` 수용 — `AngleSourceParser.parse_explicit_angles`,
  `ImpactPositionSource.parse_manual`.
- 파트이동 DOE(2026-08): `Runner/PartMoveDOE.py` (lhs/grid/explicit), Designer 곱셈,
  `doe_part_moves` 카탈로그, Runner 의 `PART_TRANSLATE` 블록 삽입
  (`StepConfigBuilder.build_part_translate_block`), KMM `PART_TRANSLATE` 모드.
- 취약조건 수확(2026-08): `Runner/RiskHarvester.py` + `KooChainRun harvest`.

**수정 이력**:
- 2026-08-05 `tolerance` 의 `doe_index` 가 base 각도마다 재시작해 충돌 → 대부분의 케이스가
  실행되지 않던 결함 수정(전역 통번호). base 2개 이상 + tolerance 조합에만 해당.
- 2026-08-05 `tolerance` 의 `doe_index` 가 1-based 라 `doe_angles` 키가 2..N+1 이 되던
  off-by-one 수정. DOE 1 이 각도 조회에 실패해 `_condition_to_euler` 폴백으로 떨어지고
  DOE N+1 은 실행되지 않았다.
- 2026-08-05 각 DOE 고유 각도(tolerance 산포)가 버려지고 base 그룹 대표 각도로 덮이던
  결함 수정. 실측 18케이스 → 고유 각도 6개, 13건이 첫 base 각도 중복이었다.
  자기 각도를 자기 base 자리에 주입하도록 변경 → 18/18 고유.
- 2026-08-05 `sampling_space` 기본값 `latlon` → `physical`.

**부분구현/확인 필요**:
- `fibonacci_lattice.angle_spacing` (정의만 있고 미사용).
- LHS/Random DOE 시드 고정 경로(재현성).
- `position_source`(A)는 코드/테스트 블록 기준 검증, `Examples/`에 단독 scenario.json 동봉 여부
  미확인(주로 `locations`(B) 예제만 확인됨).
