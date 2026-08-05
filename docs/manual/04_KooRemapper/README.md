# KooRemapper — `.k` 메쉬·재료 리매핑 CLI (op 카탈로그)

LS-DYNA 키워드(`.k`) 모델의 **메쉬·재료를 변환·리매핑**하는 C++ CLI 도구(v1.8.0, 46 op).
위 3개(Nuitka) 도구와 달리 독립 C++ 바이너리이며, `SmartTwinPreprocessor.sif` 내부에
네이티브 바이너리(`/opt/kooremapper/bin/KooRemapper`)로 구워져 KooMeshModifier 와 동일하게
`apptainer exec <sif> <바이너리>` 로 호출된다. KooChainRun 시나리오의 `REMAP` 스텝으로
삽입하거나 독립 CLI 로도 실행한다.

- 코드: `Runner/KooRemapperStep.py`(모듈 래퍼), `Runner/CumulativeScenarioRunner.py`(`_run_kooremapper_step`, REMAP 스텝 실행)
- 빌드 반영: `serviceApptainers/BuildSmartTwinPreprocessor.sh` 의 KooRemapper 복사 단계(재빌드 시 sif 에 상주)
- 경로 탐색: `Runner/PathResolver.py:find_kooremapper()`

---

## 호출 규약

두 가지 인자 형태로 46개 op를 모두 호출한다.

| 형태 | 예 | 대상 op |
|------|----|---------|
| yaml ops | `KooRemapper matdb config.yaml` | matdb, warpage, assemble, battery, tetremesh, meshfix, merge, strip, cnrb2solid, hfdamp 등 (config.yaml 필요) |
| positional ops | `KooRemapper map bent.k flat.k out.k` | map, generate, info, extract-surface 등 (위치 인자) |

> 각 op는 필요한 **입력 파일이 작업 디렉토리에 있어야** 한다(CLI 특성). REMAP 스텝은 이를 자동 준비한다.

---

## op 카탈로그 (46 op, 카테고리별)

| 카테고리 | op |
|----------|----|
| 재료 | `matdb` (525-DB 일괄 교체), `matswap` |
| 메시 생성 | `generate`, `generate-var` |
| 메시 매핑 | `map`, `shellmap`, `unfold` |
| 메시 편집 | `refine`, `elform`, `disconnect`, `offset`, `wrap`, `convert`, `restack`, `update`, `iga` |
| 표면/재메시 | `extract-surface`, `tetremesh`, `meshfix`, `cnrb2solid`, `merge`, `strip` |
| 변형/전처리 | `strain`, `prestress`, `formstrain`, `warpage`, `bend`, `indent`, `squeeze`, `assemble`, `cclip` |
| 하중/경계/접촉 | `load`, `boundary`, `rbe`, `contact`, `relax`, `stabilize`, `database`, `hfdamp` |
| 솔버 제어 | `explicit`, `implicit`, `modal`, `ale`, `optimize`, `battery` |
| 정보 | `info`, `version` |

> `battery, cnrb2solid, extract-surface, hfdamp, merge, strip, tetremesh, meshfix` 8개는 바이너리
> `--help` 최상위 목록엔 안 뜨지만 정상 동작한다(각자 Usage 출력). 전 46 op가 sif 내부 바이너리에서 호출 가능.

---

## KooChainRun `REMAP` 체인 스텝 사용법

시뮬레이션 체인의 전처리(재료 교체·메시 리매핑)로 삽입한다. 러너(`CumulativeScenarioRunner`)가
입력 모델(이전 스텝의 `*_dti.k`, 없으면 `project.model_file`)을 받아 KooRemapper 를 실행하고,
결과를 `Run_<id>/Output/Remap_dti.k` 로 써서 기존 `*_dti.k` 누적 규약으로 **다음 스텝에 자동 연결**한다.

`runner_config.json` 의 스텝/환경 스키마:

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
- `params.config`: yaml ops 용 설정 dict. `model`/`output` 은 러너가 자동 주입(입력 모델 → `Remap_dti.k`).
  `matdb` 에서 `database` 생략 시 번들 DB(`/opt/kooremapper/materials/material_db.json`) 자동 사용.
- `params.argv`: positional ops 용 인자 리스트(예: `map` → `["bent.k","flat.k","out.k"]`). `config` 대신 사용.
- `environment.kooremapper_path`: sif 내부 바이너리 경로. 생략 시 기본값(위 경로)으로 자동 탐색.

> 경계: `REMAP` 스텝은 `runner_config.json` 의 `scenario.steps` 에 직접 기술한다. `scenario.json` →
> `runner_config.json` 변환(CumulativeDesigner)의 DOE/각도 자동생성 파이프라인은 낙하/충격/열/진동
> 전용이며, REMAP(비-DOE 변환)은 이 자동생성 대상이 아니다. 환경 경로 주입(`kooremapper_path`)은 자동 처리된다.

---

## 독립 CLI 사용 예

```bash
# 재료 교체 (yaml op)
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper matdb job.yaml

# 메시 매핑 (positional op)
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper map bent.k flat.k out.k

# 모델 정보
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper info model.k
```

`matdb` 의 `job.yaml` 예:

```yaml
model: model.k
output: mapped.k
database: /opt/kooremapper/materials/material_db.json
materials:
  - match: AL7003H
    mat_type: MAT_PIECEWISE_LINEAR_PLASTICITY
  - match: "*"
```
