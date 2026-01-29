#!/bin/bash
# pyKooCAE 전체 통합 빌드 스크립트 - Python 3.13
# 사용법: ./build_all_python313.sh
# ⚠️ 주의: Python 3.13은 PythonOCC가 설치되지 않았습니다.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BUILD_DIR="$SCRIPT_DIR/build_dist"
BIN_DIR="$BUILD_DIR/bin"
LIB_DIR="$BUILD_DIR/lib"

echo "================================================================================"
echo "pyKooCAE 통합 빌드 (Python 3.13)"
echo "================================================================================"
echo "⚠️  주의: Python 3.13에는 PythonOCC가 설치되지 않았습니다."
echo "⚠️  KooMeshModifier와 KooAutomatedModeller 빌드가 실패할 수 있습니다."
echo ""
echo "Python: $(./venv313/bin/python --version)"
echo "출력 디렉토리: $BUILD_DIR"
echo ""

# 기존 빌드 결과 제거
echo "기존 빌드 결과 제거 중..."
rm -rf "$BUILD_DIR"
rm -rf koocr.build koocr.dist .nuitka
rm -rf occProject/Generators/KooMeshModifier.build occProject/Generators/KooMeshModifier.dist occProject/Generators/.nuitka
rm -rf occProject/Generators/KooAutomatedModeller.build occProject/Generators/KooAutomatedModeller.dist

mkdir -p "$BIN_DIR"
mkdir -p "$LIB_DIR"

echo ""
echo "================================================================================"
echo "1/3: KooMeshModifier 빌드"
echo "================================================================================"
echo ""

cd occProject/Generators

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
echo "✅ KooMeshModifier 빌드 완료"
echo "   이동 중: KooMeshModifier.dist → $LIB_DIR/KooMeshModifier"

mv KooMeshModifier.dist "$LIB_DIR/KooMeshModifier"
ln -sf "../lib/KooMeshModifier/KooMeshModifier.bin" "$BIN_DIR/KooMeshModifier"

echo ""
echo "================================================================================"
echo "2/3: KooAutomatedModeller 빌드"
echo "================================================================================"
echo ""

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
echo "✅ KooAutomatedModeller 빌드 완료"
echo "   이동 중: KooAutomatedModeller.dist → $LIB_DIR/KooAutomatedModeller"

mv KooAutomatedModeller.dist "$LIB_DIR/KooAutomatedModeller"
ln -sf "../lib/KooAutomatedModeller/KooAutomatedModeller.bin" "$BIN_DIR/KooAutomatedModeller"

cd "$SCRIPT_DIR"

echo ""
echo "================================================================================"
echo "3/3: koocr (KooChainRun) 빌드"
echo "================================================================================"
echo ""

./venv313/bin/python -m nuitka ./koocr \
        --standalone \
        --follow-imports \
        --include-package=Runner \
        --jobs=8 \
        --show-progress

echo ""
echo "✅ koocr 빌드 완료"
echo "   이동 중: koocr.dist → $LIB_DIR/koocr"

mv koocr.dist "$LIB_DIR/koocr"
ln -sf "../lib/koocr/koocr.bin" "$BIN_DIR/koocr"

echo ""
echo "================================================================================"
echo "통합 빌드 완료!"
echo "================================================================================"
echo ""
echo "출력 디렉토리: $BUILD_DIR"
echo ""
echo "디렉토리 구조:"
tree -L 2 "$BUILD_DIR" 2>/dev/null || find "$BUILD_DIR" -maxdepth 2 -type d
echo ""
echo "실행 파일:"
ls -lh "$BIN_DIR/"
echo ""
echo "빌드 크기:"
du -sh "$BUILD_DIR"
du -sh "$LIB_DIR/KooMeshModifier"
du -sh "$LIB_DIR/KooAutomatedModeller"
du -sh "$LIB_DIR/koocr"
echo ""
echo "테스트:"
echo "  $BIN_DIR/KooMeshModifier --help"
echo "  $BIN_DIR/KooAutomatedModeller --help"
echo "  $BIN_DIR/koocr --version"
echo ""
echo "배포 방법:"
echo "  sudo cp -r $BUILD_DIR /opt/pyKooCAE"
echo "  sudo ln -sf /opt/pyKooCAE/bin/koocr /usr/local/bin/koocr"
echo "  sudo ln -sf /opt/pyKooCAE/bin/KooMeshModifier /usr/local/bin/KooMeshModifier"
echo "  sudo ln -sf /opt/pyKooCAE/bin/KooAutomatedModeller /usr/local/bin/KooAutomatedModeller"
echo ""
echo "환경 설정:"
echo "  export PATH=/opt/pyKooCAE/bin:\$PATH"
