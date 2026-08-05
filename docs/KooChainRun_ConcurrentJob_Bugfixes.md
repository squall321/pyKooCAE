# KooChainRun 병렬 잡 동시 실행 버그픽스 보고서

**작성일**: 2026-04-03 ~ 04-04
**대상 버전**: KooChainRun 1.1.0 (v8)
**수정 파일**: `KooChainRun`, `Runner/CumulativeScenarioRunner.py`, `Runner/JobManager.py`

---

## 1. 문제 현상

Cumulative 모드로 대규모 DOE(100~300개) 잡을 Slurm에 제출할 때 다음 현상이 복합적으로 발생:

| 현상 | 설명 |
|------|------|
| **launch failed requeued held** | 첫 배치(~23개) 완료 후 다음 배치 전체가 실행 불가 |
| **KooMeshModifier 미실행** | Slurm 로그 파일조차 생성 안 됨 (Python 이전에 실패) |
| **노드 장애 연쇄** | 1개 노드 죽으면 해당 노드에 모든 후속 잡이 순차 배정 → 전부 실패 |
| **simulation_index.json 데이터 손실** | 마지막 DOE 데이터만 남고 나머지 증발 |
| **status 부정확** | 실패해도 completed 표시, 또는 running 상태로 잔존 |
| **잘못된 체인** | 멀티스텝 DOE에서 이전 step의 dynain이 아닌 원본 모델로 실행 |

---

## 2. 원인 분석

### A. NFS 관련 (클러스터 레벨)

#### A-1. rsync 동시 Burst → NFS 포화

**파일**: `KooChainRun` (scratch cleanup), `CumulativeScenarioRunner.py` (stage-out)

잡 완료 시점에 동시 rsync가 NFS를 포화시켜 다음 배치 잡이 Slurm 배치 스크립트를 읽지 못함.

```
23개 잡 동시 완료
  → Bash cleanup rsync 23개 동시 (scratch 모드)
  → Python stage-out rsync 23개 동시 (non-scratch 모드)
  → NFS I/O 포화
  → slurmstepd: run_doe_XXX.sh (NFS) 읽기 실패
  → "launch failed" → requeued → held
```

#### A-2. 공유 파일 동시 NFS 메타데이터 폭주

**파일**: `CumulativeScenarioRunner.py`

| 파일 | 문제 |
|------|------|
| `runner.log` | 100개 잡이 동일 파일에 락 없이 동시 append |
| `checkpoint.json` | 락 없는 atomic write 100개 동시 실행 → NFS rename 충돌 |
| `simulation_index.json.lock` | `open('w')` 시 동시 truncate → NFS 캐시 무효화 폭풍 |

#### A-3. NFS stale lock → 전체 잡 무한 대기

**파일**: `CumulativeScenarioRunner.py` (모든 flock 사용처)

노드가 `flock(LOCK_EX)`를 잡고 죽으면 NFS 서버에 lock 잔존. `fcntl.flock()`에 타임아웃이 없어 **모든 후속 DOE가 영원히 대기**.

```
DOE 001 (Node A): flock(LOCK_EX) → Node A 죽음 → lock 해제 안 됨
DOE 024 (Node B): flock(LOCK_SH) → NFS 서버: "Node A가 lock 보유 중" → 무한 대기
DOE 025~046: 같은 lock → 전부 무한 대기
```

---

### B. Slurm 스케줄링 관련

#### B-1. Oversubscription — 노드당 다수 잡 동시 배정

**파일**: `KooChainRun` (sbatch 헤더)

`ncpu=1, mem=2G`로 제출 시 Slurm이 한 노드에 잡 수십 개 배정. 100개 sbatch가 1초 안에 제출되면:

```
t=0.00s: DOE 001 → Node A (slots: 63 CPU 남음)
t=0.01s: DOE 024 → Node A (DOE 001이 아직 Apptainer 올리는 중)
  → 같은 노드에서 SIF 추출 경쟁, I/O 충돌
  → 나중 잡: launch failed → requeued → held
```

첫 번째로 시작된 DOE만 리소스를 선점하고 성공. 나머지는 전부 실패.

#### B-2. idle-but-dead 노드 → 잡 반복 배정 실패

Slurm `sinfo`에서 idle로 보이지만 실제 응답 불가 노드. Slurm이 계속 해당 노드에 잡 배정 → launch failed → requeue → 같은 노드에 다시 배정 → 반복 → held.

```
Node 01: dead (sinfo=idle)
DOE 024 → Node 01 → launch failed → requeue
DOE 025 → Node 01 → launch failed → requeue
...전부 Node 01에 순차 배정 → 전부 held
```

---

### C. Apptainer 관련

#### C-1. 컨테이너 정리 지연 → orphan 프로세스 → 노드 drain

**파일**: `CumulativeScenarioRunner.py` (LS-DYNA/KooMeshModifier 실행)

`subprocess.communicate()` 반환 후 Apptainer가 squashfuse unmount, sandbox 정리를 백그라운드에서 수행. 바로 다음 작업으로 진행하면 orphan 프로세스 잔존 → Slurm epilog 실패 → 노드 drain.

#### C-2. APPTAINER_TMPDIR이 NFS일 때

SIF 추출이 NFS에서 수행 → 추출 느림 + 정리 느림 → NFS 부하 가중.

---

### D. 데이터 무결성 관련

#### D-1. simulation_index.json Lost Update

**파일**: `CumulativeScenarioRunner.py` → `_update_index()`

`self.index`가 시작 시 1회만 로드. 저장 시 다른 잡의 데이터를 stale 메모리로 덮어씀 → 99개 DOE 데이터 손실.

#### D-2. `_get_prev_alias` 잘못된 Condition

**파일**: `CumulativeScenarioRunner.py` → `_get_prev_alias()`

DOE1의 condition만 사용하여 DOE2~N의 alias 잘못 생성 → `_get_prev_run_dir()` → None → 다음 step이 dynain 대신 원본 모델로 실행.

#### D-3. `_load_index` 초기화 경합

**파일**: `CumulativeScenarioRunner.py` → `_load_index()`

파일 없을 때 100개 잡이 LOCK_SH 상태에서 동시에 초기화 쓰기 → NFS 동시 write 충돌.

#### D-4. Status 업데이트 누락

| 실패 지점 | 문제 |
|-----------|------|
| `_create_step_config` 실패 | index 미업데이트 → status 이전 상태 잔존 |
| retry 전부 실패 후 `return False` | 시나리오 status 집계 건너뜀 |
| 시나리오 전체 완료 판정 | 실패 여부 무관하게 `completed` 설정 |

---

## 3. 수정 내용

### NFS 경합 방지

| Fix | 파일 | 내용 |
|-----|------|------|
| **rsync flock (bash)** | `KooChainRun` | Scratch cleanup rsync를 `.rsync_transfer.lock`으로 1개씩 직렬화 |
| **rsync flock (Python)** | `CumulativeScenarioRunner.py` | Stage-out rsync를 `.stage_out.lock`으로 1개씩 직렬화 |
| **runner.log DOE별 분리** | `CumulativeScenarioRunner.py` | `runner_doe_{N:03d}.log` — 동시 append 경합 제거 |
| **checkpoint DOE별 분리** | `CumulativeScenarioRunner.py` | `checkpoint_doe_{N:03d}.json` — 동시 write 경합 제거 |
| **lock 파일 open 'a' 모드** | `CumulativeScenarioRunner.py` | `open('w')` → `open('a')` — NFS truncate 경합 제거 |
| **잡 시작 stagger** | `KooChainRun` | `STAGGER=$((RANDOM % 300))` — 완료 시간 분산 (기본 300초) |

### NFS stale lock 대응

| Fix | 파일 | 내용 |
|-----|------|------|
| **flock timeout 120초** | `CumulativeScenarioRunner.py` | `_flock_with_timeout()` — 무한 대기 대신 120초 후 TimeoutError |
| **stale lock 삭제 + 재시도** | `CumulativeScenarioRunner.py` | `_load_index`, `_update_index`: timeout 시 lock 파일 삭제 → 재시도 → 최후 수단: lock 없이 직접 읽기/쓰기 |
| **stale lock 배치 정리** | `KooChainRun` | sbatch 스크립트에서 10분 이상 된 `.lock` 파일 자동 삭제 |

### Slurm 스케줄링 안정화

| Fix | 파일 | 내용 |
|-----|------|------|
| **`--exclusive`** (기본 True) | `KooChainRun` | 노드당 1개 잡 강제 — oversubscription 방지 |
| **`--requeue`** | `KooChainRun` | 노드 장애 시 자동 다른 노드로 재배정 |
| **노드 Health Check** | `KooChainRun` | submit 시 `srun hostname`으로 노드 사전 점검 → dead node 자동 `--exclude` |
| **노드 쓰기 점검** | `KooChainRun` | sbatch 스크립트 시작 시 `mkdir` 시도 → 실패(readonly 등) 시 `exit 1` |
| **NFS 가용성 재시도** | `KooChainRun` | `config_path` 접근 최대 5분(30초×10회) 대기 |
| **`--sequential` 모드** | `KooChainRun` | 노드당 1잡, 잡 안에서 여러 DOE 순차 실행 — 노드 전환 제거 |

### Apptainer 안정화

| Fix | 파일 | 내용 |
|-----|------|------|
| **정리 대기** | `CumulativeScenarioRunner.py` | LS-DYNA 후 5초, KooMeshModifier 후 3초 sleep |
| **tmpdir 명시적 삭제** | `CumulativeScenarioRunner.py` | `run_all()` 종료 시 `shutil.rmtree(apptainer_tmpdir)` |
| **orphan squashfuse 정리** | `KooChainRun` | sbatch 스크립트에서 `pkill -f squashfuse.*apptainer` |

### 데이터 무결성

| Fix | 파일 | 내용 |
|-----|------|------|
| **_update_index re-read + merge** | `CumulativeScenarioRunner.py` | LOCK_EX 내에서 최신 파일 재읽기 후 머지 — lost update 방지 |
| **_load_index double-checked locking** | `CumulativeScenarioRunner.py` | LOCK_SH 읽기 시도 → 실패 시 LOCK_EX 재획득 후 단독 초기화 |
| **_get_prev_alias DOE별 condition** | `CumulativeScenarioRunner.py` | `doe_angles`/`doe_positions`에서 DOE별 실제 condition 조회 |
| **시나리오 status 실제 집계** | `CumulativeScenarioRunner.py` | `_update_scenario_status()` 메서드 분리: completed/partial_failed/in_progress 판정 |
| **실패 시에도 status 집계** | `CumulativeScenarioRunner.py` | retry 전부 실패 후에도 `_update_scenario_status()` 호출 |
| **_create_step_config 실패 시 status** | `CumulativeScenarioRunner.py` | `failed` + 에러 메시지 기록 (기존: 미업데이트) |
| **DropSet_dti.k 누락 경고** | `CumulativeScenarioRunner.py` | DYNAIN_TO_INITIAL 실패 후 원본 모델 fallback 시 warning 로그 |
| **fallback shutil 디렉토리 처리** | `CumulativeScenarioRunner.py` | rsync 실패 시 fallback에서 디렉토리도 복사 (기존: 파일만) |

### 운영 기능

| Fix | 파일 | 내용 |
|-----|------|------|
| **rerun --exclude-nodes auto** | `KooChainRun`, `JobManager.py` | sacct + sinfo에서 실패/down 노드 자동 감지, `sbatch --exclude`에 전달 |
| **rerun --exclude-nodes 수동** | `KooChainRun`, `JobManager.py` | 수동 노드 지정: `--exclude-nodes node01,node07` |
| **UnicodeEncodeError 수정** | `KooChainRun` | `open(script_path, 'w', encoding='utf-8')` |

---

## 4. 수정 전후 비교

```
수정 전:
  100개 sbatch 1초 안에 제출
    → Slurm이 노드당 여러 잡 배정 (ncpu=1 → oversubscription)
    → Apptainer SIF 추출 경쟁 → 나중 잡 launch failed
    → 첫 배치 완료 시 23개 rsync 동시 → NFS 포화
    → 다음 배치 launch failed → requeued → held
    → 노드 1개 죽음 → NFS stale lock → 모든 후속 DOE 무한 hang
    → idle-but-dead 노드에 계속 잡 배정 → 전부 실패
    → simulation_index.json: 마지막 DOE 데이터만 잔존
    → status: 실패해도 completed, running 잔존

수정 후:
  submit 시 노드 health check → dead node 자동 exclude
    → --exclusive: 노드당 1잡 강제
    → stagger(~300초): 시작/완료 시간 분산
    → rsync flock (bash+Python): 1개씩 순차 전송
    → Apptainer 정리 대기 + orphan 정리
    → 노드 장애 시: --requeue로 자동 재배정
    → NFS stale lock: 120초 timeout → 삭제 → 재시도
    → _update_index: re-read + merge → 전체 데이터 보존
    → status: 성공/실패 모두 정확히 집계
    → --sequential 모드: 노드 전환 없이 순차 실행 (선택)
    → rerun --exclude-nodes auto: 실패 노드 제외 재실행
```

---

## 5. 사용법

### 기본 모드 (DOE당 1잡)

```bash
KooChainRun prepare scenario.json
KooChainRun submit runner_config.json --nodes 23 --ncpu-per-job 128
```

### Sequential 모드 (노드당 1잡, DOE 순차)

```bash
KooChainRun submit runner_config.json --nodes 23 --ncpu-per-job 128 --sequential
```

```
23개 잡 생성:
  run_seq_000.sh: DOE 1 → 24 → 47 → 70 → 93
  run_seq_001.sh: DOE 2 → 25 → 48 → 71 → 94
  ...
  run_seq_022.sh: DOE 23 → 46 → 69 → 92
```

### 실패 재실행

```bash
# 상태 확인
KooChainRun rerun test_dir --dry-run

# 실패 노드 자동 제외 재실행
KooChainRun rerun test_dir --exclude-nodes auto

# 수동 노드 제외
KooChainRun rerun test_dir --exclude-nodes node01,node07

# 특정 DOE만 재실행
KooChainRun rerun test_dir --does 1,24,25
```

### 설정 옵션

`scenario.json`의 `environment` 섹션:

| 키 | 기본값 | 설명 |
|----|--------|------|
| `job_stagger_seconds` | 300 | 잡 시작 지연 랜덤 범위 (초). 0이면 비활성 |
| `exclusive` | true | 노드 독점 (`#SBATCH --exclusive`) |
| `apptainer_tmpdir` | `/opt/tmp` | Apptainer 임시 디렉토리. **로컬 디스크 권장** (`/tmp`) |

---

## 6. 남은 한계

| 항목 | 내용 | 대응 |
|------|------|------|
| `fcntl.flock` NFS 신뢰성 | NFSv3+lockd에서 stale lock 가능 | timeout+삭제로 대응. NFSv4 권장 |
| idle-but-dead 노드 | submit 이후 죽는 노드는 health check로 감지 불가 | `--requeue` + `rerun --exclude-nodes auto` |
| sequential 노드 장애 | 1개 노드 죽으면 배정된 DOE 전부 미실행 | `rerun`으로 재실행 |
| Apptainer 정리 시간 | `time.sleep(5)` 하드코딩 | 환경에 따라 조정 필요 |

---

## 7. 수정 파일 요약

| 파일 | 수정 항목 |
|------|-----------|
| `KooChainRun` | rsync flock (bash), stagger, --requeue, --exclusive, health check, --sequential, --exclude, NFS 재시도, orphan/stale 정리, encoding='utf-8' |
| `Runner/CumulativeScenarioRunner.py` | DOE별 log/checkpoint, _update_index re-read+merge+stale lock 복구, _load_index double-checked locking+stale lock 복구, flock timeout 120초, stage-out rsync flock, Apptainer 정리 대기/tmpdir 삭제, _update_scenario_status 분리, status 보강, _get_prev_alias DOE별 condition, DropSet_dti.k 경고, fallback shutil 디렉토리 |
| `Runner/JobManager.py` | resubmit_does에 exclude_nodes 파라미터 |
