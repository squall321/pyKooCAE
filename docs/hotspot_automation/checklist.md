<!-- 핫스팟 자동 후처리 배선 체크리스트 -->
# 체크리스트 — 핫스팟 고도화 배선

- [x] 실측 — 엔진 7종·시간 집계 3종 vs `koo_deep_report` 3종 거절(rc=1), KooChainRun 3종, sphere 파트 필터 미배선
- [x] KooD3plotReader 요청서·알림(kood3plotreader-d3)
- [x] 2 `hotspot_part` → `--hotspot-part` — 이전 코드와 4경우 바이트 동일, 숫자 아닌 값 경고·제외(시험 [10])
- [x] 3 도움말 `postprocess_json`·DROP 키 — test_cli_help ALL PASS, MCP scenario_drop 재생성
- [x] KooD3plotReader §1 이름 확정(2026-10-16) — `--hotspot-criterion` 7종+엔진 별칭, `--hotspot-time-aggregate {elemmax_then_mean,mean_then_timemax,both}`
- [x] KooD3plotReader §1 구현 e8460d9 — 저장소 소스+배포 엔진으로 검증 단계 확인(별칭 통과, 잘못된 값 rc=1). 사용자 배포 승인 전달(2026-10-16)
- [x] 1b 미리 작성·시험 통과 — 패치로 보관(스크래치패드 hotspot_1b.patch), 작업 트리는 원복(그쪽 요청: 배포 알림 뒤에 넣기)
- [x] KooD3plotReader §1 배포(be9d2b0) — 노드 로컬 Post SIF 7142a658 을 헤드·node001·node002 에서 확인
- [x] 1 기준 7종·`hotspot_time_aggregate` 키(493a86d) — 시험 [9]~[12] PASS, 배포 바이너리 런타임 deep_report.sh 에 플래그 확인(아래 e2e)
- [x] 빌드 → SIF v118(1147567e) → tar·메일 → deploy_apptainers.sh 로 헤드·node001·node002 — sha 3곳 동일. SIF 안 KooRemapper 는 1164d8ed(5a0fbd6)
- [x] MCP — post_* 재생성(16efc642) + kooremapper_core 를 배포 커밋 5a0fbd6 으로(7dae7698, remap_* 3 추가) — 시험 328 통과·1 실패(벤더링 비교, 리포가 배포보다 앞섬), 서비스 재기동 167종
- [x] 배포본 e2e — MCP post_deep_report(잡 1211, 대조군 1212)·캠페인 경로(잡 1214, 대역 솔버) 모두 두 기준 23+23항목, 군집 전부 mean_timemax, 부등식 위반 0. kood3plotreader-a9 에 전달. 1214 는 HTML 전에 시간 제한으로 끊김(컨텍스트 노트)
- [x] 4 3D 인벨롭 — KooD3plotReader 45/45 완료·배포(be9d2b0). 새 CLI 옵션은 `--viewer`·`--hotspot-part` 둘뿐(각도 프리셋·컨투어는 HTML 안 기능) → `sphere_viewer`·`hotspot_part` 로 배선(493a86d), 컴파일 prepare 의 sphere_report.sh 에서 확인
