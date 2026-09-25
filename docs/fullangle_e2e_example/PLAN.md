# 전각도 낙하 클러스터 e2e 예제 패키지 계획 (2026-09-25)

## 목표

"시나리오 하나로 20방향 낙하를 클러스터에서 돌리고, 결과를 리포트까지 뽑는" 전 과정을
**남이 그대로 따라할 수 있는 형태**로 묶는다. 실측 자원량까지 같이 싣는다.

기존 자산: `/data/koopark/Test_Postprocess_v14` (2026-05-22 실행, 피보나치 20방향 DROP 1스텝 완주).
LS-DYNA 라이선스가 필요한 구간은 이미 끝나 있고, 후처리만 최신 버전으로 다시 돈다.

## 왜 후처리를 다시 도는가

5월 결과는 구버전 `koo_deep_report`/`koo_sphere_report` 산출물이다.
그 뒤에 Energy Flow·Contact Profile·핫스팟 군집·단면뷰가 들어갔다.
예제로 배포할 리포트는 현재 배포본과 일치해야 한다.

## 후처리 2변형

`koo_deep_report` 를 방향마다 두 번 돈다. 목적이 다르다.

| 변형 | 옵션 | 출력 | 용도 |
|---|---|---|---|
| light | `--no-render --ua-threads 4` | `Output/report_norender/` | 수치만 필요한 경우·CI·저사양 노드 |
| full | `--section-view --section-view-backend software --section-view-mode section --section-view-axes z --section-view-fields von_mises --ua-threads 4 --sv-threads 4` | `Output/report/` | 렌더·단면뷰 포함 완전판 |

🔴 `koo_sphere_report` 의 입력은 `$TEST_DIR/analysis_results/` 다. 이건 각 방향의
`output/Run_*/Output/report/` 를 가리키는 심볼릭 링크 모음이고, 거기 있는 `analysis_result.json` 을
읽는다(`loader.py:961`, `655`). 에너지 흐름·접촉 프로파일 탭만 binout 을 추가로 직접 읽는다.

따라서
- **full 변형(`report/`)을 전 방향 갱신한 뒤에** 집계 리포트를 떠야 한다. 안 그러면 방향별로
  신판·구판이 섞인 혼합본이 나온다(실제로 한 번 만들어 봤고 격리해 뒀다)
- light 변형은 `report_norender/` 로 나가서 링크 대상이 아니다 → 집계에 안 들어간다.
  방향별 단독 리포트 용도다
- 집계 리포트는 그래도 **1개**면 된다(변형별로 둘 만들 필요 없음)

## 자원 제약 (실측 기반)

- full 1방향 = 1:10:24, 최대 RSS 34.3 GB, 산출 388 MB (2026-09-24 실측)
- node001 은 2 CPU·4096 MB 배분 → **deep_report 를 못 돌린다**(3 GB 로 OOM rc=-9 확인)
- 따라서 후처리는 헤드노드(123 GB)에서 `ulimit -v 40000000` 걸고 **한 번에 하나**만
- d3plot 원본은 방향당 19 GB, 총 363 GB — 예제 패키지에 못 넣는다

## 단계

1. light 변형 20방향 (재개 가능 드라이버) → verify: `progress_deep_light.tsv` 20행 rc=0
2. full 변형 19방향 (1방향은 완료) → verify: `progress_deep_full.tsv` 20행 rc=0, 각 `report/contact_metrics.json` 존재
3. sphere report 1개 재생성 → verify: HTML 생성 + 탭 수·방향 수 20 확인
4. 예제 패키지 조립 → verify: README 만 보고 재현 가능한지 경로·명령 점검
5. 커밋

## 패키지에 넣는 것 / 안 넣는 것

넣는다.
- `scenario.json` (실제로 돈 것, 경로만 주석 처리)
- 실행 절차 README (prepare → submit → status → deep_report → sphere_report)
- 후처리 드라이버 스크립트 2종
- sphere report HTML + JSON
- deep report 1방향 대표 샘플(경량 파일만)
- 실측 자원 표

안 넣는다.
- d3plot (363 GB)
- 20방향 full deep_report 전량 (7.8 GB) — 경로만 안내
- 렌더 mp4/png 전량
