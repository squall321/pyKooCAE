# DROP_ATTITUDE 의 RigidAngularVelocityX/Y/Z(기기 강체 회전 → *INITIAL_VELOCITY_GENERATION)와 EndTimeTable time_unit 확인을 검증하는 회귀 시험
"""
배경
  InitialAngularVelocity 는 *INITIAL_VELOCITY 의 VXR~VZR(절점 회전 속도, R16 28-121)에 들어가 솔리드만인 기기는 돌지 않는다.
  충격 직전 상태(자세·무게중심 속도·각속도)로 시작하는 FEM 은 강체 회전이 필요하다 → *INITIAL_VELOCITY_GENERATION(R16 28-124):
  OMEGA·축·중심(XC~ZC)·VX~VZ. 두 키워드는 한 덱에 같이 쓸 수 없다(Remark 1).

  [1] 파서: 키 이름 전체 일치만, 다른 키를 바꾸지 않음, 숫자 아닌 값은 종료 코드 1
  [2] ω = 0: 키 없음(InitialAngularVelocity 0)과 비교해 *INITIAL_VELOCITY → *INITIAL_VELOCITY_GENERATION 한 덩이만 다르고,
      병진 속도 글자가 같다(Fast 세 각도 + 한 각도)
  [3] ω ≠ 0, Fast 세 각도(메시 바닥판): 카드 값 = 바닥 좌표 입력으로 따로 만든 값(RotMat 은 계약 모듈 rotation_from_euler),
      절점 속도 v + ω×(x − c) = R·(v바닥 + ω바닥 × r바닥), ID 셋 = 기기의 모든 절점(바닥판 절점 없음),
      Fast 각도 k = 같은 ω 의 단일 실행(카드 글자·CONTROL/DATABASE 같고, Fast·단일 블록 차이는 키 없을 때와 같다)
  [4] ω ≠ 0, Fast 강체벽: 카드 값·절점 속도
  [5] 오류(rc 1, 덱 없음): InitialAngularVelocity 와 함께·목록 길이·축 빠짐·덱에 *INITIAL_VELOCITY 가 이미 있음
  [6] 재질 밀도로 단위계를 못 정하는 덱: 회전 중심은 그대로 무게중심, rc 0
  [7] EndTimeTable time_unit: 덱과 다르면 rc 1, 같으면 확인 줄, 판정이 안 되면 경고만, 메타가 없으면 예전 그대로
  [8] (있으면) Examples/MinimumModel.k Fast 세 각도: 중심 = 원점 이동 뒤 기기 무게중심, 절점 속도

실행: venv312/bin/python tests/test_drop_rigid_spin.py
"""
import contextlib
import io
import math
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
PY = ROOT / "venv312" / "bin" / "python"
MINI = ROOT / "Examples" / "MinimumModel.k"
sys.path.insert(0, str(GEN))

from KooCAEManager.KooEndTimeTable import drop_direction, rotation_from_euler, write_endtime_table  # noqa: E402

FAILS = []
ANG3 = [(0, 0, 0), (30, 20, 10), (-45, 60, 15)]
W3 = [(120.0, -40.0, 15.0), (0.0, 0.0, 250.0), (-80.0, 95.0, -30.0)]   # 바닥 좌표 rad/s
H, G = 50.0, 9810.0


def check(name, cond, detail=""):
    print("  %-78s %s" % (name[:78], "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def heavy(i, j, k):
    return i == 0 or (k == 1 and j == 3)


def box2_model(path, rho1="7.85e-9", rho2="3.0e-8", extra=()):
    """밀도가 다른 두 파트로 무게중심이 바운딩 박스 가운데에서 벗어난 상자(4×4×2 육면체, 2.5×2.5×1, 절점 75개)."""
    n, h, lines, idx, nid = 4, 2.5, [], {}, 0
    for k in range(3):
        for j in range(n + 1):
            for i in range(n + 1):
                nid += 1
                idx[(i, j, k)] = nid
                lines.append(f"{nid:8d}{i * h:16.6f}{j * h:16.6f}{k * 1.0:16.6f}")
    elems, eid = [], 0
    for k in range(2):
        for j in range(n):
            for i in range(n):
                eid += 1
                c = [idx[(i, j, k)], idx[(i + 1, j, k)], idx[(i + 1, j + 1, k)], idx[(i, j + 1, k)],
                     idx[(i, j, k + 1)], idx[(i + 1, j, k + 1)], idx[(i + 1, j + 1, k + 1)], idx[(i, j + 1, k + 1)]]
                elems.append(f"{eid:8d}{2 if heavy(i, j, k) else 1:8d}" + "".join(f"{x:8d}" for x in c))
    f10 = lambda *v: "".join(f"{str(x):>10s}" for x in v)  # noqa: E731
    Path(path).write_text("\n".join(
        ["*KEYWORD", "*PART", "LIGHT", f10(1, 1, 1), "*PART", "HEAVY", f10(2, 1, 2), "*SECTION_SOLID", f10(1, 1),
         "*MAT_ELASTIC", f10(1, rho1, "200000.0", "0.3"), "*MAT_ELASTIC", f10(2, rho2, "200000.0", "0.3")] + list(extra)
        + ["*NODE"] + lines + ["*ELEMENT_SOLID"] + elems + ["*END"]) + "\n")


def box2_com(rho1=7.85e-9, rho2=3.0e-8):
    """원점 이동(바운딩 박스 가운데 → 원점) 뒤의 해석적 무게중심 — 육면체마다 질량 ρV 가 그 가운데에 있다."""
    m, c = 0.0, np.zeros(3)
    for k in range(2):
        for j in range(4):
            for i in range(4):
                mm = (rho2 if heavy(i, j, k) else rho1) * 6.25
                m += mm
                c += mm * (np.array([(i + 0.5) * 2.5, (j + 0.5) * 2.5, k + 0.5]) - np.array([5.0, 5.0, 1.0]))
    return c / m


def option(model, angles, surface, w=None, both=False, height=H, tfinal=0.002, dt=1e-4, table=None, wlines=None, extra=()):
    """w 가 None 이면 예전 꼴(InitialAngularVelocity 0). w 를 주면 RigidAngularVelocity 줄(InitialAngularVelocity 줄 없음, both 면 둘 다)."""
    n = len(angles)
    rep = lambda v: ",".join([str(v)] * n)  # noqa: E731
    lines = ["*Inputfile", model, "*Mode", "DROP_ATTITUDE,1", "**DropAttitude,1",
             "EulerRolling," + ",".join(str(a[0]) for a in angles),
             "EulerPitching," + ",".join(str(a[1]) for a in angles),
             "EulerYawing," + ",".join(str(a[2]) for a in angles),
             "Gravity,9810", "Height," + rep(height)]
    if w is not None:
        lines += wlines or [f"RigidAngularVelocity{ax}," + ",".join(str(v[a]) for v in w) for a, ax in enumerate("XYZ")]
    if table:
        lines.append(f"EndTimeTable,{table}")
    lines += ["InitialVelocityX," + rep(0), "InitialVelocityY," + rep(0), "InitialVelocityZ," + rep(0)]
    if w is None or both:
        lines += ["InitialAngularVelocityX," + rep(0), "InitialAngularVelocityY," + rep(0), "InitialAngularVelocityZ," + rep(0)]
    lines += ["OffsetDistance,0.05", "Density,7.85e-09", "YoungsModulus,200000.0", "PoissonRatio,0.3",
              f"tFinal,{tfinal}", f"dt,{dt}", f"DropSurface,{surface}"] + list(extra) + ["**EndDropAttitude", "*End"]
    return "\n".join(lines) + "\n"


def run(wd, opt_text, model="box2.k", src=None, deck_kw=None):
    """작업 폴더에 모델·옵션을 두고 KMM 을 돌린다 → (rc, stdout). 모델은 늘 사본(KMM 이 옆에 _dump.k 를 쓴다)."""
    wd = Path(wd)
    wd.mkdir(parents=True, exist_ok=True)
    if src:
        shutil.copy2(src, wd / model)
    elif not (wd / model).exists():
        box2_model(wd / model, **(deck_kw or {}))
    (wd / "opt.txt").write_text(opt_text)
    r = subprocess.run([str(PY), str(GEN / "KooMeshModifier.py"), "opt.txt", str(wd)], cwd=str(GEN),
                       capture_output=True, text=True, timeout=900)
    return r.returncode, r.stdout + r.stderr


def decks(wd, stem):
    return {p.name: p.read_bytes() for p in sorted(Path(wd).glob(f"{stem}_*.k")) if not p.name.endswith("_dump.k")}


def angle_decks(wd, stem):
    return sorted(Path(wd).glob(f"{stem}_[0-9][0-9][0-9]_DA_*.k"))


def blocks(data):
    out, cur = [], None
    for ln in data.decode().splitlines():
        if ln.startswith("*"):
            if cur is not None:
                out.append("\n".join(cur))
            cur = [ln]
        elif cur is not None:
            cur.append(ln)
    if cur is not None:
        out.append("\n".join(cur))
    return [b for b in out if not b.startswith(("*KEYWORD", "*END"))]


def block_diff(a, b):
    ca, cb = Counter(blocks(a)), Counter(blocks(b))
    return ca - cb, cb - ca


def control_db(data):
    return [b for b in blocks(data) if b.startswith(("*CONTROL", "*DATABASE"))]


def gen_card(data):
    """*INITIAL_VELOCITY_GENERATION 카드 → 값 사전(+ 글 'text'). 없으면 None."""
    lines = data.decode().splitlines()
    if "*INITIAL_VELOCITY_GENERATION" not in lines:
        return None
    i = lines.index("*INITIAL_VELOCITY_GENERATION")
    c1, c2 = lines[i + 1], lines[i + 2]
    f = lambda s, k: s[10 * k:10 * k + 10]  # noqa: E731
    return {"ID": int(f(c1, 0)), "STYP": int(f(c1, 1)), "OMEGA": float(f(c1, 2)),
            "V": np.array([float(f(c1, k)) for k in (3, 4, 5)]), "IVATN": int(f(c1, 6)), "ICID": int(f(c1, 7)),
            "C": np.array([float(f(c2, k)) for k in (0, 1, 2)]), "N": np.array([float(f(c2, k)) for k in (3, 4, 5)]),
            "PHASE": int(f(c2, 6)), "IRIGID": int(f(c2, 7)), "text": "\n".join(lines[i:i + 3]),
            "n_cards": lines.count("*INITIAL_VELOCITY_GENERATION"), "n_iv": lines.count("*INITIAL_VELOCITY")}


def node_xyz(data, max_nid):
    out, on = {}, False
    for ln in data.decode().splitlines():
        if ln.startswith("*"):
            on = ln.strip() == "*NODE"
            continue
        if on and not ln.startswith("$") and ln.strip():
            nid = int(ln[:8])
            if nid <= max_nid:
                out[nid] = np.array([float(ln[8:24]), float(ln[24:40]), float(ln[40:56])])
    return out


def node_set(data, sid):
    lines, ids = data.decode().splitlines(), None
    for i, ln in enumerate(lines):
        if ln.startswith("*SET_NODE_LIST"):
            j = i + 1
            while lines[j].startswith("$"):
                j += 1
            if int(lines[j][:10]) != sid:
                continue
            ids = []
            for ln2 in lines[j + 1:]:
                if ln2.startswith("*"):
                    break
                if not ln2.startswith("$"):
                    ids += [int(ln2[k:k + 10]) for k in range(0, len(ln2.rstrip()), 10) if ln2[k:k + 10].strip()]
            return set(ids)
    return ids


def card_vs_inputs(tag, data, ang, w, com, max_nid=75):
    """카드 값과 절점 속도를 바닥 좌표 입력으로 따로 만든 값과 견준다(카드 자리수: 10.3e·10.4f·10.3f)."""
    card = gen_card(data)
    if card is None:
        check(f"{tag}: *INITIAL_VELOCITY_GENERATION 카드 있음", False)
        return None
    R = rotation_from_euler(*ang)
    vf = np.array([0.0, 0.0, -math.sqrt(2.0 * G * H)])
    wf = np.array(w, dtype=float)
    V, Wd = R @ vf, R @ wf
    check(f"{tag}: 카드 하나, *INITIAL_VELOCITY 없음, STYP 3·IVATN 1·ICID 0·PHASE 0·IRIGID 0",
          card["n_cards"] == 1 and card["n_iv"] == 0
          and (card["STYP"], card["IVATN"], card["ICID"], card["PHASE"], card["IRIGID"]) == (3, 1, 0, 0, 0), str(card))
    check(f"{tag}: OMEGA = |ω바닥|", abs(card["OMEGA"] - np.linalg.norm(wf)) <= 6e-4 * np.linalg.norm(wf),
          f"{card['OMEGA']} / {np.linalg.norm(wf)}")
    check(f"{tag}: 축 = 단위(R·ω바닥)", np.abs(card["N"] - Wd / np.linalg.norm(Wd)).max() <= 6e-4, f"{card['N']}")
    check(f"{tag}: V = R·(0,0,−√(2gh))", np.abs(card["V"] - V).max() <= 6e-4 * np.abs(V).max(), f"{card['V']} / {V}")
    check(f"{tag}: 중심 = 원점 이동 뒤 기기 무게중심", np.abs(card["C"] - com).max() <= 6e-5, f"{card['C']} / {com}")
    nd = node_xyz(data, max_nid)
    pick = sorted(nd)[:: max(1, len(nd) // 6)][:6]
    worst = 0.0
    for nid in pick:
        x = nd[nid]
        v_card = card["V"] + card["OMEGA"] * np.cross(card["N"], x - card["C"])
        v_exp = R @ (vf + np.cross(wf, R.T @ (x - com)))
        worst = max(worst, np.linalg.norm(v_card - v_exp) / (np.linalg.norm(V) + np.linalg.norm(wf) * np.linalg.norm(x - com)))
    check(f"{tag}: 절점 {len(pick)}개 v+ω×(x−c) = R(v바닥+ω바닥×r바닥) (최대 상대오차 {worst:.1e})", worst <= 2e-3)
    return card


def parse(d, text):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            import KooMeshModifier as K
            g = K.KooMeshModifier()
            g.SetCurrentDirectory(str(d))
            Path(d, "opt.txt").write_text(text)
            g.ImportOption("opt.txt")
        return g.modeIDOption[1]
    except Exception as e:  # noqa: BLE001
        return f"{type(e).__name__}: {e}"


def test_parse(tmp):
    print("[1] 파서 — 키 이름 전체 일치, 다른 키 보존, 숫자 아닌 값")
    d = Path(tmp, "parse")
    d.mkdir()
    o0 = parse(d, option("box2.k", ANG3, "Plane,0,0,0,4,4,1"))
    o1 = parse(d, option("box2.k", ANG3, "Plane,0,0,0,4,4,1", w=W3, both=True))
    ok = isinstance(o1, dict) and isinstance(o0, dict)
    check("RigidAngularVelocity 줄을 읽음 (예외 없음)", ok, str(o1))
    if not ok:
        return
    check("RigidAngularVelocityX/Y/Z = 각도마다 값", [o1.get(f"RigidAngularVelocity{a}") for a in "XYZ"]
          == [[v[i] for v in W3] for i in range(3)], str([o1.get(f"RigidAngularVelocity{a}") for a in "XYZ"]))
    rest = {k: v for k, v in o1.items() if not k.startswith("RigidAngularVelocity")}
    check("나머지 옵션(InitialAngularVelocity 포함) = 키 없을 때", rest == o0,
          str({k: (o0.get(k), rest.get(k)) for k in set(o0) | set(rest) if o0.get(k) != rest.get(k)}))
    base = option("box2.k", ANG3, "Plane,0,0,0,4,4,1")
    o2 = parse(d, base.replace("**DropAttitude,1\n", "**DropAttitude,1\nrigidangularvelocityz,1.0D2,0,-5\n"))
    check("대소문자 무관·D 지수", isinstance(o2, dict) and o2.get("RigidAngularVelocityZ") == [100.0, 0.0, -5.0], str(o2))
    o3 = parse(d, base.replace("**DropAttitude,1\n", "**DropAttitude,1\nRigidAngularVelocityXY,1,2,3\nRigidAngularVelocity,1,2,3\n"))
    check("키 이름이 다르면(…XY·축 없음) 받지 않음", isinstance(o3, dict) and o3 == o0, str(o3))
    for bad in ("RigidAngularVelocityX,1,abc,3", "RigidAngularVelocityY,1,,3"):
        try:
            parse_text = base.replace("**DropAttitude,1\n", f"**DropAttitude,1\n{bad}\n")
            with contextlib.redirect_stdout(io.StringIO()):
                import KooMeshModifier as K
                g = K.KooMeshModifier()
                g.SetCurrentDirectory(str(d))
                Path(d, "opt.txt").write_text(parse_text)
                g.ImportOption("opt.txt")
            code = None
        except SystemExit as e:
            code = e.code
        check(f"숫자 아닌 값·빈 칸 '{bad}' → 종료 코드 1", code == 1, str(code))


def test_zero(tmp):
    print("[2] ω = 0 — *INITIAL_VELOCITY → *INITIAL_VELOCITY_GENERATION 한 덩이만 다름")
    for tag, angles in (("fast", ANG3), ("single", [(30, 20, 10)])):
        a, b = Path(tmp, f"z_{tag}_nokey"), Path(tmp, f"z_{tag}_zero")
        rc_a, _ = run(a, option("box2.k", angles, "Plane,0,0,0,4,4,1"))
        rc_b, _ = run(b, option("box2.k", angles, "Plane,0,0,0,4,4,1", w=[(0.0, 0.0, 0.0)] * len(angles)))
        da, db = decks(a, "box2"), decks(b, "box2")
        check(f"{tag}: 두 실행 rc 0, 같은 덱 이름", (rc_a, rc_b) == (0, 0) and da.keys() == db.keys() and da, str((rc_a, rc_b, list(db))))
        com = box2_com()
        for name in da:
            la, lb = da[name].decode().splitlines(), db.get(name, b"").decode().splitlines()
            changed = [i for i in range(min(len(la), len(lb))) if la[i] != lb[i]]
            i = la.index("*INITIAL_VELOCITY") if "*INITIAL_VELOCITY" in la else -1
            ok = len(la) == len(lb) and i >= 0 and changed == [i, i + 1, i + 2] and lb[i] == "*INITIAL_VELOCITY_GENERATION"
            ok = ok and la[i + 2][:30] == lb[i + 1][30:60] and la[i + 1][:10] == lb[i + 1][:10]
            ok = ok and lb[i + 1][10:30] == "         3 0.000e+00" and lb[i + 2][30:60] == "     0.000     0.000     1.000"
            ok = ok and np.abs(np.array([float(lb[i + 2][k:k + 10]) for k in (0, 10, 20)]) - com).max() <= 6e-5
            check(f"{tag}: {name[:40]} — 그 세 줄만, 병진 속도 글자·절점 셋 같음, OMEGA 0·축 (0,0,1)·중심 무게중심", ok,
                  f"{[(j + 1, la[j], lb[j]) for j in changed][:4]}")


def test_spin_fast(tmp):
    print("[3] ω ≠ 0, Fast 세 각도(메시 바닥판) — 카드 값·절점 속도·절점 셋·단일 실행 대조")
    a, s = Path(tmp, "s_nokey"), Path(tmp, "s_spin")
    rc_a, _ = run(a, option("box2.k", ANG3, "Plane,0,0,0,4,4,1"))
    rc_s, out = run(s, option("box2.k", ANG3, "Plane,0,0,0,4,4,1", w=W3))
    check("두 실행 rc 0", (rc_a, rc_s) == (0, 0), out[-500:])
    names_a, names_s = angle_decks(a, "box2"), angle_decks(s, "box2")
    check("각도 덱 3개씩", len(names_a) == len(names_s) == 3, str([p.name for p in names_s]))
    com = box2_com()
    lines = [ln for ln in out.splitlines() if ln.startswith("[RigidAngularVelocity] roll=")]
    check("로그: 각도마다 '[RigidAngularVelocity] roll=… OMEGA=…' 한 줄", len(lines) == 3, "\n".join(lines))
    for k, (p, ang, w) in enumerate(zip(names_s, ANG3, W3), 1):
        data = p.read_bytes()
        card = card_vs_inputs(f"각도 {k}", data, ang, w, com)
        if card is None:
            continue
        ns = node_set(data, card["ID"])
        check(f"각도 {k}: ID 절점 셋 = 기기의 모든 절점 1~75 (바닥판 절점 없음)", ns == set(range(1, 76)), str(sorted(ns or [])[:5]))
        # 같은 각도 단일 실행(같은 ω) 과 키 없는 단일 실행
        s1, s0 = Path(tmp, f"s_single{k}_spin"), Path(tmp, f"s_single{k}_nokey")
        rc1, _ = run(s1, option("box2.k", [ang], "Plane,0,0,0,4,4,1", w=[w]))
        rc0, _ = run(s0, option("box2.k", [ang], "Plane,0,0,0,4,4,1"))
        g1, g0 = decks(s1, "box2").get("box2_drop.k", b""), decks(s0, "box2").get("box2_drop.k", b"")
        c1 = gen_card(g1) if g1 else None
        check(f"각도 {k}: Fast 카드 = 단일 실행 카드 (글자까지)", rc1 == rc0 == 0 and c1 is not None and c1["text"] == card["text"],
              f"\n{card['text']}\n{c1 and c1['text']}")
        check(f"각도 {k}: Fast CONTROL/DATABASE = 단일", control_db(data) == control_db(g1))
        d_new, d_old = block_diff(data, g1), block_diff(names_a[k - 1].read_bytes(), g0)
        kinds = sorted({b.splitlines()[0] for b in d_new[0]} | {b.splitlines()[0] for b in d_new[1]})
        check(f"각도 {k}: Fast·단일 블록 차이 = 키 없을 때와 같음 {kinds}", d_new == d_old)


def test_spin_rigidwall(tmp):
    print("[4] ω ≠ 0, Fast 강체벽 바닥")
    s = Path(tmp, "rw_spin")
    rc, out = run(s, option("box2.k", ANG3, "RigidWall,0,0,0,0,0,0", w=W3, extra=("DropContact.FS,0.3",)))
    check("rc 0", rc == 0, out[-400:])
    for k, (p, ang, w) in enumerate(zip(angle_decks(s, "box2"), ANG3, W3), 1):
        card_vs_inputs(f"강체벽 각도 {k}", p.read_bytes(), ang, w, box2_com())


def test_errors(tmp):
    print("[5] 오류 — rc 1, 덱을 쓰지 않음")
    cases = [
        ("both", option("box2.k", ANG3, "Plane,0,0,0,4,4,1", w=W3, both=True), {}, "함께 쓸 수 없다"),
        ("length", option("box2.k", ANG3, "Plane,0,0,0,4,4,1", w=W3, wlines=[
            "RigidAngularVelocityX,1", "RigidAngularVelocityY,0,0,0", "RigidAngularVelocityZ,0,0,0"]), {}, "각도 수(3개)"),
        ("axis", option("box2.k", ANG3, "Plane,0,0,0,4,4,1", w=W3, wlines=["RigidAngularVelocityZ,1,2,3"]), {}, "X·Y·Z 셋 모두"),
        ("deck_iv", option("box2.k", ANG3, "Plane,0,0,0,4,4,1", w=W3),
         {"extra": ["*INITIAL_VELOCITY", "         0", "       1.0       0.0       0.0"]}, "이미 *INITIAL_VELOCITY"),
    ]
    for tag, text, kw, msg in cases:
        w = Path(tmp, f"err_{tag}")
        rc, out = run(w, text, deck_kw=kw)
        check(f"{tag}: rc 1, 알림 '{msg}', 덱 없음", rc == 1 and msg in out and "🔴 [RigidAngularVelocity]" in out
              and not decks(w, "box2"), f"rc={rc} {out[-400:]}")


def test_units_unknown(tmp):
    print("[6] 재질 밀도로 단위계를 못 정하는 덱 — 회전 중심은 그대로 무게중심")
    s = Path(tmp, "units_spin")
    rc, out = run(s, option("box2.k", [(30, 20, 10)], "RigidWall,0,0,0,0,0,0", w=[(0.0, 0.0, 250.0)],
                            extra=("DropContact.FS,0.3",)), deck_kw={"rho1": "5.0", "rho2": "20.0"})
    check("rc 0, 단위 이름만 임시로 주고 다시 잼(로그)", rc == 0 and "단위 이름(m-kg-s)만" in out, out[-400:])
    data = decks(s, "box2").get("box2_drop.k", b"")
    card = gen_card(data) if data else None
    com = box2_com(5.0, 20.0)
    check("중심 = 해석적 무게중심(밀도 5·20)", card is not None and np.abs(card["C"] - com).max() <= 6e-5,
          f"{card and card['C']} / {com}")


def test_time_unit(tmp):
    print("[7] EndTimeTable time_unit — 덱 시간 단위(재질 밀도)와 대조")
    ang = [(30, 20, 10)]

    def case(tag, meta, deck_kw=None):
        w = Path(tmp, f"tu_{tag}")
        d = drop_direction(*ang[0])
        w.mkdir(parents=True, exist_ok=True)
        write_endtime_table(str(w / "t.csv"), [{"name": "A001", "roll": 30.0, "pitch": 20.0, "yaw": 10.0, "dx": float(d[0]),
                                                 "dy": float(d[1]), "dz": float(d[2]), "endtim": 0.0037}], meta)
        rc, out = run(w, option("box2.k", ang, "RigidWall,0,0,0,0,0,0", table="t.csv", extra=("DropContact.FS,0.3",)),
                      deck_kw=deck_kw)
        return rc, out, decks(w, "box2")

    rc, out, ds = case("mismatch", {"units": "mm-kg-ms", "time_unit": "ms"})
    check("표 ms · 덱 mm-t-s(s) → rc 1, 덱 없음", rc == 1 and "time_unit=ms" in out and "🔴" in out and not ds, out[-400:])
    rc, out, ds = case("match", {"units": "mm-t-s", "time_unit": "s"})
    check("표 s · 덱 mm-t-s → rc 0, 확인 줄", rc == 0 and "[EndTimeTable] time_unit=s — 덱 시간 단위와 같다" in out and ds, out[-400:])
    rc, out, ds = case("unknown", {"time_unit": "s"}, {"rho1": "5.0", "rho2": "20.0"})
    check("판정 안 되는 덱 → 경고만, rc 0", rc == 0 and "WARNING [EndTimeTable] 표 time_unit=s" in out and ds, out[-400:])
    rc, out, ds = case("none", {"units": "mm-t-s"})
    check("메타에 time_unit 없음 → 예전 그대로(단위 줄 없음), rc 0", rc == 0 and "time_unit" not in out and ds, out[-400:])


def test_minimum_model(tmp):
    print("[8] MinimumModel Fast 세 각도 (있을 때만)")
    if not MINI.exists():
        print("  (Examples/MinimumModel.k 없음 — 건너뜀)")
        return
    w3 = [(30.0, -10.0, 5.0), (0.0, 0.0, 60.0), (-20.0, 25.0, -8.0)]
    s = Path(tmp, "mm_spin")
    rc, out = run(s, option("MinimumModel.k", ANG3, "Plane,0,0,0,10,10,2", w=w3, height=1500, tfinal=0.005, dt=1e-5),
                  "MinimumModel.k", MINI)
    check("MinimumModel: rc 0", rc == 0, out[-400:])
    # 기대 중심: 같은 덱을 KMM 으로 읽어 DropAttitude 와 같이 바운딩 박스 가운데를 원점으로 옮긴 뒤 강체 질량특성의 무게중심
    with contextlib.redirect_stdout(io.StringIO()):
        import KooMeshModifier as K
        from KooCAEManager.KooRigidBodyProperties import compute_rigid_body
        g = K.KooMeshModifier()
        g.SetCurrentDirectory(str(s))
        g.inputFileName = "MinimumModel.k"
        g.ImportBaseFile()
        bb = g.dynaImporter.nodeManager.GetBoundingBox()
        g.dynaImporter.nodeManager.MoveNodes(-(bb[0] + bb[3]) / 2.0, -(bb[1] + bb[4]) / 2.0, -(bb[2] + bb[5]) / 2.0)
        com = np.asarray(compute_rigid_body(g.dynaImporter, log=lambda *_: None)["com"])
    global H
    h0, H = H, 1500.0
    try:
        for k, (p, ang, w) in enumerate(zip(angle_decks(s, "MinimumModel"), ANG3, w3), 1):
            card_vs_inputs(f"MinimumModel 각도 {k}", p.read_bytes(), ang, w, com, max_nid=10 ** 9)
    finally:
        H = h0


def main():
    tmp = tempfile.mkdtemp(prefix="drop_rigid_spin_")
    test_parse(tmp)
    test_zero(tmp)
    test_spin_fast(tmp)
    test_spin_rigidwall(tmp)
    test_errors(tmp)
    test_units_unknown(tmp)
    test_time_unit(tmp)
    test_minimum_model(tmp)
    print()
    if FAILS:
        print("FAIL %d 건 (작업 폴더 %s 를 남긴다)" % (len(FAILS), tmp))
        for x in FAILS:
            print("  -", x)
        sys.exit(1)
    shutil.rmtree(tmp, ignore_errors=True)
    print("ALL PASS")


if __name__ == "__main__":
    main()
