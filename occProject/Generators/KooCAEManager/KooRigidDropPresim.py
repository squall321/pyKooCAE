# PyBullet 강체 낙하 사전 해석으로 각도별 1·2차 충돌 시점과 FEM 종료 시간(tFinal)·충돌 직전 상태를 구하는 엔진
"""
프로토타입 /home/koopark/kooOmniDropAnalyzer/fullangle_mbd/fullangle_drop_mbd.py 를 일반 강체로 옮긴 것이다.
  - 입력은 덱에서 구한 질량·무게중심·무게중심 기준 관성 텐서·볼록 껍질 꼭짓점이다(기기(덱) 좌표계, SI).
  - 접촉 설정, 충돌 이벤트 판정, 채터링 묶음(0.05 ms), 스침 버림(2%·m·v0), 시작 간격 0.5 mm,
    종료 조건(1 ms 이상 떨어졌다 닿은 묶음 뒤 1 ms 조용), 2차 충격 판정(T_sep 0.3 ms, 상승 1 mm)은 프로토타입 그대로다.
  - pybullet 은 함수 안에서 늦게 import 한다. 모듈 import 는 pybullet 없이 된다.

좌표
  - PyBullet 몸체 좌표는 무게중심 원점의 주축 좌표다. 주축은 기기 축에 가장 가깝게 고른다(대각 관성이면 단위 행렬).
    껍질 꼭짓점을 그 좌표로 옮겨 넣으므로 관성 좌표계가 단위 행렬이고, 주관성은 localInertiaDiagonal 로 준다.
  - 낙하 방향 d(기기 좌표에서 바닥을 향하는 단위 벡터, KooEndTimeTable.drop_direction)를 주축 좌표로 옮겨
    월드 -Z 로 보낸다(프로토타입 quat_down). 축 가정이 없으므로 길이 방향이 X 든 Y 든 같다.
  - 월드 = 바닥 좌표계(z 위 = 바닥 법선). 이벤트의 접촉 위치(cx/cy/cz, x/y 범위)와 바닥 법선(nb)은 기기 좌표로
    돌려 보고한다(위치는 덱 원점 기준 mm).

충돌 직전 상태(FEM 초기 조건용)
  - 이벤트마다 첫 접촉 스텝 바로 앞 스텝의 상태를 남긴다: pre_rot(바닥→덱 회전 = KMM RotMat), pre_pos·pre_v·pre_w
    (바닥 좌표 무게중심 위치·속도·각속도), pre_gap_m(최저 꼭짓점 높이), pre_contact(첫 접촉 스텝의 충격량 가중
    접촉점, 덱 좌표 m), contact_type(face/edge/corner).
  - impact_rows 가 이것을 충돌 묶음(k=1 1차, k=2 2차 …)마다 한 줄로 만든다. simulate_from_state 로 그 상태에서 다시 시작한다.
  - 한계: 정확히 대칭인 모서리·면 동시 접촉은 Bullet 이 접촉을 차례로 풀어 가짜 회전이 생긴다(프로토타입도 같다).
    예: 45° 짧은 모서리 1차 뒤 ω_x 26~52 rad/s 가 생겨 2차가 모서리 전체가 아니라 꼭짓점 하나로 닿는다.

충돌 여유(collision margin)
  - GEOM_MESH(꼭짓점만) 는 btConvexHullShape 이고, PyBullet 기본 여유 1 mm 만큼 바깥으로 부푼다(getClosestPoints 로 잼).
    changeDynamics(collisionMargin=0) 으로 없앤다. 바닥은 무한 평면이라 볼록-평면 알고리즘(지지점 질의)만 쓰므로
    여유 0 이 안전하다(GJK 를 쓰지 않는다).

속도 상한 (프로토타입과 다른 점 하나)
  - btMultiBody 는 속도 성분마다 ±100(rad/s, m/s) 으로 자른다(m_maxCoordinateVelocity). 꼭짓점·긴 모서리 충돌 직후
    각속도가 100 rad/s 를 넘으면 잘려서, 준 관성과 다른 회전이 된다(무마찰 한 점 충돌 해석해와 비교해 확인).
    maxJointVelocity=1e6 으로 사실상 끈다. 150×75×7.5 mm 상자 피보나치 1000방향 × e 3종에서 3.6% 경우가 바뀌고,
    각도별 tFinal 차이는 최대 1.4 ms 다(긴 모서리 착지처럼 긴 축 둘레로 빨리 도는 경우).

중력
  - gravity_on=True: 프로토타입처럼 g 를 켜고 v0 = √(2g(h−간격)) 으로 시작한다.
  - gravity_on=False: g 없이 v0 = √(2gh) — LS-DYNA DROP_ATTITUDE 덱(초기 속도만)과 같은 조건이다.
    이때 무게중심이 r_max(무게중심~꼭짓점 최대 거리)보다 높고 멀어지는 중이면 다시 닿을 수 없으므로 멈춘다(결과 불변).
    중력이 없으면 되떨어짐이 없으므로 'rebound'(무게중심 1 mm 넘게 상승) 로 분류된 접촉도 회전으로 온 것이다.
"""
import itertools
import math
import multiprocessing
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait

import numpy as np

from KooCAEManager.KooEndTimeTable import drop_direction, euler_from_rotation

G = 9.81
GAP = 5e-4             # 시작 시 최저점과 바닥 사이 간격 (m)
T_CHATTER = 5e-5       # 이 간격 이내 충격 스텝은 같은 이벤트 (s)
T_SEP_MAX = 1e-3       # 이만큼 떨어졌다 닿은 충돌 묶음이 이만큼 조용해지면 종료 (s)
MAX_EVENTS = 30
J_STEP = 1e-3          # 스텝 충격량 > J_STEP·m·v0 이면 충돌 스텝
J_EVENT_MIN = 0.02     # 합계 < J_EVENT_MIN·m·v0 인 이벤트는 스침으로 버림
# btMultiBody 속도 성분 상한(기본 100 rad/s·m/s)을 사실상 끔 — 기본값은 충돌 직후 ω 를 잘라 관성을 어긴다
MAX_COORD_VELOCITY = 1e6
MAX_HULL_VERTICES = 131072  # pybullet 이 한 번에 올리는 꼭짓점 수 상한(B3_MAX_NUM_VERTICES, 리눅스)
NO_PROGRESS_S = 600.0  # 이 시간 동안 끝나는 경우가 하나도 없으면 작업자가 멈춘 것으로 본다 (한 경우는 길어야 수 초)
CONTACT_TOL = 5e-5     # 충돌 직전 최저 꼭짓점에서 이 높이 안의 꼭짓점을 접촉 꼭짓점으로 봄 (m)
CONTACT_SPAN = 0.04    # 접촉 꼭짓점 퍼짐이 CONTACT_SPAN·r_max 이하인 방향은 길이 없음으로 봄 (조밀한 둥근 모서리 대비)


def quat_down(d):
    """몸체 벡터 d를 월드 -Z로 보내는 최소 회전 쿼터니언 (x, y, z, w). 프로토타입 그대로."""
    d = np.asarray(d, float) / np.linalg.norm(d)
    t = np.array([0.0, 0.0, -1.0])
    c = float(np.dot(d, t))
    if c < -1.0 + 1e-12:  # d = +Z: X축 180도
        return (1.0, 0.0, 0.0, 0.0)
    axis = np.cross(d, t)
    s = math.sqrt(2.0 * (1.0 + c))
    return (axis[0] / s, axis[1] / s, axis[2] / s, s / 2.0)


def _principal_frame(inertia):
    """→ (R, moments). R 의 열 = 주축(기기 좌표), det +1, 단위 행렬에 가장 가깝게(대각합 최대) 고른다."""
    w, V = np.linalg.eigh(inertia)
    best = None
    for perm in itertools.permutations(range(3)):
        R = V[:, perm].copy()
        R *= np.where(np.diag(R) < 0.0, -1.0, 1.0)
        if np.linalg.det(R) < 0.0:
            k = int(np.argmin(np.abs(np.diag(R))))
            R[:, k] = -R[:, k]
        if best is None or np.trace(R) > best[0] + 1e-12:
            best = (np.trace(R), R, w[list(perm)])
    return best[1], best[2]


def make_body(mass_kg, com_m, inertia_com_kgm2, hull_vertices_m):
    """기기 좌표 SI 입력 → 사전 해석용 강체 dict.

    mass_kg: 질량, com_m: 무게중심 (3,), inertia_com_kgm2: 무게중심 기준 관성 텐서 (3,3), hull_vertices_m: 껍질 꼭짓점 (N,3).
    돌려주는 dict: mass, com, inertia, R(기기←주축), moments(주관성), verts(주축 좌표 꼭짓점), r_max.
    """
    mass = float(mass_kg)
    com = np.asarray(com_m, dtype=float).reshape(3)
    inertia = np.asarray(inertia_com_kgm2, dtype=float).reshape(3, 3)
    verts = np.asarray(hull_vertices_m, dtype=float).reshape(-1, 3)
    if not (mass > 0.0 and math.isfinite(mass)):
        raise ValueError(f"rigid drop presim: mass must be positive, got {mass_kg}")
    if not (np.isfinite(com).all() and np.isfinite(inertia).all() and np.isfinite(verts).all()):
        raise ValueError("rigid drop presim: non-finite com/inertia/vertices")
    inertia = 0.5 * (inertia + inertia.T)
    R, moments = _principal_frame(inertia)
    if not moments.min() > 0.0:
        raise ValueError(f"rigid drop presim: inertia must be positive definite, principal moments {moments}")
    local = (verts - com) @ R
    if len(local) < 4 or np.linalg.svd(local - local.mean(axis=0), compute_uv=False)[-1] <= 1e-9 * np.abs(local).max():
        raise ValueError(f"rigid drop presim: hull needs >= 4 non-coplanar vertices, got {len(local)}")
    if len(local) > MAX_HULL_VERTICES:
        raise ValueError(f"rigid drop presim: {len(local)} vertices exceed pybullet limit {MAX_HULL_VERTICES}; "
                         "pass convex hull vertices only")
    return {"mass": mass, "com": com, "inertia": inertia, "R": R, "moments": moments, "verts": local,
            "r_max": float(np.linalg.norm(local, axis=1).max())}


def _contact_type(heights, pts_xy, r_max):
    """최저 꼭짓점에서 CONTACT_TOL 안의 꼭짓점들 → (face/edge/corner, 개수). 꼭짓점 8개 상자에서는 1/2/≥3 개 규칙과 같다.

    조밀한 껍질(둥근 모서리)은 한 점 근처에도 꼭짓점이 여럿이므로 개수 대신 바닥면 안 퍼짐(길이 있는 방향 수)으로 정한다.
    """
    near = heights - heights.min() <= CONTACT_TOL
    n = int(near.sum())
    if n == 1:
        return "corner", 1
    P = pts_xy[near] - pts_xy[near].mean(axis=0)
    proj = P @ np.linalg.svd(P, full_matrices=False)[2].T
    long_dirs = int(((proj.max(axis=0) - proj.min(axis=0)) > CONTACT_SPAN * r_max).sum())
    return ("corner", "edge", "face")[min(long_dirs, 2)], n


def _simulate(body, q, gap_m, v_init, w_init, e, mu, gravity_on, dt, t_max, trace, v_ref):
    """공통 적분 루프. q: 월드←주축 쿼터니언, gap_m: 최저 꼭짓점 높이, v_init·w_init: 바닥 좌표, v_ref: 문턱 기준 속도."""
    import pybullet as p

    Rp, com, mass, verts = body["R"], body["com"], body["mass"], body["verts"]
    cid = p.connect(p.DIRECT)
    try:
        p.setGravity(0, 0, -G if gravity_on else 0.0, physicsClientId=cid)
        # contactERP=0: 침투 보정이 속도를 더해 반발계수가 부풀려지는 것을 막음
        # contactSlop=0: 스텝당 침투가 slop보다 작은 작은 dt에서 반발이 사라지는 것을 막음
        p.setPhysicsEngineParameter(fixedTimeStep=dt, numSubSteps=0, numSolverIterations=50,
                                    restitutionVelocityThreshold=1e-3, contactERP=0.0,
                                    contactSlop=0.0, physicsClientId=cid)

        plane = p.createMultiBody(0, p.createCollisionShape(p.GEOM_PLANE, physicsClientId=cid),
                                  physicsClientId=cid)
        # Bullet은 두 물체 값을 곱해서 쓰므로 바닥은 1로 두고 강체 값으로 제어
        # contactProcessingThreshold=0: 선행 접촉(speculative contact)이 반발을 지우는 것을 막음
        p.changeDynamics(plane, -1, restitution=1.0, lateralFriction=1.0,
                         contactProcessingThreshold=0.0, physicsClientId=cid)

        R0 = np.array(p.getMatrixFromQuaternion(q)).reshape(3, 3)
        z0 = gap_m - (verts @ R0.T)[:, 2].min()
        shape = p.createCollisionShape(p.GEOM_MESH, vertices=verts.tolist(), physicsClientId=cid)
        phone = p.createMultiBody(mass, shape, basePosition=[0, 0, z0], baseOrientation=q, physicsClientId=cid)
        # collisionMargin=0: 껍질이 기본 여유 1 mm 만큼 부풀지 않게 함. 관성은 주관성 그대로
        p.changeDynamics(phone, -1, restitution=e, lateralFriction=mu, linearDamping=0.0,
                         angularDamping=0.0, rollingFriction=0.0, spinningFriction=0.0,
                         contactProcessingThreshold=0.0, collisionMargin=0.0, maxJointVelocity=MAX_COORD_VELOCITY,
                         localInertiaDiagonal=[float(v) for v in body["moments"]], physicsClientId=cid)
        p.resetBaseVelocity(phone, [float(v) for v in v_init], [float(v) for v in w_init], physicsClientId=cid)

        m_v0 = mass * v_ref
        j_step_th = J_STEP * m_v0
        j_event_min = J_EVENT_MIN * m_v0
        r_max = body["r_max"]

        events, cur = [], None
        z_ref = z_max = None
        tl = []
        v_prev, w_prev = np.array(v_init, dtype=float), np.array(w_init, dtype=float)
        pos_prev, orn_prev = np.array([0.0, 0.0, z0]), q
        second_found = False
        stop = "t_max"

        def close(ev):
            nonlocal z_ref, z_max, second_found
            if ev["J"] >= j_event_min:
                ev["c"] = ev["w"] / ev["J"]
                pts = np.array(ev["pts"])
                keep = pts[pts[:, 2] >= 0.05 * pts[:, 2].max()]  # 충격량 5% 미만 스침 점은 범위에서 제외
                ev["span"] = (keep[:, 0].min(), keep[:, 0].max(), keep[:, 1].min(), keep[:, 1].max())
                if events and ev["t_start"] - events[-1]["t_last"] >= T_SEP_MAX:
                    second_found = True
                events.append(ev)
                # 무게중심 상승량 기준은 확정 이벤트의 마지막 충격 시점 (스침은 기준을 바꾸지 않음)
                z_ref, z_max = ev["z_last"], ev["z_max"]

        def done(t):
            # T_SEP_MAX 이상 떨어졌다 닿은 충돌이 있고, 그 충돌 묶음이 T_SEP_MAX 동안 조용해졌으면 종료
            return len(events) >= MAX_EVENTS or (second_found and t - events[-1]["t_last"] >= T_SEP_MAX)

        for k in range(1, int(round(t_max / dt)) + 1):
            p.stepSimulation(physicsClientId=cid)
            t = k * dt
            pos, orn = p.getBasePositionAndOrientation(phone, physicsClientId=cid)
            pos = np.array(pos)
            J, wsum = 0.0, np.zeros(3)
            cps = [c for c in p.getContactPoints(phone, plane, physicsClientId=cid) if c[9] > 0]
            for c in cps:
                J += c[9] * dt
                wsum += c[9] * dt * np.array(c[5])
            if trace:  # (t, 스텝 충격량, 무게중심 z, vz, 기기 좌표 각속도 wx wy wz)
                vt, wt = p.getBaseVelocity(phone, physicsClientId=cid)
                wd = Rp @ (np.array(p.getMatrixFromQuaternion(orn)).reshape(3, 3).T @ np.array(wt))
                tl.append((t, J, pos[2], vt[2], wd[0], wd[1], wd[2]))

            if J > j_step_th:
                R = np.array(p.getMatrixFromQuaternion(orn)).reshape(3, 3)
                if cur is None:
                    rise = 0.0 if z_ref is None else z_max - z_ref
                    # 충돌 직전 접촉점의 연직 속도 (음수 = 바닥으로 접근)
                    vn = (v_prev + np.cross(w_prev, wsum / J - pos_prev))[2]
                    # nb = 바닥 법선(월드 +Z)의 몸체 좌표 성분. |nb_z| = 충격 중 두께 방향 비율
                    # pre = 첫 접촉 스텝 바로 앞 스텝의 상태 (월드←주축 회전, 무게중심 위치·속도·각속도,
                    #       첫 접촉 스텝의 충격량 가중 접촉 위치 — 무게중심 기준 월드. vn 과 같은 점)
                    cur = dict(t_start=t, t_last=t, J=0.0, w=np.zeros(3), rise=rise, vn=vn,
                               nb=R[2, :].copy(), pts=[],
                               pre=(np.array(p.getMatrixFromQuaternion(orn_prev)).reshape(3, 3), pos_prev, v_prev,
                                    w_prev, wsum / J - pos_prev))
                cur["t_last"] = t
                cur["J"] += J
                cur["w"] += R.T @ (wsum - J * pos)  # 몸체 좌표 기준 충격량 가중 접촉 위치
                for c in cps:  # 기기 좌표 접촉점 (x, y, 충격량) — 접촉 범위 계산용
                    b = com + Rp @ (R.T @ (np.array(c[5]) - pos))
                    cur["pts"].append((b[0], b[1], c[9] * dt))
                cur["z_last"] = cur["z_max"] = pos[2]
            else:
                if cur is not None:
                    cur["z_max"] = max(cur["z_max"], pos[2])
                if z_max is not None:
                    z_max = max(z_max, pos[2])
                if cur is not None and t - cur["t_last"] > T_CHATTER:
                    close(cur)
                    cur = None
                if cur is None and events and done(t):
                    stop = "max_events" if len(events) >= MAX_EVENTS else "second"
                    break
            v, w = p.getBaseVelocity(phone, physicsClientId=cid)
            v_prev, w_prev, pos_prev, orn_prev = np.array(v), np.array(w), pos, orn
            # 중력 없음: 무게중심이 r_max 보다 높고 멀어지는 중이면 어느 점도 다시 닿을 수 없다
            if not gravity_on and cur is None and events and pos[2] > r_max and v[2] >= 0.0:
                stop = "clear"
                break
        if cur is not None:
            close(cur)
    finally:
        p.disconnect(cid)

    t0 = events[0]["t_start"] if events else 0.0
    evs = []
    for i, ev in enumerate(events, start=1):
        c = com + Rp @ ev["c"]
        nb = Rp @ ev["nb"]
        Rw, pos0, v_0, w_0, rc0 = ev["pre"]
        rot = Rp @ Rw.T  # 바닥 → 덱 (KMM RotMat)
        h = pos0[2] + verts @ Rw[2, :]
        ctype, nlow = _contact_type(h, (verts @ Rw.T)[:, :2], r_max)
        c0 = com + rot @ rc0  # 첫 접촉 스텝 접촉 위치 (덱 좌표, m)
        evs.append(dict(k=i, t_start_ms=(ev["t_start"] - t0) * 1e3, t_end_ms=(ev["t_last"] - t0) * 1e3,
                        J=ev["J"], rise_mm=ev["rise"] * 1e3, vn_mps=ev["vn"],
                        cx_mm=c[0] * 1e3, cy_mm=c[1] * 1e3, cz_mm=c[2] * 1e3,
                        nbx=nb[0], nby=nb[1], nbz=nb[2],
                        x_lo_mm=ev["span"][0] * 1e3, x_hi_mm=ev["span"][1] * 1e3,
                        y_lo_mm=ev["span"][2] * 1e3, y_hi_mm=ev["span"][3] * 1e3,
                        pre_rot=tuple(tuple(float(x) for x in row) for row in rot),
                        pre_pos=tuple(float(x) for x in pos0), pre_v=tuple(float(x) for x in v_0),
                        pre_w=tuple(float(x) for x in w_0), pre_gap_m=float(h.min()),
                        pre_contact=tuple(float(x) for x in c0), contact_type=ctype, contact_nverts=nlow))
    out = {"v0": v_ref, "t0_s": t0 if events else math.nan, "stop": stop, "events": evs}
    if trace:
        out["trace"] = np.array(tl)
    return out


def simulate_drop(body, d, e, mu, height_m, gravity_on=True, dt=1e-5, t_max=1.0, trace=False):
    """한 방향 낙하. d = 기기 좌표에서 바닥을 향하는 방향.

    → {"v0", "t0_s"(첫 충돌 시작 절대 시각), "stop"(종료 이유), "events": [...]}.
    이벤트 칸은 프로토타입과 같고(시각은 첫 충돌 시작 기준 ms, 위치는 기기 좌표 mm) 충돌 직전 상태 pre_* 가 더 있다.
    trace=True 면 "trace" 도 준다 — 스텝마다 (t, 충격량, 무게중심 z, vz, 기기 좌표 각속도 wx wy wz), 검증용.
    """
    d = np.asarray(d, dtype=float)
    d = d / np.linalg.norm(d)
    v0 = math.sqrt(2.0 * G * (height_m - GAP)) if gravity_on else math.sqrt(2.0 * G * height_m)
    return _simulate(body, quat_down(body["R"].T @ d), GAP, (0.0, 0.0, -v0), (0.0, 0.0, 0.0), e, mu, gravity_on,
                     dt, t_max, trace, v0)


def simulate_from_state(body, rot_floor_to_deck, v, w, e, mu, gap_m=GAP, v_ref=None, gravity_on=True, dt=1e-5,
                        t_max=1.0, trace=False):
    """충돌 직전 상태에서 다시 시작한다(재시작 검증·연쇄용). 결과 형식은 simulate_drop 과 같다.

    rot_floor_to_deck: 바닥→덱 회전(= KMM RotMat, impact_rows 의 att_* 를 rotation_from_euler 로 바꾼 것)
    v, w: 바닥 좌표 무게중심 속도·각속도, gap_m: 최저 꼭짓점의 바닥 위 높이(음수 = 침투),
    v_ref: 이벤트 문턱 기준 속도(없으면 |v|).
    """
    from scipy.spatial.transform import Rotation

    Rw = np.asarray(rot_floor_to_deck, dtype=float).T @ body["R"]  # 월드 ← 주축
    q = tuple(float(x) for x in Rotation.from_matrix(Rw).as_quat())
    v = np.asarray(v, dtype=float)
    return _simulate(body, q, gap_m, v, np.asarray(w, dtype=float), e, mu, gravity_on, dt, t_max, trace,
                     float(np.linalg.norm(v)) if v_ref is None else float(v_ref))


def second_impact(events, t_sep_ms=0.3, rise_th_mm=1.0):
    """이격 시간 t_sep 이상 떨어졌다 다시 닿는 첫 이벤트를 2차 충격으로 본다. → (t2_start, t2_end, cls, t1_end) ms.

    cls: 무게중심이 rise_th 넘게 떴다 닿으면 "rebound", 아니면 "slapdown", 다시 닿지 않으면 "none".
    t2_end 는 t_sep 이내로 이어지는 접촉 묶음(꼭짓점 → 모서리 → 면)의 끝이다.
    "none" 이면 모든 접촉이 1차 묶음이므로 t1_end = 마지막 이벤트 끝이다(프로토타입은 NaN).
    """
    for j in range(1, len(events)):
        a, b = events[j - 1], events[j]
        if b["t_start_ms"] - a["t_end_ms"] >= t_sep_ms:
            cls = "rebound" if b["rise_mm"] > rise_th_mm else "slapdown"
            t_end = b["t_end_ms"]
            for c in events[j + 1:]:
                if c["t_start_ms"] - t_end >= t_sep_ms:
                    break
                t_end = c["t_end_ms"]
            return b["t_start_ms"], t_end, cls, a["t_end_ms"]
    return math.nan, math.nan, "none", (events[-1]["t_end_ms"] if events else math.nan)


def impact_rows(body, sim, name="", roll=0.0, pitch=0.0, yaw=0.0, e=math.nan, t_sep_ms=0.3, rise_th_mm=1.0,
                margin_ms=1.0):
    """simulate_drop 결과 → 충돌 묶음마다 FEM 초기 조건 한 줄 (k=1 1차, k=2 2차, …).

    묶음 = t_sep 이상 떨어진 곳에서 끊은 연속 이벤트(second_impact 와 같은 규칙, k=2 의 끝 = t2_end).
    시뮬은 2차 묶음 뒤 1 ms 조용하면 멈추므로 k≥3 은 그 앞에 생긴 것만 있다.
    class: k=1 "first", k≥2 "slapdown"/"rebound"(무게중심 상승 > rise_th).
    상태는 묶음 첫 이벤트의 첫 접촉 스텝 바로 앞 값이다. 접촉점(contact_*, 덱 좌표 m)은 그 첫 접촉 스텝의 충격량 가중
    위치 — 충돌이 시작되는 점이다(이벤트 전체 충격량 가중 위치는 이벤트의 cx/cy/cz_mm).
    nx·ny·nz = 바닥 법선(덱 좌표), att_* = euler_from_rotation(바닥→덱), v·w = 바닥 좌표(z 위),
    vn_contact = −(v + w × r_c)·z (접근 +, = 이벤트 vn_mps 의 부호 반대), tfinal_k_ms = 묶음 길이 + margin_ms.
    """
    clusters = []
    for ev in sim["events"]:
        if clusters and ev["t_start_ms"] - clusters[-1][-1]["t_end_ms"] < t_sep_ms:
            clusters[-1].append(ev)
        else:
            clusters.append([ev])
    m_v0 = body["mass"] * sim["v0"]
    rows = []
    for k, cl in enumerate(clusters, start=1):
        a = cl[0]
        rot, v, w = np.array(a["pre_rot"]), np.array(a["pre_v"]), np.array(a["pre_w"])
        c = np.array(a["pre_contact"])
        r_c = rot.T @ (c - body["com"])  # 무게중심 → 접촉점 (바닥 좌표)
        att = euler_from_rotation(rot)
        rows.append({"name": name, "roll": roll, "pitch": pitch, "yaw": yaw, "e": e, "k": k,
                     "class": "first" if k == 1 else "rebound" if a["rise_mm"] > rise_th_mm else "slapdown",
                     "t_start_ms": a["t_start_ms"], "t_end_ms": cl[-1]["t_end_ms"],
                     "J_over_mv0": sum(x["J"] for x in cl) / m_v0,
                     "contact_x": float(c[0]), "contact_y": float(c[1]), "contact_z": float(c[2]),
                     "contact_type": a["contact_type"],
                     "nx": float(rot[0, 2]), "ny": float(rot[1, 2]), "nz": float(rot[2, 2]),
                     "att_roll": att[0], "att_pitch": att[1], "att_yaw": att[2],
                     "vx": float(v[0]), "vy": float(v[1]), "vz": float(v[2]),
                     "wx": float(w[0]), "wy": float(w[1]), "wz": float(w[2]),
                     "vn_contact": -float((v + np.cross(w, r_c))[2]), "v0": sim["v0"],
                     "tfinal_k_ms": cl[-1]["t_end_ms"] - a["t_start_ms"] + margin_ms})
    return rows


def tfinal_ms(t2_end, cls, t1_end, margin_ms=1.0, count_rebound=False):
    """슬랩다운이면 2차 충격 묶음 끝 + 여유, 아니면 1차 충돌 끝 + 여유 (프로토타입 tfinal_map 규칙).

    count_rebound=True(중력 끔)면 'rebound' 도 2차 충격으로 센다 — 중력이 없으면 다시 닿는 것은 모두 회전으로 온 충격이다.
    """
    counted = cls == "slapdown" or (count_rebound and cls == "rebound")
    return (t2_end if counted else t1_end) + margin_ms


def endtim_from_ms(tf_ms, time_to_s=1.0):
    """tFinal(ms) → 물리 시간 0.1 ms 단위로 올림 → 덱 시간 단위 ENDTIM (time_to_s: 덱 시간 1 = time_to_s 초)."""
    up_ms = math.ceil(round(tf_ms * 10.0, 6)) / 10.0
    return round(up_ms * 1e-3 / time_to_s, 12)


_BODY = None


def _init_worker(body):
    global _BODY
    _BODY = body


def _job(args):
    i, k, d, e, mu, h, gravity_on, dt, t_max, t_sep_ms, imp = args
    r = simulate_drop(_BODY, d, e, mu, h, gravity_on=gravity_on, dt=dt, t_max=t_max)
    rows = None
    if imp:  # (name, roll, pitch, yaw, margin_ms)
        name, roll, pitch, yaw, margin_ms = imp
        rows = impact_rows(_BODY, r, name, roll, pitch, yaw, e, t_sep_ms=t_sep_ms, margin_ms=margin_ms)
    return i, k, second_impact(r["events"], t_sep_ms), r["stop"], rows


def run_presim(body, angles, height_m, restitutions=(0.1, 0.3, 0.5), friction=0.5, gravity_on=True, margin_ms=1.0,
               t_sep_ms=0.3, dt=1e-5, t_max=1.0, workers=8, time_to_s=1.0, log=print, return_impacts=False):
    """각도 목록 [(name, roll, pitch, yaw) 도] × 반발계수 → 각도마다 한 줄 (KooEndTimeTable 표 칸).

    낙하 방향은 KMM DropAttitude 규약 drop_direction(roll, pitch, yaw) (기기 좌표)이다.
    e 마다 tFinal = (slapdown 이면 t2_end, 아니면 t1_end) + margin_ms, 표 값은 e 들 가운데 최대다.
    gravity_on=False(FEM DROP_ATTITUDE 덱과 같음)면 rebound 도 2차 충격으로 센다(사용자 결정 11-07).
    endtim = 그 값을 0.1 ms 단위로 올려 덱 시간 단위로 바꾼 것이다.
    return_impacts=True 면 (rows, impacts) — impacts 는 (각도, e, 충돌 묶음 k) 마다 impact_rows 한 줄이다.
    """
    angles = [(str(n), float(r), float(pt), float(y)) for n, r, pt, y in angles]
    es = [float(e) for e in restitutions]
    if not angles or not es:
        raise ValueError("rigid drop presim: no angles or restitutions")
    if not time_to_s > 0.0:
        raise ValueError(f"rigid drop presim: time_to_s must be positive, got {time_to_s}")
    dirs = [drop_direction(r, pt, y) for _, r, pt, y in angles]
    jobs = [(i, k, dirs[i], es[k], float(friction), float(height_m), bool(gravity_on), float(dt), float(t_max),
             float(t_sep_ms), (*angles[i], float(margin_ms)) if return_impacts else None)
            for i in range(len(angles)) for k in range(len(es))]
    nw = max(1, min(int(workers), len(jobs)))
    log(f"[presim] 강체 낙하 사전 해석 {len(angles)} 각도 × 반발계수 {len(es)} = {len(jobs)} 경우 — 높이 {height_m:g} m, "
        f"마찰 {friction:g}, 중력 {'켬' if gravity_on else '끔'}, dt {dt:g} s, 최대 {t_max:g} s, 프로세스 {nw}")
    t_start = time.time()
    res, stops, imps = {}, {}, {}
    every = max(1, len(jobs) // 10)
    # fork 프로세스 풀 — 작업자마다 자기 p.DIRECT 를 연다. 작업자가 죽으면(OOM 등) BrokenProcessPool 로 멈춘다(무한 대기 없음).
    # 작업자가 멈춘 채 남으면(네이티브 스레드가 많은 프로세스의 fork) NO_PROGRESS_S 동안 끝나는 경우가 없을 때 작업자를 죽이고 멈춘다.
    pool = ProcessPoolExecutor(nw, mp_context=multiprocessing.get_context("fork"),
                               initializer=_init_worker, initargs=(body,))
    finished = False
    try:
        pending = {pool.submit(_job, job) for job in jobs}
        n = 0
        while pending:
            done, pending = wait(pending, timeout=NO_PROGRESS_S, return_when=FIRST_COMPLETED)
            if not done:
                raise RuntimeError(f"rigid drop presim: no case finished for {NO_PROGRESS_S:g} s "
                                   f"({n}/{len(jobs)} done) — a worker may be hung")
            for fut in done:
                n += 1
                i, k, si, stop, rows_k = fut.result()
                res[(i, k)], imps[(i, k)] = si, rows_k
                stops[stop] = stops.get(stop, 0) + 1
                if n % every == 0 or n == len(jobs):
                    log(f"[presim] {n}/{len(jobs)} 경우 완료 ({time.time() - t_start:.0f} s)")
        finished = True
    finally:
        if not finished:  # 멈춘 작업자를 남기지 않는다 — shutdown(wait=True) 는 멈춘 작업자를 영영 기다린다
            for proc in list((getattr(pool, "_processes", None) or {}).values()):
                proc.kill()
        pool.shutdown(wait=finished, cancel_futures=True)

    rows = []
    for i, (name, roll, pitch, yaw) in enumerate(angles):
        per = []
        for k, e in enumerate(es):
            t2s, t2e, cls, t1e = res[(i, k)]
            if math.isnan(t1e):
                raise RuntimeError(f"rigid drop presim: no floor contact for angle {name} e={e} within {t_max} s")
            per.append((e, cls, t1e, t2s, t2e, tfinal_ms(t2e, cls, t1e, margin_ms, count_rebound=not gravity_on)))
        g = max(range(len(per)), key=lambda j: (per[j][5], -j))  # 최대 tFinal, 같으면 앞의 e
        classes = [x[1] for x in per]
        row = {"name": name, "roll": roll, "pitch": pitch, "yaw": yaw,
               "dx": float(dirs[i][0]), "dy": float(dirs[i][1]), "dz": float(dirs[i][2]),
               "class": "slapdown" if "slapdown" in classes else "rebound" if "rebound" in classes else "none",
               "t1_end_ms": per[g][2], "t2_start_ms": per[g][3], "t2_end_ms": per[g][4], "tfinal_ms": per[g][5],
               "endtim": endtim_from_ms(per[g][5], time_to_s), "governing_e": per[g][0]}
        for e, cls, t1e, t2s, t2e, _ in per:
            row.update({f"class_e{e}": cls, f"t1_end_ms_e{e}": t1e, f"t2_start_ms_e{e}": t2s, f"t2_end_ms_e{e}": t2e})
        rows.append(row)

    tf = np.array([r["tfinal_ms"] for r in rows])
    n_cls = {c: sum(r["class"] == c for r in rows) for c in ("slapdown", "rebound", "none")}
    log(f"[presim] 사전 해석 끝 — {time.time() - t_start:.0f} s, 슬랩다운 {n_cls['slapdown']} · 재착지 {n_cls['rebound']} · "
        f"2차 없음 {n_cls['none']} 각도, tFinal {tf.min():.2f} ~ {tf.max():.2f} ms (중앙값 {np.median(tf):.2f}), "
        f"종료 이유 {stops}")
    if return_impacts:
        return rows, [r for i in range(len(angles)) for k in range(len(es)) for r in imps[(i, k)]]
    return rows
