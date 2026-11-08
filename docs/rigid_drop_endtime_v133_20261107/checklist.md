<!-- RIGID_DROP_ENDTIME v133(마지막 강한 재접촉 규칙) 체크리스트 -->
# 체크리스트 — RIGID_DROP_ENDTIME v133 (2026-11-07)

- [x] 근거 — 상자 폰 1000방향 멈춤 없이 끝까지: v132 가 ≥ 1.0·v0 충돌을 놓친 방향 24%, 약한 늦은 스침 521 ms (fullangle_mbd 리포트·endtime_rule_check.py)
- [x] 사용자 결정 — 마지막 강한 재접촉 규칙, 문턱 0.3·v0 옵션, Strong 계열 이름, 중력 켬·충격 조건은 v132 그대로, SIF 까지
- [x] 계획·계약 (PLAN.md)
- [x] 엔진 — STRONG_CONTACT·calm 멈춤·strong_from_events·run_presim strong_contact·새 칸, 단위 시험 88 OK, 상자 1000방향 기준과 1000/1000 같음
- [x] KMM 모드 — PresimStrongContact 키·메타 endtime_rule/strong_contact·요약·도움말 목록, 모드 시험 110 OK·도움말 527 OK
- [x] KCR — strong_contact 옵션·블록 줄(중력 끔만)·--help RIGID_DROP_ENDTIME 키 확인·table 메타 확인·도움말·시나리오 문서, 시험 149·105 OK, 끔 1924/1924 바이트 동일
- [x] 통합 — RDE 8종 + 도움말 + KMM 회귀 19종 = 28 모두 통과(encoding_guard 는 venv312), KCR 끔 바이트 동일 1924/1924
- [x] 적대 리뷰 — 물리(R4)·회귀(R5). R5 반영 8e2cf6c, 엔진 고침(세기·calm 한계, R6) 0e1c6fb
- [x] 문턱 기본 0.3 → 0.2 (사용자 결정 11-08) 4d27569 — 엔진 94·모드 110·KCR 157·도움말 527·RDE 8종 모두 통과, 상자 0.2 1000/1000
- [ ] 성능 — 2만 방향 × e 3 시간 (v132 289 s 대비)
- [ ] e2e /data/koopark/Test_E2E_v133 — v132 아는 불량 먼저, 소스 기준값
- [ ] 빌드·컴파일본 e2e (pykoocae-53 굽기 끝난 뒤)
- [ ] SIF v133·tar·Drive/메일, SIF e2e
- [ ] 커밋·푸시·알림·메모리, 헤드 /opt 교체는 사용자 확인
