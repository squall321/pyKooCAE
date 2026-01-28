# ELASTIC_TO_RIGID 모드 상세 분석

## 1. 개요

**목적**: 탄성 재료로 정의된 파트들을 강체(Rigid Body)로 변환하여 계산 시간 단축

**파일 위치**:
- 파서: `KooMeshModifier.py` (라인 197-206)
- 실행: `KooMeshModifier.py` (라인 1114-1138)

**출력 접미사**: `_etor`

---

## 2. 사용 목적

### 2.1 계산 효율성

```
탄성 재료 파트             강체 파트
┌─────────────┐           ┌─────────────┐
│ 각 요소별    │           │ 단일 강체    │
│ 응력/변형률  │    ──►    │ 6 자유도    │
│ 계산 필요    │           │ (질량+관성)  │
└─────────────┘           └─────────────┘
   계산 비용: 높음             계산 비용: 낮음
```

### 2.2 적용 시나리오

- 관심 영역이 아닌 주변 구조물
- 변형이 거의 없는 지지 구조물
- 낙하 시험에서의 임시 바닥면
- 초기 시뮬레이션에서의 빠른 검증

---

## 3. 설정 파일 구조

```
*Inputfile
model.k
*Mode
ELASTIC_TO_RIGID,1
**ElastictoRigid,1
*PIDExcept,<PID1>,<PID2>,...
**EndElastictoRigid
*End
```

### 3.1 옵션 설명

| 옵션 | 타입 | 설명 |
|------|------|------|
| *PIDExcept | List[int] | 강체 변환에서 제외할 파트 ID 목록 |

---

## 4. 알고리즘 분석

### 4.1 파서 (라인 197-206)

```python
if mode == "ELASTIC_TO_RIGID":
    if "**elasticorigid" in line.lower():
        elasticToRigid = True
    elif "**endelasticorigid" in line.lower():
        elasticToRigid = False
    elif elasticToRigid:
        if "*pidexcept" in line.lower():
            exceptPIDs = [int(x) for x in line.split(",")[1:]]
            self.modeIDOption[modeid]["PIDExcept"] = exceptPIDs
```

### 4.2 실행 로직 (라인 1114-1138)

```python
def GenerateElasticToRigid(self, modeid):
    curOption = self.modeIDOption[modeid]
    exceptPIDs = curOption.get("PIDExcept", [])

    for pid in self.dynaImporter.partManager.parts:
        if pid in exceptPIDs:
            continue  # 제외 목록에 있으면 건너뛰기

        part = self.dynaImporter.partManager.parts[pid]
        material = self.dynaImporter.matManager.materials.get(part.mid)

        if material is not None:
            # 탄성 재료를 강체 재료로 변환
            if material.matType == "ELASTIC":
                rigidMat = self.dynaImporter.matManager.CreateRigidMaterial(
                    f"Rigid_{material.name}",
                    material.rho,
                    material.E,
                    material.nu
                )
                part.mid = rigidMat.id
```

---

## 5. 생성되는 LS-DYNA 키워드

### 5.1 변환 전 (탄성 재료)

```
*MAT_ELASTIC
$   MID       RO        E       PR
      1  7.8e-09  2.1e+05      0.3
```

### 5.2 변환 후 (강체 재료)

```
*MAT_RIGID
$   MID       RO        E       PR        N    COUPLE        M     ALIAS
      2  7.8e-09  2.1e+05      0.3      0.0      0.0      0.0
$   CMO      CON1      CON2
    1.0       7       7
```

---

## 6. 사용 예시

### 6.1 모든 파트를 강체로 변환

```
**ElastictoRigid,1
**EndElastictoRigid
```

### 6.2 특정 파트 제외

```
**ElastictoRigid,1
*PIDExcept,100,101,102
**EndElastictoRigid
```

파트 100, 101, 102는 탄성 재료 유지, 나머지는 강체로 변환

---

## 7. 주의사항

1. **구속 조건**: 강체 파트는 별도의 구속 조건 처리 필요
2. **접촉**: 강체-변형체 접촉 설정 확인 필요
3. **복원**: 한번 변환하면 원래 재료 정보 손실
4. **해석 타입**: 강체가 포함되면 암시적 해석 불가능할 수 있음
