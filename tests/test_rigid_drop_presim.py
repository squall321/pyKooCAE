# 강체 낙하 사전 해석 엔진(KooRigidDropPresim)의 껍질 충실도·프로토타입 수치·규약·표 줄·충돌 직전 상태를 검증하는 시험
"""
실행: venv312/bin/python tests/test_rigid_drop_presim.py   (pybullet 필요, 약 1분, 프로세스 ≤ 4)

기준값은 프로토타입 /home/koopark/kooOmniDropAnalyzer/fullangle_mbd (PyBullet GEOM_BOX 150×75×7.5 mm, 200 g, μ 0.5)의
저장 결과(results_mu0.5, tilt45_sensitivity.csv, six_face_exact.csv)다. 전체 측정은 /data/koopark/Test_RigidDropEndtime/B 에 있다.
"""
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


BOX = P.make_body(MASS, (0.0, 0.0, 0.0), box_inertia(), CORNERS)


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
    t2s, t2e, cls, t1e = P.second_impact([ev(0, 0.01), ev(0.1, 0.2)], 0.3)
    check("none: t1_end = last event end (not NaN)", cls == "none" and t1e == 0.2 and math.isnan(t2s))
    check("tfinal rule: slapdown -> t2_end + 1, rebound -> t1_end + 1",
          P.tfinal_ms(3.35, "slapdown", 0.25) == 4.35 and P.tfinal_ms(100.0, "rebound", 0.01) == 1.01)
    check("gravity off (count_rebound): rebound -> t2_end + 1, none -> t1_end + 1",
          P.tfinal_ms(100.0, "rebound", 0.01, count_rebound=True) == 101.0
          and P.tfinal_ms(float("nan"), "none", 0.2, count_rebound=True) == 1.2)
    check("endtim: ceil to 0.1 ms, deck units", P.endtim_from_ms(1.01, 1.0) == 0.0011 and P.endtim_from_ms(17.76, 1e-3) == 17.8
          and P.endtim_from_ms(1.0000000000000002, 1.0) == 0.001 and P.endtim_from_ms(2.0, 1e-3) == 2.0)

    print("[6] run_presim 표 줄 (KooEndTimeTable) · 각도 규약 · 충돌 상태 줄")
    angles = fibonacci_angles(8) + [("Y1", 20.0, -35.0, 70.0)]
    rows, imps = P.run_presim(BOX, angles, H, ES, friction=MU, workers=4, time_to_s=1.0, log=lambda s: None,
                              return_impacts=True)
    per_e = [f"{c}_e{e}" for e in ES for c in ("class", "t1_end_ms", "t2_start_ms", "t2_end_ms")]
    check("columns = CORE_COLUMNS + per-e (class/t1/t2s/t2e _e<e>)", list(rows[0]) == CORE_COLUMNS + per_e, f"{list(rows[0])}")
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
    # 중력 끔 표: 회전으로 다시 닿는 'rebound' 도 tFinal 에 든다(사용자 결정 11-07). 실제 각도에서 확인한다.
    rb_rows = P.run_presim(BOX, [("SLOW", -18.5, -68.4, 0.0)], H, restitutions=(0.1, 0.3, 0.5), friction=MU,
                           gravity_on=False, workers=3, log=lambda *_: None)
    rb = rb_rows[0]
    reb_es = [e_ for e_ in (0.1, 0.3, 0.5) if rb[f"class_e{e_}"] == "rebound"]
    want = max([rb[f"t2_end_ms_e{e_}"] + 1.0 for e_ in (0.1, 0.3, 0.5) if rb[f"class_e{e_}"] in ("slapdown", "rebound")]
               + [rb[f"t1_end_ms_e{e_}"] + 1.0 for e_ in (0.1, 0.3, 0.5)])
    check("gravity-off table counts every re-contact (tfinal = max over e of t2_end + 1)",
          abs(rb["tfinal_ms"] - want) < 1e-9, f"tfinal={rb['tfinal_ms']} want={want} rebound_e={reb_es}")

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

    print(f"\n{'PASS' if not FAILS else 'FAIL'} ({time.time() - t_all:.0f} s)")
    for f in FAILS:
        print("  -", f)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
