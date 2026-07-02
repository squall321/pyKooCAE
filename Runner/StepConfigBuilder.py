"""
StepConfigBuilder - DROP_ATTITUDE step_config 생성 공통 모듈

cumulative와 large-scale 모드에서 동일한 옵션으로 step_config를 생성합니다.
접촉 설정, D2R, OptCard 등 모든 최신 기능이 양쪽에 동일하게 적용됩니다.
"""


def build_drop_attitude_config(
    model_file: str,
    output_dir: str,
    project: str,
    doe_index: int,
    step_num: int,
    mode: str,
    condition: str,
    euler: dict,
    sim_params: dict,
    run_directory_mode: bool = True,
    preserve_includes: list = None,
) -> str:
    """DROP_ATTITUDE step_config 내용 생성

    Args:
        model_file: 입력 모델 파일 경로
        output_dir: 출력 디렉토리
        project: 프로젝트 이름
        doe_index: DOE 번호
        step_num: Step 번호
        mode: 모드 (DROP, IMPACT 등)
        condition: 조건 문자열
        euler: {'roll': float, 'pitch': float, 'yaw': float}
        sim_params: simulation_params dict
        run_directory_mode: RunDirectoryMode 활성화 여부

    Returns:
        step_config 파일 내용 문자열
    """
    # simulation_params에서 값 가져오기
    # Unit system: [tonne, mm, s, MPa] — matches the rest of the deck
    # (height in mm, tFinal in s). Steel ref: ρ=7.85e-9, E=2.0e5.
    tFinal = sim_params.get("tFinal", 0.005)               # s
    dt = sim_params.get("dt", 0.000001)                    # s
    density = sim_params.get("density", 7.85e-9)            # tonne/mm³
    youngs_modulus = sim_params.get("youngs_modulus", 2.0e5)  # MPa
    poisson_ratio = sim_params.get("poisson_ratio", 0.3)
    sim_height = sim_params.get("height", 1500)            # mm
    offset_distance = sim_params.get("offset_distance", 0.05)

    # drop_surface 설정
    drop_surface = sim_params.get("drop_surface", {})
    ds_type = drop_surface.get("type", "Plane")
    if ds_type == "RigidWall":
        drop_surface_line = "DropSurface,RigidWall,0,0,0,0,0,0"
    elif ds_type == "PlaneGraded":
        ds_size = drop_surface.get("size", [200, 200, 20])
        ds_mesh = drop_surface.get("mesh", [10, 10, 2])
        num_outer = drop_surface.get("num_outer_layers", 5)
        graded_ratio = drop_surface.get("ratio", 1.5)
        drop_surface_line = f"DropSurface,PlaneGraded,{ds_size[0]},{ds_size[1]},{ds_size[2]},{ds_mesh[0]},{ds_mesh[1]},{ds_mesh[2]},{num_outer},{graded_ratio}"
    else:
        ds_size = drop_surface.get("size", [300, 300, 20])
        ds_mesh = drop_surface.get("mesh", [30, 30, 2])
        drop_surface_line = f"DropSurface,{ds_type},{ds_size[0]},{ds_size[1]},{ds_size[2]},{ds_mesh[0]},{ds_mesh[1]},{ds_mesh[2]}"
    if ds_type == "PlanewithRoughness":
        roughness = drop_surface.get("roughness_mode", "Random")
        r_max = drop_surface.get("r_max", 0.0)
        sf1 = drop_surface.get("shape_factor", 0.0)
        sf2 = drop_surface.get("shape_factor2", sf1)
        drop_surface_line += f",{roughness},{r_max},{sf1},{sf2}"

    # DeformableToRigid 옵션
    d2r_enabled = drop_surface.get("deformable_to_rigid", False)
    d2r_line = "\nDeformableToRigid,True" if d2r_enabled else ""

    # 누적 스텝 간 DR 안정화: dynaintoinitial.txt 에 DynamicRelaxation 옵션을 쓰게 하여
    # 다음 낙하 deck 에 *CONTROL_DYNAMIC_RELAXATION 이 실리도록 함 (기본 off = 기존 동작)
    # 값: true(간단형) 또는 {enabled, nrcyck, drtol, drfctr, drterm} 객체형.
    # 기본 drtol=0.01 — 잔류응력 릴리즈 진동은 LS-DYNA 기본(0.001)로는 수렴 불가라 완화.
    # 기본 drterm=tFinal — 미수렴이어도 pseudo-time 예산 소진 후 transient 진입(bounded DR).
    dr_cfg = sim_params.get("dynamic_relaxation", False)
    if isinstance(dr_cfg, dict):
        dr_enabled = bool(dr_cfg.get("enabled", True))
        dr_nrcyck = int(dr_cfg.get("nrcyck", 250))
        dr_tol = float(dr_cfg.get("drtol", 0.01))
        dr_fctr = float(dr_cfg.get("drfctr", 0.995))
        dr_term = float(dr_cfg.get("drterm", 0.0)) or tFinal
    else:
        dr_enabled = bool(dr_cfg)
        dr_nrcyck, dr_tol, dr_fctr, dr_term = 250, 0.01, 0.995, tFinal
    dr_line = ""
    if dr_enabled:
        dr_line = (f"\nDynainDynamicRelaxation,True"
                   f"\nDynainDynamicRelaxationNrcyck,{dr_nrcyck}"
                   f"\nDynainDynamicRelaxationTol,{dr_tol}"
                   f"\nDynainDynamicRelaxationFctr,{dr_fctr}"
                   f"\nDynainDynamicRelaxationTerm,{dr_term}")

    # Contact 처리 옵션
    convert_to_ss = sim_params.get("convert_general_to_single_surface", True)
    ensure_ss = sim_params.get("ensure_single_surface", False)
    decompose_general = sim_params.get("decompose_general_contact", False)
    robust_contact = sim_params.get("robust_contact", False)
    include_wall_in_general = sim_params.get("include_wall_in_general", False)
    decompose_margin = sim_params.get("decompose_contact_margin", 1.5)
    decompose_abs_margin_x = sim_params.get("decompose_contact_absolute_margin_x", 5.0)
    decompose_abs_margin_y = sim_params.get("decompose_contact_absolute_margin_y", 5.0)
    decompose_abs_margin_z = sim_params.get("decompose_contact_absolute_margin_z", 0.5)
    contact_opt_line = ""
    if not convert_to_ss:
        contact_opt_line += "\nConvertGeneralToSingleSurface,False"
    if ensure_ss:
        contact_opt_line += "\nEnsureSingleSurface,True"
    if decompose_general:
        contact_opt_line += "\nDecomposeGeneralContact,True"
    if decompose_margin != 1.5:
        contact_opt_line += f"\nDecomposeContactMargin,{decompose_margin}"
    if decompose_abs_margin_x != 5.0:
        contact_opt_line += f"\nDecomposeContactAbsoluteMarginX,{decompose_abs_margin_x}"
    if decompose_abs_margin_y != 5.0:
        contact_opt_line += f"\nDecomposeContactAbsoluteMarginY,{decompose_abs_margin_y}"
    if decompose_abs_margin_z != 0.5:
        contact_opt_line += f"\nDecomposeContactAbsoluteMarginZ,{decompose_abs_margin_z}"
    if robust_contact:
        contact_opt_line += "\nRobustContact,True"
        rc_tolerance = sim_params.get("robust_contact_tolerance", 0.1)
        if rc_tolerance != 1.0:
            contact_opt_line += f"\nRobustContactTolerance,{rc_tolerance}"
    if include_wall_in_general:
        contact_opt_line += "\nIncludeWallInGeneral,True"
    non_reflecting = sim_params.get("non_reflecting_boundary", False)
    if non_reflecting:
        contact_opt_line += "\nNonReflectingBoundary,True"
    rigidify_dt = sim_params.get("rigidify_small_dt_threshold", 0.0)
    if rigidify_dt > 0:
        contact_opt_line += f"\nRigidifySmallDtThreshold,{rigidify_dt}"
    rigidify_ar = sim_params.get("rigidify_max_aspect_ratio", 0.0)
    if rigidify_ar > 0:
        contact_opt_line += f"\nRigidifyMaxAspectRatio,{rigidify_ar}"
    rigidify_eids = sim_params.get("rigidify_element_ids", [])
    if rigidify_eids:
        contact_opt_line += "\nRigidifyElementIDs," + ",".join(str(e) for e in rigidify_eids)

    # Tied 접촉 옵션
    tied_options = sim_params.get("tied_options", {})
    tied_opt_line = ""
    for key, val in tied_options.items():
        tied_opt_line += f"\nTiedOptions.{key},{val}"

    # 바닥판 접촉 옵션
    drop_contact = sim_params.get("drop_contact", {})
    drop_contact_line = ""
    for key, val in drop_contact.items():
        drop_contact_line += f"\nDropContact.{key},{val}"

    # CONTROL 카드 override (*CONTROL_TIMESTEP TSSFAC/DT2MS/ERODE…, *CONTROL_HOURGLASS IHQ/QH)
    control_line = ""
    for key, val in sim_params.get("control_timestep", {}).items():
        control_line += f"\nControlTimestep.{key},{val}"
    for key, val in sim_params.get("control_hourglass", {}).items():
        control_line += f"\nControlHourglass.{key},{val}"

    # RunDirectoryMode
    if run_directory_mode:
        run_dir_line = f"*RunDirectoryMode,True,{output_dir}"
    else:
        run_dir_line = "*RunDirectoryMode,False"

    # PreserveIncludes 블록 (사용자 지정 보존 패턴)
    preserve_block = ""
    if preserve_includes:
        preserve_lines = "\n".join(p for p in preserve_includes if p)
        if preserve_lines:
            preserve_block = f"*PreserveIncludes\n{preserve_lines}\n"

    config_content = f"""*Inputfile
{model_file}
{run_dir_line}
*Info,{project},Step{step_num}
*Description,DOE{doe_index:03d} Step{step_num} {mode} {condition}
*Creator,automation,auto@system.com,CAE,AUTO
{preserve_block}*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,{euler['roll']}
EulerPitching,{euler['pitch']}
EulerYawing,{euler['yaw']}
Height,{sim_height}
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
InitialAngularVelocityX,0
InitialAngularVelocityY,0
InitialAngularVelocityZ,0
OffsetDistance,{offset_distance}
Density,{density}
YoungsModulus,{youngs_modulus}
PoissonRatio,{poisson_ratio}
tFinal,{tFinal}
dt,{dt}
{drop_surface_line}{d2r_line}{dr_line}{contact_opt_line}{drop_contact_line}{tied_opt_line}{control_line}
**EndDropAttitude
*End
"""
    return config_content


# =============================================================================
# VIBRATION_LOAD 모드 — Registry-based zero-hardcode builder
# =============================================================================
#
# 설계 원칙 (design_decisions.md 채택안 A~G 준수):
#   - (A) 모드 이름은 단일 카탈로그 `_VIB_KEYWORDS`에서만 관리
#   - (B) 옵션 키는 `_VIB_OPTION_KEYS` mapping table로 명시적 선언
#   - (C) Relative 모드별 직렬화는 `_VIB_SERIALIZERS` decorator registry로 등록
#   - (D) 기존 build_drop_attitude_config와 시그니처/헤더 패턴 대칭 유지
#   - (E) sub-block (LoadCurve/PartFactors/PartList)은 Key...EndKey 규약 따름
#   - (F) Validation은 호출자 책임 (헤더 docstring에 명시)
#   - (G) P2 확장점(per_cap / circuit_group)은 TODO 주석으로 placeholder 표기
#
# 헤더 외부 directive(`*Inputfile`, `*RunDirectoryMode`, `*Info` 등) 패턴은
# build_drop_attitude_config와 동일하게 유지 — KooMeshModifier step_config 포맷 규칙.

# 모드 이름 카탈로그 (단일 사실원천)
_VIB_KEYWORDS = {
    "mode_name": "VIBRATION_LOAD",     # *Mode 다음 줄에 들어가는 모드 식별자
    "block_open": "VibrationLoad",     # **VibrationLoad,<idx>
    "block_close": "EndVibrationLoad", # **EndVibrationLoad
    "sub_load_curve": "LoadCurve",     # LoadCurve ... EndLoadCurve
    "sub_part_factors": "PartFactors", # PartFactors ... EndPartFactors  (P1: explicit)
    "sub_part_list": "PartList",       # PartList ... EndPartList        (P2: volume-proportional)
}

# VibrationLoad 블록 내부 Key,Value 옵션 카탈로그
# (config_key, sim_params_key 또는 직접 인자명, default)
# — sim_params나 직접 인자에서 값을 가져올 키를 명시
_VIB_OPTION_KEYS = (
    # config_key,         arg_name,         default
    ("Direction",         "direction",      "Z"),
    ("LoadType",          "load_type",      "Force"),
    ("RelativeMode",      "relative_mode",  "Explicit"),
)

# Relative mode 별 직렬화 함수 레지스트리 (decorator로 등록)
_VIB_SERIALIZERS = {}


def _register_vib_serializer(relative_mode: str):
    """relative_mode → 직렬화 함수 등록 데코레이터.

    각 직렬화 함수 시그니처: (load_curve, part_factors, part_list, reference_part) -> str
    반환: 블록 내부에 삽입할 sub-block 문자열 (앞쪽 개행 포함, 끝 개행 없음).
    """
    def _decorator(fn):
        _VIB_SERIALIZERS[relative_mode] = fn
        return fn
    return _decorator


def _format_load_curve_block(load_curve: list) -> str:
    """LoadCurve sub-block 직렬화.

    포맷:
        LoadCurve
        <t1>,<v1>
        <t2>,<v2>
        ...
        EndLoadCurve
    """
    open_kw = _VIB_KEYWORDS["sub_load_curve"]
    close_kw = "End" + open_kw
    lines = [open_kw]
    for t, v in load_curve:
        lines.append(f"{t},{v}")
    lines.append(close_kw)
    return "\n".join(lines)


@_register_vib_serializer("Explicit")
def _serialize_explicit(load_curve, part_factors, part_list, reference_part) -> str:
    """Explicit relative_mode: LoadCurve + PartFactors 직렬화 (P1 범위).

    파트별 가중치를 사용자가 직접 명시 — sim_params에서 (pid, factor) 튜플 리스트로 받음.
    """
    if not load_curve:
        raise ValueError("VibrationLoad/Explicit: load_curve가 비어 있습니다.")
    if not part_factors:
        raise ValueError("VibrationLoad/Explicit: part_factors가 비어 있습니다.")

    block = "\n" + _format_load_curve_block(load_curve)

    pf_open = _VIB_KEYWORDS["sub_part_factors"]
    pf_close = "End" + pf_open
    block += "\n" + pf_open
    for pid, factor in part_factors:
        block += f"\n{pid},{factor}"
    block += "\n" + pf_close
    return block


# TODO(P2): per_cap_factors 직렬화 — Cap 단위 자동 가중치 계산
# @_register_vib_serializer("PerCap")
# def _serialize_per_cap(...): ...

# TODO(P2): circuit_group_factors 직렬화 — Circuit Group 단위 가중치
# @_register_vib_serializer("CircuitGroup")
# def _serialize_circuit_group(...): ...

# TODO(P2): VolumeProportional 직렬화 — PartList + reference_part 기반 부피 비례
# @_register_vib_serializer("VolumeProportional")
# def _serialize_volume_proportional(...): ...


def build_vibration_load_config(
    model_file: str,
    output_dir: str,
    project: str,
    doe_index: int,
    step_num: int,
    condition: str,
    direction: str,
    load_type: str,
    relative_mode: str,
    load_curve: list,
    part_factors: list = None,
    part_list: list = None,
    reference_part: int = None,
    run_directory_mode: bool = True,
    preserve_includes: list = None,
) -> str:
    """VIBRATION_LOAD step_config 내용 생성 (build_drop_attitude_config와 대칭).

    Args:
        model_file: 입력 모델 파일 경로
        output_dir: 출력 디렉토리
        project: 프로젝트 이름
        doe_index: DOE 번호
        step_num: Step 번호
        condition: 조건 문자열 (Description에 사용)
        direction: 가진 방향 "X" | "Y" | "Z"
        load_type: "Force" | "Acceleration"
        relative_mode: "Explicit" | "VolumeProportional" | "PerCap" | "CircuitGroup"
            (P1에서는 "Explicit"만 구현, 나머지는 P2 — 미등록 모드 호출 시 ValueError)
        load_curve: [(time, value), ...] — Load curve 데이터 (필수)
        part_factors: [(pid, factor), ...] — Explicit mode 전용 (P1)
        part_list: [pid, ...] — VolumeProportional mode 전용 (P2 예정)
        reference_part: int — VolumeProportional mode 전용 (P2 예정)
        run_directory_mode: RunDirectoryMode 활성화 여부
        preserve_includes: 보존할 include 패턴 리스트 (옵션)

    Returns:
        step_config 파일 내용 문자열

    Raises:
        ValueError: 등록되지 않은 relative_mode이거나 필수 데이터 누락 시.

    Note:
        - 헤더 부분(`*Inputfile`/`*RunDirectoryMode`/`*Info`/`*Description`/`*Creator`/
          `*PreserveIncludes`)는 build_drop_attitude_config와 동일 패턴.
        - 블록 내부는 `Key,Value` 라인 + sub-block(`LoadCurve...EndLoadCurve` 등).
        - 검증(Direction이 X/Y/Z인지, load_type이 Force/Acceleration인지 등)은
          호출자(scenario validator) 책임 — 본 함수는 직렬화만 담당.
    """
    # Relative mode 직렬화 함수 lookup (Registry 패턴)
    if relative_mode not in _VIB_SERIALIZERS:
        registered = sorted(_VIB_SERIALIZERS.keys())
        raise ValueError(
            f"VibrationLoad: 지원하지 않는 relative_mode='{relative_mode}'. "
            f"등록된 모드: {registered} (P2에서 추가 예정: PerCap, CircuitGroup, VolumeProportional)"
        )

    # 옵션 키 직렬화 (mapping table 기반)
    # — _VIB_OPTION_KEYS에 선언된 키들을 인자값으로 치환하여 Key,Value 라인 생성
    _arg_values = {
        "direction": direction,
        "load_type": load_type,
        "relative_mode": relative_mode,
    }
    option_lines = []
    for config_key, arg_name, default in _VIB_OPTION_KEYS:
        value = _arg_values.get(arg_name, default)
        if value is None:
            value = default
        option_lines.append(f"{config_key},{value}")
    options_block = "\n".join(option_lines)

    # Relative mode 별 sub-block 직렬화 (LoadCurve + PartFactors/PartList 등)
    serializer = _VIB_SERIALIZERS[relative_mode]
    sub_block = serializer(load_curve, part_factors, part_list, reference_part)

    # RunDirectoryMode (build_drop_attitude_config와 동일 패턴)
    if run_directory_mode:
        run_dir_line = f"*RunDirectoryMode,True,{output_dir}"
    else:
        run_dir_line = "*RunDirectoryMode,False"

    # PreserveIncludes 블록 (build_drop_attitude_config와 동일 패턴)
    preserve_block = ""
    if preserve_includes:
        preserve_lines = "\n".join(p for p in preserve_includes if p)
        if preserve_lines:
            preserve_block = f"*PreserveIncludes\n{preserve_lines}\n"

    # Mode 이름 카탈로그에서 가져오기 (단일 사실원천)
    mode_name = _VIB_KEYWORDS["mode_name"]
    block_open = _VIB_KEYWORDS["block_open"]
    block_close = _VIB_KEYWORDS["block_close"]

    config_content = f"""*Inputfile
{model_file}
{run_dir_line}
*Info,{project},Step{step_num}
*Description,DOE{doe_index:03d} Step{step_num} VIBRATION_LOAD {condition}
*Creator,automation,auto@system.com,CAE,AUTO
{preserve_block}*Mode
{mode_name},1
**{block_open},1
{options_block}{sub_block}
**{block_close}
*End
"""
    return config_content


def build_dynain_to_initial_config(
    model_file: str,
    dynain_path: str,
    drop_part_id: int = None,
    drop_contact_id: int = None,
) -> str:
    """DYNAIN_TO_INITIAL step_config 내용 생성

    Args:
        model_file: 입력 모델 파일 경로
        dynain_path: dynain 파일 경로
        drop_part_id: 제거할 바닥판 part ID (None이면 생략)
        drop_contact_id: 제거할 바닥판 contact ID (None이면 생략)

    Returns:
        step_config 파일 내용 문자열
    """
    lines = [
        "*Inputfile",
        model_file,
        "*Mode",
        "DYNAIN_TO_INITIAL,1",
        "**DynainToInitial,1",
        f"**DynainPath,{dynain_path}",
        "*IncludeStress,True",
        "*RemoveDynamicRelaxation,True",
        "*MovetoOriginAutomatic,True",
    ]
    if drop_part_id is not None:
        lines.append(f"*RemovePartbyID,{drop_part_id}")
    if drop_contact_id is not None:
        lines.append(f"*RemoveContactbyID,{drop_contact_id}")
    lines.append("**EndDynainToInitial")
    lines.append("*End")
    return "\n".join(lines) + "\n"


# zero-hardcode 표준 명명 alias (DESIGN.md 채택안 B)
# 호출처는 build_vibration_load_config를 사용해도 되고 build_vibration_load_block을 사용해도 됨.
build_vibration_load_block = build_vibration_load_config
