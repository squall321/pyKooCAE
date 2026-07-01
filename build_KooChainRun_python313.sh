#!/bin/bash
# KooChainRun (KCR) ë¹ë ì¤í¬ë¦½í¸ - Python 3.13
# ì¬ì©ë²: ./build_KooChainRun_python313.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── glibc 2.35 ê°ì  ê°ë (ê³µíµ ì¤ëí«) ──
GUARD_SELF="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
GUARD_ARGS=("$@")
source "$SCRIPT_DIR/build_glibc_guard.sh"

echo "================================================================================"
echo "KooChainRun ë¹ë (Python 3.13)"
echo "================================================================================"
echo "venv: ./venv313"
echo "Python: $(./venv313/bin/python --version)"
echo ""

# ê¸°ì¡´ ë¹ë ê²°ê³¼ ì ê±°
echo "ê¸°ì¡´ ë¹ë ê²°ê³¼ ì ê±° ì¤..."
rm -rf KooChainRun.build KooChainRun.dist .nuitka

# Nuitkaë¡ ë¹ë
echo "Nuitka ë¹ë ìì..."
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
echo "ë¹ë ìë£!"
echo "================================================================================"
echo "ì¤í íì¼: $SCRIPT_DIR/KooChainRun.bin"
echo ""
echo "ë¹ë ì ë³´:"
ls -lh KooChainRun.bin
echo ""
echo "ì¤í íì¤í¸:"
./KooChainRun.bin --version 2>&1 || true
echo ""
echo "ë°°í¬ ë°©ë²:"
echo "  sudo cp KooChainRun.bin /usr/local/bin/KooChainRun"
echo "  sudo chmod +x /usr/local/bin/KooChainRun"
