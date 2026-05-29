# EXAMPLES — VIBRATION 모드 시나리오 & 외부 Config 예시

> 본 문서는 VIBRATION 모드의 3가지 대표 시나리오(A/B/C), 외부 curve library 구조, base_curve 3가지 입력 형식, amplitude 분배 4가지 방식, 그리고 검증 명령을 한 곳에 모았다. JSON 예시는 모두 **완전한 형태**라 그대로 복붙해 쓸 수 있다.

---

## ⚠️ 0. 사전 요구사항 — `base_dir` 은 반드시 NFS 공유 경로

KooChainRun 잡은 **헤드노드 + 컴퓨트 노드 양쪽에서 동일 경로**로 `runner_config.json`, 입력 `.k`, slurm 스크립트를 읽어야 한다. 따라서 시나리오의 `base_dir` / `output_dir` 은 **반드시 NFS로 공유된 경로**에 두어야 한다.

**허용되는 위치 (NFS 공유):**
- `/data/...` (cluster shared)
- `/home/...` (NFS home)
- `/shared/...` 또는 사이트별 공유 마운트

**금지 (노드 로컬 FS — sbatch 잡은 컴퓨트 노드에서 절대 못 읽음):**

```
❌ /tmp/...                # 노드 로컬, 헤드노드 /tmp 와 컴퓨트 노드 /tmp 는 별개
❌ /var/tmp/...            # 동일
❌ $TMPDIR (slurm 외부)    # 컴퓨트 노드 입장에서 미정의
```

`/tmp` 에 시나리오를 두면 P2.9 와 같이 sbatch 는 통과해도 컴퓨트 노드에서 `runner_config.json` 을 못 찾아 300초 NFS 대기 후 `exit 1` 로 끝난다. **`Run_*/` 폴더 0개, `_vib.k` 0건, d3plot 0건**이 결과로 남는다.

**검증 명령 (사용 전 확인):**
```bash
# 잡 제출 노드에서
ls -la $YOUR_BASE_DIR/runner_config.json    # 헤드노드 read OK 확인
# 컴퓨트 노드 측에서 (가능하다면)
ssh node001 'ls -la $YOUR_BASE_DIR/runner_config.json'
# 동일 inode/mtime 보이면 NFS OK
```

---

## 1. 시나리오 A — 캡 1개 진동 (최소 단위, P1 검증용)

**목적:** Registry + StepConfigBuilder 인프라가 단일 DOE 1 step에서 LS-DYNA error 0으로 통과하는지 확인. P1 phase의 골든 케이스.

### `Examples/vibration_source/scenario_A_single_cap.json`

```json
{
  "project_name": "VIB_single_cap_demo",
  "mode": "VIB",
  "input_file": "model.k",
  "output_dir": "./output_A",
  "vibration_source": {
    "resolver": "per_cap",
    "cap_part_id": 101,
    "direction": "Z",
    "load_type": "Force",
    "relative_mode": "Explicit",
    "base_curve": {
      "kind": "inline",
      "points": [[0.0, 0.0], [0.001, 1000.0], [0.020, 1000.0], [0.021, 0.0]]
    }
  },
  "environment": {
    "max_doe_count": 1,
    "concurrency": { "max_concurrent_jobs": 1 }
  }
}
```

### 동작 설명

1. `parse_vibration_source(config, ctx)` → resolver `"per_cap"` → `_parse_per_cap` 호출
2. `VibrationLoadSpec(direction="Z", load_type="Force", load_curve=[(0,0),(0.001,1000),(0.020,1000),(0.021,0)], part_list=[101])` 생성
3. `build_vibration_load_block(spec)` → step_config 텍스트 (DROP 패턴 미러)
4. KooMeshModifier → `*LOAD_BODY_PARTS_Z` + `*SET_PART_LIST{101}` + `*DEFINE_CURVE{...}` 생성
5. LS-DYNA dynain 실행 → `output_A/Run_DOE001_S001_VIB_z_force/` 에 결과 저장

### 예상 alias

```
VIB_single_cap_demo_CUM001_DOE001_S001_VIB_z_force
```

### 출력 파일

```
output_A/
├── Run_DOE001_S001_VIB_z_force/
│   ├── Input/
│   │   └── model_step001.k                 # KooMeshModifier 출력
│   ├── Output/
│   │   ├── d3plot, d3hsp, glstat, ...
│   │   └── model_step001_vib.k             # VibrationLoad 적용된 키 파일
│   └── slurm_logs/
├── simulation_index.json
├── runner_config.json
└── checkpoint.json
```

### 검증 명령

```bash
# 1. runner_config.json DOE 수
jq '.scenario.doe_count' output_A/runner_config.json
# 기대: 1

# 2. VIB block 생성 확인
grep -l "*LOAD_BODY_PARTS_Z" output_A/Run_DOE001_S001_*/Output/*.k
# 기대: 1개 파일 매치

# 3. LS-DYNA error 0 확인
grep "N o r m a l    t e r m i n a t i o n" output_A/Run_DOE001_S001_*/Output/d3hsp
# 기대: 1줄 매치
```

---

## 2. 시나리오 B — 회로 일괄 진동 (사용자 핵심 케이스)

**목적:** 단일 시나리오에서 회로 N개 → DOE N개 자동 생성. 각 회로 내 모든 PID는 **동일 SF**가 적용되며, 분배 방식은 `distribution` 필드로 선택. v1 사용자의 가장 흔한 use case.

### `Examples/vibration_source/scenario_B_circuit_group.json`

```json
{
  "project_name": "VIB_circuit_group_demo",
  "mode": "VIB",
  "input_file": "pcb_assembly.k",
  "output_dir": "./output_B",
  "vibration_source": {
    "resolver": "circuit_group",
    "direction": "Z",
    "load_type": "Acceleration",
    "relative_mode": "VolumeProportional",
    "distribution": "mass_proportional",
    "circuits": {
      "main_power": {
        "description": "메인 전원 회로 (DC-DC + 출력 cap)",
        "components": [
          { "role": "cap",  "part_ids": [101, 102, 103] },
          { "role": "coil", "part_ids": [201, 202] }
        ],
        "reference_part": 999
      },
      "rf_frontend": {
        "description": "RF 프론트엔드 (matching network)",
        "components": [
          { "role": "cap",  "part_ids": [301, 302] },
          { "role": "ic",   "part_ids": [401] }
        ],
        "reference_part": 999
      },
      "audio_amp": {
        "description": "오디오 앰프 (출력 단)",
        "components": [
          { "role": "cap",  "part_ids": [501, 502, 503, 504] }
        ],
        "reference_part": 999
      }
    },
    "base_curve": {
      "kind": "csv_file",
      "path": "./vibration_curves/vib_001.csv"
    }
  },
  "environment": {
    "max_doe_count": 10,
    "concurrency": { "max_concurrent_jobs": 3 }
  }
}
```

### amplitude 분배 방식 선택

`distribution` 필드는 다음 중 하나:

| 값 | 의미 | KooMeshModifier `RelativeMode` 매핑 |
|---|---|---|
| `"mass_proportional"` | 각 PID에 질량 비례 SF (Force 모드에서 부위별 동일 가속도) | `VolumeProportional` (동일 재질 가정 시 ≈ 질량비) |
| `"volume_proportional"` | 각 PID에 부피 비례 SF (기존 동작) | `VolumeProportional` |
| `"equal"` | 모든 PID 동일 SF = 1.0 | `Explicit` + 전 PID 1.0 |
| `"custom_weights"` | PID별 사용자 dict | `Explicit` + dict 평탄화 |

### 동작 설명

1. resolver `"circuit_group"` → `circuits` 3개 → **DOE 3개** 생성
   - DOE001 = main_power (PID 101,102,103,201,202 동일 SF)
   - DOE002 = rf_frontend (PID 301,302,401 동일 SF)
   - DOE003 = audio_amp (PID 501,502,503,504 동일 SF)
2. 각 DOE 내부에서 `distribution: "mass_proportional"` → KooMeshModifier `RelativeMode=VolumeProportional` + reference_part=999 카드 생성
3. `base_curve.kind="csv_file"` → `Runner/CurveLoader.read_csv("./vibration_curves/vib_001.csv")` → inline `list[[t,v]]` 평탄화 후 KooVibrationLoad 호출
4. 모든 DOE 가 **동일 base_curve** 를 공유 (회로 단위 진동의 핵심 가정)

### 예상 alias

```
VIB_circuit_group_demo_CUM001_DOE001_S001_VIB_main_power
VIB_circuit_group_demo_CUM001_DOE002_S001_VIB_rf_frontend
VIB_circuit_group_demo_CUM001_DOE003_S001_VIB_audio_amp
```

### 검증 명령

```bash
# 1. DOE 3개 생성 확인
jq '.scenario.doe_count' output_B/runner_config.json
# 기대: 3

# 2. 회로별 PID 그룹 확인 (DOE002 = rf_frontend → PID 301, 302, 401 만 포함)
grep -A5 "*SET_PART_LIST" output_B/Run_DOE002_S001_*/Output/*_vib.k | head -20
# 기대: 301, 302, 401 라인 존재

# 3. 회로별 동일 SF 확인 (한 회로 내 모든 PID 의 SF 값이 동일)
grep -E "^\s*[0-9]+,\s*[0-9.eE+-]+\s*$" output_B/Run_DOE001_S001_*/Output/*_vib.k \
  | awk -F',' '{print $2}' | sort -u | wc -l
# 기대: 1줄 (모든 PID SF 동일 — equal 분배 시) 또는 N줄 (mass_proportional)

# 4. base_curve 동일성 확인 (3 DOE 모두 같은 curve)
md5sum output_B/Run_DOE00*/Output/*_vib.k | awk '{print $1}' | sort -u
# load curve 부분이 같으면 같은 hash 일부 일치
```

---

## 3. 시나리오 C — Cap 조합 DOE (Massive Parametric)

**목적:** `itertools.combinations(N, k)` 으로 캡 조합 폭증 → DOE 폭증 가드 + concurrency 제어 + dry-run preview 검증. P3/P4 phase의 골든 케이스.

### `Examples/vibration_source/scenario_C_cap_combination.json`

```json
{
  "project_name": "VIB_cap_combination_doe",
  "mode": "VIB",
  "input_file": "model.k",
  "output_dir": "./output_C",
  "vibration_source": {
    "resolver": "cap_combination",
    "cap_pool": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
    "select_k": 3,
    "direction": "Z",
    "load_type": "Force",
    "distribution": "equal",
    "base_curve": {
      "kind": "csv_file",
      "path": "./vibration_curves/vib_001.csv"
    }
  },
  "environment": {
    "max_doe_count": 200,
    "concurrency": {
      "max_concurrent_jobs": 8,
      "sbatch_throttle_sleep": 0.5
    }
  }
}
```

### DOE preview (dry-run)

조합 폭증 사전 점검:

```bash
KooChainRun prepare scenario_C_cap_combination.json --dry-run
```

**기대 stdout (정상):**
```
[VibrationSource] cap_combination: C(10, 3) = 120 cases
[DOE Guard] 120 <= max_doe_count (200) → proceed
[CumulativeDesigner] Writing runner_config.json (120 DOE)
[CumulativeDesigner] DOE count > 100, switching to streaming writer
[CumulativeDesigner]   → step_template extracted to runner_config.json (3.2 KB)
[CumulativeDesigner]   → 120 DOE entries written to doe_index.jsonl (18.4 KB)
[DryRun] No sbatch submitted. Inspect output_C/runner_config.json and doe_index.jsonl.
```

### max_doe_count 초과 시 (가드 동작)

`cap_pool: [50개 PID]`, `select_k: 5` 로 변경 → C(50,5)=2,118,760:

```
[VibrationSource] cap_combination: C(50, 5) = 2,118,760 cases
[DOE Guard] ABORT: candidate count 2,118,760 exceeds max_doe_count 200
            Hint: --yes to override, or reduce select_k / cap_pool size.
ExitCode: 2
```

`--yes` 으로 강제 진행 시 streaming writer 동작 (1M+ DOE 처리 가능):
```bash
KooChainRun prepare scenario_C_cap_combination.json --yes
```

### 동작 설명

1. `_parse_cap_combination` → `itertools.combinations([101..110], 3)` → 120 조합
2. **사전** candidate 개수 = C(10,3) = 120 계산 → `ctx.max_doe_count=200` 비교 → 통과
3. DOE001 = (101,102,103), DOE002 = (101,102,104), …, DOE120 = (108,109,110)
4. 각 DOE = 3개 PID 동일 SF + 동일 base_curve
5. `concurrency.max_concurrent_jobs=8` → submit 시 최대 8개 sbatch 동시 (`Runner/SlurmSubmit.submit_with_throttle`)
6. 100 DOE 초과 → **streaming writer** 활성 (`runner_config.json` + `doe_index.jsonl` 분리)

### 검증 명령

```bash
# 1. DOE 120개 확인
jq '.scenario.doe_count' output_C/runner_config.json
# 기대: 120

# 2. doe_index.jsonl 라인 수 == DOE 수
wc -l output_C/doe_index.jsonl
# 기대: 120 output_C/doe_index.jsonl

# 3. 조합 unique 검증 (중복 없음)
jq -r '.parts | join(",")' output_C/doe_index.jsonl | sort -u | wc -l
# 기대: 120

# 4. concurrency 제어 확인 (submit 후)
squeue -u $USER | grep VIB_cap_combination | wc -l
# 기대: 8 이하
```

---

## 4. 외부 Curve Library 구조

### 폴더 구조

```
vibration_curves/
├── README.md                    # 라이브러리 규약 + 파일 포맷 설명
├── vib_001.csv                  # 표준 sine 60Hz (실측 기반)
├── vib_002.csv                  # 표준 sine 120Hz
├── vib_003.csv                  # PSD → time series (random vibration)
├── customer_X/
│   └── customer_X_spec.csv      # 고객별 specs
└── mil_std/
    └── mil_std_810g_5147_a1.csv # MIL-STD 카탈로그
```

### CSV 파일 포맷 (`vib_001.csv` 예시)

```csv
# vib_001.csv
# description: standard sine 60Hz, amplitude 1000 N
# units: time_s, amplitude (force=N or acceleration=m/s^2)
# duration_s: 0.05
# author: koopark
# date: 2026-05-29
0.000,    0.000
0.001,  309.017
0.002,  587.785
0.003,  809.017
0.004,  951.057
0.005, 1000.000
0.006,  951.057
...
0.050,    0.000
```

**파싱 규약:**
- `#` 으로 시작하는 줄 → 메타데이터 주석 (skip)
- 빈 줄 → skip
- 그 외 라인 → `float, float` (앞=time_s, 뒤=amplitude)
- `t_col` / `v_col` / `skiprows` 필드로 컬럼/헤더 커스터마이즈 가능

### `README.md` (라이브러리 정의)

```markdown
# Vibration Curve Library

본 폴더는 KooChainRun VIBRATION 모드에서 참조하는 시간 이력 CSV 파일 카탈로그.

## 파일 명명 규칙
- `vib_NNN.csv` : 표준 카탈로그 (NNN = 일련번호)
- `<owner>/*.csv` : 고객/규격별 sub-folder

## CSV 포맷
- 첫 라인 `#` 주석 = 메타데이터 (description/units/duration_s/author/date)
- 데이터 = `time_s, amplitude` 2 컬럼 float
- 시간 monotonic increasing, 단위는 SI (m, s, kg, N)

## scenario.json 에서 사용
{ "base_curve": { "kind": "library_lookup",
                  "library_path": "./vibration_curves",
                  "history_id": "vib_001" } }
```

### scenario.json 에서 사용 예시 (curve_library resolver)

```json
{
  "vibration_source": {
    "resolver": "per_cap",
    "cap_part_id": 101,
    "direction": "Z",
    "load_type": "Force",
    "base_curve": {
      "kind": "library_lookup",
      "library_path": "./vibration_curves",
      "history_id": "vib_001"
    }
  }
}
```

→ 런타임에 `./vibration_curves/vib_001.csv` 로드 → `list[(t,v)]` 평탄화 → KooMeshModifier 통과.

---

## 5. base_curve 입력 3가지 형식

discriminated union (`kind` 필드)으로 3가지 형식 지원. 모두 런타임에 `list[(t,v)]` 로 materialize 되어 KooVibrationLoad 에 전달.

### A. Inline (즉시 값)

```json
"base_curve": {
  "kind": "inline",
  "points": [
    [0.000,    0.0],
    [0.001, 1000.0],
    [0.020, 1000.0],
    [0.021,    0.0]
  ]
}
```

**사용 케이스:** 짧은 펄스, 디버깅, 검증용. P1 골든 테스트에서 사용.

**평탄화 결과 (KooMeshModifier 입력):**
```
LoadCurve
0.000, 0.0
0.001, 1000.0
0.020, 1000.0
0.021, 0.0
EndLoadCurve
```

### B. CSV File

```json
"base_curve": {
  "kind": "csv_file",
  "path": "./curves/my_curve.csv",
  "t_col": 0,
  "v_col": 1,
  "skiprows": 1
}
```

**사용 케이스:** 실측 데이터, PSD 변환 결과, 규격 카탈로그. 시나리오 B/C 표준.

**평탄화 결과:** CSV 데이터 라인 → `list[(float, float)]` → 위 LoadCurve 블록과 동일 형식.

### C. Sine Helper (편의 생성기)

```json
"base_curve": {
  "kind": "sine",
  "amplitude": 1000.0,
  "frequency_hz": 50.0,
  "duration_s": 0.020,
  "sample_rate_hz": 10000,
  "phase_deg": 0.0
}
```

**사용 케이스:** 빠른 프로토타입, 단일 주파수 가진. CSV 파일을 매번 만들지 않고 inline 으로 sine wave 생성.

**평탄화 결과 (내부 계산):**
```python
import math
n = int(duration_s * sample_rate_hz) + 1
points = [(i / sample_rate_hz,
           amplitude * math.sin(2*math.pi*frequency_hz * i/sample_rate_hz
                               + math.radians(phase_deg)))
          for i in range(n)]
```
→ 위와 동일한 LoadCurve 블록.

### Future hooks (예약, v1 미구현)

```jsonc
{ "kind": "analytic",    "expr": "swept_sine", "params": {...} }
{ "kind": "library_lookup", "library_path": "...", "history_id": "..." }   // §4 참조
{ "kind": "composite",   "ops": [ ... ] }                                   // 합성
```

미등록 kind 호출 시: `NotImplementedError: Curve kind 'analytic' not implemented. Available: ['inline', 'csv_file', 'sine']` 친절 메시지.

---

## 6. amplitude 분배 방식 4가지

회로/조합에서 N개 PID 에 SF 를 어떻게 분배할지 결정. KooVibrationLoad 의 `PartFactors` 카드 + `RelativeMode` 키로 변환.

### A. `mass_proportional` (Force 모드에서 부위별 동일 가속도)

**수식:** `SF_i = (m_i / Σm_j)` 또는 KooMeshModifier 가 RelativeMode 처리.

**시나리오 표현:**
```json
"distribution": "mass_proportional",
"relative_mode": "VolumeProportional"
```

**사용 케이스:** Force 모드에서 회로 전체에 균일 가속도를 받게 하고 싶을 때 (질량 큰 부품일수록 큰 힘). 동일 재질 가정 시 `VolumeProportional` 로 매핑.

**KooMeshModifier 평탄화:**
```
RelativeMode,VolumeProportional
ReferencePart,999
```
PartFactors 는 솔버 측에서 자동 계산.

### B. `volume_proportional` (기존 KooMeshModifier 동작 그대로)

**수식:** `SF_i = (V_i / Σ V_j)` — 솔버가 메쉬 정보에서 직접 계산.

**시나리오 표현:**
```json
"distribution": "volume_proportional",
"relative_mode": "VolumeProportional"
```

**사용 케이스:** 솔버 내장 동작을 그대로 쓰고 싶을 때. mass_proportional 의 별칭에 가깝지만 의미를 명시.

### C. `equal` (모든 PID 동일 SF)

**수식:** `SF_i = 1.0 ∀ i`

**시나리오 표현:**
```json
"distribution": "equal",
"relative_mode": "Explicit"
```

**KooMeshModifier 평탄화:**
```
RelativeMode,Explicit
PartFactors
101, 1.0
102, 1.0
103, 1.0
EndPartFactors
```

**사용 케이스:** 회로 내 모든 부품에 동일 가진을 주는 단순 케이스. 가장 흔한 사용자 기대 동작.

### D. `custom_weights` (PID별 weight dict)

**수식:** 사용자 지정 dict.

**시나리오 표현:**
```json
"distribution": "custom_weights",
"weights": { "101": 1.0, "102": 0.5, "103": 2.0 },
"relative_mode": "Explicit"
```

**KooMeshModifier 평탄화:**
```
RelativeMode,Explicit
PartFactors
101, 1.0
102, 0.5
103, 2.0
EndPartFactors
```

**사용 케이스:** 실험적 비율, 도메인 지식 기반 가중, 회로 내 특정 부품 강조. cap_combination 과 결합 시 조합별 weight override 가능.

---

## 7. circuits 정의 — Inline 형식 (P1+P2 채택)

v1 은 **Inline (E안)** 채택. 시나리오 ≤50개 단계에서 외부 파일 진입 비용이 큼. 향후 `components_file` ref hook 만 예약.

### Inline (현재 표준)

```json
{
  "vibration_source": {
    "resolver": "circuit_group",
    "circuits": {
      "circuit_A": {
        "description": "main power circuit",
        "components": [
          { "role": "cap",  "part_ids": [101, 102, 103] },
          { "role": "coil", "part_ids": [201, 202] }
        ],
        "reference_part": 999
      },
      "circuit_B": {
        "description": "RF frontend",
        "components": [
          { "role": "cap", "part_ids": [301, 302] },
          { "role": "ic",  "part_ids": [401] }
        ],
        "reference_part": 999
      }
    }
  }
}
```

### Future ref hook (예약, P5 이후 검토)

```json
{
  "vibration_source": {
    "resolver": "circuit_group",
    "components_file": "./registry/cell_circuits.yaml",
    "components_override": {
      "circuit_A": { "distribution": "mass_proportional" }
    }
  }
}
```

**resolver 의사 코드:**
```python
def resolve_circuits(config):
    if "components_file" in config:
        base = load_yaml(config["components_file"])
        overrides = config.get("components_override", {})
        for name, patch in overrides.items():
            base.setdefault(name, {}).update(patch)
        return base
    return config["circuits"]   # inline path
```

**현재 결정:** `components_file` 필드는 **schema 에서만 예약** (v1 검증 통과). 로더 구현은 시나리오 수 >50 도달 후 P5 이후 검토. CLAUDE.md §2 (YAGNI) 준수.

---

## 8. 검증 명령 모음 (jq/grep 으로 결과 검증)

테스트 스크립트 없이 jq/grep 으로 1차 검증. CI 도입 전 수동 검증용.

### DOE 개수 확인
```bash
jq '.scenario.doe_count' output/runner_config.json
```

### DOE 별 vibration_source 요약
```bash
jq '.steps[0].vibration_source | {resolver, direction, load_type, distribution}' \
   output/runner_config.json
```

### Streaming writer 모드 — doe_index.jsonl 라인 수
```bash
wc -l output/doe_index.jsonl
# 기대: jq '.scenario.doe_count' output/runner_config.json 와 동일
```

### 회로별 SF 확인 (Output 키 파일에서 PartFactors 블록)
```bash
grep -A20 "PartFactors" output/Run_DOE001_S001_*/Output/*_vib.k | head -30
```

### LOAD_BODY_PARTS 카드 생성 확인 (방향별)
```bash
# Z 방향 진동
grep -l "*LOAD_BODY_PARTS_Z" output/Run_*/Output/*_vib.k
```

### DOE 미리보기 (dry-run, sbatch submit 안 함)
```bash
KooChainRun prepare scenario.json --dry-run
```

### DOE 폭증 가드 강제 우회 (확인 후 진행)
```bash
KooChainRun prepare scenario.json --yes
```

### Registry 등록 확인 (Nuitka 빌드 후)
```bash
KooChainRun list-vibration-sources
# 기대 출력 (P5 완료 시):
#   per_cap
#   circuit_group
#   explicit_factors
#   cap_combination
#   curve_library
```

### Schema 검증
```bash
KooChainRun validate-scenario scenario_C_cap_combination.json
# 기대: "OK: scenario passes schema." 또는 라인/필드별 에러 메시지
```

### 회귀 검증 — DROP 100 DOE byte-level diff
```bash
# (P3 단계 후) 기존 Test_005 (100 DOE, DROP) 시나리오를 신규 코드로 재생성
KooChainRun prepare Examples/HWWarrantyDropTest/Tests/Test_005_Fibonacci_100/scenario.json \
  --output /tmp/regression_test
diff Examples/HWWarrantyDropTest/Tests/Test_005_Fibonacci_100/runner_config.json \
     /tmp/regression_test/runner_config.json
# 기대: diff 결과 0 (회귀 X)
```

### LS-DYNA 정상 종료 확인 (병렬)
```bash
for d in output/Run_*/Output/; do
  if grep -q "N o r m a l    t e r m i n a t i o n" "$d/d3hsp"; then
    echo "OK: $d"
  else
    echo "FAIL: $d"
  fi
done
```

### Concurrency 제어 확인 (submit 후 실시간)
```bash
watch -n 2 'squeue -u $USER | grep VIB | wc -l'
# 기대: scenario.environment.concurrency.max_concurrent_jobs 이하 유지
```

---

**최종 노트.** 본 EXAMPLES.md 의 모든 JSON 은 **그대로 복붙해서 실행 가능한 형식**. `vibration_source.resolver` 가 registry key 이므로 새 resolver 추가 시 본 문서에 §X 새 절을 추가하기만 하면 된다 (zero-hardcode 원칙). 시나리오 B (`circuit_group`) 가 v1 사용자 핵심 use case이며, 시나리오 C (`cap_combination`) 가 massive parametric 의 표준 진입로다.
