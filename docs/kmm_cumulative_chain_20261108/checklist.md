<!-- KMM 누적 체인 결함 묶음 체크리스트 -->
# 체크리스트 — KMM 누적 체인 결함 묶음 (2026-11-08)

- [x] 조사 — C1·C2·C3 원인 자리 확인(코드 읽기), 라이선스 상태 확인(10-16 부터 만료 그대로)
- [x] kooomnidropanalyzer-43 과 파일 겹침 확인(그쪽은 이 파일들 고칠 계획 없음)
- [x] 사용자 결정 — 범위 = 이어서 하는 해석에 닿는 것만, S2 = 멈추고 알림(rc 1), 검증 뒤 배포까지
- [x] 아는 불량 기준 — 고치기 전 소스로 20건 실패(base.log), 고치기 전 트리 gen_f3a49d9(KMM_GEN)
- [x] 새 시험 tests/test_cumulative_chain.py — 새 판정은 모두 고치기 전 판에서 실패 확인
- [x] C1 강체벽 이름표 + DTI *RemoveRigidWallbyID + DROP 바닥 벽 번호(단일·Fast) — 3190bfc
- [x] C2 DWI 장치 전부(partsRigid 포함) + RemovePart 가 가리키는 카드 정리 — 80c306e
- [x] C3 IncludeWallInGeneral 바닥판을 남은·바뀐 접촉 범위에 넣기(못 넣으면 rc 1) + 묶음 번호 정리 — 6f7bb7e·80c306e
- [x] W1 강체벽 기록기(종류·제목·모든 칸·정밀도·기하 벽 BIRTH·DISPLAY·번호 없는 꼴) — 693ec9b
- [x] W2 강체벽 덱 차례(종류가 섞여도) — 693ec9b. 바닥 벽 자리 차이는 재현 안 됨(회귀 시험만)
- [x] W3 DROP 원점 이동 때 덱 사용자 강체벽도 같이 — 20b769d
- [x] S1 OutsideRigid*·byPart 의 *INTERFACE_SPRINGBACK_LSDYNA — 80c306e
- [x] S2 시편을 바꾼 충격(잘라 냄·강체로 바꿈)은 DTI 가 rc 1 — 3190bfc·80c306e(KCR 체인은 시편을 바꾸지 않아 Runner 는 그대로)
- [x] 회귀 — tests/ 60개 모두 통과(HEAD 20b769d·8405cd0, v131_review 는 읽기만 맞춤), 43 의 drop_endtime_table·drop_rigid_spin 통과, e2e_rde b·c ALL PASS(키 없는 DROP 덱 v132 와 바이트 같음). 말뭉치 비교는 하지 않음(아래 노트)
- [~] 적대 리뷰 — 에이전트 A·B 가 주간 한도로 끝나 직접 점검으로 대신(노트). 말뭉치 대조 25덱: 강체벽 없는 15덱 바이트 같음·강체벽 덱은 강체벽 블록만 다름. 한도가 풀리면(11-13) 에이전트 리뷰 다시
- [x] 빌드 v135(소스 653cbea, build_without_automatedmodeller --clean, 23:40~00:35, 최저 가용 34.9 GB) — KMM c18245a2·KCR 35511107
- [x] 컴파일본 시험 — test_cumulative_chain 51/51, test_v131_review 107/107(KMM_BIN, C.UTF-8)
- [x] host e2e(e2e_rde.sh host, 새 KMM·KCR) — ALL PASS 100(v134 와 같은 100)
- [x] SIF v135 da892a35(1,615,933,440 B, KMM c18245a2·KCR 35511107 확인)·compute-node-images 같음·tar v135 1,379,306,561 B·Drive·메일(BAKE_RC 0)
- [x] SIF 판정 — SIF 안 KMM 으로 체인 51/51, e2e_rde sif ALL PASS 100
- [x] 헤드 /opt Pre = v135 da892a35(01:13), v134 34c00cad 는 SmartTwinPreprocessor_backup_20261109_011338.sif(하드 링크·옛 inode), 새 헤드는 임시 사본 rename
- [x] 알림(kooomnidropanalyzer-43)·메모리·문서 push
- [ ] 노드(node001·002) — VM 이 꺼져 있다. 켤 때 사용자 확인 뒤 Pre v135·Post v51 을 deploy_apptainers.sh 로
- [ ] 에이전트 적대 리뷰 다시(주간 한도가 풀린 뒤, 11-13 15시 UTC)
