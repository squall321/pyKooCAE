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
- [x] 나머지 18방향 rc=0 (sv=12). 20/20 완주, 중앙 39:13 (최소 27:30 / 최대 1:17:43)
- [x] 전 방향 `contact_metrics.json` + `energy_flow_edges.csv` 존재 (`verify_reports.py` 20/20)

## sphere report
- [x] 구버전 SIF 사용 발견 — 기존 `sphere_report_latest.html` 은 09-11 판으로 생성됨
- [x] 09-18 판 SIF 로 1차 재생성 → 혼합본(방향 1개만 신판) 판명, 격리함
- [x] full 20방향 완료 후 최종 재생성 — 1:17, 0.7 GiB, HTML 7.8 MB + JSON 17.5 MB
- [x] 방향 20개 전부 반영 확인 (`sphere_report.json` `results_summary` 20개)
- [x] 탭 목록 기록 (16개: Overview…Set Report. 5월 구판은 12개)
- [x] `--json` 무언 무시 결함 발견·수정 (`--format html json terminal` 필요)

## 예제 패키지
- [x] `Examples/fullangle_drop_cluster_e2e/README.md` (runbook)
- [x] `scenario.json` 사본 + 경로 치환 안내
- [x] `scripts/run_all_deep_reports.sh`, `scripts/regen_sphere_report.sh`
- [x] `RESOURCES.md` 실측 표 + 재현성 절
- [x] sphere report HTML(7.8 MB) + JSON(gzip 2.2 MB) 동봉, `--from-json` 재생성 49초 실증
- [x] deep report 대표 샘플 동봉 (light 1방향 + full 1방향, 각 7 MB)
- [x] README 경로/명령 검수

## 후처리 재현성 조사 (신규, full 완료 후)
- [x] 전수 비교 — 40 GB 한도에서 5방향 8건, 60 GB 로 맞추면 **불일치 0건**
- [x] 통제 실험으로 원인 확정 — 변형도 비정성도 아니고 **`ulimit -v` 40 GB** 였다
- [x] RSS 분포로 교차 확인 (40 GB: 폭 215 MiB / 60 GB: 폭 2 MiB)
- [x] light 20방향 60 GB 로 전량 재생성, 증거는 `evidence_reproducibility/` 보존

## 마감
- [x] 회귀 시험 생략 — 제품 코드 변경 0건 (문서·예제·운영 스크립트만 추가)
- [x] 커밋
