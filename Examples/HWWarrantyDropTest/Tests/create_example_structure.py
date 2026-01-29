#!/usr/bin/env python3
"""
시뮬레이션 디렉토리 구조 생성 예제

runner_config.json을 읽어서 실제로 생성될 runid 디렉토리 구조를
예시로 생성합니다 (실제 시뮬레이션 파일 없이 구조만).
"""

import json
import os
import sys
from pathlib import Path


def create_example_structure(runner_config_path: str, output_base: str, max_runids: int = 3):
    """
    runner_config.json을 기반으로 예제 디렉토리 구조 생성

    Args:
        runner_config_path: runner_config.json 경로
        output_base: 출력 베이스 디렉토리 (예: /data/Test_001_Full26_1Step)
        max_runids: 생성할 최대 runid 개수 (전체 구조 확인용)
    """
    with open(runner_config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    project_name = config['project_name']
    output_dir = Path(output_base)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"프로젝트: {project_name}")
    print(f"출력 디렉토리: {output_dir}")
    print()

    # 시나리오별로 처리
    for scenario in config['scenarios']:
        scenario_name = scenario['scenario_name']
        total_steps = scenario['total_steps']

        print(f"시나리오: {scenario_name}")
        print(f"총 Step 수: {total_steps}")
        print()

        # doe_index별로 그룹화 (각 runid)
        runids = {}
        for step in scenario['steps']:
            doe_idx = step['doe_index']
            if doe_idx not in runids:
                runids[doe_idx] = []
            runids[doe_idx].append(step)

        print(f"총 runid 개수: {len(runids)}")
        print(f"예제로 생성할 runid 개수: {min(max_runids, len(runids))}")
        print()

        # runid별로 디렉토리 생성
        created_runids = []
        for doe_idx in sorted(runids.keys())[:max_runids]:
            runid_name = f"runid_{doe_idx+1:05d}"
            runid_dir = output_dir / runid_name
            runid_dir.mkdir(parents=True, exist_ok=True)

            steps = sorted(runids[doe_idx], key=lambda x: x['step_number'])

            # metadata.json 생성
            first_step = steps[0]
            angle_info = first_step['angle']

            metadata = {
                "runid": runid_name,
                "doe_index": doe_idx,
                "scenario_name": scenario_name,
                "total_steps": len(steps),
                "base_angle": {
                    "name": angle_info['name'],
                    "roll": angle_info['roll'],
                    "pitch": angle_info['pitch'],
                    "yaw": angle_info['yaw']
                },
                "steps": []
            }

            # 각 Step 디렉토리 생성
            for step in steps:
                step_num = step['step_number']
                step_dir = runid_dir / f"Step{step_num:03d}"
                step_dir.mkdir(parents=True, exist_ok=True)

                angle = step['angle']
                step_info = {
                    "step_number": step_num,
                    "mode": step['mode'],
                    "template": step['template'],
                    "angle": {
                        "name": angle['name'],
                        "roll": angle['roll'],
                        "pitch": angle['pitch'],
                        "yaw": angle['yaw']
                    },
                    "input_file": step['input_file'],
                    "dynain_source": step.get('dynain_source')
                }
                metadata['steps'].append(step_info)

                # Step 디렉토리에 README.txt 생성
                readme_content = f"""Step {step_num} - {angle['name']}

Mode: {step['mode']}
Template: {step['template']}

각도:
  Roll:  {angle['roll']:7.1f}°
  Pitch: {angle['pitch']:7.1f}°
  Yaw:   {angle['yaw']:7.1f}°

입력 파일: {step['input_file']}
"""
                if step.get('dynain_source'):
                    readme_content += f"DYNAIN 소스: {step['dynain_source']}\n"

                with open(step_dir / "README.txt", 'w', encoding='utf-8') as f:
                    f.write(readme_content)

            # metadata.json 저장
            with open(runid_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            created_runids.append({
                'runid': runid_name,
                'angle_name': angle_info['name'],
                'steps': len(steps)
            })

        # 생성된 구조 출력
        print("생성된 디렉토리 구조:")
        print(f"{output_dir}/")
        for item in created_runids:
            print(f"  {item['runid']}/  ({item['angle_name']}, {item['steps']} steps)")
            for step_num in range(1, item['steps'] + 1):
                print(f"    Step{step_num:03d}/")
                print(f"      README.txt")
            print(f"    metadata.json")

        print()
        print(f"✅ 예제 구조 생성 완료: {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_example_structure.py <runner_config.json> <output_dir> [max_runids]")
        print()
        print("Example:")
        print("  python create_example_structure.py Test_001/runner_config.json /tmp/example_Test_001 3")
        sys.exit(1)

    runner_config = sys.argv[1]
    output_base = sys.argv[2]
    max_runids = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    create_example_structure(runner_config, output_base, max_runids)
