#!/bin/bash
# pyKooCAE ë¹ë ì¤í¬ë¦½í¸ (KooAutomatedModeller ì ì¸) - Python 3.12
# KooMeshModifier + KooChainRunë§ ë¹ë
# ì¬ì©ë²:
#   ./build_without_automatedmodeller.sh           # incremental (ìºì ë³´ì¡´, ë¹ ë¦)
#   ./build_without_automatedmodeller.sh --clean   # clean ë¹ë (ëª¨ë  ìºì ì­ì , ëë¦¬ì§ë§ ìì )

set -e

CLEAN_BUILD=false
if [ "$1" == "--clean" ]; then
    CLEAN_BUILD=true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── glibc 2.35 ê°ì  ê°ë (ê³µíµ ì¤ëí«) ──
GUARD_SELF="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
GUARD_ARGS=("$@")
source "$SCRIPT_DIR/build_glibc_guard.sh"

BUILD_DIR="$SCRIPT_DIR/build_dist"
BIN_DIR="$BUILD_DIR/bin"
LIB_DIR="$BUILD_DIR/lib"

echo "================================================================================"
echo "pyKooCAE ë¹ë (KooAutomatedModeller ì ì¸, Python 3.12)"
echo "================================================================================"
echo "Python: $(./venv312/bin/python --version)"
echo "ì¶ë ¥ ëë í ë¦¬: $BUILD_DIR"
if [ "$CLEAN_BUILD" = true ]; then
    echo "ëª¨ë: CLEAN (ìºì ëª¨ë ì­ì )"
else
    echo "ëª¨ë: INCREMENTAL (ìºì ë³´ì¡´, ë³ê²½ë ëª¨ëë§ ì¬ë¹ë)"
fi
echo ""

# ê¸°ì¡´ ë¹ë ê²°ê³¼ ì ê±° (Library, KooAutomatedModeller ë³´ì¡´)
LIBRARY_BACKUP="/tmp/pyKooCAE_Library_backup_$$"
AUTOMOD_BACKUP="/tmp/pyKooCAE_AutoMod_backup_$$"
if [ -d "$BUILD_DIR/Library" ]; then
    echo "  build_dist/Library ë°±ì ì¤..."
    cp -r "$BUILD_DIR/Library" "$LIBRARY_BACKUP"
fi
if [ -d "$LIB_DIR/KooAutomatedModeller" ]; then
    echo "  build_dist/lib/KooAutomatedModeller ë°±ì ì¤..."
    cp -r "$LIB_DIR/KooAutomatedModeller" "$AUTOMOD_BACKUP"
fi
# build_distë í­ì ì ë¦¬ (ì¬ë°°ì¹ íì), Nuitka cacheë ìµì
rm -rf "$BUILD_DIR"
if [ "$CLEAN_BUILD" = true ]; then
    echo "  Nuitka cache + build/dist ì­ì  ì¤ (clean ë¹ë)..."
    rm -rf KooChainRun.build KooChainRun.dist .nuitka
    rm -rf occProject/Generators/KooMeshModifier.build occProject/Generators/KooMeshModifier.dist occProject/Generators/.nuitka
else
    echo "  Nuitka cache + .build í´ë ë³´ì¡´ (incremental, ë³ê²½ ëª¨ëë§ ì¬ë¹ë)"
fi

mkdir -p "$BIN_DIR"
mkdir -p "$LIB_DIR"

echo ""
echo "================================================================================"
echo "1/3: KooMeshModifier ë¹ë"
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
echo "â KooMeshModifier ë¹ë ìë£"
echo "   ì´ë ì¤: KooMeshModifier.dist â $LIB_DIR/KooMeshModifier"

mv KooMeshModifier.dist "$LIB_DIR/KooMeshModifier"
ln -sf "../lib/KooMeshModifier/KooMeshModifier.bin" "$BIN_DIR/KooMeshModifier"

cd "$SCRIPT_DIR"

echo ""
echo "================================================================================"
echo "2/3: KooChainRun ë¹ë"
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
echo "â KooChainRun ë¹ë ìë£"
echo "   ì´ë ì¤: KooChainRun.dist â $LIB_DIR/KooChainRun"

mv KooChainRun.dist "$LIB_DIR/KooChainRun"
ln -sf "../lib/KooChainRun/KooChainRun.bin" "$BIN_DIR/KooChainRun"

# KooAutomatedModeller ë°±ì ë³µì
if [ -d "$AUTOMOD_BACKUP" ]; then
    echo ""
    echo "KooAutomatedModeller ì´ì  ë¹ë ë³µì ì¤..."
    cp -r "$AUTOMOD_BACKUP" "$LIB_DIR/KooAutomatedModeller"
    ln -sf "../lib/KooAutomatedModeller/KooAutomatedModeller.bin" "$BIN_DIR/KooAutomatedModeller"
    rm -rf "$AUTOMOD_BACKUP"
fi

echo ""
echo "================================================================================"
echo "3/3: ì¸ë¶ ë°íì ìì¡´ì± ë³µì¬ (Library)"
echo "================================================================================"
echo ""

LIBRARY_SRC=""
if [ -d "$SCRIPT_DIR/Library" ]; then
    LIBRARY_SRC="$SCRIPT_DIR/Library"
    echo "Library ìì¤: íë¡ì í¸ ë£¨í¸ ($LIBRARY_SRC)"
elif [ -d "$LIBRARY_BACKUP" ]; then
    LIBRARY_SRC="$LIBRARY_BACKUP"
    echo "Library ìì¤: ì´ì  ë¹ë ë°±ì ($LIBRARY_SRC)"
else
    echo "  â ï¸  Library ìì¤ ìì â íë¡ì í¸ ë£¨í¸ì Library/ í´ëë¥¼ ë°°ì¹íì¸ì"
fi

mkdir -p "$BUILD_DIR/Library"

if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/gmsh-4.14.1-Linux64" ]; then
    echo "gmsh ë³µì¬ ì¤..."
    cp -r "$LIBRARY_SRC/gmsh-4.14.1-Linux64" "$BUILD_DIR/Library/gmsh-4.14.1-Linux64"
    echo "  â Library/gmsh-4.14.1-Linux64/bin/gmsh"
fi

if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/Evolver" ]; then
    echo "Evolver ë³µì¬ ì¤..."
    cp -r "$LIBRARY_SRC/Evolver" "$BUILD_DIR/Library/Evolver"
    echo "  â Library/Evolver/ (ë°ì´ëë¦¬ + ì¤í¬ë¦½í¸)"
fi

if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/OCC" ]; then
    echo "OCC ë¤ì´í°ë¸ ë¼ì´ë¸ë¬ë¦¬ ë³µì¬ ì¤..."
    cp -r "$LIBRARY_SRC/OCC" "$BUILD_DIR/Library/OCC"
    echo "  â Library/OCC/ (.so ë¼ì´ë¸ë¬ë¦¬)"
fi

if [ -d "$LIBRARY_BACKUP" ]; then
    rm -rf "$LIBRARY_BACKUP"
fi

echo ""
echo "================================================================================"
echo "ë¹ë ìë£! (KooAutomatedModeller ì ì¸)"
echo "================================================================================"
echo ""
echo "ì¶ë ¥ ëë í ë¦¬: $BUILD_DIR"
echo ""
echo "ì¤í íì¼:"
ls -lh "$BIN_DIR/"
echo ""
echo "ë¹ë í¬ê¸°:"
du -sh "$BUILD_DIR"
du -sh "$LIB_DIR/KooMeshModifier"
du -sh "$LIB_DIR/KooChainRun"
echo ""

# SmartTwinPreprocessor ì¤ì¹
STP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/SmartTwinPreprocessor"

if [ -d "$STP_DIR" ]; then
    echo "================================================================================"
    echo "SmartTwinPreprocessorì ì¤ì¹"
    echo "================================================================================"
    echo ""

    if [ -d "$STP_DIR/lib/koocr" ] || [ -L "$STP_DIR/bin/koocr" ]; then
        sudo rm -rf "$STP_DIR/lib/koocr"
        sudo rm -f "$STP_DIR/bin/koocr"
    fi

    echo "KooChainRun ì¤ì¹ ì¤..."
    sudo rm -rf "$STP_DIR/lib/KooChainRun"
    sudo cp -r "$LIB_DIR/KooChainRun" "$STP_DIR/lib/KooChainRun"
    sudo ln -sf "../lib/KooChainRun/KooChainRun.bin" "$STP_DIR/bin/KooChainRun"

    echo "KooMeshModifier ì¤ì¹ ì¤..."
    sudo rm -rf "$STP_DIR/lib/KooMeshModifier"
    sudo cp -r "$LIB_DIR/KooMeshModifier" "$STP_DIR/lib/KooMeshModifier"
    sudo ln -sf "../lib/KooMeshModifier/KooMeshModifier.bin" "$STP_DIR/bin/KooMeshModifier"

    if [ -d "$BUILD_DIR/Library" ]; then
        echo "Library ì¤ì¹ ì¤..."
        sudo mkdir -p "$STP_DIR/Library"
        sudo cp -r "$BUILD_DIR/Library/"* "$STP_DIR/Library/"
    fi

    echo ""
    echo "â SmartTwinPreprocessor ì¤ì¹ ìë£"
    echo "   $STP_DIR/bin/KooChainRun --version:"
    "$STP_DIR/bin/KooChainRun" --version 2>&1 || true
fi

DATA_STP_DIR="/data/SmartTwinPreprocessor"
if [ -d "$DATA_STP_DIR" ]; then
    echo ""
    echo "================================================================================"
    echo "/data/SmartTwinPreprocessorì ì¶ê° ë°°í¬"
    echo "================================================================================"
    echo ""

    echo "KooChainRun ë°°í¬ ì¤..."
    sudo rm -rf "$DATA_STP_DIR/lib/KooChainRun"
    sudo cp -r "$LIB_DIR/KooChainRun" "$DATA_STP_DIR/lib/KooChainRun"
    sudo ln -sf "../lib/KooChainRun/KooChainRun.bin" "$DATA_STP_DIR/bin/KooChainRun"

    echo "KooMeshModifier ë°°í¬ ì¤..."
    sudo rm -rf "$DATA_STP_DIR/lib/KooMeshModifier"
    sudo cp -r "$LIB_DIR/KooMeshModifier" "$DATA_STP_DIR/lib/KooMeshModifier"
    sudo ln -sf "../lib/KooMeshModifier/KooMeshModifier.bin" "$DATA_STP_DIR/bin/KooMeshModifier"

    echo ""
    echo "â /data/SmartTwinPreprocessor ë°°í¬ ìë£"
    echo "   $DATA_STP_DIR/bin/KooChainRun --version:"
    "$DATA_STP_DIR/bin/KooChainRun" --version 2>&1 || true
fi

echo ""
echo "================================================================================"
echo "ì ì²´ ìë£! (KooAutomatedModeller ì ì¸)"
echo "================================================================================"
