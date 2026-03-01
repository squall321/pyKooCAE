"""
충격 위치 소스 파서

충격 DOE에서 사용할 충격 위치(X, Y) 목록을 생성합니다.

position_source 타입:
    1. grid_nxm: NxM 균등 그리드 (bbox 내)
    2. grid_spacing: 간격 지정 그리드 (bbox 내)
    3. manual: 수동 좌표 목록

입력: position_source 설정 (scenario.json)
출력: ImpactPosition 리스트 [(name, x, y), ...]

Author: koo.park
Email: koo.park@samsung.com
Group: CAE
"""

import os
from typing import List, Optional
from dataclasses import dataclass


def parse_bbox_from_k_file(k_file_path: str) -> List[float]:
    """LS-DYNA .k 파일의 *NODE 섹션에서 X-Y 바운딩박스 추출

    Fixed-width 포맷: NID(8), X(16), Y(16), Z(16), TC(8), RC(8)

    Parameters:
        k_file_path: .k 파일 경로

    Returns:
        [xmin, ymin, xmax, ymax]
    """
    if not os.path.exists(k_file_path):
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {k_file_path}")

    xmin = float('inf')
    ymin = float('inf')
    xmax = float('-inf')
    ymax = float('-inf')
    node_count = 0
    in_node_section = False

    with open(k_file_path, 'r') as f:
        for line in f:
            if line.startswith('$'):
                continue

            if line.strip().upper().startswith('*NODE'):
                in_node_section = True
                continue

            if in_node_section and line.startswith('*'):
                break

            if in_node_section:
                try:
                    x = float(line[8:24].strip())
                    y = float(line[24:40].strip())
                    if x < xmin:
                        xmin = x
                    if x > xmax:
                        xmax = x
                    if y < ymin:
                        ymin = y
                    if y > ymax:
                        ymax = y
                    node_count += 1
                except (ValueError, IndexError):
                    continue

    if node_count == 0:
        raise ValueError(f"모델 파일에서 노드를 찾을 수 없습니다: {k_file_path}")

    return [xmin, ymin, xmax, ymax]


@dataclass
class ImpactPosition:
    """충격 위치"""
    name: str       # "P_001_001" (row_col) 또는 "P_0042"
    x: float
    y: float


def parse_grid_nxm(config: dict, bbox: Optional[List[float]] = None) -> List[ImpactPosition]:
    """NxM 균등 그리드 생성

    Parameters:
        config: grid_nxm 설정
            - nx: X축 포인트 수
            - ny: Y축 포인트 수
            - bbox: [xmin, ymin, xmax, ymax] (optional)
        bbox: 외부에서 전달된 bbox (config에 없을 때 사용)

    Returns:
        ImpactPosition 리스트
    """
    nx = config.get("nx", 5)
    ny = config.get("ny", 5)
    bbox = config.get("bbox", bbox)

    if bbox is None or len(bbox) != 4:
        raise ValueError("grid_nxm에 bbox가 필요합니다: [xmin, ymin, xmax, ymax]")

    xmin, ymin, xmax, ymax = bbox

    positions = []
    for iy in range(ny):
        for ix in range(nx):
            if nx == 1:
                x = (xmin + xmax) / 2.0
            else:
                x = xmin + ix * (xmax - xmin) / (nx - 1)

            if ny == 1:
                y = (ymin + ymax) / 2.0
            else:
                y = ymin + iy * (ymax - ymin) / (ny - 1)

            name = f"P_{iy+1:03d}_{ix+1:03d}"
            positions.append(ImpactPosition(name=name, x=round(x, 6), y=round(y, 6)))

    return positions


def parse_grid_spacing(config: dict, bbox: Optional[List[float]] = None) -> List[ImpactPosition]:
    """간격 지정 그리드 생성

    Parameters:
        config: grid_spacing 설정
            - spacing_x: X축 간격
            - spacing_y: Y축 간격
            - bbox: [xmin, ymin, xmax, ymax] (optional)
        bbox: 외부에서 전달된 bbox (config에 없을 때 사용)

    Returns:
        ImpactPosition 리스트
    """
    spacing_x = config.get("spacing_x")
    spacing_y = config.get("spacing_y")
    bbox = config.get("bbox", bbox)

    if spacing_x is None or spacing_y is None:
        raise ValueError("grid_spacing에 spacing_x, spacing_y가 필요합니다")
    if bbox is None or len(bbox) != 4:
        raise ValueError("grid_spacing에 bbox가 필요합니다: [xmin, ymin, xmax, ymax]")

    xmin, ymin, xmax, ymax = bbox

    positions = []
    idx = 0
    y = ymin
    iy = 0
    while y <= ymax + 1e-9:
        x = xmin
        ix = 0
        while x <= xmax + 1e-9:
            name = f"P_{iy+1:03d}_{ix+1:03d}"
            positions.append(ImpactPosition(name=name, x=round(x, 6), y=round(y, 6)))
            x += spacing_x
            ix += 1
            idx += 1
        y += spacing_y
        iy += 1

    return positions


def parse_manual(config: dict) -> List[ImpactPosition]:
    """수동 좌표 목록 파싱

    Parameters:
        config: manual 설정
            - positions: [[x1,y1], [x2,y2], ...]

    Returns:
        ImpactPosition 리스트
    """
    pos_list = config.get("positions", [])
    if not pos_list:
        raise ValueError("manual에 positions 리스트가 필요합니다")

    positions = []
    for i, pos in enumerate(pos_list):
        if len(pos) < 2:
            raise ValueError(f"위치 {i}: [x, y] 형식이 필요합니다")
        name = f"P_{i+1:04d}"
        positions.append(ImpactPosition(name=name, x=float(pos[0]), y=float(pos[1])))

    return positions


def parse_position_source(config: dict, model_file: Optional[str] = None) -> List[ImpactPosition]:
    """position_source 설정에서 충격 위치 목록 생성

    Parameters:
        config: position_source 설정
            - source_type: "grid_nxm" | "grid_spacing" | "manual"
            - grid_nxm: { nx, ny, bbox }
            - grid_spacing: { spacing_x, spacing_y, bbox }
            - manual: { positions: [[x,y], ...] }
        model_file: 모델 파일 경로 (.k) — bbox 미지정 시 자동 계산에 사용

    Returns:
        ImpactPosition 리스트

    Example:
        >>> config = {
        ...     "source_type": "grid_nxm",
        ...     "grid_nxm": { "nx": 3, "ny": 3, "bbox": [0, 0, 100, 100] }
        ... }
        >>> positions = parse_position_source(config)
        >>> len(positions)
        9
    """
    source_type = config.get("source_type", "grid_nxm")

    # bbox 자동 계산: sub_config에 bbox가 없고 model_file이 있으면 모델에서 추출
    auto_bbox = None
    if source_type in ("grid_nxm", "grid_spacing"):
        sub_config = config.get(source_type, {})
        if sub_config.get("bbox") is None and model_file:
            auto_bbox = parse_bbox_from_k_file(model_file)
            print(f"모델 바운딩박스 자동 계산: {model_file}")
            print(f"  X: [{auto_bbox[0]:.4f}, {auto_bbox[2]:.4f}]")
            print(f"  Y: [{auto_bbox[1]:.4f}, {auto_bbox[3]:.4f}]")

    if source_type == "grid_nxm":
        sub_config = config.get("grid_nxm", {})
        return parse_grid_nxm(sub_config, bbox=auto_bbox)

    elif source_type == "grid_spacing":
        sub_config = config.get("grid_spacing", {})
        return parse_grid_spacing(sub_config, bbox=auto_bbox)

    elif source_type == "manual":
        sub_config = config.get("manual", {})
        return parse_manual(sub_config)

    else:
        raise ValueError(f"지원하지 않는 position_source 타입: {source_type}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("충격 위치 소스 파서 테스트")
    print("=" * 80)

    # 테스트 1: 3x3 그리드
    print("\n테스트 1: grid_nxm (3x3, bbox=[0,0,100,100])")
    config1 = {
        "source_type": "grid_nxm",
        "grid_nxm": {"nx": 3, "ny": 3, "bbox": [0, 0, 100, 100]}
    }
    positions1 = parse_position_source(config1)
    print(f"총 위치 수: {len(positions1)}")
    for p in positions1:
        print(f"  {p.name}: X={p.x:>8.2f}, Y={p.y:>8.2f}")

    # 테스트 2: 간격 그리드
    print("\n테스트 2: grid_spacing (spacing=25, bbox=[0,0,100,100])")
    config2 = {
        "source_type": "grid_spacing",
        "grid_spacing": {"spacing_x": 25, "spacing_y": 25, "bbox": [0, 0, 100, 100]}
    }
    positions2 = parse_position_source(config2)
    print(f"총 위치 수: {len(positions2)}")
    for p in positions2:
        print(f"  {p.name}: X={p.x:>8.2f}, Y={p.y:>8.2f}")

    # 테스트 3: 수동 좌표
    print("\n테스트 3: manual (3 positions)")
    config3 = {
        "source_type": "manual",
        "manual": {"positions": [[10, 20], [50, 50], [90, 80]]}
    }
    positions3 = parse_position_source(config3)
    print(f"총 위치 수: {len(positions3)}")
    for p in positions3:
        print(f"  {p.name}: X={p.x:>8.2f}, Y={p.y:>8.2f}")

    print("\n" + "=" * 80)
    print("모든 테스트 완료!")
    print("=" * 80 + "\n")
