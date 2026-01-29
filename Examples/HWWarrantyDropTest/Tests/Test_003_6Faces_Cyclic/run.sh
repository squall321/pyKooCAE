#!/bin/bash
# Test_003: 6면 3회 연속 낙하 (Cyclic 각도 믹싱)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
KOOCR="$PROJECT_ROOT/koocr"

echo "=========================================="
echo "Test_003: 6면 3회 연속 낙하 (Cyclic)"
echo "=========================================="
echo "프로젝트 루트: $PROJECT_ROOT"
echo ""

echo "Step 1: runner_config.json 생성 중..."
"$KOOCR" prepare "$SCRIPT_DIR/scenario.json" -o "$SCRIPT_DIR/runner_config.json"

if [ ! -f "$SCRIPT_DIR/runner_config.json" ]; then
    echo "❌ runner_config.json 생성 실패"
    exit 1
fi
echo ""

echo "실행 설정:"
echo "  - 총 케이스: 6개 (6면)"
echo "  - 연속 낙하: 3회"
echo "  - 노드: 1개"
echo "  - 노드당 Job: 6개"
echo "  - 동시 실행: 6개"
echo "  - 예상 Rounds: 1회 × 3 Steps = 3회"
echo "  - 예상 시간: ~9시간"
echo ""
echo "각도 믹싱: cyclic"
echo "  Step 1: Top (0°)"
echo "  Step 2: Bottom (180°)"
echo "  Step 3: Front (90°)"
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
    --nodes 1 \
    --jobs-per-node 6 \
    --ncpu-per-job 16

echo ""
echo "=========================================="
echo "✅ 실행 완료"
echo "=========================================="
echo ""
echo "진행 상황 확인:"
echo "  squeue -u \$USER"
echo "  find /data/Test_003_6Faces_Cyclic -name '*.lock' | wc -l"
