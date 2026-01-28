#!/usr/bin/env python3
"""
DOE 병렬 처리 최적화 시스템

대규모 DOE 케이스를 병렬로 효율적으로 처리하는 두 가지 방식:
    1. Dependency Chain (권장): Slurm --dependency 사용
    2. Lock File Polling: 완료 감지 + 동적 재제출

시나리오 예시:
    Fibonacci 10 points × DOE 5 samples × 3 Steps = 150 Jobs

Author: koo.park
Email: koo.park@samsung.com
"""

import os
import sys
import json
import time
import argparse
import subprocess
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path


class DOEParallelOptimizer:
    """DOE 병렬 처리 최적화"""

    def __init__(self, runner_config_path: str, partition: str = "normal"):
        with open(runner_config_path, 'r', encoding='utf-8') as f:
            self.runner_config = json.load(f)

        self.project_name = self.runner_config.get("project_name", "Project")
        self.base_dir = self.runner_config.get("base_dir", os.getcwd())
        self.environment = self.runner_config.get("environment", {})
        self.scenarios = self.runner_config.get("scenarios", [])

        self.partition = partition
        self.ncpu = self.environment.get("ncpu", 32)
        self.memory = self.environment.get("memory", "64G")
        self.timeout = self.environment.get("timeout", 7200)

    # ========================================================================
    # 방식 A: Dependency Chain (권장) ⭐
    # ========================================================================

    def submit_doe_with_dependency_chain(self, scenario: Dict[str, Any]) -> List[str]:
        """
        방식 A: Slurm Dependency Chain

        장점:
            - Slurm 네이티브 기능 활용
            - 자동 스케줄링 (큐에서 대기)
            - Lock 파일 불필요
            - 간단하고 안정적

        단점:
            - Job ID 관리 필요
            - Slurm 스케줄러 부담 (대규모 시 주의)

        구조:
            Step 1 (DOE 1-50 병렬)
                ↓ (각각 --dependency)
            Step 2 (DOE 1-50 병렬)
                ↓ (각각 --dependency)
            Step 3 (DOE 1-50 병렬)
        """
        scenario_id = scenario.get("scenario_id")
        scenario_name = scenario.get("scenario_name")
        steps = scenario.get("steps", [])

        print(f"\n{'='*100}")
        print(f"🚀 DOE 병렬 제출 (Dependency Chain) - {scenario_name}")
        print(f"{'='*100}\n")

        # Step별로 처리
        doe_job_ids = {}  # {doe_index: {step: job_id}}

        for step_cfg in steps:
            step_number = step_cfg.get("step_number")
            doe_index = step_cfg.get("doe_index", 0)

            if doe_index not in doe_job_ids:
                doe_job_ids[doe_index] = {}

            # 이전 Step의 Job ID 찾기
            prev_job_id = None
            if step_number > 1:
                prev_job_id = doe_job_ids[doe_index].get(step_number - 1)

            # Job 제출
            job_id = self._submit_single_doe_step(
                scenario_id, step_cfg, prev_job_id
            )

            doe_job_ids[doe_index][step_number] = job_id

            print(f"  DOE {doe_index:03d}, Step {step_number}: Job {job_id}" +
                  (f" (depends on {prev_job_id})" if prev_job_id else ""))

        print(f"\n✅ 총 {len(doe_job_ids)} DOE × {len(steps)} Steps = {len(doe_job_ids) * len(steps)} Jobs 제출")
        print(f"{'='*100}\n")

        return list(doe_job_ids.keys())

    def _submit_single_doe_step(
        self,
        scenario_id: str,
        step_cfg: Dict[str, Any],
        prev_job_id: Optional[str] = None
    ) -> str:
        """
        단일 DOE Step Job 제출

        Parameters:
            scenario_id: 시나리오 ID
            step_cfg: Step 설정
            prev_job_id: 이전 Step의 Job ID (의존성)

        Returns:
            Job ID
        """
        step_number = step_cfg.get("step_number")
        doe_index = step_cfg.get("doe_index", 0)
        template = step_cfg.get("template")
        angle = step_cfg.get("angle", {})

        # Job 이름
        job_name = f"{scenario_id}_DOE{doe_index:03d}_S{step_number:03d}"

        # Slurm 스크립트 생성
        script_path = os.path.join(self.base_dir, f"slurm_{job_name}.sh")

        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"#SBATCH --job-name={job_name}\n")
            f.write(f"#SBATCH --partition={self.partition}\n")
            f.write(f"#SBATCH --nodes=1\n")
            f.write(f"#SBATCH --ntasks=1\n")
            f.write(f"#SBATCH --cpus-per-task={self.ncpu}\n")
            f.write(f"#SBATCH --mem={self.memory}\n")
            f.write(f"#SBATCH --time={self._seconds_to_slurm_time(self.timeout)}\n")
            f.write(f"#SBATCH --output={job_name}_%j.out\n")
            f.write(f"#SBATCH --error={job_name}_%j.err\n")

            # Dependency 설정
            if prev_job_id:
                f.write(f"#SBATCH --dependency=afterok:{prev_job_id}\n")

            f.write("\n")
            f.write(f"cd {self.base_dir}\n")
            f.write("\n")

            # KooMeshModifier 실행
            f.write("# KooMeshModifier 실행\n")
            f.write(f"/opt/KooMeshModifier/run.sh \\\n")
            f.write(f"  --scenario={scenario_id} \\\n")
            f.write(f"  --step={step_number} \\\n")
            f.write(f"  --doe-index={doe_index} \\\n")
            f.write(f"  --template={template} \\\n")
            f.write(f"  --roll={angle['roll']} \\\n")
            f.write(f"  --pitch={angle['pitch']} \\\n")
            f.write(f"  --yaw={angle['yaw']}\n")
            f.write("\n")

            # 완료 표시
            f.write(f'echo "✅ {job_name} 완료"\n')

        os.chmod(script_path, 0o755)

        # sbatch 제출
        result = subprocess.run(
            ["sbatch", script_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ 제출 실패: {result.stderr}")
            return "FAILED"

        job_id = result.stdout.strip().split()[-1]
        return job_id

    # ========================================================================
    # 방식 B: Lock File Polling (대안)
    # ========================================================================

    def submit_doe_with_lock_polling(self, scenario: Dict[str, Any]) -> List[str]:
        """
        방식 B: Lock 파일 + Polling

        장점:
            - 진행 상황 추적 용이
            - Slurm 스케줄러 부담 적음
            - 동적 재제출 가능

        단점:
            - Polling 오버헤드
            - Lock 파일 관리 필요
            - 복잡도 증가

        구조:
            1. Step 1 (DOE 1-50) 병렬 제출
            2. Poller Job: Step 1 완료 감지 (lock 파일)
            3. Step 2 (DOE 1-50) 병렬 제출
            4. Poller Job: Step 2 완료 감지
            5. Step 3 (DOE 1-50) 병렬 제출
        """
        scenario_id = scenario.get("scenario_id")
        scenario_name = scenario.get("scenario_name")
        steps = scenario.get("steps", [])

        print(f"\n{'='*100}")
        print(f"🚀 DOE 병렬 제출 (Lock Polling) - {scenario_name}")
        print(f"{'='*100}\n")

        # Lock 디렉토리 생성
        lock_dir = os.path.join(self.base_dir, f".locks_{scenario_id}")
        os.makedirs(lock_dir, exist_ok=True)

        # Step별로 처리
        all_job_ids = []

        for step_cfg in steps:
            step_number = step_cfg.get("step_number")

            # Step의 모든 DOE Job 제출
            job_ids = self._submit_step_doe_jobs_with_lock(
                scenario_id, step_cfg, lock_dir
            )
            all_job_ids.extend(job_ids)

            print(f"  Step {step_number}: {len(job_ids)} Jobs 제출")

            # Poller Job 제출 (Step 완료 감지)
            if step_number < len(steps):
                poller_job_id = self._submit_poller_job(
                    scenario_id, step_number, len(job_ids), lock_dir
                )
                all_job_ids.append(poller_job_id)
                print(f"  Step {step_number} Poller: Job {poller_job_id}")

        print(f"\n✅ 총 {len(all_job_ids)} Jobs 제출 (DOE + Poller)")
        print(f"{'='*100}\n")

        return all_job_ids

    def _submit_step_doe_jobs_with_lock(
        self,
        scenario_id: str,
        step_cfg: Dict[str, Any],
        lock_dir: str
    ) -> List[str]:
        """Step의 모든 DOE Job 제출 (Lock 파일 생성 포함)"""
        step_number = step_cfg.get("step_number")

        # 이 Step의 DOE 개수 (실제로는 runner_config에서 읽어야 함)
        # 여기서는 예시로 50개 가정
        doe_count = 50

        job_ids = []

        for doe_index in range(doe_count):
            job_id = self._submit_doe_job_with_lock_creation(
                scenario_id, step_cfg, doe_index, lock_dir
            )
            job_ids.append(job_id)

        return job_ids

    def _submit_doe_job_with_lock_creation(
        self,
        scenario_id: str,
        step_cfg: Dict[str, Any],
        doe_index: int,
        lock_dir: str
    ) -> str:
        """DOE Job 제출 (완료 시 Lock 파일 생성)"""
        step_number = step_cfg.get("step_number")
        job_name = f"{scenario_id}_DOE{doe_index:03d}_S{step_number:03d}"

        script_path = os.path.join(self.base_dir, f"slurm_{job_name}.sh")

        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"#SBATCH --job-name={job_name}\n")
            f.write(f"#SBATCH --partition={self.partition}\n")
            f.write(f"#SBATCH --cpus-per-task={self.ncpu}\n")
            f.write(f"#SBATCH --mem={self.memory}\n")
            f.write(f"#SBATCH --time={self._seconds_to_slurm_time(self.timeout)}\n")
            f.write(f"#SBATCH --output={job_name}_%j.out\n")
            f.write(f"#SBATCH --error={job_name}_%j.err\n")
            f.write("\n")

            f.write(f"cd {self.base_dir}\n")
            f.write("\n")

            # KooMeshModifier 실행
            f.write("/opt/KooMeshModifier/run.sh ...\n")
            f.write("\n")

            # Lock 파일 생성
            lock_file = os.path.join(lock_dir, f"Step{step_number:03d}_DOE{doe_index:03d}.lock")
            f.write(f"# Lock 파일 생성 (완료 표시)\n")
            f.write(f'echo "DONE" > {lock_file}\n')
            f.write(f'echo "✅ {job_name} 완료 (Lock 생성: {lock_file})"\n')

        os.chmod(script_path, 0o755)

        result = subprocess.run(["sbatch", script_path], capture_output=True, text=True)
        job_id = result.stdout.strip().split()[-1] if result.returncode == 0 else "FAILED"
        return job_id

    def _submit_poller_job(
        self,
        scenario_id: str,
        step_number: int,
        expected_doe_count: int,
        lock_dir: str
    ) -> str:
        """
        Poller Job 제출

        역할:
            - Step N의 모든 DOE Lock 파일 생성 대기
            - 완료 시 Step N+1 자동 제출
        """
        job_name = f"{scenario_id}_Poller_S{step_number:03d}"
        script_path = os.path.join(self.base_dir, f"slurm_{job_name}.sh")

        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"#SBATCH --job-name={job_name}\n")
            f.write(f"#SBATCH --partition={self.partition}\n")
            f.write(f"#SBATCH --cpus-per-task=1\n")
            f.write(f"#SBATCH --mem=1G\n")
            f.write(f"#SBATCH --time=24:00:00\n")
            f.write(f"#SBATCH --output={job_name}_%j.out\n")
            f.write("\n")

            f.write(f"cd {self.base_dir}\n")
            f.write("\n")

            # Polling 로직
            f.write(f"echo 'Waiting for Step {step_number} completion...'\n")
            f.write(f"EXPECTED_COUNT={expected_doe_count}\n")
            f.write(f"LOCK_DIR={lock_dir}\n")
            f.write("\n")

            f.write("while true; do\n")
            f.write(f"  COMPLETED=$(ls $LOCK_DIR/Step{step_number:03d}_DOE*.lock 2>/dev/null | wc -l)\n")
            f.write('  echo "Completed: $COMPLETED / $EXPECTED_COUNT"\n')
            f.write("\n")
            f.write("  if [ $COMPLETED -eq $EXPECTED_COUNT ]; then\n")
            f.write(f'    echo "✅ Step {step_number} 모든 DOE 완료!"\n')
            f.write("    break\n")
            f.write("  fi\n")
            f.write("\n")
            f.write("  sleep 60  # 1분마다 체크\n")
            f.write("done\n")
            f.write("\n")

            # Step N+1 제출
            f.write(f"# Step {step_number + 1} 자동 제출\n")
            f.write(f"python3 Runner/DOEParallelOptimizer.py \\\n")
            f.write(f"  runner_config.json \\\n")
            f.write(f"  --scenario={scenario_id} \\\n")
            f.write(f"  --step={step_number + 1}\n")

        os.chmod(script_path, 0o755)

        result = subprocess.run(["sbatch", script_path], capture_output=True, text=True)
        job_id = result.stdout.strip().split()[-1] if result.returncode == 0 else "FAILED"
        return job_id

    # ========================================================================
    # 유틸리티
    # ========================================================================

    def _seconds_to_slurm_time(self, seconds: int) -> str:
        """초를 Slurm 시간 형식으로 변환"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def compare_methods(self):
        """두 방식 비교"""
        print(f"\n{'='*100}")
        print("📊 DOE 병렬 처리 방식 비교")
        print(f"{'='*100}\n")

        print("방식 A: Dependency Chain (권장) ⭐")
        print("  장점:")
        print("    ✅ Slurm 네이티브 기능 (안정적)")
        print("    ✅ 자동 스케줄링")
        print("    ✅ Lock 파일 불필요")
        print("    ✅ 간단하고 명확")
        print("  단점:")
        print("    ⚠️  Job ID 관리 필요")
        print("    ⚠️  대규모 시 Slurm 부담 (수천 Job)")
        print()

        print("방식 B: Lock File Polling")
        print("  장점:")
        print("    ✅ 진행 상황 추적 용이")
        print("    ✅ 동적 재제출 가능")
        print("    ✅ Slurm 스케줄러 부담 적음")
        print("  단점:")
        print("    ⚠️  Polling 오버헤드")
        print("    ⚠️  Lock 파일 관리 필요")
        print("    ⚠️  복잡도 증가")
        print()

        print("권장:")
        print("  - DOE < 500: 방식 A (Dependency Chain)")
        print("  - DOE > 500: 방식 B (Lock Polling) 또는 Array Job")
        print(f"{'='*100}\n")


def main():
    parser = argparse.ArgumentParser(description="DOE 병렬 처리 최적화")
    parser.add_argument("runner_config", help="runner_config.json 경로")
    parser.add_argument("--method", choices=["dependency", "lock"], default="dependency",
                        help="병렬 처리 방식 (dependency 또는 lock)")
    parser.add_argument("--partition", default="normal", help="Slurm 파티션")
    parser.add_argument("--compare", action="store_true", help="두 방식 비교")
    args = parser.parse_args()

    optimizer = DOEParallelOptimizer(args.runner_config, args.partition)

    if args.compare:
        optimizer.compare_methods()
        return

    # 첫 번째 시나리오에 대해 실행 (예시)
    if optimizer.scenarios:
        scenario = optimizer.scenarios[0]

        if args.method == "dependency":
            optimizer.submit_doe_with_dependency_chain(scenario)
        elif args.method == "lock":
            optimizer.submit_doe_with_lock_polling(scenario)


if __name__ == "__main__":
    main()
