# KooMeshModifier DOE 생성 고속화 계획

## 1. 현재 문제

### 증상
- 500MB 모델 기준 DOE당 ~3분 소요
- 100 DOE → ~5시간, 1000 DOE → ~50시간
- batch_koomeshmodifier 모드에서 헤드노드 점유 시간이 과도함

### 원인: 다수의 Multi-DOE 메서드에서 매 DOE마다 전체 모델 재직렬화

```
DOE간 변하는 것: impact box/impactor (~1000 노드/요소) + 초기속도 + 접촉
DOE간 안 변하는 것: 원본 모델 전체 (노드 50만+, 요소 100만+, 재료, 섹션, 컨트롤 등)

→ 500MB 중 수 KB만 바뀌는데 매번 500MB 전체를 재직렬화
```

### 시간 내역 (DOE당 ~3분)

| 작업 | 비중 | 내용 |
|------|------|------|
| `WriteStreamDynaKeyword()` | ~40-50% | 전체 모델 직렬화 (모든 매니저) |
| `SyncronizeMaxID()` | ~30-40% | 모든 part의 모든 element ID 스캔 |
| `UpdateContactGraph()` | ~10-15% | 모든 contact의 bounding box 재계산 |
| `GetElementNodes()` + `RemoveNodesExceptNodes()` | ~5-10% | 전체 노드 순회하여 cleanup |

---

## 2. 대상 메서드 전체 분석

### 2.1 메서드 총괄 목록

KooDynaAdvancedModification.py에서 multi-DOE 루프를 실행하며 `WriteModifiedFile()` 또는 `WriteStreamDynaKeyword()`를 반복 호출하는 메서드:

| # | 메서드 | Lines | 루프 변수 | DOE당 출력 | 병목 |
|---|--------|-------|-----------|-----------|------|
| 1 | `DropAttitude()` | 1910-2266 | 각도 (Roll/Pitch/Yaw) | WriteModifiedFile | WriteStream + SyncMaxID |
| 2 | `DropWeightImpactTest()` | 2740-3210 | 위치 (locX/locY) | WriteModifiedFile | WriteStream + SyncMaxID + TetraMesh |
| 3 | `DropWeightImpactTestwithPartialRigid()` | 2372-2738 | 위치 (locX/locY) | WriteModifiedFile | WriteStream + SyncMaxID + TetraMesh + RigidPartition |
| 4 | `DropWeightImpactTestbyPart()` | 3211-3501 | Parts × 위치 | WriteModifiedFile | WriteStream + SyncMaxID + TetraMesh |
| 5 | `PartLocationDOE()` | 3664-3792 | 샘플링 위치 | WriteModifiedFile | WriteStream (전체 모델, 노드 위치만 변경) |
| 6 | `TranslationDOE()` | 4593-4628 | 변환 벡터 | WriteStreamDynaKeyword 직접 | WriteStream (전체 모델, 노드 위치만 변경) |

### 2.2 최적화 그룹 분류

#### 그룹 A: 새 지오메트리 추가형 (CacheBase + WriteDelta 적합)

DOE마다 새로운 노드/요소/파트를 생성하여 베이스 모델에 추가하고, 이전 DOE의 추가분을 제거하는 패턴.

**해당 메서드**: DropAttitude, DropWeightImpactTest, DropWeightImpactTestbyPart

**공통 패턴**:
```
루프 진입 전: 베이스 모델 설정 (재료, 섹션, 파트 등)
for each DOE:
    if i != 0: cleanup (이전 DOE 노드/요소/접촉/초기속도 삭제)
    새 지오메트리 생성 (impact box, sphere, cylinder 등)
    새 접촉/초기속도 생성
    WriteModifiedFile() ← 전체 500MB 재직렬화
```

**최적화 원리**: 베이스 모델은 불변이므로 1회 캐시하고, DOE마다 추가된 delta만 직렬화.

#### 그룹 B: 베이스 모델 변형형 (CacheBase 적용 복잡)

DOE마다 베이스 모델의 요소를 rigid/deformable로 재분류하여 베이스 모델 자체가 변경됨.

**해당 메서드**: DropWeightImpactTestwithPartialRigid

**특징**:
```
루프 진입 전: 모든 파트에 대한 rigid 복사본 생성
for each DOE:
    if i != 0:
        MoveElementsfromRigidPartstoPart() ← 베이스 요소 원래 파트로 복원
        cleanup (impactor/wall/접촉/초기속도 삭제)
    ChangetoRigidElementsOutsideofSphere() ← 충격 영역 외부 요소를 rigid 파트로 이동
    새 impactor/wall 생성
    WriteModifiedFile()
```

**CacheBase 적용 난이도**: 높음. 베이스 모델 파트 구성이 DOE마다 변하므로, 캐시된 베이스 문자열을 직접 사용할 수 없음.

#### 그룹 C: 노드 위치 변경형 (별도 최적화 필요)

DOE마다 기존 파트의 노드 위치를 변경(Translate)하고, 전체 모델을 재직렬화한 후, 원래 위치로 복원.

**해당 메서드**: PartLocationDOE, TranslationDOE

**공통 패턴**:
```
for each DOE:
    part.Translate(dx, dy, dz)           ← 노드 위치 변경
    WriteModifiedFile() 또는 WriteStream  ← 전체 500MB 재직렬화
    part.Translate(-dx, -dy, -dz)        ← 원래 위치 복원
```

**특징**: 새 엔티티 추가가 없음. 노드 좌표만 변경됨. delta = 변경된 노드 좌표들.

---

## 3. DropAttitude() 루프 상세 분석

### 3.1 루프 진입 전 (1회 실행)

| Line | 매니저 | 동작 | 비고 |
|------|--------|------|------|
| 1938-1940 | nodeSetManager | CreateNodeSet("AllNodes") | 전체 노드셋 생성 |
| 1943-1944 | nodeSetManager, boundaryNodeManager | CreateNodeSet("BottomFix"), CreateBoundarySPCNodeSet | 고정 경계조건 |
| 1947 | sectionManager | CreateSolidSection("RigidWall") | 벽 섹션 |
| 1949 | matManager | CreateElasticMaterial("RigidWall") | 벽 재료 |
| 1958 | nodeManager | MoveNodes() | **베이스 모델 원점으로 이동 (1회)** |
| 2005-2008 | partManager, additionalManager | CreatePartSet, CreateInterfaceSpringbackLSDyna | DR 설정 |

**핵심: 베이스 모델 노드는 루프 진입 전 1회 이동만 됨. 루프 내에서 회전하지 않음.**
(회전은 INITIAL_VELOCITY_RIGID_BODY의 angular velocity로 LS-DYNA가 DR 단계에서 처리)

### 3.2 루프 내 - Cleanup (i != 0)

| Line | 매니저 | 동작 |
|------|--------|------|
| 2031-2033 | elementManager, nodeManager | 이전 impact box 요소/노드 삭제 |
| 2035 | contactManager | 이전 접촉 삭제 |
| 2036 | partManager | 이전 벽 파트 삭제 |
| 2037 | initialManager | 이전 초기속도 삭제 |
| 2039 | nodeSetFixed | Clear() (노드셋 비우기) |
| 2040 | additionalManager | d2r_automatics.clear() |
| 2042 | partManager/elementManager | **SyncronizeMaxID() ← 전체 스캔 (낭비)** |

### 3.3 루프 내 - 생성 (매 DOE)

| Line | 매니저 | 동작 | 추가되는 것 |
|------|--------|------|------------|
| 2108 | initialManager | CreateInitialVelocity | 초기속도 (회전된 velocity + angular velocity) |
| 2110 | partManager | AddSolidPart | 벽 파트 1개 |
| 2111 | (global) | SyncronizeMaxID() | **전체 스캔 (낭비)** |
| 2114-2118 | nodeManager, elementManager | CreateImpactBox | 노드 ~1331개, 요소 ~1000개 |
| 2115 | nodeSetFixed | AddNodesfromDict | 상단면 노드 ~121개 |
| 2144 | contactManager | CreateContactAutoSurfacetoSurface | 접촉 1개 |
| 2152-2158 | additionalManager | CreateDeformableToRigidAutomatic (x2) | D2R 스위치 (옵션) |

### 3.4 루프 내 - 출력 (매 DOE)

| Line | 동작 | 시간 |
|------|------|------|
| 2206 | WriteModifiedFile() → WriteStreamDynaKeyword() | **~1.5분 (전체 500MB 재직렬화)** |
| 2206 | WriteModifiedFile() → AddMetaDatafromManager() → UpdateContactGraph() | **~0.5분** |

### 3.5 매니저 분류

**Static (루프 내 불변) - 캐싱 가능:**
- controlManager
- databaseManager
- dampingManager
- matManager
- sectionManager
- constrainedManager
- loadManager
- defineManager
- segmentSetManager
- 베이스 모델 노드/요소/파트
- nodeSetManager 중 "AllNodes" (불변)

**Dynamic (루프마다 변경) - Delta 직렬화 필요:**
- partManager: 벽 파트 추가/삭제
- nodeManager: impact box 노드 추가/삭제
- elementManager: impact box 요소 추가/삭제
- contactManager: 접촉 추가/삭제
- initialManager: 초기속도 추가/삭제
- nodeSetFixed ("BottomFix"): Clear/AddNodes
- additionalManager: D2R 스위치 추가/삭제 (옵션)

---

## 4. DropWeightImpactTest() 상세 분석

### 4.1 루프 진입 전 (1회 실행)

| Line | 동작 | 비고 |
|------|------|------|
| 2922-2925 | PartSet 생성, InterfaceSpringbackLSDyna | DR 설정 |
| 2937 | SetControlandDatabaseExplicit | 해석 제어 |
| 2942-2950 | (cylinder 시) ImpactorFront 파트 생성 | 재료+섹션+파트 |
| 2953-2964 | Beam 댐퍼 파트 생성 | 재료+섹션+파트 |
| 2967-2974 | Impactor 파트 생성 | 재료+섹션+파트 |
| 2976-2983 | Wall 파트 생성 (rigid) | 재료+섹션+파트 |
| 2999 | DefineCurve 생성 | 경계 조건용 |
| 3003-3005 | BoundaryPrescribedMotionRigid (x3) | 벽 고정 |

### 4.2 루프 내 - 추가 복잡성

DropAttitude와 비교한 추가 요소:

| 항목 | DropAttitude | DropWeightImpactTest |
|------|-------------|---------------------|
| Impactor 지오메트리 | **Hex box** (CreateImpactBox) | **Tetra mesh** (moduleManager → GenerateTetraMeshfromShapes) |
| Damper | 없음 | **Beam 요소** (stressWaveDistance > 0 시) |
| BoundaryDistance | 없음 | **RemoveOuterElement** (충격점에서 먼 요소 제거 + 복원) |
| nodeSet | nodeSetFixed만 | nodeSetInside + nodeSetFixed + spcBoundary |
| Impactor 타입 | 없음 (고정 box) | Sphere / Cylinder 분기 |
| SyncronizeMaxID 횟수 | 2회/DOE | **5~6회/DOE** (루프 내 PID별 반복까지 포함) |

### 4.3 DOE당 변경되는 항목 (Delta)

```
생성:
- impactorPart 메시 (tetra, moduleManager)     ← 수천 노드/요소
- wallPart 메시 (CreateImpactBox)               ← 1331 노드, 1000 요소
- (cylinder 시) impactFrontPart 메시 (tetra)
- beam 요소 (stressWaveDistance > 0 시)         ← boundaryNodes 수만큼
- beam 고정 노드 (boundaryFixNodes, boundaryBetweenNodes)
- contactWalltoObjects, contactImpactortoObjects
- (cylinder 시) tiedContactImpactortoFront
- initV (+ cylinder 시 initVFront)
- nodeSetInside, nodeSetFixed, spcBoundary (stressWaveDistance > 0 시)

삭제/복원 (cleanup):
- 위의 모든 항목 + removedElemList/removedNodeList 복원
```

### 4.4 CacheBase 적용 가능성

**적용 가능** (그룹 A). 단, DropAttitude보다 delta가 크고 복잡:

- Tetra mesh 생성은 moduleManager에서 수행 → 이 생성 시간 자체는 캐시로 줄일 수 없음
- BoundaryDistance 사용 시: 베이스 모델 요소를 제거/복원하는 패턴 → removedElemList/removedNodeList 처리 필요
- **BoundaryDistance 미사용 시**: DropAttitude와 거의 동일한 패턴으로 CacheBase 적용 가능
- **BoundaryDistance 사용 시**: 베이스 모델 요소가 DOE마다 다르게 제거되므로 캐시 적용 복잡 → 그룹 B와 유사

**결론**: BoundaryDistance 옵션 여부에 따라 그룹 A / 그룹 B 분기.

---

## 5. DropWeightImpactTestwithPartialRigid() 상세 분석

### 5.1 핵심 차이점: 베이스 모델 파트 구조 변형

```python
# 루프 진입 전 (1회)
matMan.GenerateRigidMaterialswithOffsetID(maxMatID)     # 모든 재료의 rigid 복사본 생성
partManager.GenerateRigidPartforAll(matMan, secMan)      # 모든 파트의 rigid 복사본 생성

# 루프 내 - DOE마다
ChangetoRigidElementsOutsideofSphere(impactPoint, stressWaveDistance, exceptPIDs)
# → 충격점에서 stressWaveDistance 밖의 요소를 원래 파트 → rigid 파트로 이동
# → 베이스 모델의 파트 구성 자체가 DOE마다 다름

# cleanup
MoveElementsfromRigidPartstoPart(exceptPIDs)
# → rigid 파트의 요소를 원래 deformable 파트로 복원
```

### 5.2 CacheBase 적용 난이도

**높음 (그룹 B)**. 이유:

1. 베이스 모델의 파트 구성이 DOE마다 다름 (같은 요소가 deformable 파트 / rigid 파트를 오가감)
2. rigid 파트에 속한 요소 목록이 DOE마다 다름
3. 캐시된 베이스 문자열의 노드/요소 직렬화에 파트 귀속 정보가 포함됨

**가능한 접근법**:
- 파트 구성 변경 전까지 (rigid 복사본 생성까지)를 캐시
- 요소-파트 매핑이 변경된 부분만 delta로 직렬화
- 또는: rigid 파트 전체 + deformable 파트 전체를 매번 직렬화하되, 매니저/컨트롤/재료/섹션은 캐시

**권장**: Phase 2 이후, 별도 최적화 단계에서 처리. 우선순위 낮음.

---

## 6. DropWeightImpactTestbyPart() 상세 분석

### 6.1 구조

```python
# 루프 진입 전: impactor/wall 파트 생성 (DropWeightImpactTest과 동일)
# 이중 루프:
for partID in partIDs:          # 외부: 대상 파트별
    for j in range(len(locX)):  # 내부: 위치별
        if j != 0 or i != 0: cleanup(...)
        impactor mesh 생성 (sphere/cylinder)
        wall mesh 생성
        contacts, initV 생성
        WriteModifiedFile(...)
```

### 6.2 CacheBase 적용 가능성

**적용 가능** (그룹 A). DropWeightImpactTest에서 BoundaryDistance/beam이 없는 버전. 패턴이 DropAttitude와 동일:

- 베이스 모델 불변
- DOE마다 impactor + wall + contacts + initV만 추가/삭제
- CacheBase 그대로 적용 가능

---

## 7. PartLocationDOE() 상세 분석

### 7.1 구조

```python
for i in range(numofSamples):
    part.Translate(curDx, curDy, curDz)     # 노드 위치 변경
    if part.CheckinsideValidArea(mask, ...):
        self.WriteModifiedFile(filePath, modifiedKeyword)  # 전체 500MB 재직렬화
    part.Translate(-curDx, -curDy, -curDz)  # 원래 위치 복원
```

### 7.2 특징

- 새로운 엔티티(파트/요소/접촉 등)가 추가되지 않음
- 특정 파트의 **노드 좌표**만 변경됨
- mask 검증 실패 시 출력하지 않음 (일부 DOE 건너뜀)

### 7.3 최적화 접근 (그룹 C)

**CacheBase + PatchNodes 방식**:

```python
# 루프 진입 전 (1회)
cached_base = WriteStreamDynaKeyword()  # 전체 직렬화
target_node_ids = set(part의 노드 ID 목록)

# 루프 (DOE당)
part.Translate(dx, dy, dz)
if part.CheckinsideValidArea(...):
    # 방법 1: 변경된 노드만 재직렬화 후 교체
    patched = patch_nodes_in_cached(cached_base, target_node_ids, nodeManager)
    write(patched)

    # 방법 2 (더 간단): *INCLUDE 분리
    # base_model.k (노드 제외) + nodes_{doe}.k (변경된 노드만)

part.Translate(-dx, -dy, -dz)
```

**방법 1의 기술적 과제**:
- 캐시된 문자열에서 특정 노드 ID의 좌표를 찾아 교체하려면, 노드 직렬화 위치의 인덱스가 필요
- 고정 폭 포맷이면 오프셋 계산 가능, 가변 폭이면 불가능
- LS-DYNA 키워드 포맷은 **고정 폭 (8자리/16자리)** → 오프셋 교체 가능

**방법 2 (권장)**: *INCLUDE 방식이 가장 깔끔. 별도 절에서 상세 설명.

---

## 8. TranslationDOE() 상세 분석

### 8.1 구조

```python
for i in range(numofSamples):
    for pid in translationDict:
        part.Translate(transX, transY, transZ)

    with open(curPath, "w") as f:
        f.write("*Keyword\n")
        f.write(self.dynaImporter.WriteStreamDynaKeyword())  # 직접 호출, WriteModifiedFile 미사용
        f.write("*End\n")

    for pid in translationDict:
        part.Translate(-transX, -transY, -transZ)  # 복원
```

### 8.2 PartLocationDOE와의 차이

| 항목 | PartLocationDOE | TranslationDOE |
|------|----------------|----------------|
| 출력 방식 | WriteModifiedFile() | WriteStreamDynaKeyword() 직접 |
| 대상 파트 수 | 1개 | 다수 (translationDict의 모든 PID) |
| mask 검증 | 있음 | 없음 |
| metadata/JSON | WriteModifiedFile 내부 처리 | 별도 JSON 생성 |

### 8.3 최적화 접근

PartLocationDOE와 동일한 그룹 C 최적화 적용 가능. 다수 파트의 노드가 변경되므로 PatchNodes의 대상 노드가 더 많을 수 있으나, 원리는 동일.

---

## 9. 해결 방안 총괄

### 방안 A: CacheBase + WriteDelta (그룹 A 메서드용, 권장)

#### 대상: DropAttitude, DropWeightImpactTest (BoundaryDistance 미사용 시), DropWeightImpactTestbyPart

#### 개요
루프 진입 전 베이스 모델을 1회 직렬화하여 캐시하고, 매 DOE에서는 delta만 직렬화하여 append.

#### 주의: nodeSetFixed 중복 ID 문제

캐시된 베이스에 빈 nodeSetFixed가 포함되고, delta에 채워진 nodeSetFixed가 다시 직렬화되면 동일 SID의 *SET_NODE가 2번 나타남. LS-DYNA가 이를 올바르게 처리하지 않을 수 있음.

**해결**: 베이스 캐시 시 nodeSetFixed를 제외하고, delta에서만 직렬화.

#### 구현 구조

```python
# ===== 루프 진입 전 (1회) =====

# 1. 베이스 모델 직렬화 (매니저별 분리)
cached_static = serialize_static_managers()   # control, database, damping, mat, section, etc.
cached_base_parts = serialize_base_parts()    # 베이스 파트 + 노드 + 요소
cached_base_sets = serialize_base_sets()      # AllNodes 노드셋 (nodeSetFixed 제외)
cached_boundary = serialize_boundary()        # SPC 경계조건

# 2. 베이스 상태 경계값 기록
base_max_nid = nodeManager.GetMaxID()
base_max_eid = maxEID
base_part_ids = set(partManager.parts.keys())
base_contact_keys = set(contactManager.contacts.keys())
base_initial_keys = set(initialManager.initials.keys())

# ===== 루프 (DOE당 수 초) =====
for i in range(len(RxList)):
    if i != 0:
        # 빠른 cleanup (ID 범위 기반)
        RestoreBaseState(base_max_nid, base_max_eid, base_part_ids, ...)

    # Impact box 생성 (기존 코드 그대로)
    CreateImpactBox(...)
    CreateContact(...)
    CreateInitialVelocity(...)

    # Delta만 직렬화
    delta = WriteDeltaKeyword(base_part_ids, base_contact_keys, ...)

    # 파일 출력: 캐시 + delta
    with open(output_path, 'w') as f:
        f.write("*KEYWORD\n")
        f.write(cached_static)
        f.write(cached_base_parts)
        f.write(cached_base_sets)
        f.write(cached_boundary)
        f.write(delta)
        f.write("*END\n")
```

#### 예상 시간 (DropAttitude 기준)

| 항목 | 현재 | 개선 후 |
|------|------|---------|
| 베이스 직렬화 | DOE당 ~90초 | **1회 ~90초** |
| SyncronizeMaxID | DOE당 ~60초 | **제거 (캐시값 복원)** |
| Impact box 생성 | DOE당 ~2초 | ~2초 (동일) |
| Delta 직렬화 | - | ~1초 |
| 파일 출력 (500MB 쓰기) | - | ~3초 (memcpy) |
| UpdateContactGraph | DOE당 ~20초 | ~1초 (impact box contact만) |
| **합계** | **~3분** | **~7초** |

#### DropWeightImpactTest 적용 시 추가 고려사항

- Tetra mesh 생성 시간(moduleManager)은 캐시로 줄일 수 없음 (DOE마다 다른 위치에 새 메시)
- 예상 시간: ~7초 + tetra mesh 생성 ~5-10초 = **~15초/DOE** (현재 ~3분+)

### 방안 B: CacheStatic + WriteFullParts (그룹 B 메서드용)

#### 대상: DropWeightImpactTestwithPartialRigid, DropWeightImpactTest (BoundaryDistance 사용 시)

#### 개요
매니저/제어/재료/섹션 등 static 항목만 캐시하고, 파트/노드/요소는 매번 직렬화.

```python
# 1회
cached_static = serialize_static_managers()  # control, database, damping, mat, section, etc.

# DOE마다
full_parts = serialize_all_parts()  # 변형된 파트 구성 반영
with open(output_path, 'w') as f:
    f.write("*KEYWORD\n")
    f.write(cached_static)
    f.write(full_parts)  # 파트/노드/요소 전체 직렬화
    f.write("*END\n")
```

#### 예상 효과

Static 매니저는 전체의 ~5-10%이므로 효과 제한적. 주된 병목인 SyncronizeMaxID 최적화가 더 중요:
- 현재: SyncronizeMaxID()를 cleanup마다 호출 (5~6회/DOE)
- 개선: 캐시된 base_max_eid 사용 + rigid 파트 max ID 별도 추적

**예상 시간**: ~3분 → ~1.5분 (50% 단축). 방안 A만큼 극적이지 않음.

**권장**: Phase 2 이후 별도 최적화. 우선순위 낮음.

### 방안 C: CacheBase + PatchNodes / *INCLUDE (그룹 C 메서드용)

#### 대상: PartLocationDOE, TranslationDOE

#### 접근법 1: *INCLUDE 분리 (권장)

```
base_model.k (500MB, 1회 생성):
  *KEYWORD
  [모든 키워드 - 노드 제외]
  *END

nodes_base.k (노드 좌표, 1회 생성):
  *NODE
  [전체 노드 좌표]

nodes_translated_{doe}.k (변경된 노드만, DOE당 생성):
  *NODE
  [변경된 노드 좌표 - 원래 좌표를 덮어씀]

main_{doe}.k (DOE당 생성):
  *KEYWORD
  *INCLUDE
  base_model.k
  *INCLUDE
  nodes_translated_{doe}.k    ← LS-DYNA: 동일 NID는 마지막 값 사용
  *END
```

**주의**: LS-DYNA의 *INCLUDE에서 동일 NID 중복 시 동작은 버전에 따라 다를 수 있음. 검증 필요.

#### 접근법 2: CacheBase + PatchNodes

```python
# 1회
cached_base = WriteStreamDynaKeyword()
# 노드 직렬화 구간의 (노드ID → 오프셋) 맵 구축
node_offset_map = build_node_offset_map(cached_base)

# DOE마다
part.Translate(dx, dy, dz)
patched = bytearray(cached_base.encode())
for nid in translated_node_ids:
    node = nodeManager.nodes[nid]
    offset = node_offset_map[nid]
    # 고정 폭 16자리 포맷으로 좌표 덮어쓰기
    new_coords = format_node_coords(node.x, node.y, node.z)
    patched[offset:offset+48] = new_coords.encode()
write(patched)
part.Translate(-dx, -dy, -dz)
```

**장점**: 가장 빠름 (문자열 부분 교체만)
**단점**: 노드 직렬화 포맷에 강하게 결합됨, 구현 복잡

**권장**: 접근법 1 (*INCLUDE) 우선. PatchNodes는 추가 최적화로.

#### 예상 시간

| 항목 | 현재 | *INCLUDE | PatchNodes |
|------|------|----------|------------|
| 베이스 직렬화 | DOE당 ~90초 | **1회** | **1회** |
| SyncronizeMaxID | DOE당 ~60초 | **제거** | **제거** |
| Translate | ~0.1초 | ~0.1초 | ~0.1초 |
| 변경 노드 직렬화 | - | ~0.5초 | ~0.1초 |
| 파일 쓰기 | - | ~수KB | ~3초 (500MB) |
| **합계** | **~3분** | **~1초** | **~4초** |

---

## 10. 필요한 새 함수

### 10.1 KooDynaAdvancedModification.py

```python
def CacheBaseKeyword(self):
    """루프 진입 전 베이스 모델 직렬화 및 상태 저장

    Returns:
        cached_base (str): 직렬화된 베이스 모델 문자열
        base_state (dict): 베이스 상태 경계값
            - max_nid: 베이스 최대 노드 ID
            - max_eid: 베이스 최대 요소 ID
            - part_ids: 베이스 파트 ID 집합
            - contact_keys: 베이스 접촉 키 집합
            - initial_keys: 베이스 초기조건 키 집합
            - nodeset_fixed_sid: nodeSetFixed의 SID (delta에서 직렬화)
    """

def WriteCachedOutput(self, output_path, cached_base, delta_stream):
    """캐시된 베이스 + delta를 결합하여 .k 파일 출력"""

def RestoreBaseState(self, base_state):
    """impact box 관련 항목만 빠르게 제거하고 베이스 상태로 복원

    기존 cleanup 대비 차이:
    - RemoveNodesExceptNodes(전체 순회) → RemoveNodesAboveID(impact box만)
    - SyncronizeMaxID(전체 스캔) → 캐시값 복원
    """
```

### 10.2 KooMeshImporter.py

```python
def WriteStreamBaseKeyword(self, exclude_nodesets=None):
    """베이스 모델 직렬화 (특정 노드셋 제외)

    WriteStreamDynaKeyword()와 동일하되:
    - exclude_nodesets에 포함된 노드셋 제외
    - additionalManager의 D2R 부분 제외
    """

def WriteStreamDeltaKeyword(self, base_state):
    """delta 직렬화 (베이스 이후 추가된 항목만)

    직렬화 대상:
    - partManager: base_state.part_ids에 없는 파트
    - nodeManager: ID > base_state.max_nid인 노드
    - elementManager: ID > base_state.max_eid인 요소
    - contactManager: base_state.contact_keys에 없는 접촉
    - initialManager: base_state.initial_keys에 없는 초기조건
    - nodeSetFixed: 전체 (delta에서만 직렬화)
    - additionalManager: D2R 부분
    """
```

### 10.3 KooNode.py

```python
def RemoveNodesAboveID(self, max_id):
    """ID > max_id인 노드만 삭제

    기존 RemoveNodesExceptNodes()는 O(전체 노드)
    이 함수는 O(impact box 노드 ~1000개)
    """

def WriteStreamDeltaNodes(self, stream, min_id):
    """ID > min_id인 노드만 직렬화"""
```

### 10.4 KooElement.py

```python
def RemoveElementsAboveID(self, max_id):
    """ID > max_id인 요소만 삭제"""

def WriteStreamDeltaElements(self, stream, min_id):
    """ID > min_id인 요소만 직렬화"""
```

---

## 11. 수정 대상 파일

| 파일 | 변경 | 리스크 | 대상 메서드 |
|------|------|--------|-----------|
| `KooDynaAdvancedModification.py` | CacheBaseKeyword/RestoreBaseState/WriteCachedOutput 추가, 4개 메서드 루프 수정 | 높음 | 전체 |
| `KooMeshImporter.py` | WriteStreamBaseKeyword, WriteStreamDeltaKeyword 추가 | 중간 | 전체 |
| `KooNode.py` | RemoveNodesAboveID, WriteStreamDeltaNodes 추가 | 낮음 | 그룹 A |
| `KooElement.py` | RemoveElementsAboveID, WriteStreamDeltaElements 추가 | 낮음 | 그룹 A |
| KooChainRun / Runner | **변경 없음** | - | - |

---

## 12. 구현 순서

### Phase 1: 유틸리티 함수 추가 (리스크 낮음)

기존 코드에 영향 없이 새 함수만 추가.

1. `KooNode.py`: `RemoveNodesAboveID()`, `WriteStreamDeltaNodes()`
2. `KooElement.py`: `RemoveElementsAboveID()`, `WriteStreamDeltaElements()`
3. `KooMeshImporter.py`: `WriteStreamBaseKeyword()`, `WriteStreamDeltaKeyword()`

### Phase 2: DropAttitude 캐시 모드 (리스크 중간)

기존 코드를 fallback으로 유지하면서 새 경로 추가. **가장 영향이 크고 사용 빈도가 높은 메서드를 우선**.

4. `KooDynaAdvancedModification.py`:
   - `CacheBaseKeyword()` 구현
   - `RestoreBaseState()` 구현
   - `WriteCachedOutput()` 구현
5. `DropAttitude()` 루프에 분기 추가:
   ```python
   use_fast_mode = True  # 또는 옵션으로 제어
   if use_fast_mode:
       cached_base, base_state = self.CacheBaseKeyword()
       for i in range(len(RxList)):
           if i != 0:
               self.RestoreBaseState(base_state)
           # ... impact box 생성 (기존 코드 동일) ...
           delta = self.dynaImporter.WriteStreamDeltaKeyword(base_state)
           self.WriteCachedOutput(output_path, cached_base, delta)
   else:
       # 기존 코드 그대로 (fallback)
       for i in range(len(RxList)):
           ...
   ```

### Phase 3: DropWeightImpactTest / DropWeightImpactTestbyPart 캐시 모드 (리스크 중간)

DropAttitude와 동일한 CacheBase + WriteDelta 패턴 적용.

6. `DropWeightImpactTest()` 캐시 모드 추가
   - BoundaryDistance == 0 시: 그룹 A 패턴 (완전 캐시)
   - BoundaryDistance > 0 시: fallback (기존 방식 유지, 향후 최적화)
7. `DropWeightImpactTestbyPart()` 캐시 모드 추가
   - DropWeightImpactTest의 BoundaryDistance 없는 버전과 동일 패턴

### Phase 4: 검증 (필수)

8. 동일 모델/조건으로 기존 방식 vs 새 방식 출력 비교
   - .k 파일 diff (키워드 섹션별 비교, 순서 무관하게)
   - LS-DYNA 실행 결과 비교 (d3plot, dynain 동일성)
9. 엣지 케이스 검증:
   - D2R 옵션 활성화 시
   - Roughness 모드 시
   - Sphere vs Cylinder impactor
   - BoundaryDistance > 0 vs == 0

### Phase 5: 그룹 B/C 최적화 (별도 단계, 선택적)

10. `DropWeightImpactTestwithPartialRigid()`: CacheStatic + WriteFullParts (방안 B)
11. `DropWeightImpactTest()` BoundaryDistance > 0: CacheStatic + WriteFullParts
12. `PartLocationDOE()`: *INCLUDE 분리 (방안 C)
13. `TranslationDOE()`: *INCLUDE 분리 (방안 C)

### Phase 6: 기존 코드 정리

14. 검증 완료 후 fallback 제거 (또는 옵션으로 유지)
15. 빌드 + 배포

---

## 13. 리스크 평가

### 높은 리스크

| 리스크 | 원인 | 대응 |
|--------|------|------|
| 출력 파일 불일치 | delta에서 매니저 누락 | Phase 4에서 diff 검증 |
| nodeSetFixed 중복 SID | 캐시 + delta 양쪽에 같은 SID | WriteStreamBaseKeyword에서 제외 |
| LS-DYNA 파싱 오류 | 키워드 섹션 순서 의존성 | LS-DYNA는 순서 무관하게 파싱 (확인 완료) |
| Impact 메서드 delta 누락 | DropWeightImpactTest의 beam/nodeSet 등 추가 항목 | delta 대상 목록을 메서드별로 명시적 정의 |

### 낮은 리스크

| 리스크 | 원인 | 대응 |
|--------|------|------|
| 메모리 사용 증가 | 500MB 캐시 문자열 | 계산 노드 128GB+ → 무시 가능 |
| 디스크 쓰기 속도 | 500MB memcpy → 디스크 | NVMe ~2초, HDD ~5초 → 현재보다 빠름 |

---

## 14. 기존 기능 호환성

### 영향 없는 항목
- CumulativeScenarioRunner: 출력 파일 형식 동일 (.k + .json)
- KooChainRun: KooMeshModifier 호출 방식 변경 없음
- batch_koomeshmodifier: .done 파일 생성 위치/타이밍 동일
- scratch_run: KooMeshModifier 출력이 동일 경로에 동일 형식

### 검증 필수 항목
- DropAttitude 단일 DOE 출력이 기존과 동일한지 (키워드 파일 내용)
- DropAttitude 다중 DOE에서 모든 DOE가 정상 출력되는지
- DropWeightImpactTest Sphere/Cylinder 양쪽 정상 동작
- DropWeightImpactTestbyPart 다중 파트 × 다중 위치 정상 동작
- D2R 옵션 활성화 시 *DEFORMABLE_TO_RIGID 키워드 정상 출력
- copytoOutputFolder 로직 (Output/, DynamicRelaxation/ 복사) 정상 동작
- metadata JSON 정상 생성

---

## 15. 예상 성과

### 그룹 A 메서드 (CacheBase + WriteDelta)

| 시나리오 | 현재 | 개선 후 | 단축률 |
|----------|------|---------|--------|
| DropAttitude 100 DOE (500MB) | ~5시간 | ~12분 | **96%** |
| DropAttitude 1,000 DOE (500MB) | ~50시간 | ~2시간 | **96%** |
| DropAttitude 10,313 DOE (500MB) | ~21일 | ~20시간 | **96%** |
| DropWeightImpactTest 100 DOE (500MB) | ~5시간+ | ~25분 (tetra mesh 포함) | **92%** |
| DropWeightImpactTestbyPart 5x10 DOE (500MB) | ~2.5시간 | ~13분 | **92%** |

### 그룹 B 메서드 (Phase 5, CacheStatic)

| 시나리오 | 현재 | 개선 후 | 단축률 |
|----------|------|---------|--------|
| DropWeightImpactTestwithPartialRigid 100 DOE | ~5시간+ | ~2.5시간 | **~50%** |

### 그룹 C 메서드 (Phase 5, *INCLUDE)

| 시나리오 | 현재 | 개선 후 | 단축률 |
|----------|------|---------|--------|
| PartLocationDOE 1000 DOE (500MB) | ~50시간 | ~17분 | **99%** |
| TranslationDOE 100 DOE (500MB) | ~5시간 | ~2분 | **99%** |

---

## 16. 메서드별 적용 우선순위

| 우선순위 | 메서드 | 그룹 | 효과 | 복잡도 | Phase |
|----------|--------|------|------|--------|-------|
| **1** | DropAttitude | A | 96% | 중간 | 2 |
| **2** | DropWeightImpactTest (BD=0) | A | 92% | 중간 | 3 |
| **3** | DropWeightImpactTestbyPart | A | 92% | 낮음 (2 재사용) | 3 |
| 4 | PartLocationDOE | C | 99% | 높음 (*INCLUDE) | 5 |
| 5 | TranslationDOE | C | 99% | 높음 (*INCLUDE) | 5 |
| 6 | DropWeightImpactTestwithPartialRigid | B | 50% | 높음 | 5 |
| 7 | DropWeightImpactTest (BD>0) | B | 50% | 높음 | 5 |

**Phase 1~4로 우선순위 1~3을 처리하면 가장 많이 사용되는 메서드에서 92~96% 시간 단축 달성.**
Phase 5는 별도 단계로 필요 시 진행.

---

## 17. 대안: *INCLUDE 방식 (전체 메서드 공통)

LS-DYNA의 *INCLUDE 기능을 활용하여 모든 multi-DOE 메서드에 적용 가능한 범용 접근:

```
base_model.k (500MB, 1회 생성):
  *KEYWORD
  [모든 static 키워드]
  [베이스 노드/요소/파트]
  *END

delta_{doe}.k (수 KB~수 MB, DOE당 생성):
  *KEYWORD
  [DOE별 추가 항목: impact box, impactor, wall, contact, initV, etc.]
  *END

main_{doe}.k (수 바이트, DOE당 생성):
  *KEYWORD
  *INCLUDE
  base_model.k
  *INCLUDE
  delta_{doe}.k
  *END
```

**장점**: 디스크 사용량 대폭 감소 (500MB x 1 + 수KB x N), 중복 ID 문제 없음, 모든 그룹에 적용 가능
**단점**: CumulativeScenarioRunner가 *INCLUDE 구조를 인식해야 함, copytoOutputFolder 로직 수정 필요, base_model.k 경로 관리

→ 방안 A 구현 후 추가 최적화로 고려 가능. CumulativeScenarioRunner 수정이 필요하므로 영향 범위가 넓음.

---

**작성일**: 2026-02-15
**최종 수정**: 2026-02-28
