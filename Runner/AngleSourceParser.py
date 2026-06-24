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


@dataclass
class FibonacciLatticeConfig:
    """Fibonacci Lattice 설정"""
    num_points: int                 # 포인트 개수 (26, 103, 413, ...)
    angle_spacing: Optional[float] = None  # 각도 간격 (deg) - num_points 대신 사용 가능
    progressive: bool = False       # True면 점진적(farthest-point) 샘플링 순서로 재정렬
                                    # → prefix(앞 k개)가 항상 전구면 균일, 나머지가 빈틈을 채움


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
    "E09_Right_Top":     (90.0,   -45.0, 0.0),
    "E10_Right_Bottom":  (-90.0,  -45.0, 0.0),
    "E11_Left_Top":      (90.0,    45.0, 0.0),
    "E12_Left_Bottom":   (-90.0,   45.0, 0.0),
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

    # 1) 구면 균등 분포 점 + 오일러 각 생성 (스파이럴 순서)
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
