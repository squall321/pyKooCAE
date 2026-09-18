# KooRemapper ops — 메시 편집(convert · refine · elform · disconnect · offset · wrap · restack · update · iga)

요소 차수·공식 변경, 세분화, 노드 분리, 셸 오프셋/재적층, 와인딩 프리스트레스, 좌표 갱신, IGA 변환을 수행하는 KooRemapper의 아홉 가지 **yaml-config op** 레퍼런스다.

## 실행 형태 (공통)

KooRemapper는 `SmartTwinPreprocessor.sif` 안의 C++ CLI `/opt/kooremapper/bin/KooRemapper`(v1.8.0)다. 두 가지 방법으로 호출한다.

- 컨테이너 직접 실행: `apptainer exec <sif> /opt/kooremapper/bin/KooRemapper <op> <config.yaml>`
- KooChainRun의 `REMAP` 스텝: 아래 각 op의 "REMAP 스텝" 줄 참조.
- YAML 설정의 BOM·탭·상대 경로 공통 규칙과 새로 거절되는 열거값은 [README §YAML 설정 공통 규칙](../README.md#yaml-설정-공통-규칙) 참조.

이 페이지의 아홉 op은 모두 **yaml-config op**이다(help Usage가 모두 `KooRemapper <op> <config.yaml>` 형태). 따라서 REMAP 스텝에서는 `params.op=<op>` 와 `params.config`(dict — 아래 YAML 내용을 그대로 담음)로 전달한다. positional 인자를 쓰는 op은 이 페이지에 없다.

config 스키마 관례는 두 갈래다.

- convert · refine · elform · disconnect · offset · restack · iga — 최상위 `base_model`/`output` + `operations`(op 리스트, 각 항목에 `type: <op>`) 구조 (help, examples).
- wrap · update — `operations` 래퍼 없이 최상위 flat 스키마 (help, examples/wrap).

> 근거 주의: 정본 매뉴얼 일부 절(예: §16 convert, §22 offset)은 `model:`/`convert_type:` 같은 flat 필드로 스키마를 기술하지만, v1.8.0 help와 실제 examples는 위 `base_model`/`operations[].type` 구조를 쓴다. 호출형태와 필드명은 help·examples 기준으로 적었고, 파라미터의 의미·기본값·표는 정본을 함께 인용했다.

---

## convert

### 용도

1차 요소(TET4/HEX8/QUAD4/TRIA3)를 **2차 요소**(TET10/HEX20/QUAD8/TRIA6)로 변환한다. 기존 선형 요소의 각 엣지에 중간절점(mid-side node)을 추가한다. (정본 §16, help)

### 호출형태

```
KooRemapper convert <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper convert convert.yaml
```

config 형식 (help).

```yaml
base_model: model.k
output: result
operations:
  - type: hex20          # hex20 | tet10 | quad8 | tria6
    target_pid: 1        # 생략 시 전체 파트
    elform: 23           # 목표 ELFORM (선택)
```

REMAP 스텝: `params.op=convert`, `params.config`=위 YAML dict.

### 인자

| 필드 | 필수 | 설명 | 기본값 |
|---|---|---|---|
| `base_model` | 예 | 입력 K-파일 | — |
| `output` | 예 | 출력 접두어 | — |
| `operations[].type` | 예 | 변환 유형 `tet10`/`hex20`/`quad8`/`tria6` | — |
| `operations[].target_pid` | 아니오 | 대상 파트 ID(생략 시 전체) | 전체 |
| `operations[].elform` | 아니오 | 목표 ELFORM 지정 | 자동(아래 매핑) |

자동 ELFORM 매핑 (정본 §16): `tet10` TET4→TET10 = 17, `hex20` HEX8→HEX20 = 23, `quad8` QUAD4→QUAD8 = 23, `tria6` TRIA3→TRIA6 = 24.

### 예제

```yaml
base_model: model.k
output: converted
operations:
  - type: tet10
    target_pid: 1
```

(convert 전용 디렉터리는 없으나 examples/quadratic/(hex20_test.yaml·quad8_test.yaml·tria6_test.yaml)와 examples/tet10/tet10_test.yaml가 동일 스키마를 사용한다.)

### 동작 원리

선형 요소의 각 엣지 중점에 절점을 추가해 2차 요소로 승격한다. (정본 §16, help)

### 주의사항

- 필드명은 help·다른 op examples의 `base_model`/`operations[].type` 구조를 따른다. 정본 §16은 `model`/`convert_type` flat 필드로 기술하므로, 사용하는 버전에서 실제 수용 스키마를 확인하는 것이 안전하다. (정본 §16, help)
- `elform`을 생략하면 위 매핑 표의 기본값이 적용된다. (정본 §16)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).

---

## refine

### 용도

요소를 엣지 방향으로 **1:2 또는 1:3** 비율로 균일 세분화한다. (정본 §17, help)

### 호출형태

```
KooRemapper refine <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper refine refine.yaml
```

config 형식 (help).

```yaml
base_model: model.k
output: refined
operations:
  - type: refine
    target_pid: 1        # 생략 시 전체 파트
    ratio: 2             # 2 = 1:2 분할, 3 = 1:3 분할
```

REMAP 스텝: `params.op=refine`, `params.config`=위 YAML dict.

### 인자

| 필드 | 필수 | 설명 | 기본값 |
|---|---|---|---|
| `base_model` | 예 | 입력 K-파일 | — |
| `output` | 예 | 출력 접두어 | — |
| `operations[].type` | 예 | `refine` | — |
| `operations[].target_pid` | 아니오 | 대상 파트 ID(생략 시 전체) | 전체 |
| `operations[].ratio` | 예 | 세분화 비율 `2` 또는 `3` | — |

요소 유형별 생성 수 (정본 §17, help).

| 요소 | ratio=2 | ratio=3 |
|---|---|---|
| HEX8 | 8개 서브 헥스 | 27개 서브 헥스 |
| QUAD4 | 4개 서브 쿼드 | 9개 서브 쿼드 |
| TRIA3 | 4개 서브 삼각형 | 9개 서브 삼각형 |
| TET4 | 8개 서브 테트 | — (미지원) |

### 예제

```yaml
base_model: model.k
output: refined
operations:
  - type: refine
    ratio: 2
```

(refine 전용 디렉터리는 없으나 examples/quadratic/refine_*.yaml(hex/quad 1:2·1:3, tet 1:2)가 동일 스키마를 사용한다.)

### 동작 원리

각 요소를 엣지 균등 분할해 서브요소로 대체한다. (정본 §17)

### 주의사항

- TET4는 `ratio=3`을 지원하지 않는다. (정본 §17)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).

---

## elform

### 용도

기존 요소의 **ELFORM** 번호를 `*SECTION_*` 카드에서 변경한다. (정본 §18, help)

### 호출형태

```
KooRemapper elform <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper elform elform_hex_upgrade.yaml
```

config 형식 (examples/elform).

```yaml
base_model: simple_hex.k
output: result
operations:
  - type: elform
    target_pid: 1        # 생략 시 조건에 맞는 전체 파트
    target_elform: 23    # 목표 ELFORM (숫자 또는 별칭)
```

REMAP 스텝: `params.op=elform`, `params.config`=위 YAML dict.

### 인자

| 필드 | 필수 | 설명 | 기본값 |
|---|---|---|---|
| `base_model` | 예 | 입력 K-파일 | — |
| `output` | 예 | 출력 접두어 | — |
| `operations[].type` | 예 | `elform` | — |
| `operations[].target_pid` | 아니오 | 대상 파트 ID(생략 시 전체 일치 파트) | 전체 |
| `operations[].target_elform` | 예 | 목표 ELFORM(숫자 또는 별칭) | — |

고체 요소 별칭 (정본 §18): `constant_stress`=1, `fully_integrated`=2, `tet4`=13, `tet10`=17, `hex20`=23.
셸 요소 별칭 (정본 §18): `belytschko_tsay`=2, `hughes_liu`=1, `fully_integrated_shell`=16, `quad8`=23, `tria6`=24.
참고 ELFORM 값 (help): 고체 1(1점 축소적분)/2(완전적분)/10/13/16/23, 셸 2(Belytschko-Tsay)/16(완전적분).

### 예제

```yaml
# examples/elform/elform_hex_upgrade.yaml — HEX8 → HEX20
base_model: simple_hex.k
output: elform_hex_upgraded
operations:
  - type: elform
    target_elform: 23
```

`examples/elform/elform_case_a.yaml`은 ELFORM 1→2(상수응력→완전적분)를 보인다.

### 동작 원리

대상 파트의 SECTION 카드 ELFORM 필드를 목표값으로 치환한다. (정본 §18)

### 주의사항

- `target_elform`은 숫자 또는 위 별칭표의 별칭을 쓸 수 있다. example들은 숫자 값을 사용한다. (정본 §18, examples/elform)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).

---

## disconnect

### 용도

지정 파트의 경계면 **공유 노드를 분리**해 파괴 모델링용 비연속 인터페이스를 만든다. (정본 §19, help)

### 호출형태

```
KooRemapper disconnect <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper disconnect disconnect_czm.yaml
```

config 형식 (examples/disconnect).

```yaml
base_model: two_hex_2part.k
output: result
operations:
  - type: disconnect
    mode: czm            # full | czm | mefem
    target_pid: 0        # 인터페이스 파트(czm/mefem) 또는 0=전체
    cohesive_part_id: 99 # CZM cohesive 파트 ID (czm 모드)
    failure_strain: 0.5  # CZM/mefem 파괴 변형률
```

REMAP 스텝: `params.op=disconnect`, `params.config`=위 YAML dict.

### 인자

| 필드 | 필수 | 설명 | 기본값 |
|---|---|---|---|
| `base_model` | 예 | 입력 K-파일 | — |
| `output` | 예 | 출력 접두어 | — |
| `operations[].type` | 예 | `disconnect` | — |
| `operations[].mode` | 예 | `full` / `czm` / `mefem` | — |
| `operations[].target_pid` | 예 | 인터페이스 파트 ID, `0`=전체 | — |
| `operations[].cohesive_part_id` | czm | CZM cohesive 파트 ID(정본 §19: 0=자동) | — |
| `operations[].failure_strain` | czm/mefem | 파괴 변형률 | 정본 §19 예시 0.05 |

모드별 동작 (정본 §19 / help).

| 모드 | 동작 | LS-DYNA 출력 |
|---|---|---|
| `full` | 경계 공유 노드 단순 분리(→ 독립 파트) + PERI 요소 | `*SECTION_SOLID_PERI` (ELFORM=48, DR=1.01) |
| `czm` | 분리 면에 응집(cohesive) 요소 삽입 | `*ELEMENT_SOLID`(cohesive) + `*MAT_COHESIVE_*` |
| `mefem` | MEFEM(mesh-free) peridynamic 요소 / 미세균열 확장 파라미터 | `*MAT_ADD_EROSION` (EPPF) |

### 예제

```yaml
# examples/disconnect/disconnect_mefem.yaml
base_model: two_hex_2part.k
output: disconnect_mefem_result
operations:
  - type: disconnect
    mode: mefem
    target_pid: 0
    failure_strain: 0.085
```

`examples/disconnect/disconnect_czm.yaml`(mode czm, target_pid 0), `disconnect_full.yaml`(mode full)도 참고.

### 동작 원리

(1) 대상 파트 경계의 공유 노드를 식별하고, (2) 모드별로 단순 분리(full)·응집요소 삽입(czm)·침식/peridynamic 파라미터 부여(mefem)를 수행한다. (정본 §19, help)

### 주의사항

- `target_pid=0`은 전체를 대상으로 한다. (help)
- `restack` op 뒤에 이어 붙여 레이어 스택의 CZM/Peri 분리에 쓸 수 있다. (help, examples/disconnect/restack_czm.yaml)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).

---

## offset

### 용도

셸/표면 요소를 추출해 지정 두께·방향으로 **솔리드 레이어를 압출**한다. 곡면 법선, 가변 두께, 영역 선택, tied/CZM/contact 연결을 지원한다. (정본 §22, help)

### 호출형태

```
KooRemapper offset <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper offset 01_basic_solid_tied.yaml
```

config 형식 (examples/offset).

```yaml
base_model: model.k
output: result
operations:
  - type: offset
    source_pid: 1                    # 소스 표면 파트
    element_type: solid              # solid | tshell | shell
    thickness: 1.0                   # 오프셋 거리
    num_layers: 1                    # 레이어 수
    offset_direction: +z             # +x|-x|+y|-y|+z|-z|+normal|-normal
    connection_mode: tied            # tied | czm | contact | none
    new_pid: 10                      # 새 파트 ID
    part_title: "Basic_Offset"
    use_local_normals: false         # 곡면 노드별 법선(선택)
    thickness_formula: "1.0+0.01*x"  # 가변 두께(선택, x/y/z 변수)
    material_card: |                 # MID 칸(@MID@·숫자·라벨)은 새 MID 로 바뀜
      *MAT_ELASTIC
      $#     mid        ro         e        pr
           @MID@       2.0     12000      0.25
    czm_material_card: |             # connection_mode: czm 일 때 (@CZM_MID@ 등도 새 MID 로)
      *MAT_COHESIVE_MIXED_MODE
      $#     mid        ro     roflg   intfail        en        et       gic      giic
       @CZM_MID@       2.0         0       1.0     20000     10000       0.5       0.5
      $#     xmu         t         s       und       utd     gamma
             2.0       1.0       1.0
```

REMAP 스텝: `params.op=offset`, `params.config`=위 YAML dict.

### 인자

| 필드 | 필수 | 설명 | 기본값 |
|---|---|---|---|
| `source_pid` | 예 | 소스(표면) 파트 ID | — |
| `element_type` | 아니오 | `solid` / `tshell` / `shell` | `solid` |
| `thickness` | 예 | 균일 오프셋 두께 | — |
| `thickness_formula` | 아니오 | 가변 두께 수식(x/y/z 변수) | — |
| `num_layers` | 아니오 | 레이어 수 | 1 |
| `offset_direction` | 예 | 압출 방향(`+normal` 등) | — |
| `connection_mode` | 아니오 | `tied` / `czm` / `contact` / `none` | `tied` |
| `new_pid` | 아니오 | 새 파트 ID | 자동 |
| `part_title` | 아니오 | 파트 제목 | — |
| `use_local_normals` | 아니오 | 곡면 노드별 평균 법선 사용 | `false` |
| `material_card` | 아니오 | 인라인 재료 카드. 첫 `*MAT` MID 칸(`@MID@`·숫자·라벨)이 새 MID 로 바뀜 | — |
| `material_cards` | 아니오 | 층마다 다른 재질 `- \|` 목록(단독·assemble 모두) | — |
| `czm_material_card` | czm | CZM cohesive 재료 카드(MID 칸 `@CZM_MID@` 등이 새 MID 로) | — |
| `new_secid` / `new_mid` | 아니오 | 새 SECID·MID 지정(이후 자동 발급 ID 와 겹치지 않음) | 자동 |

품질 검증 (정본 §22): Aspect Ratio warn>10 / error>20, Jacobian warn<0.1 / error<-1e-10, Warping warn>30° / error>45°.

### 예제

```yaml
# examples/offset/06_czm_connection.yaml — CZM 연결(층간 응집 요소)
base_model: ../arc30/arc30_flat.k
output: 06_czm_result
operations:
  - type: offset
    source_pid: 1
    element_type: solid
    thickness: 1.0
    num_layers: 1
    offset_direction: +z
    connection_mode: czm
    new_pid: 10
    material_card: |
      *MAT_ELASTIC
      $#     mid        ro         e        pr
           @MID@       2.0     12000      0.25
    czm_material_card: |
      *MAT_COHESIVE_MIXED_MODE
      $#     mid        ro     roflg   intfail        en        et       gic      giic
       @CZM_MID@       2.0         0       1.0     20000     10000       0.5       0.5
      $#     xmu         t         s       und       utd     gamma
             2.0       1.0       1.0
```

`examples/offset/01_basic_solid_tied.yaml`은 tied + `+z` 최소 예제다.

### 동작 원리

(1) `source_pid` 표면을 추출하고, (2) 노드별(`use_local_normals`) 또는 전역 법선/축 방향으로 `thickness`(또는 `thickness_formula`)만큼 `num_layers`를 압출해 HEX8 솔리드를 생성한 뒤, (3) `connection_mode`에 따라 원본과 결합하고, (4) 요소 품질을 자동 검증한다. (정본 §22, help)

### 주의사항

- `connection_mode` 는 `tied`(기본) / `czm` / `contact` / `none` 이며 단독·assemble 모두 같은 값만 받는다(정본 §22 정정, 구버전 `shared` 아님). 다른 값·`element_type: hex` 등은 단독 `offset` 에서도 오류로 거부된다(`restack` 도 같다).
- 재료 카드 값은 LS-DYNA 고정 폭 10열 칸 안에 둔다. 예전 예시(`@MID@  2.0  12000  0.25`)처럼 칸을 벗어나면 LS-DYNA 가 다른 칸으로 읽는다. CZM 카드는 MAT_138 배치(1행 MID·RO·ROFLG·INTFAIL·EN·ET·GIC·GIIC, 2행 XMU·T·S·UND·UTD·GAMMA)를 따른다.
- 예전 결함(수정됨): MID 칸이 5열 밀림, 카드 끝 줄바꿈 누락으로 `0.25*END` 붙음, CZM 파트가 기존 PID·SECID 와 충돌, `@CZM_MID@` 미치환, assemble 의 `connection_mode: none` 거부, 단독 offset 의 `material_cards` 누락.
- 소스 표면의 일부만 처리하려면 region 필터(bbox / nodeId / elementId)를 쓴다. (help; 정본 §22의 `bbox_*`/`node_id_*`/`element_id_*` 필드)
- 전체 예제는 `examples/offset/README.md` 참조. (help)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).

---

## wrap

### 용도

와인딩 공정의 **인장 프리스트레스**(후프 + 반경 응력)를 부여한다. 와이어/섬유 와인딩 또는 압입(press-fit) 원통 인장을 모델링한다. (정본 §33, help)

### 호출형태

```
KooRemapper wrap <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper wrap wrap_test.yaml
```

config 형식 (examples/wrap, help) — flat 스키마(`operations` 래퍼 없음).

```yaml
model: cylinder.k
output: cylinder_wrapped
target_pid: [1, 2]      # 하나 이상의 파트 ID
axis: z                 # 와인딩 축 x | y | z
tension: 100.0          # 와인딩 인장력 [force/length]
center: [0.0, 0.0]      # 축 중심(선택, 자동 감지)
material:
  E: 210000.0
  nu: 0.3
```

REMAP 스텝: `params.op=wrap`, `params.config`=위 YAML dict.

### 인자

| 필드 | 필수 | 설명 | 기본값 |
|---|---|---|---|
| `model` | 예 | 입력 K-파일 | — |
| `output` | 예 | 출력 접두어 | — |
| `target_pid` | 예 | 대상 파트 ID(하나 이상, 리스트) | — |
| `axis` | 예 | 와인딩 축 `x`/`y`/`z` | — |
| `tension` | 예 | 와인딩 인장력 | — |
| `center` | 아니오 | 축 중심 좌표 `[c1, c2]` | 자동 감지 |
| `material.E`, `material.nu` | 예 | 탄성계수 / 포아송비 | — |

물리 모델 (정본 §33): 후프 σ_θθ = tension, 반경 σ_rr = -tension × (r_outer/r − 1) / ln(r_outer/r_inner). 이후 원통→전역 좌표로 응력 변환.

### 예제

```yaml
# examples/wrap/wrap_test.yaml
model: cylinder_2layer.k
output: cylinder_wrapped
material:
  E: 210000.0
  nu: 0.3
target_pid: [1, 2]
axis: z
tension: 100.0
```

### 동작 원리

원통 좌표계(r, θ, z)에서 후프 인장·반경 압축 응력을 계산해 프리스트레스 dynain을 생성한다. 본 해석 전 `relax` 명령이나 `dynamic_relaxation: true`로 평형화한 뒤 사용한다. (정본 §33, help)

### 주의사항

- `tension` 단위가 근거마다 다르게 표기된다. help는 `[force/length]`, 정본 §33은 MPa로 기술한다. 모델의 단위계에 맞춰 해석해야 한다. (정본 §33, help)
- 축 중심 필드명은 help·example이 `center`, 정본 §33은 `axis_center`다. 여기서는 help·example 기준의 `center`를 썼다. (help, examples/wrap)
- 생성된 프리스트레스는 반드시 relax로 평형화 후 본 해석에 넘긴다. (help)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).

---

## restack

### 용도

셸 표면을 서로 다른 두께·재료의 **솔리드 레이어 스택**으로 압출한다. 다층 솔리드 스택 조립(assemble) 파이프라인에 쓰인다. (정본 §12, help)

### 호출형태

```
KooRemapper restack <config.yaml>
```

컨테이너 실행 예.

```
# operations 가 하나뿐인 설정만 단독 restack 으로 돌릴 수 있다
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper restack assemble_restack_test.yaml
```

> `examples/disconnect/restack_czm.yaml` 은 `operations` 가 2개(restack + disconnect)라 **단독 `restack` 으로는 돌지 않는다**:
> `[ERROR] [restack] restack_czm.yaml 에 operations 항목이 2개 있습니다 — 단독 명령은 한 항목만 적용합니다` 뒤에
> `'KooRemapper assemble restack_czm.yaml' 로 실행하세요` 가 뜨고 rc=1 이다. 여러 op 을 이어 붙인 설정은 `assemble` 로 실행하라.
> 단독 `restack` 은 `operations` 가 하나인 설정에만 쓴다(예: `examples/replace_test/assemble_restack_test.yaml` — 실행 확인됨).

config 형식 (examples/disconnect/restack_czm.yaml, help).

```yaml
base_model: shell.k
output: solid_stack
operations:
  - type: restack
    target_pid: 1          # 소스 셸 파트 ID
    direction: z           # auto | x | y | z (정본), help 예시는 +z
    element_type: solid    # solid | tshell | shell 만 (그 밖은 rc=1)
    layers:
      - thickness: 0.5
        material_card: |
          *MAT_ELASTIC
          ...
      - thickness: 0.2
        material_card: |
          *MAT_ELASTIC
          ...
```

REMAP 스텝: `params.op=restack`, `params.config`=위 YAML dict.

### 인자

| 필드 | 필수 | 설명 | 기본값 |
|---|---|---|---|
| `base_model` | 예 | 입력 K-파일 | — |
| `output` | 예 | 출력 접두어 | — |
| `operations[].type` | 예 | `restack` | — |
| `operations[].target_pid` | 예 | 소스 셸 파트 ID | — |
| `operations[].direction` | 아니오 | 적층 방향 `auto`/`x`/`y`/`z` | `auto` (정본 §12) |
| `operations[].element_type` | 아니오 | `solid` / `tshell` / `shell` **만**. 그 밖의 값(`hex`, 오타, 대문자 `SOLID` 포함)은 rc=1 이고 출력이 안 만들어진다 — 예전에는 전부 조용히 `solid` 였다. 층(`layers[].element_type`)도 같고, 층에서 비우면 op 값을 물려받는다 | `solid` |
| `operations[].pid_refs` | 아니오 | `strict` \| `warn`. 비운 PID·지운 요소·지운 노드를 가리키는 자리를 다 옮기지 못했을 때 `strict` 는 덱을 쓰고 **rc=1**, `warn` 은 같은 보고를 하고 rc=0. 아래 참조 이전 절 참고 | `strict` |
| `operations[].layers[]` | 예 | 레이어 리스트(`thickness` + `material_card`) | — |

### 예제

이 예제는 `operations` 가 2개이므로 `KooRemapper assemble restack_czm.yaml` 로 실행한다.

```yaml
# examples/disconnect/restack_czm.yaml — 3층 스택 후 disconnect(czm) 체이닝 (assemble 로 실행)
base_model: three_layer.k
output: restack_czm_result
operations:
  - type: restack
    target_pid: 1
    direction: z
    element_type: solid
    layers:
      - thickness: 1.0
        material_card: |
          *MAT_ELASTIC
               MAT01  7.85E-09    210000       0.3
      - thickness: 1.0
        material_card: |
          *MAT_ELASTIC
               MAT02  7.85E-09    140000       0.3
      - thickness: 1.0
        material_card: |
          *MAT_ELASTIC
               MAT03  7.85E-09     70000       0.3
  - type: disconnect
    mode: czm
    target_pid: 0
```

### 동작 원리

(1) `target_pid` 파트의 요소를 분석해 두께 방향을 결정하고, (2) 표면 메시(QUAD4)를 추출한 뒤, (3) 각 레이어를 누적 두께로 압출하고, (4) 재료 카드를 등록하며 새 파트/섹션/재료 ID를 발급한다. 각 레이어는 새 PID/MID를 자동으로 받는다. (정본 §12, help)

### 주의사항

- 층 `material_card` 의 첫 `*MAT` MID 칸(1~10열, `_TITLE` 이면 제목 다음 줄)에 `MID001`·`MAT01` 같은 **자리표시자**를 쓰면 새 MID 로 바뀌고, 라벨과 카드 내용이 같은 층끼리만 MID 를 공유한다(라벨이 같아도 물성이 다르면 따로 발급). 같은 MID 를 가리키는 `*MAT_ADD_…` 도 함께 바뀐다. (정본 §12)
- **숫자를 직접 적으면 그 번호를 그대로 쓴다**(2026-09-18 실행 확인). 이미 쓰이는 번호면 새 번호를 주고 `Restack layer 2: material MID 90 is already in use -> assigned MID 91` 로 알린다.
- `*MAT_..._TITLE` 카드에 **제목 줄이 없으면** 데이터 줄을 제대로 읽고 `[WARN] Restack layer N: *MAT_..._TITLE card had no title line -> filled it with '<layers[].title>'` 을 낸 뒤 **빠진 제목 줄을 그 층 제목으로 채워** 내보낸다. 키워드 줄 뒤에 **데이터 줄 자체가 없는** 카드는 rc=1 이다.
- 대상 파트가 **강체**(`*MAT_RIGID`/`*MAT_020` 또는 `*PART_INERTIA`)면 restack 을 시작하지 않고 rc=1 로 거부한다 (`restack: PID 1 는 *MAT_RIGID(MID 1) 강체 파트입니다 … / cannot restack a rigid part`).
- 새 층이 원 `*SECTION` 의 **ELFORM** 과 원 `*PART` 의 **HGID·TMID** 를 물려받는다. ELFORM 은 같은 요소 종류끼리만 물려준다(`*SECTION_SOLID` 의 2 와 `*SECTION_SHELL` 의 2 는 다른 정식이다). **EOSID 는 물려주지 않는다.**
- 예전 결함(수정됨): MID 칸에 숫자를 쓰면 층 PART mid 가 0 이 되고 카드가 빠짐, 단독 restack 에서 제목에 `:` 가 있으면 카드가 잘림, 마지막 층 카드 뒤 빈 줄 때문에 같은 카드가 MID 를 따로 받음.
- `disconnect` op을 restack 뒤에 이어 붙여 CZM/Peri 분리에 쓸 수 있다. (help, examples/disconnect/restack_czm.yaml)

### 참조 이전과 `pid_refs` — **기본이 rc=1 이다** (2026-09-18 실행 확인)

restack 은 대상 파트를 층으로 나누며 층마다 **새 PID/SECID/MID** 를 준다. 원 `*PART` 카드는 요소 0 개로 남고,
두께 방향 요소가 2 개 이상이면 원 중간면 노드도 사라진다. 그래서 그것들을 가리키던 카드
(`*SET_PART_*`·`*CONTACT_*`·`*SET_SOLID`·`*BOUNDARY_SPC_NODE`·`*SET_SEGMENT` …)가 아무 일도 하지 않는 채 남는다.
지금은 도구가 **죽은 PID / 지워진 요소(EID) / 지워진 노드(NODE)** 세 축을 훑어 옮길 수 있는 것은 옮기고,
나머지는 보고한다.

- 옮기는 것: 체적 의미의 `*SET_PART_LIST/_TITLE/_COLUMN` → 층 PID 전부. tied 계열 접촉
  (`*CONTACT_*TIED*`/`*TIEBREAK*`/`*SPOTWELD*`/`*CONTACT_CONSTRAINT_*`)은 상대측 기하를 적층 축에 투영해
  **층이 유일하게 정해질 때만** 그 층으로. 한 세트를 tied 와 체적 소비자가 함께 쓰면 세트를 복제해 가른다.
  그 밖의 접촉은 모든 층이 solid 일 때 층 전부를 담은 세트로 바꾼다(STYP 3→2).
- **restack 이 못 옮기는 것**: 칸 하나에 층 N 개를 담을 수 없는 스칼라 PID 칸
  (`*DAMPING_PART_MASS`/`_STIFFNESS`, `*DATABASE_HISTORY_PART`, `*MAT_ADD_THERMAL_EXPANSION`, `*PART_MOVE`,
  `*BOUNDARY_PRESCRIBED_MOTION_RIGID`, `*DEFORMABLE_TO_RIGID`, `*INITIAL_VELOCITY_GENERATION`, `*ELEMENT_MASS`)은
  `manual`(직접 고치세요)로 남는다. 새 PID 가 하나뿐인 `merge` 는 같은 칸들을 실제로 바꿔 준다 — 두 op 의 차이다.
  `*INCLUDE` 가 있는 덱은 세트의 소비자를 다 볼 수 없어 세트를 펴지 않고 보고만 한다.
- 가리키던 자리를 하나라도 찾으면 산출 덱 머리(`*KEYWORD` 바로 뒤)에 `$ KOOREMAPPER-PIDREF` 블록이 들어간다
  (찾은 것이 없으면 블록도 없다). 등급 `moved` / `left` / `manual` / `unknown` / `maybe`(화이트리스트 밖 —
  **rc 에 넣지 않는다**). 블록의 줄 번호는 **입력 덱 기준**이다.

| 키 | 값 | 기본 | 뜻 |
|---|---|---|---|
| `pid_refs` | `strict` \| `warn` | `strict` | `strict`: 못 옮긴 자리(= `maybe` 제외)가 남으면 **덱은 쓰고 rc=1**. `warn`: 같은 보고를 하고 rc=0. 그 밖의 값은 rc=1 + 산출물 없음 — `invalid pid_refs '<값>' (must be one of strict, warn)` |

쓰는 자리는 단독 YAML 의 op 수준과 `assemble` 의 `operations[]` 항목 두 곳이다.

> ⚠ **기존 REMAP 체인이 여기서 멈출 수 있다.** `Runner/KooRemapperStep.py` 는 `returncode != 0` 이면
> `RuntimeError(f"KooRemapper {operation} failed (exit {proc.returncode}): …")` 를 던지고,
> `Runner/CumulativeScenarioRunner.py` 의 `_run_kooremapper_step` 은 `result.returncode != 0` 에
> 스텝을 `status: "failed"` 로 적고 `False` 를 돌려준다. 어느 쪽도 stdout 경고를 읽지 않으므로,
> **예전에 rc=0 으로 조용히 지나가던 덱이 이제 체인을 멈춘다.** 산출 덱은 그래도 쓰여 있다.
> 조치 순서: (1) 산출 덱 머리의 `$ KOOREMAPPER-PIDREF` 블록에서 무엇이 `left`/`manual` 인지 읽고
> 그 카드를 고친다, (2) 알고도 넘기려면 그 op 에 `pid_refs: warn` 을 준다(같은 보고, rc=0).
> `warn` 은 참조를 고쳐 주지 않는다 — 덱은 그대로 솔버로 간다.

```json
{
  "mode": "REMAP",
  "params": {
    "op": "restack",
    "config": {
      "target_pid": 1,
      "direction": "z",
      "pid_refs": "warn",
      "layers": ["..."]
    }
  }
}
```

> `_run_kooremapper_step` 은 `params.config` 에 `model`/`output` 을 자동 주입하므로 위 dict 에는 적지 않는다
> (`cfg["model"] = "input.k"`, `cfg["output"] = "Remap_dti.k"`). 그래서 체인이 만드는 설정은 `base_model`/`operations`
> 형태가 아니라 **op 수준 평평한 형태**이고, `pid_refs` 도 그 수준에 둔다.

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).

---

## update

> 정본 매뉴얼에 `update` 독립 절은 없고, assemble 챕터 §39.18에 operations 형태로만 기술돼 있다. 아래 flat 스키마(model/output/dynain)는 v1.8.0 **help(Usage) 기준**이며, help에 없는 세부 옵션·기본값은 근거가 없어 생략했다.

### 용도

dynain 또는 K-파일의 `*NODE` 블록을 읽어 모델의 **일치 노드 좌표를 덮어쓴다**. 불일치 노드는 그대로 둔다. (help)

### 호출형태

```
KooRemapper update <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper update update.yaml
```

config 형식 (help) — flat 스키마.

```yaml
model:  original.k
output: updated.k
dynain: dr_result.dynain   # *NODE 블록을 가진 임의 파일
```

assemble/체인에서는 operations 항목으로도 쓸 수 있다 (help).

```yaml
operations:
  - type: update
    dynain: dr_result.dynain
```

REMAP 스텝: `params.op=update`, `params.config`=위 YAML dict.

### 인자

| 필드 | 필수 | 설명 | 기본값 |
|---|---|---|---|
| `model` | 예 | 원본 K-파일 | — |
| `output` | 예 | 출력 파일 | — |
| `dynain` | 예 | `*NODE` 블록을 포함한 소스 파일(dynain/K-file 등) | — |

### 동작 원리

소스 파일의 `*NODE` 블록을 읽어 model과 소스 양쪽에 존재하는 노드만 좌표를 갱신한다. 소스에만 있고 model에 없는 노드는 조용히 건너뛴다. `*NODE`를 포함한 어떤 파일과도 동작한다. (help)

### 주의사항

- 정본 독립 절은 없고 assemble §39.18에 operations 형태로만 있다. flat 스키마는 help(Usage) 기준으로 기술했으며, 그 밖의 옵션·기본값은 근거가 없어 생략했다. (정본 §39.18, help)
- model과 소스 양쪽에 있는 노드만 갱신되고 나머지는 유지된다. 다른 assemble op과 체이닝할 수 있다. (help)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인). 정본은 assemble 챕터 §39.18에 operations 형태로 기술.

---

## iga

### 용도

FE solid 파트를 **3D NURBS trivariate 박스**로 래핑해 LS-DYNA IGA(Isogeometric Analysis) 해석이 가능하게 변환한다. 각 대상 FE 파트를 감싸는 `*IGA_DEV_VOLUME_XYZ` 패치를 생성한다. (정본 §20, help)

### 호출형태

```
KooRemapper iga <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper iga iga_single.yaml
```

config 형식 (examples/iga, help).

```yaml
base_model: block_2x2x1.k
output: result
operations:
  - type: iga
    targets:
      - target_pid: 1          # 단일 파트
        element_size: 4.0       # NURBS 박스 복셀 크기(rr=rs=rt 공통)
        ir: 0                   # 적분 유형 0=reduced Gauss, 1=full Gauss
        pr: 2                   # 다항식 차수 r (min 1)
        ps: 2                   # 다항식 차수 s
        pt: 1                   # 다항식 차수 t
        bbox_scale: 1.4         # bbox 확장 배율
      - target_pids: [2, 3]     # 여러 파트 동일 설정
        element_size: 3.0
```

REMAP 스텝: `params.op=iga`, `params.config`=위 YAML dict.

### 인자

`operations[].targets[]` 각 항목의 필드 (정본 §20, help).

| 필드 | 설명 | 기본값 |
|---|---|---|
| `target_pid` / `target_pids` | 단일 파트 ID / 여러 파트 리스트(동일 설정) | — |
| `element_size` | NURBS 복셀 크기(rr=rs=rt 공통) | — |
| `element_size_r/s/t` | 축별 개별 크기(0=`element_size` 사용) | 0 |
| `offset` | bbox 확장량(-1=auto) | -1 |
| `bbox_scale` | 균일 확장 배율 | — |
| `bbox_scale_r/s/t` | 축별 확장 배율 | — |
| `ir` | 적분 유형(0=reduced Gauss, 1=full Gauss) | 0 |
| `styp` | LCP stabilization type | — |
| `tollg` | LCP threshold | — |
| `pr/ps/pt` | 다항식 차수(r/s/t, min 1) | — |
| `nisr/niss/nist` | 적분점 수(r/s/t) | — |

확장(offset) 우선순위 (정본 §20, 높→낮): `bbox_scale_r/s/t` > `bbox_scale` > `offset ≥ 0` > 축별 `element_size`.

생성 파일 (정본 §20, help): `<output>.k`(원본 FE 유지 + `*INCLUDE`), `<output>_iga_p{N}.k`(파트별 IGA 파일).

### 예제

```yaml
# examples/iga/iga_multipid.yaml — target_pids로 여러 파트 일괄 처리
base_model: block_2x2x1.k
output: iga_multipid_result
operations:
  - type: iga
    targets:
      - target_pids: [1, 2]
        element_size: 4.0
        ir: 0
        pr: 2
        ps: 2
        pt: 1
        bbox_scale: 1.4
```

`examples/iga/iga_single.yaml`은 `target_pid: 1` + `element_size: 4.0`의 최소 설정이다.

### 동작 원리

각 대상 FE 파트의 bounding box를 offset/scale 규칙으로 확장한 뒤, `element_size`와 다항식 차수(`pr/ps/pt`)로 NURBS trivariate 박스를 생성한다. 원본 FE는 유지하고 `*INCLUDE`로 파트별 IGA 파일을 연결한다. (정본 §20, help)

### 주의사항

- IGA 파트와 일반 FE 파트는 반드시 서로 다른 MID를 써야 한다(LS-DYNA 요구). (정본 §20, help)
- 방향별 제어점 수 = max(2, pr+1). LS-DYNA R12 이상이 필요하다. (help)
- `target_pid`(단수)와 `target_pids`(복수)는 혼용할 수 있다. (examples/iga)
- 전체 문서는 `examples/iga/iga_guide.md` 참조. (help)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).
