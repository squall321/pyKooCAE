# 키워드 리더·요소 파서 경계 결함(순환 인클루드·요소 블록 빈 줄·데이터 없는 키워드) 회귀 시험
"""
실행: venv312/bin/python tests/test_keyword_reader_edges.py

배경 (2026-10-23, 리뷰 C 가 찾고 남겨 둔 기존 결함 — 사용자 지시로 수정)
  [1] 자기 자신(또는 A→B→A)을 인클루드하면 RecursionError 로 죽었다. 이제 읽는 중인 파일은 경고하고 건너뛴다.
      같은 파일을 차례로 두 번 인클루드하는 것(순환 아님)은 그대로 읽는다.
  [2] 순수 *ELEMENT_SOLID·*ELEMENT_SHELL 레거시(8칸) 경로가 빈 줄에서 int('') 로 죽었다. 둘째 줄이 비면 1줄/2줄
      판별까지 뒤집혔다. R16 Appendix V — 빈 줄은 기본값 카드인데 EID·PID·N 은 기본값이 없어 요소 카드가 될 수 없다.
      이제 빈 줄을 건너뛰고 개수를 알린다. (*ELEMENT_SHELL_THICKNESS 의 빈 두께 카드는 의미가 있어 손대지 않는다.)
  [3] 데이터 카드가 없는 키워드(*CONTROL_MPP_IO_NOD3DUMP·*CONTROL_MPP_IO_NOTIEDIO 등)가 출력에서 빠졌다.
      R16 원문에 "This keyword has no input parameters/data cards" 인 정상 키워드다. 이제 KMM 이 같은 키워드를
      쓰지 않았으면 키워드 줄만 원문대로 남긴다(KMM 이 쓴 키워드는 KMM 판이 우선).
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

print("[3] 데이터 카드가 없는 키워드 — 출력에 남긴다")


def kwcount(text, name):
    return sum(1 for ln in text.splitlines() if ln.strip().upper() == "*" + name)


def before_end(text, name):
    lines = [ln.strip().upper() for ln in text.splitlines()]
    return "*" + name in lines and "*END" in lines and lines.index("*" + name) < lines.index("*END")


MPP = "*CONTROL_MPP_IO_NOD3DUMP\n*CONTROL_MPP_IO_NOTIEDIO\n"
rc, log, text, els = run_kmm({"model.k": "*KEYWORD\n" + MPP + nodes() + PROPS + SOLID + "*END\n"})
for name in ("CONTROL_MPP_IO_NOD3DUMP", "CONTROL_MPP_IO_NOTIEDIO"):
    check(f"중간의 *{name} — 출력에 한 번, *END 앞", rc == 0 and kwcount(text, name) == 1 and before_end(text, name),
          f"rc={rc} n={kwcount(text, name)}")
check("  요소 보존", els == WANT, f"{els}")
rc, log, text, els = run_kmm({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*CONTROL_MPP_IO_NOD3DUMP\n"})
check("파일 끝(*END 없음)의 *CONTROL_MPP_IO_NOD3DUMP — 출력에 한 번",
      rc == 0 and kwcount(text, "CONTROL_MPP_IO_NOD3DUMP") == 1 and els == WANT, f"rc={rc}")
rc, log, text, els = run_kmm({"model.k": "*KEYWORD\n*CONTROL_MPP_IO_NODUMP\n" + nodes() + PROPS + SOLID + "*END\n"})
check("전용 처리가 있는 *CONTROL_MPP_IO_NODUMP — 중복 없이 한 번", rc == 0 and kwcount(text, "CONTROL_MPP_IO_NODUMP") == 1,
      f"rc={rc} n={kwcount(text, 'CONTROL_MPP_IO_NODUMP')}")
rc, log, ref, _ = run_kmm({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*END\n"})
rc2, log2, text, els = run_kmm({"model.k": "*KEYWORD\n*PART\n" + nodes() + PROPS + SOLID + "*END\n"})
check("KMM 이 쓰는 키워드(*PART)가 빈 채로 하나 더 — KMM 판만 남는다(출력이 기준과 같다)", rc2 == 0 and text == ref,
      f"rc={rc2} PART={kwcount(text, 'PART')}")
rc, log, text, els = run_kmm({"model.k": "*KEYWORD\n*CONTROL_MPP_IO_NOD3DUMP\n*CONTROL_MPP_IO_NOD3DUMP\n" + nodes() + PROPS
                              + SOLID + "*END\n"})
check("같은 빈 키워드 두 번 — 한 번만 남긴다", rc == 0 and kwcount(text, "CONTROL_MPP_IO_NOD3DUMP") == 1, f"rc={rc}")
case_deck = ("*KEYWORD\n" + nodes() + PROPS + SOLID + "*CASE_BEGIN_1\n*BOUNDARY_SPC_NODE\n" + f10(1, 0, 1, 1, 1, 0, 0, 0)
             + "*CASE_END_1\n*END\n")
rc, log, text, els = run_kmm({"model.k": case_deck})
check("*CASE_BEGIN_1·*CASE_END_1(위치가 뜻) — 끝에 모아 되살리지 않는다(옛 판과 같다)",
      rc == 0 and kwcount(text, "CASE_BEGIN_1") == 0 and kwcount(text, "CASE_END_1") == 0, f"rc={rc}")

print("[4] *END 뒤의 *PARAMETER 정의는 쓰지 않는다 — 리뷰 D")
par = ("*KEYWORD\n*PARAMETER\nR      thk       1.0\n" + nodes() + PROPS + SOLID + "*PART\nskin\n" + f10(2, 2, 1)
       + "*SECTION_SHELL\n" + f10(2, 2) + "      &thk      &thk      &thk      &thk\n*ELEMENT_SHELL\n"
       + f"{10:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}\n*END\n*PARAMETER\nR      thk       2.0\n")
rc, log, text, els = run_kmm({"model.k": par})
shell_t = None
lines = text.splitlines()
for i, ln in enumerate(lines):
    if ln.startswith("*SECTION_SHELL"):
        j = i + 1 + (1 if ln.strip().upper().endswith("_TITLE") else 0)   # _TITLE 이면 제목 줄을 건너뛴다
        data = [x for x in lines[j:j + 6] if x.strip() and not x.startswith("$")]
        if len(data) >= 2:
            shell_t = float(data[1].split()[0])   # Card 2 의 T1
        break
check("SECTION_SHELL 두께 = *END 앞 정의 1.0 (뒤의 2.0 아님)", rc == 0 and shell_t == 1.0, f"rc={rc} t={shell_t}")

print("[5] MERGE_K — 강제로 펼친 인클루드는 첫 *END 에서 끝나고 끝의 Ctrl-Z 를 뺀다 — 리뷰 D")
MERGE_OPT = ("*Inputfile\nmodel.k\n*Mode\nMERGE_K,1\n**MergeK,1\nForceInlinePreserved,true\n**EndMergeK\n"
             "*PreserveIncludes\nkeep.k\n*End\n")
keep = ("*KEYWORD\n*DEFINE_CURVE\n         7\n            0.000000            0.000000\n            1.000000            1.000000\n"
        "*END\n*PART\nparked\n" + f10(2, 1, 1) + "*ELEMENT_SOLID\n" + f"{3:8d}{2:8d}" + "".join(f"{n:8d}" for n in range(1, 9))
        + "\n\x1a")
d = Path(tempfile.mkdtemp(dir=BASE))
Path(d, "model.k").write_text("*KEYWORD\n" + nodes() + PROPS + SOLID + "*INCLUDE\nkeep.k\n*END\n")
Path(d, "keep.k").write_text(keep)
Path(d, "opt.txt").write_text(MERGE_OPT)
r = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt.txt"], cwd=d, capture_output=True, text=True, timeout=600)
merged = Path(d, "model_merged.k").read_text() if Path(d, "model_merged.k").exists() else ""
check("MERGE_K rc 0·커브는 펼침", r.returncode == 0 and "*DEFINE_CURVE" in merged, f"rc={r.returncode} {r.stderr[-200:]}")
check("  *END 뒤 파트 parked·요소 3 은 펼치지 않는다, 0x1A 없음",
      "parked" not in merged and not any(ln.split()[:2] == ["3", "2"] for ln in merged.splitlines()) and "\x1a" not in merged,
      f"parked={'parked' in merged} ctrlz={'\x1a' in merged}")

print("[6] 덤프 *CONTROL_BULK_VISCOSITY — 값이 주석 줄에 붙지 않는다 — 리뷰 D")
d = Path(tempfile.mkdtemp(dir=BASE))
Path(d, "model.k").write_text("*KEYWORD\n*CONTROL_BULK_VISCOSITY\n" + f10(1.6, 0.07, -2) + nodes() + PROPS + SOLID + "*END\n")
Path(d, "opt.txt").write_text(OPT)
r = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt.txt"], cwd=d, capture_output=True, text=True, timeout=600)
dump = Path(d, "model_dump.k").read_text() if Path(d, "model_dump.k").exists() else ""
dl = dump.splitlines()
i = next((k for k, ln in enumerate(dl) if ln.startswith("*CONTROL_BULK_VISCOSITY")), None)
vals = None
if i is not None:
    after = [ln for ln in dl[i + 1:i + 4] if not ln.startswith("$")]
    try:
        vals = [float(v) for v in after[0].split()[:2]] if after else None
    except ValueError:
        vals = None   # 값 줄이 아니다(옛 판은 값이 주석 줄에 붙어 다음 키워드 줄이 온다)
check("model_dump.k 의 BULK_VISCOSITY 값 줄 = 1.6 0.07", r.returncode == 0 and vals == [1.6, 0.07],
      f"rc={r.returncode} {dl[i:i + 3] if i is not None else None}")

print("[7] 같은 DynaManager 재사용 — 지난 덱의 빈 키워드·인클루드 스택이 남지 않는다 — 리뷰 D")
sys.path.insert(0, str(GEN))
from KooCAEManager.KooDynaKeyword import DynaManager  # noqa: E402
import contextlib  # noqa: E402
import io  # noqa: E402
import os  # noqa: E402
cwd0 = os.getcwd()
da, db = Path(tempfile.mkdtemp(dir=BASE)), Path(tempfile.mkdtemp(dir=BASE))
Path(da, "a.k").write_text("*KEYWORD\n*CONTROL_MPP_IO_NOD3DUMP\n" + nodes() + PROPS + SOLID + "*END\n")
Path(db, "b.k").write_text("*KEYWORD\n" + nodes() + PROPS + SOLID + "*END\n")
mgr = DynaManager()
try:
    with contextlib.redirect_stdout(io.StringIO()):
        mgr.currentDirectory, mgr.inputFile = str(da), "a.k"
        mgr.ReadInputFile(str(da / "a_dump.k"), writelog=False)
        first = list(getattr(mgr, "_empty_keyword_names", []))
        mgr._include_stack.append("/stale/after/exception.k")  # 예외로 끊긴 읽기를 흉내
        mgr.currentDirectory, mgr.inputFile = str(db), "b.k"
        mgr.ReadInputFile(str(db / "b_dump.k"), writelog=False)
finally:
    os.chdir(cwd0)
check("첫 덱의 빈 키워드는 기록됐다", first == ["CONTROL_MPP_IO_NOD3DUMP"], f"{first}")
check("  둘째 덱을 읽은 뒤 빈 키워드·인클루드 스택이 비었다", mgr._empty_keyword_names == [] and mgr._include_stack == [],
      f"{mgr._empty_keyword_names} {mgr._include_stack}")

print("[8] *ELEMENT_SHELL_THICKNESS — 빈 두께 카드(=섹션 두께)·BETA 생략 줄에서 죽지 않는다 — 리뷰 D")
TH = "".join(f"{x:>16}" for x in (0.5, 0.5, 0.5, 0.5))
for label, first_card in (("첫 요소 두께 카드가 빈 줄", ""), ("첫 요소 두께 카드가 BETA 생략(64자)", TH)):
    body = (f"{10:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}\n{first_card}\n"
            f"{11:8d}{2:8d}{5:8d}{6:8d}{7:8d}{8:8d}\n" + TH + f"{0.0:>16}\n")
    rc, log, text, _ = run_kmm({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + SHELLP + "*ELEMENT_SHELL_THICKNESS\n" + body
                                + "*END\n"})
    got = shells(text) if "*ELEMENT_SHELL" in text else []
    check(f"{label} — rc 0·셸 2개 보존", rc == 0 and [g[:2] for g in got] == [["10", "2"], ["11", "2"]],
          f"rc={rc} {got} {log[-250:] if rc else ''}")

print()
if FAILS:
    print(f"FAIL {len(FAILS)}건 — 실행 폴더를 남긴다: {BASE}")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
shutil.rmtree(BASE)
print("ALL PASS")
