#!/bin/bash
# 전각도 집계 리포트(sphere_report)를 최신 배포본으로 재생성한다. LS-DYNA 불필요
#
# 사용법:
#   TEST_DIR=/data/koopark/Test_Postprocess_v14 bash regen_sphere_report.sh
#
# 환경변수: TEST_DIR(필수) SIF YIELD_STRESS(350) OUT_NAME(sphere_report)
#
# 🔴 입력은 `$TEST_DIR/analysis_results/<Run>/` 다. 이 디렉터리는 각 방향의
#    `output/Run_*/Output/report/` 를 가리키는 심볼릭 링크 모음이고, 거기 있는
#    `analysis_result.json` 을 읽는다(loader.py:961, 655). 즉 **deep_report 를 먼저 돌려야 한다**,
#    그리고 `report_norender/`(light 변형)는 링크 대상이 아니라 집계에 안 들어간다.
#    에너지 흐름·접촉 프로파일 탭만 binout 을 추가로 직접 읽는다.
# 🔴 `--json` 은 `--format` 에 json 이 있어야 효력이 있다(`__main__.py:145`). 없으면
#    경로만 받고 조용히 아무 파일도 안 만든다 — 기존 스크립트가 이 함정에 걸려 있었다.
set -e
TEST_DIR="${TEST_DIR:?TEST_DIR 를 지정할 것}"
SIF="${SIF:-/data/SmartTwinPostprocessor/SmartTwinPostprocessor.sif}"
YIELD="${YIELD_STRESS:-350}"
OUT="$TEST_DIR/output"
NAME="${OUT_NAME:-sphere_report}"

if [ ! -d "$TEST_DIR/analysis_results" ]; then
    echo "ERROR: $TEST_DIR/analysis_results 가 없다. KooChainRun collect 가 만든다" >&2
    exit 2
fi

apptainer exec --bind /data:/data "$SIF" python3 -m koo_sphere_report \
    --test-dir "$TEST_DIR" \
    --format html json terminal \
    -o "$OUT/$NAME.html" \
    --json "$OUT/$NAME.json" \
    --yield-stress "$YIELD"

echo "완료: $OUT/$NAME.html , $OUT/$NAME.json"
