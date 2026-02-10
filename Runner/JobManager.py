#!/usr/bin/env python3
"""
JobManager - Slurm Job 관리 모듈

제출된 Slurm 작업의 추적, 취소, 재실행, 실패 진단을 담당합니다.

Author: koo.park
"""

import os
import json
import subprocess
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class JobManager:
    """Slurm Job 관리자 - 작업 추적, 취소, 재실행, 진단"""

    def __init__(self, test_dir: str):
        self.test_dir = Path(test_dir).resolve()
        self.jobs_file = self.test_dir / "jobs.json"
        self.runner_config_path = self.test_dir / "runner_config.json"

    def load_jobs(self) -> dict:
        """jobs.json 로드"""
        if not self.jobs_file.exists():
            raise FileNotFoundError(f"jobs.json not found: {self.jobs_file}")
        with open(self.jobs_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_jobs(self, jobs_data: dict):
        """jobs.json 저장"""
        with open(self.jobs_file, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, indent=2, ensure_ascii=False)

    def load_runner_config(self) -> dict:
        """runner_config.json 로드"""
        if not self.runner_config_path.exists():
            raise FileNotFoundError(f"runner_config.json not found: {self.runner_config_path}")
        with open(self.runner_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _query_slurm_status(self, job_id: str) -> str:
        """sacct로 Slurm 작업 상태 조회"""
        try:
            result = subprocess.run(
                ["sacct", "-j", job_id, "--format=State", "--noheader", "--parsable2"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                # sacct는 여러 줄 반환 가능 (batch step 등), 첫 줄 사용
                state = result.stdout.strip().split('\n')[0].strip()
                return state
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # sacct 실패 시 squeue로 fallback
        try:
            result = subprocess.run(
                ["squeue", "-j", job_id, "--noheader", "--format=%T"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0].strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return "UNKNOWN"

    def _generate_alias(self, runner_config: dict, doe_index: int, step_num: int) -> str:
        """CumulativeScenarioRunner._generate_alias()와 동일한 패턴"""
        project = runner_config["project"]["name"]
        total_steps = runner_config["scenario"]["total_steps"]
        step_config = runner_config["scenario"]["steps"][step_num - 1]
        mode = step_config["mode"]
        condition = step_config["condition"]
        return f"{project}_CUM{total_steps:03d}_DOE{doe_index:03d}_S{step_num:03d}_{mode}_{condition}"

    def _load_simulation_index(self, runner_config: dict) -> dict:
        """simulation_index.json 로드"""
        index_file = runner_config["project"].get("index_file")
        if index_file and os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return {"scenarios": [{"runs": {}}]}

    def _find_log_file(self, output_dir: str, doe_idx: int) -> Optional[str]:
        """DOE의 가장 최근 로그 파일 찾기"""
        pattern = os.path.join(output_dir, "slurm_scripts", f"doe_{doe_idx:03d}_*.log")
        log_files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        return log_files[0] if log_files else None

    def _check_log_for_license_error(self, log_file: str) -> bool:
        """로그 파일에서 라이선스 에러 패턴 확인"""
        patterns = [
            "LSTC_FILE", "license", "License checkout",
            "Cannot connect to license server"
        ]
        try:
            with open(log_file, 'r', errors='ignore') as f:
                content = f.read()
                content_lower = content.lower()
                for pattern in patterns:
                    if pattern.lower() in content_lower:
                        return True
        except Exception:
            pass
        return False

    def _get_log_error_excerpt(self, log_file: str) -> str:
        """로그 파일에서 에러 관련 부분 발췌"""
        try:
            with open(log_file, 'r', errors='ignore') as f:
                lines = f.readlines()

            # ERROR 또는 FATAL 포함 줄 찾기
            error_lines = []
            for i, line in enumerate(lines):
                if any(kw in line for kw in ['[ERROR]', 'FATAL', 'MPI_ABORT', 'Error termination']):
                    start = max(0, i - 1)
                    end = min(len(lines), i + 3)
                    error_lines.extend(lines[start:end])
                    if len(error_lines) > 10:
                        break

            if error_lines:
                return ''.join(error_lines).strip()
        except Exception:
            pass
        return ""

    # ========================================================================
    # 핵심 기능: cancel_all_jobs
    # ========================================================================

    def cancel_all_jobs(self) -> Dict[int, dict]:
        """모든 작업 취소"""
        jobs_data = self.load_jobs()
        results = {}

        for doe_key, job_info in jobs_data.get("jobs", {}).items():
            doe_idx = int(doe_key)
            job_id = job_info.get("job_id")

            if not job_id:
                results[doe_idx] = {"job_id": None, "cancel_result": "no_job_id"}
                continue

            # 현재 상태 확인
            slurm_state = self._query_slurm_status(job_id)

            if slurm_state in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT",
                                "NODE_FAIL", "OUT_OF_MEMORY", "UNKNOWN"):
                results[doe_idx] = {
                    "job_id": job_id,
                    "cancel_result": "already_done",
                    "slurm_state": slurm_state
                }
                continue

            # scancel 실행
            try:
                result = subprocess.run(
                    ["scancel", job_id],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    results[doe_idx] = {"job_id": job_id, "cancel_result": "success"}
                    jobs_data["jobs"][doe_key]["status"] = "cancelled"
                else:
                    results[doe_idx] = {
                        "job_id": job_id,
                        "cancel_result": "error",
                        "error": result.stderr.strip()
                    }
            except Exception as e:
                results[doe_idx] = {"job_id": job_id, "cancel_result": "error", "error": str(e)}

        # jobs.json 업데이트
        self._save_jobs(jobs_data)
        return results

    # ========================================================================
    # 핵심 기능: get_doe_status
    # ========================================================================

    def get_doe_status(self) -> Dict[int, dict]:
        """모든 DOE의 완료/실패/중단 상태 분석"""
        jobs_data = self.load_jobs()
        runner_config = self.load_runner_config()

        output_dir = runner_config["project"]["output_dir"]
        total_steps = runner_config["scenario"]["total_steps"]
        doe_count = runner_config["scenario"]["doe_count"]

        sim_index = self._load_simulation_index(runner_config)
        runs = sim_index.get("scenarios", [{}])[0].get("runs", {})

        results = {}

        for doe_idx in range(1, doe_count + 1):
            doe_key = str(doe_idx)
            job_info = jobs_data.get("jobs", {}).get(doe_key, {})
            job_id = job_info.get("job_id")

            # Slurm 상태 조회
            slurm_state = self._query_slurm_status(job_id) if job_id else "UNKNOWN"

            # simulation_index에서 step별 상태 확인
            steps_completed = 0
            steps_failed = 0
            has_running = False

            for step_num in range(1, total_steps + 1):
                alias = self._generate_alias(runner_config, doe_idx, step_num)
                run_info = runs.get(alias, {})
                status = run_info.get("status", "not_found")

                if status == "completed":
                    # 실제 출력 파일 존재 확인
                    run_folder = run_info.get("folder", "")
                    if run_folder:
                        dynain_path = os.path.join(output_dir, run_folder, "dynain")
                        if os.path.exists(dynain_path):
                            steps_completed += 1
                        else:
                            steps_failed += 1
                    else:
                        steps_completed += 1
                elif status == "failed":
                    steps_failed += 1
                elif status == "running":
                    has_running = True

            # DOE 상태 분류
            if steps_completed == total_steps:
                doe_status = "completed"
            elif slurm_state in ("RUNNING", "PENDING"):
                doe_status = "running"
            elif slurm_state in ("CANCELLED", "TIMEOUT", "NODE_FAIL", "OUT_OF_MEMORY"):
                doe_status = "killed"
            elif slurm_state == "FAILED" or steps_failed > 0:
                # 라이선스 에러 확인
                log_file = self._find_log_file(output_dir, doe_idx)
                if log_file and self._check_log_for_license_error(log_file):
                    doe_status = "license_error"
                else:
                    doe_status = "failed"
            elif has_running and slurm_state not in ("RUNNING", "PENDING"):
                doe_status = "killed"
            else:
                doe_status = "not_started"

            results[doe_idx] = {
                "status": doe_status,
                "slurm_state": slurm_state,
                "steps_completed": steps_completed,
                "steps_total": total_steps,
                "job_id": job_id
            }

        return results

    # ========================================================================
    # 핵심 기능: resubmit_does
    # ========================================================================

    def resubmit_does(self, doe_indices: List[int]) -> Dict[int, str]:
        """특정 DOE만 재제출 (기존 slurm script 재활용)"""
        jobs_data = self.load_jobs()
        runner_config = self.load_runner_config()
        output_dir = runner_config["project"]["output_dir"]

        resubmitted = {}

        for doe_idx in doe_indices:
            doe_key = str(doe_idx)
            job_info = jobs_data.get("jobs", {}).get(doe_key, {})
            script_path = job_info.get("script_path")

            if not script_path or not os.path.exists(script_path):
                # slurm script가 없으면 기본 경로 시도
                script_path = os.path.join(output_dir, "slurm_scripts", f"run_doe_{doe_idx:03d}.sh")

            if not os.path.exists(script_path):
                print(f"  DOE {doe_idx:3d}: slurm script 없음 ({script_path})")
                continue

            # sbatch 재제출
            try:
                result = subprocess.run(
                    ["sbatch", script_path],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    new_job_id = result.stdout.strip().split()[-1]
                    resubmitted[doe_idx] = new_job_id

                    # jobs.json 업데이트
                    jobs_data["jobs"][doe_key] = {
                        "job_id": new_job_id,
                        "job_name": job_info.get("job_name", f"DOE{doe_idx:03d}"),
                        "status": "resubmitted",
                        "submitted_at": datetime.now().isoformat(),
                        "script_path": script_path,
                        "prev_job_id": job_info.get("job_id")
                    }
                    print(f"  DOE {doe_idx:3d}: 재제출 완료 (job {new_job_id})")
                else:
                    print(f"  DOE {doe_idx:3d}: 재제출 실패 - {result.stderr.strip()}")
            except FileNotFoundError:
                print(f"  DOE {doe_idx:3d}: sbatch 명령어 없음")
                break

        # jobs.json 저장
        self._save_jobs(jobs_data)
        return resubmitted

    # ========================================================================
    # 핵심 기능: diagnose_failures
    # ========================================================================

    def diagnose_failures(self) -> List[dict]:
        """실패 DOE 원인 진단"""
        status_map = self.get_doe_status()
        runner_config = self.load_runner_config()
        output_dir = runner_config["project"]["output_dir"]

        diagnoses = []

        for doe_idx, info in sorted(status_map.items()):
            if info["status"] in ("completed", "running"):
                continue

            log_file = self._find_log_file(output_dir, doe_idx)
            log_excerpt = ""
            cause = info["status"]  # 기본값

            if log_file:
                log_excerpt = self._get_log_error_excerpt(log_file)

                # 세부 원인 분류
                try:
                    with open(log_file, 'r', errors='ignore') as f:
                        content = f.read().lower()

                    if any(p in content for p in ['lstc_file', 'license', 'license checkout']):
                        cause = "license_error"
                    elif 'mpi_abort' in content and 'license' not in content:
                        cause = "mpi_error"
                    elif 'timed out' in content or 'timeout' in content.lower():
                        cause = "timeout"
                    elif 'no space left' in content:
                        cause = "disk_full"
                    elif 'out of memory' in content or 'oom' in content:
                        cause = "out_of_memory"
                    elif 'squashfuse' in content or 'libfuse' in content:
                        cause = "apptainer_error"
                    elif info["slurm_state"] == "CANCELLED":
                        cause = "cancelled"
                    elif info["slurm_state"] == "TIMEOUT":
                        cause = "slurm_timeout"
                    elif info["status"] == "not_started":
                        cause = "not_started"
                except Exception:
                    pass

            diagnoses.append({
                "doe": doe_idx,
                "status": info["status"],
                "slurm_state": info["slurm_state"],
                "cause": cause,
                "steps_completed": info["steps_completed"],
                "steps_total": info["steps_total"],
                "log_excerpt": log_excerpt,
                "job_id": info.get("job_id")
            })

        return diagnoses
