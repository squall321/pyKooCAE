#!/bin/bash
# Test_Impact_Spacing5mm: 5mm 간격 충격 DOE (멀티노드 MPI)

set -e

CONCURRENT_DOES=12
NCPU_PER_JOB=128

while [[ $# -gt 0 ]]; do
    case $1 in
        --concurrent-does) CONCURRENT_DOES="$2"; shift 2 ;;
        --ncpu-per-job) NCPU_PER_JOB="$2"; shift 2 ;;
        -h|--help)
            echo "사용법: $0 [OPTIONS]"
            echo ""
            echo "  --concurrent-does N  동시 실행 DOE 수 (기본: 12)"
            echo "  --ncpu-per-job N     노드당 CPU 수 (기본: 128)"
            exit 0 ;;
        *) echo "알 수 없는 옵션: $1"; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SCENARIO_JSON="$SCRIPT_DIR/scenario_multinode.json"
if [ ! -f "$SCENARIO_JSON" ]; then
    echo "scenario_multinode.json 없음: $SCENARIO_JSON"
    exit 1
fi

KOOCR=$(python3 -c "import json; print(json.load(open('$SCENARIO_JSON'))['environment']['koochainrun_path'])")
NODES_PER_JOB=$(python3 -c "import json; print(json.load(open('$SCENARIO_JSON'))['environment'].get('nodes_per_job', 1))")

TOTAL_NODES=$((CONCURRENT_DOES * NODES_PER_JOB))

echo "=========================================="
echo "Test_Impact_Spacing5mm: 5mm 충격 DOE (멀티노드)"
echo "=========================================="
echo ""

echo "Step 1: runner_config.json 생성 중..."
"$KOOCR" prepare "$SCENARIO_JSON" -o "$SCRIPT_DIR/runner_config_multinode.json"

if [ ! -f "$SCRIPT_DIR/runner_config_multinode.json" ]; then
    echo "runner_config_multinode.json 생성 실패"
    exit 1
fi

DOE_COUNT=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/runner_config_multinode.json'))['scenario']['doe_count'])")
echo "  생성된 충격 위치: ${DOE_COUNT}개"
echo ""

echo "Step 2: 실행 설정"
echo "  - 총 케이스: ${DOE_COUNT}개"
echo "  - nodes_per_job: ${NODES_PER_JOB}개"
echo "  - 동시 실행 DOE: ${CONCURRENT_DOES}개"
echo "  - 필요 노드: ${TOTAL_NODES}개"
echo "  - 노드당 CPU: ${NCPU_PER_JOB}개"
echo ""

read -p "실행하시겠습니까? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "실행 취소됨"
    exit 0
fi

echo ""
echo "Step 3: KooChainRun으로 작업 제출 중..."
"$KOOCR" submit "$SCRIPT_DIR/runner_config_multinode.json" \
    --nodes "$CONCURRENT_DOES" \
    --jobs-per-node 1 \
    --ncpu-per-job "$NCPU_PER_JOB"

echo ""
echo "=========================================="
echo "실행 완료"
echo "=========================================="
echo ""
echo "작업 관리:"
echo "  $SCRIPT_DIR/stop.sh              # 전체 취소"
echo "  $SCRIPT_DIR/rerun.sh --dry-run   # 상태 확인"
echo "  $SCRIPT_DIR/rerun.sh             # 실패 재실행"
echo ""
