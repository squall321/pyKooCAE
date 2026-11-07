# KMM RIGID_DROP_ENDTIME 모드 — 덱 질량특성·외곽형상으로 강체 낙하 사전 해석을 돌려 각도별 종료 시간 표·충돌 상태 표를 쓰는 모듈
"""
흐름 (KooMeshModifier 가 덱을 읽은 뒤 부른다 — 기본 .k 는 쓰지 않는다)
  1. **RigidDropEndtime 블록 → parse_option_lines(키 이름 전체 일치, 모르는 키·틀린 값은 ValueError → KMM rc 1)
  2. 지난 실행의 산출 다섯 개를 지운다(실패한 실행 뒤에 옛 표가 남아 KCR 이 읽지 않게).
  3. KooRigidBodyProperties.compute_rigid_body → <base>_rigidbody.json · <base>_surface.obj · <base>_hull.obj
  4. KooRigidDropPresim.make_body(SI 값) → run_presim(각도 × 반발계수, strong_contact, return_impacts=True)
  5. <base>_endtime.csv(KooEndTimeTable.write_endtime_table) · <base>_impacts.csv(덱 단위, PLAN §5)
     메타: deck·units·time_unit·height·v0(√(2gh), 덱 단위)·restitution·friction·gravity·endtime_rule·strong_contact(중력 끔만)·
     margin_ms·t_sep_ms·n_angles.
     표 칸에 엔진이 주는 reach(덱 길이)·n_unresolved 를 더한다. 엔진의 나머지 칸(strong_end_ms·strong_vn_max·e 별 칸)은 그대로
     옮긴다(*_ms 칸은 ms 그대로). rigidbody.json 에 사전 해석 요약("presim")을 더해 다시 쓴다.
  산출은 모두 out_dir(= KMM 작업 폴더)에 쓴다. KCR 은 *Inputfile 로 템플릿 절대 경로를, 둘째 인자로 작업 폴더를 주므로
  덱 옆에 쓰면 안 된다. base = 덱 파일 이름에서 확장자를 뺀 것.

중력: PresimGravity 기본 0 — DROP_ATTITUDE 덱(초기 속도만, 중력 없음)과 같은 조건이다(사용자 결정 11-07). 이때 사전 해석은
2차 묶음 뒤에도 이어 돌고, ENDTIM 은 접근 속도가 PresimStrongContact·v0(기본 0.3) 이상인 마지막 재접촉 묶음의 끝 + MarginMs 다.
그런 묶음이 없으면 1차 묶음 끝 + MarginMs 다(v133, 메타 endtime_rule=last_strong). 꼭짓점마다 갈라져 오는 슬랩다운 뒷부분을
담고, 오래 돈 뒤의 약한 스침은 뺀다. 1 이면 중력을 켜고 v132 규칙(첫 재접촉 묶음 끝, endtime_rule=first_recontact)을 쓴다.
무게중심이 1 mm 넘게 떴다 닿은 재착지는 2차 충격으로 세지 않고, PresimStrongContact 는 무시한다(직접 주면 경고 한 줄).
로그 줄머리는 영어 표지 [RigidDropEndtime] 다(컴파일본은 한글 글자를 찾기 어렵다).
"""
import csv
import difflib
import inspect
import math
import os
import time

import numpy as np

_TAG = "[RigidDropEndtime]"
# 키(소문자) → 옵션 이름. 키는 줄의 첫 쉼표 앞 글 전체가 같을 때만 맞는다(부분 문자열 금지)
KEYS = {"height": "Height", "anglefile": "AngleFile", "fibonacci": "Fibonacci", "angle": "Angle",
        "restitution": "Restitution", "friction": "Friction", "presimgravity": "PresimGravity",
        "marginms": "MarginMs", "excludepart": "ExcludePart", "units": "Units", "workers": "Workers",
        "presimdt": "PresimDt", "presimtmax": "PresimTMax", "presimstrongcontact": "PresimStrongContact"}
_REPEATABLE = ("Angle", "ExcludePart")
_SOURCES = ("AngleFile", "Fibonacci", "Angle")
SUFFIXES = {"rigidbody": "_rigidbody.json", "surface": "_surface.obj", "hull": "_hull.obj",
            "endtime": "_endtime.csv", "impacts": "_impacts.csv"}
# impact_rows(SI) → 덱 단위: 길이 · 속도(길이/시간) · 각속도(rad/시간)
_LEN, _VEL, _ANG = ("contact_x", "contact_y", "contact_z"), ("vx", "vy", "vz", "vn_contact", "v0"), ("wx", "wy", "wz")


def default_workers():
    """min(8, 이 프로세스가 쓸 수 있는 CPU 수)."""
    try:
        n = len(os.sched_getaffinity(0))
    except AttributeError:
        n = os.cpu_count() or 1
    return max(1, min(8, n))


def default_options(cur_dir="."):
    """옵션 기본값. GivenKeys 는 블록에 직접 준 키 이름이다(parse_option_lines 가 채운다 — 중력 켬 + PresimStrongContact 경고)."""
    return {"Height": None, "AngleFile": None, "Fibonacci": None, "Angle": [], "Restitution": [0.1, 0.3, 0.5],
            "Friction": 0.5, "PresimGravity": 0, "MarginMs": 1.0, "ExcludePart": [], "Units": None,
            "Workers": default_workers(), "PresimDt": 1e-5, "PresimTMax": 1.0, "PresimStrongContact": 0.3,
            "OutDir": os.path.abspath(cur_dir), "GivenKeys": []}


def _float(key, text):
    try:
        v = float(text)
    except ValueError:
        raise ValueError(f"{key}: '{text}' 는 숫자가 아니다 (bad number)") from None
    if not math.isfinite(v):
        raise ValueError(f"{key}: '{text}' 는 유한한 수가 아니다 (bad number)")
    return v


def _int(key, text):
    v = _float(key, text)
    if not v.is_integer():
        raise ValueError(f"{key}: '{text}' 는 정수가 아니다 (bad number)")
    return int(v)


def read_angle_file(path):
    """AngleFile csv → [(이름, roll, pitch, yaw)] 도. 머리 줄(name,roll,pitch,yaw — 차례 무관)은 있어도 없어도 되고,
    없으면 칸 차례가 name,roll,pitch,yaw 다. '#' 줄·빈 줄은 건너뛴다. yaw 가 없거나 비면 0. 틀리면 ValueError."""
    if not os.path.isfile(path):
        raise ValueError(f"AngleFile 이 없다: {path} (AngleFile not found)")
    cols, out = None, []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for n, rec in enumerate(csv.reader(f), start=1):
            cells = [c.strip() for c in rec]
            if not any(cells) or cells[0].startswith("#"):
                continue
            if cols is None and {"roll", "pitch"} <= {c.lower() for c in cells}:
                cols = {c.lower(): i for i, c in enumerate(cells)}
                continue
            idx = cols or {"name": 0, "roll": 1, "pitch": 2, "yaw": 3}
            get = lambda k: cells[idx[k]] if k in idx and idx[k] < len(cells) else ""  # noqa: E731
            where = f"AngleFile {path} {n}번째 줄"
            if not get("roll") or not get("pitch"):
                raise ValueError(f"{where}: roll·pitch 가 없다 — name,roll,pitch,yaw (bad AngleFile row)")
            out.append((get("name") or f"A{len(out) + 1:04d}", _float(where + " roll", get("roll")),
                        _float(where + " pitch", get("pitch")), _float(where + " yaw", get("yaw")) if get("yaw") else 0.0))
    if not out:
        raise ValueError(f"AngleFile {path} 에 각도 줄이 없다 (no angles)")
    return out


def parse_option_lines(lines, cur_dir):
    """**RigidDropEndtime 블록의 줄들 → 옵션 dict(기본값 채움). 키는 대소문자 무관·이름 전체 일치, 빈 줄·'$'·'#' 줄은 건너뛴다.
    모르는 키(가까운 키 이름을 알려 준다), Height 없음·0 이하, 각도 출처(AngleFile·Fibonacci·Angle 줄)가 없거나 둘 이상, 숫자
    오류, 없는 AngleFile 은 ValueError — 새 블록이라 모르는 키를 넘겨 줄 까닭이 없다(오타가 기본값으로 조용히 돈다).
    AngleFile 은 작업 폴더(cur_dir) 기준 절대 경로로 바꾼다(KMM 은 덱을 읽으며 chdir 한다)."""
    from KooCAEManager.KooRigidBodyProperties import UNIT_SYSTEMS
    opt, seen = default_options(cur_dir), set()
    for raw in lines:
        line = str(raw).strip()
        if not line or line[0] in "$#":
            continue
        key, _, rest = line.partition(",")
        name = KEYS.get(key.strip().lower())
        if name is None:
            near = difflib.get_close_matches(key.strip().lower(), list(KEYS), n=1, cutoff=0.6)
            hint = f"did you mean '{KEYS[near[0]]}'?" if near else f"키: {', '.join(KEYS.values())}"
            raise ValueError(f"모르는 키 '{key.strip()}' — {hint} (unknown key)")
        vals = [v.strip() for v in rest.split(",")] if rest.strip() else []
        if not vals or not any(vals):
            raise ValueError(f"{name}: 값이 없다 — {name},<값> (value missing)")
        if name in seen and name not in _REPEATABLE:
            raise ValueError(f"{name} 가 두 번 있다 — 한 번만 줄 것 (duplicate key)")
        seen.add(name)
        if name == "Height":
            opt[name] = _float(name, vals[0])
        elif name == "AngleFile":
            opt[name] = os.path.abspath(os.path.join(cur_dir, rest.strip()))
        elif name in ("Fibonacci", "Workers"):
            opt[name] = _int(name, vals[0])
            if opt[name] < 1:
                raise ValueError(f"{name}: 1 이상이어야 한다 ({vals[0]})")
        elif name == "Angle":
            if len(vals) != 4 or not vals[0]:
                raise ValueError(f"Angle: '{line}' — Angle,<이름>,<roll>,<pitch>,<yaw> (bad Angle line)")
            opt[name].append((vals[0], _float("Angle roll", vals[1]), _float("Angle pitch", vals[2]),
                              _float("Angle yaw", vals[3])))
        elif name == "Restitution":
            opt[name] = [_float(name, v) for v in vals if v]
            if not all(0.0 <= e <= 1.0 for e in opt[name]):
                raise ValueError(f"Restitution: 0~1 사이여야 한다 ({rest.strip()})")
        elif name == "ExcludePart":
            opt[name].extend(_int(name, v) for v in vals if v)
        elif name == "PresimGravity":
            opt[name] = _int(name, vals[0])
            if opt[name] not in (0, 1):
                raise ValueError(f"PresimGravity: 0(끔) 또는 1(켬) ({vals[0]})")
        elif name == "Units":
            if vals[0] not in UNIT_SYSTEMS:
                raise ValueError(f"Units: '{vals[0]}' — {', '.join(UNIT_SYSTEMS)} 가운데 하나 (unknown units)")
            opt[name] = vals[0]
        else:   # Friction · MarginMs · PresimDt · PresimTMax · PresimStrongContact(v0 배수 문턱)
            opt[name] = _float(name, vals[0])
            if opt[name] < 0 or (name in ("PresimDt", "PresimTMax", "PresimStrongContact") and opt[name] == 0):
                raise ValueError(f"{name}: {'양수' if name.startswith('Presim') else '0 이상'}여야 한다 ({vals[0]})")
    if opt["Height"] is None:
        raise ValueError("Height 가 없다 — 낙하 높이(덱 길이 단위)를 줄 것 (Height missing)")
    if not opt["Height"] > 0:
        raise ValueError(f"Height 는 양수여야 한다 ({opt['Height']}) (Height must be positive)")
    given = [s for s in _SOURCES if opt[s]]
    if len(given) != 1:
        raise ValueError(f"각도 출처는 AngleFile·Fibonacci·Angle 줄 가운데 꼭 하나다 — 지금 {given or '없음'} "
                         f"(angle source: need exactly one)")
    if opt["PresimTMax"] <= opt["PresimDt"]:
        raise ValueError(f"PresimTMax({opt['PresimTMax']}) 는 PresimDt({opt['PresimDt']}) 보다 커야 한다")
    if opt["AngleFile"]:
        read_angle_file(opt["AngleFile"])   # 덱을 읽기 전에 틀린 파일을 알린다
    opt["GivenKeys"] = sorted(seen)
    return opt


def resolve_angles(opt):
    """옵션의 각도 출처 하나 → [(이름, roll, pitch, yaw)]. 이름이 겹치면 ValueError(표를 이름으로 찾는 쪽이 헷갈린다)."""
    from KooCAEManager.KooEndTimeTable import fibonacci_angles
    if opt.get("AngleFile"):
        angles, src = read_angle_file(opt["AngleFile"]), f"AngleFile {opt['AngleFile']}"
    elif opt.get("Fibonacci"):
        angles, src = fibonacci_angles(int(opt["Fibonacci"])), f"Fibonacci {int(opt['Fibonacci'])}"
    elif opt.get("Angle"):
        angles, src = list(opt["Angle"]), f"Angle lines {len(opt['Angle'])}"
    else:
        raise ValueError("각도 출처가 없다 (angle source: need exactly one)")
    names = [a[0] for a in angles]
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        raise ValueError(f"각도 이름이 겹친다: {dup[:10]} (duplicate angle names)")
    return angles, src


def impacts_to_deck(impacts, length_to_m, time_to_s):
    """impact_rows(SI: m, m/s, rad/s) → 덱 단위 줄 + endtim_k(덱 시간 단위, 0.1 ms 올림). 시간 칸(_ms)·각도·법선은 그대로."""
    from KooCAEManager.KooRigidDropPresim import endtim_from_ms
    out = []
    for r in impacts:
        d = dict(r)
        d.update({k: r[k] / length_to_m for k in _LEN})
        d.update({k: r[k] * time_to_s / length_to_m for k in _VEL})
        d.update({k: r[k] * time_to_s for k in _ANG})
        d["endtim_k"] = endtim_from_ms(r["tfinal_k_ms"], time_to_s)
        out.append(d)
    return out


def table_rows(rows, length_to_m):
    """run_presim 줄 → 표 줄: CORE 칸, 그다음 reach(엔진 reach_m 을 덱 길이로)·n_unresolved(엔진이 주면), 그다음 엔진 줄의
    나머지 칸(strong_end_ms·strong_vn_max·e 별 칸)을 엔진 차례대로. 바꾸는 것은 reach 뿐이다(*_ms 칸은 ms 그대로)."""
    from KooCAEManager.KooEndTimeTable import CORE_COLUMNS
    out = []
    for r in rows:
        d = {k: r[k] for k in CORE_COLUMNS if k in r}
        if "reach_m" in r:
            d["reach"] = r["reach_m"] / length_to_m
        if "n_unresolved" in r:
            d["n_unresolved"] = r["n_unresolved"]
        d.update({k: v for k, v in r.items() if k not in d and k != "reach_m"})
        out.append(d)
    return out


def run_rigid_drop_endtime(options, dyna_importer, deck_path, out_dir, log=print):
    """KMM 이 읽은 덱 → 산출 다섯 개(out_dir/<base>_*). → {"paths": {종류: 경로}, "summary": 사전 해석 요약}.
    틀린 입력·사전 해석 실패는 ValueError·RuntimeError(KMM 이 rc 1 로 바꾼다), pybullet 이 없으면 ImportError."""
    from KooCAEManager import KooEndTimeTable as T
    from KooCAEManager.KooRigidBodyProperties import compute_rigid_body, write_obj, write_rigid_body_json
    from KooCAEManager.KooRigidDropPresim import G, MAX_HULL_VERTICES, make_body, run_presim

    t0 = time.time()
    base = os.path.splitext(os.path.basename(deck_path))[0]
    os.makedirs(out_dir, exist_ok=True)
    paths = {k: os.path.join(out_dir, base + s) for k, s in SUFFIXES.items()}
    for p in paths.values():   # 지난 실행의 산출을 먼저 지운다 — 이번 실행이 실패해도 옛 표를 KCR 이 읽지 않게
        if os.path.exists(p):
            os.remove(p)
            log(f"{_TAG} REMOVED stale {p}")
    opt = dict(default_options(out_dir), **{k: v for k, v in options.items() if v is not None})
    angles, src = resolve_angles(opt)
    import pybullet   # 덱을 다 읽은 뒤 사전 해석에서 죽지 않게 먼저 확인 — 부모가 읽어 두면 작업자(fork)가 다시 읽지 않는다
    log(f"{_TAG} pybullet {getattr(pybullet, '__file__', '?')}")
    t_sep_ms = inspect.signature(run_presim).parameters["t_sep_ms"].default   # 엔진 기본값을 그대로 쓰고 메타에 남긴다
    gravity_on = bool(opt["PresimGravity"])
    # ENDTIM 규칙(v133): 중력 끔은 문턱(PresimStrongContact·v0) 넘는 마지막 재접촉 묶음, 중력 켬은 v132 첫 재접촉 묶음
    rule = "first_recontact" if gravity_on else "last_strong"
    log(f"{_TAG} START deck={deck_path} out_dir={out_dir} angles={len(angles)} ({src}) height={opt['Height']:g} "
        f"restitution={opt['Restitution']} friction={opt['Friction']:g} gravity={int(opt['PresimGravity'])} "
        f"strong_contact={opt['PresimStrongContact']:g} margin_ms={opt['MarginMs']:g} workers={opt['Workers']}")
    if gravity_on and "PresimStrongContact" in opt["GivenKeys"]:
        log(f"{_TAG} WARNING PresimStrongContact ignored with PresimGravity 1 (first re-contact rule)")

    rb = compute_rigid_body(dyna_importer, exclude_pids=opt["ExcludePart"], units=opt["Units"], log=log)
    u = rb["units"]
    length_to_m, time_to_s = u["length_to_m"], u["time_to_s"]
    s, h = rb["surface"], rb["hull"]
    write_obj(paths["surface"], s["vertices"], s["faces"], s["groups"],
              header=[f"{base} exterior surface per part (deck coordinates, {u['name']})"])
    write_obj(paths["hull"], h["vertices"], h["faces"], header=[f"{base} convex hull (deck coordinates, {u['name']})"])
    write_rigid_body_json(paths["rigidbody"], rb)   # 사전 해석 전에 한 번 — 사전 해석이 실패해도 질량특성은 남는다
    if h["n_vertices"] > MAX_HULL_VERTICES:
        raise ValueError(f"볼록 껍질 꼭짓점 {h['n_vertices']}개가 pybullet 한도 {MAX_HULL_VERTICES} 를 넘는다 (hull too large)")

    si = rb["si"]
    body = make_body(si["mass_kg"], si["com_m"], si["inertia_com_kgm2"], si["hull_vertices_m"])
    height_m = opt["Height"] * length_to_m
    t1 = time.time()
    rows, impacts = run_presim(body, angles, height_m, restitutions=opt["Restitution"], friction=opt["Friction"],
                               gravity_on=gravity_on, margin_ms=opt["MarginMs"], dt=opt["PresimDt"],
                               t_max=opt["PresimTMax"], workers=opt["Workers"], time_to_s=time_to_s, log=log,
                               return_impacts=True, strong_contact=opt["PresimStrongContact"])
    t2 = time.time()

    # v0 = DROP_ATTITUDE 덱의 낙하 속도 √(2gh), 덱 단위 — 표를 쓰는 쪽이 자기 높이·속도와 맞는지 본다
    v0 = math.sqrt(2.0 * G * height_m) * time_to_s / length_to_m
    # endtime_rule 이 없는 표는 v132 다(KCR 이 가른다). strong_contact 는 쓰인 때(중력 끔)만 적는다
    meta = {"deck": deck_path, "units": u["name"], "time_unit": "s" if time_to_s == 1.0 else "ms",
            "height": opt["Height"], "v0": v0, "restitution": ",".join(format(e, "g") for e in opt["Restitution"]),
            "friction": opt["Friction"], "gravity": int(gravity_on), "endtime_rule": rule,
            **({} if gravity_on else {"strong_contact": opt["PresimStrongContact"]}),
            "margin_ms": opt["MarginMs"], "t_sep_ms": t_sep_ms, "n_angles": len(angles)}
    table = table_rows(rows, length_to_m)
    T.write_endtime_table(paths["endtime"], table, meta)
    T.write_csv_table(paths["impacts"], impacts_to_deck(impacts, length_to_m, time_to_s), T.IMPACT_COLUMNS, meta,
                      T.IMPACTS_FORMAT)

    tf = np.array([r["tfinal_ms"] for r in rows])
    ends = np.array([r["endtim"] for r in rows])
    reach = [float(r["reach"]) for r in table if r.get("reach") is not None and math.isfinite(r["reach"])]
    unresolved = [int(r["n_unresolved"]) for r in table if r.get("n_unresolved") is not None]
    excl = [f"{x['pid']}({x['name']}, {x['reason']}, mass {x.get('mass', 0.0):.4g}, {x.get('mass_fraction', 0.0):.2%})"
            for x in rb["excluded_parts"]]
    summary = {"params": {"height": opt["Height"], "height_m": height_m, "v0": v0, "restitution": list(opt["Restitution"]),
                          "friction": opt["Friction"], "gravity": int(gravity_on), "endtime_rule": rule,
                          "strong_contact": opt["PresimStrongContact"], "margin_ms": opt["MarginMs"],
                          "t_sep_ms": t_sep_ms, "dt_s": opt["PresimDt"], "t_max_s": opt["PresimTMax"],
                          "workers": opt["Workers"], "angle_source": src, "exclude_parts": list(opt["ExcludePart"])},
               "n_angles": len(rows), "n_impacts": len(impacts),
               "classes": {c: sum(r["class"] == c for r in rows) for c in ("slapdown", "rebound", "none")},
               "tfinal_ms": {"min": float(tf.min()), "median": float(np.median(tf)), "max": float(tf.max())},
               "endtim": {"min": float(ends.min()), "max": float(ends.max()), "time_unit": meta["time_unit"]},
               "reach_max": max(reach) if reach else None,
               "n_unresolved_total": sum(unresolved) if unresolved else None,
               "excluded_parts": excl,
               "wall_time_s": {"rigid_body": round(t1 - t0, 3), "presim": round(t2 - t1, 3),
                               "total": round(time.time() - t0, 3)}}
    rb["presim"] = summary
    write_rigid_body_json(paths["rigidbody"], rb)
    for k in SUFFIXES:
        log(f"{_TAG} WROTE {paths[k]}")
    log(f"{_TAG} DONE angles={len(rows)} impacts={len(impacts)} rule={rule} classes={summary['classes']} "
        f"tfinal_ms={tf.min():.2f}/{np.median(tf):.2f}/{tf.max():.2f} (min/median/max) "
        f"endtim={ends.min():g}..{ends.max():g} {meta['time_unit']} reach_max={summary['reach_max']} "
        f"unresolved={summary['n_unresolved_total']} excluded=[{'; '.join(excl) or 'none'}] "
        f"wall={summary['wall_time_s']['total']:.1f}s")
    return {"paths": paths, "summary": summary}
