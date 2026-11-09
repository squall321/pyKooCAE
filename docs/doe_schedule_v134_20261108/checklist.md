<!-- KCR v134 DOE 실행 순서·칸 수 체크리스트 -->
# 체크리스트 — KCR v134 DOE 실행 순서·칸 수 (2026-11-08)

- [x] 사용자 결정 — 최단 완료(LPT)·상한 안 자동 칸 수·긴 것부터 제출 + 칸 고정·D2R 은 ENDTIM 비례 표시·상대값 + 기본 고정비
- [x] 조사 — 제출 경로(cumulative·sequential·batch·large-scale·rerun), doe_endtim 형태, DOE 번호 의존처, D2R 의미·게이트, 실측 자료
- [x] 이득 추정 — 2만·100 방향 표로 기본 제출 0~0.5%, 고정 칸 최대 38%, 무릎 대수
- [x] 계획·계약 초안 (PLAN.md)
- [x] 이름·기본 동작 사용자 확인 — environment.schedule, 표가 있으면 자동 켬(끄기 enabled false)
- [x] DoeSchedule.py + test_doe_schedule.py (ddd1a4c, 지금 49 OK)
- [x] KCR submit(기본·sequential)·rerun·schedule.json·prepare 미리보기, 가짜 sbatch 시험 (tests/test_kcr_doe_schedule.py 지금 101 OK)
- [x] 꺼짐 바이트 동일, 기존 KCR 시험 묶음 (GOLDEN 10 경우 + HEAD 사본과 화면까지 직접 비교)
- [x] 문서 — scenario_reference(environment.schedule), commands/submit.md·rerun.md, cli_help_kcr
- [x] 적대 리뷰(R7) — High 1(무릎 여유 0.05 가 라운드로빈보다 최대 3.6% 늦음)·Medium 1·Low 7, 숨은 순서 의존 없음·끔 바이트 동일 80 경우·knee 이분 탐색 정확
  - [x] 2차 반영(서브에이전트) — knee_tolerance 0·칸 줄면 ⚠️·시간 단위 짐작·끔/표 없음 무검사·rerun 검사 순서·표 밖 DOE·슬롯 echo·batch+seq·돌연변이 M1·M3·M4·문서·이득 수치
- [x] 빌드 KCR 만 — 9ebe11e, build_KooChainRun_python312.sh 를 상한 24G scope 로(22:4x~22:50, 최저 가용 44 GB, glibc 2.35, Runner.DoeSchedule 들어감). /data·appt313/opt 의 KooChainRun 만 v134, KMM 은 v133(09:33) 그대로
- [x] 컴파일본 스모크(/data/koopark/Test_E2E_v134/smoke, 가짜 Slurm) — prepare 미리보기, 기본 제출 순서 2·8·6·4·3·7·5·1·9·10(긴 것부터), --sequential --nodes 4 칸 0.47·0.46·0.46·0.39 h, --nodes 10 → 6 칸 ⚠️
- [x] e2e(v133 하네스, 호스트·SIF) — v134 는 runner_config·KMM 을 바꾸지 않아 v133 golden 대조. 호스트·SIF 모두 ALL PASS 100 OK · SKIP 0 (/data/koopark/Test_E2E_v134)
- [x] SIF v134 — 굽기 전 헤드·compute-node-images a92c1080(v133)·마지막 tar v133 확인, KooRemapper 15d013ec 검증. SIF 34c00cad(compute-node-images 같음, KCR v134 + KMM v133 54d0862d), tar 20261108_v134 16e28930·Drive·메일
- [x] 커밋·푸시(f3a49d9..653cbea, pykoocae-53 커밋 7개 함께 — 허락 받음)·알림(pykoocae-53·kooremapper-fd·smarttwinmcp-c8·4c)·메모리
- [x] 헤드 /opt 교체 — 사용자 승인(11-09): 00:45, v133 은 rename 백업 _backup_20261109_004506(a92c1080), 헤드 34c00cad, apptainer exec 로 KCR environment.schedule·KMM PresimStrongContact 0.2 확인. pykoocae-53 이 v135(KCR v134 + KMM 누적 체인 고침)를 이어 굽는다
