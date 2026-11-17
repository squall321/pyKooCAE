# 런 하나의 LS-DYNA 산출물(d3hsp·mes·glstat·binout)로 정상 종료와 건강(에너지·질량·첫 운동에너지)을 판정해 health.json 을 쓴다
"""KC-02 정상 종료 판정 · 건강 요약 (stcx 요청서 v1.0).

체인 종료 코드·Slurm 상태와 따로, LS-DYNA 가 목표 시각까지 정상 종료했는지와 에너지가 건강한지를 런 폴더만 보고 판정한다.
- invalid: 정상 종료 문구 없음 · 오류 종료 · 도달 시각 < 목표(상대 허용 end_time_rel_tol) · NaN · 낙하·충격에서 첫 KE 0 ·
           첫 KE 가 기대(½mv², v = √(2gh) ⊕ 초기 속도)의 ±ke0_invalid_rel 밖 · d3hsp 없음
- warn:    에너지비 > energy_ratio_max · HG/IE ≥ hg_over_ie_max · 추가 질량 % > added_mass_pct_max · 첫 KE ±ke0_warn_rel 밖 ·
           파트 IE 튐 · 접촉 에너지 음수 큼 · mes 에 *** Error 줄(정상 종료여도)
- 미끄럼 에너지 비율은 문턱이 없다(마찰 일이라 55·80 % 도 정상 — 요청서 DROP_RUN_HEALTH_HG_NOT_SLIDING).
목표 시각은 생성 덱의 *CONTROL_TERMINATION ENDTIM(종료 시간 표가 쓴 값)이 먼저, 없으면 d3hsp termination time.
"""
import glob
import json
import math
import os
import re
import subprocess
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

SCHEMA = "kcr.health/1"

DEFAULT_THRESHOLDS = {
    "energy_ratio_max": 1.05,
    "hg_over_ie_max": 0.10,
    "added_mass_pct_max": 0.5,
    "end_time_rel_tol": 1e-3,
    "ke0_warn_rel": 0.05,
    "ke0_invalid_rel": 0.5,
    "ie_floor_frac": 0.1,             # 참고값 hg_over_ie_tmax 는 IE 가 최대의 이 비율 이상인 출력만 본다
    "part_ie_jump_frac": None,        # 끔(기본) — 런 하나로는 충돌 순간의 정상 흡수와 갈리지 않았다(Test_005 디스플레이 6 %)
    "contact_energy_neg_frac": 0.02,  # 제안값 — 접촉 에너지 최저가 −(기준 에너지 × 이 비율) 아래면 warn
    "campaign_ie_outlier_factor": 3.0,  # 캠페인 비교 — 파트 IE 최대가 같은 파트 중앙값의 이 배수를 넘으면 warn
    "campaign_min_runs": 5,
}
# 단위계 → 시간·에너지 환산(ms, mJ). DeckScan.RHO_BANDS 와 같은 이름
TIME_TO_MS = {"mm-t-s": 1e3, "mm-kg-ms": 1.0, "mm-g-ms": 1.0, "m-kg-s": 1e3}
ENERGY_TO_MJ = {"mm-t-s": 1.0, "mm-kg-ms": 1e3, "mm-g-ms": 1.0, "m-kg-s": 1e3}

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][-+]?\d+)?"
_RE_NORMAL = re.compile(r"N\s+o\s+r\s+m\s+a\s+l\s+t\s+e\s+r\s+m\s+i\s+n\s+a\s+t\s+i\s+o\s+n")
_RE_ERRTERM = re.compile(r"E\s+r\s+r\s+o\s+r\s+t\s+e\s+r\s+m\s+i\s+n\s+a\s+t\s+i\s+o\s+n")
_RE_TERM_TIME = re.compile(r"^\s*termination time\.{3,}\s*(" + _NUM + ")")
_RE_PROB_TIME = re.compile(r"Problem time\s*=\s*(" + _NUM + ")")
_RE_MPP = re.compile(r"Parallel execution with\s+(\d+)\s+MPP proc")
_RE_VERSION = re.compile(r"Version\s*:\s*(.+?)\s*\|?\s*$")
_RE_REVISION = re.compile(r"Revision\s*:\s*(.+?)\s*\|?\s*$")
_RE_PART_MASS = re.compile(r"part id\s+(\d+)\s+mass=\s*(" + _NUM + ")")
_RE_TOTAL_MASS = re.compile(r"t o t a l\s+m a s s\s*=\s*(" + _NUM + ")")
_RE_REASON = re.compile(r"(terminat\w*\s+(?:due|because)|mass increase|negative volume|out[- ]of[- ]range)", re.I)

REPORT_FILES = ("result.json", "analysis_result.json")
FULL_PARSE_MAX_BYTES = 64 * 1024 * 1024   # 이보다 크면 머리·끝 바이트로만 잘림을 본다


def _f(s) -> Optional[float]:
    try:
        v = float(str(s).replace("D", "E").replace("d", "e"))
    except (TypeError, ValueError):
        return None
    return v


def output_dir_of(run_dir: str) -> str:
    o = os.path.join(run_dir, "Output")
    return o if os.path.isdir(o) else run_dir


# ── d3hsp ────────────────────────────────────────────────────────────────────
def parse_d3hsp(path: str) -> Dict[str, Any]:
    out = {"normal": False, "error_termination": False, "termination_time": None, "problem_time": None,
           "version": None, "revision": None, "mpp": None, "part_mass": {}, "total_mass": None, "reasons": []}
    in_mass = False
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if _RE_NORMAL.search(line):
                out["normal"] = True
            if _RE_ERRTERM.search(line):
                out["error_termination"] = True
            if out["termination_time"] is None:
                m = _RE_TERM_TIME.match(line)
                if m:
                    out["termination_time"] = _f(m.group(1))
            m = _RE_PROB_TIME.search(line)
            if m:
                out["problem_time"] = _f(m.group(1))
            if out["version"] is None:
                m = _RE_VERSION.search(line)
                if m and "|" in line:
                    out["version"] = m.group(1).strip(" |")
            if out["revision"] is None:
                m = _RE_REVISION.search(line)
                if m and "|" in line:
                    out["revision"] = m.group(1).strip(" |")
            m = _RE_MPP.search(line)
            if m:
                out["mpp"] = int(m.group(1))
            if "summary of mass" in line:
                in_mass = True
                continue
            if in_mass:
                m = _RE_PART_MASS.search(line)
                if m:
                    out["part_mass"][m.group(1)] = _f(m.group(2))
                    continue
                m = _RE_TOTAL_MASS.search(line)
                if m:
                    out["total_mass"] = _f(m.group(1))
                    in_mass = False
            if _RE_REASON.search(line) and len(out["reasons"]) < 10 and "termination time" not in line:
                out["reasons"].append(line.strip()[:200])
    return out


# ── mes* ─────────────────────────────────────────────────────────────────────
def parse_mes(output_dir: str, max_lines: int = 50) -> Dict[str, Any]:
    files = sorted(glob.glob(os.path.join(output_dir, "mes[0-9]*"))) + \
        [p for p in (os.path.join(output_dir, "messag"),) if os.path.isfile(p)]
    errors, normal, reasons = [], False, []
    for p in files:
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if "*** Error" in line or "*** error" in line:
                        if len(errors) < max_lines:
                            errors.append({"file": os.path.basename(p), "line": line.strip()[:200]})
                    elif _RE_NORMAL.search(line):
                        normal = True
                    elif _RE_REASON.search(line) and len(reasons) < 10:
                        reasons.append(line.strip()[:200])
        except OSError:
            continue
    return {"files": len(files), "error_lines": errors, "normal": normal, "reasons": reasons}


# ── glstat(ASCII) ───────────────────────────────────────────────────────────
_GL_KEYS = {
    "time": "time", "kinetic energy": "ke", "internal energy": "ie", "hourglass energy": "hg",
    "total energy": "te", "total energy / initial energy": "ratio", "energy ratio w/o eroded energy": "ratio_wo",
    "sliding interface energy": "slide", "external work": "ext", "added mass": "added_mass",
    "percentage increase": "pct_increase",
}


_RE_BAD_NUM = re.compile(r"^(?:[+-]?(?:nan|inf|infinity)|\*+)$", re.I)


def parse_glstat(path: str) -> List[Dict[str, Any]]:
    """glstat 블록 → [{time, ke, ie, hg, te, ratio, …, nan}] (값이 NaN·Inf·별표면 nan=True)."""
    recs, cur = [], None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if "." not in line:
                continue
            m = re.match(r"\s*([a-z][a-z /()%\-]*?)\s*\.+\s*(\S+)", line)   # 점 하나뿐인 줄도(energy ratio w/o eroded energy.)
            if not m:
                continue
            name, raw = m.group(1).strip(), m.group(2)
            key = _GL_KEYS.get(name)
            if key is None:
                # 표에 없는 항목(침식 에너지 등)이라도 NaN·Inf·별표면 해가 터진 것이다
                if cur is not None and _RE_BAD_NUM.match(raw):
                    cur["nan"] = True
                continue
            if key == "time":
                if cur is not None:
                    recs.append(cur)
                cur = {"nan": False}
            if cur is None:
                continue
            v = _f(raw)
            if v is None or not math.isfinite(v):
                cur["nan"] = True
                v = float("nan")
            cur[key] = v
    if cur is not None:
        recs.append(cur)
    return recs


def glstat_summary(recs: List[Dict[str, Any]], th: Dict[str, float]) -> Dict[str, Any]:
    if not recs:
        return {}
    fin = lambda x: x is not None and math.isfinite(x)
    ratios = [r["ratio"] for r in recs if fin(r.get("ratio"))]
    ies = [r.get("ie") for r in recs if fin(r.get("ie"))]
    hgs = [r.get("hg") for r in recs if fin(r.get("hg"))]
    ie_max = max(ies) if ies else 0.0
    hg_ie = [r["hg"] / r["ie"] for r in recs
             if fin(r.get("hg")) and fin(r.get("ie")) and r["ie"] > 0 and r["ie"] >= th["ie_floor_frac"] * ie_max]
    last = next((r for r in reversed(recs) if fin(r.get("hg")) and fin(r.get("ie")) and r["ie"] > 0), None)
    pct = [r["pct_increase"] for r in recs if fin(r.get("pct_increase"))]
    slides = [r["slide"] for r in recs if fin(r.get("slide"))]
    nan_t = next((r.get("time") for r in recs if r.get("nan")), None)
    return {
        "records": len(recs), "end_time": recs[-1].get("time"),
        "ke0": recs[0].get("ke"), "te0": recs[0].get("te"),
        "energy_ratio_max": max(ratios) if ratios else None,
        "energy_ratio_end": ratios[-1] if ratios else None,
        # 판정값: HG 최대 / IE 최대 — 충돌 뒤 IE 가 작아진 구간의 나눗셈(Test_005 0.47)에 속지 않게
        "hg_over_ie_max": (max(hgs) / ie_max) if (hgs and ie_max > 0) else None,
        "hg_over_ie_tmax": max(hg_ie) if hg_ie else None,
        "hg_over_ie_end": (last["hg"] / last["ie"]) if last else None,
        "added_mass_pct_total": max(pct) if pct else None,
        "sliding_energy_min": min(slides) if slides else None,
        "nan_onset": nan_t,
    }


# ── step_config.txt ─────────────────────────────────────────────────────────
def parse_step_config(path: str) -> Dict[str, Any]:
    """러너가 KMM 에 준 단계 설정(Run_*/step_config.txt) 의 키=값."""
    out = {}
    if not os.path.isfile(path):
        return out
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("$"):
                continue
            if s.startswith("*Mode"):
                out["_mode_next"] = True
                continue
            if out.pop("_mode_next", False) and "," in s and not s.startswith("*"):
                out["_mode"] = s.split(",")[0].strip().upper()
                continue
            if s.startswith("*"):
                continue
            k, _, v = s.partition(",")
            out[k.strip()] = v.strip()
    return out


# ── binout(Post SIF 의 lasso) ───────────────────────────────────────────────
_BINOUT_SCRIPT = r'''
import json, sys, math
import numpy as np
from lasso.dyna import Binout
out = {"matsum": None, "sleout": None}
b = Binout(sys.argv[1])
cats = b.read()
if "matsum" in cats:
    v = b.read("matsum")
    ids = [int(x) for x in np.asarray(b.read("matsum", "ids")).ravel()]
    t = np.asarray(b.read("matsum", "time"), dtype=float).ravel()
    m = {"ids": ids, "time": t.tolist()}
    for name in ("internal_energy", "kinetic_energy", "added_mass", "mass"):
        if name in v:
            a = np.asarray(b.read("matsum", name), dtype=float)
            if a.ndim == 1:
                a = a.reshape(-1, len(ids))
            m[name] = {"first": a[0].tolist(), "max_jump": np.max(np.diff(a, axis=0), axis=0).tolist() if a.shape[0] > 1 else [0.0] * len(ids),
                       "max": np.max(a, axis=0).tolist(), "last": a[-1].tolist()}
    out["matsum"] = m
if "sleout" in cats:
    v = b.read("sleout")
    ids = [int(x) for x in np.asarray(b.read("sleout", "ids")).ravel()] if "ids" in v else []
    tot = None
    for name in ("total_energy", "total_interface_energy"):
        if name in v:
            tot = np.asarray(b.read("sleout", name), dtype=float)
            break
    if tot is None and "total_slave" in v and "total_master" in v:
        tot = np.asarray(b.read("sleout", "total_slave"), dtype=float) + np.asarray(b.read("sleout", "total_master"), dtype=float)
    if tot is not None:
        if tot.ndim == 1:
            tot = tot.reshape(-1, max(1, len(ids)))
        out["sleout"] = {"ids": ids, "min": np.min(tot, axis=0).tolist()}
json.dump(out, open(sys.argv[2], "w"))
'''


def binout_health(output_dir: str, post_sif: Optional[str], timeout: int = 900) -> Dict[str, Any]:
    """binout 의 matsum·sleout 을 Post SIF 의 lasso 로 읽는다. 못 읽으면 {'error': 까닭}."""
    if not glob.glob(os.path.join(output_dir, "binout*")):
        return {"error": "binout 없음"}
    if not post_sif or not os.path.isfile(post_sif):
        return {"error": f"Post SIF 없음({post_sif}) — binout 항목은 건너뜀"}
    with tempfile.TemporaryDirectory(prefix="kcr_health_") as td:
        script, out = os.path.join(td, "binout_health.py"), os.path.join(td, "out.json")
        with open(script, "w", encoding="utf-8") as f:
            f.write(_BINOUT_SCRIPT)
        binds = ["-B", f"{output_dir}:{output_dir}", "-B", f"{td}:{td}"]
        if os.path.isdir("/data"):
            binds += ["-B", "/data:/data"]     # binout 이 /data 의 다른 곳을 가리키는 링크여도 읽게(deep_report.sh 와 같은 묶음)
        cmd = ["apptainer", "exec", "--no-home", *binds, post_sif, "python3", script, os.path.join(output_dir, "binout*"), out]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
        except (OSError, subprocess.TimeoutExpired) as e:
            return {"error": f"binout 읽기 실패({type(e).__name__})"}
        if p.returncode != 0 or not os.path.isfile(out):
            tail = (p.stderr or "").strip().splitlines()[-1:] or [""]
            return {"error": f"binout 읽기 실패(rc {p.returncode}: {tail[0][:160]})"}
        with open(out, encoding="utf-8") as f:
            return json.load(f)


# ── 리포트 JSON 완결 ────────────────────────────────────────────────────────
def json_complete(path: str) -> Dict[str, Any]:
    """JSON 이 끝까지 있는가 — 작으면 전부 읽고, 크면 머리·끝 바이트로 본다(잘린 270~337 MB JSON 사례)."""
    if not os.path.isfile(path):
        return {"path": path, "exists": False, "complete": False, "method": None}
    size = os.path.getsize(path)
    rec = {"path": path, "exists": True, "size": size, "mtime": os.path.getmtime(path)}
    if size == 0:
        rec.update(complete=False, method="size")
        return rec
    if size <= FULL_PARSE_MAX_BYTES:
        try:
            with open(path, "r", encoding="utf-8") as f:
                json.load(f)
            rec.update(complete=True, method="parse")
        except (ValueError, UnicodeDecodeError) as e:
            rec.update(complete=False, method="parse", error=str(e)[:160])
        return rec
    with open(path, "rb") as f:
        head = f.read(64).lstrip()
        f.seek(max(0, size - 64))
        tail = f.read().rstrip()
    ok = bool(head) and bool(tail) and ((head[:1] == b"{" and tail[-1:] == b"}") or (head[:1] == b"[" and tail[-1:] == b"]"))
    rec.update(complete=ok, method="head_tail")
    return rec


def report_status(output_dir: str) -> Dict[str, Any]:
    """리포트 JSON 상태. complete = 끝까지 쓰인 파일이 하나 이상이고 있는 파일 중 잘린 것이 없다(sphere_report.sh 와 같은
    '둘 중 하나' 약속 — 옛 SIF 는 한 파일만 쓴다). complete_all = 둘 다 완결(d3plot 삭제 관문 — harvest 는 result.json,
    impact 는 analysis_result.json 을 d3plot 없이 다시 읽는다)."""
    rd = os.path.join(output_dir, "report")
    files = {name: json_complete(os.path.join(rd, name)) for name in REPORT_FILES}
    present = [v for v in files.values() if v["exists"]]
    complete = bool(present) and all(v["complete"] for v in present)
    return {"dir": rd, "files": files, "complete": complete, "complete_all": all(v["complete"] for v in files.values())}


# ── 판정 ────────────────────────────────────────────────────────────────────
def _deck_of(run_dir: str) -> Optional[str]:
    for name in ("DropSet.k", "DropWeightImpactTestSet.k", "ThermalSet.k", "VibrationSet.k", "SimulationSet.k"):
        p = os.path.join(run_dir, name)
        if os.path.isfile(p):
            return p
    return None


def _mode_of(run_dir: str, step: Dict[str, Any], deck: Optional[str]) -> Optional[str]:
    m = step.get("_mode")
    if m:
        return {"DROP_ATTITUDE": "DROP", "DROP_WEIGHT_IMPACT_TEST": "IMPACT", "THERMAL_LOAD": "THERM"}.get(m, m)
    if deck:
        return {"DropSet.k": "DROP", "DropWeightImpactTestSet.k": "IMPACT"}.get(os.path.basename(deck))
    return None


def _moving_parts(deck_info, d3: Dict[str, Any], binout: Dict[str, Any]):
    """첫 순간 움직이는 파트와 그 질량 — 초기 속도 카드(파트 지정)가 먼저, 아니면 binout matsum 의 첫 KE > 0 파트."""
    pids = []
    for iv in (deck_info or {}).get("initial_velocities", []):
        if iv.get("kw") == "*INITIAL_VELOCITY_GENERATION" and iv.get("styp") == 2 and iv.get("id"):
            pids.append(int(iv["id"]))
        elif iv.get("kw") == "*INITIAL_VELOCITY_GENERATION" and iv.get("styp") == 1 and iv.get("id"):
            pids.extend(int(p) for p in deck_info.get("part_sets", {}).get(str(iv["id"]), []))
        elif iv.get("kw") == "*INITIAL_VELOCITY_RIGID_BODY" and iv.get("pid"):
            pids.append(int(iv["pid"]))
    basis = "초기 속도 카드(파트)"
    ms = (binout or {}).get("matsum") or {}
    if not pids and ms.get("kinetic_energy"):
        pids = [pid for pid, ke in zip(ms["ids"], ms["kinetic_energy"]["first"]) if ke and ke > 0]
        basis = "binout matsum 첫 KE > 0 파트"
    if not pids:
        return None, None, None
    pm = d3.get("part_mass") or {}
    mass = sum(pm.get(str(p), 0.0) or 0.0 for p in set(pids))
    return sorted(set(pids)), (mass if mass > 0 else None), basis


def evaluate_run(run_dir: str, thresholds: Optional[Dict[str, Any]] = None, solver_exit_code: Optional[int] = None,
                 post_sif: Optional[str] = None, use_binout: bool = True, mode: Optional[str] = None,
                 binout_timeout: int = 900) -> Dict[str, Any]:
    """런 폴더(Run_*) 하나를 판정한다. 결과 dict 는 health.json 그대로."""
    th = dict(DEFAULT_THRESHOLDS)
    th.update({k: v for k, v in (thresholds or {}).items() if k in DEFAULT_THRESHOLDS and v is not None})
    out_dir = output_dir_of(run_dir)
    H: Dict[str, Any] = {"schema": SCHEMA, "run_dir": os.path.abspath(run_dir), "evaluated_at": datetime.now().isoformat(),
                         "solver_exit_code": solver_exit_code, "chain_exit_code": None, "scheduler_state": None,
                         "thresholds": th, "missing": [], "reasons": [], "verdict": None}
    invalid, warn = [], []
    step = parse_step_config(os.path.join(run_dir, "step_config.txt"))
    deck = _deck_of(run_dir)
    deck_info = None
    if deck:
        try:
            from Runner.DeckScan import scan_deck
            deck_info = scan_deck(deck)
        except Exception as e:
            H["missing"].append(f"덱 훑기 실패({type(e).__name__}: {e})")
    else:
        H["missing"].append("생성 덱 없음")
    H["mode"] = mode or _mode_of(run_dir, step, deck)
    units = (deck_info or {}).get("units")
    H["units"] = units
    tm, em = TIME_TO_MS.get(units), ENERGY_TO_MJ.get(units)

    # d3hsp
    d3p = os.path.join(out_dir, "d3hsp")
    d3 = parse_d3hsp(d3p) if os.path.isfile(d3p) else None
    mes = parse_mes(out_dir)
    if d3 is None:
        H["missing"].append("d3hsp 없음")
        invalid.append("d3hsp 없음 — LS-DYNA 가 시작하지 못했거나 산출물이 옮겨지지 않았다")
        d3 = {"part_mass": {}}
    H["normal_termination"] = bool(d3.get("normal") or mes["normal"])
    H["error_termination"] = bool(d3.get("error_termination"))
    H["solver_version"] = " ".join(x for x in (d3.get("version"), d3.get("revision")) if x) or None
    H["mpp"] = d3.get("mpp")
    H["error_lines"] = mes["error_lines"]
    H["termination_reasons"] = (d3.get("reasons") or []) + mes["reasons"]
    if d3.get("normal") is not None and not H["normal_termination"] and os.path.isfile(d3p):
        invalid.append("정상 종료 문구(N o r m a l  t e r m i n a t i o n)가 없다")
    if H["error_termination"]:
        invalid.append("오류 종료(E r r o r  t e r m i n a t i o n)")
    if H["normal_termination"] and mes["error_lines"]:
        warn.append(f"mes 에 *** Error 줄 {len(mes['error_lines'])}개(정상 종료)")

    # glstat
    glp = os.path.join(out_dir, "glstat")
    gl = glstat_summary(parse_glstat(glp), th) if os.path.isfile(glp) else {}
    if not gl:
        H["missing"].append("glstat(ASCII) 없음 — 에너지 항목은 binout 이 있으면 그것으로")

    # 목표·도달 시각
    target = (deck_info or {}).get("endtim") or d3.get("termination_time")
    reached = d3.get("problem_time")
    if reached is None:
        reached = gl.get("end_time")
    H["target_end_time"], H["end_time"] = target, reached
    H["target_end_time_source"] = "덱 ENDTIM" if (deck_info or {}).get("endtim") else ("d3hsp" if target else None)
    H["target_end_time_ms"] = target * tm if (target is not None and tm) else None
    H["end_time_ms"] = reached * tm if (reached is not None and tm) else None
    if target and reached is not None and reached < target * (1.0 - th["end_time_rel_tol"]):
        invalid.append(f"목표 시각에 못 미쳤다(도달 {reached:.6g} < 목표 {target:.6g})")
    elif target and reached is None:
        invalid.append("도달 시각을 모른다(d3hsp Problem time·glstat 없음)")

    # 에너지
    H["energy_ratio_max"] = gl.get("energy_ratio_max")
    H["hg_over_ie_max"] = gl.get("hg_over_ie_max")
    H["hg_over_ie_definition"] = "max(HG)/max(IE) — 참고: hg_over_ie_tmax(IE ≥ 최대의 ie_floor_frac 인 시각의 HG/IE 최대)·hg_over_ie_end"
    H["hg_over_ie_tmax"], H["hg_over_ie_end"] = gl.get("hg_over_ie_tmax"), gl.get("hg_over_ie_end")
    H["added_mass_pct_total"] = gl.get("added_mass_pct_total")
    H["sliding_energy_min"] = gl.get("sliding_energy_min")
    H["nan_onset"] = gl.get("nan_onset")
    H["nan_onset_ms"] = gl["nan_onset"] * tm if (gl.get("nan_onset") is not None and tm) else None
    if gl.get("nan_onset") is not None:
        invalid.append(f"값이 NaN 으로 바뀌었다(시각 {gl['nan_onset']:.6g})")
    if H["energy_ratio_max"] is not None and H["energy_ratio_max"] > th["energy_ratio_max"]:
        warn.append(f"에너지비 최대 {H['energy_ratio_max']:.4g} > {th['energy_ratio_max']}")
    if H["hg_over_ie_max"] is not None and H["hg_over_ie_max"] >= th["hg_over_ie_max"]:
        warn.append(f"HG/IE 최대 {H['hg_over_ie_max']:.3g} ≥ {th['hg_over_ie_max']}")
    if H["added_mass_pct_total"] is not None and H["added_mass_pct_total"] > th["added_mass_pct_max"]:
        warn.append(f"추가 질량 {H['added_mass_pct_total']:.3g} % > {th['added_mass_pct_max']} %(낙하판 포함)")

    # binout(파트 IE 튐·접촉 에너지·기기만 추가 질량)
    bo = {}
    if use_binout:
        bo = binout_health(out_dir, post_sif, timeout=binout_timeout)
        if bo.get("error"):
            H["missing"].append(bo["error"])
            bo = {}

    # 첫 운동에너지 대 ½mv²
    ke0 = gl.get("ke0")
    ms = (bo or {}).get("matsum") or {}
    if ke0 is None and (ms.get("kinetic_energy") or {}).get("first"):
        ke0 = sum(x for x in ms["kinetic_energy"]["first"] if x)
    H["ke0_measured"] = ke0
    g = _f(step.get("Gravity")) or (deck_info or {}).get("gravity")
    h = _f(step.get("Height"))
    iv = [(_f(step.get(k)) or 0.0) for k in ("InitialVelocityX", "InitialVelocityY", "InitialVelocityZ")]
    v_exp = None
    if h is not None and g:
        vf = math.sqrt(2.0 * g * max(h, 0.0))
        if not any(iv):
            v_exp = vf
        elif H["mode"] == "IMPACT":
            v_exp = math.sqrt(iv[0] ** 2 + iv[1] ** 2 + (iv[2] - vf) ** 2)
        elif vf == 0.0:
            v_exp = math.sqrt(sum(x * x for x in iv))
    deck_v = None
    for c in (deck_info or {}).get("initial_velocities", []):
        if c.get("v"):
            deck_v = math.sqrt(sum(x * x for x in c["v"]))
            break
    H["v_deck"], H["v_expected"], H["gravity"] = deck_v, v_exp, g
    pids, m_moving, basis = _moving_parts(deck_info, d3, bo)
    ke_exp, ke_basis = None, None
    if v_exp is not None and m_moving:
        ke_exp, ke_basis = 0.5 * m_moving * v_exp ** 2, f"½·m·v²(m = {basis} {pids} 질량, v = √(2gh))"
    elif v_exp is not None and ke0 and deck_v:
        ke_exp, ke_basis = ke0 * (v_exp / deck_v) ** 2, "½·m·v²(m 은 덱 속도로 역산, v = √(2gh))"
    H["ke0_expected"], H["ke0_expected_basis"], H["moving_parts"] = ke_exp, ke_basis, pids
    moving_case = H["mode"] in ("DROP", "IMPACT") and ((v_exp or 0) > 0 or (deck_v or 0) > 0)
    if moving_case and ke0 is not None:
        scale = max(abs(ke_exp or 0.0), abs(gl.get("te0") or 0.0), 1e-300)
        if ke0 <= 1e-12 * scale or ke0 == 0.0:
            invalid.append("첫 운동에너지가 0 이다(충격추·기기에 초기 속도가 걸리지 않았다)")
        elif ke_exp:
            rel = ke0 / ke_exp - 1.0
            H["ke0_rel_error"] = rel
            if abs(rel) > th["ke0_invalid_rel"]:
                invalid.append(f"첫 운동에너지 {ke0:.6g} 가 기대 {ke_exp:.6g} 와 {rel * 100:+.1f} % 다르다")
            elif abs(rel) > th["ke0_warn_rel"]:
                warn.append(f"첫 운동에너지 {ke0:.6g} 가 기대 {ke_exp:.6g} 와 {rel * 100:+.1f} % 다르다")
    elif moving_case:
        H["missing"].append("첫 운동에너지를 모른다(glstat·binout 없음)")

    ref_e = max(abs(ke_exp or 0.0), abs(ke0 or 0.0), abs(gl.get("te0") or 0.0))
    H["reference_energy"] = ref_e or None
    H["part_ie"], H["part_ie_jump"] = None, []
    if ms.get("internal_energy"):
        ie = ms["internal_energy"]
        H["part_ie"] = {str(pid): {"max": mx, "end": en, "max_jump": jp}
                        for pid, mx, en, jp in zip(ms["ids"], ie["max"], ie["last"], ie["max_jump"])}
        frac = th.get("part_ie_jump_frac")
        if frac and ref_e > 0:
            for pid, jump in zip(ms["ids"], ie["max_jump"]):
                if jump is not None and jump > frac * ref_e:
                    H["part_ie_jump"].append({"part": pid, "max_jump": jump, "frac_of_ref": jump / ref_e})
            if H["part_ie_jump"]:
                warn.append(f"파트 IE 튐 {[x['part'] for x in H['part_ie_jump']]}(출력 한 칸에 기준 에너지의 {frac * 100:g} % 넘게)")
    sl = (bo or {}).get("sleout") or {}
    if sl.get("min"):
        H["contact_energy_min"], H["contact_energy_source"] = min(sl["min"]), "sleout(접촉별 최저)"
    else:
        H["contact_energy_min"] = gl.get("sliding_energy_min")
        H["contact_energy_source"] = "glstat(전체 미끄럼 에너지)" if gl.get("sliding_energy_min") is not None else None
    H["contact_energy_min_mJ"] = H["contact_energy_min"] * em if (H["contact_energy_min"] is not None and em) else None
    if H["contact_energy_min"] is not None and ref_e > 0 and H["contact_energy_min"] < -th["contact_energy_neg_frac"] * ref_e:
        warn.append(f"접촉 에너지 최저 {H['contact_energy_min']:.6g} 가 −{th['contact_energy_neg_frac'] * 100:g} %·기준 에너지 아래")
    # 기기만 추가 질량(낙하판·충격추 뺌) — matsum added_mass 가 있을 때
    H["added_mass_pct_device"] = None
    am = ms.get("added_mass")
    if am and d3.get("part_mass"):
        env = set(pids or []) if H["mode"] == "IMPACT" else set()
        if H["mode"] == "DROP" and ms.get("kinetic_energy"):
            env = {pid for pid, ke in zip(ms["ids"], ms["kinetic_energy"]["first"]) if not ke}
        dev = [(pid, a) for pid, a in zip(ms["ids"], am["max"]) if pid not in env]
        m_dev = sum(d3["part_mass"].get(str(pid), 0.0) or 0.0 for pid, _ in dev)
        if m_dev > 0:
            H["added_mass_pct_device"] = 100.0 * sum(a for _, a in dev if a) / m_dev
            if H["added_mass_pct_device"] > th["added_mass_pct_max"]:
                warn.append(f"기기 추가 질량 {H['added_mass_pct_device']:.3g} % > {th['added_mass_pct_max']} %")

    # 리포트(있으면 — deep 뒤에 다시 채운다)
    rep = report_status(out_dir)
    H["report"] = rep if any(v["exists"] for v in rep["files"].values()) else None
    H["report_json_complete"] = rep["complete"] if H["report"] else None

    H["reasons"] = invalid + warn
    H["verdict"] = "invalid" if invalid else ("warn" if warn else "valid")
    H["invalid_reasons"], H["warn_reasons"] = invalid, warn
    return H


def write_health(run_dir: str, health: Dict[str, Any]) -> str:
    p = os.path.join(run_dir, "health.json")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(health, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)
    return p


def read_health(run_dir: str) -> Optional[Dict[str, Any]]:
    p = os.path.join(run_dir, "health.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def update_health_report(run_dir: str) -> Optional[Dict[str, Any]]:
    """deep_report 뒤 health.json 의 리포트 칸만 다시 채운다(판정은 그대로)."""
    H = read_health(run_dir)
    if H is None:
        return None
    rep = report_status(output_dir_of(run_dir))
    H["report"] = rep
    H["report_json_complete"] = rep["complete"]
    write_health(run_dir, H)
    return H


def load_thresholds(config: Optional[Dict[str, Any]] = None, path: Optional[str] = None) -> Dict[str, Any]:
    """문턱 — runner_config 의 health.thresholds, 그다음 --thresholds 파일(JSON)이 이긴다."""
    th = {}
    if config:
        th.update(((config.get("health") or {}).get("thresholds")) or {})
    if path:
        with open(path, encoding="utf-8") as f:
            th.update(json.load(f))
    unknown = sorted(set(th) - set(DEFAULT_THRESHOLDS))
    if unknown:
        print(f"⚠ health 문턱: 모르는 키 {unknown} — 무시(아는 키: {sorted(DEFAULT_THRESHOLDS)})")
    return th


def campaign_outliers(healths: List[Dict[str, Any]], thresholds: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
    """캠페인 비교 — 같은 파트의 IE 최대를 런끼리 견줘 중앙값의 N배를 넘는 런을 고른다(요청서 사례 — 한 패널 IE 1,346 대 다른 런 371 mJ).

    healths: health.json 목록(run_dir·part_ie·reference_energy). 반환: {run_dir: [까닭, …]}. 정상 종료 런만 기준에 넣는다.
    """
    th = dict(DEFAULT_THRESHOLDS)
    th.update({k: v for k, v in (thresholds or {}).items() if k in DEFAULT_THRESHOLDS and v is not None})
    factor, min_runs = float(th["campaign_ie_outlier_factor"]), int(th["campaign_min_runs"])
    per_part: Dict[str, List[float]] = {}
    for H in healths:
        if H.get("verdict") == "invalid" or not H.get("part_ie"):
            continue
        for pid, rec in H["part_ie"].items():
            if rec.get("max") is not None:
                per_part.setdefault(pid, []).append(float(rec["max"]))
    med = {}
    for pid, vals in per_part.items():
        if len(vals) >= min_runs:
            v = sorted(vals)
            med[pid] = v[len(v) // 2] if len(v) % 2 else 0.5 * (v[len(v) // 2 - 1] + v[len(v) // 2])
    flags: Dict[str, List[str]] = {}
    for H in healths:
        ref = H.get("reference_energy") or 0.0
        for pid, rec in (H.get("part_ie") or {}).items():
            m = med.get(pid)
            x = rec.get("max")
            if not m or x is None or m <= 0:
                continue
            if x > factor * m and x > 0.01 * ref:
                flags.setdefault(H["run_dir"], []).append(
                    f"캠페인 비교: 파트 {pid} IE 최대 {x:.6g} 가 같은 파트 중앙값 {m:.6g} 의 {x / m:.1f}배(> {factor:g}배)")
    return flags
