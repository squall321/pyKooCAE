#!/bin/bash
# Test_004: Pitching Sweep -40° ~ +40° (1° 간격)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
KOOCR="$PROJECT_ROOT/koocr"

echo "=========================================="
echo "Test_004: Pitching Sweep -40° ~ +40°"
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
echo "  - 총 케이스: 81개 (Pitch -40° ~ +40°, 1° 간격)"
echo "  - Roll: 0° (고정)"
echo "  - Yaw: 0° (고정)"
echo "  - 노드: 3개"
echo "  - 노드당 Job: 5개"
echo "  - 동시 실행: 15개"
echo "  - 예상 Rounds: 6회"
echo "  - 예상 시간: ~18시간"
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
    --nodes 3 \
    --jobs-per-node 5 \
    --ncpu-per-job 16

echo ""
echo "=========================================="
echo "✅ 실행 완료"
echo "=========================================="
echo ""
echo "진행 상황 확인:"
echo "  squeue -u \$USER"
echo "  find /data/Test_004_Pitching_Sweep -name '*.lock' | wc -l"
