# KooChainRun submit

> 근거 파일: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/KooChainRun`
> 서브파서 정의: `KooChainRun:81-140` / 디스패치: `KooChainRun:326-327` / 본체 `cmd_submit`: `KooChainRun:793-822`

---

## 1. 목적 / 개요

`submit`은 `prepare` 단계에서 생성한 `runner_config.json`을 입력받아 **Slurm 클러스터에 시뮬레이션 작업을 제출**하는 커맨드입니다. 서브파서 description(`KooChainRun:84`) 그대로 다음을 수행합니다.

> "Create directories, generate metadata, and submit Slurm array jobs"

즉, 출력 디렉토리 / Slurm 스크립트 디렉토리 생성, 메타데이터(`jobs.json`) 기록, DOE별 `sbatch` 스크립트 생성, `sbatch` 호출까지 한 번에 처리합니다. 제출된 잡은 컴퓨트 노드에서 `KooChainRun run --doe N`(또는 sequential 잡 내부에서 여러 DOE 순차 실행)을 호출하여 `KooMeshModifier → LS-DYNA → dynain → 다음 step` 파이프라인을 수행합니다.

`cmd_submit`(`KooChainRun:793`)은 `runner_config.json`의 최상위 `mode` 값과 `--mode` 옵션에 따라 다음 4개 경로 중 하나로 분기합니다.

- `mode == "part_validation"` → `submit_part_validation` (`KooChainRun:805-809`)
- `mode == "drop_weight_impact"` → `submit_drop_weight_impact` (`KooChainRun:810-814`)
- `--mode cumulative` (기본) → `_submit_cumulative` (`KooChainRun:816-817`)
- `--mode large-scale` → `_submit_large_scale` (`KooChainRun:818-819`)

어느 경로로 끝나든 마지막에 `_maybe_submit_sphere_after`(`KooChainRun:808,813,822`)가 호출되어, `postprocess.enabled`가 켜져 있으면 종합 리포트 잡(sphere 또는 impact)을 dependency 잡으로 추가 제출합니다.

---

## 2. 입력 옵션 · 인자

서브파서 정의: `KooChainRun:81-140`. 위치 인자 1개 + 옵션 9개입니다.

| 인자 / 옵션 | 형식 | 필수 | 기본값 | 설명 | 근거 (file:line) |
|---|---|---|---|---|---|
| `config` | 위치 인자 (문자열) | 예 | — | `runner_config.json` 파일 경로 | `KooChainRun:86-89` |
| `--mode` | `choices=[large-scale, cumulative]` | 아니오 | `cumulative` | 제출 방식. `cumulative`=DOE별 개별 잡, `large-scale`=`LargeScaleDOEManager` 배열 잡 | `KooChainRun:90-96` |
| `--nodes` | `int` | 아니오 | `2` | 사용할 노드 수 (sequential 모드에서는 생성할 잡 수) | `KooChainRun:97-102` |
| `--jobs-per-node` | `int` | 아니오 | `4` | 노드당 동시 잡 수 | `KooChainRun:103-108` |
| `--ncpu-per-job` | `int` | 아니오 | `None` → `environment.ncpu`, 없으면 `16` | 잡당 CPU 수 | `KooChainRun:109-114`, 적용 `KooChainRun:929,1218` |
| `--partition` | 문자열 | 아니오 | `normal` | Slurm 파티션 | `KooChainRun:115-119` |
| `--memory` | 문자열 | 아니오 | `None` → `environment.memory`, 없으면 `64G` | DOE 잡당 메모리 | `KooChainRun:120-124`, 적용 `KooChainRun:1191` |
| `--time-limit` | 문자열 | 아니오 | `24:00:00` | DOE 잡당 시간 제한 | `KooChainRun:125-129` |
| `--data-root` | 문자열 | 아니오 | `/data` | 실행 루트 디렉토리 (large-scale 모드에서 사용) | `KooChainRun:130-134`, 적용 `KooChainRun:944` |
| `--sequential` | 플래그 (`store_true`) | 아니오 | `False` | 노드당 1잡, 잡 안에서 여러 DOE 순차 실행. `--nodes` 수만큼 잡 생성 | `KooChainRun:135-140` |

호출 디스패치: `args.command == 'submit'` → `cmd_submit(args)` (`KooChainRun:326-327`).

### CLI 기본값 vs runner_config 환경값 우선순위

`cumulative` 경로에서 일부 옵션은 **CLI가 기본값과 다를 때만 CLI를 쓰고, 기본값 그대로면 `environment` 값을 사용**합니다 (`KooChainRun:1191-1193`).

- `--memory`: `args.memory or env["memory"] or "64G"` (`KooChainRun:1191`)
- `--partition`: CLI가 `normal`이 아니면 CLI, 아니면 `env["partition"]` (`KooChainRun:1192`)
- `--time-limit`: CLI가 `24:00:00`이 아니면 CLI, 아니면 `env["time_limit"]` (`KooChainRun:1193`)
- `--ncpu-per-job`: `None`이면 `env["ncpu"]`, 없으면 `16` (`KooChainRun:1218`)

> 주의: 파티션 기본값 `normal`을 CLI로 명시해도 코드상 `!= 'normal'` 비교 때문에 `environment.partition`이 우선됩니다(확인 필요 시 `KooChainRun:1192` 참고). 의도한 파티션이 `normal`인데 `environment`에 다른 값이 있으면 후자가 적용됩니다.

---

## 3. 사용 예제

### 3-1. 기본 cumulative 제출 (실제 예제 스크립트)

`Examples/HWWarrantyDropTest/Tests/Test_009_ScratchRun_100/run.sh:59-62`에서 발췌한 실제 호출입니다(prepare로 `runner_config.json` 생성 후 submit).

```bash
# Test_009/run.sh:33  (prepare 먼저)
"$KOOCR" prepare "$SCRIPT_DIR/scenario.json" -o "$SCRIPT_DIR/runner_config.json"

# Test_009/run.sh:59-62  (submit)
"$KOOCR" submit "$SCRIPT_DIR/runner_config.json" \
    --nodes "$NODES" \
    --jobs-per-node "$JOBS_PER_NODE" \
    --ncpu-per-job "$NCPU_PER_JOB"
```

### 3-2. multinode (DOE당 1잡)

`Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/run_multinode.sh:97-100`:

```bash
"$KOOCR" submit "$SCRIPT_DIR/runner_config_multinode.json" \
    --nodes "$CONCURRENT_DOES" \
    --jobs-per-node 1 \
    --ncpu-per-job "$NCPU_PER_JOB"
```

### 3-3. sequential 모드 (노드당 1잡, 여러 DOE 순차)

`Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick/run.sh:25-28`:

```bash
"$KOOCR" submit "$SCRIPT_DIR/runner_config.json" \
    --nodes "$NODES" \
    --ncpu-per-job "$NCPU_PER_JOB" \
    --sequential
```

### 3-4. submit가 읽는 `runner_config.json` 필드

`_submit_cumulative`가 직접 읽는 필드는 다음과 같습니다(`KooChainRun:1179-1235`). 아래는 `Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick/runner_config.json`에서 발췌(가공 최소화).

```json
{
  "project": {
    "name": "Test_010_Sequential_Quick",
    "model_file": ".../Test_010_Sequential_Quick/MinimumModel.k",
    "output_dir": ".../Test_010_Sequential_Quick/output"
  },
  "scenario": {
    "doe_count": 10,
    "batch_koomeshmodifier": false
  },
  "environment": {
    "ncpu": 1,
    "memory": "2G",
    "partition": "viz",
    "time_limit": "01:00:00",
    "koochainrun_path": "/data/SmartTwinPreprocessor/bin/KooChainRun",
    "apptainer_tmpdir": "/tmp"
  }
}
```

- `project.name` / `project.output_dir` / `project.model_file` (`KooChainRun:1180-1184`)
- `scenario.doe_count` — 생성할 DOE 잡 수 (`KooChainRun:1179`)
- `scenario.batch_koomeshmodifier` — batch 사전생성 모드 토글 (`KooChainRun:1235`)
- `environment.koochainrun_path` — 노드에서 호출할 `KooChainRun` 절대경로. 없으면 실행 중인 파일 자신(`KooChainRun:1188`)
- `environment.apptainer_tmpdir` 등 — sbatch 헤더/본문 생성에 사용 (`KooChainRun:1221-1223`)

### 3-5. submit가 추가로 인식하는 환경 옵션 (코드 기본값)

`runner_config.json`에 없을 수 있으나 `environment`에 넣으면 동작이 바뀌는 키들입니다.

| 키 | 기본값 | 효과 | 근거 |
|---|---|---|---|
| `environment.job_stagger_seconds` | `300` | 잡 시작 시 `0~N`초 랜덤 sleep으로 동시 완료 방지. `0`이면 비활성 | `KooChainRun:1226,1447-1451` |
| `environment.exclusive` | `True` | `#SBATCH --exclusive` + `--mem=0`(전체 메모리) | `KooChainRun:1408-1410` |
| `environment.scratch_run.enabled` | `False` | 컴퓨트 노드 로컬 scratch에서 실행 후 결과 복사 | `KooChainRun:1229-1232` |
| `environment.scratch_run.scratch_base` | `/scratch` | scratch 루트 | `KooChainRun:1231` |
| `environment.scratch_run.cleanup_on_success` | `True` | 성공 시 scratch 정리 | `KooChainRun:1232,1534` |
| `environment.additional_files` | `[]` | 제출 시 안내 출력 | `KooChainRun:1356-1358` |

---

## 4. 동작 원리 (코드 근거)

### 4-1. 진입 및 mode 분기 — `cmd_submit`
- `config_path` resolve 후 존재 확인, 없으면 종료 (`KooChainRun:796-800`).
- `runner_config.json`을 로드해 최상위 `mode`로 part_validation / drop_weight_impact 분기 (`KooChainRun:803-814`).
- 그 외에는 `--mode`에 따라 `_submit_cumulative` 또는 `_submit_large_scale` 호출 (`KooChainRun:816-819`).
- 종료 직전 `_maybe_submit_sphere_after`로 종합 리포트 잡 제출 (`KooChainRun:822`).

### 4-2. cumulative 경로 — `_submit_cumulative` (`KooChainRun:1151`)
1. 옵션/환경값 병합 (`KooChainRun:1191-1218`).
2. `sinfo -p <partition> -o %l`로 파티션 최대 시간 조회 → `time_limit` 초과 시 자동 cap (`KooChainRun:1196-1216`).
3. 노드 Health Check(advisory): `scontrol show nodes`로 `NodeAddr` 캐싱 후 SSH ping. 이는 정보 제공용이며 exclude 결정과 무관 (`KooChainRun:1256-1316`).
4. exclude 대상은 SLURM이 `down/drain/fail`로 마킹한 노드만 → `#SBATCH --exclude=` 라인 생성 (`KooChainRun:1318-1336`).
5. include 파일 검증(`KooIncludeManager`)은 실패해도 제출 계속 (`KooChainRun:1338-1353`).
6. `output_dir/slurm_scripts/` 생성 + NFS 캐시 동기화 (`KooChainRun:1362-1369`).
7. 기존 `jobs.json` 백업 후 빈 `jobs.json` 즉시 생성(crash 대비) (`KooChainRun:1371-1388`).
8. DOE별 sbatch 스크립트(`run_doe_NNN.sh`) 생성: 노드 쓰기 점검, orphan Apptainer 정리, stale lock 정리, NFS 가용성 확인, stagger sleep 후 `kcr_path run <config> --doe N` 호출 (`KooChainRun:1412-1619`).
9. 제출 방식 3분기:
   - **batch 모드**(`batch_koomeshmodifier` + pregenerated): KooMeshModifier를 `Popen`으로 백그라운드 실행하고, DOE별 `.done` 파일을 polling하여 준비된 DOE부터 즉시 `sbatch` (`KooChainRun:1653-1717`).
   - **sequential 모드**(`--sequential`): DOE를 `--nodes`개 슬롯에 round-robin 분배, 슬롯당 `run_seq_NNN.sh` 1잡 생성. `time_limit`을 슬롯 최대 DOE 수만큼 곱해 확장 후 파티션 최대로 cap (`KooChainRun:1719-1901`).
   - **일반 모드**: 1~doe_count 전부 즉시 `sbatch`. 첫 DOE에서 `sbatch` 자체가 실패하면 중단 (`KooChainRun:1903-1916`).
10. 각 제출 시 `jobs.json`의 해당 DOE에 `job_id/job_name/status="submitted"/submitted_at/script_path` 기록 (`_sbatch_doe`, `KooChainRun:1625-1651` / sequential은 `KooChainRun:1887-1897`).
11. 요약 출력 + Next steps 안내(status/logs/stop/rerun/diagnose/collect) (`KooChainRun:1918-1938`).

### 4-3. large-scale 경로 — `_submit_large_scale` (`KooChainRun:921`)
`LargeScaleDOEManager(runner_config_path, data_root, nodes, jobs_per_node, ncpu_per_job)`를 생성하고 `manager.run()`을 호출하는 배열 잡 방식입니다 (`KooChainRun:942-949`). `--data-root`는 이 경로에서만 사용됩니다.

### 4-4. 종합 리포트 자동 제출 — `_maybe_submit_sphere_after` (`KooChainRun:825`)
- `postprocess.enabled`가 아니면 즉시 반환 (`KooChainRun:837-839`).
- `report_mode_from_runner_config`로 시나리오 모드 판별: `IMPACT`이면 `impact_report.sbatch`(`auto_impact`), 그 외면 `sphere_report.sbatch`(`auto_sphere`) (`KooChainRun:849-862`).
- `jobs.json`에서 모든 `job_id`를 모아 `afterany:` dependency로 sbatch 생성 후 제출 (`KooChainRun:871-916`).

---

## 5. 주의사항 · 한계

- **`config` 인자는 `runner_config.json`** 입니다 (`scenario.json` 아님). `scenario.json`은 `prepare` 입력입니다. 먼저 `prepare`로 변환해야 합니다(예제 3-1 참고).
- **partition CLI 기본값 함정**: `--partition normal`을 명시해도 `!= 'normal'` 비교(`KooChainRun:1192`)로 인해 `environment.partition`이 우선됩니다. 의도와 다르면 `environment.partition`을 확인하세요.
- **memory와 exclusive**: `exclusive=True`(기본)일 때 `--mem`은 `0`(전체 메모리)으로 강제되어 `--memory` 값이 무시됩니다 (`KooChainRun:1410`). `--memory`를 살리려면 `environment.exclusive=false` 필요.
- **`--sequential` + scratch_run 미지원**: 조합 시 경고 출력 후 scratch를 무시하고 non-scratch로 실행 (`KooChainRun:1723-1726`).
- **`--jobs-per-node`의 효과**: cumulative 일반/ sequential 모드에서 sbatch 스크립트는 DOE당(또는 슬롯당) `--nodes=1`로 생성됩니다. `--jobs-per-node`는 large-scale 모드에서 실제 동시성에 반영되며, cumulative에서는 주로 병렬 슬롯 안내 출력 계산(`nodes * jobs_per_node`)에만 쓰입니다 (`KooChainRun:1252,938 / 1420`).
- **batch 모드 부분 실패 허용**: KooMeshModifier가 일부 DOE의 `.done`을 못 만들면 해당 DOE는 제출하지 않고, 이미 제출된 잡만 실행됩니다 (`KooChainRun:1698-1709`).
- **`sbatch`/`sinfo`/`scontrol`/`ssh` 부재 시**: 대부분 try/except로 advisory 처리되나, 첫 DOE에서 `sbatch not found`이면 일반 모드는 중단됩니다 (`KooChainRun:1649-1651,1913-1916`).
- **테스트 디렉토리는 NFS여야 함**: 컴퓨트 노드가 `output_dir`/`config`를 봐야 하므로 `/tmp`가 아닌 공유 경로(`/data/...`)에 두어야 합니다(프로젝트 운영 규칙).

---

## 6. 개발 현황

**구현됨.** `cmd_submit`(`KooChainRun:793-822`)과 4개 분기 경로 모두 본체가 존재하고, 실제 예제 스크립트(`Examples/HWWarrantyDropTest/Tests/Test_009/Test_010/Test_001` 등)에서 호출됩니다. cumulative(일반/sequential/batch), large-scale, postprocess 자동 제출까지 동작 로직이 코드에 모두 구현되어 있습니다.

- 부분구현/확인 필요: `_maybe_submit_sphere_after`는 `report_mode_from_runner_config` 등 외부 모듈(`Runner.PostprocessShellGenerator`) import에 의존하며, import 실패 시 경고만 출력하고 건너뜁니다 (`KooChainRun:841-847`). part_validation / drop_weight_impact 경로의 세부 동작은 별도 모듈(`Runner.PartValidationWorkflow`, `Runner.DropWeightImpactWorkflow`)에 있어 본 문서 범위 밖이며 별도 검증 필요.
