#!/usr/bin/env python3
"""
노드 점유율 모니터링 및 통계

주요 기능:
    1. 실시간 노드 점유율 모니터링
    2. Step별 자원 사용량 통계
    3. 자원 효율성 분석
    4. 시각화 (선택적)

사용 시나리오:
    - 클러스터 자원 사용 현황 파악
    - 자원 최적화 전략 수립
    - 비용 분석

Author: koo.park
Email: koo.park@samsung.com
"""

import os
import sys
import json
import time
import argparse
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class NodeOccupancyMonitor:
    """노드 점유율 모니터터"""

    def __init__(self, project_name: str = None):
        """
        Parameters:
            project_name: 프로젝트 이름 (필터링용)
        """
        self.project_name = project_name
        self.history = []  # 히스토리 저장

    # ========================================================================
    # 실시간 모니터링
    # ========================================================================

    def get_current_jobs(self, user: str = None) -> List[Dict[str, Any]]:
        """
        현재 실행 중인 Job 목록 조회

        Parameters:
            user: 사용자 이름 (None이면 현재 사용자)

        Returns:
            Job 정보 리스트
        """
        if user is None:
            user = os.environ.get("USER", "")

        # squeue로 Job 조회
        cmd = [
            "squeue",
            "-u", user,
            "-o", "%i|%j|%t|%M|%D|%C|%m|%P",
            "--noheader"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"⚠️  squeue 실패: {result.stderr}")
            return []

        jobs = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split('|')
            if len(parts) < 8:
                continue

            job_id, name, state, time, nodes, cpus, mem, partition = parts

            jobs.append({
                "job_id": job_id,
                "name": name,
                "state": state,
                "time": time,
                "nodes": int(nodes) if nodes.isdigit() else 0,
                "cpus": int(cpus) if cpus.isdigit() else 0,
                "memory": mem,
                "partition": partition
            })

        return jobs

    def print_current_status(self, jobs: List[Dict[str, Any]]):
        """
        현재 상태 출력

        Parameters:
            jobs: Job 정보 리스트
        """
        if not jobs:
            print("실행 중인 Job 없음")
            return

        # 통계 계산
        total_nodes = sum(j["nodes"] for j in jobs)
        total_cpus = sum(j["cpus"] for j in jobs)

        state_counts = defaultdict(int)
        for job in jobs:
            state_counts[job["state"]] += 1

        # 출력
        print("=" * 100)
        print(f"현재 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"총 Job 수: {len(jobs)} | 총 노드: {total_nodes} | 총 CPU: {total_cpus}")
        print(f"상태: {dict(state_counts)}")
        print("=" * 100)
        print(f"{'Job ID':<12} {'이름':<30} {'상태':<10} {'시간':<12} {'노드':<6} {'CPU':<6} {'메모리':<10} {'파티션':<10}")
        print("-" * 100)

        for job in jobs:
            print(f"{job['job_id']:<12} {job['name']:<30} {job['state']:<10} {job['time']:<12} "
                  f"{job['nodes']:<6} {job['cpus']:<6} {job['memory']:<10} {job['partition']:<10}")

        print("=" * 100)

    def monitor(self, interval: int = 60, max_iterations: int = 0):
        """
        실시간 모니터링

        Parameters:
            interval: 체크 간격 (초)
            max_iterations: 최대 반복 횟수 (0: 무한)
        """
        iteration = 0

        print("\n========================================")
        print("노드 점유율 실시간 모니터링 시작")
        print(f"체크 간격: {interval}초")
        print("========================================\n")

        try:
            while True:
                iteration += 1

                # Job 조회
                jobs = self.get_current_jobs()

                # 프로젝트 필터링
                if self.project_name:
                    jobs = [j for j in jobs if self.project_name in j["name"]]

                # 출력
                self.print_current_status(jobs)

                # 히스토리 저장
                self.history.append({
                    "timestamp": datetime.now().isoformat(),
                    "jobs": jobs
                })

                # 종료 조건
                if max_iterations > 0 and iteration >= max_iterations:
                    print(f"\n✅ {max_iterations}회 반복 완료")
                    break

                if not jobs:
                    print("\n✅ 모든 Job 완료")
                    break

                # 대기
                print(f"\n다음 체크: {interval}초 후... (Ctrl+C로 중단)\n")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n⚠️  모니터링 중단됨")

    # ========================================================================
    # 통계 분석
    # ========================================================================

    def analyze_step_resources(
        self,
        job_metadata: Dict[str, Any]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Step별 자원 사용량 분석

        Parameters:
            job_metadata: Job 메타데이터 (DirectInputWorkflow)

        Returns:
            Step별 통계
        """
        step_resources = job_metadata.get("step_resources", {})
        num_steps = job_metadata.get("num_steps", 0)

        stats = {}

        for step in range(1, num_steps + 1):
            res = step_resources.get(str(step), {})

            nnodes = res.get("nnodes", 1)
            ncpus_per_node = res.get("ncpus_per_node", 32)
            walltime = res.get("walltime", "02:00:00")

            # Walltime 파싱 (HH:MM:SS → 시간)
            h, m, s = map(int, walltime.split(':'))
            walltime_hours = h + m/60 + s/3600

            # CPU-시간 계산
            total_cpus = nnodes * ncpus_per_node
            cpu_hours = total_cpus * walltime_hours

            stats[step] = {
                "nnodes": nnodes,
                "ncpus_per_node": ncpus_per_node,
                "total_cpus": total_cpus,
                "walltime": walltime,
                "walltime_hours": walltime_hours,
                "cpu_hours": cpu_hours
            }

        return stats

    def print_resource_summary(self, stats: Dict[int, Dict[str, Any]]):
        """
        자원 사용량 요약 출력

        Parameters:
            stats: Step별 통계
        """
        print("\n========================================")
        print("Step별 자원 사용량 요약")
        print("========================================\n")

        print(f"{'Step':<6} {'노드':<6} {'CPU/노드':<10} {'총 CPU':<10} {'실행 시간':<12} {'CPU-시간':<12}")
        print("-" * 60)

        total_cpu_hours = 0

        for step, stat in sorted(stats.items()):
            print(f"{step:<6} {stat['nnodes']:<6} {stat['ncpus_per_node']:<10} "
                  f"{stat['total_cpus']:<10} {stat['walltime']:<12} {stat['cpu_hours']:.1f}")

            total_cpu_hours += stat['cpu_hours']

        print("-" * 60)
        print(f"{'총합':<6} {'':<6} {'':<10} {'':<10} {'':<12} {total_cpu_hours:.1f}")
        print("=" * 60)

        print(f"\n총 CPU-시간: {total_cpu_hours:.1f} CPU-hours")

        # 병렬 효율성 계산
        max_cpus = max(s['total_cpus'] for s in stats.values())
        total_walltime = sum(s['walltime_hours'] for s in stats.values())
        ideal_cpu_hours = max_cpus * total_walltime
        efficiency = (total_cpu_hours / ideal_cpu_hours) * 100 if ideal_cpu_hours > 0 else 0

        print(f"병렬 효율성: {efficiency:.1f}% (최대 CPU 대비)")

    # ========================================================================
    # 히스토리 분석
    # ========================================================================

    def save_history(self, output_path: str):
        """
        히스토리 저장

        Parameters:
            output_path: 출력 파일 경로
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

        print(f"✅ 히스토리 저장: {output_path}")

    def plot_history(self, output_path: str = None):
        """
        히스토리 시각화 (matplotlib 필요)

        Parameters:
            output_path: 출력 파일 경로 (None이면 화면 표시)
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from datetime import datetime as dt
        except ImportError:
            print("⚠️  matplotlib 설치 필요: pip install matplotlib")
            return

        if not self.history:
            print("⚠️  히스토리 없음")
            return

        # 데이터 추출
        timestamps = [dt.fromisoformat(h["timestamp"]) for h in self.history]
        node_counts = [sum(j["nodes"] for j in h["jobs"]) for h in self.history]
        cpu_counts = [sum(j["cpus"] for j in h["jobs"]) for h in self.history]

        # 플롯
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # 노드 수
        ax1.plot(timestamps, node_counts, marker='o', linestyle='-', color='blue')
        ax1.set_xlabel('시간')
        ax1.set_ylabel('노드 수')
        ax1.set_title('노드 점유율')
        ax1.grid(True)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

        # CPU 수
        ax2.plot(timestamps, cpu_counts, marker='s', linestyle='-', color='red')
        ax2.set_xlabel('시간')
        ax2.set_ylabel('CPU 수')
        ax2.set_title('CPU 점유율')
        ax2.grid(True)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"✅ 플롯 저장: {output_path}")
        else:
            plt.show()


# ========================================================================
# CLI
# ========================================================================

def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description="노드 점유율 모니터링"
    )

    subparsers = parser.add_subparsers(dest="command", help="명령")

    # monitor 명령
    monitor_parser = subparsers.add_parser("monitor", help="실시간 모니터링")
    monitor_parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="체크 간격 (초, 기본: 60)"
    )
    monitor_parser.add_argument(
        "--max-iterations",
        type=int,
        default=0,
        help="최대 반복 횟수 (0: 무한)"
    )
    monitor_parser.add_argument(
        "--project",
        help="프로젝트 이름 필터"
    )
    monitor_parser.add_argument(
        "--save",
        help="히스토리 저장 경로"
    )
    monitor_parser.add_argument(
        "--plot",
        help="플롯 저장 경로"
    )

    # analyze 명령
    analyze_parser = subparsers.add_parser("analyze", help="자원 사용량 분석")
    analyze_parser.add_argument(
        "job_metadata",
        help="Job 메타데이터 JSON 파일"
    )

    args = parser.parse_args()

    if args.command == "monitor":
        # 모니터링
        monitor = NodeOccupancyMonitor(project_name=args.project)
        monitor.monitor(
            interval=args.interval,
            max_iterations=args.max_iterations
        )

        # 히스토리 저장
        if args.save:
            monitor.save_history(args.save)

        # 플롯
        if args.plot:
            monitor.plot_history(args.plot)

    elif args.command == "analyze":
        # 분석
        with open(args.job_metadata, 'r', encoding='utf-8') as f:
            job_metadata = json.load(f)

        monitor = NodeOccupancyMonitor()
        stats = monitor.analyze_step_resources(job_metadata)
        monitor.print_resource_summary(stats)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
