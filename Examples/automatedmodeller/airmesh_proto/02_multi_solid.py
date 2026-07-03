# 분리된 솔리드 2개 STEP → occ.cut 다중 tool 동작 + 공기영역 파이프라인 검증
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gmsh
from airmesh_lib import air_mesh_pipeline, create_step_two_solids, validate_stl

WD = os.path.dirname(os.path.abspath(__file__))

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)

step = os.path.join(WD, "test_two_solids.step")
create_step_two_solids(step)
print(f"[gen] wrote {step} ({os.path.getsize(step)} bytes)")

res = air_mesh_pipeline(step, h=4.0, pad=12.0, workdir=WD, prefix="multi")

val_air = validate_stl(res["stl_paths"]["air"], res["expected_air_volume"], "air")
val_cav = validate_stl(res["stl_paths"]["cavity"],
                       res["solid_volume_cad"], "cavity(2 bodies)")
val_box = validate_stl(res["stl_paths"]["outer_box"],
                       res["box_volume"], "outer_box")
res["physical_group_stl_filter_worked"] = (
    val_cav["n_faces"] == res["tri_cavity_expected"]
    and val_box["n_faces"] == res["tri_outer_expected"])

gmsh.finalize()

res["validation"] = {"air": val_air, "cavity": val_cav, "outer_box": val_box}
print(json.dumps(res, indent=2, default=str))
