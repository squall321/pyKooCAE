# IGA Part Generator 구현 완료 보고서

## 📋 개요

KooPart에서 FEM 솔리드 파트를 IGA (Isogeometric Analysis) 포맷으로 변환하여 별도 파일로 출력하는 기능 구현 완료

**구현 날짜**: 2026-01-23

---

## ✅ 구현 완료 항목

### 1. **KooSectionIGASolid 클래스** ([KooSection.py](occProject/Generators/KooCAEManager/KooSection.py))

IGA 전용 섹션 클래스
- `elform`: 항상 0 (IGA 고정값)
- `ir`: Integration rule (0=reduced Gauss, 1=Full Gauss)
- `GenerateDynaKeyword()`: *SECTION_IGA_SOLID 키워드 생성

```python
class KooSectionIGASolid(KooSection):
    def __init__(self, id, name, ir=0):
        super().__init__(id, name)
        self.elform = 0
        self.ir = ir
```

### 2. **KooIGAPart 클래스** ([KooIGAPart.py](occProject/Generators/KooCAEManager/KooIGAPart.py))

IGA 파트 핵심 클래스

**주요 기능**:
- ✅ 바운딩박스 자동 계산 (offset ratio 지원)
- ✅ 디폴트 옵션 자동 병합
- ✅ IGA 키워드 9개 블록 생성
- ✅ 별도 파일 출력
- ✅ *INCLUDE 문 생성

**생성하는 키워드**:
1. `*PARAMETER_LOCAL`
2. `*PARAMETER_EXPRESSION_LOCAL`
3. `*IGA_DEV_STABILIZATION`
4. `*PART`
5. `*SECTION_IGA_SOLID`
6. `*IGA_DEV_VOLUME_XYZ`
7. `*IGA_SOLID`
8. `*IGA_3D_NURBS_XYZ`
9. `*IGA_REFINE_SOLID`

### 3. **디폴트 옵션** (예제 파일 기반)

```python
DEFAULT_OPTIONS = {
    'element_edge_length': {'rr': 0.6, 'rs': 0.6, 'rt': 0.6},
    'integration_rule': 0,
    'stabilization': {'styp': 4, 'tollg': 1.0e-3},
    'auto_bbox': True,
    'bbox_offset_ratio': 1.1,  # 10% 확장
    'nurbs_params': {'nr': 2, 'ns': 2, 'nt': 2, 'pr': 1, 'ps': 1, 'pt': 1},
    'iga_solid_params': {'nisr': 1, 'niss': 1, 'nist': 1},
    'refine_params': {'rtyp': 2, 'hrtyp': 2, 'itr': 2, 'its': 2, 'itt': 2},
    'volume_params': {'tetmsh': -1, 'esid': None, 'fsid': None}
}
```

### 4. **MaterialManager 확장** ([KooMaterial.py](occProject/Generators/KooCAEManager/KooMaterial.py))

Material 복제 기능 추가

```python
def CloneMaterial(self, source_material, name_suffix=''):
    """Material 복제 및 자동 ID 할당"""
    # Deep copy → ID=0 설정 → AddMaterial (자동 ID 할당)
```

### 5. **SectionManager 확장** ([KooSection.py](occProject/Generators/KooCAEManager/KooSection.py))

IGA Section 생성 기능 추가

```python
def CreateIGASection(self, name, ir=0):
    """IGA 섹션 생성 및 자동 ID 할당"""
    # KooSectionIGASolid 생성 → AddSection (자동 ID 할당)
```

### 6. **KooPartManager 확장** ([KooPart.py](occProject/Generators/KooCAEManager/KooPart.py))

IGA 파트 관리 기능 추가

**새로운 속성**:
```python
self.igaParts = {}           # {iga_pid: KooIGAPart}
self.igaIncludes = []        # ['file1.k', 'file2.k', ...]
self.maxIGAID = 0            # IGA ID 관리
```

**새로운 메서드**:
- `CreateIGAPart()`: IGA 파트 생성 (Material, Section 자동 생성)
- `CreateIGAPartWithAutoID()`: IGA ID 자동 할당
- `WriteAllIGAFiles()`: 모든 IGA 파트 파일 출력
- `WriteIGAIncludes()`: *INCLUDE 문 출력
- `RemoveIGAPart()`: IGA 파트 제거
- `GetIGAPartsBySourcePID()`: 원본 파트로 검색

---

## 🎯 ID 관리 전략 (최종 구현)

### IGA 요구사항
- **PID = VID = SID = PATCHID = RID** (모두 동일해야 함)

### 독립적 ID
- **MID**: MaterialManager가 자동 할당 (원본 복제)
- **SECID**: SectionManager가 자동 할당 (IGA 전용 Section)

### ID 충돌 방지
- 각 Manager가 `maxid`를 관리하여 중복 방지
- `AddMaterial(id=0)` → 자동 할당
- `AddSection(id=0)` → 자동 할당

---

## 📖 사용 예시

### 최소 옵션 (디폴트 사용)

```python
from KooCAEManager.KooPart import KooPartManager

# 1. IGA 파트 생성
iga_part = partManager.CreateIGAPart(
    source_pid=5,
    materialManager=materialManager,
    sectionManager=sectionManager,
    options={
        'iga_id': 100,
        'output_file': 'iga_part.k'
    }
)

# 2. IGA 파일 생성
iga_part.WriteToFile()

# 3. 메인 모델에 Include 추가
with open('main.k', 'w') as f:
    f.write('*KEYWORD\n')
    partManager.WriteStreamDynaKeyword(f)  # FEM 파트들
    partManager.WriteIGAIncludes(f)        # *INCLUDE 문
    f.write('*END\n')
```

### 커스텀 옵션

```python
options = {
    'iga_id': 100,
    'output_file': 'iga_part.k',

    # 요소 크기 변경
    'element_edge_length': {'rr': 0.8, 'rs': 0.8, 'rt': 0.5},

    # Full Gauss integration
    'integration_rule': 1,

    # 안정화 파라미터 조정
    'stabilization': {'styp': 3, 'tollg': 5.0e-4},

    # 바운딩박스 확장 비율 (20%)
    'bbox_offset_ratio': 1.2,

    # 수동 bbox 설정
    'auto_bbox': False,
    'manual_bbox': {
        'xmin': -30.0, 'xmax': 30.0,
        'ymin': -5.0, 'ymax': 5.0,
        'zmin': -10.0, 'zmax': 2.0
    }
}

iga_part = partManager.CreateIGAPart(5, materialManager, sectionManager, options)
```

### 배치 처리

```python
# 여러 파트를 IGA로 변환
part_ids = [5, 7, 12, 15]

for pid in part_ids:
    partManager.CreateIGAPartWithAutoID(
        pid,
        materialManager,
        sectionManager,
        options={'element_edge_length': {'rr': 0.8}}
    )

# 모든 IGA 파일 일괄 생성
partManager.WriteAllIGAFiles(output_dir='./iga_parts')
```

---

## 📁 생성되는 파일 구조

```
project/
├── main.k                    # 메인 모델 (FEM + IGA Includes)
└── iga_parts/               # IGA 전용 디렉토리
    ├── iga_part_5_id100.k   # IGA Part 1
    ├── iga_part_7_id101.k   # IGA Part 2
    └── ...
```

### main.k 예시

```
*KEYWORD
$
$--- FEM Parts ---
$
*PART
Part-1
$#     pid     secid       mid
         1         1         1
*ELEMENT_SOLID
...

$
$--- IGA Part Includes ---
$
*INCLUDE
iga_parts/iga_part_5_id100.k
*INCLUDE
iga_parts/iga_part_7_id101.k
*END
```

---

## 🔧 바운딩박스 계산 로직

### 자동 계산 (auto_bbox=True)

```python
# 1. 원본 파트의 모든 노드 좌표 수집
# 2. min/max 계산
# 3. bbox 중심 및 크기 계산
# 4. offset_ratio 적용

xmin = x_center - (x_size / 2.0) * bbox_offset_ratio
xmax = x_center + (x_size / 2.0) * bbox_offset_ratio
```

**예시**:
- 원본 bbox: `xmin=-1.0, xmax=1.0` (크기=2.0, 중심=0.0)
- `bbox_offset_ratio=1.1` (10% 확장)
- 결과: `xmin=-1.1, xmax=1.1`

### 템플릿의 추가 확장

PARAMETER_EXPRESSION_LOCAL에서 요소 크기만큼 추가 확장:
```
rxminn = &xmin - &rr
rxmaxx = &xmax + &rr
```

---

## ✨ 주요 특징

### 1. **완전 분리 (Recommended)**
- FEM 파트: 메인 파일에 직접 작성
- IGA 파트: 별도 파일 + *INCLUDE로 참조
- Material, Section: 각 Manager가 독립적으로 ID 관리

### 2. **유연한 옵션 시스템**
- 필수: `iga_id`, `output_file`
- 선택: 모든 파라미터 (디폴트 제공)
- 딕셔너리 병합: 일부만 변경해도 OK

### 3. **ID 충돌 방지**
- MaterialManager.CloneMaterial() → 자동 ID
- SectionManager.CreateIGASection() → 자동 ID
- 기존 FEM 모델과 완전히 독립

### 4. **템플릿 호환**
- 제공된 예제 파일과 동일한 포맷
- 모든 키워드 블록 정확히 재현
- 파라미터 이름 및 순서 일치

---

## 🧪 테스트 결과

### 독립 테스트 (test_iga_standalone.py)
- ✅ KooSectionIGASolid 키워드 생성 검증
- ✅ PARAMETER_LOCAL 포맷 검증
- ✅ 템플릿과 출력 비교 성공

---

## 📝 구현 파일 목록

| 파일 | 설명 |
|------|------|
| [KooIGAPart.py](occProject/Generators/KooCAEManager/KooIGAPart.py) | IGA 파트 클래스 (새로 생성) |
| [KooSection.py](occProject/Generators/KooCAEManager/KooSection.py) | KooSectionIGASolid 추가, CreateIGASection() 추가 |
| [KooMaterial.py](occProject/Generators/KooCAEManager/KooMaterial.py) | CloneMaterial() 메서드 추가 |
| [KooPart.py](occProject/Generators/KooCAEManager/KooPart.py) | IGA 관련 속성 및 메서드 추가 |
| [test_iga_standalone.py](test_iga_standalone.py) | 독립 테스트 스크립트 |

---

## 🚀 향후 개선 가능 사항

### Phase 5 (고급 기능)
- [ ] 다양한 IGA 요소 타입 지원 (shell, beam)
- [ ] 자동 요소 크기 추정 (adaptive sizing)
- [ ] GUI 통합
- [ ] bbox 시각화 기능
- [ ] 설정 파일 import/export (JSON/YAML)
- [ ] 병렬 처리 (여러 파트 동시 변환)
- [ ] 최적화된 bbox (OBB instead of AABB)

### 테스트 강화
- [ ] 실제 FEM 모델 테스트
- [ ] LS-DYNA 실행 검증
- [ ] 다양한 Part 타입 테스트 (Composite, STL 등)

---

## 📚 참고

- 템플릿 파일: `iga_sld_box_Part1.k` (예제)
- 계획서: [part_iga.md](part_iga.md)
- LS-DYNA Keywords:
  - *IGA_3D_NURBS_XYZ
  - *IGA_SOLID
  - *IGA_DEV_VOLUME_XYZ
  - *SECTION_IGA_SOLID

---

## 👨‍💻 작성자

**Development Team**
Date: 2026-01-23
Version: 1.0
