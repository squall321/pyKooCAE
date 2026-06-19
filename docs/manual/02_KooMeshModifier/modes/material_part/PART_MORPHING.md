# KooMeshModifier 모드: PART_MORPHING

> 근거 코드:
> - `occProject/Generators/KooMeshModifier.py`
> - `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py`
> - `occProject/Generators/KooCAEManager/KooPart.py`

## 1. 목적/개요

`PART_MORPHING` 모드는 지정한 파트(PID)의 **표면(경계) 절점을 박스(box) 영역 기준으로 한 방향(zDir)으로 밀거나(Push) 당겨(Pull)** 형상을 국소 변형(모핑)하는 모드이다. 즉, 메시 토폴로지(요소 연결성)는 유지한 채 절점 좌표만 이동시켜 돌출/함몰 같은 형상 변형을 만든다.

변형 영역은 사용자가 정의한 사각 박스(평면 폴리곤)이며, 박스 모서리로부터의 평면 거리(`inplaneDistances`)가 영향 반경(`EffectRadius`) 이내인 경계 절점만 코사인 감쇠 가중치로 이동한다 (KooPart.py:761-774). 변형 방향은 zDir, 변형량은 `PushDistance` 이다.

선택적으로 `meshsize` 가 주어지면, 변형 전에 해당 솔리드 파트의 표면 메시만 추출해 STL로 내보낸 뒤 **솔리드 메시를 재생성(remesh)** 하고 나서 모핑한다 (KooDynaAdvancedModification.py:5615-5634).

세 종류의 변형 영역 정의 방식을 지원한다.
- `morphbox` — 사용자가 박스의 위치·크기·방향을 모두 직접 지정 (`Type="Box"`).
- `morphpid` / `morphfrompidbox` — 대상 파트의 바운딩 박스를 박스로 사용 (`Type="PIDBOX"`). 위치/크기는 파트 경계상자에서 자동 계산.

> 참고: 전용 예제 파일 없음. 본 문서는 코드 근거로만 작성됨. (Examples 디렉터리에 `part_morphing` / `**partmorphing` 관련 입력·시나리오 파일 부재 확인.) 아래 "사용 예제"는 코드 파서가 기대하는 형식을 근거로 재구성한 최소 골격이며, 실측 예제로 검증된 것은 아니다 — **확인 필요**.

## 2. 입력 옵션·인자 (표)

입력은 KooMeshModifier 제어 파일의 두 블록으로 나뉜다.

### 2-1. `*mode` 블록 (모드 등록 트리거)

`*mode` 블록 안에 한 줄로 모드를 등록한다 (KooMeshModifier.py:234-269).

| 토큰 | 의미 | 비고 |
|------|------|------|
| `part_morphing` | 모드 식별자 (대소문자 무관, `svector[0]`) | line 267 |
| `<modeID>` | 모드 ID (정수, `svector[1]`) | `**partmorphing` 옵션 블록과 매칭되는 키 (line 269) |

형식: `part_morphing,<modeID>`

### 2-2. `**partmorphing,<modeID>` 옵션 블록

옵션 블록은 `**partmorphing,<modeID>` 로 시작하고 `**end`(또는 빈 줄)에서 종료한다 (KooMeshModifier.py:875-1035). 블록 기본값: `UnitScale=1.0`, `GenerateMesh=False`, `MeshSize=1.0`, `Morph={}` (line 879-882).

#### 공통 헤더 키워드

| 키워드 | 형식 | 의미 | 근거 |
|--------|------|------|------|
| `unitscale,<float>` | 콤마 구분 | STL 내보내기 단위 스케일. `curOptions["UnitScale"]` | line 892-893 |
| `meshsize,<float>` | 콤마 구분 | 솔리드 재생성 시 메시 크기. **지정 시 `GenerateMesh=True` 로 강제** (즉 remesh 활성화) | line 894-896 |

#### 변형 영역 정의 라인 (택1 또는 복수)

각 라인은 `morphid` 순서로 누적되며 같은 블록에 여러 개 둘 수 있다. 라인의 괄호 `( )` 는 제거 후 콤마 파싱된다 (line 898-902 등).

`morphbox` (직접 박스 지정, `Type="Box"`, KooMeshModifier.py:991-1033):

| 인덱스 | 토큰 | 의미 |
|--------|------|------|
| svector[1] | `pid` | 변형 대상 파트 ID (int) |
| svector[2-4] | `xloc,yloc,zloc` | 박스 중심 위치 |
| svector[5-7] | `xLength,yLength,zLength` | 박스 변 길이 |
| svector[8-10] | `xdirX,xdirY,xdirZ` | x축 방향 벡터(정규화됨) |
| svector[11-13] | `zdirX,zdirY,zdirZ` | z축(변형) 방향 벡터(정규화됨) |
| svector[14] | `pushDistance` | 변형량. `>0` → `Mode="Pull"`, `≤0` → `Mode="Push"`, 저장값은 절댓값 |
| svector[15] | `EffectRadius` | 영향 반경(코사인 감쇠) |
| svector[16] | `angle` | 경계 절점 선택 각도. `360` 이면 전체 boundaryNodes 사용 |

형식: `morphbox,<pid>,<xloc>,<yloc>,<zloc>,<xLen>,<yLen>,<zLen>,<xdirX>,<xdirY>,<xdirZ>,<zdirX>,<zdirY>,<zdirZ>,<pushDistance>,<EffectRadius>,<angle>`

`morphpid` (대상 파트 경계상자를 박스로, `Type="PIDBOX"`, KooMeshModifier.py:897-944):

| 인덱스 | 토큰 | 의미 |
|--------|------|------|
| svector[1] | `pid` | 변형 대상 파트 ID |
| svector[2] | `ptargetid` | TargetPID (`morphOption["TargetPID"]`) — 파서에 저장되나 PartMorphingPIDBox 동작에서는 미사용. 확인 필요 |
| svector[3-5] | `xdirX,xdirY,xdirZ` | x축 방향(정규화) |
| svector[6-8] | `zdirX,zdirY,zdirZ` | z축(변형) 방향(정규화) |
| svector[9] | `pushDistance` | 변형량(부호로 Push/Pull 결정, 절댓값 저장) |
| svector[10] | `EffectRadius` | 영향 반경 |
| svector[11] | `angle` | 경계 절점 선택 각도 |
| svector[12] | `numX` | `NumberofBoxXDirection` (저장되나 동작에서 미사용. 확인 필요) |
| svector[13] | `numY` | `NumberofBoxYDirection` (저장되나 동작에서 미사용. 확인 필요) |

> 위치(`Location`)와 박스 크기(`XLength/YLength/ZLength`)는 `morphpid`/`morphfrompidbox` 에서 파서상 모두 `0.0` 으로 들어가며 (line 905-910), 실제 값은 동작 단계에서 파트 바운딩 박스로 채워진다 (KooDynaAdvancedModification.py:5587-5601).

`morphfrompidbox` (KooMeshModifier.py:946-989): `morphpid` 와 동일한 `Type="PIDBOX"` 옵션을 만들되 `numX/numY` 인자가 없는 11-토큰 형식이다.

형식: `morphfrompidbox,<pid>,<ptargetid>,<xdirX>,<xdirY>,<xdirZ>,<zdirX>,<zdirY>,<zdirZ>,<pushDistance>,<EffectRadius>,<angle>`

## 3. 사용 예제

> 전용 예제 파일이 없어 아래는 코드 파서 형식을 근거로 한 **최소 골격**이다 (검증되지 않음 — 확인 필요).

```
*Inputfile
MinimumModel.k
*Mode
part_morphing,1
*End

**partmorphing,1
meshsize,1.0
morphbox,3,0.0,0.0,10.0,20.0,20.0,5.0,1.0,0.0,0.0,0.0,0.0,1.0,2.0,8.0,360
**end
```

위 예에서 파트 3의 경계 절점 중, 중심 `(0,0,10)`·크기 `20x20x5`·zDir `(0,0,1)` 박스로부터 평면거리 8 이내인 절점을 변형한다. `pushDistance=2.0`(>0)이므로 `Mode="Pull"`로 분기되며, Pull 일 때 코어에서 부호가 반전되어(KooPart.py:757-758) 절점은 -z 방향으로 최대 2 만큼 이동한다. `meshsize,1.0` 으로 인해 변형 전 솔리드 remesh 가 수행된다.

> 주의: `pushDistance>0` 이면 `Mode="Pull"`, `≤0` 이면 `Mode="Push"` 로 분기되며(line 934-937, 1025-1028), Pull 일 때 실제 이동 부호가 `distance = -distance` 로 반전된다 (KooPart.py:757-758). 의도한 방향이 나오도록 부호를 반드시 확인할 것.

## 4. 동작 원리 (코드 근거)

1. **등록·디스패치**: `*mode` 파싱에서 `part_morphing` → `modeList`에 `PART_MORPHING` 등록 (KooMeshModifier.py:267-269). `GenerateModifiedFile()` 의 분기 `elif mode == "PART_MORPHING"` 에서 `GeneratePartMorphing(modeid)` 호출, 출력 접미어 `_pm` 누적 (KooMeshModifier.py:2831-2833).
2. **옵션 추출**: `GeneratePartMorphing` 가 `modeIDOption[modeid]` 에서 `Morph`(영역 리스트), `UnitScale`, `MeshSize`, `GenerateMesh` 를 꺼내 `subOption` 으로 묶어 `advancedModification.PartMorphing(curOption, subOption)` 호출 (KooMeshModifier.py:2615-2624).
3. **타입 분기**: `PartMorphing` 가 각 영역의 `Type` 에 따라 `Box`→`PartMorphingBox`, `PIDBOX`→`PartMorphingPIDBox` 로 분기 (KooDynaAdvancedModification.py:5570-5576).
4. **PIDBOX 경계상자 산출**: `PartMorphingPIDBox` 는 대상 파트의 `GetBoundaryBox()` 로 min/max 를 구해 중심(`location`)과 변 길이(`xLength` 등)를 계산한다 (KooDynaAdvancedModification.py:5587-5601). `PartMorphingBox` 는 사용자가 준 `Location`/`XLength` 등을 그대로 사용한다 (KooDynaAdvancedModification.py:5643-5651).
5. **선택적 remesh**: `GenerateMesh == True`(= `meshsize` 지정) 이면 `AddSTLPartfromKooPart` → `ExportSTL("temp.stl", "", unitscale)` 로 표면 추출 후, 기존 솔리드 절점/요소를 제거하고 `GenerateSolidMeshfromSurfaceMesh(meshSize, meshSize)` 로 재생성한 뒤 모핑한다 (KooDynaAdvancedModification.py:5615-5634, 5668-5687).
6. **모핑 코어** `MorphwithBox` (KooPart.py:721-796):
   - `angle==360` 이면 전체 `boundaryNodes`, 아니면 `GetBoundaryNodesWithVectorwithAngle(zDir, angle)` 로 zDir 기준 각도 내 경계 절점만 선택 (line 723-728).
   - xDir/yDir(=zDir×xDir)/zLength·xLength 로 박스 평면 폴리곤 4점(p1~p4) 구성 (line 738-749).
   - `distance_from_prism_edge` 로 각 경계 절점의 평면 내 거리 산출 (line 753).
   - `Mode=="Pull"` 이면 `distance = -distance` (line 757-758).
   - 거리 `0 ≤ inDistance < effectRadius` 인 절점만 `factor = cos((π/2)·(inDistance/effectRadius))` 가중치로 zDir 방향 이동 (line 765-774).
   - `angle==360` 이면 `LaplacianSmoothingwithoutExceptedNodes(boundaryNodes, 2)`, 아니면 박스+effectRadius 범위 XY 절점에 `ZAxisSmoothingwithNodesandExceptedNodes(... 7, zDir)` 평활화 적용 (line 777-796).
7. **출력**: 모핑은 동일 `dynaImporter` 모델 내 절점 좌표를 in-place 수정한다. `PART_MORPHING` 은 `_skip_default_write` 를 설정하지 않으므로 (KooMeshModifier.py:2831-2833) 기본 출력 경로인 `WriteModifiedFile("_pm")` 로 변형된 전체 모델이 `_pm` 접미어가 붙은 .k 로 기록된다 (KooMeshModifier.py:2883-2891).

## 5. 주의사항·한계

- **부호 규약 혼동**: `pushDistance>0` → Pull, `≤0` → Push. 직관과 반대이므로 의도한 방향 검증 필수 (KooMeshModifier.py:934-937; KooPart.py:757-758).
- **저장만 되고 미사용인 인자**: `morphpid` 의 `TargetPID`, `numX`/`numY` 는 옵션에 저장되지만 PIDBOX 동작 경로에서 사용되지 않음 (KooDynaAdvancedModification.py:5579-5638). 동작에 영향 없음 — 확인 필요.
- **블록 종료 조건**: 옵션 블록 루프는 빈 줄 또는 `**end` 에서 종료된다 (KooMeshModifier.py:888-891). 영역 라인 사이에 빈 줄을 넣으면 그 시점에 블록이 조기 종료되니 주의.
- **PID 미존재**: `PartMorphingPIDBox` 에서 대상 PID 가 파트에 없으면 `"Part ID is not found"` 출력 후 해당 영역을 건너뜀 (KooDynaAdvancedModification.py:5581-5585).
- **remesh 부작용**: `meshsize` 지정 시 솔리드 절점/요소가 제거되고 표면 메시로부터 재생성되므로, 기존 요소 ID/물성 매핑·세트 참조가 영향을 받을 수 있다 (KooDynaAdvancedModification.py:5619-5632). 임시 파일 `temp.stl` 이 작업 디렉터리에 생성됨.
- **대상 요소 타입**: 솔리드 경계(`GetExternalTriBoundary`)·바운딩 박스 기반 로직이며 (KooPart.py:808-817), 셸 단독 파트 등에 대한 동작은 코드상 명확치 않음 — 확인 필요.
- **예제 부재**: Examples/시나리오에 실사용 입력이 없어 실측 검증이 어려움 — 확인 필요.

## 6. 개발 현황

**구현됨.** 트리거 등록(KooMeshModifier.py:267-269), 디스패치(KooMeshModifier.py:2831-2833), 옵션 파서(KooMeshModifier.py:875-1035), 핸들러 `PartMorphing`/`PartMorphingPIDBox`/`PartMorphingBox`(KooDynaAdvancedModification.py:5570-5690), 모핑 코어 `MorphwithBox`(KooPart.py:721-796)까지 전체 경로가 코드에 존재한다. 다만 `morphpid` 의 `TargetPID`/`numX`/`numY` 인자는 파서에만 존재하고 동작에서 사용되지 않아 일부 입력 파라미터는 미연동 상태이며, 전용 예제·테스트가 없어 실측 검증은 미확인이다.
