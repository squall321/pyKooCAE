# 리뷰 G 반영(빈 줄 부록 V·인클루드 파라미터·CASE·셸 셋·MAT_ADD_EROSION·CONTROL_ADAPTIVE·DWI 절점 소실) 회귀 시험
"""
실행: venv312/bin/python tests/test_reader_review_g.py
수정 전 코드로 돌려 실패하는지 볼 때: KMM_GEN=<옛 occProject/Generators> venv312/bin/python tests/test_reader_review_g.py

배경 (2026-10-24, 리뷰 G 와 그 확인 중 찾은 기존 결함 — 판정 근거는 R16 원문)
  [1] 빈 줄(Appendix V: 빈 줄은 기본값 카드, 기본값 없는 칸이 있으면 카드가 될 수 없다)
      *NODE(NID 기본값 none) 빈 줄이 어디서든 원점의 절점 0 을 만들었다. *DEFINE_CURVE 점 카드(A1·O1 기본값 0.0)는
      빈 줄에서 죽었다(LS-DYNA 는 (0,0) 으로 읽는다). *ELEMENT_SHELL_THICKNESS 는 카드 자리를 따라야 한다.
      *SET_SEGMENT 빈 줄은 절점 0 세그먼트를 만들었다. Ctrl-Z 는 파일 끝 표시라 그 앞 빈 줄은 이 규칙대로 읽힌다.
  [2] MERGE_K 는 리더와 같은 Ctrl-Z·줄 나누기('\n' 만)를 쓴다.
  [3] 맨 위에 인클루드한 파일의 *PARAMETER 가 메인 파일에 먹는다(LS-DYNA 는 *INCLUDE 를 그 자리에서 읽는다).
      치환 안 된 &참조만 🔴 — 제목·인클루드 이름은 숫자 칸이 아니다.
  [4] *CASE_BEGIN/END 표지는 MERGE_K·DECOMPOSE_K 도 쓰지 않는다.
  [5] *SET_SHELL·_LIST·_TITLE 이 든 덱이 출력에서 죽었다(7월 판부터). SID 도 첫 EID 로 바뀌었다.
  [6] MAT_ADD_EROSION 카드 2~5 가 출력에서 0 이 됐다(1월 첫 소스부터, 파괴 기준이 꺼짐). 5장이면 죽었다.
  [7] 짧은 *CONTROL_ADAPTIVE(ADPFREQ 만)가 읽는 도중 KMM 을 죽였다. 덤프는 카드 2~4 의 8번째 칸을 잃었다.
  [8] DWI DampingSpring + BoundaryDistance 에서 시편 파트가 둘 이상이면 시편 절점이 *NODE 에서 빠졌다.
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
ENV = dict(os.environ, PATH=str(ROOT / "venv312" / "bin") + ":" + os.environ.get("PATH", ""))   # ~/.local/bin/gmsh 회피
OPT = "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,0,0,0\n**EndTransform\n*End\n"
MERGE_OPT = ("*Inputfile\nmodel.k\n*Mode\nMERGE_K,1\n**MergeK,1\nForceInlinePreserved,true\n**EndMergeK\n"
             "*PreserveIncludes\nkeep.k\n*End\n")
MERGE_PLAIN = "*Inputfile\nmodel.k\n*Mode\nMERGE_K,1\n**MergeK,1\n**EndMergeK\n*End\n"
DEC_OPT = "*Inputfile\nmodel.k\n*Mode\nDECOMPOSE_K,1\n**DecomposeK,1\nGroup,g1,block\nOutputDir,dec\n**EndDecomposeK\n*End\n"
BASE = Path(tempfile.mkdtemp(prefix="reader_review_g_"))
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
TH = "".join(f"{x:>16}" for x in (0.5, 0.5, 0.5, 0.5))
C1 = [f"{10:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}", f"{11:8d}{2:8d}{5:8d}{6:8d}{7:8d}{8:8d}"]
C1W = [f"{10:10d}{2:10d}{1:10d}{2:10d}{3:10d}{4:10d}", f"{11:10d}{2:10d}{5:10d}{6:10d}{7:10d}{8:10d}"]
TH10 = "".join(f"{x:>16}" for x in (0.5, 0.5, 0.5, 0.5, 0.0))


def run(files, opt=OPT, outname="model_trans.k"):
    d = Path(tempfile.mkdtemp(dir=BASE))
    for name, text in files.items():
        Path(d, name).write_bytes(text.encode())
    Path(d, "opt.txt").write_text(opt)
    r = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt.txt"], cwd=d, capture_output=True, text=True,
                       timeout=900, env=ENV)
    out = Path(d, outname)
    return r.returncode, r.stdout + r.stderr, (out.read_text(errors="replace") if out.exists() else ""), d


def block(text, kw):
    """첫 *kw 블록의 데이터 줄(주석 뺌)"""
    m = re.search(r"^\*" + re.escape(kw) + r"[^\n]*\n(.*?)(?=^\*)", text, re.S | re.M)
    return [ln for ln in m.group(1).splitlines() if not ln.startswith("$")] if m else None


def node_ids(text):
    return [ln.split()[0] for ln in (block(text, "NODE") or []) if ln.split()]


def shells(text):
    out, f = [], False
    for ln in text.splitlines():
        if ln.startswith("*"):
            f = ln.startswith("*ELEMENT_SHELL")
        elif f and not ln.startswith("$") and ln.split():
            out.append(ln.split()[:2])
    return out


print("[1] 빈 줄은 부록 V 대로 — *NODE 는 건너뛰고, 커브 점은 (0,0), THICKNESS 는 카드 자리대로, SET_SEGMENT 는 건너뛴다")
WANT_N = [str(i) for i in range(1, 13)]
for label, deck in (("블록 끝(다음 키워드 앞)", "*KEYWORD\n" + nodes() + "\n" + PROPS + SOLID + "*END\n"),
                    ("*END 앞", "*KEYWORD\n" + PROPS + SOLID + nodes() + "\n*END\n"),
                    ("파일 끝(*END 없음)", "*KEYWORD\n" + PROPS + SOLID + nodes() + "\n"),
                    ("Ctrl-Z 앞(*END 없음) — 리뷰 G 1", "*KEYWORD\n" + PROPS + SOLID + nodes() + "\n\x1a"),
                    ("파일 중간 절점 사이", "*KEYWORD\n" + nodes().replace("\n       2", "\n\n       2") + PROPS + SOLID + "*END\n")):
    rc, log, text, _ = run({"model.k": deck})
    check(f"*NODE 빈 줄 · {label} — 절점 0 없음·12개 그대로", rc == 0 and node_ids(text) == WANT_N, f"rc={rc} {node_ids(text)[:4]}")
check("  건너뛰었다고 알린다", "NODE 블록의 빈 줄" in log, [ln for ln in log.splitlines() if "빈 줄" in ln])

CURVE = "*DEFINE_CURVE\n" + f10(7) + f"{0.0:>20}{0.0:>20}\n{1.0:>20}{2.0:>20}\n"


def curve_pts(text):
    rows = block(text, "DEFINE_CURVE") or []
    return [tuple(float(v) for v in ln.split()) for ln in rows[1:] if ln.split()]


for label, tail in (("블록 끝 + *END", "\n*END\n"), ("파일 끝", "\n"), ("Ctrl-Z 앞 — 리뷰 G 1", "\n\x1a")):
    rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + CURVE + tail})
    check(f"*DEFINE_CURVE 빈 점 카드 · {label} — 죽지 않고 (0,0) 으로 읽는다(LS-DYNA 와 같음)",
          rc == 0 and curve_pts(text) == [(0.0, 0.0), (1.0, 2.0), (0.0, 0.0)], f"rc={rc} {curve_pts(text)} {log[-200:]}")
check("  빈 점 카드를 알린다", "빈 점 카드 1개" in log, [ln for ln in log.splitlines() if "커브" in ln or "CURVE" in ln][:3])
rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*DEFINE_CURVE\n" + f10(7)
                        + f"{0.0:>20}{0.0:>20}\n{1.0:>20}\n*END\n"})
check("*DEFINE_CURVE 점 카드의 빈 칸(O1) — 기본값 0.0, 빈 점 카드 안내는 없음",
      rc == 0 and curve_pts(text) == [(0.0, 0.0), (1.0, 0.0)] and "빈 점 카드" not in log, f"rc={rc} {curve_pts(text)}")

for label, body in (("8칸 · 완전한 카드 뒤 빈 줄 둘 + Ctrl-Z(*END 없음) — 리뷰 G 1", f"{C1[0]}\n{TH}\n{C1[1]}\n{TH}\n\n\n\x1a"),
                    ("8칸 · 마지막 요소 뒤 빈 줄 + *END", f"{C1[0]}\n{TH}\n{C1[1]}\n{TH}\n\n*END\n"),
                    ("8칸 · 마지막 두께 카드 생략(블록이 카드 1 에서 끝남)", f"{C1[0]}\n{TH}\n{C1[1]}\n*END\n")):
    rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + SHELLP + "*ELEMENT_SHELL_THICKNESS\n" + body})
    check(f"THICKNESS {label} — 셸 2개", rc == 0 and shells(text) == [["10", "2"], ["11", "2"]], f"rc={rc} {shells(text)} {log[-200:]}")
for label, body in (("I10 · 마지막 두께 카드가 빈 줄 + *END — 리뷰 G 5", f"{C1W[0]}\n{TH10}\n{C1W[1]}\n\n*END\n"),
                    ("I10 · 마지막 두께 카드가 빈 줄 + 파일 끝", f"{C1W[0]}\n{TH10}\n{C1W[1]}\n\n"),
                    ("I10 · 마지막 두께 카드가 빈 줄 + Ctrl-Z", f"{C1W[0]}\n{TH10}\n{C1W[1]}\n\n\x1a"),
                    ("I10 · 두께 카드가 모두 빈 줄", f"{C1W[0]}\n\n{C1W[1]}\n\n*END\n"),
                    ("I10 · 완전한 쌍 사이 빈 줄 — 리뷰 G P1", f"{C1W[0]}\n{TH10}\n\n{C1W[1]}\n{TH10}\n*END\n")):
    rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + SHELLP + "*ELEMENT_SHELL_THICKNESS %\n" + body})
    check(f"THICKNESS {label} — 셸 2개", rc == 0 and shells(text) == [["10", "2"], ["11", "2"]], f"rc={rc} {shells(text)} {log[-200:]}")
check("  카드 1 자리 빈 줄을 건너뛰었다고 알린다", "ELEMENT_SHELL_THICKNESS 블록의 빈 줄 1개" in log,
      [ln for ln in log.splitlines() if "빈 줄" in ln])

SEG = "*SET_SEGMENT_TITLE\nsegs\n" + f10(5) + f10(1, 2, 3, 4) + "\n"
rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + SEG + "*END\n"})
segs = [ln.split()[:4] for ln in (block(text, "SET_SEGMENT_TITLE") or [])[2:] if ln.split()]
check("*SET_SEGMENT_TITLE 블록 끝 빈 줄 — 절점 0 세그먼트가 생기지 않는다(전수 점검)",
      rc == 0 and segs == [["1", "2", "3", "4"]], f"rc={rc} {segs}")
rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + SEG.replace("_TITLE\nsegs", "") + "*END\n"})
segs = [ln.split()[:4] for ln in (block(text, "SET_SEGMENT_TITLE") or [])[2:] if ln.split()]
check("*SET_SEGMENT 블록 끝 빈 줄 — 같음", rc == 0 and segs == [["1", "2", "3", "4"]], f"rc={rc} {segs}")

print("[2] MERGE_K — 리더와 같은 Ctrl-Z·줄 나누기")
keep = ("*KEYWORD\n*ELEMENT_SHELL_THICKNESS\n" + f"{C1[0]}\n{TH}\n{C1[1]}\n\n\x1a")   # 마지막 두께 카드가 빈 줄 + Ctrl-Z
rc, log, merged, d = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + SHELLP + "*INCLUDE\nkeep.k\n*END\n", "keep.k": keep},
                         opt=MERGE_OPT, outname="model_merged.k")
rc2, log2, text, _ = run({"model.k": merged})
check("빈 두께 카드 + Ctrl-Z 인클루드를 펼친 덱 — 다시 읽어도 셸 2개 — 리뷰 G 2",
      rc == 0 and rc2 == 0 and shells(text) == [["10", "2"], ["11", "2"]], f"rc={rc},{rc2} {shells(text)} {log2[-200:]}")
keep = "*KEYWORD\n$ note\f*END 는 주석 안이다\n" + CURVE + "*END\n"
rc, log, merged, d = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*INCLUDE\nkeep.k\n*END\n", "keep.k": keep},
                         opt=MERGE_OPT, outname="model_merged.k")
check("주석 안 FF 뒤의 '*END' 에서 멈추지 않는다(리더처럼 커브를 펼친다) — 리뷰 G P2",
      rc == 0 and "*DEFINE_CURVE" in merged, f"rc={rc} curve={'*DEFINE_CURVE' in merged}")

print("[3] 인클루드의 *PARAMETER 는 메인 파일에도 먹는다 · 치환 안 된 숫자 칸만 🔴")
SH2 = "*ELEMENT_SHELL\n" + f"{10:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}\n"
PSEC = "*SECTION_SHELL\n" + f10(2, 2) + f10("&thk", "&thk", "&thk", "&thk")


def sec_thick(text):
    rows = block(text, "SECTION_SHELL_TITLE") or block(text, "SECTION_SHELL") or []
    vals = [ln for ln in rows if ln.split() and re.match(r"\s*[-0-9.]", ln)]
    return float(vals[1].split()[0]) if len(vals) > 1 else None


def pdeck(head, tail="", sec=PSEC, part="*PART\nskin\n"):
    return ("*KEYWORD\n" + head + nodes() + PROPS + SOLID + part + f10(2, 2, 1) + sec + SH2 + tail + "*END\n")


for label, files in (
        ("맨 위 인클루드의 파라미터 파일 — 리뷰 G 3",
         {"model.k": pdeck("*INCLUDE\nparams.k\n"), "params.k": "*KEYWORD\n*PARAMETER\nR thk 2.5\n*END\n"}),
        ("메인 *PARAMETER_EXPRESSION 이 인클루드 값을 씀",
         {"model.k": pdeck("*INCLUDE\nparams.k\n*PARAMETER_EXPRESSION\nR thk thin*2.5\n"),
          "params.k": "*KEYWORD\n*PARAMETER\nR thin 1.0\n*END\n"}),
        ("중첩 인클루드(params → more)",
         {"model.k": pdeck("*INCLUDE\nparams.k\n"), "params.k": "*KEYWORD\n*INCLUDE\nmore.k\n*END\n",
          "more.k": "*KEYWORD\n*PARAMETER\nR thk 2.5\n*END\n"})):
    rc, log, text, _ = run(files)
    check(f"{label} — 두께 2.5·🔴 없음", rc == 0 and sec_thick(text) == 2.5 and "🔴" not in log,
          f"rc={rc} thick={sec_thick(text)} {[ln for ln in log.splitlines() if '🔴' in ln]}")
rc, log, text, _ = run({"model.k": pdeck("*INCLUDE\nparams.k\n"),
                        "params.k": "*KEYWORD\n*PARAMETER_LOCAL\nR thk 2.5\n*END\n"})
check("다른 파일의 *PARAMETER_LOCAL 은 메인에 먹지 않는다 — 🔴 로 알린다",
      rc == 0 and "치환되지 않은 &참조" in log and "&thk" in log, f"rc={rc} {[ln for ln in log.splitlines() if '🔴' in ln]}")
rc, log, text, _ = run({"model.k": pdeck("*PARAMETER\nR thk 2.5\n", part="*PART\nBracket &Clip\n",
                                         tail="*DEFINE_CURVE_TITLE\nLoad &Unload\n" + f10(9) + f"{0.0:>20}{0.0:>20}\n")})
check("파트 제목 'Bracket &Clip'·커브 제목 'Load &Unload' — 🔴 오경보 없음 — 리뷰 G 4",
      rc == 0 and "🔴" not in log and sec_thick(text) == 2.5, f"rc={rc} {[ln for ln in log.splitlines() if '🔴' in ln]}")
rc, log, text, _ = run({"model.k": pdeck("*PARAMETER\nR thk 2.5\n*INCLUDE\nmy &sub.k\n"), "my &sub.k": "*KEYWORD\n*END\n"})
check("인클루드 이름 'my &sub.k' — 🔴 오경보 없음 — 리뷰 G 4", rc == 0 and "🔴" not in log,
      f"rc={rc} {[ln for ln in log.splitlines() if '🔴' in ln]}")
glued = "*MAT_ELASTIC\n" + f"{3:>10}{'7.85E-09':>10}{'210000.0':>10}" + "&nope" + "\n"
rc, log, text, _ = run({"model.k": pdeck("*PARAMETER\nR thk 2.5\n", tail=glued)})
check("앞 칸에 붙은 '…210000.0&nope' 도 🔴 로 알린다 — 리뷰 G P3", "&nope" in log and "치환되지 않은 &참조" in log,
      f"rc={rc} {[ln for ln in log.splitlines() if '🔴' in ln]}")

print("[4] *CASE 표지는 MERGE_K·DECOMPOSE_K 도 쓰지 않는다 — 리뷰 G 6")
SPC = "*BOUNDARY_SPC_NODE\n" + f10(1, 0, 1, 1, 1, 0, 0, 0)
CASED = "*KEYWORD\n" + nodes() + PROPS + SOLID + "*CASE_BEGIN_1\nMEMORY=20M\n" + SPC + "*CASE_END_1\n*END\n"
rc, log, merged, d = run({"model.k": CASED}, opt=MERGE_PLAIN, outname="model_merged.k")
check("MERGE_K — 병합 덱에 *CASE_BEGIN 없음·안내함", rc == 0 and "*CASE_BEGIN" not in merged and "*CASE 구간 표지" in log,
      f"rc={rc} begin={'*CASE_BEGIN' in merged}")
rc, log, _, d = run({"model.k": CASED}, opt=DEC_OPT)
glob_k = "".join(p.read_text(errors="replace") for p in (d / "dec").glob("*.k")) if (d / "dec").exists() else ""
man = (d / "dec" / "decompose_manifest.json").read_text() if (d / "dec" / "decompose_manifest.json").exists() else ""
check("DECOMPOSE_K — 산출 .k 에 *CASE_BEGIN 없음·안내함·매니페스트에 'not written'",
      rc == 0 and glob_k and "*CASE_BEGIN" not in glob_k and "*CASE 구간 표지" in log and "not written" in man,
      f"rc={rc} files={bool(glob_k)} begin={'*CASE_BEGIN' in glob_k}")

print("[5] *SET_SHELL·_LIST·_TITLE — 출력에서 죽지 않고 SID·요소가 그대로")
SHELLS = "*ELEMENT_SHELL\n" + "".join(f"{e:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}\n" for e in range(21, 31))
for kw, head in (("SET_SHELL", ""), ("SET_SHELL_LIST", ""), ("SET_SHELL_TITLE", "my shells\n")):
    rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + SHELLP + SHELLS + f"*{kw}\n" + head + f10(55)
                            + f10(*range(21, 29)) + f10(29, 30) + "*END\n"})
    rows = block(text, "SET_SHELL_TITLE") or []
    nums = [ln.split() for ln in rows[1:]]
    sid = nums[0][0] if nums else None
    eids = [x for r in nums[1:] for x in r if x != "0"]
    check(f"*{kw} — rc 0·SID 55·요소 21~30", rc == 0 and sid == "55" and eids == [str(e) for e in range(21, 31)],
          f"rc={rc} sid={sid} eids={eids} {log[-200:] if rc else ''}")

print("[6] MAT_ADD_EROSION — 카드 원문 그대로(파괴 기준이 0 이 되던 것)")
E1 = f10(1, "", "", "", "", "", 1.0, 1.0)
E2 = f10("", "", "", 0.3, "", "", "", "")
E3 = f10(1, "", "", "", "", "", "", 77)
E4 = f10(55, 0.1, 0.2, 0.3, 0.4, 61, 62, 63)
E5 = f10(0.01, 0.6, 900.0, "1e-07")
for n, cards in ((2, [E1, E2]), (3, [E1, E2, E3]), (5, [E1, E2, E3, E4, E5])):
    rc, log, text, _ = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*MAT_ADD_EROSION\n" + "".join(cards) + "*END\n"})
    got = [ln.rstrip() for ln in (block(text, "MAT_ADD_EROSION") or [])]
    check(f"카드 {n}장 — rc 0·카드가 원문 그대로(MXEPS 0.3·LCREGD 77 …)",
          rc == 0 and got == [c.rstrip("\n").rstrip() for c in cards], f"rc={rc} {got} {log[-200:] if rc else ''}")

print("[7] *CONTROL_ADAPTIVE — 짧은 카드에서 죽지 않고, 덤프가 8번째 칸을 남긴다")
rc, log, text, d = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*CONTROL_ADAPTIVE\n" + f10(0.1) + "*END\n"})
check("ADPFREQ 만 준 카드 — rc 0", rc == 0, f"rc={rc} {log[-200:]}")
ca = "*CONTROL_ADAPTIVE\n" + f10(0.1, 5.0, 7, 3) + f10(*range(1, 9)) + f10(*range(11, 19)) + f10(*range(21, 29))
rc, log, text, d = run({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + ca + "*END\n"})
dump = (d / "model_dump.k").read_text() if (d / "model_dump.k").exists() else ""
rows = [ln.split() for ln in (block(dump, "CONTROL_ADAPTIVE") or [])]
check("ADPTYP 7 카드 4장 — 덤프의 카드 2~4 가 8칸(8·18·28) 그대로", rc == 0 and len(rows) == 4
      and rows[1][-1] == "8" and rows[2][-1] == "18" and rows[3][-1] == "28", f"rc={rc} {rows}")
check("  ADPTYP 7 머리말을 쓴다(판정이 뒤집혀 늘 1 이던 것)", "ADPFREQ              ADPTYP" in dump, "")

print("[8] DWI DampingSpring + BoundaryDistance — 시편 파트가 둘이어도 시편 절점이 *NODE 에 남는다")


def plate(nx=4, ny=4, h=0.5):
    idx, nid, out = {}, 0, []
    for k in range(2):
        for j in range(ny + 1):
            for i in range(nx + 1):
                nid += 1
                idx[(i, j, k)] = nid
                out.append(f"{nid:8d}{i * h:16.6f}{j * h:16.6f}{k * h:16.6f}")
    sol, eid = [], 0
    for j in range(ny):
        for i in range(nx):
            eid += 1
            n = [idx[(i, j, 0)], idx[(i + 1, j, 0)], idx[(i + 1, j + 1, 0)], idx[(i, j + 1, 0)],
                 idx[(i, j, 1)], idx[(i + 1, j, 1)], idx[(i + 1, j + 1, 1)], idx[(i, j + 1, 1)]]
            sol.append(f"{eid:8d}{1 if i < nx // 2 else 2:8d}" + "".join(f"{x:8d}" for x in n))
    return ("*KEYWORD\n*NODE\n" + "\n".join(out) + "\n"
            + "".join(f"*PART\np{p}\n" + f10(p, 1, 1) for p in (1, 2)) + "*SECTION_SOLID\n" + f10(1, 1)
            + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3) + "*ELEMENT_SOLID\n" + "\n".join(sol) + "\n*END\n")


DWI = ("*Inputfile\nmodel.k\n*Mode\nDROP_WEIGHT_IMPACT_TEST,1\n**DropWeightImpactTest,1\nTFinal,0.001\nDT,1e-06\n"
       "LocationX,1.0\nLocationY,1.0\nHeight,10\nInitialVelocityX,0\nInitialVelocityY,0\nInitialVelocityZ,0\n"
       "Gravity,9810.0\nImpactorType,Sphere\nImpactorDimension,0.3\nMeshSize,0.15\nDensityImpactor,7.85e-09\n"
       "YoungsModulusImpactor,200000.0\nPoissonRatioImpactor,0.3\nGenerationMode,DampingSpring\nOffsetDistance,0.05\n"
       "YoungsModulusWall,10000.0\nPoissonRatioWall,0.3\nDensityWall,1e-09\nBoundaryDistance,{bd}\n"
       "**EndDropWeightImpactTest\n*End\n")
for bd in (0.6, 50.0):
    rc, log, text, _ = run({"model.k": plate()}, opt=DWI.format(bd=bd), outname="model_dwit.k")
    have = set(node_ids(text))
    ref, f = set(), False
    for ln in text.splitlines():
        if ln.startswith("*"):
            f = ln.startswith("*ELEMENT_SOLID")
        elif f and not ln.startswith("$") and len(ln.split()) >= 10 and ln.split()[1] in ("1", "2"):
            ref.update(ln.split()[2:10])
    miss = sorted(ref - have, key=int)
    check(f"BoundaryDistance {bd} — 시편 솔리드가 쓰는 절점 {len(ref)}개가 모두 *NODE 에 있다", rc == 0 and ref and not miss,
          f"rc={rc} missing={miss[:8]} {log[-200:] if rc else ''}")

print()
if FAILS:
    print(f"FAIL {len(FAILS)}건 — 실행 폴더를 남긴다: {BASE}")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
shutil.rmtree(BASE)
print("ALL PASS")
