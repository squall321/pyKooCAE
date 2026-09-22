# 열-낙하 양방향 체인 구현 체크리스트

계획은 [PLAN.md](PLAN.md). 중단 시 마지막 체크 지점부터 이어간다. 단계마다 커밋한다.

## P0. 준비 — 기준선·시험 하네스
- [x] 골든 기준선 확보 (UniformChamber / ICPower pass1 / ICPower pass2 덱)
- [x] 기존 DROP·IMPACT 덱 골든 확보 (회귀 diff 기준)
- [x] tests/test_thermal_chain.py 작성 — 현재 코드에서 통과(기준선 고정)

## P1. THERM dynain 산출 (B1) ✅
- [x] ThermalLoad 에 전 파트 PartSet + *INTERFACE_SPRINGBACK_LSDYNA (구조 pass 한정)
- [x] ICPower pass1(SOLN=1)에는 안 들어가는 것 확인
- [x] 골든 diff = 추가 카드 2종뿐
- [ ] 시험 갱신·통과

## P2. THERM 이월 입구 (B2)
- [x] DynamicRelaxation/dynaintoinitial.txt 작성 (ThermalSet.k 기준)
- [x] KMM DYNAIN_TO_INITIAL 로 실행 가능한 내용인지 직접 실행 확인
- [ ] 러너 비최종 THERM 스텝이 degraded 없이 _dti.k 생성 (소스 레벨)
- [ ] 시험 갱신·통과

## P3. 이월 정책 — 양방향 (B7 + DROP→THERM)
- [ ] THERM→다음: thermal_carry(stress_only | hold_temperature) 구현
- [ ] DROP→THERM: 낙하 카드(INITIAL_VELOCITY·rigidwall·바닥판) 정리 경로 구현
- [x] 미해석 키워드 raw 블록 2회 출력 여부 확인 → 사실이면 수정
- [ ] 각 방향 _dti.k 카드 불변식 확인 (이전 하중 0, 초기응력 존재)
- [ ] 시험 갱신·통과

## P4. 환경조건 + 국부 발열 동시 (B3·B4)
- [ ] KooBoundary 대류/온도 경계조건을 THERMAL_LOAD 파서·러너에 배선
- [ ] ambient + heat_sources 공존 허용 (thermal_type 배타 해제)
- [ ] 외피 세그먼트 선택 규칙 확인 (개수·중복)
- [ ] 덱에 BOUNDARY_CONVECTION + LOAD_HEAT_GENERATION 공존 확인
- [ ] 시험 갱신·통과

## P5. dwell·사이클 (B5)
- [ ] thermal.temp_curve 직렬화
- [ ] thermal.tFinal 분리 (미지정 시 기존 동작)
- [ ] KMM help TempCurve 종축 설명 정정
- [ ] 시험 갱신·통과

## P6. 조건축 × 각도축 (B6)
- [ ] Designer 분기 수정 — THERM 은 조건, DROP 은 각도
- [ ] THERM-only 시나리오 기존 동작 불변 확인
- [ ] 시험 갱신·통과

## P7. 통합·배포
- [ ] 양방향 시나리오 3종 prepare 검증 (THERM→DROP, DROP→THERM, THERM→DROP→THERM)
- [ ] 기존 스위트 전부 통과 (layer_split·fall_gravity·kooremapper_chain_config·cli_help·kam_fixes)
- [ ] DROP·IMPACT 덱 바이트 동일 회귀
- [ ] 빌드 → SIF → tar → node001 배포
- [ ] node001 에서 실제 LS-DYNA 완주 (양방향)
- [ ] 문서·예제 갱신, 메모리 기록
