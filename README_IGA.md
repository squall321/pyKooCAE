# IGA Part Generator

KooPart에서 FEM 솔리드 파트를 IGA (Isogeometric Analysis) 포맷으로 변환하는 기능

## 📁 프로젝트 구조

```
pyKooCAE/
├── occProject/Generators/KooCAEManager/
│   ├── KooIGAPart.py           # IGA 파트 클래스 (신규)
│   ├── KooSection.py           # KooSectionIGASolid 추가
│   ├── KooMaterial.py          # CloneMaterial() 추가
│   └── KooPart.py              # IGA 관련 메서드 추가
│
├── docs/
│   ├── part_iga.md             # 개발 계획서
│   └── IGA_IMPLEMENTATION_SUMMARY.md  # 구현 완료 보고서
│
├── examples/
│   └── example_iga_usage.py    # 사용 예제
│
└── tests/iga_tests/
    ├── README.md
    ├── test_iga_standalone.py  # 독립 테스트 ✅
    ├── test_iga_simple.py      # 모듈 테스트
    └── test_iga_part.py        # 통합 테스트
```

## 🚀 빠른 시작

### 방법 1: KooMeshModifier 사용 (권장) ⭐

옵션 파일 기반으로 여러 파트를 자동으로 IGA 변환:

```bash
# 옵션 파일 작성
cat > iga_convert.txt << EOF
*Inputfile
model.k

*Mode
FEM_TO_IGA,22

**FEMtoIGA,22
*IGA,5,100,iga_part_5.k
*IGA,7,101,iga_part_7.k,0.4,0.4,0.3
*IGA,10,102,iga_part_10.k,0.5,0.5,0.4,1.2,1
**EndFEMtoIGA

*End
EOF

# 실행
python occProject/Generators/KooMeshModifier.py iga_convert.txt

# 생성 파일
# - model_iga.k         (FEM + *INCLUDE 문)
# - iga_part_5.k        (IGA 키워드 9개 블록)
# - iga_part_7.k        (IGA 키워드 9개 블록)
# - iga_part_10.k       (IGA 키워드 9개 블록)
```

**파라미터**:
- `PID`: 원본 FEM Part ID
- `IGAID`: IGA Part ID
- `File`: 출력 파일명
- `rr,rs,rt`: 요소 크기 (선택, 기본 0.6)
- `ratio`: bbox 확장 비율 (선택, 기본 1.1)
- `ir`: integration rule (선택, 기본 0)

### 방법 2: Python API 직접 사용

```python
from KooCAEManager.KooPart import KooPartManager

# IGA 파트 생성
iga_part = partManager.CreateIGAPart(
    source_pid=5,  # 원본 FEM Part ID
    materialManager=materialManager,
    sectionManager=sectionManager,
    options={
        'iga_id': 100,
        'output_file': 'iga_part.k'
    }
)

# IGA 파일 생성
iga_part.WriteToFile()

# 메인 모델에 Include 추가
with open('main.k', 'w') as f:
    partManager.WriteStreamDynaKeyword(f)
    partManager.WriteIGAIncludes(f)
```

### 2. 생성되는 파일

```
project/
├── main.k              # FEM 파트 + *INCLUDE 문
└── iga_part.k          # IGA 키워드 (9개 블록)
```

## 📖 문서

- **개발 계획서**: [docs/part_iga.md](docs/part_iga.md)
- **구현 보고서**: [docs/IGA_IMPLEMENTATION_SUMMARY.md](docs/IGA_IMPLEMENTATION_SUMMARY.md)
- **MODE 22 구현 계획**: [docs/fem_to_iga_mode.md](docs/fem_to_iga_mode.md)
- **KooMeshModifier 매뉴얼**: [occProject/Generators/KooMeshModifier_Manual.md](occProject/Generators/KooMeshModifier_Manual.md) (MODE 22: FEM_TO_IGA)
- **사용 예제**: [examples/example_iga_usage.py](examples/example_iga_usage.py)

## 🧪 테스트

```bash
# 독립 테스트 실행
python3 tests/iga_tests/test_iga_standalone.py
```

## 🎯 주요 기능

✅ **바운딩박스 자동 계산** (offset ratio 지원)
✅ **디폴트 옵션 제공** (예제 파일 기반)
✅ **ID 자동 할당** (Material, Section)
✅ **배치 처리** (여러 파트 일괄 변환)
✅ **템플릿 호환** (LS-DYNA IGA 키워드)
✅ **KooMeshModifier 통합** (MODE 22 - 옵션 파일 기반 자동화)

## 📋 옵션

### 필수
- `iga_id`: IGA Part ID
- `output_file`: 출력 파일명

### 선택 (디폴트 제공)
- `element_edge_length`: 요소 크기 (기본: 0.6)
- `integration_rule`: 적분 규칙 (기본: 0)
- `stabilization`: 안정화 파라미터
- `bbox_offset_ratio`: bbox 확장 비율 (기본: 1.1 = 10%)
- NURBS, refinement 등

자세한 옵션은 [examples/example_iga_usage.py](examples/example_iga_usage.py) 참조

## 📅 버전

**v1.1** (2026-01-24)
- KooMeshModifier MODE 22 추가 (FEM_TO_IGA)
- 옵션 파일 기반 일괄 변환 지원
- 간편한 한 줄 포맷 (`*IGA,PID,IGAID,File,...`)

**v1.0** (2026-01-23)
- 초기 구현 완료
- 모든 IGA 키워드 생성 지원
- 자동 ID 관리
- 배치 처리 지원
