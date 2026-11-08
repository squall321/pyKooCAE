# KMM RIGID_DROP_ENDTIME 모드(옵션 검사·산출 다섯 개·KMM→KMM 표 소비·오류 rc 1·도움말)를 실제 KMM 실행으로 검증하는 통합 시험
"""
실행: venv312/bin/python tests/test_rigid_drop_endtime_mode.py   (pybullet 필요, KMM 서브프로세스 열세 번, 1분 남짓,
      사전 해석 프로세스는 4 개 이하)

  [1] 옵션 검사(parse_option_lines) — 키 이름 전체 일치·대소문자·기본값·AngleFile 절대 경로·오류(ValueError, 모르는 키는
      did you mean), AngleFile 읽기, 충돌 상태 표의 덱 단위 환산, PresimStrongContact(기본 0.3 = 엔진 STRONG_CONTACT·값·
      틀린 값·비슷한 키), 중력 켬 + PresimStrongContact 경고 줄(가짜 덱으로 START·경고 줄까지만 돌림)
  [2] MinimumModel Fibonacci 30 — rc 0, 작업 폴더에 산출 다섯 개, 덱 옆에는 리더의 _dump.k 만, JSON 질량·사전 해석 요약,
      표(load_lookup·메타 v0·t_sep_ms·reach·n_unresolved)·충돌 상태 표(k=1 줄 = 입력 낙하 방향·(0,0,−v0)·각속도 0),
      v133 규칙(메타 endtime_rule=last_strong·strong_contact=0.3, strong_* 칸, tfinal = (strong_end 또는 t1_end) + 여유)
  [3] 변형 — Angle 줄(모든 옵션, 키 대소문자 섞음, ExcludePart 13, 중력 켬 + PresimStrongContact → 경고 한 줄·
      endtime_rule=first_recontact·v132 규칙)·AngleFile(작업 폴더 기준 상대 경로)
  [4] KMM→KMM — DROP_ATTITUDE Fast DOE 세 각도 + EndTimeTable,<[2] 의 표> → 각도 덱의 ENDTIM = 표 endtim
  [5] 오류 rc 1 — Height 없음·각도 출처 둘·없는 AngleFile·숫자 아닌 AngleFile·모르는 키·PresimStrongContact 0(덱 읽기 전),
      없는 ExcludePart·사전 해석 실패(PresimTMax 짧음)(덱 읽기 뒤 — 지난 실행의 산출 다섯 개를 지운다)
  [6] 도움말 — 모드 상세(PresimStrongContact 키), 별칭이 drop·낙하·rigid 를 다른 모드에서 뺏지 않음, format 주제의 산출 이름
  [7] PresimStrongContact 전달 — [2] 에서 강한 재접촉이 있던 각도를 문턱 100 으로 다시 → strong_end 빈칸·tfinal = t1_end + 여유

KMM 은 덱 옆에 _dump.k 를 쓰고 그 폴더로 chdir 하므로 덱은 늘 작업용 사본을 쓴다. 작업 폴더: RIGID_DROP_ENDTIME_TEST_DIR
(기본 /data/koopark/Test_RigidDropEndtime/E/test — 시작할 때 비운다).
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
PY = ROOT / "venv312" / "bin" / "python"
MINI = ROOT / "Examples" / "MinimumModel.k"
WORK = Path(os.environ.get("RIGID_DROP_ENDTIME_TEST_DIR", "/data/koopark/Test_RigidDropEndtime/E/test"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(GEN))

from KooCAEManager import KooEndTimeTable as T  # noqa: E402
from KooCAEManager.KooRigidDropEndtime import (impacts_to_deck, parse_option_lines, read_angle_file,  # noqa: E402
                                              resolve_angles, SUFFIXES)

FAILS = []
OUTS = sorted("MinimumModel" + s for s in SUFFIXES.values())
MASS_T = 1.80318e-4               # d3hsp 파트 1~22 합 (t)
V0_MM_S = math.sqrt(2 * 9810.0 * 1500.0)
WARN_STRONG = "[RigidDropEndtime] WARNING PresimStrongContact ignored with PresimGravity 1 (first re-contact rule)"


def num(text):
    """표 칸 글 → float (빈칸은 nan)."""
    return float(text) if text not in ("", None) else math.nan


def log_line(out, head):
    """출력에서 head 로 시작하는 첫 줄 (없으면 빈 글)."""
    return next((x for x in out.splitlines() if x.startswith(head)), "")


def check(name, cond, detail=""):
    print("  %-78s %s" % (name[:78], "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def option(deck, lines, mode_id=1):
    return "\n".join(["*Inputfile", str(deck), "*Mode", f"RIGID_DROP_ENDTIME,{mode_id}", f"**RigidDropEndtime,{mode_id}",
                      *lines, "**EndRigidDropEndtime", "*End"]) + "\n"


def run_kmm(work, text, timeout=900):
    """작업 폴더에 opt.txt 를 두고 소스 KMM 을 돈다 → (rc, 출력, 초)."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    (work / "opt.txt").write_text(text)
    t0 = time.time()
    r = subprocess.run([str(PY), str(GEN / "KooMeshModifier.py"), "opt.txt", str(work)], cwd=str(GEN),
                       capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr, time.time() - t0


def deck_copy(name):
    d = WORK / name
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MINI, d / MINI.name)
    return d / MINI.name


def angle_between_deg(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return math.degrees(math.acos(max(-1.0, min(1.0, float(a @ b) / (np.linalg.norm(a) * np.linalg.norm(b))))))


# ── [1] 옵션 검사 ────────────────────────────────────────────────────────────
def test_parser():
    print("[1] 옵션 검사 parse_option_lines · AngleFile · 덱 단위 환산")
    d = WORK / "parser"
    d.mkdir(parents=True, exist_ok=True)
    o = parse_option_lines(["Height,1500", "", "$ 주석", "# 주석", "FIBONACCI,12"], str(d))
    check("기본값·대소문자 무관(FIBONACCI)·빈 줄/주석 건너뜀", o["Height"] == 1500.0 and o["Fibonacci"] == 12
          and o["Restitution"] == [0.1, 0.3, 0.5] and o["Friction"] == 0.5 and o["PresimGravity"] == 0
          and o["MarginMs"] == 1.0 and o["PresimDt"] == 1e-5 and o["PresimTMax"] == 1.0 and o["Units"] is None
          and 1 <= o["Workers"] <= 8 and o["OutDir"] == os.path.abspath(d), str(o))
    from KooCAEManager import KooRigidDropPresim as P
    check(f"PresimStrongContact 기본 0.3 = 엔진 STRONG_CONTACT({getattr(P, 'STRONG_CONTACT', None)}), GivenKeys = 준 키만",
          o["PresimStrongContact"] == 0.3 == getattr(P, "STRONG_CONTACT", None) and o["GivenKeys"] == ["Fibonacci", "Height"],
          str(o))
    o = parse_option_lines(["Height,1500", "Fibonacci,12", "presimstrongcontact,0.5"], str(d))
    check("PresimStrongContact 0.5(대소문자 무관) → 값·GivenKeys", o["PresimStrongContact"] == 0.5
          and "PresimStrongContact" in o["GivenKeys"], str(o))
    for line, hint in (("HeightX,3", "did you mean 'Height'?"), ("Angles,1", "did you mean 'Angle'?"),
                       ("Restituion,0.3", "did you mean 'Restitution'?"), ("Gravity,1", "did you mean 'PresimGravity'?"),
                       ("PresimStrongContacts,0.3", "did you mean 'PresimStrongContact'?"),
                       ("StrongContact,0.3", "did you mean 'PresimStrongContact'?"),
                       ("Foo,1", "키: Height, AngleFile")):
        try:
            parse_option_lines(["Height,1500", "Fibonacci,12", line], str(d))
            msg = None
        except ValueError as e:
            msg = str(e)
        check(f"모르는 키 '{line.split(',')[0]}' → ValueError 'unknown key' + {hint}", msg is not None and "unknown key" in msg
              and hint in msg, str(msg))
    (d / "a.csv").write_text("name,pitch,roll,yaw\n# 주석\nA1,10,20,30\nA2,0,45,\n")
    (d / "b.csv").write_text("B1,1,2,3\nB2,4,5\n")
    o = parse_option_lines(["Height,10", "AngleFile,a.csv", "ExcludePart,3,4", "ExcludePart,9", "Units,mm-kg-ms",
                            "Restitution,0.2,0.4", "presimgravity,1", "Workers,3", "PresimDt,2e-5", "PresimTMax,0.2",
                            "Friction,0", "MarginMs,0"], str(d))
    check("AngleFile 은 작업 폴더 기준 절대 경로, ExcludePart 여러 줄 이어 붙임, 값 그대로",
          o["AngleFile"] == os.path.abspath(d / "a.csv") and o["ExcludePart"] == [3, 4, 9] and o["Units"] == "mm-kg-ms"
          and o["Restitution"] == [0.2, 0.4] and o["PresimGravity"] == 1 and o["Workers"] == 3, str(o))
    check("머리 줄 칸 차례(name,pitch,roll,yaw)·빈 yaw = 0",
          read_angle_file(str(d / "a.csv")) == [("A1", 20.0, 10.0, 30.0), ("A2", 45.0, 0.0, 0.0)])
    check("머리 줄 없는 csv = name,roll,pitch,yaw, yaw 없으면 0",
          read_angle_file(str(d / "b.csv")) == [("B1", 1.0, 2.0, 3.0), ("B2", 4.0, 5.0, 0.0)])
    o = parse_option_lines(["Height,10", "Angle,X,1,2,3", "angle,Y,4,5,6"], str(d))
    check("Angle 줄 여러 개 → resolve_angles", resolve_angles(o) == ([("X", 1.0, 2.0, 3.0), ("Y", 4.0, 5.0, 6.0)], "Angle lines 2"))
    try:
        resolve_angles(parse_option_lines(["Height,10", "Angle,X,1,2,3", "Angle,X,4,5,6"], str(d)))
        dup = False
    except ValueError as e:
        dup = "duplicate angle names" in str(e)
    check("각도 이름이 겹치면 ValueError", dup)
    bad = {
        "Height 없음": (["Fibonacci,3"], "Height missing"),
        "Height 0": (["Height,0", "Fibonacci,3"], "Height must be positive"),
        "각도 출처 없음": (["Height,10"], "need exactly one"),
        "각도 출처 둘(Fibonacci+Angle)": (["Height,10", "Fibonacci,3", "Angle,A,0,0,0"], "need exactly one"),
        "각도 출처 둘(AngleFile+Fibonacci)": (["Height,10", "Fibonacci,3", "AngleFile,a.csv"], "need exactly one"),
        "Height 두 번": (["Height,10", "Height,20", "Fibonacci,3"], "duplicate key"),
        "숫자 아닌 Height": (["Height,abc", "Fibonacci,3"], "bad number"),
        "정수 아닌 Fibonacci": (["Height,10", "Fibonacci,2.5"], "bad number"),
        "Angle 칸 수": (["Height,10", "Angle,A,0,0"], "bad Angle line"),
        "Restitution 범위": (["Height,10", "Fibonacci,3", "Restitution,0.3,1.5"], "0~1"),
        "PresimGravity 2": (["Height,10", "Fibonacci,3", "PresimGravity,2"], "PresimGravity"),
        "모르는 Units": (["Height,10", "Fibonacci,3", "Units,cgs"], "unknown units"),
        "값 없음": (["Height,", "Fibonacci,3"], "value missing"),
        "없는 AngleFile": (["Height,10", "AngleFile,nope.csv"], "AngleFile not found"),
        "PresimTMax ≤ PresimDt": (["Height,10", "Fibonacci,3", "PresimTMax,1e-6"], "PresimTMax"),
        "PresimStrongContact 0": (["Height,10", "Fibonacci,3", "PresimStrongContact,0"], "PresimStrongContact: 양수여야 한다"),
        "PresimStrongContact 음수": (["Height,10", "Fibonacci,3", "PresimStrongContact,-0.3"], "PresimStrongContact: 양수여야 한다"),
        "숫자 아닌 PresimStrongContact": (["Height,10", "Fibonacci,3", "PresimStrongContact,abc"], "bad number"),
        "PresimStrongContact inf": (["Height,10", "Fibonacci,3", "PresimStrongContact,inf"], "bad number"),
        "PresimStrongContact 두 번": (["Height,10", "Fibonacci,3", "PresimStrongContact,0.3", "PresimStrongContact,0.5"],
                                    "duplicate key"),
    }
    for label, (lines, marker) in bad.items():
        try:
            parse_option_lines(lines, str(d))
            msg = None
        except ValueError as e:
            msg = str(e)
        check(f"오류 {label} → ValueError '{marker}'", msg is not None and marker in msg, str(msg))
    (d / "c.csv").write_text("name,roll,pitch,yaw\nC1,abc,0,0\n")
    try:
        read_angle_file(str(d / "c.csv"))
        msg = None
    except ValueError as e:
        msg = str(e)
    check("숫자 아닌 AngleFile 칸 → ValueError(줄 번호)", msg is not None and "2번째 줄" in msg and "bad number" in msg, str(msg))
    row = {k: 0.0 for k in T.IMPACT_COLUMNS if k != "endtim_k"}
    row.update({"contact_x": 0.01, "vx": 2.0, "vn_contact": 3.0, "v0": 5.0, "wx": 100.0, "tfinal_k_ms": 3.21})
    for unit, (ln, tt, want) in {"mm-t-s": (1e-3, 1.0, (10.0, 2000.0, 3000.0, 5000.0, 100.0, 0.0033)),
                                 "mm-kg-ms": (1e-3, 1e-3, (10.0, 2.0, 3.0, 5.0, 0.1, 3.3))}.items():
        g = impacts_to_deck([row], ln, tt)[0]
        got = (g["contact_x"], g["vx"], g["vn_contact"], g["v0"], g["wx"], g["endtim_k"])
        check(f"충돌 상태 덱 단위 {unit}: mm · mm/시간 · rad/시간 · endtim_k(0.1 ms 올림)", np.allclose(got, want, rtol=1e-12), str(got))

    # 경고 줄은 중력 켬 + PresimStrongContact 를 직접 줬을 때만. 덱 대신 처음 속성을 읽을 때 멈추는 가짜를 줘
    # run_rigid_drop_endtime 을 START·경고 줄까지만 돌린다(질량특성 계산이 덱을 처음 읽는 곳에서 멈춘다)
    from KooCAEManager.KooRigidDropEndtime import run_rigid_drop_endtime

    class Halt(Exception):
        pass

    class NoDeck:
        def __getattr__(self, name):
            raise Halt(name)

    for grav, given in ((1, True), (1, False), (0, True), (0, False)):
        lines = ["Height,1500", "Angle,A,0,0,0", f"PresimGravity,{grav}"] + (["PresimStrongContact,0.5"] if given else [])
        logs, sc = [], 0.5 if given else 0.3
        try:
            run_rigid_drop_endtime(parse_option_lines(lines, str(d)), NoDeck(), str(d / "warn.k"), str(d), log=logs.append)
        except Halt:
            pass
        start = log_line("\n".join(logs), "[RigidDropEndtime] START ")
        want, shown = (1 if given else 0, "-") if grav else (0, f"{sc:g}")   # 중력 켬은 문턱을 쓰지 않아 '-'
        check(f"중력 {'켬' if grav else '끔'} · PresimStrongContact {'직접 0.5' if given else '기본'} → 경고 {want}줄, "
              f"START strong_contact={shown}", logs.count(WARN_STRONG) == want and f" strong_contact={shown} " in start,
              "\n".join(logs))


# ── [2] MinimumModel Fibonacci 30 ─────────────────────────────────────────────
def test_minimum():
    print("[2] MinimumModel — Fibonacci 30, *Inputfile 은 다른 폴더의 절대 경로")
    deck = deck_copy("fib_deck")
    work = WORK / "fib_work"
    work.mkdir(parents=True, exist_ok=True)
    rc, out, sec = run_kmm(work, option(deck, ["Height,1500", "Fibonacci,30", "Workers,4"]))
    print(f"    KMM {sec:.1f} s")
    check("rc 0 · [RigidDropEndtime] DONE · excluded=[none]", rc == 0 and "[RigidDropEndtime] DONE angles=30" in out
          and "excluded=[none]" in out, out[-2500:])
    if rc != 0:
        return None
    check("작업 폴더 = 산출 다섯 개 + opt.txt·opt.log", sorted(p.name for p in work.iterdir()) == sorted(OUTS + ["opt.log", "opt.txt"]),
          str(sorted(p.name for p in work.iterdir())))
    check("덱 옆에는 리더의 _dump.k 만 새로 생김", sorted(p.name for p in deck.parent.iterdir()) == ["MinimumModel.k", "MinimumModel_dump.k"],
          str(sorted(p.name for p in deck.parent.iterdir())))
    check("기본 .k 를 쓰지 않음(_skip_default_write)", "Default WriteModifiedFile skipped" in out)
    n_bt = out.count("pybullet build time")
    check(f"pybullet build time 줄 1번(부모가 먼저 import — fork 작업자가 다시 찍지 않음, 실제 {n_bt})", n_bt == 1)
    j = json.loads((work / "MinimumModel_rigidbody.json").read_text(encoding="utf-8"))
    pre = j.get("presim", {})
    check(f"JSON 질량 1.80318e-4 t (rel 1e-6, 실제 {j['mass']:.6e})", abs(j["mass"] / MASS_T - 1) < 1e-6)
    check("JSON presim 요약 — 각도 30·분류 합 30·중력 0·여유 1·Fibonacci 30·시간",
          pre.get("n_angles") == 30 and sum(pre.get("classes", {}).values()) == 30 and pre["params"]["gravity"] == 0
          and pre["params"]["margin_ms"] == 1.0 and pre["params"]["angle_source"] == "Fibonacci 30"
          and pre["wall_time_s"]["total"] > 0, json.dumps(pre)[:600])
    meta, rows = T.read_endtime_table(str(work / "MinimumModel_endtime.csv"))
    look = T.load_lookup(str(work / "MinimumModel_endtime.csv"))
    check("표 메타 deck·units·time_unit·height·restitution·friction·gravity·margin_ms·n_angles",
          meta.get("format") == T.FORMAT and meta.get("deck") == str(deck) and meta.get("units") == "mm-t-s"
          and meta.get("time_unit") == "s" and meta.get("height") == "1500" and meta.get("restitution") == "0.1,0.3,0.5"
          and meta.get("friction") == "0.5" and meta.get("gravity") == "0" and meta.get("margin_ms") == "1"
          and meta.get("n_angles") == "30", str(meta))
    from KooCAEManager.KooRigidDropPresim import T_SEP_MS
    check(f"표 메타 v0 = √(2·9810·1500) = {V0_MM_S:.2f} mm/s (덱 단위), t_sep_ms = 엔진 기본값 {T_SEP_MS:g}",
          abs(float(meta.get("v0", "nan")) / V0_MM_S - 1) < 1e-9 and float(meta.get("t_sep_ms", "nan")) == T_SEP_MS, str(meta))
    check("표 메타 endtime_rule=last_strong · strong_contact=0.3 (중력 끔, 기본값 — v133)",
          meta.get("endtime_rule") == "last_strong" and meta.get("strong_contact") == "0.3", str(meta))
    head_cols = next(x for x in (work / "MinimumModel_endtime.csv").read_text().splitlines() if not x.startswith("#")).split(",")
    reach = [float(r["raw"]["reach"]) for r in rows]
    check("표 칸 reach(덱 길이 mm)·n_unresolved 가 governing_e 바로 뒤, reach_m 칸 없음",
          head_cols[len(T.CORE_COLUMNS):len(T.CORE_COLUMNS) + 2] == ["reach", "n_unresolved"] and "reach_m" not in head_cols
          and all(0.0 <= x < 300.0 for x in reach), str(head_cols[:18]))
    strong_cols = ["strong_end_ms", "strong_vn_max"] + [f"strong_end_ms_e{e}" for e in ("0.1", "0.3", "0.5")]
    check("표 칸 strong_end_ms·strong_vn_max·strong_end_ms_e<e> (v133)", all(c in head_cols for c in strong_cols),
          str(head_cols))
    bad_rule, n_strong = [], 0
    for r in rows:
        x = r["raw"]
        se, vmax, t1, t2e, tf = (num(x.get(c)) for c in ("strong_end_ms", "strong_vn_max", "t1_end_ms", "t2_end_ms", "tfinal_ms"))
        n_strong += math.isfinite(se)
        if not (abs(tf - ((se if math.isfinite(se) else t1) + 1.0)) < 1e-6          # ms 그대로 — 덱 단위로 바꾸지 않음
                and math.isfinite(se) == (vmax >= 0.3 * (1 - 1e-9))                 # 강한 묶음 ⇔ 재접촉 세기 최대 ≥ 문턱 (nan 은 거짓)
                and (not math.isfinite(se) or se >= t2e - 1e-6)                     # 강한 묶음 = 첫 재접촉 묶음이거나 그 뒤
                and x.get("strong_end_ms") == x.get(f"strong_end_ms_e{x['governing_e']}")):   # 지배 e 의 값
            bad_rule.append((x["name"], x.get("strong_end_ms"), x.get("strong_vn_max"), x["t1_end_ms"], x["t2_end_ms"], x["tfinal_ms"]))
    check(f"v133 규칙: tfinal_ms = (strong_end_ms 또는 t1_end_ms) + 1 ms · strong_end ⇔ strong_vn_max ≥ 0.3 · strong_end ≥ t2_end · "
          f"지배 e 칸 (강한 재접촉 {n_strong}/30 각도)", not bad_rule and n_strong > 0, str(bad_rule[:5]))
    check(f"JSON presim: reach_max(표 칸은 10자리) = 표 최대 {max(reach):g} mm·n_unresolved_total = 표 합·v0·t_sep_ms",
          abs(pre["reach_max"] / max(reach) - 1) < 1e-9
          and pre["n_unresolved_total"] == sum(int(r["raw"]["n_unresolved"]) for r in rows)
          and abs(pre["params"]["v0"] / V0_MM_S - 1) < 1e-9 and pre["params"]["t_sep_ms"] == T_SEP_MS, json.dumps(pre)[:500])
    check("JSON presim params endtime_rule=last_strong · strong_contact 0.3",
          pre["params"].get("endtime_rule") == "last_strong" and pre["params"].get("strong_contact") == 0.3, str(pre["params"]))
    start, done = log_line(out, "[RigidDropEndtime] START "), log_line(out, "[RigidDropEndtime] DONE ")
    check("로그 START strong_contact=0.3 · DONE rule=last_strong · PresimStrongContact 경고 없음",
          " strong_contact=0.3 " in start and " rule=last_strong " in done and "WARNING PresimStrongContact" not in out,
          start + "\n" + done)
    fib = T.fibonacci_angles(30)
    check("표 30줄 = 피보나치 각도(이름·차례)", [r["name"] for r in rows] == [a[0] for a in fib]
          and all(abs(r["roll"] - a[1]) < 1e-9 and abs(r["pitch"] - a[2]) < 1e-9 for r, a in zip(rows, fib)))
    ends = [r["endtim"] for r in rows]
    check(f"endtim ∈ [0.001, 0.3] s (실제 {min(ends):g}..{max(ends):g})", min(ends) >= 0.001 and max(ends) <= 0.3)
    check("load_lookup 이 각도마다 자기 endtim 을 찾음", all(look.find(r["roll"], r["pitch"], r["yaw"]) == r["endtim"] for r in rows))
    check("JSON tfinal 요약 = 표", abs(pre["tfinal_ms"]["max"] - max(float(r["raw"]["tfinal_ms"]) for r in rows)) < 1e-9)
    imeta, imp = T.read_csv_table(str(work / "MinimumModel_impacts.csv"))
    head = (work / "MinimumModel_impacts.csv").read_text().splitlines()
    cols = next(x for x in head if not x.startswith("#")).split(",")
    check("충돌 상태 표: format=rigid_drop_endtime/impacts v1 + 같은 메타(t_sep_ms·v0·endtime_rule·strong_contact 포함), "
          "칸 = IMPACT_COLUMNS",
          imeta.get("format") == T.IMPACTS_FORMAT and cols == T.IMPACT_COLUMNS
          and all(imeta.get(k) == meta.get(k) and k in imeta for k in ("deck", "units", "height", "gravity", "t_sep_ms", "v0",
                                                                         "endtime_rule", "strong_contact")),
          str(imeta))
    k1 = [r for r in imp if r["k"] == "1"]
    check("k=1 줄이 각도 × e 마다 하나 (30 × 3)", len(k1) == 90 and {(r["name"], r["e"]) for r in k1} ==
          {(a[0], e) for a in fib for e in ("0.1", "0.3", "0.5")}, str(len(k1)))
    f = lambda r, k: float(r[k])  # noqa: E731
    worst_dir = max(angle_between_deg(T.drop_direction(f(r, "att_roll"), f(r, "att_pitch"), f(r, "att_yaw")),
                                      T.drop_direction(f(r, "roll"), f(r, "pitch"), f(r, "yaw"))) for r in k1)
    check(f"k=1 att_* 의 낙하 방향 = 입력 낙하 방향 (최대 {worst_dir:.1e}°)", worst_dir < 1e-6)
    vs = np.array([[f(r, "vx"), f(r, "vy"), f(r, "vz")] for r in k1])
    ws = np.array([[f(r, "wx"), f(r, "wy"), f(r, "wz")] for r in k1])
    check(f"k=1 v = (0, 0, −v0) mm/s, v0 = √(2·9810·1500) = {V0_MM_S:.2f}", np.allclose(vs, [0, 0, -V0_MM_S], rtol=0, atol=1e-6 * V0_MM_S)
          and all(abs(f(r, "v0") / V0_MM_S - 1) < 1e-9 for r in k1), str(vs[:2]))
    check("k=1 각속도 0", np.abs(ws).max() < 1e-9, str(np.abs(ws).max()))
    bb = np.array(j["bbox"]["min"]), np.array(j["bbox"]["max"])
    cp = np.array([[f(r, "contact_x"), f(r, "contact_y"), f(r, "contact_z")] for r in imp])
    check("접촉점은 덱 좌표 mm — 기기 bbox 안(0.01 mm 여유)", (cp >= bb[0] - 0.01).all() and (cp <= bb[1] + 0.01).all())
    from KooCAEManager.KooRigidDropPresim import endtim_from_ms
    check("endtim_k = endtim_from_ms(tfinal_k_ms) (s)", all(abs(f(r, "endtim_k") - endtim_from_ms(f(r, "tfinal_k_ms"), 1.0)) < 1e-12
                                                         for r in imp))
    check("k≥2 줄은 slapdown/rebound", all(r["class"] in ("slapdown", "rebound") for r in imp if r["k"] != "1")
          and any(r["k"] != "1" for r in imp))
    k_max = max(int(r["k"]) for r in imp)
    check(f"중력 끔 v133: 2차 묶음 뒤에도 이어 돌아 k ≥ 3 줄이 있음 (최대 k {k_max})", k_max >= 3)
    log = (work / "opt.log").read_text(encoding="utf-8")
    check("KMM 로그(opt.log)에 영어 표지 START·WROTE 다섯·DONE·[RigidBody] SUMMARY",
          "[RigidDropEndtime] START " in log and log.count("[RigidDropEndtime] WROTE ") == 5 and "[RigidDropEndtime] DONE " in log
          and "[RigidBody] SUMMARY " in log)
    return work / "MinimumModel_endtime.csv", rows


# ── [3] 변형 ─────────────────────────────────────────────────────────────────
def test_variants():
    print("[3] 변형 — Angle 줄(모든 옵션)·AngleFile(상대 경로)")
    deck = deck_copy("var_deck")
    work = WORK / "angle_work"
    lines = ["height,1000", "ANGLE,FACE,0,0,0", "Angle,EDGE45,45,0,0", "angle,CORNER,35.26,45,0", "Restitution,0.3",
             "Friction,0.3", "PresimGravity,1", "MarginMs,2", "Units,mm-t-s", "Workers,2", "PresimDt,2e-5",
             "PresimTMax,0.5", "ExcludePart,13", "PresimStrongContact,0.5"]
    rc, out, sec = run_kmm(work, option(deck, lines))
    print(f"    KMM {sec:.1f} s")
    done = next((x for x in out.splitlines() if x.startswith("[RigidDropEndtime] DONE ")), "")
    check("Angle 줄: rc 0 · DONE 줄에 뺀 파트 13(이름·이유·질량·몫)", rc == 0
          and "excluded=[13(PKG\\PKG 11, user ExcludePart, mass 1.678e-08, 0.01%)]" in done, done or out[-2000:])
    check("중력 켬 + PresimStrongContact 직접 → 경고 한 줄(그 글 그대로) · DONE rule=first_recontact",
          out.count(WARN_STRONG) == 1 and " rule=first_recontact " in done, out[-2000:])
    if rc == 0:
        meta, rows = T.read_endtime_table(str(work / "MinimumModel_endtime.csv"))
        j = json.loads((work / "MinimumModel_rigidbody.json").read_text(encoding="utf-8"))
        p = j["presim"]["params"]
        check("표 = FACE·EDGE45·CORNER, 메타 height 1000·gravity 1·margin 2·restitution 0.3·units 지정",
              [r["name"] for r in rows] == ["FACE", "EDGE45", "CORNER"] and meta["height"] == "1000" and meta["gravity"] == "1"
              and meta["margin_ms"] == "2" and meta["restitution"] == "0.3" and meta["units"] == "mm-t-s", str(meta))
        check("JSON presim params = 옵션(μ 0.3·프로세스 2·dt 2e-5·t_max 0.5·제외 [13])", p["friction"] == 0.3 and p["workers"] == 2
              and p["dt_s"] == 2e-5 and p["t_max_s"] == 0.5 and p["exclude_parts"] == [13] and j["units"]["source"] == "user", str(p))
        m13 = 1.6776001e-08   # d3hsp 파트 13
        ex = j["excluded_parts"]
        check("ExcludePart 13 → 질량 = MinimumModel − 파트 13, EXCLUDED_PART 경고(질량·몫)",
              abs(j["mass"] / (MASS_T - m13) - 1) < 1e-6 and [x["pid"] for x in ex] == [13]
              and abs(ex[0]["mass"] / m13 - 1) < 1e-6 and abs(ex[0]["mass_fraction"] - m13 / MASS_T) < 1e-6
              and any(w.startswith("EXCLUDED_PART: pid=13 ") and "% of deck mass" in w for w in j["warnings"]), str(ex))
        check("중력 켬 + e 하나 → e 칸은 0.3 만", all(r["raw"]["governing_e"] == "0.3" for r in rows))
        check("중력 켬: 메타 endtime_rule=first_recontact, strong_contact 없음 · JSON endtime_rule·strong_contact 0.5(옵션 그대로)",
              meta.get("endtime_rule") == "first_recontact" and "strong_contact" not in meta
              and p.get("endtime_rule") == "first_recontact" and p.get("strong_contact") == 0.5, f"{meta} {p}")
        check("중력 켬: strong_end_ms·strong_vn_max·strong_end_ms_e0.3 칸은 있고 모두 빈칸",
              all(r["raw"].get(c) == "" for r in rows for c in ("strong_end_ms", "strong_vn_max", "strong_end_ms_e0.3")),
              str([{c: r["raw"].get(c) for c in ("strong_end_ms", "strong_vn_max")} for r in rows]))
        v132 = [(r["name"], r["raw"]["class"], r["raw"]["t1_end_ms"], r["raw"]["t2_end_ms"], r["raw"]["tfinal_ms"]) for r in rows
                if abs(num(r["raw"]["tfinal_ms"]) - (num(r["raw"]["t2_end_ms"] if r["raw"]["class"] == "slapdown"
                                                         else r["raw"]["t1_end_ms"]) + 2.0)) > 1e-6]
        check("중력 켬 = v132 규칙: tfinal_ms = (slapdown 이면 t2_end, 아니면 t1_end) + 2 ms", not v132, str(v132))
    work = WORK / "file_work"
    work.mkdir(parents=True, exist_ok=True)
    (work / "angles.csv").write_text("name,roll,pitch,yaw\nT000,0,0,0\nT030,30,20,10\nT090,0,90,0\n")
    rc, out, sec = run_kmm(work, option(deck, ["Height,1500", "AngleFile,angles.csv", "Workers,4"]))
    print(f"    KMM {sec:.1f} s")
    check("AngleFile(작업 폴더 기준 상대 경로): rc 0", rc == 0, out[-2000:])
    if rc == 0:
        _, rows = T.read_endtime_table(str(work / "MinimumModel_endtime.csv"))
        j = json.loads((work / "MinimumModel_rigidbody.json").read_text(encoding="utf-8"))
        check("표 이름·각도 = AngleFile, 출처는 절대 경로", [(r["name"], r["roll"], r["pitch"], r["yaw"]) for r in rows]
              == [("T000", 0, 0, 0), ("T030", 30, 20, 10), ("T090", 0, 90, 0)]
              and j["presim"]["params"]["angle_source"] == f"AngleFile {os.path.abspath(work / 'angles.csv')}")


# ── [4] KMM → KMM ────────────────────────────────────────────────────────────
def drop_option(model, angles, table):
    n = len(angles)
    rep = lambda v: ",".join([str(v)] * n)  # noqa: E731
    lines = ["*Inputfile", model, "*Mode", "DROP_ATTITUDE,1", "**DropAttitude,1",
             "EulerRolling," + ",".join(a[0] for a in angles), "EulerPitching," + ",".join(a[1] for a in angles),
             "EulerYawing," + ",".join(a[2] for a in angles), "Gravity,9810", "Height," + rep(1500),
             f"EndTimeTable,{table}", "InitialVelocityX," + rep(0), "InitialVelocityY," + rep(0), "InitialVelocityZ," + rep(0),
             "InitialAngularVelocityX," + rep(0), "InitialAngularVelocityY," + rep(0), "InitialAngularVelocityZ," + rep(0),
             "OffsetDistance,0.05", "Density,7.85e-09", "YoungsModulus,200000.0", "PoissonRatio,0.3", "dt,1e-05",
             "DropSurface,Plane,0,0,0,10,10,2", "**EndDropAttitude", "*End"]
    return "\n".join(lines) + "\n"


def endtim_of(deck_path):
    lines = Path(deck_path).read_text().splitlines()
    i = lines.index("*CONTROL_TERMINATION") + 1
    while lines[i].startswith("$"):
        i += 1
    return float(lines[i][:10])


def test_kmm_to_kmm(made):
    print("[4] KMM→KMM — DROP_ATTITUDE Fast DOE 세 각도 + EndTimeTable,<[2] 의 표>")
    if made is None:
        check("[2] 표가 있어야 함", False)
        return
    table, rows = made
    picks = sorted(rows, key=lambda r: r["endtim"])
    picks = [picks[0], picks[len(picks) // 2], picks[-1]]          # 가장 짧은·가운데·가장 긴 endtim
    raw = [(r["raw"]["roll"], r["raw"]["pitch"], r["raw"]["yaw"]) for r in picks]   # 표에 적힌 글 그대로
    work = WORK / "drop_work"
    work.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MINI, work / MINI.name)
    rc, out, sec = run_kmm(work, drop_option(MINI.name, raw, table))
    print(f"    KMM {sec:.1f} s, 표 각도 {[r['name'] for r in picks]} endtim {[r['endtim'] for r in picks]}")
    check("DROP_ATTITUDE rc 0", rc == 0, out[-2500:])
    decks = sorted(work.glob("MinimumModel_[0-9][0-9][0-9]_DA_*.k"))
    check("각도 덱 셋 (Fast DOE)", len(decks) == 3, str([p.name for p in decks]))
    if len(decks) == 3:
        got = [endtim_of(p) for p in decks]
        check(f"각도 덱 ENDTIM = 표 endtim {got}", all(abs(g - r["endtim"]) <= 1e-9 * max(1.0, r["endtim"]) for g, r in zip(got, picks)))
        check("ENDTIM 이 각도마다 다름(가장 짧은 < 가장 긴)", got[0] < got[-1])
    check("로그 [EndTimeTable] 각도마다 한 줄", out.count("[EndTimeTable] roll=") == 3, out[-1500:])


# ── [7] PresimStrongContact 전달 ─────────────────────────────────────────────
def test_strong_contact(made):
    """[2](문턱 0.3)에서 강한 재접촉이 있던 각도를 문턱 100·v0(닿을 수 없는 세기)로 다시 돌린다. 값이 엔진에 닿지 않으면
    [2] 와 같은 표가 나와 strong_end 가 남는다. 문턱이 높으면 시뮬이 같은 자리에서 더 일찍 멈추기만 하므로 endtim 은 [2] 이하다."""
    print("[7] PresimStrongContact 전달 — [2] 에서 강한 재접촉이 있던 각도를 문턱 100 으로 다시")
    if made is None:
        check("[2] 표가 있어야 함", False)
        return
    picks = [r for r in made[1] if r["raw"].get("strong_end_ms")][:3]
    check(f"[2] 에 강한 재접촉 각도가 있음 {[r['name'] for r in picks]}", bool(picks))
    if not picks:
        return
    deck = deck_copy("strong_deck")
    work = WORK / "strong_work"
    lines = ["Height,1500", *(f"Angle,{r['name']},{r['raw']['roll']},{r['raw']['pitch']},{r['raw']['yaw']}" for r in picks),
             "PresimStrongContact,100", "Workers,3"]
    rc, out, sec = run_kmm(work, option(deck, lines))
    print(f"    KMM {sec:.1f} s")
    check("rc 0 · 중력 끔이라 PresimStrongContact 경고 없음", rc == 0 and "WARNING PresimStrongContact" not in out, out[-2000:])
    if rc != 0:
        return
    meta, got = T.read_endtime_table(str(work / "MinimumModel_endtime.csv"))
    j = json.loads((work / "MinimumModel_rigidbody.json").read_text(encoding="utf-8"))
    start = log_line(out, "[RigidDropEndtime] START ")
    check("메타 strong_contact=100 · endtime_rule=last_strong, JSON strong_contact 100, START strong_contact=100",
          meta.get("strong_contact") == "100" and meta.get("endtime_rule") == "last_strong"
          and j["presim"]["params"]["strong_contact"] == 100.0 and " strong_contact=100 " in start, f"{meta}\n{start}")
    before = {r["name"]: r["endtim"] for r in picks}
    seen = [(g["name"], g["raw"]["strong_end_ms"], g["raw"]["t1_end_ms"], g["raw"]["tfinal_ms"], before.get(g["name"]), g["endtim"])
            for g in got]
    check(f"문턱 100: strong_end_ms 빈칸 · tfinal = t1_end + 1 ms · endtim ≤ 문턱 0.3 의 값 {[(s[0], s[4], s[5]) for s in seen]}",
          [g["name"] for g in got] == list(before) and all(
              s[1] == "" and abs(num(s[3]) - num(s[2]) - 1.0) < 1e-6 and s[5] <= s[4] for s in seen), str(seen))


# ── [5] 오류 rc 1 ────────────────────────────────────────────────────────────
def test_errors():
    print("[5] 오류 → rc 1, 표 없음 (덱 읽기 뒤 실패는 지난 실행의 산출도 지운다)")
    deck = deck_copy("err_deck")
    cases = {   # 이름: (줄, 표지, 종류, 덱 읽기 뒤 실패인가)
        "Height 없음": (["Fibonacci,10"], "Height missing", "option error", False),
        "각도 출처 둘": (["Height,1500", "Fibonacci,10", "Angle,A,0,0,0"], "need exactly one", "option error", False),
        "없는 AngleFile": (["Height,1500", "AngleFile,nope.csv"], "AngleFile not found", "option error", False),
        "숫자 아닌 AngleFile": (["Height,1500", "AngleFile,bad.csv"], "bad number", "option error", False),
        "모르는 키 Heigth": (["Heigth,1500", "Fibonacci,10"], "did you mean 'Height'?", "option error", False),
        "PresimStrongContact 0": (["Height,1500", "Fibonacci,10", "PresimStrongContact,0"], "PresimStrongContact: 양수여야 한다",
                                  "option error", False),
        "없는 ExcludePart 999": (["Height,1500", "Fibonacci,2", "ExcludePart,999", "Workers,2"], "unknown ExcludePart",
                                "failed (ValueError)", True),
        "사전 해석 실패(PresimTMax 2e-5 s — 바닥에 닿기 전)": (["Height,1500", "Fibonacci,2", "PresimTMax,2e-5", "Workers,2"],
                                                     "no floor contact", "failed (RuntimeError)", True),
    }
    for k, (label, (lines, marker, kind, late)) in enumerate(cases.items(), 1):
        work = WORK / f"err_work{k}"
        work.mkdir(parents=True, exist_ok=True)
        (work / "bad.csv").write_text("name,roll,pitch,yaw\nA,abc,0,0\n")
        if late:   # 지난 실행이 남긴 산출 — 이번 실행이 덱을 읽은 뒤 실패해도 남으면 안 된다
            for name in OUTS:
                (work / name).write_text("STALE\n")
        rc, out, sec = run_kmm(work, option(deck, lines))
        made = {p.name for p in work.iterdir()} & {"MinimumModel_endtime.csv", "MinimumModel_impacts.csv"}
        check(f"{label}: rc 1 · '🔴 RIGID_DROP_ENDTIME {kind}' · '{marker}' · 표 없음 ({sec:.1f} s)",
              rc == 1 and f"RIGID_DROP_ENDTIME {kind}" in out and marker in out and not made, f"rc={rc} {out[-1200:]}")
        if late:
            stale = [p.name for p in work.iterdir() if p.name in OUTS and p.read_text(errors="replace") == "STALE\n"]
            check(f"{label}: 지난 산출 다섯 개를 지웠다 (REMOVED stale 다섯 줄)", not stale and out.count("REMOVED stale ") == 5,
                  str(stale))


# ── [6] 도움말 ───────────────────────────────────────────────────────────────
def test_help():
    print("[6] 도움말 — 모드 상세·별칭·format 주제")
    from KooCLIHelp import engine as E
    from KooCLIHelp.kmm_catalog import CATALOG
    top = lambda q: E.render_query(CATALOG, q)[:400]  # noqa: E731
    check("RIGID_DROP_ENDTIME 상세", top("RIGID_DROP_ENDTIME").startswith("=") and "RIGID_DROP_ENDTIME — " in top("RIGID_DROP_ENDTIME"))
    detail = E.render_query(CATALOG, "RIGID_DROP_ENDTIME")
    check("RIGID_DROP_ENDTIME 상세에 키 줄 'PresimStrongContact  [실수(v0 배수) · 기본 0.3]' (KCR 이 v133 KMM 을 이 키 이름으로 가른다)",
          "PresimStrongContact  [실수(v0 배수) · 기본 0.3]" in detail)
    for q, want in (("drop", "DROP_ATTITUDE — "), ("낙하", "DROP_ATTITUDE — "), ("rigid", "ELASTIC_TO_RIGID — "),
                    ("endtime", "RIGID_DROP_ENDTIME — "), ("사전해석", "RIGID_DROP_ENDTIME — ")):
        check(f"--help {q} → {want.split(' ')[0]}", want in top(q), top(q)[:200])
    fmt = E.render_query(CATALOG, "format")
    check("format 주제: RIGID_DROP_ENDTIME 산출 이름·빈 줄 규칙", "_endtime.csv" in fmt and "_impacts.csv" in fmt
          and re.search(r"THERMAL_LOAD·RIGID_DROP_ENDTIME 만 빈 줄", fmt) is not None)


def main():
    if not MINI.exists():
        print("SKIP Examples/MinimumModel.k 없음")
        return
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    t0 = time.time()
    test_parser()
    made = test_minimum()
    test_variants()
    test_kmm_to_kmm(made)
    test_strong_contact(made)
    test_errors()
    test_help()
    print("\n시간 %.0f s" % (time.time() - t0))
    if FAILS:
        print("FAIL %d 건" % len(FAILS))
        for x in FAILS:
            print("  -", x)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
