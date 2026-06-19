# KooChainRun diagnose

## 1. 목적 / 개요

`KooChainRun diagnose` 는 테스트 디렉토리(`runner_config.json` + `jobs.json` 이 있는 곳)에서 **완료되지 않은 DOE 들의 실패 원인을 분류·요약**해 주는 커맨드이다.

서브파서 정의상 help 는 "실패 DOE 원인 진단", description 은 "실패한 DOE들의 원인을 분석합니다 (라이선스, 타임아웃, 메모리 등)" 이다 (KooChainRun:288-292).

내부적으로 `JobManager.diagnose_failures()` 를 호출하여 각 DOE 의 상태(`get_doe_status()`)와 Slurm 로그 파일 내용을 조합해 원인(cause)을 추정하고, 원인별로 그룹화하여 해당 DOE 번호 목록과 로그 발췌(최대 3줄)를 화면에 출력한다 (KooChainRun:2661-2716, Runner/JobManager.py:464-520).

`completed`(완료) 또는 `running`(실행 중) 상태의 DOE 는 진단 대상에서 제외되며, 그 외(실패/중단/미시작) DOE 만 분석한다 (Runner/JobManager.py:472-474).

---

## 2. 입력 옵션 · 인자 (표)

| 인자 / 옵션 | 형식 | 필수 여부 | 기본값 | 설명 | 코드 근거 |
|---|---|---|---|---|---|
| `test_dir` | 위치 인자 (positional), `nargs='?'` | 선택 | `.` (현재 디렉토리) | 진단할 테스트 디렉토리 경로. `jobs.json` 과 `runner_config.json` 이 들어 있는 디렉토리를 가리켜야 한다. | KooChainRun:293-298 |

서브파서 등록 (KooChainRun:288-298):

```text
diagnose_parser = subparsers.add_parser(
    'diagnose',
    help='실패 DOE 원인 진단',
    description='실패한 DOE들의 원인을 분석합니다 (라이선스, 타임아웃, 메모리 등)'
)
diagnose_parser.add_argument(
    'test_dir',
    nargs='?',
    default='.',
    help='테스트 디렉토리 경로 (기본: 현재 디렉토리)'
)
```

> 참고: `diagnose` 의 인자는 `test_dir` 단 하나이다. 다른 커맨드(`status`, `postprocess`)가 받는 `runner_config.json` 경로가 아니라 **디렉토리** 를 받는다는 점에 유의한다. `JobManager(str(test_dir))` 가 그 디렉토리 안에서 `jobs.json` 과 `runner_config.json` 을 자동으로 찾는다 (KooChainRun:2665-2666, Runner/JobManager.py:24-27).

---

## 3. 사용 예제

### 3-1. 실제 Examples 스크립트 (`diagnose.sh`)

`Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick/diagnose.sh` 전체:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOOCR=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/scenario.json'))['environment']['koochainrun_path'])")
"$KOOCR" diagnose "$SCRIPT_DIR"
```

여기서 `test_dir` 로 스크립트가 위치한 디렉토리(`$SCRIPT_DIR`)를 그대로 넘긴다. 해당 디렉토리에는 `jobs.json`, `runner_config.json`, `output/` 이 함께 존재한다.

### 3-2. 직접 CLI 호출

```bash
# 현재 디렉토리를 진단 (test_dir 생략 → 기본값 ".")
KooChainRun diagnose

# 특정 테스트 디렉토리를 진단
KooChainRun diagnose /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick
```

### 3-3. 실제 출력 형태

`cmd_diagnose` 가 생성하는 출력 형태 (코드 기준, KooChainRun:2668-2716):

```text
================================================================================
KooChainRun - 실패 원인 진단
================================================================================

총 실패/미완료 DOE: <N>개

  [라이선스 에러] 2개
    DOE: [3, 7]
    > <log_excerpt 1행>
    > <log_excerpt 2행>
    > <log_excerpt 3행>

  [타임아웃 (KooMeshModifier/LS-DYNA)] 1개
    DOE: [5]
    > <log_excerpt 1행>
```

- 실패한 DOE 가 하나도 없으면 `"\n실패한 DOE가 없습니다."` 만 출력하고 종료한다 (KooChainRun:2678-2680).
- 원인은 코드의 `cause_labels` 매핑에 따라 한글 라벨로 표시된다. 매핑에 없는 원인은 원본 cause 문자열을 그대로 출력한다 (KooChainRun:2688-2706).

---

## 4. 동작 원리 (코드 근거)

커맨드 디스패치는 `args.command == 'diagnose'` 일 때 `cmd_diagnose(args)` 를 호출한다 (KooChainRun:338-339).

### 4-1. `cmd_diagnose` (KooChainRun:2661-2716)

1. `JobManager(str(test_dir))` 인스턴스를 생성한다. `test_dir` 은 `Path(args.test_dir).resolve()` 로 절대경로화된다 (KooChainRun:2665-2666).
2. `manager.diagnose_failures()` 를 호출한다. `FileNotFoundError`(예: `jobs.json`/`runner_config.json` 부재) 발생 시 에러 메시지를 출력하고 `sys.exit(1)` 한다 (KooChainRun:2672-2676).
3. 반환된 진단 리스트를 `cause` 키로 그룹화(`by_cause`)한다 (KooChainRun:2683-2686).
4. 원인별로 `[라벨] N개` + `DOE: [...]` 을 출력하고, 그 그룹 첫 DOE 의 `log_excerpt` 중 최대 3줄(각 줄 최대 120자)을 `>` 접두로 표시한다 (KooChainRun:2704-2716).

### 4-2. `JobManager.diagnose_failures` (Runner/JobManager.py:464-520)

핵심 분류 로직은 JobManager 안에 있다.

1. `get_doe_status()` 로 모든 DOE 의 상태 맵을 얻고, `load_runner_config()` 로 `output_dir` 을 읽는다 (Runner/JobManager.py:466-468).
2. 상태가 `completed` / `running` 인 DOE 는 건너뛴다 (Runner/JobManager.py:472-474).
3. `_find_log_file(output_dir, doe_idx)` 로 해당 DOE 의 가장 최근 로그 파일을 찾는다. 패턴은 `{output_dir}/slurm_scripts/doe_{doe_idx:03d}_*.log` 이며, 수정시각 내림차순 정렬 후 첫 파일을 사용한다 (Runner/JobManager.py:191-195).
4. 로그가 있으면 `_get_log_error_excerpt()` 로 발췌를 만들고, 로그 본문을 소문자로 읽어 **세부 원인을 우선순위 if/elif 로 분류**한다 (Runner/JobManager.py:480-507):
   - `lstc_file` / `license` / `license checkout` 포함 → `license_error`
   - `mpi_abort` 포함 + `license` 미포함 → `mpi_error`
   - `timed out` 또는 `timeout` 포함 → `timeout`
   - `no space left` 포함 → `disk_full`
   - `out of memory` 또는 `oom` 포함 → `out_of_memory`
   - `squashfuse` 또는 `libfuse` 포함 → `apptainer_error`
   - 위에 안 걸리고 `slurm_state == "CANCELLED"` → `cancelled`
   - `slurm_state == "TIMEOUT"` → `slurm_timeout`
   - `status == "not_started"` → `not_started`
   - 그 외에는 기본값 `cause = info["status"]` 유지 (Runner/JobManager.py:478)
5. 각 DOE 에 대해 `doe / status / slurm_state / cause / steps_completed / steps_total / log_excerpt / job_id` 딕셔너리를 만들어 리스트에 추가하고 반환한다 (Runner/JobManager.py:509-518).

### 4-3. 로그 발췌 추출 `_get_log_error_excerpt` (Runner/JobManager.py:214-234)

로그 줄 중 `[ERROR]`, `FATAL`, `MPI_ABORT`, `Error termination` 키워드가 포함된 줄을 찾아, 그 줄의 앞 1줄 ~ 뒤 3줄 범위를 발췌로 모은다. 누적 줄 수가 10줄을 넘으면 중단한다. 발췌가 없으면 빈 문자열을 반환한다.

### 4-4. DOE 상태 기준 `get_doe_status` (Runner/JobManager.py:291-393)

진단의 1차 입력인 DOE 상태 분류는 `jobs.json`(작업 ID) → Slurm 상태(`sacct`/`squeue`) 조회와 `simulation_index.json` 의 step별 status 를 조합해 결정된다. 분류 결과는 `completed / running / killed / license_error / failed / not_started` 중 하나이며(Runner/JobManager.py:367-383), 이 status 가 `diagnose_failures` 에서 cause 의 기본값으로 쓰인다.

> 참고: `_query_slurm_status` 는 먼저 `sacct -j <job_id> --format=State` 를 시도하고, 실패 시 `squeue -j <job_id>` 로 fallback 하며, 둘 다 실패하면 `"UNKNOWN"` 을 반환한다 (Runner/JobManager.py:76-103). 따라서 Slurm CLI 가 없는 환경에서는 slurm_state 기반 분류(`cancelled`, `slurm_timeout` 등)가 제대로 동작하지 않을 수 있다.

---

## 5. 주의사항 · 한계

- **디렉토리 인자**: `test_dir` 은 파일이 아니라 디렉토리이다. 이 디렉토리에 `jobs.json` 과 `runner_config.json` 이 없으면 `FileNotFoundError` 로 `sys.exit(1)` 한다 (KooChainRun:2672-2676, Runner/JobManager.py:31-32, 71-72). 단, `get_doe_status` 내부에서 `jobs.json` 로드 실패는 경고 후 빈 상태로 진행하므로(Runner/JobManager.py:293-297), 실제로 진단을 막는 것은 주로 `runner_config.json` 부재이다.
- **로그 기반 추정**: 세부 원인은 Slurm 로그(`{output_dir}/slurm_scripts/doe_NNN_*.log`)의 **문자열 매칭**으로 추정한다. 로그 파일이 없으면(예: 작업이 제출조차 안 됨) cause 는 `get_doe_status` 가 준 status 기본값에 머문다 (Runner/JobManager.py:476-478).
- **단순 우선순위 매칭의 한계**: 분류는 위→아래 우선순위 if/elif 이다. 예컨대 라이선스 문자열과 메모리 문자열이 한 로그에 함께 있으면 먼저 매칭되는 `license_error` 로 분류된다 (Runner/JobManager.py:488-505).
- **로그 패턴 한정**: 발췌 추출은 `[ERROR]`/`FATAL`/`MPI_ABORT`/`Error termination` 키워드에만 반응한다. 이 패턴이 없는 실패 로그는 발췌가 비어 출력에 `>` 줄이 나타나지 않는다 (Runner/JobManager.py:222-231).
- **읽기 전용**: `diagnose` 는 진단 결과를 출력만 한다. 재제출이나 정리 동작은 하지 않는다(재실행은 별도 `rerun` 커맨드). cmd_diagnose 함수에 파일 쓰기·작업 제출 코드가 없다 (KooChainRun:2661-2716).
- **출력 절단**: 로그 발췌는 그룹별로 첫 DOE 의 것만, 최대 3줄·줄당 120자로 잘려 표시된다. 전체 로그 확인은 직접 로그 파일을 열어야 한다 (KooChainRun:2710-2715).

---

## 6. 개발 현황

**구현됨**

- 근거: `diagnose` 서브파서가 정의되어 있고(KooChainRun:288-298), 디스패치(KooChainRun:338-339)에서 `cmd_diagnose` 를 호출하며, `cmd_diagnose` 가 실제로 `JobManager.diagnose_failures()` 결과를 원인별로 그룹화·출력한다 (KooChainRun:2661-2716).
- 핵심 분류·로그 발췌·DOE 상태 조회 로직(`diagnose_failures`, `_find_log_file`, `_get_log_error_excerpt`, `get_doe_status`)이 모두 `Runner/JobManager.py` 에 구현되어 있다 (Runner/JobManager.py:464-520, 191-234, 291-393).
- 실제 사용 예 스크립트(`diagnose.sh`)가 Examples 에 존재한다 (`Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick/diagnose.sh`).
