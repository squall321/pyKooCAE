#!/usr/bin/env python3
"""
Simplified Cumulative Scenario Executor (Stage 2: Executor)

runner_config.json을 읽고 시뮬레이션을 순차 실행합니다.

Usage:
    python SimplifiedExecutor.py runner_config.json [--scenario=ID] [--dry-run]

Author: koo.park
Email: koo.park@samsung.com
Group: CAE
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List
from pathlib import Path



class SimplifiedExecutor:
    """간소화된 누적 시뮬레이션 Executor"""

    def __init__(self, runner_config_path: str):
        """
        Parameters:
            runner_config_path: runner_config.json 경로
        """
        with open(runner_config_path, 'r', encoding='utf-8') as f:
            self.runner_config = json.load(f)

        self.project_name = self.runner_config.get("project_name", "Project")
        self.base_dir = self.runner_config.get("base_dir", os.getcwd())
        self.environment = self.runner_config.get("environment", {})
        self.scenarios = self.runner_config.get("scenarios", [])

    def run_all_scenarios(self, dry_run: bool = False):
        """모든 시나리오 실행"""
        print(f"\n{'='*100}")
        print(f"🚀 Cumulative Scenario Executor - {self.project_name}")
        print(f"{'='*100}\n")

        total_scenarios = len(self.scenarios)
        print(f"총 시나리오 수: {total_scenarios}\n")

        for i, scenario in enumerate(self.scenarios, start=1):
            print(f"\n{'─'*100}")
            print(f"[{i}/{total_scenarios}] 시나리오: {scenario['scenario_name']} ({scenario['scenario_id']})")
            print(f"{'─'*100}")

            self.run_scenario(scenario, dry_run)

        print(f"\n{'='*100}")
        print(f"✅ 모든 시나리오 실행 완료!")
        print(f"{'='*100}\n")

    def run_scenario(self, scenario: Dict[str, Any], dry_run: bool = False):
        """개별 시나리오 실행"""
        scenario_id = scenario.get("scenario_id")
        scenario_name = scenario.get("scenario_name")
        total_steps = scenario.get("total_steps")
        steps = scenario.get("steps", [])

        print(f"총 Step 수: {total_steps}")

        for step_cfg in steps:
            self.run_step(scenario_id, step_cfg, dry_run)

    def run_step(self, scenario_id: str, step_cfg: Dict[str, Any], dry_run: bool = False):
        """개별 Step 실행"""
        step_number = step_cfg.get("step_number")
        template = step_cfg.get("template")
        mode = step_cfg.get("mode")
        angle = step_cfg.get("angle", {})
        input_file = step_cfg.get("input_file")
        output_dir = step_cfg.get("output_dir")
        dynain_source = step_cfg.get("dynain_source")
        doe_index = step_cfg.get("doe_index", 0)

        print(f"\n  ┌─ Step {step_number} ─────────────────────────────────────────────────")
        print(f"  │ Template: {template}")
        print(f"  │ Mode: {mode}")
        print(f"  │ Angle: {angle['name']} (Roll={angle['roll']:.2f}, Pitch={angle['pitch']:.2f}, Yaw={angle['yaw']:.2f})")
        print(f"  │ Input: {input_file}")
        print(f"  │ Output: {output_dir}")
        if dynain_source:
            print(f"  │ Dynain Source: {dynain_source}")
        if doe_index > 0:
            print(f"  │ DOE Index: {doe_index}")
        print(f"  └───────────────────────────────────────────────────────────────────────")

        if dry_run:
            print(f"  [DRY-RUN] Step {step_number} 시뮬레이션 스킵")
            return

        # 실제 실행 로직 (추후 구현)
        # 1. KooMeshModifier 호출
        # 2. 템플릿에 따라 DROP_ATTITUDE, DYNAIN_TO_INITIAL, THERMAL_CYCLE 실행
        # 3. LS-DYNA 실행
        # 4. dynain 파일 생성 대기
        print(f"  ⚠️  실제 실행 로직은 KooMeshModifier 연동 필요 (추후 구현)")

    def run_single_scenario(self, scenario_id: str, dry_run: bool = False):
        """특정 시나리오만 실행"""
        scenario = None
        for s in self.scenarios:
            if s.get("scenario_id") == scenario_id:
                scenario = s
                break

        if scenario is None:
            print(f"❌ 시나리오를 찾을 수 없습니다: {scenario_id}")
            return

        print(f"\n{'='*100}")
        print(f"🚀 Cumulative Scenario Executor - {self.project_name}")
        print(f"{'='*100}\n")

        self.run_scenario(scenario, dry_run)

        print(f"\n{'='*100}")
        print(f"✅ 시나리오 실행 완료: {scenario_id}")
        print(f"{'='*100}\n")

    def print_summary(self):
        """실행 전 요약 출력"""
        print(f"\n{'='*100}")
        print(f"📋 실행 계획 요약")
        print(f"{'='*100}")
        print(f"프로젝트: {self.project_name}")
        print(f"작업 디렉토리: {self.base_dir}")
        print(f"총 시나리오 수: {len(self.scenarios)}\n")

        for i, scenario in enumerate(self.scenarios, start=1):
            print(f"[{i}] {scenario['scenario_name']} ({scenario['scenario_id']})")
            print(f"    총 Step 수: {scenario['total_steps']}")

            for step in scenario['steps']:
                angle = step['angle']
                print(f"      Step {step['step_number']}: {step['template']:<25} {step['mode']:<10} "
                      f"{angle['name']:<20} Roll={angle['roll']:>7.2f} Pitch={angle['pitch']:>7.2f}")

            print()

        print(f"{'='*100}\n")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Simplified Cumulative Scenario Executor")
    parser.add_argument("runner_config", help="runner_config.json 경로")
    parser.add_argument("--scenario", help="특정 시나리오 ID만 실행 (선택사항)")
    parser.add_argument("--dry-run", action="store_true", help="실제 실행 없이 계획만 출력")
    parser.add_argument("--summary", action="store_true", help="실행 계획 요약만 출력")
    args = parser.parse_args()

    # Executor 생성
    executor = SimplifiedExecutor(args.runner_config)

    # 요약만 출력
    if args.summary:
        executor.print_summary()
        return

    # 실행
    if args.scenario:
        executor.run_single_scenario(args.scenario, dry_run=args.dry_run)
    else:
        executor.run_all_scenarios(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
