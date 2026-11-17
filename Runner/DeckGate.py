# 본 캠페인 전에 덱 include·요소·절점 수(원 덱·생성 덱·d3plot)·TIED 파트·카나리아 건강을 점검해 거절할 덱을 거른다
"""KC-10 제출 전 덱 관문(카나리아) (stcx 요청서 v1.0). 덱을 고치지 않는다 — 확인·거절만(고치기는 KMM·DropSet 몫).

거절(rc 1):
  - 원 덱의 *INCLUDE 를 찾지 못함(상대 경로 include 를 덱만 옮긴 경우 — Error 10087 뒤 Exit 139, 직전 로그가 '라이선스 대기'라
    라이선스 문제로 오진하기 쉬움: DECK_RELATIVE_INCLUDE_MOVE_KILLS_RUN)
  - 생성 덱의 *INCLUDE 를 실행 폴더에서 찾지 못함(KMM 은 보존 include 를 파일 이름만 적는다 — 생성 덱 폴더에 있거나
    environment.additional_files·additional_dirs 로 복사돼야 한다)
  - 원 덱에 있던 파트의 요소 수가 생성 덱에서 다름(KMM 이 더한 파트 — 바닥판·충격추·벽 — 은 따로 적는다)
  - 생성 덱 합계와 d3plot 머리(NUMNP·NEL8·NEL4·NEL2·NELT)가 다름(다른 덱의 d3plot — PROJECT_HARDLINK_STALE_DECK)
  - 카나리아 health invalid
사람 점검으로 남김: TIED 결속 파트 목록(나사 자리 미결속 같은 결속 원천), 생성 덱 줄 수 실측.
"""
import glob
import json
import os
import struct
from typing import Any, Dict, List, Optional

from Runner.DeckScan import scan_deck, part_ids_of_contact_side

_WORDS = {"NDIM": 15, "NUMNP": 16, "NEL8": 23, "NEL2": 28, "NEL4": 31, "NELT": 40}


def d3plot_counts(d3plot_path: str) -> Optional[Dict[str, Any]]:
    """d3plot 머리 제어 단어 — 4바이트(단정밀)·8바이트(배정밀) 둘 다. NEL8 < 0 은 10절점 솔리드(|NEL8| 개)."""
    try:
        with open(d3plot_path, "rb") as f:
            head = f.read(64 * 8)
    except OSError:
        return None
    for ws, fmt in ((4, "<i"), (8, "<q")):
        if len(head) < 64 * ws:
            continue
        w = lambda i: struct.unpack_from(fmt, head, i * ws)[0]
        ndim = w(_WORDS["NDIM"])
        if ndim in (3, 4, 5, 7) and 0 < w(_WORDS["NUMNP"]) < 10 ** 10:
            return {"word_bytes": ws, "nodes": w(_WORDS["NUMNP"]), "solid": abs(w(_WORDS["NEL8"])),
                    "beam": w(_WORDS["NEL2"]), "shell": w(_WORDS["NEL4"]), "tshell": w(_WORDS["NELT"]), "ndim": ndim}
    return None


def _include_report(info: Dict[str, Any], label: str) -> List[Dict[str, Any]]:
    return [{"deck": label, "written": i["written"], "path": i["path"], "exists": i["exists"], "relative": i["relative"]}
            for i in info.get("includes", [])]


def _available_by_env(name: str, config: Dict[str, Any]) -> bool:
    """러너 stage-in 이 additional_files·additional_dirs 로 실행 폴더에 넣는가(모델 폴더 기준 glob)."""
    env = config.get("environment", {}) or {}
    model_dir = os.path.dirname(config.get("project", {}).get("model_file", "") or "")
    base = os.path.basename(name)
    for af in env.get("additional_files", []) or []:
        pat = af if os.path.isabs(af) else os.path.join(model_dir, af)
        if any(os.path.basename(m) == base for m in glob.glob(pat)):
            return True
    for ad in env.get("additional_dirs", []) or []:
        d = ad if os.path.isabs(ad) else os.path.join(model_dir, ad)
        if os.path.isfile(os.path.join(os.path.dirname(d), name)) or os.path.isfile(os.path.join(d, base)):
            return True
    return False


def deck_gate(config: Dict[str, Any], canary_run_dirs: Optional[List[str]] = None) -> Dict[str, Any]:
    proj = config.get("project", {}) or {}
    model = proj.get("model_file")
    reject, warn, info_lines = [], [], []
    res: Dict[str, Any] = {"model_file": model, "includes": [], "parts": {}, "canaries": [], "tied": []}
    if not model or not os.path.isfile(model):
        reject.append(f"모델 덱이 없다: {model}")
        res.update(reject=reject, warn=warn, verdict="reject")
        return res
    M = scan_deck(model)
    res["model_counts"] = {"nodes": M["nodes"], **{k: v for k, v in M["elements"].items() if v}, "lines": M["total_lines"]}
    res["includes"] += _include_report(M, "원 덱")
    for inc in M["includes"]:
        if not inc["exists"]:
            reject.append(f"원 덱의 *INCLUDE '{inc['written']}' 를 찾지 못한다({inc['path']}) — 상대 경로 include 는 "
                          f"그것을 적은 파일의 폴더 기준이다(덱만 옮기면 Error 10087)")
    if M["uncertain"]:
        warn += [f"원 덱: {u}" for u in M["uncertain"]]
    # TIED 결속 파트 목록(사람 점검)
    for c in M["contacts"]:
        if "TIED" in c["kw"]:
            res["tied"].append({"kw": c["kw"], "cid": c.get("cid"), "title": c.get("title"),
                                "slave_parts": part_ids_of_contact_side(M, c.get("ssid"), c.get("sstyp")),
                                "master_parts": part_ids_of_contact_side(M, c.get("msid"), c.get("mstyp")),
                                "ssid": c.get("ssid"), "sstyp": c.get("sstyp"), "msid": c.get("msid"), "mstyp": c.get("mstyp")})
    use_local = (config.get("environment", {}) or {}).get("use_local_scratch", True)
    for rd in canary_run_dirs or []:
        cr: Dict[str, Any] = {"run_dir": rd}
        deck = next((os.path.join(rd, n) for n in ("DropSet.k", "DropWeightImpactTestSet.k", "ThermalSet.k",
                                                   "VibrationSet.k", "SimulationSet.k") if os.path.isfile(os.path.join(rd, n))), None)
        if not deck:
            cr["reject"] = ["생성 덱 없음"]
            reject.append(f"카나리아 {os.path.basename(rd)}: 생성 덱 없음")
            res["canaries"].append(cr)
            continue
        G = scan_deck(deck)
        cr["deck"], cr["lines"] = deck, G["total_lines"]
        cr["counts"] = {"nodes": G["nodes"], **{k: v for k, v in G["elements"].items() if v}}
        res["includes"] += _include_report(G, f"생성 덱 {os.path.basename(rd)}")
        for inc in G["includes"]:
            if not inc["exists"] and not _available_by_env(inc["written"], config):
                msg = (f"카나리아 {os.path.basename(rd)}: 생성 덱의 *INCLUDE '{inc['written']}' 를 실행 폴더에서 찾지 못한다 — "
                       f"environment.additional_files 에 넣을 것" + (" (stage-in 이 생성 덱 폴더 기준으로 찾는다)" if use_local else ""))
                reject.append(msg)
            elif inc["exists"] and inc["relative"] and os.sep in inc["written"] and use_local:
                warn.append(f"카나리아 {os.path.basename(rd)}: 생성 덱 *INCLUDE '{inc['written']}' 는 하위 폴더 상대 경로 — "
                            f"stage-in 은 include 를 한 폴더에 납작하게 복사해 LS-DYNA 가 못 찾을 수 있다")
        # 원 덱 파트별 요소 수 대 생성 덱
        lost = []
        for pid, n in M["elements_by_part"].items():
            g = G["elements_by_part"].get(pid, 0)
            if g != n:
                lost.append(f"파트 {pid}: 원 덱 {n} · 생성 덱 {g}")
        added = sorted((p for p in G["elements_by_part"] if p not in M["elements_by_part"]), key=lambda x: int(x))
        cr["added_parts"] = {p: G["elements_by_part"][p] for p in added}
        if lost:
            reject.append(f"카나리아 {os.path.basename(rd)}: 원 덱 파트의 요소 수가 다르다 — " + "; ".join(lost[:10]))
        # d3plot 머리
        d3 = d3plot_counts(os.path.join(rd, "Output", "d3plot"))
        cr["d3plot"] = d3
        if d3:
            diffs = [f"{k} 생성 덱 {G['elements'][k] if k != 'nodes' else G['nodes']} · d3plot {d3[k]}"
                     for k in ("nodes", "solid", "shell", "beam", "tshell")
                     if (G["nodes"] if k == "nodes" else G["elements"][k]) != d3[k]]
            if diffs:
                reject.append(f"카나리아 {os.path.basename(rd)}: 생성 덱과 d3plot 개수가 다르다(다른 덱의 결과?) — " + "; ".join(diffs))
        else:
            info_lines.append(f"카나리아 {os.path.basename(rd)}: d3plot 이 없어 3자 대조 중 d3plot 은 건너뜀")
        # 카나리아 건강
        try:
            with open(os.path.join(rd, "health.json"), encoding="utf-8") as f:
                H = json.load(f)
        except (OSError, ValueError):
            H = None
        cr["health"] = (H or {}).get("verdict")
        if H and H.get("verdict") == "invalid":
            reject.append(f"카나리아 {os.path.basename(rd)}: health invalid — " + "; ".join(H.get("invalid_reasons") or []))
        elif H and H.get("verdict") == "warn":
            warn.append(f"카나리아 {os.path.basename(rd)}: health warn — " + "; ".join(H.get("warn_reasons") or []))
        elif not H:
            info_lines.append(f"카나리아 {os.path.basename(rd)}: health.json 없음(돌지 않았거나 옛 판)")
        res["canaries"].append(cr)
    if not canary_run_dirs:
        info_lines.append("카나리아 런이 없다 — 정적 점검만 했다. 몇 DOE 를 먼저 돌린 뒤 --canary 로 다시")
    res.update(reject=reject, warn=warn, info=info_lines,
               verdict="reject" if reject else ("warn" if warn else "pass"))
    return res
