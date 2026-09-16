# KooRemapper ops — 변형·초기응력(strain · prestress · formstrain · warpage · bend · indent · squeeze)

SmartTwinPreprocessor.sif 안 `/opt/kooremapper/bin/KooRemapper`(C++ CLI, v1.8.0)의 변형·초기응력 계열 op 7종 레퍼런스다. 각 op는 컨테이너에서 직접 실행하거나 KooChainRun 의 REMAP 스텝으로 호출한다.

## 공통 실행 형태

- 직접 실행: `apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper <op> ...`
- REMAP 스텝: `params.op` 로 op를 선택하고, positional 계열은 `params.argv`(리스트), yaml-config 계열은 `params.config`(dict)로 인자를 전달한다. `squeeze` 는 positional 3인자(`<mesh.k> <config.yaml> <output_prefix>`)라 `params.argv` 로 전달하며, config.yaml 은 파일 경로로 준다.

호출형태 분류(help `Usage:` 기준).

- positional 계열: `strain`, `prestress`
- positional + config 파일 계열: `squeeze`(config.yaml 을 positional 인자로 받음)
- yaml-config 계열: `formstrain`, `warpage`, `bend`, `indent`

각 op의 `사용법` 줄은 help `Usage:` 와 정확히 일치한다. yaml-config 계열의 config 스키마는 help의 `YAML Config Format` 과 예제 YAML을 정본으로 삼고, 정본 매뉴얼 §N 이 추가로 문서화한 파라미터는 그 출처를 명시해 구분한다.

---

## strain

### 용도
기준 형상(reference)과 변형 형상(deformed) 메시 쌍의 변형률 텐서를 계산해 요소별 6성분 CSV로 출력한다(정본 §10; help).

### 사용법
```
KooRemapper strain [options] <ref_mesh> <def_mesh> <output.csv>
```

### 인자 (help)
| 인자/옵션 | 구분 | 설명 | 기본값 |
|---|---|---|---|
| `<ref_mesh>` | positional | 기준(미변형) 메시 k-파일 | — |
| `<def_mesh>` | positional | 변형 메시 k-파일 | — |
| `<output.csv>` | positional | 변형률 결과 CSV | — |
| `--type <t>` | option | 변형률 유형 `engineering`/`green`/`log` | `engineering` |

변형률 유형 의미(정본 §10). `engineering`(소변형), `green`(Green-Lagrange, 대변형 비선형 항 포함), `log`(로그/진변형률, 대변형).

### 예제
```
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper strain ref.k def.k strain.csv --type green
```

### 동작원리
두 메시의 동일 토폴로지 요소 간 절점 변위로부터 변형률 텐서를 구하고, 각 요소의 εxx, εyy, εzz, εxy, εyz, εxz 6성분을 CSV로 기록한다(정본 §10).

### REMAP 스텝
positional 계열이므로 `params.op: strain` + `params.argv: ["ref.k", "def.k", "strain.csv", "--type", "green"]`.

### 주의
- 두 메시는 동일 토폴로지여야 한다(변위 매칭 전제, 정본 §10).
- 출력은 CSV뿐이며 초기응력 dynain은 생성하지 않는다. 응력이 필요하면 `prestress` 를 쓴다(help).

### 개발현황
구현됨(v1.8.0 바이너리 내장, help 확인).

---

## prestress

### 용도
기준·변형 메시 쌍의 변형률로부터 Hooke의 법칙으로 응력을 계산해 LS-DYNA `*INITIAL_STRESS_SOLID`(dynain)로 출력한다(정본 §6; help).

### 사용법
```
KooRemapper prestress [options] <ref_mesh> <def_mesh> <output>
```

### 인자 (help)
| 인자/옵션 | 구분 | 설명 | 기본값 |
|---|---|---|---|
| `<ref_mesh>` | positional | 기준(미변형) 메시 k-파일 | — |
| `<def_mesh>` | positional | 변형 메시 k-파일(동일 토폴로지) | — |
| `<output>` | positional | 출력 파일(dynain 또는 CSV) | — |
| `--E <value>` | option | 영률(K-파일 재료 오버라이드) | K-파일 값 |
| `--nu <value>` | option | 푸아송 비(K-파일 재료 오버라이드) | K-파일 값 |
| `--strain <type>` | option | 변형률 유형 `engineering`/`green` | `green` |
| `--csv` | option | 변형률/응력 CSV 추가 출력 | off |

### 재료 우선순위 (help)
1. 명령행 `--E`, `--nu`(전체 오버라이드).
2. K-파일의 `*PART` + `*MAT_ELASTIC`(요소가 속한 파트별 재료 자동 인식).

재료가 확보되면 Hooke의 법칙(라메 상수 λ, μ)으로 Cauchy 응력을 계산해 `*INITIAL_STRESS_SOLID` 카드를 낸다(정본 §6).

### 예제
```
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper prestress --E 210000 --nu 0.3 --csv ref.k def.k prestress_out
```

### REMAP 스텝
positional 계열이므로 `params.op: prestress` + `params.argv: ["ref.k", "def.k", "prestress_out", "--E", "210000", "--nu", "0.3", "--csv"]`.

### 주의
- 두 메시는 동일 토폴로지여야 한다(help).
- 재료가 없고 `--E`/`--nu` 도 없으면 응력을 계산할 수 없다(변형률만, 정본 §6·help).
- `--strain` 기본값은 help 기준 `green` 이다(정본 §6 본문의 기본값 서술과 차이가 있으므로 v1.8.0 바이너리 기준 `green` 을 따른다).

### 개발현황
구현됨(v1.8.0 바이너리 내장, help 확인).

---

## formstrain

### 용도
셸 메시의 이면각(dihedral angle)으로부터 굽힘 곡률 κ=θ/L 을 구해 성형 등가 소성 변형률(EPS)을 추정하고 초기 변형률 카드로 내보낸다(help). (정본 §15 는 출력 카드를 `*INITIAL_STRESS_SHELL`(초기 응력)로 서술해 help 의 `*INITIAL_STRAIN_SHELL`(초기 변형률)와 상충하므로 카드 종류는 v1.8.0 바이너리 기준 help 를 따른다.)

### 사용법
```
KooRemapper formstrain <config.yaml>
```

### config 스키마 (help / examples)
| 키 | 위치 | 설명 |
|---|---|---|
| `base_model` | top | 굽힘 셸 메시 k-파일 |
| `output` | top | 출력 접두 |
| `dynain_embed` | top | 출력에 초기 변형률 셸 카드 임베드(true/false) |
| `operations[].type` | op | `formstrain` |
| `operations[].target_pid` | op | 대상 파트. 생략 시 전체 셸 파트 자동 감지 |
| `operations[].shell_thickness` | op | 두께 오버라이드(선택) |
| `operations[].min_curvature` | op | 임계값 미만 평탄부 무시(노이즈 필터) |

### 예제
`examples/formstrain/formstrain_test.yaml`.
```yaml
base_model: bent_shell.k
output: formstrain_result
dynain_embed: true
operations:
  - type: formstrain
    # target_pid 생략 -> 전체 셸 파트 자동 감지
```

### 동작원리
인접 셸 요소 쌍의 이면각 θ와 중심 간 거리 L 로 곡률 κ=θ/L 을 얻고, 두께 t 에 대해 EPS = t·θ/(√3·L) 로 등가 소성 변형률을 산정한다. 재료 항복응력 sigy 는 `*MAT_024` 에서 읽어 EPS 스케일에 쓴다. 동일 요소에 여러 이웃 곡률이 겹치면 합산이 아니라 최대값(max)으로 병합한다(정본 §15; help).

### REMAP 스텝
yaml-config 계열이므로 `params.op: formstrain` + `params.config: {base_model, output, dynain_embed, operations: [...]}`.

### 주의
- `*ELEMENT_SHELL` 을 가진 굽힘 셸 메시가 필요하다(help).
- EPS 병합은 max() 이며 sum() 이 아니다(정본 §15; help).

### 개발현황
구현됨(v1.8.0 바이너리 내장, help 확인). 동작 예제 `examples/formstrain/`(formstrain_test.yaml, shield_can_test.yaml) 제공.

---

## warpage

### 용도
측정 워피지 변형 데이터(CSV/dat)를 읽어 셸 또는 솔리드 파트에 면외 변형장을 적용한다(정본 §21; help).

### 사용법
```
KooRemapper warpage <config.yaml>
```

### config 스키마 (help)
| 키 | 위치 | 설명 |
|---|---|---|
| `base_model` | top | 기준 메시 k-파일 |
| `output` | top | 출력 접두 |
| `operations[].type` | op | `warpage` |
| `operations[].target_pid` | op | 대상 파트 |
| `operations[].source` | op | `dat_file` 또는 `formula` |
| `operations[].dat_file` | op | 측정 변형 데이터 파일 |
| `operations[].dat_top` / `dat_bottom` | op | 상/하면 컬럼명 |
| `operations[].x_min`/`x_max`/`y_min`/`y_max` | op | 데이터 바운딩 박스(선택) |

정본 §21 은 추가로 `mode`(curvature/raw), `morph_factor`(변형 배율, 기본 1.0), `deflection_axis`, `plane`(투영 평면), `noise_threshold`(기본 0.001), `finite_strain`(기본 false), `outside_behavior`(clamp/zero, 기본 clamp), `mask_value`(무효 데이터 마커) 파라미터를 문서화한다. 다만 v1.8.0 help 예시의 `operations:` 스키마 내 정확한 배치는 help에 나타나지 않으므로 사용 전 실제 스키마 확인이 필요하다.

### 예제
```yaml
base_model: flat.k
output: warped
operations:
  - type: warpage
    target_pid: 1
    source: dat_file
    dat_file: warpage.dat
    dat_top: top
    dat_bottom: bottom
    x_min: 0.0
    x_max: 100.0
    y_min: 0.0
    y_max: 100.0
```

### 동작원리
dat 파일(탭/공백 구분 x, y, z 컬럼)에서 격자 변형 데이터를 로드하고, 중간 절점 위치는 바이리니어 보간으로 변형량을 산정해 메시를 변형한다. curvature 모드는 유한 차분으로 곡률을 구해 굽힘 응력을, raw 모드는 직접 절점 변위만 적용한다(정본 §21).

### REMAP 스텝
yaml-config 계열이므로 `params.op: warpage` + `params.config: {base_model, output, operations: [...]}`.

### 주의
- dat 파일은 탭/공백 구분의 x, y, z 컬럼 형식이어야 한다(help).
- 정본 §21 문서화 파라미터(mode, morph_factor 등)의 help 스키마 내 배치는 미확인이므로 확인 필요.

### 개발현황
구현됨(v1.8.0 바이너리 내장, help 확인).

---

## bend

### 용도
처짐 함수 w(x1, x2)로 기술되는 굽힘을 파트에 적용하고 선택적으로 초기 응력을 계산한다. 수식(formula) 또는 dat 파일 곡률 입력을 지원한다(정본 §13; help).

### 사용법
```
KooRemapper bend <config.yaml>
```

### config 스키마 (help)
| 키 | 위치 | 설명 |
|---|---|---|
| `base_model` | top | 기준 메시 k-파일 |
| `output` | top | 출력 접두 |
| `operations[].type` | op | `bend` |
| `operations[].target_pid` | op | 대상 파트 |
| `operations[].plane` | op | 굽힘 평면 `xy`/`xz`/`yz` |
| `operations[].mode` | op | `formula` 또는 `dat` |
| `operations[].expression` | op | 처짐 w(x1) 수식(formula 모드) |
| `operations[].source`/`dat_file`/`dat_top`/`dat_bottom` | op | dat 모드 입력 |

수식 변수(help; 정본 §13). `x1`, `x2`(바운딩 박스 최소값 기준 상대 좌표), `L1`, `L2`(바운딩 박스 치수), `pi`. 정본 §13 은 추가로 `material`(E, nu), `mode: deform|stress`, `source: dat_pair`(dat_top/dat_bottom 쌍), 지원 함수 sin/cos/tan/sqrt/exp/log/abs/pow 를 문서화한다.

### 예제
```yaml
base_model: flat.k
output: bent
operations:
  - type: bend
    target_pid: 1
    plane: xz
    mode: formula
    expression: "0.001*x1"
```

### 동작원리
처짐 함수 w 로부터 곡률 κ1, κ2, κ12(= −∂²w) 를 구하고, 중립면에서 거리 d 인 지점의 굽힘 변형률 ε = d·κ 를 적용한다. 응력은 절점 변위 적용 전에 계산해 중립면 위치를 보존한다(정본 §13).

### REMAP 스텝
yaml-config 계열이므로 `params.op: bend` + `params.config: {base_model, output, operations: [...]}`.

### 주의
- 응력은 노드 변위 적용 전에 계산된다(중립면 보존, 정본 §13).
- `plane` 은 help 기준 `xy`/`xz`/`yz` 다(정본 §13 본문의 `zx` 표기와 차이가 있으므로 v1.8.0 바이너리 기준을 따른다).

### 개발현황
구현됨(v1.8.0 바이너리 내장, help 확인).

---

## indent

### 용도
폐곡선(원 또는 다각형 펀치) 안쪽 영역에 필렛 프로파일로 압입(depth > 0) 또는 엠보싱(depth < 0)을 적용하고 선택적으로 초기 응력을 계산한다(정본 §14; help).

### 사용법
```
KooRemapper indent <config.yaml>
```

### config 스키마 (help)
| 키 | 위치 | 설명 |
|---|---|---|
| `base_model` | top | 기준 메시 k-파일 |
| `output` | top | 출력 접두 |
| `operations[].type` | op | `indent` |
| `operations[].target_pid` | op | 대상 파트 |
| `operations[].plane` | op | 압입 평면 |
| `operations[].direction` | op | 펀치 방향(예: `-z`) |
| `operations[].depth` | op | 압입 깊이(음수 = 엠보싱) |
| `operations[].r1` | op | 펀치(바닥) 반경 |
| `operations[].r2` | op | 필렛 반경 |
| `operations[].stress` | op | 초기 응력 계산 여부 |
| `operations[].shape.type` | op | `circle` 또는 `polygon` |
| `operations[].shape.points` | op | polygon 꼭짓점 리스트 |

정본 §14 는 추가로 `bottom_ratio`(두께 방향 관통 비율, 기본 0.5), `shell_thickness`(셸 요소 응력에 필요), `shape.type: spline`, `material`(E, nu) 을 문서화한다.

### 예제
```yaml
base_model: flat.k
output: indented
operations:
  - type: indent
    target_pid: 1
    plane: xy
    direction: -z
    depth: 0.5
    r1: 2.0
    r2: 0.5
    stress: true
    shape:
      type: circle
```

### 동작원리
부호 있는 거리 d 에 대해 quarter-arc 필렛 프로파일 h(d) 로 절점을 이동한다. r1 구역·평탄 구역·r2 구역으로 나뉘며, depth < 0 이면 바깥으로 당기는 엠보싱이 된다. 응력은 절점 변위 전에 계산하고, h''(d) 특이점은 상한으로 제한한다(정본 §14).

### REMAP 스텝
yaml-config 계열이므로 `params.op: indent` + `params.config: {base_model, output, operations: [...]}`.

### 주의
- depth < 0 은 엠보싱(바깥으로 돌출)이다(help; 정본 §14).
- 셸 요소 응력 계산에는 `shell_thickness` 가 필요하다(help).

### 개발현황
구현됨(v1.8.0 바이너리 내장, help 확인).

---

## squeeze

### 용도
간섭(interference fit) 조립 시뮬레이션을 위해 대상 파트를 지정 변형률로 압축하고, 그 역방향(인장) 초기 응력을 dynain 으로 출력한다(정본 §7; help).

### 사용법
```
KooRemapper squeeze <mesh.k> <config.yaml> <output_prefix>
```

positional 로 입력 메시·config·출력 접두를 받지만, config 는 파트별 변형 조건을 담는 yaml-config 계열이다. 출력은 `<prefix>.k`(압축 메시 + `*INCLUDE` dynain)와 `<prefix>_dynain.dat`(역방향 `*INITIAL_STRESS_SOLID`)이다(help).

### config 스키마 (help / examples)
| 키 | 위치 | 설명 |
|---|---|---|
| `parts[].pid` | part | 대상 파트 ID |
| `parts[].eps_x`/`eps_y`/`eps_z` | part | 축별 변형률(음수 = 압축) |
| `material.E` | top | 영률(K-파일 재료 오버라이드, 선택) |
| `material.nu` | top | 푸아송 비(선택) |

정본 §7 은 추가로 파트별 `swelling`(등방 팽창) 모드를 문서화한다. `swelling` 파트는 절점을 이동하지 않고 `*MAT_ADD_THERMAL_EXPANSION` + `*INITIAL_TEMPERATURE` + `*LOAD_THERMAL_VARIABLE` 카드를 삽입하며 dynain 에는 포함되지 않는다.

### 예제
`examples/squeeze/ex01_stress_yaml_material.yaml`(변형률 지정 + YAML 재료).
```yaml
parts:
  - pid: 1
    eps_x: -0.01
    eps_y: -0.01
    eps_z:  0.0
material:
  E: 210000.0
  nu: 0.3
```

`examples/squeeze/ex04_swelling.yaml`(등방 팽윤, 정본 §7).
```yaml
parts:
  - pid: 1
    swelling: 0.03
  - pid: 2
    swelling: 0.05
```

### 동작원리
각 파트에 대해 바운딩 박스 중심(중립면)을 구하고, 그 중심 기준으로 지정 변형률만큼 절점을 압축한 뒤 Hooke의 법칙으로 역방향(인장) 초기 응력을 생성한다. LS-DYNA 동적 이완(dynamic relaxation)과 함께 써서 간섭 끼워맞춤을 모델링한다(정본 §7; help).

### REMAP 스텝
positional 3인자 계열이므로 `params.op: squeeze` + `params.argv: ["mesh.k", "config.yaml", "output_prefix"]` 로 전달한다. 여기서 `config.yaml` 은 파트별 변형 조건(`parts`, `material`)을 담은 YAML 파일의 경로이며, `mesh.k` 와 `output_prefix` 는 positional 인자라 `params.config`(dict)만으로는 전달할 수 없다.

### 주의
- `swelling` 과 `eps_x/y/z` 는 같은 파트에 동시 사용할 수 없다(정본 §7).
- `swelling` 파트는 K-파일에 해당 파트의 `*MAT_*` 카드가 반드시 있어야 한다(MID 연결, examples/squeeze/ex04_swelling.yaml).

### 개발현황
구현됨(v1.8.0 바이너리 내장, help 확인). 동작 예제 `examples/squeeze/`(ex01~ex05: 응력/재료/무재료/swelling/혼합) 제공.
