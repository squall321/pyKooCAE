# 적응 샘플링 Phase 3 — 완료 결과 기반 대기 잡 우선순위 재배치 (scontrol top/hold)
"""
모델 C 의 실행 훅. 이미 던져진(고정 격자) DOE 잡들 중 "대기 중"인 것을, 완료 결과의
위험영역 근처 순으로 재배치한다. 새 잡을 만들지 않는다.

흐름:
  1) runner_config → DOE별 방향(roll/pitch/yaw)  = 고정 격자
  2) jobs.json     → DOE별 slurm job_id
  3) output_dir 의 result.json harvest → 완료 DOE(=실행) + per-part 리스크
     (Phase 1 AdaptiveOrientation.harvest/compute_risk 재사용)
  4) 미실행 DOE(=대기) 의 우선순위 = 핫 방향 근접도 (Phase 2 prioritize_unrun)
  5) plan(): 대기 잡을 top(우선)/hold(후순위) 로 분류
  6) apply(): scontrol top(주) / hold(폴백). dry-run 기본.

squeue 없이 동작 — "대기"는 result.json 부재로 판정(현재 큐 불안정 회피). 실제 적용 시
scontrol top 은 enable_user_top 필요, 안 되면 far 잡 hold 로 폴백.

계획: docs/PLAN_AdaptiveOrientationSampling.md (모델 C)
"""
import os
import re
import json
import shutil
import subprocess
from typing import Dict, List, Optional

from Runner.AdaptiveOrientation import (
    harvest, compute_risk, euler_to_vec, prioritize_unrun,
)


def _doe_orientations(runner_config: dict) -> Dict[int, tuple]:
    """runner_config → {doe(1-based): (roll,pitch,yaw)} = 고정 격자.

    권위 소스는 scenario.doe_angles = {doe(1-based str): {step: {roll,pitch,yaw}}}.
    DROP 단일 스텝이면 step 1 의 각도. 없으면 scenarios(plural) doe_index(0-based)+1 폴백.
    """
    out = {}
    sc = runner_config.get("scenario") or {}
    for doe_str, steps in (sc.get("doe_angles") or {}).items():
        if not isinstance(steps, dict) or not steps:
            continue
        first = steps[sorted(steps, key=lambda x: int(x))[0]]
        roll, pitch, yaw = first.get("roll"), first.get("pitch"), first.get("yaw", 0.0)
        if roll is not None and pitch is not None:
            out[int(doe_str)] = (float(roll), float(pitch), float(yaw or 0.0))
    if out:
        return out
    for s in runner_config.get("scenarios", []):  # 폴백: doe_index 0-based → +1
        for st in s.get("steps", []):
            ang = st.get("angle") or {}
            roll = ang.get("roll", ang.get("angle_roll"))
            pitch = ang.get("pitch", ang.get("angle_pitch"))
            yaw = ang.get("yaw", ang.get("angle_yaw", 0.0))
            di = st.get("doe_index")
            if roll is not None and pitch is not None and di is not None:
                out[int(di) + 1] = (float(roll), float(pitch), float(yaw or 0.0))
    return out


def _doe_jobs(jobs_json: dict) -> Dict[int, dict]:
    """jobs.json → {doe(1-based): {job_id, status}} (job_name '..._DOE%03d')."""
    out = {}
    jobs = jobs_json.get("jobs", {})
    items = jobs.values() if isinstance(jobs, dict) else jobs
    for j in items:
        m = re.search(r"DOE0*(\d+)", str(j.get("job_name", "")))
        if m and j.get("job_id"):
            out[int(m.group(1))] = {"job_id": str(j["job_id"]), "status": j.get("status")}
    return out


def _run_doe_index(output_dir: str):
    """simulation_index.json → ({folder(=harvest run_id): doe(1-based)}, 완료 doe set).

    Run 디렉토리는 Run_<타임스탬프>_<해시> 라 경로에서 doe 를 못 뽑는다. simulation_index
    의 alias('..._DOE001_...')→folder('Run_<ts>') 매핑으로 run↔doe 를 잇는다.
    """
    folder2doe: Dict[str, int] = {}
    completed = set()
    p = os.path.join(output_dir, "simulation_index.json")
    if not os.path.exists(p):
        return folder2doe, completed
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return folder2doe, completed
    for sc in d.get("scenarios", []):
        for alias, info in (sc.get("runs") or {}).items():
            m = re.search(r"DOE0*(\d+)", alias)
            if not m:
                continue
            doe = int(m.group(1))
            folder = info.get("folder") or (f"Run_{info['run_id']}" if info.get("run_id") else None)
            if folder:
                folder2doe[folder] = doe
            if info.get("status") == "completed":
                completed.add(doe)
    return folder2doe, completed


def plan(test_dir: str, runner_config: dict, jobs_json: dict,
         radius_deg: float = 25.0, kernel: str = "gaussian",
         z_thr: float = 1.5, yield_factor: float = 1.0,
         top_n: Optional[int] = None, hold_far: bool = True) -> dict:
    """대기 잡 재배치 계획. 반환: {top:[{doe,job_id,priority}], hold:[{doe,job_id}], 통계}."""
    orient = _doe_orientations(runner_config)
    doe_jobs = _doe_jobs(jobs_json)
    output_dir = (runner_config.get("project", {}) or {}).get("output_dir") \
        or os.path.join(test_dir, "output")
    folder2doe, completed = _run_doe_index(output_dir)

    # 완료 결과 → 실행 DOE + 리스크 (run_id=folder 로 doe 매핑)
    run_samples = []
    for s in harvest(output_dir):
        doe = folder2doe.get(s["run_id"])
        if doe is None or doe not in orient:
            continue
        s["doe"] = doe
        s["vec"] = euler_to_vec(*orient[doe])
        run_samples.append(s)
    compute_risk(run_samples, z_thr=z_thr, yield_factor=yield_factor)

    # 고정 격자 = 모든 DOE 방향 (이름에 doe 인코딩)
    lattice = [(f"DOE{d}", *orient[d]) for d in sorted(orient)]
    ranked = prioritize_unrun(run_samples, lattice, radius_deg=radius_deg, kernel=kernel)

    top, hold = [], []
    for r in ranked:
        d = int(r["name"][3:])
        if d in completed:  # 이미 완료된 doe (결과 삭제 등) → 재배치 대상 아님
            continue
        jb = doe_jobs.get(d)
        if not jb:  # 잡 없음(미제출) → 건너뜀
            continue
        if r["priority"] > 0:
            top.append({"doe": d, "job_id": jb["job_id"], "priority": r["priority"]})
        elif hold_far:
            hold.append({"doe": d, "job_id": jb["job_id"]})
    if top_n:
        top = top[:top_n]
    return {
        "top": top, "hold": hold,
        "n_doe": len(orient), "n_run": len(run_samples),
        "n_hot": sum(1 for s in run_samples if s.get("is_hot")),
        "n_pending_jobs": len([d for d in doe_jobs if d not in completed]),
    }


def _scontrol_top_ok() -> bool:
    """scontrol top 사용 가능성(대략) — scontrol 존재 여부. 실제 enable_user_top 은
    호출 시 실패로 판별(폴백)."""
    return shutil.which("scontrol") is not None


def apply(plan_result: dict, dry_run: bool = True, prefer_top: bool = True) -> List[List[str]]:
    """plan 을 scontrol 로 적용. top(주)/hold(폴백). dry_run=True 면 명령만 반환(실행 X).

    top 은 '나중에 top 한 잡이 더 위' 이므로 우선순위 낮은 것부터(reverse) 적용해
    최우선 잡이 큐 최상단에 오게 한다. top 이 막히면 far 잡 hold 로 효과.
    """
    cmds: List[List[str]] = []
    top_ids = [t["job_id"] for t in plan_result.get("top", [])]
    if prefer_top:
        for jid in reversed(top_ids):  # 최우선이 마지막 → 큐 최상단
            cmds.append(["scontrol", "top", jid])
    for h in plan_result.get("hold", []):
        cmds.append(["scontrol", "hold", h["job_id"]])

    if dry_run:
        return cmds

    top_failed = False
    for c in cmds:
        try:
            r = subprocess.run(c, capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                if c[1] == "top":
                    top_failed = True
                print(f"[reprioritize] {' '.join(c)} → rc={r.returncode} {r.stderr.strip()[:120]}")
        except Exception as e:
            print(f"[reprioritize] {' '.join(c)} 실패: {e}")
    # top 이 막혔으면(enable_user_top off) 폴백: top 대상 외 대기 잡을 hold 로 후순위화
    if top_failed and prefer_top:
        print("[reprioritize] scontrol top 불가 → far 잡 hold 폴백 권장 (--hold-fallback)")
    return cmds


def _main():
    import argparse
    ap = argparse.ArgumentParser(description="적응 샘플링 Phase3 — 대기 잡 재우선순위")
    ap.add_argument("test_dir", help="runner_config.json + jobs.json 이 있는 디렉토리")
    ap.add_argument("--apply", action="store_true", help="실제 scontrol 실행 (기본: dry-run)")
    ap.add_argument("--radius-deg", type=float, default=25.0)
    ap.add_argument("--z-thr", type=float, default=1.5)
    ap.add_argument("--top-n", type=int, default=None)
    args = ap.parse_args()

    rc_path = os.path.join(args.test_dir, "runner_config.json")
    jj_path = os.path.join(args.test_dir, "jobs.json")
    if not os.path.exists(rc_path) or not os.path.exists(jj_path):
        print("runner_config.json / jobs.json 필요:", args.test_dir)
        return
    rc = json.load(open(rc_path, encoding="utf-8"))
    jj = json.load(open(jj_path, encoding="utf-8"))
    pl = plan(args.test_dir, rc, jj, radius_deg=args.radius_deg, z_thr=args.z_thr, top_n=args.top_n)
    print(f"DOE {pl['n_doe']} / 실행 {pl['n_run']} / 핫 {pl['n_hot']} / 잡 {pl['n_pending_jobs']}")
    print(f"top(우선) {len(pl['top'])}개, hold(후순위) {len(pl['hold'])}개")
    for t in pl["top"][:10]:
        print(f"  TOP doe={t['doe']} job={t['job_id']} priority={t['priority']:.3f}")
    cmds = apply(pl, dry_run=not args.apply)
    print(f"\n{'적용됨' if args.apply else 'DRY-RUN'} — scontrol 명령 {len(cmds)}개:")
    for c in cmds[:12]:
        print("  ", " ".join(c))


if __name__ == "__main__":
    _main()
