# 강체 질량특성 모듈(KooRigidBodyProperties)을 손으로 푼 작은 덱과 실제 덱(d3hsp·Radioss 기준값)으로 검증하는 시험
"""
실행: venv312/bin/python tests/test_rigid_body_properties.py

덱은 KMM 리더(KooMeshModifier → ImportBaseFile)로 읽는다. 리더는 덱 옆에 <이름>_dump.k 를 쓰고 그 폴더로 chdir 하므로
덱은 언제나 작업 폴더(RIGID_BODY_TEST_DIR, 기본 /data/koopark/Test_RigidDropEndtime/A/test)에 복사해 읽는다.

  [1] 작은 덱 — 육면체·쐐기 셋(R16 1 2 3 4 5 5 6 6·TSHELL 1 2 3 3 4 5 6 6·KMM PENTA6)·피라미드·사면체·10절점 사면체·셸
      (MAREA·*ELEMENT_SHELL_THICKNESS·N4=N3 삼각형)·*PART_COMPOSITE·빔·절점 질량·I10, 손으로 푼 질량·무게중심·관성과 견준다
  [2] 원문 키워드 — *ELEMENT_MASS_PART(_SET)·*PART_INERTIA(IRCS=1)·*CONSTRAINED_NODAL_RIGID_BODY_INERTIA·원문 *MAT 밀도
  [3] 제외 규칙·단위 판정
  [4] 실제 덱 — MinimumModel(d3hsp)·DropSet(바닥 자동 제외)·SimpleDrop(Radioss)·경계 장난감 덱, OBJ/JSON 열어 보기
      d3hsp·Radioss 관성은 절점 집중 질량으로 잰 값이다. 그래서 같은 요소 질량을 절점에 나눈 값(이 시험이 따로 계산)은
      출력 자릿수 안에서 맞아야 하고, 모듈의 연속체 관성은 격자가 거친 만큼 다르다(차이를 찍는다).
덱 파일이 없으면 그 덱은 SKIP 줄을 찍고 건너뛴다.
"""
import contextlib
import gc
import io
import json
import os
import re
import resource
import shutil
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(GEN))

WORK = Path(os.environ.get("RIGID_BODY_TEST_DIR", "/data/koopark/Test_RigidDropEndtime/A/test"))
MINIMUM = ROOT / "Examples" / "MinimumModel.k"
MIN_D3HSP = Path("/data/koopark/Test_Postprocess_v14/output/Run_20260522_132307_0d0978/Output/d3hsp")
DROPSET = Path("/data/koopark/manual_lsdyna_test/DropSet.k")
DROPSET_D3HSP = Path("/data/koopark/manual_lsdyna_test/d3hsp")
SIMPLE = Path("/home/koopark/claude/KooOpenRadioss/DynaExamples/SimpleDrop/simple_drop/case01_simple.k")
SIMPLE_OUT = SIMPLE.with_name("case01_simple_0000.out")
TOY = Path("/data/koopark/review_v131_R2/a_drop2_new/model.k")
DROPSET_SHIFT = np.array([35.5, 73.5, 4.5])   # DropSet.k(=d3hsp 좌표) = MinimumModel.k − 이 값. [4b] 에서 절점으로 확인한다

RHO = 7.85e-9
FAILS = []


def check(name, cond, detail=""):
    print("  %-74s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def rel(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.abs(a - b).max() / max(np.abs(b).max(), 1e-300))


# ── 덱 글 ──────────────────────────────────────────────────────────────────
def f10(*v):
    return "".join(f"{str(x):>10s}" for x in v)


def kdeck(*secs, head="*KEYWORD"):
    out = [head]
    for s in secs:
        out += s
    return "\n".join(out + ["*END"]) + "\n"


def kw_nodes(nodes, i10=False):
    if i10:
        return ["*NODE"] + [f"{n:10d}{x:16.8f}{y:16.8f}{z:16.8f}" for n, (x, y, z) in nodes.items()]
    return ["*NODE"] + [f"{n:8d}{x:16.8f}{y:16.8f}{z:16.8f}" for n, (x, y, z) in nodes.items()]


def kw_solids(elems, i10=False):
    w = 10 if i10 else 8
    return ["*ELEMENT_SOLID"] + ["".join(f"{v:{w}d}" for v in (e, p, *ns)) for e, p, ns in elems]


def kw_part(pid, sid, mid, title=None):
    return ["*PART", title or f"part{pid}", f10(pid, sid, mid)]


def kw_mat(mid, rho):
    return ["*MAT_ELASTIC", f10(mid, f"{rho:.4E}", "210000.0", "0.3")]


def solid_part(pid, rho, mid=None):
    mid = mid or pid
    return kw_part(pid, pid, mid) + ["*SECTION_SOLID", f10(pid, 1)] + kw_mat(mid, rho)


def cube(n0, o, a=1.0):
    pts = [(0, 0, 0), (a, 0, 0), (a, a, 0), (0, a, 0), (0, 0, a), (a, 0, a), (a, a, a), (0, a, a)]
    return {n0 + i: (o[0] + p[0], o[1] + p[1], o[2] + p[2]) for i, p in enumerate(pts)}, list(range(n0, n0 + 8))


def body(rho, vol, com, s_c):
    """밀도·부피·무게중심·무게중심 둘레 ∫rrᵀdV → (질량, 무게중심, 관성 텐서)."""
    s_c = np.asarray(s_c, float)
    return rho * vol, np.asarray(com, float), rho * (np.trace(s_c) * np.eye(3) - s_c)


def from_origin(rho, vol, f, s):
    """원점 둘레 모멘트(V, ∫x, ∫xxᵀ) → (질량, 무게중심, 관성)."""
    c = np.asarray(f, float) / vol
    return body(rho, vol, c, np.asarray(s, float) - vol * np.outer(c, c))


def combine(items):
    m = sum(i[0] for i in items)
    c = sum(i[0] * i[1] for i in items) / m
    inertia = np.zeros((3, 3))
    for mi, ci, ii in items:
        d = ci - c
        inertia += ii + mi * (d @ d * np.eye(3) - np.outer(d, d))
    return m, c, inertia


def cube_body(rho, o, a=1.0):
    return body(rho, a ** 3, np.asarray(o, float) + a / 2, a ** 5 / 12 * np.eye(3))


def point_body(m, x):
    return m, np.asarray(x, float), np.zeros((3, 3))


# ── 읽기·계산 ────────────────────────────────────────────────────────────────
KMM = None


def load(name, text=None, src=None):
    """덱을 작업 폴더에 두고 KMM 리더로 읽는다 → (dynaImporter, 리더 로그)."""
    global KMM
    with contextlib.redirect_stdout(io.StringIO()):
        if KMM is None:
            import KooMeshModifier as KMM_mod
            KMM = KMM_mod
    from KooCAEManager.KooElement import IMPORT_LOSS
    IMPORT_LOSS.clear()                       # 리더 소실 장부는 프로세스 전역이다 — 덱마다 새로
    d = WORK / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    if text is not None:
        fn = "model.k"
        (d / fn).write_text(text)
    else:
        fn = Path(src).name
        shutil.copy(src, d / fn)
    cwd, buf = os.getcwd(), io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            g = KMM.KooMeshModifier()
            g.SetCurrentDirectory(str(d))
            g.inputFileName = fn
            g.ImportBaseFile()
    finally:
        os.chdir(cwd)
    return g.dynaImporter, buf.getvalue()


def compute(imp, **kw):
    from KooCAEManager.KooRigidBodyProperties import compute_rigid_body
    logs = []
    rb = compute_rigid_body(imp, log=logs.append, **kw)
    return rb, logs


def part_of(rb, pid):
    return next(p for p in rb["parts"] if p["pid"] == pid)


def has_warn(rb, code, text=""):
    return any(w.startswith(code) and text in w for w in rb["warnings"])


def check_body(tag, got, want, tol=1e-9):
    m, c, inertia = want
    check(f"{tag}: 질량 {m:.6e}", rel(got["mass"], m) < tol, f"{got['mass']} vs {m}")
    check(f"{tag}: 무게중심 {np.round(c, 6)}", np.abs(np.asarray(got["com"]) - c).max() < tol * (1 + np.abs(c).max()),
          f"{got['com']} vs {c}")
    key = "inertia_com"
    check(f"{tag}: 관성 텐서(상대 {tol:g})", rel(got[key], inertia) < tol, f"\n{got[key]}\nvs\n{inertia}")


# ── 기준값 읽기 ──────────────────────────────────────────────────────────────
def read_d3hsp(path):
    """d3hsp 'mass properties of part #' → {PID: (질량, 무게중심, 관성 텐서)} — 관성은 파트 무게중심 둘레다."""
    lines, out = path.read_text(errors="replace").splitlines(), {}
    for i, ln in enumerate(lines):
        m = re.match(r"\s*m a s s   p r o p e r t i e s   o f   p a r t #\s*(\d+)", ln)
        if m:
            val = lambda k: float(lines[i + k].split("=")[1])
            rows = [[float(x) for x in lines[i + 7 + r].split("=")[1].split()] for r in range(3)]
            out[int(m.group(1))] = (val(1), np.array([val(2), val(3), val(4)]), np.array(rows))
    return out


def read_radioss(path):
    """Radioss 시작 출력 'PART MASS & INERTIA' → {PID: (질량, 무게중심, [Ixx Iyy Izz])}."""
    lines, out = path.read_text(errors="replace").splitlines(), {}
    for i, ln in enumerate(lines[:-4]):
        m = re.match(r"\s*PART :\s*(\d+),", ln)
        if m and "Mass" in lines[i + 1]:
            v = [float(x) for x in lines[i + 2].split()]
            out[int(m.group(1))] = (v[0], np.array([float(x) for x in lines[i + 4].split()[:3]]), np.array(v[1:4]))
    return out


def lumped(part, rho):
    """솔버처럼 절점 집중 질량(사면체 m/4·육면체 m/8)으로 잰 파트 (질량, 무게중심, 관성). 부피는 모듈과 따로 계산한다
    (사면체 행렬식, 육면체 2×2×2 가우스 — 삼선형 부피에 정확)."""
    g = 1 / np.sqrt(3)
    q = np.array([(a, b, c) for a in (-g, g) for b in (-g, g) for c in (-g, g)])
    s = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)
    t = 1 + q[:, None, :] * s[None]
    dn = np.stack([s[None, :, k] * t[:, :, [m for m in range(3) if m != k]].prod(2) / 8 for k in range(3)], axis=2)
    ids, xyz, tet, hexa = {}, [], [], []
    for e in part.elementManager.elements.values():
        rows = []
        for n in e.nodes[:4 if e.type == "TETRA4" else 8]:
            if n.id not in ids:
                ids[n.id] = len(xyz)
                xyz.append((n.x, n.y, n.z))
            rows.append(ids[n.id])
        (tet if e.type == "TETRA4" else hexa).append(rows)
    xyz, nm = np.array(xyz, float), np.zeros(len(xyz))
    if tet:
        tet = np.array(tet)
        p = xyz[tet]
        v = np.abs(np.einsum("ij,ij->i", p[:, 1] - p[:, 0], np.cross(p[:, 2] - p[:, 0], p[:, 3] - p[:, 0]))) / 6
        np.add.at(nm, tet.ravel(), np.repeat(rho * v / 4, 4))
    if hexa:
        hexa = np.array(hexa)
        v = np.abs(np.linalg.det(np.einsum("gik,nid->ngdk", dn, xyz[hexa])).sum(1))
        np.add.at(nm, hexa.ravel(), np.repeat(rho * v / 8, 8))
    m = nm.sum()
    c = (nm[:, None] * xyz).sum(0) / m
    d = xyz - c
    sc = np.einsum("n,ni,nj->ij", nm, d, d)
    return m, c, np.trace(sc) * np.eye(3) - sc


def read_obj(path):
    v, f, g = [], [], []
    for ln in Path(path).read_text().splitlines():
        if ln.startswith("v "):
            v.append([float(x) for x in ln.split()[1:4]])
        elif ln.startswith("f "):
            f.append([int(x) for x in ln.split()[1:4]])
        elif ln.startswith("g "):
            g.append(ln[2:])
    return np.array(v), np.array(f, int), g


# ── [1] 작은 덱 ──────────────────────────────────────────────────────────────
def test_small_solids():
    print("[1a] 육면체 하나 (mm-t-s, 원점 밖)")
    o = (10.0, 20.0, 30.0)
    nodes, conn = cube(1, o)
    imp, _ = load("cube", kdeck(solid_part(1, RHO), kw_nodes(nodes), kw_solids([(1, 1, conn)])))
    rb, logs = compute(imp)
    want = cube_body(RHO, o)
    check_body("육면체", rb, want, 1e-12)
    check("단위계 mm-t-s 자동, 경고 없음", rb["units"]["name"] == "mm-t-s" and rb["units"]["source"].startswith("auto")
          and not rb["warnings"], str(rb["units"]) + str(rb["warnings"]))
    check("주관성 오름차순 = m/6 셋, 주축 오른손 정규직교", np.allclose(rb["principal_moments"], RHO / 6, rtol=1e-12)
          and abs(np.linalg.det(rb["principal_axes"]) - 1) < 1e-12
          and np.allclose(rb["principal_axes"].T @ rb["principal_axes"], np.eye(3), atol=1e-12))
    h = rb["hull"]
    check("볼록 껍질: 꼭짓점 8·삼각형 12·부피 1·넓이 6", h["n_vertices"] == 8 and len(h["faces"]) == 12
          and abs(h["volume"] - 1) < 1e-12 and abs(h["area"] - 6) < 1e-12, str(h["volume"]))
    s = rb["surface"]
    check("외곽면: 삼각형 12·넓이 6·묶음 PART_1_part1", s["n_triangles"] == 12 and abs(s["area"] - 6) < 1e-12
          and [g for g, _ in s["groups"]] == ["PART_1_part1"])
    check("bbox·OBB(크기 1, 가운데 = 무게중심)", np.allclose(rb["bbox"]["min"], o) and np.allclose(rb["bbox"]["max"], np.add(o, 1))
          and np.allclose(rb["obb"]["extents"], 1) and np.allclose(rb["obb"]["center"], want[1]))
    si = rb["si"]
    check("SI 환산: kg·m·kg·m²", rel(si["mass_kg"], RHO * 1e3) < 1e-12 and np.allclose(si["com_m"], want[1] * 1e-3)
          and rel(si["inertia_com_kgm2"], want[2] * 1e3 * 1e-6) < 1e-12 and np.allclose(si["hull_vertices_m"], h["vertices"] * 1e-3))
    check("로그 표지: UNITS·SUMMARY (영어)", any(x.startswith("[RigidBody] UNITS mm-t-s") for x in logs)
          and any(x.startswith("[RigidBody] SUMMARY mass=") for x in logs), "\n".join(logs))

    print("[1b] 같은 육면체를 *KEYWORD I10=Y (9자리 절점·요소 번호)")
    nodes, conn = cube(100000001, o)
    imp, _ = load("cube_i10", kdeck(solid_part(1, RHO), kw_nodes(nodes, True), kw_solids([(200000001, 1, conn)], True),
                                   head="*KEYWORD I10=Y"))
    rb, _ = compute(imp)
    check_body("I10 육면체", rb, want, 1e-12)

    print("[1c] 쐐기 셋·피라미드·사면체 (겹친 절점 육면체)")
    nodes, elems, wants = {}, [], {}
    # PID 1: R16 쐐기 1 2 3 4 5 5 6 6 — xz 삼각형 (0,0)(1,0)(0,1) 을 y 0~1 로 민 것
    nodes.update({1: (0, 0, 0), 2: (1, 0, 0), 3: (1, 1, 0), 4: (0, 1, 0), 5: (0, 0, 1), 6: (0, 1, 1)})
    elems.append((1, 1, [1, 2, 3, 4, 5, 5, 6, 6]))
    wants[1] = from_origin(RHO, 0.5, [1 / 6, 1 / 4, 1 / 6],
                           [[1 / 12, 1 / 12, 1 / 24], [1 / 12, 1 / 6, 1 / 12], [1 / 24, 1 / 12, 1 / 12]])
    # PID 2: TSHELL·응집 쐐기 1 2 3 3 4 5 6 6 / PID 3: KMM PENTA6(1줄 6절점 + 6 6) — xy 삼각형을 z 0~1 로 민 것
    prism_s = [[1 / 12, 1 / 24, 1 / 12], [1 / 24, 1 / 12, 1 / 12], [1 / 12, 1 / 12, 1 / 6]]
    for pid, n0, ox, order in ((2, 11, 5.0, [0, 1, 2, 2, 3, 4, 5, 5]), (3, 21, 10.0, [0, 1, 2, 3, 4, 5, 5, 5])):
        tri = [(0, 0), (1, 0), (0, 1)]
        nodes.update({n0 + i: (ox + tri[i % 3][0], tri[i % 3][1], float(i // 3)) for i in range(6)})
        elems.append((pid, pid, [n0 + k for k in order]))
        m, c, inertia = from_origin(RHO, 0.5, [1 / 6, 1 / 6, 1 / 4], prism_s)
        wants[pid] = (m, c + [ox, 0, 0], inertia)
    # PID 4: 사면체 1 2 3 4 4 4 4 4
    nodes.update({31: (15, 0, 0), 32: (16, 0, 0), 33: (15, 1, 0), 34: (15, 0, 1)})
    elems.append((4, 4, [31, 32, 33, 34, 34, 34, 34, 34]))
    m, c, inertia = from_origin(RHO, 1 / 6, [1 / 24] * 3, np.full((3, 3), 1 / 120) + np.eye(3) / 120)
    wants[4] = (m, c + [15, 0, 0], inertia)
    # PID 5: 피라미드 1 2 3 4 5 5 5 5 (밑면 단위 정사각형, 꼭짓점 (0.5,0.5,1)) — 리더는 PENTA6(5 가 둘)로 읽는다
    nodes.update({41: (20, 0, 0), 42: (21, 0, 0), 43: (21, 1, 0), 44: (20, 1, 0), 45: (20.5, 0.5, 1)})
    elems.append((5, 5, [41, 42, 43, 44, 45, 45, 45, 45]))
    wants[5] = body(RHO, 1 / 3, [20.5, 0.5, 0.25], np.diag([1 / 60, 1 / 60, 1 / 80]))
    secs = []
    for pid in range(1, 6):
        secs += kw_part(pid, 1, 1) if pid > 1 else solid_part(1, RHO)
    imp, _ = load("wedges", kdeck(secs, kw_nodes(nodes), kw_solids(elems)))
    types = {e.type for p in imp.partManager.parts.values() for e in p.elementManager.elements.values()}
    check("리더 형식: HEXA8(쐐기 둘)·PENTA6(KMM 쐐기·피라미드)·TETRA4", types == {"HEXA8", "PENTA6", "TETRA4"}, str(types))
    rb, _ = compute(imp)
    names = {1: "R16 쐐기 1 2 3 4 5 5 6 6", 2: "TSHELL 쐐기 1 2 3 3 4 5 6 6", 3: "KMM PENTA6", 4: "사면체 4 4 4 4", 5: "피라미드 5 5 5 5"}
    for pid in range(1, 6):
        check_body(names[pid], part_of(rb, pid), wants[pid], 1e-12)
    check_body("다섯 파트 합", rb, combine([wants[p] for p in range(1, 6)]), 1e-11)
    s = rb["surface"]
    check("외곽면: 쐐기 8·8·8·사면체 4·피라미드 6 삼각형(겹친 면은 삼각형·선은 버림)", s["n_triangles"] == 34,
          str(s["n_triangles"]))

    print("[1d] 10절점 사면체 (ten nodes format, 곧은 변)")
    c4 = {51: (0, 0, 0), 52: (1, 0, 0), 53: (0, 1, 0), 54: (0, 0, 1)}
    mids = {55: (51, 52), 56: (52, 53), 57: (53, 51), 58: (51, 54), 59: (52, 54), 60: (53, 54)}
    nodes = dict(c4)
    nodes.update({k: tuple((np.add(c4[a], c4[b]) / 2).tolist()) for k, (a, b) in mids.items()})
    imp, _ = load("tet10", kdeck(solid_part(1, RHO), kw_nodes(nodes), ["*ELEMENT_SOLID (ten nodes format)",
                                 f"{1:8d}{1:8d}", "".join(f"{n:8d}" for n in range(51, 61))]))
    types = {e.type for p in imp.partManager.parts.values() for e in p.elementManager.elements.values()}
    rb, _ = compute(imp)
    m, c, inertia = from_origin(RHO, 1 / 6, [1 / 24] * 3, np.full((3, 3), 1 / 120) + np.eye(3) / 120)
    check("리더 형식 TETRA10", types == {"TETRA10"}, str(types))
    check_body("10절점 사면체 = 4절점 값", rb, (m, c, inertia), 1e-12)
    check("껍질은 중간 절점까지 10개 → 꼭짓점 4", rb["hull"]["n_vertices"] == 4 and abs(rb["hull"]["volume"] - 1 / 6) < 1e-12)


def test_small_shells_beams_points():
    print("[1e] 셸: 단면 T1(빈 T2~T4)·MAREA, *ELEMENT_SHELL_THICKNESS(빈 THIC 은 단면 값), N4=N3 삼각형")
    marea, t1 = 1e-10, 0.1
    nodes = {1: (0, 0, 0), 2: (2, 0, 0), 3: (2, 1, 0), 4: (0, 1, 0),
             11: (0, 0, 5), 12: (1, 0, 5), 13: (0, 1, 5), 21: (0, 0, 6), 22: (1, 0, 6), 23: (0, 1, 6),
             31: (5, 0, 0), 32: (6, 0, 0), 33: (5, 1, 0)}
    text = kdeck(kw_part(1, 1, 1), ["*SECTION_SHELL", f10(1, 2), f10(t1, "", "", "", 0.0, marea)], kw_mat(1, RHO),
                 kw_part(2, 2, 1), ["*SECTION_SHELL", f10(2, 2), f10(t1)], kw_part(3, 2, 1), kw_nodes(nodes),
                 ["*ELEMENT_SHELL", f"{1:8d}{1:8d}{1:8d}{2:8d}{3:8d}{4:8d}", f"{4:8d}{3:8d}{31:8d}{32:8d}{33:8d}{33:8d}"],
                 ["*ELEMENT_SHELL_THICKNESS", f"{2:8d}{2:8d}{11:8d}{12:8d}{13:8d}{0:8d}", f"{0.2:16.4f}" * 3 + " " * 32,
                  f"{3:8d}{2:8d}{21:8d}{22:8d}{23:8d}{0:8d}", f"{0.0:16.4f}" * 4])
    imp, _ = load("shells", text)
    rb, _ = compute(imp)
    a, ln, w = 2.0, 2.0, 1.0
    m1 = (RHO * t1 + marea) * a
    tterm = RHO * a * t1 ** 3 / 12
    check_body("판 2×1 (T1=0.1, MAREA, 두께 항 t²/12)", part_of(rb, 1),
               (m1, np.array([1, 0.5, 0]), np.diag([m1 * w ** 2 / 12 + tterm, m1 * ln ** 2 / 12 + tterm, m1 * (ln ** 2 + w ** 2) / 12])), 1e-12)
    m_a, m_b = RHO * 0.5 * 0.2, RHO * 0.5 * 0.1
    p2 = part_of(rb, 2)
    check("THIC 0.2 삼각형 + 빈 THIC(단면 0.1) 삼각형: 질량·무게중심 z", rel(p2["mass"], m_a + m_b) < 1e-12
          and abs(p2["com"][2] - (m_a * 5 + m_b * 6) / (m_a + m_b)) < 1e-12, str(p2["mass"]))
    p3 = part_of(rb, 3)
    check("N4=N3 로 적은 삼각형 셸(리더는 겹친 사각형): 질량 = ρ·0.5·T1", rel(p3["mass"], RHO * 0.5 * t1) < 1e-12, str(p3["mass"]))
    check("외곽면: 넓이 0 조각 없이 2+1+1+1 삼각형", rb["surface"]["n_triangles"] == 5, str(rb["surface"]["n_triangles"]))

    print("[1f] 평평한 판 하나 → 껍질 HULL_DEGENERATE 경고")
    imp, _ = load("flat", kdeck(kw_part(1, 1, 1), ["*SECTION_SHELL", f10(1, 2), f10(t1)], kw_mat(1, RHO),
                                kw_nodes({k: nodes[k] for k in (1, 2, 3, 4)}), ["*ELEMENT_SHELL", f"{1:8d}{1:8d}{1:8d}{2:8d}{3:8d}{4:8d}"]))
    rb, _ = compute(imp)
    check("평평한 판: 질량 맞고 HULL_DEGENERATE, 껍질 부피 ≈ 0", rel(rb["mass"], RHO * t1 * a) < 1e-12
          and has_warn(rb, "HULL_DEGENERATE") and rb["hull"]["n_vertices"] >= 4 and rb["hull"]["volume"] < 1e-6, str(rb["warnings"]))

    print("[1g] 빔: ELFORM 1(TS·TT, NSM)·ELFORM 2(카드 2 의 A), 방향 절점은 껍질에서 뺀다")
    nodes, conn = cube(1, (0, 0, 0))
    nodes.update({101: (0, 0, 0), 102: (10, 0, 0), 103: (0, 100, 0), 201: (0, 2, 0), 202: (0, 2, 4)})
    nsm = 1e-10
    text = kdeck(solid_part(1, RHO), kw_part(2, 2, 1), ["*SECTION_BEAM", f10(2, 1, 1.0, 2.0, 0, 0.0, nsm), f10(1.0, 1.0, 2.0, 2.0)],
                 kw_part(3, 3, 1), ["*SECTION_BEAM", f10(3, 2), f10(3.0, 1.0, 1.0, 1.0, 1.0)], kw_nodes(nodes),
                 kw_solids([(1, 1, conn)]), ["*ELEMENT_BEAM", f"{2:8d}{2:8d}{101:8d}{102:8d}{103:8d}", f"{3:8d}{3:8d}{201:8d}{202:8d}"])
    imp, _ = load("beams", text)
    rb, _ = compute(imp)
    mb = (RHO * 2.0 + nsm) * 10
    check_body("빔 ELFORM 1: (ρA+NSM)L, 선 질량", part_of(rb, 2), (mb, np.array([5, 0, 0]), np.diag([0, mb * 100 / 12, mb * 100 / 12])), 1e-12)
    mc = RHO * 3.0 * 4
    check_body("빔 ELFORM 2: ρAL", part_of(rb, 3), (mc, np.array([0, 2, 2]), np.diag([mc * 16 / 12, mc * 16 / 12, 0])), 1e-12)
    check("방향 절점(0,100,0)은 껍질·bbox 밖", rb["bbox"]["max"][1] < 50 and not has_warn(rb, "BEAM_MASS"), str(rb["bbox"]))

    print("[1h] 절점 질량: *ELEMENT_MASS(PID 있음)·*ELEMENT_MASS_NODE_SET(셋에 똑같이)·PID 없는 떨어진 절점")
    o = (0.0, 0.0, 0.0)
    nodes, conn = cube(1, o)
    nodes[99] = (0.5, 0.5, 0.5)
    m = RHO
    text = kdeck(solid_part(1, RHO), kw_nodes(nodes), kw_solids([(1, 1, conn)]),
                 ["*SET_NODE_LIST", f10(10), f10(1, 2, 3, 4)],
                 ["*ELEMENT_MASS", f"{101:8d}{7:8d}{m:16.6e}{1:8d}", f"{103:8d}{99:8d}{m:16.6e}"],
                 ["*ELEMENT_MASS_NODE_SET", f"{102:8d}{10:8d}{2 * m:16.6e}"])
    imp, _ = load("points", text)
    rb, _ = compute(imp)
    items = [cube_body(RHO, o), point_body(m, nodes[7])] + [point_body(m / 2, nodes[k]) for k in (1, 2, 3, 4)] + [point_body(m, nodes[99])]
    check_body("육면체 + 절점 질량 셋", rb, combine(items), 1e-11)
    check("point_masses: 3개, 질량 4m", rb["point_masses"]["count"] == 3 and rel(rb["point_masses"]["mass"], 4 * m) < 1e-12,
          str(rb["point_masses"]))


def test_raw_keywords():
    print("[2a] *ELEMENT_MASS_PART(마지막 줄·FINMASS)·_SET(MWD 0 부피, 1 질량 비례)")
    nodes, elems = {}, []
    for k, x in enumerate((0, 3, 6, 9)):
        nd, cn = cube(10 * k + 1, (x, 0, 0))
        nodes.update(nd)
        elems.append((k + 1, k + 1, cn))
    m = RHO
    text = kdeck(solid_part(1, RHO), kw_part(2, 1, 1), kw_part(3, 1, 1), kw_part(4, 1, 2), kw_mat(2, 2 * RHO),
                 kw_nodes(nodes), kw_solids(elems), ["*SET_PART_LIST", f10(7), f10(3, 4)],
                 ["*ELEMENT_MASS_PART", f"{1:8d}{m / 2:16.6e}{0.0:16.6e}", f"{1:8d}{m:16.6e}{0.0:16.6e}", f"{2:8d}{0.0:16.6e}{3 * m:16.6e}"],
                 ["*ELEMENT_MASS_PART_SET", f"{7:8d}{2 * m:16.6e}{0.0:16.6e}{0:8d}{0:8d}", f"{7:8d}{3 * m:16.6e}{0.0:16.6e}{0:8d}{1:8d}"])
    imp, _ = load("mass_part", text)
    rb, _ = compute(imp)
    got = [part_of(rb, p)["mass"] / m for p in (1, 2, 3, 4)]
    check("파트 질량 2m·3m·3m·5m (마지막 줄, FINMASS, 셋 MWD 0/1)", np.allclose(got, [2, 3, 3, 5], rtol=1e-12), str(got))
    check("셋 분배는 면적·부피 비례 → 파트 무게중심 그대로", all(np.allclose(part_of(rb, p)["com"], [x + 0.5, 0.5, 0.5])
                                                         for p, x in zip((1, 2, 3, 4), (0, 3, 6, 9))))
    check_body("전체", rb, combine([cube_body(RHO * k, (x, 0, 0)) for k, x in zip((2, 3, 3, 5), (0, 3, 6, 9))]), 1e-11)
    check("mass_source 에 mass_part", all("mass_part" in part_of(rb, p)["mass_source"] for p in (1, 2, 3, 4)))

    print("[2b] *PART_INERTIA(IRCS=1 국부축, 요소는 리더가 버림)·*CONSTRAINED_NODAL_RIGID_BODY_INERTIA(NODEID 무게중심)")
    nodes, conn = cube(1, (0, 0, 0))
    nodes2, conn2 = cube(21, (8, 0, 0))
    nodes.update(nodes2)
    m = RHO
    il = np.diag([1e-9, 2e-9, 3e-9])
    text = kdeck(solid_part(1, RHO), ["*PART_INERTIA", "lumped body", f10(5, 1, 9),
                                      f10(5.0, 1.0, 2.0, f"{2 * m:.4E}", 1, 0), f10(*[f"{x:.1E}" for x in (1e-9, 0, 0, 2e-9, 0, 3e-9)]),
                                      f10(0, 0, 0, 0, 0, 0), f10(0.0, 1.0, 0.0, -1.0, 0.0, 0.0)],
                 ["*MAT_RIGID", f10(9, f"{RHO:.4E}", "210000.0", "0.3"), f10(0.0), ""], kw_nodes(nodes),
                 kw_solids([(1, 1, conn), (2, 5, conn2)]), ["*SET_NODE_LIST", f10(30), f10(1, 2)],
                 ["*CONSTRAINED_NODAL_RIGID_BODY_INERTIA", f10(20, 0, 30), f10(0.0, 0.0, 0.0, f"{3 * m:.4E}", 0, 7),
                  f10("1.0E-09", 0, 0, "1.0E-09", 0, "1.0E-09"), f10(0, 0, 0, 0, 0, 0)])
    imp, _ = load("inertia_cards", text)
    rb, _ = compute(imp)
    r = np.column_stack([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
    want = combine([cube_body(RHO, (0, 0, 0)), (2 * m, np.array([5.0, 1.0, 2.0]), r @ il @ r.T),
                    (3 * m, np.array(nodes[7], float), 1e-9 * np.eye(3))])
    check_body("육면체 + PART_INERTIA(국부 diag 1·2·3 → 전역 2·1·3) + CNRB_INERTIA", rb, want, 1e-11)
    check("경고: PART_INERTIA·CNRB_INERTIA·IMPORT_LOSS(버린 요소)", has_warn(rb, "PART_INERTIA", "PID 5")
          and has_warn(rb, "CNRB_INERTIA", "PID 20") and has_warn(rb, "IMPORT_LOSS"), str(rb["warnings"]))
    check("PART_INERTIA 파트 요소는 껍질에 없다(bbox x ≤ 1)", rb["bbox"]["max"][0] <= 1.0 + 1e-12, str(rb["bbox"]))

    print("[2c] 원문 *MAT 밀도: *MAT_024(리더 미해석)·*MAT_GENERAL_VISCOELASTIC(GetRho 0)·*PART_COMPOSITE 층 밀도")
    nodes, elems = {}, []
    for k, x in enumerate((0, 3, 9)):
        nd, cn = cube(10 * k + 1, (x, 0, 0))
        nodes.update(nd)
        elems.append((k + 1 if k < 2 else 4, k + 1 if k < 2 else 4, cn))
    nodes.update({41: (6, 0, 0), 42: (7, 0, 0), 43: (7, 1, 0), 44: (6, 1, 0)})
    text = kdeck(kw_part(1, 1, 2), ["*SECTION_SOLID", f10(1, 1)], ["*MAT_024", f10(2, "2.7000E-09", "70000.0", "0.33", "200.0"),
                                                                     f10(0, 0, 0, 0, 0), f10(*[0.0] * 8), f10(*[0.0] * 8)],
                 kw_part(2, 1, 3), ["*MAT_GENERAL_VISCOELASTIC", f10(3, "1.2000E-09", "3000.0"), f10(0, 0), f10(100.0, 10.0)],
                 kw_mat(1, RHO), ["*PART_COMPOSITE", "laminate", f10(3, 2), f10(1, 0.1, 0.0, "", 2, 0.3, 0.0, "")],
                 kw_part(4, 1, 99), kw_nodes(nodes), kw_solids(elems), ["*ELEMENT_SHELL", f"{3:8d}{3:8d}{41:8d}{42:8d}{43:8d}{44:8d}"])
    imp, _ = load("raw_density", text)
    rb, _ = compute(imp)
    check("재질이 어디에도 없는 파트 4: 질량 0 + DENSITY_ZERO", part_of(rb, 4)["mass"] == 0 and has_warn(rb, "DENSITY_ZERO", "PID 4"),
          str(rb["warnings"]))
    check("*MAT_024 육면체 질량 = 2.7e-9 (원문 RO)", rel(part_of(rb, 1)["mass"], 2.7e-9) < 1e-12, str(part_of(rb, 1)))
    check("*MAT_GENERAL_VISCOELASTIC 육면체 질량 = 1.2e-9 (원문 RO)", rel(part_of(rb, 2)["mass"], 1.2e-9) < 1e-12, str(part_of(rb, 2)))
    check("*PART_COMPOSITE 셸 질량 = Σρᵢtᵢ·A", rel(part_of(rb, 3)["mass"], RHO * 0.1 + 2.7e-9 * 0.3) < 1e-12, str(part_of(rb, 3)))
    check("DENSITY_RAW 경고 MID 2·3", has_warn(rb, "DENSITY_RAW", "MID 2") and has_warn(rb, "DENSITY_RAW", "MID 3"), str(rb["warnings"]))


def test_exclusion_units():
    print("[3a] 제외: SPC 절점 하나·*MAT_RIGID CMO=1 CON1=7·ExcludePart, 회전 구속·회전 SPC 는 넣는다")
    si = 7850.0                                  # 바닥판에 SI 밀도 — 제외 전 중앙값이면 단위를 잘못 본다
    nodes, elems = {}, []
    spec = [(1, (0, 0, 10), RHO), (2, (0, 0, -2), si), (3, (3, 0, -2), si), (4, (3, 0, 10), RHO), (5, (6, 0, -2), si), (6, (6, 0, 10), RHO)]
    for pid, o, _ in spec:
        nd, cn = cube(10 * pid + 1, o)
        nodes.update(nd)
        elems.append((pid, pid, cn))
    secs = []
    for pid, _, rho in spec:
        secs += kw_part(pid, 1, pid) + (kw_mat(pid, rho) if pid not in (3, 4) else [])
    secs += ["*SECTION_SOLID", f10(1, 1)]
    secs += ["*MAT_RIGID", f10(3, f"{si:.4E}", "2.1E+11", "0.3"), f10(1.0, 7, 7), ""]
    secs += ["*MAT_RIGID", f10(4, f"{RHO:.4E}", "210000.0", "0.3"), f10(1.0, 0, 7), ""]
    text = kdeck(secs, kw_nodes(nodes), kw_solids(elems), ["*BOUNDARY_SPC_NODE", f10(21, 0, 1, 1, 1, 0, 0, 0)],
                 ["*SET_NODE_LIST", f10(60), f10(61, 62)], ["*BOUNDARY_SPC_SET_ID", f10(1, "rotonly"), f10(60, 0, 0, 0, 0, 1, 1, 1)],
                 ["*BOUNDARY_SPC_SET", f10(77, 0, 1, 1, 1)],
                 ["*BOUNDARY_PRESCRIBED_MOTION_RIGID", f10(4, 3, 0, 1)],
                 ["*ELEMENT_MASS", f"{901:8d}{22:8d}{1.0:16.6e}", f"{902:8d}{11:8d}{RHO:16.6e}"])
    imp, _ = load("exclusion", text)
    rb, logs = compute(imp, exclude_pids=[5, 999])
    ex = {x["pid"]: x["reason"] for x in rb["excluded_parts"]}
    check("뺀 파트 2(SPC 1/8)·3(MAT_RIGID)·5(ExcludePart)", sorted(ex) == [2, 3, 5] and "BOUNDARY_SPC 1/8" in ex[2]
          and "MAT_RIGID CMO=1 CON1=7" in ex[3] and "user ExcludePart" in ex[5], str(ex))
    check("넣은 파트 1·4(회전 구속)·6(회전 SPC)", sorted(p["pid"] for p in rb["parts"]) == [1, 4, 6])
    items = [cube_body(RHO, o) for pid, o, _ in spec if pid in (1, 4, 6)] + [point_body(RHO, nodes[11])]
    check_body("남은 질량 = 육면체 셋 + 절점 질량(바닥 절점의 1.0 은 뺌)", rb, combine(items), 1e-11)
    check("단위는 제외 뒤 중앙값으로 mm-t-s", rb["units"]["name"] == "mm-t-s", str(rb["units"]))
    check("경고: ROTATION_CONSTRAINT 4·PRESCRIBED_MOTION 4·EXCLUDE_UNKNOWN_PID 999·SPC_SET_MISSING 77",
          has_warn(rb, "ROTATION_CONSTRAINT", "PID 4") and has_warn(rb, "PRESCRIBED_MOTION", "PID 4")
          and has_warn(rb, "EXCLUDE_UNKNOWN_PID", "999") and has_warn(rb, "SPC_SET_MISSING", "77"), str(rb["warnings"]))
    check("로그 EXCLUDE 줄 셋 (영어 표지)", sum(x.startswith("[RigidBody] EXCLUDE pid=") for x in logs) == 3, "\n".join(logs))
    check("excluded_parts 에 뺀 질량", abs(next(x for x in rb["excluded_parts"] if x["pid"] == 2)["mass"] - si) < 1e-6)

    print("[3b] 단위 판정 (밀도 중앙값) · Units 지정 · 판정 불가")
    from KooCAEManager.KooRigidBodyProperties import UNIT_SYSTEMS
    nodes, conn = cube(1, (0, 0, 0))
    for rho, want in ((7.85e-9, "mm-t-s"), (7.85e-6, "mm-kg-ms"), (7.85e-3, "mm-g-ms"), (7850.0, "m-kg-s"), (7.85, None)):
        imp, _ = load("units", kdeck(solid_part(1, rho), kw_nodes(nodes), kw_solids([(1, 1, conn)])))
        if want:
            rb, _ = compute(imp)
            u = UNIT_SYSTEMS[want]
            check(f"ρ={rho:g} → {want}, SI 질량 = ρ·mass_to_kg", rb["units"]["name"] == want
                  and rel(rb["si"]["mass_kg"], rho * u["mass_to_kg"]) < 1e-12, str(rb["units"]))
        else:
            try:
                compute(imp)
                ok = False
            except ValueError as e:
                ok = "cannot detect units" in str(e)
            check("ρ=7.85 (g/cm³ 꼴) → ValueError", ok)
            rb, _ = compute(imp, units="mm-g-ms")
            check("Units 를 주면 그 값(source=user)", rb["units"]["name"] == "mm-g-ms" and rb["units"]["source"] == "user")
            try:
                compute(imp, units="cgs")
                ok = False
            except ValueError:
                ok = True
            check("모르는 Units 이름 → ValueError", ok)


# ── [4] 실제 덱 ──────────────────────────────────────────────────────────────
def part_size(part):
    pts = np.array([[n.x, n.y, n.z] for e in part.elementManager.elements.values() for n in e.nodes])
    return float(np.linalg.norm(pts.max(0) - pts.min(0)))


def importer_snapshot(imp):
    raw = imp.dynaManager._raw_keyword_dict
    return (len(raw), sum(len(b) for v in raw.values() for b in v if isinstance(b, list)), len(imp.partManager.parts),
            sum(len(p.elementManager.elements) for p in imp.partManager.parts.values()), len(imp.nodeManager.nodes))


def test_minimum():
    print("[4a] MinimumModel.k ↔ d3hsp (파트 1~22, 기준 실행은 DropSet 좌표 = MinimumModel − (35.5, 73.5, 4.5))")
    if not (MINIMUM.exists() and MIN_D3HSP.exists()):
        print("  SKIP MinimumModel 또는 d3hsp 없음")
        return None
    t0 = time.time()
    imp, _ = load("minimum", src=MINIMUM)
    t1 = time.time()
    before = importer_snapshot(imp)
    rb, _ = compute(imp)
    t2 = time.time()
    print("  읽기 %.1f s · 계산 %.2f s · 프로세스 최대 RSS %.0f MB" % (t1 - t0, t2 - t1, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024))
    check("리더 상태 그대로(원문 블록·파트·요소·절점 수)", importer_snapshot(imp) == before)
    ref = read_d3hsp(MIN_D3HSP)
    check("경고 없음, 제외 없음, 파트 22, mm-t-s", not rb["warnings"] and not rb["excluded_parts"] and len(rb["parts"]) == 22
          and rb["units"]["name"] == "mm-t-s", str(rb["warnings"]))
    em = ec = ecl = el = 0.0
    fine, coarse = 0.0, []
    print("    PID  요소   질량오차  무게중심오차/크기(연속체·집중)  관성오차(연속체·집중)")
    for p in rb["parts"]:
        rm, rc, ri = ref[p["pid"]]
        part = imp.partManager.parts[p["pid"]]
        size = part_size(part)
        lm = lumped(part, p["rho"])
        e_m, e_c = abs(p["mass"] / rm - 1), np.linalg.norm(p["com"] - DROPSET_SHIFT - rc) / size
        e_cl = np.linalg.norm(lm[1] - DROPSET_SHIFT - rc) / size
        sc = np.abs(np.diag(ri)).max()
        e_i = np.abs(np.diag(p["inertia_com"]) - np.diag(ri)).max() / sc
        e_l = np.abs(np.diag(lm[2]) - np.diag(ri)).max() / sc
        print("    %3d %6d   %.1e    %.1e · %.1e                %.2e · %.1e" % (p["pid"], p["n_elements"], e_m, e_c, e_cl, e_i, e_l))
        em, ec, ecl, el = max(em, e_m), max(ec, e_c), max(ecl, e_cl), max(el, e_l)
        if p["n_elements"] >= 300:
            fine = max(fine, e_i)
        else:
            coarse.append(e_i)
    check(f"파트 질량 d3hsp 와 0.1% 안 (최대 {em:.1e})", em < 1e-3)
    check(f"파트 무게중심 d3hsp 와 파트 크기의 0.1% 안 (최대 {ec:.1e})", ec < 1e-3)
    check(f"집중 질량 무게중심 = d3hsp (출력 자릿수, 최대 {ecl:.1e} × 크기)", ecl < 1e-6)
    check(f"집중 질량으로 다시 잰 파트 관성 = d3hsp (출력 4자리, 최대 {el:.1e})", el < 1e-3)
    check(f"연속체 관성: 요소 300개 이상 파트 0.5% 안 (최대 {fine:.2e}); 거친 칩 파트 최대 {max(coarse):.0%}", fine < 5e-3)
    tot = combine([ref[p] for p in range(1, 23)])
    e_tot = np.abs(np.diag(rb["inertia_com"]) / np.diag(tot[2]) - 1)
    print("    전체: 질량 %.8e (기준 %.8e) 무게중심 %s 관성 대각 %s (기준 %s)" % (
        rb["mass"], tot[0], np.round(rb["com"] - DROPSET_SHIFT, 5), np.round(np.diag(rb["inertia_com"]), 6), np.round(np.diag(tot[2]), 6)))
    check(f"전체 질량 180.318 g 의 0.1% 안 ({rb['mass'] * 1e6:.3f} g)", abs(rb["mass"] / 1.80318e-4 - 1) < 1e-3)
    check("전체 무게중심(평행축으로 합친 d3hsp)과 1e-4 mm 안", np.abs(rb["com"] - DROPSET_SHIFT - tot[1]).max() < 1e-4)
    check(f"전체 관성 대각 0.5% 안 (오차 {np.array2string(e_tot, precision=5)})", e_tot.max() < 5e-3)

    print("[4a'] OBJ·JSON 쓰고 다시 열기")
    from KooCAEManager.KooRigidBodyProperties import write_obj, write_rigid_body_json
    out = WORK / "minimum"
    s, h = rb["surface"], rb["hull"]
    write_obj(out / "MinimumModel_surface.obj", s["vertices"], s["faces"], s["groups"], header="surface of MinimumModel")
    write_obj(out / "MinimumModel_hull.obj", h["vertices"], h["faces"], header=["convex hull", "deck units"])
    write_rigid_body_json(out / "MinimumModel_rigidbody.json", rb)
    v, f, g = read_obj(out / "MinimumModel_surface.obj")
    check("외곽면 OBJ: v·f 수, 번호 1..nv, 묶음 22, 좌표 그대로", len(v) == len(s["vertices"]) and len(f) == s["n_triangles"]
          and f.min() == 1 and f.max() == len(v) and len(g) == 22 and np.allclose(v, s["vertices"], rtol=1e-9, atol=1e-9))
    hv, hf, _ = read_obj(out / "MinimumModel_hull.obj")
    check("껍질 OBJ: v·f 수, 번호 1..nv", len(hv) == h["n_vertices"] and len(hf) == len(h["faces"]) and hf.min() == 1 and hf.max() == len(hv))
    try:
        import trimesh
    except ImportError:
        trimesh = None
        print("  SKIP trimesh 없음 — 닫힘 검사 건너뜀")
    if trimesh is not None:
        hm = trimesh.Trimesh(hv, hf - 1, process=False)
        check("껍질: 닫힘·볼록·부피 일치", hm.is_watertight and hm.is_convex and rel(hm.volume, h["volume"]) < 1e-9, str(hm.volume))
        vols, bad = {p["pid"]: p["volume"] for p in rb["parts"]}, []
        for name, idx in s["groups"]:
            mm = trimesh.Trimesh(s["vertices"], s["faces"][idx], process=False)
            mm.remove_unreferenced_vertices()
            if not (mm.is_watertight and mm.is_winding_consistent and rel(mm.volume, vols[int(name.split("_")[1])]) < 1e-9):
                bad.append(name)
        check("파트 외곽면 22개 모두 닫힘·바깥 향함·둘러싼 부피 = 요소 부피", not bad, str(bad))
    j = json.loads((out / "MinimumModel_rigidbody.json").read_text(encoding="utf-8"))
    check("JSON: 질량·단위·파트 22, 배열(껍질·외곽면·SI 껍질) 빠짐", rel(j["mass"], rb["mass"]) < 1e-15 and j["units"]["name"] == "mm-t-s"
          and len(j["parts"]) == 22 and "vertices" not in j["hull"] and "faces" not in j["surface"]
          and "hull_vertices_m" not in j["si"] and j["surface"]["n_triangles"] == s["n_triangles"])
    keep = {"mass": rb["mass"], "com": rb["com"], "inertia": rb["inertia_com"], "node": imp.nodeManager.nodes[11946]}
    keep["node"] = np.array([keep["node"].x, keep["node"].y, keep["node"].z])
    del imp, rb
    gc.collect()
    return keep


def test_dropset(mini):
    print("[4b] DropSet.k: 바닥판 파트 23(SI 밀도 7850, 아랫면 SPC) 자동 제외 → MinimumModel 과 같아야")
    if not DROPSET.exists():
        print("  SKIP DropSet.k 없음")
        return
    imp, _ = load("dropset", src=DROPSET)
    rb, logs = compute(imp)
    ex = rb["excluded_parts"]
    check("파트 23 만 빠짐(BOUNDARY_SPC, 절점 일부만 묶임)", [x["pid"] for x in ex] == [23] and "BOUNDARY_SPC" in ex[0]["reason"], str(ex))
    check("로그 '[RigidBody] EXCLUDE pid=23 … reason=BOUNDARY_SPC'", any(x.startswith("[RigidBody] EXCLUDE pid=23 ")
                                                                       and "reason=BOUNDARY_SPC" in x for x in logs), "\n".join(logs))
    check("단위 mm-t-s (제외 뒤 중앙값)", rb["units"]["name"] == "mm-t-s")
    if DROPSET_D3HSP.exists():
        ref = read_d3hsp(DROPSET_D3HSP)
        e = max(abs(p["mass"] / ref[p["pid"]][0] - 1) for p in rb["parts"])
        ec = max(np.linalg.norm(p["com"] - ref[p["pid"]][1]) / part_size(imp.partManager.parts[p["pid"]]) for p in rb["parts"])
        check(f"자체 d3hsp: 파트 질량·무게중심(파트 크기 대비) 0.1% 안 (최대 {e:.1e}, {ec:.1e})", e < 1e-3 and ec < 1e-3)
    if mini is not None:
        node = imp.nodeManager.nodes[11946]
        check("덱 이동량 = (35.5, 73.5, 4.5) (절점 11946)", np.allclose(mini["node"] - [node.x, node.y, node.z], DROPSET_SHIFT, atol=1e-9))
        check("질량·관성 = MinimumModel (1e-9), 무게중심 = MinimumModel − 이동량",
              rel(rb["mass"], mini["mass"]) < 1e-9 and rel(rb["inertia_com"], mini["inertia"]) < 1e-9
              and np.abs(rb["com"] + DROPSET_SHIFT - mini["com"]).max() < 1e-9,
              f"{rb['mass']} {mini['mass']} {rb['com']} {mini['com']}")
    del imp, rb
    gc.collect()


def test_simpledrop():
    print("[4c] SimpleDrop case01 (mm-kg-ms) ↔ Radioss 시작 출력, 바닥 PID 3 자동 제외")
    if not (SIMPLE.exists() and SIMPLE_OUT.exists()):
        print("  SKIP SimpleDrop 없음")
        return
    imp, _ = load("simpledrop", src=SIMPLE)
    rb, _ = compute(imp)
    ref = read_radioss(SIMPLE_OUT)
    ex = rb["excluded_parts"]
    check("PID 3 Rigid_Floor 제외(SPC 셋 100 + MAT_RIGID CON1=7), mm-kg-ms", [x["pid"] for x in ex] == [3]
          and "BOUNDARY_SPC 242/242" in ex[0]["reason"] and "MAT_RIGID" in ex[0]["reason"] and rb["units"]["name"] == "mm-kg-ms", str(ex))
    for pid in (1, 2):
        p, (rm, rc, ri) = part_of(rb, pid), ref[pid]
        lm = lumped(imp.partManager.parts[pid], p["rho"])
        e_c = np.abs(np.diag(p["inertia_com"]) / ri - 1)
        print(f"    PID {pid} {p['name']}: 질량 {p['mass'] * 1e3:.4f} g  무게중심 {np.round(p['com'], 4)}  "
              f"관성 연속체 {np.round(np.diag(p['inertia_com']), 3)} / 집중 {np.round(np.diag(lm[2]), 3)} / Radioss {ri} kg·mm²")
        check(f"PID {pid}: 질량·무게중심 = Radioss (1e-8)", rel(p["mass"], rm) < 1e-8 and np.abs(p["com"] - rc).max() < 1e-6)
        check(f"PID {pid}: 집중 질량 관성 = Radioss (1e-6)", rel(np.diag(lm[2]), ri) < 1e-6)
        check(f"PID {pid}: 연속체 관성은 Radioss 보다 작고 1.5% 안 ({np.array2string(e_c, precision=4)})",
              (np.diag(p["inertia_com"]) < ri).all() and e_c.max() < 1.5e-2)
    tot = combine([(ref[p][0], ref[p][1], np.diag(ref[p][2])) for p in (1, 2)])
    e = np.diag(rb["inertia_com"]) / np.diag(tot[2]) - 1
    print("    기기 합: 질량 %.3f g (Radioss 합 %.3f) 무게중심 z %.4f (%.4f) 관성 %s (Radioss 합 %s) 오차 %s" % (
        rb["mass"] * 1e3, tot[0] * 1e3, rb["com"][2], tot[1][2], np.round(np.diag(rb["inertia_com"]), 2),
        np.round(np.diag(tot[2]), 2), np.array2string(e, precision=4)))
    check("기기 질량 219.7 g·무게중심 = Radioss 합", abs(rb["mass"] * 1e3 - 219.72) < 0.01 and np.abs(rb["com"] - tot[1]).max() < 1e-6)
    check("기기 관성(연속체) Radioss 합(집중)과 1.5% 안", np.abs(e).max() < 1.5e-2)
    del imp, rb
    gc.collect()


def test_toy():
    print("[4d] 경계 장난감 덱 (hex·TSHELL·PART_COMPOSITE_TSHELL·DISCRETE·SEATBELT·*ELEMENT_MASS·요소 없는 *PART_INERTIA)")
    if not TOY.exists():
        print("  SKIP 장난감 덱 없음")
        return
    imp, _ = load("toy", src=TOY)
    rb, _ = compute(imp)
    want = 2 * RHO + 1 * RHO + 1e-3 + 2e-6        # 육면체 2 mm³·TSHELL 1 mm³·절점 질량 0.001·PART_INERTIA 둘
    check(f"질량 = 육면체 + TSHELL + 절점 질량 + PART_INERTIA 둘 ({want:.7e})", rel(rb["mass"], want) < 1e-12, str(rb["mass"]))
    check("경고: PART_INERTIA 8·9, ELEMENT_SEATBELT, TSHELL PID 5(PART_COMPOSITE_TSHELL), 무게중심 껍질 밖",
          has_warn(rb, "PART_INERTIA", "PID 8") and has_warn(rb, "PART_INERTIA", "PID 9")
          and has_warn(rb, "UNREAD_ELEMENTS", "ELEMENT_SEATBELT") and has_warn(rb, "UNREAD_ELEMENTS", "PID [5]")
          and has_warn(rb, "COM_OUTSIDE_HULL"), "\n".join(rb["warnings"]))
    check("ELEMENT_DISCRETE(질량 없음)는 경고하지 않는다", not any("ELEMENT_DISCRETE" in w for w in rb["warnings"]))
    check("요소 없는 파트 6·7 은 질량 0·무게중심 None", part_of(rb, 6)["mass"] == 0 and part_of(rb, 6)["com"] is None)
    del imp, rb
    gc.collect()


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    test_small_solids()
    test_small_shells_beams_points()
    test_raw_keywords()
    test_exclusion_units()
    mini = test_minimum()
    test_dropset(mini)
    test_simpledrop()
    test_toy()
    print("\n시간 %.0f s · 최대 RSS %.0f MB" % (time.time() - t0, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024))
    if FAILS:
        print("FAIL %d 건" % len(FAILS))
        for x in FAILS:
            print("  -", x)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
