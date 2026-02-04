#!/bin/bash
# KooChainRun (KCR) 빌드 스크립트 - Python 3.13
# 사용법: ./build_KooChainRun_python313.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "KooChainRun 빌드 (Python 3.13)"
echo "================================================================================"
echo "venv: ./venv313"
echo "Python: $(./venv313/bin/python --version)"
echo ""

# 기존 빌드 결과 제거
echo "기존 빌드 결과 제거 중..."
rm -rf KooChainRun.build KooChainRun.dist .nuitka

# Nuitka로 빌드
echo "Nuitka 빌드 시작..."
./venv313/bin/python -m nuitka ./KooChainRun \
        --standalone \
        --onefile \
        --follow-imports \
        --include-package=Runner \
        --include-package=occProject \
        --jobs=8 \
        --show-progress \
        --output-filename=KooChainRun.bin

echo ""
echo "================================================================================"
echo "빌드 완료!"
echo "================================================================================"
echo "실행 파일: $SCRIPT_DIR/KooChainRun.bin"
echo ""
echo "빌드 정보:"
ls -lh KooChainRun.bin
echo ""
echo "실행 테스트:"
./KooChainRun.bin --version 2>&1 || true
echo ""
echo "배포 방법:"
echo "  sudo cp KooChainRun.bin /usr/local/bin/KooChainRun"
echo "  sudo chmod +x /usr/local/bin/KooChainRun"
