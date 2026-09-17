# KooAutomatedModeller --help 카탈로그 — PKG·CAP·PCB·ArrayPCB·PBA·AIRMESH 입력 형식과 검증된 사례
"""
사례의 verify 는 tests/test_cli_help.py 가 각 모드의 실제 파서로 읽어 확인한다.
  {"parser": "pkg"|"cap"|"odb"|"airmesh", "expect": {"속성.경로": 값}}
"""

from .engine import Catalog, Example, Key, Mode, Topic

K = Key

TOPICS = [
    Topic("cli", "명령 형식 — 모드 이름은 대소문자 그대로", aliases=["사용법", "인자", "argv", "usage"], body=[
        "KooAutomatedModeller <모드> <입력파일> [작업폴더|None] [표시 True|False]",
        "",
        "  <모드>        PKG | CAPACITOR (=CAP) | PCB | ArrayPCB | PBA | AIRMESH   — 대소문자 구분 (pkg 는 안 됨)",
        "  <입력파일>    작업폴더 기준 상대경로",
        "  [작업폴더]    주면 그 폴더로 이동한 뒤 실행. None 이면 현재 폴더",
        "  [표시]        GUI 표시 여부. 서버에서는 항상 headless 라 무시해도 된다",
        "",
        "공통 규칙",
        "  - 입력 파일은 `키,값` 줄 형식 (AIRMESH 만 JSON). `#` 로 시작하는 줄은 주석.",
        "  - 블록 헤더는 `*` 로 시작 (*Layer, *Capacitor, *PCB, *ODB ...). 키 이름은 대소문자 구분·접두 일치.",
        "  - 파일 끝에 *End 를 둘 것 — PCB/ArrayPCB 파서는 *End 가 없으면 EOF 에서 멈추지 않는다.",
        "  - 모르는 모드 이름·입력 파일 없음·라이선스 게이트·최상위 키워드 오류·Evolver 실패는 종료 코드 1. *Layer 안의 모르는 키는 조용히 무시되므로 로그의 Complete/FAILED 와 산출물도 확인할 것 (AIRMESH 는 항상 0, report.json 의 status 로 판단).",
        "  - 실행 시 등록 IP·사용 기한(2027-12-31)을 확인한다. `Access denied` 면 그 머신에서는 실행되지 않는다 (종료 코드 1). 계산 노드 대역 192.168.122.x 는 허용.",
    ]),
    Topic("outputs", "모드별 산출물", aliases=["출력", "산출물", "output"], body=[
        "  PKG       메시 키워드가 없으면 <입력>.step, 첫 *Layer 에 MeshGenerationType 이 있으면 <입력>.k (LS-DYNA)",
        "  CAPACITOR STEP + (MeshSize 계열 키가 있으면) LS-DYNA 메시",
        "  PCB/ArrayPCB  PCB 형상 STEP",
        "  PBA       <입력>_total.step (+ ExportPackage,True 면 패키지별 .txt/STEP 폴더)",
        "  AIRMESH   <prefix>_air.stl / _cavity.stl / _outer_box.stl / _air.msh / _report.json (prefix 기본 = JSON 파일명)",
    ]),
]

MODES = []


def mode(*a, **kw):
    MODES.append(Mode(*a, **kw))


PKG_STEP = """*Translation,0.0,0.0,0.0
*Rotation,0
*Mirror,False
*IsTop,True
*Layer,Substrate
Location,0,0,0
Length,10.0,8.0
Thickness,0.3
*Layer,Die
Location,0,0
Length,6.0,5.0
Thickness,0.2
*End"""

PKG_MESH = """*Layer,PCB
Location,0,0,0
Length,10.0,10.0
Thickness,0.5
MeshGenerationType,Solid,Hexa
MeshPath,PackageMesh
MeshSizeInPlane,1.0
NumberofElementinThickness,2
MaterialID,1
*Layer,Mold
Location,0,0
Length,6.0,6.0
Thickness,0.4
MeshGenerationType,Solid,Hexa
MeshPath,PackageMesh
MeshSizeInPlane,1.0
NumberofElementinThickness,2
MaterialID,2
*End"""

PKG_CONFORMAL = """*Layer,PCB
Location,0,0,0
Length,10.0,10.0
Thickness,0.5
MeshGenerationType,Solid,ConformalHexa
MeshSizeInPlane,0.5
NumberofElementinThickness,3
MeshPath,./conformal_mesh_output
*Layer,SolderJoint
Location,0,0
Length,6.0,6.0
Thickness,0.12
MeshGenerationType,Solid,ConformalHexa
MeshSizeInPlane,0.3
NumberofElementinThickness,2
MeshPath,./conformal_mesh_output
Cylinder,-2.0,2.0,0.11
Cylinder,0.0,2.0,0.11
Cylinder,2.0,2.0,0.11
*End"""

mode("PKG", "적층(Layer) 정의 텍스트로 반도체 패키지 형상(STEP) 또는 LS-DYNA 메시(.k) 생성",
     category="패키지·부품", aliases=["package", "패키지", "layer", "적층", "bga", "솔더볼", "conformal"],
     when=["기판·다이·몰드 같은 층과 솔더볼(Cylinder)·패드(Box)를 쌓아 패키지 모델을 만들 때",
           "PBA 모드가 내보낸 패키지별 .txt (ExportPackage) 를 개별 모델로 만들 때"],
     syntax=["[*Translation,x,y,z] [*Rotation,deg] [*Mirror,True|False] [*IsTop,True|False]",
             "*Layer,<이름>[,Defined|Warped|SolderJointWarped]", "키,값 ...", "*Layer,<다음 층> ...",
             "[*Material  다음 줄에 재료 파일]", "*End"],
     keys=[
         K("*Layer", "이름[,genMode]", "Defined", "층 시작. 층은 적은 순서대로 아래에서 위로 쌓인다"),
         K("Location", "x,y[,z]", "-", "층 위치. z 를 생략하면 앞 층 위(누적 두께)에 쌓는다"),
         K("Length", "xLen,yLen[,matID]", "-", "층 평면 크기"),
         K("Thickness", "실수", "-", "층 두께 (누적 z 에 더해짐)"),
         K("MaterialID", "정수", "-", "층 재료 ID"),
         K("MeshGenerationType", "Solid|Shell[,Hexa|Tetra|ConformalHexa]", "끔 (Hexa)", "있으면 STEP 대신 메시(.k). 판정은 첫 *Layer 기준"),
         K("MeshSizeInPlane", "실수", "-", "면내 요소 크기"),
         K("NumberofElementinThickness", "정수", "-", "두께 방향 요소 수"),
         K("NumberofElementinXDirection / YDirection", "정수", "-", "Hexa 면내 분할 수 직접 지정"),
         K("MeshPath", "폴더", "-", "gmsh 중간 파일 폴더"),
         K("ConformalBufferThickness", "실수", "-", "ConformalHexa 인접 층 사이 Tetra 버퍼 두께"),
         K("Cylinder", "x,y,r[,Shell|Solid|Composite][,matID]", "-", "원통 피처 (솔더볼 등) — 층 안에 여러 줄"),
         K("Box", "x,y,xLen,yLen[,...]", "-", "사각 피처. x,y 는 모서리 시작점 (꼭짓점 2쌍 아님)"),
         K("SurfaceTension / MisalignmentAngle / SMD / NSMD", "-", "-", "SolderJoint 층 전용 형상 키"),
         K("*Material", "다음 줄 = 파일", "-", "재료 정의 파일 (입력 파일과 같은 폴더)"),
     ],
     examples=[
         Example("기판 + 다이 2층 STEP (메시 키 없음)", PKG_STEP,
                 explain=["실행: KooAutomatedModeller PKG pkg_step.txt → pkg_step.step"],
                 verify={"parser": "pkg", "expect": {
                     "@len:layerList": 2, "layerList.0.name": "Substrate", "layerList.1.name": "Die",
                     "layerList.0.meshGenerationMode": False, "layerList.1.thickness": 0.2}}),
         Example("PCB + 몰드 Hexa 메시 → LS-DYNA .k", PKG_MESH,
                 explain=["실행: KooAutomatedModeller PKG pkg_mesh.txt → pkg_mesh.k"],
                 verify={"parser": "pkg", "expect": {
                     "@len:layerList": 2, "layerList.0.meshGenerationMode": True,
                     "layerList.0.meshType": "Hexa", "layerList.1.name": "Mold"}}),
         Example("PCB + 솔더볼 3개 ConformalHexa (절점 공유 메시)", PKG_CONFORMAL,
                 explain=["ConformalHexa 는 층 경계에서 절점을 공유하도록 통합 메시를 만든다. 볼 수·면내 크기에 따라 .k 가 급격히 커진다."],
                 verify={"parser": "pkg", "expect": {
                     "@len:layerList": 2, "layerList.1.name": "SolderJoint",
                     "layerList.1.meshType": "ConformalHexa"}}),
     ],
     notes=["메시/STEP 분기는 첫 *Layer 의 MeshGenerationType 유무로만 정해진다 — 층마다 섞지 말 것.",
            "PKG 메시 출력은 LS-DYNA .k 만 (Nastran/ANSYS/ABAQUS 출력은 꺼져 있음)."],
     related=["PBA", "CAPACITOR"])

CAP_TEXT = """*Capacitor,C0603
Location,0.0,0.0,0.0
Rotation,0
Mirror,False
IsTop,True
XSize,600
YSize,300
ZSize,300
Ndi,27
tdi,5
tel,6
epsilon,1660
ldi,170
swr,0.6
str,0.7
sbr,0.6
MeshPath,PackageInfoCap
MeshSize,40
MeshSizeSolder,20
MeshSizeBody,20
NumberofElementMLCC,20,10,3
MaterialID,Solder,5
MaterialID,CeramicBody,8
*End"""

mode("CAPACITOR", "MLCC 칩 커패시터(패드·터미널·솔더·유전체 적층) 형상과 메시 생성",
     category="패키지·부품", aliases=["CAP", "mlcc", "커패시터", "캐패시터", "chip"],
     when=["0603·1005 같은 MLCC 를 솔더 필렛·내부 전극까지 모델링할 때",
           "압전 재료·전압 곡선을 붙인 MLCC 진동(어쿠스틱 노이즈) 모델이 필요할 때"],
     syntax=["*Capacitor[,이름]", "키,값 ...", "[**addscript,LSDyna … **endscript]", "*End"],
     keys=[
         K("Location / Translation", "x,y,z", "0,0,0", "배치 원점"),
         K("Rotation / Mirror / IsTop", "도 / True|False / True|False", "0/False/True", "배치 방향"),
         K("XSize / YSize / ZSize", "실수", "-", "칩 외형 (예제 단위 µm). YSize 만 주면 ZSize 도 같음"),
         K("Ndi / tdi / tel / epsilon / ldi", "수", "-", "유전체 층 수·두께, 전극 두께, 비유전율, 마진 → 정전용량 계산"),
         K("swr / str / sbr / tens / sg / tilt", "실수", "-", "솔더 폭·두께·하단 비율, 표면장력, Evolver SG, 기울기"),
         K("lpw lph rpw rph piw pt cbw cbh cbt ...", "실수", "-", "패드·바디·터미널·배리어·피니시·솔더 세부 치수 약어"),
         K("MeshSize / MeshSizeSolder / MeshSizeBody", "실수", "-", "하나라도 있으면 메시 생성"),
         K("NumberofElementMLCC", "nx,ny,nz", "-", "MLCC 바디 분할"),
         K("MeshPath", "폴더", "-", "메시 중간 파일 폴더"),
         K("MaterialID", "<부위>,<id>", "Pad1 Terminal2 Barrier3 Finish4 Solder5 Dielectric6 Electrode7 CeramicBody8", "부위별 재료 ID"),
         K("dxx…dyz / px11… / py11… / pz11…", "실수", "-", "압전 유전·압전 행렬 성분"),
         K("LeftVoltageValue / RightVoltageValue", "실수", "-", "좌우 전압 상수"),
         K("LeftVoltageCurve / RightVoltageCurve … End", "시간,전압 줄", "-", "좌우 전압 곡선 (End 가 든 줄에서 끝)"),
     ],
     examples=[Example("0603 MLCC 메시", CAP_TEXT,
                       explain=["실행: KooAutomatedModeller CAP cap0603.txt",
                                "같은 키를 두 번 쓰면 뒤 값이 이긴다."],
                       verify={"parser": "cap", "expect": {
                           "@len:capacitors": 1, "capacitors.1.name": "C0603", "capacitors.1.meshSize": 40.0}})],
     notes=["Surface Evolver 는 작업 폴더 Library/Evolver → 상위 폴더 → PATH → 설치본(SIF 의 /opt/SmartTwinPreprocessor/Library/Evolver) 순으로 찾고, 작업 폴더에 Library/Evolver/evolver 링크를 만들어 거기서 계산한다. 못 찾으면 종료 코드 1.",
            "산출물: <이름>_detail.step 등 STEP + PackageInfoCap 폴더 메시"],
     related=["PKG"])

ODB_PCB = """*PCB
FileName,feature.txt
Location,0.0,0.0,0.0
Rotation,90
Mirror,True
Layup,CUPPGCOMP,PPGT2,CUPPG2
Thickness,2.0E-05,3.0E-05,1.2E-05
MaterialFileName,MAT_EM370Z.txt
PatternFeatures,./steps/pcb/layers/comp/features,CUPPGCOMP
PatternFeatures,./steps/pcb/layers/l2/features,CUPPG2
SymbolsFolder,symbols
Warpage,None
*End"""

ODB_ARRAY = """*ArrayPCB
FileName,ArrayFeature.txt
Location,0.0,0.0,0.0
Rotation,0
Mirror,False
Layup,CUPPGCOMP,PPGT2,CUPPG2
Thickness,2.0E-05,3.0E-05,1.2E-05
MaterialFileName,MAT_EM370Z.txt
PatternFeatures,./steps/array/layers/comp/features,CUPPGCOMP
SymbolsFolder,symbols
Warpage,ArrayWarpage.txt
*End"""

PCB_KEYS = [
    K("FileName", "파일", "-", "ECAD 외곽 피처 파일"),
    K("Location", "x,y,z", "-", "배치 위치"),
    K("Rotation", "정수(도)", "-", "회전"),
    K("Mirror", "True|False", "False", "정확히 True 일 때만 미러"),
    K("Layup", "층 이름...", "-", "위→아래 층 이름 목록"),
    K("Thickness", "실수...", "-", "층별 두께 (m). 내부에서 ×1000 → mm"),
    K("MaterialFileName", "파일", "-", "재료 파일"),
    K("PatternFeatures", "폴더,층이름", "-", "층별 패턴 피처 폴더 (층마다 한 줄)"),
    K("SymbolsFolder", "폴더", "-", "ODB++ symbols 폴더"),
    K("Warpage", "None|파일", "-", "None = 평판, 파일 = 워피지 반영"),
]

mode("PCB", "ODB++ 추출 피처로 다층 PCB 형상(STEP) 생성",
     category="PCB·PBA", aliases=["pcb", "기판", "odb", "layup"],
     when=["ECAD(ODB++) 에서 뽑은 층별 패턴으로 PCB 동박·프리프레그 적층 형상을 만들 때"],
     syntax=["*PCB", "키,값 ...", "*End"],
     keys=PCB_KEYS,
     examples=[Example("3층 PCB, 90° 회전·미러, 평판", ODB_PCB,
                       explain=["실행: KooAutomatedModeller PCB pcb.txt  (FileName·PatternFeatures 경로의 ODB 추출 파일이 있어야 한다)"],
                       verify={"parser": "odb", "expect": {
                           "PCBFileList": ["feature.txt"], "PCBRotationList": [90], "PCBMirrorList": [True],
                           "PCBLayupList": [["CUPPGCOMP", "PPGT2", "CUPPG2"]],
                           "PCBThicknessList": [[0.02, 0.03, 0.012]], "PCBWarpageList": ["None"]}})],
     notes=["Thickness 는 m 로 넣는다 (×1000 해서 mm 로 쓴다).", "파일 끝 *End 필수 (없으면 파서가 끝나지 않는다)."],
     related=["ArrayPCB", "PBA"])

mode("ArrayPCB", "어레이(판넬) PCB 형상 생성 — *PCB 와 같은 키, 워피지 파일 지원",
     category="PCB·PBA", aliases=["array", "판넬", "panel", "어레이"],
     when=["여러 개가 배열된 판넬 PCB 를 한 번에 만들 때"],
     syntax=["*ArrayPCB", "키,값 ... (PCB 모드와 같은 키)", "*End"],
     keys=PCB_KEYS,
     examples=[Example("어레이 PCB + 워피지", ODB_ARRAY,
                       explain=["실행: KooAutomatedModeller ArrayPCB array.txt"],
                       verify={"parser": "odb", "expect": {
                           "PCBArrayFileList": ["ArrayFeature.txt"], "PCBArrayMirrorList": [False],
                           "PCBArrayThicknessList": [[0.02, 0.03, 0.012]], "PCBArrayWarpageList": ["ArrayWarpage.txt"]}})],
     notes=["모드 이름은 정확히 ArrayPCB (대소문자 구분).", "파일 끝 *End 필수."],
     related=["PCB"])

ODB_PBA = """*ODB
ODBFile,P3_EUR_REV03.zip
ZLocation,0.0000
Thickness,2.5e-5,3.1e-5,1.5e-5,3.1e-5,1.5e-5
ThicknessSolderPaste,1.5e-5
ThicknessSolderMask,1.5e-5
MinimumSize,0.005
BoundaryBox,0.025,0.005,0.03,0.01
DetailPAD,ALL
ExportPackage,True,PackageExported
*End"""

mode("PBA", "ODB++ 압축파일(.zip/.tgz)에서 PCB + 부품 실장 보드(PBA) 전체 형상 생성",
     category="PCB·PBA", aliases=["pba", "보드", "odb++", "ecad", "실장"],
     when=["ODB++ 로 받은 보드 전체를 STEP 으로 만들 때",
           "부품별 패키지 정의(.txt)를 뽑아 PKG 모드로 개별 모델링할 때 (ExportPackage)"],
     syntax=["*ODB", "키,값 ...", "*End"],
     keys=[
         K("ODBFile", "파일", "-", "ODB++ 압축 파일"),
         K("ZLocation", "실수", "-", "보드 기준 z"),
         K("Thickness", "실수...", "-", "층별 두께 (m, ×1000)"),
         K("ThicknessSolderPaste / ThicknessSolderMask", "실수", "-", "솔더 페이스트·마스크 두께 (m, ×1000)"),
         K("MinimumSize", "실수", "-", "이보다 작은 형상 무시 (m, ×1000)"),
         K("BoundaryBox", "xmin,ymin,xmax,ymax", "없음", "이 영역만 상세 모델링 (m, ×1000)"),
         K("DetailPAD", "이름|ALL", "-", "상세 PAD"),
         K("ExportPackage", "True|False[,폴더]", "False, PackageExported", "부품별 패키지 .txt 내보내기"),
         K("SkipLayer", "층 이름", "-", "건너뛸 층 (여러 줄)"),
         K("PKG", "부품명,패키지명", "-", "사용자 패키지 매핑"),
         K("UndefinedUnitAmps", "실수", "25.4", "단위 미정 값 배율"),
     ],
     examples=[Example("보드 일부 영역 상세 + 패키지 내보내기", ODB_PBA,
                       explain=["실행: KooAutomatedModeller PBA pba.txt → pba_total.step, PackageExported/*.txt"],
                       verify={"parser": "odb", "expect": {
                           "ODBFile": ["P3_EUR_REV03.zip"], "detailOption": True, "exportPKGOption": True,
                           "exportPKGFolderName": "PackageExported", "thicknessSolderPaste": 0.015,
                           "detailPADName": {"ALL": 1}}})],
     notes=["ThicknessSolderPaste 는 Thickness 보다 먼저 판정되므로 줄 순서는 상관없다.",
            "길이 값은 m 단위로 넣고 내부에서 mm 로 바꾼다."],
     related=["PKG", "PCB"])

mode("AIRMESH", "STEP 솔리드 주변 공기 영역을 경계 추종 사면체로 채우고 STL 스킨 추출",
     category="메시", aliases=["air", "공기", "airmesh", "음향", "cfd", "stl"],
     when=["하우징·부품 주변 공기(음향·열·유동)용 체적 메시와 경계 STL 이 필요할 때"],
     syntax=["JSON 파일", '{"airmesh_version": 1, "input_step": "<STEP>", "mesh_size": <h>, ...}'],
     keys=[
         K("airmesh_version", "1", "-", "형식 버전", True),
         K("input_step", "경로", "-", "STEP 파일 (JSON 파일 위치 기준)", True),
         K("mesh_size", "실수", "-", "목표 요소 크기 (모델 단위)", True),
         K("padding", "실수 | [x-,x+,y-,y+,z-,z+]", "-", "솔리드 bbox 에서 공기 박스까지 여유"),
         K("units", "문자", "mm", "리포트 표기용 단위 이름 (변환 안 함)"),
         K("occ_target_unit", "MM|M 등", "\"\"", "지정 시 STEP 을 이 단위로 리스케일"),
         K("solid_selection", "all | [1-based 인덱스]", "all", "빼낼 솔리드. 미선택 솔리드는 공기에 흡수"),
         K("heal", "auto|on|off", "auto", "형상 치유"),
         K("mesh.algorithm3d / mesh.optimize / mesh.max_estimated_elements", "-", "hxt / true / 5e7", "gmsh 세부"),
         K("outputs.prefix / outputs.dir", "문자", "JSON 파일명 / 작업폴더", "산출물 이름·폴더"),
     ],
     examples=[Example("구·원통 솔리드 주변 15 mm 여유, 4 mm 사면체", """{
  "airmesh_version": 1,
  "input_step": "sphere_cyl.stp",
  "mesh_size": 4.0,
  "units": "mm",
  "padding": 15.0
}""",
                       explain=["실행: KooAutomatedModeller AIRMESH airmesh.json <출력폴더>",
                                "성공 판정: <prefix>_report.json 의 status 가 ok (종료 코드는 항상 0).",
                                "골든 예제: pyKooCAE/Examples/automatedmodeller/airmesh_sphere/"],
                       verify={"parser": "airmesh", "expect": {
                           "errors": [], "cfg.mesh_size": 4.0, "cfg.padding": 15.0, "cfg.solid_selection": "all",
                           "cfg.outputs.prefix": "airmesh"}})],
     notes=["모든 padding 을 0 으로 주면 공기가 0 이라 E_BOOLEAN 으로 실패한다.",
            "미세 형상(ECAD 등)은 mesh_size 가 작으면 요소가 폭증한다 — size_guard 가 막는다."],
     related=["PKG"])


CATALOG = Catalog(
    tool="KooAutomatedModeller",
    tagline="패키지·MLCC·PCB·PBA 형상(STEP)/메시(.k) 생성 + STEP 주변 공기 메시",
    usage=["KooAutomatedModeller <모드> <입력파일> [작업폴더|None] [True|False]",
           "KooAutomatedModeller --help [모드 또는 검색어]"],
    overview=["모드 이름은 대소문자 그대로 (PKG, CAPACITOR/CAP, PCB, ArrayPCB, PBA, AIRMESH).",
              "성패는 종료 코드와 함께 로그·산출물로 확인 (--help cli)."],
    modes=MODES, topics=TOPICS,
    footer=["KooAutomatedModeller --help cli                명령 형식·공통 규칙",
            "KooAutomatedModeller --help outputs            모드별 산출물"],
)
