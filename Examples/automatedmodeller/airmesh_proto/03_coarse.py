# 메시 사이즈가 솔리드 특징 치수보다 훨씬 클 때(h=40 >> r=10) 거동 확인
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gmsh
from airmesh_lib import air_mesh_pipeline, validate_stl

WD = os.path.dirname(os.path.abspath(__file__))
step = os.path.join(WD, "test_solid.step")  # 01에서 생성됨

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)

res = air_mesh_pipeline(step, h=40.0, pad=15.0, workdir=WD, prefix="coarse")
val_air = validate_stl(res["stl_paths"]["air"], res["expected_air_volume"], "air")
val_cav = validate_stl(res["stl_paths"]["cavity"],
                       res["solid_volume_cad"], "cavity")
gmsh.finalize()

res["validation"] = {"air": val_air, "cavity": val_cav}
print(json.dumps(res, indent=2, default=str))
