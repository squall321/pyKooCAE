#!/usr/bin/env python3
"""
PathResolver - pyKooCAE 실행 파일 경로 자동 탐색

KooMeshModifier 경로를 다음 우선순위로 탐색:
1. 상대 경로 (KooChainRun와 같은 bin 디렉토리)
2. 환경 변수 KOO_PATH
3. scenario.json 설정
4. 기본값 (/opt/KooMeshModifier/run.sh)
"""

import os
import sys
from pathlib import Path
from typing import Optional


def find_koomeshmodifier(config_path: Optional[str] = None) -> str:
    """
    KooMeshModifier 실행 파일 경로를 탐색

    Args:
        config_path: scenario.json에 설정된 경로 (선택)

    Returns:
        KooMeshModifier 실행 파일 경로

    우선순위:
        1. 상대 경로: KooChainRun 실행 파일과 같은 bin 디렉토리
        2. 환경 변수: $KOO_PATH/bin/KooMeshModifier
        3. 설정 파일: config_path
        4. 기본값: /opt/KooMeshModifier/run.sh
    """

    # 1. 상대 경로: KooChainRun 실행 파일 위치 기준
    try:
        if getattr(sys, 'frozen', False):
            # Nuitka로 빌드된 경우
            exe_dir = Path(sys.executable).parent.resolve()
        else:
            # Python 스크립트로 실행된 경우
            exe_dir = Path(__file__).parent.parent.resolve()

        # bin 디렉토리에서 KooMeshModifier 찾기
        relative_path = exe_dir / "bin" / "KooMeshModifier"
        if relative_path.exists():
            return str(relative_path)

        # 같은 디렉토리에서 찾기
        same_dir_path = exe_dir / "KooMeshModifier"
        if same_dir_path.exists():
            return str(same_dir_path)

    except Exception:
        pass

    # 2. 환경 변수: KOO_PATH
    koo_path = os.environ.get("KOO_PATH")
    if koo_path:
        env_path = Path(koo_path) / "bin" / "KooMeshModifier"
        if env_path.exists():
            return str(env_path)

        # KOO_PATH가 직접 실행 파일을 가리킬 수도 있음
        if Path(koo_path).exists():
            return str(koo_path)

    # 3. 설정 파일
    if config_path and Path(config_path).exists():
        return config_path

    # 4. 기본값
    default_paths = [
        "/opt/pyKooCAE/bin/KooMeshModifier",
        "/opt/KooMeshModifier/run.sh",
        "/usr/local/bin/KooMeshModifier"
    ]

    for default_path in default_paths:
        if Path(default_path).exists():
            return default_path

    # 어디에도 없으면 기본값 반환 (실행 시 에러 발생할 것)
    return "/opt/KooMeshModifier/run.sh"


def find_kooremapper(config_path: Optional[str] = None) -> str:
    """KooRemapper 네이티브 바이너리 경로 탐색 (find_koomeshmodifier 와 동일 우선순위).

    REMAP 스텝은 KooMeshModifier 와 똑같이 apptainer exec <sif> <바이너리> 로 호출되므로,
    SmartTwinPreprocessor.sif 내부에 구워진 /opt/kooremapper/bin/KooRemapper 가 기본값.

    우선순위:
        1. 상대 경로: 실행 파일과 같은 bin 디렉토리
        2. 환경 변수: $KOO_PATH/bin/KooRemapper
        3. 설정 파일: config_path
        4. 기본값: /opt/kooremapper/bin/KooRemapper
    """
    try:
        if getattr(sys, 'frozen', False):
            exe_dir = Path(sys.executable).parent.resolve()
        else:
            exe_dir = Path(__file__).parent.parent.resolve()

        relative_path = exe_dir / "bin" / "KooRemapper"
        if relative_path.exists():
            return str(relative_path)
    except Exception:
        pass

    koo_path = os.environ.get("KOO_PATH")
    if koo_path:
        env_path = Path(koo_path) / "bin" / "KooRemapper"
        if env_path.exists():
            return str(env_path)

    if config_path and Path(config_path).exists():
        return config_path

    default_paths = [
        "/opt/kooremapper/bin/KooRemapper",
        "/opt/pyKooCAE/bin/KooRemapper",
    ]
    for default_path in default_paths:
        if Path(default_path).exists():
            return default_path

    return "/opt/kooremapper/bin/KooRemapper"


def get_koo_root() -> Optional[Path]:
    """
    pyKooCAE 루트 디렉토리 반환

    Returns:
        pyKooCAE 루트 디렉토리 (build_dist/)
    """
    try:
        if getattr(sys, 'frozen', False):
            # Nuitka 빌드: bin 디렉토리의 부모
            exe_dir = Path(sys.executable).parent.resolve()
            if exe_dir.name == "bin":
                return exe_dir.parent
            return exe_dir
        else:
            # Python 스크립트: pyKooCAE 루트
            return Path(__file__).parent.parent.resolve()
    except Exception:
        return None


if __name__ == "__main__":
    # 테스트
    print("KooMeshModifier 경로 탐색:")
    print(f"  발견: {find_koomeshmodifier()}")
    print()
    print("pyKooCAE 루트:")
    print(f"  {get_koo_root()}")
