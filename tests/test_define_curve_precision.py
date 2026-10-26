# *DEFINE_CURVE 머리 칸(SFA·SFO·OFFA·OFFO)이 KMM 출력에서 값을 잃지 않는지 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_define_curve_precision.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-10-26, 리뷰 L): KooDefineCurve 가 머리 칸을 >10.3f 로만 썼다. SFO 1.0E-6 → 0.000 이 되고 LS-DYNA 는 0 을
기본값 1.0 으로 읽어 커브가 10⁶ 배가 된다(R16 DEFINE_CURVE: "SFO … EQ.0.0: Default set to 1.0"). 0.0012 → 0.001,
1.0E6 → 11칸이라 뒤 칸을 밀었다. 1월(08ce963)부터. 서버 덱 1,175 커브 중 20개(실 덱 uvssoc SFO 0.0316 → 0.032).
10.3f 가 값을 그대로 담는 커브(1.0·0.0 등)는 예전 바이트 그대로여야 한다.
"""
import os
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
# LCID → (SFA, SFO, OFFA, OFFO) 글 — 7: 작은 값들, 8: 큰 SFO, 9: 10.3f 로 그대로 담기는 값(예전 바이트와 같아야 함)
CURVES = {7: ("0.0012", "1.0E-6", "0.0004", "2.5E-4"), 8: ("1.0", "1.0E6", "0.0", "0.0316"), 9: ("1.0", "2.5", "0.0", "0.0")}
FAILS = []


def check(name, cond, detail=""):
    print("  %-70s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def deck():
    nodes = "*NODE\n" + "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n" for i, (x, y, z) in enumerate(
        [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]))
    mat = "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
    curves = "".join("*DEFINE_CURVE\n" + f10(lc, 0, *h) + f"{0.0:>20}{250.0:>20}\n{1.0:>20}{300.0:>20}\n"
                     for lc, h in CURVES.items())
    return ("*KEYWORD\n" + nodes + "*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + mat + curves
            + "*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(1, 9)) + "\n*END\n")


def curve_headers(text):
    """출력의 *DEFINE_CURVE 머리 줄 {LCID: 줄}"""
    out, lines = {}, text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().upper() == "*DEFINE_CURVE":
            j = i + 1
            while j < len(lines) and lines[j].startswith("$"):
                j += 1
            out[int(lines[j][:10])] = lines[j]
    return out


def main():
    d = Path(tempfile.mkdtemp(prefix="curve_prec_"))
    (d / "model.k").write_text(deck())
    (d / "opt.txt").write_text(OPT)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=600, env=ENV)
    out = d / "model_trans.k"
    check("rc 0·출력", r.returncode == 0 and out.exists(), (r.stdout + r.stderr)[-500:])
    if out.exists():
        hdr = curve_headers(out.read_text(errors="replace"))
        check("커브 3개 그대로", sorted(hdr) == sorted(CURVES), str(sorted(hdr)))
        for lc, h in CURVES.items():
            ln = hdr.get(lc, "")
            got = [ln[a:a + 10] for a in (20, 30, 40, 50)]
            try:
                same = all(abs(float(g) - float(w)) <= 1e-12 * max(1.0, abs(float(w))) for g, w in zip(got, h))
            except ValueError:
                same = False
            check(f"LCID {lc}: SFA·SFO·OFFA·OFFO = {'·'.join(h)} (10칸 자리 그대로)", same, repr(ln))
        old9 = f"{9:>10}{0:>10}" + "".join(format(float(x), ">10.3f") for x in CURVES[9]) + f"{0:>10}{0:>10}"
        check("LCID 9: 10.3f 로 담기는 값은 예전 바이트 그대로", hdr.get(9, "") == old9, f"{hdr.get(9)!r} vs {old9!r}")
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:400])
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
