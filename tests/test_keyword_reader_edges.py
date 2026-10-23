# 키워드 리더·요소 파서 경계 결함(순환 인클루드·요소 블록 빈 줄·데이터 없는 키워드) 회귀 시험
"""
실행: venv312/bin/python tests/test_keyword_reader_edges.py

배경 (2026-10-23, 리뷰 C 가 찾고 남겨 둔 기존 결함 — 사용자 지시로 수정)
  [1] 자기 자신(또는 A→B→A)을 인클루드하면 RecursionError 로 죽었다. 이제 읽는 중인 파일은 경고하고 건너뛴다.
      같은 파일을 차례로 두 번 인클루드하는 것(순환 아님)은 그대로 읽는다.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
PY = str(ROOT / "venv312" / "bin" / "python")
OPT = "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,0,0,0\n**EndTransform\n*End\n"
BASE = Path(tempfile.mkdtemp(prefix="reader_edges_"))
FAILS = []


def check(name, cond, detail=""):
    print("  %-70s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def nodes():
    out, nid = [], 0
    for z in range(3):
        for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1)):
            nid += 1
            out.append(f"{nid:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}")
    return "*NODE\n" + "\n".join(out) + "\n"


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


PROPS = "*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
SOLID = "*ELEMENT_SOLID\n" + "".join(f"{e:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(4 * e - 3, 4 * e + 5)) + "\n"
                                     for e in (1, 2))
WANT = [ln for ln in SOLID.splitlines()[1:]]


def run_kmm(files):
    d = Path(tempfile.mkdtemp(dir=BASE))
    for name, text in files.items():
        Path(d, name).write_text(text)
    Path(d, "opt.txt").write_text(OPT)
    r = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt.txt"], cwd=d, capture_output=True, text=True,
                       timeout=600)
    out = Path(d, "model_trans.k")
    text = out.read_text() if out.exists() else ""
    els, f = [], False
    for ln in text.splitlines():
        if ln.startswith("*ELEMENT_SOLID"):
            f = True
            continue
        if ln.startswith("*"):
            f = False
        elif f and not ln.startswith("$") and len(ln.split()) >= 3:
            els.append(ln)
    return r.returncode, r.stdout + r.stderr, text, els


print("[1] 순환 인클루드 — 읽는 중인 파일은 건너뛴다")
rc, log, _, els = run_kmm({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*INCLUDE\nmodel.k\n*END\n"})
check("자기 자신을 인클루드 — rc 0·요소 보존", rc == 0 and els == WANT, f"rc={rc} {log[-300:]}")
check("  순환 인클루드라고 알린다", "순환 인클루드" in log, [ln for ln in log.splitlines() if "nclude" in ln][:4])
rc, log, _, els = run_kmm({"model.k": "*KEYWORD\n" + PROPS + "*INCLUDE\na.k\n*END\n",
                           "a.k": "*KEYWORD\n" + nodes() + SOLID + "*INCLUDE\nmodel.k\n*END\n"})
check("A→B→A — rc 0·요소 보존", rc == 0 and els == WANT and "순환 인클루드" in log, f"rc={rc} {log[-300:]}")
note = "*KEYWORD\n$ shared note only\n*END\n"
rc, log, _, els = run_kmm({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*INCLUDE\nnote.k\n*INCLUDE\nnote.k\n*END\n",
                           "note.k": note})
check("같은 파일을 차례로 두 번 인클루드(순환 아님) — 경고 없이 rc 0", rc == 0 and els == WANT and "순환 인클루드" not in log,
      f"rc={rc}")
rc, log, _, els = run_kmm({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*INCLUDE\na.k\n*INCLUDE\nb.k\n*END\n",
                           "a.k": "*KEYWORD\n*INCLUDE\nnote.k\n*END\n", "b.k": "*KEYWORD\n*INCLUDE\nnote.k\n*END\n",
                           "note.k": note})
check("마름모(a·b 가 같은 note.k 를 인클루드) — 경고 없이 rc 0", rc == 0 and els == WANT and "순환 인클루드" not in log,
      f"rc={rc}")

print()
if FAILS:
    print(f"FAIL {len(FAILS)}건 — 실행 폴더를 남긴다: {BASE}")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
shutil.rmtree(BASE)
print("ALL PASS")
