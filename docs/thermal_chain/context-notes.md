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
