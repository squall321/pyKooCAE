#!/usr/bin/env python3
"""
실제 runid 디렉토리 구조 생성 스크립트

runner_config.json을 읽어서 실제 시뮬레이션이 사용할 디렉토리 구조를 생성합니다.
(시뮬레이션 실행 없이 디렉토리와 metadata.json만 생성)
"""

import json
import os
import sys
from pathlib import Path


def create_simulation_directories(runner_config_path: str, output_base: str):
    """
    runner_config.json을 기반으로 실제 시뮬레이션 디렉토리 생성

    Args:
        runner_config_path: runner_config.json 경로
        output_base: 출력 베이스 디렉토리 (예: /data/Test_001_Full26_1Step)
    """
    with open(runner_config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    project_name = config['project_name']
    output_dir = Path(output_base)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"================================================================================")
    print(f"실제 시뮬레이션 디렉토리 생성")
    print(f"================================================================================")
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
        print()

        # runid별로 디렉토리 생성
        created_count = 0
        for doe_idx in sorted(runids.keys()):
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

            # metadata.json 저장
            with open(runid_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            created_count += 1
            if created_count % 10 == 0:
                print(f"  생성 완료: {created_count}/{len(runids)} runids")

        print(f"  총 생성: {created_count} runids")
        print()
        print(f"✅ 디렉토리 생성 완료: {output_dir}")
        print()
        print(f"생성된 구조:")
        print(f"  {output_dir}/")
        print(f"    runid_00001/ ~ runid_{len(runids):05d}/")
        print(f"      metadata.json")
        print(f"      Step001/ ~ Step{total_steps:03d}/")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_directories.py <runner_config.json> <output_dir>")
        print()
        print("Example:")
        print("  python create_directories.py Test_001/runner_config.json /data/Test_001_Full26_1Step")
        sys.exit(1)

    runner_config = sys.argv[1]
    output_base = sys.argv[2]

    create_simulation_directories(runner_config, output_base)
