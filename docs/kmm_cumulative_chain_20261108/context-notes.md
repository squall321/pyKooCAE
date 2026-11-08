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
