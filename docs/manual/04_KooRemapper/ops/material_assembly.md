# KooRemapper ops — 재료·어셈블리(matdb · matswap · assemble)

LS-DYNA 데크의 재료 카드를 DB/번들로 일괄 교체하고 여러 파트 연산을 순차 결합해 초기응력까지 누적하는 KooRemapper 재료·어셈블리 계열 op 레퍼런스다.

---

## 0. 공통 사항

### 실행 방식

세 op 모두 SmartTwinPreprocessor.sif 안 `/opt/kooremapper/bin/KooRemapper`(C++ CLI, v1.8.0) 서브커맨드이며 두 경로로 실행된다.

- 컨테이너 직접 실행 — `apptainer exec <sif> /opt/kooremapper/bin/KooRemapper <op> <config.yaml>`
- KooChainRun 의 REMAP 스텝 — 파이프라인 러너가 위 CLI 를 대신 호출

세 op 는 모두 **yaml-config op** 다. 호출 형태는 help `Usage:` 와 정확히 일치하며 항상 `KooRemapper <op> config.yaml` 한 개의 config 파일만 받는다(matswap 만 하위호환용 레거시 positional 형태를 별도 지원).

### REMAP 스텝에서의 사용

yaml-config op 이므로 REMAP 스텝에서는 config 를 파일로 두는 대신 스텝 `params` 로 넘긴다.

- `params.op` — op 이름(`matdb` / `matswap` / `assemble`)
- `params.config` — YAML config 본문에 해당하는 dict

이때 `model`(또는 assemble 의 `base_model`)과 `output` 은 체인 러너가 이전 스텝 산출물/작업 디렉터리 기준으로 **자동 주입**하므로 REMAP 스텝 `params.config` 에는 원칙적으로 적지 않는다. 나머지 op 고유 키(matdb 의 `database`·`materials`, matswap 의 `swaps`, assemble 의 `operations` 등)만 채운다.

---

## matdb

### 용도

JSON 재료 데이터베이스(`material_db.json`)를 기준으로 모델의 `*MAT` 카드를 일괄 교체하는 op 다. 파트 이름 자동 매칭 또는 직접 MID 지정을 지원하며, 구조 재료뿐 아니라 열 재료 카드까지 삽입할 수 있다. REMAP 스텝에서 가장 많이 쓰는 재료 교체 수단으로, 번들로 동봉된 525종 재료 DB(`/opt/kooremapper/materials/material_db.json`)를 그대로 활용해 모델 전체 재료를 한 번에 갱신한다. (근거: 정본 §24, help; 재료 수 525종은 materials/MATERIAL_DB_REPORT.md)

### 호출 형태

```
KooRemapper matdb config.yaml
```

(근거: help `Usage: KooRemapper matdb <config.yaml>`)

### config 인자

| 키 | 타입 | 설명 | 근거 |
|---|---|---|---|
| `model` | str | 입력 K 파일(REMAP 스텝에서는 러너 자동 주입) | 정본 §24, help |
| `output` | str | 출력 K 파일(REMAP 스텝에서는 러너 자동 주입) | 정본 §24, help |
| `database` | str | 재료 DB(JSON) 경로. **생략 시 번들 DB(exe 상대경로 `materials/material_db.json`, SIF 내 `/opt/kooremapper/materials/material_db.json`, 525종) 자동 사용** | help 노트, 정본 §24(525종은 materials/MATERIAL_DB_REPORT.md) |
| `mat_type` | str | 기본 구조 카드 유형(예: `MAT_ELASTIC`, `MAT_024`) | 정본 §24, help |
| `thermal` | bool | 열 재료 카드 기본 삽입 여부(기본 `false`) | 정본 §24, help |
| `materials` | list | 개별 매칭 규칙 목록(선택). 아래 하위 키 참조 | 정본 §24, help |

`materials[]` 항목 하위 키.

| 키 | 설명 | 근거 |
|---|---|---|
| `match` | 파트 title 을 DB 의 name/tag 와 부분 문자열 매칭(대소문자 무시). `"*"` 는 미매칭 재료 전체에 자동 매칭 시도(catch-all) | 정본 §24, help |
| `mid` | 파트 이름 대신 재료 ID(MID) 직접 지정 | 정본 §24, help |
| `mat_type` | 해당 규칙에만 적용할 구조 카드 유형 override | 정본 §24, help |
| `thermal` | 해당 규칙에만 적용할 열 재료 삽입 override | 정본 §24, help |

### 예제

번들 DB + 이름 매칭 리스트 형식(정본/현행 config 형식 기준).

```yaml
# model / output 은 REMAP 스텝에서 러너가 자동 주입
database: material_db.json      # 생략 시 번들 525종 DB 자동 사용
mat_type: MAT_ELASTIC          # 기본 구조 카드
thermal: false
materials:
  - match: "AL7003H"
    mat_type: MAT_PIECEWISE_LINEAR_PLASTICITY
  - match: "SUS304_annealed"
    mat_type: MAT_PIECEWISE_LINEAR_PLASTICITY
  - match: "OCA Rigid Standard"
    mat_type: MAT_VISCOELASTIC
  - mid: 5                      # 이름 대신 MID 직접 지정
    thermal: true
  - match: "*"                  # 나머지 전부 자동 매칭
```

(근거: 정본 §24, `materials/matdb_smartphone.yaml`; 주석의 525종은 materials/MATERIAL_DB_REPORT.md)

### 동작 원리

- 매칭은 파트 title 과 DB 의 name/tag 를 부분 문자열로 대조하며 대소문자를 무시한다. (근거: 정본 §24, help)
- `match: "*"` 는 앞선 규칙에서 매칭되지 않은 재료에 대해 자동 매칭을 시도하는 catch-all 이다. (근거: 정본 §24)
- `thermal: true` 이면 `*MAT_THERMAL_ISOTROPIC` 과 `*MAT_ADD_THERMAL_EXPANSION` 을 자동 삽입하고 TMID 링크를 자동 연결한다. (근거: 정본 §24, help)
- assemble 내부에서도 `- type: matdb` 로 동일 알고리즘을 호출할 수 있다(정본 §39.15).

### 주의사항

- `database` 를 생략하면 exe 상대경로의 번들 DB 를 쓴다. 사용자 지정 DB 를 쓰려면 명시적으로 경로를 넣어야 한다. (근거: help 노트)
- REMAP 스텝에서는 `model`/`output` 을 러너가 주입하므로 `params.config` 에 직접 적지 않는다.

### 개발 현황

**구현됨** — 정본 §24 및 help 에 op·config 형식이 명시되어 있고, assemble 하위 연산(§39.15)으로도 노출된다. 번들 DB 는 `/opt/kooremapper/materials/material_db.json` 로 동봉된다.

---

## matswap

### 용도

`*MAT_*`, `*HOURGLASS`, `*DEFINE_CURVE`, `*SECTION_*` 를 하나의 번들 파일(`*.k`)로 묶어 특정 파트에 **완전한 한 세트로** 일괄 교체하는 op 다. ID 충돌 방지, 고아(orphan) 카드 자동 제거, 복수 파트 동시 교체를 지원한다. (근거: 정본 §23, help)

### 호출 형태

```
KooRemapper matswap config.yaml
KooRemapper matswap <model.k> <bundle.k> <pid> <output.k>   # legacy positional
```

(근거: help `Usage:` 2줄)

### config 인자

| 키 | 타입 | 설명 | 근거 |
|---|---|---|---|
| `model` | str | 입력 K 파일(REMAP 스텝에서는 러너 자동 주입) | 정본 §23, help |
| `output` | str | 출력 K 파일(REMAP 스텝에서는 러너 자동 주입) | 정본 §23, help |
| `swaps` | list | 교체 규칙 목록. 각 항목에 `bundle` + 타겟 지정 | 정본 §23, help |

`swaps[]` 항목 하위 키.

| 키 | 설명 | 근거 |
|---|---|---|
| `bundle` | 교체할 재료 번들 파일(`*PARAMETER` 블록 포함 `*.k`) | 정본 §23, help |
| `pid` | 타겟 파트 ID(단일) | 정본 §23, help |
| `pids` | 타겟 파트 ID 목록(복수) | 정본 §23, help |
| `swap_all` | `true` 시 모델 전체 파트를 자동 검색해 교체 | 정본 §23, help |
| `mid` / `mids` | MID 로 타겟(이 경우 SECTION 은 교체하지 않음) | 정본 §23 |

### 예제

단일 PID 교체.

```yaml
# model / output 은 REMAP 스텝에서 러너가 자동 주입
swaps:
  - bundle: rubber.k
    pid: 1
```

복수 PID 동시 교체(재료 카드 1세트만 삽입, 두 파트가 공유).

```yaml
swaps:
  - bundle: rubber.k
    pids: [1, 2]
```

모델 전체 교체.

```yaml
swaps:
  - bundle: rubber.k
    swap_all: true
```

(근거: `examples/matswap/01_single_pid.yaml`, `examples/matswap/02_multiple_pids.yaml`, `examples/matswap/03_swap_all.yaml`)

### 번들 파일과 파라미터 규칙

번들 `*.k` 는 `*PARAMETER` 블록으로 ID 를 파라미터화하며, 파라미터 이름 접두사로 ID 종류가 자동 인식된다.

| 접두사 | ID 종류 | 재매핑 동작 |
|---|---|---|
| `HGID*` | Hourglass ID | 항상 새 ID(모델 max + 1) |
| `LCID*` | Curve ID | 항상 새 ID(모델 max + 1) |
| `SECID*` | Section ID | 항상 새 ID(모델 max + 1) |
| `MID*` | Material ID | 고아면 재사용, 아니면 max + 1 |
| `PID*` | Part ID | 재매핑 없음(PART 카드 삽입 스킵) |

(근거: 정본 §23 표 23-1, help)

### 동작 원리

- 타겟 파트의 기존 MID/SECID/HGID 를 조회해 다른 파트가 쓰지 않는 고아 카드는 제거하고, 공유 카드는 유지한다. (근거: help 노트, `examples/matswap/README.md`)
- 번들 카드의 `&VARNAME` 은 숫자로 resolve 되며 출력 파일에는 `*PARAMETER` 없이 확정된 숫자값만 남는다. (근거: help 노트)
- assemble 내부에서도 `- type: matswap`(하위 키 `bundle`, `pid`/`pids`/`swap_all`)으로 동일 알고리즘을 호출한다. (근거: 정본 §39.14, help, `examples/matswap/04_assemble_integration.yaml`)

### 주의사항

- 번들 파일은 반드시 `*PARAMETER` 블록과 위 접두사 규칙을 따르는 ID 를 가져야 한다. (근거: 정본 §23, help)
- `mid`/`mids` 로 타겟하면 SECTION 은 교체되지 않는다. (근거: 정본 §23)

### 개발 현황

**구현됨** — 정본 §23·help·`examples/matswap/`(단일/복수/전체/assemble 통합 4종 예제와 `rubber.k` 번들)로 동작 형태가 모두 제공된다.

---

## assemble

### 용도

여러 파트 연산을 **순차적으로 적용**하는 KooRemapper 최대 복합 op 다. 기본 모델을 로드하고 각 오퍼레이션을 순서대로 실행하며, 누적된 초기응력을 단일 dynain 으로 출력한다. replace/squeeze/restack/DR 등 파트 변형·재료·초기응력 연산을 한 config 에 엮는다. (근거: 정본 §39, help)

### 호출 형태

```
KooRemapper assemble config.yaml
```

(근거: help `Usage: KooRemapper assemble <config.yaml>`)

### 출력

- `<output>.k` — 조립된 모델(모든 키워드 보존)
- `<output>.dynain` — 누적 초기응력(`*INITIAL_STRESS_SOLID`)

(근거: help Output, 정본 §39)

### config 최상위 키

| 키 | 타입 | 설명 | 근거 |
|---|---|---|---|
| `base_model` | str | 입력 K 파일. 첫 오퍼레이션이 `generate` 면 생략 가능(REMAP 스텝에서는 러너 자동 주입) | 정본 §39, help, `examples/assemble/al_cu_explicit.yaml` |
| `output` | str | 출력 접두사(확장자 없음, REMAP 스텝에서는 러너 자동 주입) | 정본 §39, help |
| `dynamic_relaxation` | bool | `true` 시 `*CONTROL_DYNAMIC_RELAXATION` 삽입 | 정본 §39, help, `examples/replace_test/assemble_dr_test.yaml` |
| `dynain_embed` | bool | `true` 시 dynain 을 인라인 임베드(별도 `.dynain` 파일 없음) | 정본 §39, help |
| `material` | map | 전역 재료. `E`(Young's modulus), `nu`(Poisson's ratio) | 정본 §39, help, `examples/replace_test/assemble_replace.yaml` |
| `operations` | list | 순차 실행할 오퍼레이션 목록. 각 항목은 `type` + 연산별 인자 | 정본 §39, help |

### 공통 특성

- **원본 키워드 보존** — `*CONTACT`, `*BOUNDARY`, `*LOAD` 등 미파싱 키워드를 그대로 유지한다.
- **응력 누적** — 동일 요소에 여러 오퍼레이션을 적용하면 응력을 합산한다.
- **ID 자동 관리** — 파트/섹션/노드/요소 ID 를 충돌 없이 자동 발급한다.

각 오퍼레이션은 동일 이름의 독립 명령과 같은 알고리즘을 쓰며, assemble 안에서는 `- type: <이름>` 으로 지정해 여러 개를 순차 결합한다. (근거: 정본 §39)

### 하위 오퍼레이션(type)

예제로 config 근거가 확보된 대표 연산.

| type | 핵심 인자(예제 근거) | 설명 | 근거 |
|---|---|---|---|
| `replace` | `target_pid`, `detail_flat`, `shell_bent`, `prestress` | 파트를 매핑된 상세 메시로 교체. `prestress: true` 시 굽힘 초기응력 계산 | 정본 §39.1, help, `examples/replace_test/assemble_replace.yaml` |
| `squeeze` | `target_pid`, `eps_x`, `eps_y`, `eps_z` | 간섭 끼워맞춤 — 파트 노드를 압축 | 정본 §39.2, help, `examples/replace_test/assemble_dr_test.yaml` |
| `restack` | `target_pid`, `direction`, `element_type`, `layers[].thickness`, `layers[].material_card` | 레이어 재적층(솔리드 재구성). 같은 `MIDxxx` 는 물성 ID 공유 | 정본 §39.3, `examples/replace_test/assemble_restack_test.yaml`, `examples/assemble/al_cu_explicit.yaml` |
| `bend` | `target_pid`, `plane`, `source: formula`, `expression` | 굽힘 변형 + 초기응력 | 정본 §39.4, `examples/assemble/assemble_example.yaml` |
| `generate` | `shape`, `lx/ly/lz`, `nx/ny/nz`, `rho`, `E`, `nu`, `mid`, `secid`, `pid`, `part_title` | `base_model` 없이 시작 시 첫 오퍼레이션으로 인라인 메시 생성 | 정본 §39.17, `examples/assemble/al_cu_explicit.yaml` |
| `control` | `endtime`, `tssfac`, `energy`, `ihq`, `qh`, `q1`, `q2`, `dt2ms` | `*CONTROL_*` 카드 삽입/수정 | 정본 §39.19, `examples/assemble/al_cu_explicit.yaml` |
| `database` | `preset`(crash/drop/nve/all), `dt`, `dt_plot` | `*DATABASE_*` 출력 카드 일괄 삽입 | 정본 §39.20, `examples/assemble/al_cu_explicit.yaml` |
| `matswap` | `bundle`, `pid`/`pids`/`swap_all` | 재료 번들 교체(위 matswap 참조) | 정본 §39.14, help, `examples/matswap/04_assemble_integration.yaml` |

> **restack 필드 주의** — 예제·정본은 `target_pid` + `layers[].material_card`(인라인 MAT 카드) 형식을 쓴다. help `Usage:` 에는 `source_pid` + `layers[].{pid,secid,mid,hgid}` 형태도 표기되어 있어 레이어 지정 문법이 두 갈래로 보인다. 실제 REMAP 사용은 예제 형식을 따르고, `pid/secid/mid/hgid` 개별 지정 방식은 **확인 필요**.

정본 §39 에 나열되지만 이 페이지에서 별도 예제 근거를 확인하지 못한 하위 연산(각 인자 상세는 정본 참조, 미확인 필드는 **확인 필요**).

- `indent`(§39.5), `formstrain`(§39.6), `tet10`/`hex20`/`quad8`/`tria6` 2차 요소 변환(§39.7), `refine`(§39.8), `elform`(§39.9), `disconnect`(§39.10), `iga`(§39.11), `warpage`(§39.12), `offset`(§39.13), `matdb`(§39.15), `wrap`(§39.16), `update`(§39.18)

### 예제

replace 후 squeeze 순차 결합 + 전역 재료.

```yaml
# base_model / output 은 REMAP 스텝에서 러너가 자동 주입
operations:
  - type: replace
    target_pid: 1
    detail_flat: detail_flat.k
    shell_bent: shell_bent.k
    prestress: true

  - type: squeeze
    target_pid: 1
    eps_x: 0.0
    eps_y: -0.01
    eps_z: 0.0

material:
  E: 210000.0
  nu: 0.3
```

(근거: `examples/replace_test/assemble_replace_squeeze.yaml`)

restack 재적층(두께 일치 + MID 공유) + Dynamic Relaxation.

```yaml
dynamic_relaxation: true

operations:
  - type: restack
    target_pid: 1
    direction: auto
    element_type: solid
    layers:
      - thickness: 0.3
        material_card: |
          *MAT_ELASTIC
          $#     mid        ro         e        pr
              MID001  7.85E-09  2.10E+05       0.3
      - thickness: 0.4
        material_card: |
          *MAT_ELASTIC
          $#     mid        ro         e        pr
              MID002  7.85E-09  1.50E+05      0.25
      - thickness: 0.3       # 라벨·내용이 1층과 같음 → MID 공유, MAT 카드 1회만 출력
        material_card: |
          *MAT_ELASTIC
          $#     mid        ro         e        pr
              MID001  7.85E-09  2.10E+05       0.3

material:
  E: 210000.0
  nu: 0.3
```

(근거: `examples/replace_test/assemble_restack_test.yaml`)

generate → restack → control → database 원샷.

```yaml
# base_model 없음 → 첫 오퍼레이션 generate 로 메시 생성
output: al_cu_result           # REMAP 스텝에서는 러너 자동 주입

operations:
  - type: generate
    shape: box
    lx: 100.0
    ly: 20.0
    lz: 10.0
    nx: 10
    ny: 4
    nz: 2
    rho: 7.85e-9
    E: 210000.0
    nu: 0.3
    pid: 1
    secid: 1
    mid: 1
    part_title: Base Box

  - type: restack
    target_pid: 1
    direction: z
    element_type: solid
    layers:
      - thickness: 5.0
        material_card: |
          *MAT_ELASTIC
          $#     mid        ro         e        pr        da        db  not used
                   2  2.70E-09   68900.0      0.33       0.0       0.0       0.0
      - thickness: 5.0
        material_card: |
          *MAT_ELASTIC
          $#     mid        ro         e        pr        da        db  not used
                   3  8.96E-09  117000.0      0.34       0.0       0.0       0.0

  - type: control
    endtime: 0.001
    tssfac: 0.9
    energy: true
    ihq: 4
    qh: 0.05
    q1: 1.5
    q2: 0.06

  - type: database
    preset: crash
    dt: 0.0001
    dt_plot: 0.001
```

(근거: `examples/assemble/al_cu_explicit.yaml`)

### 동작 원리

- `operations` 목록 순서대로 각 연산을 적용하고, 동일 요소에 응력이 겹치면 합산해 최종 dynain 하나로 출력한다. (근거: 정본 §39)
- `base_model` 없이 첫 오퍼레이션이 `generate` 면 메시를 인라인 생성해 어셈블리를 시작한다. (근거: 정본 §39.17, `examples/assemble/al_cu_explicit.yaml`)
- `dynamic_relaxation: true` 는 `*CONTROL_DYNAMIC_RELAXATION` 을, `dynain_embed: true` 는 dynain 인라인 임베드를 유발한다. (근거: 정본 §39, help)

### 주의사항

- `output` 은 확장자 없는 접두사다. `.k` 와 `.dynain` 이 각각 생성된다. (근거: help Output)
- 오퍼레이션 순서가 결과에 영향을 준다(응력 누적·ID 발급이 순차 진행). (근거: 정본 §39)
- restack 레이어 지정 문법 이원화는 위 표 하단 주석 참조(**확인 필요**).

### 개발 현황

**구현됨** — 정본 §39·help 에 최상위 키와 20여 개 하위 오퍼레이션이 명시되어 있고, `examples/assemble/`·`examples/replace_test/`·`examples/matswap/` 에 replace/squeeze/restack/generate/control/database/matswap/DR 동작 예제가 제공된다. 예제 근거가 없는 하위 연산의 개별 필드는 정본 §39 각 절을 참조하고, 미확인 필드는 **확인 필요**로 남긴다.
