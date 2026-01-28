# occProject/Generators 디렉토리 구조 개요

## 1. 전체 개요

`occProject/Generators` 디렉토리는 LS-DYNA 모델 자동화를 위한 종합 프레임워크입니다.

### 구성 요소
- **27개 최상위 Python 파일**: CAD/CAE 모델링 및 시뮬레이션 자동화
- **KooCAEManager/ 서브디렉토리**: 40개 이상의 핵심 CAE 관리 모듈
- **KooODBCADManager/ 서브디렉토리**: ODB/PCB 전용 CAD 작업
- **KooAnalysisWeb/ 서브디렉토리**: 웹 기반 분석 도구

---

## 2. 최상위 Python 파일 목록

### 2.1 핵심 시뮬레이션/메시 도구

| 파일명 | 크기 | 설명 |
|--------|------|------|
| **KooMeshModifier.py** | 128 KB | 핵심 LS-DYNA 모델 수정 도구 (21개 변환 모드) |
| KooSimulationGenerator.py | - | 시뮬레이션 생성 및 메시 조작 기본 클래스 |
| KooImpactSimulationGenerator.py | 45 KB | 충격/낙하 시험 시뮬레이션 설정 |
| KooThreePointBendingSimulationGenerator.py | 57 KB | 3점 굴곡 시험 시뮬레이션 |
| KooWearSimulationGenerator.py | - | 마모 시뮬레이션 생성 |
| KooMultiscaleGenerator.py | - | 멀티스케일 모델 생성 |

### 2.2 CAD 모델링 도구

| 파일명 | 크기 | 설명 |
|--------|------|------|
| KooAutomatedModeller.py | 33 KB | 메인 자동화 CAD 모델링 GUI |
| KooCADSimple.py | 21 KB | 간소화된 CAD 작업 |
| KooCADPlaneModellingWindow.py | 63 KB | 평면/레이어 기반 모델링 |
| KooCADStackModellingWindow.py | 88 KB | 스택/조립체 모델링 |
| KooCADMultiscaleModelWindow.py | 93 KB | 멀티스케일 CAD 인터페이스 |
| KooCADCAEView.py | 5 KB | CAD/CAE 시각화 뷰 |

### 2.3 UI 및 다이얼로그 컴포넌트

| 파일명 | 설명 |
|--------|------|
| KooBooleanOperatorWidget.py | 부울 연산 인터페이스 |
| KooPropertyWidget.py (18 KB) | 기하/조작기 속성 패널 |
| KooPopupDialog.py | 팝업 다이얼로그 |
| KooImportImageDialog.py | 이미지 가져오기 인터페이스 |
| KooLayerDialog.py | 레이어 구성 다이얼로그 |
| KooLayerPropertyDialog.py | 레이어 속성 편집기 |
| KooPolyLineGeneratorfromCellWidget.py | 셀에서 폴리라인 생성 |

### 2.4 분석 및 후처리

| 파일명 | 크기 | 설명 |
|--------|------|------|
| KooPostProcessor.py | 87 KB | 결과 후처리 및 시각화 |
| KooPostProcessManager.py | 8 KB | 후처리 관리 |
| KooDynaDOEManager.py | 62 KB | LS-DYNA용 실험 설계(DOE) |
| KooDynaDOEManagerprev.py | - | 이전 DOE 관리자 버전 |

### 2.5 시뮬레이션 관리

| 파일명 | 설명 |
|--------|------|
| KooRunSimulationManager.py | 시뮬레이션 실행 관리자 |
| KooOptimizer.py (6 KB) | 최적화 도구 |
| KooTester.py (8 KB) | 테스트 유틸리티 |
| KooTesterMultiscale.py | 멀티스케일 테스트 |

### 2.6 지원/유틸리티

| 파일명 | 설명 |
|--------|------|
| pyKooCADCAE.py (66 KB) | 핵심 CAD/CAE 기능 기본 모듈 |

---

## 3. KooCAEManager 서브디렉토리 (40+ 모듈)

### 3.1 핵심 데이터 관리

| 파일명 | 설명 |
|--------|------|
| KooNode.py | 노드 관리 및 작업 |
| KooElement.py | 요소 정의 및 속성 |
| KooPart.py | 파트 조립 및 관리 |
| KooMaterial.py | 재료 속성 데이터베이스 |
| KooSection.py | 섹션/속성 정의 |

### 3.2 분석 관련

| 파일명 | 설명 |
|--------|------|
| KooContact.py | 접촉 쌍 관리 |
| KooLoad.py | 경계 조건 및 하중 정의 |
| KooBoundaryNode.py | 구속 노드 관리 |
| KooDynaControl.py | 해석 제어 설정 |
| KooDynaResult.py | 결과 및 출력 관리 |
| KooDamping.py | 감쇠 정의 |

### 3.3 메시 및 기하

| 파일명 | 설명 |
|--------|------|
| KooMeshImporter.py | MSH/DYNA 파일 가져오기 |
| KooMeshManagerGMSH.py | GMSH 메시 생성 인터페이스 |
| KooWarpage.py | 휨/변형 처리 |
| KooGeometry.py | 기하 정의 |
| KooGeometryManager.py | 기하 관리자 |
| KooDynaAdvancedModification.py | 고급 메시/모델 변환 |

### 3.4 시각화 (AIS)

| 파일명 | 설명 |
|--------|------|
| KooAISGeometry.py | AIS 기하 객체 |
| KooAISGeometryManager.py | AIS 기하 관리자 |
| KooAISBoundary.py | AIS 경계 객체 |
| KooAISBoundaryManager.py | AIS 경계 관리자 |
| KooAISPreviewManager.py | AIS 미리보기 관리자 |

### 3.5 CAD/CAE 모델

| 파일명 | 설명 |
|--------|------|
| KooCAEModel.py | CAE 모델 데이터 구조 |
| KooCADCAEModel.py | CAD/CAE 통합 모델 |

---

## 4. 기술 스택

| 구분 | 기술 |
|------|------|
| 기본 프레임워크 | Python 3.x |
| CAD 커널 | OpenCASCADE (OCC) - PyOCC 바인딩 |
| GUI | PyQt5 |
| 메시 생성 | GMSH (gmsh-4.11.1) |
| FEA 파일 포맷 | LS-DYNA 키워드 포맷 (.k 파일) |
| 데이터 내보내기 | JSON 메타데이터, Nastran BDF, ABAQUS INP |

---

## 5. 클래스 상속 구조

```
KooMeshModifier (extends KooSimulationGenerator)
    ├── 부모: KooSimulationGenerator
    │   └── 관리: dynaImporter, curDir, addScriptList, IDs
    └── 주요 관리자: KooDynaAdvancedModification
```

### dynaImporter 하위 관리자 (12개)
1. NodeManager - 3D 좌표 노드 관리
2. ElementManager - 유한 요소 관리
3. PartManager - 파트 정의 관리
4. SectionManager - 요소 섹션 관리
5. MaterialManager - 재료 속성 관리
6. LoadManager - 경계 하중 관리
7. ContactManager - 접촉 정의 관리
8. BoundaryNodeManager - 구속 관리
9. SegmentSetManager - 표면 그룹 관리
10. KooControlManager - 시뮬레이션 제어 관리
11. KooDampingManager - 감쇠 관리
12. KooDynaResultManager - 결과 저장 관리

---

## 6. 데이터 흐름

```
설정 파일
    ↓
ImportOption() - 파서
    ↓
dynaImporter - 데이터 관리자
    ↓
Generate<Mode>() - 변환 로직
    ↓
WriteModifiedFile() - 내보내기
    ↓
출력 .k 파일
```
