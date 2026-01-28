#!/bin/bash
#SBATCH --job-name=CumScenario_Parallel
#SBATCH --nodes=5
#SBATCH --ntasks-per-node=32
#SBATCH --time=24:00:00
#SBATCH --output=scenario_parallel_%j.out
#SBATCH --error=scenario_parallel_%j.err

# ============================================================================
# Cumulative Scenario Runner - Parallel DOE Execution
#
# 여러 DOE 케이스를 병렬로 실행
# 각 DOE는 독립적이므로 동시 실행 가능
#
# Usage:
#   sbatch run_scenario_parallel.sh runner_config.json 5
#   (5개 DOE를 5개 노드에서 병렬 실행)
#
# Author: koo.park
# Email: koo.park@samsung.com
# Group: CAE
# ============================================================================

# 설정 파일 경로
CONFIG_FILE=${1:-runner_config.json}
DOE_COUNT=${2:-5}

# 스크립트 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER_SCRIPT="${SCRIPT_DIR}/CumulativeScenarioRunner.py"

echo "============================================================================"
echo "Starting Parallel Cumulative Scenario Runner"
echo "============================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Nodes: $SLURM_NODELIST"
echo "Config: $CONFIG_FILE"
echo "DOE Count: $DOE_COUNT"
echo "Start Time: $(date)"
echo "============================================================================"

# DOE 병렬 실행
for DOE in $(seq 1 $DOE_COUNT); do
    echo "Launching DOE $DOE..."
    srun --nodes=1 --ntasks=32 --exclusive \
        python3 "$RUNNER_SCRIPT" "$CONFIG_FILE" --doe=$DOE &
done

# 모든 DOE 완료 대기
wait

echo ""
echo "============================================================================"
echo "All DOE cases completed"
echo "End Time: $(date)"
echo "============================================================================"
