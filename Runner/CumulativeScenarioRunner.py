#!/usr/bin/env python3
"""
Cumulative Scenario Runner - 독립 실행자

SIMULATION_AUTOMATION에서 생성한 runner_config.json을 읽고
실제 시뮬레이션을 순차 실행합니다.

Usage:
    python CumulativeScenarioRunner.py runner_config.json [--resume] [--doe=N]

Author: koo.park
Email: koo.park@samsung.com
Group: CAE
"""

import os
import sys
import json
import subprocess
import time
import logging
import argparse
import hashlib
import uuid
import fcntl
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


def _flock_with_timeout(fd, operation, timeout=120):
    """fcntl.flock with timeout — NFS stale lock 무한 대기 방지

    Args:
        fd: file descriptor
        operation: fcntl.LOCK_SH, fcntl.LOCK_EX, fcntl.LOCK_UN
        timeout: 최대 대기 시간 (초), 기본 120초

    Raises:
        TimeoutError: timeout 초 내에 lock 획득 실패
    """
    if operation == fcntl.LOCK_UN:
        fcntl.flock(fd, operation)
        return
    deadline = time.time() + timeout
    while True:
        try:
            fcntl.flock(fd, operation | fcntl.LOCK_NB)
            return  # lock 획득 성공
        except (BlockingIOError, OSError):
            if time.time() >= deadline:
                raise TimeoutError(
                    f"flock 획득 실패 (timeout={timeout}s). "
                    f"NFS stale lock 가능성 — lock 파일 삭제 후 재시도 필요")
            time.sleep(1)


def _semaphore_acquire(lock_dir, max_concurrency, timeout=120, poll_interval=1.0):
    """Token-file semaphore — 동시 max_concurrency개까지만 진입 허용.

    NFS-safe (O_CREAT|O_EXCL은 NFSv3+에서 atomic). 글로벌 flock과 달리
    여러 잡이 동시 작업 가능, 단 N개 cap.

    동작:
      lock_dir/.stage_out.token_00, _01, ... _<N-1>  토큰 파일 N개
      각 잡이 그 중 하나를 O_EXCL로 생성 → 성공하면 잡음
      모두 점유면 poll_interval 후 재시도, deadline 도달 시 TimeoutError

    Args:
        lock_dir: 토큰 파일 두는 디렉토리 (output_dir 같이 공유 위치)
        max_concurrency: 동시 진입 허용 수 (>= 1)
        timeout: 토큰 획득 timeout (초)
        poll_interval: 재시도 간격 (초)

    Returns:
        (fd, token_path): _semaphore_release에 그대로 전달
    """
    os.makedirs(lock_dir, exist_ok=True)
    deadline = time.time() + timeout
    while True:
        for i in range(max_concurrency):
            token = os.path.join(lock_dir, f".stage_out.token_{i:02d}")
            try:
                fd = os.open(token, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o644)
                return fd, token
            except FileExistsError:
                continue
        if time.time() >= deadline:
            raise TimeoutError(
                f"semaphore 획득 실패 (timeout={timeout}s, "
                f"max_concurrency={max_concurrency}). "
                f"stale token 가능성 — {lock_dir}/.stage_out.token_* 확인")
        time.sleep(poll_interval)


def _semaphore_release(fd, token):
    """semaphore 토큰 반환. 예외는 무시 (best-effort cleanup)."""
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        os.unlink(token)
    except OSError:
        pass


class ApptainerWrapper:
    """Apptainer 컨테이너 래핑 유틸리티"""

    def __init__(self, config: Dict[str, Any]):
        env = config.get("environment", {})
        self.apptainer_sif = env.get("apptainer_sif")
        self.apptainer_bind = env.get("apptainer_bind", "/data:/data")
        self.lsdyna_apptainer_sif = env.get("lsdyna_apptainer_sif")
        self.lsdyna_apptainer_bind = env.get("lsdyna_apptainer_bind", "/data:/data")
        self.lsdyna_apptainer_env = env.get("lsdyna_apptainer_env", {})
        self.apptainer_env = env.get("apptainer_env", {})
        self.nodes_per_job = env.get("nodes_per_job", 1)
        # APPTAINER_TMPDIR: 노드 로컬 디스크 사용 (NFS 충돌 방지)
        # Job별 고유 디렉토리로 동시 실행 시 충돌 방지
        base_tmpdir = env.get("apptainer_tmpdir", "/opt/tmp")
        job_id = os.environ.get("SLURM_JOB_ID", str(os.getpid()))
        self.apptainer_tmpdir = os.path.join(base_tmpdir, f"apptainer_job_{job_id}")

    def wrap_command(self, cmd: List[str], use_lsdyna: bool = False, pwd: str = None) -> List[str]:
        """명령어를 apptainer exec로 래핑"""
        if use_lsdyna:
            sif = self.lsdyna_apptainer_sif
            bind = self.lsdyna_apptainer_bind
            env_vars = self.lsdyna_apptainer_env
        else:
            sif = self.apptainer_sif
            bind = self.apptainer_bind
            env_vars = self.apptainer_env

        if not sif:
            return cmd

        # APPTAINER_TMPDIR 디렉토리 생성
        os.makedirs(self.apptainer_tmpdir, exist_ok=True)
        # 호스트 환경변수에 APPTAINER_TMPDIR 설정 (sandbox 추출에 필요)
        os.environ["APPTAINER_TMPDIR"] = self.apptainer_tmpdir

        wrapped = ["apptainer", "exec"]
        if bind:
            wrapped.extend(["--bind", bind])
        if pwd:
            wrapped.extend(["--pwd", pwd])
        for key, value in env_vars.items():
            wrapped.extend(["--env", f"{key}={value}"])
        wrapped.append(sif)
        wrapped.extend(cmd)
        return wrapped

    def build_apptainer_exec_args(self, use_lsdyna: bool = False) -> List[str]:
        """apptainer exec 인자 목록 생성 (멀티노드 MPI용)

        멀티노드에서는 mpirun이 apptainer 바깥에서 실행되므로,
        각 MPI rank가 실행할 'apptainer exec ... <binary>' 형태가 필요.
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
            return []

        # APPTAINER_TMPDIR 디렉토리 생성
        os.makedirs(self.apptainer_tmpdir, exist_ok=True)
        # 호스트 환경변수에 APPTAINER_TMPDIR 설정 (sandbox 추출에 필요)
        os.environ["APPTAINER_TMPDIR"] = self.apptainer_tmpdir

        args = ["apptainer", "exec"]
        if bind:
            args.extend(["--bind", bind])
        for key, value in env_vars.items():
            args.extend(["--env", f"{key}={value}"])
        args.append(sif)
        return args

    def cleanup_after_exec(self):
        """apptainer exec 후 orphan squashfuse 및 stale mount 정리"""
        import subprocess as _sp
        user = os.environ.get("USER", os.environ.get("LOGNAME", ""))

        # 1. orphan squashfuse 프로세스 정리
        try:
            _sp.run(["pkill", "-u", user, "-f", "squashfuse"],
                    capture_output=True, timeout=5)
        except Exception:
            pass

        # 2. stale FUSE mount lazy unmount (APPTAINER_TMPDIR 하위)
        try:
            result = _sp.run(["findmnt", "-n", "-o", "TARGET", "-t", "fuse.squashfuse"],
                             capture_output=True, text=True, timeout=5)
            for mount in result.stdout.strip().splitlines():
                if self.apptainer_tmpdir in mount or "/tmp" in mount:
                    _sp.run(["fusermount", "-uz", mount], capture_output=True, timeout=5)
        except Exception:
            pass

    def cleanup_tmpdir(self):
        """APPTAINER_TMPDIR 정리 (stage-out 완료 후 호출)"""
        if self.apptainer_tmpdir and os.path.isdir(self.apptainer_tmpdir):
            try:
                import shutil
                shutil.rmtree(self.apptainer_tmpdir, ignore_errors=True)
            except Exception:
                pass


class LSDynaSolverRunner:
    """LS-DYNA Solver 실행 및 관리"""

    def __init__(self, config: Dict[str, Any]):
        env = config.get("environment", {})
        self.solver_path = env.get("lsdyna_path", "/opt/lsdyna/lsdyna")
        self.mpi_path = env.get("mpi_path", "mpirun")
        self.ncpu = env.get("ncpu", 32)
        self.memory = env.get("lsdyna_memory", env.get("memory", "2000m"))
        self.mpi_enabled = env.get("mpi_enabled", False)
        self.mpi_launcher = env.get("mpi_launcher", "mpirun")  # "mpirun" or "srun"
        self.apptainer = ApptainerWrapper(config)

    def run(self, input_file: str, working_dir: str, timeout: int = 7200) -> bool:
        """LS-DYNA 실행 및 완료 대기

        멀티노드 + srun (nodes_per_job >= 2, mpi_launcher == "srun"):
            srun --mpi=pmi2 apptainer exec ... lsdyna i=... memory=...
            → Slurm이 직접 프로세스 spawn, 호스트 MPI 불필요

        멀티노드 + mpirun (nodes_per_job >= 2, mpi_launcher == "mpirun"):
            mpirun -np {ncpu} -hostfile $SLURM_NODEFILE apptainer exec ... lsdyna i=... memory=...
            → 호스트 MPI 필요, MPI가 apptainer 바깥에서 실행

        단일노드 (nodes_per_job == 1):
            apptainer exec ... mpirun -np {ncpu} lsdyna i=... memory=...
            → 기존 방식: apptainer 안에서 mpirun + lsdyna 실행
        """
        nodes_per_job = self.apptainer.nodes_per_job

        if nodes_per_job >= 2 and self.mpi_enabled:
            appt_args = self.apptainer.build_apptainer_exec_args(use_lsdyna=True)

            if self.mpi_launcher == "srun":
                # srun 방식: Slurm이 직접 프로세스 spawn, 호스트 MPI 불필요
                # srun --mpi=pmi2 apptainer exec ... lsdyna i=... memory=...
                cmd = ["srun", "--mpi=pmi2"]
                if appt_args:
                    cmd.extend(appt_args)
                cmd.extend([
                    self.solver_path,
                    f"i={input_file}",
                    f"memory={self.memory}"
                ])
            else:
                # mpirun 방식: 호스트 MPI가 프로세스 spawn
                # mpirun -np {ncpu} -hostfile $SLURM_NODEFILE apptainer exec ... lsdyna i=... memory=...
                cmd = [
                    self.mpi_path, "-np", str(self.ncpu),
                    "-hostfile", os.environ.get("SLURM_NODEFILE", "/dev/null"),
                ]
                if appt_args:
                    cmd.extend(appt_args)
                cmd.extend([
                    self.solver_path,
                    f"i={input_file}",
                    f"memory={self.memory}"
                ])
        elif self.mpi_enabled:
            cmd = [
                self.mpi_path, "-np", str(self.ncpu),
                self.solver_path,
                f"i={input_file}",
                f"memory={self.memory}"
            ]
            # 단일노드: 기존 방식 (apptainer 안에서 mpirun)
            cmd = self.apptainer.wrap_command(cmd, use_lsdyna=True, pwd=working_dir)
        else:
            cmd = [
                self.solver_path,
                f"i={input_file}",
                f"ncpu={self.ncpu}",
                f"memory={self.memory}"
            ]
            # Apptainer 래핑 (설정 시)
            cmd = self.apptainer.wrap_command(cmd, use_lsdyna=True, pwd=working_dir)

        logging.info(f"Executing: {' '.join(cmd)}")
        logging.info(f"Working directory: {working_dir}")

        try:
            # LS-DYNA 출력을 로그 파일에 실시간 저장
            log_file = os.path.join(working_dir, "lsdyna_stdout.log")
            with open(log_file, "w") as flog:
                process = subprocess.Popen(
                    cmd,
                    cwd=working_dir,
                    stdout=flog,
                    stderr=subprocess.PIPE
                )

                _, stderr = process.communicate(timeout=timeout)

            # Apptainer 컨테이너 정리 대기 (squashfuse unmount, sandbox 정리)
            time.sleep(5)
            self.apptainer.cleanup_after_exec()

            if process.returncode != 0:
                _stderr_str = stderr.decode('utf-8', errors='ignore')
                # Apptainer squashfuse cleanup 메시지 필터
                _stderr_filtered = "\n".join(
                    l for l in _stderr_str.splitlines()
                    if not any(k in l for k in ('squashfuse', 'cleanup error', 'fuse: reading device'))
                )
                logging.error(f"LS-DYNA failed with return code {process.returncode}")
                if _stderr_filtered.strip():
                    logging.error(f"stderr: {_stderr_filtered}")
                return False

            return True

        except subprocess.TimeoutExpired:
            process.kill()
            logging.error(f"LS-DYNA timed out after {timeout} seconds")
            return False
        except FileNotFoundError:
            logging.error(f"LS-DYNA solver not found: {self.solver_path}")
            return False
        except Exception as e:
            logging.error(f"LS-DYNA execution error: {e}")
            return False

    def wait_for_dynain(self, output_dir: str, timeout: int = 7200, interval: int = 10) -> bool:
        """dynain 파일 생성 대기"""
        dynain_path = os.path.join(output_dir, "dynain")
        elapsed = 0

        while elapsed < timeout:
            if os.path.exists(dynain_path):
                # 파일 크기 안정화 확인
                size1 = os.path.getsize(dynain_path)
                time.sleep(2)
                size2 = os.path.getsize(dynain_path)
                if size1 == size2 and size1 > 0:
                    logging.info(f"dynain generated: {dynain_path} ({size1} bytes)")
                    return True
            time.sleep(interval)
            elapsed += interval
            if elapsed % 60 == 0:
                logging.info(f"Waiting for dynain... ({elapsed}s elapsed)")

        logging.error(f"dynain not generated within {timeout} seconds")
        return False


class CumulativeScenarioRunner:
    """누적 시나리오 실행자"""

    def __init__(self, config_path: str, doe_filter: Optional[int] = None,
                 skip_koomeshmodifier: bool = False, pregenerated_dir: Optional[str] = None):
        """
        Args:
            config_path: runner_config.json 경로
            doe_filter: 특정 DOE만 실행 (병렬 실행 시 사용)
            skip_koomeshmodifier: KooMeshModifier 실행 생략 (batch 사전 생성 모드)
            pregenerated_dir: 사전 생성된 DropSet.k 파일 디렉토리
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.config_path = config_path
        self.doe_filter = doe_filter
        self.skip_koomeshmodifier = skip_koomeshmodifier
        self.pregenerated_dir = pregenerated_dir
        self.solver = LSDynaSolverRunner(self.config)
        self.apptainer = ApptainerWrapper(self.config)
        self.koomesh_path = self.config["environment"]["koomeshmodifier_path"]
        self.output_dir = self.config["project"]["output_dir"]
        self.index_file = self.config["project"]["index_file"]
        # --doe N 모드: DOE별 개별 checkpoint (동시 write 경합 방지)
        base_checkpoint = self.config["execution"]["checkpoint_file"]
        if doe_filter is not None:
            cp_dir = os.path.dirname(base_checkpoint)
            self.checkpoint_file = os.path.join(cp_dir, f"checkpoint_doe_{doe_filter:03d}.json")
        else:
            self.checkpoint_file = base_checkpoint

        self._setup_logging()
        self._load_checkpoint()
        self._load_index()

    def _setup_logging(self):
        """로깅 설정"""
        os.makedirs(self.output_dir, exist_ok=True)
        # --doe N 모드: DOE별 개별 로그 파일 (동시 write 경합 방지)
        if self.doe_filter is not None:
            log_file = os.path.join(self.output_dir, f"runner_doe_{self.doe_filter:03d}.log")
        else:
            log_file = os.path.join(self.output_dir, "runner.log")

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def _load_checkpoint(self):
        """체크포인트 로드"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.checkpoint = json.loads(content)
                        logging.info(f"Checkpoint loaded: DOE {self.checkpoint['current_doe']}, "
                                    f"Step {self.checkpoint['current_step']}")
                        return
            except json.JSONDecodeError as e:
                # 백업에서 복구 시도
                backup = self.checkpoint_file + ".bak"
                if os.path.exists(backup):
                    logging.warning(f"checkpoint.json 손상 감지, 백업에서 복구: {e}")
                    with open(backup, 'r', encoding='utf-8') as bf:
                        self.checkpoint = json.load(bf)
                    return
                logging.warning(f"checkpoint.json 손상, 백업 없음. 초기화합니다: {e}")

        # 위 경로에서 self.checkpoint가 설정되지 않은 경우 (빈 파일, 손상+백업없음 등) 초기화
        if not hasattr(self, 'checkpoint') or self.checkpoint is None:
            self.checkpoint = {
                "scenario_id": self.config["scenario"]["id"],
                "current_doe": 1,
                "current_step": 1,
                "completed_runs": [],
                "last_updated": datetime.now().isoformat(),
                "failure_count": 0
            }

    def _save_checkpoint(self, doe: int, step: int):
        """체크포인트 저장 (atomic write: 중단 시 파일 손상 방지)"""
        self.checkpoint["current_doe"] = doe
        self.checkpoint["current_step"] = step
        self.checkpoint["last_updated"] = datetime.now().isoformat()
        target = self.checkpoint_file
        # 기존 파일 백업
        if os.path.exists(target):
            try:
                os.replace(target, target + ".bak")
            except OSError:
                pass
        dir_path = os.path.dirname(target) or "."
        fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(self.checkpoint, f, indent=2)
            os.replace(tmp_path, target)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _load_index(self):
        """simulation_index.json 로드 (double-checked locking + stale lock 복구)
        - 정상 경로: LOCK_SH로 동시 읽기 허용
        - 파일 없거나 손상 시: LOCK_EX로 재획득 후 단독 초기화/복구
        - NFS stale lock 시: lock 파일 삭제 후 재시도
        """
        lock_file = self.index_file + ".lock"

        for attempt in range(2):  # stale lock 복구 시 최대 1회 재시도
            try:
                return self._load_index_locked(lock_file)
            except TimeoutError:
                if attempt == 0:
                    logging.warning(
                        f"NFS stale lock 감지: {lock_file} — "
                        f"노드 장애로 인한 잔존 lock 가능성. lock 파일 삭제 후 재시도")
                    try:
                        os.unlink(lock_file)
                    except OSError:
                        pass
                else:
                    logging.error(f"lock 재시도 실패. lock 없이 index 직접 읽기 시도")
                    # 최후 수단: lock 없이 직접 읽기
                    if os.path.exists(self.index_file):
                        try:
                            with open(self.index_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            if content.strip():
                                self.index = json.loads(content)
                                return
                        except (json.JSONDecodeError, OSError):
                            pass
                    self.index = self._init_index()

    def _load_index_locked(self, lock_file):
        """_load_index 내부: flock 사용 읽기"""
        # 1단계: LOCK_SH로 빠른 읽기 시도
        with open(lock_file, 'a') as lf:
            _flock_with_timeout(lf, fcntl.LOCK_SH)
            try:
                if os.path.exists(self.index_file):
                    try:
                        with open(self.index_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if content.strip():
                            self.index = json.loads(content)
                            return  # 정상 읽기 성공, EX 불필요
                    except (json.JSONDecodeError, OSError):
                        pass  # 손상 → 2단계로
            finally:
                _flock_with_timeout(lf, fcntl.LOCK_UN)

        # 2단계: 파일 없거나 손상 → LOCK_EX로 단독 초기화/복구
        with open(lock_file, 'a') as lf:
            _flock_with_timeout(lf, fcntl.LOCK_EX)
            try:
                # EX 획득 후 재확인 (다른 잡이 먼저 초기화했을 수 있음)
                if os.path.exists(self.index_file):
                    try:
                        with open(self.index_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if content.strip():
                            self.index = json.loads(content)
                            return  # 다른 잡이 이미 초기화함
                    except json.JSONDecodeError as e:
                        backup = self.index_file + ".bak"
                        if os.path.exists(backup):
                            logging.warning(f"simulation_index.json 손상, 백업에서 복구: {e}")
                            with open(backup, 'r', encoding='utf-8') as bf:
                                self.index = json.load(bf)
                        else:
                            logging.warning(f"simulation_index.json 손상, 초기화: {e}")
                            self.index = self._init_index()
                        self._save_index_unlocked()
                        return
                # 파일 없음 → 초기화
                self.index = self._init_index()
                self._save_index_unlocked()
            finally:
                _flock_with_timeout(lf, fcntl.LOCK_UN)

    def _init_index(self) -> Dict[str, Any]:
        """simulation_index.json 초기화"""
        scenario = self.config["scenario"]
        mode_sequence = [step["mode"] for step in scenario["steps"]]

        return {
            "project": self.config["project"]["name"],
            "created": datetime.now().isoformat(),
            "scenarios": [{
                "id": scenario["id"],
                "name": scenario["name"],
                "type": scenario["type"],
                "total_steps": scenario["total_steps"],
                "doe_count": scenario["doe_count"],
                "total_runs": scenario["doe_count"] * scenario["total_steps"],
                "status": "in_progress",
                "mode_sequence": mode_sequence,
                "runs": {}
            }]
        }

    def _save_index_unlocked(self):
        """simulation_index.json 저장 (잠금 없이 - 이미 잠금 상태에서 호출, atomic write)"""
        target = self.index_file
        if os.path.exists(target):
            try:
                os.replace(target, target + ".bak")
            except OSError:
                pass
        dir_path = os.path.dirname(target) or "."
        fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, target)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _save_index(self):
        """simulation_index.json 저장 (파일 잠금 + atomic write)"""
        lock_file = self.index_file + ".lock"
        with open(lock_file, 'a') as lf:  # 'a': NFS truncate 경합 방지
            _flock_with_timeout(lf, fcntl.LOCK_EX)
            try:
                self._save_index_unlocked()
            finally:
                _flock_with_timeout(lf, fcntl.LOCK_UN)

    def _update_index(self, alias: str, run_info: Dict[str, Any]):
        """simulation_index.json 업데이트 (lock 내 re-read + 머지로 lost update 방지)
        NFS stale lock 시 lock 파일 삭제 후 재시도"""
        lock_file = self.index_file + ".lock"
        for attempt in range(2):
            try:
                self._update_index_locked(lock_file, alias, run_info)
                return
            except TimeoutError:
                if attempt == 0:
                    logging.warning(f"_update_index: NFS stale lock 감지 — lock 파일 삭제 후 재시도")
                    try:
                        os.unlink(lock_file)
                    except OSError:
                        pass
                else:
                    logging.error(f"_update_index: lock 재시도 실패. lock 없이 직접 쓰기")
                    self.index["scenarios"][0]["runs"][alias] = run_info
                    self._save_index_unlocked()

    def _update_index_locked(self, lock_file, alias, run_info):
        """_update_index 내부: flock 사용 업데이트"""
        with open(lock_file, 'a') as lf:  # 'a': NFS truncate 경합 방지
            _flock_with_timeout(lf, fcntl.LOCK_EX)
            try:
                # 최신 파일 재읽기: 다른 DOE 잡이 쓴 내용을 반영
                if os.path.exists(self.index_file):
                    try:
                        with open(self.index_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content.strip():
                                self.index = json.loads(content)
                    except (json.JSONDecodeError, OSError):
                        pass  # 손상 시 self.index 그대로 유지
                self.index["scenarios"][0]["runs"][alias] = run_info
                self._save_index_unlocked()
            finally:
                _flock_with_timeout(lf, fcntl.LOCK_UN)

    def _generate_run_id(self) -> str:
        """Run ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_hash = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:6]
        return f"{timestamp}_{unique_hash}"

    def _generate_alias(self, doe_index: int, step: int, mode: str, condition: str) -> str:
        """별칭 생성"""
        project = self.config["project"]["name"]
        total_steps = self.config["scenario"]["total_steps"]
        return f"{project}_CUM{total_steps:03d}_DOE{doe_index:03d}_S{step:03d}_{mode}_{condition}"

    def _get_prev_alias(self, doe_index: int, step: int) -> Optional[str]:
        """이전 step의 별칭 반환"""
        if step <= 1:
            return None
        prev_step = self.config["scenario"]["steps"][step - 2]  # 0-indexed
        prev_mode = prev_step["mode"]

        # DOE별 실제 condition 조회 (doe_angles / doe_positions)
        doe_key = str(doe_index)
        prev_step_key = str(step - 1)
        doe_angles = self.config.get("scenario", {}).get("doe_angles", {})
        doe_positions = self.config.get("scenario", {}).get("doe_positions", {})
        if doe_key in doe_positions and prev_step_key in doe_positions[doe_key]:
            prev_condition = doe_positions[doe_key][prev_step_key].get("position_name", prev_step["condition"])
        elif doe_key in doe_angles and prev_step_key in doe_angles[doe_key]:
            prev_condition = doe_angles[doe_key][prev_step_key].get("angle_name", prev_step["condition"])
        else:
            prev_condition = prev_step["condition"]

        return self._generate_alias(doe_index, step - 1, prev_mode, prev_condition)

    def _generate_and_maybe_run_deep_report(self, run_dir: str, output_run_dir: str):
        """deep_report.sh를 run_dir에 항상 생성, postprocess.enabled && auto_deep이면 자동 실행.

        auto_deep_mode (default 'inline'):
          - 'inline': 시뮬 잡 안에서 bash 실행 (노드 점유 유지)
          - 'separate_job': dependent sbatch 별도 제출 (시뮬 노드 즉시 해방)

        postprocess 옵션 없으면 전체 skip (회귀 무영향).
        """
        pp = self.config.get("postprocess")
        if not pp:
            return  # 옵션 없으면 아무것도 안 함

        try:
            from Runner.PostprocessShellGenerator import build_deep_report_sh
            sh_text = build_deep_report_sh(
                run_dir=output_run_dir,
                sif_path=pp.get("sif_path"),
                options=pp,
            )
            sh_path = os.path.join(run_dir, "deep_report.sh")
            with open(sh_path, 'w') as f:
                f.write(sh_text)
            os.chmod(sh_path, 0o755)
            logging.info(f"deep_report.sh 생성: {sh_path}")
        except Exception as e:
            logging.warning(f"deep_report.sh 생성 실패 (skip): {e}")
            return

        # 자동 실행
        if not (pp.get("enabled") and pp.get("auto_deep", True)):
            return

        mode = pp.get("auto_deep_mode", "inline").lower()
        if mode == "separate_job":
            self._submit_deep_report_sbatch(run_dir, sh_path, pp)
        else:  # inline
            try:
                log_path = os.path.join(run_dir, "deep_report.log")
                logging.info(f"deep_report 자동 실행 (inline): {sh_path}")
                with open(log_path, 'w') as logf:
                    result = subprocess.run(
                        ["bash", sh_path],
                        cwd=run_dir,
                        stdout=logf, stderr=subprocess.STDOUT,
                        timeout=pp.get("deep_timeout_seconds", 7200),
                    )
                if result.returncode != 0:
                    logging.warning(f"deep_report 실행 실패 (rc={result.returncode}, log={log_path})")
            except Exception as e:
                logging.warning(f"deep_report 자동 실행 실패 (skip): {e}")

    def _submit_deep_report_sbatch(self, run_dir: str, sh_path: str, pp: dict):
        """auto_deep_mode=separate_job: dependent sbatch 잡으로 deep_report 제출.

        시뮬 잡 안에서 호출되므로 SLURM_JOB_ID 환경변수로 현재 잡 ID 얻어
        afterok dependency 설정 (단, 잡이 이미 끝나가는 시점이라 afterok 대신 즉시 제출).
        """
        try:
            from Runner.PostprocessShellGenerator import build_deep_report_sbatch
            env = self.config.get("environment", {})
            run_id = os.path.basename(run_dir.rstrip("/"))
            sbatch_text = build_deep_report_sbatch(
                run_dir=run_dir,
                sh_path=sh_path,
                options=pp,
                environment=env,
                dependency_id=None,  # 시뮬 잡 안에서 호출되니 dependent 불필요 (즉시 제출 OK)
                job_name_suffix=run_id,
            )
            sbatch_path = os.path.join(run_dir, "deep_report.sbatch")
            with open(sbatch_path, 'w') as f:
                f.write(sbatch_text)
            os.chmod(sbatch_path, 0o755)
            result = subprocess.run(
                ["sbatch", sbatch_path],
                capture_output=True, text=True, check=True, timeout=60,
            )
            jid = result.stdout.strip().split()[-1]
            logging.info(f"deep_report sbatch 제출 (separate_job): job={jid}, {sbatch_path}")
            # 잡 ID 기록 (sphere가 나중에 dependent 잡으로 모음에 활용 가능)
            jids_log = os.path.join(os.path.dirname(run_dir), "deep_report_jobs.txt")
            with open(jids_log, 'a') as f:
                f.write(f"{jid}\t{run_id}\n")
        except Exception as e:
            logging.warning(f"deep_report sbatch 제출 실패 (skip): {e}")

    def _get_prev_run_dir(self, doe_index: int, step: int) -> Optional[str]:
        """이전 step의 결과 폴더 반환"""
        prev_alias = self._get_prev_alias(doe_index, step)
        if prev_alias is None:
            return None

        scenario = self.index["scenarios"][0]
        if prev_alias in scenario["runs"]:
            return scenario["runs"][prev_alias].get("folder")
        return None

    def run_all(self) -> bool:
        """전체 시나리오 실행"""
        scenario = self.config["scenario"]
        doe_count = scenario["doe_count"]
        steps = scenario["steps"]

        logging.info("=" * 60)
        logging.info(f"Starting scenario: {scenario['name']}")
        logging.info(f"DOE count: {doe_count}, Steps per DOE: {len(steps)}")
        logging.info("=" * 60)

        # DOE 필터가 있으면 해당 DOE만 실행
        doe_range = [self.doe_filter] if self.doe_filter else range(1, doe_count + 1)

        for doe in doe_range:
            # 체크포인트에서 시작 step 결정
            # doe_filter가 있으면 (--doe N 모드) checkpoint 무시하고 step 1부터 실행
            if self.doe_filter:
                start_step = 1
            elif doe == self.checkpoint["current_doe"]:
                start_step = self.checkpoint["current_step"]
            elif doe < self.checkpoint["current_doe"]:
                continue  # 이미 완료된 DOE
            else:
                start_step = 1

            logging.info(f"\n{'='*60}")
            logging.info(f"Processing DOE {doe}/{doe_count}")
            logging.info(f"{'='*60}")

            for step_config in steps:
                step_num = step_config["step"]
                if step_num < start_step:
                    continue

                success = self.run_single_step(doe, step_config)

                if not success:
                    logging.error(f"Step {step_num} failed for DOE {doe}")
                    self.checkpoint["failure_count"] += 1

                    if self.config["execution"]["retry_on_failure"]:
                        max_retries = self.config["execution"]["max_retries"]
                        for retry in range(max_retries):
                            logging.info(f"Retry {retry + 1}/{max_retries}")
                            success = self.run_single_step(doe, step_config)
                            if success:
                                break

                    if not success:
                        logging.error(f"All retries failed for DOE {doe}, Step {step_num}")
                        self._save_checkpoint(doe, step_num)
                        self._update_scenario_status()  # 실패 시에도 시나리오 status 집계
                        return False

                self._save_checkpoint(doe, step_num + 1)

            # DOE 완료, 다음 DOE 준비
            self._save_checkpoint(doe + 1, 1)

        self._update_scenario_status()

        if self.index["scenarios"][0]["status"] == "completed":
            logging.info("\n" + "=" * 60)
            logging.info("All scenarios completed successfully!")
            logging.info("=" * 60)

        # Apptainer tmpdir 명시적 정리 (orphan squashfuse/sandbox 방지)
        try:
            tmpdir = self.apptainer.apptainer_tmpdir
            if tmpdir and os.path.isdir(tmpdir):
                logging.info(f"Apptainer tmpdir 정리: {tmpdir}")
                shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass

        return True

    def _update_scenario_status(self):
        """시나리오 status 집계 (lock 내 re-read 후 실제 결과 기반 판정)"""
        lock_file = self.index_file + ".lock"
        try:
            with open(lock_file, 'a') as lf:
                _flock_with_timeout(lf, fcntl.LOCK_EX)
                try:
                    if os.path.exists(self.index_file):
                        try:
                            with open(self.index_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if content.strip():
                                    self.index = json.loads(content)
                        except (json.JSONDecodeError, OSError):
                            pass
                    scenario_data = self.index["scenarios"][0]
                    runs = scenario_data.get("runs", {})
                    expected = scenario_data.get("total_runs", 0)
                    n_completed = sum(1 for r in runs.values() if r.get("status") == "completed")
                    n_failed = sum(1 for r in runs.values() if r.get("status") == "failed")
                    n_running = sum(1 for r in runs.values() if r.get("status") == "running")
                    if expected > 0 and n_completed == expected:
                        scenario_data["status"] = "completed"
                    elif n_failed > 0:
                        scenario_data["status"] = "partial_failed"
                        logging.warning(
                            f"Scenario status: {n_completed} completed, {n_failed} failed, "
                            f"{n_running} running / {expected} total")
                    else:
                        scenario_data["status"] = "in_progress"
                    self._save_index_unlocked()
                finally:
                    _flock_with_timeout(lf, fcntl.LOCK_UN)
        except TimeoutError:
            logging.warning("_update_scenario_status: flock timeout — status 업데이트 생략")

    def run_single_step(self, doe_index: int, step_config: Dict[str, Any]) -> bool:
        """단일 Step 실행"""
        step_num = step_config["step"]
        mode = step_config["mode"]
        condition = step_config["condition"]
        params = step_config.get("params", {})

        # DOE별 실제 condition 교체 (angle_name 또는 position_name)
        doe_angles = self.config.get("scenario", {}).get("doe_angles", {})
        doe_positions = self.config.get("scenario", {}).get("doe_positions", {})
        doe_key = str(doe_index)
        step_key = str(step_num)
        if doe_key in doe_positions and step_key in doe_positions[doe_key]:
            condition = doe_positions[doe_key][step_key].get("position_name", condition)
        elif doe_key in doe_angles and step_key in doe_angles[doe_key]:
            condition = doe_angles[doe_key][step_key].get("angle_name", condition)

        alias = self._generate_alias(doe_index, step_num, mode, condition)
        logging.info(f"\n--- Running: {alias} ---")

        # 0. 이미 완료된 step 스킵 (rerun 시 효율화)
        scenario_runs = self.index["scenarios"][0]["runs"]
        if alias in scenario_runs:
            prev_run = scenario_runs[alias]
            if prev_run.get("status") == "completed":
                prev_folder = prev_run.get("folder", "")
                dynain_path = os.path.join(self.output_dir, prev_folder, "Output", "dynain")
                if prev_folder and os.path.exists(dynain_path):
                    logging.info(f"이미 완료된 step 스킵: {alias} (폴더: {prev_folder})")
                    return True

        # 1. Index 업데이트 (running 상태, run_dir은 KooMeshModifier 실행 후 결정)
        run_id = None
        run_dir = None

        # 2. KooMeshModifier (사전 생성 모드이면 복사, 아니면 실행)
        if self.skip_koomeshmodifier and self.pregenerated_dir:
            # Batch 사전 생성 모드: Runner가 폴더 생성
            run_id = self._generate_run_id()
            run_dir = os.path.join(self.output_dir, f"Run_{run_id}")
            os.makedirs(run_dir, exist_ok=True)
            os.makedirs(os.path.join(run_dir, "Output"), exist_ok=True)
            os.makedirs(os.path.join(run_dir, "DynamicRelaxation"), exist_ok=True)
            self._update_index(alias, {
                "run_id": run_id, "status": "running",
                "folder": f"Run_{run_id}", "mode": mode,
                "condition": condition,
                "started_at": datetime.now().isoformat(),
                "prev": self._get_prev_alias(doe_index, step_num)
            })
            if not self._copy_pregenerated(doe_index, run_dir, mode):
                self._update_index(alias, {
                    "run_id": run_id, "status": "failed",
                    "folder": f"Run_{run_id}", "mode": mode,
                    "condition": condition,
                    "error": "Pregenerated DropSet.k 복사 실패"
                })
                return False
        else:
            # 일반 모드: KooMeshModifier가 Run 폴더 + DropSet.k + Output/ + DynamicRelaxation/ 생성
            config_file = self._create_step_config(doe_index, step_config)
            if config_file is None:
                logging.error("Failed to create step config file")
                self._update_index(alias, {
                    "run_id": "", "status": "failed",
                    "folder": "", "mode": mode, "condition": condition,
                    "error": "step config file creation failed"
                })
                return False

            koomesh_result = self._run_koomeshmodifier(config_file, self.output_dir)
            if koomesh_result is None:
                self._update_index(alias, {
                    "run_id": "", "status": "failed",
                    "folder": "", "mode": mode, "condition": condition,
                    "error": "KooMeshModifier failed"
                })
                return False

            run_id = koomesh_result
            run_dir = os.path.join(self.output_dir, f"Run_{run_id}")

            if not os.path.isdir(run_dir):
                logging.error(f"KooMeshModifier 완료했으나 Run 폴더 없음: {run_dir}")
                self._update_index(alias, {
                    "run_id": run_id, "status": "failed",
                    "folder": f"Run_{run_id}", "mode": mode,
                    "condition": condition,
                    "error": f"Run folder not found: {run_dir}"
                })
                return False

            # step_config.txt를 run_dir로 이동 (기록 보존)
            src_config = config_file
            dst_config = os.path.join(run_dir, "step_config.txt")
            if os.path.exists(src_config) and not os.path.exists(dst_config):
                import shutil
                shutil.move(src_config, dst_config)

            self._update_index(alias, {
                "run_id": run_id, "status": "running",
                "folder": f"Run_{run_id}", "mode": mode,
                "condition": condition,
                "started_at": datetime.now().isoformat(),
                "prev": self._get_prev_alias(doe_index, step_num)
            })

        # 5. LS-DYNA 실행 (로컬 디스크 stage-in/out으로 NFS 부하 방지)
        input_file = self._find_input_file(run_dir, mode)
        timeout = self.config["execution"].get("timeout_per_step_seconds", 604800)
        output_run_dir = os.path.join(run_dir, "Output")
        os.makedirs(output_run_dir, exist_ok=True)

        use_local = self.config.get("environment", {}).get("use_local_scratch", True)
        if use_local and self.apptainer.apptainer_tmpdir:
            import shutil
            local_work_dir = os.path.join(self.apptainer.apptainer_tmpdir, f"Run_{run_id}")
            os.makedirs(local_work_dir, exist_ok=True)
            # Stage-in: 입력 파일 + include 파일을 로컬로 복사
            local_input = os.path.join(local_work_dir, os.path.basename(input_file))
            shutil.copy2(input_file, local_input)
            # include 파일 복사
            try:
                from KooCAEManager.KooIncludeManager import KooIncludeManager
                inc_mgr = KooIncludeManager(input_file)
                inc_mgr.CopyTo(local_work_dir)
            except Exception as e:
                logging.debug(f"Include scan skipped: {e}")
            # additional_files 복사
            additional_files = self.config.get("environment", {}).get("additional_files", [])
            additional_dirs = self.config.get("environment", {}).get("additional_dirs", [])
            model_dir = os.path.dirname(self.config["project"]["model_file"])
            for af in additional_files:
                af_path = af if os.path.isabs(af) else os.path.join(model_dir, af)
                import glob as _glob
                for matched in _glob.glob(af_path):
                    dst = os.path.join(local_work_dir, os.path.basename(matched))
                    if not os.path.exists(dst):
                        shutil.copy2(matched, dst)
            for ad in additional_dirs:
                ad_path = ad if os.path.isabs(ad) else os.path.join(model_dir, ad)
                if os.path.isdir(ad_path):
                    dst_dir = os.path.join(local_work_dir, os.path.basename(ad_path))
                    if not os.path.exists(dst_dir):
                        shutil.copytree(ad_path, dst_dir)
            logging.info(f"Stage-in: {input_file} -> {local_work_dir}")

            # LS-DYNA 실행 (로컬 디스크)
            solver_success = self.solver.run(os.path.basename(local_input), local_work_dir, timeout)

            # Stage-out: rsync로 결과를 NFS로 복사
            # Semaphore 직렬화: 동시 진입 N개 cap (NFS burst 방지하면서도 throughput 보장)
            #   - environment.stage_out_concurrency  (default 8)
            #   - environment.stage_out_timeout_seconds  (default 120)
            #   대형 클러스터(노드 수십~수백)는 시나리오에서 16/32로 늘리고 timeout도 늘리는 게 좋음.
            if os.path.isdir(local_work_dir):
                env = self.config.get("environment", {})
                sem_n = int(env.get("stage_out_concurrency", 8))
                sem_timeout = int(env.get("stage_out_timeout_seconds", 120))
                logging.info(f"Stage-out semaphore 대기 (DOE {doe_index}, concurrency={sem_n}, timeout={sem_timeout}s)")
                _sem_fd, _sem_token = _semaphore_acquire(self.output_dir, sem_n, timeout=sem_timeout)
                try:
                    logging.info(f"Stage-out: {local_work_dir} -> {output_run_dir} (token={os.path.basename(_sem_token)})")
                    rsync_ret = subprocess.run(
                        ["rsync", "-a", "--size-only", local_work_dir + "/", output_run_dir + "/"],
                        capture_output=True, text=True)
                    if rsync_ret.returncode != 0:
                        logging.warning(f"rsync failed ({rsync_ret.returncode}), fallback to shutil")
                        for fname in os.listdir(local_work_dir):
                            src = os.path.join(local_work_dir, fname)
                            dst = os.path.join(output_run_dir, fname)
                            if os.path.isfile(src):
                                shutil.copy2(src, dst)
                            elif os.path.isdir(src):
                                dst_dir = os.path.join(output_run_dir, fname)
                                if not os.path.exists(dst_dir):
                                    shutil.copytree(src, dst_dir)
                                else:
                                    for sub in os.listdir(src):
                                        shutil.copy2(os.path.join(src, sub), os.path.join(dst_dir, sub))
                    logging.info(f"Stage-out 완료: DOE {doe_index}")
                finally:
                    _semaphore_release(_sem_fd, _sem_token)
                # 로컬 정리 (Run 폴더 + 상위 apptainer_job 폴더)
                shutil.rmtree(local_work_dir, ignore_errors=True)
                job_dir = os.path.dirname(local_work_dir)
                if job_dir and os.path.isdir(job_dir) and not os.listdir(job_dir):
                    shutil.rmtree(job_dir, ignore_errors=True)
        else:
            solver_success = self.solver.run(input_file, output_run_dir, timeout)

        if not solver_success:
            self._update_index(alias, {
                "run_id": run_id,
                "status": "failed",
                "folder": f"Run_{run_id}",
                "mode": mode,
                "condition": condition,
                "error": "LS-DYNA failed"
            })
            return False

        # 6. dynain 생성 대기 (Output/ 폴더)
        dynain_timeout = self.config["execution"].get("timeout_dynain_seconds", 604800)
        if not self.solver.wait_for_dynain(output_run_dir, dynain_timeout):
            self._update_index(alias, {
                "run_id": run_id,
                "status": "failed",
                "folder": f"Run_{run_id}",
                "mode": mode,
                "condition": condition,
                "error": "dynain not generated"
            })
            return False

        # 6.5 KooD3plotReader deep_report sh 생성 + (옵션 시) 자동 실행
        # postprocess 옵션 없으면 전체 skip → 회귀 무영향
        self._generate_and_maybe_run_deep_report(run_dir, output_run_dir)

        # 7. DYNAIN_TO_INITIAL 실행 (마지막 step 제외)
        total_steps = self.config["scenario"]["total_steps"]
        if step_num < total_steps:
            dti_file = os.path.join(run_dir, "DynamicRelaxation", "dynaintoinitial.txt")
            if os.path.exists(dti_file):
                if self._run_koomeshmodifier(dti_file, run_dir) is None:
                    logging.warning("DYNAIN_TO_INITIAL failed, but continuing...")

        # 8. Index 업데이트 (completed)
        self._update_index(alias, {
            "run_id": run_id,
            "status": "completed",
            "folder": f"Run_{run_id}",
            "mode": mode,
            "condition": condition,
            "completed_at": datetime.now().isoformat(),
            "prev": self._get_prev_alias(doe_index, step_num)
        })

        # 9. 체크포인트에 완료 기록
        self.checkpoint["completed_runs"].append(alias)

        logging.info(f"Completed: {alias}")
        return True

    def _build_preserve_block(self) -> str:
        """scenario.json의 preserve_includes를 *PreserveIncludes 블록으로 변환.

        Returns:
            "*PreserveIncludes\\npat1\\npat2\\n" 형식 또는 빈 문자열
        """
        patterns = self.config.get("preserve_includes", [])
        if not patterns:
            return ""
        valid = [p for p in patterns if p]
        if not valid:
            return ""
        lines = "\n".join(valid)
        return f"*PreserveIncludes\n{lines}\n"

    def _create_step_config(self, doe_index: int, step_config: Dict[str, Any]) -> Optional[str]:
        """Step별 KooMeshModifier 설정 파일 생성 (output_dir에 저장)"""
        step_num = step_config["step"]
        mode = step_config["mode"]
        condition = step_config["condition"]
        params = step_config.get("params", {})

        # 이전 step의 결과 경로 (있다면)
        prev_run_dir = self._get_prev_run_dir(doe_index, step_num)

        # 모델 파일 결정
        if prev_run_dir:
            # 이전 step의 dynain을 사용
            prev_output = os.path.join(self.output_dir, prev_run_dir, "DynamicRelaxation")
            model_file = os.path.join(prev_output, "DropSet_dti.k")
            if not os.path.exists(model_file):
                logging.warning(
                    f"DYNAIN_TO_INITIAL 결과 파일 없음 (DYNAIN_TO_INITIAL 실패 가능성): "
                    f"{model_file} — 원본 모델 파일로 fallback (결과 부정확 가능)")
                model_file = self.config["project"]["model_file"]
        else:
            model_file = self.config["project"]["model_file"]

        project = self.config["project"]["name"]
        config_content = ""

        if mode == "DROP":
            # 낙하 시뮬레이션 설정
            from Runner.StepConfigBuilder import build_drop_attitude_config
            euler = self._get_doe_euler(doe_index, step_num, condition)
            sim_params = self.config.get("simulation_params", {})

            preserve_includes = self.config.get("preserve_includes", [])
            config_content = build_drop_attitude_config(
                model_file=model_file,
                output_dir=self.output_dir,
                project=project,
                doe_index=doe_index,
                step_num=step_num,
                mode=mode,
                condition=condition,
                euler=euler,
                sim_params=sim_params,
                run_directory_mode=True,
                preserve_includes=preserve_includes,
            )

        elif mode == "IMPACT":
            # 충격 위치 DOE 설정
            pos = self._get_doe_position(doe_index, step_num, condition)

            sim_params = self.config.get("simulation_params", {})
            impact_params = sim_params.get("impact", {})

            dim_damper = impact_params.get("dimension_damper", [0.001, 0.001, 0.001])
            dim_damper_str = ",".join(str(v) for v in dim_damper)
            preserve_block = self._build_preserve_block()

            config_content = f"""*Inputfile
{model_file}
*RunDirectoryMode,True,{self.output_dir}
*Info,{project},Step{step_num}
*Description,DOE{doe_index:03d} Step{step_num} {mode} {condition}
*Creator,automation,auto@system.com,CAE,AUTO
{preserve_block}*Mode
DROP_WEIGHT_IMPACT_TEST,1
**DropWeightImpactTest,1
GenerationMode,DampingSpring
LocationX,{pos['x']}
LocationY,{pos['y']}
Height,{impact_params.get('height', 0.5)}
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
Type,{impact_params.get('type', 'Sphere')}
Dimension,{impact_params.get('dimension', 0.008)}
MeshSize,{impact_params.get('mesh_size', 0.001)}
DimensionDamper,{dim_damper_str}
Density,{impact_params.get('density', 7800)}
YoungsModulus,{impact_params.get('youngs_modulus', 201e9)}
PoissonRatio,{impact_params.get('poisson_ratio', 0.3)}
tFinal,{impact_params.get('tFinal', 0.001)}
dt,{impact_params.get('dt', 1e-6)}
OffsetDistance,{impact_params.get('offset_distance', 0.00001)}
**EndDropWeightImpactTest
*End
"""

        elif mode == "THERM":
            # 열응력 시뮬레이션 설정 (기본 템플릿)
            target_temp = params.get("target_temp_C", 85)
            hold_time = params.get("hold_time_s", 1800)
            preserve_block = self._build_preserve_block()

            config_content = f"""*Inputfile
{model_file}
*RunDirectoryMode,True,{self.output_dir}
*Info,{project},Step{step_num}
*Description,DOE{doe_index:03d} Step{step_num} {mode} {condition} T={target_temp}C
*Creator,automation,auto@system.com,CAE,AUTO
{preserve_block}*Mode
THERMAL_CYCLE,1
**ThermalCycle,1
TargetTemperature,{target_temp}
HoldTime,{hold_time}
InitialTemperature,25
RampTime,600
**EndThermalCycle
*End
"""

        elif mode == "VIBRATION":
            # ─────────────────────────────────────────────────────────────
            # VIBRATION_LOAD 모드 — Registry-based zero-hardcode builder 호출
            # ─────────────────────────────────────────────────────────────
            # 설계 원칙 (design_decisions.md 채택안 A~G 준수):
            #   - DROP/IMPACT/THERM과 달리, mode 키워드/옵션 키/relative_mode 직렬화는
            #     StepConfigBuilder 내부의 `_VIB_KEYWORDS` / `_VIB_OPTION_KEYS` /
            #     `_VIB_SERIALIZERS` 카탈로그·레지스트리에서만 관리됨 (zero-hardcode).
            #   - 본 분기는 sim_params/params에서 인자만 추출 → builder에 위임.
            #
            # P1 범위: explicit_factors (relative_mode="Explicit") — part_factors 사용.
            # TODO(P2): per_cap_factors / circuit_group_factors / VolumeProportional 지원
            #          — StepConfigBuilder 측 `_VIB_SERIALIZERS`에 데코레이터로 추가 등록되며,
            #            본 분기는 인자 패스스루만 추가하면 됨 (build_vibration_load_config
            #            의 part_list / reference_part 인자 활용).
            from Runner.StepConfigBuilder import build_vibration_load_config

            sim_params = self.config.get("simulation_params", {})
            vib_params = sim_params.get("vibration", {})

            # params(step별) > vibration(전역 simulation_params) 순으로 lookup
            # — step 단위 override가 가능하도록 params를 우선
            def _vib_get(key, default=None):
                if key in params:
                    return params[key]
                return vib_params.get(key, default)

            direction = _vib_get("direction", "Z")
            load_type = _vib_get("load_type", "Force")
            relative_mode = _vib_get("relative_mode", "Explicit")
            load_curve = _vib_get("load_curve", [])
            # P1: explicit_factors — [(pid, factor), ...] 튜플 리스트 또는
            #     JSON 호환 [[pid, factor], ...] 리스트 모두 허용
            part_factors = _vib_get("part_factors", None)
            # TODO(P2): part_list / reference_part 추출 (VolumeProportional 모드용)
            part_list = _vib_get("part_list", None)
            reference_part = _vib_get("reference_part", None)

            preserve_includes = self.config.get("preserve_includes", [])
            config_content = build_vibration_load_config(
                model_file=model_file,
                output_dir=self.output_dir,
                project=project,
                doe_index=doe_index,
                step_num=step_num,
                condition=condition,
                direction=direction,
                load_type=load_type,
                relative_mode=relative_mode,
                load_curve=load_curve,
                part_factors=part_factors,
                part_list=part_list,
                reference_part=reference_part,
                run_directory_mode=True,
                preserve_includes=preserve_includes,
            )

        else:
            # 기타 모드는 기본 템플릿
            preserve_block = self._build_preserve_block()
            config_content = f"""*Inputfile
{model_file}
*RunDirectoryMode,True,{self.output_dir}
*Info,{project},Step{step_num}
*Description,DOE{doe_index:03d} Step{step_num} {mode} {condition}
*Creator,automation,auto@system.com,CAE,AUTO
{preserve_block}*Mode
{mode},1
**{mode},1
**End{mode}
*End
"""

        # 설정 파일 저장 (output_dir에 임시 저장, KooMeshModifier 실행 후 run_dir로 이동)
        config_path = os.path.join(self.output_dir, f"step_config_doe{doe_index:03d}_s{step_num:03d}.txt")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            return config_path
        except Exception as e:
            logging.error(f"Failed to write config file: {e}")
            return None

    def _get_doe_euler(self, doe_index: int, step_num: int, condition: str) -> Dict[str, float]:
        """DOE별 Euler 각도 조회

        doe_angles 테이블이 있으면 DOE별 각도 사용,
        없으면 condition 코드 기반 변환 (하위 호환)
        """
        doe_angles = self.config.get("scenario", {}).get("doe_angles", {})
        doe_key = str(doe_index)

        if doe_key in doe_angles:
            step_key = str(step_num)
            if step_key in doe_angles[doe_key]:
                angle_info = doe_angles[doe_key][step_key]
                return {
                    "roll": angle_info["roll"],
                    "pitch": angle_info["pitch"],
                    "yaw": angle_info["yaw"]
                }

        # 하위 호환: condition 코드 기반 변환
        return self._condition_to_euler(condition)

    def _get_doe_position(self, doe_index: int, step_num: int, condition: str) -> Dict[str, float]:
        """DOE별 충격 위치 조회

        doe_positions 테이블에서 DOE별 위치(X, Y) 조회
        """
        doe_positions = self.config.get("scenario", {}).get("doe_positions", {})
        doe_key = str(doe_index)

        if doe_key in doe_positions:
            step_key = str(step_num)
            if step_key in doe_positions[doe_key]:
                pos_info = doe_positions[doe_key][step_key]
                return {
                    "x": pos_info["x"],
                    "y": pos_info["y"]
                }

        logging.warning(f"DOE {doe_index} Step {step_num}의 충격 위치를 찾을 수 없습니다. 기본값(0,0) 사용")
        return {"x": 0.0, "y": 0.0}

    def _condition_to_euler(self, condition: str) -> Dict[str, float]:
        """Condition 코드 → Euler 각도 변환"""
        # Face 매핑
        face_map = {
            "F1": {"roll": 0, "pitch": 0, "yaw": 0},        # Back
            "F2": {"roll": 180, "pitch": 0, "yaw": 0},      # Front
            "F3": {"roll": 0, "pitch": -90, "yaw": 0},      # Right
            "F4": {"roll": 0, "pitch": 90, "yaw": 0},       # Left
            "F5": {"roll": 90, "pitch": 0, "yaw": 0},       # Top
            "F6": {"roll": -90, "pitch": 0, "yaw": 0},      # Bottom
        }

        # Edge 매핑 (대표적인 모서리들)
        edge_map = {
            "E1": {"roll": 45, "pitch": 0, "yaw": 0},
            "E2": {"roll": -45, "pitch": 0, "yaw": 0},
            "E3": {"roll": 0, "pitch": 45, "yaw": 0},
            "E4": {"roll": 0, "pitch": -45, "yaw": 0},
            "E5": {"roll": 45, "pitch": 45, "yaw": 0},
            "E6": {"roll": -45, "pitch": 45, "yaw": 0},
            "E7": {"roll": 45, "pitch": -45, "yaw": 0},
            "E8": {"roll": -45, "pitch": -45, "yaw": 0},
            "E9": {"roll": 135, "pitch": 0, "yaw": 0},
            "E10": {"roll": -135, "pitch": 0, "yaw": 0},
            "E11": {"roll": 0, "pitch": 135, "yaw": 0},
            "E12": {"roll": 0, "pitch": -135, "yaw": 0},
        }

        # Corner 매핑
        corner_map = {
            "C1": {"roll": 35.264, "pitch": 45, "yaw": 0},
            "C2": {"roll": -35.264, "pitch": 45, "yaw": 0},
            "C3": {"roll": 35.264, "pitch": -45, "yaw": 0},
            "C4": {"roll": -35.264, "pitch": -45, "yaw": 0},
            "C5": {"roll": 144.736, "pitch": 45, "yaw": 0},
            "C6": {"roll": -144.736, "pitch": 45, "yaw": 0},
            "C7": {"roll": 144.736, "pitch": -45, "yaw": 0},
            "C8": {"roll": -144.736, "pitch": -45, "yaw": 0},
        }

        if condition in face_map:
            return face_map[condition]
        elif condition in edge_map:
            return edge_map[condition]
        elif condition in corner_map:
            return corner_map[condition]
        else:
            logging.warning(f"Unknown condition: {condition}, using default angles")
            return {"roll": 0, "pitch": 0, "yaw": 0}

    def _run_koomeshmodifier(self, config_file: str, working_dir: str) -> Optional[str]:
        """KooMeshModifier 실행

        Returns:
            성공 시 run_id (str), 실패 시 None
            RunDirectoryMode=False거나 run_id 파싱 불가 시 빈 문자열 "" 반환 (성공은 성공)
        """
        # KooMeshModifier는 Nuitka 바이너리이므로 python3 prefix 없이 직접 실행
        cmd = [self.koomesh_path, config_file]
        # Apptainer 래핑 (설정 시)
        cmd = self.apptainer.wrap_command(cmd, use_lsdyna=False)
        logging.info(f"Running KooMeshModifier: {' '.join(cmd)}")
        logging.info(f"  working_dir: {working_dir}")

        try:
            koomesh_timeout = self.config["execution"].get("timeout_koomeshmodifier_seconds", 604800)
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=koomesh_timeout
            )

            # Apptainer 컨테이너 정리
            time.sleep(3)
            self.apptainer.cleanup_after_exec()

            # stdout/stderr 항상 기록
            if result.stdout:
                logging.info(f"KooMeshModifier stdout:\n{result.stdout}")
            if result.stderr:
                # Apptainer squashfuse cleanup 메시지 필터 (정상 종료 시 발생하는 무해한 경고)
                _stderr_lines = [l for l in result.stderr.strip().splitlines()
                                 if not any(k in l for k in ('squashfuse', 'cleanup error', 'fuse: reading device'))]
                if _stderr_lines:
                    logging.warning(f"KooMeshModifier stderr:\n" + "\n".join(_stderr_lines))

            if result.returncode != 0:
                logging.error(f"KooMeshModifier failed (returncode={result.returncode})")
                return None

            # stdout에서 run_id 파싱 — 마지막 매치 사용 (KooMeshModifier가 run_id를 여러 번 생성할 수 있음)
            import re
            matches = re.findall(r'(\S+)\s+is generated as run_id', result.stdout)
            if matches:
                run_id = matches[-1]  # 마지막 run_id가 실제 폴더에 사용됨
                logging.info(f"KooMeshModifier run_id: {run_id} (총 {len(matches)}개 중 마지막)")
                return run_id
            else:
                logging.warning("KooMeshModifier stdout에서 run_id를 찾지 못함, 폴더 탐색")
                # Run_ 폴더를 직접 탐색하여 가장 최근 생성된 것 사용
                run_dirs = sorted(
                    [d for d in os.listdir(working_dir) if d.startswith("Run_") and os.path.isdir(os.path.join(working_dir, d))],
                    key=lambda d: os.path.getmtime(os.path.join(working_dir, d)),
                    reverse=True
                )
                if run_dirs:
                    run_id = run_dirs[0].replace("Run_", "", 1)
                    logging.info(f"KooMeshModifier run_id (폴더 탐색): {run_id}")
                    return run_id
                logging.error("KooMeshModifier: Run 폴더도 찾지 못함")
                return None

        except subprocess.TimeoutExpired:
            logging.error("KooMeshModifier timed out")
            return None
        except Exception as e:
            logging.error(f"KooMeshModifier execution error: {e}")
            return None

    def _copy_pregenerated(self, doe_index: int, run_dir: str, mode: str) -> bool:
        """사전 생성된 DropSet.k를 pregenerated 디렉토리에서 run_dir로 복사

        Args:
            doe_index: DOE 인덱스 (1-based)
            run_dir: 실행 디렉토리
            mode: 시뮬레이션 모드 (DROP, IMPACT, THERM)

        Returns:
            bool: 성공 여부
        """
        # pregenerated 폴더 경로: Run_{doe_idx}/
        src_dir = os.path.join(self.pregenerated_dir, f"Run_{doe_index}")

        if not os.path.isdir(src_dir):
            logging.error(f"Pregenerated 디렉토리 없음: {src_dir}")
            return False

        # 입력 파일명 결정
        input_filename = self._find_input_file(run_dir, mode)

        # src_dir에서 모든 파일을 run_dir로 복사
        copied_files = []
        try:
            for item in os.listdir(src_dir):
                src_path = os.path.join(src_dir, item)
                dst_path = os.path.join(run_dir, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                    copied_files.append(item)
                elif os.path.isdir(src_path):
                    if os.path.exists(dst_path):
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                    copied_files.append(f"{item}/")
        except Exception as e:
            logging.error(f"Pregenerated 파일 복사 실패: {e}")
            return False

        # 입력 파일 존재 확인
        if not os.path.exists(os.path.join(run_dir, input_filename)):
            logging.error(f"Pregenerated 입력 파일 없음: {input_filename} (복사된 파일: {copied_files})")
            return False

        logging.info(f"Pregenerated 파일 복사 완료: {src_dir} → {run_dir} ({len(copied_files)}개 파일)")
        return True

    def _find_input_file(self, run_dir: str, mode: str) -> str:
        """LS-DYNA 입력 파일 찾기 (절대경로 — cwd가 Output/이므로)

        DROP/IMPACT/THERM은 KooDynaAdvancedModification 측 RunDirectory 분기에서
        고정 파일명(`DropSet.k` 등)이 강제되지만, VIBRATION은 KooMeshModifier의
        일반 경로(`additionalword += "_vib"`)를 타기 때문에 입력 모델 파일의
        베이스명에 `_vib.k` 접미사가 붙는다 (예: `MinimumModel.k` → `MinimumModel_vib.k`).
        """
        if mode == "DROP":
            fname = "DropSet.k"
        elif mode == "IMPACT":
            fname = "DropWeightImpactTestSet.k"
        elif mode == "THERM":
            fname = "ThermalSet.k"
        elif mode == "VIBRATION":
            # KooMeshModifier 일반경로: `{inputFileName}_vib.k` (replace(".k","") + "_vib" + ".k")
            # — self.config의 model_file 베이스명에 의존 (DROP과 다른 명명 규칙).
            model_file = self.config["project"]["model_file"]
            base = os.path.basename(model_file)
            if base.endswith(".k"):
                base = base[:-2]
            fname = f"{base}_vib.k"
        else:
            fname = "SimulationSet.k"
        return os.path.join(run_dir, fname)


def main():
    parser = argparse.ArgumentParser(description="Cumulative Scenario Runner")
    parser.add_argument("config", help="Path to runner_config.json")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--doe", type=int, help="Run specific DOE only (for parallel execution)")
    parser.add_argument("--skip-koomeshmodifier", action="store_true",
                        help="KooMeshModifier 실행 생략 (batch 사전 생성 모드)")
    parser.add_argument("--pregenerated-dir", type=str, default=None,
                        help="사전 생성된 DropSet.k 파일 디렉토리")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)

    runner = CumulativeScenarioRunner(
        args.config,
        doe_filter=args.doe,
        skip_koomeshmodifier=args.skip_koomeshmodifier,
        pregenerated_dir=args.pregenerated_dir
    )
    success = runner.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
