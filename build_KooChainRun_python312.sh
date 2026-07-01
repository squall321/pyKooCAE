#!/bin/bash
# KooChainRun (KCR) 빌드 스크립트 - Python 3.12
# 사용법:
#   ./build_KooChainRun_python312.sh           # incremental (캐시 보존)
#   ./build_KooChainRun_python312.sh --clean   # clean 빌드
#   GLIBC_GUARD=0 ./build_KooChainRun_python312.sh  # 가드 우회(권장 안 함)
#
# 🔴 glibc 2.35 강제: Nuitka --standalone 은 '빌드 머신의 glibc' 를 그대로 박는다.
#    계산노드(Ubuntu22.04=glibc2.35)에서 돌리려면 반드시 glibc<=2.35 환경에서 빌드해야 한다.
#    (헤드노드는 2026-06-18 pgvector/jdk 설치 때 glibc 가 2.39 로 딸려 올라가 오염됨 → 직접 빌드 금지.)
#    glibc 2.35 로 빌드한 .bin 은 운영서버(Ubuntu24.04=2.39)에서도 동작(전방호환, 실증됨).
#    이 스크립트는 호스트 glibc 가 2.35 초과면 KooSimulationPython313 샌드박스(2.35) 안에서
#    자기 자신을 재실행한다.

set -e

CLEAN_BUILD=false
if [ "$1" == "--clean" ]; then
    CLEAN_BUILD=true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── glibc 2.35 강제 가드 (공통 스니펫) ───────────────────────────────────────
GUARD_SELF="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
GUARD_ARGS=("$@")
source "$SCRIPT_DIR/build_glibc_guard.sh"
# ─────────────────────────────────────────────────────────────────────────────

echo "================================================================================"
echo "KooChainRun 빌드 (Python 3.12)"
echo "================================================================================"
echo "venv: ./venv312"
echo "Python: $(./venv312/bin/python --version)"
if [ "$CLEAN_BUILD" = true ]; then
    echo "모드: CLEAN (캐시 모두 삭제)"
else
    echo "모드: INCREMENTAL (캐시 보존)"
fi
echo ""

# Nuitka cache + .build/.dist는 옵션
if [ "$CLEAN_BUILD" = true ]; then
    echo "Nuitka cache + build/dist 삭제 중..."
    rm -rf KooChainRun.build KooChainRun.dist .nuitka
else
    echo "Nuitka cache 보존 (변경 모듈만 재빌드)"
fi

# Nuitka로 빌드
echo "Nuitka 빌드 시작..."
./venv312/bin/python -m nuitka ./KooChainRun \
        --standalone \
        --follow-imports \
        --include-package=Runner \
        --jobs=8 \
        --show-progress

BUILD_DIR="$SCRIPT_DIR/build_dist"
BIN_DIR="$BUILD_DIR/bin"
LIB_DIR="$BUILD_DIR/lib"

rm -rf "$BUILD_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$LIB_DIR"

mv KooChainRun.dist "$LIB_DIR/KooChainRun"
ln -sf "../lib/KooChainRun/KooChainRun.bin" "$BIN_DIR/KooChainRun"

echo ""
echo "================================================================================"
echo "빌드 완료!"
echo "================================================================================"
echo ""
echo "빌드 정보:"
ls -lh "$LIB_DIR/KooChainRun/KooChainRun.bin"

# ── 산출물 glibc 검증: .bin 이 요구하는 최고 GLIBC 가 2.35 이하인지 확인 ──
echo ""
echo "산출물 glibc 검증 (계산노드 baseline ${GLIBC_MAX:-2.35}):"
REQ_GLIBC="$(objdump -T "$LIB_DIR/KooChainRun/KooChainRun.bin" 2>/dev/null \
    | grep -oE 'GLIBC_[0-9]+\.[0-9]+' | sed 's/GLIBC_//' | sort -V | tail -1)"
echo "  요구 최고 GLIBC: ${REQ_GLIBC:-(확인불가)}"
if [ -n "$REQ_GLIBC" ]; then
    if [ "$(printf '%s\n%s\n' "$REQ_GLIBC" "${GLIBC_MAX:-2.35}" | sort -V | tail -1)" = "${GLIBC_MAX:-2.35}" ]; then
        echo "  ✅ ${REQ_GLIBC} <= ${GLIBC_MAX:-2.35}: 계산노드(2.35)·운영서버(2.39) 양쪽 호환."
    else
        echo "  ❌ ${REQ_GLIBC} > ${GLIBC_MAX:-2.35}: 계산노드에서 실행 불가! 2.35 환경에서 재빌드 필요."
        echo "     (헤드노드 glibc 오염 상태로 빌드됐을 가능성 — GLIBC_GUARD 확인.)"
        exit 1
    fi
fi
echo ""
echo "실행 테스트:"
"$BIN_DIR/KooChainRun" --version 2>&1 || true
echo ""
echo "디렉토리 구조:"
echo "  $BUILD_DIR/"
echo "  ├── bin/KooChainRun → ../lib/KooChainRun/KooChainRun.bin"
echo "  └── lib/KooChainRun/"
echo ""

echo "================================================================================"
echo "SmartTwinPreprocessor에 설치"
echo "================================================================================"
echo ""

STP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/SmartTwinPreprocessor"

if [ -d "$STP_DIR" ]; then
    echo "설치 대상: $STP_DIR"
    echo ""

    # 기존 koocr 제거 (이름 변경 대응)
    if [ -d "$STP_DIR/lib/koocr" ] || [ -L "$STP_DIR/bin/koocr" ]; then
        echo "기존 koocr 제거 중..."
        sudo rm -rf "$STP_DIR/lib/koocr"
        sudo rm -f "$STP_DIR/bin/koocr"
    fi

    echo "KooChainRun 설치 중..."
    sudo rm -rf "$STP_DIR/lib/KooChainRun"
    sudo cp -r "$LIB_DIR/KooChainRun" "$STP_DIR/lib/KooChainRun"
    sudo ln -sf "../lib/KooChainRun/KooChainRun.bin" "$STP_DIR/bin/KooChainRun"

    echo ""
    echo "✅ SmartTwinPreprocessor 설치 완료"
    echo "   $STP_DIR/bin/KooChainRun --version:"
    "$STP_DIR/bin/KooChainRun" --version 2>&1 || true
else
    echo "⚠️  SmartTwinPreprocessor 디렉토리 없음: $STP_DIR"
    echo "   수동 배포:"
    echo "   sudo cp -r $LIB_DIR/KooChainRun /opt/KooChainRun"
    echo "   sudo ln -sf /opt/KooChainRun/KooChainRun.bin /usr/local/bin/KooChainRun"
fi

# /data/SmartTwinPreprocessor에도 설치 (테스트 환경용)
DATA_STP_DIR="/data/SmartTwinPreprocessor"
if [ -d "$DATA_STP_DIR" ]; then
    echo ""
    echo "================================================================================"
    echo "/data/SmartTwinPreprocessor에 설치"
    echo "================================================================================"
    echo ""
    sudo rm -rf "$DATA_STP_DIR/lib/KooChainRun"
    sudo cp -r "$LIB_DIR/KooChainRun" "$DATA_STP_DIR/lib/KooChainRun"
    sudo ln -sf "../lib/KooChainRun/KooChainRun.bin" "$DATA_STP_DIR/bin/KooChainRun"
    echo "✅ /data/SmartTwinPreprocessor 설치 완료"
    "$DATA_STP_DIR/bin/KooChainRun" --version 2>&1 || true
fi
