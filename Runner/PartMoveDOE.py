# 파트 위치 변경 DOE 파서 — scenario.part_doe → 이동 케이스 리스트 생성

"""
파트 이동 DOE 소스 파서

취약 조건(각도/위치)을 고정한 채 특정 파트의 장착 위치를 흔들어보는 DOE.
조건 축과 직교하며, Designer 가 두 축을 곱해 최종 DOE 케이스를 만든다.

sampling.method:
    1. lhs      : Latin Hypercube — 범위 내 층화 무작위 (num_samples 개)
    2. grid     : 균등 격자 — nx·ny·nz 개
    3. explicit : cases 로 이동량 직접 열거

입력: part_doe 설정 (scenario.json)
출력: PartMoveCase 리스트

Author: koo.park
Email: koo.park@samsung.com
Group: CAE
"""

import json
import os
import random
from typing import List, Optional, Tuple
from dataclasses import dataclass, field


# 이동량이 이보다 작으면 "이동 없음"으로 간주한다. 모델 단위(mm 가정)에서
# 1e-9 는 어떤 메시 크기에서도 무의미한 값이라 KMM 호출을 아낀다.
ZERO_MOVE_EPS = 1e-9


@dataclass
class PartMove:
    """단일 파트의 이동량 (모델 글로벌 XYZ, 모델 단위 그대로)"""
    pid: int
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0

    def is_zero(self) -> bool:
        return (abs(self.dx) < ZERO_MOVE_EPS
                and abs(self.dy) < ZERO_MOVE_EPS
                and abs(self.dz) < ZERO_MOVE_EPS)

    def to_dict(self) -> dict:
        return {"pid": self.pid, "dx": self.dx, "dy": self.dy, "dz": self.dz}


@dataclass
class PartMoveCase:
    """이동 DOE 한 케이스 — 여러 파트를 동시에 옮길 수 있다"""
    name: str
    moves: List[PartMove] = field(default_factory=list)

    def is_identity(self) -> bool:
        """전 파트가 무이동 = 원본 모델과 동일"""
        return all(m.is_zero() for m in self.moves)


def _axis_range(spec, axis: str, pid) -> Tuple[float, float]:
    """dx/dy/dz 스펙 → (lo, hi). 생략 시 (0, 0) = 이동 없음."""
    if spec is None:
        return (0.0, 0.0)
    if isinstance(spec, (int, float)):
        return (float(spec), float(spec))    # 스칼라 = 고정 이동
    if not isinstance(spec, (list, tuple)) or len(spec) != 2:
        raise ValueError(
            f"part_doe parts[pid={pid}].{axis}: [최소, 최대] 또는 스칼라여야 합니다 "
            f"(받은 값: {spec!r})")
    lo, hi = float(spec[0]), float(spec[1])
    if lo > hi:
        raise ValueError(
            f"part_doe parts[pid={pid}].{axis}: 최소({lo}) > 최대({hi}) 입니다")
    return (lo, hi)


def _parse_parts_ranges(parts_cfg: list) -> List[Tuple[int, dict]]:
    """parts 설정 → [(pid, {axis: (lo, hi)}), ...]"""
    if not parts_cfg:
        raise ValueError(
            "part_doe.parts 가 비어 있습니다. "
            '이동할 파트를 [{"pid": 12, "dx": [-0.5, 0.5]}, ...] 형식으로 지정하세요.')

    out = []
    seen = set()
    for i, pc in enumerate(parts_cfg):
        if not isinstance(pc, dict) or "pid" not in pc:
            raise ValueError(f"part_doe.parts[{i}]: pid 는 필수입니다 (받은 값: {pc!r})")
        pid = int(pc["pid"])
        if pid in seen:
            raise ValueError(
                f"part_doe.parts 에 PID {pid} 가 중복 지정됐습니다. "
                f"한 파트의 이동은 한 항목에 모으세요.")
        seen.add(pid)
        ranges = {ax: _axis_range(pc.get(ax), ax, pid) for ax in ("dx", "dy", "dz")}
        if all(lo == 0.0 and hi == 0.0 for lo, hi in ranges.values()):
            raise ValueError(
                f"part_doe.parts[pid={pid}]: dx/dy/dz 가 모두 비어 있어 이동이 없습니다.")
        out.append((pid, ranges))
    return out


def _sample_lhs(parts: List[Tuple[int, dict]], num_samples: int,
                seed: Optional[int]) -> List[PartMoveCase]:
    """Latin Hypercube — 각 축을 num_samples 구간으로 층화 후 구간별 1점 무작위.

    축이 여러 개(파트×3축)라도 각 축이 독립적으로 층화되므로 주변분포가 균등하다.
    """
    if num_samples < 1:
        raise ValueError(f"part_doe.sampling.num_samples 는 1 이상이어야 합니다 (받은 값: {num_samples})")

    rng = random.Random(seed)

    # 축별로 [0,1) 층화 순열을 만든다
    axis_keys = [(pid, ax) for pid, _ in parts for ax in ("dx", "dy", "dz")]
    strata = {}
    for key in axis_keys:
        order = list(range(num_samples))
        rng.shuffle(order)
        strata[key] = [(order[i] + rng.random()) / num_samples for i in range(num_samples)]

    cases = []
    for s in range(num_samples):
        moves = []
        for pid, ranges in parts:
            vals = {}
            for ax in ("dx", "dy", "dz"):
                lo, hi = ranges[ax]
                vals[ax] = lo if lo == hi else lo + strata[(pid, ax)][s] * (hi - lo)
            moves.append(PartMove(pid=pid, **{k: round(v, 9) for k, v in vals.items()}))
        cases.append(PartMoveCase(name=f"M{s + 1:04d}", moves=moves))
    return cases


def _sample_grid(parts: List[Tuple[int, dict]], nx: int, ny: int, nz: int) -> List[PartMoveCase]:
    """균등 격자 — 전 파트가 같은 격자 인덱스를 공유한다.

    파트마다 독립 격자를 쓰면 조합수가 (nx·ny·nz)^파트수 로 폭발하므로,
    "여러 파트가 함께 같은 방향으로 어긋난다"는 공차 해석에 맞춰 인덱스를 공유한다.
    """
    for label, n in (("nx", nx), ("ny", ny), ("nz", nz)):
        if n < 1:
            raise ValueError(f"part_doe.sampling.{label} 는 1 이상이어야 합니다 (받은 값: {n})")

    def _lin(lo: float, hi: float, n: int, i: int) -> float:
        if n == 1 or lo == hi:
            return (lo + hi) / 2.0
        return lo + i * (hi - lo) / (n - 1)

    cases = []
    for iz in range(nz):
        for iy in range(ny):
            for ix in range(nx):
                moves = []
                for pid, ranges in parts:
                    moves.append(PartMove(
                        pid=pid,
                        dx=round(_lin(*ranges["dx"], nx, ix), 9),
                        dy=round(_lin(*ranges["dy"], ny, iy), 9),
                        dz=round(_lin(*ranges["dz"], nz, iz), 9),
                    ))
                cases.append(PartMoveCase(name=f"M{len(cases) + 1:04d}", moves=moves))
    return cases


def _parse_explicit(cases_cfg: list) -> List[PartMoveCase]:
    """cases 로 이동량 직접 열거"""
    if not cases_cfg:
        raise ValueError(
            'part_doe.sampling.method="explicit" 인데 cases 가 비어 있습니다.')

    out = []
    seen = set()
    for i, cc in enumerate(cases_cfg):
        if not isinstance(cc, dict):
            raise ValueError(f"part_doe.cases[{i}]: 딕셔너리여야 합니다 (받은 값: {cc!r})")
        name = str(cc.get("name") or f"M{i + 1:04d}").strip()
        if name in seen:
            raise ValueError(f"part_doe.cases 에 중복된 이름: {name!r}")
        seen.add(name)

        moves_cfg = cc.get("moves") or []
        if not moves_cfg:
            raise ValueError(f"part_doe.cases[{i}] ({name}): moves 가 비어 있습니다")

        moves, pids = [], set()
        for j, mc in enumerate(moves_cfg):
            if not isinstance(mc, dict) or "pid" not in mc:
                raise ValueError(
                    f"part_doe.cases[{i}].moves[{j}]: pid 는 필수입니다 (받은 값: {mc!r})")
            pid = int(mc["pid"])
            if pid in pids:
                raise ValueError(
                    f"part_doe.cases[{i}] ({name}): PID {pid} 가 중복 지정됐습니다")
            pids.add(pid)
            moves.append(PartMove(pid=pid,
                                  dx=float(mc.get("dx") or 0.0),
                                  dy=float(mc.get("dy") or 0.0),
                                  dz=float(mc.get("dz") or 0.0)))
        out.append(PartMoveCase(name=name, moves=moves))
    return out


def parse_part_doe(config: Optional[dict]) -> List[PartMoveCase]:
    """part_doe 설정 → 이동 케이스 리스트

    블록이 없거나 enabled=false 면 **빈 리스트**를 반환한다. 호출 측(Designer)은
    빈 리스트를 "이동 축 없음"으로 해석해 기존 경로를 그대로 탄다 → 회귀 0.

    Parameters:
        config: part_doe 설정
            - enabled: bool (기본 True — 블록을 썼다면 쓰겠다는 뜻)
            - apply_step: int (기본 1)
            - sampling: { method: "lhs"|"grid"|"explicit", ... }
            - parts: [{pid, dx, dy, dz}, ...]        (lhs/grid)
            - cases: [{name, moves:[...]}, ...]      (explicit)
            - file: JSON 파일 경로 (내용이 위 설정 전체를 대체)

    Returns:
        PartMoveCase 리스트 (비활성 시 [])

    Example:
        >>> cases = parse_part_doe({"sampling": {"method": "grid", "nx": 3, "ny": 1, "nz": 1},
        ...                         "parts": [{"pid": 12, "dx": [-1.0, 1.0]}]})
        >>> [c.name for c in cases]
        ['M0001', 'M0002', 'M0003']
    """
    if not config:
        return []
    if not config.get("enabled", True):
        return []

    # 파일 참조 — 이동 케이스를 별도 파일로 관리할 때
    src_file = config.get("file")
    if src_file:
        if not os.path.exists(src_file):
            raise FileNotFoundError(f"part_doe.file 을 찾을 수 없습니다: {src_file}")
        with open(src_file, encoding="utf-8") as f:
            doc = json.load(f)
        merged = dict(doc)
        # enabled/apply_step 은 scenario.json 쪽 지정을 우선한다
        for k in ("enabled", "apply_step"):
            if k in config:
                merged[k] = config[k]
        config = merged

    sampling = config.get("sampling") or {}
    method = str(sampling.get("method", "lhs")).lower()

    if method == "explicit":
        return _parse_explicit(config.get("cases") or [])

    parts = _parse_parts_ranges(config.get("parts") or [])

    if method == "lhs":
        return _sample_lhs(parts,
                           int(sampling.get("num_samples", 10)),
                           sampling.get("seed"))

    if method == "grid":
        return _sample_grid(parts,
                            int(sampling.get("nx", 1)),
                            int(sampling.get("ny", 1)),
                            int(sampling.get("nz", 1)))

    raise ValueError(
        f'지원하지 않는 part_doe.sampling.method: "{method}". '
        f'lhs | grid | explicit 중 하나여야 합니다.')


def get_apply_step(config: Optional[dict]) -> int:
    """이동을 적용할 스텝 번호 (기본 1).

    누적 step>=2 는 이전 스텝의 *_dti.k(이미 이동된 변형 형상)를 입력으로 쓰므로
    재적용하면 이동량이 누적된다. 그래서 기본값이 1 이다.
    """
    if not config:
        return 1
    return int(config.get("apply_step", 1))
