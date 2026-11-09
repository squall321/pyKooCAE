<!-- KMM 누적 체인 결함 묶음 — 결정·근거 노트 -->
# 결정 노트 — KMM 누적 체인 결함 묶음 (2026-11-08)

## 결정
- **사용자(11-08).** v131 뒤 남은 일 가운데 「이어서 하는 해석의 결함 고치기」 를 먼저 하기로 했다(계산 노드 갱신은 나중).
- **사용자(11-08) 결정 셋.** 범위는 이어서 하는 해석에 닿는 것만(무관한 작은 결함은 다음으로). 시편을 잘라 낸 충격(BoundaryDistance≠0)을 이어서 하려 하면 멈추고 알린다(rc 1). 검증 뒤 배포까지(빌드·SIF·tar·메일·헤드 교체, 노드는 VM 을 켤 때 따로 묻는다).

## 조사(코드 읽기, 11-08)
- **C1.** `KooDynaKeyword.RigidWallPlanarMovingForcesID.getRigidWallPlanarMovingForcesID()` 가 카드 다섯 장(ID·1·2·MOVING·FORCES)을 돌려주면서
  이름표를 `*RIGIDWALL_PLANAR_MOVING_FORCES` 로 붙인다 — 받는 쪽이 네 장짜리로 읽어 ID 카드를 첫 카드로 본다(v131 리뷰 R7 이 찾음).
  DTI(`KooDynaAdvancedModification.DynaintoInitial`)가 받는 지우기는 *RemovePartbyName·*RemovePartbyID·*RemoveContactbyID·*RemoveDynamicRelaxation
  뿐이다(파서는 KooMeshModifier.py 의 `**dynaintoinitial` 블록). DROP 의 dynaintoinitial.txt 는 바닥판 파트와 바닥 접촉만 적는다 — 바닥이
  강체벽이면 지울 것을 하나도 적지 않는다.
- **C2.** DWI 는 받침 벽 파트(처방 운동 RIGID 셋), 충격체·앞·가운데 단(초기 속도 GENERATION), 댐퍼 빔(DamperMaterial·DamperSetion), BoundaryDistance≠0
  이면 바깥 요소를 지우고 BoundaryFixNodes 에 SPC_BottomFix 를 건다. dynaintoinitial.txt 에는 충격체 파트 하나와 DWI 파트를 가리키는 접촉만 적는다.
  `KooMeshImporter.RemovePart` 는 요소·남는 절점 세트·그 세트의 경계·접촉(MSTYP 3)·파트만 지운다 — 그 파트를 가리키는 처방 운동 RIGID·초기 속도
  GENERATION·*SET_PART 번호는 남는다.
- **C3.** IncludeWallInGeneral 이고 GENERAL 이 없으면 「AllParts_General」 파트 묶음(바닥판 포함)으로 AUTOMATIC_GENERAL 을 만든다. 다음 단계 DTI 가
  바닥판 파트를 지워도 묶음에는 그 번호가 남는다. 둘째 DROP 은 GENERAL 이 있으니 「바닥판이 기존 GENERAL 에 자동 포함」 이라고만 찍는다 — 묶음에
  새 바닥판 번호가 없어 바닥 접촉이 없다. 지워진 번호가 묶음에 남는 것은 LS-DYNA 가 덱을 거절할 수도 있다(확인 필요).
- **라이선스.** LSTC 서버 기록(/home/koopark/LSTCManager/logtest.txt)에 10-16 「License for code expired」 뒤로 허가가 없다 — 실제 해석 판정은 못 한다.
- **판 번호.** kooomnidropanalyzer-43 도 다음 판(전각도 낙하 해석 대수·순서)을 준비한다. 번호는 굽는 차례로 정해지므로 문서는 번호를 쓰지 않는다.

## 아는 불량 기준(11-08, 지금 main f3a49d9 소스)
- tests/test_cumulative_chain.py 를 고치기 전 소스로 돌려 20건 실패(/data/koopark/Test_cumchain_20261108/base.log). C1 은 _dti.k 에 깨진 벽
  (XT 1.0 = ID 값, 나머지 0)이 남고 2단계 DropSet.k 에 벽이 둘(깨진 벽 + 새 벽). C2 는 _dti.k 에 받침 벽·댐퍼 등 파트와 처방 운동 RIGID 셋이
  남고 2단계에 장치가 두 벌. C3 은 파트 묶음에 지운 바닥판 번호가 남는다. S1 은 OutsideRigidElement·Part 덱에 springback 카드가 없다. S2 는
  시편을 바꾼 충격 뒤 DTI 가 rc 0 으로 넘긴다. 접촉(C2)은 44e3b44 덕에 이미 다 지워진다. 초기 속도는 DTI 의 ClearInitial 이 지운다.
- **C3 의 실제 원인은 한 단계짜리에서도 있다.** DROP 은 ConvertGeneralToSingleSurface(기본 True)로 모델의 GENERAL 을 「모델 파트만」 SINGLE_SURFACE
  로 바꾼 뒤, IncludeWallInGeneral 갈래에서 GENERAL 이 있었다는 것만 보고 「바닥판이 기존 GENERAL 에 자동 포함」 이라고 찍는다 — 바닥판은 어느 접촉
  에도 들지 않는다. 체인은 1단계가 GENERAL 을 만들어 2단계가 이 길을 밟는다.
- **S2 와 KCR.** KCR 누적 IMPACT 는 늘 GenerationMode DampingSpring·BoundaryDistance 없음·StressWaveVelocity 없음이라 시편을 바꾸지 않는다 —
  KCR 체인에서 S2 는 생기지 않는다. 그래서 Runner 는 고치지 않고 KMM DTI 가 rc 1 로 멈춘다(손으로 짠 체인). KCR 은 drop_surface RigidWall 과
  include_wall_in_general 을 준다 — C1·C3 은 KCR 체인에서도 생긴다.
- **S2 가 막는 범위.** 충격 단계에서 멈추면 이어서 하지 않는 보통 충격까지 막힌다(DWI 는 dynaintoinitial.txt 를 늘 쓴다). 그래서 DWI 는 덱을
  그대로 만들고 dynaintoinitial.txt 에 *SpecimenModified 를 적고, 다음 단계로 넘기는 DTI 가 멈춘다. OutsideRigid*(바깥을 강체로 바꿈)도 시편을
  바꾸므로 같은 규칙(사용자 결정 「잘라 낸 시편」 의 같은 경우로 보고 보고에 적는다).
- **W1 추가로 본 것.** GEOMETRIC_FLAT_DISPLAY 리더가 카드 1 에 OFFSET 칸이 있다고 읽어(R16 카드 1 = NSID·NSIDEX·BOXID·BIRTH·DEATH) BIRTH 자리에
  DEATH(1E20)를 넣는다 — 벽이 켜지지 않는다. 평면 벽 기록기는 카드 1 의 OFFSET·BIRTH·DEATH·RWKSF 와 카드 2 의 WVEL 을 쓰지 않는다(덱 값이 기본값으로
  바뀜). KMM 이 만드는 바닥 벽(MOVING_FORCES_ID, MASS 0)은 그대로 둔다 — 매니저 판단 근거(매뉴얼·실행)가 없고 기존 낙하를 바꾸지 않기 위해서다.
  덱에서 읽은 벽만 읽은 종류·제목·값 그대로 쓴다.

## 고친 뒤 판정·발견(11-08 저녁)
- **W2 바닥 벽 자리.** v131 노트의 「단일 각도 RigidWall 은 바닥 벽을 원문 강체벽 앞에 쓴다(Fast 는 뒤)」 는 고치기 전 트리(gen_f3a49d9)에서도
  재현되지 않았다 — 사용자 벽 _ID 5 덱에서 단일·Fast 모두 바닥 벽이 뒤다. 회귀 시험(W2 DROP single·fast)으로만 남긴다. 실제 W2 결함은 종류가
  섞인 덱의 차례(종류별로 읽음)였고, 읽기가 lines_with_asterisk 에서 강체벽 덱 차례(dynaKeywordMan.rigidwall_order)를 남겨 그 차례로 만든다.
- **아는 불량 트리.** /data/koopark/Test_cumchain_20261108/gen_f3a49d9(고치기 전 main 의 occProject/Generators) — KMM_GEN 으로 같은 시험을
  돌린다. W1 다섯·W2 차례·C3 셋이 그 트리에서 실패한다(새 판정은 모두 고치기 전 판에서 실패 확인).
- **W1 의 바이트 변화.** 덱에서 읽은 벽은 읽은 종류·제목·값 그대로 나간다. KMM 이 만드는 바닥 벽(MOVING_FORCES_ID)도 이제 카드 1 의
  OFFSET·BIRTH·DEATH·RWKSF 와 카드 2 의 WVEL 을 쓰고 실수는 _real10 이다 — DROP 의 DropContact RW_BIRTH·RW_DEATH·RWKSF 를 처음으로 출력에 싣는다.

## 회귀(11-08 22시)
- tests/ 60개를 /data/koopark/Test_cumchain_20261108/run_suite.sh 로 하나씩. venv312 에 pytest 가 없어 __main__ 없는 9개는 venv312 python 으로 스크립트처럼
  (test_drop_attitude_angles 만 진짜 pytest — /usr/bin/python3 -m pytest 30 passed). 모두 통과.
- test_v131_io 가 묶음 안에서 rc 137 로 죽었다 — 홀로 다시 돌리니 31 OK(37 s, 최대 591 MB). 같은 무렵(22:19:57) 시스템 가용이 45 GB 에서 몇 초 만에 3 GB 로 떨어져 earlyoom 이 kube-controller·coredns·NewsKoo 서비스들과 dashboard_backend·smarttwin-mcp·cae_backend 를 죽였다(systemd 가 다시 띄움). 빌드 scope 는 없었고 직전에 NewsKoo analyzer 인스턴스가 새로 떴다 — 원인은 확정 못 함(이 묶음의 시험 아님).
- test_v131_review 의 R6·R7 강체벽 읽기는 「KMM 이 늘 MOVING_FORCES_ID 로 쓴다」 를 가정했다 — W1 뒤 읽은 종류 그대로라 종류마다 ID 카드 유무로 읽게 고쳤다(판정 뜻은 그대로). R7·R8 의 DWI→DTI 는 BoundaryDistance 0.6(OutsideRigidElement 강체화)이라 S2 로 멈췄다 — 시편을 바꾸지 않게 BoundaryDistance 를 뺐다(8405cd0).
- e2e(/data/koopark/Test_E2E_v133/e2e_rde.sh source, 케이스 b·c): source 모드는 다 통과하면 GOLDEN 에 기준을 쓴다 — 그쪽 기준을 덮지 않게 GOLDEN 을 이 묶음 폴더의 사본으로 줬다. ALL PASS.
- 말뭉치 대조(/data/koopark/Test_cumchain_20261108/corpus_run.py, 고치기 전 트리 gen_f3a49d9 ↔ 지금 소스, TRANSFORM 0): 강체벽 없는 실제 덱 15개
  (Tests MinimumModel·배터리 병합 덱)는 출력이 바이트 같다. 강체벽 덱 10개는 rc 가 고치기 전·후 같고, 출력이 있는 4개는 강체벽 블록만 다르다(의도 —
  *RIGIDWALL_PLANAR 가 그 종류 그대로, 모든 칸·정밀도). 6개는 고치기 전·후 모두 rc 1 이다(아래 범위 밖 결함).

## 다음 판으로(이번 범위 밖 — 말뭉치에서 나온 기존 결함, 고치기 전·후 같음)
- ⚪ CLI 도움말(KooCLIHelp/kmm_catalog.py, Runner 사본과 바이트 같아야 함): DYNAIN_TO_INITIAL 에 *RemoveRigidWallbyID·*SpecimenModified 가 없고, *RemovePartbyID 설명이 지운 파트를 가리키는 처방 운동·초기 속도·파트 묶음 정리를 말하지 않는다. DROP_ATTITUDE IncludeWallInGeneral 의 rc 1 조건도. KMM 이 스스로 적는 지시어라 기능에는 영향 없음 — v135 는 빌드·굽기를 다시 하지 않으려고 그대로 냈다.
- 🔴 *INITIAL_VELOCITY 리더(KooDynaKeyword.py InitialVelocity.parse): 빈 칸(공백 10자)을 `int()` 로 읽어 ValueError — 웹 자동화 산출 taylor_A_dump.k 등.
- 🔴 *DATABASE_* 리더(KooDynaDatabase.SetDatabasefromDyna): `float(' 1.0000-06')`(Fortran 지수, 'E' 없음)에서 ValueError — taylor_A.k.
- 🔴 *LOAD_SEGMENT_SET(KooLoad.AddLoadfromDyna): 빈 AT 칸 `float('')` ValueError — KooRemapper 회귀 덱 ref.k·out.k.

## 적대 리뷰(11-08 23시)
- 에이전트 리뷰 A(체인·DTI·DWI·RemovePart·IncludeWallInGeneral)·B(강체벽 읽기·쓰기·차례·낙하 이동)를 띄웠으나 둘 다 주간 사용 한도(11-13 15시 UTC 에 풀림)로
  중간에 끝났다 — 결과 없음. 대신 리뷰 항목을 직접 점검했다(아래). 한도가 풀리면 같은 두 리뷰를 다시 돌릴 것.
- 직접 점검: ① importer RemovePart 는 DTI(*RemovePartbyID·ByName)에서만 불린다 — 지운 파트를 가리키는 카드 정리는 다른 모드에 닿지 않는다.
  ② _ApplyThermalCarryPolicy 는 파트를 만들지 않는다 — DWI 시편 파트 찍기를 그 앞에 둬도 된다. ③ lines_with_asterisk 는 '*'+키워드 대문자에서 '*' 를 뗀
  이름만 담는다 — rigidwall_order 짝짓기가 맞다. ④ _real10 은 1E20·7.85E-9·1E-6 꼴(10칸, LS-DYNA 가 읽는 Fortran 꼴)을 낸다. ⑤ Fast 여러 충격점은 충격점마다
  기준 상태로 되돌린 뒤 장치를 만들어, 쓸 때의 시편 밖 파트는 그 충격점 장치뿐이다(partsRigid 는 처음 한 번 만들어 모든 충격점에 같다).
- **IncludeWallInGeneral + RobustContact(모델에 GENERAL).** RobustContact 가 바뀐 SINGLE_SURFACE 를 세그먼트 묶음(SSTYP 0)으로 바꿔 바닥판을 넣을 곳이
  없다 — 이제 rc 1 로 멈춘다. 예전엔 같은 조합이 「자동 포함」 이라고만 찍고 바닥 접촉 없이 rc 0 이었다(알아보게 바뀐 것).
