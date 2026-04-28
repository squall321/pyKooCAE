#!/usr/bin/env python3
"""
Tied Segment 제외 검증 스크립트

RobustContact_SS 생성 시 Tied 인터페이스 segment가 올바르게 제외되는지 검증.

사용법:
    python verify_tied_exclusion.py <model.k>

출력:
    1. 모델 내 Tied 접촉 리스트
    2. 파트별 외부 segment 수
    3. Tied 인터페이스 segment 감지 결과 (CID별)
    4. 제외 전/후 segment 수 비교
    5. 제외된 segment 샘플 (노드 ID + 좌표)
"""

import sys
import os
import math
import numpy as np

# KooCAEManager 경로 추가
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
sys.path.insert(0, os.path.join(PROJECT_ROOT, "occProject", "Generators"))

from KooCAEManager.KooMeshImporter import KooMeshImporter
from KooCAEManager.KooElement import (
    compute_segment_normal, compute_segment_center, are_segments_facing,
    FaceElement, SolidElement
)
from scipy.spatial import KDTree


def verify_tied_exclusion(model_path, tolerance=0.1, normal_angle_limit=30.0):
    """Tied segment 제외 과정을 단계별로 검증."""

    print("=" * 80)
    print("Tied Segment 제외 검증")
    print("=" * 80)
    print(f"모델: {model_path}")
    print(f"Tolerance: {tolerance} mm")
    print(f"Normal angle limit: {normal_angle_limit} deg")
    print()

    # 1. 모델 로드
    print("[1/5] 모델 로딩 중...")
    importer = KooMeshImporter()
    importer.ImportDynaKeyword(model_path)
    print(f"  파트: {len(importer.partManager.parts)}개")
    print(f"  노드: {len(importer.nodeManager.nodes)}개")
    print()

    # 2. Tied 접촉 리스트
    print("[2/5] Tied 접촉 리스트")
    print("-" * 80)
    contactManager = importer.contactManager
    nodeMan = importer.nodeManager
    tied_contacts = []
    for cid, contact in contactManager.contacts.items():
        ctype = type(contact).__name__
        if 'Tied' in ctype:
            tied_contacts.append((cid, contact, ctype))
            ssid = contact.SSID
            msid = contact.MSID
            sstyp = contact.SSTYP
            mstyp = contact.MSTYP
            print(f"  CID={cid:>6} | {ctype:<50} | SSID={ssid} (TYP={sstyp}) MSID={msid} (TYP={mstyp})")

    if not tied_contacts:
        print("  Tied 접촉 없음")
        return

    print(f"\n  총 {len(tied_contacts)}개 Tied 접촉")
    print()

    # 3. 파트별 외부 segment 수집
    print("[3/5] 파트별 외부 segment 수집")
    print("-" * 80)

    def _get_part_segments(part):
        elems = part.elementManager.elements
        if not elems:
            return []
        first_elem = next(iter(elems.values()))
        if isinstance(first_elem, FaceElement):
            segs = []
            for eid, elem in elems.items():
                nids = [n.id for n in elem.nodes if n is not None]
                if len(nids) >= 3:
                    segs.append(nids)
            return segs
        else:
            return [s for s in part.elementManager.GetExternalBoundary(False) if len(set(s)) >= 3]

    all_segments = []
    part_seg_counts = {}
    for pid, p in importer.partManager.parts.items():
        if not p.elementManager.elements:
            continue
        segs = _get_part_segments(p)
        part_seg_counts[pid] = len(segs)
        all_segments.extend(segs)

    # 상위 10개 파트 출력
    sorted_parts = sorted(part_seg_counts.items(), key=lambda x: -x[1])[:10]
    for pid, cnt in sorted_parts:
        pname = getattr(importer.partManager.parts[pid], 'name', '').strip()
        print(f"  PID={pid:>8} | {cnt:>6} segments | {pname}")
    print(f"\n  전체 외부 segment: {len(all_segments)}개 ({len(part_seg_counts)}개 파트)")
    print()

    # 4. Tied 인터페이스 segment 감지
    print("[4/5] Tied 인터페이스 segment 감지 (CID별)")
    print("-" * 80)

    # 파트별 segment 캐시 (center + normal + KD-tree)
    _bound_cache = {}

    def _get_part_surface(pid):
        if pid in _bound_cache:
            return _bound_cache[pid]
        p = importer.partManager.parts.get(pid)
        if p is None or not p.elementManager.elements:
            _bound_cache[pid] = ([], [], [], None)
            return _bound_cache[pid]
        first_elem = next(iter(p.elementManager.elements.values()))
        if isinstance(first_elem, FaceElement):
            segs = []
            for eid, elem in p.elementManager.elements.items():
                nids = [n.id for n in elem.nodes if n is not None]
                if len(nids) >= 3:
                    segs.append(nids)
        else:
            segs = [s for s in p.elementManager.GetExternalBoundary(False) if len(set(s)) >= 3]
        centers, normals, valid_segs = [], [], []
        for seg in segs:
            c = compute_segment_center(seg, nodeMan)
            n = compute_segment_normal(seg, nodeMan)
            if c is not None and n is not None:
                centers.append(c)
                normals.append(n)
                valid_segs.append(seg)
        tree = KDTree(centers) if centers else None
        _bound_cache[pid] = (valid_segs, centers, normals, tree)
        return _bound_cache[pid]

    tied_interface_segments = set()
    per_cid_excluded = {}

    for cid, contact, ctype in tied_contacts:
        cid_segments = set()

        if contact.SSTYP == 3 and contact.MSTYP == 3:
            # Part-to-Part
            pidA, pidB = contact.SSID, contact.MSID
            segsA, centersA, normalsA, treeA = _get_part_surface(pidA)
            segsB, centersB, normalsB, treeB = _get_part_surface(pidB)

            if treeB and centersA:
                for i, seg in enumerate(segsA):
                    dists, idxs = treeB.query(centersA[i], k=1)
                    if dists < tolerance:
                        j = int(idxs)
                        if are_segments_facing(normalsA[i], normalsB[j], normal_angle_limit):
                            cid_segments.add(frozenset(seg))
                            cid_segments.add(frozenset(segsB[j]))

            if treeA and centersB:
                for i, seg in enumerate(segsB):
                    dists, idxs = treeA.query(centersB[i], k=1)
                    if dists < tolerance:
                        j = int(idxs)
                        if are_segments_facing(normalsB[i], normalsA[j], normal_angle_limit):
                            cid_segments.add(frozenset(seg))
                            cid_segments.add(frozenset(segsA[j]))

        elif contact.SSTYP == 0 and contact.MSTYP == 0:
            # Segment Set 기반
            segSetMan = importer.segmentSetManager
            ssidA = contact.SSID
            ssidB = contact.MSID
            if ssidA in segSetMan.segmentSetList:
                for seg in segSetMan.segmentSetList[ssidA].segments:
                    cid_segments.add(frozenset(seg))
            if ssidB in segSetMan.segmentSetList:
                for seg in segSetMan.segmentSetList[ssidB].segments:
                    cid_segments.add(frozenset(seg))

        elif contact.SSTYP == 3 and contact.MSTYP == 0:
            # Part + Segment Set 혼합
            pidA = contact.SSID
            segsA, centersA, normalsA, treeA = _get_part_surface(pidA)
            segSetMan = importer.segmentSetManager
            if contact.MSID in segSetMan.segmentSetList:
                msSegs = segSetMan.segmentSetList[contact.MSID].segments
                for seg in msSegs:
                    cid_segments.add(frozenset(seg))
                    c = compute_segment_center(list(seg), nodeMan)
                    if c is not None and treeA:
                        nM = compute_segment_normal(list(seg), nodeMan)
                        dists, idxs = treeA.query(c, k=1)
                        if dists < tolerance:
                            j = int(idxs)
                            if are_segments_facing(nM, normalsA[j], normal_angle_limit):
                                cid_segments.add(frozenset(segsA[j]))

        elif contact.SSTYP == 0 and contact.MSTYP == 3:
            pidB = contact.MSID
            segsB, centersB, normalsB, treeB = _get_part_surface(pidB)
            segSetMan = importer.segmentSetManager
            if contact.SSID in segSetMan.segmentSetList:
                ssSegs = segSetMan.segmentSetList[contact.SSID].segments
                for seg in ssSegs:
                    cid_segments.add(frozenset(seg))
                    c = compute_segment_center(list(seg), nodeMan)
                    if c is not None and treeB:
                        nS = compute_segment_normal(list(seg), nodeMan)
                        dists, idxs = treeB.query(c, k=1)
                        if dists < tolerance:
                            j = int(idxs)
                            if are_segments_facing(nS, normalsB[j], normal_angle_limit):
                                cid_segments.add(frozenset(segsB[j]))

        tied_interface_segments.update(cid_segments)
        per_cid_excluded[cid] = len(cid_segments)
        print(f"  CID={cid:>6} | {len(cid_segments):>6} segments 감지 | SSTYP={contact.SSTYP} MSTYP={contact.MSTYP}")

    print(f"\n  총 Tied 인터페이스 segment: {len(tied_interface_segments)}개")
    print()

    # 5. 제외 결과
    print("[5/5] 제외 결과")
    print("-" * 80)

    # 중복 제거
    seen_segs = set()
    filtered = []
    n_dup = 0
    for seg in all_segments:
        seg_key = frozenset(seg)
        if seg_key in seen_segs:
            n_dup += 1
            continue
        seen_segs.add(seg_key)
        if seg_key not in tied_interface_segments:
            filtered.append(seg)

    excluded_count = len(seen_segs) - len(filtered)

    print(f"  전체 외부 segment:     {len(all_segments)}")
    print(f"  파트 간 중복 제거:     {n_dup}")
    print(f"  고유 segment:          {len(seen_segs)}")
    print(f"  Tied 제외:             {excluded_count}")
    print(f"  최종 RobustContact_SS: {len(filtered)}")
    print()

    # 비율
    if len(seen_segs) > 0:
        ratio = excluded_count / len(seen_segs) * 100
        print(f"  제외 비율: {ratio:.1f}%")
    print()

    # 제외된 segment 샘플 (최대 5개)
    if excluded_count > 0:
        print("  제외된 segment 샘플:")
        sample_count = 0
        for seg in all_segments:
            if frozenset(seg) in tied_interface_segments and sample_count < 5:
                coords_str = []
                for nid in seg:
                    n = nodeMan.GetNode(nid)
                    if n:
                        coords_str.append(f"N{nid}({n.x:.1f},{n.y:.1f},{n.z:.1f})")
                print(f"    {coords_str}")
                sample_count += 1

    # 검증: 제외 0이면 경고
    if excluded_count == 0 and len(tied_contacts) > 0:
        print()
        print("  ⚠️  WARNING: Tied 접촉이 있지만 제외된 segment가 0개!")
        print("     가능한 원인:")
        print("     - tolerance 값이 너무 작음 (현재: {tolerance}mm)")
        print("     - Tied 접촉의 SSTYP/MSTYP 조합이 지원되지 않음")
        print("     - 파트 간 간격이 tolerance보다 큼")

    print()
    print("=" * 80)
    print("검증 완료")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_tied_exclusion.py <model.k> [tolerance] [angle_limit]")
        sys.exit(1)

    model_path = sys.argv[1]
    tolerance = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
    angle_limit = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0

    verify_tied_exclusion(model_path, tolerance, angle_limit)
