"""
Case txt 파일 파서 (Priority 1)

표준 Case txt 파일을 파싱하여 각도 정보를 추출합니다.

파일 형식:
    *Inputfile
    MinimumModel.k
    *Mode
    DROP_ATTITUDE,1
    **DropAttitude,1
    $ Case names (comma-separated)
    EulerRolling,0,180,0,...
    EulerPitching,0,0,-90,...
    EulerYawing,0,0,0,...
    Height,1500,1500,...
    **EndDropAttitude
    *End

지원 파일:
    - 26case_6F12E8C_cuboid.txt (26 케이스)
    - fibonacci_*deg_*cases.txt (Fibonacci 각도)
    - pitching_10deg_19cases.txt (Pitching 스윕)
    - rolling_10deg_36cases.txt (Rolling 스윕)
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import os


@dataclass
class CaseTxtConfig:
    """Case txt 파일 설정"""
    file_path: str
    selected_indices: Optional[List[int]] = None  # None = 전체, List = 특정 인덱스만


@dataclass
class DropAngle:
    """낙하 각도 정보"""
    name: str
    roll: float
    pitch: float
    yaw: float
    height: float = 1500.0
    initial_velocity_x: float = 0.0
    initial_velocity_y: float = 0.0
    initial_velocity_z: float = 0.0
    initial_angular_velocity_x: float = 0.0
    initial_angular_velocity_y: float = 0.0
    initial_angular_velocity_z: float = 0.0


def parse_case_txt_file(file_path: str) -> List[DropAngle]:
    """
    표준 Case txt 파일 파싱

    Parameters:
        file_path: Case txt 파일 경로 (절대 경로 또는 상대 경로)

    Returns:
        List of DropAngle 객체

    Example:
        >>> angles = parse_case_txt_file("FullAngleDrop/26case_6F12E8C_cuboid.txt")
        >>> len(angles)
        26
        >>> angles[0].name
        'F1_Back'
        >>> angles[0].roll, angles[0].pitch, angles[0].yaw
        (0.0, 0.0, 0.0)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Case txt 파일을 찾을 수 없습니다: {file_path}")

    case_names = []
    euler_rolling = []
    euler_pitching = []
    euler_yawing = []
    heights = []
    initial_velocity_x = []
    initial_velocity_y = []
    initial_velocity_z = []
    initial_angular_velocity_x = []
    initial_angular_velocity_y = []
    initial_angular_velocity_z = []

    with open(file_path, 'r') as f:
        lines = f.readlines()

    # 파싱 상태
    in_drop_attitude = False

    for line in lines:
        line = line.strip()

        # DROP_ATTITUDE 섹션 시작
        if line.startswith('**DropAttitude'):
            in_drop_attitude = True
            continue

        # DROP_ATTITUDE 섹션 종료
        if line.startswith('**EndDropAttitude'):
            in_drop_attitude = False
            continue

        # DROP_ATTITUDE 섹션 내부에서만 파싱
        if not in_drop_attitude:
            continue

        # 주석 라인 ($로 시작)에서 Case 이름 추출
        if line.startswith('$') and ',' in line:
            # "$ F1_Back,F2_Front,..." 형식
            # 첫 번째 $ 라인에서 case 이름 추출
            if not case_names:
                content = line[1:].strip()  # $ 제거
                # 주석이 아닌 경우에만 파싱 (=로 시작하지 않음)
                if not content.startswith('='):
                    case_names = [name.strip() for name in content.split(',')]
            continue

        # 데이터 라인 파싱
        if ',' in line:
            parts = line.split(',')
            key = parts[0].strip()
            values = [v.strip() for v in parts[1:]]

            if key == 'EulerRolling':
                euler_rolling = [float(v) for v in values if v]
            elif key == 'EulerPitching':
                euler_pitching = [float(v) for v in values if v]
            elif key == 'EulerYawing':
                euler_yawing = [float(v) for v in values if v]
            elif key == 'Height':
                heights = [float(v) for v in values if v]
            elif key == 'InitialVelocityX':
                initial_velocity_x = [float(v) for v in values if v]
            elif key == 'InitialVelocityY':
                initial_velocity_y = [float(v) for v in values if v]
            elif key == 'InitialVelocityZ':
                initial_velocity_z = [float(v) for v in values if v]
            elif key == 'InitialAngularVelocityX':
                initial_angular_velocity_x = [float(v) for v in values if v]
            elif key == 'InitialAngularVelocityY':
                initial_angular_velocity_y = [float(v) for v in values if v]
            elif key == 'InitialAngularVelocityZ':
                initial_angular_velocity_z = [float(v) for v in values if v]

    # 데이터 검증
    num_cases = len(euler_rolling)
    if not num_cases:
        raise ValueError(f"Case txt 파일에서 각도 데이터를 찾을 수 없습니다: {file_path}")

    if len(euler_pitching) != num_cases or len(euler_yawing) != num_cases:
        raise ValueError(f"각도 데이터 개수가 일치하지 않습니다: "
                        f"Roll={len(euler_rolling)}, Pitch={len(euler_pitching)}, Yaw={len(euler_yawing)}")

    # Case 이름이 없으면 자동 생성 (P0001, P0002, ...)
    if not case_names:
        case_names = [f"P{i+1:04d}" for i in range(num_cases)]
    elif len(case_names) != num_cases:
        # Case 이름 개수가 맞지 않으면 자동 생성
        print(f"경고: Case 이름 개수({len(case_names)})와 각도 개수({num_cases})가 다릅니다. 자동 생성합니다.")
        case_names = [f"P{i+1:04d}" for i in range(num_cases)]

    # Height 기본값
    if not heights:
        heights = [1500.0] * num_cases
    elif len(heights) != num_cases:
        heights = [1500.0] * num_cases

    # 초기 속도 기본값
    def fill_default(data_list, num_cases, default=0.0):
        if not data_list:
            return [default] * num_cases
        elif len(data_list) != num_cases:
            return [default] * num_cases
        return data_list

    initial_velocity_x = fill_default(initial_velocity_x, num_cases)
    initial_velocity_y = fill_default(initial_velocity_y, num_cases)
    initial_velocity_z = fill_default(initial_velocity_z, num_cases)
    initial_angular_velocity_x = fill_default(initial_angular_velocity_x, num_cases)
    initial_angular_velocity_y = fill_default(initial_angular_velocity_y, num_cases)
    initial_angular_velocity_z = fill_default(initial_angular_velocity_z, num_cases)

    # DropAngle 객체 생성
    angles = []
    for i in range(num_cases):
        angle = DropAngle(
            name=case_names[i],
            roll=euler_rolling[i],
            pitch=euler_pitching[i],
            yaw=euler_yawing[i],
            height=heights[i],
            initial_velocity_x=initial_velocity_x[i],
            initial_velocity_y=initial_velocity_y[i],
            initial_velocity_z=initial_velocity_z[i],
            initial_angular_velocity_x=initial_angular_velocity_x[i],
            initial_angular_velocity_y=initial_angular_velocity_y[i],
            initial_angular_velocity_z=initial_angular_velocity_z[i]
        )
        angles.append(angle)

    return angles


def parse_case_txt_with_selection(config: CaseTxtConfig) -> List[DropAngle]:
    """
    Case txt 파일 파싱 (특정 인덱스 선택 가능)

    Parameters:
        config: CaseTxtConfig 객체

    Returns:
        List of DropAngle 객체

    Example:
        >>> config = CaseTxtConfig(
        ...     file_path="FullAngleDrop/fibonacci_10deg_413cases.txt",
        ...     selected_indices=[0, 1, 2, 10, 100]
        ... )
        >>> angles = parse_case_txt_with_selection(config)
        >>> len(angles)
        5
    """
    # 전체 각도 파싱
    all_angles = parse_case_txt_file(config.file_path)

    # 특정 인덱스 선택
    if config.selected_indices is None:
        return all_angles

    # 인덱스 검증
    max_index = len(all_angles)
    selected_angles = []

    for idx in config.selected_indices:
        if idx < 0 or idx >= max_index:
            raise ValueError(f"인덱스 범위 초과: {idx} (최대: {max_index-1})")
        selected_angles.append(all_angles[idx])

    return selected_angles


def get_case_count(file_path: str) -> int:
    """
    Case txt 파일의 케이스 개수 반환 (빠른 조회용)

    Parameters:
        file_path: Case txt 파일 경로

    Returns:
        케이스 개수
    """
    angles = parse_case_txt_file(file_path)
    return len(angles)


def print_case_summary(file_path: str, max_display: int = 10):
    """
    Case txt 파일 요약 출력 (디버깅용)

    Parameters:
        file_path: Case txt 파일 경로
        max_display: 최대 표시 개수
    """
    angles = parse_case_txt_file(file_path)

    print(f"\n{'='*80}")
    print(f"Case txt 파일: {file_path}")
    print(f"총 케이스 수: {len(angles)}")
    print(f"{'='*80}\n")

    print(f"{'Index':<8} {'Name':<20} {'Roll':>10} {'Pitch':>10} {'Yaw':>10} {'Height':>10}")
    print(f"{'-'*80}")

    for i, angle in enumerate(angles[:max_display]):
        print(f"{i:<8} {angle.name:<20} {angle.roll:>10.2f} {angle.pitch:>10.2f} "
              f"{angle.yaw:>10.2f} {angle.height:>10.1f}")

    if len(angles) > max_display:
        print(f"... ({len(angles) - max_display} more cases)")

    print(f"{'-'*80}\n")


# 테스트 코드
if __name__ == "__main__":
    # 테스트 1: Cuboid 26 케이스
    print("\n테스트 1: Cuboid 26 케이스")
    cuboid_file = "/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/FullAngleDrop/26case_6F12E8C_cuboid.txt"
    if os.path.exists(cuboid_file):
        print_case_summary(cuboid_file, max_display=26)

    # 테스트 2: Fibonacci 10deg 413 케이스
    print("\n테스트 2: Fibonacci 10deg 413 케이스")
    fib_file = "/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/FullAngleDrop/fibonacci_10deg_413cases.txt"
    if os.path.exists(fib_file):
        print_case_summary(fib_file, max_display=10)

    # 테스트 3: 특정 인덱스 선택
    print("\n테스트 3: 특정 인덱스 선택 (0, 1, 2, 10, 100)")
    if os.path.exists(fib_file):
        config = CaseTxtConfig(
            file_path=fib_file,
            selected_indices=[0, 1, 2, 10, 100]
        )
        selected = parse_case_txt_with_selection(config)
        for angle in selected:
            print(f"  {angle.name}: Roll={angle.roll:.2f}, Pitch={angle.pitch:.2f}, Yaw={angle.yaw:.2f}")
