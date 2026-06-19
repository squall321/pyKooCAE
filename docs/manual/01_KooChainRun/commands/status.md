# KooChainRun status

## 1. 목적 / 개요

`KooChainRun status` 는 현재 사용자가 제출한 시뮬레이션 작업의 실행 상태를 확인하는 커맨드이다.

핵심 동작은 Slurm 큐(`squeue -u $USER`) 출력을 표시하는 것이며, 선택적으로 `runner_config.json` 경로를 인자로 받아 해당 설정 파일의 존재 여부를 확인한다.

서브파서 정의상 description 은 "Monitor progress of running simulations" 이다 (KooChainRun:148). 다만 아래 4) 동작 원리와 6) 개발 현황에서 설명하듯, `runner_config.json` 기반의 상세 진행률 모니터링은 현재 코드에서 미구현 상태(플레이스홀더)이다.

---

## 2. 입력 옵션 · 인자 (표)

| 인자 / 옵션 | 형식 | 필수 여부 | 기본값 | 설명 | 코드 근거 |
|---|---|---|---|---|---|
| `config` | 위치 인자 (positional), `nargs='?'` | 선택 | 없음 (생략 가능) | `runner_config.json` 파일 경로. 생략 가능 | KooChainRun:150-154 |
| `--watch` | 플래그 (`action='store_true'`) | 선택 | `False` | 도움말상 "Continuously monitor status (update every 60s)". **단, 코드에서 참조되지 않아 실제 동작 없음 (확인 필요/미구현)** | KooChainRun:155-159 |

서브파서 등록:

```text
status_parser = subparsers.add_parser(
    'status',
    help='Check execution status',
    description='Monitor progress of running simulations'
)
```
(KooChainRun:145-149)

> 참고: `--watch` 플래그는 `add_argument` 로 정의되어 있으나(KooChainRun:155-159), 소스 전체에서 `args.watch` 또는 `watch` 를 참조하는 코드가 존재하지 않는다(`grep "watch"` 결과 KooChainRun:156 한 줄만 매치). 따라서 `--watch` 를 지정해도 60초 주기 반복 갱신은 수행되지 않는다.

---

## 3. 사용 예제

### 3-1. 인자 없이 Slurm 큐만 확인

`Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/README.md:101-102` 발췌:

```bash
# 3. 진행 상황 확인
KooChainRun status
```

### 3-2. config 경로 지정

`Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/README.md:242` 발췌:

```bash
KooChainRun status runner_config.json
```

`Examples/HWWarrantyDropTest/QUICK_START_GUIDE.md:137` 발췌 (제출 직후 안내 메시지):

```text
Next steps:
  Check status:    KooChainRun status /path/to/runner_config.json
  Collect results: KooChainRun collect /path/to/runner_config.json
```

### 3-3. 실제 출력 형태

`cmd_status` 함수가 생성하는 출력 형태(코드 기준, KooChainRun:1987-2011):

```text
================================================================================
KooChainRun - Execution Status
================================================================================

📊 Slurm Queue Status:
--------------------------------------------------------------------------------
<squeue -u $USER 출력>

Config: /절대경로/runner_config.json
(Detailed progress monitoring coming soon)

Commands:
  squeue -u $USER              # Check Slurm jobs
  scancel <job_id>             # Cancel a job
  find RUNDIR -name '*.lock'   # Count completed cases
```

config 인자를 생략하면 위 출력에서 `Config: ...` 및 `(Detailed progress monitoring coming soon)` 두 줄이 나타나지 않는다.

---

## 4. 동작 원리 (코드 근거)

`cmd_status(args)` (KooChainRun:1985) 의 실행 흐름:

1. **헤더 출력**: "KooChainRun - Execution Status" 배너를 출력한다 (KooChainRun:1987-1990).
2. **Slurm 큐 조회**: `os.system("squeue -u $USER")` 를 직접 호출하여 현재 사용자의 Slurm 작업 목록을 그대로 표준 출력에 흘려보낸다 (KooChainRun:1993-1996). 즉 큐 상태는 셸 명령 출력을 그대로 보여주는 방식이다.
3. **config 처리 분기** (KooChainRun:1998-2005):
   - `args.config` 가 주어지면 `Path(args.config).resolve()` 로 절대경로화한다 (KooChainRun:1999).
   - 파일이 존재하면 `Config: <경로>` 와 함께 `"(Detailed progress monitoring coming soon)"` 만 출력한다. 실제 `runner_config.json` 파싱·진행률 계산은 `# TODO` 주석으로 남아 있다 (KooChainRun:2001-2003).
   - 파일이 없으면 경고 `⚠️  Warning: Config file not found: <경로>` 를 출력한다 (KooChainRun:2004-2005).
4. **수동 명령 안내**: 사용자가 직접 활용할 수 있는 보조 명령(`squeue`, `scancel`, `find ... -name '*.lock'`)을 안내한다 (KooChainRun:2008-2011).

커맨드 디스패치는 `args.command == 'status'` 일 때 `cmd_status(args)` 를 호출한다 (KooChainRun:330-331).

> 주목할 점: 이 함수는 `runner_config.json` 의 내용을 읽지 않으며(존재 여부만 확인), `--watch` 인자도 사용하지 않는다. 실질적 정보 제공은 `squeue -u $USER` 출력에 의존한다.

---

## 5. 주의사항 · 한계

- **상세 진행률 미구현**: config 를 넘겨도 DOE/스텝별 진행률, 완료 케이스 수 등 상세 정보는 표시되지 않는다. 코드에 `(Detailed progress monitoring coming soon)` 및 `# TODO` 로 명시되어 있다 (KooChainRun:2001-2003).
- **`--watch` 무동작**: `--watch` 플래그는 정의만 되어 있고 코드에서 참조되지 않아, 지정해도 자동 반복 갱신이 일어나지 않는다 (확인 필요 → grep 결과상 미사용). 실시간 모니터링이 필요하면 셸에서 `watch -n 60 squeue -u $USER` 등을 직접 사용해야 한다.
- **Slurm 의존**: `squeue` 가 PATH 에 없는 환경(예: 로그인 노드가 아닌 곳, Slurm 미설치 환경)에서는 큐 출력이 비어 있거나 오류 메시지가 표시될 수 있다. `os.system` 사용으로 오류는 셸 표준 오류로 그대로 노출된다.
- **상태 추적 파일과 무관**: 다른 커맨드(`stop` 등)는 `JobManager` 와 `jobs.json` 을 사용하지만, `status` 는 이를 읽지 않는다. 즉 제출 시 생성되는 `jobs.json`/`simulation_index.json`/`checkpoint.json` 정보를 반영하지 않는다.

---

## 6. 개발 현황

**부분구현**

- 구현됨: Slurm 큐 출력(`squeue -u $USER`), config 파일 존재 여부 확인 및 경고, 보조 명령 안내 (KooChainRun:1985-2011).
- 미구현: config 기반 상세 진행 모니터링(`# TODO`, KooChainRun:2001-2003), `--watch` 60초 주기 자동 갱신(플래그만 정의, 코드 미참조; KooChainRun:155-159, grep 결과 미사용).
