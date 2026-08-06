# 완료된 전각도 낙하/전위치 충격 결과에서 취약 조건을 뽑아 scenario.json 이 물릴 JSON 으로 방출

"""
취약조건 수확기

전각도 낙하(sphere) 또는 전위치 부분충격(impact) 결과를 읽어 위험도 상위 조건을
추려, 그대로 scenario.json 의 angle_source.explicit.file /
position_source.manual.file 에 물릴 수 있는 JSON 을 만든다.

소스 우선순위
    1. sphere_report.json  (전각도 낙하 통합) — 각도가 이미 붙어 있어 가장 정확
    2. impact_report.json  (전위치 충격 통합) — 위치(x,y)가 이미 붙어 있음
    3. 개별 result.json 스캔 (deep_report 산출물) — 통합 리포트가 없을 때 폴백

위험도 판정은 AdaptiveOrientation.compute_risk 를 재사용한다
(per-part z-score 상대 + yield 절대비 병행). 새 알고리즘을 만들지 않는다.

Author: koo.park
Email: koo.park@samsung.com
Group: CAE
"""

import glob
import json
import os
from typing import Dict, List, Optional, Tuple

from Runner.AdaptiveOrientation import harvest as _harvest_results
from Runner.AdaptiveOrientation import compute_risk


def _find_report(test_dir: str, basename: str) -> Optional[str]:
    """test_dir 하위에서 통합 리포트 JSON 을 찾는다 (가장 최근 것)."""
    hits = glob.glob(os.path.join(test_dir, "**", basename), recursive=True)
    if not hits:
        return None
    return max(hits, key=os.path.getmtime)


def _risk_from_parts(parts: Dict[str, dict], z_thr: float, yield_factor: float,
                     parts_filter: Optional[set] = None) -> List[dict]:
    """{조건키: {pid: {peak_stress, stress_limit}}} 형태를 compute_risk 입력으로 변환.

    parts_filter 를 주면 그 파트만으로 위험도를 계산한다. 파트이동 DOE 로 옮길
    파트가 정해졌을 때, 그 파트가 가혹한 조건을 골라내기 위한 용도.
    (전 파트 max 로 뽑으면 옮길 파트와 무관하게 뜨거운 조건이 섞인다)
    """
    if parts_filter:
        # 🔴 필터가 하나도 안 맞으면 compute_risk 가 전 조건 risk=0 을 조용히 반환해
        #    "위험한 조건이 없다"로 오독된다. 여기서 끊는다.
        available = set()
        for pinfo in parts.values():
            available.update(pinfo.keys())
        missing = parts_filter - available
        if missing == parts_filter:
            raise ValueError(
                f"지정한 파트 {sorted(parts_filter)} 가 리포트에 없습니다. "
                f"리포트에 있는 파트: {sorted(available)[:20]}"
                + (" ..." if len(available) > 20 else ""))
        if missing:
            print(f"  ⚠️  리포트에 없는 파트는 제외: {sorted(missing)}")
            parts_filter = parts_filter - missing

    samples = [{"run_id": key, "parts": pinfo, "orientation": None, "vec": None}
               for key, pinfo in parts.items()]
    compute_risk(samples, z_thr=z_thr, yield_factor=yield_factor,
                 parts_filter=parts_filter)
    return samples


def parts_from_scenario(scenario_path: str) -> List[str]:
    """scenario.json 의 part_doe 에서 옮길 파트 ID 를 뽑는다.

    "DOE 로 옮길 파트를 정했으면 그 파트 기준으로 취약 조건을 뽑는다"는 흐름을
    손으로 PID 를 옮겨 적지 않고 잇기 위한 것.
    """
    with open(scenario_path, encoding="utf-8") as f:
        doc = json.load(f)

    pids = []
    for scen in doc.get("scenarios") or []:
        pd = scen.get("part_doe") or {}
        if not pd or not pd.get("enabled", True):
            continue
        for p in pd.get("parts") or []:
            if "pid" in p:
                pids.append(str(p["pid"]))
        for c in pd.get("cases") or []:
            for m in c.get("moves") or []:
                if "pid" in m:
                    pids.append(str(m["pid"]))

    if not pids:
        raise ValueError(
            f"{scenario_path} 에서 part_doe 의 파트를 찾지 못했습니다. "
            f"part_doe.parts[].pid 또는 part_doe.cases[].moves[].pid 가 필요합니다.")
    # 순서 보존 중복 제거
    return list(dict.fromkeys(pids))


def harvest_from_sphere(report_path: str, z_thr: float = 1.5,
                        yield_factor: float = 1.0,
                        parts_filter: Optional[set] = None) -> List[dict]:
    """sphere_report.json → [{name, roll, pitch, yaw, risk, is_hot, hot_parts}, ...]"""
    with open(report_path, encoding="utf-8") as f:
        doc = json.load(f)

    rows = doc.get("results_summary") or []
    if not rows:
        raise ValueError(f"sphere_report 에 results_summary 가 없습니다: {report_path}")

    meta: Dict[str, dict] = {}
    parts_by_key: Dict[str, dict] = {}
    for i, r in enumerate(rows):
        ang = r.get("angle") or {}
        if ang.get("roll") is None or ang.get("pitch") is None:
            continue
        key = str(r.get("run_id") or r.get("name") or f"R{i + 1:04d}")
        meta[key] = {
            "name": key,
            "roll": float(ang["roll"]),
            "pitch": float(ang["pitch"]),
            "yaw": float(ang.get("yaw") or 0.0),
        }
        pdict = {}
        for pid, pr in (r.get("parts") or {}).items():
            ps = pr.get("peak_stress")
            if ps is None:
                continue
            pdict[str(pid)] = {
                "name": pr.get("name", ""),
                "peak_stress": float(ps),
                "stress_limit": float(pr.get("stress_limit") or 0.0),
            }
        if pdict:
            parts_by_key[key] = pdict

    if not parts_by_key:
        raise ValueError(
            f"sphere_report 에서 peak_stress 를 가진 케이스를 찾지 못했습니다: {report_path}")

    out = []
    for s in _risk_from_parts(parts_by_key, z_thr, yield_factor, parts_filter):
        m = meta.get(s["run_id"])
        if not m:
            continue
        out.append({**m, "risk": s.get("risk", 0.0),
                    "is_hot": bool(s.get("is_hot")),
                    "hot_parts": s.get("hot_parts", [])})
    return out


def harvest_from_impact(report_path: str, z_thr: float = 1.5,
                        yield_factor: float = 1.0,
                        parts_filter: Optional[set] = None) -> List[dict]:
    """impact_report.json → [{name, x, y, risk, is_hot, hot_parts}, ...]

    impact_report 의 results 는 (위치 x 파트) 평탄 리스트라 위치 단위로 다시 묶는다.
    """
    with open(report_path, encoding="utf-8") as f:
        doc = json.load(f)

    rows = doc.get("results") or []
    if not rows:
        raise ValueError(f"impact_report 에 results 가 없습니다: {report_path}")

    # 파트별 항복강도 (있으면 절대 기준에 쓴다)
    limits = {}
    for p in doc.get("parts") or []:
        pid = p.get("part_id", p.get("pid"))
        lim = p.get("stress_limit", p.get("yield_stress"))
        if pid is not None and lim:
            limits[str(pid)] = float(lim)

    meta: Dict[str, dict] = {}
    parts_by_key: Dict[str, dict] = {}
    for r in rows:
        ps = r.get("peak_stress")
        if ps is None:
            continue
        pos_id = r.get("pos_id")
        face = r.get("face")
        key = f"{face}_{pos_id}" if face else str(pos_id)
        if key not in meta:
            meta[key] = {"name": str(key),
                         "x": float(r.get("x", 0.0)),
                         "y": float(r.get("y", 0.0))}
            parts_by_key[key] = {}
        pid = str(r.get("part_id"))
        parts_by_key[key][pid] = {
            "name": pid,
            "peak_stress": float(ps),
            "stress_limit": limits.get(pid, 0.0),
        }

    parts_by_key = {k: v for k, v in parts_by_key.items() if v}
    if not parts_by_key:
        raise ValueError(
            f"impact_report 에서 peak_stress 를 가진 위치를 찾지 못했습니다: {report_path}")

    out = []
    for s in _risk_from_parts(parts_by_key, z_thr, yield_factor, parts_filter):
        m = meta.get(s["run_id"])
        if not m:
            continue
        out.append({**m, "risk": s.get("risk", 0.0),
                    "is_hot": bool(s.get("is_hot")),
                    "hot_parts": s.get("hot_parts", [])})
    return out


def harvest_from_results(test_dir: str, runner_config: Optional[dict],
                         z_thr: float = 1.5, yield_factor: float = 1.0,
                         parts_filter: Optional[set] = None) -> List[dict]:
    """개별 result.json 스캔 폴백 (통합 리포트가 아직 없을 때).

    runner_config 가 있으면 각도가 붙어 DROP 조건으로 방출할 수 있다.
    """
    samples = _harvest_results(test_dir, runner_config)
    if not samples:
        raise ValueError(
            f"result.json 을 찾지 못했습니다: {test_dir}\n"
            f"deep_report 가 아직 돌지 않았을 수 있습니다.")
    compute_risk(samples, z_thr=z_thr, yield_factor=yield_factor,
                 parts_filter=parts_filter)

    out = []
    for s in samples:
        row = {"name": s["run_id"], "risk": s.get("risk", 0.0),
               "is_hot": bool(s.get("is_hot")), "hot_parts": s.get("hot_parts", [])}
        ori = s.get("orientation")
        if ori:
            row.update({"roll": float(ori[0]), "pitch": float(ori[1]),
                        "yaw": float(ori[2] if len(ori) > 2 else 0.0)})
        out.append(row)
    return out


def select(rows: List[dict], top: Optional[int] = None,
           hot_only: bool = False) -> List[dict]:
    """위험도 내림차순 정렬 후 상위 선별."""
    ranked = sorted(rows, key=lambda r: -r.get("risk", 0.0))
    if hot_only:
        ranked = [r for r in ranked if r.get("is_hot")]
    if top:
        ranked = ranked[:top]
    return ranked


def to_scenario_json(rows: List[dict], kind: str) -> dict:
    """선별 결과 → scenario.json 이 그대로 물릴 수 있는 딕셔너리.

    kind="angles"    → {"angles":    [{name, roll, pitch, yaw}, ...]}
    kind="positions" → {"positions": [{name, x, y}, ...]}

    risk/hot_parts 는 사람이 보고 취사선택하라고 남기지만, 파서는 무시한다.
    """
    if kind == "angles":
        items = [{"name": r["name"], "roll": r["roll"],
                  "pitch": r["pitch"], "yaw": r.get("yaw", 0.0),
                  "risk": round(r.get("risk", 0.0), 4)}
                 for r in rows if "roll" in r and "pitch" in r]
        return {"angles": items}
    if kind == "positions":
        items = [{"name": r["name"], "x": r["x"], "y": r["y"],
                  "risk": round(r.get("risk", 0.0), 4)}
                 for r in rows if "x" in r and "y" in r]
        return {"positions": items}
    raise ValueError(f'지원하지 않는 kind: {kind} (angles | positions)')


def detect_and_harvest(test_dir: str, z_thr: float = 1.5,
                       yield_factor: float = 1.0,
                       parts_filter: Optional[set] = None) -> Tuple[List[dict], str, str]:
    """소스를 자동 판별해 수확한다.

    Returns:
        (rows, kind, source_path) — kind 는 "angles" | "positions"
    """
    sphere = _find_report(test_dir, "sphere_report.json")
    impact = _find_report(test_dir, "impact_report.json")

    # 둘 다 있으면 더 최근 것을 쓴다 (한 테스트 디렉토리에 둘 다 있는 경우는 드물다)
    if sphere and impact:
        if os.path.getmtime(impact) > os.path.getmtime(sphere):
            sphere = None
        else:
            impact = None

    if sphere:
        return harvest_from_sphere(sphere, z_thr, yield_factor, parts_filter), "angles", sphere
    if impact:
        return harvest_from_impact(impact, z_thr, yield_factor, parts_filter), "positions", impact

    # 폴백: 개별 result.json + runner_config 의 각도
    rc = None
    rc_path = os.path.join(test_dir, "runner_config.json")
    if os.path.exists(rc_path):
        with open(rc_path, encoding="utf-8") as f:
            rc = json.load(f)
    rows = harvest_from_results(test_dir, rc, z_thr, yield_factor, parts_filter)
    kind = "angles" if any("roll" in r for r in rows) else "positions"
    if kind == "positions":
        raise ValueError(
            "개별 result.json 만 있고 각도 정보가 없습니다. "
            "충격(위치) 결과는 impact_report.json 이 필요합니다 "
            "(postprocess 로 통합 리포트를 먼저 생성하세요).")
    return rows, kind, os.path.join(test_dir, "result.json(스캔)")
