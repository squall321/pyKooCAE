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
| `scripts/verify_reports.py` | 산출물 온전성 검증 (rc=0 만으로는 부족하다) |
| `scripts/compare_variants.py` | 두 변형 `result.json` 전수 비교 |
| `scripts/make_resources_md.py` | 실측 TSV → `RESOURCES.md` 생성 |
| `reports/` | 생성된 리포트 실물 — 집계 리포트(HTML+JSON) + 방향별 샘플 2종 |
| `RESOURCES.md` | 단계별 실측 시간·메모리·용량, 재현성 조사 결과 |

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

🔴 **헤드노드에서 돌린다.** 요구 메모리가 32.84 GiB 라 4 GB 배분 계산노드에서는 OOM(rc=-9)
된다. 드라이버는 **한 번에 하나씩** 돈다. 동시 2개는 메모리를 넘긴다.

🔴 **`ulimit -v` 를 요구량 근처로 조이지 말 것.** 40 GB 로 걸었더니 후처리가 **경고 없이**
`rc=0` 으로 끝나면서 피크를 최대 3.3% 낮게 보고했다(안전계수 과대평가 방향). 드라이버 기본
`VMEM_KB` 는 60 GB 다. 근거와 통제 실험은 [RESOURCES.md](RESOURCES.md).

끝나면 검증한다. rc=0 은 산출물이 온전하다는 뜻이 아니다.

```bash
TEST_DIR=/data/koopark/Test_Postprocess_v14 python3 scripts/verify_reports.py light full
TEST_DIR=/data/koopark/Test_Postprocess_v14 python3 scripts/compare_variants.py
```

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

## 4. d3plot 없이 다시 뜨기

`reports/sphere_report.json.gz` 만 있으면 집계 리포트를 다시 만들 수 있다(실측 49초).
자세한 것과 주의점은 [reports/README.md](reports/README.md).

## 실측 비용

| 단계 | 1방향 | 20방향 | 최대 RSS |
|---|---|---|---|
| deep_report light | 3:06 | 약 1시간 | 32.8 GiB |
| deep_report full (`--sv-threads 12`) | 39:13 | 약 13시간 | 33.2 GiB |
| sphere_report | — | 1:17 | 0.7 GiB |

전체는 [RESOURCES.md](RESOURCES.md).

## 이 예제에 없는 것

- `d3plot` 원본 — 방향당 19 GB, 20방향 363 GB. 원본 경로로만 안내한다
- 방향별 `analysis_result.json` — 각 96 MB. 집계 리포트의 실제 입력이다
- full 변형 단면뷰 영상 — 방향당 25개 217 MB. 대표 방향도 영상은 빼고 넣었다
