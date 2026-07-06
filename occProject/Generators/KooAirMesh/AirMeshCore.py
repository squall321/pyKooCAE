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

    try:
        stale = gmsh.isInitialized()
    except AttributeError as e:
        # libgmsh 부재 시 import는 성공(CDLL(None))하고 첫 API 호출이 심볼 오류로 죽는다 (O10)
        raise AirMeshError(
            "E_GMSH_INIT",
            "libgmsh 네이티브 심볼 로드 실패 — 배포본에 libgmsh.so.4.15 포함 여부 확인: {e}".format(e=e))
    if stale:
        gmsh.finalize()
    # sys.argv 전달 금지(KAM argv 오파싱) + ~/.gmshrc 전역 옵션 유입 차단
    gmsh.initialize(readConfigFiles=False)
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
        air_vols, bool_info, box_min, box_max = _build_air_region(
            cfg, box_min, box_max, sum(solid_vols), diag, warnings, healed)
        report["boolean"] = bool_info
        if bool_info["eps_pad_retry"]:
            # 재시도로 박스가 커졌으면 유효 경계를 이후 단계·리포트에 반영
            diag = float(np.linalg.norm(box_max - box_min))
            report["bbox"]["padded"] = [box_min.tolist(), box_max.tolist()]
            report["bbox"]["diagonal"] = diag
        t_stage["boolean"] = time.perf_counter() - t0

        # ---- S6 경계면 분류 (outer_box / cavity) ---------------------------
        t0 = time.perf_counter()
        outer_tags, cavity_tags = _classify_boundary(
            air_vols, box_min, box_max, diag, warnings)
        if not outer_tags:
            raise AirMeshError(
                "E_INTERNAL",
                "외곽 박스면을 하나도 분류하지 못함 — 단위 스케일/패딩 확인 (전 면 cavity 판정)")
        report["surfaces"] = {"n_cavity": len(cavity_tags), "n_outer": len(outer_tags)}
        t_stage["classify"] = time.perf_counter() - t0

        # ---- S7 사면체 메시 -------------------------------------------------
        t0 = time.perf_counter()
        _pre_mesh_guard(cfg, bool_info["air_cad_volume"], h_used, cfg["mesh_size"])
        try:
            algo_used, fallback_hit = _generate_mesh(cfg, h_used)
        except AirMeshError as e:
            if healed or bool_info["healed_retry"]:
                # 실증: 깨끗한 형상에 healShapes를 적용하면 주기면 병리로 메시 실패 가능
                raise AirMeshError(e.code, e.message + " — healShapes가 정상 형상을 열화시켰을 수 있음 (heal=always면 auto 권장)")
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
    orig_dims = {}
    for d, _ in imported:
        orig_dims[d] = orig_dims.get(d, 0) + 1

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
        raise AirMeshError(
            "E_STEP_NO_SOLID",
            "STEP에 닫힌 솔리드가 없음 (임포트 엔티티 dim:개수 = {dims}) — 서피스 모델 여부 확인".format(
                dims=orig_dims))

    picked = _select_solids(cfg, solids)
    unselected = [dt for dt in solids if dt not in picked]
    if unselected:
        # 모델에 남겨두면 함께 메시되어 품질 게이트·.msh 출력이 오염된다 (리뷰 확정 결함)
        gmsh.model.occ.remove(unselected, recursive=True)
        gmsh.model.occ.synchronize()
        warnings.append("solid_selection 밖 솔리드 {n}개를 모델에서 제거".format(
            n=len(unselected)))
    if len(picked) > 100:
        warnings.append("솔리드 {n}개 — 불리언 비용 증가 예상".format(n=len(picked)))
    return picked, healed


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

def _build_air_region(cfg, box_min, box_max, solid_vol_sum, diag, warnings,
                      healed_already):
    info = {"eps_pad_retry": False, "healed_retry": False, "slivers_removed": 0,
            "slivers_removed_volume": 0.0}
    size = box_max - box_min

    def _cut(bmin_arr, size_arr):
        # 도구 = 현재 동기화된 볼륨 전부 (힐링 재시도 후 태그가 바뀌어도 안전)
        # addBox 직후 미동기화 상태라 getEntities(3)에 새 박스는 포함되지 않는다
        tools = list(gmsh.model.getEntities(3))
        box = gmsh.model.occ.addBox(*bmin_arr.tolist(), *size_arr.tolist())
        try:
            out, _ = gmsh.model.occ.cut(
                [(3, box)], tools, removeObject=True, removeTool=True)
        except Exception:
            # 실패한 cut은 박스를 모델에 남길 수 있다 — 다음 시도 전 반드시 제거
            # (실증: 잔류 박스가 함께 메시되어 사면체 수가 2배로 오염됨)
            try:
                gmsh.model.occ.remove([(3, box)], recursive=True)
                gmsh.model.occ.synchronize()
            except Exception:
                pass
            raise
        gmsh.model.occ.synchronize()
        return [dt for dt in out if dt[0] == 3]

    # 재시도 사다리: 원 cut → eps-pad(형상 무손상, 접촉/공면 해결) → 힐링(최후 수단).
    # heal을 먼저 쓰면 깨끗한 형상을 열화시킬 수 있음이 실증됨(주기면 병리) — PLAN O6 보정
    try:
        air_vols = _cut(box_min, size)
    except Exception as e1:
        warnings.append("불리언 실패({e}) — eps-pad 재시도".format(e=e1))
        info["eps_pad_retry"] = True
        eps = 1e-3 * diag
        box_min = box_min - eps
        box_max = box_max + eps
        size = box_max - box_min
        try:
            air_vols = _cut(box_min, size)
        except Exception as e2:
            if cfg["heal"] != "never" and not healed_already:
                warnings.append("eps-pad도 실패({e}) — 힐링 후 재시도".format(e=e2))
                try:
                    _heal(gmsh.model.getEntities(3), cfg["heal_tolerance"])
                    info["healed_retry"] = True
                    air_vols = _cut(box_min, size)
                except Exception as e3:
                    raise AirMeshError(
                        "E_BOOLEAN",
                        "불리언 차집합 실패 (eps-pad·힐링 재시도 포함): {e}".format(e=e3))
            else:
                raise AirMeshError(
                    "E_BOOLEAN",
                    "불리언 차집합 실패 (eps-pad 재시도 포함): {e}".format(e=e2))
    # 주의: cut이 솔리드를 소모(removeTool=True)하므로 이 시점 이후 솔리드 태그 사용 금지

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
    return kept, info, box_min, box_max


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
    # OCC bbox는 절대값 ~1e-7(Precision::Confusion)만큼 부풀려 반환된다 — 순수 상대
    # 허용오차는 diag<0.1(미터 단위 소형 부품)에서 전 면 오분류를 일으킴 (리뷰 확정)
    eps = max(1e-6 * diag, 1e-6)
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

def _pre_mesh_guard(cfg, air_volume, h, h_requested):
    n_est = 8.49 * air_volume / (h ** 3)
    if n_est > cfg["mesh"]["max_estimated_elements"]:
        h_suggest = (8.49 * air_volume / cfg["mesh"]["max_estimated_elements"]) ** (1.0 / 3.0)
        msg = "예상 사면체 {n:.3g}개 > 한도 {m:.3g} — mesh_size를 {h:.4g} 이상으로".format(
            n=n_est, m=float(cfg["mesh"]["max_estimated_elements"]), h=h_suggest)
        if h < h_requested:
            # size_guard가 클램프한 상태면 mesh_size를 키워도 같은 실패가 반복된다
            msg += (" (주의: size_guard가 h를 {c:.4g}로 클램프 중 — mesh.size_guard=false,"
                    " solid_selection으로 미세 솔리드 제외, 또는 max_estimated_elements"
                    " 상향이 실제 해결책)").format(c=h)
        raise AirMeshError("E_TOO_LARGE", msg)


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
    bins = [-np.inf] + [i / 10.0 for i in range(11)]
    hist, _ = np.histogram(q, bins=bins)
    labels = ["<=0.0"] + ["{a:.1f}-{b:.1f}".format(a=i / 10.0, b=(i + 1) / 10.0)
                          for i in range(10)]
    quality = {
        "minSICN": {"min": float(q.min()), "mean": float(q.mean()),
                    "n_inverted": int((q <= 0).sum()),
                    "histogram": dict(zip(labels, [int(v) for v in hist]))},
        "gamma": {"min": float(g.min()), "mean": float(g.mean())},
    }
    return quality, len(node_tags), int(len(all_tags))


# ---------------------------------------------------------------------------
# S9 출력
# ---------------------------------------------------------------------------

def _out_path(cfg, suffix):
    return os.path.join(cfg["outputs"]["dir"], cfg["outputs"]["prefix"] + suffix)


def _write_group_stl(path, tags, name, binary):
    """물리그룹 필터 STL 쓰기 — SaveAll/그룹 순서 고정 (프로토타입 P4).

    빈 그룹 금지: SaveAll=0 + 엔티티 0개 그룹이면 gmsh가 조용히 전체 요소를
    저장해버린다 (리뷰 확정 결함). 빈 태그는 호출부에서 걸러야 하며 여기서도 방어.
    """
    if not tags:
        raise AirMeshError("E_INTERNAL", "빈 표면 그룹으로 STL 쓰기 시도: " + name)
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
                path, binary, warnings)
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


def _fix_air_stl_orientation(path, binary, warnings):
    """P1 보정: 각 셸의 법선을 '공기 기준 외향'으로 정렬해 signed volume = 공기체적.

    규칙(리뷰 확정 결함 반영): 셸의 중첩 깊이(자신을 포함하는 다른 셸 수)가
    홀수면 반전. 깊이 0=외곽 박스(또는 분리 공기영역 외피, 유지), 1=캐비티(반전),
    2=밀폐 하우징 내부 보이드(공기가 셸 안쪽 — 유지).
    """
    m = trimesh.load(path, force="mesh")
    if len(m.faces) > 5_000_000:
        warnings.append("air.stl 삼각형 {n}개 > 5M — orientation 후처리 생략".format(
            n=len(m.faces)))
        return False
    bodies = [b.copy() for b in m.split(only_watertight=False)]
    if len(bodies) == 0:
        warnings.append("air.stl 바디 분리 실패 — orientation 후처리 생략")
        return False
    for b in bodies:
        b.fix_normals()  # 각 셸을 자기 내부 기준 outward로 정렬

    def _depth(i):
        probe = bodies[i].vertices[0].reshape(1, 3)
        d = 0
        for j, other in enumerate(bodies):
            if j == i:
                continue
            bmin, bmax = other.bounds
            if not (np.all(probe >= bmin - 1e-12) and np.all(probe <= bmax + 1e-12)):
                continue  # bbox 밖이면 포함 불가
            try:
                inside = bool(other.contains(probe)[0])
            except Exception:
                inside = True  # ray 검사 실패 시 bbox 포함으로 근사
            if inside:
                d += 1
        return d

    for i, b in enumerate(bodies):
        if _depth(i) % 2 == 1:
            b.invert()  # 홀수 깊이 = 공기가 셸 바깥 → 반전해야 공기 외향
    merged = trimesh.util.concatenate(bodies)
    merged.export(path, file_type="stl" if binary else "stl_ascii")
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
