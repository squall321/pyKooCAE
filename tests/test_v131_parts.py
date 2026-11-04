# KMM 파트·요소·단면 결함 묶음(v131 P1~P4·R1~R2)을 보는 회귀 시험 — *PART_CONTACT·*ELEMENT_SHELL_THICKNESS·NODUMP·사용자 솔리드 카드·원문 번호 예약
"""
실행: venv312/bin/python tests/test_v131_parts.py   (KMM 약 14회, 1~2분)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-11-04, 남은 기존 결함 묶음 — docs/kmm_remaining_defects_20261104/)
  P1 *PART_CONTACT 를 파트로 읽지 않아 그 파트의 솔리드·셸이 사라졌다(rc 3). 한 블록에 파트가 둘 이상이면 덤프 기록기가 죽었다(rc 1).
     R16: 카드 묶음(제목·카드 2·접촉 카드 8)을 다음 키워드까지 되풀이한다.
  P2 *ELEMENT_SHELL_THICKNESS 의 요소별 두께를 읽고도 일반 *ELEMENT_SHELL 로 써서, 두께가 단면 두께로 조용히 바뀌었다.
  P3 *CONTROL_MPP_IO_NODUMP 를 매니저가 '*' 없는 이름과 비교해 못 썼다 — 뒤에 빈 줄이 있거나 DECOMPOSE_K 면 사라졌다.
  P4 *SECTION_SOLID ELFORM 101~105 의 사용자 카드(카드 3·적분점 NIP 장·속성 ceil(LMC/8) 장)를 카드 1 로 읽어 유령 단면이 생기고
     실제 단면 번호를 밀어냈다.
  R1·R2 원문으로 두는 *PART_* 변형의 PID 와 원문 요소의 EID 를 번호 매기기에 넣지 않아, KMM 이 새로 만드는 파트·요소와 겹칠 수 있었다.
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


def run(name, deck, opt=TRANS):
    d = Path(tempfile.mkdtemp(prefix=f"v131p_{name}_"))
    (d / "model.k").write_text(deck)
    (d / "opt.txt").write_text(opt)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
    return d, r.returncode, r.stdout + r.stderr


def out_text(d, name="model_trans.k"):
    p = d / name
    return p.read_text(errors="replace") if p.exists() else ""


def no_tb(log):
    return "Traceback (most recent call last)" not in log


def blocks(text, kw, exact=False):
    """kw 로 시작(exact 면 같은)하는 키워드 블록마다 (키워드 줄, 데이터 줄(주석 뺌)) 목록."""
    out, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("*"):
            h = ln.split()[0].upper()
            cur = [] if (h == kw if exact else h.startswith(kw)) else None
            if cur is not None:
                out.append((ln, cur))
            continue
        if cur is not None and not ln.startswith("$"):
            cur.append(ln)
    return out


def eids(text):
    """요소 블록의 EID 목록(8칸·'%' 10칸). 질량·이산 요소 포함."""
    ids = []
    for head, rows in blocks(text, "*ELEMENT_"):
        w = 10 if head.split()[1:2] == ["%"] else 8
        thick = "THICKNESS" in head.upper()
        k = 0
        for r in rows:
            if not r.strip():
                if thick:
                    k += 1
                continue
            if thick and k % 2 == 1:
                k += 1
                continue
            try:
                ids.append((head.split()[0].upper(), int(r[:w])))
            except ValueError:
                pass
            k += 1
    return ids


NODES16 = "*NODE\n" + "".join(f"{i:8d}{x:16.1f}{y:16.1f}{z:16.1f}\n" for i, (x, y, z) in enumerate(
    [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1), (2, 0, 0), (2, 1, 0), (2, 0, 1), (2, 1, 1),
     (3, 0, 0), (3, 1, 0), (3, 0, 1), (3, 1, 1)], 1))
PROPS = ("*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000.0, 0.3) + "*SECTION_SOLID\n" + f10(1, 1)
         + "*SECTION_SHELL\n" + f10(2, 2, 1.0, 2) + f10(1.0, 1.0, 1.0, 1.0) + "*SECTION_TSHELL\n" + f10(3, 1, 1.0, 2, 1))
ELEMS = ("*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in (1, 2, 3, 4, 5, 6, 7, 8)) + "\n"
         + f"{2:8d}{2:8d}" + "".join(f"{n:8d}" for n in (2, 9, 10, 3, 6, 11, 12, 7)) + "\n"
         + "*ELEMENT_TSHELL\n" + f"{3:8d}{3:8d}" + "".join(f"{n:8d}" for n in (9, 13, 14, 10, 11, 15, 16, 12)) + "\n"
         + "*ELEMENT_SHELL\n" + f"{4:8d}{4:8d}" + "".join(f"{n:8d}" for n in (1, 2, 6, 5)) + "\n")
C2 = f10(0.2, 0.1, 0.0, 0.0, 0.5, 1.0, 1.0).rstrip("\n")
C4 = f10(0.3, 0.2, 0.0, 0.0, 0.0, 1.0, 1.0).rstrip("\n")
C3 = f10(0.3).rstrip("\n")


def pc_deck(one_block):
    sets2 = "solid with contact card\n" + f10(2, 1, 1) + C2 + "\n"
    sets4 = "shell with contact card\n" + f10(4, 2, 1) + C4 + "\n"
    pcs = ("*PART_CONTACT\n" + sets2 + sets4) if one_block else ("*PART_CONTACT\n" + sets2 + "*PART_CONTACT\n" + sets4)
    return ("*KEYWORD\n" + PROPS + "*PART\nsolid normal\n" + f10(1, 1, 1) + pcs
            + "*PART_CONTACT\ntshell with contact card\n" + f10(3, 3, 1) + C3 + "\n" + NODES16 + ELEMS + "*END\n")


def main():
    # ── P1 *PART_CONTACT ──────────────────────────────────────────────────────────────────────
    for one in (True, False):
        tag = "한 블록에 두 파트" if one else "블록마다 한 파트"
        d, rc, log = run(f"p1_{int(one)}", pc_deck(one))
        t = out_text(d)
        pcs = {}
        for head, rows in blocks(t, "*PART_CONTACT", exact=True):
            data = [r for r in rows if r.strip()]
            for k in range(0, len(data) - 2, 3):
                try:
                    pcs[int(data[k + 1][:10])] = data[k + 2].rstrip()
                except ValueError:
                    pass
        got = sorted(set(e for _, e in eids(t)))
        check(f"P1 {tag}: rc 0·Traceback 없음", rc == 0 and no_tb(log), f"rc={rc} " + log[-500:])
        check(f"P1 {tag}: 요소 1~4(솔리드·TSHELL·셸)가 모두 남는다", got == [1, 2, 3, 4], str(got))
        check(f"P1 {tag}: *PART_CONTACT 2·3·4 가 접촉 카드 원문과 함께 나간다",
              pcs.get(2) == C2.rstrip() and pcs.get(4) == C4.rstrip() and pcs.get(3) == C3.rstrip(), str(pcs))
    # ── R1·R2 원문 *PART_* 변형 PID·원문 요소 EID 예약(DROP 바닥판이 그 번호를 받지 않는다) ─────────────────
    raw_pid = ("*PART_INERTIA\ninertia part\n" + f10(7, 1, 1) + f10(0.0, 0.0, 0.0, 1.0e-6, 0, 0)
               + f10(1.0e-6, 0.0, 0.0, 1.0e-6, 0.0, 1.0e-6) + f10(0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    disc = ("*SECTION_DISCRETE\n" + f10(6, 0, 0.0, 0.0, 0.0, 0.0) + f10(0.0, 0.0) + "*MAT_SPRING_ELASTIC\n" + f10(6, 1000.0)
            + "*PART\nspring\n" + f10(6, 6, 6) + "*ELEMENT_DISCRETE\n" + f"{50:8d}{6:8d}{1:8d}{16:8d}{0:8d}{1.0:16.4f}{0:8d}{0.0:16.4f}\n")
    rdeck = ("*KEYWORD\n" + PROPS + "*PART\nsolid normal\n" + f10(1, 1, 1) + "*PART\nsolid two\n" + f10(2, 1, 1) + raw_pid + disc
             + NODES16 + ELEMS.split("*ELEMENT_TSHELL")[0] + "*END\n")
    drop = ("*Inputfile\nmodel.k\n*RunDirectoryMode,True,runs\n*Mode\nDROP_ATTITUDE,1\n**DropAttitude,1\nEulerRolling,0\n"
            "EulerPitching,0\nEulerYawing,0\nHeight,100\nInitialVelocityX,0\nInitialVelocityY,0\nInitialVelocityZ,0\n"
            "InitialAngularVelocityX,0\nInitialAngularVelocityY,0\nInitialAngularVelocityZ,0\nOffsetDistance,0.05\n"
            "Density,7.85e-9\nYoungsModulus,2.0e5\nPoissonRatio,0.3\ntFinal,0.001\ndt,1e-6\n**EndDropAttitude\n*End\n")
    d, rc, log = run("r12", rdeck, drop)
    ds = [p for p in sorted(d.rglob("DropSet.k")) if p.parent.parent.name == "runs"]
    t = ds[0].read_text(errors="replace") if ds else ""
    pids = []
    for head, rows in blocks(t, "*PART"):   # 제목 줄은 빈 줄일 수 있다(바닥판 *PART) — 거르면 카드 2 를 엉뚱한 줄에서 읽는다
        if head.split()[0].upper() in ("*PART", "*PART_INERTIA") and len(rows) >= 2:
            try:
                pids.append(int(rows[1][:10]))
            except ValueError:
                pass
    ids = [e for _, e in eids(t)]
    check("R1 DROP: 원문 *PART_INERTIA 7(=다음 PID) 과 KMM 이 만드는 파트 번호가 겹치지 않는다",
          rc in (0, 3) and pids.count(7) == 1 and len(pids) == len(set(pids)), f"rc={rc} pids={pids}")
    check("R2 DROP: 원문 *ELEMENT_DISCRETE 50 과 바닥판 요소 번호가 겹치지 않는다", ids.count(50) == 1, f"50×{ids.count(50)}")

    # ── P2 *ELEMENT_SHELL_THICKNESS ──────────────────────────────────────────────────────────
    th_nodes = "*NODE\n" + "".join(f"{i:8d}{x:16.1f}{y:16.1f}{0.0:16.1f}\n" for i, (x, y) in enumerate(
        [(0, 0), (1, 0), (1, 1), (0, 1), (2, 0), (2, 1), (3, 0), (3, 1)], 1))
    T1 = "".join(f"{x:>16}" for x in ("0.5", "0.6", "0.7", "0.8", "30.0"))
    T3 = "".join(f"{x:>16}" for x in ("0.25", "0.25", "0.25", "0.25"))
    th_deck = ("*KEYWORD\n*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000.0, 0.3) + "*SECTION_SHELL\n" + f10(1, 2, 1.0, 2) + f10(1.0, 1.0, 1.0, 1.0)
               + "*PART\nshell thickness part\n" + f10(1, 1, 1) + th_nodes + "*ELEMENT_SHELL_THICKNESS\n"
               + f"{1:8d}{1:8d}{1:8d}{2:8d}{3:8d}{4:8d}\n" + T1 + "\n" + f"{2:8d}{1:8d}{2:8d}{5:8d}{6:8d}{3:8d}\n\n"
               + f"{3:8d}{1:8d}{5:8d}{7:8d}{8:8d}{6:8d}\n" + T3 + "\n*END\n")

    def thick(text):
        """*ELEMENT_SHELL_THICKNESS → {EID: (절점들, 두께 카드 숫자들)}."""
        out = {}
        for head, rows in blocks(text, "*ELEMENT_SHELL_THICKNESS"):
            w = 10 if head.split()[1:2] == ["%"] else 8
            for k in range(0, len(rows) - 1, 2):
                c1, c2 = rows[k], rows[k + 1]
                try:
                    e = int(c1[:w])
                except ValueError:
                    continue
                ns = [int(c1[w * j:w * (j + 1)]) for j in range(2, 6)]
                out[e] = (ns, [float(c2[16 * j:16 * (j + 1)]) for j in range(5) if c2[16 * j:16 * (j + 1)].strip()])
        return out
    d, rc, log = run("p2", th_deck)
    t = out_text(d)
    th = thick(t)
    check("P2 THICKNESS: rc 0", rc == 0 and no_tb(log), f"rc={rc} " + log[-300:])
    check("P2 THICKNESS: 요소 1(0.5/0.6/0.7/0.8·BETA 30)·2(빈 두께 카드)·3(0.25×4) 의 두께 카드가 그대로 나간다",
          th.get(1, ([], []))[1] == [0.5, 0.6, 0.7, 0.8, 30.0] and th.get(2, ([], [0]))[1] == [] and th.get(3, ([], []))[1] == [0.25] * 4,
          str(th))
    if t:
        d2, rc2, log2 = run("p2rt", t)
        th2 = thick(out_text(d2))
        check("P2 THICKNESS: 출력을 다시 읽어도 같다(누적 체인)", rc2 == 0 and th2 == th, str(th2))
    d, rc, log = run("p2m", th_deck, "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nMirror,XY\n**EndTransform\n*End\n")
    th = thick(out_text(d))
    pair = dict(zip(th.get(1, ([], []))[0], th.get(1, ([], []))[1][:4]))
    check("P2 THICKNESS MIRROR: 절점과 두께의 짝이 그대로(1→0.5·2→0.6·3→0.7·4→0.8)", pair == {1: 0.5, 2: 0.6, 3: 0.7, 4: 0.8}, str(th))
    beta = th_deck.replace("*ELEMENT_SHELL_THICKNESS\n", "*ELEMENT_SHELL_BETA\n").replace(T1 + "\n", f"{30.0:16.4f}\n").replace(
        f"{2:8d}{1:8d}{2:8d}{5:8d}{6:8d}{3:8d}\n\n", f"{2:8d}{1:8d}{2:8d}{5:8d}{6:8d}{3:8d}\n{0.0:16.4f}\n").replace(T3 + "\n", f"{0.0:16.4f}\n")
    d, rc, log = run("p2b", beta)
    check("P2 *ELEMENT_SHELL_BETA: 원문으로 둔다고 알린다(파트가 요소 없이 보이는 것을 숨기지 않는다)",
          "*ELEMENT_SHELL_BETA" in log and "원문 그대로" in log, log[-400:])

    # ── P2Q 2차 셸(QUAD8·TRI6)·3절점 두께 + MIRROR — 중간 절점은 새 변의 가운데, 두께는 절점을 따라간다 ─────────────────
    q_xy = [(0, 0), (2, 0), (2, 2), (0, 2), (1, 0), (2, 1), (1, 2), (0, 1),      # QUAD8 1~4 꼭짓점·5~8 중간(1-2·2-3·3-4·4-1)
            (3, 0), (5, 0), (3, 2), (4, 0), (4, 1), (3, 1),                      # TRI6 9~11 꼭짓점·12~14 중간(9-10·10-11·11-9)
            (6, 0), (7, 0), (6, 1)]                                              # TRI3(N4=0)·퇴화 사각형(N4=N3) 15~17
    q_nodes = "*NODE\n" + "".join(f"{i:8d}{x:16.1f}{y:16.1f}{0.0:16.1f}\n" for i, (x, y) in enumerate(q_xy, 1))
    q_thk = {**{n: 1.0 + n / 10 for n in range(1, 9)}, **{n: 2.0 + (n - 8) / 10 for n in range(9, 15)},
             15: 0.1, 16: 0.2, 17: 0.3}
    s16 = lambda *v: "".join(f"{x:>16}" for x in v) + "\n"
    q_deck = ("*KEYWORD\n*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000.0, 0.3) + "*SECTION_SHELL\n" + f10(1, 23, 1.0, 2) + f10(1.0, 1.0, 1.0, 1.0)
              + "*SECTION_SHELL\n" + f10(2, 2, 1.0, 2) + f10(1.0, 1.0, 1.0, 1.0)
              + "*PART\nquadratic\n" + f10(1, 1, 1) + "*PART\nlinear\n" + f10(2, 2, 1) + q_nodes
              + "*ELEMENT_SHELL_THICKNESS\n" + "".join(f"{v:8d}" for v in (1, 1, 1, 2, 3, 4, 5, 6, 7, 8)) + "\n"
              + s16(*(f"{q_thk[n]:.1f}" for n in (1, 2, 3, 4)), "0.0") + s16(*(f"{q_thk[n]:.1f}" for n in (5, 6, 7, 8)))
              + "".join(f"{v:8d}" for v in (2, 1, 9, 10, 11, 12, 13, 14, 0, 0)) + "\n"
              + s16(*(f"{q_thk[n]:.1f}" for n in (9, 10, 11, 12)), "0.0") + s16(f"{q_thk[13]:.1f}", f"{q_thk[14]:.1f}")
              + "*ELEMENT_SHELL_THICKNESS\n" + "".join(f"{v:8d}" for v in (3, 2, 15, 16, 17, 0)) + "\n"
              + s16("0.1", "0.2", "0.3", "0.3") + "".join(f"{v:8d}" for v in (4, 2, 15, 16, 17, 17)) + "\n"
              + s16("0.1", "0.2", "0.3", "0.3") + "*END\n")

    def q_read(text):
        """출력 → ({NID: (x, y)}, {EID: (절점들, 두께들)}) — 두께 블록은 N5 가 있으면 요소마다 카드 3장, 일반 *ELEMENT_SHELL 은
        두께 없이 카드 1 만(중간 절점 판정은 두께를 쓰든 말든 본다)."""
        xy, el = {}, {}
        for head, rows in blocks(text, "*NODE", exact=True):
            for r in rows:
                try:
                    xy[int(r[:8])] = (float(r[8:24]), float(r[24:40]))
                except ValueError:
                    pass
        for head, rows in blocks(text, "*ELEMENT_SHELL"):
            thick = head.split()[0].upper() == "*ELEMENT_SHELL_THICKNESS"
            k = 0
            while k < len(rows):
                c1 = rows[k]
                try:
                    e = int(c1[:8])
                except ValueError:
                    k += 1
                    continue
                ns = [int(c1[8 * j:8 * (j + 1)]) for j in range(2, 10) if c1[8 * j:8 * (j + 1)].strip()]
                ns = [n for n in ns if n]
                cards = rows[k + 1:k + (3 if len(ns) > 4 else 2)] if thick else []
                ts = [c[16 * j:16 * (j + 1)].strip() for i, c in enumerate(cards) for j in range(5 if i == 0 else 4)]
                el[e] = (ns, ts[:4] + ts[5:] if len(cards) == 2 else ts[:4])
                k += 1 + len(cards)
        return xy, el

    for plane in ("XY", "YZ", "XZ"):
        d, rc, log = run(f"p2q{plane}", q_deck,
                         f"*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nMirror,{plane}\n**EndTransform\n*End\n")
        xy, el = q_read(out_text(d))
        mid_ok, pair_ok = True, True
        for e, ncorner in ((1, 4), (2, 3)):
            ns = el.get(e, ([], []))[0]
            if len(ns) < 2 * ncorner:
                mid_ok = False
                continue
            for k in range(ncorner):
                a, b, m = xy.get(ns[k]), xy.get(ns[(k + 1) % ncorner]), xy.get(ns[ncorner + k])
                if not (a and b and m) or abs((a[0] + b[0]) / 2 - m[0]) > 1e-6 or abs((a[1] + b[1]) / 2 - m[1]) > 1e-6:
                    mid_ok = False
        for e in (1, 2, 3, 4):   # 3 = TRI3(N4=0 으로 읽어 KMM 이 N3 을 되풀이해 쓴다)·4 = 퇴화 사각형(QUAD4 로 읽는다)
            ns, ts = el.get(e, ([], []))
            nn = ns[:3] if e == 3 else ns
            if not nn or len(ts) < len(nn) or any(abs(float(t or 0) - q_thk[n]) > 1e-9 for n, t in zip(nn, ts)):
                pair_ok = False
        t3 = el.get(3, ([], []))[1]
        check(f"P2Q MIRROR {plane}: rc 0", rc == 0 and no_tb(log), f"rc={rc} " + log[-300:])
        check(f"P2Q MIRROR {plane}: QUAD8·TRI6 중간 절점이 새 변의 가운데", mid_ok, str(el))
        check(f"P2Q MIRROR {plane}: 두께가 절점을 따라간다(THIC5~8 포함, TRI3 THIC4 = 새 N3 두께)",
              pair_ok and len(t3) == 4 and t3[3] == t3[2], str(el))

    # ── P3 *CONTROL_MPP_IO_NODUMP ────────────────────────────────────────────────────────────
    nd = ("*KEYWORD\n*CONTROL_TERMINATION\n" + f10(1.0) + "*CONTROL_MPP_IO_NODUMP\n\n" + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000.0, 0.3)
          + "*SECTION_SOLID\n" + f10(1, 1) + "*PART\nsolid normal\n" + f10(1, 1, 1) + NODES16.split("       9")[0]
          + "*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in (1, 2, 3, 4, 5, 6, 7, 8)) + "\n*END\n")
    d, rc, log = run("p3", nd)
    t = out_text(d)
    n = sum(1 for ln in t.splitlines() if ln.strip().upper() == "*CONTROL_MPP_IO_NODUMP")
    check("P3 NODUMP(뒤에 빈 줄): 출력에 한 번 나간다", rc == 0 and n == 1, f"rc={rc} n={n}")
    dec = ("*Inputfile\nmodel.k\n*Mode\nDECOMPOSE_K,1\n**DecomposeK,1\nGroup,g1,solid*\nOutputDir,dec_out\nModelIndependentSplit,True\n"
           "**End\n*End\n")
    d, rc, log = run("p3d", nd.replace("*CONTROL_MPP_IO_NODUMP\n\n", "*CONTROL_MPP_IO_NODUMP\n"), dec)
    allt = "\n".join(p.read_text(errors="replace") for p in sorted((d / "dec_out").rglob("*.k")))
    n = sum(1 for ln in allt.splitlines() if ln.strip().upper() == "*CONTROL_MPP_IO_NODUMP")
    check("P3 NODUMP DECOMPOSE_K: 분해 출력에 한 번 나간다", rc == 0 and n == 1, f"rc={rc} n={n}")

    # ── P4 *SECTION_SOLID ELFORM 101~105 사용자 카드 ──────────────────────────────────────────
    gp = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
    user = ([f10(8, 0, 1, 0, 2, 0, 0).rstrip("\n")] + ["".join(f"{s * 0.5773503:>10.7f}" for s in g) + f"{1.0:>10}" for g in gp]
            + [f10(210000.0, 0.3).rstrip("\n")])
    for title in (False, True):
        tag = "_TITLE" if title else ""
        sec1 = ("*SECTION_SOLID_TITLE\nuser101\n" if title else "*SECTION_SOLID\n") + f10(1, 101) + "\n".join(user) + "\n"
        sec8 = ("*SECTION_SOLID_TITLE\nstd\n" if title else "*SECTION_SOLID\n") + f10(8, 1)
        deck = ("*KEYWORD\n*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000.0, 0.3) + sec1 + sec8 + "*PART\nuser solid\n" + f10(1, 1, 1)
                + "*PART\nstd solid\n" + f10(2, 8, 1) + NODES16.split("      13")[0]
                + "*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in (1, 2, 3, 4, 5, 6, 7, 8)) + "\n"
                + f"{2:8d}{2:8d}" + "".join(f"{n:8d}" for n in (2, 9, 10, 3, 6, 11, 12, 7)) + "\n*END\n")
        d, rc, log = run(f"p4{tag}", deck)
        t = out_text(d)
        secs = {}
        for head, rows in blocks(t, "*SECTION_SOLID"):
            data = [r for r in rows if r.strip()]
            if head.split()[0].upper().endswith("_TITLE"):
                data = data[1:]
            if data:
                try:
                    secs[int(float(data[0][:10]))] = (int(float(data[0][10:20])), [r.rstrip() for r in data[1:]])
                except ValueError:
                    pass
        check(f"P4{tag} 사용자 솔리드: 단면은 1(ELFORM 101)·8(ELFORM 1) 둘뿐(유령 없음)", rc == 0 and sorted(secs) == [1, 8], f"rc={rc} {sorted(secs)}")
        check(f"P4{tag} 사용자 솔리드: SECID 1 의 사용자 카드 10줄(카드 3·적분점 8·속성 1)이 원문 그대로",
              secs.get(1, (0, []))[1] == [u.rstrip() for u in user], str(secs.get(1)))
        check(f"P4{tag} 사용자 솔리드: SECID 8 은 ELFORM 1 그대로", secs.get(8, (0,))[0] == 1, str(secs.get(8)))
        dump = out_text(d, "model_dump.k")
        check(f"P4{tag} 사용자 솔리드: 덤프에도 사용자 카드 10줄이 원문 그대로", all(u.rstrip() in dump for u in user) and dump.count(user[1].rstrip()) == 1,
              dump[-600:])

    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
