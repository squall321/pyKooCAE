# occProject/Generators 파일 관계도

## 1. 전체 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            occProject/Generators                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         메인 실행 모듈                                   │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │ │
│  │  │ KooMeshModifier  │  │KooAutomatedModeller│  │ KooPostProcessor    │  │ │
│  │  │   (21 modes)     │  │     (CAD GUI)      │  │  (결과 후처리)       │  │ │
│  │  └────────┬─────────┘  └─────────┬──────────┘  └──────────┬─────────┘  │ │
│  └───────────┼──────────────────────┼──────────────────────────┼──────────┘ │
│              │                      │                          │             │
│              ▼                      ▼                          │             │
│  ┌────────────────────────────────────────────────────────────┼──────────┐ │
│  │                    시뮬레이션 생성기                          │           │ │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐  │           │ │
│  │  │ KooSimulationGenerator  │  │KooImpactSimulationGen   │  │           │ │
│  │  │      (기본 클래스)        │  │  (충격 시뮬레이션)       │  │           │ │
│  │  └───────────┬─────────────┘  └─────────────────────────┘  │           │ │
│  │              │                                              │           │ │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐  │           │ │
│  │  │ KooThreePointBending    │  │ KooMultiscaleGenerator  │  │           │ │
│  │  │ SimulationGenerator     │  │   (멀티스케일 모델)      │  │           │ │
│  │  └─────────────────────────┘  └─────────────────────────┘  │           │ │
│  └─────────────────────────────────────────────────────────────┼──────────┘ │
│                          │                                     │             │
│                          ▼                                     │             │
│  ┌─────────────────────────────────────────────────────────────┼──────────┐ │
│  │                     KooCAEManager/                           │           │ │
│  │                   (핵심 CAE 관리 모듈)                        │           │ │
│  │                                                              │           │ │
│  │  ┌──────────────────────────────────────────────────────┐   │           │ │
│  │  │                  KooDynaImporter                      │   │           │ │
│  │  │              (LS-DYNA 파일 관리 중앙)                   │   │           │ │
│  │  └────────────────────────┬─────────────────────────────┘   │           │ │
│  │                           │                                  │           │ │
│  │  ┌────────────────────────┼─────────────────────────────┐   │           │ │
│  │  │                 하위 관리자들                           │   │           │ │
│  │  │                                                        │   │           │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │   │           │ │
│  │  │  │ NodeManager │ │ElementManager│ │ PartManager │     │   │           │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘     │   │           │ │
│  │  │                                                        │   │           │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │   │           │ │
│  │  │  │MaterialManager│ │SectionManager│ │ LoadManager │   │   │           │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘     │   │           │ │
│  │  │                                                        │   │           │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │   │           │ │
│  │  │  │ContactManager│ │BoundaryNode │ │SegmentSet   │     │   │           │ │
│  │  │  │              │ │ Manager     │ │  Manager    │     │   │           │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘     │   │           │ │
│  │  │                                                        │   │           │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │   │           │ │
│  │  │  │ControlManager│ │DampingManager│ │ResultManager│    │   │           │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘     │   │           │ │
│  │  └────────────────────────────────────────────────────────┘   │           │ │
│  │                                                              │           │ │
│  │  ┌──────────────────────────────────────────────────────┐   │           │ │
│  │  │          KooDynaAdvancedModification                  │   │           │ │
│  │  │            (고급 모델 변환 로직)                         │◄──┘           │ │
│  │  └──────────────────────────────────────────────────────┘               │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 클래스 상속 관계

```
KooSimulationGenerator
    │
    ├── KooMeshModifier (21개 변환 모드)
    │
    ├── KooImpactSimulationGenerator (충격 시뮬레이션)
    │
    ├── KooThreePointBendingSimulationGenerator (3점 굴곡)
    │
    ├── KooWearSimulationGenerator (마모 시뮬레이션)
    │
    └── KooMultiscaleGenerator (멀티스케일)
```

---

## 3. KooMeshModifier 핵심 의존성

```
KooMeshModifier
    │
    ├── KooSimulationGenerator (부모 클래스)
    │       │
    │       └── dynaImporter : KooDynaImporter
    │               │
    │               ├── nodeMan : NodeManager
    │               ├── elemMan : ElementManager
    │               ├── partMan : KooPartManager
    │               ├── matMan : KooMaterialManager
    │               ├── secMan : KooSectionManager
    │               ├── loadMan : KooLoadManager
    │               ├── contactMan : KooContactManager
    │               ├── boundaryNodeMan : KooBoundaryNodeManager
    │               ├── segSetMan : KooSegmentSetManager
    │               ├── controlMan : KooControlManager
    │               ├── dampingMan : KooDampingManager
    │               └── dynaResultMan : KooDynaResultManager
    │
    └── advancedModification : KooDynaAdvancedModification
            │
            └── 21개 모드 실행 메서드
                    ├── WeakCoupling()
                    ├── DefeatureMesh()
                    ├── DropAttitude()
                    ├── Transform()
                    ├── DropWeightImpactTest()
                    ├── MaterialExchange()
                    ├── PartLocationDOE()
                    ├── ErodingMinDT()
                    ├── ConstrainedNodalRigidBodyToBeam()
                    ├── PartMorphing()
                    ├── WarpedPart()
                    ├── WarpedtoInitialStressPart()
                    ├── DimensionalTolerance()
                    ├── CohesiveBetweenConformalMeshes()
                    ├── DynaintoInitial()
                    ├── ContactAutoDecomposition()
                    ├── TranslationDOE()
                    ├── SimulationAutomation()
                    ├── RemoveDuplicateTiedContacts()
                    └── ConvertHexato()
```

---

## 4. KooCAEManager 모듈 관계

### 4.1 데이터 관리 모듈

```
┌───────────────────────────────────────────────────────────────┐
│                    데이터 관리 계층                             │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  KooNode.py                     KooElement.py                 │
│  ┌─────────────────┐           ┌─────────────────┐           │
│  │ class Node      │◄──────────│ class Element   │           │
│  │ class NodeManager│           │ class ElementMgr│           │
│  │ class NodeSet    │           │ class ElemSet   │           │
│  │ class NodeSetMgr │           │                  │           │
│  └─────────────────┘           └─────────────────┘           │
│           │                            │                       │
│           └──────────┬─────────────────┘                       │
│                      ▼                                         │
│              KooPart.py                                        │
│              ┌─────────────────┐                               │
│              │ class Part      │                               │
│              │ class PartManager│                              │
│              └─────────────────┘                               │
│                      │                                         │
│           ┌──────────┼──────────┐                             │
│           ▼          ▼          ▼                             │
│  KooMaterial.py  KooSection.py  KooContact.py                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                 │
│  │ Material  │  │ Section   │  │ Contact   │                 │
│  │ Manager   │  │ Manager   │  │ Manager   │                 │
│  └───────────┘  └───────────┘  └───────────┘                 │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

### 4.2 I/O 및 변환 모듈

```
┌───────────────────────────────────────────────────────────────┐
│                     I/O 및 변환 계층                            │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  KooMeshImporter.py                                           │
│  ┌─────────────────────────────────────────────┐             │
│  │ class KooMSHImporter    (GMSH .msh 파일)     │             │
│  │ class KooDynaImporter   (LS-DYNA .k 파일)    │             │
│  └─────────────────────────────────────────────┘             │
│                      │                                         │
│                      ▼                                         │
│  KooDynaKeyword.py                                            │
│  ┌─────────────────────────────────────────────┐             │
│  │ LS-DYNA 키워드 파싱/생성                       │             │
│  │ parse_whole(), KooDynaInt(), KooDynaFloat() │             │
│  └─────────────────────────────────────────────┘             │
│                      │                                         │
│                      ▼                                         │
│  KooDynaAdvancedModification.py                               │
│  ┌─────────────────────────────────────────────┐             │
│  │ 21개 고급 변환 메서드                          │             │
│  │ WriteModifiedFile()                          │             │
│  └─────────────────────────────────────────────┘             │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

### 4.3 시각화 모듈 (AIS)

```
┌───────────────────────────────────────────────────────────────┐
│                   시각화 계층 (OpenCASCADE AIS)                 │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  KooAISGeometry.py                                            │
│  ┌─────────────────────────────────────────────┐             │
│  │ KooAISGeomVertex, KooAISGeomEdge            │             │
│  │ KooAISGeomWire, KooAISGeomFace              │             │
│  │ KooAISGeomShell, KooAISGeomSolid            │             │
│  │ KooAISGeomTextureBox                        │             │
│  └─────────────────────────────────────────────┘             │
│                      │                                         │
│                      ▼                                         │
│  KooAISGeometryManager.py                                     │
│  ┌─────────────────────────────────────────────┐             │
│  │ AddVertex(), AddEdge(), AddFace()            │             │
│  │ AddSolid(), RemoveSolid()                    │             │
│  │ Transform(), Display()                       │             │
│  └─────────────────────────────────────────────┘             │
│                      │                                         │
│                      ▼                                         │
│  KooAISBoundary.py / KooAISBoundaryManager.py                │
│  ┌─────────────────────────────────────────────┐             │
│  │ 경계 조건 시각화                               │             │
│  └─────────────────────────────────────────────┘             │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

---

## 5. 모드별 파일 의존성

### 5.1 DROP_ATTITUDE 모드

```
KooMeshModifier.py
    │
    ├── ImportOption()
    │       └── 파서: *DropAttitude 블록
    │
    ├── GenerateDropAttitude(modeid)
    │       │
    │       └── advancedModification.DropAttitude()
    │               │
    │               ├── KooMeshManagerGMSH (낙하면 메시 생성)
    │               ├── NodeManager (노드 변환)
    │               ├── ElementManager (요소 생성)
    │               ├── PartManager (파트 추가)
    │               ├── MaterialManager (재료 추가)
    │               ├── ContactManager (접촉 정의)
    │               └── BoundaryNodeManager (경계 조건)
    │
    └── WriteModifiedFile()
```

### 5.2 PART_EXCHANGE 모드

```
KooMeshModifier.py
    │
    ├── ImportOption()
    │       └── 파서: **PartExchange 블록
    │
    ├── GeneratePartExchange(modeid)
    │       │
    │       ├── ConvertHexato() [Shell/TShell/Solid 변환]
    │       │       │
    │       │       └── advancedModification.ConvertHexato()
    │       │               ├── 요소 타입 변환
    │       │               ├── 레이업 적용
    │       │               └── 메시 재구성
    │       │
    │       └── ConvertUnstructuredtoStructured() [비구조→구조 변환]
    │               │
    │               └── advancedModification.ConvertUnstructuredtoStructured()
    │                       ├── 메시 재생성
    │                       └── 노드 재배열
    │
    └── WriteModifiedFile()
```

### 5.3 DYNAIN_TO_INITIAL 모드

```
KooMeshModifier.py
    │
    ├── ImportOption()
    │       └── 파서: **DynainToInitial 블록
    │
    ├── GenerateDynainToInitial(modeid)
    │       │
    │       └── advancedModification.DynaintoInitial()
    │               │
    │               ├── dynain 파일 파싱
    │               │       └── KooDynaImporter 추가 인스턴스
    │               │
    │               ├── 노드 위치 업데이트
    │               │       └── NodeManager.UpdateNodePosition()
    │               │
    │               ├── 초기 응력 설정 (선택)
    │               │       └── KooInitialManager.AddInitialStress()
    │               │
    │               └── 동적 이완 제거 (선택)
    │                       └── ControlManager.RemoveDynamicRelaxation()
    │
    └── WriteModifiedFile()
```

---

## 6. 외부 라이브러리 의존성

```
┌─────────────────────────────────────────────────────────────────┐
│                        외부 라이브러리                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Python 표준 라이브러리                                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ os, sys, json, csv, copy, math, logging, pathlib, typing  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  과학 계산                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ numpy          - 수치 계산                                  │ │
│  │ scipy.spatial  - KDTree (공간 검색)                         │ │
│  │ scipy.stats    - truncnorm (절단 정규분포)                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  CAD 커널                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ OCC.Core.gp    - 기하 기본 요소 (gp_Pnt, gp_Vec, gp_Trsf)  │ │
│  │ OCC.Core.BRep  - B-Rep 기하                                │ │
│  │ OCC.Core.AIS   - 대화형 시각화                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  GUI                                                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ PyQt5          - GUI 프레임워크                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  메시 생성                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ gmsh           - GMSH 메시 생성기 API                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. 데이터 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            데이터 흐름                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐                                                           │
│  │ 설정 파일     │  Option.txt                                               │
│  │ (.txt)       │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                           │
│  │ ImportOption │  설정 파서                                                 │
│  │              │  - modeList, modeIDList, modeIDOption 생성                │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                           │
│  │ 입력 파일     │  *.k (LS-DYNA 키워드 파일)                                 │
│  │              │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                           │
│  │ImportBaseFile│  LS-DYNA 파일 로드                                        │
│  │              │  - dynaImporter에 모든 데이터 저장                         │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       dynaImporter (메모리)                            │  │
│  │  ┌──────┐ ┌────────┐ ┌──────┐ ┌────────┐ ┌─────────┐ ┌───────────┐  │  │
│  │  │Nodes │ │Elements│ │Parts │ │Materials│ │Sections │ │Contacts   │  │  │
│  │  └──────┘ └────────┘ └──────┘ └────────┘ └─────────┘ └───────────┘  │  │
│  │  ┌──────┐ ┌────────┐ ┌──────┐ ┌────────┐                            │  │
│  │  │Loads │ │Boundary│ │Sets  │ │Controls│                            │  │
│  │  └──────┘ └────────┘ └──────┘ └────────┘                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    GenerateModifiedFile()                             │  │
│  │                                                                        │  │
│  │  for each mode in modeList:                                           │  │
│  │      ┌──────────────────────────────────────────────────────────┐    │  │
│  │      │  Generate<ModeName>(modeid)                                │    │  │
│  │      │      │                                                      │    │  │
│  │      │      ▼                                                      │    │  │
│  │      │  advancedModification.<MethodName>()                       │    │  │
│  │      │      │                                                      │    │  │
│  │      │      ├── 데이터 읽기 (dynaImporter)                         │    │  │
│  │      │      ├── 변환 로직 실행                                     │    │  │
│  │      │      └── 데이터 쓰기 (dynaImporter 업데이트)                │    │  │
│  │      └──────────────────────────────────────────────────────────┘    │  │
│  │                                                                        │  │
│  │  dynaImporter.SyncronizeMaxID()                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                           │
│  │WriteModified │  결과 출력                                                 │
│  │    File()    │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐  ┌──────────────┐                                        │
│  │ 출력 파일     │  │ 메타데이터    │                                        │
│  │ *_suffix.k   │  │ *.json       │                                        │
│  └──────────────┘  └──────────────┘                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. GUI 모듈 관계 (KooAutomatedModeller)

```
KooAutomatedModeller.py (메인 윈도우)
    │
    ├── pyKooCADCAE.py (핵심 CAD/CAE 기능)
    │       │
    │       ├── KooCADCAEModel (데이터 모델)
    │       └── KooGeometryManager (기하 관리)
    │
    ├── KooCADCAEView.py (3D 뷰어)
    │       │
    │       ├── KooAISGeometryManager (시각화)
    │       └── KooCoordinate (좌표계/그리드)
    │
    ├── KooPropertyWidget.py (속성 패널)
    │       │
    │       ├── KooFaceGeometryWidget
    │       ├── KooSolidGeometryWidget
    │       └── KooManipulatorWidget
    │
    ├── 모델링 윈도우들
    │       │
    │       ├── KooCADPlaneModellingWindow.py (평면 모델링)
    │       ├── KooCADStackModellingWindow.py (스택 모델링)
    │       └── KooCADMultiscaleModelWindow.py (멀티스케일)
    │
    └── 다이얼로그들
            │
            ├── KooPopupDialog.py
            ├── KooLayerDialog.py
            ├── KooLayerPropertyDialog.py
            └── KooImportImageDialog.py
```
