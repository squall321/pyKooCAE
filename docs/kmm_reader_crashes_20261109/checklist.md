<!-- KMM 리더 크래시 묶음 체크리스트 -->
# 체크리스트 — KMM 리더 크래시 묶음 (2026-11-09)

- [x] 사용자 결정 — 찾은 결함 셋 고치기(배포는 그때 다시 묻는다)
- [x] 조사 — R1·R2·R3 자리, R4(RBDOUT 조건) 발견
- [x] 시험 tests/test_reader_crashes_20261109.py — 고치기 전 트리(gen_a1c4ec6)에서 8건 실패(_ID 짧은 접촉은 예전부터 멈춰 일관성 확인용)
- [x] R1 *INITIAL_VELOCITY 빈 NSIDEX(_whole_int, 카드 3 은 있을 때만)
- [x] R2 *DATABASE_* — 함수 안 float 3·int 44 를 KooDynaFloat·KooDynaInt 로
- [x] R3 *LOAD_SEGMENT_SET(_ID) 빈 SF·AT(기본값 1.0·0.0)
- [x] R4 *DATABASE_RBDOUT 이 출력에서 조용히 빠지던 것(조건의 '*' 누락) 확인·고침
- [x] R5 카드 2·3 을 생략한 짧은 접촉(ref.k 다음 크래시) — 빈 카드로 채우지 않고 R16 필수 카드 규칙(_contact_cards 와 같은 뜻)으로 원인을 밝혀 멈춤
- [x] 회귀 tests/ 61개 모두 rc 0 · 말뭉치 대조(a1c4ec6 ↔ 지금): taylor_A 계열 4덱 rc 1 → 0, ref·out 은 필수 카드로 멈춤(rc 1), 배터리 덱 3개는 빠지던 *DATABASE_RBDOUT 이 돌아온 2줄만 다름, 나머지 같음
- [x] 배포 여부를 사용자에게 물음 — 11-11 「배포」
- [x] 커밋 51a2160·102d945·cc37c43·2de828a(고침)·fc0c6a0(시험)·2915d1c(문서), push
- [x] (v135 때 빠뜨린 것) KMM --help DTI 에 *RemoveRigidWallbyID·*SpecimenModified·RemovePart 가 함께 지우는 카드 — test_cli_help ALL PASS, v135 이전 파서(gen_f3a49d9)로는 새 두 항목 FAIL
- [x] 빌드 v136(4d8eb00, 16:43~17:39) — KMM 41f37642, KCR 35511107·KAM 580f028e 그대로
- [x] 컴파일본 시험 9/51/107 · 호스트 e2e ALL PASS 100
- [x] SIF v136 1c973c25 = compute-node-images, tar v136·Drive·메일 · SIF 판정 9/51/107·e2e ALL PASS 100
- [x] 헤드 /opt = v136(18:25), v135 da892a35 는 SmartTwinPreprocessor_backup_20261111_182504.sif(하드 링크) · 헤드 SIF 로 리더 크래시 9/9·--help DTI 새 항목 확인
- [x] 알림(kooomnidropanalyzer-43·kooremapper-fd·4a)·메모리
- [ ] 노드(node001·002) — VM 꺼짐. 켤 때 사용자 확인 뒤 Pre v136·Post v51 을 deploy_apptainers.sh 로
