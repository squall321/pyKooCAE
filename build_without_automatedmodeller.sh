#!/bin/bash
# pyKooCAE 빌드 스크립트 (KooAutomatedModeller 제외) - Python 3.12
# KooMeshModifier + KooChainRun만 빌드 (~20분)
# 사용법: ./build_without_automatedmodeller.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BUILD_DIR="$SCRIPT_DIR/build_dist"
BIN_DIR="$BUILD_DIR/bin"
LIB_DIR="$BUILD_DIR/lib"

echo "================================================================================"
echo "pyKooCAE 빌드 (KooAutomatedModeller 제외, Python 3.12)"
echo "================================================================================"
echo "Python: $(./venv312/bin/python --version)"
echo "출력 디렉토리: $BUILD_DIR"
echo ""

# 기존 빌드 결과 제거 (Library, KooAutomatedModeller 보존)
echo "기존 빌드 결과 제거 중 (KooAutomatedModeller 보존)..."
LIBRARY_BACKUP="/tmp/pyKooCAE_Library_backup_$$"
AUTOMOD_BACKUP="/tmp/pyKooCAE_AutoMod_backup_$$"
if [ -d "$BUILD_DIR/Library" ]; then
    echo "  build_dist/Library 백업 중..."
    cp -r "$BUILD_DIR/Library" "$LIBRARY_BACKUP"
fi
if [ -d "$LIB_DIR/KooAutomatedModeller" ]; then
    echo "  build_dist/lib/KooAutomatedModeller 백업 중..."
    cp -r "$LIB_DIR/KooAutomatedModeller" "$AUTOMOD_BACKUP"
fi
rm -rf "$BUILD_DIR"
rm -rf KooChainRun.build KooChainRun.dist .nuitka
rm -rf occProject/Generators/KooMeshModifier.build occProject/Generators/KooMeshModifier.dist occProject/Generators/.nuitka

mkdir -p "$BIN_DIR"
mkdir -p "$LIB_DIR"

echo ""
echo "================================================================================"
echo "1/3: KooMeshModifier 빌드"
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

cd "$SCRIPT_DIR"

echo ""
echo "================================================================================"
echo "2/3: KooChainRun 빌드"
echo "================================================================================"
echo ""

./venv312/bin/python -m nuitka ./KooChainRun \
        --standalone \
        --include-package=Runner \
        --include-module=Runner.PathResolver \
        --include-module=Runner.CaseTxtParser \
        --include-module=Runner.AngleSourceParser \
        --include-module=Runner.ToleranceDOEGenerator \
        --include-module=Runner.AngleMixingStrategy \
        --include-module=Runner.TemplateManager \
        --include-module=Runner.AliasManager \
        --include-module=Runner.CumulativeDesigner \
        --include-module=Runner.CumulativeScenarioRunner \
        --include-module=Runner.LargeScaleDOEManager \
        --include-module=Runner.SimplifiedExecutor \
        --include-module=Runner.SlurmSubmitter \
        --include-module=Runner.DOEParallelOptimizer \
        --include-module=Runner.NodeOccupancyMonitor \
        --include-module=Runner.DirectInputWorkflow \
        --include-module=Runner.ImpactPositionSource \
        --include-module=Runner.StepConfigBuilder \
        --include-module=Runner.PartValidationWorkflow \
        --include-module=Runner.DropWeightImpactWorkflow \
        --jobs=8 \
        --show-progress

echo ""
echo "✅ KooChainRun 빌드 완료"
echo "   이동 중: KooChainRun.dist → $LIB_DIR/KooChainRun"

mv KooChainRun.dist "$LIB_DIR/KooChainRun"
ln -sf "../lib/KooChainRun/KooChainRun.bin" "$BIN_DIR/KooChainRun"

# KooAutomatedModeller 백업 복원
if [ -d "$AUTOMOD_BACKUP" ]; then
    echo ""
    echo "KooAutomatedModeller 이전 빌드 복원 중..."
    cp -r "$AUTOMOD_BACKUP" "$LIB_DIR/KooAutomatedModeller"
    ln -sf "../lib/KooAutomatedModeller/KooAutomatedModeller.bin" "$BIN_DIR/KooAutomatedModeller"
    rm -rf "$AUTOMOD_BACKUP"
fi

echo ""
echo "================================================================================"
echo "3/3: 외부 런타임 의존성 복사 (Library)"
echo "================================================================================"
echo ""

LIBRARY_SRC=""
if [ -d "$SCRIPT_DIR/Library" ]; then
    LIBRARY_SRC="$SCRIPT_DIR/Library"
    echo "Library 소스: 프로젝트 루트 ($LIBRARY_SRC)"
elif [ -d "$LIBRARY_BACKUP" ]; then
    LIBRARY_SRC="$LIBRARY_BACKUP"
    echo "Library 소스: 이전 빌드 백업 ($LIBRARY_SRC)"
else
    echo "  ⚠️  Library 소스 없음 — 프로젝트 루트에 Library/ 폴더를 배치하세요"
fi

mkdir -p "$BUILD_DIR/Library"

if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/gmsh-4.14.1-Linux64" ]; then
    echo "gmsh 복사 중..."
    cp -r "$LIBRARY_SRC/gmsh-4.14.1-Linux64" "$BUILD_DIR/Library/gmsh-4.14.1-Linux64"
    echo "  ✅ Library/gmsh-4.14.1-Linux64/bin/gmsh"
fi

if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/Evolver" ]; then
    echo "Evolver 복사 중..."
    cp -r "$LIBRARY_SRC/Evolver" "$BUILD_DIR/Library/Evolver"
    echo "  ✅ Library/Evolver/ (바이너리 + 스크립트)"
fi

if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/OCC" ]; then
    echo "OCC 네이티브 라이브러리 복사 중..."
    cp -r "$LIBRARY_SRC/OCC" "$BUILD_DIR/Library/OCC"
    echo "  ✅ Library/OCC/ (.so 라이브러리)"
fi

if [ -d "$LIBRARY_BACKUP" ]; then
    rm -rf "$LIBRARY_BACKUP"
fi

echo ""
echo "================================================================================"
echo "빌드 완료! (KooAutomatedModeller 제외)"
echo "================================================================================"
echo ""
echo "출력 디렉토리: $BUILD_DIR"
echo ""
echo "실행 파일:"
ls -lh "$BIN_DIR/"
echo ""
echo "빌드 크기:"
du -sh "$BUILD_DIR"
du -sh "$LIB_DIR/KooMeshModifier"
du -sh "$LIB_DIR/KooChainRun"
echo ""

# SmartTwinPreprocessor 설치
STP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/SmartTwinPreprocessor"

if [ -d "$STP_DIR" ]; then
    echo "================================================================================"
    echo "SmartTwinPreprocessor에 설치"
    echo "================================================================================"
    echo ""

    if [ -d "$STP_DIR/lib/koocr" ] || [ -L "$STP_DIR/bin/koocr" ]; then
        sudo rm -rf "$STP_DIR/lib/koocr"
        sudo rm -f "$STP_DIR/bin/koocr"
    fi

    echo "KooChainRun 설치 중..."
    sudo rm -rf "$STP_DIR/lib/KooChainRun"
    sudo cp -r "$LIB_DIR/KooChainRun" "$STP_DIR/lib/KooChainRun"
    sudo ln -sf "../lib/KooChainRun/KooChainRun.bin" "$STP_DIR/bin/KooChainRun"

    echo "KooMeshModifier 설치 중..."
    sudo rm -rf "$STP_DIR/lib/KooMeshModifier"
    sudo cp -r "$LIB_DIR/KooMeshModifier" "$STP_DIR/lib/KooMeshModifier"
    sudo ln -sf "../lib/KooMeshModifier/KooMeshModifier.bin" "$STP_DIR/bin/KooMeshModifier"

    if [ -d "$BUILD_DIR/Library" ]; then
        echo "Library 설치 중..."
        sudo mkdir -p "$STP_DIR/Library"
        sudo cp -r "$BUILD_DIR/Library/"* "$STP_DIR/Library/"
    fi

    echo ""
    echo "✅ SmartTwinPreprocessor 설치 완료"
    echo "   $STP_DIR/bin/KooChainRun --version:"
    "$STP_DIR/bin/KooChainRun" --version 2>&1 || true
fi

DATA_STP_DIR="/data/SmartTwinPreprocessor"
if [ -d "$DATA_STP_DIR" ]; then
    echo ""
    echo "================================================================================"
    echo "/data/SmartTwinPreprocessor에 추가 배포"
    echo "================================================================================"
    echo ""

    echo "KooChainRun 배포 중..."
    sudo rm -rf "$DATA_STP_DIR/lib/KooChainRun"
    sudo cp -r "$LIB_DIR/KooChainRun" "$DATA_STP_DIR/lib/KooChainRun"
    sudo ln -sf "../lib/KooChainRun/KooChainRun.bin" "$DATA_STP_DIR/bin/KooChainRun"

    echo "KooMeshModifier 배포 중..."
    sudo rm -rf "$DATA_STP_DIR/lib/KooMeshModifier"
    sudo cp -r "$LIB_DIR/KooMeshModifier" "$DATA_STP_DIR/lib/KooMeshModifier"
    sudo ln -sf "../lib/KooMeshModifier/KooMeshModifier.bin" "$DATA_STP_DIR/bin/KooMeshModifier"

    echo ""
    echo "✅ /data/SmartTwinPreprocessor 배포 완료"
    echo "   $DATA_STP_DIR/bin/KooChainRun --version:"
    "$DATA_STP_DIR/bin/KooChainRun" --version 2>&1 || true
fi

echo ""
echo "================================================================================"
echo "전체 완료! (KooAutomatedModeller 제외)"
echo "================================================================================"
