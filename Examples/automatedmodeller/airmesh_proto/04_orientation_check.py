# air.stl 캐비티 면 법선 방향 분석 + 공기영역 부호체적 보정 방법 검증
import json
import os
import sys

import numpy as np
import trimesh

WD = os.path.dirname(os.path.abspath(__file__))

m = trimesh.load(os.path.join(WD, "single_air.stl"), force="mesh")
bodies = m.split(only_watertight=False)
report = {"n_bodies": len(bodies), "bodies": []}

# 바깥쪽 바디 = bbox 대각선이 가장 큰 것
diag = [np.linalg.norm(b.bounds[1] - b.bounds[0]) for b in bodies]
outer_i = int(np.argmax(diag))
air_signed = 0.0
for i, b in enumerate(bodies):
    info = {"i": i, "n_faces": len(b.faces),
            "signed_volume": float(b.volume),
            "watertight": bool(b.is_watertight),
            "role": "outer_box" if i == outer_i else "cavity"}
    report["bodies"].append(info)
    if i == outer_i:
        air_signed += abs(b.volume)
    else:
        air_signed -= abs(b.volume)  # 캐비티는 항상 공기에서 빼야 함
report["air_volume_component_corrected"] = air_signed

# 올바른 방향의 air.stl 재작성: 캐비티 바디 법선 뒤집기(부호체적 양수면 뒤집음)
fixed = []
for i, b in enumerate(bodies):
    bb = b.copy()
    bb.fix_normals()  # 각 바디 outward 정렬
    if i != outer_i:
        bb.invert()    # 캐비티는 공기 기준 outward = 솔리드 안쪽으로
    fixed.append(bb)
merged = trimesh.util.concatenate(fixed)
out = os.path.join(WD, "single_air_oriented.stl")
merged.export(out)

m2 = trimesh.load(out, force="mesh")
report["oriented_stl"] = {"path": out,
                          "watertight": bool(m2.is_watertight),
                          "winding_consistent": bool(m2.is_winding_consistent),
                          "signed_volume": float(m2.volume)}
print(json.dumps(report, indent=2))
