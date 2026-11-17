<!-- KooChainRun · stcx 개발 요청서 v1.0(2026-11-17) 대응 계획 — 요청과 지금 코드 대조, 묶음 순서, 1묶음 설계안 -->
# KooChainRun · stcx 요청서 v1.0 대응 계획 (2026-11-17)

요청서: stcx 운영 쪽이 보낸 「KooChainRun · stcx 개발 요청서 v1.0」(10건, P0 4 · P1 5 · P2 1). 사용자가 붙여 넣고 「확인해보고 필요하면 수정해」.
요청의 핵심은 캠페인마다 새로 짜는 감시·집계·재제출·정리 스크립트를 KooChainRun 기능으로 옮기는 것이다. 수치·사례 근거는 요청자 쪽 캠페인 메모라 이 기계에는 없다.

## 1. 요청 ↔ 지금 코드 대조 (11-17, HEAD d95d2ed)

| ID | 요청 | 지금 코드 | 빠진 것 | 크기 |
|---|---|---|---|---|
| KC-01 출처·매니페스트 | Run_*/provenance.json, return_manifest.jsonl, `provenance`·`manifest` 명령 | 없음(`provenance`·`sha256` 0건). 런은 `runner_config.json` 을 뜰 때 한 번 읽는다 | 읽은 시점 설정 해시, 덱·include sha256, SIF·LS-DYNA 판, 잡 id, 시각 | 중 |
| KC-02 정상 종료·건강 | health.json, 'COMPLETED 0:0' 이어도 비정상이면 invalid, deep 실패면 체인 rc ≠ 0 | 러너는 LS-DYNA **프로세스 종료 코드만** 본다(`LSDynaSolverRunner.run`). 정상 종료 문구는 sphere 집계 필터에만. inline deep_report 실패는 경고 한 줄(`_generate_and_maybe_run_deep_report`) | d3hsp·mes·glstat 판정, 도달 시각 대 목표, 종료 코드 정책 | 큼 |
| KC-03 삭제 전 추출·삭제 관문 | 필수 추출 끝난 런만 d3plot 삭제, extraction.json | `delete_d3plot_after_deep` 이면 koo_deep_report rc 0 뒤 **무조건** `rm d3plot*` | 리포트 완결 확인, 필수 추출 목록, 삭제 기록, 캠페인 안 값 불일치 경고 | 중~큼 |
| KC-04 디스크 예산 | 제출 전 정점 예상 대 문턱 | 없음(`disk_usage`·`df` 0건) | 전부 | 중 |
| KC-05 deep_report 프로필 | `postprocess.profile: screening\|detail`, 시간·메모리 | `deep_extra_args`·`deep_timeout_seconds`·`deep_time_limit` 만. Post v51 koo_deep_report 에 `--no-section-view-per-part`·`--parts`·`--no-figures` 있음 | 프로필, 옛 SIF 가 모르는 옵션 거르기(sphere 의 has_opt 같은 것) | 작~중 |
| KC-06 완료 집계 | `status --csv`, solver_done 대 report_done | `cmd_status` 는 squeue 출력 + "coming soon", `cmd_collect` 도 빈 껍데기. 판정은 `JobManager.get_doe_status`(index·sacct) | 상태 표 전부 | 중 |
| KC-07 후처리 지킴이 | `keeper`, 같은 런 두 번 안 냄, viz 규약 | 없음(`postprocess --deep` 은 순차 실행) | 전부. Slurm 제출이라 시험은 dry-run | 중~큼 |
| KC-08 IMPACT 관문 | `prepare --check-impact` | 관문 없음. `simulation_params.impact` 의 모르는 키(`sphere` 등)를 **조용히 버리고** 기본값 `Dimension 0.008`·`height 0.5`·`dt 1e-6`(SI 크기)을 쓴다 | 관문 전부, 무시 키 경고 | 중 |
| KC-09 자리 표 | `sites --csv` | ImpactPositionSource 가 자리를 만든다 | 내보내기·빠진 자리 까닭 | 작 |
| KC-10 덱 관문 | include 상대 경로·요소 수 3자 대조·TIED·카나리아 | 없음 | 정적 점검 + 카나리아(KC-02 재사용) | 중 |

참고(이 기계의 실제 런): /data/koopark/Test_005_Fibonacci_100 97런 — 모두 정상 종료, `glstat`(ASCII)·`binout`(이진)·`d3hsp`·`mes0000`. d3hsp 에 `termination time ... 0.5000E-02`(목표)·`Problem time = 5.0000E-03`(도달)·판 머리(`ls-dyna mpp s R16 …`)·`Parallel execution with N MPP proc` 가 있다. binout 리더(lasso.dyna)는 Post SIF 에만 있고 KooChainRun venv 에는 없다.

## 2. 경계

- KooChainRun 은 명령줄 + 런·캠페인 폴더 파일(JSON·CSV)까지. MCP 도구·REST 경로는 HWAX 게이트웨이·stcx 백엔드 몫(요청서 이름안만 맞춘다).
- DynaForge: provenance 칸 이름은 요청서(DF-02)대로. DF-04 필수 추출 목록 형식·삭제 허가 API 는 미확인 → 자리(설정 칸)만 두고 미설정이면 건너뛴다.
- 덱 수정은 KMM·DropSet 몫(KC-10 경계 그대로). KooChainRun 은 확인·거절만.
- 검증: stcx 캠페인 사례는 이 기계에 없다. 이 기계의 정상 런 사본으로 아는 불량을 만들어(정상 문구 지움·도달 시각 줄임·NaN·첫 KE 0·리포트 JSON 자름) 지금 코드가 성공으로 보고 새 코드가 invalid 로 보는지 판정한다. stcx 사례 재현은 배포 뒤 stcx 쪽에서.
- LS-DYNA 라이선스가 만료라 새 해석은 못 돌린다 — 판정기는 기존 산출물로, 러너 배선은 대역 솔버로 본다.

## 3. 사용자 결정(11-17)

- 범위 = **10건 전부 한 번에**(묶음 하나, 배포 한 번).
- 종료 코드 = **구분해서 반영** — LS-DYNA 비정상(정상 종료 문구 없음·목표 시각 미달·NaN·첫 KE 0 등 invalid)이면 그 단계 실패(rc 1, 누적 체인은 다음 단계로 가지 않음). 해석은 정상인데 후처리만 실패하면 rc 3(재실행이 해석을 다시 돌리지 않게). 문턱 경고(warn)는 rc 0 + health.json.
- 배포 = **검증 뒤 배포까지**(KooChainRun 빌드 → SIF·tar → 헤드 교체).

## 4. 설계

공통: 새 모듈은 Runner/ 아래(빌드가 `--include-package=Runner`). 설정 키는 Designer 가 그대로 넘기는 `environment`·`postprocess` 블록과 새 최상위 `health` 블록(Designer 한 줄 추가). 결과 파일은 런 폴더(`Run_*/`)와 캠페인 출력 폴더에 JSON·CSV.

- **덱 훑개(Runner/DeckScan.py)** — KC-02·08·10 이 같이 쓴다. *INCLUDE(상대·절대, 있는지)·절점 수·요소 수(종류별·파트별, 1줄·2줄 꼴과 _THICKNESS 류 덧줄)·*PART·재질 밀도(단위계 판정 띠는 KooRigidBodyProperties 와 같게)·*INITIAL_VELOCITY*·*CONTROL_TERMINATION ENDTIM·*DATABASE_BINARY_D3PLOT DT·*CONTACT_*(종류·면 묶음)·줄 수. 모르는 꼴은 「불확실」 로 표시하고 추측하지 않는다.
- **KC-01 RunProvenance** — 러너가 runner_config 를 읽는 순간의 바이트로 sha256·읽은 시각, 그 사본을 캠페인 폴더 `.kcr_config_snapshots/<sha>.json` 에 한 번만. 단계마다 `Run_*/provenance.json`: 덱·include sha256, SIF 셋(KMM·LS-DYNA·Post — 경로·크기·mtime·sha256, sha 는 캐시), LS-DYNA 판·MPP 수(d3hsp), Slurm 잡·배열 id·노드, DOE·단계·별칭, 시각(시작·끝), deep 도구 판·플래그, 래퍼(`KCR_WRAPPER_NAME`·`KCR_WRAPPER_VERSION`·`KCR_WRAPPER_PATH` → sha256)·잡 스크립트(`KCR_JOB_SCRIPT`, KooChainRun 이 만드는 sbatch 가 내보냄). 칸 이름은 DF-02 그대로, 모르는 값은 null + `missing[]` 에 까닭. `KooChainRun provenance <run_dir>`, `KooChainRun manifest <campaign> [--since] [-o]` → `return_manifest.jsonl`(머리 줄: 래퍼별·설정 sha 별 런 수).
- **KC-02 RunHealth** — LS-DYNA 뒤 `Run_*/health.json`. d3hsp(정상 종료 문구·`termination time`·`Problem time`·판·MPP·파트 질량), mes*(`*** Error` 줄), glstat(에너지비 최대·HG/IE 최대·추가 질량 %·첫 KE·NaN 시작), 덱(초기 속도·단위계), DropSet.json·DropWeightImpactTestSet.json(높이·충격추 질량·요소 수). binout(파트별 IE 튐·자체 접촉 최소 에너지·기기만 추가 질량)은 Post SIF 의 lasso 로(없으면 null + 까닭). invalid = 정상 종료 아님 / 도달 < 목표 / NaN / (낙하·충격) 첫 KE 0 / 첫 KE 가 기대의 ±50 % 밖. warn = 에너지비 > 1.05 / HG/IE ≥ 10 % / 추가 질량 > 0.5 % / 첫 KE ±5 % 밖 / 파트 IE 튐 / 접촉 에너지 음수 큼 / mes 에 Error 줄(정상 종료여도). 문턱은 `health` 블록·`--thresholds` 로 바꿈. 러너: invalid 면 단계 failed(rc 1). `KooChainRun health <run_dir> [--thresholds] [--json]`.
- **KC-03 D3plotGate** — deep_report.sh 는 이제 d3plot 을 직접 지우지 않고 관문(`KooChainRun d3plot-delete <run_dir> --gate`)을 부른다. 관문: ① 리포트 JSON 이 끝까지 읽힘 ② `postprocess.required_extractions`(이름·명령·산출 파일) 다 있음 ③ `postprocess.deletion_clearance`(파일 또는 URL, 설정했을 때만) 허가 ④ health 가 invalid 아님. 못 지우면 지우지 않고 `extraction.json` 에 까닭, 지우면 `deleted_at`·지운 크기·남긴 파일. `KooChainRun extract <run_dir> [--spec]` 은 필수 추출을 돌리고 확인만. prepare·submit 때 캠페인 안 runner_config 들의 `delete_d3plot_after_deep` 이 다르면 경고.
- **KC-04 StorageBudget** — `KooChainRun budget <config> --pilot <run_dir> [--concurrency N] [--threshold 90]`. 파일럿(정상 런)의 도는 중 정점(d3plot 포함)·끝난 뒤(삭제 뒤, extraction.json 기록 우선) 크기, 런 수(DOE × 단계), 동시 수, 후처리 대기 여유, df(출력 폴더 파일시스템) → 정점 예상 대 문턱 선(기본 90 %). 판정 pass / reduce_concurrency(넣을 수 있는 동시 수) / enable_delete / reject + 근거 줄. IMPACT 는 dt 가 다르면 상태 수 비로 d3plot 몫을 늘린다. submit 은 `environment.storage_budget.pilot` 이 있으면 자동 점검, reject 면 멈춘다(`--ignore-budget` 로 넘김).
- **KC-05** `postprocess.profile: screening|detail`. screening = deep 에 `--no-section-view-per-part`(도구가 아는 옵션만 — deep_report.sh 에 has_opt), `--parts` 없으면 안내, 시간·메모리 기본값. 도는 런에 먹이려면 requeue 필요하다는 안내를 prepare·submit 에.
- **KC-06 CampaignStatus** — `KooChainRun status <config> --csv [path]` → `doe_status.csv`(DOE·단계·상태 norun·running·solver_done·report_wait·report_done·report_failed·invalid·deleted·까닭·잡 id·경과) + 상태별 수, solver_done 대 report_done 차이 강조. 리포트 JSON 은 끝 바이트·크기로 잘림 확인(전체 파싱 결과가 extraction.json 에 있으면 그것). sacct·squeue 는 한 번씩 묶어서.
- **KC-07 DeepKeeper** — `KooChainRun keeper <config…> [--interval 분] [--once] [--dry-run]`. 상태 표로 report_wait(정상 종료·리포트 없음·내 deep 잡 없음)만 골라 **배열 잡 하나**로 deep_report 를 낸다(태스크별 scontrol update 없음). 자원 기본 40 CPU·400G·제어 노드(slurmctld 호스트) 제외, `postprocess.viz` 로 바꿈. 같은 런은 `Run_*/.deep_keeper.json`(잡 id) 과 squeue 로 두 번 안 낸다. `keeper_log.jsonl`.
- **KC-08 ImpactGate** — `KooChainRun prepare <scenario> --check-impact [--sample N]` 와 `simulation_params.impact` 모르는 키 경고(did you mean, `sphere` 하위 객체 포함 — prepare 때 늘). mm 덱에서 SI 크기 기본값(height 0.5·dimension 0.008·dt 1e-6)이 쓰이면 경고. 관문은 위치마다(또는 표본) KMM 으로 덱을 만들어(`--sample`) 충격추 요소 수·질량·VZ 대 √(2gh)(덱 단위계의 g)·자리 오차·충격추 접촉이 전역 접촉과 겹침·d3plot 간격·예상 런 크기를 표로. 몸통 요소 0 이면 거절.
- **KC-09** `KooChainRun sites <config> [--csv]` → `sites.csv`(site_id·face·col·row·x·y·run_key·생성 여부·까닭). 계획 = position_source, 생성 = index·런 폴더, 빠진 자리 까닭 = index error·KMM 로그.
- **KC-10 DeckGate** — `KooChainRun gate <config> [--canary DOE목록]`: 모델 덱 include(상대 경로가 덱 폴더 기준으로 없음 → 거절), 요소·절점 수 3자 대조(원 덱·생성 덱·d3plot 머리), TIED 결속 파트 목록(사람 점검용), 카나리아 런 health, 생성 덱 줄 수. 거절이면 rc 1.
- **러너 배선** — 단계 시작 provenance → LS-DYNA → health(invalid 면 실패) → deep(rc·리포트 완결 기록, 실패면 끝 코드 3) → 관문 삭제 → provenance 끝 시각·결과. index 런 기록에 `health`·`postprocess` 칸.

## 5. 시험

- tests/test_kcr_stcx_requests.py — 판정기는 이 기계의 실제 정상 런(Test_005) 사본으로 아는 불량을 만든다(정상 문구 지움·Problem time 줄임·glstat NaN·첫 KE 0·리포트 JSON 자름·d3plot 있음/없음). 지금 코드(health 없음)는 성공으로 보고 새 코드는 invalid 로 보는지. 러너 배선은 대역 솔버(정상 산출물을 복사하는 가짜 lsdyna)로.
- 기존 tests/ 전부 회귀, 새 명령은 test_cli_help(KCR 명령 카탈로그)에.
- 컴파일본(KCR_BIN)으로 같은 시험, SIF 판정, e2e_rde(host·sif) 회귀.
