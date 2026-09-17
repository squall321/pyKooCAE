# KooChainRun --help 카탈로그 — 시나리오 모드별 scenario.json 형식·검증된 사례 + 명령 요약
"""
사례의 verify 는 tests/test_cli_help.py [KCR] 가 확인한다.
  cumulative: CumulativeDesigner(prepare) → runner_config → 러너 step config 생성 → KMM ImportOption 파싱까지
    {"kind": "cumulative", "doe_count": n, "modes": [...], "step": 1, "step_expect": {"키": "값"}}
  workflow  : {"kind": "drop_weight_impact"|"part_validation", ...}
"""

import json

from Runner.cli_help_engine import Catalog, Example, Key, Mode, Topic

K = Key

ENV = {
    "koomeshmodifier_path": "/data/SmartTwinPreprocessor/bin/KooMeshModifier",
    "koochainrun_path": "/data/SmartTwinPreprocessor/bin/KooChainRun",
    "lsdyna_path": "/opt/ls-dyna/lsdyna_R16.1.1",
    "apptainer_sif": "/opt/apptainers/SmartTwinPreprocessor.sif",
    "apptainer_bind": "/data:/data",
    "lsdyna_apptainer_sif": "/opt/apptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif",
    "lsdyna_apptainer_bind": "/data:/data",
    "lsdyna_apptainer_env": {"LSTC_LICENSE_SERVER": "192.168.122.1", "FI_PROVIDER": "tcp"},
    "apptainer_tmpdir": "/data/tmp",
    "ncpu": 8,
    "memory": "16G",
    "partition": "normal",
    "timeout_per_step_seconds": 7200,
}


def _j(d):
    return json.dumps(d, ensure_ascii=False, indent=2)


def _scenario(name, sim, scen, **top):
    d = {"project_name": name, "base_dir": "/data/<사용자>/" + name, "environment": ENV,
         "simulation_params": sim, "scenarios": [scen]}
    d.update(top)
    return _j(d)


TOPICS = [
    Topic("commands", "명령 목록과 순서 — prepare → submit → status → collect/postprocess", aliases=["명령", "command", "workflow", "순서"], body=[
        "  KooChainRun prepare scenario.json [-o runner_config.json]   시나리오 → runner_config.json (+ 모드별 준비물)",
        "  KooChainRun submit runner_config.json [--nodes 2 --jobs-per-node 4 --ncpu-per-job N --partition P --sequential]",
        "                                                              Slurm 제출. jobs.json 에 잡 기록",
        "  KooChainRun status runner_config.json [--watch]             진행 상황",
        "  KooChainRun collect runner_config.json [결과폴더]            결과 수집",
        "  KooChainRun postprocess runner_config.json                  KooD3plotReader 후처리 수동 실행",
        "  KooChainRun diagnose [테스트폴더]                            실패 DOE 원인 진단",
        "  KooChainRun rerun [테스트폴더] [--dry-run --does 1,5 --exclude-nodes n1]   실패·미완료 DOE 재실행",
        "  KooChainRun stop [테스트폴더]                                제출한 잡 전부 취소",
        "  KooChainRun run runner_config.json --doe N [--resume]       (계산 노드용) DOE 하나 실행",
        "  KooChainRun reprioritize [테스트폴더] [--apply]              완료 결과로 대기 잡 우선순위 재배치",
        "  KooChainRun harvest [테스트폴더] [--top N --hot-only]        취약 각도/위치를 JSON 으로 뽑기",
        "",
        "  명령별 전체 옵션: KooChainRun <명령> --help",
        "",
        "규칙",
        "  - 테스트 폴더는 계산 노드가 보는 NFS(/data/...) 에 둘 것. /tmp 는 노드에서 안 보인다.",
        "  - scenario.json 의 상대경로(template, model_file)는 scenario.json 위치 기준이다.",
    ]),
    Topic("environment", "environment 블록 — 실행 경로·SIF·라이선스·자원", aliases=["환경", "env", "sif", "license", "라이선스"], body=[
        "  koomeshmodifier_path      KooMeshModifier 경로 (생략 시 자동 탐색)",
        "  lsdyna_path               LS-DYNA 실행 파일",
        "  apptainer_sif / _bind     전처리(KMM) 컨테이너. 생략 시 직접 실행",
        "  lsdyna_apptainer_sif      LS-DYNA 컨테이너 (_bind, _env)",
        "  lsdyna_apptainer_env      컨테이너 안 env. LSTC_LICENSE_SERVER 는 헤드노드 IP (localhost 금지)",
        "  apptainer_tmpdir          잡별 임시 폴더 기준 (기본 /opt/tmp)",
        "  ncpu / memory / lsdyna_memory / partition / nodes_per_job",
        "  timeout_per_step_seconds  스텝 wall-clock 제한 (기본 7일). 발산 케이스의 최종 안전망 — 짧게 줄 것",
        "  timeout_koomeshmodifier_seconds / timeout_dynain_seconds",
    ]),
    Topic("postprocess_json", "scenario.json 의 postprocess 블록 — 해석 뒤 자동 후처리", aliases=["후처리설정", "report", "리포트", "deep"], body=[
        '  "postprocess": {"enabled": true, "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",',
        '                  "auto_deep": true, "auto_deep_mode": "inline", "auto_sphere": true,',
        '                  "auto_impact": false, "delete_d3plot_after_deep": false}',
        "  auto_deep    DOE 마다 deep report (응력·핫스팟)",
        "  auto_sphere  전각도 낙하 종합 리포트 / auto_impact  전위치 충격 종합 리포트",
        "  *_extra_args 각 리포트 명령에 붙일 인자",
    ]),
    Topic("units", "단위 — 입력은 모델 .k 단위 그대로", aliases=["단위", "unit"], body=[
        "  KMM 은 값을 변환하지 않는다. 표준 낙하 모델은 [tonne, mm, s, MPa] (강철 ρ 7.85e-9, E 2.0e5).",
        "  낙하 속도 √(2gh) 의 g 는 simulation_params.gravity (IMPACT 는 impact.gravity 도) 로 지정한다.",
        "  없으면 KMM 이 모델 재질 밀도로 단위계를 판정한다 (ton-mm-s → 9810, kg-m-s → 9.81).",
        "  kg-mm-ms 처럼 판정이 안 되는 단위계는 반드시 gravity 를 줄 것 (로그에 WARNING).",
    ]),
]

MODES = []


def mode(*a, **kw):
    MODES.append(Mode(*a, **kw))


DROP_SIM = {"height": 1500, "tFinal": 0.005, "dt": 1e-05, "density": 7.85e-09, "youngs_modulus": 200000.0,
            "poisson_ratio": 0.3,
            "drop_surface": {"type": "Plane", "size": [300, 300, 20], "mesh": [30, 30, 2]}}

DROP_FIB = _scenario("Drop_Fibonacci26", DROP_SIM, {
    "scenario_name": "Fib26",
    "template": "model.k",
    "angle_source": {"source_type": "fibonacci_lattice", "fibonacci_lattice": {"num_points": 26}},
    "cumulative": {"num_steps": 1, "mode_sequence": ["DROP"]}})

DROP_CUM = _scenario("Drop_Cumulative3", {
    "height": 1000, "tFinal": 0.003, "dt": 5e-05, "density": 7.85e-09, "youngs_modulus": 200000.0,
    "poisson_ratio": 0.3,
    "drop_surface": {"type": "PlaneGraded", "size": [200, 200, 20], "mesh": [10, 10, 2],
                     "num_outer_layers": 5, "ratio": 1.5},
    "robust_contact": True,
    "rigidify_small_dt_threshold": 1e-07,
    "drop_contact": {"SOFT": 2, "DTSTIF": 3e-08},
    "dynamic_relaxation": True,
}, {
    "scenario_name": "Face6_Cum3",
    "template": "model.k",
    "angle_source": {"source_type": "cuboid_geometry",
                     "cuboid_geometry": {"include_faces": True, "include_edges": False, "include_corners": False}},
    "cumulative": {"num_steps": 3, "mode_sequence": ["DROP", "DROP", "DROP"],
                   "angle_mixing": {"strategy": "cyclic", "cyclic_offset": 1}}})

mode("DROP", "낙하 시나리오 — 자세 DOE(피보나치·육면체·스윕) × 누적 스텝",
     category="시나리오 모드", aliases=["drop", "낙하", "전각도", "fibonacci", "cuboid", "누적낙하"],
     when=["여러 낙하 자세를 클러스터에 한꺼번에 돌릴 때", "같은 제품을 여러 번 떨어뜨리는 누적 낙하 (num_steps ≥ 2)"],
     syntax=['scenarios[].cumulative.mode_sequence: ["DROP", ...]', "scenarios[].angle_source: 자세 목록",
             "simulation_params: 낙하 조건 (KMM DROP_ATTITUDE 로 전달)"],
     keys=[
         K("angle_source.source_type", "문자", "cuboid_geometry", "cuboid_geometry(면·모서리·꼭짓점 26) | fibonacci_lattice | pitching_sweep | rolling_sweep | case_txt_file"),
         K("angle_source.fibonacci_lattice.num_points", "정수", "26", "피보나치 구면 점 수 (별칭 num_directions)"),
         K("angle_source.cuboid_geometry.include_faces/edges/corners", "bool", "true", "육면체 방향 선택"),
         K("angle_source.fibonacci_lattice.sampling_space", "physical | latlon", "physical", "physical = 실제 낙하 방향 등간격. latlon = 옛 방식(방향이 적도에 몰림)"),
         K("tolerance.roll/pitch/yaw + doe_type/doe_count", "객체", "lhs / 10", "각도 공차 DOE 확장"),
         K("cumulative.num_steps / mode_sequence", "정수 / 배열", "1 / DROP×n", "누적 스텝"),
         K("cumulative.angle_mixing.strategy", "문자", "same_angle", "same_angle | cyclic | random | opposite | custom_mapping"),
         K("simulation_params.height", "실수", "1500", "낙하 높이 (모델 단위)"),
         K("simulation_params.gravity", "실수", "재질 밀도로 판정", "자유낙하 g (모델 단위, --help units)"),
         K("simulation_params.tFinal / dt", "실수", "0.005 / 1e-6", "종료 시간 / d3plot 간격"),
         K("simulation_params.density / youngs_modulus / poisson_ratio", "실수", "7.85e-9 / 2e5 / 0.3", "바닥판 재질"),
         K("simulation_params.offset_distance", "실수", "0.05", "바닥판 초기 간격"),
         K("simulation_params.drop_surface", "객체", "Plane 300×300×20, 30×30×2", "type: Plane | PlaneGraded(num_outer_layers, ratio) | RigidWall | PlanewithRoughness"),
         K("simulation_params.drop_contact", "객체", "{}", "바닥판 접촉 카드 필드 (SOFT, DTSTIF, FS ...)"),
         K("simulation_params.robust_contact / robust_contact_tolerance", "bool / 실수", "false / 0.1", "Tied 면 제외 SINGLE_SURFACE"),
         K("simulation_params.rigidify_small_dt_threshold", "실수", "0", "작은 dt 요소 강체화"),
         K("simulation_params.control_timestep / control_hourglass", "객체", "{}", "*CONTROL_TIMESTEP(DT2MS 등) / *CONTROL_HOURGLASS 덮어쓰기"),
         K("simulation_params.dynamic_relaxation", "bool | 객체", "false", "누적 스텝 사이 DR (nrcyck, drtol, drfctr, drterm)"),
         K("simulation_params.dtmin", "실수", "1e-10 (DR 이면 0.01)", "CONTROL_TERMINATION DTMIN"),
         K("simulation_params.non_reflecting_boundary / include_wall_in_general", "bool", "false", "바닥판 옵션"),
     ],
     examples=[
         Example("피보나치 26 자세 1.5 m 1회 낙하", DROP_FIB,
                 explain=["model.k 는 scenario.json 옆에 둔다. prepare → submit → status → collect."],
                 verify={"kind": "cumulative", "doe_count": 26, "modes": ["DROP"], "step": 1,
                         "step_expect": {"Height": "1500", "tFinal": "0.005", "dt": "1e-05",
                                         "DropSurface": "Plane,300,300,20,30,30,2"}}),
         Example("육면 6 자세 × 3회 누적 (cyclic), 견고 접촉·작은 dt 강체화·DR", DROP_CUM,
                 explain=["step 2 부터 앞 스텝 dynain(변형+응력)을 이어받는다.",
                          "dynamic_relaxation 이 켜져 있으면 dtmin 미지정 시 0.01 이 자동으로 들어간다."],
                 verify={"kind": "cumulative", "doe_count": 6, "modes": ["DROP", "DROP", "DROP"], "step": 1,
                         "step_expect": {"RigidifySmallDtThreshold": "1e-07", "DropContact.DTSTIF": "3e-08",
                                         "RobustContact": "True", "dt": "5e-05"}}),
     ],
     notes=["자세 수 × 스텝 수만큼 LS-DYNA 가 돈다 — 먼저 작은 num_points 로 확인할 것.",
            "발산 대비 environment.timeout_per_step_seconds 를 실제 walltime 의 2~3 배로."],
     related=["IMPACT", "REMAP", "part_validation"])

IMP_SPHERE = _scenario("Impact_Grid3x3", {
    "impact": {"type": "Sphere", "dimension": 8, "height": 500, "mesh_size": 1, "dimension_damper": [1, 1, 1],
               "density": 7.85e-09, "youngs_modulus": 201000.0, "poisson_ratio": 0.3,
               "tFinal": 0.001, "dt": 1e-05, "offset_distance": 0.01},
    "wall": {"density": 1e-09, "youngs_modulus": 10000.0, "poisson_ratio": 0.3}}, {
    "scenario_name": "Grid3x3",
    "template": "model.k",
    "position_source": {"source_type": "grid_nxm", "grid_nxm": {"nx": 3, "ny": 3, "bbox": [-40, -40, 40, 40]}},
    "cumulative": {"num_steps": 1, "mode_sequence": ["IMPACT"]}})

IMP_CYL = _scenario("Impact_Cylinder3Stage", {
    "impact": {"type": "cylinder", "height": 200, "mesh_size": 2, "tFinal": 0.001, "dt": 1e-05,
               "offset_distance": 0.01,
               "cylinder_stages": [
                   {"role": "front", "diameter": 8, "outer_diameter": 20, "height": 6,
                    "density": 1.18e-09, "youngs_modulus": 100.0, "poisson": 0.49},
                   {"role": "mid", "diameter": 20, "height": 14,
                    "density": 6.57e-09, "youngs_modulus": 207000.0, "poisson": 0.3},
                   {"role": "back", "diameter": 44.5, "height": 38.003,
                    "density": 6.57e-09, "youngs_modulus": 207000.0, "poisson": 0.3}]},
    "wall": {"density": 1e-09, "youngs_modulus": 10000.0, "poisson_ratio": 0.3}}, {
    "scenario_name": "Cyl8pi",
    "template": "model.k",
    "position_source": {"source_type": "grid_nxm", "grid_nxm": {"nx": 2, "ny": 2, "bbox": [-20, -20, 20, 20]}},
    "cumulative": {"num_steps": 1, "mode_sequence": ["IMPACT"]}},
    postprocess={"enabled": True, "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
                 "auto_deep": True, "auto_deep_mode": "inline", "auto_impact": True})

mode("IMPACT", "충격 시나리오 — 모델 윗면 격자 위치마다 구·다단 실린더 충격추 낙하",
     category="시나리오 모드", aliases=["impact", "충격", "낙추", "전위치", "ball drop", "cylinder"],
     when=["화면·배면 여러 위치에 충격추를 떨어뜨려 취약 위치를 찾을 때"],
     syntax=['cumulative.mode_sequence: ["IMPACT"]', "position_source: 위치 목록", "simulation_params.impact / wall"],
     keys=[
         K("position_source.source_type", "문자", "grid_nxm", "grid_nxm(nx, ny, bbox) | grid_spacing(spacing_x, spacing_y, bbox) | manual"),
         K("position_source.grid_nxm.bbox", "[xmin,ymin,xmax,ymax]", "모델 bbox", "위치 격자 범위"),
         K("simulation_params.impact.type", "Sphere | cylinder", "Sphere", "충격추 형상"),
         K("simulation_params.impact.dimension", "실수", "0.008", "구 반지름"),
         K("simulation_params.impact.cylinder_stages", "배열", "-", "[front, back] 또는 [front, mid, back]. 각 role, diameter, outer_diameter(front), height, density, youngs_modulus, poisson"),
         K("simulation_params.impact.height", "실수", "0.5", "낙하 높이 (모델 단위)"),
         K("simulation_params.impact.gravity", "실수", "재질 밀도로 판정", "자유낙하 g (모델 단위, --help units)"),
         K("simulation_params.impact.mesh_size / offset_distance", "실수", "0.001 / 1e-5", "충격추 요소 크기 / 초기 간격"),
         K("simulation_params.impact.density / youngs_modulus / poisson_ratio", "실수", "7.85e-9 / 2.01e5 / 0.3", "구 재질 (실린더는 stage 값 우선, back 단 = 본체)"),
         K("simulation_params.impact.tFinal / dt / dtmin", "실수", "0.001 / 1e-6 / -", "시간"),
         K("simulation_params.wall.density / youngs_modulus / poisson_ratio / num_x,y,z", "-", "1e-9 / 1e4 / 0.3 / 10", "바닥 벽"),
     ],
     examples=[
         Example("반지름 8 mm 강구, 80×80 영역 3×3 위치, 500 mm 낙하", IMP_SPHERE,
                 verify={"kind": "cumulative", "doe_count": 9, "modes": ["IMPACT"], "step": 1,
                         "step_expect": {"Type": "Sphere", "Height": "500", "DensityImpactor": "7.85e-09",
                                         "YoungsModulusWall": "10000.0"}}),
         Example("3단 실린더 충격추 2×2 위치 + 자동 후처리", IMP_CYL,
                 explain=["back 단 재질이 KMM 의 *Impactor 슬롯(본체)으로 들어간다."],
                 verify={"kind": "cumulative", "doe_count": 4, "modes": ["IMPACT"], "step": 1,
                         "step_expect": {"Type": "cylinder", "DensityImpactor": "6.57e-09",
                                         "DensityImpactorFront": "1.18e-09", "YoungsModulusImpactorMid": "207000.0"}}),
     ],
     related=["DROP", "drop_weight_impact"])

VIB = _scenario("Vib_Explicit", {}, {
    "scenario_name": "VibZ",
    "template": "model.k",
    "vibration_source": {
        "source_type": "explicit_factors", "direction": "Z", "load_type": "Force", "relative_mode": "Explicit",
        "base_curve": {"kind": "inline", "points": [[0, 0], [0.0005, 500], [0.001, 0]]},
        "explicit_factors": [[1, 1.0], [2, 0.5]]},
    "cumulative": {"num_steps": 1, "mode_sequence": ["VIBRATION"]}})

mode("VIBRATION", "진동 시나리오 — 하중 곡선 × 파트 계수 (명시·캡별·회로별 DOE)",
     category="시나리오 모드", aliases=["vib", "진동", "vibration", "가진"],
     when=["부품별 가진 하중 케이스를 만들 때"],
     syntax=['cumulative.mode_sequence: ["VIBRATION"] (또는 "VIB")', "scenarios[].vibration_source"],
     keys=[
         K("vibration_source.source_type", "문자", "-", "explicit_factors(1 DOE) | per_cap(캡마다) | circuit_group(회로마다)", True),
         K("vibration_source.direction / load_type / relative_mode", "문자", "- / Force / Explicit", "X|Y|Z / Force|Acceleration"),
         K("vibration_source.base_curve", "객체", "-", '{"kind": "inline", "points": [[t, v], ...]} (2점 이상)'),
         K("vibration_source.explicit_factors", "[[pid, 계수], ...]", "-", "explicit_factors 입력"),
         K("vibration_source.per_cap", "{cap_pids, amplitude}", "-", "per_cap 입력"),
         K("vibration_source.circuit_group.circuits", "{이름: {parts, amplitude}}", "-", "circuit_group 입력"),
     ],
     examples=[Example("Z 방향 힘 펄스, 파트 1·2 계수 1.0·0.5", VIB,
                       verify={"kind": "cumulative", "doe_count": 1, "modes": ["VIBRATION"], "step": 1,
                               "step_expect": {"Direction": "Z", "LoadType": "Force", "RelativeMode": "Explicit"}})],
     notes=["진동 모드에는 dtmin 이 배선돼 있지 않다."],
     related=["THERM"])

THERM = _scenario("Therm_85C", {
    "thermal": {"thermal_type": "UniformChamber", "base_temp_C": 25, "target_temp_C": 85,
                "ramp_time_s": 0.001, "dt": 1e-06, "default_cte_1_K": 1.7e-05, "part_cte": {"1": 2.3e-05}}}, {
    "scenario_name": "Chamber85",
    "template": "model.k",
    "thermal_conditions": ["85C"],
    "cumulative": {"num_steps": 1, "mode_sequence": ["THERM"]}})

mode("THERM", "열 시나리오 — 균일 챔버 온도 열응력 또는 IC 발열 2-pass",
     category="시나리오 모드", aliases=["therm", "thermal", "열", "온도", "열응력", "icpower"],
     when=["고온 챔버 온도 변화에 의한 열응력", "IC 발열 → 온도장 → 구조 해석 (ICPower)"],
     syntax=['cumulative.mode_sequence: ["THERM"]', "scenarios[].thermal_conditions: 조건 이름 목록 (= DOE)",
             "simulation_params.thermal"],
     keys=[
         K("thermal_conditions", "문자 배열", '["THERM"]', "조건마다 DOE 1개"),
         K("simulation_params.thermal.thermal_type", "UniformChamber | ICPower", "UniformChamber", "열 하중 종류"),
         K("simulation_params.thermal.base_temp_C / target_temp_C", "실수", "25 / 85", "℃"),
         K("simulation_params.thermal.ramp_time_s / dt / dtmin", "실수", "1e-3 / 1e-6 / -", "승온 시간 / 출력 간격"),
         K("simulation_params.thermal.default_cte_1_K / part_cte", "실수 / {pid: cte}", "1.7e-5 / {}", "열팽창계수"),
         K("simulation_params.thermal.materials / heat_sources / timestep", "-", "-", "ICPower 전용 (전 파트 rho·hc·tc 필요)"),
     ],
     examples=[Example("25→85 ℃ 챔버, 파트 1 CTE 지정", THERM,
                       explain=["열해석은 배정밀 LS-DYNA SIF(_mpp_d) 가 필요하다."],
                       verify={"kind": "cumulative", "doe_count": 1, "modes": ["THERM"], "step": 1,
                               "step_expect": {"ThermalType": "UniformChamber", "TargetTempC": "85"}})],
     related=["VIBRATION"])

REMAP = _scenario("Drop_Remap_Drop", DROP_SIM, {
    "scenario_name": "RemapMat",
    "template": "model.k",
    "angle_source": {"source_type": "fibonacci_lattice", "fibonacci_lattice": {"num_points": 2}},
    "cumulative": {"num_steps": 3, "mode_sequence": ["DROP", "REMAP", "DROP"],
                   "step_params": {"2": {"op": "matdb", "config": {
                       "materials": [{"match": "*"}]}}}}})

mode("REMAP", "누적 스텝 사이에 KooRemapper 변환(재질 교체 등)을 끼우는 러너 전용 스텝",
     category="시나리오 모드", aliases=["remap", "kooremapper", "matdb", "재질교체"],
     when=["1차 낙하 후 재질·형상을 KooRemapper 로 바꾸고 2차 낙하를 이어갈 때"],
     syntax=['mode_sequence: ["DROP", "REMAP", "DROP"]', 'cumulative.step_params: {"<스텝번호>": {"op": ..., "config": {...}}}'],
     keys=[
         K("step_params.<n>.op", "문자", "-", "KooRemapper 명령 (matdb, map ...)", True),
         K("step_params.<n>.config", "객체", "-", "YAML ops 설정. model/output 은 러너가 넣는다"),
         K("step_params.<n>.argv", "배열", "-", "config 대신 위치 인자 (출력은 *_dti.k 로)"),
     ],
     examples=[Example("낙하 → matdb 재질 교체 → 누적 낙하", REMAP,
                       explain=["REMAP 스텝은 LS-DYNA 를 돌리지 않는다. 입력·출력 dynain 핸드오프는 러너가 한다.",
                                "KooRemapper 명령 옵션은 KooRemapper help matdb."],
                       verify={"kind": "cumulative", "doe_count": 2, "modes": ["DROP", "REMAP", "DROP"],
                               "step_params": {"2": {"op": "matdb"}}})],
     notes=['REMAP 만 있는 시퀀스는 DROP 경로를 타서 기본 angle_source(26 방향)만큼 DOE 가 생긴다.'],
     related=["DROP"])

PV = _j({"project_name": "PartValidation", "mode": "part_validation", "model_file": "model.k",
         "output_dir": "validation_output",
         "simulation_params": {"height": 100, "tFinal": 0.0005, "dt": 1e-05},
         "environment": {"koomeshmodifier_path": "/data/SmartTwinPreprocessor/bin/KooMeshModifier",
                         "sif_path": "/opt/apptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif",
                         "solver_command": "ls-dyna", "ncpu": 4, "memory": "4G", "partition": "normal"},
         "min_elements": 10, "except_pids": []})

mode("part_validation", "파트별 0° 낙하 검증 — 파트마다 독립 .k 로 쪼개 해석 가능 여부 사전 점검",
     category="워크플로우 (최상위 mode)", aliases=["validation", "검증", "파트검증", "사전점검"],
     when=["전각도 낙하 전에 어떤 파트가 단독으로도 터지는지(메시 불량) 찾을 때"],
     syntax=['최상위 "mode": "part_validation"', "model_file / output_dir / simulation_params / environment / min_elements / except_pids"],
     keys=[
         K("mode", "part_validation", "-", "워크플로우 선택", True),
         K("model_file", "경로", "-", "모델 .k (scenario.json 기준)", True),
         K("output_dir", "경로", "validation_output", "분할 결과"),
         K("simulation_params.height / tFinal / dt", "실수", "100 / 5e-4 / 1e-5", "검증 낙하 조건"),
         K("min_elements / except_pids", "정수 / 배열", "1 / []", "대상 파트 거르기"),
         K("environment.koomeshmodifier_path / sif_path / solver_command / ncpu / memory / partition", "-", "-", "실행 환경"),
     ],
     examples=[Example("요소 10 개 이상 파트 전부 100 mm 낙하 검증", PV,
                       explain=["prepare 가 KooMeshModifier 로 파트를 쪼갠다 (시간이 걸린다). submit → collect 로 PASS/FAIL 리포트."],
                       verify={"kind": "part_validation", "expect": {"mode": "part_validation", "min_elements": 10}})],
     related=["DROP"])

DWI = _j({"project_name": "BallDrop", "mode": "drop_weight_impact", "model_file": "model.k",
          "output_dir": "dwi_output",
          "simulation_params": {"tFinal": 0.001, "dt": 1e-06,
                                "impactor": {"type": "Sphere", "radius": 5.0, "height": 500,
                                             "density": 7.85e-09, "youngs_modulus": 200000.0, "poisson_ratio": 0.3},
                                "locations": {"mode": "grid", "margin": 0.9, "x_count": 3, "y_count": 3},
                                "generation_mode": "DampingSpring", "boundary_distance": 0.0,
                                "offset_distance": 0.05,
                                "wall": {"density": 7.85e-09, "youngs_modulus": 200000.0, "poisson_ratio": 0.3}},
          "environment": {"koomeshmodifier_path": "/data/SmartTwinPreprocessor/bin/KooMeshModifier",
                          "koochainrun_path": "/data/SmartTwinPreprocessor/bin/KooChainRun",
                          "ncpu": 4, "memory": "4G", "partition": "normal"}})

mode("drop_weight_impact", "(구) 전위치 부분충격 워크플로우 — IMPACT 시나리오와 별도 스키마",
     category="워크플로우 (최상위 mode)", aliases=["dwi", "balldrop", "부분충격"],
     when=["기존 drop_weight_impact 설정을 이어 쓸 때. 새 작업은 IMPACT 시나리오 권장"],
     syntax=['최상위 "mode": "drop_weight_impact"', "model_file / output_dir / simulation_params.impactor·locations·wall / environment"],
     keys=[
         K("simulation_params.impactor", "객체", "-", "type(Sphere|Cylinder), radius, height, density, youngs_modulus, poisson_ratio"),
         K("simulation_params.locations", "객체", "-", "mode(grid|list|lhs|part_center), x_count/y_count 또는 spacing, margin"),
         K("simulation_params.generation_mode", "문자", "DampingSpring", "DampingSpring | OutsideRigidPart | OutsideRigidElement"),
         K("simulation_params.boundary_distance / offset_distance", "실수", "0 / -", "강체화 반경 / 초기 간격"),
     ],
     examples=[Example("구 충격추 3×3 위치", DWI,
                       verify={"kind": "drop_weight_impact", "expect": {"mode": "drop_weight_impact"}})],
     notes=["이 워크플로우는 mm 단위를 전제해 Gravity,9810 을 넘긴다. 다른 단위계면 simulation_params.gravity 로 바꿀 것."],
     related=["IMPACT"])

CMDS = [
    ("prepare", "scenario.json → runner_config.json", "KooChainRun prepare scenario.json [-o runner_config.json]"),
    ("submit", "Slurm 제출", "KooChainRun submit runner_config.json --nodes 2 --jobs-per-node 4 [--ncpu-per-job 8] [--partition normal] [--sequential]"),
    ("status", "진행 상황", "KooChainRun status runner_config.json [--watch]"),
    ("collect", "결과 수집", "KooChainRun collect runner_config.json [결과폴더]"),
    ("postprocess", "후처리 수동 실행", "KooChainRun postprocess runner_config.json"),
    ("diagnose", "실패 원인 진단", "KooChainRun diagnose [테스트폴더]"),
    ("rerun", "실패·미완료 재실행", "KooChainRun rerun [테스트폴더] [--dry-run] [--does 3,7] [--exclude-nodes node002]"),
    ("stop", "잡 전부 취소", "KooChainRun stop [테스트폴더]"),
    ("run", "계산 노드에서 DOE 하나 실행 (submit 이 부른다)", "KooChainRun run runner_config.json --doe 1 [--resume]"),
    ("reprioritize", "대기 잡 우선순위 재배치", "KooChainRun reprioritize [테스트폴더] [--apply] [--radius-deg 25]"),
    ("harvest", "취약 조건 JSON 추출", "KooChainRun harvest [테스트폴더] [--top 20] [--hot-only] [--yield 350]"),
]
for name, summary, usage in CMDS:
    mode(name, summary, category="명령", syntax=[usage, f"전체 옵션: KooChainRun {name} --help"])


CATALOG = Catalog(
    tool="KooChainRun",
    tagline="누적·DOE CAE 해석 자동화 (scenario.json → Slurm 제출 → 수집·후처리)",
    usage=["KooChainRun <명령> [인자]            (명령별 옵션: KooChainRun <명령> --help)",
           "KooChainRun --help [모드·명령·검색어]"],
    overview=["기본 흐름: scenario.json 작성 → prepare → submit → status → collect / postprocess.",
              "scenario.json 모드는 cumulative.mode_sequence (DROP·IMPACT·VIBRATION·THERM·REMAP) 로,",
              "별도 워크플로우는 최상위 mode (part_validation·drop_weight_impact) 로 고른다."],
    modes=MODES, topics=TOPICS, mode_label="모드·명령",
    footer=["KooChainRun --help commands                   명령 순서",
            "KooChainRun --help environment                환경 블록",
            "KooChainRun --help postprocess_json           자동 후처리 설정",
            "KooChainRun --help units                      단위·높이 함정"],
)
