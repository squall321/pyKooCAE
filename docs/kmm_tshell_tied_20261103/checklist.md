<!-- KMM TSHELL·TIED 보존 체크리스트 -->
# 체크리스트 — KMM TSHELL 단면·TIED 두께 보존 (2026-11-03)

- [x] 조사 — TSHELL 읽기가 값을 버리고 칸이 밀림(KooSection.py), R16 카드 정의, TIED 0.005 출처(3d3f50c)·R16 주의 4 묶기 거리, KooChainRun 은 tied_options 를 그대로 넘김(기본값 없음)
- [x] 사용자 결정 — TSHELL 수정·배포, TIED "고친다 — 덱 값 보존"
- [ ] TSHELL 시험(아는 불량 먼저: TRANSFORM·DROP_ATTITUDE, ICOMP=1 각도, _TITLE) → 수정 → 통과 → 커밋
- [ ] TIED 시험(아는 불량 먼저: RobustContact 에서 덱 SST·MST 보존, TiedOptions 로 준 값 반영·로그) → 수정 → help → 통과 → 커밋
- [ ] 기존 시험 전부
- [ ] 말뭉치(지난 말뭉치 + TSHELL·TIED 덱) — 바뀐 것은 의도한 것뿐
- [ ] 적대 리뷰 → 고침
- [ ] 굽기 전 확인 — 헤드·compute-node-images sha, /data 마지막 tar 번호, 도는 잡
- [ ] 빌드(캡 scope) — bin 시각 확인
- [ ] 컴파일본 e2e
- [ ] SIF · compute-node-images · tar · Drive · 메일
- [ ] SIF e2e
- [ ] push
- [ ] 헤드 /opt 교체(하드 링크 백업) · 확인
- [ ] H8·H9 보고 세션·KooRemapper 쪽에 알림, 메모리·문서
