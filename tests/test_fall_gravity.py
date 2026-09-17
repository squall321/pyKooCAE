# 자유낙하 g 결정(Gravity 키 > 재질 밀도 단위계)과 drop_weight_impact 속도 이중 가산 제거를 검증하는 회귀 시험
"""
배경
  - KMM 은 Height > 100 이면 mm(g=9810), 이하면 m(g=9.81) 로 추정했다 → mm 모델의 50 mm 낙하가 31 배 느렸다.
  - drop_weight_impact 워크플로우는 속도를 InitialVelocityZ 로 주고 Height 도 넘겨 KMM 이 한 번 더 더했다.

실행: venv312/bin/python tests/test_fall_gravity.py
"""
import contextlib
import io
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(GEN))

FAILS = []


def check(name, cond, detail=""):
    print("  %-66s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def box_model(path, rho):
    n, h, lines, idx, nid = 4, 2.5, [], {}, 0
    for k in range(3):
        for j in range(n + 1):
            for i in range(n + 1):
                nid += 1
                idx[(i, j, k)] = nid
                lines.append(f"{nid:8d}{i * h:16.6f}{j * h:16.6f}{k * 1.0:16.6f}")
    elems, eid = [], 0
    for k in range(2):
        for j in range(n):
            for i in range(n):
                eid += 1
                c = [idx[(i, j, k)], idx[(i + 1, j, k)], idx[(i + 1, j + 1, k)], idx[(i, j + 1, k)],
                     idx[(i, j, k + 1)], idx[(i + 1, j, k + 1)], idx[(i + 1, j + 1, k + 1)], idx[(i, j + 1, k + 1)]]
                elems.append(f"{eid:8d}{1:8d}" + "".join(f"{x:8d}" for x in c))
    f10 = lambda *v: "".join(f"{str(x):>10s}" for x in v)  # noqa: E731
    Path(path).write_text("\n".join(
        ["*KEYWORD", "*PART", "BLOCK", f10(1, 1, 1), "*SECTION_SOLID", f10(1, 1),
         "*MAT_ELASTIC", f10(1, rho, "200000.0", "0.3"), "*NODE"] + lines + ["*ELEMENT_SOLID"] + elems + ["*END"]) + "\n")


class _Mat:
    def __init__(self, rho):
        self.rho = rho

    def GetRho(self):
        return self.rho


class _MatMan:
    def __init__(self, rhos):
        self.materials = {i: _Mat(r) for i, r in enumerate(rhos)}
        self.rigidMaterials = {}


def main():
    with contextlib.redirect_stdout(io.StringIO()):
        import KooMeshModifier as K
        from KooCAEManager.KooDynaAdvancedModification import KooDynaAdvancedModification

    print("[1] g 판정 헬퍼")
    adv = KooDynaAdvancedModification.__new__(KooDynaAdvancedModification)

    class _Imp:
        pass
    adv.dynaImporter = _Imp()

    def resolve(rhos, option=None):
        adv.dynaImporter.matManager = _MatMan(rhos)
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            f = adv._ResolveFallGravity(option or {}, "T")
        return f, buf.getvalue()

    f, _ = resolve([7.85e-9, 2.33e-9, 1.2e-9])
    check("ton-mm-s 모델 → h=50 에서도 g=9810", f(50) == 9810.0 and f(1500) == 9810.0)
    f, _ = resolve([7850.0, 2700.0, 1200.0])
    check("kg-m-s 모델 → h=0.5 에서 g=9.81", f(0.5) == 9.81)
    f, _ = resolve([7.85e-9], {"Gravity": 9.81e-3})
    check("Gravity 키가 밀도 판정보다 우선", f(50) == 9.81e-3)
    f, out = resolve([7.85e-6, 2.7e-6])
    check("kg-mm-ms 처럼 판정 불가 → 옛 추정 + 경고", f(150) == 9810.0 and f(50) == 9.81 and "WARNING" in out)
    f, out = resolve([7.85, 2.7, 1.2])
    check("g-cm-s(g/cm³ 7.85) → kg-m-s 로 오판하지 않고 경고", "WARNING" in out and "→ kg-m-s" not in out)
    f, out = resolve([])
    check("재질 없음 → 옛 추정 + 경고", f(50) == 9.81 and "WARNING" in out)
    f, _ = resolve([7.85e-9, 7.85e-9, 7850.0])
    check("중앙값으로 판정 (이상값 하나에 안 흔들림)", f(50) == 9810.0)

    print("[2] KMM 파서 Gravity 키")
    d = tempfile.mkdtemp(prefix="fallg_")
    Path(d, "o.txt").write_text("""*Inputfile
m.k
*Mode
DROP_ATTITUDE,1
DROP_WEIGHT_IMPACT_TEST,2
**DropAttitude,1
EulerRolling,0
EulerPitching,0
EulerYawing,0
Gravity,9810
Height,50
**EndDropAttitude
**DropWeightImpactTest,2
Gravity,9.81
Height,0.5
Type,Sphere
**EndDropWeightImpactTest
*End
""")
    with contextlib.redirect_stdout(io.StringIO()):
        g = K.KooMeshModifier()
        g.SetCurrentDirectory(d)
        g.ImportOption("o.txt")
    check("DROP_ATTITUDE Gravity=9810, Height=[50]",
          g.modeIDOption[1].get("Gravity") == 9810.0 and g.modeIDOption[1].get("Height") == [50.0])
    check("DWI Gravity=9.81, Type=Sphere",
          g.modeIDOption[2].get("Gravity") == 9.81 and g.modeIDOption[2].get("Type") == "Sphere")

    print("[3] drop_weight_impact 워크플로우 — 속도는 한 번만")
    from Runner.DropWeightImpactWorkflow import _write_dwi_step_config
    cfg = os.path.join(d, "dwi.txt")
    with contextlib.redirect_stdout(io.StringIO()):
        _write_dwi_step_config(cfg, "m.k", d, 1.0, 2.0, 1, 1, {"type": "Sphere", "radius": 5.0, "height": 500},
                               0.001, 1e-6, "DampingSpring", 0.0, {})
    text = Path(cfg).read_text()
    check("InitialVelocityZ,0", re.search(r"^InitialVelocityZ,0$", text, re.M) is not None, text[:400])
    check("Gravity,9810.0 명시", re.search(r"^Gravity,9810(\.0)?$", text, re.M) is not None)
    with contextlib.redirect_stdout(io.StringIO()):
        g = K.KooMeshModifier()
        g.SetCurrentDirectory(d)
        g.ImportOption("dwi.txt")
    o = g.modeIDOption[1]
    check("KMM 이 읽은 값: Vz=[0], Height=[500], Gravity=9810", o.get("InitialVelocityZ") == [0.0]
          and o.get("Height") == [500.0] and o.get("Gravity") == 9810.0, str({k: o.get(k) for k in ("InitialVelocityZ", "Height", "Gravity")}))

    print("[4] 러너 simulation_params.gravity → Gravity 줄")
    from Runner.StepConfigBuilder import build_drop_attitude_config
    base = dict(model_file="m.k", output_dir="/tmp", project="P", doe_index=1, step_num=1, mode="DROP",
                condition="c", euler={"roll": 0, "pitch": 0, "yaw": 0}, run_directory_mode=False)
    t0 = build_drop_attitude_config(sim_params={"height": 50}, **base)
    t1 = build_drop_attitude_config(sim_params={"height": 50, "gravity": 9810}, **base)
    check("gravity 미지정 → Gravity 줄 없음 (기존 출력 불변)", "Gravity," not in t0)
    check("gravity 지정 → Gravity,9810", "\nGravity,9810\n" in t1)
    check("둘의 차이는 Gravity 줄 하나", t1.replace("\nGravity,9810", "") == t0)

    print("[5] 끝단: ton-mm-s 모델 50 mm 낙하 → 초기속도 √(2·9810·50)")
    w = tempfile.mkdtemp(prefix="fallg_e2e_", dir="/tmp")
    box_model(os.path.join(w, "box.k"), "7.85e-9")
    t = build_drop_attitude_config(sim_params={"height": 50, "tFinal": 0.001, "dt": 1e-4}, **base)
    Path(w, "drop.txt").write_text(t.replace("*Inputfile\nm.k", "*Inputfile\nbox.k"))
    r = subprocess.run([str(ROOT / "venv312" / "bin" / "python"), str(GEN / "KooMeshModifier.py"), "drop.txt", w],
                       cwd=str(GEN), capture_output=True, text=True, timeout=600)
    deck = Path(w, "box_drop.k")
    vz = None
    if deck.exists():
        lines = deck.read_text().splitlines()
        for i, ln in enumerate(lines):
            if ln.startswith("*INITIAL_VELOCITY"):
                cards = [x for x in lines[i + 1:i + 6] if not x.startswith("$")]
                # _GENERATION: 1번 카드 VZ(51~60칸) / 일반: 2번 카드 VZ(21~30칸)
                vz = float(cards[0][50:60]) if "GENERATION" in ln else float(cards[1][20:30])
                break
    want = -math.sqrt(2 * 9810 * 50)
    check(f"INITIAL_VELOCITY VZ ≈ {want:.1f}", vz is not None and abs(vz - want) < 1.0, f"실제 {vz}, rc={r.returncode} {r.stdout[-300:]}")

    print()
    if FAILS:
        print("FAIL %d 건" % len(FAILS))
        for x in FAILS:
            print("  -", x)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
