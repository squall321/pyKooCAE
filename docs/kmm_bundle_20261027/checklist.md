<!-- KMM v126 묶음 체크리스트 -->
# 체크리스트 — KMM v126 묶음 (2026-10-27)

- [x] 조사 — 요소 소실 재현(merge 덱 rc 0·12개 소실, 셸은 IndexError rc 1), 러너는 KMM rc≠0 이면 멈춤, KMM 바이너리에 PyYAML 포함, KAM 식은 쉼표 없는 한 줄(`from math import *` 이름공간)
- [x] 계획·체크리스트·결정 노트
- [ ] 1 요소 소실 → 🔴 + 종료 코드 3 — 시험(아는 불량 먼저) → 구현 → 통과 → 커밋
- [ ] 2 part_yield MAT_017 min(SIGY, FS) — 시험(아는 불량 먼저) → 구현 → 통과 → 커밋
- [ ] 3 `*Recipe` 펼치기 — 시험(MCP 함수와 바이트 대조·거절 꼴·`*Recipe` 없는 파일 그대로) → 구현 → 통과 → help 주제 → 커밋
- [ ] 4 KAM eval 교체 — 시험(허용 식 값이 eval 과 같음·위험 식 거절·큰 거듭제곱) → 구현 → 통과 → 커밋
- [ ] 기존 시험 전부(run_suite.sh)
- [ ] 말뭉치 P(b480941 대비)
- [ ] 적대 리뷰 → 고침 → 다시 확인
- [ ] 빌드 v126(캡 scope, 빌드 중 소스 수정 금지) — bin 시각 확인
- [ ] 컴파일본 e2e(이번 네 가지 + 지난 판 묶음)
- [ ] SIF v126(kooremapper-fd 에 앞뒤로 알림) · compute-node-images · tar · Drive · 메일
- [ ] SIF e2e
- [ ] push
- [ ] 헤드 /opt 교체(백업) · 다시 확인
- [ ] 메모리·문서 갱신
