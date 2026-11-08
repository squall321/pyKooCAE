# 강체 낙하 사전 해석 엔진(KooRigidDropPresim)의 껍질 충실도·프로토타입 수치·규약·표 줄·충돌 직전 상태를 검증하는 시험
"""
실행: venv312/bin/python tests/test_rigid_drop_presim.py   (pybullet 필요, 약 2분, 프로세스 ≤ 4)

기준값은 프로토타입 /home/koopark/kooOmniDropAnalyzer/fullangle_mbd (PyBullet GEOM_BOX 150×75×7.5 mm, 200 g, μ 0.5)의
저장 결과(results_mu0.5, tilt45_sensitivity.csv, six_face_exact.csv)다. 전체 측정은 /data/koopark/Test_RigidDropEndtime/B 에 있다.
프로토타입 대조는 프로토타입 규칙(2차 이격 0.3 ms)으로 하고, 엔진 기본(1 ms, 사용자 결정 11-07)은 [11] 에서 따로 본다.
v133 중력 끔 규칙(마지막 강한 재접촉, strong_contact 기본 0.2 — 상자 수용 대조는 기준 csv 가 있는 0.3)은 [15] 에서 본다. v132 규칙을 보는 [7]·[11]·[12] 는
strong_contact=None 으로 v132 규칙을 고정하고, v133 기대값을 옆에 둔다.
[15] 의 v132 비트 동일 대조는 git 의 v132 엔진(V132_COMMIT)과 하고, 수용 대조 기준은 멈춤 없이 끝까지 돌린
endtime_rule_check.csv(REF_V133, 칸 last>=0.3)다. 둘 다 없으면 그 대조만 SKIP 한다.
"""
import csv
import importlib.util
import inspect
import math
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(GEN))

from KooCAEManager import KooRigidDropPresim as P  # noqa: E402
from KooCAEManager.KooEndTimeTable import (CORE_COLUMNS, drop_direction, euler_from_direction,  # noqa: E402
                                           fibonacci_angles, load_lookup, read_endtime_table, rotation_from_euler,
                                           write_endtime_table)

FAILS = []
MASS, SIZE, H, MU, ES = 0.200, (0.150, 0.075, 0.0075), 1.5, 0.5, (0.1, 0.3, 0.5)
HALF = np.array(SIZE) / 2.0
CORNERS = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]) * HALF
IMPACT_KEYS = ["name", "roll", "pitch", "yaw", "e", "k", "class", "t_start_ms", "t_end_ms", "J_over_mv0",
               "contact_x", "contact_y", "contact_z", "contact_type", "nx", "ny", "nz", "att_roll", "att_pitch",
               "att_yaw", "vx", "vy", "vz", "wx", "wy", "wz", "vn_contact", "v0", "tfinal_k_ms"]
# 프로토타입 results_mu0.5 (피보나치 1000 중 10방향) — e 0.1/0.3/0.5 마다 (분류, t2_end ms)
PROTO_REF = {50: [("slapdown", 3.17), ("slapdown", 3.23), ("slapdown", 3.29)],
             150: [("slapdown", 1.28), ("slapdown", 1.39), ("slapdown", 1.53)],
             250: [("slapdown", 10.28), ("slapdown", 10.47), ("slapdown", 10.70)],
             350: [("slapdown", 61.97), ("rebound", 187.13), ("rebound", 365.77)],
             450: [("rebound", 122.46), ("rebound", 350.48), ("rebound", 558.96)],
             550: [("slapdown", 3.11), ("slapdown", 3.02), ("slapdown", 2.94)],
             650: [("slapdown", 17.12), ("rebound", 187.66), ("rebound", 375.59)],
             750: [("slapdown", 14.88), ("slapdown", 15.76), ("slapdown", 16.92)],
             850: [("slapdown", 14.00), ("slapdown", 13.25), ("slapdown", 12.61)],
             950: [("slapdown", 2.75), ("slapdown", 2.89), ("slapdown", 3.06)]}
# 프로토타입 tilt45_sensitivity.csv (μ 0.5): 45° 짧은 모서리 t2_start ms, 2차 접촉 속도/v0
PROTO_45 = {0.1: (17.44, 1.1718), 0.3: (16.76, 1.1708), 0.5: (16.17, 1.1334)}
# v133: v132 엔진의 마지막 커밋(비트 동일 대조 기준), 멈춤 없이 끝까지 돌린 방향별 기준 tFinal(피보나치 1000, 중력 끔, μ 0.5)
V132_COMMIT = "6504b11"
REF_V133 = "/home/koopark/kooOmniDropAnalyzer/fullangle_mbd/results_v132_mu0.5/endtime_rule_check.csv"
NEW_KEYS = ["strong_end_ms", "strong_vn_max"]
# calm 건전성 표본(피보나치 1000 번호) — 상자는 440·457 의 e 0.5(clear)만 빼고 calm 으로 멈춘다(0·1·440·457 은 강한 재접촉 없음).
# 여기에 e 0.9(강한 재접촉 뒤 calm — 상자·막대·치우친 폰)와, 옛 한계(ω_max·r_max)로는 t_max 까지 가던 긴 막대 e 0.1 을 더한다.
# 긴 막대는 문턱 0.3 으로 본다 — 기본 0.2 에서는 55·155 의 남은 회전이 0.2·v0 아래로 못 내려가 꼭짓점별 한계로도 t_max 다
SOUND_IDX = (0, 1, 13, 15, 20, 37, 440, 457, 850)
SOUND_E09 = (("box", 605), ("box", 905), ("rod", 155), ("rod", 855), ("offset", 305), ("offset", 805))
SOUND_ROD = (55, 155, 380)


def check(name, cond, detail=""):
    print("  %-70s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def box_inertia(mass=MASS, size=SIZE):
    lx, ly, lz = size
    return np.diag([mass / 12.0 * (ly * ly + lz * lz), mass / 12.0 * (lx * lx + lz * lz), mass / 12.0 * (lx * lx + ly * ly)])


def proto_fibonacci(n):
    """프로토타입 fibonacci_sphere (위상 i+0.5) — PROTO_REF 의 방향."""
    i = np.arange(n) + 0.5
    z = 1.0 - 2.0 * i / n
    r = np.sqrt(1.0 - z * z)
    phi = i * math.pi * (3.0 - math.sqrt(5.0))
    return np.stack([r * np.cos(phi), r * np.sin(phi), z], axis=1)


def rotz(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def rot_axis(axis, deg):
    """축 axis 둘레 deg 회전 (로드리게스)."""
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    K = np.array([[0.0, -a[2], a[1]], [a[2], 0.0, -a[0]], [-a[1], a[0], 0.0]])
    return np.eye(3) + math.sin(math.radians(deg)) * K + (1.0 - math.cos(math.radians(deg))) * K @ K


def _ref_job(args):
    idx, e = args
    r = P.simulate_drop(BOX, proto_fibonacci(1000)[idx], e, MU, H)
    return idx, e, P.second_impact(r["events"], 0.3)


def _face_job(d):
    out = []
    for e in ES:
        r = P.simulate_drop(BOX, d, e, MU, H)
        t2s, t2e, cls, t1e = P.second_impact(r["events"], 0.3)
        out.append((cls, P.tfinal_ms(t2e, cls, t1e)))
    return out


def tf_strong(st, margin_ms=1.0):
    """strong_from_events 결과 → v133 tFinal (마지막 강한 재접촉 묶음 끝, 없으면 1차 묶음 끝) + 여유."""
    return (st[0] if math.isnan(st[1]) else st[1]) + margin_ms


def _sound_job(args):
    """calm 건전성: v133(calm 켬) 과 calm 을 끈 v133 실행(멈춤은 clear·t_max·이벤트 400 만)의 이벤트·tFinal."""
    bkey, idx, e, thr = args
    body, d = SOUND_BODIES[bkey], proto_fibonacci(1000)[idx]
    r = P.simulate_drop(body, d, e, MU, H, gravity_on=False, strong_vn=thr)
    old = P.CALM_EVERY, P.MAX_EVENTS_FULL
    P.CALM_EVERY, P.MAX_EVENTS_FULL = 10 ** 9, 400  # calm 끔 — fork 작업자 안에서만 바꾸고 되돌린다
    try:
        ref = P.simulate_drop(body, d, e, MU, H, gravity_on=False, strong_vn=thr)
    finally:
        P.CALM_EVERY, P.MAX_EVENTS_FULL = old
    key = lambda evs: [(x["t_start_ms"], x["t_end_ms"], x["J"], x["approach_max_mps"]) for x in evs]  # noqa: E731
    prefix = key(r["events"]) == key(ref["events"])[:len(r["events"])]
    return (bkey, idx, e, r["stop"], ref["stop"], P.strong_from_events(r["events"], r["v0"], thr),
            P.strong_from_events(ref["events"], ref["v0"], thr), prefix)


def same_value(a, b):
    """비트 동일 비교 — nan 은 nan 과 같다고 본다."""
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    return a == b


def same_as_v132(new_rows, old_rows):
    """v133 표 줄이 v132 줄과 같다: v132 칸은 차례·값이 비트까지 같고, 새 칸(strong_*)은 모두 nan."""
    for a, b in zip(new_rows, old_rows):
        if [k for k in a if k in b] != list(b) or not all(same_value(a[k], b[k]) for k in b):
            return False
        extra = [k for k in a if k not in b]
        if sorted(extra) != sorted(NEW_KEYS + [f"strong_end_ms_e{e}" for e in ES]) or not all(math.isnan(a[k]) for k in extra):
            return False
    return len(new_rows) == len(old_rows)


def load_v132():
    """git 의 v132 엔진(V132_COMMIT)을 이름 있는 모듈로 읽는다(fork 작업자에 _job 을 넘기려면 이름으로 찾아져야 한다). 없으면 None."""
    rel = "occProject/Generators/KooCAEManager/KooRigidDropPresim.py"
    try:
        src = subprocess.run(["git", "-C", str(ROOT), "show", f"{V132_COMMIT}:{rel}"], capture_output=True, text=True,
                             check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "KooRigidDropPresim_v132.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        spec = importlib.util.spec_from_file_location("KooRigidDropPresim_v132", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    return mod


BOX = P.make_body(MASS, (0.0, 0.0, 0.0), box_inertia(), CORNERS)
# 긴 막대 200×30×20 mm, 150 g — calm 한계의 꼭짓점별 상수가 r_max/√I_min 의 0.25 배
ROD_SIZE = (0.200, 0.030, 0.020)
ROD = P.make_body(0.150, (0.0, 0.0, 0.0), box_inertia(0.150, ROD_SIZE), CORNERS / HALF * (np.array(ROD_SIZE) / 2.0))
# 무게중심이 치우치고 관성 주축이 기기 축과 20° 어긋난 폰 (껍질은 같은 상자) — R4 F2 재현 몸체
_RO = rot_axis((1, 2, 3), 20.0)
OFFSET = P.make_body(MASS, (0.030, 0.010, 0.001), _RO @ (box_inertia() @ np.diag([1.0, 1.3, 0.9])) @ _RO.T, CORNERS)
SOUND_BODIES = {"box": BOX, "rod": ROD, "offset": OFFSET}


def main():
    t_all = time.time()
    print("[0] pybullet 없이 모듈 import")
    code = ("import sys; sys.path.insert(0, %r); sys.modules['pybullet'] = None\n"
            "import KooCAEManager.KooRigidDropPresim as m\nprint('ok', m.GAP)") % str(GEN)
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    check("import works with pybullet unavailable (lazy import)", res.returncode == 0 and "ok" in res.stdout, res.stderr[-300:])

    print("[1] make_body 주축 좌표")
    check("diagonal inertia -> R = I exactly, moments = diag", np.array_equal(BOX["R"], np.eye(3))
          and np.allclose(BOX["moments"], np.diag(box_inertia()), rtol=1e-14, atol=0))
    check("r_max = half diagonal", abs(BOX["r_max"] - np.linalg.norm(HALF)) < 1e-15)
    RY = rotz(90.0)
    by = P.make_body(MASS, (0, 0, 0), RY @ box_inertia() @ RY.T, CORNERS @ RY.T)
    check("Y-long box -> R = I (no axis assumption), moments permuted",
          np.allclose(by["R"], np.eye(3), atol=1e-12) and np.allclose(by["moments"], np.diag(box_inertia())[[1, 0, 2]], rtol=1e-12))
    rng = np.random.default_rng(5)
    q = rng.normal(size=4)
    q /= np.linalg.norm(q)
    x, y, z, w = q
    Q = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    T = np.array([0.012, -0.034, 0.056])
    bq = P.make_body(MASS, T, Q @ box_inertia() @ Q.T, CORNERS @ Q.T + T)
    D = bq["R"].T @ (Q @ box_inertia() @ Q.T) @ bq["R"]
    check("rotated device: R^T I R diagonal, det R = +1", np.abs(D - np.diag(np.diag(D))).max() < 1e-15
          and abs(np.linalg.det(bq["R"]) - 1) < 1e-12)
    check("rotated device: hull in principal frame = box (half extents)",
          np.allclose(np.sort(np.abs(bq["verts"]).max(axis=0)), np.sort(HALF), atol=1e-12))

    def rot_vn_ref(b):  # 꼭짓점마다 √λ_max([r]× I⁻¹ [r]×ᵀ) — 엔진(σ_max 노름)과 다른 길로
        best = 0.0
        for r_ in b["verts"]:
            X = np.array([[0.0, -r_[2], r_[1]], [r_[2], 0.0, -r_[0]], [-r_[1], r_[0], 0.0]])
            best = max(best, float(np.linalg.eigvalsh(X @ np.diag(1.0 / b["moments"]) @ X.T).max()))
        return math.sqrt(best)
    wr = rng.normal(size=(2000, 3)) * 50.0  # 아무 각속도(주축 좌표): 꼭짓점 회전 속도 |ω × r| ≤ √(2T)·rot_vn_k
    vmax_ratio = max(float((np.linalg.norm(np.cross(w_, b["verts"]), axis=1).max()
                            / math.sqrt(w_ @ (b["moments"] * w_))) / b["rot_vn_k"]) for b in (BOX, bq, ROD) for w_ in wr)
    check("calm constant rot_vn_k = max_i sigma_max([r_i]x I^-1/2) (box, rotated, rod); |w x r| <= sqrt(2T) rot_vn_k; "
          "rod 0.25x, box 0.63x of r_max/sqrt(I_min)",
          all(abs(b["rot_vn_k"] / rot_vn_ref(b) - 1.0) < 1e-12 for b in (BOX, bq, ROD)) and vmax_ratio <= 1.0 + 1e-12
          and abs(ROD["rot_vn_k"] * math.sqrt(ROD["moments"].min()) / ROD["r_max"] - 0.250) < 1e-3
          and abs(BOX["rot_vn_k"] * math.sqrt(BOX["moments"].min()) / BOX["r_max"] - 0.634) < 1e-3,
          f"{[b['rot_vn_k'] / rot_vn_ref(b) for b in (BOX, bq, ROD)]} {vmax_ratio}")
    for label, args in (("mass 0", (0.0, (0, 0, 0), box_inertia(), CORNERS)),
                        ("non-PD inertia", (MASS, (0, 0, 0), np.diag([1e-4, -1e-4, 1e-4]), CORNERS)),
                        ("coplanar hull", (MASS, (0, 0, 0), box_inertia(), CORNERS * [1, 1, 0])),
                        ("> 131072 vertices", (MASS, (0, 0, 0), box_inertia(), rng.normal(size=(131073, 3))))):
        try:
            P.make_body(*args)
            check(f"make_body rejects {label}", False)
        except ValueError:
            check(f"make_body rejects {label}", True)

    print("[2] 볼록 껍질 여유(collision margin) — 형상 그대로")
    import pybullet as pb
    cid = pb.connect(pb.DIRECT)
    plane = pb.createMultiBody(0, pb.createCollisionShape(pb.GEOM_PLANE, physicsClientId=cid), physicsClientId=cid)
    hull = pb.createMultiBody(MASS, pb.createCollisionShape(pb.GEOM_MESH, vertices=CORNERS.tolist(), physicsClientId=cid),
                              basePosition=[0, 0, HALF[2] + 0.005], physicsClientId=cid)
    d_def = min(c[8] for c in pb.getClosestPoints(hull, plane, 0.05, physicsClientId=cid))
    pb.changeDynamics(hull, -1, collisionMargin=0.0, physicsClientId=cid)
    d_zero = min(c[8] for c in pb.getClosestPoints(hull, plane, 0.05, physicsClientId=cid))
    pb.disconnect(cid)
    check("pybullet GEOM_MESH hull default margin inflates by 1 mm", abs((0.005 - d_def) - 1e-3) < 1e-9, f"{d_def}")
    check("collisionMargin=0 -> exact geometry (gap 5 mm reported 5 mm)", abs(d_zero - 0.005) < 1e-12, f"{d_zero}")
    r = P.simulate_drop(BOX, (0, 0, -1), 0.3, MU, H)
    check("first contact at GAP/v0 (+<=2 steps): 0.5 mm gap really 0.5 mm",
          P.GAP / r["v0"] <= r["t0_s"] <= P.GAP / r["v0"] + 2e-5, f"t0={r['t0_s']}")
    r = P.simulate_drop(BOX, (0, 0, -1), 0.0, MU, P.GAP + 1e-4, t_max=0.05, trace=True)
    zrest = r["trace"][-1, 2]
    check("resting CoM height = half thickness 3.75 mm within 5 µm", abs(zrest - HALF[2]) < 5e-6, f"z={zrest}")

    print("[3] 프로토타입 수치 (상자 껍질 = GEOM_BOX)")
    vals = []
    for e in ES:
        r = P.simulate_drop(BOX, (0, 0, -1), e, MU, H, t_max=0.01, trace=True)
        tr = r["trace"]
        k = int(np.argmax(tr[:, 1] > 1e-3 * MASS * r["v0"]))
        vals.append(tr[k:k + 100, 3].max() / r["v0"])
    check("flat drop restitution 0.089/0.288/0.516 (prototype) +-0.003",
          np.allclose(vals, [0.089, 0.288, 0.516], atol=3e-3), f"{np.round(vals, 4)}")
    with mp.get_context("fork").Pool(4) as pool:
        got = pool.map(_ref_job, [(i, e) for i in PROTO_REF for e in ES], chunksize=1)
    bad = []
    for i, e, si in got:
        cls_ref, t2e_ref = PROTO_REF[i][ES.index(e)]
        if si[2] != cls_ref or abs(si[1] - t2e_ref) > 0.011:  # 한 스텝(0.01 ms) + 반올림
            bad.append((i, e, si[2], si[1], cls_ref, t2e_ref))
    check("10 Fibonacci dirs x 3 e: class and t2_end = prototype results_mu0.5", not bad, f"{bad}")
    d45 = (math.sin(math.radians(45)), 0.0, -math.cos(math.radians(45)))
    for e in ES:
        r = P.simulate_drop(BOX, d45, e, MU, H)
        t2s, t2e, cls, t1e = P.second_impact(r["events"], 0.3)
        b = next(ev for ev in r["events"] if ev["t_start_ms"] == t2s)
        check(f"45° short edge e={e}: slapdown t2 {PROTO_45[e][0]} ms, vn2/v0 {PROTO_45[e][1]} (prototype)",
              cls == "slapdown" and abs(t2s - PROTO_45[e][0]) < 0.02 and abs(-b["vn_mps"] / r["v0"] - PROTO_45[e][1]) < 2e-3,
              f"{cls} {t2s} {-b['vn_mps'] / r['v0']}")
    faces = [(0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0)]
    with mp.get_context("fork").Pool(4) as pool:
        fr = pool.map(_face_job, faces)
    flat = [x for f in fr for x in f]
    check("6 exact faces x 3 e: no slapdown, tfinal = t1_end + 1 <= 1.02 ms (six_face_exact.csv)",
          all(c == "rebound" for c, _ in flat) and max(t for _, t in flat) <= 1.02, f"{flat}")
    dirs = proto_fibonacci(1000)
    for idx in (123, 870):
        a = P.second_impact(P.simulate_drop(BOX, dirs[idx], 0.3, MU, H)["events"], 0.3)
        b = P.second_impact(P.simulate_drop(BOX, dirs[idx], 0.3, MU, H, dt=1e-6)["events"], 0.3)
        check(f"dt 1e-5 vs 1e-6 idx {idx}: same class, |dt2| < 0.1 ms", a[2] == b[2] and abs(a[0] - b[0]) < 0.1, f"{a} {b}")

    print("[4] 관성·무게중심을 그대로 씀 (무마찰 꼭짓점 1점 충돌 해석해, 속도 상한 해제)")
    d = np.array([0.5, 0.3, -0.8]) / np.linalg.norm([0.5, 0.3, -0.8])
    corner = CORNERS[np.argmax(CORNERS @ d)]
    I0 = box_inertia()
    for label, com, I in (("Iyy x3", (0, 0, 0), np.diag([I0[0, 0], 3 * I0[1, 1], I0[2, 2]])),
                          ("CoM (+20,-10,+2) mm", (0.020, -0.010, 0.002), I0),
                          ("axes rotated 35 deg", (0, 0, 0), rotz(35) @ I0 @ rotz(35).T)):
        body = P.make_body(MASS, com, I, CORNERS)
        rc = corner - np.asarray(com)
        rn = np.cross(rc, -d)
        Ja = (1 + 0.3) * math.sqrt(2 * P.G * H) / (1 / MASS + rn @ np.linalg.solve(I, rn))
        wa = np.linalg.solve(I, rn) * Ja
        r = P.simulate_drop(body, d, 0.3, 0.0, H, t_max=0.002, trace=True)
        tr, ev = r["trace"], r["events"][0]
        kk = int(np.argmin(np.abs(tr[:, 0] - (r["t0_s"] + ev["t_end_ms"] * 1e-3))))
        wm = tr[kk + 1, 4:7]
        check(f"{label}: J and post-impact w = analytic (J 0.1%, w 0.5%)", abs(ev["J"] / Ja - 1) < 1e-3
              and np.linalg.norm(wm - wa) / np.linalg.norm(wa) < 5e-3, f"J {ev['J']}/{Ja} w {wm} vs {wa}")

    print("[5] second_impact · tfinal · endtim")
    ev = lambda s, e_, rise=0.0: {"t_start_ms": s, "t_end_ms": e_, "rise_mm": rise}  # noqa: E731
    check("slapdown cluster: t2_end extends through gaps < t_sep",
          P.second_impact([ev(0, 0.05), ev(0.2, 0.25), ev(3.0, 3.1), ev(3.3, 3.35), ev(9.0, 9.0)], 0.3) == (3.0, 3.35, "slapdown", 0.25))
    check("rebound when CoM rose > 1 mm", P.second_impact([ev(0, 0.01), ev(100.0, 100.0, 1.5)], 0.3)[2] == "rebound")
    check("default t_sep = 1 ms (= stop rule T_SEP_MAX) in second_impact, impact_rows, run_presim", P.T_SEP_MS == 1.0
          and all(inspect.signature(f).parameters["t_sep_ms"].default == 1.0
                  for f in (P.second_impact, P.impact_rows, P.run_presim)))
    evs = [ev(0, 0.01), ev(0.5, 0.6), ev(5.0, 5.1)]
    check("1 ms rule: a re-contact 0.49 ms later is part of the 1st cluster",
          P.second_impact(evs) == (5.0, 5.1, "slapdown", 0.6) and P.second_impact(evs, 0.3) == (0.5, 0.6, "slapdown", 0.01))
    try:
        P.run_presim(BOX, [("A", 0.0, 0.0, 0.0)], H, t_sep_ms=1.5, log=lambda s: None)
        check("run_presim rejects t_sep_ms > 1 ms (stop rule cannot capture it)", False)
    except ValueError:
        check("run_presim rejects t_sep_ms > 1 ms (stop rule cannot capture it)", True)
    t2s, t2e, cls, t1e = P.second_impact([ev(0, 0.01), ev(0.1, 0.2)], 0.3)
    check("none: t1_end = last event end (not NaN)", cls == "none" and t1e == 0.2 and math.isnan(t2s))
    check("tfinal rule: slapdown -> t2_end + 1, rebound -> t1_end + 1",
          P.tfinal_ms(3.35, "slapdown", 0.25) == 4.35 and P.tfinal_ms(100.0, "rebound", 0.01) == 1.01)
    check("gravity off (count_rebound): rebound -> t2_end + 1, none -> t1_end + 1",
          P.tfinal_ms(100.0, "rebound", 0.01, count_rebound=True) == 101.0
          and P.tfinal_ms(float("nan"), "none", 0.2, count_rebound=True) == 1.2)
    check("endtim: ceil to 0.1 ms, deck units", P.endtim_from_ms(1.01, 1.0) == 0.0011 and P.endtim_from_ms(17.76, 1e-3) == 17.8
          and P.endtim_from_ms(1.0000000000000002, 1.0) == 0.001 and P.endtim_from_ms(2.0, 1e-3) == 2.0)
    # v133 strong_from_events — 첫 접촉 vn·이벤트 안 최대 접근 속도 peak(÷ v0, 안 주면 vn 과 같게)를 가진 이벤트, v_ref = 2
    sv = lambda s, e_, vn, peak=None: {"t_start_ms": s, "t_end_ms": e_, "rise_mm": 0.0, "vn_mps": -2.0 * vn,  # noqa: E731
                                       "approach_max_mps": 2.0 * (vn if peak is None else peak)}
    evs = [sv(0, 0.4, 1.0), sv(0.9, 1.0, 0.1), sv(2.25, 2.25, 0.72), sv(3.92, 3.92, 1.86), sv(5.73, 5.8, 0.98),
           sv(6.5, 6.6, 0.05), sv(30.0, 30.0, 0.06)]
    check("strong_from_events: clusters as second_impact, last re-contact cluster with max vn >= thr, vn_max over re-contacts",
          P.strong_from_events(evs, 2.0, 0.3) == (1.0, 6.6, 1.86) and P.second_impact(evs)[3] == 1.0)
    check("strong_from_events: strength = cluster max (weak start, strong later in the cluster), >= thr counts",
          P.strong_from_events([sv(0, 0, 1.0), sv(5.0, 5.0, 0.1), sv(5.5, 5.6, 0.3), sv(9.0, 9.0, 0.2)], 2.0, 0.3)
          == (0.0, 5.6, 0.3))
    t1, se, vm = P.strong_from_events([sv(0, 0.25, 1.0), sv(1.25, 1.25, 0.29), sv(400.0, 400.0, 0.06)], 2.0, 0.3)
    check("strong_from_events: only weak re-contacts -> (t1_end, nan, max) ; gap exactly t_sep starts a new cluster",
          t1 == 0.25 and math.isnan(se) and vm == 0.29)
    t1, se, vm = P.strong_from_events([sv(0, 0.2, 1.0), sv(0.7, 0.9, 0.8)], 2.0, 0.3)
    e0 = P.strong_from_events([], 2.0, 0.3)
    check("strong_from_events: no re-contact -> (t1_end, nan, nan); no events -> all nan",
          t1 == 0.9 and math.isnan(se) and math.isnan(vm) and all(math.isnan(x) for x in e0))
    t1, se, vm = P.strong_from_events([sv(0, 0, 1.0), sv(5.0, 5.0, 0.9, 0.2)], 2.0, 0.3)  # vn_mps 는 세기에 안 쓴다
    check("strong_from_events: strength = approach_max_mps (in-event peak), not first-contact vn_mps (F2: 0.27 -> 1.215)",
          P.strong_from_events([sv(0, 0, 1.0), sv(13.64, 13.67, 0.27, 1.215)], 2.0, 0.3) == (0.0, 13.67, 1.215)
          and t1 == 0.0 and math.isnan(se) and vm == 0.2)
    check("v133 defaults: STRONG_CONTACT 0.2 (run_presim default), MAX_EVENTS_FULL 200, strong_vn default None",
          P.STRONG_CONTACT == 0.2 and P.MAX_EVENTS_FULL == 200
          and inspect.signature(P.run_presim).parameters["strong_contact"].default == P.STRONG_CONTACT
          and inspect.signature(P.simulate_drop).parameters["strong_vn"].default is None)
    bad = []
    for v in (0.0, -0.3, float("nan"), float("inf")):
        try:
            P.run_presim(BOX, [("A", 0.0, 0.0, 0.0)], H, gravity_on=False, strong_contact=v, log=lambda s: None)
            bad.append(v)
        except ValueError:
            pass
    check("run_presim rejects strong_contact 0, < 0, nan, inf (ValueError before any simulation)", not bad, f"{bad}")

    print("[6] run_presim 표 줄 (KooEndTimeTable) · 각도 규약 · 충돌 상태 줄")
    angles = fibonacci_angles(8) + [("Y1", 20.0, -35.0, 70.0)]
    rows, imps = P.run_presim(BOX, angles, H, ES, friction=MU, workers=4, time_to_s=1.0, log=lambda s: None,
                              return_impacts=True)
    # v133: strong_end_ms·strong_vn_max(지배 e)를 reach_m 뒤에, e 마다 strong_end_ms_e<e> 를 t2_end_ms_e<e> 뒤에 더한다
    per_e = [f"{c}_e{e}" for e in ES for c in ("class", "t1_end_ms", "t2_start_ms", "t2_end_ms", "strong_end_ms")]
    check("columns = CORE_COLUMNS + n_unresolved, reach_m, strong_end_ms, strong_vn_max + per-e (class/t1/t2s/t2e/strong)",
          list(rows[0]) == CORE_COLUMNS + ["n_unresolved", "reach_m"] + NEW_KEYS + per_e, f"{list(rows[0])}")
    check("gravity on: new columns strong_end_ms, strong_vn_max, strong_end_ms_e<e> are all nan (v132 rule)",
          all(math.isnan(r_[k]) for r_ in rows for k in NEW_KEYS + [f"strong_end_ms_e{e}" for e in ES]))
    ok = True
    for row, (name, rr, pp, yy) in zip(rows, angles):
        tfs = []
        for e in ES:
            c, t1, t2 = row[f"class_e{e}"], row[f"t1_end_ms_e{e}"], row[f"t2_end_ms_e{e}"]
            tfs.append(P.tfinal_ms(t2, c, t1))
        cls = [row[f"class_e{e}"] for e in ES]
        ok &= abs(row["tfinal_ms"] - max(tfs)) < 1e-12 and row["governing_e"] == ES[int(np.argmax(tfs))]
        ok &= row["class"] == ("slapdown" if "slapdown" in cls else "rebound" if "rebound" in cls else "none")
        n01 = round(row["endtim"] * 1e4)  # endtim = 0.1 ms 의 배수 가운데 tfinal 이상인 가장 작은 값 (s 덱)
        ok &= abs(row["endtim"] - n01 * 1e-4) < 1e-15 and n01 * 0.1 >= row["tfinal_ms"] - 1e-9 > (n01 - 1) * 0.1
        ok &= np.allclose([row["dx"], row["dy"], row["dz"]], drop_direction(rr, pp, yy), atol=1e-15)
    check("tfinal = max over e, governing_e, class rule, endtim (s deck), d = drop_direction", ok)
    rows_ms = P.run_presim(BOX, angles[:3], H, ES, friction=MU, workers=4, time_to_s=1e-3, log=lambda s: None)
    check("time_to_s=1e-3 (ms deck): endtim = s-deck value x 1000",
          all(abs(a["endtim"] - 1e3 * b["endtim"]) < 1e-9 for a, b in zip(rows_ms, rows[:3])))
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "MinimumModel_endtime.csv")
        write_endtime_table(path, rows, {"units": "mm-t-s", "height": 1500})
        meta, back = read_endtime_table(path)
        lk = load_lookup(path)
        check("write/read round trip + EndTimeLookup finds every angle",
              len(back) == len(rows) and all(lk.find(a[1], a[2], a[3]) == r_["endtim"] for a, r_ in zip(angles, rows)))
    check("impact rows: keys exactly as contracted", all(list(x) == IMPACT_KEYS for x in imps), f"{list(imps[0])}")
    k1 = [x for x in imps if x["k"] == 1]
    check("one k=1 row per (angle, e), class 'first'", len(k1) == len(angles) * len(ES) and all(x["class"] == "first" for x in k1))
    k2 = {(x["name"], x["e"]): x for x in imps if x["k"] == 2}
    check("k=2 class/time = table per-e class and t2 (when present)",
          all(k2[(r_["name"], e)]["class"] == r_[f"class_e{e}"] and abs(k2[(r_["name"], e)]["t_end_ms"] - r_[f"t2_end_ms_e{e}"]) < 1e-12
              for r_ in rows for e in ES if r_[f"class_e{e}"] != "none"))
    err = max(np.abs(drop_direction(x["att_roll"], x["att_pitch"], x["att_yaw"]) - drop_direction(x["roll"], x["pitch"], x["yaw"])).max()
              for x in k1)
    check("k=1 attitude reproduces the input drop direction (< 1e-12)", err < 1e-12, f"{err}")
    check("k=1 v = (0,0,-v0) (+ g*0.1 ms), w = 0, vn_contact = v0", all(
        abs(x["vz"] + x["v0"]) < 1.1e-3 and abs(x["vx"]) + abs(x["vy"]) < 1e-12 and max(abs(x["wx"]), abs(x["wy"]), abs(x["wz"])) == 0
        and abs(x["vn_contact"] / x["v0"] - 1) < 3e-4 for x in k1))
    check("n = RotMat(att)·z, tfinal_k = t_end - t_start + margin", all(
        np.allclose(rotation_from_euler(x["att_roll"], x["att_pitch"], x["att_yaw"])[:, 2], [x["nx"], x["ny"], x["nz"]], atol=1e-12)
        and abs(x["tfinal_k_ms"] - (x["t_end_ms"] - x["t_start_ms"] + 1.0)) < 1e-12 for x in imps))
    r1, p1, _ = euler_from_direction(drop_direction(20.0, -35.0, 70.0), ndigits=12)
    rr2 = P.run_presim(BOX, [("Y1", 20.0, -35.0, 70.0), ("Y0", r1, p1, 0.0)], H, ES, friction=MU, workers=4, log=lambda s: None)
    check("yaw only matters through d: (r,p,y) and (r',p',0) same d -> same tfinal",
          abs(rr2[0]["tfinal_ms"] - rr2[1]["tfinal_ms"]) < 0.02 and rr2[0]["class"] == rr2[1]["class"])
    ry = P.run_presim(by, [(a[0], a[1], a[2], -90.0) for a in angles[:6]], H, ES, friction=MU, workers=4, log=lambda s: None)
    check("Y-long device with yaw -90 = X-long device (class, tfinal within 0.5 ms)",
          all(a["class"] == b["class"] and abs(a["tfinal_ms"] - b["tfinal_ms"]) < 0.5 for a, b in zip(ry, rows[:6])),
          f"{[(a['tfinal_ms'], b['tfinal_ms']) for a, b in zip(ry, rows[:6])]}")

    print("[7] 중력 끔 (DROP_ATTITUDE 덱 조건)")
    dg = (0.0, 0.0, -1.0)  # 넓은 면 낙하: 한 번 튀고 멀어짐 → 'clear' 로 멈춤 (2차가 1 ms 넘게 떨어져 오면 'second' 가 먼저)
    r_off = P.simulate_drop(BOX, dg, 0.5, MU, H, gravity_on=False)
    r_full = P.simulate_drop(dict(BOX, r_max=float("inf")), dg, 0.5, MU, H, gravity_on=False)
    check("v0 = sqrt(2 g h) without gravity", abs(r_off["v0"] - math.sqrt(2 * P.G * H)) < 1e-12)
    check("early stop 'clear' gives the same events as running to t_max", r_off["stop"] == "clear" and r_full["stop"] == "t_max"
          and [(e_["t_start_ms"], e_["J"]) for e_ in r_off["events"]] == [(e_["t_start_ms"], e_["J"]) for e_ in r_full["events"]],
          f"{r_off['stop']} {r_full['stop']}")
    # 중력 끔 표(v132 규칙): 회전으로 다시 닿는 'rebound' 도 tFinal 에 든다(사용자 결정 11-07). 실제 각도에서 확인한다.
    # v133 기본 규칙은 같은 각도에서 다르다(약한 늦은 재접촉을 뺌) — strong_contact=None 으로 v132 규칙을 고정한다.
    rb_rows = P.run_presim(BOX, [("SLOW", -18.5, -68.4, 0.0)], H, restitutions=(0.1, 0.3, 0.5), friction=MU,
                           gravity_on=False, workers=3, log=lambda *_: None, strong_contact=None)
    rb = rb_rows[0]
    reb_es = [e_ for e_ in (0.1, 0.3, 0.5) if rb[f"class_e{e_}"] == "rebound"]
    want = max([rb[f"t2_end_ms_e{e_}"] + 1.0 for e_ in (0.1, 0.3, 0.5) if rb[f"class_e{e_}"] in ("slapdown", "rebound")]
               + [rb[f"t1_end_ms_e{e_}"] + 1.0 for e_ in (0.1, 0.3, 0.5)])
    check("gravity-off table, v132 rule (strong_contact=None): counts every re-contact (tfinal = max over e of t2_end + 1)",
          abs(rb["tfinal_ms"] - want) < 1e-9, f"tfinal={rb['tfinal_ms']} want={want} rebound_e={reb_es}")
    rs = P.run_presim(BOX, [("SLOW", -18.5, -68.4, 0.0)], H, restitutions=(0.1, 0.3, 0.5), friction=MU,
                      gravity_on=False, workers=3, log=lambda *_: None)[0]
    want_s = max((rs[f"t1_end_ms_e{e_}"] if math.isnan(rs[f"strong_end_ms_e{e_}"]) else rs[f"strong_end_ms_e{e_}"]) + 1.0
                 for e_ in (0.1, 0.3, 0.5))
    check(f"gravity-off table, v133 rule: tfinal = max over e of (strong_end or t1_end) + 1; SLOW {rb['tfinal_ms']:.1f} -> "
          f"{rs['tfinal_ms']:.2f} ms (weak re-contact excluded), class/t2 columns unchanged",
          abs(rs["tfinal_ms"] - want_s) < 1e-12 and rs["tfinal_ms"] < 2.0 and math.isnan(rs["strong_end_ms"])
          and all(same_value(rs[k], rb[k]) for k in rb if k.startswith(("class", "t1_end", "t2_"))),
          f"{rs}")

    print("[8] 충돌 직전 상태 — 45° 짧은 모서리 2차, 에너지, 재시작")
    for e in (0.3,):
        sim = P.simulate_drop(BOX, d45, e, MU, H)
        imp = P.impact_rows(BOX, sim, "S45", 0.0, 45.0, 0.0, e)
        a2 = imp[1]
        M = rotation_from_euler(a2["att_roll"], a2["att_pitch"], a2["att_yaw"])
        wd = M @ [a2["wx"], a2["wy"], a2["wz"]]
        check("45° short edge k=2: slapdown on the opposite end (x = -75 mm)",
              a2["class"] == "slapdown" and abs(a2["contact_x"] + 0.075) < 1e-4 and imp[0]["contact_x"] > 0.0749)
        check("45° short edge k=2: vn_contact/v0 = prototype 1.171, rotation mainly about device y",
              abs(a2["vn_contact"] / a2["v0"] - PROTO_45[e][1]) < 2e-3 and abs(wd[1]) > 0.6 * np.linalg.norm(wd), f"{wd}")
        e1, e2 = sim["events"][0], next(x for x in sim["events"] if x["t_start_ms"] == a2["t_start_ms"])
        wdeck = np.array(e2["pre_rot"]) @ np.array(e2["pre_w"])
        E1 = 0.5 * MASS * np.dot(e1["pre_v"], e1["pre_v"]) + MASS * P.G * e1["pre_pos"][2]
        E2 = 0.5 * MASS * np.dot(e2["pre_v"], e2["pre_v"]) + 0.5 * wdeck @ BOX["inertia"] @ wdeck + MASS * P.G * e2["pre_pos"][2]
        check("energy before impact 2 <= energy before impact 1", E2 <= E1 * (1 + 1e-6), f"E2/E1={E2 / E1}")
        for label, gap, tol in (("exact captured state", e2["pre_gap_m"], 1e-6), ("lowest point 0.05 mm above floor", 5e-5, 0.01)):
            rs = P.simulate_from_state(BOX, M, [a2["vx"], a2["vy"], a2["vz"]], [a2["wx"], a2["wy"], a2["wz"]], e, MU,
                                       gap_m=gap, v_ref=sim["v0"])
            b1 = P.impact_rows(BOX, rs)[0]
            check(f"restart from k=2 state ({label}): impulse and duration reproduced",
                  abs(b1["J_over_mv0"] / a2["J_over_mv0"] - 1) <= tol
                  and abs((b1["t_end_ms"] - b1["t_start_ms"]) - (a2["t_end_ms"] - a2["t_start_ms"])) < 0.011,
                  f"J {b1['J_over_mv0']} vs {a2['J_over_mv0']}")

    print("[9] 작업자가 죽으면 무한 대기 없이 예외")

    def killer():
        time.sleep(0.8)
        kids = mp.active_children()
        if kids:
            os.kill(kids[0].pid, signal.SIGKILL)
    threading.Thread(target=killer, daemon=True).start()
    t = time.time()
    try:
        P.run_presim(BOX, fibonacci_angles(300), H, ES, workers=2, log=lambda s: None)
        check("killed worker raises BrokenProcessPool", False, "finished without error")
    except Exception as exc:  # noqa: BLE001
        check("killed worker raises BrokenProcessPool (no hang)", type(exc).__name__ == "BrokenProcessPool"
              and time.time() - t < 60, f"{type(exc).__name__} after {time.time() - t:.1f}s")

    print("[10] 작업자가 멈추면(SIGSTOP) 감시 시간 뒤 예외 + 작업자 정리")
    stopped = []

    def stopper():
        time.sleep(0.8)
        for kid in mp.active_children():
            os.kill(kid.pid, signal.SIGSTOP)
            stopped.append(kid.pid)
    old_np = P.NO_PROGRESS_S
    P.NO_PROGRESS_S = 3.0
    threading.Thread(target=stopper, daemon=True).start()
    t = time.time()
    try:
        P.run_presim(BOX, fibonacci_angles(300), H, ES, workers=2, log=lambda s: None)
        check("hung workers raise RuntimeError", False, "finished without error")
    except RuntimeError as exc:
        time.sleep(1.0)
        alive = [pid for pid in stopped if os.path.exists(f"/proc/{pid}") and
                 open(f"/proc/{pid}/stat").read().split()[2] not in ("Z", "X")]
        check("hung workers → RuntimeError within the watchdog, no worker left", "hung" in str(exc)
              and time.time() - t < 20 and not alive, f"{exc} after {time.time() - t:.1f}s alive={alive}")
    finally:
        P.NO_PROGRESS_S = old_np

    print("[11] 2차 이격 0.3 → 1 ms (H1): 상자 피보나치 1000 × e 3, 중력 끔 — 짧아지는 각도 없음 (v132 규칙)")
    # v132 규칙의 결정을 보는 시험이라 strong_contact=None 으로 고정한다(v133 규칙이면 P0005 는 0.3 ms 로도 2.09 ms 충격을 담는다)
    ang1000 = fibonacci_angles(1000)
    old = P.run_presim(BOX, ang1000, H, ES, friction=MU, gravity_on=False, t_sep_ms=0.3, workers=4, log=lambda s: None,
                       strong_contact=None)
    new = P.run_presim(BOX, ang1000, H, ES, friction=MU, gravity_on=False, workers=4, log=lambda s: None,
                       strong_contact=None)
    d = np.array([b["tfinal_ms"] - a["tfinal_ms"] for a, b in zip(old, new)])
    longer = d > 1e-9
    print(f"      longer {int(longer.sum())} angles, increase median {np.median(d[longer]):.2f} max {d.max():.2f} ms, "
          f"total {sum(a['tfinal_ms'] for a in old) / 1e3:.2f} -> {sum(b['tfinal_ms'] for b in new) / 1e3:.2f} s")
    check("no angle gets a shorter tfinal with the 1 ms rule", (d >= -1e-9).all(), f"min {d.min()}")
    p5o, p5n = old[4], new[4]
    check("P0005 (roll 1.34, pitch -172.42): old 1.42 ms missed the 1.86·v0 impact at 2.09 ms; new tfinal covers it",
          p5n["name"] == "P0005" and abs(p5o["tfinal_ms"] - 1.42) < 0.011 and p5n["tfinal_ms"] >= 3.27 + 1.0 - 1e-9
          and abs(p5n["t2_start_ms_e0.5"] - 2.09) < 0.011, f"{p5o['tfinal_ms']} -> {p5n['tfinal_ms']}")

    print("[12] 중력 끔에서 t_max 까지 2차도 벗어남도 없음 → n_unresolved + WARNING (L1)")
    # v132 규칙(strong_contact=None)의 미해결 뜻: 2차도 바닥 벗어남도 없이 t_max·이벤트 상한으로 끝난 e
    logs = []
    ru = P.run_presim(BOX, [("FACE", 0.0, 0.0, 0.0), ("S45", 0.0, 45.0, 0.0)], H, ES, friction=MU, gravity_on=False,
                      t_max=0.002, workers=2, log=logs.append, strong_contact=None)
    warn = [x for x in logs if "WARNING" in x]
    check("v132 rule: face drop stopped at t_max=2 ms: n_unresolved = 3, tfinal kept = t1_end + 1",
          ru[0]["n_unresolved"] == 3 and abs(ru[0]["tfinal_ms"] - (ru[0]["t1_end_ms"] + 1.0)) < 1e-12, f"{ru[0]}")
    check("one English WARNING line naming the angle; gravity on -> 0", len(warn) == 1 and "FACE" in warn[0]
          and all(r_["n_unresolved"] == 0 for r_ in P.run_presim(BOX, [("FACE", 0.0, 0.0, 0.0)], H, ES, t_max=0.002,
                                                                 workers=2, log=lambda s: None)), f"{warn}")
    # v133 규칙의 미해결 뜻: 시뮬이 t_max·이벤트 상한(MAX_EVENTS_FULL)으로 끝난 e. 2 ms 안에서 평판 낙하는 e 마다 1 ms 조용 뒤
    # calm 으로 풀리고(꼭짓점별 한계에서 튀어 오르는 v_z 를 뺀다), 2° 기운 낙하는 e 0.1 만 풀리며, 45° 모서리는 2차(약 17 ms)
    # 전이라 모두 t_max 다
    logs = []
    three = (("FACE", (0.0, 0.0)), ("T2", (0.0, 2.0)), ("S45", (0.0, 45.0)))
    ru = P.run_presim(BOX, [(nm, *a, 0.0) for nm, a in three], H, ES, friction=MU, gravity_on=False,
                      t_max=0.002, workers=2, log=logs.append)
    warn = [x for x in logs if "WARNING" in x]
    stops = {nm: [P.simulate_drop(BOX, drop_direction(*a), e, MU, H, gravity_on=False, t_max=0.002,
                                  strong_vn=P.STRONG_CONTACT)["stop"] for e in ES] for nm, a in three}
    check("v133 rule: n_unresolved = e count stopped on t_max/max_events (FACE all calm, T2 calm + t_max mix, S45 all t_max)",
          [r_["n_unresolved"] for r_ in ru] == [sum(s in ("t_max", "max_events") for s in stops[nm]) for nm, _ in three]
          and stops["FACE"] == ["calm"] * 3 and "calm" in stops["T2"] and "t_max" in stops["T2"]
          and stops["S45"] == ["t_max"] * 3, f"{stops}")
    check("v133 rule: one WARNING line naming T2 and S45, not FACE (t_max or event cap, tfinal = last strong re-contact so far)",
          len(warn) == 1 and "T2" in warn[0] and "S45" in warn[0] and "FACE" not in warn[0] and "200 events" in warn[0],
          f"{warn}")
    old_cap = P.MAX_EVENTS_FULL
    P.MAX_EVENTS_FULL = 3  # fork 작업자가 이어받는다 — idx 15 e 0.5 는 이벤트 5 개
    try:
        rcap = P.run_presim(BOX, [("I15", *euler_from_direction(proto_fibonacci(1000)[15], ndigits=10))], H, (0.5,),
                            friction=MU, gravity_on=False, workers=1, log=lambda s: None)[0]
    finally:
        P.MAX_EVENTS_FULL = old_cap
    check("v133 rule: event cap (MAX_EVENTS_FULL) counts as unresolved", rcap["n_unresolved"] == 1, f"{rcap}")

    print("[13] 바닥 위 접촉 거리 reach_m (L6)")
    sim = P.simulate_drop(BOX, d45, 0.3, MU, H)
    evs = sim["events"]
    t2s, t2e, cls, t1e = P.second_impact(evs)
    p1 = np.array([evs[0]["floor_x_m"], evs[0]["floor_y_m"]])
    lower = max(np.hypot(e_["floor_x_m"] - p1[0], e_["floor_y_m"] - p1[1]) for e_ in evs if e_["t_end_ms"] <= t2e + 1e-9)
    rr = P.run_presim(BOX, [("S45", 0.0, 45.0, 0.0)], H, (0.3,), friction=MU, workers=1, log=lambda s: None)[0]
    check("45° short edge: reach = slap end to first end on the floor (0.13-0.17 m) >= event centroids' distance",
          0.13 < rr["reach_m"] < 0.17 and rr["reach_m"] >= lower - 1e-9, f"reach {rr['reach_m']} lower {lower}")
    check("reach_m = max of per-event reach over events inside tfinal",
          abs(rr["reach_m"] - max(e_["reach_m"] for e_ in evs if e_["t_end_ms"] <= t2e + 1e-9)) < 1e-12)
    flat = P.simulate_drop(BOX, (0, 0, -1), 0.3, MU, H)["events"][0]
    check("flat drop 1st event: reach from the face-contact centroid to a corner ~ half diagonal 83.9 mm (80-90)",
          0.080 < flat["reach_m"] < 0.090, f"{flat['reach_m']}")

    print("[14] 부모가 kill -9 로 죽으면 작업자도 몇 초 안에 죽는다 (고아 작업자 없음, R2-1)")

    def children_of(pid):
        kids = []
        for dname in os.listdir("/proc"):
            if dname.isdigit():
                try:
                    st = open(f"/proc/{dname}/stat").read().rsplit(")", 1)[1].split()
                except OSError:
                    continue
                if int(st[1]) == pid and st[0] not in ("Z", "X"):
                    kids.append(int(dname))
        return kids

    def alive(pid):
        try:
            return open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()[0] not in ("Z", "X")
        except OSError:
            return False
    code = ("import sys; sys.path.insert(0, %r)\nimport numpy as np\n"
            "from KooCAEManager import KooRigidDropPresim as P\nfrom KooCAEManager.KooEndTimeTable import fibonacci_angles\n"
            "C = np.array([[a, b, c] for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]) * np.array(%r)\n"
            "B = P.make_body(0.2, (0, 0, 0), np.diag(%r), C)\n"
            "P.run_presim(B, fibonacci_angles(5000), 1.5, workers=2, log=lambda s: None)\n") % (
        str(GEN), HALF.tolist(), np.diag(box_inertia()).tolist())
    parent = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    kids, t = [], time.time()
    while time.time() - t < 30 and len(kids) < 2:
        time.sleep(0.2)
        kids = children_of(parent.pid)
    os.kill(parent.pid, signal.SIGKILL)
    parent.wait()
    t = time.time()
    while time.time() - t < 5 and any(alive(k) for k in kids):
        time.sleep(0.1)
    check("2 workers seen, all gone within 5 s after SIGKILL of the parent", len(kids) == 2 and not any(alive(k) for k in kids),
          f"kids {kids} alive {[k for k in kids if alive(k)]}")
    for k in kids:  # 실패했을 때 남은 것 정리
        if alive(k):
            os.kill(k, signal.SIGKILL)

    print("[15] v133 마지막 강한 재접촉 규칙(중력 끔, 기본 0.2·수용 대조 0.3) — v132 동일 경로·calm 건전성·상자 예시·수용 대조")
    # (a) 중력 켬, strong_contact=None 은 v132 엔진과 비트까지 같다 (표 줄의 v132 칸·충돌 상태 줄 전부)
    V = load_v132()
    if V is None:
        print(f"  SKIP v132 bit-identity: git or commit {V132_COMMIT} not available")
    else:
        ang = fibonacci_angles(8) + [("Y1", 20.0, -35.0, 70.0), ("S45", 0.0, 45.0, 0.0)]
        for label, kw in (("gravity on (default strong_contact ignored)", dict()),
                          ("gravity on, strong_contact=None", dict(strong_contact=None)),
                          ("gravity off, strong_contact=None", dict(gravity_on=False, strong_contact=None)),
                          ("gravity off, strong_contact=None, t_sep 0.3 ms", dict(gravity_on=False, strong_contact=None,
                                                                                 t_sep_ms=0.3))):
            g_on = kw.get("gravity_on", True)
            nr, ni = P.run_presim(BOX, ang, H, ES, friction=MU, workers=4, log=lambda s: None, return_impacts=True, **kw)
            orow, oimp = V.run_presim(BOX, ang, H, ES, friction=MU, gravity_on=g_on, t_sep_ms=kw.get("t_sep_ms", 1.0),
                                      workers=4, log=lambda s: None, return_impacts=True)
            same_imp = len(ni) == len(oimp) and all(list(a) == list(b) and all(same_value(a[k], b[k]) for k in b)
                                                    for a, b in zip(ni, oimp))
            check(f"v132 ({V132_COMMIT}) bit-identical table rows + impact rows: {label}", same_as_v132(nr, orow) and same_imp)
        sa = P.simulate_drop(BOX, d45, 0.3, MU, H, gravity_on=True, strong_vn=0.3)
        sb = V.simulate_drop(BOX, d45, 0.3, MU, H)
        check("simulate_drop gravity on ignores strong_vn: events and stop = v132",
              sa["stop"] == sb["stop"] and [list(x.items()) for x in sa["events"]] == [list(x.items()) for x in sb["events"]])
        so = P.simulate_drop(BOX, d45, 0.3, MU, H, gravity_on=False)
        sbo = V.simulate_drop(BOX, d45, 0.3, MU, H, gravity_on=False)
        s3 = P.simulate_drop(BOX, d45, 0.3, MU, H, gravity_on=False, strong_vn=0.3)
        check("simulate_drop gravity off, strong_vn=None: events and stop = v132; v133 path adds only approach_max_mps",
              so["stop"] == sbo["stop"] and [list(x.items()) for x in so["events"]] == [list(x.items()) for x in sbo["events"]]
              and all(list(x) == list(sbo["events"][0]) + ["approach_max_mps"] for x in s3["events"]))

    # (b) calm 건전성: calm 으로 멈춘 실행의 이벤트는 calm 을 끈 실행의 앞부분이고 tFinal·strong_end 가 같다
    sc = P.STRONG_CONTACT
    cases = ([("box", i, e, sc) for i in SOUND_IDX for e in ES] + [(b, i, 0.9, sc) for b, i in SOUND_E09]
             + [("rod", i, 0.1, 0.3) for i in SOUND_ROD])
    with mp.get_context("fork").Pool(4) as pool:
        snd = pool.map(_sound_job, cases, chunksize=1)
    n_calm = sum(x[3] == "calm" for x in snd)
    bad = [(b, i, e, s, rs_, tf_strong(a), tf_strong(c)) for b, i, e, s, rs_, a, c, pre in snd
           if not (pre and tf_strong(a) == tf_strong(c) and same_value(a[1], c[1]) and rs_ in ("clear", "t_max"))]
    check(f"calm soundness on {len(snd)} cases ({n_calm} stopped calm): events = prefix of the no-stop run, same tFinal",
          not bad and n_calm >= 30, f"calm {n_calm} bad {bad}")
    e09 = [x for x in snd if x[2] == 0.9]
    rod = [x for x in snd if x[0] == "rod" and x[2] == 0.1]
    check("calm at e 0.9 after strong re-contacts (box, rod, offset-CoM phone): calm tFinal = no-stop tFinal",
          len(e09) == 6 and all(x[3] == "calm" and not math.isnan(x[6][1]) for x in e09) and not bad, f"{e09}")
    check("per-vertex bound (thr 0.3): rod e 0.1 dirs that ran to t_max with the old bound now stop calm (no-stop: t_max)",
          len(rod) == 3 and all(x[3] == "calm" and x[4] == "t_max" for x in rod) and not bad, f"{rod}")

    # (c) 꼭짓점별로 갈라져 오는 슬랩다운 — 더 센 뒷묶음이 이제 담긴다 (피보나치 1000 idx 15, e 0.5)
    d15 = proto_fibonacci(1000)[15]
    r15 = P.simulate_drop(BOX, d15, 0.5, MU, H, gravity_on=False, strong_vn=P.STRONG_CONTACT)
    imp15 = P.impact_rows(BOX, r15)
    st15 = P.strong_from_events(r15["events"], r15["v0"], P.STRONG_CONTACT)
    si15 = P.second_impact(P.simulate_drop(BOX, d15, 0.5, MU, H, gravity_on=False)["events"])
    tf132 = P.tfinal_ms(si15[1], si15[2], si15[3], count_rebound=True)
    check("idx 15 e 0.5: clusters 0 / 2.25 / 3.92 / 5.73 ms (gravity off now gives k=1..4 impact rows)",
          [round(x["t_start_ms"], 2) for x in imp15] == [0.0, 2.25, 3.92, 5.73], f"{[x['t_start_ms'] for x in imp15]}")
    check("idx 15 e 0.5: v132 tFinal 3.25 ms (2nd cluster 0.72·v0) -> v133 6.98 ms (last strong cluster, max 1.86·v0)",
          abs(tf132 - 3.25) < 1e-9 and abs(tf_strong(st15) - 6.98) < 1e-9 and abs(st15[2] - 1.857) < 1e-3, f"{tf132} {st15}")
    a15 = euler_from_direction(d15, ndigits=10)
    row15 = P.run_presim(BOX, [("I15", *a15)], H, (0.5,), friction=MU, gravity_on=False, workers=1, log=lambda s: None)[0]
    check("idx 15 e 0.5 table row: tfinal 6.98, strong_end 5.98, strong_vn_max 1.86, class/t2 = first re-contact (2.25 ms)",
          abs(row15["tfinal_ms"] - 6.98) < 1e-9 and abs(row15["strong_end_ms"] - 5.98) < 1e-9
          and row15["strong_end_ms_e0.5"] == row15["strong_end_ms"] and abs(row15["strong_vn_max"] - st15[2]) < 1e-9
          and row15["class"] == "slapdown" and abs(row15["t2_end_ms"] - 2.25) < 1e-9 and row15["endtim"] == 0.007,
          f"{row15}")

    # (c2) R4 F2: 한 꼭짓점이 0.27·v0 로 약하게 닿고 0.03 ms 뒤 먼 꼭짓점이 1.215·v0 로 닿아 한 이벤트(T_CHATTER 0.05 ms)로
    #      붙는다. 묶음 세기를 첫 접촉 스텝 vn 으로만 재면 v133 tFinal 이 1.0 ms 였다 — 이벤트 안 최대(approach_max_mps)로 14.67 ms
    zf, gf = 1.0 - 2.0 * 270.5 / 300, math.pi * (3.0 - math.sqrt(5.0))  # R4 repro_strength 방향 (피보나치 300 중 270)
    df = np.array([math.sqrt(1 - zf * zf) * math.cos(gf * 270), math.sqrt(1 - zf * zf) * math.sin(gf * 270), zf])
    rf = P.simulate_drop(OFFSET, df, 0.5, MU, H, gravity_on=False, strong_vn=P.STRONG_CONTACT)
    stf = P.strong_from_events(rf["events"], rf["v0"], P.STRONG_CONTACT)
    ef = rf["events"][-1]
    check("F2 merged hard hit (offset-CoM phone, e 0.5): 13.64 ms event starts 0.271·v0, peaks 1.215·v0 -> tFinal 14.67 ms "
          "(was 1.0), stop clear (= no-stop run)",
          rf["stop"] == "clear" and len(rf["events"]) == 2 and abs(ef["t_start_ms"] - 13.64) < 1e-6
          and abs(-ef["vn_mps"] / rf["v0"] - 0.271) < 1e-3 and abs(ef["approach_max_mps"] / rf["v0"] - 1.215) < 1e-3
          and abs(tf_strong(stf) - 14.67) < 1e-9 and abs(stf[2] - ef["approach_max_mps"] / rf["v0"]) < 1e-15,
          f"{rf['stop']} {[(x['t_start_ms'], x['vn_mps'], x['approach_max_mps']) for x in rf['events']]} {stf}")

    # (d) 거의 멈춰 돌다 수백 ms 뒤 스치는 약한 접촉은 이제 ENDTIM 을 늘리지 않는다 (e 0.1)
    al, be = math.radians(2.0), math.radians(-13.0)
    for label, d, want132, want133 in (
            ("mirror (dx, dy, -dz) of idx 618", proto_fibonacci(1000)[618] * [1.0, 1.0, -1.0], 465.18, 1.69),
            ("side alpha 2, beta -13", (math.sin(al) * math.cos(be), -math.cos(al) * math.cos(be), math.sin(be)), 520.91, 1.98)):
        r_old = P.simulate_drop(BOX, d, 0.1, MU, H, gravity_on=False)
        si = P.second_impact(r_old["events"])
        r_new = P.simulate_drop(BOX, d, 0.1, MU, H, gravity_on=False, strong_vn=P.STRONG_CONTACT)
        st = P.strong_from_events(r_new["events"], r_new["v0"], P.STRONG_CONTACT)
        tf_old = P.tfinal_ms(si[1], si[2], si[3], count_rebound=True)
        check(f"weak late graze, {label}: v132 {want132} ms -> v133 {want133} ms (graze {st[2]:.3f}·v0 < 0.3)",
              abs(tf_old - want132) < 1e-9 and abs(tf_strong(st) - want133) < 1e-9 and st[2] < 0.1
              and abs(si[0] - (want132 - 1.0)) < 1e-9, f"{tf_old} {st} {si}")

    # (e) 수용 대조: 피보나치 1000(프로토타입 위상) × e 3 — 멈춤 없이 끝까지 돌린 기준(last>=0.3)과 방향마다 같다.
    #     기준 csv 는 첫 접촉 vn 세기로 만들었지만, 이벤트 안 최대 세기(approach_max_mps)로 다시 만들어도 1000 방향 모두 같다
    #     (재접촉 묶음 5391 개 가운데 0.3 문턱을 넘나드는 것 0 — R6 검증)
    ang_p = [(f"P{i + 1:04d}", *euler_from_direction(d_, ndigits=10)) for i, d_ in enumerate(proto_fibonacci(1000))]
    logs = []
    t = time.time()
    acc = P.run_presim(BOX, ang_p, H, ES, friction=MU, gravity_on=False, strong_contact=0.3, workers=4, log=logs.append)
    wall = time.time() - t
    tf_acc = np.array([r_["tfinal_ms"] for r_ in acc])
    print(f"      1000 x 3 cases {wall:.1f} s (4 workers): total {tf_acc.sum() / 1e3:.5f} s, max {tf_acc.max():.2f} ms, "
          f"{[x for x in logs if '종료 이유' in x][0].split('종료 이유 ')[-1]}")
    check("acceptance: total 19.48153 s, max 139.05 ms (= no-stop reference, rule last>=0.3)",
          abs(tf_acc.sum() - 19481.53) < 1e-6 and abs(tf_acc.max() - 139.05) < 1e-9, f"{tf_acc.sum()} {tf_acc.max()}")
    if os.path.exists(REF_V133):
        with open(REF_V133, newline="") as f:
            ref = np.array([float(x["last>=0.3"]) for x in csv.DictReader(f)])
        mism = np.nonzero(tf_acc != ref)[0]
        check("acceptance: tfinal per direction == no-stop reference (endtime_rule_check.csv, last>=0.3), 0 mismatches",
              len(ref) == 1000 and len(mism) == 0, f"{len(mism)} mismatches, first {mism[:10]}")
    else:
        print(f"  SKIP per-direction acceptance: {REF_V133} not found")

    print(f"\n{'PASS' if not FAILS else 'FAIL'} ({time.time() - t_all:.0f} s)")
    for f in FAILS:
        print("  -", f)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
