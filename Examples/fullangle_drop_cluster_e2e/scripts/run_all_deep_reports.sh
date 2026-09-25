#!/bin/bash
# 전각도 낙하 결과의 방향별 deep_report 를 변형(light/full)마다 순차 재생성하는 재개 가능 드라이버
#
# 사용법:
#   TEST_DIR=/data/koopark/Test_Postprocess_v14 bash run_all_deep_reports.sh full
#
# 환경변수
#   TEST_DIR    (필수) Run_* 이 들어 있는 output/ 의 부모
#   SIF         후처리 SIF (기본 /data/SmartTwinPostprocessor/SmartTwinPostprocessor.sif)
#   UA_THREADS  d3plot 분석 스레드 (기본 4). 🔴 올리면 최대 RSS 가 같이 올라간다
#   SV_THREADS  단면뷰 렌더 스레드 (기본 12). 시간을 지배하는 단계라 여기를 올린다
#   VMEM_KB     ulimit -v 상한 (기본 60000000 = 60 GB)
#   MAX_RUNS    이번 패스에서 돌릴 방향 수 (기본 0 = 전부). 프로브용
#
# 🔴 헤드노드에서 돌린다. 분석 단계 최대 RSS 가 34 GB 라 4 GB 배분 계산노드에서는 OOM 된다.
# 🔴 한 번에 하나만 돈다. 동시 2개는 메모리를 넘긴다.
set -u

VARIANT="${1:-}"
TEST_DIR="${TEST_DIR:?TEST_DIR 를 지정할 것 (Run_* 이 들어 있는 output/ 의 부모)}"
SIF="${SIF:-/data/SmartTwinPostprocessor/SmartTwinPostprocessor.sif}"
BASE="$TEST_DIR/output"
UA_THREADS="${UA_THREADS:-4}"
SV_THREADS="${SV_THREADS:-12}"
VMEM_KB="${VMEM_KB:-60000000}"
MAX_RUNS="${MAX_RUNS:-0}"

case "$VARIANT" in
  light)
    OUTNAME=report_norender
    OPTS=(--no-render --ua-threads "$UA_THREADS")
    ;;
  full)
    OUTNAME=report
    OPTS=(--section-view --section-view-backend software --section-view-mode section
          --section-view-axes z --section-view-fields von_mises
          --ua-threads "$UA_THREADS" --sv-threads "$SV_THREADS")
    ;;
  *)
    echo "usage: TEST_DIR=<dir> $0 light|full" >&2
    exit 2
    ;;
esac

LOGDIR="$TEST_DIR/logs_deep_$VARIANT"
PROGRESS="$TEST_DIR/progress_deep_$VARIANT.tsv"
mkdir -p "$LOGDIR"
[ -f "$PROGRESS" ] || printf 'run\trc\telapsed\tmaxRSS_KB\tsize\tua\tsv\n' > "$PROGRESS"

if [ ! -f "$SIF" ]; then
    echo "[driver] ERROR: SIF 없음: $SIF" >&2
    exit 2
fi

echo "[driver] variant=$VARIANT outdir=$OUTNAME ua=$UA_THREADS sv=$SV_THREADS vmem=${VMEM_KB}KB max=$MAX_RUNS 시작 $(date '+%F %T')"

DONE_THIS_PASS=0
for RUN in $(ls -d "$BASE"/Run_*/ | sort); do
    if [ "$MAX_RUNS" -gt 0 ] && [ "$DONE_THIS_PASS" -ge "$MAX_RUNS" ]; then
        echo "[driver] MAX_RUNS=$MAX_RUNS 도달 — 중단"
        break
    fi

    NAME=$(basename "${RUN%/}")
    OUT="${RUN%/}/Output"
    RD="$OUT/$OUTNAME"

    if [ -f "$RD/.koo_driver_done" ]; then
        echo "[driver] skip(완료) $NAME"
        continue
    fi

    # full 변형은 report/ 를 덮어쓴다. 구버전 결과가 있으면 보존한다.
    # contact_metrics.json 은 신버전 산출물에만 있어 신·구 판별자로 쓴다.
    if [ "$VARIANT" = full ] && [ -d "$RD" ] \
       && [ ! -f "$RD/contact_metrics.json" ] && [ ! -d "$OUT/report_prev" ]; then
        mv "$RD" "$OUT/report_prev"
        echo "[driver] 구버전 보존 $NAME -> report_prev/"
    fi

    mkdir -p "$RD"
    echo "[driver] run $NAME  $(date '+%F %T')"
    ( ulimit -v "$VMEM_KB"
      /usr/bin/time -v apptainer exec --bind /data:/data \
          "$SIF" python3 -m koo_deep_report "$OUT" -o "$RD" "${OPTS[@]}"
    ) > "$LOGDIR/$NAME.log" 2>&1
    rc=$?
    DONE_THIS_PASS=$((DONE_THIS_PASS + 1))

    EL=$(grep -oP 'Elapsed \(wall clock\) time.*?: \K.*' "$LOGDIR/$NAME.log" | tail -1)
    RS=$(grep -oP 'Maximum resident set size \(kbytes\): \K[0-9]+' "$LOGDIR/$NAME.log" | tail -1)
    SZ=$(du -sh "$RD" 2>/dev/null | cut -f1)
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$NAME" "$rc" "${EL:-?}" "${RS:-?}" "${SZ:-?}" "$UA_THREADS" "$SV_THREADS" >> "$PROGRESS"

    if [ "$rc" -eq 0 ]; then
        touch "$RD/.koo_driver_done"
        echo "[driver] ok   $NAME  $EL  ${RS}KB  $SZ"
    else
        echo "[driver] FAIL $NAME rc=$rc (로그: $LOGDIR/$NAME.log)"
    fi
done

echo "[driver] variant=$VARIANT 종료 $(date '+%F %T')"
