# KMM 모드 결함 묶음(v131 M1~M8·X1·X2)을 보는 회귀 시험 — DECOMPOSE_K·IMPORT_MERGE_K·Fast DOE·DTI·DWI OutsideRigid·MIRROR·TShellMode·PART_EXCHANGE
"""
실행: venv312/bin/python tests/test_v131_modes.py   (KMM 약 25회, 2~4분)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-11-04, 남은 기존 결함 묶음 — docs/kmm_remaining_defects_20261104/)
  M1 DECOMPOSE_K 가 원문 요소만 쓰는 절점·PID 없는 *ELEMENT_MASS·셋·데이터 없는 키워드를 버렸다. *ELEMENT_MASS_NODE_SET 이 든 파트는 TypeError.
  M2 IMPORT_MERGE_K — 가져온 PART 의 SECID 가 밀리지 않아 기준 덱 단면을 가리켰다. psid 오프셋이 늘 0. *SET_NODE_LIST·*SET_PART_LIST 크래시.
     가져온 덱의 원문 블록·해석된 초기·하중 조건이 경고 없이 사라졌다.
  M3 Fast 기록기(여러 각도 DROP·TRANSLATION_DOE·PART_LOCATION_DOE·DWI Part)가 원문 블록을 쓰지 않았고, 여러 각도 DROP 은
     바닥판 접촉이 가리키는 *SET_PART 를 빠뜨렸다. *KEYWORD 줄 옵션도 버렸다.
  M4 DTI 가 dynain 의 *INITIAL_STRESS_SHELL·TSHELL 을 버렸다.
  M5 DWI OutsideRigid*·Part 가 *RunDirectoryMode 를 무시해 Run_* 밖에 썼다(워크플로가 덱을 못 찾음). 원문 재질 파트에서 AttributeError.
  M6 MIRROR 가 TSHELL 연결을 뒤집지 않아 요소가 뒤집혔다(자코비안 음수).
  M7 같은 실행에서 ConvertHexato,TShell 로 만든 파트를 TSHELL 판정(발열원 거부·수동 강체화)에서 놓쳤다.
  M8 PART_EXCHANGE 가 요소 종류와 맞지 않는 단면(HEXA8 ← *SECTION_TSHELL 등)을 경고 없이 붙였다.
  X1 원문으로 나가는 *MAT_SPRING_ELASTIC·*MAT_SEATBELT 를 '재질 MID 소실' 🔴 로 잘못 알렸다.
  X2 서로 다른 모드가 같은 모드 ID 를 쓰면 옵션이 덮여 엉뚱한 곳에서 죽었다.
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
RAW_KWS = ("*PART_COMPOSITE_TSHELL", "*SECTION_DISCRETE", "*MAT_SPRING_ELASTIC", "*ELEMENT_DISCRETE", "*ELEMENT_SEATBELT",
           "*CONTROL_MPP_IO_NOD3DUMP")


def check(name, cond, detail=""):
    print("  %-80s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def node_lines(pts):
    return "".join(f"{i:8d}{x:16.6f}{y:16.6f}{z:16.6f}\n" for i, (x, y, z) in sorted(pts.items()))


# ── 덱(mm-ton-s): 파트 1 HEXA8 2개 · 파트 2 TSHELL8 2개 · 파트 5 *PART_COMPOSITE_TSHELL(원문 TSHELL 1개) · 파트 6 스프링(원문)
#    · PID 없는 *ELEMENT_MASS(절점 43) · 파트 7 시트벨트(원문) · *CONTROL_MPP_IO_NOD3DUMP(데이터 없는 키워드)
def points():
    pts, nid = {}, 0
    for z in (0.0, 1.0):
        for y in (0.0, 1.0):
            for x in (0.0, 1.0, 2.0):
                nid += 1
                pts[nid] = (x, y, z)
    k = 13
    for z in (1.0, 1.5):
        for y in (0.0, 1.0):
            for x in (0.0, 1.0, 2.0):
                pts[k] = (x, y, z)
                k += 1
    k = 29
    for z in (0.0, 0.5):
        for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1)):
            pts[k] = (x + 10.0, y, z)
            k += 1
    for n, x in ((41, 20.0), (42, 21.0), (43, 22.0), (44, 23.0), (45, 24.0)):
        pts[n] = (x, 0.0, 0.0)
    return pts


SOLID = {1: (1, 2, 5, 4, 7, 8, 11, 10), 2: (2, 3, 6, 5, 8, 9, 12, 11)}
TSH = {3: (13, 14, 17, 16, 19, 20, 23, 22), 4: (14, 15, 18, 17, 20, 21, 24, 23)}
TSH_COMP = {8: (29, 30, 31, 32, 33, 34, 35, 36)}


def base_deck(raw=True, extra="", keyword="*KEYWORD"):
    rows = "".join(f"{e:8d}{2:8d}" + "".join(f"{n:8d}" for n in c) + "\n" for e, c in TSH.items())
    if raw:
        rows += "".join(f"{e:8d}{5:8d}" + "".join(f"{n:8d}" for n in c) + "\n" for e, c in TSH_COMP.items())
    out = [keyword + "\n", "*CONTROL_TERMINATION\n", f10(0.001), "*NODE\n", node_lines(points() if raw else
                                                                                    {k: v for k, v in points().items() if k <= 24}),
           "*ELEMENT_SOLID\n" + "".join(f"{e:8d}{1:8d}" + "".join(f"{n:8d}" for n in c) + "\n" for e, c in SOLID.items()),
           "*ELEMENT_TSHELL\n" + rows,
           "*PART\nhousing\n" + f10(1, 1, 1) + "*PART\nfpcb\n" + f10(2, 2, 1),
           "*SECTION_SOLID\n" + f10(1, 1) + "*SECTION_TSHELL\n" + f10(2, 1, 0.8333, 3, 1, 0.0, 0, 0),
           "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)]
    if raw:
        out += ["*PART_COMPOSITE_TSHELL\nlaminate\n" + f10(5, 1, 0.8333, 0, 0, 0, 0, 0) + f10(1, 0.25, 0.0, "", 1, 0.25, 90.0, ""),
                "*PART\nspring\n" + f10(6, 6, 6), "*SECTION_DISCRETE\n" + f10(6, 0, 0.0, 0.0, 0.0, 0.0) + f10(0.0, 0.0),
                "*MAT_SPRING_ELASTIC\n" + f10(6, 1000.0),
                "*ELEMENT_DISCRETE\n" + f"{50:8d}{6:8d}{41:8d}{42:8d}{0:8d}{1.0:16.4f}{0:8d}{0.0:16.4f}\n",
                "*ELEMENT_MASS\n" + f"{60:8d}{43:8d}{0.001:16.6f}{'':8}\n",
                "*PART\nbelt\n" + f10(7, 7, 7), "*SECTION_SEATBELT\n" + f10(7, 1.0), "*MAT_SEATBELT\n" + f10(7, 1.0e-9, 0, 0, 0.0, 0.0, 0.0),
                "*ELEMENT_SEATBELT\n" + f"{70:8d}{7:8d}{44:8d}{45:8d}{0:8d}{0.0:16.4f}{0:8d}\n",
                "*CONTROL_MPP_IO_NOD3DUMP\n"]
    out += [extra, "*END\n"]
    return "".join(out)


def run(name, deck_files, opt):
    d = Path(tempfile.mkdtemp(prefix=f"v131m_{name}_", dir=os.environ.get("V131_TMP") or None))
    for fn, text in deck_files.items():
        (d / fn).write_text(text)
    (d / "opt.txt").write_text(opt.replace("@D@", str(d)))
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=1200, env=ENV)
    return d, r.returncode, r.stdout + r.stderr


def no_tb(log):
    return "Traceback (most recent call last)" not in log


def kw_lines(text):
    return [ln.split()[0].upper() for ln in text.splitlines() if ln.startswith("*")]


def k_nodes(text):
    ids, on = set(), False
    for ln in text.splitlines():
        if ln.startswith("*"):
            on = ln.split()[0].upper() == "*NODE"
            continue
        if on and ln.strip() and not ln.startswith("$"):
            try:
                ids.add(int(ln[:8]))
            except ValueError:
                pass
    return ids


def blocks(text, kw):
    """kw 로 시작하는 키워드 블록마다 데이터 줄(주석 뺌) 목록."""
    out, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("*"):
            cur = [] if ln.split()[0].upper().startswith(kw) else None
            if cur is not None:
                out.append(cur)
            continue
        if cur is not None and not ln.startswith("$"):
            cur.append(ln)
    return out


def parts_of(text):
    """*PART(_TITLE 포함) → {PID: SECID}."""
    out, lines = {}, text.splitlines()
    for i, ln in enumerate(lines):
        if ln.split()[:1] and ln.split()[0].upper() in ("*PART", "*PART_TITLE"):
            data = [x for x in lines[i + 1:i + 6] if not x.startswith("$")]
            if len(data) >= 2:
                try:
                    out[int(data[1][:10])] = int(float(data[1][10:20]))
                except ValueError:
                    pass
    return out


def sections_of(text):
    """*SECTION_SOLID(_TITLE) → {SECID: ELFORM}."""
    out = {}
    for u in ("*SECTION_SOLID",):
        lines = text.splitlines()
        for i, ln in enumerate(lines):
            h = ln.split()[0].upper() if ln.startswith("*") else ""
            if h in ("*SECTION_SOLID", "*SECTION_SOLID_TITLE"):
                data = [x for x in lines[i + 1:i + 5] if not x.startswith("$") and not x.startswith("*")]
                if h.endswith("_TITLE"):
                    data = data[1:]
                if data:
                    out[int(float(data[0][:10]))] = int(float(data[0][10:20]))
    return out


def jac(X):
    d = lambda a, b: [sum(X[i][k] for i in a) / 4 - sum(X[i][k] for i in b) / 4 for k in range(3)]
    a = d((1, 2, 5, 6), (0, 3, 4, 7))
    b = d((2, 3, 6, 7), (0, 1, 4, 5))
    c = d((4, 5, 6, 7), (0, 1, 2, 3))
    return a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0])


def hex_signs(text):
    """*ELEMENT_SOLID·*ELEMENT_TSHELL(8칸·'%' 10칸) 8절점 요소 → {EID: 중심 자코비안}."""
    nodes, elems, kw, w = {}, [], None, 8
    for ln in text.splitlines():
        if ln.startswith("*"):
            p = ln.split()
            kw, w = p[0].upper(), (10 if len(p) > 1 and p[1] == "%" else 8)
            continue
        if ln.startswith("$") or not ln.strip():
            continue
        if kw == "*NODE":
            nodes[int(ln[:w])] = (float(ln[w:w + 16]), float(ln[w + 16:w + 32]), float(ln[w + 32:w + 48]))
        elif kw in ("*ELEMENT_SOLID", "*ELEMENT_TSHELL"):
            f = [int(ln[i * w:(i + 1) * w]) for i in range(10)]
            elems.append((f[0], f[2:]))
    return {e: jac([nodes[n] for n in ns]) for e, ns in elems if all(n in nodes for n in ns)}


def main():
    # ── M1 DECOMPOSE_K ────────────────────────────────────────────────────────────────────────
    dec = ("*Inputfile\nmodel.k\n*Mode\nDECOMPOSE_K,1\n**DecomposeK,1\nGroup,housing,housing\nGroup,fpcb,fpcb\n"
           "OutputDir,decomposed_output\nSharedNodesPolicy,duplicate\nModelIndependentSplit,True\n**End\n*End\n")
    d, rc, log = run("m1", {"model.k": base_deck(extra="*SET_SOLID\n" + f10(11) + f10(1, 2))}, dec)
    texts = [p.read_text(errors="replace") for p in sorted((d / "decomposed_output").rglob("*.k"))]
    allt = "\n".join(texts)
    got = set().union(*[k_nodes(t) for t in texts]) if texts else set()
    miss = sorted(set(points()) - got)
    check("M1 DECOMPOSE_K: rc 0", rc == 0 and no_tb(log), f"rc={rc} " + log[-500:])
    check("M1 DECOMPOSE_K: 입력 절점 45개가 모두 어딘가 *NODE 로 나간다(원문 요소·질량·벨트 절점 포함)", not miss, f"없음 {miss}")
    check("M1 DECOMPOSE_K: PID 없는 *ELEMENT_MASS 60·*SET_SOLID 11·*CONTROL_MPP_IO_NOD3DUMP 가 남는다",
          any(r[:8].strip() == "60" for b in blocks(allt, "*ELEMENT_MASS") for r in b) and "*CONTROL_MPP_IO_NOD3DUMP" in kw_lines(allt)
          and any(r[:10].strip() == "11" for b in blocks(allt, "*SET_SOLID") for r in b[:2]), str(sorted(set(kw_lines(allt)))))
    massn = "*SET_NODE_LIST\n" + f10(21) + f10(1, 2) + "*ELEMENT_MASS_NODE_SET\n" + f"{61:8d}{21:8d}{0.002:16.6f}{1:8d}\n"
    d, rc, log = run("m1c", {"model.k": base_deck(raw=False, extra=massn)}, dec)
    check("M1c DECOMPOSE_K: 파트에 *ELEMENT_MASS_NODE_SET 이 있어도 죽지 않는다", rc == 0 and no_tb(log), f"rc={rc} " + log[-400:])

    # ── M2 IMPORT_MERGE_K ─────────────────────────────────────────────────────────────────────
    def hexn(x0):
        pts, nid = {}, 1
        for z in (0.0, 1.0):
            for y in (0.0, 1.0):
                for x in (0.0, 1.0):
                    pts[nid] = (x + x0, y, z)
                    nid += 1
        return pts
    hexrow = f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in (1, 2, 4, 3, 5, 6, 8, 7)) + "\n"
    base_k = ("*KEYWORD\n*NODE\n" + node_lines(hexn(0.0)) + "*ELEMENT_SOLID\n" + hexrow + "*PART\nbase_part\n" + f10(1, 1, 1)
              + "*SECTION_SOLID\n" + f10(1, 1) + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
              + "*SET_PART_LIST\n" + f10(1) + f10(1) + "*END\n")

    def imp_k(extra=""):
        pts = hexn(5.0)
        pts[20], pts[21] = (10.0, 0.0, 0.0), (11.0, 0.0, 0.0)
        return ("*KEYWORD\n*NODE\n" + node_lines(pts) + "*ELEMENT_SOLID\n" + hexrow + "*PART\nimported_part\n" + f10(1, 1, 2)
                + "*SECTION_SOLID\n" + f10(1, 2) + "*MAT_ELASTIC\n" + f10(2, "2.70E-09", 70000, 0.33) + extra + "*END\n")
    imo = "*Inputfile\nbase.k\n*Mode\nIMPORT_MERGE_K,1\n**ImportMergeK,1\nImportFile,imp.k\n**End\n*End\n"
    d, rc, log = run("m2a", {"base.k": base_k, "imp.k": imp_k()}, imo)
    t = (d / "base_imported.k").read_text(errors="replace") if (d / "base_imported.k").exists() else ""
    parts, secs = parts_of(t), sections_of(t)
    newp = [p for p in parts if p != 1]
    check("M2a IMPORT_MERGE_K: rc 0", rc == 0 and no_tb(log), f"rc={rc} " + log[-400:])
    check("M2a 가져온 파트의 SECID 가 가져온 단면(ELFORM 2)을 가리킨다(기준 덱 단면 1 이 아니다)",
          len(newp) == 1 and secs.get(parts[newp[0]]) == 2 and parts[newp[0]] != 1, f"parts={parts} secs={secs}")
    d, rc, log = run("m2c1", {"base.k": base_k, "imp.k": imp_k("*SET_NODE_LIST\n" + f10(1) + f10(1, 2, 3))}, imo)
    t = (d / "base_imported.k").read_text(errors="replace") if (d / "base_imported.k").exists() else ""
    nsets = [[x for ln in b[1:] for x in ln.split()] for b in blocks(t, "*SET_NODE")]
    check("M2c1 가져올 덱의 *SET_NODE_LIST: 죽지 않고 밀린 절점 9·10·11 을 가리킨다",
          rc == 0 and no_tb(log) and ["9", "10", "11"] in nsets, f"rc={rc} sets={nsets} " + log[-300:])
    d, rc, log = run("m2c2", {"base.k": base_k, "imp.k": imp_k("*SET_PART_LIST\n" + f10(1) + f10(1))}, imo)
    t = (d / "base_imported.k").read_text(errors="replace") if (d / "base_imported.k").exists() else ""
    psets = {}
    for b in blocks(t, "*SET_PART"):
        data = [ln for ln in b if ln.strip()]
        for k in (0, 1):   # *SET_PART_LIST_TITLE 이면 첫 줄이 제목이다
            try:
                psets[int(data[k][:10])] = [x for ln in data[k + 1:] for x in ln.split()]
                break
            except (ValueError, IndexError):
                continue
    check("M2c2 가져올 덱의 *SET_PART_LIST: 죽지 않고 새 셋 번호(≠1)로 밀린 PID 2 를 담는다",
          rc == 0 and no_tb(log) and psets.get(1) == ["1"] and any(k != 1 and v == ["2"] for k, v in psets.items()),
          f"rc={rc} psets={psets} " + log[-300:])
    raw = ("*PART\nspring\n" + f10(6, 6, 6) + "*SECTION_DISCRETE\n" + f10(6, 0, 0.0, 0.0, 0.0, 0.0) + f10(0.0, 0.0)
           + "*MAT_SPRING_ELASTIC\n" + f10(6, 1000.0) + "*ELEMENT_DISCRETE\n" + f"{50:8d}{6:8d}{20:8d}{21:8d}{0:8d}{1.0:16.4f}{0:8d}{0.0:16.4f}\n")
    d, rc, log = run("m2d", {"base.k": base_k, "imp.k": imp_k(raw)}, imo)
    check("M2d 가져올 덱의 원문 블록(SECTION_DISCRETE·MAT_SPRING_ELASTIC·ELEMENT_DISCRETE)을 옮기지 못하면 🔴 + rc 3",
          rc == 3 and "🔴" in log and all(k in log for k in ("SECTION_DISCRETE", "MAT_SPRING_ELASTIC", "ELEMENT_DISCRETE")),
          f"rc={rc} " + log[-500:])
    # M2e 병합이 기준 덱 정의·설정을 덮지 않는다 — 예전엔 같은 번호의 곡선·경계·HOURGLASS 를 가져온 것으로 덮고, 가져온 CONTROL 이
    # 기준 덱 설정을 바꾸고, 구속·감쇠·강체벽은 밀리지 않은 PID·NSID 로 기준 덱 파트·셋을 가리켰다
    curve = lambda v: "*DEFINE_CURVE\n" + f10(1) + f"{0.0:20.4f}{v:20.4f}\n" + f"{1.0:20.4f}{v:20.4f}\n"
    base_e = (base_k.replace("*NODE\n", "*CONTROL_TERMINATION\n" + f10(0.005) + "*NODE\n").replace("*END\n", "")
              + "*SET_NODE_LIST\n" + f10(1) + f10(1, 2) + curve(1.0) + "*BOUNDARY_SPC_NODE\n" + f10(1, 0, 1, 1, 1, 0, 0, 0)
              + "*BOUNDARY_PRESCRIBED_MOTION_RIGID\n" + f10(1, 3, 2, 1, 1.0) + "*HOURGLASS\n" + f10(1, 4, 0.05) + "*END\n")

    def imp_e(cv, hgq):
        return imp_k("*CONTROL_TERMINATION\n" + f10(0.123) + "*SET_NODE_LIST\n" + f10(1) + f10(3, 4) + curve(cv)
                     + "*BOUNDARY_SPC_NODE\n" + f10(5, 0, 1, 1, 1, 0, 0, 0) + "*BOUNDARY_PRESCRIBED_MOTION_RIGID\n" + f10(1, 3, 2, 1, 1.0)
                     + "*HOURGLASS\n" + f10(1, 4, hgq) + "*CONSTRAINED_EXTRA_NODES_SET\n" + f10(1, 1) + "*DAMPING_PART_STIFFNESS\n"
                     + f10(1, 0.05) + "*RIGIDWALL_PLANAR\n" + f10(1, 0, 0, 0) + f10(0.0, 0.0, -1.0, 0.0, 0.0, 1.0, 0.0))
    for tag, cv, hgq in (("같은 곡선·HOURGLASS", 1.0, 0.05), ("다른 곡선·HOURGLASS", 2.0, 0.07)):
        d, rc, log = run("m2e", {"base.k": base_e, "imp.k": imp_e(cv, hgq)}, imo)
        t = (d / "base_imported.k").read_text(errors="replace") if (d / "base_imported.k").exists() else ""
        rows = lambda kw: [r for b in blocks(t, kw) for r in b if r.strip()]
        term = [r for r in rows("*CONTROL_TERMINATION")][:1]
        crv = [r for r in rows("*DEFINE_CURVE")]
        spc = sorted(int(r[:10]) for r in rows("*BOUNDARY_SPC_NODE"))
        pmr = sorted(int(b[1][:10]) for b in blocks(t, "*BOUNDARY_PRESCRIBED_MOTION_RIGID") if len(b) > 1)
        hg = rows("*HOURGLASS")
        k = set(kw_lines(t))
        check(f"M2e {tag}: 기준 덱 CONTROL_TERMINATION(0.005)·곡선 1(1.0)·HOURGLASS 1(0.05)이 그대로",
              term and "5.000e-03" in term[0] and len(crv) == 3 and "2.0000" not in "".join(crv) and len(hg) == 1 and "0.050" in hg[0],
              f"term={term} crv={crv} hg={hg}")
        check(f"M2e {tag}: 경계는 기준 덱 것(절점 1·PID 1)과 가져온 것(밀린 절점 13·PID 2)이 모두 있다",
              spc == [1, 13] and pmr == [1, 2], f"spc={spc} pmr={pmr}")
        check(f"M2e {tag}: 구속·부분 감쇠·강체벽은 옮기지 않고 🔴 + rc 3",
              rc == 3 and not k & {"*CONSTRAINED_EXTRA_NODES_SET", "*DAMPING_PART_STIFFNESS"} and not any(x.startswith("*RIGIDWALL") for x in k)
              and all(x in log for x in ("CONSTRAINED_EXTRA_NODES_SET", "DAMPING_PART_STIFFNESS", "RIGIDWALL_PLANAR")), f"rc={rc} {sorted(k)}")
        conflict = "같은 번호인데 내용이 다른 정의" in log
        check(f"M2e {tag}: 번호 충돌 알림은 내용이 다를 때만(곡선 LCID 1·HOURGLASS HGID 1)",
              conflict == (cv != 1.0) and (not conflict or ("곡선 LCID 1" in log and "HOURGLASS HGID 1" in log)), log[-400:])

    # ── M3 Fast 기록기 ────────────────────────────────────────────────────────────────────────
    def raw_ok(text):
        k = set(kw_lines(text))
        return all(x in k for x in RAW_KWS) and any(r[:8].strip() == "8" for b in blocks(text, "*ELEMENT_TSHELL") for r in b)
    tdoe = ("*Inputfile\nmodel.k\n*Mode\nTRANSLATION_DOE,1\n**Translation_DOE,1\nTranslationX,1,0.0,5.0\n"
            "TranslationY,1,0.0,0.0\nTranslationZ,1,0.0,0.0\n**End\n*End\n")
    d, rc, log = run("m3t", {"model.k": base_deck(keyword="*KEYWORD 2000m")}, tdoe)
    outs = [p.read_text(errors="replace") for p in sorted(d.glob("model_TranslationDOE_*.k"))]
    check("M3 TRANSLATION_DOE 2개: 두 출력 모두 원문 블록(TSHELL 줄·DISCRETE·SEATBELT·NOD3DUMP)이 있다",
          rc == 0 and len(outs) == 2 and all(raw_ok(t) for t in outs), f"rc={rc} n={len(outs)} " + str([sorted(set(kw_lines(t))) for t in outs][:1]))
    check("M3 TRANSLATION_DOE 2개: *KEYWORD 줄 옵션(2000m)을 지킨다",
          len(outs) == 2 and all(t.splitlines()[0].strip().upper() == "*KEYWORD 2000M" for t in outs), str([t.splitlines()[:1] for t in outs]))
    d, rc, log = run("m3k", {"model.k": base_deck(keyword="*KEYWORD 2000m")}, TRANS)
    t = (d / "model_trans.k").read_text(errors="replace") if (d / "model_trans.k").exists() else ""
    check("M3 일반 기록기(TRANSFORM)도 *KEYWORD 줄 옵션(2000m)을 지킨다 — 예전엔 '*KEYWORD' 로 고정",
          rc == 0 and t.splitlines()[:1] == ["*KEYWORD 2000m"], f"rc={rc} {t.splitlines()[:1]}")
    pld = ("*Inputfile\nmodel.k\n*Mode\nPART_LOCATION_DOE,1\n**PartLocationDOE,1\n*PIDs,1\n*dx,0.5\n*dy,0.5\n*nx,10\n*ny,10\n"
           "*MaskPID,0\n*Dilation,1\n*Sampling,LatinHypercube,2\n**EndPartLocationDOE\n*End\n")
    d, rc, log = run("m3p", {"model.k": base_deck()}, pld)
    outs = [p.read_text(errors="replace") for p in sorted(d.glob("model_DX_*.k"))]
    check("M3 PART_LOCATION_DOE 2개: 두 출력 모두 원문 블록이 있다", rc == 0 and len(outs) == 2 and all(raw_ok(t) for t in outs),
          f"rc={rc} n={len(outs)}")
    drop = ("*Inputfile\nmodel.k\n*RunDirectoryMode,True,runs\n*Mode\nDROP_ATTITUDE,1\n**DropAttitude,1\nEulerRolling,0,90\n"
            "EulerPitching,0,0\nEulerYawing,0,0\nHeight,100,100\nInitialVelocityX,0,0\nInitialVelocityY,0,0\nInitialVelocityZ,0,0\n"
            "InitialAngularVelocityX,0,0\nInitialAngularVelocityY,0,0\nInitialAngularVelocityZ,0,0\nOffsetDistance,0.05\n"
            "Density,7.85e-9\nYoungsModulus,2.0e5\nPoissonRatio,0.3\ntFinal,0.001\ndt,1e-6\n**EndDropAttitude\n*End\n")
    d, rc, log = run("m3d", {"model.k": base_deck()}, drop)
    dsets = [p for p in sorted(d.rglob("DropSet.k")) if p.parent.parent.name == "runs"]
    outs = [p.read_text(errors="replace") for p in dsets]

    def ssid_defined(text):
        """SSTYP 2(파트 셋)로 가리키는 접촉 SSID·MSID 가 모두 *SET_PART 로 정의돼 있는가."""
        defined = set()
        for b in blocks(text, "*SET_PART"):
            data = [ln for ln in b if ln.strip()]
            for ln in data[:2]:
                try:
                    defined.add(int(ln[:10]))
                    break
                except ValueError:
                    continue
        need = set()
        lines = text.splitlines()
        for i, ln in enumerate(lines):
            if ln.startswith("*CONTACT_"):
                data = [x for x in lines[i + 1:i + 6] if not x.startswith("$") and not x.startswith("*")]
                if ln.upper().rstrip().endswith("_ID") and data:
                    data = data[1:]
                if data:
                    c = data[0]
                    for idx, typ in ((0, 2), (1, 3)):
                        try:
                            if int(c[typ * 10:(typ + 1) * 10] or 0) == 2:
                                need.add(int(c[idx * 10:(idx + 1) * 10]))
                        except ValueError:
                            pass
        return need <= defined, need, defined
    check("M3 DROP 2각도: 두 DropSet.k 모두 원문 블록이 있다", rc == 0 and len(outs) == 2 and all(raw_ok(t) for t in outs),
          f"rc={rc} n={len(outs)}")
    check("M3 DROP 2각도: 접촉이 가리키는 파트 셋(SSTYP 2)이 덱에 모두 정의돼 있다",
          len(outs) == 2 and all(ssid_defined(t)[0] for t in outs), str([ssid_defined(t)[1:] for t in outs]))
    dwip = ("*Inputfile\nmodel.k\n*Mode\nDROP_WEIGHT_IMPACT_TEST,1\n**DropWeightImpactTest,1\nGenerationMode,Part\nPartIDs,1\n"
            "LocationMode,2X1\nHeight,100\nInitialVelocityX,0\nInitialVelocityY,0\nInitialVelocityZ,0\nGravity,9810\n"
            "ImpactorType,Sphere\nImpactorDimension,0.5\nMeshSize,0.25\nTFinal,0.0001\nDT,1e-05\nOffsetDistance,0.05\n"
            "**EndDropWeightImpactTest\n*End\n")
    d, rc, log = run("m3w", {"model.k": base_deck()}, dwip)
    outs = [p.read_text(errors="replace") for p in sorted(d.glob("model_MODE_DWIP_*.k"))]
    check("M3 DWI Part 2X1: 두 출력 모두 원문 블록이 있다", rc == 0 and len(outs) == 2 and all(raw_ok(t) for t in outs),
          f"rc={rc} n={len(outs)}")

    # ── M4 DTI ───────────────────────────────────────────────────────────────────────────────
    def dti_pts():
        p = {k: v for k, v in points().items() if k <= 24}
        p.update({50: (5.0, 0.0, 0.0), 51: (6.0, 0.0, 0.0), 52: (6.0, 1.0, 0.0), 53: (5.0, 1.0, 0.0)})
        return p

    def dti_elems():
        return ("*ELEMENT_SOLID\n" + "".join(f"{e:8d}{1:8d}" + "".join(f"{n:8d}" for n in c) + "\n" for e, c in SOLID.items())
                + "*ELEMENT_TSHELL\n" + "".join(f"{e:8d}{2:8d}" + "".join(f"{n:8d}" for n in c) + "\n" for e, c in TSH.items())
                + "*ELEMENT_SHELL\n" + f"{9:8d}{3:8d}{50:8d}{51:8d}{52:8d}{53:8d}\n")
    dti_base = ("*KEYWORD\n*CONTROL_TERMINATION\n" + f10(0.001) + "*NODE\n" + node_lines(dti_pts()) + dti_elems()
                + "*PART\nhousing\n" + f10(1, 1, 1) + "*PART\nfpcb\n" + f10(2, 2, 1) + "*PART\nplate\n" + f10(3, 3, 1)
                + "*SECTION_SOLID\n" + f10(1, 1) + "*SECTION_TSHELL\n" + f10(2, 1, 0.8333, 3, 1, 0.0, 0, 0)
                + "*SECTION_SHELL\n" + f10(3, 2, 0.8333, 3) + f10(0.5, 0.5, 0.5, 0.5) + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
                + "*END\n")

    def dynain(s):
        p = {k: (x, y, z + 0.01) for k, (x, y, z) in dti_pts().items()}
        return ("*KEYWORD\n*NODE\n" + node_lines(p) + dti_elems()
                + "*INITIAL_STRESS_SOLID\n" + f10(1, 1, 0, 0, 0, 0, 0, 0) + f10(s + 1.0, s + 2.0, s + 3.0, 1.0, 2.0, 3.0, 0.01)
                + "*INITIAL_STRESS_SHELL\n" + f10(9, 1, 3, 0, 0, 0, 0, 0)
                + "".join(f10(t, s + 21.0, 22.0, 0.0, 2.1, 0.0, 0.0, 0.02) for t in (-0.7746, 0.0, 0.7746))
                + "*INITIAL_STRESS_TSHELL\n" + f10(3, 1, 3, 0, 0)
                + "".join(f10(t, s + 31.0, 32.0, 33.0, 3.1, 3.2, 3.3, 0.03) for t in (-0.7746, 0.0, 0.7746)) + "*END\n")
    dti = ("*Inputfile\nmodel.k\n*Mode\nDYNAIN_TO_INITIAL,1\n**DynainToInitial,1\n*DynainPath,dynain\n*IncludeStress,True\n"
           "*RemoveDynamicRelaxation,True\n**EndDynainToInitial\n*End\n")
    d, rc, log = run("m4", {"model.k": dti_base, "dynain": dynain(0.0)}, dti)
    t = (d / "model_dti.k").read_text(errors="replace") if (d / "model_dti.k").exists() else ""
    sh, ts = blocks(t, "*INITIAL_STRESS_SHELL"), blocks(t, "*INITIAL_STRESS_TSHELL")
    check("M4 DTI: rc 0", rc == 0 and no_tb(log), f"rc={rc} " + log[-400:])
    check("M4 DTI: dynain 의 *INITIAL_STRESS_SHELL(EID 9)·TSHELL(EID 3) 이 출력에 그대로 있다",
          len(sh) == 1 and len(ts) == 1 and "21.0" in "".join(sh[0]) and "31.0" in "".join(ts[0]) and "*INITIAL_STRESS_SOLID" in kw_lines(t),
          f"shell={sh} tshell={ts}")
    if t:
        d2, rc2, log2 = run("m4b", {"model.k": t, "dynain": dynain(100.0)}, dti)
        t2 = (d2 / "model_dti.k").read_text(errors="replace") if (d2 / "model_dti.k").exists() else ""
        ts2 = blocks(t2, "*INITIAL_STRESS_TSHELL")
        check("M4 DTI 두 번째 단계: 새 dynain 의 TSHELL 응력 한 벌만(앞 단계 값이 남거나 겹치지 않는다)",
              rc2 == 0 and len(ts2) == 1 and "131.0" in "".join(ts2[0]) and " 31.0" not in "".join(ts2[0]), f"rc={rc2} {ts2}")

    # ── M5 DWI OutsideRigid*·Part 와 *RunDirectoryMode ──────────────────────────────────────────
    def dwi(mode, extra=""):
        return ("*Inputfile\nmodel.k\n*RunDirectoryMode,True,@D@/results/dwi_0001\n*Mode\nDROP_WEIGHT_IMPACT_TEST,1\n"
                "**DropWeightImpactTest,1\nTFinal,0.0001\nDT,1e-05\nLocationX,1.0\nLocationY,0.5\nHeight,100\nInitialVelocityX,0\n"
                "InitialVelocityY,0\nInitialVelocityZ,0\nGravity,9810\nImpactorType,Sphere\nImpactorDimension,0.5\nMeshSize,0.25\n"
                "DensityImpactor,7.85e-09\nYoungsModulusImpactor,200000.0\nPoissonRatioImpactor,0.3\n"
                f"GenerationMode,{mode}\n{extra}BoundaryDistance,0.6\nOffsetDistance,0.05\nYoungsModulusWall,10000.0\n"
                "PoissonRatioWall,0.3\nDensityWall,1e-09\n**EndDropWeightImpactTest\n*End\n")
    for mode, extra in (("DampingSpring", ""), ("OutsideRigidElement", ""), ("OutsideRigidPart", ""), ("Part", "PartIDs,1\nLocationMode,1X1\n")):
        d, rc, log = run(f"m5_{mode}", {"model.k": base_deck(raw=False)}, dwi(mode, extra))
        sets = sorted((d / "results" / "dwi_0001").glob("Run_*/DropWeightImpactTestSet.k"))
        check(f"M5 DWI {mode}: *RunDirectoryMode 아래 Run_*/DropWeightImpactTestSet.k 가 생긴다", rc == 0 and len(sets) == 1,
              f"rc={rc} {sets} " + log[-300:])
    d, rc, log = run("m5_rawmat", {"model.k": base_deck(raw=True)}, dwi("OutsideRigidElement"))
    check("M5 DWI OutsideRigidElement: 원문 재질 파트(스프링)가 있어도 죽지 않는다", rc == 0 and no_tb(log), f"rc={rc} " + log[-400:])

    # ── M6 MIRROR ────────────────────────────────────────────────────────────────────────────
    for plane in ("XY", "YZ", "XZ"):
        mo = f"*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nMirror,{plane}\n**EndTransform\n*End\n"
        d, rc, log = run(f"m6_{plane}", {"model.k": base_deck()}, mo)
        t = (d / "model_trans.k").read_text(errors="replace") if (d / "model_trans.k").exists() else ""
        s = hex_signs(t)
        check(f"M6 MIRROR {plane}: HEXA8 1·2·TSHELL8 3·4·원문 TSHELL 8 의 자코비안이 모두 양수",
              rc == 0 and all(s.get(e, -1) > 0 for e in (1, 2, 3, 4, 8)), f"rc={rc} {s}")

    # ── M7 TShellMode(같은 실행 ConvertHexato,TShell) ──────────────────────────────────────────
    def slab():
        pts, ids, n = {}, {}, 1
        for k, z in enumerate((0.0, 0.5)):
            for j in range(3):
                for i in range(3):
                    pts[n] = (float(i), float(j), z)
                    ids[(i, j, k)] = n
                    n += 1
        rows, e = [], 1
        for j in range(2):
            for i in range(2):
                c = [ids[(i, j, 0)], ids[(i + 1, j, 0)], ids[(i + 1, j + 1, 0)], ids[(i, j + 1, 0)],
                     ids[(i, j, 1)], ids[(i + 1, j, 1)], ids[(i + 1, j + 1, 1)], ids[(i, j + 1, 1)]]
                rows.append(f"{e:8d}{1:8d}" + "".join(f"{x:8d}" for x in c) + "\n")
                e += 1
        return ("*KEYWORD\n*NODE\n" + node_lines(pts) + "*ELEMENT_SOLID\n" + "".join(rows) + "*PART\nslab\n" + f10(1, 1, 1)
                + "*SECTION_SOLID\n" + f10(1, 1) + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3) + "*END\n")
    pex = "**PartExchange,1\n*PID,1\n*ConvertHexato,TShell,(0,0,1),5.0\n**EndPartExchange\n"
    therm = ("**ThermalLoad,2\nThermalType,ICPower\nPhase,thermal\nAnalysisType,transient\nUnitSystem,SI\nInitialTemperatureC,25\n"
             "TimestepIts,0.01\nMaterials\n1,7.85e-09,4.6e+08,50\nEndMaterials\nHeatSources\n1,1.5,8.0\nEndHeatSources\n**EndThermalLoad\n")
    d, rc, log = run("m7t", {"model.k": slab()}, "*Inputfile\nmodel.k\n*Mode\nPART_EXCHANGE,1\nTHERMAL_LOAD,2\n" + pex + therm + "*End\n")
    check("M7 PART_EXCHANGE ConvertHexato,TShell → THERMAL 발열원: 덱 TSHELL 과 같이 원인을 밝혀 멈춘다(rc 1)",
          rc == 1 and "TSHELL 파트 발열은 지원하지 않는다" in log, f"rc={rc} " + log[-400:])
    rig = "**RigidifySmallDt,2\n*DtThreshold,0.0\n*ElementIDs,2\n**End\n"
    d, rc, log = run("m7r", {"model.k": slab()}, "*Inputfile\nmodel.k\n*Mode\nPART_EXCHANGE,1\nRIGIDIFY_SMALL_DT,2\n" + pex + rig + "*End\n")
    outs = [p for p in sorted(d.glob("*.k")) if p.name not in ("model.k",) and "dump" not in p.name]
    t = outs[-1].read_text(errors="replace") if outs else ""
    k = kw_lines(t)
    sec_kind, lines = {}, t.splitlines()
    for i, ln in enumerate(lines):   # 단면 번호 → 종류(_TITLE 이면 제목 줄 다음이 카드 1)
        h = ln.split()[0].upper() if ln.startswith("*SECTION_") else ""
        if h:
            data = [x for x in lines[i + 1:i + 4] if not x.startswith("$")]
            card = data[1] if h.endswith("_TITLE") and len(data) > 1 else (data[0] if data else "")
            try:
                sec_kind[int(card[:10])] = h.replace("_TITLE", "")
            except ValueError:
                pass
    used = {p: sec_kind.get(s) for p, s in parts_of(t).items()}   # 원래 솔리드 단면 1 은 ConvertHexato 뒤 아무도 쓰지 않는 카드로 남는다
    check("M7 PART_EXCHANGE ConvertHexato,TShell → 수동 강체화: 강체 조각도 *ELEMENT_TSHELL·TSHELL 단면(솔리드로 바뀌지 않음)",
          rc == 0 and "*ELEMENT_SOLID" not in k and "*ELEMENT_TSHELL" in k and len(used) == 2
          and all(v == "*SECTION_TSHELL" for v in used.values()), f"rc={rc} {sorted(set(k))} parts→단면 {used}")

    # ── M8 PART_EXCHANGE 단면·요소 종류 불일치 ────────────────────────────────────────────────
    ts_sec = "*SECTION_TSHELL\n" + f"{'SID':>10}" + f10(1, 0.8333, 3, 1, 0.0, 0, 0).rstrip("\n") + "\n"
    d, rc, log = run("m8", {"model.k": slab()}, "*Inputfile\nmodel.k\n*Mode\nPART_EXCHANGE,1\n**PartExchange,1\n*PID,1\n" + ts_sec
                     + "**EndPartExchange\n*End\n")
    check("M8 PART_EXCHANGE: HEXA8 파트에 *SECTION_TSHELL 만 주면 경고(ConvertHexato 안내)", "ConvertHexato" in log and "⚠" in log,
          log[-400:])

    # ── X1 원문 재질의 거짓 '재질 MID 소실' ─────────────────────────────────────────────────────
    d, rc, log = run("x1", {"model.k": base_deck()}, TRANS)
    check("X1 원문으로 나가는 *MAT_SPRING_ELASTIC·*MAT_SEATBELT 를 '재질 MID 소실' 로 알리지 않는다",
          rc == 0 and "재질 MID 소실" not in log, [ln for ln in log.splitlines() if "재질" in ln][:3])

    # ── X2 서로 다른 모드의 같은 모드 ID ─────────────────────────────────────────────────────────
    d, rc, log = run("x2", {"model.k": slab()}, "*Inputfile\nmodel.k\n*Mode\nPART_EXCHANGE,1\nTHERMAL_LOAD,1\n" + pex
                     + therm.replace("**ThermalLoad,2", "**ThermalLoad,1") + "*End\n")
    check("X2 PART_EXCHANGE,1·THERMAL_LOAD,1: 모드 ID 가 겹친다고 알리고 멈춘다(rc 1, Traceback 없음)",
          rc == 1 and "모드 ID" in log and no_tb(log), f"rc={rc} " + log[-400:])

    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
