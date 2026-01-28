# TRANSFORM 모드 상세 분석

## 1. 개요

**목적**: 모델에 기하학적 변환(이동, 회전, 스케일, 미러링)을 순차적으로 적용

**파일 위치**:
- 파서: `KooMeshModifier.py` (라인 550-585)
- 실행: `KooDynaAdvancedModification.py` (라인 2246-2348)

**출력 접미사**: `_trans`

---

## 2. 지원 변환 타입

| 타입 | 설명 | 파라미터 |
|------|------|----------|
| Translation | 이동 | X, Y, Z 이동량 |
| Rotation | 오일러 각도 회전 | X, Y, Z 각도 (도) |
| Scale | 스케일링 | X, Y, Z 스케일 비율 |
| Mirror | 미러링 | 평면 (XY, YZ, XZ) |
| VectorRotation | 벡터 방향 회전 | X, Y, Z 벡터 |
| VectorToVectorRotation | 벡터→벡터 회전 | from 벡터, to 벡터 |

---

## 3. 설정 파일 구조

```
**Transform,<모드ID>
Translation,<X>,<Y>,<Z>
Rotation,<angleX>,<angleY>,<angleZ>
Scale,<sX>,<sY>,<sZ>
Mirror,<평면>
VectorRotation,<X>,<Y>,<Z>
VectorToVectorRotation,<fromX>,<fromY>,<fromZ>,<toX>,<toY>,<toZ>
**EndTransform
```

**중요**: 변환은 지정된 순서대로 순차 적용됩니다.

---

## 4. 핵심 알고리즘 (라인 2246-2348)

### 4.1 Translation (이동)

```python
if curOptionMode.lower() == "translation":
    tx = curOption[1]
    ty = curOption[2]
    tz = curOption[3]
    nodeMan.MoveNodes(tx, ty, tz)
```

모든 노드를 (tx, ty, tz) 만큼 이동

### 4.2 Rotation (회전)

```python
elif curOptionMode.lower() == "rotation":
    angleX = curOption[1]
    angleY = curOption[2]
    angleZ = curOption[3]

    # X축 회전
    trsfX = gp_Trsf()
    axX = gp_Ax1(gp_Pnt(0,0,0), gp_Dir(1,0,0))
    trsfX.SetRotation(axX, math.radians(angleX))

    # Y축 회전
    trsfY = gp_Trsf()
    axY = gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,1,0))
    trsfY.SetRotation(axY, math.radians(angleY))

    # Z축 회전
    trsfZ = gp_Trsf()
    axZ = gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,0,1))
    trsfZ.SetRotation(axZ, math.radians(angleZ))

    # 복합 변환 (X → Y → Z 순서)
    combinedTrsf = trsfX.Multiplied(trsfY)
    combinedTrsf = combinedTrsf.Multiplied(trsfZ)
    nodeMan.Transform(combinedTrsf)
```

### 4.3 Scale (스케일)

```python
elif curOptionMode.lower() == "scale":
    sx = curOption[1]
    sy = curOption[2]
    sz = curOption[3]
    nodeMan.Scaling(sx, sy, sz)
```

각 축별 독립 스케일링 지원

### 4.4 Mirror (미러링)

```python
elif curOptionMode.lower() == "mirror":
    mode = curOption[1]

    if mode.lower() == "xy":
        # XY 평면 대칭 (Z 반전)
        trsf = gp_Trsf()
        trsf.SetMirror(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(0,0,1)))
        for id in nodeMan.nodes:
            nodeMan.nodes[id].Transform(trsf)
        # 요소 연결성 수정
        for pid in self.dynaImporter.partManager.parts:
            elemMan = self.dynaImporter.partManager.parts[pid].elementManager
            elemMan.SetMirrorConnectivityXYPlane()

    elif mode.lower() == "yz":
        # YZ 평면 대칭 (X 반전)
        trsf.SetMirror(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(1,0,0)))
        ...

    elif mode.lower() == "xz":
        # XZ 평면 대칭 (Y 반전)
        trsf.SetMirror(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(0,1,0)))
        ...
```

**중요**: 미러링 시 요소 연결성도 함께 수정하여 법선 방향 유지

---

## 5. 사용 예시

### 5.1 단순 이동

```
**Transform,1
Translation,100,0,0
**EndTransform
```

X 방향으로 100만큼 이동

### 5.2 회전 후 이동

```
**Transform,1
Rotation,0,0,45
Translation,50,50,0
**EndTransform
```

1. Z축 기준 45도 회전
2. (50, 50, 0) 이동

### 5.3 스케일 + 미러링

```
**Transform,1
Scale,1.5,1.5,1.0
Mirror,XY
**EndTransform
```

1. X, Y 방향 1.5배 확대
2. XY 평면 대칭

### 5.4 복합 변환

```
**Transform,1
Translation,-50,-50,-50
Rotation,30,45,60
Scale,2.0,2.0,2.0
Translation,100,100,100
**EndTransform
```

1. 원점으로 이동 (-50, -50, -50)
2. 회전 (30°, 45°, 60°)
3. 2배 확대
4. 최종 위치로 이동 (100, 100, 100)

---

## 6. 변환 순서의 중요성

```
예: 이동 후 회전 vs 회전 후 이동

이동(100,0,0) → 회전(90°Z)      회전(90°Z) → 이동(100,0,0)

  초기: (0,0)                      초기: (0,0)
    │                                │
    ▼ 이동                           ▼ 회전
  (100,0)                          (0,0)
    │                                │
    ▼ 회전                           ▼ 이동
  (0,100)                          (100,0)

결과가 다름!
```

---

## 7. OpenCASCADE gp_Trsf 활용

이 모드는 OpenCASCADE의 기하 변환 라이브러리를 사용합니다:

```python
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax1, gp_Ax2, gp_Trsf

# 변환 객체 생성
trsf = gp_Trsf()

# 회전 설정
trsf.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,0,1)), angle)

# 미러 설정
trsf.SetMirror(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(0,0,1)))

# 스케일 설정
trsf.SetScaleFactor(scale)

# 복합 변환
combined = trsf1.Multiplied(trsf2)
```

---

## 8. 주의사항

1. **회전 순서**: X → Y → Z 순서로 적용 (Tait-Bryan 각도)
2. **회전 중심**: 항상 원점(0, 0, 0) 기준
3. **미러링 연결성**: 미러링 시 요소 노드 순서 자동 보정
4. **비균일 스케일**: 접촉 조건에 영향 줄 수 있음
5. **단위**: 이동량은 모델 단위와 동일해야 함
