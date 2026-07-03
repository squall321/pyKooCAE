# 공기영역(bbox - solid) 테트라 메시 생성 + 경계면 STL 추출 프로토타입 공용 함수
import os
import time

import gmsh
import numpy as np
import trimesh


# ---------------------------------------------------------------- test STEPs
def create_step_fused(path):
    """구+원기둥 fuse 단일 솔리드 STEP 생성."""
    gmsh.clear()
    gmsh.model.add("solidgen_fused")
    sph = gmsh.model.occ.addSphere(0, 0, 0, 10)
    cyl = gmsh.model.occ.addCylinder(0, 0, 0, 25, 0, 0, 4)
    out, _ = gmsh.model.occ.fuse([(3, sph)], [(3, cyl)])
    gmsh.model.occ.synchronize()
    gmsh.write(path)
    return out


def create_step_two_solids(path):
    """서로 떨어진 솔리드 2개(구 + 박스) STEP 생성."""
    gmsh.clear()
    gmsh.model.add("solidgen_two")
    gmsh.model.occ.addSphere(0, 0, 0, 8)
    gmsh.model.occ.addBox(30, -5, -5, 10, 10, 10)
    gmsh.model.occ.synchronize()
    gmsh.write(path)


# ---------------------------------------------------------------- pipeline
def air_mesh_pipeline(step_path, h, pad, workdir, prefix, h_min=None,
                      algo3d_primary=10, split_stl=True):
    """STEP → bbox 패딩 박스 → cut → 테트라 메시 → 표면 STL 추출.

    반환: 결과 dict (타이밍, 요소수, 품질, 체적, STL 경로 등).
    """
    res = {"prefix": prefix, "h": h, "pad": pad}
    t0 = time.perf_counter()

    gmsh.clear()
    gmsh.model.add("air_" + prefix)

    # 1) STEP import
    imported = gmsh.model.occ.importShapes(step_path)
    solids = [dt for dt in imported if dt[0] == 3]
    res["imported_dimtags"] = imported
    res["n_solids"] = len(solids)
    if not solids:
        raise RuntimeError(f"no 3D solid in {step_path}: {imported}")
    gmsh.model.occ.synchronize()

    # 2) bbox (전체 솔리드 합집합 bbox) + 솔리드 체적
    bb = np.array([gmsh.model.getBoundingBox(3, t) for _, t in solids])
    bmin = bb[:, :3].min(axis=0)
    bmax = bb[:, 3:].max(axis=0)
    res["solid_bbox"] = (bmin.tolist(), bmax.tolist())
    solid_vol = sum(gmsh.model.occ.getMass(3, t) for _, t in solids)
    res["solid_volume_cad"] = solid_vol

    # 3) 패딩 박스 생성 + boolean cut(box - solids)
    pmin = bmin - pad
    size = (bmax - bmin) + 2 * pad
    box_vol = float(np.prod(size))
    res["box_volume"] = box_vol
    res["expected_air_volume"] = box_vol - solid_vol
    box = gmsh.model.occ.addBox(*pmin.tolist(), *size.tolist())
    out, _ = gmsh.model.occ.cut([(3, box)], solids,
                                removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    res["air_dimtags"] = out
    air_vols = [dt for dt in out if dt[0] == 3]
    air_vol_cad = sum(gmsh.model.occ.getMass(3, t) for _, t in air_vols)
    res["air_volume_cad"] = air_vol_cad
    res["t_geometry"] = time.perf_counter() - t0

    # 4) 균일 메시 사이즈 + 3D 메시 (HXT → 실패 시 Delaunay)
    t1 = time.perf_counter()
    gmsh.option.setNumber("Mesh.MeshSizeMin", h if h_min is None else h_min)
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.Algorithm3D", algo3d_primary)
    try:
        gmsh.model.mesh.generate(3)
        res["algo3d_used"] = algo3d_primary
    except Exception as e:
        res["algo3d_primary_error"] = repr(e)
        gmsh.model.mesh.clear()
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Delaunay
        gmsh.model.mesh.generate(3)
        res["algo3d_used"] = 1
    res["t_mesh"] = time.perf_counter() - t1

    # 5) 요소 수 + 품질
    type_names = {4: "tet4", 5: "hex8", 6: "prism6", 7: "pyramid5"}
    etypes, etags, _ = gmsh.model.mesh.getElements(3)
    counts = {type_names.get(t, f"type{t}"): len(tags)
              for t, tags in zip(etypes, etags)}
    res["elem3d_counts"] = counts
    all_tags = np.concatenate([np.asarray(t) for t in etags])
    q = np.array(gmsh.model.mesh.getElementQualities(all_tags, "minSICN"))
    res["quality_minSICN"] = {"min": float(q.min()), "mean": float(q.mean()),
                              "n_negative": int((q < 0).sum())}
    g = np.array(gmsh.model.mesh.getElementQualities(all_tags, "gamma"))
    res["quality_gamma"] = {"min": float(g.min()), "mean": float(g.mean())}

    # 6) 경계면 분류: 외곽 박스면 vs 캐비티(솔리드 스킨)면
    surfs = gmsh.model.getBoundary(air_vols, combined=False, oriented=False)
    eps = 1e-6 * float(np.linalg.norm(size))
    outer, cavity = [], []
    box_min, box_max = pmin, pmin + size
    for _, s in surfs:
        sb = gmsh.model.getBoundingBox(2, abs(s))
        smin, smax = np.array(sb[:3]), np.array(sb[3:])
        on_plane = any(
            (abs(smin[k] - v) < eps and abs(smax[k] - v) < eps)
            for k in range(3) for v in (box_min[k], box_max[k]))
        (outer if on_plane else cavity).append(abs(s))
    res["n_outer_surfs"] = len(outer)
    res["n_cavity_surfs"] = len(cavity)

    # 기대 삼각형 수 (표면별 2D 요소 합)
    def tri_count(tags):
        n = 0
        for s in tags:
            et, etg, _ = gmsh.model.mesh.getElements(2, s)
            for t, tg in zip(et, etg):
                if t == 2:
                    n += len(tg)
        return n
    res["tri_outer_expected"] = tri_count(outer)
    res["tri_cavity_expected"] = tri_count(cavity)

    # 7) STL 출력
    t2 = time.perf_counter()
    paths = {}
    air_stl = os.path.join(workdir, f"{prefix}_air.stl")
    gmsh.model.removePhysicalGroups()
    gmsh.option.setNumber("Mesh.SaveAll", 1)  # 전체 2D 요소 = 공기영역 경계
    gmsh.write(air_stl)
    paths["air"] = air_stl

    if split_stl:
        gmsh.option.setNumber("Mesh.SaveAll", 0)
        cav_stl = os.path.join(workdir, f"{prefix}_cavity.stl")
        gmsh.model.removePhysicalGroups()
        gmsh.model.addPhysicalGroup(2, cavity, name="cavity")
        gmsh.write(cav_stl)
        paths["cavity"] = cav_stl

        box_stl = os.path.join(workdir, f"{prefix}_outer_box.stl")
        gmsh.model.removePhysicalGroups()
        gmsh.model.addPhysicalGroup(2, outer, name="outer_box")
        gmsh.write(box_stl)
        paths["outer_box"] = box_stl
        gmsh.model.removePhysicalGroups()
    res["t_stl"] = time.perf_counter() - t2
    res["stl_paths"] = paths
    res["t_total"] = time.perf_counter() - t0
    return res


# ---------------------------------------------------------------- manual STL
def write_surface_stl_manual(surf_tags, path):
    """물리그룹 STL 필터가 안 통할 때 대비: 표면 태그별 삼각형 직접 추출."""
    node_tags, coords, _ = gmsh.model.mesh.getNodes()
    coords = np.asarray(coords).reshape(-1, 3)
    idx = {int(t): i for i, t in enumerate(node_tags)}
    faces_xyz = []
    for s in surf_tags:
        et, _, entags = gmsh.model.mesh.getElements(2, s)
        for t, nt in zip(et, entags):
            if t != 2:
                continue
            for tri in np.asarray(nt, dtype=np.int64).reshape(-1, 3):
                faces_xyz.append([coords[idx[int(n)]] for n in tri])
    v = np.asarray(faces_xyz).reshape(-1, 3)
    f = np.arange(len(v)).reshape(-1, 3)
    m = trimesh.Trimesh(vertices=v, faces=f, process=True)
    m.export(path)
    return len(m.faces)


# ---------------------------------------------------------------- validation
def validate_stl(path, expected_volume=None, label=""):
    """trimesh로 STL 로드 → watertight / 체적 검증."""
    m = trimesh.load(path, force="mesh")
    out = {"label": label or os.path.basename(path),
           "n_faces": len(m.faces), "n_vertices": len(m.vertices),
           "watertight": bool(m.is_watertight),
           "winding_consistent": bool(m.is_winding_consistent),
           "volume_raw": float(m.volume)}
    if not m.is_winding_consistent or m.volume < 0:
        m2 = m.copy()
        m2.fix_normals()
        out["volume_fixed_normals"] = float(m2.volume)
    vol = out.get("volume_fixed_normals", out["volume_raw"])
    if expected_volume is not None:
        out["expected_volume"] = expected_volume
        out["rel_error_pct"] = 100.0 * (vol - expected_volume) / expected_volume
    return out
