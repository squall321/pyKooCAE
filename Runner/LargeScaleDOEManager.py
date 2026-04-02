#!/usr/bin/env python3
"""
대규모 DOE 관리 시스템 (수백~만 개 해석)

핵심 설계:
    1. Job 등록: /data/jobs/registry/ 에 Job 메타데이터 등록
    2. Lock 기반 완료 추적: /data/jobs/locks/ 에 .lock 파일 생성
    3. 자동 수집: 모든 Lock 확인 후 결과 복사
    4. Array Job 활용: Slurm 부담 최소화

시나리오:
    Fibonacci 10,000 points × DOE 10 × 3 Steps = 300,000 Jobs
    → Array Job 3개로 관리 (Step당 1개)

Author: koo.park
Email: koo.park@samsung.com
"""

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import hashlib


class LargeScaleDOEManager:
    """대규모 DOE 관리자"""

    def __init__(self, runner_config_path: str, data_root: str = "/data",
                 nodes: int = 1, jobs_per_node: int = 1, ncpu_per_job: int = 16):
        """
        Parameters:
            runner_config_path: runner_config.json 경로
            data_root: 데이터 루트 디렉토리 (기본: /data)
            nodes: 사용할 노드 수 (기본: 1)
            jobs_per_node: 노드당 동시 실행 Job 수 (기본: 1)
            ncpu_per_job: 각 Job이 사용할 CPU 수 (기본: 16)
        """
        with open(runner_config_path, 'r', encoding='utf-8') as f:
            self.runner_config = json.load(f)

        self.project_name = self.runner_config.get("project_name", "Project")
        self.base_dir = self.runner_config.get("base_dir", os.getcwd())
        self.environment = self.runner_config.get("environment", {})
        self.scenarios = self.runner_config.get("scenarios", [])

        # 데이터 루트 (/data/파일이름/)
        self.data_root = data_root
        self.project_dir = os.path.join(data_root, self.project_name)

        # 디렉토리 생성
        os.makedirs(self.project_dir, exist_ok=True)

        # Slurm 자원 설정
        self.nodes = nodes
        self.jobs_per_node = jobs_per_node
        self.ncpu_per_job = ncpu_per_job
        self.total_concurrent_jobs = nodes * jobs_per_node

        # Slurm 기본 설정 (환경에서 override 가능)
        self.partition = self.environment.get("partition", "normal")
        self.memory = self.environment.get("memory", "64G")
        self.timeout = self.environment.get("timeout", 7200)

        # 실행 파일 경로 (환경에서 override 가능)
        self.koomeshmodifier_path = self.environment.get("koomeshmodifier_path", "/opt/KooMeshModifier/run.sh")
        self.lsdyna_path = self.environment.get("lsdyna_path", "/opt/lsdyna/bin/ls-dyna")
        self.mpi_path = self.environment.get("mpi_path", "mpirun")
        self.lsdyna_memory = self.environment.get("lsdyna_memory", "2000m")

        # Apptainer 설정 (환경에서 override 가능)
        self.apptainer_sif = self.environment.get("apptainer_sif", None)
        self.apptainer_bind = self.environment.get("apptainer_bind", "/data:/data")

        # LS-DYNA용 별도 Apptainer (선택사항)
        self.lsdyna_apptainer_sif = self.environment.get("lsdyna_apptainer_sif", None)
        self.lsdyna_apptainer_bind = self.environment.get("lsdyna_apptainer_bind", "/data:/data")
        self.lsdyna_apptainer_env = self.environment.get("lsdyna_apptainer_env", {})
        self.apptainer_env = self.environment.get("apptainer_env", {})

        # 멀티노드 MPI 설정
        self.nodes_per_job = self.environment.get("nodes_per_job", 1)
        self.mpi_launcher = self.environment.get("mpi_launcher", "mpirun")  # "mpirun" or "srun"

        # APPTAINER_TMPDIR: /tmp 대신 /data 사용 (공간 부족 방지)
        self.apptainer_tmpdir = self.environment.get("apptainer_tmpdir", "/data/tmp")

        # Scratch Run 설정
        scratch_cfg = self.environment.get("scratch_run", {})
        self.scratch_enabled = scratch_cfg.get("enabled", False)
        self.scratch_base = scratch_cfg.get("scratch_base", "/scratch")
        self.scratch_cleanup = scratch_cfg.get("cleanup_on_success", True)

        # 호환성을 위해 ncpu도 유지 (ncpu_per_job과 동일)
        self.ncpu = ncpu_per_job

    # ========================================================================
    # Apptainer Helper
    # ========================================================================

    def wrap_with_apptainer(self, command: str, use_lsdyna: bool = False) -> str:
        """
        명령어를 Apptainer로 래핑

        Parameters:
            command: 실행할 명령어
            use_lsdyna: True이면 LS-DYNA용 Apptainer 사용, False이면 KooMeshModifier용

        Returns:
            Apptainer로 래핑된 명령어 (SIF 설정 시) 또는 원본 명령어

        Example:
            # KooMeshModifier
            Input:  "/opt/KooMeshModifier/run.sh --input=input.txt"
            Output: "apptainer exec --bind /data:/data /path/to/koomesh.sif /opt/KooMeshModifier/run.sh --input=input.txt"

            # LS-DYNA
            Input:  "mpirun -np 16 /opt/lsdyna/bin/ls-dyna i=input.k"
            Output: "apptainer exec --bind /data:/data /path/to/lsdyna.sif mpirun -np 16 /opt/lsdyna/bin/ls-dyna i=input.k"
        """
        if use_lsdyna:
            # LS-DYNA용 Apptainer (있으면)
            sif = self.lsdyna_apptainer_sif
            bind = self.lsdyna_apptainer_bind
            env_vars = self.lsdyna_apptainer_env
        else:
            # KooMeshModifier용 Apptainer
            sif = self.apptainer_sif
            bind = self.apptainer_bind
            env_vars = self.apptainer_env

        if sif:
            # Apptainer가 설정되어 있으면 래핑
            # APPTAINER_TMPDIR 디렉토리 생성 및 호스트 환경변수 설정
            os.makedirs(self.apptainer_tmpdir, exist_ok=True)
            os.environ["APPTAINER_TMPDIR"] = self.apptainer_tmpdir
            bind_option = f"--bind {bind}" if bind else ""
            env_options = " ".join(f"--env {k}={v}" for k, v in env_vars.items())
            options = " ".join(filter(None, [bind_option, env_options]))
            return f"apptainer exec {options} {sif} {command}"
        else:
            # Apptainer 없으면 원본 명령어 그대로
            return command

    def build_apptainer_exec_prefix(self, use_lsdyna: bool = False) -> str:
        """apptainer exec 프리픽스 생성 (멀티노드 MPI용)

        멀티노드에서는 mpirun이 apptainer 바깥에서 실행되므로,
        각 MPI rank가 실행할 'apptainer exec ...' 프리픽스가 필요.

        Returns:
            "apptainer exec --bind ... --env ... /path/to/sif" 또는 "" (SIF 미설정 시)
        """
        if use_lsdyna:
            sif = self.lsdyna_apptainer_sif
            bind = self.lsdyna_apptainer_bind
            env_vars = self.lsdyna_apptainer_env
        else:
            sif = self.apptainer_sif
            bind = self.apptainer_bind
            env_vars = self.apptainer_env

        if not sif:
            return ""

        # APPTAINER_TMPDIR 디렉토리 생성 및 호스트 환경변수 설정
        os.makedirs(self.apptainer_tmpdir, exist_ok=True)
        os.environ["APPTAINER_TMPDIR"] = self.apptainer_tmpdir
        bind_option = f"--bind {bind}" if bind else ""
        env_options = " ".join(f"--env {k}={v}" for k, v in env_vars.items())
        options = " ".join(filter(None, [bind_option, env_options]))
        return f"apptainer exec {options} {sif}"

    # ========================================================================
    # Job 등록 시스템
    # ========================================================================

    def create_runid_directory(
        self,
        scenario_id: str,
        step_number: int,
        doe_index: int,
        job_metadata: Dict[str, Any]
    ) -> str:
        """
        runid 디렉토리 생성 (/data/파일이름/runid_XXXXX/)

        Parameters:
            scenario_id: 시나리오 ID
            step_number: Step 번호
            doe_index: DOE 인덱스
            job_metadata: Job 메타데이터

        Returns:
            runid 디렉토리 경로

        디렉토리 구조:
            /data/{파일이름}/
            ├── runid_00001/
            │   ├── Step001/
            │   │   ├── dynain
            │   │   ├── d3plot01
            │   │   └── .lock  ← 완료 표시
            │   ├── Step002/
            │   └── Step003/
            ├── runid_00002/
            └── ...

        metadata.json 내용:
            {
                "scenario_id": "...",
                "step_number": 1,
                "doe_index": 123,
                "angle": {"roll": 0, "pitch": 0, "yaw": 0},
                "template": "DROP_FIRST"
            }
        """
        runid = f"runid_{doe_index:05d}"
        runid_dir = os.path.join(self.project_dir, runid)
        step_dir = os.path.join(runid_dir, f"Step{step_number:03d}")

        # 디렉토리 생성
        os.makedirs(step_dir, exist_ok=True)

        # metadata.json 작성 (runid 루트에)
        metadata_file = os.path.join(runid_dir, "metadata.json")
        if not os.path.exists(metadata_file):
            metadata = {
                "scenario_id": scenario_id,
                "doe_index": doe_index,
                "runid": runid,
                "created_at": datetime.now().isoformat(),
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

        # Step metadata.json 작성 (Step 디렉토리에)
        step_metadata_file = os.path.join(step_dir, "metadata.json")
        step_metadata = {
            "scenario_id": scenario_id,
            "step_number": step_number,
            "doe_index": doe_index,
            "runid": runid,
            "registered_at": datetime.now().isoformat(),
            **job_metadata
        }

        with open(step_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(step_metadata, f, indent=2)

        # step_config.txt 생성 (공통 모듈 사용)
        angle = job_metadata.get("angle", {"roll": 0, "pitch": 0, "yaw": 0})
        template = job_metadata.get("template", "")
        model_file = self.environment.get("model_file") or \
                     self.runner_config.get("project", {}).get("model_file") or \
                     template or ""
        if not model_file:
            print(f"  Warning: model_file not found for DOE {doe_index}, step_config may be invalid")

        sim_params = self.runner_config.get("simulation_params", {})

        try:
            from Runner.StepConfigBuilder import build_drop_attitude_config
            step_config_content = build_drop_attitude_config(
                model_file=model_file,
                output_dir=step_dir,
                project=scenario_id,
                doe_index=doe_index,
                step_num=step_number,
                mode="DROP",
                condition=f"DOE{doe_index:03d}",
                euler=angle,
                sim_params=sim_params,
                run_directory_mode=False,
            )
            step_config_path = os.path.join(step_dir, "step_config.txt")
            with open(step_config_path, 'w', encoding='utf-8') as scf:
                scf.write(step_config_content)

            # Step 2+: dynaintoinitial.txt도 사전 생성
            if step_number > 1:
                from Runner.StepConfigBuilder import build_dynain_to_initial_config
                prev_dynain = f"../Step{step_number-1:03d}/dynain"
                dti_content = build_dynain_to_initial_config(
                    model_file=model_file,
                    dynain_path=prev_dynain,
                )
                dti_path = os.path.join(step_dir, "dynaintoinitial.txt")
                with open(dti_path, 'w', encoding='utf-8') as dtif:
                    dtif.write(dti_content)
        except Exception as e:
            print(f"  Warning: step_config.txt generation failed for DOE {doe_index}: {e}")

        return step_dir

    def create_lock_file(self, runid_dir: str, step_number: int):
        """
        Lock 파일 생성 (Job 완료 표시)

        Lock 파일:
            /data/{파일이름}/runid_XXXXX/StepXXX/.lock

        내용:
            {
                "completed_at": "2026-01-23T12:45:00",
                "exit_code": 0
            }
        """
        step_dir = os.path.join(runid_dir, f"Step{step_number:03d}")
        lock_file = os.path.join(step_dir, ".lock")

        lock_data = {
            "completed_at": datetime.now().isoformat(),
            "exit_code": 0
        }

        with open(lock_file, 'w', encoding='utf-8') as f:
            json.dump(lock_data, f, indent=2)

    def check_step_completion(self, scenario_id: str, step_number: int, expected_doe_count: int) -> Tuple[int, int]:
        """
        특정 Step의 완료 상태 체크

        Parameters:
            scenario_id: 시나리오 ID
            step_number: Step 번호
            expected_doe_count: 예상 DOE 개수

        Returns:
            (완료된 DOE 개수, 전체 DOE 개수)
        """
        # /data/{파일이름}/runid_*/StepXXX/.lock 파일 카운트
        step_pattern = f"Step{step_number:03d}"
        completed_count = 0

        for runid_dir in Path(self.project_dir).glob("runid_*"):
            lock_file = runid_dir / step_pattern / ".lock"
            if lock_file.exists():
                completed_count += 1

        return completed_count, expected_doe_count

    def wait_for_step_completion(
        self,
        scenario_id: str,
        step_number: int,
        expected_doe_count: int,
        check_interval: int = 60
    ):
        """
        Step 완료 대기 (Polling)

        Parameters:
            scenario_id: 시나리오 ID
            step_number: Step 번호
            expected_doe_count: 예상 DOE 개수
            check_interval: 체크 간격 (초)
        """
        print(f"\n{'='*100}")
        print(f"⏳ Step {step_number} 완료 대기 중... (예상 DOE: {expected_doe_count})")
        print(f"{'='*100}\n")

        while True:
            completed, total = self.check_step_completion(
                scenario_id, step_number, expected_doe_count
            )

            progress = (completed / total * 100) if total > 0 else 0
            print(f"  진행률: {completed}/{total} ({progress:.1f}%) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            if completed >= total:
                print(f"\n✅ Step {step_number} 완료! (총 {completed}개 DOE)")
                break

            time.sleep(check_interval)

    # ========================================================================
    # 결과 수집 시스템
    # ========================================================================

    def collect_results(self, scenario_id: str, step_number: int, target_dir: str):
        """
        결과 수집 (/data/{파일이름}/ → 로컬)

        모든 Lock 파일 확인 후:
            1. /data/{파일이름}/runid_*/StepXXX/.lock 찾기
            2. 해당 Step 디렉토리 → target_dir 복사
            3. 통계 생성
        """
        print(f"\n{'='*100}")
        print(f"📦 결과 수집 시작 - {scenario_id} Step {step_number}")
        print(f"{'='*100}\n")

        # Lock 파일 목록
        step_pattern = f"Step{step_number:03d}"
        lock_files = []

        for runid_dir in sorted(Path(self.project_dir).glob("runid_*")):
            lock_file = runid_dir / step_pattern / ".lock"
            if lock_file.exists():
                lock_files.append((runid_dir, lock_file))

        print(f"총 Lock 파일: {len(lock_files)}개")

        # 결과 디렉토리 생성
        step_results_dir = os.path.join(target_dir, f"Step{step_number:03d}")
        os.makedirs(step_results_dir, exist_ok=True)

        # 각 runid 처리
        for runid_dir, lock_file in lock_files:
            runid = runid_dir.name
            step_dir = runid_dir / step_pattern

            # 결과 복사 (전체 Step 디렉토리)
            doe_result_dir = os.path.join(step_results_dir, runid)
            if os.path.exists(doe_result_dir):
                shutil.rmtree(doe_result_dir)
            shutil.copytree(step_dir, doe_result_dir)

            # metadata.json 읽기
            metadata_file = step_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    doe_index = metadata.get("doe_index", 0)
            else:
                doe_index = 0

            print(f"  {runid} (DOE {doe_index:05d}): 복사 완료")

        print(f"\n✅ 결과 수집 완료: {step_results_dir}")
        print(f"{'='*100}\n")

    # ========================================================================
    # Array Job 제출 (대규모 최적화)
    # ========================================================================

    def submit_step_array_job(
        self,
        scenario: Dict[str, Any],
        step_number: int,
        doe_start: int,
        doe_end: int,
        dependency_job_id: Optional[str] = None
    ) -> str:
        """
        Step Array Job 제출

        Parameters:
            scenario: 시나리오 설정
            step_number: Step 번호
            doe_start: DOE 시작 인덱스 (1-based)
            doe_end: DOE 종료 인덱스 (1-based)
            dependency_job_id: 의존 Job ID

        Returns:
            Job ID

        디렉토리 구조:
            /data/{파일이름}/
            ├── runid_00001/
            │   ├── Step001/
            │   │   ├── metadata.json     ← Step 메타데이터
            │   │   ├── dynain
            │   │   ├── d3plot01
            │   │   └── .lock  ← 완료 표시
            │   ├── Step002/
            │   └── Step003/
            └── runid_00002/

        Array Job 구조:
            #SBATCH --array={doe_start}-{doe_end}

            각 Array Task:
                1. metadata.json 읽기 (DOE 정보)
                2. KooMeshModifier용 txt 파일 작성 (data/result 경로 룰)
                3. KooMeshModifier 실행
                4. Lock 파일 생성
        """
        scenario_id = scenario.get("scenario_id")
        scenario_name = scenario.get("scenario_name")

        job_name = f"{scenario_id}_S{step_number:03d}_Array"

        # 동시 실행 제한 계산
        total_jobs = doe_end - doe_start + 1
        concurrent_limit = self.total_concurrent_jobs

        print(f"\n{'─'*100}")
        print(f"🚀 Array Job 제출: {job_name}")
        print(f"  DOE 범위: {doe_start}-{doe_end} ({total_jobs}개)")
        print(f"  자원 설정:")
        print(f"    - 노드: {self.nodes}개")
        print(f"    - 노드당 Job: {self.jobs_per_node}개")
        print(f"    - Job당 CPU: {self.ncpu_per_job}개")
        print(f"    - 동시 실행 제한: {concurrent_limit}개")
        print(f"    - 예상 Rounds: {(total_jobs + concurrent_limit - 1) // concurrent_limit}회")
        if self.scratch_enabled:
            print(f"    - Scratch Run: 활성 (base: {self.scratch_base})")
        if dependency_job_id:
            print(f"  의존성: {dependency_job_id}")
        print(f"{'─'*100}")

        # Slurm 스크립트 생성
        script_path = os.path.join(self.base_dir, f"slurm_{job_name}.sh")

        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"#SBATCH --job-name={job_name}\n")
            f.write(f"#SBATCH --partition={self.partition}\n")
            f.write(f"#SBATCH --array={doe_start}-{doe_end}%{concurrent_limit}\n")
            f.write(f"#SBATCH --nodes={self.nodes_per_job}\n")
            if self.nodes_per_job >= 2:
                f.write(f"#SBATCH --ntasks-per-node={self.ncpu_per_job}\n")
                f.write(f"#SBATCH --cpus-per-task=1\n")
            else:
                f.write(f"#SBATCH --ntasks={self.ncpu_per_job}\n")
                f.write(f"#SBATCH --cpus-per-task=1\n")
            f.write(f"#SBATCH --mem={self.memory}\n")
            f.write(f"#SBATCH --time={self._seconds_to_slurm_time(self.timeout)}\n")
            f.write(f"#SBATCH --output={job_name}_%A_%a.out\n")
            f.write(f"#SBATCH --error={job_name}_%A_%a.err\n")

            if dependency_job_id:
                f.write(f"#SBATCH --dependency=afterok:{dependency_job_id}\n")

            # APPTAINER_TMPDIR 설정 (job별 격리)
            if self.apptainer_tmpdir:
                f.write(f"\nexport APPTAINER_TMPDIR={self.apptainer_tmpdir}/apptainer_job_${{SLURM_ARRAY_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}\n")
                f.write("mkdir -p $APPTAINER_TMPDIR\n")

            f.write("\n")
            f.write("# ====================================================================\n")
            f.write("# 초기화\n")
            f.write("# ====================================================================\n")
            f.write("\n")
            f.write("# Array Task ID → DOE Index\n")
            f.write("DOE_INDEX=$SLURM_ARRAY_TASK_ID\n")
            f.write("\n")

            f.write("# runid 디렉토리 경로 (NFS 원본)\n")
            f.write(f'RUNID="runid_$(printf %05d $DOE_INDEX)"\n')
            f.write(f'ORIG_RUNID_DIR="{self.project_dir}/$RUNID"\n')
            f.write(f'ORIG_STEP_DIR="$ORIG_RUNID_DIR/Step{step_number:03d}"\n')
            f.write("\n")

            f.write('if [ ! -d "$ORIG_STEP_DIR" ]; then\n')
            f.write('    echo "❌ Step directory not found: $ORIG_STEP_DIR"\n')
            f.write('    exit 1\n')
            f.write('fi\n')
            f.write("\n")

            if self.scratch_enabled:
                f.write("# ====================================================================\n")
                f.write("# Scratch Run 설정 (로컬 디스크에서 실행)\n")
                f.write("# ====================================================================\n")
                f.write("\n")
                f.write("EXIT_CODE=1\n")
                f.write(f'SCRATCH_DIR={self.scratch_base}/$SLURM_JOB_ID/$RUNID/Step{step_number:03d}\n')
                f.write('mkdir -p $SCRATCH_DIR\n')
                f.write('echo "Scratch 디렉토리: $SCRATCH_DIR"\n')
                f.write("\n")
                f.write('# 메타데이터 + config + include 파일 복사\n')
                f.write('cp $ORIG_STEP_DIR/metadata.json $SCRATCH_DIR/\n')
                f.write('cp $ORIG_STEP_DIR/step_config.txt $SCRATCH_DIR/ 2>/dev/null || true\n')
                f.write('cp $ORIG_STEP_DIR/dynaintoinitial.txt $SCRATCH_DIR/ 2>/dev/null || true\n')
                f.write('cp $ORIG_STEP_DIR/*.k $SCRATCH_DIR/ 2>/dev/null || true\n')
                f.write(f'cp {self.project_dir}/$RUNID/metadata.json $SCRATCH_DIR/../ 2>/dev/null || true\n')
                f.write('echo "메타데이터/config/include 복사 완료"\n')
                f.write("\n")

                if step_number > 1:
                    f.write(f'# 이전 Step dynain 복사\n')
                    f.write(f'PREV_STEP_DIR="$ORIG_RUNID_DIR/Step{step_number-1:03d}"\n')
                    f.write(f'SCRATCH_PREV_DIR={self.scratch_base}/$SLURM_JOB_ID/$RUNID/Step{step_number-1:03d}\n')
                    f.write('mkdir -p $SCRATCH_PREV_DIR\n')
                    f.write('if [ -f "$PREV_STEP_DIR/dynain" ]; then\n')
                    f.write('    cp $PREV_STEP_DIR/dynain $SCRATCH_PREV_DIR/\n')
                    f.write('    echo "이전 Step dynain 복사 완료"\n')
                    f.write('else\n')
                    f.write('    echo "❌ 이전 Step dynain 없음: $PREV_STEP_DIR/dynain"\n')
                    f.write('    exit 1\n')
                    f.write('fi\n')
                    f.write("\n")

                cleanup_flag = 'true' if self.scratch_cleanup else 'false'
                f.write('# EXIT trap: 결과를 NFS로 복사\n')
                f.write('cleanup() {\n')
                f.write('    echo ""\n')
                f.write('    echo "========================================"\n')
                f.write('    echo "결과 복사: scratch → NFS 원본 위치"\n')
                f.write('    echo "========================================"\n')
                f.write('    rsync -a $SCRATCH_DIR/ $ORIG_STEP_DIR/ 2>/dev/null || \\\n')
                f.write('        cp -r $SCRATCH_DIR/* $ORIG_STEP_DIR/ 2>/dev/null || true\n')
                f.write('    echo "결과 복사 완료"\n')
                f.write(f'    if [ "{cleanup_flag}" = "true" ] && [ $EXIT_CODE -eq 0 ]; then\n')
                f.write(f'        rm -rf {self.scratch_base}/$SLURM_JOB_ID/$RUNID\n')
                f.write('        echo "Scratch 디렉토리 정리 완료"\n')
                f.write('    else\n')
                f.write('        echo "Scratch 디렉토리 유지: $SCRATCH_DIR"\n')
                f.write('    fi\n')
                f.write('}\n')
                f.write('trap cleanup EXIT\n')
                f.write("\n")
                f.write('# 작업 디렉토리 → scratch\n')
                f.write('STEP_DIR="$SCRATCH_DIR"\n')
                f.write('RUNID_DIR="$(dirname $SCRATCH_DIR)"\n')
            else:
                f.write('# NFS에서 직접 실행\n')
                f.write('STEP_DIR="$ORIG_STEP_DIR"\n')
                f.write('RUNID_DIR="$ORIG_RUNID_DIR"\n')

            f.write("\n")
            f.write("# ====================================================================\n")
            f.write("# metadata.json 읽기\n")
            f.write("# ====================================================================\n")
            f.write("\n")
            f.write('METADATA_FILE="$ORIG_STEP_DIR/metadata.json"\n')
            f.write("\n")
            f.write('if [ ! -f "$METADATA_FILE" ]; then\n')
            f.write('    echo "❌ Metadata not found: $METADATA_FILE"\n')
            f.write('    exit 1\n')
            f.write('fi\n')
            f.write("\n")

            f.write("# JSON 파싱 (jq 사용)\n")
            f.write('TEMPLATE=$(jq -r .template "$METADATA_FILE")\n')
            f.write('ROLL=$(jq -r .angle.roll "$METADATA_FILE")\n')
            f.write('PITCH=$(jq -r .angle.pitch "$METADATA_FILE")\n')
            f.write('YAW=$(jq -r .angle.yaw "$METADATA_FILE")\n')
            f.write("\n")

            f.write("# ====================================================================\n")
            f.write("# step_config.txt 확인 (사전 생성됨, StepConfigBuilder 공통 모듈)\n")
            f.write("# ====================================================================\n")
            f.write("\n")
            f.write('INPUT_TXT="$STEP_DIR/step_config.txt"\n')
            f.write('if [ ! -f "$INPUT_TXT" ]; then\n')
            f.write('    echo "step_config.txt not found: $INPUT_TXT"\n')
            f.write('    exit 1\n')
            f.write('fi\n')
            f.write("\n")

            f.write("# ====================================================================\n")
            f.write("# KooMeshModifier 실행 (DROP_ATTITUDE or DROP_CUMULATIVE)\n")
            f.write("# ====================================================================\n")
            f.write("\n")
            f.write('cd "$STEP_DIR"\n')
            f.write("\n")
            f.write('echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"\n')
            f.write(f'echo "Step {step_number}: KooMeshModifier + LS-DYNA 실행"\n')
            f.write('echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"\n')
            f.write("\n")

            # Step 2+ : DYNAIN_TO_INITIAL 먼저 실행
            if step_number > 1:
                f.write("# ====================================================================\n")
                f.write("# Step 2+: DYNAIN_TO_INITIAL 실행 (이전 Step dynain → Initial)\n")
                f.write("# ====================================================================\n")
                f.write("\n")
                f.write('echo "1/3: DYNAIN_TO_INITIAL 실행 (이전 dynain 변환)..."\n')
                f.write("\n")

                f.write(f"# 이전 Step dynain 확인\n")
                f.write(f'PREV_DYNAIN="../Step{step_number-1:03d}/dynain"\n')
                f.write('if [ ! -f "$PREV_DYNAIN" ]; then\n')
                f.write('    echo "❌ 이전 Step dynain 없음: $PREV_DYNAIN"\n')
                f.write('    exit 1\n')
                f.write('fi\n')
                f.write("\n")

                f.write("# dynaintoinitial.txt 확인 (사전 생성됨)\n")
                f.write('DTI_TXT="$STEP_DIR/dynaintoinitial.txt"\n')
                f.write('if [ ! -f "$DTI_TXT" ]; then\n')
                f.write('    echo "dynaintoinitial.txt not found: $DTI_TXT"\n')
                f.write('    exit 1\n')
                f.write('fi\n')
                f.write("\n")

                f.write("# DYNAIN_TO_INITIAL 실행\n")
                km_cmd = self.wrap_with_apptainer(f'{self.koomeshmodifier_path} --input="$DTI_TXT"')
                f.write(f"{km_cmd}\n")
                f.write("\n")

                f.write('DTI_EXIT=$?\n')
                f.write('if [ $DTI_EXIT -ne 0 ]; then\n')
                f.write('    echo "❌ DYNAIN_TO_INITIAL 실패"\n')
                f.write('    exit $DTI_EXIT\n')
                f.write('fi\n')
                f.write("\n")

                f.write('echo "✅ DYNAIN_TO_INITIAL 완료 (Initial 상태 생성)"\n')
                f.write("\n")

            # DROP_ATTITUDE 실행
            f.write("# ====================================================================\n")
            if step_number == 1:
                f.write("# Step 1: DROP_FIRST 실행\n")
                f.write('echo "1/2: DROP_FIRST 실행 (메쉬 회전 + DR 추가)..."\n')
            else:
                f.write("# Step 2+: DROP_CUMULATIVE 실행\n")
                f.write('echo "2/3: DROP_CUMULATIVE 실행 (메쉬 회전 + DR 추가)..."\n')
            f.write("# ====================================================================\n")
            f.write("\n")

            f.write("# DROP_ATTITUDE 설정 파일 실행\n")
            km_cmd = self.wrap_with_apptainer(f'{self.koomeshmodifier_path} --input="$INPUT_TXT"')
            f.write(f"{km_cmd}\n")
            f.write("\n")

            f.write("KM_EXIT=$?\n")
            f.write('if [ $KM_EXIT -ne 0 ]; then\n')
            f.write('    echo "❌ KooMeshModifier (DROP_ATTITUDE) 실패"\n')
            f.write('    exit $KM_EXIT\n')
            f.write('fi\n')
            f.write("\n")

            f.write('echo "✅ KooMeshModifier 완료 (회전된 .k 파일 생성)"\n')
            f.write("\n")

            f.write("# ====================================================================\n")
            f.write("# 생성된 .k 파일 찾기 (SimulationAutomation 메타데이터 활용)\n")
            f.write("# ====================================================================\n")
            f.write("\n")
            f.write("# KooMeshModifier가 생성한 .k 파일 찾기 (가장 최근 파일)\n")
            f.write('OUTPUT_K=$(find . -maxdepth 1 -name "*.k" -type f -printf "%T@ %p\\n" | sort -rn | head -1 | cut -d" " -f2-)\n')
            f.write("\n")
            f.write('if [ -z "$OUTPUT_K" ] || [ ! -f "$OUTPUT_K" ]; then\n')
            f.write('    echo "❌ KooMeshModifier 출력 .k 파일을 찾을 수 없음"\n')
            f.write('    exit 1\n')
            f.write('fi\n')
            f.write("\n")
            f.write('echo "  생성된 .k 파일: $OUTPUT_K"\n')
            f.write("\n")

            f.write("# ====================================================================\n")
            f.write("# LS-DYNA 실행\n")
            f.write("# ====================================================================\n")
            f.write("\n")
            if step_number == 1:
                f.write('echo "2/2: LS-DYNA 실행 (낙하 시뮬레이션)..."\n')
            else:
                f.write('echo "3/3: LS-DYNA 실행 (누적 낙하 시뮬레이션)..."\n')
            f.write("\n")

            f.write("# LS-DYNA 실행 (MPI 병렬)\n")
            if self.nodes_per_job >= 2:
                total_ncpu = self.ncpu_per_job * self.nodes_per_job
                appt_prefix = self.build_apptainer_exec_prefix(use_lsdyna=True)

                if self.mpi_launcher == "srun":
                    # srun 방식: Slurm이 직접 프로세스 spawn, 호스트 MPI 불필요
                    # srun --mpi=pmi2 apptainer exec ... lsdyna i=... memory=...
                    if appt_prefix:
                        lsdyna_cmd = (
                            f'srun --mpi=pmi2 '
                            f'{appt_prefix} {self.lsdyna_path} i="$OUTPUT_K" memory={self.lsdyna_memory}'
                        )
                    else:
                        lsdyna_cmd = (
                            f'srun --mpi=pmi2 '
                            f'{self.lsdyna_path} i="$OUTPUT_K" memory={self.lsdyna_memory}'
                        )
                else:
                    # mpirun 방식: 호스트 MPI가 프로세스 spawn
                    # mpirun -np {ncpu} -hostfile $SLURM_NODEFILE apptainer exec ... lsdyna i=... memory=...
                    if appt_prefix:
                        lsdyna_cmd = (
                            f'{self.mpi_path} -np {total_ncpu} -hostfile $SLURM_NODEFILE '
                            f'{appt_prefix} {self.lsdyna_path} i="$OUTPUT_K" memory={self.lsdyna_memory}'
                        )
                    else:
                        lsdyna_cmd = (
                            f'{self.mpi_path} -np {total_ncpu} -hostfile $SLURM_NODEFILE '
                            f'{self.lsdyna_path} i="$OUTPUT_K" memory={self.lsdyna_memory}'
                        )
            else:
                # 단일노드: 기존 방식 (apptainer 안에서 mpirun)
                lsdyna_cmd = self.wrap_with_apptainer(
                    f'{self.mpi_path} -np {self.ncpu} {self.lsdyna_path} i="$OUTPUT_K" memory={self.lsdyna_memory} ncpu={self.ncpu}',
                    use_lsdyna=True
                )
            f.write(f"{lsdyna_cmd}\n")
            f.write("\n")

            f.write("LSDYNA_EXIT=$?\n")
            f.write('if [ $LSDYNA_EXIT -ne 0 ]; then\n')
            f.write('    echo "❌ LS-DYNA 실패"\n')
            f.write('    exit $LSDYNA_EXIT\n')
            f.write('fi\n')
            f.write("\n")

            f.write('echo "✅ LS-DYNA 완료 (dynain, d3plot* 생성)"\n')
            f.write("\n")

            f.write("# 결과 파일 확인\n")
            f.write('if [ ! -f "dynain" ]; then\n')
            f.write('    echo "⚠️  경고: dynain 파일 없음"\n')
            f.write('fi\n')
            f.write('if [ ! -f "d3plot01" ]; then\n')
            f.write('    echo "⚠️  경고: d3plot01 파일 없음"\n')
            f.write('fi\n')
            f.write("\n")

            if self.scratch_enabled:
                f.write("EXIT_CODE=0\n")
            else:
                f.write("EXIT_CODE=0\n")
            f.write("\n")

            f.write("# ====================================================================\n")
            f.write("# Lock 파일 생성 (완료 표시)\n")
            f.write("# ====================================================================\n")
            f.write("\n")
            f.write('LOCK_FILE="$STEP_DIR/.lock"\n')
            f.write('cat > "$LOCK_FILE" << EOF\n')
            f.write('{\n')
            f.write('  "completed_at": "$(date -Iseconds)",\n')
            f.write('  "exit_code": $EXIT_CODE\n')
            f.write('}\n')
            f.write('EOF\n')
            f.write("\n")

            f.write(f'echo "✅ $RUNID Step {step_number} 완료 (Lock: $LOCK_FILE)"\n')
            f.write("\n")
            f.write("exit $EXIT_CODE\n")

        os.chmod(script_path, 0o755)

        # sbatch 제출
        result = subprocess.run(
            ["sbatch", "--parsable", script_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ 제출 실패: {result.stderr}")
            return "FAILED"

        job_id = result.stdout.strip()
        print(f"✅ Job ID: {job_id}")

        return job_id

    # ========================================================================
    # 전체 워크플로
    # ========================================================================

    def run(self):
        """
        전체 워크플로 실행 (모든 시나리오)

        KooChainRun CLI에서 호출되는 메인 메서드
        """
        if not self.scenarios:
            print("⚠️  경고: 실행할 시나리오가 없습니다.")
            return

        # 모든 시나리오 실행
        for scenario in self.scenarios:
            self.run_large_scale_workflow(scenario)

    def run_large_scale_workflow(self, scenario: Dict[str, Any]):
        """
        대규모 워크플로 실행

        1. runid 디렉토리 생성 (모든 DOE × Step)
        2. Step 1 Array Job 제출
        3. Step 1 완료 대기 (옵션)
        4. 결과 수집 (옵션)
        5. Step 2 Array Job 제출
        6. 반복...
        """
        scenario_id = scenario.get("scenario_id")
        scenario_name = scenario.get("scenario_name")
        steps = scenario.get("steps", [])

        print(f"\n{'='*100}")
        print(f"🚀 대규모 워크플로 시작 - {scenario_name}")
        print(f"{'='*100}\n")

        # DOE 개수 계산
        doe_indices = sorted(set(step.get("doe_index") for step in steps))
        doe_count = len(doe_indices)

        print(f"시나리오: {scenario_id}")
        print(f"총 DOE 수: {doe_count}")
        print(f"총 Step 수: {len(steps) // doe_count if doe_count > 0 else 0}")
        print(f"데이터 경로: {self.project_dir}")
        print()

        # Step별로 처리
        num_steps = len(steps) // doe_count if doe_count > 0 else 0
        prev_job_id = None

        for step_num in range(1, num_steps + 1):
            print(f"\n{'─'*100}")
            print(f"Step {step_num} 처리")
            print(f"{'─'*100}")

            # 1. runid 디렉토리 생성
            print(f"\n1️⃣  runid 디렉토리 생성 중...")
            for step_cfg in steps:
                if step_cfg.get("step_number") == step_num:
                    step_dir = self.create_runid_directory(
                        scenario_id,
                        step_num,
                        step_cfg.get("doe_index"),
                        {
                            "angle": step_cfg.get("angle"),
                            "template": step_cfg.get("template")
                        }
                    )

            print(f"✅ runid 디렉토리 생성 완료: {doe_count}개")

            # 2. Array Job 제출
            print(f"\n2️⃣  Array Job 제출 중...")
            job_id = self.submit_step_array_job(
                scenario,
                step_num,
                doe_start=min(doe_indices),
                doe_end=max(doe_indices),
                dependency_job_id=prev_job_id
            )

            prev_job_id = job_id

            # 3. 완료 대기 (옵션)
            # self.wait_for_step_completion(scenario_id, step_num, doe_count)

            # 4. 결과 수집 (옵션)
            # target_dir = os.path.join(self.base_dir, "results", scenario_id)
            # self.collect_results(scenario_id, step_num, target_dir)

        print(f"\n{'='*100}")
        print(f"✅ 모든 Array Job 제출 완료!")
        print(f"{'='*100}\n")

        print(f"제출된 Job ID:")
        print(f"  최종 Job ID: {prev_job_id}")
        print()

        print(f"진행 상황 모니터링:")
        print(f"  squeue -u $USER")
        print(f"  find {self.project_dir} -name '.lock' | wc -l")

    # ========================================================================
    # 유틸리티
    # ========================================================================

    def _seconds_to_slurm_time(self, seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def print_statistics(self):
        """통계 출력"""
        print(f"\n{'='*100}")
        print(f"📊 프로젝트 통계 - {self.project_name}")
        print(f"{'='*100}\n")

        # runid 디렉토리 개수
        runid_dirs = list(Path(self.project_dir).glob("runid_*"))
        print(f"등록된 runid: {len(runid_dirs)}개")

        # Lock 개수 (모든 Step 합산)
        lock_files = list(Path(self.project_dir).glob("runid_*/Step*/.lock"))
        print(f"완료된 Step: {len(lock_files)}개")

        # Step별 진행률
        print(f"\nStep별 완료 상황:")
        for step_num in range(1, 10):  # 최대 Step 9까지 체크
            step_pattern = f"Step{step_num:03d}"
            step_locks = list(Path(self.project_dir).glob(f"runid_*/{step_pattern}/.lock"))
            if len(step_locks) > 0:
                progress = len(step_locks) / len(runid_dirs) * 100 if len(runid_dirs) > 0 else 0
                print(f"  Step {step_num}: {len(step_locks)}/{len(runid_dirs)} ({progress:.1f}%)")

        print(f"\n디렉토리:")
        print(f"  프로젝트: {self.project_dir}")
        print(f"{'='*100}\n")


def main():
    parser = argparse.ArgumentParser(description="대규모 DOE 관리 시스템")
    parser.add_argument("runner_config", help="runner_config.json 경로")
    parser.add_argument("--data-root", default="/data", help="데이터 루트 디렉토리")

    # Slurm 자원 설정
    parser.add_argument("--nodes", type=int, default=1, help="사용할 노드 수 (기본: 1)")
    parser.add_argument("--jobs-per-node", type=int, default=1, help="노드당 동시 실행 Job 수 (기본: 1)")
    parser.add_argument("--ncpu-per-job", type=int, default=16, help="각 Job이 사용할 CPU 수 (기본: 16)")

    # 기타 옵션
    parser.add_argument("--stats", action="store_true", help="통계 출력")
    parser.add_argument("--collect", type=int, metavar="STEP", help="결과 수집 (Step 번호)")
    parser.add_argument("--wait", type=int, metavar="STEP", help="Step 완료 대기")
    args = parser.parse_args()

    manager = LargeScaleDOEManager(
        args.runner_config,
        args.data_root,
        nodes=args.nodes,
        jobs_per_node=args.jobs_per_node,
        ncpu_per_job=args.ncpu_per_job
    )

    if args.stats:
        manager.print_statistics()
        return

    if args.collect:
        # 첫 번째 시나리오의 특정 Step 결과 수집
        if manager.scenarios:
            scenario = manager.scenarios[0]
            target_dir = os.path.join(manager.base_dir, "results", scenario.get("scenario_id"))
            manager.collect_results(scenario.get("scenario_id"), args.collect, target_dir)
        return

    if args.wait:
        # Step 완료 대기
        if manager.scenarios:
            scenario = manager.scenarios[0]
            scenario_id = scenario.get("scenario_id")
            steps = scenario.get("steps", [])
            doe_count = len(set(s.get("doe_index") for s in steps))
            manager.wait_for_step_completion(scenario_id, args.wait, doe_count)
        return

    # 기본: 전체 워크플로 실행
    if manager.scenarios:
        manager.run_large_scale_workflow(manager.scenarios[0])


if __name__ == "__main__":
    main()
