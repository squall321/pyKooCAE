<!-- P2(IC 발열 열응력, 2-pass) 구현 체크리스트 -->
# P2 — IC 발열 정상상태 열응력 (T2 steady, T3 transient) 체크리스트

계획: [PLAN_ThermalStress_Automation.md](PLAN_ThermalStress_Automation.md) §6 P2 (2.1~2.6).
방식: **2-pass** — pass1 SOLN=1 thermal solve → 온도 d3plot → pass2 SOLN=0 구조 + LOAD_THERMAL_D3PLOT + CTE.

## 0. 스코핑 (177e332 가 깔아둔 빌딩블록)
- [x] `MAT_THERMAL_ISOTROPIC` (KooMaterialThermalIsotropic + CreateThermalIsotropicMaterial)
- [x] `MAT_ADD_THERMAL_EXPANSION` (KooMaterialAddThermalExpansion + Create, T1)
- [x] `SET_SOLID` (SolidElementSet + KooElement.CreateSolidSet/withID)
- [x] `LOAD_HEAT_GENERATION_SET_SOLID` (KooLoadHeatGenerationSetSolid + Create)
- [x] `LOAD_THERMAL_D3PLOT` (KooLoadThermalD3plot + Create)
- [x] `KooBoundaryConvection` 클래스 (단 Create/emit 경로 미확인)

## 1. 카드 emit 레이어 (클러스터 없이 단위검증 가능)
- [ ] **A. CONTROL 카드** (KooDynaControl.py): `KooControlSolution`(SOLN), `KooControlThermalSolver`(Card1, blank 31-40 컬럼 함정), `KooControlThermalTimestep` + 매니저 멤버/Set/write루프 → 단위 deck-golden
- [ ] **B. INITIAL_TEMPERATURE** (KooInitial.py): `*INITIAL_TEMPERATURE_SET`/`_NODE` + Create → deck-golden
- [ ] **C. BOUNDARY_CONVECTION_SET** (KooBoundary/Manager): Create + emit (segment set 경로) → deck-golden

## 2. 오케스트레이션
- [ ] **D. ICPower resolver** (KooThermalLoad.apply_thermal_load): `ThermalType=='ICPower'` 분기 — SET_SOLID(칩) + HEAT_GEN(q''') + THERMAL_ISOTROPIC(파트별) + PART TMID + CONTROL_SOLUTION(SOLN=1) + CONTROL_THERMAL_SOLVER + INITIAL_TEMPERATURE + CONVECTION 조립. SI→ton-mm-s 환산(resolver 한 곳). 현재 NotImplementedError.
- [ ] **E. Runner config 전달** (CumulativeScenarioRunner `_therm_get` ICPower 필드 + StepConfigBuilder) → step_config 골든
- [ ] **F. 2-pass 오케스트레이션** (CumulativeScenarioRunner): Run_<id>/thermal(pass1) → structural(pass2), pass2 실행라인 `T=../thermal/d3plot jobid=struct`, .done 폴링

## 3. 게이트 (클러스터/사용자 도메인)
- [ ] **GATE-SMOKE**: SIF LS-DYNA 가 thermal solver(SOLN=1, SOLVER=11, 배정밀) 지원하는지 최소 deck smoke. [미확인] — implicit MPI_Comm_dup 결함과 별개로 thermal solve 가능한지 선검증 필수.
- [ ] **GATE-P2**: T2 steady e2e (`/data/koopark/Test_*` NFS) — pass1 온도장 비균일 + pass2 열응력 비0, normal termination.

## 단위계 (SI 입력 → ton-mm-s, resolver 한 곳)
ρ ×1e-12, HC ×1e6, TC ×1, CTE ×1, q'''=power_W·1000/vol_mm3 [mW/mm³], h ×1e-3, T °C.
