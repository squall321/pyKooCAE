<!-- 강체 낙하 사전 해석으로 각도별 종료 시간(ENDTIM)을 정하는 기능(RIGID_DROP_ENDTIME) — 계획 -->
# 계획 — 강체 낙하 사전 해석 → 각도별 종료 시간 (2026-11-07, v132)

## 배경
전각도 낙하 해석은 지금 모든 각도에 같은 `simulation_params.tFinal` 하나를 쓴다. 각도마다 2차 충격(슬랩다운)이 끝나는 시점은 2 ms~110 ms 로 크게 다르다(`/home/koopark/kooOmniDropAnalyzer/fullangle_mbd` 프로토타입, 피보나치 1000방향, 리포트 https://claude.ai/artifact/TDoKQjGP4kk2f9UsqsDNJP).
- 짧게 잡으면 2차 충격을 놓친다.
- 길게 잡으면 d3plot 이 각도당 18 GB 씩 쌓인다.

사용자 요청(11-07).
- "낙하시뮬레이션 파일 있으면 오브젝트 파일과 외곽형상 그리고 I A등을 도출해서 이차충격 시뮬레이션을 돌려서 각도별 전각도 낙하 해석 파이널 타겟타임을 결정하는 시뮬을 하게끔"
- "kmm쪽에도 여기의 결과를 입력으로 받아가서 각도별 엔드타임 설정을 달리 가져가게끔"

## 사용자 결정 (11-07, 질문 넷)
1. **구조**는 KMM 새 모드에 KCR 자동 연결을 붙인다.
   - KMM 이 맡는 것: 덱 읽기·질량특성·OBJ·사전 해석·표 생성.
   - KCR 이 맡는 것: scenario 옵션이 켜지면 prepare 때 이 모드를 불러 DOE 에 표를 붙인다.
2. **이름**은 아래처럼 정했다.

   | 대상 | 이름 |
   |---|---|
   | 모드 | `RIGID_DROP_ENDTIME` |
   | 블록 | `**RigidDropEndtime` |
   | DROP_ATTITUDE 표 키 | `EndTimeTable` |
   | scenario 키 | `simulation_params.endtime_presim` |
   | 산출 | `<base>_endtime.csv` |
3. **물리 기본값**은 리포트처럼 **중력을 켠다**. 재착지(되튀어 다시 떨어짐)는 2차 충격에서 빼는 프로토타입 규칙을 그대로 쓴다.
   - KMM DROP_ATTITUDE 덱에는 중력이 없다(초기 속도만). 이 차이는 사용자가 알고 고른 것이다.
   - `PresimGravity,0` 으로 끌 수 있다.
4. **배포 범위**는 SIF v132·tar·Drive/메일까지다. 헤드 /opt 교체와 노드 배포는 결과를 보고 따로 묻는다.

해석: "I A" 는 관성(I)과 면적(A)으로 본다. 그래서 질량·무게중심·관성 텐서·주축·바운딩 박스·외곽면 면적·볼록 껍질 부피와 면적을 JSON 으로 낸다.

## 구조
```
[KMM RIGID_DROP_ENDTIME]  덱(.k) ──KMM 리더──▶ KooRigidBodyProperties ──▶ <base>_rigidbody.json, <base>_surface.obj, <base>_hull.obj
                                                       │ (SI 질량·무게중심·관성·껍질)
                                                       ▼
                                          KooRigidDropPresim (PyBullet) ──▶ <base>_endtime.csv
[KMM DROP_ATTITUDE]  EndTimeTable,<csv> ──KooEndTimeTable.lookup──▶ 각도마다 ENDTIM·NPLTC (단일·Fast DOE 모두)
[KCR prepare]  simulation_params.endtime_presim.enabled ──▶ KMM RIGID_DROP_ENDTIME 실행(템플릿마다) ──▶ 모든 DROP 스텝 설정에 EndTimeTable 줄
```

새 파일은 아래와 같고, 모두 `occProject/Generators/KooCAEManager/` 아래에 둔다. 공유 코드는 고치지 않는다.

| 파일 | 내용 |
|---|---|
| `KooEndTimeTable.py` | 표 형식 계약: 쓰기·읽기·각도 찾기·낙하 방향 규약. numpy 만 쓴다 |
| `KooRigidBodyProperties.py` | 질량특성·외곽면·볼록 껍질·OBJ/JSON |
| `KooRigidDropPresim.py` | PyBullet 사전 해석(프로토타입 `fullangle_drop_mbd.py` 이식). pybullet 은 함수 안에서 늦게 import 한다 |

고치는 파일은 아래와 같다. 모두 더하기만 하고 키가 없으면 출력이 바이트까지 같다.

| 파일 | 고치는 곳 |
|---|---|
| `KooMeshModifier.py` | 모드 등록 4곳, DROP_ATTITUDE 블록의 `EndTimeTable` 키 |
| `KooDynaAdvancedModification.py` | DropAttitude·Fast DOE 의 각도별 ENDTIM |
| `KooCLIHelp/kmm_catalog.py` | 새 모드 항목, DROP_ATTITUDE 키 |
| Runner | `CumulativeDesigner`·`StepConfigBuilder`·`CumulativeScenarioRunner`·`LargeScaleDOEManager`·`KooChainRun`(배치)·`cli_help_kcr.py` |

## 계약

### 1. KMM 옵션 파일 — 새 모드
```
*Inputfile
MinimumModel.k
*Mode
RIGID_DROP_ENDTIME,1
**RigidDropEndtime,1
Height,1500
Fibonacci,100
**EndRigidDropEndtime
*End
```
키는 대소문자를 가리지 않고 **키 이름 전체가 같을 때만** 맞춘다(부분 문자열 금지).

| 키 | 값 | 기본값 |
|---|---|---|
| `Height` | 낙하 높이, 덱 길이 단위 | 필수 |
| `AngleFile` | csv `name,roll,pitch,yaw`(도) | 셋 중 하나 필수 |
| `Fibonacci` | N — 실제 낙하 방향 균일 N 점, 이름 P0001… | 〃 |
| `Angle` | `<name>,<roll>,<pitch>,<yaw>` (여러 줄) | 〃 |
| `Restitution` | e 목록 | 0.1,0.3,0.5 |
| `Friction` | μ | 0.5 |
| `PresimGravity` | 1 켬 / 0 끔 | 1 |
| `MarginMs` | 여유(ms) | 1.0 |
| `ExcludePart` | PID 목록(바닥판 등) | 없음(+ 모든 절점이 SPC 고정인 파트는 자동 제외, 로그에 이유) |
| `Units` | `mm-t-s`·`mm-kg-ms`·`mm-g-ms`·`m-kg-s` | 재질 밀도 중앙값으로 자동, 판정 불가면 rc 1 |
| `Workers` | 프로세스 수 | min(8, CPU) |
| `PresimDt` | PyBullet 시간 간격(s) | 1e-5 |
| `PresimTMax` | 한 경우 최대 시뮬 시간(s) | 1.0 |

산출(작업 폴더, base = 입력 덱 이름에서 확장자를 뺀 것)은 `<base>_rigidbody.json`, `<base>_surface.obj`, `<base>_hull.obj`, `<base>_endtime.csv` 다. 기본 .k 는 쓰지 않는다(`_skip_default_write`, VIBRATION_LOAD 와 같다).

### 2. 표 `<base>_endtime.csv` (정본 = `KooEndTimeTable.py`)
- 첫 줄들은 `# key=value` 메타다(format, deck, units, time_unit, height, restitution, friction, gravity, margin_ms).
- 그다음 머리 줄 하나와 각도마다 한 줄이 온다.

| 칸 | 뜻 |
|---|---|
| `name,roll,pitch,yaw` | 입력 각도(도) |
| `dx,dy,dz` | 덱 좌표계 낙하 방향 = Rz(-yaw)·Ry(-pitch)·Rx(-roll)·(0,0,-1) — KMM DropAttitude 규약 |
| `class` | e 들 가운데 `slapdown` 이 하나라도 있으면 slapdown, 아니면 `rebound`/`none` |
| `t1_end_ms,t2_start_ms,t2_end_ms` | 가장 긴 tFinal 을 낸 e 의 값(2차 충격 없으면 빈칸) |
| `tfinal_ms` | 각 e 마다 (slapdown 이면 t2_end, 아니면 t1_end) + 여유. e 들 가운데 최대값이다 |
| `endtim` | `tfinal_ms` 를 덱 시간 단위로 바꾸고 0.1 ms 단위로 올림한 값 — **KMM 이 그대로 ENDTIM 에 넣는다** |
| `governing_e` | 최대를 낸 e |
| `class_e<e>`, `t1_end_ms_e<e>`, `t2_start_ms_e<e>`, `t2_end_ms_e<e>` | e 별 세부 |

### 3. DROP_ATTITUDE 의 `EndTimeTable,<csv>`
- 블록 키 검사 **맨 앞**에서 정확히 일치할 때만 받는다(표 경로에 tfinal·height 같은 글자가 있어도 기존 키에 안 걸리게).
- 경로는 옵션을 읽을 때 절대 경로로 바꾼다(KMM 은 덱을 읽으며 chdir 한다).
- 각도마다 표에서 낙하 방향 사이 각이 0.01° 이하인 줄을 찾는다.
  - 여럿이면 `endtim` 최대를 쓴다.
  - 없으면 **rc 1 로 멈춘다**(조용한 기본값 금지).
- 찾은 값이 그 각도의 tFinal 이 된다. ENDTIM 과 tFinal 에서 나오는 값(NPLTC = int(tFinal/dt) 등)이 각도마다 바뀐다. dt 가 없으면 rc 1 이다.
- 키가 없으면 출력은 지금과 바이트까지 같다.

### 4. scenario `simulation_params.endtime_presim`
```json
"endtime_presim": {"enabled": true, "table": null, "restitution": [0.1, 0.3, 0.5],
                   "friction": 0.5, "gravity": true, "margin_ms": 1.0, "exclude_parts": [], "workers": 8}
```
- `enabled` 가 없거나 false 이면 runner_config·스텝 설정이 지금과 바이트까지 같다.
- 켜면 prepare 가 DROP 스텝이 쓰는 템플릿마다 고유 각도를 모아 `<output_dir>/endtime_presim/<i>/angles.csv` 를 쓴다. 그다음 KMM `RIGID_DROP_ENDTIME` 을 러너와 같은 방식(apptainer 감싸기 포함)으로 돌린다.
- 결과로 runner_config 에 `scenario.endtime_tables` 와 `scenario.doe_endtim`({doe: {step: endtim}}, 보기용)을 남긴다. 모든 DROP 스텝 설정(누적·대규모·배치)에는 `EndTimeTable,<절대경로>` 줄을 넣는다.
- `table` 을 주면 사전 해석을 건너뛰고 그 표를 쓴다.
- KMM 이 실패하거나 표에 빠진 각도가 있으면 prepare 를 멈춘다.

## 검증 기준(값으로 잰다)
- **질량특성, MinimumModel.k**: 총질량 180.318 g, 파트별 질량·무게중심·관성은 d3hsp(`/data/koopark/Test_Postprocess_v14/output/Run_20260522_132307_0d0978/Output/d3hsp`)와 0.1% 안이어야 한다.
- **질량특성, SimpleDrop**: 바닥 자동 제외, 219.7 g, 관성 95.6/396.1/489.4 kg·mm²(Radioss 시작 출력에서 합친 값). 표준 위치는 `/home/koopark/claude/KooOpenRadioss/DynaExamples/SimpleDrop/simple_drop/case01_simple.k`.
- **질량특성, DropSet.k 바닥판 파트 23**(SI 밀도): 자동 제외 뒤 MinimumModel 과 같은 값이어야 한다.
- **사전 해석**: 150×75×7.5 mm·200 g 상자를 껍질(꼭짓점 8개)로 넣은 결과가 프로토타입 GEOM_BOX 결과와 맞아야 한다(분류 일치율·t2 차이를 잰다).
  - 평판 반발계수가 입력값과 맞아야 한다.
  - dt 1e-5 와 1e-6 결과가 같아야 한다.
  - 45° 짧은 모서리, μ 0.5 에서 약 17 ms 가 나와야 한다.
  - 정확한 6면은 2차 충격이 없어야 한다.
- **KMM 표 소비**: 키가 없을 때 MinimumModel 단일·Fast DOE 출력이 바이트까지 같아야 한다.
  - 표 값을 모두 tFinal 과 같게 주면 바이트까지 같아야 한다.
  - 값을 달리 주면 ENDTIM·NPLTC 줄만 달라야 한다.
- **KCR**: 옵션이 없을 때 runner_config·스텝 설정이 바이트까지 같아야 한다. 켜면 세 경로 모두 EndTimeTable 줄이 들어가야 한다.
- **아는 불량 먼저**: 새 판정은 v131 바이너리(헤드 /opt)로 먼저 FAIL 하는지 본다.

## 단계
1. 계약 파일 `KooEndTimeTable.py` 를 쓴다(직접).
2. 병렬 구현(서브에이전트, 파일이 겹치지 않게)한다.
   - A 질량특성
   - B 사전 해석
   - C KMM 표 소비
   - D KCR 연결
3. 모드 연결(E)을 한다. A·B·C 가 끝난 뒤 KooMeshModifier 등록·카탈로그·통합 시험을 한다.
4. 적대 리뷰(물리·KMM 회귀·KCR)를 하고 고친다. 전체 시험 묶음을 돌린다.
5. 빌드를 한다.
   - `build_without_automatedmodeller.sh --clean` 을 캡 scope 래퍼로 돌린다(약 53분, 무거운 작업 하나만). pybullet 이 dist 에 들었는지 확인한다.
6. 컴파일본 e2e 를 `/data/koopark/Test_E2E_v132` 에서 돌린다(v131 아는 불량 먼저).
7. SIF v132 를 굽는다.
   - 굽기 전에 헤드·compute-node-images sha 와 마지막 tar 번호를 확인하고 kooremapper-fd 에 알린다.
   - `sudo HOME=/home/koopark bash BuildSmartTwinPreprocessor.sh` 로 굽는다.
   - SIF e2e 를 돌린다.
8. 마무리한다.
   - 커밋·푸시(pathspec)
   - smarttwinmcp 에 알림(새 kmm 모드·키·scenario 키)
   - 메모리·문서 정리
   - 헤드 /opt 교체 여부를 사용자에게 묻는다

## 위험
- **덱 리더 차이**: `*PART_INERTIA` 파트의 요소는 리더가 버린다(rc 3). 질량은 원문 TM 으로 더하고 경고한다. 리더는 고치지 않는다.
- **밀도 0 재질**: 해석 안 되는 MAT 는 `GetRho()` 가 0 이다. 원문 카드 1 의 RO 로 대신하고, 그래도 0 이면 경고한다.
- **볼록 껍질 여유(collision margin)**: PyBullet 껍질은 여유만큼 부푼다. changeDynamics 로 줄이고, 상자로 GEOM_BOX 와 대조해 잰다.
- **중력 켬의 분류 위험**: 회전으로 온 2차 충격인데 무게중심이 1 mm 넘게 떠 있으면 'rebound' 로 분류돼 tFinal 이 짧아질 수 있다. 상자 1000방향에서 몇 건인지 잰다(중력 끈 재실행과 비교). 많으면 사용자에게 알린다.
- **Nuitka + pybullet**: 102 MB 확장 모듈이 dist 에 들어가야 한다. 시작할 때 stdout 에 빌드 시각을 찍는다(KMM 로그에만 남는다).
- **SIF LD_LIBRARY_PATH**: KMM lib 이 먼저라 같은 KMM 안이면 문제없다.
- **시간 상한**: sbatch `--time`·`timeout_per_step_seconds` 는 그대로다(짧아지기만 하니 안전).
- **DR drterm**: 기본값이 tFinal 이다. 표는 KMM 안에서만 쓰므로 drterm 은 전역 tFinal 그대로다.
- **누적 2스텝 이후**: 변형된 dti.k 에서 시작하지만 사전 해석은 원래 강체 형상이다(근사, 문서에 적는다).
- **다른 세션**: pykoocae-53 이 Post v45 빌드 여부를 사용자에게 묻고 있다. 무거운 빌드는 겹치지 않는다. KooRemapper 세션은 굽기 앞뒤로 알린다.
