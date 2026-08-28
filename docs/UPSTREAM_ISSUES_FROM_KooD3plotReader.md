# pyKooCAE 상류 이슈 보고 — 후처리(KooD3plotReader) 측 검증 결과

작성 2026-08-28 · 보고 주체 KooD3plotReader (후처리) · 대상 pyKooCAE `origin/main` (784e761)

> **B·C 는 본 PR 에서 수정 완료**. A 는 이미 머지돼 있어 조치하지 않았고,
> A-1(재질 키 누락 시 조용한 SI 폴백)만 별건으로 남습니다.

후처리 쪽에서 전각도 낙하 보고서의 각도 규약을 확정·검증하는 과정에서 상류 pyKooCAE
산출물의 문제 두 건을 확인했습니다. 세 번째(단위계)는 **이미 해결돼 있어 PR 대상이 아님**을
같이 기록합니다.

각 항목은 현재 HEAD 코드에서 실재를 확인했고, 실산출 덱으로 영향 범위를 셌으며,
적대적 반증 검증을 통과했습니다.

| # | 항목 | 실재 | 영향 | PR 필요 |
|---|------|------|------|---------|
| A | 단위계 키 mismatch | ❌ 해결됨 (`381ba31`) | 없음 | 아니오 |
| B | 코너 각도 9.74° 오차 + 정의 이중화 | ✅ | 전각도 26케이스 중 8 (30.8%) | **예** |
| C | DropSet 라벨이 전 런 동일 | ✅ | DropSet.json 1,719+ · 표본 캠페인 17/17 | **예** |

---

## A. 단위계 키 mismatch — 이미 해결됨 (조치 불요)

2026-06 자 진단서(후처리 저장소 `docs/pyKooCAE-unit-system-fix.md`)가 지목한
`CumulativeScenarioRunner.py:1227-1229` 의 접미사 없는 `Density/YoungsModulus/PoissonRatio`
키 문제는 **pyKooCAE `381ba31` (2026-06-03, "fix(vibration, units): … IMPACT 단위계
silent miss 해결")** 로 이미 반영돼 있습니다.

현재 코드 (`Runner/CumulativeScenarioRunner.py:1557-1562`)

```
DensityImpactor,{impact_params.get('density', 7.85e-9)}
YoungsModulusImpactor,{impact_params.get('youngs_modulus', 2.01e5)}
PoissonRatioImpactor,{impact_params.get('poisson_ratio', 0.3)}
DensityWall,{wall_params.get('density', 1.0e-9)}
YoungsModulusWall,{wall_params.get('youngs_modulus', 1.0e4)}
PoissonRatioWall,{wall_params.get('poisson_ratio', 0.3)}
```

실덱 확인 — `/data` 전체의 `DropWeightImpactTestSet*.k` 81개 중 75개가 정상
`7.850e-09`(ton-mm-s), `Test_Impact_A` 25 DOE 는 25/25 정상.

**그 진단서를 PR 로 내지 마십시오.** no-op 이거나 충돌합니다.

### A-1. 다만 하나는 살아 있습니다 — 재질 키 누락 시 조용한 SI 폴백

진단서가 "정책상 미적용"으로 닫아 둔 항목이 실제로 재발했습니다.

- `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py:3287, 3295, 3300, 3308`
  이 `EWall=1.0e10 / rhoWall=1000.0 / EImpactor=2.07e11 / rhoImpactor=7800.0` (SI) 로 폴백
- `occProject/Generators/KooMeshModifier.py` 의 DWI 파서 `elif` 체인에 말단 `else` 가 없어
  인식하지 못한 라인이 경고 없이 사라짐

실증: `/data/koopark/Test_dtmin_e2e/out_imp/Run_20260711_091016_89548b/` (2026-07-11,
수정 5주 뒤). 재질 라인이 없는 손작성 `impact_config.txt` 로 돌린 결과 **한 덱 안에서
단위가 섞였습니다.**

| 파트 | 밀도 | 영률 | 단위계 |
|------|------|------|--------|
| 모델 MAT 23–27 | `2.330e-09` | `1.660e+05` | ton-mm-s ✅ |
| ImpactorMaterial MAT 30 | `7.800e+03` | `2.070e+11` | **SI ❌ (10¹² 배)** |
| WallMaterial MAT 31 | `1.000e+03` | `1.000e+10` | **SI ❌** |

Runner 경유 산출물은 정상이므로 시급하지는 않지만, **경고 없이** 12자리 어긋난 덱이
나온다는 점은 남아 있습니다. 최소 조치는 폴백 시 경고 한 줄입니다.

---

## B. cuboid 코너 각도가 참 꼭짓점을 향하지 않음 (+ 정의가 두 곳에 이중화)

### B-1. 문제

`Runner/AngleSourceParser.py:153-162`

```python
CUBOID_CORNERS = {
    "C1_Back_Right_Top":      (45.0,   -45.0, 0.0),
    ...
    "C8_Front_Left_Bottom":   (-135.0, -45.0, 0.0),
}
```

roll 45°/135° 는 정육면체 **면의 대각선** 방향이지 **꼭짓점** 방향이 아닙니다.
꼭짓점을 향하려면 `roll = asin(1/√3) = 35.264390°` 여야 합니다.

### B-2. 수학적 근거

덱 생성기가 쓰는 회전은
`occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py:2222-2251` 에서
`Rx=-roll, Ry=-pitch, Rz=-yaw` 로 `RotMat = Rz·Ry·Rx = [Rx(roll)·Ry(pitch)·Rz(yaw)]ᵀ`,
그리고 `velocity = RotMat·(0,0,-√(2gh))` 입니다. 즉 기기 좌표 충격방향은

```
d = Rᵀ·(0,0,-1) = (cos r·sin p,  -sin r,  -cos r·cos p)      (yaw=0)
```

이는 `AngleSourceParser.py:439` 의 자체 헬퍼 `_physical_drop_dir` 와 동일합니다.
`d = (±1,±1,±1)/√3` 를 풀면 `r = ±asin(1/√3) = ±35.264390°`, `p = ±45°`.
Front 계열은 `cos r` 부호가 반대라 `r = ±(180 − 35.264390) = ±144.735610°`.

### B-3. 실측 — 26케이스 전수

| 그룹 | 케이스 | 참 방향 대비 최대 오차 |
|------|--------|----------------------|
| 면 F1–F6 | 6 | **0.00°** ✅ |
| 모서리 E01–E12 | 12 | **0.00°** ✅ |
| 코너 C1–C8 | 8 | **9.74°** ❌ |

실덱 교차 확인 — `/data/Tests/Test_001_Full26_1Step/output` 26 Run 의
`DropSet.k` `*INITIAL_VELOCITY` 를 전수 추출한 결과 C 계열 8개 방향이 모두
`(±0.5000, ±0.7072, ±0.5000)` 로, 참 코너 `(±0.5774, ±0.5774, ±0.5774)` 대비 **9.740°**.

수정 후에는 8/8 모두 **0.000000°** 입니다.

### B-4. 이 저장소는 이미 정답을 알고 있습니다 (정의 이중화)

`Runner/CumulativeScenarioRunner.py:1855-1864` 의 하위호환 `corner_map` 은
**이미 35.264 / 144.736 을 씁니다.** 즉 같은 저장소 안에 코너 정의가 두 벌 있고
서로 다릅니다. 게다가 그 두 벌은 축 배정도 어긋납니다.

| C 번호 | AngleSourceParser (r, p) → 실제 향하는 꼭짓점 | CumulativeScenarioRunner (r, p) → 실제 향하는 꼭짓점 | 일치 |
|--------|---------------------------------------|----------------------------------------------|------|
| C1 | (45.0, −45.0) → `C1_Back_Right_Top` | (35.264, +45.0) → `C3_Back_Left_Top` | ❌ |
| C2 | (−45.0, −45.0) → `C2_Back_Right_Bottom` | (−35.264, +45.0) → `C4_Back_Left_Bottom` | ❌ |
| C3 | (45.0, +45.0) → `C3_Back_Left_Top` | (35.264, −45.0) → `C1_Back_Right_Top` | ❌ |
| C4 | (−45.0, +45.0) → `C4_Back_Left_Bottom` | (−35.264, −45.0) → `C2_Back_Right_Bottom` | ❌ |
| C5–C8 | (±135, ±45) → 이름과 일치 | (±144.736, ±45) → 이름과 일치 | ✅ |

정리하면 **AngleSourceParser 는 축 배정이 맞고 크기가 틀렸으며, CumulativeScenarioRunner
는 크기가 맞고 Back 계열(C1–C4) 축이 스왑돼 있습니다.** 어느 쪽도 단독으로는 옳지 않습니다.

### B-5. 제안 수정

`Runner/AngleSourceParser.py` (`math` 는 :20 에서 이미 import)

```diff
@@ -151,13 +151,20 @@ CUBOID_EDGES = {
  }

+# 정확한 꼭짓점 방향 roll.
+#   충격방향 d = Rᵀ·(0,0,-1) = (cos r·sin p, -sin r, -cos r·cos p)   (_physical_drop_dir 와 동일)
+#   d = (±1,±1,±1)/√3 를 풀면  r = ±asin(1/√3) = ±35.264390°, p = ±45°
+#   Front 계열은 cos r 부호가 반대라  r = ±(180 - 35.264390) = ±144.735610°
+#   45/135 를 쓰면 d=(±0.5,±0.7071,±0.5) 로 참 코너에서 9.736° 벗어난다.
+_CORNER_ROLL   = math.degrees(math.asin(1.0 / math.sqrt(3.0)))   # 35.2643896828
+_CORNER_ROLL_F = 180.0 - _CORNER_ROLL                            # 144.7356103172
+
 CUBOID_CORNERS = {
-    "C1_Back_Right_Top":      (45.0,   -45.0, 0.0),
-    "C2_Back_Right_Bottom":   (-45.0,  -45.0, 0.0),
-    "C3_Back_Left_Top":       (45.0,    45.0, 0.0),
-    "C4_Back_Left_Bottom":    (-45.0,   45.0, 0.0),
-    "C5_Front_Right_Top":     (135.0,   45.0, 0.0),
-    "C6_Front_Right_Bottom":  (-135.0,  45.0, 0.0),
-    "C7_Front_Left_Top":      (135.0,  -45.0, 0.0),
-    "C8_Front_Left_Bottom":   (-135.0, -45.0, 0.0),
+    "C1_Back_Right_Top":      ( _CORNER_ROLL,   -45.0, 0.0),
+    "C2_Back_Right_Bottom":   (-_CORNER_ROLL,   -45.0, 0.0),
+    "C3_Back_Left_Top":       ( _CORNER_ROLL,    45.0, 0.0),
+    "C4_Back_Left_Bottom":    (-_CORNER_ROLL,    45.0, 0.0),
+    "C5_Front_Right_Top":     ( _CORNER_ROLL_F,  45.0, 0.0),
+    "C6_Front_Right_Bottom":  (-_CORNER_ROLL_F,  45.0, 0.0),
+    "C7_Front_Left_Top":      ( _CORNER_ROLL_F, -45.0, 0.0),
+    "C8_Front_Left_Bottom":   (-_CORNER_ROLL_F, -45.0, 0.0),
 }
```

같은 PR 에 함께 넣기를 권합니다.

1. **정의 단일화** — `CumulativeScenarioRunner.py:1855-1864` 의 `corner_map` 을 지우고
   `from Runner.AngleSourceParser import CUBOID_CORNERS` 로 대체. 두 벌을 남기면
   B-4 의 스왑이 계속 살아남습니다.
2. **문서 갱신** — `Examples/HWWarrantyDropTest/KooChainRun_Complete_Guide.md:380, 382`,
   `docs/PLAN_RiskConditionPartDOE.md:41` 의 `Roll=45°` 표기.
3. **회귀 테스트 신설** — 26케이스 전부가 이름이 뜻하는 방향을 향하는지 검사.
   모서리의 짐벌 퇴화(과거 E09–E12 사고)도 같은 테스트로 다시 막힙니다.

```python
def test_cuboid_directions_match_names():
    """F/E/C 26케이스가 이름이 뜻하는 방향을 실제로 향하는지."""
    for table in (CUBOID_FACES, CUBOID_EDGES, CUBOID_CORNERS):
        for name, (r, p, y) in table.items():
            d = np.array(_physical_drop_dir(r, p))
            t = _truth_from_name(name)      # Right=-X, Top=-Y, Back=-Z (관측자 기준)
            assert math.degrees(math.acos(float(d @ t))) < 1e-6, name
```

### B-6. 주의

roll 값이 런 폴더/alias 이름에 `format(RxOrigin, '.3f')`
(`KooDynaAdvancedModification.py:3100`) 로 들어가므로 폴더명이 `..._35.264` 형태로
바뀝니다. 기존 결과와 이름을 비교하는 스크립트가 있으면 함께 확인이 필요합니다.

---

## C. DropSet 라벨의 각도/위치 이름이 전 런 동일

### C-1. 문제

`Runner/CumulativeScenarioRunner.py:1417-1421`

```python
def _create_step_config(self, doe_index: int, step_config: Dict[str, Any]) -> Optional[str]:
    step_num  = step_config["step"]
    mode      = step_config["mode"]
    condition = step_config["condition"]        # ← 시나리오 템플릿의 steps[0].condition 에 고정
```

`condition` 이 DOE 인덱스와 무관하게 시나리오 템플릿 값(보통 첫 케이스 이름)으로 고정되어,
`*Description` 과 그 산출물인 `DropSet.json.description` 의 각도/위치 이름 토큰이
모든 런에서 같아집니다.

**물리량은 정상입니다.** `_get_doe_euler`(:1769) / `_get_doe_position`(:1791) 은
`doe_angles` / `doe_positions` 를 `doe_index` 로 직접 조회하므로 EulerRolling/Pitching/Yawing
과 LocationX/Y 는 런마다 올바르게 다릅니다. **틀린 것은 라벨뿐입니다.**

### C-2. 실측

`/data/Tests/Test_001_Full26_1Step` 의 26 Run — 오일러는 26개 전부 다른데
description 의 각도 토큰은 **26/26 모두 `C1_Back_Right_Top`**:

```
DOE001  (  0.00,   0.00, 0.0) → 실제 F1_Back                 라벨 C1_Back_Right_Top ✗
DOE002  (180.00,   0.00, 0.0) → 실제 F2_Front                라벨 C1_Back_Right_Top ✗
DOE007  (  0.00, -45.00, 0.0) → 실제 E01_Back_Right          라벨 C1_Back_Right_Top ✗
DOE019  ( 45.00, -45.00, 0.0) → 실제 C1_Back_Right_Top       라벨 C1_Back_Right_Top ✓ (유일)
DOE026  (-135.0, -45.00, 0.0) → 실제 C8_Front_Left_Bottom    라벨 C1_Back_Right_Top ✗
```

**라벨 불일치 25/26.** 우연히 맞는 1건은 템플릿 값과 같은 케이스뿐입니다.

전 캠페인 집계 (측정 범위를 함께 적습니다 — `/data` 전체 깊이 스캔은 20분 내 완료되지 않아
깊이 5 이내로 제한했습니다)

- `/data` 깊이 5 이내 `DropSet.json` **1,719개**. 그중 런 2개 이상인 캠페인
  **17개를 표본 집계한 결과 17/17 전부** 각도 토큰 유일값이 **1개** — DOE 별로
  다른 파일은 **0개**. (표본 합계 1,637개)
- `Test_006_Fibonacci_6deg` 1,144 런 — description 전체값은 1,144개로 달라 보이지만
  (DOE 번호 접두사 때문) **각도 토큰 유일값은 1개** (`P0001` × 1,144).
  같은 캠페인의 `runner_config.json` 에는 `doe_angles` 의 angle_name 이 P0001~P1146 로
  정상 저장돼 있어, 값은 있는데 라벨에 못 실린 것이 확인됩니다.
- IMPACT 계열 `DropWeightImpactTestSet.json` **27개** 도 동일 (위치 이름 토큰 고정)

즉 이 저장소가 만든 낙하 산출물 전체가 대상입니다.

### C-3. 영향

덱과 결과는 정확하므로 해석 결과 자체는 틀리지 않습니다. 문제는 **추적성**입니다.

- 산출물만 보고는 어느 런이 어느 자세인지 알 수 없습니다 (오일러를 직접 읽어야 함)
- 후처리 보고서가 이 이름을 표시하면 사용자는 전부 같은 케이스로 오인합니다
- 후처리(KooD3plotReader)는 이 불일치를 방어하기 위해 **덱의 오일러를 1순위 진실로 삼고**,
  이름과 실낙하 방향이 15° 이상 어긋나면 경고를 띄우도록 이미 대응해 두었습니다
  (`⚠ 이름 방향과 실제 낙하 방향이 N° 어긋남 — 덱(실낙하) 기준으로 표시`).
  상류가 고쳐지면 이 경고는 자연히 사라집니다.

### C-4. 제안 수정

치환 로직을 헬퍼로 단일화하고 `_create_step_config` 진입점에서 풀어 줍니다.
한 곳만 고치면 `*Description` 템플릿 5곳(`StepConfigBuilder.py:248, 481`,
`CumulativeScenarioRunner.py:1541, 1651, 1750`)이 모두 정상화됩니다.

```diff
+    def _resolve_doe_condition(self, doe_index: int, step_num: int, condition: str) -> str:
+        """DOE별 실제 condition(angle_name / position_name) 해석 — 단일 사실원천.
+        테이블이 없으면 입력을 그대로 반환해 기존 동작을 보존한다."""
+        sc = self.config.get("scenario", {})
+        angles    = sc.get("doe_angles")    or []
+        positions = sc.get("doe_positions") or []
+        if 0 <= doe_index < len(angles) and angles[doe_index].get("angle_name"):
+            return angles[doe_index]["angle_name"]
+        if 0 <= doe_index < len(positions) and positions[doe_index].get("position_name"):
+            return positions[doe_index]["position_name"]
+        return condition
+
     def _create_step_config(self, doe_index: int, step_config: Dict[str, Any]) -> Optional[str]:
         step_num  = step_config["step"]
         mode      = step_config["mode"]
-        condition = step_config["condition"]
+        condition = self._resolve_doe_condition(doe_index, step_num,
+                                                step_config["condition"])
```

회귀 테스트 제안 — 한 캠페인의 DropSet.json 을 모아 각도 토큰 유일값이 런 수와 같은지 검사.

---

## 참고 — 후처리 쪽 규약 (대조용)

이 보고서의 방향 계산은 후처리 저장소가 1,144런 실덱의 `*INITIAL_VELOCITY` 와 대조해
확정한 규약과 동일합니다 (최악 내적 +1.0000).

- 충격 방향(기기 좌표) `= Rᵀ·(0,0,−1)`, `R = Rx(roll)·Ry(pitch)·Rz(yaw)`
- 이름 규약은 **관측자 기준**: `Right = −X`, `Top = −Y`, `Back = −Z`
- 근거: KooD3plotReader `docs/custom_report/context-notes.md`

문의는 후처리 저장소 이슈로 주시면 됩니다.
