"""
Cumulative Scenario Designer (Stage 1: Designer)

사용자 JSON 설정 → runner_config.json 생성

입력: 사용자 JSON 설정 파일
출력: runner_config.json (Executor가 읽는 실행 설정)

처리 과정:
    1. 각도 소스 파싱 (AngleSourceParser)
    2. Tolerance/DOE 적용 (ToleranceDOEGenerator)
    3. 각도 믹싱 전략 적용 (AngleMixingStrategy)
    4. 템플릿 자동 선택 (TemplateManager)
    5. runner_config.json 생성

Author: koo.park
Email: koo.park@samsung.com
Group: CAE
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

# Runner 모듈 임포트
from Runner.PathResolver import find_koomeshmodifier, find_kooremapper
from Runner.CaseTxtParser import DropAngle
from Runner.AngleSourceParser import (
    AngleSourceConfig, AngleSourceType,
    CuboidGeometryConfig, FibonacciLatticeConfig,
    PitchingSweepConfig, RollingSweepConfig, CaseTxtFileConfig,
    parse_angle_source
)
from Runner.ToleranceDOEGenerator import (
    ToleranceConfig, ToleranceRange, DOEType,
    apply_tolerance_doe
)
from Runner.AngleMixingStrategy import (
    CumulativeAngleConfig, MixingStrategy,
    generate_cumulative_angle_sequence
)
from Runner.TemplateManager import (
    SimulationMode, TemplateType,
    select_template_for_scenario
)
from Runner.ImpactPositionSource import (
    ImpactPosition, parse_position_source
)

# ── VIBRATION 모드 (P1: explicit_factors only) ────────────────────────────────
# VibrationSource 모듈은 별도 sub-task로 구현 예정.
# Import 실패 시(모듈 미구현 상태)에도 DROP/IMPACT 기존 경로는 영향받지 않도록
# try/except로 graceful import 처리. _process_vibration_scenario 호출 시점에만
# 부재가 표면화됨 (호출 직전 None 체크로 명시적 ImportError 재발생).
try:
    from Runner.VibrationSource import (
        VibrationLoadSpec, VibrationContext, parse_vibration_source
    )
except ImportError:
    VibrationLoadSpec = None
    VibrationContext = None
    parse_vibration_source = None


@dataclass
class StepConfig:
    """Step 설정 (runner_config.json용)"""
    step_number: int
    template: str
    mode: str
    angle_name: str
    angle_roll: float
    angle_pitch: float
    angle_yaw: float
    input_file: str
    output_dir: str
    dynain_source: Optional[str] = None
    doe_index: int = 0


@dataclass
class ScenarioConfig:
    """시나리오 설정 (runner_config.json용)"""
    scenario_id: str
    scenario_name: str
    total_steps: int
    steps: List[StepConfig]


@dataclass
class RunnerConfig:
    """Runner 설정 (runner_config.json)"""
    project_name: str
    base_dir: str
    scenarios: List[ScenarioConfig]
    environment: Dict[str, Any]
    simulation_params: Optional[Dict[str, Any]] = None
    postprocess: Optional[Dict[str, Any]] = None


class CumulativeDesigner:
    """누적 시뮬레이션 Designer"""

    def __init__(self, user_config: Dict[str, Any], scenario_dir: Optional[str] = None):
        """
        Parameters:
            user_config: 사용자 JSON 설정
            scenario_dir: scenario.json이 위치한 디렉토리 (template 상대경로 해석용)
        """
        self.user_config = user_config
        self.project_name = user_config.get("project_name", "CumulativeProject")
        self.base_dir = user_config.get("base_dir", os.getcwd())
        self.scenario_dir = scenario_dir or os.getcwd()

    def parse_user_config(self) -> RunnerConfig:
        """
        사용자 JSON → runner_config.json 변환

        Returns:
            RunnerConfig 객체
        """
        # 환경 설정
        environment = self.user_config.get("environment", {})

        # 실행 파일 경로 기본값 설정 (사용자가 override 가능)
        if "koomeshmodifier_path" not in environment:
            # PathResolver로 자동 탐색: 상대경로 → KOO_PATH → 설정 → 기본값
            environment["koomeshmodifier_path"] = find_koomeshmodifier()
        if "lsdyna_path" not in environment:
            environment["lsdyna_path"] = "/opt/lsdyna/bin/ls-dyna"
        # KooRemapper(REMAP 스텝)용 네이티브 바이너리 경로 (sif 내부 기본값, 자동 탐색)
        if "kooremapper_path" not in environment:
            environment["kooremapper_path"] = find_kooremapper()

        # 시나리오 설정
        scenarios_config = self.user_config.get("scenarios", [])
        scenarios = []

        for scenario_cfg in scenarios_config:
            scenario = self._process_scenario(scenario_cfg)
            scenarios.append(scenario)

        # simulation_params 가져오기 (없으면 None)
        simulation_params = self.user_config.get("simulation_params", None)

        # postprocess 옵션 (KooD3plotReader pipeline, 없으면 None)
        postprocess = self.user_config.get("postprocess", None)

        return RunnerConfig(
            project_name=self.project_name,
            base_dir=self.base_dir,
            scenarios=scenarios,
            environment=environment,
            simulation_params=simulation_params,
            postprocess=postprocess
        )

    def _process_scenario(self, scenario_cfg: Dict[str, Any]) -> ScenarioConfig:
        """
        개별 시나리오 처리

        Parameters:
            scenario_cfg: 시나리오 설정

        Returns:
            ScenarioConfig
        """
        scenario_name = scenario_cfg.get("scenario_name", "UnnamedScenario")
        # 사용자가 지정한 모델 파일 (template 필드) - 첫 시나리오만 저장
        # scenario.json 기준 상대경로 → 절대경로 변환
        if not hasattr(self, '_current_model_file') or not self._current_model_file:
            template_raw = scenario_cfg.get("template", "")
            if template_raw and not os.path.isabs(template_raw):
                template_abs = str(Path(self.scenario_dir) / template_raw)
            else:
                template_abs = template_raw
            self._current_model_file = template_abs

        # 누적 모드 및 스텝 수
        cumulative_cfg = scenario_cfg.get("cumulative", {})
        num_steps = cumulative_cfg.get("num_steps", 1)
        mode_sequence = self._parse_mode_sequence(cumulative_cfg, num_steps)

        # IMPACT 모드 여부 확인
        has_impact = any(m == SimulationMode.IMPACT for m in mode_sequence)
        # VIBRATION 모드 여부 확인
        # SimulationMode enum에는 VIB("VIB")와 VIBRATION("VIBRATION") 두 멤버가
        # 별도로 존재한다 (TemplateManager.py L34-35; long alias 정책 — DESIGN.md 채택안 C).
        # Enum 멤버는 value가 같지 않으면 별개 객체이므로 둘 다 명시적으로 체크.
        # (P1 잔여 버그: 이전엔 VIB만 체크하여 "VIBRATION" scenario는 _process_drop_scenario로
        #  폴백 → angle_source 기본값(cuboid_geometry 26방향) 적용되어 doe_count=26 발생)
        has_vibration = any(
            m in (SimulationMode.VIB, SimulationMode.VIBRATION) for m in mode_sequence
        )
        # THERM 모드 여부 (고온 열전달·열응력 — angle/position 없음, conditions 개수가 DOE)
        has_thermal = any(m == SimulationMode.THERM for m in mode_sequence)

        # VIBRATION을 IMPACT보다 먼저 분기 (혼합 시퀀스는 P2에서 정책 결정).
        # P1 범위: 시퀀스 전체가 VIB-only일 때만 vibration 처리 진입.
        if has_vibration:
            return self._process_vibration_scenario(scenario_cfg, scenario_name,
                                                     cumulative_cfg, num_steps, mode_sequence)
        elif has_thermal:
            return self._process_thermal_scenario(scenario_cfg, scenario_name,
                                                   cumulative_cfg, num_steps, mode_sequence)
        elif has_impact:
            return self._process_impact_scenario(scenario_cfg, scenario_name,
                                                  cumulative_cfg, num_steps, mode_sequence)
        else:
            return self._process_drop_scenario(scenario_cfg, scenario_name,
                                                cumulative_cfg, num_steps, mode_sequence)

    def _process_thermal_scenario(self, scenario_cfg: Dict[str, Any],
                                  scenario_name: str,
                                  cumulative_cfg: Dict[str, Any],
                                  num_steps: int,
                                  mode_sequence: List[SimulationMode]) -> ScenarioConfig:
        """고온 열전달·열응력(THERM) 시나리오 처리 (P1: T1 균일온도).

        angle_source/position_source 없음 — `thermal_conditions` 리스트 개수가 DOE 수.
        조건 미지정 시 단일 DOE(condition="THERM"). VIBRATION 결 답습하되 더 단순.
        """
        templates = select_template_for_scenario(mode_sequence)
        # thermal_conditions: ["HOT85", "COLD-40"] 등. 없으면 단일 DOE.
        conditions = scenario_cfg.get("thermal_conditions", [])
        if not conditions:
            conditions = ["THERM"]

        steps = []
        for doe_idx, cond in enumerate(conditions):
            for i in range(num_steps):
                step_number = i + 1
                template = templates[i]
                mode = mode_sequence[i]
                step_cfg = StepConfig(
                    step_number=step_number,
                    template=template.value,
                    mode=mode.value,
                    angle_name=str(cond),       # condition 식별자를 angle_name에 보존
                    angle_roll=0.0,
                    angle_pitch=0.0,
                    angle_yaw=0.0,
                    input_file=f"Step{step_number:03d}.k",
                    output_dir=f"Step{step_number:03d}",
                    dynain_source=f"Step{step_number-1:03d}/dynain" if step_number > 1 else None,
                    doe_index=doe_idx
                )
                steps.append(step_cfg)

        scenario_id = f"{scenario_name}_S{num_steps:03d}"
        return ScenarioConfig(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            total_steps=num_steps,
            steps=steps
        )

    def _process_drop_scenario(self, scenario_cfg: Dict[str, Any],
                                scenario_name: str,
                                cumulative_cfg: Dict[str, Any],
                                num_steps: int,
                                mode_sequence: List[SimulationMode]) -> ScenarioConfig:
        """낙하/열응력 시나리오 처리 (기존 로직)"""

        # Step 1: 각도 소스 파싱
        angle_source_cfg = scenario_cfg.get("angle_source", {})
        base_angles = self._parse_angle_source(angle_source_cfg)

        # Step 2: Tolerance/DOE 적용
        tolerance_cfg = scenario_cfg.get("tolerance", None)
        if tolerance_cfg:
            tolerance_config = self._parse_tolerance_config(tolerance_cfg)
            doe_angles = apply_tolerance_doe(base_angles, tolerance_config)
        else:
            # Tolerance 없으면 원본 그대로 (각 케이스에 고유 doe_index 부여)
            doe_angles = [(name, roll, pitch, yaw, idx) for idx, (name, roll, pitch, yaw) in enumerate(base_angles)]

        # Step 3: 각도 믹싱 전략
        mixing_cfg = cumulative_cfg.get("angle_mixing", {})
        base_angle_index = cumulative_cfg.get("base_angle_index", 0)
        mixing_config = self._parse_mixing_config(mixing_cfg)

        # Step 4: 템플릿 자동 선택
        templates = select_template_for_scenario(mode_sequence)

        # Step 5: 각 DOE마다 Step 시퀀스 생성
        steps = []

        # DOE 각도 그룹화 (base 각도별로)
        doe_by_base = {}
        for name, roll, pitch, yaw, doe_idx in doe_angles:
            # Base 이름 추출 (DOE 접미사 제거)
            base_name = name.split('_DOE')[0] if '_DOE' in name else name

            if base_name not in doe_by_base:
                doe_by_base[base_name] = []
            doe_by_base[base_name].append((name, roll, pitch, yaw, doe_idx))

        # 전체 base 각도 리스트 (cyclic, random 등을 위해 모든 base 각도 사용)
        all_base_angles = []
        for base_name in sorted(doe_by_base.keys()):
            # 각 base_name의 첫 DOE만 사용 (Tolerance 없는 경우 1개씩만 존재)
            first_doe = doe_by_base[base_name][0]
            all_base_angles.append((first_doe[0], first_doe[1], first_doe[2], first_doe[3]))

        # 각 DOE에 대해 누적 Step 시퀀스 생성
        for base_name in sorted(doe_by_base.keys()):
            doe_list = doe_by_base[base_name]

            for doe_name, doe_roll, doe_pitch, doe_yaw, doe_idx in doe_list:
                # 현재 DOE가 전체 base 각도 리스트에서 몇 번째인지 찾기
                current_base_idx = 0
                for idx, (n, r, p, y) in enumerate(all_base_angles):
                    if n == doe_name and abs(r - doe_roll) < 0.01 and abs(p - doe_pitch) < 0.01:
                        current_base_idx = idx
                        break

                # 각도 믹싱 전략 적용하여 Step별 각도 생성
                angle_sequence = generate_cumulative_angle_sequence(
                    all_base_angles, num_steps, mixing_config, current_base_idx
                )

                # 이 DOE의 Step 설정 생성
                for i in range(num_steps):
                    step_number = i + 1
                    template = templates[i]
                    mode = mode_sequence[i]
                    angle_name, angle_roll, angle_pitch, angle_yaw = angle_sequence[i]

                    step_cfg = StepConfig(
                        step_number=step_number,
                        template=template.value,
                        mode=mode.value,
                        angle_name=angle_name,
                        angle_roll=angle_roll,
                        angle_pitch=angle_pitch,
                        angle_yaw=angle_yaw,
                        input_file=f"Step{step_number:03d}.k",
                        output_dir=f"Step{step_number:03d}",
                        dynain_source=f"Step{step_number-1:03d}/dynain" if step_number > 1 else None,
                        doe_index=doe_idx
                    )
                    steps.append(step_cfg)

        # 시나리오 ID 생성
        scenario_id = f"{scenario_name}_S{num_steps:03d}"

        return ScenarioConfig(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            total_steps=num_steps,
            steps=steps
        )

    def _process_impact_scenario(self, scenario_cfg: Dict[str, Any],
                                  scenario_name: str,
                                  cumulative_cfg: Dict[str, Any],
                                  num_steps: int,
                                  mode_sequence: List[SimulationMode]) -> ScenarioConfig:
        """충격 위치 DOE 시나리오 처리

        position_source로 충격 위치 목록을 생성하고,
        각 위치를 DOE 케이스로 매핑합니다.
        """
        # position_source 파싱 (bbox 미지정 시 모델 파일에서 자동 계산)
        position_source_cfg = scenario_cfg.get("position_source", {})
        positions = parse_position_source(position_source_cfg, model_file=self._current_model_file)

        if not positions:
            raise ValueError("position_source에서 충격 위치가 생성되지 않았습니다")

        # 충격 위치 목록 저장 (save_runner_config에서 doe_positions 생성에 사용)
        self._impact_positions = positions

        # 템플릿 자동 선택
        templates = select_template_for_scenario(mode_sequence)

        # 각 위치(DOE)마다 Step 시퀀스 생성
        steps = []
        for doe_idx, pos in enumerate(positions):
            for i in range(num_steps):
                step_number = i + 1
                template = templates[i]
                mode = mode_sequence[i]

                step_cfg = StepConfig(
                    step_number=step_number,
                    template=template.value,
                    mode=mode.value,
                    angle_name=pos.name,  # position_name을 angle_name에 저장
                    angle_roll=0.0,       # IMPACT에서는 각도 미사용
                    angle_pitch=0.0,
                    angle_yaw=0.0,
                    input_file=f"Step{step_number:03d}.k",
                    output_dir=f"Step{step_number:03d}",
                    dynain_source=f"Step{step_number-1:03d}/dynain" if step_number > 1 else None,
                    doe_index=doe_idx
                )
                steps.append(step_cfg)

        scenario_id = f"{scenario_name}_S{num_steps:03d}"

        return ScenarioConfig(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            total_steps=num_steps,
            steps=steps
        )

    def _process_vibration_scenario(self, scenario_cfg: Dict[str, Any],
                                     scenario_name: str,
                                     cumulative_cfg: Dict[str, Any],
                                     num_steps: int,
                                     mode_sequence: List[SimulationMode]) -> ScenarioConfig:
        """진동(VIBRATION) 시나리오 처리 (P1: explicit_factors only)

        vibration_source로 진동 케이스 목록(DOE 인자 조합)을 생성하고,
        각 케이스를 DOE로 매핑합니다. IMPACT 패턴을 모방하되 step별 각도 필드는
        stub(0.0)로 두고 실제 DOE 메타데이터는 doe_vibrations 출력 필드로 분리합니다.

        P1 범위 (design_decisions.md A~G 채택안):
            - explicit_factors: 사용자가 명시적으로 인자 조합 리스트를 제공
            - per_cap / circuit_group 전략은 P2에서 추가

        Parameters:
            scenario_cfg: 시나리오 설정 (vibration_source 키 포함)
            scenario_name: 시나리오 이름
            cumulative_cfg: 누적 설정
            num_steps: Step 수
            mode_sequence: 모드 시퀀스 (모두 VIB)

        Returns:
            ScenarioConfig
        """
        # parse_vibration_source 모듈 부재 시 명시적 에러 (호출 시점까지 지연)
        if parse_vibration_source is None:
            raise ImportError(
                "VibrationSource 모듈을 import할 수 없습니다. "
                "VIBRATION 시나리오를 사용하려면 Runner/VibrationSource.py 구현이 필요합니다 "
                "(parse_vibration_source, VibrationLoadSpec, VibrationContext)."
            )

        # vibration_source 파싱 → 단일 VibrationLoadSpec
        # parse_vibration_source 시그니처: (config: dict, ctx: VibrationContext) -> VibrationLoadSpec
        # ctx 에는 scenario_dir 등 컨텍스트 전달 (P2+ max_doe_count 가드 진입로).
        vibration_source_cfg = scenario_cfg.get("vibration_source", {})
        ctx = VibrationContext(scenario_dir=self.scenario_dir)
        spec = parse_vibration_source(vibration_source_cfg, ctx)

        if spec is None:
            raise ValueError("vibration_source에서 VibrationLoadSpec이 생성되지 않았습니다")

        # DOE 케이스 = spec.doe_factors_list (P1 explicit_factors 길이 1;
        # P2 per_cap/circuit_group 길이 N)
        doe_factors_list = spec.doe_factors_list
        if not doe_factors_list:
            raise ValueError(
                "VibrationLoadSpec.doe_factors_list 가 비어 있습니다 "
                "(P1 explicit_factors 는 최소 1개 케이스를 생성해야 함)"
            )

        # 진동 spec 저장 (save_runner_config 에서 doe_vibrations 생성에 사용)
        # IMPACT의 self._impact_positions 와 동일한 상태 저장 패턴
        self._vibration_spec = spec

        # 템플릿 자동 선택 (VIB → VIBRATION_FIRST / VIBRATION_CUMULATIVE)
        templates = select_template_for_scenario(mode_sequence)

        # 각 DOE 케이스마다 Step 시퀀스 생성
        steps = []
        for doe_idx, (case_name, _case_factors) in enumerate(doe_factors_list):
            for i in range(num_steps):
                step_number = i + 1
                template = templates[i]
                mode = mode_sequence[i]

                # VIBRATION에서 각도 필드는 stub. 실제 DOE 인자는 doe_vibrations에 분리 저장.
                # angle_name에는 케이스 식별자(case_name)를 보존하여 condition 컬럼으로 노출.
                step_cfg = StepConfig(
                    step_number=step_number,
                    template=template.value,
                    mode=mode.value,
                    angle_name=case_name,  # 케이스 이름을 condition으로 사용
                    angle_roll=0.0,        # VIBRATION에서는 각도 미사용
                    angle_pitch=0.0,
                    angle_yaw=0.0,
                    input_file=f"Step{step_number:03d}.k",
                    output_dir=f"Step{step_number:03d}",
                    dynain_source=f"Step{step_number-1:03d}/dynain" if step_number > 1 else None,
                    doe_index=doe_idx
                )
                steps.append(step_cfg)

        scenario_id = f"{scenario_name}_S{num_steps:03d}"

        return ScenarioConfig(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            total_steps=num_steps,
            steps=steps
        )

    def _parse_angle_source(self, angle_source_cfg: Dict[str, Any]) -> List[tuple]:
        """각도 소스 파싱"""
        source_type_str = angle_source_cfg.get("source_type", "cuboid_geometry")
        source_type = AngleSourceType(source_type_str)

        if source_type == AngleSourceType.CUBOID_GEOMETRY:
            cuboid_cfg = angle_source_cfg.get("cuboid_geometry", {})
            config = AngleSourceConfig(
                source_type=source_type,
                cuboid_geometry=CuboidGeometryConfig(
                    include_faces=cuboid_cfg.get("include_faces", True),
                    include_edges=cuboid_cfg.get("include_edges", True),
                    include_corners=cuboid_cfg.get("include_corners", True)
                )
            )

        elif source_type == AngleSourceType.FIBONACCI_LATTICE:
            fib_cfg = angle_source_cfg.get("fibonacci_lattice", {})
            # num_directions는 num_points의 별칭으로 허용
            num_pts = fib_cfg.get("num_points") or fib_cfg.get("num_directions", 26)
            config = AngleSourceConfig(
                source_type=source_type,
                fibonacci_lattice=FibonacciLatticeConfig(
                    num_points=num_pts,
                    progressive=bool(fib_cfg.get("progressive", False)),
                    principal_directions=fib_cfg.get("principal_directions"),
                    sampling_space=fib_cfg.get("sampling_space"),
                    previous_stages=fib_cfg.get("previous_stages")
                )
            )

        elif source_type == AngleSourceType.PITCHING_SWEEP:
            pitch_cfg = angle_source_cfg.get("pitching_sweep", {})
            config = AngleSourceConfig(
                source_type=source_type,
                pitching_sweep=PitchingSweepConfig(
                    pitch_min=pitch_cfg.get("pitch_min", -90.0),
                    pitch_max=pitch_cfg.get("pitch_max", 90.0),
                    pitch_step=pitch_cfg.get("pitch_step", 10.0),
                    roll_fixed=pitch_cfg.get("roll_fixed", 0.0),
                    yaw_fixed=pitch_cfg.get("yaw_fixed", 0.0)
                )
            )

        elif source_type == AngleSourceType.ROLLING_SWEEP:
            roll_cfg = angle_source_cfg.get("rolling_sweep", {})
            config = AngleSourceConfig(
                source_type=source_type,
                rolling_sweep=RollingSweepConfig(
                    roll_min=roll_cfg.get("roll_min", -180.0),
                    roll_max=roll_cfg.get("roll_max", 170.0),
                    roll_step=roll_cfg.get("roll_step", 10.0),
                    pitch_fixed=roll_cfg.get("pitch_fixed", 0.0),
                    yaw_fixed=roll_cfg.get("yaw_fixed", 0.0)
                )
            )

        elif source_type == AngleSourceType.CASE_TXT_FILE:
            case_cfg = angle_source_cfg.get("case_txt_file", {})
            config = AngleSourceConfig(
                source_type=source_type,
                case_txt_file=CaseTxtFileConfig(
                    file_path=case_cfg.get("file_path"),
                    selected_indices=case_cfg.get("selected_indices")
                )
            )

        else:
            raise ValueError(f"지원하지 않는 각도 소스 타입: {source_type}")

        return parse_angle_source(config)

    def _parse_tolerance_config(self, tolerance_cfg: Dict[str, Any]) -> ToleranceConfig:
        """Tolerance 설정 파싱"""
        roll_cfg = tolerance_cfg.get("roll")
        pitch_cfg = tolerance_cfg.get("pitch")
        yaw_cfg = tolerance_cfg.get("yaw")

        roll_range = None
        pitch_range = None
        yaw_range = None

        if roll_cfg:
            if "tolerance" in roll_cfg:
                roll_range = ToleranceRange.from_tolerance(roll_cfg["tolerance"])
            else:
                roll_range = ToleranceRange(roll_cfg["min"], roll_cfg["max"])

        if pitch_cfg:
            if "tolerance" in pitch_cfg:
                pitch_range = ToleranceRange.from_tolerance(pitch_cfg["tolerance"])
            else:
                pitch_range = ToleranceRange(pitch_cfg["min"], pitch_cfg["max"])

        if yaw_cfg:
            if "tolerance" in yaw_cfg:
                yaw_range = ToleranceRange.from_tolerance(yaw_cfg["tolerance"])
            else:
                yaw_range = ToleranceRange(yaw_cfg["min"], yaw_cfg["max"])

        doe_type_str = tolerance_cfg.get("doe_type", "lhs")
        doe_type = DOEType(doe_type_str)

        return ToleranceConfig(
            roll=roll_range,
            pitch=pitch_range,
            yaw=yaw_range,
            doe_type=doe_type,
            doe_count=tolerance_cfg.get("doe_count", 10)
        )

    def _parse_mode_sequence(self, cumulative_cfg: Dict[str, Any], num_steps: int) -> List[SimulationMode]:
        """모드 시퀀스 파싱"""
        mode_sequence_cfg = cumulative_cfg.get("mode_sequence", ["DROP"] * num_steps)

        mode_sequence = []
        for mode_str in mode_sequence_cfg:
            mode = SimulationMode(mode_str.upper())
            mode_sequence.append(mode)

        # 길이 확인
        if len(mode_sequence) < num_steps:
            # 부족하면 마지막 모드로 채우기
            last_mode = mode_sequence[-1] if mode_sequence else SimulationMode.DROP
            mode_sequence.extend([last_mode] * (num_steps - len(mode_sequence)))

        return mode_sequence[:num_steps]

    def _parse_mixing_config(self, mixing_cfg: Dict[str, Any]) -> CumulativeAngleConfig:
        """각도 믹싱 설정 파싱"""
        strategy_str = mixing_cfg.get("strategy", "same_angle")
        strategy = MixingStrategy(strategy_str)

        custom_mapping = mixing_cfg.get("custom_mapping")
        if custom_mapping:
            # JSON의 키를 int로 변환
            custom_mapping = {int(k): v for k, v in custom_mapping.items()}

        return CumulativeAngleConfig(
            mixing_strategy=strategy,
            cyclic_offset=mixing_cfg.get("cyclic_offset", 1),
            random_seed=mixing_cfg.get("random_seed"),
            custom_mapping=custom_mapping
        )

    def _get_batch_koomeshmodifier_flag(self) -> bool:
        """batch_koomeshmodifier 설정 확인

        scenario.json의 scenarios[0].batch_koomeshmodifier가 true이고
        num_steps == 1인 경우에만 활성화. 그 외에는 False 반환.
        """
        scenarios = self.user_config.get("scenarios", [])
        if not scenarios:
            return False

        scenario_cfg = scenarios[0]
        batch_flag = scenario_cfg.get("batch_koomeshmodifier", False)
        if not batch_flag:
            return False

        cumulative_cfg = scenario_cfg.get("cumulative", {})
        num_steps = cumulative_cfg.get("num_steps", 1)
        if num_steps != 1:
            print(f"⚠️  batch_koomeshmodifier는 num_steps=1일 때만 사용 가능합니다 (현재: {num_steps}). 무시합니다.")
            return False

        return True

    def save_runner_config(self, runner_config: RunnerConfig, output_path: str):
        """runner_config.json 저장

        CumulativeScenarioRunner가 기대하는 스키마로 출력:
            project: name, model_file, output_dir, index_file
            scenario: id, name, type, total_steps, doe_count, steps[]
            execution: checkpoint_file, timeout_per_step_seconds, retry_on_failure, max_retries
            environment: koomeshmodifier_path, lsdyna_path, ncpu, memory, ...
            scenarios: (원본 시나리오 목록 - LargeScaleDOEManager 등 다른 Runner용)
        """
        output_dir_path = str(Path(output_path).parent / "output")
        model_file = getattr(self, '_current_model_file', '')

        # 첫 번째 시나리오를 기준으로 Runner 호환 구조 생성
        first_scenario = runner_config.scenarios[0] if runner_config.scenarios else None

        # DOE 수 계산: unique doe_index 수
        doe_indices = set()
        if first_scenario:
            for step in first_scenario.steps:
                doe_indices.add(step.doe_index)
        doe_count = len(doe_indices) if doe_indices else 1

        # 러너 전용 스텝(REMAP 등) 파라미터: scenarios[0].cumulative.step_params
        #   {"<step_num>": {"op":"matdb","config":{...}}} 또는 {"op":"map","argv":[...]}
        # 미지정 시 {} → 기존 DROP/IMPACT/THERM/VIB 출력과 바이트 동일.
        _scens = self.user_config.get("scenarios", [])
        _scen0 = _scens[0] if _scens else {}
        step_params_map = _scen0.get("cumulative", {}).get("step_params", {})

        # CumulativeScenarioRunner 호환 steps 변환
        # step_number별로 모드 정보 추출 (step 구조는 DOE 공통)
        runner_steps = []
        if first_scenario:
            seen_steps = set()
            for step in first_scenario.steps:
                if step.step_number not in seen_steps:
                    seen_steps.add(step.step_number)
                    runner_steps.append({
                        "step": step.step_number,
                        "mode": step.mode,
                        "condition": step.angle_name,
                        "params": step_params_map.get(str(step.step_number), {})
                    })

        # DOE별 각도 매핑 테이블 생성
        # doe_index → { step_number → { angle_name, roll, pitch, yaw } }
        doe_angle_map = {}
        if first_scenario:
            for step in first_scenario.steps:
                doe_idx = step.doe_index
                if doe_idx not in doe_angle_map:
                    doe_angle_map[doe_idx] = {}
                doe_angle_map[doe_idx][step.step_number] = {
                    "angle_name": step.angle_name,
                    "roll": step.angle_roll,
                    "pitch": step.angle_pitch,
                    "yaw": step.angle_yaw
                }

        # DOE index를 1-based로 변환 (CumulativeScenarioRunner는 1-based)
        doe_angles = {}
        for doe_idx in sorted(doe_angle_map.keys()):
            doe_angles[str(doe_idx + 1)] = doe_angle_map[doe_idx]

        # IMPACT 모드: doe_positions 생성
        doe_positions = {}
        if hasattr(self, '_impact_positions') and self._impact_positions:
            for pos_idx, pos in enumerate(self._impact_positions):
                doe_key = str(pos_idx + 1)  # 1-based
                doe_positions[doe_key] = {
                    "1": {
                        "position_name": pos.name,
                        "x": pos.x,
                        "y": pos.y
                    }
                }
                # 누적 step이 있으면 모든 step에 같은 위치 할당
                if first_scenario:
                    for step in first_scenario.steps:
                        if step.doe_index == pos_idx:
                            step_key = str(step.step_number)
                            doe_positions[doe_key][step_key] = {
                                "position_name": pos.name,
                                "x": pos.x,
                                "y": pos.y
                            }

        # VIBRATION 모드: doe_vibrations 생성 (P1: explicit_factors only)
        # 패턴: doe_positions와 동일 — 1-based DOE key, step_key → factor 딕셔너리
        # VibrationLoadSpec.doe_factors_list: [(case_name, ((pid, factor), ...)), ...]
        # P2 확장 여지: per_cap / circuit_group 도 동일 doe_factors_list 형식 채워
        # 별도 분기 없이 동일 루프로 카탈로그 생성.
        doe_vibrations = {}
        if hasattr(self, '_vibration_spec') and self._vibration_spec is not None:
            spec = self._vibration_spec
            # spec 공통 필드 평탄화 — runner_config 에 직렬화하여 Runner 가
            # spec 객체 없이도 build_vibration_load_config 호출에 필요한 모든
            # 인자를 복원할 수 있도록 함. (load_curve/direction/load_type/
            # relative_mode 누락 시 StepConfigBuilder._serialize_explicit
            # 가 "load_curve가 비어 있습니다." 로 raise 했던 회귀 결함 fix)
            load_curve_serialized = [[float(t), float(v)]
                                     for t, v in spec.load_curve]
            common_fields = {
                "direction": spec.direction,
                "load_type": spec.load_type,
                "relative_mode": spec.relative_mode,
                "load_curve": load_curve_serialized,
            }
            for case_idx, (case_name, case_part_factors) in enumerate(spec.doe_factors_list):
                doe_key = str(case_idx + 1)  # 1-based
                # part_factors → {"<pid>": factor} 딕셔너리 (JSON-friendly)
                factors_dict = {str(pid): float(factor)
                                for pid, factor in case_part_factors}

                # Step 1 기본 항목 (DOE 단일 케이스도 doe_vibrations에 등록되도록)
                doe_vibrations[doe_key] = {
                    "1": {
                        "case_name": case_name,
                        "factors": factors_dict,
                        **common_fields,
                    }
                }
                # 누적 step이 있으면 모든 step에 같은 케이스 할당
                if first_scenario:
                    for step in first_scenario.steps:
                        if step.doe_index == case_idx:
                            step_key = str(step.step_number)
                            doe_vibrations[doe_key][step_key] = {
                                "case_name": case_name,
                                "factors": factors_dict,
                                **common_fields,
                            }

        data = {
            # CumulativeScenarioRunner 호환 섹션
            "project": {
                "name": runner_config.project_name,
                "model_file": model_file,
                "output_dir": output_dir_path,
                "index_file": str(Path(output_dir_path) / "simulation_index.json")
            },
            "scenario": {
                "id": first_scenario.scenario_id if first_scenario else "",
                "name": first_scenario.scenario_name if first_scenario else "",
                "type": "cumulative",
                "total_steps": first_scenario.total_steps if first_scenario else 0,
                "doe_count": doe_count,
                "steps": runner_steps,
                "doe_angles": doe_angles,
                **({"doe_positions": doe_positions} if doe_positions else {}),
                # VIBRATION DOE 메타데이터 (P1: explicit_factors only)
                # conditional spread로 비-VIB 시나리오 출력에 노이즈 없음
                **({"doe_vibrations": doe_vibrations} if doe_vibrations else {}),
                # batch_koomeshmodifier: 1-step 시나리오에서 헤드노드 일괄 생성 옵션
                "batch_koomeshmodifier": self._get_batch_koomeshmodifier_flag()
            },
            "execution": {
                "checkpoint_file": str(Path(output_dir_path) / "checkpoint.json"),
                "timeout_per_step_seconds": runner_config.environment.get("timeout_per_step_seconds", 604800),
                "timeout_koomeshmodifier_seconds": runner_config.environment.get("timeout_koomeshmodifier_seconds", 604800),
                "timeout_dynain_seconds": runner_config.environment.get("timeout_dynain_seconds", 604800),
                "retry_on_failure": True,
                "max_retries": 2,
                # 누적 무결성: true 면 DYNAIN_TO_INITIAL 실패/_dti.k 부재를 step 실패로 승격
                # (기본 false = 기존 동작: warning + degraded 태깅 후 원본 fallback)
                "strict_accumulation": bool(runner_config.environment.get("strict_accumulation", False))
            },
            "environment": runner_config.environment,
            # simulation_params (있으면 추가)
            **({"simulation_params": runner_config.simulation_params} if runner_config.simulation_params else {}),
            # postprocess (있으면 추가) — KooD3plotReader pipeline
            **({"postprocess": runner_config.postprocess} if runner_config.postprocess else {}),
            # 원본 시나리오 목록 (LargeScaleDOEManager 등 다른 Runner 호환)
            "project_name": runner_config.project_name,
            "base_dir": runner_config.base_dir,
            "scenarios": []
        }

        # 원본 시나리오 데이터 (기존 구조 유지)
        for scenario in runner_config.scenarios:
            scenario_data = {
                "scenario_id": scenario.scenario_id,
                "scenario_name": scenario.scenario_name,
                "total_steps": scenario.total_steps,
                "steps": []
            }

            for step in scenario.steps:
                step_data = {
                    "step_number": step.step_number,
                    "template": step.template,
                    "mode": step.mode,
                    "angle": {
                        "name": step.angle_name,
                        "roll": step.angle_roll,
                        "pitch": step.angle_pitch,
                        "yaw": step.angle_yaw
                    },
                    "input_file": step.input_file,
                    "output_dir": step.output_dir,
                    "dynain_source": step.dynain_source,
                    "doe_index": step.doe_index
                }
                scenario_data["steps"].append(step_data)

            data["scenarios"].append(scenario_data)

        # JSON 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"runner_config.json 생성 완료: {output_path}")

        # postprocess 옵션이 있으면 sphere_report.sh + impact_report.sh를 항상 생성
        # (수동 trigger 보장). enabled 무관 — sh는 항상 만들어 두고 사용자가 언제든
        # bash로 실행 가능. 실제 어느 것이 자동 실행될지는 scenario mode 로 routing
        # (DROP→sphere, IMPACT→impact) — report_mode_from_runner_config 참조.
        if runner_config.postprocess:
            output_dir = data["project"].get("output_dir", str(Path(output_path).parent / "output"))
            try:
                from Runner.PostprocessShellGenerator import build_sphere_report_sh
                os.makedirs(output_dir, exist_ok=True)
                sh_text = build_sphere_report_sh(
                    output_dir=output_dir,
                    sif_path=runner_config.postprocess.get("sif_path"),
                    options=runner_config.postprocess,
                )
                sh_path = os.path.join(output_dir, "sphere_report.sh")
                with open(sh_path, 'w') as f:
                    f.write(sh_text)
                os.chmod(sh_path, 0o755)
                print(f"sphere_report.sh 생성 (수동 실행 가능): {sh_path}")
            except Exception as e:
                print(f"  Warning: sphere_report.sh 생성 실패 (skip): {e}")

            try:
                from Runner.PostprocessShellGenerator import build_impact_report_sh
                os.makedirs(output_dir, exist_ok=True)
                impact_sh_text = build_impact_report_sh(
                    output_dir=output_dir,
                    sif_path=runner_config.postprocess.get("sif_path"),
                    options=runner_config.postprocess,
                )
                impact_sh_path = os.path.join(output_dir, "impact_report.sh")
                with open(impact_sh_path, 'w') as f:
                    f.write(impact_sh_text)
                os.chmod(impact_sh_path, 0o755)
                print(f"impact_report.sh 생성 (수동 실행 가능): {impact_sh_path}")
            except Exception as e:
                print(f"  Warning: impact_report.sh 생성 실패 (skip): {e}")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Cumulative Scenario Designer")
    parser.add_argument("input_json", help="사용자 JSON 설정 파일")
    parser.add_argument("-o", "--output", default="runner_config.json", help="출력 runner_config.json 경로")
    args = parser.parse_args()

    # 사용자 JSON 읽기
    with open(args.input_json, 'r', encoding='utf-8') as f:
        user_config = json.load(f)

    # Designer 실행
    scenario_dir = str(Path(args.input_json).resolve().parent)
    designer = CumulativeDesigner(user_config, scenario_dir=scenario_dir)
    runner_config = designer.parse_user_config()

    # runner_config.json 저장
    designer.save_runner_config(runner_config, args.output)

    # 요약 출력
    print(f"\n{'='*80}")
    print(f"📋 시나리오 요약")
    print(f"{'='*80}")
    print(f"프로젝트: {runner_config.project_name}")
    print(f"총 시나리오 수: {len(runner_config.scenarios)}")

    for scenario in runner_config.scenarios:
        print(f"\n시나리오: {scenario.scenario_name} ({scenario.scenario_id})")
        print(f"  총 Step 수: {scenario.total_steps}")
        print(f"  Step 세부:")
        for step in scenario.steps:
            print(f"    Step {step.step_number}: {step.template:<25} {step.mode:<10} {step.angle_name:<20} "
                  f"Roll={step.angle_roll:>7.2f} Pitch={step.angle_pitch:>7.2f}")

    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
