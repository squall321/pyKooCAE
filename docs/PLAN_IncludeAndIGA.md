# PLAN: Include File Handling + IGA Keyword Support (v4 Final)

## 핵심 원칙

- `*INCLUDE`는 같은 폴더 상대경로
- 읽기는 인라인 (include 안의 키워드도 접근 가능)
- 출력 시 **source_file 태깅**으로 원본 소속 추적 → include 파일 분리 출력
- include 파일은 원본 복사, 메인 파일만 수정

---

## 아키텍처

```
읽기 (현재 동작 유지):
  main.k 읽기 → 키워드 A, B, C         (source: main.k)
  *INCLUDE iga_p1.k → 키워드 D, E      (source: iga_p1.k)
  *INCLUDE iga_p2.k → 키워드 F, G      (source: iga_p2.k)
  → 모든 키워드가 메모리에 인라인 (접촉 분해 등 가능)

수정:
  키워드 A 수정, 키워드 H 추가          (source: main.k)
  키워드 D~G는 수정 안 함              (source 유지)

출력 (preserve_includes=True):
  DropSet.k:
    수정된 A, B, C, H
    *INCLUDE iga_p1.k
    *INCLUDE iga_p2.k
  iga_p1.k: 원본 복사 (D, E 그대로)
  iga_p2.k: 원본 복사 (F, G 그대로)
```

---

## Phase 1: Source File 태깅

**파일**: `KooCAEManager/KooDynaKeyword.py`

### 1a. 읽기 시 태깅

`ReadKeywordsfromFile`에서 각 키워드에 source_file 기록:

```python
def ReadKeywordsfromFile(self, path, ...):
    current_source = path  # 현재 읽고 있는 파일
    ...
    for keyword in parsed_keywords:
        keyword.source_file = current_source  # 태깅
    ...
    # *INCLUDE 발견 시 재귀 호출 (source_file이 include 파일로 바뀜)
    for include_file in include_list:
        self.ReadKeywordsfromFile(include_file, ...)  # 자동으로 태깅
```

### 1b. 메인 파일 vs include 파일 구분

```python
class DynaKeyword:
    source_file = None  # 기본값: None (하위 호환)
```

기존 코드는 source_file을 무시하므로 하위 호환성 유지.

---

## Phase 2: IncludeManager

**파일**: `KooCAEManager/KooIncludeManager.py` (신규)

```python
class KooIncludeManager:
    def __init__(self, main_file_path):
        self.main_file = main_file_path
        self.base_dir = os.path.dirname(main_file_path)
        self.include_files = []   # 상대 파일명 목록
        self.visited = set()      # 순환 참조 방지

    def Scan(self):
        # main_file에서 *INCLUDE 줄 추출 (재귀, 순환 감지)
        # include 파일 안의 *INCLUDE도 재귀 스캔

    def CopyTo(self, target_dir):
        # include 파일을 target_dir로 복사 (같은 폴더에 flat)

    def Validate(self) -> list[str]:
        # 누락 파일 목록 반환

    def GetAllFiles(self) -> list[str]:
        # 메인 + include 전체 절대경로
```

---

## Phase 3: INCLUDE 보존 출력

**파일**: `KooCAEManager/KooMeshImporter.py`, `KooDynaKeyword.py`

### 3a. 출력 시 source_file 기반 분리

```python
def WriteStreamDynaKeyword(self, stream, preserve_includes=True):
    if preserve_includes:
        include_sources = set()  # include 파일 목록 수집

        for keyword in all_keywords:
            if keyword.source_file and keyword.source_file != self.main_file:
                include_sources.add(keyword.source_file)
                continue  # include 소속 키워드는 메인 출력에서 스킵
            keyword.write(stream)  # 메인 소속만 출력

        # *INCLUDE 문 출력
        for include_file in include_sources:
            stream.write("*INCLUDE\n")
            stream.write(f" {os.path.basename(include_file)}\n")
    else:
        # 기존 동작: 전부 인라인
        for keyword in all_keywords:
            keyword.write(stream)
```

### 3b. include 파일 원본 복사

KooMeshModifier가 출력할 때:
```python
if preserve_includes:
    include_mgr = KooIncludeManager(input_file)
    include_mgr.CopyTo(output_dir)  # include 파일 원본 복사
```

### 3c. 옵션

- `preserve_includes=True` (기본): include 구조 보존
- `*MergeIncludes,True`: 전부 인라인 (기존 동작)

---

## Phase 4: IGA Passthrough 파서

**파일**: `KooCAEManager/KooPassthroughKeyword.py` (신규)

```python
class PassthroughKeyword(DynaKeyword):
    """미지원 키워드를 원문 그대로 저장/출력"""
    def __init__(self, keyword_name):
        super().__init__(keyword_name)
        self.raw_lines = []

    def parse(self, raw_text):
        self.raw_lines = raw_text

    def write(self, stream):
        stream.write(f"*{self.keyword_name}\n")
        for line in self.raw_lines:
            stream.write(line)
            if not line.endswith('\n'):
                stream.write('\n')
```

**등록 대상**:
- `IGA_SOLID`, `IGA_3D_NURBS_XYZ`, `IGA_DEV_VOLUME_XYZ`
- `IGA_DEV_STABILIZATION`, `IGA_REFINE_SOLID`, `SECTION_IGA_SOLID`

**용도**:
- preserve_includes=True: include 파일이 원본 복사되므로 passthrough 불필요
- preserve_includes=False (인라인 모드): passthrough가 IGA 키워드를 보존

---

## Phase 5: Stage-in/out + additional_files

### 5a. Stage-in include 복사

**CumulativeScenarioRunner**:
```python
shutil.copy2(input_file, local_input)
mgr = KooIncludeManager(input_file)
mgr.CopyTo(local_work_dir)
```

**LargeScaleDOEManager**:
- `create_runid_directory()`에서 include 사전 복사
- scratch 모드: include도 scratch에 복사

### 5b. additional_files

**scenario.json**:
```json
{
  "environment": {
    "additional_files": ["thermal_input.k", "em_coupling.k"],
    "additional_dirs": ["include_files/"]
  }
}
```

- Stage-in: additional_files도 같은 폴더에 복사
- additional_files 내 `*INCLUDE`도 재귀 스캔

### 5c. 제출 시 검증

`KooChainRun submit`에서:
```python
mgr = KooIncludeManager(model_file)
missing = mgr.Validate()
if missing:
    print(f"Warning: missing include files: {missing}")
```

---

## 구현 순서

| 순서 | Phase | 내용 | 규모 |
|------|-------|------|------|
| 1 | Phase 1 | source_file 태깅 | 소 |
| 2 | Phase 2 | IncludeManager | 소 |
| 3 | Phase 3 | INCLUDE 보존 출력 | 중 |
| 4 | Phase 4 | IGA Passthrough | 소 |
| 5 | Phase 5 | Stage-in + additional_files | 중 |

---

## 파일 변경 목록

| 파일 | 변경 |
|------|------|
| **신규** `KooCAEManager/KooIncludeManager.py` | Include 스캔/복사/검증 |
| **신규** `KooCAEManager/KooPassthroughKeyword.py` | 범용 Passthrough 클래스 |
| `KooCAEManager/KooDynaKeyword.py` | source_file 태깅, INCLUDE 보존 |
| `KooCAEManager/KooMeshImporter.py` | preserve_includes 출력, passthrough 저장 |
| `Runner/CumulativeScenarioRunner.py` | stage-in include 복사 |
| `Runner/LargeScaleDOEManager.py` | include 사전 복사 |
| `Runner/StepConfigBuilder.py` | additional_files 반영 |
| `KooChainRun` | additional_files, 제출 시 검증 |
| `KooMeshModifier.py` | preserve_includes 옵션 |

---

## 테스트

| 테스트 | 검증 |
|--------|------|
| source_file 태깅 | import 후 각 키워드의 source_file 확인 |
| INCLUDE 보존 출력 | `iga_multipid_result.k` → 수정 → `*INCLUDE` 유지 + 파일 분리 |
| IGA 보존 | include 안 IGA 키워드가 원본과 동일 |
| 인라인 모드 | `MergeIncludes=True` → 단일 파일 + IGA passthrough |
| Stage-in | include 파일이 scratch에 복사됨 |
| 순환 참조 | A→B→A 감지 |
| additional_files | 커플링 입력 2개 → 둘 다 stage-in |

---

## 호환성

- include 없는 모델: 기존과 완전 동일 (source_file=None → 무시)
- 기본 모드: include 보존
- `*MergeIncludes,True`: 기존 인라인 동작
- IGA passthrough: 인라인 시에만 필요, 보존 시 원본 복사
