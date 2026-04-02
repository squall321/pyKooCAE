# PLAN: Include File Handling + IGA Keyword Support (v3 Final)

## 핵심 원칙

- `*INCLUDE`는 항상 **같은 폴더 상대경로**
- 파일 이동 = 메인 파일 + include 파일을 **같은 폴더에 함께 복사**
- 경로 재작성 불필요

---

## Phase 1: IncludeManager (파일 스캔 + 복사)

**파일**: `KooCAEManager/KooIncludeManager.py` (신규)

```python
class KooIncludeManager:
    def __init__(self, k_file_path):
        self.base_dir = os.path.dirname(k_file_path)
        self.include_files = []  # 상대 파일명 목록

    def Scan(self):
        # K파일에서 *INCLUDE 줄 추출 (재귀, 순환 감지)
        # 결과: self.include_files = ["iga_p1.k", "iga_p2.k", ...]

    def CopyTo(self, target_dir):
        # include 파일을 target_dir로 복사 (같은 폴더에 flat)

    def Validate(self) -> list[str]:
        # 누락 파일 목록 반환

    def GetAllFiles(self) -> list[str]:
        # 메인 + include 전체 절대경로 목록
```

---

## Phase 2: INCLUDE 보존 출력

**문제**: KooDynaKeyword.py가 출력 시 `*INCLUDE`를 제거하고 인라인

**수정**: `KooDynaKeyword.py`
```python
# 기존: INCLUDE 제거
while "INCLUDE" in lines_with_asterisk:
    lines_with_asterisk.remove("INCLUDE")

# 변경: preserve_includes 옵션에 따라 분기
if not self.preserve_includes:
    while "INCLUDE" in lines_with_asterisk:
        lines_with_asterisk.remove("INCLUDE")
# preserve_includes=True면 *INCLUDE 유지 + 파일 복사
```

**KooMeshModifier RunDirectoryMode**:
- Run_xxx 폴더 생성 시 include 파일도 같은 폴더에 복사

**기본값**: `preserve_includes=True`
**인라인 모드**: `*MergeIncludes,True` 옵션으로 전환 가능

---

## Phase 3: Stage-in/out Include 지원

### 3a. CumulativeScenarioRunner stage-in
```python
shutil.copy2(input_file, local_input)
# include 파일 스캔 + 같은 폴더에 복사
mgr = KooIncludeManager(input_file)
mgr.CopyTo(local_work_dir)
```

### 3b. LargeScaleDOEManager
- `create_runid_directory()`에서 include 파일 사전 복사
- Slurm scratch 모드: include 파일도 scratch에 복사

### 3c. 제출 시 검증
- `KooChainRun submit` 시 include 파일 존재 확인
- 누락 시 warning 출력

---

## Phase 4: additional_files 옵션

**scenario.json**:
```json
{
  "environment": {
    "additional_files": ["thermal_input.k", "em_coupling.k"],
    "additional_dirs": ["include_files/"]
  }
}
```

**동작**:
- Stage-in: additional_files도 메인 파일과 같은 폴더에 복사
- additional_files 내 `*INCLUDE`도 재귀 스캔 (IncludeManager)
- glob 패턴 지원 (`*.k`)

---

## Phase 5: IGA Passthrough 파서

**파일**: `KooCAEManager/KooPassthroughKeyword.py` (신규)

```python
class PassthroughKeyword(DynaKeyword):
    """미지원 키워드를 원문 그대로 저장/출력 (IGA 등)"""
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

**등록 대상**: `IGA_SOLID`, `IGA_3D_NURBS_XYZ`, `IGA_DEV_VOLUME_XYZ`, `IGA_DEV_STABILIZATION`, `IGA_REFINE_SOLID`, `SECTION_IGA_SOLID`

**KooMeshImporter 연동**:
- `keywordInterpreted`에 등록
- `WriteStreamDynaKeyword()`에서 passthrough 키워드 출력

**범용 설계**: IGA 전용이 아닌, 향후 미지원 키워드에도 재사용 가능

---

## 구현 순서

| 순서 | Phase | 규모 | 의존성 |
|------|-------|------|--------|
| 1 | Phase 1: IncludeManager | 소 | 없음 |
| 2 | Phase 2: INCLUDE 보존 출력 | 중 | Phase 1 |
| 3 | Phase 5: IGA Passthrough | 소 | Phase 2 |
| 4 | Phase 3: Stage-in include 복사 | 소 | Phase 1 |
| 5 | Phase 4: additional_files | 중 | Phase 1 |

---

## 파일 변경 목록

| 파일 | 변경 |
|------|------|
| **신규** `KooCAEManager/KooIncludeManager.py` | Include 스캔/복사/검증 |
| **신규** `KooCAEManager/KooPassthroughKeyword.py` | 범용 Passthrough 클래스 |
| `KooCAEManager/KooDynaKeyword.py` | INCLUDE 보존 옵션 |
| `KooCAEManager/KooMeshImporter.py` | IncludeManager + passthrough 연동 |
| `Runner/CumulativeScenarioRunner.py` | stage-in include 복사 |
| `Runner/LargeScaleDOEManager.py` | include 파일 사전 복사 |
| `Runner/StepConfigBuilder.py` | additional_files 반영 |
| `KooChainRun` | additional_files, 제출 시 검증 |

---

## 테스트

| 테스트 | 검증 |
|--------|------|
| `iga_multipid_result.k` import → export | `*INCLUDE` 유지 + IGA 키워드 보존 |
| Stage-in | include 파일이 로컬 scratch에 복사됨 |
| RunDirectoryMode | Run 폴더에 include 파일 존재 |
| 순환 참조 | A→B→A 감지 + 경고 |
| 누락 검증 | 없는 include → warning |
| additional_files | 커플링 입력파일 2개 → 둘 다 stage-in |

---

## 호환성

- include 없는 모델: 기존과 동일
- `preserve_includes=True` 기본: INCLUDE 구조 보존
- `*MergeIncludes,True`: 기존 인라인 동작
- additional_files 미지정: 기존 동작
- IGA passthrough: 원본 보존, 데이터 손실 없음
