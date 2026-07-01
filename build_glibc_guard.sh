# glibc 2.35 강제 가드 (공통) — 각 빌드 스크립트가 SCRIPT_DIR/ARGS 설정 후 source.
#
# 🔴 Nuitka --standalone 은 '빌드 머신 glibc' 를 그대로 박는다. 계산노드(Ubuntu22.04
#    =glibc2.35)에서 돌리려면 반드시 glibc<=2.35 환경에서 빌드해야 한다. 헤드노드는
#    2026-06-18 pgvector/jdk 설치 때 glibc 가 2.39 로 딸려 올라가 오염됨 → 직접 빌드 금지.
#    2.35 로 빌드한 .bin 은 운영서버(Ubuntu24.04=2.39)에서도 동작(전방호환, 실증됨).
#
# 사용법 (호출 스크립트에서):
#   GUARD_ARGS=("$@")
#   source "$SCRIPT_DIR/build_glibc_guard.sh"
# glibc>2.35 면 KooSimulationPython313 샌드박스(2.35) 안에서 '호출 스크립트 자신' 을 재실행.
# GLIBC_GUARD=0 으로 우회(비권장). 산출물 검증은 assert_glibc_max <bin> 로.

GLIBC_GUARD="${GLIBC_GUARD:-1}"
GLIBC_MAX="${GLIBC_MAX:-2.35}"
BUILD_SANDBOX="${BUILD_SANDBOX:-/home/koopark/serviceApptainers/KooSimulationPython313}"
BUILD_SIF="${BUILD_SIF:-/opt/apptainers/SmartTwinPreprocessor.sif}"

_ver_le() { [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -1)" = "$1" ]; }

# 산출물 .bin 이 요구하는 최고 GLIBC 가 GLIBC_MAX 이하인지 검증 (초과면 exit 1)
assert_glibc_max() {
    local bin="$1"
    [ -f "$bin" ] || { echo "assert_glibc_max: 파일 없음 $bin"; return 0; }
    local req
    req="$(objdump -T "$bin" 2>/dev/null | grep -oE 'GLIBC_[0-9]+\.[0-9]+' | sed 's/GLIBC_//' | sort -V | tail -1)"
    echo "  산출물 요구 최고 GLIBC: ${req:-(확인불가)} (baseline ${GLIBC_MAX})"
    if [ -n "$req" ] && [ "$(printf '%s\n%s\n' "$req" "$GLIBC_MAX" | sort -V | tail -1)" != "$GLIBC_MAX" ]; then
        echo "  ❌ ${req} > ${GLIBC_MAX}: 계산노드 실행 불가! 2.35 환경 재빌드 필요."
        exit 1
    fi
    [ -n "$req" ] && echo "  ✅ ${req} <= ${GLIBC_MAX}: 계산노드(2.35)·운영서버(2.39) 호환."
}

if [ "$GLIBC_GUARD" = "1" ] && [ -z "${KCR_IN_BUILD_SANDBOX:-}" ]; then
    HOST_GLIBC="$(ldd --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+$')"
    echo "빌드 환경 glibc: ${HOST_GLIBC} (허용 최대: ${GLIBC_MAX})"
    if [ -n "$HOST_GLIBC" ] && _ver_le "$HOST_GLIBC" "$GLIBC_MAX"; then
        echo "✅ glibc ${HOST_GLIBC} <= ${GLIBC_MAX}: 이 환경에서 직접 빌드 진행."
    else
        echo "⚠️  glibc ${HOST_GLIBC} > ${GLIBC_MAX}: 계산노드(2.35)에서 실행 불가 → 2.35 컨테이너 재실행."
        _CONTAINER=""
        if command -v apptainer >/dev/null 2>&1 && [ -d "$BUILD_SANDBOX" ]; then
            _CONTAINER="$BUILD_SANDBOX"
        elif command -v apptainer >/dev/null 2>&1 && [ -f "$BUILD_SIF" ]; then
            _CONTAINER="$BUILD_SIF"
        fi
        if [ -n "$_CONTAINER" ]; then
            echo "→ 2.35 컨테이너에서 재실행: $_CONTAINER"
            exec env KCR_IN_BUILD_SANDBOX=1 apptainer exec -B /home -B /data "$_CONTAINER" \
                bash "$GUARD_SELF" "${GUARD_ARGS[@]}"
        fi
        echo "❌ 2.35 빌드 컨테이너를 못 찾음($BUILD_SANDBOX / $BUILD_SIF)."
        echo "   glibc<=2.35 환경에서 빌드하거나, GLIBC_GUARD=0 으로 강제 진행(계산노드 비호환 위험)."
        exit 1
    fi
fi
