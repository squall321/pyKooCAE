# PLAN: Include File Handling + IGA Keyword Support

## 현재 상태 분석

### 1. *INCLUDE 처리
- **KooDynaKeyword.py**: `*INCLUDE`를 파싱하고 재귀적으로 포함 파일을 읽음 (line 11386-11414)
- **KooIGAPart.py**: IGA 파트용 `*INCLUDE` 생성 가능 (line 385-400)
- **문제**: 포함 파일을 **읽기만** 하고, 출력/복사/이동 시 포함 파일을 **따라가지 않음**

### 2. KooChainRun 파일 이동
- **stage-in**: 메인 입력 파일(DropSet.k)만 로컬로 복사, include 파일 무시
- **copy.sh/copylog.sh**: 결과 파일만 동기화, include 파일 고려 없음
- **폴더 생성**: KooMeshModifier가 Run_xxx 폴더 생성 시 include 파일 미복사

### 3. IGA 키워드
- `*SECTION_IGA_SOLID`, `*IGA_SOLID`, `*IGA_3D_NURBS_XYZ` 등 6종 미지원
- KooRemapper가 별도로 생성하고 include 파일로 참조
- KooDynaKeyword.py에 파서 없음

---

## 구현 계획

### Phase 1: Include File Tracker (IncludeManager)

**목표**: K파일에서 `*INCLUDE`된 파일 목록을 추적하고, 파일 이동 시 함께 처리

**구현 위치**: `KooCAEManager/KooIncludeManager.py` (신규)

```
class KooIncludeManager:
    - include_files: dict  # {relative_path: absolute_path}
    - base_dir: str        # 기준 디렉토리

    - ScanIncludes(k_file_path) → [파일 경로 목록]
      # K파일을 읽어서 *INCLUDE 라인 추출 (재귀)

    - CopyIncludesToDir(target_dir)
      # include 파일들을 target_dir로 복사
      # 상대경로 유지

    - ResolveRelativePaths(new_base_dir)
      # include 경로를 new_base_dir 기준으로 재계산

    - GetAllFiles() → [메인 + include 파일 전체 목록]
```

**KooMeshImporter 연동**:
- `importDynaFile()` 시 include 파일 목록을 `KooIncludeManager`에 등록
- `WriteStreamDynaKeyword()` 시 include 경로를 출력에 반영

**영향 범위**: KooMeshModifier, KooMeshImporter

---

### Phase 2: KooChainRun Include 지원

**목표**: stage-in/out, 폴더 이동 시 include 파일도 함께 처리

#### 2a. Stage-in 개선

**현재** (CumulativeScenarioRunner.py):
```python
shutil.copy2(input_file, local_input)  # 메인 파일만
```

**변경**:
```python
# 메인 파일 복사
shutil.copy2(input_file, local_input)
# include 파일 스캔 + 복사
include_mgr = KooIncludeManager(input_file)
include_mgr.CopyIncludesToDir(local_work_dir)
```

#### 2b. KooMeshModifier Run 폴더 생성 시

KooMeshModifier가 `Run_xxx/` 폴더에 `DropSet.k`를 생성할 때, 원본 모델의 include 파일도 함께 복사:
- `DropSet.k` 내의 `*INCLUDE` 경로를 Run 폴더 기준 상대경로로 변환
- include 파일을 Run 폴더 하위에 복사

#### 2c. copy.sh/copylog.sh 개선

include 파일도 동기화 대상에 포함:
- `rsync`에 include 파일 경로 추가
- 또는 Run 폴더 전체를 rsync (현재도 이렇게 동작)

---

### Phase 3: scenario.json 추가 파일 옵션

**목표**: 커플링 해석 등에서 입력 파일이 2개 이상일 때, 추가 파일을 지정

**scenario.json 확장**:
```json
{
  "environment": {
    "additional_files": [
      "thermal_input.k",
      "em_coupling.k",
      "material_library/*.k"
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
- `KooChainRun submit`: slurm script에 추가 파일 복사 명령 포함
- Stage-in: additional_files + include 파일 모두 로컬로 복사
- Stage-out: 결과 + additional_files를 NFS로 복사

**step_config.txt 확장**:
```
*AdditionalFiles
thermal_input.k
em_coupling.k
include_files/
*EndAdditionalFiles
```

---

### Phase 4: IGA 키워드 파서 (KooDynaKeyword.py)

**목표**: IGA 관련 6종 키워드를 파싱하여 KooMeshImporter에서 읽기/쓰기 가능

#### 4a. 키워드 클래스 구현

| 키워드 | 클래스 | 설명 |
|--------|--------|------|
| `*SECTION_IGA_SOLID` | `SectionIGASolid` | IGA 솔리드 섹션 |
| `*IGA_SOLID` | `IGASolid` | 패치-파트 연결 |
| `*IGA_3D_NURBS_XYZ` | `IGA3DNurbsXYZ` | NURBS 볼륨 패치 (제어점, 매듭벡터) |
| `*IGA_DEV_VOLUME_XYZ` | `IGADevVolumeXYZ` | 트리밍된 NURBS 볼륨 |
| `*IGA_DEV_STABILIZATION` | `IGADevStabilization` | LCP 안정화 설정 |
| `*IGA_REFINE_SOLID` | `IGARefineSolid` | k-리파인먼트 |

#### 4b. 파서 구현 방식

IGA 키워드는 구조가 복잡 (가변 길이 매듭벡터, 3D 제어점 배열). 두 가지 접근:

**옵션 A: Full Parse** — 각 필드를 개별 속성으로 파싱
- 장점: 수정/변환 가능
- 단점: 구현 복잡, 유지보수 부담

**옵션 B: Passthrough Parse** — 키워드 블록을 통째로 저장
- 장점: 구현 간단, 원본 보존 보장
- 단점: 내부 데이터 수정 불가
- **권장**: IGA 데이터는 KooRemapper가 생성하고 KooMeshModifier는 보존만 하면 되므로

```python
class IGAPassthrough(DynaKeyword):
    """IGA 키워드를 원문 그대로 저장/출력"""
    def __init__(self, keyword_name):
        super().__init__(keyword_name)
        self.raw_lines = []

    def parse(self, lines):
        self.raw_lines = lines  # 원문 그대로 저장

    def write(self, stream):
        stream.write(f"*{self.keyword_name}\n")
        for line in self.raw_lines:
            stream.write(line + "\n")
```

#### 4c. KooMeshImporter 연동

- `keywordInterpreted`에 IGA 키워드 등록
- `importIGA()` 메서드 추가
- `WriteStreamDynaKeyword()`에서 IGA 키워드 출력

#### 4d. KooDynaControl에 IGA 섹션 매니저 추가

- `KooSectionManager`에 `SectionIGASolid` 지원 추가
- IGA 파트 매핑 (FE part ↔ IGA patch)

---

### Phase 5: Include-aware Write

**목표**: K파일 출력 시 include 파일 구조를 보존하거나 재구성

#### 5a. 보존 모드 (기본)
- 원본의 `*INCLUDE` 구조 그대로 유지
- include 파일 내용은 수정하지 않고 원본 복사
- 메인 파일의 non-include 부분만 수정하여 출력

#### 5b. 병합 모드 (옵션)
- 모든 include 파일 내용을 메인 파일에 인라인
- 단일 파일 출력
- `*MergeIncludes,True` 옵션으로 활성화

#### 5c. 분리 모드 (옵션)
- 특정 키워드 블록을 별도 include 파일로 분리
- IGA 데이터를 별도 파일로 분리하여 관리
- `*SplitIncludes,True` 옵션으로 활성화

---

## 구현 순서 및 우선순위

| 순서 | Phase | 우선순위 | 예상 규모 | 의존성 |
|------|-------|----------|-----------|--------|
| 1 | Phase 1: IncludeManager | **높음** | 중 | 없음 |
| 2 | Phase 2a: Stage-in 개선 | **높음** | 소 | Phase 1 |
| 3 | Phase 3: additional_files | **높음** | 중 | 없음 |
| 4 | Phase 4b: IGA Passthrough | 중간 | 소 | 없음 |
| 5 | Phase 2b: Run 폴더 include 복사 | 중간 | 중 | Phase 1 |
| 6 | Phase 4a: IGA Full Parse | 낮음 | 대 | Phase 4b |
| 7 | Phase 5: Include-aware Write | 낮음 | 대 | Phase 1 |

---

## 파일 변경 목록

| 파일 | 변경 내용 |
|------|-----------|
| **신규** `KooCAEManager/KooIncludeManager.py` | Include 파일 추적/복사/경로 해석 |
| `KooCAEManager/KooMeshImporter.py` | IncludeManager 연동, IGA import |
| `KooCAEManager/KooDynaKeyword.py` | IGA 키워드 파서 추가 |
| `KooCAEManager/KooSection.py` | SectionIGASolid 추가 |
| `Runner/CumulativeScenarioRunner.py` | stage-in에 include 복사 추가 |
| `Runner/CumulativeDesigner.py` | additional_files 설정 파싱 |
| `KooChainRun` | additional_files CLI 옵션, helper script 생성 |
| `KooMeshModifier.py` | AdditionalFiles 모드 파싱 |

---

## 테스트 계획

| 테스트 | 검증 내용 |
|--------|-----------|
| IGA 예제 읽기/쓰기 | `iga_multipid_result.k` → import → export → diff |
| Include 파일 복사 | Stage-in 후 로컬 디렉토리에 include 파일 존재 확인 |
| 추가 파일 지정 | scenario.json에 additional_files 지정 → submit 후 파일 존재 확인 |
| 커플링 해석 | 2개 입력 파일 → 두 파일 모두 stage-in/out 확인 |
| IGA + DROP_ATTITUDE | IGA 모델로 낙하 시뮬레이션 → IGA 키워드 보존 확인 |

---

## 호환성

- 기존 기능에 영향 없음 (include 없는 모델은 기존과 동일하게 동작)
- additional_files 미지정 시 기존 동작 유지
- IGA 키워드는 Passthrough로 처리하여 원본 보존
