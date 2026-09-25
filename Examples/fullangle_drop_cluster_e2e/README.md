# 전각도 낙하 — 클러스터 e2e 예제

시나리오 하나로 **피보나치 20방향 낙하**를 Slurm 에 던지고, 방향별 깊은 분석과
전각도 집계 리포트까지 뽑는 전 과정이다. 실제로 완주한 결과(2026-05-22 해석,
2026-09-25 후처리 재생성)와 그때 쓴 스크립트·실측 자원량을 함께 싣는다.

원본 작업 디렉터리: `/data/koopark/Test_Postprocess_v14` (NFS)

## 구성

| 파일 | 내용 |
|---|---|
| `scenario.json` | 실제로 돈 시나리오 (20방향 피보나치, DROP 1스텝, 자동 후처리 켬) |
| `scripts/run_all_deep_reports.sh` | 방향별 deep_report 재생성 드라이버 (재개 가능, light/full) |
| `scripts/regen_sphere_report.sh` | 전각도 집계 리포트 재생성 |
| `reports/` | 생성된 리포트 실물 (집계 리포트 + 대표 1방향 샘플) |
| `RESOURCES.md` | 단계별 실측 시간·메모리·용량 |

## 1. 해석 (LS-DYNA 필요)

```bash
cd /data/koopark/Test_Postprocess_v14          # NFS. /tmp 는 계산노드가 못 본다
KooChainRun prepare  scenario.json             # → runner_config.json
KooChainRun submit   runner_config.json        # → jobs.json, output/slurm_scripts/
KooChainRun status   runner_config.json        # 진행 확인
KooChainRun collect  runner_config.json        # 결과 수집
```

`scenario.json` 에서 실제 환경에 맞게 고쳐야 하는 값.

- `base_dir` — 이 작업 디렉터리
- `scenarios[].template` — 모델 `.k`
- `environment.lsdyna_apptainer_env.LSTC_LICENSE_SERVER` — **헤드노드 IP**
  (`localhost` 로 두면 계산노드에서 signal 12 로 죽는다)
- `environment.memory` / `lsdyna_memory` / `ncpu` — 노드 Slurm 배분에 맞춘 값.
  크게 적으면 sbatch 가 영구 PENDING 된다

결과 배치.

```
output/
  Run_<타임스탬프>/            방향 하나 = Run 폴더 하나 (20개)
    DropSet.k                  이 방향 자세로 회전된 입력 덱
    step_config.txt            KMM 옵션 파일
    Output/
      d3plot, d3plot01…        상태 파일 (방향당 약 19 GB)
      binout0000               시간이력
  simulation_index.json        방향 ↔ Run 폴더 매핑
  slurm_scripts/               제출 스크립트와 로그
```

## 2. 방향별 깊은 분석 (deep_report)

`scenario.json` 의 `postprocess.enabled` 가 켜져 있으면 해석 직후 자동으로 돈다.
**나중에 다시 돌리거나 최신 배포본으로 갱신할 때**는 드라이버를 쓴다.

```bash
TEST_DIR=/data/koopark/Test_Postprocess_v14 \
SIF=/data/SmartTwinPostprocessor/SmartTwinPostprocessor.sif \
    bash scripts/run_all_deep_reports.sh full      # 렌더·단면뷰 포함
TEST_DIR=... bash scripts/run_all_deep_reports.sh light   # 수치만 (--no-render)
```

두 변형은 목적이 다르다.

| 변형 | 출력 | 용도 |
|---|---|---|
| `full` | `Output/report/` | 렌더·단면뷰 포함 완전판. 보고용 |
| `light` | `Output/report_norender/` | 수치만. CI·재집계·저사양 환경 |

🔴 **헤드노드에서 돌린다.** 최대 RSS 가 34 GB 라 4 GB 배분 계산노드에서는 OOM(rc=-9)
된다. 드라이버가 `ulimit -v 40000000` 로 상한을 걸고 **한 번에 하나씩** 돈다.
동시 2개는 메모리를 넘긴다.

중단됐으면 같은 명령을 다시 준다. rc=0 인 방향만 `.koo_driver_done` 표식이 있어 건너뛴다.
진행 상황은 `progress_deep_<변형>.tsv` 에 방향·rc·경과·최대RSS·용량으로 쌓인다.

## 3. 전각도 집계 리포트 (sphere_report)

```bash
TEST_DIR=/data/koopark/Test_Postprocess_v14 bash scripts/regen_sphere_report.sh
```

입력은 `analysis_results/` 다. `KooChainRun collect` 가 만드는 심볼릭 링크 모음으로,
각 방향의 `output/Run_*/Output/report/` 를 가리킨다. 거기 있는 `analysis_result.json` 을 읽고
(`loader.py:961`, `655`), 에너지 흐름·접촉 프로파일 탭만 binout 을 추가로 직접 읽는다.

🔴 그래서 순서가 있다. **full 변형을 전 방향 갱신한 뒤에** 집계 리포트를 뜬다.
일부만 갱신된 상태로 뜨면 방향별로 신판·구판이 섞인 혼합본이 나오고, 겉보기로는 구분되지 않는다.

🔴 light 변형은 `report_norender/` 로 나가므로 링크 대상이 아니다 — 집계에 들어가지 않는다.
방향별 단독 리포트 용도다. 집계 리포트는 변형과 무관하게 1개면 된다.

🔴 `--json` 은 `--format` 에 `json` 이 있어야 효력이 있다(`__main__.py:145`).
없으면 경로만 받고 조용히 아무 파일도 안 만든다.

## 이 예제에 없는 것

- `d3plot` 원본 — 방향당 19 GB, 20방향 363 GB. 원본 경로로만 안내한다
- full 변형 20방향 전량 산출물 — 방향당 388 MB. 대표 1방향만 동봉한다
