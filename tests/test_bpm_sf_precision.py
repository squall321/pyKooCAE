# *BOUNDARY_PRESCRIBED_MOTION 의 SF(곡선 배율)가 KMM 출력에서 값을 잃지 않는지 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_bpm_sf_precision.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-10-26, 리뷰 M): KooBoundaryNode 가 SF 를 >10.3f 로 썼다. SF 1.0E-4 → 0.000 이고 R16 은 "SF Load curve scale
factor. Default set to 1.0" 이라 LS-DYNA 가 운동을 10⁴ 배로 읽는다. SF 2.5E6 → '2500000.000'(11칸)이라 뒤 칸이 밀린다.
62ba543(*DEFINE_CURVE 머리)와 같은 계열 — 같은 _real10 을 쓴다. 서버 SF 1,431줄 중 손실 0.
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
SFS = ["1.0E-4", "2.5E6", "1.0"]
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
    mats = "*MAT_RIGID\n" + f10(1, "7.85E-09", 210000, 0.3) + f10(1.0, 7, 7) + "\n"
    bpm = "".join("*BOUNDARY_PRESCRIBED_MOTION_RIGID\n" + f10(1, d, 2, 7, sf, 0, "1.0E28", 0.0)
                  for d, sf in zip((1, 2, 3), SFS))
    curve = "*DEFINE_CURVE\n" + f10(7) + f"{0.0:>20}{0.0:>20}\n{1.0:>20}{1.0:>20}\n"
    return ("*KEYWORD\n" + nodes + "*PART\nbox\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + mats + bpm + curve
            + "*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(1, 9)) + "\n*END\n")


def bpm_rows(text):
    """출력의 BPM 데이터 줄(제목/ID 줄 뺌) — SF 는 41~50 열"""
    rows, lines = [], text.splitlines()
    for i, ln in enumerate(lines):
        if ln.upper().startswith("*BOUNDARY_PRESCRIBED_MOTION"):
            j = i + 1 + (1 if ln.upper().rstrip().endswith("_ID") else 0)
            while j < len(lines) and (lines[j].startswith("$") or not lines[j].strip()):
                j += 1
            if j < len(lines) and not lines[j].startswith("*"):
                rows.append(lines[j])
    return rows


def main():
    d = Path(tempfile.mkdtemp(prefix="bpm_sf_"))
    (d / "model.k").write_text(deck())
    (d / "opt.txt").write_text(OPT)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=600, env=ENV)
    out = d / "model_trans.k"
    check("rc 0·출력", r.returncode == 0 and out.exists(), (r.stdout + r.stderr)[-500:])
    if out.exists():
        rows = bpm_rows(out.read_text(errors="replace"))
        check("BPM 3장 그대로", len(rows) == 3, str(rows))
        for sf, row in zip(SFS, rows):
            try:
                same = abs(float(row[40:50]) - float(sf)) <= 1e-12 * max(1.0, abs(float(sf)))
                cols_ok = int(row[30:40]) == 7 and abs(float(row[60:70]) - 1.0e28) < 1e16   # SF 뒤 칸(DEATH 61~70열)도 제자리
            except ValueError:
                same = cols_ok = False
            check(f"SF {sf} 그대로(41~50열)·앞뒤 칸(LCID·DEATH) 안 밀림", same and cols_ok, repr(row))
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:400])
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
