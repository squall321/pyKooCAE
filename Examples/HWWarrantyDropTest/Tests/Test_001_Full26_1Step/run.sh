#!/bin/bash
# Test_001: 전각도 26방향 1회 낙하 실행 스크립트

set -e  # 오류 발생 시 중단

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Tests/Test_001 → Examples/HWWarrantyDropTest → pyKooCAE
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# KooChainRun CLI path
KOOCR="$PROJECT_ROOT/koocr"

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
echo "  - 노드: 2개"
echo "  - 노드당 Job: 4개"
echo "  - 동시 실행: 8개"
echo "  - 예상 Rounds: 4회"
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
    --nodes 2 \
    --jobs-per-node 4 \
    --ncpu-per-job 16

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
