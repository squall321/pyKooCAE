# IMPACT(전위치 부분충격) 생성 덱을 제출 전에 점검하는 관문과 자리 격자 표 — 모르는 키·SI 기본값·충격추 요소·질량·속도·자리·접촉·출력 간격
"""KC-08 IMPACT 모드 관문 · KC-09 자리 격자 표 (stcx 요청서 v1.0).

모르는 키(prepare 때 늘): simulation_params.impact 의 키를 러너가 읽는 표와 견줘 경고(did you mean). 하위 객체(`"sphere": {...}`)는
  러너가 읽지 않는다 — 그때 Dimension 기본값 0.008 이 들어갔다(KOOCHAINRUN_IMPACT_MODE_PITFALLS).
SI 크기 기본값: 모델이 mm 단위계인데 height·dimension·dt·tFinal 을 주지 않으면 러너 기본값(0.5·0.008·1e-6·0.001)이 덱 단위로 들어간다 — 경고.
생성 덱 점검(`prepare --check-impact`, 표본 또는 전부): 러너와 같은 경로(단계 설정 → KMM)로 덱을 만들고
  - 충격추 파트(초기 속도 GENERATION 파트) 수가 설계 단 수와 같고 파트마다 요소 > 0 (몸통 요소 0 → 거절)
  - 충격추 질량(요소 부피 × 밀도) 대 설계(구·원통 단) — 큰 차이만 경고(메시가 원을 깎아 몇 % 작게 나온다)
  - 초기 속도 |v| 대 √(2gh)(g 는 impact.gravity, 없으면 덱 단위계의 g — mm 면 9810) — 1 % 넘게 다르면 거절
  - 자리 오차(충격추 부피 중심 대 LocationX·Y) · 충격추 접촉이 전역 접촉과 겹치는지(경고) · d3plot 간격·상태 수·예상 크기(어림)
"""
import csv
import difflib
import json
import math
import os
import re
import shutil
from typing import Any, Dict, List, Optional

# 러너 IMPACT 갈래(CumulativeScenarioRunner._create_step_config)가 읽는 키
IMPACT_KEYS = {"height", "type", "dimension", "cylinder_stages", "mesh_size", "dimension_damper", "density",
               "youngs_modulus", "poisson_ratio", "poisson", "tFinal", "dt", "offset_distance", "gravity", "dtmin"}
STAGE_KEYS = {"role", "diameter", "outer_diameter", "height", "density", "youngs_modulus", "poisson", "poisson_ratio"}
RUNNER_DEFAULTS = {"height": 0.5, "dimension": 0.008, "dt": 1e-6, "tFinal": 0.001}


def check_impact_keys(sim_params: Optional[Dict[str, Any]]) -> List[str]:
    """simulation_params.impact 의 모르는 키·하위 객체 경고 줄."""
    imp = (sim_params or {}).get("impact")
    if not isinstance(imp, dict):
        return []
    out = []
    for k, v in imp.items():
        if k in IMPACT_KEYS:
            continue
        near = difflib.get_close_matches(k, sorted(IMPACT_KEYS), n=1, cutoff=0.6)
        hint = f" — did you mean '{near[0]}'?" if near else ""
        if isinstance(v, dict):
            out.append(f"⚠ simulation_params.impact.{k}: 하위 객체는 러너가 읽지 않는다(조용히 버려진다){hint}. "
                       f"크기는 impact.dimension(구는 반지름)·cylinder_stages 로")
        else:
            out.append(f"⚠ simulation_params.impact.{k}: 모르는 키 — 러너가 읽지 않는다{hint}")
    for i, st in enumerate(imp.get("cylinder_stages") or []):
        for k in (st or {}):
            if k not in STAGE_KEYS:
                near = difflib.get_close_matches(k, sorted(STAGE_KEYS), n=1, cutoff=0.6)
                out.append(f"⚠ simulation_params.impact.cylinder_stages[{i}].{k}: 모르는 키" +
                           (f" — did you mean '{near[0]}'?" if near else ""))
    return out


def si_default_warnings(sim_params: Optional[Dict[str, Any]], units: Optional[str]) -> List[str]:
    """모델이 mm 단위계인데 SI 크기 러너 기본값이 쓰이면 경고."""
    imp = (sim_params or {}).get("impact") or {}
    if not units or not units.startswith("mm"):
        return []
    out = []
    missing = [k for k in ("height", "dimension") if k not in imp and not (k == "dimension" and imp.get("cylinder_stages"))]
    for k in missing:
        out.append(f"⚠ 모델이 {units} 인데 impact.{k} 가 없어 러너 기본값 {RUNNER_DEFAULTS[k]} 이 {units} 로 들어간다"
                   f"({'높이 0.5 mm' if k == 'height' else '충격추 0.008 mm'})")
    if "dt" not in imp:
        tf = float(imp.get("tFinal", RUNNER_DEFAULTS["tFinal"]))
        out.append(f"⚠ impact.dt 가 없어 기본값 1e-6 — d3plot·ELOUT·NODOUT·INTFOR 간격이 1e-6 이라 tFinal {tf:g} 에 "
                   f"{tf / 1e-6:.0f}상태(런당 수백 GB 사례 — 486 GB)")
    if units == "mm-kg-ms" and "tFinal" not in imp:
        out.append("⚠ 모델이 mm-kg-ms(시간 ms)인데 impact.tFinal 이 없어 기본값 0.001 = 0.001 ms 다")
    return out


def design_mass(sim_params: Dict[str, Any]) -> Optional[float]:
    """설계 충격추 질량 — 구(dimension = 반지름) 또는 원통 단(front 는 바깥 지름으로 어림)."""
    imp = (sim_params or {}).get("impact") or {}
    t = str(imp.get("type", "Sphere")).lower()
    rho = float(imp.get("density", 7.85e-9))
    if t == "sphere":
        r = imp.get("dimension")
        try:
            r = float(r if not isinstance(r, (list, tuple)) else r[0])
        except (TypeError, ValueError):
            return None
        return 4.0 / 3.0 * math.pi * r ** 3 * rho
    st = imp.get("cylinder_stages") or []
    if t == "cylinder" and st:
        m = 0.0
        for i, s in enumerate(st):
            d = s.get("outer_diameter", s.get("diameter")) if i == 0 else s.get("diameter")
            if d is None or s.get("height") is None:
                return None
            r = float(d) / 2.0
            m += math.pi * r * r * float(s["height"]) * float(s.get("density", rho if i == len(st) - 1 else 7.85e-9))
        return m
    return None


def design_stage_count(sim_params: Dict[str, Any]) -> Optional[int]:
    imp = (sim_params or {}).get("impact") or {}
    if str(imp.get("type", "Sphere")).lower() == "cylinder" and imp.get("cylinder_stages"):
        return len(imp["cylinder_stages"])
    return None


def state_bytes_estimate(info: Dict[str, Any]) -> int:
    """d3plot 한 상태의 어림 바이트(4바이트 단어 — 절점 9·솔리드 10·셸 33·두꺼운 셸 10·보 14)."""
    e = info.get("elements") or {}
    w = info.get("nodes", 0) * 9 + e.get("solid", 0) * 10 + e.get("shell", 0) * 33 + e.get("tshell", 0) * 10 + e.get("beam", 0) * 14
    return 4 * w


KMM_STD_ALL_CONTACTS = 2   # KMM 충격 덱의 표준 접촉 — 「전부 대 벽」·「전부 대 충격추」(둘 다 SSTYP 5 라 충격추를 덮는다)


def analyze_impact_run(run_dir: str, sim_params: Dict[str, Any], gravity_cfg: Optional[float] = None,
                       pos_tol: Optional[float] = None, model_contacts: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """생성된 DropWeightImpactTestSet.k 하나 — 관문 줄(dict).

    model_contacts: 원 모델 덱의 접촉(kw·cid·title) — 주면 그 접촉이 충격추를 덮을 때만 겹침 경고(정확). 없으면 「전부」형
    접촉(SSTYP 5·6·SINGLE_SURFACE)이 KMM 표준 두 장보다 많을 때 경고. 실린더 단끼리 묶는 TIED(파트 지정)는 세지 않는다.
    """
    from Runner.DeckScan import scan_deck, part_ids_of_contact_side
    from Runner.RunHealth import parse_step_config
    deck = os.path.join(run_dir, "DropWeightImpactTestSet.k")
    step = parse_step_config(os.path.join(run_dir, "step_config.txt"))
    row: Dict[str, Any] = {"run_dir": run_dir, "run_key": os.path.basename(run_dir), "reject": [], "warn": []}
    if not os.path.isfile(deck):
        row["reject"].append("생성 덱 없음")
        return row
    pre = scan_deck(deck)
    imp_pids = sorted({int(iv["id"]) for iv in pre["initial_velocities"]
                       if iv.get("kw") == "*INITIAL_VELOCITY_GENERATION" and iv.get("styp") == 2 and iv.get("id")})
    info = scan_deck(deck, collect_parts=imp_pids) if imp_pids else pre
    row["units"] = info["units"]
    row["impactor_parts"] = imp_pids
    row["impactor_elems"] = {str(p): info["elements_by_part"].get(str(p), 0) for p in imp_pids}
    if not imp_pids:
        row["reject"].append("충격추(초기 속도 GENERATION 파트)를 찾지 못했다")
    for p, n in row["impactor_elems"].items():
        if n == 0:
            row["reject"].append(f"충격추 파트 {p} 요소 0(몸통 요소 0)")
    ns = design_stage_count(sim_params)
    if ns and len(imp_pids) < ns:
        row["reject"].append(f"충격추 파트 {len(imp_pids)}개 < 설계 단 {ns}개")
    # 질량
    mass = 0.0
    for p in imp_pids:
        mid = (info["parts"].get(str(p)) or {}).get("mid")
        rho = (info["materials"].get(str(mid)) or {}).get("density") or 0.0
        mass += (info.get("part_volume", {}).get(str(p)) or 0.0) * rho
    row["impactor_mass"] = mass or None
    row["impactor_mass_g"] = _to_g(mass, info["units"]) if mass else None
    md = design_mass(sim_params)
    row["design_mass"] = md
    if md and mass:
        rel = mass / md - 1.0
        row["mass_rel"] = rel
        if rel < -0.5 or rel > 0.5:
            row["reject"].append(f"충격추 질량 {mass:.4g} 이 설계 {md:.4g} 와 {rel * 100:+.0f} % 다르다")
        elif abs(rel) > 0.15:
            row["warn"].append(f"충격추 질량 {mass:.4g} 이 설계 {md:.4g} 와 {rel * 100:+.0f} % 다르다")
    # 속도
    g_units = info.get("gravity")
    g = gravity_cfg if gravity_cfg is not None else (float(step["Gravity"]) if step.get("Gravity") else g_units)
    h = float(step["Height"]) if step.get("Height") not in (None, "") else None
    v_deck = None
    for iv in info["initial_velocities"]:
        if iv.get("kw") == "*INITIAL_VELOCITY_GENERATION" and iv.get("id") in imp_pids:
            v_deck = math.sqrt(sum(x * x for x in iv["v"]))
            row["vz"] = iv["v"][2]
            break
    ivs = [float(step.get(k) or 0.0) for k in ("InitialVelocityX", "InitialVelocityY", "InitialVelocityZ")]
    if h is not None and g_units:
        vf = math.sqrt(2.0 * g_units * max(h, 0.0))
        v_exp = math.sqrt(ivs[0] ** 2 + ivs[1] ** 2 + (ivs[2] - vf) ** 2)
        row["vz_expected"] = ivs[2] - vf
        row["v_expected"] = v_exp
        if v_deck is not None and v_exp > 0 and abs(v_deck / v_exp - 1.0) > 0.01:
            row["reject"].append(f"초기 속도 {v_deck:.6g} 가 √(2gh) {v_exp:.6g}(g {g_units:g} — 덱 {info['units']}) 와 "
                                 f"{(v_deck / v_exp - 1) * 100:+.1f} % 다르다")
    if g is not None and g_units and abs(g / g_units - 1.0) > 0.01:
        row["reject"].append(f"중력 {g:g} 이 덱 단위계 {info['units']} 의 g {g_units:g} 와 다르다")
    # 자리
    cen = info.get("part_centroid") or {}
    vols = info.get("part_volume") or {}
    vt = sum(vols.get(str(p), 0.0) for p in imp_pids)
    if vt > 0 and step.get("LocationX") not in (None, ""):
        cx = sum(vols[str(p)] * cen[str(p)][0] for p in imp_pids if cen.get(str(p))) / vt
        cy = sum(vols[str(p)] * cen[str(p)][1] for p in imp_pids if cen.get(str(p))) / vt
        lx, ly = float(step["LocationX"]), float(step.get("LocationY") or 0.0)
        row["pos_err"] = math.hypot(cx - lx, cy - ly)
        tol = pos_tol if pos_tol is not None else 0.05 * max(1e-12, (vt / math.pi) ** (1.0 / 3.0))
        if row["pos_err"] > tol:
            row["warn"].append(f"자리 오차 {row['pos_err']:.4g} > {tol:.3g}")
    # 접촉 겹침 — 원 모델 덱의 접촉이 충격추를 덮으면(요청서 사례: 에너지비 1.68 → 그 접촉을 지운 뒤 0.995)
    imp_set = set(imp_pids)
    mkeys = {(c.get("kw"), c.get("cid"), (c.get("title") or "").strip()) for c in (model_contacts or [])}
    touching = []
    for c in info["contacts"]:
        sides = [part_ids_of_contact_side(info, c.get("ssid"), c.get("sstyp")),
                 part_ids_of_contact_side(info, c.get("msid"), c.get("mstyp"))]
        hit = any(sd is not None and imp_set & set(sd) for sd in sides)
        if hit:
            glob_like = c.get("sstyp") in (5, 6) or "SINGLE_SURFACE" in c["kw"]
            from_model = (c["kw"], c.get("cid"), (c.get("title") or "").strip()) in mkeys
            touching.append({"kw": c["kw"], "cid": c.get("cid"), "global": glob_like, "from_model": from_model})
    row["contact_cards"] = touching
    if model_contacts is not None:
        over = [t for t in touching if t["from_model"]]
        if over:
            row["warn"].append(f"원 모델의 접촉 {[t['cid'] for t in over]} 이 충격추까지 덮는다 — 충격추 전용 접촉과 겹쳐 가짜 에너지가 날 수 있다")
    elif sum(1 for t in touching if t["global"]) > KMM_STD_ALL_CONTACTS:
        row["warn"].append(f"「전부」형 접촉 {sum(1 for t in touching if t['global'])}장이 충격추를 덮는다(KMM 표준 {KMM_STD_ALL_CONTACTS}장보다 많다) — "
                           f"겹친 접촉은 가짜 에너지를 낸다")
    # 출력 간격·크기
    row["d3plot_dt"], row["endtim"] = info.get("d3plot_dt"), info.get("endtim")
    if info.get("d3plot_dt") and info.get("endtim"):
        states = int(info["endtim"] / info["d3plot_dt"] + 1e-9) + 1
        row["states"] = states
        row["est_size_gb"] = round(states * state_bytes_estimate(info) / 1024 ** 3, 2)
    row["verdict"] = "reject" if row["reject"] else ("warn" if row["warn"] else "pass")
    return row


def _to_g(mass, units):
    return {"mm-t-s": mass * 1e6, "mm-kg-ms": mass * 1e3, "mm-g-ms": mass, "m-kg-s": mass * 1e3}.get(units)


def sample_does(doe_count: int, sample) -> List[int]:
    if doe_count <= 0:
        return []
    if str(sample).lower() == "all":
        return list(range(1, doe_count + 1))
    n = max(1, min(int(sample), doe_count))
    if n == 1:
        return [1]
    return sorted({1 + round(i * (doe_count - 1) / (n - 1)) for i in range(n)})


def run_impact_gate(config_path: str, sample="5", out_dir: Optional[str] = None, keep: bool = True) -> Dict[str, Any]:
    """러너와 같은 경로로 표본 위치의 덱을 만들어 점검한다. 결과: {rows, verdict, out_dir}."""
    from Runner.CumulativeScenarioRunner import CumulativeScenarioRunner
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    steps = [s for s in cfg["scenario"]["steps"] if s.get("mode") == "IMPACT"]
    if not steps:
        return {"rows": [], "verdict": "skip", "note": "IMPACT 단계가 없다"}
    gate_dir = os.path.abspath(out_dir or os.path.join(os.path.dirname(cfg["project"]["output_dir"]), "impact_gate"))
    os.makedirs(gate_dir, exist_ok=True)
    gcfg = json.loads(json.dumps(cfg))
    gcfg["project"]["output_dir"] = os.path.join(gate_dir, "output")
    gcfg["project"]["index_file"] = os.path.join(gate_dir, "output", "simulation_index.json")
    gcfg["execution"]["checkpoint_file"] = os.path.join(gate_dir, "output", "checkpoint.json")
    gpath = os.path.join(gate_dir, "runner_config.gate.json")
    with open(gpath, "w", encoding="utf-8") as f:
        json.dump(gcfg, f, ensure_ascii=False, indent=1)
    runner = CumulativeScenarioRunner(gpath)
    sim = cfg.get("simulation_params") or {}
    model_contacts = None
    try:
        from Runner.DeckScan import scan_deck
        mf = cfg["project"].get("model_file")
        model_contacts = scan_deck(mf)["contacts"] if mf and os.path.isfile(mf) else None
    except Exception:
        model_contacts = None
    g_cfg = (sim.get("impact") or {}).get("gravity", sim.get("gravity"))
    rows = []
    for doe in sample_does(int(cfg["scenario"]["doe_count"]), sample):
        st = steps[0]
        cf = runner._create_step_config(doe, st)
        rid = runner._run_koomeshmodifier(cf, runner.output_dir) if cf else None
        if not rid:
            rows.append({"doe": doe, "run_dir": None, "verdict": "reject", "reject": ["KMM 덱 생성 실패"], "warn": []})
            continue
        rd = os.path.join(runner.output_dir, f"Run_{rid}")
        if cf and os.path.isfile(cf):
            shutil.move(cf, os.path.join(rd, "step_config.txt"))
        r = analyze_impact_run(rd, sim, gravity_cfg=float(g_cfg) if g_cfg is not None else None, model_contacts=model_contacts)
        r["doe"] = doe
        pos = ((cfg["scenario"].get("doe_positions") or {}).get(str(doe)) or {}).get(str(st["step"])) or {}
        r["site"] = pos.get("position_name")
        rows.append(r)
        if not keep:
            shutil.rmtree(rd, ignore_errors=True)
    verdict = "reject" if any(r["verdict"] == "reject" for r in rows) else ("warn" if any(r["verdict"] == "warn" for r in rows) else "pass")
    res = {"rows": rows, "verdict": verdict, "out_dir": gate_dir, "sample": str(sample),
           "key_warnings": check_impact_keys(sim)}
    with open(os.path.join(gate_dir, "impact_gate.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(gate_dir, "impact_gate.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["doe", "site", "verdict", "impactor_elems", "impactor_mass_g", "vz", "vz_expected", "pos_err",
                    "contact_cards", "d3plot_dt", "states", "est_size_gb", "reasons", "run_dir"])
        for r in rows:
            w.writerow([r.get("doe"), r.get("site"), r.get("verdict"), json.dumps(r.get("impactor_elems")),
                        r.get("impactor_mass_g"), r.get("vz"), r.get("vz_expected"), r.get("pos_err"),
                        ";".join(f"{c['kw']}#{c.get('cid')}" for c in r.get("contact_cards") or []), r.get("d3plot_dt"),
                        r.get("states"), r.get("est_size_gb"), " | ".join((r.get("reject") or []) + (r.get("warn") or [])),
                        r.get("run_dir")])
    return res


# ── KC-09 자리 격자 표 ────────────────────────────────────────────────────
_RE_GRID = re.compile(r"^P_(\d+)_(\d+)$")


def sites_table(config: Dict[str, Any], face: Optional[str] = None) -> Dict[str, Any]:
    """계획 자리(doe_positions) 대 생성(index·Run 폴더) — 빠진 자리마다 까닭."""
    from Runner.CampaignStatus import load_index_runs, alias_of
    sc = config.get("scenario", {})
    pos = sc.get("doe_positions") or {}
    out_dir = config.get("project", {}).get("output_dir", "")
    runs = load_index_runs(config)
    rows = []
    for doe_s in sorted(pos, key=lambda x: int(x)):
        steps = pos[doe_s]
        first = sorted(steps, key=lambda x: int(x))[0]
        p = steps[first]
        name = p.get("position_name") or f"P_{int(doe_s):04d}"
        m = _RE_GRID.match(name)
        row_i, col_i = (int(m.group(1)), int(m.group(2))) if m else (None, None)
        try:
            alias = alias_of(config, int(doe_s), int(first))
        except (KeyError, IndexError):
            alias = None
        r = runs.get(alias) or {}
        rd = os.path.join(out_dir, r["folder"]) if r.get("folder") else ""
        generated = bool(rd) and os.path.isfile(os.path.join(rd, "DropWeightImpactTestSet.k"))
        why = ""
        if not generated:
            why = r.get("error") or ("아직 돌지 않았다" if not r else f"index {r.get('status')} — 덱 없음")
        rows.append({"site_id": name, "face": face or "", "col": col_i, "row": row_i, "x_mm": p.get("x"), "y_mm": p.get("y"),
                     "run_key": alias or "", "doe": int(doe_s), "generated": generated, "missing_reason": why})
    planned = len(rows)
    gen = sum(1 for r in rows if r["generated"])
    return {"rows": rows, "planned": planned, "generated": gen, "missing": planned - gen}


SITES_FIELDS = ("site_id", "face", "col", "row", "x_mm", "y_mm", "run_key", "doe", "generated", "missing_reason")


def write_sites_csv(tab: Dict[str, Any], path: str) -> str:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SITES_FIELDS)
        w.writeheader()
        for r in tab["rows"]:
            w.writerow(r)
    return path
