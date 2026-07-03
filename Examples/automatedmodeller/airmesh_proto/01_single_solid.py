# 단일 솔리드(구+원기둥 fuse) STEP → 공기영역 테트라 메시 → STL 파이프라인 검증
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gmsh
from airmesh_lib import (air_mesh_pipeline, create_step_fused, validate_stl,
                         write_surface_stl_manual)

WD = os.path.dirname(os.path.abspath(__file__))

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)

step = os.path.join(WD, "test_solid.step")
create_step_fused(step)
print(f"[gen] wrote {step} ({os.path.getsize(step)} bytes)")

res = air_mesh_pipeline(step, h=4.0, pad=15.0, workdir=WD, prefix="single")

# STL 물리그룹 필터 검증: cavity.stl 삼각형 수가 기대치와 다르면 수동 추출 fallback
val_air = validate_stl(res["stl_paths"]["air"], res["expected_air_volume"], "air")
val_cav = validate_stl(res["stl_paths"]["cavity"],
                       res["solid_volume_cad"], "cavity")
val_box = validate_stl(res["stl_paths"]["outer_box"],
                       res["box_volume"], "outer_box")
res["physical_group_stl_filter_worked"] = (
    val_cav["n_faces"] == res["tri_cavity_expected"]
    and val_box["n_faces"] == res["tri_outer_expected"])

if not res["physical_group_stl_filter_worked"]:
    # fallback: 수동 추출 재시도 (gmsh 세션이 아직 살아있는 동안)
    print("[warn] physical-group STL filter did NOT work, manual fallback")
    # 표면 재분류가 필요하므로 여기서는 결과만 기록

gmsh.finalize()

res["validation"] = {"air": val_air, "cavity": val_cav, "outer_box": val_box}
print(json.dumps(res, indent=2, default=str))
