# KMM 경계 조건 리더·기록기 결함(v131 B1~B3)을 보는 회귀 시험 — 강체 처방 운동 PID·여러 절점 처방 운동·SPC 블록 되풀이
"""
실행: venv312/bin/python tests/test_v131_boundary.py   (KMM 3회, 10초 안팎)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-11-04, 남은 기존 결함 묶음 v131 — IMPORT_MERGE_K 를 고치다 찾았다)
  B1 *BOUNDARY_PRESCRIBED_MOTION_RIGID(_ID) 의 TYPEID(강체 PID)를 절점 번호로 찾아, 같은 번호 절점이 없으면 조건을 버렸고
     ('노드 미발견' 경고) 절점 번호가 바뀌면 다른 PID 를 썼다.
  B2 *BOUNDARY_PRESCRIBED_MOTION_NODE(_ID 없는 판)를 읽으면 TypeError 로 죽었다(단수 생성 함수를 인자 없이 부르고, 여러 절점 그릇의
     super()·기록기 속성도 틀렸다).
  B3 *BOUNDARY_SPC_NODE 블록이 둘 이상이면 블록마다 모든 블록의 절점을 되풀이해 썼다(가변 기본 인자 [] 를 같이 썼다).
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


def check(name, cond, detail=""):
    print("  %-80s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def run(name, deck):
    d = Path(tempfile.mkdtemp(prefix=f"v131b_{name}_"))
    (d / "model.k").write_text(deck)
    (d / "opt.txt").write_text(TRANS)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=600, env=ENV)
    p = d / "model_trans.k"
    return r.returncode, r.stdout + r.stderr, (p.read_text(errors="replace") if p.exists() else "")


def blocks(text, kw):
    """kw 와 같은 키워드 블록마다 데이터 줄(주석·빈 줄 뺌) 목록."""
    out, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("*"):
            cur = [] if ln.split()[0].upper() == kw else None
            if cur is not None:
                out.append(cur)
            continue
        if cur is not None and ln.strip() and not ln.startswith("$"):
            cur.append(ln)
    return out


# 솔리드 2개(절점 1~16) — 파트 1 일반, 파트 20 강체(절점 20 은 없다)
PTS = [(x, y, z) for z in (0.0, 1.0) for y in (0.0, 1.0) for x in (0.0, 1.0)] + \
      [(x + 3.0, y, z) for z in (0.0, 1.0) for y in (0.0, 1.0) for x in (0.0, 1.0)]
NODES = "*NODE\n" + "".join(f"{i:8d}{x:16.1f}{y:16.1f}{z:16.1f}\n" for i, (x, y, z) in enumerate(PTS, 1))
HEX = (1, 2, 4, 3, 5, 6, 8, 7)
BASE = ("*KEYWORD\n" + NODES + "*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in HEX) + "\n"
        + f"{2:8d}{20:8d}" + "".join(f"{n + 8:8d}" for n in HEX) + "\n"
        + "*PART\nbody\n" + f10(1, 1, 1) + "*PART\nrigid\n" + f10(20, 1, 20) + "*SECTION_SOLID\n" + f10(1, 1)
        + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000.0, 0.3) + "*MAT_RIGID\n" + f10(20, "7.85E-09", 210000.0, 0.3)
        + "*DEFINE_CURVE\n" + f10(1) + f"{0.0:20.4f}{1.0:20.4f}\n" + f"{1.0:20.4f}{1.0:20.4f}\n")


def main():
    # ── B1 강체 처방 운동의 PID ────────────────────────────────────────────────────────────────
    rc, log, t = run("b1", BASE + "*BOUNDARY_PRESCRIBED_MOTION_RIGID\n" + f10(20, 3, 2, 1, 1.0) + "*END\n")
    got = [int(b[-1][:10]) for kw in ("*BOUNDARY_PRESCRIBED_MOTION_RIGID", "*BOUNDARY_PRESCRIBED_MOTION_RIGID_ID")
           for b in blocks(t, kw) if b]
    check("B1 *BOUNDARY_PRESCRIBED_MOTION_RIGID: 같은 번호 절점이 없는 강체 PID 20 의 조건이 남는다", rc == 0 and got == [20],
          f"rc={rc} {got} " + log[-300:])

    # ── B2 여러 절점 처방 운동(_ID 없는 판) ─────────────────────────────────────────────────────
    rc, log, t = run("b2", BASE + "*BOUNDARY_PRESCRIBED_MOTION_NODE\n" + f10(3, 1, 0, 1, 1.0) + f10(5, 3, 0, 1, 1.0)
                     + "*BOUNDARY_PRESCRIBED_MOTION_NODE\n" + f10(4, 2, 0, 1, 1.0) + "*END\n")
    pm = [[(int(r[:10]), int(r[10:20])) for r in b] for b in blocks(t, "*BOUNDARY_PRESCRIBED_MOTION_NODE")]
    check("B2 *BOUNDARY_PRESCRIBED_MOTION_NODE 두 블록: 죽지 않는다", rc == 0 and "Traceback" not in log, f"rc={rc} " + log[-300:])
    check("B2 블록마다 제 절점·자유도만(3·X, 5·Z / 4·Y)", pm == [[(3, 1), (5, 3)], [(4, 2)]], str(pm))

    # ── B3 *BOUNDARY_SPC_NODE 블록 둘 ─────────────────────────────────────────────────────────
    rc, log, t = run("b3", BASE + "*BOUNDARY_SPC_NODE\n" + f10(1, 0, 1, 0, 0, 0, 0, 0)
                     + "*BOUNDARY_SPC_NODE\n" + f10(2, 0, 0, 1, 0, 0, 0, 0) + "*END\n")
    spc = [[int(r[:10]) for r in b] for b in blocks(t, "*BOUNDARY_SPC_NODE")]
    check("B3 *BOUNDARY_SPC_NODE 두 블록: 블록마다 제 절점만(1 / 2 — 되풀이 없음)", rc == 0 and spc == [[1], [2]], f"rc={rc} {spc}")

    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
