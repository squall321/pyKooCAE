# LS-DYNA .k 덱을 가볍게 훑어 include·개수·파트·재질 밀도·초기 속도·접촉·출력 간격을 모으는 읽기 전용 스캐너
"""KooChainRun 의 관문·건강 판정이 같이 쓰는 덱 훑개(KMM 리더를 끌어오지 않는다 — 컴파일본 크기·기동 시간).

모으는 것: 파일별 줄 수와 *INCLUDE(적힌 경로·찾은 경로·있는지·상대인지), 절점 수, 요소 수(종류별·파트별),
*PART(제목·SECID·MID), 재질 밀도와 단위계, *INITIAL_VELOCITY 류, *CONTROL_TERMINATION ENDTIM,
*DATABASE_BINARY_D3PLOT DT, *CONTACT_*(종류·면·묶음), *SET_PART_LIST.
모르는 꼴(LONG 형식, 줄 수를 모르는 옵션)은 `uncertain` 에 적고 추측하지 않는다.
"""
import math
import os
import re
from typing import Dict, List, Optional

# 밀도 중앙값 → 단위계 (KooRigidBodyProperties._RHO_BANDS 와 같은 띠). g 는 그 단위계의 중력 가속도
RHO_BANDS = (("mm-t-s", 1e-10, 1e-7), ("mm-kg-ms", 1e-7, 1e-4), ("mm-g-ms", 1e-4, 0.1), ("m-kg-s", 100.0, 1e5))
GRAVITY = {"mm-t-s": 9810.0, "mm-kg-ms": 9.81e-3, "mm-g-ms": 9.81e-3, "m-kg-s": 9.81}

_ELEM_KINDS = {"SOLID": "solid", "SHELL": "shell", "TSHELL": "tshell", "BEAM": "beam",
               "DISCRETE": "discrete", "MASS": "mass", "SEATBELT": "seatbelt", "SPH": "sph"}


def unit_system_from_densities(densities) -> Optional[str]:
    """밀도 목록의 중앙값이 어느 띠에 드는가. 띠 밖이면 None."""
    vals = sorted(d for d in densities if d and d > 0 and math.isfinite(d))
    if not vals:
        return None
    med = vals[len(vals) // 2]
    for name, lo, hi in RHO_BANDS:
        if lo <= med < hi:
            return name
    return None


def _num(s):
    """LS-DYNA 수 칸 — 'E' 없는 Fortran 지수('1.0000-06')·빈 칸(None)까지."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        m = re.fullmatch(r"([+-]?\d*\.?\d+)([+-]\d+)", s)
        if m:
            return float(m.group(1) + "e" + m.group(2))
        return None


def _int(s):
    v = _num(s)
    if v is None or not float(v).is_integer():
        return None
    return int(v)


class DeckInfo(dict):
    """훑은 결과(JSON 으로 그대로 쓸 수 있는 dict). 주요 칸은 아래 scan_deck 참고."""


class _Scanner:
    def __init__(self, collect_parts=None):
        self.info = DeckInfo(
            files=[], includes=[], total_lines=0, keywords={}, nodes=0,
            elements={k: 0 for k in _ELEM_KINDS.values()}, elements_by_part={},
            parts={}, materials={}, part_sets={}, initial_velocities=[], endtim=None,
            d3plot_dt=None, contacts=[], uncertain=[], i10=False, units=None, gravity=None)
        self.collect_parts = set(collect_parts or [])
        self.node_xyz = {}          # collect_parts 가 있을 때만: 그 파트 요소의 절점 좌표
        self.part_nodes = {}        # pid → 절점 id 집합(collect_parts 만)
        self.part_elems = {}        # pid → [(종류, 절점 id 순서), …](collect_parts 만 — 부피·질량)
        self._all_xyz = {}          # collect_parts 가 있을 때 절점 좌표 전부(나중에 걸러 냄)
        self._visited = set()
        self._include_paths = []    # *INCLUDE_PATH 폴더

    # ── 칸 나누기 ────────────────────────────────────────────────────────────
    @staticmethod
    def fields(line, width=10, n=8):
        if "," in line:
            return [x.strip() for x in line.rstrip("\n").split(",")]
        return [line[i * width:(i + 1) * width] for i in range(n)]

    def warn(self, msg):
        if msg not in self.info["uncertain"]:
            self.info["uncertain"].append(msg)

    # ── 파일 ────────────────────────────────────────────────────────────────
    def scan_file(self, path, written=None, parent=None):
        ap = os.path.abspath(path)
        rec = {"written": written or path, "path": ap, "exists": os.path.isfile(ap),
               "relative": written is not None and not os.path.isabs(written), "parent": parent, "lines": 0}
        if written is not None:
            self.info["includes"].append(rec)
        if ap in self._visited or not rec["exists"]:
            return rec
        self._visited.add(ap)
        self.info["files"].append(rec)
        with open(ap, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        rec["lines"] = len(lines)
        self.info["total_lines"] += len(lines)
        self._parse(lines, os.path.dirname(ap), ap)
        return rec

    # ── 키워드 블록 ─────────────────────────────────────────────────────────
    def _parse(self, lines, base_dir, src):
        i, n = 0, len(lines)
        while i < n:
            line = lines[i]
            if not line.startswith("*"):
                i += 1
                continue
            kw_line = line.strip()
            toks = kw_line.split()
            kw = toks[0].upper() if toks else "*"
            if len(toks) > 1 and toks[-1] in ("%", "+"):
                kw += toks[-1]                # '*NODE %' 꼴
            j = i + 1
            data = []
            while j < n and not lines[j].startswith("*"):
                if not lines[j].startswith("$"):
                    data.append(lines[j])     # 빈 줄도 카드다(LS-DYNA 는 기본값으로 읽는다 — 제목이 빈 *PART)
                j += 1
            while data and not data[-1].strip():
                data.pop()                    # 블록 끝 빈 줄만 뗀다
            self.info["keywords"][kw] = self.info["keywords"].get(kw, 0) + 1
            try:
                self._block(kw, kw_line, data, base_dir, src)
            except Exception as e:  # 한 블록의 꼴이 낯설어도 나머지는 훑는다
                self.warn(f"{kw}: 읽지 못함({type(e).__name__}: {e})")
            i = j

    def _block(self, kw, kw_line, data, base_dir, src):
        base_kw = kw.rstrip("%+")
        if kw == "*KEYWORD":
            up = kw_line.upper()
            if re.search(r"\bI10\s*=\s*Y", up):
                self.info["i10"] = True
            if re.search(r"\bLONG\s*=\s*(S|Y)", up):
                self.warn("*KEYWORD LONG 형식 — 칸 폭을 모른다(개수·값이 틀릴 수 있다)")
            return
        wide = self.info["i10"] or kw.endswith("%")
        if kw.endswith("+"):
            self.warn(f"{kw}: 긴 형식(+) — 칸 폭을 모른다")
        if base_kw in ("*INCLUDE", "*INCLUDE_TRANSFORM"):
            rows = [l for l in data if l.strip()]
            if rows:
                written = rows[0].strip()
                tgt = written if os.path.isabs(written) else os.path.join(base_dir, written)
                if not os.path.isfile(tgt) and not os.path.isabs(written):
                    for d in self._include_paths:
                        cand = os.path.join(d, written)
                        if os.path.isfile(cand):
                            tgt = cand
                            break
                self.scan_file(tgt, written=written, parent=src)
            return
        if base_kw.startswith("*INCLUDE_PATH"):
            for l in data:
                d = l.strip()
                if d:
                    self._include_paths.append(d if os.path.isabs(d) else os.path.join(base_dir, d))
            return
        if base_kw == "*NODE":
            self._nodes(data, wide)
            return
        if base_kw.startswith("*ELEMENT_"):
            self._elements(base_kw, data, wide)
            return
        if base_kw.startswith("*PART") and not base_kw.startswith("*PART_"):
            self._parts(base_kw, data)
            return
        if base_kw.startswith("*PART_") and base_kw not in ("*PART_CONTACT", "*PART_INERTIA"):
            # *PART_MOVE 등 다른 키워드
            return
        if base_kw in ("*PART_CONTACT", "*PART_INERTIA"):
            self._parts(base_kw, data)
            return
        if base_kw.startswith("*MAT_") and not base_kw.startswith(("*MAT_ADD_", "*MAT_THERMAL")):
            self._material(base_kw, data)
            return
        if base_kw.startswith("*SET_PART_LIST"):
            self._part_set(base_kw, data)
            return
        if base_kw.startswith("*INITIAL_VELOCITY"):
            self._initial_velocity(base_kw, data)
            return
        if base_kw == "*CONTROL_TERMINATION" and data:
            self.info["endtim"] = _num(self.fields(data[0])[0])
            return
        if base_kw == "*DATABASE_BINARY_D3PLOT" and data:
            self.info["d3plot_dt"] = _num(self.fields(data[0])[0])
            return
        if base_kw.startswith("*CONTACT_"):
            self._contact(base_kw, data)
            return

    # ── 절점 ────────────────────────────────────────────────────────────────
    def _nodes(self, data, wide):
        iw = 10 if wide else 8
        want = bool(self.collect_parts)
        for l in data:
            if not l.strip():
                continue
            self.info["nodes"] += 1
            if not want:
                continue
            if "," in l:
                f = [x.strip() for x in l.split(",")]
                nid, xyz = _int(f[0]), [_num(x) for x in f[1:4]]
            else:
                nid = _int(l[:iw])
                xyz = [_num(l[iw + 16 * k: iw + 16 * (k + 1)]) for k in range(3)]
            if nid is not None and None not in xyz:
                self._all_xyz[nid] = tuple(xyz)

    # ── 요소 ────────────────────────────────────────────────────────────────
    def _elements(self, kw, data, wide):
        tail = kw[len("*ELEMENT_"):]
        toks = tail.split("_")
        kind = _ELEM_KINDS.get(toks[0])
        opts = set(toks[1:])
        if kind is None:
            if data:
                self.warn(f"{kw}: 요소 종류를 모른다 — 세지 않음")
            return
        iw = 10 if wide else 8
        extra = 0
        if kind == "solid":
            extra += 2 if "ORTHO" in opts else 0
            extra += 1 if "DOF" in opts else 0
            known = {"ORTHO", "DOF", "TITLE"}
        elif kind == "shell":
            extra += 1 if opts & {"THICKNESS", "BETA", "MCID"} else 0
            extra += 1 if "OFFSET" in opts else 0
            extra += 1 if "DOF" in opts else 0
            known = {"THICKNESS", "BETA", "MCID", "OFFSET", "DOF"}
        elif kind == "tshell":
            extra += 1 if "BETA" in opts else 0
            known = {"BETA"}
        elif kind == "beam":
            extra += sum(1 for o in ("THICKNESS", "SECTION", "SCALAR", "PID", "OFFSET", "ORIENTATION", "WARPAGE", "ELBOW")
                         if o in opts)
            if "THICKNESS" in opts and "SECTION" in opts:
                extra -= 1
            known = {"THICKNESS", "SECTION", "SCALAR", "PID", "OFFSET", "ORIENTATION", "WARPAGE", "ELBOW"}
        else:
            known = set()
        unknown = opts - known
        if unknown and data:
            self.warn(f"{kw}: 옵션 {sorted(unknown)} 의 줄 수를 모른다 — 요소 수가 틀릴 수 있다")
        want = self.collect_parts
        i, n = 0, len(data)
        while i < n:
            l = data[i]
            if not l.strip():
                i += 1
                continue
            if "," in l:
                f = [x.strip() for x in l.split(",")]
            else:
                f = [l[k * iw:(k + 1) * iw] for k in range(max(2, (len(l.rstrip("\n")) + iw - 1) // iw))]
            nonempty = [x for x in f if x.strip()]
            pid = _int(f[1]) if len(f) > 1 else None
            if kind == "solid" and len(nonempty) <= 2:
                nodes_line = data[i + 1] if i + 1 < n else ""
                step = 2
            else:
                nodes_line = None
                step = 1
            if pid is not None:
                self.info["elements"][kind] += 1
                key = str(pid)
                self.info["elements_by_part"][key] = self.info["elements_by_part"].get(key, 0) + 1
                if want and pid in want:
                    if nodes_line is not None:
                        nf = ([x.strip() for x in nodes_line.split(",")] if "," in nodes_line else
                              [nodes_line[k * iw:(k + 1) * iw] for k in range(10)])
                    else:
                        nf = f[2:]
                    order = [v for v in (_int(x) for x in nf[:10]) if v]
                    self.part_nodes.setdefault(pid, set()).update(order)
                    self.part_elems.setdefault(pid, []).append((kind, tuple(order)))
            i += step + extra

    # ── 파트 ────────────────────────────────────────────────────────────────
    def _parts(self, kw, data):
        opts = set(kw.split("_")[1:]) - {""}
        extra = 0
        if "INERTIA" in opts:
            extra += 3
            self.warn("*PART_INERTIA: IRCS=1 이면 한 줄 더 — 그 경우 파트 뒤 칸이 밀릴 수 있다")
        if "CONTACT" in opts:
            extra += 1
        unknown = opts - {"INERTIA", "CONTACT"}
        if unknown:
            self.warn(f"{kw}: 옵션 {sorted(unknown)} 의 줄 수를 모른다 — 파트 표가 틀릴 수 있다")
        i, n = 0, len(data)
        while i + 1 < n:
            title = data[i].rstrip("\n").strip()
            f = self.fields(data[i + 1], 10, 8)
            pid = _int(f[0])
            if pid is not None:
                self.info["parts"][str(pid)] = {"title": title, "secid": _int(f[1]), "mid": _int(f[2])}
            i += 2 + extra

    # ── 재질 ────────────────────────────────────────────────────────────────
    def _material(self, kw, data):
        rows = data[1:] if kw.endswith("_TITLE") else data
        if not rows:
            return
        f = self.fields(rows[0], 10, 8)
        mid, rho = _int(f[0]), _num(f[1]) if len(f) > 1 else None
        if mid is not None:
            self.info["materials"][str(mid)] = {"kw": kw, "density": rho}

    def _part_set(self, kw, data):
        if not data:
            return
        sid = _int(self.fields(data[0], 10, 8)[0])
        pids = []
        gen = "GENERATE" in kw
        for l in data[1:]:
            if not l.strip():
                continue
            vals = [v for v in (_int(x) for x in self.fields(l, 10, 8)) if v is not None]
            if gen:
                for a, b in zip(vals[0::2], vals[1::2]):
                    pids.extend(range(a, b + 1))
            else:
                pids.extend(v for v in vals if v)
        if sid is not None:
            self.info["part_sets"][str(sid)] = pids

    def _initial_velocity(self, kw, data):
        rec = {"kw": kw}
        if kw == "*INITIAL_VELOCITY" and len(data) >= 2:
            f1, f2 = self.fields(data[0], 10, 5), self.fields(data[1], 10, 6)
            rec.update(nsid=_int(f1[0]), irigid=_int(f1[3]), v=[_num(x) or 0.0 for x in f2[:3]])
        elif kw == "*INITIAL_VELOCITY_GENERATION" and data:
            for l in data[0::2]:
                f = self.fields(l, 10, 8)
                self.info["initial_velocities"].append(
                    {"kw": kw, "id": _int(f[0]), "styp": _int(f[1]), "omega": _num(f[2]) or 0.0,
                     "v": [_num(x) or 0.0 for x in f[3:6]]})
            return
        elif kw == "*INITIAL_VELOCITY_RIGID_BODY" and data:
            f = self.fields(data[0], 10, 7)
            rec.update(pid=_int(f[0]), v=[_num(x) or 0.0 for x in f[1:4]])
        elif kw == "*INITIAL_VELOCITY_NODE":
            rec.update(count=len(data))
        else:
            rec.update(rows=len(data))
        self.info["initial_velocities"].append(rec)

    def _contact(self, kw, data):
        opts = kw[len("*CONTACT_"):]
        rows = list(data)
        rec = {"kw": kw, "cid": None, "title": None}
        if re.search(r"_(ID|TITLE)(_|$)", opts) and rows:
            f = self.fields(rows[0], 10, 8)
            rec["cid"] = _int(f[0])
            rec["title"] = rows[0][10:].strip() if "," not in rows[0] else (f[1] if len(f) > 1 else None)
            rows = rows[1:]
        if "_MPP" in opts and rows:
            first = rows.pop(0)
            if first.rstrip().endswith("&") and rows:
                rows.pop(0)
        if rows:
            f = self.fields(rows[0], 10, 8)
            rec.update(ssid=_int(f[0]), msid=_int(f[1]), sstyp=_int(f[2]) or 0, mstyp=_int(f[3]) or 0)
        self.info["contacts"].append(rec)


def scan_deck(path: str, collect_parts=None) -> DeckInfo:
    """덱(과 include)을 훑는다. collect_parts=[pid,…] 를 주면 그 파트 요소의 절점 좌표를 `part_xyz` 로 준다.

    결과 칸: files·includes(written·path·exists·relative·parent·lines)·total_lines·keywords·nodes·elements(종류별)·
    elements_by_part·parts·materials·part_sets·initial_velocities·endtim·d3plot_dt·contacts·uncertain·i10·units·gravity
    """
    s = _Scanner(collect_parts)
    s.scan_file(path)
    info = s.info
    used_mids = {str(p.get("mid")) for p in info["parts"].values() if p.get("mid") is not None}
    dens = [m["density"] for k, m in info["materials"].items() if (k in used_mids or not used_mids) and m.get("density")]
    info["units"] = unit_system_from_densities(dens)
    info["gravity"] = GRAVITY.get(info["units"]) if info["units"] else None
    if collect_parts:
        info["part_xyz"] = {str(pid): [s._all_xyz[nid] for nid in sorted(ids) if nid in s._all_xyz]
                            for pid, ids in s.part_nodes.items()}
        info["part_volume"], info["part_centroid"] = {}, {}
        for pid, els in s.part_elems.items():
            vt, cx, cy, cz = 0.0, 0.0, 0.0, 0.0
            for k, nodes in els:
                v = element_volume(k, nodes, s._all_xyz)
                pts = [s._all_xyz[nd] for nd in dict.fromkeys(nodes[:8]) if nd in s._all_xyz]
                if v > 0 and pts:
                    vt += v
                    cx += v * sum(q[0] for q in pts) / len(pts)
                    cy += v * sum(q[1] for q in pts) / len(pts)
                    cz += v * sum(q[2] for q in pts) / len(pts)
            info["part_volume"][str(pid)] = vt
            info["part_centroid"][str(pid)] = (cx / vt, cy / vt, cz / vt) if vt > 0 else None
    return info


# 솔리드 부피 — 면 적분(발산 정리). 겹친 절점(쐐기·사면체를 8절점 꼴로 쓴 것)은 넓이 0 면이 되어 그대로 맞다
_HEX_FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
_TET_FACES = ((0, 2, 1), (0, 1, 3), (1, 2, 3), (0, 3, 2))


def element_volume(kind, nodes, xyz) -> float:
    if kind != "solid":
        return 0.0
    try:
        if len(nodes) >= 8 and len(set(nodes[:8])) > 4:
            pts, faces = [xyz[n] for n in nodes[:8]], _HEX_FACES
        else:
            pts, faces = [xyz[n] for n in nodes[:4]], _TET_FACES   # 4절점·10절점 사면체(꼭짓점 4개)
    except KeyError:
        return 0.0
    v = 0.0
    for f in faces:
        a = pts[f[0]]
        for i in range(1, len(f) - 1):
            b, c = pts[f[i]], pts[f[i + 1]]
            v += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                  + a[2] * (b[0] * c[1] - b[1] * c[0]))
    return abs(v) / 6.0


def part_ids_of_contact_side(info: DeckInfo, sid, styp) -> Optional[List[int]]:
    """접촉 면(SSTYP·MSTYP 2 = 파트 묶음, 3 = 파트)의 파트 목록. 다른 종류(세그먼트·절점 묶음, 0 = 전체)는 None."""
    if sid is None and styp not in (5,):
        return None
    if styp == 3:
        return [sid]
    if styp == 2:
        return info["part_sets"].get(str(sid))
    every = [int(p) for p in info["parts"]]
    if styp == 5:                     # 전부(SSID 무시)
        return every
    if styp == 6:                     # 묶음 SSID 를 뺀 전부
        ex = set(info["part_sets"].get(str(sid)) or [])
        return [p for p in every if p not in ex]
    return None
