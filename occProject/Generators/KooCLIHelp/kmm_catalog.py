# KooMeshModifier --help 카탈로그 — 32 모드의 키·형식·검증된 사례
"""
사례의 verify 는 tests/test_cli_help.py 가 KMM ImportOption 으로 파싱해 확인한다.
  {"mode": 모드이름, "id": 모드ID, "expect": {"옵션키": 값, "A.B": 중첩값}}
사례를 고치면 시험을 돌릴 것. 파서 동작이 바뀌면 여기 설명도 같이 고칠 것.
"""

from .engine import Catalog, Example, Key, Mode, Topic

K = Key


def _opt(model, mode_lines, block, header=None):
    head = header or ""
    return f"*Inputfile\n{model}\n{head}*Mode\n{mode_lines}\n{block}\n*End"


# ── 공통 주제 ───────────────────────────────────────────────────
TOPICS = [
    Topic("format", "옵션 파일 전체 구조 (CSV 아님)", aliases=["형식", "옵션파일", "구조", "syntax"], body=[
        "KooMeshModifier 는 LS-DYNA .k 모델과 옵션 파일(.txt) 하나를 받아 수정된 .k 를 만든다.",
        "",
        "  *Inputfile                         다음 줄에 모델 파일명 (옵션 파일 폴더 기준 상대경로)",
        "  model.k",
        "  *RunDirectoryMode,True,Data/Results[,Data/Metadata]   (선택) 결과를 Run_<시각>_<해시>/ 폴더에",
        "  *Info,<모델이름>,<단계>                (선택) 메타데이터",
        "  *Description,<설명>                   (선택)",
        "  *Creator,<이름>,<메일>,<그룹>,<팀>      (선택)",
        "  *PreserveIncludes                    (선택) 다음 줄들 = 원문 그대로 둘 *INCLUDE 파일 패턴",
        "  *Mode                                실행할 모드 목록, 한 줄에 하나 `모드이름,모드ID`",
        "  DROP_ATTITUDE,1",
        "  **DropAttitude,1                     모드별 옵션 블록 — 헤더 뒤 숫자가 *Mode 의 모드ID 와 짝",
        "  Key,Value",
        "  **EndDropAttitude                    `**End` 로 시작하는 줄이면 블록 종료 (**End 만 써도 됨)",
        "  *End                                 파일 끝",
        "",
        "규칙",
        "  - 모드 이름·키는 대소문자 무관. 값은 쉼표로 구분하고 쉼표 앞뒤 공백은 넣지 않는 편이 안전하다.",
        "  - 모드ID 는 파일 안에서 모드마다 달라야 한다 (같은 ID 를 두 모드에 쓰면 뒤 블록이 앞 블록을 덮는다).",
        "  - 옵션 블록은 *Mode 목록 뒤에 둔다. *Mode 목록은 `*` 로 시작하는 줄에서 끝난다.",
        "  - 블록 안의 빈 줄: DROP_ATTITUDE·DROP_WEIGHT_IMPACT_TEST 등 대부분의 모드는 빈 줄에서 블록이 끝나",
        "    뒤 키가 조용히 무시된다. 블록 안에는 빈 줄을 넣지 말 것 (DECOMPOSE_K·MERGE_K·IMPORT_MERGE_K·",
        "    VIBRATION_LOAD·THERMAL_LOAD 만 빈 줄을 건너뛴다).",
        "  - 키는 줄에 부분 문자열이 들어있는지로 찾는 모드가 많다. 모르는 키는 에러 없이 무시되므로",
        "    오타·잘못된 키 이름은 결과 .k 에 반영되지 않는다. 반드시 이 help 의 키 이름을 그대로 쓸 것.",
        "",
        "실행",
        "  KooMeshModifier <옵션파일.txt> [작업폴더]",
        "  작업폴더를 생략하면 현재 폴더. 모델·옵션 파일은 작업폴더 기준으로 찾는다.",
        "  로그는 <옵션파일>.log 로 같은 폴더에 남는다.",
        "",
        "출력 (입력 모델은 바꾸지 않는다)",
        "  - <모델>_dump.k 는 읽은 모델을 다시 쓴 확인용 사본이다 (항상 생긴다).",
        "  - 기본 결과: <모델><접미사>.k — 모드 여러 개면 접미사가 순서대로 붙는다 (model_pt_drop.k).",
        "    접미사  ELASTIC_TO_RIGID _etor · MATERIAL_EXCHANGE _mex · PART_LOCATION_DOE _pld · ERODING_MIN_DT _emdt",
        "            RIGIDIFY_SMALL_DT _rsdt · REMESH_TETRA _remesh · PART_VALIDATION_SPLIT _pvsplit · PART_EXCHANGE _pex",
        "            REMOVE_DUPLICATE_TIED_CONTACTS _rdc · WEAK_COUPLING _wc · DEFEATURE_MESH _def · DROP_ATTITUDE _drop",
        "            TRANSLATION_DOE·TRANSFORM _trans · PART_TRANSLATE _pt · DROP_WEIGHT_IMPACT_TEST _dwit · PART_MORPHING _pm",
        "            CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM _crb · CONVERT_CNRB_TO_SOLID _cnrb2solid · WARPED_PART _warp",
        "            WARPED_TO_INITIAL_STRESS_PART _w2is · DIMENSIONAL_TOLERANCE _dt · COHESIVE_BETWEEN_CONFORMAL_MESHES _cbcm",
        "            DYNAIN_TO_INITIAL _dti · CONTACT_AUTO_DECOMPOSITION _cad · SIMULATION_AUTOMATION _sa · FEM_TO_IGA _iga",
        "            IMPORT_MERGE_K _imported",
        "  - 자체 출력: DECOMPOSE_K → OutputDir/ · MERGE_K → OutputFile · VIBRATION_LOAD → <모델>_vib.k + .json",
        "    THERMAL_LOAD → Run_<시각>/ThermalSet.k · TRANSLATION_DOE → <모델>_TranslationDOE_<i>.k + .json",
        "  - *RunDirectoryMode,True,<폴더> 면 DROP_ATTITUDE 는 <폴더>/Run_<시각>_<해시>/DropSet.k 로 쓴다.",
    ]),
    Topic("chain", "한 옵션 파일에 여러 모드를 순서대로 적용", aliases=["여러모드", "연쇄", "multi", "순서"], body=[
        "*Mode 목록 순서대로 같은 모델에 차례로 적용하고 마지막에 한 번 저장한다.",
        "예) 파트 5 를 제외하고 강체화 → 파트 5 의 재료·단면 교체",
        "",
        "  *Inputfile",
        "  model.k",
        "  *Mode",
        "  ELASTIC_TO_RIGID,1",
        "  PART_EXCHANGE,2",
        "  **ElastictoRigid,1",
        "  *PIDExcept,5",
        "  **EndElastictoRigid",
        "  **PartExchange,2",
        "  ...",
        "  **EndPartExchange",
        "  *End",
        "",
        "- 모드ID 는 모드마다 다르게. 블록 순서는 상관없고 *Mode 목록 순서가 실행 순서다.",
        "- 출력 이름에는 모드 접미사가 순서대로 붙는다 (model_etor_pex.k).",
        "- PART_TRANSLATE 는 이동을 유지하므로 뒤이은 DROP_ATTITUDE 가 이동된 형상 위에서 동작한다.",
    ]),
    Topic("units", "단위계 — 모델 .k 단위를 그대로 따른다", aliases=["단위", "unit"], body=[
        "KMM 은 단위를 변환하지 않는다. 옵션 값은 모델 .k 와 같은 단위로 넣을 것.",
        "사내 낙하 모델 표준은 [tonne, mm, s, MPa] — 강철 ρ=7.85e-9, E=2.0e5, 높이 mm, 시간 s.",
        "SI(kg, m, s, Pa) 모델이면 ρ=7850, E=2.0e11, 높이 m.",
        "예외: WARPED_PART·WARPED_TO_INITIAL_STRESS_PART 의 UnitScale 은 워피지 데이터 단위를 지정한다.",
        "낙하 속도 √(2gh) 의 g: DROP_ATTITUDE·DROP_WEIGHT_IMPACT_TEST 의 Gravity 키. 없으면 모델 재질 밀도 중앙값으로",
        "  ton-mm-s(< 1e-7) → 9810, kg-m-s(1~1e5) → 9.81. kg-mm-ms 등은 판정 불가라 Gravity 를 꼭 줄 것 (로그 WARNING).",
    ]),
]


# ── 모드 ────────────────────────────────────────────────────────
MODES = []


def mode(*a, **kw):
    MODES.append(Mode(*a, **kw))


# ━━ 낙하·충격 ━━
DROP_BASIC = _opt("model.k", "DROP_ATTITUDE,1", """**DropAttitude,1
EulerRolling,0
EulerPitching,45
EulerYawing,0
Height,1500
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
InitialAngularVelocityX,0
InitialAngularVelocityY,0
InitialAngularVelocityZ,0
OffsetDistance,0.05
Density,7.85e-09
YoungsModulus,200000.0
PoissonRatio,0.3
tFinal,0.005
dt,1e-06
DropSurface,Plane,300,300,20,30,30,2
**EndDropAttitude""")

DROP_MULTI = _opt("model.k", "DROP_ATTITUDE,1", """**DropAttitude,1
EulerRolling,0,90,0
EulerPitching,0,0,90
EulerYawing,0,0,0
Height,1000,1000,1000
InitialVelocityX,0,0,0
InitialVelocityY,0,0,0
InitialVelocityZ,0,0,0
InitialAngularVelocityX,0,0,0
InitialAngularVelocityY,0,0,0
InitialAngularVelocityZ,0,0,0
OffsetDistance,0.05
Density,7.85e-09
YoungsModulus,200000.0
PoissonRatio,0.3
tFinal,0.003
dt,5e-05
DropSurface,RigidWall,0,0,0,0,0,0
DropContact.FS,0.3
DropContact.RWKSF,1.0
**EndDropAttitude""")

DROP_ROBUST = _opt("model.k", "DROP_ATTITUDE,1", """**DropAttitude,1
EulerRolling,30
EulerPitching,20
EulerYawing,10
Gravity,9810
Height,1500
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
InitialAngularVelocityX,0
InitialAngularVelocityY,0
InitialAngularVelocityZ,0
OffsetDistance,0.05
Density,7.85e-09
YoungsModulus,200000.0
PoissonRatio,0.3
tFinal,0.005
dt,1e-05
DropSurface,PlaneGraded,200,200,20,10,10,2,5,1.5
RobustContact,True
RobustContactTolerance,0.1
RigidifySmallDtThreshold,1e-07
DropContact.SOFT,2
DropContact.DTSTIF,3e-08
TiedOptions.ConvertToSegment,True
ControlTimestep.DT2MS,-1e-07
DTMIN,0.01
**EndDropAttitude""", header="*RunDirectoryMode,True,Data/Results\n")

mode("DROP_ATTITUDE", "제품 낙하 해석 덱 생성 — 자세(오일러각)·높이·바닥판·접촉 자동 구성",
     category="낙하·충격", aliases=["drop", "낙하", "자유낙하", "dropset", "오일러", "바닥판"],
     when=["모델을 지정 자세로 돌려 바닥판 위 높이에 두고 낙하 속도·중력·접촉·CONTROL 을 붙인 해석 덱이 필요할 때",
           "여러 자세를 한 번에 — 각 리스트 키에 값을 같은 개수로 나열하면 i 번째 값끼리 한 케이스가 된다"],
     syntax=["**DropAttitude,<ID>", "EulerRolling,<도>[,<도>...]   (리스트 키는 모두 같은 개수)",
             "...", "**EndDropAttitude"],
     keys=[
         K("EulerRolling", "실수 리스트", "-", "X 축 회전(도). 여러 값 = 여러 케이스", True),
         K("EulerPitching", "실수 리스트", "-", "Y 축 회전(도)", True),
         K("EulerYawing", "실수 리스트", "-", "Z 축 회전(도)", True),
         K("Height", "실수 리스트", "-", "낙하 높이 → 초기 속도 √(2gh) 가 InitialVelocity 에 더해진다 (모델은 OffsetDistance 간격에 놓임). g 는 Gravity 키, 없으면 모델 재질 밀도로 단위계 판정 (ton-mm-s → 9810, kg-m-s → 9.81)", True),
         K("Gravity", "실수", "모델 재질 밀도로 판정", "자유낙하 g (모델 단위). 재질 밀도 중앙값 < 1e-7 → 9810, 1~1e5 → 9.81. 판정 불가(kg-mm-ms 등)면 WARNING 후 옛 추정 → 그 단위계는 반드시 지정"),
         K("InitialVelocityX/Y/Z", "실수 리스트", "-", "추가 초기 속도 (각 케이스). Height 속도와 합산", True),
         K("InitialAngularVelocityX/Y/Z", "실수 리스트", "-", "초기 각속도 (각 케이스)", True),
         K("OffsetDistance", "실수", "-", "바닥판과의 초기 간격", True),
         K("Density", "실수", "-", "바닥판 밀도 (RigidWall 이면 쓰지 않지만 키는 필요)", True),
         K("YoungsModulus", "실수", "-", "바닥판 탄성계수", True),
         K("PoissonRatio", "실수", "-", "바닥판 포아송비", True),
         K("tFinal", "실수", "0 (필수로 줄 것)", "종료 시간. tFinal 과 dt 가 둘 다 0 이 아니어야 CONTROL/DATABASE 카드를 쓴다"),
         K("dt", "실수", "0 (필수로 줄 것)", "d3plot 출력 간격 (키 이름 정확히 dt)"),
         K("DTMIN", "실수", "없음", "CONTROL_TERMINATION DTMIN — dt 붕괴 시 자동 종료 비율"),
         K("DropSurface", "형식별", "Plane,0,0,0,10,10,10", "Plane,Lx,Ly,Lz,Nx,Ny,Nz | PlaneGraded,Lx,Ly,Lz,Nx,Ny,Nz[,외곽층수=5[,비율=1.5]] | RigidWall,0,0,0,0,0,0 | PlanewithRoughness,Lx,Ly,Lz,Nx,Ny,Nz,모드,Rmax,SF1[,SF2]"),
         K("DeformableToRigid", "True/False", "False", "DEFORMABLE_TO_RIGID 자동 카드"),
         K("NonReflectingBoundary", "True/False", "False", "바닥판 아랫면 BOUNDARY_NON_REFLECTING (응력파 흡수)"),
         K("IncludeWallInGeneral", "True/False", "False", "바닥판을 일반 접촉에 포함"),
         K("ConvertGeneralToSingleSurface", "True/False", "True", "모델의 일반 접촉을 SINGLE_SURFACE 로 전환"),
         K("EnsureSingleSurface", "True/False", "False", "SINGLE_SURFACE 접촉이 없으면 생성"),
         K("DecomposeGeneralContact", "True/False", "False", "AUTOMATIC_GENERAL 을 파트쌍 접촉으로 자동 분해"),
         K("DecomposeContactMargin", "실수", "1.5", "분해 시 bbox 여유 배율"),
         K("DecomposeContactAbsoluteMarginX/Y/Z", "실수", "5.0/5.0/0.5", "분해 시 bbox 절대 여유"),
         K("RobustContact", "True/False", "False", "Tied 면 제외 Segment Set 으로 SINGLE_SURFACE 재구성 (SOFT=2, DEPTH=3 강제)"),
         K("RobustContactTolerance", "실수", "0.1", "Tied 면 판정 거리"),
         K("RigidifySmallDtThreshold", "실수", "0 (끔)", "이 값보다 stable dt 가 작은 요소를 강체 파트로 분리"),
         K("RigidifyMaxAspectRatio", "실수", "0 (끔)", "종횡비가 이 값보다 큰 요소도 강체화"),
         K("RigidifyElementIDs", "정수 리스트", "없음", "지정 요소를 강체화"),
         K("DropContact.<필드>", "실수/문자", "SOFT=2 SOFSCL=0.1 SBOPT=3 DEPTH=35 ...", "바닥판 접촉 카드 필드 (FS, FD, SOFT, DTSTIF, DTPCHK, IGNORE 등). RigidWall 이면 FS·RWKSF·RW_SOFT·RW_MASS"),
         K("TiedOptions.<필드>", "실수/문자", "-", "Tied 접촉 옵션. TiedOptions.ConvertToSegment,True 는 노드셋→세그먼트 변환"),
         K("ControlTimestep.<필드>", "실수", "-", "*CONTROL_TIMESTEP 덮어쓰기 (TSSFAC, DT2MS 등)"),
         K("ControlHourglass.<필드>", "실수", "-", "*CONTROL_HOURGLASS 덮어쓰기 (IHQ, QH)"),
         K("DynainDynamicRelaxation", "True/False", "False", "누적 스텝용 동적 이완(DR) 블록"),
         K("DynainDynamicRelaxationNrcyck/Tol/Fctr/Term", "수", "0", "DR 파라미터"),
         K("runid", "정수 리스트", "[]", "여러 케이스 중 실행할 케이스 번호만 선택"),
     ],
     examples=[
         Example("한 자세(피치 45°) 1.5 m 낙하, 메시 바닥판", DROP_BASIC,
                 explain=["[tonne, mm, s, MPa] 단위 모델 기준. Height 1500 = 1.5 m.",
                          "결과: model_drop.k (INITIAL_VELOCITY·CONTROL_TERMINATION·DATABASE 카드 포함)."],
                 verify={"mode": "DROP_ATTITUDE", "id": 1, "expect": {
                     "EulerPitching": [45.0], "Height": [1500.0], "TFinal": 0.005, "DT": 1e-06,
                     "OffsetDistance": 0.05, "DropSurface": ["Plane", 300.0, 300.0, 20.0, 30, 30, 2]}}),
         Example("세 자세를 한 파일로 (정면·롤 90°·피치 90°), 강체벽 바닥", DROP_MULTI,
                 explain=["리스트 키의 i 번째 값끼리 케이스 i. 개수가 다르면 IndexError.",
                          "RigidWall 은 메시가 없는 무한 강체 평면 — 접촉 옵션은 DropContact.FS/RWKSF 로."],
                 verify={"mode": "DROP_ATTITUDE", "id": 1, "expect": {
                     "EulerRolling": [0.0, 90.0, 0.0], "EulerPitching": [0.0, 0.0, 90.0],
                     "DropSurface": ["RigidWall"], "DropContact.FS": 0.3, "DropContact.RWKSF": 1.0,
                     "DT": 5e-05}}),
         Example("KooChainRun 이 만드는 형태 — 등급 바닥판·견고 접촉·작은 dt 강체화·질량 스케일링", DROP_ROBUST,
                 explain=["*RunDirectoryMode 가 켜져 있어 결과는 Data/Results/Run_<시각>_<해시>/DropSet.k (Output/, DynamicRelaxation/ 폴더 함께).",
                          "RigidifySmallDtThreshold·DropContact.DTSTIF 처럼 이름에 dt 가 든 키도 dt 와 섞이지 않는다 (2026-09 수정).",
                          "ControlTimestep.DT2MS 음수 = 질량 스케일링 목표 dt."],
                 verify={"mode": "DROP_ATTITUDE", "id": 1, "expect": {
                     "DT": 1e-05, "Gravity": 9810.0, "RigidifySmallDtThreshold": 1e-07, "DropContact.DTSTIF": 3e-08,
                     "DropContact.SOFT": 2.0, "RobustContact": True, "RobustContactTolerance": 0.1,
                     "TiedOptions.ConvertToSegment": True, "ControlTimestep.DT2MS": -1e-07, "DTMIN": 0.01,
                     "DropSurface": ["PlaneGraded", 200.0, 200.0, 20.0, 10, 10, 2, 5, 1.5]}}),
     ],
     notes=["Euler/Height/InitialVelocity/InitialAngularVelocity 10 개 리스트 키와 OffsetDistance·Density·YoungsModulus·PoissonRatio 는 빠지면 KeyError 로 멈춘다.",
            "블록 안 빈 줄에서 블록이 끝난다 — 뒤 키는 무시된다.",
            "오일러 회전 순서 R = Rz·Ry·Rx (롤 → 피치 → 요).",
            "누적 낙하·전각도 DOE 는 KooChainRun 시나리오로 돌리는 편이 낫다 (KooChainRun --help drop)."],
     related=["DROP_WEIGHT_IMPACT_TEST", "RIGIDIFY_SMALL_DT", "DYNAIN_TO_INITIAL", "PART_TRANSLATE"])

IMPACT_SPHERE = _opt("model.k", "DROP_WEIGHT_IMPACT_TEST,1", """**DropWeightImpactTest,1
LocationX,0.0
LocationY,0.0
Height,150
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
Type,Sphere
Dimension,4.0
MeshSize,0.5
DensityImpactor,7.85e-09
YoungsModulusImpactor,200000.0
PoissonRatioImpactor,0.3
DensityWall,1e-09
YoungsModulusWall,10000.0
PoissonRatioWall,0.3
WallNumX,10
WallNumY,10
WallNumZ,10
tFinal,0.001
dt,1e-05
OffsetDistance,0.01
**EndDropWeightImpactTest""")

IMPACT_CYL = _opt("model.k", "DROP_WEIGHT_IMPACT_TEST,1", """**DropWeightImpactTest,1
LocationX,10.0
LocationY,-5.0
Height,200
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
Type,Cylinder
Dimension,4.0,6.0,3.0,5.0,4.0,8.0,20.0
MeshSize,0.5
DimensionDamper,0.1,0.1,1.0
DensityImpactorFront,1.2e-09
YoungsModulusImpactorFront,50.0
PoissonRatioImpactorFront,0.45
DensityImpactorMid,2.7e-09
YoungsModulusImpactorMid,70000.0
PoissonRatioImpactorMid,0.33
DensityImpactor,7.85e-09
YoungsModulusImpactor,200000.0
PoissonRatioImpactor,0.3
DensityWall,1e-09
YoungsModulusWall,10000.0
PoissonRatioWall,0.3
WallNumX,10
WallNumY,10
WallNumZ,10
tFinal,0.002
dt,2e-05
OffsetDistance,0.01
DTMIN,0.01
**EndDropWeightImpactTest""")

IMPACT_BYPART = _opt("model.k", "DROP_WEIGHT_IMPACT_TEST,1", """**DropWeightImpactTest,1
GenerationMode,Part
PartIDs,3
LocationMode,3X3
Height,150
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
Type,Sphere
Dimension,4.0
MeshSize,0.5
DensityImpactor,7.85e-09
YoungsModulusImpactor,200000.0
PoissonRatioImpactor,0.3
tFinal,0.001
dt,1e-05
OffsetDistance,0.01
**EndDropWeightImpactTest""")

mode("DROP_WEIGHT_IMPACT_TEST", "낙추(충격추) 시험 덱 — 구·다단 실린더 충격추를 모델 위 지점에 떨어뜨림",
     category="낙하·충격", aliases=["impact", "낙추", "충격", "충격추", "impactor", "ball drop", "cylinder"],
     when=["구나 실린더 충격추로 국부 충격(화면·배면 등)을 주는 해석 덱이 필요할 때",
           "파트 표면 격자점(3X3 등)에 자동 배치해 여러 케이스를 만들 때 (GenerationMode,Part)"],
     syntax=["**DropWeightImpactTest,<ID>", "Key,Value", "**EndDropWeightImpactTest"],
     keys=[
         K("LocationX / LocationY", "실수 리스트", "-", "충격 지점 (케이스별). GenerationMode,Part 면 생략"),
         K("Height", "실수 리스트", "0.5", "충격추 낙하 높이 → 초기 속도 √(2gh) 가 InitialVelocity 에 더해진다 (모델은 OffsetDistance 간격에 놓임). g 는 Gravity 키, 없으면 모델 재질 밀도로 단위계 판정 (ton-mm-s → 9810, kg-m-s → 9.81)"),
         K("Gravity", "실수", "모델 재질 밀도로 판정", "자유낙하 g (모델 단위). 재질 밀도 중앙값 < 1e-7 → 9810, 1~1e5 → 9.81. 판정 불가(kg-mm-ms 등)면 WARNING 후 옛 추정 → 그 단위계는 반드시 지정"),
         K("InitialVelocityX/Y/Z", "실수 리스트", "0", "추가 초기 속도 (케이스별). Height 속도와 합산되므로 둘 다 주면 이중 가산"),
         K("Type", "Sphere|Cylinder", "Sphere", "충격추 형상"),
         K("Dimension", "실수 리스트", "0.008", "Sphere: 반지름. Cylinder 5값(2단): r,외곽r,앞높이,뒤높이,뒤r / 7값(3단): r,외곽r,앞높이,중간r,중간높이,뒤r,뒤높이"),
         K("MeshSize", "실수", "0.001", "충격추 요소 크기"),
         K("DimensionDamper", "실수 리스트", "-", "댐퍼 치수 (있을 때만 댐퍼 생성)"),
         K("DensityImpactor / YoungsModulusImpactor / PoissonRatioImpactor", "실수", "7.8e-9 / 2.07e5 / 0.3", "충격추 본체(실린더의 뒤 단) 재질"),
         K("...ImpactorFront / ...ImpactorMid", "실수", "본체와 같음", "실린더 앞 단·중간 단 재질 (Density/YoungsModulus/PoissonRatio 접두)"),
         K("MaterialIDImpactor[Front|Mid]", "정수", "0", "0 이면 새 재질 생성, 아니면 기존 MID 재사용"),
         K("DensityWall / YoungsModulusWall / PoissonRatioWall", "실수", "-", "바닥 벽 재질"),
         K("WallNumX/Y/Z", "정수", "10", "바닥 벽 분할 수"),
         K("DensityDamper / YoungsModulusDamper / PoissonRatioDamper", "실수", "-", "댐퍼 재질"),
         K("tFinal", "실수", "0", "종료 시간"),
         K("dt", "실수", "1e-6", "d3plot 출력 간격"),
         K("DTMIN", "실수", "없음", "CONTROL_TERMINATION DTMIN"),
         K("OffsetDistance", "실수", "1e-9", "충격추와 표면 초기 간격"),
         K("GenerationMode", "DampingSpring|Part", "DampingSpring", "Part = PartIDs 파트 표면 격자에 자동 배치"),
         K("PartIDs", "정수 리스트", "[]", "GenerationMode,Part 대상 파트"),
         K("LocationMode", "NXM 문자열", "1X1", "파트 표면 격자 배치 (예: 3X3 → 9 케이스)"),
         K("BoundaryDistance / DistanceMargin / StressWaveVelocity", "실수", "0", "부분 강체화 경계 거리 계산용"),
         K("DynainDynamicRelaxation[Nrcyck|Tol|Fctr|Term]", "수", "False/0", "누적 스텝 DR"),
     ],
     examples=[
         Example("반지름 4 mm 강구를 150 mm 높이에서 원점에 (mm-ton-s)", IMPACT_SPHERE,
                 verify={"mode": "DROP_WEIGHT_IMPACT_TEST", "id": 1, "expect": {
                     "Type": "Sphere", "Dimension": [4.0], "DensityImpactor": 7.85e-09,
                     "YoungsModulusWall": 10000.0, "WallNumX": 10, "TFinal": 0.001, "DT": 1e-05,
                     "OffsetDistance": 0.01}}),
         Example("3단 실린더 충격추 (앞 고무·중간 알루미늄·뒤 강철)", IMPACT_CYL,
                 explain=["뒤 단(back) 재질은 별도 슬롯이 없고 DensityImpactor/YoungsModulusImpactor/PoissonRatioImpactor 가 뒤 단이다.",
                          "Dimension 7값 = r,외곽r,앞높이,중간r,중간높이,뒤r,뒤높이."],
                 verify={"mode": "DROP_WEIGHT_IMPACT_TEST", "id": 1, "expect": {
                     "Type": "Cylinder", "Dimension": [4.0, 6.0, 3.0, 5.0, 4.0, 8.0, 20.0],
                     "DensityImpactorFront": 1.2e-09, "YoungsModulusImpactorMid": 70000.0,
                     "DensityImpactor": 7.85e-09, "PoissonRatioImpactor": 0.3, "DTMIN": 0.01, "DT": 2e-05}}),
         Example("파트 3 표면 3×3 격자에 자동 배치 (9 케이스)", IMPACT_BYPART,
                 verify={"mode": "DROP_WEIGHT_IMPACT_TEST", "id": 1, "expect": {
                     "Mode": "Part", "PartIDs": [3], "LocationMode": ["3X3"]}}),
     ],
     notes=["키 이름은 YoungsModulus (s 포함). 옛 예제의 YoungModulus·Density(접미 없음)는 인식되지 않아 기본값이 쓰인다.",
            "Type 줄은 Dimension 줄보다 앞에 둘 것 — Dimension 해석이 Type 에 따라 달라진다.",
            "블록 안 빈 줄에서 블록이 끝난다."],
     related=["DROP_ATTITUDE"])


# ━━ 하중 ━━
mode("VIBRATION_LOAD", "진동 하중 — 하중곡선 × 파트별 계수로 LOAD_BODY/LOAD_NODE 생성",
     category="하중", aliases=["vibration", "진동", "가진", "load curve", "loadcurve"],
     when=["시간 이력 하중(힘·가속도)을 파트별 비율로 걸 때"],
     syntax=["**VibrationLoad,<ID>", "Direction,X|Y|Z", "LoadType,Force|Acceleration",
             "RelativeMode,Explicit|Volume|...", "LoadCurve  (다음 줄부터 `시간, 값` … EndLoadCurve)",
             "PartFactors (다음 줄부터 `PID, 계수` … EndPartFactors)", "PartList (PID 나열 … EndPartList)",
             "**EndVibrationLoad"],
     keys=[
         K("Direction", "X|Y|Z", "Z", "하중 방향"),
         K("LoadType", "Force|Acceleration", "Force", "하중 종류"),
         K("RelativeMode", "Explicit|Volume 등", "Explicit", "Explicit = PartFactors 계수 그대로, Volume = 부피 비례 (ReferencePart 기준)"),
         K("ReferencePart", "정수", "-", "상대 모드 기준 파트"),
         K("LoadCurve … EndLoadCurve", "시간, 값 줄들", "[]", "하중 곡선"),
         K("PartFactors … EndPartFactors", "PID, 계수 줄들", "{}", "파트별 배율 (Explicit)"),
         K("PartList … EndPartList", "PID 나열", "[]", "대상 파트 (상대 모드)"),
     ],
     examples=[
         Example("Z 방향 힘, 파트별 계수", _opt("MinimumModel.k", "VIBRATION_LOAD,1", """**VibrationLoad,1
Direction,Z
LoadType,Force
RelativeMode,Explicit
LoadCurve
0.0, 0.0
0.001, 100.0
0.002, 0.0
EndLoadCurve
PartFactors
1, 1.0
2, 0.5
EndPartFactors
**EndVibrationLoad"""),
                 explain=["결과: MinimumModel_vib.k (DEFINE_CURVE + LOAD_BODY_GENERALIZED_SET_PART) + MinimumModel_vib.json."],
                 verify={"mode": "VIBRATION_LOAD", "id": 1, "expect": {
                     "Direction": "Z", "LoadType": "Force", "RelativeMode": "Explicit",
                     "LoadCurve": [[0.0, 0.0], [0.001, 100.0], [0.002, 0.0]],
                     "PartFactors": {1: 1.0, 2: 0.5}}}),
     ],
     notes=["이 모드 블록은 빈 줄·`$` 줄을 건너뛴다.", "모르는 키는 Warning 을 찍고 무시한다."],
     related=["THERMAL_LOAD"])

mode("THERMAL_LOAD", "열 하중 — 균일 온도 변화 열응력 또는 IC 발열(ICPower) 2-pass",
     category="하중", aliases=["thermal", "열", "온도", "열응력", "cte", "icpower", "발열"],
     when=["챔버 온도 변화(25→85 ℃ 등)로 열팽창 응력을 볼 때 (UniformChamber)",
           "IC 발열로 온도장을 푼 뒤 그 온도로 구조 해석할 때 (ICPower, Phase thermal → structural)"],
     syntax=["**ThermalLoad,<ID>", "ThermalType,UniformChamber|ICPower", "Key,Value",
             "PartCTE / Materials / HeatSources / TempCurve 하위 블록 (End<이름> 으로 닫음)", "**EndThermalLoad"],
     keys=[
         K("ThermalType", "UniformChamber|ICPower", "UniformChamber", "열 하중 종류"),
         K("BaseTempC / TargetTempC", "실수", "25 / 85", "시작·목표 온도 ℃"),
         K("RampTimeS", "실수", "1e-3", "온도 상승 시간 s"),
         K("DT", "실수", "1e-6", "d3plot 출력 간격"),
         K("DTMIN", "실수", "없음", "CONTROL_TERMINATION DTMIN"),
         K("DefaultCTE", "실수", "1.7e-5", "PartCTE 에 없는 파트의 열팽창계수"),
         K("PartCTE … EndPartCTE", "PID, CTE 줄들", "{}", "파트별 열팽창계수"),
         K("TempCurve … EndTempCurve", "시간, 온도 줄들", "[]", "온도 곡선 직접 지정"),
         K("Phase", "thermal|structural", "thermal", "ICPower: pass1 열해석 / pass2 구조"),
         K("AnalysisType", "transient|steady", "transient", "ICPower 열해석 종류"),
         K("UnitSystem", "SI 등", "SI", "ICPower 단위계"),
         K("InitialTemperatureC", "실수", "25", "ICPower 초기 온도"),
         K("TimestepIts / TimestepTmax / TimestepDtemp", "실수", "-", "*CONTROL_THERMAL_TIMESTEP"),
         K("Materials … EndMaterials", "PID, rho, hc, tc[, cte]", "{}", "ICPower 파트별 열물성 — 전 파트 필요"),
         K("HeatSources … EndHeatSources", "PID, 발열W, 부피mm3", "[]", "ICPower 발열원"),
     ],
     examples=[
         Example("25→85 ℃ 균일 챔버, 파트별 CTE", _opt("model.k", "THERMAL_LOAD,1", """**ThermalLoad,1
ThermalType,UniformChamber
BaseTempC,25
TargetTempC,85
RampTimeS,0.001
DT,1e-06
DefaultCTE,1.7e-05
PartCTE
1,2.3e-05
2,1.7e-05
EndPartCTE
**EndThermalLoad""", header="*RunDirectoryMode,True,out\n"),
                 explain=["결과: out/Run_<시각>_<해시>/ThermalSet.k (+ ThermalSet.json). 열해석은 배정밀 LS-DYNA 가 필요하다."],
                 verify={"mode": "THERMAL_LOAD", "id": 1, "expect": {
                     "ThermalType": "UniformChamber", "BaseTempC": 25.0, "TargetTempC": 85.0,
                     "RampTimeS": 0.001, "DT": 1e-06, "PartCTE": {1: 2.3e-05, 2: 1.7e-05}}}),
         Example("IC 발열 pass1 (열해석)", _opt("model.k", "THERMAL_LOAD,1", """**ThermalLoad,1
ThermalType,ICPower
Phase,thermal
AnalysisType,transient
UnitSystem,SI
InitialTemperatureC,25
TimestepIts,0.01
Materials
1,7.85e-09,4.6e+08,50
2,2.33e-09,7.0e+08,150
EndMaterials
HeatSources
2,1.5,8.0
EndHeatSources
**EndThermalLoad"""),
                 explain=["pass2 는 같은 블록에 Phase,structural 로 다시 실행 (KooChainRun THERM 모드가 자동으로 두 번 부른다)."],
                 verify={"mode": "THERMAL_LOAD", "id": 1, "expect": {
                     "ThermalType": "ICPower", "Phase": "thermal", "timestep.its": 0.01,
                     "materials": {1: {"rho": 7.85e-09, "hc": 4.6e+08, "tc": 50.0},
                                   2: {"rho": 2.33e-09, "hc": 7.0e+08, "tc": 150.0}},
                     "heat_sources": [{"part": 2, "power_W": 1.5, "volume_mm3": 8.0}]}}),
     ],
     notes=["이 모드 블록은 빈 줄·`$` 줄을 건너뛴다.", "ICPower 는 전 파트 열물성(rho/hc/tc)이 없으면 열해석이 실패한다."],
     related=["VIBRATION_LOAD"])


# ━━ 파트·재료 ━━
mode("ELASTIC_TO_RIGID", "모든 변형체 파트를 강체(MAT_RIGID)로 — 지정 PID 만 제외",
     category="파트·재료", aliases=["rigid", "강체", "강체화", "etor"],
     when=["관심 파트만 변형체로 남기고 나머지를 강체로 바꿔 해석을 가볍게 할 때"],
     syntax=["**ElastictoRigid,<ID>", "*PIDExcept,<pid>[,<pid>...]", "**EndElastictoRigid"],
     keys=[K("*PIDExcept", "정수 리스트", "없음 (전부 강체)", "강체화에서 제외할 파트")],
     examples=[Example("파트 5·7 만 변형체로 남김", _opt("model.k", "ELASTIC_TO_RIGID,1", """**ElastictoRigid,1
*PIDExcept,5,7
**EndElastictoRigid"""),
                       explain=["결과: model_etor.k (파트 5·7 외 재료가 MAT_RIGID)."],
                       verify={"mode": "ELASTIC_TO_RIGID", "id": 1, "expect": {"PIDExcept": [5, 7]}})],
     related=["RIGIDIFY_SMALL_DT", "PART_EXCHANGE"])

mode("MATERIAL_EXCHANGE", "재료 카드 치환 + 변수 스윕 — 값 목록마다 .k 한 개씩",
     category="파트·재료", aliases=["material", "재료", "재료교체", "mat", "mex", "스윕"],
     when=["재료 물성(E 등)을 여러 값으로 바꾼 모델을 한꺼번에 만들 때"],
     syntax=["**MaterialExchange,<ID>", "*VarList,<변수>,<값1>,<값2>,...",
             "*MID<번호>,<*MAT 키워드>", "<카드 제목 줄>", "<10칸 고정폭 카드 줄들 — 변수 이름을 칸에 그대로>",
             "**EndMaterialExchange"],
     keys=[K("*VarList", "이름 + 실수 리스트", "-", "카드 안에서 치환할 변수와 값 목록"),
           K("*MID<n>,<키워드>", "블록", "-", "교체할 재료 카드. 다음 줄=제목, 그 뒤 `*` 로 시작하는 줄 전까지 10칸 카드. 첫 칸 MID 가 교체 대상 재료 ID. 같은 *MAT 키워드는 한 블록에 한 번")],
     examples=[Example("MAT_ELASTIC 재료 1 의 E 를 3 가지로", _opt("model.k", "MATERIAL_EXCHANGE,1", """**MaterialExchange,1
*VarList,E01,2.0e9,3.0e9,4.0e9
*MID01,*MAT_ELASTIC_TITLE
Steel
$$     MID        RO         E        PR        DA        DB         K
         1 1.100e+03       E01 3.700e-01
**EndMaterialExchange"""),
                       explain=["카드 줄은 10칸 고정폭. 변수 이름(E01)을 해당 칸에 오른쪽 정렬로 넣는다."],
                       verify={"mode": "MATERIAL_EXCHANGE", "id": 1, "expect": {"Vars.E01": [2.0e9, 3.0e9, 4.0e9],
                                                                          "MIDs.*MAT_ELASTIC_TITLE.2.2": "       E01"}})],
     related=["PART_EXCHANGE"])

mode("PART_EXCHANGE", "파트의 재료·단면·요소 형식 교체 (솔리드→TShell, 비정렬→정렬 격자 등)",
     category="파트·재료", aliases=["part exchange", "파트교체", "단면교체", "tshell", "structured", "pex"],
     when=["파트의 SECTION/MAT 카드를 새 카드로 바꿀 때",
           "헥사 솔리드를 TShell 로, 비정렬 메시를 정렬 격자로 바꿀 때"],
     syntax=["**PartExchange,<ID>", "*PID,<pid> 또는 *PIDS,<pid...>|ALL",
             "(카드 교체) *SECTION_... / *MAT_... 카드 원문 — 첫 칸 SID/MID 는 문자 그대로",
             "(변환) *ConvertHexato,TShell,(nx,ny,nz),<각도공차>",
             "(변환) *UnstructuredtoStructured,(NX,NY,NZ) [+ *LayerThickness … *EndLayerThickness]",
             "**EndPartExchange"],
     keys=[K("*PID / *PIDS", "정수 | ALL", "-", "대상 파트"),
           K("*SECTION_... / *MAT_... / *EOS / *HOURGLASS", "카드 원문", "-", "교체할 카드. ID 칸에 SID/MID 등 문자를 쓰면 새 ID 로 채운다"),
           K("*ConvertHexato", "TShell,(방향),각도", "-", "헥사 솔리드 → 두께 방향 TShell"),
           K("*UnstructuredtoStructured", "(NX,NY,NZ)", "-", "비정렬 → 정렬 격자"),
           K("*LayerThickness … *EndLayerThickness", "실수 줄들", "-", "정렬 격자 Z 층 두께"),
           K("*NumberofElements / *InplaneRotation / *Layup", "-", "-", "정렬 격자·적층 세부")],
     examples=[
         Example("파트 5 의 단면·재료를 새 카드로", _opt("model.k", "PART_EXCHANGE,1", """**PartExchange,1
*PID,5
*SECTION_SOLID_TITLE
ImpactBallSection
$$   SECID    ELFORM       AET    COHOFF   GASKETT
       SID         1
*MAT_ELASTIC_TITLE
Steel
$$     MID        RO         E        PR        DA        DB         K
       MID 7.850e-09 2.000e+05 3.000e-01
**EndPartExchange"""),
                 explain=["카드 ID 칸의 SID·MID 문자는 새 ID 로 채워진다. 칸 폭 10 을 지킬 것."],
                 verify={"mode": "PART_EXCHANGE", "id": 1, "expect": {"PID": 5, "*SECTION_SOLID_TITLE.2.0": "       SID", "*MAT_ELASTIC_TITLE.2.0": "       MID"}}),
         Example("파트 1 헥사 솔리드 → TShell (두께 방향 +Z, 각도 공차 5°)", _opt("model.k", "PART_EXCHANGE,1", """**PartExchange,1
*PID,1
*ConvertHexato,TShell,(0,0,1),5.0
**EndPartExchange"""),
                 verify={"mode": "PART_EXCHANGE", "id": 1, "expect": {"PID": 1, "converthexato": {"Type": "TShell", "Vector": [0.0, 0.0, 1.0], "ToleranceAngle": 5.0}}}),
     ],
     notes=["변환 기능은 모델 형상 조건이 까다롭다 — 작은 모델로 먼저 확인할 것."],
     related=["MATERIAL_EXCHANGE", "ELASTIC_TO_RIGID"])

mode("PART_MORPHING", "파트 형상 국부 변형 — 박스/파트 영역을 밀거나 당김",
     category="파트·재료", aliases=["morph", "모핑", "형상변형", "dent", "찍힘"],
     when=["찍힘·볼록 같은 국부 형상 변화를 메시에 직접 줄 때"],
     syntax=["**PartMorphing,<ID>", "*UnitScale,<배율>",
             "*MorphBox,<PID>,(x,y,z 원점),(Lx,Ly,Lz),(X방향),(Z방향),<변위>,<영향반경>,<각도>",
             "*MorphfromPIDBox,<PID>,<박스PID>,(X방향),(Z방향),<변위>,<영향반경>,<각도>",
             "**EndPartMorphing"],
     keys=[K("*UnitScale", "실수", "1.0", "좌표 배율"),
           K("*MeshSize", "실수", "끔", "지정 시 재메시"),
           K("*MorphBox", "위 형식", "-", "박스 영역 모핑. 변위 양수 = Pull, 음수 = Push (파서 기준, 크기는 절댓값)"),
           K("*MorphfromPIDBox", "위 형식", "-", "박스PID 파트의 bbox 를 박스로 사용 (0 이나 자기 자신이면 대상 파트 bbox)"),
           K("*MorphPID", "-", "-", "파트 전체 모핑")],
     examples=[Example("파트 1 박스 영역 모핑 — 변위 0.01 (양수라 Pull)", _opt("model.k", "PART_MORPHING,1", """**PartMorphing,1
*UnitScale,1
*MorphBox,1,(0.0,0.0,0.0),(0.2,0.2,100.0),(1,0,0),(0,0,-1),0.01,0.2,5.0
**EndPartMorphing"""),
                       verify={"mode": "PART_MORPHING", "id": 1, "expect": {"UnitScale": 1.0, "Morph.1.Type": "Box", "Morph.1.Mode": "Pull", "Morph.1.PushDistance": 0.01,
                           "Morph.1.ZLength": 100.0, "Morph.1.ZDir": [0.0, 0.0, -1.0]}})],
     notes=["옛 예제 주석의 Push(+)/Pull(-) 표기는 파서와 반대다 — 양수가 Pull."],
     related=["WARPED_PART"])

mode("WARPED_PART", "워피지(휨) 측정 데이터를 파트 형상에 반영",
     category="파트·재료", aliases=["warpage", "워피지", "휨", "warp"],
     when=["측정한 휨 형상을 PCB·패널 파트 좌표에 입힐 때"],
     syntax=["**WarpedPart,<ID>", "*Key,Value", "**EndWarpedPart"],
     keys=[K("*UnitScale", "mm|Microm 등", "mm", "워피지 데이터 단위"),
           K("*AmplitudeTop / *AmplitudeBottom", "실수", "1.0 / 0.0", "윗면·아랫면 변위 배율"),
           K("*Location", "x,y,z", "0,0,0", "데이터 원점"),
           K("*XLength / *YLength", "실수", "0 (자동)", "데이터 영역 크기"),
           K("*Direction", "x,y,z", "0,0,1", "변위 방향"),
           K("*WarpageFileTop / *WarpageFileBottom", "파일", "warpage.dat / 없음", "워피지 격자 데이터"),
           K("*PIDs", "정수 리스트", "[]", "대상 파트")],
     examples=[Example("파트 1~4 에 윗면 워피지 0.1 배", _opt("model.k", "WARPED_PART,1", """**WarpedPart,1
*UnitScale,Microm
*AmplitudeTop,0.1
*AmplitudeBottom,0.0
*Location,0.0,0.0,0.0
*XLength,0.0
*YLength,0.0
*Direction,0.0,0.0,1.0
*WarpageFileTop,warpage.dat
*PIDs,1,2,3,4
**EndWarpedPart"""),
                       verify={"mode": "WARPED_PART", "id": 1, "expect": {
                           "UnitScale": "Microm", "AmplitudeTop": 0.1, "WarpageFileTop": "warpage.dat",
                           "PIDs": [1, 2, 3, 4], "Direction": [0.0, 0.0, 1.0]}})],
     related=["WARPED_TO_INITIAL_STRESS_PART"])

mode("WARPED_TO_INITIAL_STRESS_PART", "워피지를 형상 대신 초기 응력으로 부여",
     category="파트·재료", aliases=["warpage stress", "초기응력", "워피지응력", "w2is"],
     when=["휨을 형상이 아니라 잔류 응력 상태로 넣고 싶을 때"],
     syntax=["**WarpedtoInitialStressPart,<ID>", "*Key,Value", "**EndWarpedtoInitialStressPart"],
     keys=[K("(WARPED_PART 키 전부)", "-", "-", "UnitScale·Amplitude·Location·Direction·WarpageFile·PIDs"),
           K("*AdditionalThickness", "실수", "0.0", "추가 두께")],
     examples=[Example("파트 1 윗면·아랫면 워피지를 초기 응력으로", _opt("PlateSolid.k", "WARPED_TO_INITIAL_STRESS_PART,1", """**WarpedtoInitialStressPart,1
*UnitScale,Microm
*AmplitudeTop,1000.0
*AmplitudeBottom,1000.0
*Location,0.0,0.0,0.0
*Direction,0.0,0.0,1.0
*AdditionalThickness,0.0
*WarpageFileTop,warpage.dat
*WarpageFileBottom,warpage.dat
*PIDs,1
**EndWarpedtoInitialStressPart"""),
                       verify={"mode": "WARPED_TO_INITIAL_STRESS_PART", "id": 1, "expect": {
                           "AmplitudeBottom": 1000.0, "WarpageFileBottom": "warpage.dat", "PIDs": [1]}})],
     related=["WARPED_PART"])

mode("DIMENSIONAL_TOLERANCE", "파트 치수 공차 DOE — 목록/정규분포/LHS 로 파트 크기 변형 케이스 생성",
     category="파트·재료", aliases=["tolerance", "공차", "치수공차", "lhs", "doe"],
     when=["조립 공차에 따른 파트 치수 변화를 여러 케이스로 만들 때"],
     syntax=["**DimensionalTolerance,<ID>", "*PartDimTolerance,LIST            → 다음 줄들 `PID,방향,공차1,공차2,...`",
             "*PartDimTolerance,NORM,<샘플수>    → `PID,방향,평균,표준편차`",
             "*PartDimTolerance,LHS,<샘플수>     → `PID,방향,최소,최대`", "**EndDimensionalTolerance"],
     keys=[K("*PartDimTolerance", "LIST|NORM,n|LHS,n", "LIST, 1", "공차 샘플링 방식"),
           K("PID,방향,값...", "데이터 줄", "-", "방향 X|Y|Z. `#` 줄은 주석")],
     examples=[
         Example("목록 방식 — 파트 1 Z 방향 3 값", _opt("PlateSolid.k", "DIMENSIONAL_TOLERANCE,1", """**DimensionalTolerance,1
*PartDimTolerance,LIST
#PID,Direction,tol1,tol2,...
1,Z,0.00,-0.3,0.05
**EndDimensionalTolerance"""),
                 verify={"mode": "DIMENSIONAL_TOLERANCE", "id": 1, "expect": {"Mode": "LIST", "PartOption.1.z": ["0.00", "-0.3", "0.05"]}}),
         Example("LHS 100 샘플 — 파트 1 X 방향 ±0.05", _opt("PlateSolid.k", "DIMENSIONAL_TOLERANCE,1", """**DimensionalTolerance,1
*PartDimTolerance,LHS,100
1,X,-0.05,0.05
**EndDimensionalTolerance"""),
                 verify={"mode": "DIMENSIONAL_TOLERANCE", "id": 1, "expect": {"Mode": "LHS", "NumberofSamples": 100, "PartOption.1.x": ["-0.05", "0.05"]}}),
     ],
     related=["PART_LOCATION_DOE", "TRANSLATION_DOE"])


# ━━ 메시 ━━
mode("RIGIDIFY_SMALL_DT", "stable dt 가 작은 요소를 강체 파트로 분리하고 접촉에서 제외",
     category="메시", aliases=["small dt", "작은dt", "강체화", "rsdt", "timestep"],
     when=["찌그러진 몇 개 요소 때문에 해석 dt 가 무너질 때"],
     syntax=["**RigidifySmallDt,<ID>", "*DtThreshold,<dt>", "**End"],
     keys=[K("*DtThreshold", "실수", "1e-8", "이보다 stable dt 가 작은 요소를 강체화"),
           K("*MaxAspectRatio", "실수", "0 (끔)", "종횡비가 이 값보다 큰 요소도"),
           K("*ElementIDs", "정수 리스트", "없음", "지정 요소를 강제로"),
           K("*ExceptPID", "정수 리스트", "없음", "제외 파트")],
     examples=[Example("dt 1e-8 미만 + 종횡비 20 초과 요소 강체화, 파트 5·6 제외", _opt("model.k", "RIGIDIFY_SMALL_DT,1", """**RigidifySmallDt,1
*DtThreshold,1.0e-8
*MaxAspectRatio,20.0
*ExceptPID,5,6
**End"""),
                       explain=["출력: model_rsdt.k. DROP_ATTITUDE 안에서 쓰려면 RigidifySmallDtThreshold 키를 쓴다."],
                       verify={"mode": "RIGIDIFY_SMALL_DT", "id": 1, "expect": {
                           "DtThreshold": 1e-08, "MaxAspectRatio": 20.0, "ExceptPIDs": {5, 6}}})],
     related=["ERODING_MIN_DT", "REMESH_TETRA", "DROP_ATTITUDE"])

mode("ERODING_MIN_DT", "요소 삭제(erosion) 최소 dt 설정 — MAT_ADD_EROSION 류",
     category="메시", aliases=["erosion", "eroding", "요소삭제", "dtmin", "emdt"],
     when=["dt 가 너무 작아진 요소를 해석 중 삭제하도록 할 때"],
     syntax=["**ErodingMinDT,<ID>", "*DT,<dt>", "**EndErodingMinDT"],
     keys=[K("*DT", "실수", "1e-9", "이 값보다 dt 가 작아지면 요소 삭제")],
     examples=[Example("dt 1e-8 미만 요소 삭제", _opt("model.k", "ERODING_MIN_DT,1", """**ErodingMinDT,1
*DT,1.0e-8
**EndErodingMinDT"""),
                       verify={"mode": "ERODING_MIN_DT", "id": 1, "expect": {"DT": 1e-08}})],
     notes=["erosion 은 발산을 막는 수단으로는 믿을 수 없다 — 긴 해석은 wall-clock timeout 을 함께 쓸 것."],
     related=["RIGIDIFY_SMALL_DT"])

mode("REMESH_TETRA", "지정 파트를 품질 좋은 사면체로 재메시 (공유 절점 유지)",
     category="메시", aliases=["remesh", "재메시", "tetra", "사면체", "메시품질"],
     when=["불량 요소가 몰린 파트를 새 사면체 메시로 바꿀 때"],
     syntax=["**RemeshTetra,<ID>", "*PID,<pid...>", "*Key,Value", "**EndRemeshTetra"],
     keys=[K("*PID", "정수 리스트", "[]", "대상 파트"),
           K("*MinDt", "실수", "0", "목표 최소 stable dt"),
           K("*TargetEdgeLength", "실수", "0 (자동)", "목표 모서리 길이"),
           K("*MaxAspectRatio", "실수", "10", "허용 종횡비"),
           K("*SmoothingIterations", "정수", "-", "스무딩 반복"),
           K("*PreserveSharedNodes", "True/False", "True", "다른 파트와 공유 절점 유지"),
           K("*Objective", "문자", "-", "최적화 목표")],
     examples=[Example("파트 100099·35202 재메시", _opt("model.k", "REMESH_TETRA,1", """**RemeshTetra,1
*PID,100099,35202
*MinDt,1.0e-8
*TargetEdgeLength,0.5
*MaxAspectRatio,10.0
*SmoothingIterations,5
*PreserveSharedNodes,True
**EndRemeshTetra"""),
                       verify={"mode": "REMESH_TETRA", "id": 1, "expect": {
                           "PID": [100099, 35202], "MinDt": 1e-08, "TargetEdgeLength": 0.5,
                           "SmoothingIterations": 5, "PreserveSharedNodes": True}})],
     related=["RIGIDIFY_SMALL_DT", "DEFEATURE_MESH"])

mode("DEFEATURE_MESH", "짧은 모서리(작은 형상) 제거로 메시 단순화",
     category="메시", aliases=["defeature", "형상단순화", "짧은모서리", "def"],
     when=["작은 필렛·구멍 때문에 dt 가 작은 파트를 단순화할 때"],
     syntax=["**DefeatureMesh,<ID>", "*PIDS,<pid...>", "*MinLength,<길이>", "**EndDefeatureMesh"],
     keys=[K("*PIDS", "정수 리스트", "[]", "대상 파트"), K("*MinLength", "실수", "-", "이보다 짧은 모서리 제거")],
     examples=[Example("파트 5 의 0.05 mm 미만 모서리 제거", _opt("model.k", "DEFEATURE_MESH,1", """**DefeatureMesh,1
*PIDS,5
*MinLength,0.05
**EndDefeatureMesh"""),
                       verify={"mode": "DEFEATURE_MESH", "id": 1, "expect": {"PIDS": [5], "MinLength": 0.05}})],
     related=["REMESH_TETRA"])

mode("COHESIVE_BETWEEN_CONFORMAL_MESHES", "절점 공유 두 파트 사이에 코히시브 요소층 삽입",
     category="메시", aliases=["cohesive", "코히시브", "접착", "박리", "cbcm"],
     when=["접착·솔더 계면의 박리를 코히시브 요소로 모델링할 때"],
     syntax=["**CohesiveBetweenConformalMeshes,<ID>", "재료키,값 (RO, EN, ET, GIC, GIIC, XMU, T, S, UND, UTD, GAMMA, ROFlag, INTFAIL)",
             "Pair,<파트A>,<파트B>,<두께>", "**EndCohesiveBetweenConformalMeshes"],
     keys=[K("Pair", "PID,PID,두께", "-", "코히시브를 넣을 파트 쌍 (여러 줄 가능)"),
           K("RO / ROFlag / INTFAIL", "실수", "2.3e-9 / 0 / 0", "MAT_COHESIVE 밀도·플래그"),
           K("EN / ET", "실수", "1000 / 100", "법선·접선 강성"),
           K("GIC / GIIC", "실수", "10 / 10", "파괴 에너지"),
           K("T / S", "실수", "100 / 100", "법선·전단 강도"),
           K("UND / UTD / GAMMA / XMU", "실수", "10 / 10 / 1 / 1", "파단 변위·지수")],
     examples=[Example("파트 1-2 사이 0.15 mm 코히시브", _opt("model.k", "COHESIVE_BETWEEN_CONFORMAL_MESHES,1", """**CohesiveBetweenConformalMeshes,1
RO,2.3e-9
EN,1000.0
ET,100.0
GIC,10.0
GIIC,10.0
T,100.0
S,100.0
Pair,1,2,0.15
**EndCohesiveBetweenConformalMeshes"""),
                       verify={"mode": "COHESIVE_BETWEEN_CONFORMAL_MESHES", "id": 1, "expect": {
                           "PartA": [1], "PartB": [2], "Thickness": [0.15], "CohesiveMat.T": 100.0, "CohesiveMat.EN": 1000.0}})],
     notes=["키를 한 글자(T, S)나 짧은 부분 문자열로 찾으므로 목록에 없는 키를 넣으면 엉뚱한 값에 들어갈 수 있다."])

mode("CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM", "CNRB(절점 강체) 연결을 빔 요소로 치환",
     category="메시", aliases=["cnrb", "beam", "빔", "절점강체", "connector"],
     when=["나사·용접 CNRB 연결을 강성 있는 빔으로 바꿀 때"],
     syntax=["**ConstrainedNodalRigidbodytoBeam,<ID>", "*PID,ALL | *PID,<cnrb id...>", "*E,.. *PR,.. *RHO,.. *Width,.. *Height,..",
             "**EndConstrainedNodalRigidbodytoBeam"],
     keys=[K("*PID", "ALL | 정수 리스트", "ALL", "대상 CNRB"),
           K("*E / *PR / *RHO", "실수", "1e6 / 0.3 / 7e-9", "빔 재질"),
           K("*Width / *Height", "실수", "1.0 / 1.0", "빔 사각 단면")],
     examples=[Example("모든 CNRB 를 1×1 강철 빔으로", _opt("Connector.k", "CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM,1", """**ConstrainedNodalRigidbodytoBeam,1
*PID,ALL
*E,1.0e7
*PR,0.3
*RHO,7.8e-9
*Width,1.0
*Height,1.0
**EndConstrainedNodalRigidbodytoBeam"""),
                       verify={"mode": "CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM", "id": 1, "expect": {
                           "ALL": True, "E": 1.0e7, "RHO": 7.8e-9, "Width": 1.0}})],
     related=["CONVERT_CNRB_TO_SOLID"])

mode("CONVERT_CNRB_TO_SOLID", "원통 배치 CNRB(나사 등)를 솔리드 원통으로 치환",
     category="메시", aliases=["cnrb solid", "나사", "screw", "원통", "cylinder"],
     when=["원형으로 배치된 CNRB 절점을 실제 솔리드 원통(보스·나사)으로 바꿀 때"],
     syntax=["**ConvertCNRBtoSolid,<ID>", "Key,Value", "**EndConvertCNRBtoSolid"],
     keys=[K("ALL", "True/False", "True", "모든 CNRB"), K("CNRB_IDs", "정수 리스트", "[]", "ALL,False 일 때 대상"),
           K("E / PR / RHO", "실수", "2e11 / 0.3 / 7850", "원통 재질 (기본값은 SI 단위)"),
           K("RadiusScale", "실수", "0.999", "원통 반지름 배율"),
           K("NumCircumNodes", "정수", "0 (자동)", "원주 절점 수"),
           K("AxisDirection", "Auto|X|Y|Z", "Auto", "원통 축"),
           K("InnerRadiusRatio", "실수", "0.3", "내경 비율"),
           K("ZTolerance / RTolerance", "실수", "0.01 / 0.5", "축·반경 판정 공차")],
     examples=[Example("전체 CNRB, 원주 8 절점", _opt("sample_cnrb.k", "CONVERT_CNRB_TO_SOLID,1", """**ConvertCNRBtoSolid,1
ALL,True
E,200000000000
PR,0.3
RHO,7850
RadiusScale,0.999
NumCircumNodes,8
AxisDirection,Auto
InnerRadiusRatio,0.3
ZTolerance,0.1
**EndConvertCNRBtoSolid"""),
                       verify={"mode": "CONVERT_CNRB_TO_SOLID", "id": 1, "expect": {
                           "ALL": True, "E": 2.0e11, "NumCircumNodes": 8, "AxisDirection": "Auto", "ZTolerance": 0.1}})],
     notes=["모델이 mm-ton 단위면 E·RHO 를 반드시 바꿔 줄 것 (기본값 SI)."],
     related=["CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM"])

mode("FEM_TO_IGA", "FEM 파트를 IGA(NURBS) 파트로 변환",
     category="메시", aliases=["iga", "nurbs", "isogeometric"],
     when=["파트를 IGA 솔리드로 바꿔 LS-DYNA IGA 해석을 할 때"],
     syntax=["**FEMtoIGA,<ID>", "*IGA,<PID>,<IGAID>,<출력파일>[,rr[,rs[,rt[,ratio[,ir]]]]]", "**EndFEMtoIGA"],
     keys=[K("*IGA", "위 형식", "rr=rs=rt=0.6, ratio=1.1, ir=0", "파트별 한 줄. rr/rs/rt = 방향별 요소 크기 비, ratio = bbox 확장 배율, ir = 적분 규칙(0/1)")],
     examples=[Example("파트 1·3 을 IGA 로", _opt("MinimumModel.k", "FEM_TO_IGA,22", """**FEMtoIGA,22
# PID 1 기본 옵션
*IGA,1,101,iga_part_01.k
# PID 3 요소 더 세밀하게
*IGA,3,103,iga_part_03.k,0.4,0.4,0.4
**EndFEMtoIGA"""),
                       explain=["`#` 줄은 주석. IGA 파일은 원본 .k 에 *INCLUDE 로 연결된다."],
                       verify={"mode": "FEM_TO_IGA", "id": 22, "expect": {"@len:IGAParts": 2, "IGAParts.1.element_edge_length": {"rr": 0.4, "rs": 0.4, "rt": 0.4},
                                                                  "IGAParts.0.bbox_offset_ratio": 1.1}})],
     related=["MERGE_K"])


# ━━ 접촉·검증 ━━
mode("CONTACT_AUTO_DECOMPOSITION", "큰 접촉을 근접 파트 쌍 접촉으로 자동 분해",
     category="접촉·검증", aliases=["contact", "접촉", "접촉분해", "cad"],
     when=["AUTOMATIC_SINGLE_SURFACE 하나를 파트쌍 접촉으로 쪼개 제어하고 싶을 때"],
     syntax=["**ContactAutoDecomposition,<ID>", "*SearchMarginX/Y/Z,<배율>",
             "*ContactKeyword", "<*CONTACT_... 카드 원문 — 분해된 접촉에 쓸 템플릿>", "**EndContactAutoDecomposition"],
     keys=[K("*SearchMarginX/Y/Z", "실수", "1.5", "근접 판정 bbox 여유 배율"),
           K("*ContactKeyword", "카드 블록", "-", "다음 줄의 *CONTACT 카드를 템플릿으로 사용")],
     examples=[Example("여유 1.5 배, SOFT=2 템플릿", _opt("MinimumModel.k", "CONTACT_AUTO_DECOMPOSITION,1", """**ContactAutoDecomposition,1
*SearchMarginX,1.5
*SearchMarginY,1.5
*SearchMarginZ,1.5
*ContactKeyword
*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID
$       ID                                                               heading
       CID                                                      Body Interaction
$     ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         0         0         3         3         0         0         0         0
$       fs        fd        dc        vc       vdc    penchk        bt        dt
       0.3         0         0         0        10         0         0     1e+20
$      sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
         1         1         0         0         1         1         1         1
**EndContactAutoDecomposition"""),
                       verify={"mode": "CONTACT_AUTO_DECOMPOSITION", "id": 1, "expect": {
                           "SearchMarginX": 1.5, "SearchMarginZ": 1.5,
                           "ContactKeyword.0": "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID", "ContactKeyword.3.0": "       0.3"}})],
     related=["REMOVE_DUPLICATE_TIED_CONTACTS", "DROP_ATTITUDE"])

mode("REMOVE_DUPLICATE_TIED_CONTACTS", "같은 면을 중복으로 묶은 TIED 접촉 제거",
     category="접촉·검증", aliases=["tied", "중복접촉", "rdc"],
     when=["임포트 과정에서 TIED 접촉이 중복돼 경고·과구속이 생길 때"],
     syntax=["**remove_duplicate_tied_contacts,<ID>", "remove_duplicate_tied_contacts,true", "**End"],
     keys=[K("remove_duplicate_tied_contacts", "true/false", "true", "켜기")],
     examples=[Example("중복 TIED 제거", _opt("MinimumModel.k", "REMOVE_DUPLICATE_TIED_CONTACTS,1", """**remove_duplicate_tied_contacts,1
remove_duplicate_tied_contacts,true
**End"""),
                       verify={"mode": "REMOVE_DUPLICATE_TIED_CONTACTS", "id": 1, "expect": {"RemoveDuplicateTiedContacts": True}})],
     related=["CONTACT_AUTO_DECOMPOSITION"])

mode("WEAK_COUPLING", "전체 모델 결과(d3plot) 경계 변위로 부분 모델 구동 (서브모델링)",
     category="접촉·검증", aliases=["submodel", "서브모델", "weak coupling", "경계조건", "wc"],
     when=["전체 해석 결과를 국부 상세 모델의 경계 조건으로 넘길 때"],
     syntax=["**WeakCoupling,<ID>", "FilePath,<전체모델 d3plot>", "Set,NodeSet|SegmentSet,<SID>",
             "BoundaryBox,xmin,xmax,ymin,ymax,zmin,zmax", "**End"],
     keys=[K("FilePath", "경로", "-", "전체 모델 d3plot"),
           K("Set", "NodeSet|SegmentSet,SID", "-", "경계 셋"),
           K("BoundaryBox", "6 실수", "없음", "경계 영역")],
     examples=[Example("노드셋 101 에 전체 해석 변위 부여", _opt("local.k", "WEAK_COUPLING,1", """**WeakCoupling,1
FilePath,/data/global/d3plot
Set,NodeSet,101
BoundaryBox,-10.0,10.0,-10.0,10.0,0.0,5.0
**End"""),
                       verify={"mode": "WEAK_COUPLING", "id": 1, "expect": {
                           "FilePath": "/data/global/d3plot", "Mode": "NodeSet", "SetID": 101,
                           "BoundaryBox": [-10.0, 10.0, -10.0, 10.0, 0.0, 5.0]}})],
     notes=["블록 안 키 판정이 부분 문자열(`set`)이라 FilePath 경로에 'set' 이 들어가도 FilePath 로 먼저 잡힌다 — FilePath 줄을 Set 줄보다 앞에 둘 것."])

mode("PART_VALIDATION_SPLIT", "파트별 독립 .k 분할 + 0° 낙하 검증 모델 일괄 생성",
     category="접촉·검증", aliases=["validation", "검증", "파트검증", "split", "pvsplit"],
     when=["전각도 낙하 전에 각 파트가 단독으로 해석이 끝나는지 사전 점검할 때"],
     syntax=["**PartValidationSplit,<ID>", "*Height,<mm>", "*tFinal,<s>", "*Dt,<s>", "*OutputDir,<폴더>",
             "*MinElements,<n>", "*ExceptPID,<pid...>", "**End"],
     keys=[K("*Height", "실수", "100", "낙하 높이"), K("*tFinal", "실수", "5e-4", "종료 시간"),
           K("*Dt", "실수", "1e-5", "출력 간격"), K("*OutputDir", "경로", "-", "분할 결과 폴더"),
           K("*MinElements", "정수", "-", "이보다 요소가 적은 파트 제외"),
           K("*ExceptPID", "정수 리스트", "[]", "제외 파트")],
     examples=[Example("파트별 100 mm 낙하 검증 세트", _opt("model.k", "PART_VALIDATION_SPLIT,1", """**PartValidationSplit,1
*Height,100.0
*tFinal,0.0005
*Dt,1e-05
*OutputDir,validation_output
*MinElements,10
*ExceptPID,99
**End"""),
                       explain=["결과 폴더에 파트별 .k, validation_manifest.json, run.sh (Slurm array).",
                                "보통은 KooChainRun prepare (mode: part_validation) 가 이 모드를 부른다."],
                       verify={"mode": "PART_VALIDATION_SPLIT", "id": 1, "expect": {
                           "height": 100.0, "tFinal": 0.0005, "dt": 1e-05, "output_dir": "validation_output",
                           "min_elements": 10, "except_pids": [99]}})],
     related=["DROP_ATTITUDE"])


# ━━ DOE·변환 ━━
mode("TRANSFORM", "모델 전체 이동·회전·스케일·미러",
     category="DOE·변환", aliases=["transform", "이동", "회전", "스케일", "미러", "mirror", "rotate", "translate"],
     when=["모델 전체 좌표를 바꿀 때 (적은 순서대로 누적 적용)"],
     syntax=["**Transform,<ID>", "Translation,dx,dy,dz", "Rotation,degX,degY,degZ",
             "VectorRotation,x,y,z", "VectortoVectorRotation,x1,y1,z1,x2,y2,z2", "Scale,sx,sy,sz",
             "Mirror,XY|YZ|XZ", "**EndTransform"],
     keys=[K("Translation", "3 실수", "-", "평행 이동"),
           K("Rotation", "3 실수(도)", "-", "원점 기준 X→Y→Z 회전"),
           K("VectorRotation", "3 실수", "-", "X 축을 이 벡터로 정렬"),
           K("VectortoVectorRotation", "6 실수", "-", "벡터1 → 벡터2 정렬"),
           K("Scale", "3 실수", "-", "원점 기준 배율"),
           K("Mirror", "XY|YZ|XZ", "-", "평면 대칭 + 요소 연결 순서 반전")],
     examples=[Example("10 mm 올리고 Z 축 90° 회전, 0.001 배(mm→m)", _opt("model.k", "TRANSFORM,1", """**Transform,1
Translation,0.0,0.0,10.0
Rotation,0.0,0.0,90.0
Scale,0.001,0.001,0.001
**EndTransform"""),
                       verify={"mode": "TRANSFORM", "id": 1, "expect": {
                           "@list": [["Translation", 0.0, 0.0, 10.0], ["Rotation", 0.0, 0.0, 90.0],
                                     ["Scale", 0.001, 0.001, 0.001]]}})],
     notes=["키는 Translation (Translate 아님 — Translate 는 무시된다)."],
     related=["PART_TRANSLATE"])

mode("PART_TRANSLATE", "특정 파트만 이동 (이동 유지 — 뒤 모드가 이동된 형상 사용)",
     category="DOE·변환", aliases=["part move", "파트이동", "partmove"],
     when=["조립 위치를 바꾼 뒤 같은 파일에서 바로 DROP_ATTITUDE 등을 돌릴 때"],
     syntax=["**PartTranslate,<ID>", "Translate,<pid>,<dx>,<dy>,<dz>", "**EndPartTranslate"],
     keys=[K("Translate", "pid,dx,dy,dz", "-", "파트별 한 줄. 5칸 미만이면 ValueError")],
     examples=[Example("파트 12 를 x+0.5 이동 후 낙하", _opt("model.k", "PART_TRANSLATE,1\nDROP_ATTITUDE,2", """**PartTranslate,1
Translate,12,0.5,0.0,0.0
**EndPartTranslate
**DropAttitude,2
EulerRolling,0
EulerPitching,0
EulerYawing,0
Height,1000
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
InitialAngularVelocityX,0
InitialAngularVelocityY,0
InitialAngularVelocityZ,0
OffsetDistance,0.05
Density,7.85e-09
YoungsModulus,200000.0
PoissonRatio,0.3
tFinal,0.003
dt,1e-05
DropSurface,Plane,300,300,20,30,30,2
**EndDropAttitude"""),
                       verify={"mode": "PART_TRANSLATE", "id": 1, "expect": {
                           "Translation": {12: {"X": 0.5, "Y": 0.0, "Z": 0.0}}}})],
     related=["TRANSLATION_DOE", "TRANSFORM", "DROP_ATTITUDE"])

mode("TRANSLATION_DOE", "파트 위치 DOE — 파트별 이동량 목록마다 .k 한 개씩 (원복)",
     category="DOE·변환", aliases=["translation doe", "위치doe", "이동doe"],
     when=["파트 위치를 여러 값으로 바꾼 모델 세트를 만들 때"],
     syntax=["**Translation_DOE,<ID>", "TranslationX,<pid>,<x0>,<x1>,...", "TranslationY,<pid>,...",
             "TranslationZ,<pid>,...", "**End"],
     keys=[K("TranslationX/Y/Z", "pid + 실수 리스트", "-", "i 번째 값끼리 케이스 i. 파트마다 세 줄")],
     examples=[Example("파트 100 을 x 0 / 5 두 케이스", _opt("MinimumModel.k", "TRANSLATION_DOE,1", """**Translation_DOE,1
TranslationX,100,0.0,5.0
TranslationY,100,0.0,0.0
TranslationZ,100,0.0,0.0
**End"""),
                       explain=["결과: MinimumModel_TranslationDOE_0.k, _1.k 와 MinimumModel_TranslationDOE.json."],
                       verify={"mode": "TRANSLATION_DOE", "id": 1, "expect": {
                           "Translation": {100: {"X": [0.0, 5.0], "Y": [0.0, 0.0], "Z": [0.0, 0.0]}}}})],
     notes=["옵션 블록은 *Mode 목록 바로 뒤, *End 앞에 둘 것 (*End 뒤 블록은 읽지 않는다)."],
     related=["PART_TRANSLATE", "PART_LOCATION_DOE"])

mode("PART_LOCATION_DOE", "파트 배치 DOE — 마스크 파트 안 격자/샘플 위치에 파트 배치",
     category="DOE·변환", aliases=["location doe", "배치doe", "위치", "sampling"],
     when=["부품을 기판(마스크) 위 여러 위치에 놓은 모델 세트를 만들 때"],
     syntax=["**PartLocationDOE,<ID>", "*PIDs,<pid...>", "*MaskPID,<pid>", "*dx/*dy/*dz,<간격>",
             "*nx/*ny/*nz,<개수>", "*Dilation,<n>", "*Sampling,<방법>,<샘플수>", "**EndPartLocationDOE"],
     keys=[K("*PIDs", "정수 리스트", "[]", "옮길 파트"), K("*MaskPID", "정수", "0", "배치 허용 영역 파트"),
           K("*ObstaclePID", "정수 리스트", "[]", "피할 파트"),
           K("*dx / *dy / *dz", "실수", "0", "격자 간격"), K("*nx / *ny / *nz", "정수", "10/10/0", "격자 수"),
           K("*Dilation", "정수", "1", "장애물 팽창"), K("*Sampling", "방법,샘플수", "-", "LatinHypercube 등")],
     examples=[Example("파트 1 을 파트 2 영역 안 LHS 100 위치", _opt("model.k", "PART_LOCATION_DOE,1", """**PartLocationDOE,1
*PIDs,1
*dx,0.5
*dy,0.5
*nx,10
*ny,10
*MaskPID,2
*Dilation,1
*Sampling,LatinHypercube,100
**EndPartLocationDOE"""),
                       verify={"mode": "PART_LOCATION_DOE", "id": 1, "expect": {
                           "PIDs": [1], "MaskPID": 2, "DX": 0.5, "NX": 10, "Dilation": 1,
                           "Sampling.Method": "LatinHypercube", "Sampling.NumberofSamples": 100}})],
     related=["TRANSLATION_DOE", "DIMENSIONAL_TOLERANCE"])


# ━━ k 파일 입출력 ━━
mode("DECOMPOSE_K", "모델을 그룹별 include 파일 세트로 분해 (master.k + groups/*.k)",
     category="k 파일", aliases=["decompose", "분해", "include", "split k", "그룹"],
     when=["큰 모델을 파트 그룹별 파일로 나눠 관리·교체할 때"],
     syntax=["**DecomposeK,<ID>", "Group,<그룹이름>,<파트이름 또는 glob>...", "GroupFromFile,<그룹이름>,<목록파일>",
             "OutputDir,<폴더>", "**End"],
     keys=[K("Group", "이름,멤버...", "-", "멤버는 PART 제목(이름). * ? [] 가 있으면 glob. 먼저 적은 그룹이 우선"),
           K("GroupFromFile", "이름,파일", "-", "파일에 멤버를 줄/쉼표로"),
           K("OutputDir", "경로", "-", "출력 폴더"),
           K("DefaultGroupName", "문자", "default", "어느 그룹에도 안 든 파트"),
           K("GroupsSubdir", "문자", "groups", "그룹 파일 하위 폴더"),
           K("SeparateMaterials", "True/False", "False", "그룹별 재료 분리"),
           K("SharedNodesPolicy", "duplicate 등", "duplicate", "그룹 경계 공유 절점 처리"),
           K("EmitGroupSets", "True/False", "True", "그룹 SET 출력"),
           K("ModelIndependentSplit", "True/False", "-", "controls.k 와 globals.k 분리"),
           K("GroupBoundaryPolicy", "inline 등", "inline", "그룹 간 요소 처리")],
     examples=[Example("하우징·배터리 두 그룹으로 분해", _opt("MinimumModel.k", "DECOMPOSE_K,1", """**DecomposeK,1
Group,housing,HOUSING*,COVER
Group,battery,BATTERY_CELL,BATTERY_CAN
OutputDir,decomposed_output
SharedNodesPolicy,duplicate
ModelIndependentSplit,True
**End"""),
                       explain=["결과: decomposed_output/master.k, controls.k, materials.k, groups/housing.k ... decompose_manifest.json",
                                "되돌리기는 master.k 를 *Inputfile 로 MERGE_K."],
                       verify={"mode": "DECOMPOSE_K", "id": 1, "expect": {
                           "Groups": [{"name": "housing", "patterns": ["HOUSING*"], "parts": ["COVER"]},
                                      {"name": "battery", "patterns": [], "parts": ["BATTERY_CELL", "BATTERY_CAN"]}],
                           "OutputDir": "decomposed_output", "ModelIndependentSplit": True}})],
     notes=["멤버는 PID 가 아니라 PART 제목과 비교한다.", "이 모드 블록은 빈 줄·`$` 줄을 건너뛴다."],
     related=["MERGE_K", "IMPORT_MERGE_K"])

mode("MERGE_K", "*INCLUDE 로 나뉜 모델을 한 .k 로 합침",
     category="k 파일", aliases=["merge", "병합", "합치기", "include", "all in one"],
     when=["include 트리를 한 파일로 만들어 전달·비교할 때"],
     syntax=["**MergeK,<ID>", "OutputFile,<출력.k>", "**End"],
     keys=[K("OutputFile", "경로", "-", "합친 결과 파일"),
           K("ForceInlineIGA", "True/False", "False", "IGA include 도 인라인"),
           K("ForceInlinePreserved", "True/False", "False", "*PreserveIncludes 대상도 인라인")],
     examples=[Example("include 트리를 한 파일로", _opt("model_with_includes.k", "MERGE_K,1", """**MergeK,1
OutputFile,model_all_in_one.k
ForceInlineIGA,False
**End"""),
                       verify={"mode": "MERGE_K", "id": 1, "expect": {
                           "OutputFile": "model_all_in_one.k", "ForceInlineIGA": False}})],
     related=["DECOMPOSE_K", "IMPORT_MERGE_K"])

mode("IMPORT_MERGE_K", "다른 .k 파일을 불러와 ID 충돌 없이 현재 모델에 합침",
     category="k 파일", aliases=["import", "가져오기", "파트추가", "imported"],
     when=["별도로 만든 파트(.k)를 기존 모델에 붙일 때"],
     syntax=["**ImportMergeK,<ID>", "ImportFile,<파일.k>", "**End"],
     keys=[K("ImportFile", "경로", "-", "붙일 .k (ID 는 자동 재번호)")],
     examples=[Example("new_part.k 를 base_model 에 합침", _opt("base_model.k", "IMPORT_MERGE_K,1", """**ImportMergeK,1
ImportFile,new_part.k
**End"""),
                       explain=["출력: base_model_imported.k"],
                       verify={"mode": "IMPORT_MERGE_K", "id": 1, "expect": {"ImportFile": "new_part.k"}})],
     related=["MERGE_K"])

mode("DYNAIN_TO_INITIAL", "이전 해석 dynain(변형 형상+응력)을 다음 해석 초기 상태로",
     category="k 파일", aliases=["dynain", "누적", "초기응력", "restart", "dti"],
     when=["누적 낙하처럼 앞 해석의 변형·응력을 이어받아 다음 해석을 만들 때"],
     syntax=["**DynainToInitial,<ID>", "*Key,Value", "**EndDynainToInitial"],
     keys=[K("*DynainPath", "경로", "dynain", "dynain 파일"),
           K("*IncludeStress", "True/False", "True", "응력도 이어받기"),
           K("*RemoveDynamicRelaxation", "True/False", "True", "기존 DR 카드 제거"),
           K("*DynamicRelaxation", "True/False", "False", "새 DR 추가 (Nrcyck/Tol/Fctr/Term 접미 키)"),
           K("*MovetoOriginAutomatic", "True/False", "False", "모델을 원점으로"),
           K("*MovetoOriginbyNode", "정수", "[]", "지정 절점 기준 원점 이동"),
           K("*RemovePartbyID / *RemovePartbyName", "리스트", "[]", "파트 제거 (바닥판 등)"),
           K("*RemoveContactbyID", "정수 리스트", "[]", "접촉 제거")],
     examples=[Example("dynain 응력 이어받고 바닥판(파트 23) 제거", _opt("drop_step1.k", "DYNAIN_TO_INITIAL,1", """**DynainToInitial,1
*DynainPath,dynain
*IncludeStress,True
*RemoveDynamicRelaxation,True
*MovetoOriginAutomatic,True
*RemovePartbyID,23
**EndDynainToInitial"""),
                       verify={"mode": "DYNAIN_TO_INITIAL", "id": 1, "expect": {
                           "DynainPath": "dynain", "IncludeStress": True, "MovetoOriginAutomatic": True,
                           "RemovePartIDList": [23]}})],
     related=["DROP_ATTITUDE"])


# ━━ 자동화 ━━
mode("SIMULATION_AUTOMATION", "시나리오 JSON 으로 여러 해석 모델을 일괄 생성",
     category="자동화", aliases=["automation", "자동화", "scenario", "json"],
     when=["웹 UI 등에서 만든 시나리오 JSON 을 받아 모델 세트를 만들 때"],
     syntax=["**SimulationAutomation,<ID>", "JsonFile,<시나리오.json>", "**EndSimulationAutomation"],
     keys=[K("JsonFile", "경로", "-", "시나리오 JSON")],
     examples=[Example("시나리오 JSON 실행", _opt("MinimumModel.k", "SIMULATION_AUTOMATION,1", """**SimulationAutomation,1
JsonFile,scenarios.json
**EndSimulationAutomation""", header="*RunDirectoryMode,True,Data/Results,Data/Metadata\n"),
                       verify={"mode": "SIMULATION_AUTOMATION", "id": 1, "expect": {"JsonFile": "scenarios.json"}})],
     notes=["클러스터 누적·DOE 해석은 KooChainRun 시나리오가 표준이다."])


CATALOG = Catalog(
    tool="KooMeshModifier",
    tagline="LS-DYNA .k 모델을 옵션 파일대로 수정·생성 (낙하·충격 덱, 파트/재료 교체, DOE, 분해·병합)",
    usage=["KooMeshModifier <옵션파일.txt> [작업폴더]",
           "KooMeshModifier --help [모드 또는 검색어]"],
    overview=["옵션 파일은 CSV 가 아니라 *Inputfile / *Mode / **<블록>,<ID> 구조다 (--help format).",
              "처음이면  --help format  →  --help <모드>  의 사례를 그대로 복사해 값만 바꿀 것."],
    modes=MODES, topics=TOPICS,
    footer=["KooMeshModifier --help format                 옵션 파일 구조·실행·출력",
            "KooMeshModifier --help chain                  여러 모드 연쇄"],
)
