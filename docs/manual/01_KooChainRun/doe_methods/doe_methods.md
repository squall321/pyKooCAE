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

세 옵션 모두 true면 6+12+8 = **26방향** (`AngleSourceParser.py:132-159`).

#### (2) `fibonacci_lattice` — 구면 균등 분포

| 키 | 기본값 | 설명 |
|---|---|---|
| `num_points` | 26 | 생성할 포인트(케이스) 수 |
| `num_directions` | — | `num_points` 별칭 (CumulativeDesigner에서 허용, `CumulativeDesigner.py:522`) |
| `angle_spacing` | `None` | 각도 간격(deg). dataclass에 정의는 있으나 파서에서 사용 안 됨 → "확인 필요" |

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

### 2-B. 각도 산포 DOE (`tolerance`, `Runner/ToleranceDOEGenerator.py`)

각도 소스로 만든 base 각도에 ±산포를 더해 DOE 샘플을 만든다.
`tolerance` 키가 있으면 적용 (`CumulativeDesigner.py:270-273`).

| 키 | 기본값 | 설명 |
|---|---|---|
| `roll` / `pitch` / `yaw` | 없음 | 각 축 산포. `{ "tolerance": 2.0 }`(±2°) 또는 `{ "min": -2, "max": 2 }` (`CumulativeDesigner.py:581-597`) |
| `doe_type` | `"lhs"` | `lhs` / `grid` / `random` (`DOEType`, `ToleranceDOEGenerator.py:34-38`) |
| `doe_count` | 10 | LHS/Random: 샘플 수. **Grid: 축당 분할 수 → 총 `doe_count³`** (`ToleranceDOEGenerator.py:198`, 198-243) |

세 축 모두 미설정이면 산포 없이 원본 그대로(doe_index=0) 반환 (`ToleranceDOEGenerator.py:340-342`).

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
| `manual` | `positions` | (필수) | `[[x1,y1],[x2,y2],...]` |

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

## 4. 동작 원리 (코드 근거)

### 각도 소스
- 디스패치: `parse_angle_source` (`AngleSourceParser.py:293-348`)가 `source_type`별 파서 호출.
- `cuboid_geometry`: 모듈 상수 `CUBOID_FACES`/`CUBOID_EDGES`/`CUBOID_CORNERS`
  (`AngleSourceParser.py:92-125`)에 (Roll,Pitch,Yaw) 하드코딩. 포함 플래그에 따라 합침
  (`:132-159`).
- `fibonacci_lattice`: 황금각(`golden_angle = π(3-√5)`)으로 구면 균등점 (x,y,z) 생성 후
  위/경도 → Euler 변환 (`:179-205`). 이름 `P0001…`.
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
  총 `doe_count³` (`:198-243`).
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
  총 `doe_count³` 케이스가 된다(예: 5 → 125). `lhs`/`random`은 총 `doe_count` 개.
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
  스키마 매핑 `Runner/CumulativeDesigner.py:503-569`.
- 산포 DOE 3종: `Runner/ToleranceDOEGenerator.py` (lhs/grid/random) +
  매핑 `CumulativeDesigner.py:571-608`.
- 믹싱 5종: `Runner/AngleMixingStrategy.py` + 매핑 `CumulativeDesigner.py:627-642`.
- 위치 (A) 3종: `Runner/ImpactPositionSource.py` (grid_nxm/grid_spacing/manual), 사용처
  `CumulativeDesigner.py:362-370`.
- 위치 (B) 4종: `Runner/DropWeightImpactWorkflow.py` (grid/list/part_center/lhs),
  실제 예제 `Examples/drop_weight_impact/scenario_{grid_auto,grid_spacing,lhs,list,part_center}.json`.

**부분구현/확인 필요**:
- `fibonacci_lattice.angle_spacing` (정의만 있고 미사용).
- LHS/Random DOE 시드 고정 경로(재현성).
- `position_source`(A)는 코드/테스트 블록 기준 검증, `Examples/`에 단독 scenario.json 동봉 여부
  미확인(주로 `locations`(B) 예제만 확인됨).
</content>
</invoke>
