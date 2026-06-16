# 3단 실린더 임팩터 (고무팁+중간단+본체) 설계서

작성 2026-06-15. LS-DYNA 부분충격 실린더 충격추 3단 형상 지원.

## 사용자 표준 (확정)

| 실린더 | 단 구성 | 목표 질량 | 계산 질량 |
|--------|--------|----------|----------|
| 8파이 | 고무팁(⌀8→⌀20 필렛 h6, ρ1.18e-9) + ⌀20 SUS h14 + ⌀44.5 SUS h38 (ρ6.57e-9) | 400g | ~418g |
| 15파이 | 앞⌀15+필렛(h15→⌀44.5) + ⌀44.5 h45.01 (전체 SUS ρ6.854e-9) | 500g | ~500g (본체480+필렛) |

I now have the complete and accurate picture, including the critical discovery that there are **three** consumer functions (LENS 2 found only two). I have all line numbers verified. Writing the design document now.

---

# 3단 실린더 임팩터 지원 설계서 (Cylinder Three-Stage Impactor)

## 1. 현 2단 구조와 한계

실린더 임팩터는 현재 **front(고무팁) + back(본체) = 2 part / 2 재질 / tied 1개** 로 고정되어 있다. CAD 레이어(`Module.py`)에 `shapesFront`/`shapesBack` 두 dict만 존재하므로 재질을 2개 이상 부여할 수 없고, dimension 스키마가 정확히 5값(`[radius, outerRadius, hFront, hBack, backRadius]`)으로 하드코딩되어 단(stage) 추가 여지가 없다.

사용자 요구는 **고무팁 + 중간단 + 본체 = 3단**이다 (8파이 케이스: 고무팁 ⌀8→⌀20 필렛 h6 ρ1.18 / ⌀20 SUS h14 / ⌀44.5 SUS h38 = 400g). 15파이는 2단으로도 표현 가능하므로 3단은 **추가**되어야 하며 **기존 2단은 절대 깨지면 안 된다(하위호환 필수)**.

**검증 중 발견한 LENS 2 누락:** 동일 cylinder 로직을 가진 함수가 2개가 아니라 **3개**다.
- `DropWeightImpactTestwithPartialRigid` (L3185) — part 인라인 생성(L3366), 메시(L3497), tied(L3529)
- `DropWeightImpactTest` (L3554) — part 인라인(L3778), 메시(L4016), tied(L4050)
- `DropWeightImpactTestbyPart` (L4321) — part를 **헬퍼 `CreateCylinderImpactorPart`(L4700)** 로 분리, 호출 L4450, 메시 L4580-4592, tied L4608-4613

세 번째 경로는 헬퍼가 8-tuple을 반환하므로 mid 추가 시 **반환 시그니처까지 바뀐다.** 한쪽이라도 누락하면 robust_contact / 재사용(reusable_pids)에서 mid part가 silent miss 된다.

---

## 2. 3단 확장 설계

### 2.1 CAD 형상 — `Module.py` `CylinderwithMassImpactModule` (L64-138)

`__init__`(L65)에 mid 파라미터 추가, **default=0 이면 2단 동작**(하위호환 핵심):

```python
def __init__(self, id, name, radius=1, outerRadius=1.2, heightFront=0.5,
             heightBack=1.0, center=..., zDir=..., backRadius=1.2,
             midRadius=0, heightMid=0):   # 0 → 2단
```

L78-79 dict 선언에 `self.shapesMid = {}` 추가. `GenerateShape`(L85)에서 단 순서를 **front(고무) → mid → back(본체)** 로 재배치:
- mid 활성(`heightMid>0`) 시 back의 축 원점은 `center + zDir*(heightFront+heightMid)` 로 이동 (L108-110 패턴 확장: `zDirwithAmpHeightFront+heightMid`).
- mid 실린더 = `BRepPrimAPI_MakeCylinder(axisMid, midRadius, heightMid)`, 축 원점 = `center + zDir*heightFront`.
- 단차 fillet: `filletMidRadius = midRadius - outerRadius`, `filletBackRadius = backRadius - midRadius` 로 재계산. 음수→0 가드는 기존 L115-116 그대로. fillet edge 선택은 검증된 `i==3` 패턴(L100-104) 재사용 — mid/back 모두 raw cylinder라 topology 순서 동일하게 유효.
- shape 등록(L129-134): mid 활성 시 `maxShapeID` 1회 더 증가 + `shapes`/`shapesMid` 등록. **mid 미활성이면 등록 건너뛰어 기존 2개 shape 그대로** → 2단 완전 보존.

ModuleManager.py L18 시그니처에 `midRadius=0, heightMid=0` 추가, L20 생성자 호출에 전달.

### 2.2 dimension 스키마 확장 — zero-hardcode 권장 (stages)

현재 `[radius, outerRadius, hF, hB, backRadius]` 5값. 두 방식 병행:
- **하위호환:** 5값 → 2단 (현행 그대로).
- **3단:** 7값 `[radius, outerRadius, hFront, midRadius, hMid, backRadius, hBack]`. 길이로 단수 판별(`len==5`→2단, `len==7`→3단). 단순·명시적이라 stage dict 도입보다 코드 변경 표면적이 작다.

scenario.json 레이어(2.5)에서는 가독성을 위해 `cylinder_stages` list를 두고 Runner가 flat dimension으로 직렬화 → 기존 dimension 파이프라인 무손실 재사용 (VibrationSource registry의 평탄화 결 답습).

### 2.3 메시/재질 — `KooDynaAdvancedModification.py` (3개 함수 대칭)

**재질/part:** front/back 사이에 mid 삽입. 인라인 2함수(L3366-3373 / L3778-3785)와 헬퍼(L4700~)에 `materialImpactorMid` + `impactMidPart` 추가. mid는 `heightMid>0`(또는 dimension 길이 7) 일 때만 생성하는 **조건 게이트** 필수 — 2단 경로에서 None.

옵션 읽기 블록(L3210-3244, L3580-3614, 헬퍼 L4758~)에 `MaterialIDImpactorMid / YoungsModulusImpactorMid / PoissonRatioImpactorMid / DensityImpactorMid` 4개 default 추가.

**메시(L3497-3499 / L4016-4018 / L4580-4592):**
```python
impactorPart.GenerateTetraMeshfromShapes(simodule.shapesBack, ...)
impactFrontPart.GenerateTetraMeshfromShapes(simodule.shapesFront, ...)
if heightMid > 0:
    impactMidPart.GenerateTetraMeshfromShapes(simodule.shapesMid, ...)  # 신규
```

**헬퍼 반환 시그니처(L4700 L96):** mid 활성 시 `impactMidPart, materialImpactorMid, sectionImpactorMid, impactMidElemMan` 4개를 tuple에 추가. 호출부 L4450 언팩도 동시 수정 — **둘 중 하나만 고치면 ValueError.** mid 비활성 호환 위해 항상 12-tuple 반환하되 mid 슬롯에 None 채우는 방식 권장(언팩 길이 고정).

### 2.4 tied contact — front↔mid↔back

현 tied 1개(L3529 / L4050 / L4613, `CreateContactTiedSurfacetoSurfaceOffset(SSID, MSID,3,3,...)`)를 mid 활성 시 **2개**로:
- tied A: SSID=`impactFrontPart.id`, MSID=`impactMidPart.id`
- tied B: SSID=`impactMidPart.id`, MSID=`impactorPart.id`(back)

초기속도: front/back에 더해 mid에도 `CreateInitialVelocityGeneration(impactMidPart.id,...)` 추가 (L3525 / L4035·4047 / L4611 패턴). 접촉 바닥판 SS의 MSID는 여전히 front(L3521) — mid는 접촉 지표에 노출 안 됨.

### 2.5 KooMeshModifier 파싱 — `KooMeshModifier.py`

**재질 옵션(L1088-1147):** Front 블록 4쌍을 복제해 `...ImpactorMid` 4개 추가:
```python
elif "youngsmodulusimpactormid" in line.lower(): curOptions["YoungsModulusImpactorMid"] = ...
# poissonratio / materialid / density 동일 4쌍
```
주의: `elif` 체인에서 `"impactormid"` 가드를 `"impactor"` 보다 **위**에 둘 것 — `"impactor" in "...impactormid"` 가 True라 순서 틀리면 mid가 impactor로 잘못 매칭(L1096/1128/1144 silent miss).

**dimension(L1222-1232):** cylinder 분기에 길이 분기 추가:
```python
elif curOptions["Type"].lower() == "cylinder":
    vals = [KooDynaFloat(svector[k]) for k in range(1, len(svector))]
    if len(vals) == 7:   curOptions["Dimension"] = vals            # 3단
    elif len(vals) >= 5: curOptions["Dimension"] = vals[:5]        # 2단 (현행)
    else:                curOptions["Dimension"] = vals + [vals[1]] # v5=v2 보정
```

### 2.6 exceptPIDs / reusable_pids — silent miss 최대 위험

front/impactor PID가 다수 산재 등록됨: L3429-3432, L3465-3468(except), L4475-4477·4534-4537(reusable, byPart). mid 활성 시 **모든 지점에 `impactMidPart.id` 동반 등록** 필수. 누락 시 robust_contact가 mid를 강체 변환하거나 재사용 cleanup에서 mid 노드를 안 지워 잔류 → 질량 오차·접촉 오류. 헬퍼 함수 한 곳(`_register_impactor_pids`)으로 묶어 3경로에서 호출하면 누락 구조적 방지(권장).

---

## 3. 구현 단계 (파일별 + 검증)

| # | 작업 | 파일/위치 | verify |
|---|------|-----------|--------|
| 1 | CAD mid 추가 (default 0) | `Module.py` L65,78,108-134 / `ModuleManager.py` L18,20 | 단독 GenerateShape: midRadius=0 → shape 2개(2단 동일), midRadius>0 → 3개 |
| 2 | dimension 7값 파싱 | `KooMeshModifier.py` L1222-1232 | 5값→len5, 7값→len7, `impactormid` 가드 순서 |
| 3 | mid 재질 4쌍 파싱 | `KooMeshModifier.py` L1088-1147 | curOptions에 4키, impactor와 분리 매칭 |
| 4 | 재질/part/메시/tied/PID — **3함수 대칭** | `KooDynaAdvancedModification.py` L3366·3497·3529·3429 / L3778·4016·4050·3848 / 헬퍼 L4700+L4450 | dimension=5 → 기존 .k diff 無 (하위호환 회귀) |
| 5 | scenario stages → dimension 직렬화 | Runner (CumulativeScenarioRunner) | 8파이 stages → dimension 7값 |
| 6 | e2e | 8파이/15파이 | 질량 ±2%, tied 면 정렬, NFS(`/data/koopark/Test_*`)에서 실행 |

**최우선 회귀 기준:** dimension 5값 입력 시 mid 분기 전체가 비활성, 생성 .k가 변경 전과 **byte-identical**. 이게 통과해야 하위호환 보증.

---

## 4. stages 정의 예시 (scenario.json)

8파이 (400g, 고무팁 + SUS 2단):
```json
"impactor": {
  "type": "cylinder",
  "cylinder_stages": [
    {"role":"front", "diameter":8,  "outer_diameter":20, "height":6,  "density":1.18e-9, "youngs_modulus":7.8,    "poisson":0.49, "material":"rubber"},
    {"role":"mid",                   "diameter":20,       "height":14, "density":6.57e-9, "youngs_modulus":2.07e5, "poisson":0.3,  "material":"SUS"},
    {"role":"back",                  "diameter":44.5,     "height":38, "density":6.57e-9, "youngs_modulus":2.07e5, "poisson":0.3,  "material":"SUS"}
  ]
}
```
→ Runner 직렬화: `Dimension = [4, 10, 6, 10, 14, 22.25, 38]` (radius=⌀/2; mid 단차 fillet = midR−outerR = 0, back 단차 = 22.25−10).

15파이 (500g, 전체 SUS) — 2단으로 표현, 기존 5값 경로 그대로:
```json
"cylinder_stages":[
  {"role":"front","diameter":15,"outer_diameter":44.5,"height":15,"density":6.854e-9,"youngs_modulus":2.07e5,"material":"SUS"},
  {"role":"back","diameter":44.5,"height":45.01,"density":6.854e-9,"youngs_modulus":2.07e5,"material":"SUS"}
]
```
→ `Dimension = [7.5, 22.25, 15, 45.01, 22.25]` (5값, mid 비활성).

---

## 5. 위험요소

1. **OCC fillet 실패:** mid 단차 fillet radius(`midR−outerR`)가 단 높이보다 크면 `fillet.Build()` 예외. 음수 가드(L115-116) 외에 `min(filletR, height*0.49)` 클램프 권장. `i==3` edge 선택은 raw cylinder에서만 검증됨 — mid도 raw라 유효하나 fillet된 shape엔 edge 인덱스가 바뀌므로 단을 순차 fillet하지 말 것.
2. **tied contact 정렬:** front↔mid, mid↔back 두 면이 `heightFront`, `heightFront+heightMid` 평행이동으로 정확히 면접촉해야 tied가 잡힘. CAD 좌표는 맞지만 tet 메시가 면에서 갈라지면 tied 누락 → 단 분리. SST/MST=3(L3529) offset 유지.
3. **질량 오차:** stages 밀도/체적이 목표 질량(400/500g)과 일치하는지 Runner에서 사전 검산(체적×ρ 합) 후 경고. fillet 전이부 체적 손실로 ±1-2% 발생 가능.
4. **silent miss(최대):** §2.6 PID 산재 등록 + §2.3 헬퍼 8→12 tuple. 3함수 비대칭이 근본 위험원 — PID 등록·part 생성을 헬퍼로 단일화하면 구조적으로 차단.

---

**핵심 변경 지점 요약:** `Module.py` L65/78/108-134 (CAD mid+shapesMid, default 0 하위호환) · `ModuleManager.py` L18/20 · `KooMeshModifier.py` L1088-1147(mid 재질, 가드순서)/L1222-1232(7값) · `KooDynaAdvancedModification.py` **3함수 대칭** (인라인 2개 L3366·3497·3529 / L3778·4016·4050, 헬퍼 1개 L4700+호출 L4450) + PID 산재 등록 L3429·3465·4475·4534. LENS 2가 놓친 세 번째 경로(`DropWeightImpactTestbyPart` → `CreateCylinderImpactorPart` 8-tuple)가 가장 누락되기 쉬운 지점이다.

---

## 부록: CAD 분석 (LENS1)

# LENS 1 — 실린더 2단 CAD 형상 생성 코드 분석

## 1. `__init__` 파라미터 (line 65)
- `radius=1`: front 실린더 바닥 fillet 후 유효 반경 (실제 외경 - fillet 반경)
- `outerRadius=1.2`: **front 실린더 실제 반경** (line 92에서 사용)
- `heightFront=0.5`: front 실린더 높이
- `heightBack=1.0`: back 실린더 높이
- `backRadius=1.2`: **back 실린더 반경** (line 111)
- `center`, `zDir`: 위치/축 방향. `zDir`은 line 73-74에서 정규화

## 2. GenerateShape 흐름
**Front 실린더 + 바닥 fillet (line 88-106):**
- `axis = gp_Ax2(center, zDirVec, xDirVec)` → `cylinder = BRepPrimAPI_MakeCylinder(axis, outerRadius, heightFront)`
- `filletRadius = outerRadius - radius` (line 95)
- edge 순회 중 `i == 3`번째 edge에 fillet 적용 (line 100-104)

**Back 실린더 + 단차 fillet (line 108-126):**
- `axisBack` 원점 = `center + zDir*heightFront` → front 끝이 back 시작 (line 108-110, **4번 항목**)
- `cylinderBack = BRepPrimAPI_MakeCylinder(axisBack, backRadius, heightBack)`
- `filletBackRadius = backRadius - outerRadius`, 음수면 0 (line 114-116)
- 양수일 때만 `i == 3` edge에 단차 fillet (line 118-126)

## 3. shapesFront / shapesBack 분리 (line 129-134)
`maxShapeID` 증가시키며 `shapes`(전체) + `shapesFront`/`shapesBack`(재질 분리용)에 각각 등록. 2개 shape만 존재.

## 4. axisBack 위치 계산 (line 108-110)
```python
zDirwithAmpHeightFront = (zDir[0]*heightFront, zDir[1]*heightFront, zDir[2]*heightFront)
axisBack = gp_Ax2(gp_Pnt(center[0]+...[0], ...), zDirVec, xDirVec)
```
front 높이만큼 zDir 방향 평행이동 → 두 실린더 면접촉.

## 5. fillet 적용 방식 (`i == 3`)
```python
for e in TopologyExplorer(cylinder).edges():
    i += 1
    if i == 3:
        fillet.Add(filletRadius, e)
```
edge 순회 카운터의 3번째(바닥 원형 edge)만 선택. **하드코딩 가정** — back에서도 동일 `i==3` 사용.

## 3단 확장 정확 지점
1. **`__init__` (line 65)**: `radius3rd`/`heightThird`/`thirdRadius` 파라미터 추가.
2. **GenerateShape (line 126 직후)**: back 블록을 복제해 3단 실린더 생성. `axisThird` 원점 = `center + zDir*(heightFront+heightBack)` (line 108-110 패턴 확장).
3. **단차 fillet**: `filletThirdRadius = thirdRadius - backRadius`, `i==3` edge 패턴 재사용 (line 114-126).
4. **shape 등록 (line 132-134 직후)**: `maxShapeID` 1회 더 증가 + `shapes`/`shapesBack`(또는 신규 `shapesThird` dict) 등록. dict는 line 78-79에서 선언 추가 필요.

핵심 주의: `i==3` edge 선택이 모든 단에서 유효한지는 OCC topology 순서에 의존 — back/third 실린더가 fillet된 shape이 아닌 raw cylinder이므로 동일 패턴 유효함.

대상 파일: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/occProject/Generators/KooODBCADManager/Module.py` (line 64-138)

## 부록: 메시/재질 흐름 (LENS2)

LENS 2 — 실린더 임팩터 호출/메시/재질 분기 전체 흐름 (현행 2단 구조)

현재 실린더는 **front(고무팁) + back(본체) = 2 part / 2 재질 / tied 1개** 구조. 3단(고무팁+중간단+본체)으로 확장 시 영향 위치:

## 1. dimension[5] → CAD 인자 매핑
`dimension = [radius, outerRadius, height1, height2, backRadius]` (5값) → `CreateCylinderwithMassImpactModule(name, radius, outerRadius, height1, height2, impactLoc, zDir, backRadius)`
- 파싱: `KooMeshModifier.py:1217-1232` — cylinder는 정확히 5값 파싱(부족 시 v5=v2 보정). **3단이면 height3/midRadius 추가 → 6~7값 파싱 분기 + 시그니처 인자 추가**
- 매핑: `KooDynaAdvancedModification.py:3487-3494`(1차) / `3997-4013`(2차) — 두 곳 동일하게 dimension 언팩 + 호출
- CAD 시그니처: `ModuleManager.py:18` — 8인자. **midRadius/height3 인자 추가 + 내부 shapesMid 생성 필요**

## 2. part/재질 생성 (front=고무, back=SUS)
`KooDynaAdvancedModification.py:3366-3387`(1차) / `3784-3809`(2차):
- front: matIDImpactorFront / rho·E·nuImpactorFront → `materialImpactorFront`, `impactFrontPart` (L3366-3373)
- back: matIDImpactor / ...Impactor → `materialImpactor`, `impactorPart` (L3380-3387)
- **3단이면 중간단 part/재질 = `impactMidPart` + `materialImpactorMid` 신규 (두 함수 모두)**

## 3. 메시 생성 (GenerateTetraMeshfromShapes)
`L3497-3499`(1차) / `4016-4018`(2차):
- `impactorPart ← simodule.shapesBack`, `impactFrontPart ← simodule.shapesFront`
- **`impactMidPart ← simodule.shapesMid` 추가**

## 4. tied contact (front↔back)
`L3528-3529`(1차) / `4049-4050`(2차): `CreateContactTiedSurfacetoSurfaceOffset(impactFront, impactor, ...)` 1개.
초기속도: `L3515/3525`, 접촉 SS(L3521 `MSID=impactFrontPart`). **3단이면 tied 2개(front↔mid, mid↔back) 필요**

## 5. 재질 옵션 파싱 (KooMeshModifier)
`L1090-1147`: Front/Impactor 각각 E·nu·matID·rho 4쌍 = 2재질. **Mid용 4쌍(`...ImpactorMid`) 추가 + curOptions 전달**

## 6. exceptPIDs/reusable_pids (robust_contact·재사용)
`L3431-3432, 3467-3468, 3848-3879, 3942-3944, 4131, 4219, 4477, 4537`: front/impactor PID 등록 다수. **mid PID 동일 등록 누락 시 silent miss 위험.**

---
**확장 위치 요약 (3 모듈):**
- `ModuleManager.py:18` — 시그니처+shapesMid
- `KooMeshModifier.py:1090-1147`(Mid 재질 파싱), `1217-1232`(dimension 6값)
- `KooDynaAdvancedModification.py` — **2개 함수 대칭**: 재질/part(3366·3784), 메시(3497·4016), tied(3528·4049), exceptPIDs/reusable(3431·3848 외 다수)

핵심 위험: 동일 로직이 **2개 함수에 중복** + PID 등록이 산재 → 한쪽 누락 시 robust_contact/재사용에서 mid part 빠짐.