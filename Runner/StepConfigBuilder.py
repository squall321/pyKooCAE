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
    tFinal = sim_params.get("tFinal", 0.005)
    dt = sim_params.get("dt", 0.000001)
    density = sim_params.get("density", 7850)
    youngs_modulus = sim_params.get("youngs_modulus", 200000000000)
    poisson_ratio = sim_params.get("poisson_ratio", 0.3)
    sim_height = sim_params.get("height", 1500)
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

    # RunDirectoryMode
    if run_directory_mode:
        run_dir_line = f"*RunDirectoryMode,True,{output_dir}"
    else:
        run_dir_line = "*RunDirectoryMode,False"

    config_content = f"""*Inputfile
{model_file}
{run_dir_line}
*Info,{project},Step{step_num}
*Description,DOE{doe_index:03d} Step{step_num} {mode} {condition}
*Creator,automation,auto@system.com,CAE,AUTO
*Mode
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
{drop_surface_line}{d2r_line}{contact_opt_line}{drop_contact_line}{tied_opt_line}
**EndDropAttitude
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
