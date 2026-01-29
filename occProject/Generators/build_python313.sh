#!/bin/bash
# KooAutomatedModeller 빌드 스크립트 - Python 3.13
# 사용법: ./build_python313.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "KooAutomatedModeller 빌드 (Python 3.13)"
echo "================================================================================"
echo "venv: ../../venv313"
echo "Python: $(../../venv313/bin/python --version)"
echo ""

# 기존 빌드 결과 제거
echo "기존 빌드 결과 제거 중..."
rm -rf KooAutomatedModeller.build KooAutomatedModeller.dist .nuitka

# Nuitka로 빌드
echo "Nuitka 빌드 시작..."
../../venv313/bin/python -m nuitka ./KooAutomatedModeller.py \
        --standalone \
        --enable-plugin=pyqt5 \
        --jobs=8 \
        --include-package=OCC \
        --include-package=vtk \
        --include-package=vtkmodules \
        --include-package=trimesh \
        --include-package-data=trimesh \
        --follow-imports \
        --show-progress

echo ""
echo "================================================================================"
echo "빌드 완료!"
echo "================================================================================"
echo "출력 디렉토리: $SCRIPT_DIR/KooAutomatedModeller.dist"
echo "실행 파일: $SCRIPT_DIR/KooAutomatedModeller.dist/KooAutomatedModeller.bin"
echo ""
echo "빌드 정보:"
ls -lh KooAutomatedModeller.dist/KooAutomatedModeller.bin
echo ""
echo "실행 테스트:"
cd KooAutomatedModeller.dist
./KooAutomatedModeller.bin --help 2>&1 | head -10 || true
