# pyKooCAE 자동화 현황 인벤토리 + IC 파워 발열·열응력 자동화 계획

작성일: 2026-06-10 / 기준 코드: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE` (commit 381ba31)

---

# Part 1 — 자동화 현황 인벤토리

## 1.1 검증 완료된 자동화 (mode × DOE 소스 × 검증 상태)

| 모드 | DOE 소스 | 소스 종류 | 검증 상태 | 검증 예제 |
|---|---|---|---|---|
| DROP_ATTITUDE (전각도 낙하) | `angle_source` | `cuboid_geometry`(26방향), `fibonacci_lattice`(임의 N점), `pitching_sweep`, `rolling_sweep`, `case_txt_file` — 5종 | **PASS** — Fibonacci 100각도 e2e 100/100 완료 | `Examples/HWWarrantyDropTest/Tests/Test_005_Fibonacci_100/`, `Examples/scenario_examples/drop_attitude_example.json` |
| DROP_WEIGHT_IMPACT_TEST (전위치 부분충격) | `position_source` | `grid_nxm`(bbox 자동 계산), `grid_spacing`, `manual` — 3종 | **PASS** — 5×5=25위치 e2e + 단위계 silent miss 수정 (381ba31) | `Examples/ImpactTest/Tests/Test_Impact_Grid5x5/`, `/data/koopark/Test_Impact_A/output/checkpoint_doe_*.json` |
| VIBRATION_LOAD (전시나리오 진동) | `vibration_source` | `explicit_factors`, `per_cap`, `circuit_group` — 3종 등록 (open-set registry, `cap_combination`/`curve_library` 예약) | **PASS** — 진동 정식 카드 + DROP/IMPACT/VIBRATION 3모드 동시 e2e (381ba31) | `Examples/scenario_examples/vibration_example.json` |
| DROP 다단계 누적 (mode_sequence) | dynain 체인 | `["DROP","DROP","DROP"]` 높이/각속도 변화 | **PASS** — dynain 이어받기 검증 완료 (이종 모드 혼합은 미검증) | `Examples/HWWarrantyDropTest/docs/CustomScenarios/scenario_height_variation.json` |

세 DOE 축 모두 **registry/enum 기반 zero-hardcode 자동화** 완료. 특히 `VibrationSource.py`의 `@register_vibration_source` 데코레이터 패턴은 source_type을 코드 수정 없이 확장할 수 있는 표준 plugin 패턴으로 자리잡았다 — Part 2의 열 소스 설계가 답습할 결.

## 1.2 KooChainRun 워크플로우 자동화

CLI 9개 서브커맨드 (`KooChainRun.py`):

| 단계 | Subcommand | 역할 |
|---|---|---|
| 설계 | `prepare` | scenario.json → runner_config.json (`CumulativeDesigner`) + helper sh 자동 생성 |
| 제출 | `submit` | Slurm 제출. `--mode` cumulative/large-scale + runner_config의 `mode`로 `part_validation`/`drop_weight_impact` 우선 분기 → 총 4종 실행 모드 |
| 실행 | `run` | 컴퓨트 노드 내 단일 DOE 파이프라인 (KooMeshModifier → LS-DYNA → dynain) |
| 모니터링 | `status` | jobs.json + sacct/squeue 조합 |
| 관리 | `stop` / `rerun` / `diagnose` | 전체 취소 / 실패 DOE 단위 재제출(`--exclude-nodes`) / 라이선스 에러 검출 포함 원인 진단 |
| 수집 | `collect` / `postprocess` | 결과 수집 / 후처리 수동 트리거 |

prepare 시 `rerun.sh`, `stop.sh`(kill_dyna.sh 연쇄), `diagnose.sh`, `copy.sh`(scratch→NFS 동기화) 가 self-contained로 자동 생성된다.

## 1.3 KooMeshModifier 모드 전체 (30종)

| 분류 | 모드 |
|---|---|
| 하중/시나리오 | DROP_ATTITUDE, DROP_WEIGHT_IMPACT_TEST, VIBRATION_LOAD |
| DOE/변동 | TRANSLATION_DOE, PART_LOCATION_DOE (norm/lhs), DIMENSIONAL_TOLERANCE, PART_MORPHING, TRANSFORM |
| 파트/재료 치환 | PART_EXCHANGE, MATERIAL_EXCHANGE, ELASTIC_TO_RIGID, RIGIDIFY_SMALL_DT, ERODING_MIN_DT |
| 메시 | REMESH_TETRA, DEFEATURE_MESH, PART_VALIDATION_SPLIT, FEM_TO_IGA |
| 연결/접촉 | WEAK_COUPLING, CNRB→BEAM, CONVERT_CNRB_TO_SOLID, COHESIVE_BETWEEN_CONFORMAL_MESHES, CONTACT_AUTO_DECOMPOSITION, REMOVE_DUPLICATE_TIED_CONTACTS |
| 잔류/초기상태 | WARPED_PART, WARPED_TO_INITIAL_STRESS_PART, DYNAIN_TO_INITIAL |
| 파일/통합 | SIMULATION_AUTOMATION, DECOMPOSE_K, MERGE_K, IMPORT_MERGE_K |

**THERMAL 계열 모드는 modeList에 존재하지 않는다** (grep 'thermal' 0건) — Part 2의 핵심 갭.

## 1.4 후처리 자동화 (KooD3plotReader 연동 — 구현 완료)

| 기능 | 내용 |
|---|---|
| `deep_report.sh` | 단일 시뮬 d3plot → `koo_deep_report` (per-job, run_dir 위치) |
| `sphere_report.sh` | 162방향 통합 → `koo_sphere_report` (normal termination 필터) |
| 자동 트리거 | scenario.json `postprocess.auto_deep` → 시뮬 완료 후 자동 실행; `auto_sphere` → dependent Slurm job (`SlurmSubmitter.py:97-136`) |
| 수동 트리거 | `KooChainRun postprocess --deep/--sphere/--all` |
| 회귀 안전 | `postprocess` 옵션 없으면 전체 skip; SIF 미존재 시 에러 후 skip |

## 1.5 미완/부분 자동화 영역 (gap 표)

| Gap | 현재 수준 | 비고 |
|---|---|---|
| **THERM 모드** | Runner 스캐폴딩만 — deck 생성 전구간 미구현 | Part 2 대상 |
| 이종 모드 혼합 누적 (DROP→VIBRATION 등) | 미검증 | mode_sequence 인프라는 존재 |
| vibration `cap_combination`/`curve_library` | registry 주석 상태 | 패턴은 확립됨 |
| REMESH_TETRA 고도화 | 계획 단계 (`project_remesh_tetra_plan.md`) | 외곽면 품질 + 최소 dt 보장 |
| 후처리 설계 문서 | docstring만 존재, docs/ plan 부재 | 문서화 부채 |

---

# Part 2 — IC 파워 발열 + 열응력 자동화 계획

## 2.1 현재 THERM 모드 수준 진단

**결론: "config 문자열 생성까지만" — 체인 중간에서 silent miss (IMPACT/VIBRATION에서 최근 고친 패턴과 동일).**

| 레이어 | 상태 | 근거 |
|---|---|---|
| scenario.json 입력 (`mode: THERM`, `target_temp_C`, `hold_time_s`) | ✅ 수용 | `KooDynaAutomaticSimulationScriptGenerator.py:987-988` |
| TemplateManager (THERMAL_FIRST / THERMAL_CUMULATIVE / THERMAL_TO_DROP) | ✅ 선택 로직 완비 | `Runner/TemplateManager.py` |
| Runner → KooMeshModifier config (`**ThermalCycle` 블록) | ✅ 생성 | `CumulativeScenarioRunner.py:1241-1262` (단, InitialTemperature=25, RampTime=600 **하드코딩**) |
| KooMeshModifier 모드 파서 | ❌ THERMAL_CYCLE 분기 없음 → 블록 조용히 무시 | `KooMeshModifier.py` L277-325, 디스패치 L2729-2783 |
| ThermalSet.k 생성기 | ❌ thermal 코드 0건 | `KooDynaAdvancedModification.py` |
| Runner `_find_input_file` | ⚠️ `ThermalSet.k`를 기대 → **실행 시 파일 없음으로 실패 확정** | `CumulativeScenarioRunner.py:1589` |
| LS-DYNA 열 카드 (HEAT_GENERATION, CONTROL_THERMAL, MAT_THERMAL, CTE, INITIAL_TEMPERATURE) | ❌ 전무 | grep 0건 |

또한 현 설계는 **균일 온도 램프-홀드(방법 3 간이법)** 개념이라, IC 발열에 의한 국소 온도구배는 원리적으로 표현 불가. 매뉴얼 명시: "Nodal temperatures will be uniform throughout the model" (*LOAD_THERMAL_LOAD_CURVE, Vol I 33-160).

## 2.2 목표 워크플로우

```
scenario.json (ic_power_map + thermal_env + 기존 THERM params)
  → prepare: CumulativeDesigner가 ThermalLoadSpec 정규화 (ThermalSource registry)
  → run (Run_<id>/):
      [Step A] KooMeshModifier THERMAL_GENERATION 모드
               → ThermalSet.k + .done 강제 출력 (VibrationSet.k 결 답습)
      [Step B] LS-DYNA 열해석 (SOLN=1, implicit thermal, 큰 dt) → d3plot 온도장
      [Step C] LS-DYNA 구조해석 (SOLN=0) — *LOAD_THERMAL_D3PLOT으로 온도장 매핑
               + *MAT_ADD_THERMAL_EXPANSION → 열응력/열변형
  → collect / postprocess (deep_report 재활용)
  → (옵션) THERMAL_TO_DROP: dynain 이어받아 고온 상태 낙하 누적
```

채택 커플링: **방법 1 (순차 열→구조)**. 근거 — (a) IC 발열·전도·대류의 국소 온도장은 열해석 없이는 불가, (b) 1800 s 홀드 준정적 시간스케일은 implicit thermal로 저비용, (c) 완전 커플(SOLN=2)은 비용 대비 이득 없음. 방법 3(현 균일 온도)은 `uniform_ramp` 소스 타입으로 **하위호환 유지**.

## 2.3 LS-DYNA 키워드 설계 (R16 매뉴얼 기준)

**Run A — 열해석 deck (ThermalSet.k)**

| 카드 | 핵심 필드 | 설계 |
|---|---|---|
| `*CONTROL_SOLUTION` | SOLN=1 | 열 단독 (Vol I 12-527) |
| `*CONTROL_THERMAL_SOLVER` | ATYPE=1(과도), SOLVER=11(직접) 또는 12(MPP CG) | SOLUTION 카드 필수 전제 |
| `*CONTROL_THERMAL_TIMESTEP` | TS=1(가변), TIP=1.0, ITS=초기증분 | hold_time 1800 s 커버 |
| `*MAT_THERMAL_ISOTROPIC` | TRO, HC, TC | **전 파트 필수** + *PART TMID 연결 |
| `*INITIAL_TEMPERATURE_SET` | 초기온도 (scenario의 `initial_temp_C`) | 하드코딩 25 제거 |
| `*LOAD_HEAT_GENERATION_SET_SOLID` | SID(칩별 *SET_SOLID), LCID=0, MULT=q''' | q''' = P/V_chip; 시간 가변 파워는 LCID>0 곡선 |
| `*BOUNDARY_CONVECTION_SET` | HLCID=0/HMULT=h, TLCID=0/TMULT=T∞ | 외기 노출면 segment set |
| `*BOUNDARY_TEMPERATURE_SET` (옵션) | 챔버 고정온도 | |
| `*DATABASE_TPRINT` + d3plot | 온도 출력 | Run B 입력 |

**Run B — 구조 deck 추가 카드**

| 카드 | 설계 |
|---|---|
| `*LOAD_THERMAL_D3PLOT` | Run A d3plot 온도장 매핑 (실행라인 `T=tpf`; 이름 충돌 주의, Vol I 33-159) |
| `*MAT_ADD_THERMAL_EXPANSION` | 파트별 CTE α(T) — 기존 구조 MAT 무수정 부여 (Vol II 2-139) |

복사(`*BOUNDARY_RADIATION_SEGMENT`)는 P3 옵션 — 사용 시 **Kelvin 절대온도 필수**라 단위계 분기 필요.

## 2.4 단위계 (ton-mm-s, 에너지=mJ / 파워=mW)

| 물리량 | SI | ton-mm-s | 환산 |
|---|---|---|---|
| 파워 P | W | mW | ×10³ (3 W = 3000 mW) |
| 체적발열률 q''' | W/m³ | mW/mm³ | ×10⁻⁶ |
| 열전도율 TC | W/(m·K) | mW/(mm·K) | ×1 (수치 동일) |
| 비열 HC | J/(kg·K) | mJ/(ton·K) | ×10⁶ |
| 밀도 TRO | kg/m³ | ton/mm³ | ×10⁻¹² |
| 대류계수 h | W/(m²·K) | mW/(mm²·K) | ×10⁻³ |

예: 칩 10×10×1 mm(V=100 mm³)에 3 W → q''' = 3000/100 = **30 mW/mm³** → `*LOAD_HEAT_GENERATION_SET_SOLID` / `SID, 0, 30.0`. q''' 환산은 `power_W`+파트 체적에서 **코드가 자동 계산** (사용자는 W 단위 입력) — IMPACT 단위계 silent miss 재발 방지를 위해 환산 로그를 Korean 메시지로 명시 출력.

## 2.5 구현 Phase 분해

| Phase | 작업 | 파일 | 검증 기준 (e2e 게이트) |
|---|---|---|---|
| **P1: deck 생성 체인 복구** (작업량 中) | ① KooMeshModifier modeList에 `THERMAL_CYCLE` 추가 + `**ThermalCycle` 파서/디스패치 분기 ② KooDynaAdvancedModification에 ThermalSet.k 생성기 (`Run_<id>/ThermalSet.k` + `.done` — VibrationSet.k 결 그대로) ③ 우선 방법 3(균일 램프-홀드, *LOAD_THERMAL_LOAD_CURVE + CTE)으로 end-to-end 관통 ④ InitialTemperature/RampTime 하드코딩 → params 노출 | `KooMeshModifier.py`, `KooDynaAdvancedModification.py`, `CumulativeScenarioRunner.py` | `/data/koopark/Test_*` NFS에서 THERM 단일 스텝 sbatch → ThermalSet.k 생성 + normal termination + 열변형 d3plot 확인. **빌드 필수** (Nuitka, `build_KooChainRun_python312.sh` + MeshModifier 빌드) |
| **P2: IC 발열 순차 열→구조** (작업량 大) | ① `Runner/ThermalSource.py` 신설 — `@register_thermal_source` registry (`uniform_ramp`, `ic_power_map`, 향후 `power_profile_csv`) ② ic_power_map → 파트 체적 조회 + q''' 환산 + *SET_SOLID/*LOAD_HEAT_GENERATION 생성 ③ MAT_THERMAL/CONVECTION/CONTROL 카드 writer ④ Run A→Run B 2-pass 실행 시퀀스 (Runner가 d3plot 경로 전달, *LOAD_THERMAL_D3PLOT) | `Runner/ThermalSource.py`(신규), `Runner/CumulativeDesigner.py`, `CumulativeScenarioRunner.py`, `KooDynaAdvancedModification.py` | 단순 2파트 모델(칩+보드) 3 W 발열 e2e: 온도 상승 해석해(ΔT=Pt/mc 단열 근사) 대비 오차 확인 + 열응력 발생 확인 |
| **P3: 누적 통합 + 후처리** (작업량 中) | ① THERMAL_TO_DROP 템플릿 실동작 (열응력 dynain → DROP 이어받기) ② THERMAL_CUMULATIVE 온도장 이월 ③ deep_report 열 결과 항목 ④ 복사 BC/온도의존 물성 옵션 | `TemplateManager.py`, `PostprocessShellGenerator.py` | THERM→DROP 2스텝 mode_sequence e2e PASS + MODE_CONDITION_Reference.md HOT85/COLD-40 "⚠️"→"✅" 갱신 |

각 Phase 종료마다 사용자 검사 게이트 — 자가 진행 금지, bin mtime 확인 (`feedback_verify_each_step` 철칙).

## 2.6 scenario.json 스키마 제안 (zero-hardcode)

```json
{
  "mode_sequence": [{"mode": "THERM", "condition": "HOT85"}],
  "thermal_source": {
    "source_type": "ic_power_map",
    "initial_temp_C": 25,
    "duration_s": 1800,
    "heat_sources": [
      {"part_id": 101, "power_W": 3.0},
      {"part_id": 102, "power_W": 1.5,
       "power_curve": [[0, 0], [10, 1.5], [1800, 1.5]]}
    ],
    "convection": {"h_W_m2K": 10.0, "ambient_temp_C": 85,
                   "surfaces": "auto_external"},
    "thermal_materials": {
      "default": {"hc_J_kgK": 900, "tc_W_mK": 1.0},
      "per_part": {"101": {"hc_J_kgK": 700, "tc_W_mK": 150}}
    },
    "expansion": {"per_part": {"101": {"cte_1_K": 2.6e-6}},
                  "default_cte_1_K": 1.7e-5},
    "coupling": "sequential"
  }
}
```

설계 원칙: ① `source_type`은 ThermalSource registry open-set — `uniform_ramp`(기존 THERM 하위호환), `ic_power_map`, 향후 타입 무코드수정 추가 ② 물성 입력은 SI, 환산은 코드 책임 ③ `surfaces: "auto_external"`은 robust_contact의 외곽면 추출 로직 재사용 ④ VibrationSource의 `VibrationLoadSpec`처럼 `ThermalLoadSpec` dataclass로 정규화 후 하류 전달.

## 2.7 위험 요소 + 대응

| 위험 | 내용 | 대응 |
|---|---|---|
| Silent miss 재발 | 파서 미인식 블록이 조용히 무시되는 구조적 패턴 (THERM에서 현재 진행형) | P1에서 **미인식 `**Block` 경고/실패 처리** 추가; ThermalSet.k 부재 시 Runner가 명시적 에러 |
| MAT_THERMAL 누락 파트 | 열해석은 전 파트 TMID 필수 — 하나라도 빠지면 solver 에러 | `default` 물성 폴백 + prepare 단계 사전 검증 리포트 |
| 2-pass 실행 복잡도 | Run A d3plot → Run B 경로 전달, d3plot 이름 충돌 (Vol I 33-159 경고) | Run_<id> 내 서브디렉토리 분리 (`thermal/`, `structural/`); 기존 dynain 체인 패턴 준용 |
| 단위 환산 실수 | HC ×10⁶, h ×10⁻³ 등 자릿수 사고 | 환산표 단위테스트 + 환산 결과 한국어 로그 출력 (IMPACT 단위계 사고 교훈) |
| 복사 BC 절대온도 | Celsius 기반 deck에 radiation 추가 시 오답 | P3까지 radiation 보류; 도입 시 Kelvin 오프셋 명시 검증 |
| SIF solver 기능 | 사용 중 LS-DYNA 빌드의 thermal/implicit 라이선스·MPP SOLVER 지원 여부 미확인 | P1 착수 전 최소 thermal 카드 수동 deck으로 컴퓨트 노드 smoke test |
| Nuitka 배포 불일치 | 소스 수정 후 .bin 미재빌드 시 구버전 실행 | 매 Phase 빌드 + bin mtime 확인 의무화 |

**핵심 요약**: 3대 DOE 축(전각도/전위치/진동)은 registry 기반 자동화 + e2e PASS로 완성 단계이며, THERM만 Runner 스캐폴딩에서 끊겨 있다. 진동 모드가 확립한 결(registry 소스 → KooMeshModifier 모드 분기 → `Run_<id>/XxxSet.k` + `.done` → e2e 게이트)을 그대로 이식하면, P1(간이 균일온도 관통)→P2(IC 파워맵 순차 열-구조)→P3(누적 통합)의 3단계로 IC 발열 열응력 자동화를 기존 아키텍처 변경 없이 달성할 수 있다.

---

# 부록 — 조사 상세 (Survey Lens 원문)


## 부록: survey_cli

## KooChainRun subcommand 표

| Subcommand | 역할 (help 인용) | 구현 |
|---|---|---|
| `prepare` | "Generate runner configuration from scenario" | `cmd_prepare` (L345) |
| `submit` | "Submit jobs to Slurm cluster" | `cmd_submit` (L791) |
| `status` | "Check execution status" | `cmd_status` (L1962) |
| `run` | "Run single DOE pipeline on compute node" | `cmd_run` (L1918) |
| `collect` | "Collect simulation results" | `cmd_collect` (L1991) |
| `stop` | "제출된 모든 작업 취소" | `cmd_stop` (L2038) |
| `rerun` | "실패/미완료 DOE만 재실행" | `cmd_rerun` (L2337) |
| `diagnose` | "실패 DOE 원인 진단" | `cmd_diagnose` (L2609) |
| `postprocess` | "KooD3plotReader 후처리 수동 실행" | `cmd_postprocess` (L2509) |

**submit mode 분기** (`--mode choices=['large-scale', 'cumulative']`, L91-92): CLI 플래그 외에 runner_config의 `rc.get("mode")`로 `part_validation` (L803), `drop_weight_impact` (L808) 워크플로우 우선 분기 → 총 4종 실행 모드.

## Runner/ 모듈 표 (docstring 인용)

| 모듈 | 역할 |
|---|---|
| `CumulativeDesigner` | "Cumulative Scenario Designer (Stage 1)" — 사용자 JSON 설정 → runner_config.json 생성 |
| `CumulativeScenarioRunner` | "독립 실행자" — runner_config.json 읽고 실행 |
| `SimplifiedExecutor` | "Simplified Cumulative Scenario Executor (Stage 2: Executor)" |
| `LargeScaleDOEManager` | "대규모 DOE 관리 시스템 (수백~만 개 해석)" |
| `JobManager` | "Slurm Job 관리 모듈" — 추적, 취소, 재실행, 실패 진단 |
| `SlurmSubmitter` | "Slurm 병렬 제출" — 각 시나리오를 독립 Slurm Job으로 제출 |
| `StepConfigBuilder` | "DROP_ATTITUDE step_config 생성 공통 모듈" (cumulative + large-scale 공용) |
| `VibrationSource` | "Registry + Decorator dispatch for vibration load sources" — `vibration_source` 블록 → `VibrationLoadSpec` 정규화 |
| `DropWeightImpactWorkflow` | "전위치 부분충격 시뮬레이션 워크플로우" (drop_weight_impact 모드) |
| `PartValidationWorkflow` | "파트별 낙하 검증 워크플로우" |
| `DirectInputWorkflow` | "낙하 각도 정보 없이 직접 입력 파일로 LS-DYNA 실행" |
| `TemplateManager` | "템플릿 자동 선택 시스템" — Step별 템플릿 자동 선택 |
| `PostprocessShellGenerator` | "KooD3plotReader 후처리 sh 스크립트 텍스트 생성" (deep_report.sh 등) |
| `AliasManager` | "별칭 관리 유틸리티" |
| `AngleSourceParser` | "각도 소스 파서 (Priority 3)" |
| `AngleMixingStrategy` | "각도 믹싱 전략 (Priority 6)" |
| `CaseTxtParser` | "Case txt 파일 파서 (Priority 1)" |
| `ImpactPositionSource` | "충격 위치 소스 파서" |
| `ToleranceDOEGenerator` | "Tolerance/DOE 시스템 (Priority 4)" |
| `DOEParallelOptimizer` | "DOE 병렬 처리 최적화 시스템" |
| `NodeOccupancyMonitor` | "노드 점유율 모니터링 및 통계" |
| `PathResolver` | "pyKooCAE 실행 파일 경로 자동 탐색" |
| `_test_vibration_load_curve_roundtrip` | vibration load curve 왕복 테스트 |

파일: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/KooChainRun`, `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Runner/`

## 부록: survey_modes

KooMeshModifier 모드 전체 인벤토리 (modeList 30개, THERMAL 계열 모드는 존재하지 않음 — grep 'thermal' 0건):

| 모드 | 하는 일 (추정) |
|---|---|
| DROP_ATTITUDE | 낙하 자세(각도) 변환 + 낙하 시뮬 카드 생성 (`DropAttitude`) |
| DROP_WEIGHT_IMPACT_TEST | 낙하추 충격시험 모델 자동 생성; 부분강체/파트별 변형 지원 (`DropWeightImpactTest*`, Wall/Sphere/Cylinder 임팩터 생성) |
| VIBRATION_LOAD | 진동 하중 카드(VibrationSet.k) 생성 (`VibrationLoad`) |
| TRANSFORM | 파트/모델 이동·회전 변환 (`Transform`) |
| TRANSLATION_DOE | 위치 이동 DOE 케이스 생성 |
| PART_LOCATION_DOE | 파트 위치 DOE 샘플링 (norm/lhs 분포 지원) |
| DIMENSIONAL_TOLERANCE | 치수 공차 변동 모델 생성 (List/Norm 변형 포함) |
| PART_MORPHING | 파트 형상 모핑 (PIDBox/Box 방식) |
| PART_EXCHANGE | 파트 교체 |
| MATERIAL_EXCHANGE | 재료 카드 교체 |
| ELASTIC_TO_RIGID | 탄성 파트 → MAT_RIGID 변환 |
| RIGIDIFY_SMALL_DT | stable dt 이하 요소를 MAT_RIGID 파트로 분리 + 접촉 제외 (v40~42 신규) |
| ERODING_MIN_DT | 최소 dt 기준 요소 삭제(eroding) 설정 |
| REMESH_TETRA | gmsh 기반 사면체 리메시 (`RemeshTetra`) |
| DEFEATURE_MESH | 메시 디피처링(소형 피처 제거) |
| PART_VALIDATION_SPLIT | 파트별 독립 .k 분할 + 0도 낙하 검증용 모델 생성 |
| WEAK_COUPLING | 약결합(weak coupling) 연결 생성 |
| CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM | CNRB → 빔 요소 변환 |
| CONVERT_CNRB_TO_SOLID | CNRB → 솔리드(실린더) 변환 (`ConvertCNRBtoSolidCylinder`) |
| WARPED_PART | 휨(warpage) 형상 파트 생성 |
| WARPED_TO_INITIAL_STRESS_PART | 휨 형상 → 초기응력 파트 변환 |
| COHESIVE_BETWEEN_CONFORMAL_MESHES | 컨포멀 메시 사이 cohesive 요소 삽입 |
| DYNAIN_TO_INITIAL | dynain 결과 → INITIAL_* 카드 변환 (누적 시뮬 체인용) |
| CONTACT_AUTO_DECOMPOSITION | 접촉 자동 분해(파트별 접촉 정의 생성) |
| REMOVE_DUPLICATE_TIED_CONTACTS | 중복 tied contact 제거 |
| SIMULATION_AUTOMATION | 시뮬레이션 자동화 통합 모드(여러 수정 일괄 실행) |
| FEM_TO_IGA | FEM 메시 → IGA 변환 |
| DECOMPOSE_K | .k 파일 분해(파트/키워드 단위 분할) |
| MERGE_K | 다중 .k 파일 병합 |
| IMPORT_MERGE_K | 외부 .k 임포트 후 병합 (`ImportMergeK`, simGenerator 연동) |

비고:
- 파일: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/occProject/Generators/KooMeshModifier.py` (modeList 244–332행, Generate* 디스패치 2351행~, `GenerateModifiedFile` 2691행~ elif 분기)
- 실행 백엔드: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py` — 모드 외 보조 자동화 단위로 Solid→TShell/Shell/StructuredSolid 변환(`ConvertSolidto*`, `ConvertUnstructuredtoStructured`), 명시적 해석 컨트롤/DB 카드 세팅(`SetControlandDatabaseExplicit`), 임팩터/벽 파트 생성기 보유
- DOE 분포 분기: norm/lhs (KooMeshModifier.py 632, 638행)

## 부록: survey_therm

LENS 3 — THERM 모드 구현 수준 분석 결과.

## 현재 구현 수준: "config 생성까지만" (체인 중간에서 silent miss)

**되는 것 (scenario.json → step_config):**
- scenario.json에서 `{"mode": "THERM", "condition": "HOT85", "params": {"target_temp_C": 85, "hold_time_s": 1800}}` 입력 수용 (`occProject/Generators/KooCAEManager/KooDynaAutomaticSimulationScriptGenerator.py:987-988`에 예제 존재)
- `Runner/TemplateManager.py`: THERM enum + 템플릿 3종 선택 로직 완비 — `THERMAL_FIRST`, `THERMAL_CUMULATIVE` (DYNAIN_TO_INITIAL→THERMAL_CYCLE), `THERMAL_TO_DROP` (열→낙하 전환)
- `Runner/CumulativeScenarioRunner.py:1241-1262`: THERM 분기가 KooMeshModifier config를 생성 — `*Mode THERMAL_CYCLE,1` + `**ThermalCycle` 블록 (TargetTemperature/HoldTime/InitialTemperature/RampTime)

**끊기는 지점 (KooMeshModifier → deck):**
- `occProject/Generators/KooMeshModifier.py`의 모드 파서(라인 277~325)는 `DROP_ATTITUDE`, `DYNAIN_TO_INITIAL`, `VIBRATION_LOAD`만 인식. **THERMAL_CYCLE 파싱 분기 없음** → config의 `**ThermalCycle` 블록이 조용히 무시됨 (IMPACT/VIBRATION에서 최근 고친 silent miss와 동일 패턴). 디스패치부(2729~2783)에도 THERMAL 분기 없음
- `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py`: thermal/temperature 관련 코드 **0건**. DropSet.k/DropWeightImpactTestSet.k/VibrationSet.k 강제 출력 코드는 있지만 ThermalSet.k 작성 코드 부재
- 반면 Runner의 `_find_input_file` (라인 1589)은 `ThermalSet.k`를 기대 → THERM 스텝 실행 시 파일 없음으로 실패 확정. 라인 1582 docstring의 "ThermalSet.k 강제된다"는 희망사항이지 실제 코드 아님
- `Examples/HWWarrantyDropTest/docs/MODE_CONDITION_Reference.md:118-120`도 HOT85/COLD-40 = "⚠️ 템플릿", HOT125 = "❌"로 자인

## 현재 파라미터
| 파라미터 | 노출 | 디폴트 |
|---|---|---|
| `target_temp_C` | scenario.json params | 85 |
| `hold_time_s` | scenario.json params | 1800 |
| InitialTemperature | **하드코딩** | 25 |
| RampTime | **하드코딩** | 600 |

## 빠진 것 (deck 레벨 전부)
- **IC 파워/발열원 없음**: heat_gen/HEAT 키워드 grep 0건 — `*LOAD_HEAT_GENERATION`, 파트별 발열 입력 경로 자체가 미설계
- **열경계 없음**: 대류(`*BOUNDARY_CONVECTION`), 복사, 챔버 온도 BC 미구현
- **열-구조 커플링 없음**: `*CONTROL_SOLUTION` (SOLN=2), `*CONTROL_THERMAL_SOLVER/TIMESTEP`, `*MAT_THERMAL_*`, `*MAT_ADD_THERMAL_EXPANSION`(CTE) 카드 생성 코드 전무
- **온도 초기화/이월 없음**: `*INITIAL_TEMPERATURE`, dynain에 온도장 이월 처리 없음 (THERMAL_CUMULATIVE 템플릿은 이름만 존재)
- ThermalSet.k 생성기 자체 (KooDynaAdvancedModification 측 runDirectoryMode 분기)

**요약**: THERM은 Runner/Template 레이어 스캐폴딩 + config 문자열 생성까지만 존재하고, KooMeshModifier 파서부터 LS-DYNA 열 카드 생성까지 전 구간 미구현. 진동(VibrationSet.k + .done) 패턴을 그대로 이식하는 작업이 필요한 상태.

## 부록: survey_doe

**LENS 4 — DOE 소스 자동화 현황 + 검증 상태**

**1. 전각도 낙하 (angle_source, 5종)** — `Runner/AngleSourceParser.py` / `Runner/CumulativeDesigner.py:453`
- `cuboid_geometry` (디폴트, 26방향: 면6+모서리12+꼭짓점8)
- `fibonacci_lattice` (구면 균등 N점 — 임의 개수 전각도)
- `pitching_sweep` / `rolling_sweep` (축별 각도 스윕)
- `case_txt_file` (사용자 정의 각도 목록)
- 검증: Fibonacci 100각도 e2e 완료 (`Examples/HWWarrantyDropTest/Tests/Test_005_Fibonacci_100/` — jobs.json/output 존재, DROP 100/100 PASS 이력). 검증 예제 `Examples/scenario_examples/drop_attitude_example.json`.

**2. 전위치 충격 (position_source, 3종)** — `Runner/ImpactPositionSource.py`
- `grid_nxm` (NxM 균등 그리드, bbox 모델에서 자동 계산), `grid_spacing` (간격 지정 그리드), `manual` (좌표 직접 지정)
- 검증: `Examples/ImpactTest/Tests/Test_Impact_Grid5x5/` 5x5=25위치 실행 이력 (`/data/koopark/Test_Impact_A/output/checkpoint_doe_*.json` 존재). 최근 커밋 381ba31에서 IMPACT 단위계 silent miss 수정 + e2e PASS.

**3. 진동 (vibration_source, 3종 등록 + open-set registry)** — `Runner/VibrationSource.py`
- `explicit_factors`, `per_cap`, `circuit_group` (등록 완료); `cap_combination`/`curve_library`는 주석 상태(미구현)
- zero-hardcode registry 패턴 (`@register_vibration_source`) — source_type 자유 확장 가능
- 검증: 커밋 381ba31 "진동 정식 카드 + 3 mode e2e PASS" — DROP/IMPACT/VIBRATION 3모드 동시 e2e 통과. 예제 `Examples/scenario_examples/vibration_example.json`.

**4. Cumulative 다단계 (mode_sequence)**
- `["DROP","DROP","DROP"]` 높이 변화 (`Examples/HWWarrantyDropTest/docs/CustomScenarios/scenario_height_variation.json`), `["DROP","DROP"]` 각속도 변화 예제 존재
- dynain 이어받기 방식 (KooMeshModifier → LS-DYNA → dynain 체인). DROP/IMPACT/VIBRATION 단일모드 + DROP 다단계 누적 검증 완료; 이종 모드 혼합(DROP→VIBRATION 등) 예제는 미확인.

**요약:** 3개 DOE 축 모두 registry/enum 기반 자동화 완료, 3모드 e2e PASS (commit 381ba31). 검증 예제 디렉토리: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/scenario_examples/`.

## 부록: survey_post

## LENS 5 — 후처리/리포트/잡관리 자동화 현황

### 후처리 자동화 (KooD3plotReader 연동 — 구현 완료)

| 기능 | 내용 | 상태 |
|---|---|---|
| deep_report.sh | 단일 시뮬 d3plot → `koo_deep_report` (per-job, run_dir 위치). `build_deep_report_sh()` (`Runner/PostprocessShellGenerator.py:22`) | 구현됨 |
| sphere_report.sh | 162방향 통합 → `koo_sphere_report` (output_dir 위치, normal termination 필터 포함). `build_sphere_report_sh()` (:81) | 구현됨 |
| 자동 트리거 | `scenario.json`의 `postprocess` 옵션 → `CumulativeDesigner`가 runner_config로 전파. `auto_deep`이면 시뮬 완료 후 자동 실행/sbatch (`CumulativeScenarioRunner.py:678`), `auto_sphere`면 dependent Slurm job 제출 (`SlurmSubmitter.py:97-136`) | 구현됨 |
| 수동 트리거 | `KooChainRun postprocess <config>` 서브커맨드 (`--deep`/`--sphere`/`--all`, default all). auto 옵션 없어도 prepare 시 생성된 sh 실행 가능 | 구현됨 |
| 회귀 안전 | `postprocess` 옵션 없으면 전체 skip. SIF 미존재 시 에러 메시지 후 skip | 구현됨 |
| 실행 방식 | Apptainer SIF 내 `python3 -m koo_deep_report` / `koo_sphere_report` | 구현됨 |

### 잡관리 (Runner/JobManager.py + CLI)

| 명령 | 구현 | 비고 |
|---|---|---|
| stop | `cancel_all_jobs()` (:240) | stop.sh가 `kill_dyna.sh`도 연쇄 호출 |
| rerun | `resubmit_does()` (:399) | DOE 단위 재제출, `--exclude-nodes` 지원 |
| diagnose | `diagnose_failures()` (:464) | 라이선스 에러 검출(`_check_log_for_license_error`), 로그 에러 발췌 |
| status | `get_doe_status()` (:291) | jobs.json + sacct/squeue 조합 |
| collect | CLI 서브커맨드 존재 | 결과 수집 |

**Helper 스크립트 자동 생성** (`KooChainRun:415`, prepare 시): `rerun.sh`, `stop.sh`, `diagnose.sh`, `copy.sh` — scenario.json의 `koochainrun_path`를 읽어 self-contained 실행. `copy.sh`는 로컬 scratch → NFS 동기화 (jobs.json 기반, `--all`/스레드 5개).

**문서 갭**: `docs/`에 postprocess 전용 plan/설계 문서 없음 (PLAN_ConformalMesh, FastDOE, IncludeAndIGA, wall_part만 존재). 후처리 파이프라인은 코드 docstring으로만 문서화됨.

## 부록: thermal_keywords

LS-DYNA Keyword User's Manual Vol. I, R16@e545952c7 (03/21/25) 기준 조사 결과.

## 1. *LOAD_HEAT_GENERATION_{SOLID|SET_SOLID|SHELL|SET_SHELL} (LOAD 33-67~68)

Card 1: `SID, LCID, MULT, WBLCID, CBLCID, TBLCID` (WB/CB/TB는 혈류 관류용, IC에선 미사용)
- SID: 요소 ID 또는 요소 셋 ID
- LCID: 체적 발열률 q''' 지정. "SI units are W/m³". **GT.0**: (time, q''') 곡선, **EQ.0**: MULT 값의 상수, **LT.0**: (temperature, q''') 곡선 (|-LCID| 입력)
- MULT: q''' 곡선 배율 (LCID=0이면 상수값 자체)
- Remark 1: *DEFINE_FUNCTION 참조 시 f(x,y,z,vx,vy,vz,temp,time) 가능

**IC 3W 발열 표현**: 칩 솔리드 요소를 *SET_SOLID로 묶고 q''' = P/V_chip. 예: 칩 10×10×1 mm (V=100 mm³), 3 W = 3000 mW → q''' = **30 mW/mm³** → `*LOAD_HEAT_GENERATION_SET_SOLID` / `SID, 0, 30.0` (ton-mm-s). 시간 가변 파워는 LCID>0 곡선(세로축 mW/mm³).

## 2. CONTROL 카드 (12-527, 12-568~570, 12-575~576)

- **\*CONTROL_SOLUTION**: Card 1 `SOLN, NLQ, ISNAN, LCINT, LCACC, NCDCF, NOCOPY, CRVP`. SOLN: EQ.0 구조만, **EQ.1 열해석 단독, EQ.2 구조-열 연성**
- **\*CONTROL_THERMAL_SOLVER** (*CONTROL_SOLUTION 필수 전제): Card 1 `ATYPE, PTYPE, SOLVER, -, GPT, EQHEAT, FWORK, SBC`. ATYPE: 0 정상상태/1 과도. SOLVER: 11 직접법, 12 대각 CG(MPP 기본) 등. SBC: Stefan-Boltzmann 상수(enclosure 복사용)
- **\*CONTROL_THERMAL_TIMESTEP**: Card 1 `TS, TIP, ITS, TMIN, TMAX, DTEMP, TSCP, LCTS`. TS: 0 고정/1 가변, TIP: 0.5 Crank-Nicolson / 1.0 완전음해(기본), ITS: 초기 열 시간증분

## 3. BOUNDARY 카드

- **\*BOUNDARY_CONVECTION_{SEGMENT|SET}** (5-30~31): Card 1 `SSID, PSEROD`(SET) 또는 `N1~N4`(SEGMENT); Card 2 `HLCID, HMULT, TLCID, TMULT, LOC`. h와 T∞ 모두 GT.0 시간곡선 / EQ.0 상수(MULT) / h는 LT.0 온도의존 곡선
- **\*BOUNDARY_TEMPERATURE_{NODE|SET}** (5-146): Card 1 `NID, TLCID, TMULT, LOC, TDEATH, TBIRTH`. TLCID=0이면 TMULT 상수온도
- **\*BOUNDARY_RADIATION_SEGMENT** (5-107~108, 5-115~116): Card 1 `N1, N2, N3, N4, TYPE(=1 환경복사)`; Card 2 `FLCID, FMULT, TLCID, TMULT, LOC`. f = σεF (방사율×형상계수×SB상수 곱을 한 계수로 입력). **주의(5-108 Remarks)**: 복사 시 절대온도 스케일(Kelvin) 필수, Celsius 불가

## 4. IC 발열 최소 카드 셋

```
*CONTROL_SOLUTION        (SOLN=1 또는 2)
*CONTROL_THERMAL_SOLVER  (ATYPE=1, SOLVER=11)
*CONTROL_THERMAL_TIMESTEP (TS=1, ITS=초기증분)
*MAT_THERMAL_ISOTROPIC   (TRO, HC, TC — 모든 파트 필수)
*INITIAL_TEMPERATURE_SET (초기온도)
*LOAD_HEAT_GENERATION_SET_SOLID (칩: LCID=0, MULT=q''')
*BOUNDARY_CONVECTION_SET (외기 노출면 h, T∞)
*DATABASE_TPRINT / d3plot 출력
```

## 5. ton-mm-s 단위 환산표 (에너지=mJ, 파워=mW)

| 물리량 | SI | ton-mm-s | 환산계수 |
|---|---|---|---|
| 파워 | W | mW | ×10³ (3 W = 3000 mW) |
| 체적발열률 q''' | W/m³ | mW/mm³ | ×10⁻⁶ |
| 열전도율 TC | W/(m·K) | mW/(mm·K) | ×1 (수치 동일) |
| 비열 HC | J/(kg·K) | mJ/(ton·K) | ×10⁶ |
| 밀도 TRO | kg/m³ | ton/mm³ | ×10⁻¹² |
| 대류계수 h | W/(m²·K) | mW/(mm²·K) | ×10⁻³ |
| SB상수 σ | 5.67e-8 W/(m²·K⁴) | 5.67e-11 mW/(mm²·K⁴) | ×10⁻³ |

예: Si 칩 — TRO=2.33e-9, HC=7.0e8, TC=148(수치 그대로), 3 W/100 mm³ → MULT=30.

소스 PDF: /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/docs/LS-DYNA/Vol_I_Chapters/{34_LOAD.pdf p67-68, 13_CONTROL.pdf p527/568-570/575-576, 06_BOUNDARY.pdf p30-31/107-108/115-116/146}

## 부록: thermal_coupling

## THERMAL LENS B — 열응력 커플링 3방법 비교

### 현재 THERM 모드 확인 (질문 3)
`/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Runner/CumulativeScenarioRunner.py:1241-1262` — THERM 모드는 `THERMAL_CYCLE` 블록(TargetTemperature/HoldTime/RampTime/InitialTemperature=25)만 생성. **균일 온도 램프-홀드 = 방법 3(간이)에 해당.** pyKooCAE 소스에 `*LOAD_THERMAL` writer는 없음(다운스트림 KooMeshModifier 바이너리 담당). 공간 온도구배·열전도 해석 없음.

### 비교표

| 항목 | 방법 1: 순차 | 방법 2: 완전 커플 | 방법 3: 간이 (현 THERM) |
|---|---|---|---|
| SOLN (*CONTROL_SOLUTION) | Run A: SOLN=1 → Run B: SOLN=0 | SOLN=2 | SOLN=0 (카드 불필요) |
| 온도장 | 국소 분포 (전도 해석) | 국소 분포 + 변형 피드백 | 전체 균일 (구배 없음) |
| IC 발열 표현 | 가능 (*LOAD_HEAT_GENERATION) | 가능 | 불가 |
| 비용 | 낮음 (열해석 implicit, 큰 dt) | 높음 (구조+열 동시) | 최저 |
| 비고 | d3plot 정밀도/이름 충돌 주의 (Vol I 33-159 Warnings) | *LOAD_THERMAL_*는 커플 해석에서 무시됨 (Vol I 33-151) | "Nodal temperatures will be uniform throughout the model" (Vol I 33-160) |

### 방법별 필요 카드

**방법 1 — 순차 (열 → 구조)**
- Run A (열만): `*CONTROL_SOLUTION` SOLN=1 (12-527) / `*CONTROL_THERMAL_SOLVER` (12-567, "thermal only or coupled... *CONTROL_SOLUTION also required") / `*CONTROL_THERMAL_TIMESTEP` / (비선형 시 `*CONTROL_THERMAL_NONLINEAR`, 12-566) / `*MAT_THERMAL_ISOTROPIC` (T01: HC, TC; TGRLC/TGMULT 자체발열, Vol II 3-2) + *PART의 TMID / `*INITIAL_TEMPERATURE` (28-115, "used in a thermal only or coupled" 해석용) / `*LOAD_HEAT_GENERATION` (IC 발열, 요소셋 체적열원) / `*BOUNDARY_CONVECTION` 등
- Run B (구조만): `*LOAD_THERMAL_D3PLOT` (33-159, "Temperatures computed in a prior thermal-only analysis... T=tpf on execution line") / `*MAT_ADD_THERMAL_EXPANSION` (Vol II 2-139, 임의 재료에 α(T) 부여) 또는 열탄소성 MAT

**방법 2 — 완전 커플 (SOLN=2)**
- `*CONTROL_SOLUTION` SOLN=2 ("Combined structural, multiphysics, and thermal") / `*CONTROL_THERMAL_SOLVER` + `_TIMESTEP` (+`_NONLINEAR`) / 구조 MAT + `*MAT_ADD_THERMAL_EXPANSION` / `*MAT_THERMAL_ISOTROPIC` (*PART TMID 연결) / `*INITIAL_TEMPERATURE` / `*LOAD_HEAT_GENERATION`, `*BOUNDARY_CONVECTION`
- 주의: `*LOAD_THERMAL_*`는 "ignored in a thermal only or coupled thermal/structural analysis" (33-151)

**방법 3 — 간이 (구조만, 온도 처방)**
- `*LOAD_THERMAL_LOAD_CURVE` (33-160: 균일 온도 T(t), t=0 온도가 기준온도) — 현 THERM 모드 등가
- 국소성 흉내: `*LOAD_THERMAL_VARIABLE` (33-16x: 노드셋별 T=TB+TS·f(t), type 4 — type 2와 혼용 불가)
- `*MAT_ADD_THERMAL_EXPANSION` 필수. `*INITIAL_TEMPERATURE`는 사용 안 함("For thermal loading in a structural only analysis, see *LOAD_THERMAL", 28-115)

### 권장 (질문 4): IC 발열 → 국소 온도 → 열응력
**방법 1 (순차) 권장.** 근거: (a) IC 발열·전도·대류로 형성되는 국소 온도장은 열해석 필수 — 방법 3은 원리적으로 불가(균일 온도만), (b) 1800 s 홀드 같은 준정적 시간스케일에서 SOLN=2는 구조 솔버가 전 구간 동행해야 해 비용 과다, (c) 변형→열 피드백(접촉 열저항 변화, 마찰열 FWORK)이 없는 전자기기 열응력은 단방향 커플로 충분. 흐름: 열-only(SOLN=1, *LOAD_HEAT_GENERATION으로 IC die 열원) → d3plot 온도장 → 구조-only(*LOAD_THERMAL_D3PLOT + *MAT_ADD_THERMAL_EXPANSION). 중간 단계 대안으로 *LOAD_THERMAL_VARIABLE(IC 주변 노드셋만 고온)을 현 THERM 모드 확장으로 쓰면 열해석 없이 국소성 1차 근사 가능.

인용: LS-DYNA R16 Vol I — 12-527(*CONTROL_SOLUTION), 12-566~567(*CONTROL_THERMAL_*), 28-115(*INITIAL_TEMPERATURE), 33-151(*LOAD_THERMAL 개요), 33-159(*LOAD_THERMAL_D3PLOT), 33-160(*LOAD_THERMAL_LOAD_CURVE); Vol II — 2-139(*MAT_ADD_THERMAL_EXPANSION), 3-2(*MAT_THERMAL_ISOTROPIC).
