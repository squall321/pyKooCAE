# DYNAIN_TO_INITIAL 모드 상세 분석

## 1. 개요

**목적**: LS-DYNA 동적 이완(Dynamic Relaxation) 시뮬레이션 결과(dynain 파일)를 초기 조건으로 로드하여 새로운 시뮬레이션의 시작점으로 사용

**파일 위치**:
- 파서: `KooMeshModifier.py` (라인 677-716)
- 실행: `KooDynaAdvancedModification.py` (라인 4461-4556)

**출력 접미사**: `_dti`

---

## 2. 이 모드가 필요한 이유

### 2.1 동적 이완 (Dynamic Relaxation) 개념

동적 이완은 정적 평형 상태를 얻기 위한 수치적 방법입니다:

```
┌─────────────────────────────────────────────────────────────────┐
│                    동적 이완 프로세스                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  초기 상태                    동적 이완                   평형 상태 │
│  (무응력)        ──────►    (감쇠 진동)      ──────►    (응력 분포) │
│                                                                  │
│  ┌─────┐                     ┌─────┐                  ┌─────┐   │
│  │     │                     │ ~~~ │                  │     │   │
│  │     │      자중/구속       │ ~~~ │     수렴        │ === │   │
│  │     │    ──────────►      │ ~~~ │  ──────────►    │ === │   │
│  │     │                     │ ~~~ │                  │ === │   │
│  └─────┘                     └─────┘                  └─────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 워크플로우에서의 역할

```
1. DROP_ATTITUDE 실행
   └── 낙하 시뮬레이션 모델 생성 (동적 이완 포함)

2. LS-DYNA 실행
   └── 동적 이완으로 평형 상태 도달
   └── dynain 파일 출력 (노드 위치 + 응력 상태)

3. DYNAIN_TO_INITIAL 실행  ◄── 이 모드
   └── dynain 결과를 현재 모델에 적용
   └── 임시 구조물(바닥, 접촉) 제거
   └── 좌표계 복원
   └── 새로운 시뮬레이션 준비 완료

4. 실제 충격 시뮬레이션
   └── 초기 응력이 포함된 상태로 정확한 해석
```

---

## 3. 함수 호출 흐름

```
KooMeshModifier.ImportOption()
    │
    ├── **DynainToInitial 블록 파싱
    │       └── modeIDOption[modeid] 에 옵션 저장
    │
    └── GenerateDynainToInitial(modeid)
            │
            └── advancedModification.DynaintoInitial(option, folderPath, filePath)
                    │
                    ├── 1. 옵션 파싱 (경로, 플래그들)
                    ├── 2. 동적 이완 설정 제거 (선택)
                    ├── 3. 원점 복귀용 기준 노드 결정
                    ├── 4. dynain 파일 로드 (새 KooDynaImporter)
                    ├── 5. 응력 데이터 처리 (선택)
                    ├── 6. 현재 모델에 덮어쓰기
                    ├── 7. 좌표 변환 (원점 복귀)
                    ├── 8. 파트/접촉 제거
                    └── 9. 동적 이완 재설정 (선택)
```

---

## 4. 설정 파일 옵션 상세

### 4.1 파서 구조 (KooMeshModifier.py, 라인 677-716)

```python
def ParseDynaintoInitial(self, optionid, curOption, curKeyword):
    if "dynainpath" in optionid.lower():
        curOption["DynainPath"] = curKeyword[0]
    elif "includestress" in optionid.lower():
        if "true" in curKeyword[0].lower():
            curOption["IncludeStress"] = True
        else:
            curOption["IncludeStress"] = False
    elif "removedynamicrelaxation" in optionid.lower():
        if "true" in curKeyword[0].lower():
            curOption["RemoveDynamicRelaxation"] = True
        else:
            curOption["RemoveDynamicRelaxation"] = False
    elif "dynamicrelaxation" in optionid.lower():
        if "true" in curKeyword[0].lower():
            curOption["DynamicRelaxation"] = True
        else:
            curOption["DynamicRelaxation"] = False
    elif "movetooriginbynode" in optionid.lower():
        curOption["MovetoOriginbyNode"] = curKeyword
    elif "movetooriginautomatic" in optionid.lower():
        if "true" in curKeyword[0].lower():
            curOption["MovetoOriginAutomatic"] = True
        else:
            curOption["MovetoOriginAutomatic"] = False
    elif "removepartbyname" in optionid.lower():
        curOption["RemovePartNameList"] = curKeyword
    elif "removepartbyid" in optionid.lower():
        curOption["RemovePartIDList"] = curKeyword
    elif "removecontactbyid" in optionid.lower():
        curOption["RemoveContactIDList"] = curKeyword
```

### 4.2 전체 옵션 목록

| 옵션명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| DynainPath | string | dynain 파일 경로 | "dynain" |
| IncludeStress | bool | 초기 응력 포함 여부 | False |
| RemoveDynamicRelaxation | bool | 동적 이완 설정 제거 | False |
| DynamicRelaxation | bool | 새 동적 이완 설정 추가 | False |
| MovetoOriginByNode | List[int] | 기준 노드 ID 3개 | [] |
| MovetoOriginAutomatic | bool | 자동 원점 복귀 | False |
| RemovePartNameList | List[str] | 이름으로 파트 제거 | [] |
| RemovePartIDList | List[int] | ID로 파트 제거 | [] |
| RemoveContactIDList | List[int] | ID로 접촉 제거 | [] |

---

## 5. 핵심 알고리즘 분석

### 5.1 동적 이완 설정 제거 (라인 4481-4482)

```python
if removeDynamicRelaxation is True and self.dynaImporter.controlManager.controlDynamicRelaxation is not None:
    self.dynaImporter.controlManager.controlDynamicRelaxation = None
```

**역할**: *CONTROL_DYNAMIC_RELAXATION 키워드를 모델에서 제거하여 일반 명시적 해석으로 전환

### 5.2 기준 노드 결정 (라인 4483-4512)

```python
rotation = False
rotationNodeList = []

# 자동 모드: 바운딩박스 코너 노드 사용
if moveToOriginAutomatic == True or len(moveToOriginbyNode) < 3:
    xmin, ymin, zmin, xmax, ymax, zmax = self.dynaImporter.nodeManager.GetBoundingBox()
    node1 = self.dynaImporter.nodeManager.FindClosestNodefromPoint(xmin, ymin, zmin)
    node2 = self.dynaImporter.nodeManager.FindClosestNodefromPoint(xmax, ymin, zmin)
    node3 = self.dynaImporter.nodeManager.FindClosestNodefromPoint(xmin, ymax, zmin)
    rotationNodeList.append(node1)
    rotationNodeList.append(node2)
    rotationNodeList.append(node3)
    rotation = True

# 수동 모드: 지정된 노드 ID 사용
elif len(moveToOriginbyNode) == 3:
    node1 = self.dynaImporter.nodeManager.FindNodefromID(moveToOriginbyNode[0])
    node2 = self.dynaImporter.nodeManager.FindNodefromID(moveToOriginbyNode[1])
    node3 = self.dynaImporter.nodeManager.FindNodefromID(moveToOriginbyNode[2])
    # ... (null 체크 후 fallback)
    rotation = True

# 원본 좌표 저장 (변환 전)
if rotation == True:
    P = [[node1.x, node1.y, node1.z],
         [node2.x, node2.y, node2.z],
         [node3.x, node3.y, node3.z]]
```

**핵심 개념**:
- 3개의 기준 노드로 좌표계 정의
- 변환 전 좌표(P)와 변환 후 좌표(Q)를 비교하여 역변환 적용

### 5.3 dynain 파일 로드 (라인 4519-4532)

```python
# 새로운 임포터 인스턴스 생성
dynainImporter : KooDynaImporter = KooDynaImporter()
self.dynaSubImporter[dynainpath] = dynainImporter

# dynain 파일 파싱
dynainImporter.importDynaFile(dynainpath)
dynainImporter.importKeywordstoManager()

# 응력 데이터 처리
if includeStress is False:
    dynainImporter.initialManager.ClearInitial()  # dynain의 응력 제거
else:
    self.dynaImporter.initialManager.ClearInitial()  # 기존 모델의 응력 제거

# 현재 모델에 덮어쓰기
self.dynaImporter.OverwritefromManager(dynainImporter)
```

**중요**:
- dynain 파일은 별도의 임포터로 로드
- `OverwritefromManager()`가 노드 좌표와 초기 조건을 덮어씀

### 5.4 좌표계 복원 (라인 4534-4540)

```python
if rotation == True:
    # 변환 후 노드 좌표 획득
    movedNode1 = self.dynaImporter.nodeManager.FindNodefromID(node1.id)
    movedNode2 = self.dynaImporter.nodeManager.FindNodefromID(node2.id)
    movedNode3 = self.dynaImporter.nodeManager.FindNodefromID(node3.id)
    Q = [[movedNode1.x, movedNode1.y, movedNode1.z],
         [movedNode2.x, movedNode2.y, movedNode2.z],
         [movedNode3.x, movedNode3.y, movedNode3.z]]

    # 3점 기반 역변환 적용
    self.dynaImporter.nodeManager.ApplyTransformfromThreePoints(P, Q, None, True)
```

**알고리즘**:
```
원본 좌표계 (P)          동적이완 후 (Q)         복원 후
   P1 ────────►             Q1 ────────►         P1
   │                        │                    │
   P2                       Q2                   P2
   │                        │                    │
   P3                       Q3                   P3

역변환 T를 계산: Q → P
모든 노드에 T 적용
```

### 5.5 새 동적 이완 설정 (선택) (라인 4542-4545)

```python
if dynamicRelaxation == True:
    self.dynaImporter.controlManager.clear()
    self.dynaImporter.databaseManager.clear()
    self.dynaImporter.controlManager.SetControlDynamicRelaxation(
        250,        # NRCYCK: 수렴 체크 주기
        0.00001,    # DRTERM: 수렴 기준
        0.35,       # TSSFDR: 동적 이완 시간 스케일
        1.0e+99,    # IRELAL: 이완 플래그
        0.3,        # EDTTL: 에너지 감소 허용치
        0,          # IDRFLG: 동적 이완 플래그
        0.0001,     # DRFCTR: 댐핑 팩터
        -1          # DRTERM2: 두번째 수렴 기준
    )
```

### 5.6 파트 및 접촉 제거 (라인 4547-4556)

```python
# 이름으로 파트 제거
if len(removePartNameList) > 0:
    for name in removePartNameList:
        self.dynaImporter.RemovePartbyName(name, True)

# ID로 파트 제거
if len(removePartIDList) > 0:
    for pid in removePartIDList:
        self.dynaImporter.RemovePart(pid, True)

# ID로 접촉 제거
if len(removeContactIDList) > 0:
    for cid in removeContactIDList:
        self.dynaImporter.contactManager.RemoveContactbyID(cid)
```

---

## 6. dynain 파일 구조

### 6.1 dynain 파일 내용

LS-DYNA가 생성하는 dynain 파일에는 다음이 포함됩니다:

```
*KEYWORD
*NODE
$   NID        X               Y               Z
      1  1.234567e+00   2.345678e+00   3.456789e+00
      2  ...
$
*INITIAL_STRESS_SOLID
$    EID    NHISV   NINTGR   NTHINT    NHISVI
      1        0        8        0        0
$    SIGXX       SIGYY       SIGZZ       SIGXY       SIGYZ       SIGXZ
 1.234e+02   2.345e+02   3.456e+02   4.567e+01   5.678e+01   6.789e+01
$
*INITIAL_STRESS_SHELL
...
*END
```

### 6.2 로드되는 데이터

| 데이터 타입 | 키워드 | 설명 |
|------------|--------|------|
| 노드 좌표 | *NODE | 변형된 노드 위치 |
| 솔리드 응력 | *INITIAL_STRESS_SOLID | 3D 요소 초기 응력 |
| 쉘 응력 | *INITIAL_STRESS_SHELL | 쉘 요소 초기 응력 |
| 빔 응력 | *INITIAL_STRESS_BEAM | 빔 요소 초기 응력 |

---

## 7. 사용 예시

### 7.1 기본 사용 (자동 원점 복귀)

```
*Inputfile
DropSet.k
*Mode
DYNAIN_TO_INITIAL,1
**DynainToInitial,1
*DynainPath,Output/dynain
*IncludeStress,True
*RemoveDynamicRelaxation,True
*MovetoOriginAutomatic,True
*RemovePartbyID,1000
*RemoveContactbyID,500
**EndDynainToInitial
*End
```

### 7.2 수동 노드 지정

```
**DynainToInitial,1
*DynainPath,../simulation1/dynain
*IncludeStress,True
*RemoveDynamicRelaxation,True
*MovetoOriginByNode,1,2,3
**EndDynainToInitial
```

### 7.3 이름으로 파트 제거

```
**DynainToInitial,1
*DynainPath,dynain
*IncludeStress,True
*RemovePartByName,RigidWall,ImpactPlate
**EndDynainToInitial
```

### 7.4 연속 동적 이완

```
**DynainToInitial,1
*DynainPath,dynain
*IncludeStress,True
*DynamicRelaxation,True
**EndDynainToInitial
```

---

## 8. DROP_ATTITUDE와의 연동

### 8.1 자동 생성된 dynaintoinitial.txt 분석

DROP_ATTITUDE 모드가 생성하는 파일:

```
*Inputfile
DropSet.k                           # 원본 낙하 모델
*Mode
DYNAIN_TO_INITIAL,1
**DynainPath,/path/to/Output/dynain # 동적 이완 결과 경로
*IncludeStress,True                 # 응력 포함
*RemoveDynamicRelaxation,True       # DR 설정 제거
*MovetoOriginAutomatic,True         # 자동 원점 복귀
*RemovePartbyID,<바닥파트ID>         # 임시 바닥 제거
*RemoveContactbyID,<접촉ID>          # 임시 접촉 제거
**EndDynainToInitial
*End
```

### 8.2 전체 워크플로우 다이어그램

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    낙하 시험 전체 워크플로우                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  STEP 1: DROP_ATTITUDE                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ Input: model.k (초기 모델)                                           │ │
│  │ Output: DropSet.k (바닥 + 접촉 + 동적이완 설정)                       │ │
│  │         dynaintoinitial.txt (다음 단계 설정)                         │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    │                                      │
│                                    ▼                                      │
│  STEP 2: LS-DYNA 실행 (동적 이완)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ Input: DropSet.k                                                     │ │
│  │ 실행: 감쇠 진동으로 정적 평형 도달                                    │ │
│  │ Output: Output/dynain (변형 노드 + 응력)                             │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    │                                      │
│                                    ▼                                      │
│  STEP 3: DYNAIN_TO_INITIAL                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ Input: DropSet.k + Output/dynain                                     │ │
│  │ 처리:                                                                │ │
│  │   1. dynain 로드 (노드 위치 + 응력)                                  │ │
│  │   2. 바닥 파트 제거                                                  │ │
│  │   3. 접촉 정의 제거                                                  │ │
│  │   4. 좌표계 원점 복귀                                                │ │
│  │   5. 동적이완 설정 제거                                              │ │
│  │ Output: DropSet_dti.k (초기응력 포함 모델)                           │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    │                                      │
│                                    ▼                                      │
│  STEP 4: 실제 충격 시뮬레이션                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ Input: DropSet_dti.k (초기응력 있음)                                 │ │
│  │ 실행: 정확한 충격 해석 (자중에 의한 내부 응력 포함)                    │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 9. 주의사항 및 제한사항

### 9.1 노드 ID 일치

dynain 파일의 노드 ID가 원본 모델과 일치해야 합니다.

```
원본 모델 노드:  1, 2, 3, 4, 5, ...
dynain 노드:     1, 2, 3, 4, 5, ...  ← 반드시 일치
```

### 9.2 응력 데이터 호환성

- 솔리드 요소: *INITIAL_STRESS_SOLID
- 쉘 요소: *INITIAL_STRESS_SHELL
- 요소 타입이 변경되면 응력 데이터 적용 불가

### 9.3 좌표 변환 정확도

3점 기반 변환은 다음 경우에 부정확할 수 있습니다:
- 큰 변형이 발생한 경우
- 기준 노드가 특이점에 있는 경우
- 회전과 병진이 복합된 경우

### 9.4 메모리 사용

```python
# 새 임포터가 생성됨 - 메모리 사용 증가
dynainImporter : KooDynaImporter = KooDynaImporter()
self.dynaSubImporter[dynainpath] = dynainImporter  # 캐싱됨
```

---

## 10. 디버깅 팁

### 10.1 원점 복귀 확인

```python
# 변환 전후 좌표 출력
print("Original P:", P)
print("After dynain Q:", Q)
```

### 10.2 응력 데이터 확인

```python
# 응력 데이터 개수 확인
print("Initial stress count:", len(self.dynaImporter.initialManager.initialList))
```

### 10.3 제거된 파트 확인

```python
# 파트 목록 출력
for pid in self.dynaImporter.partManager.parts:
    print(f"Part {pid}: {self.dynaImporter.partManager.parts[pid].name}")
```
