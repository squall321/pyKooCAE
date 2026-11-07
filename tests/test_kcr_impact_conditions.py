# KooChainRun angle_source impact_conditions(충돌 직전 상태 → 대표 충격 조건 DOE)와 harvest --impact-map 을 가짜 KMM 으로 검증하는 시험
"""
실행: venv312/bin/python tests/test_kcr_impact_conditions.py      (가짜 KMM·prepare 십여 번, 수십 초)

  [0] 꺼짐 회귀 — impact_conditions 가 없으면 runner_config·누적·대규모·배치가 바꾸기 전 코드와 바이트까지 같다
      (정답은 test_kcr_endtime_presim 의 GOLDEN — 기능을 넣기 전 코드로 뽑은 sha256)
  [1] 고르기 규칙 — 손으로 푼 예(심각도 상위 + 비최대 억제 → 최원점 → 가까운 대표), 같은 상태 묶기, 결정성,
      독립 구현(계약 모듈 RotMat)과 대조, severity_fraction 0·1, 상태보다 많은 count
  [2] 켬 + 가짜 KMM — 옵션 파일(Fibonacci·중력 켬)·호출 형식·runner_config(doe_impact_meta·doe_impact_state·
      endtime_tables·doe_endtim)·endtime.csv(time_unit)·index.json(conditions·assignments·가장 가까운 대표)
  [3] 스텝 설정 세 경로 — Euler=att, Height 0, InitialVelocity=v, RigidAngularVelocity=w(InitialAngularVelocity 줄 없음),
      EndTimeTable. 나머지 줄은 옵션 없는 설정과 같다. 배치는 DOE 목록
  [4] table 지름길 — KMM 없이 같은 고르기
  [5] 실패 — 다중 스텝·THERM·tolerance·part_doe·endtime_presim 함께·칸 빠짐·rigidbody 없음·KMM rc≠0·옵션 값 → 표식
  [6] harvest --impact-map — 가짜 result.json·simulation_index.json 으로 per_angle_risk.csv·요약·빠진 DOE 수, 기존 harvest 그대로
  [7] 수정 묶음 — σ/항복 비 지배(R3 e3)·다시 prepare 한 뒤 남은 Run 빼기·completed 먼저·sphere 건너뛰기(postprocess·prepare)
  ([4] 에 BOM 표, [5] 에 exclude_parts·RigidAngularVelocity 모르는 KMM·rc 3·v0·gravity 메타·mm-kg-ms g·presim_timeout_seconds·
   table 의 rigidbody 사전 해석 기록 없음/ExcludePart, [2] 에 endtime.csv 에 v0 없음)
"""
import contextlib
import copy
import csv
import io
import json
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(ROOT / "tests"))

import test_kcr_endtime_presim as EPT  # noqa: E402  (꺼짐 회귀 정답·prepare/러너/대규모/배치 도우미)
from KooCAEManager.KooEndTimeTable import drop_direction as contract_dir, rotation_from_euler  # noqa: E402

FAILS = []
MARK = "[IMPACT_CONDITIONS_FAILED]"

FAKE_IC_KMM = r'''#!{py}
# 가짜 KMM — RIGID_DROP_ENDTIME(Fibonacci) 옵션을 읽고 작업 폴더에 계약 모양의 <base>_impacts.csv·<base>_rigidbody.json 을 쓴다 (물리 없음)
import csv, json, math, os, sys
sys.path.insert(0, {gen!r})
from KooCAEManager.KooEndTimeTable import fibonacci_angles, rotation_from_euler
MODE = {mode!r}
if sys.argv[1:2] == ["--help"]:   # prepare 의 KMM 버전 확인 — oldhelp 은 EndTimeTable 만 아는 KMM(RigidAngularVelocity 모름)
    print("DROP_ATTITUDE — 가짜 도움말\n  EndTimeTable  [경로]")
    if MODE != "oldhelp":
        print("  RigidAngularVelocityX/Y/Z  [실수 리스트]")
    sys.exit(0)
start_cwd = os.getcwd()
opt, work = sys.argv[1], sys.argv[2]
lines = [l.rstrip("\n") for l in open(os.path.join(work, opt), encoding="utf-8")]
template = lines[lines.index("*Inputfile") + 1]
kv = dict(l.split(",", 1) for l in lines if "," in l and not l.startswith("*"))
os.chdir(os.path.dirname(template))   # 진짜 KMM 처럼 덱 폴더로 chdir
json.dump({{"argv": sys.argv, "cwd": start_cwd, "kv": kv}}, open(os.path.join(work, "fake_kmm_call.json"), "w"))
if MODE == "rc1":
    print("가짜 실패"); sys.exit(1)
if MODE == "rc3":
    print("🔴 요소 소실 (가짜)"); sys.exit(3)
base = os.path.splitext(os.path.basename(template))[0]
H = float(kv["Height"])
units, g = ("mm-kg-ms", 9.81e-3) if MODE == "mmkgms" else ("mm-t-s", 9810.0)
v0 = math.sqrt(2 * g * H)
es = [float(x) for x in kv["Restitution"].split(",")]
cols = ["name", "roll", "pitch", "yaw", "e", "k", "class", "t_start_ms", "t_end_ms", "J_over_mv0", "contact_x", "contact_y",
        "contact_z", "contact_type", "nx", "ny", "nz", "att_roll", "att_pitch", "att_yaw", "vx", "vy", "vz", "wx", "wy", "wz",
        "vn_contact", "v0", "tfinal_k_ms", "endtim_k"]
if MODE == "nocols":
    cols.remove("vn_contact")
rows = []
for i, (name, r, p, y) in enumerate(fibonacci_angles(int(kv["Fibonacci"]))):
    for e in es:
        for k in (1, 2, 3):
            if k == 3 and i % 3:
                continue
            if k == 1:   # 1차 충돌 직전 = 처음 자세·수직 낙하 — e 와 무관하게 같은 상태 (J 만 e 마다 다르다)
                att, v, w, vn, tf = (r, p, y), (0.0, 0.0, -v0), (0.0, 0.0, 0.0), v0, 1.1 + 2.0 * e
                J = (1.0 + e) * (0.35 + 0.65 * abs(math.cos(1.3 * i + 0.4)))
            else:
                att = (r + 11.0 * k + 7.0 * e, p - 13.0 * k, y + 3.0 * k)
                v = (0.1 * v0 * math.sin(i + e), 0.07 * v0 * math.cos(i * e + k), -(0.3 + 0.2 * e) * v0)
                w = (30.0 * math.sin(i + k), 20.0 * math.cos(i + e), 10.0 * math.sin(i * k + e))
                vn = (0.3 + 0.4 * abs(math.sin(i * 1.7 + e * 3.0 + k))) * v0 * (2.0 if k == 3 else 1.0)
                tf = 2.0 + 0.1 * (i % 5) + 0.3 * e
                J = (1.0 + e) * (0.2 + 0.6 * abs(math.sin(0.9 * i + k + e))) * (1.5 if k == 3 else 1.0)
            n = rotation_from_euler(*att)[:, 2]
            rows.append({{"name": name, "roll": r, "pitch": p, "yaw": y, "e": e, "k": k,
                         "class": "first" if k == 1 else ("slapdown" if i % 2 else "rebound"),
                         "t_start_ms": 0.1 * k, "t_end_ms": 0.1 * k + tf - 1.0, "J_over_mv0": J,
                         "contact_x": 1.0, "contact_y": 2.0, "contact_z": 0.5,
                         "contact_type": ("corner", "edge", "face")[i % 3],
                         "nx": float(n[0]), "ny": float(n[1]), "nz": float(n[2]),
                         "att_roll": att[0], "att_pitch": att[1], "att_yaw": att[2],
                         "vx": v[0], "vy": v[1], "vz": v[2], "wx": w[0], "wy": w[1], "wz": w[2],
                         "vn_contact": vn, "v0": v0, "tfinal_k_ms": tf,
                         "endtim_k": math.ceil(round(tf * 10.0, 6)) / 10.0 * 1e-3}})
with open(os.path.join(work, base + "_impacts.csv"), "w", newline="", encoding="utf-8-sig" if MODE == "bom" else "utf-8") as f:
    f.write("# format=rigid_drop_endtime/impacts v1\n# deck=" + template + "\n# units=" + units + "\n# time_unit="
            + ("ms" if MODE == "mmkgms" else "s") + "\n# height=" + kv["Height"]
            + "\n# v0=" + format(v0 * (1.01 if MODE == "badv0" else 1.0), ".10g")
            + "\n# restitution=" + kv["Restitution"] + "\n# friction=" + kv["Friction"]
            + "\n# gravity=" + ("0" if MODE == "grav0" else kv["PresimGravity"]) + "\n# margin_ms=" + kv["MarginMs"]
            + "\n# t_sep_ms=1\n")
    wr = csv.writer(f)
    wr.writerow(cols)
    for row in rows:
        wr.writerow([format(row[c], ".10g") if isinstance(row[c], float) else row[c] for c in cols])
if MODE != "norigid":
    rb = {{"units": {{"length": "mm"}}, "mass": 2e-4, "com": [75.0, 37.5, 3.75],
          "bbox": {{"min": [0.0, 0.0, 0.0], "max": [150.0, 75.0, 7.5]}}}}
    if MODE != "norecord":   # 진짜 KMM 처럼 사전 해석 기록(presim.params.exclude_parts)을 남긴다
        rb["presim"] = {{"params": {{"exclude_parts": [7] if MODE == "exclrb" else []}}}}
    json.dump(rb, open(os.path.join(work, base + "_rigidbody.json"), "w"))
print("fake KMM", MODE, len(rows), "rows")
'''
L_BOX = 0.5 * math.sqrt(150.0 ** 2 + 75.0 ** 2 + 7.5 ** 2)


def check(name, cond, detail=""):
    print("  %-70s %s" % (name[:70], "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def write_fake(tmp, mode="ok"):
    p = os.path.join(tmp, f"fake_ic_kmm_{mode}.py")
    Path(p).write_text(FAKE_IC_KMM.format(py=sys.executable, gen=str(GEN), mode=mode), encoding="utf-8")
    os.chmod(p, 0o755)
    return p


def scen_ic(tmp, ic=None, **env):
    """1 스텝 DROP + angle_source impact_conditions (피보나치 12 방향, 대표 6)."""
    d = EPT.scen_faces2(tmp)
    d["project_name"] = "EtpIC"
    d["scenarios"] = [{"scenario_name": "IC", "template": "model.k",
                       "angle_source": {"source_type": "impact_conditions",
                                        "impact_conditions": {"num_directions": 12, "count": 6, **(ic or {})}},
                       "cumulative": {"num_steps": 1, "mode_sequence": ["DROP"]}}]
    d["environment"].update(env)
    return d


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


# ── 독립 구현(계약 모듈 RotMat·순수 파이썬) ─────────────────────
def ref_feature(r, L):
    wd = rotation_from_euler(r["att_roll"], r["att_pitch"], r["att_yaw"]) @ [r["wx"], r["wy"], r["wz"]]
    return [r["nx"], r["ny"], r["nz"], r["vn_contact"] / r["v0"], math.hypot(r["vx"], r["vy"]) / r["v0"]] + \
        [float(x) * L / r["v0"] for x in wd]


def ref_select(cands, L, count, frac, tie=1e-3, min_d=0.2):
    """규칙을 그대로 다시 짠 것 — 같은 (자세·속도·각속도) 는 한 상태. 심각도(J·vn/v0, 묶음 최대) 순위를 내려가며 고르되
    이미 고른 심각도 상태와 min_d 보다 가까우면 건너뛴다(비최대 억제), 0.1% 묶음은 최원점 차례. 순위가 떨어지면 남은 몫은
    덮기 → 최원점 → 가까운 대표. → (대표 첫 줄들, 출처 줄들(묶음에서 심각도 최대), 묶음, 실제 심각도 몫, 가장 가까운 다른 대표 거리)"""
    key = lambda r: tuple(r[c] for c in ("att_roll", "att_pitch", "att_yaw", "vx", "vy", "vz", "wx", "wy", "wz",  # noqa
                                         "nx", "ny", "nz", "vn_contact"))
    heads, members = [], {}
    for i, r in enumerate(cands):
        if key(r) not in members:
            members[key(r)] = []
            heads.append(i)
        members[key(r)].append(i)
    row_sev = lambda i: cands[i]["J_over_mv0"] * cands[i]["vn_contact"] / cands[i]["v0"]  # noqa: E731
    F = [ref_feature(r, L) for r in cands]
    dist = lambda a, b: math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))  # noqa: E731
    n_target = min(count, len(heads))
    n_sev = min(math.ceil(round(count * frac, 9)), n_target)
    sev = [max(row_sev(i) for i in members[key(cands[h])]) for h in heads]
    order = sorted(range(len(heads)), key=lambda j: (-sev[j], j))
    mind = lambda j: min((dist(F[heads[j]], F[heads[p]]) for p in picked), default=math.inf)  # noqa: E731
    picked, i = [], 0
    while n_sev and i < len(order) and len(picked) < n_sev:
        lo = sev[order[i]] - tie * abs(sev[order[i]])
        group = []
        while i < len(order) and sev[order[i]] >= lo:
            group.append(order[i])
            i += 1
        while len(picked) < n_sev:
            pool = [j for j in group if j not in picked and mind(j) >= min_d]
            if not pool:
                break
            picked.append(pool[0] if not picked else max(pool, key=lambda j: (mind(j), -pool.index(j))))
    got_sev = len(picked)
    if not picked and n_target:
        picked = [order[0]]
    while len(picked) < n_target:
        picked.append(max((j for j in range(len(heads)) if j not in picked), key=lambda j: (mind(j), -j)))
    assign = []
    for i in range(len(cands)):
        ds = [dist(F[i], F[heads[p]]) for p in picked]
        assign.append(ds.index(min(ds)) + 1)
    sources = [max(members[key(cands[heads[j]])], key=lambda i: (row_sev(i), -i)) for j in picked]
    near = [min(dist(F[heads[a]], F[heads[b]]) for b in picked if b != a) for a in picked]
    return [heads[j] for j in picked], sources, assign, got_sev, near


# ── [0] 꺼짐 회귀 ───────────────────────────────────────────────
def test_off(kcr):
    print("[0] 꺼짐 회귀 — impact_conditions 없음 = 바꾸기 전 코드")
    tmp = EPT.new_tmp("ic_off_")
    _, _, rc_text, cum, ls, bat = EPT.all_artifacts(kcr, tmp, EPT.scen_faces2(tmp))
    got = EPT.digests(tmp, rc_text, cum, ls, bat)
    for k, v in got.items():
        check(f"{k} sha256 == 바꾸기 전", EPT.GOLDEN[k] == v, f"{v} != {EPT.GOLDEN[k]}")
    every = rc_text + "".join(cum.values()) + "".join(ls.values()) + bat
    check("RigidAngularVelocity·doe_impact_* 없음",
          "RigidAngularVelocity" not in every and "doe_impact" not in every and "impact_conditions" not in every)
    from Runner.StepConfigBuilder import build_drop_attitude_config
    base = dict(model_file="/m.k", output_dir="/o", project="P", doe_index=1, step_num=1, mode="DROP", condition="c",
                euler={"roll": 1.5, "pitch": -2.0, "yaw": 3.0}, sim_params={"height": 800, "tFinal": 0.002, "dt": 1e-5})
    check("빌더: 새 인자 None = 인자 없음 (바이트 같음)", build_drop_attitude_config(**base) == build_drop_attitude_config(
        **base, initial_velocity=None, rigid_angular_velocity=None, height=None))


# ── [1] 고르기 규칙 ─────────────────────────────────────────────
def synth(name, e, k, n, vn, vxy=0.0, att=(0.0, 0.0, 0.0), w=(0.0, 0.0, 0.0), J=1.0):
    """v0 = 1 인 손 계산용 줄 — 심각도 = J·vn."""
    return {"name": name, "roll": 0.0, "pitch": 0.0, "yaw": 0.0, "e": e, "k": k, "class": "first", "J_over_mv0": J,
            "contact_type": "face", "nx": n[0], "ny": n[1], "nz": n[2], "att_roll": att[0], "att_pitch": att[1],
            "att_yaw": att[2], "vx": vxy, "vy": 0.0, "vz": -1.0, "wx": w[0], "wy": w[1], "wz": w[2],
            "vn_contact": vn, "v0": 1.0, "endtim_k": 0.001}


def test_selection():
    print("[1] 고르기 규칙 — 손 계산·같은 상태·결정성·독립 구현 대조")
    import Runner.ImpactConditions as IC
    hand = [synth("s0", 0.1, 1, (0, 0, 1), 5.0), synth("s0", 0.3, 1, (0, 0, 1), 5.0),   # 같은 상태(e 만 다름)
            synth("s1", 0.1, 1, (0, 0, 1), 4.0), synth("s2", 0.1, 1, (0, 0, 1), 3.0),
            synth("s3", 0.1, 1, (1, 0, 0), 1.0), synth("s4", 0.1, 1, (1, 0, 0), 1.1, vxy=0.5)]
    reps, assign = IC.select_conditions(hand, 10.0, 3, 0.5)
    check("손 계산: 심각도 2(=ceil 1.5) s0·s1, 덮기 1 s3 (최원점 √11 > √10.66)",
          [hand[r["head"]]["name"] for r in reps] == ["s0", "s1", "s3"]
          and [r["pick"] for r in reps] == ["severity", "severity", "coverage"]
          and [r["severity_rank"] for r in reps] == [1, 2, "coverage"], str(reps))
    check("손 계산: 같은 상태 두 줄은 한 대표(묶음 2줄)", reps[0]["group"] == [0, 1], str(reps[0]))
    check("손 계산: 묶음 s0→1 s0'→1 s1→2 s2→2 s3→3 s4→3", [d + 1 for d, _ in assign] == [1, 1, 2, 2, 3, 3], str(assign))
    check("손 계산: 거리 s2→s1 = 1, s4→s3 = √0.26", abs(assign[3][1] - 1.0) < 1e-12
          and abs(assign[5][1] - math.sqrt(0.26)) < 1e-12 and assign[1][1] == 0.0, str(assign))
    r0, _ = IC.select_conditions(hand, 10.0, 3, 0.0)
    check("severity_fraction 0: 심각도 1위에서 덮기 시작 (모두 coverage)",
          [hand[r["head"]]["name"] for r in r0][0] == "s0" and all(r["pick"] == "coverage" for r in r0))
    r1, _ = IC.select_conditions(hand, 10.0, 3, 1.0)
    check("severity_fraction 1: 심각도 상위 3", [hand[r["head"]]["name"] for r in r1] == ["s0", "s1", "s2"])
    rall, _ = IC.select_conditions(hand, 10.0, 99, 0.5)
    check("count > 상태 수 → 상태 5개 모두", len(rall) == 5)
    # 심각도가 0.1% 안으로 같은 묶음(1차 충돌은 모두 vn = v0) — 파일 순서가 아니라 최원점으로 채운다
    tie = [synth("t0", 0.1, 1, (0, 0, 1), 1.0), synth("t1", 0.1, 1, (0, 0.0998, 0.995), 1.0004),
           synth("t2", 0.1, 1, (0, 1, 0), 1.0), synth("t3", 0.1, 1, (1, 0, 0), 1.0),
           synth("t4", 0.1, 1, (0, 0, -1), 0.9995), synth("t5", 0.1, 1, (0, 0, 1), 0.5)]
    rt, _ = IC.select_conditions(tie, 10.0, 2, 1.0)
    check("심각도 묶음(0.1% 안): 1위 t1 다음은 그 묶음의 최원점 t4 (값 순서면 t0)",
          [tie[r["head"]]["name"] for r in rt] == ["t1", "t4"] and all(r["pick"] == "severity" for r in rt),
          str([tie[r["head"]]["name"] for r in rt]))
    rt2, _ = IC.select_conditions(tie, 10.0, 3, 0.34)
    check("묶음 밖(0.5)은 심각도 몫에 안 들고, 덮기는 남은 상태 전체에서", [tie[r["head"]]["name"] for r in rt2][:2] == ["t1", "t4"]
          and rt2[2]["pick"] == "coverage", str([(tie[r["head"]]["name"], r["pick"]) for r in rt2]))
    # 심각도 = J·vn/v0 (사용자 결정 11-07). 같은 상태로 묶인 줄은 그 가운데 최대 — k=1 은 e 마다 J 가 다르다
    jj = [synth("a0", 0.1, 1, (0, 0, 1), 1.0, J=1.0), synth("a0", 0.5, 1, (0, 0, 1), 1.0, J=2.0),
          synth("a1", 0.1, 1, (1, 0, 0), 1.5, J=1.2), synth("a2", 0.1, 1, (0, 1, 0), 1.0, J=1.9),
          synth("a3", 0.1, 1, (0, 0, -1), 3.0, J=0.5)]
    rj, _ = IC.select_conditions(jj, 10.0, 2, 1.0)
    check("심각도 = J·vn/v0: a0(묶음 최대 2.0)·a2(1.9) 순 — vn 만으로 고르면 a3·a1",
          [jj[r["head"]]["name"] for r in rj] == ["a0", "a2"] and [r["severity"] for r in rj] == [2.0, 1.9],
          str([(jj[r["head"]]["name"], r["severity"]) for r in rj]))
    check("묶인 상태의 출처 줄 = 묶음에서 심각도가 가장 큰 줄(a0 의 e 0.5)", rj[0]["group"] == [0, 1] and rj[0]["source"] == 1)
    # 비최대 억제(사용자 결정 11-07) — 이미 고른 심각도 상태와 f 거리 < severity_min_distance 면 건너뛴다
    nm = [synth("p0", 0.1, 1, (0, 0, 1), 3.0), synth("p1", 0.1, 1, (0, 0, 1), 2.9),
          synth("p2", 0.1, 1, (0, 0.15, 0.989), 2.8), synth("p3", 0.1, 1, (1, 0, 0), 1.0),
          synth("p4", 0.1, 1, (0, 1, 0), 0.5)]
    name = lambda rs, src: [src[r["head"]]["name"] for r in rs]  # noqa: E731
    rn, _ = IC.select_conditions(nm, 10.0, 4, 0.5, min_distance=0.2)
    check("비최대 억제: p1(p0 과 0.1)을 건너뛰고 p0·p2(0.25), 덮기 p4·p3 — 억제 없으면 p0·p1",
          name(rn, nm) == ["p0", "p2", "p4", "p3"] and [r["pick"] for r in rn] == ["severity"] * 2 + ["coverage"] * 2,
          str(name(rn, nm)))
    check("가장 가까운 다른 대표 거리: p0↔p2 0.2503", abs(rn[0]["nearest_pick_distance"] - math.sqrt(0.15 ** 2 + 0.011 ** 2 + 0.2 ** 2))
          < 1e-12 and rn[0]["nearest_pick_distance"] == rn[1]["nearest_pick_distance"], str([r["nearest_pick_distance"] for r in rn]))
    roff, _ = IC.select_conditions(nm, 10.0, 4, 0.5, min_distance=0.0)
    check("severity_min_distance 0 = 억제 없음 (p0·p1)", name(roff, nm)[:2] == ["p0", "p1"], str(name(roff, nm)))
    rx, _ = IC.select_conditions(nm, 10.0, 4, 1.0, min_distance=3.0)
    check("순위가 다 떨어지면 남은 몫은 덮기 — 심각도 p0 하나, 덮기 p4·p3·p2",
          name(rx, nm) == ["p0", "p4", "p3", "p2"] and [r["pick"] for r in rx] == ["severity"] + ["coverage"] * 3,
          str([(name(rx, nm)[n], r["pick"]) for n, r in enumerate(rx)]))
    tn = [synth("q0", 0.1, 1, (0, 0, 1), 1.0), synth("q1", 0.1, 1, (0, 0.1, 0.995), 1.0),
          synth("q2", 0.1, 1, (0, 0, -1), 1.0), synth("q3", 0.1, 1, (1, 0, 0), 0.5)]
    rq, _ = IC.select_conditions(tn, 10.0, 3, 1.0, min_distance=0.2)
    rq0, _ = IC.select_conditions(tn, 10.0, 3, 1.0, min_distance=0.0)
    check("같은 심각도 묶음은 최원점 차례 + 거리 조건: q0·q2 다음 q1(억제) 대신 다음 묶음 q3 (억제 없으면 q1)",
          name(rq, tn) == ["q0", "q2", "q3"] and name(rq0, tn) == ["q0", "q2", "q1"] and all(r["pick"] == "severity" for r in rq),
          f"{name(rq, tn)} / {name(rq0, tn)}")
    for label, data, cnt, frac, md in (("손 계산", hand, 3, 0.5, 0.2), ("비최대 억제", nm, 4, 0.5, 0.2),
                                       ("억제·소진", nm, 4, 1.0, 3.0), ("묶음+억제", tn, 3, 1.0, 0.2), ("J", jj, 2, 1.0, 0.2)):
        got, ga = IC.select_conditions(data, 10.0, cnt, frac, min_distance=md)
        rh, rs, ra, rsev, rnear = ref_select(data, 10.0, cnt, frac, min_d=md)
        check(f"독립 구현과 같다 — {label}", [r["head"] for r in got] == rh and [d + 1 for d, _ in ga] == ra
              and sum(r["pick"] == "severity" for r in got) == rsev, f"{[r['head'] for r in got]} != {rh}")

    # 계약 모양 후보(가짜 KMM 과 같은 생성식)로 독립 구현 대조
    tmp = EPT.new_tmp("ic_sel_")
    work = os.path.join(tmp, "w")
    os.makedirs(work)
    Path(work, "o.txt").write_text(f"*Inputfile\n{tmp}/model.k\n**RigidDropEndtime,1\nHeight,1000\nFibonacci,30\n"
                                   "Restitution,0.1,0.3,0.5\nFriction,0.5\nPresimGravity,1\nMarginMs,1.0\n*End\n",
                                   encoding="utf-8")
    subprocess.run([write_fake(tmp), "o.txt", work], cwd=work, capture_output=True, encoding="utf-8", check=True)
    _, rows = IC.read_impacts_csv(os.path.join(work, "model_impacts.csv"))
    cands = [r for r in rows if r["k"] in (1, 2)]
    reps, assign = IC.select_conditions(cands, L_BOX, 20, 0.5)
    ref_heads, ref_src, ref_assign, ref_sev, ref_near = ref_select(cands, L_BOX, 20, 0.5)
    check(f"독립 구현과 같은 대표 20개 (후보 {len(cands)}줄)", [r["head"] for r in reps] == ref_heads,
          f"{[r['head'] for r in reps]} != {ref_heads}")
    check("독립 구현과 같은 묶음 (모든 후보 → 가장 가까운 대표)", [d + 1 for d, _ in assign] == ref_assign)
    check(f"심각도 몫 {ref_sev} = ceil(20·0.5), 나머지 coverage",
          sum(r["pick"] == "severity" for r in reps) == ref_sev == 10)
    check("독립 구현과 같은 출처 줄 (묶음에서 심각도 최대)", [r["source"] for r in reps] == ref_src)
    by_state = {}
    for r in cands:
        key = IC._state_key(r, L_BOX)
        by_state[key] = max(by_state.get(key, 0.0), r["J_over_mv0"] * r["vn_contact"] / r["v0"])
    top = sorted(by_state.values(), reverse=True)[:10]
    sev_vals = [r["severity"] for r in reps if r["pick"] == "severity"]
    Fs = [IC.features(cands[r["head"]], L_BOX) for r in reps if r["pick"] == "severity"]
    gap = min(math.dist(a, b) for n, a in enumerate(Fs) for b in Fs[n + 1:])
    check(f"심각도 몫: 1위 = 상태별 심각도 최대, 서로 f 거리 ≥ 0.2 (비최대 억제, 최소 {gap:.3f})",
          len(sev_vals) == 10 and sev_vals[0] == top[0] and gap >= 0.2, f"{sev_vals} vs {top}")
    check("독립 구현과 같은 '가장 가까운 다른 대표' 거리", all(
        abs(r["nearest_pick_distance"] - v) < 1e-9 for r, v in zip(reps, ref_near)))
    check("k=1 은 e 3개가 한 상태로 묶인다", sum(len(r["group"]) == 3 for r in reps if cands[r["head"]]["k"] == 1)
          == sum(cands[r["head"]]["k"] == 1 for r in reps))
    again, again_a = IC.select_conditions(cands, L_BOX, 20, 0.5)
    check("결정성: 두 번 돌려도 같다", again == reps and again_a == assign)
    worst = 0.0
    for r in cands[:40]:
        a, b = IC.rot_from_euler(r["att_roll"], r["att_pitch"], r["att_yaw"]), rotation_from_euler(
            r["att_roll"], r["att_pitch"], r["att_yaw"])
        worst = max(worst, max(abs(a[i][j] - b[i][j]) for i in range(3) for j in range(3)))
    check(f"RotMat = KooEndTimeTable.rotation_from_euler (최대 차 {worst:.1e})", worst < 1e-12)


# ── [2]·[3] 켬 + 가짜 KMM, 스텝 설정 세 경로 ───────────────────
def line_diff(text_on, text_off):
    a, b = text_on.splitlines(), text_off.splitlines()
    return [x for x in a if x not in b], [x for x in b if x not in a]


def test_enabled(kcr):
    print("[2] 켬 + 가짜 KMM — 옵션 파일·호출·runner_config·endtime.csv·index.json")
    import Runner.ImpactConditions as IC
    tmp = EPT.new_tmp("ic_on_")
    fake = write_fake(tmp, "ok")
    rc, out = EPT.designer_prepare(tmp, scen_ic(tmp, koomeshmodifier_path=fake))
    root = os.path.join(tmp, "output", "impact_conditions")
    work = os.path.join(root, "presim")
    opt = Path(work, "rigid_drop_endtime.txt").read_text(encoding="utf-8")
    want = (f"*Inputfile\n{tmp}/model.k\n*Mode\nRIGID_DROP_ENDTIME,1\n**RigidDropEndtime,1\nHeight,1000\nFibonacci,12\n"
            "Restitution,0.1,0.3,0.5\nFriction,0.5\nPresimGravity,1\nMarginMs,1.0\nWorkers,8\n"
            "**EndRigidDropEndtime\n*End\n")
    check("옵션 파일: Fibonacci,12 · 중력 켬(기본) · ExcludePart 없음 · 템플릿 절대 경로", opt == want, repr(opt))
    et = Path(root, "endtime.csv").read_text(encoding="utf-8")
    check("endtime.csv 메타에 v0 없음 (KMM NOT_PURE_DROP — 충격 조건 DOE 는 초기 속도가 있다), time_unit 은 있음",
          "# v0=" not in et and "# time_unit=s" in et, et[:300])
    call = json.load(open(os.path.join(work, "fake_kmm_call.json"), encoding="utf-8"))
    check("호출: [KMM, 옵션 이름, 작업 폴더] · cwd 작업 폴더", call["argv"] == [fake, "rigid_drop_endtime.txt", work]
          and os.path.realpath(call["cwd"]) == os.path.realpath(work), str(call))
    _, rows = IC.read_impacts_csv(os.path.join(work, "model_impacts.csv"))
    from KooCAEManager.KooEndTimeTable import IMPACT_COLUMNS, IMPACTS_FORMAT
    head = [x for x in Path(work, "model_impacts.csv").read_text(encoding="utf-8").splitlines() if not x.startswith("#")][0]
    check("가짜 KMM 표 = 계약(KooEndTimeTable IMPACT_COLUMNS·IMPACTS_FORMAT) 모양",
          head.split(",") == IMPACT_COLUMNS and f"# format={IMPACTS_FORMAT}" in Path(work, "model_impacts.csv").read_text(
              encoding="utf-8") and set(IC.REQUIRED_COLUMNS) <= set(IMPACT_COLUMNS), head)
    cands = [r for r in rows if r["k"] in (1, 2)]
    ref_heads, ref_src, ref_assign, _, ref_near = ref_select(cands, L_BOX, 6, 0.5)
    sc = rc["scenario"]
    check("DOE 6개 · 1 스텝 DROP · 이름 IC001…", sc["doe_count"] == 6 and [s["mode"] for s in sc["steps"]] == ["DROP"]
          and [sc["doe_angles"][str(d)]["1"]["angle_name"] for d in range(1, 7)] == [f"IC{d:03d}" for d in range(1, 7)])
    check("DOE 자세 = 대표 줄의 att (독립 구현의 대표 순서)",
          [(sc["doe_angles"][str(d)]["1"]["roll"], sc["doe_angles"][str(d)]["1"]["pitch"], sc["doe_angles"][str(d)]["1"]["yaw"])
           for d in range(1, 7)] == [(cands[h]["att_roll"], cands[h]["att_pitch"], cands[h]["att_yaw"]) for h in ref_heads])
    st = sc.get("doe_impact_state") or {}
    check("doe_impact_state: 속도 v·강체 각속도 w·높이 0 (바닥 좌표, 덱 단위)", all(
        st[str(d)]["1"] == {"velocity": [cands[h]["vx"], cands[h]["vy"], cands[h]["vz"]],
                            "rigid_angular_velocity": [cands[h]["wx"], cands[h]["wy"], cands[h]["wz"]], "height": 0.0}
        for d, h in enumerate(ref_heads, 1)), str(st)[:300])
    meta = sc.get("doe_impact_meta") or {}
    check("doe_impact_meta: 원래 각도·e·k·class·contact_type", all(
        meta[str(d)] == {"name": f"IC{d:03d}", "source_angle": {k: cands[h][k] for k in ("name", "roll", "pitch", "yaw")},
                         "e": cands[h]["e"], "k": cands[h]["k"], "class": cands[h]["class"],
                         "contact_type": cands[h]["contact_type"]} for d, h in enumerate(ref_src, 1)), str(meta)[:300])
    check("묶인 1차 충돌 상태는 e 0.5 줄이 출처 (J 가 가장 큼)", all(
        cands[h]["e"] == 0.5 for h in ref_src if cands[h]["k"] == 1) and any(cands[h]["k"] == 1 for h in ref_src))
    table = os.path.join(root, "endtime.csv")
    check("endtime_tables: impact_conditions/endtime.csv", sc.get("endtime_tables") == [
        {"template": f"{tmp}/model.k", "table": table, "source": "impact_conditions", "angles": 6}], str(sc.get("endtime_tables")))
    lines = Path(table).read_text(encoding="utf-8").splitlines()
    trows = read_csv(table)
    group_max = []
    for h in ref_heads:
        key = IC._state_key(cands[h], L_BOX)
        group_max.append(max(r["endtim_k"] for r in cands if IC._state_key(r, L_BOX) == key))
    check("endtime.csv: 메타 time_unit=s · 머리 name,roll,pitch,yaw,endtim", "# time_unit=s" in lines
          and "name,roll,pitch,yaw,endtim" in lines)
    check("endtime.csv: 대표마다 att·endtim = 같은 상태 줄들의 endtim_k 최대", [
        (r["name"], float(r["roll"]), float(r["pitch"]), float(r["yaw"]), float(r["endtim"])) for r in trows] == [
        (f"IC{d:03d}", cands[h]["att_roll"], cands[h]["att_pitch"], cands[h]["att_yaw"], group_max[d - 1])
        for d, h in enumerate(ref_heads, 1)], str(trows))
    check("k=1 대표의 endtim 은 e 0.5 의 값(최대)", all(
        g == 0.0021 for g, h in zip(group_max, ref_heads) if cands[h]["k"] == 1) and any(cands[h]["k"] == 1 for h in ref_heads))
    check("doe_endtim = endtime.csv 값", sc.get("doe_endtim") == {str(d): {"1": g} for d, g in enumerate(group_max, 1)})

    idx = json.load(open(os.path.join(root, "index.json"), encoding="utf-8"))
    check("index.json format·source·features",
          idx["format"] == "impact_conditions/index v1" and idx["source"]["deck"] == f"{tmp}/model.k"
          and idx["source"]["impacts_csv"] == os.path.join(work, "model_impacts.csv")
          and idx["source"]["presim"]["num_directions"] == 12 and idx["source"]["presim"]["gravity"] is True
          and idx["source"]["num_directions"] == 12 and abs(idx["features"]["L"] - L_BOX) < 1e-9
          and len(idx["features"]["definition"]) == 8, json.dumps(idx["source"])[:300])
    conds = idx["conditions"]
    check("index conditions: DOE·이름·원래 줄·묶인 수·심각도 순위",
          [c["doe"] for c in conds] == list(range(1, 7)) and [c["source"]["name"] for c in conds]
          == [cands[h]["name"] for h in ref_heads] and sum(c["n_members"] for c in conds) == len(cands)
          and [c["severity_rank"] for c in conds] == [1, 2, 3, "coverage", "coverage", "coverage"]
          and all(set(c["source"]) >= {"name", "roll", "pitch", "yaw", "e", "k", "class", "contact_type", "vn_contact",
                                        "J_over_mv0", "v", "w", "att", "endtim_k"} for c in conds), json.dumps(conds[0])[:300])
    sev_ref = [cands[h]["J_over_mv0"] * cands[h]["vn_contact"] / cands[h]["v0"] for h in ref_src]
    check("index: 심각도 정의(J_over_mv0·vn_contact/v0) 기록 · 조건마다 심각도 값 = 출처 줄의 J·vn/v0",
          "J_over_mv0·vn_contact/v0" in idx["features"]["selection"]["severity"]
          and all(abs(c["severity"] - v) < 1e-12 for c, v in zip(conds, sev_ref))
          and [c["source"]["e"] for c in conds] == [cands[h]["e"] for h in ref_src], str([c["severity"] for c in conds]))
    check("index: severity_min_distance 0.2 · severity_quota 3 · 조건마다 가장 가까운 다른 대표 거리(독립 구현)",
          idx["features"]["selection"]["severity_min_distance"] == 0.2 and idx["features"]["selection"]["severity_quota"] == 3
          and all(abs(c["nearest_pick_distance"] - v) < 1e-9 for c, v in zip(conds, ref_near)),
          str([c.get("nearest_pick_distance") for c in conds]))
    asg = idx["assignments"]
    check(f"index assignments: 후보 {len(cands)}줄 모두, k=3 없음", len(asg) == len(cands) and all(a["k"] in (1, 2) for a in asg))
    check("index assignments: 가장 가까운 대표 = 독립 구현", [a["doe"] for a in asg] == ref_assign)
    dd = max(max(abs(a[c] - float(v)) for c, v in zip(("dx", "dy", "dz"), contract_dir(a["roll"], a["pitch"], a["yaw"])))
             for a in asg)
    check(f"index assignments: dx·dy·dz = 원래 각도 낙하 방향 (최대 차 {dd:.1e})", dd < 1e-12)
    check("prepare 출력에 요약", "충격 조건 DOE 6개" in out and "심각도 상위 3" in out, out[-300:])
    t3 = EPT.new_tmp("ic_nms_")
    rc3, out3 = EPT.designer_prepare(t3, scen_ic(t3, {"table": os.path.join(work, "model_impacts.csv"),
                                                      "severity_min_distance": 50.0}, koomeshmodifier_path=fake))
    sel3 = json.load(open(os.path.join(t3, "output", "impact_conditions", "index.json"), encoding="utf-8"))["features"]["selection"]
    check("severity_min_distance 가 커서 심각도 몫을 못 채우면 경고하고 남은 몫은 덮기 (1 + 5)",
          "severity quota not filled" in out3 and sel3["n_severity"] == 1 and sel3["n_coverage"] == 5
          and sel3["severity_quota"] == 3 and rc3["scenario"]["doe_count"] == 6, out3[-300:])
    return rc, tmp, cands, ref_heads


def test_three_paths(kcr, on):
    print("[3] 스텝 설정 세 경로 — 높이 0·초기 속도·강체 각속도·EndTimeTable")
    from Runner.StepConfigBuilder import build_drop_attitude_config
    rc, tmp, cands, heads = on
    table = rc["scenario"]["endtime_tables"][0]["table"]
    cum = EPT.runner_step_configs(rc)
    ok = len(cum) == 6
    for d, h in enumerate(heads, 1):
        r = cands[h]
        text = cum[f"step_config_doe{d:03d}_s001.txt"]
        plain = build_drop_attitude_config(model_file=rc["project"]["model_file"], output_dir=rc["project"]["output_dir"],
                                           project=rc["project"]["name"], doe_index=d, step_num=1, mode="DROP",
                                           condition=f"IC{d:03d}", euler={"roll": r["att_roll"], "pitch": r["att_pitch"],
                                                                          "yaw": r["att_yaw"]},
                                           sim_params=rc["simulation_params"], run_directory_mode=True, preserve_includes=[])
        added, removed = line_diff(text, plain)
        want_add = ["Height,0.0", f"InitialVelocityX,{r['vx']}", f"InitialVelocityY,{r['vy']}", f"InitialVelocityZ,{r['vz']}",
                    f"RigidAngularVelocityX,{r['wx']}", f"RigidAngularVelocityY,{r['wy']}",
                    f"RigidAngularVelocityZ,{r['wz']}", f"EndTimeTable,{table}"]
        want_rm = ["Height,1000", "InitialVelocityX,0", "InitialVelocityY,0", "InitialVelocityZ,0",
                   "InitialAngularVelocityX,0", "InitialAngularVelocityY,0", "InitialAngularVelocityZ,0"]
        if (sorted(added) != sorted(want_add) or sorted(removed) != sorted(want_rm)
                or f"EulerRolling,{r['att_roll']}" not in text.splitlines()):
            ok = False
            print("    ", d, added, removed)
    check("누적 러너: 옵션 없는 설정 + 높이 0·v·w·EndTimeTable 만 다르다 (6 DOE)", ok)
    check("누적 러너: InitialAngularVelocity 줄 없음 (RigidAngularVelocity 와 함께 못 쓴다)",
          all("InitialAngularVelocity" not in t for t in cum.values()))
    ls = EPT.large_scale_configs(os.path.join(tmp, "runner_config.json"), os.path.join(tmp, "ls_root"))
    ls_cfg = {k.split("/")[1]: v for k, v in ls.items() if k.endswith("step_config.txt")}
    ok = len(ls_cfg) == 6
    for d, h in enumerate(heads, 1):
        t, r = ls_cfg[f"runid_{d - 1:05d}"].splitlines(), cands[h]
        ok &= all(x in t for x in ("Height,0.0", f"InitialVelocityX,{r['vx']}", f"RigidAngularVelocityZ,{r['wz']}",
                                   f"EndTimeTable,{table}", f"EulerPitching,{r['att_pitch']}"))
    check("대규모: doe_index 0-based → 표 1-based 로 같은 값", ok)
    bat, _ = EPT.batch_config(kcr, rc)
    bl = bat.splitlines()
    vals = lambda key: [c for c in bl if c.startswith(key + ",")]  # noqa: E731
    ok = (vals("Height") == ["Height," + ",".join(["0.0"] * 6)]
          and vals("InitialVelocityY") == ["InitialVelocityY," + ",".join(str(cands[h]["vy"]) for h in heads)]
          and vals("RigidAngularVelocityX") == ["RigidAngularVelocityX," + ",".join(str(cands[h]["wx"]) for h in heads)]
          and vals("EulerRolling") == ["EulerRolling," + ",".join(str(cands[h]["att_roll"]) for h in heads)]
          and not vals("InitialAngularVelocityX") and vals("EndTimeTable") == [f"EndTimeTable,{table}"])
    check("배치(Fast DOE): DOE 목록 높이 0·v·w·att · EndTimeTable 한 줄", ok, bat[:600])


# ── [4] table 지름길 ────────────────────────────────────────────
def test_table(kcr, on):
    print("[4] table 지름길 — KMM 없이 같은 고르기")
    rc, tmp, _, _ = on
    src = os.path.join(tmp, "output", "impact_conditions", "presim")
    t2 = EPT.new_tmp("ic_tbl_")
    os.makedirs(os.path.join(t2, "pre"))
    for n in ("model_impacts.csv", "model_rigidbody.json"):
        Path(t2, "pre", n).write_bytes(Path(src, n).read_bytes())
    fake = write_fake(t2, "rc1")   # 불리면 실패
    rc2, out = EPT.designer_prepare(t2, scen_ic(t2, {"table": "pre/model_impacts.csv"}, koomeshmodifier_path=fake))
    a, b = rc["scenario"], rc2["scenario"]
    check("같은 대표·상태·종료 시간", a["doe_angles"] == b["doe_angles"] and a["doe_impact_state"] == b["doe_impact_state"]
          and a["doe_endtim"] == b["doe_endtim"])
    idx = json.load(open(os.path.join(t2, "output", "impact_conditions", "index.json"), encoding="utf-8"))
    check("index source.presim = {table}, KMM 안 부름", idx["source"]["presim"] == {"table": os.path.join(t2, "pre", "model_impacts.csv")}
          and not os.path.exists(os.path.join(t2, "output", "impact_conditions", "presim")))
    t3 = EPT.new_tmp("ic_tbl_bom_")
    os.makedirs(os.path.join(t3, "pre"))
    Path(t3, "pre", "model_impacts.csv").write_bytes("\ufeff".encode("utf-8") + Path(src, "model_impacts.csv").read_bytes())
    Path(t3, "pre", "model_rigidbody.json").write_bytes("\ufeff".encode("utf-8") + Path(src, "model_rigidbody.json").read_bytes())
    try:
        rc3, _ = EPT.designer_prepare(t3, scen_ic(t3, {"table": "pre/model_impacts.csv"}, koomeshmodifier_path=fake))
        same = rc3["scenario"]["doe_impact_state"] == a["doe_impact_state"]
    except Exception as e:
        same = repr(e)
    check("BOM(엑셀 저장) 붙은 impacts.csv·rigidbody.json 도 같은 대표", same is True, str(same))


# ── [5] 실패 ────────────────────────────────────────────────────
def test_errors(kcr):
    print("[5] 실패 — 표식 붙은 오류")
    import Runner.ImpactConditions as IC

    def expect(label, user_fn, words, mode="ok", cli=False):
        tmp = EPT.new_tmp("ic_err_")
        user = user_fn(tmp, write_fake(tmp, mode))
        if cli:
            code, out = EPT.cli_prepare(tmp, user)
            ok = code != 0 and MARK in out and all(w in out for w in words) \
                and not os.path.exists(os.path.join(tmp, "runner_config.json"))
            check(f"{label} (CLI 종료 코드 {code})", ok, out[-600:])
            return
        try:
            EPT.designer_prepare(tmp, user)
            check(label, False, "오류 없음")
        except IC.ImpactConditionsError as e:
            check(label, MARK in str(e) and all(w in str(e) for w in words), str(e))

    def multi(t, f):
        u = scen_ic(t, koomeshmodifier_path=f)
        u["scenarios"][0]["cumulative"] = {"num_steps": 2, "mode_sequence": ["DROP", "DROP"]}
        return u

    def therm(t, f):
        u = scen_ic(t, koomeshmodifier_path=f)
        u["scenarios"][0]["cumulative"] = {"num_steps": 2, "mode_sequence": ["THERM", "DROP"]}
        u["scenarios"][0]["thermal_conditions"] = ["HOT"]
        return u

    def tol(t, f):
        u = scen_ic(t, koomeshmodifier_path=f)
        u["scenarios"][0]["tolerance"] = {"doe_type": "lhs", "doe_count": 3, "roll": {"tolerance": 5.0}}
        return u

    def part(t, f):
        u = scen_ic(t, koomeshmodifier_path=f)
        u["scenarios"][0]["part_doe"] = {"sampling": {"method": "explicit"}, "cases": [{"name": "M", "moves": [{"pid": 1, "dx": 1}]}]}
        return u

    def both(t, f):
        u = scen_ic(t, koomeshmodifier_path=f)
        u["simulation_params"]["endtime_presim"] = {"enabled": True}
        return u

    expect("다중 스텝", multi, ["1 스텝 DROP", "unsupported scenario"])
    expect("THERM→DROP", therm, ["1 스텝 DROP"])
    expect("tolerance 함께", tol, ["tolerance"])
    expect("part_doe 함께", part, ["part_doe"])
    expect("endtime_presim 함께", both, ["endtime_presim"], cli=True)
    expect("impacts.csv 칸 빠짐 (vn_contact)", lambda t, f: scen_ic(t, koomeshmodifier_path=f), ["missing columns", "vn_contact"],
           mode="nocols")
    expect("rigidbody.json 없음", lambda t, f: scen_ic(t, koomeshmodifier_path=f), ["model_rigidbody.json", "output not written"],
           mode="norigid")
    expect("KMM 종료 코드 1", lambda t, f: scen_ic(t, koomeshmodifier_path=f), ["종료 코드 1", "KMM rc=1"], mode="rc1", cli=True)
    expect("옵션 값 오류 (count 0)", lambda t, f: scen_ic(t, {"count": 0}, koomeshmodifier_path=f), ["count", "bad value"])
    expect("table 없음", lambda t, f: scen_ic(t, {"table": "nope_impacts.csv"}, koomeshmodifier_path=f), ["table not found"])

    def no_rigid_table(t, f):
        Path(t, "x_impacts.csv").write_text("name,roll\n", encoding="utf-8")
        return scen_ic(t, {"table": "x_impacts.csv"}, koomeshmodifier_path=f)
    expect("table 옆 rigidbody.json 없음", no_rigid_table, ["x_rigidbody.json", "rigidbody json not found"])

    def impacts_k(t, f):
        return scen_ic(t, {"impacts": [5]}, koomeshmodifier_path=f)
    expect("후보 없음 (impacts [5])", impacts_k, ["no candidates"])
    # 이번 수정 — 사용자 결정(버전 확인·rc 3·표 메타·exclude_parts)과 R3(시간 제한 키·table 사전 해석 기록·중력 메타)
    expect("exclude_parts [7] → 쓸 수 없다 (10% SPC 규칙 안내)",
           lambda t, f: scen_ic(t, {"exclude_parts": [7]}, koomeshmodifier_path=f),
           ["exclude_parts unsupported", "10%", "SPC_ON_DEVICE_PART"])
    expect("러너 KMM 이 RigidAngularVelocityX 를 모름 (EndTimeTable 만 아는 도움말)",
           lambda t, f: scen_ic(t, koomeshmodifier_path=f), ["KMM version skew", "RigidAngularVelocityX"], mode="oldhelp",
           cli=True)
    expect("KMM 종료 코드 3 (덱 요소 소실)", lambda t, f: scen_ic(t, koomeshmodifier_path=f),
           ["요소를 버렸다", "model_rigidbody.json", "KMM rc=3 element loss"], mode="rc3", cli=True)
    expect("표 메타 v0 가 이 낙하 √(2gh) 와 다름", lambda t, f: scen_ic(t, koomeshmodifier_path=f),
           ["v0", "table drop mismatch"], mode="badv0")
    expect("표 메타 gravity 0 ≠ 옵션 gravity true", lambda t, f: scen_ic(t, koomeshmodifier_path=f),
           ["사전 해석 중력", "table drop mismatch"], mode="grav0")
    expect("mm-kg-ms 덱인데 simulation_params.gravity 없음", lambda t, f: scen_ic(t, koomeshmodifier_path=f),
           ["mm-kg-ms", "0.00981", "gravity required for mm-kg-ms"], mode="mmkgms")
    expect("presim_timeout_seconds 0 → 값 오류", lambda t, f: scen_ic(t, {"presim_timeout_seconds": 0}, koomeshmodifier_path=f),
           ["presim_timeout_seconds", "bad value"])

    def table_from(mode):
        def build(t, f):
            src = EPT.new_tmp("ic_src_")
            pre = scen_ic(src, koomeshmodifier_path=write_fake(src, mode))
            with contextlib.redirect_stdout(io.StringIO()):
                try:
                    EPT.designer_prepare(src, pre)
                except IC.ImpactConditionsError:
                    pass
            for n in ("model_impacts.csv", "model_rigidbody.json"):
                Path(t, n).write_bytes(Path(src, "output", "impact_conditions", "presim", n).read_bytes())
            return scen_ic(t, {"table": "model_impacts.csv"}, koomeshmodifier_path=f)
        return build
    expect("table 옆 rigidbody.json 에 사전 해석 기록 없음", table_from("norecord"), ["rigidbody presim record missing"])
    expect("table 의 사전 해석이 ExcludePart 로 돌았음", table_from("exclrb"), ["ExcludePart [7]", "exclude_parts unsupported"])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        IC.impact_options({"count": 3, "bogus": 1})
    check("모르는 키는 경고만", "bogus" in buf.getvalue() and "모르는 키" in buf.getvalue())


# ── [6] harvest --impact-map ───────────────────────────────────
def test_harvest(kcr, on):
    print("[6] harvest --impact-map — per_angle_risk.csv·요약·빠진 DOE")
    rc, tmp, cands, heads = on
    out = rc["project"]["output_dir"]
    runs, peaks = {}, {}
    for d in range(1, 7):
        if d == 4:
            continue   # DOE 4 는 결과 없음
        for n, stamp in ((0, "20261107_100000"), (1, "20261107_120000")) if d == 2 else ((1, "20261107_110000"),):
            folder = f"Run_{stamp}_d{d}{n}"
            p1, p2 = 100.0 + 10 * d + 500 * (n == 0 and d == 2), 50.0 + 40 * d   # DOE 2 는 늦은 Run(n=1)이 써야 한다
            os.makedirs(os.path.join(out, folder, "Output", "report"))
            json.dump({"parts": {"1": {"name": "Case", "peak_stress": p1}, "2": {"name": "Chip", "peak_stress": p2}}},
                      open(os.path.join(out, folder, "Output", "report", "result.json"), "w"))
            runs[f"EtpIC_CUM001_DOE{d:03d}_S001_DROP_IC{d:03d}_{n}"] = {"run_id": folder[4:], "status": "completed",
                                                                         "folder": folder}
            peaks[d] = max((p1, "1", "Case"), (p2, "2", "Chip"), key=lambda x: x[0])
    json.dump({"project": "EtpIC", "scenarios": [{"runs": runs}]}, open(os.path.join(out, "simulation_index.json"), "w"))
    r = subprocess.run([sys.executable, str(ROOT / "KooChainRun"), "harvest", "--impact-map", tmp, "--yield", "200"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    txt = r.stdout + r.stderr
    check("종료 코드 0 · 빠진 DOE 1개(4) 출력", r.returncode == 0 and "5/6 결과 있음" in txt and "없음 1개: 4" in txt, txt[-500:])
    rows = read_csv(os.path.join(tmp, "per_angle_risk.csv"))
    idx = json.load(open(os.path.join(out, "impact_conditions", "index.json"), encoding="utf-8"))
    check("per_angle_risk.csv 칸 순서", list(rows[0]) == ["angle", "roll", "pitch", "yaw", "dx", "dy", "dz", "e", "k", "doe",
                                                     "distance", "peak_stress", "worst_pid", "worst_part", "ratio"])
    ok = len(rows) == len(idx["assignments"])
    for row, a in zip(rows, idx["assignments"]):
        ok &= row["angle"] == a["angle"] and int(row["doe"]) == a["doe"] and int(row["k"]) == a["k"]
        if a["doe"] == 4:
            ok &= row["peak_stress"] == row["worst_pid"] == row["ratio"] == ""
        else:
            pk, pid, nm = peaks[a["doe"]]
            ok &= (abs(float(row["peak_stress"]) - pk) < 1e-9 and row["worst_pid"] == pid and row["worst_part"] == nm
                   and abs(float(row["ratio"]) - pk / 200.0) < 1e-12)
    check(f"배정 {len(rows)}줄마다 대표 DOE 의 최대 응력·파트·비(--yield 200), DOE 4 는 빈칸", ok)
    check("같은 DOE 를 두 번 돌렸으면 늦은 Run 값 (DOE 2 = 130, 이른 Run 의 620 아님)",
          all(abs(float(x["peak_stress"]) - peaks[2][0]) < 1e-9 for x in rows if x["doe"] == "2") and peaks[2][0] == 130.0)
    summ = read_csv(os.path.join(tmp, "per_angle_risk_summary.csv"))
    exp = {}
    for a in idx["assignments"]:
        e = exp.setdefault(a["angle"], {"n": 0, "miss": 0, "peak": None})
        e["n"] += 1
        if a["doe"] == 4:
            e["miss"] += 1
        elif e["peak"] is None or peaks[a["doe"]][0] > e["peak"]:
            e["peak"] = peaks[a["doe"]][0]
    ok = len(summ) == len(exp) == 12
    for s in summ:
        e = exp[s["angle"]]
        ok &= int(s["n_impacts"]) == e["n"] and int(s["n_missing"]) == e["miss"] and (
            s["peak_stress"] == "" if e["peak"] is None else abs(float(s["peak_stress"]) - e["peak"]) < 1e-9)
    check("요약: 원래 각도 12개마다 e·k 가운데 최대, 빠진 수", ok, str(summ[:2]))
    r2 = subprocess.run([sys.executable, str(ROOT / "KooChainRun"), "harvest", "--impact-map", EPT.new_tmp("ic_noidx_")],
                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    check("index.json 없는 폴더 → 종료 코드 1 + 표식", r2.returncode == 1 and MARK in r2.stdout and "index not found" in r2.stdout)
    rc_plain = copy.deepcopy(rc)
    plain_dir = EPT.new_tmp("ic_plain_")
    json.dump(rc_plain, open(os.path.join(plain_dir, "runner_config.json"), "w"))
    os.makedirs(os.path.join(plain_dir, "Run_3", "Output", "report"))   # Run_<doe> 폴백으로 DOE 3 각도가 붙는다
    json.dump({"parts": {"1": {"name": "Case", "peak_stress": 99.0}}},
              open(os.path.join(plain_dir, "Run_3", "Output", "report", "result.json"), "w"))
    r3 = subprocess.run([sys.executable, str(ROOT / "KooChainRun"), "harvest", plain_dir],
                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    check("--impact-map 없이: 기존 수확 그대로 (risk_angles.json, per_angle_risk 없음)", r3.returncode == 0
          and os.path.exists(os.path.join(plain_dir, "risk_angles.json"))
          and not os.path.exists(os.path.join(plain_dir, "per_angle_risk.csv")), r3.stdout[-400:])


# ── [7] harvest·sphere 수정 (R3) ─────────────────────────────────
def test_harvest_r3(on):
    print("[7] harvest --impact-map 수정 — σ/항복 비 지배·지난 prepare 의 Run 빼기·completed 먼저 / sphere 건너뛰기")
    import Runner.ImpactConditions as IC
    tmp = EPT.new_tmp("ic_hv3_")
    out = os.path.join(tmp, "output")
    os.makedirs(os.path.join(out, "impact_conditions"))
    json.dump({"project": {"output_dir": out}}, open(os.path.join(tmp, "runner_config.json"), "w"))
    conds = [{"doe": d, "name": f"IC{d:03d}", "source": {"att": [10.0 * d, 0.0, 0.0], "v": [0.0, 0.0, -100.0],
                                                           "w": [0.0, 1.5, 0.0]}} for d in (1, 2, 3)]
    asg = [{"angle": n, "roll": 0, "pitch": 0, "yaw": 0, "dx": 0, "dy": 0, "dz": -1, "e": 0.3, "k": k, "doe": d,
            "distance": 0.0} for n, k, d in (("P1", 1, 1), ("P1", 2, 2), ("P2", 1, 3))]
    json.dump({"format": IC.INDEX_FORMAT, "conditions": conds, "assignments": asg},
              open(os.path.join(out, "impact_conditions", "index.json"), "w"))
    runs = {}

    def run(d, n, stamp, parts, status="completed", att=None):
        folder = f"Run_{stamp}_d{d}{n}"
        os.makedirs(os.path.join(out, folder, "Output", "report"))
        json.dump({"parts": parts}, open(os.path.join(out, folder, "Output", "report", "result.json"), "w"))
        a = 10.0 * d if att is None else att
        Path(out, folder, "step_config.txt").write_text(
            f"*Mode\nDROP_ATTITUDE,1\n**DropAttitude,1\nEulerRolling,{a}\nEulerPitching,0.0\nEulerYawing,0.0\nHeight,0.0\n"
            "InitialVelocityX,0.0\nInitialVelocityY,0.0\nInitialVelocityZ,-100.0\nRigidAngularVelocityX,0.0\n"
            "RigidAngularVelocityY,1.5\nRigidAngularVelocityZ,0.0\n**EndDropAttitude\n*End\n", encoding="utf-8")
        runs[f"Hv_CUM001_DOE{d:03d}_S001_DROP_IC{d:03d}_{n}"] = {"run_id": folder[4:], "status": status, "folder": folder}
    case, chip = lambda v: {"name": "Case", "peak_stress": v}, lambda v: {"name": "Chip", "peak_stress": v}
    run(1, 0, "20261107_100001", {"1": case(300.0), "2": chip(150.0)})   # R3 e3: Case 300/350, Chip 150/120 = 1.25
    run(2, 0, "20261107_100002", {"1": case(320.0), "2": chip(60.0)})    # Case 320/350 = 0.914
    run(2, 1, "20261107_200002", {"1": case(9999.0)}, att=55.0)          # 다시 prepare 하기 전 Run — 늦고 커도 뺀다
    run(3, 0, "20261107_100003", {"1": case(100.0)})
    run(3, 1, "20261107_200003", {"1": case(7777.0)}, status="failed")    # 뒤에 실패한 재실행이 결과를 남겼다
    json.dump({"scenarios": [{"runs": runs}]}, open(os.path.join(out, "simulation_index.json"), "w"))

    def harvest(*extra):
        r = subprocess.run([sys.executable, str(ROOT / "KooChainRun"), "harvest", "--impact-map", tmp, *extra],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        return (r.returncode, r.stdout + r.stderr, {x["doe"]: x for x in read_csv(os.path.join(tmp, "per_angle_risk.csv"))},
                {x["angle"]: x for x in read_csv(os.path.join(tmp, "per_angle_risk_summary.csv"))})
    code, txt, rows, summ = harvest("--yield-by-part", "1:350,2:120")
    check("종료 코드 0", code == 0, txt[-400:])
    check("DOE 1: σ/항복 비가 큰 Chip(150/120 = 1.25) 지배 — 최대 응력 Case(300) 아님, peak_stress 는 그 파트 응력",
          rows["1"]["worst_part"] == "Chip" and abs(float(rows["1"]["ratio"]) - 1.25) < 1e-12
          and float(rows["1"]["peak_stress"]) == 150.0, str(rows.get("1")))
    check("DOE 2: 다시 prepare 하기 전 Run(자세 55°, 9999)은 빼고 수를 찍는다 → Case 320",
          rows["2"]["worst_part"] == "Case" and float(rows["2"]["peak_stress"]) == 320.0
          and "Run 1개는 뺐다" in txt and "stale runs skipped" in txt, txt[-600:])
    check("DOE 3: 늦게 실패한 재실행(7777)이 completed(100)를 덮지 않는다", float(rows["3"]["peak_stress"]) == 100.0)
    p1 = summ["P1"]
    check("요약 P1: 비 1.25(DOE 1)가 지배 — 응력이 더 큰 DOE 2(320, 비 0.914) 아님",
          p1["governing_doe"] == "1" and p1["worst_part"] == "Chip" and abs(float(p1["ratio"]) - 1.25) < 1e-12, str(p1))
    code, txt, rows, summ = harvest()
    check("항복강도가 없으면 예전처럼 최대 응력: DOE 1 Case 300 · 요약 P1 은 DOE 2(320)",
          code == 0 and rows["1"]["worst_part"] == "Case" and float(rows["1"]["peak_stress"]) == 300.0
          and summ["P1"]["governing_doe"] == "2" and rows["1"]["ratio"] == "", str(rows.get("1")))

    # sphere — 충격 조건 runner_config 는 전각도 sphere 를 돌리지 않는다. 보통 시나리오는 그대로
    rc_ic, ic_tmp = on[0], on[1]
    r = subprocess.run([sys.executable, str(ROOT / "KooChainRun"), "postprocess", os.path.join(ic_tmp, "runner_config.json"),
                        "--sphere"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    check("postprocess --sphere: 충격 조건이면 종료 코드 1 + harvest --impact-map 안내",
          r.returncode == 1 and "sphere report skipped for impact_conditions" in r.stdout and "--impact-map" in r.stdout,
          r.stdout[-400:])
    t_plain = EPT.new_tmp("ic_sph_plain_")
    EPT.designer_prepare(t_plain, EPT.scen_faces2(t_plain))
    r2 = subprocess.run([sys.executable, str(ROOT / "KooChainRun"), "postprocess", os.path.join(t_plain, "runner_config.json"),
                         "--sphere"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    check("보통 DROP 시나리오는 sphere 그대로 (안내 없음)", "impact_conditions" not in r2.stdout, r2.stdout[-300:])
    pp = {"enabled": True, "sif_path": "/opt/apptainers/KooD3plotReader.sif", "auto_sphere": True}
    t_ic = EPT.new_tmp("ic_sph_pp_")
    u = scen_ic(t_ic, koomeshmodifier_path=write_fake(t_ic, "ok"))
    u["postprocess"] = pp
    rc_pp, out_pp = EPT.designer_prepare(t_ic, u)
    t_n = EPT.new_tmp("ic_sph_pp_plain_")
    u2 = EPT.scen_faces2(t_n)
    u2["postprocess"] = pp
    EPT.designer_prepare(t_n, u2)
    check("prepare: 충격 조건이면 sphere_report.sh 를 쓰지 않고 알린다 · 보통 시나리오는 쓴다",
          not os.path.exists(os.path.join(t_ic, "output", "sphere_report.sh")) and "sphere report skipped" in out_pp
          and os.path.exists(os.path.join(t_n, "output", "sphere_report.sh")) and IC.is_impact_conditions(rc_pp)
          and not IC.is_impact_conditions(json.load(open(os.path.join(t_n, "runner_config.json"), encoding="utf-8"))))


def main():
    with contextlib.redirect_stdout(io.StringIO()):
        kcr = EPT.load_kcr()
    test_off(kcr)
    test_selection()
    on = test_enabled(kcr)
    test_three_paths(kcr, on)
    test_table(kcr, on)
    test_errors(kcr)
    test_harvest(kcr, on)
    test_harvest_r3(on)
    print()
    if FAILS:
        print("FAIL %d:" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
