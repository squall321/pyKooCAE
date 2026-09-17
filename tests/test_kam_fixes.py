# KAM 결함 수정 회귀 시험 — Evolver 작업 폴더 준비, bare exit() 제거, 계산 노드 IP 대역
"""
실행: venv312/bin/python tests/test_kam_fixes.py

  [Evolver] 작업 폴더에 Library/Evolver 가 있으면 그대로 / 없으면 설치본을 찾아 링크 / 끝내 없으면 종료 코드 1
  [exit]    컴파일 바이너리에는 site 의 exit() 가 없어 NameError 로 죽는다 → KAM 소스에 bare exit( 가 없어야 한다
  [IP]      계산 노드(192.168.122.x)가 허용 목록에 있어야 한다
"""
import io
import contextlib
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
sys.path.insert(0, str(GEN))

from KooODBCADManager import EvolverLocator as EL  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print("  %-66s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def fake_evolver(dirpath):
    os.makedirs(dirpath, exist_ok=True)
    p = os.path.join(dirpath, "evolver")
    Path(p).write_text("#!/bin/sh\n")
    os.chmod(p, 0o755)
    return p


def main():
    print("[Evolver]")
    real_opt = "/opt/Evolver/evolver"
    orig_install, orig_which = EL._install_dirs, EL.shutil.which
    try:
        EL.shutil.which = lambda name: None

        w = tempfile.mkdtemp(prefix="evo_local_")
        local = fake_evolver(os.path.join(w, "Library", "Evolver"))
        EL._install_dirs = lambda: []
        if not os.path.exists(real_opt):
            with contextlib.redirect_stdout(io.StringIO()):
                got = EL.find_linux_evolver(w)
            check("작업 폴더 Library/Evolver 가 있으면 그것을 그대로", got == local, got)
            check("  기존 폴더는 건드리지 않음 (링크 아님)", not os.path.islink(local))

        w = tempfile.mkdtemp(prefix="evo_install_")
        inst = tempfile.mkdtemp(prefix="evo_inst_")
        exe = fake_evolver(os.path.join(inst, "Library", "Evolver"))
        EL._install_dirs = lambda: [os.path.join(inst, "Library", "Evolver")]
        with contextlib.redirect_stdout(io.StringIO()):
            got = EL.find_linux_evolver(w)
        link = os.path.join(w, "Library", "Evolver", "evolver")
        if not os.path.exists(real_opt):
            check("작업 폴더에 없으면 설치본을 찾음", got == exe, got)
        check("작업 폴더 Library/Evolver/evolver 를 만들어 둠", os.path.exists(link))
        check("  설치본을 가리키는 링크", os.path.islink(link) and os.path.realpath(link) == os.path.realpath(got))

        w = tempfile.mkdtemp(prefix="evo_parent_")
        sub = os.path.join(w, "a", "b")
        os.makedirs(sub)
        up = fake_evolver(os.path.join(w, "Library", "Evolver"))
        EL._install_dirs = lambda: []
        with contextlib.redirect_stdout(io.StringIO()):
            got = EL.find_linux_evolver(sub)
        if not os.path.exists(real_opt):
            check("상위 폴더 Library/Evolver 도 기존처럼 찾음", os.path.realpath(got) == os.path.realpath(up), got)
        check("  그때도 작업 폴더에 실행 자리를 만듦 (예전엔 스크립트 쓰기에서 실패)",
              os.path.exists(os.path.join(sub, "Library", "Evolver", "evolver")))

        if not os.path.exists(real_opt):
            w = tempfile.mkdtemp(prefix="evo_none_")
            EL._install_dirs = lambda: []
            code = None
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    EL.find_linux_evolver(w)
            except SystemExit as e:
                code = e.code
            check("끝내 없으면 종료 코드 1", code == 1, str(code))
    finally:
        EL._install_dirs, EL.shutil.which = orig_install, orig_which

    print("[exit]")
    targets = [GEN / "KooAutomatedModeller.py"] + sorted((GEN / "KooODBCADManager").glob("*.py"))
    bare = []
    for p in targets:
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if re.match(r"^\s*exit\(", line):
                bare.append(f"{p.name}:{n}")
    check("KAM 소스에 bare exit( 없음", not bare, str(bare))

    print("[IP]")
    src = (GEN / "KooAutomatedModeller.py").read_text(encoding="utf-8")
    check("192.168.122.x 계산 노드 대역 허용", '"192.168.122."+str(i)' in src)

    print()
    if FAILS:
        print("FAIL %d 건" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
