# IGA Part Generator 개발 계획서

## 1. 개요

### 목적
KooPart에서 FEM 솔리드 파트를 IGA (Isogeometric Analysis) 포맷으로 변환하여 별도 파일로 출력하는 기능 개발

### 핵심 기능
- 단일 Part ID를 기반으로 IGA 전용 파트 생성
- 재료(Material)와 섹션(Section)을 동일 속성으로 복제하되 별도 ID 관리
- IGA 포맷 키워드 생성 (*IGA_3D_NURBS_XYZ, *IGA_SOLID 등)
- Stream 기반 별도 파일 출력
- 메인 모델에서 *INCLUDE로 참조

---

## 2. 입력 파라미터 분석

### 사용자 설정 옵션 (모든 파라미터 옵션화)
```python
options = {
    # === 필수 파라미터 ===
    'source_pid': int,           # 원본 FEM Part ID (필수)
    'iga_id': int,               # IGA용 통합 ID (PID, SECID, VID, SID, PATCHID, RID) (필수)
    'output_file': str,          # 출력 파일명 (예: 'iga_sld_box_Part1.k') (필수)

    # === 요소 크기 설정 (선택, default 있음) ===
    'element_edge_length': {     # 요소 크기 (knot span size)
        'rr': float,             # r-방향 (x) (default: 0.6)
        'rs': float,             # s-방향 (y) (default: 0.6)
        'rt': float              # t-방향 (z) (default: 0.6)
    },

    # === Integration Rule (선택) ===
    'integration_rule': int,     # 0=reduced Gauss, 1=Full Gauss (default: 0)

    # === Stabilization 설정 (선택) ===
    'stabilization': {
        'styp': int,             # 안정화 타입 (default: 4)
        'tollg': float           # LCP threshold (default: 1.0e-3)
    },

    # === 바운딩박스 설정 (선택) ===
    'auto_bbox': bool,           # 자동 바운딩박스 계산 (default: True)
    'manual_bbox': {             # 수동 bbox 설정 (auto_bbox=False일 때 사용)
        'xmin': float, 'xmax': float,
        'ymin': float, 'ymax': float,
        'zmin': float, 'zmax': float
    },

    # === IGA_3D_NURBS_XYZ 파라미터 (선택, 고급) ===
    'nurbs_params': {
        'nr': int, 'ns': int, 'nt': int,    # 각 방향 knot 개수 (default: 2, 2, 2)
        'pr': int, 'ps': int, 'pt': int,    # 다항식 차수 (default: 1, 1, 1)
        'unir': int, 'unis': int, 'unit': int  # Uniform knot vector (default: 1, 1, 1)
    },

    # === IGA_SOLID 파라미터 (선택, 고급) ===
    'iga_solid_params': {
        'nisr': int, 'niss': int, 'nist': int  # Integration points (default: 1, 1, 1)
    },

    # === IGA_REFINE_SOLID 파라미터 (선택, 고급) ===
    'refine_params': {
        'rtyp': int,             # Refinement type (default: 2)
        'hrtyp': int,            # h-refinement type (default: 2)
        'itr': int, 'its': int, 'itt': int  # Refinement iterations (default: 2, 2, 2)
    },

    # === IGA_DEV_VOLUME_XYZ 파라미터 (선택, 고급) ===
    'volume_params': {
        'tetmsh': int,           # FE embedding option (default: -1)
        'esid': int,             # (default: None, 비워둠)
        'fsid': int              # (default: None, 비워둠)
    }
}
```

### 디폴트 값 정의
```python
DEFAULT_OPTIONS = {
    'element_edge_length': {'rr': 0.6, 'rs': 0.6, 'rt': 0.6},
    'integration_rule': 0,
    'stabilization': {'styp': 4, 'tollg': 1.0e-3},
    'auto_bbox': True,
    'nurbs_params': {'nr': 2, 'ns': 2, 'nt': 2,
                     'pr': 1, 'ps': 1, 'pt': 1,
                     'unir': 1, 'unis': 1, 'unit': 1},
    'iga_solid_params': {'nisr': 1, 'niss': 1, 'nist': 1},
    'refine_params': {'rtyp': 2, 'hrtyp': 2, 'itr': 2, 'its': 2, 'itt': 2},
    'volume_params': {'tetmsh': -1, 'esid': None, 'fsid': None}
}
```

### 간단한 사용 예시 (필수 파라미터만)
```python
# 최소 옵션 - 나머지는 디폴트 사용
options = {
    'source_pid': 5,
    'iga_id': 11,
    'output_file': 'iga_sld_box_Part1.k'
}
```

### 고급 사용 예시 (커스텀 파라미터)
```python
# 고급 옵션 - 세부 튜닝
options = {
    'source_pid': 5,
    'iga_id': 11,
    'output_file': 'iga_sld_box_Part1.k',
    'element_edge_length': {'rr': 0.8, 'rs': 0.8, 'rt': 0.5},
    'integration_rule': 1,  # Full Gauss
    'stabilization': {'styp': 3, 'tollg': 5.0e-4},
    'nurbs_params': {'nr': 3, 'ns': 3, 'nt': 2, 'pr': 2, 'ps': 2, 'pt': 1},
    'manual_bbox': {'xmin': -30.0, 'xmax': 30.0,
                    'ymin': -5.0, 'ymax': 5.0,
                    'zmin': -10.0, 'zmax': 2.0}
}
```

---

## 3. 주요 컴포넌트 설계

### 3.0 기존 구조와의 통합 전략

#### 현재 KooPartManager 구조
```
KooPartManager
├── parts{}              # 일반 파트 (FEM)
├── partsRigid{}         # Rigid 파트
├── partSets{}           # 파트 세트
├── constrainedParts{}   # 제약 파트
├── WritetoDynaKeyword() # 모든 파트를 통합 출력
└── WriteStreamDynaKeyword() # Stream 기반 출력
```

#### 제안하는 IGA 통합 방식 (3가지 옵션)

---

### 🎯 **옵션 1: 별도 관리 (권장)**
```
KooPartManager
├── parts{}              # 기존 FEM 파트
├── igaParts{}           # 새로운: IGA 파트 딕셔너리
├── igaIncludes[]        # 새로운: IGA Include 파일 경로 리스트
├── WriteStreamDynaKeyword()  # 기존 FEM만 출력
└── WriteIGAIncludes(stream)  # 새로운: IGA Include 문만 출력

장점:
✅ 기존 코드 영향 최소화 (FEM 로직 그대로 유지)
✅ IGA와 FEM 명확히 분리
✅ IGA 파트는 별도 파일로만 존재
✅ 메인 모델 파일에는 *INCLUDE만 추가

단점:
❌ 새로운 딕셔너리/리스트 관리 필요

사용 예시:
```python
# IGA 파트 생성
iga_part = partManager.CreateIGAPart(source_pid=5, options={...})
iga_part.WriteToFile()  # 별도 파일 생성

# 메인 모델 출력
with open('main.k', 'w') as f:
    f.write('*KEYWORD\n')
    partManager.WriteStreamDynaKeyword(f)  # FEM 파트들
    partManager.WriteIGAIncludes(f)        # IGA Include들
    f.write('*END\n')
```
```

---

### **옵션 2: 파트 상속 구조**
```
KooPart (기존)
├── KooPartComposite (기존)
├── KooSTLPart (기존)
└── KooIGAPart (새로운)  # KooPart 상속

KooPartManager
└── parts{}  # 모든 파트 타입 통합 관리

장점:
✅ 일관된 파트 관리 구조
✅ parts{} 하나로 모든 파트 관리

단점:
❌ IGA는 별도 파일 출력이므로 WriteStreamDynaPart() 로직 복잡해짐
❌ KooIGAPart가 FEM 요소를 가지지 않으므로 상속 구조가 부자연스러움
❌ WritetoDynaElements() 등 불필요한 메서드 상속
```

---

### **옵션 3: 하이브리드 (파트는 별도, 참조는 유지)**
```
KooPartManager
├── parts{}              # 기존 FEM 파트
├── igaParts{}           # IGA 파트 딕셔너리
│   └── {iga_id: (source_pid, KooIGAPart)} # 원본 파트와 연결
└── methods:
    - CreateIGAPart(source_pid, options)
    - WriteIGAFiles(output_dir)  # 모든 IGA 파일 생성
    - WriteIGAIncludes(stream)   # Include 문 출력

장점:
✅ 원본 파트와 IGA 파트 관계 명확
✅ 원본 파트 삭제/수정 시 IGA 파트도 추적 가능
✅ 별도 관리의 장점 + 참조 관계 유지

단점:
❌ 복잡도 약간 증가
```

---

### 🏆 **최종 권장: 옵션 1 (별도 관리)**

**이유:**
1. **명확한 분리**: FEM은 메인 파일, IGA는 Include 파일
2. **기존 코드 보호**: WritetoDynaKeyword() 로직 변경 불필요
3. **간단한 구현**: 새로운 메서드 몇 개만 추가
4. **확장성**: 나중에 다른 Include 타입도 동일 패턴 사용 가능

---

### 3.1 클래스 구조

#### 3.1.1 KooIGAPart (새로 생성, KooPart 상속 안함)
```
위치: occProject/Generators/KooCAEManager/KooIGAPart.py

class KooIGAPart:
    """IGA 솔리드 파트를 관리하는 클래스"""

    속성:
    - id: int                    # 통합 ID (PID, SECID, VID, SID, PATCHID, RID)
    - name: str                  # 파트명
    - source_part: KooPart       # 원본 FEM 파트 참조
    - material: KooMaterial      # IGA용 재료 (복제)
    - section: KooSectionIGASolid # IGA 전용 섹션
    - bbox: dict                 # 바운딩박스 {xmin, xmax, ymin, ...}
    - edge_length: dict          # {rr, rs, rt}
    - integration_rule: int      # IR
    - stabilization: dict        # {styp, tollg}
    - nurbs_params: dict         # {nr, ns, nt, pr, ps, pt, unir, unis, unit}
    - iga_solid_params: dict     # {nisr, niss, nist}
    - refine_params: dict        # {rtyp, hrtyp, itr, its, itt}
    - volume_params: dict        # {tetmsh, esid, fsid}
    - output_file: str           # 출력 파일 경로

    메서드:
    - __init__(source_part, options)
    - _MergeWithDefaults(options)  # 디폴트 값 병합
    - CalculateBoundingBox()     # 자동 bbox 계산
    - CloneMaterialAndSection()  # 재료/섹션 복제
    - GenerateIGAKeywords()      # IGA 키워드 문자열 생성
    - WriteStreamIGAKeyword(stream)  # Stream 출력
    - WriteToFile()              # 별도 파일 생성
    - GenerateInclude()          # *INCLUDE 문자열 반환
```

#### 3.1.2 KooSectionIGASolid (새로 생성)
```
위치: occProject/Generators/KooCAEManager/KooSection.py에 추가

class KooSectionIGASolid(KooSection):
    """IGA 솔리드 섹션"""

    속성:
    - id: int
    - name: str
    - elform: int = 0            # IGA는 항상 0
    - ir: int                    # Integration rule

    메서드:
    - WritetoDynaKeyword()       # *SECTION_IGA_SOLID 생성
    - WriteStreamDynaKeyword(stream)
```

---

### 3.2 KooPartManager에 추가할 속성
```python
class KooPartManager:
    def __init__(self, ...):
        # 기존 속성
        self.maxID = 0
        self.parts = {}
        self.partsRigid = {}
        self.partSets = {}
        self.constrainedParts = {}

        # === IGA 관련 새로운 속성 ===
        self.igaParts = {}           # {iga_id: KooIGAPart}
        self.igaIncludes = []        # ['file1.k', 'file2.k', ...]
        self.maxIGAID = 0            # IGA ID 자동 할당용
```

---

### 3.3 바운딩박스 계산 알고리즘

#### 입력: KooPart.elementManager.elements
#### 출력: {xmin, xmax, ymin, ymax, zmin, zmax}

```python
def CalculateBoundingBox(self):
    """
    원본 파트의 요소들로부터 바운딩박스 계산

    Process:
    1. part.elementManager에서 모든 요소 획득
    2. 각 요소의 노드 ID 추출
    3. part.nodeManager에서 노드 좌표 획득
    4. 전체 노드의 min/max 좌표 계산
    5. 1개 요소 크기만큼 확장 (template 요구사항)
       - xmin -= rr, xmax += rr
       - ymin -= rs, ymax += rs
       - zmin -= rt, zmax += rt
    """

    구현 세부사항:
    - NodeManager.nodes{} → {node_id: KooNode}
    - KooNode.xyz → [x, y, z]
    - ElementManager.elements{} → {elem_id: KooElement}
    - KooElement.nids → [노드ID 리스트]

    고려사항:
    - 솔리드 요소만 처리 (shell/beam 제외)
    - 빈 요소 리스트 예외처리
    - 수치 정밀도 (float precision)
```

---

### 3.4 재료 및 섹션 복제

#### 재료 복제
```python
def CloneMaterial(self, source_material, new_id):
    """
    원본 재료를 새 ID로 복제

    Process:
    1. source_material의 클래스 타입 확인
       (KooMaterialElastic, KooMaterialRigid 등)
    2. 동일 타입의 새 인스턴스 생성
    3. 모든 속성 복사 (rho, E, nu, ...)
    4. id만 new_id로 변경
    5. name에 '_IGA' 접미사 추가

    주의:
    - dynaKeywordString은 복사하지 않음 (재생성)
    - 참조 타입 속성은 deep copy
    """
```

#### 섹션 생성
```python
def CreateIGASection(self, section_id, ir):
    """
    IGA 전용 섹션 생성

    Return: KooSectionIGASolid instance

    Note:
    - elform은 항상 0 (IGA 고정값)
    - ir만 사용자 옵션에서 가져옴
    """
```

---

### 3.5 IGA 키워드 생성

#### 생성할 키워드 블록 (순서대로)

1. **PARAMETER_LOCAL**
```
변수:
- Iid: IGA ID
- Imid: Material ID (동일)
- Ifepid: 원본 FEM Part ID
- Rxmin, Rxmax, Rymin, Rymax, Rzmin, Rzmax: bbox
- Rrs, Rrs, Rrt: 요소 크기
- Iir: Integration rule
- Istyp: 안정화 타입
- Rtollg: 안정화 threshold
```

2. **PARAMETER_EXPRESSION_LOCAL**
```
계산된 변수:
- rxminn = &xmin - &rr
- rxmaxx = &xmax + &rr
- ryminn = &ymin - &rs
- rymaxx = &ymax + &rs
- rzminn = &zmin - &rt
- rzmaxx = &zmax + &rt
```

3. **IGA_DEV_STABILIZATION**
```
sid: &id
styp: &styp
tollg: &tollg
```

4. **PART**
```
name: "Nurbs-Solid_<원본파트명>"
pid: &id
secid: &id
mid: &mid
```

5. **SECTION_IGA_SOLID**
```
secid: &id
elform: 0
ir: &ir
```

6. **IGA_DEV_VOLUME_XYZ**
```
vid: &id
patchid: &id
TETMSH: -1
fepid: &fepid (원본 FEM PID)
```

7. **IGA_SOLID**
```
sid: &id
pid: &id
nisr, niss, nist: 1, 1, 1
rid: &id
```

8. **IGA_3D_NURBS_XYZ**
```
patchid: &id
nr, ns, nt: 2, 2, 2
pr, ps, pt: 1, 1, 1
unir, unis, unit: 1, 1, 1
rfirst/rlast: &xminn / &xmaxx
sfirst/slast: &yminn / &ymaxx
tfirst/tlast: &zminn / &zmaxx

8개 제어점 좌표 (박스 코너):
1. (xminn, yminn, zminn, 1.0)
2. (xmaxx, yminn, zminn, 1.0)
3. (xminn, ymaxx, zminn, 1.0)
4. (xmaxx, ymaxx, zminn, 1.0)
5. (xminn, yminn, zmaxx, 1.0)
6. (xmaxx, yminn, zmaxx, 1.0)
7. (xminn, ymaxx, zmaxx, 1.0)
8. (xmaxx, ymaxx, zmaxx, 1.0)
```

9. **IGA_REFINE_SOLID**
```
rid: &id
rtyp: 2
hrtyp: 2
rr, rs, rt: &rr, &rs, &rt
itr, its, itt: 2, 2, 2
```

---

### 3.6 파일 출력 및 Include 생성

#### 3.5.1 별도 파일 출력
```python
def WriteToFile(self):
    """
    IGA 키워드를 별도 파일로 출력

    Process:
    1. output_file 경로로 파일 오픈
    2. *KEYWORD 헤더 작성
    3. GenerateIGAKeywords() 또는 WriteStreamIGAKeyword() 호출
    4. *END 푸터 작성
    5. 파일 닫기

    Return: 생성된 파일 경로
    """
```

#### 3.5.2 Include 문 생성
```python
def GenerateInclude(self):
    """
    메인 모델에 삽입할 *INCLUDE 문 생성

    Return:
        "*INCLUDE\n" + self.output_file + "\n"

    Note:
    - 상대경로/절대경로 옵션 제공
    """
```

---

## 4. 통합 워크플로우

### 4.1 사용 예시

#### 4.1.1 간단한 사용 (디폴트 값 활용)
```python
from occProject.Generators.KooCAEManager.KooIGAPart import KooIGAPart

# 1. 원본 파트 가져오기
source_part = partManager.parts[5]  # PID=5

# 2. 최소 옵션만 설정 (나머지는 디폴트)
options = {
    'source_pid': 5,
    'iga_id': 11,
    'output_file': 'iga_sld_box_Part1.k'
}

# 3. IGA 파트 생성 (디폴트 자동 적용)
iga_part = KooIGAPart(source_part, options)

# 4. 파일 출력
output_path = iga_part.WriteToFile()

# 5. Include 문 생성
include_string = iga_part.GenerateInclude()

# 6. 메인 모델에 Include 추가
main_model_stream.write(include_string)
```

#### 4.1.2 커스텀 설정 사용
```python
# 1. 원본 파트 가져오기
source_part = partManager.parts[5]

# 2. 고급 옵션 설정
options = {
    'source_pid': 5,
    'iga_id': 11,
    'output_file': 'iga_sld_box_Part1.k',

    # 요소 크기 커스텀
    'element_edge_length': {'rr': 0.8, 'rs': 0.8, 'rt': 0.5},

    # Full Gauss integration
    'integration_rule': 1,

    # 안정화 파라미터 조정
    'stabilization': {'styp': 3, 'tollg': 5.0e-4},

    # 수동 bbox 설정
    'auto_bbox': False,
    'manual_bbox': {
        'xmin': -30.0, 'xmax': 30.0,
        'ymin': -5.0, 'ymax': 5.0,
        'zmin': -10.0, 'zmax': 2.0
    },

    # NURBS 파라미터 커스텀 (2차 다항식)
    'nurbs_params': {
        'nr': 3, 'ns': 3, 'nt': 2,
        'pr': 2, 'ps': 2, 'pt': 1
    },

    # Refinement 반복 횟수 조정
    'refine_params': {'itr': 3, 'its': 3, 'itt': 2}
}

# 3. IGA 파트 생성
iga_part = KooIGAPart(source_part, options)

# 4. 파일 출력
output_path = iga_part.WriteToFile()
print(f"IGA file created: {output_path}")
```

#### 4.1.3 배치 처리 (여러 파트)
```python
# 여러 파트를 IGA로 변환
part_ids = [5, 7, 12, 15]
iga_parts = []

for i, pid in enumerate(part_ids):
    source_part = partManager.parts[pid]

    options = {
        'source_pid': pid,
        'iga_id': 100 + i,  # IGA ID 자동 할당
        'output_file': f'iga_sld_box_Part{pid}.k'
    }

    iga_part = KooIGAPart(source_part, options)
    iga_part.WriteToFile()
    iga_parts.append(iga_part)

# 모든 Include 문을 메인 모델에 추가
with open('main_model_includes.k', 'w') as f:
    for iga_part in iga_parts:
        f.write(iga_part.GenerateInclude())
```

### 4.2 PartManager 통합 (권장 구조)

#### 4.2.1 KooPartManager 확장
```python
# occProject/Generators/KooCAEManager/KooPart.py 에 추가

class KooPartManager:
    def __init__(self, nodeManager=None, elementManager=None):
        # 기존 속성들...
        self.maxID = 0
        self.parts = {}
        self.partsRigid = {}
        # ... 생략 ...

        # === 새로 추가 ===
        self.igaParts = {}           # {iga_id: KooIGAPart}
        self.igaIncludes = []        # ['file1.k', 'file2.k', ...]
        self.maxIGAID = 0            # IGA ID 관리

    # === 새로운 메서드들 ===

    def CreateIGAPart(self, source_pid, options):
        """
        IGA 파트 생성 및 자동 등록

        Args:
            source_pid: 원본 FEM Part ID
            options: IGA 옵션 딕셔너리

        Returns:
            KooIGAPart 인스턴스

        Example:
            iga_part = partManager.CreateIGAPart(5, {
                'iga_id': 11,
                'output_file': 'iga_part5.k'
            })
        """
        if source_pid not in self.parts:
            raise ValueError(f"Source part {source_pid} not found")

        source_part = self.parts[source_pid]

        # options에 source_pid 자동 추가
        if 'source_pid' not in options:
            options['source_pid'] = source_pid

        # IGA 파트 생성
        iga_part = KooIGAPart(source_part, options)

        # IGA ID 관리
        iga_id = options.get('iga_id')
        if iga_id in self.igaParts:
            print(f"Warning: IGA ID {iga_id} already exists, overwriting")

        self.igaParts[iga_id] = iga_part
        self.maxIGAID = max(self.maxIGAID, iga_id)

        # Include 파일 경로 저장
        if iga_part.output_file not in self.igaIncludes:
            self.igaIncludes.append(iga_part.output_file)

        return iga_part

    def CreateIGAPartWithAutoID(self, source_pid, options):
        """
        IGA ID를 자동 할당하여 IGA 파트 생성

        Args:
            source_pid: 원본 FEM Part ID
            options: IGA 옵션 (iga_id 없어도 됨)

        Returns:
            KooIGAPart 인스턴스
        """
        self.maxIGAID += 1
        options['iga_id'] = self.maxIGAID

        if 'output_file' not in options:
            options['output_file'] = f'iga_part_{source_pid}_id{self.maxIGAID}.k'

        return self.CreateIGAPart(source_pid, options)

    def WriteAllIGAFiles(self, output_dir='.'):
        """
        모든 IGA 파트를 파일로 출력

        Args:
            output_dir: 출력 디렉토리 (default: 현재 디렉토리)

        Returns:
            생성된 파일 경로 리스트
        """
        import os

        created_files = []

        for iga_id, iga_part in self.igaParts.items():
            # 출력 경로 조정
            if output_dir != '.':
                original_file = iga_part.output_file
                filename = os.path.basename(original_file)
                iga_part.output_file = os.path.join(output_dir, filename)

            # 파일 생성
            file_path = iga_part.WriteToFile()
            created_files.append(file_path)

            print(f"IGA Part {iga_id} written to: {file_path}")

        return created_files

    def WriteIGAIncludes(self, stream, relative_path=True):
        """
        모든 IGA Include 문을 메인 파일에 출력

        Args:
            stream: 파일 스트림
            relative_path: True이면 상대경로, False이면 절대경로

        Example:
            with open('main.k', 'w') as f:
                partManager.WriteStreamDynaKeyword(f)
                partManager.WriteIGAIncludes(f)
        """
        if len(self.igaParts) == 0:
            return

        stream.write("$\n")
        stream.write("$--- IGA Part Includes ---\n")
        stream.write("$\n")

        for iga_part in self.igaParts.values():
            include_str = iga_part.GenerateInclude(relative_path)
            stream.write(include_str)

    def RemoveIGAPart(self, iga_id):
        """
        IGA 파트 제거

        Args:
            iga_id: 제거할 IGA Part ID
        """
        if iga_id in self.igaParts:
            iga_part = self.igaParts[iga_id]

            # Include 리스트에서도 제거
            if iga_part.output_file in self.igaIncludes:
                self.igaIncludes.remove(iga_part.output_file)

            del self.igaParts[iga_id]
            print(f"IGA Part {iga_id} removed")
        else:
            print(f"IGA Part {iga_id} not found")

    def GetIGAPartsBySourcePID(self, source_pid):
        """
        특정 원본 파트로부터 생성된 IGA 파트들 찾기

        Args:
            source_pid: 원본 FEM Part ID

        Returns:
            List[KooIGAPart]
        """
        result = []
        for iga_part in self.igaParts.values():
            if iga_part.source_part.id == source_pid:
                result.append(iga_part)
        return result
```

---

#### 4.2.2 전체 워크플로우 예시
```python
from occProject.Generators.KooCAEManager.KooPart import KooPartManager
from occProject.Generators.KooCAEManager.KooIGAPart import KooIGAPart

# 1. PartManager 및 FEM 모델 구축
partManager = KooPartManager()
# ... FEM 파트 생성 ...

# 2. IGA 파트 생성 (수동 ID)
iga_part1 = partManager.CreateIGAPart(
    source_pid=5,
    options={
        'iga_id': 100,
        'output_file': 'iga_box_part5.k'
    }
)

# 3. IGA 파트 생성 (자동 ID)
iga_part2 = partManager.CreateIGAPartWithAutoID(
    source_pid=7,
    options={'element_edge_length': {'rr': 0.8}}
)

# 4. 배치 생성
part_ids = [10, 12, 15]
for pid in part_ids:
    partManager.CreateIGAPartWithAutoID(pid, {})

# 5. 모든 IGA 파일 생성
partManager.WriteAllIGAFiles(output_dir='./iga_parts')

# 6. 메인 모델 파일 출력
with open('main_model.k', 'w') as f:
    f.write('*KEYWORD\n')
    f.write('$\n')
    f.write('$--- FEM Parts ---\n')
    f.write('$\n')

    # 기존 FEM 파트 출력
    partManager.WriteStreamDynaKeyword(f)

    f.write('$\n')
    f.write('$--- IGA Parts (via Include) ---\n')
    f.write('$\n')

    # IGA Include 출력
    partManager.WriteIGAIncludes(f)

    f.write('*END\n')

print("Model export completed!")
print(f"IGA Parts: {len(partManager.igaParts)}")
```

---

#### 4.2.3 생성되는 파일 구조
```
project/
├── main_model.k          # 메인 파일 (FEM + IGA Includes)
└── iga_parts/            # IGA 전용 디렉토리
    ├── iga_box_part5.k   # IGA Part 1
    ├── iga_part_7_id101.k  # IGA Part 2 (자동 이름)
    ├── iga_part_10_id102.k
    ├── iga_part_12_id103.k
    └── iga_part_15_id104.k
```

#### 4.2.4 main_model.k 내용 예시
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
$--- IGA Parts (via Include) ---
$
*INCLUDE
iga_parts/iga_box_part5.k
*INCLUDE
iga_parts/iga_part_7_id101.k
*INCLUDE
iga_parts/iga_part_10_id102.k
*INCLUDE
iga_parts/iga_part_12_id103.k
*INCLUDE
iga_parts/iga_part_15_id104.k
*END
```

---

## 5. 구현 단계

### Phase 1: 기본 구조 (1단계)
- [x] KooIGAPart 클래스 골격 생성
- [ ] KooSectionIGASolid 클래스 구현
- [ ] 바운딩박스 계산 알고리즘 구현
- [ ] 단위 테스트 작성

### Phase 2: 복제 및 키워드 생성 (2단계)
- [ ] 재료 복제 함수 구현
- [ ] IGA 키워드 블록 생성 함수 구현
  - [ ] PARAMETER_LOCAL
  - [ ] PARAMETER_EXPRESSION_LOCAL
  - [ ] IGA_DEV_STABILIZATION
  - [ ] PART
  - [ ] SECTION_IGA_SOLID
  - [ ] IGA_DEV_VOLUME_XYZ
  - [ ] IGA_SOLID
  - [ ] IGA_3D_NURBS_XYZ
  - [ ] IGA_REFINE_SOLID
- [ ] 문자열 포맷팅 검증

### Phase 3: 파일 출력 (3단계)
- [ ] WriteToFile() 메서드 구현
- [ ] WriteStreamIGAKeyword() 메서드 구현
- [ ] GenerateInclude() 메서드 구현
- [ ] 파일 경로 처리 (상대/절대)

### Phase 4: 통합 및 테스트 (4단계)
- [ ] KooPartManager 통합
- [ ] 다중 파트 처리 테스트
- [ ] ID 충돌 방지 로직
- [ ] 예외 처리 강화
- [ ] 실제 템플릿과 출력 비교 검증

### Phase 5: 고급 기능 (5단계)
- [ ] 수동 bbox 설정 지원
- [ ] bbox 시각화 기능
- [ ] 배치 처리 인터페이스
- [ ] 설정 파일 import/export
- [ ] 문서화 및 예제 코드

---

## 6. 기술적 고려사항

### 6.1 옵션 병합 로직
```python
def _MergeWithDefaults(self, user_options):
    """
    사용자 옵션과 디폴트 값을 병합

    Process:
    1. DEFAULT_OPTIONS를 복사
    2. user_options의 각 키를 확인
    3. 딕셔너리 타입 옵션은 재귀적으로 병합
       (예: element_edge_length에서 rr만 지정하면 rs, rt는 디폴트)
    4. 단일 값 옵션은 덮어쓰기

    Example:
        user = {'element_edge_length': {'rr': 0.8}}
        결과 = {'element_edge_length': {'rr': 0.8, 'rs': 0.6, 'rt': 0.6}}

    Return: 완전한 옵션 딕셔너리
    """
    import copy

    merged = copy.deepcopy(DEFAULT_OPTIONS)

    for key, value in user_options.items():
        if isinstance(value, dict) and key in merged:
            # 딕셔너리 타입은 재귀 병합
            merged[key].update(value)
        else:
            # 단일 값은 덮어쓰기
            merged[key] = value

    return merged
```

### 6.2 ID 관리 전략
```
문제: IGA에서는 PID, SECID, VID, SID, PATCHID, RID가 모두 동일해야 함

해결책:
1. 단일 'iga_id' 파라미터로 모든 ID 통일
2. PartManager의 maxID와 충돌 방지
   - 별도의 iga_id_pool 관리
   - 또는 사용자가 명시적으로 제공
3. 재료/섹션 ID는 동일 iga_id 사용
```

### 6.3 바운딩박스 확장
```
템플릿 요구사항:
"The trivariate B-Spline Box is extended by one element in each direction
to cut-off boundary elements -> larger time step possible"

구현:
- 계산된 bbox에서 각 방향으로 요소 크기만큼 확장
- xmin_extended = xmin - rr
- xmax_extended = xmax + rr
- (y, z 방향도 동일)
```

### 6.4 좌표 정밀도
```
LS-DYNA 좌표 포맷:
- 고정폭 20자리 (E format)
- 예: "              &xminn" → 파라미터로 처리
- 실제 좌표값은 충분한 유효숫자 유지
```

### 6.5 파라미터 타입 구분
```
LS-DYNA 파라미터:
- I: Integer (Iid, Imid, Ifepid, Iir, Istyp)
- R: Real (Rxmin, Rrs, Rtollg)

구현:
- 타입에 따라 적절한 포맷 적용
- Integer: %d
- Real: %.6e 또는 %.3f
```

### 6.6 파라미터 유효성 검증
```python
def _ValidateOptions(self, options):
    """
    옵션 유효성 검증

    체크 항목:
    1. 필수 파라미터 존재 여부 (source_pid, iga_id, output_file)
    2. 타입 검증 (int는 int, float는 float)
    3. 범위 검증:
       - iga_id > 0
       - element_edge_length > 0
       - integration_rule in [0, 1]
       - styp >= 0
       - tollg > 0
    4. bbox 일관성 (xmin < xmax 등)

    Raises:
        ValueError: 유효하지 않은 옵션
    """
```

---

## 7. 테스트 계획

### 7.1 단위 테스트
```python
# test_iga_part.py

def test_bounding_box_calculation():
    """bbox 계산 정확도 테스트"""
    # 알려진 좌표의 간단한 박스 요소 생성
    # 예상 bbox와 비교

def test_material_cloning():
    """재료 복제 완전성 테스트"""
    # 다양한 재료 타입 복제
    # 모든 속성 복사 확인

def test_keyword_generation():
    """IGA 키워드 문자열 정확도"""
    # 템플릿과 라인별 비교

def test_file_output():
    """파일 출력 및 include 생성"""
    # 파일 생성 확인
    # *KEYWORD, *END 확인
```

### 7.2 통합 테스트
```python
def test_full_workflow():
    """전체 워크플로우 테스트"""
    # 실제 FEM 모델 로드
    # IGA 변환 수행
    # LS-DYNA로 검증 (가능하면)
```

### 7.3 검증 데이터
```
제공된 템플릿 파일:
- Part ID: 11
- Material ID: 5
- FE PID: 5
- bbox: xmin=-25.3, xmax=23.9, ymin=-3.74, ymax=1.0, zmin=-8.0, zmax=0.3
- 요소크기: rr=rs=rt=0.6

→ 이 데이터로 역산하여 검증
```

---

## 8. 확장 가능성

### 8.1 향후 개선 사항
- 다양한 IGA 요소 타입 지원 (shell, beam)
- 자동 요소 크기 추정 (adaptive sizing)
- GUI 통합
- 병렬 처리 (여러 파트 동시 변환)
- 최적화된 bbox (OBB instead of AABB)

### 8.2 호환성
- LS-DYNA 버전 호환성 확인
- Nastran/ANSYS IGA 지원 검토

---

## 9. 참고 자료

### 관련 파일
- Template: 제공된 IGA 솔리드 템플릿
- KooPart.py: 기존 파트 구조
- KooMaterial.py: 재료 관리
- KooSection.py: 섹션 관리

### LS-DYNA 문서
- *IGA_3D_NURBS_XYZ keyword
- *IGA_SOLID keyword
- *IGA_DEV_VOLUME_XYZ keyword
- PARAMETER_LOCAL/EXPRESSION_LOCAL

---

## 10. 예상 결과물

### 10.1 파일 구조
```
project/
├── main_model.k              # 메인 모델
│   └── *INCLUDE iga_sld_box_Part1.k
├── iga_sld_box_Part1.k       # IGA 파트 1
├── iga_sld_box_Part2.k       # IGA 파트 2
└── ...
```

### 10.2 출력 파일 예시
```
iga_sld_box_Part1.k:
- *KEYWORD
- *PARAMETER_LOCAL (9개 파라미터)
- *PARAMETER_EXPRESSION_LOCAL (6개 변수)
- *IGA_DEV_STABILIZATION
- *PART
- *SECTION_IGA_SOLID
- *IGA_DEV_VOLUME_XYZ
- *IGA_SOLID
- *IGA_3D_NURBS_XYZ (8개 제어점)
- *IGA_REFINE_SOLID
- *END
```

### 10.3 Include 예시
```
메인 모델에 추가:
*INCLUDE
iga_sld_box_Part1.k
```

---

## 완료 기준

1. ✅ 단일 Part ID로부터 IGA 파일 생성 성공
2. ✅ 재료/섹션 자동 복제 및 별도 ID 할당
3. ✅ 자동 바운딩박스 계산 정확도
4. ✅ 템플릿과 동일한 포맷의 키워드 생성
5. ✅ Stream 기반 파일 출력
6. ✅ Include 문 자동 생성
7. ✅ 단위/통합 테스트 통과
8. ✅ 실제 LS-DYNA 실행 검증 (optional)

---

---

## 11. 파라미터 참조표

### 11.1 디폴트 값 요약
| 파라미터 | 디폴트 값 | 설명 | 변경 가능 |
|---------|----------|------|---------|
| **element_edge_length** |
| rr | 0.6 | r-방향 (x) 요소 크기 | ✅ |
| rs | 0.6 | s-방향 (y) 요소 크기 | ✅ |
| rt | 0.6 | t-방향 (z) 요소 크기 | ✅ |
| **integration_rule** | 0 | 0=reduced, 1=Full Gauss | ✅ |
| **stabilization** |
| styp | 4 | 안정화 타입 (권장값) | ✅ |
| tollg | 1.0e-3 | LCP threshold | ✅ |
| **auto_bbox** | True | 자동 bbox 계산 | ✅ |
| **nurbs_params** |
| nr, ns, nt | 2, 2, 2 | 각 방향 knot 개수 | ✅ |
| pr, ps, pt | 1, 1, 1 | 다항식 차수 (1=linear) | ✅ |
| unir, unis, unit | 1, 1, 1 | Uniform knot vector | ✅ |
| **iga_solid_params** |
| nisr, niss, nist | 1, 1, 1 | Integration points | ✅ |
| **refine_params** |
| rtyp | 2 | Refinement type | ✅ |
| hrtyp | 2 | h-refinement type | ✅ |
| itr, its, itt | 2, 2, 2 | Refinement iterations | ✅ |
| **volume_params** |
| tetmsh | -1 | FE embedding (고정값) | ⚠️ |
| esid | None | (비워둠) | ✅ |
| fsid | None | (비워둠) | ✅ |

### 11.2 파라미터 의미 (알려진 것)
- **styp=4**: 검증된 안정화 타입 (다른 값은 LS-DYNA 문서 참조)
- **tollg=1.0e-3**: LCP (Light Control Point) threshold
- **tetmsh=-1**: FEM 솔리드 파트를 IGA 메쉬로 임베딩
- **nr, ns, nt=2**: 선형 박스의 각 방향 knot 개수
- **pr, ps, pt=1**: 1차 다항식 (선형)
- **rtyp=2, hrtyp=2**: Refinement 타입 (구체적 의미는 LS-DYNA 문서 참조)

### 11.3 고급 사용자를 위한 가이드
일반 사용자는 디폴트 값으로 충분하며, 다음 경우에만 변경 권장:
- **element_edge_length**: 메쉬 밀도 조절 (작을수록 세밀)
- **integration_rule**: 정확도 vs 속도 트레이드오프
- **pr, ps, pt**: 고차 다항식 (2=quadratic, 3=cubic) - nr, ns, nt도 함께 증가 필요
- **stabilization**: 불안정성 발생 시 tollg 값 증가 (예: 1.0e-2)

---

**작성일**: 2026-01-23
**버전**: 1.1
**업데이트**: 모든 파라미터 옵션화 및 디폴트 값 설정
**작성자**: Development Planning
