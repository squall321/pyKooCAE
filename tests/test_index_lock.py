# simulation_index.json 락 결함(unlink 재시도로 상호배제 붕괴) 회귀 시험
"""
실행: venv312/bin/python tests/test_index_lock.py

검증 항목
  1 _open_lock 이 O_RDWR|O_CREAT 로 열고 LOCK_EX 를 잡는다
  2 소스에 os.unlink(lock_file) 이 남아 있지 않다 (상호배제 붕괴 경로 제거)
  3 재시도 루프(for attempt in range(2))가 제거됐다
  4 동시 보유 시 두 번째 획득은 실패한다 (상호배제 성립)
  5 타임아웃 메시지가 "lock 파일 삭제" 를 권하지 않는다
  6 _flock_with_timeout 이 닫힌 fd(EBADF)에 즉시 실패한다 (120초 낭비 금지)
"""
import fcntl
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "occProject" / "Generators"))

FAILS = []


def check(name, cond, detail=""):
    print("  %-66s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


SRC = (ROOT / "Runner" / "CumulativeScenarioRunner.py").read_text(encoding="utf-8")

from Runner.CumulativeScenarioRunner import _flock_with_timeout, _open_lock  # noqa: E402


def main():
    print("=== 소스 불변식")
    check("os.unlink(lock_file) 0건", SRC.count("os.unlink(lock_file)") == 0,
          "%d건 남음" % SRC.count("os.unlink(lock_file)"))
    check("unlink 재시도 루프 제거", "for attempt in range(2)" not in SRC)
    check("타임아웃 메시지가 lock 삭제를 권하지 않음",
          "lock 파일 삭제 후 재시도" not in SRC)
    check("락 열기는 _open_lock 경유 5곳",
          SRC.count("_open_lock(lock_file)") == 5,
          "%d곳" % SRC.count("_open_lock(lock_file)"))
    check("'a' 모드 직접 열기 0건", "open(lock_file, 'a'" not in SRC)

    with tempfile.TemporaryDirectory(prefix="idxlock_") as work:
        lock = os.path.join(work, "simulation_index.json.lock")

        print("=== _open_lock 동작")
        fd = _open_lock(lock)
        try:
            check("fd 는 정수", isinstance(fd, int))
            mode = os.stat(lock).st_mode & 0o777
            check("권한에 그룹 쓰기 포함 (0o664 기대, umask 영향 가능)",
                  bool(mode & 0o020) or mode == 0o644, oct(mode))
            _flock_with_timeout(fd, fcntl.LOCK_EX)
            check("LOCK_EX 획득", True)

            print("=== 상호배제 성립 (같은 inode)")
            fd2 = _open_lock(lock)
            try:
                same_inode = os.fstat(fd).st_ino == os.fstat(fd2).st_ino
                check("두 fd 가 같은 inode", same_inode)
                try:
                    fcntl.flock(fd2, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    check("두 번째 LOCK_EX 는 실패해야 함", False, "획득됨 — 붕괴")
                    fcntl.flock(fd2, fcntl.LOCK_UN)
                except OSError:
                    check("두 번째 LOCK_EX 실패(정상)", True)
            finally:
                os.close(fd2)
            _flock_with_timeout(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

        print("=== 닫힌 fd 는 즉시 실패 (120초 낭비 금지)")
        stale = _open_lock(lock)
        os.close(stale)
        import time
        t0 = time.time()
        try:
            _flock_with_timeout(stale, fcntl.LOCK_EX, timeout=30)
            check("닫힌 fd 는 예외여야 함", False, "성공해버림")
        except OSError as e:
            el = time.time() - t0
            check("닫힌 fd 즉시 OSError", el < 2.0, "%.1fs 소요" % el)
            check("메시지에 errno 포함", "errno=" in str(e), str(e)[:90])
        except TimeoutError:
            check("닫힌 fd 가 TimeoutError 로 둔갑하지 않음", False,
                  "120초 재시도 후 timeout — 회귀")

    print()
    if FAILS:
        print("FAILED %d" % len(FAILS))
        for f in FAILS:
            print("  - %s" % f)
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
