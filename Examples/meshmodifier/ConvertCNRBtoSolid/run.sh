#!/bin/bash
# CNRB to Solid Cylinder 변환 예제
# 사용법: ./run.sh
#
# 입력: sample_cnrb.k (CNRB 포함 모델)
# 출력: sample_cnrb_cnrb2solid.k (CNRB → hexa 실린더 변환)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# KooMeshModifier 경로 (로컬 빌드 또는 배포)
MESHMOD="${MESHMOD:-/data/SmartTwinPreprocessor/bin/KooMeshModifier}"

if [ ! -f "$MESHMOD" ]; then
    # Python 직접 실행
    MESHMOD="python3 ../../occProject/Generators/KooMeshModifier.py"
fi

echo "=========================================="
echo "CNRB to Solid Cylinder Example"
echo "=========================================="
echo "Input:  sample_cnrb.k"
echo "Config: step_config.txt"
echo ""

$MESHMOD step_config.txt

echo ""
echo "=========================================="
echo "Output files:"
ls -lh sample_cnrb_cnrb2solid.k 2>/dev/null || echo "  (출력 파일 없음)"
echo "=========================================="
