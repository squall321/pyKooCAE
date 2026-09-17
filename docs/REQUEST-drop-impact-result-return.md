# 요청 — 낙하·부분충격 리포트가 클러스터에서 **저절로** 돌아오려면 pyKooCAE 에서 막히는 것들

**보내는 곳** HWAX Portal · 절차(procedures) 기능
**날짜** 2026-09-17
**기준 커밋** pyKooCAE `bf32432` · KooD3plotReader `1f17ea1` · KooSlurm(KooSlurmInstallAutomationRefactory) `351c7787` — 행 번호는 이 기준, 리포 이름 없는 경로는 pyKooCAE.
**한 줄** 부분충격은 지금 리포트가 **아예 안 생기고**, 초속이 **두 번 더해지며**, 후처리 실패가 **성공과 같은 모양**입니다.
**성격** 결함 수정 요청입니다. 고치는 방법은 이 리포가 정합니다(§4).

---

## 1. 왜 지금 쓰나

포털에서 **해석을 걸어 두면 결과가 stcx 클러스터에서 DynaForge 로 저절로 돌아오게** 하기로 정했습니다
(HWAXPortal `docs/procedures/context-notes.md` W-93). DynaForge 후처리 연산이 클러스터에 후처리 잡을 걸고 **리포트 HTML 만**
받습니다(d3plot 37~50GB 는 나르지 않음). 길은 대시보드 REST 기본, ssh 대체입니다. 그 연산은 **리포트가 실제로 생긴다**와
**실패가 실패로 보인다**를 믿어야 하는데 둘 다 KooChainRun 안에 있습니다. 대시보드 파일 REST 인증·귀환 매니페스트는 KooSlurm 에,
후처리 예약 연산은 KooRemapper 에 따로 요청합니다. 조사 중 결과 **해석**에 걸리는 결함(초속 이중 합산)이 나와 함께 올립니다.

## 2. 확인한 현재 상태

| | 지금 |
|---|---|
| 부분충격(`smarttwin_submit`) | `impact_report.sbatch` 는 생기는데 그 잡이 부를 `impact_report.sh` 가 없다 → 리포트 0건(A) |
| 부분충격 초속 | 워크플로와 KMM 이 각자 √(2gh) 를 만든다 → h>100 이면 2배(B) |
| 후처리 실패 | `KooChainRun postprocess` 가 실패해도 종료코드 0(C) |
| 전각도 리포트 | `sphere_report.html` 만 생기고 JSON 은 없다(D) |
| 드라이버 후처리 | `--all` 이 Run 전부에 deep 을 드라이버 자원 안에서 돈다. 부분충격 `output_dir` 은 `"output"` 일 때만 맞는다(E) |
| 단위 | 단위계 키 없음, 기본 tonne-mm-s-MPa. 예제·폴백에 SI 값이 남아 있다(F) |

## 3. 부탁 (우선순위 순)

### A. [1순위] 부분충격 prepare 가 `impact_report.sh` 를 만들어 주십시오

**근거**
- `impact_report.sh` 를 쓰는 곳은 누적 경로 하나입니다(`Runner/CumulativeDesigner.py:1037-1051`). 부분충격은 prepare 가 곧장
  갈라지고(`KooChainRun:588-592`), `Runner/DropWeightImpactWorkflow.py:22-133` 은 `.sh` 없이 `postprocess` 설정만 넘깁니다(123행).
- 그런데 submit 은 그 `.sh` 를 부르는 의존 잡을 겁니다(`KooChainRun:1354-1357` → `1394-1400`·`1443-1446`, 본문
  `Runner/PostprocessShellGenerator.py:600`). 드라이버의 `postprocess --all` 도 `.sh` 가 없으면 두 줄 찍고 넘어갑니다(`KooChainRun:3297-3301`).
- dev 실물 `/data/single/<사용자>/generic_submit_e2e_871/output/` 에 `impact_report.sbatch`(afterany:872)만 있고
  `impact_report.sh`·`impact_report.html`·`impact_report.slurm.out` 은 없습니다.
- 읽는 쪽은 준비돼 있습니다 — KooD3plotReader `python/koo_impact_report/koo_impact_report/loader.py:2046-2060` 이
  `output/results/dwi_*/Run_*` 를 읽습니다(단 `test_dir/output` 고정, 1977행).

**왜** 없으면 의존 잡으로도, 드라이버 후처리로도, `KooChainRun postprocess --impact` 로 손으로 돌려도 부분충격 리포트는 안 나옵니다
(SIF 에서 `koo_impact_report` 를 직접 부르면 로더가 DWI 배치를 읽으므로 나옵니다 — `loader.py:2046-2060`).

**함께 봐 주십시오** 의존 잡 자원이 LS-DYNA 자식용 `environment.memory` 를 물려받습니다(`PostprocessShellGenerator.py:572-573`).
dev 871 sbatch 는 `--cpus-per-task=1 --mem=2G` 였고, deep 산출물이 없으면 Run 마다 unified_analyzer 를 도는데(같은 파일 340-343행,
`loader.py:1938-1939`) 2G 로 되는지는 확인하지 못했습니다.
**확인** smarttwin-partial-impact 기본 격자로 prepare → `output/impact_report.sh` 가 있고, 의존 잡 뒤 `impact_report.html`·`.json` 이 생기면 됩니다.

### B. [1순위] 부분충격 초속이 두 번 더해집니다 — 한쪽만 만들어 주십시오

**근거**
- 워크플로가 `vz=-√(2·9810·h)` 를 만들어 `Height,h` 와 **함께** 씁니다(`Runner/DropWeightImpactWorkflow.py:506-508`, 532·535행).
- 파서는 둘 다 넘깁니다 — `occProject/Generators/KooMeshModifier.py:1207-1213`(Height)·`1228-1234`(InitialVelocityZ),
  `GenerationMode`→`Mode`(1095-1097), 함수 분기(2711-2716).
- KMM 세 함수가 모두 `Vz - √(2·g·h)` 를 한 번 더 합니다. g 는 h>100 이면 9810, 아니면 9.81입니다 —
  `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py:3508-3509`(OutsideRigid*)·`3998-3999`(DampingSpring, 기본)·`4711-4712`(Part).
- 누적 부분충격 생성기는 `Height` 와 `InitialVelocityZ,0` 을 씁니다(`Runner/CumulativeScenarioRunner.py:1649-1657`). 전각도 낙하 생성기도
  같은 모양이고(`Runner/StepConfigBuilder.py:256-259`) KMM DropAttitude 가 높이로만 속도를 만듭니다(`KooDynaAdvancedModification.py:2248-2255`).
- dev 871 `dwi_0001` 실측 — step config `Height,100`·`InitialVelocityZ,-1400.71` 인데 덱의 `*INITIAL_VELOCITY_GENERATION`
  VZ 는 `-1.445e+03` 입니다(1400.71 + √(2·9.81·100) = 1445.01).

**이미 돌린 결과를 읽는 법** 맞는지 확인해 주십시오.
- h>100 이면 실제 속도 2√(2·9810·h), 의도의 **2배·에너지 4배**입니다.
- h≤100 이면 √(2·9810·h)+√(2·9.81·h), **약 1.032배·에너지 약 1.064배**입니다. 템플릿 기본 높이 100 이 여기 듭니다
  (KooSlurm `dashboard/templates/official/simulation/smarttwin-partial-impact.yaml:40`).
- 실제로 넣은 속도는 각 Run 의 `DropWeightImpactTestSet.json` `energy.speed` 에 남습니다(KMM `4256-4264`). 같은 블록의
  `equivalent_height` 는 h≤100 이면 g=9.81 로 나눠 틀립니다(4258-4259행, dev 871 값 106424.6).

**왜** 과제 간 비교는 해석 조건(높이)으로 묶습니다. 조건표의 높이와 실제 충돌 에너지가 4배 다르면 비교가 조용히 틀립니다.
**확인** h=150 한 케이스로 prepare 한 뒤 그 step_config 를 KooMeshModifier 로 돌려(덱은 run.sh 가 만든다 — `DropWeightImpactWorkflow.py:82-92`·`629-637`)
나온 `DropWeightImpactTestSet.k` 의 VZ 가 -1715.5 이면 됩니다(지금 코드로는 -3431.0).

### C. [2순위] 후처리 실패를 종료코드로 올려 주십시오

**근거**
- `cmd_postprocess` 는 deep·sphere·impact 실패를 찍기만 하고 정상 반환합니다(`KooChainRun:3272-3276`·`3292-3295`·`3310-3313`).
  `.sh` 없음도 같고(3281-3283, 3299-3301), main 은 반환값을 안 봅니다(395-396행). 명시적 종료코드 1 은 runner_config·output_dir 가 없을 때뿐입니다(3186-3188, 3198-3200 — 잡히지 않은 예외도 비영).
- `impact_report.sh` 는 SIF 에 모듈이 없으면 `exit 0` 으로 건너뜁니다(`Runner/PostprocessShellGenerator.py:393-397`).
- dev 1092 `output/sphere_report.log` 에 "0 / 2 … skip" 이 남았습니다. 코드상 postprocess 는 `✗ rc=1, log=…` 한 줄만 찍고 정상 반환합니다
  (`KooChainRun:3294-3295`, `sphere_report.sh` 의 exit 1 은 `PostprocessShellGenerator.py:316-321`). 같은 skip 이 의존 잡 `sphere_report.slurm.out` 에도 남았습니다.
  (템플릿 post_exec 의 `|| echo WARN` 은 KooSlurm 에 따로 올립니다.)

**왜** KooSlurm 에 귀환 매니페스트(`output/return_manifest.json` — 리포트별 있음/없음·이유·후처리 rc)를 요청합니다. rc 가 늘 0 이면
이유 칸이 비고 "리포트 없음" 이 "성공" 과 같아집니다. 가능하면 **건너뜀과 실패를 구분**해 주십시오(`.sh` 없음·산출 0·구버전 SIF·실행 실패).
**확인** `impact_report.sh` 가 없는 runner_config 로 `KooChainRun postprocess … --impact` → 종료코드가 0 이 아니면 됩니다.

### D. [2순위] sphere_report 도 JSON 을 내 주십시오

**근거**
- sphere `.sh` 는 `--json` 경로만 주고 `--format` 을 안 줍니다(`Runner/PostprocessShellGenerator.py:325-330`). `koo_sphere_report` 는
  `--format` 기본이 `html terminal` 이고 json 은 거기 있을 때만 씁니다(KooD3plotReader `python/koo_sphere_report/koo_sphere_report/__main__.py:43-47`·`145-153`).
  impact 는 이미 `--format html json` 입니다(403행).
- dev `/data/single/<사용자>/verify_drop2_828/output/` 에 `sphere_report.html`(9.8MB)만 있고 JSON 은 없습니다.

**이미 되는 길** `postprocess.sphere_extra_args: ["--format","html","json","terminal"]` 이면 지금도 나옵니다(`PostprocessShellGenerator.py:259-261`).
다만 템플릿은 `{"enabled": true}` 만 주입해(KooSlurm `smarttwin-fullangle-drop.yaml:136`) 기본 잡엔 안 붙습니다. 기본값을 바꿀지 템플릿이 넣을지 정해 주십시오.

**왜** DynaForge 가 HTML 을 파싱하지 않고 값으로 판독·검증할 길이고, impact 와 모양이 맞습니다.
⚠ **작지는 않습니다** — dev 작업 폴더의 `Test_Postprocess_v14`(20 Run) 재생성본이 JSON 10.6MB, HTML 7.5MB 였습니다.
**확인** 전각도 잡 뒤 `output/sphere_report.json` 이 있으면 됩니다.

### E. [2순위] 드라이버 안 deep 을 줄이고, 부분충격 `output_dir` 을 따라 주십시오

**근거 — deep**
- `--all` 은 Run 전부에 deep 을 돌고(`KooChainRun:3212-3216`, `3240-3276`) 보고서가 이미 있어도 건너뛰지 않습니다. 같은 판정
  (`report/result.json`·`analysis_result.json`)을 `sphere_report.sh` 는 이미 씁니다(`PostprocessShellGenerator.py:307`).
- 드라이버 자원은 전각도 1 CPU·4G, 부분충격 2 CPU·4G 이고(KooSlurm `smarttwin-fullangle-drop.yaml:23-24`·`smarttwin-partial-impact.yaml:23-24`),
  post_exec 가 그 안에서 `postprocess --all` 을 부릅니다(각 211-212·247-250행).
- dev 1092(전각도 2각) — 자식 잡 안 deep 이 두 Run 모두 먼저 rc=3 으로 실패했고(`output/runner_doe_001.log:194-196`·`runner_doe_002.log:194-196`), 뒤이은 postprocess 의 deep 이
  두 Run 모두 `unified_analyzer failed (rc=-9)` 였습니다(`output/Run_*/deep_report.log` 4행, 23:10·23:12:04). `cmd_postprocess` 만 쓰는
  `sphere_report.log`(`KooChainRun:3286`)가 23:12:05 로 바로 뒤입니다. 드라이버 post_exec 였는지는 잡 로그를 못 봐 확인하지 못했습니다.
  ⚠ 이 사례는 **성공한 deep 의 재실행이 아니라 드라이버 자원 안의 deep** 이 죽은 것이라 건너뛰기만으로는 못 막습니다.
- **부분충격은 사정이 다릅니다** — 부분충격 run.sh 에는 deep 단계가 없어(`DropWeightImpactWorkflow.py:601-681`) 드라이버 `--all` 이 유일한
  deep 생산자입니다(`KooChainRun:3230-3233`·`3262-3264`). impact 로더는 그 산출물이 있으면 unified_analyzer 를 건너뜁니다(`loader.py:1930-1952`).
  드라이버 deep 을 그냥 없애면 1 CPU·2G 의존 잡이 Run 마다 unified_analyzer 를 떠안습니다.
- **이미 되는 길** — 전각도에는 자식 deep 을 별도 잡으로 빼는 설정이 있습니다(`postprocess.auto_deep_mode: separate_job` + `deep_ncpu`·`deep_memory`,
  `CumulativeScenarioRunner.py:765-767`, `PostprocessShellGenerator.py:446-496`).

**근거 — output_dir**
- 부분충격 runner_config 는 최상위 `output_dir` 을 쓰고 기본값은 `dwi_output` 입니다(`Runner/DropWeightImpactWorkflow.py:42`·116행).
  예제 9개도 전부 `dwi_*` 입니다(`Examples/drop_weight_impact/scenario*.json`).
- postprocess 와 의존 잡 제출은 `project.output_dir` → `<config 폴더>/output` 만 보고(`KooChainRun:3193-3197`·`1409-1413`), 로더도
  `test_dir/output` 고정입니다(KooD3plotReader `loader.py:1977`). 그래서 `output_dir` 가 정확히 `"output"` 일 때만 맞습니다(runner_config.json 이 scenario 와 같은 폴더일 때). 템플릿 기본
  격자가 그렇고(`smarttwin-partial-impact.yaml:98`), 템플릿 설명이 권하는 예제를 올리면 어긋납니다(같은 파일 9-10행).
**확인** `Examples/drop_weight_impact/scenario.json`(dwi_output)으로 prepare 한 뒤 postprocess 가 `dwi_output` 을 보면 됩니다.

### F. [3순위] 예제·폴백의 SI 물성을 정리해 주십시오

**근거**
- 낙하·충격 경로에 단위계 키가 없고 값을 변환 없이 씁니다(`Runner/StepConfigBuilder.py:264-266` → KMM `2062-2064`·`2094`).
  코드 기본값은 tonne-mm-s-MPa 입니다(`StepConfigBuilder.py:121-128`, `DropWeightImpactWorkflow.py:499-504`·`563-569`).
- 부분충격 예제 9개 전부 충격추 7850/2.0e11, `scenario.json` 은 바닥도 같습니다(`Examples/drop_weight_impact/scenario.json:17-24`·`49-53`).
- `Examples/HWWarrantyDropTest/Tests` 의 추적된 9개(Test_001~008·Test_009_ScratchRun_100) 전부 `density 7850`·`youngs_modulus 2e11` 입니다
  (작업 트리의 미추적 3개도 같음). dev `/data/scenario` 프리셋 5종과 `simulation_params` 가 같고, `26direction`=Test_001·`fibonacci-100`=Test_005 는
  글자 그대로 같습니다. 어느 쪽이 원본인지는 확인하지 못했습니다.
  커밋 `381ba31` 이 "사용자 production scenario.json 단위 점검" 을 미해결로 남겼습니다.
- KMM 내부 폴백이 SI 입니다 — `KooDynaAdvancedModification.py:3712`(경고)·`3717-3773`(충격추 2.07e11/7800, Damper·Wall 1e10/1000).
- 워크플로가 Damper 재질 키를 안 내서 기본 덱에 폴백이 박힙니다(dev 871 덱 `DamperMaterial 1.000e+03 1.000e+10`, 빔 요소 0개).
  `BoundaryDistance` 가 0 이 아니면(KMM 3675-3678, StressWaveVelocity 경로 3882-3887 은 워크플로가 키를 내지 않아 0) 빔 요소를 만들고(4104-4125)
  그 파트 재질이 DamperMaterial 입니다(3920-3931). 그래서 **`boundary_distance>0` 이면**(`DropWeightImpactWorkflow.py:556-557`) SI 폴백 1e3/1e10 이
  tonne-mm-s-MPa 덱에 실제로 쓰입니다.

## 4. 우리가 **안 정한 것** — 이 리포가 정해 주십시오

- **초속을 어느 쪽에서 만드나.** 워크플로가 `InitialVelocityZ,0` 을 쓰거나 KMM 이 `Height` 를 무시하거나. 누적 부분충격 생성기와 전각도 낙하 생성기는 전자 모양입니다(B).
- **단위계 키를 새로 만드나.** 만든다면 기본은 tonne-mm-s-MPa 여야 기존 덱이 안 바뀝니다. ⚠ 열하중 ICPower 가 이미 `UnitSystem` 키를 쓰고 기본값이 `SI` 입니다
  (`CumulativeScenarioRunner.py:1711·1718`, `KooMeshModifier.py:2501·2594-2595`) — 같은 이름을 낙하·충격에 다른 기본값으로 쓰면 뜻이 갈립니다.
  커밋 `381ba31` 도 "scenario.json unit_system 필드 + 자동 변환" 을 미해결로 남겼습니다.
- **impact_report 를 의존 잡으로 거나, 드라이버에서 도나.** 지금은 둘 다 합니다(`KooChainRun:1354-1357`, 템플릿 post_exec). 하나로 정하면 매니페스트가 기다릴 대상도 하나가 됩니다.
- **귀환 매니페스트를 누가 쓰나.** KooChainRun 인지 템플릿인지(KooSlurm 과 함께).

## 5. 급한가

**B 는 급합니다** — 이미 돌린 부분충격 결과의 해석이 걸려 있습니다. **A** 는 부분충격 자동 귀환의 전제라 그다음입니다.
C·D·E 는 전각도 자동 귀환의 품질이고, F 는 늦어도 됩니다(포털 제출 절차가 물성을 늘 명시하게 이미 막아 둠, W-91).

---

### 참고 — 이 요청이 나온 경위

포털 W-92 에서 네 리포(KooSlurm·pyKooCAE·KooRemapper·SmartTwinMCP)를 반박 검증까지 돌려 "결과가 어디까지 저절로 오나" 를 지도로 만들었고 W-93 에서
귀환 모양이 정해졌습니다. 그 조사 주장을 **쓰기 직전에 현재 코드와 dev 실물로 다시 읽어** 고쳤습니다. 틀린 데나 **이미 되는 길이 있으면 알려 주십시오** — 그 길을 쓰고 부탁을 접겠습니다.
