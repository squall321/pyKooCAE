#!/bin/bash
# pyKooCAE 전체 통합 빌드 스크립트 - Python 3.12
# 사용법:
#   ./build_all_python312.sh           # incremental (캐시 보존)
#   ./build_all_python312.sh --clean   # clean 빌드

set -e

CLEAN_BUILD=false
if [ "$1" == "--clean" ]; then
    CLEAN_BUILD=true
fi

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
if [ "$CLEAN_BUILD" = true ]; then
    echo "모드: CLEAN (캐시 모두 삭제)"
else
    echo "모드: INCREMENTAL (캐시 보존)"
fi
echo ""

# 기존 빌드 결과 제거 (Library 백업 후 복원)
LIBRARY_BACKUP="/tmp/pyKooCAE_Library_backup_$$"
if [ -d "$BUILD_DIR/Library" ]; then
    echo "  build_dist/Library 백업 중..."
    cp -r "$BUILD_DIR/Library" "$LIBRARY_BACKUP"
fi
rm -rf "$BUILD_DIR"
if [ "$CLEAN_BUILD" = true ]; then
    echo "Nuitka cache + build/dist 삭제 중..."
    rm -rf KooChainRun.build KooChainRun.dist .nuitka
    rm -rf occProject/Generators/KooMeshModifier.build occProject/Generators/KooMeshModifier.dist occProject/Generators/.nuitka
    rm -rf occProject/Generators/KooAutomatedModeller.build occProject/Generators/KooAutomatedModeller.dist
else
    echo "Nuitka cache 보존 (변경 모듈만 재빌드)"
fi

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

echo ""
echo "================================================================================"
echo "4/4: 외부 런타임 의존성 복사 (Library)"
echo "================================================================================"
echo ""

# Library 소스 결정: 프로젝트 루트 Library/ → 백업에서 복원
# 우선순위:
#   1. $SCRIPT_DIR/Library/ (프로젝트 루트)
#   2. $LIBRARY_BACKUP/ (빌드 전 build_dist/Library/ 백업)
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

# gmsh: KooMeshModifier, KooAutomatedModeller에서 subprocess로 호출
#   탐색 경로: /opt/gmsh-4.14.1-Linux64/bin/gmsh
#            → {basePath}/../../Library/gmsh-4.14.1-Linux64/bin/gmsh  (상위 탐색)
#            → ./Library/gmsh-4.14.1-Linux64/bin/gmsh  (cwd 기준)
if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/gmsh-4.14.1-Linux64" ]; then
    echo "gmsh 복사 중..."
    cp -r "$LIBRARY_SRC/gmsh-4.14.1-Linux64" "$BUILD_DIR/Library/gmsh-4.14.1-Linux64"
    echo "  ✅ Library/gmsh-4.14.1-Linux64/bin/gmsh"
else
    echo "  ⚠️  gmsh-4.14.1-Linux64 없음 — 배포 환경에서 /opt/gmsh-4.14.1-Linux64 또는 PATH 필요"
fi

# Evolver: WarpageSolderJoint에서 subprocess로 호출 (바이너리 + 스크립트 파일 모두 필요)
#   탐색 경로: /opt/Evolver/evolver
#            → {basePath}/../../Library/Evolver/evolver  (상위 탐색)
#            → ./Library/Evolver/evolver  (cwd 기준)
#   스크립트:  {folderPath}/Library/Evolver/{fileName}
if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/Evolver" ]; then
    echo "Evolver 복사 중..."
    cp -r "$LIBRARY_SRC/Evolver" "$BUILD_DIR/Library/Evolver"
    echo "  ✅ Library/Evolver/ (바이너리 + 스크립트)"
else
    echo "  ⚠️  Evolver 없음 — 배포 환경에서 /opt/Evolver 또는 PATH 필요"
fi

# OCC 네이티브 라이브러리 (.so): LD_LIBRARY_PATH로 로드
#   탐색 경로: {cwd}/Library/OCC/
#   Nuitka --include-package=OCC는 Python 바인딩만 포함, .so는 별도 필요
if [ -n "$LIBRARY_SRC" ] && [ -d "$LIBRARY_SRC/OCC" ]; then
    echo "OCC 네이티브 라이브러리 복사 중..."
    cp -r "$LIBRARY_SRC/OCC" "$BUILD_DIR/Library/OCC"
    echo "  ✅ Library/OCC/ (.so 라이브러리)"
else
    echo "  ⚠️  OCC 없음 — pythonOCC .so가 Nuitka standalone에 이미 포함되었을 수 있음"
fi

# 백업 정리
if [ -d "$LIBRARY_BACKUP" ]; then
    rm -rf "$LIBRARY_BACKUP"
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

# /data/SmartTwinPreprocessor 추가 배포 (공유 스토리지)
DATA_STP_DIR="/data/SmartTwinPreprocessor"
if [ -d "$DATA_STP_DIR" ]; then
    echo ""
    echo "================================================================================"
    echo "6/6: /data/SmartTwinPreprocessor에 추가 배포"
    echo "================================================================================"
    echo ""
    echo "배포 대상: $DATA_STP_DIR"

    echo "KooChainRun 배포 중..."
    sudo rm -rf "$DATA_STP_DIR/lib/KooChainRun"
    sudo cp -r "$LIB_DIR/KooChainRun" "$DATA_STP_DIR/lib/KooChainRun"
    sudo ln -sf "../lib/KooChainRun/KooChainRun.bin" "$DATA_STP_DIR/bin/KooChainRun"

    echo "KooMeshModifier 배포 중..."
    sudo rm -rf "$DATA_STP_DIR/lib/KooMeshModifier"
    sudo cp -r "$LIB_DIR/KooMeshModifier" "$DATA_STP_DIR/lib/KooMeshModifier"
    sudo ln -sf "../lib/KooMeshModifier/KooMeshModifier.bin" "$DATA_STP_DIR/bin/KooMeshModifier"

    echo "KooAutomatedModeller 배포 중..."
    sudo rm -rf "$DATA_STP_DIR/lib/KooAutomatedModeller"
    sudo cp -r "$LIB_DIR/KooAutomatedModeller" "$DATA_STP_DIR/lib/KooAutomatedModeller"
    sudo ln -sf "../lib/KooAutomatedModeller/KooAutomatedModeller.bin" "$DATA_STP_DIR/bin/KooAutomatedModeller"

    echo ""
    echo "✅ /data/SmartTwinPreprocessor 배포 완료"
    echo "   $DATA_STP_DIR/bin/KooChainRun --version:"
    "$DATA_STP_DIR/bin/KooChainRun" --version 2>&1 || true
fi

echo ""
echo "================================================================================"
echo "전체 완료!"
echo "================================================================================"
echo ""
echo "빌드 출력: $BUILD_DIR"
echo "설치 위치: $STP_DIR"
if [ -d "$DATA_STP_DIR" ]; then
    echo "추가 배포: $DATA_STP_DIR"
fi
echo ""
echo "환경 설정:"
echo "  export PATH=$STP_DIR/bin:\$PATH"
