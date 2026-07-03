#!/bin/bash
# AIRMESH 예제: 구+원기둥 STEP의 공기영역(bbox−솔리드) 사면체 메시 + STL 추출
cd "$(dirname "$0")"
KAM=${KAM:-../../../occProject/Generators/KooAutomatedModeller.py}
PY=${PY:-../../../venv312/bin/python}
(cd ../../../occProject/Generators && "$PY" KooAutomatedModeller.py AIRMESH airmesh.json ../../Examples/automatedmodeller/airmesh_sphere)
