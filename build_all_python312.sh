#!/bin/bash
# pyKooCAE ì ì²´ íµí© ë¹ë ì¤í¬ë¦½í¸ - Python 3.12
# ì¬ì©ë²:
#   ./build_all_python312.sh           # incremental (ìºì ë³´ì¡´)
#   ./build_all_python312.sh --clean   # clean ë¹ë

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
echo "pyKooCAE íµí© ë¹ë (Python 3.12)"
echo "================================================================================"
echo "Python: $(./venv312/bin/python --version)"
echo "ì¶ë ¥ ëë í ë¦¬: $BUILD_DIR"
if [ "$CLEAN_BUILD" = true ]; then
    echo "ëª¨ë: CLEAN (ìºì ëª¨ë ì­ì )"
else
    echo "ëª¨ë: INCREMENTAL (ìºì ë³´ì¡´)"
fi
echo ""

# ê¸°ì¡´ ë¹ë ê²°ê³¼ ì ê±° (Library ë°±ì í ë³µì)
LIBRARY_BACKUP="/tmp/pyKooCAE_Library_backup_$$"
if [ -d "$BUILD_DIR/Library" ]; then
    echo "  build_dist/Library ë°±ì ì¤..."
    cp -r "$BUILD_DIR/Library" "$LIBRARY_BACKUP"
fi
rm -rf "$BUILD_DIR"
if [ "$CLEAN_BUILD" = true ]; then
    echo "Nuitka cache + build/dist ì­ì  ì¤..."
    rm -rf KooChainRun.build KooChainRun.dist .nuitka
    rm -rf occProject/Generators/KooMeshModifier.build occProject/Generators/KooMeshModifier.dist occProject/Generators/.nuitka
    rm -rf occProject/Generators/KooAutomatedModeller.build occProject/Generators/KooAutomatedModeller.dist
else
    echo "Nuitka cache ë³´ì¡´ (ë³ê²½ ëª¨ëë§ ì¬ë¹ë)"
fi

mkdir -p "$BIN_DIR"
mkdir -p "$LIB_DIR"

echo ""
echo "================================================================================"
echo "1/4: KooMeshModifier ë¹ë"
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

echo ""
echo "================================================================================"
echo "2/4: KooAutomatedModeller ë¹ë"
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
echo "â KooAutomatedModeller ë¹ë ìë£"
echo "   ì´ë ì¤: KooAutomatedModeller.dist â $LIB_DIR/KooAutomatedModeller"

mv KooAutomatedModeller.dist "$LIB_DIR/KooAutomatedModeller"
ln -sf "../lib/KooAutomatedModeller/KooAutomatedModeller.bin" "$BIN_DIR/KooAutomatedModeller"

cd "$SCRIPT_DIR"

echo ""
echo "================================================================================"
echo "3/4: KooChainRun ë¹ë"
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

echo ""
echo "================================================================================"
echo "4/4: ì¸ë¶ ë°íì ìì¡´ì± ë³µì¬ (Library)"
echo "================================================================================"
echo ""

# Library ìì¤ ê²°ì : íë¡ì í¸ ë£¨í¸ Library/ â ë°±ììì ë³µì
# ì°ì ìì:
#   1. $SCRIPT_DIR/Library/ (íë¡ì í¸ ë£¨í¸)
#   2. $LIBRARY_BACKUP/ (ë¹ë ì  build_dist/Library/ ë°±ì)
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

# gmsh: KooMeshModifier, KooAutomatedModellerìì subprocessë¡ í¸ì¶
#   íì ê²½ë¡: /opt/gmsh-4.14.1-Linux64/bin/gmsh
#            â {basePath}/../../Library/gmsh-4.14.1-Linux64/bin/gmsh  (ìì íì)
#            â ./Library/gmsh-4.14.1-Linux64/bin/gmsh  (cwd ê¸°ì¤)
if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/gmsh-4.14.1-Linux64" ]; then
    echo "gmsh ë³µì¬ ì¤..."
    cp -r "$LIBRARY_SRC/gmsh-4.14.1-Linux64" "$BUILD_DIR/Library/gmsh-4.14.1-Linux64"
    echo "  â Library/gmsh-4.14.1-Linux64/bin/gmsh"
else
    echo "  â ï¸  gmsh-4.14.1-Linux64 ìì â ë°°í¬ íê²½ìì /opt/gmsh-4.14.1-Linux64 ëë PATH íì"
fi

# Evolver: WarpageSolderJointìì subprocessë¡ í¸ì¶ (ë°ì´ëë¦¬ + ì¤í¬ë¦½í¸ íì¼ ëª¨ë íì)
#   íì ê²½ë¡: /opt/Evolver/evolver
#            â {basePath}/../../Library/Evolver/evolver  (ìì íì)
#            â ./Library/Evolver/evolver  (cwd ê¸°ì¤)
#   ì¤í¬ë¦½í¸:  {folderPath}/Library/Evolver/{fileName}
if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/Evolver" ]; then
    echo "Evolver ë³µì¬ ì¤..."
    cp -r "$LIBRARY_SRC/Evolver" "$BUILD_DIR/Library/Evolver"
    echo "  â Library/Evolver/ (ë°ì´ëë¦¬ + ì¤í¬ë¦½í¸)"
else
    echo "  â ï¸  Evolver ìì â ë°°í¬ íê²½ìì /opt/Evolver ëë PATH íì"
fi

# OCC ë¤ì´í°ë¸ ë¼ì´ë¸ë¬ë¦¬ (.so): LD_LIBRARY_PATHë¡ ë¡ë
#   íì ê²½ë¡: {cwd}/Library/OCC/
#   Nuitka --include-package=OCCë Python ë°ì¸ë©ë§ í¬í¨, .soë ë³ë íì
if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/OCC" ]; then
    echo "OCC ë¤ì´í°ë¸ ë¼ì´ë¸ë¬ë¦¬ ë³µì¬ ì¤..."
    cp -r "$LIBRARY_SRC/OCC" "$BUILD_DIR/Library/OCC"
    echo "  â Library/OCC/ (.so ë¼ì´ë¸ë¬ë¦¬)"
else
    echo "  â ï¸  OCC ìì â pythonOCC .soê° Nuitka standaloneì ì´ë¯¸ í¬í¨ëìì ì ìì"
fi

# ë°±ì ì ë¦¬
if [ -d "$LIBRARY_BACKUP" ]; then
    rm -rf "$LIBRARY_BACKUP"
fi

echo ""
echo "================================================================================"
echo "íµí© ë¹ë ìë£!"
echo "================================================================================"
echo ""
echo "ì¶ë ¥ ëë í ë¦¬: $BUILD_DIR"
echo ""
echo "ëë í ë¦¬ êµ¬ì¡°:"
tree -L 2 "$BUILD_DIR" 2>/dev/null || find "$BUILD_DIR" -maxdepth 2 -type d
echo ""
echo "ì¤í íì¼:"
ls -lh "$BIN_DIR/"
echo ""
echo "ë¹ë í¬ê¸°:"
du -sh "$BUILD_DIR"
du -sh "$LIB_DIR/KooMeshModifier"
du -sh "$LIB_DIR/KooAutomatedModeller"
du -sh "$LIB_DIR/KooChainRun"
echo ""
echo "íì¤í¸:"
echo "  $BIN_DIR/KooMeshModifier --help"
echo "  $BIN_DIR/KooAutomatedModeller --help"
echo "  $BIN_DIR/KooChainRun --version"
echo ""
echo "================================================================================"
echo "5/5: SmartTwinPreprocessorì ì¤ì¹"
echo "================================================================================"
echo ""

STP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/SmartTwinPreprocessor"

if [ -d "$STP_DIR" ]; then
    echo "ì¤ì¹ ëì: $STP_DIR"
    echo ""

    # ê¸°ì¡´ koocr ì ê±° (ì´ë¦ ë³ê²½ ëì)
    if [ -d "$STP_DIR/lib/koocr" ] || [ -L "$STP_DIR/bin/koocr" ]; then
        echo "ê¸°ì¡´ koocr ì ê±° ì¤..."
        sudo rm -rf "$STP_DIR/lib/koocr"
        sudo rm -f "$STP_DIR/bin/koocr"
    fi

    # lib ë³µì¬
    echo "KooChainRun ì¤ì¹ ì¤..."
    sudo rm -rf "$STP_DIR/lib/KooChainRun"
    sudo cp -r "$LIB_DIR/KooChainRun" "$STP_DIR/lib/KooChainRun"
    sudo ln -sf "../lib/KooChainRun/KooChainRun.bin" "$STP_DIR/bin/KooChainRun"

    echo "KooMeshModifier ì¤ì¹ ì¤..."
    sudo rm -rf "$STP_DIR/lib/KooMeshModifier"
    sudo cp -r "$LIB_DIR/KooMeshModifier" "$STP_DIR/lib/KooMeshModifier"
    sudo ln -sf "../lib/KooMeshModifier/KooMeshModifier.bin" "$STP_DIR/bin/KooMeshModifier"

    echo "KooAutomatedModeller ì¤ì¹ ì¤..."
    sudo rm -rf "$STP_DIR/lib/KooAutomatedModeller"
    sudo cp -r "$LIB_DIR/KooAutomatedModeller" "$STP_DIR/lib/KooAutomatedModeller"
    sudo ln -sf "../lib/KooAutomatedModeller/KooAutomatedModeller.bin" "$STP_DIR/bin/KooAutomatedModeller"

    # Library (gmsh, Evolver) ë³µì¬
    if [ -d "$BUILD_DIR/Library" ]; then
        echo "Library ì¤ì¹ ì¤..."
        sudo mkdir -p "$STP_DIR/Library"
        sudo cp -r "$BUILD_DIR/Library/"* "$STP_DIR/Library/"
    fi

    echo ""
    echo "â SmartTwinPreprocessor ì¤ì¹ ìë£"
    echo "   $STP_DIR/bin/KooChainRun --version:"
    "$STP_DIR/bin/KooChainRun" --version 2>&1 || true
else
    echo "â ï¸  SmartTwinPreprocessor ëë í ë¦¬ ìì: $STP_DIR"
    echo "   ìë ì¤ì¹ê° íìí©ëë¤."
fi

# /data/SmartTwinPreprocessor ì¶ê° ë°°í¬ (ê³µì  ì¤í ë¦¬ì§)
DATA_STP_DIR="/data/SmartTwinPreprocessor"
if [ -d "$DATA_STP_DIR" ]; then
    echo ""
    echo "================================================================================"
    echo "6/6: /data/SmartTwinPreprocessorì ì¶ê° ë°°í¬"
    echo "================================================================================"
    echo ""
    echo "ë°°í¬ ëì: $DATA_STP_DIR"

    echo "KooChainRun ë°°í¬ ì¤..."
    sudo rm -rf "$DATA_STP_DIR/lib/KooChainRun"
    sudo cp -r "$LIB_DIR/KooChainRun" "$DATA_STP_DIR/lib/KooChainRun"
    sudo ln -sf "../lib/KooChainRun/KooChainRun.bin" "$DATA_STP_DIR/bin/KooChainRun"

    echo "KooMeshModifier ë°°í¬ ì¤..."
    sudo rm -rf "$DATA_STP_DIR/lib/KooMeshModifier"
    sudo cp -r "$LIB_DIR/KooMeshModifier" "$DATA_STP_DIR/lib/KooMeshModifier"
    sudo ln -sf "../lib/KooMeshModifier/KooMeshModifier.bin" "$DATA_STP_DIR/bin/KooMeshModifier"

    echo "KooAutomatedModeller ë°°í¬ ì¤..."
    sudo rm -rf "$DATA_STP_DIR/lib/KooAutomatedModeller"
    sudo cp -r "$LIB_DIR/KooAutomatedModeller" "$DATA_STP_DIR/lib/KooAutomatedModeller"
    sudo ln -sf "../lib/KooAutomatedModeller/KooAutomatedModeller.bin" "$DATA_STP_DIR/bin/KooAutomatedModeller"

    echo ""
    echo "â /data/SmartTwinPreprocessor ë°°í¬ ìë£"
    echo "   $DATA_STP_DIR/bin/KooChainRun --version:"
    "$DATA_STP_DIR/bin/KooChainRun" --version 2>&1 || true
fi

echo ""
echo "================================================================================"
echo "ì ì²´ ìë£!"
echo "================================================================================"
echo ""
echo "ë¹ë ì¶ë ¥: $BUILD_DIR"
echo "ì¤ì¹ ìì¹: $STP_DIR"
if [ -d "$DATA_STP_DIR" ]; then
    echo "ì¶ê° ë°°í¬: $DATA_STP_DIR"
fi
echo ""
echo "íê²½ ì¤ì :"
echo "  export PATH=$STP_DIR/bin:\$PATH"
