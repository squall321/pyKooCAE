# 런마다 실제로 읽은 설정·덱·include·SIF·LS-DYNA 판·잡 정보를 provenance.json 에, 끝난 런 목록을 return_manifest.jsonl 에 남긴다
"""KC-01 런 출처 기록 · 귀환 매니페스트 (stcx 요청서 v1.0).

- 러너가 runner_config.json 을 읽는 순간의 바이트로 sha256 을 잡는다(RUNNER_CONFIG_LIVE_VS_FROZEN — 대기 잡은 고친 값을 먹고
  도는 잡은 requeue 해야 먹는다). 그 사본은 캠페인 출력 폴더 `.kcr_config_snapshots/<sha>.json` 에 한 번만 둔다.
- 런 폴더 `Run_*/provenance.json` — 칸 이름은 DynaForge DF-02 `run.provenance` 와 같게. 모르는 값은 null 이고 `missing` 에 까닭.
- 래퍼는 KooChainRun 이 알 수 없다 — 래퍼가 `KCR_WRAPPER_NAME`·`KCR_WRAPPER_VERSION`·`KCR_WRAPPER_PATH` 를 내보내면 적는다.
  KooChainRun 이 만든 잡 스크립트는 `KCR_JOB_SCRIPT` 를 내보낸다.
- 덱 경로는 runner_config·러너가 실제로 넘긴 입력에서만 잡는다(파일 이름 추측 금지 — DECK_PATH_FROM_RUNNER_CONFIG).
"""
import glob
import hashlib
import json
import os
import socket
import sys
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

SCHEMA = "kcr.provenance/1"
MANIFEST_SCHEMA = "kcr.return_manifest/1"
SNAPSHOT_DIR = ".kcr_config_snapshots"
SHA_CACHE = ".kcr_sha_cache.json"
PREPARE_SCHEMA = "kcr.prepare/1"
# 게이트웨이 GW-03(해석 실적)이 매니페스트에서 읽는 해석 방법 키(사용자 결정 C4, 11-17). 그 밖의 모드는 null
ANALYSIS_METHOD = {"DROP": "ANL-DROP", "IMPACT": "ANL-PARTIAL_IMPACT"}


def prepare_record_path(runner_config_path: str) -> str:
    """prepare 가 runner_config 옆에 남기는 기록 — runner_config 바이트는 그대로 둔다(e2e 가 기준과 바이트 대조)."""
    d, n = os.path.split(os.path.abspath(runner_config_path))
    return os.path.join(d, f".{n}.kcr_prepare.json")


def write_prepare_record(runner_config_path: str, scenario_path: str, extra: Optional[Dict[str, Any]] = None) -> str:
    rec = {"schema": PREPARE_SCHEMA, "prepared_at": datetime.now().isoformat(),
           "scenario_path": os.path.abspath(scenario_path), "scenario_sha256": sha256_file(scenario_path),
           "runner_config_path": os.path.abspath(runner_config_path),
           "runner_config_sha256": sha256_file(runner_config_path)}
    rec.update(extra or {})
    p = prepare_record_path(runner_config_path)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)
    return p

PROVENANCE_FIELDS = (
    "wrapper_name", "wrapper_version", "wrapper_sha256", "prescription_set", "scenario_sha256", "runner_config_sha256",
    "runner_config_read_at", "deck_sha256", "include_sha256", "sif_path", "sif_version", "solver_version", "mpp",
    "deep_report_tool_commit", "deep_report_flags", "slurm_job_id", "array_task_id", "doe", "submitted_at",
    "started_at", "ended_at",
)


def sha256_file(path: str, chunk: int = 4 * 1024 * 1024) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                b = f.read(chunk)
                if not b:
                    break
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class ConfigSnapshot:
    """러너가 읽은 runner_config 바이트 — sha·읽은 시각·사본 경로."""

    def __init__(self, path: str, raw: bytes):
        self.path = os.path.abspath(path)
        self.raw = raw
        self.sha256 = sha256_bytes(raw)
        self.read_at = datetime.now().isoformat()
        self.snapshot_path = None

    def save(self, campaign_dir: str) -> Optional[str]:
        d = os.path.join(campaign_dir, SNAPSHOT_DIR)
        p = os.path.join(d, f"{self.sha256}.json")
        try:
            os.makedirs(d, exist_ok=True)
            if not os.path.exists(p):
                tmp = f"{p}.{os.getpid()}.tmp"
                with open(tmp, "wb") as f:
                    f.write(self.raw)
                os.replace(tmp, p)
            self.snapshot_path = p
        except OSError:
            self.snapshot_path = None
        return self.snapshot_path


def read_config_bytes(path: str):
    """runner_config 를 바이트로 읽어 (dict, ConfigSnapshot) — 러너가 쓰는 값과 해시가 같은 순간의 것."""
    with open(path, "rb") as f:
        raw = f.read()
    return json.loads(raw.decode("utf-8")), ConfigSnapshot(path, raw)


def cached_sha(path: Optional[str], cache_dir: Optional[str]) -> Optional[str]:
    """큰 파일(SIF 1.6 GB)의 sha256 을 (경로·크기·mtime) 열쇠로 캠페인 폴더에 한 번만 잰다."""
    if not path or not os.path.isfile(path):
        return None
    st = os.stat(path)
    key = f"{os.path.abspath(path)}|{st.st_size}|{int(st.st_mtime)}"
    cache = {}
    cp = os.path.join(cache_dir, SHA_CACHE) if cache_dir else None
    if cp and os.path.isfile(cp):
        try:
            with open(cp, encoding="utf-8") as f:
                cache = json.load(f)
        except (OSError, ValueError):
            cache = {}
    if key in cache:
        return cache[key]
    h = sha256_file(path)
    if h and cp:
        cache[key] = h
        try:
            tmp = f"{cp}.{os.getpid()}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=1)
            os.replace(tmp, cp)
        except OSError:
            pass
    return h


def _file_rec(path: Optional[str], cache_dir: Optional[str] = None, big: bool = False) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    rec = {"path": os.path.abspath(path), "exists": os.path.isfile(path)}
    if rec["exists"]:
        st = os.stat(path)
        rec.update(size=st.st_size, mtime=datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                   sha256=cached_sha(path, cache_dir) if big else sha256_file(path))
    return rec


def _sif_label(path: Optional[str]) -> Optional[str]:
    """SIF 판 — 이름 옆 VERSION 파일이나 이름의 _vNN 꼴(없으면 None)."""
    if not path:
        return None
    for cand in (path + ".version", os.path.join(os.path.dirname(path), "VERSION")):
        try:
            with open(cand, encoding="utf-8") as f:
                return f.read().strip()[:80] or None
        except OSError:
            continue
    return None


def slurm_env() -> Dict[str, Any]:
    e = os.environ
    return {
        "slurm_job_id": e.get("SLURM_JOB_ID"), "array_job_id": e.get("SLURM_ARRAY_JOB_ID"),
        "array_task_id": e.get("SLURM_ARRAY_TASK_ID"), "job_name": e.get("SLURM_JOB_NAME"),
        "node": e.get("SLURMD_NODENAME") or socket.gethostname(), "partition": e.get("SLURM_JOB_PARTITION"),
        "submit_dir": e.get("SLURM_SUBMIT_DIR"),
        "job_start_time": e.get("SLURM_JOB_START_TIME"), "restart_count": e.get("SLURM_RESTART_COUNT"),
    }


def wrapper_env(cache_dir: Optional[str] = None) -> Dict[str, Any]:
    e = os.environ
    wp = e.get("KCR_WRAPPER_PATH")
    js = e.get("KCR_JOB_SCRIPT")
    return {
        "wrapper_name": e.get("KCR_WRAPPER_NAME"), "wrapper_version": e.get("KCR_WRAPPER_VERSION"),
        "wrapper_path": wp, "wrapper_sha256": sha256_file(wp) if wp and os.path.isfile(wp) else None,
        "prescription_set": e.get("KCR_PRESCRIPTION_SET"),
        "job_script": js, "job_script_sha256": sha256_file(js) if js and os.path.isfile(js) else None,
    }


def build_provenance(run_dir: str, config: Dict[str, Any], snapshot: Optional[ConfigSnapshot], deck: Optional[str],
                     doe: Optional[int] = None, step: Optional[int] = None, alias: Optional[str] = None,
                     mode: Optional[str] = None, campaign_dir: Optional[str] = None) -> Dict[str, Any]:
    """단계 시작 때의 provenance(끝 시각·판정은 finish_provenance 가 채운다)."""
    env = config.get("environment", {}) or {}
    pp = config.get("postprocess", {}) or {}
    proj = config.get("project", {}) or {}
    cache_dir = campaign_dir or proj.get("output_dir")
    missing: List[str] = []
    P: Dict[str, Any] = {"schema": SCHEMA, "run_dir": os.path.abspath(run_dir), "run_key": alias,
                         "doe": doe, "step": step, "mode": mode, "started_at": datetime.now().isoformat(),
                         "ended_at": None, "submitted_at": None}
    P.update(wrapper_env(cache_dir))
    if not P["wrapper_name"]:
        missing.append("wrapper_name — 래퍼가 KCR_WRAPPER_NAME 을 내보내지 않았다")
    # scenario — prepare 기록(runner_config 옆). 스크래치 모드는 원본 runner_config 경로(KCR_RUNNER_CONFIG_ORIG) 옆을 본다
    rc_orig = os.environ.get("KCR_RUNNER_CONFIG_ORIG") or (snapshot.path if snapshot else None)
    prep = read_json(prepare_record_path(rc_orig)) if rc_orig else None
    P["prepare_record"] = prep
    sc = (prep or {}).get("scenario_path")
    P["scenario_path"] = sc
    P["scenario_sha256"] = sha256_file(sc) if sc and os.path.isfile(sc) else None
    if P["scenario_sha256"] is None:
        missing.append("scenario_sha256 — prepare 기록이 없거나 scenario.json 이 옮겨졌다")
    elif prep.get("scenario_sha256") and prep["scenario_sha256"] != P["scenario_sha256"]:
        missing.append("scenario.json 이 prepare 뒤에 바뀌었다(prepare 때 sha 와 다름)")
    if snapshot:
        P.update(runner_config_path=snapshot.path, runner_config_sha256=snapshot.sha256,
                 runner_config_read_at=snapshot.read_at, runner_config_snapshot=snapshot.snapshot_path)
    else:
        P.update(runner_config_path=None, runner_config_sha256=None, runner_config_read_at=None, runner_config_snapshot=None)
        missing.append("runner_config_sha256 — 러너가 읽은 바이트가 없다")
    orig = os.environ.get("KCR_RUNNER_CONFIG_ORIG")
    if orig:
        P["runner_config_orig_path"], P["runner_config_orig_sha256"] = orig, sha256_file(orig)
    # 덱·include(러너가 실제로 넘기는 입력)
    P["deck"] = _file_rec(deck)
    P["deck_sha256"] = (P["deck"] or {}).get("sha256")
    P["include_sha256"] = []
    P["deck_counts"] = None
    if deck and os.path.isfile(deck):
        try:
            from Runner.DeckScan import scan_deck
            info = scan_deck(deck)
            P["deck_counts"] = {"nodes": info["nodes"], "elements": {k: v for k, v in info["elements"].items() if v},
                                "total_elements": sum(info["elements"].values()), "lines": info["total_lines"]}
            for inc in info["includes"]:
                P["include_sha256"].append({"written": inc["written"], "path": inc["path"], "exists": inc["exists"],
                                            "sha256": cached_sha(inc["path"], cache_dir) if inc["exists"] else None})
        except Exception as e:
            missing.append(f"include_sha256 — 덱 훑기 실패({type(e).__name__})")
    else:
        missing.append("deck_sha256 — 덱이 없다")
    P["model_file"] = _file_rec(proj.get("model_file"), cache_dir, big=True)
    # SIF 셋(KMM·LS-DYNA·Post) — sha 는 캠페인 폴더 캐시로 한 번만
    sifs = {"kmm": env.get("apptainer_sif"), "lsdyna": env.get("lsdyna_apptainer_sif"),
            "post": pp.get("sif_path") or ("/opt/apptainers/SmartTwinPostprocessor.sif" if pp else None)}
    P["sif"] = {k: (dict(_file_rec(v, cache_dir, big=True) or {}, version=_sif_label(v)) if v else None)
                for k, v in sifs.items()}
    P["sif_path"] = sifs["lsdyna"] or sifs["kmm"]
    P["sif_version"] = _sif_label(P["sif_path"])
    P["solver_path"] = env.get("lsdyna_path")
    P["solver_version"], P["mpp"] = None, env.get("ncpu") if env.get("mpi_enabled") else 1
    P["mpp_declared"] = P["mpp"]
    P["deep_report_flags"] = pp.get("deep_extra_args")
    P["deep_report_profile"] = pp.get("profile")
    P["deep_report_tool_commit"] = None
    P.update(slurm_env())
    P["submitted_at"] = _submitted_at(cache_dir, doe)
    P["kooChainRun"] = {"argv0": os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else None}
    P["missing"] = missing
    return P


def _submitted_at(campaign_dir: Optional[str], doe: Optional[int]) -> Optional[str]:
    """jobs.json(제출 기록)의 그 DOE 제출 시각 — 캠페인 폴더의 위(test_dir)에 있다."""
    if not campaign_dir or doe is None:
        return None
    for p in (os.path.join(os.path.dirname(campaign_dir), "jobs.json"), os.path.join(campaign_dir, "jobs.json")):
        try:
            with open(p, encoding="utf-8") as f:
                j = json.load(f)
        except (OSError, ValueError):
            continue
        rec = (j.get("jobs") or {}).get(str(doe)) or {}
        return rec.get("submitted_at") or rec.get("submit_time") or j.get("submitted_at")
    return None


def finish_provenance(P: Dict[str, Any], health: Optional[Dict[str, Any]] = None, status: Optional[str] = None,
                      postprocess: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> Dict[str, Any]:
    P["ended_at"] = datetime.now().isoformat()
    P["status"] = status
    if error:
        P["error"] = error
    if health:
        P["solver_version"] = health.get("solver_version") or P.get("solver_version")
        if health.get("mpp"):
            P["mpp"] = health["mpp"]
        P["health_verdict"] = health.get("verdict")
    if postprocess is not None:
        P["postprocess"] = postprocess
    return P


def write_provenance(run_dir: str, P: Dict[str, Any]) -> str:
    from Runner.RunHealth import json_safe
    p = os.path.join(run_dir, "provenance.json")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(json_safe(P), f, ensure_ascii=False, indent=2, allow_nan=False)
    os.replace(tmp, p)
    return p


def read_json(p: str) -> Optional[Dict[str, Any]]:
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def provenance_for_run(run_dir: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """`KooChainRun provenance <run_dir>` — 기록이 있으면 그것, 없으면(옛 런) 지금 파일로 다시 만든다(missing 에 표시)."""
    P = read_json(os.path.join(run_dir, "provenance.json"))
    if P:
        return P
    cfg, snap = ({}, None)
    if config_path and os.path.isfile(config_path):
        cfg, snap = read_config_bytes(config_path)
    deck = next((os.path.join(run_dir, n) for n in ("DropSet.k", "DropWeightImpactTestSet.k", "ThermalSet.k",
                                                    "VibrationSet.k", "SimulationSet.k")
                 if os.path.isfile(os.path.join(run_dir, n))), None)
    P = build_provenance(run_dir, cfg, snap, deck, campaign_dir=os.path.dirname(os.path.abspath(run_dir)))
    P["reconstructed"] = True
    P["missing"].insert(0, "provenance.json 없음 — 지금 파일로 다시 만든 값(런이 읽은 시점과 다를 수 있다)")
    P["started_at"] = None
    return P


# ── 귀환 매니페스트 ───────────────────────────────────────────────────────
def _index_runs(output_dir: str) -> Dict[str, Dict[str, Any]]:
    """simulation_index(.json·_doe_NNN.json) 의 런 기록을 폴더 이름 → {alias·status·…} 로."""
    runs = {}
    for p in [os.path.join(output_dir, "simulation_index.json")] + sorted(glob.glob(os.path.join(output_dir, "simulation_index_doe_*.json"))):
        j = read_json(p)
        if not j:
            continue
        for alias, r in ((j.get("scenarios") or [{}])[0].get("runs") or {}).items():
            folder = r.get("folder")
            if folder:
                runs[folder] = dict(r, alias=alias)
    return runs


def build_manifest(config: Dict[str, Any], since: Optional[str] = None, query_slurm: bool = True) -> List[Dict[str, Any]]:
    """끝난 런마다 한 줄 — run_key·리포트 경로·provenance·health·extraction. 첫 줄은 머리(래퍼별·설정 sha 별 런 수)."""
    out_dir = (config.get("project") or {}).get("output_dir")
    if not out_dir or not os.path.isdir(out_dir):
        raise FileNotFoundError(f"출력 폴더가 없다: {out_dir}")
    idx = _index_runs(out_dir)
    rows = []
    for rd in sorted(glob.glob(os.path.join(out_dir, "Run_*"))):
        if not os.path.isdir(rd):
            continue
        name = os.path.basename(rd)
        ir = idx.get(name, {})
        P = read_json(os.path.join(rd, "provenance.json"))
        H = read_json(os.path.join(rd, "health.json"))
        X = read_json(os.path.join(rd, "extraction.json"))
        ended = (P or {}).get("ended_at") or ir.get("completed_at")
        if since and ended and ended < since:
            continue
        if not (P or H or ir.get("status") in ("completed", "failed")):
            continue   # 아직 도는 런·빈 폴더
        rep_dir = os.path.join(rd, "Output", "report")
        mode = (P or {}).get("mode") or ir.get("mode")
        rows.append({
            "run_key": ir.get("alias") or (P or {}).get("run_key") or name, "run_dir": rd, "status": ir.get("status"),
            "analysis_method": ANALYSIS_METHOD.get(str(mode).upper()) if mode else None,
            "deck_element_count": ((P or {}).get("deck_counts") or {}).get("total_elements"),
            "report": {"dir": rep_dir, "result_json": os.path.join(rep_dir, "result.json")
                       if os.path.isfile(os.path.join(rep_dir, "result.json")) else None},
            "provenance": P, "health": H, "extraction": X, "ended_at": ended,
        })
    # 잡 상태·잡 끝 코드 — health.json 의 solver_exit_code 와 따로(KC-02 '셋을 따로'). sacct 를 한 번에 묶어 부른다
    try:
        from Runner.CampaignStatus import sacct_states
        sl = sacct_states([(r["provenance"] or {}).get("slurm_job_id") for r in rows]) if query_slurm else {}
    except Exception:
        sl = {}
    for r in rows:
        j = sl.get(str((r["provenance"] or {}).get("slurm_job_id") or ""))
        r["scheduler_state"] = (j or {}).get("state")
        ec = (j or {}).get("exit_code") or ""
        r["chain_exit_code"] = int(ec.split(":")[0]) if ec.split(":")[0].isdigit() else None
        r["solver_exit_code"] = (r["health"] or {}).get("solver_exit_code")
    head = {"schema": MANIFEST_SCHEMA, "generated_at": datetime.now().isoformat(), "output_dir": out_dir,
            "runs": len(rows), "since": since,
            "by_wrapper": _count(r["provenance"].get("wrapper_name") if r["provenance"] else None for r in rows),
            "by_runner_config_sha256": _count(r["provenance"].get("runner_config_sha256") if r["provenance"] else None for r in rows),
            "by_health": _count(r["health"].get("verdict") if r["health"] else None for r in rows),
            "without_provenance": sum(1 for r in rows if not r["provenance"])}
    if len([k for k in head["by_wrapper"] if k != "(없음)"]) > 1:
        head["note"] = "래퍼가 둘 이상 — by_wrapper 로 런 수를 본다"
    return [head] + rows


def _count(vals: Iterable[Optional[str]]) -> Dict[str, int]:
    c: Dict[str, int] = {}
    for v in vals:
        k = v if v else "(없음)"
        c[k] = c.get(k, 0) + 1
    return c


def write_manifest(rows: List[Dict[str, Any]], path: str) -> str:
    from Runner.RunHealth import json_safe
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(json_safe(r), ensure_ascii=False, allow_nan=False) + "\n")
    os.replace(tmp, path)
    return path
