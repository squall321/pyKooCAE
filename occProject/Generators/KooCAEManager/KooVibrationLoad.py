"""Vibration Load: 다중 파트에 동기화된 진동 하중 적용.

핵심 동작:
- 파트마다 상대 진동력 (Explicit) 또는 볼륨 비례 (VolumeProportional)
- 동일 시간 곡선 (DEFINE_CURVE 1개) + 파트별 다른 SF
- 파트 합력 = 사용자 입력 곡선 × relative_factor
- LS-DYNA *LOAD_BODY_PARTS_<dir> 카드 생성 (가속도 = 합력 / mass)

LS-DYNA 카드:
    *DEFINE_CURVE  (1개, 시간-가속도)
    *SET_PART_LIST (파트당 1개, 단일 PID 포함)
    *LOAD_BODY_PARTS_<dir> (파트당 1개, PSID + LCID + SF)
"""
import os
import numpy as np


def apply_vibration_load(dynaImporter, option):
    """진동 하중 적용 진입.

    Args:
        dynaImporter: KooDynaImporter
        option: dict
            - Direction: 'X' | 'Y' | 'Z'
            - LoadType: 'Force' (default) | 'Acceleration'
            - RelativeMode: 'Explicit' | 'VolumeProportional'
            - ReferencePart: PID (VolumeProportional 시; 없으면 첫 파트 fallback + warning)
            - LoadCurve: list of [t, value] pairs
            - PartFactors: dict {pid: factor} (Explicit 모드)
            - PartList: list of PID (VolumeProportional 모드)
    """
    direction = option.get("Direction", "Z").upper()
    if direction not in ("X", "Y", "Z"):
        raise ValueError(f"[VIBRATION_LOAD] Direction must be X/Y/Z, got: {direction}")
    load_type = option.get("LoadType", "Force")
    relative_mode = option.get("RelativeMode", "Explicit")
    load_curve = option.get("LoadCurve", [])
    if not load_curve or len(load_curve) < 2:
        raise ValueError("[VIBRATION_LOAD] LoadCurve required (최소 2 points)")

    # 1. 대상 파트 목록 결정
    if relative_mode.lower() == "explicit":
        part_factors = option.get("PartFactors", {})
        if not part_factors:
            raise ValueError("[VIBRATION_LOAD] Explicit mode requires PartFactors")
        target_pids = list(part_factors.keys())
    elif relative_mode.lower() == "volumeproportional":
        part_list = option.get("PartList", [])
        if not part_list:
            raise ValueError("[VIBRATION_LOAD] VolumeProportional mode requires PartList")
        target_pids = list(part_list)
        # 기준 파트
        ref_pid = option.get("ReferencePart")
        if ref_pid is None:
            ref_pid = target_pids[0]
            print(f"[VIBRATION_LOAD] Warning: ReferencePart 미명시 → 첫 파트 PID {ref_pid} 자동 선택")
        if ref_pid not in target_pids:
            raise ValueError(f"[VIBRATION_LOAD] ReferencePart {ref_pid}가 PartList에 없음")
    else:
        raise ValueError(f"[VIBRATION_LOAD] RelativeMode must be Explicit/VolumeProportional, got: {relative_mode}")

    # 2. 파트 mass/volume 계산
    print(f"[VIBRATION_LOAD] Direction={direction}, LoadType={load_type}, Mode={relative_mode}, Targets={target_pids}")
    # LoadCurve 요약
    max_abs = max(abs(pt[1]) for pt in load_curve)
    t_range = (load_curve[0][0], load_curve[-1][0])
    unit_label = "force" if load_type.lower() == "force" else "accel"
    print(f"  LoadCurve: t=[{t_range[0]}, {t_range[1]}], max |{unit_label}|={max_abs:.4e}")
    part_props = {}  # {pid: {'mass': m, 'volume': v}}
    for pid in target_pids:
        m, v = _compute_part_mass_volume(dynaImporter, pid)
        part_props[pid] = {'mass': m, 'volume': v}
        warn = ""
        if v <= 0:
            warn = "  [WARN] volume=0 (Beam/Discrete 또는 빈 파트 — 무시될 수 있음)"
        elif m <= 0:
            warn = "  [WARN] mass=0 (density=0 또는 MAT 누락 — Force 모드에서 SF 무한대 위험)"
        print(f"  PID {pid}: volume={v:.4e}, mass={m:.4e}{warn}")

    # 3. relative_factor 계산
    if relative_mode.lower() == "explicit":
        rel_factors = {pid: float(part_factors[pid]) for pid in target_pids}
    else:  # VolumeProportional
        v_ref = part_props[ref_pid]['volume']
        if v_ref <= 0:
            raise ValueError(f"[VIBRATION_LOAD] ReferencePart {ref_pid} volume이 0")
        rel_factors = {pid: part_props[pid]['volume'] / v_ref for pid in target_pids}

    # 4. SF 계산 (LoadType에 따라)
    # *LOAD_BODY_PARTS_<dir>의 LCID는 가속도 곡선
    # LoadType=Force: 사용자 곡선 = 합력 → 가속도 = 합력 / mass
    #                 → SF_i = rel_factor_i / mass_i (curve는 정규화 후 곱셈)
    # LoadType=Acceleration: 사용자 곡선 = 가속도 그대로
    #                        → SF_i = rel_factor_i (mass 무관)
    if load_type.lower() == "force":
        # 곡선 amplitude 정규화: max abs value를 1.0으로 → SF에 max_F 흡수
        # 단순화: 곡선 그대로 두고 SF에 1/mass 적용 (LCID amplitude = 합력값과 같음)
        # → SF_i = rel_factor_i / mass_i
        sf_map = {pid: rel_factors[pid] / part_props[pid]['mass']
                  if part_props[pid]['mass'] > 0 else 0
                  for pid in target_pids}
    else:  # Acceleration
        sf_map = {pid: rel_factors[pid] for pid in target_pids}

    # 5. *DEFINE_CURVE 생성 (공통 1개)
    defineMan = dynaImporter.defineManager
    new_lcid = _alloc_lcid(defineMan)
    a1 = [pt[0] for pt in load_curve]
    o1 = [pt[1] for pt in load_curve]
    if hasattr(defineMan, 'CreateDefineCurvewithID'):
        defineMan.CreateDefineCurvewithID(
            LCID=new_lcid, A1=a1, O1=o1,
            name=f"VibLoad_{direction}_curve"
        )
    else:
        raise RuntimeError("[VIBRATION_LOAD] DefineManager.CreateDefineCurvewithID not found")
    print(f"  → *DEFINE_CURVE LCID={new_lcid} ({len(a1)} points)")

    # 6. 파트마다 *SET_PART (단일 PID) + *LOAD_BODY_PARTS_<dir>
    partMan = dynaImporter.partManager
    loadMan = dynaImporter.loadManager
    for pid in target_pids:
        # 단일 파트만 포함하는 PartSet 생성
        new_psid = _alloc_psid(partMan)
        ps = _create_single_part_set(partMan, new_psid, [pid], name=f"VibLoad_PSID_{pid}")
        # LOAD_BODY_PARTS
        loadMan.CreateLoadBodyParts(
            direction=direction,
            psid=new_psid,
            lcid=new_lcid,
            sf=sf_map[pid],
            drlcid=0,
            drsf=1.0
        )
        rel = rel_factors[pid]
        m = part_props[pid]['mass']
        print(f"  → PSID={new_psid} (PID={pid}), SF={sf_map[pid]:.4e}, rel={rel:.3f}, mass={m:.4e}")


# ============================================================================
# helpers
# ============================================================================
def _compute_part_mass_volume(dynaImporter, pid):
    """파트의 mass와 volume 계산 (Solid + Shell, Beam 무시)."""
    partMan = dynaImporter.partManager
    matMan = dynaImporter.matManager
    secMan = dynaImporter.sectionManager

    part = partMan.parts.get(pid) or getattr(partMan, 'partsRigid', {}).get(pid)
    if part is None:
        print(f"  Warning: PID {pid} not found")
        return 0.0, 0.0

    # Material density
    mid = getattr(part, 'mid', 0)
    mat = matMan.materials.get(mid)
    if mat is None:
        print(f"  Warning: MID {mid} (for PID {pid}) not found, density=0")
        rho = 0.0
    else:
        try:
            rho = float(mat.GetRho()) if hasattr(mat, 'GetRho') else float(getattr(mat, 'rho', 0))
        except Exception:
            rho = 0.0

    # Section thickness (shell)
    secid = getattr(part, 'secid', 0)
    section = secMan.sections.get(secid)
    shell_thickness = 0.0
    if section is not None:
        # SECTION_SHELL: T1/T2/T3/T4 평균
        ts = [getattr(section, attr, 0) for attr in ('T1', 'T2', 'T3', 'T4')]
        ts = [float(t) for t in ts if t is not None and float(t) > 0]
        if ts:
            shell_thickness = sum(ts) / len(ts)

    # 요소 순회
    total_volume = 0.0
    elem_mgr = getattr(part, 'elementManager', None)
    if elem_mgr is None:
        return 0.0, 0.0

    for elem in elem_mgr.elements.values():
        try:
            cls_name = type(elem).__name__
            if cls_name in ('SolidElement',) or 'Solid' in cls_name:
                total_volume += _solid_volume(elem)
            elif cls_name in ('FaceElement',) or 'Face' in cls_name or 'Shell' in cls_name:
                # Shell: area × thickness
                area = _face_area(elem)
                if shell_thickness > 0:
                    total_volume += area * shell_thickness
            # LineElement / Beam: 무시 (사용자 결정 Q7)
        except Exception as e:
            # 실패 시 그 요소만 스킵
            continue

    mass = total_volume * rho
    return mass, total_volume


def _solid_volume(elem):
    """Solid 요소 부피 (hex8 / tet4)."""
    nodes = [n for n in getattr(elem, 'nodes', []) if n is not None]
    if len(nodes) == 0:
        return 0.0
    coords = np.array([[n.x, n.y, n.z] for n in nodes])
    unique_count = len(set(id(n) for n in nodes))
    if unique_count == 4 or len(coords) == 4:
        # Tetra: V = |det((v1-v0, v2-v0, v3-v0))| / 6
        v = coords[1:4] - coords[0]
        return abs(np.linalg.det(v)) / 6.0
    elif len(coords) == 8:
        # Hex8: 6 tetra 분할 합 (consistent decomposition)
        # Convention: 0-1-2-3 bottom, 4-5-6-7 top
        # 6 tetra: (0,1,2,5), (0,2,3,7), (0,2,5,7), (0,4,5,7), (2,5,6,7), (3,2,7,...)는 패턴 다양
        # 간단한 구현: 8 노드 cell의 signed volume via 6-tet decomposition (Grandy 1997)
        idx_tets = [(0,1,3,4), (1,2,3,6), (1,3,4,6), (3,4,6,7), (1,4,5,6)]
        v = 0.0
        for tet in idx_tets:
            a, b, c, d = coords[list(tet)]
            v += abs(np.linalg.det(np.array([b-a, c-a, d-a]))) / 6.0
        return v
    elif len(coords) == 6:
        # Pentahedron (wedge): 3 tetra 분할
        idx_tets = [(0,1,2,3), (1,2,3,4), (2,3,4,5)]
        v = 0.0
        for tet in idx_tets:
            a, b, c, d = coords[list(tet)]
            v += abs(np.linalg.det(np.array([b-a, c-a, d-a]))) / 6.0
        return v
    return 0.0


def _face_area(elem):
    """Shell/Face 요소 면적 (quad4 / tri3)."""
    nodes = [n for n in getattr(elem, 'nodes', []) if n is not None]
    if len(nodes) < 3:
        return 0.0
    coords = np.array([[n.x, n.y, n.z] for n in nodes])
    if len(coords) >= 4:
        # Quad: 두 삼각형 합 (0-1-2 + 0-2-3)
        a1 = 0.5 * np.linalg.norm(np.cross(coords[1]-coords[0], coords[2]-coords[0]))
        a2 = 0.5 * np.linalg.norm(np.cross(coords[2]-coords[0], coords[3]-coords[0]))
        return a1 + a2
    elif len(coords) == 3:
        return 0.5 * np.linalg.norm(np.cross(coords[1]-coords[0], coords[2]-coords[0]))
    return 0.0


def _alloc_lcid(defineMan):
    """기존 LCID 중 max + 1."""
    existing = list(getattr(defineMan, 'defines', {}).keys())
    return (max(existing) + 1) if existing else 1


def _alloc_psid(partMan):
    """기존 partSets 중 max psid + 1. partManager.maxSID도 참고."""
    existing = [getattr(ps, 'psid', 0)
                for ps in getattr(partMan, 'partSets', {}).values()]
    base = max(existing) if existing else 0
    base = max(base, getattr(partMan, 'maxSID', 0))
    return base + 1


def _create_single_part_set(partMan, psid, pid_list, name=""):
    """단일/복수 PID를 가진 SET_PART_LIST 생성."""
    from KooCAEManager.KooPart import PartSet
    ps = PartSet(psid=psid, pids=list(pid_list), name=name)
    if not hasattr(partMan, 'partSets'):
        partMan.partSets = {}
    partMan.partSets[psid] = ps
    if hasattr(partMan, 'maxSID'):
        partMan.maxSID = max(partMan.maxSID, psid)
    return ps
