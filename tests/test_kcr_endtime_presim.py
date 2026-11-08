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
  [6] apptainer 감싸기 명령 형식 (실행하지 않고 subprocess.run 을 가로채 본다) — 사전 해석과 러너 KMM 버전 확인(--help)
  [7] 시간 제한 배율 — ceil(endtim ÷ tFinal): submit(누적·sequential) --time, 러너 스텝 timeout. 표가 없거나 짧으면 그대로
  [8] reach(바닥판 반폭 비교, RigidWall 제외)·n_unresolved 알림, drop_v0 단위 환산
  [9] 수정 묶음 — BOM 표, 표 메타 gravity·deck·mm-kg-ms g, numpy 찾기(옛 식과 같고 2만×2만 < 30 초), presim_timeout_seconds,
      batch_koomeshmodifier 의 호스트 KMM 묻기, 러너 노드 표식 확인, 대규모 배열 --time·스크립트 grep, deep report 배율,
      DOE 배율 F_d(짧은 표 = 예전 step/DR), _hms_scale Slurm 형식
  [10] v133 strong_contact — table 메타 endtime_rule(없음 → v132 경고, 중력 켬 표는 빼고, 대소문자 무관)·last_strong
      strong_contact(상대 1e-9 넘게 다르면 멈춤, 옵션 중력 켬이면 멈춤)·first_recontact(중력 켬은 안 봄, 끔이면 경고)·모르는 규칙, 사전 해석 중력 켬은 v132 와 같은 옵션 파일(줄·RIGID_DROP_ENDTIME 확인 없음)
  ([5] 에 러너 KMM 버전(v131 도움말·도움말 없는 옛 바이너리·table 지름길), KMM rc 3, 표 v0 다름, 시간 초과면 묶음째 죽임,
   사전 해석 KMM 이 PresimStrongContact 를 모름(v132 도움말 — 사전 해석 전에 멈춤)·표 strong_contact 다름,
   [4] 에 표 높이 다름 → 멈춤, [1] 에 strong_contact 옵션 값·PresimStrongContact 줄, [6] 에 --help RIGID_DROP_ENDTIME 감싸기·
   (실행 파일, SIF, 모드) 기억)
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
if sys.argv[1:2] == ["--help"]:   # 러너 KMM 버전 확인 — 부를 때마다 옆 파일에 한 줄 남긴다
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_help_calls.txt"), "a").write(" ".join(sys.argv[1:]) + "\n")
    if MODE == "nohelp":   # 도움말이 없는 옛 바이너리 — '--help' 를 옵션 파일로 읽다 죽는다
        raise FileNotFoundError("DROP_ATTITUDE/--help")
    if sys.argv[2:3] == ["RIGID_DROP_ENDTIME"]:   # 사전 해석 KMM 의 v133 키 확인 — v132help·oldhelp 는 그 키를 모른다
        print("RIGID_DROP_ENDTIME — 가짜 도움말\n  Height  [실수 · 필수]\n  PresimGravity  [0|1 · 기본 0]")
        if MODE not in ("v132help", "oldhelp"):
            print("  PresimStrongContact  [실수 · 기본 0.2]")
        sys.exit(0)
    print("DROP_ATTITUDE — 가짜 도움말\n  Height  [실수]\n  tFinal  [실수]")
    if MODE != "oldhelp":
        print("  EndTimeTable  [경로]\n  RigidAngularVelocityX/Y/Z  [실수 리스트]")
    sys.exit(0)
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
if MODE == "v132help" and "PresimStrongContact" in kv:   # v132 KMM 은 모르는 블록 키에서 죽는다
    print("[RIGID_DROP_ENDTIME] 모르는 키 PresimStrongContact (가짜 v132)"); sys.exit(1)
if MODE == "rc3":
    print("🔴 요소 소실: 읽기에서 요소 12개를 버렸다 (가짜)"); sys.exit(3)
if MODE == "sleep":
    time.sleep(60)
if MODE == "sleepchild":   # 작업자처럼 자식을 띄우고 기다린다 — 시간 초과면 묶음째 죽어야 한다
    import subprocess as sp
    child = sp.Popen(["sleep", "120"])
    open(os.path.join(work, "child.pid"), "w").write(str(child.pid))
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
                 "governing_e": 0.3, "reach": (160.0 if MODE == "farreach" and i == 1 else 10.0 + i),
                 "n_unresolved": (1 if MODE == "farreach" and i in (0, 2) else 0)}})
base = os.path.splitext(os.path.basename(template))[0]
v0 = (2 * 9810.0 * float(kv["Height"])) ** 0.5 * (1.01 if MODE == "badv0" else 1.0)   # E 와 같은 메타 — √(2gh), 덱 단위
meta = {{"deck": template, "units": "mm-t-s", "time_unit": "s", "height": kv["Height"], "v0": v0,
        "restitution": kv["Restitution"], "friction": kv["Friction"], "gravity": kv["PresimGravity"],
        "margin_ms": kv["MarginMs"], "t_sep_ms": 1.0}}
if MODE not in ("v132help", "v132table"):   # v133 KMM 의 규칙 메타 — 중력 끔 last_strong + strong_contact, 켬 first_recontact
    if kv["PresimGravity"] == "1":
        meta["endtime_rule"] = "first_recontact"
    else:
        meta.update(endtime_rule="last_strong",
                    strong_contact="0.5" if MODE == "badstrong" else kv.get("PresimStrongContact", "0.2"))
write_endtime_table(os.path.join(work, base + "_endtime.csv"), rows, meta)
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


def help_calls(tmp):
    """가짜 KMM 이 받은 --help 호출(그 폴더의 fake_help_calls.txt) — ['--help DROP_ATTITUDE', ...]."""
    p = os.path.join(tmp, "fake_help_calls.txt")
    return Path(p).read_text(encoding="utf-8").splitlines() if os.path.exists(p) else []


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

    o = EP.presim_options({"endtime_presim": {"enabled": True}})
    check("strong_contact 기본 0.2", o["strong_contact"] == 0.2 == EP.DEFAULTS["strong_contact"], str(o))
    good_sc = [0.5, 1, 2.0, 1e-6]
    check("strong_contact 0.5·1·2.0·1e-6 → 그대로", all(
        EP.presim_options({"endtime_presim": {"enabled": True, "strong_contact": v}})["strong_contact"] == v for v in good_sc))
    bad_sc = [0, 0.0, -0.1, True, False, "0.3", None, float("nan"), [0.3]]
    nbad = 0
    for v in bad_sc:
        try:
            EP.presim_options({"endtime_presim": {"enabled": True, "strong_contact": v}})
        except EP.EndTimePresimError as e:
            nbad += (MARK in str(e) and "strong_contact 는 0.0 보다 큰 숫자여야 한다" in str(e) and "bad value" in str(e))
    check(f"strong_contact 0·음수·bool·글자·None·nan·목록 {len(bad_sc)}가지 → 값 오류 (0 보다 커야 한다)", nbad == len(bad_sc),
          f"{nbad}/{len(bad_sc)}")
    try:
        EP.presim_options({"endtime_presim": {"enabled": True, "strong_contact": float("inf")}})
        msg = ""
    except EP.EndTimePresimError as e:
        msg = str(e)
    check("strong_contact inf → 값 오류 (유한한 수)", MARK in msg and "유한한 수여야 한다" in msg and "bad value" in msg, msg)
    warn = []
    for extra in ({"strong_contact": 0.5}, {}):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            EP.presim_options({"endtime_presim": {"enabled": True, "gravity": True, **extra}})
        warn.append(buf.getvalue().count("ignored with gravity"))
    check("gravity=true 에 strong_contact 를 주면 경고 한 줄(쓰지 않음), 안 주면 경고 없음", warn == [1, 0], str(warn))

    opts = {**EP.DEFAULTS, "enabled": True, "exclude_parts": [23, 24]}
    text = EP.build_option_text("/m/Deck.k", "/w/angles.csv", 1500, opts)
    want = ("*Inputfile\n/m/Deck.k\n*Mode\nRIGID_DROP_ENDTIME,1\n**RigidDropEndtime,1\nHeight,1500\n"
            "AngleFile,/w/angles.csv\nRestitution,0.1,0.3,0.5\nFriction,0.5\nPresimGravity,0\nMarginMs,1.0\n"
            "ExcludePart,23,24\nWorkers,8\n**EndRigidDropEndtime\n*End\n")
    check("KMM 옵션 파일 글 (계약 §1 그대로)", text == want, repr(text))
    text = EP.build_option_text("/m/Deck.k", "/w/angles.csv", 1500, opts, strong_contact=0.3)
    check("strong_contact 를 주면 PresimGravity 바로 뒤 PresimStrongContact,0.3 한 줄만 더해진다",
          text == want.replace("PresimGravity,0\n", "PresimGravity,0\nPresimStrongContact,0.3\n"), repr(text))
    ic = EP.build_option_text("/m/Deck.k", None, 1000, {**opts, "gravity": True, "exclude_parts": []}, fibonacci=12)
    check("impact_conditions 꼴(Fibonacci, strong_contact 안 줌) → PresimStrongContact 줄 없음",
          "PresimStrongContact" not in ic and "Fibonacci,12\nRestitution" in ic and "PresimGravity,1\nMarginMs" in ic, repr(ic))
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
            f"PresimGravity,0\nPresimStrongContact,0.2\nMarginMs,1.0\nExcludePart,99\nWorkers,8\n**EndRigidDropEndtime\n*End\n")
    check("옵션 파일: 템플릿 절대 경로·높이·AngleFile·기본값(PresimStrongContact,0.2 — 중력 끔)·ExcludePart", opt == want,
          repr(opt))
    check("KMM 에 묻기: --help DROP_ATTITUDE(표 줄) → --help RIGID_DROP_ENDTIME(PresimStrongContact) 각 한 번",
          help_calls(tmp) == ["--help DROP_ATTITUDE", "--help RIGID_DROP_ENDTIME"], str(help_calls(tmp)))
    check("v133 표(endtime_rule=last_strong·strong_contact=0.2) → v132 표 경고·strong_contact 오류 없음",
          "v132 first-recontact table" not in out and "strong_contact" not in out, out[-400:])
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
    try:
        designer_prepare(tmp, u)
        err = ""
    except EP.EndTimePresimError as e:
        err = str(e)
    check("표 높이(1000) ≠ simulation_params.height(1500) → 멈춘다 (table drop mismatch)",
          MARK in err and "table drop mismatch" in err and "높이 1000" in err, err)


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
    t_to = run_case("시간 초과 (presim_timeout_seconds 2)", "sleepchild", {"enabled": True, "presim_timeout_seconds": 2},
                    ["초 안에 끝나지 않았다", "presim_timeout_seconds", "timeout"])
    pid_file = os.path.join(t_to, "output", "endtime_presim", "1", "child.pid")
    alive = None
    if os.path.exists(pid_file):
        pid = int(Path(pid_file).read_text())
        for _ in range(30):
            try:
                st = Path(f"/proc/{pid}/stat").read_text().split()[2]
            except OSError:
                st = None
            alive = st not in (None, "Z")
            if not alive:
                break
            import time
            time.sleep(0.1)
    check("시간 초과면 KMM 프로세스 묶음째 죽인다 (작업자 자식도 남지 않는다)", alive is False, f"pid file {pid_file} alive={alive}")
    run_case("KMM 실행 파일 없음", None, on, ["KMM 을 실행하지 못했다", "cannot run KMM"])
    run_case("table 파일 없음", "rc1", {"enabled": True, "table": "nope.csv"}, ["table 파일이 없다", "table not found"])
    run_case("옵션 값 오류 (restitution 1.5)", "ok", {"enabled": True, "restitution": [1.5]}, ["bad value"])
    run_case("러너 KMM 이 EndTimeTable 을 모름 (v131 도움말)", "oldhelp", on,
             ["KMM version skew", "EndTimeTable", "apptainer_sif", "v132"])
    run_case("러너 KMM 에 도움말이 없음 (옛 바이너리 — '--help' 를 옵션 파일로 읽다 죽음)", "nohelp", on,
             ["KMM version skew", "DROP_ATTITUDE/--help"])
    ptmp = new_tmp("etp_tbl_old_")
    Path(ptmp, "t.csv").write_text("name,roll,pitch,yaw,endtim\nA,0,0,0,0.004\n", encoding="utf-8")
    run_case("table 지름길도 버전 확인 (v131 도움말)", "oldhelp", {"enabled": True, "table": "t.csv"},
             ["KMM version skew"], keep_tmp=ptmp)
    run_case("KMM 종료 코드 3 (덱 요소 소실) — 이유·rigidbody.json 안내", "rc3", on,
             ["요소를 버렸다", "model_rigidbody.json", "table 로", "KMM rc=3 element loss"])
    run_case("사전 해석 표 v0 가 이 낙하 √(2gh) 와 다름", "badv0", on, ["v0", "table drop mismatch"])
    t_old = run_case("사전 해석 KMM 이 PresimStrongContact 를 모름 (v132 도움말, 중력 끔)", "v132help", on,
                     ["KMM too old for strong_contact", "PresimStrongContact", "v133", "apptainer_sif",
                      "koomeshmodifier_path", "gravity=true(v132 규칙)", "미리 만든 table"])
    check("  … 사전 해석을 돌리기 전에 멈춘다 (KMM 호출 기록 없음) · 물은 것 DROP_ATTITUDE → RIGID_DROP_ENDTIME",
          not os.path.exists(os.path.join(t_old, "output", "endtime_presim", "1", "fake_kmm_call.json"))
          and help_calls(t_old) == ["--help DROP_ATTITUDE", "--help RIGID_DROP_ENDTIME"], str(help_calls(t_old)))
    run_case("사전 해석 표 strong_contact(0.5) ≠ 옵션(기본 0.2)", "badstrong", on,
             ["strong_contact mismatch", "strong_contact=0.5", "strong_contact 0.2 와 다르다"])

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
    print("[6] apptainer 감싸기 명령 (실행 없이 Popen 가로채기) — 새 세션·시간 제한·임시 폴더 정리")
    import Runner.EndTimePresim as EP
    tmp = new_tmp("etp_apt_")
    env = {"koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
           "apptainer_sif": "/opt/apptainers/SmartTwinPreprocessor.sif", "apptainer_bind": "/data:/data",
           "apptainer_env": {"A": "1"}, "apptainer_tmpdir": os.path.join(tmp, "apt"),
           "timeout_koomeshmodifier_seconds": 77}
    doe_angles = {"1": {"1": {"angle_name": "F1", "roll": 0.0, "pitch": 0.0, "yaw": 0.0}}}
    steps = [{"step": 1, "mode": "DROP"}]
    calls, helps = [], []

    class FakePopen:
        def __init__(self, cmd, **kw):
            self.cmd, self.kw, self.pid, self.returncode, self.timeout = cmd, kw, -1, 0, None
            self.tmpdir_env = os.environ.get("APPTAINER_TMPDIR")
            (helps if "--help" in cmd else calls).append(self)

        def communicate(self, timeout=None):
            self.timeout = timeout
            if "--help" in self.cmd:   # 러너 KMM 버전 확인 — 모드마다 그 모드의 새 키를 아는 v133 KMM 처럼 답한다
                return ("  PresimStrongContact  [실수]\n" if self.cmd[-1] == "RIGID_DROP_ENDTIME"
                        else "  EndTimeTable  [경로]\n"), None
            self.returncode = 2
            return None, None

        def wait(self):
            return self.returncode

    job = os.environ.get("SLURM_JOB_ID", str(os.getpid()))
    real, old_tmpdir = EP.subprocess.Popen, os.environ.get("APPTAINER_TMPDIR")
    EP._KMM_HELP_CACHE.clear()
    EP.subprocess.Popen = FakePopen
    err = ""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            EP.prepare_endtime_tables({"height": 800, "endtime_presim": {"enabled": True, "presim_timeout_seconds": 77}},
                                      env, os.path.join(tmp, "model.k"), os.path.join(tmp, "output"), tmp, doe_angles,
                                      steps)
    except EP.EndTimePresimError as e:
        err = str(e)
    finally:
        EP.subprocess.Popen = real
    work = os.path.join(tmp, "output", "endtime_presim", "1")
    c = calls[0] if calls else None
    check("apptainer exec --bind --env <sif> <KMM> <옵션> <작업 폴더>",
          c is not None and c.cmd == ["apptainer", "exec", "--bind", "/data:/data", "--env", "A=1",
                                      "/opt/apptainers/SmartTwinPreprocessor.sif",
                                      "/opt/SmartTwinPreprocessor/bin/KooMeshModifier", "rigid_drop_endtime.txt", work],
          str(c and c.cmd))
    check("cwd = 작업 폴더 · 시간 제한 = presim_timeout_seconds(77 — 러너 timeout 이 아니다) · 새 세션(start_new_session)",
          c is not None and c.kw.get("cwd") == work and c.timeout == 77 and c.kw.get("start_new_session") is True,
          str(c and (c.kw, c.timeout)))
    check("rc≠0 → 표식 + 종료 코드", MARK in err and "종료 코드 2" in err, err)
    wrap = ["apptainer", "exec", "--bind", "/data:/data", "--env", "A=1", "/opt/apptainers/SmartTwinPreprocessor.sif",
            "/opt/SmartTwinPreprocessor/bin/KooMeshModifier"]
    check("버전 확인도 러너와 같은 감싸기: apptainer exec … <sif> <KMM> --help DROP_ATTITUDE → --help RIGID_DROP_ENDTIME "
          "(각 한 번, 사전 해석 전, 새 세션)",
          len(helps) == 2 and [h.cmd for h in helps] == [wrap + ["--help", "DROP_ATTITUDE"], wrap + ["--help", "RIGID_DROP_ENDTIME"]]
          and all(h.kw.get("stdout") == subprocess.PIPE and h.timeout == EP.KMM_HELP_TIMEOUT
                  and h.kw.get("start_new_session") is True for h in helps), str([(x.cmd, x.kw) for x in helps]))
    job_dir = os.path.join(tmp, "apt", f"apptainer_job_{job}")
    check("apptainer 임시 폴더: 실행 중 APPTAINER_TMPDIR = apptainer_tmpdir/apptainer_job_<id>, 끝나면 지우고 환경 변수를 되돌린다",
          c is not None and c.tmpdir_env == job_dir and not os.path.exists(job_dir)
          and os.environ.get("APPTAINER_TMPDIR") == old_tmpdir, f"{c and c.tmpdir_env} exists={os.path.exists(job_dir)}")
    env2 = {k: v for k, v in env.items() if k != "apptainer_tmpdir"}
    env2["apptainer_sif"] = "/opt/apptainers/Other.sif"   # 다른 SIF — 기억에 없어 다시 묻는다
    EP.subprocess.Popen = FakePopen
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            EP.check_kmm_supports(env2, ("EndTimeTable",), tmp, EP.EndTimePresimError)
    finally:
        EP.subprocess.Popen = real
    sys_job = os.path.join(tempfile.gettempdir(), f"apptainer_job_{job}")
    check("apptainer_tmpdir 가 없으면 시스템 임시 폴더 아래(/opt/tmp 아님)에 만들고 지운다",
          len(helps) == 3 and helps[2].tmpdir_env == sys_job and not os.path.exists(sys_job)
          and not os.path.exists(f"/opt/tmp/apptainer_job_{job}"), str(helps[-1].tmpdir_env))
    EP.subprocess.Popen = FakePopen
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            EP.check_kmm_supports(env, ("EndTimeTable",), tmp, EP.EndTimePresimError)
            EP.check_kmm_strong_contact(env, tmp)
    finally:
        EP.subprocess.Popen = real
    check("같은 KMM·모드는 prepare(프로세스) 안에서 한 번만 묻는다 (기억)", len(helps) == 3, str(len(helps)))
    EP.subprocess.Popen = FakePopen
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            EP.check_kmm_strong_contact(env2, tmp)
            EP.check_kmm_strong_contact(env2, tmp)
    finally:
        EP.subprocess.Popen = real
    check("기억은 (실행 파일, SIF, 모드) 마다 — 다른 SIF 의 RIGID_DROP_ENDTIME 은 한 번 더 묻는다",
          len(helps) == 4 and helps[3].cmd[-3:] == ["/opt/SmartTwinPreprocessor/bin/KooMeshModifier", "--help",
                                                    "RIGID_DROP_ENDTIME"] and "/opt/apptainers/Other.sif" in helps[3].cmd,
          str([h.cmd for h in helps[3:]]))


# ── [7] 시간 제한 배율 ──────────────────────────────────────────
def submit_scripts(kcr, rc_path, sequential=False, time_limit="01:00:00", schedule=None):
    """_submit_cumulative 를 가짜 sinfo·sbatch 로 돌려 slurm 스크립트 글과 화면 출력을 돌려준다 (실제 제출 없음).
    schedule 을 주면 environment.schedule 로 넣고(v134 — false 면 표가 있어도 라운드로빈), 없으면 그 키를 뺀다."""
    import argparse
    rc = json.load(open(rc_path, encoding="utf-8"))
    rc["environment"]["time_limit"] = time_limit
    if schedule is None:
        rc["environment"].pop("schedule", None)
    else:
        rc["environment"]["schedule"] = schedule
    json.dump(rc, open(rc_path, "w", encoding="utf-8"), indent=1)
    slurm = os.path.join(rc["project"]["output_dir"], "slurm_scripts")
    real = subprocess.run

    def fake_run(cmd, *a, **k):
        out = {"sinfo": "7-00:00:00\n" if "%l" in cmd else "", "sbatch": "Submitted batch job 4242\n",
               "scontrol": ""}.get(cmd[0])
        if out is None:
            raise RuntimeError(f"예상 밖 명령 {cmd}")
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")
    args = argparse.Namespace(config=rc_path, mode="cumulative", nodes=2, jobs_per_node=4, ncpu_per_job=None,
                              partition=None, memory=None, time_limit=None, data_root="/data", sequential=sequential)
    buf = io.StringIO()
    subprocess.run = fake_run
    try:
        with contextlib.redirect_stdout(buf):
            kcr._submit_cumulative(args, Path(rc_path))
    finally:
        subprocess.run = real
    texts = {n: Path(slurm, n).read_text(encoding="utf-8") for n in sorted(os.listdir(slurm)) if n.endswith(".sh")}
    for n in texts:
        os.remove(os.path.join(slurm, n))
    return texts, buf.getvalue()


def test_time_factor(kcr, on):
    print("[7] 시간 제한 배율 — ceil(endtim ÷ tFinal), 표가 없으면 그대로")
    import Runner.EndTimePresim as EP
    from Runner.CumulativeScenarioRunner import CumulativeScenarioRunner
    f = EP.endtime_time_factor
    check("표 없음 → 1", f({}) == 1 and f({"scenario": {}}) == 1 and f({"scenario": {"doe_endtim": {}}}) == 1)
    cfg = {"scenario": {"doe_endtim": {"1": {"1": 0.012}, "2": {"1": 0.0042, "2": 0.0101}}},
           "simulation_params": {"tFinal": 0.005}}
    check("최대 0.012 / tFinal 0.005 → 3 · DOE 1 → 3 · DOE 2 스텝 1 → 1 · 스텝 2 → 3",
          f(cfg) == 3 and f(cfg, 1, 1) == 3 and f(cfg, 2, 1) == 1 and f(cfg, 2, 2) == 3 and f(cfg, 9, 1) == 1)
    check("부동소수 잡음: 0.01 / 0.005 → 2 (3 아님) · tFinal 기본 0.005", f({"scenario": {"doe_endtim": {"1": {"1": 0.01}}},
          "simulation_params": {"tFinal": 0.005}}) == 2 and f({"scenario": {"doe_endtim": {"1": {"1": 0.01}}}}) == 2)
    check("충격 조건처럼 짧은 표(2 ms < tFinal 5 ms) → 1", f({"scenario": {"doe_endtim": {"1": {"1": 0.0021}}}}) == 1)
    r = CumulativeScenarioRunner.__new__(CumulativeScenarioRunner)
    r.config = {"execution": {"timeout_per_step_seconds": 7200}, **cfg}
    check("러너 스텝 시간 제한 = timeout_per_step_seconds × 그 DOE·스텝 배율", r._step_timeout(1, 1) == 21600
          and r._step_timeout(2, 1) == 7200 and r._step_timeout(2, 2) == 21600)
    r.config = {"execution": {"timeout_per_step_seconds": 7200}, "scenario": {}}
    check("러너: 표 없으면 예전 값", r._step_timeout(1, 1) == 7200)

    rc, tmp = on[0], on[1]
    rc_path = os.path.join(tmp, "runner_config.json")
    tf = rc["simulation_params"]["tFinal"]
    # DOE 배율 F_d = Σ 스텝 ceil(endtim ÷ tFinal) (DR 없음) — 2 스텝 cyclic 이라 DOE 마다 다르다
    fd = {int(d): sum(max(1, math.ceil(round(v / tf, 9))) for v in st.values())
          for d, st in rc["scenario"]["doe_endtim"].items()}
    want = max(fd.values())
    texts, out = submit_scripts(kcr, rc_path)
    tl = [l for t in texts.values() for l in t.splitlines() if l.startswith("#SBATCH --time=")]
    check(f"submit(누적): DOE 배율 F_d = Σ 스텝 ceil(endtim/tFinal) {sorted(fd.values())} → --time 01:00:00 × 최대 {want}"
          f" (예전 식 step 배율 2 × 표 배율 {max(math.ceil(round(v / tf, 9)) for st in rc['scenario']['doe_endtim'].values() for v in st.values())} 이 아니다)",
          want > 2 and tl and all(l == f"#SBATCH --time={want}:00:00" for l in tl)
          and f"endtime factor {want}" in out, f"{set(tl)} {out[-300:]}")
    # 라운드로빈 (d − 1) % 2 기대값은 schedule 끈 경우다 — 켜면 칸이 lpt_lanes 로 바뀐다(tests/test_kcr_doe_schedule.py)
    texts, out = submit_scripts(kcr, rc_path, sequential=True, schedule=False)
    tl = {l for n, t in texts.items() if not n.startswith("run_doe_")   # DOE 별 스크립트도 미리 쓴다 — 슬롯 스크립트만 본다
          for l in t.splitlines() if l.startswith("#SBATCH --time=")}
    slot = max(sum(f for d, f in fd.items() if (d - 1) % 2 == n) for n in range(2))
    check(f"submit --sequential(schedule 끔): 01:00:00 × 슬롯마다 F_d 합의 최대 {slot} (노드 2)",
          tl == {f"#SBATCH --time={slot}:00:00"}, str(tl))
    tmp0 = new_tmp("etp_tl_off_")
    rc0, _ = designer_prepare(tmp0, scen_faces2(tmp0))
    sdf = kcr._step_dr_time_factor(rc0)
    texts, out = submit_scripts(kcr, os.path.join(tmp0, "runner_config.json"))
    tl = {l for t in texts.values() for l in t.splitlines() if l.startswith("#SBATCH --time=")}
    check(f"표 없음: --time = 01:00:00 × step 배율 {sdf} (예전 그대로) · 표 배율 안내 없음",
          sdf == 2 and tl == {"#SBATCH --time=2:00:00"} and "endtime factor" not in out, str(tl))
    try:
        texts, out = submit_scripts(kcr, os.path.join(tmp0, "runner_config.json"), sequential=True, time_limit="100:00:00")
        tl = {l for n, t in texts.items() if n.startswith("run_seq_") for l in t.splitlines() if l.startswith("#SBATCH --time=")}
    except Exception as e:   # 고치기 전: 파티션 최대로 잘린 '7-00:00:00' 을 int('7-00') 로 읽다 죽었다
        tl = repr(e)
    check("sequential: 파티션 최대(7-00:00:00)로 잘린 DOE 시간도 읽는다 → 슬롯도 7-00:00:00", tl == {"#SBATCH --time=7-00:00:00"},
          str(tl))
    rc2 = json.load(open(rc_path, encoding="utf-8"))
    rc2["scenario"]["doe_endtim"] = {d: {s: 0.0021 for s in st} for d, st in rc2["scenario"]["doe_endtim"].items()}
    json.dump(rc2, open(rc_path, "w", encoding="utf-8"), indent=1)
    texts, out = submit_scripts(kcr, rc_path)
    tl = {l for t in texts.values() for l in t.splitlines() if l.startswith("#SBATCH --time=")}
    check("표가 tFinal 보다 짧으면(충격 조건 1~2 ms) 표 없을 때와 같은 시간 (F_d = step 배율)",
          tl == {"#SBATCH --time=2:00:00"}, str(tl))


# ── [8] reach·n_unresolved 알림 ─────────────────────────────────
def test_reach():
    print("[8] reach·n_unresolved — 바닥판 반폭과 비교, 미해결 각도 수")
    tmp = new_tmp("etp_reach_")
    rc, out = designer_prepare(tmp, with_presim(scen_faces2(tmp), {"enabled": True},
                                                koomeshmodifier_path=write_fake(tmp, "farreach")))
    check("reach 최대 160 > 바닥판 200×200 반폭 100 → 경고 (한 변 320 이상으로)",
          "reach 최대 160" in out and "plate reach" in out and "320" in out, out[-600:])
    check("n_unresolved > 0 인 각도 2개 경고", "n_unresolved > 0 인 각도 2개" in out, out[-600:])
    tmp2 = new_tmp("etp_reach_ok_")
    _, out2 = designer_prepare(tmp2, with_presim(scen_faces2(tmp2), {"enabled": True},
                                                 koomeshmodifier_path=write_fake(tmp2, "ok")))
    check("reach 15 < 반폭 100 → 경고 없음, 미해결 없음", "reach 최대 15" in out2 and "plate reach" not in out2
          and "n_unresolved" not in out2, out2[-400:])
    tmp3 = new_tmp("etp_reach_rw_")
    u = with_presim(scen_faces2(tmp3), {"enabled": True}, koomeshmodifier_path=write_fake(tmp3, "farreach"))
    u["simulation_params"]["drop_surface"] = {"type": "RigidWall"}
    _, out3 = designer_prepare(tmp3, u)
    check("RigidWall 이면 판 크기 경고 없음", "RigidWall" in out3 and "plate reach" not in out3, out3[-400:])
    import Runner.EndTimePresim as EP
    check("drop_v0: mm-t-s 1500 → 5424.9 mm/s, mm-kg-ms → 5.4249 mm/ms, m-kg-s 1.5 → 5.4249 m/s, gravity 주면 그것",
          abs(EP.drop_v0(1500, "mm-t-s") - 5424.942396) < 1e-5 and abs(EP.drop_v0(1500, "mm-kg-ms") - 5.424942396) < 1e-8
          and abs(EP.drop_v0(1.5, "m-kg-s") - 5.424942396) < 1e-8 and abs(EP.drop_v0(1000, "mm-t-s", 9000) - 4242.640687) < 1e-5)


# ── [9] 수정 묶음 (사용자 결정·리뷰 R3) ───────────────────────────
def faces_table(tmp, angles, meta, bom=False, name="t.csv"):
    """육면 6 자세 표(endtim 0.003 + 0.0001·i) — meta 는 '# k=v' 줄로, bom 이면 엑셀처럼 BOM 을 붙인다."""
    lines = [f"# {k}={v}" for k, v in meta.items()] + ["name,roll,pitch,yaw,endtim"]
    lines += [f"T{i},{r},{p},{y},{0.003 + 0.0001 * i:.6g}" for i, (_, r, p, y) in enumerate(angles)]
    Path(tmp, name).write_text(("﻿" if bom else "") + "\n".join(lines) + "\n", encoding="utf-8")
    return os.path.join(tmp, name)


def table_prepare(tmp, presim_extra=None, sim_extra=None):
    """table 지름길 prepare → (runner_config | None, 출력, 오류 글)."""
    import Runner.EndTimePresim as EP
    u = with_presim(scen_faces2(tmp), {"enabled": True, "table": "t.csv", **(presim_extra or {})},
                    koomeshmodifier_path=write_fake(tmp, "rc1"))
    u["simulation_params"].update(sim_extra or {})
    try:
        rc, out = designer_prepare(tmp, u)
        return rc, out, ""
    except EP.EndTimePresimError as e:
        return None, "", str(e)


def ref_find(rows, roll, pitch, yaw):
    """옛 순수 파이썬 찾기 — numpy 판과 대조용."""
    import Runner.EndTimePresim as EP
    d = EP.drop_direction(roll, pitch, yaw)
    hits = [r["endtim"] for r in rows if sum(a * b for a, b in zip(r["dir"], d)) >= math.cos(math.radians(0.01))]
    return max(hits) if hits else None


def test_r3(kcr, rc_off):
    print("[9] 수정 묶음 — BOM·중력 메타·단위 g·덱·numpy 찾기·사전 해석 시간 제한·batch KMM·노드 확인·배열·deep·F_d")
    import time
    import Runner.EndTimePresim as EP
    angles = EP.collect_drop_angles(rc_off["scenario"]["doe_angles"], rc_off["scenario"]["steps"])
    v0 = math.sqrt(2 * 9810.0 * 1000)
    good = {"format": "rigid_drop_endtime/endtime v1", "units": "mm-t-s", "time_unit": "s", "height": 1000, "v0": v0,
            "gravity": 0, "t_sep_ms": 1.0}

    tmp = new_tmp("etp_bom_")
    faces_table(tmp, angles, good, bom=True)
    rc, out, err = table_prepare(tmp)
    got = sorted({v for st in (rc or {}).get("scenario", {}).get("doe_endtim", {}).values() for v in st.values()})
    check("BOM(엑셀 저장) 붙은 표도 메타·칸을 읽는다", rc is not None and len(got) == 6 and abs(got[0] - 0.003) < 1e-12
          and "t_sep_ms 메타가 없다" not in out, err or out[-300:])

    tmp = new_tmp("etp_grav_")
    faces_table(tmp, angles, {**good, "gravity": 1})
    rc, out, err = table_prepare(tmp)
    check("표 메타 gravity 1 ≠ 옵션 gravity false → 멈춘다", rc is None and "사전 해석 중력 켬" in err
          and "table drop mismatch" in err, err)
    rc, out, err = table_prepare(tmp, {"gravity": True})
    check("옵션 gravity true 면 같은 표를 받는다", rc is not None, err)

    tmp = new_tmp("etp_deck_")
    faces_table(tmp, angles, {**good, "deck": "/elsewhere/other_model.k"})
    rc, out, err = table_prepare(tmp)
    check("표 메타 deck 이 템플릿과 다르면 경고만", rc is not None and "표를 만든 덱 /elsewhere/other_model.k" in out, err)

    tmp = new_tmp("etp_mmkgms_")
    faces_table(tmp, angles, {**good, "units": "mm-kg-ms", "time_unit": "ms", "v0": math.sqrt(2 * 9.81e-3 * 1000)})
    rc, out, err = table_prepare(tmp)
    check("mm-kg-ms 덱(표 메타)인데 simulation_params.gravity 없음 → 멈춘다 (FEM KMM 이 그 단위 g 를 못 정한다)",
          rc is None and "gravity required for mm-kg-ms" in err and "0.00981" in err, err)
    rc, out, err = table_prepare(tmp, sim_extra={"gravity": 0.00981})
    check("simulation_params.gravity 0.00981 을 주면 받는다", rc is not None, err)

    rnd = random.Random(7)
    rows = []
    for i in range(400):
        r, p, y = rnd.uniform(-180, 180), rnd.uniform(-90, 90), rnd.uniform(-180, 180)
        rows.append({"name": f"R{i}", "roll": r, "pitch": p, "yaw": y, "endtim": rnd.uniform(1e-3, 9e-3),
                     "dir": EP.drop_direction(r, p, y)})
    queries = [(r["roll"] + dr, r["pitch"] + dp, r["yaw"]) for r in rows[:150]
               for dr, dp in ((0.0, 0.0), (0.004, 0.003), (0.012, 0.0), (0.0, 0.0099))]
    queries += [(rnd.uniform(-180, 180), rnd.uniform(-90, 90), 0.0) for _ in range(100)]
    same = all(EP.find_endtim(rows, *q) == ref_find(rows, *q) for q in queries)
    check(f"numpy 찾기 = 옛 순수 파이썬 찾기 ({len(queries)} 묻기, 경계 0.004~0.012° 포함)", same)
    big = [{"name": f"B{i}", "roll": a, "pitch": b, "yaw": 0.0, "endtim": 0.002 + 1e-7 * i,
            "dir": EP.drop_direction(a, b, 0.0)}
           for i, (a, b) in enumerate((rnd.uniform(-180, 180), rnd.uniform(-90, 90)) for _ in range(20000))]
    t0 = time.time()
    res = EP._endtims_for(big, [(r["name"], r["roll"], r["pitch"], 0.0) for r in big], "big.csv", by_name=True)
    dt = time.time() - t0
    check(f"2만 각도 × 2만 줄 찾기 {dt:.1f} 초 (< 30 초, 옛 순수 파이썬 99 초)", dt < 30 and len(res) == 20000, f"{dt:.1f}")

    o = EP.presim_options({"endtime_presim": {"enabled": True}})
    check("presim_timeout_seconds 기본 21600 (6 시간)", o["presim_timeout_seconds"] == 21600 == EP.PRESIM_TIMEOUT)
    bad = []
    for v in (0, -5, "x", True):
        try:
            EP.presim_options({"endtime_presim": {"enabled": True, "presim_timeout_seconds": v}})
            bad.append(v)
        except EP.EndTimePresimError as e:
            if "presim_timeout_seconds" not in str(e):
                bad.append(v)
    check("presim_timeout_seconds 0·음수·글자·bool → 값 오류", not bad, str(bad))

    # batch_koomeshmodifier — SIF 없고 /opt/ 경로면 koochainrun_path 옆 호스트 KMM 을 묻고 그것으로 사전 해석한다
    tmp = new_tmp("etp_batch_")
    os.makedirs(os.path.join(tmp, "bin"))
    host = os.path.join(tmp, "bin", "KooMeshModifier")
    Path(host).write_text(Path(write_fake(tmp, "ok")).read_text(encoding="utf-8"), encoding="utf-8")
    os.chmod(host, 0o755)
    u = with_presim(scen_faces2(tmp), {"enabled": True}, koomeshmodifier_path="/opt/nonexistent_kcr_test/bin/KooMeshModifier",
                    koochainrun_path=os.path.join(tmp, "bin", "KooChainRun"))
    u["scenarios"][0]["cumulative"] = {"num_steps": 1, "mode_sequence": ["DROP"]}
    u["scenarios"][0]["batch_koomeshmodifier"] = True
    EP._KMM_HELP_CACHE.clear()
    try:
        rc, out = designer_prepare(tmp, u)
        err = ""
    except EP.EndTimePresimError as e:
        rc, out, err = None, "", str(e)
    call = os.path.join(tmp, "output", "endtime_presim", "1", "fake_kmm_call.json")
    argv0 = json.load(open(call, encoding="utf-8"))["argv"][0] if os.path.exists(call) else None
    bcmd = batch_config(kcr, rc)[1] if rc else None
    check("batch: 버전 확인·사전 해석 = 배치가 돌릴 호스트 KMM(koochainrun_path 옆) = _prepare_batch_koomeshmodifier 명령",
          rc is not None and rc["scenario"].get("batch_koomeshmodifier") is True
          and os.path.exists(os.path.join(tmp, "bin", "fake_help_calls.txt")) and argv0 == host
          and bcmd and bcmd[0] == host, f"{err} argv0={argv0} bcmd={bcmd}")
    check("batch: --help RIGID_DROP_ENDTIME(PresimStrongContact)도 그 호스트 KMM 에 묻는다",
          help_calls(os.path.join(tmp, "bin")) == ["--help DROP_ATTITUDE", "--help RIGID_DROP_ENDTIME"],
          str(help_calls(os.path.join(tmp, "bin"))))
    u["scenarios"][0]["batch_koomeshmodifier"] = False
    EP._KMM_HELP_CACHE.clear()
    try:
        designer_prepare(tmp, u)
        err = ""
    except EP.EndTimePresimError as e:
        err = str(e)
    check("batch 가 아니면 러너 KMM(koomeshmodifier_path)을 묻는다 — 헤드에 없으면 멈추고 헤드 실행이 필요하다고 알린다",
          "cannot run KMM" in err and "/opt/nonexistent_kcr_test" in err and "헤드 노드" in err, err)

    # 노드 쪽 확인 — KMM 출력에 [EndTimeTable]·[RigidAngularVelocity] 표식이 없으면 그 스텝을 실패로
    from Runner.CumulativeScenarioRunner import CumulativeScenarioRunner as CSR
    cfg = os.path.join(tmp, "cfg.txt")
    Path(cfg).write_text("**DropAttitude,1\ntFinal,0.004\nEndTimeTable,/data/t.csv\nRigidAngularVelocityX,1\n**EndDropAttitude\n",
                         encoding="utf-8")
    plain = os.path.join(tmp, "plain.txt")
    Path(plain).write_text("**DropAttitude,1\ntFinal,0.004\nInitialAngularVelocityX,0\n**EndDropAttitude\n", encoding="utf-8")
    try:
        u1 = CSR._unread_table_keys(cfg, "run ok")
        u2 = CSR._unread_table_keys(cfg, "[EndTimeTable] /data/t.csv: 표 6줄에서 각도 1개를 모두 찾았다\n"
                                         "[RigidAngularVelocity] centre=(0, 0, 0)")
        u3 = CSR._unread_table_keys(cfg, "[EndTimeTable] ok")
        u4 = CSR._unread_table_keys(plain, "")
        ok = (u1 == ["EndTimeTable", "RigidAngularVelocity"] and u2 == [] and u3 == ["RigidAngularVelocity"] and u4 == [])
    except Exception as e:   # 고치기 전 코드에는 없다
        ok, u1 = False, repr(e)
    check("러너: 스텝 설정의 표 줄을 KMM 출력 표식으로 확인 (표 줄 없는 설정은 검사 없음)", ok, str(u1))

    # 대규모 배열 --time — 배열 DOE(0-based)의 최대 배율, 파티션 최대에서 자르고 🔴 경고
    from Runner.LargeScaleDOEManager import LargeScaleDOEManager as LS
    m = LS.__new__(LS)
    m.partition, m.timeout = "normal", 7200
    m.runner_config = {"simulation_params": {"tFinal": 0.004},
                       "scenario": {"doe_endtim": {"1": {"1": 0.004}, "2": {"1": 0.0101}, "3": {"1": 0.004}}}}
    real = subprocess.run

    def fake_sinfo(cmd, *a, **k):
        return subprocess.CompletedProcess(cmd, 0, stdout="1-00:00:00\n" if cmd[0] == "sinfo" else "", stderr="")
    buf = io.StringIO()
    subprocess.run = fake_sinfo
    try:
        with contextlib.redirect_stdout(buf):
            t_all = m._array_time_limit(1, 0, 2)
            t_one = m._array_time_limit(1, 0, 0)
            m.timeout = 50000
            t_cap = m._array_time_limit(1, 1, 1)
            m.runner_config = {"scenario": {}}
            t_off = m._array_time_limit(1, 0, 2)
    except Exception as e:
        t_all = t_one = t_cap = t_off = repr(e)
    finally:
        subprocess.run = real
    check("대규모 배열: DOE 0..2(표 1..3) 최대 배율 3 → 06:00:00, DOE 0 만 → 02:00:00",
          t_all == "06:00:00" and t_one == "02:00:00", f"{t_all} {t_one}")
    check("대규모 배열: 50000 s × 3 > 파티션 1-00:00:00 → 24:00:00 + 🔴 경고 · 표 없으면 timeout 그대로",
          t_cap == "24:00:00" and "time limit capped below need" in buf.getvalue() and t_off == "13:53:20",
          f"{t_cap} {t_off} {buf.getvalue()[-200:]}")

    # 대규모 배열 스크립트 — 표가 있을 때만 KMM 출력을 남겨 표식을 grep 한다
    def array_script(rcfile, root):
        m2 = None
        with contextlib.redirect_stdout(io.StringIO()):
            m2 = LS(rcfile, data_root=root)
        m2.base_dir = root
        subprocess.run = lambda cmd, *a, **k: subprocess.CompletedProcess(cmd, 0, stdout="4242\n", stderr="")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                m2.submit_step_array_job(m2.scenarios[0], 1, 0, 5)
        finally:
            subprocess.run = real
        names = [n for n in os.listdir(root) if n.startswith("slurm_") and n.endswith(".sh")]
        return Path(root, names[0]).read_text(encoding="utf-8") if names else ""
    try:
        tmp_on, tmp_off = new_tmp("etp_ls_on_"), new_tmp("etp_ls_off_")
        designer_prepare(tmp_on, with_presim(scen_faces2(tmp_on), {"enabled": True},
                                             koomeshmodifier_path=write_fake(tmp_on, "ok")))
        designer_prepare(tmp_off, scen_faces2(tmp_off))
        s_on = array_script(os.path.join(tmp_on, "runner_config.json"), os.path.join(tmp_on, "ls"))
        s_off = array_script(os.path.join(tmp_off, "runner_config.json"), os.path.join(tmp_off, "ls"))
    except Exception as e:
        s_on = s_off = repr(e)
    check("대규모 배열 스크립트: 표가 있으면 KMM 출력 tee + [EndTimeTable] grep, 없으면 그 줄이 없다",
          'tee "$STEP_DIR/kmm_drop_attitude.log"' in s_on and "KM_EXIT=${PIPESTATUS[0]}" in s_on
          and '[EndTimeTable]' in s_on and "KMM version skew" in s_on
          and "kmm_drop_attitude.log" not in s_off and "KM_EXIT=$?" in s_off, (s_on + s_off)[-300:])

    # deep report 시간 제한 — 그 스텝 배율
    try:
        pp1 = CSR._scaled_deep_options({"deep_timeout_seconds": 3600, "deep_time_limit": "1-00:00:00", "x": 1}, 3)
        pp2 = CSR._scaled_deep_options({}, 3)
        from Runner.PostprocessShellGenerator import build_deep_report_sbatch
        sb = build_deep_report_sbatch("/data/r", "/data/r/deep_report.sh", options=pp2, environment={})
        ok = (pp1 == {"deep_timeout_seconds": 10800, "deep_time_limit": "72:00:00", "x": 1}
              and pp2 == {"deep_timeout_seconds": 21600} and "#SBATCH --time=06:10:00" in sb)
    except Exception as e:
        ok, pp1 = False, repr(e)
    check("deep report: deep_timeout_seconds·deep_time_limit × 배율 → sbatch --time 도 늘어난다", ok, str(pp1))

    # DOE 배율 F_d — r 이 모두 1 이면 _step_dr_time_factor 와 같다
    def cfg(steps, dr, table):
        return {"scenario": {"total_steps": steps, "doe_count": len(table), "doe_endtim": table},
                "simulation_params": {"tFinal": 0.004, "dynamic_relaxation": dr}}
    try:
        f_eq = [EP.doe_time_factors(cfg(n, dr, {"1": {str(s): 0.004 for s in range(1, n + 1)}}))[1]
                == kcr._step_dr_time_factor(cfg(n, dr, {})) for n in (1, 2, 3) for dr in (False, True, {"enabled": True})]
        f1 = EP.doe_time_factors(cfg(3, True, {"1": {"1": 0.012, "2": 0.004, "3": 0.004}, "2": {"2": 0.0081}}))
        f0 = EP.doe_time_factors({"scenario": {"total_steps": 2}})
        ok = all(f_eq) and f1 == {1: 3 + 2 + 2, 2: 1 + 4 + 2} and f0 is None
    except Exception as e:
        ok, f1 = False, repr(e)
    check("F_d = Σ 스텝 (ceil(endtim/tFinal) + DR 2 스텝부터 1): 짧은 표 = 예전 step/DR 배율, 표에 없는 스텝(열)은 1",
          ok, str(f1))
    try:
        hs = [kcr._hms_scale(a, b) for a, b in (("01:00:00", 3), ("1-00:00:00", 2), ("30", 2), ("2-12", 1), ("45:30", 2))]
    except Exception as e:
        hs = [repr(e)]
    check("_hms_scale: Slurm 형식 HH:MM:SS·D-HH:MM:SS·MM·D-HH·MM:SS", hs == ["3:00:00", "48:00:00", "1:00:00", "60:00:00",
                                                                           "1:31:00"], str(hs))


# ── [10] v133 strong_contact ───────────────────────────────────
def test_v133(kcr, rc_off):
    print("[10] v133 strong_contact — 표 메타 endtime_rule·strong_contact, 사전 해석 중력 켬은 v132 와 같은 옵션 파일")
    import Runner.EndTimePresim as EP
    angles = EP.collect_drop_angles(rc_off["scenario"]["doe_angles"], rc_off["scenario"]["steps"])
    v0 = math.sqrt(2 * 9810.0 * 1000)
    base = {"format": "rigid_drop_endtime/endtime v1", "units": "mm-t-s", "time_unit": "s", "height": 1000, "v0": v0,
            "gravity": 0, "t_sep_ms": 1.0}
    strong = {**base, "endtime_rule": "last_strong", "strong_contact": 0.2}
    W132, MIS = "v132 first-recontact table", "strong_contact mismatch"

    def tbl(meta, presim_extra=None):
        tmp = new_tmp("etp_rule_")
        faces_table(tmp, angles, meta)
        rc, out, err = table_prepare(tmp, presim_extra)
        return rc, out, err, help_calls(tmp)

    rc, out, err, calls = tbl(base)
    check("table: endtime_rule 없는 v132 표(중력 끔) → 경고 한 줄 + 받는다", rc is not None and out.count(W132) == 1,
          err or out[-400:])
    check("table 지름길은 --help RIGID_DROP_ENDTIME 을 묻지 않는다 (DROP_ATTITUDE 만)", calls == ["--help DROP_ATTITUDE"],
          str(calls))
    rc, out, err, _ = tbl(strong)
    check("table: last_strong·strong_contact 0.2 = 옵션 기본 → 경고·오류 없음",
          rc is not None and W132 not in out and "strong_contact" not in out, err or out[-400:])
    rc, out, err, _ = tbl({**strong, "strong_contact": "0.2000000001"})
    check("table: strong_contact 차 1e-10 (≤ 1e-9) → 받는다", rc is not None, err)
    rc, out, err, _ = tbl({**strong, "strong_contact": "0.200001"})
    check("table: strong_contact 차 1e-6 → 멈춘다 (두 값을 찍는다)", rc is None and MIS in err and "strong_contact=0.200001" in err
          and "strong_contact 0.2 와 다르다" in err, err)
    rc, out, err, _ = tbl({**strong, "strong_contact": 0.5}, {"strong_contact": 0.5})
    check("table: 옵션 strong_contact 0.5 = 표 0.5 → 받는다", rc is not None, err)
    rc, out, err, _ = tbl(strong, {"strong_contact": 0.5})
    check("table: 옵션 0.5 ≠ 표 0.2 → 멈춘다", rc is None and MIS in err, err)
    rc, out, err, _ = tbl({**base, "gravity": 1, "endtime_rule": "first_recontact", "strong_contact": 9}, {"gravity": True})
    check("table: first_recontact(중력 켬) 표는 strong_contact 를 보지 않는다 (메타 9 여도 받는다, 경고 없음)",
          rc is not None and W132 not in out and "strong_contact" not in out, err or out[-400:])
    rc, out, err, _ = tbl({**base, "gravity": 1}, {"gravity": True})
    check("table: endtime_rule 없는 중력 켬 표(v132) → 경고 없음 (v133 도 같은 첫 재접촉 규칙)",
          rc is not None and W132 not in out, err or out[-400:])
    rc, out, err, _ = tbl({**base, "endtime_rule": "some_future_rule"})
    check("table: 모르는 endtime_rule → 경고만", rc is not None and "unknown endtime_rule" in out, err or out[-400:])
    rc, out, err, _ = tbl({**base, "endtime_rule": "last_strong"})
    check("table: last_strong 인데 strong_contact 메타 없음 → 경고만", rc is not None and "strong_contact unreadable" in out,
          err or out[-400:])
    rc, out, err, _ = tbl({**strong, "strong_contact": "1000.0000005"}, {"strong_contact": 1000.0})
    check("table: 문턱 1000 · 표 1000.0000005 (상대 5e-10) → 받는다 (상대 허용차)", rc is not None, err)
    rc, out, err, _ = tbl({**strong, "strong_contact": "1000.00001"}, {"strong_contact": 1000.0})
    check("table: 문턱 1000 · 표 1000.00001 (상대 1e-8) → 멈춘다", rc is None and MIS in err, err)
    rc, out, err, _ = tbl({**strong, "endtime_rule": " Last_Strong "})
    check("table: endtime_rule 대소문자·공백 무관 (' Last_Strong ') → 경고 없음",
          rc is not None and "unknown endtime_rule" not in out and W132 not in out, err or out[-400:])
    rc, out, err, _ = tbl({**strong, "endtime_rule": "LAST_STRONG"}, {"strong_contact": 0.5})
    check("table: LAST_STRONG 도 문턱을 본다 (옵션 0.5 ≠ 표 0.2 → 멈춘다)", rc is None and MIS in err, err)
    rc, out, err, _ = tbl({**base, "endtime_rule": "first_recontact"})
    check("table: 중력 끔 표인데 endtime_rule=first_recontact → 경고 한 줄 + 받는다",
          rc is not None and out.count(W132) == 1 and "first_recontact 인 표" in out, err or out[-400:])
    nograv = {k: v for k, v in strong.items() if k != "gravity"}
    rc, out, err, _ = tbl(nograv, {"gravity": True})
    check("table: last_strong 표 · 메타 gravity 없음 · 옵션 gravity=true → 멈춘다 (중력 다름)",
          rc is None and "gravity mismatch" in err and "endtime_rule=last_strong" in err, err)
    rc, out, err, _ = tbl({k: v for k, v in base.items() if k != "gravity"}, {"gravity": True})
    check("table: 규칙·gravity 메타 없는 v132 표 · 옵션 gravity=true → 경고 없음 (같은 첫 재접촉 규칙)",
          rc is not None and W132 not in out, err or out[-400:])

    def presim(opts, mode):
        tmp = new_tmp("etp_v133_")
        try:
            rc, out = designer_prepare(tmp, with_presim(scen_faces2(tmp), {"enabled": True, **opts},
                                                        koomeshmodifier_path=write_fake(tmp, mode)))
            err = ""
        except EP.EndTimePresimError as e:
            rc, out, err = None, "", str(e)
        work = os.path.join(tmp, "output", "endtime_presim", "1")
        p = os.path.join(work, "rigid_drop_endtime.txt")
        return rc, out, err, (Path(p).read_text(encoding="utf-8") if os.path.exists(p) else ""), help_calls(tmp), tmp, work

    rc, out, err, opt, calls, tmp, work = presim({"gravity": True}, "v132help")
    want = (f"*Inputfile\n{os.path.join(tmp, 'model.k')}\n*Mode\nRIGID_DROP_ENDTIME,1\n**RigidDropEndtime,1\n"
            f"Height,1000\nAngleFile,{os.path.join(work, 'angles.csv')}\nRestitution,0.1,0.3,0.5\nFriction,0.5\n"
            f"PresimGravity,1\nMarginMs,1.0\nWorkers,8\n**EndRigidDropEndtime\n*End\n")
    check("사전 해석 중력 켬: 옵션 파일에 PresimStrongContact 없음 (v132 와 같은 글) → v132 KMM 으로도 돈다",
          rc is not None and opt == want, err or repr(opt))
    check("사전 해석 중력 켬: --help RIGID_DROP_ENDTIME 을 묻지 않는다 · 경고 없음",
          calls == ["--help DROP_ATTITUDE"] and "ignored with gravity" not in out and W132 not in out, f"{calls} {out[-300:]}")
    rc, out, err, opt, calls, tmp, work = presim({"gravity": True, "strong_contact": 0.5}, "ok")
    check("사전 해석 중력 켬 + strong_contact 0.5 → 경고 한 줄, 줄은 넘기지 않는다",
          rc is not None and out.count("ignored with gravity") == 1 and "PresimStrongContact" not in opt, err or out[-300:])
    rc, out, err, opt, calls, tmp, work = presim({"strong_contact": 0.5}, "ok")
    check("사전 해석 중력 끔 + strong_contact 0.5 → PresimGravity,0 뒤 PresimStrongContact,0.5 (표 메타 0.5 와 맞는다)",
          rc is not None and "\nPresimGravity,0\nPresimStrongContact,0.5\nMarginMs,1.0\n" in opt and MIS not in out,
          err or repr(opt))
    rc, out, err, opt, calls, tmp, work = presim({}, "v132table")
    check("사전 해석 표에 endtime_rule 이 없으면(KMM 이 규칙 메타를 안 씀) → v132 표 경고 한 줄",
          rc is not None and out.count(W132) == 1, err or out[-300:])


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
    test_time_factor(kcr, on)
    test_reach()
    test_r3(kcr, off[0])
    test_v133(kcr, off[0])
    print()
    if FAILS:
        print("FAIL %d:" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
