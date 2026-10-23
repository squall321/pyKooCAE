# 키워드 리더·요소 파서 경계 결함(순환 인클루드·요소 블록 빈 줄·데이터 없는 키워드) 회귀 시험
"""
실행: venv312/bin/python tests/test_keyword_reader_edges.py

배경 (2026-10-23, 리뷰 C 가 찾고 남겨 둔 기존 결함 — 사용자 지시로 수정)
  [1] 자기 자신(또는 A→B→A)을 인클루드하면 RecursionError 로 죽었다. 이제 읽는 중인 파일은 경고하고 건너뛴다.
      같은 파일을 차례로 두 번 인클루드하는 것(순환 아님)은 그대로 읽는다.
  [2] 순수 *ELEMENT_SOLID·*ELEMENT_SHELL 레거시(8칸) 경로가 빈 줄에서 int('') 로 죽었다. 둘째 줄이 비면 1줄/2줄
      판별까지 뒤집혔다. R16 Appendix V — 빈 줄은 기본값 카드인데 EID·PID·N 은 기본값이 없어 요소 카드가 될 수 없다.
      이제 빈 줄을 건너뛰고 개수를 알린다. (*ELEMENT_SHELL_THICKNESS 의 빈 두께 카드는 의미가 있어 손대지 않는다.)
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

print("[2] 요소 블록의 빈 줄 — 건너뛰고 알린다")
L1, L2 = WANT
for label, body in (("솔리드 1줄 형식 중간 빈 줄", f"{L1}\n\n{L2}\n"),
                    ("솔리드 공백만 있는 줄", f"{L1}\n        \n{L2}\n"),
                    ("솔리드 둘째 줄이 빈 줄(1줄/2줄 판별)", f"{L1}\n\n{L2}\n\n"),
                    ("솔리드 블록 끝 빈 줄", f"{L1}\n{L2}\n\n\n")):
    rc, log, _, els = run_kmm({"model.k": "*KEYWORD\n" + nodes() + PROPS + "*ELEMENT_SOLID\n" + body + "*END\n"})
    check(f"{label} — rc 0·요소 보존", rc == 0 and els == WANT, f"rc={rc} {log[-300:]}")
    check("  빈 줄을 건너뛰었다고 알린다", "ELEMENT_SOLID 블록의 빈 줄" in log, [ln for ln in log.splitlines() if "빈 줄" in ln])
two = "".join(f"{e:8d}{1:8d}\n" + "".join(f"{n:8d}" for n in range(4 * e - 3, 4 * e + 5)) + "\n\n" for e in (1, 2))
rc, log, _, els = run_kmm({"model.k": "*KEYWORD\n" + nodes() + PROPS + "*ELEMENT_SOLID\n" + two + "*END\n"})
check("선언 없는 2줄 형식 + 빈 줄(원래 건너뛰던 경로) — 요소 보존", rc == 0 and els == WANT, f"rc={rc} {els}")
SHELLP = ("*PART\nskin\n" + f10(2, 2, 1) + "*SECTION_SHELL\n" + f10(2, 2) + f10(1.0, 1.0, 1.0, 1.0))
SH = [f"{10:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}", f"{11:8d}{2:8d}{5:8d}{6:8d}{7:8d}{8:8d}"]
shell_ref = "*KEYWORD\n" + nodes() + PROPS + SHELLP + "*ELEMENT_SHELL\n" + "\n".join(SH) + "\n*END\n"
def shells(text):
    out, f = [], False
    for ln in text.splitlines():
        if ln.startswith("*"):
            f = ln.startswith("*ELEMENT_SHELL")
        elif f and not ln.startswith("$") and ln.split():
            out.append(ln.split()[:6])  # 출력은 N5~N8=0 을 채운 8절점 형식
    return out


rc, log, sref, _ = run_kmm({"model.k": shell_ref})
check("기준 — 셸 2개(EID·PID·N1~N4)", rc == 0 and shells(sref) == [s.split() for s in SH], f"rc={rc} {shells(sref)}")
rc, log, text, _ = run_kmm({"model.k": shell_ref.replace(SH[0] + "\n", SH[0] + "\n\n")})
check("셸 1줄 형식 중간 빈 줄 — 출력이 기준과 같다", rc == 0 and text == sref, f"rc={rc} {log[-300:]}")
check("  빈 줄을 건너뛰었다고 알린다", "ELEMENT_SHELL 블록의 빈 줄" in log, [ln for ln in log.splitlines() if "빈 줄" in ln])
rc, log, text, _ = run_kmm({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*END\n"})
check("빈 줄 없는 블록 — 빈 줄 안내 없음", rc == 0 and "빈 줄" not in log, f"rc={rc}")

print()
if FAILS:
    print(f"FAIL {len(FAILS)}건 — 실행 폴더를 남긴다: {BASE}")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
shutil.rmtree(BASE)
print("ALL PASS")
