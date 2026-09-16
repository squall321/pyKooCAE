#!/bin/bash
# Test_009: Fibonacci Lattice 100방향 (Scratch Run)

set -e

NODES=23
JOBS_PER_NODE=2
NCPU_PER_JOB=64

while [[ $# -gt 0 ]]; do
    case $1 in
        --nodes) NODES="$2"; shift 2 ;;
        --jobs-per-node) JOBS_PER_NODE="$2"; shift 2 ;;
        --ncpu-per-job) NCPU_PER_JOB="$2"; shift 2 ;;
        -h|--help)
            echo "사용법: $0 [OPTIONS]"
            echo "  --nodes N          노드 수 (기본: 23)"
            echo "  --jobs-per-node N  노드당 Job 수 (기본: 2)"
            echo "  --ncpu-per-job N   Job당 CPU 수 (기본: 64)"
            exit 0 ;;
        *) echo "알 수 없는 옵션: $1"; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOOCR=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/scenario.json'))['environment']['koochainrun_path'])")

echo "=========================================="
echo "Test_009: Fibonacci Lattice 100방향 (Scratch Run)"
echo "=========================================="

echo "Step 1: runner_config.json 및 헬퍼 스크립트 생성 중..."
"$KOOCR" prepare "$SCRIPT_DIR/scenario.json" -o "$SCRIPT_DIR/runner_config.json"

if [ ! -f "$SCRIPT_DIR/runner_config.json" ]; then
    echo "❌ runner_config.json 생성 실패"
    exit 1
fi
echo ""

echo "실행 설정:"
echo "  - 총 케이스: 100개"
echo "  - 노드: ${NODES}개"
echo "  - 노드당 Job: ${JOBS_PER_NODE}개"
echo "  - 동시 실행: $((NODES * JOBS_PER_NODE))개"
echo "  - Job당 CPU: ${NCPU_PER_JOB}개"
echo "  - Scratch 실행: /scratch (완료 시 자동 정리)"
echo ""

read -p "실행하시겠습니까? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "실행 취소됨"
    exit 0
fi

echo ""
echo "KooChainRun으로 작업 제출 중..."
"$KOOCR" submit "$SCRIPT_DIR/runner_config.json" \
    --nodes "$NODES" \
    --jobs-per-node "$JOBS_PER_NODE" \
    --ncpu-per-job "$NCPU_PER_JOB"

echo ""
echo "=========================================="
echo "✅ 실행 완료"
echo "=========================================="
