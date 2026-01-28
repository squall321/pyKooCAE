# FEM_TO_IGA MODE 22 Bug Fixes

## 날짜
2026-01-24

## 발견된 버그 및 수정 사항

### 1. 옵션 파일 파싱 버그 - 빈 줄에서 break

**위치**: `KooMeshModifier.py` line 1849-1852

**문제**:
```python
line = f.readline()
line = line.replace('\n','')
if not line:  # 빈 줄에서 break!
    break
```

빈 줄(공백만 있는 줄)을 읽으면 `.replace('\n','')` 후 빈 문자열이 되고, `if not line:` 조건이 True가 되어 루프를 빠져나갑니다. 이로 인해:
- 옵션 파일의 빈 줄 이후 내용이 전혀 읽히지 않음
- `*Mode` 블록도 읽히지 않아 FEM_TO_IGA 모드가 등록되지 않음

**수정**:
```python
line = f.readline()
if not line:  # EOF만 break
    break
line = line.replace('\n','')
line = line.strip()
if not line:  # 빈 줄은 skip
    continue
```

EOF(파일 끝)일 때만 break하고, 빈 줄은 continue로 건너뛰도록 수정.

**영향**:
- 이 버그로 인해 FEM_TO_IGA 모드뿐만 아니라, 옵션 파일에서 빈 줄 이후에 정의된 다른 모든 설정도 무시되었을 가능성 있음
- 기존 다른 모드들도 영향을 받았을 수 있음

---

### 2. FEMtoIGA 내부 파싱 버그 - 빈 줄에서 break

**위치**: `KooMeshModifier.py` line 1804-1810 (수정 전)

**문제**:
```python
while True:
    line = f.readline().strip()
    line = line.replace('\n','')
    if not line:  # 빈 줄에서 break!
        break
```

`**FEMtoIGA` 블록 내부에서도 동일한 버그 발생:
- 주석 라인(`#`) 다음에 빈 줄이 오면 즉시 break
- 실제 `*IGA` 설정 라인을 읽기 전에 루프 종료
- "0 parts configured" 경고와 함께 아무것도 처리되지 않음

**수정**:
```python
while True:
    line = f.readline()
    if not line:  # EOF만 break
        break
    line = line.strip()
    line = line.replace('\n','')
    if not line:  # 빈 줄은 skip
        continue
```

**영향**:
- FEMtoIGA 옵션 파일의 주석과 빈 줄 처리가 불가능했음
- 실제 IGA 파트 설정이 하나도 파싱되지 않았음

---

### 3. 노드 속성 접근 버그 - nids vs nodes

**위치**: `KooIGAPart.py` line 160

**문제**:
```python
for nid in elem.nids:  # AttributeError!
```

`SolidElement` 클래스는 `.nids` 속성이 없고 `.nodes` 속성만 존재합니다.

**수정**:
```python
for node in elem.nodes:
```

**영향**:
- IGA Part 생성 시 bounding box 계산 단계에서 즉시 실패
- `AttributeError: 'SolidElement' object has no attribute 'nids'` 에러 발생

---

### 4. 노드 좌표 접근 버그 - xyz 속성 없음

**위치**: `KooIGAPart.py` line 161

**문제**:
```python
node = self.source_part.nodeManager.nodes[nid]  # KeyError!
all_coords.append(node.xyz)  # AttributeError!
```

두 가지 문제:
1. `elem.nodes`는 Node 객체 리스트이지 node ID 리스트가 아님
2. Node 객체에 `.xyz` 속성이 없음 (`.x`, `.y`, `.z` 속성만 존재)

**수정**:
```python
for node in elem.nodes:
    all_coords.append([node.x, node.y, node.z])
```

**영향**:
- 노드 좌표를 읽을 수 없어 bounding box 계산 불가
- `KeyError` 또는 `AttributeError` 발생

---

## 테스트 결과

### 수정 전
```
Warning: No IGA parts specified in FEMtoIGA mode
```
- 아무것도 생성되지 않음

### 수정 후
```
✓ IGA Part 101 created from FEM Part 1 → iga_part_01_front_metal.k
✓ IGA Part 102 created from FEM Part 2 → iga_part_02_front_wall.k
✓ IGA Part 103 created from FEM Part 3 → iga_part_03_pcb.k
✓ IGA Part 104 created from FEM Part 4 → iga_part_04_pkg1.k
✓ IGA Part 105 created from FEM Part 5 → iga_part_05_pkg3.k
✓ IGA Part 106 created from FEM Part 6 → iga_part_06_pkg4.k
✓ IGA Part 107 created from FEM Part 7 → iga_part_07_pkg5.k
✓ IGA Part 108 created from FEM Part 8 → iga_part_08_pkg6.k
✓ IGA Part 109 created from FEM Part 9 → iga_part_09_pkg7.k
✓ IGA Part 110 created from FEM Part 10 → iga_part_10_pkg8.k
```

**생성 파일**:
- `MinimumModel_iga.k` (8.5MB) - 10개 *INCLUDE 문 포함
- `iga_part_01_front_metal.k` ~ `iga_part_10_pkg8.k` (각 2.8KB) - 11개 키워드 블록

---

## 교훈

1. **빈 줄 처리**: 파일 파싱 시 EOF와 빈 줄을 구분해야 함
   - EOF: `f.readline()` → `''` (빈 문자열)
   - 빈 줄: `f.readline()` → `'\n'` 또는 `'  \n'` → `.strip()` → `''`
   - EOF에서만 break, 빈 줄은 continue

2. **객체 속성 확인**: 클래스의 실제 속성 이름을 확인해야 함
   - `SolidElement.nodes` (○) vs `SolidElement.nids` (✗)
   - `Node.x, y, z` (○) vs `Node.xyz` (✗)

3. **데이터 타입 확인**: 리스트 요소의 타입을 확인해야 함
   - `elem.nodes` → Node 객체 리스트
   - `elem.nodes[i].id` → node ID

4. **디버그 로깅**: 복잡한 파싱 로직에서는 단계별 디버그 출력이 매우 유용함

---

## 파일 수정 내역

1. **KooMeshModifier.py**
   - Line ~1849: 메인 옵션 파싱 루프 빈 줄 처리 수정
   - Line ~1804: FEMtoIGA 블록 파싱 루프 빈 줄 처리 수정

2. **KooIGAPart.py**
   - Line 160: `elem.nids` → `elem.nodes`
   - Line 161: `node.xyz` → `[node.x, node.y, node.z]`

---

## 추가 권장 사항

### 1. 기존 모드들 검증
다른 `**` 블록 파싱 코드들도 동일한 빈 줄 처리 버그가 있을 수 있습니다. 검토 필요:
- `**ElasticToRigid`
- `**MaterialExchange`
- `**PartExchange`
- 기타 모든 `**` 블록

### 2. 유닛 테스트 추가
옵션 파일 파싱 로직에 대한 유닛 테스트 작성 권장:
- 빈 줄이 포함된 옵션 파일
- 주석이 포함된 옵션 파일
- 다양한 줄바꿈 스타일 (LF, CRLF)

### 3. 에러 메시지 개선
```python
# Before
if not line:
    break

# After
if not line:  # EOF
    break
```

코드에 주석을 달아 의도를 명확히 하면 향후 유지보수에 도움됩니다.
