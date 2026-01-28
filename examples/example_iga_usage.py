#!/usr/bin/env python3
"""
IGA Part Generator 사용 예제

사용 방법:
    이 파일을 프로젝트에서 import하여 사용하거나,
    직접 실행하여 예제를 확인할 수 있습니다.
"""

# === 예제 1: 최소 옵션으로 IGA 파트 생성 ===

def example_minimal_options(partManager, materialManager, sectionManager):
    """
    최소 옵션만 사용하여 IGA 파트 생성
    나머지는 디폴트 값 사용
    """
    iga_part = partManager.CreateIGAPart(
        source_pid=5,  # 원본 FEM Part ID
        materialManager=materialManager,
        sectionManager=sectionManager,
        options={
            'iga_id': 100,
            'output_file': 'iga_sld_box_Part1.k'
        }
    )

    # IGA 파일 생성
    iga_part.WriteToFile()

    return iga_part


# === 예제 2: 커스텀 옵션 사용 ===

def example_custom_options(partManager, materialManager, sectionManager):
    """
    세부 파라미터를 커스터마이징하여 IGA 파트 생성
    """
    options = {
        # 필수 파라미터
        'iga_id': 101,
        'output_file': 'iga_custom_part.k',

        # 요소 크기 조정 (더 세밀하게)
        'element_edge_length': {
            'rr': 0.4,
            'rs': 0.4,
            'rt': 0.3
        },

        # Full Gauss integration 사용
        'integration_rule': 1,

        # 안정화 파라미터 조정
        'stabilization': {
            'styp': 3,
            'tollg': 5.0e-4
        },

        # 바운딩박스 20% 확장
        'bbox_offset_ratio': 1.2,

        # NURBS 파라미터 (2차 다항식)
        'nurbs_params': {
            'nr': 3, 'ns': 3, 'nt': 2,
            'pr': 2, 'ps': 2, 'pt': 1
        },

        # Refinement 반복 횟수 증가
        'refine_params': {
            'itr': 3,
            'its': 3,
            'itt': 2
        }
    }

    iga_part = partManager.CreateIGAPart(
        source_pid=7,
        materialManager=materialManager,
        sectionManager=sectionManager,
        options=options
    )

    iga_part.WriteToFile()
    return iga_part


# === 예제 3: 수동 바운딩박스 설정 ===

def example_manual_bbox(partManager, materialManager, sectionManager):
    """
    자동 계산 대신 수동으로 바운딩박스 지정
    """
    options = {
        'iga_id': 102,
        'output_file': 'iga_manual_bbox.k',

        # 자동 bbox 비활성화
        'auto_bbox': False,

        # 수동 bbox 설정
        'manual_bbox': {
            'xmin': -30.0, 'xmax': 30.0,
            'ymin': -5.0, 'ymax': 5.0,
            'zmin': -10.0, 'zmax': 2.0
        }
    }

    iga_part = partManager.CreateIGAPart(
        source_pid=8,
        materialManager=materialManager,
        sectionManager=sectionManager,
        options=options
    )

    iga_part.WriteToFile()
    return iga_part


# === 예제 4: 배치 처리 (여러 파트 일괄 변환) ===

def example_batch_processing(partManager, materialManager, sectionManager):
    """
    여러 파트를 IGA로 일괄 변환
    """
    part_ids = [5, 7, 10, 12, 15]

    for i, pid in enumerate(part_ids):
        partManager.CreateIGAPartWithAutoID(
            source_pid=pid,
            materialManager=materialManager,
            sectionManager=sectionManager,
            options={
                'output_file': f'iga_part_{pid}.k',
                'element_edge_length': {'rr': 0.6, 'rs': 0.6, 'rt': 0.6}
            }
        )

    # 모든 IGA 파일 일괄 생성
    created_files = partManager.WriteAllIGAFiles(output_dir='./iga_parts')

    print(f"생성된 파일: {len(created_files)}개")
    for file in created_files:
        print(f"  - {file}")

    return created_files


# === 예제 5: 메인 모델 파일 생성 ===

def example_create_main_model(partManager, output_filename='main_model.k'):
    """
    FEM 파트 + IGA Include가 포함된 메인 모델 파일 생성
    """
    with open(output_filename, 'w') as f:
        f.write('*KEYWORD\n')
        f.write('$\n')
        f.write('$===============================================\n')
        f.write('$  FEM Parts\n')
        f.write('$===============================================\n')
        f.write('$\n')

        # 기존 FEM 파트들 출력
        partManager.WriteStreamDynaKeyword(f)

        f.write('$\n')
        f.write('$===============================================\n')
        f.write('$  IGA Parts (via Include)\n')
        f.write('$===============================================\n')
        f.write('$\n')

        # IGA Include 문 출력
        partManager.WriteIGAIncludes(f)

        f.write('*END\n')

    print(f"메인 모델 파일 생성: {output_filename}")


# === 예제 6: IGA 파트 검색 및 제거 ===

def example_manage_iga_parts(partManager):
    """
    IGA 파트 관리 (검색, 제거)
    """
    # 특정 원본 파트로부터 생성된 IGA 파트들 찾기
    iga_parts = partManager.GetIGAPartsBySourcePID(source_pid=5)
    print(f"Source Part 5로부터 생성된 IGA 파트: {len(iga_parts)}개")

    # IGA 파트 제거
    if len(iga_parts) > 0:
        partManager.RemoveIGAPart(iga_parts[0].pid)
        print(f"IGA Part {iga_parts[0].pid} 제거됨")


# === 전체 워크플로우 예제 ===

def complete_workflow_example():
    """
    전체 워크플로우 예제
    (실제 실행은 Manager들이 초기화된 후에 가능)
    """
    print("""
    전체 IGA 워크플로우:

    1. 기본 FEM 모델 구축
       - partManager, materialManager, sectionManager 생성
       - FEM 파트들 추가

    2. IGA 파트 생성
       iga_part = partManager.CreateIGAPart(
           source_pid=5,
           materialManager=materialManager,
           sectionManager=sectionManager,
           options={'iga_id': 100, 'output_file': 'iga_part.k'}
       )

    3. IGA 파일 생성
       iga_part.WriteToFile()

    4. 메인 모델 출력
       with open('main.k', 'w') as f:
           partManager.WriteStreamDynaKeyword(f)
           partManager.WriteIGAIncludes(f)

    생성되는 파일:
       - main.k              (FEM + *INCLUDE 문)
       - iga_part.k          (IGA 키워드)
    """)


# === 옵션 참조표 ===

def print_option_reference():
    """
    사용 가능한 모든 옵션 출력
    """
    print("""
    === IGA 파트 생성 옵션 참조 ===

    필수 옵션:
      - iga_id: int            # IGA Part ID (PID, VID, SID, PATCHID, RID)
      - output_file: str       # 출력 파일명

    요소 설정 (선택):
      - element_edge_length:
          rr: 0.6              # r-방향 (x) 요소 크기
          rs: 0.6              # s-방향 (y) 요소 크기
          rt: 0.6              # t-방향 (z) 요소 크기

      - integration_rule: 0    # 0=reduced Gauss, 1=Full Gauss

    안정화 (선택):
      - stabilization:
          styp: 4              # 안정화 타입
          tollg: 1.0e-3        # LCP threshold

    바운딩박스 (선택):
      - auto_bbox: True        # 자동 계산
      - bbox_offset_ratio: 1.1 # 확장 비율 (1.0=없음, 1.1=10%)

      - manual_bbox:           # 수동 설정 (auto_bbox=False일 때)
          xmin, xmax, ymin, ymax, zmin, zmax

    NURBS (선택):
      - nurbs_params:
          nr, ns, nt: 2, 2, 2  # knot 개수
          pr, ps, pt: 1, 1, 1  # 다항식 차수
          unir, unis, unit: 1  # uniform knot vector

    IGA_SOLID (선택):
      - iga_solid_params:
          nisr, niss, nist: 1, 1, 1

    Refinement (선택):
      - refine_params:
          rtyp: 2              # refinement type
          hrtyp: 2             # h-refinement type
          itr, its, itt: 2, 2, 2

    Volume (선택):
      - volume_params:
          tetmsh: -1           # 고정값
          esid, fsid: None
    """)


if __name__ == "__main__":
    print("=" * 80)
    print("IGA Part Generator 사용 예제")
    print("=" * 80)
    print()

    # 옵션 참조표 출력
    print_option_reference()

    print()
    print("=" * 80)

    # 워크플로우 설명
    complete_workflow_example()
