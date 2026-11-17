<!-- KooChainRun · stcx 요청서 v1.0(10건) 체크리스트 -->
# 체크리스트 — KooChainRun · stcx 요청서 v1.0 (2026-11-17)

- [x] 요청서 대조(요청 ↔ 지금 코드) — PLAN §1
- [x] 사용자 결정 — 10건 전부 한 번에, 종료 코드 구분(invalid rc 1 · 후처리만 실패 rc 3 · warn rc 0), 검증 뒤 배포까지
- [x] 아는 불량 기준 — 옛 트리 gen_d95d2ed(KCR_ROOT)로 새 시험 3 OK / 29 FAIL, 옛 러너는 정상 문구 없는 런을 completed·rc 0
- [x] 덱 훑개 Runner/DeckScan.py — 실제 낙하 덱 절점·요소·재질 수가 d3hsp 와 같음
- [x] KC-01 출처 기록·매니페스트(+ C4 analysis_method·deck_element_count)
- [x] KC-02 정상 종료·건강 판정(binout 은 Post SIF lasso, 캠페인 비교)
- [x] KC-03 삭제 전 추출·d3plot 삭제 관문
- [x] KC-04 디스크 예산(submit 은 pilot 이 있으면 자동, 통과가 아니면 멈춤)
- [x] KC-05 deep_report 프로필(도구가 아는 옵션만·실측 최대 RSS 기록)
- [x] KC-06 완료 집계(status --csv, 후처리 대기 강조)
- [x] KC-07 후처리 지킴이(배열 잡 하나·두 번 안 냄·제어 노드 제외·실측 RSS)
- [x] KC-08 IMPACT 관문(SIF 안 KMM 으로 표본 덱 — 정상 통과·g 9.81 거절)
- [x] KC-09 자리 표(sites.csv)
- [x] KC-10 덱 관문(include·요소 수 3자 대조·TIED·카나리아)
- [x] 러너 배선 — 가짜 LS-DYNA 로 rc 0·1(재시도 없음)·3 확인
- [x] 도움말 카탈로그(새 명령 9·주제 health_json·run_files·IMPACT 키) + test_cli_help ALL PASS
- [x] 새 시험 tests/test_kcr_stcx_requests.py 86 판정 통과
- [ ] 기존 tests/ 회귀
- [ ] 커밋(기능별)·push
- [ ] 빌드(KooChainRun) → 컴파일본 시험 → SIF·tar → SIF 판정 → 헤드 교체
- [ ] 알림·메모리
