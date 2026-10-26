<!-- sphere_report 자동화 수정 체크리스트 -->
# 체크리스트 — sphere_report 자동화 (2026-10-26)

- [x] 대조 — 문서 진단을 코드로 확인(자원 고정·rc 0·순차 루프·350 고정), 정정 4건(context-notes)
- [x] 계획 PLAN.md, a9 에 도구 쪽 인터페이스 제안
- [ ] ① build_sphere_sbatch — 런 수 N 으로 자원 산출, LS-DYNA environment 의 ncpu·memory 를 물려받지 않음, 명시값보다 산출값이 크면 산출값 + 알림, 파티션 상한 + 알림
- [ ] ① 두 호출부가 N(runner_config 의 step 총수)·도구 옵션 지원 여부를 넘김 — KooChainRun._maybe_submit_sphere_after, SlurmSubmitter._maybe_submit_sphere_job
- [ ] ②③④ sphere_report.sh — 실행 시점에 --parallel-runs·--yield-map 지원 확인 후 넘김, 'Loaded 0 results' 를 셸에서도 잡아 비 0 종료(옛 SIF 대비)
- [ ] ④ KMM — 낙하 덱을 쓸 때 파트별 항복응력 맵 JSON(MAT_003·MAT_024 SIGY/LCSS·ORIENTED_CRACK)
- [ ] ④ CumulativeDesigner — sphere_report.sh 에 맵 경로
- [ ] 시험 — tests/test_sphere_resources.py (자원 산출·우선순위·상한·sh 배선·맵)
- [ ] 회귀 — 시험 전부·MinimumModel md5
- [ ] 적대 리뷰
- [ ] 빌드 KMM·KCR → SIF v125 → tar → Drive·메일, 헤드 /opt
- [ ] a9 — ② 0건 비 0 종료 ③ --parallel-runs(선행 캐시 채우기) ④ --yield-map → Post v42
