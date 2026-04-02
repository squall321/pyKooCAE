# PLAN: Include File Handling + IGA Keyword Support (v5 Final)

## 핵심 원칙

- `*INCLUDE`는 같은 폴더 상대경로
- 메인 파일: 완전 파싱 (FE 키워드 수정 가능)
- Include 파일: 별도 importer로 로드 (내부 키워드 접근 가능)
- 출력 시 메인/include 분리 보존
- `*PARAMETER_LOCAL` (`&id` 등) 해석 or graceful skip

---

## 아키텍처

```
IncludeManager("main.k")
├── main_importer: KooDynaImporter     ← 메인 파일 완전 파싱
│   ├── partManager (메인 parts)
│   ├── contactManager (접촉 분해 등)
│   └── controlManager (CONTROL 카드)
│
├── includes:
│   ├── "iga_p1.k": KooDynaImporter   ← include 별도 파싱
│   │   ├── partManager (IGA parts)
│   │   ├── matManager (IGA materials)
│   │   └── passthroughKeywords (IGA_3D_NURBS_XYZ 등)
│   └── "iga_p2.k": KooDynaImporter
│       └── ...
│
└── 출력:
    ├── main_output.k  (메인 키워드 + *INCLUDE 문)
    ├── iga_p1.k       (수정 or 원본)
    └── iga_p2.k       (수정 or 원본)
```

---

## Phase 1: PARAMETER_LOCAL 처리

**문제**: include 파일에 `*PARAMETER_LOCAL`로 `&id`, `&mid` 등 변수 정의 → `int('&id')` 에러

**해결 방안**:

### 1a. 파라미터 해석기
```python
class ParameterResolver:
    def __init__(self):
        self.params = {}  # {"id": 1, "mid": 2, ...}

    def ParseParameterLocal(self, lines):
        # *PARAMETER_LOCAL 블록에서 변수=값 추출

    def Resolve(self, value_str) -> str:
        # "&id" → "1" (해석된 값 반환)
        # "123" → "123" (일반 값은 그대로)
```

### 1b. KooDynaKeyword에 적용
```python
# 파싱 시 &변수를 만나면 ParameterResolver로 치환
if value.startswith('&'):
    value = param_resolver.Resolve(value)
```

### 1c. Fallback: Passthrough
파라미터 해석 실패 시 해당 키워드를 PassthroughKeyword로 저장 (에러 대신 원문 보존)

---

## Phase 2: IncludeManager 확장

**파일**: `KooCAEManager/KooIncludeManager.py`

```python
class KooIncludeManager:
    def __init__(self, main_file_path):
        self.main_file = os.path.abspath(main_file_path)
        self.base_dir = os.path.dirname(self.main_file)
        self.include_files = []          # 절대경로 목록
        self.include_importers = {}      # {basename: KooDynaImporter}
        self.main_importer = None        # 메인 파일 importer

    def Scan(self):
        # *INCLUDE 파일 목록 추출 (재귀, 순환 감지)

    def LoadMain(self, preserve_includes=True):
        # 메인 파일 파싱 (include는 스킵)
        self.main_importer = KooDynaImporter()
        self.main_importer.dynaManager.preserve_includes = True
        self.main_importer.importDynaFile(self.main_file)
        self.main_importer.importKeywordstoManager()

    def LoadInclude(self, include_basename):
        # 특정 include 파일을 별도 importer로 파싱
        # PARAMETER_LOCAL 해석 적용
        inc_path = os.path.join(self.base_dir, include_basename)
        imp = KooDynaImporter()
        imp.importDynaFile(inc_path)
        imp.importKeywordstoManager()
        self.include_importers[include_basename] = imp

    def LoadAllIncludes(self):
        # 모든 include 파일을 별도 파싱
        for inc_path in self.include_files:
            self.LoadInclude(os.path.basename(inc_path))

    def GetIncludeImporter(self, basename) -> KooDynaImporter:
        return self.include_importers.get(basename)

    def WriteMain(self, output_dir):
        # 메인 파일 출력 + *INCLUDE 문 + include 파일 복사/출력

    def CopyTo(self, target_dir):
        # include 파일을 target_dir로 복사

    def Validate(self) -> list[str]:
        # 누락 파일 목록
```

**사용 예**:
```python
mgr = KooIncludeManager("model.k")
mgr.Scan()
mgr.LoadMain()

# 메인 파일 접촉 분해
mgr.main_importer.contactManager.ConvertAss5ToAstsPartPairs(...)

# include 파일 내부 접근
mgr.LoadInclude("iga_p1.k")
iga_parts = mgr.include_importers["iga_p1.k"].partManager
print(iga_parts.parts)  # IGA part 정보 접근

# 출력
mgr.WriteMain("output/")  # main + *INCLUDE + include 파일
```

---

## Phase 3: INCLUDE 보존 출력

### 3a. 읽기
- 메인 파일: `preserve_includes=True` → include 내용 인라인 안 함
- Include 파일: 별도 `LoadInclude()`로 독립 파싱

### 3b. 출력
```python
def WriteMain(self, output_dir):
    # 1. 메인 파일 출력 (FE 키워드만)
    main_output = os.path.join(output_dir, "DropSet.k")
    with open(main_output, 'w') as f:
        f.write("*KEYWORD\n")
        f.write(self.main_importer.WriteStreamDynaKeyword())
        # *INCLUDE 문 출력
        for inc_file in self.include_files:
            f.write("*INCLUDE\n")
            f.write(f" {os.path.basename(inc_file)}\n")
        f.write("*END\n")

    # 2. include 파일 처리
    for inc_file in self.include_files:
        basename = os.path.basename(inc_file)
        if basename in self.include_importers:
            # 수정된 include → 새로 출력
            imp = self.include_importers[basename]
            out_path = os.path.join(output_dir, basename)
            with open(out_path, 'w') as f:
                f.write(imp.WriteStreamDynaKeyword())
        else:
            # 미수정 include → 원본 복사
            shutil.copy2(inc_file, os.path.join(output_dir, basename))
```

---

## Phase 4: IGA Passthrough 파서

**파일**: `KooCAEManager/KooPassthroughKeyword.py` (이미 구현)

**등록 대상**:
- `IGA_SOLID`, `IGA_3D_NURBS_XYZ`, `IGA_DEV_VOLUME_XYZ`
- `IGA_DEV_STABILIZATION`, `IGA_REFINE_SOLID`, `SECTION_IGA_SOLID`

**용도**:
- include 파일을 `LoadInclude()`로 파싱할 때, IGA 키워드를 passthrough로 보존
- 파라미터 해석 후에도 IGA 데이터 원문 유지

---

## Phase 5: Stage-in/out + additional_files

### 5a. Stage-in (이미 구현)
```python
# CumulativeScenarioRunner
inc_mgr = KooIncludeManager(input_file)
inc_mgr.CopyTo(local_work_dir)  # include 파일 복사
# + additional_files 복사
```

### 5b. additional_files (이미 구현)
```json
{
  "environment": {
    "additional_files": ["thermal.k", "em.k"],
    "additional_dirs": ["includes/"]
  }
}
```

### 5c. 제출 시 검증 (이미 구현)
```
KooChainRun submit 시:
  Include files: 2
    iga_p1.k
    iga_p2.k
  WARNING: Missing include files: [...]  (있으면)
```

---

## Phase 6: KooMeshModifier 연동

### 6a. preserve_includes 옵션

KooMeshModifier step_config에서:
```
*PreserveIncludes,True       ← 기본값
*MergeIncludes,True          ← 인라인 모드 (기존 동작)
```

### 6b. KooMeshModifier 내부

```python
# KooMeshModifier.py
if preserve_includes:
    mgr = KooIncludeManager(input_file)
    mgr.Scan()
    mgr.LoadMain()
    # 수정 작업은 mgr.main_importer에 대해
    advMod = KooDynaAdvancedModification(mgr.main_importer)
    advMod.DropAttitude(...)
    # 출력
    mgr.WriteMain(output_dir)
else:
    # 기존 동작: 전부 인라인
    importer = KooDynaImporter()
    importer.importDynaFile(input_file)
    ...
```

---

## 구현 순서

| 순서 | Phase | 내용 | 규모 | 상태 |
|------|-------|------|------|------|
| 1 | Phase 1a | ParameterResolver | 중 | 미구현 |
| 2 | Phase 2 | IncludeManager 확장 (LoadInclude) | 중 | 부분 구현 |
| 3 | Phase 3 | INCLUDE 보존 출력 (WriteMain) | 중 | 부분 구현 |
| 4 | Phase 4 | IGA Passthrough 등록 | 소 | 클래스 구현, 등록 미완 |
| 5 | Phase 5 | Stage-in + additional_files | 소 | ✅ 구현 |
| 6 | Phase 6 | KooMeshModifier 연동 | 중 | 미구현 |

---

## 파일 변경 목록

| 파일 | 변경 |
|------|------|
| **신규** `KooCAEManager/KooParameterResolver.py` | PARAMETER_LOCAL 해석 |
| `KooCAEManager/KooIncludeManager.py` | LoadMain/LoadInclude/WriteMain 추가 |
| `KooCAEManager/KooPassthroughKeyword.py` | 이미 구현 |
| `KooCAEManager/KooDynaKeyword.py` | source_file 태깅, preserve_includes |
| `KooCAEManager/KooMeshImporter.py` | passthrough 키워드 등록/출력 |
| `Runner/CumulativeScenarioRunner.py` | stage-in include 복사 (구현됨) |
| `Runner/LargeScaleDOEManager.py` | scratch include 복사 (구현됨) |
| `KooChainRun` | include 검증 (구현됨) |
| `KooMeshModifier.py` | preserve_includes 모드 분기 |

---

## 테스트

| 테스트 | 검증 |
|--------|------|
| IGA 예제 preserve | `iga_multipid_result.k` → LoadMain → WriteMain → *INCLUDE 유지 |
| IGA include 접근 | LoadInclude → partManager 접근 가능 |
| PARAMETER_LOCAL | `&id` → 실제 값으로 치환 |
| Passthrough | IGA_3D_NURBS_XYZ 원문 보존 |
| 수정된 include 출력 | include 파트 수정 → 새 파일로 출력 |
| 미수정 include | 원본 복사 |
| Stage-in | include + additional_files 로컬 복사 |
| DROP_ATTITUDE + IGA | IGA 모델 낙하 시뮬 → IGA 보존 + 접촉 추가 |

---

## 호환성

- include 없는 모델: 기존과 완전 동일
- `preserve_includes=True` 기본: include 구조 보존
- `*MergeIncludes,True`: 기존 인라인 동작
- PARAMETER_LOCAL 없는 include: 정상 파싱
- PARAMETER_LOCAL 있는 include: 해석 후 파싱, 실패 시 passthrough
