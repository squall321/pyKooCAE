# Surface Evolver 실행 파일을 찾고 작업 폴더에 Library/Evolver 실행 자리를 마련한다 (Capacitor·SolderJoint 공용)
import os
import shutil
import sys


def _install_dirs():
    """배포 설치본 위치 — 컴파일 바이너리는 <설치>/lib/<도구>/<도구>.bin 이라 두 단계 위가 설치 루트."""
    dirs = []
    for base in (os.path.dirname(os.path.abspath(sys.argv[0])), os.path.dirname(os.path.abspath(sys.executable))):
        for up in range(4):
            dirs.append(os.path.normpath(os.path.join(base, *([".."] * up), "Library", "Evolver")))
    dirs += ["/opt/SmartTwinPreprocessor/Library/Evolver", "/data/SmartTwinPreprocessor/Library/Evolver"]
    return dirs


def find_linux_evolver(basePath=None):
    """evolver 실행 파일 경로를 돌려준다.

    찾는 순서는 기존과 같고(/opt/Evolver → basePath 와 상위 4단계의 Library/Evolver → PATH),
    그래도 없으면 설치본(실행 파일 기준 Library/Evolver, /opt·/data 의 SmartTwinPreprocessor)을 본다.
    호출부는 basePath/Library/Evolver 를 스크립트·STL 작업 폴더로 쓰므로, 실행 파일이 그 밖에 있으면
    그 폴더를 만들고 evolver 와 보조 파일(*.cmd, fe/) 링크를 둔다. 못 찾으면 이유를 찍고 종료 코드 1."""
    base = basePath if basePath is not None else os.getcwd()
    candidates = ["/opt/Evolver/evolver"]
    for i in range(5):
        prefix = os.path.join(base, *([".."] * i)) if i > 0 else base
        candidates.append(os.path.join(prefix, "Library", "Evolver", "evolver"))
    found = next((c for c in candidates if os.path.exists(c)), None)
    if found is None:
        found = shutil.which("evolver")
    if found is None:
        found = next((os.path.join(d, "evolver") for d in _install_dirs()
                      if os.path.exists(os.path.join(d, "evolver"))), None)
    if found is None:
        print("evolver not found — 작업 폴더에 Library/Evolver/evolver 를 두거나 "
              "SmartTwinPreprocessor 설치본(Library/Evolver)을 확인할 것")
        sys.exit(1)

    workdir = os.path.join(base, "Library", "Evolver")
    # 링크면 실제 설치 위치 기준 (앞 실행이 evolver 링크만 만든 폴더도 보조 파일을 채우도록)
    srcdir = os.path.dirname(os.path.realpath(found))
    if os.path.realpath(srcdir) != os.path.realpath(workdir):
        # 스크립트가 작업 폴더에서 `read "stl.cmd"` 처럼 보조 파일을 읽으므로 실행 파일과 함께 연결한다.
        # 산출물(.stl/.step/tmpScript 등)은 새로 쓰는 파일이라 링크하지 않는다 (설치본은 읽기 전용일 수 있음).
        support = [n for n in os.listdir(srcdir) if n.endswith(".cmd") or n == "fe"]
        linked = []
        for name in ["evolver"] + support:
            dst = os.path.join(workdir, name)
            if os.path.lexists(dst):
                continue
            os.makedirs(workdir, exist_ok=True)
            src = found if name == "evolver" else os.path.join(srcdir, name)
            try:
                os.symlink(os.path.abspath(src), dst)
            except OSError:
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            linked.append(name)
        if linked:
            print(f"Evolver 작업 폴더 준비: {workdir} ← {srcdir} ({', '.join(linked)})")
    return found
