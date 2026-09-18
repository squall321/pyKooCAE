# KooRemapper ops — 메시 생성(generate · generate-var · battery · cclip)

KooRemapper(SmartTwinPreprocessor.sif 내 `/opt/kooremapper/bin/KooRemapper`, C++ CLI v1.8.0)의 메시 생성 계열 op 4종 레퍼런스다. 각 op은 `apptainer exec <sif> /opt/kooremapper/bin/KooRemapper <op> ...` 로 직접 실행하거나 KooChainRun 의 REMAP 스텝으로 실행한다.

- REMAP 스텝 매핑 규칙 — positional op(`generate`, `generate-var`)은 `params.op` + `params.argv`(리스트), yaml-config op(`battery`, `cclip`)은 `params.op` + `params.config`(dict)로 넘긴다. 각 op 절에 다시 표기한다.
- YAML 설정의 BOM·탭·상대 경로 공통 규칙과 새로 거절되는 열거값은 [README §YAML 설정 공통 규칙](../README.md#yaml-설정-공통-규칙) 참조.

---

## generate

### 용도

테스트·데모용 기하 형상 HEX8 메시를 생성한다(정본 §8). `box` 하위명령은 YAML 설정으로 직육면체(rectangular solid) 메시를 만든다(help).

호출형태(help `Usage:`)는 두 가지다.

```bash
KooRemapper generate [options] <type> <output_prefix>
KooRemapper generate box <config.yaml>
```

- REMAP 스텝: `params.op: generate` + `params.argv: [<type>, <output_prefix>, ...]`(positional op, 리스트). box 하위명령은 `params.argv: ["box", "<config.yaml>"]`.

### 인자 (표)

| 인자/옵션 | 타입 | 기본값 | 설명 | 근거 |
|---|---|---|---|---|
| `type` | positional | (필수) | 메시 형상: `teardrop`, `arc`, `scurve`, `helix`, `torus`, `twist`, `bendtwist`, `wave`, `bulge`, `taper`, `waterdrop`(foldable display) | help |
| `output_prefix` | positional | (필수) | 출력 파일 접두사 | help |
| `--dim-i <n>` | int | 10 | I 방향 요소 수 | help |
| `--dim-j <n>` | int | 5 | J 방향 요소 수 | help |
| `--dim-k <n>` | int | 5 | K 방향 요소 수 | help |
| `box <config.yaml>` | 하위명령 | — | YAML 로 박스 메시 생성 | help |

`box` YAML 파라미터(help).

| 키 | 설명 |
|---|---|
| `output` | 출력 파일 경로 (예: `box.k`). `.k` 가 없으면 붙는다. **상대 경로는 이 YAML 파일이 있는 폴더 기준**이다 — 작업 폴더 기준이 아니다 |
| `lx` / `ly` / `lz` | X/Y/Z 길이 [mm] |
| `nx` / `ny` / `nz` | X/Y/Z 방향 요소 수 |
| `rho` | 밀도 [t/mm3] |
| `E` | 영률 [MPa] |
| `nu` | 포아송비 |
| `mid` / `secid` / `pid` | material / section / part ID |
| `part_title` | 파트 제목 |

### 예제

```bash
# 형상 메시
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper generate --dim-i 20 --dim-j 10 teardrop demo_teardrop

# 박스 메시 (examples/cclip/gen_board.yaml — cclip 입력용 BeCu 육면체)
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper generate box examples/cclip/gen_board.yaml
```

`examples/cclip/gen_board.yaml` 는 `lx/ly/lz`, `nx/ny/nz`, `rho/E/nu`, `mid/secid/pid`, `part_title` 로 3.0×1.5×0.5mm 단일 파트를 정의한다(examples/cclip/gen_board.yaml).

### 동작 원리

`type`/`output_prefix` 를 받아 지정 형상의 HEX8 메시를 `--dim-i/j/k` 해상도로 생성한다. `box` 는 YAML 의 치수·요소수·재료·파트 메타를 그대로 반영한 직육면체를 출력한다(help).

### 주의

- 호출형태는 help `Usage:` 기준(`<type> <output_prefix>`, box 하위명령, `bendtwist` 타입, `--dim-*` 옵션)이다. 정본 §8 은 `generate <type> [options] <output.k>` 형태와 `bendtwist`·box 하위명령이 빠진 예전 목록을 보여주므로 v1.8.0 은 help 를 따른다.
- `generate box` 의 YAML 은 [YAML 설정 공통 규칙](../README.md#yaml-설정-공통-규칙)을 따른다: BOM 은 무시하고, 들여쓰기에 탭이 있으면 rc=1 (`[ERROR] [generate] YAML 들여쓰기에 탭을 쓸 수 없습니다 …`), `output` 의 상대 경로는 YAML 폴더 기준이다. `type` 모드는 YAML 을 받지 않는다.

### 개발 현황

**구현됨** — help 에 형상 타입·옵션·box 하위명령이 명시되고, box 입력 예제(examples/cclip/gen_board.yaml)가 제공된다.

---

## generate-var

### 용도

변밀도(variable density) 메시를 YAML 설정으로 생성한다. 평면(`flat`)과 중심선 기반 곡선(`curved`) 두 타입을 지원한다(정본 §8, help).

호출형태(help `Usage:`).

```bash
KooRemapper generate-var [options] <config.yaml> <output.k>
```

- REMAP 스텝: `params.op: generate-var` + `params.argv: [<config.yaml>, <output.k>, ...]`(positional op, 리스트).

### 인자 (표)

| 인자/옵션 | 타입 | 기본값 | 설명 | 근거 |
|---|---|---|---|---|
| `config.yaml` | positional | (필수) | YAML 설정 파일 | help |
| `output.k` | positional | (필수) | 출력 K파일 | help |
| `--ref <file>` | 옵션 | — | 스케일링용 참조 평면 메시 | help |
| `--no-scale` | 플래그 | off | 참조로 스케일하지 않고 YAML 길이를 그대로 사용 | help |

YAML 필드(help).

| 타입 | 키 | 설명 |
|---|---|---|
| 공통 | `type` | `flat`(기본) 또는 `curved` |
| flat | `reference.flat_mesh` | 자동 스케일용 참조 메시 |
| flat | `elements_j` / `elements_k` | J/K 방향 요소 수 |
| flat | `variable_density.<zone>.length` / `.num_elements` | 존별 길이·요소 수 |
| curved | `reference.flat_mesh` | 스케일용(선택) |
| curved | `centerline_points` | 중심선 좌표 리스트 `[[x,y], ...]` |
| curved | `interpolation` | `linear` / `catmull_rom` / `bspline` |
| curved | `cross_section.width` / `.thickness` | 단면 치수(참조 없을 때만) |
| curved | `elements_along_curve` | 곡선 방향 요소 수 |
| curved | `elements_j` / `elements_k` | J/K 방향 요소 수 |

### 예제

```bash
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper generate-var --ref ref_flat.k config.yaml out.k
```

flat 예(help).

```yaml
type: flat
reference:
  flat_mesh: "ref_flat.k"
elements_j: 50
elements_k: 10
variable_density:
  zone1_dense_start:
    length: 10.0
    num_elements: 50
```

### 동작 원리

flat 은 존별 `length`/`num_elements` 로 길이 방향 밀도를 배분하고, `--ref`/`reference.flat_mesh` 가 있으면 참조 메시 치수에 맞춰 자동 스케일한다(`--no-scale` 시 스케일 생략). curved 는 `centerline_points` 를 `interpolation` 방식으로 보간해 중심선을 만들고 단면(참조 또는 `cross_section`)을 스윕한다(help).

### 주의

- YAML 스키마는 help(v1.8.0) 기준으로 `variable_density` + `elements_j/k` 구조다. 정본 §8 예시는 `zones:` 리스트(`id`/`nx`/`ny`/`nz`/`x_min`/`x_max`...) 형태를 보여주어 서로 다르다 — 현재 바이너리가 파싱하는 스키마는 help 형식이며, zones 형식 병행 지원 여부는 **확인 필요**.

### 개발 현황

**구현됨** — help 에 flat/curved 스키마와 옵션이 명시된다. 정본과 help 간 YAML 스키마 표기 차이는 위 주의 참조.

---

## battery

### 용도

배터리 셀(적층 `stacked` / 권취 `wound`) 모델을 YAML 설정에서 생성하고, 스웰링(swelling) 상태의 평형을 `CONTROL_DYNAMIC_RELAXATION` 으로 잡는 데크를 만든다(examples/battery/swell/*). 정본에는 없다.

호출형태(examples/battery YAML 주석의 `Usage:` 및 help — 다음 인자를 battery config 파일로 여는 동작).

```bash
KooRemapper battery <config.yaml>
```

- REMAP 스텝: `params.op: battery` + `params.config: {dict}`(yaml-config op).

### 인자 (표)

config 필드는 예제 관찰 기반이다(examples/battery/swell/stacked/stacked_swell.yaml, examples/battery/swell/wound/wound_swell.yaml). help 는 필드 문서를 출력하지 않는다.

| 키 | 설명 |
|---|---|
| `output` | 출력 접두사/경로. **상대 경로는 이 YAML 파일이 있는 폴더 기준**이다(2026-09-18 실행 확인 — 예전에는 작업 폴더 기준이었다). 가리키는 폴더는 미리 있어야 한다. 실제 파일 이름은 여기에 tier·phase 접미사와 `.k` 가 붙는다 |
| `use_dynain` / `dynain_file` | 이전 페이즈 상태를 `*INCLUDE_DYNAIN` 으로 물려받는다. **`dynain_file` 은 경로로 풀지 않는다** — 적힌 문자열이 덱에 그대로 찍히고 KooRemapper 는 그 파일을 열지 않는다(아래 주의 참조) |
| `model_type` | `stacked` 또는 `wound` |
| `tier` / `phase` | 티어·페이즈 지정 |
| `mode` | `swell` |
| `solid_electrode` | 전극층을 solid 로 |
| `solid_elform` | (wound) 1=reduced(안정), 2=fully integrated |
| `airbag_fill` / `no_pcm` / `no_thermal` | 채움·PCM·열해석 스위치 |
| `geometry.cell_width` / `.cell_height` | 셀 폭·높이 [mm] |
| `geometry.n_unit_cells` | (stacked) 단위셀 수 |
| `layer_thickness.*` | `al_cc`, `cathode`, `separator`, `anode`, `cu_cc`, `pouch`, `electrolyte_buffer` 두께 [mm] |
| `pouch.r_fillet` / `.n_fillet_segs` / `.buf_x` / `.buf_y` / `.dome_cap` | 파우치 필렛·버퍼·돔캡 |
| `wound.flat` / `.flat_ratio` / `.n_winds` | (wound) 편평·비율·권취 수 |
| `swelling.soc` / `.nmc_cte` / `.graphite_cte` | SOC, NMC 양극/흑연 음극 팽창률 |
| `dr_endtim` / `dr_tolerance` / `dr_factor` / `dr_nrcyck` | Dynamic Relaxation 파라미터 |
| `timestep_safety` / `output_interval` | 타임스텝 안전계수·출력 간격 |

### 예제

```bash
# 적층 셀 스웰링 (examples/battery/swell/stacked/stacked_swell.yaml)
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper battery examples/battery/swell/stacked/stacked_swell.yaml

# 권취 셀 스웰링 (examples/battery/swell/wound/wound_swell.yaml)
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper battery examples/battery/swell/wound/wound_swell.yaml
```

### 동작 원리

`layer_thickness` 로 전극·집전체·세퍼레이터·파우치 층을 쌓아 `model_type`(stacked/wound) 셀을 구성하고, `swelling` 의 인터칼레이션 팽창률(예: 흑연 10%)을 적용한 뒤 `dr_*` 설정의 Dynamic Relaxation 으로 팽창 상태 평형을 찾는다(examples/battery/swell/* 주석).

### 주의

- 정본에 없는 op 이므로 필드 정의는 예제 YAML 관찰에 근거한다. 예제에 등장하지 않는 추가 필드·기본값·검증 규칙은 **확인 필요**.
- help 는 config 파일 경로를 인자로 요구하며, 파일을 못 열면 `[ERROR] Cannot open battery config: ...` 로 실패한다(help).
- **`output` 의 상대 경로는 YAML 폴더 기준이다**(2026-09-18 실행 확인). `KooRemapper battery cfg/b.yaml` 의 `output: bat_out` 은 `cfg/bat_out_tier0_phase1.k` 로 나간다 — 예전에는 작업 폴더에 떨어졌다.
- **`dynain_file` 만은 경로 해석 대상이 아니다.** `*INCLUDE_DYNAIN` 다음 줄에 **적힌 문자열 그대로** 찍히고 KooRemapper 는 그 파일을 열지 않는다. 솔버가 산출 덱이 있는 폴더 기준으로 읽으므로, `dynain_file: ../state/my.dynain` 은 덱에도 `../state/my.dynain` 이 그대로 들어간다(2026-09-18 실행 확인). **산출 덱 옆에서 솔버가 찾을 이름**으로 적어라. 배치 체이닝(`use_dynain: true` + `batch.phases: [1, 2]`)에서 자동 계산되는 값도 같은 규칙이다.

### 개발 현황

**구현됨** — stacked/wound 각각 다수의 동작 예제(examples/battery/swell/stacked, /wound)가 제공된다. 정본 문서화 및 help 필드 설명은 부재.

---

## cclip

### 용도

스마트폰 스프링 접점 등 hex box 파트를 측정 힘-변위(force-deflection) 데이터에 캘리브레이션한 C형 쉘 스트립 클립으로 치환하고, 눌린(pressed) 상태로 `*INITIAL_STRESS_SHELL` 을 넣어 출력한다(help). 정본 명령 목록(§ 명령 개요, 155행)에는 한 줄 설명으로 등장하나 전용 섹션·config 필드 문서는 없다.

호출형태(help `Usage:`).

```bash
KooRemapper cclip <config.yaml>
```

- REMAP 스텝: `params.op: cclip` + `params.config: {dict}`(yaml-config op).

### 인자 (표)

config 필드(help + examples/cclip/*.yaml).

| 키 | 값/설명 | 근거 |
|---|---|---|
| `model` | 입력 모델 .k | help |
| `output` | 출력 접두사 — `.k` + `_cclip_report.json` 생성 | help |
| `mode` | `analytic` 또는 `deck`(LS-DYNA press deck) | help |
| `attach` | `none` 또는 `cnrb`(foot tied to board) | help |
| `stress_output` | `embed` 또는 `include`(.dynain + `*INCLUDE`) | help |
| `free_output` | true 시 `<output>_free.k`(눌리지 않은 원안)도 출력 | help |
| `element` | `shell` 또는 `solid`(through-thickness HEX8) | help |
| `axis` | `auto` 또는 `[+|-]x|y|z`(press-from side) | help |
| `open` | C 벌징 방향(길이축 기준, 예: `"+"`) | help |
| `calibration.point` | `{deflection, force}` 단일 작동점 | help, examples/cclip/cclip.yaml |
| `calibration.curve` | `[[d,F], ...]` F-δ 곡선 | help, examples/cclip/cclip_deck.yaml |
| `calibration.operating_deflection` | 곡선 모드 필수(설치 눌림량) | examples/cclip/cclip_deck.yaml |
| `calibration.tolerance` | 캘리브레이션 허용오차 | help |
| `clips[].pid` | 대상 파트 ID (또는 `match_part: "CCLIP_*"`, `auto: true`) | help |
| `clips[].overtravel` | free height = installed + overtravel | help, examples/cclip/cclip.yaml |

### 예제

```bash
# analytic — 작동점 1점 (examples/cclip/cclip.yaml)
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper cclip examples/cclip/cclip.yaml

# deck — F-δ 곡선 (examples/cclip/cclip_deck.yaml)
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper cclip examples/cclip/cclip_deck.yaml
```

`cclip.yaml` 은 `mode: analytic` + `calibration.point`, `cclip_deck.yaml` 은 `mode: deck` + `calibration.curve`/`operating_deflection` 를 쓴다. deck 모드는 자유 상태 클립·강체 압축판·변위 제어(implicit) 압축덱(`<output>_cclip_deck_<pid>.k`)을 추가로 생성한다(examples/cclip/cclip_deck.yaml).

### 동작 원리

대상 파트의 강성을 캘리브레이션 데이터에 맞춰 닫힌 형식(closed form)으로 풀고, 프리스트레스 모멘트장이 작동 접촉력과 평형을 이루도록 눌린 상태 C형 클립을 만든다. 원래 PID 를 유지하여 기존 SET/CONTACT 참조가 살아남는다(help).

### 주의

- 강성은 닫힌 형식으로 풀며, 오차가 `tolerance` 를 넘으면 실패한다(help).
- 곡선(`curve`) 캘리브레이션에서는 `operating_deflection`(설치 눌림량)이 필수다(examples/cclip/cclip_deck.yaml).
- 출력 검증은 솔버 없이 `tools/cclip_check.py` 로 수행한다(help).
- 정본 명령 목록에는 한 줄 설명만 있고 전용 섹션·config 필드 문서가 없어, 세부는 help 와 examples/cclip 근거. 그 외 필드·조합은 **확인 필요**.

### 개발 현황

**구현됨** — help 에 config 스키마·동작·검증 도구가 명시되고, analytic/deck 예제(examples/cclip/cclip.yaml, cclip_deck.yaml)와 입력 생성용 gen_board.yaml 이 제공된다. 정본 문서화는 부재.
