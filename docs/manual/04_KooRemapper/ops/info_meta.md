# KooRemapper ops — 정보·메타(info · modelmeta · version · neutralaxis · linkage-fit · section · surfview · stackdiagram)

모델을 변형하지 않고 메시/모델의 상태만 읽어내는 조회·추출 op 묶음이다. `info` 는 메시 요약을 콘솔에 출력하고, `modelmeta` 는 파트별 기하·재료·연결성을 JSON으로 추출하며, `version` 은 바이너리 버전을 출력한다. 2026-10 판에서 다섯이 더해졌다 — `neutralaxis`(적층 중립축·굽힘강성) · `linkage-fit`(접힌 덱에서 힌지 찾기) · 격자를 그림으로 보는 `section`(단면) · `surfview`(자유면) · `stackdiagram`(층 모식도).

## 실행 방법

KooRemapper 는 `SmartTwinPreprocessor.sif` 안 `/opt/kooremapper/bin/KooRemapper` C++ CLI(v1.8.0)다. 두 가지 경로로 실행한다.

- 직접 실행: `apptainer exec <sif> /opt/kooremapper/bin/KooRemapper <op> ...`
- 체인 실행: KooChainRun 의 `REMAP` 스텝. `params.op` 에 op 이름을 지정하고, positional op 는 `params.argv`(리스트), yaml-config op 는 `params.config`(dict)로 인자를 넘긴다.
- YAML 설정의 BOM·탭·상대 경로 공통 규칙과 새로 거절되는 열거값은 [README §YAML 설정 공통 규칙](../README.md#yaml-설정-공통-규칙) 참조.

이 페이지의 op 는 모두 모델을 바꾸지 않는다. 덱(`Remap_dti.k`)을 내지 않으므로 **체인(REMAP 스텝)으로는 쓸 수 없다** — 러너는 Output 폴더에 `input.k` 만 두고 끝난 뒤 `Remap_dti.k` 가 없으면 「output not produced」로 실패를 친다(2026-10-16 러너 배선 실측 — 예전 판의 REMAP 예시는 그래서 지웠다). 체인 앞뒤에서 직접 실행한다. `modelmeta`·`section` 은 JSON, 그림 셋은 SVG, `linkage-fit` 은 YAML 을 남긴다.

---

## info

### 용도

LS-DYNA K-파일의 메시 정보를 분석해 콘솔에 출력한다. 절점/요소/파트 개수, 바운딩 박스(두 기준), 메시 유효성, 요소 품질(Jacobian),
**참조 무결성**(정의되지 않은 세트 · 파트 · 섹션 · 재질 · 절점)을 한 번에 확인하는 조회용 op다. 마스터 덱이면 **인클루드 닫힘까지** 읽어
실제 모델 값을 낸다(2026-10-16 — 그 전에는 마스터 덱에서 절점 0 · 「Mesh has no nodes」였다).

### 호출 형태

바이너리 help 의 `Usage:` 줄과 정확히 일치한다.

```
Usage: KooRemapper info <mesh_file> [--strict]
```

| 인자 | 위치 | 필수 | 설명 |
|---|---|---|---|
| `<mesh_file>` | positional 1 | 필수 | 분석할 LS-DYNA K-파일 경로. 인클루드 파일은 이 덱이 가리키는 자리(대개 같은 폴더)에 있어야 함께 읽는다 |
| `--strict` | 플래그 | 선택 | 미정의 참조 · 망가진 카드 · 없는 노드를 가리키는 요소 중 하나라도 **단정**할 수 있으면 rc=1. 없으면 rc 는 언제나 0 이다(상위 파이프라인과의 계약) |

### 출력 정보

| 항목 | 설명 |
|---|---|
| 노드 · 요소 · 파트 수 | 인클루드 닫힘까지 센 값(마스터 덱이면 「인클루드 N개를 함께 읽었다」) |
| `Min bound` · `Max bound` · `Size` | ★**요소가 쓰는 절점** 기준이다(고아 제외) — 낙하판 · 접촉면을 bbox 로 놓는 도구는 이 값을 써야 한다 |
| `bbox basis` | 위 bbox 의 기준을 적는다(항상 나온다) |
| `All-node min/max/size` · `Orphan nodes` | 고아 절점(요소가 안 쓰는 절점)이 있을 때만 — `*NODE` 전체 bbox 와 고아 수·비율. 두 bbox 가 최대 요소 범위의 1% 넘게 다르면 축을 지목해 경고한다 |
| 참조 무결성 | `[OK] 참조 무결성 OK (세트·파트·섹션·재질·절점 …)` 또는 줄마다 한 건씩 `line N <키워드>: … 이 정의되지 않았습니다`(인클루드 안이면 끝에 `— 인클루드 <파일>`) |
| 검증 결과 | 메시 유효성 검사 |
| 요소 품질 | Jacobian 최소/최대 · 음수 Jacobian 요소 수. 셸(QUAD4)과 기하를 믿을 수 없는 2차 솔리드(ELFORM 25~28 · 칸이 모자란 카드)는 재지 않는다 — TET10 · 20/27/64절점 육면체는 코너로 잰다(2026-10-17) |

### 주의사항

- 현장 사고(2026-10-10) — 요소 기준 bbox 14.55 mm 와 전체 절점 bbox 67.50 mm 가 갈려 낙하판이 기기 밖 53 mm 에 생겼고 충돌이 아예
  없었다. 그 67.50 은 이 도구가 아니라 하류가 `*NODE` 에서 직접 뽑은 값이다 — bbox 는 이 도구의 `Min/Max bound` 를 쓴다.
- **2차 솔리드** — 리더가 절점 칸을 **다** 읽는다(2026-10-17). 고아 수는 중간절점까지 세어 정확하고, TET10 · 20/27/64절점 육면체의
  야코비안은 **코너로** 잰다(「코너로 그린다」 알림). 코너 차례를 모르는 ELFORM 25~28 과 칸이 모자란 카드(노드 8+2 쪼갬)만 경고하고 그
  파트의 야코비안은 재지 않는다 — 모자란 카드가 있으면 `Orphan nodes` 는 **상한**이다. (2026-10-16 까지는 앞 8칸만 담아 TET10 덱에서
  거짓 고아 · 거짓 「음수 2」를 냈다.)
- `--strict` 는 세트(`*SET_NODE` 계열 · `*SET_SEGMENT`) · `*BOUNDARY_SPC_NODE` · `*LOAD_NODE_POINT` · `*INITIAL_VELOCITY_NODE` ·
  `*BOUNDARY_PRESCRIBED_MOTION_NODE` · `*CONSTRAINED_EXTRA_NODES_NODE` · `*ELEMENT_MASS` · `*DATABASE_HISTORY_NODE` · CNRB PNODE ·
  `*DEFINE_COORDINATE_NODES` 가 가리키는 **절점**도 본다(2026-10-16 · 줄마다 한 건). 이름이 정확히 같을 때만 보고, 변종 · 조인트 ·
  스폿용접은 「검사하지 않은 자리」로 센다. 맨 `*NODE` 가 하나도 없는 조각 덱은 단정하지 않는다. 실사용 6,053장에서 거짓 경보 0.
- 인클루드를 하나라도 못 읽으면(없는 파일 · `*INCLUDE_TRANSFORM` 등) 참조를 **단정하지 않고** `*INCLUDE 안은 보지 않았습니다:` 줄에
  그 파일만 적는다. `*INCLUDE +` · `*INCLUDE -`(그 파일의 칸 폭을 바꾼다)가 있으면 펼치지 않고 주 덱만 읽었다고 말한다.
- 접촉 Card 3 자리에 Card A 가 밀려 올라온 손상(옛 `contact modify` 가 만들던 꼴)을 **의심**으로 말한다 — 표기로만 알아본 것이라 단정하지 않는다.

### 예제

직접 실행이다.

```bash
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper info clip_board.k
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper info master.k --strict   # 인클루드 파일은 master.k 가 가리키는 자리에
```

**체인(REMAP 스텝)으로는 쓸 수 없다.** 덱(`Remap_dti.k`)을 내지 않으므로 rc 0 이어도 러너가 「output not produced」로 실패를 친다
(러너는 Output 폴더에 `input.k` 하나만 둔다 — 2026-10-16 배선 실측). 체인 앞뒤에서 직접 실행한다.

### 개발 현황

정본 `KooRemapper/docs/KooRemapper_Manual.md` §11(bbox 두 기준 · `--strict` · 참조 무결성 · 인클루드 닫힘). 회귀
`test_info_include_closure.py` · `test_reader_include_closure.py` · `test_dangling_node_refs.py` · `test_secondorder_solid.py`.

---

## modelmeta

> 지금은 정본 `KooRemapper/docs/KooRemapper_Manual.md` §43.5 가 있다(2026-10 판). 아래 본문은 2026-09-18 에 바이너리 help 와 예제 YAML 로 쓴 것이고, 그 뒤 바뀐 것은 끝의 「2026-10 정본 대조」에 모았다.

### 용도

K-파일을 읽어 파트별 기하 메트릭·재료·연결성(connectivity)을 구조화된 JSON 으로 추출한다. 모델을 변형하지 않는 읽기 전용 메타 추출 op다. `*CONTACT` 카드가 없어도 기하학적으로 닿는 파트쌍을 탐지할 수 있다.

### 호출 형태

`modelmeta` 는 config YAML 파일 경로를 positional 인자로 받는 yaml-config op다.

```
KooRemapper modelmeta <config.yaml>
```

근거: `modelmeta` 는 별도의 `Usage:` help 줄을 출력하지 않는다. `--help` 를 붙여 실행하면 이를 config 파일 경로로 간주해 `[ERROR] [modelmeta] Cannot open config: --help` 로 실패하는데, 이 동작이 "첫 positional 인자 = config 파일" 임을 보여준다. 실제 호출 형태는 예제 YAML 헤더의 `KooRemapper modelmeta examples/modelmeta/modelmeta.yaml` 을 따른다.

### config YAML 인자

`examples/modelmeta/modelmeta.yaml` 기준이다.

| 키 | 예제값 / 기본 | 설명 |
|---|---|---|
| `model` | (필수) | 분석 대상 K-파일. 읽기 전용 · `*INCLUDE` 닫힘 **전체**(중첩 · 매뉴얼 규칙)를 읽는다 — 메시 · 재질 · 접촉 |
| `detect` | `true`(예제값) | `*CONTACT` 없이도 기하학적으로 닿는 파트쌍 탐지 |
| `gap_tol` | `0.2`(예제값) | 탐지 갭 허용치(모델 길이 단위) |
| `output` | 생략 시 `model` 이름에서 유도 → `<model>_modelmeta.json` | 출력 JSON 의 **접두사** — 뒤에 `_modelmeta.json` 이 항상 붙는다(확장자까지 적으면 `meta.json_modelmeta.json` 이 된다) |
| `material_db` | 생략 시 실행파일 옆 번들 DB | 재료 DB 경로. 상대 경로는 YAML 폴더 기준이지만 **번들 폴백이 없다**(matdb 의 `database` 와 다르다) |
| `db_mid_fallback` | `false`(opt-in) | MID 일치 폴백. 로컬 MID 충돌 위험이 있어 명시적으로 켤 때만 사용 |

`detect`/`gap_tol` 의 값은 예제에 설정된 값이며, 실제 내장 기본값 여부는 확인 필요. 그 밖의 키 존재 여부도 확인 필요.

### 출력

`output` 은 파일 이름이 아니라 **접두사**다(2026-09-18 실행 확인) — 뒤에 `_modelmeta.json` 이 항상 붙는다. `output: meta3` → `meta3_modelmeta.json`, 생략하면 `<model>_modelmeta.json`. **확장자까지 적으면 그대로 접두사가 되어** `output: meta5.json` → `meta5.json_modelmeta.json` 이 나온다. JSON 스키마의 상세 필드 구성은 확인 필요.

`material_db` 의 상대 경로는 [README §YAML 설정 공통 규칙](../README.md#yaml-설정-공통-규칙) 대로 YAML 폴더 기준이지만, **`matdb` 의 `database` 와 달리 번들 DB 폴백이 없다**(2026-09-18 실행 확인). `material_db: material_db.json` 이라고 이름만 적었는데 YAML 폴더에 그 파일이 없으면 번들로 넘어가지 않고 `[INFO] [modelmeta] Material DB: <YAML폴더>/material_db.json (0 entries)` 로 **재료 매칭이 전부 빠진 채 rc=0** 으로 끝난다 — 오류가 안 나므로 알아채기 어렵다. 키를 생략하거나 절대 경로를 써라. 생략하면 `<exe>/materials/` → `<exe>/../materials/` → 작업 폴더 `materials/` 순으로 찾는다(`matdb` 는 작업 폴더를 **먼저** 본다 — 탐색 순서도 다르다).

### 예제

직접 실행이다.

```bash
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper modelmeta examples/modelmeta/modelmeta.yaml
```

config YAML(`examples/modelmeta/modelmeta.yaml`) 예시다.

```yaml
model: clip_board.k        # 분석 대상 (읽기 전용, *INCLUDE 닫힘 전체)
detect: true               # *CONTACT 없이도 기하학적으로 닿는 파트쌍 탐지
gap_tol: 0.2               # 탐지 갭 허용치 (모델 길이 단위)
# output: my_model         # 생략 시 model 이름에서 유도 → <model>_modelmeta.json
# material_db: /path/material_db.json   # 생략 시 실행파일 옆 번들 DB
# db_mid_fallback: false   # MID 일치 폴백 (로컬 MID 충돌 위험 — opt-in)
```

**체인(REMAP 스텝)으로는 쓸 수 없다.** 러너가 넣는 `output: Remap_dti.k` 가 접두사가 되어 `Remap_dti.k_modelmeta.json` 을 쓰고, `Remap_dti.k` 가 없어 러너가 실패로 친다(2026-10-16 러너 배선 실측). 직접 실행한다.

### 주의사항

- 정본에 없는 op 이므로, 위 인자표·동작은 help 동작과 단일 예제에서 유추한 것이다. 확인되지 않은 옵션·기본값은 실제 실행으로 검증할 것.
- `db_mid_fallback` 은 로컬 MID 충돌 위험 때문에 opt-in 이다. 근거 없이 켜지 말 것.
- `model` 은 읽기 전용이다. `*INCLUDE` 는 닫힘 전체를 읽고, 못 읽은 인클루드와 따라가지 않는 변종(`*INCLUDE_TRANSFORM` 등)은 이름으로 경고한다(2026-10-16 전에는 한 단계만 따라갔고 `_TRANSFORM` 파일의 재질을 ID 오프셋 없이 그 번호 그대로 썼다).

### 2026-10 정본 대조

- ★**2차 솔리드**(ELFORM 16·17·23~29) 파트는 `part.second_order: true` 이고 기하 값 — `volume` · `area_ext` · `proj` · `edge_len` · `mass` — 은 **코너로 잰 값**이다(`geometry_basis: "corners"` · 2026-10-17 — 모서리가 곧으면 정확하고 중간절점이 휜 모서리는 곧게 본다). 1차 파트는 `"nodes"`. `n_node` · `bbox` · `model.orphan_nodes` 는 중간절점까지 세어 정확하다. **`null`** 은 기하를 믿을 수 없는 파트뿐이다 — 코너 차례를 매뉴얼이 적지 않은 ELFORM 25~28 과 절점 칸이 모자란 카드(`geometry_basis: null` + `geometry_reason` · `mass_reason`). `model.second_order_solid_pids` 는 2차 파트 전부를 `geometry_basis` 와 함께 적는다. **`null` 을 0 으로 읽지 마라.** (2026-10-16 까지는 리더가 앞 8칸만 담아 2차 파트 전부가 null 이었다 — 실측 부피 −48.4%.)
- `edge_len` 은 요소 종류의 모서리 표로 잰다(2026-10-17) — 예전에는 육면체 12모서리 표를 사면체에도 써 n1–n3 이 빠졌다(실측 max 9.055 · 참 10.0). 사면체 파트의 값이 이 판부터 달라질 수 있다.
- 메시도 인클루드 닫힘까지 읽는다(2026-10-16) — 마스터 덱의 파트가 비지 않는다(재질 · 접촉 원문은 원래 닫힘까지 모았다).
- `parts[].edge_len {min, p50, max}` 를 낸다 — min·max 는 정확값, p50 은 버킷 2048개 히스토그램(오차 ≤ (max−min)/2048).

### 개발 현황

바이너리(v1.8.0)에 op 로 존재하며 동작 예제 YAML 이 제공된다. 정본 §43.5 · §45.5a(2차 솔리드). 회귀 `test_modelmeta_includes.py` · `test_secondorder_solid.py`.

---

## version

### 용도

KooRemapper 바이너리의 버전을 콘솔에 출력한다.

### 호출 형태

```
KooRemapper version
```

인자 없음.

### 예제

```bash
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper version
```

출력 버전은 `1.8.0` 이다(help 배너 기준). REMAP 스텝으로 쓸 경우 `params.op: version` 이며, 정보 출력용이라 체인 산출 파일은 없다.

### 개발 현황

정본 매뉴얼에 전용 섹션은 없으나 버전 문자열은 바이너리 배너로 확인된다(v1.8.0).

---

## neutralaxis

### 용도

적층의 EI 가중 중립축·굽힘강성 계산.

적층 단면의 EI 가중 중립축·굽힘강성 계산 (읽기 전용 보고).

### 호출 형태

위치 인자 op 다.

```
KooRemapper neutralaxis <mesh_file> [--axis x|y|z]
```

근거 — 바이너리 `help neutralaxis` 의 사용법(2026-10-16 · SmartTwinPreprocessor.sif 판).

### 인자

| 키 | 필수 · 기본 | 설명 |
|---|---|---|
| `mesh_file` | 필수 | 적층이 든 입력 메시 파일(K-파일) |
| `axis` | 기본 `z` | 적층 방향(기본 z — shellmap·restack 관례와 같다) |

### 예제

KooRemapper 저장소 예제다 — 같은 형식의 자기 모델로 바꿔 쓴다.

`box.yaml`

```yaml
output: box.k
lx: 20.0
ly: 10.0
lz: 2.0
nx: 10
ny: 5
nz: 2
rho: 7.85e-9
E: 210000.0
nu: 0.3
mid: 1
secid: 1
pid: 1
part_title: PLATE
```

직접 실행이다(필요한 입력을 작업 폴더에 둔다).

```bash
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper neutralaxis box.k
```

**체인(REMAP 스텝)으로는 쓸 수 없다.** 콘솔에 숫자만 낸다(파일 없음) — 직접 실행한다.

### 주의사항

- 층 = 파트. 솔리드는 두께를 메시에서, 셸은 *SECTION_SHELL 에서 읽는다
- E 나 두께를 못 읽은 파트는 **제외하고 그렇게 말한다** — 0 으로 쓰지 않는다
- shellmap 은 평면 덱의 축=0 을 중립면으로 본다 — 이 op 의 오프셋이 그 전제를 재는 자다

### 개발 현황

바이너리(v1.8.0 · 63 op 판, 2026-10-16 SIF)에 있다. 정본 `KooRemapper/docs/KooRemapper_Manual.md` §44.4 · 회귀 `tools/regress/test_neutralaxis.py`.

---

## linkage-fit

### 용도

접힌 덱에서 군별 강체변환 역산 (축·각·피벗·축이동).

접힌 덱에서 군별 강체변환(축·각·피벗·축이동) 역산 — 피벗 산포를 함께 보고.

### 호출 형태

config YAML 파일 경로를 위치 인자로 받는 yaml-config op 다.

```
KooRemapper linkage-fit <config.yaml>
```

근거 — 바이너리 `help linkage-fit` 의 사용법(2026-10-16 · SmartTwinPreprocessor.sif 판).

### config YAML 인자

| 키 | 필수 · 기본 | 설명 |
|---|---|---|
| `reference` | 필수 | 기준(펼친) 덱(k-파일) |
| `folded` | 필수 | 기준과 절점 번호가 같은 접힌 덱(k-파일) |
| `output` | 필수 | 출력 접두사 — `applyfold` 용 `<output>.yaml` 을 쓴다 |
| `angle_tol` | 기본 `0.5` | 두 파트를 한 군으로 볼 각도 공차[deg](축 방향에도 쓴다) |
| `pivot_tol` | 기본 `0.5` | 군을 묶을 때 피벗·축 방향 미끄럼의 길이 공차. 각도만으로 묶었다는 경고의 문턱이기도 하다 |

### 예제

KooRemapper 저장소 예제다 — 같은 형식의 자기 모델로 바꿔 쓴다.

`lf.yaml`

```yaml
reference: examples/linkage_fit/arm_flat.k
folded: examples/linkage_fit/arm_folded.k
output: fold_groups
```

직접 실행이다(필요한 입력을 작업 폴더에 둔다).

```bash
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper linkage-fit lf.yaml
```

필요한 입력 — `examples/linkage_fit/arm_flat.k`

**체인(REMAP 스텝)으로는 쓸 수 없다.** 산출이 군 표 YAML(`<output>.yaml`)이다 — 직접 실행해 그 표를 `applyfold` 의 `groups` 로 넘긴다.

### 주의사항

- 두 덱의 **절점 번호가 같아야** 한다 — 짝이 없으면 몇 개인지 말하고 rc=1
- 회전은 Horn 사원수법(자체 Jacobi)으로 최소제곱 적합한다. 외부 선형대수를 쓰지 않는다
- 축이동(slide)이 0 이 아니면 **나사 운동**이다 — 단순 힌지가 아니라는 뜻이다
- 잔차가 모델 치수에 견주어 크면 **강체가 아니다** — 변형이 섞인 파트는 힌지로 안 환원된다
- ★군 묶기는 각·축·피벗·축이동이 **모두** 맞아야 한다. 각도만으로 묶으면 조용히 틀린다 — 같은 각 파트의 피벗이 pivot_tol 보다 흩어지면 그 산포를 **숫자로** 경고한다
- 피벗은 축 위 어느 점이든 같다 — 파트 중심의 축 좌표를 가진 점으로 보고한다

### 개발 현황

바이너리(v1.8.0 · 63 op 판, 2026-10-16 SIF)에 있다. 정본 `KooRemapper/docs/KooRemapper_Manual.md` §44.6 · 회귀 `tools/regress/test_linkage_fit.py`.

---

## section

### 용도

메시를 평면으로 잘라 요소 다각형 + 매니페스트.

메시를 평면으로 잘라 요소 다각형 + 매니페스트를 낸다 (그림의 엔진).

### 호출 형태

config YAML 파일 경로를 위치 인자로 받는 yaml-config op 다.

```
KooRemapper section <config.yaml>
```

근거 — 바이너리 `help section` 의 사용법(2026-10-16 · SmartTwinPreprocessor.sif 판).

### config YAML 인자

| 키 | 필수 · 기본 | 설명 |
|---|---|---|
| `model` | 필수 | 자를 덱(k-파일). 마스터 덱은 `*INCLUDE` 닫힘 전체를 읽으므로 포함 파일이 덱이 가리키는 자리에 있어야 한다(플랫폼이면 같은 세션). 그래도 요소가 없으면 빈 그림을 내지 않고 거절하며, 어느 인클루드를 못 읽었는지 목록과 함께 말한다 |
| `output` | 필수 | 출력 접두사 — `<output>_section.json` 과 `<output>_section.svg` 를 쓴다 |
| `axis` | 기본 `auto` | 자르는 평면의 법선. `auto` 는 단면이 선으로 무너지는 축을 빼고 파트를 가장 많이 만나는 축을 고르며, 동점이면 단면 bbox 넓이로 가른다. 「적층에 수직」이 규칙이 **아니다** — 실측 61파트 배터리 적층에서 z 는 2파트, x·y 는 59파트를 만났고 감긴 덱에서는 반대였다 |
| `at` | 선택 | 축 위의 평면 위치. 생략하면 bbox 중앙이다. 평면이 절점층에 정확히 걸리면(가장 보고 싶은 층 경계다) 알아채고 ε 만큼 비켜 자르며 두 사실을 다 적는다 |
| `max_parts` | 기본 `60` | SVG 범례에 쓰는 파트 수 상한 — 넘는 것은 생략 수로 센다. 매니페스트와 다각형은 자르지 않는다(평면이 자른 파트를 전부 낸다) |
| `compare` | 선택 | 같은 그림에 그릴 둘째 덱(선택). `mode: panels` 면 덱마다 축·축척을 따로 잡고, `mode: overlay` 면 **같은 평면**으로 둘 다 잘라 둘째를 점선으로 그린다. 짝은 절점 번호다(linkage-fit·applyfold 가 같은 절점 번호를 요구하므로 겹쳐 맞추는 비용이 없다) |
| `mode` | 기본 `panels` | `panels` = 나란히, `overlay` = 한 틀 |
| `width` | 기본 `1200` | SVG 폭 px(430 이상 — 여백 70×2 + 범례 260 + 그림) |
| `height` | 기본 `900` | SVG 높이 px(240 이상) |
| `isotropic` | 기본 `False` | true 면 두 축을 한 축척으로 그린다. 기본은 비등방이다 — 실제 적층은 1:9,375 라 등축이면 최박층이 실측 0.081 px 다. 확대한 축과 배율은 늘 그림에 적는다 |
| `svg` | 기본 `True` | false 면 JSON 만 쓴다 |

### 예제

KooRemapper 저장소 예제다 — 같은 형식의 자기 모델로 바꿔 쓴다.

`sec.yaml`

```yaml
model: examples/stackwrap/flat_stack.k
output: stack
axis: auto
```

직접 실행이다(필요한 입력을 작업 폴더에 둔다).

```bash
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper section sec.yaml
```

필요한 입력 — `examples/stackwrap/flat_stack.k`

**체인(REMAP 스텝)으로는 쓸 수 없다.** 산출이 SVG·JSON 이라 rc 0 이어도 `Remap_dti.k` 가 없어 러너가 실패(`output not produced`)로 친다 — 직접 실행한다.

### 주의사항

- ★2차 솔리드는 **코너로 그린다**(2026-10-17 — TET10 ELFORM 16·17 · 20/27/64절점 육면체 23·24·29 · 휜 모서리는 곧게 · 콘솔이 「코너로 그린다」 고 말한다). 실측: `convert type: tet10` 덱의 단면 총면적이 1차 원본과 같은 0.665(예전 리더는 앞 8칸만 담아 0.19). **거절하는 것**은 코너 차례를 매뉴얼이 적지 않은 ELFORM 25~28 과 절점 칸이 모자란 카드(노드 8+2 쪼갬)뿐이다
- **모서리 기반**이다 — 면 테이블로 짜면 TET4 가 틀린다(면 0·3 이 가짜 면으로 통과한다)
- 육면체 12 모서리 표를 TET 에 쓰면 모서리 (n0,n2) 가 빠진다 → 종류별 표를 쓴다
- ★`axis: auto` 는 ① 선에 가까운 축을 빼고 ② 파트를 가장 많이 만나는 축 ③ 동점이면 단면 bbox 넓이 '적층 방향에 수직' 이 규칙이 **아니다** — 실측 배터리 덱은 z 가 61 중 2파트, x·y 는 59파트
- ★평면이 절점층에 정확히 걸리면(= 가장 보고 싶은 자리) **ε 비켜 다시 자르고 그 사실을 적는다**
- 셸은 선분이 나온다 — 두께는 메시에 없고 *SECTION_SHELL 에서 읽으며 **출처를 적는다**
- 매니페스트가 그림이 거짓말하지 않게 하는 장치다 — 축 선택 근거·맞은 파트 수/전체·절점 적중· ε 비킴·퇴화 절단 수·단면 범위·종횡비·**최소 피처**·파트별 두께와 출처
- 단위를 주장하지 않는다 — LS-DYNA 덱은 단위를 담지 않는다
- 산출은 JSON + **SVG** 다(덱은 쓰지 않는다). SVG 는 op 이 쓴다 — 프런트와 MCP 가 각각 그리면 구현이 둘이 되어 갈린다. 의존성은 0 이다
- `compare:` 로 두 덱을 한 그림에 — `mode: panels`(칸마다 축·축척 따로) 또는 `mode: overlay`(**같은 평면**으로 자르고 B 를 점선으로). 절점 번호가 짝이라 공짜다
- ★비등방이 기본 — 등축으로 그리면 실제 적층(1:9,375)은 층이 안 보인다(0.081 px). **확대 축과 배율을 그림 안에 적는다** — 적는 것이 기능의 일부다
- 최소피처가 1.5 px 미만이면 '보이지 않는다' 고 말한다(획을 줄여도 안 보인다)
- 파트 제목은 자유 텍스트다 — XML 이스케이프하고 제어문자는 ? 로 바꾸고 그 사실을 적는다
- 메시를 **인클루드 닫힘까지** 읽는다(2026-10-16) — 마스터 덱도 자른다. 인클루드를 못 찾아 요소가 없으면 거절하고 그 파일을 짚는다

### 개발 현황

바이너리(v1.8.0 · 63 op 판, 2026-10-16 SIF)에 있다. 정본 `KooRemapper/docs/KooRemapper_Manual.md` §45.2 · 회귀 `tools/regress/test_section.py`.

---

## surfview

### 용도

자유면만 직교투영·깊이정렬로 그린다.

자유면만 뽑아 직교투영·깊이정렬로 그린다 (전체 와이어프레임은 검은 덩어리가 된다).

### 호출 형태

config YAML 파일 경로를 위치 인자로 받는 yaml-config op 다.

```
KooRemapper surfview <config.yaml>
```

근거 — 바이너리 `help surfview` 의 사용법(2026-10-16 · SmartTwinPreprocessor.sif 판).

### config YAML 인자

| 키 | 필수 · 기본 | 설명 |
|---|---|---|
| `model` | 필수 | 그릴 덱(k-파일). 마스터 덱은 `*INCLUDE` 닫힘 전체를 읽는다(포함 파일이 덱이 가리키는 자리에 있어야 한다 — 플랫폼이면 같은 세션). 그래도 요소가 없으면 빈 그림을 내지 않고 거절하며 어느 인클루드를 못 읽었는지 말한다 |
| `output` | 필수 | 출력 접두사 — `<output>_surface.svg` 를 쓴다 |
| `azimuth` | 기본 `35.0` | 보는 방위각[deg] |
| `elevation` | 기본 `25.0` | 보는 고도각[deg] |
| `wire` | 기본 `False` | true 면 음영 면 대신 모서리만 그린다. op 이 ink_ratio(그린 선 길이 px ÷ 캔버스 px)를 보고하고 1.0 을 넘으면 경고한다 — 그 위로는 선이 더해도 보이는 게 없다(실측 286k 요소 덱의 자유면 1.94 · 모든 모서리 5.49) |
| `width` | 기본 `1200` | SVG 폭 px(430 이상) |
| `height` | 기본 `900` | SVG 높이 px(240 이상) |
| `max_parts` | 기본 `60` | 범례에 쓰는 파트 수 상한 — 넘는 것은 생략 수로 센다 |

### 예제

KooRemapper 저장소 예제다 — 같은 형식의 자기 모델로 바꿔 쓴다.

`sv.yaml`

```yaml
model: examples/stackwrap/flat_stack.k
output: stack
azimuth: 35
elevation: 25
```

직접 실행이다(필요한 입력을 작업 폴더에 둔다).

```bash
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper surfview sv.yaml
```

필요한 입력 — `examples/stackwrap/flat_stack.k`

**체인(REMAP 스텝)으로는 쓸 수 없다.** 산출이 SVG·JSON 이라 rc 0 이어도 `Remap_dti.k` 가 없어 러너가 실패(`output not produced`)로 친다 — 직접 실행한다.

### 주의사항

- ★2차 솔리드는 **코너로 그린다**(2026-10-17 — TET10 ELFORM 16·17 · 20/27/64절점 육면체 23·24·29 · 휜 모서리는 곧게 · 콘솔이 「코너로 그린다」 고 말한다). 실측: `convert type: tet10` 덱의 단면 총면적이 1차 원본과 같은 0.665(예전 리더는 앞 8칸만 담아 0.19). **거절하는 것**은 코너 차례를 매뉴얼이 적지 않은 ELFORM 25~28 과 절점 칸이 모자란 카드(노드 8+2 쪼갬)뿐이다
- 자유면만 그린다 — 실측 286k 요소 덱에서 전체 면 855,575 중 자유면 57,098(6.7%)뿐이다
- ★면도 **종류별 표**다 — 육면체 표로 세면 TET4 자유면이 4면이 아니라 5면(3개가 가짜)이 된다
- 사각면은 삼각형 둘로 쪼갠다 — 그래야 TET 의 자유면 집합이 완전해진다
- 음영은 법선과 보는 방향의 **절대** 각이다 — 부호를 쓰면 뒤집힌 요소에서 명암이 거꾸로 된다. 대신 **등진 삼각형 수**를 보고한다(닫힌 볼록체면 정확히 절반이어야 한다)
- ★이 그림은 **등축**이다 — 3D 형상을 비등방으로 늘이면 모양 자체가 거짓이다. 적층이 얇게 보이는 것이 사실이고, 층 두께를 보려면 `section` 을 쓴다
- `wire: true` 면 모서리만. `ink_ratio` 가 1.0 을 넘으면 포화라고 경고한다(실측 1.94)
- 삼각형을 **솎지 않는다** — 구멍이 뚫리면 그림이 거짓이다. 대신 SVG 크기를 말하고 5MB 를 넘으면 MCP 다운로드가 거절한다고 알린다(실측 12.2MB)
- 메시를 **인클루드 닫힘까지** 읽는다(2026-10-16) — 마스터 덱도 그린다. 인클루드를 못 찾아 요소가 없으면 거절하고 그 까닭을 말한다

### 개발 현황

바이너리(v1.8.0 · 63 op 판, 2026-10-16 SIF)에 있다. 정본 `KooRemapper/docs/KooRemapper_Manual.md` §45.3 · 회귀 `tools/regress/test_surfview.py`.

---

## stackdiagram

### 용도

파트 축범위로 층 모식도 + 중립축.

파트별 축 범위로 층 모식도를 그리고 중립축·기하 중심면을 함께 긋는다 (포개지는 적층은 거절한다).

### 호출 형태

config YAML 파일 경로를 위치 인자로 받는 yaml-config op 다.

```
KooRemapper stackdiagram <config.yaml>
```

근거 — 바이너리 `help stackdiagram` 의 사용법(2026-10-16 · SmartTwinPreprocessor.sif 판).

### config YAML 인자

| 키 | 필수 · 기본 | 설명 |
|---|---|---|
| `model` | 필수 | 읽을 덱(k-파일). 마스터 덱은 `*MAT` 까지 `*INCLUDE` 닫힘 전체를 읽는다(포함 파일이 덱이 가리키는 자리에 있어야 한다 — 플랫폼이면 같은 세션). 그래도 요소가 없으면 빈 그림을 내지 않고 거절하며 어느 인클루드를 못 읽었는지 말한다 |
| `output` | 필수 | 출력 접두사 — `<output>_stackdiagram.svg` 를 쓴다 |
| `axis` | 기본 `z` | 적층 축 x·y·z. 층을 재는 방향이며 `neutralaxis` 가 받는 축과 같다 |
| `force` | 기본 `False` | true 면 솔리드 파트의 축 범위가 포개져도 그린다. 그때 그림에 층 순서를 믿지 말라는 경고를 싣는다 — `section` 을 쓰라 |
| `enclosure_min_inside` | 기본 `2` | 한 파트가 다른 층을 몇 개 이상 **안에 품어야** 층이 아니라 감싸는 것(점선 외곽)으로 볼지. 1 이상 |
| `min_bar_px` | 기본 `3.0` | 얇은 층이 보이게 하는 막대 두께 바닥[px]. 바닥을 쓴 층은 두께가 과장되므로 몇 층인지 세고, 그림이 옆 숫자가 참이라고 적는다 |
| `width` | 기본 `900` | SVG 폭 px(430 이상) |
| `height` | 기본 `700` | SVG 높이 px(240 이상) |
| `max_parts` | 기본 `60` | 이름을 붙이는 층 수 상한 — 넘는 것은 생략 수로 센다 |

### 예제

KooRemapper 저장소 예제다 — 같은 형식의 자기 모델로 바꿔 쓴다.

`sd.yaml`

```yaml
model: examples/stackwrap/flat_stack.k
output: stack
axis: z
```

직접 실행이다(필요한 입력을 작업 폴더에 둔다).

```bash
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper stackdiagram sd.yaml
```

필요한 입력 — `examples/stackwrap/flat_stack.k`

**체인(REMAP 스텝)으로는 쓸 수 없다.** 산출이 SVG·JSON 이라 rc 0 이어도 `Remap_dti.k` 가 없어 러너가 실패(`output not produced`)로 친다 — 직접 실행한다.

### 주의사항

- ★2차 솔리드는 **코너로 그린다**(2026-10-17 — TET10 ELFORM 16·17 · 20/27/64절점 육면체 23·24·29 · 휜 모서리는 곧게 · 콘솔이 「코너로 그린다」 고 말한다). 실측: `convert type: tet10` 덱의 단면 총면적이 1차 원본과 같은 0.665(예전 리더는 앞 8칸만 담아 0.19). **거절하는 것**은 코너 차례를 매뉴얼이 적지 않은 ELFORM 25~28 과 절점 칸이 모자란 카드(노드 8+2 쪼갬)뿐이다
- 격자를 자르지 않는다 — 파트별 **축 범위**(사실상 AABB)만 쓰는 **모식도**다. 그래서 평평한 적층에서는 빠르고 또렷하지만, 쓸 수 있는 덱이 제한된다
- ★범위가 포개지는 적층(감긴 셀)은 **거절한다** — 포갠 것을 층처럼 쌓으면 층 순서가 거짓이 되고 그림은 그럴듯해 보인다. 그 덱은 `section` 으로 잘라서 봐야 한다 (`force: true` 로 넘길 수 있지만 그림에 '믿지 말라' 고 적는다)
- 적층 전체를 **품는** 파트(케이스·탭)는 갈라내서 점선 외곽으로만 그린다 — 실측에서 '전체의 90% 이상' 같은 분수 문턱은 88.4% 에서 빗나갔다(셸 띠가 분모를 늘린다)
- `*MAT` 을 못 읽으면(포함 파일을 못 찾은 경우 등 — 닫힘 안의 `*MAT` 은 읽는다) 층은 그리고 **중립축만** 생략한다
- 메시와 `*MAT` 을 **인클루드 닫힘까지** 읽는다(2026-10-16) — 마스터 덱도 그린다. 인클루드를 못 찾아 요소가 없으면 거절하고 그 까닭을 말한다
- 중립축·굽힘강성은 `neutralaxis` 와 **같은 계산**이다 — 숫자가 서로 다르면 결함이다
- 얇은 층은 min_bar_px 로 바닥 처리하므로 두께가 과장된다 — 그 층은 **옆 숫자가 참**이고 그림이 아니다. 몇 층을 바닥 처리했는지 말한다

### 개발 현황

바이너리(v1.8.0 · 63 op 판, 2026-10-16 SIF)에 있다. 정본 `KooRemapper/docs/KooRemapper_Manual.md` §45.4 · 회귀 `tools/regress/test_stackdiagram.py`.
