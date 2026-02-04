#!/bin/bash
# Test_001: 전각도 26방향 1회 낙하 (멀티노드 MPI)
#
# 멀티노드 MPI 모드:
#   - 각 DOE가 nodes_per_job(=2)개 노드를 점유
#   - mpirun이 apptainer 바깥에서 실행
#   - mpirun -np {total_cpu} -hostfile $SLURM_NODEFILE apptainer exec ... lsdyna ...
#
# 자원 계산 예시 (디폴트):
#   - 동시 DOE 12개 x nodes_per_job 2 = 24노드 필요
#   - 각 DOE: 2노드 x 128코어 = 256 MPI ranks

set -e

# 디폴트 설정
CONCURRENT_DOES=12       # 동시 실행 DOE 수
NCPU_PER_JOB=128         # 노드당 CPU 수 (nodes_per_job은 scenario_multinode.json에서 설정)

# 옵션 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        --concurrent-does) CONCURRENT_DOES="$2"; shift 2 ;;
        --ncpu-per-job) NCPU_PER_JOB="$2"; shift 2 ;;
        -h|--help)
            echo "사용법: $0 [OPTIONS]"
            echo ""
            echo "멀티노드 MPI 모드: 각 DOE가 여러 노드를 점유하여 실행"
            echo ""
            echo "  --concurrent-does N  동시 실행 DOE 수 (기본: 12)"
            echo "  --ncpu-per-job N     노드당 CPU 수 (기본: 128)"
            echo ""
            echo "nodes_per_job은 scenario_multinode.json의 environment.nodes_per_job에서 설정"
            echo ""
            echo "자원 계산:"
            echo "  필요 노드 = concurrent_does x nodes_per_job"
            echo "  MPI ranks/DOE = ncpu_per_job x nodes_per_job"
            exit 0 ;;
        *) echo "알 수 없는 옵션: $1"; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# scenario_multinode.json 사용
SCENARIO_JSON="$SCRIPT_DIR/scenario_multinode.json"
if [ ! -f "$SCENARIO_JSON" ]; then
    echo "❌ scenario_multinode.json 없음: $SCENARIO_JSON"
    exit 1
fi

KOOCR=$(python3 -c "import json; print(json.load(open('$SCENARIO_JSON'))['environment']['koochainrun_path'])")
NODES_PER_JOB=$(python3 -c "import json; print(json.load(open('$SCENARIO_JSON'))['environment'].get('nodes_per_job', 1))")

TOTAL_NODES=$((CONCURRENT_DOES * NODES_PER_JOB))
TOTAL_MPI_RANKS=$((NCPU_PER_JOB * NODES_PER_JOB))

echo "=========================================="
echo "Test_001: 전각도 26방향 1회 낙하 (멀티노드)"
echo "=========================================="
echo "프로젝트 루트: $PROJECT_ROOT"
echo ""

# Step 1: runner_config.json 생성
echo "Step 1: runner_config.json 생성 중..."
"$KOOCR" prepare "$SCENARIO_JSON" -o "$SCRIPT_DIR/runner_config_multinode.json"

if [ ! -f "$SCRIPT_DIR/runner_config_multinode.json" ]; then
    echo "❌ runner_config_multinode.json 생성 실패"
    exit 1
fi
echo ""

# Step 2: 실행 설정 확인
echo "Step 2: 실행 설정"
echo "  - 총 케이스: 26개"
echo "  - nodes_per_job: ${NODES_PER_JOB}개 (DOE당 노드 수)"
echo "  - 동시 실행 DOE: ${CONCURRENT_DOES}개"
echo "  - 필요 노드: ${TOTAL_NODES}개"
echo "  - 노드당 CPU: ${NCPU_PER_JOB}개"
echo "  - DOE당 MPI ranks: ${TOTAL_MPI_RANKS}개"
echo ""
echo "MPI 구조: mpirun → apptainer exec → lsdyna (호스트 MPI)"
echo ""

# Step 3: 실행 확인
read -p "실행하시겠습니까? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "실행 취소됨"
    exit 0
fi

# Step 4: KooChainRun으로 작업 제출
echo ""
echo "Step 3: KooChainRun으로 작업 제출 중..."
"$KOOCR" submit "$SCRIPT_DIR/runner_config_multinode.json" \
    --nodes "$CONCURRENT_DOES" \
    --jobs-per-node 1 \
    --ncpu-per-job "$NCPU_PER_JOB"

echo ""
echo "=========================================="
echo "✅ 실행 완료"
echo "=========================================="
echo ""
echo "진행 상황 확인:"
echo "  $KOOCR status"
echo "  squeue -u \$USER"
echo ""
echo "결과 수집:"
echo "  $KOOCR collect $SCRIPT_DIR/runner_config_multinode.json"
