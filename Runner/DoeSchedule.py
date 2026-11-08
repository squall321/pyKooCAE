# 사전 해석 ENDTIM 표로 DROP DOE 의 실행 비용·순서(긴 것부터)·칸 배정·무릎 대수를 정하는 순수 함수 모음 (KCR v134)
"""
쓰는 곳: KooChainRun submit(기본 제출 순서·--sequential 칸)·rerun·prepare 미리보기. 계약은
docs/doe_schedule_v134_20261108/PLAN.md 다.

  비용(초) = overhead_seconds + seconds_per_ms × Σ_스텝 (T_{d,s} + [DR 켬 이고 s ≥ 2]·tFinal) (ms 로 바꿔서)
    T_{d,s} = scenario.doe_endtim[d][s](덱 시간 단위). 표에 없는 스텝은 tFinal 이다. 구조는 EndTimePresim.doe_time_factors
    (시간 상한 배율 F_d)와 같고, 올림 없이 연속값이다.
  순서 = 비용 내림차순(LPT). 같으면 DOE 번호 오름차순이다 — 비용이 모두 같으면 지금(DOE 번호) 순서 그대로다.
  칸 배정 = 긴 것부터 지금 가장 덜 찬 칸으로(같으면 낮은 칸 번호). 칸 안 순서도 긴 것부터다.
  무릎 = 상한 cap 안에서 완료 시각이 (1 + knee_tolerance)·완료(cap) 이하가 되는 가장 작은 칸 수다. 기본 knee_tolerance 0 이면
    완료 시각이 더 줄지 않는 가장 작은 칸 수다(0.05 는 실제 2만 표 앞 500 개·칸 19 에서 라운드로빈보다 3.6% 늦었다, 11-08).

D2R(drop_surface.deformable_to_rigid)이 실제로 켜지면(카드가 생기는 조건까지) 비용은 그대로 ENDTIM 비례이고, '보정 안 됨'
표시만 한다. KCR D2R 은 비행 중 강체·접촉 중 변형체라 실제 비용은 다를 수 있지만 실행 시간 자료가 없다(사용자 결정 11-08).
"""
import heapq
import math
import os

DEFAULTS = {"enabled": True, "licenses": None, "licenses_per_job": 1, "max_concurrent": None,
            "overhead_seconds": 300.0, "seconds_per_ms": 20.0, "knee_tolerance": 0.0}
FORMAT = "kcr_doe_schedule v1"
SCHEDULE_FILE = "schedule.json"
RERUN_SCHEDULE_FILE = "schedule_rerun.json"   # rerun 계획 — submit 의 schedule.json 을 덮지 않는다
_TO_MS = {"s": 1000.0, "ms": 1.0}


class DoeScheduleError(ValueError):
    """environment.schedule 값이 틀렸다."""


def _is_num(v):
    return not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v)


def schedule_options(environment):
    """environment.schedule → 기본값을 채운 dict, 꺼졌으면 None. 없으면(또는 true·null) 기본값으로 켠다.
    모르는 키는 경고 한 줄, 틀린 값은 DoeScheduleError 다. false·{"enabled": false} 는 다른 키를 보지 않고 바로 None 이다."""
    raw = (environment or {}).get("schedule", None)
    if raw is None or raw is True:
        raw = {}
    if raw is False or (isinstance(raw, dict) and raw.get("enabled", True) is False):
        return None
    if not isinstance(raw, dict):
        raise DoeScheduleError(f"environment.schedule 는 true/false 또는 객체여야 한다: {raw!r} (bad value)")
    unknown = sorted(k for k in raw if k not in DEFAULTS)
    if unknown:
        print(f"⚠️  environment.schedule: 모르는 키 {unknown} 는 쓰지 않는다 — 쓸 수 있는 키 {sorted(DEFAULTS)}")
    opts = {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS}}

    def bad(key, want):
        raise DoeScheduleError(f"environment.schedule.{key} 는 {want}: {opts[key]!r} (bad value)")
    if not isinstance(opts["enabled"], bool):
        bad("enabled", "true/false 여야 한다")
    for key in ("licenses", "max_concurrent"):
        v = opts[key]
        if v is not None and (isinstance(v, bool) or not isinstance(v, int) or v < 1):
            bad(key, "1 이상 정수 또는 null 이어야 한다")
    v = opts["licenses_per_job"]
    if isinstance(v, bool) or not isinstance(v, int) or v < 1:
        bad("licenses_per_job", "1 이상 정수여야 한다")
    if not (_is_num(opts["overhead_seconds"]) and opts["overhead_seconds"] >= 0):
        bad("overhead_seconds", "0 이상 숫자여야 한다")
    if not (_is_num(opts["seconds_per_ms"]) and opts["seconds_per_ms"] > 0):
        bad("seconds_per_ms", "0 보다 큰 숫자여야 한다")
    if not (_is_num(opts["knee_tolerance"]) and opts["knee_tolerance"] >= 0):
        bad("knee_tolerance", "0 이상 숫자여야 한다")
    if opts["licenses"] is not None and opts["licenses"] < opts["licenses_per_job"]:
        bad("licenses", f"licenses_per_job({opts['licenses_per_job']}) 이상이어야 한다 — 잡 하나도 못 돈다")
    return opts if opts["enabled"] else None


def _table_meta(path):
    """표 csv 의 '# key=value' 메타 줄 → dict (BOM 이 붙어도 된다). 읽지 못하면 {}."""
    meta = {}
    try:
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                if not line.startswith("#"):
                    break
                k, sep, v = line[1:].strip().partition("=")
                if sep:
                    meta[k.strip()] = v.strip()
    except OSError:
        return {}
    return meta


def time_unit_to_ms(config):
    """덱 시간 1 단위의 ms → (값, 알림 목록). scenario.endtime_tables 의 표 메타 time_unit(s·ms)이 먼저이고, 없으면 units 메타의
    끝(mm-t-s → s, mm-kg-ms → ms)이다. 둘 다 없으면 tFinal 로 짐작한다(0.5 이상이면 ms, 아니면 s). 짐작하면 알린다.
    표마다 다르면 첫 표 값을 쓰고 알린다."""
    tables = ((config or {}).get("scenario") or {}).get("endtime_tables") or []
    units, notes = [], []
    for t in tables:
        meta = _table_meta(str((t or {}).get("table") or ""))
        tu = meta.get("time_unit", "").strip().lower()
        if tu not in _TO_MS:
            tu = meta.get("units", "").strip().lower().rsplit("-", 1)[-1]
            note = f"표 메타 time_unit 이 없어 units {meta.get('units', '').strip()} 의 끝 {tu} 를 덱 시간 단위로 본다"
            if tu in _TO_MS and note not in notes:
                notes.append(note)
        if tu in _TO_MS:
            units.append(tu)
    if not units:
        tf = float(((config or {}).get("simulation_params") or {}).get("tFinal", 0.005))
        tu = "ms" if tf >= 0.5 else "s"
        return _TO_MS[tu], [f"표 메타 time_unit·units 가 없어 tFinal {tf:g} 로 덱 시간 단위를 {tu} 로 짐작한다(0.5 이상이면 ms)"]
    if len(set(units)) > 1:
        notes.append(f"표마다 time_unit 이 다르다 {sorted(set(units))} — 첫 표 {units[0]} 를 쓴다")
    return _TO_MS[units[0]], notes


def d2r_active(config):
    """D2R 카드가 실제로 생기는가 — drop_surface.deformable_to_rigid 가 켜졌고, 바닥이 RigidWall 이 아니며,
    include_wall_in_general 이 아니고, drop_contact Type 을 General 로 직접 주지 않았을 때다(KMM D2R_SKIPPED·D2R_FLOOR_GENERAL)."""
    sim = (config or {}).get("simulation_params") or {}
    ds = sim.get("drop_surface") or {}
    if not isinstance(ds, dict) or not ds.get("deformable_to_rigid"):
        return False
    if str(ds.get("type", "Plane")) == "RigidWall" or sim.get("include_wall_in_general"):
        return False
    norm = lambda x: str(x).strip().lower().replace("_", "")  # noqa: E731
    dc = sim.get("drop_contact") or {}
    return not any(norm(k) == "type" and norm(v) == "general" for k, v in (dc.items() if isinstance(dc, dict) else []))


def doe_costs(config, opts):
    """DOE 마다 예상 실행 시간(초) → ({doe(1-based): 초}, 알림 목록). 표(scenario.doe_endtim)가 없거나 opts 가 None 이면
    (None, [])이라 호출 쪽은 지금 동작 그대로다."""
    scenario = (config or {}).get("scenario") or {}
    table = scenario.get("doe_endtim") or {}
    if opts is None or not table:
        return None, []
    try:
        total = max(1, int(scenario.get("total_steps", 1)))
    except (TypeError, ValueError):
        total = 1
    sim = (config or {}).get("simulation_params") or {}
    tfinal = float(sim.get("tFinal", 0.005))
    dr = sim.get("dynamic_relaxation", False)
    dr_on = bool(dr.get("enabled", True)) if isinstance(dr, dict) else bool(dr)
    n = int(scenario.get("doe_count") or max(int(k) for k in table))
    to_ms, notes = time_unit_to_ms(config)
    costs = {}
    for d in range(1, n + 1):
        steps = table.get(str(d)) or {}
        t = 0.0
        for s in range(1, total + 1):
            v = steps.get(str(s))
            t += (float(v) if v is not None else tfinal) + (tfinal if dr_on and s >= 2 else 0.0)
        costs[d] = float(opts["overhead_seconds"]) + float(opts["seconds_per_ms"]) * t * to_ms
    return costs, notes


def lpt_order(costs):
    """비용 내림차순 DOE 목록 — 같으면 DOE 번호 오름차순."""
    return sorted(costs, key=lambda d: (-costs[d], d))


def lpt_lanes(costs, n):
    """칸 n 개에 긴 것부터 지금 가장 덜 찬 칸으로 넣는다(같으면 낮은 칸 번호) → [[doe, …] × n], 칸 안은 긴 것부터."""
    n = max(1, int(n))
    heap = [(0.0, i) for i in range(n)]
    lanes = [[] for _ in range(n)]
    for d in lpt_order(costs):
        load, i = heapq.heappop(heap)
        lanes[i].append(d)
        heapq.heappush(heap, (load + costs[d], i))
    return lanes


def makespan(costs, n):
    """칸 n 개로 긴 것부터 넣었을 때 완료 시각(초) — 빈 칸에 다음 잡이 바로 드는 동적 배치와 같다."""
    n = max(1, int(n))
    heap = [0.0] * n
    for d in lpt_order(costs):
        heapq.heappush(heap, heapq.heappop(heap) + costs[d])
    return max(heap) if costs else 0.0


def lower_bound(costs, n):
    """완료 시각 하한 max(최장, 합 ÷ n)."""
    if not costs:
        return 0.0
    return max(max(costs.values()), sum(costs.values()) / max(1, int(n)))


def concurrency_cap(opts, nodes=None, doe_count=None):
    """동시 칸 상한 → (cap, {출처: 값}). nodes·licenses ÷ licenses_per_job·max_concurrent·DOE 수 가운데 가장 작은 값(1 이상)."""
    src = {}
    if nodes is not None:
        src["nodes"] = max(1, int(nodes))
    if opts and opts.get("licenses") is not None:
        src["licenses"] = max(1, opts["licenses"] // opts["licenses_per_job"])
    if opts and opts.get("max_concurrent") is not None:
        src["max_concurrent"] = opts["max_concurrent"]
    if doe_count is not None:
        src["doe_count"] = max(1, int(doe_count))
    return (min(src.values()) if src else 1), src


def knee_n(costs, cap, tol):
    """1 ≤ n ≤ cap 가운데 makespan(n) ≤ (1 + tol)·makespan(cap) 인 가장 작은 n. 이분 탐색이고 찾은 n 을 다시 확인한다."""
    cap = max(1, min(int(cap), len(costs) or 1))
    target = (1.0 + tol) * makespan(costs, cap) * (1 + 1e-12)
    lo, hi = 1, cap
    while lo < hi:
        mid = (lo + hi) // 2
        if makespan(costs, mid) <= target:
            hi = mid
        else:
            lo = mid + 1
    return lo if makespan(costs, lo) <= target else cap


def _by_n(costs, cap, knee):
    """완료 시각 표 — 1·2·4·… 와 무릎·상한."""
    ns = {1, knee, cap}
    k = 2
    while k < cap:
        ns.add(k)
        k *= 2
    return [{"n": n, "makespan_seconds": round(makespan(costs, n), 3), "lower_bound_seconds": round(lower_bound(costs, n), 3)}
            for n in sorted(x for x in ns if 1 <= x <= cap)]


def build_schedule(config, opts, mode, nodes=None, lanes=False, does=None):
    """스케줄 dict(schedule.json 내용) — 표가 없거나 꺼졌으면 None. mode: 'submit'·'sequential'·'rerun'·'prepare'.
    nodes 는 칸 상한에 넣을 노드 수(--sequential 의 --nodes). lanes=True 면 무릎 칸 수로 칸 배정을 넣는다.
    does 를 주면 그 DOE 만으로 짠다(rerun 대상). 표 밖 DOE(doe_count 밖)는 빼고 알림을 남긴다 — 부르는 쪽이 맨 뒤에 그대로
    낸다. 표 안 DOE 가 하나도 없으면 None 이라 호출 쪽은 지금 동작 그대로다."""
    costs, notes = doe_costs(config, opts)
    if costs is None:
        return None
    if does is not None:
        outside, keep = [d for d in does if d not in costs], set(does)
        costs = {d: c for d, c in costs.items() if d in keep}
        if not costs:
            return None
        if outside:
            notes = notes + [f"표 밖 DOE {outside} 는 계획에서 빼고 맨 뒤에 그대로 낸다(예전처럼 그 DOE 만 실패한다)"]
    cap, cap_from = concurrency_cap(opts, nodes, len(costs))
    knee = knee_n(costs, cap, opts["knee_tolerance"])
    d2r = d2r_active(config)
    if d2r:
        notes = notes + ["D2R 켬 — 비용은 ENDTIM 비례로 두었다(비행 중 강체라 실제는 더 짧을 수 있다, 보정 안 됨)"]
    plan = {"format": FORMAT, "mode": mode,
            "assumptions": {"overhead_seconds": opts["overhead_seconds"], "seconds_per_ms": opts["seconds_per_ms"],
                            "knee_tolerance": opts["knee_tolerance"], "calibrated": False, "d2r": d2r},
            "doe_count": len(costs), "cap": cap, "cap_from": cap_from, "knee": knee,
            "makespan_seconds": round(makespan(costs, knee), 3), "lower_bound_seconds": round(lower_bound(costs, knee), 3),
            "total_seconds": round(sum(costs.values()), 3), "longest_seconds": round(max(costs.values()), 3),
            "by_n": _by_n(costs, cap, knee), "order": lpt_order(costs),
            "costs_seconds": {str(d): round(c, 3) for d, c in costs.items()}, "notes": notes}
    if lanes:
        plan["lanes"] = lpt_lanes(costs, knee)
    return plan


def _h(sec):
    return f"{sec / 3600:.2f} h"


def summary_line(plan):
    """사람이 읽을 한 줄 요약."""
    a = plan["assumptions"]
    caps = ", ".join(f"{k} {v}" for k, v in plan["cap_from"].items())
    tail = " · D2R 켬(보정 안 됨)" if a["d2r"] else ""
    return (f"[schedule] DOE {plan['doe_count']} · 예상 합 {_h(plan['total_seconds'])} · 최장 {_h(plan['longest_seconds'])} · "
            f"무릎 {plan['knee']} 칸(상한 {plan['cap']}: {caps}) · 예상 완료 {_h(plan['makespan_seconds'])} "
            f"(하한 {_h(plan['lower_bound_seconds'])}) — 가정 고정비 {a['overhead_seconds']:g} s · 해석 1 ms 당 "
            f"{a['seconds_per_ms']:g} s, 보정 안 됨{tail}")


def fewer_slots_line(plan, nodes, label):
    """칸 배정(lanes)이 노드 nodes 개보다 적은 칸을 쓰면 알림 한 줄, 아니면 None. 상한(licenses·max_concurrent·DOE 수)에 걸렸는지,
    무릎(나머지를 써도 예상 완료가 줄지 않는다)인지를 적고 무릎 칸·상한 칸의 예상 완료를 함께 적는다."""
    if plan is None or "lanes" not in plan or nodes is None or plan["knee"] >= nodes:
        return None
    why = []
    if plan["cap"] < nodes:
        caps = ", ".join(f"{k} {v}" for k, v in plan["cap_from"].items() if k != "nodes" and v == plan["cap"])
        why.append(f"상한 {plan['cap']}({caps})")
    if plan["knee"] < plan["cap"]:
        why.append(f"나머지를 써도 예상 완료가 줄지 않는다(무릎, knee_tolerance {plan['assumptions']['knee_tolerance']:g})")
    at_cap = next(x["makespan_seconds"] for x in plan["by_n"] if x["n"] == plan["cap"])
    return (f"⚠️  {label} {nodes} 가운데 {plan['knee']} 칸만 쓴다 — {' · '.join(why)} · 예상 완료 "
            f"{_h(plan['makespan_seconds'])} ({plan['cap']} 칸 {_h(at_cap)})")


def write_schedule(plan, directory, name=SCHEDULE_FILE):
    """plan 을 directory/name(기본 schedule.json) 으로 쓴다 → 경로."""
    import json
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return path
