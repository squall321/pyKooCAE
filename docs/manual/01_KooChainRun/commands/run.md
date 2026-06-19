# KooChainRun run

> 단일 DOE 누적 파이프라인 실행 커맨드 레퍼런스
> 근거 소스: `KooChainRun` (CLI 진입점), `Runner/CumulativeScenarioRunner.py` (실제 실행 로직)

---

## 1. 목적 / 개요

`run`은 **하나의 DOE(Design Of Experiment) 인덱스**에 대한 누적 시뮬레이션 파이프라인
(`KooMeshModifier → LS-DYNA → dynain → 다음 step`)을 실행하는 커맨드입니다.

서브파서 정의(`KooChainRun:164-168`):

```
help        = 'Run single DOE pipeline on compute node'
description = 'Execute a single DOE cumulative pipeline (MeshModifier → LS-DYNA → dynain → next step). '
              'Designed to be called from within a Slurm job.'
```

즉 이 커맨드는 사용자가 직접 손으로 치기보다는 **Slurm 잡 스크립트 내부에서 호출되도록 설계**되었습니다.
실제로 `submit` / `rerun` 커맨드가 DOE별 Slurm 스크립트를 생성할 때 그 내부에
`KooChainRun run <config> --doe N` 명령을 써 넣습니다
(`KooChainRun:1155`, `1443`, `1445`, `1555`, `1557`, `1830`, `2271`).

내부적으로 `cmd_run()`은 `CumulativeScenarioRunner`를 생성하여 `run_all()`을 호출합니다
(`KooChainRun:1966-1972`).

---

## 2. 입력 옵션 · 인자

서브파서 정의 위치: `KooChainRun:164-195`

| 인자 / 옵션 | 형식 | 필수 | 기본값 | 설명 (근거 라인) |
|---|---|---|---|---|
| `config` | 위치 인자 (문자열) | 예 | — | `runner_config.json` 파일 경로. `KooChainRun:170-173` |
| `--doe` | `int` | **예** (`required=True`) | — | 실행할 DOE 인덱스 (1-based). `KooChainRun:174-179` |
| `--resume` | 플래그 (`store_true`) | 아니오 | `False` | 체크포인트에서 이어 실행. `KooChainRun:180-184` (주의사항 참조) |
| `--skip-koomeshmodifier` | 플래그 (`store_true`) | 아니오 | `False` | KooMeshModifier 실행 생략 (batch 사전 생성 모드). `KooChainRun:185-189` |
| `--pregenerated-dir` | 문자열 | 아니오 | `None` | 사전 생성된 `DropSet.k`(등) 파일이 있는 디렉토리 경로. `KooChainRun:190-195` |

`config` 경로는 `cmd_run()`에서 `Path(args.config).resolve()`로 절대경로화되며,
존재하지 않으면 에러 출력 후 `sys.exit(1)` 합니다 (`KooChainRun:1945-1949`).

---

## 3. 사용 예제

### 3.1 가장 기본형 (단일 DOE)

`submit`이 생성한 Slurm 스크립트의 실제 호출부
(`Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick/output/slurm_scripts/run_doe_002.sh:56`):

```bash
/data/SmartTwinPreprocessor/bin/KooChainRun run \
  /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick/runner_config.json \
  --doe 2
```

### 3.2 batch 사전 생성 모드 (KooMeshModifier 생략)

헤드노드에서 KooMeshModifier를 일괄로 미리 돌린 뒤, 컴퓨트 노드에서는 LS-DYNA만 돌리는 모드.
실제 호출부 (`Examples/HWWarrantyDropTest/Tests/Test_008_Fibonacci_100_v2/output/slurm_scripts/run_doe_026.sh:20`):

```bash
/data/SmartTwinPreprocessor/bin/KooChainRun run \
  /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_008_Fibonacci_100_v2/runner_config.json \
  --doe 26 \
  --skip-koomeshmodifier \
  --pregenerated-dir /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_008_Fibonacci_100_v2/output/pregenerated
```

`--skip-koomeshmodifier`와 `--pregenerated-dir`가 **둘 다** 주어지면, Runner는
`<pregenerated-dir>/Run_<doe>` 폴더에서 사전 생성된 메시를 복사해 사용합니다
(`CumulativeScenarioRunner.py:926`, `1607`).

### 3.3 Slurm 잡 스크립트 내부 맥락

`run`은 Slurm 스크립트 안에서 NFS 가용성 점검 / orphan Apptainer 정리 / stale lock 정리 등을
거친 뒤 마지막에 호출됩니다 (`run_doe_002.sh` 발췌):

```bash
# ... (노드 health check, NFS 대기, lock 정리 생략) ...
/data/SmartTwinPreprocessor/bin/KooChainRun run \
  .../runner_config.json --doe 2

EXIT_CODE=$?
echo "Exit code: $EXIT_CODE"
exit $EXIT_CODE
```

DOE 실패 시 `run`은 `sys.exit(1)`을 반환하므로(아래 참조) `EXIT_CODE`로 성공/실패가 전달됩니다.

---

## 4. 동작 원리 (코드 근거)

### 4.1 진입 흐름

1. `main()`의 디스패치: `args.command == 'run'`이면 `cmd_run(args)` 호출
   (`KooChainRun:328-329`).
2. `cmd_run()`:
   - config 경로 resolve 및 존재 확인 (`KooChainRun:1945-1949`).
   - `--skip-koomeshmodifier`, `--pregenerated-dir`를 `getattr`로 안전하게 읽음
     (`KooChainRun:1951-1952`).
   - 실행 정보 헤더 출력 (`KooChainRun:1954-1963`).
   - `CumulativeScenarioRunner(config, doe_filter=args.doe, skip_koomeshmodifier=..., pregenerated_dir=...)`
     생성 후 `runner.run_all()` 호출 (`KooChainRun:1966-1972`).
   - 성공 시 완료 메시지, 실패 시 `sys.exit(1)`; 예외 시 traceback 출력 후 `sys.exit(1)`
     (`KooChainRun:1973-1982`).

### 4.2 Runner 측 처리

- 생성자에서 `doe_filter`, `skip_koomeshmodifier`, `pregenerated_dir`를 보관
  (`CumulativeScenarioRunner.py:382-384`).
- `--doe N`이 지정되면(`doe_filter is not None`) **DOE별 개별 체크포인트/로그 파일**을 사용하여
  동시 write 경합을 방지합니다:
  - 체크포인트: `checkpoint_doe_<NNN>.json` (`CumulativeScenarioRunner.py:392-394`).
  - 로그: `runner_doe_<NNN>.log` (`CumulativeScenarioRunner.py:406-407`).
- `run_all()`:
  - `doe_filter`가 있으면 `doe_range = [self.doe_filter]`로 **해당 DOE만** 실행
    (`CumulativeScenarioRunner.py:788`).
  - `doe_filter` 모드에서는 **체크포인트를 무시하고 step 1부터** 실행
    (`CumulativeScenarioRunner.py:792-794`).
  - 각 step을 `run_single_step()`으로 실행, 실패 시 `retry_on_failure` / `max_retries`
    설정에 따라 재시도 (`CumulativeScenarioRunner.py:806-831`).
  - 이미 `completed`이고 `Output/dynain`이 존재하는 step은 스킵 (rerun 효율화)
    (`CumulativeScenarioRunner.py:910-919`).
- 사전 생성 모드 분기: `self.skip_koomeshmodifier and self.pregenerated_dir`이면 Runner가
  `Run_<run_id>` 폴더를 직접 만들고 KooMeshModifier 호출 대신 메시를 복사
  (`CumulativeScenarioRunner.py:926-935`, 복사 소스 경로 `1607`).
- 종료 시 Apptainer tmpdir를 명시적으로 정리(orphan squashfuse/sandbox 방지)
  (`CumulativeScenarioRunner.py:843-850`).

---

## 5. 주의사항 · 한계

- **`--resume`의 실제 효력 — 확인 필요.**
  서브파서에는 `--resume` 플래그가 정의되어 있으나(`KooChainRun:180-184`),
  `cmd_run()`은 이를 헤더 출력에만 사용하고(`KooChainRun:1959`)
  `CumulativeScenarioRunner` 생성자에는 **전달하지 않습니다**(`KooChainRun:1966-1971`).
  또한 `--doe`가 항상 필수이고, `doe_filter`가 지정되면 `run_all()`은
  **체크포인트를 무시하고 step 1부터** 시작합니다(`CumulativeScenarioRunner.py:792-794`).
  따라서 `run` 커맨드 경로에서 `--resume`는 사실상 동작에 영향을 주지 않는 것으로 보입니다.
  (참고: 별도 `CumulativeScenarioRunner.main()` 진입점도 `--resume`를 받기만 하고
  생성자에 넘기지 않음 — `CumulativeScenarioRunner.py:1665`, `1677-1682`.)

- `--doe`는 **필수**입니다(`required=True`, `KooChainRun:177`). 생략 시 argparse 에러로 종료됩니다.

- 컴퓨트 노드 실행 전제 설계입니다. NFS 가시성 / 라이선스 서버 / Apptainer tmpdir 등은
  호출하는 Slurm 스크립트 쪽(또는 `runner_config.json`의 `environment`)에서 보장되어야 합니다.

- batch 사전 생성 모드는 `--skip-koomeshmodifier`와 `--pregenerated-dir`를 **함께** 줘야
  메시 복사 분기를 탑니다(`CumulativeScenarioRunner.py:926`). 한쪽만 주면 의도와 다르게
  동작할 수 있습니다(확인 필요 — `--skip-koomeshmodifier` 단독 시의 폴백 경로는 본문에서 미확인).

- 실패한 DOE는 `sys.exit(1)`로 종료되며, 시나리오 status 집계도 함께 갱신됩니다
  (`CumulativeScenarioRunner.py:827-829`).

---

## 6. 개발 현황

**구현됨 (단, 일부 옵션 미연결).**

근거:
- `run` 서브파서와 `cmd_run()`이 정의되어 디스패치까지 연결됨
  (`KooChainRun:164-195`, `328-329`, `1941-1982`).
- 실제 Slurm 스크립트들이 이 커맨드를 사용 중이며 작동 사례가 Examples에 존재함
  (예: `Examples/HWWarrantyDropTest/Tests/Test_010_Sequential_Quick/output/slurm_scripts/run_doe_002.sh:56`,
  `Test_008_Fibonacci_100_v2/output/slurm_scripts/run_doe_026.sh:20`).
- 단, `--resume` 옵션은 정의만 되어 있고 Runner로 전달되지 않아 **부분 구현/미연결** 상태
  (`KooChainRun:1966-1971`, 5절 참조).
