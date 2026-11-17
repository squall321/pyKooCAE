<!-- KooChainRun · stcx 요청서 v1.0 작업 노트 — 결정과 그 까닭 -->
# 작업 노트 — KooChainRun · stcx 요청서 v1.0 (2026-11-17)

## 출발점(11-17)
- 요청서 원문은 리포 밖 /data/koopark/Test_kcr_stcx_20261117/REQUEST_v1.0.md(사용자가 붙여 넣음 — 미출시 과제 이름·PC 경로가 있어 리포에 두지 않는다, 사용자 부탁 11-17). 근거 메모는 요청자 쪽·stcx 에만 있다.
- HEAD d95d2ed(v136 배포 기록). 헤드·compute-node-images Pre = v136 1c973c25.
- 사용자 결정: 10건 전부 한 번에 · 종료 코드 구분(invalid rc 1, 후처리만 실패 rc 3, warn rc 0) · 검증 뒤 배포까지.

## 코드에서 확인한 사실
- 러너 성공 판정은 LS-DYNA 프로세스 종료 코드뿐(`LSDynaSolverRunner.run` → returncode 0 이면 True). 정상 종료 문구는 sphere_report.sh 의 집계 필터에만 있다.
- inline deep_report 실패는 `logging.warning` 한 줄 — 단계·잡 결과에 닿지 않는다(요청서의 「실패해도 Exit code 0」).
- deep_report.sh: `set -e`, koo_deep_report rc 0 뒤 `delete_d3plot_after_deep` 이면 `rm -f d3plot d3plot[0-9]*` — 리포트가 완결인지 보지 않는다.
- 잡 스크립트(run_doe_XXX.sh)는 러너 종료 코드를 그대로 넘긴다(`exit $EXIT_CODE`). 'COMPLETED 0:0' 거짓 정상은 러너가 0 을 돌려준 경우다.
- `cmd_status`·`cmd_collect` 는 빈 껍데기("coming soon"). DOE 상태는 `JobManager.get_doe_status`(index 의 단계 status + sacct).
- IMPACT 단계 설정(`_create_step_config` IMPACT 갈래)은 `simulation_params.impact` 에서 아는 키만 읽고 나머지는 조용히 버린다. 기본값 `height 0.5`·`dimension 0.008`·`dt 1e-6`·`tFinal 0.001`·`offset_distance 1e-5` 은 SI 크기. 중력은 주면 넘기고, 없으면 KMM 이 재질 밀도로 단위계를 판정한다.
- d3hsp 에 목표 `termination time`·도달 `Problem time`·판 머리·`Parallel execution with N MPP proc`·`summary of mass`(파트별)·`t o t a l  m a s s` 가 있다. glstat(ASCII)은 BINARY 3 이면 생긴다. matsum·sleout 은 MPP 에서 binout 에만 있다 — lasso.dyna 는 Post SIF 에만.
- DROP 덱: `*INITIAL_VELOCITY` NSID 1(기기 절점), DropSet.json 에 drop_height·velocity. IMPACT 덱 메타(DropWeightImpactTestSet.json)에 충격추 mass·num_elements·energy(kinetic_energy·speed·drop_height).
- 단위계 띠(KooRigidBodyProperties): 밀도 중앙값 1e-10~1e-7 mm-t-s · 1e-7~1e-4 mm-kg-ms · 1e-4~0.1 mm-g-ms · 100~1e5 m-kg-s.
- Post v51 koo_deep_report 에 `--no-section-view-per-part`·`--parts`·`--no-figures` 가 있다.
- Designer 는 `environment`·`simulation_params`·`postprocess` 를 그대로 runner_config 로 넘긴다.

## 결정과 까닭(구현 중, 11-17)
- **runner_config 바이트는 그대로.** 43 의 e2e_rde 가 runner_config 를 기준과 바이트로 대조한다 — scenario 경로·sha 는 runner_config 옆
  `.<이름>.kcr_prepare.json` 에 따로 쓴다. Designer 는 scenario 에 `health` 블록이 있을 때만 그 키를 더한다(없으면 바이트 같음).
- **목표 시각은 생성 덱 ENDTIM 이 먼저**(종료 시간 표가 쓴 값 — 43 의견). 없을 때만 d3hsp termination time. 상대 허용 1e-3(출력 반올림).
- **HG/IE 판정값 = max(HG)/max(IE).** 시간별 HG/IE 최대는 충돌 뒤 IE 가 작아진 구간의 나눗셈이라 정상 런(Test_005)도 0.47 로 걸렸다 —
  참고값(hg_over_ie_tmax·_end)으로만 남긴다. Test_005 각도에 따라 1.5·8.1·17.4 % — 17.4 % 런이 warn 인 것은 요청한 규칙대로.
- **파트 IE 튐은 런 하나 문턱을 끈다(기본).** 출력 한 칸에 첫 KE 의 5 % 문턱이 정상 런(디스플레이 6 %)을 걸었다. 요청서 사례(1,346 대 371 mJ)는
  다른 런과의 비교라 캠페인 비교(같은 파트 IE 최대가 중앙값의 3배 넘음 → warn)로 잡는다. 문턱은 stcx 사례로 다시 맞출 것.
- **health invalid 는 재시도하지 않는다(결정적).** 라이선스 문구가 있으면만 재시도. 기록 코드(health·provenance)가 실패해도 해석 판정은
  예전처럼 LS-DYNA 종료 코드로 간다(경고만).
- **rc 3 은 잡 끝 코드에만.** 단계 status 는 completed — JobManager.get_doe_status 가 completed 로 보아 rerun 대상이 아니다(시험으로 묶음).
- **d3plot 삭제는 관문 명령으로.** deep_report.sh 는 이제 직접 지우지 않는다. 관문 명령을 모르는 틀(DWI)은 리포트 JSON 두 개 끝 바이트를 본다.
  postprocess --deep 은 관문 없이 지우던 옛 deep_report.sh 를 다시 만든다. 이미 있음(--all 건너뛰기) 판정은 파일 존재가 아니라 완결.
- **deep_report.sh 빈 리포트 = rc 3.** koo_deep_report 는 성공하면 report/ 에 result.json·analysis_result.json 을 둘 다 쓴다
  (analysis_result.json 이 없으면 도구가 RuntimeError 로 끝난다) — 둘 다 요구해도 정상 런을 실패로 잡지 않는다.
- **충격추 접촉 겹침 규칙.** KMM 충격 덱은 늘 「전부 대 벽」·「전부 대 충격추」(둘 다 SSTYP 5) 두 장이 충격추를 덮는다 — 처음 규칙은 모든
  IMPACT 덱에 경고가 났다. 원 모델 덱의 접촉이 충격추를 덮을 때만(관문은 모델 덱을 안다), 모델 정보가 없으면 「전부」형이 두 장보다 많을 때만.
  실린더 단끼리 TIED 는 세지 않는다.
- **호스트 KMM 은 gmsh 가 없어 충격추를 메시하지 못한다.** 관문 끝까지 시험을 호스트 KMM 으로 돌렸더니 충격추 몸통 요소 0 덱이 나왔고 관문이
  거절했다 — 요청서의 「몸통 요소 0」 도 이런 원인일 수 있다(관문이 잡는다). 시험은 운영처럼 SIF 안 KMM 으로.
- **디스크 예산 시험은 사용량을 고정**(usage 인자) — 공유 NFS 사용량이 시험 사이에 바뀌어 한 번 뒤집혔다.
- **대역 솔버 e2e 주의.** 지난 실해석 출력을 복사하는 대역 솔버는 새 덱과 높이·ENDTIM 이 다르면 이제 health 에 걸릴 수 있다 — 배선만 보는
  시험이면 `health.enabled: false`.
- **미출시 과제 이름·PC 경로는 리포에 적지 않는다**(사용자 부탁 — KooSlurm-35 경유). 요청서 원문은 리포 밖으로 옮기고 코드 주석에서 걷어 냈다.
- **C4(사용자 결정 전달)**: 매니페스트 줄에 analysis_method(DROP → ANL-DROP, IMPACT → ANL-PARTIAL_IMPACT, 그 밖 null)·deck_element_count.
  D2: 진입점은 KooChainRun 직접 제출 유지.

## 시험(11-17)
- tests/test_kcr_stcx_requests.py 86 판정 모두 통과. 옛 트리(gen_d95d2ed, KCR_ROOT)는 3 OK / 29 FAIL — 통과 3개는 예전 동작을 지키는 판정.
  옛 러너는 LS-DYNA rc 0·정상 문구 없음 런을 completed·rc 0 으로 본다(요청서의 'COMPLETED 0:0' 그대로 재현).

## 회귀·커밋·빌드(11-17)
- **회귀 1차(suite1).** tests/ 62개 중 59개 rc 0. 실패 셋: test_encoding_guard(DeepKeeper open() encoding 빠짐), test_kcr_doe_schedule(잡 스크립트
  KC-01 세 줄로 [0] 바이트 동일 10건 — 43 의 정답 GOLDEN 은 두고 norm() 이 그 세 줄만 지우게, 43 확인), test_result_return(가짜 deep 이
  analysis_result.json 하나만 쓴다 — '둘 중 하나' 약속을 내가 깼다).
- **리포트 완결 규칙을 둘로.** complete = 끝까지 쓰인 파일이 하나 이상·있는 것 중 잘린 것 없음(deep 성공·postprocess --all 건너뛰기·상태 표 —
  옛 SIF 는 한 파일만 쓴다). complete_all = 둘 다(d3plot 삭제 관문 — harvest 는 result.json, impact 는 analysis_result.json).
- 패치 뒤 다시: 세 시험 + cli_help·hotspot_keys·새 시험 모두 rc 0.
- **매니페스트**에 scheduler_state·chain_exit_code(sacct 한 번)·solver_exit_code. **예산**은 파일럿 provenance 의 읽은 설정 사본으로 IMPACT 상태 수 비를 저절로.
- **커밋** de3d443..d59a868(13개)·push.
- **빌드** KooChainRun 만(build_capped_kcr.sh — root scope MemoryMax 14G·adj 1000, 2.35 컨테이너 가드) 08:50~08:53 BUILD_RC 0,
  최저 가용 35.8 GB. KCR ebb0c6cb(/data = SIF 소스 트리), glibc 요구 최고 2.35. KMM·KAM 은 v136 그대로(소스 변경 없음).
- **컴파일본 시험(KCR_BIN, C.UTF-8).** test_kcr_stcx_requests 88 · test_result_return 41 · test_kcr_doe_schedule 101 · test_kcr_endtime_presim 157 ·
  test_kcr_impact_conditions 105 — 모두 FAIL 0.

## 독립 적대 리뷰와 반영(11-17)
- 에이전트 리뷰(읽기 전용, /data 의 실제 KCR 런 약 190개·다른 연구 폴더 d3hsp 153개로 판정 재현). DROP·누적 DROP·VIB·THERM 정상 런의 거짓 invalid 는
  없었다. 막아야 할 것과 반영(검토 번호는 상·중·하 — 제품 코드명과 겹치지 않게):
  - **상1** 회전 초기 속도(충격 조건 DOE 의 RigidAngularVelocity·낙하 InitialAngularVelocity·IVG OMEGA·*INITIAL_VELOCITY VXR..)가 있으면 첫 KE 에
    ½ωᵀIω 가 더해져 ½mv² 비교가 +60 % → 재시도 없는 invalid 였다 → 회전·집중 질량(중5)이면 비교를 건너뛰고 첫 KE 0 판정만 남긴다.
  - **상2** 지킴이 중복 제출 — 러너 separate_job deep 잡(deep_report_jobs.txt)을 보지 않음·도는 deep 을 report_failed 로 봄·squeue 실패를 '대기 잡 없음'
    으로 봄 → 러너 잡 기록과 최근 recent_minutes(30) 안에 바뀐 리포트·deep 로그는 건너뛰고, squeue 를 못 읽으면 그 패스는 아무것도 내지 않는다.
  - **상3** 지킴이·postprocess 가 옛 판 deep_report.sh(관문 없는 rm·빈 리포트 성공)를 그대로 돌림 → 표지(빈 리포트 검사 줄)가 없으면 지금 설정으로 다시 만든다
    (postprocess 는 지금 설정이 삭제 끔이어도).
  - 중1 submit 예산의 동시 수가 argparse 기본 2×4 → 모르면 런 수 전부(sequential 은 --nodes). 중2 스크래치 rc 3 이면 노드 임시 폴더가 남음 → 0·3 이면 정리.
    중3 지킴이 배열이 MaxArraySize 를 넘음 → max_array(1000)로 나눔. 중4 64 MB 넘는 JSON 은 머리·끝만 봐서 0.4~0.5 % 잘림을 놓침 → 삭제 관문은 크기와
    상관없이 끝까지 읽는다(관문 명령이 없는 DWI 틀도 SIF 안 python 으로). 중5 집중 질량(*ELEMENT_MASS) → ½mv² 비교 건너뜀.
  - 하1 E 없는 세 자리 지수('4.17160+258') 읽기. 하2 "health": true 같은 비객체 → 경고 뒤 무시(러너 생성자가 죽어 모든 DOE rc 1 이던 것).
    하3 KCR_HEALTH=off|record|on·health.enforce(기록만) — 대역 솔버 e2e. 하4 모델·include sha 는 캠페인 캐시, binout 시간 제한 기본 300 s.
    하5 health.json·provenance·manifest 에 NaN 을 쓰지 않음(allow_nan=False), 시간 초과면 solver_exit_code None, 없는·빈 파일럿은 오류,
    status 는 예외에 죽지 않음, health 캠페인 판정은 index 모드, *Mode 에 PART_TRANSLATE 가 앞에 와도 주 모드.
  - 동작 변경(버그 아님, 사용자 결정대로): DTMIN·ENDMAS·ENDCYC 로 목표 시각 전에 끝난 런은 이제 재시도 없는 invalid.
- 반영 뒤: 새 시험 107(리뷰 판정 17) 모두 통과, 리뷰 반영 전 트리(d59a868)는 리뷰 판정 14 FAIL·2 OK(예전 동작을 지키는 판정·모듈 단위). KCR·Runner 를
  쓰는 기존 시험 21개 모두 rc 0, cli_help ALL PASS.
