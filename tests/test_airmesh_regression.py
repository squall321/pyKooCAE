# AIRMESH 회귀 테스트 — 적대적 리뷰가 실증한 결함 시나리오 포함 (venv312로 실행)
# 실행: venv312/bin/python tests/test_airmesh_regression.py
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GEN = os.path.join(ROOT, "occProject", "Generators")
sys.path.insert(0, GEN)

import gmsh  # noqa: E402
import trimesh  # noqa: E402

from KooAirMesh.AirMeshGenerator import run_from_config  # noqa: E402

WD = tempfile.mkdtemp(prefix="airmesh_test_")
PASS = []


def check(name, cond, detail=""):
    if not cond:
        raise AssertionError("{n} FAILED {d}".format(n=name, d=detail))
    PASS.append(name)
    print("  ok:", name, detail)


def make_step(path, builder):
    gmsh.initialize(readConfigFiles=False)
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("gen")
        builder()
        gmsh.model.occ.synchronize()
        gmsh.write(path)
    finally:
        gmsh.finalize()


def run_cfg(name, cfg):
    p = os.path.join(WD, name + ".json")
    with open(p, "w") as f:
        json.dump(cfg, f)
    cwd = os.getcwd()
    os.chdir(WD)
    try:
        run_from_config(p)
    finally:
        os.chdir(cwd)
    rp = os.path.join(WD, name + "_report.json")
    return json.load(open(rp)) if os.path.exists(rp) else None


# ---- T1: 골든 예제를 run.sh로 (run.sh 경로 수정 검증 포함) --------------------
def t1_golden_runsh():
    ex = os.path.join(ROOT, "Examples", "automatedmodeller", "airmesh_sphere")
    r = subprocess.run(["bash", os.path.join(ex, "run.sh")],
                       capture_output=True, text=True, timeout=600)
    check("T1 run.sh exit0", r.returncode == 0, r.stderr[-300:])
    check("T1 Complete line", "Complete AIRMESH" in r.stdout)
    rep = json.load(open(os.path.join(ex, "airmesh_report.json")))
    m = trimesh.load(os.path.join(ex, "airmesh_air.stl"))
    check("T1 gates", rep["status"] == "ok" and m.is_watertight
          and abs(rep["volumes"]["air_discrete_vs_expected_pct"]) < 0.5
          and rep["mesh"]["quality"]["minSICN"]["n_inverted"] == 0)
    check("T1 histogram", "histogram" in rep["mesh"]["quality"]["minSICN"])


# ---- T2: 밀폐 하우징 내부 보이드 — orientation 홀짝 규칙 (CRITICAL 재발 방지) --
def t2_hollow_void():
    step = os.path.join(WD, "hollow.step")

    def b():
        outer = gmsh.model.occ.addBox(0, 0, 0, 20, 20, 20)
        inner = gmsh.model.occ.addBox(5, 5, 5, 10, 10, 10)
        gmsh.model.occ.cut([(3, outer)], [(3, inner)])
    make_step(step, b)
    rep = run_cfg("hollow", {"airmesh_version": 1, "input_step": step,
                             "mesh_size": 2.0, "padding": 5.0})
    check("T2 status ok", rep and rep["status"] == "ok")
    check("T2 two air volumes", rep["boolean"]["n_air_volumes"] == 2,
          str(rep["boolean"]["n_air_volumes"]))
    m = trimesh.load(os.path.join(WD, "hollow_air.stl"))
    # 진짜 공기 = 30^3 − (20^3 − 10^3) = 27000 − 7000 = 20000 (보이드 1000 포함)
    check("T2 signed volume = air(void 포함)", abs(m.volume - 20000.0) / 20000.0 < 0.01,
          "signed={v:.1f}".format(v=m.volume))
    check("T2 vs_expected", abs(rep["volumes"]["air_discrete_vs_expected_pct"]) < 0.5,
          str(rep["volumes"].get("air_discrete_vs_expected_pct")))


# ---- T3: 분리 솔리드 2개 ------------------------------------------------------
def t3_multi():
    step = os.path.join(WD, "two.step")

    def b():
        gmsh.model.occ.addSphere(0, 0, 0, 8)
        gmsh.model.occ.addBox(30, -5, -5, 10, 10, 10)
    make_step(step, b)
    rep = run_cfg("two", {"airmesh_version": 1, "input_step": step,
                          "mesh_size": 3.0, "padding": 8.0})
    m = trimesh.load(os.path.join(WD, "two_air.stl"))
    check("T3 gates", rep["status"] == "ok" and m.is_watertight
          and abs(rep["volumes"]["air_discrete_vs_expected_pct"]) < 0.5)


# ---- T4: solid_selection — 미선택 솔리드가 메시/품질에 포함되면 안 됨 (MAJOR) --
def t4_selection():
    step = os.path.join(WD, "sel.step")

    def b():
        gmsh.model.occ.addBox(0, 0, 0, 10, 10, 10)
        gmsh.model.occ.addBox(20, 0, 0, 2, 2, 2)  # 미선택 대상
    make_step(step, b)
    rep = run_cfg("sel", {"airmesh_version": 1, "input_step": step,
                          "mesh_size": 2.0, "padding": 5.0,
                          "solid_selection": [1]})
    check("T4 status ok", rep["status"] == "ok")
    check("T4 제거 경고", any("solid_selection" in w for w in rep["warnings"]))
    # .msh 안의 3D 요소 수 == 리포트 n_tets (미선택 솔리드 잔류 메시 없음)
    gmsh.initialize(readConfigFiles=False)
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.open(os.path.join(WD, "sel_air.msh"))
        _, etags, _ = gmsh.model.mesh.getElements(3)
        n3d = sum(len(t) for t in etags)
        nvol = len(gmsh.model.getEntities(3))
    finally:
        gmsh.finalize()
    check("T4 msh 3D == n_tets", n3d == rep["mesh"]["n_tets"],
          "{a} vs {b}".format(a=n3d, b=rep["mesh"]["n_tets"]))
    check("T4 msh 볼륨 수 == 공기 볼륨 수",
          nvol == rep["boolean"]["n_air_volumes"], str(nvol))


# ---- T5: 불리언 1회 실패 주입 — eps-pad 재시도 경로 (CRITICAL 재발 방지) -------
def t5_epspad_injection():
    from KooAirMesh import AirMeshCore
    step = os.path.join(ROOT, "Examples", "automatedmodeller",
                        "airmesh_sphere", "sphere_cyl.stp")
    base = run_cfg("inj_base", {"airmesh_version": 1, "input_step": step,
                                "mesh_size": 4.0, "padding": 15.0})
    orig_cut = AirMeshCore.gmsh.model.occ.cut
    state = {"failed": False}

    def failing_once(*a, **k):
        if not state["failed"]:
            state["failed"] = True
            raise RuntimeError("injected boolean failure")
        return orig_cut(*a, **k)

    AirMeshCore.gmsh.model.occ.cut = failing_once
    try:
        rep = run_cfg("inj", {"airmesh_version": 1, "input_step": step,
                              "mesh_size": 4.0, "padding": 15.0})
    finally:
        AirMeshCore.gmsh.model.occ.cut = orig_cut
    check("T5 status ok", rep["status"] == "ok")
    check("T5 eps_pad_retry", rep["boolean"]["eps_pad_retry"] is True)
    check("T5 outer 6면 분류", rep["surfaces"]["n_outer"] >= 6,
          str(rep["surfaces"]))
    ratio = rep["mesh"]["n_tets"] / base["mesh"]["n_tets"]
    check("T5 잔류 박스 없음(tet 비율)", 0.8 < ratio < 1.3,
          "ratio={r:.2f}".format(r=ratio))
    check("T5 체적 경고 없음",
          not any("CAD 공기체적" in w for w in rep["warnings"]), str(rep["warnings"]))
    m = trimesh.load(os.path.join(WD, "inj_air.stl"))
    check("T5 watertight+체적", m.is_watertight
          and abs(rep["volumes"]["air_discrete_vs_expected_pct"]) < 0.5)


# ---- T6: 미터 단위 소형 부품 — 분류 톨러런스 절대 하한 (MAJOR 재발 방지) -------
def t6_meter_scale():
    step = os.path.join(WD, "meter.step")

    def b():
        gmsh.model.occ.addSphere(0, 0, 0, 0.008)
    make_step(step, b)
    rep = run_cfg("meter", {"airmesh_version": 1, "input_step": step,
                            "mesh_size": 0.002, "padding": 0.005})
    check("T6 status ok", rep["status"] == "ok")
    check("T6 outer 6면 분류", rep["surfaces"]["n_outer"] >= 6, str(rep["surfaces"]))
    check("T6 vs_expected", abs(rep["volumes"]["air_discrete_vs_expected_pct"]) < 0.5)


# ---- T7: 실패 경로 계약 -------------------------------------------------------
def t7_failure_contract():
    rep = run_cfg("bad", {"airmesh_version": 1, "typo": 1})
    check("T7 config 오류 리포트", rep and rep["status"] == "failed"
          and rep["error"]["code"] == "E_CONFIG")
    rep = run_cfg("nostep", {"airmesh_version": 1, "input_step": "ghost.stp",
                             "mesh_size": 1.0})
    check("T7 없는 STEP", rep["status"] == "failed")


if __name__ == "__main__":
    try:
        for t in (t1_golden_runsh, t2_hollow_void, t3_multi, t4_selection,
                  t5_epspad_injection, t6_meter_scale, t7_failure_contract):
            print("[{n}]".format(n=t.__name__))
            t()
        print("\nALL {n} CHECKS PASS".format(n=len(PASS)))
    finally:
        shutil.rmtree(WD, ignore_errors=True)
