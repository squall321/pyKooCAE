# KMM 입출력 결함 묶음(v131 I1~I8·C1·B1)을 보는 회귀 시험 — I10 폭·콤마 자유형식·long·덱 전체 LONG·단면 정밀도·덤프 칸·ERODING 카드 4·접촉 선택 카드
"""
실행: venv312/bin/python tests/test_v131_io.py   (KMM 약 25회, 1~3분)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-11-04, 남은 기존 결함 묶음 — docs/kmm_remaining_defects_20261104/)
  I1 *KEYWORD I10=Y 덱의 DropSet.k 가 I10=Y 를 남기면서 *ELEMENT_BEAM·*ELEMENT_MASS 를 8칸으로 썼다(LS-DYNA 가 잘못 읽음).
     *ELEMENT_MASS_NODE_SET 은 읽을 때부터 I10 을 무시했다.
  I2·I3 콤마 자유형식 카드(R16: 카드마다 섞을 수 있다) — *DEFINE_CURVE·*MAT_RIGID 는 죽고, *MAT_ELASTIC·*SET_PART 는 조용히 0·빈 셋.
     *MAT_RIGID 빈 카드 2(R16 허용)는 덤프에서 죽었다.
  I4 콤마·long('+') *NODE 를 못 읽어 NID 0 유령 절점과 요소 소실(rc 3).
  I5 덱 전체 *KEYWORD LONG=Y·K(20칸 입력)를 잘못 읽었다 — 알아보게 멈춘다. LONG=S 는 R16 '표준 입력을 읽고 long 으로 쓴다' 라 그대로 읽는다.
     KMM 이 20칸으로 읽지 못하는 키워드의 '+' 블록도 멈춘다.
  I6 단면 실수를 10.3e(유효숫자 4자리)로 써 0.833333·0.012345·1.23457E-6 이 깎였다. *SECTION_BEAM NSM 은 10.1f 라 0.0012 가 0.0.
  I7 model_dump.k 가 *SECTION_SOLID COHOFF·GASKETT 를 4·5번째 칸에 써, 덤프를 다시 읽으면 값이 사라졌다.
  I8 *CONTACT_ERODING_* 의 필수 카드 4 가 빠진 덱이 IndexError 로 죽었다(원인 안내 없음).
  C1 AUTOMATIC_SINGLE_SURFACE·SURFACE_TO_SURFACE(_ID)·ERODING 접촉의 선택 카드 A~(SOFT·SBOPT·DEPTH…)가 출력에서 조용히 사라졌다.
     KMM 이 자기 산출 덱을 다시 읽는 누적 체인도 같다.
  B1 짧은 *ELEMENT_BEAM 카드(EID PID N1 N2)가 IndexError.
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
DROP = ("*Inputfile\nmodel.k\n*RunDirectoryMode,True,runs\n*Mode\nDROP_ATTITUDE,1\n**DropAttitude,1\nEulerRolling,0\nEulerPitching,0\n"
        "EulerYawing,0\nHeight,100\nInitialVelocityX,0\nInitialVelocityY,0\nInitialVelocityZ,0\nInitialAngularVelocityX,0\n"
        "InitialAngularVelocityY,0\nInitialAngularVelocityZ,0\nOffsetDistance,0.05\nDensity,7.85e-9\nYoungsModulus,2.0e5\n"
        "PoissonRatio,0.3\ntFinal,0.001\ndt,1e-6\n**EndDropAttitude\n*End\n")


def check(name, cond, detail=""):
    print("  %-80s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def run(name, files, opt=TRANS):
    d = Path(tempfile.mkdtemp(prefix=f"v131i_{name}_"))
    if isinstance(files, str):
        files = {"model.k": files}
    for fn, text in files.items():
        (d / fn).write_text(text)
    (d / "opt.txt").write_text(opt)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
    return d, r.returncode, r.stdout + r.stderr


def out(d, name="model_trans.k"):
    p = d / name
    return p.read_text(errors="replace") if p.exists() else ""


def no_tb(log):
    return "Traceback (most recent call last)" not in log


def blocks(text, kw, exact=True):
    """키워드 블록마다 (키워드 줄, 데이터 줄(주석 뺌)) — exact 면 이름이 같은 것만."""
    res, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("*"):
            h = ln.split()[0].upper()
            cur = [] if (h == kw if exact else h.startswith(kw)) else None
            if cur is not None:
                res.append((ln, cur))
            continue
        if cur is not None and not ln.startswith("$"):
            cur.append(ln)
    return res


def num(s):
    s = s.strip()
    return float(s) if s else 0.0


NODES8 = "*NODE\n" + "".join(f"{i:8d}{x:16.6f}{y:16.6f}{z:16.6f}{0:8d}{0:8d}\n" for i, (x, y, z) in enumerate(
    [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], 1))
HEX = "*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(1, 9)) + "\n"
BLOCK = "*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000.0, 0.3)


def deck(extra="", nodes=NODES8, head="*KEYWORD"):
    return head + "\n" + nodes + BLOCK + HEX + extra + "*END\n"


def main():
    # ── I1 I10 덱의 빔·질량 폭, 질량 절점셋 읽기 ───────────────────────────────────────────────
    i10n = "*NODE\n" + "".join(f"{1000 + i:10d}{x:16.6f}{y:16.6f}{z:16.6f}{0:10d}{0:10d}\n" for i, (x, y, z) in enumerate(
        [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1), (2, 0, 0), (3, 0, 0), (2, 1, 0)], 1))
    i10 = ("*KEYWORD I10=Y\n" + i10n + "*PART\nsolidpart\n" + f10(1, 1, 1) + "*PART\nbeampart\n" + f10(2, 2, 2) + "*SECTION_SOLID\n"
           + f10(1, 1) + "*SECTION_BEAM\n" + f10(2, 1, 1.0, 2, 0) + f10(0.1, 0.1, 0.1, 0.1) + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000.0, 0.3)
           + "*MAT_ELASTIC\n" + f10(2, "7.85E-09", 210000.0, 0.3) + "*ELEMENT_SOLID\n" + f10(5001, 1, *range(1001, 1009))
           + "*ELEMENT_BEAM\n" + f10(6001, 2, 1009, 1010, 1011, 0, 0, 0, 0, 0) + "*ELEMENT_MASS\n" + f"{7001:10d}{1001:10d}{0.5:16}{1:10d}\n"
           + "*SET_NODE_LIST\n" + f10(77) + f10(1005, 1006) + "*ELEMENT_MASS_NODE_SET\n" + f"{7002:10d}{77:10d}{0.25:16}{1:10d}\n" + "*END\n")

    def i10_rows(text, kw):
        """kw 블록 데이터 줄을 그 블록 폭으로 — 덱 머리가 I10=Y 면 10칸(블록 '-' 는 8칸), 블록 '%' 는 10칸."""
        glob = text.splitlines()[0].upper().replace(" ", "").find("I10=Y") >= 0 if text else False
        rows = []
        for head, data in blocks(text, kw):
            p = head.split()
            w = 10 if (p[1:2] == ["%"] or (glob and p[1:2] != ["-"])) else 8
            rows += [(w, r) for r in data if r.strip()]
        return rows
    d, rc, log = run("i1", i10, DROP)
    ds = [p for p in sorted(d.rglob("DropSet.k")) if p.parent.parent.name == "runs"]
    t = ds[0].read_text(errors="replace") if ds else ""
    beam = [(w, r) for w, r in i10_rows(t, "*ELEMENT_BEAM") if r[:w].strip() == "6001"]
    mass = [(w, r) for w, r in i10_rows(t, "*ELEMENT_MASS") if r[:w].strip() == "7001"]
    check("I1 I10=Y DROP: DropSet.k 의 *ELEMENT_BEAM 6001 을 그 폭으로 읽으면 N1·N2·N3 = 1009·1010·1011",
          rc == 0 and beam and [beam[0][1][k * beam[0][0]:(k + 1) * beam[0][0]].strip() for k in (2, 3, 4)] == ["1009", "1010", "1011"],
          f"rc={rc} {beam} " + log[-200:])
    check("I1 I10=Y DROP: *ELEMENT_MASS 7001 을 그 폭으로 읽으면 NID 1001·MASS 0.5·PID 1",
          bool(mass) and mass[0][1][mass[0][0]:2 * mass[0][0]].strip() == "1001"
          and num(mass[0][1][2 * mass[0][0]:2 * mass[0][0] + 16]) == 0.5
          and mass[0][1][2 * mass[0][0] + 16:3 * mass[0][0] + 16].strip() == "1", str(mass))
    d, rc, log = run("i1t", i10)
    t = out(d)
    ms = [(w, r) for w, r in i10_rows(t, "*ELEMENT_MASS_NODE_SET")]
    check("I1 I10=Y *ELEMENT_MASS_NODE_SET 7002·NSID 77·MASS 0.25·PID 1 을 그대로 읽고 쓴다",
          rc == 0 and len(ms) == 1 and ms[0][1][:ms[0][0]].strip() == "7002" and ms[0][1][ms[0][0]:2 * ms[0][0]].strip() == "77"
          and num(ms[0][1][2 * ms[0][0]:2 * ms[0][0] + 16]) == 0.25, f"rc={rc} {ms}")

    # ── I2·I3 콤마 자유형식 ──────────────────────────────────────────────────────────────────
    comma = ("*DEFINE_CURVE\n656,0,2.0,3.0\n0,-0.001\n1.0,0.5\n" + "*DEFINE_CURVE_TITLE\ncurve, with comma\n657,,1.5\n0.0,0.0\n2.0,4.0\n"
             + "*MAT_RIGID\n" + f10(2, "7.85E-09", 210000.0, 0.3) + "1,7,7\n\n" + "*PART\nrigid\n" + f10(2, 1, 2)
             + "*MAT_ELASTIC\n5,7.85e-9,2.1e5,0.3\n" + "*PART\nel5\n" + f10(3, 1, 5) + "*SET_PART_LIST\n9\n1,2,3\n")
    d, rc, log = run("i23", deck(comma))
    t = out(d)
    c656 = [r for h, r in blocks(t, "*DEFINE_CURVE")] + [r for h, r in blocks(t, "*DEFINE_CURVE_TITLE")]
    cur = {}
    for rows in c656:
        data = [r for r in rows if r.strip()]
        for k, r in enumerate(data):
            if r[:10].strip() in ("656", "657"):
                cur[int(r[:10])] = (num(r[20:30]), num(r[30:40]), [(num(x[:20]), num(x[20:40])) for x in data[k + 1:k + 3]])
                break
    check("I2 *DEFINE_CURVE 콤마: rc 0", rc == 0 and no_tb(log), f"rc={rc} " + log[-400:])
    check("I2 *DEFINE_CURVE 656 콤마 카드 1(SFA 2·SFO 3)·점 (0,-0.001)(1,0.5)",
          cur.get(656) == (2.0, 3.0, [(0.0, -0.001), (1.0, 0.5)]), str(cur.get(656)))
    check("I2 *DEFINE_CURVE_TITLE 657: 제목 안 쉼표 보존·SFA 1.5·점 (0,0)(2,4)",
          "curve, with comma" in t and cur.get(657) == (1.5, 0.0, [(0.0, 0.0), (2.0, 4.0)]), str(cur.get(657)))
    def data_of(head, rows):
        data = [r for r in rows if r.strip()]
        return data[1:] if head.split()[0].upper().endswith("_TITLE") else data
    rig = [data_of(h, rows) for h, rows in blocks(t, "*MAT_RIGID", exact=False)]
    rig2 = [d[1] for d in rig if len(d) > 1 and d[0][:10].strip() == "2"]
    check("I3 *MAT_RIGID 콤마 카드 2(CMO 1·CON1 7·CON2 7)", bool(rig2) and [num(rig2[0][k * 10:(k + 1) * 10]) for k in range(3)] == [1.0, 7.0, 7.0],
          str(rig[:3]))
    el5 = [rows for h, rows in blocks(t, "*MAT_ELASTIC", exact=False) if rows and rows[0][:10].strip() == "5"]
    el5 = el5 or [rows[1:] for h, rows in blocks(t, "*MAT_ELASTIC_TITLE") if len(rows) > 1 and rows[1][:10].strip() == "5"]
    check("I3 *MAT_ELASTIC 콤마 카드 1(MID 5·RO 7.85e-9·E 2.1e5·PR 0.3)",
          bool(el5) and [num(el5[0][0][k * 10:(k + 1) * 10]) for k in range(1, 4)] == [7.85e-9, 2.1e5, 0.3], str(el5[:1]))
    ps = [data_of(h, rows) for h, rows in blocks(t, "*SET_PART", exact=False)]
    mem = [x for rows in ps if rows and rows[0][:10].strip() == "9" for r in rows[1:] for x in r.split()]
    check("I3 *SET_PART_LIST 콤마: 셋 9 에 파트 1·2·3", any(rows and rows[0][:10].strip() == "9" for rows in ps) and {"1", "2", "3"} <= set(mem),
          str(ps))
    d, rc, log = run("i3f", deck("*MAT_RIGID\n" + f10(2, "7.85E-09", 210000.0, 0.3) + "\n\n" + "*PART\nrigid\n" + f10(2, 1, 2)))
    check("I3 *MAT_RIGID 빈 카드 2·3(R16 허용): 죽지 않는다", rc == 0 and no_tb(log), f"rc={rc} " + log[-300:])

    # ── I4 콤마·long *NODE ─────────────────────────────────────────────────────────────────
    pts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
    for tag, nodes in (("콤마", "*NODE\n" + "".join(f"{i},{x}.0,{y}.0,{z}.0\n" for i, (x, y, z) in enumerate(pts, 1))),
                       ("long", "*NODE +\n" + "".join(f"{i:20d}{float(x):20.1f}{float(y):20.1f}{float(z):20.1f}{0:20d}{0:20d}\n"
                                                      for i, (x, y, z) in enumerate(pts, 1))),
                       ("섞임", "*NODE\n" + f"{1:8d}{0.0:16.1f}{0.0:16.1f}{0.0:16.1f}\n" + "".join(f"{i},{x}.0,{y}.0,{z}.0\n" for i, (x, y, z) in enumerate(pts[1:], 2)))):
        d, rc, log = run(f"i4_{tag}", deck(nodes=nodes))
        t = out(d)
        got = {}
        for h, rows in blocks(t, "*NODE"):
            w = 10 if h.split()[1:2] == ["%"] else 8
            for r in rows:
                if r.strip():
                    got[int(r[:w])] = (num(r[w:w + 16]), num(r[w + 16:w + 32]), num(r[w + 32:w + 48]))
        check(f"I4 *NODE {tag}: rc 0·절점 1~8 좌표 그대로·NID 0 없음",
              rc == 0 and got == {i: tuple(float(v) for v in p) for i, p in enumerate(pts, 1)}, f"rc={rc} {sorted(got)[:3]} " + log[-200:])

    # ── I5 덱 전체 LONG ─────────────────────────────────────────────────────────────────────
    longdeck = ("*KEYWORD LONG=Y\n*NODE\n" + "".join(f"{i:20d}{float(x):20.1f}{float(y):20.1f}{float(z):20.1f}\n" for i, (x, y, z) in enumerate(pts, 1))
                + "*PART\n" + f"{'block':<40}\n" + "".join(f"{x:>20}" for x in (1, 1, 1)) + "\n*SECTION_SOLID\n" + "".join(f"{x:>20}" for x in (1, 1))
                + "\n*MAT_ELASTIC\n" + "".join(f"{x:>20}" for x in (1, "7.85E-09", 210000.0, 0.3)) + "\n*ELEMENT_SOLID\n"
                + "".join(f"{x:>20}" for x in (1, 1)) + "\n" + "".join(f"{x:>20}" for x in range(1, 9)) + "\n*END\n")
    for opt in ("Y", "K"):
        d, rc, log = run(f"i5{opt}", longdeck.replace("LONG=Y", f"LONG={opt}"))
        check(f"I5 *KEYWORD LONG={opt}: 지원하지 않는다고 알리고 멈춘다(rc 1, 출력 없음)",
              rc == 1 and f"LONG={opt}" in log and "지원하지 않는다" in log and not (d / "model_trans.k").exists(), f"rc={rc} " + log[-300:])
    d, rc, log = run("i5S", deck(head="*KEYWORD I10=Y LONG=S", nodes=NODES8.replace("*NODE\n", "*NODE -\n")).replace("*ELEMENT_SOLID\n", "*ELEMENT_SOLID -\n"))
    check("I5 *KEYWORD I10=Y LONG=S(R16: 표준 입력을 읽는다): 그대로 읽는다(rc 0)", rc == 0 and "지원하지 않는다" not in log, f"rc={rc} " + log[-300:])
    d, rc, log = run("i5plus", deck(extra="*MAT_ELASTIC +\n" + "".join(f"{x:>20}" for x in (5, "7.85E-09", 210000.0, 0.3)) + "\n"))
    check("I5 KMM 이 20칸으로 못 읽는 키워드의 '+' 블록(*MAT_ELASTIC +): 알리고 멈춘다(rc 1)",
          rc == 1 and "MAT_ELASTIC" in log and "지원하지 않는다" in log, f"rc={rc} " + log[-300:])
    inc = {"model.k": "*KEYWORD\n*INCLUDE +\nnodes_long.k\n" + BLOCK + HEX + "*END\n",
           "nodes_long.k": "*KEYWORD\n*NODE\n" + "".join(f"{i:20d}{float(x):20.1f}{float(y):20.1f}{float(z):20.1f}{0:20d}{0:20d}\n"
                                                         for i, (x, y, z) in enumerate(pts, 1)) + "*END\n"}
    d, rc, log = run("i5inc", inc)
    t = out(d)
    n = sum(1 for h, rows in blocks(t, "*NODE") for r in rows if r.strip())
    check("I5 *INCLUDE + (인클루드 전체 long, *NODE 만): long *NODE 로 읽는다(rc 0·절점 8)", rc == 0 and n == 8, f"rc={rc} n={n} " + log[-300:])

    # ── I6 단면 실수 정밀도 ─────────────────────────────────────────────────────────────────
    sh = ("*PART\nskin\n" + f10(2, 2, 1) + "*SECTION_SHELL\n" + f10(2, 16, 0.833333, 5, 1.0, 0.0, 0, 1)
          + "  0.012345 0.0123456   1.23457  0.012345       0.51.23457E-6       0.0          \n"
          + "*ELEMENT_SHELL\n" + f"{10:8d}{2:8d}{1:8d}{2:8d}{3:8d}{4:8d}\n"
          + "*PART\nbeam\n" + f10(3, 3, 1) + "*SECTION_BEAM\n" + f10(3, 1, 0.833333, 2, 0, 0.0, 0.0012, 0) + f10(0.12345, 0.12345, 0.1, 0.1, 0.0, 0.0)
          + "*ELEMENT_BEAM\n" + f"{20:8d}{3:8d}{5:8d}{6:8d}{0:8d}{0:8d}{0:8d}{0:8d}{0:8d}{0:8d}\n"
          + "*PART\nexact\n" + f10(4, 4, 1) + "*SECTION_SHELL\n" + f10(4, 2, 0.8333, 2) + f10(1.0, 1.0, 1.0, 1.0))
    d, rc, log = run("i6", deck(sh))
    t = out(d)

    def sec(kw, sid):
        for h, rows in blocks(t, kw, exact=False):
            data = [r for r in rows if r.strip()]
            if h.split()[0].upper().endswith("_TITLE"):
                data = data[1:]
            if data and data[0][:10].strip() == str(sid):
                return [[num(r[k * 10:(k + 1) * 10]) for k in range(8)] for r in data[:2]]
        return None
    s2, b3, s4 = sec("*SECTION_SHELL", 2), sec("*SECTION_BEAM", 3), sec("*SECTION_SHELL", 4)
    check("I6 *SECTION_SHELL 2: SHRF 0.833333·T1~T4 0.012345/0.0123456/1.23457/0.012345·MAREA 1.23457E-6 그대로",
          s2 is not None and s2[0][2] == 0.833333 and s2[1][:4] == [0.012345, 0.0123456, 1.23457, 0.012345] and s2[1][5] == 1.23457e-6, str(s2))
    check("I6 *SECTION_BEAM 3: SHRF 0.833333·NSM 0.0012·TS1·TS2 0.12345 그대로",
          b3 is not None and b3[0][2] == 0.833333 and b3[0][6] == 0.0012 and b3[1][:2] == [0.12345, 0.12345], str(b3))
    exact = [ln for h, rows in blocks(t, "*SECTION_SHELL", exact=False) for ln in rows if ln[:10].strip() == "4"]
    check("I6 *SECTION_SHELL 4(10.3e 로 정확한 값 0.8333): 예전 출력 그대로(8.333e-01)", bool(exact) and "8.333e-01" in exact[0], str(exact))

    # ── I7 덤프 COHOFF·GASKETT 칸 ───────────────────────────────────────────────────────────
    coh = deck().replace("*SECTION_SOLID\n" + f10(1, 1), "*SECTION_SOLID\n" + f10(1, 1, 0, "", "", "", 0.5, 2.0))
    d, rc, log = run("i7", coh)
    dump = out(d, "model_dump.k")
    row = [r for h, rows in blocks(dump, "*SECTION_SOLID", exact=False) for r in rows if r[:10].strip() == "1"]
    check("I7 model_dump.k *SECTION_SOLID: COHOFF 0.5·GASKETT 2.0 이 R16 7·8번째 칸",
          bool(row) and num(row[0][60:70]) == 0.5 and num(row[0][70:80]) == 2.0 and not row[0][30:50].strip(), str(row))
    if dump:
        d2, rc2, log2 = run("i7b", dump)
        row2 = [r for h, rows in blocks(out(d2), "*SECTION_SOLID", exact=False) for r in rows if r[:10].strip() == "1"]
        check("I7 덤프를 다시 읽어도 COHOFF·GASKETT 가 남는다", rc2 == 0 and bool(row2) and num(row2[0][60:70]) == 0.5 and num(row2[0][70:80]) == 2.0,
              str(row2))

    # ── I8 ERODING 필수 카드 4 ──────────────────────────────────────────────────────────────
    ero = ("*SET_PART_LIST\n" + f10(1) + f10(1) + "*CONTACT_ERODING_SURFACE_TO_SURFACE_ID\n" + f10(8) + f10(1, 1, 2, 2, 0, 0, 0, 0)
           + f10(0.2, 0.2, 0, 0, 0, 0, 0, "1e+20") + f10(1.0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0))
    d, rc, log = run("i8", deck(ero))
    check("I8 *CONTACT_ERODING_SURFACE_TO_SURFACE_ID 카드 4 없음: 원인(필수 카드 4)을 밝혀 멈춘다(rc 1)", rc == 1 and "카드 4" in log, f"rc={rc} " + log[-300:])

    # ── C1 접촉 선택 카드 ─────────────────────────────────────────────────────────────────
    A = f10(2, 0.1, 0, 1.025, 2.0, 3, 0, 1).rstrip("\n")
    B = f10(0.0, 1, 0.0, 0, 0, 0, 0.0, 0.0).rstrip("\n")
    con = ("*SET_PART_LIST\n" + f10(1) + f10(1) + "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID\n" + f10(8, "auto_contact") + f10(1, 1, 2, 2, 0, 0, 0, 0)
           + f10(0.2, 0.2, 0, 0, 0, 0, 0, "1e+20") + f10(1.0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0) + A + "\n" + B + "\n"
           + "*CONTACT_AUTOMATIC_SINGLE_SURFACE\n" + f10(1, 0, 2, 0, 0, 0, 0, 0) + f10(0.1, 0.1, 0, 0, 0, 0, 0, "1e+20")
           + f10(1.0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0) + A + "\n"
           + "*CONTACT_ERODING_SURFACE_TO_SURFACE_ID\n" + f10(9) + f10(1, 1, 2, 2, 0, 0, 0, 0) + f10(0.2, 0.2, 0, 0, 0, 0, 0, "1e+20")
           + f10(1.0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0) + f10(1, 1, 1) + A + "\n")
    d, rc, log = run("c1", deck(con))
    t = out(d)

    def cards(kw, nth=0):
        bl = blocks(t, kw)
        if len(bl) <= nth:
            return []
        return [r.rstrip() for r in bl[nth][1] if r.strip()]
    s2s, er = cards("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID"), cards("*CONTACT_ERODING_SURFACE_TO_SURFACE_ID")
    ss = cards("*CONTACT_AUTOMATIC_SINGLE_SURFACE") or cards("*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID")[1:]   # KMM 은 _ID 로 고쳐 쓴다

    def same(row, want):
        return row is not None and [num(row[k * 10:(k + 1) * 10]) for k in range(8)] == [num(want[k * 10:(k + 1) * 10]) for k in range(8)]
    check("C1 rc 0", rc == 0 and no_tb(log), f"rc={rc} " + log[-300:])
    check("C1 AUTOMATIC_SURFACE_TO_SURFACE_ID: 선택 카드 A(SOFT 2·SOFSCL 0.1·MAXPAR 1.025·SBOPT 2·DEPTH 3·FRCFRQ 1)·B 가 남는다",
          len(s2s) >= 6 and same(s2s[4], A) and same(s2s[5], B), str(s2s))
    check("C1 AUTOMATIC_SINGLE_SURFACE: 선택 카드 A 가 남는다", len(ss) >= 4 and same(ss[3], A), str(ss))
    check("C1 ERODING_SURFACE_TO_SURFACE_ID: 카드 4 뒤 선택 카드 A 가 남는다", len(er) >= 6 and same(er[5], A), str(er))
    if t:
        d2, rc2, log2 = run("c1rt", t)
        t, s2s2 = out(d2), None
        s2s2 = cards("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID")
        check("C1 출력을 다시 읽어도 선택 카드 A·B 가 남는다(누적 체인)", rc2 == 0 and len(s2s2) >= 6 and same(s2s2[4], A) and same(s2s2[5], B), str(s2s2))

    # ── B1 짧은 *ELEMENT_BEAM 카드 ─────────────────────────────────────────────────────────
    short = ("*PART\nbeam\n" + f10(2, 2, 1) + "*SECTION_BEAM\n" + f10(2, 1, 0.8333, 2, 0) + f10(0.1, 0.1, 0.1, 0.1)
             + "*NODE\n" + f"{9:8d}{2.0:16.1f}{0.0:16.1f}{0.0:16.1f}\n" + f"{10:8d}{3.0:16.1f}{0.0:16.1f}{0.0:16.1f}\n"
             + "*ELEMENT_BEAM\n" + f"{20:8d}{2:8d}{9:8d}{10:8d}\n")
    d, rc, log = run("b1", deck(short))
    beams = [r for h, rows in blocks(out(d), "*ELEMENT_BEAM") for r in rows if r.strip()]
    check("B1 짧은 *ELEMENT_BEAM(EID PID N1 N2): 죽지 않고 빔 20 이 남는다", rc == 0 and any(r[:8].strip() == "20" for r in beams),
          f"rc={rc} {beams} " + log[-300:])

    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
