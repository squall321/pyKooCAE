"""
각도 소스 파서 (Priority 3)

5가지 각도 소스 타입을 지원합니다:
    1. cuboid_geometry: F1-F6 (Face), E1-E12 (Edge), C1-C8 (Corner) - 26개
    2. fibonacci_lattice: 구면 균등 분포 (26~41,253 케이스)
    3. pitching_sweep: Pitch -90~90° 스윕 (Roll 고정)
    4. rolling_sweep: Roll -180~170° 스윕 (Pitch 고정)
    5. case_txt_file: 표준 Case txt 파일 (11개 파일 지원)

각도 소스 설정 → (name, roll, pitch, yaw) 리스트 반환
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import os
import math

from Runner.CaseTxtParser import parse_case_txt_file, DropAngle


class AngleSourceType(Enum):
    """각도 소스 타입"""
    CUBOID_GEOMETRY = "cuboid_geometry"
    FIBONACCI_LATTICE = "fibonacci_lattice"
    PITCHING_SWEEP = "pitching_sweep"
    ROLLING_SWEEP = "rolling_sweep"
    CASE_TXT_FILE = "case_txt_file"


@dataclass
class CuboidGeometryConfig:
    """Cuboid 기하 설정"""
    include_faces: bool = True      # F1-F6 포함
    include_edges: bool = True      # E1-E12 포함
    include_corners: bool = True    # C1-C8 포함
    only: Optional[List[str]] = None  # 특정 자세만 선택. 설정 시 include_* 무시.
                                    # 전체 이름("C1_Back_Right_Top") 또는 짧은 코드("C1","F5","E01")
                                    # 둘 다 허용하며 대소문자 무관. 나열 순서대로 방출한다.
                                    # 오타는 조용히 무시하지 않고 ValueError 로 막는다.


@dataclass
class FibonacciLatticeConfig:
    """Fibonacci Lattice 설정"""
    num_points: int                 # 포인트 개수 (26, 103, 413, ...)
    angle_spacing: Optional[float] = None  # 각도 간격 (deg) - num_points 대신 사용 가능
    progressive: bool = False       # True면 점진적(farthest-point) 샘플링 순서로 재정렬
                                    # → prefix(앞 k개)가 항상 전구면 균일, 나머지가 빈틈을 채움
    principal_directions: Optional[str] = None  # None | "faces"(6) | "faces_corners"(14) | "cuboid26"(26)
                                    # 설정 시: 표준 낙하자세를 먼저 배치(시드) + 나머지를 그 사이
                                    # 등간격(seeded farthest-point)으로 채움. (물리 frame 강제)
    sampling_space: Optional[str] = None  # None/"latlon"=기존(lat/lon 파라미터 공간 균일, 호환)
                                    # "physical"=실제 낙하방향(DropAttitude 회전) 공간에서 등간격.
                                    # lat/lon 균일은 실제 충격방향 공간에선 한쪽 쏠림(비∞) → physical 권장.
                                    # principal_directions 설정 시 자동으로 physical 적용.
    previous_stages: Optional[List[int]] = None  # 이미 돌린 단계들의 누적 개수 (오름차순).
                                    # 예: [120, 500] + num_points=1000 → 이미 500개를 돌렸고
                                    # 이번에 500개를 추가해 누적 1000개를 만든다.
                                    # 이전 단계 위치를 결정론적으로 재현한 뒤, 이번 N세트에서
                                    # 그것들과 가까운 점을 정확히 제거하고 나머지만 방출한다.
                                    # → 단계 경로와 무관하게 누적 위치 셋이 항상 동일.
                                    # 🔴 모든 단계가 num_points 를 제외하고 같은 설정이어야 한다.


@dataclass
class PitchingSweepConfig:
    """Pitching 스윕 설정"""
    pitch_min: float = -90.0        # Pitch 최소값
    pitch_max: float = 90.0         # Pitch 최대값
    pitch_step: float = 10.0        # Pitch 간격
    roll_fixed: float = 0.0         # Roll 고정값
    yaw_fixed: float = 0.0          # Yaw 고정값


@dataclass
class RollingSweepConfig:
    """Rolling 스윕 설정"""
    roll_min: float = -180.0        # Roll 최소값
    roll_max: float = 170.0         # Roll 최대값
    roll_step: float = 10.0         # Roll 간격
    pitch_fixed: float = 0.0        # Pitch 고정값
    yaw_fixed: float = 0.0          # Yaw 고정값


@dataclass
class CaseTxtFileConfig:
    """Case txt 파일 설정"""
    file_path: str                  # 파일 경로
    selected_indices: Optional[List[int]] = None  # 특정 인덱스 선택


@dataclass
class AngleSourceConfig:
    """각도 소스 설정"""
    source_type: AngleSourceType
    cuboid_geometry: Optional[CuboidGeometryConfig] = None
    fibonacci_lattice: Optional[FibonacciLatticeConfig] = None
    pitching_sweep: Optional[PitchingSweepConfig] = None
    rolling_sweep: Optional[RollingSweepConfig] = None
    case_txt_file: Optional[CaseTxtFileConfig] = None


# ============================================================================
# Cuboid Geometry 정의 (F/E/C)
# ============================================================================

# Cuboid 좌표계: LS-DYNA 글로벌 (X=오른쪽, Y=위, Z=전면)
# Euler 각도: Roll → Pitch → Yaw (Z-Y-X 내재 회전)

CUBOID_FACES = {
    "F1_Back":    (0.0,    0.0,  0.0),
    "F2_Front":   (180.0,  0.0,  0.0),
    "F3_Right":   (0.0,   -90.0, 0.0),
    "F4_Left":    (0.0,    90.0, 0.0),
    "F5_Top":     (90.0,   0.0,  0.0),
    "F6_Bottom":  (-90.0,  0.0,  0.0),
}

CUBOID_EDGES = {
    "E01_Back_Right":    (0.0,    -45.0, 0.0),
    "E02_Back_Left":     (0.0,     45.0, 0.0),
    "E03_Back_Top":      (45.0,    0.0,  0.0),
    "E04_Back_Bottom":   (-45.0,   0.0,  0.0),
    "E05_Front_Right":   (180.0,   45.0, 0.0),
    "E06_Front_Left":    (180.0,  -45.0, 0.0),
    "E07_Front_Top":     (135.0,   0.0,  0.0),
    "E08_Front_Bottom":  (-135.0,  0.0,  0.0),
    "E09_Right_Top":     (45.0,   -90.0, 0.0),
    "E10_Right_Bottom":  (-45.0,  -90.0, 0.0),
    "E11_Left_Top":      (45.0,    90.0, 0.0),
    "E12_Left_Bottom":   (-45.0,   90.0, 0.0),
}

CUBOID_CORNERS = {
    "C1_Back_Right_Top":      (45.0,   -45.0, 0.0),
    "C2_Back_Right_Bottom":   (-45.0,  -45.0, 0.0),
    "C3_Back_Left_Top":       (45.0,    45.0, 0.0),
    "C4_Back_Left_Bottom":    (-45.0,   45.0, 0.0),
    "C5_Front_Right_Top":     (135.0,   45.0, 0.0),
    "C6_Front_Right_Bottom":  (-135.0,  45.0, 0.0),
    "C7_Front_Left_Top":      (135.0,  -45.0, 0.0),
    "C8_Front_Left_Bottom":   (-135.0, -45.0, 0.0),
}


# ============================================================================
# 각도 소스 파서 함수들
# ============================================================================

def parse_cuboid_geometry(config: CuboidGeometryConfig) -> List[Tuple[str, float, float, float]]:
    """
    Cuboid 기하 각도 생성 (F/E/C)

    Returns:
        List of (name, roll, pitch, yaw)

    Example:
        >>> config = CuboidGeometryConfig()
        >>> angles = parse_cuboid_geometry(config)
        >>> len(angles)
        26
    """
    all_dirs = {}
    all_dirs.update(CUBOID_FACES)
    all_dirs.update(CUBOID_EDGES)
    all_dirs.update(CUBOID_CORNERS)

    # only 가 있으면 그것만 (특정 자세 집중 조사용 — tolerance 와 함께 쓰는 것이 일반적)
    only = getattr(config, "only", None)
    if only:
        if isinstance(only, str):
            only = [only]
        # 짧은 코드(C1/F5/E01) → 전체 이름. 대소문자 무관.
        by_code = {}
        for full in all_dirs:
            by_code[full.upper()] = full
            by_code[full.split('_')[0].upper()] = full
        picked, bad = [], []
        for token in only:
            key = str(token).strip().upper()
            if key in by_code:
                name = by_code[key]
                picked.append((name,) + all_dirs[name])
            else:
                bad.append(token)
        if bad:
            raise ValueError(
                f"cuboid_geometry.only 에 알 수 없는 자세명: {bad}. "
                f"사용 가능한 코드: F1~F6, E01~E12, C1~C8 (또는 전체 이름 {sorted(all_dirs)[:2]}...)")
        return picked

    angles = []

    if config.include_faces:
        for name, (roll, pitch, yaw) in CUBOID_FACES.items():
            angles.append((name, roll, pitch, yaw))

    if config.include_edges:
        for name, (roll, pitch, yaw) in CUBOID_EDGES.items():
            angles.append((name, roll, pitch, yaw))

    if config.include_corners:
        for name, (roll, pitch, yaw) in CUBOID_CORNERS.items():
            angles.append((name, roll, pitch, yaw))

    return angles


def parse_fibonacci_lattice(config: FibonacciLatticeConfig) -> List[Tuple[str, float, float, float]]:
    """
    Fibonacci Lattice 각도 생성

    fibonacci_lattice_generator.py와 동일한 알고리즘 사용:
        1. fibonacci_sphere(N)으로 구면 균등 분포 (x, y, z) 생성
        2. vector_to_euler(x, y, z)로 오일러 각도 변환

    Returns:
        List of (name, roll, pitch, yaw)

    Example:
        >>> config = FibonacciLatticeConfig(num_points=26)
        >>> angles = parse_fibonacci_lattice(config)
        >>> len(angles)
        26
    """
    N = config.num_points
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))  # ≈ 137.508°

    # 0-a) 단계별(staged) 생성: 이미 돌린 단계가 선언되면 그 위치를 재현하고 빼고 방출한다.
    if getattr(config, "previous_stages", None):
        return _staged_lattice(config)

    # 0) physical 공간 생성: 실제 낙하방향(DropAttitude 회전) 공간에서 등간격.
    #    principal_directions 가 설정되면(표준 자세 시드) 무조건 physical(그래야 면이 안 붕괴됨).
    #
    # 🔴 기본값이 physical 이다(2026-08-05 변경). 과거 기본이던 lat/lon 파라미터 공간 균등은
    #    실제 낙하방향으로 환산하면 심하게 뒤틀린다 — 실측(낙하방향 이웃 각거리 최대/최소):
    #      N=20  기본 ∞배(중복 발생) vs physical 1.1배
    #      N=100 기본 65.6배        vs physical 1.1배
    #      N=500 기본 ∞배(중복 발생) vs physical 1.1배
    #    게다가 방향이 적도 부근에 74% 몰리고 극(위/아래 낙하)은 5% 밖에 안 뽑혀,
    #    N=20 에서는 20개 중 1쌍이 완전히 같은 방향이 되는 사고가 실제로 있었다.
    #    구 동작이 필요하면 sampling_space 에 "latlon" 을 명시해야 한다.
    principal = getattr(config, "principal_directions", None)
    space = getattr(config, "sampling_space", None) or "physical"
    if space != "latlon" or principal:
        return _physical_lattice(N, principal, bool(getattr(config, "progressive", False)), golden_angle)

    # 1) 구면 균등 분포 점 + 오일러 각 생성 (스파이럴 순서) — 기존 lat/lon 경로 (호환)
    vecs = []      # 단위 벡터 (재정렬용)
    eulers = []    # (roll, pitch, yaw)
    for i in range(N):
        y = 1 - (i / float(N - 1)) * 2 if N > 1 else 0
        radius = math.sqrt(max(0.0, 1 - y * y))
        theta = golden_angle * i
        x = math.cos(theta) * radius
        z = math.sin(theta) * radius

        r = math.sqrt(x*x + y*y + z*z)
        if r == 0:
            roll, pitch, yaw = 0.0, 0.0, 0.0
        else:
            lat = math.asin(max(-1, min(1, y / r)))
            lon = math.atan2(z, x)
            roll = round(math.degrees(lat) - 90, 2)
            pitch = round(-math.degrees(lon), 2)
            yaw = 0.0
        vecs.append((x, y, z))
        eulers.append((roll, pitch, yaw))

    # 2) 샘플링 순서 결정
    #    progressive=True → farthest-point(max-min) 순서: prefix(앞 k개)가 항상
    #    전구면에 균일하게 퍼지고, 뒤로 갈수록 그 사이 빈틈을 채운다. 중간까지만
    #    돌려도 의미 있는 균등 커버리지를 얻는다. (스파이럴 기본 순서는 prefix가
    #    상단 캡만 덮어 부분 실행 시 편향됨.)
    order = list(range(N))
    if getattr(config, "progressive", False) and N > 2:
        order = _farthest_point_order(vecs)

    # 3) 결정된 순서대로 출력 (이름은 샘플링 순번 = doe 순서)
    angles = []
    for new_i, orig_i in enumerate(order):
        roll, pitch, yaw = eulers[orig_i]
        angles.append((f"P{new_i+1:04d}", roll, pitch, yaw))

    return angles


def _remove_nearest(cand_dirs: List[Tuple[float, float, float]],
                    prev_dirs: List[Tuple[float, float, float]],
                    k: int) -> List[int]:
    """후보에서 prev 에 가까운 점을 정확히 k 개 제거하고, 남은 후보의 인덱스를 반환.

    prev 를 순서대로 훑으며 각자 "가장 가까운 아직 안 지워진 후보" 하나씩을 가져간다.
    - 결정론적(입력 순서만으로 결과가 정해짐)
    - O(P·N) 시간 / O(N) 메모리. 전역 그리디 매칭과 품질이 동일함을 실측 확인했고
      (누적 500 기준 둘 다 최소간격 4.59°), 메모리가 선형이라 큰 N 에서도 안전하다.
    """
    removed = set()
    for p in prev_dirs:
        if len(removed) >= k:
            break
        best_dot, best_i = -2.0, None
        for i, c in enumerate(cand_dirs):
            if i in removed:
                continue
            d = p[0] * c[0] + p[1] * c[1] + p[2] * c[2]   # 클수록 가깝다
            if d > best_dot:
                best_dot, best_i = d, i
        if best_i is None:
            break
        removed.add(best_i)
    return [i for i in range(len(cand_dirs)) if i not in removed]


def _staged_lattice(config: FibonacciLatticeConfig) -> List[Tuple[str, float, float, float]]:
    """이전 단계를 재현한 뒤, 이번 단계의 신규분만 방출.

    previous_stages=[120,500], num_points=1000 이면
      acc = gen(120)                              → 120
      acc += gen(500) 에서 acc 근처 120개 제거     → 500
      new  = gen(1000) 에서 acc 근처 500개 제거    → 500  ← 방출
    이름은 누적 순번을 잇는다(P0501~P1000).
    """
    N = config.num_points
    stages = list(config.previous_stages or [])

    # --- 입력 검증: 조용히 틀린 각도 셋을 내보내지 않는다 ---
    if any((not isinstance(s, int)) or s <= 0 for s in stages):
        raise ValueError(f"previous_stages 는 양의 정수여야 합니다: {stages}")
    if any(b <= a for a, b in zip(stages, stages[1:])):
        raise ValueError(f"previous_stages 는 오름차순이어야 합니다: {stages}")
    if stages[-1] >= N:
        raise ValueError(
            f"previous_stages 의 마지막({stages[-1]})은 num_points({N})보다 작아야 합니다. "
            f"num_points 는 '최종 누적 총량'입니다.")

    def _gen(n: int) -> List[Tuple[str, float, float, float]]:
        """같은 설정으로 n 개 생성 (단계 재현용 — previous_stages 만 뗀다)."""
        sub = FibonacciLatticeConfig(
            num_points=n,
            angle_spacing=config.angle_spacing,
            progressive=config.progressive,
            principal_directions=config.principal_directions,
            sampling_space=config.sampling_space,
            previous_stages=None,
        )
        return parse_fibonacci_lattice(sub)

    # 거리는 실제 낙하방향 공간에서 잰다(파라미터 공간이 아니라 물리적으로 가까운지가 기준).
    acc_dirs: List[Tuple[float, float, float]] = []
    for s in stages:
        cand = _gen(s)
        cand_dirs = [_physical_drop_dir(r, p) for _, r, p, _ in cand]
        keep = _remove_nearest(cand_dirs, acc_dirs, len(acc_dirs))
        acc_dirs.extend(cand_dirs[i] for i in keep)

    cand = _gen(N)
    cand_dirs = [_physical_drop_dir(r, p) for _, r, p, _ in cand]
    keep = _remove_nearest(cand_dirs, acc_dirs, len(acc_dirs))

    base = len(acc_dirs)
    # 🔴 이전 단계를 빠뜨리고 선언하면 재현이 어긋나 실제 기존 점과 겹치는 각도가 섞인다
    #    (실측: [120,500] 을 [500] 로 잘못 적으면 1000개 중 4개가 1° 이내 중복).
    #    실제로 돌린 단계를 하나도 빠짐없이 적었는지 이 줄로 확인할 것.
    print(f"  단계별 각도 생성: 이전 단계 {stages} → 재현 누적 {base}개, "
          f"이번 신규 {len(keep)}개, 최종 누적 {base + len(keep)}개")
    return [(f"P{base + j + 1:04d}", cand[i][1], cand[i][2], cand[i][3])
            for j, i in enumerate(keep)]


def _farthest_point_order(vecs: List[Tuple[float, float, float]]) -> List[int]:
    """단위 벡터 집합을 farthest-point(greedy max-min) 순서로 재정렬한 인덱스 리스트.

    각 단계에서 "이미 선택된 점들로부터 최소 각거리가 가장 큰" 점을 추가한다.
    → 어떤 prefix 도 전구면에 고르게 분포(progressive/저불일치). O(N^2), 순수 파이썬.
    """
    n = len(vecs)
    if n <= 2:
        return list(range(n))

    def dot(a, b):
        return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

    selected = [0]
    remaining = set(range(1, n))
    # nearest_dot[i] = 선택집합 중 i와의 최대 내적(=최소 각거리). 작을수록 멀다.
    nearest_dot = [dot(vecs[i], vecs[0]) for i in range(n)]
    while remaining:
        # 선택집합에서 가장 먼(=nearest_dot 최소) 점 선택
        best = min(remaining, key=lambda i: nearest_dot[i])
        selected.append(best)
        remaining.discard(best)
        vb = vecs[best]
        for i in remaining:
            d = dot(vecs[i], vb)
            if d > nearest_dot[i]:
                nearest_dot[i] = d
    return selected


def _euler_to_vec(roll: float, pitch: float, yaw: float = 0.0) -> Tuple[float, float, float]:
    """(roll,pitch,yaw) → 단위벡터. parse_fibonacci_lattice 의 vector→euler 규약 역변환."""
    lat = math.radians(roll + 90.0)
    lon = math.radians(-pitch)
    cl = math.cos(lat)
    return (cl * math.cos(lon), math.sin(lat), cl * math.sin(lon))


def _principal_seed(which: str) -> List[Tuple[str, float, float, float]]:
    """표준 낙하자세 시드. faces(6) / faces_corners(14) / cuboid26(26)."""
    items = list(CUBOID_FACES.items())
    if which == "faces_corners":
        items += list(CUBOID_CORNERS.items())
    elif which == "cuboid26":
        items += list(CUBOID_EDGES.items()) + list(CUBOID_CORNERS.items())
    return [(name, r, p, y) for name, (r, p, y) in items]


def _physical_drop_dir(roll: float, pitch: float) -> Tuple[float, float, float]:
    """(roll,pitch,yaw=0) → 실제 낙하방향. DropAttitude 규약 RotMat·(0,0,-1).
    유도: dx=sin(pitch)cos(roll), dy=-sin(roll), dz=-cos(pitch)cos(roll)."""
    rr = math.radians(roll); pp = math.radians(pitch)
    cr = math.cos(rr)
    return (math.sin(pp) * cr, -math.sin(rr), -math.cos(pp) * cr)


def _dir_to_euler(dx: float, dy: float, dz: float) -> Tuple[float, float, float]:
    """낙하방향(dx,dy,dz) → (roll,pitch,yaw=0) 해석적 역산. _physical_drop_dir 의 역.
    roll∈[-90,90] 정규형: roll=-asin(dy), pitch=atan2(dx,-dz). 극(cos roll≈0)이면 pitch=0."""
    n = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
    dx, dy, dz = dx / n, dy / n, dz / n
    roll = -math.degrees(math.asin(max(-1.0, min(1.0, dy))))
    cr = math.sqrt(max(0.0, 1.0 - dy * dy))
    pitch = 0.0 if cr < 1e-9 else math.degrees(math.atan2(dx, -dz))
    return (round(roll, 2), round(pitch, 2), 0.0)


def _physical_lattice(N: int, principal: Optional[str], progressive: bool,
                      golden_angle: float) -> List[Tuple[str, float, float, float]]:
    """실제 낙하방향 공간에서 등간격 생성.

    - principal 설정 시: 표준 자세(면/모서리/꼭짓점)를 먼저 시드(이름·euler 보존) +
      **정규 N세트에서 시드와 가장 가까운 점을 시드 개수만큼 제거한 나머지**로 채움.
      즉 principal_directions="cuboid26", num_points=100 이면
      26개 표준 자세 + (정규 100세트 − 표준에 가장 가까운 26개) = 74개 → 총 100개.
      previous_stages 의 단계별 규칙과 동일한 로직(_remove_nearest)이므로,
      채워지는 74개는 정규 100세트의 실제 위치이고 단계 확장과도 일관된다.
    - principal 없음 + progressive: 후보를 farthest-point 순서로 정렬.
    - principal 없음 + non-progressive: 후보 스파이럴 순서 그대로.
    채움/후보 방향은 모두 _dir_to_euler 로 정규형 euler 변환(P#### 이름).
    """
    def dot(a, b):
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    # 표준 시드: 물리방향 기준 중복 제거(roll=±90 gimbal 로 면과 겹치는 에지 등 → 첫 이름 보존).
    raw_seed = _principal_seed(principal) if principal else []
    seed, seed_dirs = [], []
    for name, r, p, yw in raw_seed:
        if len(seed) >= N:
            break
        d = _physical_drop_dir(r, p)
        if any(dot(d, sd) > 0.9998 for sd in seed_dirs):  # ~1° 이내면 중복
            continue
        seed.append((name, r, p, yw)); seed_dirs.append(d)
    out = list(seed)
    if len(out) >= N:
        return out

    def gen_cands(M):
        cd = []
        for i in range(M):
            y = 1 - (2 * i + 1) / float(M)
            radius = math.sqrt(max(0.0, 1 - y * y))
            theta = golden_angle * i
            cd.append((math.cos(theta) * radius, y, math.sin(theta) * radius))
        return cd

    if not seed and not progressive:
        # 스파이럴 순서 그대로 (offset fibonacci N개 → 물리방향 → 정규 euler)
        for i, d in enumerate(gen_cands(N)):
            r, p, yw = _dir_to_euler(*d)
            out.append((f"P{i + 1:04d}", r, p, yw))
        return out

    if seed_dirs:
        # 표준 자세 시드 + 정규 N세트에서 시드 최근접분을 제거한 나머지로 채움.
        # 임의 후보풀(4N)에서 고르지 않고 정규 N세트의 실제 위치를 쓰므로,
        # previous_stages 단계 확장과 같은 규칙이 되어 결과가 서로 일관된다.
        cand_dirs = gen_cands(N)
        keep = _remove_nearest(cand_dirs, seed_dirs, len(seed_dirs))
        for i in keep:
            if len(out) >= N:
                break
            r, p, yw = _dir_to_euler(*cand_dirs[i])
            out.append((f"P{len(out) + 1:04d}", r, p, yw))
        return out

    # 여기부터는 principal 없음 + progressive 경로만 도달한다(위 seed 분기에서 return).
    # 채움(farthest-point): 후보풀을 넉넉히(≥4N) 잡아 상호 중복 없이 균일 선택
    cand_dirs = gen_cands(max(4 * N, 64))

    remaining = set(range(len(cand_dirs)))
    first = cand_dirs[0]
    r, p, yw = _dir_to_euler(*first)
    out.append((f"P{len(out) + 1:04d}", r, p, yw))
    remaining.discard(0)
    nearest = [dot(cand_dirs[i], first) for i in range(len(cand_dirs))]

    while len(out) < N and remaining:
        best = min(remaining, key=lambda i: nearest[i])
        r, p, yw = _dir_to_euler(*cand_dirs[best])
        out.append((f"P{len(out) + 1:04d}", r, p, yw))
        remaining.discard(best)
        vb = cand_dirs[best]
        for i in remaining:
            d = dot(cand_dirs[i], vb)
            if d > nearest[i]:
                nearest[i] = d
    return out


def parse_pitching_sweep(config: PitchingSweepConfig) -> List[Tuple[str, float, float, float]]:
    """
    Pitching 스윕 각도 생성

    Returns:
        List of (name, roll, pitch, yaw)

    Example:
        >>> config = PitchingSweepConfig(pitch_min=-90, pitch_max=90, pitch_step=10)
        >>> angles = parse_pitching_sweep(config)
        >>> len(angles)
        19
    """
    angles = []
    pitch = config.pitch_min

    idx = 1
    while pitch <= config.pitch_max + 1e-6:  # 부동소수점 오차 허용
        name = f"Pitch_{pitch:+.1f}"
        angles.append((name, config.roll_fixed, pitch, config.yaw_fixed))
        pitch += config.pitch_step
        idx += 1

    return angles


def parse_rolling_sweep(config: RollingSweepConfig) -> List[Tuple[str, float, float, float]]:
    """
    Rolling 스윕 각도 생성

    Returns:
        List of (name, roll, pitch, yaw)

    Example:
        >>> config = RollingSweepConfig(roll_min=-180, roll_max=170, roll_step=10)
        >>> angles = parse_rolling_sweep(config)
        >>> len(angles)
        36
    """
    angles = []
    roll = config.roll_min

    idx = 1
    while roll <= config.roll_max + 1e-6:  # 부동소수점 오차 허용
        name = f"Roll_{roll:+.1f}"
        angles.append((name, roll, config.pitch_fixed, config.yaw_fixed))
        roll += config.roll_step
        idx += 1

    return angles


def parse_case_txt_file_angles(config: CaseTxtFileConfig) -> List[Tuple[str, float, float, float]]:
    """
    Case txt 파일에서 각도 추출

    Returns:
        List of (name, roll, pitch, yaw)

    Example:
        >>> config = CaseTxtFileConfig(file_path="FullAngleDrop/26case_6F12E8C_cuboid.txt")
        >>> angles = parse_case_txt_file_angles(config)
        >>> len(angles)
        26
    """
    # 전체 각도 파싱
    drop_angles = parse_case_txt_file(config.file_path)

    # 특정 인덱스 선택
    if config.selected_indices is not None:
        max_index = len(drop_angles)
        selected_drop_angles = []
        for idx in config.selected_indices:
            if idx < 0 or idx >= max_index:
                raise ValueError(f"인덱스 범위 초과: {idx} (최대: {max_index-1})")
            selected_drop_angles.append(drop_angles[idx])
        drop_angles = selected_drop_angles

    # (name, roll, pitch, yaw) 형식으로 변환
    angles = [(da.name, da.roll, da.pitch, da.yaw) for da in drop_angles]
    return angles


def parse_angle_source(config: AngleSourceConfig) -> List[Tuple[str, float, float, float]]:
    """
    각도 소스 설정 → (name, roll, pitch, yaw) 리스트 반환

    Parameters:
        config: AngleSourceConfig

    Returns:
        List of (name, roll, pitch, yaw)

    Example:
        >>> # Cuboid
        >>> config = AngleSourceConfig(
        ...     source_type=AngleSourceType.CUBOID_GEOMETRY,
        ...     cuboid_geometry=CuboidGeometryConfig()
        ... )
        >>> angles = parse_angle_source(config)
        >>> len(angles)
        26

        >>> # Fibonacci
        >>> config = AngleSourceConfig(
        ...     source_type=AngleSourceType.FIBONACCI_LATTICE,
        ...     fibonacci_lattice=FibonacciLatticeConfig(num_points=413)
        ... )
        >>> angles = parse_angle_source(config)
        >>> len(angles)
        413
    """
    if config.source_type == AngleSourceType.CUBOID_GEOMETRY:
        if config.cuboid_geometry is None:
            raise ValueError("cuboid_geometry 설정이 필요합니다.")
        return parse_cuboid_geometry(config.cuboid_geometry)

    elif config.source_type == AngleSourceType.FIBONACCI_LATTICE:
        if config.fibonacci_lattice is None:
            raise ValueError("fibonacci_lattice 설정이 필요합니다.")
        return parse_fibonacci_lattice(config.fibonacci_lattice)

    elif config.source_type == AngleSourceType.PITCHING_SWEEP:
        if config.pitching_sweep is None:
            raise ValueError("pitching_sweep 설정이 필요합니다.")
        return parse_pitching_sweep(config.pitching_sweep)

    elif config.source_type == AngleSourceType.ROLLING_SWEEP:
        if config.rolling_sweep is None:
            raise ValueError("rolling_sweep 설정이 필요합니다.")
        return parse_rolling_sweep(config.rolling_sweep)

    elif config.source_type == AngleSourceType.CASE_TXT_FILE:
        if config.case_txt_file is None:
            raise ValueError("case_txt_file 설정이 필요합니다.")
        return parse_case_txt_file_angles(config.case_txt_file)

    else:
        raise ValueError(f"지원하지 않는 각도 소스 타입: {config.source_type}")


# 테스트 코드
if __name__ == "__main__":
    print("\n" + "="*100)
    print("각도 소스 파서 테스트")
    print("="*100)

    # 테스트 1: Cuboid Geometry
    print("\n테스트 1: Cuboid Geometry (F1-F6, E1-E12, C1-C8)")
    config1 = AngleSourceConfig(
        source_type=AngleSourceType.CUBOID_GEOMETRY,
        cuboid_geometry=CuboidGeometryConfig()
    )
    angles1 = parse_angle_source(config1)
    print(f"총 케이스 수: {len(angles1)}")
    print(f"샘플 (처음 5개):")
    for name, roll, pitch, yaw in angles1[:5]:
        print(f"  {name:<20} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    # 테스트 2: Fibonacci Lattice (26 points)
    print("\n테스트 2: Fibonacci Lattice (26 points)")
    config2 = AngleSourceConfig(
        source_type=AngleSourceType.FIBONACCI_LATTICE,
        fibonacci_lattice=FibonacciLatticeConfig(num_points=26)
    )
    angles2 = parse_angle_source(config2)
    print(f"총 케이스 수: {len(angles2)}")
    print(f"샘플 (처음 5개):")
    for name, roll, pitch, yaw in angles2[:5]:
        print(f"  {name:<20} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    # 테스트 3: Pitching Sweep
    print("\n테스트 3: Pitching Sweep (-90~90, step=10)")
    config3 = AngleSourceConfig(
        source_type=AngleSourceType.PITCHING_SWEEP,
        pitching_sweep=PitchingSweepConfig()
    )
    angles3 = parse_angle_source(config3)
    print(f"총 케이스 수: {len(angles3)}")
    print(f"샘플 (처음 5개):")
    for name, roll, pitch, yaw in angles3[:5]:
        print(f"  {name:<20} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    # 테스트 4: Rolling Sweep
    print("\n테스트 4: Rolling Sweep (-180~170, step=10)")
    config4 = AngleSourceConfig(
        source_type=AngleSourceType.ROLLING_SWEEP,
        rolling_sweep=RollingSweepConfig()
    )
    angles4 = parse_angle_source(config4)
    print(f"총 케이스 수: {len(angles4)}")
    print(f"샘플 (처음 5개):")
    for name, roll, pitch, yaw in angles4[:5]:
        print(f"  {name:<20} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    # 테스트 5: Case txt 파일 (Cuboid)
    print("\n테스트 5: Case txt 파일 (26case_6F12E8C_cuboid.txt)")
    cuboid_file = "/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/FullAngleDrop/26case_6F12E8C_cuboid.txt"
    if os.path.exists(cuboid_file):
        config5 = AngleSourceConfig(
            source_type=AngleSourceType.CASE_TXT_FILE,
            case_txt_file=CaseTxtFileConfig(file_path=cuboid_file)
        )
        angles5 = parse_angle_source(config5)
        print(f"총 케이스 수: {len(angles5)}")
        print(f"샘플 (처음 5개):")
        for name, roll, pitch, yaw in angles5[:5]:
            print(f"  {name:<20} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    # 테스트 6: Case txt 파일 (Fibonacci, 특정 인덱스 선택)
    print("\n테스트 6: Case txt 파일 (Fibonacci, 인덱스 0,1,2,10,100 선택)")
    fib_file = "/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/FullAngleDrop/fibonacci_10deg_413cases.txt"
    if os.path.exists(fib_file):
        config6 = AngleSourceConfig(
            source_type=AngleSourceType.CASE_TXT_FILE,
            case_txt_file=CaseTxtFileConfig(
                file_path=fib_file,
                selected_indices=[0, 1, 2, 10, 100]
            )
        )
        angles6 = parse_angle_source(config6)
        print(f"총 케이스 수: {len(angles6)}")
        for name, roll, pitch, yaw in angles6:
            print(f"  {name:<20} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    print("\n" + "="*100)
    print("모든 테스트 완료!")
    print("="*100 + "\n")
