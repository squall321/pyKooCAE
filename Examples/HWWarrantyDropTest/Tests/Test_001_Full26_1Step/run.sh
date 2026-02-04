#!/bin/bash
# Test_001: 전각도 26방향 1회 낙하 실행 스크립트

set -e  # 오류 발생 시 중단

# 디폴트 설정
NODES=23
JOBS_PER_NODE=2
NCPU_PER_JOB=64

# 옵션 파싱
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
# Tests/Test_001 → Examples/HWWarrantyDropTest → pyKooCAE
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# KooChainRun CLI path
KOOCR=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/scenario.json'))['environment']['koochainrun_path'])")

echo "=========================================="
echo "Test_001: 전각도 26방향 1회 낙하"
echo "=========================================="
echo "프로젝트 루트: $PROJECT_ROOT"
echo ""

# Step 1: runner_config.json 생성
echo "Step 1: runner_config.json 생성 중..."
"$KOOCR" prepare "$SCRIPT_DIR/scenario.json" -o "$SCRIPT_DIR/runner_config.json"

if [ ! -f "$SCRIPT_DIR/runner_config.json" ]; then
    echo "❌ runner_config.json 생성 실패"
    exit 1
fi
echo ""

# Step 2: 실행 설정 확인
echo "Step 2: 실행 설정"
echo "  - 총 케이스: 26개"
echo "  - 노드: ${NODES}개"
echo "  - 노드당 Job: ${JOBS_PER_NODE}개"
echo "  - 동시 실행: $((NODES * JOBS_PER_NODE))개"
echo "  - Job당 CPU: ${NCPU_PER_JOB}개"
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
"$KOOCR" submit "$SCRIPT_DIR/runner_config.json" \
    --nodes "$NODES" \
    --jobs-per-node "$JOBS_PER_NODE" \
    --ncpu-per-job "$NCPU_PER_JOB"

echo ""
echo "=========================================="
echo "✅ 실행 완료"
echo "=========================================="
echo ""
echo "진행 상황 확인:"
echo "  $KOOCR status"
echo "  find RUNDIR -name 'Step001.lock' | wc -l"
echo ""
echo "결과 수집:"
echo "  $KOOCR collect $SCRIPT_DIR/runner_config.json"
