<!-- 강체 낙하 사전 해석 → 각도별 종료 시간(RIGID_DROP_ENDTIME, v132) 체크리스트 -->
# 체크리스트 — 강체 낙하 사전 해석 → 각도별 종료 시간 (2026-11-07, v132)

- [x] 사용자 결정 — KMM 새 모드 + KCR 자동 연결, RIGID_DROP_ENDTIME 계열 이름, 사전 해석 중력 켬(리포트처럼), SIF v132·tar·Drive/메일까지(헤드 /opt 는 따로)
- [x] 조사 — KMM 리더·모드 등록 4곳·부분 문자열 함정, KCR tFinal 흐름(누적·대규모·배치), 빌드·SIF 패턴, 이전 세션 규칙, 시험 덱·기준값
- [x] 계획·체크리스트·결정 노트
- [x] 계약 파일 `KooEndTimeTable.py`(표 쓰기·읽기·각도 찾기·낙하 방향 규약) + 시험 `tests/test_end_time_table.py` 22/22
- [ ] A 질량특성 `KooRigidBodyProperties.py` — MinimumModel d3hsp·SimpleDrop·DropSet 바닥 제외·장난감 덱
- [ ] B 사전 해석 `KooRigidDropPresim.py` — 상자 껍질 vs GEOM_BOX, e·dt 검증, 45° 17 ms, 6면, 중력 분류 위험 측정
- [ ] C KMM 표 소비 — DROP_ATTITUDE `EndTimeTable`(단일·Fast DOE), 키 없을 때 바이트 동일
- [ ] D KCR 연결 — `simulation_params.endtime_presim`, prepare 실행, 누적·대규모·배치 세 경로, 옵션 없을 때 바이트 동일, cli_help_kcr
- [ ] E KMM 모드 연결 — `RIGID_DROP_ENDTIME` 등록·카탈로그·통합 시험(MinimumModel)
- [ ] 적대 리뷰 — 물리·KMM 회귀·KCR, 고친 것마다 회귀 시험
- [ ] 전체 시험 묶음(tests/*.py) 통과
- [ ] 빌드 — build_without_automatedmodeller.sh --clean (캡 scope), pybullet dist 포함, "호스트 배포 완료", bin mtime
- [ ] 컴파일본 e2e `/data/koopark/Test_E2E_v132` — v131 아는 불량 먼저
- [ ] SIF v132 — 굽기 전 sha·tar 번호 확인, kooremapper-fd 알림, 굽기, SIF e2e, Drive·메일
- [ ] 커밋·푸시(pathspec)
- [ ] 알림 — smarttwinmcp(새 kmm 모드·키·scenario 키), kooremapper-fd(굽기 뒤)
- [ ] 메모리·문서(context-notes 결론, project 메모리, node_sif_deploy v132)
- [ ] 헤드 /opt 교체·노드 배포 — 사용자에게 묻기
