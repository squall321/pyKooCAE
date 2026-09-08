# 후처리 현장 가이드 — `scenario.json` 하나로 끝내기

실제 계산 노드에서 쓰는 것을 전제로 한 실무 문서.
설계 배경과 코드 근거는 [postprocess.md](postprocess.md) 참조.

**기준 SIF**: `SmartTwinPostprocessor.sif` (2026-09-08 빌드, node001 배포 확인)
아래 옵션 목록은 그 SIF에서 `--help` 로 직접 뽑은 것이다.

---

## 0. 시작 전 30초 점검

새 옵션을 넣기 전에 **노드의 SIF가 그 옵션을 아는지** 반드시 확인한다.

```bash
ssh node001 'apptainer exec /opt/apptainers/SmartTwinPostprocessor.sif \
  python3 -m koo_deep_report --help' | grep hotspot
```

🔴 **이 확인을 건너뛰면 리포트가 통째로 날아간다.**
`deep_extra_args` 는 검증 없이 명령에 붙는다. 구버전 SIF가 모르는 인자를 받으면
argparse 가 `unrecognized arguments` 로 exit 2 를 내고, `deep_report.sh` 가
`set -e` 라 그 즉시 전체가 실패한다. 해석은 다 돌았는데 리포트만 없는 상태가 된다.

**`/opt/apptainers` 는 노드 로컬이라 노드마다 버전이 다를 수 있다.**
2026-09-08 기준 새 SIF가 올라간 것은 **node001 뿐**이다.

---

## 1. 그대로 쓰는 블록

```json
"postprocess": {
  "enabled": true,
  "auto_deep": true,
  "auto_sphere": true,
  "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
  "yield_stress_mpa": 350,

  "section_view_mode": "section",
  "section_view_axes": ["z"],
  "section_view_fields": ["von_mises", "strain"],

  "deep_extra_args": [
    "--hotspot-clusters",
    "--hotspot-top-percent", "3.0",
    "--section-view-target-patterns", "*interposer*", "*pcb*",
    "--section-view-fade", "2.0"
  ],

  "ua_threads": 8,
  "sv_threads": 8,
  "deep_memory": "16G",
  "deep_time_limit": "02:00:00",
  "sphere_memory": "32G",
  "sphere_time_limit": "04:00:00"
}
```

이 블록이 만드는 실제 명령.

```
apptainer exec --bind /data:/data,"$RUN_DIR":"$RUN_DIR" \
    "$SIF_PATH" python3 -m koo_deep_report "$RUN_DIR" \
    -o "$REPORT_DIR" \
    --section-view \
    --section-view-backend software \
    --section-view-mode section \
    --section-view-axes z \
    --section-view-fields von_mises strain \
    --ua-threads 8 \
    --sv-threads 8 \
    --hotspot-clusters --hotspot-top-percent 3.0 --section-view-target-patterns '*interposer*' '*pcb*' --section-view-fade 2.0
```

통과 인자(`deep_extra_args`)가 **맨 뒤**에 붙는 것을 확인할 수 있다 —
그래서 앞의 고정 플래그를 덮어쓸 수 있다.

---

## 2. 전용 키 (21개)

`postprocess` 블록에 바로 쓰는 키. 나머지는 §3 통과 인자로 넣는다.

### 스위치

| 키 | 기본 | 뜻 |
|---|---|---|
| `enabled` | — | 마스터 스위치. 없으면 후처리 자체를 안 함 |
| `auto_deep` | `true` | 케이스별 deep_report |
| `auto_sphere` | `true` | 종합 sphere_report (DROP 시나리오) |
| `auto_impact` | `true` | 종합 impact_report (IMPACT 시나리오) |
| `auto_deep_mode` | `inline` | `inline` 또는 `separate_job` |
| `sif_path` | `/opt/apptainers/SmartTwinPostprocessor.sif` | 후처리 SIF |

### 공통

| 키 | 기본 | 뜻 |
|---|---|---|
| `yield_stress_mpa` | 350 | 항복 기준 (MPa) |
| `ua_threads` | 8 | 분석 스레드 |
| `sv_threads` | 8 | 단면 뷰 렌더 스레드 |
| `delete_d3plot_after_deep` | `false` | deep 성공 후 d3plot 삭제 (디스크 절약) |
| `deep_timeout_seconds` | 7200 | deep 실행 상한 |

### 단면 뷰

| 키 | 기본 | 값 |
|---|---|---|
| `section_view_mode` | `section` | `section` / `section_3d` / `iso_surface` |
| `section_view_axes` | `["z"]` | `x` `y` `z` — **자르는 평면의 법선** |
| `section_view_fields` | `["von_mises"]` | `von_mises` `strain` `eps` `displacement` `pressure` `max_shear` |

**축 ↔ 보이는 평면**

| 지정 | 단면 |
|---|---|
| `z` | **XY 평면** |
| `y` | XZ 평면 |
| `x` | YZ 평면 |

**필드 뜻** — `strain` = 총변형률(변위 기반), `eps` = 소성변형률.

### 자원 (Slurm)

`deep_` / `sphere_` / `impact_` 접두사에 각각 붙는다.
**미지정 시 `environment` 블록을 먼저 보고, 거기에도 없으면 아래 기본값을 쓴다.**

| 키 | 폴백 순서 → 기본값 |
|---|---|
| `deep_ncpu` | `environment.ncpu` → **1** |
| `deep_memory` | `environment.memory` → **8G** |
| `deep_time_limit` | `deep_timeout_seconds + 600초` 를 환산 |
| `sphere_ncpu` | `environment.sphere_ncpu` → `environment.ncpu` → **8** |
| `sphere_memory` | `environment.sphere_memory` → `environment.memory` → **16G** |
| `sphere_time_limit` | `environment.sphere_time_limit` → **04:00:00** |
| `impact_ncpu` / `impact_memory` / `impact_time_limit` | sphere 와 동일 구조 |

`_partition` 은 시나리오의 `environment.partition` 을 따른다.
`impact_yield_stress` 는 impact 전용 항복 기준(미지정 시 `yield_stress_mpa`).

⚠️ **`deep_ncpu` 기본이 1이다.** `environment.ncpu` 가 1이면 deep 잡도 1코어로
돌아 `ua_threads: 8` 을 줘도 실효가 없다. 무거운 덱이면 `deep_ncpu` 를 명시할 것.

---

## 3. 통과 인자 — 전용 키가 없는 모든 옵션

세 리포트에 각각 임의 인자를 넘길 수 있다.

| 키 | 대상 |
|---|---|
| `deep_extra_args` | `koo_deep_report` |
| `sphere_extra_args` | `koo_sphere_report` |
| `impact_extra_args` | `koo_impact_report` |

**고정 플래그 뒤에 붙으므로 기본값을 덮어쓸 수도 있다.**
리스트로 주면 각 원소가 셸 이스케이프된다(공백·와일드카드 안전).

```json
"deep_extra_args": ["--section-view-target-patterns", "*interposer*", "*pcb*"]
```

### 배포된 SIF의 실제 옵션

**`koo_deep_report`** — 아래가 전부다.

```
--hotspot-clusters --hotspot-top-percent --hotspot-distance-factor
--hotspot-min-elements --hotspot-max-clusters
--section-view --section-view-backend --section-view-mode --section-view-axes
--section-view-fields --section-view-target-ids --section-view-target-patterns
--section-view-fade --section-view-per-part --no-section-view-per-part
--section-view-iso-clip --no-section-view-iso-clip --section-view-iso-clip-margin
--section-view-section-position --section-view-section-margin
--section-view-reverse-cut --no-section-view-reverse-cut
--section-view-sliding --section-view-sliding-steps --section-view-sliding-pad
--section-view-sliding-near-to-far --section-view-sliding-far-to-near
--section-view-sliding-peak-time --section-view-sliding-freeze-time
--section-view-sliding-iso-style --no-section-view-sliding-iso-style
--section-view-sliding-section-style --no-section-view-sliding-section-style
--section-view-background-alpha --section-view-edge-width --section-view-crf
--parts --part-pattern --per-part-render --element-quality
--yield-stress --strain-limit --design-overrides --material-overrides
--ua-threads --sv-threads --render-threads --no-render
--config --install-dir --label --output --verbose
```

**`koo_sphere_report`**

```
--test-dir --json --output --format --from-json
--yield-stress --ts-points --terminal-only
```

**`koo_impact_report`**

```
--test-dir --json --output --format --from-json --single-file
--yield-stress --stress-limit --g-limit --units
--threshold-warning --threshold-critical --faces
--threads-per-run --parallel-runs --chunked
--no-cache --refresh-cache
```

---

## 4. 핫스팟 군집

파트별로 상위 X% 요소를 공간 군집화해 **덩어리 단위**로 보고한다.
"집중이 한 곳에 뭉쳤나 여러 군데 흩어졌나", "어디에 얼마나 큰 범위로 있나"를 답한다.

| 옵션 | 기본 | 뜻 |
|---|---|---|
| `--hotspot-clusters` | 꺼짐 | 활성화 |
| `--hotspot-top-percent` | 5.0 | 파트별 상위 백분위 (%) |
| `--hotspot-distance-factor` | 1.5 | 거리 임계 = 이 값 × 파트 대표 요소 크기 |
| `--hotspot-min-elements` | 5 | 이 개수 미만 덩어리는 노이즈로 버림 |
| `--hotspot-max-clusters` | 20 | 파트당 보고 최대 덩어리 (0=무제한) |

`analysis_result.json` 의 `hotspot_clusters` 에 나온다.

```json
{
  "part_id": 100, "part_name": "Part_100",
  "element_count_total": 1152, "element_count_selected": 34,
  "element_count_clustered": 26,
  "element_size_ref": 2.249, "distance_threshold": 3.373,
  "threshold_value": 1.503, "strain_available": true,
  "clusters": [
    { "rank": 1, "element_count": 14,
      "center": [73.356, 107.500, 0.693],
      "radius_enclosing": 5.867, "radius_rms": 2.636, "volume": 168.3,
      "stress_mean": 2.095, "stress_max": 2.983,
      "strain_mean": 8.65e-06, "strain_max": 1.231e-05,
      "peak_element_id": 13212, "peak_time": 0.00099999 }
  ]
}
```

| 필드 | 뜻 |
|---|---|
| `center` | 응력×부피 가중 중심. **초기 형상 기준** |
| `radius_enclosing` | 중심 → 구성 요소의 **최원 절점**. 덩어리 실제 크기 |
| `radius_rms` | 부피 가중 RMS 반경. **뭉침 정도** — 포함반경보다 훨씬 작으면 한 점 집중 |
| `stress_mean` | **부피 가중** 평균 (산술평균 아님) |

### 🔴 `top_percent` 를 실제 집중 범위에 맞출 것

**상위 X% 는 "컷 이상 전부"가 아니라 정확히 N개다.**
N 이 진짜 집중된 요소 수보다 크면 **배경 요소가 딸려 들어와 평균이 희석된다.**

요소 180개 파트에서 실제 집중부가 3개인데 `top_percent: 5` 를 주면 9개가 뽑히고
그중 6개가 배경이다. 배경이 집중부에 인접하면 같은 덩어리로 묶여 `stress_mean` 이 급락한다.

**판단법** — `stress_mean` 이 `stress_max` 대비 지나치게 낮으면 `top_percent` 를 줄인다.
보통 **1~5%** 가 적정.

### `distance_factor` 감

거리 임계 = `distance_factor × 파트 대표 요소 크기`(부피 중앙값의 세제곱근).
메시 밀도가 다른 파트에도 자동 적응한다.

| 값 | 효과 |
|---|---|
| < 1.0 | 인접 요소도 안 묶임 — 잘게 쪼개짐 |
| **1.5** | 붙은 요소는 묶고 한 칸 건너뛴 것은 분리 |
| > 3.0 | 떨어진 집중부가 하나로 합쳐짐 |

---

## 5. 특정 파트만 단면 뷰

파트 이름 매칭은 **대소문자를 구분하지 않는다**(패턴·파트명 양쪽을 소문자로 내려 비교).
`*INTERPOSER*` 든 `*interposer*` 든 `Interposer_Top` 을 잡는다.

```json
"deep_extra_args": [
  "--section-view-target-patterns", "*interposer*", "*pcb*",
  "--section-view-fade", "2.0"
]
```

패턴을 여러 개 나열하면 **OR** 로 묶인다.

| 옵션 | 용도 |
|---|---|
| `--section-view-target-ids` | 파트 ID 직접 지정 |
| `--section-view-target-patterns` | 이름 패턴 (glob) |
| `--section-view-fade` | 비타겟 파트를 거리별 반투명 (0=단색) |
| `--section-view-per-part` | 파트별로 단면을 따로 뽑음 (타겟 미지정 시 자동 ON) |

⚠️ `*pcb*` 는 `Main_PCB_Bracket`, `PCB_Screw` 같은 것도 잡는다.
의도보다 많이 잡히면 패턴을 좁히거나 파트 ID로 지정한다.

---

## 6. 리포트 종류는 자동 판정

`auto_sphere: true` 를 줘도 **IMPACT 시나리오면 sphere 는 안 돈다.**

| `mode_sequence` | 도는 것 |
|---|---|
| 전 스텝 `DROP` | sphere_report (`auto_sphere` 확인) |
| 전 스텝 `IMPACT` | impact_report (`auto_impact` 확인) |
| 혼합 | 첫 스텝 모드 |
| `mode: "drop_weight_impact"` | impact (최우선) |

둘 다 돌지는 않는다.

---

## 7. 문제 해결

| 증상 | 원인 · 조치 |
|---|---|
| 리포트가 아예 없음 | `deep_extra_args` 오타 → SIF가 모르는 인자 → exit 2 → `set -e` 로 전체 실패. §0 점검 |
| `hotspot_clusters` 가 빈 배열 | `auto_deep` 이 꺼졌거나 solid 응력 잡이 없음 |
| `strain_available: false` | 덱에 변형률 텐서가 없음(`*DATABASE_EXTENT_BINARY` 의 `STRFLG` 확인). 값이 전부 0이면 "미기록"으로 판정해 생략한다 — 0 을 실측값처럼 보고하지 않는다 |
| `stress_mean` 이 너무 낮음 | `top_percent` 가 과함 → 배경이 섞였다. §4 참조 |
| 덩어리가 잘게 쪼개짐 | `distance_factor` 를 키운다 |
| sphere 가 안 돔 | 시나리오가 IMPACT다. §6 |
| 노드마다 결과가 다름 | `/opt/apptainers` 는 노드 로컬. SIF 버전 확인 |

**로그 위치**

```
{output_dir}/deep_report.sh              생성된 스크립트 (명령 확인용)
{output_dir}/sphere_report.slurm.out     종합 리포트 stdout
{output_dir}/sphere_report.slurm.err     stderr
Run_*/report/analysis_result.json        케이스별 결과
```

`deep_report.sh` 를 열어보면 실제로 어떤 명령이 나갔는지 그대로 보인다 —
옵션이 안 먹는 것 같으면 여기부터 확인한다.

---

## 8. 수동 실행

후처리 스크립트는 `enabled` 와 무관하게 **prepare 시점에 항상 생성**된다.
자동 실행을 껐거나 나중에 다시 돌리고 싶으면 그대로 실행하면 된다.

```bash
bash {output_dir}/Run_.../deep_report.sh          # 케이스 1건
sbatch {output_dir}/sphere_report.sbatch          # 종합
KooChainRun postprocess runner_config.json        # CLI 경유
```

---

## 9. 현재 제한

| 항목 | 상태 |
|---|---|
| 솔리드 요소 핫스팟 | 지원 |
| **셸 요소 핫스팟** | **미지원** |
| 핫스팟 기준량 | von Mises 고정 |
| 시각별 군집 추적 | 미지원 (전 시간 최대 기준 1회) |
| 자연어 구역 라벨("좌하단") | 미지원 — 상대 좌표까지만 |
| 침식(삭제) 요소 필터 | 구현했으나 침식 덱으로 미검증 |
| GUI 에서 핫스팟 YAML 생성 | 미지원 |
