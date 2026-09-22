# 열-낙하 양방향 체인 회귀 시험 — THERM 덱 카드 구성·dynain 산출·이월 입구 (LS-DYNA 불필요)
"""
실행: venv312/bin/python tests/test_thermal_chain.py

  [1] 기준선   UniformChamber / ICPower pass1 / ICPower pass2 덱의 카드 구성이 기대대로다
  [2] dynain   구조 pass 는 *INTERFACE_SPRINGBACK_LSDYNA 를 남기고, 열해석 pass1 은 남기지 않는다   (P1)
  [3] 이월     THERM Run 폴더에 DynamicRelaxation/dynaintoinitial.txt 가 있고 KMM 으로 실행 가능하다  (P2)
  [4] 중복     왕복(DYNAIN_TO_INITIAL) 후 늘어난 카드가 없다                                    (P3a)
  [5] 양방향   THERM→DROP 은 이월 열하중을 정책대로, DROP→THERM 은 이월 초기속도를 정리한다          (P3b)
  [6] 환경조건  국부 발열과 환경조건(대류·규정온도)을 한 덱에 함께 걸 수 있다                            (P4)
  [7] 프로파일  TempCurveMode(factor|absolute)와 TFinal(dwell) 이 덱에 반영된다                   (P5)

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


DROP_OPT = """*Inputfile
{model}
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,0
EulerPitching,0
EulerYawing,0
Height,50
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
InitialAngularVelocityX,0
InitialAngularVelocityY,0
InitialAngularVelocityZ,0
OffsetDistance,0.05
Density,1.9e-09
YoungsModulus,24000.0
PoissonRatio,0.15
tFinal,0.001
dt,0.0001{extra}
**EndDropAttitude
*End
"""


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

    print("[5] 양방향 이월 정책 (P3b)")
    # (a) THERM → DROP : 열 덱을 낙하 입력으로
    d = tempfile.mkdtemp(prefix="thchain_bidir_", dir=str(WORK))
    write_model(os.path.join(d, "model.k"))
    r = run_kmm(d, "opt_therm.txt", OPTS["uniform"])
    thermed = os.path.join(d, "model_therm.k")
    check("(a) 열 덱 생성", r.returncode == 0 and os.path.exists(thermed), r.stderr[-200:])
    if os.path.exists(thermed):
        c0 = cards(thermed)
        check("  열 덱에 열하중·램프커브 있음",
              c0.get("LOAD_THERMAL_VARIABLE", 0) == 1 and c0.get("DEFINE_CURVE_TITLE", 0) >= 1, str(c0))
        for label, extra, want_load, want_curve in (
                ("stress_only(기본)", "", 0, 0),
                ("hold_temperature", "\nThermalCarry,hold_temperature", 1, 1)):
            Path(d, "opt_drop.txt").write_text(DROP_OPT.format(model="model_therm.k", extra=extra))
            out = os.path.join(d, "model_therm_drop.k")
            if os.path.exists(out):
                os.remove(out)
            r2 = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt_drop.txt"], cwd=d,
                                capture_output=True, text=True, timeout=900)
            check(f"  {label}: 낙하 덱 생성", r2.returncode == 0 and os.path.exists(out),
                  (r2.stdout[-250:] + r2.stderr[-250:]))
            if not os.path.exists(out):
                continue
            c1 = cards(out)
            body = Path(out).read_text(errors="replace")
            check(f"    열하중 {want_load}개", c1.get("LOAD_THERMAL_VARIABLE", 0) == want_load,
                  str(c1.get("LOAD_THERMAL_VARIABLE")))
            check(f"    ThermLoad 램프커브 {want_curve}개", body.count("ThermLoad_temp_curve") == want_curve,
                  str(body.count("ThermLoad_temp_curve")))
            check("    CTE 카드는 그대로 (2개)", c1.get("MAT_ADD_THERMAL_EXPANSION", 0) == 2,
                  str(c1.get("MAT_ADD_THERMAL_EXPANSION")))
            check("    낙하 초기속도 있음", c1.get("INITIAL_VELOCITY", 0) == 1, str(c1.get("INITIAL_VELOCITY")))
            if want_curve:
                # 제목 다음 줄은 커브 헤더(LCID/SIDR/SFA…)이고 그 뒤가 (시간, 값) 점들이다
                seg = body.split("ThermLoad_temp_curve", 1)[1].splitlines()[2:6]
                pts = []
                for ln in seg:
                    f = ln.split()
                    if len(f) == 2 and all(re.match(r"^-?\d+\.\d+e[+-]\d+$", x) for x in f):
                        pts.append(float(f[1]))
                check("    커브가 평탄화됨 (값이 모두 같음)", len(pts) >= 2 and len(set(pts)) == 1, str(pts))

    # (b) DROP → THERM : 낙하 덱을 열 입력으로
    d2 = tempfile.mkdtemp(prefix="thchain_bidir2_", dir=str(WORK))
    write_model(os.path.join(d2, "model.k"))
    Path(d2, "opt_drop.txt").write_text(DROP_OPT.format(model="model.k", extra=""))
    r3 = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt_drop.txt"], cwd=d2,
                        capture_output=True, text=True, timeout=900)
    dropped = os.path.join(d2, "model_drop.k")
    check("(b) 낙하 덱 생성", r3.returncode == 0 and os.path.exists(dropped), r3.stderr[-200:])
    if os.path.exists(dropped):
        cd_ = cards(dropped)
        check("  낙하 덱에 초기속도·springback 있음",
              cd_.get("INITIAL_VELOCITY", 0) == 1 and cd_.get("INTERFACE_SPRINGBACK_LSDYNA", 0) == 1, str(cd_))
        body = OPTS["uniform"]
        Path(d2, "opt_therm.txt").write_text(
            "\n".join(["*Inputfile", "model_drop.k", "*Mode", "THERMAL_LOAD,1", "**ThermalLoad,1",
                        body, "**EndThermalLoad", "*End"]) + "\n")
        r4 = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt_therm.txt"], cwd=d2,
                            capture_output=True, text=True, timeout=900)
        out2 = os.path.join(d2, "model_drop_therm.k")
        check("  열 덱 생성", r4.returncode == 0 and os.path.exists(out2), (r4.stdout[-250:] + r4.stderr[-250:]))
        if os.path.exists(out2):
            c2 = cards(out2)
            check("    이월 초기속도 제거됨", c2.get("INITIAL_VELOCITY", 0) == 0, str(c2.get("INITIAL_VELOCITY")))
            check("    springback 은 1개 (중복 추가 안 함)",
                  c2.get("INTERFACE_SPRINGBACK_LSDYNA", 0) == 1, str(c2.get("INTERFACE_SPRINGBACK_LSDYNA")))
            check("    열하중 적용됨", c2.get("LOAD_THERMAL_VARIABLE", 0) == 1, str(c2.get("LOAD_THERMAL_VARIABLE")))

    print("[6] 환경조건 + 국부 발열 동시 (P4)")
    AMB_CURVE = OPTS["ic1"] + """
Ambient
mode,convection
h,0.025
temp_C,-40
TempCurve
0.0,25.0
1.0,-40.0
30.0,-40.0
EndTempCurve
EndAmbient"""
    AMB_CONST = OPTS["ic1"] + """
Ambient
mode,convection
h,0.025
temp_C,-40
EndAmbient"""
    AMB_TEMP = OPTS["ic1"] + """
Ambient
mode,temperature
temp_C,-40
EndAmbient"""
    for label, body, want in (
            ("대류 + 환경온도 커브", AMB_CURVE, "conv_curve"),
            ("대류 (상수 T∞)", AMB_CONST, "conv_const"),
            ("규정온도", AMB_TEMP, "temp")):
        d3 = tempfile.mkdtemp(prefix="thchain_amb_", dir=str(WORK))
        write_model(os.path.join(d3, "model.k"))
        r5 = run_kmm(d3, "opt.txt", body)
        out3 = os.path.join(d3, "model_therm.k")
        check(f"{label}: 실행 성공", r5.returncode == 0 and os.path.exists(out3),
              (r5.stdout[-300:] + r5.stderr[-300:]))
        if not os.path.exists(out3):
            continue
        c3 = cards(out3)
        text3 = Path(out3).read_text(errors="replace")
        check("  발열 카드 있음 (국부 발열 유지)", c3.get("LOAD_HEAT_GENERATION_SET_SOLID", 0) == 1, str(c3.get("LOAD_HEAT_GENERATION_SET_SOLID")))
        check("  Ambient 경고 없음", "unknown Ambient option" not in r5.stdout, r5.stdout[-200:])
        if want.startswith("conv"):
            check("  *BOUNDARY_CONVECTION_SET 2개 (파트별)", c3.get("BOUNDARY_CONVECTION_SET", 0) == 2, str(c3.get("BOUNDARY_CONVECTION_SET")))
            check("  *SET_SEGMENT 2개", c3.get("SET_SEGMENT_TITLE", 0) + c3.get("SET_SEGMENT", 0) == 2, str(c3))
            # 주석($#)·빈 줄을 빼고 데이터 줄만 — [0]=SSID, [1]=HLCID/HMULT/TLCID/TMULT/LOC
            seg = [ln for ln in text3.split("*BOUNDARY_CONVECTION_SET", 1)[1].splitlines()
                   if ln.strip() and not ln.startswith("$") and not ln.startswith("*")][:2]
            # 🔴 고정폭 카드다 — 공백으로 자르면 "0-4.000e+01" 처럼 붙어 나온다. 10칸씩 자른다
            fields = [seg[1][i:i + 10].strip() for i in range(0, 50, 10)]
            # 포맷 — 검증된 덱(Test_ICThermal) 관례: 필드폭 10 고정, 실수는 %10.3e
            data = seg[1]
            widths = [len(data[i:i + 10]) for i in range(0, len(data.rstrip()), 10)]
            check("    카드 필드폭이 모두 10칸", widths == [10] * 5, str(widths))
            check("    실수 필드가 %10.3e 형식",
                  all(re.match(r"^-?\d\.\d{3}e[+-]\d{2}$", fields[i]) for i in (1, 3)), str(fields))
            check("    SET_SEGMENT solver 가 MECH (검증된 덱 값)", "      MECH" in text3, "MECH 없음")
            if want == "conv_curve":
                check("    커브 지정 시 TLCID != 0 이고 TMULT = 1 (곱수)",
                      len(fields) >= 4 and fields[2] != "0" and float(fields[3]) == 1.0, str(fields))
                check("    환경온도 커브가 절대값으로 들어감 (25 → -40)",
                      "Ambient_temp_curve" in text3 and "2.5000000000000e+01" in text3, "커브 없음")
            else:
                check("    상수 T∞ 는 TLCID = 0, TMULT = T∞",
                      len(fields) >= 4 and fields[2] == "0" and float(fields[3]) == -40.0, str(fields))
        else:
            check("  *BOUNDARY_TEMPERATURE_SET 2개", c3.get("BOUNDARY_TEMPERATURE_SET", 0) == 2, str(c3.get("BOUNDARY_TEMPERATURE_SET")))
            check("  대류 카드는 없음", c3.get("BOUNDARY_CONVECTION_SET", 0) == 0, str(c3.get("BOUNDARY_CONVECTION_SET")))

    # Ambient 미지정 시 아무 것도 추가되지 않는다 (기존 동작 불변)
    d4 = tempfile.mkdtemp(prefix="thchain_noamb_", dir=str(WORK))
    write_model(os.path.join(d4, "model.k"))
    r6 = run_kmm(d4, "opt.txt", OPTS["ic1"])
    out4 = os.path.join(d4, "model_therm.k")
    if os.path.exists(out4):
        c4 = cards(out4)
        check("Ambient 미지정 → 경계조건 카드 0 (기존 동작 불변)",
              c4.get("BOUNDARY_CONVECTION_SET", 0) == 0 and c4.get("BOUNDARY_TEMPERATURE_SET", 0) == 0, str(c4))

    print("[7] 온도 프로파일 — 커브 종축·dwell (P5)")
    PROFILE = """ThermalType,UniformChamber
BaseTempC,25
TargetTempC,-40
RampTimeS,0.002
TFinal,0.01
DT,1e-04
DefaultCTE,1.8e-05
TempCurveMode,absolute
TempCurve
0.0,25.0
0.002,-40.0
0.01,-40.0
EndTempCurve"""
    d5 = tempfile.mkdtemp(prefix="thchain_prof_", dir=str(WORK))
    write_model(os.path.join(d5, "model.k"))
    r7 = run_kmm(d5, "opt.txt", PROFILE)
    out5 = os.path.join(d5, "model_therm.k")
    check("절대온도 커브 + dwell: 실행 성공", r7.returncode == 0 and os.path.exists(out5),
          (r7.stdout[-300:] + r7.stderr[-300:]))
    if os.path.exists(out5):
        text5 = Path(out5).read_text(errors="replace")
        endtim = None
        for i, ln in enumerate(text5.splitlines()):
            if ln.startswith("*CONTROL_TERMINATION"):
                for nxt in text5.splitlines()[i + 1:i + 4]:
                    if nxt.strip() and not nxt.startswith("$"):
                        endtim = nxt[:10].strip()
                        break
                break
        check("  ENDTIM 이 TFinal(0.01)", endtim is not None and abs(float(endtim) - 0.01) < 1e-12, str(endtim))
        check("  절대온도 모드 → T = 0 + 1·f(t) (로그)",
              "T=0.0+1.0" in r7.stdout, [l for l in r7.stdout.splitlines() if "LOAD_THERMAL_VARIABLE" in l][:1])
        check("  커브 점 3개가 절대온도로 (25 → -40 → 유지)",
              text5.count("2.5000000000000e+01") >= 1 and text5.count("-4.0000000000000e+01") >= 2,
              str((text5.count("2.5000000000000e+01"), text5.count("-4.0000000000000e+01"))))
    # factor 모드(기본)는 기존 동작 — ts=ΔT, tb=base
    d6 = tempfile.mkdtemp(prefix="thchain_prof2_", dir=str(WORK))
    write_model(os.path.join(d6, "model.k"))
    r8 = run_kmm(d6, "opt.txt", OPTS["uniform"])
    check("factor 모드(기본): ts=ΔT·tb=base 유지 (기존 동작)",
          r8.returncode == 0 and "T=25.0+-65.0" in r8.stdout,
          [l for l in r8.stdout.splitlines() if "LOAD_THERMAL_VARIABLE" in l][:1])
    if os.path.exists(os.path.join(d6, "model_therm.k")):
        t6 = Path(os.path.join(d6, "model_therm.k")).read_text(errors="replace")
        for i, ln in enumerate(t6.splitlines()):
            if ln.startswith("*CONTROL_TERMINATION"):
                for nxt in t6.splitlines()[i + 1:i + 4]:
                    if nxt.strip() and not nxt.startswith("$"):
                        check("  TFinal 미지정 → ENDTIM = RampTimeS(0.002)",
                              abs(float(nxt[:10]) - 0.002) < 1e-12, nxt[:10])
                        break
                break

    print()
    if FAILS:
        print("FAIL %d 건" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
