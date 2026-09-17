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
| `<output>` | positional | dynain 파일 경로(재료가 없으면 CSV) | — |
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

### 출력 (바이너리 동작)
- `<output>`: `*INITIAL_STRESS_SOLID`(dynain). `pre.k` 처럼 `.k` 로 끝나면 `pre.dynain` 으로 쓴다(메시 사본과 같은 파일이 되어 dynain 이 덮어써지고 자기 자신을 `*INCLUDE` 하던 결함 수정).
- `<output 에서 확장자를 뗀 이름>.k`: 변형 메시 사본 + dynain `*INCLUDE`.
- `<output 에서 확장자를 뗀 이름>.csv`: `--csv` 일 때. 재료를 못 찾으면 dynain 대신 `<output>` 에 CSV 만 쓴다.

위 예제(`prestress_out`)는 `prestress_out`(dynain) + `prestress_out.k` + `prestress_out.csv` 를 만든다. 알아보기 쉬운 이름을 원하면 `prestress_out.dynain` 을 준다.

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
| `operations[].dat_file` | op | 처짐값 격자 파일(필수, YAML 폴더 기준 상대 경로) |
| `operations[].plane` | op | `xy`(기본) / `yz` / `zx` |
| `operations[].deflection_axis` | op | `+z`(기본 `z`) / `-z` / `±x` / `±y` |
| `operations[].unit` | op | 격자 값 단위 `um`(기본) / `mm` / `m` |
| `operations[].mode` | op | `prestress`(기본, 초기응력만) / `deform`(노드 이동) |
| `operations[].morph_factor` | op | 처짐 배율(> 0, 기본 1.0) |
| `operations[].finite_strain` | op | `true`(기본, von Kármán) / `false`(Kirchhoff) |
| `operations[].outside_behavior` | op | 격자 범위 밖 노드 `zero`(기본) / `clamp` / `extrapolate` |
| `operations[].mask_value` / `noise_threshold` | op | 결측 값(기본 9999, 주변 보간) / 노이즈 임계값(기본 1e-10) |
| `operations[].data_bbox.{x_min,x_max,y_min,y_max}` | op | 격자가 덮는 평면 범위(생략 시 파트 bbox) |

이전 help 와 이 문서가 적었던 `source`·`dat_top`·`dat_bottom`·op 바로 아래 `x_min~y_max` 는 warpage 파서가 읽지 않는 키였다(오류 없이 무시, 바이너리 help 도 정정됨). `mode` 는 `curvature/raw` 가 아니라 `prestress/deform` 이다.

### 예제
```yaml
base_model: flat.k
output: warped
operations:
  - type: warpage
    target_pid: 1
    dat_file: warpage.dat
    plane: xy
    deflection_axis: +z
    unit: um
    mode: prestress
```

`warpage.dat` 은 공백 구분 처짐값 행렬이다(아래는 가운데가 100 um 솟은 3×5 격자). 빈 폴더 실행 사례는 `KooRemapper help warpage` 에 있다.
```
0  0   0   0  0
0 50 100  50  0
0  0   0   0  0
```

### 동작원리
처짐값 행렬을 `data_bbox`(생략 시 파트 bbox)에 펼친다. **열 0 = 평면 1축 최소, 행 0 = 2축 최소**다(bend 의 dat 는 행 0 = x2 최대로 반대). 노드 위치의 처짐은 바이리니어 보간으로 구하고, prestress 모드는 유한 차분 곡률 → Kirchhoff/von Kármán 굽힘 변형률 → 초기응력을, deform 모드는 노드를 처짐만큼 이동한다(정본 §21).

### REMAP 스텝
yaml-config 계열이므로 `params.op: warpage` + `params.config: {base_model, output, operations: [...]}`.

### 주의
- dat 파일은 x y z 열이 아니라 처짐값 행렬이다(값 단위는 `unit`, 기본 um).
- YAML 이 작업 폴더에 있을 때 `dat_file` 을 루트(`/파일`)에서 찾던 결함은 수정됐다(REMAP 스텝처럼 작업 폴더에서 실행하는 경우).

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
| `operations[].plane` | op | 굽힘 평면 `xy` / `yz` / `zx` (x1,x2 = X,Y / Y,Z / Z,X) |
| `operations[].mode` | op | `deform`(노드 이동 + 역응력) / `stress`(노드 그대로, 정응력) |
| `operations[].source` | op | `formula` / `dat` / `dat_pair` (필수) |
| `operations[].expression` | op | 처짐 w(x1, x2) 수식(`source: formula`) |
| `operations[].dat_file` / `dat_top`·`dat_bottom` | op | `source: dat` 격자 / `dat_pair` 상·하면 격자 |
| `material.E`·`material.nu` | top | 선택(생략 시 대상 파트의 `*MAT_ELASTIC`) |

수식 변수: `x1`, `x2`(바운딩 박스 최소값 기준 상대 좌표), `L1`, `L2`(바운딩 박스 치수), `pi`. 지원 함수 sin/cos/tan/sqrt/exp/log/abs/pow. dat 격자는 파트 평면 bbox 에 펼치며 행 0 = x2 최대, 열 0 = x1 최소다.

### 예제
```yaml
base_model: flat.k
output: bent
operations:
  - type: bend
    target_pid: 1
    plane: xy
    mode: deform
    source: formula
    expression: "0.001*x1"
```

### 동작원리
처짐 함수 w 로부터 곡률 κ1, κ2, κ12(= −∂²w) 를 구하고, 중립면에서 거리 d 인 지점의 굽힘 변형률 ε = d·κ 를 적용한다. 응력은 절점 변위 적용 전에 계산해 중립면 위치를 보존한다(정본 §13).

### REMAP 스텝
yaml-config 계열이므로 `params.op: bend` + `params.config: {base_model, output, operations: [...]}`.

### 주의
- 응력은 노드 변위 적용 전에 계산된다(중립면 보존, 정본 §13).
- `plane` 은 `xy`/`yz`/`zx` 다. 이전 help 와 이 문서의 `xz`·`mode: formula` 는 설정 검사에서 거부되는 값이었다(바이너리 help 도 정정됨). 단독 `bend` 는 예전엔 검사 없이 `source` 가 없으면 비정상 종료(SIGSEGV)했으나 이제 assemble 과 같은 오류를 낸다.

### 개발현황
구현됨(v1.8.0 바이너리 내장, help 확인).

---

## indent

### 용도
폐곡선(다각형 또는 스플라인 펀치 윤곽) 안쪽 영역에 필렛 프로파일로 압입(depth > 0) 또는 엠보싱(depth < 0)을 적용하고 선택적으로 초기 응력을 계산한다(정본 §14; help).

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
| `operations[].plane` | op | 압입 평면 `xy` / `yz` / `zx` |
| `operations[].direction` | op | 펀치 방향 `+z`/`-z`/`+x`/`-x`/`+y`/`-y` |
| `operations[].depth` | op | 압입 깊이(> 0 압입, < 0 엠보싱, 0 불가) |
| `operations[].r1` | op | 바닥 쪽 전이 호 반경(> 0, 윤곽 바깥 0~r1) |
| `operations[].r2` | op | 표면 쪽 전이 호 반경(> 0, 윤곽 바깥 r1~r1+r2) |
| `operations[].bottom_ratio` | op | 반대 면 변위 비율(기본 0 = 반대 면 고정) |
| `operations[].stress` | op | 초기 응력 계산 여부(기본 false) |
| `operations[].shell_thickness` | op | 셸 응력 두께(기본 0 = `*SECTION_SHELL`) |
| `operations[].shape.type` | op | `polygon` / `spline` |
| `operations[].shape.points` | op | 평평한 바닥 윤곽 `- [x1, x2]` 3점 이상(모델 좌표) |

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
      type: polygon
      points:
        - [6, 3]
        - [12, 3]
        - [12, 7]
        - [6, 7]
```

### 동작원리
윤곽 안쪽은 depth 만큼 평평하게 누르고, 윤곽 바깥 거리 d 에서 r1 호(0 ≤ d < r1) → r2 호(r1 ≤ d < r1+r2) 로 표면까지 되돌린다(k = depth/(r1+r2)). 두께 방향으로는 눌리는 면 h → 반대 면 bottom_ratio·h 로 선형 보간하며, depth < 0 이면 바깥으로 당기는 엠보싱이 된다. 응력은 절점 변위 전에 계산하고, h''(d) 특이점은 상한으로 제한한다(정본 §14).

### REMAP 스텝
yaml-config 계열이므로 `params.op: indent` + `params.config: {base_model, output, operations: [...]}`.

### 주의
- depth < 0 은 엠보싱(바깥으로 돌출)이다(help; 정본 §14).
- `shape.type: circle` 은 없다(이전 help 표기 오류, 바이너리 help 정정됨). 단독 `indent` 는 예전엔 points·r1/r2 가 없으면 비정상 종료(abort)했으나 이제 assemble 과 같은 오류를 낸다.
- 셸 요소 응력 두께는 `shell_thickness`(0 이면 `*SECTION_SHELL` 값)다.

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

positional 로 입력 메시·config·출력 접두를 받지만, config 는 파트별 변형 조건을 담는 yaml-config 계열이다. 출력은 `<prefix>.k`(압축 메시 + `*INCLUDE` dynain)와 `<prefix>.dynain`(역방향 `*INITIAL_STRESS_SOLID`)이다. 접두어 끝의 `.k` 는 뗀다(예전엔 `out.k.k`).

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
