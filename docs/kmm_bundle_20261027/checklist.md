<!-- KMM v126 묶음 체크리스트 -->
# 체크리스트 — KMM v126 묶음 (2026-10-27)

- [x] 조사 — 요소 소실 재현(merge 덱 rc 0·12개 소실, 셸은 IndexError rc 1), 러너는 KMM rc≠0 이면 멈춤, KMM 바이너리에 PyYAML 포함, KAM 식은 쉼표 없는 한 줄(`from math import *` 이름공간)
- [x] 계획·체크리스트·결정 노트
- [x] 1 요소 소실 → 🔴 + 종료 코드 3 (4612cee) — 옛 코드 5 FAIL → 10 OK. merge 예제 rc 3·로그 파일에도 요약
- [x] 2 part_yield MAT_017 min(SIGY, FS) (631eaf6) — 옛 코드 FS 30<SIGY 45 에 45 → 30 'FS(파괴)'
- [x] 3 `*Recipe` 펼치기 (a331d8e) — 옛 코드는 `*Recipe` 를 조용히 무시(rc 0) 21 FAIL → 24 OK. MCP recipes.save 로 만든 판·MCP 옵션 글과 바이트 같음·거절 12꼴·help recipe
- [x] 4 KAM eval 교체 (49d10e7) — 옛 코드는 os.system 실제 실행(MARK 생성)·9**9**9 멈춤 9 FAIL → 24 OK. v125 컴파일 KAM 도 PKG 로 실행 확인(판정기 kam_pkg_check.sh)
- [x] 기존 시험 전부(run_suite.sh, suite_r) — 38종 통과(test_drop_attitude_angles 는 venv 에 pytest 가 없어 대역 실행기로 30건)
- [x] 말뭉치 P(앞 518건, 4개 커밋 상태) — 다름 1(F_z1 Ctrl-Z 실제 소실 rc 0→3). 리뷰 R 고침을 위해 멈춤
- [x] 말뭉치 Q·R(중간 점검, 455·467건) — 다름은 실제 소실 rc 0→3 뿐(R 의 자기 *INCLUDE 2건은 오탐 → T 에서 고침)
- [x] 적대 리뷰 R — 9건(중간 3·낮음 6) 모두 고침(fbe4eca·d545b9b·d547730·1c2d801), 시험 묶음 2회 통과
- [x] 집중 리뷰 S — 9건(높음 1: DTI 회귀) 모두 고침(de5e5bc·584dc70·4afbf7c·a462dfe·d70f16d), 시험 묶음 3회 통과
- [x] 확인 리뷰 T — 낮음 5건 + 말뭉치 R 오탐 2건(자기 *INCLUDE) 고침(2632734·3296a37·2762399). 리뷰 라운드 종료(수렴)
- [x] 시험 묶음 4회째(suite_u) 통과 · 말뭉치 S(최종, 738건) — 같음 725, 다름 13 모두 KMM 출력의 실제 요소 소실이 rc 3 으로 드러난 것
      (C_g6·C_real_kr_offset·F_z1·H_t7×2·I_X4b·J_M6·J_Y5·L_P7·M_m024×2·V126×2 — 오탐 0)
- [ ] 빌드 v126(캡 scope, 빌드 중 소스 수정 금지) — bin 시각 확인
- [ ] 컴파일본 e2e(이번 네 가지 + 지난 판 묶음)
- [ ] SIF v126(kooremapper-fd 에 앞뒤로 알림) · compute-node-images · tar · Drive · 메일
- [ ] SIF e2e
- [ ] push
- [ ] 헤드 /opt 교체(백업) · 다시 확인
- [ ] 메모리·문서 갱신
