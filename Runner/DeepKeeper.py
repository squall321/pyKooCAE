# 끝났는데 리포트가 없는 런만 골라 deep_report 를 배열 잡 하나로 다시 내는 후처리 지킴이 — 같은 런을 두 번 내지 않는다
"""KC-07 후처리 지킴이 공통화 (stcx 요청서 v1.0).

캠페인마다 새로 짜던 재제출 스크립트(h89keeper·cyl_keeper·finish.sh·on4_deepprio_hourly·rerep_v42)를 대신한다.
- 대상: 상태 표(KC-06)의 report_wait(해석 정상·리포트 없음) — 그리고 report_failed 는 시도 수 max_attempts 까지.
  health invalid 런은 내지 않는다.
- 같은 런을 두 번 내지 않는다: Run_*/.deep_keeper.json 의 잡이 squeue 에 PENDING·RUNNING 이면 건너뛴다. 한 번에 한 지킴이만
  (출력 폴더 .keeper.lock).
- 한 패스의 대상을 **배열 잡 하나**로 낸다 — 우선순위는 배열 단위로만 바꿀 수 있게(태스크별 scontrol update 금지:
  STCX_HEAD_ROOTFS_SPACE, binlog 시간당 8.8 GB). 지킴이 자신은 우선순위를 바꾸지 않는다.
- 자원 기본: 40 CPU · 400G · 제어 노드(slurmctld 호스트) 제외(STCX_VIZ_HEAD_MASS_SUBMIT_HANG). postprocess.viz 로 바꾼다.
  실측 최대 RSS(deep_report.maxrss_kb)가 요청 메모리보다 크면 실측 × 1.2 로 올린다.
- 기록: 출력 폴더 keeper_log.jsonl(시각·DOE·별칭·동작·까닭).
"""
import fcntl
import json
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from Runner.CampaignStatus import campaign_status

STATE_FILE = ".deep_keeper.json"
LOG_FILE = "keeper_log.jsonl"
DEFAULT_VIZ = {"cpus": 40, "mem": "400G", "time": "04:00:00", "max_parallel": 20, "max_attempts": 2}


def _mem_gb(m: str) -> Optional[float]:
    s = str(m).strip().upper()
    try:
        if s.endswith("T"):
            return float(s[:-1]) * 1024
        if s.endswith("G"):
            return float(s[:-1])
        if s.endswith("M"):
            return float(s[:-1]) / 1024
        return float(s) / 1024   # Slurm 기본 단위 MB
    except ValueError:
        return None


def controller_hosts() -> List[str]:
    """slurmctld 호스트(제어 노드) — 읽기만(scontrol show config)."""
    try:
        p = subprocess.run(["scontrol", "show", "config"], capture_output=True, text=True, timeout=20,
                           encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return []
    hosts = []
    for line in (p.stdout or "").splitlines():
        if line.strip().startswith(("SlurmctldHost", "ControlMachine", "BackupController")):
            v = line.split("=", 1)[-1].strip()
            name = v.split("(")[0].strip()
            if name and name != "(null)":
                hosts.append(name)
    return hosts


def queued_jobs() -> Dict[str, str]:
    """사용자의 대기·실행 잡 id → 상태(배열 태스크는 'JOB_TASK')."""
    try:
        p = subprocess.run(["squeue", "-h", "-u", os.environ.get("USER", ""), "-o", "%i|%T"], capture_output=True,
                           text=True, timeout=30, encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return {}
    out = {}
    for line in (p.stdout or "").splitlines():
        f = line.split("|")
        if len(f) == 2:
            out[f[0].strip()] = f[1].strip()
    return out


def _queued(state: Dict[str, Any], q: Dict[str, str]) -> bool:
    jid = str(state.get("job_id") or "")
    if not jid:
        return False
    idx = state.get("array_index")
    keys = {jid, f"{jid}_{idx}"} if idx is not None else {jid}
    if any(k in q for k in keys):
        return True
    # 아직 시작 안 한 배열 태스크는 squeue 에 'JOB_[0-9,…]' 꼴로 한 줄
    return any(k.startswith(f"{jid}_[") for k in q)


def _read(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _log(out_dir: str, rec: Dict[str, Any]):
    rec = dict(rec, at=datetime.now().isoformat())
    with open(os.path.join(out_dir, LOG_FILE), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def build_array_sbatch(list_path: str, n: int, viz: Dict[str, Any], out_dir: str, job_name: str) -> str:
    excl = viz.get("exclude")
    excl = ",".join(excl) if isinstance(excl, (list, tuple)) else excl
    lines = ["#!/bin/bash", f"#SBATCH --job-name={job_name}", f"#SBATCH --array=0-{n - 1}%{int(viz['max_parallel'])}",
             "#SBATCH --ntasks=1", f"#SBATCH --cpus-per-task={int(viz['cpus'])}", f"#SBATCH --mem={viz['mem']}",
             f"#SBATCH --time={viz['time']}", f"#SBATCH --output={out_dir}/keeper_logs/deep_%A_%a.out", "#SBATCH --chdir=/data"]
    if viz.get("partition"):
        lines.append(f"#SBATCH --partition={viz['partition']}")
    if excl:
        lines.append(f"#SBATCH --exclude={excl}")
    lines += ["# ── 로케일 고정 (컴파일 바이너리의 ascii 기동 방지) ──", "export LANG=C.UTF-8", "export LC_ALL=C.UTF-8",
              "export PYTHONUTF8=1", "export PYTHONIOENCODING=utf-8", "",
              f'RUN="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" {list_path})"',
              'if [ -z "$RUN" ] || [ ! -f "$RUN/deep_report.sh" ]; then echo "[keeper] deep_report.sh 없음: $RUN" >&2; exit 2; fi',
              'echo "[keeper] deep_report: $RUN (task $SLURM_ARRAY_TASK_ID)"',
              'cd "$RUN" && bash "$RUN/deep_report.sh" > "$RUN/deep_report.log" 2>&1', ""]
    return "\n".join(lines)


def keeper_pass(config_path: str, dry_run: bool = False, viz_override: Optional[Dict[str, Any]] = None,
                sbatch_cmd: str = "sbatch") -> Dict[str, Any]:
    """한 패스 — 대상 고르기 → (dry_run 이 아니면) 배열 잡 하나 제출 → 런마다 상태 파일·로그."""
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    out_dir = config["project"]["output_dir"]
    pp = config.get("postprocess") or {}
    if not pp:
        return {"config": config_path, "submitted": 0, "note": "postprocess 블록 없음 — 지킴이가 할 일 없음"}
    viz = dict(DEFAULT_VIZ)
    viz.update({k: v for k, v in (pp.get("viz") or {}).items() if v is not None})
    viz.update({k: v for k, v in (viz_override or {}).items() if v is not None})
    if "exclude" not in (pp.get("viz") or {}) and not (viz_override or {}).get("exclude"):
        viz["exclude"] = controller_hosts()
    lock_path = os.path.join(out_dir, ".keeper.lock")
    lk = open(lock_path, "a", encoding="utf-8")
    try:
        try:
            fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return {"config": config_path, "submitted": 0, "note": "다른 지킴이가 이 캠페인을 보고 있다(.keeper.lock)"}
        jobs = _read(os.path.join(os.path.dirname(os.path.abspath(config_path)), "jobs.json"))
        st = campaign_status(config, jobs)
        q = queued_jobs()
        picks, skipped = [], []
        maxrss = []
        for r in st["rows"]:
            rd = r["run_dir"]
            if not rd:
                continue
            p = os.path.join(rd, "Output", "deep_report.maxrss_kb")
            try:
                with open(p, encoding="utf-8") as f:
                    maxrss.append(int(f.read().split()[-1]))
            except (OSError, ValueError, IndexError):
                pass
            if r["state"] not in ("report_wait", "report_failed"):
                continue
            stt = _read(os.path.join(rd, STATE_FILE)) or {}
            if _queued(stt, q):
                skipped.append((r, "이미 대기·실행 중인 keeper 잡이 있다"))
                continue
            if r["state"] == "report_failed" and int(stt.get("attempts", 0)) >= int(viz["max_attempts"]):
                skipped.append((r, f"시도 {stt.get('attempts')}회 — max_attempts {viz['max_attempts']}"))
                continue
            if r["health"] == "invalid":
                skipped.append((r, "health invalid"))
                continue
            if not os.path.isfile(os.path.join(rd, "deep_report.sh")):
                skipped.append((r, "deep_report.sh 없음 — KooChainRun postprocess --deep 로 만든다"))
                continue
            picks.append((r, stt))
        # 메모리 — 실측 최대 RSS 이상
        mem_note = None
        if maxrss:
            need_gb = max(maxrss) / 1024 / 1024 * 1.2
            have = _mem_gb(viz["mem"])
            if have is not None and need_gb > have:
                mem_note = f"요청 메모리 {viz['mem']} < 실측 최대 RSS {max(maxrss) / 1024 / 1024:.1f} GB × 1.2 — {int(need_gb + 1)}G 로 올린다"
                viz["mem"] = f"{int(need_gb + 1)}G"
        res = {"config": config_path, "candidates": len(picks), "skipped": len(skipped), "viz": viz, "mem_note": mem_note,
               "submitted": 0, "job_id": None, "dry_run": dry_run}
        if not dry_run:
            for r, why in skipped:
                _log(out_dir, {"doe": r["doe"], "alias": r["alias"], "action": "skip", "reason": why})
        if not picks:
            return res
        kd = os.path.join(out_dir, "keeper_logs")
        os.makedirs(kd, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        list_path = os.path.join(kd, f"deep_list_{stamp}.txt")
        with open(list_path, "w", encoding="utf-8") as f:
            for r, _ in picks:
                f.write(r["run_dir"] + "\n")
        sb_path = os.path.join(kd, f"deep_keeper_{stamp}.sbatch")
        with open(sb_path, "w", encoding="utf-8") as f:
            f.write(build_array_sbatch(list_path, len(picks), viz, out_dir, f"deep_keeper_{config.get('project', {}).get('name', '')}"))
        res.update(list=list_path, sbatch=sb_path)
        if dry_run:
            res["would_submit"] = [r["alias"] for r, _ in picks]
            return res
        p = subprocess.run([sbatch_cmd, sb_path], capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
        if p.returncode != 0:
            res["error"] = (p.stderr or p.stdout or "").strip()[-300:]
            for r, _ in picks:
                _log(out_dir, {"doe": r["doe"], "alias": r["alias"], "action": "submit_failed", "reason": res["error"]})
            return res
        jid = (p.stdout or "").strip().split()[-1]
        res.update(submitted=len(picks), job_id=jid)
        for i, (r, stt) in enumerate(picks):
            new = {"job_id": jid, "array_index": i, "submitted_at": datetime.now().isoformat(),
                   "attempts": int(stt.get("attempts", 0)) + 1, "state_at_submit": r["state"]}
            with open(os.path.join(r["run_dir"], STATE_FILE), "w", encoding="utf-8") as f:
                json.dump(new, f, ensure_ascii=False, indent=1)
            _log(out_dir, {"doe": r["doe"], "alias": r["alias"], "action": "submit", "job_id": jid, "array_index": i,
                           "reason": r["state"]})
        return res
    finally:
        try:
            fcntl.flock(lk, fcntl.LOCK_UN)
        except OSError:
            pass
        lk.close()
