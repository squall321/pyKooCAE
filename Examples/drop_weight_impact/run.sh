#!/bin/bash
# 전위치 부분충격 (Ball Drop) 시뮬레이션
#
# 사용법:
#   ./run.sh                           기본 설정으로 실행
#   ./run.sh --nodes 10                노드 10개로 실행
#   ./run.sh --ncpu-per-job 32         Job당 CPU 32개
#   ./run.sh --dry-run                 제출 없이 설정만 생성
#
# 옵션:
#   --nodes N          사용할 Slurm 노드 수 (기본: 5)
#   --jobs-per-node N  노드당 동시 실행 Job 수 (기본: 2)
#   --ncpu-per-job N   각 Job이 사용할 CPU 수 (기본: 16)
#   --dry-run          prepare만 실행하고 submit은 하지 않음
#   -h, --help         도움말

set -e

NODES=5
JOBS_PER_NODE=2
NCPU_PER_JOB=16
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --nodes) NODES="$2"; shift 2 ;;
        --jobs-per-node) JOBS_PER_NODE="$2"; shift 2 ;;
        --ncpu-per-job) NCPU_PER_JOB="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help)
            echo "전위치 부분충격 (Ball Drop) 시뮬레이션"
            echo ""
            echo "사용법: $0 [OPTIONS]"
            echo ""
            echo "옵션:"
            echo "  --nodes N          Slurm 노드 수 (기본: 5)"
            echo "  --jobs-per-node N  노드당 Job 수 (기본: 2)"
            echo "  --ncpu-per-job N   Job당 CPU 수 (기본: 16)"
            echo "  --dry-run          설정 생성만, 제출 안 함"
            echo ""
            echo "scenario.json 주요 설정:"
            echo "  model_file         LS-DYNA 모델 파일 경로"
            echo "  impactor.type      충격자 형상 (Sphere/Cylinder)"
            echo "  impactor.radius    충격자 반경 (mm)"
            echo "  impactor.height    낙하 높이 (mm)"
            echo "  locations.mode     위치 생성 (grid/list/lhs)"
            echo "  locations.margin   모델 대비 범위 비율 (0~1)"
            echo "  locations.spacing  격자 간격 (mm, grid 모드)"
            echo "  boundary_distance  부분 강체화 반경 (mm)"
            echo ""
            echo "흐름:"
            echo "  1. prepare  → 충격 위치 DOE + step_config + run.sh 생성"
            echo "  2. submit   → Slurm array job으로 전위치 병렬 실행"
            echo "  3. collect  → 결과 수집 + 리포트"
            exit 0 ;;
        *) echo "알 수 없는 옵션: $1"; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# KooChainRun 경로 (scenario.json에서 읽기)
KOOCR=$(python3 -c "
import json
cfg = json.load(open('$SCRIPT_DIR/scenario.json'))
print(cfg.get('environment',{}).get('koochainrun_path', '/data/SmartTwinPreprocessor/bin/KooChainRun'))
" 2>/dev/null || echo "/data/SmartTwinPreprocessor/bin/KooChainRun")

echo "=========================================="
echo "전위치 부분충격 (Ball Drop) 시뮬레이션"
echo "=========================================="
echo ""

# scenario.json 요약 출력
python3 -c "
import json
cfg = json.load(open('$SCRIPT_DIR/scenario.json'))
sp = cfg.get('simulation_params', {})
imp = sp.get('impactor', {})
loc = sp.get('locations', {})
print(f'  모델: {cfg.get(\"model_file\", \"?\")}')
print(f'  충격자: {imp.get(\"type\",\"?\")} R={imp.get(\"radius\",\"?\")}mm H={imp.get(\"height\",\"?\")}mm')
print(f'  위치 모드: {loc.get(\"mode\",\"grid\")}', end='')
if 'spacing' in loc:
    print(f' (spacing={loc[\"spacing\"]}mm)')
elif 'x_count' in loc:
    print(f' ({loc.get(\"x_count\",\"?\")}x{loc.get(\"y_count\",\"?\")})')
else:
    print()
print(f'  margin: {loc.get(\"margin\", 0.9)}')
print(f'  tFinal: {sp.get(\"tFinal\",\"?\")}s')
print(f'  generation_mode: {sp.get(\"generation_mode\",\"DampingSpring\")}')
" 2>/dev/null
echo ""

# Step 1: prepare
echo "Step 1: runner_config.json 생성 중..."
"$KOOCR" prepare "$SCRIPT_DIR/scenario.json" -o "$SCRIPT_DIR/runner_config.json"

if [ ! -f "$SCRIPT_DIR/runner_config.json" ]; then
    echo "❌ runner_config.json 생성 실패"
    exit 1
fi
echo ""

# 총 케이스 수 읽기
TOTAL=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/runner_config.json'))['total_cases'])" 2>/dev/null || echo "?")

echo "실행 설정:"
echo "  - 총 케이스: ${TOTAL}개"
echo "  - 노드: ${NODES}개"
echo "  - 노드당 Job: ${JOBS_PER_NODE}개"
echo "  - 동시 실행: $((NODES * JOBS_PER_NODE))개"
echo "  - Job당 CPU: ${NCPU_PER_JOB}개"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "✅ Dry run 완료 (제출 안 함)"
    echo "  runner_config: $SCRIPT_DIR/runner_config.json"
    echo "  수동 제출: KooChainRun submit $SCRIPT_DIR/runner_config.json"
    exit 0
fi

read -p "실행하시겠습니까? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "실행 취소됨"
    exit 0
fi

# Step 2: submit
echo ""
echo "Step 2: 작업 제출 중..."
"$KOOCR" submit "$SCRIPT_DIR/runner_config.json"

echo ""
echo "=========================================="
echo "✅ 제출 완료"
echo "=========================================="
echo ""
echo "상태 확인: KooChainRun collect $SCRIPT_DIR/runner_config.json"
