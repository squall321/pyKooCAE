#!/bin/bash
# Test_Impact_Spacing5mm: 5mm 간격 전 위치 충격 DOE 실행 스크립트

set -e

# 디폴트 설정
NODES=4
JOBS_PER_NODE=4
NCPU_PER_JOB=1

# 옵션 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        --nodes) NODES="$2"; shift 2 ;;
        --jobs-per-node) JOBS_PER_NODE="$2"; shift 2 ;;
        --ncpu-per-job) NCPU_PER_JOB="$2"; shift 2 ;;
        -h|--help)
            echo "사용법: $0 [OPTIONS]"
            echo "  --nodes N          노드 수 (기본: 4)"
            echo "  --jobs-per-node N  노드당 Job 수 (기본: 4)"
            echo "  --ncpu-per-job N   Job당 CPU 수 (기본: 1)"
            exit 0 ;;
        *) echo "알 수 없는 옵션: $1"; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOOCR=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/scenario.json'))['environment']['koochainrun_path'])")

echo "=========================================="
echo "Test_Impact_Spacing5mm: 5mm 간격 충격 DOE"
echo "=========================================="
echo ""

# Step 1: runner_config.json 생성
echo "Step 1: runner_config.json 생성 중..."
"$KOOCR" prepare "$SCRIPT_DIR/scenario.json" -o "$SCRIPT_DIR/runner_config.json"

if [ ! -f "$SCRIPT_DIR/runner_config.json" ]; then
    echo "runner_config.json 생성 실패"
    exit 1
fi

# DOE 수 출력
DOE_COUNT=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/runner_config.json'))['scenario']['doe_count'])")
echo "  생성된 충격 위치: ${DOE_COUNT}개"
echo ""

# Step 2: 실행 설정 확인
echo "Step 2: 실행 설정"
echo "  - 총 케이스: ${DOE_COUNT}개"
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
echo "실행 완료"
echo "=========================================="
echo ""
echo "작업 관리:"
echo "  $SCRIPT_DIR/stop.sh              # 전체 취소"
echo "  $SCRIPT_DIR/rerun.sh --dry-run   # 상태 확인"
echo "  $SCRIPT_DIR/rerun.sh             # 실패 재실행"
echo "  $KOOCR diagnose $SCRIPT_DIR      # 실패 진단"
echo ""
