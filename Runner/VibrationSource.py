"""VibrationSource — Registry + Decorator dispatch for vibration load sources.

본 모듈은 VIB 모드 시나리오의 `vibration_source` 블록을 파싱하여
`VibrationLoadSpec` (불변 dataclass) 로 정규화한다.

아키텍처 (DESIGN.md L3 레이어):
    scenario.json `vibration_source` 블록
        │  (open-set string discriminator: D)
        ▼
    parse_vibration_source(config, ctx)
        │  → _VIBRATION_PARSERS[source_type](config, ctx)
        ▼
    VibrationLoadSpec  →  StepConfigBuilder.build_vibration_load_block

Zero-Hardcode 원칙 (DESIGN.md §2 채택안 A·D·E·F·G):
    - A. Registry + Decorator (정적 import만, Nuitka 안전)
    - D. source_type 은 open-set 문자열 discriminator (schema enum 금지)
    - E. components 정의는 inline 우선, `$ref` 진입로만 예약 (v1)
    - F. direction 은 X/Y/Z axis string (vector hook 만 예약)
    - G. base_curve 는 `kind` discriminated union (inline/csv/...)

P1 범위 (IMPLEMENTATION.md):
    - Registry/decorator 인프라
    - `explicit_factors` 1개 등록 (단일 캡 골든 케이스용)
    - components/curve/direction 헬퍼

P2+ 범위 (본 파일 미구현 — TODO 주석으로 진입로만 표시):
    - per_cap, circuit_group, cap_combination, curve_library resolver
    - csv kind materializer
    - components_ref 외부화
    - max_doe_count 가드 (보강 결정 H)

Nuitka 호환:
    - 동적 import (importlib/pkgutil) 사용 0
    - 데코레이터는 모듈 import 시점에 1회 실행되어 `_VIBRATION_PARSERS` 채움
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 1. 정규화 산출물 — VibrationLoadSpec
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VibrationLoadSpec:
    """진동 하중 단일 정규화 표현.

    L3 (VibrationSource) 의 유일한 export 타입. L4 (StepConfigBuilder) 가
    본 dataclass 만 입력으로 받아 step_config 텍스트로 직렬화한다.

    Attributes:
        direction: 가진 방향. "X" | "Y" | "Z" (대문자 정규화 완료).
        load_type: "Force" | "Acceleration". KooMeshModifier 의
            *LOAD_BODY_PARTS_<dir> 카드 선택 키.
        relative_mode: "Explicit" | "VolumeProportional" 등. 파트별 가중치
            분배 모드. (P1 은 "Explicit" 만 사용)
        load_curve: 시간-진폭 페어 리스트 [(t0, v0), (t1, v1), ...].
            materialize_curve() 가 kind 무관 동일 포맷으로 반환.
        part_factors: [(pid, factor), ...] — RelativeMode=Explicit 시 사용.
            None 이면 part_list 기반 균등 분배.
            (DOE 첫 번째 케이스의 part_factors — 단일 DOE 호환 진입로)
        part_list: [pid, ...] — RelativeMode=VolumeProportional 시 사용.
        reference_part: VolumeProportional 의 기준 PID. None 이면 첫 파트.
        doe_factors_list: [(case_name, [(pid, factor), ...]), ...] — DOE 케이스 목록.
            P1 explicit_factors: 길이 1 (단일 명시 조합).
            P2 per_cap: 길이 N (cap별 단독 가진).
            P2 circuit_group: 길이 N (group 멤버 일괄 가진).
            CumulativeDesigner._process_vibration_scenario 가 본 필드 길이로
            DOE 개수를 결정하며, save_runner_config 가 case_name/factors 로
            doe_vibrations 카탈로그를 생성한다.
    """

    direction: str
    load_type: str
    relative_mode: str
    load_curve: List[Tuple[float, float]]
    part_factors: Optional[List[Tuple[int, float]]] = None
    part_list: Optional[List[int]] = None
    reference_part: Optional[int] = None
    doe_factors_list: Any = ()
    doe_names: Optional[List[str]] = None

    @property
    def doe_count(self) -> int:
        """DOE 케이스 수 (doe_factors_list 길이). 비어 있으면 1 (단일 명시)."""
        return len(self.doe_factors_list) if self.doe_factors_list else 1


@dataclass
class VibrationContext:
    """parse 시점 컨텍스트.

    Registry 함수에 공통으로 전달되는 호출 환경. 추후 P3 의
    `max_doe_count` 가드 (보강 결정 H) 와 컴포넌트 외부 registry 경로
    해석에 사용된다. P1 에서는 components 만 활용.

    Attributes:
        components: 컴포넌트 메타 사전 (PID, 회로 그룹 등). v1 은 inline.
        scenario_dir: scenario.json 의 위치 (상대 경로 해석용, 미사용 가능).
        max_doe_count: DOE 폭증 가드 임계 (P3 도입 예정).
    """

    components: Dict[str, Any] = field(default_factory=dict)
    scenario_dir: Optional[str] = None
    max_doe_count: int = 500  # 보강 결정 H — P3 에서 가드 적용 예정


# ---------------------------------------------------------------------------
# 2. Registry + Decorator (채택안 A)
# ---------------------------------------------------------------------------

# 모듈 전역 registry — 데코레이터가 import 시점에 정적으로 채움.
# Nuitka 컴파일 산출물에서도 동일하게 동작 (Verify1-Q2 확인).
_VIBRATION_PARSERS: Dict[str, Callable[[dict, VibrationContext], VibrationLoadSpec]] = {}


def register_vibration_source(name: str) -> Callable:
    """진동 source resolver 등록 데코레이터.

    사용:
        @register_vibration_source("explicit_factors")
        def _parse_explicit_factors(config, ctx): ...

    Args:
        name: scenario.json `source_type` 값과 일치하는 registry 키.

    Returns:
        decorator — 원본 함수를 그대로 반환 (래핑 없음).

    Raises:
        RuntimeError: 동일 name 이 중복 등록될 때 (조용한 덮어쓰기 방지).
    """

    def deco(fn: Callable) -> Callable:
        if name in _VIBRATION_PARSERS:
            raise RuntimeError(f"Duplicate vibration source: {name}")
        _VIBRATION_PARSERS[name] = fn
        return fn

    return deco


def parse_vibration_source(config: dict, ctx: VibrationContext) -> VibrationLoadSpec:
    """`vibration_source` 블록을 정규화된 VibrationLoadSpec 으로 변환.

    Args:
        config: scenario.json 의 `vibration_source` 객체.
        ctx: 호출 컨텍스트 (components, max_doe_count 등).

    Returns:
        VibrationLoadSpec — L4 직렬화 입력.

    Raises:
        ValueError: source_type 누락 또는 미등록 시. 미등록 시 가능한 키
            카탈로그를 메시지에 포함 ("Registered: [...]").
    """
    src = config.get("source_type")
    if src is None:
        raise ValueError(
            f"vibration_source.source_type is required. "
            f"Registered: {sorted(_VIBRATION_PARSERS)}"
        )
    if src not in _VIBRATION_PARSERS:
        raise ValueError(
            f"Unknown vibration source_type: {src!r}. "
            f"Registered: {sorted(_VIBRATION_PARSERS)}"
        )
    return _VIBRATION_PARSERS[src](config, ctx)


def list_registered_sources() -> List[str]:
    """등록된 source_type 목록 반환 (smoke test / CLI 조회용)."""
    return sorted(_VIBRATION_PARSERS)


# ---------------------------------------------------------------------------
# 3. 공용 헬퍼 — direction / curve / components
# ---------------------------------------------------------------------------

# 채택안 F: solver 측 (KooVibrationLoad.py L33–34) 가 X/Y/Z만 hard validate
_VALID_DIRECTIONS = ("X", "Y", "Z")


def validate_direction(direction: Any) -> str:
    """direction 값 검증 + 정규화.

    P1 은 axis string ("X"/"Y"/"Z") 만 지원. 향후 vector 입력
    ({"axis": [...]}) hook 은 schema 에 예약되어 있으나 본 함수는 string
    경로만 검사한다 (채택안 F).

    Args:
        direction: scenario.json 의 direction 필드값.

    Returns:
        대문자 정규화된 "X" | "Y" | "Z".

    Raises:
        ValueError: 미지원 타입 또는 값.
    """
    if isinstance(direction, str):
        d = direction.upper()
        if d not in _VALID_DIRECTIONS:
            raise ValueError(
                f"direction must be one of {_VALID_DIRECTIONS}, got: {direction!r}"
            )
        return d
    # TODO(P?): vector 입력 {"axis": [x,y,z]} → 자동 축 결정 hook.
    # 솔버 (*LOAD_BODY_PARTS_<dir>) 가 축 한정이므로 P1 에서는 미지원.
    raise ValueError(
        f"direction must be a string ('X'|'Y'|'Z'), got: {type(direction).__name__}"
    )


# 채택안 G: base_curve.kind discriminated union.
# inline 만 P1 구현. csv/analytic/library_ref/composite 는 hook 예약.
_CURVE_MATERIALIZERS: Dict[str, Callable[[dict, VibrationContext], List[Tuple[float, float]]]] = {}


def _register_curve_kind(kind: str) -> Callable:
    """내부 curve kind dispatch 등록 데코레이터.

    `register_vibration_source` 와 동일 패턴 — Nuitka 안전 정적 등록.
    """

    def deco(fn: Callable) -> Callable:
        if kind in _CURVE_MATERIALIZERS:
            raise RuntimeError(f"Duplicate curve kind: {kind}")
        _CURVE_MATERIALIZERS[kind] = fn
        return fn

    return deco


@_register_curve_kind("inline")
def _materialize_inline(curve: dict, ctx: VibrationContext) -> List[Tuple[float, float]]:
    """`{"kind": "inline", "points": [[t, v], ...]}` → [(t, v), ...]."""
    points = curve.get("points")
    if not points or len(points) < 2:
        raise ValueError("base_curve(inline) requires 'points' with >= 2 entries")
    out: List[Tuple[float, float]] = []
    for i, pt in enumerate(points):
        if len(pt) != 2:
            raise ValueError(
                f"base_curve.points[{i}] must be [t, value] pair, got: {pt!r}"
            )
        out.append((float(pt[0]), float(pt[1])))
    return out


# TODO(P2+): csv kind materializer.
# @_register_curve_kind("csv")
# def _materialize_csv(curve, ctx):
#     # path/t_col/v_col/skiprows 로 numpy.loadtxt 또는 csv.reader
#     ...

# TODO(P?+): analytic / library_ref / composite hooks.


def materialize_curve(curve: dict, ctx: VibrationContext) -> List[Tuple[float, float]]:
    """base_curve 를 kind 무관 동일 포맷 [(t, v), ...] 으로 materialize.

    Args:
        curve: scenario.json 의 `base_curve` 객체. `kind` 필드 필수.
        ctx: csv 경로 해석 등에 사용 (P1 inline 만).

    Returns:
        [(time, value), ...] 시간 오름차순 페어 리스트.

    Raises:
        ValueError: kind 누락/미지원 시. 메시지에 등록 카탈로그 포함.
    """
    if not isinstance(curve, dict):
        raise ValueError(f"base_curve must be an object, got: {type(curve).__name__}")
    kind = curve.get("kind")
    if kind is None:
        raise ValueError(
            f"base_curve.kind is required. "
            f"Supported kinds: {sorted(_CURVE_MATERIALIZERS)}"
        )
    if kind not in _CURVE_MATERIALIZERS:
        raise ValueError(
            f"Unknown base_curve.kind: {kind!r}. "
            f"Supported kinds: {sorted(_CURVE_MATERIALIZERS)}"
        )
    return _CURVE_MATERIALIZERS[kind](curve, ctx)


def resolve_components(config: dict, ctx: VibrationContext) -> Dict[str, Any]:
    """components 정의 해석 (inline 우선, $ref 진입로만 예약).

    채택안 E: 시나리오 ≤ 50 → inline 시작. v1 은 inline 만 처리하되
    `components_ref` / `components_override` 필드는 schema 에 정의되어
    있으므로 호환 hook 만 둔다.

    Args:
        config: vibration_source 블록.
        ctx: 외부 registry 경로 해석에 사용 (P2+).

    Returns:
        components 사전. 없으면 빈 dict (P1 explicit_factors 는 미사용).
    """
    if "components" in config:
        comps = config["components"]
        if not isinstance(comps, dict):
            raise ValueError(
                f"vibration_source.components must be an object, "
                f"got: {type(comps).__name__}"
            )
        return comps
    # TODO(P2+): components_ref 외부 파일 로드 + components_override 병합.
    # ref_path = config.get("components_ref")
    # if ref_path: ... load from file relative to ctx.scenario_dir ...
    return {}


# ---------------------------------------------------------------------------
# 4. P1 등록 — explicit_factors
# ---------------------------------------------------------------------------

@register_vibration_source("explicit_factors")
def _parse_explicit_factors(config: dict, ctx: VibrationContext) -> VibrationLoadSpec:
    """`explicit_factors` resolver — 사용자 명시 [(pid, factor), ...] 그대로 사용.

    scenario.json 예시:
        "vibration_source": {
            "source_type": "explicit_factors",
            "direction": "Z",
            "load_type": "Force",
            "explicit_factors": [[101, 1.0], [102, 0.7]],
            "base_curve": {"kind": "inline",
                           "points": [[0, 0], [0.001, 1000], [0.02, 0]]}
        }

    P1 골든 케이스 (Example A `scenario_A_single_cap.json`) 의 최소 표현.
    P2 의 `per_cap` / `circuit_group` 는 components 메타에서 PID 를 lookup
    한 뒤 본 함수와 동일한 정규화 산출물을 생성하게 된다.

    Args:
        config: vibration_source 블록.
        ctx: VibrationContext (P1 미활용).

    Returns:
        VibrationLoadSpec (relative_mode="Explicit", part_factors 채움).

    Raises:
        ValueError: 필수 키 누락 또는 항목 형식 오류.
    """
    # 채택안 F — direction
    direction = validate_direction(config.get("direction"))

    # load_type — solver 한정 (KooVibrationLoad.py)
    load_type = config.get("load_type", "Force")
    if load_type not in ("Force", "Acceleration"):
        raise ValueError(
            f"load_type must be 'Force' or 'Acceleration', got: {load_type!r}"
        )

    # explicit_factors — 본 resolver 의 핵심 입력
    # 두 입력 형태 모두 허용 (surgical, 사용자 시나리오 호환):
    #   (a) list 형태:  [[pid, factor], ...]
    #   (b) dict 형태:  {"part_factors": {"pid": factor, ...}}
    raw = config.get("explicit_factors")
    if not raw:
        raise ValueError(
            "vibration_source.explicit_factors required for "
            "source_type='explicit_factors' "
            "(expected: [[pid, factor], ...] or "
            "{'part_factors': {pid: factor, ...}})"
        )

    part_factors: List[Tuple[int, float]] = []
    if isinstance(raw, dict):
        pf_dict = raw.get("part_factors")
        if not pf_dict or not isinstance(pf_dict, dict):
            raise ValueError(
                "explicit_factors(dict 형태): 'part_factors' 키에 {pid: factor} "
                f"매핑이 필요합니다. got: {raw!r}"
            )
        for pid, factor in pf_dict.items():
            part_factors.append((int(pid), float(factor)))
    elif isinstance(raw, list):
        for i, item in enumerate(raw):
            if len(item) != 2:
                raise ValueError(
                    f"explicit_factors[{i}] must be [pid, factor] pair, got: {item!r}"
                )
            pid, factor = item
            part_factors.append((int(pid), float(factor)))
    else:
        raise ValueError(
            f"explicit_factors must be list or dict, got: {type(raw).__name__}"
        )

    # 채택안 G — base_curve materialize
    base_curve = config.get("base_curve")
    if base_curve is None:
        raise ValueError("vibration_source.base_curve is required")
    load_curve = materialize_curve(base_curve, ctx)

    # P1: explicit_factors 는 단일 DOE 케이스 — doe_factors_list 길이 1
    # case_name 은 사용자 지정(case_name) 또는 기본 "VIB_EXPLICIT".
    # P2 per_cap/circuit_group 은 동일 필드를 길이 N 으로 채우게 된다.
    case_name = str(config.get("case_name", "VIB_EXPLICIT"))
    doe_factors_list = ((case_name, tuple(part_factors)),)

    return VibrationLoadSpec(
        direction=direction,
        load_type=load_type,
        relative_mode="Explicit",
        load_curve=load_curve,
        part_factors=part_factors,
        doe_factors_list=doe_factors_list,
    )


# ---------------------------------------------------------------------------
# 5. P2+ 진입로 (TODO — 본 PR 미구현)
# ---------------------------------------------------------------------------

@register_vibration_source("per_cap")
def _parse_per_cap(config: dict, ctx: VibrationContext) -> VibrationLoadSpec:
    """`per_cap` resolver — cap PID 리스트 → 각 캡 1 DOE (N=len(cap_pids)).

    scenario.json 예시:
        "vibration_source": {
            "source_type": "per_cap",
            "direction": "Z",
            "load_type": "Force",
            "per_cap": {
                "cap_pids": [4, 5, 6, 7, 8],
                "amplitude": 1.0
            },
            "base_curve": {"kind": "inline",
                           "points": [[0, 0], [0.001, 1000], [0.02, 0]]}
        }

    각 cap PID 가 단독으로 가진되는 DOE 케이스 N 개를 생성한다.
    doe_factors_list 는 ((case_name, ((pid, amplitude),)), ...) 형태로,
    explicit_factors 와 동일한 정규화 산출물 구조를 따른다.
    part_factors 는 첫 DOE 케이스 (호환 진입로) 를 노출한다.

    Args:
        config: vibration_source 블록.
        ctx: VibrationContext (P2 미활용 — components 미참조).

    Returns:
        VibrationLoadSpec (relative_mode="Explicit", doe_factors_list 길이 N).

    Raises:
        ValueError: cap_pids 누락/비어있음 또는 필수 키 누락 시.
    """
    # 채택안 F — direction
    direction = validate_direction(config.get("direction"))

    # load_type
    load_type = config.get("load_type", "Force")
    if load_type not in ("Force", "Acceleration"):
        raise ValueError(
            f"load_type must be 'Force' or 'Acceleration', got: {load_type!r}"
        )

    # per_cap 블록 — 본 resolver 의 핵심 입력
    block = config.get("per_cap")
    if not block or not isinstance(block, dict):
        raise ValueError(
            "vibration_source.per_cap object required for "
            "source_type='per_cap' "
            "(expected: {'cap_pids': [...], 'amplitude': float})"
        )

    cap_pids = block.get("cap_pids")
    if not cap_pids or not isinstance(cap_pids, list):
        raise ValueError(
            f"per_cap.cap_pids must be a non-empty list, got: {cap_pids!r}"
        )
    amplitude = float(block.get("amplitude", 1.0))

    # 채택안 G — base_curve materialize
    base_curve = config.get("base_curve")
    if base_curve is None:
        raise ValueError("vibration_source.base_curve is required")
    load_curve = materialize_curve(base_curve, ctx)

    # DOE fan-out: 각 cap PID → 1 케이스, factors=((pid, amplitude),)
    # case_name 패턴: VIB_CAP_<pid> (CumulativeDesigner DOE 카탈로그용).
    doe_factors_list = tuple(
        (f"VIB_CAP_{int(pid)}", ((int(pid), amplitude),))
        for pid in cap_pids
    )

    # part_factors — 단일 DOE 호환 진입로 (첫 번째 DOE 케이스)
    first_factors: List[Tuple[int, float]] = list(doe_factors_list[0][1])

    return VibrationLoadSpec(
        direction=direction,
        load_type=load_type,
        relative_mode="Explicit",
        load_curve=load_curve,
        part_factors=first_factors,
        doe_factors_list=doe_factors_list,
    )

@register_vibration_source("circuit_group")
def _parse_circuit_group(config: dict, ctx: VibrationContext) -> VibrationLoadSpec:
    """`circuit_group` resolver — 회로별 일괄 amplitude → 각 회로 1 DOE.

    사용자 핵심 요구: 회로 단위 일괄 진동 (회로 내 모든 PID 가 동일 amplitude
    로 동기 가진). DOE 폭증 가드 불필요 (DOE 수 = 회로 수, 통상 ≤ 10).

    scenario.json 예시 (채택안 E — inline circuits):
        "vibration_source": {
            "source_type": "circuit_group",
            "direction": "Z",
            "load_type": "Force",
            "circuit_group": {
                "circuits": {
                    "C1_power":  {"parts": [4, 5, 6],    "amplitude": 1.0},
                    "C2_signal": {"parts": [9, 10, 11],  "amplitude": 0.5},
                    "C3_motor":  {"parts": [18],         "amplitude": 2.0}
                }
            },
            "base_curve": {"kind": "inline",
                           "points": [[0, 0], [0.001, 1000], [0.02, 0]]}
        }

    각 회로가 1개의 DOE 케이스가 되며, 회로 내 모든 part 가 동일 amplitude
    로 가진된다. doe_factors_list 는 회로별 {pid: amplitude} dict 리스트로
    구성되고, 회로 이름은 doe_names 에 별도 보존 (alias 토큰).

    Args:
        config: vibration_source 블록.
        ctx: VibrationContext (P2 미활용).

    Returns:
        VibrationLoadSpec.
            doe_count = len(circuits)
            doe_factors_list = [{pid: amp, ...}, ...]  (회로별 dict)
            doe_names = [circuit_name, ...]  (alias 생성용)

    Raises:
        ValueError: circuit_group.circuits 누락/비어있음, 필수 키 누락 시.
    """
    # circuit_group 블록 — 본 resolver 의 핵심 입력
    block = config.get("circuit_group", {})
    circuits = block.get("circuits", {})
    if not circuits or not isinstance(circuits, dict):
        raise ValueError(
            f"circuit_group.circuits must be a non-empty dict, got: {circuits!r}"
        )

    # 채택안 F — direction
    direction = validate_direction(config.get("direction", "Z"))

    # load_type — solver 한정
    load_type = config.get("load_type", "Force")
    if load_type not in ("Force", "Acceleration"):
        raise ValueError(
            f"load_type must be 'Force' or 'Acceleration', got: {load_type!r}"
        )

    relative_mode = config.get("relative_mode", "Explicit")

    # 채택안 G — base_curve materialize (기본값 0 곡선)
    curve_cfg = config.get("base_curve", {"kind": "inline", "points": [[0.0, 0.0]]})
    load_curve = materialize_curve(curve_cfg, ctx)

    # 각 회로 → 1 DOE: (case_name, ((pid, amplitude), ...))
    # per_cap / explicit_factors 와 동일 정규화 산출물 구조 (CumulativeDesigner 통합 진입로).
    doe_factors_pairs: List[Tuple[str, Tuple[Tuple[int, float], ...]]] = []
    for circuit_name, circuit_def in circuits.items():
        parts = circuit_def.get("parts", [])
        amplitude = float(circuit_def.get("amplitude", 1.0))
        if not parts:
            raise ValueError(f"circuit '{circuit_name}' has empty parts list")
        part_factors = tuple((int(pid), amplitude) for pid in parts)
        doe_factors_pairs.append((f"VIB_{circuit_name}", part_factors))

    doe_factors_list = tuple(doe_factors_pairs)

    # part_factors — 단일 DOE 호환 진입로 (첫 번째 DOE 케이스)
    first_factors: List[Tuple[int, float]] = list(doe_factors_list[0][1])

    return VibrationLoadSpec(
        direction=direction,
        load_type=load_type,
        relative_mode=relative_mode,
        load_curve=load_curve,
        part_factors=first_factors,
        doe_factors_list=doe_factors_list,
    )

# TODO(P3): cap_combination resolver — C(N, k) 조합 폭증 → max_doe_count 가드
# @register_vibration_source("cap_combination")
# def _parse_cap_combination(config, ctx) -> VibrationLoadSpec:
#     """cap_pool + select_k → C(N, k) 조합. DOE 폭증 시 ctx.max_doe_count 로 abort."""
#     ...

# TODO(P?+): curve_library resolver — 외부 곡선 사전 lookup
# @register_vibration_source("curve_library")
# def _parse_curve_library(config, ctx) -> VibrationLoadSpec:
#     ...
