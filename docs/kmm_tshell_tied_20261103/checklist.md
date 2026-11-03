<!-- KMM TSHELL·TIED 보존 체크리스트 -->
# 체크리스트 — KMM TSHELL 단면·TIED 두께 보존 (2026-11-03)

- [x] 조사 — TSHELL 읽기가 값을 버리고 칸이 밀림(KooSection.py), R16 카드 정의, TIED 0.005 출처(3d3f50c)·R16 주의 4 묶기 거리, KooChainRun 은 tied_options 를 그대로 넘김(기본값 없음)
- [x] 사용자 결정 — TSHELL 수정·배포, TIED "고친다 — 덱 값 보존"
- [x] TSHELL 시험(아는 불량 먼저: TRANSFORM·DROP_ATTITUDE, ICOMP=1 각도, _TITLE) → 수정 → 통과 → 커밋 — 864524d. 옛 코드 6 FAIL → 10/10 OK. 키워드 읽기의 ICOMP 글 비교(공백째 "1")도 같이 고침
- [x] TIED 시험(아는 불량 먼저: RobustContact 에서 덱 SST·MST 보존, TiedOptions 로 준 값 반영·로그) → 수정 → help → 통과 → 커밋 — 옛 코드 3 FAIL → 7/7 OK, test_cli_help ALL PASS
- [x] 기존 시험 전부 — 0d9c65b 40/41 rc 0 + shim 30건(suite9). 최종 5625a74 로 다시(suite10)
- [x] 말뭉치 — U(지난 739건 + 재현 5, 645098e↔0d9c65b)·V(실제 덱 88건: 의도한 다름 45·같음 43·예상 밖 0, rc 1 36건은 옛 코드도 같은 기존 결함). V 는 최종 트리로 다시
- [x] 적대 리뷰 U → 🔴 없음, 🟡1(NIP 0 각도)·🟡2(TiedOptions 로그)·⚪7(문서) 고침(aa0e07c·5625a74), 🟡3(TSHELL 파트 접촉 빠짐, 기존)은 사용자 결정으로
- [ ] 굽기 전 확인 — 헤드·compute-node-images sha, /data 마지막 tar 번호, 도는 잡
- [ ] 빌드(캡 scope) — bin 시각 확인
- [ ] 컴파일본 e2e
- [ ] SIF · compute-node-images · tar · Drive · 메일
- [ ] SIF e2e
- [ ] push
- [ ] 헤드 /opt 교체(하드 링크 백업) · 확인
- [ ] H8·H9 보고 세션·KooRemapper 쪽에 알림, 메모리·문서
