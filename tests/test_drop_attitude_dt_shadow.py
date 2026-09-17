# DROP_ATTITUDE 옵션의 'dt' 키가 이름에 dt 가 든 다른 키를 삼키지 않는지 검증하는 회귀 시험
"""
KMM ImportOption 의 **DropAttitude 블록은 `"dt" in line.lower()` 부분 문자열로 d3plot 간격을
읽었다. 이 분기가 RigidifySmallDtThreshold / DropContact.DTSTIF / DropContact.DTPCHK 분기보다
앞에 있어서, 러너(StepConfigBuilder)가 dt 뒤에 이 줄들을 쓰면
  - DT 가 마지막 줄 값으로 덮어써지고
  - 원래 키는 조용히 버려졌다(작은 dt 강체화 미적용, 바닥판 접촉 DTSTIF 미적용).

실행: venv312/bin/python tests/test_drop_attitude_dt_shadow.py
"""
import contextlib
import io
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "occProject" / "Generators"))

from Runner.StepConfigBuilder import build_drop_attitude_config  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print("  %-64s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def parse(text):
    d = tempfile.mkdtemp(prefix="dropdt_")
    Path(d, "opt.txt").write_text(text)
    with contextlib.redirect_stdout(io.StringIO()):
        import KooMeshModifier as K
        g = K.KooMeshModifier()
        g.SetCurrentDirectory(d)
        g.ImportOption("opt.txt")
    return g.modeIDOption


def build(sim_params):
    return build_drop_attitude_config(
        model_file="model.k", output_dir="/tmp", project="P", doe_index=1, step_num=1,
        mode="DROP", condition="c", euler={"roll": 0, "pitch": 0, "yaw": 0},
        sim_params=sim_params, run_directory_mode=False)


def main():
    print("[1] 러너 출력 → 파서: dt 뒤에 dt 포함 키들이 올 때")
    sp = {"tFinal": 0.001, "dt": 1e-5,
          "rigidify_small_dt_threshold": 1e-7,
          "drop_contact": {"DTSTIF": 3e-8, "DTPCHK": 2e-8, "SOFT": 2}}
    text = build(sp)
    check("러너가 dt 뒤에 RigidifySmallDtThreshold 를 씀",
          text.index("\ndt,") < text.index("RigidifySmallDtThreshold,"))
    o = parse(text)[1]
    check("DT = 1e-5 (덮어써지지 않음)", o.get("DT") == 1e-5, str(o.get("DT")))
    check("RigidifySmallDtThreshold = 1e-7", o.get("RigidifySmallDtThreshold") == 1e-7,
          str(o.get("RigidifySmallDtThreshold")))
    dc = o.get("DropContact", {})
    check("DropContact.DTSTIF = 3e-8", dc.get("DTSTIF") == 3e-8, str(dc))
    check("DropContact.DTPCHK = 2e-8", dc.get("DTPCHK") == 2e-8, str(dc))
    check("DropContact.SOFT = 2", dc.get("SOFT") == 2, str(dc))

    print("[2] 기존 입력 회귀: dt 만 있을 때, DTMIN·ControlTimestep 와 함께일 때")
    o = parse(build({"tFinal": 0.002, "dt": 4e-5}))[1]
    check("DT = 4e-5", o.get("DT") == 4e-5, str(o.get("DT")))
    check("TFinal = 0.002", o.get("TFinal") == 0.002, str(o.get("TFinal")))
    check("RigidifySmallDtThreshold 미설정", o.get("RigidifySmallDtThreshold") in (None, 0, 0.0),
          str(o.get("RigidifySmallDtThreshold")))
    text = build({"tFinal": 0.002, "dt": 4e-5, "dtmin": 0.01,
                  "control_timestep": {"DT2MS": -1e-7}})
    o = parse(text)[1]
    check("DT = 4e-5 (DTMIN·DT2MS 동반)", o.get("DT") == 4e-5, str(o.get("DT")))
    check("러너가 DTMIN 줄을 씀", "dtmin," in text.lower())
    if "dtmin," in text.lower():
        check("DTMIN = 0.01", o.get("DTMIN") == 0.01, str(o.get("DTMIN")))

    print("[3] 대소문자·공백 변형: 'DT , 1e-5'")
    base = build({"tFinal": 0.001, "dt": 9e-6})
    o = parse(base.replace("\ndt,9e-06", "\nDT ,9e-06"))[1]
    check("DT = 9e-6 (대문자·공백)", o.get("DT") == 9e-6, str(o.get("DT")))

    print()
    if FAILS:
        print("FAIL %d 건" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
