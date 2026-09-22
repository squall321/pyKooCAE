# 작업 노트 — 열-낙하 양방향 체인

계속 덧붙여 쓴다. 이어받을 때 여기부터 읽는다.

## 손댈 자리 (조사로 확정)
- `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py`
  - `ThermalLoad`(5266~5322) — 여기에 P1(springback)·P2(dynaintoinitial.txt)를 넣는다
  - 참고 구현: `DropAttitude` 의 springback(2226~2228), dynaintoinitial.txt(3103~3130)
  - `WriteModifiedFile(..., copytoOutputFolder=True)`(78~) 이 `Output/`·`DynamicRelaxation/` 을 만들고 덱을 복사한다
    → THERM Run 폴더에 DynamicRelaxation/ 은 이미 있다. 파일만 없다
- `occProject/Generators/KooCAEManager/KooThermalLoad.py` — UniformChamber(18~95) / ICPower pass1(97~184) / pass2(185~)
- `occProject/Generators/KooCAEManager/KooBoundary.py` — Convection(348)·Temperature(263)·HeatFlux(320)·Radiation(383) **이미 존재**
- `occProject/Generators/KooMeshModifier.py` — THERMAL_LOAD 파서(2505~2626), TempCurve 블록(2549~2562)
- `Runner/CumulativeScenarioRunner.py` — THERM 옵션 직렬화(1681~1772), 2-pass(1324~1441),
  다음 스텝 입력 선택(1490~1514, `Output/*_dti.k` glob), `_find_input_file`(THERM→ThermalSet.k)
- `Runner/CumulativeDesigner.py` — 열 시나리오 분기(209~270, 각도 0 고정), execution 블록(958~968)

## 결정 1 — springback 은 구조 pass 에만
ICPower pass1 은 `*CONTROL_SOLUTION(SOLN=1)` 열해석이라 dynain 이 의미가 없다.
UniformChamber 와 ICPower `Phase=structural` 에만 넣는다. pass1 에 들어가면 불필요한 파일과 혼동이 생긴다.

## 결정 2 — 이월 정책을 옵션으로
열 스텝의 `_dti.k` 가 `*LOAD_THERMAL_VARIABLE` 을 들고 가면 낙하 중에 온도가 다시 스윕된다.
기본은 `stress_only`(열하중 제거, 잔류응력만 이월) — 표준적인 선택이다.
`hold_temperature` 는 커브를 평탄화해 낙하 내내 그 온도를 유지한다(온도 의존 물성이 없으므로 효과는 제한적).

## 열린 질문 (진행하며 답한다)
- DROP→THERM 에서 낙하 카드 제거를 DYNAIN_TO_INITIAL 옵션으로 할지, THERMAL_LOAD 진입 시 할지
- 미해석 키워드 raw 블록 2회 출력이 실제인지 (조사에서 관측됐다는 보고 — 직접 재현 필요)
- 외피 세그먼트 자동 선택을 어디서 할지 (GetExternalBoundary 재사용 가능 여부)

## P1·P2 완료 (2026-09-22)
- P1: `ThermalLoad` 에 전 파트 PartSet + `*INTERFACE_SPRINGBACK_LSDYNA`. 구조 pass 한정
  (`isThermalSolvePass` 로 ICPower pass1 제외). 골든 대비 추가 카드는 그 2종뿐임을 diff 로 확인.
- P2: `DynamicRelaxation/dynaintoinitial.txt` 발행. 합성 dynain 으로 DYNAIN_TO_INITIAL 을 실제로 돌려
  `Output/ThermalSet_dti.k` 에 `*INITIAL_STRESS_SOLID` 가 들어가는 것까지 확인 (러너가 glob 하는 경로와 일치).

## P3a 완료 — 미해석 raw 키워드 이중 출력 (기존 결함, 열 전용 아님)
🔴 조사에서 보고된 "raw 블록 2회 출력" 은 사실이었고 **열 경로만의 문제가 아니었다.**
`KooMeshModifier.WriteModifiedFile` 이 공유 writer(`WriteStreamDynaKeyword`, raw 보존 포함)를 부른 뒤
`self._write_uninterpreted_raw_blocks(f)` 를 또 불렀다. 공유 writer 에 raw 보존이 나중에 추가되면서 생긴 이중 호출이다.
실측: 왕복 1회에 `*DATABASE_NCFORC` 1→2, `*LOAD_THERMAL_VARIABLE` 1→2, `*MAT_ADD_THERMAL_EXPANSION` 2→4.
누적은 스텝마다 왕복하므로 스텝을 거듭하면 배로 늘어난다 — **기존 낙하 체인에도 있던 결함**이다.
- 수정: KMM 쪽 중복 호출 제거(주석으로 사유 남김).
- 보강: `KooRawKeywordDedup.filter_duplicate_raw_blocks` 신설 — 매니저가 같은 **내용**을 이미 썼으면 raw 를 건너뛰고,
  내용이 다르면 보존한다. 공유 writer 와 KooKFileMerger 양쪽에 적용(이름이 아니라 내용 기준이라 유실 위험 없음).
- 회귀: DROP·IMPACT 덱 바이트 동일, 기존 시험 3종 통과, 왕복 후 늘어난 카드 0(시험 [4] 로 고정).

## P3b 완료 — 양방향 이월 정책 (2026-09-22)

### 재임포트 시 카드가 어디로 들어오는지 (실측, 중요)
| 카드 | 재임포트 위치 | interpreted |
|---|---|---|
| `*LOAD_THERMAL_VARIABLE` | **raw 블록만** | False |
| `*MAT_ADD_THERMAL_EXPANSION` | **raw 블록만** | False |
| `*DEFINE_CURVE_TITLE` | defineManager (이름 `ThermLoad_temp_curve`) | True |
| `*INITIAL_VELOCITY` | initialManager.inits | True |
| `*INTERFACE_SPRINGBACK_LSDYNA` | additionalManager.interfaces | True |
🔴 그래서 열하중 제거는 **매니저만 보면 안 되고 raw 딕트도 지워야** 한다. 첫 구현이 이것 때문에 무동작이었다.

### 구현
- `_ApplyThermalCarryPolicy(option, context)` — DropAttitude·DropWeightImpactTest 진입부에서 호출.
  `ThermalCarry` = `stress_only`(기본, 열하중 raw 블록 + 램프 커브 제거) | `hold_temperature`(커브를 마지막 값으로 평탄화).
  CTE 카드는 양쪽 모두 남긴다(온도 하중이 없으면 무해하고, 변경을 최소화).
- `_RemoveCarriedDynamicLoads(option, context)` — ThermalLoad 진입부. `RemoveCarriedVelocity`(기본 True)면
  `KooInitialVelocity*` 를 전부 제거한다(열 스텝은 준정적이라 초기속도가 남으면 모델이 날아간다).
- P1 springback 발행을 **멱등**으로 바꿨다. 이월 덱에는 이미 springback 이 있어 그대로 추가하면 두 장이 됐다(실측 PSID 1·3).
- 러너 배선: `simulation_params.thermal_carry` → DROP/IMPACT 설정의 `ThermalCarry` 줄,
  `simulation_params.thermal.remove_carried_velocity` → THERM 설정의 `RemoveCarriedVelocity` 줄.
  🔴 둘 다 **미지정 시 줄을 넣지 않는다** → 기존 출력 바이트 불변(시험으로 고정).

### 안 한 것과 이유
- 낙하판 파트·접촉 제거는 넣지 않았다. THERMAL_LOAD 가 어느 파트가 바닥판인지 신뢰성 있게 구분할 수 없고
  (제목이 비어 있다), 필요하면 `DYNAIN_TO_INITIAL` 의 기존 옵션 `RemovePartIDList`·`RemoveContactIDList` 로 지정할 수 있다.
  합성 dynain 왕복에서는 바닥판이 이미 빠졌으나 그 동작은 dynain 내용에 의존하므로 실 dynain 으로 재확인이 필요하다(P7 e2e 항목).

## P4 완료 — 환경조건 + 국부 발열 동시 (2026-09-22)

🔴 **조사 결과 정정**: "경계조건 카드 클래스가 이미 있다"는 틀렸다. `KooBoundary.py` 의
`KooBoundaryConvection`·`KooBoundaryTemperature` 는 CAD 형상용이고 **LS-DYNA writer 도 매니저도 없다**
(게다가 `super(KooBoundaryConvection).__init__(...)` 오용으로 부모 초기화가 안 된다 — 죽은 코드).
그래서 카드를 새로 구현했다.

- `KooBoundaryNode.py` — `KooBoundaryConvectionSet`(*BOUNDARY_CONVECTION_SET),
  `KooBoundaryTemperatureSet`(*BOUNDARY_TEMPERATURE_SET) + 매니저 Create API. 기존 SPC 클래스와 같은 패턴.
- `KooThermalLoad.apply_ambient_boundary` — 파트별 외피(`GetExternalBoundary(True)`)로 *SET_SEGMENT(THERMAL) 를 만들고
  대류를 건다. 규정온도 모드는 외피 노드 세트로. UniformChamber·ICPower pass1 양쪽에서 호출(미지정이면 무동작).
- 🔴 **TMULT 는 곱수다**: 커브를 줄 때 `TMULT=1.0`, 커브가 없을 때만 `TMULT=T∞`. 처음에 T∞ 를 그대로 넣어
  `T∞ = -40 × 곡선값` 이 되는 오류를 냈다가 카드를 직접 읽어 잡았다.
- 옵션: `Ambient / mode,convection|temperature / h,… / temp_C,… / pids,… / TempCurve…EndTempCurve / EndAmbient`
- 시나리오: `simulation_params.thermal.ambient` → 러너가 위 블록으로 직렬화(미지정 시 줄 없음 = 출력 불변).

검증: 대류+커브 / 대류 상수 / 규정온도 3경로 모두 덱에 정확히 실림, 발열 카드와 공존,
Ambient 미지정 시 경계조건 0, DROP·IMPACT 덱 바이트 동일.
