# 실린더 충격추 back 단 재질이 KMM 옵션(*Impactor 키)으로 전달되는지 검증하는 회귀 시험
"""
back 질량은 KMM 에서 'Impactor' 파트로 만들어지고 DensityImpactor/YoungsModulusImpactor/
PoissonRatioImpactor 로 재질을 받는다. 예전 러너는 cylinder_stages[-1] 에서 지름·높이만 읽고
재질을 버려, 공식 예제 impact_cylinder_8pi 의 충격추가 ≈418 g → ≈493 g(+18%)로 생성됐다.

실행: python3 tests/test_impact_cylinder_back_material.py
"""
import contextlib
import copy
import io
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from Runner.CumulativeDesigner import CumulativeDesigner              # noqa: E402
from Runner.CumulativeScenarioRunner import CumulativeScenarioRunner  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print("  %-64s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.msgs = []

    def emit(self, record):
        self.msgs.append(record.getMessage())


def gen(cfg):
    cfg = copy.deepcopy(cfg)
    base = tempfile.mkdtemp(prefix="impback_")
    cfg["base_dir"] = base
    Path(base, cfg["scenarios"][0]["template"]).write_text(
        "*KEYWORD\n*NODE\n       1             0.0             0.0             0.0\n*END\n")
    with contextlib.redirect_stdout(io.StringIO()):
        d = CumulativeDesigner(cfg)
        rc = d.parse_user_config()
        p = os.path.join(base, "runner_config.json")
        d.save_runner_config(rc, p)
    rcfg = json.load(open(p, encoding="utf-8"))
    out = tempfile.mkdtemp(prefix="impback_out_")
    rcfg["project"]["output_dir"] = out
    r = CumulativeScenarioRunner.__new__(CumulativeScenarioRunner)
    r.config, r.output_dir, r.run_id, r.input_dir = rcfg, out, "t", "/tmp"
    r._get_prev_run_dir = lambda doe, step: None
    r._build_preserve_block = lambda: ""
    step = next(s for s in rcfg["scenario"]["steps"] if s["mode"] == "IMPACT")
    cap = _Capture()
    logging.getLogger().addHandler(cap)
    try:
        txt = Path(r._create_step_config(1, step)).read_text(encoding="utf-8")
    finally:
        logging.getLogger().removeHandler(cap)
    kv = {}
    for line in txt.splitlines():
        if "," in line and not line.startswith("*"):
            k, v = line.split(",", 1)
            kv[k] = v
    return kv, cap.msgs


def ex(name):
    return json.load(open(ROOT / "Examples/scenario_examples" / (name + ".json"), encoding="utf-8"))


print("[1] 공식 예제 3단(8파이) — back 단 재질이 *Impactor 로 나간다")
kv, _ = gen(ex("impact_cylinder_8pi"))
check("DensityImpactor = back 단 6.57e-09", float(kv["DensityImpactor"]) == 6.57e-09, kv["DensityImpactor"])
check("YoungsModulusImpactor = back 단 207000", float(kv["YoungsModulusImpactor"]) == 207000.0)
check("PoissonRatioImpactor = back 단 0.3", float(kv["PoissonRatioImpactor"]) == 0.3)
check("front·mid 는 그대로", float(kv["DensityImpactorFront"]) == 1.18e-09 and float(kv["DensityImpactorMid"]) == 6.57e-09)

print("\n[2] 공식 예제 2단(15파이)")
kv, _ = gen(ex("impact_cylinder_15pi"))
check("DensityImpactor = back 단 6.854e-09", float(kv["DensityImpactor"]) == 6.854e-09, kv["DensityImpactor"])

print("\n[3] back 단에 재질이 없으면 기존 동작 — 최상위 값, 없으면 기본값")
v = ex("impact_cylinder_8pi")
imp = v["simulation_params"]["impact"]
for st in imp["cylinder_stages"]:
    if st.get("role") == "back":
        for k in ("density", "youngs_modulus", "poisson"):
            st.pop(k, None)
imp.update({"density": 5.0e-9, "youngs_modulus": 190000.0, "poisson_ratio": 0.29})
kv, _ = gen(v)
check("최상위 density 5e-09", float(kv["DensityImpactor"]) == 5.0e-09)
check("최상위 poisson_ratio 0.29", float(kv["PoissonRatioImpactor"]) == 0.29)
for k in ("density", "youngs_modulus", "poisson_ratio"):
    imp.pop(k)
kv, _ = gen(v)
check("둘 다 없으면 기본 7.85e-09 / 201000 / 0.3",
      (float(kv["DensityImpactor"]), float(kv["YoungsModulusImpactor"]), float(kv["PoissonRatioImpactor"]))
      == (7.85e-09, 201000.0, 0.3))

print("\n[4] 충돌 — back 단과 최상위가 다르면 back 단 우선 + 경고")
v = ex("impact_cylinder_8pi")
v["simulation_params"]["impact"]["density"] = 5.0e-9
kv, logs = gen(v)
check("back 단 6.57e-09 우선", float(kv["DensityImpactor"]) == 6.57e-09)
check("경고 로그", any("back 단 density" in m for m in logs), str(logs))

print("\n[5] 단 안 poisson_ratio 표기도 받는다 (front·back)")
v = ex("impact_cylinder_15pi")
for st in v["simulation_params"]["impact"]["cylinder_stages"]:
    st["poisson_ratio"] = 0.31
    st.pop("poisson", None)
kv, _ = gen(v)
check("back PoissonRatioImpactor 0.31", float(kv["PoissonRatioImpactor"]) == 0.31)
check("front PoissonRatioImpactorFront 0.31 (예전엔 0.49 로 조용히 떨어짐)", float(kv["PoissonRatioImpactorFront"]) == 0.31)

print("\n[6] 구 충격추 예제 — 영향 없음")
kv, _ = gen(ex("impact_example"))
imp = ex("impact_example")["simulation_params"]["impact"]
check("구 충격추 재질 = 최상위(또는 기본)",
      float(kv["DensityImpactor"]) == float(imp.get("density", 7.85e-9)))

print()
if FAILS:
    print("[FAIL] 실패 %d 건" % len(FAILS))
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
print("[PASS] 실패 0 건")
