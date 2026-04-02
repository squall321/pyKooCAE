# PLAN: Include File Handling + IGA Keyword Support (v2)

## 현재 상태 분석

### 1. *INCLUDE 처리
- **KooDynaKeyword.py**: `*INCLUDE`를 파싱하고 재귀적으로 포함 파일을 읽음
- **문제 1**: 출력 시 `*INCLUDE`가 **제거**되고 내용이 인라인됨 (line 14531-14532)
- **문제 2**: include 파일 경로 추적 없음 → 파일 이동 시 경로 깨짐
- **문제 3**: stage-in/out에서 include 파일 미복사

### 2. IGA 키워드
- 6종 중 `*SECTION_IGA_SOLID`만 KooSection에 부분 지원
- 나머지 5종 (`*IGA_SOLID`, `*IGA_3D_NURBS_XYZ`, `*IGA_DEV_VOLUME_XYZ`, `*IGA_DEV_STABILIZATION`, `*IGA_REFINE_SOLID`)은 파서 없음
- IGA 파일은 `*INCLUDE`로 참조되므로, include 보존이 IGA 지원의 전제조건

### 3. INCLUDE 패턴 (실제 사용)
```
*INCLUDE
 iga_multipid_result_iga_p1.k      ← 상대경로 (같은 디렉토리)
*INCLUDE
 ../shared/material_library.k      ← 상위 디렉토리 참조
*INCLUDE
 /data/shared/materials.k          ← 절대경로
```

### 4. 치명적 문제: INCLUDE 제거
현재 KooDynaKeyword.py가 출력 시 `*INCLUDE`를 제거하고 내용을 인라인:
```python
while "INCLUDE" in lines_with_asterisk:
    lines_with_asterisk.remove("INCLUDE")  # ← INCLUDE 키워드 삭제
```
이러면 IGA include 파일 구조가 파괴됨. 보존 모드가 필수.

---

## 개선된 구현 계획

### Phase 1: IncludeManager + 경로 추적

**목표**: K파일의 `*INCLUDE` 파일 목록을 추적, 복사, 경로 재계산

**구현 위치**: `KooCAEManager/KooIncludeManager.py` (신규)

```python
class KooIncludeManager:
    include_files: dict     # {상대경로: 절대경로}
    base_dir: str           # 기준 디렉토리
    visited: set            # 순환 참조 방지

    def ScanIncludes(k_file_path) -> list[str]
        # K파일에서 *INCLUDE 라인 추출 (재귀, 순환 감지)
        # 경로 정규화 (os.path.normpath)
        # 존재하지 않는 파일 경고

    def CopyIncludesToDir(target_dir, preserve_structure=True)
        # include 파일들을 target_dir로 복사
        # preserve_structure=True: 상대경로 구조 유지
        # preserve_structure=False: flat 복사

    def RewriteIncludePaths(k_file_content, new_base_dir) -> str
        # K파일 내 *INCLUDE 경로를 new_base_dir 기준으로 재작성

    def ValidateAll() -> list[str]
        # 모든 include 파일 존재 확인, 누락 목록 반환

    def GetAllFiles() -> list[str]
        # 메인 + 모든 include 파일 절대경로 목록
```

**핵심 고려사항**:
- 순환 참조 감지 (`visited` set)
- 경로 정규화 (`os.path.normpath`)
- 심볼릭 링크 처리 (`os.path.realpath`)
- 누락 파일 경고 (에러가 아닌 warning)
- 상대/절대 경로 혼합 처리
- `*INCLUDE_PATH` (LS-DYNA 검색 경로) 지원 고려

---

### Phase 2: INCLUDE 보존 출력

**목표**: K파일 출력 시 `*INCLUDE` 구조를 보존

**현재 문제**: KooDynaKeyword.py가 INCLUDE를 제거하고 인라인

**해결**:

#### 2a. KooDynaKeyword.py 수정
```python
# 기존: INCLUDE 제거
while "INCLUDE" in lines_with_asterisk:
    lines_with_asterisk.remove("INCLUDE")

# 변경: 옵션에 따라 보존 또는 인라인
if self.preserve_includes:
    # *INCLUDE 키워드와 경로를 출력에 유지
    # include 파일은 별도로 복사 (IncludeManager)
else:
    # 기존 동작: 인라인
    while "INCLUDE" in lines_with_asterisk:
        lines_with_asterisk.remove("INCLUDE")
```

#### 2b. KooMeshImporter 연동
- `importDynaFile()` 시 include 파일 목록을 IncludeManager에 등록
- `WriteStreamDynaKeyword()` 시:
  - 보존 모드: `*INCLUDE` 출력 + include 파일 원본 복사
  - 인라인 모드: 기존 동작 (모든 내용 단일 파일)

#### 2c. KooMeshModifier RunDirectoryMode
- Run_xxx 폴더 생성 시 include 파일도 함께 복사
- DropSet.k 내 `*INCLUDE` 경로를 Run 폴더 기준으로 재작성

**기본값**: 보존 모드 (`preserve_includes=True`)
**옵션**: `*MergeIncludes,True`로 인라인 모드 전환 가능

---

### Phase 3: Stage-in/out Include 지원

**목표**: KooChainRun에서 파일 이동 시 include 파일도 함께 처리

#### 3a. Stage-in 개선 (CumulativeScenarioRunner)
```python
# 메인 파일 복사
shutil.copy2(input_file, local_input)
# include 파일 스캔 + 복사
from KooIncludeManager import KooIncludeManager
include_mgr = KooIncludeManager(input_file)
missing = include_mgr.ValidateAll()
if missing:
    logging.warning(f"Missing include files: {missing}")
include_mgr.CopyIncludesToDir(local_work_dir)
```

#### 3b. Stage-in 개선 (LargeScaleDOEManager)
- Slurm script에 include 파일 복사 명령 추가
- 또는 `create_runid_directory()`에서 사전 복사

#### 3c. 제출 시 검증
- `KooChainRun submit` 실행 시 include 파일 존재 확인
- 누락 시 경고 + 계속 진행 (또는 `--strict` 옵션으로 중단)

---

### Phase 4: additional_files 옵션

**목표**: 커플링 해석 등에서 추가 입력 파일을 지정

**scenario.json 확장**:
```json
{
  "environment": {
    "additional_files": [
      "thermal_input.k",
      "em_coupling.k"
    ],
    "additional_dirs": [
      "include_files/",
      "material_data/"
    ]
  }
}
```

**동작**:
- `KooChainRun prepare`: additional_files를 runner_config에 기록
- Stage-in: additional_files + include 파일 모두 로컬로 복사
- Stage-out: 결과 + additional_files를 NFS로 복사
- large-scale: Slurm script에 추가 파일 복사 포함

**주의사항**:
- additional_files 자체의 `*INCLUDE`도 재귀 스캔 (IncludeManager 활용)
- glob 패턴 (`*.k`) 지원 — `glob.glob()` 사용
- 디렉토리 구조 보존 (상대경로 유지)
- additional_files와 include 파일의 중복 감지

---

### Phase 5: IGA 키워드 Passthrough 파서

**목표**: IGA 키워드를 원문 그대로 보존

#### 5a. 범용 Passthrough 파서

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

이 클래스를 IGA 전용이 아닌 **범용**으로 만들어서,
향후 미지원 키워드가 추가될 때도 재사용 가능.

#### 5b. 등록 대상 IGA 키워드

| 키워드 | 데이터 구조 | 비고 |
|--------|-------------|------|
| `*IGA_SOLID` | 고정 (1줄 헤더 + 데이터) | |
| `*IGA_3D_NURBS_XYZ` | 가변 (제어점 배열, 매듭벡터) | 가장 복잡 |
| `*IGA_DEV_VOLUME_XYZ` | 가변 | 트리밍 볼륨 |
| `*IGA_DEV_STABILIZATION` | 고정 | LCP 안정화 |
| `*IGA_REFINE_SOLID` | 고정 | k-리파인먼트 |
| `*SECTION_IGA_SOLID` | 고정 | 이미 KooSection에 부분 지원 |

#### 5c. KooMeshImporter 연동

```python
# keywordInterpreted 등록
for kw in ["IGA_SOLID", "IGA_3D_NURBS_XYZ", "IGA_DEV_VOLUME_XYZ",
           "IGA_DEV_STABILIZATION", "IGA_REFINE_SOLID", "SECTION_IGA_SOLID"]:
    if kw in dynaKeyword:
        self.keywordInterpreted[kw] = True

# Passthrough 저장
self.passthroughKeywords = {}
for kw_name, kw_data in dynaKeyword.items():
    if kw_name.startswith("IGA_") and kw_name not in self.keywordInterpreted:
        self.passthroughKeywords[kw_name] = kw_data
```

#### 5d. 출력 시 Passthrough 키워드 포함

```python
def WriteStreamDynaKeyword(self, stream):
    # ... 기존 키워드 출력 ...
    # Passthrough 키워드 출력
    for kw_name, kw_data in self.passthroughKeywords.items():
        kw_data.write(stream)
```

---

### Phase 6: IGA Full Parse (향후)

**목표**: IGA 데이터를 개별 필드로 파싱하여 수정/변환 가능

**우선순위**: 낮음 — Passthrough로 충분한 경우가 대부분
**필요한 경우**: IGA 스케일링, 제어점 이동, 패치 ID 재매핑

---

## 구현 순서 (수정됨)

| 순서 | Phase | 우선순위 | 규모 | 의존성 | 이유 |
|------|-------|----------|------|--------|------|
| 1 | **Phase 1**: IncludeManager | 높음 | 중 | 없음 | 모든 후속 작업의 기반 |
| 2 | **Phase 2a**: INCLUDE 보존 출력 | **최고** | 중 | Phase 1 | INCLUDE 제거가 치명적 문제 |
| 3 | **Phase 5b**: IGA Passthrough | 높음 | 소 | Phase 2 | IGA 파일이 INCLUDE로 참조되므로 |
| 4 | **Phase 3a**: Stage-in include 복사 | 높음 | 소 | Phase 1 | 계산노드 실행 시 필수 |
| 5 | **Phase 4**: additional_files | 중간 | 중 | Phase 1 | 커플링 해석 지원 |
| 6 | **Phase 2c**: RunDirectory include | 중간 | 중 | Phase 1 | KooMeshModifier 연동 |
| 7 | **Phase 3c**: 제출 시 검증 | 중간 | 소 | Phase 1 | 안정성 |
| 8 | **Phase 6**: IGA Full Parse | 낮음 | 대 | Phase 5 | 향후 필요 시 |

---

## 파일 변경 목록

| 파일 | 변경 내용 |
|------|-----------|
| **신규** `KooCAEManager/KooIncludeManager.py` | Include 파일 추적/복사/경로 재작성/검증 |
| **신규** `KooCAEManager/KooPassthroughKeyword.py` | 범용 Passthrough 키워드 클래스 |
| `KooCAEManager/KooDynaKeyword.py` | INCLUDE 보존 옵션, IGA 파서 등록 |
| `KooCAEManager/KooMeshImporter.py` | IncludeManager 연동, IGA passthrough 저장/출력 |
| `Runner/CumulativeScenarioRunner.py` | stage-in include 복사 |
| `Runner/LargeScaleDOEManager.py` | Slurm script에 include 복사 추가 |
| `Runner/CumulativeDesigner.py` | additional_files 파싱 |
| `Runner/StepConfigBuilder.py` | additional_files 설정 반영 |
| `KooChainRun` | additional_files CLI, 제출 시 검증, helper script |
| `KooMeshModifier.py` | preserve_includes 옵션 |

---

## 테스트 계획

| 테스트 | 검증 내용 |
|--------|-----------|
| INCLUDE 보존 | `iga_multipid_result.k` import → export → `*INCLUDE` 유지 확인 |
| IGA passthrough | include 파일 내 IGA 키워드 원문 보존 확인 |
| 중첩 INCLUDE | A.k → B.k → C.k 재귀 포함 + 출력 시 구조 보존 |
| 순환 참조 | A.k → B.k → A.k 감지 + 경고 |
| Stage-in | include 파일이 로컬 scratch에 복사 확인 |
| 경로 재작성 | Run 폴더 이동 후 INCLUDE 경로 유효성 |
| additional_files | scenario.json 추가 파일 → stage-in/out 확인 |
| 누락 검증 | 존재하지 않는 include → warning 출력 |
| 대규모 DOE | 1000 DOE × shared include → 불필요한 중복 복사 방지 |
| apptainer bind | 절대경로 include가 bind mount 내에서 접근 가능 |

---

## 호환성

- 기존 기능에 영향 없음 (include 없는 모델은 기존과 동일)
- 기본값: `preserve_includes=True` (INCLUDE 보존)
- `*MergeIncludes,True`로 기존 인라인 동작 사용 가능
- additional_files 미지정 시 기존 동작 유지
- IGA passthrough는 원본 보존이므로 데이터 손실 없음

---

## 이전 버전 대비 변경점 (v1 → v2)

1. **Phase 2를 최고 우선순위로 상향** — INCLUDE 제거가 치명적 문제
2. **범용 Passthrough 클래스 추가** — IGA 전용이 아닌 재사용 가능 설계
3. **순환 참조 감지** 추가
4. **제출 시 include 파일 검증** 추가
5. **경로 재작성 로직** 추가 (Run 폴더 이동 시)
6. **대규모 DOE 시 중복 복사 방지** 고려
7. **apptainer bind mount 호환성** 고려
