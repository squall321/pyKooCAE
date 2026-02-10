#!/bin/bash
# KooChainRun (KCR) 빌드 스크립트 - Python 3.12
# 사용법: ./build_KooChainRun_python312.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "KooChainRun 빌드 (Python 3.12)"
echo "================================================================================"
echo "venv: ./venv312"
echo "Python: $(./venv312/bin/python --version)"
echo ""

# 기존 빌드 결과 제거
echo "기존 빌드 결과 제거 중..."
rm -rf KooChainRun.build KooChainRun.dist .nuitka

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
