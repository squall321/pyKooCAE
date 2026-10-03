# simulation_index.json 락 결함 수정 계획 (2026-10-03)

## 신고

v89 서비스 중 v107 배포 후 잡이 전량 죽는다. KMM 실행 전 index 파일을 잠그는 과정에서 죽는다.
v89 도 같은 실패를 하고 있었으나 **숨기고 있었다** — 잡마다 2분을 버린 뒤 **락 없이** index 를
읽고 썼다. v107 이 그 우회 경로를 없애서 실패가 드러났다.

v89 로그: `NFS stale lock 감지 … lock 파일 삭제 후 재시도` → `2분 뒤 lock 재시도 실패. lock 없이 index 직접 읽기 시도`
v107 로그: `재시도해도 복구되지 않는 오류 … fd 수명 또는 파일시스템 지원 문제`

## 측정으로 확인한 것 / 못 한 것

🔴 **열기 모드는 원인이 아니다.** 헤드(ext4)와 node001(**nfs**) 양쪽에서 측정했다.

| 방식 | 헤드(ext4) | node001(nfs) |
|---|---|---|
| 현재 `open(path,'a')` | LOCK_EX 성공 | LOCK_EX 성공 |
| 제안 `os.open(O_RDWR\|O_CREAT)` | LOCK_EX 성공 | LOCK_EX 성공 |
| `open(path,'r')` | LOCK_EX 성공 | LOCK_EX 성공 |
| 이미 닫힌 fd | **EBADF(9)** | **EBADF(9)** |

→ `O_RDWR|O_CREAT` 로 바꾸는 것만으로는 이 파일시스템에서 결과가 달라지지 않는다.
EBADF 가 나는 유일한 조건은 **이미 닫힌 fd** 다. 프로브: `/data/koopark/Test_flock/probe.py`

## 코드를 읽어서 증명되는 결함 3건

### D1 🔴 `os.unlink(lock_file)` 이 상호배제를 깬다 (최우선)
`_load_index`(548행)·`_update_index`(670행)가 타임아웃 시 lock 파일을 **삭제**하고 재시도한다.
삭제 후 재시도의 `open(lock_file,'a')` 는 **새 inode** 를 만든다. 기존 보유 잡은 옛 inode 의
락을, 재시도 잡은 새 inode 의 락을 쥐고 **둘 다 진행**한다. 잡이 많으면 이름이 여러 inode 를
갈아타며 사실상 **락이 동작하지 않는다** → `simulation_index.json` 동시 쓰기 → lost update.

flock 은 보유 프로세스가 죽으면 **자동 해제**된다. 파일을 지울 이유가 없다. 신고 내용과 일치한다.

### D2 재시도 구조가 죽는 시간만 늘린다
`for attempt in range(2)` — 1회차 120초 대기 후 unlink, 2회차 120초 대기 후 raise.
합계 최대 4분. 신고의 "1~4분 만에 죽습니다" 와 맞는다.
v89 는 2회차에서 락 없이 진행했기에 "동작"했다(대가는 무언 손상).

### D3 경합 증폭 — 잡마다 락을 과하게 잡는다
`_load_index_locked` 가 LOCK_SH 로 열고 닫은 뒤 **별도 open 으로** LOCK_EX 를 다시 잡는다.
여기에 `_save_index`·`_update_index` 가 각각 LOCK_EX 를 잡는다. 수백 DOE 잡이 **단일 락 파일**에
1초 폴링으로 몰리면 120초 초과는 흔하다. 즉 타임아웃은 "stale lock" 이 아니라 **평범한 혼잡**을
저장소 장애로 오진한 것이다.

## 단계

### P0 재현 고정
- `tests/test_index_lock.py` — ① unlink 후 상호배제 붕괴 재현 ② 동시 N 잡 index 무결성
- 검증: 현재 코드에서 ①이 **붕괴를 재현**(기준선), 수정 후 통과

### P1 D1 제거 — unlink 금지 (최우선, 단독으로도 효과)
- `_load_index`·`_update_index` 의 `os.unlink(lock_file)` 삭제
- 타임아웃 메시지를 "stale lock" 추정에서 **혼잡**으로 정정하고 조치 지시 교체
- 검증: 상호배제 시험 통과, 기존 단일 잡 경로 불변

### P2 락 획득 단일화 (D3)
- `_load_index_locked` 의 2단계 open 을 **한 번의 open + 한 번의 LOCK_EX** 로
- 검증: 잡당 락 획득 횟수 감소, index 내용 동일

### P3 락 파일 열기 방식 정리 (신고 요청)
- `os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o664)` 로 교체
- 근거: 측정상 이 FS 에서 결과는 같지만 ⓐ 쓰지 않는 파일을 텍스트 append 스트림으로
  여는 것이 부적절하고 ⓑ **0o664 명시**로 다른 사용자·root 가 만든 락 파일을 그룹이
  쓸 수 있다(재현은 못 했으나 예방 가치 있음)

### P4 미확인 errno 대응 — **정보 필요**
v107 이 찍은 `재시도해도 복구되지 않는 오류` 는 화이트리스트 밖 errno 에서만 나온다.
어떤 errno 인지가 조치를 가른다.
- `ENOLCK(37)` → NFS 락 매니저 자원 부족. 재시도 대상에 넣어야 한다
- `EBADF(9)` → fd 수명 버그. 코드에서 찾아 고쳐야 한다
🔴 **숫자를 모르는 상태로 화이트리스트를 넓히지 않는다.** 실패 잡 로그의 `errno=` 값 요청.

## 회귀 방어
- 단일 잡 DROP/IMPACT/THERM 덱 바이트 동일
- 기존 스위트 전부 통과 (`test_encoding_guard` 가 `_flock_with_timeout` 을 직접 시험한다)
