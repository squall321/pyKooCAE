# KooRemapper ops — 하중·경계·접촉(load · boundary · rbe · contact · relax · stabilize · database · hfdamp)

LS-DYNA 데크에 하중·경계조건·RBE·접촉·완화(relaxation)·안정화·출력제어·고주파 댐핑 키워드를 삽입/관리하는 KooRemapper의 여덟 개 YAML-config op에 대한 레퍼런스다.

## 실행 형태 (공통)

KooRemapper는 `SmartTwinPreprocessor.sif` 안의 C++ CLI `/opt/kooremapper/bin/KooRemapper`(v1.8.0)다. 두 가지 방법으로 호출한다.

- 컨테이너 직접 실행: `apptainer exec <sif> /opt/kooremapper/bin/KooRemapper <op> <config.yaml>`
- KooChainRun의 `REMAP` 스텝: 아래 각 op의 "REMAP 스텝" 줄 참조.
- YAML 설정의 BOM·탭·상대 경로 공통 규칙과 새로 거절되는 열거값은 [README §YAML 설정 공통 규칙](../README.md#yaml-설정-공통-규칙) 참조.

이 페이지의 여덟 op는 모두 **YAML-config op**다. 인자로 설정 파일 경로 하나만 받으며, `model`(입력 k-file)과 `output`(출력 k-file)을 config 안에 지정한다. 따라서 REMAP 스텝에서는 `params.op=<op>` 와 함께 설정을 `params.config`(dict, 곧 YAML 내용)로 전달한다.

> 스키마 근거 우선순위: 호출형태는 바이너리 `--help`의 `Usage:` 줄, config 필드는 shipped 예제(`examples/<op>/`)를 1차 근거로 한다. 일부 op는 정본 매뉴얼 본문(정본 §N)이 예제와 다른 구버전 스키마를 보여주므로, 아래 각 op의 주의사항에 명시했다.

---

## load

### 용도

파트의 면을 선택해 압력/힘/중력 하중을 부여한다. `*LOAD_*`, `*DEFINE_CURVE`, `*SET_*` 키워드를 삽입한다. (help, 정본 §26)

### 호출형태

```
KooRemapper load <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper load load_tied.yaml
```

REMAP 스텝: `params.op=load`, `params.config`에 아래 YAML 내용을 dict로 전달.

### config

```yaml
model: mesh.k
output: mesh_loaded.k
loads:
  - part: 10
    mode: pressure          # pressure | force | gravity
    value: 1.0              # 하중 크기
    direction: [0, 0, 1]    # 하중 방향 벡터
    select: tied            # direction | set | tied  ('all' 은 없다)
    angle: 45.0             # 면 선택 각도 허용치(°)
    curve:                  # 선택. 시간-하중 곡선 → *DEFINE_CURVE
      - [0.0, 0.0]
      - [0.001, 1.0]
      - [0.01, 1.0]
```

| 키 | 설명 |
|---|---|
| `part` | 하중 대상 파트 ID |
| `mode` | `pressure` / `force` / `gravity` |
| `value` | 하중 크기 |
| `direction` | 하중 방향 벡터 `[x, y, z]` |
| `select` | 면 선택 방식. `direction`(방향벡터 각도 내 법선 면) / `set`(기존 `*SET_SEGMENT`, `set_id` 필요) / `tied`(tied 접촉 참여 면). **`all` 은 `load` 에 없다** — 주면 rc=1 `[load] loads[0]: unsupported select 'all' (allowed: direction, set, tied)` |
| `angle` | 면 선택 각도 허용치(°) |
| `curve` | 선택. `[[t, f], ...]` 시간-하중 곡선 |

근거: help, `examples/load/load_tied.yaml`.

### 예제

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper load load_tied.yaml
```

PID 10이 참여하는 tied 접촉 세그먼트를 자동 탐색해, 그중 z+ 방향 면에만 시간 곡선 압력을 부과한다. (`examples/load/load_tied.yaml`)

### 주의사항

- 정본 §26 본문 표는 `type/nid/pid/dof/lcid` 형태의 노드/파트 ID 기반 구버전 스키마를 보여주나, v1.8.0 바이너리 help와 shipped 예제는 위 `part/mode/select/direction` 면-선택 스키마를 사용한다. 실제 실행 기준은 help·예제다.

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인, `examples/load` 예제 제공).

---

## boundary

### 용도

파트의 면을 선택해 자유도 구속(SPC) 또는 강체벽 경계를 부여한다. `*BOUNDARY_SPC_NODE`, `*RIGIDWALL_PLANAR` 키워드를 삽입한다. (help, 정본 §27)

### 호출형태

```
KooRemapper boundary <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper boundary boundary_fixed.yaml
```

REMAP 스텝: `params.op=boundary`, `params.config`에 아래 YAML 내용을 dict로 전달.

### config

```yaml
model: mesh.k
output: mesh_bc.k
boundaries:
  - part: 9
    dof: all                 # all | x | y | z | xy | xz | yz
    direction: [0, 0, -1]    # 면 선택 방향
    select: direction        # direction | all | set  (set 은 set_id 필수)
    angle: 45.0              # 면 선택 각도 허용치(°)
```

| 키 | 설명 |
|---|---|
| `part` | 경계 대상 파트 ID |
| `dof` | 구속 자유도. `all`(6 DOF 전체) / `x`·`y`·`z`(단일 병진) / `xy`·`xz`·`yz`(두 병진) |
| `direction` | 면 선택 방향 벡터 |
| `select` | `direction`(방향 면) / `all`(파트 노출면 전체 — 이때 `direction` 은 무시된다) / `set`(기존 `*SET_NODE`, `set_id` 필요). 그 밖의 값은 rc=1 `boundary: boundaries[i]: unsupported select '<값>' (allowed: direction, all, set)` |
| `angle` | 면 선택 각도 허용치(°) |

근거: help, `examples/boundary/boundary_fixed.yaml`, `examples/boundary/boundary_partial.yaml`.

### 예제

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper boundary boundary_partial.yaml
```

PID 9 하단면(z-)은 z 방향만 구속하고, PID 11 상단면(z+)은 `xyz` 병진 구속(회전 자유)한다. (`examples/boundary/boundary_partial.yaml`)

### 주의사항

- help의 `dof` 목록은 `all|x|y|z|xy|xz|yz`이나, 예제는 세 방향 병진 구속에 `xyz`도 사용한다(`boundary_partial.yaml`).
- 정본 §27 본문 표는 `type: spc/prescribed_motion` + `nid` + `dofx~dofrz` 형태의 노드 ID 기반 구버전 스키마를 보여주나, v1.8.0 help·예제는 위 `part/dof/select` 면-선택 스키마를 사용한다.
- 바이너리의 `boundary` help 는 아직 `select: direction  # direction | all` 만 찍는데, 실제 허용값은 `direction`/`all`/`set` 이다. 위 표를 따르라.
- `rbe` 와 허용값이 다르다: `boundary` 는 `set` 을 받고 `rbe` 는 받지 않는다.

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인, `examples/boundary` 예제 제공).

---

## rbe

### 용도

파트의 면을 선택해 RBE2/RBE3 강체 요소 구속을 만든다. RBE2는 `*CONSTRAINED_NODAL_RIGID_BODY`, RBE3는 `*CONSTRAINED_INTERPOLATION`을 삽입한다. (help, 정본 §28)

### 호출형태

```
KooRemapper rbe <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper rbe rbe_spider.yaml
```

REMAP 스텝: `params.op=rbe`, `params.config`에 아래 YAML 내용을 dict로 전달.

### config

```yaml
model: mesh.k
output: mesh_rbe.k
rbe:
  - part: 9
    select: direction        # direction | all  (set 은 없다)
    direction: [0, 0, -1]
    angle: 45.0
    type: rbe3               # rbe2 | rbe3
    mode: spider             # spider | face
```

| 키 | 설명 |
|---|---|
| `part` | 대상 파트 ID |
| `select` | `direction`(방향 면) / `all`(면 전체). 이 둘뿐이다 — `set` 이나 오타는 rc=1 `rbe: constraints[i]: unsupported select '<값>' (allowed: direction, all)` 이고, 예전처럼 조용히 `all` 로 떨어지지 않는다 |
| `direction` | 면 선택 방향 벡터 |
| `angle` | 면 선택 각도 허용치(°) |
| `type` | `rbe2`(강체: 슬레이브가 마스터와 정확히 동일 이동) / `rbe3`(보간: 마스터 이동이 슬레이브 가중 평균) |
| `mode` | `spider`(centroid 마스터 노드 1개) / `face`(면마다 centroid 노드) |

근거: help, `examples/boundary/rbe_spider.yaml`, `examples/boundary/rbe_face.yaml`, `examples/boundary/rbe_spider_rbe2.yaml`.

### 예제

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper rbe rbe_spider.yaml
```

PID 9 하단면(z-)에 centroid 노드 1개 + `*CONSTRAINED_INTERPOLATION`(RBE3 spider)을 생성한다. `mode: face`로 바꾸면 면마다 centroid를 만든다. (`examples/boundary/rbe_spider.yaml`, `rbe_face.yaml`)

### 주의사항

- 정본 §28 본문 표는 `type: rbe2/rbe3` + `master_nid`/`slave_nids`/`dof`/`weights` 형태의 노드 ID 직접 지정 구버전 스키마를 보여주나, v1.8.0 help·예제는 위 `part/select/mode` 면-선택 스키마를 사용한다.

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인, `examples/boundary` 예제 제공).

---

## contact

### 용도

`*CONTACT_*`, `*SET_SEGMENT`, `*SET_PART`, `*SET_NODE` 키워드를 일괄 관리한다. 하나의 YAML로 분석·생성·변환·수정·삭제·자동 감지를 순차 실행한다. (help, 정본 §25)

### 호출형태

```
KooRemapper contact <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper contact 09_detect_all.yaml
```

REMAP 스텝: `params.op=contact`, `params.config`에 아래 YAML 내용을 dict로 전달.

### config 기본 구조

```yaml
model:  model.k
output: model_contact.k    # analyze 전용이면 생략 가능
contacts:
  - action: <analyze | create | convert | modify | remove | detect>
    ...                     # 여러 액션을 순서대로 나열 가능
```

`contacts`는 액션 리스트다. 여러 액션을 나열하면 순서대로 처리된다(예: 삭제 → 감지 → 수정). `contact_index`는 `analyze` 리포트가 매기는 번호([0], [1], ...)로, convert/modify/remove에서 참조한다. (정본 §25, `examples/contact/12_multi_action.yaml`)

### action 목록

| action | 용도 | 주요 키 | 근거 |
|---|---|---|---|
| `analyze` | 기존 접촉 리포트(읽기 전용), `contact_index` 확인 | (없음) | 정본 §25.1, `examples/contact/01` |
| `create` | 새 접촉 생성 | `type`, `slave`, `master`, `friction`, `soft`, `title` | 정본 §25.2, `examples/contact/02~04, 15, 16` |
| `convert` | 기존 접촉의 SSTYP/MSTYP 방식 변환 | `contact_index`, `slave_to`, `master_to`, `facing` | 정본 §25.3, `examples/contact/05` |
| `modify` | 기존 접촉 파라미터 in-place 수정 | `contact_index`, `friction`, `soft`, `depth`, ... | 정본 §25.4, `examples/contact/06` |
| `remove` | 접촉 블록 삭제 | `contact_index` | 정본 §25.5, `examples/contact/07` |
| `detect` | Spatial Hash Grid로 접촉 쌍 자동 검출(+`auto_create`) | `slave`/`master` 또는 `scope`/`include`/`exclude`, `tolerance`, `auto_create`, `contact_type` | 정본 §25.6, `examples/contact/08~14` |

### slave/master 지정 방식 (create/detect)

| 형태 | 결과 (SSTYP/MSTYP) |
|---|---|
| `{ pid: N }` | 파트 ID 직접 (SSTYP=3) |
| `{ pids: [a, b, ...] }` | `*SET_PART` 자동 생성 (SSTYP=2). 인라인 목록과 블록 목록(`pids:` 다음 줄부터 `- a` / `- b`)은 같은 덱을 만든다 — 예전에는 블록 목록이 조용히 무시돼 `*SET_PART` 가 안 생겼다 |
| `{ pid: N, as_segment: true }` | 외곽면 추출 → `*SET_SEGMENT` (SSTYP=0) |
| `{ pid: N, as_segment: true, facing: true }` | 세그먼트 중 마주보는 면만 추출(얇은 파트에서 반대면 포함 방지) |

근거: help, `examples/contact/02, 03, 04`.

### type 값 (create)

단독 `contact` 명령의 약칭 표(assemble 과 다르다 — 아래 주의 참조).

| 약칭 | 만들어지는 키워드 |
|---|---|
| `auto` / `automatic` / **키 생략** | `*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE` |
| `tied` | `*CONTACT_TIED_SURFACE_TO_SURFACE` |
| `tied_thermal` / `thermal` | `*CONTACT_TIED_SURFACE_TO_SURFACE_THERMAL` |
| `tiebreak` | `*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_TIEBREAK` |
| `mortar` | `*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_MORTAR` |
| `tied_mortar` | `*CONTACT_TIED_SURFACE_TO_SURFACE_MORTAR` |
| `single` | `*CONTACT_AUTOMATIC_SINGLE_SURFACE` |
| `eroding` | `*CONTACT_ERODING_SURFACE_TO_SURFACE` |
| `forming` | `*CONTACT_FORMING_SURFACE_TO_SURFACE` |

약칭에 없는 값은 대문자로 바꿔 `*CONTACT_<값>` 으로 그대로 삽입한다(rc=0). 그래서 전체 키워드를
직접 써도 된다 — `automatic_nodes_to_surface`, `automatic_general`,
`forming_one_way_surface_to_surface`, `tied_shell_edge_to_surface` 등. 다만 KooRemapper 가 아는
키워드 목록에 없으면 경고를 함께 찍는다:
`[WARN] [contact] create: type '<값>' is not a known contact keyword — writing *CONTACT_<값> as-is`.
쓰는 카드는 언제나 Card 1·2 (+선택 THERMAL/TIEBREAK)이므로 다른 카드 구성을 요구하는 키워드는
LS-DYNA 쪽에서 거절된다. 예전에는 키를 생략하면 이름 없는 `*CONTACT_` 가, `type: auto` 는 실재하지
않는 `*CONTACT_AUTO` 가 나왔다. (정본 §25.2, `examples/contact/15_create_thermal.yaml`, `16_create_tiebreak.yaml`)

### contact_type 프리셋 (detect)

`auto` / `automatic` / `tied` / `tied_thermal` / `thermal` / `tiebreak` / `mortar` / `tied_mortar` / `single` / `eroding` / `forming` (대소문자 무시, 빈 값도 허용).

> **`create` 의 `type` 과 같은 값 공간이 아니다.** `detect` 의 `contact_type` 은 위 약칭 11개만 받는 닫힌 목록이라,
> `create` 라면 그대로 써 주는 전체 LS-DYNA 키워드(`automatic_surface_to_surface`, `automatic_nodes_to_surface` 등)를 여기 주면
> **rc=1** 로 죽는다: `[ERROR] [contact] unsupported contact_type '<값>' (allowed: auto, tied, tied_thermal, tiebreak, mortar, tied_mortar, single, eroding, forming)`.
> 찍히는 `allowed` 목록에는 `automatic`·`thermal` 이 빠져 있지만 둘 다 실제로는 통과한다(src/commands/contact.cpp 의 화이트리스트 11개).
> 정리하면 — `detect` 에는 약칭만, 전체 키워드는 `create` 의 `type` 에만 쓴다.

(help, `examples/contact/README.md`, 실행 확인)

### detect 옵션

| 키 | 기본값 | 설명 |
|---|---|---|
| `scope` | — | `all`: 모든 파트 쌍 탐색 |
| `include` / `exclude` | — | 파트 이름 키워드로 대상/제외 선택(대소문자 무시) |
| `tolerance` | 0.1 | 접촉 간격 허용치 |
| `normal_angle` | 45.0 | 법선 방향 허용 각도(°) |
| `auto_create` | false | 검출 쌍마다 접촉 자동 생성 |
| `skip_existing` | — | `tied`: tied 있는 쌍 skip / `all`: 접촉 있는 쌍 skip |
| `subtract_existing` | false | 기존 tied 세그먼트를 차집합으로 제외 |

근거: 정본 §25.6, `examples/contact/08~14`.

### Optional Cards (create / modify / detect+auto_create 공통)

`friction`, `fd`(Card 2) · `soft`, `sofscl`, `depth`, `sbopt`(Card A) · `penmax`, `thkopt`, `shlthk`(Card B) · `igap`, `ignore`(Card C) 등을 지정한다. (정본 §25.7, `examples/contact/11_detect_optcards.yaml`)

### 예제

분석(읽기 전용).

```yaml
contacts:
  - action: analyze
```

Part ID 직접 접촉 생성(SSTYP=3).

```yaml
contacts:
  - action: create
    type: automatic_surface_to_surface
    slave:  { pid: 1 }
    master: { pid: 3 }
    friction: 0.3
    soft: 2
    title: Left_to_Right
```

전체 파트 자동 감지 + 생성.

```yaml
contacts:
  - action: detect
    scope: all
    tolerance: 0.1
    auto_create: true
    contact_type: auto
    friction: 0.15
```

복합 워크플로우(삭제 → 감지 → 수정).

```yaml
contacts:
  - action: remove
    contact_index: 1
  - action: detect
    scope: all
    auto_create: true
    contact_type: mortar
  - action: modify
    contact_index: 0
    friction: 0.4
```

근거: `examples/contact/01, 02, 09, 12`.

### 주의사항

- convert/modify/remove의 `contact_index`는 먼저 `analyze`로 확인한 번호를 써야 한다. (정본 §25, help Workflow)
- tied 변환에는 마주보는 면만 남기는 `facing: true`가 사실상 필수다(얇은 파트에서 반대면이 tied에 포함되는 문제 방지). (`examples/contact/04, 05`)
- **`assemble` 안의 contact create 도 이제 같은 약칭 표를 쓴다**(2026-09-18 실행 확인). 코드에서 표가 한 곳(`ct_getPreset`)으로 합쳐져 단독 `contact` 와 `assemble` 의 `- type: contact` 가 같은 11종 약칭을 받고 같은 키워드를 낸다 — `assemble` 에서 `type: tied_thermal` 은 `*CONTACT_TIED_SURFACE_TO_SURFACE_THERMAL_TITLE`, `type: tiebreak` 는 `*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_TIEBREAK_TITLE` 로 나간다. 대소문자를 가리지 않고 `-` 를 `_` 로 읽는 것도 같다. 예전에는 `assemble` 에만 `tied_thermal`·`thermal`·`tiebreak` 가 없어 LS-DYNA 에 없는 `*CONTACT_TIED_THERMAL`·`*CONTACT_THERMAL`·`*CONTACT_TIEBREAK` 가 나갔다 — 그 우회로 전체 키워드를 적어 둔 기존 설정은 여전히 그대로 동작한다.
- 모르는 `type` 은 단독·assemble 모두 rc=0 이고 경고만 찍는다(단독은 `[WARN] `, assemble 은 `[WARNING] ` 접두). 출력 덱은 만들어지므로 오타를 눈치채려면 로그를 봐야 한다.

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인, `examples/contact` 01~16 예제 제공).

---

## relax

### 용도

초기 응력 평형을 위한 Dynamic Relaxation을 설정한다. 5단계 프리셋으로 `*CONTROL_DYNAMIC_RELAXATION`을 삽입한다. (help, 정본 §31)

### 호출형태

```
KooRemapper relax <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper relax relax_test.yaml
```

REMAP 스텝: `params.op=relax`, `params.config`에 아래 YAML 내용을 dict로 전달.

### config

```yaml
model: cylinder_wrapped.k
output: cylinder_relaxed.k
level: 2               # 1(빠름)~5(최대 보수), 기본 2
mode: explicit         # explicit(IDRFLG=1) | implicit(IDRFLG=5), 기본 explicit
drterm: 100.0          # DR 종료 시간 (0=수렴까지)
endtime: 1.0           # DR 후 해석 종료 시간(선택)
d3drlf: true           # DATABASE_BINARY_D3DRLF 출력(기본 true)
strip: false           # true면 DR 키워드 제거만
# 세부 오버라이드(레벨 기본값을 덮어씀):
# nrcyck / drtol / drfctr / tssfdr / irelal / edttl / fix_shell_elform
```

| 키 | 설명 |
|---|---|
| `level` | 1~5 프리셋(아래 표), 기본 2 |
| `mode` | `explicit`(IDRFLG=1, 속도 감쇠로 운동에너지 소산) / `implicit`(IDRFLG=5, 암시적 솔버로 평형) |
| `drterm` | DR 종료 시간(0=수렴까지) |
| `endtime` | DR 후 실제 해석 종료 시간(선택) |
| `d3drlf` | `*DATABASE_BINARY_D3DRLF` 출력 여부 |
| `strip` | `true`면 DR 키워드 제거만(삽입 안 함) |

레벨 프리셋(help).

| Lv | 이름 | NRCYCK | DRTOL | DRFCTR | TSSFDR | IRELAL | EDTTL |
|---|---|---|---|---|---|---|---|
| 1 | 빠름 | 500 | 0.010 | 0.990 | 0.95 | 0 | 0.04 |
| 2 | 표준 | 250 | 0.001 | 0.995 | 0.90 | 0 | 0.04 |
| 3 | 안정 | 100 | 0.001 | 0.998 | 0.80 | 0 | 0.04 |
| 4 | 보수 | 50 | 1e-4 | 0.999 | 0.67 | 1 | 0.01 |
| 5 | 최대 | 25 | 1e-5 | 0.999 | 0.50 | 1 | 0.001 |

근거: help, 정본 §31, `examples/wrap/relax_test.yaml`, `examples/wrap/relax_implicit_test.yaml`.

### 예제

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper relax relax_implicit_test.yaml
```

`level: 3`, `mode: implicit`로 암시적 초기화 DR을 설정한다. (`examples/wrap/relax_implicit_test.yaml`)

### 주의사항

- `strip: true`는 `*CONTROL_DYNAMIC_RELAXATION`, `*DATABASE_BINARY_D3DRLF`를 제거한다. (정본 §31)
- 세부 오버라이드(nrcyck 등)를 생략하면 레벨 기본값이 쓰인다. (help)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인, `examples/wrap` relax 예제 제공).

---

## stabilize

### 용도

Explicit 솔버 안정화 조치를 단계적으로 적용한다. **12단계 누적 시스템**으로, 각 레벨은 하위 레벨 조치를 모두 포함한다. (help, 정본 §36)

### 호출형태

```
KooRemapper stabilize <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper stabilize stabilize.yaml
```

REMAP 스텝: `params.op=stabilize`, `params.config`에 아래 YAML 내용을 dict로 전달.

### config (레벨 프리셋)

```yaml
model:     model.k
output:    stabilized.k
stabilize: explicit
level:     6           # 1~12 누적
```

### config (수동 지정)

```yaml
model:     model.k
output:    stabilized.k
stabilize: explicit
tssfac:    0.80        # *CONTROL_TIMESTEP TSSFAC
ihq:       4           # *CONTROL_HOURGLASS 타입
soft:      1           # *CONTACT_* Card A SOFT
```

수동 모드에서 지정 가능한 옵션: `tssfac esort_solid esort_shell osu inn ihq qh bwc miter irnxx wrpang orien shlthk xpene islchk enmass nsbcs soft sbopt depth maxpar ignore bulk_q1 bulk_q2 erode confirm_erosion hgen rwen slnten rylen`. (help)

레벨 프리셋 요약.

| Lv | 주요 변경 |
|---|---|
| 1 | 에너지 진단(HGEN=RWEN=SLNTEN=RYLEN=2) |
| 2 | 정확도(OSU=1, INN=4, ESORT=1) |
| 3 | TSSFAC=0.80 |
| 4 | 아워글래스 강성 IHQ=4, QH=0.10 |
| 5 | 셸 안정화(BWC=1, MITER=2, IRNXX=-2, WRPANG=10) — 모델에 셸 없으면 자동 skip |
| 6 | 접촉 stage 1(ORIEN=2, SHLTHK=1, XPENE=2, ISLCHK=2; SOFT=1, SBOPT=2, DEPTH=3) |
| 7 | TSSFAC=0.67 + BULK Q1=1.5, Q2=0.06(강제) |
| 8 | 접촉 stage 2 pinball(SOFT=2, SBOPT=3, DEPTH=5, IGNORE=1 등) |
| 9 | 최적 아워글래스 IHQ=6(Belytschko-Bindeman), QH=1.0 |
| 10 | TSSFAC=0.60, NSBCS=2 |
| 11 | Erosion(ERODE=11, ENMASS=2, TSSFAC=0.55) — `confirm_erosion: true` 또는 대화형 y/N 필요 |
| 12 | 최대 보수(TSSFAC=0.50, Q1=2.0, Q2=0.10) |

근거: help, 정본 §36.

### 예제

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper stabilize stabilize.yaml
```

`level: 6`은 에너지 진단부터 접촉 soft stage 1까지 누적 적용한다.

### 주의사항

- 레벨은 누적된다. `level: N`은 1~N 조치를 모두 포함한다. (정본 §36)
- Lv 5(셸 안정화)는 모델에 `*ELEMENT_SHELL`이 없으면 자동 skip된다. (help)
- Lv 11(Erosion)은 `confirm_erosion: true`가 없으면 대화형 y/N 확인을 요구한다. 자동 파이프라인에서는 반드시 `confirm_erosion: true`를 넣어야 한다. (help)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인, help가 `examples/explicit/` 예제를 안내).

---

## database

### 용도

`*DATABASE_*` 출력 제어 키워드를 삽입한다. 프리셋 또는 개별 키워드 토글을 지원하며, 기존 키워드는 자동으로 감지해 건너뛴다. (help, 정본 §37)

### 호출형태

```
KooRemapper database <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper database database_drop.yaml
```

REMAP 스텝: `params.op=database`, `params.config`에 아래 YAML 내용을 dict로 전달.

### config (프리셋)

```yaml
model:   model.k
output:  model_db.k
preset:  drop          # all/drop/crash/static/thermal/forming/modal/minimal
dt:      0.001         # 전역 ASCII 출력 간격(기본 0.001)
dt_plot: 0.01          # D3PLOT 간격(기본 0.01)
```

### config (개별 지정)

```yaml
model:  model.k
output: model_db.k
ascii:
  glstat: true
  matsum: true
  nodout: true
  rcforc: true
binary:
  d3plot: true
  d3thdt: true
extent:
  neiph:  6            # 추가 적분점 히스토리 변수
  strflg: 1            # 변형률 텐서 출력
  sigflg: 1            # 응력 텐서 출력
  epsflg: 1            # 유효 소성 변형률 출력
```

프리셋(8종).

| 프리셋 | 내용 |
|---|---|
| `all` | ASCII 20종 전체 + D3PLOT/D3THDT/D3DUMP/RUNRSF |
| `drop` | glstat matsum rcforc nodout elout sleout jntforc + d3plot |
| `crash` | glstat matsum rcforc sleout spcforc rwforc abstat + d3plot d3thdt |
| `static` | glstat matsum nodout elout spcforc bndout + d3plot |
| `thermal` | glstat matsum nodout elout tprint + d3plot d3thdt |
| `forming` | glstat matsum rcforc sleout rwforc swforc + d3plot |
| `modal` | glstat matsum nodout elout + d3plot |
| `minimal` | glstat matsum + d3plot |

ASCII 키워드(20종): glstat matsum nodout elout rcforc sleout spcforc nodfor rwforc secforc jntforc bndout abstat swforc ssstat deforc disbout ncforc tprint massout. Binary 키워드(6종): d3plot d3thdt d3dump runrsf intfor d3drlf. (help)

근거: help, 정본 §37, `examples/database/database_drop.yaml`, `examples/database/database_all.yaml`.

### 예제

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper database database_drop.yaml
```

낙하 해석용 `drop` 프리셋을 ASCII 간격 0.0001, D3PLOT 간격 0.005로 삽입한다. (`examples/database/database_drop.yaml`)

### 주의사항

- 기존 `*DATABASE_*` 키워드는 스캔되어 중복 삽입을 건너뛴다(`[SKIP]` 표시). (정본 §37)
- 출력 블록은 `*END` 직전에 삽입된다. (정본 §37)
- 프리셋과 개별 지정이 모두 없으면 `all` 프리셋이 자동 적용된다. (정본 §37)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인, `examples/database` 예제 제공).

---

## hfdamp

### 용도

소형 요소가 만드는 고주파(스퓨리어스) 진동을 억제한다. `*DAMPING_FREQUENCY_RANGE_DEFORM`을 삽입한다(selective 모드에서는 대상 파트를 모은 `*SET_PART_LIST`도 생성). (`examples/hfdamp/hfdamp_full.yaml`, `README`)

### 호출형태

```
KooRemapper hfdamp <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper hfdamp basic.yaml
```

REMAP 스텝: `params.op=hfdamp`, `params.config`에 아래 YAML 내용을 dict로 전달.

### config

```yaml
model:  input.k
output: output.k
dt_target:   3.0e-8    # 필수. FLOW = 1/(2×dt_target) 이상 주파수를 댐핑
cdamp:       0.99      # 임계 감쇠비(기본 0.99, 0 < cdamp ≤ 1)
fhigh_ratio: 100.0     # FHIGH = FLOW × ratio (기본 100, 권장 10~300)
mode:        global    # global | selective
tssfac:      0.9       # selective 전용. 요소 dt 추정 안전계수(기본 0.9)
```

| 키 | 기본값 | 설명 |
|---|---|---|
| `dt_target` | (필수) | 댐핑 타겟 dt(모델 시간 단위). `FLOW = 1/(2×dt_target)` |
| `cdamp` | 0.99 | 임계 감쇠비. 대역 [FLOW, FHIGH]에 적용 |
| `fhigh_ratio` | 100.0 | `FHIGH = FLOW × ratio`, 권장 10~300 |
| `mode` | global | `global`: PSID=0(전 파트) / `selective`: 요소 dt ≤ dt_target 파트만 `*SET_PART_LIST` 생성(재료 E·PR·RHO 필요) |
| `tssfac` | 0.9 | selective 전용. `dt_element = tssfac × L / c` 추정, 모델 TSSFAC와 맞춘다 |

근거: `examples/hfdamp/hfdamp_full.yaml`, `examples/hfdamp/basic.yaml`, `examples/hfdamp/selective.yaml`, `examples/hfdamp/README.md`.

### 예제

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper hfdamp selective.yaml
```

요소 dt를 계산해 `dt_target` 이하인 파트만 골라 `*SET_PART_LIST`를 만들고 그 파트에만 댐핑을 건다(조밀 메시 파트만 겨냥, 성긴 파트 과감쇠 방지). (`examples/hfdamp/selective.yaml`)

### 주의사항

- DEFORM 옵션은 요소 응력/힘을 감쇠하며 강체 운동은 감쇠하지 않는다. 비선형 explicit 해석에 적합하다. (`examples/hfdamp/hfdamp_full.yaml`)
- DEFORM 옵션은 동적 강성을 약 CDAMP% 증가시킨다. 필요하면 E를 소폭 낮춰 보정한다. (`examples/hfdamp/hfdamp_full.yaml`)
- `selective` 모드는 K-파일에 재료 물성(E, PR, RHO)이 있어야 한다. (`examples/hfdamp/hfdamp_full.yaml`)

### 개발 현황

v1.8.0 바이너리에 구현됨(정본 섹션 없음. `--help`는 인자를 config 경로로 해석해 에러를 내므로, 호출형태·옵션은 `examples/hfdamp`와 `README` 기준).
