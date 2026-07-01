#!/bin/bash
# pyKooCAE ì ì²´ íµí© ë¹ë ì¤í¬ë¦½í¸ - Python 3.10
# ì¬ì©ë²: ./build_all_python310.sh

set -e

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
echo "pyKooCAE íµí© ë¹ë (Python 3.10)"
echo "================================================================================"
echo "Python: $(./venv/bin/python --version)"
echo "ì¶ë ¥ ëë í ë¦¬: $BUILD_DIR"
echo ""

# ê¸°ì¡´ ë¹ë ê²°ê³¼ ì ê±°
echo "ê¸°ì¡´ ë¹ë ê²°ê³¼ ì ê±° ì¤..."
rm -rf "$BUILD_DIR"
rm -rf KooChainRun.build KooChainRun.dist .nuitka
rm -rf occProject/Generators/KooMeshModifier.build occProject/Generators/KooMeshModifier.dist occProject/Generators/.nuitka
rm -rf occProject/Generators/KooAutomatedModeller.build occProject/Generators/KooAutomatedModeller.dist

mkdir -p "$BIN_DIR"
mkdir -p "$LIB_DIR"

echo ""
echo "================================================================================"
echo "1/3: KooMeshModifier ë¹ë"
echo "================================================================================"
echo ""

cd occProject/Generators

../../venv/bin/python -m nuitka ./KooMeshModifier.py \
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
echo "2/3: KooAutomatedModeller ë¹ë"
echo "================================================================================"
echo ""

../../venv/bin/python -m nuitka ./KooAutomatedModeller.py \
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
echo "3/3: KooChainRun (KooChainRun) ë¹ë"
echo "================================================================================"
echo ""

./venv/bin/python -m nuitka ./KooChainRun \
        --standalone \
        --follow-imports \
        --include-package=Runner \
        --jobs=8 \
        --show-progress

echo ""
echo "â KooChainRun ë¹ë ìë£"
echo "   ì´ë ì¤: KooChainRun.dist â $LIB_DIR/KooChainRun"

mv KooChainRun.dist "$LIB_DIR/KooChainRun"
ln -sf "../lib/KooChainRun/KooChainRun.bin" "$BIN_DIR/KooChainRun"

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
echo "ë°°í¬ ë°©ë²:"
echo "  sudo cp -r $BUILD_DIR /opt/pyKooCAE"
echo "  sudo ln -sf /opt/pyKooCAE/bin/KooChainRun /usr/local/bin/KooChainRun"
echo "  sudo ln -sf /opt/pyKooCAE/bin/KooMeshModifier /usr/local/bin/KooMeshModifier"
echo "  sudo ln -sf /opt/pyKooCAE/bin/KooAutomatedModeller /usr/local/bin/KooAutomatedModeller"
echo ""
echo "íê²½ ì¤ì :"
echo "  export PATH=/opt/pyKooCAE/bin:\$PATH"
