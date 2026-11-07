# KMM 덱 모델에서 강체 질량특성·외곽면·볼록 껍질을 계산하고 OBJ/JSON 으로 내보내는 모듈
"""강체 낙하 사전 해석(RIGID_DROP_ENDTIME)의 입력 — 덱 하나를 강체 하나로 보고 질량특성과 외곽 형상을 낸다.

덱은 KMM 리더가 읽은 dynaImporter 로 받는다. 새 파서는 만들지 않는다(*PARAMETER·I10·*INCLUDE·고정폭·10절점 수정 이력이 리더에
있다). 리더·공유 매니저는 읽기만 하고 고치지 않는다. 리더가 해석하지 않는 키워드만 리더가 남긴 원문 블록(_raw_keyword_dict,
*PARAMETER 치환·주석 제거 뒤)을 리더의 칸 나누기(_card_fields)로 읽는다.

질량원 (값은 모두 덱 단위)
  - 솔리드: 밀도 × 부피. TETRA4 는 사면체 정확식, TETRA10 은 중간 절점으로 나눈 사면체 8개(곧은 변이면 정확, 휜 변은 근사).
    HEXA8·TSHELL8·PENTA6·HEXA20(꼭짓점 8개)은 8절점 삼선형 사상을 3×3×3 가우스로 적분한다 — 삼선형 육면체의 부피·1차·2차
    모멘트에 정확하고, 절점이 겹친 육면체(R16 쐐기 1 2 3 4 5 5 6 6, TSHELL 쐐기 1 2 3 3 4 5 6 6, 피라미드)도 그대로 맞다.
  - 셸: (밀도 × 두께 + MAREA) × 면적. 두께는 *ELEMENT_SHELL_THICKNESS 절점값(0·빈 칸은 단면 값, R16), 없으면 *SECTION_SHELL
    T1~T4(0·빈 칸은 T1, R16)의 꼭짓점 평균이다. 사각형은 삼각형 둘로 나눈다(평면이면 정확). 관성은 얇은 판에 두께 항
    m·t²/12(법선 방향)을 더한다.
  - 빔: (밀도 × 단면적 + NSM) × 길이를 선 질량으로 본다(단면 회전 관성은 뺀다). 단면적은 ELFORM 1·11(TS·TT, CST 0·1)과
    ELFORM 2·3·12·13(카드 2 의 A)에서 읽는다. 그 밖은 질량을 세지 않고 경고한다.
  - *ELEMENT_MASS: 절점 질량. _NODE_SET 은 R16 대로 셋의 절점에 똑같이 나눈다.
  - 원문만 있는 키워드
      *ELEMENT_MASS_PART(_SET): ADDMASS(또는 FINMASS − 파트 질량)를 면적·부피 비례로 나눈다(_SET 의 MWD=1 은 질량 비례).
        _SET 은 여러 줄을 더하고, 파트 하나 짜리는 마지막 줄만 쓴다(R16).
      *PART_INERTIA: TM·무게중심·관성을 카드 그대로 더한다. 리더가 그 파트의 요소를 버리므로 형상(껍질·외곽면)에는 없다 — 경고.
      *CONSTRAINED_NODAL_RIGID_BODY_INERTIA: TM·무게중심·관성을 더한다(이론 매뉴얼 29.1: 강체 질량은 물리 질량 + 절점 질량).
    관성 카드의 비대각 항은 텐서 성분이다(R16 *PART 비고 4: 관성곱과 부호가 반대).
    그 밖에 리더가 해석하지 않는 질량 요소 키워드(*ELEMENT_INERTIA·*ELEMENT_SEATBELT 등)는 세지 않고 경고한다.
  - 밀도: 재질 GetRho(). 0 이거나 재질이 없으면(리더가 해석하지 않는 *MAT) 원문 *MAT 카드 1 의 RO 다. 그래도 0 인데 요소가
    있는 파트(MID 없음 등)는 질량이 조용히 빠지므로 ValueError 다 — 그 파트를 ExcludePart 로 빼면 넘어간다.
    *PART_COMPOSITE 는 층 두께 가중 평균(KooPartComposite.GetAverageDensity 와 같은 식, 층 밀도는 위 규칙)이다.
  - KMM 이 읽지 않고 *INCLUDE 로 남긴 파일(*PreserveIncludes 패턴, IGA·*PARAMETER_LOCAL 자동 passthrough)은 질량·껍질에 들지
    않는다. 그 안에 요소·질량 키워드가 있으면 ValueError(PASSTHROUGH_INCLUDE_PARTS), 없으면 경고만 한다.
  관성은 연속체(일관 질량) 값이라 격자와 무관하다(요소 하나짜리 상자도 정확). LS-DYNA d3hsp·Radioss 시작 출력은 절점 집중
  질량으로 재므로 그보다 크다 — 한 겹짜리 칩 파트는 수십 %, 기기 전체는 0.1~1%(MinimumModel·SimpleDrop 에서 잼).

제외 (단위 판정보다 먼저 — 바닥판은 밀도 단위가 틀린 일이 있다)
  - exclude_pids(없는 PID 면 ValueError), 그리고 고정 지지물로 보이는 파트를 뺀다. 떨어지는 기기는 땅에 묶일 수 없기 때문이다.
      병진 자유도를 묶는 *BOUNDARY_SPC_NODE/SET(_ID)(_BIRTH_DEATH) 절점이 그 파트 절점의 10% 이상인 파트(DropSet 바닥판
      961/2883 = 33%). 10% 미만이면 기기 파트로 보고 넣고 SPC_ON_DEVICE_PART 경고를 남긴다(SPC 하나로 기기를 빼지 않게).
      병진 구속(CMO=1·CON1≠0, CMO=-1·CON2 병진 자리≠0)이 있는 *MAT_RIGID 파트.
  - 자동으로 뺄 파트가 넣을 파트와 절점을 나누면 받침인지 기기인지 정할 수 없어 ValueError 다(ExcludePart 로 직접 주면 된다).
  - 뺀 파트는 모두 EXCLUDED_PART 경고에 이유·질량·덱 질량 가운데 몫을 남긴다.
  - PID 가 없는 *ELEMENT_MASS 는 그 절점이 뺀 파트에만 있으면 함께 뺀다.

단위: 넣은 파트 밀도의 중앙값이 1e-10~1e-7 이면 mm-t-s, 1e-7~1e-4 mm-kg-ms, 1e-4~0.1 mm-g-ms, 100~1e5 m-kg-s 다(모두 실제
밀도 100~1e5 kg/m³). 어느 띠에도 없으면 units 를 주지 않는 한 ValueError 다.

로그는 log 인자(기본 print)로 낸다. 줄머리 표지는 영어다(컴파일본은 한글 글자를 찾기 어렵다):
  [RigidBody] EXCLUDE · UNITS · WARNING <코드> · SUMMARY
"""
import json
import re

import numpy as np

UNIT_SYSTEMS = {
    "mm-t-s": {"length_to_m": 1e-3, "mass_to_kg": 1e3, "time_to_s": 1.0},
    "mm-kg-ms": {"length_to_m": 1e-3, "mass_to_kg": 1.0, "time_to_s": 1e-3},
    "mm-g-ms": {"length_to_m": 1e-3, "mass_to_kg": 1e-3, "time_to_s": 1e-3},
    "m-kg-s": {"length_to_m": 1.0, "mass_to_kg": 1.0, "time_to_s": 1.0},
}
_RHO_BANDS = (("mm-t-s", 1e-10, 1e-7), ("mm-kg-ms", 1e-7, 1e-4), ("mm-g-ms", 1e-4, 0.1), ("m-kg-s", 100.0, 1e5))
_TAG = "[RigidBody]"
SPC_EXCLUDE_FRACTION = 0.10   # 파트 절점 가운데 이 몫 이상이 병진 SPC 면 고정 지지물로 보고 뺀다

# 카드 1 둘째 칸이 RO 가 아닌 *MAT (스프링·댐퍼·안전띠·열·덧붙임 재질) — 원문 밀도표에서 뺀다
_NO_RO = ("MAT_ADD_", "MAT_THERMAL_", "MAT_T0", "MAT_T1", "MAT_SPRING_", "MAT_DAMPER_", "MAT_S0", "MAT_S1",
          "MAT_SEATBELT", "MAT_B0", "MAT_NONLOCAL")
_RIGID_KW = ("MAT_RIGID", "MAT_RIGID_TITLE", "MAT_020", "MAT_020_TITLE")
# 질량이 없는 요소 키워드 — 리더가 해석하지 않아도 경고하지 않는다
_MASSLESS_ELEM = {"ELEMENT_DISCRETE", "ELEMENT_DISCRETE_LCO", "ELEMENT_PLOTEL", "ELEMENT_SEATBELT_ACCELEROMETER",
                  "ELEMENT_SEATBELT_PRETENSIONER", "ELEMENT_SEATBELT_RETRACTOR", "ELEMENT_SEATBELT_SENSOR",
                  "ELEMENT_SEATBELT_SLIPRING"}

_TET_FACES = np.array([(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)])
_HEX_FACES = np.array([(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)])
# TETRA10(R16: 5=1-2, 6=2-3, 7=3-1, 8=1-4, 9=2-4, 10=3-4) → 꼭짓점 사면체 넷 + 가운데 팔면체(대각 5-10)를 넷으로
_TET10_SUB = np.array([(0, 4, 6, 7), (4, 1, 5, 8), (6, 5, 2, 9), (7, 8, 9, 3),
                       (4, 9, 5, 6), (4, 9, 6, 7), (4, 9, 7, 8), (4, 9, 8, 5)])


def _hex_gauss():
    """8절점 육면체(R16 절점 차례)의 3×3×3 가우스 점 모양함수·미분·가중치."""
    gp, gw = np.array([-np.sqrt(0.6), 0.0, np.sqrt(0.6)]), np.array([5.0, 8.0, 5.0]) / 9.0
    sgn = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)
    q = np.array([(a, b, c) for a in gp for b in gp for c in gp])
    w = np.array([a * b * c for a in gw for b in gw for c in gw])
    t = 1.0 + q[:, None, :] * sgn[None, :, :]
    dn = np.empty((27, 8, 3))
    for k in range(3):
        o = [m for m in range(3) if m != k]
        dn[:, :, k] = sgn[None, :, k] * t[:, :, o[0]] * t[:, :, o[1]] / 8.0
    return t.prod(axis=2) / 8.0, dn, w


_HEX_N, _HEX_DN, _HEX_W = _hex_gauss()


class _Mom:
    """질량(또는 부피·면적) 0·1·2차 모멘트 — m, f=∫x, s=∫xxᵀ (기준점 x0 에서 잰 좌표)."""
    __slots__ = ("m", "f", "s")

    def __init__(self, m=0.0, f=None, s=None):
        self.m = float(m)
        self.f = np.zeros(3) if f is None else np.asarray(f, float)
        self.s = np.zeros((3, 3)) if s is None else np.asarray(s, float)

    def add(self, o, k=1.0):
        self.m += k * o.m
        self.f = self.f + k * o.f
        self.s = self.s + k * o.s
        return self

    def scaled(self, k):
        return _Mom(k * self.m, k * self.f, k * self.s)


def _point_mom(m, x):
    x = np.asarray(x, float)
    return _Mom(m, m * x, m * np.outer(x, x))


def _body_mom(m, c, inertia):
    """질량 m·무게중심 c·무게중심 관성 텐서 → 모멘트. 무게중심 둘레 ∫rrᵀ = tr(I)/2·1 − I."""
    inertia = np.asarray(inertia, float)
    return _point_mom(m, c).add(_Mom(0.0, None, np.trace(inertia) / 2.0 * np.eye(3) - inertia))


def _props(mom, x0):
    """모멘트 → (질량, 무게중심, 무게중심 관성 텐서 I = tr(S)·1 − S)."""
    if mom.m <= 0:
        return 0.0, np.asarray(x0, float), np.zeros((3, 3))
    d = mom.f / mom.m
    sc = mom.s - mom.m * np.outer(d, d)
    return mom.m, np.asarray(x0, float) + d, np.trace(sc) * np.eye(3) - sc


def _tet_mom(p):
    """사면체들 (n,4,3) → (부피 모멘트 합, 부호 배열). ∫xxᵀ = V/20·(Σvvᵀ + 16ggᵀ). 거울 차례도 |V| 로 센다."""
    if len(p) == 0:
        return _Mom(), np.ones(0)
    v = np.einsum("ij,ij->i", p[:, 1] - p[:, 0], np.cross(p[:, 2] - p[:, 0], p[:, 3] - p[:, 0])) / 6.0
    sgn, v = np.where(v < 0, -1.0, 1.0), np.abs(v)
    g = p.mean(axis=1)
    s = np.einsum("n,nki,nkj->ij", v / 20.0, p, p) + np.einsum("n,ni,nj->ij", v * 0.8, g, g)
    return _Mom(v.sum(), (v[:, None] * g).sum(0), s), sgn


def _hex_mom(p, chunk=20000):
    """삼선형 육면체들 (n,8,3) → (부피 모멘트 합, 부호 배열). 거울 차례(부피 음)는 부호를 뒤집어 |V| 로 센다."""
    mom, sgns = _Mom(), []
    for a in range(0, len(p), chunk):
        x8 = p[a:a + chunk]
        xg = np.einsum("gi,nid->ngd", _HEX_N, x8)
        dv = np.linalg.det(np.einsum("gik,nid->ngdk", _HEX_DN, x8)) * _HEX_W
        sg = np.where(dv.sum(1) < 0, -1.0, 1.0)
        dv = dv * sg[:, None]
        mom.add(_Mom(dv.sum(), np.einsum("ng,ngd->d", dv, xg), np.einsum("ng,ngd,nge->de", dv, xg, xg)))
        sgns.append(sg)
    return mom, (np.concatenate(sgns) if sgns else np.ones(0))


def _tri_mom(t3, thick):
    """삼각형들 (n,3,3)·두께 (n,) → (면적 모멘트, 두께 가중 부피 모멘트). 부피 쪽에 두께 항 A·t³/12·nnᵀ 를 더한다."""
    if len(t3) == 0:
        return _Mom(), _Mom()
    c = np.cross(t3[:, 1] - t3[:, 0], t3[:, 2] - t3[:, 0])
    a2 = np.linalg.norm(c, axis=1)
    area = a2 / 2.0
    nrm = c / np.where(a2 > 0, a2, 1.0)[:, None]
    g = t3.mean(axis=1)
    se = (area / 12.0)[:, None, None] * (np.einsum("nki,nkj->nij", t3, t3) + 9.0 * np.einsum("ni,nj->nij", g, g))
    at = area * thick
    geo = _Mom(area.sum(), (area[:, None] * g).sum(0), se.sum(0))
    vol = _Mom(at.sum(), (at[:, None] * g).sum(0),
               np.einsum("n,nij->ij", thick, se) + np.einsum("n,ni,nj->ij", at * thick ** 2 / 12.0, nrm, nrm))
    return geo, vol


def _seg_mom(a, b):
    """선분들 a→b (n,3) → 길이 모멘트. ∫xxᵀ = L·((aaᵀ+bbᵀ)/3 + (abᵀ+baᵀ)/6)."""
    if len(a) == 0:
        return _Mom()
    ln = np.linalg.norm(b - a, axis=1)
    s = np.einsum("n,ni,nj->ij", ln / 3.0, a, a) + np.einsum("n,ni,nj->ij", ln / 3.0, b, b)
    s += np.einsum("n,ni,nj->ij", ln / 6.0, a, b) + np.einsum("n,ni,nj->ij", ln / 6.0, b, a)
    return _Mom(ln.sum(), (ln[:, None] * (a + b) / 2.0).sum(0), s)


def _safe_name(name):
    return re.sub(r"[^\w.-]+", "_", str(name).strip()).strip("_") or "noname"


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, np.generic):
        return o.item()
    return o


class _Deck:
    """리더 결과 위의 읽기 도구 — 원문 블록·칸 나누기(리더의 _card_fields)·숫자 읽기·절점 셋."""

    def __init__(self, imp):
        from KooCAEManager.KooDynaKeyword import _card_fields, _dyna_float, _whole_int
        self.imp = imp
        self._cf, self._fl, self._wi = _card_fields, _dyna_float, _whole_int
        mgr = imp.dynaManager
        self.raw = getattr(mgr, "_raw_keyword_dict", None) or {}
        self.fmts = getattr(mgr, "_block_formats", None) or {}

    def blocks(self, kw, keep_blank=False):
        """키워드의 (블록 줄 목록, 형식). 빈 줄은 뺀다 — keep_blank 면 제목 줄 자리를 지키려 끝의 빈 줄만 뺀다."""
        f = self.fmts.get(kw) or []
        for bi, block in enumerate(self.raw.get(kw) or []):
            if not isinstance(block, list):
                continue
            lines = [str(ln) for ln in block]
            if keep_blank:
                while lines and not lines[-1].strip():
                    lines.pop()
            else:
                lines = [ln for ln in lines if ln.strip()]
            yield lines, (f[bi] if bi < len(f) else None)

    def fields(self, line, fmt, n=8, widths=None):
        """카드 칸 — 기본은 리더 규칙(10칸·long 20칸·콤마), widths 를 주면 고정폭 그 너비(콤마·long 은 리더 규칙)."""
        if widths is None or "," in line or fmt == "long":
            return self._cf(line, fmt, n)
        s, out, pos = line.replace("\n", ""), [], 0
        for w in widths:
            out.append(s[pos:pos + w])
            pos += w
        return out

    def num(self, s, default=0.0):
        try:
            return float(self._fl(s, default))
        except ValueError:
            return default

    def int(self, s, default=0):
        v = self._wi(s)
        return default if v is None else v

    def set_nodes(self, nsid):
        """절점 셋의 절점 번호 집합 — 리더가 읽은 셋이 없으면 None."""
        ns = self.imp.nodeSetManager.nodeSets.get(nsid)
        if ns is None:
            return None
        nodes = getattr(ns, "nodes", None)
        if nodes:
            return set(nodes.keys()) if isinstance(nodes, dict) else {getattr(n, "id", n) for n in nodes}
        ids = set()
        for a, b in getattr(ns, "nodeidPairs", None) or []:
            ids.update(range(int(a), int(b) + 1))
        return ids

    def node_xyz(self, nid):
        n = self.imp.nodeManager.nodes.get(nid)
        return None if n is None else np.array([float(n.x), float(n.y), float(n.z)])


def _raw_materials(dk):
    """원문 *MAT → ({MID: (RO, 키워드)}, {MID: (CMO, CON1, CON2 글)}) — 강체 구속은 *MAT_RIGID 계열만."""
    ro, rigid = {}, {}
    for kw in dk.raw:
        if not kw.startswith("MAT_") or kw.startswith(_NO_RO):
            continue
        off = 1 if kw.endswith("_TITLE") else 0
        for lines, fmt in dk.blocks(kw, keep_blank=bool(off)):
            if len(lines) <= off:
                continue
            c1 = dk.fields(lines[off], fmt, 8)
            mid = dk.int(c1[0], None)
            if mid is None:
                continue
            ro[mid] = (dk.num(c1[1]), kw)
            if kw in _RIGID_KW:
                c2 = dk.fields(lines[off + 1], fmt, 3) if len(lines) > off + 1 else ["", "", ""]
                rigid[mid] = (dk.num(c2[0]), dk.int(c2[1], 0), c2[2].strip())
    return ro, rigid


def _rigid_fixed(cmo, con1, con2):
    """*MAT_RIGID 구속 → (병진 구속, 회전 구속). CMO=1: CON1 병진 0~7, CON2 회전 0~7. CMO=-1: CON2 여섯 자리(x y z rx ry rz)."""
    if cmo == 1.0:
        return con1 != 0, con2 not in ("", "0", "0.0")
    if cmo == -1.0:
        try:
            flags = str(int(float(con2 or 0))).zfill(6)
        except ValueError:
            flags = "000000"
        return any(ch != "0" for ch in flags[:3]), any(ch != "0" for ch in flags[3:6])
    return False, False


def _card_rows(dk, kw, tok):
    """_ID(제목 줄 먼저)·_BIRTH_DEATH(뒤에 한 줄) 변형을 감안한 데이터 카드 줄들."""
    per = 1 + ("ID" in tok) + ("BIRTH" in tok)
    lead = 1 if "ID" in tok else 0
    for lines, fmt in dk.blocks(kw):
        for k in range(lead, len(lines), per):
            yield lines[k], fmt


def _spc_nodes(dk, warn):
    """병진 자유도를 묶는 *BOUNDARY_SPC_NODE/SET(_ID)(_BIRTH_DEATH) 절점 번호 — 원문에서 읽는다(리더는 _SET 블록의 첫 줄만 쓴다)."""
    fixed = set()
    for kw in list(dk.raw):
        tok = kw.split("_")
        if len(tok) < 3 or tok[:2] != ["BOUNDARY", "SPC"] or tok[2] not in ("NODE", "SET"):
            continue
        for ln, fmt in _card_rows(dk, kw, tok[3:]):
            f = dk.fields(ln, fmt, 8)
            ident = dk.int(f[0], 0)
            if ident <= 0 or not any(dk.int(x, 0) != 0 for x in f[2:5]):
                continue
            if tok[2] == "NODE":
                fixed.add(ident)
                continue
            ids = dk.set_nodes(ident)
            if not ids:
                warn("SPC_SET_MISSING", f"*{kw} 의 절점 셋 {ident} 을 리더가 읽지 않았거나 비었다 — 제외 판정에 쓰지 못한다")
            else:
                fixed |= ids
    return fixed


def _prescribed_rigid_pids(dk):
    """*BOUNDARY_PRESCRIBED_MOTION_RIGID(_ID…) 의 TYPEID(=PID)."""
    pids = set()
    for kw in list(dk.raw):
        if kw.startswith("BOUNDARY_PRESCRIBED_MOTION_RIGID"):
            for ln, fmt in _card_rows(dk, kw, kw.split("_")[4:]):
                pids.add(dk.int(dk.fields(ln, fmt, 1)[0], 0))
    return pids


def _inertia_cards(dk, c3, c4, c6, where, warn):
    """관성 카드 3·4(·6) → (TM, 무게중심, 무게중심 관성 텐서). IRCS=1 은 카드 6 의 두 벡터로 돌린다."""
    xc, yc, zc, tm = (dk.num(c3[i]) for i in range(4))
    ircs, nodeid = dk.int(c3[4], 0), dk.int(c3[5], 0)
    c = np.array([xc, yc, zc])
    if nodeid > 0:
        p = dk.node_xyz(nodeid)
        if p is None:
            warn("INERTIA_NODE", f"{where}: 무게중심 절점 {nodeid} 가 없다 — XC·YC·ZC 를 쓴다")
        else:
            c = p
    ixx, ixy, ixz, iyy, iyz, izz = (dk.num(c4[i]) for i in range(6))
    inertia = np.array([[ixx, ixy, ixz], [ixy, iyy, iyz], [ixz, iyz, izz]])
    if ircs == 1:
        ex = np.array([dk.num(c6[i]) for i in range(3)]) if c6 else np.zeros(3)
        ez = np.cross(ex, np.array([dk.num(c6[i]) for i in range(3, 6)]) if c6 else np.zeros(3))
        if (c6 and dk.int(c6[6], 0) > 0) or np.linalg.norm(ez) == 0:
            warn("INERTIA_LOCAL", f"{where}: IRCS=1 국부 좌표계(CID 또는 벡터)를 풀지 못했다 — 관성을 전역으로 본다")
        else:
            ex, ez = ex / np.linalg.norm(ex), ez / np.linalg.norm(ez)
            r = np.column_stack([ex, np.cross(ez, ex), ez])
            inertia = r @ inertia @ r.T
    return tm, c, inertia


def _part_inertia(dk, warn):
    """원문 *PART_INERTIA(옵션 차례 무관, 한 블록에 여러 파트) → [(PID, 이름, MID, TM, 무게중심, 관성)]."""
    out = []
    for kw in list(dk.raw):
        tok = kw.split("_")
        if tok[0] != "PART" or "INERTIA" not in tok[1:]:
            continue
        extra = sum(o in tok for o in ("REPOSITION", "CONTACT", "PRINT", "ATTACHMENT", "FIELD"))
        for lines, fmt in dk.blocks(kw, keep_blank=True):
            k = 0
            while k + 5 <= len(lines):
                c2, c3 = dk.fields(lines[k + 1], fmt, 8), dk.fields(lines[k + 2], fmt, 6)
                ircs = dk.int(c3[4], 0)
                c6 = dk.fields(lines[k + 5], fmt, 7) if ircs == 1 and k + 5 < len(lines) else None
                pid = dk.int(c2[0], 0)
                if pid > 0:
                    tm, c, inertia = _inertia_cards(dk, c3, dk.fields(lines[k + 3], fmt, 6), c6, f"*{kw} PID {pid}", warn)
                    out.append((pid, lines[k].strip(), dk.int(c2[2], 0), tm, c, inertia))
                k += 5 + (ircs == 1) + extra
    return out


def _cnrb_inertia(dk, warn):
    """원문 *CONSTRAINED_NODAL_RIGID_BODY_…INERTIA… → [(PID, TM, 무게중심, 관성)]."""
    head, out = "CONSTRAINED_NODAL_RIGID_BODY", []
    for kw in list(dk.raw):
        tok = kw[len(head):].split("_") if kw.startswith(head) else []
        if "INERTIA" not in tok:
            continue
        title, spc = "TITLE" in tok, "SPC" in tok
        for lines, fmt in dk.blocks(kw, keep_blank=title):
            k = 0
            while k + title + spc + 4 <= len(lines):
                j = k + title + 1 + spc                       # 관성 카드 1 (XC YC ZC TM IRCS NODEID)
                c3 = dk.fields(lines[j], fmt, 6)
                ircs = dk.int(c3[4], 0)
                c6 = dk.fields(lines[j + 3], fmt, 7) if ircs == 1 and j + 3 < len(lines) else None
                pid = dk.int(dk.fields(lines[k + title], fmt, 1)[0], 0)
                tm, c, inertia = _inertia_cards(dk, c3, dk.fields(lines[j + 1], fmt, 6), c6, f"*{kw} PID {pid}", warn)
                out.append((pid, tm, c, inertia))
                size = title + 1 + spc + 3 + (ircs == 1) + ("THERMAL" in tok)
                if "OVERRIDE" in tok and len(lines) % size and not len(lines) % (size + 1):
                    size += 1   # OVERRIDE 카드 7 은 "optional" 이다 — 줄 수가 맞을 때만 있다고 본다
                k += size
    return out


def _passthrough_includes(imp):
    """KMM 이 읽지 않고 *INCLUDE 로 남긴 파일(*PreserveIncludes 패턴, IGA·*PARAMETER_LOCAL 자동) → [(파일, {질량 키워드: 수})].
    질량 키워드 = 질량이 있는 *ELEMENT_*·*IGA_*·*PART_…INERTIA…·*CONSTRAINED_NODAL_RIGID_BODY_…INERTIA…"""
    out = []
    for entry in getattr(imp.dynaManager, "_include_passthrough_data", None) or []:
        kws = {}
        for line in str(entry.get("content", "")).splitlines():
            m = re.match(r"\*([A-Za-z0-9_]+)", line)
            if not m:
                continue
            k, tok = m.group(1).upper(), m.group(1).upper().split("_")
            if ((k.startswith("ELEMENT_") and k not in _MASSLESS_ELEM) or k.startswith("IGA_")
                    or (tok[0] == "PART" and "INERTIA" in tok) or (k.startswith("CONSTRAINED_NODAL_RIGID_BODY") and "INERTIA" in tok)):
                kws[k] = kws.get(k, 0) + 1
        out.append((str(entry.get("file", "?")), kws))
    return out


def _mass_part_cards(dk):
    """원문 *ELEMENT_MASS_PART(_SET)(ID ADDMASS FINMASS LCID MWD, 8·16·16·8·8칸) → ({PID: (ADD, FIN)} 마지막 줄, [(PSID, ADD, FIN, MWD)])."""
    single, sets = {}, []
    for kw in ("ELEMENT_MASS_PART", "ELEMENT_MASS_PART_SET"):
        for lines, fmt in dk.blocks(kw):
            widths = [10, 16, 16, 10, 10] if fmt == "i10" else [8, 16, 16, 8, 8]
            for ln in lines:
                f = dk.fields(ln, fmt, 5, widths)
                ident, add, fin = dk.int(f[0], 0), dk.num(f[1]), dk.num(f[2])
                if kw == "ELEMENT_MASS_PART":
                    single[ident] = (add, fin)
                else:
                    sets.append((ident, add, fin, dk.int(f[4], 0)))
    return single, sets


class _PartData:
    """파트 하나의 요소 연결(전역 절점 행 번호)과 두께."""

    def __init__(self):
        self.tet4, self.tet10, self.hex, self.beam = [], [], [], []
        self.shell, self.shell_t = [], []   # 꼭짓점 3·4 개, 요소 두께
        self.points = []                    # (절점 행 목록, 질량) — 셋 질량은 행마다 똑같이 나눈다
        self.n_elem = 0
        self.nodes = set()                  # 요소 절점 번호(질량 요소·빔 방향 절점 제외)


def _section(imp, part):
    return getattr(part, "section", None) or (getattr(imp.sectionManager, "sections", {}) or {}).get(getattr(part, "secid", 0))


def _shell_section_t(part, sec):
    """셸 단면의 절점 두께 T1~T4(0·빈 칸은 T1) — *PART_COMPOSITE 는 층 두께 합."""
    if getattr(part, "partType", "") == "PartComposite":
        return [float(sum(float(x) for x in getattr(part, "thicki", []) or []))] * 4
    t = [float(getattr(sec, a, 0.0) or 0.0) for a in ("T1", "T2", "T3", "T4")] if sec is not None else [0.0] * 4
    return [x if x > 0 else t[0] for x in t]


def _collect(imp, dk, warn):
    """파트마다 요소를 모은다 → (전역 절점 좌표, 절점 번호→행, {PID: _PartData}, 파트 밖 질량 요소)."""
    xyz, row = [], {}

    def ix(n):
        r = row.get(n.id)
        if r is None:
            r = row[n.id] = len(xyz)
            xyz.append((float(n.x), float(n.y), float(n.z)))
        return r

    def add_point(d, e):
        mass = float(getattr(e, "mass", 0.0) or 0.0)
        if e.type == "POINT":
            ns = [n for n in (e.nodes or []) if n is not None]
            if ns:
                d.points.append(([ix(ns[0])], mass))
            return
        nodes = [imp.nodeManager.nodes.get(i) for i in sorted(dk.set_nodes(getattr(e, "nsid", 0)) or ())]
        nodes = [n for n in nodes if n is not None]
        if nodes:
            d.points.append(([ix(n) for n in nodes], mass))
        else:
            warn("MASS_NODE_SET", f"*ELEMENT_MASS_NODE_SET EID {e.id}: 절점 셋 {getattr(e, 'nsid', '?')} 이 비었거나 없다 — "
                                  f"질량 {mass:g} 을 세지 않는다")

    parts, unknown = {}, {}
    for pid, part in imp.partManager.parts.items():
        d = parts[pid] = _PartData()
        st = None
        for e in part.elementManager.elements.values():
            t, ns = e.type, e.nodes
            if t in ("POINT", "POINT_NSET"):
                add_point(d, e)
                d.n_elem += 1
                continue
            if t in ("LINE2", "LINE3"):            # 셋째 절점은 방향 절점이다(R16 *ELEMENT_BEAM N3)
                ns = ns[:2]
                d.beam.append([ix(n) for n in ns])
            elif t == "TETRA4":
                d.tet4.append([ix(n) for n in ns[:4]])
            elif t == "TETRA10":
                d.tet10.append([ix(n) for n in ns[:10]])
            elif t in ("HEXA8", "TSHELL8", "HEXA20"):
                d.hex.append([ix(n) for n in ns[:8]])
            elif t == "PENTA6":                    # KMM 쐐기(삼각형 1-2-3·4-5-6) → 1 2 3 3 4 5 6 6, 끝 둘이 같으면 피라미드
                r = [ix(n) for n in ns[:6]]
                d.hex.append(r[:5] + [r[4]] * 3 if ns[4].id == ns[5].id else [r[0], r[1], r[2], r[2], r[3], r[4], r[5], r[5]])
            elif t in ("TRI3", "QUAD4", "TRI6", "QUAD8"):
                k = 3 if t.startswith("TRI") else 4
                ns = ns[:k]
                if st is None:
                    st = _shell_section_t(part, _section(imp, part))
                th = list(getattr(e, "theta", None) or [])
                tn = [dk.num(str(th[i])) if i < len(th) else 0.0 for i in range(k)]
                d.shell.append([ix(n) for n in ns])
                d.shell_t.append(float(np.mean([tn[i] if tn[i] > 0 else st[i] for i in range(k)])))
            else:
                unknown[t] = unknown.get(t, 0) + 1
                continue
            d.n_elem += 1
            d.nodes.update(n.id for n in ns)
    if unknown:
        warn("ELEMENT_TYPE", f"질량을 셀 줄 모르는 요소 형식 {unknown} — 세지 않는다")
    root, pm = _PartData(), imp.partManager
    holders = [pm.elementManager] + [getattr(p, "elementManager", None) for p in
                                     list(getattr(pm, "partsRigid", {}).values()) + list(getattr(pm, "constrainedParts", {}).values())]
    for em in holders:
        for e in (getattr(em, "elements", None) or {}).values():
            if getattr(e, "type", "") in ("POINT", "POINT_NSET"):
                add_point(root, e)
    return np.array(xyz, float).reshape(-1, 3), row, parts, root


def _rho_of(part, imp, raw_ro, warn, noted):
    """파트 밀도와 출처 — 재질 GetRho(), 0 이면 원문 카드 RO. *PART_COMPOSITE 는 층 두께 가중 평균."""
    mats = imp.matManager.materials

    def one(mid):
        m = mats.get(mid)
        try:
            r = float(m.GetRho()) if m is not None else 0.0
        except (TypeError, ValueError):
            r = 0.0
        if r > 0:
            return r, type(m).__name__
        r, kw = raw_ro.get(mid, (0.0, None))
        if r > 0:
            if mid not in noted:
                noted.add(mid)
                warn("DENSITY_RAW", f"MID {mid}: 리더 재질 밀도가 0 이거나 재질을 읽지 않아(*{kw}) 원문 카드 1 의 RO={r:g} 를 쓴다")
            return r, f"raw *{kw}"
        return 0.0, "none"

    if getattr(part, "partType", "") == "PartComposite":
        th = [float(x) for x in getattr(part, "thicki", []) or []]
        rs = [one(int(m))[0] for m in getattr(part, "midi", []) or []]
        tot = sum(th[:len(rs)])
        return (sum(r * t for r, t in zip(rs, th)) / tot if tot > 0 else 0.0), "PART_COMPOSITE"
    return one(getattr(part, "mid", 0))


def _beam_area(sec, dk):
    """빔 단면적 — ELFORM 1·11 은 TS·TT(CST 0 사각·1 관, 두 끝 선형 변화 평균), 2·3·12·13 은 카드 2 의 A. 모르면 None."""
    if sec is None:
        return None
    el, opt, cards = getattr(sec, "elform", 1), list(getattr(sec, "options", None) or []), getattr(sec, "raw_cards", None) or []
    if el in (1, 11) and len(opt) >= 4 and not cards:
        s1, s2, t1, t2 = (float(x) for x in opt[:4])
        cst = getattr(sec, "cst", 0)
        if cst == 0:
            return (2 * s1 * t1 + s1 * t2 + s2 * t1 + 2 * s2 * t2) / 6.0
        if cst == 1:
            return np.pi / 4.0 * ((s1 * s1 + s1 * s2 + s2 * s2) - (t1 * t1 + t1 * t2 + t2 * t2)) / 3.0
        return None
    if el in (2, 3, 12, 13) and len(cards) >= 2:
        a = dk.num(dk.fields(str(cards[1]), None, 1)[0])
        return a if a > 0 else None
    return None


def _hull(points, warn):
    """볼록 껍질 — 꼭짓점만 다시 번호 매기고 삼각형은 바깥으로 향하게 한다. 평평하면 QJ(흔들기)로 다시 한다."""
    from scipy.spatial import ConvexHull
    empty = {"vertices": np.zeros((0, 3)), "faces": np.zeros((0, 3), int), "volume": 0.0, "area": 0.0, "n_vertices": 0}
    pts = np.unique(np.asarray(points, float).reshape(-1, 3), axis=0)
    if len(pts) < 4:
        warn("HULL_DEGENERATE", f"볼록 껍질을 만들 절점이 {len(pts)}개뿐이다")
        return empty
    try:
        h = ConvexHull(pts)
    except Exception:   # 한 평면·한 줄 (scipy.spatial.QhullError)
        try:
            h = ConvexHull(pts, qhull_options="QJ")
        except Exception as e:
            warn("HULL_DEGENERATE", f"볼록 껍질을 만들지 못했다: {e}")
            return empty
        warn("HULL_DEGENERATE", "절점이 한 평면에 있어 흔든(QJ) 껍질을 쓴다 — 부피가 거의 0 이다")
    tri = h.simplices.copy()
    p = pts[tri]
    flip = np.einsum("ij,ij->i", np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), h.equations[:, :3]) < 0
    tri[flip] = tri[flip][:, [0, 2, 1]]
    used, inv = np.unique(tri, return_inverse=True)
    return {"vertices": pts[used], "faces": inv.reshape(-1, 3), "volume": float(h.volume), "area": float(h.area),
            "n_vertices": int(len(used))}


def _part_surface(d, sg_tet, sg_t10, sg_hex):
    """파트 외곽면 → 삼각형 (k,3) 전역 절점 행. 솔리드 면은 파트 안에서 한 번만 나오는 면, 셸은 요소 그대로다.
    면은 요소 바깥을 향한다(거울 차례 요소는 뒤집는다). 겹친 꼭짓점이 하나인 사각 면은 삼각형, 둘 이상이면 버린다."""
    quads = []
    for idx, sg in ((d.tet4, sg_tet), ([r[:4] for r in d.tet10], sg_t10)):
        if idx:
            f = np.asarray(idx)[:, _TET_FACES]
            f[sg < 0] = f[sg < 0][:, :, [0, 2, 1]]
            f = f.reshape(-1, 3)
            quads.append(np.column_stack([f, np.full(len(f), -1)]))
    if d.hex:
        q = np.asarray(d.hex)[:, _HEX_FACES]
        q[sg_hex < 0] = q[sg_hex < 0][:, :, ::-1]
        q = q.reshape(-1, 4)
        a, b, c, e = q.T
        eq = np.stack([a == b, b == c, c == e, e == a], axis=1)
        ne = eq.sum(1)
        t3 = np.where(eq[:, [0]], q[:, [0, 2, 3]], np.where(eq[:, [1]], q[:, [0, 1, 3]], q[:, [0, 1, 2]]))
        quads.append(q[(ne == 0) & (a != c) & (b != e)])
        quads.append(np.column_stack([t3[ne == 1], np.full(int((ne == 1).sum()), -1)]))
    tris = []
    if quads:
        f4 = np.concatenate(quads)
        _, inv, cnt = np.unique(np.sort(f4, axis=1), axis=0, return_inverse=True, return_counts=True)
        f4 = f4[cnt[inv.ravel()] == 1]
        is3 = f4[:, 3] < 0
        tris += [f4[is3][:, :3], f4[~is3][:, [0, 1, 2]], f4[~is3][:, [0, 2, 3]]]
    st = [t for el in d.shell for t in ([el[:3]] if len(el) == 3 else [el[:3], [el[0], el[2], el[3]]])
          if len(set(t)) == 3]             # N4=N3 로 적은 삼각형 셸의 넓이 0 조각은 뺀다
    if st:
        tris.append(np.asarray(st))
    return np.concatenate(tris).astype(int) if tris else np.zeros((0, 3), int)


def compute_rigid_body(dyna_importer, exclude_pids=(), units=None, log=print):
    """KMM 이 읽은 덱 → 강체 질량특성·외곽면·볼록 껍질 dict(값은 덱 단위, si 만 SI). 규칙은 모듈 설명에 있다.

    exclude_pids 는 뺄 PID, units 는 UNIT_SYSTEMS 이름(없으면 밀도 중앙값으로 판정, 못 하면 ValueError), log 는 줄을 받는 함수다.
    돌려주는 dict 의 약속:
      inertia_com  무게중심 둘레 관성 텐서 ∫(r²·1 − rrᵀ)dm — 비대각은 관성곱의 음수(LS-DYNA *PART_INERTIA·d3hsp 와 같다)
      principal_moments 오름차순, principal_axes 는 그 열벡터(오른손 좌표계)
      obb          주축 틀 상자 — center, axes(=principal_axes), extents(축마다 전체 길이, 껍질 꼭짓점 기준)
      hull         넣은 파트 요소 절점의 볼록 껍질(질량 요소 절점·빔 방향 절점 제외), faces 는 바깥을 향한 삼각형
      surface      파트마다의 외곽면 삼각형(사각형은 둘로), groups=[('PART_<pid>_<이름>', 면 번호 배열)] → write_obj
      parts        넣은 파트 — 파트마다 inertia_com 도 준다(계약에 더한 칸). 질량 0 인 파트의 com 은 None
      excluded_parts  뺀 파트와 이유(reason), 질량(mass)·덱 질량 가운데 몫(mass_fraction) — 계약에 더한 칸
    틀린 입력은 ValueError(영어 표지): unknown units · unknown ExcludePart · ambiguous auto-exclusion · density missing ·
    PASSTHROUGH_INCLUDE_PARTS · total mass is 0 · cannot detect units.
    """
    imp = dyna_importer
    warnings = []

    def warn(code, msg):
        warnings.append(f"{code}: {msg}")
        log(f"{_TAG} WARNING {code}: {msg}")

    def quiet(code, msg):
        pass

    if units is not None and units not in UNIT_SYSTEMS:
        raise ValueError(f"{_TAG} unknown units '{units}' — {', '.join(UNIT_SYSTEMS)} 가운데 하나")
    dk = _Deck(imp)
    hidden = _passthrough_includes(imp)
    carry = [(f, kws) for f, kws in hidden if kws]
    if carry:   # 그 요소의 질량·형상이 빠진 채로 표를 만들면 각도별 종료 시간이 조용히 틀린다
        raise ValueError(f"{_TAG} PASSTHROUGH_INCLUDE_PARTS: KMM 이 읽지 않고 *INCLUDE 로 남긴 파일에 요소가 있다 — "
                         + "; ".join(f"{f} {kws}" for f, kws in carry)
                         + " — 질량·볼록 껍질에서 빠진다. 이 모드에서는 그 *PreserveIncludes 패턴을 빼거나 include 를 덱에 풀어 넣을 것"
                           " (passthrough include carries elements)")
    for f, _ in hidden:
        warn("PASSTHROUGH_INCLUDE_PARTS", f"{f} 는 KMM 이 읽지 않고 *INCLUDE 로 남겼다 — 요소·질량 키워드가 없어 질량에는 영향이 없다")
    xyz, row, pdata, root = _collect(imp, dk, warn)
    if len(xyz) == 0:
        raise ValueError(f"{_TAG} no element nodes — 요소가 있는 파트가 없다")
    x0 = (xyz.min(0) + xyz.max(0)) / 2.0   # 모멘트 기준점(좌표가 커도 자릿수를 잃지 않게)
    xs = xyz - x0
    parts_obj = imp.partManager.parts
    raw_ro, raw_rigid = _raw_materials(dk)
    pin = _part_inertia(dk, warn)
    name_of = {pid: nm for pid, nm, *_ in pin}
    name_of.update({pid: str(getattr(p, "name", "")).strip() for pid, p in parts_obj.items()})

    cnrb = _cnrb_inertia(dk, warn)
    for pid, *_ in cnrb:
        name_of.setdefault(pid, "CNRB_INERTIA")

    # ── 제외 ────────────────────────────────────────────────────────────────
    explicit = {int(p) for p in exclude_pids or ()}
    unknown = sorted(explicit - set(name_of))
    if unknown:
        raise ValueError(f"{_TAG} unknown ExcludePart PID {unknown} — 읽은 파트·*PART_INERTIA·CNRB 가운데 없다 (unknown ExcludePart)")
    reasons = {pid: ["user ExcludePart"] for pid in sorted(explicit)}
    auto = {}
    spc = _spc_nodes(dk, warn)
    for pid, d in pdata.items():
        hit = len(d.nodes & spc)
        if not hit:
            continue
        if hit >= SPC_EXCLUDE_FRACTION * len(d.nodes):
            auto.setdefault(pid, []).append(f"BOUNDARY_SPC {hit}/{len(d.nodes)} nodes")
        elif pid not in explicit:
            warn("SPC_ON_DEVICE_PART", f"pid={pid} ({name_of.get(pid, '')}) {hit}/{len(d.nodes)} nodes 가 병진 SPC 로 묶였다 — "
                                       f"{SPC_EXCLUDE_FRACTION:.0%} 미만이라 기기 파트로 보고 넣는다. 받침·고정구면 ExcludePart 로 뺄 것")
    mids = {pid: mid for pid, _, mid, *_ in pin}
    mids.update({pid: getattr(p, "mid", 0) for pid, p in parts_obj.items()})
    for pid, mid in sorted(mids.items()):
        if mid in raw_rigid:
            cmo, con1, con2 = raw_rigid[mid]
            trans, rot = _rigid_fixed(cmo, con1, con2)
            if trans:
                auto.setdefault(pid, []).append(f"MAT_RIGID CMO={cmo:g} CON1={con1} CON2={con2 or 0}")
            elif rot and pid not in auto and pid not in explicit:
                warn("ROTATION_CONSTRAINT", f"PID {pid}: *MAT_RIGID 회전 구속(CMO={cmo:g} CON2={con2})은 무시하고 넣는다")
    for pid, why in auto.items():
        reasons.setdefault(pid, []).extend(why)
    out_pids = set(reasons)
    keep_nodes = set().union(*[d.nodes for p, d in pdata.items() if p not in out_pids])
    clash = {p: len(pdata[p].nodes & keep_nodes) for p in sorted(auto) if p not in explicit and p in pdata}
    clash = {p: n for p, n in clash.items() if n}
    if clash:   # 바닥판이 기기와 절점을 나누면(병합 절점) 받침인지 기기인지 이 규칙으로 정할 수 없다
        raise ValueError(f"{_TAG} auto-excluded part shares nodes with included parts — "
                         + ", ".join(f"PID {p} ({name_of.get(p, '')}, {'; '.join(auto[p])}) {n} nodes" for p, n in clash.items())
                         + " — 받침인지 기기 파트인지 정할 수 없다. 뺄 파트를 ExcludePart 로 직접 줄 것 (ambiguous auto-exclusion)")
    excluded = []
    for pid in sorted(reasons):
        why = "; ".join(reasons[pid])
        excluded.append({"pid": pid, "name": name_of[pid], "reason": why})
        log(f"{_TAG} EXCLUDE pid={pid} ({name_of[pid]}) reason={why} — 강체에서 뺀다")
    for pid in sorted(_prescribed_rigid_pids(dk) & (set(parts_obj) - out_pids)):
        warn("PRESCRIBED_MOTION", f"PID {pid}: *BOUNDARY_PRESCRIBED_MOTION_RIGID 가 걸린 파트를 넣었다 — 받침·충격체면 ExcludePart 로 뺄 것")

    # ── 파트별 모멘트 (뺀 파트도 잰다 — 셋 질량 분배·제외 목록 질량에 쓴다) ──────────
    noted, recs, sg, no_rho = set(), {}, {}, []
    for pid, d in pdata.items():
        part, w_ = parts_obj[pid], (quiet if pid in out_pids else warn)
        rho, rsrc = _rho_of(part, imp, raw_ro, w_, noted)
        tet, sgt = _tet_mom(xs[np.asarray(d.tet4, int).reshape(-1, 4)])
        t10, sg10 = _Mom(), np.ones(0)
        if d.tet10:
            ten = np.asarray(d.tet10, int)
            for s in _TET10_SUB:
                t10.add(_tet_mom(xs[ten[:, s]])[0])
            sg10 = _tet_mom(xs[ten[:, :4]])[1]
        hexm, sgh = _hex_mom(xs[np.asarray(d.hex, int).reshape(-1, 8)])
        solid = _Mom().add(tet).add(t10).add(hexm)
        tri_idx, tri_t = [], []
        for el, t in zip(d.shell, d.shell_t):
            tri_idx += [el[:3]] if len(el) == 3 else [el[:3], [el[0], el[2], el[3]]]
            tri_t += [t] * (len(el) - 2)
        sgeo, svol = _tri_mom(xs[np.asarray(tri_idx, int).reshape(-1, 3)], np.asarray(tri_t, float))
        sec, marea = _section(imp, part), 0.0
        if d.shell:
            marea = dk.num(str(getattr(part if getattr(part, "partType", "") == "PartComposite" else sec, "marea", "") or ""))
            if min(d.shell_t) <= 0:
                w_("SHELL_THICKNESS", f"PID {pid}: 두께 0 인 셸이 있다 — 그 셸은 질량이 없다")
        beam, bvol = _Mom(), 0.0
        if d.beam:
            area = _beam_area(sec, dk)
            if area is None:
                w_("BEAM_MASS", f"PID {pid}: 빔 단면적을 모른다(ELFORM {getattr(sec, 'elform', '?')}) — beam mass not counted")
            else:
                b = np.asarray(d.beam, int)
                line = _seg_mom(xs[b[:, 0]], xs[b[:, 1]])
                beam, bvol = line.scaled(rho * area + float(getattr(sec, "nsm", 0.0) or 0.0)), area * line.m
        if rho <= 0 and (solid.m > 0 or sgeo.m > 0 or d.beam) and pid not in out_pids:
            no_rho.append(f"{pid} ({name_of.get(pid, '')}, MID {getattr(part, 'mid', 0)})")
        pts = _Mom()
        for rows, m in d.points:
            for r in rows:
                pts.add(_point_mom(m / len(rows), xs[r]))
        tokens = [n for n, ok in (("solid", solid.m > 0), ("shell", sgeo.m > 0), ("beam", beam.m > 0), ("point", bool(d.points))) if ok]
        recs[pid] = {"elem": solid.scaled(rho).add(svol, rho).add(sgeo, marea).add(beam), "geo": _Mom().add(solid).add(sgeo),
                     "points": pts, "add": _Mom(), "rho": rho, "rsrc": rsrc, "volume": solid.m + svol.m + bvol,
                     "tokens": tokens, "n": d.n_elem}
        sg[pid] = (sgt, sg10, sgh)
    if no_rho:   # 요소가 있는데 밀도가 없으면 질량이 조용히 빠진다(MID 가 없거나 읽지 못한 재질)
        raise ValueError(f"{_TAG} density missing for parts with elements: PID {', '.join(no_rho)} — 재질 밀도를 찾지 못했다. "
                         f"재질(MID)을 고치거나 강체에서 뺄 파트면 ExcludePart 로 줄 것 (density missing)")

    # ── *ELEMENT_MASS_PART(_SET) ────────────────────────────────────────────
    single, sets = _mass_part_cards(dk)
    for pid, (add, fin) in sorted(single.items()):
        r = recs.get(pid)
        if r is None:
            warn("MASS_PART", f"*ELEMENT_MASS_PART PID {pid}: 읽은 파트가 없다 — 무시")
            continue
        add = fin - r["elem"].m if fin > 0 else add
        if add <= 0 or r["geo"].m <= 0:
            warn("MASS_PART", f"*ELEMENT_MASS_PART PID {pid}: 더할 질량 {add:g} 또는 면적·부피가 0 이다 — 무시")
            continue
        r["add"].add(r["geo"].scaled(add / r["geo"].m))
        r["tokens"].append("mass_part")
    for psid, add, fin, mwd in sets:
        ps = (getattr(imp.partManager, "partSets", {}) or {}).get(psid)
        pids = [p for p in (getattr(ps, "pids", None) or []) if p in recs]
        key = "elem" if mwd == 1 else "geo"
        tot = sum(recs[p][key].m for p in pids)
        add = fin - sum(recs[p]["elem"].m for p in pids) if fin > 0 else add
        if not pids or add <= 0 or tot <= 0:
            warn("MASS_PART", f"*ELEMENT_MASS_PART_SET PSID {psid}: 파트 셋이 없거나, 더할 질량 {add:g}·나눌 바탕이 0 이다 — 무시")
            continue
        for p in pids:
            recs[p]["add"].add(recs[p][key].scaled(add / tot))
            if "mass_part" not in recs[p]["tokens"]:
                recs[p]["tokens"].append("mass_part")

    # ── 합치기 ─────────────────────────────────────────────────────────────
    total, part_list, n_pt, m_pt = _Mom(), [], 0, 0.0
    excl_by_pid = {x["pid"]: x for x in excluded}
    for pid in sorted(recs):
        r = recs[pid]
        mom = _Mom().add(r["elem"]).add(r["points"]).add(r["add"])
        m, c, inertia = _props(mom, x0)
        if pid in out_pids:
            excl_by_pid[pid]["mass"] = m
            continue
        total.add(mom)
        n_pt += len(pdata[pid].points)
        m_pt += r["points"].m
        part_list.append({"pid": pid, "name": name_of.get(pid, ""), "n_elements": r["n"], "mass": m,
                          "com": c if m > 0 else None, "volume": r["volume"], "rho": r["rho"], "inertia_com": inertia,
                          "mass_source": ("+".join(r["tokens"]) or "none") + f" rho={r['rsrc']}"})
    out_nodes = set().union(*[pdata[p].nodes for p in out_pids if p in pdata])
    in_nodes = set().union(*[d.nodes for p, d in pdata.items() if p not in out_pids])
    nid_of = {r: nid for nid, r in row.items()}
    for rows, m in root.points:
        nids = {nid_of[r] for r in rows}
        if nids <= out_nodes and not nids & in_nodes:
            continue
        for r in rows:
            total.add(_point_mom(m / len(rows), xs[r]))
        n_pt += 1
        m_pt += m
    for pid, nm, mid, tm, c, inertia in pin:
        if pid in out_pids:
            excl_by_pid[pid]["mass"] = tm
            continue
        total.add(_body_mom(tm, c - x0, inertia))
        part_list.append({"pid": pid, "name": nm, "n_elements": 0, "mass": tm, "com": c, "volume": 0.0,
                          "rho": raw_ro.get(mid, (0.0, None))[0], "inertia_com": inertia, "mass_source": "PART_INERTIA"})
        warn("PART_INERTIA", f"PID {pid} ({nm}): 질량 TM={tm:g}·무게중심·관성은 카드 그대로 더했다. KMM 리더는 이 파트의 "
                             f"요소를 버리므로 껍질·외곽면에 형상이 없다")
    for pid, tm, c, inertia in cnrb:
        if pid in out_pids:
            excl_by_pid[pid]["mass"] = tm
            continue
        total.add(_body_mom(tm, c - x0, inertia))
        part_list.append({"pid": pid, "name": "CNRB_INERTIA", "n_elements": 0, "mass": tm, "com": c, "volume": 0.0, "rho": 0.0,
                          "inertia_com": inertia, "mass_source": "CNRB_INERTIA"})
        warn("CNRB_INERTIA", f"CNRB PID {pid}: TM={tm:g}·무게중심·관성을 절점 질량에 더했다(이론 매뉴얼 29.1)")

    # ── 리더가 못 읽은 질량 알림 ─────────────────────────────────────────────
    from KooCAEManager.KooElement import IMPORT_LOSS
    if IMPORT_LOSS:
        warn("IMPORT_LOSS", "리더가 버린 요소의 질량은 빠졌다 — " + " · ".join(f"{k} {v}개" for k, v in IMPORT_LOSS.items()))
    interp, pin_pids = getattr(imp, "keywordInterpreted", {}) or {}, {p for p, *_ in pin}
    for kw in sorted(dk.raw):
        if not kw.startswith("ELEMENT_") or kw in _MASSLESS_ELEM or kw.startswith("ELEMENT_MASS_PART") or interp.get(kw, False):
            continue
        if kw == "ELEMENT_TSHELL":   # 리더가 파트로 읽지 않은 PID 의 줄만 원문에 남긴다
            left = {}
            for lines, fmt in dk.blocks(kw):
                wd = 10 if fmt == "i10" else 8
                for ln in lines:
                    p = dk.int(dk.fields(ln, fmt, 2, [wd, wd])[1], 0)
                    if p not in pin_pids and p not in out_pids:
                        left[p] = left.get(p, 0) + 1
            if left:
                warn("UNREAD_ELEMENTS", f"*ELEMENT_TSHELL {sum(left.values())}개(PID {sorted(left)})는 KMM 이 파트로 읽지 않았다"
                                        f"(*PART_COMPOSITE_TSHELL 등) — 질량·형상을 세지 않는다")
        else:
            n = sum(len(lines) for lines, _ in dk.blocks(kw))
            warn("UNREAD_ELEMENTS", f"*{kw} 줄 {n}개는 KMM 이 해석하지 않는다 — 그 질량은 세지 않는다")

    if total.m <= 0:
        raise ValueError(f"{_TAG} total mass is 0 — 넣은 파트에 질량이 없다(밀도·제외 확인)")
    m_all = total.m + sum(x.get("mass", 0.0) for x in excluded)
    for x in excluded:   # 뺀 파트는 모두(자동·직접) 질량과 몫을 경고로 남긴다 — 기기 파트를 잘못 뺐는지 보이게
        x.setdefault("mass", 0.0)
        x["mass_fraction"] = x["mass"] / m_all
        warn("EXCLUDED_PART", f"pid={x['pid']} ({x['name']}) reason={x['reason']} mass={x['mass']:.6g} "
                              f"({x['mass_fraction']:.2%} of deck mass) — 강체에서 뺐다")

    # ── 단위 (제외 뒤 넣은 파트 밀도의 중앙값) ─────────────────────────────────
    rhos = [p["rho"] for p in part_list if p["rho"] > 0 and p["volume"] > 0]   # 밀도로 질량을 낸 파트만
    med = float(np.median(rhos)) if rhos else 0.0
    if units is None:
        units = next((n for n, lo, hi in _RHO_BANDS if lo <= med < hi), None)
        if units is None:
            raise ValueError(f"{_TAG} cannot detect units from median density {med:g} — 띠 밖이다. Units 를 주어라 "
                             f"({', '.join(UNIT_SYSTEMS)})")
        source = f"auto (median rho {med:.4g} of {len(rhos)} parts)"
    else:
        source = "user"
    u = dict(UNIT_SYSTEMS[units], name=units, source=source)
    log(f"{_TAG} UNITS {units} ({source}) — 덱 단위계")

    # ── 질량특성 ────────────────────────────────────────────────────────────
    mass, com, inertia = _props(total, x0)
    pm_, pa = np.linalg.eigh(inertia)
    if np.linalg.det(pa) < 0:
        pa[:, 2] = -pa[:, 2]

    # ── 형상: 볼록 껍질·외곽면 ────────────────────────────────────────────────
    keep = sorted(p for p in pdata if p not in out_pids)
    geo_rows = sorted({row[n] for p in keep for n in pdata[p].nodes})
    pts = xyz[geo_rows] if geo_rows else np.zeros((0, 3))
    hull = _hull(pts, warn)
    if hull["n_vertices"]:
        hv, hf = hull["vertices"], hull["faces"]
        size = np.linalg.norm(hv.max(0) - hv.min(0))
        if hull["volume"] > 1e-9 * size ** 3:      # 평평한(흔든) 껍질은 안팎을 따지지 않는다
            nrm = np.cross(hv[hf[:, 1]] - hv[hf[:, 0]], hv[hf[:, 2]] - hv[hf[:, 0]])
            nrm /= np.maximum(np.linalg.norm(nrm, axis=1), 1e-300)[:, None]
            gap = float(np.einsum("ij,ij->i", nrm, com - hv[hf[:, 0]]).max())
            if gap > 1e-9 * size:
                warn("COM_OUTSIDE_HULL", f"무게중심이 볼록 껍질 밖 {gap:.4g} 에 있다 — 껍질 밖 질량(떨어진 절점 질량·*PART_INERTIA 등)을 확인할 것")
        loc = (hv - com) @ pa
        lo, hi = loc.min(0), loc.max(0)
        obb = {"center": com + pa @ ((lo + hi) / 2.0), "axes": pa, "extents": hi - lo}
    else:
        obb = {"center": com, "axes": pa, "extents": np.zeros(3)}
    tris, groups, start = [], [], 0
    for pid in keep:
        t = _part_surface(pdata[pid], *sg[pid])
        if len(t):
            groups.append((f"PART_{pid}_{_safe_name(name_of.get(pid, ''))}", np.arange(start, start + len(t))))
            tris.append(t)
            start += len(t)
    used, inv = np.unique(np.concatenate(tris) if tris else np.zeros((0, 3), int), return_inverse=True)
    sv, sf = xyz[used], inv.reshape(-1, 3)
    sarea = float(np.linalg.norm(np.cross(sv[sf[:, 1]] - sv[sf[:, 0]], sv[sf[:, 2]] - sv[sf[:, 0]]), axis=1).sum() / 2.0)

    ln, ms = u["length_to_m"], u["mass_to_kg"]
    rb = {
        "units": u, "mass": mass, "com": com, "inertia_com": inertia, "principal_moments": pm_, "principal_axes": pa,
        "bbox": {"min": pts.min(0) if len(pts) else com, "max": pts.max(0) if len(pts) else com},
        "obb": obb, "hull": hull,
        "surface": {"vertices": sv, "faces": sf, "groups": groups, "area": sarea, "n_triangles": int(len(sf))},
        "parts": part_list, "excluded_parts": excluded, "point_masses": {"count": n_pt, "mass": m_pt},
        "warnings": warnings,
        "si": {"mass_kg": mass * ms, "com_m": com * ln, "inertia_com_kgm2": inertia * ms * ln * ln,
               "hull_vertices_m": hull["vertices"] * ln},
    }
    log(f"{_TAG} SUMMARY mass={mass:.6e} com=({com[0]:.4f}, {com[1]:.4f}, {com[2]:.4f}) "
        f"I1..3=({pm_[0]:.4e}, {pm_[1]:.4e}, {pm_[2]:.4e}) parts={len(part_list)} excluded={len(excluded)} "
        f"hull_vertices={hull['n_vertices']} surface_triangles={len(sf)} warnings={len(warnings)}")
    return rb


def write_obj(path, vertices, faces, groups=None, header=None):
    """삼각형 메시 → Wavefront OBJ(1부터 번호). groups=[(이름, 면 번호 배열)] 이면 'g 이름' 으로 묶고, 어느 묶음에도 없는 면은
    'g ungrouped' 로 쓴다. header 는 글 또는 줄 목록이고 '# ' 를 붙여 맨 앞에 쓴다."""
    v = np.asarray(vertices, float).reshape(-1, 3)
    f = np.asarray(faces, int).reshape(-1, 3) + 1
    out = ["# " + h for h in (header.splitlines() if isinstance(header, str) else header)] if header else []
    out += ["v %.10g %.10g %.10g" % tuple(p) for p in v]
    if groups:
        seen = np.zeros(len(f), bool)
        for name, idx in groups:
            idx = np.asarray(idx, int)
            out.append("g " + re.sub(r"\s+", "_", str(name)))
            out += ["f %d %d %d" % tuple(t) for t in f[idx]]
            seen[idx] = True
        if not seen.all():
            out.append("g ungrouped")
            out += ["f %d %d %d" % tuple(t) for t in f[~seen]]
    else:
        out += ["f %d %d %d" % tuple(t) for t in f]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")


def write_rigid_body_json(path, rb):
    """compute_rigid_body 결과 → JSON. 껍질·외곽면 배열과 SI 껍질 꼭짓점은 빼고 개수·부피·면적·묶음 이름만 남긴다."""
    view = {k: v for k, v in rb.items() if k not in ("hull", "surface", "si")}
    h, s = rb["hull"], rb["surface"]
    view["hull"] = {"volume": h["volume"], "area": h["area"], "n_vertices": h["n_vertices"], "n_faces": int(len(h["faces"]))}
    view["surface"] = {"area": s["area"], "n_triangles": s["n_triangles"], "n_vertices": int(len(s["vertices"])),
                       "groups": [name for name, _ in s["groups"]]}
    view["si"] = {k: v for k, v in rb["si"].items() if k != "hull_vertices_m"}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(_jsonable(view), fh, indent=2, ensure_ascii=False)
        fh.write("\n")
