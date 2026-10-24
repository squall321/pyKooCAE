# 리뷰 H 반영(파라미터 중복·변형, 요소 셋 0 칸·종류별 SID, 빈 THICKNESS 블록, *ELEMENT_MASS 칸 위치) 회귀 시험
"""
실행: venv312/bin/python tests/test_reader_review_h.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-10-24, 리뷰 H)
  [1] 인클루드 미리 읽기(3dd79ae)가 인클루드 *PARAMETER_EXPRESSION 을 메인의 평문 *PARAMETER 보다 늦게 평가해, 같은 이름이면
      인클루드 값이 메인 카드에 들어갔다(평문 값은 읽는 즉시, 식은 다 읽은 뒤 정해지는 해석기 순서). 이제 메인이 정의한 이름은
      미리 읽기에서 빼고, 인클루드끼리는 먼저 값(R16 *PARAMETER_DUPLICATION 기본 DFLAG=1)을 쓴다. LOCAL 이 아닌 변형
      (NOECHO·MUTABLE·EXPRESSION_NOECHO)도 전역이라 미리 읽는다.
  [2] 셸·솔리드 셋의 빈 칸이 0 으로 들어가 IMPORT_MERGE_K 의 OffsetID 가 0+offset 을 실제 EID 로 만들었다. 같은 SID 의
      *SET_SHELL 과 *SET_SOLID 는 사전 하나에 담겨 하나가 사라졌다(R16: 셋 ID 는 셋 종류마다 따로).
  [3] 빈 줄만 든 *ELEMENT_SHELL_THICKNESS 블록, N5 칸이 공백인 80자 카드 1 이 덤프 기록기에서 죽었다.
  [4] *ELEMENT_MASS 기록기가 MASS 를 8칸(17~24열)에 쓰고 PID 를 25~32열에 썼다. R16 MASS 는 17~32열, PID 는 33~40열이다.
      KMM 이 자기 출력을 다시 읽으면(누적 체인) 질량 요소가 사라졌다.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = Path(os.environ.get("KMM_GEN", ROOT / "occProject" / "Generators"))
PY = str(ROOT / "venv312" / "bin" / "python")
KMM_CMD = [os.environ["KMM_BIN"]] if os.environ.get("KMM_BIN") else [PY, str(GEN / "KooMeshModifier.py")]
ENV = dict(os.environ, PATH=str(ROOT / "venv312" / "bin") + ":" + os.environ.get("PATH", ""))
OPT = "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,0,0,0\n**EndTransform\n*End\n"
IMPORT_OPT = ("*Inputfile\nmodel.k\n*Mode\nIMPORT_MERGE_K,1\n**ImportMergeK,1\nImportFile,other.k\n**EndImportMergeK\n*End\n")
BASE = Path(tempfile.mkdtemp(prefix="reader_review_h_"))
FAILS = []


def check(name, cond, detail=""):
    print("  %-78s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def nodes():
    out, nid = [], 0
    for z in range(3):
        for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1)):
            nid += 1
            out.append(f"{nid:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}")
    return "*NODE\n" + "\n".join(out) + "\n"


PROPS = "*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
SOLID = "*ELEMENT_SOLID\n" + "".join(f"{e:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(4 * e - 3, 4 * e + 5)) + "\n"
                                     for e in (1, 2))
SHELLP = "*PART\nskin\n" + f10(2, 2, 1) + "*SECTION_SHELL\n" + f10(2, 2) + f10(1.0, 1.0, 1.0, 1.0)
SHELLS = "*ELEMENT_SHELL\n" + "".join(f"{e:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}\n" for e in range(21, 31))


def run(files, opt=OPT, outname="model_trans.k"):
    d = Path(tempfile.mkdtemp(dir=BASE))
    for name, text in files.items():
        Path(d, name).write_bytes(text.encode())
    Path(d, "opt.txt").write_text(opt)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
    out = Path(d, outname)
    return r.returncode, r.stdout + r.stderr, (out.read_text(errors="replace") if out.exists() else ""), d


def blocks(text, kw):
    """*kw(정확히 그 이름) 블록마다 데이터 줄(주석 뺌) 목록"""
    out = []
    for m in re.finditer(r"^\*" + re.escape(kw) + r"[ \t]*\n(.*?)(?=^\*)", text, re.S | re.M):
        out.append([ln for ln in m.group(1).splitlines() if not ln.startswith("$")])
    return out


def sec_thick(text):
    """*SECTION_SHELL(_TITLE) 두께 카드의 T1, T2"""
    rows = (blocks(text, "SECTION_SHELL_TITLE") or blocks(text, "SECTION_SHELL") or [[]])[0]
    vals = [ln for ln in rows if ln.split() and re.match(r"\s*[-0-9.]", ln)]
    return tuple(float(x) for x in vals[1].split()[:2]) if len(vals) > 1 else None


print("[1] 인클루드 *PARAMETER — 메인이 정의한 이름은 메인 값, 인클루드끼리는 먼저 값, LOCAL 아닌 변형은 모두 읽는다")
SECP = "*SECTION_SHELL\n" + f10(2, 2) + f10("&thk", "&t2", "&thk", "&thk")


def pdeck(head, mid=""):
    return ("*KEYWORD\n" + head + nodes() + PROPS + SOLID + "*PART\nskin\n" + f10(2, 2, 1) + mid + SECP
            + "*ELEMENT_SHELL\n" + f"{10:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}\n" + "*END\n")


EXPR_INC = "*KEYWORD\n*PARAMETER_EXPRESSION\nR thk 2.0*1.25\n*END\n"
T2 = "*PARAMETER_EXPRESSION\nR t2 thk*2.0\n"
for label, files, want in (
        ("메인 *PARAMETER thk 1.0 뒤 인클루드 식 thk 2.5 — 리뷰 H C1",
         {"model.k": pdeck("*PARAMETER\nR thk 1.0\n" + T2 + "*INCLUDE\nparams.k\n"), "params.k": EXPR_INC}, (1.0, 2.0)),
        ("인클루드 식 thk 2.5 가 맨 위, 메인 thk 1.0 이 뒤 — 메인 값(지금 규칙)",
         {"model.k": pdeck("*INCLUDE\nparams.k\n*PARAMETER\nR thk 1.0\n" + T2), "params.k": EXPR_INC}, (1.0, 2.0)),
        ("인클루드 둘이 thk 를 1.0·2.0 으로 정의 — 먼저 값 1.0(DFLAG=1)",
         {"model.k": pdeck("*INCLUDE\na.k\n*INCLUDE\nb.k\n" + T2), "a.k": "*KEYWORD\n*PARAMETER\nR thk 1.0\n*END\n",
          "b.k": "*KEYWORD\n*PARAMETER\nR thk 2.0\n*END\n"}, (1.0, 2.0)),
        ("인클루드 *PARAMETER_NOECHO — 리뷰 H C4",
         {"model.k": pdeck("*INCLUDE\nparams.k\n" + T2), "params.k": "*KEYWORD\n*PARAMETER_NOECHO\nR thk 2.5\n*END\n"}, (2.5, 5.0)),
        ("인클루드 *PARAMETER_MUTABLE",
         {"model.k": pdeck("*INCLUDE\nparams.k\n" + T2), "params.k": "*KEYWORD\n*PARAMETER_MUTABLE\nR thk 2.5\n*END\n"}, (2.5, 5.0)),
        ("인클루드 *PARAMETER_EXPRESSION_NOECHO",
         {"model.k": pdeck("*INCLUDE\nparams.k\n" + T2),
          "params.k": "*KEYWORD\n*PARAMETER_EXPRESSION_NOECHO\nR thk 1.0*2.5\n*END\n"}, (2.5, 5.0))):
    rc, log, text, _ = run(files)
    got = sec_thick(text)
    check(f"{label} — 두께 {want}·🔴 없음", rc == 0 and got == want and "🔴" not in log,
          f"rc={rc} got={got} {[ln for ln in log.splitlines() if '🔴' in ln]}")

print("[2] 요소 셋 — 빈 칸·0 은 요소가 아니고, *SET_SHELL·*SET_SOLID 는 같은 SID 여도 둘 다 남는다")
OTHER = ("*KEYWORD\n" + nodes() + SHELLP + "*MAT_ELASTIC\n"
         + f10(1, "7.85E-09", 210000, 0.3) + SHELLS + "*SET_SHELL\n" + f10(55) + f10(*range(21, 29)) + f10(29, 30) + "*END\n")
rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*END\n", "other.k": OTHER}, opt=IMPORT_OPT,
                       outname="model_imported.k")
rows = (blocks(text, "SET_SHELL_TITLE") or [[]])[0]
eids = [x for ln in rows[2:] for x in ln.split()]
check("IMPORT_MERGE_K *SET_SHELL 55 — 요소 23~32 만(0 칸이 기준 모델 EID 2 가 되지 않는다) — 리뷰 H C2",
      rc == 0 and eids == [str(e) for e in range(23, 33)], f"rc={rc} {eids} {log[-200:] if rc else ''}")
OTHER_S = ("*KEYWORD\n" + nodes() + PROPS + SOLID + "*SET_SOLID\n" + f10(66) + f10(1, 2) + "*END\n")
rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*END\n", "other.k": OTHER_S}, opt=IMPORT_OPT,
                       outname="model_imported.k")
rows = (blocks(text, "SET_SOLID_TITLE") or [[]])[0]
eids = [x for ln in rows[2:] for x in ln.split()]
check("IMPORT_MERGE_K *SET_SOLID 66 — 요소 3·4 만", rc == 0 and eids == ["3", "4"], f"rc={rc} {eids}")
rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + SHELLP + SHELLS
                        + "*SET_SHELL\n" + f10(5) + f10(21, 22) + "*SET_SOLID\n" + f10(5) + f10(1, 2) + "*END\n"})
sh = [x for b in blocks(text, "SET_SHELL_TITLE") for ln in b[2:] for x in ln.split()]
so = [x for b in blocks(text, "SET_SOLID_TITLE") for ln in b[2:] for x in ln.split()]
check("같은 SID 5 의 *SET_SHELL·*SET_SOLID — 둘 다 남는다 — 리뷰 H C3", rc == 0 and sh == ["21", "22"] and so == ["1", "2"],
      f"rc={rc} shell={sh} solid={so}")

print("[3] *ELEMENT_SHELL_THICKNESS — 빈 줄만 든 블록, N5 칸이 공백인 80자 카드 1 에서 죽지 않는다")
TH = "".join(f"{x:>16}" for x in (0.5, 0.5, 0.5, 0.5))
for label, body in (("8칸 빈 줄만", "\n\n"), ("I10 빈 줄만", None), ("80자 카드 1(N5~N8 공백)", "80")):
    if body is None:
        kw, data = "*ELEMENT_SHELL_THICKNESS %\n", "\n\n"
    elif body == "80":
        kw, data = "*ELEMENT_SHELL_THICKNESS\n", (f"{10:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}" + " " * 32 + "\n" + TH + "\n")
    else:
        kw, data = "*ELEMENT_SHELL_THICKNESS\n", body
    rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + SHELLP + kw + data + "*END\n"})
    check(f"{label} — rc 0 — 리뷰 H C6", rc == 0, f"rc={rc} {log[-250:]}")


def shells(text):
    out, f = [], False
    for ln in text.splitlines():
        if ln.startswith("*"):
            f = ln.startswith("*ELEMENT_SHELL")
        elif f and not ln.startswith("$") and ln.split():
            out.append(ln.split()[:2])
    return out


C8 = f"{10:8d}{2:8d}" + "".join(f"{n:8d}" for n in range(1, 9))   # 8절점 카드 1
for label, kw, data, want in (
        ("요소 하나짜리 THICKNESS 블록(행 2개) — 리뷰 H 기존 결함", "*ELEMENT_SHELL_THICKNESS\n",
         f"{10:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}\n" + TH + "\n", [["10", "2"]]),
        ("8절점 3카드 THICKNESS — 리뷰 H 기존 결함", "*ELEMENT_SHELL_THICKNESS\n",
         C8 + "\n" + TH + f"{0.0:>16}\n" + TH + "\n", [["10", "2"]]),
        ("일반 *ELEMENT_SHELL 80칸 공백 채움(N5~N8 공백)", "*ELEMENT_SHELL\n",
         f"{10:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}" + " " * 32 + "\n" + f"{11:8d}{2:8d}{5:8d}{6:8d}{7:8d}{8:8d}" + " " * 32 + "\n",
         [["10", "2"], ["11", "2"]])):
    rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + SHELLP + kw + data + "*END\n"})
    check(f"{label} — rc 0·셸 {len(want)}개", rc == 0 and shells(text) == want, f"rc={rc} {shells(text)} {log[-250:]}")

print("[4] *ELEMENT_MASS — MASS 는 17~32열, PID 는 33~40열(R16). KMM 이 자기 출력을 다시 읽어도 질량이 그대로")
MASS = "*ELEMENT_MASS\n" + f"{800:8d}{5:8d}{'1.2345678e-03':>16}{1:8d}\n"


def masses(text):
    out = []
    for b in blocks(text, "ELEMENT_MASS"):
        for ln in b:
            if ln.strip():
                out.append((int(ln[0:8]), int(ln[8:16]), float(ln[16:32]), int(ln[32:40] or 0)))
    return out


rc, log, text1, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + MASS + "*END\n"})
try:
    m1 = masses(text1)
except ValueError as e:
    m1 = f"ValueError {e}"
check("1차 출력 — 칸대로 읽어 EID 800·NID 5·MASS 1.2345678e-3·PID 1", rc == 0 and m1 == [(800, 5, 1.2345678e-3, 1)],
      f"rc={rc} {m1} {[ln for ln in text1.splitlines() if ln.startswith('     800')]}")
rc2, log2, text2, _ = run({"model.k": text1})
try:
    m2 = masses(text2)
except ValueError as e:
    m2 = f"ValueError {e}"
check("1차 출력을 다시 읽은 2차 출력 — 질량 요소가 그대로(누적 체인)", rc2 == 0 and m2 == [(800, 5, 1.2345678e-3, 1)],
      f"rc={rc2} {m2}")

print()
if FAILS:
    print(f"FAIL {len(FAILS)}건 — 실행 폴더를 남긴다: {BASE}")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
shutil.rmtree(BASE)
print("ALL PASS")
