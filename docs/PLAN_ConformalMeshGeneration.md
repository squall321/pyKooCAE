# Conformal Mesh Generation Plan

## 1. 개요

### 1.1 목적
KooAutomatedModeller의 PKG 모드에 **완전 conformal mesh** 생성 기능을 추가한다.
conformal mesh만 지원하는 솔버(Peridynamics 등)에서 사용 가능한 격자를 생성하는 것이 목표이다.

### 1.2 배경
- 현재 메쉬 모드(Hexa/Tetra/Quad/Tri)는 레이어 내 실린더와 본체를 **독립적으로** 메쉬 → non-conformal
- 레이어 간 인터페이스도 노드가 불일치 → non-conformal
- conformal 전용 솔버에서는 사용 불가

### 1.3 핵심 전략: Hexa Core + Tetra Buffer

각 레이어 내부는 **2D BooleanFragments + Extrude로 conformal hexa**를 생성하고,
레이어 간 인터페이스는 **tetra buffer layer**로 연결하여 전체 모델의 conformal을 보장한다.

---

## 2. 아키텍처

### 2.1 전체 메쉬 구조

```
z ↑
  │  ┌─── Layer N (Conformal Hexa) ────┐  core_thickness = t - 2*buffer
  │  ├─── Buffer (Tetra) ─────────────┤  buffer_thickness
  │  ├─── Layer N-1 (Conformal Hexa) ──┤  core_thickness = t - 2*buffer
  │  ├─── Buffer (Tetra) ─────────────┤  buffer_thickness
  │  ├─── Layer N-2 (Conformal Hexa) ──┤  core_thickness = t - 2*buffer
  │  └────────────────────────────────┘

  최상층/최하층: buffer는 한쪽(내측)만 적용
```

### 2.2 레이어 내 Conformal Hexa 생성 (핵심)

```
Step 1: 2D 면 구성
  - 본체 사각형 (외곽 Curve Loop)
  - 실린더 원들 (내부 Disk)

Step 2: BooleanFragments
  - Gmsh OpenCASCADE의 BooleanFragments로 2D 면 분할
  - 본체에서 실린더 영역이 깔끔하게 분리됨
  - 공유 엣지에서 노드가 자동 일치 → conformal

Step 3: Recombine + Extrude
  - Recombine Surface → Quad 메쉬
  - Extrude {0,0,core_thickness} Layers{N}; Recombine; → Hexa

Step 4: Physical Volume 분리
  - 본체 영역 → Physical Volume("MainBody")
  - 각 실린더 → Physical Volume("Cylinder_i")
```

### 2.3 레이어 간 Tetra Buffer 생성

```
Step 1: 인접 레이어의 경계면 노드 추출
  - Layer N의 상면 (top face) 노드/요소
  - Layer N+1의 하면 (bottom face) 노드/요소

Step 2: Buffer Volume 정의
  - 하면: Layer N 상면 geometry
  - 상면: Layer N+1 하면 geometry
  - 측면: 외곽 연결
  - 높이: buffer_thickness

Step 3: Tetra 채움
  - 상하면의 기존 메쉬 노드를 고정 (imposed boundary)
  - Gmsh가 내부를 tetra로 채움 → 양쪽 모두 conformal
```

### 2.4 왜 Tetra Buffer가 작동하는가

```
Layer N 상면:  Quad 패턴 A (피치 0.35, 실린더 1635개 포함)
    ↕ Buffer (tetra)
Layer N+1 하면: Quad 패턴 B (피치 0.40, 실린더 496개 포함)

Tetra는 임의의 두 면 사이를 항상 conformal하게 채울 수 있다.
피치가 달라도, 실린더 배치가 달라도, 면적이 달라도 문제없다.
```

---

## 3. 입력 포맷

### 3.1 aptest.txt 키워드 추가

```
*Layer,PCB
Location,0,0,0
Length,30.0,30.0
Thickness,0.512
MeshGenerationType,Solid,ConformalHexa      ← 새 MeshType
MeshSizeInPlane,0.3
NumberofElementinThickness,3
ConformalBufferThickness,0.02               ← 새 키워드 (buffer 두께)

*Layer,SolderJoint
Location,0,0
Length,14.0,16.4
Thickness,0.12
MeshGenerationType,Solid,ConformalHexa
MeshSizeInPlane,0.1
NumberofElementinThickness,2
ConformalBufferThickness,0.02
Cylinder,-6.65,7.875,0.11
Cylinder,-6.3,7.875,0.11
...
```

### 3.2 키워드 동작 규칙

| 키워드 | 값 | 설명 |
|--------|-----|------|
| `MeshGenerationType` | `Solid,ConformalHexa` | conformal 모드 활성화 |
| `ConformalBufferThickness` | float (mm) | 레이어 간 tetra buffer 두께 |
| `MeshSizeInPlane` | float (mm) | 2D 면 메쉬 크기 |
| `NumberofElementinThickness` | int | 코어 hexa 두께 방향 요소 수 |

- `ConformalBufferThickness`가 없으면 → 레이어 내 conformal만 (레이어 간은 독립)
- `ConformalBufferThickness`가 있으면 → 레이어 간 tetra buffer 생성
- `ConformalHexa` 대신 기존 `Hexa/Tetra/Quad/Tri` → 기존 동작 그대로 (변경 없음)

---

## 4. 구현 상세

### 4.1 수정 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `PackageGenerator.py` | `ConformalHexa` MeshType 파싱, `ConformalBufferThickness` 키워드 파싱 |
| `PackageLayer.py` | `GenerateCylinderShapes()`에 ConformalHexa 분기, `GenerateConformalMesh()` 신규 메소드 |
| `KooMeshManagerGMSH.py` | `mesh_conformal_extrude_hexa()` 신규 메소드, `mesh_tetra_buffer()` 신규 메소드 |

### 4.2 PackageGenerator.py 변경

```python
# 기존 MeshType 파싱 (line ~315) 에 추가
elif svector[0] == "ConformalBufferThickness":
    conformalBufferThickness = float(svector[1])
    layer.SetConformalBufferThickness(conformalBufferThickness)
    print("ConformalBufferThickness: ", conformalBufferThickness)
```

### 4.3 PackageLayer.py 변경

#### GenerateCylinderShapes() 분기

```python
def GenerateCylinderShapes(self):
    self.cylinderShapeList = []

    if self.meshType == "ConformalHexa":
        # conformal 모드: shape만 생성, 개별 mesh 생성 SKIP
        for cylinder in self.cylinderList:
            x = cylinder[0] + self.posX
            y = cylinder[1] + self.posY
            z = self.posZ
            r = cylinder[2]
            cylinder_shape = BRepPrimAPI_MakePrism(
                circle_face, gp_Vec(0,0,self.thickness)
            ).Shape()
            self.cylinderShapeList.append(cylinder_shape)
        # cylinderMeshList는 빈 상태로 유지
        return

    # 기존 코드 (Hexa/Tetra/Quad/Tri) 그대로 유지
    ...
```

#### GenerateShape() 분기

```python
def GenerateShape(self):
    ...
    if self.meshType == "ConformalHexa":
        self.GenerateConformalMesh()
    elif self.meshGenerationMode:
        # 기존 mesh_shape() 호출 (Tetra 등)
        ...
```

#### GenerateConformalMesh() 신규 메소드

```python
def GenerateConformalMesh(self):
    """레이어 내 conformal hexa mesh 생성"""
    meshManager = KooMeshManagerGMSH(...)
    meshManager.SetPath(self.meshPath)
    meshManager.SetName("{0}_ConformalMesh".format(self.name))

    # 실린더 위치/반지름 목록 전달
    cylinderParams = []
    for cyl in self.cylinderList:
        x = cyl[0] + self.posX
        y = cyl[1] + self.posY
        r = cyl[2]
        cylinderParams.append((x, y, r))

    # 본체 영역 정보
    bodyParams = {
        'x': self.posX - self.xLength/2,
        'y': self.posY - self.yLength/2,
        'z': self.posZ + self.conformalBufferThickness,  # buffer 만큼 offset
        'xLen': self.xLength,
        'yLen': self.yLength,
        'thickness': self.thickness - 2*self.conformalBufferThickness,  # core 두께
    }

    meshManager.mesh_conformal_extrude_hexa(
        bodyParams, cylinderParams,
        self.meshSizeInPlane,
        self.numberofElementinThickness,
        self.maxNID, self.maxEID
    )

    self.conformalMesh = meshManager
    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
```

### 4.4 KooMeshManagerGMSH.py 신규 메소드

#### mesh_conformal_extrude_hexa()

```python
def mesh_conformal_extrude_hexa(self, body, cylinders, meshSize, numElemThick,
                                 maxNID=0, maxEID=0):
    """
    2D BooleanFragments + Extrude로 conformal hexa 생성

    body: dict {x, y, z, xLen, yLen, thickness}
    cylinders: list of (cx, cy, r)
    """
    geo = 'SetFactory("OpenCASCADE");\n'
    geo += f'Mesh.CharacteristicLengthMin = {meshSize*0.5};\n'
    geo += f'Mesh.CharacteristicLengthMax = {meshSize*1.5};\n\n'

    # 본체 사각형
    geo += f'Rectangle(1) = {{{body["x"]}, {body["y"]}, {body["z"]}, '
    geo += f'{body["xLen"]}, {body["yLen"]}}};\n\n'

    # 실린더 원들 (Disk)
    for i, (cx, cy, r) in enumerate(cylinders):
        geo += f'Disk({i+2}) = {{{cx}, {cy}, {body["z"]}, {r}}};\n'

    # BooleanFragments (conformal 핵심)
    n = len(cylinders)
    if n > 0:
        disk_ids = ",".join(str(i+2) for i in range(n))
        geo += f'\nBooleanFragments{{ Surface{{1}}; Delete; }}'
        geo += f'{{ Surface{{{disk_ids}}}; Delete; }}\n'

    # Recombine → Quad
    geo += '\nMesh.Algorithm = 8;\n'  # Frontal-Delaunay for Quads
    geo += 'Mesh.RecombineAll = 1;\n'

    # Extrude → Hexa
    thickness = body["thickness"]
    geo += f'\nExtrude {{0, 0, {thickness}}} {{\n'
    geo += f'  Surface{{:}}; Layers{{{numElemThick}}}; Recombine;\n'
    geo += '}\n'

    # Physical Volume 분리 (본체/실린더별)
    # → msh import 후 파트 분리에 사용

    # GEO 파일 저장 및 Gmsh 실행
    ...
```

#### mesh_tetra_buffer()

```python
def mesh_tetra_buffer(self, bottomMeshFile, topMeshFile, bufferThickness,
                       meshSize, maxNID=0, maxEID=0):
    """
    두 conformal hexa 레이어 사이를 tetra로 채움

    bottomMeshFile: 아래 레이어 상면 메쉬 (.msh)
    topMeshFile:    위 레이어 하면 메쉬 (.msh)
    bufferThickness: buffer 층 두께
    """
    geo = 'SetFactory("OpenCASCADE");\n'

    # 아래 레이어 상면과 위 레이어 하면을 경계로
    # 박스 volume 생성
    geo += f'// Buffer volume between layers\n'
    geo += f'Merge "{bottomMeshFile}";\n'
    geo += f'Merge "{topMeshFile}";\n'

    # 기존 면 메쉬 노드 고정
    geo += 'Mesh.MeshOnlyEmpty = 1;\n'

    # 내부를 tetra로 채움
    geo += 'Mesh.Algorithm3D = 1;\n'  # Delaunay
    geo += f'Mesh.CharacteristicLengthMax = {meshSize*2};\n'

    # Gmsh 실행
    ...
```

---

## 5. 처리 흐름도

```
aptest.txt 파싱
    │
    ├─ MeshType != "ConformalHexa"
    │   └─ 기존 흐름 (변경 없음)
    │
    └─ MeshType == "ConformalHexa"
        │
        ├─ Phase 1: 레이어별 Conformal Hexa Core 생성
        │   │
        │   ├─ Layer 0 (PCB)
        │   │   ├─ 2D: Rectangle (30x30)
        │   │   ├─ BooleanFragments (실린더 없음 → 단순 사각형)
        │   │   ├─ Recombine + Extrude → Hexa
        │   │   └─ 상면/하면 메쉬 노드 저장
        │   │
        │   ├─ Layer 1 (SolderJoint)
        │   │   ├─ 2D: Rectangle (14x16.4) + Disk x 1635
        │   │   ├─ BooleanFragments → 분할된 면
        │   │   ├─ Recombine + Extrude → Hexa (본체+실린더 conformal)
        │   │   └─ 상면/하면 메쉬 노드 저장
        │   │
        │   └─ ... (각 레이어 반복)
        │
        ├─ Phase 2: Tetra Buffer 생성 (ConformalBufferThickness 있을 때)
        │   │
        │   ├─ Buffer 0-1: PCB 상면 ↔ SolderJoint 하면 → Tetra
        │   ├─ Buffer 1-2: SolderJoint 상면 ↔ Subcore 하면 → Tetra
        │   └─ ... (인접 레이어 쌍마다 반복)
        │
        └─ Phase 3: 전체 메쉬 조립
            ├─ 모든 Hexa core + Tetra buffer 합치기
            ├─ NID/EID 연속 번호 부여
            └─ Physical Volume별 파트 정보 출력
```

---

## 6. 예상 문제점 및 개선안

### 6.1 Gmsh BooleanFragments 성능

**문제:**
- SolderJoint 1635개 Disk + 1개 Rectangle → BooleanFragments
- OpenCASCADE의 Boolean 연산이 수천 개 면에서 매우 느리거나 실패할 수 있음
- 메모리 사용량 폭증 가능

**개선안:**
- **배치 처리**: 실린더를 N개씩 묶어서 순차 Fragment (예: 100개씩)
- **영역 분할**: 본체를 4분할/9분할 → 각 영역별로 Fragment → 경계에서 노드 일치시킴
- **Gmsh API 사용**: GEO 파일 대신 Python API (`gmsh.model.occ.fragment()`) 사용 시 더 안정적
- **병렬 처리**: 독립 영역을 멀티프로세스로 처리

### 6.2 Tetra Buffer 품질

**문제:**
- buffer 두께가 너무 얇으면 → tetra aspect ratio 극악 (납작한 삼각형)
- 상면과 하면의 메쉬 밀도 차이가 크면 → tetra가 불균일

**개선안:**
- **buffer 두께 하한 설정**: `max(ConformalBufferThickness, meshSizeInPlane * 0.5)` 등으로 최소값 보장
- **중간면 삽입**: buffer가 두꺼우면 중간에 자유 면을 넣어 tetra 2단 분할
- **메쉬 크기 전이**: buffer 내부에서 상면/하면 메쉬 크기의 점진적 전이 (grading)
- **aspect ratio 검증**: 생성 후 자동 품질 체크, 기준 미달 시 경고

### 6.3 상하면 노드 추출 및 매칭

**문제:**
- Hexa core 메쉬의 상면/하면 노드를 정확히 식별해야 함
- z좌표 부동소수점 비교 시 오차 발생 가능
- 경계면에 있는 노드가 여러 면에 공유될 수 있음

**개선안:**
- **z좌표 tolerance 비교**: `abs(z - target_z) < 1e-6` 수준으로
- **Extrude 메쉬의 구조 활용**: Extrude로 생성된 메쉬는 최상/최하 레이어 노드가 명확히 분리됨
- **Gmsh Physical Surface 활용**: Extrude 시 자동 생성되는 top/bottom surface ID 사용

### 6.4 레이어 간 면적 불일치

**문제:**
- PCB: 30x30mm, SolderJoint: 14x16.4mm → 면적이 다름
- Buffer tetra의 하면(큰 면)과 상면(작은 면)의 크기가 다름
- 작은 레이어 외곽 → buffer가 어떤 형상이 되어야 하는가?

**개선안:**
```
옵션 A: 작은 레이어 영역만 buffer 생성
  PCB 상면 중 SolderJoint 영역만 잘라서 → buffer 하면
  SolderJoint 하면 전체 → buffer 상면
  → 나머지 PCB 상면은 자유면 (다른 레이어와 연결 없음)

옵션 B: Buffer를 큰 쪽 면적으로 확장
  SolderJoint 하면 외곽을 PCB 크기로 연장 (z좌표만 동일한 평면)
  → buffer가 전체 면적을 커버
  → SolderJoint 외곽은 빈 공간 (air/void) 파트로 처리
```
**옵션 A 권장** — 실제 접촉하는 영역만 buffer 생성이 물리적으로도 맞음

### 6.5 실린더가 Buffer 영역을 관통하는 경우

**문제:**
- 실린더 높이 = 레이어 두께 전체
- core 두께 = 레이어 두께 - 2*buffer
- → 실린더가 buffer 영역까지 연장되어야 하는가?

**개선안:**
```
옵션 A: 실린더는 core에만 존재 (buffer에는 없음)
  → buffer는 균질 tetra (실린더 없는 면)
  → 구현 단순, but 물리적으로 약간 부정확

옵션 B: 실린더가 buffer까지 연장
  → buffer 상하면에도 실린더 원이 포함
  → buffer tetra가 실린더 경계를 인식해야 함
  → 구현 복잡도 증가

옵션 C: Buffer 두께를 실린더 영역에서는 0으로 설정
  → 실린더 부분은 위아래 레이어가 직접 연결 (공유 노드)
  → 비실린더 영역만 buffer → 가장 물리적으로 정확
  → 구현 난이도 높음
```
**옵션 A로 시작**, 필요 시 옵션 B/C로 발전

### 6.6 NID/EID 연속성

**문제:**
- 여러 Gmsh 세션에서 독립적으로 메쉬 생성 → NID/EID 충돌
- 최종 조립 시 번호 재매핑 필요

**개선안:**
- 기존 코드의 `maxNID/maxEID` 패턴 그대로 활용
- 각 메쉬 생성 후 `GetMaxIDs()` → 다음 메쉬에 전달
- 레이어 순서: 아래→위 순서로 생성, NID/EID 연속 증가

### 6.7 대규모 모델 메모리

**문제:**
- 현재 aptest.txt: 실린더 2131개 → STEP만 22MB
- conformal mesh까지 생성하면 메모리 사용량 대폭 증가

**개선안:**
- **레이어별 독립 처리**: 전체를 한번에 올리지 않고 레이어별로 메쉬 생성→저장→메모리 해제
- **Gmsh 외부 프로세스**: subprocess로 Gmsh 실행, 완료 후 .msh만 읽어옴 (기존 방식과 동일)
- **메모리 제한 모니터링**: `resource.getrusage()` 등으로 사용량 체크

### 6.8 Recombine 실패 (Quad 생성 실패)

**문제:**
- BooleanFragments 후 생성된 면이 복잡하면 Gmsh Recombine이 100% quad를 보장하지 않음
- 일부 tri가 남아있으면 Extrude 시 prism(삼각기둥)이 섞임

**개선안:**
- `Mesh.RecombinationAlgorithm = 3` (blossom-quad 강제)
- `Mesh.SubdivisionAlgorithm = 2` (모든 tri를 강제로 quad 분할)
- 실패 시 fallback: conformal tetra (Extrude 없이 3D tetra로 전환)
- 메쉬 생성 후 요소 타입 통계 출력 → quad 비율 리포트

---

## 7. 구현 순서 (단계별)

### Phase 1: 단일 레이어 Conformal Hexa (MVP)
1. `KooMeshManagerGMSH.mesh_conformal_extrude_hexa()` 구현
2. `PackageLayer.GenerateConformalMesh()` 구현
3. `PackageGenerator.py`에 `ConformalHexa` 파싱 추가
4. 테스트: SolderJoint 레이어 단독 (1635 실린더)
5. 검증: Gmsh에서 메쉬 시각화, conformal 확인

### Phase 2: Tetra Buffer 레이어
1. `KooMeshManagerGMSH.mesh_tetra_buffer()` 구현
2. `PackageGenerator.py`에서 레이어 간 buffer 조립 로직 추가
3. 테스트: PCB + SolderJoint 2개 레이어 + buffer 1개
4. 검증: 인터페이스 노드 일치 확인

### Phase 3: 전체 다층 모델
1. 전체 8개 레이어 + 7개 buffer 생성
2. NID/EID 연속성 검증
3. 면적 불일치 레이어 처리 (6.4절)
4. 솔버 입력 파일 출력 (LS-DYNA .k / 기타)

### Phase 4: 성능 최적화 및 안정화
1. 대규모 실린더 배치 처리 (6.1절)
2. 메쉬 품질 자동 검증 (6.2절, 6.8절)
3. 에러 처리 및 fallback 메커니즘
4. 메모리 최적화 (6.7절)

---

## 8. 테스트 계획

### 8.1 단위 테스트

| 테스트 | 입력 | 기대 결과 |
|--------|------|----------|
| 실린더 없는 레이어 | 사각형만 | 정규 structured hexa |
| 실린더 1개 | 사각형 + 원 1개 | conformal hexa (원 경계 일치) |
| 실린더 10개 | 사각형 + 원 10개 | conformal hexa |
| 실린더 1635개 | SolderJoint 전체 | conformal hexa (성능 확인) |
| 2층 + buffer | PCB + SolderJoint | 전층 conformal |

### 8.2 품질 검증 항목

- [ ] 모든 요소 노드가 인접 요소와 공유 (hanging node 없음)
- [ ] Hexa core: quad face에서 인접 요소 면 완전 일치
- [ ] Tetra buffer: 상하면 노드가 인접 hexa면 노드와 정확히 일치
- [ ] Aspect ratio > 0.1 (극단적 납작한 요소 없음)
- [ ] Jacobian > 0 (역전된 요소 없음)

---

## 9. 참고: 현재 코드 위치

| 파일 | 경로 | 핵심 역할 |
|------|------|----------|
| PackageGenerator.py | `occProject/Generators/KooODBCADManager/` | 입력 파싱, 레이어 조립 |
| PackageLayer.py | `occProject/Generators/KooODBCADManager/` | 레이어별 shape/mesh 생성 |
| KooMeshManagerGMSH.py | `occProject/Generators/KooCAEManager/` | Gmsh 기반 메쉬 생성 |

### 기존 메쉬 관련 메소드 (참고)

| 메소드 | 용도 | conformal 활용 |
|--------|------|---------------|
| `mesh_shape_extrude_3D()` | BREP → Extrude Hexa | GEO 패턴 참고 |
| `mesh_shape_extrude_3D_polygon_refine()` | 점 목록 → GEO → Extrude | GEO 직접 생성 패턴 참고 |
| `mesh_shape()` | 일반 3D Tetra | buffer tetra 참고 |
| `mesh_shape_quad_2D()` | 2D Quad | 2D recombine 참고 |
