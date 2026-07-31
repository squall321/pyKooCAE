import numpy as np 
from pyDOE import lhs
from matplotlib.path import Path
from typing import Dict, Tuple, List, Iterable
BoundBox = Tuple[float, float, float, float, float, float]  # (minX,maxX,minY,maxY,minZ,maxZ)

def parse_whole(curString, chunkList):
    chunk_size = len(chunkList)
    chunks = []

    start = 0
    for i in range(0,chunk_size):
        end = start + chunkList[i]
        chunks.append(curString[start:end])            
        start = end

    for i in range(0,chunk_size):
        if '\n' in chunks[i]:
            chunks[i] = chunks[i].replace('\n','')
        
    return chunks    

def KooDynaFloat(value, default = 0.0):
    reValue = default
    if value.strip() == "":
        reValue = default
    elif not value.replace("-","").replace(".","").replace("E","").replace("e","").replace("+","").strip().isdigit():
        reValue = default
    else:
        reValue = float(value)
    return reValue

def KooDynaInt(value, default = 0):
    reValue = default
    if value.strip() == "":
        reValue = default
    # check it can be changed into integer include minus sign
    elif not value.replace("-","").strip().isdigit():
        # Altair 등 일부 프리프로세서가 정수 필드를 '2.0' 처럼 실수로 기록한다.
        # 기존에는 여기서 조용히 default(0)로 떨어져 SSID/SSTYP/SBOPT 등이 0 이 되는
        # 무언 손상이 있었다 → 정수값을 가진 실수 표기는 정수로 복원한다.
        try:
            reValue = int(round(float(value)))
        except (TypeError, ValueError, OverflowError):
            reValue = default
    else:
        reValue = int(value)
    return reValue

def KooDynaString(value, default = ""):
    reValue = default
    if value.strip() == "":
        reValue = default
    else:
        reValue = value
    return reValue


         
    
def project_point_to_plane(point, plane_point, plane_normal):
    # 직선 투영: p_proj = p - ((p - p0)·n) * n / ||n||^2
    v = point - plane_point
    n = plane_normal / np.linalg.norm(plane_normal)
    dist = np.dot(v, n)
    return point - dist * n

def build_2d_basis(polygon_3d, direction):
    # 평면 위 직교 좌표계 정의
    v1 = polygon_3d[1] - polygon_3d[0]
    v1 /= np.linalg.norm(v1)
    v2 = np.cross(direction, v1)
    v2 /= np.linalg.norm(v2)
    return v1, v2

def to_2d_coords(points_3d, origin_3d, v1, v2):
    return np.array([[np.dot(p - origin_3d, v1), np.dot(p - origin_3d, v2)] for p in points_3d])


def point_in_quad(p, quad):
    # 2D 폴리곤 내부 점 판정 (사각형 quad는 2D 평면상 점 4개)
    path = Path(quad)
    return path.contains_point(p)

def is_inside_prism(point, quad_3d, direction):
    # 평면 정의
    plane_point = quad_3d[0]
    plane_normal = direction

    # 점과 사각형 꼭짓점들을 평면에 투영
    projected_point = project_point_to_plane(point, plane_point, plane_normal)
    projected_quad = np.array([project_point_to_plane(p, plane_point, plane_normal) for p in quad_3d])

    # 투영된 좌표계를 평면 위에서 2D로 정렬 (기준 벡터 설정)
    v1 = projected_quad[1] - projected_quad[0]
    v1 /= np.linalg.norm(v1)
    v2 = np.cross(direction, v1)
    v2 /= np.linalg.norm(v2)

    def to_2d(p):
        return [np.dot(p - projected_quad[0], v1), np.dot(p - projected_quad[0], v2)]

    quad_2d = [to_2d(p) for p in projected_quad]
    point_2d = to_2d(projected_point)

    return point_in_quad(point_2d, quad_2d)

def are_points_inside_prism(points, polygon_3d, direction):
    plane_point = polygon_3d[0]
    normal = direction

    projected_polygon = np.array([project_point_to_plane(p, plane_point, normal) for p in polygon_3d])
    projected_points = np.array([project_point_to_plane(p, plane_point, normal) for p in points])

    v1, v2 = build_2d_basis(projected_polygon, normal)

    polygon_2d = to_2d_coords(projected_polygon, projected_polygon[0], v1, v2)
    points_2d = to_2d_coords(projected_points, projected_polygon[0], v1, v2)

    path = Path(polygon_2d)
    return path.contains_points(points_2d)

def distance_from_multiple_prism_edge(points, polygon_3ds, directions):
    distances = np.zeros(len(points))
    for polygon_3d, direction in zip(polygon_3ds, directions):
        dists = distance_from_prism_edge(points, polygon_3d, direction)
        distances = np.minimum(distances, dists)
    return distances

def elliptical_distance_from_box(points, polygon3D, xDir, yDir, boxLength, effectRadius):
    # Polygon center
    center = np.mean(polygon3D, axis=0)

    v1 = np.array(xDir)
    v2 = np.array(yDir)

    # Project points to local 2D frame
    local_points = []
    for p in points:
        vec = p - center
        local_x = np.dot(vec, v1)
        local_y = np.dot(vec, v2)
        local_points.append([local_x, local_y])
    local_points = np.array(local_points)

    # Normalize distances to [0,1] ellipse
    norm_x = local_points[:,0] / (boxLength[0]/2.0)
    norm_y = local_points[:,1] / (boxLength[1]/2.0)

    norm_distance = np.sqrt(norm_x**2 + norm_y**2)
    # scale to effectRadius
    distances = norm_distance * effectRadius
    return distances

def distance_from_prism_edge(points, polygon_3d, direction):
    plane_point = polygon_3d[0]
    normal = direction

    projected_polygon = np.array([project_point_to_plane(p, plane_point, normal) for p in polygon_3d])
    projected_points = np.array([project_point_to_plane(p, plane_point, normal) for p in points])

    v1, v2 = build_2d_basis(projected_polygon, normal)

    polygon_2d = to_2d_coords(projected_polygon, projected_polygon[0], v1, v2)
    points_2d = to_2d_coords(projected_points, projected_polygon[0], v1, v2)

    path = Path(polygon_2d)
    inside_mask = path.contains_points(points_2d)

    # 외곽선에서 거리 계산
    distances = []
    for i, p in enumerate(points_2d):
        if inside_mask[i]:
            distances.append(0.0)
        else:
            d_min = float("inf")
            for j in range(len(polygon_2d)):
                a = polygon_2d[j]
                b = polygon_2d[(j+1) % len(polygon_2d)]
                ab = b - a
                t = np.dot(p - a, ab) / np.dot(ab, ab)
                t = np.clip(t, 0, 1)
                proj = a + t * ab
                dist = np.linalg.norm(p - proj)
                d_min = min(d_min, dist)
            distances.append(d_min)
    return np.array(distances)

def sample_lhs_1d(n_samples, x_range=(-1.0, 1.0)):
    # 1D LHS: shape = (n_samples, 1)
    unit_samples = lhs(1, samples=n_samples)
    
    # 범위 조정
    x_samples = x_range[0] + unit_samples[:, 0] * (x_range[1] - x_range[0])
    
    return x_samples.reshape(-1, 1)

def sample_lhs_2d(n_samples, x_range=(-1.0, 1.0), y_range=(-1.0, 1.0)):
    # 2D LHS: shape = (n_samples, 2)
    unit_samples = lhs(2, samples=n_samples)
    
    # 범위 조정
    x_samples = x_range[0] + unit_samples[:, 0] * (x_range[1] - x_range[0])
    y_samples = y_range[0] + unit_samples[:, 1] * (y_range[1] - y_range[0])
    
    return np.column_stack((x_samples, y_samples))
    
    
def sample_lhs_3d(n_samples, x_range=(-1.0, 1.0), y_range=(-1.0, 1.0), z_range=(-1.0, 1.0)):
    # 3D LHS: shape = (n_samples, 3)
    unit_samples = lhs(3, samples=n_samples)
    
    # 범위 조정
    x_samples = x_range[0] + unit_samples[:, 0] * (x_range[1] - x_range[0])
    y_samples = y_range[0] + unit_samples[:, 1] * (y_range[1] - y_range[0])
    z_samples = z_range[0] + unit_samples[:, 2] * (z_range[1] - z_range[0])
    
    return np.column_stack((x_samples, y_samples, z_samples))
    
def find_perpendicular_component(v1, nz):
    v1 = np.array(v1)
    v1 = v1 / np.linalg.norm(v1)
    nz = np.array(nz)
    
    # v1과 평행한 성분
    proj = np.dot(nz, v1) / np.dot(v1, v1) * v1
    
    # 수직한 성분
    perp = nz - proj
    
    if np.linalg.norm(perp) < 1e-8:
        # nz가 v1과 거의 평행한 경우
        # v1과 수직한 아무 벡터 생성
        if abs(v1[0]) > 1e-8 or abs(v1[1]) > 1e-8:
            arbitrary = np.array([-v1[1], v1[0], 0.0])
        else:
            arbitrary = np.array([1.0, 0.0, 0.0])
        return arbitrary / np.linalg.norm(arbitrary)
    else:
        return perp / np.linalg.norm(perp)        
    
def rotation_matrix_from_z(z_target):
    v1 = np.array([0, 0, 1])
    v2 = np.array(z_target) / np.linalg.norm(z_target)
    u = np.cross(v1, v2)
    c = np.dot(v1, v2)
    s = np.linalg.norm(u)
    
    if s < 1e-8:
        return np.eye(3) if c > 0 else -np.eye(3)
    
    u /= s  # normalize rotation axis
    ux, uy, uz = u
    K = np.array([
        [0, -uz, uy],
        [uz, 0, -ux],
        [-uy, ux, 0]
    ])
    
    R = np.eye(3) + K * s + K @ K * (1 - c)
    return R
            
            
def overlap_areas_xy_yz_zx(b1, b2) -> Dict[str, float]:
    """
    Return overlapping areas on XY, YZ, ZX planes between two AABBs.
    If there is no overlap along a dimension, that dimension's length is 0.
    """
    x1min, x1max, y1min, y1max, z1min, z1max = b1
    x2min, x2max, y2min, y2max, z2min, z2max = b2

    dx = max(0.0, min(x1max, x2max) - max(x1min, x2min))
    dy = max(0.0, min(y1max, y2max) - max(y1min, y2min))
    dz = max(0.0, min(z1max, z2max) - max(z1min, z2min))

    return {
        "A_xy": dx * dy,  # overlap area projected on XY
        "A_yz": dy * dz,  # overlap area projected on YZ
        "A_zx": dz * dx,  # overlap area projected on ZX
    }
    
def boxes_overlap(b1: BoundBox, b2: BoundBox, tol: float = 0.0) -> bool:
    """세 축 모두에서 구간이 겹치면 True. tol로 경계 접촉 허용 여유를 조절."""
    minX1, maxX1, minY1, maxY1, minZ1, maxZ1 = b1
    minX2, maxX2, minY2, maxY2, minZ2, maxZ2 = b2
    # 한 축이라도 떨어져 있으면 겹치지 않음
    if maxX1 < minX2 - tol or maxX2 < minX1 - tol: return False
    if maxY1 < minY2 - tol or maxY2 < minY1 - tol: return False
    if maxZ1 < minZ2 - tol or maxZ2 < minZ1 - tol: return False
    return True

def find_contact_pairs_naive(boundBoxDict: Dict[int, BoundBox], tol: float = 0.0) -> List[Tuple[int, int]]:
    """간단 O(N²) 버전. (id_small, id_large) 정렬 쌍만 반환(중복/순서 제거)."""
    ids = list(boundBoxDict.keys())
    pairs: List[Tuple[int,int]] = []
    for i in range(len(ids)):
        id1 = ids[i]
        b1 = boundBoxDict[id1]
        for j in range(i+1, len(ids)):
            id2 = ids[j]
            b2 = boundBoxDict[id2]
            if boxes_overlap(b1, b2, tol=tol):
                a, b = (id1, id2) if id1 < id2 else (id2, id1)
                pairs.append((a, b))
    return pairs

def find_contact_pairs_sweep(boundBoxDict: Dict[int, BoundBox], tol: float = 0.0) -> List[Tuple[int, int]]:
    """
    스윕&프룬: X축 minX 기준 정렬 후, X축에서 겹칠 가능성 있는 후보만 Y/Z로 정밀 체크.
    평균적으로 O(N log N + K) 수준(K는 후보 비교 수).
    """
    # X-시작점 기준 정렬
    items: List[Tuple[int, BoundBox]] = sorted(boundBoxDict.items(), key=lambda kv: kv[1][0])  # minX
    active: List[Tuple[int, BoundBox]] = []  # X축에서 아직 겹칠 가능성이 있는 박스들
    pairs_set = set()

    for id_cur, box_cur in items:
        minXc, maxXc, minYc, maxYc, minZc, maxZc = box_cur

        # X축에서 더 이상 겹치지 않는(active 후보에서 제외) 것들 제거
        new_active: List[Tuple[int, BoundBox]] = []
        for id_a, box_a in active:
            # box_a의 maxX가 현재 minX보다 크면 아직 겹칠 가능성 있음 -> 유지
            if box_a[1] >= minXc - tol:
                new_active.append((id_a, box_a))
        active = new_active

        # 남아 있는 active 후보들과 Y/Z축까지 정밀 체크
        for id_a, box_a in active:
            if boxes_overlap(box_cur, box_a, tol=tol):
                a, b = (id_cur, id_a) if id_cur < id_a else (id_a, id_cur)
                pairs_set.add((a, b))

        # 현재 박스를 active에 추가
        active.append((id_cur, box_cur))

    return sorted(pairs_set)