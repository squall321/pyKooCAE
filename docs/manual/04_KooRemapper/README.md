# KooRemapper — `.k` 메쉬·재료 리매핑 CLI (op 색인)

LS-DYNA 키워드(`.k`) 모델의 **메쉬·재료를 변환·리매핑**하는 C++ CLI 도구(v1.8.0, **47 op**).
위 3개(Nuitka) 도구와 달리 독립 C++ 바이너리이며, `SmartTwinPreprocessor.sif` 내부에
네이티브 바이너리(`/opt/kooremapper/bin/KooRemapper`)로 구워져 KooMeshModifier 와 동일하게
`apptainer exec <sif> <바이너리>` 로 호출된다. KooChainRun 시나리오의 `REMAP` 스텝으로
삽입하거나 독립 CLI 로도 실행한다.

- 코드: `Runner/KooRemapperStep.py`(모듈 래퍼), `Runner/CumulativeScenarioRunner.py`(`_run_kooremapper_step`, REMAP 스텝 실행)
- 빌드 반영: `serviceApptainers/BuildSmartTwinPreprocessor.sh` 의 KooRemapper 복사 단계(재빌드 시 sif 에 상주)
- 경로 탐색: `Runner/PathResolver.py:find_kooremapper()`
- **op별 상세 레퍼런스**: 아래 [op 레퍼런스](#op-레퍼런스-카테고리별) 표의 카테고리 페이지(`ops/`).
- **여러 도구와 엮어 시나리오 구성**: [통합 조합 가이드](../00_overview/composition_guide.md).

---

## 호출 규약

두 가지 인자 형태로 47개 op를 모두 호출한다. op가 어느 형태인지는 각 op 레퍼런스의 바이너리 `Usage` 로 확정한다.

| 형태 | 예 | 대상 op(예) |
|------|----|---------|
| yaml-config ops | `KooRemapper matdb config.yaml` | matdb, matswap, assemble, battery, cnrb2solid, hfdamp, contact, load, boundary, rbe, relax, database, bend, indent 등 |
| positional ops | `KooRemapper map bent.k flat.k out.k` | map, shellmap, unfold, generate, strain, prestress, info, extract-surface 등. 일부는 config.yaml 을 **위치 인자**로 받는다(예: `generate-var <config.yaml> <output.k>`, `squeeze <mesh.k> <config.yaml> <output_prefix>`) |

> 각 op는 필요한 **입력 파일이 작업 디렉토리에 있어야** 한다(CLI 특성). REMAP 스텝은 이를 자동 준비한다.

---

## YAML 설정 공통 규칙

`config.yaml` 을 받는 op 40종(load · boundary · rbe · strip · merge · contact · relax · explicit ·
implicit · modal · ale · database · optimize · stabilize · matdb · cclip · convert · refine · elform ·
restack · bend · indent · formstrain · disconnect · iga · warpage · offset · wrap · update · cnrb2solid ·
hfdamp · battery · modelmeta · assemble · matswap · tetremesh · meshfix · `generate box` · squeeze ·
generate-var)이 같은 리더를 쓴다. 아래는 그 공통 규칙이다.

| 규칙 | 내용 |
|---|---|
| UTF-8 BOM | 파일 앞 BOM 은 무시한다. 윈도우 편집기(메모장 등)로 저장한 설정도 그대로 쓸 수 있다. |
| 탭 들여쓰기 | 들여쓰기에 탭이 있으면 **rc=1** 로 거절한다 — `[ERROR] [<op>] YAML 들여쓰기에 탭을 쓸 수 없습니다 (공백을 쓰세요): <n>번째 줄: <줄 내용>`. 파일 전체를 훑으므로 그 op 이 읽지도 않는 키 아래의 탭도 걸린다(예전에는 rc=0 으로 통과하던 설정이 지금은 실패한다). 따옴표 값 안의 탭은 그대로 값이지만, `\|`/`>` 리터럴 블록(`material_card`·`czm_material_card`·`material_cards`) 안에서 탭으로 시작한 줄은 거절한다 — 예전에는 그 카드 줄이 조용히 사라졌다. |
| 상대 경로 | 명령줄에 준 경로만 작업 폴더(CWD) 기준이다. **YAML 안의 상대 경로는 폴더가 붙어 있든(`../data/box.k`) 없든(`box.k`) 그 YAML 파일이 있는 폴더 기준**이며 작업 폴더로 되돌아가지 않는다. 절대 경로(`/`·`\` 시작, `X:` 드라이브)는 그대로 쓴다. |
| 예외 | `map <config.yaml>` 은 이 리더를 쓰지 않는다 — BOM 이 있으면 `YAML config missing required keys (bent, flat, output)` 로 죽고, 탭은 거절 대신 조용히 잘못 읽힌다. `squeeze <mesh> <config> <prefix>` 는 탭은 거절하지만 BOM 은 못 걸러 `No parts defined in squeeze config` 가 된다. `matdb` 의 `database` 키만 경로 규칙이 다르다(슬래시 없는 파일 이름은 YAML 폴더 기준, 폴더가 붙으면 작업 폴더 기준). |
| 파이프 입력 | 파이프·프로세스 치환·`/dev/stdin` 으로 설정을 넘기면 탭 검사를 건너뛴다(되감을 수 없는 스트림). |

### 단독 op 의 `output` 은 필수다

`wrap` · `update` · `restack` · `bend` · `indent` · `formstrain` · `convert` · `refine` · `elform` ·
`disconnect` · `iga` · `warpage` · `offset` 13종은 `output` 이 비어 있으면 rc=1 로 거절한다.
예전에는 입력 모델 파일을 그대로 덮어썼다.

### 모르는 값은 조용히 넘어가지 않는다

예전에 '기본값으로 조용히 떨어지던' 열거값들이 이제 rc=1 이고 출력 파일도 만들지 않는다.
단독 명령과 `assemble` 안 양쪽에 같은 검사가 걸린다.

| op / 키 | 허용값 | 예전 동작 |
|---|---|---|
| `restack` 의 `element_type`(층별 포함) | `solid` \| `tshell` \| `shell` (대소문자 구분 — `SOLID` 도 거절) | 그 밖의 값은 전부 조용히 `solid` |
| `matdb` 의 `damping_preset` | `smartphone_drop` \| `smartphone_drop_aggressive` \| `quasi_static` \| `off` (대소문자 무시, 키 생략은 그대로 허용) | `light`/`moderate`/`heavy`/`custom` 같은 옛 문서 값도 통과 |
| `boundary` 의 `select` | `direction` \| `all` \| `set`(`set` 은 `set_id` 필수) | 오타가 `direction` 으로 |
| `rbe` 의 `select` | `direction` \| `all` (여기엔 `set` 이 없다) | 오타·`set` 이 조용히 `all` 로 |
| `load` 의 `select` | `direction` \| `set` \| `tied` (여기엔 `all` 이 없다) | — |

거절 메시지에는 단독·`assemble` 모두 `[ERROR] ` 접두가 붙고, 그 뒤 op 표기는 op 마다 두 갈래다 —
`<op>: ` 형(`[ERROR] boundary: boundaries[0]: unsupported select 'x' (allowed: direction, all, set)`,
`rbe: constraints[0]: …`, `matdb: unsupported damping_preset …`, `restack: layers[0]: …`)과
`[<op>] ` 형(`[ERROR] [load] loads[0]: unsupported select 'all' (allowed: direction, set, tied)`,
`[ERROR] [contact] unsupported contact_type …`). 같은 값을 `assemble` 안에서 줘도 문구는 똑같다
(예: `[ERROR] restack: layers[0]: unsupported element_type 'hex' (allowed: solid, tshell, shell)`) —
`assemble` 이라고 접두가 더 붙지는 않는다. 로그를 grep 할 때는 `unsupported ` 로 잡는 편이 안전하다.

> `boundary` 와 `rbe` 의 허용값이 서로 다르다. `boundary` 에는 `set` 이 있고 `all` 도 있지만,
> `rbe` 에는 `set` 이 없다. 두 op 의 help 가 오랫동안 같은 `direction | all` 을 찍어 혼동을 키웠다
> (바이너리의 `boundary` help 는 아직 `direction | all` 만 적어 실제와 다르다 — 위 표를 따르라).

---

## op 레퍼런스 (카테고리별)

47개 op를 9개 카테고리 페이지로 나눠 op별(용도·호출·인자·예제·주의)로 문서화했다.

| 카테고리 | op | 페이지 |
|----------|----|--------|
| 메시 매핑 | `map` · `shellmap` · `unfold` | [ops/mesh_mapping.md](ops/mesh_mapping.md) |
| 메시 생성 | `generate` · `generate-var` · `battery` · `cclip` | [ops/mesh_generate.md](ops/mesh_generate.md) |
| 메시 편집 | `convert` · `refine` · `elform` · `disconnect` · `offset` · `wrap` · `restack` · `update` · `iga` | [ops/mesh_edit.md](ops/mesh_edit.md) |
| 표면·재메시 | `extract-surface` · `tetremesh` · `meshfix` · `cnrb2solid` · `merge` · `strip` | [ops/surface_remesh.md](ops/surface_remesh.md) |
| 변형·초기응력 | `strain` · `prestress` · `formstrain` · `warpage` · `bend` · `indent` · `squeeze` | [ops/deform_prestress.md](ops/deform_prestress.md) |
| 재료·어셈블리 | `matdb` · `matswap` · `assemble` | [ops/material_assembly.md](ops/material_assembly.md) |
| 하중·경계·접촉 | `load` · `boundary` · `rbe` · `contact` · `relax` · `stabilize` · `database` · `hfdamp` | [ops/load_bc_contact.md](ops/load_bc_contact.md) |
| 솔버 설정 | `explicit` · `implicit` · `modal` · `ale` · `optimize` | [ops/solver_setup.md](ops/solver_setup.md) |
| 정보·메타 | `info` · `modelmeta` · `version` | [ops/info_meta.md](ops/info_meta.md) |

> **숨은(hidden) op 5종**: `extract-surface` · `tetremesh` · `meshfix` · `merge` · `strip` 은
> 바이너리 `--help` 최상위 목록엔 안 뜨지만 정상 동작한다(각자 `Usage` 출력, 실행 검증됨).
> `split_fillet`/`tet10`/`quadratic`/`remesh` 는 op가 아니라 예제·요소타입 이름이므로 명령이 아니다.

---

## KooChainRun `REMAP` 체인 스텝 사용법

시뮬레이션 체인의 전처리(재료 교체·메시 리매핑)로 삽입한다. 러너(`CumulativeScenarioRunner`)가
입력 모델(이전 스텝의 `*_dti.k`, 없으면 `project.model_file`)을 받아 KooRemapper 를 실행하고,
결과를 `Run_<id>/Output/Remap_dti.k` 로 써서 기존 `*_dti.k` 누적 규약으로 **다음 스텝에 자동 연결**한다.

`runner_config.json` 의 스텝/환경 스키마.

```json
{
  "environment": {
    "kooremapper_path": "/opt/kooremapper/bin/KooRemapper"
  },
  "scenario": {
    "steps": [
      {
        "step": 1,
        "mode": "REMAP",
        "condition": "remap",
        "params": {
          "op": "matdb",
          "config": {
            "materials": [
              {"match": "AL7003H", "mat_type": "MAT_PIECEWISE_LINEAR_PLASTICITY"},
              {"match": "OCA Rigid Standard", "mat_type": "MAT_VISCOELASTIC"},
              {"match": "*"}
            ]
          }
        }
      }
    ]
  }
}
```

- `params.op`: 실행할 op(예: `matdb`).
- `params.config`: yaml-config ops 용 설정 dict. `model`/`output` 은 러너가 자동 주입(입력 모델 → `Remap_dti.k`).
  `matdb` 에서 `database` 생략 시 번들 DB(`/opt/kooremapper/materials/material_db.json`) 자동 사용.
- `params.argv`: positional ops 용 인자 리스트(예: `map` → `["bent.k","flat.k","out.k"]`). `config` 대신 사용.
- `environment.kooremapper_path`: sif 내부 바이너리 경로. 생략 시 기본값(위 경로)으로 자동 탐색.

> 경계: `REMAP` 스텝은 `runner_config.json` 의 `scenario.steps` 에 직접 기술한다. `scenario.json` →
> `runner_config.json` 변환(CumulativeDesigner)의 DOE/각도 자동생성 파이프라인은 낙하/충격/열/진동
> 전용이며, REMAP(비-DOE 변환)은 이 자동생성 대상이 아니다. 환경 경로 주입(`kooremapper_path`)은 자동 처리된다.

---

## 독립 CLI 사용 예

```bash
# 재료 교체 (yaml-config op)
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper matdb job.yaml

# 메시 매핑 (positional op)
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper map bent.k flat.k out.k

# 모델 정보
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper info model.k
```

`matdb` 의 `job.yaml` 예.

```yaml
model: model.k
output: mapped.k
database: /opt/kooremapper/materials/material_db.json
materials:
  - match: AL7003H
    mat_type: MAT_PIECEWISE_LINEAR_PLASTICITY
  - match: "*"
```
