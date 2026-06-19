# 후처리 자동화 (deep / sphere / impact)

## 1. 목적 / 개요

KooChainRun 의 후처리 파이프라인은 LS-DYNA 시뮬레이션 결과(`d3plot`)를 KooD3plotReader 기반 SIF(`SmartTwinPostprocessor.sif`)로 분석하여 리포트를 생성한다. `scenario.json` 의 `postprocess` 블록 하나로 다음 3단계가 자동화된다.

- **per-job deep_report** — 각 시뮬 케이스(`Run_*/Output/`)의 d3plot 을 단건 분석. `koo_deep_report` 호출 (Runner/PostprocessShellGenerator.py:57-131).
- **aggregate sphere_report** — DROP(전각도 낙하) 시나리오 전 케이스 통합. `koo_sphere_report` 호출 (Runner/PostprocessShellGenerator.py:134-228).
- **aggregate impact_report** — IMPACT(전위치 부분충격) 시나리오 전 케이스 통합. `koo_impact_report` 호출 (Runner/PostprocessShellGenerator.py:231-297).

핵심 설계 원칙(Runner/PostprocessShellGenerator.py:11-23):

- 후처리 sh 스크립트는 `postprocess.enabled` 와 무관하게 **prepare 시점에 항상 생성**된다. 따라서 자동 실행을 끄거나 SIF 미배포 환경이어도 나중에 수동(`KooChainRun postprocess ...`)으로 trigger 할 수 있다.
- `enabled=true` 이고 해당 `auto_*` 플래그가 켜져 있을 때만 자동 실행된다.
- 종합 리포트는 **DROP→sphere, IMPACT→impact** 로 mode 라우팅되며 **둘 다 돌지 않는다** (Runner/PostprocessShellGenerator.py:8-9, SlurmSubmitter.py:106-108). 과거에는 `auto_sphere` 만 검사해 IMPACT 데이터에도 sphere 가 도는 버그가 있었다.

`postprocess` 키가 아예 없으면 후처리 sh 생성조차 하지 않는다 → 기존 KooChainRun 동작과 동일(회귀 무영향) (Runner/CumulativeScenarioRunner.py:687-689, CumulativeDesigner.py:875).

---

## 2. 입력 옵션 · 인자 (표)

`scenario.json` 의 `postprocess` 블록 키 전체. default 와 코드 근거를 함께 표기한다.

### 2.1 마스터 토글 / 라우팅

| 옵션 | 형식 | default | 의미 | 코드 근거 |
|---|---|---|---|---|
| `enabled` | bool | `false` (키 없을 때 truthy 검사) | 마스터 토글. false 면 자동 실행 안 함 (sh 만 생성). | CumulativeScenarioRunner.py:708, SlurmSubmitter.py:112 |
| `auto_deep` | bool | `true` | `enabled=true` 시 각 시뮬 직후 deep_report 자동 실행. | CumulativeScenarioRunner.py:708 |
| `auto_deep_mode` | str | `"inline"` | `"inline"` / `"separate_job"`. deep_report 실행 방식. | CumulativeScenarioRunner.py:711-714 |
| `auto_sphere` | bool | `true` | DROP 시나리오에서 종합 리포트(sphere) dependent job 제출. | SlurmSubmitter.py:132 |
| `auto_impact` | bool | `true` | IMPACT 시나리오에서 종합 리포트(impact) dependent job 제출. | SlurmSubmitter.py:126 |

> mode 판정은 `report_mode_from_runner_config()` 가 담당한다. `runner_config["scenario"]["steps"][].mode` 가 모두 IMPACT → `"IMPACT"`, 모두 DROP → `"DROP"`, mixed → 첫 step mode, 비어있으면 `doe_positions`(IMPACT) vs `doe_angles`(DROP) fallback, 그것도 없으면 `"DROP"` (Runner/PostprocessShellGenerator.py:300-327).

### 2.2 deep_report 콘텐츠 옵션

| 옵션 | default | 의미 | 코드 근거 |
|---|---|---|---|
| `section_view_axes` | `["z"]` | 단면뷰 축 (`--section-view-axes`). | PostprocessShellGenerator.py:77,124 |
| `section_view_fields` | `["von_mises"]` | 시각화 필드 (`--section-view-fields`). | PostprocessShellGenerator.py:78,125 |
| `section_view_mode` | `"section"` | `"section"` / `"section_3d"` / `"iso_surface"`. | PostprocessShellGenerator.py:79,123 |
| `ua_threads` | `8` | unified_analyzer threads (`--ua-threads`). | PostprocessShellGenerator.py:80,126 |
| `sv_threads` | `8` | section view 렌더 threads (`--sv-threads`). | PostprocessShellGenerator.py:81,127 |
| `delete_d3plot_after_deep` | `false` | deep_report **성공 시에만** `Run_*/Output/d3plot*` 삭제 (디스크 절약). | PostprocessShellGenerator.py:93-100 |

### 2.3 종합 리포트 콘텐츠 옵션

| 옵션 | default | 적용 대상 | 의미 | 코드 근거 |
|---|---|---|---|---|
| `yield_stress_mpa` | `350` | sphere | 안전계수 계산 기준 (`--yield-stress`, MPa). | PostprocessShellGenerator.py:159,225 |
| `impact_yield_stress` | 없음(미부착) | impact | 있으면 `--yield-stress` 부착, 없으면 per-part *MAT 카드 사용. sphere 의 `yield_stress_mpa` 를 재사용하지 않음. | PostprocessShellGenerator.py:257-260 |

### 2.4 임의 인자 pass-through (extra_args)

각 리포트의 고정 플래그 **뒤에** 그대로 추가되므로 argparse "마지막 우선" 으로 기본값 override 가능. 값은 JSON 리스트(권장) 또는 공백 구분 문자열 (PostprocessShellGenerator.py:16-23, 37-54).

| 옵션 | 적용 대상 | 코드 근거 |
|---|---|---|
| `deep_extra_args` | koo_deep_report | PostprocessShellGenerator.py:86-87 |
| `sphere_extra_args` | koo_sphere_report | PostprocessShellGenerator.py:161-162 |
| `impact_extra_args` | koo_impact_report | PostprocessShellGenerator.py:262-263 |

### 2.5 Slurm 리소스 옵션 (separate_job + 종합 리포트 잡)

미지정 시 `environment` 블록 동명 키 → 기본값으로 fallback (시뮬 환경과 자동 일치).

| 옵션 | fallback 체인 | 대상 잡 | 코드 근거 |
|---|---|---|---|
| `deep_ncpu` | `environment.ncpu` → `1` | deep (separate_job) | PostprocessShellGenerator.py:350 |
| `deep_memory` | `environment.memory` → `"8G"` | deep (separate_job) | PostprocessShellGenerator.py:351 |
| `deep_partition` | `environment.partition` → `""` | deep (separate_job) | PostprocessShellGenerator.py:352 |
| `deep_timeout_seconds` | `7200` (2h) | inline=subprocess timeout, separate_job=time-limit base | CumulativeScenarioRunner.py:723; PostprocessShellGenerator.py:353 |
| `deep_time_limit` | `(timeout_seconds + 600)` 자동 산정 | deep (separate_job) | PostprocessShellGenerator.py:354 |
| `sphere_ncpu` | `env.sphere_ncpu` → `env.ncpu` → `8` | sphere | PostprocessShellGenerator.py:399 |
| `sphere_memory` | `env.sphere_memory` → `env.memory` → `"16G"` | sphere | PostprocessShellGenerator.py:400 |
| `sphere_partition` | `env.partition` → `""` | sphere | PostprocessShellGenerator.py:401 |
| `sphere_time_limit` | `env.sphere_time_limit` → `"04:00:00"` | sphere | PostprocessShellGenerator.py:402 |
| `impact_ncpu` | `env.impact_ncpu` → `env.ncpu` → `8` | impact | PostprocessShellGenerator.py:441 |
| `impact_memory` | `env.impact_memory` → `env.memory` → `"16G"` | impact | PostprocessShellGenerator.py:442 |
| `impact_partition` | `env.partition` → `""` | impact | PostprocessShellGenerator.py:443 |
| `impact_time_limit` | `env.impact_time_limit` → `"04:00:00"` | impact | PostprocessShellGenerator.py:444 |

### 2.6 인프라

| 옵션 | default | 의미 | 코드 근거 |
|---|---|---|---|
| `sif_path` | `/opt/apptainers/SmartTwinPostprocessor.sif` | compute node SIF 절대경로. | PostprocessShellGenerator.py:28,75,157,255 |

---

## 3. 사용 예제

### 3.1 표준 DROP 파이프라인 (inline, sphere)

`Examples/postprocess_pipeline/scenario_with_postprocess.json` 의 `postprocess` 블록 (발췌):

```json
"postprocess": {
  "enabled": true,
  "auto_deep": true,
  "auto_sphere": true,
  "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
  "yield_stress_mpa": 350,
  "section_view_axes": ["z"],
  "section_view_fields": ["von_mises"],
  "section_view_mode": "section",
  "ua_threads": 8,
  "sv_threads": 8,
  "deep_timeout_seconds": 7200,
  "sphere_memory": "32G",
  "sphere_time_limit": "04:00:00"
}
```

각 시뮬 잡 안에서 deep_report 가 inline 실행되고, 모든 시뮬 종료 후 sphere_report 가 dependent job 으로 제출된다.

### 3.2 대규모 separate_job (deep 별도 잡, sphere)

`Examples/postprocess_pipeline/scenario_with_postprocess_separate_job.json` (발췌):

```json
"postprocess": {
  "enabled": true,
  "auto_deep": true,
  "auto_deep_mode": "separate_job",
  "auto_sphere": true,
  "deep_ncpu": 4,
  "deep_memory": "8G",
  "deep_time_limit": "02:00:00",
  "sphere_memory": "32G",
  "sphere_time_limit": "04:00:00"
}
```

시뮬 노드를 즉시 해방하므로 큐 회전이 빠르다. deep_report 는 별도 sbatch 잡으로 제출되고 잡 ID 가 `output/deep_report_jobs.txt` 에 기록된다 (CumulativeScenarioRunner.py:759-761).

### 3.3 IMPACT 파이프라인 (impact, d3plot 삭제)

`Examples/scenario_examples/impact_cylinder_8pi.json` 의 `postprocess` 블록 (전체):

```json
"postprocess": {
  "enabled": true,
  "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
  "auto_deep": true,
  "auto_deep_mode": "inline",
  "delete_d3plot_after_deep": true,
  "auto_impact": true
}
```

scenario step mode 가 IMPACT 이므로 종합 리포트는 sphere 가 아닌 impact 로 라우팅된다. deep_report 성공 후 d3plot 이 삭제되어 디스크를 절약한다.

### 3.4 수동 실행 (CLI)

자동 실행을 끄거나 fail 시, `prepare` 로 생성된 sh 를 수동 trigger 한다 (KooChainRun:303-318).

```bash
# deep 전부 + scenario mode 에 맞는 종합 리포트 (--all 또는 무플래그)
KooChainRun postprocess <runner_config.json> --all

# deep만 (각 Run_*/deep_report.sh)
KooChainRun postprocess <runner_config.json> --deep

# sphere만 (DROP), impact만 (IMPACT)
KooChainRun postprocess <runner_config.json> --sphere
KooChainRun postprocess <runner_config.json> --impact
```

> CLI 커맨드 자체의 상세 인자는 `commands/postprocess.md` 참조.

---

## 4. 동작 원리 (코드 근거)

### 4.1 prepare 시점 — sh 항상 생성

- `CumulativeDesigner.create_runner_config()` 가 `runner_config.postprocess` 가 있으면 `output_dir` 에 `sphere_report.sh` 와 `impact_report.sh` 를 **둘 다 항상** 생성한다 (`enabled` 무관) (Runner/CumulativeDesigner.py:871-907). 어느 것이 실제 실행될지는 mode 라우팅이 결정한다.
- per-job `deep_report.sh` 는 시뮬 실행 시점(`run_simulation`)에 생성된다 (아래 4.2).

### 4.2 per-job deep_report

- `CumulativeScenarioRunner._generate_and_maybe_run_deep_report()` 가 핵심 (Runner/CumulativeScenarioRunner.py:678-728), `run_simulation` 의 6.5 단계에서 호출된다 (CumulativeScenarioRunner.py:1105-1107).
- 동작 순서:
  1. `postprocess` 키 없으면 즉시 return (CumulativeScenarioRunner.py:687-689).
  2. `build_deep_report_sh()` 로 `run_dir/deep_report.sh` 생성 + `chmod 755` (CumulativeScenarioRunner.py:691-702).
  3. `enabled` 와 `auto_deep`(default true) 둘 다 truthy 일 때만 자동 실행 (CumulativeScenarioRunner.py:708).
  4. `auto_deep_mode` 분기 (CumulativeScenarioRunner.py:711-714):
     - `"separate_job"` → `_submit_deep_report_sbatch()` (별도 sbatch, CumulativeScenarioRunner.py:730-763).
     - 그 외(inline) → `subprocess.run(["bash", sh_path])`, `deep_timeout_seconds` 적용, 로그는 `run_dir/deep_report.log` (CumulativeScenarioRunner.py:715-728).
- 생성되는 sh 는 `apptainer exec ... python3 -m koo_deep_report "$RUN_DIR" -o "$REPORT_DIR" --section-view ...` 이며 `set -e` 로 묶여 있다 (PostprocessShellGenerator.py:102-131).

### 4.3 d3plot 삭제 (delete_d3plot_after_deep)

- `delete_d3plot_after_deep=true` 면 deep_report.sh 끝에 cleanup 블록이 추가된다 (PostprocessShellGenerator.py:93-100).
- sh 가 `set -e` 라서 `koo_deep_report` 가 성공해 cleanup 줄에 도달했을 때만 `rm -f "$RUN_DIR"/d3plot "$RUN_DIR"/d3plot[0-9]*` 가 실행된다 → **deep 실패 시 d3plot 보존** (PostprocessShellGenerator.py:88-92).
- `report/`(analysis_result.json + motion 등)는 보존되며, impact aggregate 는 이를 재사용한다 (PostprocessShellGenerator.py:91-92).

### 4.4 aggregate 종합 리포트 — mode 라우팅 + dependent job

- prepare 직후 자동 제출 경로: `SlurmSubmitter._maybe_submit_sphere_job()` 가 모든 시뮬 잡 제출 후 호출된다 (Runner/SlurmSubmitter.py:99, 103-175).
  - `enabled` 아니면 skip (SlurmSubmitter.py:112-113).
  - `report_mode_from_runner_config()` 로 mode 판정 (SlurmSubmitter.py:124).
  - IMPACT → `auto_impact` 확인 후 `build_impact_sbatch` / `impact_report.sbatch` (SlurmSubmitter.py:125-130).
  - DROP → `auto_sphere` 확인 후 `build_sphere_sbatch` / `sphere_report.sbatch` (SlurmSubmitter.py:131-136).
  - 모든 시뮬 잡 ID 를 `--dependency=afterany:<...>` 로 묶어 제출 (SlurmSubmitter.py:142, 149-173; sbatch 빌더 PostprocessShellGenerator.py:405-407, 447-449).
- 수동 경로: `cmd_postprocess()` 가 동일 `report_mode_from_runner_config()` 로 라우팅 (KooChainRun:2557-2571). `--all`/무플래그면 `do_impact=(report_mode=="IMPACT")`, `do_sphere=not do_impact` (KooChainRun:2568-2571).

### 4.5 sphere_report 내부 (normal termination 필터)

- `sphere_report.sh` 는 `test_dir = output_dir 의 parent` 로 잡고, `output_dir/Run_*/Output/{mes0000,d3hsp,*.log}` 에서 `"N o r m a l    t e r m i n a t i o n"` 을 grep 하여 정상 종료 케이스만 통과시킨다 (PostprocessShellGenerator.py:170-199).
- 정상 종료 + deep_report 완료(`result.json` 또는 `analysis_result.json` 존재) 케이스만 `analysis_results/<Run_*>` 로 symlink, 0개면 에러 종료 (PostprocessShellGenerator.py:200-217).
- 정상 목록은 `output_dir/sphere_normal_term.txt` 에 기록 (PostprocessShellGenerator.py:178,199).

### 4.6 impact_report 내부

- sphere 보다 단순하다: `koo_impact_report` 의 flat-DOE 로더가 Run 마다 내부에서 unified_analyzer 를 직접 실행하므로 analysis_results symlink dance 가 불필요하고, normal-termination 사전 필터도 v1 에서는 생략(로더가 깨진 Run 을 자체 skip) (PostprocessShellGenerator.py:234-238).
- 구버전 SIF soft-degrade: SIF 에 `koo_impact_report` 가 없으면(2.3.x 이전) 경고 후 `exit 0` 으로 skip (PostprocessShellGenerator.py:282-286).
- `apptainer exec ... python3 -m koo_impact_report --test-dir "$TEST_DIR" --format html json --output ... --json ...` 실행 (PostprocessShellGenerator.py:288-294).

---

## 5. 주의사항 · 한계

- **종합 리포트는 mode 당 하나만 실행된다.** mixed mode 시나리오는 `report_mode_from_runner_config()` 가 첫 step mode 를 채택하므로(PostprocessShellGenerator.py:323), 혼합 시나리오에서는 한쪽 리포트만 생성된다 — 의도된 동작.
- **sphere 는 deep_report 선행 필수.** deep_report 완료 케이스가 0개면 sphere 는 에러 종료하며 "KooChainRun postprocess --deep 먼저 실행" 힌트를 출력한다 (PostprocessShellGenerator.py:211-217).
- **`delete_d3plot_after_deep` 는 deep 성공 시에만 삭제**되나, impact aggregate 가 d3plot 부재 시 deep output 을 재사용하려면 `koo_impact_report` 가 force_reuse 를 지원해야 한다 (PostprocessShellGenerator.py:91-92, 주석상 전제). 지원 여부는 SIF 측 구현에 의존하므로 **확인 필요**.
- **separate_job 의 deep sbatch 는 dependency 없이 즉시 제출**된다 (시뮬 잡 안에서 호출되어 잡이 끝나가는 시점이므로) (CumulativeScenarioRunner.py:745).
- **SIF 미배포 시** 모든 sh 는 `SIF not found` 로 `exit 2` 한다 (PostprocessShellGenerator.py:113-116,180-183,277-280).
- **`impact_yield_stress` 와 `yield_stress_mpa` 는 별개 키**이다. impact 단위계가 deck 의존이라 sphere 의 값을 재사용하지 않는다 (PostprocessShellGenerator.py:245-247).
- `_maybe_submit_sphere_job()` 는 단일 base_dir(첫 시나리오 기준)을 가정한다 (SlurmSubmitter.py:138-140).

---

## 6. 개발 현황

**구현됨.**

근거:
- deep/sphere/impact sh 생성 + sbatch 빌더 전부 구현 (Runner/PostprocessShellGenerator.py:57-464).
- per-job deep_report 자동 실행(inline/separate_job) 및 prepare 6.5 단계 wiring (Runner/CumulativeScenarioRunner.py:678-763, 1105-1107).
- mode 라우팅(DROP→sphere, IMPACT→impact) 자동 제출 (Runner/SlurmSubmitter.py:103-175) + 수동 CLI (KooChainRun:2532-2651).
- 실제 동작 예제가 repo 에 존재 (`Examples/postprocess_pipeline/*.json`, `Examples/scenario_examples/impact_cylinder_8pi.json`).

부분/미확인:
- impact 의 normal-termination 사전 필터는 v1 에서 생략(로더 self-skip 의존) (PostprocessShellGenerator.py:237-238).
- d3plot 삭제 후 impact 의 deep output 재사용(force_reuse) 동작은 SIF 측 구현 의존 → **확인 필요**.
