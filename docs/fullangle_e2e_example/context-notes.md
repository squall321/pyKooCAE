# 컨텍스트 노트 — 전각도 낙하 클러스터 e2e 예제

## 2026-09-25 sphere_report 는 deep_report 를 소비하지 않는다
`koo_sphere_report/loader.py` 에 `report/` 를 읽는 코드가 없다. 대신
`from koo_deep_report.core.binout_reader import parse_binout` /
`contact_map` / `energy_flow_builder` 를 임포트해 d3plot·binout 에서 직접 계산한다.
→ deep_report 변형(light/full)은 per-run 리포트에만 영향. sphere report 는 1개면 된다.
처음엔 "변형마다 sphere report 1개씩" 으로 계획했는데 근거 없이 2개를 만들 참이었다.

## 후처리는 헤드노드에서만 가능
node001 Slurm 배분이 2 CPU·4096 MB 다. `--cpus-per-task=8 --mem=16G` 는 영구 PENDING,
2스레드·3 GB 는 OOM(rc=-9). 실측 최대 RSS 가 34.3 GB 라 애초에 4 GB 노드로는 불가능하다.
헤드노드 123 GB 에서 `ulimit -v 40000000` 로 상한을 걸고 **순차** 실행한다.
동시 2개는 34×2=68 GB 로 available(66 GB)을 넘어 위험하다.

## SIF 버전 차이에 물렸던 것
node 로컬 `/opt/apptainers/SmartTwinPostprocessor.sif` 는 09-11 판,
`/data/SmartTwinPostprocessor/SmartTwinPostprocessor.sif` 는 09-18 판이다.
헤드노드에서 돌릴 때는 `/data` 쪽(신판)을 쓴다. 5월 생성 스크립트는 node 로컬 경로가 박혀 있어
그대로 쓰면 구버전으로 돌아간다.

## 구버전 결과 보존 규칙
full 변형은 `report/` 를 덮어쓴다. 5월 결과를 잃지 않게 드라이버가
`contact_metrics.json` 이 없는 `report/` 는 `report_20260522/` 로 옮긴 뒤 새로 만든다.
`contact_metrics.json` 은 신버전에만 있는 파일이라 신·구 판별자로 쓴다.

## 재개 설계
드라이버는 `<outdir>/.koo_driver_done` 이 있으면 건너뛴다. rc=0 일 때만 표식을 만들므로
중간에 죽거나 OOM 나면 그 방향만 다시 돈다. 진행 상황은 `progress_deep_<변형>.tsv` 에
방향·rc·경과·최대RSS·용량으로 한 줄씩 누적한다.

## light 는 시간만 1/13, 메모리는 같다 (실측)
| 변형 | 경과 | 최대 RSS | 산출 |
|---|---|---|---|
| light (`--no-render`) | 5:24.61 | 34.3 GB | 171 MB |
| full (렌더+단면뷰) | 1:10:24 | 34.3 GB | 388 MB |

최대 RSS 가 같다 = 메모리를 먹는 건 `unified_analyzer` 의 d3plot 분석이고, 렌더는 시간만 먹는다.
따라서 "메모리가 부족하면 `--no-render` 로 피한다"는 통하지 않는다. 34 GB 는 변형과 무관하게 필요하다.
4 GB 계산노드에서 못 돌리는 건 두 변형 모두 마찬가지다.

## regen_report.sh 가 구버전 SIF 를 가리키고 있었다
`/opt/apptainers/SmartTwinPostprocessor.sif` = 2026-09-11 판 (961 MB)
`/data/SmartTwinPostprocessor/SmartTwinPostprocessor.sif` = 2026-09-18 판 (980 MB)
5월에 생성된 스크립트는 노드 로컬 경로가 박혀 있고, 헤드노드의 `/opt/apptainers` 도 09-11 판이다.
그래서 09-23 에 만든 `sphere_report_latest.html` 은 **구판 산출물**이다. 09-18 판으로 다시 뜬다.
예제 패키지의 스크립트는 기본값을 `/data` 쪽으로 두고 `SIF=` 로 덮을 수 있게 했다.

## full 70분의 정체 — 단면뷰가 53분 (산출물 mtime 재구성)
`report/` 의 파일 mtime 으로 단계를 되짚었다.
- 21:55 시작 → 22:01:29 분석 완료 (`analysis_result.json`·motion·strain·stress·surface 전부 이 시각)
- 22:12~23:05 단면뷰 영상 25개 (전체 1 + 파트별 24), **약 53분**
- `renders/` 아래에는 `section_view_*` 밖에 없다 = 정규 LSPrePost 렌더는 애초에 생성 안 됨.
  따라서 `--render-threads` 는 이 설정에서 무의미하고, 시간 지배 knob 은 `--sv-threads` 다.

파트별 완료 시각이 단조가 아니다(part_7 이 part_6 보다 먼저) → `--sv-threads 4` 로 4워커 병렬이 맞다.
파트 하나가 2~9분이라 워커를 12로 올리면 최장 파트에 수렴한다(예상 20~25분).

최대 RSS 가 light(34345144 KB)와 full(34358828 KB)이 사실상 같다 = 34 GB 는 **분석 단계** 값이고
단면뷰 단계는 그보다 낮다. 그래서 sv-threads 를 올려도 34 GB 위로 크게 튀지 않을 것으로 보고
`ulimit -v` 를 60 GB 로 올린 뒤 **1방향 프로브**로 확인한 다음 잔여에 적용한다(추정으로 19방향 걸지 않는다).

## 🔴 돌고 있는 셸 스크립트를 덮어썼다 (내 실수, 복구함)
light 드라이버가 실행 중인 `run_all_deep_reports.sh` 를 heredoc 으로 덮어썼다.
bash 는 for 루프 같은 복합 명령을 통째로 파싱해 메모리에 들고 있지만, **루프 이후 구간은
파일 오프셋에서 다시 읽는다.** 새 내용은 길이가 달라 그 오프셋에 엉뚱한 바이트가 놓인다
— 최악의 경우 루프 본문 조각(`mv "$RD" ...` 등)이 실행될 수 있었다.
복구: 실행 중 프로세스가 붙잡고 있는 inode 에 **원본 내용을 그대로 다시 써서**(크기 2446 바이트 일치)
오프셋 이후 바이트를 원상복구하고, 새 버전은 다른 파일명(`run_deep_v2.sh`)으로 분리했다.
교훈: 실행 중 스크립트는 절대 같은 경로에 덮어쓰지 않는다. 새 파일명으로 쓴다.

## 🔴 정정 — sphere_report 는 deep_report 산출물을 읽는다
앞서 "읽지 않는다"고 적었는데 **틀렸다.** `loader.py` 를 `report`/`glob` 키워드로만 훑어
`koo_deep_report.core.*` 임포트만 보고 결론을 냈다. 실제 입력 경로는 따로 있었다.

- `loader.py:961` — `analysis_dir = test_dir / "analysis_results"`
- `loader.py:655` — `json_path = result_dir / "analysis_result.json"`
- `analysis_results/Run_xxx` → `output/Run_xxx/Output/report` 심볼릭 링크 (collect 가 생성)

binout 직접 읽기는 **에너지 흐름·접촉 프로파일 탭에만** 추가로 쓰이는 것이었다.
증거: 재생성이 41초에 끝났다. 20×19 GB d3plot 재분석이라면 불가능한 시간이다.
"시간이 안 맞는다"를 이상신호로 받아들인 게 발견 경로였다.

귀결.
- 집계 리포트는 **full 변형 전 방향 갱신 후**에 떠야 한다. 03:12 에 뜬 것은 방향 1개만 신판,
  19개는 5월 구판인 혼합본 → `sphere_report_mixed_vintage_0312.html` 로 격리
- light 변형(`report_norender/`)은 링크 대상이 아니라 집계에 안 들어간다. 방향별 단독 용도
- 교훈: 코드 근거는 임포트만 보지 말고 **입력 경로를 끝까지** 따라간다

## 🔴 `--json` 은 `--format json` 없이는 무언 무시
`__main__.py:145` `if "json" in formats:` 안에서만 `args.json` 을 쓴다.
`--format` 기본값은 `html terminal` 이라 `--json path` 만 주면 **경로만 받고 아무것도 안 만든다**.
기존 `regen_report.sh` 가 이 함정에 걸려 있었고(09-23 실행분도 JSON 없음), 내 첫 패키지 스크립트도
같은 실수를 복제했다. `--format html json terminal` 로 고쳤다.

## 🔴 두 변형의 result.json 이 파트 1개에서 다르다 (후처리 재현성 의심)
같은 방향 `9f4583`, 같은 `--ua-threads 4`, 입력 d3plot 동일인데 `report/` 와 `report_norender/` 의
`result.json` 이 파트 23개 중 **PID 14 (`PKG\PKG 2`, ELASTIC)** 하나에서 다르다.

```
peak_stress          18.64575598  vs  19.04540767   (2.1%)
time_of_peak_stress  0.001353408792 vs 0.001352394349
peak_strain          1.244992745e-05 vs 1.264130606e-05
strain_ratio         0.006224963725 vs 0.006320653030
```

- `contact_metrics.json`·`energy_flow_edges.csv` 는 **바이트 동일**
- 변위·가속도 피크(`peak_disp_mag`, `peak_acc_mag`)는 일치 → 절점 단위는 문제 없음
- 요소 단위(응력·변형률) 피크 스캔에만 나타남
- 2% 차이라 근사 동률 tie-break 가 아니다 = 한쪽이 그 상태를 놓쳤다

원인 후보: 요소 스캔의 상태 누락 또는 공유 max 버퍼 경쟁. `KooD3plotReader`(SmartTwinPostprocessor)
쪽이라 이 프로젝트 범위 밖이지만 리포트 재현성에 직접 영향이 있다.

검증 계획 (full 20방향 완료 후, 지금은 메모리 겹치기 금지로 보류).
1. 전 20방향 두 변형 `result.json` 비교 → 얼마나 퍼져 있는지 정량화
2. 같은 방향을 같은 옵션으로 **한 번 더** 돌려 변형별 결정성인지 매 실행 비정성인지 판정
