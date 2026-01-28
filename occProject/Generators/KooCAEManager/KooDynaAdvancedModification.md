# KooDynaAdvancedModification

LS-DYNA 키워드 파일의 고급 수정 기능을 제공하는 클래스입니다.

## 클래스 개요

```python
class KooDynaAdvancedModification:
    def __init__(self, dynaImporter: KooDynaImporter)
```

`KooDynaImporter` 객체를 받아서 다양한 메시 변환, 시뮬레이션 설정, 재료 교체 등의 작업을 수행합니다.

---

## 주요 메서드

### 파일 출력

| 메서드 | 설명 |
|--------|------|
| `WriteModifiedFile(filePath, modifiedKeyword="", copytoOutputFolder=False)` | 수정된 DYNA 키워드 파일을 저장 |

---

### 약결합 및 외부 결과 처리

| 메서드 | 설명 |
|--------|------|
| `WeakCoupling(option)` | 외부 DYNA 결과(d3plot)를 읽어서 변위 경계조건으로 적용 |

---

### 메시 변환 (Defeature / Convert)

| 메서드 | 설명 |
|--------|------|
| `DefeatureMesh(option)` | 메시 단순화 (요소 병합, 노드 제거 등) |
| `ConvertUnstructuredtoStructured(option)` | 비정형 메시를 정형 메시로 변환 |
| `ConvertHexato(option, layupList=[], curOption=None, filePath=None)` | Hexa 요소 변환 |
| `ConvertSolidtoStructuredSolidwithZSlack(part, dirVector, toleranceAngle, curOption, filePath)` | 솔리드를 Z방향 슬랙이 있는 정형 솔리드로 변환 |
| `ConvertSolidtoSolidwithSlack(part, dirVector, toleranceAngle, layupList, option, filePath)` | 솔리드를 슬랙이 있는 솔리드로 변환 |
| `ConvertSolidtoSolidComp(part, dirVector, toleranceAngle, layupList)` | 솔리드를 복합재 솔리드로 변환 |
| `ConvertSolidtoTShell(part, dirVector, toleranceAngle)` | 솔리드를 TShell로 변환 |
| `ConvertSolidtoShell(part, dirVector, toleranceAngle)` | 솔리드를 Shell로 변환 |
| `ConvertParttoPartComp(partCompKeyword)` | Part를 Part_Composite로 변환 |

---

### 시뮬레이션 제어 설정

| 메서드 | 설명 |
|--------|------|
| `SetControlandDatabaseExplicit(tFinal, dt)` | Explicit 해석용 Control 및 Database 설정 |
| `ErodingMinDT(dt)` | Eroding 요소의 최소 시간 간격 설정 |

---

### 낙하/충격 시험 설정

| 메서드 | 설명 |
|--------|------|
| `DropAttitude(option, filePath)` | 낙하 자세 설정 |
| `DropWeightImpactTest(option, filePath)` | 낙하 충격 시험 설정 |
| `DropWeightImpactTestwithPartialRigid(option, filePath)` | 부분 강체를 포함한 낙하 충격 시험 |
| `DropWeightImpactTestbyPart(option, filePath)` | Part 단위 낙하 충격 시험 |

---

### 형상 생성

| 메서드 | 설명 |
|--------|------|
| `CreateWallPart(option)` | 벽면 Part 생성 |
| `CreateSphereImpactorPart(option)` | 구형 충돌체 Part 생성 |
| `CreateCylinderImpactorPart(option)` | 원통형 충돌체 Part 생성 |

---

### 변환 및 변형

| 메서드 | 설명 |
|--------|------|
| `Transform(option)` | 좌표 변환 (이동, 회전 등) |
| `PartMorphing(option, subOption)` | Part 모핑 |
| `PartMorphingPIDBox(option, subOption)` | PID Box 기반 Part 모핑 |
| `PartMorphingBox(option, subOption)` | Box 기반 Part 모핑 |
| `WarpedPart(option)` | Part 뒤틀림 적용 |
| `WarpedtoInitialStressPart(option)` | 뒤틀림을 초기 응력으로 변환 |

---

### 재료 및 위치 DOE

| 메서드 | 설명 |
|--------|------|
| `MaterialExchange(option, filePath="")` | 재료 교체 |
| `PartLocationDOE(option, filePath="")` | Part 위치 DOE (실험계획법) |

---

### 치수 공차

| 메서드 | 설명 |
|--------|------|
| `DimensionalTolerance(option, filePath)` | 치수 공차 적용 |
| `DimensionalToleranceList(option, filePath)` | 리스트 기반 치수 공차 |
| `DimensionalToleranceNorm(option, filePath)` | 정규분포 기반 치수 공차 |
| `DimensionalToleranceLHS(option, filePath)` | LHS (Latin Hypercube Sampling) 기반 치수 공차 |

---

### 접촉 및 결합

| 메서드 | 설명 |
|--------|------|
| `CohesiveBetweenConformalMeshes(option)` | Conformal 메시 간 Cohesive 요소 생성 |
| `ContactAutoDecomposition(option)` | Contact 자동 분해 |
| `RemoveDuplicateTiedContacts()` | 중복 Tied Contact 제거 (SSID/MSID 순서 무관하게 동일 페어 제거) |

---

### 제약조건

| 메서드 | 설명 |
|--------|------|
| `ConstrainedNodalRigidBodyToBeam(option)` | CNRB를 Beam으로 변환 |

---

### DYNAIN 처리

| 메서드 | 설명 |
|--------|------|
| `DynaintoInitial(option, folderPath, filePath)` | DYNAIN 결과를 초기 조건으로 적용 |

---

### 시뮬레이션 자동화

| 메서드 | 설명 |
|--------|------|
| `SimulationAutomation(jsonOptionList, inputFile, inputObjFile, metaData)` | JSON 옵션 기반 시뮬레이션 자동화 |
| `SimulationAutomationPrevious(jsonOptionList, inputFile, inputObjFile)` | 이전 버전 시뮬레이션 자동화 |

---

## 유틸리티 함수 (모듈 레벨)

| 함수 | 설명 |
|------|------|
| `truncated_normal_samples(mu, sigma, x, size=1000, eps=50)` | 절단 정규분포 샘플링 |
| `lhs_unit(n_samples, n_dims, rng)` | Latin Hypercube Sampling 단위 함수 |

---

## 사용 예시

```python
from KooDynaImporter import KooDynaImporter
from KooDynaAdvancedModification import KooDynaAdvancedModification

# DYNA 파일 로드
importer = KooDynaImporter()
importer.ImportDynaKeyword("model.k")

# 수정 객체 생성
modifier = KooDynaAdvancedModification(importer)

# 중복 Tied Contact 제거
modifier.RemoveDuplicateTiedContacts()

# 수정된 파일 저장
modifier.WriteModifiedFile("model_modified.k")
```