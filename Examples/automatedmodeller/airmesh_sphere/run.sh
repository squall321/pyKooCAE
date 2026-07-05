#!/bin/bash
# AIRMESH 예제: 구+원기둥 STEP의 공기영역(bbox−솔리드) 사면체 메시 + STL 추출
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
cd "$ROOT/occProject/Generators"
exec "$ROOT/venv312/bin/python" KooAutomatedModeller.py AIRMESH airmesh.json "$HERE"
