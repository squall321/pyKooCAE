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
- [x] 기존 tests/ 회귀(62개 — 처음 실패 3개 고침, KCR 관련 21개 rc 0·cli_help ALL PASS)
- [x] 커밋(기능별)·push
- [x] 독립 적대 리뷰 상·중·하 반영
- [x] 빌드 KCR a558c8ed → 굽기 v137 / 관문 pkill 수정 → KCR 336b0f28 → 굽기 v138 (둘 다 헤드에 넣지 않음)
- [x] 🔴 사고(헤드 노드 서비스 컨테이너 32개) — 시험 가짜 pkill·관문 정리 끔·러너 정리 SLURM_JOB_ID 가드(e6126f9·e2b76a2), 복구는 포털 세션
- [x] 가드 빌드 KCR 501601d7 → 컴파일본 시험 110·41·101·157·105 FAIL 0
- [x] e2e_rde host(501601d7) ALL PASS 100
- [x] 굽기 v139(SIF 28574f6a·KooRemapper 248ec9bc·tar v139·Drive·메일) → SIF 판정(KCR_IN_SIF 105 OK·e2e sif ALL PASS 100) → 헤드 /opt 교체(v136 → v139, 22:11)
- [x] 알림(43·kooremapper-fd·4a·포털 sha256)·문서 커밋(660b1a9)·메모리
