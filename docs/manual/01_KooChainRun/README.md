# KooChainRun 개요 · 커맨드 맵

> 근거 파일: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/KooChainRun`
> argparse 서브커맨드 정의: L58–L318 / 디스패치: L324–L344 / 본체 함수: `cmd_*` (L347–L2716)
> 모듈 헤더 자기소개: "KooChainRun (KCR) - Sequential CAE Analysis Workflow Manager" (L3), Version 1.4.0 (L9, L56)

---

## 1. 목적 / 개요

`KooChainRun`(KCR)은 **다단계 연쇄(chained) CAE 시뮬레이션을 Slurm 클러스터에서 관리**하는
CLI 툴이다. 모듈 docstring은 "A CLI tool for managing multi-step chained CAE simulations with
automatic Slurm job submission and dependency management" 라고 정의한다(L4–L6).

핵심 데이터 흐름은 다음과 같다(`prepare`/`run` 본체에서 import 하는 모듈로 확인):

- 사용자 친화 `scenario.json` → `prepare` → 상세 `runner_config.json`
  (`Runner.CumulativeDesigner` 사용, L350)
- `runner_config.json` → `submit` → Slurm 잡 제출 (`jobs.json` 기록)
- 각 compute node에서 단일 DOE 파이프라인(`KooMeshModifier` → LS-DYNA → dynain → 다음 step) 실행
  (`Runner.CumulativeScenarioRunner`, L1943; `run` description L167)
- 진행/실패 모니터링(`status`/`diagnose`) · 재실행(`rerun`) · 후처리(`postprocess`)

이 문서는 **9개 서브커맨드의 전체 지도**와 **전형적 워크플로우**를 제공한다.
각 커맨드의 상세는 [`commands/`](commands/) 하위 문서를 참조한다.

`KooChainRun` 은 `argparse` 의 서브파서 구조다(`subparsers = parser.add_subparsers(...)`, L58).
서브커맨드 없이 호출하면 도움말을 출력하고 종료한다(`else: parser.print_help(); sys.exit(1)`, L342–L344).

---

## 2. 입력 옵션 · 인자 (서브커맨드 한눈 표)

argparse 정의 출처: 각 `*_parser = subparsers.add_parser(...)` 블록 L63–L318.
디스패치: `if args.command == ...` L324–L341.

| # | 서브커맨드 | 위치 인자 | 주요 옵션 | 본체 함수 (file:line) | 상세 문서 |
|---|---|---|---|---|---|
| 1 | `prepare` | `scenario` (필수) | `-o/--output` | `cmd_prepare` (L347) | (commands/prepare.md — 미작성) |
| 2 | `submit` | `config` (필수) | `--mode {large-scale,cumulative}`, `--nodes`, `--jobs-per-node`, `--ncpu-per-job`, `--partition`, `--memory`, `--time-limit`, `--data-root`, `--sequential` | `cmd_submit` (L793) | [submit.md](commands/submit.md) |
| 3 | `status` | `config` (선택) | `--watch` | `cmd_status` (L1985) | [status.md](commands/status.md) |
| 4 | `run` | `config` (필수) | `--doe` (필수), `--resume`, `--skip-koomeshmodifier`, `--pregenerated-dir` | `cmd_run` (L1941) | [run.md](commands/run.md) |
| 5 | `collect` | `config` (필수), `output_dir` (선택, 기본 `./results`) | — | `cmd_collect` (L2014) | [collect.md](commands/collect.md) |
| 6 | `stop` | `test_dir` (선택, 기본 `.`) | — | `cmd_stop` (L2061) | [stop.md](commands/stop.md) |
| 7 | `rerun` | `test_dir` (선택, 기본 `.`) | `--dry-run`, `--force`, `--does`, `--exclude-nodes`, `--sequential`, `--nodes`, `--cleanup-stale` | `cmd_rerun` (L2360) | (commands/rerun.md — 미작성) |
| 8 | `diagnose` | `test_dir` (선택, 기본 `.`) | — | `cmd_diagnose` (L2661) | (commands/diagnose.md — 미작성) |
| 9 | `postprocess` | `config` (필수) | `--deep` \| `--sphere` \| `--impact` \| `--all` (상호배타) | `cmd_postprocess` (L2532) | (commands/postprocess.md — 미작성) |

전역 옵션: `--version` (출력 `KooChainRun 1.4.0`, L56).

### 커맨드별 한 줄 요약 (parser `help` 문구 발췌)

| 커맨드 | `help` (코드 근거) |
|---|---|
| `prepare` | "Generate runner configuration from scenario" (L65) |
| `submit` | "Submit jobs to Slurm cluster" (L83) |
| `status` | "Check execution status" (L147) |
| `run` | "Run single DOE pipeline on compute node" (L166) |
| `collect` | "Collect simulation results" (L202) |
| `stop` | "제출된 모든 작업 취소" (L221) |
| `rerun` | "실패/미완료 DOE만 재실행" (L236) |
| `diagnose` | "실패 DOE 원인 진단" (L290) |
| `postprocess` | "KooD3plotReader 후처리 수동 실행" (L305) |

### 입력 인자 구분

- **`config`** 계열(`prepare`/`submit`/`status`/`run`/`collect`/`postprocess`)은
  `scenario.json` 또는 `runner_config.json` **파일 경로**를 받는다.
- **`test_dir`** 계열(`stop`/`rerun`/`diagnose`)은 `jobs.json` 이 들어 있는
  **테스트 디렉토리 경로**를 받는다(기본 `.`). 이 세 커맨드는 모두 내부적으로
  `Runner.JobManager` 를 사용한다(`cmd_stop` L2063, `cmd_rerun` L2364, `cmd_diagnose` L2663).

---

## 3. 사용 예제

### 3-1. 전형적 워크플로우 (`run.sh` 발췌)

`Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick/run.sh` — prepare → submit 2단계:

```bash
KOOCR="/data/SmartTwinPreprocessor/bin/KooChainRun"
NODES=2
NCPU_PER_JOB=1

# 1. Prepare: scenario.json → runner_config.json
"$KOOCR" prepare "$SCRIPT_DIR/scenario.json" -o "$SCRIPT_DIR/runner_config.json"

# 2. Submit (sequential mode)
"$KOOCR" submit "$SCRIPT_DIR/runner_config.json" \
    --nodes "$NODES" \
    --ncpu-per-job "$NCPU_PER_JOB" \
    --sequential

# 상태 확인
# squeue -u $USER
```

### 3-2. 입력 `scenario.json` (실측 발췌)

`prepare` 의 입력. `Test_010_Sequential_Quick/scenario.json` 상단 구조:

```json
{
  "project_name": "Test_010_Sequential_Quick",
  "environment": {
    "koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "koochainrun_path": "/data/SmartTwinPreprocessor/bin/KooChainRun",
    "ncpu": 1,
    "time_limit": "01:00:00",
    "partition": "viz"
  },
  "simulation_params": { "height": 1500, "tFinal": 0.005, "dt": 1e-06 },
  "scenarios": [
    {
      "scenario_name": "Sequential_Quick_10",
      "template": "MinimumModel.k",
      "angle_source": {
        "source_type": "fibonacci_lattice",
        "fibonacci_lattice": { "num_directions": 10 }
      },
      "cumulative": { "num_steps": 1, "mode_sequence": ["DROP"] }
    }
  ]
}
```

`environment.koochainrun_path` 는 각 compute node 잡이 다시 호출할 `KooChainRun run` 실행 파일
경로로 쓰인다(prepare가 생성하는 헬퍼 스크립트 헤더에서도 같은 키를 읽음, L428).

### 3-3. 모니터링 · 재실행 · 후처리 (CLI 직접 호출)

```bash
# 진행 상태 (squeue + config)
KooChainRun status /path/to/runner_config.json

# 실패 원인 진단 (test_dir = jobs.json 있는 폴더)
KooChainRun diagnose /path/to/test_dir

# 실패/미완료 DOE만 재실행 (먼저 dry-run으로 대상 확인)
KooChainRun rerun /path/to/test_dir --dry-run
KooChainRun rerun /path/to/test_dir --does 1,3,7 --force

# 전체 작업 취소
KooChainRun stop /path/to/test_dir

# 후처리 리포트 수동 실행 (deep 전부 + scenario mode 에 맞는 종합 리포트)
KooChainRun postprocess /path/to/runner_config.json --all
```

`prepare` 실행 시 `rerun.sh` / `stop.sh` / `diagnose.sh` / `copy.sh` 헬퍼 스크립트가
시나리오 디렉토리에 자동 생성되므로(`_generate_helper_scripts`, L408, L417–L433),
위 CLI 대신 `./rerun.sh` `./stop.sh` `./diagnose.sh` 로도 호출할 수 있다.

---

## 4. 동작 원리 (코드 근거)

### 4-1. 디스패치 구조

`main()`(L32)에서 `argparse` 서브파서를 모두 등록(L58–L318)한 뒤
`args = parser.parse_args()`(L321)로 파싱하고, `args.command` 값에 따라 9개 `cmd_*` 함수로
분기한다(L324–L341). 매칭되는 커맨드가 없으면 도움말 출력 후 종료(L342–L344).

```
prepare → cmd_prepare (L325)        collect → cmd_collect (L333)     diagnose → cmd_diagnose (L339)
submit  → cmd_submit  (L327)        stop    → cmd_stop    (L335)     postprocess → cmd_postprocess (L341)
run     → cmd_run     (L329)        rerun   → cmd_rerun   (L337)
status  → cmd_status  (L331)
```

### 4-2. 전형적 워크플로우의 내부 연결

1. **prepare** — `scenario.json` 로드 후 `mode` 에 따라 분기한다(L377–L386):
   `part_validation` → `Runner.PartValidationWorkflow.prepare_part_validation`,
   `drop_weight_impact` → `Runner.DropWeightImpactWorkflow.prepare_drop_weight_impact`,
   그 외 기본 → `CumulativeDesigner(...).parse_user_config()` 로 `runner_config.json` 생성(L389–L393).
   이어서 `output_dir/slurm_scripts` 를 미리 만들고(L399–L402, NFS 전파 시간 확보),
   `rerun.sh`/`stop.sh`/`diagnose.sh`/`copy.sh` 헬퍼를 생성한다(L408).

2. **submit** — `runner_config.json` 을 받아 디렉토리/메타데이터 생성, DOE별 sbatch 스크립트
   생성, `sbatch` 호출, `jobs.json` 기록까지 수행한다(parser description L84).
   `cumulative`(기본)/`large-scale`/`part_validation`/`drop_weight_impact` 4경로로 분기하며,
   끝에서 후처리 dependent job을 자동 제출할 수 있다(상세는 [submit.md](commands/submit.md)).

3. **status / diagnose** — `status` 는 `squeue -u $USER` 를 실행하고(`os.system`, L1995)
   config가 주어지면 경로만 표시한다(상세 진행률은 "coming soon" 주석, L2001–L2003 — 부분 구현).
   `diagnose` 는 `JobManager.diagnose_failures()` 로 실패 DOE를 원인별(라이선스/MPI/타임아웃/디스크/
   메모리/Apptainer/취소 등)로 그룹화해 로그 발췌와 함께 출력한다(L2673–L2716).

4. **run** — submit이 만든 각 잡 스크립트가 compute node에서 호출하는 단일 DOE 실행기.
   `CumulativeScenarioRunner(config, doe_filter=args.doe, ...)` 생성 후 `run_all()` 실행
   (L1966–L1972). `--skip-koomeshmodifier`/`--pregenerated-dir` 는 batch 선생성 모드용(L1951–L1952).

5. **rerun** — `JobManager.get_doe_status()` 로 DOE 상태 테이블을 출력하고,
   `failed`/`killed`/`not_started`/`license_error` 상태 DOE를 재실행 대상으로 선정한다
   (`json_corrupted` DOE는 제외, L2401–L2405). `--does` 로 특정 DOE만 지정 가능(L2398–L2399).
   `--sequential` 이면 `_rerun_sequential` 로 남은 DOE를 노드에 round-robin 분배해 배치 잡으로
   재제출한다(L2096–).

6. **postprocess** — `runner_config.json` 에서 `output_dir` 를 추출하고
   `report_mode_from_runner_config` 로 DROP→sphere / IMPACT→impact 종합 리포트를 선택한다(L2558–L2559).
   플래그에 따라 각 `Run_*/deep_report.sh`(L2584–L2622) 및 `sphere_report.sh`/`impact_report.sh`
   (L2624–L2658)를 `bash` 로 순차 실행한다. 무플래그/`--all` 은 deep 전부 + mode에 맞는 종합 1개(L2567–L2571).

### 4-3. JobManager 공유 (stop/rerun/diagnose)

세 커맨드는 모두 `test_dir` 의 `jobs.json` 을 읽는 `Runner.JobManager` 를 생성한다
(`cmd_stop` L2063–L2066, `cmd_rerun` L2364–L2367, `cmd_diagnose` L2663–L2666).
`stop` 은 `cancel_all_jobs()`(L2073), `rerun` 은 `get_doe_status()`(L2374),
`diagnose` 는 `diagnose_failures()`(L2673)를 호출한다. `jobs.json` 이 없으면
`FileNotFoundError` 로 종료한다(L2074–L2076 등).

---

## 5. 주의사항 · 한계

- **두 종류의 입력 경로를 혼동하지 말 것** — `config` 계열은 파일 경로(`scenario.json`/
  `runner_config.json`), `test_dir` 계열은 디렉토리 경로(`jobs.json` 포함)다. 잘못 주면
  대상 파일을 못 찾아 종료한다(예: `cmd_run` L1947–L1949).
- **`status` 의 상세 진행률은 부분 구현** — config를 줘도 현재는 경로만 찍고 "(Detailed progress
  monitoring coming soon)" 을 출력한다(L2002–L2003). 실제 진행률은 `squeue` 와 `rerun`(상태 테이블)으로 확인.
- **`collect` 의 결과 수집은 미구현** — `cmd_collect` 에서 `cumulative`/기본 경로는
  "Result collection not yet implemented" 를 출력하고 수동 복사 안내만 한다(L2051–L2054).
  단, `part_validation`/`drop_weight_impact` 모드는 전용 워크플로우로 위임되어 동작한다(L2026–L2033).
- **NFS 공유 경로 필수** — submit이 만든 잡 스크립트는 compute node에서 `runner_config.json`/
  `output_dir` 를 다시 읽으므로 `/data/...` 같은 공유 경로에 둬야 한다(`/tmp` 등 로컬 금지,
  프로젝트 메모리 규칙과 일치). prepare가 `output_dir/slurm_scripts` 를 미리 만드는 것도
  NFS 전파 지연 대비다(L399–L402).
- **`prepare` 가 헬퍼 스크립트를 덮어쓴다** — `rerun.sh`/`stop.sh`/`diagnose.sh`/`copy.sh` 는
  매 prepare마다 재생성된다(L430–L433). 수동 수정분은 보존되지 않는다.
- **`postprocess`/종합 리포트 스크립트 의존** — `sphere_report.sh`/`impact_report.sh` 가 없으면
  실행하지 않고 경고만 한다("prepare 시 postprocess 옵션이 있어야 자동 생성됨", L2628, L2646).
- **상세 동작은 본 문서 범위 밖** — `submit` 의 4분기, `rerun` 의 sequential 분배, mode별
  워크플로우(part_validation / drop_weight_impact) 등은 각 커맨드 문서 및 워크플로우 모듈에서 다룬다.

---

## 6. 개발 현황

**구현됨** (일부 커맨드는 부분구현).

근거:
- 9개 서브파서가 main parser에 모두 등록되어 있고(L63–L318), 디스패치가 9개 `cmd_*` 함수로
  연결되어 있다(L324–L341). 각 `cmd_*` 본체가 실제로 정의되어 있음을 확인했다
  (`cmd_prepare` L347, `cmd_submit` L793, `cmd_run` L1941, `cmd_status` L1985, `cmd_collect` L2014,
  `cmd_stop` L2061, `cmd_rerun` L2360, `cmd_diagnose` L2661, `cmd_postprocess` L2532).
- end-to-end 사용 흔적: 실제 호출 스크립트(`Test_010_Sequential_Quick/run.sh`)와 입력
  `scenario.json` 이 존재한다.

**부분구현으로 표기해야 하는 항목**:
- `status` 의 config 기반 상세 진행률(L2003, "coming soon" 주석).
- `collect` 의 기본/`cumulative` 경로 결과 수집(L2052, "not yet implemented").

> 비고: 본 개요 문서의 [`commands/`](commands/) 링크 중 `submit`/`status`/`run`/`collect`/`stop`
> 5개는 작성 완료, `prepare`/`rerun`/`diagnose`/`postprocess` 4개는 본 문서 작성 시점 기준
> 미작성(확인 필요 시 디렉토리 재확인). 커맨드 자체는 9개 모두 코드에 구현되어 있다.
