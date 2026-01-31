# ODB Advanced V1.1 - OC(Arc) Support & Edge-to-Arc Reduction

## 개요

ODB++ 파일에서 `OC` (Outline Curve, 원호 세그먼트) 키워드를 파싱하고,
폴리곤의 edge가 과도하게 많을 때 연속된 직선 점들을 arc로 치환하여 점 수를 줄이는 기능을 추가한다.

---

## Part 1: OC 키워드 파싱 추가

### 1.1 OC 키워드 포맷

```
OB xStart yStart [I/E]    <- 시작점
OS xEnd yEnd               <- 직선 세그먼트
OC xEnd yEnd xCenter yCenter Y/N  <- 원호 세그먼트 (Y=시계방향, N=반시계방향)
OE                          <- 종료
```

### 1.2 수정 파일 목록

#### (A) ODBPPImporter.py [완료]

| 함수 | 라인 | 변경 내용 |
|------|------|-----------|
| `ImportPolygon` (CT 블록) | 54-94 | OC 파싱 추가. prevVertex 추적하여 Line/Arc edge를 명시적으로 생성. edges가 있으면 `CreatePolygon(vertices, 'CT', edges)` 호출 |
| `ImportFeature` | 98-136 | 동일한 OC 파싱 패턴 추가 |
| `ImportEdgeFeature` | 150-187 | OC를 `[xprev,yprev,xEnd,yEnd,xCenter,yCenter,clk]` 7원소 raw edge로 저장 (기존 Arc 처리와 동일 포맷) |

#### (B) Layer.py [미완료]

**생산 코드 (Import):**

| 함수 | 라인 | 변경 내용 |
|------|------|-----------|
| `ImportPatternfromODBStringList` | 217-241 | OB 블록 내부에서 OC 처리 추가. `patternClockwiseList` 도입 |
| `ImportPatternfromODBStream` | 361-387 | 동일 |
| `Layer.__init__` | 54-57 | `self.patternClockwiseList = []` 초기화 추가 |
| `CombinePatternofLayer` | 70-76 | `self.patternClockwiseList.extend(...)` 추가 |

**소비 코드 (Generate/Export):**

| 함수 | 라인 | 변경 내용 | 영향도 |
|------|------|-----------|--------|
| `GetExternalShape` | 1831-1866 | clockwiseList 전달 추가 | 높음 |
| `GetShape` | 1868-1902 | clockwiseList 전달 추가 | 높음 |
| `GetOBShapePrev` | 2278-2319 | clockwise 정보에 따라 직선/Arc Edge 분기 생성. `BRepBuilderAPI_MakePolygon` -> `BRepBuilderAPI_MakeWire` + Line/Arc 혼합 | 높음 (핵심) |
| `GetOBShape` | 2228-2276 | 동일 변경. `create_closed_loop`에 clockwise 전달 | 중간 |
| `ExportUnitFeature` | 1169-1223 | Arc 세그먼트를 OC 키워드로 내보내기 | 낮음 |
| `GenerateSolid` | 1160-1167 | 변경 불필요 (len() 호출뿐) | 없음 |
| `ImportODBZipExternalGeometry` | 552 | 반환값에 clockwiseList 추가 고려 | 낮음 |

### 1.3 데이터 구조 변경

**기존:**
```python
self.patternXList = []          # [i] = [x0, x1, x2, ...]
self.patternYList = []          # [i] = [y0, y1, y2, ...]
self.patternSymbolIDList = []   # [i] = symbolID or -1
self.patternPolarityList = []   # [i] = 0 or 1
```

**추가:**
```python
self.patternClockwiseList = []  # [i] = [None, None, 1, 0, None, ...]
#                                        직선  직선  CW  CCW  직선
# - None = 직선 세그먼트 (OS, 이전점->현재점)
# - 1 = 시계방향 Arc (OC, cw=Y)
# - 0 = 반시계방향 Arc (OC, cw=N)
```

OC가 있는 세그먼트의 경우, xVec/yVec에는 아래처럼 저장:
- OS: xVec에 끝점 x, yVec에 끝점 y (1개씩)
- OC: xVec에 [끝점x, 중심x], yVec에 [끝점y, 중심y] (2개씩)
  -> 기존 flat 구조와 충돌하므로, **xMat/yMat 2D 리스트 방식**을 사용

Symbol.py의 기존 패턴을 따라 세그먼트별로 저장:
```python
patternXList[i] = [[xStart, xEnd], [xStart, xEnd], [xStart, xEnd, xCenter], ...]
patternYList[i] = [[yStart, yEnd], [yStart, yEnd], [yStart, yEnd, yCenter], ...]
patternClockwiseList[i] = [None, None, 1, ...]
```

단, 기존 P/L/A 패턴(symbolID >= 0)은 **xVec/yVec flat 리스트 유지** (소비 코드에서 symbolID로 분기하므로 호환성 유지).

OB 블록(symbolID == -1)만 위 2D 구조로 변경.

### 1.4 GetOBShapePrev 핵심 변경

```python
# 변경 전: BRepBuilderAPI_MakePolygon (직선만)
polygon_builder = BRepBuilderAPI_MakePolygon()
for j in range(len(xVec)):
    polygon_builder.Add(gp_Pnt(xVec[j], yVec[j], zLoc))

# 변경 후: BRepBuilderAPI_MakeWire + Line/Arc 혼합
wire_builder = BRepBuilderAPI_MakeWire()
for j in range(len(xMat)):
    if cwList[j] is None:
        # 직선 세그먼트
        p1 = gp_Pnt(xMat[j][0], yMat[j][0], zLoc)
        p2 = gp_Pnt(xMat[j][1], yMat[j][1], zLoc)
        edge = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
    else:
        # Arc 세그먼트
        pStart = gp_Pnt(xMat[j][0], yMat[j][0], zLoc)
        pEnd   = gp_Pnt(xMat[j][1], yMat[j][1], zLoc)
        pCenter = gp_Pnt(xMat[j][2], yMat[j][2], zLoc)
        radius = pCenter.Distance(pStart)
        normal = gp_Dir(0, 0, 1) if cwList[j] == 0 else gp_Dir(0, 0, -1)
        ax2 = gp_Ax2(pCenter, normal)
        edge = BRepBuilderAPI_MakeEdge(gp_Circ(ax2, radius), pStart, pEnd).Edge()
    wire_builder.Add(edge)
```

---

## Part 2: Edge-to-Arc Reduction (점 축소 알고리즘)

### 2.1 목적

Polynomial(CT) 폴리곤이 OB/OS로만 구성되어 있을 때, edge 수가 수백~수천 개가 되면
CAD 생성 성능이 저하된다. 연속된 직선 세그먼트 중 같은 원호 위에 놓인 점들을 감지하여
하나의 Arc edge로 치환하면 edge 수를 대폭 줄일 수 있다.

### 2.2 알고리즘

기존 `create_closed_loop` (Layer.py:2145-2226)에 이미 유사한 로직이 존재한다:
- 연속 3점에서 외접원 중심/반경 계산 (`calculate_circle_center_radius`)
- 중심과 반경이 유사한 연속 점들을 그룹화
- 그룹 내 시작점/중간점/끝점 3개로 Arc 생성

이 로직을 **Polygon2D 레벨에서 재사용 가능한 함수로 추출**한다.

#### 단계:
1. 연속 3점(p_{i-1}, p_i, p_{i+1})으로 외접원 (center, radius) 계산
2. 인접 세그먼트끼리 center/radius 비교:
   - `|center_i - center_{i+1}| / (radius_i + radius_{i+1}) < tol_center` (기본 0.05)
   - `|radius_i - radius_{i+1}| / (radius_i + radius_{i+1}) < tol_radius` (기본 0.05)
   - 두 조건 모두 만족 → 같은 Arc 그룹
3. Arc 그룹의 시작점/끝점/중심점으로 단일 Arc edge 생성
4. 비그룹 점들은 기존 Line edge 유지

### 2.3 수정 파일

| 파일 | 추가/변경 | 내용 |
|------|-----------|------|
| `Polygon.py` | 함수 추가 | `Polygon2D.ReduceEdgesToArcs(tol_center, tol_radius)` — edges 리스트에서 연속 Line을 Arc로 치환 |
| `PolygonManager.py` | 변경 없음 | 기존 `CreateArc`, `CreateLine` 그대로 사용 |
| `ODBPPImporter.py` | 호출 추가 | `ImportPolygon`, `ImportFeature`에서 CT 폴리곤 생성 후 `ReduceEdgesToArcs()` 호출 |
| `Layer.py` | 호출 추가 | `GetOBShapePrev`, `GetOBShape`에서 shape 생성 전에 edge reduction 적용 가능 |

### 2.4 ReduceEdgesToArcs 상세 설계

```python
def ReduceEdgesToArcs(self, tol_center=0.05, tol_radius=0.05, min_group_size=3):
    """
    연속된 Line edge들 중 같은 원호 위에 있는 것들을 감지하여
    하나의 Arc edge로 치환한다.

    Args:
        tol_center: 중심점 거리 비율 허용 오차
        tol_radius: 반경 비율 허용 오차
        min_group_size: Arc로 치환할 최소 연속 Line 수 (기본 3)
    """
    if len(self.edges) < min_group_size:
        return

    # 1) 각 연속 3점에서 center, radius 계산
    # 2) 같은 Arc 그룹으로 묶기
    # 3) 그룹 크기 >= min_group_size인 것만 Arc로 치환
    # 4) self.edges, self.vertices 재구성
```

위치: `Polygon.py`의 `Polygon2D` 클래스 내부, `Generate` 함수 바로 위.

### 2.5 유효숫자 기반 판별

ODB 파일의 좌표는 일반적으로 소수점 이하 3~6자리로 저장된다.
이 유효숫자 범위 내에서 외접원 중심/반경이 일치하면 Arc로 치환 가능하다고 판단한다.

- 좌표 유효숫자에서 center 비교: `abs(cx1 - cx2) < 10^(-significant_digits + 1)`
- radius 비교: `abs(r1 - r2) / max(r1, r2) < tol_radius`

---

## 구현 순서

1. [완료] ODBPPImporter.py - OC 파싱 (ImportPolygon, ImportFeature, ImportEdgeFeature)
2. [완료] Layer.py - `patternClockwiseList` 도입 및 Import 함수 수정
3. [완료] Layer.py - 소비 코드 수정 (GetOBShapePrev, GetOBShape, GetExternalShape, GetShape)
4. [완료] Layer.py - ExportUnitFeature OC 내보내기
5. [완료] Polygon.py - `ReduceEdgesToArcs` 구현 + `_circumcircle` 유틸리티
6. [완료] ODBPPImporter.py - CT 폴리곤에 ReduceEdgesToArcs 적용
7. [예정] 테스트 및 검증

---

## 파일별 수정 요약

| 파일 | Part 1 (OC) | Part 2 (Reduction) |
|------|-------------|---------------------|
| `ODBPPImporter.py` | ImportPolygon, ImportFeature, ImportEdgeFeature [완료] | CT 폴리곤에 ReduceEdgesToArcs 호출 추가 |
| `Layer.py` | __init__, CombinePatternofLayer, ImportPatternfromODBStringList, ImportPatternfromODBStream, GetExternalShape, GetShape, GetOBShapePrev, GetOBShape, ExportUnitFeature | GetOBShape에서 reduction 적용 가능 |
| `Polygon.py` | 변경 없음 | ReduceEdgesToArcs 함수 추가 |
| `PolygonManager.py` | 변경 없음 | 변경 없음 |
| `Symbol.py` | 변경 없음 (이미 OC 지원) | 변경 없음 |
