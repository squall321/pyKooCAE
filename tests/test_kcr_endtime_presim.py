# KooChainRun 의 강체 낙하 사전 해석 연결(simulation_params.endtime_presim)을 가짜 KMM 으로 끝까지 검증하는 시험
"""
실행: venv312/bin/python tests/test_kcr_endtime_presim.py      (가짜 KMM·prepare 십여 번, 수십 초)

  [0] 꺼짐 회귀 — 옵션이 없으면 runner_config·누적 러너·대규모·배치 설정이 바꾸기 전 코드와 바이트까지 같다
      (정답 sha256 은 기능을 넣기 전 코드로 뽑아 박았다. 임시 폴더 경로만 <TMP> 로 바꿔 잰다)
      enabled=false(+모르는 키)도 스텝 설정은 같고, 모르는 키는 경고만 한다
  [1] 순수 함수 — DROP 각도 모으기(열 스텝 제외·값 중복 제거·이름), 낙하 방향 규약(KooEndTimeTable 과 대조),
      옵션 값 검사, KMM 옵션 파일 글, endtime_table_for_step
  [2] 켬 + 가짜 KMM — angles.csv·옵션 파일·호출 형식(작업 폴더를 둘째 인자로)·runner_config 기록(endtime_tables·doe_endtim)
      가짜 KMM 은 진짜처럼 템플릿 폴더로 chdir 한 뒤 작업 폴더에 표를 쓴다 — 산출물이 템플릿 옆에 생기면 안 된다
  [3] 세 경로 EndTimeTable 줄 — 누적 러너·대규모·배치. 켠 출력 = 끈 출력 + tFinal 바로 뒤 한 줄. THERM 스텝은 줄 없음
  [4] table 지름길 — KMM 을 돌리지 않고, 다른 오일러 표기·같은 방향 줄 여럿(최대)을 낙하 방향으로 찾는다
  [5] 실패 — KMM rc≠0·각도 빠짐·표 없음(지난 표 재사용 금지)·endtim≤0·시간 초과·실행 파일 없음·table 없음·
      table 각도 빠짐·옵션 값 오류 → `KooChainRun prepare` 비정상 종료 + [ENDTIME_PRESIM_FAILED] + 한글 이유, runner_config 없음
  [6] apptainer 감싸기 명령 형식 (실행하지 않고 subprocess.run 을 가로채 본다)
"""
import contextlib
import copy
import csv
import glob
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import logging
import math
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
sys.path.insert(0, str(ROOT))

FAILS = []
MARK = "[ENDTIME_PRESIM_FAILED]"

# 기능을 넣기 전 코드(cf06055)로 뽑은 정답 — [0] 꺼짐 회귀
GOLDEN = {
    "runner_config": "02d658d4a3d7b676a6848f1034d277e1975fc94f2d99bcd750059bb53c03d343",
    "cumulative": "afb0f463251e32f514c4483514af5bb7399cd37cae28caf5a10d0052371ab8ac",
    "large_scale": "dffb221e4010772a241f332ae94ddaa93227718dcd3cc8b9c4c743bf41d7cc69",
    "batch": "8941ba5329649f48457f1d0adfb046e579a5beff6830723711ff6d12f13dcd42",
}

# 가짜 KMM — 옵션 파일을 읽고, 진짜 KMM 처럼 템플릿 폴더로 chdir 한 뒤, 작업 폴더(둘째 인자)에 계약 모듈로 표를 쓴다
FAKE_KMM = r'''#!{py}
# 가짜 KMM — RIGID_DROP_ENDTIME 옵션 파일을 읽고 작업 폴더에 <base>_endtime.csv 를 계약 모듈로 쓴다 (물리 없음)
import csv, json, os, sys, time
sys.path.insert(0, {gen!r})
from KooCAEManager.KooEndTimeTable import write_endtime_table, drop_direction
MODE = {mode!r}
start_cwd = os.getcwd()
opt, work = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else os.path.curdir)
lines = [l.rstrip("\n") for l in open(os.path.join(work, opt), encoding="utf-8")]
template = lines[lines.index("*Inputfile") + 1]
kv = dict(l.split(",", 1) for l in lines if "," in l and not l.startswith("*"))
os.chdir(os.path.dirname(template))   # 진짜 KMM 처럼 덱 폴더로 chdir — work 가 '.' 이면 산출물이 템플릿 옆으로 간다
with open(os.path.join(work, "fake_kmm_call.json"), "w", encoding="utf-8") as f:
    json.dump({{"argv": sys.argv, "cwd": start_cwd, "mode": MODE}}, f)
print("fake KMM", MODE)
if MODE == "rc1":
    print("가짜 실패"); sys.exit(1)
if MODE == "sleep":
    time.sleep(60)
if MODE == "nooutput":
    sys.exit(0)
angles = list(csv.DictReader(open(kv["AngleFile"], encoding="utf-8")))
if MODE == "missing":
    angles = angles[1:]
rows = []
for i, a in enumerate(angles):
    d = drop_direction(a["roll"], a["pitch"], a["yaw"])
    endtim = 0.0 if (MODE == "zero" and i == 0) else round(0.002 + 0.0005 * i, 6)
    rows.append({{"name": a["name"], "roll": float(a["roll"]), "pitch": float(a["pitch"]), "yaw": float(a["yaw"]),
                 "dx": float(d[0]), "dy": float(d[1]), "dz": float(d[2]), "class": "slapdown", "t1_end_ms": 1.0,
                 "t2_start_ms": 2.0, "t2_end_ms": endtim * 1000 - 1.0, "tfinal_ms": endtim * 1000, "endtim": endtim,
                 "governing_e": 0.3}})
base = os.path.splitext(os.path.basename(template))[0]
write_endtime_table(os.path.join(work, base + "_endtime.csv"), rows,
                    {{"deck": template, "units": "mm-t-s", "time_unit": "s", "height": kv["Height"],
                     "restitution": kv["Restitution"], "friction": kv["Friction"], "gravity": kv["PresimGravity"],
                     "margin_ms": kv["MarginMs"]}})
'''


def check(name, cond, detail=""):
    print("  %-70s %s" % (name[:70], "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def write_fake(tmp, mode="ok"):
    p = os.path.join(tmp, f"fake_kmm_{mode}.py")
    Path(p).write_text(FAKE_KMM.format(py=sys.executable, gen=str(GEN), mode=mode), encoding="utf-8")
    os.chmod(p, 0o755)
    return p


def new_tmp(prefix):
    tmp = tempfile.mkdtemp(prefix=prefix)
    Path(tmp, "model.k").write_text("*KEYWORD\n*END\n", encoding="utf-8")
    return tmp


def scen_faces2(tmp):
    """육면 6 자세 × 2 스텝(cyclic) — 경로마다 바뀌지 않는 값만 쓴다."""
    return {
        "project_name": "EtpReg",
        "base_dir": tmp,
        "environment": {"koomeshmodifier_path": "/opt/x/bin/KooMeshModifier",
                        "kooremapper_path": "/opt/x/bin/KooRemapper",
                        "lsdyna_path": "/opt/x/ls-dyna"},
        "simulation_params": {"height": 1000, "tFinal": 0.004, "dt": 1e-05, "density": 7.85e-09,
                              "youngs_modulus": 200000.0, "poisson_ratio": 0.3,
                              "drop_surface": {"type": "Plane", "size": [200, 200, 20], "mesh": [20, 20, 2]}},
        "scenarios": [{"scenario_name": "Faces2", "template": "model.k",
                       "angle_source": {"source_type": "cuboid_geometry",
                                        "cuboid_geometry": {"include_faces": True, "include_edges": False,
                                                            "include_corners": False}},
                       "cumulative": {"num_steps": 2, "mode_sequence": ["DROP", "DROP"],
                                      "angle_mixing": {"strategy": "cyclic"}}}],
    }


def scen_therm_drop(tmp):
    """열 1 스텝(각도 0/0/0) → 낙하 1 스텝(피보나치 3) — 열 스텝 각도는 사전 해석에서 빠져야 한다."""
    d = scen_faces2(tmp)
    d["project_name"] = "EtpThermDrop"
    d["simulation_params"]["thermal"] = {"thermal_type": "UniformChamber", "base_temp_C": 25, "target_temp_C": 85}
    d["scenarios"] = [{"scenario_name": "HotDrop", "template": "model.k", "thermal_conditions": ["HOT85"],
                       "angle_source": {"source_type": "fibonacci_lattice", "fibonacci_lattice": {"num_points": 3}},
                       "cumulative": {"num_steps": 2, "mode_sequence": ["THERM", "DROP"]}}]
    return d


def with_presim(user, presim, **env):
    user["simulation_params"]["endtime_presim"] = presim
    user["environment"].update(env)
    return user


def designer_prepare(tmp, user):
    """prepare 의 Designer 부분을 그대로 돈다 → (runner_config dict, 화면 출력)."""
    from Runner.CumulativeDesigner import CumulativeDesigner
    rc_path = os.path.join(tmp, "runner_config.json")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        des = CumulativeDesigner(copy.deepcopy(user), scenario_dir=tmp)
        des.save_runner_config(des.parse_user_config(), rc_path)
    return json.load(open(rc_path, encoding="utf-8")), buf.getvalue()


def cli_prepare(tmp, user):
    """KooChainRun prepare 를 실제 명령으로 → (종료 코드, 출력)."""
    Path(tmp, "scenario.json").write_text(json.dumps(user, ensure_ascii=False, indent=2), encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "KooChainRun"), "prepare", "scenario.json"], cwd=tmp,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    return r.returncode, r.stdout + r.stderr


def runner_step_configs(rc):
    """누적 러너 _create_step_config — 러너는 __new__ 로 만들고 config·output_dir·run_id·input_dir 만 준다."""
    from Runner.CumulativeScenarioRunner import CumulativeScenarioRunner
    out = rc["project"]["output_dir"]
    os.makedirs(out, exist_ok=True)
    r = CumulativeScenarioRunner.__new__(CumulativeScenarioRunner)
    r.config, r.output_dir, r.run_id, r.input_dir = rc, out, "t", os.path.dirname(out)
    r._get_prev_run_dir = lambda doe, step: None
    files = {}
    logging.disable(logging.CRITICAL)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            for doe in range(1, int(rc["scenario"]["doe_count"]) + 1):
                for st in rc["scenario"]["steps"]:
                    p = r._create_step_config(doe, st)
                    files[os.path.basename(p)] = Path(p).read_text(encoding="utf-8")
    finally:
        logging.disable(logging.NOTSET)
    return files


def large_scale_configs(rc_path, root):
    """LargeScaleDOEManager.create_runid_directory 가 쓰는 step_config.txt·dynaintoinitial.txt."""
    from Runner.LargeScaleDOEManager import LargeScaleDOEManager
    with contextlib.redirect_stdout(io.StringIO()):
        m = LargeScaleDOEManager(rc_path, data_root=root)
        for sc in m.scenarios:
            for st in sc["steps"]:
                m.create_runid_directory(sc["scenario_id"], st["step_number"], st["doe_index"],
                                         {"angle": st["angle"], "template": st["template"]})
    return {os.path.relpath(p, root): Path(p).read_text(encoding="utf-8")
            for p in sorted(glob.glob(os.path.join(root, "**", "*.txt"), recursive=True))}


def load_kcr():
    loader = importlib.machinery.SourceFileLoader("kcr_script", str(ROOT / "KooChainRun"))
    spec = importlib.util.spec_from_loader("kcr_script", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def batch_config(kcr, rc):
    """KooChainRun _prepare_batch_koomeshmodifier 가 쓰는 batch_config.txt (Fast DOE 한 파일)."""
    with contextlib.redirect_stdout(io.StringIO()):
        pdir, cmd = kcr._prepare_batch_koomeshmodifier(rc, rc["project"]["output_dir"], rc.get("environment", {}))
    return Path(pdir, "batch_config.txt").read_text(encoding="utf-8"), cmd


def digest(tmp, texts):
    """{이름: 글} → 임시 경로를 <TMP> 로 바꾼 뒤 이름 순으로 이어 sha256."""
    h = hashlib.sha256()
    for k in sorted(texts):
        h.update(k.encode("utf-8") + b"\0" + texts[k].replace(tmp, "<TMP>").encode("utf-8") + b"\0")
    return h.hexdigest()


def all_artifacts(kcr, tmp, user):
    """prepare → (runner_config, 화면 출력, runner_config 글, 누적, 대규모, 배치)."""
    rc, out = designer_prepare(tmp, user)
    rc_text = Path(tmp, "runner_config.json").read_text(encoding="utf-8")
    cum = runner_step_configs(rc)
    ls = large_scale_configs(os.path.join(tmp, "runner_config.json"), os.path.join(tmp, "ls_root"))
    bat, _ = batch_config(kcr, rc)
    return rc, out, rc_text, cum, ls, bat


def digests(tmp, rc_text, cum, ls, bat):
    return {"runner_config": digest(tmp, {"rc": rc_text}), "cumulative": digest(tmp, cum),
            "large_scale": digest(tmp, ls), "batch": digest(tmp, {"batch": bat})}


# ── [0] 꺼짐 회귀 ───────────────────────────────────────────────
def test_disabled(kcr):
    print("[0] 꺼짐 회귀 — 바꾸기 전 코드와 바이트 비교")
    tmp = new_tmp("etp_off_")
    rc, _, rc_text, cum, ls, bat = all_artifacts(kcr, tmp, scen_faces2(tmp))
    for k, v in digests(tmp, rc_text, cum, ls, bat).items():
        check(f"{k} sha256 == 바꾸기 전", GOLDEN[k] == v, f"{v} != {GOLDEN[k]}")
    every = (rc_text + "".join(cum.values()) + "".join(ls.values()) + bat).replace(tmp, "<TMP>")
    check("어디에도 EndTimeTable 줄·endtime_tables·doe_endtim 키 없음",
          "EndTimeTable" not in every and '"endtime_tables"' not in every and '"doe_endtim"' not in every)
    check(f"누적 {len(cum)}·대규모 {len(ls)} 설정 생성", len(cum) == 12 and len(ls) == 18, f"{len(cum)} {len(ls)}")

    tmp2 = new_tmp("etp_false_")
    rc2, out2, rc_text2, cum2, ls2, bat2 = all_artifacts(
        kcr, tmp2, with_presim(scen_faces2(tmp2), {"enabled": False, "bogus_key": 1}))
    d2 = digests(tmp2, rc_text2, cum2, ls2, bat2)
    check("enabled=false: 누적·대규모·배치 설정이 바꾸기 전과 같다",
          all(d2[k] == GOLDEN[k] for k in ("cumulative", "large_scale", "batch")), str(d2))
    check("enabled=false: runner_config 에 endtime_tables·doe_endtim 없음",
          "endtime_tables" not in rc2["scenario"] and "doe_endtim" not in rc2["scenario"])
    check("enabled=false: 사전 해석 폴더 없음", not os.path.exists(os.path.join(tmp2, "output", "endtime_presim")))
    check("모르는 키는 경고만 (bogus_key)", "bogus_key" in out2 and "모르는 키" in out2, out2[-300:])
    return rc, tmp, cum, ls, bat


# ── [1] 순수 함수 ───────────────────────────────────────────────
def test_pure():
    print("[1] 순수 함수 — 각도 모으기·방향 규약·옵션 검사·옵션 파일")
    import Runner.EndTimePresim as EP
    from Runner.AngleSourceParser import _physical_drop_dir
    sys.path.insert(0, str(GEN))
    from KooCAEManager.KooEndTimeTable import drop_direction as contract_dir

    steps = [{"step": 1, "mode": "THERM"}, {"step": 2, "mode": "DROP"}, {"step": 3, "mode": "DROP"}]
    doe_angles = {
        "2": {1: {"angle_name": "HOT", "roll": 0.0, "pitch": 0.0, "yaw": 0.0},
              2: {"angle_name": "HOT__P0002", "roll": 30.0, "pitch": -132.49, "yaw": 0.0},
              3: {"angle_name": "a b,c", "roll": 5.0, "pitch": 6.0, "yaw": 7.0}},
        "1": {"1": {"angle_name": "HOT", "roll": 0.0, "pitch": 0.0, "yaw": 0.0},
              "2": {"angle_name": "HOT__P0001", "roll": -30.0, "pitch": 90.0, "yaw": 0.0},
              "3": {"angle_name": "HOT__P0002", "roll": 30.0, "pitch": -132.49, "yaw": 0.0}},
        "10": {"2": {"angle_name": "HOT__P0001", "roll": 1.0, "pitch": 2.0, "yaw": 3.0}},
    }
    got = EP.collect_drop_angles(doe_angles, steps)
    check("DROP 스텝만 — 열 스텝 0/0/0 은 빠진다", (0.0, 0.0, 0.0) not in [g[1:] for g in got], str(got))
    check("값으로 중복 제거 + DOE·스텝 순서 (1→2→10)",
          [g[1:] for g in got] == [(-30.0, 90.0, 0.0), (30.0, -132.49, 0.0), (5.0, 6.0, 7.0), (1.0, 2.0, 3.0)], str(got))
    check("이름: 처음 나온 DOE 이름, 안전한 글자, 겹치면 _2",
          [g[0] for g in got] == ["HOT__P0001", "HOT__P0002", "a_b_c", "HOT__P0001_2"], str(got))

    rnd = random.Random(7)
    worst = 0.0
    for _ in range(300):
        r, p, y = rnd.uniform(-180, 180), rnd.uniform(-180, 180), rnd.uniform(-180, 180)
        a, b = EP.drop_direction(r, p, y), contract_dir(r, p, y)
        worst = max(worst, max(abs(a[i] - float(b[i])) for i in range(3)))
    check(f"낙하 방향 = KooEndTimeTable.drop_direction (최대 차 {worst:.1e})", worst < 1e-12)
    check("AngleSourceParser._physical_drop_dir 와 같은 식 (yaw=0)", all(
        abs(u - v) < 1e-12 for u, v in zip(EP.drop_direction(-30, 90), _physical_drop_dir(-30, 90))))
    rows = [{"name": "A", "roll": 0.0, "pitch": 0.0, "yaw": 0.0, "endtim": 0.003},
            {"name": "B", "roll": 0.0, "pitch": 0.0, "yaw": 45.0, "endtim": 0.007},
            {"name": "C", "roll": 0.0, "pitch": 0.02, "yaw": 0.0, "endtim": 0.009}]
    for r in rows:
        r["dir"] = EP.drop_direction(r["roll"], r["pitch"], r["yaw"])
    check("같은 방향 여럿이면 endtim 최대 (yaw 만 다른 평면 낙하)", EP.find_endtim(rows, 0, 0, 90) == 0.007)
    check("0.01° 밖(0.02°)은 안 잡힌다 / 0.005° 는 잡힌다",
          EP.find_endtim(rows[2:], 0, 0, 0) is None and EP.find_endtim(rows[2:], 0, 0.015, 0) == 0.009)

    check("옵션 없음 → None", EP.presim_options({}) is None and EP.presim_options(None) is None)
    check("enabled=false → None", EP.presim_options({"endtime_presim": {"enabled": False}}) is None)
    o = EP.presim_options({"endtime_presim": True})
    check("true 는 기본값으로 켬", o == {**EP.DEFAULTS, "enabled": True}, str(o))
    o = EP.presim_options({"endtime_presim": {"enabled": True, "restitution": 0.3, "exclude_parts": 23}})
    check("숫자 하나도 목록으로 (restitution·exclude_parts)", o["restitution"] == [0.3] and o["exclude_parts"] == [23])
    bad = [{"enabled": "true"}, {"enabled": True, "restitution": [1.5]}, {"enabled": True, "restitution": []},
           {"enabled": True, "friction": -1}, {"enabled": True, "workers": 0}, {"enabled": True, "gravity": 1},
           {"enabled": True, "exclude_parts": ["23"]}, {"enabled": True, "table": ""}, [1]]
    nbad = 0
    for b in bad:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                EP.presim_options({"endtime_presim": b})
        except EP.EndTimePresimError as e:
            nbad += MARK in str(e) and "bad value" in str(e)
    check(f"잘못된 값 {len(bad)}가지 → 표식 붙은 오류", nbad == len(bad), f"{nbad}/{len(bad)}")

    opts = {**EP.DEFAULTS, "enabled": True, "exclude_parts": [23, 24]}
    text = EP.build_option_text("/m/Deck.k", "/w/angles.csv", 1500, opts)
    want = ("*Inputfile\n/m/Deck.k\n*Mode\nRIGID_DROP_ENDTIME,1\n**RigidDropEndtime,1\nHeight,1500\n"
            "AngleFile,/w/angles.csv\nRestitution,0.1,0.3,0.5\nFriction,0.5\nPresimGravity,0\nMarginMs,1.0\n"
            "ExcludePart,23,24\nWorkers,8\n**EndRigidDropEndtime\n*End\n")
    check("KMM 옵션 파일 글 (계약 §1 그대로)", text == want, repr(text))
    text = EP.build_option_text("/m/Deck.k", "/w/angles.csv", 800.0,
                                {**opts, "exclude_parts": [], "gravity": True, "workers": 2})
    check("ExcludePart 는 줄 때만 · PresimGravity,1(켬)", "ExcludePart" not in text and "PresimGravity,1\n" in text
          and "Height,800.0\n" in text and "Workers,2\n" in text)
    check("블록 안 빈 줄 없음 (KMM 은 빈 줄에서 블록을 끝낸다)", "\n\n" not in text)

    cfg = {"scenario": {"steps": [{"step": 1, "mode": "THERM"}, {"step": 2, "mode": "DROP"}],
                        "endtime_tables": [{"template": "/m.k", "table": "/t/m_endtime.csv"}]}}
    check("endtime_table_for_step: DROP 스텝 → 표 경로", EP.endtime_table_for_step(cfg, 2) == "/t/m_endtime.csv")
    check("endtime_table_for_step: THERM 스텝·없는 스텝 → None",
          EP.endtime_table_for_step(cfg, 1) is None and EP.endtime_table_for_step(cfg, "9") is None)
    check("endtime_table_for_step: 표 없음 → None", EP.endtime_table_for_step({"scenario": {"steps": cfg["scenario"]["steps"]}}, 2)
          is None and EP.endtime_table_for_step({}, 1) is None)


# ── [2] 켬 + 가짜 KMM ───────────────────────────────────────────
def read_angles_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [(r["name"], float(r["roll"]), float(r["pitch"]), float(r["yaw"])) for r in csv.DictReader(f)]


def expected_doe_endtim(rc, angles):
    """가짜 KMM 은 angles.csv 의 i 번째 각도에 0.002+0.0005·i 를 준다."""
    by = {a[1:]: round(0.002 + 0.0005 * i, 6) for i, a in enumerate(angles)}
    drop = {s["step"] for s in rc["scenario"]["steps"] if s["mode"] == "DROP"}
    out = {}
    for doe, st in rc["scenario"]["doe_angles"].items():
        for step, a in st.items():
            if int(step) in drop:
                out.setdefault(doe, {})[step] = by[(a["roll"], a["pitch"], a["yaw"])]
    return out


def test_enabled(kcr):
    print("[2] 켬 + 가짜 KMM — angles.csv·옵션 파일·호출·runner_config")
    tmp = new_tmp("etp_on_")
    fake = write_fake(tmp, "ok")
    user = with_presim(scen_faces2(tmp), {"enabled": True, "exclude_parts": [99]}, koomeshmodifier_path=fake)
    rc, out, rc_text, cum, ls, bat = all_artifacts(kcr, tmp, user)
    work = os.path.join(tmp, "output", "endtime_presim", "1")
    table = os.path.join(work, "model_endtime.csv")
    angles = read_angles_csv(os.path.join(work, "angles.csv"))
    doe_vals = {(a["roll"], a["pitch"], a["yaw"]) for st in rc["scenario"]["doe_angles"].values() for a in st.values()}
    check(f"angles.csv: 고유 DROP 각도 {len(angles)}개 = DOE 각도 집합", len(angles) == 6
          and {a[1:] for a in angles} == doe_vals, str(angles))
    check("angles.csv 머리 줄 name,roll,pitch,yaw",
          Path(work, "angles.csv").read_text(encoding="utf-8").splitlines()[0] == "name,roll,pitch,yaw")
    opt = Path(work, "rigid_drop_endtime.txt").read_text(encoding="utf-8")
    want = (f"*Inputfile\n{os.path.join(tmp, 'model.k')}\n*Mode\nRIGID_DROP_ENDTIME,1\n**RigidDropEndtime,1\n"
            f"Height,1000\nAngleFile,{os.path.join(work, 'angles.csv')}\nRestitution,0.1,0.3,0.5\nFriction,0.5\n"
            f"PresimGravity,0\nMarginMs,1.0\nExcludePart,99\nWorkers,8\n**EndRigidDropEndtime\n*End\n")
    check("옵션 파일: 템플릿 절대 경로·높이·AngleFile·기본값·ExcludePart", opt == want, repr(opt))
    call = json.load(open(os.path.join(work, "fake_kmm_call.json"), encoding="utf-8"))
    check("호출: [KMM, 옵션 이름, 작업 폴더 절대 경로] (apptainer 없음)",
          call["argv"] == [fake, "rigid_drop_endtime.txt", work], str(call["argv"]))
    check("호출: cwd = 작업 폴더", os.path.realpath(call["cwd"]) == os.path.realpath(work), call["cwd"])
    check("표가 작업 폴더에 있고 템플릿 옆에는 없다 (chdir 함정)",
          os.path.isfile(table) and not os.path.exists(os.path.join(tmp, "model_endtime.csv")))
    check("KMM 출력은 작업 폴더 kmm_stdout.log", "fake KMM ok" in Path(work, "kmm_stdout.log").read_text(encoding="utf-8"))
    sc = rc["scenario"]
    check("runner_config scenario.endtime_tables",
          sc.get("endtime_tables") == [{"template": os.path.join(tmp, "model.k"), "table": table,
                                        "source": "presim", "angles": 6}], str(sc.get("endtime_tables")))
    check("runner_config scenario.doe_endtim = 표 값 (DOE 6 × 스텝 2)",
          sc.get("doe_endtim") == expected_doe_endtim(rc, angles), str(sc.get("doe_endtim")))
    check("prepare 출력에 표 요약", "각도별 종료 시간 표" in out and "DROP 각도 6개" in out, out[-400:])
    keys = list(sc)
    check("scenario 키 순서: doe_angles 뒤, batch_koomeshmodifier 앞",
          keys.index("doe_angles") < keys.index("endtime_tables") < keys.index("doe_endtim")
          < keys.index("batch_koomeshmodifier"), str(keys))

    tmp2 = new_tmp("etp_on_therm_")
    fake2 = write_fake(tmp2, "ok")
    rc2, _ = designer_prepare(tmp2, with_presim(scen_therm_drop(tmp2), {"enabled": True}, koomeshmodifier_path=fake2))
    work2 = os.path.join(tmp2, "output", "endtime_presim", "1")
    ang2 = read_angles_csv(os.path.join(work2, "angles.csv"))
    check("THERM→DROP: 열 스텝(0/0/0) 빼고 DROP 각도 3개", len(ang2) == 3 and (0.0, 0.0, 0.0) not in [a[1:] for a in ang2],
          str(ang2))
    check("THERM→DROP: doe_endtim 은 DROP 스텝(2)만", all(list(v) == ["2"] for v in rc2["scenario"]["doe_endtim"].values())
          and len(rc2["scenario"]["doe_endtim"]) == 3, str(rc2["scenario"].get("doe_endtim")))
    return rc, tmp, table, cum, ls, bat, rc2, tmp2


# ── [3] 세 경로 EndTimeTable 줄 ─────────────────────────────────
def strip_endtime(text, table):
    return text.replace(f"\nEndTimeTable,{table}", "")


def endtime_line_ok(text, table):
    ls = text.splitlines()
    line = f"EndTimeTable,{table}"
    if text.count("EndTimeTable") != 1 or line not in ls:
        return False
    i = ls.index(line)
    opened = max(j for j, x in enumerate(ls) if x.startswith("**DropAttitude,"))
    return ls[i - 1].startswith("tFinal,") and opened < i < ls.index("**EndDropAttitude")


def test_three_paths(kcr, off, on):
    print("[3] 세 경로 EndTimeTable 줄 — 누적 러너·대규모·배치")
    _, tmp_off, cum_off, ls_off, bat_off = off
    _, tmp_on, table, cum_on, ls_on, bat_on, rc2, tmp2 = on
    norm = lambda t, tmp: t.replace(tmp, "<TMP>")  # noqa: E731
    check(f"누적 러너: DROP 설정 {len(cum_on)}개 모두 tFinal 바로 뒤 한 줄",
          len(cum_on) == 12 and all(endtime_line_ok(t, table) for t in cum_on.values()))
    check("누적 러너: 줄을 빼면 끈 출력과 바이트 같다", sorted(cum_on) == sorted(cum_off) and all(
        norm(strip_endtime(cum_on[k], table), tmp_on) == norm(cum_off[k], tmp_off) for k in cum_off))
    st_cfgs = [v for k, v in ls_on.items() if k.endswith("step_config.txt")]
    check(f"대규모: step_config {len(st_cfgs)}개 모두 한 줄", len(st_cfgs) == 12
          and all(endtime_line_ok(t, table) for t in st_cfgs))
    check("대규모: dynaintoinitial 에는 없음", all("EndTimeTable" not in v for k, v in ls_on.items()
                                                 if k.endswith("dynaintoinitial.txt")))
    check("대규모: 줄을 빼면 끈 출력과 바이트 같다", sorted(ls_on) == sorted(ls_off) and all(
        norm(strip_endtime(ls_on[k], table), tmp_on) == norm(ls_off[k], tmp_off) for k in ls_off))
    check("배치(Fast DOE 한 파일): 한 줄", endtime_line_ok(bat_on, table))
    check("배치: 줄을 빼면 끈 출력과 바이트 같다", norm(strip_endtime(bat_on, table), tmp_on) == norm(bat_off, tmp_off))
    check("tFinal 줄은 그대로 남는다", all("\ntFinal,0.004\n" in strip_endtime(t, table) for t in cum_on.values()))

    table2 = rc2["scenario"]["endtime_tables"][0]["table"]
    cum2 = runner_step_configs(rc2)
    s1 = [v for k, v in cum2.items() if k.endswith("_s001.txt")]
    s2 = [v for k, v in cum2.items() if k.endswith("_s002.txt")]
    check("THERM→DROP 누적: THERM 스텝 설정엔 줄 없음", s1 and all("EndTimeTable" not in t for t in s1))
    check("THERM→DROP 누적: DROP 스텝 설정엔 한 줄", s2 and all(endtime_line_ok(t, table2) for t in s2))
    ls2 = large_scale_configs(os.path.join(tmp2, "runner_config.json"), os.path.join(tmp2, "ls_root"))
    check("THERM→DROP 대규모: Step001 없음 · Step002 한 줄",
          all(("EndTimeTable" in v) == ("Step002" in k) for k, v in ls2.items() if k.endswith("step_config.txt")))


# ── [4] table 지름길 ────────────────────────────────────────────
def test_table_shortcut(kcr, rc_off):
    print("[4] table 지름길 — KMM 없이, 낙하 방향으로 찾기")
    import Runner.EndTimePresim as EP
    sys.path.insert(0, str(GEN))
    from KooCAEManager.KooEndTimeTable import write_endtime_table, drop_direction as contract_dir
    angles = EP.collect_drop_angles(rc_off["scenario"]["doe_angles"], rc_off["scenario"]["steps"])
    tmp = new_tmp("etp_table_")
    os.makedirs(os.path.join(tmp, "tables"))
    rows, want = [], {}
    for i, (name, r, p, y) in enumerate(angles):
        r2, p2, y2 = 180.0 - r, p + 180.0, y   # 다른 오일러 표기, 같은 낙하 방향 (계약 식으로 확인)
        assert max(abs(a - b) for a, b in zip(contract_dir(r, p, y), contract_dir(r2, p2, y2))) < 1e-12
        e = round(0.01 + 0.001 * i, 6)
        rows.append({"name": f"T{i}", "roll": r2, "pitch": p2, "yaw": y2, "endtim": e})
        want[(r, p, y)] = e
    n0, r0, p0, y0 = angles[0]
    rows.append({"name": "DUP", "roll": r0, "pitch": p0, "yaw": y0, "endtim": 0.5})   # 같은 방향 둘 → 최대
    want[(r0, p0, y0)] = 0.5
    path = os.path.join(tmp, "tables", "user_endtime.csv")
    write_endtime_table(path, rows, {"height": 1000, "units": "mm-t-s"})
    differ = sum((r, p, y) != (rw["roll"], rw["pitch"], rw["yaw"]) for (_, r, p, y), rw in zip(angles, rows))
    fake = write_fake(tmp, "rc1")   # 불리면 실패하는 가짜 — 지름길은 KMM 을 부르지 않아야 한다
    rc, out = designer_prepare(tmp, with_presim(scen_faces2(tmp), {"enabled": True, "table": "tables/user_endtime.csv"},
                                                koomeshmodifier_path=fake))
    sc = rc["scenario"]
    check(f"오일러 표기가 다른 줄 {differ}개로 시험", differ == len(angles) == 6, str(differ))
    check("endtime_tables: scenario.json 기준 상대 경로 → 절대, source=table",
          sc.get("endtime_tables") == [{"template": os.path.join(tmp, "model.k"), "table": path,
                                        "source": "table", "angles": 6}], str(sc.get("endtime_tables")))
    got = {(a["roll"], a["pitch"], a["yaw"]): sc["doe_endtim"][d][s]
           for d, st in sc["doe_angles"].items() for s, a in st.items()}
    check("doe_endtim: 방향으로 찾은 값 + 같은 방향 여럿이면 최대", got == want, f"{got} != {want}")
    check("KMM 을 부르지 않았다 (사전 해석 폴더·호출 기록 없음)",
          not os.path.exists(os.path.join(tmp, "output", "endtime_presim")))
    cum = runner_step_configs(rc)
    check("스텝 설정의 EndTimeTable = 사용자 표 경로", all(endtime_line_ok(t, path) for t in cum.values()))
    check("높이가 같으면 경고 없음", "height mismatch" not in out)
    rc3, out3 = designer_prepare(tmp, with_presim(scen_faces2(tmp), {"enabled": True, "table": path},
                                                  koomeshmodifier_path=fake))
    check("절대 경로 table 도 된다", rc3["scenario"]["endtime_tables"][0]["table"] == path)
    u = with_presim(scen_faces2(tmp), {"enabled": True, "table": path}, koomeshmodifier_path=fake)
    u["simulation_params"]["height"] = 1500
    _, out4 = designer_prepare(tmp, u)
    check("표 높이(1000) ≠ simulation_params.height(1500) → 경고", "height mismatch" in out4, out4[-300:])


# ── [5] 실패 ────────────────────────────────────────────────────
def test_failures():
    print("[5] 실패 — prepare 가 멈춘다 (종료 코드·표식·이유·runner_config 없음)")

    def run_case(label, fake_mode, presim, expect, env=None, keep_tmp=None, base=scen_faces2):
        tmp = keep_tmp or new_tmp("etp_fail_")
        fake = write_fake(tmp, fake_mode) if fake_mode else "/nonexistent/bin/KooMeshModifier"
        rc_path = os.path.join(tmp, "runner_config.json")
        if os.path.exists(rc_path):
            os.remove(rc_path)
        user = with_presim(base(tmp), presim, koomeshmodifier_path=fake, **(env or {}))
        code, out = cli_prepare(tmp, user)
        ok = code != 0 and MARK in out and all(e in out for e in expect) and not os.path.exists(rc_path)
        check(f"{label} → 종료 코드 {code}", ok, out[-700:])
        return tmp

    on = {"enabled": True}
    run_case("KMM 종료 코드 1", "rc1", on, ["종료 코드 1", "KMM rc=1", "가짜 실패"])
    run_case("표에 각도 하나 빠짐", "missing", on, ["DROP 각도 1/6개가 없다", "angles missing"])
    run_case("endtim 0", "zero", on, ["endtim 이 양수가 아니다", "endtim must be positive"])
    run_case("시간 초과", "sleep", on, ["초 안에 끝나지 않았다", "timeout"], env={"timeout_koomeshmodifier_seconds": 2})
    run_case("KMM 실행 파일 없음", None, on, ["KMM 을 실행하지 못했다", "cannot run KMM"])
    run_case("table 파일 없음", "rc1", {"enabled": True, "table": "nope.csv"}, ["table 파일이 없다", "table not found"])
    run_case("옵션 값 오류 (restitution 1.5)", "ok", {"enabled": True, "restitution": [1.5]}, ["bad value"])

    tmp = new_tmp("etp_stale_")
    code, out = cli_prepare(tmp, with_presim(scen_faces2(tmp), on, koomeshmodifier_path=write_fake(tmp, "ok")))
    check("정상 prepare (CLI) → 종료 코드 0 + runner_config", code == 0 and os.path.exists(
        os.path.join(tmp, "runner_config.json")), out[-500:])
    run_case("표를 안 쓴 KMM (지난 prepare 표가 남아 있어도)", "nooutput", on, ["표가 없다", "table not written"],
             keep_tmp=tmp)

    ttmp = new_tmp("etp_tbl_miss_")
    Path(ttmp, "t.csv").write_text("# format=x\nname,roll,pitch,yaw,endtim\nA,0,0,0,0.004\n", encoding="utf-8")
    run_case("table 에 각도 빠짐", "rc1", {"enabled": True, "table": "t.csv"}, ["5/6개가 없다", "angles missing"],
             keep_tmp=ttmp)
    Path(ttmp, "t.csv").write_text("name,roll,pitch\nA,0,0\n", encoding="utf-8")
    run_case("table 칸 빠짐 (yaw·endtim)", "rc1", {"enabled": True, "table": "t.csv"}, ["missing columns"],
             keep_tmp=ttmp)


# ── [6] apptainer 감싸기 ────────────────────────────────────────
def test_apptainer():
    print("[6] apptainer 감싸기 명령 (실행 없이 가로채기)")
    import Runner.EndTimePresim as EP
    tmp = new_tmp("etp_apt_")
    env = {"koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
           "apptainer_sif": "/opt/apptainers/SmartTwinPreprocessor.sif", "apptainer_bind": "/data:/data",
           "apptainer_env": {"A": "1"}, "apptainer_tmpdir": os.path.join(tmp, "apt"),
           "timeout_koomeshmodifier_seconds": 77}
    doe_angles = {"1": {"1": {"angle_name": "F1", "roll": 0.0, "pitch": 0.0, "yaw": 0.0}}}
    steps = [{"step": 1, "mode": "DROP"}]
    seen = {}

    def fake_run(cmd, **kw):
        seen.update(cmd=cmd, **kw)
        return subprocess.CompletedProcess(cmd, 3)
    real, old_tmpdir = EP.subprocess.run, os.environ.get("APPTAINER_TMPDIR")
    EP.subprocess.run = fake_run
    err = ""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            EP.prepare_endtime_tables({"height": 800, "endtime_presim": {"enabled": True}}, env,
                                      os.path.join(tmp, "model.k"), os.path.join(tmp, "output"), tmp, doe_angles, steps)
    except EP.EndTimePresimError as e:
        err = str(e)
    finally:
        EP.subprocess.run = real
        if old_tmpdir is None:
            os.environ.pop("APPTAINER_TMPDIR", None)
        else:
            os.environ["APPTAINER_TMPDIR"] = old_tmpdir
    work = os.path.join(tmp, "output", "endtime_presim", "1")
    check("apptainer exec --bind --env <sif> <KMM> <옵션> <작업 폴더>",
          seen.get("cmd") == ["apptainer", "exec", "--bind", "/data:/data", "--env", "A=1",
                              "/opt/apptainers/SmartTwinPreprocessor.sif",
                              "/opt/SmartTwinPreprocessor/bin/KooMeshModifier", "rigid_drop_endtime.txt", work],
          str(seen.get("cmd")))
    check("cwd = 작업 폴더 · 시간 제한 = timeout_koomeshmodifier_seconds",
          seen.get("cwd") == work and seen.get("timeout") == 77, str({k: seen.get(k) for k in ("cwd", "timeout")}))
    check("rc≠0 → 표식 + 종료 코드", MARK in err and "종료 코드 3" in err, err)


def main():
    with contextlib.redirect_stdout(io.StringIO()):
        kcr = load_kcr()
    if "--print-golden" in sys.argv:   # 기능을 넣기 전 코드에서만 의미가 있다
        tmp = new_tmp("etp_gold_")
        _, _, rc_text, cum, ls, bat = all_artifacts(kcr, tmp, scen_faces2(tmp))
        print(json.dumps(digests(tmp, rc_text, cum, ls, bat), indent=1))
        return
    off = test_disabled(kcr)
    test_pure()
    on = test_enabled(kcr)
    test_three_paths(kcr, off, on)
    test_table_shortcut(kcr, off[0])
    test_failures()
    test_apptainer()
    print()
    if FAILS:
        print("FAIL %d:" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
