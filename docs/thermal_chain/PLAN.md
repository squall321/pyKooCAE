# 열-낙하 양방향 체인 구현 계획 (2026-09-22)

## 목표

`THERM → DROP` 과 `DROP → THERM` 이 **둘 다** 자동으로 누적되어야 한다.
열하중은 **환경조건(챔버 온도)과 국부 발열(IC)을 함께** 걸 수 있어야 한다.

조사 근거는 [../thermal_shock_drop/REQUIREMENTS.md](../thermal_shock_drop/REQUIREMENTS.md) (25 에이전트 교차조사 + 반박 검증).

## 현재 상태 한 줄 요약

낙하 쪽 이월 배관(dynain → DYNAIN_TO_INITIAL → `*INITIAL_STRESS_SOLID`)은 완성돼 있고,
열 쪽은 그 배관의 **입구 두 개(dynain 요청 카드, dynaintoinitial.txt)를 만들지 않는다.**
그래서 열 스텝은 체인에 끼우는 순간 끊긴다. 환경조건·국부발열은 각각은 되지만 동시에는 안 된다.

## 단계

각 단계는 **검증 기준**을 통과해야 다음으로 넘어간다. 단계마다 커밋한다.

### P0. 준비 — 기준선과 시험 하네스
THERM 회귀시험이 0건이라 "빠지는 것 0"을 증명할 수단이 없다. 먼저 만든다.
- 골든 기준선: 현재 배포본으로 UniformChamber·ICPower(pass1/pass2) 덱을 떠서 보관
- 시험: `tests/test_thermal_chain.py` — 덱 카드 단위 단언 (LS-DYNA 불필요, KMM 소스 실행)
- 검증: 시험이 **현재 코드에서 통과**(기준선 고정) → 이후 변경의 diff 를 이 시험으로 잡는다

### P1. THERM 스텝이 dynain 을 남기게 (B1)
`ThermalLoad` 에 전 파트 PartSet + `*INTERFACE_SPRINGBACK_LSDYNA` 발행.
🔴 **구조 pass 에만** 넣는다 — ICPower pass1 은 SOLN=1 열해석이라 dynain 이 무의미하다.
- 대상: UniformChamber, ICPower `Phase=structural`
- 제외: ICPower `Phase=thermal`(pass1)
- 검증: 생성 덱에 `*SET_PART_LIST` + `*INTERFACE_SPRINGBACK_LSDYNA` 각 1개, pass1 에는 0개.
  기존 카드 수·내용 불변(골든 diff 는 이 두 카드 추가분만)

### P2. THERM 스텝이 이월 입구를 남기게 (B2)
`ThermalLoad` runDirectoryMode 분기에 `DynamicRelaxation/dynaintoinitial.txt` 작성
(DropAttitude:3103-3118 과 같은 형식, `*Inputfile` 은 `ThermalSet.k`).
- 검증: THERM Run 폴더에 파일 생성, 내용이 KMM DYNAIN_TO_INITIAL 로 실행 가능,
  러너의 비최종 THERM 스텝이 degraded 없이 `_dti.k` 를 만든다

### P3. 이월 정책 — 양방향 오염 제거 (B7 + DROP→THERM)
이월 덱이 이전 스텝의 하중을 끌고 가면 다음 스텝이 오염된다. 두 방향 모두 정리한다.
- **THERM → 다음**: `_dti.k` 에 남는 `*LOAD_THERMAL_VARIABLE` + 램프 커브 처리.
  옵션 `thermal_carry`: `stress_only`(기본, 열하중 제거) | `hold_temperature`(커브를 평탄화해 온도 유지)
- **DROP → THERM**: `_dti.k` 에 남는 낙하 카드(`*INITIAL_VELOCITY`, rigidwall, 바닥판 접촉) 처리.
  열 스텝 진입 시 제거 또는 DYNAIN_TO_INITIAL 옵션으로 제거
- 미해석 키워드 raw 블록이 **두 번** 출력되는 현상 확인 → 사실이면 별건으로 수정
- 검증: 각 방향 `_dti.k` 에서 이전 스텝 하중 카드 0개, 초기응력 카드 존재, 카드 총수 불변식

### P4. 환경조건 + 국부 발열 동시 (B3·B4)
카드 클래스는 이미 있다 — `KooCAEManager/KooBoundary.py` 의 `KooBoundaryConvection`(348),
`KooBoundaryTemperature`(263), `KooBoundaryHeatFlux`(320), `KooBoundaryRadiation`(383).
THERMAL_LOAD 파서·러너에서 여기로 가는 길만 뚫는다.
- 옵션: `ambient: {mode: convection|temperature, h, temp_C | temp_curve, segments: auto|pids}`
- `heat_sources` 와 `ambient` 를 함께 허용 (지금은 thermal_type 이 배타)
- 이게 들어가면 열충격 표면 구배와 ICPower steady 도 함께 열린다
- 검증: 덱에 `*BOUNDARY_CONVECTION_SET`(+ T∞ 커브) 와 `*LOAD_HEAT_GENERATION` 공존,
  외피 세그먼트만 선택됐는지 개수 확인

### P5. dwell·사이클 프로파일 (B5)
- `thermal.temp_curve: [[t, factor], …]` 를 러너가 직렬화 (KMM 파서는 이미 지원)
- `ENDTIM` 을 `ramp_time_s` 에서 분리 — `thermal.tFinal` 신설(미지정 시 기존 동작 유지)
- KMM help 의 TempCurve 종축 설명(절대온도 → factor) 정정
- 검증: 램프+유지 2구간 커브가 덱에 그대로, ENDTIM 이 tFinal

### P6. 열 조건축 × 낙하 각도축 (B6)
`CumulativeDesigner._process_thermal_scenario` 가 `angle_source` 를 버리는 것을 고쳐,
THERM 스텝은 `thermal_conditions`, DROP 스텝은 `angle_source` 를 쓰게 한다.
- 검증: 혼합 시퀀스에서 DROP 스텝 각도가 0/0/0 이 아님, THERM-only 시나리오는 기존과 동일

### P7. 통합
- 양방향 시나리오 e2e (THERM→DROP, DROP→THERM, THERM→DROP→THERM)
- 빌드 → SIF → tar → node001 → 실제 LS-DYNA 완주
- 문서·예제 갱신

## 회귀 방어 (모든 단계 공통)

- 기존 DROP/IMPACT/VIBRATION 덱은 **바이트 동일**해야 한다 (`work/thermal_chain/reg/` 골든).
- 기존 THERM 덱은 P1·P2 가 더하는 카드 외에는 동일해야 한다.
- 각 단계마다 `tests/test_thermal_chain.py` + 기존 스위트(`test_layer_split`, `test_fall_gravity`,
  `test_kooremapper_chain_config`, `test_cli_help`) 전부 통과.
- 🔴 공유 코드(`KooDynaAdvancedModification`, `CumulativeScenarioRunner`)를 건드리므로
  [[protect_existing]] 원칙 — "빠지는 것 0" 을 diff 로 증명하기 전에는 다음 단계로 안 간다.

## 범위 밖 (이번에 안 함)
- 온도 의존 물성(온도별 E·항복) — 별건, 규모가 다르다
- 크립·응력완화 모델
- ICPower steady(ATYPE=0) 자체 — P4 의 경계조건이 들어가면 가능해지지만 검증은 별도
