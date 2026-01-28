# PART_EXCHANGE 모드 상세 분석

## 1. 개요

**목적**: 파트의 메시 타입 변환, 재료/섹션 교체, 복합재 레이어 적용 등 복잡한 파트 교체 작업 수행

**파일 위치**:
- 파서: `KooMeshModifier.py` (라인 296-440)
- 실행: `KooDynaAdvancedModification.py` (라인 549-1908)

**출력 접미사**: `_pex`

---

## 2. 주요 기능

### 2.1 메시 타입 변환

| 변환 | 설명 |
|------|------|
| Hexa → Shell | 육면체 요소를 쉘 요소로 |
| Hexa → TShell | 육면체 요소를 두꺼운 쉘로 |
| Hexa → Solid | 육면체 요소를 다른 솔리드로 |
| Hexa → SolidComp | 육면체 요소를 복합재 솔리드로 |
| Unstructured → Structured | 비구조 메시를 구조 메시로 |

### 2.2 지원 기능

- 재료 속성 교체
- 섹션 속성 교체
- 복합재 레이업 적용
- 레이어별 두께 지정
- EOS (상태방정식) 추가
- Hourglass 제어 추가

---

## 3. 설정 파일 구조

```
**PartExchange,<모드ID>
*PID,<파트ID>
*PIDs,<PID1>,<PID2>,...
*ConvertHexaTo,<타입>,<벡터X>,<벡터Y>,<벡터Z>,<허용각도>
*UnstructuredtoStructured,<NX>,<NY>,<NZ>
*LayerThickness
<두께1>
<두께2>
...
*THK01,<두께값>
*NUME01,<요소수>
*MID01,<재료키워드>
<재료데이터>
*EOS01,<EOS키워드>
<EOS데이터>
*HGID01,<Hourglass키워드>
<Hourglass데이터>
*Layup
<레이업정의>
*PART_COMPOSITE
<파트컴포지트정의>
*SECTION_...
<섹션정의>
**EndPartExchange
```

---

## 4. 변환 타입별 상세

### 4.1 ConvertHexaTo 옵션

```
*ConvertHexaTo,<타입>,<dirX>,<dirY>,<dirZ>,<toleranceAngle>
```

**타입 옵션**:
- `Shell`: 쉘 요소로 변환
- `TShell`: 두꺼운 쉘 요소로 변환
- `Solid`: 솔리드 요소 유지 (재료/섹션만 변경)
- `SolidComp`: 복합재 솔리드로 변환
- `SolidwithSlack`: 슬랙이 있는 솔리드 (커넥터용)
- `SolidStructuredZSlack`: Z방향 슬랙 구조 솔리드

**방향 벡터**: 쉘 변환 시 두께 방향 결정
**허용 각도**: 방향 벡터와의 각도 허용 범위 (도)

### 4.2 UnstructuredtoStructured 옵션

```
*UnstructuredtoStructured,<NX>,<NY>,<NZ>
```

비구조 메시를 NX × NY × NZ 구조 메시로 재생성

---

## 5. 핵심 알고리즘 (KooDynaAdvancedModification.py)

### 5.1 ConvertHexato 함수 (라인 987-1908)

```python
def ConvertHexato(self, option, layupList=[], curOption=None, filePath=None):
    convertType = option["Type"]  # Shell, TShell, Solid, etc.
    dirVec = [option["DirX"], option["DirY"], option["DirZ"]]
    toleranceAngle = option["ToleranceAngle"]
    pid = option["PID"]

    if convertType.lower() == "shell":
        # 1. 육면체 요소의 면 추출
        # 2. 방향 벡터와 각도 비교
        # 3. 허용 범위 내의 면을 쉘 요소로 변환
        self.ConvertHexatoShell(pid, dirVec, toleranceAngle)

    elif convertType.lower() == "tshell":
        # 두꺼운 쉘로 변환 (두께 정보 포함)
        self.ConvertHexatoTShell(pid, dirVec, toleranceAngle)

    elif convertType.lower() == "solidcomp":
        # 복합재 솔리드로 변환
        self.ConvertHexatoSolidComp(pid, layupList)
```

### 5.2 ConvertUnstructuredtoStructured 함수 (라인 549-799)

```python
def ConvertUnstructuredtoStructured(self, option):
    pids = option["PIDS"]
    layerThickness = option.get("LayerThickness", [])

    for pid in pids:
        part = self.dynaImporter.partManager.parts[pid]

        # 1. 기존 요소의 바운딩 박스 계산
        bbox = part.elementManager.GetBoundingBox()

        # 2. 새로운 구조 메시 생성
        nx, ny, nz = self.CalculateStructuredMeshCount(bbox, layerThickness)

        # 3. 노드 재생성
        newNodes = self.CreateStructuredNodes(bbox, nx, ny, nz)

        # 4. 요소 재생성
        newElements = self.CreateStructuredElements(newNodes, nx, ny, nz)

        # 5. 기존 요소 교체
        part.elementManager.ReplaceElements(newElements)
```

---

## 6. 복합재 레이업 정의

### 6.1 Layup 형식

```
*Layup
THK01,MID01,BETA1,NUME01
THK02,MID02,BETA2,NUME02
...
```

**필드**:
- THK: 두께 (변수명으로 치환 가능)
- MID: 재료 ID (변수명으로 치환 가능)
- BETA: 섬유 방향 각도
- NUME: 적분점 수

### 6.2 변수 치환

```
*THK01,0.1
*THK02,0.2
*MID01,*MAT_ELASTIC
    1  7.8e-9  2.1e5  0.3
*MID02,*MAT_ELASTIC
    2  1.2e-9  7.0e4  0.35
*Layup
THK01,MID01,0,2
THK02,MID02,45,2
THK02,MID02,-45,2
THK01,MID01,90,2
```

---

## 7. 사용 예시

### 7.1 육면체를 쉘로 변환

```
**PartExchange,1
*PID,100
*ConvertHexaTo,Shell,0.0,0.0,1.0,45.0
*MID01,*MAT_ELASTIC
    1  7.8e-9  2.1e5  0.3
*SECTION_SHELL
    1  2.0
**EndPartExchange
```

### 7.2 복합재 솔리드 적용

```
**PartExchange,1
*PID,100
*ConvertHexaTo,SolidComp,0.0,0.0,1.0,45.0
*THK01,0.1
*THK02,0.15
*MID01,*MAT_ORTHOTROPIC_ELASTIC
    1  7.8e-9  ...
*MID02,*MAT_ELASTIC
    2  1.2e-9  ...
*Layup
THK01,MID01,0,2
THK02,MID02,45,2
THK02,MID02,-45,2
THK01,MID01,90,2
*PART_COMPOSITE
<composite part definition>
**EndPartExchange
```

### 7.3 비구조→구조 메시 변환

```
**PartExchange,1
*PIDs,100,101,102
*UnstructuredtoStructured,10,10,5
*LayerThickness
0.5
0.3
0.5
**EndPartExchange
```

---

## 8. 주의사항

1. **방향 벡터 정규화**: 방향 벡터는 자동으로 정규화되지 않음
2. **요소 연결성**: 변환 시 요소 연결성 유지 확인 필요
3. **접촉 정의**: 메시 변환 후 접촉 정의 재설정 필요할 수 있음
4. **재료 ID 충돌**: 새로운 재료 생성 시 ID 충돌 주의
5. **레이업 순서**: 레이업은 지정된 순서대로 적용됨 (하부→상부)
