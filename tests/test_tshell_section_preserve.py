# KMM 이 *SECTION_TSHELL(·_TITLE) 칸을 덱 값 그대로 쓰는지 보는 회귀 시험 — TRANSFORM·DROP_ATTITUDE(DropSet.k) 두 경로
"""
실행: venv312/bin/python tests/test_tshell_section_preserve.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-11-03, H8·H9 캠페인 보고): 원본 FPCB 단면 ELFORM 3·SHRF 0.8333·NIP 5 가 DropSet.k 에서 ELFORM 1·SHRF 1.0·
NIP 2·PROPT 1(LS-DYNA 기본값)로 바뀌었다. KooSectionManager 가 칸을 지역 변수로만 읽고 단면에 넣지 않았고, PROPT 를
빠뜨려 QR·ICOMP·TSHEAR 를 한 칸씩 밀려 읽었다. R16 카드 1 = SECID ELFORM SHRF NIP PROPT QR ICOMP TSHEAR,
ICOMP=1 이면 각도 NIP 개(카드당 8개, NIP 0 은 2개 — R16 "EQ.0: set to 2 integration points").
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
FAILS = []
TRANS = "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,0,0,0\n**EndTransform\n*End\n"
DROP = """*Inputfile
model.k
*RunDirectoryMode,True,runs
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,0
EulerPitching,0
EulerYawing,0
Height,50
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
InitialAngularVelocityX,0
InitialAngularVelocityY,0
InitialAngularVelocityZ,0
OffsetDistance,1
Density,7.85e-9
YoungsModulus,210000
PoissonRatio,0.3
tFinal,0.001
dt,0.0001
**EndDropAttitude
*End
"""
# (SECID, ELFORM, SHRF, NIP, PROPT, QR, ICOMP, TSHEAR, 각도)
SEC1 = (1, 3, 0.8333, 5, 1, 0.0, 0, 0, [])                       # H8·H9 FPCB 꼴
SEC2 = (2, 5, 0.75, 3, 2, 0.5, 1, 1, [0.0, 45.0, 90.0])         # _TITLE·ICOMP=1 — 각도 NIP 개
SEC3 = (3, 2, 0.8333333, 10, 1, 0.0, 1, 0, [10.0 * k for k in range(10)])   # 각도 두 카드(8+2)·SHRF 5/6 자리수
SEC4 = (4, 1, 1.0, 0, 1, 0.0, 1, 0, [30.0, 60.0])            # NIP 0 = 적분점 2개(R16) — ICOMP=1 이면 각도 2개


def check(name, cond, detail=""):
    print("  %-72s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def deck():
    pts = [(x, y, z) for z in (0.0, 0.5) for y in (0, 1) for x in (0, 1, 2)]
    nodes = "*NODE\n" + "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n" for i, (x, y, z) in enumerate(pts))
    s1 = SEC1
    s2 = SEC2
    secs = ("*SECTION_TSHELL\n" + f10(*s1[:8])
            + "*SECTION_TSHELL_TITLE\nfpcb_layered\n" + f10(*s2[:8]) + f10(*s2[8])
            + "*SECTION_TSHELL\n" + f10(*SEC3[:8]) + f10(*SEC3[8][:8]) + f10(*SEC3[8][8:])
            + "*SECTION_TSHELL\n" + f10(*SEC4[:8]) + f10(*SEC4[8]))
    parts = "*PART\nfpcb_a\n" + f10(1, 1, 1) + "*PART\nfpcb_b\n" + f10(2, 2, 1) + "*PART\nfpcb_c\n" + f10(3, 3, 1) + "*PART\nfpcb_d\n" + f10(4, 4, 1)
    mat = "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
    els = ("*ELEMENT_TSHELL\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in (1, 2, 5, 4, 7, 8, 11, 10)) + "\n"
           + f"{2:8d}{2:8d}" + "".join(f"{n:8d}" for n in (2, 3, 6, 5, 8, 9, 12, 11)) + "\n")
    return "*KEYWORD\n" + nodes + parts + secs + mat + els + "*END\n"


def tshell_sections(text):
    """출력의 TSHELL 단면 → {SECID: (ELFORM, SHRF, NIP, PROPT, QR, ICOMP, TSHEAR, [각도])}."""
    out, lines, i = {}, text.splitlines(), 0
    while i < len(lines):
        u = lines[i].strip().upper()
        if u.startswith("*SECTION_TSHELL"):
            i += 1
            if u.startswith("*SECTION_TSHELL_TITLE"):
                while i < len(lines) and lines[i].startswith("$"):
                    i += 1
                i += 1                                       # 제목 줄
            while i < len(lines) and lines[i].startswith("$"):
                i += 1
            c = [lines[i][k * 10:(k + 1) * 10].strip() for k in range(8)]
            i += 1
            angles = []
            while i < len(lines) and not lines[i].startswith("*"):
                if not lines[i].startswith("$") and lines[i].strip():
                    angles += [float(lines[i][k * 10:(k + 1) * 10]) for k in range(8) if lines[i][k * 10:(k + 1) * 10].strip()]
                i += 1
            fl = lambda s, d: float(s) if s else d
            out[int(float(c[0]))] = (int(fl(c[1], 1)), fl(c[2], 1.0), int(fl(c[3], 2)), int(fl(c[4], 1)), fl(c[5], 0.0),
                                     int(fl(c[6], 0)), int(fl(c[7], 0)), angles)
            continue
        i += 1
    return out


def want(s):
    return (s[1], s[2], s[3], s[4], s[5], s[6], s[7], list(s[8]))


def run(name, opt, out_glob):
    d = Path(tempfile.mkdtemp(prefix=f"tshell_{name}_"))
    (d / "model.k").write_text(deck())
    (d / "opt.txt").write_text(opt)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
    outs = sorted(d.glob(out_glob))
    return r, (outs[0].read_text(errors="replace") if outs else None), r.stdout + r.stderr


def main():
    for name, opt, glob in (("TRANSFORM", TRANS, "model_trans.k"), ("DROP_ATTITUDE(DropSet.k)", DROP, "runs/Run_*/DropSet.k")):
        r, out, log = run(name.split("(")[0].lower(), opt, glob)
        check(f"{name}: rc 0 · 출력 있음", r.returncode == 0 and out is not None, f"rc={r.returncode} " + log[-600:])
        if out is None:
            continue
        got = tshell_sections(out)
        check(f"{name}: *SECTION_TSHELL — ELFORM 3·SHRF 0.8333·NIP 5·PROPT 1 그대로", got.get(1) == want(SEC1), str(got.get(1)))
        check(f"{name}: *SECTION_TSHELL_TITLE — ELFORM 5·SHRF 0.75·NIP 3·PROPT 2·QR 0.5·ICOMP 1·TSHEAR 1·각도 0/45/90",
              got.get(2) == want(SEC2), str(got.get(2)))
        check(f"{name}: *SECTION_TSHELL — NIP 10 각도 두 카드(8+2)·SHRF 0.8333333 자리수 그대로", got.get(3) == want(SEC3), str(got.get(3)))
        check(f"{name}: *SECTION_TSHELL — NIP 0·ICOMP 1 이면 각도 2개(30/60) 그대로", got.get(4) == want(SEC4), str(got.get(4)))
        check(f"{name}: *ELEMENT_TSHELL 두 요소가 남음", out.count("*ELEMENT_TSHELL") >= 1
              and all(f"{e:8d}" in out for e in (1, 2)), "")
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
