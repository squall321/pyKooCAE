<!-- KMM TSHELL·TIED 보존 체크리스트 -->
# 체크리스트 — KMM TSHELL 단면·TIED 두께 보존 (2026-11-03)

- [x] 조사 — TSHELL 읽기가 값을 버리고 칸이 밀림(KooSection.py), R16 카드 정의, TIED 0.005 출처(3d3f50c)·R16 주의 4 묶기 거리, KooChainRun 은 tied_options 를 그대로 넘김(기본값 없음)
- [x] 사용자 결정 — TSHELL 수정·배포, TIED "고친다 — 덱 값 보존"
- [x] TSHELL 시험(아는 불량 먼저: TRANSFORM·DROP_ATTITUDE, ICOMP=1 각도, _TITLE) → 수정 → 통과 → 커밋 — 864524d. 옛 코드 6 FAIL → 10/10 OK. 키워드 읽기의 ICOMP 글 비교(공백째 "1")도 같이 고침
- [x] TIED 시험(아는 불량 먼저: RobustContact 에서 덱 SST·MST 보존, TiedOptions 로 준 값 반영·로그) → 수정 → help → 통과 → 커밋 — 옛 코드 3 FAIL → 7/7 OK, test_cli_help ALL PASS
- [x] 기존 시험 전부 — 0d9c65b 40/41 rc 0 + shim 30건(suite9). 최종 5625a74 도 41/41(suite10) + shim 30건
- [x] 말뭉치 — U(지난 739건 + 재현 5, 645098e↔0d9c65b)·V(실제 덱 88건: 의도한 다름 45·같음 43·예상 밖 0, rc 1 36건은 옛 코드도 같은 기존 결함). V 는 최종 트리로 다시
- [x] 적대 리뷰 U → 🔴 없음, 🟡1(NIP 0 각도)·🟡2(TiedOptions 로그)·⚪7(문서) 고침(aa0e07c·5625a74), 🟡3(TSHELL 파트 접촉 빠짐, 기존)은 사용자 결정으로
- [x] 굽기 전 확인 — 헤드 = compute-node-images = v127(4d31651f), 마지막 tar v128 → 다음 v129, 잡 0, 노드 down(VM 꺼짐), KooRemapper 스테이징 8c7c4f87 그대로
- [x] 빌드(캡 scope, build_without_automatedmodeller --clean, 소스 dc6490d) — 13:55~14:48 rc 0, 최저 여유 26.6 GB. KMM 36ab6c8e(14:39) NFS == SIF 소스 트리, KAM 580f028e 그대로, KCR 6b19f55d 는 v127 과 바이트 같음(같은 소스)
- [x] 컴파일본 e2e(Test_E2E_v129/e2e_v129_host.log) — 아는 불량 먼저: 헤드 v127 컴파일본 TSHELL 6·TIED 3 FAIL. 새 컴파일본 10절점·파일끝 8종 ALL PASS, KMM 시험 14종 0 FAIL(TSHELL 13·TIED 12·요소 소실 50·레시피 39 …), KCR 결과 귀환·sphere ALL PASS, LANG=C 에서 TIED 12/12(⚠ 경고 줄 포함)
- [x] SIF · compute-node-images · tar · Drive · 메일 — SIF v129 sha 79275a4f(14:57), compute-node-images 같음, KooRemapper 8c7c4f87(기대=실제), tar v129 1,346,109,707 B(14:59), Drive·메일 완료
- [x] SIF e2e(Test_E2E_v129/e2e_v129_sif.log) — SIF 안 KMM 36ab6c8e·KAM 580f028e·KCR 6b19f55d == 소스 트리, 10절점·파일끝 ALL PASS, KMM 시험 14종 0 FAIL, KAM 곡선 식 ALL OK
- [ ] push
- [ ] 헤드 /opt 교체(하드 링크 백업) · 확인
- [ ] H8·H9 보고 세션·KooRemapper 쪽에 알림, 메모리·문서
