# KCR v134 DoeSchedule(ENDTIM 으로 DOE 비용·긴 것부터 순서·칸 배정·무릎 대수)의 순수 함수 시험
"""
실행: venv312/bin/python tests/test_doe_schedule.py      (몇 초 — 2만 DOE 성능 확인 포함)

  [1] schedule_options — 없음·true·false·enabled false·모르는 키 경고·틀린 값
  [2] doe_costs — 고정비 + ms 당 시간 × Σ(스텝 T + DR), 표에 없는 스텝은 tFinal, time_unit s·ms·없음·섞임
  [3] lpt_order·lpt_lanes·makespan·lower_bound — 같은 값 처리, 작은 집합 전수 탐색 대조(LPT 4/3 보장), 칸 분할
  [4] knee_n·concurrency_cap — 균일·꼬리 분포, 여유, 상한 출처
  [5] d2r_active — 켬·dict·RigidWall·include_wall_in_general·drop_contact Type General
  [6] build_schedule·summary_line·write_schedule — 표 없음 None, 칸 배정, D2R 알림, does(rerun 대상만·표 밖이면 None)
  [7] 성능 — 2만 DOE build_schedule(상한 2만), 실제 2만 방향 표가 있으면 라운드로빈 대비 이득
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


def check(name, cond, detail=""):
    print("  %-70s %s" % (name[:70], "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def table_file(tmp, unit, name="t.csv"):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(("" if unit is None else f"# time_unit={unit}\n") + "# format=rigid_drop_endtime/endtime v1\n"
                "name,roll,pitch,yaw,endtim\nA,0,0,0,0.001\n")
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
    check("없음 → 기본값으로 켬", d == S.DEFAULTS, str(d))
    check("true → 기본값, false → None, enabled false → None",
          S.schedule_options({"schedule": True}) == S.DEFAULTS and S.schedule_options({"schedule": False}) is None
          and S.schedule_options({"schedule": {"enabled": False}}) is None)
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
    c, notes = S.doe_costs(config({"1": {"1": 0.010}}), opts)
    check("time_unit 메타 없음 → s 로 보고 알림", abs(c[1] - 500) < 1e-9 and notes and "s 로 본다" in notes[0], f"{notes}")
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
    print("[6] build_schedule·summary_line·write_schedule")
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
    check("does 가 비었거나 표 밖 DOE(21) 가 있으면 None — 호출 쪽은 지금 동작",
          S.build_schedule(cfg, opts, "rerun", does=[]) is None and S.build_schedule(cfg, opts, "rerun", does=[1, 21]) is None)


def test_perf():
    print("[7] 성능·실제 표")
    rng = random.Random(11)
    cfg = config({str(d): {"1": rng.uniform(0.001, 0.17)} for d in range(1, 20001)})
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        p = S.build_schedule(cfg, dict(S.DEFAULTS), "sequential", nodes=20000, lanes=True)
    dt = time.time() - t0
    check(f"2만 DOE·상한 2만 build_schedule {dt:.1f} s (< 60 s), 무릎 {p['knee']}", dt < 60 and p["knee"] > 1, f"{dt}")
    if not os.path.exists(TABLE_20K):
        print(f"  SKIP 실제 2만 방향 표 없음: {TABLE_20K}")
        return
    meta = S._table_meta(TABLE_20K)
    rows = [ln.rstrip("\n").split(",") for ln in open(TABLE_20K, encoding="utf-8") if not ln.startswith("#")]
    head = rows[0]
    end = [float(dict(zip(head, r))["endtim"]) for r in rows[1:]]
    costs = {d + 1: 300 + 20 * e * 1000 for d, e in enumerate(end)}
    n = 100
    rr = [0.0] * n
    for d in range(1, len(costs) + 1):
        rr[(d - 1) % n] += costs[d]
    gain = 1 - S.makespan(costs, n) / max(rr)
    check(f"실제 2만 방향 표(time_unit {meta.get('time_unit')}) 칸 100 — 라운드로빈 대비 {100 * gain:.1f}% 짧다 (≥ 3%)",
          gain >= 0.03, f"{gain}")


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
