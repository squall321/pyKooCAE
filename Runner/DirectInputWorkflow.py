#!/usr/bin/env python3
"""
Direct Input Workflow Manager
낙하 각도 정보 없이 직접 입력 파일로 LS-DYNA 실행

주요 기능:
    1. 입력 파일 기반 워크플로우 (각도 정보 없음)
    2. KooMeshModifier + LS-DYNA 통합 실행
    3. 단계별 노드 점유율 및 노드 수 설정
    4. Slurm Array Job 최적화

사용 시나리오:
    - 이미 준비된 입력 파일로 시뮬레이션 실행
    - 사용자 정의 메쉬 수정 + LS-DYNA 실행
    - 단계별 자원 요구사항이 다른 경우

Author: koo.park
Email: koo.park@samsung.com
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime


class ResourceConfig:
    """Step별 자원 설정"""

    def __init__(
        self,
        nnodes: int = 1,
        ncpus_per_node: int = 32,
        memory_per_node: str = "64G",
        walltime: str = "02:00:00",
        partition: str = "normal"
    ):
        """
        Parameters:
            nnodes: 노드 수
            ncpus_per_node: 노드당 CPU 수
            memory_per_node: 노드당 메모리
            walltime: 최대 실행 시간
            partition: Slurm 파티션
        """
        self.nnodes = nnodes
        self.ncpus_per_node = ncpus_per_node
        self.memory_per_node = memory_per_node
        self.walltime = walltime
        self.partition = partition

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "nnodes": self.nnodes,
            "ncpus_per_node": self.ncpus_per_node,
            "memory_per_node": self.memory_per_node,
            "walltime": self.walltime,
            "partition": self.partition
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceConfig':
        """딕셔너리에서 생성"""
        return cls(
            nnodes=data.get("nnodes", 1),
            ncpus_per_node=data.get("ncpus_per_node", 32),
            memory_per_node=data.get("memory_per_node", "64G"),
            walltime=data.get("walltime", "02:00:00"),
            partition=data.get("partition", "normal")
        )


class DirectInputWorkflow:
    """Direct Input Workflow Manager"""

    def __init__(
        self,
        project_name: str,
        data_root: str = "/data",
        base_dir: str = None
    ):
        """
        Parameters:
            project_name: 프로젝트 이름
            data_root: 데이터 루트 디렉토리 (기본: /data)
            base_dir: 베이스 디렉토리
        """
        self.project_name = project_name
        self.data_root = data_root
        self.base_dir = base_dir or os.getcwd()

        # 프로젝트 디렉토리
        self.project_dir = os.path.join(data_root, project_name)
        os.makedirs(self.project_dir, exist_ok=True)

        # 실행 파일 경로
        self.koomesh_bin = "/opt/KooMeshModifier/run.sh"
        self.lsdyna_bin = "/opt/lsdyna/bin/ls-dyna"  # LS-DYNA 실행 파일

    # ========================================================================
    # 입력 파일 기반 워크플로우
    # ========================================================================

    def create_direct_input_job(
        self,
        job_name: str,
        input_files: List[str],
        num_steps: int,
        step_resources: Dict[int, ResourceConfig],
        use_koomesh: bool = True,
        use_lsdyna: bool = True,
        koomesh_params: Dict[str, Any] = None,
        lsdyna_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        직접 입력 파일 기반 Job 생성

        Parameters:
            job_name: Job 이름
            input_files: 입력 파일 경로 리스트
            num_steps: Step 수
            step_resources: Step별 자원 설정 {step_number: ResourceConfig}
            use_koomesh: KooMeshModifier 사용 여부
            use_lsdyna: LS-DYNA 실행 여부
            koomesh_params: KooMeshModifier 추가 파라미터
            lsdyna_params: LS-DYNA 추가 파라미터

        Returns:
            Job 메타데이터
        """
        job_id = f"{job_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job_dir = os.path.join(self.project_dir, job_id)

        # Job 디렉토리 생성
        os.makedirs(job_dir, exist_ok=True)

        # 메타데이터
        metadata = {
            "job_id": job_id,
            "job_name": job_name,
            "created_at": datetime.now().isoformat(),
            "input_files": input_files,
            "num_steps": num_steps,
            "use_koomesh": use_koomesh,
            "use_lsdyna": use_lsdyna,
            "step_resources": {k: v.to_dict() for k, v in step_resources.items()},
            "koomesh_params": koomesh_params or {},
            "lsdyna_params": lsdyna_params or {}
        }

        # 메타데이터 저장
        metadata_path = os.path.join(job_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # 입력 파일 복사
        for i, input_file in enumerate(input_files):
            if os.path.exists(input_file):
                dst = os.path.join(job_dir, f"input_{i+1:03d}.k")
                shutil.copy(input_file, dst)
                print(f"✅ 입력 파일 복사: {input_file} → {dst}")

        return metadata

    # ========================================================================
    # Slurm 스크립트 생성
    # ========================================================================

    def generate_direct_slurm_script(
        self,
        job_metadata: Dict[str, Any],
        step_number: int,
        output_dir: str = None
    ) -> str:
        """
        직접 입력 파일 기반 Slurm 스크립트 생성

        Parameters:
            job_metadata: Job 메타데이터
            step_number: Step 번호
            output_dir: 출력 디렉토리

        Returns:
            생성된 스크립트 경로
        """
        job_id = job_metadata["job_id"]
        job_dir = os.path.join(self.project_dir, job_id)
        step_dir = os.path.join(job_dir, f"Step{step_number:03d}")
        os.makedirs(step_dir, exist_ok=True)

        # 자원 설정
        resources = job_metadata["step_resources"].get(
            str(step_number),
            ResourceConfig().to_dict()
        )

        # Slurm 스크립트
        script_path = os.path.join(
            output_dir or self.base_dir,
            f"slurm_{job_id}_S{step_number:03d}.sh"
        )

        use_koomesh = job_metadata.get("use_koomesh", True)
        use_lsdyna = job_metadata.get("use_lsdyna", True)
        koomesh_params = job_metadata.get("koomesh_params", {})
        lsdyna_params = job_metadata.get("lsdyna_params", {})

        # 스크립트 생성
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(f"""#!/bin/bash
#SBATCH --job-name={job_id}_S{step_number:03d}
#SBATCH --nodes={resources['nnodes']}
#SBATCH --ntasks-per-node={resources['ncpus_per_node']}
#SBATCH --mem={resources['memory_per_node']}
#SBATCH --time={resources['walltime']}
#SBATCH --partition={resources['partition']}
#SBATCH --output={step_dir}/slurm_%j.out
#SBATCH --error={step_dir}/slurm_%j.err

# ========================================================================
# Direct Input Workflow - Step {step_number}
# Generated by DirectInputWorkflow
# ========================================================================

echo "=================================================="
echo "Job ID: {job_id}"
echo "Step: {step_number}"
echo "Nodes: {resources['nnodes']}"
echo "CPUs per node: {resources['ncpus_per_node']}"
echo "Memory: {resources['memory_per_node']}"
echo "Start time: $(date)"
echo "=================================================="

# 작업 디렉토리 이동
cd "{step_dir}"

# 실행 시간 측정
START_TIME=$(date +%s)

""")

            # KooMeshModifier 실행
            if use_koomesh:
                input_file = f"{job_dir}/input_{step_number:03d}.k"

                f.write(f"""
# ========================================================================
# Step 1: KooMeshModifier 실행
# ========================================================================

echo "Step 1: Running KooMeshModifier..."

INPUT_FILE="{input_file}"
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ 입력 파일 없음: $INPUT_FILE"
    exit 1
fi

""")

                # KooMeshModifier 파라미터
                koomesh_cmd = f"{self.koomesh_bin}"
                for key, value in koomesh_params.items():
                    koomesh_cmd += f" --{key}=\"{value}\""

                f.write(f"""{koomesh_cmd} --input="$INPUT_FILE" --output-dir="./"

KOOMESH_EXIT=$?
if [ $KOOMESH_EXIT -ne 0 ]; then
    echo "❌ KooMeshModifier 실패 (Exit code: $KOOMESH_EXIT)"
    exit $KOOMESH_EXIT
fi

echo "✅ KooMeshModifier 완료"

""")

            # LS-DYNA 실행
            if use_lsdyna:
                ncpus_total = resources['nnodes'] * resources['ncpus_per_node']
                memory_mb = lsdyna_params.get("memory", 60000)

                f.write(f"""
# ========================================================================
# Step 2: LS-DYNA 실행
# ========================================================================

echo "Step 2: Running LS-DYNA..."

# dynain 파일 확인
DYNAIN_FILE="./dynain"
if [ ! -f "$DYNAIN_FILE" ]; then
    echo "❌ dynain 파일 없음: $DYNAIN_FILE"
    exit 1
fi

# LS-DYNA 실행
mpirun -np {ncpus_total} {self.lsdyna_bin} \\
    i=dynain \\
    memory={memory_mb}m \\
    ncpu={ncpus_total}

LSDYNA_EXIT=$?
if [ $LSDYNA_EXIT -ne 0 ]; then
    echo "❌ LS-DYNA 실패 (Exit code: $LSDYNA_EXIT)"
    exit $LSDYNA_EXIT
fi

echo "✅ LS-DYNA 완료"

# 결과 파일 확인
if [ ! -f "d3plot01" ]; then
    echo "⚠️  경고: d3plot01 파일 없음"
fi

""")

            # Lock 파일 생성
            f.write(f"""
# ========================================================================
# 완료 처리
# ========================================================================

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# Lock 파일 생성
cat > .lock << EOF
{{
  "completed_at": "$(date -Iseconds)",
  "elapsed_seconds": $ELAPSED,
  "exit_code": 0
}}
EOF

echo "=================================================="
echo "✅ Step {step_number} 완료"
echo "소요 시간: ${{ELAPSED}}초"
echo "완료 시각: $(date)"
echo "=================================================="
""")

        # 실행 권한 부여
        os.chmod(script_path, 0o755)

        print(f"✅ Slurm 스크립트 생성: {script_path}")
        return script_path

    # ========================================================================
    # Slurm 제출
    # ========================================================================

    def submit_direct_workflow(
        self,
        job_metadata: Dict[str, Any],
        dry_run: bool = False
    ) -> List[str]:
        """
        직접 입력 워크플로우 제출

        Parameters:
            job_metadata: Job 메타데이터
            dry_run: Dry-run 모드

        Returns:
            제출된 Job ID 리스트
        """
        job_ids = []
        num_steps = job_metadata["num_steps"]

        for step in range(1, num_steps + 1):
            # Slurm 스크립트 생성
            script_path = self.generate_direct_slurm_script(job_metadata, step)

            # 의존성 설정 (Step 2+)
            dependency = ""
            if step > 1 and len(job_ids) > 0:
                dependency = f"--dependency=afterok:{job_ids[-1]}"

            # Slurm 제출
            cmd = ["sbatch"]
            if dependency:
                cmd.append(dependency)
            cmd.extend(["--parsable", script_path])

            if dry_run:
                print(f"[DRY-RUN] {' '.join(cmd)}")
                job_ids.append(f"DRYRUN_{step}")
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    job_id = result.stdout.strip()
                    job_ids.append(job_id)
                    print(f"✅ Step {step} 제출: Job ID {job_id}")
                else:
                    print(f"❌ Step {step} 제출 실패: {result.stderr}")
                    break

        return job_ids

    # ========================================================================
    # 노드 점유율 모니터링
    # ========================================================================

    def monitor_node_occupancy(
        self,
        job_ids: List[str],
        interval: int = 60
    ):
        """
        노드 점유율 모니터링

        Parameters:
            job_ids: 모니터링할 Job ID 리스트
            interval: 체크 간격 (초)
        """
        import time

        print("\n========================================")
        print("노드 점유율 모니터링 시작")
        print("========================================\n")

        while True:
            all_completed = True

            for job_id in job_ids:
                # scontrol로 Job 정보 조회
                result = subprocess.run(
                    ["scontrol", "show", "job", job_id],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    output = result.stdout

                    # JobState 추출
                    state = "UNKNOWN"
                    nodes = "N/A"
                    cpus = "N/A"

                    for line in output.split('\n'):
                        if "JobState=" in line:
                            state = line.split("JobState=")[1].split()[0]
                        if "NumNodes=" in line:
                            nodes = line.split("NumNodes=")[1].split()[0]
                        if "NumCPUs=" in line:
                            cpus = line.split("NumCPUs=")[1].split()[0]

                    print(f"Job {job_id}: {state} | Nodes: {nodes} | CPUs: {cpus}")

                    if state not in ["COMPLETED", "FAILED", "CANCELLED"]:
                        all_completed = False

            if all_completed:
                print("\n✅ 모든 Job 완료")
                break

            print(f"\n다음 체크: {interval}초 후...\n")
            time.sleep(interval)


# ========================================================================
# CLI
# ========================================================================

def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description="Direct Input Workflow Manager"
    )

    parser.add_argument(
        "config",
        help="직접 입력 워크플로우 설정 JSON 파일"
    )

    parser.add_argument(
        "--data-root",
        default="/data",
        help="데이터 루트 디렉토리 (기본: /data)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run 모드 (실제 제출 안함)"
    )

    parser.add_argument(
        "--monitor",
        action="store_true",
        help="노드 점유율 모니터링"
    )

    args = parser.parse_args()

    # 설정 파일 로드
    with open(args.config, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Workflow 생성
    workflow = DirectInputWorkflow(
        project_name=config["project_name"],
        data_root=args.data_root
    )

    # Job 생성
    step_resources = {
        int(k): ResourceConfig.from_dict(v)
        for k, v in config.get("step_resources", {}).items()
    }

    job_metadata = workflow.create_direct_input_job(
        job_name=config["job_name"],
        input_files=config["input_files"],
        num_steps=config["num_steps"],
        step_resources=step_resources,
        use_koomesh=config.get("use_koomesh", True),
        use_lsdyna=config.get("use_lsdyna", True),
        koomesh_params=config.get("koomesh_params", {}),
        lsdyna_params=config.get("lsdyna_params", {})
    )

    # Workflow 제출
    job_ids = workflow.submit_direct_workflow(
        job_metadata,
        dry_run=args.dry_run
    )

    print(f"\n✅ 제출 완료: {len(job_ids)} Steps")
    for i, job_id in enumerate(job_ids, 1):
        print(f"  Step {i}: {job_id}")

    # 모니터링
    if args.monitor and not args.dry_run:
        workflow.monitor_node_occupancy(job_ids)


if __name__ == "__main__":
    main()
