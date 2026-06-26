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

## 리스크 (게이트)
- **[미확인] SIF thermal solver 지원.** SOLN=1+SOLVER=11 이 실제 도는지 최소 deck smoke 선검증 필요(클러스터/사용자). 안 되면 P2 전체 무의미 → 이게 1순위 게이트.
- e2e(T2 steady)는 `/data/koopark/Test_*` NFS 에서만 (compute node 가시성). `/tmp` 금지.

## 빌드
- 카드/리졸버는 KooMeshModifier 컴파일 필요. Runner 변경은 KooChainRun 컴파일. → `build_without_automatedmodeller.sh`. 래핑은 serviceApptainers. [[build_flow]]
