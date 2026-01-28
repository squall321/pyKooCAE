"""
각도 믹싱 전략 (Priority 6)

누적 시뮬레이션에서 각 Step의 각도 조합 방식을 정의합니다.

5가지 믹싱 전략:
    1. same_angle: 동일 각도 반복
    2. cyclic: 순환 (인덱스 +offset)
    3. random: 랜덤 샘플링
    4. opposite: 대칭 각도
    5. custom_mapping: 사용자 정의 매핑

예시:
    Base 각도: [F1, F2, F3, ..., F26]
    누적 3회, same_angle 전략
    → Step 1: F1, Step 2: F1, Step 3: F1

    Base 각도: [P0001, P0002, ..., P0413]
    누적 3회, cyclic(offset=1) 전략
    → Step 1: P0001, Step 2: P0002, Step 3: P0003
"""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import random
import math


class MixingStrategy(Enum):
    """각도 믹싱 전략"""
    SAME_ANGLE = "same_angle"              # 동일 각도 반복
    CYCLIC = "cyclic"                      # 순환 (인덱스 +offset)
    RANDOM = "random"                      # 랜덤 샘플링
    OPPOSITE = "opposite"                  # 대칭 각도
    CUSTOM_MAPPING = "custom_mapping"      # 사용자 정의 매핑


@dataclass
class CumulativeAngleConfig:
    """누적 각도 설정"""
    mixing_strategy: MixingStrategy
    cyclic_offset: int = 1                 # cyclic 전략에서 인덱스 증가량
    random_seed: Optional[int] = None      # random 전략에서 랜덤 시드
    custom_mapping: Optional[Dict[int, int]] = None  # custom_mapping 전략에서 Step → 인덱스 매핑


def generate_same_angle_sequence(
    base_angles: List[Tuple[str, float, float, float]],
    num_steps: int,
    base_index: int = 0
) -> List[Tuple[str, float, float, float]]:
    """
    동일 각도 반복 전략

    Parameters:
        base_angles: Base 각도 리스트
        num_steps: Step 개수
        base_index: Base 각도 인덱스 (기본값: 0)

    Returns:
        Step별 각도 리스트

    Example:
        >>> base_angles = [("F1", 0, 0, 0), ("F2", 180, 0, 0)]
        >>> sequence = generate_same_angle_sequence(base_angles, 3, base_index=0)
        >>> [name for name, _, _, _ in sequence]
        ['F1', 'F1', 'F1']
    """
    if base_index < 0 or base_index >= len(base_angles):
        raise ValueError(f"base_index 범위 초과: {base_index} (최대: {len(base_angles)-1})")

    base_angle = base_angles[base_index]
    return [base_angle] * num_steps


def generate_cyclic_sequence(
    base_angles: List[Tuple[str, float, float, float]],
    num_steps: int,
    start_index: int = 0,
    offset: int = 1
) -> List[Tuple[str, float, float, float]]:
    """
    순환 전략 (인덱스 +offset)

    Parameters:
        base_angles: Base 각도 리스트
        num_steps: Step 개수
        start_index: 시작 인덱스
        offset: 인덱스 증가량

    Returns:
        Step별 각도 리스트

    Example:
        >>> base_angles = [("F1", 0, 0, 0), ("F2", 180, 0, 0), ("F3", 0, -90, 0)]
        >>> sequence = generate_cyclic_sequence(base_angles, 5, start_index=0, offset=1)
        >>> [name for name, _, _, _ in sequence]
        ['F1', 'F2', 'F3', 'F1', 'F2']
    """
    sequence = []
    num_angles = len(base_angles)

    for step in range(num_steps):
        idx = (start_index + step * offset) % num_angles
        sequence.append(base_angles[idx])

    return sequence


def generate_random_sequence(
    base_angles: List[Tuple[str, float, float, float]],
    num_steps: int,
    seed: Optional[int] = None
) -> List[Tuple[str, float, float, float]]:
    """
    랜덤 샘플링 전략

    Parameters:
        base_angles: Base 각도 리스트
        num_steps: Step 개수
        seed: 랜덤 시드 (재현성)

    Returns:
        Step별 각도 리스트

    Example:
        >>> base_angles = [("F1", 0, 0, 0), ("F2", 180, 0, 0), ("F3", 0, -90, 0)]
        >>> sequence = generate_random_sequence(base_angles, 5, seed=42)
        >>> len(sequence)
        5
    """
    if seed is not None:
        random.seed(seed)

    sequence = []
    for _ in range(num_steps):
        angle = random.choice(base_angles)
        sequence.append(angle)

    return sequence


def generate_opposite_sequence(
    base_angles: List[Tuple[str, float, float, float]],
    num_steps: int,
    base_index: int = 0
) -> List[Tuple[str, float, float, float]]:
    """
    대칭 각도 전략

    Step 1: Base 각도
    Step 2: Opposite 각도 (Roll +180°, Pitch 반전)
    Step 3: Base 각도
    Step 4: Opposite 각도
    ...

    Opposite 각도 계산:
        Roll_opposite = (Roll + 180) % 360 - 180  # [-180, 180] 범위로 정규화
        Pitch_opposite = -Pitch
        Yaw_opposite = Yaw

    Parameters:
        base_angles: Base 각도 리스트
        num_steps: Step 개수
        base_index: Base 각도 인덱스

    Returns:
        Step별 각도 리스트

    Example:
        >>> base_angles = [("F1_Back", 0, 0, 0)]
        >>> sequence = generate_opposite_sequence(base_angles, 4, base_index=0)
        >>> [(name, roll, pitch) for name, roll, pitch, _ in sequence]
        [('F1_Back', 0.0, 0.0), ('F1_Back_OPPOSITE', 180.0, 0.0), ('F1_Back', 0.0, 0.0), ('F1_Back_OPPOSITE', 180.0, 0.0)]
    """
    if base_index < 0 or base_index >= len(base_angles):
        raise ValueError(f"base_index 범위 초과: {base_index} (최대: {len(base_angles)-1})")

    base_name, base_roll, base_pitch, base_yaw = base_angles[base_index]

    # Opposite 각도 계산
    opposite_roll = ((base_roll + 180.0) % 360.0)
    if opposite_roll > 180.0:
        opposite_roll -= 360.0
    opposite_pitch = -base_pitch
    opposite_yaw = base_yaw

    opposite_name = f"{base_name}_OPPOSITE"
    opposite_angle = (opposite_name, opposite_roll, opposite_pitch, opposite_yaw)

    # Step별 각도 생성 (Base, Opposite, Base, Opposite, ...)
    sequence = []
    for step in range(num_steps):
        if step % 2 == 0:
            sequence.append((base_name, base_roll, base_pitch, base_yaw))
        else:
            sequence.append(opposite_angle)

    return sequence


def generate_custom_mapping_sequence(
    base_angles: List[Tuple[str, float, float, float]],
    num_steps: int,
    custom_mapping: Dict[int, int]
) -> List[Tuple[str, float, float, float]]:
    """
    사용자 정의 매핑 전략

    Parameters:
        base_angles: Base 각도 리스트
        num_steps: Step 개수
        custom_mapping: Step → 각도 인덱스 매핑 (1-based)

    Returns:
        Step별 각도 리스트

    Example:
        >>> base_angles = [("F1", 0, 0, 0), ("F2", 180, 0, 0), ("F3", 0, -90, 0)]
        >>> mapping = {1: 0, 2: 2, 3: 1}  # Step 1 → F1, Step 2 → F3, Step 3 → F2
        >>> sequence = generate_custom_mapping_sequence(base_angles, 3, mapping)
        >>> [name for name, _, _, _ in sequence]
        ['F1', 'F3', 'F2']
    """
    sequence = []

    for step in range(1, num_steps + 1):
        if step not in custom_mapping:
            raise ValueError(f"Step {step}에 대한 매핑이 없습니다.")

        idx = custom_mapping[step]
        if idx < 0 or idx >= len(base_angles):
            raise ValueError(f"Step {step}의 인덱스 범위 초과: {idx} (최대: {len(base_angles)-1})")

        sequence.append(base_angles[idx])

    return sequence


def generate_cumulative_angle_sequence(
    base_angles: List[Tuple[str, float, float, float]],
    num_steps: int,
    config: CumulativeAngleConfig,
    base_index: int = 0
) -> List[Tuple[str, float, float, float]]:
    """
    누적 각도 시퀀스 생성

    Parameters:
        base_angles: Base 각도 리스트
        num_steps: Step 개수
        config: CumulativeAngleConfig
        base_index: Base 각도 인덱스 (same_angle, opposite 전략용)

    Returns:
        Step별 각도 리스트

    Example:
        >>> base_angles = [("F1", 0, 0, 0), ("F2", 180, 0, 0)]
        >>> config = CumulativeAngleConfig(mixing_strategy=MixingStrategy.SAME_ANGLE)
        >>> sequence = generate_cumulative_angle_sequence(base_angles, 3, config, base_index=0)
        >>> [name for name, _, _, _ in sequence]
        ['F1', 'F1', 'F1']
    """
    if config.mixing_strategy == MixingStrategy.SAME_ANGLE:
        return generate_same_angle_sequence(base_angles, num_steps, base_index)

    elif config.mixing_strategy == MixingStrategy.CYCLIC:
        return generate_cyclic_sequence(base_angles, num_steps, base_index, config.cyclic_offset)

    elif config.mixing_strategy == MixingStrategy.RANDOM:
        return generate_random_sequence(base_angles, num_steps, config.random_seed)

    elif config.mixing_strategy == MixingStrategy.OPPOSITE:
        return generate_opposite_sequence(base_angles, num_steps, base_index)

    elif config.mixing_strategy == MixingStrategy.CUSTOM_MAPPING:
        if config.custom_mapping is None:
            raise ValueError("custom_mapping 전략에서 custom_mapping이 필요합니다.")
        return generate_custom_mapping_sequence(base_angles, num_steps, config.custom_mapping)

    else:
        raise ValueError(f"지원하지 않는 믹싱 전략: {config.mixing_strategy}")


# 테스트 코드
if __name__ == "__main__":
    print("\n" + "="*100)
    print("각도 믹싱 전략 테스트")
    print("="*100)

    # 테스트용 Base 각도
    base_angles = [
        ("F1_Back", 0.0, 0.0, 0.0),
        ("F2_Front", 180.0, 0.0, 0.0),
        ("F3_Right", 0.0, -90.0, 0.0),
        ("F4_Left", 0.0, 90.0, 0.0),
        ("F5_Top", 90.0, 0.0, 0.0),
    ]

    # 테스트 1: same_angle 전략
    print("\n테스트 1: same_angle 전략 (3 steps, base_index=0)")
    config1 = CumulativeAngleConfig(mixing_strategy=MixingStrategy.SAME_ANGLE)
    sequence1 = generate_cumulative_angle_sequence(base_angles, 3, config1, base_index=0)
    print(f"총 Step 수: {len(sequence1)}")
    for i, (name, roll, pitch, yaw) in enumerate(sequence1, start=1):
        print(f"  Step {i}: {name:<20} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    # 테스트 2: cyclic 전략
    print("\n테스트 2: cyclic 전략 (5 steps, offset=1)")
    config2 = CumulativeAngleConfig(mixing_strategy=MixingStrategy.CYCLIC, cyclic_offset=1)
    sequence2 = generate_cumulative_angle_sequence(base_angles, 5, config2, base_index=0)
    print(f"총 Step 수: {len(sequence2)}")
    for i, (name, roll, pitch, yaw) in enumerate(sequence2, start=1):
        print(f"  Step {i}: {name:<20} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    # 테스트 3: cyclic 전략 (offset=2)
    print("\n테스트 3: cyclic 전략 (5 steps, offset=2)")
    config3 = CumulativeAngleConfig(mixing_strategy=MixingStrategy.CYCLIC, cyclic_offset=2)
    sequence3 = generate_cumulative_angle_sequence(base_angles, 5, config3, base_index=0)
    print(f"총 Step 수: {len(sequence3)}")
    for i, (name, roll, pitch, yaw) in enumerate(sequence3, start=1):
        print(f"  Step {i}: {name:<20} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    # 테스트 4: random 전략
    print("\n테스트 4: random 전략 (5 steps, seed=42)")
    config4 = CumulativeAngleConfig(mixing_strategy=MixingStrategy.RANDOM, random_seed=42)
    sequence4 = generate_cumulative_angle_sequence(base_angles, 5, config4)
    print(f"총 Step 수: {len(sequence4)}")
    for i, (name, roll, pitch, yaw) in enumerate(sequence4, start=1):
        print(f"  Step {i}: {name:<20} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    # 테스트 5: opposite 전략
    print("\n테스트 5: opposite 전략 (4 steps, base_index=0)")
    config5 = CumulativeAngleConfig(mixing_strategy=MixingStrategy.OPPOSITE)
    sequence5 = generate_cumulative_angle_sequence(base_angles, 4, config5, base_index=0)
    print(f"총 Step 수: {len(sequence5)}")
    for i, (name, roll, pitch, yaw) in enumerate(sequence5, start=1):
        print(f"  Step {i}: {name:<25} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    # 테스트 6: custom_mapping 전략
    print("\n테스트 6: custom_mapping 전략 (3 steps, mapping={1:0, 2:2, 3:4})")
    custom_mapping = {1: 0, 2: 2, 3: 4}  # Step 1 → F1, Step 2 → F3, Step 3 → F5
    config6 = CumulativeAngleConfig(
        mixing_strategy=MixingStrategy.CUSTOM_MAPPING,
        custom_mapping=custom_mapping
    )
    sequence6 = generate_cumulative_angle_sequence(base_angles, 3, config6)
    print(f"총 Step 수: {len(sequence6)}")
    for i, (name, roll, pitch, yaw) in enumerate(sequence6, start=1):
        print(f"  Step {i}: {name:<20} Roll={roll:>7.2f}, Pitch={pitch:>7.2f}, Yaw={yaw:>7.2f}")

    print("\n" + "="*100)
    print("모든 테스트 완료!")
    print("="*100 + "\n")
