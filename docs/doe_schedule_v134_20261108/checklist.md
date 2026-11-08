<!-- KCR v134 DOE 실행 순서·칸 수 체크리스트 -->
# 체크리스트 — KCR v134 DOE 실행 순서·칸 수 (2026-11-08)

- [x] 사용자 결정 — 최단 완료(LPT)·상한 안 자동 칸 수·긴 것부터 제출 + 칸 고정·D2R 은 ENDTIM 비례 표시·상대값 + 기본 고정비
- [x] 조사 — 제출 경로(cumulative·sequential·batch·large-scale·rerun), doe_endtim 형태, DOE 번호 의존처, D2R 의미·게이트, 실측 자료
- [x] 이득 추정 — 2만·100 방향 표로 기본 제출 0~0.5%, 고정 칸 최대 38%, 무릎 대수
- [x] 계획·계약 초안 (PLAN.md)
- [x] 이름·기본 동작 사용자 확인 — environment.schedule, 표가 있으면 자동 켬(끄기 enabled false)
- [ ] DoeSchedule.py + test_doe_schedule.py
- [x] KCR submit(기본·sequential)·rerun·schedule.json·prepare 미리보기, 가짜 sbatch 시험 (tests/test_kcr_doe_schedule.py 69 OK)
- [x] 꺼짐 바이트 동일, 기존 KCR 시험 묶음 (GOLDEN 10 경우 + HEAD 사본과 화면까지 직접 비교)
- [ ] 문서 — scenario_reference(environment.schedule), commands/submit.md, cli_help_kcr
- [ ] 적대 리뷰
- [ ] 빌드(KCR 만, pykoocae-53 과 순서 맞춤)·SIF·tar, 커밋·푸시·알림·메모리
