# AIRMESH 코어: gmsh Python API로 bbox−솔리드 공기영역을 절단·사면체화·STL 스킨 추출
# 설계/근거: docs/PLAN_AirMeshGeneration.md (프로토타입 실증 P1~P5 반영)
import os
import time

import gmsh
import numpy as np
import trimesh


class AirMeshError(Exception):
    """AIRMESH 파이프라인 실패 (code + 사용자 메시지). 절대 sys.exit 하지 않는다."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__("{code}: {message}".format(code=code, message=message))


_ALGO3D = {"hxt": 10, "delaunay": 1, "frontal": 4}
_TET4 = 4  # gmsh 3D 요소 타입: 4=tet4 (5=hex8, 6=prism6, 7=pyramid5)


def run_pipeline(cfg, report):
    """공기영역 메시 파이프라인 전체 실행. report dict를 채우고, 실패 시 AirMeshError.

    gmsh 세션은 이 함수가 소유한다 (finally에서 finalize).
    """
    t_stage = {}
    warnings = report.setdefault("warnings", [])
    deferred_failures = []

    if gmsh.isInitialized():
        gmsh.finalize()
    gmsh.initialize()  # sys.argv 절대 전달 금지 (KAM argv가 gmsh 옵션으로 오파싱됨)
    try:
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.option.setNumber("General.Verbosity", 2)
        gmsh.logger.start()
        if cfg["mesh"]["threads"] > 0:
            gmsh.option.setNumber("General.NumThreads", cfg["mesh"]["threads"])
        if cfg["occ_target_unit"]:
            gmsh.option.setString("Geometry.OCCTargetUnit", cfg["occ_target_unit"])
        gmsh.model.add("airmesh")

        # ---- S2/S3 STEP 임포트 + 힐링 -------------------------------------
        t0 = time.perf_counter()
        solids, healed = _import_solids(cfg, warnings)
        report["input"] = {
            "step": cfg["input_step"],
            "n_solids": len(solids),
            "healed": healed,
        }
        t_stage["import"] = time.perf_counter() - t0

        # ---- S4 bbox / 패딩 / size guard ----------------------------------
        t0 = time.perf_counter()
        bmin, bmax, solid_vols, min_solid_diag = _bbox_and_volumes(solids)
        report["input"]["solid_cad_volumes"] = solid_vols
        h_used = _apply_size_guard(cfg, min_solid_diag, warnings)
        box_min, box_max, pad_applied = _padded_box(cfg, bmin, bmax)
        diag = float(np.linalg.norm(box_max - box_min))
        report["bbox"] = {
            "tight": [bmin.tolist(), bmax.tolist()],
            "padded": [box_min.tolist(), box_max.tolist()],
            "diagonal": diag,
            "padding_applied": pad_applied,
        }
        _units_sanity_check(diag, h_used, warnings)
        t_stage["bbox"] = time.perf_counter() - t0

        # ---- S5 불리언 (box − solids) --------------------------------------
        t0 = time.perf_counter()
        air_vols, bool_info = _build_air_region(
            cfg, solids, box_min, box_max, sum(solid_vols), diag, warnings)
        report["boolean"] = bool_info
        t_stage["boolean"] = time.perf_counter() - t0

        # ---- S6 경계면 분류 (outer_box / cavity) ---------------------------
        t0 = time.perf_counter()
        outer_tags, cavity_tags = _classify_boundary(
            air_vols, box_min, box_max, diag, warnings)
        report["surfaces"] = {"n_cavity": len(cavity_tags), "n_outer": len(outer_tags)}
        t_stage["classify"] = time.perf_counter() - t0

        # ---- S7 사면체 메시 -------------------------------------------------
        t0 = time.perf_counter()
        _pre_mesh_guard(cfg, bool_info["air_cad_volume"], h_used)
        try:
            algo_used, fallback_hit = _generate_mesh(cfg, h_used)
        except AirMeshError as e:
            if healed and cfg["heal"] == "always":
                # 실증: 깨끗한 형상에 healShapes를 강제하면 주기면 병리로 메시 실패 가능
                raise AirMeshError(e.code, e.message + " — heal=always가 정상 형상을 열화시켰을 수 있음, heal=auto 권장")
            raise
        t_stage["mesh"] = time.perf_counter() - t0

        # ---- S8 품질 (타입 하드 단언 + SICN/gamma) --------------------------
        t0 = time.perf_counter()
        quality, n_nodes, n_tets = _quality_stats()
        report["mesh"] = {
            "algorithm3d_used": algo_used,
            "fallback_triggered": fallback_hit,
            "h_requested": cfg["mesh_size"],
            "h_used": h_used,
            "n_nodes": n_nodes,
            "n_tets": n_tets,
            "quality": quality,
        }
        if quality["minSICN"]["n_inverted"] > 0:
            msg = "역요소 {n}개 (minSICN<=0)".format(n=quality["minSICN"]["n_inverted"])
            if cfg["validation"]["fail_on_inverted"]:
                deferred_failures.append(("E_QUALITY", msg))
            warnings.append(msg)
        if quality["minSICN"]["min"] < cfg["validation"]["min_sicn_warn"]:
            warnings.append("최저 품질 minSICN={v:.3f} < 경고 기준 {w}".format(
                v=quality["minSICN"]["min"], w=cfg["validation"]["min_sicn_warn"]))
        t_stage["quality"] = time.perf_counter() - t0

        # ---- S9 출력 (.msh / STL 3종 + orientation 후처리) ------------------
        t0 = time.perf_counter()
        air_vol_tags = [t for _, t in air_vols]
        stl_info = _write_outputs(cfg, air_vol_tags, outer_tags, cavity_tags, warnings)
        report["stl"] = stl_info
        t_stage["outputs"] = time.perf_counter() - t0

        # ---- S10 검증 (watertight / 체적) -----------------------------------
        t0 = time.perf_counter()
        vol_info = _validate_outputs(cfg, stl_info, bool_info, warnings, deferred_failures)
        report["volumes"] = vol_info
        t_stage["validate"] = time.perf_counter() - t0

        report["timings_s"] = {k: round(v, 4) for k, v in t_stage.items()}
        report["timings_s"]["total"] = round(sum(t_stage.values()), 4)

        if deferred_failures:
            code, msg = deferred_failures[0]
            raise AirMeshError(code, msg + " (산출물은 검사용으로 보존됨)")
    finally:
        try:
            log = gmsh.logger.get()
            report["gmsh_log_tail"] = list(log[-50:])
            gmsh.logger.stop()
        except Exception:
            pass
        if gmsh.isInitialized():
            gmsh.finalize()


# ---------------------------------------------------------------------------
# S2/S3 임포트 + 힐링
# ---------------------------------------------------------------------------

def _import_solids(cfg, warnings):
    try:
        imported = gmsh.model.occ.importShapes(cfg["input_step"])
    except Exception as e:
        raise AirMeshError("E_STEP_IMPORT", "STEP 임포트 실패: {e}".format(e=e))
    gmsh.model.occ.synchronize()

    healed = False
    if cfg["heal"] == "always":
        imported = _heal(imported, cfg["heal_tolerance"])
        healed = True

    solids = [dt for dt in imported if dt[0] == 3]
    if not solids and cfg["heal"] == "auto":
        warnings.append("임포트 결과 솔리드 0개 — healShapes 후 재시도")
        imported = _heal(imported, cfg["heal_tolerance"])
        healed = True
        solids = [dt for dt in imported if dt[0] == 3]
    if not solids:
        dims = {}
        for d, _ in imported:
            dims[d] = dims.get(d, 0) + 1
        raise AirMeshError(
            "E_STEP_NO_SOLID",
            "STEP에 닫힌 솔리드가 없음 (발견된 엔티티 dim:개수 = {dims}) — 서피스 모델 여부 확인".format(dims=dims))

    solids = _select_solids(cfg, solids)
    if len(solids) > 100:
        warnings.append("솔리드 {n}개 — 불리언 비용 증가 예상".format(n=len(solids)))
    return solids, healed


def _heal(dimtags, tolerance):
    # 주의(실증됨): healShapes는 원본 shape를 소모하고 치유 복사본으로 교체한다.
    # 반환 리스트는 하위 엔티티(면/선/점)가 중복 포함된 노이즈라 그대로 못 쓴다.
    # 원본을 추가로 remove하면 태그 충돌로 치유본까지 삭제되므로 절대 금지.
    gmsh.model.occ.healShapes(
        dimTags=dimtags, tolerance=tolerance,
        fixDegenerated=True, fixSmallEdges=True, fixSmallFaces=True,
        sewFaces=True, makeSolids=True)
    gmsh.model.occ.synchronize()
    return gmsh.model.getEntities(3)  # 이 시점 모델의 볼륨 = 치유된 솔리드 전부


def _select_solids(cfg, solids):
    sel = cfg["solid_selection"]
    if sel == "all":
        return solids
    picked = []
    for i in sel:  # 1-based (occ.importShapes 반환 순서)
        if i < 1 or i > len(solids):
            raise AirMeshError(
                "E_CONFIG",
                "solid_selection {i}가 범위 밖 (솔리드 {n}개)".format(i=i, n=len(solids)))
        picked.append(solids[i - 1])
    return picked


# ---------------------------------------------------------------------------
# S4 bbox / 패딩 / size guard
# ---------------------------------------------------------------------------

def _bbox_and_volumes(solids):
    bb = np.array([gmsh.model.getBoundingBox(3, t) for _, t in solids])
    bmin = bb[:, :3].min(axis=0)
    bmax = bb[:, 3:].max(axis=0)
    solid_vols = [float(gmsh.model.occ.getMass(3, t)) for _, t in solids]
    per_diag = np.linalg.norm(bb[:, 3:] - bb[:, :3], axis=1)
    return bmin, bmax, solid_vols, float(per_diag.min())


def _apply_size_guard(cfg, min_solid_diag, warnings):
    h = cfg["mesh_size"]
    limit = 0.25 * min_solid_diag
    if h > limit:
        if cfg["mesh"]["size_guard"]:
            warnings.append(
                "mesh_size {h}가 최소 솔리드 대각 {d:.4g}의 1/4 초과 — {c:.4g}로 클램프".format(
                    h=h, d=min_solid_diag, c=limit))
            return limit
        warnings.append(
            "mesh_size {h}가 조대함 (권장 <= {c:.4g}) — facet화 체적 오차 커짐".format(
                h=h, c=limit))
    return h


def _padded_box(cfg, bmin, bmax):
    pad = cfg["padding"]
    diag = float(np.linalg.norm(bmax - bmin))
    if isinstance(pad, list):
        p = [float(v) for v in pad]  # [x-,x+,y-,y+,z-,z+]
    else:
        p = [float(pad)] * 6
    if cfg["padding_relative"]:
        p = [v * diag for v in p]
    box_min = bmin - np.array([p[0], p[2], p[4]])
    box_max = bmax + np.array([p[1], p[3], p[5]])
    return box_min, box_max, p


def _units_sanity_check(diag, h, warnings):
    ratio = diag / h
    if ratio > 1e5 or ratio < 2:
        warnings.append(
            "bbox 대각선/메시 사이즈 비율 {r:.3g} — 단위(mm/m) 혼동 의심".format(r=ratio))


# ---------------------------------------------------------------------------
# S5 불리언
# ---------------------------------------------------------------------------

def _build_air_region(cfg, solids, box_min, box_max, solid_vol_sum, diag, warnings):
    info = {"eps_pad_retry": False, "healed_retry": False, "slivers_removed": 0,
            "slivers_removed_volume": 0.0}
    size = box_max - box_min

    def _cut(bmin_arr, size_arr):
        box = gmsh.model.occ.addBox(*bmin_arr.tolist(), *size_arr.tolist())
        out, _ = gmsh.model.occ.cut(
            [(3, box)], list(solids), removeObject=True, removeTool=True)
        gmsh.model.occ.synchronize()
        return [dt for dt in out if dt[0] == 3]

    try:
        air_vols = _cut(box_min, size)
    except Exception as e1:
        warnings.append("불리언 실패({e}) — eps-pad 재시도".format(e=e1))
        info["eps_pad_retry"] = True
        eps = 1e-3 * diag
        try:
            air_vols = _cut(box_min - eps, size + 2 * eps)
        except Exception as e2:
            raise AirMeshError(
                "E_BOOLEAN",
                "불리언 차집합 실패 (eps-pad 재시도 포함): {e}".format(e=e2))
    # 주의: cut이 solids를 소모(removeTool=True)하므로 이 시점 이후 솔리드 태그 사용 금지

    if not air_vols:
        raise AirMeshError("E_BOOLEAN", "불리언 결과 공기 볼륨이 없음 (솔리드가 박스 전체를 채움?)")

    # 슬리버 제거
    box_vol = float(np.prod(size))
    kept = []
    for dt in air_vols:
        v = float(gmsh.model.occ.getMass(3, dt[1]))
        if v < 1e-9 * box_vol:
            info["slivers_removed"] += 1
            info["slivers_removed_volume"] += v
            gmsh.model.occ.remove([dt], recursive=True)
        else:
            kept.append(dt)
    if info["slivers_removed"]:
        gmsh.model.occ.synchronize()
        warnings.append("슬리버 공기 볼륨 {n}개 제거 (총 {v:.3g})".format(
            n=info["slivers_removed"], v=info["slivers_removed_volume"]))
    if not kept:
        raise AirMeshError("E_BOOLEAN", "슬리버 제거 후 남은 공기 볼륨이 없음")

    air_cad = sum(float(gmsh.model.occ.getMass(3, t)) for _, t in kept)
    expected = box_vol - solid_vol_sum
    info.update({
        "n_air_volumes": len(kept),
        "air_cad_volume": air_cad,
        "box_volume": box_vol,
        "expected_air_volume_cad": expected,
    })
    if expected > 0 and abs(air_cad - expected) / expected > 1e-6:
        warnings.append(
            "CAD 공기체적 {a:.6g} != 기대 {e:.6g} — 솔리드 중첩 또는 박스 접촉 가능".format(
                a=air_cad, e=expected))
    return kept, info


# ---------------------------------------------------------------------------
# S6 경계면 분류
# ---------------------------------------------------------------------------

def _classify_boundary(air_vols, box_min, box_max, diag, warnings):
    # combined=True: 볼륨 간 공유(내부) 면은 상쇄되어 진짜 외피(skin)만 남는다 (O9)
    skin = set(abs(s) for _, s in gmsh.model.getBoundary(
        air_vols, combined=True, oriented=False))
    per_vol = set(abs(s) for _, s in gmsh.model.getBoundary(
        air_vols, combined=False, oriented=False))
    internal = per_vol - skin
    if internal:
        warnings.append(
            "공기 볼륨 간 내부 공유 면 {n}개 — STL 외피에서 제외".format(n=len(internal)))
    eps = 1e-6 * diag
    outer, cavity = [], []
    for s in skin:
        sb = gmsh.model.getBoundingBox(2, s)
        smin, smax = np.array(sb[:3]), np.array(sb[3:])
        on_plane = any(
            (abs(smin[k] - v) < eps and abs(smax[k] - v) < eps)
            for k in range(3) for v in (box_min[k], box_max[k]))
        (outer if on_plane else cavity).append(s)
    return sorted(outer), sorted(cavity)


# ---------------------------------------------------------------------------
# S7 메시
# ---------------------------------------------------------------------------

def _pre_mesh_guard(cfg, air_volume, h):
    n_est = 8.49 * air_volume / (h ** 3)
    if n_est > cfg["mesh"]["max_estimated_elements"]:
        h_suggest = (8.49 * air_volume / cfg["mesh"]["max_estimated_elements"]) ** (1.0 / 3.0)
        raise AirMeshError(
            "E_TOO_LARGE",
            "예상 사면체 {n:.3g}개 > 한도 {m:.3g} — mesh_size를 {h:.4g} 이상으로".format(
                n=n_est, m=float(cfg["mesh"]["max_estimated_elements"]), h=h_suggest))


def _generate_mesh(cfg, h):
    gmsh.option.setNumber("Mesh.MeshSizeMin", h)
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Optimize", 1 if cfg["mesh"]["optimize"] else 0)

    primary = _ALGO3D[cfg["mesh"]["algorithm3d"]]
    ladder = [primary]
    if cfg["mesh"]["fallback"]:
        ladder += [a for a in (1, 4) if a != primary]

    last_err = None
    for i, algo in enumerate(ladder):
        gmsh.option.setNumber("Mesh.Algorithm3D", algo)
        try:
            gmsh.model.mesh.generate(3)
            return algo, i > 0
        except Exception as e:
            last_err = e
            gmsh.model.mesh.clear()
    raise AirMeshError("E_MESH", "3D 메시 생성 실패 (알고리즘 {l}): {e}".format(
        l=ladder, e=last_err))


def _quality_stats():
    etypes, etags, _ = gmsh.model.mesh.getElements(3)
    type_set = set(int(t) for t in etypes)
    if type_set != {_TET4}:
        # 5절점 피라미드는 KooElement 임포터에서 무경고 소실됨 — 구조적 차단 (O13)
        raise AirMeshError(
            "E_INTERNAL", "3D 요소 타입이 tet4 외 발견: {s}".format(s=type_set))
    all_tags = np.concatenate([np.asarray(t) for t in etags])
    q = np.array(gmsh.model.mesh.getElementQualities(all_tags, "minSICN"))
    g = np.array(gmsh.model.mesh.getElementQualities(all_tags, "gamma"))
    node_tags, _, _ = gmsh.model.mesh.getNodes()
    quality = {
        "minSICN": {"min": float(q.min()), "mean": float(q.mean()),
                    "n_inverted": int((q <= 0).sum())},
        "gamma": {"min": float(g.min()), "mean": float(g.mean())},
    }
    return quality, len(node_tags), int(len(all_tags))


# ---------------------------------------------------------------------------
# S9 출력
# ---------------------------------------------------------------------------

def _out_path(cfg, suffix):
    return os.path.join(cfg["outputs"]["dir"], cfg["outputs"]["prefix"] + suffix)


def _write_group_stl(path, tags, name, binary):
    """물리그룹 필터 STL 쓰기 — SaveAll/그룹 순서 고정 (프로토타입 P4)."""
    gmsh.option.setNumber("Mesh.Binary", 1 if binary else 0)
    gmsh.option.setNumber("Mesh.SaveAll", 0)
    gmsh.model.removePhysicalGroups()
    gmsh.model.addPhysicalGroup(2, tags, name=name)
    gmsh.write(path)
    gmsh.model.removePhysicalGroups()


def _write_outputs(cfg, air_vol_tags, outer_tags, cavity_tags, warnings):
    out = cfg["outputs"]
    stl_info = {}

    # 체적 메시 먼저 (.msh 4.1 ASCII — KooMSHImporter 전방호환)
    if out["volume_mesh"] in ("msh", "both"):
        gmsh.model.removePhysicalGroups()
        gmsh.model.addPhysicalGroup(3, air_vol_tags, name="air_volume")
        if cavity_tags:
            gmsh.model.addPhysicalGroup(2, cavity_tags, name="cavity")
        gmsh.model.addPhysicalGroup(2, outer_tags, name="outer_box")
        gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
        gmsh.option.setNumber("Mesh.Binary", 0)
        gmsh.option.setNumber("Mesh.SaveAll", 1)
        gmsh.write(_out_path(cfg, "_air.msh"))
        gmsh.model.removePhysicalGroups()
        stl_info["msh"] = {"path": _out_path(cfg, "_air.msh")}
    if out["volume_mesh"] in ("vtk", "both"):
        gmsh.option.setNumber("Mesh.SaveAll", 1)
        gmsh.write(_out_path(cfg, "_air.vtk"))
        stl_info["vtk"] = {"path": _out_path(cfg, "_air.vtk")}

    if out["geometry_debug"]:
        try:
            gmsh.write(_out_path(cfg, "_air_geom.brep"))
        except Exception as e:
            warnings.append("brep 디버그 출력 실패: {e}".format(e=e))

    binary = out["stl_binary"]
    if out["air_stl"]:
        path = _out_path(cfg, "_air.stl")
        _write_group_stl(path, outer_tags + cavity_tags, "air", binary)
        stl_info["air"] = {"path": path, "orientation_fixed": False}
        if out["fix_orientation"]:
            stl_info["air"]["orientation_fixed"] = _fix_air_stl_orientation(
                path, warnings)
    if out["split_stls"]:
        if cavity_tags:
            path = _out_path(cfg, "_cavity.stl")
            _write_group_stl(path, cavity_tags, "cavity", binary)
            stl_info["cavity"] = {"path": path}
        else:
            warnings.append("cavity 면이 없음 — 분리 STL 생략 (솔리드가 박스 밖?)")
        path = _out_path(cfg, "_outer_box.stl")
        _write_group_stl(path, outer_tags, "outer_box", binary)
        stl_info["outer_box"] = {"path": path}
    return stl_info


def _fix_air_stl_orientation(path, warnings):
    """P1 보정: cavity 바디 법선 반전으로 signed volume = 공기체적이 되게 재작성."""
    m = trimesh.load(path, force="mesh")
    if len(m.faces) > 5_000_000:
        warnings.append("air.stl 삼각형 {n}개 > 5M — orientation 후처리 생략".format(
            n=len(m.faces)))
        return False
    bodies = m.split(only_watertight=False)
    if len(bodies) == 0:
        warnings.append("air.stl 바디 분리 실패 — orientation 후처리 생략")
        return False
    diag = [float(np.linalg.norm(b.bounds[1] - b.bounds[0])) for b in bodies]
    outer_i = int(np.argmax(diag))
    fixed = []
    for i, b in enumerate(bodies):
        bb = b.copy()
        bb.fix_normals()  # 각 바디 outward 정렬
        if i != outer_i:
            bb.invert()  # 캐비티: 공기 기준 outward = 솔리드 안쪽 방향
        fixed.append(bb)
    trimesh.util.concatenate(fixed).export(path)
    return True


# ---------------------------------------------------------------------------
# S10 검증
# ---------------------------------------------------------------------------

def _validate_stl_file(path):
    m = trimesh.load(path, force="mesh")
    return {
        "triangles": int(len(m.faces)),
        "watertight": bool(m.is_watertight),
        "winding_consistent": bool(m.is_winding_consistent),
        "signed_volume": float(m.volume),
    }


def _validate_outputs(cfg, stl_info, bool_info, warnings, deferred_failures):
    vol_info = {}
    for key in ("air", "cavity", "outer_box"):
        if key in stl_info:
            stl_info[key].update(_validate_stl_file(stl_info[key]["path"]))

    if "air" in stl_info:
        air = stl_info["air"]
        if not (air["watertight"] and air["winding_consistent"]):
            deferred_failures.append(
                ("E_STL_INVALID", "air.stl watertight={w} winding={c}".format(
                    w=air["watertight"], c=air["winding_consistent"])))

        air_discrete = air["signed_volume"]
        vol_info["air_discrete"] = air_discrete
        cad = bool_info["air_cad_volume"]
        vol_info["faceting_error_vs_cad_pct"] = 100.0 * (air_discrete - cad) / cad

        # 이산 기대값 대비 검증 (P2): box_discrete − cavity_discrete
        if "outer_box" in stl_info and "cavity" in stl_info:
            expected_discrete = abs(stl_info["outer_box"]["signed_volume"]) \
                - abs(stl_info["cavity"]["signed_volume"])
            vol_info["air_expected_discrete"] = expected_discrete
            if expected_discrete > 0:
                err = 100.0 * (air_discrete - expected_discrete) / expected_discrete
                vol_info["air_discrete_vs_expected_pct"] = err
                if abs(err) > 0.5:
                    warnings.append(
                        "이산 공기체적 불일치 {e:.3f}% (>0.5%)".format(e=err))
        if abs(vol_info["faceting_error_vs_cad_pct"]) > 100.0 * cfg["validation"]["volume_error_warn"]:
            warnings.append(
                "CAD 대비 체적 오차 {e:.2f}% > 경고 기준 — mesh_size 축소 검토".format(
                    e=vol_info["faceting_error_vs_cad_pct"]))
    return vol_info
