<!-- 리포트 자동 귀환 요청 A~F 처리 체크리스트 -->
# 체크리스트 — 리포트 자동 귀환 요청 (2026-10-28)

- [x] 대조: 요청서 A~F 를 현재 코드(015ac05)로 확인. B·F 폴백은 이미 해결(PLAN 표)
- [x] kooremapper-4a 에 B(5baae8d)·F 폴백(7b31d09 외) 회신
- [x] 1. A + E(output_dir) 4119850 — 출력 폴더 헬퍼, DWI prepare impact_report.sh, .impact_root 링크(실제 SIF 로더로 런 2개 확인)
- [x] 2. C ce61cd4 — postprocess 종료 코드 0/1/3 + 요약 줄, impact 구버전 SIF exit 4
- [x] 3. E(deep) 282f3dd — `--all` 은 deep 이 있는 Run 을 건너뜀, `--deep` 은 다시 돎
- [x] 4. D 639da3d — sphere `--format html json terminal`(--help 에 있을 때만). 실제 20런 e2e JSON 20/20·harvest 소비
- [x] 5. E(DWI deep) abc2eb5 — run.sh inline deep(체인과 같은 계약)
- [ ] 6. F(예제): DWI 예제는 0b79c68 에서 이미 정리. HWWarranty 9개·/data/scenario 프리셋 바닥판 SI 값은 **사용자 결정 대기**
- [x] 7. 시험 test_result_return 41검사(각 묶음 부모 판 실패 확인) · 전체 39종 중 38 통과(test_drop_attitude_angles 는 venv pytest 없음 — 기존) · 회귀 바이트 비교(impact 셸 3/3, DWI prepare 6파일)
- [x] 8. 도움말 0ffaeb7 + test_cli_help
- [x] 9a. 빌드 KooChainRun c556a678(22:42, BUILD_RC 0, GLIBC 2.35, 최저 가용 44 GB) — /data·SIF 소스 트리·build_dist 같음
- [x] 9b. 컴파일본 e2e — KCR_BIN ALL PASS(e2e_host_bin.log), 헤드 SIF v126 바이너리로 22건 실패 먼저 확인(1건은 SIF 안 PATH 대역 문제), 바이너리 prepare 셸 3종 = 소스 판
- [x] 9c. SIF v127 4d31651f(22:46, KooRemapper 8c7c4f87 기대=실제, op 3/3) · compute-node-images 같음 · tar v127 1,346,086,303 B · Drive·메일 · kooremapper-fd 앞뒤 알림 · SIF 안 KCR c556a678·prepare·rc 3·LANG=C 도움말, KMM·KAM 은 v126 과 같음
- [ ] 9d. 헤드 /opt 교체·노드 배포 — 사용자 승인/VM 대기
- [x] 10. kooremapper-4a 에 커밋·v127 알림(KooSlurm 은 0a8c9cca 로 post_exec 겹침을 이미 해소 — 제안 불필요, DWI 리포트 자리만 전달)
