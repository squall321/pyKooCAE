# 낙하 방향 적응 샘플링 (Phase 1) — 완료 deep_report 결과 harvest + per-part 리스크 판정
"""
적응형 낙하 방향 재우선순위(Adaptive Orientation Refinement)의 분석 코어.

Phase 1 범위 (신규 시뮬 없음, 이미 완료된 결과만 읽음):
  - harvest(): test_dir 하위의 deep_report result.json 들을 찾아 run별
    per-part 최대응력(peak_stress) 수집. deep 출력 layout 2종 지원:
      <run>/Output/report/result.json        (chainrun inline)
      <test_dir>/deep_reports/<run>/result.json  (batch)
  - compute_risk(): per-part z-score(평균 대비 상대) + yield 절대비, 둘 다 병행으로
    각 방향(run)의 risk·is_hot 판정.
  - hotspots(): 리스크 높은 run 정렬.

방향(roll/pitch/yaw)→단위벡터 변환(euler_to_vec)도 제공 — Phase 2/3(근접 기반
대기 잡 재우선순위)에서 사용. risk 계산 자체는 방향 없이도 동작한다.

계획: docs/PLAN_AdaptiveOrientationSampling.md
"""
import os
import json
import glob
import math
from typing import Dict, List, Optional, Tuple


def euler_to_vec(roll: float, pitch: float, yaw: float = 0.0) -> Tuple[float, float, float]:
    """AngleSourceParser 의 vector→euler 규약(roll=deg(lat)-90, pitch=-deg(lon)) 역변환.

    낙하 방향을 구면 단위벡터로 — 방향 간 각거리(근접도) 계산용.
    """
    lat = math.radians(roll + 90.0)
    lon = math.radians(-pitch)
    cl = math.cos(lat)
    return (cl * math.cos(lon), math.sin(lat), cl * math.sin(lon))


def angular_distance(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> float:
    """두 단위벡터 사이 각거리(라디안)."""
    d = max(-1.0, min(1.0, v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]))
    return math.acos(d)


def _run_id_from_path(p: str) -> str:
    parts = p.replace("\\", "/").split("/")
    for seg in parts:
        if seg.startswith("Run_"):
            return seg
    return parts[-2] if len(parts) >= 2 else p


def _peak_stress_by_part(result_json_path: str) -> Dict[str, dict]:
    """result.json → {pid: {name, peak_stress, stress_limit}}."""
    with open(result_json_path, encoding="utf-8") as f:
        d = json.load(f)
    out = {}
    for pid, info in (d.get("parts") or {}).items():
        ps = info.get("peak_stress")
        if ps is None:
            continue
        out[str(pid)] = {
            "name": info.get("name", ""),
            "peak_stress": float(ps),
            # stress_limit(=yield). 0/None 이면 절대 기준 미적용.
            "stress_limit": float(info.get("stress_limit") or 0.0),
        }
    return out


def harvest(test_dir: str, runner_config: Optional[dict] = None) -> List[dict]:
    """test_dir 하위 모든 result.json 수집 → run별 per-part 최대응력 샘플 리스트.

    반환: [{run_id, result_path, parts:{pid:{name,peak_stress,stress_limit}},
            orientation:(roll,pitch,yaw)|None, vec:(x,y,z)|None}]
    같은 run_id 가 중복(두 layout 공존) 시 첫 번째만 사용.
    """
    paths = sorted(set(glob.glob(os.path.join(test_dir, "**", "result.json"), recursive=True)))
    samples = []
    seen = set()
    for p in paths:
        try:
            parts = _peak_stress_by_part(p)
        except Exception:
            continue
        if not parts:
            continue
        rid = _run_id_from_path(p)
        if rid in seen:
            continue
        seen.add(rid)
        samples.append({
            "run_id": rid,
            "result_path": p,
            "parts": parts,
            "orientation": None,
            "vec": None,
        })
    if runner_config:
        _attach_orientation(samples, runner_config)
    return samples


def _attach_orientation(samples: List[dict], runner_config: dict) -> None:
    """runner_config 의 step angle 을 run_id(Run_<doe>) 기준으로 best-effort 매핑."""
    by_doe = {}
    for sc in runner_config.get("scenarios", []):
        for st in sc.get("steps", []):
            ang = st.get("angle") or {}
            roll = ang.get("angle_roll", ang.get("roll"))
            pitch = ang.get("angle_pitch", ang.get("pitch"))
            yaw = ang.get("angle_yaw", ang.get("yaw", 0.0))
            if roll is None or pitch is None:
                continue
            by_doe[int(st.get("doe_index", -1))] = (float(roll), float(pitch), float(yaw))
    for s in samples:
        rid = s["run_id"]
        doe = None
        tail = rid.split("Run_")[-1]
        if tail.isdigit():
            doe = int(tail)
        if doe is not None and doe in by_doe:
            o = by_doe[doe]
            s["orientation"] = o
            s["vec"] = euler_to_vec(*o)


def compute_risk(samples: List[dict], z_thr: float = 1.5, yield_factor: float = 1.0,
                 w_z: float = 1.0, w_a: float = 1.0,
                 parts_filter: Optional[set] = None) -> List[dict]:
    """각 sample 에 risk(점수)·is_hot·hot_parts 주석. (상대 z-score + yield 절대, 둘 다)

    - 상대: 파트 p 의 전 방향 평균 μ_p·표준편차 s_p → z_p=(σ−μ)/s
    - 절대: a_p = σ / yield_p (yield 미지정 시 생략)
    - risk(o) = max_p ( w_z·max(0,z_p) + w_a·max(0, a_p−1) )
    - is_hot = 어떤 파트라도 (z_p ≥ z_thr) 또는 (a_p ≥ yield_factor)
    """
    part_vals: Dict[str, List[float]] = {}
    for s in samples:
        for pid, info in s["parts"].items():
            if parts_filter and pid not in parts_filter:
                continue
            part_vals.setdefault(pid, []).append(info["peak_stress"])

    stats = {}
    for pid, vals in part_vals.items():
        n = len(vals)
        mu = sum(vals) / n
        var = sum((v - mu) ** 2 for v in vals) / n if n > 0 else 0.0
        stats[pid] = (mu, math.sqrt(var))

    for s in samples:
        risk = 0.0
        hot = False
        hot_parts = []
        for pid, info in s["parts"].items():
            if parts_filter and pid not in parts_filter:
                continue
            mu, sd = stats.get(pid, (0.0, 0.0))
            sigma = info["peak_stress"]
            z = (sigma - mu) / sd if sd > 1e-30 else 0.0
            yld = info["stress_limit"]
            a = (sigma / yld) if yld > 1e-30 else 0.0
            contrib = w_z * max(0.0, z) + w_a * max(0.0, a - 1.0)
            if contrib > risk:
                risk = contrib
            if (z >= z_thr) or (yld > 1e-30 and a >= yield_factor):
                hot = True
                hot_parts.append({"pid": pid, "name": info["name"],
                                  "z": round(z, 2), "a": round(a, 2), "stress": sigma})
        s["risk"] = round(risk, 4)
        s["is_hot"] = hot
        s["hot_parts"] = hot_parts
    return samples


def hotspots(samples: List[dict]) -> List[dict]:
    """is_hot 인 sample 을 risk 내림차순으로."""
    return sorted([s for s in samples if s.get("is_hot")], key=lambda s: -s.get("risk", 0.0))


def _main():
    import argparse
    ap = argparse.ArgumentParser(description="적응 샘플링 Phase1 — 결과 harvest + 리스크 판정")
    ap.add_argument("test_dir", help="deep_report result.json 들이 있는 루트")
    ap.add_argument("--z-thr", type=float, default=1.5)
    ap.add_argument("--yield-factor", type=float, default=1.0)
    args = ap.parse_args()

    samples = harvest(args.test_dir)
    if not samples:
        print("result.json 을 찾지 못했습니다:", args.test_dir)
        return
    compute_risk(samples, z_thr=args.z_thr, yield_factor=args.yield_factor)
    hot = hotspots(samples)
    print(f"수집된 run: {len(samples)}개  /  핫: {len(hot)}개  (z_thr={args.z_thr})")
    print("--- 리스크 상위 ---")
    for s in sorted(samples, key=lambda x: -x["risk"])[:10]:
        flag = "HOT" if s["is_hot"] else "   "
        hp = ", ".join(f"{h['name']}(z={h['z']})" for h in s["hot_parts"][:3])
        print(f"  [{flag}] risk={s['risk']:.2f}  {s['run_id']}  {hp}")


if __name__ == "__main__":
    _main()
