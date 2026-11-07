<!-- 강체 낙하 사전 해석 → 각도별 종료 시간(RIGID_DROP_ENDTIME, v132) — 결정·근거 노트 -->
# 결정 노트 — 강체 낙하 사전 해석 → 각도별 종료 시간 (2026-11-07, v132)

## 결정
- **사용자(11-07).** 프로토타입(`/home/koopark/kooOmniDropAnalyzer/fullangle_mbd`)을 SmartTwin 프리프로세서에 정식으로 넣으라고 했다. 흐름은 덱 → OBJ·외곽형상·I·A → 2차 충격 사전 해석 → 각도별 tFinal 이다. KMM 이 그 결과를 받아 각도별 ENDTIM 을 쓰게 하라고도 했다. SIF 로 묶는 기존 패턴을 지키고 서브에이전트를 많이 쓰라고 했다.
- 질문 넷의 답은 다음과 같다.
  - 구조: KMM 새 모드 + KCR 자동 연결.
  - 이름: RIGID_DROP_ENDTIME 계열.
  - 물리: 리포트처럼 중력을 켠다.
  - 범위: SIF v132·tar·Drive/메일까지.
- **"I A" 해석.** 관성(I)·면적(A)으로 본다. 질량특성 JSON 에 질량·무게중심·관성 텐서·주축·바운딩 박스·OBB·외곽면 면적·껍질 부피와 면적을 모두 넣는다.

## 조사에서 정한 것 (근거)
- **KMM 리더를 다시 쓴다.** 새 파서는 만들지 않는다. *PARAMETER·I10·*INCLUDE·고정폭·10절점 결함 이력이 리더에 쌓여 있다.
  - 질량·무게중심·관성 코드는 없다. VIB `_compute_part_mass_volume` 은 TETRA10·HEXA20 이 0 이고, 밀도 0 재질·요소 두께·질량 요소를 빠뜨린다. VIBRATION_LOAD 가 쓰므로 고치지 않고, 새 모듈에 새로 짠다.
- **모드 등록 함정**(부분 문자열, 앞에서 먼저 맞으면 끝).
  - 모드 이름에 `drop_attitude`·`transform`·`merge_k` 등이 들어가면 그 모드로 잡힌다. `rigid_drop_endtime` 은 어느 것과도 겹치지 않는다.
  - 블록 머리에 `*end`·`*mode`·`*step`·`*info`·`dropattitude` 가 들어가면 안 된다. `**rigiddropendtime` 은 괜찮다.
  - test_cli_help 는 `self.modeList.append("NAME")` 을 정규식으로 세어 카탈로그와 양방향 대조한다(큰따옴표, `[A-Z_]`).
- **DROP_ATTITUDE 블록은 줄 전체를 부분 문자열로 본다**(`"tfinal" in line.lower()` 등). 그래서 `EndTimeTable` 은 블록 검사 맨 앞에 두고, 키 이름 전체 일치로만 받는다.
- **각도별 ENDTIM 자리.**
  - 누적 경로는 DOE·스텝마다 옵션 파일을 따로 쓴다(StepConfigBuilder `tFinal,` 줄). 그래서 KMM 이 표를 받기만 하면 된다.
  - Fast DOE(한 옵션 파일에 여러 각도, KCR 배치 경로)는 ENDTIM 을 각도 반복 전에 한 번 캐시에 굽는다. 이 경로는 KMM 수정 없이는 각도별 값이 불가능하다. 사용자 요청("kmm쪽에도")이 바로 이 자리다.
- **낙하 방향 규약**: d = Rz(-yaw)·Ry(-pitch)·Rx(-roll)·(0,0,-1) 이다(ADV:2355-2371, AngleSourceParser `_physical_drop_dir`).
  - 기기는 돌리지 않고 바닥 법선과 속도를 돌린다.
  - 바닥은 등방이고 초기 회전이 없으면 결과는 d 에만 달려 있다(yaw 로 법선 둘레를 도는 것은 무관).
- **중력.**
  - DROP_ATTITUDE 덱에는 LOAD_BODY 가 없다. g 는 √(2gh) 에만 쓴다.
  - 사용자는 리포트처럼 중력 켬을 골랐다. 덱과의 차이는 알고 고른 것이다.
  - 중력을 켜면 rebound 분류(무게중심 상승 > 1 mm)가 생긴다. 회전으로 온 충격이 rebound 로 잘못 분류되는 위험은 B 가 잰다.
- **tFinal 규칙**(프로토타입 tfinal_map.py 그대로).
  - 슬랩다운: 2차 충격 묶음 끝 + 1 ms.
  - 그 밖: 1차 충돌 끝 + 1 ms.
  - 반발계수 셋 가운데 최대를 쓴다.
  - 정확한 각도에서 돌리므로 이웃 6방향 최대(conservative)는 쓰지 않는다.
- **단위.** 출력 `endtim` 은 덱 시간 단위다. mm-t-s·m-kg-s 는 s, mm-kg-ms·mm-g-ms 는 ms 다. 소비 쪽(KMM)은 단위를 모른 채 그대로 넣는다.
- **바닥판 제외.** SimpleDrop·DropSet 에는 바닥판이 파트로 들어 있다(DropSet 은 SI 밀도라 1.4e10 t). 모든 절점이 SPC 로 묶인 파트는 자동으로 빼고 이유를 남긴다. `ExcludePart` 로 직접 뺄 수도 있다.

## 진행 기록
- **11-07 계약.** `KooEndTimeTable.py` 와 시험 22/22(cf06055)를 넣었다. 낙하 방향은 ADV DropAttitude 의 RotMat 식을 그대로 옮긴 것과 임의 500 자세에서 1e-12 안으로 같다. tests/test_drop_attitude_angles.py 의 `_drop_dir` 과도 같은 식이다.
- **11-07 다른 세션과 조율.**
  - pykoocae-53 이 Post v45(KooD3plotReader 5e589fb) 굽기를 28 GB scope 로 돌리는 중이다. 끝났다고 알릴 때까지 pyKooCAE 빌드·굽기는 하지 않는다.
  - 그 세션은 우리 커밋(9e26014·cf06055, 로컬)이 함께 올라가지 않도록 pyKooCAE 커밋·push 를 멈췄다. 기능이 검증되면 이쪽에서 push 하고 알린다.
  - 헤드 /opt·compute-node-images Pre 는 v131(32260efb)이고, 마지막 tar 는 v131 이다(굽기 직전에 다시 본다).
  - Fast DROP 기록기(캐시 상태·되돌리기·차분 기록기)의 기존 결함과 고친 이력은 docs/kmm_remaining_defects_20261104/context-notes.md 에 있다(cdbbd66 RigidWall 등). C 에 전달했다.
- **11-07 A 질량특성(4ce5fd8).**
  - **SPC 제외 규칙**은 "모든 절점 고정" 이 아니라 "병진이 묶인 절점이 하나라도 있으면" 이다. DropSet 바닥판은 2883 절점 가운데 961 만 묶여 앞의 규칙으로는 빠지지 않는다. `*BOUNDARY_SPC_SET` 은 리더가 첫 줄만 남겨 원문 블록에서 읽는다.
  - **관성**은 연속체 정확값이다. d3hsp·Radioss 는 절점 집중 질량으로 재서, 큰 파트는 0.35% 안이고 한 요소 두께 칩은 크게 다르다. 집중 질량으로 다시 셈하면 Radioss 와 1e-6, d3hsp 와 3e-4(출력 4자리 한계)로 맞는다. 그러니 질량·형상은 정확하고 남은 차이는 솔버의 집중 방식이다.
  - **TETRA10** 은 중간 절점으로 8 개 사면체로 나눈다. HEXA8·PENTA6·TSHELL8 은 3×3×3 가우스 적분이다(겹친 절점 쐐기·피라미드 정확).
  - **d3hsp 기준값**은 DropSet 좌표(MinimumModel 을 (−35.5, −73.5, −4.5) 옮긴 것)다.
- **11-07 B 사전 해석(fdecb6d).**
  - **볼록 껍질 여유**: GEOM_MESH 에 1 mm 여유가 붙는다. `changeDynamics(collisionMargin=0)` 으로 형상 그대로 만든다(첫 접촉 0.110 ms 가 GEOM_BOX 와 같다).
  - **속도 상한**: Bullet btMultiBody 는 기저 속도 성분을 ±100 rad/s 로 자른다(주어진 관성이 무시된다). `maxJointVelocity=1e6` 으로 풀었다.
    - 상자 1000 각도의 3.6% 에서 tFinal 이 −1.41~+0.42 ms 움직였다(긴 모서리 계열).
    - 45° 짧은 모서리는 그대로다.
    - 상한을 되돌리면 프로토타입과 비트까지 같다.
  - **중력 실측**(상자 1000 각도): 중력 켬 표는 끔 덱보다 228 각도에서 1 ms 넘게, 42 각도에서 20 ms 넘게 짧았다. 가장 나쁜 것은 P0675(천천히 넘어짐 40 대 195 ms)다. 중력 켬일 때 '재착지' 가운데 25 건은 회전으로 온 충격이었다(강한 것 3).
  - **사용자 결정 11-07**: 종료 시간 표는 중력 끔(재접촉 모두 셈), 충격 조건은 중력 켬이다.
  - **충돌 직전 상태**: impact_rows·simulate_from_state 로 낸다. 2차 충돌 상태에서 다시 시작하면 276/276 이 같다. 0.05 mm 틈을 두면 98.6% 가 5% 안이다. FEM 재시작은 틈을 0.05 mm 이하로 둔다.
  - **성능**: 2만 각도 × e 3 개에 4.8분, RSS 572 MB 다.
- **11-07 C 표 소비(b58e359).**
  - 블록 맨 앞에서 키 이름 전체가 같을 때만 받고 `continue` 한다. 경로는 작업 폴더 기준 절대 경로로 바꾼다.
  - 덱을 쓰기 전에 모든 각도를 찾는다. 값이 바뀌는 각도마다 기존 SetControlandDatabaseExplicit 를 다시 부른다.
  - Fast 는 캐시 판의 CONTROL·DATABASE 글을 바꾼다(한 곳만 맞아야 하고, 아니면 rc 1).
  - 다른 값이면 ENDTIM·D3PLOT/INTFOR NPLTC 세 줄만 달라진다. Fast 각도 k 는 단일 실행(tFinal=endtim_k)과 같다.
  - DR Term 기본값은 옵션 tFinal 그대로다. 단위는 확인하지 않는다(F 에서 time_unit 확인을 더한다).
- **11-07 D KCR(9980e10).**
  - `*Inputfile` 은 템플릿 절대 경로다(복사하면 상대 *INCLUDE 를 잃는다). KMM 두 번째 인자로 작업 폴더를 주므로 **산출은 curDir 에 써야 한다**(E 계약).
  - 러너의 cleanup_after_exec(pkill squashfuse)는 부르지 않는다. 헤드에서 남의 컨테이너를 죽일 수 있다.
  - SIF 를 쓰면 apptainer_tmpdir 가 있어야 한다(기본 /opt/tmp 는 헤드에 없음).
- **11-07 InitialAngularVelocity 확인.** R16 Vol I 28-121 에서 `*INITIAL_VELOCITY` 의 VXR/VYR/VZR 은 절점 회전 속도다. 솔리드 기기는 돌지 않는다. 강체 회전은 `*INITIAL_VELOCITY_GENERATION` 으로 준다(Remark 1: 둘은 함께 못 쓴다). 2단계 F 에서 새 키로 넣는다.
