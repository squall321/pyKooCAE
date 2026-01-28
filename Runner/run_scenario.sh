#!/bin/bash
#SBATCH --job-name=CumScenario
#SBATCH --nodes=1
#SBATCH --ntasks=32
#SBATCH --time=48:00:00
#SBATCH --output=scenario_%j.out
#SBATCH --error=scenario_%j.err
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=koo.park@samsung.com

# ============================================================================
# Cumulative Scenario Runner - SLURM Job Script
#
# Usage:
#   sbatch run_scenario.sh runner_config.json
#   sbatch run_scenario.sh runner_config.json --resume
#
# Author: koo.park
# Email: koo.park@samsung.com
# Group: CAE
# ============================================================================

# 환경 설정
module load python/3.9 2>/dev/null || true
module load lsdyna/R13 2>/dev/null || true

# 설정 파일 경로
CONFIG_FILE=${1:-runner_config.json}
EXTRA_ARGS=${@:2}

# 스크립트 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER_SCRIPT="${SCRIPT_DIR}/CumulativeScenarioRunner.py"

# 시작 시간 기록
START_TIME=$(date +%s)

echo "============================================================================"
echo "Starting Cumulative Scenario Runner"
echo "============================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Tasks: $SLURM_NTASKS"
echo "Config: $CONFIG_FILE"
echo "Extra Args: $EXTRA_ARGS"
echo "Start Time: $(date)"
echo "============================================================================"

# Config 파일 존재 확인
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE"
    exit 1
fi

# Runner 스크립트 존재 확인
if [ ! -f "$RUNNER_SCRIPT" ]; then
    echo "ERROR: Runner script not found: $RUNNER_SCRIPT"
    exit 1
fi

# Python 환경 확인
python3 --version || { echo "ERROR: Python3 not found"; exit 1; }

# Runner 실행
echo ""
echo "Executing CumulativeScenarioRunner..."
echo ""

python3 "$RUNNER_SCRIPT" "$CONFIG_FILE" $EXTRA_ARGS

EXIT_CODE=$?

# 종료 시간 및 소요 시간 계산
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))
SECONDS=$((ELAPSED % 60))

echo ""
echo "============================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "Scenario completed successfully"
else
    echo "Scenario failed with exit code $EXIT_CODE"
fi
echo "End Time: $(date)"
echo "Elapsed Time: ${HOURS}h ${MINUTES}m ${SECONDS}s"
echo "============================================================================"

exit $EXIT_CODE
