#!/bin/bash
# KooChainRun (KCR) ë¹ë ì¤í¬ë¦½í¸ - Python 3.10
# ì¬ì©ë²: ./build_KooChainRun_python310.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── glibc 2.35 ê°ì  ê°ë (ê³µíµ ì¤ëí«) ──
GUARD_SELF="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
GUARD_ARGS=("$@")
source "$SCRIPT_DIR/build_glibc_guard.sh"

echo "================================================================================"
echo "KooChainRun ë¹ë (Python 3.10)"
echo "================================================================================"
echo "venv: ./venv"
echo "Python: $(./venv/bin/python --version)"
echo ""

# ê¸°ì¡´ ë¹ë ê²°ê³¼ ì ê±°
echo "ê¸°ì¡´ ë¹ë ê²°ê³¼ ì ê±° ì¤..."
rm -rf KooChainRun.build KooChainRun.dist .nuitka

# Nuitkaë¡ ë¹ë
echo "Nuitka ë¹ë ìì..."
./venv/bin/python -m nuitka ./KooChainRun \
        --standalone \
        --follow-imports \
        --include-package=Runner \
        --jobs=8 \
        --show-progress

echo ""
echo "================================================================================"
echo "ë¹ë ìë£!"
echo "================================================================================"
echo "ì¶ë ¥ ëë í ë¦¬: $SCRIPT_DIR/KooChainRun.dist"
echo "ì¤í íì¼: $SCRIPT_DIR/KooChainRun.dist/KooChainRun.bin"
echo ""
echo "ë¹ë ì ë³´:"
ls -lh KooChainRun.dist/KooChainRun.bin
echo ""
echo "ì¤í íì¤í¸:"
cd KooChainRun.dist
./KooChainRun.bin --version 2>&1 || true
cd ..
echo ""
echo "ë°°í¬ ë°©ë²:"
echo "  sudo cp -r KooChainRun.dist /opt/KooChainRun"
echo "  sudo ln -sf /opt/KooChainRun/KooChainRun.bin /usr/local/bin/KooChainRun"
