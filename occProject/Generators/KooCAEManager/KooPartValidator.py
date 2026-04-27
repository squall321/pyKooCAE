"""
KooPartValidator — 파트별 낙하 검증용 분할/실행/수집 모듈

Phase 1: Split + Simulate
- 원본 모델을 파트별 개별 .k 파일로 분할
- 각 파트에 바닥판 + 0도 낙하 조건 자동 추가
- validation_manifest.json 생성
- DOE array job으로 병렬 실행
"""

import os
import json
import math
import numpy as np
from io import StringIO


def split_parts_for_validation(dynaImporter, output_dir, option=None):
    """원본 모델을 파트별 개별 .k 파일로 분할하여 낙하 검증용 모델 생성.

    Args:
        dynaImporter: KooMeshImporter (원본 모델)
        output_dir: 출력 디렉토리
        option: 옵션 dict
            - height: 낙하 높이 (mm, 기본 100)
            - tFinal: 종료 시간 (기본 0.0005)
            - dt: 출력 간격 (기본 0.00001)
            - floor_size: 바닥판 크기 [x, y, z] (기본 자동)
            - except_pids: 제외할 PID 리스트
            - min_elements: 이 개수 미만 파트는 skip (기본 1)

    Returns:
        manifest: dict (validation_manifest.json 내용)
    """
    from KooCAEManager.KooElement import FaceElement, SolidElement

    if option is None:
        option = {}

    height = option.get("height", 100.0)
    tFinal = option.get("tFinal", 0.0005)
    dt_output = option.get("dt", 0.00001)
    except_pids = set(option.get("except_pids", []))
    min_elements = option.get("min_elements", 1)

    os.makedirs(output_dir, exist_ok=True)

    partManager = dynaImporter.partManager
    nodeManager = dynaImporter.nodeManager
    matManager = dynaImporter.matManager
    sectionManager = dynaImporter.sectionManager
    contactManager = dynaImporter.contactManager

    # Tied 접촉 정보 수집
    tied_contacts = []
    for cid, contact in contactManager.contacts.items():
        ctype = type(contact).__name__
        if 'Tied' in ctype:
            tied_contacts.append({
                "cid": cid,
                "type": ctype,
                "ssid": contact.SSID,
                "msid": contact.MSID,
                "sstyp": contact.SSTYP,
                "mstyp": contact.MSTYP,
            })

    # 파트별 분할
    manifest = {
        "source": "",
        "output_dir": output_dir,
        "height": height,
        "tFinal": tFinal,
        "parts": {},
        "tied_contacts": tied_contacts,
        "results": {},
    }

    total_parts = 0
    skipped_parts = 0

    for pid, part in partManager.parts.items():
        if pid in except_pids:
            skipped_parts += 1
            continue

        elemMan = part.elementManager
        if not elemMan.elements or len(elemMan.elements) < min_elements:
            skipped_parts += 1
            continue

        # 재료 확인 — 강체면 skip
        mat = part.material
        if mat is None:
            skipped_parts += 1
            continue
        mat_name = getattr(mat, 'name', '')
        if 'RIGID' in str(mat_name).upper():
            skipped_parts += 1
            continue

        # 파트 바운딩 박스
        part_nodes = set()
        for eid, elem in elemMan.elements.items():
            for n in elem.nodes:
                if n is not None:
                    part_nodes.add(n)

        if len(part_nodes) < 3:
            skipped_parts += 1
            continue

        coords = np.array([[n.x, n.y, n.z] for n in part_nodes])
        bbox_min = coords.min(axis=0)
        bbox_max = coords.max(axis=0)
        bbox_size = bbox_max - bbox_min
        bbox_center = (bbox_min + bbox_max) / 2.0

        # 파트 파일 생성
        part_filename = f"Part_{pid:06d}.k"
        part_filepath = os.path.join(output_dir, part_filename)

        # 노드 ID 수집
        node_ids = sorted([n.id for n in part_nodes])

        # 바닥판 크기: 파트 바운딩 박스의 2배
        floor_x = max(bbox_size[0] * 2, 10.0)
        floor_y = max(bbox_size[1] * 2, 10.0)
        floor_z = 1.0  # 얇은 바닥판

        # 개별 .k 파일 작성
        _write_single_part_model(
            part, mat, nodeManager, matManager, sectionManager,
            part_filepath, part_nodes, node_ids,
            height, tFinal, dt_output,
            floor_x, floor_y, floor_z,
            bbox_center, bbox_min, pid
        )

        # manifest 기록
        manifest["parts"][str(pid)] = {
            "file": part_filename,
            "name": part.name if hasattr(part, 'name') else f"Part_{pid}",
            "num_elements": len(elemMan.elements),
            "num_nodes": len(part_nodes),
            "bbox_min": bbox_min.tolist(),
            "bbox_max": bbox_max.tolist(),
            "node_id_range": [min(node_ids), max(node_ids)],
        }
        total_parts += 1

    # manifest 저장
    manifest_path = os.path.join(output_dir, "validation_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"PartValidationSplit: {total_parts} 파트 분할 완료, {skipped_parts} 파트 skip")
    print(f"  출력: {output_dir}")
    print(f"  manifest: {manifest_path}")

    # scenario.json 생성
    scenario = _generate_validation_scenario(manifest, output_dir, option)
    scenario_path = os.path.join(output_dir, "scenario.json")
    with open(scenario_path, 'w') as f:
        json.dump(scenario, f, indent=2, ensure_ascii=False)
    print(f"  scenario: {scenario_path}")

    # run.sh 생성
    run_sh_path = os.path.join(output_dir, "run.sh")
    _generate_run_sh(run_sh_path, output_dir, total_parts, option)
    print(f"  run.sh: {run_sh_path}")

    return manifest


def _generate_validation_scenario(manifest, output_dir, option):
    """파트별 검증용 scenario.json 생성."""
    height = manifest.get("height", 100.0)
    tFinal = manifest.get("tFinal", 0.0005)
    env = option.get("environment", {})

    parts_list = []
    for pid_str, pinfo in manifest["parts"].items():
        parts_list.append({
            "pid": int(pid_str),
            "file": pinfo["file"],
            "name": pinfo.get("name", f"Part_{pid_str}"),
        })

    scenario = {
        "project_name": "PartValidation",
        "description": "파트별 낙하 검증 시뮬레이션",
        "base_dir": output_dir,
        "mode": "part_validation",
        "environment": env if env else {
            "solver_path": "/data/SmartTwinPreprocessor/bin/KooMeshModifier",
            "sif_path": "",
            "ncpu": 4,
            "memory": "4G",
        },
        "simulation_params": {
            "height": height,
            "tFinal": tFinal,
        },
        "parts": parts_list,
        "total_cases": len(parts_list),
    }
    return scenario


def _generate_run_sh(run_sh_path, output_dir, total_parts, option):
    """Slurm array job용 run.sh 생성."""
    env = option.get("environment", {})
    ncpu = env.get("ncpu", 4)
    memory = env.get("memory", "4G")
    partition = env.get("partition", "normal")
    sif_path = env.get("sif_path", "")
    solver_cmd = env.get("solver_command", "ls-dyna")

    script = f"""#!/bin/bash
#SBATCH --job-name=PartValidation
#SBATCH --array=1-{total_parts}
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={ncpu}
#SBATCH --mem={memory}
#SBATCH --partition={partition}
#SBATCH --output={output_dir}/logs/slurm_%A_%a.out
#SBATCH --error={output_dir}/logs/slurm_%A_%a.err

# 로그 디렉토리 생성
mkdir -p {output_dir}/logs
mkdir -p {output_dir}/results

# 파트 리스트에서 현재 array index에 해당하는 .k 파일 가져오기
PART_FILES=($(ls {output_dir}/Part_*.k | sort))
IDX=$((SLURM_ARRAY_TASK_ID - 1))
KFILE=${{PART_FILES[$IDX]}}
BASENAME=$(basename "$KFILE" .k)

echo "=== PartValidation: $BASENAME ==="
echo "  Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "  Input: $KFILE"

# 작업 디렉토리 생성
WORKDIR={output_dir}/results/$BASENAME
mkdir -p $WORKDIR
cp $KFILE $WORKDIR/

cd $WORKDIR

# LS-DYNA 실행
"""

    if sif_path:
        script += f"""apptainer exec {sif_path} {solver_cmd} i=$(basename $KFILE) ncpu={ncpu} memory={memory}
"""
    else:
        script += f"""{solver_cmd} i=$(basename $KFILE) ncpu={ncpu} memory={memory}
"""

    script += f"""
EXIT_CODE=$?

# 결과 기록
if [ $EXIT_CODE -eq 0 ]; then
    echo "PASS" > $WORKDIR/status.txt
else
    echo "FAIL (exit=$EXIT_CODE)" > $WORKDIR/status.txt
fi

echo "=== Done: $BASENAME (exit=$EXIT_CODE) ==="
"""

    with open(run_sh_path, 'w') as f:
        f.write(script)
    os.chmod(run_sh_path, 0o755)


def _write_single_part_model(
    part, mat, globalNodeManager, matManager, sectionManager,
    filepath, part_nodes, node_ids,
    height, tFinal, dt_output,
    floor_x, floor_y, floor_z,
    bbox_center, bbox_min, pid
):
    """단일 파트 낙하 검증 모델 .k 파일 작성."""
    from KooCAEManager.KooElement import FaceElement

    stream = StringIO()

    stream.write("*KEYWORD\n")
    stream.write(f"*TITLE\nPartValidation_PID{pid}\n")

    # CONTROL cards
    stream.write("*CONTROL_TERMINATION\n")
    stream.write(f"{tFinal:>10.4E}{'0':>10}{'1.0E-10':>10}{'0.0':>10}{'1.0E+07':>10}{'0':>10}\n")

    stream.write("*CONTROL_TIMESTEP\n")
    stream.write(f"{'0.0':>10}{'0.67':>10}{'0':>10}{'0.0':>10}{'0.0':>10}{'0':>10}{'1':>10}{'0':>10}\n")

    stream.write("*CONTROL_HOURGLASS\n")
    stream.write(f"{'5':>10}{'0.1':>10}\n")

    stream.write("*CONTROL_BULK_VISCOSITY\n")
    stream.write(f"{'1.5':>10}{'0.06':>10}{'1':>10}{'0':>10}{'0':>10}\n")

    stream.write("*CONTROL_CONTACT\n")
    stream.write(f"{'0':>10}{'0.0':>10}{'2':>10}{'0':>10}{'1':>10}\n")

    stream.write("*CONTROL_ENERGY\n")
    stream.write(f"{'2':>10}{'2':>10}{'2':>10}{'2':>10}\n")

    # DATABASE
    stream.write(f"*DATABASE_GLSTAT\n{dt_output:>10.4E}\n")
    stream.write(f"*DATABASE_MATSUM\n{dt_output:>10.4E}\n")
    stream.write(f"*DATABASE_RCFORC\n{dt_output:>10.4E}\n")
    stream.write(f"*DATABASE_BINARY_D3PLOT\n{dt_output:>10.4E}\n")

    # 재료 + 섹션 출력
    if mat.dynaKeywordString:
        stream.write(mat.dynaKeywordString)
        if not mat.dynaKeywordString.endswith('\n'):
            stream.write('\n')
    if hasattr(part, 'section') and part.section is not None:
        part.section.WriteStreamDynaKeyword(stream)

    # 바닥판 재료 + 섹션
    # 바닥판 ID: 원본과 충돌 방지 — 고유하게 생성
    floor_id_base = 99000000 + pid
    floor_mid = floor_id_base
    floor_sid = floor_id_base
    floor_pid_val = floor_id_base

    stream.write("*MAT_ELASTIC_TITLE\n")
    stream.write(f"{'Floor_Elastic':>80}\n")
    stream.write(f"{floor_mid:>10}{'7.85E-09':>10}{'2.0E+05':>10}{'0.3':>10}\n")

    # Shell section for floor
    stream.write("*SECTION_SHELL_TITLE\n")
    stream.write(f"{'Floor_Section':>80}\n")
    stream.write(f"{floor_sid:>10}{'-16':>10}{'0.0':>10}{'3':>10}{'0.0':>10}{'0':>10}{'0':>10}{'1':>10}\n")
    stream.write(f"{floor_z:>10.3f}{floor_z:>10.3f}{floor_z:>10.3f}{floor_z:>10.3f}\n")

    # 파트 정의
    part_mid = mat.id
    part_sid = part.section.id if hasattr(part, 'section') and part.section is not None else 1
    stream.write(f"*PART\n")
    stream.write(f"{'Part_' + str(pid):>80}\n")
    stream.write(f"{pid:>10}{part_sid:>10}{part_mid:>10}\n")

    # 바닥판 파트
    stream.write(f"*PART\n")
    stream.write(f"{'Floor':>80}\n")
    stream.write(f"{floor_pid_val:>10}{floor_sid:>10}{floor_mid:>10}\n")

    # 노드 출력
    stream.write("*NODE\n")
    for n in part_nodes:
        stream.write(f"{n.id:>8}{n.x:>16.6f}{n.y:>16.6f}{n.z:>16.6f}{'0':>8}{'0':>8}\n")

    # 요소 출력
    first_elem = next(iter(part.elementManager.elements.values()))
    if isinstance(first_elem, FaceElement):
        # Shell
        etype = first_elem.type
        if etype in ("TRI3",):
            stream.write("*ELEMENT_SHELL\n")
            for eid, elem in part.elementManager.elements.items():
                nids = [n.id for n in elem.nodes if n is not None]
                if len(nids) == 3:
                    stream.write(f"{eid:>8}{pid:>8}{nids[0]:>8}{nids[1]:>8}{nids[2]:>8}{nids[2]:>8}\n")
                elif len(nids) >= 4:
                    stream.write(f"{eid:>8}{pid:>8}{nids[0]:>8}{nids[1]:>8}{nids[2]:>8}{nids[3]:>8}\n")
        else:
            stream.write("*ELEMENT_SHELL\n")
            for eid, elem in part.elementManager.elements.items():
                nids = [n.id for n in elem.nodes if n is not None]
                if len(nids) >= 4:
                    stream.write(f"{eid:>8}{pid:>8}{nids[0]:>8}{nids[1]:>8}{nids[2]:>8}{nids[3]:>8}\n")
                elif len(nids) == 3:
                    stream.write(f"{eid:>8}{pid:>8}{nids[0]:>8}{nids[1]:>8}{nids[2]:>8}{nids[2]:>8}\n")
    else:
        # Solid
        etype = first_elem.type
        if etype in ("TETRA4", "TETRA10"):
            stream.write("*ELEMENT_SOLID\n")
            for eid, elem in part.elementManager.elements.items():
                nids = [n.id for n in elem.nodes if n is not None]
                if len(nids) == 4:
                    stream.write(f"{eid:>8}{pid:>8}{nids[0]:>8}{nids[1]:>8}{nids[2]:>8}{nids[3]:>8}{nids[3]:>8}{nids[3]:>8}{nids[3]:>8}{nids[3]:>8}\n")
                elif len(nids) == 6:
                    stream.write(f"{eid:>8}{pid:>8}{nids[0]:>8}{nids[1]:>8}{nids[2]:>8}{nids[3]:>8}{nids[4]:>8}{nids[5]:>8}{nids[5]:>8}{nids[5]:>8}\n")
                elif len(nids) >= 8:
                    stream.write(f"{eid:>8}{pid:>8}{nids[0]:>8}{nids[1]:>8}{nids[2]:>8}{nids[3]:>8}{nids[4]:>8}{nids[5]:>8}{nids[6]:>8}{nids[7]:>8}\n")
        else:
            stream.write("*ELEMENT_SOLID\n")
            for eid, elem in part.elementManager.elements.items():
                nids = [n.id for n in elem.nodes if n is not None]
                while len(nids) < 8:
                    nids.append(nids[-1])
                stream.write(f"{eid:>8}{pid:>8}{nids[0]:>8}{nids[1]:>8}{nids[2]:>8}{nids[3]:>8}{nids[4]:>8}{nids[5]:>8}{nids[6]:>8}{nids[7]:>8}\n")

    # 바닥판 메시 생성 (간단한 quad 메시)
    floor_center_x = bbox_center[0]
    floor_center_y = bbox_center[1]
    floor_z_pos = bbox_min[2] - height  # 바닥판 위치: 파트 하단에서 높이만큼 아래

    # 바닥판 노드/요소 ID 오프셋
    floor_nid_start = max(node_ids) + 1000
    floor_eid_start = max(part.elementManager.elements.keys()) + 1000

    nx, ny = 10, 10  # 바닥판 메시 밀도
    dx = floor_x / nx
    dy = floor_y / ny

    # 바닥판 노드
    floor_node_ids = {}
    nid = floor_nid_start
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = floor_center_x - floor_x / 2 + i * dx
            y = floor_center_y - floor_y / 2 + j * dy
            z = floor_z_pos
            stream.write(f"{nid:>8}{x:>16.6f}{y:>16.6f}{z:>16.6f}{'0':>8}{'0':>8}\n")
            floor_node_ids[(i, j)] = nid
            nid += 1

    # 바닥판 요소
    stream.write("*ELEMENT_SHELL\n")
    eid = floor_eid_start
    for j in range(ny):
        for i in range(nx):
            n1 = floor_node_ids[(i, j)]
            n2 = floor_node_ids[(i + 1, j)]
            n3 = floor_node_ids[(i + 1, j + 1)]
            n4 = floor_node_ids[(i, j + 1)]
            stream.write(f"{eid:>8}{floor_pid_val:>8}{n1:>8}{n2:>8}{n3:>8}{n4:>8}\n")
            eid += 1

    # 바닥판 SPC 구속
    stream.write("*BOUNDARY_SPC_SET\n")
    floor_nsid = floor_pid_val  # 노드셋 ID = 파트 ID 재활용
    stream.write(f"{floor_nsid:>10}{'0':>10}{'1':>10}{'1':>10}{'1':>10}{'1':>10}{'1':>10}{'1':>10}\n")
    stream.write(f"*SET_NODE_LIST_TITLE\n{'Floor_Nodes':>80}\n")
    stream.write(f"{floor_nsid:>10}\n")
    count = 0
    for nid_val in floor_node_ids.values():
        stream.write(f"{nid_val:>10}")
        count += 1
        if count % 8 == 0:
            stream.write("\n")
    if count % 8 != 0:
        stream.write("\n")

    # 초기속도 (0도 자유낙하: Z방향 속도)
    g = 9810.0  # mm/s^2
    vz = -math.sqrt(2.0 * g * height)  # 자유낙하 속도

    # 파트 노드셋
    part_nsid = pid
    stream.write(f"*SET_NODE_LIST_TITLE\n{'Part_Nodes':>80}\n")
    stream.write(f"{part_nsid:>10}\n")
    count = 0
    for nid_val in node_ids:
        stream.write(f"{nid_val:>10}")
        count += 1
        if count % 8 == 0:
            stream.write("\n")
    if count % 8 != 0:
        stream.write("\n")

    stream.write("*INITIAL_VELOCITY\n")
    stream.write(f"{part_nsid:>10}{'0':>10}{'0':>10}{'0':>10}{'0':>10}\n")
    stream.write(f"{'0.0':>10}{'0.0':>10}{vz:>10.2f}{'0.0':>10}{'0.0':>10}{'0.0':>10}\n")
    stream.write(f"{'0.0':>10}{'0.0':>10}{'0.0':>10}{'0.0':>10}{'0.0':>10}{'0.0':>10}\n")

    # 접촉: AUTOMATIC_SURFACE_TO_SURFACE
    stream.write("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE\n")
    stream.write(f"{'':>80}\n")  # title
    stream.write(f"{part_nsid:>10}{floor_pid_val:>10}{'4':>10}{'3':>10}{'0':>10}{'0':>10}{'0':>10}{'0':>10}\n")
    stream.write(f"{'0.3':>10}{'0.2':>10}{'0.0':>10}{'0.0':>10}{'10.0':>10}{'0':>10}{'0.0':>10}{'1.0E+20':>10}\n")
    stream.write(f"{'1.0':>10}{'1.0':>10}{'0.0':>10}{'0.0':>10}{'1.0':>10}{'1.0':>10}{'1.0':>10}{'1.0':>10}\n")
    # OptCardA: SOFT=2
    stream.write(f"{'2':>10}{'0.1':>10}{'0':>10}{'1.025':>10}{'3':>10}{'35':>10}{'100':>10}{'1':>10}\n")

    # 중력
    stream.write("*LOAD_BODY_Z\n")
    stream.write(f"{'0':>10}{g:>10.1f}\n")

    stream.write("*END\n")

    # 파일 쓰기
    with open(filepath, 'w') as f:
        f.write(stream.getvalue())

    print(f"  PID {pid}: {filepath} ({len(part.elementManager.elements)} elements, {len(part_nodes)} nodes)")
