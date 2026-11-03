# RobustContact 가 TIED 접촉 두께(SST·MST)를 덱 값 그대로 두고, TiedOptions 로 줄 때만 바꾸는지 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_robust_contact_tied_thickness.py   (KMM 4회, 약 1~2분)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-11-03 사용자 결정 "고친다 — 덱 값 보존"): DROP_ATTITUDE 의 RobustContact 는 TiedOptions 에 SAST·SBST 가
없으면 모든 TIED 접촉의 SST·MST 를 0.005 로 바꿨다(3d3f50c, 근거 기록 없음). R16 접촉 일반 주의 4 의 묶기 거리
δ = max(0.6×(두 두께 합), 0.05×최소 대각선)에 들어가는 셸 두께를 단위 없이 덮어, mm 덱에선 사실상 0·m 덱에선 5 mm 였다.
  robust      — RobustContact,True → 덱의 SST 0.3·MST 0.4 그대로
  robust_sast — + TiedOptions.SAST,0.1 → SST 0.1(지정)·MST 0.4(덱), 실제로 바꾼 칸(SST=0.1)을 로그에
  robust_lower — + TiedOptions.sast,0.1 → 칸 이름은 대문자라 아무것도 안 바뀐다. 덱 값 그대로 + 무시했다는 경고,
                 '바꿨다' 거짓 로그 없음(리뷰 U 🟡2 — 예전엔 받은 키를 그대로 찍었다)
  plain       — RobustContact 없음 → 그대로
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


def check(name, cond, detail=""):
    print("  %-72s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def deck():
    pts = [(x, y, z) for z in (0.0, 1.0) for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1))]
    pts += [(x, y, z) for z in (1.0, 2.0) for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1))]
    nodes = "*NODE\n" + "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n" for i, (x, y, z) in enumerate(pts))
    els = ("*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(1, 9)) + "\n"
           + f"{2:8d}{2:8d}" + "".join(f"{n:8d}" for n in range(9, 17)) + "\n")
    props = ("*PART\nlower\n" + f10(1, 1, 1) + "*PART\nupper\n" + f10(2, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1)
             + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3))
    tied = ("*CONTACT_TIED_SURFACE_TO_SURFACE\n" + f10(1, 2, 3, 3) + f10(0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, "1.0E+20")
            + f10(1.0, 1.0, 0.3, 0.4, 1.0, 1.0, 1.0, 1.0))
    return "*KEYWORD\n" + nodes + els + props + tied + "*END\n"


CFG = """*Inputfile
model.k
*RunDirectoryMode,True,out
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,0
EulerPitching,0
EulerYawing,0
Height,100
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
InitialAngularVelocityX,0
InitialAngularVelocityY,0
InitialAngularVelocityZ,0
OffsetDistance,0.05
Density,7.85e-9
YoungsModulus,2.0e5
PoissonRatio,0.3
tFinal,0.001
dt,1e-6{extra}
**EndDropAttitude
*End
"""


def tied_card3(text):
    """출력의 첫 *CONTACT_TIED_SURFACE_TO_SURFACE 카드 3(SFS SFM SST MST …) → [실수 8개]."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        u = ln.strip().upper()
        if u.startswith("*CONTACT_TIED_SURFACE_TO_SURFACE"):
            data, j = [], i + 1
            while j < len(lines) and not lines[j].startswith("*"):
                if not lines[j].startswith("$") and lines[j].strip():
                    data.append(lines[j])
                j += 1
            if "_ID" in u or "_TITLE" in u:
                data = data[1:]
            if len(data) < 3:
                return None
            return [float(data[2][k * 10:(k + 1) * 10] or 0) for k in range(8)]
    return None


def run(name, extra):
    d = Path(tempfile.mkdtemp(prefix=f"tiedthk_{name}_"))
    (d / "model.k").write_text(deck())
    (d / "opt.txt").write_text(CFG.format(extra=extra))
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
    outs = [p for p in d.rglob("DropSet.k") if "/Output/" not in str(p) and "/DynamicRelaxation/" not in str(p)]
    return r, (outs[0].read_text(errors="replace") if outs else None), r.stdout + r.stderr


def main():
    for name, extra, sst, mst, log_needle in (
            ("robust", "\nRobustContact,True", 0.3, 0.4, None),
            ("robust_sast", "\nRobustContact,True\nTiedOptions.SAST,0.1", 0.1, 0.4, "applied"),
            ("robust_lower", "\nRobustContact,True\nTiedOptions.sast,0.1", 0.3, 0.4, "ignored"),
            ("plain", "", 0.3, 0.4, None)):
        r, out, log = run(name, extra)
        check(f"{name}: rc 0 · DropSet.k", r.returncode == 0 and out is not None, f"rc={r.returncode} " + log[-600:])
        if out is None:
            continue
        c3 = tied_card3(out)
        check(f"{name}: TIED 카드 3 SST {sst}·MST {mst}", c3 is not None and abs(c3[2] - sst) < 1e-9 and abs(c3[3] - mst) < 1e-9,
              str(c3))
        mod_lines = [ln for ln in log.splitlines() if "[ModifyTiedParameters]" in ln]
        if log_needle == "applied":
            check(f"{name}: 로그가 실제로 바꾼 칸(SST=0.1)을 적음", any("SST=0.1" in ln and "바꿨다" in ln for ln in mod_lines), str(mod_lines))
        if log_needle == "ignored":
            check(f"{name}: 맞는 칸이 없는 키(sast)를 무시했다고 경고", any("sast" in ln and "무시" in ln for ln in mod_lines), str(mod_lines))
            check(f"{name}: '바꿨다' 거짓 로그 없음", not any("바꿨다" in ln for ln in log.splitlines()), str(mod_lines))
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
