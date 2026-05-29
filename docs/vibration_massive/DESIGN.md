# DESIGN — VIBRATION 모드 Zero-Hardcode 아키텍처

> 본 문서는 `design_decisions.md` (7개 결정 A–G) + `final_plan.md` (DOE 가드 / 스트리밍 / submit throttle 보강 결정) + `verifications.json` (호환성 5개 + DOE explosion 5개 검증) 를 통합한 **단일 진실원 (Single Source of Truth) 아키텍처 문서**다.
>
> 원칙 준수: CLAUDE.md §1 Think Before — 가정 명시 / §2 Simplicity — 최소 코드 / §3 Surgical — 인접 코드 미터치 / §4 Goal-Driven — 검증 가능 산출물.

---

## 1. 아키텍처 5 레이어 다이어그램

각 레이어는 **단방향 의존** (위→아래) 만 허용한다. 역방향 import 금지.

```
┌─────────────────────────────────────────────────────────────────────┐
│ L1 │ User Input                                                     │
│    │   scenario.json — vibration_source 블록 (source_type 자유 문자열) │
│    │   CLI flags: --components-override <path>, --yes               │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ (open-set string discriminator: D)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ L2 │ External Configs (선택적 외부화 — v1은 inline)                  │
│    │   vibration_curves/*.csv              (G: kind="csv")          │
│    │   components.yaml  (E: $ref 진입로, v1은 inline 우선)          │
│    │   mode_definitions은 코드 상수로 inline (YAGNI)                │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ (file paths or inline dict)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ L3 │ VibrationSource Registry — Runner/VibrationSource.py (신규)    │
│    │                                                                │
│    │   _VIBRATION_PARSERS: Dict[str, Callable] = {}                 │
│    │   @register_vibration_source("per_cap")           ──┐          │
│    │   @register_vibration_source("circuit_group")     ──┤ 정적      │
│    │   @register_vibration_source("explicit_factors")  ──┤ import만  │
│    │   @register_vibration_source("cap_combination")   ──┤ (Nuitka  │
│    │   @register_vibration_source("curve_library")     ──┘  안전)   │
│    │                                                                │
│    │   parse_vibration_source(config, ctx) → VibrationLoadSpec      │
│    │     · 미등록 source_type → "Registered: [...]" 명시 ValueError │
│    │     · ctx.max_doe_count 초과 → abort (DOE 폭증 가드)            │
│    │   resolve_components(config) — inline | ref+override            │
│    │   materialize_curve(spec)    — kind=inline|csv (확장 hook)     │
│    │   validate_direction(d)      — "X|Y|Z" 즉시 / object 미래 hook │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ VibrationLoadSpec (frozen dataclass)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ L4 │ StepConfigBuilder — Runner/StepConfigBuilder.py (함수 추가)    │
│    │                                                                │
│    │   build_vibration_load_block(spec) → step_config text          │
│    │     · _VIB_KEYWORDS    : KooMeshModifier 파서 계약 1곳 격리    │
│    │     · _VIB_OPTION_KEYS : 옵션 키 카탈로그                       │
│    │     · DROP의 build_drop_attitude_config 패턴 미러링            │
│    │                                                                │
│    │   IMPACT/THERM 인라인 f-string은 본 PR 미터치 (surgical)       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ step_config: str (LS-DYNA-like keyword text)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ L5 │ 기존 KooChainRun Pipeline (재사용, 비대칭만 추가)              │
│    │                                                                │
│    │   CumulativeScenarioRunner._run_step()                         │
│    │     L1175 if   mode == "DROP":   build_drop_attitude_config()  │
│    │     L1196 elif mode == "IMPACT": (인라인, 본 PR 미터치)         │
│    │     L1237 elif mode == "THERM":  (인라인, 본 PR 미터치)         │
│    │     L????  elif mode == "VIB":   build_vibration_load_block() ◄│
│    │                                              [+12 LOC]         │
│    │                                                                │
│    │   TemplateManager.select_template_for_step()                   │
│    │     _FIRST_TEMPLATE_BY_MODE  = {DROP, IMPACT, THERM, VIB → …}  │
│    │     _CUMULATIVE_TEMPLATE_BY_MODE = {…}                         │
│    │                                                                │
│    │   → KooMeshModifier → LS-DYNA → dynain (변경 0)                │
└─────────────────────────────────────────────────────────────────────┘
```

**역방향 의존 검증:** L3 (VibrationSource) 는 L4 (StepConfigBuilder) 를 import 하지 않는다 — L3 은 `VibrationLoadSpec` dataclass 만 반환하고, L4 가 이를 입력으로 받아 직렬화한다. 이 일방향성이 단위 테스트 격리의 기반이다.

---

## 2. Zero-Hardcode 7 결정 상세

### A. `source_type` dispatch — Registry + Decorator

**채택안:**
```python
# Runner/VibrationSource.py
_VIBRATION_PARSERS: Dict[str, Callable[[dict, Context], VibrationLoadSpec]] = {}

def register_vibration_source(name: str):
    def deco(fn):
        if name in _VIBRATION_PARSERS:
            raise RuntimeError(f"Duplicate vibration source: {name}")
        _VIBRATION_PARSERS[name] = fn
        return fn
    return deco
```

**기각안:**
| 안 | 기각 이유 |
|---|---|
| if/elif chain (5 분기) | OCP 위반, 새 source 추가 시 4곳 동시 수정, Audit 1 위험 #1 |
| Plugin auto-discovery (`pkgutil.iter_modules`) | Nuitka 컴파일 산출물에서 `.so` 경로 silent skip 위험 (Audit 4) |

**영향 파일 + 시그니처:**
- `Runner/VibrationSource.py` (신규) — `parse_vibration_source(config: dict, ctx: Context) -> VibrationLoadSpec`
- `Runner/CumulativeDesigner.py` (호출부 1곳) — `from Runner.VibrationSource import parse_vibration_source`

**회귀 위험:** **낮음**. 호출자는 단일 함수 시그니처만 보며, registry는 모듈 import 시점에 정적으로 채워진다 (Verify1-Q2 확인).

---

### B. `step_config` 직렬화 — StepConfigBuilder 함수

**채택안:** 단일 함수 `build_vibration_load_block(**kwargs) -> str` — DROP의 `build_drop_attitude_config` 패턴 그대로 미러링.

**기각안:**
| 안 | 기각 이유 |
|---|---|
| 인라인 f-string (IMPACT/THERM 패턴 복제) | Audit 2 위험 1–7 모두 노출, 안티패턴 4번째 복제 |
| Jinja 템플릿 파일 | SIF 마운트 의존성 추가 (CLAUDE.md §2 위반) |
| 커스텀 DSL | over-engineering, 단일 사용처 (YAGNI) |

**영향 파일:**
- `Runner/StepConfigBuilder.py` — `+~90 LOC`
- `Runner/CumulativeScenarioRunner.py` (L1240 근방) — `+~14 LOC`

**회귀 위험:** **낮음**. DROP과 대칭 패턴, IMPACT/THERM 미터치 (surgical).

---

### C. Mode dispatch — 기존 Enum + lookup dict

**채택안:**
```python
# Runner/TemplateManager.py
_FIRST_TEMPLATE_BY_MODE = {
    SimulationMode.DROP:   TemplateType.DROP_FIRST,
    SimulationMode.IMPACT: TemplateType.IMPACT_FIRST,
    SimulationMode.THERM:  TemplateType.THERM_FIRST,
    SimulationMode.VIB:    TemplateType.VIB_FIRST,
}
```

**기각안:**
| 안 | 기각 이유 |
|---|---|
| `mode_definitions.yaml` 외부화 | config 폭증, SIF 마운트 의존성, IDE 타입 안전성 손실 |
| Mode 전체를 Registry로 치환 | over-engineering, `SimulationMode.VIB`는 line 34에 이미 존재 |

**영향 파일:** `Runner/TemplateManager.py` L145–179 (elif → mapping dict), `Runner/CumulativeDesigner.py` L170–178.

**회귀 위험:** **매우 낮음**. 외부 consumer가 `TemplateType` 문자열을 참조하지 않음 (Audit 3 grep 확인).

---

### D. `source_type` 위치 — resolver discriminator (open-set string)

**채택안:**
```jsonc
"vibration_source": {
  "type": "object",
  "required": ["source_type"],
  "properties": {
    "source_type": { "type": "string" }   // enum 명시 금지
  },
  "additionalProperties": true
}
```

검증은 런타임 registry lookup 시점에서 처리하고, 미등록 시 `Registered: [per_cap, circuit_group, …]` 메시지로 가능한 값을 공개한다.

**기각안:** JSON Schema `enum: [per_cap, ...]` → 폐쇄형, 신규 source 추가 시 schema 동시 수정 (single point of failure 분할).

**영향 파일:** `Runner/schemas/vibration_source.schema.json` (신규).
**회귀 위험:** **0**. 기존 유효 문자열은 그대로 통과.

---

### E. components 정의 — Inline + `$ref` 진입로 예약

**채택안:** 시나리오 수 ≤ 50 (현재 battery_study 추정 30–50) → inline 시작. Schema에 `components_ref` 필드만 미리 정의해 forward-compatible.

**기각안:**
| 안 | 기각 이유 |
|---|---|
| 즉시 external registry 강제 | 시나리오 수 미달, YAGNI |
| 환경별 registry 분리 (dev/staging/prod) | over-engineering (Audit 5) |

**영향 파일:** `Runner/VibrationSource.py::resolve_components`, `schemas/vibration_source.schema.json`.
**회귀 위험:** **0**. 기존 inline 시나리오 그대로 동작.

---

### F. Direction 표현 — axis string "X/Y/Z"

**채택안:** `"direction": "Z"` 즉시 채택, 향후 vector 입력 `{"axis": [0.7, 0.7, 0]}` 은 schema `oneOf` 로 hook만 예약.

**근거:** `KooVibrationLoad.py:33–34` 가 `X/Y/Z` 만 hard validate, `*LOAD_BODY_PARTS_X/Y/Z` 카드 자체가 솔버 한계.

**기각안:** 즉시 vector 채택 → 솔버 layer 변경 0 인데 schema만 복잡해짐 (추상화 이득 없음).

**영향 파일:** `Runner/VibrationSource.py::validate_direction`.
**회귀 위험:** **0** (솔버 한계 그대로 반영).

---

### G. `base_curve` 입력 — discriminated union by `kind`

**채택안:**
```jsonc
{ "kind": "inline", "points": [[0,0],[0.001,100],[0.002,0]] }
{ "kind": "csv",    "path": "./curves/swept_sine.csv", "t_col": 0, "v_col": 1, "skiprows": 1 }
// 미래 예약 (hook만): "analytic" | "library_ref" | "composite"
```

**기각안:**
| 안 | 기각 이유 |
|---|---|
| inline list 영구 강제 | CSV/analytic/library 차단 (Audit 4 위험 #3) |
| 모든 kind 즉시 구현 | over-engineering, sine/sweep/library 즉시 요구 없음 |

**영향 파일:** `Runner/VibrationSource.py::materialize_curve` (curve materializer registry).
**회귀 위험:** **0**. 모든 kind는 런타임에 `list[(t,v)]`로 materialize → KooVibrationLoad 변경 0줄.

---

### 보강 결정 (final_plan.md, verifications.json)

| ID | 항목 | 채택안 | 근거 |
|---|---|---|---|
| H | DOE explosion 가드 | `environment.max_doe_count` (default 500) + `--yes` override | Verify2-Q1: C(50,5)=2.1M 무방어 |
| I | runner_config.json 스트리밍 | total_doe > 1000 시 `step_template` 추출 + `doe_index.jsonl` per-line | Verify2-Q5: 100 DOE = 56KB 선형 → 1M DOE = ~570MB OOM |
| J | sbatch throttle | `Runner/SlurmSubmit.py` 단일 helper, 7개 site 점진 마이그레이션 | Verify2-Q3: 호출 site 분산 |

---

## 3. JSON Schema (draft 2020-12) — `vibration_source` 블록

```jsonc
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://pyKooCAE/schemas/vibration_source.schema.json",
  "type": "object",
  "required": ["source_type", "direction", "load_type", "base_curve"],
  "additionalProperties": true,
  "properties": {
    "source_type":    { "type": "string" },
    "direction": {
      "oneOf": [
        { "type": "string", "enum": ["X", "Y", "Z"] },
        { "type": "object", "required": ["axis"],
          "properties": {
            "axis": { "type": "array", "minItems": 3, "maxItems": 3,
                       "items": { "type": "number" } } } }
      ]
    },
    "load_type":     { "type": "string", "enum": ["Force", "Acceleration"] },
    "relative_mode": { "type": "string",
                       "enum": ["Explicit", "VolumeProportional",
                                "MassProportional", "Equal"] },
    "reference_part": { "type": "integer", "minimum": 1 },
    "base_curve": {
      "type": "object",
      "required": ["kind"],
      "oneOf": [
        { "properties": {
            "kind":   { "const": "inline" },
            "points": { "type": "array", "minItems": 2,
                        "items": { "type": "array", "minItems": 2,
                                   "maxItems": 2,
                                   "items": { "type": "number" } } } },
          "required": ["points"] },
        { "properties": {
            "kind":     { "const": "csv" },
            "path":     { "type": "string" },
            "t_col":    { "type": "integer", "minimum": 0, "default": 0 },
            "v_col":    { "type": "integer", "minimum": 0, "default": 1 },
            "skiprows": { "type": "integer", "minimum": 0, "default": 0 } },
          "required": ["path"] }
      ]
    },
    "components":     { "type": "object" },
    "components_ref": { "type": "string" },
    "components_override": { "type": "object" },
    "cap_part_id":    { "type": "integer", "minimum": 1 },
    "cap_pool":       { "type": "array", "items": { "type": "integer", "minimum": 1 } },
    "select_k":       { "type": "integer", "minimum": 1 },
    "circuit_group":  { "type": "string" },
    "explicit_factors": {
      "type": "array",
      "items": { "type": "array", "minItems": 2, "maxItems": 2 }
    },
    "curve_library":  { "type": "string" }
  }
}
```

**검증 책임 분담:** Schema 는 **구조 검증** (필수 필드/타입), 런타임 `parse_vibration_source` 는 **의미 검증** (source_type registry lookup, max_doe_count 가드, curve_library 존재 여부).

---

## 4. Registry 구현 패턴

```python
# Runner/VibrationSource.py (~30 줄 핵심)
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

@dataclass(frozen=True)
class VibrationLoadSpec:
    direction: str
    load_type: str
    relative_mode: str
    load_curve: List[Tuple[float, float]]
    part_list: Optional[List[int]] = None
    part_factors: Optional[List[Tuple[int, float]]] = None
    reference_part: Optional[int] = None

_VIBRATION_PARSERS: Dict[str, Callable] = {}

def register_vibration_source(name: str):
    def deco(fn):
        if name in _VIBRATION_PARSERS:
            raise RuntimeError(f"Duplicate vibration source: {name}")
        _VIBRATION_PARSERS[name] = fn
        return fn
    return deco

def parse_vibration_source(config: dict, ctx) -> VibrationLoadSpec:
    src = config.get("source_type")
    if src not in _VIBRATION_PARSERS:
        raise ValueError(
            f"Unknown source_type: {src!r}. "
            f"Registered: {sorted(_VIBRATION_PARSERS)}"
        )
    return _VIBRATION_PARSERS[src](config, ctx)

@register_vibration_source("per_cap")
def _parse_per_cap(config, ctx) -> VibrationLoadSpec: ...
```

**Nuitka 안전 보장:** decorator는 모듈 import 시점에 1회 실행 → `_VIBRATION_PARSERS` 가 모듈 전역 dict 로 채워짐. `importlib`/`pkgutil` 사용 0.

---

## 5. StepConfigBuilder.build_vibration_load_block — 시그니처 + 파서 계약 카탈로그

```python
# Runner/StepConfigBuilder.py

# 파서 계약 카탈로그 (KooMeshModifier 측과 1:1 매핑)
_VIB_KEYWORDS = {
    "block_open":  "**VibrationLoad,1",
    "block_close": "**EndVibrationLoad",
    "curve_end":   "EndLoadCurve",
    "factors_end": "EndPartFactors",
}

_VIB_OPTION_KEYS = (
    "Direction", "LoadType", "RelativeMode",
    "ReferencePart", "LoadCurve", "PartFactors", "PartList",
)

def build_vibration_load_block(
    *,
    direction: str,                              # "X" | "Y" | "Z"
    load_type: str,                              # "Force" | "Acceleration"
    relative_mode: str,                          # "Explicit" | "VolumeProportional" | ...
    load_curve: List[Tuple[float, float]],       # 이미 materialize됨
    part_factors: Optional[List[Tuple[int, float]]] = None,
    part_list: Optional[List[int]] = None,
    reference_part: Optional[int] = None,
) -> str:
    ...
```

**반환 텍스트 예시 (per_cap, direction=Z, Force, PartList=[101]):**
```
**VibrationLoad,1
Direction,Z
LoadType,Force
RelativeMode,Explicit
LoadCurve
0.0, 0.0
0.001, 1.0
0.02, 1.0
0.021, 0.0
EndLoadCurve
PartList
101
**EndVibrationLoad
```

**파서 계약 (KooMeshModifier/KooVibrationLoad 1:1 매핑):**
| 카탈로그 키 | KooVibrationLoad 측 |
|---|---|
| `**VibrationLoad,1` | block_open token |
| `Direction,<X\|Y\|Z>` | line 33–34 hard validation |
| `LoadType,<Force\|Acceleration>` | `*LOAD_BODY_PARTS_*` 카드 선택 |
| `RelativeMode,<Explicit\|VolumeProportional\|…>` | 가중치 분배 모드 |
| `LoadCurve … EndLoadCurve` | `*DEFINE_CURVE` 생성 |
| `PartFactors … EndPartFactors` | `*SET_PART_LIST_GENERATE` per-part factor |
| `PartList` | `*SET_PART_LIST` |
| `**EndVibrationLoad` | block_close token |

---

## 6. 회귀 안전 보장 — DROP / IMPACT / THERM 무수정

| 모드 | 본 PR 변경 | 회귀 위험 |
|---|---|---|
| DROP | **0줄** — `build_drop_attitude_config` 그대로 사용 | **0** |
| IMPACT | **0줄** — L1196 인라인 f-string 미터치 (surgical) | **0** |
| THERM | **0줄** — L1237 인라인 f-string 미터치 (surgical) | **0** |
| VIB | `elif mode == "VIB":` 분기 신규 추가 (~12 LOC) | 신규 모드, 회귀 N/A |

**검증 절차 (P3 종료 시 byte-level diff):**
1. Test_005 (DROP 100 DOE) → 신규 코드로 `runner_config.json` 재생성 → `diff` → byte-level diff 0.
2. `Examples/drop_weight_impact/scenario_part_center.json` (IMPACT) → 재생성 → diff 0.
3. CumulativeDesigner dispatch (`if has_impact else` → dict lookup) 변환 후 동일 입력 출력 bit-exact.

**TemplateManager 의 elif → mapping dict 평탄화 회귀:** 외부 consumer 가 `TemplateType` 문자열을 참조하지 않음 (Audit 3 grep 확인 완료) → 회귀 위험 없음.

---

## 7. Nuitka 빌드 호환성

### 7.1 정적 import 원칙

| 항목 | 본 PR 사용 여부 | 비고 |
|---|---|---|
| `import Runner.VibrationSource` (top-level static) | YES | Nuitka `--follow-imports` 안전 |
| `@register_vibration_source` decorator (모듈 로드 시 1회 실행) | YES | `_VIBRATION_PARSERS` 모듈-전역 dict, Nuitka 호환 확인 (Verify1-Q2) |
| `importlib.import_module` | NO | 동적 import 금지 |
| `pkgutil.iter_modules` | NO | plugin auto-discovery 금지 |
| 엔트리포인트 기반 plugin | NO | SIF/Nuitka 환경 silent skip 위험 |

### 7.2 호출자 명시 import 요건

```python
# Runner/CumulativeDesigner.py 상단에 명시 (Verify1-Q2 (i) 항)
from Runner.VibrationSource import (
    parse_vibration_source,
    resolve_components,
    materialize_curve,
)
```

이 import 가 모듈 로드 시점에 데코레이터를 실행시키므로 registry 가 채워진다. **lazy import 금지** — 데코레이터 미실행 위험.

### 7.3 빌드 후 smoke test

```bash
bash build_KooChainRun_python312.sh

# 산출물에 VibrationSource 포함 확인
find build_dist/lib/KooChainRun -name "VibrationSource*" | grep -q VibrationSource

# Registry 등록 smoke (신규 명령)
KooChainRun list-vibration-sources
# 기대 출력 (5개 모두):
#   per_cap / circuit_group / explicit_factors / cap_combination / curve_library

# jsonschema metaschema 로드 확인 (Verify1-Q5)
KooChainRun validate-scenario Examples/vibration_source/scenario_A_single_cap.json
```

**실패 fallback (Verify1-Q5):** `build_KooChainRun_python312.sh` 에 `--include-package=jsonschema_specifications --include-package-data=jsonschema_specifications` 추가. v1 은 inline schema 만 쓰므로 RefResolver 경로 미사용 → fallback 미적용 가능 (YAGNI).

### 7.4 빌드 사이즈 영향

| 항목 | 추정 영향 |
|---|---|
| `Runner/VibrationSource.py` (~280 LOC) | < 0.1 MB |
| `Runner/StepConfigBuilder.py` 추가 함수 | < 0.05 MB |
| `jsonschema-specifications` 데이터 파일 (fallback 시) | ~0.3 MB |
| **합계** | **< 0.5 MB / 빌드 사이즈 증가 <5%** (P6 검증 기준) |

---

**문서 끝.** 본 DESIGN.md는 P1–P6 구현 phase의 단일 reference. 변경 시 design_decisions.md, final_plan.md, verifications.json 의 정합성을 동시에 갱신할 것.
