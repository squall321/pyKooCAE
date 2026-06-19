# KooChainRun stop

## 1. 목적 / 개요

`KooChainRun stop`은 테스트 디렉토리의 `jobs.json`에 기록된 **제출된 모든 Slurm 작업을 일괄 취소**하는 커맨드입니다.

서브파서 정의(`KooChainRun:219-223`)에 명시된 설명은 다음과 같습니다.

- help: `제출된 모든 작업 취소`
- description: `jobs.json에 저장된 Slurm 작업을 모두 취소합니다`

내부적으로는 `Runner.JobManager.JobManager.cancel_all_jobs()`를 호출하여, 각 DOE에 매핑된 `job_id`를 `scancel`로 취소하고 그 결과를 집계해 출력합니다(`KooChainRun:2061-2093`).

특정 DOE만 골라서 취소하는 옵션은 제공하지 않습니다. 항상 `jobs.json`에 있는 전체 작업을 대상으로 합니다.

## 2. 입력 옵션 · 인자 (표)

`stop` 서브파서는 위치 인자 1개만 정의되어 있고, 별도의 플래그(옵션)는 없습니다(`KooChainRun:224-229`).

| 인자 / 옵션 | 종류 | 필수 | 기본값 | 설명 (코드 근거) |
|---|---|---|---|---|
| `test_dir` | 위치 인자 (`nargs='?'`) | 아니오 | `.` (현재 디렉토리) | 테스트 디렉토리 경로. `jobs.json`과 `runner_config.json`이 위치한 디렉토리 (`KooChainRun:224-229`) |

> 참고: `--force`, `--dry-run`, `--does` 같은 옵션은 `rerun` 커맨드에는 있지만 `stop`에는 **없습니다**. `stop`은 확인 절차 없이 즉시 전체 취소를 수행합니다(코드상 확인 프롬프트 부재, `KooChainRun:2061-2093`).

## 3. 사용 예제

### 3.1 현재 디렉토리의 작업 전체 취소

테스트 디렉토리로 이동한 뒤 인자 없이 실행하면 현재 디렉토리(`.`)가 대상이 됩니다.

```bash
KooChainRun stop
```

### 3.2 테스트 디렉토리를 명시하여 취소

```bash
KooChainRun stop Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick
```

### 3.3 대상이 되는 `jobs.json` 구조 (예시 발췌)

`stop`은 아래와 같은 `jobs.json`의 `jobs` 항목을 순회하여 각 `job_id`를 취소합니다. 아래는 `Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick/jobs.json`에서 발췌한 실제 구조입니다(가공 최소화).

```json
{
  "project_name": "Test_010_Sequential_Quick",
  "doe_count": 10,
  "jobs": {
    "1": {
      "job_id": "3127",
      "job_name": "Test_010_Sequential_Quick_SEQ000",
      "status": "submitted",
      "sequential_slot": 0
    },
    "3": {
      "job_id": "3127",
      "job_name": "Test_010_Sequential_Quick_SEQ000",
      "status": "submitted",
      "sequential_slot": 0
    }
  }
}
```

### 3.4 예상 출력 형식

`cmd_stop`이 콘솔에 출력하는 형식(`KooChainRun:2068-2093`)은 다음과 같습니다.

```
================================================================================
KooChainRun - 작업 취소
================================================================================

  DOE   1: 취소 완료 (job 3127)
  DOE   3: 이미 종료됨 (COMPLETED)
  DOE   5: 취소 실패 - <stderr 내용>

취소: 1개 / 이미 종료: 1개 / 실패: 1개
```

## 4. 동작 원리 (코드 근거)

처리 흐름은 다음과 같습니다.

1. **디스패치** — `args.command == 'stop'`일 때 `cmd_stop(args)` 호출 (`KooChainRun:334-335`).
2. **JobManager 생성** — `test_dir`를 절대경로로 변환 후 `JobManager(str(test_dir))` 생성 (`KooChainRun:2065-2066`). 생성자에서 `jobs.json` / `runner_config.json` 경로를 결정 (`Runner/JobManager.py:24-27`).
3. **전체 취소 호출** — `manager.cancel_all_jobs()` 실행. `jobs.json`이 없거나 비어 있으면 `FileNotFoundError`가 발생하며, `cmd_stop`은 이를 잡아 `Error: ...` 출력 후 `sys.exit(1)` (`KooChainRun:2072-2076`, `Runner/JobManager.py:29-36`).
4. **DOE별 취소 로직** (`Runner/JobManager.py:240-285`):
   - `jobs_data["jobs"]`의 각 항목을 순회하며 `job_id`를 추출. `job_id`가 없으면 `cancel_result = "no_job_id"` (`JobManager.py:245-251`).
   - `_query_slurm_status(job_id)`로 현재 상태 조회. 내부적으로 `sacct -j <id> --format=State --noheader --parsable2`를 먼저 시도하고, 실패 시 `squeue`로 폴백하며, 둘 다 실패하면 `"UNKNOWN"` 반환 (`JobManager.py:76-103`).
   - 상태가 `COMPLETED, FAILED, CANCELLED, TIMEOUT, NODE_FAIL, OUT_OF_MEMORY, UNKNOWN` 중 하나면 이미 종료된 것으로 보고 `scancel`을 호출하지 않음 → `cancel_result = "already_done"` (`JobManager.py:256-263`).
   - 그 외 상태(예: RUNNING, PENDING)면 `scancel <job_id>` 실행. 반환코드 0이면 `"success"`로 기록하고 `jobs.json`의 해당 작업 `status`를 `"cancelled"`로 갱신, 0이 아니면 `"error"`(stderr 포함) (`JobManager.py:265-281`).
5. **jobs.json 갱신** — 변경된 상태를 atomic write(임시파일 → rename, `.bak` 백업)로 저장 (`JobManager.py:283-284`, `48-67`).
6. **결과 집계 및 출력** — `cmd_stop`에서 `success / already_done / error` 개수를 집계하고, DOE 인덱스 오름차순으로 각 결과를 출력한 뒤 요약 라인을 출력 (`KooChainRun:2078-2093`).

## 5. 주의사항 · 한계

- **전체 취소만 가능**: 특정 DOE/작업만 선택 취소하는 옵션이 없습니다. `jobs.json`의 모든 작업이 대상입니다(`stop` 서브파서에 위치 인자 외 옵션 없음, `KooChainRun:224-229`).
- **확인 절차 없음**: `--force`나 확인 프롬프트가 없어 실행 즉시 취소가 진행됩니다(`cmd_stop`에 확인 로직 부재, `KooChainRun:2061-2093`).
- **`jobs.json` 의존**: `jobs.json`이 없거나 비어 있으면 `Error` 후 종료(`sys.exit(1)`)합니다(`JobManager.py:29-36`, `KooChainRun:2074-2076`). `jobs.json`은 submit 단계에서 생성됩니다.
- **상태 판정은 Slurm 가용성에 의존**: `sacct`/`squeue`가 모두 실패하면 상태가 `"UNKNOWN"`으로 처리되어 `already_done`으로 분류되고 `scancel`이 호출되지 않습니다(`JobManager.py:89-103`, `256-263`). 즉 Slurm CLI 접근이 불가능한 환경에서는 실제 실행 중인 작업이 취소되지 않을 수 있습니다 — **확인 필요**(실제 클러스터 환경에서의 거동).
- **Sequential 모드의 job_id 공유**: 시퀀셜 제출에서는 여러 DOE가 동일한 `job_id`(예: 위 예시의 `3127`)를 공유합니다(`jobs.json` 발췌 참조). 이 경우 동일 `job_id`에 대해 `scancel`이 중복 호출될 수 있으나, Slurm은 동일 작업의 중복 취소를 허용하므로 동작상 문제는 없습니다 — **확인 필요**(중복 호출 시 결과 분류가 success/already_done 중 무엇으로 기록되는지).

## 6. 개발 현황

**구현됨**

근거:
- `stop` 서브파서가 정의되어 있고 위치 인자 `test_dir`을 받습니다(`KooChainRun:219-229`).
- 디스패처가 `cmd_stop`으로 연결되어 있습니다(`KooChainRun:334-335`).
- `cmd_stop`이 `JobManager.cancel_all_jobs()`를 호출하고 결과를 출력합니다(`KooChainRun:2061-2093`).
- `cancel_all_jobs()`가 `scancel`을 실제로 실행하고 `jobs.json`을 갱신하는 로직이 구현되어 있습니다(`Runner/JobManager.py:240-285`).
