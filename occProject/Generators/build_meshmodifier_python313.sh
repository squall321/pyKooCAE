#!/bin/bash
# KooMeshModifier 빌드 스크립트 - Python 3.13
# 사용법: ./build_meshmodifier_python313.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "KooMeshModifier 빌드 (Python 3.13)"
echo "================================================================================"
echo "venv: ../../venv313"
echo "Python: $(../../venv313/bin/python --version)"
echo ""

# 기존 빌드 결과 제거
echo "기존 빌드 결과 제거 중..."
rm -rf KooMeshModifier.build KooMeshModifier.dist .nuitka

# Nuitka로 빌드
echo "Nuitka 빌드 시작..."
../../venv313/bin/python -m nuitka ./KooMeshModifier.py \
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
echo "출력 디렉토리: $SCRIPT_DIR/KooMeshModifier.dist"
echo "실행 파일: $SCRIPT_DIR/KooMeshModifier.dist/KooMeshModifier.bin"
echo ""
echo "빌드 정보:"
ls -lh KooMeshModifier.dist/KooMeshModifier.bin
echo ""
echo "실행 테스트:"
cd KooMeshModifier.dist
./KooMeshModifier.bin --help 2>&1 | head -10 || true
