# 통합 조합 가이드 — 5개 도구로 CAE 시나리오 구성하기

SmartTwinPreprocessor(pyKooCAE)의 도구들을 **하나의 파이프라인으로 엮어** 모델 생성부터
대량 해석·후처리까지 자동화하는 방법을 정리한다. 각 도구의 개별 기능은 해당 매뉴얼
(`01_KooChainRun` ~ `04_KooRemapper`)을 참조하고, 이 문서는 **어떻게 조합하느냐**에 집중한다.

> 근거: `01_KooChainRun/README.md`(커맨드 맵·워크플로우), `04_KooRemapper/`(op 레퍼런스),
> 실측 config `Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick/scenario.json`,
> `Examples/KooRemapper/remap_step/runner_config.template.json`.

---

## 1. 5개 도구와 역할

| 도구 | 역할 | 입력 → 출력 | 상세 |
|------|------|-----------|------|
| **KooAutomatedModeller** (KAM) | CAD/ECAD(ODB++)·정의파일 → 형상 자동 생성 + FEA 메시 | ODB++/정의 → `.k` + STEP | [03_KooAutomatedModeller](../03_KooAutomatedModeller/README.md) |
| **KooMeshModifier** (KMM) | `.k` 모델 변형 엔진(낙하 자세·메시 연산·재료/파트 교체·DOE·하중) | `.k` + 제어 `.txt` → 변형된 `.k` | [02_KooMeshModifier](../02_KooMeshModifier/README.md) |
| **KooRemapper** (KR) | `.k` 메쉬·재료 리매핑 CLI(47 op). 재료 DB 교체·메시 매핑·어셈블리 등 | `.k`(+YAML) → 변환된 `.k` | [04_KooRemapper](../04_KooRemapper/README.md) |
| **KooChainRun** (KCR) | 오케스트레이션. 시나리오 준비 → Slurm 제출 → 상태/재실행 → 후처리 | `scenario.json` → 대량 잡 → 결과/리포트 | [01_KooChainRun](../01_KooChainRun/README.md) |
| **KooDynaPostProcessor** | 후처리 엔진(deep/sphere/impact 리포트 생성). KCR `postprocess`가 호출 | d3plot → 리포트 HTML | [후처리 가이드](../01_KooChainRun/postprocess/postprocess.md) |

이 다섯은 **호출 계층이 두 층**이다.

- **엔진 도구**(KAM · KMM · KR · KooDynaPostProcessor) — 각각 독립 CLI. `apptainer exec <sif> <바이너리>` 로 단독 실행 가능.
- **오케스트레이터**(KCR) — 위 엔진들을 시나리오/스텝 규약에 따라 compute node에서 순차 호출한다.

---

## 2. 표준 파이프라인 (데이터 흐름)

```
KooAutomatedModeller        KooMeshModifier / KooRemapper        KooChainRun               KooDynaPostProcessor
(CAD/ECAD → .k, STEP)  →   (.k 변형: 자세·메시·재료·하중)   →   (DOE 생성 → Slurm 대량 실행)  →  (deep/sphere/impact 리포트)
     [모델 준비]                    [전처리]                          [해석 오케스트레이션]            [후처리]
                                        │                                   │
                                        └── KR: REMAP 스텝으로 체인에 삽입      └── KCR postprocess 가 자동 호출
```

각 compute node의 단일 DOE 파이프라인은 KCR이 다음 순서로 돌린다(근거: `01_KooChainRun/README.md §1`).

```
KooMeshModifier(변형/REMAP=KooRemapper) → LS-DYNA(솔브) → dynain(결과) → 다음 step 초기조건
```

즉 **전처리 도구(KMM·KR)는 KCR 스텝 안에서 호출**되고, 해석 후 `dynain`이 다음 스텝으로 누적된다.

---

## 3. 2계층 구성 모델 — scenario.json vs runner_config.json

KCR은 사용자 친화 입력(`scenario.json`)을 상세 실행 설정(`runner_config.json`)으로 변환한다.

```
scenario.json  ──(KooChainRun prepare, CumulativeDesigner)──▶  runner_config.json  ──(submit)──▶  Slurm 잡
[사람이 쓴다]                                                    [러너가 읽는다]
```

- **`scenario.json`** — DOE(각도/위치/치수) 자동생성 규칙을 간결히 기술한다. 낙하/충격/열/진동 시나리오에 적합.
- **`runner_config.json`** — 스텝을 명시적으로 나열한다. **REMAP(KooRemapper) 스텝은 이 계층에 직접 기술**한다(§5-2 참조).

### 3-1. scenario.json 골격 (실측 발췌)

`Test_010_Sequential_Quick/scenario.json` 근거.

```json
{
  "project_name": "Test_010_Sequential_Quick",
  "environment": {
    "koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "koochainrun_path": "/data/SmartTwinPreprocessor/bin/KooChainRun",
    "ncpu": 1, "time_limit": "01:00:00", "partition": "viz"
  },
  "simulation_params": { "height": 1500, "tFinal": 0.005, "dt": 1e-06 },
  "scenarios": [
    {
      "scenario_name": "Sequential_Quick_10",
      "template": "MinimumModel.k",
      "angle_source": { "source_type": "fibonacci_lattice",
                        "fibonacci_lattice": { "num_directions": 10 } },
      "cumulative": { "num_steps": 1, "mode_sequence": ["DROP"] }
    }
  ]
}
```

- `angle_source` / DOE 소스: `fibonacci_lattice`·`grid`·`lhs`·`part_center`·`spacing` 등
  (상세 [doe_methods.md](../01_KooChainRun/doe_methods/doe_methods.md)).
- `cumulative.mode_sequence`: 스텝별 모드 배열(예: `["DROP"]`, `["DROP","DROP"]` 다단 낙하).
- 전체 키 레퍼런스: [scenario_reference.md](../01_KooChainRun/scenarios/scenario_reference.md).

---

## 4. 스텝 모드 지도

`runner_config.json` 의 각 step은 `mode` 를 가진다. 모드는 두 갈래다.

| 갈래 | 모드 | 구성 방식 | 담당 엔진 |
|------|------|-----------|-----------|
| **DOE 자동생성** | `DROP` · `IMPACT` · `THERM` · `VIBRATION` | `scenario.json` 의 `angle_source`/`simulation_params`로 CumulativeDesigner가 자동 전개 | KooMeshModifier |
| **명시 스텝** | `REMAP` | `runner_config.json` 의 `scenario.steps`에 직접 기술(비-DOE 변환) | KooRemapper |

> 경계(의도적): `scenario.json → runner_config.json` 자동생성은 DROP/IMPACT/THERM/VIBRATION 전용이다.
> REMAP(재료 교체·메시 리매핑 같은 비-DOE 전처리)은 자동 DOE 대상이 아니므로 `runner_config.json` 에
> 스텝으로 직접 넣는다(근거: `04_KooRemapper/README.md`).

---

## 5. KooRemapper를 체인에 삽입하기 (REMAP 스텝)

KooRemapper의 전처리(재료 DB 교체·메시 리매핑·어셈블리 등)를 시뮬레이션 체인의 한 스텝으로 넣는 방법이다.

### 5-1. 동작

러너(`CumulativeScenarioRunner._run_kooremapper_step`)가 입력 모델(이전 스텝의 `*_dti.k`,
없으면 `project.model_file`)을 받아 KooRemapper를 실행하고, 결과를 `Run_<id>/Output/Remap_dti.k` 로
써서 기존 `*_dti.k` 누적 규약으로 **다음 스텝에 자동 연결**한다. LS-DYNA 솔브는 없다.

### 5-2. runner_config.json 스텝 스키마 (실측 근거)

`Examples/KooRemapper/remap_step/runner_config.template.json` 발췌.

```json
{
  "scenario": {
    "type": "cumulative",
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
  },
  "environment": {
    "kooremapper_path": "/opt/kooremapper/bin/KooRemapper"
  }
}
```

- `params.op` — 실행할 KooRemapper op(예: `matdb`). 전체 47 op는 [04_KooRemapper](../04_KooRemapper/README.md).
- `params.config` — **yaml-config op**용 설정 dict. `model`/`output` 은 러너가 자동 주입(입력 모델 → `Remap_dti.k`).
- `params.argv` — **positional op**용 인자 리스트(예: `map` → `["bent.k","flat.k","out.k"]`). `config` 대신 사용.
- `environment.kooremapper_path` — sif 내부 바이너리 경로. 생략 시 기본값으로 자동 탐색(`PathResolver.find_kooremapper()`).

> op가 yaml-config형인지 positional형인지는 `04_KooRemapper/ops/` 각 페이지의 호출형태(바이너리 `Usage`)로 확인한다.

---

## 6. 누적(cumulative) 체인 — 여러 스텝 엮기

여러 전처리·해석 스텝을 하나의 케이스로 잇는 규약이다.

- 각 스텝은 결과를 `*_dti.k`(변형된 초기조건 데크)로 남기고, **다음 스텝이 이를 입력으로 받는다**.
- REMAP 스텝은 `Remap_dti.k`, 낙하/충격 스텝은 dynain→`DYNAIN_TO_INITIAL` 변환으로 누적된다.
- `scenario.cumulative.num_steps` / `mode_sequence` 로 스텝 수와 순서를 정한다.

전형적 조합 순서(예).

```
step1  REMAP(KooRemapper matdb)     재료를 실물 DB로 교체        → Remap_dti.k
step2  DROP(KooMeshModifier)        낙하 자세·바닥판·초기속도 부여 → 솔브 → dynain
step3  DROP(KooMeshModifier)        이전 dynain 누적 후 2차 낙하   → 솔브 → dynain
postprocess  KooDynaPostProcessor   deep/sphere 리포트            → *.html
```

---

## 7. 조합 레시피 (자주 쓰는 시나리오)

각 레시피는 개별 도구 문서의 세부로 연결된다. 명령은 sif 내부 경로 기준이다.

### 7-1. 재료 교체 후 전각도 낙하
1. `REMAP`/`matdb` 로 번들 525-DB 재료 치환([material_assembly.md](../04_KooRemapper/ops/material_assembly.md)).
2. `DROP` + `angle_source: fibonacci_lattice` 로 전각도 DOE([full_angle_drop.md](../01_KooChainRun/examples/full_angle_drop.md)).
3. `KooChainRun submit --sequential` → `postprocess --sphere`(sphere 종합 리포트).

### 7-2. 전위치 부분충격
1. (선택) `REMAP` 전처리.
2. `IMPACT` + `angle_source: part_center`/`grid` 로 위치 DOE([partial_impact.md](../01_KooChainRun/examples/partial_impact.md)).
3. `submit` → `postprocess --impact`.

### 7-3. CAD부터 시작(모델 자동 생성)
1. KooAutomatedModeller로 PKG/PBA/PCB 형상 → `.k`([03_KooAutomatedModeller](../03_KooAutomatedModeller/README.md)).
2. KMM/KR로 전처리(자세·재료), 이후 KCR DOE.

### 7-4. KooRemapper 단독(체인 없이)
```bash
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper matdb job.yaml     # yaml-config op
apptainer exec SmartTwinPreprocessor.sif /opt/kooremapper/bin/KooRemapper map bent.k flat.k out.k   # positional op
```

---

## 8. 도구·경로 레지스트리 (environment 키)

`scenario.json`/`runner_config.json` 의 `environment` 에 도구 경로를 둔다. 배포 sif 기준 기본값.

| 키 | 기본 경로 | 도구 |
|----|-----------|------|
| `koomeshmodifier_path` | `/opt/SmartTwinPreprocessor/bin/KooMeshModifier` | KMM |
| `kooremapper_path` | `/opt/kooremapper/bin/KooRemapper` | KR(REMAP 스텝) |
| `koochainrun_path` | `/data/SmartTwinPreprocessor/bin/KooChainRun` | KCR(compute node 재호출) |
| `lsdyna_path` | (환경별) 예: `/opt/ls-dyna/lsdyna_R16.1.1` | 솔버 |
| `apptainer_sif` | 배포 sif 경로 | 컨테이너 |

> KooAutomatedModeller·KooDynaPostProcessor는 KCR의 후처리/모델 단계에서 각각 별도 경로/스크립트로
> 호출된다(후처리는 `postprocess` 커맨드가 `Run_*/deep_report.sh` 등을 실행 — `01_KooChainRun/README.md §4-2`).

---

## 9. 어디서 무엇을 보나 (링크 맵)

| 하고 싶은 것 | 볼 문서 |
|-------------|---------|
| 전체 커맨드·워크플로우 | [01_KooChainRun/README.md](../01_KooChainRun/README.md) |
| scenario.json 키 전체 | [scenario_reference.md](../01_KooChainRun/scenarios/scenario_reference.md) |
| DOE(각도/위치) 생성법 | [doe_methods.md](../01_KooChainRun/doe_methods/doe_methods.md) |
| `.k` 변형 모드(낙하·메시·하중) | [02_KooMeshModifier/README.md](../02_KooMeshModifier/README.md) |
| 형상 자동 생성(CAD/ECAD) | [03_KooAutomatedModeller/README.md](../03_KooAutomatedModeller/README.md) |
| KooRemapper op별 레퍼런스 | [04_KooRemapper/README.md](../04_KooRemapper/README.md) + `ops/` |
| 후처리(deep/sphere/impact) | [postprocess.md](../01_KooChainRun/postprocess/postprocess.md) |

---

## 10. 주의 · 경계

- **NFS 공유 경로 필수** — submit이 만든 잡 스크립트는 compute node에서 config/output_dir를 다시 읽으므로
  `/data/...` 같은 공유 경로에 둔다(`/tmp` 로컬 금지, `01_KooChainRun/README.md §5`).
- **단위계 일치** — `simulation_params`(density/E/속도/높이 등)는 변환 없이 데크에 기록되므로 모델 `.k`
  단위계(예: ton-mm-s)와 반드시 일치시킨다(`02_KooMeshModifier/modes/drop_impact/DROP_ATTITUDE.md §5`).
- **REMAP은 자동 DOE 대상 아님** — REMAP 스텝은 `runner_config.json` 에 직접 기술한다(§4, §5).
- **후처리 스크립트 의존** — `sphere_report.sh`/`impact_report.sh` 는 prepare 시 postprocess 옵션이 있어야
  자동 생성된다. 없으면 `postprocess` 가 경고만 하고 건너뛴다(`01_KooChainRun/README.md §5`).
- **부분구현 주의** — KCR `status` 상세 진행률, `collect` 기본 경로는 부분구현이다(진행률은 `squeue`/`rerun`으로 확인).
