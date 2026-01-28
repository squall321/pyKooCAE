# DROP_ATTITUDE 모드 상세 분석

## 1. 개요

**목적**: 다양한 낙하 자세(오일러 각도)와 조건으로 LS-DYNA 낙하 시험 모델을 자동 생성

**파일 위치**:
- 파서: `KooMeshModifier.py` (라인 190-262, 1731-1768)
- 실행: `KooDynaAdvancedModification.py` (라인 1910-2244)

**출력 접미사**: `_drop`

---

## 2. 함수 호출 흐름

```
KooMeshModifier.ImportOption()
    │
    ├── *DropAttitude 블록 파싱
    │       └── modeIDOption[modeid] 에 옵션 저장
    │
    └── GenerateDropAttitude(modeid)
            │
            └── advancedModification.DropAttitude(option, filePath)
                    │
                    ├── 1. 제어/데이터베이스 설정
                    ├── 2. 전체 노드를 노드셋으로 생성
                    ├── 3. 고정 경계조건 노드셋 생성
                    ├── 4. 강체벽 섹션/재료 생성
                    ├── 5. 바운딩박스 계산 및 모델 중심 이동
                    ├── 6. 동적 이완용 파트셋 생성
                    │
                    └── 7. 각 낙하 조건별 반복:
                            ├── 오일러 각도로 회전행렬 계산
                            ├── 속도/각속도 벡터 회전
                            ├── 낙하 높이로부터 속도 계산
                            ├── 충격점 계산 (가장 낮은 노드)
                            ├── 초기 속도 조건 생성
                            ├── 낙하면(바닥) 파트 생성
                            ├── 접촉 조건 생성
                            ├── 메타데이터 업데이트
                            └── 파일 출력
```

---

## 3. 설정 파일 옵션 상세

### 3.1 파서 구조 (KooMeshModifier.py)

```python
# 라인 1731-1768
def ParseDropAttitude(self, optionid, curOption, curKeyword):
    if "runid" in optionid.lower():
        curOption["runid"] = curKeyword
    elif "eulerrolling" in optionid.lower():
        curOption["EulerRolling"] = curKeyword    # X축 회전 (Roll)
    elif "eulerpitching" in optionid.lower():
        curOption["EulerPitching"] = curKeyword   # Y축 회전 (Pitch)
    elif "euleryawing" in optionid.lower():
        curOption["EulerYawing"] = curKeyword     # Z축 회전 (Yaw)
    elif "height" in optionid.lower():
        curOption["Height"] = curKeyword          # 낙하 높이
    elif "initialvelocityx" in optionid.lower():
        curOption["InitialVelocityX"] = curKeyword
    elif "initialvelocityy" in optionid.lower():
        curOption["InitialVelocityY"] = curKeyword
    elif "initialvelocityz" in optionid.lower():
        curOption["InitialVelocityZ"] = curKeyword
    elif "initialangularvelocityx" in optionid.lower():
        curOption["InitialAngularVelocityX"] = curKeyword
    elif "initialangularvelocityy" in optionid.lower():
        curOption["InitialAngularVelocityY"] = curKeyword
    elif "initialangularvelocityz" in optionid.lower():
        curOption["InitialAngularVelocityZ"] = curKeyword
    elif "offsetdistance" in optionid.lower():
        curOption["OffsetDistance"] = curKeyword[0]
    elif "density" in optionid.lower():
        curOption["Density"] = curKeyword[0]      # 바닥 밀도
    elif "youngsmodulus" in optionid.lower():
        curOption["YoungsModulus"] = curKeyword[0]
    elif "poissonratio" in optionid.lower():
        curOption["PoissonRatio"] = curKeyword[0]
    elif "tfinal" in optionid.lower():
        curOption["TFinal"] = curKeyword[0]       # 종료 시간
    elif "dt" in optionid.lower():
        curOption["DT"] = curKeyword[0]           # 출력 시간 간격
    elif "dropsurface" in optionid.lower():
        curOption["DropSurface"] = curKeyword     # 낙하면 설정
```

### 3.2 전체 옵션 목록

| 옵션명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| RunID | List[str] | 실행 ID 목록 | 자동 생성 |
| EulerRolling | List[float] | X축 회전 각도 (도) | [0] |
| EulerPitching | List[float] | Y축 회전 각도 (도) | [0] |
| EulerYawing | List[float] | Z축 회전 각도 (도) | [0] |
| Height | List[float] | 낙하 높이 | [1.0] |
| InitialVelocityX | List[float] | X방향 초기 속도 | [0.0] |
| InitialVelocityY | List[float] | Y방향 초기 속도 | [0.0] |
| InitialVelocityZ | List[float] | Z방향 초기 속도 | [0.0] |
| InitialAngularVelocityX | List[float] | X축 초기 각속도 | [0.0] |
| InitialAngularVelocityY | List[float] | Y축 초기 각속도 | [0.0] |
| InitialAngularVelocityZ | List[float] | Z축 초기 각속도 | [0.0] |
| OffsetDistance | float | 충격점 오프셋 거리 | 0.0 |
| Density | float | 바닥 재료 밀도 | - |
| YoungsModulus | float | 바닥 재료 영률 | - |
| PoissonRatio | float | 바닥 재료 포아송비 | - |
| TFinal | float | 시뮬레이션 종료 시간 | 0.0 |
| DT | float | 데이터 출력 시간 간격 | 0.0 |
| DropSurface | List | 낙하면 설정 | - |

### 3.3 DropSurface 옵션 형식

**평면 (Plane)**:
```
DropSurface,Plane,<X길이>,<Y길이>,<Z길이>,<numX>,<numY>,<numZ>
```

**거칠기 있는 평면 (PlanewithRoughness)**:
```
DropSurface,PlanewithRoughness,<X길이>,<Y길이>,<Z길이>,<numX>,<numY>,<numZ>,<모드>,<RMax>,<형상계수1>,<형상계수2>
```

**거칠기 모드**:
- `XYRandom`: XY 랜덤 거칠기
- `XRandom`: X방향 랜덤
- `YRandom`: Y방향 랜덤
- `XSin`: X방향 사인파
- `YSin`: Y방향 사인파
- `XYSin`: XY 사인파

---

## 4. 핵심 알고리즘 분석

### 4.1 오일러 각도 회전 변환 (라인 2059-2094)

```python
# 역회전 적용 (평면 법선을 회전시키기 위함)
Rx = -RxOrigin * 3.141592653589793 / 180.0
Ry = -RyOrigin * 3.141592653589793 / 180.0
Rz = -RzOrigin * 3.141592653589793 / 180.0

# 회전 행렬 생성 (Rz * Ry * Rx 순서)
RotMatx = np.array([[1, 0, 0],
                    [0, math.cos(Rx), -math.sin(Rx)],
                    [0, math.sin(Rx), math.cos(Rx)]])
RotMaty = np.array([[math.cos(Ry), 0, math.sin(Ry)],
                    [0, 1, 0],
                    [-math.sin(Ry), 0, math.cos(Ry)]])
RotMatz = np.array([[math.cos(Rz), -math.sin(Rz), 0],
                    [math.sin(Rz), math.cos(Rz), 0],
                    [0, 0, 1]])
RotMat = np.dot(RotMatz, np.dot(RotMaty, RotMatx))

# 방향 벡터 회전
x_direction = np.dot(RotMat, [1.0, 0.0, 0.0])
y_direction = np.dot(RotMat, [0.0, 1.0, 0.0])
z_direction = np.dot(RotMat, [0.0, 0.0, 1.0])
```

**핵심 개념**:
- 오일러 각도를 역으로 적용하여 바닥면의 법선 벡터를 계산
- 이렇게 하면 모델을 회전시키지 않고 바닥면을 회전시키는 효과

### 4.2 낙하 높이로부터 속도 계산 (라인 2085-2092)

```python
# 높이가 100 초과면 mm 단위로 가정, 아니면 m 단위
if height > 100:
    velocity_from_height = [0.0, 0.0, -np.sqrt(2.0 * 9810.0 * height)]
else:
    velocity_from_height = [0.0, 0.0, -np.sqrt(2.0 * 9.81 * height)]

# 회전된 속도 합산
velocity_from_height = np.dot(RotMat, velocity_from_height)
velocity = velocity + velocity_from_height
```

**공식**: v = sqrt(2 * g * h)
- 자유낙하 속도 공식 적용
- 단위 자동 감지: height > 100이면 mm 단위 (g=9810), 아니면 m 단위 (g=9.81)

### 4.3 충격점 계산 (라인 2098-2106)

```python
# z_direction 방향으로 가장 먼 노드 찾기 (충격점)
minNode, maxNode = self.dynaImporter.nodeManager.FindFarthestNodes(z_direction)
impactPoint = [minNode.x, minNode.y, minNode.z]

# 법선 방향 반전 및 오프셋 적용
z_direction = -z_direction
impactPoint = [
    impactPoint[0] + z_direction[0] * offset_distance,
    impactPoint[1] + z_direction[1] * offset_distance,
    impactPoint[2] + z_direction[2] * offset_distance
]
```

### 4.4 낙하면 생성 (라인 2111-2117)

```python
if dropSurface[0] == "Plane":
    # 평평한 바닥면 생성
    nsFixed = part.elementManager.CreateImpactBox(
        impactPoint, z_direction, x_direction,
        xLength, yLength, zLength,
        numX, numY, numZ
    )
    nodeSetFixed.AddNodesfromDict(nsFixed)

elif dropSurface[0] == "PlanewithRoughness":
    # 거칠기가 있는 바닥면 생성
    nsFixed = part.elementManager.CreateImpactBoxwithRoughness(
        impactPoint, z_direction, x_direction,
        xLength, yLength, zLength,
        numX, numY, numZ,
        roughnessMode, RMax, ShapeFactor, ShapeFactor2
    )
```

---

## 5. 생성되는 LS-DYNA 키워드

### 5.1 자동 생성 키워드 목록

| 키워드 | 설명 |
|--------|------|
| *SET_NODE | 전체 노드 세트 (AllNodes) |
| *SET_NODE | 고정 노드 세트 (BottomFix) |
| *BOUNDARY_SPC_NODE | 바닥 고정 경계조건 |
| *SECTION_SOLID | 강체벽 섹션 |
| *MAT_ELASTIC | 강체벽 재료 |
| *PART | 바닥면 파트 |
| *ELEMENT_SOLID | 바닥면 요소들 |
| *NODE | 바닥면 노드들 |
| *INITIAL_VELOCITY | 초기 속도 조건 |
| *CONTACT_AUTOMATIC_SURFACE_TO_SURFACE | 접촉 정의 |
| *SET_PART | 동적 이완용 파트 세트 |
| *INTERFACE_SPRINGBACK_LSDYNA | 스프링백 인터페이스 |
| *DATABASE_BINARY_D3PLOT | 출력 설정 |
| *CONTROL_TERMINATION | 종료 제어 |

### 5.2 접촉 설정 (라인 2119-2144)

```python
surfacetosurfaceContact = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(
    SSID=0,         # 슬레이브: 전체 (타입 5)
    MSID=part.id,   # 마스터: 바닥 파트
    SSTYP=5,        # 슬레이브 타입: 파트 ID 없음 = 전체
    MSTYP=3,        # 마스터 타입: 파트 ID
    VDC=5.0,        # 점성 댐핑 계수
    ...
)
surfacetosurfaceContact.SetOptCardA(2)  # 소프트 제약 접촉
```

---

## 6. 출력 구조

### 6.1 RunDirectoryMode = True 인 경우

```
<runDirectoryPath>/
├── Run_<timestamp>_<hash>/
│   ├── DropSet.k                    # LS-DYNA 입력 파일
│   ├── DropSet.json                 # 메타데이터
│   ├── Output/                      # 결과 출력 폴더
│   │   └── dynain                   # 동적 이완 후 결과
│   └── DynamicRelaxation/
│       └── dynaintoinitial.txt      # 다음 단계 설정 파일
└── outputPathList.txt               # 모든 출력 경로 목록
```

### 6.2 자동 생성되는 dynaintoinitial.txt (라인 2193-2211)

```
*Inputfile
DropSet.k
*Mode
DYNAIN_TO_INITIAL,1
**DynainPath,<dynainPath>
*IncludeStress,True
*RemoveDynamicRelaxation,True
*MovetoOriginAutomatic,True
*RemovePartbyID,<바닥파트ID>
*RemoveContactbyID,<접촉ID>
**EndDynainToInitial
*End
```

**중요**: 이 파일은 동적 이완 완료 후 DYNAIN_TO_INITIAL 모드를 실행하여 초기 상태로 변환하는데 사용됨

### 6.3 RunDirectoryMode = False 인 경우

파일명 패턴:
```
<inputfile>_<번호>_DA_EX_<roll>_EY_<pitch>_EZ_<yaw>_H_<height>_VX_<vx>_VY_<vy>_VZ_<vz>_WX_<wx>_WY_<wy>_WZ_<wz>.k
```

---

## 7. 메타데이터 업데이트 (라인 2145-2155)

```python
self.dynaImporter.metaData["scenario_mode"] = "DropAttitude"
self.dynaImporter.metaData["initial_conditions"]["orientation_euler_deg"]["pitch"] = RyOrigin
self.dynaImporter.metaData["initial_conditions"]["orientation_euler_deg"]["roll"] = RxOrigin
self.dynaImporter.metaData["initial_conditions"]["orientation_euler_deg"]["yaw"] = RzOrigin
self.dynaImporter.metaData["initial_conditions"]["velocity"][0] = pure_velocity[0]
self.dynaImporter.metaData["initial_conditions"]["velocity"][1] = pure_velocity[1]
self.dynaImporter.metaData["initial_conditions"]["velocity"][2] = pure_velocity[2]
self.dynaImporter.metaData["initial_conditions"]["angular_velocity"][0] = angular_velocity[0]
self.dynaImporter.metaData["initial_conditions"]["angular_velocity"][1] = angular_velocity[1]
self.dynaImporter.metaData["initial_conditions"]["angular_velocity"][2] = angular_velocity[2]
self.dynaImporter.metaData["initial_conditions"]["drop_height"] = height
```

---

## 8. 사용 예시

### 8.1 단일 낙하 조건

```
*Inputfile
model.k
*Mode
DROP_ATTITUDE,1
*DropAttitude,1
EulerRolling,30.0
EulerPitching,0.0
EulerYawing,0.0
Height,1.5
InitialVelocityX,0.0
InitialVelocityY,0.0
InitialVelocityZ,0.0
Density,7.8e-9
YoungsModulus,2.0e5
PoissonRatio,0.3
TFinal,0.002
DT,1.0e-7
DropSurface,Plane,100,100,10,20,20,2
**EndDropAttitude
*End
```

### 8.2 다중 낙하 조건 (DOE)

```
*DropAttitude,1
EulerRolling,0,15,30,45
EulerPitching,0,0,0,0
EulerYawing,0,0,0,0
Height,1.5,1.5,1.5,1.5
...
```

### 8.3 거칠기 있는 바닥면

```
DropSurface,PlanewithRoughness,100,100,10,40,40,2,XYRandom,0.5,1.0,1.0
```

---

## 9. 관련 모드와의 연계

### DROP_ATTITUDE → DYNAIN_TO_INITIAL 워크플로우

```
1. DROP_ATTITUDE 실행
   └── 동적 이완 시뮬레이션용 .k 파일 생성

2. LS-DYNA 실행 (동적 이완)
   └── Output/dynain 파일 생성

3. DYNAIN_TO_INITIAL 실행
   └── dynain 결과를 초기 조건으로 변환
   └── 바닥/접촉 제거
   └── 원점 복귀

4. 최종 모델
   └── 초기 응력이 적용된 상태로 다음 시뮬레이션 준비 완료
```

---

## 10. 주의사항 및 제한사항

1. **단위 일관성**: height > 100 이면 자동으로 mm 단위로 간주
2. **리스트 길이**: EulerRolling, EulerPitching, EulerYawing, Height, Velocity 등의 리스트 길이가 모두 동일해야 함
3. **바운딩박스**: 모델이 원점 중심으로 자동 이동됨
4. **동적 이완**: *INTERFACE_SPRINGBACK_LSDYNA가 자동 생성되어 동적 이완 시뮬레이션 지원
5. **메모리 관리**: 다중 케이스 생성 시 이전 바닥/접촉이 자동으로 제거됨 (라인 2031-2040)
