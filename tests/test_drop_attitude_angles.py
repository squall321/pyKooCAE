# cuboid 26케이스 낙하자세가 이름이 뜻하는 방향을 실제로 향하는지 검사하는 회귀 테스트
"""낙하자세 각도표 회귀 테스트.

과거 두 가지 사고가 있었다.
  1) 코너 C1~C8 이 roll 45°/135° 로 되어 있어 참 꼭짓점에서 9.74° 벗어났다.
     (45°/135° 는 면 대각선 방향이지 꼭짓점 방향이 아니다)
  2) 모서리 E09~E12 가 roll=±90 이라 짐벌 퇴화로 pitch 가 무효화돼
     ±Y 면으로 떨어졌다.
둘 다 "이름은 코너/모서리인데 실제로는 다른 곳으로 떨어지는" 형태라
덱만 봐서는 알아채기 어려웠다. 여기서 방향을 직접 계산해 막는다.

규약 (KooDynaAdvancedModification.DropAttitude 와 동일)
  R = Rx(roll)·Ry(pitch)·Rz(yaw),  충격방향 d = Rᵀ·(0,0,-1)
  yaw=0 이면  d = (cos r·sin p, -sin r, -cos r·cos p)
이름 규약은 관측자 기준: Right = -X, Top = -Y, Back = -Z.
"""

import math

import pytest

from Runner.AngleSourceParser import CUBOID_CORNERS, CUBOID_EDGES, CUBOID_FACES

# 이름 토큰 → 기기 좌표 단위 방향 (관측자 기준)
_AXIS = {
    "Right": (-1.0, 0.0, 0.0), "Left": (1.0, 0.0, 0.0),
    "Top": (0.0, -1.0, 0.0),   "Bottom": (0.0, 1.0, 0.0),
    "Back": (0.0, 0.0, -1.0),  "Front": (0.0, 0.0, 1.0),
}


def _drop_dir(roll: float, pitch: float, yaw: float = 0.0):
    """충격 방향 d = Rᵀ·(0,0,-1)."""
    r, p, y = math.radians(roll), math.radians(pitch), math.radians(yaw)
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    return (cr * sp * cy - sr * sy,
            -sr * cy - cr * sp * sy,
            -cr * cp)


def _truth_from_name(name: str):
    """'C1_Back_Right_Top' → 그 이름이 뜻하는 단위 방향."""
    v = [0.0, 0.0, 0.0]
    for token in name.split("_")[1:]:
        axis = _AXIS.get(token)
        if axis is None:
            continue
        for i in range(3):
            v[i] += axis[i]
    norm = math.sqrt(sum(c * c for c in v))
    assert norm > 0, f"이름에서 방향을 못 읽음: {name}"
    return tuple(c / norm for c in v)


def _angle_between(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / (na * nb)))))


ALL_CASES = [
    (name, rpy)
    for table in (CUBOID_FACES, CUBOID_EDGES, CUBOID_CORNERS)
    for name, rpy in table.items()
]


@pytest.mark.parametrize("name,rpy", ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_case_points_at_its_own_name(name, rpy):
    """26케이스 각각이 이름이 뜻하는 방향을 향해야 한다."""
    err = _angle_between(_drop_dir(*rpy), _truth_from_name(name))
    assert err < 1e-6, f"{name} {rpy} 가 참 방향에서 {err:.4f}° 벗어남"


def test_case_count():
    """면 6 + 모서리 12 + 코너 8 = 26."""
    assert len(CUBOID_FACES) == 6
    assert len(CUBOID_EDGES) == 12
    assert len(CUBOID_CORNERS) == 8


def test_no_gimbal_degeneracy():
    """roll=±90 이면 pitch 가 무효가 된다 — 그런 케이스가 없어야 한다.

    과거 E09~E12 가 (±90, ∓45) 여서 pitch 와 무관하게 ±Y 면으로 떨어졌다.
    """
    for name, (roll, pitch, _yaw) in ALL_CASES:
        if abs(abs(roll) - 90.0) < 1e-9:
            assert abs(pitch) < 1e-9, (
                f"{name}: roll=±90 은 짐벌 퇴화라 pitch={pitch} 가 무효화된다")


def test_all_directions_distinct():
    """26개 방향이 서로 달라야 한다 (중복 = 케이스 낭비 또는 오정의)."""
    dirs = [(name, _drop_dir(*rpy)) for name, rpy in ALL_CASES]
    for i, (n1, d1) in enumerate(dirs):
        for n2, d2 in dirs[i + 1:]:
            assert _angle_between(d1, d2) > 1e-6, f"{n1} 과 {n2} 가 같은 방향"


def test_corner_roll_is_exact_vertex_angle():
    """코너 roll 크기는 asin(1/√3)=35.264390° (또는 180-그 값) 여야 한다."""
    exact = math.degrees(math.asin(1.0 / math.sqrt(3.0)))
    for name, (roll, _pitch, _yaw) in CUBOID_CORNERS.items():
        mag = abs(roll)
        assert (abs(mag - exact) < 1e-6) or (abs(mag - (180.0 - exact)) < 1e-6), (
            f"{name}: roll 크기 {mag} 는 꼭짓점 각 {exact:.6f}/{180 - exact:.6f} 가 아님")
