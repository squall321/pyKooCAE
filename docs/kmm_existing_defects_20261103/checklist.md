<!-- KMM 기존 결함 묶음(v130) 체크리스트 -->
# 체크리스트 — KMM 기존 결함 묶음 (2026-11-03, v130)

- [x] 조사 — 결함마다 원인 자리 확인(B1 DatabaseExtentIntfor.parse, B2 get_nodes→None 건너뜀, B3 `*` 빠진 비교·함수 이름, B4 *SET_SEGMENT_GENERAL, B5 KooRemapper ModelAssembler 82자 줄, B6 SectionShell 카드 2, C1 SHELL ICOMP 각도 소실 실측, C2 KooDynaFloat, C4 AddSectionfromDyna None, C5 블록 형식 미전달)
- [x] 사용자 결정 — 범위 "이번 보고분 전부", 검증 뒤 v130 배포까지
- [x] B1 DATABASE_EXTENT_INTFOR 카드 2 선택 — 3e96db7
- [x] B3 ERODING_SURFACE_TO_SURFACE_ID — fadbb3f
- [x] B4 LOAD_SEGMENT_SET → 해석 안 하는 세트 — f085731
- [x] B6 SECTION_SHELL 카드 2 없음 — 53bc855(단면 카드 묶음과 함께)
- [x] C2 KooDynaFloat Fortran 꼴 + B5 원인 짚는 오류 — d7dbf28, KooRemapper 쪽(kooremapper-fd)에 ModelAssembler 82자 줄 수정 요청
- [x] C1·C3·C5 단면 카드 묶음(여러 단면·SHELL ICOMP 각도·사용자 요소 카드·ICOMP 판정·long·콤마) — 53bc855
- [x] C4 PART_EXCHANGE — 모든 단면 형식에서 SECID 미동기(새로 찾음) + TSHELL·SOLID_PERI None — e27a183(옛 14 FAIL → 17/17)
- [x] B2 정의 안 된 절점 요소 → 읽기 소실 장부 — 86adf0b
- [x] A *ELEMENT_TSHELL → TSHELL8 — 1b515b6(옛 7 FAIL → 11/11, 리뷰 탐침 GEN_tshell SINGLE_SURFACE 1→2 parts·RC_tshell 외부 면 6→16)
- [x] D(새로 찾음) 원문 통과 블록 '%'·'+' 표시 — 8ae3318(test_kmm_real_deck_crashes 29/29)
- [x] help·문서 — `--help` 에 이번 변경으로 틀려진 문구가 없다(종료 코드 3 '요소가 빠졌다' 는 읽기 소실에도 맞다). 기록은 context-notes
- [x] 기존 시험 전부 — 최종 트리 694494c 에서 44개 통과(test_drop_attitude_angles 는 pytest 없어 shim 30건). fcae54f·97aaff9 도 통과
- [x] 말뭉치 U(옛 5625a74) · V(실제 덱) — 바뀐 것은 의도한 것뿐. 최종 트리 694494c: W5 같음 733·다름 14(W + L_P7_long), V6 은 V5 와 바이트까지 같음
- [x] 적대 리뷰 → 고침 — W(🔴 2·🟡 6, 76b14ff~dac9b98)·X(🔴 1·🟡 2·⚪ 3, 1227bac·11d208e·97aaff9)·Y(🟡 3·⚪ 2, c22d68d·c70259e·fcae54f)·Z(🟡 1·참고 1, 694494c) 고침
- [x] 굽기 전 확인(헤드·compute-node-images sha, 마지막 tar, 잡) — v129 79275a4f·tar v129·잡 없음
- [x] 빌드(캡 scope) — bin 시각: KMM 0a832f04(22:03)·KCR 74a62ce8(22:12, 상수 순서만 다름)·KAM 그대로
- [x] 컴파일본 e2e(아는 불량 먼저: 헤드 v129) — 헤드 v129 는 최종 시험에서 크래시 21·단면 26·TSHELL 13 FAIL, v130 컴파일본은 KMM 시험 17종·10절점 8종·KCR 결과 귀환·sphere 모두 통과
- [x] SIF v130 · compute-node-images · tar · Drive · 메일 — SIF 9d166fd0(22:28)·tar v130 1,346,209,884 B·KooRemapper b9d4c12d 스테이징·메일 sent OK
- [x] SIF e2e — SIF 안 바이너리 = 소스 트리, KooRemapper b9d4c12d test_card_80col 18/18, 10절점 8/8, KMM 시험 17종·KAM 곡선 식 통과
- [x] push — b72807f..52fbded
- [x] 헤드 /opt 교체(하드 링크 백업) · 확인 — v130 9d166fd0(22:51), v129 백업 SmartTwinPreprocessor_backup_20261103_225131.sif, 껍데기 시험 통과. 노드는 down 이라 미배포
- [x] 알림(kooremapper-fd: B5 출력기·v130), 메모리·문서 — H8·H9 쪽은 사용자에게 전달 글
