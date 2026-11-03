<!-- KMM 기존 결함 묶음(v130) 체크리스트 -->
# 체크리스트 — KMM 기존 결함 묶음 (2026-11-03, v130)

- [x] 조사 — 결함마다 원인 자리 확인(B1 DatabaseExtentIntfor.parse, B2 get_nodes→None 건너뜀, B3 `*` 빠진 비교·함수 이름, B4 *SET_SEGMENT_GENERAL, B5 KooRemapper ModelAssembler 82자 줄, B6 SectionShell 카드 2, C1 SHELL ICOMP 각도 소실 실측, C2 KooDynaFloat, C4 AddSectionfromDyna None, C5 블록 형식 미전달)
- [x] 사용자 결정 — 범위 "이번 보고분 전부", 검증 뒤 v130 배포까지
- [ ] B1 DATABASE_EXTENT_INTFOR 카드 2 선택 — 시험(아는 불량 먼저) → 고침 → 커밋
- [ ] B3 ERODING_SURFACE_TO_SURFACE_ID — 시험 → 고침 → 커밋
- [ ] B4 LOAD_SEGMENT_SET → 해석 안 하는 세트 — 시험 → 고침 → 커밋
- [ ] B6 SECTION_SHELL 카드 2 없음 — 시험 → 고침 → 커밋
- [ ] C2 KooDynaFloat Fortran 꼴 + B5 원인 짚는 오류 — 시험 → 고침 → 커밋, KooRemapper 쪽 알림
- [ ] C1·C3·C5 단면 카드 묶음(여러 단면·SHELL ICOMP 각도·ICOMP 판정·long·콤마) — 시험 → 고침 → 커밋
- [ ] C4 PART_EXCHANGE TSHELL·SOLID_PERI — 시험 → 고침 → 커밋
- [ ] B2 정의 안 된 절점 요소 → 읽기 소실 장부 — 시험 → 고침 → 커밋
- [ ] A *ELEMENT_TSHELL → TSHELL8 — 솔리드 전용 경로 점검 → 시험(리뷰 U 탐침: SINGLE_SURFACE 파트 수·RobustContact 면·Tied 감지) → 고침 → 커밋
- [ ] help·문서
- [ ] 기존 시험 전부
- [ ] 말뭉치 U(옛 5625a74) · V(실제 덱) — 바뀐 것은 의도한 것뿐
- [ ] 적대 리뷰 → 고침
- [ ] 굽기 전 확인(헤드·compute-node-images sha, 마지막 tar, 잡)
- [ ] 빌드(캡 scope) — bin 시각
- [ ] 컴파일본 e2e(아는 불량 먼저: 헤드 v129)
- [ ] SIF v130 · compute-node-images · tar · Drive · 메일
- [ ] SIF e2e
- [ ] push
- [ ] 헤드 /opt 교체(하드 링크 백업) · 확인
- [ ] 알림(kooremapper-fd: B5 출력기·v130), 메모리·문서
