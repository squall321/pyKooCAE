# ascii 사고 수정 — 결정 노트

## 왜 "인터프리터로 테스트했더니 멀쩡" 했나
PEP 540. 로케일이 `C`/`POSIX` 면 CPython 이 UTF-8 모드를 자동으로 켠다.
`env -u LANG` 로 아무리 지워도 인터프리터에서는 재현이 안 된다.
Nuitka 산출물은 이 자동 활성화를 못 받아 `utf8_mode=0` 으로 뜬다 (프로브 실측).

→ **교훈: 이 계열 결함은 반드시 컴파일 산출물로 검증해야 한다.**
   ([[feedback_nuitka_no_korean_strings]] 와 같은 계열 — 소스 검증이 배포본을 대변하지 못한다.)

## 왜 `setlocale` 을 1층으로 두는가
호출부 44+47 지점을 다 고쳐도, 앞으로 추가될 호출부와 서드파티 코드는 못 막는다.
`setlocale` 은 `nl_langinfo(CODESET)` 을 바꾸므로 `getpreferredencoding` 을 쓰는
**모든** 경로가 한 번에 덮인다. 실측으로 미수정 호출부 통과 확인.

## 왜 그것만으로 끝내지 않는가
`C.UTF-8` 로케일이 없는 시스템이면 `setlocale` 이 `locale.Error` 로 실패한다.
glibc 2.35 는 내장이라 계산노드는 안전하지만, 컨테이너 내부는 보장할 수 없다.
두 층은 서로 독립적으로 성립해야 한다.

## `errors=` 선택
- **자식 출력 디코딩**: `errors="replace"`. 로그를 읽으려다 파이프라인을 죽이면 안 된다.
  솔버가 비 UTF-8 바이트를 뱉어도 진행돼야 한다.
- **우리 파일 입출력**: `errors` 미지정(strict). 우리가 쓰는 덱·JSON 이 깨지면
  조용히 뭉개는 것보다 즉시 아는 게 낫다.

이 구분은 의도적이다. 전부 `replace` 로 통일하면 덱 손상이 무증상으로 흘러간다.

## D3 를 격상한 이유
`sys.getfilesystemencoding()` 은 시작 시 고정이라 `setlocale` 로 못 바꾼다.
한글 경로/인자는 `text=` 와 무관하게 `subprocess._execute_child` 에서 죽는다.
프로세스 시작 전 환경변수만이 유일한 해결책이므로 "보험" 이 아니다.

## D4 재시도 정책
`UnicodeDecodeError` 는 결정적이다. 같은 입력이면 100% 같은 결과다.
재시도는 시간만 태우고, 로그에는 "3회 재시도 후 실패" 로 남아
**원인이 일시적 자원 문제인 것처럼 보이게 만든다**. 이번 사고의 오진 원인 중 하나.

## D5 락 없는 폴백을 남기지 않는 이유
동시 186 잡이 index 를 락 없이 읽으면 부분 기록 상태를 읽는다.
"락 못 잡음" 은 실패로 처리하는 게 맞다. 조용히 깨진 데이터를 읽는 것보다 낫다.

## 실증 결과 (2026-09-10)

### 컴파일 바이너리 가드 ON/OFF (env -i)
| 경로 | 가드 OFF | 가드 ON |
|---|---|---|
| `subprocess text=True` | UnicodeDecodeError | OK |
| `open(read)` | UnicodeDecodeError | OK |
| `open(write)` | UnicodeEncodeError | OK |
| `logging.FileHandler` | UnicodeEncodeError | OK |
| `print(한글)` | 프로세스 사망 | 정상 출력 |

**호출부를 하나도 안 고친 상태**에서 1층만으로 전부 통과했다.

### 클러스터 e2e (잡 1137~1140, node001)
`LANG`/`LC_ALL` 제거 상태로 `prepare` → `submit` → 계산노드 실행.

- 계산노드 로그에 `ELEMENT_SOLID 개수 검사: 입력 43657 = 등록 43657 (소실 0)`
  → **자식(KooMeshModifier) 한글 stdout 이 부모에서 디코딩됨. 사고의 D1 경로 그대로.**
- `logging.FileHandler` 한글 기록 정상 (D2)
- 3개 로그 전부 `UnicodeDecodeError`/`UnicodeEncodeError`/`ANSI_X3.4-1968` **0건**
- `scontrol write batch_script` 로 Slurm 이 읽은 원본 확인 — 지시자 14개 전부 보존,
  `--dependency=afterany:1137:1138:1139` 등록, `job_env` 가 기본값 뒤에 적용

### ⚠️ 완주는 확인 못 했다
LS-DYNA 가 `Error 70022` + `Program license has expired` 로 종료했다.
**라이선스 만료이며 이번 수정과 무관하다.** 따라서 "완주 수" 기준 판정은 미완이다.
다만 파이프라인은 솔버 실패를 정상 처리했다 — 재시도, stage-out, status 집계,
체크포인트 모두 동작했고 트레이스백 없이 종료했다.

## 놓쳤다가 잡은 것 — run_doe_NNN.sh
1차 D3 는 `Runner/*.py` 만 훑어 `KooChainRun` 안의 템플릿 8곳을 통째로 빠뜨렸다.
그 중 `run_doe_NNN.sh` 는 DOE 잡 본체이자 사고 보고서의 재현 명령이 지목한 스크립트다.
소스 스캔 범위를 좁게 잡은 것이 원인. 회귀 테스트에 shebang 전수 검사를 추가했다.

또한 `{exclusive_line}{exclude_line}` 처럼 **변수로 주입되는 `#SBATCH`** 앞에
export 를 넣으면 지시자가 통째로 무효화된다. 리터럴 `#SBATCH` 만 보고 위치를
잡으면 안 된다 — `PostprocessShellGenerator` 에서 실제로 이 실수를 했고
생성물 검사가 잡았다.
