<!-- 리포트 자동 귀환 요청 A~F 처리 체크리스트 -->
# 체크리스트 — 리포트 자동 귀환 요청 (2026-10-28)

- [x] 대조: 요청서 A~F 를 현재 코드(015ac05)로 확인. B·F 폴백은 이미 해결(PLAN 표)
- [x] kooremapper-4a 에 B(5baae8d)·F 폴백(7b31d09 외) 회신
- [ ] 1. A + E(output_dir): 출력 폴더 헬퍼, DWI prepare impact_report.sh, .impact_root 링크
- [ ] 2. C: postprocess 종료 코드 0/1/3 + 요약 줄, impact 구버전 SIF exit 4
- [ ] 3. E(deep): `--all` 은 deep 이 있는 Run 을 건너뜀, `--deep` 은 다시 돎
- [ ] 4. D: sphere `--format html json terminal`(--help 에 있을 때만)
- [ ] 5. E(DWI deep): run.sh inline deep(체인과 같은 계약)
- [ ] 6. F(예제): 모델 단위계 확인 후 예제 SI 물성 정리
- [ ] 7. 시험 tests/test_result_return.py: 부모 판에서 실패 확인 → 통과, 기존 시험 전부 통과, 회귀 바이트 비교
- [ ] 8. 도움말(cli_help_kcr) postprocess 설명 갱신 + test_cli_help
- [ ] 9. 빌드 → SIF 소스 트리 → SIF → tar → 노드, 컴파일본 e2e
- [ ] 10. kooremapper-4a 에 커밋 알림, KooSlurm 에 템플릿 post_exec 제안
