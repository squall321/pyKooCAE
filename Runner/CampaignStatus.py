# 캠페인 진행을 디렉토리 이름 추측 없이 DOE·단계마다 한 표(doe_status.csv)로 센다 — index·jobs.json·sacct·health·리포트·추출 기록
"""KC-06 완료 집계 표 (stcx 요청서 v1.0).

상태: norun · pending · running · killed · failed · invalid · solver_done · report_wait · report_failed · report_done · deleted
- 근거: simulation_index(_doe_NNN).json 의 단계 status, jobs.json 의 잡 id, sacct(한 번에 묶어), Run_*/health.json·extraction.json,
  Output/report/{result,analysis_result}.json 이 끝까지 쓰였는지(health.json 기록 → 머리·끝 바이트).
- 'solver_done 수 > report_done 수' 를 따로 보여 후처리 대기(viz 대기열 묶임 — DEEP_REPORT_VIZ_QUEUE_STARVATION)를 드러낸다.
- 읽기만 한다(index 병합본도 쓰지 않는다).
"""
import csv
import json
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from Runner.RunHealth import json_complete, REPORT_FILES

STATES = ("norun", "pending", "running", "killed", "failed", "invalid", "solver_done",
          "report_wait", "report_failed", "report_done", "deleted")


def _read(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def load_index_runs(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """별칭 → 런 기록. 스크래치 모드의 simulation_index_doe_*.json 이 메인 index 보다 앞선다(JobManager 와 같은 순서)."""
    import glob
    proj = config.get("project", {})
    out_dir = proj.get("output_dir", "")
    runs: Dict[str, Dict[str, Any]] = {}
    main = proj.get("index_file") or os.path.join(out_dir, "simulation_index.json")
    for p in [main] + sorted(glob.glob(os.path.join(out_dir, "simulation_index_doe_*.json"))):
        j = _read(p)
        if j and j.get("scenarios"):
            runs.update(j["scenarios"][0].get("runs") or {})
    return runs


def alias_of(config: Dict[str, Any], doe: int, step: int) -> str:
    from Runner.JobManager import JobManager
    return JobManager.__new__(JobManager)._generate_alias(config, doe, step)


def sacct_states(job_ids: List[str]) -> Dict[str, Dict[str, str]]:
    """잡 id → {state, elapsed, exit_code}. sacct 를 묶어서 부르고, 없으면 squeue 한 번."""
    ids = sorted({str(j) for j in job_ids if j})
    out: Dict[str, Dict[str, str]] = {}
    for i in range(0, len(ids), 400):
        chunk = ids[i:i + 400]
        try:
            p = subprocess.run(["sacct", "-j", ",".join(chunk), "-X", "-n", "-P", "--format=JobID,State,Elapsed,ExitCode"],
                               capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
        except (OSError, subprocess.TimeoutExpired):
            break
        for line in (p.stdout or "").splitlines():
            f = line.split("|")
            if len(f) >= 4:
                jid = f[0].split("_")[0].split(".")[0]
                out[jid] = {"state": f[1].split()[0] if f[1] else "", "elapsed": f[2], "exit_code": f[3]}
    missing = [j for j in ids if j not in out]
    if missing:
        try:
            p = subprocess.run(["squeue", "-h", "-o", "%i|%T|%M"], capture_output=True, text=True, timeout=30,
                               encoding="utf-8", errors="replace")
            for line in (p.stdout or "").splitlines():
                f = line.split("|")
                if len(f) >= 3:
                    jid = f[0].split("_")[0]
                    if jid in missing:
                        out.setdefault(jid, {"state": f[1], "elapsed": f[2], "exit_code": ""})
        except (OSError, subprocess.TimeoutExpired):
            pass
    return out


def _report_complete(run_dir: str, health: Optional[Dict[str, Any]]) -> Optional[bool]:
    """리포트 JSON 둘이 끝까지 있는가 — health.json 의 기록이 그 파일(크기·mtime)과 같으면 그것, 아니면 머리·끝 바이트."""
    rd = os.path.join(run_dir, "Output", "report")
    if not os.path.isdir(rd):
        return None
    cached = ((health or {}).get("report") or {}).get("files") or {}
    oks = []
    for name in REPORT_FILES:
        p = os.path.join(rd, name)
        if not os.path.isfile(p):
            continue                    # 둘 중 하나만 있어도 된다(옛 SIF) — 있는 것 중 잘린 것이 없어야 한다
        c = cached.get(name) or {}
        st = os.stat(p)
        if c.get("size") == st.st_size and c.get("mtime") == st.st_mtime and c.get("method") == "parse":
            oks.append(bool(c.get("complete")))
        else:
            oks.append(_fast_complete(p))
    return bool(oks) and all(oks)


def _fast_complete(path: str) -> bool:
    size = os.path.getsize(path)
    if size == 0:
        return False
    with open(path, "rb") as f:
        head = f.read(64).lstrip()
        f.seek(max(0, size - 64))
        tail = f.read().rstrip()
    return (head[:1] == b"{" and tail[-1:] == b"}") or (head[:1] == b"[" and tail[-1:] == b"]")


def campaign_status(config: Dict[str, Any], jobs: Optional[Dict[str, Any]] = None,
                    query_slurm: bool = True) -> Dict[str, Any]:
    """DOE·단계마다 한 줄. jobs = jobs.json 내용(없으면 잡 id 칸이 빈다)."""
    sc = config.get("scenario", {})
    out_dir = config.get("project", {}).get("output_dir", "")
    doe_count, total_steps = int(sc.get("doe_count", 0)), int(sc.get("total_steps", 0))
    pp = config.get("postprocess") or {}
    want_report = bool(pp and pp.get("enabled"))
    runs = load_index_runs(config)
    jobmap = (jobs or {}).get("jobs") or {}
    sl = sacct_states([str((jobmap.get(str(d)) or {}).get("job_id") or "") for d in range(1, doe_count + 1)]) if query_slurm else {}
    rows = []
    for doe in range(1, doe_count + 1):
        jrec = jobmap.get(str(doe)) or {}
        jid = str(jrec.get("job_id") or "")
        sst = (sl.get(jid) or {}).get("state", "") if jid else ""
        for step in range(1, total_steps + 1):
            try:
                alias = alias_of(config, doe, step)
            except (KeyError, IndexError):
                alias = f"DOE{doe:03d}_S{step:03d}"
            r = runs.get(alias) or {}
            folder = r.get("folder") or ""
            rd = os.path.join(out_dir, folder) if folder else ""
            H = _read(os.path.join(rd, "health.json")) if rd else None
            X = _read(os.path.join(rd, "extraction.json")) if rd else None
            ist = r.get("status")
            reason = ""
            if not r:
                state = {"PENDING": "pending", "RUNNING": "running"}.get(sst, "norun")
            elif ist == "running":
                state = "running" if sst in ("RUNNING", "PENDING", "") and jid else "killed"
                if state == "killed":
                    reason = f"index 는 running, 잡은 {sst or '모름'}"
            elif ist == "failed":
                inv = (r.get("health") == "invalid") or ((H or {}).get("verdict") == "invalid")
                state = "invalid" if inv else "failed"
                reason = r.get("error") or ""
                if inv and H and H.get("invalid_reasons"):
                    reason = "; ".join(H["invalid_reasons"])
            elif ist == "completed":
                if not want_report:
                    state = "solver_done"
                else:
                    rc = (r.get("postprocess") or {}).get("rc")
                    comp = _report_complete(rd, H) if rd else None
                    if comp:
                        state = "deleted" if (X and X.get("deleted_at")) else "report_done"
                    elif comp is False and rc not in (None, 0):
                        state, reason = "report_failed", f"deep rc {rc}"
                    elif comp is False:
                        state, reason = "report_failed", "리포트 JSON 이 잘렸거나 하나가 없다"
                    elif rc not in (None, 0):
                        state, reason = "report_failed", f"deep rc {rc}"
                    else:
                        state = "report_wait"
                if H and H.get("verdict") == "warn":
                    reason = (reason + "; " if reason else "") + "health warn: " + "; ".join(H.get("warn_reasons") or [])
            else:
                state = "norun"
            elapsed = ""
            if r.get("started_at") and r.get("completed_at"):
                try:
                    elapsed = str(datetime.fromisoformat(r["completed_at"]) - datetime.fromisoformat(r["started_at"])).split(".")[0]
                except ValueError:
                    elapsed = ""
            elif jid and sl.get(jid):
                elapsed = sl[jid].get("elapsed", "")
            rows.append({"doe": doe, "step": step, "alias": alias, "state": state, "reason": reason[:300],
                         "job_id": jid, "slurm_state": sst, "elapsed": elapsed, "run_dir": rd,
                         "health": (H or {}).get("verdict") or r.get("health") or "",
                         "report_complete": "" if not rd else str(_report_complete(rd, H)),
                         "d3plot_deleted": "" if not X else str(bool(X.get("deleted_at")))})
    summary = {s: sum(1 for r in rows if r["state"] == s) for s in STATES}
    solver_done = sum(summary[s] for s in ("solver_done", "report_wait", "report_failed", "report_done", "deleted"))
    report_done = summary["report_done"] + summary["deleted"]
    return {"rows": rows, "summary": summary, "solver_done": solver_done, "report_done": report_done,
            "report_backlog": solver_done - report_done if want_report else 0, "want_report": want_report,
            "doe_count": doe_count, "total_steps": total_steps, "generated_at": datetime.now().isoformat()}


CSV_FIELDS = ("doe", "step", "alias", "state", "reason", "job_id", "slurm_state", "elapsed", "health",
              "report_complete", "d3plot_deleted", "run_dir")


def write_csv(st: Dict[str, Any], path: str) -> str:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in st["rows"]:
            w.writerow(r)
    os.replace(tmp, path)
    return path


def summary_lines(st: Dict[str, Any]) -> List[str]:
    s = st["summary"]
    lines = [f"DOE {st['doe_count']} × 단계 {st['total_steps']} = {len(st['rows'])} 칸",
             "  " + " · ".join(f"{k} {v}" for k, v in s.items() if v)]
    if st["want_report"]:
        lines.append(f"  해석 끝 {st['solver_done']} · 리포트 끝 {st['report_done']}"
                     + (f" — 🔴 후처리 대기 {st['report_backlog']}(viz 대기열을 볼 것)" if st["report_backlog"] > 0 else ""))
    return lines
