# KooRemapper ops — 메시 편집(convert · refine · elform · disconnect · offset · wrap · restack · update · iga · cleanup-nodes · extract-parts · cad_solid_merge_to_deck · rebind_entities_after_remesh · id_floor)

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

### 2026-10 정본 대조

- `mefem` 의 새 `*SET_NODE` 번호가 덱 · 인클루드의 기존 `*SET_NODE` 위에서 난다(관례 `PID 최대 + 1000` 은 바닥으로 남는다 — 2026-10-15. 그 전에는 기존 세트를 보지 않아 같은 SID 를 다시 냈다). 겹치지 않는 덱은 번호가 그대로다.

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

### 2026-10 정본 대조

- ★`element_type: tshell` 산출이 **진짜 TSHELL 덱**이다(2026-10-16) — 8절점 `*ELEMENT_TSHELL`(그 전에는 4절점 `*ELEMENT_SHELL` 로 써서 윗면 절점 넷이 빠졌다) · `*SECTION_TSHELL` ELFORM 1(16 은 TSHELL 정식이 아니다) · 섹션은 Card 1 만 · 삼각 바닥은 매뉴얼의 쐐기 꼴.
- ★TSHELL 도 `connection_mode` 를 솔리드와 같은 뜻으로 받는다(2026-10-16) — `tied`(기본) · `none` 이면 0층이 원본 면 절점을 공유해 붙고, `czm` 은 복제한 절점과 원본 면 사이에 코히시브(ELFORM 20)를 면 수만큼 만들고, `contact` 는 복제해 떼고 접촉 안내를 붙인다. 그 전에는 기본값으로 만든 층이 원본 면에서 떠 있었다.
- ⚠ `element_type: shell` + `connection_mode: czm` 은 **적용되지 않는다** — rc 0 인데 코히시브를 하나도 만들지 않고 말도 하지 않는다(2026-10-16 실측). 셸 층에는 czm 을 주지 마라.
- 새 셸 EID 가 덱의 요소 EID 와 겹치던 것을 고쳤다(셸 · TSHELL 도 요소 공용 커서). 정본 §22 · 회귀 `test_offset_tshell_deck.py`.

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

- 옮기는 것: 체적 의미의 `*SET_PART_LIST/_TITLE` → 층 PID 전부(한 줄 8 개 규칙을 지켜 줄을 늘린다).
  `*SET_PART_COLUMN` 은 구성원마다 딸린 칸이 있어 죽은 PID 줄을 층마다 한 줄씩으로 늘린다(딸린 칸은 그대로 복사).
  tied 계열 접촉(이름에 `TIED`·`TIEBREAK`·`SPOTWELD`·`CONSTRAINT` 가 있는 것)은 상대측 기하를 적층 축에 투영해
  **층이 유일하게 정해질 때만** 그 층으로. 한 세트를 tied 와 체적 소비자가 함께 쓰면 세트를 복제해 가른다(새 SID 발급).
  미끄러지는 계열(`AUTOMATIC`·`ERODING`·`SINGLE_SURFACE`·`SLIDING`·`FORMING`·`DRAWBEAD`·`ONE_WAY`·
  `SURFACE_TO_SURFACE`·`NODES_TO_SURFACE`)은 모든 층이 solid 일 때 층 전부를 담은 세트로 바꾼다(STYP 3→2).
  두 목록 어디에도 없는 이름은 안전한 쪽인 tied 로 본다 — `*CONTACT_ENTITY`·`*CONTACT_FORCE_TRANSDUCER_PENALTY`
  처럼 묶지 않는 카드도 한 층으로 붙으니 결과를 확인한다.
- **restack 이 못 옮기는 것**: 칸 하나에 층 N 개를 담을 수 없는 스칼라 PID 칸
  (`*DAMPING_PART_MASS`/`_STIFFNESS`, `*DATABASE_HISTORY_PART`, `*MAT_ADD_THERMAL_EXPANSION`, `*PART_MOVE`,
  `*BOUNDARY_PRESCRIBED_MOTION_RIGID`, `*DEFORMABLE_TO_RIGID`, `*INITIAL_VELOCITY_GENERATION`)은
  `manual`(직접 고치세요)로 남는다. 새 PID 가 하나뿐인 `merge` 는 이 칸들을 실제로 바꿔 준다 — 두 op 의 차이다.
  단 `*ELEMENT_MASS`(`_PART` 포함)는 예외로 **두 op 모두** `manual` 이다 — 집중질량은 나눠 주지 않으니 직접 배분한다.
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

### 2026-10 정본 대조

- 두께 방향 컬럼 높이가 **불균일하면 rc=1 로 거절**한다 — `[ERROR] Part N: non-uniform column heights - not a valid extrusion`. 슬릿·구멍 때문에 컬럼마다 높이가 다른 격자(지지격자 등)는 대상이 아니다(의도된 가드 · 컬럼별 모드는 없다).
- 계면(tied/CZM)은 **한 연산 안의 층 사이**에만 만든다. 이미 나뉜 적층의 요소 타입만 바꾸려고 1층짜리 restack 을 층마다 돌리면 셸이 아무것에도 묶이지 않는다 — 그때 `셸 층을 만들었는데 계면이 0건입니다` 를 경고한다. 묶으려면 그 층들을 한 연산에 함께 넣는다.
- 정본 §12.

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

---

## cleanup-nodes

### 용도

아무도 참조하지 않는 절점을 보고(기본)·삭제 + 세트 정리.

덱에서 아무것도 가리키지 않는 절점을 보고(기본)하거나 지운다 — 숫자를 긁지 않고 키워드마다 칸을 읽는다.

### 호출 형태

config YAML 파일 경로를 위치 인자로 받는 yaml-config op 다.

```
KooRemapper cleanup-nodes <config.yaml>
```

근거 — 바이너리 `help cleanup-nodes` 의 사용법(2026-10-16 · SmartTwinPreprocessor.sif 판).

### config YAML 인자

| 키 | 필수 · 기본 | 설명 |
|---|---|---|
| `model` | 필수 | 입력 K-파일(또는 `input`). 참조를 셀 때 `*INCLUDE` 를 따라간다 |
| `output` | 선택 | 출력 K-파일. mode 가 safe·force 일 때만 쓴다. 기본은 입력 이름에 `_clean` |
| `mode` | 기본 `report` | `report`(기본)는 분류만 하고 덱을 쓰지 않는다. `safe` 는 이해하는 키워드도 모르는 키워드도 가리킬 수 없는 절점만 지우고, 못 읽은 `*INCLUDE` 가 있으면 거절한다. `force` 는 모델링하지 않는 키워드만 가리키던 절점까지 지우고 `force_deleted_despite_unknown` 에 센다 |
| `prune_sets` | 기본 `True` | 지운 절점을 `*SET_NODE`·`*SET_NODE_LIST`·`*SET_NODE_COLUMN` 구성원에서 뺀다. 끄면 세트가 없는 절점을 가리키게 되고 되읽기 검증이 실패로 보고한다 |
| `verify` | 기본 `True` | 쓴 덱을 다시 읽어 모든 요소 절점 참조와 절점 세트 구성원이 정의돼 있는지 본다. 아니면 0 이 아닌 종료 |
| `keep_referenced_by` | 기본 `['CONSTRAINED_NODAL_RIGID_BODY', 'BOUNDARY_SPC_NODE', 'DATABASE_HISTORY_NODE', 'CONSTRAINED_EXTRA_NODES', 'INITIAL_VELOCITY_NODE']` | 보고에서 이름으로 귀속하고 `mode: force` 에서도 지키는 키워드 접두사(앞의 `*` 없이). 이 목록에 없는 키워드도 여전히 훑고 그 절점을 지킨다 — `unknown_keyword_kept` 로 보고될 뿐이다 |
| `report` | 선택 | 분류를 JSON 으로 쓴다 — 절점 수 · 키워드별 kept_by · unknown_keyword_kept · sets_pruned · verify · bbox_before/after |

### 예제

KooRemapper 저장소 예제다 — 같은 형식의 자기 모델로 바꿔 쓴다.

`cn.yaml`

```yaml
model: examples/cleanup-nodes/cleanup_demo.k
output: cleaned.k
mode: safe
report: cleanup_report.json
```

직접 실행이다(필요한 입력을 작업 폴더에 둔다).

```bash
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper cleanup-nodes cn.yaml
```

필요한 입력 — `examples/cleanup-nodes/cleanup_demo.k`

**체인(REMAP 스텝)으로 쓸 수 있다.** 체인의 입력 덱에 바로 적용된다.

```yaml
params:
  op: cleanup-nodes
  config:
    mode: safe
    report: cleanup_report.json
```

`model` 과 `output` 은 러너가 넣는다(`input.k` → `Remap_dti.k`).

### 주의사항

- **기본 `mode` 는 `report` 다 — 덱을 쓰지 않는다.** 지우려면 `mode: safe` 를 적어야 한다
- ★`*SET_NODE_*` **멤버십은 참조로 세지 않는다.** 운영 덱에는 '전체 절점' 세트가 있고 그 블록은 모든 절점 ID 를 글자 그대로 담는다 — 그걸 참조로 세면 고아가 **전부** 가려진다 (실측: 13.4M 절점 덱에서 고아 118,568개가 '전부 참조됨' 으로 나온 원인이 이것이다) 대신 지운 절점을 **세트에서 뺀다**(`prune_sets`, 안 빼면 LS-DYNA `Error 10233`)
- ★반대 실수도 똑같이 나쁘다 — CNRB 는 절점을 **NSID 로** 가리킨다. 그래서 세트를 **이름하는 카드**가 있으면 그 멤버를 전이로 남긴다(그 덱의 CNRB 71건이 이 경로다)
- ★`safe` 의 뜻은 '**내가 이해한 것만 지운다**' 다 — 모르는 키워드도 전수 훑어서, 삭제 후보와 같은 정수를 가지면 남기고 `unknown_keyword_kept` 에 적는다. 그래서 안전을 만드는 것은 `keep_referenced_by` **목록이 아니라 전수 훑기**다 (목록은 귀속을 적고 `mode: force` 에서만 갈라진다)
- `*INCLUDE` 를 **읽는다** — 안 읽으면 인클루드가 쓰는 절점을 고아로 보고 지운다. `safe` 는 못 읽은 인클루드가 하나라도 있으면 **쓰지 않는다**(rc=1). 인클루드 안에 정의된 절점은 **지우지 않는다**(주 덱만 다시 쓴다)
- ★`bbox_before`/`bbox_after` 를 반드시 낸다 — 이 op 이 생긴 까닭이다. 기기 두께가 14.55mm 인데 `*NODE` bbox 가 67.50mm 라 낙하판이 기기에서 **53mm 밖**에 생겼다. 두 bbox 를 나란히 보면 그 중 얼마가 애초에 형상이 아니었는지가 보인다
- 산출 덱을 **되읽어** 증명한다 — 요소가 쓰는 절점·세트 멤버가 전부 있는지 보고, 없으면 rc≠0 이다(`prune_sets: false` 로 일부러 깨면 그 자리에서 잡힌다)
- 칸 폭은 덱을 따른다 — 고정폭을 **먼저** 읽고, 칸 하나에 두 수가 든 경우에만 공백으로 되돌린다. 절점 ID 8자리는 8칸을 꽉 채우므로 공백 분해를 먼저 하면 한 토큰으로 읽혀 **요소가 쓰는 절점을 전부 지운다**(실측으로 재현했다)

### 개발 현황

바이너리(v1.8.0 · 63 op 판, 2026-10-16 SIF)에 있다. 정본 `KooRemapper/docs/KooRemapper_Manual.md` §47 · 회귀 `tools/regress/test_cleanup_nodes.py`.

---

## extract-parts

### 용도

고른 파트만 뽑아 **돌아가는** 덱으로 (ID·칸폭·CRLF 보존).

고른 파트만 든 덱을 쓴다 — 모든 ID · 칸 폭 · 개행을 그대로 두고, 다시 읽어 빠진 참조를 보고한다.

### 호출 형태

config YAML 파일 경로를 위치 인자로 받는 yaml-config op 다.

```
KooRemapper extract-parts <config.yaml>
```

근거 — 바이너리 `help extract-parts` 의 사용법(2026-10-16 · SmartTwinPreprocessor.sif 판).

### config YAML 인자

| 키 | 필수 · 기본 | 설명 |
|---|---|---|
| `model` | 필수 | 입력 K-파일(또는 `input`). `*INCLUDE` 를 따라가 산출에 펼쳐 넣는다 |
| `output` | 선택 | 출력 K-파일. 기본은 입력 이름에 `_extracted` |
| `parts` | 선택 | 뽑을 PID 목록. 덱에 없는 PID 는 빈 덱을 조용히 내지 않고 거절한다. 이것이나 part_titles 하나는 있어야 한다 |
| `part_titles` | 선택 | `*PART` 제목에 맞출 패턴(`*`·`?` 와일드카드, 대소문자 무시). 아무것도 안 맞는 패턴은 거절한다 |
| `renumber` | 기본 `False` | 절점·요소를 1부터 다시 매기고 `<output>_renumber_map.json` 에 옛→새 짝을 쓴다. 줄마다 칸 0 만 제자리에서 바꿔 좌표 글자는 바이트 그대로다. 두 요소 갈래가 같은 EID 를 쓰면 거절한다 |
| `verify` | 기본 `True` | 쓴 덱을 다시 읽어 정의되지 않은 절점·파트·섹션·재질을 보고한다. 하나라도 있으면 0 이 아닌 종료 |
| `include.nodes` | 기본 `True` | 뽑은 요소가 쓰는 `*NODE` 줄을 싣는다 |
| `include.sets` | 기본 `referenced` | `referenced` 는 `*SET_NODE`·`*SET_PART`·`*SET_SOLID`·`*SET_SHELL`·`*SET_TSHELL` 을 산출에 있는 것으로 줄이고, 네 절점이 모두 남는 `*SET_SEGMENT` 면만 남긴다. 구성원을 ID 로 읽을 수 없는 변종(`_GENERATE`·`_GENERAL`·`_ADD`·`_INTERSECT`)은 빼고 그 SID 를 적는다 |
| `include.materials` | 기본 `True` | 고른 파트가 쓰는 `*MAT_*`·`*EOS_*`·`*HOURGLASS` 블록과 `*DEFINE_CURVE`·`*DEFINE_TABLE`(숫자뿐 — 절점 참조 없음)을 싣는다. 정의가 여럿 든 블록은 통째로 싣고 센다 |
| `include.sections` | 기본 `True` | 고른 파트가 쓰는 `*SECTION_*` 블록을 싣는다 |
| `report` | 선택 | 결과를 JSON 으로 쓴다 — 고른 파트 · 집은 수 · 필요한 섹션/재질 ID · 줄이고 뺀 세트 · 뺀 키워드 · 재번호 표 경로 · 되읽기 검증 |

### 예제

KooRemapper 저장소 예제다 — 같은 형식의 자기 모델로 바꿔 쓴다.

`ep.yaml`

```yaml
model: examples/extract-parts/assembly.k
output: extracted.k
parts: [1, 2]
report: extract_report.json
```

직접 실행이다(필요한 입력을 작업 폴더에 둔다).

```bash
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper extract-parts ep.yaml
```

필요한 입력 — `examples/extract-parts/assembly.k` · `examples/extract-parts/part2_include.k`

**체인(REMAP 스텝)으로 쓸 수 있다.** 러너는 입력 덱 **하나만** Output 폴더에 복사하므로, 덱이 `*INCLUDE` 로 나뉘어 있으면 그 안의 파트를 못 찾는다(실측 — 「덱에 없는 PID」 rc 1). 인클루드가 없는 덱에 쓴다.

```yaml
params:
  op: extract-parts
  config:
    parts: [1, 2]
    report: extract_report.json
```

`model` 과 `output` 은 러너가 넣는다(`input.k` → `Remap_dti.k`).

### 주의사항

- ★어려운 부분은 '뽑기' 가 아니라 **남은 것이 멀쩡한가** 다. 뽑은 덱이 없는 절점·파트· 섹션·재질을 가리키면 LS-DYNA 는 **엉뚱한 자리**에서 죽고 원인이 추출이라는 걸 한참 뒤에 안다. 그래서 산출 덱을 **되읽어** 미정의 참조를 세고, 0 이 아니면 rc≠0 이다
- ★`*INCLUDE` 를 **펼쳐 넣는다** — 2.32GB 급 덱은 거의 늘 인클루드로 쪼개져 있고, 고른 파트의 요소가 그 안에 있으면 안 읽는 순간 **요소가 하나도 없는 덱**이 조용히 나온다. 산출은 **홀로 서는 한 파일**이고, 못 읽는 인클루드는 **거절**한다
- 격자 3족 말고 **보 족 5종**(BEAM·DISCRETE·MASS·SEATBELT·PLOTEL)도 읽는다 — 칸 자리를 매뉴얼로 확정해 두었다. 절점 칸 **개수**까지 아므로 보의 RT1·LOCAL 이나 안전벨트의 SBRID·SLEN 을 절점으로 세지 않는다(번호를 다시 매길 때 그 칸을 덮어쓰면 카드가 깨진다). PID 칸은 족마다 다르고(`*ELEMENT_MASS` 는 칸 3), `PLOTEL` 은 PID 가 없어 **두 절점이 다 남았을 때만** 싣는다
- ★그래도 모르는 변형(`*ELEMENT_MASS_NODE_SET`·`*ELEMENT_INERTIA` 등)이 **고른 파트의** 요소를 담고 있으면 **거절한다**. 조용히 빠뜨린 덱은 그럴듯하게 돌면서 틀린다. 안 고른 파트의 것이면 버리고 **수로 적는다**
- 버린 것은 전부 `dropped_keywords` 에 키워드별로 적는다 — 안 보이는 손실을 만들지 않는다
- `part_titles` 는 `*` `?` 와일드카드다(대소문자 무시) — 61파트 덱에서 PID 를 외우지 않아도 된다. 덱에 없는 PID 는 **거절**한다(오타면 조용히 빈 덱이 나온다)
- `renumber: false` 가 기본. `true` 면 절점·요소를 1 부터 매기고 **매핑 표를 함께** 낸다(`<output>_renumber_map.json`) — 없으면 되돌릴 수 없다. 칸만 **제자리에서** 갈아 끼우므로 좌표 글자는 바이트 그대로다(실수 왕복 오차 0)
- `include.sets: referenced` 는 세트를 **자른다**(빼지 않는다) — 세트를 가리키는 접촉· 경계 카드가 미정의 참조가 되면 덱이 안 돈다. `*SET_SEGMENT` 는 **네 절점이 다 남은** 면만 싣는다(일부만 남은 면은 면이 아니다)
- `*DATABASE_HISTORY_*` 는 버린다(절점·요소 ID 를 담는다). 그 밖 `*DATABASE_` 와 `*CONTROL_*` 은 그대로 싣는다 — 안 싣으면 뽑은 덱이 애초에 안 돈다

### 개발 현황

바이너리(v1.8.0 · 63 op 판, 2026-10-16 SIF)에 있다. 정본 `KooRemapper/docs/KooRemapper_Manual.md` §48 · 회귀 `tools/regress/test_extract_parts.py`.

---

## cad_solid_merge_to_deck

### 용도

StepForge 조각(.k + 대응표)을 기존 덱에 **넣는다** — 계약 대조 · 번호 이동 · coord_sha 검산.

StepForge 조각(.k + 대응표 JSON)을 기존 덱에 넣는다. 경계 계약대로 대조하고, 조각 번호가 덱 최대값(인클루드 닫힘까지) 위면 옮기지 않으며 아래에 걸치면 위로 옮긴다. 파트마다 coord_sha 를 다시 잰다.

### 호출 형태

config YAML 파일 경로를 위치 인자로 받는 yaml-config op 다.

```
KooRemapper cad_solid_merge_to_deck <config.yaml>
```

근거 — 바이너리 `help cad_solid_merge_to_deck` 의 사용법(2026-10-16 · SmartTwinPreprocessor.sif 판).

### config YAML 인자

| 키 | 필수 · 기본 | 설명 |
|---|---|---|
| `model` | 필수 | 조각이 들어갈 기존 덱. `*INCLUDE` 닫힘을 읽어 새 번호가 인클루드의 번호와도 겹치지 않게 한다 |
| `output` | 필수 | 출력 덱. 옆에 `<output>_fragment_map.json`(조각이 받은 덱 번호를 적은 대응표)을 쓴다 |
| `fragment` | 필수 | StepForge 조각 .k(`export_part_fragment`) |
| `fragment_map` | 필수 | StepForge 조각 대응표 JSON. 모르는 칸·빠진 칸은 거절한다 |
| `deck_unit` | 기본 `mm-t-s` | 대상 덱의 단위계. 조각의 unit 이 같아야 한다 — 환산하지 않는다 |

### 예제

KooRemapper 저장소 예제다 — 같은 형식의 자기 모델로 바꿔 쓴다.

`m.yaml`

```yaml
model: examples/cad_solid_merge_to_deck/deck.k
output: merged.k
fragment: examples/cad_solid_merge_to_deck/stepforge_fragment.k
fragment_map: examples/cad_solid_merge_to_deck/stepforge_fragment.json
```

직접 실행이다(필요한 입력을 작업 폴더에 둔다).

```bash
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper cad_solid_merge_to_deck m.yaml
```

필요한 입력 — `examples/cad_solid_merge_to_deck/deck.k` · `examples/cad_solid_merge_to_deck/stepforge_fragment.k` · `examples/cad_solid_merge_to_deck/stepforge_fragment.json`

**체인(REMAP 스텝)으로 쓸 수 있다.** `fragment`·`fragment_map` 을 **절대 경로**로 준다(러너는 입력 덱만 Output 폴더에 복사한다).

```yaml
params:
  op: cad_solid_merge_to_deck
  config:
    fragment: examples/cad_solid_merge_to_deck/stepforge_fragment.k
    fragment_map: examples/cad_solid_merge_to_deck/stepforge_fragment.json
```

`model` 과 `output` 은 러너가 넣는다(`input.k` → `Remap_dti.k`).

### 주의사항

- 경계 합의(StepForge `docs/BOUNDARY-DYNAFORGE.md` §3-3) — 조각을 **쓰는** 것은 StepForge, 기존 덱에 **넣는** 것은 이 op 이다(이미 있는 덱의 바이트를 바꾸는 일이라서)
- ★대응표는 **계약의 칸 그대로** 읽는다 — 맨 위 넷(unit·frame·ranges·parts) · ranges 넷 · parts 여덟. 모르는 칸·빠진 칸은 **거절**한다. `ranges` 의 `null`(그 번호를 안 썼다)은 받는다
- ★넣기 전에 조각을 대응표와 **대조**한다 — 번호가 ranges 안이고 lo·hi 가 실제 최소·최대인가 · 파트 집합 · 파트마다 요소 수·구간 · 그 요소가 쓰는 절점 = 절점 구간 · **coord_sha**(저쪽과 같은 식 — `%16.9e` 셋씩 이은 줄을 정렬해 sha256 앞 16자). 하나라도 어긋나면 넣지 않는다(rc=1)
- ★조각 번호가 이 덱(**인클루드 닫힘까지** 센 최대값) **위에 있으면 옮기지 않는다** — 대응표 번호 = 덱 번호 (요청 때 발행 — `id_floor` 가 낸 시작 번호로 받은 조각). 최대값 이하에 걸치면 그 위로 옮긴다(과도기 길 — 저쪽 기본값 1 로 받은 조각). PID·SECID·MID 는 **한 이동량**이다(저쪽이 셋을 같은 번호로 쓴다)
- 좌표 글자는 **바이트 그대로** 두고 번호 칸만 이 덱의 폭(8 · i10 이면 10)으로 쓴다. 넣을 블록을 **다시 읽어** coord_sha 를 한 번 더 잰다. long 덱은 받지 않는다
- unit 은 `deck_unit`(기본 mm-t-s)과 같아야 하고 frame 은 world 여야 한다 — 환산·변환은 하지 않는다
- 계약 밖 키워드(`*SET_*`·`*MAT_ADD_*`·`*MAT_THERMAL_*` …)가 든 조각·`ranges.sid` 가 null 이 아닌 조각은 거절
- 저쪽 자리표시 물성(RO = E = 1.0)은 그대로 넣되 MID 마다 **경고**한다 — 해석 전에 바꿀 것
- 산출 둘 — `<output>.k` · `<output>_fragment_map.json`(같은 칸 집합의 대응표를 **덱 번호**로 옮긴 것)

### 개발 현황

바이너리(v1.8.0 · 63 op 판, 2026-10-16 SIF)에 있다. 정본 `KooRemapper/docs/KooRemapper_Manual.md` §49 · 회귀 `tools/regress/test_cad_solid_merge.py`.

---

## rebind_entities_after_remesh

### 용도

재메시 뒤 덧붙인 블록의 절점·파트·요소 번호를 새 덱 번호에 **다시 묶는다** — 절점은 (파트 이름, 좌표) · 파트는 제목 · 요소는 (파트, 절점 좌표).

StepForge 가 재메시로 덱 전체를 다시 번호 매긴 뒤, 그 위에 덧붙인 블록(세트 · SPC · 하중 · 이력 · 접촉 · CNRB …)의 절점·파트·요소 번호를 새 덱 번호로 옮긴다. 절점은 (파트 제목, 좌표), 파트는 `*PART` 제목, 요소는 (파트 제목, 절점 좌표 집합)으로 **정확히** 짝짓는다.

### 호출 형태

config YAML 파일 경로를 위치 인자로 받는 yaml-config op 다.

```
KooRemapper rebind_entities_after_remesh <config.yaml>
```

근거 — 바이너리 `help rebind_entities_after_remesh` 의 사용법(2026-10-16 · SmartTwinPreprocessor.sif 판).

### config YAML 인자

| 키 | 필수 · 기본 | 설명 |
|---|---|---|
| `old_deck` | 필수 | 덧붙인 블록이 쓰인 기준 덱(그 번호가 블록이 가리키는 번호다). 한 파일 덱만 |
| `new_deck` | 필수 | 다시 구운 덱. 한 파일 덱만 · 정수 칸 폭이 old_deck 과 같아야 한다 |
| `entities` | 필수 | 우리가 덧붙인 블록만 든 .k(절점·세그먼트·파트·요소 세트 · SPC · 하중 · 이력 · CNRB · 강체 묶음 · 접촉 · 질량 · 좌표계 절점 · 곡선 · 박스). 고치지 않는다 |
| `output` | 필수 | 다시 묶은 블록 — new_deck 과 함께 `*INCLUDE` 해 쓴다. entities 와 달라야 한다 |
| `range_diff` | 선택 | StepForge 구간 표(range_diff JSON, 선택). 파트마다 coord_sha 를 두 덱에서 다시 재어 대조한다 |

### 예제

KooRemapper 저장소 예제다 — 같은 형식의 자기 모델로 바꿔 쓴다.

`rb.yaml`

```yaml
old_deck: examples/rebind_entities_after_remesh/v1.k
new_deck: examples/rebind_entities_after_remesh/v2.k
entities: examples/rebind_entities_after_remesh/ours.k
output: ours_rebound.k
range_diff: examples/rebind_entities_after_remesh/range_diff.json
```

직접 실행이다(필요한 입력을 작업 폴더에 둔다).

```bash
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper rebind_entities_after_remesh rb.yaml
```

필요한 입력 — `examples/rebind_entities_after_remesh/v1.k` · `examples/rebind_entities_after_remesh/v2.k` · `examples/rebind_entities_after_remesh/ours.k` · `examples/rebind_entities_after_remesh/range_diff.json`

**체인(REMAP 스텝)으로는 쓸 수 없다.** 러너가 넣는 `model` 키를 **모르는 키로 거절**한다(rc 1 — 엉뚱한 덱을 조용히 집지 않게 하려는 거절이다). 직접 실행한다.

### 주의사항

- 경계 합의(StepForge §3-6 · Q12) — StepForge 덱은 메시 잡마다 파트 순서대로 **전역 재번호**한다. 그 위에 덧붙인 세트·SPC·이력·CNRB 를 새 덱 번호로 옮기는 것이 이 op 이다(구간 표 + 좌표 기준)
- ★짝은 옛 절점의 (그 절점을 쓰는 파트 **이름**, 좌표 `%16.9e`×3)와 **정확히** 같은 새 절점이다 — 공차·가장 가까운 절점은 쓰지 않는다(물리가 조용히 바뀐다). 맞닿은 두 파트의 같은 자리 절점은 파트 이름으로 가른다
- 다시 구운 파트의 사라진 자리 · 짝이 여럿 · 정본이 칸 뜻을 단정 못 한 카드(초기응력 · 파트 감쇠 · `_GENERATE` 세트 …) · 자유형식 줄 · 블록이 정의한 번호가 새 덱과 겹침 — 하나라도 있으면 **쓰지 않는다**(rc 1)
- `range_diff` 를 주면 파트마다 `coords.before`/`after` 를 두 덱에서 **다시 재어** 대조한다 — 다르면 거절
- 번호 칸만 같은 폭으로 바꾸고 나머지 바이트는 그대로다. 산출을 새 덱과 함께 `*INCLUDE` 해 쓴다
- 한 파일 덱만 받는다(인클루드가 있으면 거절) · 절점 칸 자리는 `info --strict` 와 같은 정본(`parser/NodeRefs`)
- ★v2 — 파트는 `*PART` 제목으로, 요소는 (파트 제목, 요소 절점 좌표 집합)으로 옮긴다(`*SET_PART` · 접촉 SSTYP 3 · 강체 묶음 · 요소 세트 · 요소 이력 — 정본 `parser/IdRefs`). 초기응력·파트 감쇠 같은 갈래는 아직 거절한다

### 개발 현황

바이너리(v1.8.0 · 63 op 판, 2026-10-16 SIF)에 있다. 정본 `KooRemapper/docs/KooRemapper_Manual.md` §50 · 회귀 `tools/regress/test_rebind_after_remesh.py`.

---

## id_floor

### 용도

덱(인클루드 닫힘)의 번호 **바닥** — StepForge 조각을 요청할 때 줄 시작 번호 · 대응표 대조.

StepForge 조각을 요청할 때 줄 시작 번호를 낸다 — 덱 최대값 + 1(인클루드 닫힘까지). 대응표를 주면 그 범위가 바닥 위인지 대조한다.

### 호출 형태

config YAML 파일 경로를 위치 인자로 받는 yaml-config op 다.

```
KooRemapper id_floor <config.yaml>
```

근거 — 바이너리 `help id_floor` 의 사용법(2026-10-16 · SmartTwinPreprocessor.sif 판).

### config YAML 인자

| 키 | 필수 · 기본 | 설명 |
|---|---|---|
| `model` | 필수 | 조각이 들어갈 덱. `*INCLUDE` 닫힘을 읽는다 |
| `output` | 필수 | deck · basis · node_start · elem_start · pid_start · sid_start 를 담는 JSON. `fragment_map` 을 주면 범위마다 `check`(above · below · unused — 대응표의 범위가 null 이면 unused)를 더한다. 이름에 `.json` 이 없으면 붙인다 |
| `fragment_map` | 선택 | 바닥과 대조할 StepForge 조각 대응표 JSON(선택) |

### 예제

KooRemapper 저장소 예제다 — 같은 형식의 자기 모델로 바꿔 쓴다.

`f.yaml`

```yaml
model: examples/cad_solid_merge_to_deck/deck.k
output: floor.json
fragment_map: examples/cad_solid_merge_to_deck/stepforge_fragment.json
```

직접 실행이다(필요한 입력을 작업 폴더에 둔다).

```bash
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper id_floor f.yaml
```

필요한 입력 — `examples/cad_solid_merge_to_deck/deck.k` · `examples/cad_solid_merge_to_deck/stepforge_fragment.json`

**체인(REMAP 스텝)으로는 쓸 수 없다.** 산출이 JSON(`<output>.json`)이다 — 직접 실행한다.

### 주의사항

- ★**요청 때 발행**(2026-10-16) — 대역표를 두지 않는다. 조각을 요청할 때 이 op 이 낸 네 번호를 StepForge `export_part_fragment` 의 인자(`node_start`·`elem_start`·`pid_start`·`sid_start` — 이름 그대로)로 주면 조각이 그 번호로 쓰이고 `cad_solid_merge_to_deck` 가 **옮기지 않고** 넣는다(대응표 번호 = 덱 번호)
- 바닥 = assemble 과 같은 커서(**인클루드 닫힘까지**)의 최대값 + 1. pid_start 는 PID·SECID·MID 셋의 최대값 위다 (조각은 셋을 같은 번호로 쓴다 — 삽입도 한 이동량으로 옮긴다)
- `fragment_map` 을 주면 그 `ranges` 가 바닥 위인지 대조한다 — 아래에 걸치면 rc 1(그 조각은 넣을 때 옮겨진다)
- 경계 문서의 `id_floor`(Q7 — 대응표의 `ranges` 를 읽어 대조한다)가 이 op 이다

### 개발 현황

바이너리(v1.8.0 · 63 op 판, 2026-10-16 SIF)에 있다. 정본 `KooRemapper/docs/KooRemapper_Manual.md` §51 · 회귀 `tools/regress/test_id_floor.py`.
