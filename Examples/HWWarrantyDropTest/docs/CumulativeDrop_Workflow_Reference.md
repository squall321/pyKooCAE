# Cumulative Drop Workflow Reference

## Overview

누적낙하(Cumulative Drop) 시뮬레이션을 위한 KooMeshModifier 모드 및 워크플로우 참조 문서입니다.

---

## 1. 핵심 워크플로우

```
┌─────────────────────────────────────────────────────────────┐
│  1. DROP_ATTITUDE        →  첫 번째 낙하 시뮬레이션          │
│     (d3plot/dynain 출력)                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2. DYNAIN_TO_INITIAL    →  dynain을 초기조건으로 변환       │
│     (변위/응력 상태 유지, 낙하면 제거, 좌표 정렬)             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3. DROP_ATTITUDE        →  두 번째 낙하 (손상 누적 상태)    │
│     ...반복...                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 관련 모드 상세

### 2.1 DROP_ATTITUDE (낙하 자세 시험)

| 항목 | 내용 |
|------|------|
| **모드 ID** | 9 |
| **출력 접미사** | `_drop` |
| **목적** | 다양한 오일러 각도로 낙하 시뮬레이션 생성 |

**주요 파라미터:**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| EulerRolling | [float] | Roll 각도 목록 (°) |
| EulerPitching | [float] | Pitch 각도 목록 (°) |
| EulerYawing | [float] | Yaw 각도 목록 (°) |
| Height | [float] | 낙하 높이 (mm) |
| InitialVelocityX/Y/Z | [float] | 초기 속도 |
| InitialAngularVelocityX/Y/Z | [float] | 초기 각속도 |
| OffsetDistance | float | 낙하면 오프셋 거리 |
| Density | float | 낙하면 밀도 |
| YoungsModulus | float | 낙하면 영률 |
| PoissonRatio | float | 낙하면 포아송비 |
| TFinal | float | 시뮬레이션 종료 시간 |
| DT | float | 시간 간격 |
| DropSurface | tuple | 낙하면 정의 |

**DropSurface 형식:**
```
DropSurface,Plane,<Width>,<Length>,<Thickness>,<MeshX>,<MeshY>,<MeshZ>
```

**출력:**
- 각 케이스별 시뮬레이션 파일
- INTERFACE_SPRINGBACK_LSDYNA (dynain 출력용)
- d3plot 결과

---

### 2.2 DYNAIN_TO_INITIAL (Dynain → 초기조건 변환)

| 항목 | 내용 |
|------|------|
| **모드 ID** | 18 |
| **출력 접미사** | `_dti` |
| **목적** | 이전 시뮬레이션 결과를 다음 시뮬레이션의 초기조건으로 변환 |

**주요 파라미터:**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| DynainPath | string | "dynain" | Dynain 파일 경로 |
| IncludeStress | bool | true | 응력 포함 여부 |
| RemoveDynamicRelaxation | bool | true | DR 제어 제거 |
| DynamicRelaxation | bool | false | 새 DR 적용 여부 |
| MovetoOriginAutomatic | bool | false | 자동 원점 이동 |
| MovetoOriginbyNode | [int] | - | 3개 노드로 좌표 정렬 |
| RemovePartByName | [string] | - | 제거할 파트 이름 |
| RemovePartByID | [int] | - | 제거할 파트 ID |
| RemoveContactByID | [int] | - | 제거할 접촉 ID |

**핵심 기능:**
- 변위/응력 상태 유지
- 낙하면/임팩터 제거
- 좌표 재정렬 (3점 변환)

**사용 예시:**
```
**DynainToInitial,1
DynainPath,dynain
IncludeStress,true
RemoveDynamicRelaxation,true
MovetoOriginAutomatic,true
RemovePartByID,500,501
**EndDynainToInitial
```

---

### 2.3 WARPED_TO_INITIAL_STRESS_PART (휨 → 초기응력 변환)

| 항목 | 내용 |
|------|------|
| **모드 ID** | 15 |
| **출력 접미사** | `_w2is` |
| **목적** | 휨/변형 데이터를 초기 응력으로 변환 |

**주요 파라미터:**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| UnitScale | string | 단위 스케일 (mm, Microm 등) |
| AmplitudeTop | float | 상단 휨 진폭 |
| AmplitudeBottom | float | 하단 휨 진폭 |
| Location | [float] | 휨 위치 (X, Y, Z) |
| XLength | float | X 방향 길이 |
| YLength | float | Y 방향 길이 |
| Direction | [float] | 휨 방향 벡터 |
| WarpageFileTop | string | 상단 휨 데이터 파일 |
| WarpageFileBottom | string | 하단 휨 데이터 파일 |
| PIDs | [int] | 대상 파트 ID 목록 |

**자동 추가:**
- CONTROL_DYNAMIC_RELAXATION
- INITIAL_STRESS_SOLID

**Dynamic Relaxation 설정:**
```python
SetControlDynamicRelaxation(
    NRCYCK=250,      # 최대 이완 사이클 수
    DRTOL=0.00001,   # 수렴 공차
    DRFCRT=0.35,     # 강제 감소 계수
    TSSFDR=0.3,      # 시간 스케일 안전 계수
    EDTTL=0.0001,    # 에너지 수렴 공차
    IDRFLG=-1        # 동적 이완 플래그
)
```

---

### 2.4 DROP_WEIGHT_IMPACT_TEST (낙하추 충격 시험)

| 항목 | 내용 |
|------|------|
| **모드 ID** | 12 |
| **출력 접미사** | `_dwit` |
| **목적** | 임팩터를 이용한 충격 시험 |

**주요 파라미터:**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| GenerationMode | string | DampingSpring, OutsideRigidPart, OutsideRigidElement |
| Type | string | Sphere, Cylinder, Box |
| Dimension | [float] | 임팩터 치수 |
| DimensionDamper | [float] | 댐퍼 너비, 높이, 오프셋 |
| LocationX | [float] | X 위치 목록 |
| LocationY | [float] | Y 위치 목록 |
| Height | [float] | 낙하 높이 목록 |
| MeshSize | float | 메시 크기 |
| YoungsModulusImpactor | float | 임팩터 영률 |
| DensityImpactor | float | 임팩터 밀도 |

---

### 2.5 TRANSFORM (기하 변환)

| 항목 | 내용 |
|------|------|
| **모드 ID** | 11 |
| **출력 접미사** | `_trans` |
| **목적** | 이동, 회전, 스케일, 미러링 |

**변환 타입:**

| 타입 | 파라미터 | 설명 |
|------|---------|------|
| Translation | X, Y, Z | 이동 거리 |
| Rotation | angleX, angleY, angleZ | 오일러 회전 (°) |
| Scale | sX, sY, sZ | 스케일링 비율 |
| Mirror | 평면 | XY, YZ, XZ |
| VectorRotation | X, Y, Z | 벡터 방향 회전 |
| VectorToVectorRotation | fromX,Y,Z, toX,Y,Z | 벡터→벡터 회전 |

---

## 3. 현재 구현 상태

| 모드 | 구현 상태 | 누적낙하 역할 |
|------|----------|--------------|
| DROP_ATTITUDE | ✅ 완료 | 낙하 시뮬레이션 생성 |
| DYNAIN_TO_INITIAL | ✅ 완료 | 결과 → 초기조건 변환 |
| WARPED_TO_INITIAL_STRESS_PART | ✅ 완료 | 휨 → 초기응력 |
| DROP_WEIGHT_IMPACT_TEST | ✅ 완료 | 충격 시험 생성 |
| TRANSFORM | ✅ 완료 | 좌표 정렬 |
| SIMULATION_AUTOMATION | ⚠️ 파싱만 완료 | 전체 워크플로우 자동화 |

---

## 4. 누적낙하 시뮬레이션 전체 흐름

```
┌─────────────────────────────────────────────────────────────┐
│   1단계: 모델 전처리 (선택)                                  │
│   - TRANSFORM: 좌표 정렬                                    │
│   - PART_MORPHING: 기하 형상 조정                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│   2단계: 첫 번째 낙하                                        │
│   - DROP_ATTITUDE: 낙하 자세 및 초기 조건 설정               │
│   - LS-DYNA 실행 → d3plot, dynain 출력                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│   3단계: 결과 → 초기조건 변환                                │
│   - DYNAIN_TO_INITIAL: dynain 로드                          │
│     → 응력/변위 상태 유지                                    │
│     → 낙하면 제거                                           │
│     → 좌표 재정렬                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│   4단계: 두 번째 낙하                                        │
│   - DROP_ATTITUDE: 새로운 낙하 방향/높이                     │
│   - 손상 누적 상태에서 시작                                  │
│   - LS-DYNA 실행 → d3plot, dynain 출력                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
              ┌─ 반복 (3~4단계) ─┐
              │ (필요한 낙하 횟수만큼)
              └─────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│   최종: 누적 손상 평가                                       │
│   - 최종 d3plot 분석                                        │
│   - 누적 응력, 변형, 파손 평가                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 설정 파일 예시

### 5.1 첫 번째 낙하 설정

```
*Inputfile
model.k
*RunDirectoryMode,True,Data/Results,Data/Metadata
*Info,Smartphone,CumulativeDrop_Step1
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,0
EulerPitching,0
EulerYawing,0
Height,1500
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
OffsetDistance,0.1
Density,7850
YoungsModulus,200000000000
PoissonRatio,0.3
tFinal,0.005
dt,0.000001
DropSurface,Plane,300,300,20,30,30,2
**EndDropAttitude
*End
```

### 5.2 Dynain → 초기조건 변환

```
*Inputfile
model_drop.k
*RunDirectoryMode,True,Data/Results,Data/Metadata
*Info,Smartphone,CumulativeDrop_Step2_Convert
*Mode
DYNAIN_TO_INITIAL,1
**DynainToInitial,1
DynainPath,../Step1/dynain
IncludeStress,true
RemoveDynamicRelaxation,true
MovetoOriginAutomatic,true
RemovePartByID,9999
**EndDynainToInitial
*End
```

### 5.3 두 번째 낙하 설정

```
*Inputfile
model_drop_dti.k
*RunDirectoryMode,True,Data/Results,Data/Metadata
*Info,Smartphone,CumulativeDrop_Step3
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,180
EulerPitching,0
EulerYawing,0
Height,1500
...
**EndDropAttitude
*End
```

---

## 6. 주의사항

1. **Dynain 파일 경로**: 이전 시뮬레이션의 결과 디렉토리를 정확히 지정
2. **파트 ID 관리**: 낙하면/임팩터 파트 ID를 RemovePartByID로 제거
3. **좌표 정렬**: MovetoOriginAutomatic 또는 MovetoOriginbyNode로 좌표계 재정렬
4. **응력 포함**: IncludeStress=true로 누적 손상 반영
5. **Dynamic Relaxation 제거**: RemoveDynamicRelaxation=true로 이전 DR 설정 제거

---

---

## 7. RunDirectoryMode 자동 연계 시스템

### 7.1 설정 방법

```
*RunDirectoryMode,True,Data/Results,Data/Metadata
```

| 파라미터 | 설명 |
|---------|------|
| 1번째 | True/False - 활성화 여부 |
| 2번째 | runDirectoryPath - 결과 저장 경로 |
| 3번째 | metaDirectoryPath - 메타데이터 경로 |

### 7.2 자동 생성되는 폴더 구조

```
Data/Results/
└── Run_{YYYYMMDD_HHMMSS}_{hash}/
    ├── DropSet.k                    # 낙하 시뮬레이션 입력 파일
    ├── DropSet.json                 # 메타데이터 (JSON)
    ├── Output/
    │   └── dynain                   # LS-DYNA 실행 후 생성
    └── DynamicRelaxation/
        ├── DropSet.k                # 복사본
        └── dynaintoinitial.txt      # 다음 단계 연계 설정 파일 (자동 생성!)
```

### 7.3 자동 생성되는 dynaintoinitial.txt

DROP_ATTITUDE 실행 시 **자동으로** 다음 단계를 위한 DYNAIN_TO_INITIAL 설정 파일 생성:

```
*Inputfile
DropSet.k
*Mode
DYNAIN_TO_INITIAL,1
**DynainPath,{Output/dynain 경로}
*IncludeStress,True
*RemoveDynamicRelaxation,True
*MovetoOriginAutomatic,True
*RemovePartbyID,{낙하면 파트 ID}
*RemoveContactbyID,{접촉 ID}
**EndDynainToInitial
*End
```

### 7.4 MetaData 시스템

각 시뮬레이션의 메타데이터가 JSON으로 저장됨:

```json
{
    "model_name": "Smartphone",
    "stage": "DV1",
    "description": "6-Face Drop Test",
    "created_by": {
        "name": "koo.park",
        "email": "koo.park@samsung.com",
        "group": "CAE",
        "team": "Samsung"
    },
    "initial_conditions": {
        "euler_angles": [0, 0, 0],
        "velocity": [0, 0, 0],
        "angular_velocity": [0, 0, 0],
        "drop_height": 1500
    }
}
```

### 7.5 자동 연계 워크플로우

```
┌─────────────────────────────────────────────────────────────┐
│  1. DROP_ATTITUDE (RunDirectoryMode=True)                   │
│     → Run_xxx/DropSet.k 생성                                │
│     → Run_xxx/DynamicRelaxation/dynaintoinitial.txt 자동생성│
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2. LS-DYNA 실행                                            │
│     → Run_xxx/Output/dynain 생성                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3. dynaintoinitial.txt 실행 (KooMeshModifier)              │
│     → DYNAIN_TO_INITIAL 모드로 다음 단계 모델 생성           │
└─────────────────────────────────────────────────────────────┘
                              ↓
              ┌─ 반복 ─┐
```

---

## Author

- Creator: koo.park
- Email: koo.park@samsung.com
- Group: CAE
