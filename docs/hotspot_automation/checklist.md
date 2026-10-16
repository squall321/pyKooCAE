<!-- 핫스팟 자동 후처리 배선 체크리스트 -->
# 체크리스트 — 핫스팟 고도화 배선

- [x] 실측 — 엔진 7종·시간 집계 3종 vs `koo_deep_report` 3종 거절(rc=1), KooChainRun 3종, sphere 파트 필터 미배선
- [x] KooD3plotReader 요청서·알림(kood3plotreader-d3)
- [x] 2 `hotspot_part` → `--hotspot-part` — 이전 코드와 4경우 바이트 동일, 숫자 아닌 값 경고·제외(시험 [10])
- [x] 3 도움말 `postprocess_json`·DROP 키 — test_cli_help ALL PASS, MCP scenario_drop 재생성
- [x] KooD3plotReader §1 이름 확정(2026-10-16) — `--hotspot-criterion` 7종+엔진 별칭, `--hotspot-time-aggregate {elemmax_then_mean,mean_then_timemax,both}`
- [ ] (대기) KooD3plotReader §1 배포 알림
- [ ] 1 기준 7종·`hotspot_time_aggregate` 키 → verify: 생성 sh 에 플래그, 배포 deep 이 받음
- [ ] 빌드(KMM·KooChainRun) → SIF → tar·메일 → 노드 → sha — 이 SIF 에 KooRemapper 10-16 판(e37fdf4f)도 들어간다
- [ ] MCP — kooremapper_core 재벤더링(새 op 3개) + 생성기 재실행 + post_deep_report 설명 재생성(새 --help)
- [ ] 배포본 e2e — 핫스팟 켠 캠페인 postprocess 산출물에 새 기준 항목
- [ ] 4 3D 인벨롭 — KooD3plotReader 완료 후 새 옵션 키 배선
