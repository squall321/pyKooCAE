<!-- 강체 낙하 사전 해석 → 각도별 종료 시간(RIGID_DROP_ENDTIME, v132) 체크리스트 -->
# 체크리스트 — 강체 낙하 사전 해석 → 각도별 종료 시간 (2026-11-07, v132)

- [x] 사용자 결정 — KMM 새 모드 + KCR 자동 연결, RIGID_DROP_ENDTIME 계열 이름, 사전 해석 중력 켬(리포트처럼), SIF v132·tar·Drive/메일까지(헤드 /opt 는 따로)
- [x] 조사 — KMM 리더·모드 등록 4곳·부분 문자열 함정, KCR tFinal 흐름(누적·대규모·배치), 빌드·SIF 패턴, 이전 세션 규칙, 시험 덱·기준값
- [x] 계획·체크리스트·결정 노트
- [x] 계약 파일 `KooEndTimeTable.py`(표 쓰기·읽기·각도 찾기·낙하 방향 규약) + 시험 `tests/test_end_time_table.py` 22/22
- [x] A 질량특성 `KooRigidBodyProperties.py` — MinimumModel d3hsp 총질량 4e-8 안, SimpleDrop·DropSet 바닥 제외, 시험 122 (4ce5fd8)
- [x] B 사전 해석 `KooRigidDropPresim.py` — 프로토타입 분류 100%, 껍질 여유 0, 속도 상한 해제, 45° 17.44 ms, 충돌 직전 상태·재시작, 2만×3 4.8분, 시험 52 (fdecb6d)
- [x] C KMM 표 소비 — DROP_ATTITUDE `EndTimeTable`(단일·Fast DOE), 키 없을 때 10사례 바이트 동일, 시험 45 (b58e359)
- [x] D KCR 연결 — `simulation_params.endtime_presim`, 누적·대규모·배치, 옵션 없을 때 1128 파일 바이트 동일, 시험 75 (9980e10)
- [x] 사용자 결정(2단계) — 연계 전체를 이번 판에, RigidAngularVelocity 계열 이름, 심각도 절반+고르게 절반, 2만 방향·대표 100, 각도별 위험 표까지(구면 지도는 Post 요청), 종료 시간은 중력 끔·충격 조건은 중력 켬
- [x] 중력 끔 기본값 반영 — PresimGravity 0, endtime_presim.gravity false, 끄면 재접촉을 모두 2차 충격으로 셈
- [x] E KMM 모드 연결 — `RIGID_DROP_ENDTIME` 등록·카탈로그·`<base>_impacts.csv`·통합 시험 70(MinimumModel, KMM→KMM) (c8c4947)
- [x] 사전 해석 무진행 감시(작업자 멈춤 600 초) (31bc924)
- [x] F KMM 강체 회전 — `RigidAngularVelocityX/Y/Z` → *INITIAL_VELOCITY_GENERATION(STYP 3·IVATN 1·무게중심), Fast DOE, 표 time_unit 확인, 시험 95 (9d04533)
- [x] 사용자 결정 — 심각도 지표 J × vn/v0 (1차 충격은 모두 vn = v0 라 vn 으로는 못 가름)
- [ ] G KCR 충격 조건 — `angle_source impact_conditions`(고르기·DOE·index.json), `harvest --impact-map` → per_angle_risk.csv
- [ ] H Post 계약서 — 구면 보고서가 per_angle_risk.csv·index.json 을 그리도록 KooD3plotReader 세션에 요청
- [ ] 적대 리뷰 — 물리·KMM 회귀·KCR, 고친 것마다 회귀 시험
- [ ] 전체 시험 묶음(tests/*.py) 통과
- [ ] 빌드 — build_without_automatedmodeller.sh --clean (캡 scope), pybullet dist 포함, "호스트 배포 완료", bin mtime
- [ ] 컴파일본 e2e `/data/koopark/Test_E2E_v132` — v131 아는 불량 먼저
- [ ] SIF v132 — 굽기 전 sha·tar 번호 확인, kooremapper-fd 알림, 굽기, SIF e2e, Drive·메일
- [ ] 커밋·푸시(pathspec)
- [ ] 알림 — smarttwinmcp(새 kmm 모드·키·scenario 키), kooremapper-fd(굽기 뒤)
- [ ] 메모리·문서(context-notes 결론, project 메모리, node_sif_deploy v132)
- [ ] 헤드 /opt 교체·노드 배포 — 사용자에게 묻기
