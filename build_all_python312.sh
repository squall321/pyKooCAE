#!/bin/bash
# pyKooCAE 전체 통합 빌드 스크립트 - Python 3.12
# 사용법: ./build_all_python312.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BUILD_DIR="$SCRIPT_DIR/build_dist"
BIN_DIR="$BUILD_DIR/bin"
LIB_DIR="$BUILD_DIR/lib"

echo "================================================================================"
echo "pyKooCAE 통합 빌드 (Python 3.12)"
echo "================================================================================"
echo "Python: $(./venv312/bin/python --version)"
echo "출력 디렉토리: $BUILD_DIR"
echo ""

# 기존 빌드 결과 제거
echo "기존 빌드 결과 제거 중..."
rm -rf "$BUILD_DIR"
rm -rf KooChainRun.build KooChainRun.dist .nuitka
rm -rf occProject/Generators/KooMeshModifier.build occProject/Generators/KooMeshModifier.dist occProject/Generators/.nuitka
rm -rf occProject/Generators/KooAutomatedModeller.build occProject/Generators/KooAutomatedModeller.dist

mkdir -p "$BIN_DIR"
mkdir -p "$LIB_DIR"

echo ""
echo "================================================================================"
echo "1/4: KooMeshModifier 빌드"
echo "================================================================================"
echo ""

cd occProject/Generators

../../venv312/bin/python -m nuitka ./KooMeshModifier.py \
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
echo "2/4: KooAutomatedModeller 빌드"
echo "================================================================================"
echo ""

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
echo "✅ KooAutomatedModeller 빌드 완료"
echo "   이동 중: KooAutomatedModeller.dist → $LIB_DIR/KooAutomatedModeller"

mv KooAutomatedModeller.dist "$LIB_DIR/KooAutomatedModeller"
ln -sf "../lib/KooAutomatedModeller/KooAutomatedModeller.bin" "$BIN_DIR/KooAutomatedModeller"

cd "$SCRIPT_DIR"

echo ""
echo "================================================================================"
echo "3/4: KooChainRun 빌드"
echo "================================================================================"
echo ""

./venv312/bin/python -m nuitka ./KooChainRun \
        --standalone \
        --follow-imports \
        --include-package=Runner \
        --jobs=8 \
        --show-progress

echo ""
echo "✅ KooChainRun 빌드 완료"
echo "   이동 중: KooChainRun.dist → $LIB_DIR/KooChainRun"

mv KooChainRun.dist "$LIB_DIR/KooChainRun"
ln -sf "../lib/KooChainRun/KooChainRun.bin" "$BIN_DIR/KooChainRun"

echo ""
echo "================================================================================"
echo "4/4: 외부 런타임 의존성 복사 (Library)"
echo "================================================================================"
echo ""

# gmsh: KooMeshModifier, KooAutomatedModeller에서 subprocess로 호출
#   탐색 경로: /opt/gmsh-4.14.1-Linux64/bin/gmsh
#            → {basePath}/../../Library/gmsh-4.14.1-Linux64/bin/gmsh  (상위 탐색)
#            → ./Library/gmsh-4.14.1-Linux64/bin/gmsh  (cwd 기준)
if [ -d "$SCRIPT_DIR/Library/gmsh-4.14.1-Linux64" ]; then
    echo "gmsh 복사 중..."
    cp -r "$SCRIPT_DIR/Library/gmsh-4.14.1-Linux64" "$BUILD_DIR/Library/gmsh-4.14.1-Linux64"
    echo "  ✅ Library/gmsh-4.14.1-Linux64/bin/gmsh"
else
    echo "  ⚠️  Library/gmsh-4.14.1-Linux64 없음 — 배포 환경에서 /opt/gmsh-4.14.1-Linux64 또는 PATH 필요"
fi

# Evolver: WarpageSolderJoint에서 subprocess로 호출 (바이너리 + 스크립트 파일 모두 필요)
#   탐색 경로: /opt/Evolver/evolver
#            → {basePath}/../../Library/Evolver/evolver  (상위 탐색)
#            → ./Library/Evolver/evolver  (cwd 기준)
#   스크립트:  {folderPath}/Library/Evolver/{fileName}
if [ -d "$SCRIPT_DIR/Library/Evolver" ]; then
    echo "Evolver 복사 중..."
    cp -r "$SCRIPT_DIR/Library/Evolver" "$BUILD_DIR/Library/Evolver"
    echo "  ✅ Library/Evolver/ (바이너리 + 스크립트)"
else
    echo "  ⚠️  Library/Evolver 없음 — 배포 환경에서 /opt/Evolver 또는 PATH 필요"
fi

# OCC 네이티브 라이브러리 (.so): LD_LIBRARY_PATH로 로드
#   탐색 경로: {cwd}/Library/OCC/
#   Nuitka --include-package=OCC는 Python 바인딩만 포함, .so는 별도 필요
if [ -d "$SCRIPT_DIR/Library/OCC" ]; then
    echo "OCC 네이티브 라이브러리 복사 중..."
    cp -r "$SCRIPT_DIR/Library/OCC" "$BUILD_DIR/Library/OCC"
    echo "  ✅ Library/OCC/ (.so 라이브러리)"
else
    echo "  ⚠️  Library/OCC 없음 — pythonOCC .so가 Nuitka standalone에 이미 포함되었을 수 있음"
fi

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
du -sh "$LIB_DIR/KooChainRun"
echo ""
echo "테스트:"
echo "  $BIN_DIR/KooMeshModifier --help"
echo "  $BIN_DIR/KooAutomatedModeller --help"
echo "  $BIN_DIR/KooChainRun --version"
echo ""
echo "================================================================================"
echo "5/5: SmartTwinPreprocessor에 설치"
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

    # lib 복사
    echo "KooChainRun 설치 중..."
    sudo rm -rf "$STP_DIR/lib/KooChainRun"
    sudo cp -r "$LIB_DIR/KooChainRun" "$STP_DIR/lib/KooChainRun"
    sudo ln -sf "../lib/KooChainRun/KooChainRun.bin" "$STP_DIR/bin/KooChainRun"

    echo "KooMeshModifier 설치 중..."
    sudo rm -rf "$STP_DIR/lib/KooMeshModifier"
    sudo cp -r "$LIB_DIR/KooMeshModifier" "$STP_DIR/lib/KooMeshModifier"
    sudo ln -sf "../lib/KooMeshModifier/KooMeshModifier.bin" "$STP_DIR/bin/KooMeshModifier"

    echo "KooAutomatedModeller 설치 중..."
    sudo rm -rf "$STP_DIR/lib/KooAutomatedModeller"
    sudo cp -r "$LIB_DIR/KooAutomatedModeller" "$STP_DIR/lib/KooAutomatedModeller"
    sudo ln -sf "../lib/KooAutomatedModeller/KooAutomatedModeller.bin" "$STP_DIR/bin/KooAutomatedModeller"

    # Library (gmsh, Evolver) 복사
    if [ -d "$BUILD_DIR/Library" ]; then
        echo "Library 설치 중..."
        sudo mkdir -p "$STP_DIR/Library"
        sudo cp -r "$BUILD_DIR/Library/"* "$STP_DIR/Library/"
    fi

    echo ""
    echo "✅ SmartTwinPreprocessor 설치 완료"
    echo "   $STP_DIR/bin/KooChainRun --version:"
    "$STP_DIR/bin/KooChainRun" --version 2>&1 || true
else
    echo "⚠️  SmartTwinPreprocessor 디렉토리 없음: $STP_DIR"
    echo "   수동 설치가 필요합니다."
fi

echo ""
echo "================================================================================"
echo "전체 완료!"
echo "================================================================================"
echo ""
echo "빌드 출력: $BUILD_DIR"
echo "설치 위치: $STP_DIR"
echo ""
echo "환경 설정:"
echo "  export PATH=$STP_DIR/bin:\$PATH"
