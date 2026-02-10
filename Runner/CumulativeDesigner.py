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
from Runner.PathResolver import find_koomeshmodifier
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

        # 시나리오 설정
        scenarios_config = self.user_config.get("scenarios", [])
        scenarios = []

        for scenario_cfg in scenarios_config:
            scenario = self._process_scenario(scenario_cfg)
            scenarios.append(scenario)

        # simulation_params 가져오기 (없으면 None)
        simulation_params = self.user_config.get("simulation_params", None)

        return RunnerConfig(
            project_name=self.project_name,
            base_dir=self.base_dir,
            scenarios=scenarios,
            environment=environment,
            simulation_params=simulation_params
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

        # Step 3: 누적 모드 및 스텝 수
        cumulative_cfg = scenario_cfg.get("cumulative", {})
        num_steps = cumulative_cfg.get("num_steps", 1)
        mode_sequence = self._parse_mode_sequence(cumulative_cfg, num_steps)

        # Step 4: 각도 믹싱 전략
        mixing_cfg = cumulative_cfg.get("angle_mixing", {})
        base_angle_index = cumulative_cfg.get("base_angle_index", 0)
        mixing_config = self._parse_mixing_config(mixing_cfg)

        # Step 5: 템플릿 자동 선택
        templates = select_template_for_scenario(mode_sequence)

        # Step 6: 각 DOE마다 Step 시퀀스 생성
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
                    num_points=num_pts
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
                        "params": {}
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
                "doe_angles": doe_angles
            },
            "execution": {
                "checkpoint_file": str(Path(output_dir_path) / "checkpoint.json"),
                "timeout_per_step_seconds": 7200,
                "retry_on_failure": True,
                "max_retries": 2
            },
            "environment": runner_config.environment,
            # simulation_params (있으면 추가)
            **({"simulation_params": runner_config.simulation_params} if runner_config.simulation_params else {}),
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
