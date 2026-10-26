# *LOAD_BODY 의 SF 와 *CONTROL_DYNAMIC_RELAXATION 의 DRTOL·DRFCTR 가 KMM 출력에서 값을 잃지 않는지 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_load_body_dr_precision.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-10-26, 리뷰 N): 두 키워드가 사용자 덱 값을 >10.3f 로 썼다(62ba543·24135b3 와 같은 계열).
- *LOAD_BODY SF 1.0E-4 → 0.000 — 부록 V "When a field is blank or set to 0, then LS-DYNA applies a default value", SF 기본값
  1. 이라 하중이 10⁴ 배. kg-mm-ms 중력 9.81E-3 → 0.010(+1.9%).
- *CONTROL_DYNAMIC_RELAXATION DRTOL 1.0E-4 → 0.000(기본값 0.001 — 수렴 기준 10배 느슨), DRFCTR 0.9995 → 1.000(감쇠 없음 —
  기본값 .995). KooChainRun dynamic_relaxation 옵션으로 사용자가 주는 값이다.
리뷰 O: DimensionalTolerance 경로가 넣는 DR 상수(DRTOL 1E-5·EDTTL 1E-4)는 예전 출력에서 0.000 으로 잘려 늘 기본값으로 돌았다
(d83a1af 실측, 그 경로는 미변경으로 둠). 출력이 값을 지키면서 동작이 바뀌지 않게 그 상수를 실제로 쓰이던 0(기본값)으로 적었다 —
예제(dist/Examples/5.SimulationModify/DimensionalTolerance)의 DR 카드가 예전 바이트 그대로여야 한다.
"""
import os
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
    return ("*KEYWORD\n" + nodes + "*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1)
            + "*MAT_ELASTIC\n" + f10(1, "7.85E-06", 210, 0.3)
            + "*LOAD_BODY_Z\n" + f10(7, "9.81E-3") + "*LOAD_BODY_Y\n" + f10(7, "1.0E-4") + "*LOAD_BODY_X\n" + f10(7, "1.0")
            + "*CONTROL_DYNAMIC_RELAXATION\n" + f10(250, "1.0E-4", "0.9995", "1.0E20", "0.0", 0, "0.04", 0)
            + "*DEFINE_CURVE\n" + f10(7) + f"{0.0:>20}{1.0:>20}\n{1.0:>20}{1.0:>20}\n"
            + "*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(1, 9)) + "\n*END\n")


def first_data(text, kw):
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().upper() == kw:
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("*"):
                    break
                if lines[j].strip() and not lines[j].startswith("$"):
                    return lines[j]
    return ""


def fnum(s):
    try:
        return float(s)
    except ValueError:
        return None


def main():
    d = Path(tempfile.mkdtemp(prefix="load_dr_"))
    (d / "model.k").write_text(deck())
    (d / "opt.txt").write_text(OPT)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=600, env=ENV)
    out = d / "model_trans.k"
    check("rc 0·출력", r.returncode == 0 and out.exists(), (r.stdout + r.stderr)[-500:])
    if out.exists():
        t = out.read_text(errors="replace")
        for kw, sf in (("*LOAD_BODY_Z", 9.81e-3), ("*LOAD_BODY_Y", 1.0e-4), ("*LOAD_BODY_X", 1.0)):
            row = first_data(t, kw)
            check(f"{kw} SF {sf} 그대로(11~20열)", fnum(row[10:20]) == sf, repr(row))
        row = first_data(t, "*CONTROL_DYNAMIC_RELAXATION")
        got = (fnum(row[10:20]), fnum(row[20:30]), fnum(row[60:70]))
        check("DR DRTOL 1.0E-4·DRFCTR 0.9995·EDTTL 0.04 그대로", got == (1.0e-4, 0.9995, 0.04), repr(row))
    ex = ROOT / "occProject" / "Generators" / "dist" / "Examples" / "5.SimulationModify" / "DimensionalTolerance"
    d2 = Path(tempfile.mkdtemp(prefix="dimtol_dr_"))
    for f in ("PlateSolid.k", "DimensionalTolerance.txt"):
        shutil.copy(ex / f, d2 / f)
    r = subprocess.run(KMM_CMD + ["DimensionalTolerance.txt"], cwd=d2, capture_output=True, text=True, timeout=900, env=ENV)
    dt = d2 / "PlateSolid_dt.k"
    check("DimensionalTolerance 예제: rc 0·출력", r.returncode == 0 and dt.exists(), (r.stdout + r.stderr)[-400:])
    if dt.exists():
        row = first_data(dt.read_text(errors="replace"), "*CONTROL_DYNAMIC_RELAXATION")
        old = "       250     0.000     0.350 1.000e+99     0.300         0     0.000        -1"
        check("DimensionalTolerance DR 카드 예전 바이트 그대로(DRTOL·EDTTL = 0 → 기본값)", row.rstrip() == old, repr(row))
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:400])
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
