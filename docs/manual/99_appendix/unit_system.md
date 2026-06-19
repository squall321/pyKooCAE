# 단위계 (ton-mm-s)

## 1. 목적/개요

pyKooCAE의 LS-DYNA 해석은 **ton-mm-s 단위계**(LS-DYNA 표준 `[tonne, mm, s, MPa]`)를 전제로 한다.

핵심 원칙: **KooMeshModifier / Runner 는 사용자 입력값을 단위 변환 없이 그대로 LS-DYNA deck(model.k)에 박는다.** 따라서 `scenario.json`에 입력하는 모든 차원량(길이, 밀도, 탄성계수, 시간, 낙하높이 등)은 반드시 ton-mm-s 단위로 적어야 한다. SI(kg, m, Pa)로 입력하면 deck에 SI 숫자가 그대로 들어가 단위가 혼용되고 비현실적인 결과가 나온다.

근거: `Examples/scenario_examples/drop_attitude_example.json:2` — *"KooMeshModifier는 사용자 입력값을 변환 없이 그대로 deck에 박는다. scenario.json 입력값 단위는 반드시 deck (LS-DYNA model.k) 단위계와 일치시켜야 한다."*

### 단위 환산표 (ton-mm-s)

| 물리량 | 단위 | 비고 |
|--------|------|------|
| 길이 (length) | mm | 직경, 높이, 메쉬 크기 등 |
| 질량 (mass) | tonne (= 1000 kg) | |
| 시간 (time) | s | `tFinal`, `dt` |
| 밀도 (ρ, density) | tonne/mm³ | 강철 7.85e-9 |
| 탄성계수 (E, Young's modulus) | MPa (= N/mm²) | 강철 2.0e5 (= 200 GPa) |
| 응력 (stress) | MPa | |
| 힘 (force) | N (= tonne·mm/s²) | |
| 가속도 | mm/s² | |
| 중력가속도 (g) | 9810 mm/s² | = 9.81 m/s² × 1000 |
| 낙하높이 (height) | mm | 자유낙하 속도 계산 입력 |

근거: `Examples/scenario_examples/README.md:17-28`, `drop_attitude_example.json:3`, `impact_example.json:2-4`.

> 환산 직관: SI 밀도 7850 kg/m³ → ton-mm-s 7.85e-9 tonne/mm³ (×1e-12), SI E 200 GPa = 2.0e11 Pa → 2.0e5 MPa (×1e-6).

---

## 2. 입력 옵션·인자 (표)

`scenario.json`의 `simulation_params` 안에서 단위계와 직접 관련된 차원 입력은 다음과 같다.

| 키 | 위치 | 단위 | 설명 | 근거 |
|----|------|------|------|------|
| `height` | DROP: `simulation_params`, IMPACT: `simulation_params.impact` | mm | 자유낙하 높이. `v = √(2·g·h)` 계산 입력 | `drop_attitude_example.json:34`, `impact_example.json:39` |
| `tFinal` | `simulation_params` 또는 `.impact` | s | 해석 종료 시간 | `impact_example.json:45` |
| `dt` | `simulation_params` 또는 `.impact` | s | 출력/타임스텝 간격 | `impact_example.json:46` |
| `density` | `simulation_params` / `.impact` / `.wall` / `cylinder_stages[]` | tonne/mm³ | 재료 밀도 | `drop_attitude_example.json:37`, `impact_example.json:42` |
| `youngs_modulus` | 동상 | MPa | 탄성계수 | `drop_attitude_example.json:38`, `impact_example.json:43` |
| `poisson_ratio` / `poisson` | 동상 | 무차원 | 푸아송비 | `drop_attitude_example.json:39`, `impact_cylinder_8pi.json:45` |
| `dimension` / `diameter` / `outer_diameter` | `.impact`, `cylinder_stages[]` | mm | 충격추 직경/외경 | `impact_example.json:38`, `impact_cylinder_8pi.json:42-44` |
| `mesh_size` | `.impact` | mm | 메쉬 크기 | `impact_example.json:40` |
| `offset_distance` | `.impact` | mm | 충격추-대상 초기 간극 | `impact_example.json:47` |
| `size` (drop_surface) | `simulation_params.drop_surface` | mm | 바닥판 크기 [x,y,z] | `drop_attitude_example.json:42` |
| `base_curve.points` (VIBRATION) | `vibration_source.base_curve` | s, (하중단위) | `[시간(s), 진폭]` — Force는 N | `vibration_example.json:49-51` |

> 모든 키는 **입력 단위가 곧 deck 단위**다. 자동 변환·자동 추정은 없다(단, 낙하높이의 g 단위는 4절 참조).

---

## 3. 사용 예제

### 3-1. DROP_ATTITUDE — 강철 기준 (단위 일관 입력)

`Examples/scenario_examples/drop_attitude_example.json:32-46` 발췌:

```json
"simulation_params": {
  "height": 1500,
  "tFinal": 0.005,
  "dt": 1e-06,
  "density": 7.85e-09,
  "youngs_modulus": 2.0e5,
  "poisson_ratio": 0.3,
  "drop_surface": {
    "type": "Plane",
    "size": [300, 300, 20],
    "mesh": [30, 30, 2],
    "deformable_to_rigid": false
  }
}
```

- `height: 1500` → 1500 mm 낙하 (1.5 m)
- `density: 7.85e-09` tonne/mm³, `youngs_modulus: 2.0e5` MPa → 강철 (SUS 계열)

### 3-2. IMPACT — 충격추(Impactor) + 바닥판(Wall)

`Examples/scenario_examples/impact_example.json:34-54` 발췌:

```json
"impact": {
  "type": "Sphere",
  "dimension": 8,
  "height": 500,
  "mesh_size": 1,
  "density": 7.85e-09,
  "youngs_modulus": 2.01e5,
  "poisson_ratio": 0.3,
  "tFinal": 0.001,
  "dt": 1e-06,
  "offset_distance": 0.01
},
"wall": {
  "density": 1.0e-09,
  "youngs_modulus": 1.0e4,
  "poisson_ratio": 0.3
}
```

### 3-3. 3단 실린더 충격추 — SUS + 고무 혼합 (재료값 예)

`Examples/scenario_examples/impact_cylinder_8pi.json:37-62` 발췌 (8파이 ~418g, 목표 400g):

```json
"cylinder_stages": [
  { "role": "front", "diameter": 8, "outer_diameter": 20, "height": 6,
    "density": 1.18e-09, "youngs_modulus": 100.0,    "poisson": 0.49 },
  { "role": "mid",   "diameter": 20, "height": 14,
    "density": 6.57e-09, "youngs_modulus": 207000.0, "poisson": 0.3 },
  { "role": "back",  "diameter": 44.5, "height": 38.003,
    "density": 6.57e-09, "youngs_modulus": 207000.0, "poisson": 0.3 }
]
```

- `front` 단 = **고무 팁**: ρ=1.18e-9 tonne/mm³, E=100 MPa, ν=0.49 (저강성·비압축성에 가까움)
- `mid`/`back` 단 = **SUS(스테인리스)**: ρ=6.57e-9 tonne/mm³, E=207000 MPa (207 GPa)

근거 주석: `impact_cylinder_8pi.json:2` — "고무팁(충돌 거동) + ⌀20 SUS 중간단 + ⌀44.5 SUS 본체".

### 자주 쓰는 재료값 (ton-mm-s)

| 재료 | ρ (tonne/mm³) | E (MPa) | ν | 근거 |
|------|---------------|---------|-----|------|
| 강철 (Steel ref) | 7.85e-9 | 2.0e5 (200 GPa) | 0.3 | `drop_attitude_example.json:3`, `DropWeightImpactWorkflow.py:484-486` |
| SUS (스테인리스) | 6.57e-9 ~ 6.854e-9 | 207000 (207 GPa) | 0.3 | `impact_cylinder_8pi.json:51-53`, `impact_cylinder_15pi.json:43-44` |
| 고무 (rubber, 충격추 팁) | 1.18e-9 | 100 | 0.49 | `impact_cylinder_8pi.json:43-45` |
| Wall (강체 바닥판) | 1.0e-9 | 1.0e4 | 0.3 | `impact_example.json:50-53`, `README.md:28` |

> SUS 밀도가 강철(7.85e-9)보다 작은 6.57e-9로 입력된 것은 해당 시나리오가 **목표 질량(~400g)에 맞춘 등가 밀도**를 쓰기 때문이다(주석 "8파이 ~418g"). 실제 SUS 물성이 아니라 질량 보정값임에 주의.

---

## 4. 동작 원리 (코드 근거)

### 4-1. 자유낙하 속도와 중력 단위 자동 추정

낙하 모드는 입력 `height`로부터 자유낙하 속도 `v = √(2·g·h)`를 계산해 초기속도로 부여한다. 이때 **`height` 값이 100보다 크면 mm 단위(g=9810 mm/s²), 100 이하면 m 단위(g=9.81 m/s²)로 자동 추정**한다.

- DROP_ATTITUDE 경로: `KooDynaAdvancedModification.py:2231-2234`
  ```python
  if height > 100:
      velocity_from_height = [0.0, 0.0, -np.sqrt(2.0*9810.0*height)]
  else:
      velocity_from_height = [0.0, 0.0, -np.sqrt(2.0*9.81*height)]
  ```
- 실린더 충격추 경로(`g_fall`): `KooDynaAdvancedModification.py:3438-3440` 및 동일 패턴 `:3926-3928`
  ```python
  # height>100이면 mm(g=9810 mm/s²), 이하면 m(g=9.81 m/s²) 자동 추정.
  g_fall = 9810.0 if height > 100 else 9.81
  velocity = [Vx, Vy, Vz - np.sqrt(2.0 * g_fall * height)]
  ```
- DropWeightImpactWorkflow (non-cumulative IMPACT 경로): `DropWeightImpactWorkflow.py:490-491` — 여기서는 **항상 g=9810 mm/s² 고정**(추정 없음)
  ```python
  g = 9810.0  # mm/s^2
  vz = -math.sqrt(2.0 * g * imp_height)
  ```

### 4-2. 재료값 deck 기록 (변환 없음 + 기본값 단위)

사용자 입력 density/youngs_modulus는 변환 없이 deck 카드(`*MAT_ELASTIC`, `*MAT_RIGID`)에 기록된다. 입력이 없을 때의 **기본값(default)도 모두 ton-mm-s**로 정의돼 있어, g=9810과 단위 일관성이 유지된다.

- IMPACT default: `DropWeightImpactWorkflow.py:485-486` — `imp_density = ...get("density", 7.85e-9)`, `imp_E = ...get("youngs_modulus", 2.0e5)`, 주석 `:482-484` "Defaults are in the LS-DYNA [tonne, mm, s, MPa] convention ... Steel reference: ρ = 7.85e-9 tonne/mm³, E = 2.0e5 MPa."
- Wall default: `DropWeightImpactWorkflow.py:550-552` — `wall_E ...get("youngs_modulus", 1.0e4)`, `wall_density ...get("density", 1.0e-9)`
- DROP(StepConfigBuilder) default: `StepConfigBuilder.py:44-45` — `density ...get("density", 7.85e-9)`, `youngs_modulus ...get("youngs_modulus", 2.0e5)`, 주석 `:40-41` "Unit system: [tonne, mm, s, MPa] ... Steel ref: ρ=7.85e-9, E=2.0e5."
- Cumulative IMPACT default: `CumulativeScenarioRunner.py:1266-1267` — `DensityImpactor` 기본 7.85e-9, `YoungsModulusImpactor` 기본 2.01e5

---

## 5. 주의사항·한계

- **자동 변환 없음**: scenario.json 입력값은 그대로 deck로 들어간다. SI로 입력하면 단위 혼용이 발생한다(`README.md:30-31`). 입력 전 반드시 ton-mm-s로 환산할 것.
- **g 자동 추정의 경계값 함정**: 낙하높이를 mm로 입력해야 하나, `height ≤ 100`이면 코드가 m로 오인해 g=9.81을 써서 속도가 약 31배 작게 계산된다(√1000). 즉 **100 mm 이하의 짧은 낙하(예: 50 mm)는 의도와 달리 m로 해석**된다 — 이 경계 동작은 `KooDynaAdvancedModification.py:2231`, `:3439`에 명시된 자동 추정 로직의 한계다.
- `DropWeightImpactWorkflow` 경로는 g 추정 없이 **항상 9810 고정**이므로(`:490`), 이 경로에서는 height를 반드시 mm로 입력해야 한다(m 입력 시 속도가 1000배 과다).
- **시나리오의 SUS 밀도는 등가 질량 보정값**일 수 있다(4단원 주석 참조). 실제 SUS 물성(보통 7.9e-9~8.0e-9)과 다를 수 있으므로, 목표 질량 맞춤이 아닌 경우 표준값을 직접 입력할 것.
- **구버전 빌드 silent miss**: 옛 KooChainRun은 IMPACT 키 이름 mismatch로 입력 단위를 무시하고 하드코딩 SI default를 deck에 박는 버그가 있었다(`impact_example.json:5` fix history). 현 빌드에서 deck의 ρ/E가 입력값과 일치하는지 검증 권장(`README.md:62-66`).
- VIBRATION의 `base_curve.points` 진폭 단위는 하중 타입에 따른다(Force=N, Acceleration=mm/s²) — `vibration_example.json:2`.

---

## 6. 개발 현황

**구현됨.**

근거:
- ton-mm-s 단위계 정책 + g=9810 처리: `KooDynaAdvancedModification.py:2231-2234`, `:3438-3440`, `:3926-3928`, `DropWeightImpactWorkflow.py:490-491`.
- ton-mm-s 기본값(강철/Wall): `DropWeightImpactWorkflow.py:482-486, 550-552`, `StepConfigBuilder.py:40-45`, `CumulativeScenarioRunner.py:1266-1267`.
- 검증된 예제 3 mode + 실린더 충격추 2종: `Examples/scenario_examples/*.json` (README.md "2026-06 fix 후 검증된 단위계/키 이름 일관", `README.md:3`).

**확인 필요**: g 단위 자동 추정(`height>100`)은 DROP/실린더 경로에만 있고 `DropWeightImpactWorkflow`(고정 9810)와 동작이 다르다. 두 경로의 height 입력 규약이 통일되어 있는지(또는 통일 계획이 있는지)는 코드 주석만으로는 불명확하다.
