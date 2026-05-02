"""
KooTetraRemesher — 사면체 파트 리메시 모듈

찌그러진 사면체 요소를 gmsh로 리메시하여 품질 개선.
외곽면 STL 추출 → gmsh 3D 메시 생성 → 원본 교체.

최소 dt 보장, 공유 노드 보존(옵션) 지원.
"""

import os
import sys
import math
import numpy as np
import tempfile
from scipy.spatial import KDTree


def _check_pids_not_in_preserved_includes(dynaImporter, pids, mode_name):
    """수정 대상 PID가 보존된 include에 있으면 명확한 에러로 중단.

    Args:
        dynaImporter: KooDynaImporter
        pids: 수정 대상 PID 리스트
        mode_name: 모드 이름 (에러 메시지용)

    Raises:
        ValueError: 모순 발견 시
    """
    dyna_mgr = getattr(dynaImporter, 'dynaManager', None)
    if dyna_mgr is None or not hasattr(dyna_mgr, 'findPreservedIncludeForPID'):
        return
    conflicts = []
    for pid in pids:
        inc_file = dyna_mgr.findPreservedIncludeForPID(pid)
        if inc_file:
            conflicts.append((pid, inc_file))
    if conflicts:
        msg_lines = [
            f"[{mode_name}] 보존된 include 안의 PID를 수정할 수 없습니다:",
        ]
        for pid, f in conflicts:
            msg_lines.append(f"  PID {pid} → '{os.path.basename(f)}' (보존 지정됨)")
        msg_lines.append(
            "해결: scenario.json의 'preserve_includes'에서 해당 파일을 제외하거나 PID를 수정 대상에서 빼세요."
        )
        raise ValueError("\n".join(msg_lines))


def remesh_tetra_parts(dynaImporter, option):
    """사면체 파트 리메시 메인 함수.

    Args:
        dynaImporter: KooMeshImporter
        option: dict
            - PID: 대상 PID 리스트
            - MinDt: 최소 보장 timestep (기본 0)
            - TargetEdgeLength: 목표 요소 크기 (기본 0=자동)
            - MaxAspectRatio: 허용 최대 aspect ratio (기본 10)
            - SmoothingIterations: gmsh smoothing 반복 (기본 5)
            - PreserveSharedNodes: 공유 노드 보존 (기본 True)
    """
    from KooCAEManager.KooElement import (
        compute_element_stable_dt, compute_element_min_edge_length,
        SolidElement, FaceElement
    )
    from KooCAEManager.KooPart import KooPart

    pids = option.get("PID", [])
    min_dt = option.get("MinDt", 0.0)
    target_edge = option.get("TargetEdgeLength", 0.0)
    max_aspect = option.get("MaxAspectRatio", 10.0)
    smooth_iter = option.get("SmoothingIterations", 5)
    preserve_shared = option.get("PreserveSharedNodes", True)
    objective = option.get("Objective", "quality").lower()
    # objective: quality, coarsen, refine, match_dt

    if not pids:
        print("RemeshTetra: PID가 지정되지 않았습니다.")
        return

    # 보존된 include 안의 PID를 건드리려 하는지 검사 → 모순 시 즉시 에러
    _check_pids_not_in_preserved_includes(dynaImporter, pids, "RemeshTetra")

    partManager = dynaImporter.partManager
    nodeManager = dynaImporter.nodeManager
    matManager = dynaImporter.matManager

    # gmsh 바이너리 경로 (기존 KooPart 방식, basePath 지정)
    import os as _os
    _base = _os.path.dirname(_os.path.abspath(__file__))
    gmsh_path = KooPart._find_linux_gmsh(basePath=_base)

    total_remeshed = 0

    for pid in pids:
        part = partManager.parts.get(pid)
        if part is None:
            print(f"RemeshTetra: PID {pid} 없음, skip")
            continue
        if not part.elementManager.elements:
            print(f"RemeshTetra: PID {pid} 요소 없음, skip")
            continue

        # 사면체 확인 (TETRA4 또는 퇴화 HEXA8 = 고유 노드 4개)
        first_elem = next(iter(part.elementManager.elements.values()))
        if not isinstance(first_elem, SolidElement):
            print(f"RemeshTetra: PID {pid} 솔리드가 아님, skip")
            continue
        unique_nodes = len(set(n.id for n in first_elem.nodes if n is not None))
        if first_elem.type in ("TETRA4", "TETRA10"):
            pass  # 정상 사면체
        elif first_elem.type == "HEXA8" and unique_nodes <= 5:
            print(f"RemeshTetra: PID {pid} 퇴화 HEXA8 → 사면체로 처리 (고유 노드 {unique_nodes}개)")
        else:
            print(f"RemeshTetra: PID {pid} 사면체가 아님 ({first_elem.type}, 고유 노드 {unique_nodes}개), skip")
            continue

        # 재료 물성
        mat = part.material
        if mat is None:
            print(f"RemeshTetra: PID {pid} 재료 없음, skip")
            continue
        E = mat.GetE()
        rho = mat.GetRho()
        nu = mat.GetNu()
        if E <= 0 or rho <= 0:
            print(f"RemeshTetra: PID {pid} 물성 이상 (E={E}, rho={rho}), skip")
            continue

        # nu 클램프
        if nu > 0.45:
            print(f"RemeshTetra: PID {pid} nu={nu} > 0.45 → 0.45로 클램프 (음속 계산용)")
            nu = 0.45

        print(f"\n{'='*60}")
        print(f"RemeshTetra: PID {pid} 리메시 시작")
        print(f"{'='*60}")

        max_retries = 3
        current_target_edge = target_edge
        for attempt in range(max_retries):
            success, bad_count = _remesh_single_part(
                part, pid, nodeManager, partManager,
                E, rho, nu,
                min_dt, current_target_edge, max_aspect, smooth_iter,
                preserve_shared, gmsh_path, objective
            )

            if success and bad_count == 0:
                break
            elif success and bad_count > 0 and attempt < max_retries - 1:
                if objective == "coarsen":
                    # coarsen은 AR 미달이어도 재시도 안 함 (더 줄이면 악화)
                    print(f"  → coarsen 모드: AR 미달 {bad_count}개 허용")
                    break
                # aspect ratio 미달 → target_edge 줄여서 재시도
                current_target_edge *= 0.7
                print(f"  → 재시도 {attempt+2}/{max_retries}: target_edge={current_target_edge:.4f}")
            else:
                break

        if success:
            total_remeshed += 1

    print(f"\nRemeshTetra: {total_remeshed}/{len(pids)} 파트 리메시 완료")


def _remesh_single_part(part, pid, nodeManager, partManager,
                        E, rho, nu,
                        min_dt, target_edge, max_aspect, smooth_iter,
                        preserve_shared, gmsh_path, objective="quality"):
    """단일 파트 리메시."""
    from KooCAEManager.KooElement import (
        compute_element_stable_dt, compute_element_min_edge_length,
        SolidElement
    )

    elemMan = part.elementManager

    # === Phase 1: 사전 분석 ===
    print(f"  [1/5] 사전 분석...")
    edge_lengths = []
    dts = []
    for eid, elem in elemMan.elements.items():
        el = compute_element_min_edge_length(elem)
        dt = compute_element_stable_dt(elem, E, rho, nu)
        if el < float('inf'):
            edge_lengths.append(el)
        if dt < float('inf'):
            dts.append(dt)

    if not edge_lengths:
        print(f"  PID {pid}: edge length 계산 실패")
        return False, 0

    avg_edge = np.mean(edge_lengths)
    min_edge = np.min(edge_lengths)
    max_edge = np.max(edge_lengths)
    old_min_dt = np.min(dts) if dts else float('inf')
    old_num_elems = len(elemMan.elements)

    # 기존 worst aspect ratio
    old_worst_ar = 0.0
    for eid, elem in elemMan.elements.items():
        nodes_e = [n for n in elem.nodes if n is not None]
        if len(nodes_e) < 4:
            continue
        coords_e = [np.array([n.x, n.y, n.z]) for n in nodes_e]
        unique_coords = []
        seen = set()
        for c in coords_e:
            key = (round(c[0], 8), round(c[1], 8), round(c[2], 8))
            if key not in seen:
                seen.add(key)
                unique_coords.append(c)
        if len(unique_coords) < 4:
            continue
        edges_e = []
        for i in range(len(unique_coords)):
            for j in range(i+1, len(unique_coords)):
                d = np.linalg.norm(unique_coords[i] - unique_coords[j])
                if d > 1e-30:
                    edges_e.append(d)
        if edges_e:
            ar = max(edges_e) / min(edges_e)
            old_worst_ar = max(old_worst_ar, ar)

    old_bad_ar_count = sum(1 for eid, elem in elemMan.elements.items()
        if len([n for n in elem.nodes if n is not None]) >= 4
        and (lambda ns: (lambda es: max(es)/min(es) if es else 0)(
            [np.linalg.norm(np.array([ns[i].x-ns[j].x, ns[i].y-ns[j].y, ns[i].z-ns[j].z]))
             for i in range(len(ns)) for j in range(i+1, len(ns))
             if np.linalg.norm(np.array([ns[i].x-ns[j].x, ns[i].y-ns[j].y, ns[i].z-ns[j].z])) > 1e-30]
        ) > max_aspect)([n for n in elem.nodes if n is not None]))

    print(f"    요소 수: {old_num_elems}")
    print(f"    Edge: min={min_edge:.4f}, avg={avg_edge:.4f}, max={max_edge:.4f}")
    print(f"    Min dt: {old_min_dt:.2E}")
    print(f"    Worst aspect ratio: {old_worst_ar:.2f}")
    print(f"    Aspect ratio > {max_aspect}: {old_bad_ar_count}/{old_num_elems} 요소")

    # min_dt 기반 L_min 계산
    factor = (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
    if factor <= 0:
        factor = 1.0
    c = math.sqrt(E * factor / rho)  # P-wave speed
    L_min = min_dt * c if min_dt > 0 else avg_edge * 0.1

    # 목표 요소 크기 결정 (objective 기반)
    if target_edge <= 0:
        if objective == "coarsen":
            target_edge = avg_edge * 2.0  # 기존 평균의 2배 → 요소 수 감소
        elif objective == "refine":
            target_edge = avg_edge * 0.5  # 기존 평균의 절반 → 요소 수 증가
        elif objective == "match_dt":
            target_edge = max(L_min * 1.5, avg_edge * 0.5) if min_dt > 0 else avg_edge
        else:  # quality
            target_edge = avg_edge  # 기존 평균 유지

    # L_min이 target_edge보다 작으면 L_min으로 제한
    if L_min <= 0:
        L_min = target_edge * 0.1

    print(f"    Objective: {objective}")
    print(f"    음속: {c:.1f}, L_min (dt 기반): {L_min:.4f}")
    print(f"    목표 요소 크기: {target_edge:.4f}")

    # === Phase 2: 공유 노드 수집 ===
    print(f"  [2/5] 공유 노드 수집...")
    part_nids = set()
    for eid, elem in elemMan.elements.items():
        for n in elem.nodes:
            if n is not None:
                part_nids.add(n.id)

    shared_nids = set()
    if preserve_shared:
        for other_pid, other_part in partManager.parts.items():
            if other_pid == pid:
                continue
            if not other_part.elementManager.elements:
                continue
            for eid, elem in other_part.elementManager.elements.items():
                for n in elem.nodes:
                    if n is not None and n.id in part_nids:
                        shared_nids.add(n.id)
        print(f"    공유 노드: {len(shared_nids)}개 (보존)")
    else:
        print(f"    공유 노드: 보존 안 함")

    # 공유 노드 좌표
    shared_node_coords = {}
    for nid in shared_nids:
        n = nodeManager.GetNode(nid)
        if n:
            shared_node_coords[nid] = (n.x, n.y, n.z)

    # === Phase 3: 외곽면 STL 추출 + gmsh 리메시 ===
    print(f"  [3/5] gmsh 리메시...")
    ext_segs = elemMan.GetExternalBoundary(False)
    if not ext_segs:
        print(f"  PID {pid}: 외곽면 추출 실패")
        return False, 0

    # 노드 좌표 수집
    part_nodes = {}
    for nid in part_nids:
        n = nodeManager.GetNode(nid)
        if n:
            part_nodes[nid] = (n.x, n.y, n.z)

    # STL 작성 + gmsh subprocess 호출
    tmpdir = tempfile.mkdtemp(prefix=f"remesh_P{pid}_")
    stl_path = os.path.join(tmpdir, "surface.stl")
    geo_path = os.path.join(tmpdir, "input.geo")
    msh_path = os.path.join(tmpdir, "output.msh")

    _write_stl(stl_path, ext_segs, part_nodes)

    _write_geo(geo_path, stl_path, msh_path,
               L_min, target_edge, smooth_iter,
               shared_node_coords if preserve_shared else {})

    cmd = f'{gmsh_path} -setnumber General.Verbosity 2 -setnumber Mesh.MshFileVersion 2.2 "{geo_path}" -3 -o "{msh_path}" -format msh2'
    print(f"    명령: {cmd}")
    ret = os.system(cmd)

    if ret != 0 or not os.path.exists(msh_path):
        print(f"  PID {pid}: gmsh 실행 실패 (exit={ret})")
        _cleanup(tmpdir)
        return False, 0

    # === Phase 4: 결과 교체 ===
    print(f"  [4/5] 결과 교체...")
    new_nodes, new_elements = _read_msh(msh_path)

    if not new_nodes or not new_elements:
        print(f"  PID {pid}: gmsh 결과 없음")
        _cleanup(tmpdir)
        return False, 0

    # 공유 노드 매핑
    nid_map = {}  # gmsh NID → 원본/새 NID
    if preserve_shared and shared_node_coords:
        new_coords = np.array([[new_nodes[nid][0], new_nodes[nid][1], new_nodes[nid][2]]
                               for nid in sorted(new_nodes.keys())])
        new_nid_list = sorted(new_nodes.keys())
        tree = KDTree(new_coords)

        for orig_nid, (ox, oy, oz) in shared_node_coords.items():
            dist, idx = tree.query([ox, oy, oz])
            if dist < 1e-4:  # tolerance
                gmsh_nid = new_nid_list[idx]
                nid_map[gmsh_nid] = orig_nid
            else:
                print(f"    ⚠️ 공유 노드 N{orig_nid} 매칭 실패 (dist={dist:.6f})")

    # 기존 노드/요소 제거
    old_eids = list(elemMan.elements.keys())
    for eid in old_eids:
        elem = elemMan.elements[eid]
        for n in elem.nodes:
            if n is not None and n.id not in shared_nids:
                if n.id in nodeManager.nodes:
                    del nodeManager.nodes[n.id]
        del elemMan.elements[eid]
    elemMan.maxID = 0

    # 새 노드 추가
    max_nid = max(nodeManager.nodes.keys()) if nodeManager.nodes else 0
    max_eid = 0
    for p in partManager.parts.values():
        for eid in p.elementManager.elements:
            max_eid = max(max_eid, eid)

    gmsh_to_real_nid = {}
    for gmsh_nid in sorted(new_nodes.keys()):
        x, y, z = new_nodes[gmsh_nid]
        if gmsh_nid in nid_map:
            # 공유 노드: 원본 NID 유지
            real_nid = nid_map[gmsh_nid]
            gmsh_to_real_nid[gmsh_nid] = real_nid
        else:
            # 새 노드
            max_nid += 1
            real_nid = max_nid
            node = nodeManager.CreateNode(x, y, z)
            node.id = real_nid
            nodeManager.nodes[real_nid] = node
            gmsh_to_real_nid[gmsh_nid] = real_nid

    # 새 요소 추가
    new_elem_count = 0
    for gmsh_eid, gnids in new_elements.items():
        max_eid += 1
        real_nids = [gmsh_to_real_nid[gn] for gn in gnids]
        real_nodes = [nodeManager.GetNode(rnid) for rnid in real_nids]
        if any(n is None for n in real_nodes):
            continue
        elem = SolidElement(max_eid, real_nodes)
        elemMan.elements[max_eid] = elem
        elemMan.maxID = max(elemMan.maxID, max_eid)
        new_elem_count += 1

    print(f"    노드: {len(part_nids)} → {len(gmsh_to_real_nid)} (공유 {len(nid_map)}개 보존)")
    print(f"    요소: {old_num_elems} → {new_elem_count}")

    # === Phase 5: 검증 ===
    print(f"  [5/5] 검증...")
    new_dts = []
    new_edges = []
    for eid, elem in elemMan.elements.items():
        dt = compute_element_stable_dt(elem, E, rho, nu)
        el = compute_element_min_edge_length(elem)
        if dt < float('inf'):
            new_dts.append(dt)
        if el < float('inf'):
            new_edges.append(el)

    new_min_dt = np.min(new_dts) if new_dts else float('inf')
    new_avg_edge = np.mean(new_edges) if new_edges else 0
    new_min_edge = np.min(new_edges) if new_edges else 0

    # aspect ratio 검증 (max_edge / min_edge per element)
    bad_aspect_count = 0
    new_worst_ar = 0.0
    for eid, elem in elemMan.elements.items():
        nodes_e = [n for n in elem.nodes if n is not None]
        if len(nodes_e) < 4:
            continue
        coords_e = [np.array([n.x, n.y, n.z]) for n in nodes_e]
        edges_e = []
        for i in range(len(coords_e)):
            for j in range(i+1, len(coords_e)):
                d = np.linalg.norm(coords_e[i] - coords_e[j])
                if d > 1e-30:
                    edges_e.append(d)
        if edges_e:
            ar = max(edges_e) / min(edges_e)
            new_worst_ar = max(new_worst_ar, ar)
            if ar > max_aspect:
                bad_aspect_count += 1

    print(f"    Edge: min={new_min_edge:.4f}, avg={new_avg_edge:.4f}")
    print(f"    Min dt: {old_min_dt:.2E} → {new_min_dt:.2E}")
    print(f"    Worst aspect ratio: {old_worst_ar:.2f} → {new_worst_ar:.2f}")
    print(f"    Aspect ratio > {max_aspect}: {bad_aspect_count}/{new_elem_count} 요소")

    # 전후 요약
    print(f"\n    --- 리메시 전후 비교 ---")
    print(f"    {'':>20} {'Before':>12} {'After':>12}")
    print(f"    {'요소 수':>20} {old_num_elems:>12} {new_elem_count:>12}")
    print(f"    {'Min edge':>20} {min_edge:>12.4f} {new_min_edge:>12.4f}")
    print(f"    {'Avg edge':>20} {avg_edge:>12.4f} {new_avg_edge:>12.4f}")
    print(f"    {'Min dt':>20} {old_min_dt:>12.2E} {new_min_dt:>12.2E}")
    print(f"    {'Worst AR':>20} {old_worst_ar:>12.2f} {new_worst_ar:>12.2f}")
    print(f"    {'AR > {0}'.format(max_aspect):>20} {old_bad_ar_count:>12} {bad_aspect_count:>12}")

    if min_dt > 0 and new_min_dt < min_dt:
        print(f"    ⚠️ 목표 min_dt({min_dt:.2E}) 미달!")
    if bad_aspect_count > 0:
        print(f"    ⚠️ 품질 미달 요소 {bad_aspect_count}개 존재")

    # 정리
    _cleanup(tmpdir)
    print(f"  PID {pid}: 리메시 완료 ✓")
    return True, bad_aspect_count


def _write_stl(stl_path, segments, node_coords):
    """외곽면 segment → STL 파일."""
    with open(stl_path, 'w') as f:
        f.write("solid surface\n")
        for seg in segments:
            unique_nids = []
            seen = set()
            for nid in seg:
                if nid not in seen:
                    unique_nids.append(nid)
                    seen.add(nid)

            if len(unique_nids) < 3:
                continue

            # 삼각형 분할
            coords = [node_coords.get(nid) for nid in unique_nids]
            if any(c is None for c in coords):
                continue

            # 첫 삼각형
            p0, p1, p2 = np.array(coords[0]), np.array(coords[1]), np.array(coords[2])
            normal = np.cross(p1 - p0, p2 - p0)
            norm = np.linalg.norm(normal)
            if norm > 1e-30:
                normal = normal / norm
            else:
                normal = np.array([0, 0, 1])

            f.write(f"  facet normal {normal[0]:.6e} {normal[1]:.6e} {normal[2]:.6e}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {coords[0][0]:.10e} {coords[0][1]:.10e} {coords[0][2]:.10e}\n")
            f.write(f"      vertex {coords[1][0]:.10e} {coords[1][1]:.10e} {coords[1][2]:.10e}\n")
            f.write(f"      vertex {coords[2][0]:.10e} {coords[2][1]:.10e} {coords[2][2]:.10e}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")

            # 사각형이면 두 번째 삼각형
            if len(unique_nids) == 4:
                p3 = np.array(coords[3])
                normal2 = np.cross(p2 - p0, p3 - p0)
                norm2 = np.linalg.norm(normal2)
                if norm2 > 1e-30:
                    normal2 = normal2 / norm2
                else:
                    normal2 = normal

                f.write(f"  facet normal {normal2[0]:.6e} {normal2[1]:.6e} {normal2[2]:.6e}\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {coords[0][0]:.10e} {coords[0][1]:.10e} {coords[0][2]:.10e}\n")
                f.write(f"      vertex {coords[2][0]:.10e} {coords[2][1]:.10e} {coords[2][2]:.10e}\n")
                f.write(f"      vertex {coords[3][0]:.10e} {coords[3][1]:.10e} {coords[3][2]:.10e}\n")
                f.write("    endloop\n")
                f.write("  endfacet\n")

        f.write("endsolid surface\n")


def _write_geo(geo_path, stl_path, msh_path,
               cl_min, cl_max, smooth_iter, fixed_points):
    """gmsh .geo 파일 생성."""
    with open(geo_path, 'w') as f:
        f.write("// Auto-generated by KooTetraRemesher\n")
        f.write(f'Merge "{stl_path}";\n')
        f.write("\n")

        # 면 분류 (feature edge 보존)
        f.write("ClassifySurfaces{40 * Pi/180, 1, 1};\n")
        f.write("CreateGeometry;\n")
        f.write("\n")

        # 볼륨 생성
        f.write("Surface Loop(1) = Surface{:};\n")
        f.write("Volume(1) = {1};\n")
        f.write("\n")

        # 메시 옵션
        f.write(f"Mesh.CharacteristicLengthMin = {cl_min:.6e};\n")
        f.write(f"Mesh.CharacteristicLengthMax = {cl_max:.6e};\n")
        f.write("Mesh.Algorithm3D = 10;  // HXT\n")
        f.write("Mesh.OptimizeNetgen = 1;\n")
        f.write("Mesh.Optimize = 1;\n")
        f.write(f"Mesh.Smoothing = {smooth_iter};\n")
        f.write("Mesh.ElementOrder = 1;  // Linear\n")
        f.write("Mesh.QualityType = 2;  // SICN (Signed Inverse Condition Number)\n")
        f.write("Mesh.OptimizeThreshold = 0.3;  // 품질 0.3 이하 요소 최적화 대상\n")
        f.write("Mesh.AnisoMax = 3.0;  // 최대 이방성 비율 제한 → 납작한 요소 방지\n")
        f.write("\n")

        # 고정점 (공유 노드)
        if fixed_points:
            f.write("// Fixed points (shared nodes)\n")
            for i, (nid, (x, y, z)) in enumerate(fixed_points.items()):
                pt_id = 10000 + i
                f.write(f"Point({pt_id}) = {{{x:.10e}, {y:.10e}, {z:.10e}, {cl_max:.6e}}};\n")
            f.write("Point{")
            f.write(",".join(str(10000 + i) for i in range(len(fixed_points))))
            f.write("} In Volume{1};\n")


def _read_msh(msh_path):
    """gmsh .msh (v2) 파일 읽기. 노드 + 사면체 요소만 추출."""
    nodes = {}       # nid → (x, y, z)
    elements = {}    # eid → [n1, n2, n3, n4]

    with open(msh_path, 'r') as f:
        line = f.readline()
        while line:
            line = line.strip()

            if line == "$Nodes":
                num_nodes = int(f.readline().strip())
                for _ in range(num_nodes):
                    parts = f.readline().strip().split()
                    nid = int(parts[0])
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    nodes[nid] = (x, y, z)

            elif line == "$Elements":
                num_elems = int(f.readline().strip())
                for _ in range(num_elems):
                    parts = f.readline().strip().split()
                    eid = int(parts[0])
                    etype = int(parts[1])
                    ntags = int(parts[2])
                    nid_start = 3 + ntags

                    if etype == 4:  # 4-node tetrahedron
                        n1 = int(parts[nid_start])
                        n2 = int(parts[nid_start + 1])
                        n3 = int(parts[nid_start + 2])
                        n4 = int(parts[nid_start + 3])
                        elements[eid] = [n1, n2, n3, n4]

            line = f.readline()

    return nodes, elements


def _cleanup(tmpdir):
    """임시 디렉토리 정리."""
    import shutil
    try:
        shutil.rmtree(tmpdir)
    except Exception:
        pass
