# 낙하추 충격(DWI) 재질·댐퍼 치수 폴백이 모델 단위계(재질 밀도로 판정)를 따르는지 덱 카드 값으로 판정하는 회귀 시험
"""
실행: venv312/bin/python tests/test_dwi_fallback_units.py   (KMM 을 작은 블록 모델로 여러 번 돌린다, ~1분)

배경 (2026-10-23)
  KMM DropWeightImpactTest(DampingSpring)·PartialRigid(OutsideRigid*) 는 받지 못한 재질 키에 SI 값을 넣었다.
  - 충격체 앞부분: E 2.07e11·ρ 7800
  - 댐퍼: E 1e10·ρ 1000·치수 0.001
  - 바닥판: E 1e10·ρ 1000
  그런데 러너(DWI·누적 IMPACT)는 댐퍼 재질 키를 넘기지 않는다. 그래서 mm(ton-mm-s) 덱에 E 1e10 MPa·ρ 1000 ton/mm³
  인 댐퍼 보가 들어갔다(받침 강성·질량이 수천~10^12 배 어긋남). 이제 KMM 이 중력 판정(_ResolveFallGravity)과 같은
  재질 밀도 판정으로 단위계를 고르고, 같은 물성을 그 단위로 바꿔 쓴다. SI 모델은 그대로다.
판정은 출력 덱(model_dwit.k)의 MAT_ELASTIC_TITLE·SECTION_BEAM_TITLE 카드 값으로 한다.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
PY = str(ROOT / "venv312" / "bin" / "python")
import os  # noqa: E402
# 이 호스트의 ~/.local/bin/gmsh 는 시스템 파이썬으로 돌아 충격체가 0 요소가 된다 → venv312/bin 을 PATH 앞에(리뷰 F)
ENV = dict(os.environ, PATH=str(ROOT / "venv312" / "bin") + ":" + os.environ.get("PATH", ""))
BASE = Path(tempfile.mkdtemp(prefix="dwi_units_"))
FAILS = []


def check(name, cond, detail=""):
    print("  %-70s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def model(scale, rho, e):
    """1×1×2 블록(육면체 2개). scale=1 → mm, 0.001 → m."""
    out, nid = [], 0
    for z in range(3):
        for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1)):
            nid += 1
            out.append(f"{nid:8d}{x * scale:16.6e}{y * scale:16.6e}{z * scale:16.6e}")
    return ("*KEYWORD\n*NODE\n" + "\n".join(out) + "\n*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1)
            + "*MAT_ELASTIC\n" + f10(1, rho, e, 0.3) + "*ELEMENT_SOLID\n"
            + "".join(f"{k:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(4 * k - 3, 4 * k + 5)) + "\n" for k in (1, 2))
            + "*END\n")


MM = dict(scale=1.0, rho="7.85E-09", e=210000, g=9810.0, h=10, loc=0.5, sphere="0.3", cyl="0.3,0.4,0.2,0.4,0.4",
          mesh=0.1, off=0.05, imp_rho="7.85e-09", imp_e="200000.0", wall_e="10000.0", wall_rho="1e-09")
SI = dict(scale=0.001, rho="7850.0", e="2.1E+11", g=9.81, h=0.01, loc=0.0005, sphere="0.0003",
          cyl="0.0003,0.0004,0.0002,0.0004,0.0004", mesh=0.0001, off=0.00005, imp_rho="7850.0", imp_e="2.0e11",
          wall_e="1.0e10", wall_rho="1000.0")


def run_dwi(u, mode="DampingSpring", itype="Sphere", extra=""):
    imp = "" if u["imp_rho"] is None else (f"DensityImpactor,{u['imp_rho']}\nYoungsModulusImpactor,{u['imp_e']}\n"
                                           "PoissonRatioImpactor,0.3\n")
    d = Path(tempfile.mkdtemp(dir=BASE))
    Path(d, "model.k").write_text(model(u["scale"], u["rho"], u["e"]))
    dim = u["sphere"] if itype == "Sphere" else u["cyl"]
    Path(d, "opt.txt").write_text(f"""*Inputfile
model.k
*Mode
DROP_WEIGHT_IMPACT_TEST,1
**DropWeightImpactTest,1
TFinal,0.001
DT,1e-06
LocationX,{u['loc']}
LocationY,{u['loc']}
Height,{u['h']}
Gravity,{u['g']}
ImpactorType,{itype}
ImpactorDimension,{dim}
MeshSize,{u['mesh']}
{imp}GenerationMode,{mode}
OffsetDistance,{u['off']}
YoungsModulusWall,{u['wall_e']}
PoissonRatioWall,0.3
DensityWall,{u['wall_rho']}
{extra}**EndDropWeightImpactTest
*End
""")
    r = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt.txt"], cwd=d, capture_output=True, text=True,
                       timeout=900, env=ENV)
    out = Path(d, "model_dwit.k")
    return r.returncode, r.stdout + r.stderr, out.read_text() if out.exists() else ""


def card_after(text, keyword, title, skip_comments=True, nth=1):
    """keyword 블록 중 제목이 title 인 것의 nth 번째 데이터 줄 → 숫자 목록."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().upper() == keyword and i + 1 < len(lines) and lines[i + 1].strip() == title:
            k, seen = i + 2, 0
            while k < len(lines) and not lines[k].startswith("*"):
                if not (skip_comments and lines[k].startswith("$")):
                    seen += 1
                    if seen == nth:
                        return [float(x) for x in lines[k].split()]
                k += 1
    return None


def mat(text, title):
    c = card_after(text, "*MAT_ELASTIC_TITLE", title)
    return None if c is None else (c[1], c[2])   # (RO, E)


def close(a, b):
    return a is not None and b is not None and abs(a - b) <= 1e-6 * max(abs(a), abs(b))


print("[1] mm(ton-mm-s) 모델 — 댐퍼 폴백을 같은 물성의 mm 단위로")
rc, log, text = run_dwi(MM)
m = mat(text, "DamperMaterial")
check("DampingSpring·구 — rc 0", rc == 0, log[-300:])
check("  DamperMaterial ρ=1e-9·E=1e4", m is not None and close(m[0], 1e-9) and close(m[1], 1e4), f"{m}")
sec = card_after(text, "*SECTION_BEAM_TITLE", "DamperSetion", nth=2)
check("  댐퍼 단면(TS1·TS2·TT1·TT2) = 1.0 mm", sec is not None and all(close(v, 1.0) for v in sec[:4]), f"{sec}")
check("  안내가 ton-mm-s 판정을 말하고 '10^12 배' 경고는 없다", "ton-mm-s" in log and "10^12" not in log,
      [ln for ln in log.splitlines() if "누락" in ln or "10^12" in ln][:3])

print("[2] SI(kg-m-s) 모델 — 지금과 같다")
rc, log, text = run_dwi(SI)
m = mat(text, "DamperMaterial")
check("DampingSpring·구 — rc 0", rc == 0, log[-300:])
check("  DamperMaterial ρ=1000·E=1e10 (옛 값)", m is not None and close(m[0], 1000.0) and close(m[1], 1e10), f"{m}")
sec = card_after(text, "*SECTION_BEAM_TITLE", "DamperSetion", nth=2)
check("  댐퍼 단면 = 0.001 m (옛 값)", sec is not None and all(close(v, 0.001) for v in sec[:4]), f"{sec}")

print("[3] mm 모델 실린더 — 앞부분 재질(충격체 재질도 없으면 단위계 폴백)")
bare = dict(MM, imp_rho=None, imp_e=None)
for mode in ("DampingSpring", "OutsideRigidPart"):
    rc, log, text = run_dwi(bare, mode=mode, itype="cylinder")
    m = mat(text, "ImpactorFrontMaterial")
    check(f"{mode}·실린더·충격체 재질 없음 — 앞부분 ρ=7.8e-9·E=2.07e5", rc == 0 and m is not None and close(m[0], 7.8e-9)
          and close(m[1], 2.07e5), f"rc={rc} {m} {log[-200:] if rc else ''}")
    m = mat(text, "ImpactorMaterial")
    check("  충격체 본체도 단위계 폴백 7.8e-9·2.07e5", m is not None and close(m[0], 7.8e-9) and close(m[1], 2.07e5), f"{m}")

print("[4] 값을 준 키는 그대로 쓴다")
rc, log, text = run_dwi(MM, extra="DensityDamper,2e-9\nYoungsModulusDamper,5000\nDimensionDamper,2,2,2\n")
m = mat(text, "DamperMaterial")
sec = card_after(text, "*SECTION_BEAM_TITLE", "DamperSetion", nth=2)
check("DensityDamper·YoungsModulusDamper·DimensionDamper 지정 — 그 값", rc == 0 and m is not None and close(m[0], 2e-9)
      and close(m[1], 5000.0) and sec is not None and all(close(v, 2.0) for v in sec[:4]), f"rc={rc} {m} {sec}")

print("[6] 명시한 Gravity 가 단위계 판정에 앞선다(_ResolveFallGravity 와 같은 순서) — 리뷰 E A1")
d1 = model(SI["scale"], SI["rho"], SI["e"]).replace("*ELEMENT_SOLID", "*MAT_ELASTIC\n" + f10(5, "1.0E-12", 1.0, 0.3)
                                                  + "*MAT_ELASTIC\n" + f10(6, "1.0E-12", 1.0, 0.3) + "*ELEMENT_SOLID")


def run_deck(deck, u, mode="DampingSpring", itype="Sphere", extra=""):
    imp = "" if u["imp_rho"] is None else (f"DensityImpactor,{u['imp_rho']}\nYoungsModulusImpactor,{u['imp_e']}\n"
                                           "PoissonRatioImpactor,0.3\n")
    d = Path(tempfile.mkdtemp(dir=BASE))
    rc, log, text = None, None, None
    Path(d, "model.k").write_text(deck)
    dim = u["sphere"] if itype == "Sphere" else u["cyl"]
    Path(d, "opt.txt").write_text(f"""*Inputfile
model.k
*Mode
DROP_WEIGHT_IMPACT_TEST,1
**DropWeightImpactTest,1
TFinal,0.001
DT,1e-06
LocationX,{u['loc']}
LocationY,{u['loc']}
Height,{u['h']}
Gravity,{u['g']}
ImpactorType,{itype}
ImpactorDimension,{dim}
MeshSize,{u['mesh']}
{imp}GenerationMode,{mode}
OffsetDistance,{u['off']}
YoungsModulusWall,{u['wall_e']}
PoissonRatioWall,0.3
DensityWall,{u['wall_rho']}
{extra}**EndDropWeightImpactTest
*End
""")
    r = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
    out = Path(d, "model_dwit.k")
    return r.returncode, r.stdout + r.stderr, out.read_text() if out.exists() else ""


rc, log, text = run_deck(d1, SI)
m = mat(text, "DamperMaterial")
check("SI 모델 + 밀도 1e-12 더미 재질 둘 + Gravity 9.81 — 댐퍼 SI(1000·1e10)", rc == 0 and m is not None
      and close(m[0], 1000.0) and close(m[1], 1e10), f"rc={rc} {m}")
d2 = model(MM["scale"], MM["rho"], MM["e"]).replace("*MAT_ELASTIC\n" + f10(1, MM["rho"], MM["e"], 0.3),
                                                    "*MAT_HYPERELASTIC_RUBBER\n" + f10(1, MM["rho"], 0.49, 0) + f10(0.1, 0.2))
rc, log, text = run_deck(d2, MM)
m = mat(text, "DamperMaterial")
check("mm 모델인데 밀도를 못 읽는 재질뿐 + Gravity 9810 — 댐퍼 ton-mm-s(1e-9·1e4)", rc == 0 and m is not None
      and close(m[0], 1e-9) and close(m[1], 1e4), f"rc={rc} {m} {log[-200:] if rc else ''}")

print("[7] 실린더 앞부분 재질을 주지 않으면 충격체 본체 재질을 물려받는다(Mid 와 같은 규칙) — 리뷰 E")
al = dict(MM, imp_rho="2.7e-09", imp_e="70000.0")
for mode in ("DampingSpring", "OutsideRigidPart"):
    rc, log, text = run_dwi(al, mode=mode, itype="cylinder")
    m = mat(text, "ImpactorFrontMaterial")
    check(f"{mode}·실린더·충격체 알루미늄 — 앞부분 2.7e-9·7e4", rc == 0 and m is not None and close(m[0], 2.7e-9)
          and close(m[1], 7e4), f"rc={rc} {m}")
cyl3 = dict(MM, cyl="0.3,0.4,0.2,0.35,0.2,0.4,0.4")
rc, log, text = run_dwi(cyl3, mode="OutsideRigidPart", itype="cylinder")
check("OutsideRigidPart·3단 실린더(7값) — NameError 없이 rc 0·중간단 재질 생성", rc == 0 and mat(text, "ImpactorMidMaterial")
      is not None, f"rc={rc} {log[-300:] if rc else ''}")

print("[8] 3단 실린더 다위치 — 두 번째 위치 덱의 중간단·초기속도·tied 접촉이 한 위치 덱과 같다 — 리뷰 F")
import re  # noqa: E402


def mid_stats(text):
    lines = text.splitlines()
    mat = {lines[i + 2].split()[0]: lines[i + 1].strip() for i, ln in enumerate(lines)
           if ln.startswith("*MAT_ELASTIC_TITLE") and i + 2 < len(lines) and lines[i + 2].split()}
    mid = None
    for i, ln in enumerate(lines):
        if ln.startswith("*PART"):
            data = [x for x in lines[i + 1:i + 4] if not x.startswith("$")]
            f = data[1].split() if len(data) >= 2 else []
            if len(f) > 2 and mat.get(f[2]) == "ImpactorMidMaterial":
                mid = f[0]
    el, sect = 0, None
    for ln in lines:
        if ln.startswith("*"):
            sect = ln.strip().upper()
        elif sect and sect.startswith("*ELEMENT_SOLID") and ln.split() and not ln.startswith("$"):
            el += ln.split()[1] == mid
    return (el, len(re.findall(r"^\*INITIAL_VELOCITY_GENERATION", text, re.M)), len(re.findall(r"^\*CONTACT_TIED", text, re.M)))


def run_locs(xs, mode, bd):
    d = Path(tempfile.mkdtemp(dir=BASE))
    Path(d, "model.k").write_text(model(MM["scale"], MM["rho"], MM["e"]))
    n = len(xs)
    Path(d, "opt.txt").write_text(
        "*Inputfile\nmodel.k\n*Mode\nDROP_WEIGHT_IMPACT_TEST,1\n**DropWeightImpactTest,1\nTFinal,0.001\nDT,1e-06\n"
        f"LocationX,{','.join(map(str, xs))}\nLocationY,{','.join(['0.5'] * n)}\nHeight,{','.join(['10'] * n)}\n"
        f"InitialVelocityX,{','.join(['0'] * n)}\nInitialVelocityY,{','.join(['0'] * n)}\nInitialVelocityZ,{','.join(['0'] * n)}\n"
        "Gravity,9810.0\nImpactorType,cylinder\nImpactorDimension,0.3,0.4,0.2,0.35,0.2,0.4,0.4\nMeshSize,0.1\n"
        "DensityImpactor,7.85e-09\nYoungsModulusImpactor,200000.0\nPoissonRatioImpactor,0.3\n"
        f"GenerationMode,{mode}\nOffsetDistance,0.05\nYoungsModulusWall,10000.0\nPoissonRatioWall,0.3\nDensityWall,1e-09\n"
        + (f"BoundaryDistance,{bd}\n" if bd else "") + "**EndDropWeightImpactTest\n*End\n")
    r = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
    decks = {re.search(r"LOCX_([0-9.e+-]+)", q.name).group(1): q.read_text() for q in d.glob("model_MODE_*.k")}
    if not decks and Path(d, "model_dwit.k").exists():
        decks = {"only": Path(d, "model_dwit.k").read_text()}
    return r.returncode, decks


for mode, bd in (("OutsideRigidPart", 5.0), ("OutsideRigidElement", 0), ("DampingSpring", 0), ("DampingSpring", 0.2)):
    rc1, one = run_locs([0.7], mode, bd)
    rc2, two = run_locs([0.3, 0.7], mode, bd)
    s1 = mid_stats(next(iter(one.values()))) if one else None
    s2 = mid_stats(two.get("7.000e-01", "")) if two else None
    check(f"{mode}·BD={bd} — 2위치 x=0.7 덱 (중간단 요소, IVG, tied) = 1위치 덱", rc1 == 0 and rc2 == 0 and s1 is not None
          and s1[0] > 0 and s1 == s2, f"rc={rc1},{rc2} 1위치={s1} 2위치={s2}")

print("[5] 누적 IMPACT 템플릿 — mesh_size·dimension_damper 는 시나리오에 있을 때만 넘긴다")
import contextlib  # noqa: E402
import copy  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402

sys.path.insert(0, str(ROOT))
from Runner.CumulativeDesigner import CumulativeDesigner  # noqa: E402
from Runner.CumulativeScenarioRunner import CumulativeScenarioRunner  # noqa: E402


def impact_kv(cfg):
    cfg = copy.deepcopy(cfg)
    base = tempfile.mkdtemp(dir=BASE)
    cfg["base_dir"] = base
    Path(base, cfg["scenarios"][0]["template"]).write_text(
        "*KEYWORD\n*NODE\n       1             0.0             0.0             0.0\n*END\n")
    with contextlib.redirect_stdout(io.StringIO()):
        d = CumulativeDesigner(cfg)
        rcfg_obj = d.parse_user_config()
        p = os.path.join(base, "runner_config.json")
        d.save_runner_config(rcfg_obj, p)
    rcfg = json.load(open(p, encoding="utf-8"))
    out = tempfile.mkdtemp(dir=BASE)
    rcfg["project"]["output_dir"] = out
    r = CumulativeScenarioRunner.__new__(CumulativeScenarioRunner)
    r.config, r.output_dir, r.run_id, r.input_dir = rcfg, out, "t", "/tmp"
    r._get_prev_run_dir = lambda doe, step: None
    r._build_preserve_block = lambda: ""
    step = next(s for s in rcfg["scenario"]["steps"] if s["mode"] == "IMPACT")
    with contextlib.redirect_stdout(io.StringIO()):
        txt = Path(r._create_step_config(1, step)).read_text(encoding="utf-8")
    return dict(ln.split(",", 1) for ln in txt.splitlines() if "," in ln and not ln.startswith("*"))


ex = json.load(open(ROOT / "Examples/scenario_examples/impact_example.json", encoding="utf-8"))
kv = impact_kv(ex)
check("공식 예제(mesh_size 1·dimension_damper [1,1,1]) — 그대로 넘긴다",
      kv.get("MeshSize") == "1" and kv.get("DimensionDamper") == "1,1,1", f"{kv.get('MeshSize')} {kv.get('DimensionDamper')}")
ex2 = copy.deepcopy(ex)
ex2["simulation_params"]["impact"].pop("mesh_size")
ex2["simulation_params"]["impact"].pop("dimension_damper")
kv = impact_kv(ex2)
check("둘 다 빼면 줄을 쓰지 않는다(KMM 이 단위계에 맞춰 정함)", "MeshSize" not in kv and "DimensionDamper" not in kv,
      f"{kv.get('MeshSize')} {kv.get('DimensionDamper')}")
ex3 = copy.deepcopy(ex)
ex3["simulation_params"]["impact"].update({"mesh_size": 0.001, "dimension_damper": [0.001, 0.001, 0.001]})
kv = impact_kv(ex3)
check("SI 값을 직접 준 시나리오 — 그대로", kv.get("MeshSize") == "0.001" and kv.get("DimensionDamper") == "0.001,0.001,0.001",
      f"{kv.get('MeshSize')} {kv.get('DimensionDamper')}")

print()
if FAILS:
    print(f"FAIL {len(FAILS)}건 — 실행 폴더를 남긴다: {BASE}")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
shutil.rmtree(BASE)
print("ALL PASS")
