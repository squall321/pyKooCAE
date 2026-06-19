# KooChainRun rerun

## 1. 목적 / 개요

`KooChainRun rerun` 은 테스트 디렉토리에서 **실패하거나 완료되지 않은 DOE만 식별하여 재제출**하는 커맨드입니다. `jobs.json` 과 `simulation_index.json` 을 분석해 각 DOE 의 상태(완료/실패/중단/미시작 등)를 판정하고, 재실행이 필요한 DOE 에 대해 기존 Slurm 스크립트를 다시 `sbatch` 합니다.

- subparser 정의: `KooChainRun:234-283` (`'rerun'` add_parser)
- 디스패치: `KooChainRun:336-337` (`elif args.command == 'rerun': cmd_rerun(args)`)
- 핸들러: `KooChainRun:2360-2529` (`def cmd_rerun`)
- sequential 모드 헬퍼: `KooChainRun:2096-2358` (`def _rerun_sequential`)
- 상태 분석: `Runner/JobManager.py:291-393` (`get_doe_status`)
- 재제출: `Runner/JobManager.py:399-458` (`resubmit_does`)

CLI add_parser 의 help/description (`KooChainRun:236-237`):
> help: `실패/미완료 DOE만 재실행`
> description: `실패하거나 완료되지 않은 DOE만 식별하여 재제출합니다`

---

## 2. 입력 옵션 · 인자 (표)

`rerun` subparser 에 정의된 인자/옵션은 다음과 같습니다 (`KooChainRun:239-283`).

| 인자 / 옵션 | 종류 | 기본값 | 설명 | 근거 |
|------|------|--------|------|------|
| `test_dir` | 위치 인자 (`nargs='?'`) | `.` (현재 디렉토리) | 테스트 디렉토리 경로. 이 디렉토리의 `jobs.json` / `runner_config.json` / `simulation_index.json` 을 읽음 | `KooChainRun:239-244` |
| `--dry-run` | 플래그 (`store_true`) | `False` | 실제 제출 없이 상태와 재실행 대상만 표시 | `KooChainRun:245-249` |
| `--force` | 플래그 (`store_true`) | `False` | 확인(y/n) 없이 즉시 재제출 | `KooChainRun:250-254` |
| `--does` | 문자열 | `None` | 특정 DOE만 재실행 (콤마 구분, 예: `1,3,7`). 지정 시 자동 대상 선정 무시 | `KooChainRun:255-260` |
| `--exclude-nodes` | 문자열 | `None` | 제외할 노드 (콤마 구분, 예: `node07,node12`). `auto` 로 설정하면 이전 실패 노드를 자동 감지·제외 | `KooChainRun:261-267` |
| `--sequential` | 플래그 (`store_true`) | `False` | 남은 DOE 를 노드에 분배해 배치 잡으로 실행 (`submit --sequential` 과 동일) | `KooChainRun:268-272` |
| `--nodes` | 정수 | `None` | `--sequential` 모드에서 사용할 노드 수 (기본: 살아있는 노드 자동 감지) | `KooChainRun:273-278` |
| `--cleanup-stale` | 플래그 (`store_true`) | `False` | 재실행 전 중단된 DOE 의 이전 Run 디렉토리 자동 삭제 (기본: 안 함) | `KooChainRun:279-283` |

추가로 argparse 가 자동 제공하는 `-h` / `--help` 가 사용 가능합니다 (별도 add 정의는 없으나 argparse 기본 동작).

`test_dir` 은 `cmd_rerun` 내부에서 `Path(args.test_dir).resolve()` 로 절대경로 변환된 뒤 `JobManager(str(test_dir))` 에 전달됩니다 (`KooChainRun:2366-2367`).

---

## 3. 사용 예제

### 3.1 상태만 확인 (dry-run)

```bash
KooChainRun rerun /path/to/test_dir --dry-run
```

재실행 대상 DOE 목록과 상태 테이블만 출력하고 실제 제출은 하지 않습니다 (`KooChainRun:2475-2477`).

### 3.2 특정 DOE 만 강제 재제출

```bash
KooChainRun rerun /path/to/test_dir --does 1,3,7 --force
```

`--does` 로 대상 DOE 를 직접 지정하고, `--force` 로 y/n 확인을 건너뜁니다 (`KooChainRun:2398-2399`, `2479`).

### 3.3 실패 노드 자동 제외

```bash
KooChainRun rerun /path/to/test_dir --exclude-nodes auto
```

`auto` 지정 시 실패 잡의 노드(`sacct`)와 Slurm down/drain 노드(`sinfo`)를 감지해 `sbatch --exclude` 로 제외합니다 (`KooChainRun:2425-2469`).

### 3.4 노드 수동 제외

```bash
KooChainRun rerun /path/to/test_dir --exclude-nodes node01,node07
```

지정 노드를 그대로 제외 목록으로 사용합니다 (`KooChainRun:2471-2473`).

### 3.5 sequential 모드 + 이전 Run 정리

```bash
KooChainRun rerun /path/to/test_dir --sequential --nodes 4 --cleanup-stale --force
```

남은 DOE 를 4개 노드에 round-robin 분배해 배치 잡으로 재제출하고(`KooChainRun:2153-2156`), 재제출 전 중단된 DOE 의 이전 Run 디렉토리를 삭제합니다(`KooChainRun:2493-2516`).

### 3.6 자동 생성된 헬퍼 스크립트(rerun.sh) 사용

`prepare`/`submit` 단계에서 테스트 디렉토리에 `rerun.sh` 가 자동 생성됩니다. 생성 템플릿(`KooChainRun:421`)으로 만들어진 실제 스크립트(예: `Examples/HWWarrantyDropTest/Tests/Test_002_Full26_3Step/rerun.sh`)는 다음과 같습니다.

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOOCR=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/scenario.json'))['environment']['koochainrun_path'])")
"$KOOCR" rerun "$SCRIPT_DIR" "$@"
```

즉 `rerun.sh` 는 `scenario.json` 의 `environment.koochainrun_path` 로 KooChainRun 경로를 읽어, 자기 디렉토리를 `test_dir` 로 하여 `rerun` 을 실행합니다. 모든 `rerun` 옵션은 `"$@"` 로 그대로 전달됩니다.

```bash
./rerun.sh --dry-run
./rerun.sh --exclude-nodes auto --force
```

### 3.7 예상 콘솔 출력 형태

`cmd_rerun` 의 상태 테이블 출력 형식(`KooChainRun:2369-2419`):

```
================================================================================
KooChainRun - DOE 상태 확인
================================================================================

    DOE  상태             Slurm        Step
  ---------------------------------------------
      1  completed        COMPLETED     3/3
      2  failed           FAILED        1/3
      3  not_started      UNKNOWN       0/3

완료: 1/3개
재실행 대상: 2개 - DOE [2, 3]
```

---

## 4. 동작 원리 (코드 근거)

1. **인자 파싱 / 디스패치**
   - `rerun` subparser 가 `test_dir` 위치 인자 + 7개 옵션을 정의 — `KooChainRun:234-283`.
   - `args.command == 'rerun'` 일 때 `cmd_rerun(args)` 호출 — `KooChainRun:336-337`.

2. **JobManager 초기화 / 상태 분석** — `KooChainRun:2366-2395`
   - `test_dir = Path(args.test_dir).resolve()` 후 `JobManager(str(test_dir))` 생성 (`jobs.json`, `runner_config.json` 경로 보관 — `Runner/JobManager.py:24-27`).
   - `manager.get_doe_status()` 로 모든 DOE 상태 맵을 산출 — `KooChainRun:2374`, 구현 `Runner/JobManager.py:291-393`.
     - `jobs.json` 의 `job_id` → `_query_slurm_status` 로 Slurm 상태 조회(`sacct` 후 `squeue` fallback, 둘 다 실패 시 `"UNKNOWN"`) — `JobManager.py:336`, `76-103`.
     - `simulation_index.json` 의 step 별 `status` 와 중간 step 의 `dynain` 존재 여부로 `steps_completed` 계산 — `JobManager.py:343-364`.
     - 상태 분류: 전 step 완료→`completed`, Slurm RUNNING/PENDING→`running`, CANCELLED/TIMEOUT/NODE_FAIL/OUT_OF_MEMORY→`killed`, FAILED 또는 step 실패→(로그에 라이선스 에러면 `license_error` 그 외 `failed`), 그 외→`not_started` — `JobManager.py:367-383`.
   - `FileNotFoundError`(파일 없음) 또는 `json.JSONDecodeError`(JSON 손상) 시 메시지 출력 후 `sys.exit(1)` — `KooChainRun:2375-2381`.

3. **상태 테이블 출력 + 손상 DOE 표시** — `KooChainRun:2384-2395`
   - DOE 인덱스 오름차순으로 `DOE / 상태 / Slurm / Step` 한 줄씩 출력.
   - `json_corrupted` 플래그가 있는 DOE 는 `json_corrupted` 라벨로 표시되고 `corrupted_does` 에 수집됨.

4. **재실행 대상 결정** — `KooChainRun:2397-2419`
   - `--does` 지정 시: 콤마 분리 정수 리스트를 그대로 대상으로 사용 — `KooChainRun:2398-2399`.
   - 미지정 시: 상태가 `failed`/`killed`/`not_started`/`license_error` 이면서 `json_corrupted` 가 아닌 DOE 를 자동 선정 — `KooChainRun:2401-2405`.
   - 손상(`json_corrupted`) DOE 는 재실행 대상에서 제외되고 경고 출력 — `KooChainRun:2404`, `2411-2413`.
   - 대상이 없으면 `재실행 대상 DOE가 없습니다.` 출력 후 `return` — `KooChainRun:2415-2417`.

5. **실패 노드 제외 처리** — `KooChainRun:2422-2473`
   - `--exclude-nodes auto`:
     - 실패/중단 DOE 의 `job_id` 들을 모아(`CANCELLED` 는 사용자 취소로 보고 제외) `sacct --format=NodeList` 로 노드 감지 — `KooChainRun:2429-2448`.
     - `sinfo -t down,drain,drng` 의 노드도 제외 목록에 추가 — `KooChainRun:2453-2462`.
   - `--exclude-nodes <list>`: 콤마 분리 노드를 그대로 제외 집합으로 사용 — `KooChainRun:2471-2473`.

6. **dry-run / 확인 분기** — `KooChainRun:2475-2490`
   - `--dry-run` 이면 `[DRY-RUN] 실제 제출하지 않습니다.` 출력 후 `return` — `KooChainRun:2475-2477`.
   - `--force` 가 아니면 `input()` 으로 y/n 확인(sequential 여부에 따라 문구 분기). `y` 가 아니면 취소, 비대화형(EOFError)이면 `--force` 사용 안내 후 `return` — `KooChainRun:2479-2490`.

7. **--cleanup-stale (선택)** — `KooChainRun:2493-2516`
   - 대상 DOE 의 각 step alias 를 생성(`_generate_alias`)해 `simulation_index` 에서 Run 정보 조회 — `KooChainRun:2503-2504`, `JobManager.py:105-123`.
   - status 가 `completed` 가 아닌 Run 의 폴더가 실제 디렉토리이면 `shutil.rmtree` 로 삭제, 삭제 개수 출력 — `KooChainRun:2505-2516`.

8. **재제출 실행** — `KooChainRun:2518-2529`
   - **일반 모드**: `manager.resubmit_does(target_does, exclude_nodes=exclude_list)` 호출 — `KooChainRun:2526`.
     - 각 DOE 의 `script_path`(없으면 `output_dir/slurm_scripts/run_doe_{NNN}.sh` 시도)를 `sbatch [--exclude <nodes>]` 로 재제출 — `JobManager.py:415-435`.
     - 성공 시 새 `job_id` 로 `jobs.json` 갱신(`status: resubmitted`, `prev_job_id` 보존) — `JobManager.py:436-449`, 저장 `JobManager.py:457`(atomic write `48-67`).
   - **sequential 모드**: `_rerun_sequential(manager, target_does, exclude_list, args)` 호출 — `KooChainRun:2522-2524`.
     - 노드 수 결정(`--nodes` 또는 `sinfo` idle/mix 자동 감지) — `KooChainRun:2120-2146`.
     - DOE 를 노드에 round-robin 분배 — `KooChainRun:2153-2156`.
     - 노드당 DOE 수에 비례해 time_limit 확장(+파티션 최대 cap) — `KooChainRun:2161-2200`.
     - 슬롯별 `rerun_seq_<HHMMSS>_<NNN>.sh` 스크립트를 생성, 각 DOE 에 대해 `{koochainrun_path} run {config} --doe {N}` 을 순차 실행하는 배치 잡으로 `sbatch` 제출 — `KooChainRun:2239-2342`.
     - 제출된 슬롯의 모든 DOE 를 `jobs.json` 에 `status: resubmitted`, `rerun: true`, `sequential_slot` 으로 기록(atomic write) — `KooChainRun:2328-2353`.

---

## 5. 주의사항 · 한계

- **상태 파일 의존**: 상태 판정은 `jobs.json` + `simulation_index.json` + Slurm 조회 결과에 의존합니다. `runner_config.json` 이 없으면 `get_doe_status` 단계에서 `FileNotFoundError` 로 종료(exit 1) — `JobManager.py:71-72`, `KooChainRun:2375-2377`. (단 `jobs.json` 자체는 손상/없을 때 경고 후 빈 상태로 진행 — `JobManager.py:294-297`.)
- **JSON 손상 DOE 는 자동 재실행 안 됨**: `json_corrupted` DOE 는 자동 대상에서 빠지고 경고만 출력됩니다. 단, `--does` 로 명시하면 해당 DOE 도 대상이 될 수 있습니다 (`--does` 분기는 손상 여부를 검사하지 않음 — `KooChainRun:2398-2399`).
- **Slurm 조회 실패 시 `UNKNOWN`**: `sacct`/`squeue` 가 실패하면 Slurm 상태가 `"UNKNOWN"` 으로 잡히며, step 도 완료가 아니면 `not_started` 로 분류되어 재실행 대상에 포함될 수 있습니다 — `JobManager.py:103`, `382-383`.
- **`--exclude-nodes auto` 는 외부 도구 의존**: `sacct`/`sinfo` 가 없거나 timeout 이면 노드 자동 감지가 생략되며, 제외 노드가 비면 그대로 진행됩니다 — `KooChainRun:2449-2469`.
- **일반 모드 재제출은 기존 스크립트 재사용**: `resubmit_does` 는 기존 `script_path`(또는 `run_doe_{NNN}.sh`)를 그대로 `sbatch` 합니다. 스크립트가 없으면 해당 DOE 는 건너뜀(`slurm script 없음`) — `JobManager.py:417-423`. 즉 입력 모델/조건이 바뀌었다면 `prepare` 재실행이 필요합니다.
- **--cleanup-stale 는 비가역**: 미완료 Run 디렉토리를 `rmtree` 로 영구 삭제합니다. 삭제 실패 시 경고만 출력하고 계속 진행 — `KooChainRun:2510-2514`.
- **sequential time_limit 확장 / mem=0**: sequential 모드는 노드당 DOE 수만큼 time_limit 을 곱하고(파티션 cap 적용), `exclusive` 일 때 `--mem=0` 으로 제출합니다 — `KooChainRun:2161-2173`, `2207`. 따라서 일반 모드와 자원 요청이 달라질 수 있습니다.
- **비대화형 실행**: 자동화(파이프/스크립트)에서는 `input()` 이 EOFError 를 일으켜 취소됩니다. `--force` 를 함께 사용해야 합니다 — `KooChainRun:2488-2490`.

---

## 6. 개발 현황

**구현됨.**

근거:
- `rerun` subparser 와 8개 인자/옵션(`test_dir`, `--dry-run`, `--force`, `--does`, `--exclude-nodes`, `--sequential`, `--nodes`, `--cleanup-stale`)이 모두 정의됨 — `KooChainRun:234-283`.
- 디스패치 분기 존재 — `KooChainRun:336-337`.
- 핸들러 `cmd_rerun` 가 상태 분석→대상 선정→노드 제외→dry-run/확인→cleanup→재제출까지 완전히 구현 — `KooChainRun:2360-2529`.
- 핵심 로직 `get_doe_status`/`resubmit_does` 가 상태 판정과 `sbatch` 재제출, `jobs.json` 갱신을 포함해 구현됨 — `Runner/JobManager.py:291-393`, `399-458`.
- sequential 재제출 경로 `_rerun_sequential` 가 노드 분배·스크립트 생성·제출까지 구현됨 — `KooChainRun:2096-2358`.
- 실제 테스트 디렉토리에 자동 생성된 `rerun.sh` 가 다수 존재하여 워크플로우에 통합되어 있음 (예: `Examples/HWWarrantyDropTest/Tests/Test_002_Full26_3Step/rerun.sh`, `Examples/ImpactTest/Tests/Test_Impact_Grid5x5/rerun.sh`).
