# KCR v134 DoeSchedule(ENDTIM 으로 DOE 비용·긴 것부터 순서·칸 배정·무릎 대수)의 순수 함수 시험
"""
실행: venv312/bin/python tests/test_doe_schedule.py      (몇 초 — 2만 DOE 성능·실제 표 훑기 포함)

  [1] schedule_options — 없음·true·null·false·enabled false(다른 키를 보지 않음)·모르는 키 경고·틀린 값, 기본 무릎 여유 0
  [2] doe_costs — 고정비 + ms 당 시간 × Σ(스텝 T + DR), 표에 없는 스텝은 tFinal, 시간 단위 = time_unit → units 끝 → tFinal
      짐작(0.5 이상 ms) 순서와 알림, 섞임
  [3] lpt_order·lpt_lanes·makespan·lower_bound — 같은 값 처리, 작은 집합 전수 탐색 대조(LPT 4/3 보장), 칸 분할
  [4] knee_n·concurrency_cap — 균일·꼬리 분포, 여유, 상한 출처
  [5] d2r_active — 켬·dict·RigidWall·include_wall_in_general·drop_contact Type General
  [6] build_schedule·summary_line·write_schedule·fewer_slots_line — 표 없음 None, 칸 배정, D2R 알림, does(rerun 대상만·표 밖
      DOE 는 빼고 알림·표 안이 없으면 None), 칸이 --nodes 보다 적을 때 알림 한 줄(무릎·상한)
  [7] 성능·실제 무릎 — 2만 DOE build_schedule(상한 2만), 기본 가정 --sequential 모델 완료(상한 안 무릎 칸 LPT) ≤ 라운드로빈
      (같은 --nodes): 실제 2만·100 방향 표가 있으면 N 을 훑고, 표 모양 합성 자료도 훑는다. 작은 합성 집합은 LPT 가 라운드로빈에
      우연히 질 수 있어(무릎 탓이 아니다) '무릎 칸 완료 ≤ 상한 칸 LPT 완료' 만 본다
"""
import contextlib
import io
import itertools
import json
import math
import os
import random
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import Runner.DoeSchedule as S  # noqa: E402

FAILS = []
TABLE_20K = "/data/koopark/Test_E2E_v133/perf_20k/MinimumModel_endtime.csv"
TABLE_100 = "/data/koopark/Test_E2E_v133/golden/a_rde/MinimumModel_endtime.csv"


def check(name, cond, detail=""):
    print("  %-70s %s" % (name[:70], "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def table_file(tmp, unit, name="t.csv", units=None):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(("" if unit is None else f"# time_unit={unit}\n") + ("" if units is None else f"# units={units}\n")
                + "# format=rigid_drop_endtime/endtime v1\nname,roll,pitch,yaw,endtim\nA,0,0,0,0.001\n")
    return path


def config(endtim, total_steps=1, tfinal=0.005, dr=False, tables=None, doe_count=None):
    sc = {"doe_endtim": endtim, "total_steps": total_steps}
    if tables is not None:
        sc["endtime_tables"] = [{"table": t} for t in tables]
    if doe_count is not None:
        sc["doe_count"] = doe_count
    return {"scenario": sc, "simulation_params": {"tFinal": tfinal, "dynamic_relaxation": dr}}


def test_options():
    print("[1] schedule_options")
    d = S.schedule_options({})
    check("없음 → 기본값으로 켬, 기본 knee_tolerance 0", d == S.DEFAULTS and d["knee_tolerance"] == 0.0, str(d))
    check("true·null → 기본값, false → None, enabled false → None",
          S.schedule_options({"schedule": True}) == S.DEFAULTS and S.schedule_options({"schedule": None}) == S.DEFAULTS
          and S.schedule_options({"schedule": False}) is None and S.schedule_options({"schedule": {"enabled": False}}) is None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        off = [S.schedule_options({"schedule": {"enabled": False, "licenses": 0}}),
               S.schedule_options({"schedule": {"enabled": False, "licence": 2}})]
    check("enabled false 는 다른 키를 보지 않는다 — licenses 0 도 None(오류 없음), 모르는 키도 경고 없음",
          off == [None, None] and buf.getvalue() == "", buf.getvalue())
    o = S.schedule_options({"schedule": {"licenses": 40, "licenses_per_job": 2, "seconds_per_ms": 5}})
    check("값 넣기 — licenses 40·licenses_per_job 2·seconds_per_ms 5, 나머지 기본",
          o["licenses"] == 40 and o["licenses_per_job"] == 2 and o["seconds_per_ms"] == 5 and o["overhead_seconds"] == 300.0)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        S.schedule_options({"schedule": {"licence": 3}})
    check("모르는 키 → 경고 한 줄(쓸 수 있는 키 목록)", "모르는 키 ['licence']" in buf.getvalue(), buf.getvalue())
    bad = [{"enabled": "yes"}, {"licenses": 0}, {"licenses": True}, {"licenses": 2.5}, {"max_concurrent": 0},
           {"licenses_per_job": 0}, {"overhead_seconds": -1}, {"overhead_seconds": float("inf")}, {"seconds_per_ms": 0},
           {"seconds_per_ms": "20"}, {"knee_tolerance": -0.1}, {"licenses": 1, "licenses_per_job": 2}]
    n = 0
    for b in bad + ["yes", 3]:
        try:
            S.schedule_options({"schedule": b})
        except S.DoeScheduleError as e:
            n += "(bad value)" in str(e)
    check(f"틀린 값 {len(bad) + 2}가지 → DoeScheduleError (bad value)", n == len(bad) + 2, f"{n}")


def test_costs(tmp):
    print("[2] doe_costs")
    opts = dict(S.DEFAULTS)
    c, notes = S.doe_costs(config({"1": {"1": 0.010}, "2": {"1": 0.002}}, tables=[table_file(tmp, "s")]), opts)
    check("한 스텝 s 단위 — 300 + 20×10 ms = 500 s, 300 + 20×2 = 340 s, 알림 없음",
          abs(c[1] - 500) < 1e-9 and abs(c[2] - 340) < 1e-9 and not notes, f"{c} {notes}")
    c, notes = S.doe_costs(config({"1": {"1": 10.0}}, tfinal=5.0, tables=[table_file(tmp, "ms", "m.csv")]), opts)
    check("ms 단위 표 — 10 ms → 500 s", abs(c[1] - 500) < 1e-9 and not notes, f"{c}")
    c, notes = S.doe_costs(config({"1": {"1": 10.0}}, tfinal=5.0, tables=[table_file(tmp, None, "u.csv", units="mm-kg-ms")]),
                           opts)
    check("time_unit 없고 units=mm-kg-ms → 끝 ms(10 ms → 500 s), 알림", abs(c[1] - 500) < 1e-9
          and notes == ["표 메타 time_unit 이 없어 units mm-kg-ms 의 끝 ms 를 덱 시간 단위로 본다"], f"{c} {notes}")
    c, notes = S.doe_costs(config({"1": {"1": 0.010}}, tables=[table_file(tmp, None, "v.csv", units="mm-t-s")]), opts)
    check("time_unit 없고 units=mm-t-s → s, 알림", abs(c[1] - 500) < 1e-9 and len(notes) == 1 and "끝 s 를" in notes[0],
          f"{notes}")
    c, notes = S.doe_costs(config({"1": {"1": 0.010}}), opts)
    check("표 메타 없음·tFinal 0.005 → s 로 짐작하고 알림", abs(c[1] - 500) < 1e-9 and len(notes) == 1
          and "tFinal 0.005 로 덱 시간 단위를 s 로 짐작한다" in notes[0], f"{notes}")
    c, notes = S.doe_costs(config({"1": {"1": 10.0}}, tfinal=5.0, tables=[table_file(tmp, None, "w.csv")]), opts)
    check("표 메타(time_unit·units) 없음·tFinal 5 (≥ 0.5) → ms 로 짐작하고 알림 (10 ms → 500 s)",
          abs(c[1] - 500) < 1e-9 and len(notes) == 1 and "tFinal 5 로 덱 시간 단위를 ms 로 짐작한다" in notes[0], f"{notes}")
    c, notes = S.doe_costs(config({"1": {"1": 0.010}}, tables=[table_file(tmp, "s"), table_file(tmp, "ms", "m.csv")]), opts)
    check("표마다 단위 다름 → 첫 표(s)를 쓰고 알림", abs(c[1] - 500) < 1e-9 and "다르다" in notes[0], f"{notes}")
    cfg = config({"1": {"1": 0.010, "3": 0.020}, "2": {}}, total_steps=3, dr=True, tables=[table_file(tmp, "s")], doe_count=3)
    c, _ = S.doe_costs(cfg, opts)
    # DOE 1: 스텝 1 10 + 스텝 2 tFinal 5 + DR 5 + 스텝 3 20 + DR 5 = 45 ms, DOE 2·3: 5 + (5 + 5) + (5 + 5) = 25 ms
    check("세 스텝·DR 켬 — 없는 스텝은 tFinal, 둘째 스텝부터 + tFinal, doe_count 3 이면 DOE 3 도(모두 tFinal)",
          abs(c[1] - (300 + 20 * 45)) < 1e-9 and abs(c[2] - (300 + 20 * 25)) < 1e-9 and abs(c[3] - (300 + 20 * 25)) < 1e-9,
          f"{c}")
    check("DR dict enabled false 는 끔", abs(S.doe_costs(config({"1": {"1": 0.010}}, total_steps=2,
                                                                 dr={"enabled": False}, tables=[table_file(tmp, "s")]),
                                                          opts)[0][1] - (300 + 20 * 15)) < 1e-9)
    check("표 없음·opts None → (None, [])", S.doe_costs(config({}), opts) == (None, [])
          and S.doe_costs(config({"1": {"1": 0.01}}), None) == (None, []))


def brute_opt(costs, n):
    """작은 집합 최적 완료 시각(전수)."""
    ds = list(costs)
    best = math.inf
    for assign in itertools.product(range(n), repeat=len(ds)):
        loads = [0.0] * n
        for d, a in zip(ds, assign):
            loads[a] += costs[d]
        best = min(best, max(loads))
    return best


def test_lpt():
    print("[3] lpt_order·lpt_lanes·makespan·lower_bound")
    c = {1: 5.0, 2: 9.0, 3: 5.0, 4: 1.0}
    check("순서 = 비용 내림차순, 같으면 DOE 번호 오름차순", S.lpt_order(c) == [2, 1, 3, 4], str(S.lpt_order(c)))
    check("비용이 모두 같으면 DOE 번호 순서 그대로", S.lpt_order({d: 7.0 for d in range(1, 9)}) == list(range(1, 9)))
    lanes = S.lpt_lanes(c, 2)
    check("칸 2 — 9 → 칸0, 5 → 칸1, 5 → 덜 찬 칸1, 1 → 칸0 = [[2, 4], [1, 3]] (10·10)", lanes == [[2, 4], [1, 3]], str(lanes))
    rng = random.Random(7)
    worst, ok_part = 0.0, True
    for _ in range(60):
        k, n = rng.randint(2, 7), rng.randint(2, 3)
        cc = {d: round(rng.uniform(0.5, 10), 3) for d in range(1, k + 1)}
        ln = S.lpt_lanes(cc, n)
        ok_part &= sorted(x for lane in ln for x in lane) == list(cc) and all(
            [cc[x] for x in lane] == sorted((cc[x] for x in lane), reverse=True) for lane in ln)
        ms = S.makespan(cc, n)
        ok_part &= abs(ms - max(sum(cc[x] for x in lane) for lane in ln)) < 1e-9 and ms >= S.lower_bound(cc, n) - 1e-9
        worst = max(worst, ms / brute_opt(cc, n))
    check(f"작은 집합 60개 — 칸이 DOE 를 한 번씩 나눔·칸 안 내림차순·완료 = 칸 최대 ≥ 하한, LPT/최적 최대 {worst:.3f} ≤ 4/3",
          ok_part and worst <= 4 / 3 + 1e-9, f"{worst}")
    check("칸 ≥ DOE 수 → 완료 = 최장, 빈 집합 → 0", S.makespan(c, 10) == 9.0 and S.makespan({}, 3) == 0.0
          and S.lower_bound({}, 3) == 0.0)


def test_knee():
    print("[4] knee_n·concurrency_cap")
    uni = {d: 1.0 for d in range(1, 11)}
    check("균일 10개·상한 10 → 무릎 10 (계단이라 끝까지 준다)", S.knee_n(uni, 10, 0.05) == 10, str(S.knee_n(uni, 10, 0.05)))
    tail = {1: 10.0, **{d: 1.0 for d in range(2, 11)}}
    check("꼬리 분포(10 + 1×9)·상한 10 → 무릎 2 (최장이 정함)", S.knee_n(tail, 10, 0.05) == 2, str(S.knee_n(tail, 10, 0.05)))
    check("여유 1.0 → 더 작은 무릎(균일 10개, 완료 ≤ 2 = ceil(10/n) → 5), 여유 0.5 는 그대로 10",
          S.knee_n(uni, 10, 1.0) == 5 and S.knee_n(uni, 10, 0.5) == 10, f"{S.knee_n(uni, 10, 1.0)} {S.knee_n(uni, 10, 0.5)}")
    check("상한이 DOE 수보다 크면 DOE 수로", S.knee_n(uni, 100, 0.0) == 10)
    rng = random.Random(3)
    cc = {d: rng.uniform(1, 100) for d in range(1, 301)}
    k = S.knee_n(cc, 200, 0.05)
    check("무릎 성질 — makespan(k) ≤ 1.05·makespan(200), makespan(k−1) > 그 값",
          S.makespan(cc, k) <= 1.05 * S.makespan(cc, 200) * (1 + 1e-12) and S.makespan(cc, k - 1) > 1.05 * S.makespan(cc, 200),
          f"k={k}")
    cap, src = S.concurrency_cap({**S.DEFAULTS, "licenses": 41, "licenses_per_job": 4, "max_concurrent": 20}, nodes=16, doe_count=100)
    check("상한 = min(노드 16, 라이선스 41÷4=10, max_concurrent 20, DOE 100) = 10 · 출처",
          cap == 10 and src == {"nodes": 16, "licenses": 10, "max_concurrent": 20, "doe_count": 100}, f"{cap} {src}")
    check("출처 없음 → 1, DOE 수만 → DOE 수", S.concurrency_cap(None) == (1, {})
          and S.concurrency_cap(S.DEFAULTS, doe_count=7)[0] == 7)


def test_d2r():
    print("[5] d2r_active")
    sp = lambda **kw: {"simulation_params": kw}  # noqa: E731
    cases = [(sp(drop_surface={"deformable_to_rigid": True}), True),
             (sp(drop_surface={"deformable_to_rigid": {"time3": 0.001}}), True),
             (sp(drop_surface={"deformable_to_rigid": {}}), False),
             (sp(drop_surface={"deformable_to_rigid": False}), False),
             (sp(), False),
             (sp(drop_surface={"type": "RigidWall", "deformable_to_rigid": True}), False),
             (sp(drop_surface={"deformable_to_rigid": True}, include_wall_in_general=True), False),
             (sp(drop_surface={"deformable_to_rigid": True}, drop_contact={"Type": "General"}), False),
             (sp(drop_surface={"deformable_to_rigid": True}, drop_contact={"type": "general"}), False),
             (sp(drop_surface={"deformable_to_rigid": True}, drop_contact={"Type": "SurfaceToSurface"}), True)]
    got = [S.d2r_active(c) for c, _ in cases]
    check("켬·dict 켬 / 빈 dict·끔·없음·RigidWall·include_wall_in_general·Type General(대소문자) 끔 / Type S2S 켬",
          got == [w for _, w in cases], str(got))


def test_build(tmp):
    print("[6] build_schedule·summary_line·write_schedule·fewer_slots_line")
    opts = dict(S.DEFAULTS)
    check("표 없음 → None", S.build_schedule(config({}), opts, "submit") is None)
    cfg = config({str(d): {"1": 0.001 * d} for d in range(1, 21)}, tables=[table_file(tmp, "s")])
    p = S.build_schedule(cfg, opts, "sequential", nodes=4, lanes=True)
    check("칸 4 — 상한 4(nodes·doe_count), 순서 = 긴 것부터(20…1), 칸 = lpt_lanes(무릎)",
          p["cap"] == 4 and p["order"] == list(range(20, 0, -1)) and p["lanes"] == S.lpt_lanes(
              {d: 300 + 20 * d for d in range(1, 21)}, p["knee"]) and p["format"] == S.FORMAT, json.dumps(p)[:300])
    check("by_n 에 1·무릎·상한, costs_seconds 문자열 키, 가정 calibrated false·d2r false",
          {1, p["knee"], p["cap"]} <= {x["n"] for x in p["by_n"]} and p["costs_seconds"]["20"] == 700.0
          and p["assumptions"]["calibrated"] is False and p["assumptions"]["d2r"] is False)
    cfg_d2r = {**cfg, "simulation_params": {**cfg["simulation_params"], "drop_surface": {"deformable_to_rigid": True}}}
    p2 = S.build_schedule(cfg_d2r, opts, "submit")
    line = S.summary_line(p2)
    check("D2R 켬 → 알림·d2r true·요약 줄에 'D2R 켬(보정 안 됨)', lanes 없음",
          p2["assumptions"]["d2r"] and any("D2R 켬" in n for n in p2["notes"]) and "D2R 켬(보정 안 됨)" in line
          and "lanes" not in p2, line)
    check("요약 줄 — DOE 수·무릎·상한·가정", "DOE 20" in line and f"무릎 {p2['knee']} 칸" in line and "보정 안 됨" in line, line)
    path = S.write_schedule(p, os.path.join(tmp, "slurm_scripts"))
    check("schedule.json 쓰기·읽기 같음", json.load(open(path, encoding="utf-8")) == json.loads(json.dumps(p)), path)
    p3 = S.build_schedule(cfg, opts, "rerun", nodes=4, lanes=True, does=[3, 20, 7, 3])
    check("does(rerun 대상) — 그 DOE 만(중복 한 번): DOE 3·순서 [20, 7, 3]·상한 3(doe_count)·칸 = lpt_lanes(대상 비용)",
          p3["doe_count"] == 3 and p3["order"] == [20, 7, 3] and set(p3["costs_seconds"]) == {"3", "7", "20"}
          and p3["cap_from"] == {"nodes": 4, "doe_count": 3}
          and p3["lanes"] == S.lpt_lanes({20: 700.0, 7: 440.0, 3: 360.0}, p3["knee"]), json.dumps(p3)[:300])
    p4 = S.build_schedule(cfg, opts, "rerun", does=[21, 1, 22, 21])
    check("does 에 표 밖 DOE(21·22) — 표 안 DOE 1 만으로 짜고 받은 순서 그대로 알림 [21, 22, 21]",
          p4 is not None and p4["order"] == [1] and p4["doe_count"] == 1
          and p4["notes"][-1].startswith("표 밖 DOE [21, 22, 21] 는 계획에서 빼고 맨 뒤에 그대로 낸다"), str(p4 and p4["notes"]))
    check("does 가 비었거나 표 밖 DOE 뿐이면 None — 호출 쪽은 지금 동작",
          S.build_schedule(cfg, opts, "rerun", does=[]) is None and S.build_schedule(cfg, opts, "rerun", does=[21]) is None)

    # fewer_slots_line — 꼬리 분포(DOE 1 만 100 ms, 나머지 1 ms): 무릎 3 칸이면 완료가 최장 DOE 1 과 같다
    tail = config({"1": {"1": 0.1}, **{str(d): {"1": 0.001} for d in range(2, 11)}}, tables=[table_file(tmp, "s")])
    pt = S.build_schedule(tail, opts, "sequential", nodes=10, lanes=True)
    lt = S.fewer_slots_line(pt, 10, "--sequential: --nodes")
    check("무릎 3 < --nodes 10 → '--nodes 10 가운데 3 칸만 쓴다 — 나머지를 써도 … (무릎, knee_tolerance 0) · 예상 완료 0.64 h "
          "(10 칸 0.64 h)'", pt["knee"] == 3 and lt == "⚠️  --sequential: --nodes 10 가운데 3 칸만 쓴다 — 나머지를 써도 예상 완료가 "
          "줄지 않는다(무릎, knee_tolerance 0) · 예상 완료 0.64 h (10 칸 0.64 h)", str(lt))
    pt12 = S.build_schedule(tail, opts, "sequential", nodes=12, lanes=True)
    lt12 = S.fewer_slots_line(pt12, 12, "--sequential: --nodes") or ""
    check("--nodes 12 > DOE 10 → 상한 10(doe_count 10) · 무릎 둘 다 적는다",
          "--nodes 12 가운데 3 칸만 쓴다 — 상한 10(doe_count 10) · 나머지를 써도" in lt12, lt12)
    plic = S.build_schedule(tail, {**opts, "licenses": 2}, "sequential", nodes=10, lanes=True)
    llic = S.fewer_slots_line(plic, 10, "--sequential: --nodes") or ""
    check("licenses 2 → 상한 2 = 무릎 2: 상한만 적는다", plic["knee"] == plic["cap"] == 2
          and "--nodes 10 가운데 2 칸만 쓴다 — 상한 2(licenses 2) · 예상 완료" in llic and "무릎" not in llic, llic)
    check("칸 = --nodes(무릎 4 = 4)·lanes 없음(submit)·plan None 이면 None",
          S.fewer_slots_line(p, 4, "x") is None and S.fewer_slots_line(p2, 2, "x") is None
          and S.fewer_slots_line(None, 4, "x") is None, str(S.fewer_slots_line(p, 4, "x")))


def test_perf():
    print("[7] 성능·실제 무릎 — 켬(무릎 칸 LPT) ≤ 라운드로빈")
    rng = random.Random(11)
    cfg = config({str(d): {"1": rng.uniform(0.001, 0.17)} for d in range(1, 20001)})
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        p = S.build_schedule(cfg, dict(S.DEFAULTS), "sequential", nodes=20000, lanes=True)
    dt = time.time() - t0
    check(f"2만 DOE·상한 2만 build_schedule {dt:.1f} s (< 60 s), 무릎 {p['knee']}", dt < 60 and p["knee"] > 1, f"{dt}")

    # 기본 가정 --sequential 의 모델 완료(상한 안 무릎 칸 LPT) ≤ 같은 --nodes 의 v133 라운드로빈 — 표 모양 합성 자료
    rng = random.Random(23)
    pool = [rng.uniform(0.0015, 0.17) for _ in range(500)]
    worse = [(k, n) for k in (60, 200) for cc in [{d: 300 + 20e3 * rng.choice(pool) for d in range(1, k + 1)}]
             for n in range(1, k + 1) if on_makespan(cc, n)[0] > rr_makespan(cc, n) * (1 + 1e-9)]
    check("표 모양 합성(DOE 60·200, ENDTIM 1.5~170 ms) — 모든 --nodes 1..DOE 수에서 켬 ≤ 라운드로빈", not worse, str(worse[:5]))
    rng2, n_cases, rr_wins, knee_worse = random.Random(5), 0, 0, 0
    for _ in range(1500):
        k = rng2.randint(2, 12)
        cc = {d: float(rng2.randint(1, 20)) for d in range(1, k + 1)}
        for n in range(1, k + 3):
            n_cases += 1
            on, knee = on_makespan(cc, n)
            knee_worse += on > S.makespan(cc, min(n, k)) * (1 + 1e-9)
            rr_wins += on > rr_makespan(cc, n) * (1 + 1e-9)
    check(f"작은 합성 집합 {n_cases} 경우 — 무릎 칸 완료 ≤ 상한 칸 LPT 완료(무릎은 완료를 늦추지 않는다)", knee_worse == 0,
          f"{knee_worse}")
    print(f"  (참고) 그중 {rr_wins} 경우는 라운드로빈이 LPT 보다 우연히 빠르다 — 무릎 탓이 아니라 LPT 의 한계다")
    for path, label, ns in ((TABLE_20K, "2만", list(range(2, 61)) + [100, 200, 500, 1000, 2000, 5000]),
                            (TABLE_100, "100", list(range(1, 101)))):
        if not os.path.exists(path):
            print(f"  SKIP 실제 {label} 방향 표 없음: {path}")
            continue
        end = read_endtim(path)
        costs = {d + 1: 300 + 20 * e * 1000 for d, e in enumerate(end)}
        worse = [n for n in ns if on_makespan(costs, n)[0] > rr_makespan(costs, n) * (1 + 1e-9)]
        check(f"실제 {label} 방향 표 — --nodes {ns[0]}..{ns[-1]} ({len(ns)} 개)에서 켬(무릎 칸 LPT) ≤ 라운드로빈",
              not worse, str(worse[:8]))
        if label == "2만":   # 문서 수치 — 실제 경로(build_schedule, 표 메타 time_unit)로 --nodes 100
            cfg = {"scenario": {"doe_endtim": {str(d + 1): {"1": e} for d, e in enumerate(end)}, "total_steps": 1,
                                "doe_count": len(end), "endtime_tables": [{"table": path}]},
                   "simulation_params": {"tFinal": 0.005}}
            p = S.build_schedule(cfg, S.schedule_options({}), "sequential", nodes=100, lanes=True)
            on = max(sum(costs[d] for d in lane) for lane in p["lanes"])
            gain = 1 - on / rr_makespan(costs, 100)
            check(f"실제 2만 방향 표 --nodes 100 — 무릎 {p['knee']} 칸 배정의 완료가 라운드로빈보다 {100 * gain:.2f}% 짧다 (≥ 3%), "
                  f"알림 없음", gain >= 0.03 and p["knee"] <= 100 and not p["notes"]
                  and abs(on - p["makespan_seconds"]) < 1e-2, f"{gain} {p['knee']} {p['notes']}")


def read_endtim(path):
    rows = [ln.rstrip("\n").split(",") for ln in open(path, encoding="utf-8") if not ln.startswith("#")]
    return [float(dict(zip(rows[0], r))["endtim"]) for r in rows[1:]]


def rr_makespan(costs, n):
    """v133 --sequential 라운드로빈 — DOE d 를 칸 (d − 1) % n 에(빈 칸은 0)."""
    lanes = [0.0] * n
    for d in sorted(costs):
        lanes[(d - 1) % n] += costs[d]
    return max(lanes)


def on_makespan(costs, nodes):
    """기본 가정으로 --sequential --nodes nodes 를 켰을 때 모델 완료 → (완료, 무릎). 상한 = min(nodes, DOE 수)."""
    knee = S.knee_n(costs, min(nodes, len(costs)), S.DEFAULTS["knee_tolerance"])
    return S.makespan(costs, knee), knee


def main():
    with tempfile.TemporaryDirectory() as tmp:
        test_options()
        test_costs(tmp)
        test_lpt()
        test_knee()
        test_d2r()
        test_build(tmp)
        test_perf()
    print()
    if FAILS:
        print("FAIL %d:" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
