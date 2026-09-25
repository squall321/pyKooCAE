# 체크리스트 — 전각도 낙하 클러스터 e2e 예제

## 준비
- [x] sphere_report 가 deep_report 산출물을 읽는지 코드로 확인 → 안 읽음(직접 재분석)
- [x] `--no-render` 플래그 존재 확인 (`koo_deep_report --help`)
- [x] 재개 가능 드라이버 작성 `run_all_deep_reports.sh light|full`
- [x] 완료 표식 방식 확정 (`<outdir>/.koo_driver_done`, rc=0 에만 생성)
- [x] 5월 구버전 `report/` 를 `report_20260522/` 로 보존하는 분기

## light 변형 (report_norender/)
- [x] 20방향 전부 rc=0
- [x] 1방향 실측 기록 — 5:24.61 / 34.3 GB / 171 MB (full 대비 시간 1/13, 메모리 동일)
- [x] `report.html` 생성 확인, 렌더 산출물 없음 확인 (`verify_reports.py` 20/20 통과)

## full 변형 (report/)
- [x] 1방향 완료 sv=4 (Run_20260522_094055_9f4583, 1:10:24 / 32.8 GiB / 388 MB)
- [x] sv=12 프로브 성공 (Run_20260522_094238_01adb3, 34:21 / 33.2 GiB / 403 MB) — 2.05배 단축
- [ ] 나머지 18방향 rc=0 (sv=12, 약 10시간)
- [ ] 전 방향 `contact_metrics.json` + `energy_flow_edges.csv` 존재

## sphere report
- [x] 구버전 SIF 사용 발견 — 기존 `sphere_report_latest.html` 은 09-11 판으로 생성됨
- [x] 09-18 판 SIF 로 1차 재생성 → 혼합본(방향 1개만 신판) 판명, 격리함
- [ ] full 20방향 완료 후 최종 재생성 (chain5 예약)
- [ ] 방향 20개 전부 반영 확인
- [x] 탭 목록 기록 (16개: Overview…Set Report. 5월 구판은 12개)
- [x] `--json` 무언 무시 결함 발견·수정 (`--format html json terminal` 필요)

## 예제 패키지
- [ ] `Examples/fullangle_drop_cluster_e2e/README.md` (runbook)
- [x] `scenario.json` 사본 + 경로 치환 안내
- [x] `scripts/run_all_deep_reports.sh`, `scripts/regen_sphere_report.sh`
- [ ] `RESOURCES.md` 실측 표
- [ ] sphere report HTML/JSON 동봉
- [x] deep report 대표 샘플 동봉 (light 1방향 + full 1방향, 각 7 MB)
- [ ] README 경로/명령 검수

## 후처리 재현성 조사 (신규, full 완료 후)
- [ ] 20방향 두 변형 `result.json` 전수 비교 — PID 14 불일치가 얼마나 퍼져 있는지
- [ ] 같은 방향 같은 옵션 재실행 → 변형별 결정성 vs 매 실행 비정성 판정

## 마감
- [ ] 기존 시험 스위트 회귀 확인 (코드 변경 없으면 생략 사유 기록)
- [ ] 커밋
