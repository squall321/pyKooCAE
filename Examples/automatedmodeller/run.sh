#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYKOOCAE_ROOT="$(cd "$SCRIPT_DIR/../../" && pwd)"
GENERATOR="$PYKOOCAE_ROOT/occProject/Generators/KooAutomatedModeller.py"

python3 "$GENERATOR" PKG aptest.txt
