#!/bin/bash
# KooChainRun (koocr) 빌드 스크립트 - Python 3.10
# 사용법: ./build_koocr_python310.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "KooChainRun (koocr) 빌드 (Python 3.10)"
echo "================================================================================"
echo "venv: ./venv"
echo "Python: $(./venv/bin/python --version)"
echo ""

# 기존 빌드 결과 제거
echo "기존 빌드 결과 제거 중..."
rm -rf koocr.build koocr.dist .nuitka

# Nuitka로 빌드
echo "Nuitka 빌드 시작..."
./venv/bin/python -m nuitka ./koocr \
        --standalone \
        --follow-imports \
        --include-package=Runner \
        --jobs=8 \
        --show-progress

echo ""
echo "================================================================================"
echo "빌드 완료!"
echo "================================================================================"
echo "출력 디렉토리: $SCRIPT_DIR/koocr.dist"
echo "실행 파일: $SCRIPT_DIR/koocr.dist/koocr.bin"
echo ""
echo "빌드 정보:"
ls -lh koocr.dist/koocr.bin
echo ""
echo "실행 테스트:"
cd koocr.dist
./koocr.bin --version 2>&1 || true
cd ..
echo ""
echo "배포 방법:"
echo "  sudo cp -r koocr.dist /opt/koocr"
echo "  sudo ln -sf /opt/koocr/koocr.bin /usr/local/bin/koocr"
