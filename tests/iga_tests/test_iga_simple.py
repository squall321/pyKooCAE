#!/usr/bin/env python3
"""
IGA Part 모듈 간단 테스트
"""

import sys
import os

# 현재 디렉토리 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'occProject', 'Generators'))

# IGA 모듈 import 테스트
try:
    from KooCAEManager.KooIGAPart import KooIGAPart, DEFAULT_OPTIONS
    print("✓ KooIGAPart 모듈 import 성공")
    print(f"\n디폴트 옵션:")
    for key, value in DEFAULT_OPTIONS.items():
        print(f"  {key}: {value}")

except Exception as e:
    print(f"✗ KooIGAPart import 실패: {e}")
    import traceback
    traceback.print_exc()

# Section 모듈 테스트
try:
    from KooCAEManager.KooSection import KooSectionIGASolid, KooSectionManager
    print("\n✓ KooSectionIGASolid 모듈 import 성공")

    # Section Manager 테스트
    secManager = KooSectionManager()
    iga_section = secManager.CreateIGASection("TestSection", ir=1)
    print(f"  - 생성된 Section ID: {iga_section.id}")
    print(f"  - Section elform: {iga_section.elform}")
    print(f"  - Section ir: {iga_section.ir}")

    # 키워드 생성 테스트
    keyword = iga_section.GenerateDynaKeyword()
    print(f"\n생성된 키워드:\n{keyword}")

except Exception as e:
    print(f"✗ KooSection import/테스트 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("모듈 테스트 완료!")
print("=" * 60)
