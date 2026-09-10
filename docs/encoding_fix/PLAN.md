# ascii 디코딩 전량 사망 — 수정 계획

## 1. 근본 원인 (실측 확정)

**Nuitka 컴파일 바이너리는 `sys.flags.utf8_mode = 0` 으로 기동한다.**

인터프리터는 PEP 540 에 따라 로케일이 `C`/`POSIX` 이면 UTF-8 모드를 **자동으로 켠다**.
Nuitka 산출물은 그 자동 활성화를 받지 못한다. 그래서 `LANG` 이 없는 환경에서

| 실행체 | `getpreferredencoding` | 결과 |
|---|---|---|
| `python3 KooChainRun` (개발/수동 테스트) | `utf-8` | 정상 |
| `KooChainRun.bin` (배포·sbatch) | `ANSI_X3.4-1968` | **전량 사망** |

이것이 "로컬에서는 재현이 안 되는데 클러스터에서만 죽는" 이유다.

실측 (동일 플래그 `--standalone --follow-imports` 로 컴파일한 프로브).

```
=== [1] LANG=C.UTF-8 ===         === [2] LANG 없음 ===
flags.utf8_mode: 0                flags.utf8_mode: 0
setlocale      : C.UTF-8          setlocale      : C
nl_langinfo    : UTF-8            nl_langinfo    : ANSI_X3.4-1968
getpreferred   : UTF-8            getpreferred   : ANSI_X3.4-1968
stdout.encoding: utf-8            stdout.encoding: ascii
```

[2] 에서 자식 한글 출력을 `text=True` 로 읽으면 보고서와 **문구까지 동일한** 예외가 난다.

```
UnicodeDecodeError: 'ascii' codec can't decode byte 0xea in position 14
decoding with 'ANSI_X3.4-1968' codec failed
```

## 2. 기존 방어가 왜 안 통했나

`KooChainRun` 17–23 행에 이미 stdout/stderr UTF-8 래핑이 있고 배포 v89 바이너리에도 들어 있다.
그런데도 죽었다. 그 래핑은 **자기 출력만** 덮기 때문이다.

| 경로 | 무엇을 쓰나 | 래핑이 덮나 |
|---|---|---|
| `print()` | `sys.stdout` | ✅ 덮음 |
| `subprocess(text=True)` | `locale.getpreferredencoding(False)` | ❌ **안 덮음** ← 사고 지점 |
| `open(path, 'r')` | 〃 | ❌ 안 덮음 |
| `logging.FileHandler` | 〃 | ❌ 안 덮음 |

`os.environ.setdefault('PYTHONIOENCODING','utf-8')` 도 **자식의 stdio** 만 바꾼다.
부모가 파이프를 디코딩하는 코덱과는 무관하다.

## 3. 2층 방어

### 1층 — 런타임 벨트 (진입점 1곳)

`locale.setlocale(LC_ALL, 'C.UTF-8')` 하나로 `nl_langinfo(CODESET)` 이 UTF-8 이 되고,
`getpreferredencoding` 을 쓰는 **미수정 호출부까지 전부** 덮인다. 실측.

```
before setlocale: ANSI_X3.4-1968      after: UTF-8
  subprocess text=True (미수정 호출부) : OK
  open(read)  no encoding (미수정)     : OK
  open(write) no encoding (미수정)     : OK
  logging.FileHandler no encoding      : OK
```

### 2층 — 호출부 명시 (보고서 D1·D2)

1층은 시스템에 `C.UTF-8` 로케일이 있어야 성립한다(glibc 2.35 는 내장, 컨테이너는 보장 못 함).
없으면 그대로 죽으므로 호출부에 `encoding="utf-8"` 을 박는다. 두 층은 독립이다.

## 4. 🔴 보고서 D3 등급 정정 — "보험" 이 아니다

`sys.getfilesystemencoding()` 은 **인터프리터 시작 시 고정**이라 `setlocale` 로 안 바뀐다. 실측.

```
fsencoding before: ascii
fsencoding after : ascii      ← setlocale 무효
fsencode korean  : [FAIL] UnicodeEncodeError
```

즉 **한글이 든 경로/인자로 자식을 띄우면 `text=` 와 무관하게 `_execute_child` 에서 죽는다.**
이건 1층·2층 어느 쪽으로도 못 막고, **프로세스 시작 전 환경변수(D3)만이 유일한 해결책**이다.
저장소에 한글 파일명 실재(`occProject/Generators/[pnt용백업]…py`). 한글 프로젝트명이면 재현된다.

→ D3 는 "제출 경로 실수에 대한 보험" 이 아니라 **한 실패 모드의 단독 해결책**이다. High 유지가 아니라 D1·D2 와 동급으로 취급한다.

## 5. 범위

| 항목 | 지점 수 | 근거 |
|---|---|---|
| D1 subprocess 출력 캡처 | **44** | AST 스캔, 전부 `encoding=` 없음 |
| D2 `logging.FileHandler` | **1** | `CumulativeScenarioRunner.py:455` |
| 확장 text-mode `open()` | **47** | 보고서 미포함. 동일 원인 |
| D3 생성 셸 스크립트 | **14** | 전 생성 지점에 로케일 전문 |
| D4 결정적 실패 재시도 | — | Unicode*/FileNotFound 즉시 중단 |
| D5 flock fd 수명 + 락 없는 폴백 | — | `CumulativeScenarioRunner.py:51,541` |

## 6. 검증 기준

1. 컴파일 프로브가 `env -i` 에서 D1·D2·open 전부 OK
2. 실제 `KooChainRun.bin` 을 `env -u LANG -u LC_ALL` 로 실행해 한글 출력 정상
3. 기존 동작 회귀 0 (기존 테스트 스위트)
4. 클러스터 e2e — 보고서의 재현 명령으로 제출, **완주 수**로 판정
