"""Vibration runner_config 직렬화 라운드트립 회귀 방지 테스트.

배경 (결함):
    CumulativeDesigner.save_runner_config 의 doe_vibrations 직렬화가
    case_name + factors 만 출력하고 spec.load_curve / direction /
    load_type / relative_mode 를 누락하여,
    CumulativeScenarioRunner._create_step_config 의 VIBRATION 분기에서
    load_curve=[] 빈 리스트로 build_vibration_load_config 가 호출되고
    StepConfigBuilder._serialize_explicit 가
    "VibrationLoad/Explicit: load_curve가 비어 있습니다." 로 raise.

검증 대상:
    A) parse_vibration_source 가 explicit / per_cap / circuit_group 모두
       load_curve 평탄화
    B) Designer save_runner_config → 디스크 JSON 라운드트립 시
       doe_vibrations 각 entry 에 load_curve/direction/load_type/
       relative_mode/factors 모두 보존
    C) Runner _create_step_config 가 doe_vibrations 만으로 (params 비어있음,
       simulation_params.vibration 부재) 빈 load_curve raise 없이 통과
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# Runner 모듈 import 경로 보장
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)


def _make_scenario_dict(base_dir: str,
                        source_type: str = "circuit_group") -> dict:
    """In-memory scenario.json equivalent.

    절대경로 픽스처 의존성을 제거하고, 테스트가 임의 tempdir 위에서
    독립적으로 실행되도록 한다. Test_VibP2/scenario.json 구조를 그대로 따른다.
    """
    vibration_source = {
        "source_type": source_type,
        "direction": "Z",
        "load_type": "Force",
        "relative_mode": "Explicit",
        "base_curve": {"kind": "inline",
                       "points": [[0, 0], [0.0005, 500], [0.001, 0]]},
    }
    if source_type == "circuit_group":
        vibration_source["circuit_group"] = {
            "circuits": {
                "C1_power": {"parts": [4, 5], "amplitude": 1.0},
                "C2_signal": {"parts": [9, 10], "amplitude": 0.5},
                "C3_motor": {"parts": [18], "amplitude": 2.0},
            }
        }
    elif source_type == "explicit_factors":
        vibration_source["explicit_factors"] = {
            "part_factors": {"4": 1.0},
        }
    elif source_type == "per_cap":
        vibration_source["per_cap"] = {
            "cap_pids": [4, 5], "amplitude": 1.0,
        }
    return {
        "project_name": "VibrationP2_inmem",
        "base_dir": base_dir,
        "environment": {
            "koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
            "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
            "mpi_path": "mpirun",
            "memory": "2G",
            "lsdyna_memory": "2000m",
            "apptainer_sif": "/opt/apptainers/SmartTwinPreprocessor.sif",
            "apptainer_bind": "/data:/data",
            "apptainer_env": {},
            "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif",
            "lsdyna_apptainer_bind": "/data:/data",
            "lsdyna_apptainer_env": {"LSTC_FILE": "/opt/ls-dyna_license/LSTC_FILE",
                                     "LSTC_LICENSE_SERVER": "127.0.0.1"},
            "apptainer_tmpdir": "/tmp",
            "ncpu": 1,
            "koochainrun_path": "/data/SmartTwinPreprocessor/bin/KooChainRun",
            "time_limit": "01:00:00",
        },
        "simulation_params": {"tFinal": 0.001, "dt": 1e-06},
        "scenarios": [
            {
                "scenario_name": "VibP2_inmem",
                "template": "MinimumModel.k",
                "vibration_source": vibration_source,
                "cumulative": {"num_steps": 1,
                               "mode_sequence": ["VIBRATION"]},
            }
        ],
    }


def test_parse_vibration_source_load_curve_flattening():
    """A) 세 source_type 모두 base_curve → spec.load_curve 평탄화."""
    from Runner.VibrationSource import parse_vibration_source, VibrationContext

    cases = [
        ("explicit_factors", {
            "source_type": "explicit_factors",
            "direction": "Z",
            "load_type": "Force",
            "relative_mode": "Explicit",
            "base_curve": {"kind": "inline",
                           "points": [[0, 0], [0.0005, 1000], [0.001, 0]]},
            "explicit_factors": {"part_factors": {"4": 1.0}},
        }),
        ("per_cap", {
            "source_type": "per_cap",
            "direction": "Z",
            "load_type": "Force",
            "relative_mode": "Explicit",
            "base_curve": {"kind": "inline",
                           "points": [[0, 0], [0.0005, 1000], [0.001, 0]]},
            "per_cap": {"cap_pids": [4, 5], "amplitude": 1.0},
        }),
        ("circuit_group", {
            "source_type": "circuit_group",
            "direction": "Z",
            "load_type": "Force",
            "relative_mode": "Explicit",
            "base_curve": {"kind": "inline",
                           "points": [[0, 0], [0.0005, 500], [0.001, 0]]},
            "circuit_group": {
                "circuits": {
                    "C1": {"parts": [4, 5], "amplitude": 1.0},
                    "C2": {"parts": [9], "amplitude": 0.5},
                }
            },
        }),
    ]
    for sname, cfg in cases:
        spec = parse_vibration_source(cfg, VibrationContext())
        assert spec is not None, f"{sname}: spec is None"
        assert spec.load_curve and len(spec.load_curve) >= 2, (
            f"{sname}: load_curve not flattened (got={spec.load_curve!r})"
        )
        assert spec.doe_factors_list, (
            f"{sname}: doe_factors_list empty"
        )


def test_designer_doe_vibrations_roundtrip_preserves_load_curve():
    """B) Designer 직렬화 → JSON 라운드트립 시 doe_vibrations entry 보존.

    절대경로 픽스처 없이 in-memory scenario dict + tempfile.mkdtemp 으로 실행.
    """
    from Runner.CumulativeDesigner import CumulativeDesigner

    base_dir = tempfile.mkdtemp(prefix="vibtest_designer_")
    cfg = _make_scenario_dict(base_dir, source_type="circuit_group")
    d = CumulativeDesigner(cfg)
    rc = d.parse_user_config()

    tmp_path = os.path.join(base_dir, "runner_config.json")
    d.save_runner_config(rc, tmp_path)
    with open(tmp_path) as f:
        serialized = json.load(f)

    dv = serialized.get("scenario", {}).get("doe_vibrations", {})
    assert dv, "doe_vibrations missing from runner_config"
    for doe_key, entry in dv.items():
        for step_key, sv in entry.items():
            for required in ("load_curve", "direction", "load_type",
                             "relative_mode", "factors", "case_name"):
                assert required in sv, (
                    f"doe_vibrations[{doe_key}][{step_key}] "
                    f"missing key {required!r}: got keys={list(sv.keys())}"
                )
            assert len(sv["load_curve"]) >= 2, (
                f"doe_vibrations[{doe_key}][{step_key}].load_curve "
                f"too short: {sv['load_curve']!r}"
            )


def test_runner_create_step_config_vibration_no_raise():
    """C) Runner 가 doe_vibrations 만으로 build_vibration_load_config 호출 통과.

    절대경로 픽스처 없이 in-memory scenario dict + tempfile.mkdtemp 으로 실행.
    """
    from Runner.CumulativeDesigner import CumulativeDesigner
    from Runner.CumulativeScenarioRunner import CumulativeScenarioRunner

    base_dir = tempfile.mkdtemp(prefix="vibtest_runner_")
    cfg = _make_scenario_dict(base_dir, source_type="circuit_group")
    d = CumulativeDesigner(cfg)
    rc = d.parse_user_config()

    tmp_path = os.path.join(base_dir, "runner_config.json")
    d.save_runner_config(rc, tmp_path)
    with open(tmp_path) as f:
        runner_config = json.load(f)

    # dummy model_file (build_vibration_load_config 가 경로 존재성 미검증이라
    # 단순 stub 으로 충분)
    model_file = runner_config["project"].get("model_file", "")
    if model_file and not os.path.exists(model_file):
        Path(model_file).parent.mkdir(parents=True, exist_ok=True)
        Path(model_file).touch()

    out_dir = Path(tempfile.mkdtemp(prefix="vibtest_out_"))
    runner_config["project"]["output_dir"] = str(out_dir)

    runner = CumulativeScenarioRunner.__new__(CumulativeScenarioRunner)
    runner.config = runner_config
    runner.output_dir = str(out_dir)
    runner.run_id = "test"
    runner.input_dir = "/tmp"
    runner._get_prev_run_dir = lambda doe, step: None
    runner._build_preserve_block = lambda: ""

    sc = runner_config["scenario"]
    vib_step = next(
        (s for s in sc["steps"] if s.get("mode") == "VIBRATION"), None
    )
    assert vib_step is not None, "scenario에 VIBRATION step 없음"

    # doe_vibrations key 는 1-based — 모든 DOE 케이스 호출
    for doe_key in sc.get("doe_vibrations", {}):
        doe_index = int(doe_key)
        # build_vibration_load_config 가 ValueError raise 시 회귀 발견
        result = runner._create_step_config(doe_index, vib_step)
        assert result is not None, (
            f"_create_step_config returned None for doe_index={doe_index}"
        )
        config_text = Path(result).read_text()
        # 평탄화된 load_curve 가 builder 출력에 실제 반영되었는지 검증
        assert "LoadCurve" in config_text, (
            f"DOE{doe_index} config 에 LoadCurve 블록 없음"
        )
        assert "PartFactors" in config_text, (
            f"DOE{doe_index} config 에 PartFactors 블록 없음"
        )


if __name__ == "__main__":
    test_parse_vibration_source_load_curve_flattening()
    print("[PASS] A) parse_vibration_source load_curve flattening")
    test_designer_doe_vibrations_roundtrip_preserves_load_curve()
    print("[PASS] B) Designer doe_vibrations roundtrip preserves load_curve")
    test_runner_create_step_config_vibration_no_raise()
    print("[PASS] C) Runner _create_step_config no raise on doe_vibrations only")
    print("ALL TESTS PASSED")
