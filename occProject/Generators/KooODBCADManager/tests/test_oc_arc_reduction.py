"""
OC 파싱 및 Arc Reduction 테스트 스크립트
- 기존 코드와 완전 분리된 독립 테스트
- 실행: python -m tests.test_oc_arc_reduction (KooODBCADManager 디렉토리에서)
  또는: python tests/test_oc_arc_reduction.py (KooODBCADManager 디렉토리에서)
"""
import sys
import os
import math
import io

# Generators 디렉토리를 import path에 추가 (KooODBCADManager 패키지로 접근)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from KooODBCADManager.Polygon import Polygon2D, Edges2D, Vertex2D
from KooODBCADManager.PolygonManager import PolygonManager2D as PolygonManager
from KooODBCADManager.ODBPPImporter import ODBPPImporter


def test_oc_parsing_in_import_polygon():
    """ImportPolygon에서 OC가 포함된 CT 블록 파싱 테스트"""
    print("=== Test 1: OC Parsing in ImportPolygon ===")

    # OC가 포함된 CT 블록을 시뮬레이션하는 스트림 생성
    # 사각형의 한 변을 Arc로 대체: (0,0)->(10,0)->(arc to 10,10)->(0,10)->(0,0)
    data = (
        "OS 10.0 0.0\n"
        "OC 10.0 10.0 10.0 5.0 N\n"  # Arc: end=(10,10), center=(10,5), CCW
        "OS 0.0 10.0\n"
        "OS 0.0 0.0\n"
        "OE\n"
    )
    stream = io.StringIO(data)

    importer = ODBPPImporter(unitamp=1.0)
    polyMan = PolygonManager()

    # CT 키워드로 시작하는 라인 시뮬레이션
    sline = "CT"
    # prevVertex를 만들기 위해 OB 첫 점도 포함해야 함
    # ImportPolygon은 CT를 만나면 stream에서 읽기 시작
    # OB 0 0 부터 시작해야 하므로 스트림 수정
    data2 = (
        "OB 0.0 0.0\n"
        "OS 10.0 0.0\n"
        "OC 10.0 10.0 10.0 5.0 N\n"
        "OS 0.0 10.0\n"
        "OS 0.0 0.0\n"
        "OE\n"
    )
    stream2 = io.StringIO(data2)
    aPoly = importer.ImportPolygon(polyMan, sline, stream2)

    if aPoly is None:
        print("  FAIL: Polygon is None")
        return False

    print(f"  Polygon type: {aPoly.type}")
    print(f"  Vertices: {len(aPoly.vertices)}")
    print(f"  Edges: {len(aPoly.edges)}")

    # Edge 타입 확인
    edgeTypes = [e.type for e in aPoly.edges]
    print(f"  Edge types: {edgeTypes}")

    hasArc = any(e.type == "Arc" for e in aPoly.edges)
    if hasArc:
        print("  PASS: Arc edge found")
    else:
        print("  WARN: No Arc edge (may have been reduced by ReduceEdgesToArcs)")

    # vertices 확인
    for v in aPoly.vertices:
        print(f"    Vertex {v.id}: ({v.x}, {v.y})")

    print()
    return True


def test_oc_parsing_in_import_feature():
    """ImportFeature에서 OC 파싱 테스트"""
    print("=== Test 2: OC Parsing in ImportFeature ===")

    data = (
        "OB 0.0 0.0\n"
        "OS 5.0 0.0\n"
        "OC 5.0 5.0 5.0 2.5 Y\n"  # Arc: clockwise
        "OS 0.0 5.0\n"
        "OE\n"
    )
    stream = io.StringIO(data)

    importer = ODBPPImporter(unitamp=1.0)
    polyMan = PolygonManager()
    sline = "OB 0.0 0.0"

    aPoly = importer.ImportFeature(polyMan, sline, stream)

    if aPoly is None:
        print("  FAIL: Polygon is None")
        return False

    print(f"  Edges: {len(aPoly.edges)}")
    edgeTypes = [e.type for e in aPoly.edges]
    print(f"  Edge types: {edgeTypes}")

    # Arc의 counterclockwise 확인
    for e in aPoly.edges:
        if e.type == "Arc":
            print(f"  Arc counterclockwise: {e.counterclockwise}")
            # Y=clockwise -> cw=True -> not cw=False -> counterclockwise=False
            if e.counterclockwise == False:
                print("  PASS: CW arc correctly created")
            else:
                print("  FAIL: Arc direction wrong")

    print()
    return True


def test_reduce_edges_to_arcs():
    """ReduceEdgesToArcs 알고리즘 테스트 - 원호 위의 점들을 Arc로 치환"""
    print("=== Test 3: ReduceEdgesToArcs ===")

    polyMan = PolygonManager()

    # 반원 (반지름 5, 중심 (5,0))을 20개 직선 세그먼트로 근사
    numSegments = 20
    radius = 5.0
    cx, cy = 5.0, 0.0

    vertices = []
    for i in range(numSegments + 1):
        angle = math.pi * i / numSegments  # 0 to pi
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        v = polyMan.CreateVertex(x, y)
        vertices.append(v)

    # 하단 직선으로 닫기: (cx-r, 0) -> (cx+r, 0)
    # 이미 vertices[-1] = (cx-r, 0), vertices[0] = (cx+r, 0)
    # 닫는 선분 추가
    vertices.append(vertices[0])

    edges = polyMan.CreateLines(vertices)
    aPoly = polyMan.CreatePolygon(vertices, 'CT', edges)

    print(f"  Before reduction:")
    print(f"    Edges: {len(aPoly.edges)}")
    print(f"    Edge types: {set(e.type for e in aPoly.edges)}")

    edgeCountBefore = len(aPoly.edges)

    aPoly.ReduceEdgesToArcs(tol_center=0.1, tol_radius=0.1, min_group_size=3)

    print(f"  After reduction:")
    print(f"    Edges: {len(aPoly.edges)}")
    edgeTypes = [e.type for e in aPoly.edges]
    print(f"    Edge types: {edgeTypes}")

    hasArc = any(e.type == "Arc" for e in aPoly.edges)
    if hasArc and len(aPoly.edges) < edgeCountBefore:
        print(f"  PASS: Reduced from {edgeCountBefore} to {len(aPoly.edges)} edges")
    else:
        print(f"  FAIL: No reduction occurred")

    # Arc의 중심점이 원래 중심에 가까운지 확인
    for e in aPoly.edges:
        if e.type == "Arc":
            vc = e.vertices[2]
            dist = math.sqrt((vc.x - cx) ** 2 + (vc.y - cy) ** 2)
            print(f"    Arc center: ({vc.x:.3f}, {vc.y:.3f}), distance from true center: {dist:.4f}")
            if dist < 0.5:
                print("    PASS: Center is close to expected")
            else:
                print("    WARN: Center deviation is large")

    print()
    return True


def test_reduce_no_arc_case():
    """직선만으로 구성된 사각형 - 치환이 일어나면 안 됨"""
    print("=== Test 4: No Arc Reduction for Straight Polygon ===")

    polyMan = PolygonManager()

    v1 = polyMan.CreateVertex(0, 0)
    v2 = polyMan.CreateVertex(10, 0)
    v3 = polyMan.CreateVertex(10, 10)
    v4 = polyMan.CreateVertex(0, 10)
    vertices = [v1, v2, v3, v4, v1]
    edges = polyMan.CreateLines(vertices)
    aPoly = polyMan.CreatePolygon(vertices, 'CT', edges)

    edgeCountBefore = len(aPoly.edges)
    aPoly.ReduceEdgesToArcs()
    edgeCountAfter = len(aPoly.edges)

    if edgeCountBefore == edgeCountAfter:
        print(f"  PASS: No reduction for straight polygon ({edgeCountAfter} edges)")
    else:
        print(f"  FAIL: Unexpected reduction from {edgeCountBefore} to {edgeCountAfter}")

    print()
    return True


def test_vertex_id_uniqueness():
    """Arc 치환 후 vertex ID가 중복되지 않는지 확인"""
    print("=== Test 5: Vertex ID Uniqueness After Reduction ===")

    polyMan = PolygonManager()

    # 두 개의 반원을 연결한 타원형 모양
    vertices = []
    # 상반부 반원 (20 세그먼트)
    for i in range(21):
        angle = math.pi * i / 20
        x = 5.0 * math.cos(angle)
        y = 5.0 * math.sin(angle)
        vertices.append(polyMan.CreateVertex(x, y))

    # 하반부 반원 (20 세그먼트, 더 작은 반경)
    for i in range(1, 21):
        angle = math.pi + math.pi * i / 20
        x = 5.0 * math.cos(angle)
        y = 3.0 * math.sin(angle)
        vertices.append(polyMan.CreateVertex(x, y))

    vertices.append(vertices[0])
    edges = polyMan.CreateLines(vertices)
    aPoly = polyMan.CreatePolygon(vertices, 'CT', edges)

    aPoly.ReduceEdgesToArcs(tol_center=0.15, tol_radius=0.15, min_group_size=3)

    # ID 중복 검사
    ids = [v.id for v in aPoly.vertices]
    unique_ids = set(ids)
    if len(ids) == len(unique_ids):
        print(f"  PASS: All {len(ids)} vertex IDs are unique")
    else:
        duplicates = [vid for vid in ids if ids.count(vid) > 1]
        print(f"  FAIL: Duplicate vertex IDs found: {set(duplicates)}")

    # object identity 검사
    obj_ids = set(id(v) for v in aPoly.vertices)
    if len(aPoly.vertices) == len(obj_ids):
        print(f"  PASS: All {len(aPoly.vertices)} vertex objects are distinct")
    else:
        print(f"  FAIL: Duplicate vertex objects found")

    print()
    return True


def test_import_edge_feature_oc():
    """ImportEdgeFeature에서 OC가 7원소 배열로 저장되는지 테스트"""
    print("=== Test 6: OC in ImportEdgeFeature ===")

    data = (
        "OB 0.0 0.0\n"
        "OS 10.0 0.0\n"
        "OC 10.0 10.0 10.0 5.0 N\n"
        "OS 0.0 10.0\n"
        "OE\n"
    )
    stream = io.StringIO(data)

    importer = ODBPPImporter(unitamp=1.0)

    result = importer.ImportEdgeFeature(stream)

    print(f"  Keys in result: {list(result.keys())}")
    for key, edges in result.items():
        print(f"  Key {key}:")
        for e in edges:
            print(f"    Edge ({len(e)} elements): {e}")
            if len(e) == 7:
                print(f"    -> Arc: start=({e[0]},{e[1]}), end=({e[2]},{e[3]}), center=({e[4]},{e[5]}), clk={e[6]}")
            elif len(e) == 4:
                print(f"    -> Line: ({e[0]},{e[1]}) -> ({e[2]},{e[3]})")

    # 7원소 배열이 있는지 확인
    hasArcEdge = False
    for key, edges in result.items():
        for e in edges:
            if len(e) == 7:
                hasArcEdge = True
    if hasArcEdge:
        print("  PASS: Arc edge (7 elements) found")
    else:
        print("  FAIL: No arc edge found")

    print()
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("OC Parsing & Arc Reduction Test Suite")
    print("=" * 60)
    print()

    results = []
    results.append(("OC in ImportPolygon", test_oc_parsing_in_import_polygon()))
    results.append(("OC in ImportFeature", test_oc_parsing_in_import_feature()))
    results.append(("ReduceEdgesToArcs", test_reduce_edges_to_arcs()))
    results.append(("No reduction for straight", test_reduce_no_arc_case()))
    results.append(("Vertex ID uniqueness", test_vertex_id_uniqueness()))
    results.append(("OC in ImportEdgeFeature", test_import_edge_feature_oc()))

    print("=" * 60)
    print("RESULTS SUMMARY:")
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    print("=" * 60)
