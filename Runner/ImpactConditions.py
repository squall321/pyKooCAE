# 강체 낙하 사전 해석의 충돌 직전 상태(<base>_impacts.csv)에서 대표 충격 조건을 골라 FEM DOE 로 만들고, 결과를 원래 각도로 되돌려 붙이는 모듈
"""
angle_source.source_type = "impact_conditions" — KooChainRun prepare(CumulativeDesigner.save_runner_config)가 부른다.

  1. 사전 해석. 템플릿에 KMM RIGID_DROP_ENDTIME(Fibonacci,<num_directions>, PresimGravity=gravity, 기본 켬)을 EndTimePresim 과
     같은 방식(러너와 같은 KMM·apptainer 감싸기·작업 폴더를 둘째 인자로)으로 <output_dir>/impact_conditions/presim/ 에서 돌려
     <base>_impacts.csv(충돌 묶음마다 충돌 직전 상태, 덱 단위)와 <base>_rigidbody.json(바운딩 박스)을 받는다.
     table 을 주면 그 impacts.csv(옆에 <base>_rigidbody.json)를 쓰고 KMM 을 돌리지 않는다.
  2. 고르기. 후보 = k ∈ impacts 인 줄. 자세·속도·각속도가 같은 줄은 한 상태로 묶는다(k=1 은 e 와 무관한 같은 상태가 e 마다 있다 —
     묶지 않으면 심각도 몫을 같은 FEM 입력이 나눠 먹는다).
     특징 f = [nx, ny, nz, vn_contact/v0, |(vx,vy)|/v0, (RotMat(att)·w)·L/v0] (무차원, L = 바운딩 박스 대각선의 절반).
     심각도 = J_over_mv0 × vn_contact/v0 (충격량 × 접근 속도 — 충격 에너지 m_eff·vn² 대용, 같은 상태로 묶인 줄들 가운데 최대).
     ceil(count·severity_fraction) 개는 심각도 순위를 내려가며 고르되, 이미 고른 심각도 상태와 f 거리가
     severity_min_distance(기본 0.2) 보다 가까운 상태는 건너뛴다(비최대 억제). 값이 0.1% 안으로 같은 묶음은 최원점 차례로
     돈다(같은 값이 많을 때 파일 순서로 자르면 한쪽 방향에 몰린다). 순위가 다 떨어지면 남은 몫은 덮기로 간다(경고).
     나머지는 이미 고른 점에서 시작하는 f 공간 최원점 샘플링. 그 밖의 같은 값은 파일에서 먼저 나온 상태가
     먼저다. 모든 후보는 가장 가까운 대표(유클리드, 같으면 앞 DOE)에 묶는다.
  3. DOE. 대표 하나 = DOE 하나(1 스텝 DROP, 이름 IC001…). roll/pitch/yaw = att, InitialVelocity = v, RigidAngularVelocity = w
     (바닥 좌표, 덱 단위), Height 0. 종료 시간은 impact_conditions/endtime.csv 를 EndTimeTable 로 쓴다(같은 상태 줄들의 endtim_k 최대).
  4. 기록. impact_conditions/index.json, runner_config scenario.doe_impact_meta(보기용)·doe_impact_state(러너 입력)·
     endtime_tables·doe_endtim.

러너 쪽(누적·대규모·배치)은 impact_kwargs()/impact_state_for_step() 으로 runner_config 에서만 읽는다.
harvest_impact_map() 은 `KooChainRun harvest --impact-map` — 완료 DOE 결과를 index.json assignments 로 원래 각도마다 붙인다.
KCR Nuitka 빌드는 Runner 패키지만 넣으므로 occProject(KooEndTimeTable)를 import 하지 않는다. RotMat 은 같은 식을 math 로 쓴다.
"""
import csv
import json
import math
import os
import subprocess

from Runner.EndTimePresim import (OPTION_FILE, STDOUT_FILE, _same_direction, _tail, build_option_text, drop_direction,
                                  run_kmm)

MARKER = "[IMPACT_CONDITIONS_FAILED]"
INDEX_FORMAT = "impact_conditions/index v1"
ENDTIME_FORMAT = "rigid_drop_endtime/endtime v1"
DEFAULTS = {"num_directions": 20000, "restitution": [0.1, 0.3, 0.5], "friction": 0.5, "gravity": True,
            "margin_ms": 1.0, "exclude_parts": [], "workers": 8, "count": 100, "impacts": [1, 2],
            "severity_fraction": 0.5, "severity_min_distance": 0.2, "table": None}
TEXT_COLUMNS = ("name", "class", "contact_type")
FLOAT_COLUMNS = ("roll", "pitch", "yaw", "e", "nx", "ny", "nz", "att_roll", "att_pitch", "att_yaw",
                 "vx", "vy", "vz", "wx", "wy", "wz", "vn_contact", "v0", "J_over_mv0", "endtim_k")
REQUIRED_COLUMNS = TEXT_COLUMNS + ("k",) + FLOAT_COLUMNS
SEVERITY = "J_over_mv0·vn_contact/v0"   # 사용자 결정 11-07 — 충격량 × 접근 속도(충격 에너지 m_eff·vn² 대용)
SEVERITY_TIE_REL = 1e-3   # 심각도 경계값과 이 비율 안이면 같은 심각도 — 그 묶음 안에서는 최원점으로 고른다
FEATURES = ["nx", "ny", "nz", "vn_contact/v0", "|(vx,vy)|/v0",
            "(RotMat(att)·w)_x·L/v0", "(RotMat(att)·w)_y·L/v0", "(RotMat(att)·w)_z·L/v0"]
RISK_COLUMNS = ["angle", "roll", "pitch", "yaw", "dx", "dy", "dz", "e", "k", "doe", "distance",
                "peak_stress", "worst_pid", "worst_part", "ratio"]
SUMMARY_COLUMNS = ["angle", "roll", "pitch", "yaw", "dx", "dy", "dz", "peak_stress", "worst_pid", "worst_part", "ratio",
                   "governing_e", "governing_k", "governing_doe", "n_impacts", "n_missing"]


class ImpactConditionsError(RuntimeError):
    """충격 조건 DOE 준비·결과 모음 실패 — prepare·harvest 를 멈춘다."""

    def __init__(self, msg):
        super().__init__(f"{MARKER} {msg}")


def impact_options(raw):
    """angle_source.impact_conditions → 기본값을 채운 dict. 모르는 키는 경고만, 틀린 값은 멈춘다."""
    raw = {} if raw is None else raw
    if not isinstance(raw, dict):
        raise ImpactConditionsError(f"angle_source.impact_conditions 는 객체여야 한다: {raw!r} (bad value)")
    for k in raw:
        if k not in DEFAULTS:
            print(f"⚠️  angle_source.impact_conditions.{k}: 모르는 키라 무시한다 (unknown key, ignored)")
    o = {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS}}

    def bad(key):
        raise ImpactConditionsError(f"angle_source.impact_conditions.{key} 값이 틀렸다: {o[key]!r} (bad value)")

    real = lambda x: not isinstance(x, bool) and isinstance(x, (int, float)) and math.isfinite(x)  # noqa: E731
    whole = lambda x: not isinstance(x, bool) and isinstance(x, int)  # noqa: E731
    for key in ("num_directions", "count", "workers"):
        if not (whole(o[key]) and o[key] >= 1):
            bad(key)
    for key, hi in (("friction", None), ("margin_ms", None), ("severity_fraction", 1.0), ("severity_min_distance", None)):
        if not (real(o[key]) and o[key] >= 0 and (hi is None or o[key] <= hi)):
            bad(key)
    for key, ok in (("restitution", lambda x: real(x) and 0.0 <= x <= 1.0), ("impacts", lambda x: whole(x) and x >= 1),
                    ("exclude_parts", whole)):
        o[key] = list(o[key]) if isinstance(o[key], list) else [o[key]]
        if not all(ok(x) for x in o[key]) or (key != "exclude_parts" and not o[key]):
            bad(key)
    if not isinstance(o["gravity"], bool):
        bad("gravity")
    if o["table"] is not None and not (isinstance(o["table"], str) and o["table"].strip()):
        bad("table")
    return o


def rot_from_euler(roll, pitch, yaw=0.0):
    """KMM DropAttitude 의 RotMat = Rz(-yaw)·Ry(-pitch)·Rx(-roll) — 바닥 좌표 벡터 → 덱 좌표 (KooEndTimeTable 과 같은 식)."""
    a, b, c = (-math.radians(float(v)) for v in (roll, pitch, yaw))
    rx = ((1.0, 0.0, 0.0), (0.0, math.cos(a), -math.sin(a)), (0.0, math.sin(a), math.cos(a)))
    ry = ((math.cos(b), 0.0, math.sin(b)), (0.0, 1.0, 0.0), (-math.sin(b), 0.0, math.cos(b)))
    rz = ((math.cos(c), -math.sin(c), 0.0), (math.sin(c), math.cos(c), 0.0), (0.0, 0.0, 1.0))

    def mul(p, q):
        return tuple(tuple(sum(p[i][k] * q[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return mul(rz, mul(ry, rx))


def features(r, L):
    """후보 줄 → 무차원 특징 8개 (FEATURES 순서). 각속도는 덱 좌표(RotMat(att)·w)로 바꿔 L/v0 를 곱한다."""
    v0 = r["v0"]
    m = rot_from_euler(r["att_roll"], r["att_pitch"], r["att_yaw"])
    w = (r["wx"], r["wy"], r["wz"])
    wd = [sum(m[i][j] * w[j] for j in range(3)) for i in range(3)]
    return [r["nx"], r["ny"], r["nz"], r["vn_contact"] / v0, math.hypot(r["vx"], r["vy"]) / v0] + [x * L / v0 for x in wd]


def _state_key(r, L):
    """FEM 입력(자세·속도·각속도)과 고르기 값(법선·vn)이 모두 같으면 같은 열쇠. 실제 표에서는 자세·속도·각속도가 같으면
    법선·vn 도 같다 — 둘 다 넣어 손으로 만든 표에서도 다른 상태를 합치지 않게 한다."""
    v0 = r["v0"]
    return (tuple(round(r[c], 6) for c in ("att_roll", "att_pitch", "att_yaw"))
            + tuple(round(r[c] / v0, 9) for c in ("vx", "vy", "vz", "vn_contact"))
            + tuple(round(r[c] * L / v0, 9) for c in ("wx", "wy", "wz"))
            + tuple(round(r[c], 9) for c in ("nx", "ny", "nz")))


def severity(r):
    """후보 줄의 심각도 = J_over_mv0 × vn_contact/v0 (SEVERITY)."""
    return r["J_over_mv0"] * r["vn_contact"] / r["v0"]


def select_conditions(cands, L, count, severity_fraction, min_distance=None):
    """후보 줄 → (대표 목록, 묶음).

    대표 = {"head": 상태의 첫 후보 번호, "group": 같은 상태 후보 번호들, "pick": "severity"|"coverage", "severity": 값,
            "source": 묶음에서 심각도가 가장 큰 줄 번호(보고하는 e·J 의 출처), "severity_rank": n|"coverage"}
    (고른 순서 = DOE 순서). 묶음 = 후보마다 (대표 번호 0-based, f 거리).
    """
    import numpy as np
    min_distance = DEFAULTS["severity_min_distance"] if min_distance is None else min_distance
    F = np.array([features(r, L) for r in cands], dtype=float)
    slot, groups = {}, []
    for i, r in enumerate(cands):
        key = _state_key(r, L)
        if key not in slot:
            slot[key] = len(groups)
            groups.append([])
        groups[slot[key]].append(i)
    heads = [g[0] for g in groups]
    FU = F[heads]
    sev = [max(severity(cands[i]) for i in g) for g in groups]   # 묶인 줄(k=1 은 e 마다 J 가 다르다) 가운데 최대
    n_target = min(count, len(heads))
    n_sev = min(math.ceil(round(count * severity_fraction, 9)), n_target)
    order = sorted(range(len(heads)), key=lambda j: (-sev[j], j))
    dmin = np.full(len(heads), np.inf)
    picked, kinds, chosen = [], [], set()

    def take(j, kind):
        nonlocal dmin
        picked.append(j)
        kinds.append(kind)
        chosen.add(j)
        dmin = np.minimum(dmin, np.linalg.norm(FU - FU[j], axis=1))

    def farthest(pool):   # pool 가운데 고른 점들에서 가장 먼 것 (같으면 pool 앞쪽)
        if not picked:
            return pool[0]
        dm = dmin[pool]
        return pool[int(np.argmax(dm))]

    if n_sev:
        # 심각도 순위를 내려가며 n_sev 개. 이미 고른 심각도 상태와 f 거리가 min_distance 보다 가까우면 건너뛴다(비최대 억제 —
        # 사용자 결정 11-07: 거의 같은 슬랩다운 수십 개가 몫을 다 먹지 않게). 값이 0.1% 안으로 같은 묶음은 최원점 차례로 돈다
        # (같은 값이 많을 때 파일 순서로 자르면 한쪽 방향의 이웃만 남는다). 순위가 다 떨어지면 남은 자리는 아래 덮기로 간다
        i = 0
        while i < len(order) and len(picked) < n_sev:
            lo = sev[order[i]] - SEVERITY_TIE_REL * abs(sev[order[i]])
            tied = []
            while i < len(order) and sev[order[i]] >= lo:
                tied.append(order[i])
                i += 1
            while len(picked) < n_sev:
                pool = [j for j in tied if j not in chosen and dmin[j] >= min_distance]
                if not pool:
                    break
                take(farthest(pool), "severity")
    if not picked and n_target:   # severity_fraction 0 — 심각도 1위에서 덮기를 시작한다
        take(order[0], "coverage")
    while len(picked) < n_target:
        dm = dmin.copy()
        dm[picked] = -1.0
        take(int(np.argmax(dm)), "coverage")   # 같으면 앞 상태
    best = np.full(len(cands), np.inf)
    arg = np.zeros(len(cands), dtype=int)
    for d, j in enumerate(picked):
        dist = np.linalg.norm(F - FU[j], axis=1)
        closer = dist < best   # 같으면 앞 DOE
        best[closer] = dist[closer]
        arg[closer] = d
    P = FU[picked]
    near = []
    for a in range(len(picked)):   # 가장 가까운 다른 대표까지 f 거리 (대표가 하나면 None)
        d = np.linalg.norm(P - P[a], axis=1)
        d[a] = np.inf
        near.append(float(d.min()) if len(picked) > 1 else None)
    reps = [{"head": heads[j], "group": groups[j], "pick": kind, "severity": sev[j],
             "source": max(groups[j], key=lambda i: (severity(cands[i]), -i)),
             "severity_rank": n + 1 if kind == "severity" else "coverage", "nearest_pick_distance": near[n]}
            for n, (j, kind) in enumerate(zip(picked, kinds))]
    return reps, [(int(a), float(b)) for a, b in zip(arg, best)]


def read_impacts_csv(path):
    """<base>_impacts.csv → (meta, rows). '#' 줄은 meta. 필요한 칸이 없거나 값이 틀리면 멈춘다."""
    meta, body = {}, []
    with open(path, newline="", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                k, _, v = line[1:].strip().partition("=")
                meta[k.strip()] = v.strip()
            elif line.strip():
                body.append(line)
    reader = csv.DictReader(body)
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ImpactConditionsError(f"충격 상태 표 {path} 에 칸 {missing} 이 없다 (missing columns)")
    rows = []
    for n, raw in enumerate(reader, start=1):
        try:
            r = {c: (raw[c] or "").strip() for c in TEXT_COLUMNS}
            r.update({c: float(raw[c]) for c in FLOAT_COLUMNS})
            r["k"] = int(float(raw["k"]))
        except (TypeError, ValueError):
            raise ImpactConditionsError(f"충격 상태 표 {path} {n}번째 줄의 숫자를 읽지 못했다 (bad number)") from None
        wrong = [c for c in FLOAT_COLUMNS if c != "e" and not math.isfinite(r[c])]
        wrong += [c for c in ("v0", "endtim_k") if not r[c] > 0.0]
        if wrong:
            raise ImpactConditionsError(f"충격 상태 표 {path} {n}번째 줄({r['name']} k={r['k']}) 값이 틀렸다: "
                                        f"{sorted(set(wrong))} (bad value)")
        rows.append(r)
    if not rows:
        raise ImpactConditionsError(f"충격 상태 표 {path} 에 줄이 없다 (no data rows)")
    return meta, rows


def half_diagonal(path):
    """<base>_rigidbody.json 의 bbox min/max → L = 대각선의 절반 (덱 길이 단위)."""
    try:
        with open(path, encoding="utf-8") as f:
            bb = json.load(f)["bbox"]
        lo, hi = [float(x) for x in bb["min"]], [float(x) for x in bb["max"]]
        L = 0.5 * math.sqrt(sum((b - a) ** 2 for a, b in zip(lo, hi)))
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise ImpactConditionsError(f"질량특성 {path} 에서 바운딩 박스(bbox.min/max)를 읽지 못했다: {e} "
                                    f"(bad rigidbody json)") from None
    if len(lo) != 3 or len(hi) != 3 or not (L > 0.0 and math.isfinite(L)):
        raise ImpactConditionsError(f"질량특성 {path} 의 바운딩 박스가 틀렸다: min={lo} max={hi} (bad rigidbody json)")
    return L


def _run_presim(opts, sim_params, environment, template, work):
    """옵션 파일을 쓰고 KMM 을 돌려 (impacts.csv, rigidbody.json) 경로를 돌려준다. 실패하면 멈춘다."""
    if not os.path.isfile(template):
        raise ImpactConditionsError(f"사전 해석할 템플릿(project.model_file)이 없다: {template} (template not found)")
    os.makedirs(work, exist_ok=True)
    base = os.path.splitext(os.path.basename(template))[0]
    outs = [os.path.join(work, f"{base}_impacts.csv"), os.path.join(work, f"{base}_rigidbody.json")]
    for p in outs:
        if os.path.exists(p):
            os.remove(p)   # 지난 prepare 의 산출을 이번 결과로 잘못 읽지 않게
    with open(os.path.join(work, OPTION_FILE), "w", encoding="utf-8") as f:
        f.write(build_option_text(template, None, sim_params.get("height", 1500), opts, fibonacci=opts["num_directions"]))
    timeout = environment.get("timeout_koomeshmodifier_seconds", 604800)
    print(f"  [impact_conditions] KMM RIGID_DROP_ENDTIME 실행 — 방향 {opts['num_directions']}개 × e {len(opts['restitution'])}개, "
          f"중력 {'켬' if opts['gravity'] else '끔'}, 작업 폴더 {work}")
    log_path = os.path.join(work, STDOUT_FILE)
    try:
        rc, _cmd, log_path = run_kmm(environment, work, timeout)
    except subprocess.TimeoutExpired:
        _tail(log_path)
        raise ImpactConditionsError(f"KMM 사전 해석이 {timeout}초 안에 끝나지 않았다 — 로그 {log_path} (timeout)") from None
    except OSError as e:
        raise ImpactConditionsError(f"KMM 을 실행하지 못했다: {e} — environment.koomeshmodifier_path·apptainer_sif·"
                                    f"apptainer_tmpdir 를 확인할 것 (cannot run KMM)") from None
    if rc != 0:
        _tail(log_path)
        raise ImpactConditionsError(f"KMM 사전 해석이 실패했다(종료 코드 {rc}) — 로그 {log_path} (KMM rc={rc})")
    for p in outs:
        if not os.path.isfile(p):
            _tail(log_path)
            raise ImpactConditionsError(f"KMM 이 끝났는데 {os.path.basename(p)} 가 없다: {p} — 로그 {log_path} "
                                        f"(output not written)")
    return outs


def _source_row(r):
    e = r["e"] if math.isfinite(r["e"]) else None
    return {"name": r["name"], "roll": r["roll"], "pitch": r["pitch"], "yaw": r["yaw"], "e": e, "k": r["k"],
            "class": r["class"], "contact_type": r["contact_type"], "vn_contact": r["vn_contact"],
            "J_over_mv0": r["J_over_mv0"],
            "v": [r["vx"], r["vy"], r["vz"]], "w": [r["wx"], r["wy"], r["wz"]],
            "att": [r["att_roll"], r["att_pitch"], r["att_yaw"]], "endtim_k": r["endtim_k"]}


def _write_index(path, index):
    """index.json — 앞부분은 들여 쓰고, assignments(수만 줄)는 한 줄에 하나씩 붙인다."""
    head = json.dumps({k: v for k, v in index.items() if k != "assignments"}, ensure_ascii=False, indent=1)
    rows = ",\n  ".join(json.dumps(a, ensure_ascii=False, separators=(",", ":")) for a in index["assignments"])
    with open(path, "w", encoding="utf-8") as f:
        f.write(head[:-2] + ',\n "assignments": [\n  ' + rows + "\n ]\n}\n")


def prepare_impact_conditions(opts, sim_params, environment, model_file, output_dir, scenario_dir):
    """사전 해석(또는 table) → 대표 고르기 → endtime.csv·index.json.

    → {"conditions": [{doe, name, roll, pitch, yaw, ...}], "index", "endtime_tables", "doe_endtim", "doe_impact_meta",
       "doe_impact_state"}. 실패는 ImpactConditionsError.
    """
    template = os.path.abspath(model_file)
    root = os.path.abspath(os.path.join(output_dir, "impact_conditions"))
    os.makedirs(root, exist_ok=True)
    if opts["table"]:
        impacts = opts["table"].strip()
        impacts = os.path.abspath(impacts if os.path.isabs(impacts) else os.path.join(scenario_dir, impacts))
        if not os.path.isfile(impacts):
            raise ImpactConditionsError(f"angle_source.impact_conditions.table 파일이 없다: {impacts} (table not found)")
        stem = impacts[:-len("_impacts.csv")] if impacts.endswith("_impacts.csv") else os.path.splitext(impacts)[0]
        rigid = stem + "_rigidbody.json"
        if not os.path.isfile(rigid):
            raise ImpactConditionsError(f"table 옆에 질량특성 {rigid} 가 없다 — KMM RIGID_DROP_ENDTIME 이 함께 쓴 파일을 "
                                        f"같은 폴더에 둘 것 (rigidbody json not found)")
        presim = {"table": impacts}
        print(f"  [impact_conditions] 사전 해석을 건너뛰고 주어진 충격 상태 표를 쓴다: {impacts}")
    else:
        impacts, rigid = _run_presim(opts, sim_params, environment, template, os.path.join(root, "presim"))
        presim = {k: opts[k] for k in ("num_directions", "restitution", "friction", "gravity", "margin_ms",
                                       "exclude_parts", "workers")}
        presim["height"] = sim_params.get("height", 1500)
    meta, rows = read_impacts_csv(impacts)
    L = half_diagonal(rigid)
    wanted = set(opts["impacts"])
    cands = [r for r in rows if r["k"] in wanted]
    if not cands:
        raise ImpactConditionsError(f"충격 상태 표 {impacts} 에 충돌 차수 {sorted(wanted)} 인 줄이 없다 (no candidates)")
    reps, assign = select_conditions(cands, L, opts["count"], opts["severity_fraction"], opts["severity_min_distance"])
    quota = min(math.ceil(round(opts["count"] * opts["severity_fraction"], 9)), len(reps))
    n_sev = sum(1 for r in reps if r["pick"] == "severity")
    if n_sev < quota:
        print(f"⚠️  impact_conditions: 심각도 순위를 끝까지 봤지만 서로 severity_min_distance({opts['severity_min_distance']:g}) "
              f"이상 떨어진 상태가 {n_sev}개뿐이다 — 심각도 몫 {quota} 가운데 나머지 {quota - n_sev}개는 고르게(최원점) 골랐다 "
              f"(severity quota not filled)")

    members = [0] * len(reps)
    for d, _ in assign:
        members[d] += 1
    conditions = []
    for d, rep in enumerate(reps, start=1):
        r = cands[rep["source"]]   # 자세·속도·각속도는 묶음 안에서 같다 — e·J 는 심각도를 낸 줄의 것
        conditions.append({"doe": d, "name": f"IC{d:03d}", "roll": r["att_roll"], "pitch": r["att_pitch"],
                           "yaw": r["att_yaw"], "velocity": [r["vx"], r["vy"], r["vz"]],
                           "rigid_angular_velocity": [r["wx"], r["wy"], r["wz"]], "height": 0.0,
                           "endtim": max(cands[i]["endtim_k"] for i in rep["group"]), "row": r,
                           "pick": rep["pick"], "severity": rep["severity"], "severity_rank": rep["severity_rank"],
                           "n_members": members[d - 1], "n_same_state": len(rep["group"]),
                           "nearest_pick_distance": rep["nearest_pick_distance"]})

    # 종료 시간 표 — KMM 은 자세의 낙하 방향으로 찾고, 0.01° 안에 여럿이면 endtim 최대를 쓴다
    table = os.path.join(root, "endtime.csv")
    with open(table, "w", newline="", encoding="utf-8") as f:
        f.write(f"# format={ENDTIME_FORMAT}\n# source=impact_conditions\n")
        if meta.get("time_unit"):
            f.write(f"# time_unit={meta['time_unit']}\n")
        f.write(f"# impacts={impacts}\n")
        w = csv.writer(f)
        w.writerow(["name", "roll", "pitch", "yaw", "endtim"])
        w.writerows([c["name"], c["roll"], c["pitch"], c["yaw"], c["endtim"]] for c in conditions)
    if not meta.get("time_unit"):
        print(f"⚠️  impact_conditions: {impacts} 에 time_unit 메타가 없어 KMM 이 표 단위를 확인하지 못한다 (no time_unit)")
    dirs = [drop_direction(c["roll"], c["pitch"], c["yaw"]) for c in conditions]
    doe_endtim, shared = {}, []
    for c, d in zip(conditions, dirs):
        same = [o for o, u in zip(conditions, dirs) if _same_direction(u, d)]
        doe_endtim[str(c["doe"])] = {"1": max(o["endtim"] for o in same)}
        if len(same) > 1:
            shared.append(f"{c['name']}↔{'·'.join(o['name'] for o in same if o is not c)}")
    if shared:
        print(f"⚠️  impact_conditions: 낙하 방향이 0.01° 안으로 같은 대표가 있다 — KMM 은 그들 가운데 endtim 최대를 쓴다: "
              f"{', '.join(shared[:10])}{' …' if len(shared) > 10 else ''}")

    index = {
        "format": INDEX_FORMAT,
        "source": {"deck": template, "impacts_csv": impacts, "rigidbody_json": rigid, "presim": presim,
                   "num_directions": len({(r["name"], r["roll"], r["pitch"], r["yaw"]) for r in rows}),
                   "impacts_meta": meta},
        "features": {"definition": FEATURES, "L": L,
                     "normalisation": "속도는 각 줄의 v0 로 나누고 각속도(덱 좌표)는 L/v0 를 곱한다 — 무차원, 유클리드 거리",
                     "selection": {"count": opts["count"], "impacts": opts["impacts"],
                                   "severity_fraction": opts["severity_fraction"],
                                   "severity": f"{SEVERITY} (같은 상태로 묶인 줄들 가운데 최대)",
                                   "severity_tie_rel": SEVERITY_TIE_REL,
                                   "severity_min_distance": opts["severity_min_distance"], "severity_quota": quota,
                                   "n_candidates": len(cands), "n_states": len({_state_key(r, L) for r in cands}),
                                   "n_severity": n_sev, "n_coverage": len(conditions) - n_sev}},
        "conditions": [{"doe": c["doe"], "name": c["name"], "source": _source_row(c["row"]),
                        "endtim": doe_endtim[str(c["doe"])]["1"], "n_members": c["n_members"],
                        "n_same_state": c["n_same_state"], "severity": c["severity"],
                        "severity_rank": c["severity_rank"], "nearest_pick_distance": c["nearest_pick_distance"]}
                       for c in conditions],
        "assignments": [],
    }
    for r, (a, dist) in zip(cands, assign):
        d = drop_direction(r["roll"], r["pitch"], r["yaw"])
        index["assignments"].append({"angle": r["name"], "roll": r["roll"], "pitch": r["pitch"], "yaw": r["yaw"],
                                     "dx": d[0], "dy": d[1], "dz": d[2],
                                     "e": r["e"] if math.isfinite(r["e"]) else None, "k": r["k"],
                                     "doe": a + 1, "distance": dist})
    index_path = os.path.join(root, "index.json")
    _write_index(index_path, index)
    print(f"✅ 충격 조건 DOE {len(conditions)}개 (심각도 상위 {n_sev} + 고르게 {len(conditions) - n_sev}) — 후보 "
          f"{len(cands)}줄, 상태 {index['features']['selection']['n_states']}개, L={L:.6g}. 기록 {index_path}")
    return {
        "conditions": conditions, "index": index_path,
        "endtime_tables": [{"template": template, "table": table, "source": "impact_conditions",
                            "angles": len(conditions)}],
        "doe_endtim": doe_endtim,
        "doe_impact_meta": {str(c["doe"]): {"name": c["name"],
                                            "source_angle": {k: c["row"][k] for k in ("name", "roll", "pitch", "yaw")},
                                            "e": _source_row(c["row"])["e"], "k": c["row"]["k"],
                                            "class": c["row"]["class"], "contact_type": c["row"]["contact_type"]}
                            for c in conditions},
        "doe_impact_state": {str(c["doe"]): {"1": {"velocity": c["velocity"],
                                                   "rigid_angular_velocity": c["rigid_angular_velocity"],
                                                   "height": c["height"]}} for c in conditions},
    }


def impact_state_for_step(config, doe, step):
    """runner_config scenario.doe_impact_state 에서 이 DOE(1-based)·스텝의 충격 상태. 없으면 None."""
    table = ((config or {}).get("scenario") or {}).get("doe_impact_state") or {}
    return (table.get(str(doe)) or {}).get(str(step))


def impact_kwargs(config, doe, step):
    """build_drop_attitude_config 에 넘길 충격 조건 인자 — 없으면 {} 라 예전 출력 그대로다."""
    s = impact_state_for_step(config, doe, step)
    if not s:
        return {}
    return {"initial_velocity": s["velocity"], "rigid_angular_velocity": s["rigid_angular_velocity"],
            "height": s["height"]}


# ── harvest --impact-map ───────────────────────────────────────────
def _pid_order(pid):
    return (0, int(pid), "") if str(pid).isdigit() else (1, 0, str(pid))


def _doe_peak(parts, parts_filter):
    """{pid: {name, peak_stress, stress_limit}} → 최대 응력 파트(같으면 작은 PID)와 그 파트의 peak/limit."""
    items = sorted(((p, i) for p, i in parts.items() if not parts_filter or p in parts_filter), key=lambda x: _pid_order(x[0]))
    if not items:
        return None
    pid, info = max(items, key=lambda x: x[1]["peak_stress"])
    lim = info.get("stress_limit") or 0.0
    return {"peak_stress": info["peak_stress"], "worst_pid": pid, "worst_part": info.get("name", ""),
            "ratio": info["peak_stress"] / lim if lim > 0 else None}


def _cell(v):
    if v is None:
        return ""
    return format(v, ".10g") if isinstance(v, float) else str(v)


def harvest_impact_map(test_dir, out_csv=None, parts_filter=None, yields=None):
    """완료 DOE 의 파트별 최대 응력을 index.json assignments 의 (원래 각도, e, k) 마다 붙여 CSV 두 개를 쓴다.

    per_angle_risk.csv(배정마다 한 줄)와 per_angle_risk_summary.csv(원래 각도마다 e·충격 차수 가운데 최대). → 통계 dict.
    같은 DOE 를 여러 번 돌렸으면 폴더 이름이 가장 늦은 Run 의 결과를 쓴다.
    """
    from Runner.AdaptiveOrientation import harvest, run_folder_to_doe
    from Runner.RiskHarvester import _apply_yield
    test_dir = os.path.abspath(test_dir)
    rc = {}
    rc_path = os.path.join(test_dir, "runner_config.json")
    if os.path.isfile(rc_path):
        with open(rc_path, encoding="utf-8") as f:
            rc = json.load(f)
    output_dir = (rc.get("project") or {}).get("output_dir") or os.path.join(test_dir, "output")
    index_path = os.path.join(output_dir, "impact_conditions", "index.json")
    if not os.path.isfile(index_path):
        raise ImpactConditionsError(f"index.json 이 없다: {index_path} — angle_source impact_conditions 로 prepare 한 "
                                    f"테스트 폴더를 줄 것 (index not found)")
    with open(index_path, encoding="utf-8") as f:
        idx = json.load(f)
    if idx.get("format") != INDEX_FORMAT:
        raise ImpactConditionsError(f"{index_path} 형식이 {INDEX_FORMAT!r} 가 아니다: {idx.get('format')!r} (bad index)")

    f2d, _completed = run_folder_to_doe(output_dir)
    samples = {s["run_id"]: s for s in harvest(test_dir)}
    if not os.path.abspath(output_dir).startswith(test_dir + os.sep):
        samples.update({s["run_id"]: s for s in harvest(output_dir)})
    per_doe = {}
    for rid in sorted(samples):   # 같은 DOE 가 여럿이면 늦은 Run 이 뒤에 와서 덮는다
        doe = f2d.get(rid)
        if doe is None and rid.split("Run_")[-1].isdigit():
            doe = int(rid.split("Run_")[-1])
        if doe is not None:
            per_doe[doe] = samples[rid]["parts"]
    _apply_yield(per_doe, yields or {})
    if parts_filter and not any(p in parts_filter for parts in per_doe.values() for p in parts):
        raise ImpactConditionsError(f"지정한 파트 {sorted(parts_filter)} 가 어느 결과에도 없다 (parts not found)")
    peaks = {d: _doe_peak(parts, parts_filter) for d, parts in per_doe.items()}
    does = [c["doe"] for c in idx.get("conditions", [])]
    missing_does = [d for d in does if not peaks.get(d)]
    if len(missing_does) == len(does):
        raise ImpactConditionsError(f"충격 조건 DOE {len(does)}개 가운데 결과(result.json)가 있는 것이 없다 — "
                                    f"{test_dir} 아래에서 찾았다 (no results)")

    rows = []
    for a in idx["assignments"]:
        res = peaks.get(a["doe"]) or {}
        rows.append({**{k: a.get(k) for k in RISK_COLUMNS[:11]},
                     **{k: res.get(k) for k in ("peak_stress", "worst_pid", "worst_part", "ratio")}})
    summary, order = {}, []
    for r in rows:
        key = (r["angle"], r["roll"], r["pitch"], r["yaw"])
        if key not in summary:
            order.append(key)
            summary[key] = {**{k: r[k] for k in ("angle", "roll", "pitch", "yaw", "dx", "dy", "dz")},
                            "peak_stress": None, "n_impacts": 0, "n_missing": 0}
        s = summary[key]
        s["n_impacts"] += 1
        if r["peak_stress"] is None:
            s["n_missing"] += 1
        elif s["peak_stress"] is None or r["peak_stress"] > s["peak_stress"]:
            s.update({k: r[k] for k in ("peak_stress", "worst_pid", "worst_part", "ratio")},
                     governing_e=r["e"], governing_k=r["k"], governing_doe=r["doe"])

    out_csv = os.path.abspath(out_csv) if out_csv else os.path.join(test_dir, "per_angle_risk.csv")
    out_sum = os.path.splitext(out_csv)[0] + "_summary.csv"
    for path, cols, data in ((out_csv, RISK_COLUMNS, rows), (out_sum, SUMMARY_COLUMNS, [summary[k] for k in order])):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows([_cell(d.get(c)) for c in cols] for d in data)
    stats = {"per_angle_risk": out_csv, "summary": out_sum, "n_does": len(does),
             "n_does_with_result": len(does) - len(missing_does), "missing_does": missing_does,
             "n_assignments": len(rows), "n_assignments_missing": sum(1 for r in rows if r["peak_stress"] is None),
             "n_angles": len(order), "n_angles_missing": sum(1 for k in order if summary[k]["peak_stress"] is None)}
    print(f"  index     : {index_path}")
    print(f"  DOE       : {stats['n_does_with_result']}/{stats['n_does']} 결과 있음"
          + (f" — 없음 {len(missing_does)}개: {', '.join(map(str, missing_does[:15]))}{' …' if len(missing_does) > 15 else ''}"
             if missing_does else ""))
    print(f"  (각도, e, k): {stats['n_assignments']}줄 (결과 없음 {stats['n_assignments_missing']})")
    print(f"  원래 각도 : {stats['n_angles']}개 (결과 없음 {stats['n_angles_missing']})")
    print(f"✅ 방출: {out_csv}")
    print(f"✅ 각도별 최대: {out_sum}")
    return stats
