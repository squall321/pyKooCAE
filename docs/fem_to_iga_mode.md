# FEM_TO_IGA Mode 구현 계획

KooMeshModifier에 새로운 MODE 22: FEM_TO_IGA 추가

## 1. 개요

### 목적
- 여러 FEM 파트를 IGA로 일괄 변환하는 자동화 모드
- 기존 IGA Part Generator 기능을 KooMeshModifier 워크플로우에 통합

### 포맷
```
*Mode
FEM_TO_IGA,22

**FEMtoIGA,22
*IGA,<PID>,<IGAID>,<File>[,rr[,rs[,rt[,ratio[,ir]]]]]
*IGA,<PID>,<IGAID>,<File>[,rr[,rs[,rt[,ratio[,ir]]]]]
...
**EndFEMtoIGA
```

### 파라미터 설명
- **PID**: 원본 FEM Part ID
- **IGAID**: 생성할 IGA Part ID (PID=VID=SID=PATCHID=RID)
- **File**: 출력 파일명 (예: `iga_part1.k`)
- **rr, rs, rt**: 요소 크기 (선택, 기본값: 0.6)
- **ratio**: bbox_offset_ratio (선택, 기본값: 1.1 = 10% 확장)
- **ir**: integration_rule (선택, 기본값: 0)

### 예제
```
*Inputfile
model.k

*Mode
FEM_TO_IGA,22

**FEMtoIGA,22
# 최소 옵션 (나머지 디폴트)
*IGA,5,100,iga_part5.k

# 요소 크기 지정
*IGA,7,101,iga_part7.k,0.4,0.4,0.3

# 모든 옵션 지정
*IGA,10,102,iga_part10.k,0.5,0.5,0.4,1.2,1

**EndFEMtoIGA

*End
```

## 2. 구현 계획

### 2.1 KooMeshModifier.py 수정

#### A. 모드 등록 (ImportOption 메서드)
**위치**: 약 line 257 (마지막 mode 등록 뒤)

```python
elif "fem_to_iga" in svector[0].lower():
    self.modeList.append("FEM_TO_IGA")
    self.modeIDList.append(int(svector[1]))
```

#### B. 옵션 파싱 블록
**위치**: 약 line 1790 (마지막 mode block parser 뒤)

```python
elif "**femtoiga" in line.lower():
    svector = line.split(",")
    curModeID = int(svector[1])
    curOptions = {}
    curOptions["IGAParts"] = []  # List of IGA part configs

    while True:
        line = f.readline().strip()
        line = line.replace('\n','')
        if not line:
            break
        if "**end" in line.lower():
            break
        elif len(line) > 0 and line[0] == "#":
            continue
        elif len(line) > 0 and line[0] == "$":
            continue
        elif "*iga" in line.lower():
            svector = line.split(",")

            # 필수 파라미터
            source_pid = int(svector[1])
            iga_id = int(svector[2])
            output_file = svector[3]

            # 선택 파라미터 (디폴트)
            rr = float(svector[4]) if len(svector) > 4 else 0.6
            rs = float(svector[5]) if len(svector) > 5 else 0.6
            rt = float(svector[6]) if len(svector) > 6 else 0.6
            ratio = float(svector[7]) if len(svector) > 7 else 1.1
            ir = int(svector[8]) if len(svector) > 8 else 0

            iga_config = {
                'source_pid': source_pid,
                'iga_id': iga_id,
                'output_file': output_file,
                'element_edge_length': {'rr': rr, 'rs': rs, 'rt': rt},
                'bbox_offset_ratio': ratio,
                'integration_rule': ir
            }

            curOptions["IGAParts"].append(iga_config)
        else:
            print(f"Invalid option in FEMtoIGA: {line}")
            exit()

    self.modeIDOption[curModeID] = curOptions
```

#### C. Generator 메서드
**위치**: 약 line 1928 (마지막 Generator 메서드 뒤)

```python
def GenerateFEMtoIGA(self, modeid):
    curOption = self.modeIDOption[modeid]
    self.advancedModification.FEMtoIGA(curOption)
```

#### D. 모드 디스패치
**위치**: GenerateModifiedFile 메서드 내 (약 line 2150)

```python
elif mode == "FEM_TO_IGA":
    self.GenerateFEMtoIGA(modeid)
    additionalword += "_iga"
```

### 2.2 KooDynaAdvancedModification.py 수정

**위치**: 약 line 4661 (마지막 메서드 뒤)

```python
def FEMtoIGA(self, option):
    """
    FEM 파트들을 IGA로 일괄 변환

    option = {
        'IGAParts': [
            {
                'source_pid': int,
                'iga_id': int,
                'output_file': str,
                'element_edge_length': {'rr': float, 'rs': float, 'rt': float},
                'bbox_offset_ratio': float,
                'integration_rule': int
            },
            ...
        ]
    }
    """
    iga_parts_configs = option.get("IGAParts", [])

    if not iga_parts_configs:
        print("Warning: No IGA parts specified in FEMtoIGA mode")
        return

    partManager = self.dynaImporter.partManager
    materialManager = self.dynaImporter.matManager
    sectionManager = self.dynaImporter.sectionManager

    for config in iga_parts_configs:
        try:
            # CreateIGAPart 호출
            iga_part = partManager.CreateIGAPart(
                source_pid=config['source_pid'],
                materialManager=materialManager,
                sectionManager=sectionManager,
                options={
                    'iga_id': config['iga_id'],
                    'output_file': config['output_file'],
                    'element_edge_length': config['element_edge_length'],
                    'bbox_offset_ratio': config['bbox_offset_ratio'],
                    'integration_rule': config['integration_rule']
                }
            )

            # IGA 파일 생성
            iga_part.WriteToFile()

            print(f"✓ IGA Part {config['iga_id']} created from FEM Part {config['source_pid']} → {config['output_file']}")

        except Exception as e:
            print(f"✗ Failed to create IGA Part {config.get('iga_id', '?')} from PID {config.get('source_pid', '?')}: {e}")
            raise
```

### 2.3 KooPart.py 확인

기존 구현된 메서드들 확인:
- ✅ `CreateIGAPart()` - 이미 구현됨
- ✅ `WriteIGAIncludes()` - 이미 구현됨
- ✅ `WriteAllIGAFiles()` - 이미 구현됨 (배치 파일 생성)

**추가 필요사항**: 없음 (기존 API 사용)

### 2.4 메인 파일 출력 수정

**위치**: KooMeshModifier.py의 `WriteModifiedFile` 메서드

현재 코드:
```python
def WriteModifiedFile(self, modifiedKeyword):
    filePath = os.path.join(self.curDir, self.inputFileName)
    filePath = filePath.replace(".k","")
    filePath = filePath + modifiedKeyword + ".k"

    with open(filePath, "w") as f:
        f.write("*KEYWORD\n")
        f.write(self.dynaImporter.WriteStreamDynaKeyword())
        f.write("*END\n")
```

수정 후:
```python
def WriteModifiedFile(self, modifiedKeyword):
    filePath = os.path.join(self.curDir, self.inputFileName)
    filePath = filePath.replace(".k","")
    filePath = filePath + modifiedKeyword + ".k"

    with open(filePath, "w") as f:
        f.write("*KEYWORD\n")
        f.write(self.dynaImporter.WriteStreamDynaKeyword())

        # IGA Include 문 추가
        if len(self.dynaImporter.partManager.igaParts) > 0:
            self.dynaImporter.partManager.WriteIGAIncludes(f)

        f.write("*END\n")
```

## 3. 테스트 계획

### 3.1 테스트 옵션 파일

**파일**: `tests/iga_tests/FEMtoIGA_Test.txt`

```
*Inputfile
model.k

*Info,TestModel,v1.0
*Description,FEM to IGA conversion test

*Mode
FEM_TO_IGA,22

**FEMtoIGA,22
# Test 1: Minimal options
*IGA,5,100,iga_part_5.k

# Test 2: Custom element size
*IGA,7,101,iga_part_7.k,0.4,0.4,0.3

# Test 3: All options
*IGA,10,102,iga_part_10.k,0.5,0.5,0.4,1.2,1

**EndFEMtoIGA

*End
```

### 3.2 예상 결과

실행:
```bash
python occProject/Generators/KooMeshModifier.py tests/iga_tests/FEMtoIGA_Test.txt
```

생성 파일:
```
model_iga.k          # FEM + *INCLUDE 문
iga_part_5.k         # IGA 키워드 (9개 블록)
iga_part_7.k         # IGA 키워드 (9개 블록)
iga_part_10.k        # IGA 키워드 (9개 블록)
FEMtoIGA_Test.log    # 로그
```

## 4. 체크리스트

### 구현
- [ ] KooMeshModifier.py: 모드 등록 추가
- [ ] KooMeshModifier.py: 옵션 파싱 블록 추가
- [ ] KooMeshModifier.py: GenerateFEMtoIGA 메서드 추가
- [ ] KooMeshModifier.py: 모드 디스패치 추가
- [ ] KooMeshModifier.py: WriteModifiedFile IGA include 추가
- [ ] KooDynaAdvancedModification.py: FEMtoIGA 메서드 추가

### 테스트
- [ ] 테스트 옵션 파일 작성
- [ ] 테스트 FEM 모델 준비
- [ ] 실행 및 파일 생성 확인
- [ ] 생성된 IGA 키워드 검증

### 문서
- [ ] KooMeshModifier_Manual.md 업데이트 (MODE 22 설명 추가)
- [ ] README_IGA.md에 KooMeshModifier 사용법 추가
- [ ] 예제 파일 추가: `occProject/Generators/dist/Examples/5.SimulationModify/FEMtoIGA.txt`

## 5. 디폴트 값 정리

| 파라미터 | 필수/선택 | 디폴트 | 설명 |
|---------|----------|--------|------|
| PID | 필수 | - | 원본 FEM Part ID |
| IGAID | 필수 | - | IGA Part ID |
| File | 필수 | - | 출력 파일명 |
| rr | 선택 | 0.6 | r-방향 요소 크기 |
| rs | 선택 | 0.6 | s-방향 요소 크기 |
| rt | 선택 | 0.6 | t-방향 요소 크기 |
| ratio | 선택 | 1.1 | bbox 확장 비율 (10%) |
| ir | 선택 | 0 | integration rule (0=reduced) |

## 6. 에러 처리

### 검증 항목
1. source_pid 존재 확인
2. iga_id 중복 확인
3. Material ID 존재 확인 (KooPart.py에서 이미 구현됨)
4. 파일명 유효성 확인

### 에러 메시지
```python
# source_pid not found
ValueError: Source part PID {pid} not found in parts

# iga_id duplicate
ValueError: IGA Part ID {iga_id} already exists

# material_id not found
ValueError: Source part material ID {mid} not found in MaterialManager
```

## 7. 추가 고려사항

### 7.1 파일 경로
- 상대 경로 지원: `iga_parts/part1.k`
- 절대 경로 지원: `/path/to/iga_part.k`
- 디렉터리 자동 생성 고려

### 7.2 배치 처리 최적화
- 현재는 순차 처리
- 필요시 병렬 처리 고려 (나중에)

### 7.3 로깅
- 각 IGA 파트 생성 성공/실패 로그
- 생성된 파일 목록 출력
- 에러 발생 시 계속 진행 vs 중단 정책

## 8. 관련 파일

### 수정 대상
1. `occProject/Generators/KooMeshModifier.py`
2. `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py`

### 참조 파일
1. `occProject/Generators/KooCAEManager/KooPart.py` (CreateIGAPart)
2. `occProject/Generators/KooCAEManager/KooIGAPart.py` (DEFAULT_OPTIONS)
3. `docs/part_iga.md` (원본 계획서)
4. `docs/IGA_IMPLEMENTATION_SUMMARY.md` (구현 완료 보고서)

### 테스트 파일
1. `tests/iga_tests/FEMtoIGA_Test.txt` (신규 생성)
2. `tests/iga_tests/test_mode_integration.py` (통합 테스트, 신규)

## 9. 완료 기준

✅ 모든 체크리스트 항목 완료
✅ 테스트 성공 (최소 3개 IGA 파트 생성)
✅ 생성된 IGA 키워드 9개 블록 검증
✅ Include 문 올바르게 생성
✅ 문서 업데이트 완료
