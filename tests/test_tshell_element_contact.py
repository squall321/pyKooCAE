# *ELEMENT_TSHELL 을 요소로 읽어 TSHELL 파트가 DROP_ATTITUDE 접촉 집합(SINGLE_SURFACE·RobustContact 면·Tied 감지)에 들어가는지 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_tshell_element_contact.py   (KMM 3회, 약 30초)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-11-03, 리뷰 U 🟡3 → 기존 결함 묶음 A): KMM 은 *ELEMENT_TSHELL 을 해석하지 않고 원문으로만 다시 썼다. 그래서 TSHELL
파트는 요소가 없는 파트로 보여 DROP_ATTITUDE 의 SINGLE_SURFACE 파트 셋·바닥판 Outer·RobustContact 전체 외부 면·Tied 면 감지에서
모두 빠졌다. H8·H9 FPCB 처럼 TSHELL 파트가 있는 덱은 그 파트에 접촉이 없었다.
덱: 솔리드 파트 1(헥사 2개, z 0~1) 위에 TSHELL 파트 2(2개, z 1~1.5)가 맞물리고 TIED 로 묶임 + I10('%') TSHELL 파트 3(1개, 떨어져 있음).
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
# TSHELL 요소 연결(EID, PID, N1~N8)
# 파트 2 아랫면 13~18(z=1, 솔리드 윗면과 같은 자리)·윗면 19~24(z=1.5), 파트 3 은 x+10 에 떨어진 I10 블록 요소
TS = {2: (2, 13, 14, 17, 16, 19, 20, 23, 22), 3: (2, 14, 15, 18, 17, 20, 21, 24, 23), 4: (3, 29, 30, 31, 32, 33, 34, 35, 36)}


def check(name, cond, detail=""):
    print("  %-76s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def deck():
    pts = {}
    nid = 0
    for z in (0.0, 1.0):                       # 솔리드 절점 1~12 (x 0,1,2 × y 0,1 × z 0,1)
        for y in (0.0, 1.0):
            for x in (0.0, 1.0, 2.0):
                nid += 1
                pts[nid] = (x, y, z)
    # TSHELL 아랫면은 솔리드 윗면 절점을 따로 둔다(9~14 는 z=1 솔리드 윗면과 같은 자리) — TIED 로 묶는 꼴
    ts_nodes = {}
    for k, (x, y, z) in enumerate([(x, y, z) for z in (1.0, 1.5) for y in (0.0, 1.0) for x in (0.0, 1.0, 2.0)]):
        ts_nodes[9 + k] = (x, y, z)
    ts_nodes = {k + 4: v for k, v in ts_nodes.items()}          # 13~24 로 밀어 솔리드 절점과 겹치지 않게
    far = {21 + 8 + k: (x + 10.0, y, z) for k, (x, y, z) in enumerate([(x, y, z) for z in (0.0, 0.5) for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1))])}
    allp = dict(pts)
    allp.update(ts_nodes)
    allp.update(far)
    nodes = "*NODE\n" + "".join(f"{i:8d}{x:16.6f}{y:16.6f}{z:16.6f}\n" for i, (x, y, z) in sorted(allp.items()))
    sol = ("*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in (1, 2, 5, 4, 7, 8, 11, 10)) + "\n"
           + f"{5:8d}{1:8d}" + "".join(f"{n:8d}" for n in (2, 3, 6, 5, 8, 9, 12, 11)) + "\n")
    tsh = ("*ELEMENT_TSHELL\n" + "".join(f"{e:8d}" + "".join(f"{n:8d}" for n in TS[e]) + "\n" for e in (2, 3))
           + "*ELEMENT_TSHELL %\n" + f"{4:10d}" + "".join(f"{n:10d}" for n in TS[4]) + "\n")
    props = ("*PART\nhousing\n" + f10(1, 1, 1) + "*PART\nfpcb\n" + f10(2, 2, 1) + "*PART\nfpcb_far\n" + f10(3, 2, 1)
             + "*SECTION_SOLID\n" + f10(1, 1) + "*SECTION_TSHELL\n" + f10(2, 3, 0.8333, 5, 1, 0.0, 0, 0)
             + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3))
    tied = ("*CONTACT_TIED_SURFACE_TO_SURFACE\n" + f10(1, 2, 3, 3) + f10(0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, "1.0E+20")
            + f10(1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0))
    gen = "*CONTACT_AUTOMATIC_GENERAL\n" + f10(0, 0, 0, 0) + f10(0.2, 0.2) + f10("")
    return "*KEYWORD\n" + nodes + sol + tsh + props + tied + gen + "*END\n"


def tshell_cards(text):
    """출력의 *ELEMENT_TSHELL 카드 → {EID: (PID, N1~N8)} 과 블록 수."""
    out, lines, i, blocks, seen = {}, text.splitlines(), 0, 0, []
    while i < len(lines):
        u = lines[i].strip().upper()
        if u.startswith("*ELEMENT_TSHELL"):
            blocks += 1
            w = 10 if u.endswith("%") else 8
            i += 1
            while i < len(lines) and not lines[i].startswith("*"):
                ln = lines[i]
                if ln.strip() and not ln.startswith("$"):
                    try:
                        f = [int(ln[k * w:(k + 1) * w]) for k in range(10)]
                    except ValueError:      # 폭 표시('%')를 잃은 원문 블록 — LS-DYNA 도 8칸으로 잘못 읽는다
                        seen.append(("틀린 폭", ln.strip()[:40]))
                        i += 1
                        continue
                    seen.append(f[0])
                    out[f[0]] = tuple(f[1:])
                i += 1
            continue
        i += 1
    return out, blocks, seen


def run(name, opt):
    d = Path(tempfile.mkdtemp(prefix=f"tsheltc_{name}_"))
    (d / "model.k").write_text(deck())
    (d / "opt.txt").write_text(opt)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
    return d, r.returncode, r.stdout + r.stderr


def grab(log, needle):
    for ln in log.splitlines():
        if needle in ln:
            return ln
    return ""


def main():
    # TRANSFORM — 요소가 그대로·한 번씩
    d, rc, log = run("trans", TRANS)
    t = (d / "model_trans.k").read_text(errors="replace") if (d / "model_trans.k").exists() else ""
    cards, blocks, seen = tshell_cards(t)
    check("TRANSFORM: rc 0", rc == 0, f"rc={rc} " + log[-600:])
    check("TRANSFORM: TSHELL 3개(I10 '%' 블록 포함)를 읽었다고 개수 검사", "ELEMENT_TSHELL 개수 검사: 입력 3 = 등록 3" in log, grab(log, "ELEMENT_TSHELL"))
    check("TRANSFORM: *ELEMENT_TSHELL 연결(EID·PID·N1~N8)이 입력 그대로", cards == {e: TS[e] for e in TS}, str(cards))
    check("TRANSFORM: 같은 TSHELL 이 두 번 나가지 않음(원문 블록 중복 없음)", sorted(map(str, seen)) == ['2', '3', '4'], str(seen))
    # DROP_ATTITUDE — 일반 접촉 → SINGLE_SURFACE 파트 셋
    d, rc, log = run("drop_gen", DROP.format(extra=""))
    check("DROP: rc 0", rc == 0, f"rc={rc} " + log[-600:])
    ss = grab(log, "-> SINGLE_SURFACE(")
    check("DROP: GENERAL → SINGLE_SURFACE 파트 셋에 TSHELL 파트까지 3 parts", "3 parts" in ss, ss)
    ds = sorted(d.rglob("DropSet.k"))
    t = ds[0].read_text(errors="replace") if ds else ""
    cards, blocks, seen = tshell_cards(t)
    check("DROP: DropSet.k 의 *ELEMENT_TSHELL 연결이 입력 그대로·한 번씩", cards == {e: TS[e] for e in TS} and sorted(map(str, seen)) == ['2', '3', '4'],
          f"{cards} {seen}")
    # DROP_ATTITUDE + RobustContact — 외부 면·Tied 감지
    d, rc, log = run("drop_rc", DROP.format(extra="\nRobustContact,True"))
    check("RobustContact: rc 0", rc == 0, f"rc={rc} " + log[-600:])
    seg = grab(log, "전체 외부 segment")
    tied = grab(log, "Tied 인터페이스 segment 감지")
    # 솔리드 2개 외부 면 10 + TSHELL 파트 2 외부 면 10 + 파트 3 외부 면 6 = 26
    check("RobustContact: 전체 외부 면에 TSHELL 면 포함(10 + 10 + 6 = 26)", "26개" in seg, seg)
    check("RobustContact: 솔리드–TSHELL TIED 면을 감지(0 이 아님)", tied != "" and "— 0 Tied" not in tied, tied)
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
