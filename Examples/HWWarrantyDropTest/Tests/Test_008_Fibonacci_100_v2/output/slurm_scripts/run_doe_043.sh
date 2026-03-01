#!/bin/bash
#SBATCH --job-name=Test_008_Fibonacci_100_v2_DOE043
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=24:00:00
#SBATCH --output=/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_008_Fibonacci_100_v2/output/slurm_scripts/doe_043_%j.log
#SBATCH --error=/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_008_Fibonacci_100_v2/output/slurm_scripts/doe_043_%j.log
export APPTAINER_TMPDIR=/data/tmp

echo "========================================"
echo "Job: Test_008_Fibonacci_100_v2_DOE043"
echo "DOE: 43/100"
echo "Node: $(hostname)"
echo "Start: $(date)"
echo "========================================"

/data/SmartTwinPreprocessor/bin/KooChainRun run /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_008_Fibonacci_100_v2/runner_config.json --doe 43 --skip-koomeshmodifier --pregenerated-dir /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_008_Fibonacci_100_v2/output/pregenerated

EXIT_CODE=$?

echo "========================================"
echo "End: $(date)"
echo "Exit code: $EXIT_CODE"
echo "========================================"

exit $EXIT_CODE
