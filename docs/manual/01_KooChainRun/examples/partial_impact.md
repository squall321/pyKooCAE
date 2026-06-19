# 예제: 전위치 부분충격 (IMPACT)

## 1. 목적 / 개요

제품 표면의 여러 위치에 동일한 충격추(impactor)를 떨어뜨려 위치별 응력/거동을 평가하는 **전위치 부분충격 DOE** 예제이다. 충격 위치를 `grid_nxm` 으로 14x10 = 140 점으로 펼친 뒤, 각 위치마다 독립 LS-DYNA 충격 해석을 수행하고, per-job 후처리(deep_report) 후 d3plot 을 삭제하여 디스크를 절약하고, 마지막에 전위치 결과를 `impact_report` 로 통합한다.

충격추는 **3단 실린더**(고무팁 front + ⌀20 SUS mid + ⌀44.5 SUS 본체 back)로 구성하여 실제 충격추의 질량/강성/충돌 거동을 근사한다. KooMeshModifier 의 `DROP_WEIGHT_IMPACT_TEST` 모드가 모델에 Impactor 파트와 Wall(받침) 파트를 자동 생성한다.

근거 예제 파일:
- 3단 실린더 시나리오: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/scenario_examples/impact_cylinder_8pi.json`
- 2단 실린더 시나리오: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/scenario_examples/impact_cylinder_15pi.json`
- 실행/제출 스크립트: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/ImpactTest/Tests/Test_Impact_Grid5x5/run.sh`
- IMPACT deck 생성 로직: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Runner/CumulativeScenarioRunner.py`

처리 흐름:

```
scenario.json (grid 14x10 + cylinder_stages 3단 + postprocess)
   │  KooChainRun prepare
   ▼
runner_config.json  (각 grid 점 → 1개 DOE, 총 140 DOE)
   │  KooChainRun submit (Slurm 병렬)
   ▼
DOE별 Run_*  (KooMeshModifier IMPACT deck → LS-DYNA → d3plot)
   │  auto_deep=inline : per-job koo_deep_report → report/ 생성
   │  delete_d3plot_after_deep=true : deep 성공 시 d3plot 삭제
   ▼
전 DOE 종료 후 dependent job : koo_impact_report (report/ 만 읽어 통합)
   ▼
output/impact_report.html + impact_report.json
```

---

## 2. 입력 옵션 · 인자 (표)

### `simulation_params.impact` (충격추)

| 키 | 형식 | 설명 | 코드 근거 |
|---|---|---|---|
| `type` | str | 충격추 형상. 실린더는 `"cylinder"` (대소문자 무관) | CumulativeScenarioRunner.py:1213,1217 |
| `height` | float | 낙하 높이 → `Height` 카드 | CumulativeScenarioRunner.py:1258 |
| `mesh_size` | float | 충격추/Wall 메쉬 크기 → `MeshSize` | CumulativeScenarioRunner.py:1264 |
| `tFinal` | float | 해석 종료 시간 → `tFinal` | CumulativeScenarioRunner.py:1275 |
| `dt` | float | 시간증분 → `dt` | CumulativeScenarioRunner.py:1276 |
| `offset_distance` | float | 충격추 초기 이격거리 → `OffsetDistance` | CumulativeScenarioRunner.py:1277 |
| `cylinder_stages` | list | 실린더 단(stage) 목록 `[front, (mid), back]`. 2단 또는 3단 | CumulativeScenarioRunner.py:1212,1217 |
| `dimension_damper` | list | 댐퍼 치수 `[x,y,z]` → `DimensionDamper` (기본 `[0.001,0.001,0.001]`) | CumulativeScenarioRunner.py:1204-1205 |
| `density` / `youngs_modulus` / `poisson_ratio` | float | 단순 형상(Sphere 등) 충격추 재질 → `DensityImpactor` 등 | CumulativeScenarioRunner.py:1266-1268 |

### `cylinder_stages[]` 각 단(stage)

| 키 | 형식 | 설명 | 코드 근거 |
|---|---|---|---|
| `role` | str | 단 역할 라벨 `front`/`mid`/`back` (배열 순서로 처리, 라벨 자체는 미사용) | impact_cylinder_8pi.json:39,48,56 |
| `diameter` | float | 단 직경. 반경 = 직경/2 로 변환됨 | CumulativeScenarioRunner.py:1220-1222 |
| `outer_diameter` | float | front 단 전용. 평탄부(`diameter`)→필렛 후 외경. 미지정 시 `diameter` 사용 | CumulativeScenarioRunner.py:1221 |
| `height` | float | 단 높이 | CumulativeScenarioRunner.py:1224,1226,1230 |
| `density` / `youngs_modulus` / `poisson` | float | 단별 재질. front/mid 는 별도 카드(`*ImpactorFront`/`*ImpactorMid`)로 직렬화 | CumulativeScenarioRunner.py:1233-1235,1241-1243 |

> dimension 직렬화 규칙 (CumulativeScenarioRunner.py:1210, 1231/1238):
> - **3단**: `[radius, outerRadius, hFront, midRadius, hMid, backRadius, hBack]` (값 7개)
> - **2단**: `[radius, outerRadius, hFront, hBack, backRadius]` (값 5개)
> 여기서 radius = front.diameter/2, outerRadius = front.outer_diameter/2, backRadius = back.diameter/2.

### `simulation_params.wall` (받침판)

| 키 | 형식 | 설명 | 코드 근거 |
|---|---|---|---|
| `density` / `youngs_modulus` / `poisson_ratio` | float | Wall 재질 → `DensityWall` 등 (기본 `1e-9`/`1e4`/`0.3`) | CumulativeScenarioRunner.py:1269-1271 |
| `num_x` / `num_y` / `num_z` | int | Wall 분할 수 → `WallNumX/Y/Z` (기본 각 10) | CumulativeScenarioRunner.py:1272-1274 |

### `scenarios[].position_source` (충격 위치 DOE)

| 키 | 형식 | 설명 | 코드 근거 |
|---|---|---|---|
| `source_type` | str | `"grid_nxm"` / `"grid_spacing"` / `"manual"` | ImpactPositionSource.py:218,230-243 |
| `grid_nxm.nx` / `grid_nxm.ny` | int | X/Y 방향 격자 점 수 (기본 5/5) | ImpactPositionSource.py:100-101 |
| `grid_nxm.bbox` | list | `[xmin, ymin, xmax, ymax]`. 미지정 시 모델 .k 의 *NODE 에서 자동 계산 | ImpactPositionSource.py:102-107, 224-226 |

> 위치 이름은 `P_{row:03d}_{col:03d}` 형식이며, 각 위치가 1개 DOE(1-based)로 매핑된다 (ImpactPositionSource.py:122, CumulativeDesigner.py:726-738). 따라서 14x10 grid → 140 DOE.

### `postprocess` (후처리)

| 키 | 형식 | 설명 | 코드 근거 |
|---|---|---|---|
| `enabled` | bool | 후처리 자동 실행 on/off | CumulativeScenarioRunner.py:708, SlurmSubmitter.py:112 |
| `sif_path` | str | SmartTwinPostprocessor.sif 경로 | PostprocessShellGenerator.py:75,255 |
| `auto_deep` | bool | per-job deep_report 자동 실행 (기본 true) | CumulativeScenarioRunner.py:708 |
| `auto_deep_mode` | str | `"inline"`(잡 내 실행, 기본) / `"separate_job"`(별도 sbatch) | CumulativeScenarioRunner.py:711-713 |
| `delete_d3plot_after_deep` | bool | deep 성공 시 d3plot 삭제 (기본 false) | PostprocessShellGenerator.py:93-100 |
| `auto_impact` | bool | 전위치 통합 impact_report 자동 실행 (기본 true) | SlurmSubmitter.py:124-130 |

---

## 3. 사용 예제

### 3.1 3단 실린더 충격추 (8파이) — `simulation_params.impact` 발췌

`Examples/scenario_examples/impact_cylinder_8pi.json` 발췌 (3단: 고무팁 front + ⌀20 SUS mid + ⌀44.5 SUS back):

```json
"impact": {
  "type": "cylinder",
  "height": 200,
  "mesh_size": 2,
  "tFinal": 0.001,
  "dt": 1e-06,
  "offset_distance": 0.01,
  "cylinder_stages": [
    { "role": "front", "diameter": 8,    "outer_diameter": 20, "height": 6,
      "density": 1.18e-09, "youngs_modulus": 100.0,    "poisson": 0.49 },
    { "role": "mid",   "diameter": 20,   "height": 14,
      "density": 6.57e-09, "youngs_modulus": 207000.0, "poisson": 0.3  },
    { "role": "back",  "diameter": 44.5, "height": 38.003,
      "density": 6.57e-09, "youngs_modulus": 207000.0, "poisson": 0.3  }
  ]
}
```

### 3.2 grid 14x10 위치 DOE + postprocess — 시나리오 발췌

```json
"postprocess": {
  "enabled": true,
  "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
  "auto_deep": true,
  "auto_deep_mode": "inline",
  "delete_d3plot_after_deep": true,
  "auto_impact": true
},
"scenarios": [
  {
    "scenario_name": "Cyl8pi_grid14x10",
    "template": "NM4_DV1.k",
    "position_source": {
      "source_type": "grid_nxm",
      "grid_nxm": {
        "nx": 14, "ny": 10,
        "bbox": [-31.628, 114.045, 31.628, 155.068]
      }
    },
    "cumulative": {
      "num_steps": 1,
      "mode_sequence": ["IMPACT"]
    }
  }
]
```

> 단위계는 ton-mm-s (직경 mm, 밀도 ton/mm³, E MPa). 모든 dimensional 입력은 모델 deck(.k) 단위계와 반드시 일치해야 한다 (impact_cylinder_8pi.json:3, impact_example.json:1).

### 3.3 2단 실린더 (15파이) — front+back 만 사용

`impact_cylinder_15pi.json` 은 mid 단을 생략한 2단 구성이다. front 의 평탄부 ⌀15 → 필렛 후 외경 ⌀44.5 를 `outer_diameter` 로 표현한다:

```json
"cylinder_stages": [
  { "role": "front", "diameter": 15,   "outer_diameter": 44.5, "height": 15,
    "density": 6.854e-09, "youngs_modulus": 207000.0, "poisson": 0.3 },
  { "role": "back",  "diameter": 44.5, "height": 45.01,
    "density": 6.854e-09, "youngs_modulus": 207000.0, "poisson": 0.3 }
]
```

### 3.4 실행 (run.sh)

`Examples/ImpactTest/Tests/Test_Impact_Grid5x5/run.sh` 가 표준 실행 흐름이다. 내부적으로 `prepare` → `submit` 두 단계를 호출한다 (run.sh:37, 65-68):

```bash
# 디폴트: --nodes 2 --jobs-per-node 2 --ncpu-per-job 1
./run.sh

# 동시 실행 수 조절 (예: 10노드 x 4잡 = 40 병렬)
./run.sh --nodes 10 --jobs-per-node 4 --ncpu-per-job 1
```

run.sh 가 수행하는 명령 (직접 호출 등가):

```bash
# Step 1: scenario.json → runner_config.json
KooChainRun prepare scenario.json -o runner_config.json

# Step 2: Slurm 제출
KooChainRun submit runner_config.json \
    --nodes 2 --jobs-per-node 2 --ncpu-per-job 1
```

(submit 인자 형식은 컴파일된 `KooChainRun` 바이너리 usage 와 일치: `KooChainRun submit runner_config.json --nodes 10 --jobs-per-node 4 --ncpu-per-job 16`.)

제출 후 작업 관리 (run.sh:75-79):

```bash
./stop.sh                  # 전체 취소
./rerun.sh --dry-run       # 상태 확인
./rerun.sh                 # 실패 재실행
KooChainRun diagnose <test_dir>   # 실패 진단
```

---

## 4. 동작 원리 (코드 근거)

### 4.1 충격 위치 DOE 전개

`grid_nxm` 은 bbox 를 nx x ny 균등 격자로 펼친다 (ImpactPositionSource.py:110-123). bbox 미지정 시 모델 .k 의 *NODE 섹션 X-Y 바운딩박스를 fixed-width 파싱으로 자동 계산한다 (ImpactPositionSource.py:24-76, 224-226). 각 위치는 `ImpactPosition(name, x, y)` 가 되고(ImpactPositionSource.py:79-85), CumulativeDesigner 가 위치마다 1-based DOE 키로 `doe_positions` 에 직렬화한다 (CumulativeDesigner.py:726-738). 즉 14x10 격자는 140개 독립 DOE 가 된다.

### 4.2 IMPACT deck (KooMeshModifier 입력) 생성

DOE/step 별로 `mode == "IMPACT"` 분기에서 KooMeshModifier 설정을 만든다 (CumulativeScenarioRunner.py:1196-1280). 해당 위치(x,y)를 `LocationX/LocationY` 로 넣고 `DROP_WEIGHT_IMPACT_TEST` 모드 + `GenerationMode,DampingSpring` 헤더를 출력한다 (CumulativeScenarioRunner.py:1252-1256).

실린더 3단 처리 (CumulativeScenarioRunner.py:1217-1244):
- `type` 이 cylinder 이고 `cylinder_stages` 가 있으면, front=stages[0], back=stages[-1] 로 잡고 반경 변환(직경/2)을 수행한다 (1218-1226).
- 3단(len>=3)이면 mid=stages[1] 을 추가하여 dimension 7값 직렬화 + `DensityImpactorMid`/`YoungsModulusImpactorMid`/`PoissonRatioImpactorMid` 라인을 만든다 (1227-1236).
- 2단이면 dimension 5값으로 직렬화한다 (1237-1238).
- front 재질은 항상 `DensityImpactorFront`/`YoungsModulusImpactorFront`/`PoissonRatioImpactorFront` 로 별도 직렬화한다 (1240-1244).

직렬화된 `dimension_str` 와 front/mid 재질 블록은 `Dimension,...` 및 그 직후 라인에 삽입된다 (CumulativeScenarioRunner.py:1263, 1269). Wall 파트는 `DensityWall`/`WallNumX/Y/Z` 등으로 함께 생성된다 (1269-1274).

### 4.3 per-job 후처리 + d3plot 삭제

각 Run 종료 후 `build_deep_report_sh` 로 `deep_report.sh` 를 항상 생성하고, `postprocess.enabled && auto_deep` 이면 자동 실행한다 (CumulativeScenarioRunner.py:687-708). 기본 모드 `inline` 은 시뮬 잡 안에서 `bash deep_report.sh` 를 직접 돌린다 (CumulativeScenarioRunner.py:711-728).

`delete_d3plot_after_deep=true` 면 deep_report.sh 끝에 d3plot 삭제 블록이 붙는다 (PostprocessShellGenerator.py:93-100). 스크립트가 `set -e` 이므로 `koo_deep_report` 가 성공해 삭제 줄까지 도달했을 때만 삭제되고, 실패 시 d3plot 은 보존된다 (PostprocessShellGenerator.py:88-92, 99). impact aggregate 는 `report/` 만 읽으므로 d3plot 삭제의 영향을 받지 않는다 (impact_cylinder_8pi.json:74 주석, PostprocessShellGenerator.py:90-92).

### 4.4 전위치 통합 impact_report

전 DOE 종료 후 dependent Slurm job 으로 종합 리포트를 제출한다 (SlurmSubmitter.py:99, 103-175). 리포트 모드는 step mode 로 판정하며, 모든 step 이 IMPACT 이면 `"IMPACT"` 를 반환한다 (PostprocessShellGenerator.py:300-327). IMPACT 이고 `auto_impact != false` 이면 `build_impact_sbatch` 로 impact_report 잡을 제출한다 (SlurmSubmitter.py:124-130).

`impact_report.sh` 는 `test_dir = output_dir 의 parent` 를 잡아 `koo_impact_report --test-dir ... --format html json` 을 실행한다 (PostprocessShellGenerator.py:270-294). flat-DOE 경로(`load_partial_impact_doe_report`)가 Run 마다 unified_analyzer 를 직접 돌리므로 sphere_report 같은 symlink dance 가 없다 (PostprocessShellGenerator.py:234-238). 결과는 `output/impact_report.html` + `impact_report.json` 이다 (PostprocessShellGenerator.py:274-275).

---

## 5. 주의사항 · 한계

- **d3plot 삭제는 복구 불가**: `delete_d3plot_after_deep=true` 는 디스크 절약용이나 원본 결과를 영구 삭제한다. 첫 운영 전 1~2 잡으로 검증 권장 (impact_cylinder_8pi.json:74 주석).
- **단위계 일관성**: impact/wall 의 모든 dimensional 입력은 모델 deck(.k)와 동일한 단위계여야 한다. 예제는 ton-mm-s. 과거 Runner 의 키 mismatch 로 SI default 가 silent 하게 박혀 단위 혼용 deck 이 생성되던 버그가 있었다 (impact_example.json:5 fix_history 주석).
- **delete + 통합 의존**: d3plot 을 삭제하므로 `koo_impact_report` 는 d3plot 부재 시 deep output 재사용(force_reuse)을 지원해야 한다 (PostprocessShellGenerator.py:90-93 주석). 통합 단계에서 deep output 의존이 깨지면 결과 누락 가능 — **확인 필요**.
- **구버전 SIF**: SIF 에 `koo_impact_report` 가 없으면(2.3.x 이전) 통합 리포트는 경고 후 skip 된다 (PostprocessShellGenerator.py:282-286).
- **cylinder_stages 라벨**: `role` 값은 라벨일 뿐 배열 순서(`[0]`=front, `[-1]`=back, `[1]`=mid)로 처리된다. 단 순서를 잘못 주면 의도와 다르게 직렬화된다 (CumulativeScenarioRunner.py:1218-1230).
- **run.sh 대화형 확인**: run.sh 는 제출 전 `y/n` 확인을 받는다 (run.sh:55-60). 무인 자동화 시 우회 입력이 필요하다.
- **CLI 인자 근거**: submit 의 `--nodes`/`--jobs-per-node`/`--ncpu-per-job` 인자는 run.sh(검증됨) 및 컴파일된 `KooChainRun` 바이너리 usage 문자열에서 확인했다. 메인 CLI 의 argparse 파이썬 소스(`KooChainRun.py`)는 본 트리에 포함되어 있지 않다(컴파일 바이너리만 존재) — 인자 기본값/help 텍스트의 정확한 file:line 근거는 **확인 필요**.

---

## 6. 개발 현황

**구현됨.**

근거:
- IMPACT deck 생성 + 실린더 2/3단 직렬화 + front/mid 재질 블록: CumulativeScenarioRunner.py:1196-1280 (실제 코드 경로 존재).
- grid_nxm 위치 DOE 전개: ImpactPositionSource.py:87-125, CumulativeDesigner.py:726-738.
- per-job deep_report + d3plot 삭제 + 전위치 impact_report 라우팅: PostprocessShellGenerator.py:57-327, SlurmSubmitter.py:103-175, CumulativeScenarioRunner.py:687-728.
- 실행 스크립트(run.sh): Examples/ImpactTest/Tests/Test_Impact_Grid5x5/run.sh 존재.
- e2e 시나리오 파일: impact_cylinder_8pi.json(3단), impact_cylinder_15pi.json(2단) 존재.

최근 커밋 메시지(`feat(thermal, impact): ... 3단 실린더 충격추 ...`, `feat(postprocess): wire IMPACT report into chainrun (auto_impact) ...`)도 이 기능이 통합되었음을 뒷받침한다. 단, 본 트리에서 140-DOE 규모 e2e 실행 로그는 확인하지 못했다 — 통합 동작의 대규모 검증 여부는 **확인 필요**.
