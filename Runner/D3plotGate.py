# d3plot 을 지우기 전에 리포트 완결·필수 추출·삭제 허가·건강을 확인하고, 통과한 런만 지운 뒤 extraction.json 에 남긴다
"""KC-03 삭제 전 추출 · d3plot 삭제 관문 (stcx 요청서 v1.0).

예전: deep_report.sh 가 koo_deep_report rc 0 뒤 `delete_d3plot_after_deep` 이면 확인 없이 `rm d3plot*`.
지금: 관문(`KooChainRun d3plot-delete <run_dir> --gate`)이 아래를 다 볼 때만 지운다. 못 지우면 지우지 않고 까닭을 남긴다.
  ① Output/report/result.json · analysis_result.json 이 끝까지 읽힘(d3plot 을 지운 뒤 impact·harvest 가 이 둘을 다시 읽는다)
  ② postprocess.required_extractions 의 산출 파일이 다 있음(명령이 있으면 관문 앞 `extract` 가 돌린다)
  ③ postprocess.deletion_clearance(file·url) 를 설정했으면 그 허가
  ④ health.json 이 invalid 가 아님(없으면 보지 않음)
지우는 것은 d3plot·d3plotNN 뿐이다. result.json·analysis_result.json·step_config.txt 는 옮기지도 지우지도 않는다.

required_extractions 항목(목록): {"name": 이름, "command": 셸 명령(선택, {run_dir}·{output_dir}·{report_dir} 치환),
  "outputs": [Output 기준 상대 경로 또는 절대 경로, …], "timeout_seconds": 초(선택), "kind": "peak"|"field"|…(선택)}
  산출물이 JSON 이고 states_total·states_read·peak 칸이 있으면 extraction.json 에 옮긴다.
deletion_clearance: {"file": 경로} — JSON {"cleared": true} 또는 {"runs": [run_key, …]}
                    {"url": "...{run_key}..."} — GET 한 JSON 이 {"cleared": true}·{"allowed": true}·{"runs": [...]} (DynaForge DF-04
                    형식 확정 전의 가정. 형식이 정해지면 여기만 맞춘다)
"""
import glob
import json
import math
import os
import shlex
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from Runner.RunHealth import output_dir_of, read_health, report_status, json_complete

SCHEMA = "kcr.extraction/1"
D3PLOT_GLOBS = ("d3plot", "d3plot[0-9]*")


def d3plot_files(output_dir: str) -> List[str]:
    out = []
    for g in D3PLOT_GLOBS:
        out.extend(p for p in glob.glob(os.path.join(output_dir, g)) if os.path.isfile(p))
    return sorted(set(out))


def kcr_command(config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """deep_report.sh 가 부를 KooChainRun 명령(셸 문자열). environment.koochainrun_path > KCR_BIN > 지금 실행 파일."""
    env = (config or {}).get("environment", {}) or {}
    p = env.get("koochainrun_path") or os.environ.get("KCR_BIN")
    if p:
        return shlex.quote(p)
    if "__compiled__" in globals():
        return shlex.quote(os.path.abspath(sys.argv[0]))
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "KooChainRun")
    if os.path.isfile(src):
        return f"{shlex.quote(sys.executable)} {shlex.quote(src)}"
    return None


def _subst(text: str, run_dir: str) -> str:
    od = output_dir_of(run_dir)
    return (text.replace("{run_dir}", run_dir).replace("{output_dir}", od)
            .replace("{report_dir}", os.path.join(od, "report")))


def _out_path(run_dir: str, rel: str) -> str:
    rel = _subst(rel, run_dir)
    return rel if os.path.isabs(rel) else os.path.join(output_dir_of(run_dir), rel)


def run_extractions(run_dir: str, spec: Optional[List[Dict[str, Any]]], run_commands: bool = True) -> List[Dict[str, Any]]:
    """필수 추출을 (명령이 있으면) 돌리고 산출물을 확인한다. 반환: 항목별 {name·ran·rc·outputs[{path·exists·size·complete}]·ok}."""
    res = []
    for item in spec or []:
        name = str(item.get("name") or f"extraction_{len(res) + 1}")
        rec: Dict[str, Any] = {"name": name, "kind": item.get("kind"), "ran": False, "rc": None, "ok": False}
        cmd = item.get("command")
        if cmd and run_commands:
            outs_ok = all(_output_ok(_out_path(run_dir, o)) for o in item.get("outputs") or [])
            if outs_ok and item.get("outputs") and not item.get("always_run"):
                rec["skipped"] = "산출물이 이미 있다"
            else:
                c = _subst(cmd, run_dir)
                try:
                    p = subprocess.run(["bash", "-c", c], cwd=output_dir_of(run_dir), capture_output=True, text=True,
                                       timeout=int(item.get("timeout_seconds") or 7200), encoding="utf-8", errors="replace")
                    rec.update(ran=True, rc=p.returncode, stderr_tail=(p.stderr or "")[-400:])
                except subprocess.TimeoutExpired:
                    rec.update(ran=True, rc=None, error="시간 초과")
                except OSError as e:
                    rec.update(ran=True, rc=None, error=str(e))
        outs = []
        for o in item.get("outputs") or []:
            path = _out_path(run_dir, o)
            r = {"path": path, "exists": os.path.isfile(path), "size": os.path.getsize(path) if os.path.isfile(path) else 0}
            r["complete"] = json_complete(path, full=True)["complete"] if path.endswith(".json") and r["exists"] else (r["exists"] and r["size"] > 0)
            if path.endswith(".json") and r["complete"]:
                try:
                    with open(path, encoding="utf-8") as f:
                        j = json.load(f)
                    if isinstance(j, dict):
                        r["meta"] = {k: j[k] for k in ("states_total", "states_read", "peak", "peak_source") if k in j}
                except (OSError, ValueError):
                    pass
            outs.append(r)
        rec["outputs"] = outs
        failed_cmd = rec["ran"] and rec["rc"] != 0
        rec["ok"] = bool(outs) and all(r["complete"] for r in outs) and not failed_cmd
        if not item.get("outputs"):
            rec["ok"] = False
            rec["error"] = "outputs 가 없다 — 무엇이 끝났는지 확인할 수 없다"
        res.append(rec)
    return res


def _output_ok(path: str) -> bool:
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        return False
    return json_complete(path)["complete"] if path.endswith(".json") else True


def check_clearance(run_dir: str, run_key: Optional[str], clearance: Optional[Dict[str, Any]],
                    require: bool = False) -> Dict[str, Any]:
    """삭제 허가. 설정이 없으면 require 일 때만 거절."""
    if not clearance:
        return {"configured": False, "granted": not require,
                "reason": "허가 설정 없음 — --require-clearance 라 지우지 않는다" if require else None}
    key = run_key or os.path.basename(os.path.abspath(run_dir))
    doc, src = None, None
    try:
        if clearance.get("file"):
            src = _subst(str(clearance["file"]), run_dir)
            with open(src, encoding="utf-8") as f:
                doc = json.load(f)
        elif clearance.get("url"):
            import urllib.request
            src = str(clearance["url"]).replace("{run_key}", key)
            with urllib.request.urlopen(src, timeout=float(clearance.get("timeout", 10))) as r:
                doc = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"configured": True, "granted": False, "source": src, "reason": f"허가를 읽지 못했다({type(e).__name__}: {e})"}
    ok = isinstance(doc, dict) and (doc.get("cleared") is True or doc.get("allowed") is True or key in (doc.get("runs") or []))
    return {"configured": True, "granted": bool(ok), "source": src, "reason": None if ok else f"허가 목록에 {key} 가 없다"}


def gate(run_dir: str, config: Optional[Dict[str, Any]] = None, run_key: Optional[str] = None,
         require_clearance: bool = False, run_commands: bool = True) -> Dict[str, Any]:
    """지워도 되는가 — {delete, reasons[], report, extractions[], clearance, health_verdict}."""
    pp = (config or {}).get("postprocess", {}) or {}
    od = output_dir_of(run_dir)
    reasons = []
    rep = report_status(od, full=True)        # 되돌릴 수 없는 판단 — 크기와 상관없이 끝까지 읽는다(리뷰 중4)
    if not rep["complete_all"]:
        bad = [f"{n}({'잘림' if v['exists'] else '없음'})" for n, v in rep["files"].items() if not v["complete"]]
        reasons.append(f"리포트 JSON 이 완결이 아니다 — {', '.join(bad)}(d3plot 을 지운 뒤 harvest·impact 가 둘 다 다시 읽는다)")
    ex = run_extractions(run_dir, pp.get("required_extractions"), run_commands=run_commands)
    for e in ex:
        if not e["ok"]:
            reasons.append(f"필수 추출 {e['name']} 이 끝나지 않았다" + (f"(rc {e['rc']})" if e.get("rc") not in (None, 0) else ""))
    cl = check_clearance(run_dir, run_key, pp.get("deletion_clearance"), require=require_clearance)
    if not cl["granted"]:
        reasons.append(cl["reason"] or "삭제 허가가 없다")
    H = read_health(run_dir)
    hv = (H or {}).get("verdict")
    if hv == "invalid":
        reasons.append("health 가 invalid — 다시 볼 수 있게 d3plot 을 남긴다")
    return {"delete": not reasons, "reasons": reasons, "report": rep, "extractions": ex, "clearance": cl,
            "health_verdict": hv, "d3plot_files": [os.path.basename(p) for p in d3plot_files(od)]}


def _states_estimate(run_dir: str) -> Optional[int]:
    H = read_health(run_dir) or {}
    end = H.get("end_time")
    try:
        from Runner.DeckScan import scan_deck
        deck = next((os.path.join(run_dir, n) for n in ("DropSet.k", "DropWeightImpactTestSet.k", "ThermalSet.k",
                                                        "VibrationSet.k", "SimulationSet.k")
                     if os.path.isfile(os.path.join(run_dir, n))), None)
        dt = scan_deck(deck)["d3plot_dt"] if deck else None
    except Exception:
        dt = None
    if end and dt and dt > 0:
        return int(math.floor(end / dt + 1e-9)) + 1
    return None


def write_extraction(run_dir: str, X: Dict[str, Any]) -> str:
    p = os.path.join(run_dir, "extraction.json")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(X, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)
    return p


def gate_and_delete(run_dir: str, config: Optional[Dict[str, Any]] = None, run_key: Optional[str] = None,
                    require_clearance: bool = False, dry_run: bool = False, run_commands: bool = True) -> Dict[str, Any]:
    """관문을 보고 통과하면 d3plot 을 지운다. extraction.json 을 쓰고 그 내용을 돌려준다."""
    od = output_dir_of(run_dir)
    G = gate(run_dir, config, run_key=run_key, require_clearance=require_clearance, run_commands=run_commands)
    files = d3plot_files(od)
    nbytes = sum(os.path.getsize(p) for p in files)
    X: Dict[str, Any] = {"schema": SCHEMA, "run_dir": os.path.abspath(run_dir), "run_key": run_key,
                         "evaluated_at": datetime.now().isoformat(), "gate": G, "d3plot_bytes": nbytes,
                         "states_total": None, "states_read": None, "peak_source": None, "fields_extracted": [],
                         "d3plot_retained": True, "deleted_at": None, "deleted_files": [], "retained_reasons": G["reasons"]}
    for e in G["extractions"]:
        if e["ok"]:
            X["fields_extracted"].append(e["name"])
        for o in e.get("outputs", []):
            m = o.get("meta") or {}
            if m.get("states_total") is not None:
                X["states_total"] = m["states_total"]
            if m.get("states_read") is not None and (e.get("kind") == "peak" or X["states_read"] is None):
                X["states_read"] = m["states_read"]
            if e.get("kind") == "peak" or "peak" in m:
                X["peak_source"] = m.get("peak_source") or e["name"]
    if X["states_total"] is None:
        X["states_total"] = _states_estimate(run_dir)
        X["states_total_basis"] = "어림(도달 시각 ÷ 덱 d3plot DT + 1)" if X["states_total"] else None
    if not files:
        X["d3plot_retained"] = False
        X["note"] = "d3plot 이 이미 없다"
    elif G["delete"] and not dry_run:
        gone = []
        for p in files:
            try:
                os.remove(p)
                gone.append(os.path.basename(p))
            except OSError as e:
                X.setdefault("delete_errors", []).append(f"{os.path.basename(p)}: {e}")
        X["deleted_files"] = gone
        X["d3plot_retained"] = len(gone) < len(files)
        X["deleted_at"] = datetime.now().isoformat()
    elif G["delete"] and dry_run:
        X["dry_run"] = True
    try:
        X["kept_files"] = sorted(n for n in os.listdir(od) if os.path.isfile(os.path.join(od, n)))[:500]
    except OSError:
        X["kept_files"] = []
    write_extraction(run_dir, X)
    return X


def delete_consistency(config_path: str) -> Dict[str, Any]:
    """캠페인 안 runner_config 들(같은 폴더 runner_config*.json·형제 폴더 */runner_config*.json)의 delete_d3plot_after_deep 비교.

    한 runner_config 만 false 로 남아 있던 요청서 사례 — 제출 전 `grep delete_d3plot */runner_config.json` 을 대신한다.
    """
    me = os.path.abspath(config_path)
    d = os.path.dirname(me)
    cands = set(glob.glob(os.path.join(d, "runner_config*.json"))) | set(glob.glob(os.path.join(os.path.dirname(d), "*", "runner_config*.json")))
    vals: Dict[str, List[str]] = {}
    for p in sorted(cands):
        try:
            with open(p, encoding="utf-8") as f:
                cfg = json.load(f)
        except (OSError, ValueError):
            continue
        pp = cfg.get("postprocess") or {}
        v = "없음(postprocess 없음)" if not pp else str(bool(pp.get("delete_d3plot_after_deep", False))).lower()
        vals.setdefault(v, []).append(p)
    return {"values": vals, "consistent": len(vals) <= 1, "mine": next((k for k, ps in vals.items() if me in ps), None)}
