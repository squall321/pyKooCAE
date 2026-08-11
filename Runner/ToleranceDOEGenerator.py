"""
Tolerance/DOE 시스템 (Priority 4)

각도 산포 분석을 위한 DOE (Design of Experiments) 생성기

DOE 타입:
    - LHS: Latin Hypercube Sampling (권장)
    - Grid: Grid Sampling (전체 조합)
    - Random: Random Sampling

Tolerance 설정:
    - roll: {min, max} 또는 {tolerance}
    - pitch: {min, max} 또는 {tolerance}
    - yaw: {min, max} 또는 {tolerance}

예시:
    Base: F1_Back (Roll=0, Pitch=0, Yaw=0)
    Tolerance: Roll=±2°, Pitch=±2°, Yaw=±1°
    DOE Count: 10

    → 10개의 DOE 샘플 생성:
        F1_Back_DOE001: Roll=-1.2, Pitch=+1.5, Yaw=-0.3
        F1_Back_DOE002: Roll=+0.8, Pitch=-0.9, Yaw=+0.7
        ...
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import random
import numpy as np


class DOEType(Enum):
    """DOE 타입"""
    LHS = "lhs"              # Latin Hypercube Sampling
    GRID = "grid"            # Grid Sampling
    RANDOM = "random"        # Random Sampling


@dataclass
class ToleranceRange:
    """Tolerance 범위 설정"""
    min_value: float
    max_value: float

    @classmethod
    def from_tolerance(cls, tolerance: float):
        """
        ±tolerance 형식으로 생성

        Example:
            >>> ToleranceRange.from_tolerance(2.0)
            ToleranceRange(min_value=-2.0, max_value=2.0)
        """
        return cls(min_value=-abs(tolerance), max_value=abs(tolerance))


@dataclass
class ToleranceConfig:
    """Tolerance 설정"""
    roll: Optional[ToleranceRange] = None
    pitch: Optional[ToleranceRange] = None
    yaw: Optional[ToleranceRange] = None
    doe_type: DOEType = DOEType.LHS
    doe_count: int = 10
    include_nominal: bool = False   # base 각도 자체(무섭동)를 케이스로 추가.
                                    # 산포 n 개에 **더해서** 1 개가 붙는다 (면당 n+1).
                                    # LHS 층화를 n 구간 그대로 두기 위해 n 을 깎지 않는다.

    def has_tolerance(self) -> bool:
        """Tolerance 설정 여부 확인"""
        return self.roll is not None or self.pitch is not None or self.yaw is not None


def _emit_nominal(result: list, doe_seq: int, base_name: str,
                  base_roll: float, base_pitch: float, base_yaw: float,
                  tolerance_config: ToleranceConfig) -> int:
    """include_nominal 이면 base 각도 자체를 케이스로 추가하고 다음 doe_seq 를 반환.

    산포 샘플보다 **앞에** 놓아 결과 정렬 시 기준 케이스가 먼저 오게 한다.

    🔴 이름에 `_DOE000` 을 넣는 이유. Designer 는 base 그룹을
       `name.split('_DOE')[0]` 로 뽑는다. `{base}_NOM` 으로 두면 `_DOE` 가 없어
       그룹이 `{base}_NOM` 이 되어 산포 샘플과 **다른 그룹**으로 쪼개지고,
       cyclic/random 믹싱의 base 각도 목록이 2배로 부풀어 오른다.
    """
    if not tolerance_config.include_nominal:
        return doe_seq
    result.append((f"{base_name}_DOE000_NOM", base_roll, base_pitch, base_yaw, doe_seq))
    return doe_seq + 1


def generate_lhs_samples(
    base_angles: List[Tuple[str, float, float, float]],
    tolerance_config: ToleranceConfig
) -> List[Tuple[str, float, float, float, int]]:
    """
    Latin Hypercube Sampling (LHS)으로 DOE 샘플 생성

    LHS는 각 변수의 범위를 균등하게 분할하고, 각 구간에서 하나씩 샘플링하여
    전체 공간을 효율적으로 커버합니다.

    Parameters:
        base_angles: [(name, roll, pitch, yaw), ...]
        tolerance_config: ToleranceConfig

    Returns:
        [(name, roll, pitch, yaw, doe_index), ...]

    Example:
        >>> base_angles = [("F1_Back", 0.0, 0.0, 0.0)]
        >>> config = ToleranceConfig(
        ...     roll=ToleranceRange.from_tolerance(2.0),
        ...     pitch=ToleranceRange.from_tolerance(2.0),
        ...     yaw=ToleranceRange.from_tolerance(1.0),
        ...     doe_type=DOEType.LHS,
        ...     doe_count=10
        ... )
        >>> samples = generate_lhs_samples(base_angles, config)
        >>> len(samples)
        10
    """
    n_samples = tolerance_config.doe_count
    # 🔴 doe_index 는 base 각도 전체를 관통하는 전역 통번호여야 한다.
    #    과거에는 base 마다 1 부터 다시 시작해 인덱스가 충돌했고,
    #    CumulativeDesigner 의 doe_count = len(set(doe_index)) 가 base 수만큼 축소돼
    #    러너의 range(1, doe_count+1) 루프에서 대부분의 케이스가 실행되지 않았다.
    #    (예: 꼭짓점 8개 x doe_count 10 = 80 이어야 하는데 doe_count 가 10 으로 기록)
    # 🔴 0-based 여야 한다. save_runner_config 가 doe_angles 키를 doe_index+1 로 만들고
    #    러너는 range(1, doe_count+1) 을 조회한다. 1-based 로 두면 키가 2..N+1 이 되어
    #    DOE 1 이 각도 조회에 실패(_condition_to_euler 폴백)하고 DOE N+1 은 실행되지 않는다.
    result = []
    doe_seq = 0

    # 각 base 각도에 대해 DOE 샘플 생성
    for base_name, base_roll, base_pitch, base_yaw in base_angles:
        doe_seq = _emit_nominal(result, doe_seq, base_name,
                                base_roll, base_pitch, base_yaw, tolerance_config)

        # Tolerance 범위 확인
        ranges = []
        base_values = []

        if tolerance_config.roll is not None:
            ranges.append((tolerance_config.roll.min_value, tolerance_config.roll.max_value))
            base_values.append(base_roll)
        else:
            ranges.append((0.0, 0.0))
            base_values.append(base_roll)

        if tolerance_config.pitch is not None:
            ranges.append((tolerance_config.pitch.min_value, tolerance_config.pitch.max_value))
            base_values.append(base_pitch)
        else:
            ranges.append((0.0, 0.0))
            base_values.append(base_pitch)

        if tolerance_config.yaw is not None:
            ranges.append((tolerance_config.yaw.min_value, tolerance_config.yaw.max_value))
            base_values.append(base_yaw)
        else:
            ranges.append((0.0, 0.0))
            base_values.append(base_yaw)

        # LHS 샘플 생성 (3차원: roll, pitch, yaw)
        n_vars = 3
        lhs_samples = np.zeros((n_samples, n_vars))

        for i in range(n_vars):
            # 각 변수를 n_samples 구간으로 분할
            intervals = np.linspace(0, 1, n_samples + 1)
            # 각 구간에서 무작위 샘플링
            samples = []
            for j in range(n_samples):
                lower = intervals[j]
                upper = intervals[j + 1]
                sample = random.uniform(lower, upper)
                samples.append(sample)
            # 구간 순서 섞기
            random.shuffle(samples)
            lhs_samples[:, i] = samples

        # [0, 1] 범위를 실제 Tolerance 범위로 변환
        for i in range(n_samples):
            roll_delta = lhs_samples[i, 0] * (ranges[0][1] - ranges[0][0]) + ranges[0][0]
            pitch_delta = lhs_samples[i, 1] * (ranges[1][1] - ranges[1][0]) + ranges[1][0]
            yaw_delta = lhs_samples[i, 2] * (ranges[2][1] - ranges[2][0]) + ranges[2][0]

            new_roll = base_roll + roll_delta
            new_pitch = base_pitch + pitch_delta
            new_yaw = base_yaw + yaw_delta

            doe_name = f"{base_name}_DOE{i+1:03d}"
            result.append((doe_name, new_roll, new_pitch, new_yaw, doe_seq))
            doe_seq += 1

    return result


def generate_grid_samples(
    base_angles: List[Tuple[str, float, float, float]],
    tolerance_config: ToleranceConfig
) -> List[Tuple[str, float, float, float, int]]:
    """
    Grid Sampling으로 DOE 샘플 생성

    각 변수의 범위를 균등하게 분할하고 전체 조합을 생성합니다.
    주의: doe_count는 각 변수당 샘플 개수로 해석됩니다.
    총 샘플 수 = doe_count^3 (3차원)

    Parameters:
        base_angles: [(name, roll, pitch, yaw), ...]
        tolerance_config: ToleranceConfig

    Returns:
        [(name, roll, pitch, yaw, doe_index), ...]

    Example:
        >>> base_angles = [("F1_Back", 0.0, 0.0, 0.0)]
        >>> config = ToleranceConfig(
        ...     roll=ToleranceRange.from_tolerance(2.0),
        ...     pitch=ToleranceRange.from_tolerance(2.0),
        ...     yaw=ToleranceRange.from_tolerance(1.0),
        ...     doe_type=DOEType.GRID,
        ...     doe_count=3  # 3x3x3 = 27 샘플
        ... )
        >>> samples = generate_grid_samples(base_angles, config)
        >>> len(samples)
        27
    """
    n_per_axis = tolerance_config.doe_count
    # 🔴 doe_index 는 base 각도 전체를 관통하는 전역 통번호여야 한다.
    #    과거에는 base 마다 1 부터 다시 시작해 인덱스가 충돌했고,
    #    CumulativeDesigner 의 doe_count = len(set(doe_index)) 가 base 수만큼 축소돼
    #    러너의 range(1, doe_count+1) 루프에서 대부분의 케이스가 실행되지 않았다.
    #    (예: 꼭짓점 8개 x doe_count 10 = 80 이어야 하는데 doe_count 가 10 으로 기록)
    result = []
    doe_seq = 0

    for base_name, base_roll, base_pitch, base_yaw in base_angles:
        doe_seq = _emit_nominal(result, doe_seq, base_name,
                                base_roll, base_pitch, base_yaw, tolerance_config)

        # Grid 생성
        roll_grid = []
        pitch_grid = []
        yaw_grid = []

        if tolerance_config.roll is not None:
            roll_grid = np.linspace(
                base_roll + tolerance_config.roll.min_value,
                base_roll + tolerance_config.roll.max_value,
                n_per_axis
            )
        else:
            roll_grid = [base_roll]

        if tolerance_config.pitch is not None:
            pitch_grid = np.linspace(
                base_pitch + tolerance_config.pitch.min_value,
                base_pitch + tolerance_config.pitch.max_value,
                n_per_axis
            )
        else:
            pitch_grid = [base_pitch]

        if tolerance_config.yaw is not None:
            yaw_grid = np.linspace(
                base_yaw + tolerance_config.yaw.min_value,
                base_yaw + tolerance_config.yaw.max_value,
                n_per_axis
            )
        else:
            yaw_grid = [base_yaw]

        # 전체 조합 생성
        doe_idx = 1
        for roll_val in roll_grid:
            for pitch_val in pitch_grid:
                for yaw_val in yaw_grid:
                    doe_name = f"{base_name}_DOE{doe_idx:03d}"
                    result.append((doe_name, roll_val, pitch_val, yaw_val, doe_seq))
                    doe_seq += 1
                    doe_idx += 1

    return result


def generate_random_samples(
    base_angles: List[Tuple[str, float, float, float]],
    tolerance_config: ToleranceConfig
) -> List[Tuple[str, float, float, float, int]]:
    """
    Random Sampling으로 DOE 샘플 생성

    각 변수의 범위 내에서 무작위로 샘플링합니다.

    Parameters:
        base_angles: [(name, roll, pitch, yaw), ...]
        tolerance_config: ToleranceConfig

    Returns:
        [(name, roll, pitch, yaw, doe_index), ...]

    Example:
        >>> base_angles = [("F1_Back", 0.0, 0.0, 0.0)]
        >>> config = ToleranceConfig(
        ...     roll=ToleranceRange.from_tolerance(2.0),
        ...     pitch=ToleranceRange.from_tolerance(2.0),
        ...     yaw=ToleranceRange.from_tolerance(1.0),
        ...     doe_type=DOEType.RANDOM,
        ...     doe_count=10
        ... )
        >>> samples = generate_random_samples(base_angles, config)
        >>> len(samples)
        10
    """
    n_samples = tolerance_config.doe_count
    # 🔴 doe_index 는 base 각도 전체를 관통하는 전역 통번호여야 한다.
    #    과거에는 base 마다 1 부터 다시 시작해 인덱스가 충돌했고,
    #    CumulativeDesigner 의 doe_count = len(set(doe_index)) 가 base 수만큼 축소돼
    #    러너의 range(1, doe_count+1) 루프에서 대부분의 케이스가 실행되지 않았다.
    #    (예: 꼭짓점 8개 x doe_count 10 = 80 이어야 하는데 doe_count 가 10 으로 기록)
    result = []
    doe_seq = 0

    for base_name, base_roll, base_pitch, base_yaw in base_angles:
        doe_seq = _emit_nominal(result, doe_seq, base_name,
                                base_roll, base_pitch, base_yaw, tolerance_config)

        for i in range(n_samples):
            # Random delta 생성
            roll_delta = 0.0
            pitch_delta = 0.0
            yaw_delta = 0.0

            if tolerance_config.roll is not None:
                roll_delta = random.uniform(
                    tolerance_config.roll.min_value,
                    tolerance_config.roll.max_value
                )

            if tolerance_config.pitch is not None:
                pitch_delta = random.uniform(
                    tolerance_config.pitch.min_value,
                    tolerance_config.pitch.max_value
                )

            if tolerance_config.yaw is not None:
                yaw_delta = random.uniform(
                    tolerance_config.yaw.min_value,
                    tolerance_config.yaw.max_value
                )

            new_roll = base_roll + roll_delta
            new_pitch = base_pitch + pitch_delta
            new_yaw = base_yaw + yaw_delta

            doe_name = f"{base_name}_DOE{i+1:03d}"
            result.append((doe_name, new_roll, new_pitch, new_yaw, doe_seq))
            doe_seq += 1

    return result


def apply_tolerance_doe(
    base_angles: List[Tuple[str, float, float, float]],
    tolerance_config: ToleranceConfig
) -> List[Tuple[str, float, float, float, int]]:
    """
    Tolerance/DOE 적용

    Parameters:
        base_angles: [(name, roll, pitch, yaw), ...]
        tolerance_config: ToleranceConfig

    Returns:
        [(name, roll, pitch, yaw, doe_index), ...]

    Example:
        >>> base_angles = [("F1_Back", 0.0, 0.0, 0.0)]
        >>> config = ToleranceConfig(
        ...     roll=ToleranceRange.from_tolerance(2.0),
        ...     pitch=ToleranceRange.from_tolerance(2.0),
        ...     yaw=ToleranceRange.from_tolerance(1.0),
        ...     doe_type=DOEType.LHS,
        ...     doe_count=10
        ... )
        >>> samples = apply_tolerance_doe(base_angles, config)
        >>> len(samples)
        10
    """
    if not tolerance_config.has_tolerance():
        # Tolerance 없으면 원본 그대로 반환 (doe_index=0)
        return [(name, roll, pitch, yaw, 0) for name, roll, pitch, yaw in base_angles]

    if tolerance_config.doe_type == DOEType.LHS:
        return generate_lhs_samples(base_angles, tolerance_config)
    elif tolerance_config.doe_type == DOEType.GRID:
        return generate_grid_samples(base_angles, tolerance_config)
    elif tolerance_config.doe_type == DOEType.RANDOM:
        return generate_random_samples(base_angles, tolerance_config)
    else:
        raise ValueError(f"지원하지 않는 DOE 타입: {tolerance_config.doe_type}")


# 테스트 코드
if __name__ == "__main__":
    print("\n" + "="*100)
    print("Tolerance/DOE 시스템 테스트")
    print("="*100)

    # 테스트 1: LHS (Latin Hypercube Sampling)
    print("\n테스트 1: LHS (10 samples)")
    base_angles = [("F1_Back", 0.0, 0.0, 0.0)]
    config1 = ToleranceConfig(
        roll=ToleranceRange.from_tolerance(2.0),
        pitch=ToleranceRange.from_tolerance(2.0),
        yaw=ToleranceRange.from_tolerance(1.0),
        doe_type=DOEType.LHS,
        doe_count=10
    )
    samples1 = apply_tolerance_doe(base_angles, config1)
    print(f"총 샘플 수: {len(samples1)}")
    print(f"샘플 (처음 5개):")
    for name, roll, pitch, yaw, doe_idx in samples1[:5]:
        print(f"  {name:<25} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}, DOE={doe_idx}")

    # 테스트 2: Grid (3x3x3 = 27 samples)
    print("\n테스트 2: Grid (3x3x3 = 27 samples)")
    config2 = ToleranceConfig(
        roll=ToleranceRange.from_tolerance(2.0),
        pitch=ToleranceRange.from_tolerance(2.0),
        yaw=ToleranceRange.from_tolerance(1.0),
        doe_type=DOEType.GRID,
        doe_count=3
    )
    samples2 = apply_tolerance_doe(base_angles, config2)
    print(f"총 샘플 수: {len(samples2)}")
    print(f"샘플 (처음 5개):")
    for name, roll, pitch, yaw, doe_idx in samples2[:5]:
        print(f"  {name:<25} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}, DOE={doe_idx}")

    # 테스트 3: Random (10 samples)
    print("\n테스트 3: Random (10 samples)")
    config3 = ToleranceConfig(
        roll=ToleranceRange.from_tolerance(2.0),
        pitch=ToleranceRange.from_tolerance(2.0),
        yaw=ToleranceRange.from_tolerance(1.0),
        doe_type=DOEType.RANDOM,
        doe_count=10
    )
    samples3 = apply_tolerance_doe(base_angles, config3)
    print(f"총 샘플 수: {len(samples3)}")
    print(f"샘플 (처음 5개):")
    for name, roll, pitch, yaw, doe_idx in samples3[:5]:
        print(f"  {name:<25} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}, DOE={doe_idx}")

    # 테스트 4: 다중 Base 각도 (Cuboid F1-F6)
    print("\n테스트 4: 다중 Base 각도 (Cuboid F1-F6) + LHS (5 samples)")
    base_angles_cuboid = [
        ("F1_Back", 0.0, 0.0, 0.0),
        ("F2_Front", 180.0, 0.0, 0.0),
        ("F3_Right", 0.0, -90.0, 0.0),
        ("F4_Left", 0.0, 90.0, 0.0),
        ("F5_Top", 90.0, 0.0, 0.0),
        ("F6_Bottom", -90.0, 0.0, 0.0),
    ]
    config4 = ToleranceConfig(
        roll=ToleranceRange.from_tolerance(1.0),
        pitch=ToleranceRange.from_tolerance(1.0),
        doe_type=DOEType.LHS,
        doe_count=5
    )
    samples4 = apply_tolerance_doe(base_angles_cuboid, config4)
    print(f"총 샘플 수: {len(samples4)} (6 base × 5 DOE)")
    print(f"샘플 (처음 10개):")
    for name, roll, pitch, yaw, doe_idx in samples4[:10]:
        print(f"  {name:<25} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}, DOE={doe_idx}")

    # 테스트 5: Tolerance 없음 (원본 그대로)
    print("\n테스트 5: Tolerance 없음 (원본 그대로)")
    config5 = ToleranceConfig(doe_count=10)  # Tolerance 설정 없음
    samples5 = apply_tolerance_doe(base_angles, config5)
    print(f"총 샘플 수: {len(samples5)}")
    for name, roll, pitch, yaw, doe_idx in samples5:
        print(f"  {name:<25} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}, DOE={doe_idx}")

    print("\n" + "="*100)
    print("모든 테스트 완료!")
    print("="*100 + "\n")
