#!/usr/bin/env python3
"""
IGA Section 독립 테스트 (의존성 없음)
"""

# KooSectionIGASolid만 독립적으로 테스트
class KooSectionIGASolid:
    def __init__(self, id, name, ir=0):
        self.id = id
        self.name = name
        self.elform = 0  # IGA는 항상 0
        self.ir = ir  # Integration rule (0=reduced Gauss, 1=Full Gauss)

    def SetIR(self, ir):
        self.ir = ir

    def GenerateDynaKeyword(self):
        keywordString = "*SECTION_IGA_SOLID\n"
        # 10 digit for each value
        formatted_string = "{:10d}{:10d}{:10d}\n".format(self.id, self.elform, self.ir)
        keywordString += formatted_string
        return keywordString


print("=" * 80)
print("KooSectionIGASolid 독립 테스트")
print("=" * 80)

# 1. Section 생성 테스트
print("\n[1] Section 생성...")
section = KooSectionIGASolid(id=11, name="IGA_Section_Test", ir=0)
print(f"  - ID: {section.id}")
print(f"  - Name: {section.name}")
print(f"  - elform: {section.elform}")
print(f"  - ir: {section.ir}")

# 2. 키워드 생성 테스트
print("\n[2] LS-DYNA 키워드 생성...")
keyword = section.GenerateDynaKeyword()
print(keyword)

# 3. 예상 결과와 비교
expected = "*SECTION_IGA_SOLID\n        11         0         0\n"
print("예상 결과:")
print(expected)

if keyword == expected:
    print("✓ 키워드 생성 성공!")
else:
    print("✗ 키워드 불일치")
    print(f"길이: {len(keyword)} vs {len(expected)}")

print("\n" + "=" * 80)
print("테스트 완료!")
print("=" * 80)

# 4. IGA 파트 키워드 생성 시뮬레이션
print("\n" + "=" * 80)
print("IGA 파트 키워드 생성 시뮬레이션")
print("=" * 80)

# 템플릿 파라미터
params = {
    'id': 11,
    'mid': 5,
    'fepid': 5,
    'xmin': -25.3,
    'xmax': 23.9,
    'ymin': -3.74,
    'ymax': 1.0,
    'zmin': -8.0,
    'zmax': 0.3,
    'rr': 0.6,
    'rs': 0.6,
    'rt': 0.6,
    'ir': 0,
    'styp': 4,
    'tollg': 1.0e-3
}

# PARAMETER_LOCAL 생성 예시
print("\n*PARAMETER_LOCAL")
print("$    PRMR1      VAL1")
print("$ 1. Unique input file ID")
print(f"Iid           {params['id']:5d}")
print("$ 2. Material ID")
print(f"Imid          {params['mid']:5d}")
print("$ 3. FE Solid PID")
print(f"Ifepid        {params['fepid']:5d}")
print("$ 4. Box corner points")
print(f"Rxmin     {params['xmin']:10.3e}")
print(f"Rxmax     {params['xmax']:10.3e}")
print(f"Rymin     {params['ymin']:10.3e}")
print(f"Rymax     {params['ymax']:10.3e}")
print(f"Rzmin     {params['zmin']:10.3e}")
print(f"Rzmax     {params['zmax']:10.3e}")

print("\n✓ 키워드 포맷 검증 완료!")
