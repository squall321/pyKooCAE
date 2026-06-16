#!/usr/bin/env python3
"""
Slurm 병렬 제출 스크립트

runner_config.json의 각 시나리오를 독립적인 Slurm Job으로 제출합니다.

Usage:
    python SlurmSubmitter.py runner_config.json [--partition=PARTITION] [--dry-run]

Features:
    - 시나리오별 독립 실행 (병렬 처리)
    - DOE 케이스별 배열 Job (Array Job)
    - 자원 효율 최적화
    - Step별 의존성 관리 (--dependency)

Author: koo.park
Email: koo.park@samsung.com
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, List


class SlurmSubmitter:
    """Slurm 병렬 제출 관리자"""

    def __init__(self, runner_config_path: str, partition: str = "normal", dry_run: bool = False):
        """
        Parameters:
            runner_config_path: runner_config.json 경로
            partition: Slurm 파티션
            dry_run: Dry-run 모드
        """
        with open(runner_config_path, 'r', encoding='utf-8') as f:
            self.runner_config = json.load(f)

        self.project_name = self.runner_config.get("project_name", "Project")
        self.base_dir = self.runner_config.get("base_dir", os.getcwd())
        self.environment = self.runner_config.get("environment", {})
        self.scenarios = self.runner_config.get("scenarios", [])

        self.partition = partition
        self.dry_run = dry_run

        # Slurm 기본 설정
        self.ncpu = self.environment.get("ncpu", 32)
        self.memory = self.environment.get("memory", "64G")
        self.timeout = self.environment.get("timeout", 7200)
        self.time_limit = self._seconds_to_slurm_time(self.timeout * 2)  # 2배 여유

    def _seconds_to_slurm_time(self, seconds: int) -> str:
        """초를 Slurm 시간 형식으로 변환 (HH:MM:SS)"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def submit_all_scenarios_parallel(self):
        """모든 시나리오를 병렬로 제출 (각각 독립 Job)"""
        print(f"\n{'='*100}")
        print(f"🚀 Slurm 병렬 제출 - {self.project_name}")
        print(f"{'='*100}\n")
        print(f"총 시나리오 수: {len(self.scenarios)}")
        print(f"파티션: {self.partition}")
        print(f"자원: {self.ncpu} CPU, {self.memory} 메모리")
        print(f"시간 제한: {self.time_limit}")
        print(f"{'='*100}\n")

        job_ids = []

        for i, scenario in enumerate(self.scenarios, start=1):
            scenario_id = scenario.get("scenario_id")
            scenario_name = scenario.get("scenario_name")

            print(f"[{i}/{len(self.scenarios)}] 시나리오 제출: {scenario_name} ({scenario_id})")

            job_id = self._submit_scenario_sequential(scenario)
            job_ids.append((scenario_id, job_id))

            print(f"  → Job ID: {job_id}\n")

        print(f"{'='*100}")
        print(f"✅ {len(job_ids)}개 시나리오 제출 완료!")
        print(f"{'='*100}\n")

        # Job ID 요약
        print("제출된 Job ID:")
        for scenario_id, job_id in job_ids:
            print(f"  {scenario_id}: {job_id}")
        print()

        # postprocess.enabled이면 scenario mode 로 sphere(DROP) / impact(IMPACT)
        # 중 하나를 dependent job 으로 제출
        self._maybe_submit_sphere_job(job_ids)

        return job_ids

    def _maybe_submit_sphere_job(self, job_ids):
        """postprocess 종합 리포트 dependent Slurm job 제출 (scenario mode 로 routing).

        DROP→sphere_report(auto_sphere), IMPACT→impact_report(auto_impact). 둘 다
        돌지 않는다 — 과거에는 auto_sphere 만 검사해 IMPACT 데이터에도 sphere 가
        돌던 버그가 있었다. 해당 .sh 자체는 prepare 시점에 항상 생성되어 있다고 가정.
        이 함수는 sbatch 텍스트 생성 + Slurm 제출만 담당.
        """
        pp = self.runner_config.get("postprocess")
        if not pp or not pp.get("enabled"):
            return

        try:
            from Runner.PostprocessShellGenerator import (
                build_sphere_sbatch, build_impact_sbatch, report_mode_from_runner_config,
            )
        except Exception as e:
            print(f"  Warning: PostprocessShellGenerator import 실패 (skip): {e}")
            return

        # scenario mode 로 sphere vs impact 선택
        mode = report_mode_from_runner_config(self.runner_config)
        if mode == "IMPACT":
            if not pp.get("auto_impact", True):
                return
            report_label = "Impact"
            sbatch_builder = build_impact_sbatch
            sbatch_name = "impact_report.sbatch"
        else:
            if not pp.get("auto_sphere", True):
                return
            report_label = "Sphere"
            sbatch_builder = build_sphere_sbatch
            sbatch_name = "sphere_report.sbatch"

        # 각 시나리오 base_dir에 종합 리포트 적용
        # (단순화: 단일 base_dir 가정 — 첫 시나리오 기준)
        output_dir = self.base_dir
        # job_ids는 [(scenario_id, job_id_str), ...] 형태
        dep_ids = [str(jid) for _, jid in job_ids if jid]
        if not dep_ids:
            print(f"  Warning: dependency용 job_id 없음 ({report_label.lower()} job 제출 skip)")
            return

        env_for_report = dict(self.environment)
        env_for_report.setdefault("partition", self.partition)
        sbatch_text = sbatch_builder(
            output_dir=output_dir,
            sif_path=pp.get("sif_path"),
            options=pp,
            environment=env_for_report,
            dependency_ids=dep_ids,
        )
        sbatch_path = os.path.join(output_dir, sbatch_name)
        with open(sbatch_path, 'w') as f:
            f.write(sbatch_text)
        os.chmod(sbatch_path, 0o755)
        print(f"\n[{report_label} Postprocess] sbatch 생성: {sbatch_path}")
        print(f"  Dependency: afterany:{':'.join(dep_ids)}")

        if self.dry_run:
            print(f"  [DRY-RUN] sbatch 제출 skip")
            return

        try:
            result = subprocess.run(
                ["sbatch", sbatch_path],
                capture_output=True, text=True, check=True
            )
            report_job_id = result.stdout.strip().split()[-1]
            print(f"  → {report_label} Job ID: {report_job_id}")
        except Exception as e:
            print(f"  Warning: {report_label.lower()} job 제출 실패: {e}")

    def _submit_scenario_sequential(self, scenario: Dict[str, Any]) -> str:
        """
        시나리오 제출 (순차 실행 - Step 간 의존성 있음)

        각 시나리오는 독립 Job으로 제출되지만,
        시나리오 내부 Step들은 순차 실행 (dynain 의존성)
        """
        scenario_id = scenario.get("scenario_id")
        scenario_name = scenario.get("scenario_name")
        total_steps = scenario.get("total_steps")

        # Slurm 스크립트 생성
        script_path = os.path.join(self.base_dir, f"slurm_{scenario_id}.sh")

        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"#SBATCH --job-name={scenario_id}\n")
            f.write(f"#SBATCH --partition={self.partition}\n")
            f.write(f"#SBATCH --nodes=1\n")
            f.write(f"#SBATCH --ntasks=1\n")
            f.write(f"#SBATCH --cpus-per-task={self.ncpu}\n")
            f.write(f"#SBATCH --mem={self.memory}\n")
            f.write(f"#SBATCH --time={self.time_limit}\n")
            f.write(f"#SBATCH --output={scenario_id}_%j.out\n")
            f.write(f"#SBATCH --error={scenario_id}_%j.err\n")
            f.write("\n")

            f.write("# 환경 변수 설정\n")
            f.write(f"export OMP_NUM_THREADS={self.ncpu}\n")
            f.write(f"export MKL_NUM_THREADS={self.ncpu}\n")
            f.write("\n")

            f.write("# 작업 디렉토리 이동\n")
            f.write(f"cd {self.base_dir}\n")
            f.write("\n")

            f.write("# SimplifiedExecutor 실행 (특정 시나리오만)\n")
            f.write(f"python3 Runner/SimplifiedExecutor.py runner_config.json \\\n")
            f.write(f"  --scenario={scenario_id}\n")
            f.write("\n")

            f.write("# 완료 메시지\n")
            f.write(f'echo "✅ 시나리오 완료: {scenario_id}"\n')

        # 실행 권한 부여
        os.chmod(script_path, 0o755)

        if self.dry_run:
            print(f"  [DRY-RUN] sbatch {script_path}")
            return "DRY_RUN_JOB_ID"

        # Slurm 제출
        result = subprocess.run(
            ["sbatch", script_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"  ❌ 제출 실패: {result.stderr}")
            return "FAILED"

        # Job ID 추출 (예: "Submitted batch job 123456")
        job_id = result.stdout.strip().split()[-1]
        return job_id

    def submit_all_scenarios_with_dependency(self):
        """
        모든 시나리오를 병렬로 제출 + Step별 의존성 관리

        고급 기능: 각 Step을 독립 Job으로 제출하고 --dependency로 연결
        → 더 세밀한 제어 가능하지만 복잡도 증가
        """
        print(f"\n{'='*100}")
        print(f"🚀 Slurm 병렬 제출 (Step별 의존성) - {self.project_name}")
        print(f"{'='*100}\n")

        all_job_ids = []

        for scenario in self.scenarios:
            job_ids = self._submit_scenario_with_dependency(scenario)
            all_job_ids.extend(job_ids)

        print(f"\n{'='*100}")
        print(f"✅ 총 {len(all_job_ids)}개 Job 제출 완료!")
        print(f"{'='*100}\n")

        return all_job_ids

    def _submit_scenario_with_dependency(self, scenario: Dict[str, Any]) -> List[str]:
        """
        시나리오의 각 Step을 독립 Job으로 제출 + --dependency 설정
        """
        scenario_id = scenario.get("scenario_id")
        scenario_name = scenario.get("scenario_name")
        steps = scenario.get("steps", [])

        print(f"\n시나리오: {scenario_name} ({scenario_id})")
        print(f"  총 Step 수: {len(steps)}")

        job_ids = []
        prev_job_id = None

        for step_cfg in steps:
            step_number = step_cfg.get("step_number")

            # Step Job 스크립트 생성
            script_path = os.path.join(
                self.base_dir,
                f"slurm_{scenario_id}_Step{step_number:03d}.sh"
            )

            with open(script_path, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(f"#SBATCH --job-name={scenario_id}_S{step_number:03d}\n")
                f.write(f"#SBATCH --partition={self.partition}\n")
                f.write(f"#SBATCH --nodes=1\n")
                f.write(f"#SBATCH --ntasks=1\n")
                f.write(f"#SBATCH --cpus-per-task={self.ncpu}\n")
                f.write(f"#SBATCH --mem={self.memory}\n")
                f.write(f"#SBATCH --time={self.time_limit}\n")
                f.write(f"#SBATCH --output={scenario_id}_S{step_number:03d}_%j.out\n")
                f.write(f"#SBATCH --error={scenario_id}_S{step_number:03d}_%j.err\n")

                # Step 2+ → 이전 Step 완료 후 실행
                if prev_job_id:
                    f.write(f"#SBATCH --dependency=afterok:{prev_job_id}\n")

                f.write("\n")
                f.write(f"cd {self.base_dir}\n")
                f.write("\n")

                # Step 실행 (KooMeshModifier 호출)
                f.write("# KooMeshModifier 실행\n")
                f.write(f"/opt/KooMeshModifier/run.sh \\\n")
                f.write(f"  --step={step_number} \\\n")
                f.write(f"  --scenario={scenario_id} \\\n")
                f.write(f"  --config=runner_config.json\n")
                f.write("\n")

                f.write(f'echo "✅ Step {step_number} 완료"\n')

            os.chmod(script_path, 0o755)

            if self.dry_run:
                print(f"  Step {step_number}: [DRY-RUN] sbatch {script_path}")
                job_id = f"DRY_{step_number}"
            else:
                result = subprocess.run(
                    ["sbatch", script_path],
                    capture_output=True,
                    text=True
                )
                job_id = result.stdout.strip().split()[-1] if result.returncode == 0 else "FAILED"
                print(f"  Step {step_number}: Job ID {job_id}")

            job_ids.append(job_id)
            prev_job_id = job_id

        return job_ids

    def print_resource_estimate(self):
        """자원 사용량 예측"""
        print(f"\n{'='*100}")
        print(f"📊 자원 사용량 예측")
        print(f"{'='*100}\n")

        total_steps = sum(scenario.get("total_steps", 0) for scenario in self.scenarios)

        print(f"병렬 제출 방식 (시나리오별 독립 Job):")
        print(f"  - 동시 실행 시나리오 수: {len(self.scenarios)}개")
        print(f"  - 시나리오당 평균 Step: {total_steps / len(self.scenarios):.1f}개")
        print(f"  - 총 Step 수: {total_steps}개")
        print(f"  - 자원 점유: {len(self.scenarios)}개 노드 × {self.ncpu} 코어 × {self.time_limit}")
        print(f"  - 예상 총 소요 시간: ~{self.time_limit} (가장 긴 시나리오 기준)")
        print()

        print(f"순차 제출 방식 (하나의 Job):")
        print(f"  - 총 Step 수: {total_steps}개")
        print(f"  - 자원 점유: 1개 노드 × {self.ncpu} 코어")

        # Step당 평균 시간 추정 (예: 1시간)
        step_time_hours = self.timeout / 3600
        total_time_hours = total_steps * step_time_hours
        print(f"  - 예상 총 소요 시간: ~{total_time_hours:.1f} 시간 (Step당 {step_time_hours:.1f}h 가정)")
        print()

        print(f"권장: 병렬 제출 방식")
        print(f"  → 시간 단축: ~{total_time_hours / len(self.scenarios):.1f}배")
        print(f"  → 노드 필요: {len(self.scenarios)}개 (동시 실행 시)")
        print(f"{'='*100}\n")


def main():
    parser = argparse.ArgumentParser(description="Slurm 병렬 제출 스크립트")
    parser.add_argument("runner_config", help="runner_config.json 경로")
    parser.add_argument("--partition", default="normal", help="Slurm 파티션 (기본: normal)")
    parser.add_argument("--mode", choices=["parallel", "dependency"], default="parallel",
                        help="제출 모드 (parallel: 시나리오별 독립, dependency: Step별 의존성)")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run 모드")
    parser.add_argument("--estimate", action="store_true", help="자원 사용량 예측만 출력")
    args = parser.parse_args()

    submitter = SlurmSubmitter(args.runner_config, args.partition, args.dry_run)

    if args.estimate:
        submitter.print_resource_estimate()
        return

    if args.mode == "parallel":
        submitter.submit_all_scenarios_parallel()
    elif args.mode == "dependency":
        submitter.submit_all_scenarios_with_dependency()


if __name__ == "__main__":
    main()
