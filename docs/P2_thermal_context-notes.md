<!-- P2 구현 중 내린 결정·근거·함정 (이어받기용) -->
# P2 Context Notes

## 결정
- **2-pass 채택** (계획대로). 연성 SOLN=2 단일런은 더 단순하나, SIF LS-DYNA가 implicit MPI_Comm_dup 결함이 있어(계획 §0) explicit 구조 + 별도 thermal solve 가 안전. pass1 thermal(SOLN=1) → 온도 d3plot → pass2 구조(SOLN=0) + LOAD_THERMAL_D3PLOT.
- **ThermalSource.py 안 만듦.** 계획은 registry 모듈을 가정했으나 T1 이 CumulativeScenarioRunner `_therm_get` 인라인으로 갔음. 그 결을 따라 ICPower도 인라인 확장(새 모듈 X, 일관성).
- **카드 emit 패턴.** CONTROL=KooDynaControl.py `KooControl*` 클래스(GenerateDynaKeyword/WriteStreamDynaKeyword) + 매니저 멤버/Set/write루프(1310). MAT/LOAD/SET/INITIAL=각 매니저 Create* (T1 결: apply_thermal_load 가 defineMan/loadMan/matMan.Create* 호출).

## 함정 (코드/매뉴얼)
- **CONTROL_THERMAL_SOLVER Card1 31-40 blank.** ATYPE/PTYPE/SOLVER 다음 31-40 은 빈 10칸이어야 GPT가 41-50에 떨어짐. emit 시 빈 필드를 `" "*10`(또는 "" format)로 명시.
- **배정밀 필수.** thermal solve 는 단정밀 거부 → 배정밀 SIF. pass1 d3plot 배정밀.
- **pass1/pass2 d3plot rootname 충돌 금지** → 실행라인 `jobid=` 분리, pass2 는 `T=../thermal/d3plot`.
- **단위 환산은 resolver 한 곳에서만** (zero-hardcode). SI→ton-mm-s.

## 게이트 — ✅ 해소됨 (계획 §0, 2026-06-14 smoke)
- **SIF thermal solver 확정**: `/data/koopark/Test_ThermalSmoke/thermal_smoke.k` (단일 hex) 가 compute 노드에서
  CONTROL_THERMAL_SOLVER/TIMESTEP + MAT_THERMAL_ISOTROPIC + INITIAL_TEMPERATURE_SET(NSID=0) +
  LOAD_HEAT_GENERATION_SET_SOLID 전부 인식 + normal termination + 온도 d3plot. (내가 §0 안 읽고 리스크로 오판했음.)
- 🔴 **배정밀 SIF 필수**: thermal 은 `LSDynaBasic_aocc420_ompi4.0.5_mpp_d.sif`. 단정밀(_s.sif)은
  `Error 40343` 로 thermal 거부. → thermal scenario `environment.lsdyna_apptainer_sif` = `_mpp_d.sif`. (Unit E 에서 반영)
- **검증 deck = transient(ATYPE=1), heat sink 없음**. 단일 hex 가 시간따라 가열될 뿐 → convection/고정온도 불필요.
  → **Unit C(convection) 보류**. T2/T3 첫 cut 은 transient 가열로 가면 A·B + 기존 빌딩블록으로 충분.
- thermal_smoke.k 카드순: CONTROL_SOLUTION(1) → THERMAL_SOLVER(atype=1,gpt8) → THERMAL_TIMESTEP →
  TERMINATION → PART → SECTION_SOLID → MAT_ELASTIC(MID) → MAT_THERMAL_ISOTROPIC(TMID) →
  INITIAL_TEMPERATURE_SET(0,25) → SET_SOLID(100) → LOAD_HEAT_GENERATION_SET_SOLID(sid100,mult30) → D3PLOT.
  내 A 카드 emit 이 smoke 와 컬럼 일치 확인됨.
- e2e 는 `/data/koopark/Test_*` NFS 에서만(compute node 가시성). `/tmp` 금지.

## 미해결 (D 착수 전 1개)
- `*SET_SOLID` emit 경로: SolidSet(KooElement) vs SolidElementSet(KooElementSet) 두 클래스 — 어느 게 emit/write 되는지 확인 필요.

## 빌드
- 카드/리졸버는 KooMeshModifier 컴파일 필요. Runner 변경은 KooChainRun 컴파일. → `build_without_automatedmodeller.sh`. 래핑은 serviceApptainers. [[build_flow]]
