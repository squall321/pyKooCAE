# 열-낙하 양방향 체인 회귀 시험 — THERM 덱 카드 구성·dynain 산출·이월 입구 (LS-DYNA 불필요)
"""
실행: venv312/bin/python tests/test_thermal_chain.py

  [1] 기준선   UniformChamber / ICPower pass1 / ICPower pass2 덱의 카드 구성이 기대대로다
  [2] dynain   구조 pass 는 *INTERFACE_SPRINGBACK_LSDYNA 를 남기고, 열해석 pass1 은 남기지 않는다   (P1)
  [3] 이월     THERM Run 폴더에 DynamicRelaxation/dynaintoinitial.txt 가 있고 KMM 으로 실행 가능하다  (P2)

P1·P2 가 구현되기 전에는 [2]·[3] 이 실패한다 — 그게 이 시험의 목적이다.
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
PY = str(ROOT / "venv312" / "bin" / "python")

# 임시 산출물도 프로젝트 안에 둔다 (/tmp 금지 — 사용자 지시)
WORK = ROOT / "work" / "thermal_chain" / "tmp"
WORK.mkdir(parents=True, exist_ok=True)

FAILS = []


def check(name, cond, detail=""):
    print("  %-68s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def write_model(path):
    """보드(PID 1) + 칩(PID 2) 2층 스택, ton-mm-s"""
    nx, ny, cell = 6, 4, 5.0
    zs = [0.0, 1.0, 1.5]
    idx, nodes, nid = {}, [], 0
    for k, z in enumerate(zs):
        for j in range(ny + 1):
            for i in range(nx + 1):
                nid += 1
                idx[(i, j, k)] = nid
                nodes.append(f"{nid:8d}{i * cell:16.6f}{j * cell:16.6f}{z:16.6f}")
    elems, eid = [], 0
    for k in range(2):
        for j in range(ny):
            for i in range(nx):
                if k == 1 and not (2 <= i <= 3 and 1 <= j <= 2):
                    continue
                eid += 1
                pid = 1 if k == 0 else 2
                c = [idx[(i, j, k)], idx[(i + 1, j, k)], idx[(i + 1, j + 1, k)], idx[(i, j + 1, k)],
                     idx[(i, j, k + 1)], idx[(i + 1, j, k + 1)], idx[(i + 1, j + 1, k + 1)], idx[(i, j + 1, k + 1)]]
                elems.append(f"{eid:8d}{pid:8d}" + "".join(f"{v:8d}" for v in c))
    f10 = lambda *v: "".join(f"{str(x):>10s}" for x in v)  # noqa: E731
    Path(path).write_text("\n".join(
        ["*KEYWORD", "*PART", "Board_FR4", f10(1, 1, 1), "*PART", "Chip_Si", f10(2, 1, 2),
         "*SECTION_SOLID", f10(1, 1),
         "*MAT_ELASTIC", f10(1, "1.9e-9", "24000.0", "0.15"),
         "*MAT_ELASTIC", f10(2, "2.33e-9", "169000.0", "0.28"),
         "*NODE"] + nodes + ["*ELEMENT_SOLID"] + elems + ["*END"]) + "\n")


OPTS = {
    "uniform": """ThermalType,UniformChamber
BaseTempC,25
TargetTempC,-40
RampTimeS,0.002
DT,1e-05
DefaultCTE,1.8e-05
PartCTE
1,1.8e-05
2,2.6e-06
EndPartCTE""",
    "ic1": """ThermalType,ICPower
Phase,thermal
AnalysisType,transient
UnitSystem,SI
InitialTemperatureC,25
DT,1e-05
DefaultCTE,1.8e-05
Materials
1,1900,1200,0.3,1.8e-05
2,2330,700,149.0,2.6e-06
EndMaterials
HeatSources
2,2.0,50.0
EndHeatSources""",
    "ic2": """ThermalType,ICPower
Phase,structural
UnitSystem,SI
InitialTemperatureC,25
RampTimeS,0.002
DT,1e-05
DefaultCTE,1.8e-05
PartCTE
1,1.8e-05
2,2.6e-06
EndPartCTE""",
}


def run_kmm(workdir, optname, body, run_dir_mode=False):
    header = ["*Inputfile", "model.k"]
    if run_dir_mode:
        header += [f"*RunDirectoryMode,True,{workdir}"]
    header += ["*Mode", "THERMAL_LOAD,1", "**ThermalLoad,1", body, "**EndThermalLoad", "*End"]
    Path(workdir, optname).write_text("\n".join(header) + "\n")
    r = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), optname], cwd=workdir,
                       capture_output=True, text=True, timeout=900)
    return r


def cards(path):
    text = Path(path).read_text(errors="replace")
    out = {}
    for m in re.finditer(r"^\*([A-Z_0-9]+)", text, re.M):
        out[m.group(1)] = out.get(m.group(1), 0) + 1
    return out


def make_case(kind, run_dir_mode=False):
    d = tempfile.mkdtemp(prefix=f"thchain_{kind}_", dir=str(WORK))
    write_model(os.path.join(d, "model.k"))
    r = run_kmm(d, "opt.txt", OPTS[kind], run_dir_mode=run_dir_mode)
    return d, r


def main():
    print("[1] 기준선 — 덱 카드 구성")
    decks = {}
    for kind, want, forbid in (
        ("uniform", ["LOAD_THERMAL_VARIABLE", "DEFINE_CURVE_TITLE", "MAT_ADD_THERMAL_EXPANSION"],
                    ["MAT_THERMAL_ISOTROPIC", "LOAD_HEAT_GENERATION_SET_SOLID", "CONTROL_THERMAL_SOLVER"]),
        ("ic1", ["MAT_THERMAL_ISOTROPIC", "INITIAL_TEMPERATURE_SET", "LOAD_HEAT_GENERATION_SET_SOLID",
                 "SET_SOLID_TITLE"], ["LOAD_THERMAL_VARIABLE"]),
        ("ic2", ["LOAD_THERMAL_D3PLOT", "MAT_ADD_THERMAL_EXPANSION"],
                ["LOAD_HEAT_GENERATION_SET_SOLID", "MAT_THERMAL_ISOTROPIC"]),
    ):
        d, r = make_case(kind)
        out = os.path.join(d, "model_therm.k")
        check(f"{kind}: KMM 실행 성공", r.returncode == 0 and os.path.exists(out),
              (r.stdout[-300:] + r.stderr[-300:]))
        if not os.path.exists(out):
            continue
        c = cards(out)
        decks[kind] = (d, out, c)
        for w in want:
            check(f"  {kind}: *{w} 있음", c.get(w, 0) >= 1, str(sorted(c)[:12]))
        for f in forbid:
            check(f"  {kind}: *{f} 없음", c.get(f, 0) == 0, f"{f}={c.get(f)}")
    if "uniform" in decks:
        c = decks["uniform"][2]
        check("  uniform: CTE 카드가 파트 수(2)와 같음", c.get("MAT_ADD_THERMAL_EXPANSION") == 2,
              str(c.get("MAT_ADD_THERMAL_EXPANSION")))

    print("[2] dynain 산출 — *INTERFACE_SPRINGBACK_LSDYNA (P1)")
    for kind, want_springback in (("uniform", True), ("ic2", True), ("ic1", False)):
        if kind not in decks:
            continue
        c = decks[kind][2]
        got = c.get("INTERFACE_SPRINGBACK_LSDYNA", 0)
        if want_springback:
            check(f"  {kind}(구조 pass): springback 카드 1개", got == 1, f"got={got}")
            check(f"  {kind}: 전 파트 SET_PART_LIST 있음",
                  c.get("SET_PART_LIST", 0) + c.get("SET_PART_LIST_TITLE", 0) >= 1, str(c))
        else:
            check(f"  {kind}(열해석 pass1): springback 카드 없음", got == 0, f"got={got}")

    print("[3] 이월 입구 — dynaintoinitial.txt (P2)")
    d, r = make_case("uniform", run_dir_mode=True)
    runs = sorted(Path(d).glob("Run_*"))
    check("RunDirectoryMode 실행 성공", r.returncode == 0 and bool(runs),
          (r.stdout[-300:] + r.stderr[-300:]))
    if runs:
        run = runs[0]
        check("  ThermalSet.k 생성", (run / "ThermalSet.k").exists())
        dti = run / "DynamicRelaxation" / "dynaintoinitial.txt"
        check("  DynamicRelaxation/dynaintoinitial.txt 생성", dti.exists(), str(list((run / 'DynamicRelaxation').glob('*'))))
        if dti.exists():
            body = dti.read_text(errors="replace")
            check("    *Inputfile 이 ThermalSet.k", "ThermalSet.k" in body, body[:200])
            check("    DYNAIN_TO_INITIAL 모드", "DYNAIN_TO_INITIAL" in body)
            check("    *IncludeStress,True", "IncludeStress,True" in body)
            check("    dynain 경로가 Output/dynain", re.search(r"DynainPath,.*Output/dynain", body) is not None,
                  body[:300])

    print("[4] 왕복 중복 없음 — 이월 덱은 초기응력만 늘어난다 (P3a)")
    # dynain 을 합성해 DYNAIN_TO_INITIAL 까지 돌린다 (LS-DYNA 불필요)
    if runs:
        run = runs[0]
        deck = run / "ThermalSet.k"
        nodes, elems, kw = [], [], None
        for line in deck.read_text(errors="replace").splitlines():
            if line.startswith("*"):
                kw = line.strip().upper()
                continue
            if line.startswith("$") or not line.strip():
                continue
            if kw == "*NODE" and len(line) > 55:
                nodes.append(line)
            elif kw and kw.startswith("*ELEMENT_SOLID") and len(line) >= 80:
                elems.append(line)
        out = ["*KEYWORD", "*NODE"]
        for l in nodes:
            try:
                nid = int(l[:8]); x = float(l[8:24]); y = float(l[24:40]); z = float(l[40:56]) * 0.999
            except ValueError:
                continue
            out.append(f"{nid:8d}{x:16.6f}{y:16.6f}{z:16.6f}")
        out.append("*INITIAL_STRESS_SOLID")
        for l in elems[:5]:
            out.append(f"{int(l[:8]):10d}{1:10d}{0:10d}{0:10d}")
            out.append(f"{12.5:10.3f}{3.1:10.3f}{-4.2:10.3f}{0.5:10.3f}{0.2:10.3f}{0.1:10.3f}{0.0:10.3f}{0.0:10.3f}")
        out.append("*END")
        (run / "Output" / "dynain").write_text("\n".join(out) + "\n")
        r2 = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "dynaintoinitial.txt"],
                            cwd=str(run / "DynamicRelaxation"), capture_output=True, text=True, timeout=900)
        dti_deck = run / "Output" / "ThermalSet_dti.k"
        check("DYNAIN_TO_INITIAL 실행 성공", r2.returncode == 0 and dti_deck.exists(),
              (r2.stdout[-300:] + r2.stderr[-300:]))
        if dti_deck.exists():
            before, after = cards(deck), cards(dti_deck)
            check("  초기응력 카드가 이월됨", after.get("INITIAL_STRESS_SOLID", 0) >= 1, str(sorted(after)[:12]))
            dup = {k: (before.get(k), after[k]) for k in after
                   if k != "INITIAL_STRESS_SOLID" and after[k] > before.get(k, 0)}
            check("  왕복으로 늘어난 카드 없음 (미해석 raw 이중 출력 방지)", not dup, str(dup))
            check("  Uninterpreted 헤더가 한 번만", dti_deck.read_text(errors="replace").count(
                "Uninterpreted keywords") <= 1, str(dti_deck.read_text(errors="replace").count("Uninterpreted keywords")))

    print()
    if FAILS:
        print("FAIL %d 건" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
