#!/usr/bin/env python3
"""
IGA Part Generator 사용 예제
"""

import sys
sys.path.append('occProject/Generators')

from KooCAEManager.KooPart import KooPartManager
from KooCAEManager.KooMaterial import KooMaterialManager, KooMaterialElastic
from KooCAEManager.KooSection import KooSectionManager, KooSectionSolid
from KooCAEManager.KooNode import NodeManager, Node
from KooCAEManager.KooElement import ElementManager, ElementSolid


def create_simple_box_part():
    """간단한 박스 파트 생성 (테스트용)"""

    # 1. Manager 생성
    nodeManager = NodeManager()
    elementManager = ElementManager(nodeManager)
    partManager = KooPartManager(nodeManager, elementManager)
    materialManager = KooMaterialManager()
    sectionManager = KooSectionManager()

    # 2. Material 생성
    material = KooMaterialElastic(id=1, name="Steel", rho=7850, E=2.1e11, nu=0.3)
    materialManager.AddMaterial(material)

    # 3. Section 생성
    section = sectionManager.CreateSolidSection(name="SolidSection", elform=1)

    # 4. 노드 생성 (간단한 박스 8개 노드)
    nodes = [
        Node(1, [-1.0, -1.0, -1.0]),
        Node(2, [1.0, -1.0, -1.0]),
        Node(3, [1.0, 1.0, -1.0]),
        Node(4, [-1.0, 1.0, -1.0]),
        Node(5, [-1.0, -1.0, 1.0]),
        Node(6, [1.0, -1.0, 1.0]),
        Node(7, [1.0, 1.0, 1.0]),
        Node(8, [-1.0, 1.0, 1.0])
    ]

    for node in nodes:
        nodeManager.AddNode(node)

    # 5. 요소 생성 (Hex8)
    element = ElementSolid(id=1, nids=[1, 2, 3, 4, 5, 6, 7, 8], elform=1)
    elementManager.AddElement(element)

    # 6. Part 생성
    from KooCAEManager.KooPart import KooPart
    part = KooPart(id=5, name="BoxPart")
    part.mid = material.id
    part.secid = section.id
    part.nodeManager = nodeManager
    part.elementManager = elementManager

    partManager.parts[part.id] = part
    partManager.maxID = part.id

    return partManager, materialManager, sectionManager


def test_iga_part_creation():
    """IGA 파트 생성 테스트"""

    print("=" * 80)
    print("IGA Part Generator 테스트")
    print("=" * 80)

    # 1. 기본 FEM 모델 생성
    print("\n[1] 기본 FEM 모델 생성...")
    partManager, materialManager, sectionManager = create_simple_box_part()
    print(f"   - Parts: {list(partManager.parts.keys())}")
    print(f"   - Materials: {list(materialManager.materials.keys())}")
    print(f"   - Sections: {list(sectionManager.sections.keys())}")

    # 2. IGA 파트 생성 (최소 옵션)
    print("\n[2] IGA 파트 생성 (디폴트 옵션)...")
    options = {
        'iga_id': 100,
        'output_file': 'iga_sld_box_Part1.k'
    }

    iga_part = partManager.CreateIGAPart(
        source_pid=5,
        materialManager=materialManager,
        sectionManager=sectionManager,
        options=options
    )

    print(f"   - IGA Part ID: {iga_part.pid}")
    print(f"   - Material ID: {iga_part.mid}")
    print(f"   - Section ID: {iga_part.secid}")
    print(f"   - Bounding Box: {iga_part.bbox}")
    print(f"   - Output File: {iga_part.output_file}")

    # 3. IGA 파트 파일 생성
    print("\n[3] IGA 파일 생성...")
    output_path = iga_part.WriteToFile()
    print(f"   - 생성된 파일: {output_path}")

    # 4. 메인 모델 파일 생성
    print("\n[4] 메인 모델 파일 생성...")
    with open('main_model_test.k', 'w') as f:
        f.write('*KEYWORD\n')
        f.write('$\n')
        f.write('$--- FEM Parts ---\n')
        f.write('$\n')

        # FEM 파트 출력
        partManager.WriteStreamDynaKeyword(f)

        f.write('$\n')
        f.write('$--- IGA Parts (via Include) ---\n')
        f.write('$\n')

        # IGA Include 출력
        partManager.WriteIGAIncludes(f)

        f.write('*END\n')

    print("   - 생성된 파일: main_model_test.k")

    # 5. 결과 확인
    print("\n[5] 생성된 파일 확인...")
    print("\n--- iga_sld_box_Part1.k (처음 30줄) ---")
    with open('iga_sld_box_Part1.k', 'r') as f:
        lines = f.readlines()[:30]
        for line in lines:
            print(line.rstrip())

    print("\n--- main_model_test.k ---")
    with open('main_model_test.k', 'r') as f:
        content = f.read()
        print(content)

    print("\n" + "=" * 80)
    print("테스트 완료!")
    print("=" * 80)


if __name__ == "__main__":
    test_iga_part_creation()
