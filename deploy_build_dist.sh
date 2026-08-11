#!/bin/bash
# build_dist 산출물을 호스트 배포 대상에 반영 (SIF 소스트리 + /data)
#
# 🔴 왜 별도 스크립트인가.
#    build_glibc_guard.sh 는 glibc>2.35 인 머신에서 빌드를 apptainer 컨테이너 안에서
#    재실행한다. 컨테이너에는 sudo 가 없어서, 빌드 스크립트 내부의 배포 블록이
#    "sudo: command not found" 로 조용히 실패해 왔다.
#    실측(2026-08-11): /data 의 KooChainRun 이 v81(08-05) 에 멈춰 있었고 v82 도 반영 안 됨.
#    SIF·계산노드는 최신인데 헤드노드 호스트 CLI 만 구버전이라, submit 이 호스트
#    바이너리를 직접 호출하는 구조에서 신규 기능이 동작하지 않았다.
#    → 배포는 반드시 컨테이너 **밖**에서 돌아야 한다. 가드가 컨테이너 빌드 종료 후
#      이 스크립트를 호출한다.
#
# 사용법: bash deploy_build_dist.sh [build_dist 경로]
#         (생략 시 이 스크립트 옆의 build_dist)
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${1:-$SCRIPT_DIR/build_dist}"
LIB_DIR="$BUILD_DIR/lib"

# 빌드 스크립트들과 동일한 대상 (STP_DIR / DATA_STP_DIR)
STP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/SmartTwinPreprocessor"   # SIF 소스트리
DATA_STP_DIR="/data/SmartTwinPreprocessor"

if [ ! -d "$LIB_DIR" ]; then
    echo "❌ build_dist/lib 없음: $LIB_DIR"
    exit 1
fi

if ! command -v sudo >/dev/null 2>&1; then
    echo "❌ sudo 없음 — 컨테이너 안에서 실행된 것 같다. 이 스크립트는 호스트에서 돌려야 한다."
    exit 1
fi

# build_dist 에 실제로 존재하는 모듈만 배포한다.
# (KooChainRun 단독 빌드 후에는 build_dist 에 KooChainRun 만 있으므로
#  대상의 KooMeshModifier 등은 건드리지 않는 것이 맞다)
MODULES=()
for d in "$LIB_DIR"/*/; do
    m="$(basename "$d")"
    [ -f "$d/$m.bin" ] && MODULES+=("$m")
done

if [ ${#MODULES[@]} -eq 0 ]; then
    echo "❌ build_dist/lib 에 배포할 모듈(.bin)이 없다"
    exit 1
fi

echo "================================================================================"
echo "build_dist 호스트 배포"
echo "================================================================================"
echo "  원본  : $LIB_DIR"
echo "  모듈  : ${MODULES[*]}"

rc=0
for TARGET in "$STP_DIR" "$DATA_STP_DIR"; do
    if [ ! -d "$TARGET" ]; then
        echo "  (없음, skip) $TARGET"
        continue
    fi
    echo
    echo "→ $TARGET"
    sudo mkdir -p "$TARGET/lib" "$TARGET/bin"
    for M in "${MODULES[@]}"; do
        # 빌드 스크립트의 rm -rf + cp -r 와 동치. .bak_* 는 남기지 않는다.
        if ! sudo rsync -a --delete --exclude '*.bak_*' "$LIB_DIR/$M/" "$TARGET/lib/$M/"; then
            echo "  🔴 $M 배포 실패"; rc=1; continue
        fi
        sudo ln -sf "../lib/$M/$M.bin" "$TARGET/bin/$M"
        printf "   %-22s %s\n" "$M" "$(sudo stat -c %y "$TARGET/lib/$M/$M.bin" | cut -d. -f1)"
    done
    if [ -d "$BUILD_DIR/Library" ]; then
        sudo mkdir -p "$TARGET/Library"
        sudo cp -r "$BUILD_DIR/Library/." "$TARGET/Library/" && echo "   Library 반영"
    fi
done

[ $rc -eq 0 ] || { echo; echo "🔴 배포 중 실패 발생"; exit 1; }

# 배포본이 실제로 실행되는지 확인 (문자열이 아니라 동작).
# KooChainRun 은 CLI 라 --help 로 검증 가능. 나머지는 파일 존재로 갈음.
if [ -x "$DATA_STP_DIR/bin/KooChainRun" ] && printf '%s\n' "${MODULES[@]}" | grep -qx KooChainRun; then
    if "$DATA_STP_DIR/bin/KooChainRun" --help >/dev/null 2>&1; then
        echo
        echo "✅ 호스트 CLI 동작 확인: $DATA_STP_DIR/bin/KooChainRun"
    else
        echo
        echo "🔴 호스트 CLI 실행 실패: $DATA_STP_DIR/bin/KooChainRun"
        exit 1
    fi
fi

echo
echo "✅ 호스트 배포 완료"
