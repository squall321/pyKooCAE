# 캠페인을 내기 전에 정상 파일럿 런 크기 × 런 수 × 동시 수를 출력 파일시스템의 남은 칸·문턱 선과 견줘 통과·축소·거절을 판정한다
"""KC-04 제출 전 디스크 예산 점검 (stcx 요청서 v1.0).

정점 예상(바이트):
  d3plot 삭제 켬  = 런 수 × 끝난 뒤 크기 + (동시 수 + 후처리 대기 여유) × (도는 중 정점 − 끝난 뒤 크기)
  d3plot 삭제 끔  = 런 수 × 도는 중 정점
- 크기는 '중간 종료 런을 뺀 정상 런' 실측이어야 한다 — 파일럿의 health.json 이 valid·warn 이 아니면 경고(요청서 사례 — 런당 86 GB 어림이
  중간 종료 런이 섞인 평균이라 2배 과소였다).
- 끝난 뒤 크기는 extraction.json(지운 크기 기록)이 먼저, 없으면 파일럿에서 d3plot·d3plotNN 을 뺀 크기.
- 문턱은 '남은 칸' 이 아니라 파일시스템 전체의 threshold_pct 선(기본 90 %)까지 — 그 선까지 남은 바이트와 견준다.
- IMPACT: 캠페인 impact.dt·tFinal 의 상태 수가 파일럿과 다르면 d3plot 몫을 그 비로 늘린다(dt 1e-6 이면 1 ms 에 1,000상태 · 런당 486 GB).
판정: pass · reduce_concurrency(넣을 수 있는 동시 수 제안) · enable_delete(삭제를 켜면 들어감) · reject.
"""
import math
import os
import shutil
from typing import Any, Dict, Optional

from Runner.D3plotGate import d3plot_files

DEFAULT_THRESHOLD_PCT = 90.0


def dir_bytes(path: str) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for n in files:
            try:
                total += os.lstat(os.path.join(root, n)).st_size
            except OSError:
                pass
    return total


def pilot_sizes(pilot_run_dir: str) -> Dict[str, Any]:
    """파일럿 런의 도는 중 정점(d3plot 포함)·끝난 뒤(삭제 뒤) 크기."""
    from Runner.RunHealth import read_health, output_dir_of
    X = None
    try:
        import json
        with open(os.path.join(pilot_run_dir, "extraction.json"), encoding="utf-8") as f:
            X = json.load(f)
    except (OSError, ValueError):
        X = None
    total = dir_bytes(pilot_run_dir)
    od = output_dir_of(pilot_run_dir)
    d3 = sum(os.path.getsize(p) for p in d3plot_files(od))
    if X and X.get("deleted_at") and X.get("d3plot_bytes"):
        after, peak, basis = total, total + int(X["d3plot_bytes"]), "extraction.json(지운 d3plot 크기 기록)"
    else:
        after, peak, basis = total - d3, total, "파일럿 실측(d3plot·d3plotNN 을 뺀 크기 = 끝난 뒤)"
    H = read_health(pilot_run_dir) or {}
    return {"run_dir": os.path.abspath(pilot_run_dir), "peak_bytes": peak, "after_bytes": after, "d3plot_bytes": peak - after,
            "basis": basis, "health": H.get("verdict"), "end_time": H.get("end_time"),
            "target_end_time": H.get("target_end_time")}


def _impact_states(config: Dict[str, Any]) -> Optional[float]:
    imp = ((config.get("simulation_params") or {}).get("impact")) or {}
    dt, tf = imp.get("dt"), imp.get("tFinal")
    try:
        return float(tf) / float(dt) if dt and tf else None
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _pilot_config_from_provenance(run_dir: str) -> Optional[Dict[str, Any]]:
    import json
    try:
        with open(os.path.join(run_dir, "provenance.json"), encoding="utf-8") as f:
            snap = json.load(f).get("runner_config_snapshot")
        with open(snap, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError, TypeError):
        return None


def budget(config: Dict[str, Any], pilot_run_dir: str, concurrency: Optional[int] = None,
           threshold_pct: Optional[float] = None, backlog: Optional[int] = None,
           pilot_config: Optional[Dict[str, Any]] = None, fs_path: Optional[str] = None,
           usage=None) -> Dict[str, Any]:
    """판정 dict — verdict·lines(근거 줄)·숫자들. usage(total·used 칸이 있는 것)를 주면 df 대신 쓴다(시험)."""
    env = config.get("environment", {}) or {}
    sb = env.get("storage_budget") or {}
    pp = config.get("postprocess") or {}
    sc = config.get("scenario", {}) or {}
    th = float(threshold_pct if threshold_pct is not None else sb.get("threshold_pct", DEFAULT_THRESHOLD_PCT))
    runs = int(sc.get("doe_count", 0)) * max(1, int(sc.get("total_steps", 1)))
    conc = int(concurrency or sb.get("concurrency") or env.get("max_concurrent") or 0) or None
    lines = []
    if conc is None:
        conc = runs
        lines.append("동시 수를 모른다(--concurrency·environment.storage_budget.concurrency·max_concurrent 없음) — 런 수 전부로 본다")
    back = int(backlog if backlog is not None else sb.get("report_backlog", conc))
    delete_on = bool(pp.get("delete_d3plot_after_deep"))
    P = pilot_sizes(pilot_run_dir)
    if P["health"] not in ("valid", "warn"):
        lines.append(f"⚠ 파일럿 health = {P['health'] or '없음'} — 정상 런 크기가 아닐 수 있다(중간 종료 런은 크기가 작다)")
    peak, after = P["peak_bytes"], P["after_bytes"]
    # IMPACT 상태 수 비 — 파일럿 runner_config(주지 않으면 파일럿 provenance 의 읽은 설정 사본)
    if pilot_config is None:
        pilot_config = _pilot_config_from_provenance(pilot_run_dir)
    s_new, s_old = _impact_states(config), _impact_states(pilot_config or {})
    if s_new and s_old and abs(s_new / s_old - 1) > 1e-6 and P["d3plot_bytes"] > 0:
        scale = s_new / s_old
        d3 = P["d3plot_bytes"] * scale
        lines.append(f"IMPACT 상태 수 {s_old:.0f} → {s_new:.0f}(× {scale:.3g}) 로 d3plot 몫을 늘린다")
        peak = after + d3
    fs = fs_path or (config.get("project", {}) or {}).get("output_dir") or pilot_run_dir
    while fs and not os.path.exists(fs):
        fs = os.path.dirname(fs)
    du = usage if usage is not None else shutil.disk_usage(fs)
    line_bytes = du.total * th / 100.0
    room = line_bytes - du.used
    if delete_on:
        need = runs * after + (conc + back) * max(0.0, peak - after)
    else:
        need = runs * peak
    T = 1024 ** 4
    lines += [f"파일럿 {P['run_dir']} — 도는 중 정점 {peak / 1024**3:.1f} GiB · 끝난 뒤 {after / 1024**3:.1f} GiB ({P['basis']})",
              f"런 {runs} · 동시 {conc} · 후처리 대기 여유 {back} · d3plot 삭제 {'켬' if delete_on else '끔'}",
              f"정점 예상 {need / T:.2f} TiB 대 {th:g} % 선까지 남은 {room / T:.2f} TiB (파일시스템 {fs}: 전체 {du.total / T:.2f} TiB · 사용 {du.used / T:.2f} TiB)"]
    verdict, suggest = "pass", None
    if need > room:
        if delete_on:
            per = max(1.0, peak - after)
            cmax = int(math.floor((room - runs * after) / per)) - back
            if cmax >= 1:
                verdict, suggest = "reduce_concurrency", cmax
                lines.append(f"→ 동시 수를 {cmax} 이하로(후처리 대기 여유 {back} 를 그대로 두면)")
            else:
                verdict = "reject"
                lines.append("→ 끝난 런만으로도 선을 넘는다 — 런 수를 줄이거나 공간을 비울 것")
        else:
            need_on = runs * after + (conc + back) * max(0.0, peak - after)
            if need_on <= room:
                verdict = "enable_delete"
                lines.append(f"→ delete_d3plot_after_deep 을 켜면 정점 {need_on / T:.2f} TiB 로 들어간다")
            else:
                verdict = "reject"
                lines.append("→ 삭제를 켜도 선을 넘는다")
    return {"verdict": verdict, "suggest_concurrency": suggest, "need_bytes": need, "room_bytes": room,
            "threshold_pct": th, "runs": runs, "concurrency": conc, "report_backlog": back, "delete_d3plot": delete_on,
            "pilot": P, "fs": fs, "fs_total": du.total, "fs_used": du.used, "lines": lines}
