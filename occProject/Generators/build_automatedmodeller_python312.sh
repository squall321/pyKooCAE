#!/bin/bash
# KooAutomatedModeller 빌드 스크립트 - Python 3.12
# 사용법: ./build_automatedmodeller_python312.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "KooAutomatedModeller 빌드 (Python 3.12)"
echo "================================================================================"
echo "venv: ../../venv312"
echo "Python: $(../../venv312/bin/python --version)"
echo ""

# 기존 빌드 결과 제거
echo "기존 빌드 결과 제거 중..."
rm -rf KooAutomatedModeller.build KooAutomatedModeller.dist .nuitka

# Nuitka로 빌드
echo "Nuitka 빌드 시작..."
../../venv312/bin/python -m nuitka ./KooAutomatedModeller.py \
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
# AIRMESH: gmsh Python API는 ctypes(CDLL)로 libgmsh를 로드하므로 Nuitka가 번들하지 않음
# → dist 루트에 수동 복사 필수 (누락 시 배포 머신에서 첫 호출에 missing-symbol 크래시)
echo "AIRMESH: libgmsh.so.4.15 복사 중..."
cp ../../venv312/lib/libgmsh.so.4.15 KooAutomatedModeller.dist/

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

# AIRMESH dist 스모크 테스트: 골든 예제를 임시 디렉토리에서 실행해 Complete 라인 확인
echo ""
echo "AIRMESH dist 스모크 테스트..."
SMOKE_DIR=$(mktemp -d /tmp/airmesh_smoke_XXXXXX)
cp "$SCRIPT_DIR/../../Examples/automatedmodeller/airmesh_sphere/airmesh.json" \
   "$SCRIPT_DIR/../../Examples/automatedmodeller/airmesh_sphere/sphere_cyl.stp" "$SMOKE_DIR/"
SMOKE_OUT=$(./KooAutomatedModeller.bin AIRMESH airmesh.json "$SMOKE_DIR" 2>&1 || true)
cd "$SCRIPT_DIR"
rm -rf "$SMOKE_DIR"
if echo "$SMOKE_OUT" | grep -q "Complete AIRMESH"; then
    echo "✅ AIRMESH 스모크 통과"
else
    echo "❌ AIRMESH 스모크 실패 — libgmsh 번들/로드 확인 필요"
    echo "$SMOKE_OUT" | tail -5
    exit 1
fi
