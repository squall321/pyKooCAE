# KCR v134 environment.schedule(사전 해석 ENDTIM 으로 긴 것부터 제출·--sequential 무릎 칸·rerun)을 가짜 sbatch 로 검증하는 시험
"""
실행: venv312/bin/python tests/test_kcr_doe_schedule.py      (prepare 스물다섯 번·가짜 sbatch·가짜 KMM, 십 초 안팎)

  [0] 꺼짐 바이트 동일 — 표 있음 + schedule 끔(submit 경로 false, rerun 경로 {"enabled": false})과 표 없음(기본 켬):
      기본·--sequential·batch 제출, rerun(기본·--sequential)의 sbatch 순서·slurm 스크립트·jobs.json 이 바꾸기 전 코드와 같다
      (정답 sha256 은 바꾸기 전 코드(ddd1a4c)에서 --print-golden 으로 뽑아 박았다. 임시 폴더·KCR 경로·시각·rerun 번호만 바꿔 잰다)
  [1] 기본 제출 — sbatch 순서 = ENDTIM 긴 것부터(같으면 DOE 번호), 스크립트는 끈 것과 같고 jobs.json 은 키·필드 그대로
      (키 순서만 제출 순서), slurm_scripts/schedule.json·요약 한 줄
  [2] --sequential --nodes K — 칸 수 = 상한(--nodes·licenses÷licenses_per_job·DOE 수) 안 무릎, 칸 DOE = lpt_lanes(칸 안도
      긴 것부터), 칸 --time = 기준 × 칸 F_d 합의 최대(지금 식), jobs.json sequential_slot, 마지막 요약의 칸 수
  [3] rerun — 대상을 긴 것부터, --does 로 고른 일부만으로 짠 순서, --sequential rerun 은 대상만으로 짠 무릎·lpt_lanes
  [4] batch_koomeshmodifier — .done 이 함께 보이면 긴 것부터 낸다
  [5] 틀린 environment.schedule — submit·--sequential·rerun 이 sbatch 전에 ❌ 종료 1, jobs.json 을 건드리지 않는다
  [6] prepare 미리보기 — 표가 있으면 요약 한 줄(상한은 licenses·max_concurrent·DOE 수, 노드 없음), 없거나 끄면 없음,
      틀린 값은 ❌ 한 줄(prepare 는 마친다)
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import test_kcr_endtime_presim as EPT  # noqa: E402  (prepare·가짜 KMM·KCR 불러오기 도우미)
import Runner.DoeSchedule as S  # noqa: E402
from Runner.EndTimePresim import doe_time_factors  # noqa: E402

FAILS = []
UNSET = object()
# DOE → ENDTIM(s, 스텝 1 개). 긴 것부터 4 · 2·6(같음 → 번호) · 9 · 1·3·8 · 7 · 5·10. 1 스텝·DR 없음이라 비용은 ENDTIM 에 단조다
ENDTIM = {1: 0.004, 2: 0.010, 3: 0.004, 4: 0.020, 5: 0.002, 6: 0.010, 7: 0.003, 8: 0.004, 9: 0.006, 10: 0.002}
LPT = sorted(ENDTIM, key=lambda d: (-ENDTIM[d], d))
COSTS = {d: 300.0 + 20.0 * e * 1000 for d, e in ENDTIM.items()}   # 기본 가정 — 고정비 300 s + 1 ms 당 20 s

# 바꾸기 전 코드(ddd1a4c)로 뽑은 정답 — [0] 꺼짐 바이트 동일
GOLDEN = {
    "submit_off": "43431646486015440f22e8a6c70996b61aa2af3e225689f22045fbc538cc86c4",
    "sequential_off": "a688b7c6285429f0f3aa1b0a19b047273cf156a54572e618588c7df3a3a5dcee",
    "batch_off": "077ecd6bf891acf574d3cac580fc60ab7507b55f10090e08b453b12104bb204e",
    "rerun_off": "64a42bef4402f45ff43a69295ffa70ba9ee5ec22dd66396d390d507915d3c20d",
    "rerun_sequential_off": "926ec2c86e86874330344bc3bb64b21426bd4dcb8ffc5b2c6136a7a10519d0b2",
    "submit_notable": "c82ab24f90f9f0b8679b836eeb0a9a43ed5ca07b4b9fb143cb38f87ef49eaa40",
    "sequential_notable": "09551b0910e4f75332a04df68619a6dfe4deb2d0b5086ffd8503f16da7798f14",
    "batch_notable": "8c8ed93087f03fca63c271ef8c06fbf40caef68ac1ba55cd569f2f221f0e9f84",
    "rerun_notable": "f0de6a5b3b9956dfbb1392af97d07818783c541af45f0286bb18c25ac0dffc37",
    "rerun_sequential_notable": "bdcfa26a5fa32ce54772339b37e9e9f932f206e6a97b85fcbbd4a3dcbfeae77c",
}


def check(name, cond, detail=""):
    print("  %-70s %s" % (name[:70], "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def scen10(tmp):
    """피보나치 10 자세 × DROP 1 스텝 → DOE 10개 (tFinal 0.004, DR 없음)."""
    d = EPT.scen_faces2(tmp)
    d["project_name"] = "SchedReg"
    d["scenarios"] = [{"scenario_name": "Fib10", "template": "model.k",
                       "angle_source": {"source_type": "fibonacci_lattice", "fibonacci_lattice": {"num_points": 10}},
                       "cumulative": {"num_steps": 1, "mode_sequence": ["DROP"]}}]
    return d


def fake_batch_kmm(tmp):
    """batch_koomeshmodifier 의 가짜 KMM — .done 은 시험이 미리 만들어 두어 바로 끝난다."""
    p = os.path.join(tmp, "fake_batch_kmm.py")
    Path(p).write_text(f"#!{sys.executable}\n# 가짜 batch KMM — 아무것도 하지 않고 끝난다\n", encoding="utf-8")
    os.chmod(p, 0o755)
    return p


def prepared(tag, table=True, schedule=UNSET, batch=False):
    """scen10 을 Designer 로 prepare 한 뒤 runner_config 에 표(scenario.doe_endtim ← ENDTIM)·environment.schedule·batch 를
    넣는다 → (임시 폴더, runner_config 경로). time_limit 은 01:00:00 이다."""
    tmp = os.path.realpath(EPT.new_tmp(f"sched_{tag}_"))
    EPT.designer_prepare(tmp, scen10(tmp))
    rc_path = os.path.join(tmp, "runner_config.json")
    with open(rc_path, encoding="utf-8") as f:
        rc = json.load(f)
    rc["environment"]["time_limit"] = "01:00:00"
    if table:
        rc["scenario"]["doe_endtim"] = {str(d): {"1": e} for d, e in ENDTIM.items()}
    if schedule is not UNSET:
        rc["environment"]["schedule"] = schedule
    if batch:   # .done 을 모두 미리 만들어 두면 첫 폴링에서 모두 보인다 — 그 안의 순서만 본다
        rc["scenario"]["batch_koomeshmodifier"] = True
        rc["environment"]["koomeshmodifier_path"] = fake_batch_kmm(tmp)
        for d in ENDTIM:
            run = os.path.join(rc["project"]["output_dir"], "pregenerated", f"Run_{d}")
            os.makedirs(run, exist_ok=True)
            Path(run, ".done").write_text("", encoding="utf-8")
    with open(rc_path, "w", encoding="utf-8") as f:
        json.dump(rc, f, indent=1)
    return tmp, rc_path


class FakeSlurm:
    """subprocess.run 가로채기 — sbatch 는 낸 스크립트 이름을 적고 잡 번호를 first 부터 1 씩 늘려 준다. sinfo %l(파티션 최대)은
    7-00:00:00, 나머지 sinfo·scontrol·sacct·squeue 는 빈 답(노드 없음·상태 모름)이다. 다른 명령은 시험을 멈춘다."""

    def __init__(self, first):
        self.sbatch, self.next = [], first

    def __call__(self, cmd, *a, **k):
        if cmd[0] == "sbatch":
            self.sbatch.append(os.path.basename(cmd[-1]))
            self.next += 1
            return subprocess.CompletedProcess(cmd, 0, stdout=f"Submitted batch job {self.next - 1}\n", stderr="")
        out = {"sinfo": "7-00:00:00\n" if "%l" in cmd else "", "scontrol": "", "sacct": "", "squeue": ""}.get(cmd[0])
        if out is None:
            raise RuntimeError(f"예상 밖 명령 {cmd}")
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")


def call(fn, args, tmp, first):
    """fn(args) 를 가짜 Slurm 으로 돈다 → {order: sbatch 낸 스크립트 이름, files: slurm_scripts 의 .sh·schedule.json 과
    jobs.json 글, out: 화면 출력, code: 종료 코드}."""
    fake = FakeSlurm(first)
    real, buf, code = subprocess.run, io.StringIO(), 0
    subprocess.run = fake
    try:
        with contextlib.redirect_stdout(buf):
            fn(args)
    except SystemExit as e:
        code = e.code
    finally:
        subprocess.run = real
    slurm = os.path.join(tmp, "output", "slurm_scripts")
    files = {n: Path(slurm, n).read_text(encoding="utf-8") for n in sorted(os.listdir(slurm))
             if n.endswith(".sh") or n in (S.SCHEDULE_FILE, S.RERUN_SCHEDULE_FILE)} if os.path.isdir(slurm) else {}
    if os.path.exists(os.path.join(tmp, "jobs.json")):
        files["jobs.json"] = Path(tmp, "jobs.json").read_text(encoding="utf-8")
    return {"order": fake.sbatch, "files": files, "out": buf.getvalue(), "code": code}


def run_submit(kcr, rc_path, sequential=False, nodes=8, first=1001):
    args = argparse.Namespace(config=rc_path, mode="cumulative", nodes=nodes, jobs_per_node=4, ncpu_per_job=None,
                              partition=None, memory=None, time_limit=None, data_root="/data", sequential=sequential)
    return call(lambda a: kcr._submit_cumulative(a, Path(rc_path)), args, os.path.dirname(rc_path), first)


def run_rerun(kcr, tmp, sequential=False, nodes=8, does=None, first=2001):
    """cmd_rerun --force — 실행 기록이 없어 모든 DOE 가 not_started 라 대상은 모두(또는 --does)다."""
    args = argparse.Namespace(test_dir=tmp, dry_run=False, force=True, does=does, exclude_nodes=None,
                              sequential=sequential, nodes=nodes, cleanup_stale=False)
    return call(kcr.cmd_rerun, args, tmp, first)


def norm(text, tmp, kcr):
    """임시 폴더·KCR 경로·제출 시각·rerun 번호(HHMMSS) → 자리표."""
    t = text.replace(tmp, "<TMP>").replace(str(Path(kcr.__file__).resolve()), "<KCR>")
    t = re.sub(r'"submitted_at": "[^"]*"', '"submitted_at": "<TS>"', t)
    return re.sub(r"rerun_seq_\d+_", "rerun_seq_<T>_", t)


def digest(res, tmp, kcr):
    """sbatch 순서 + {이름: 글}(이름 순) → sha256."""
    h = hashlib.sha256()
    for k, v in sorted((norm(k, tmp, kcr), norm(v, tmp, kcr)) for k, v in res["files"].items()):
        h.update(k.encode("utf-8") + b"\0" + v.encode("utf-8") + b"\0")
    h.update(json.dumps([norm(x, tmp, kcr) for x in res["order"]]).encode("utf-8"))
    return h.hexdigest()


PATHS = ("submit", "sequential", "batch", "rerun", "rerun_sequential")


def off_case(kcr, path, tag):
    """끈 경우 하나 → (임시 폴더, 결과). off = 표 있음 + 끔(submit 경로 false, rerun 경로 {"enabled": false}),
    notable = 표 없음(키 없음 = 기본 켬). --sequential 은 --nodes 8 이다."""
    table = tag == "off"
    sched = (({"enabled": False} if path.startswith("rerun") else False) if table else UNSET)
    tmp, rc = prepared(f"{tag}_{path}", table, sched, batch=path == "batch")
    if path.startswith("rerun"):
        run_submit(kcr, rc)
        return tmp, run_rerun(kcr, tmp, sequential=path == "rerun_sequential", nodes=8)
    return tmp, run_submit(kcr, rc, sequential=path == "sequential", nodes=8)


def off_digests(kcr):
    out = {}
    for tag in ("off", "notable"):
        for path in PATHS:
            tmp, res = off_case(kcr, path, tag)
            out[f"{path}_{tag}"] = digest(res, tmp, kcr)
    return out


def doe_of(script):
    """run_doe_004.sh → 4."""
    return int(re.search(r"run_doe_(\d+)\.sh", script).group(1))


def script_does(text):
    """슬롯 스크립트의 DOE 실행 순서 — '... run <config> --doe N' 줄."""
    return [int(x) for x in re.findall(r" run \S+ --doe (\d+)\n", text)]


def sbatch_time(text):
    return [ln for ln in text.splitlines() if ln.startswith("#SBATCH --time=")]


def jobs(res):
    return json.loads(res["files"]["jobs.json"])


def plan_of(res, name=S.SCHEDULE_FILE):
    return json.loads(res["files"][name]) if name in res["files"] else None


# ── [0] 꺼짐 바이트 동일 ───────────────────────────────────────
def test_off(kcr):
    print("[0] 꺼짐 바이트 동일 — schedule 끔·표 없음: 바꾸기 전 코드와 sha256 비교")
    for tag in ("off", "notable"):
        for path in PATHS:
            tmp, res = off_case(kcr, path, tag)
            name = f"{path}_{tag}"
            d = digest(res, tmp, kcr)
            check(f"{name}: sha256 == 바꾸기 전", GOLDEN.get(name) == d, f"{d} != {GOLDEN.get(name)}")
            check(f"{name}: sbatch {len(res['order'])}개·schedule.json 없음·요약 줄 없음·종료 0",
                  res["order"] and S.SCHEDULE_FILE not in res["files"] and "[schedule]" not in res["out"]
                  and not res["code"], f"{res['order']} {res['code']} {res['out'][-300:]}")
            if path in ("submit", "batch", "rerun"):
                got = [doe_of(s) for s in res["order"]]
                check(f"{name}: DOE 번호 순서 그대로", got == list(range(1, 11)), str(got))


# ── [1] 기본 제출 ───────────────────────────────────────────────
def test_submit(kcr):
    print("[1] 기본 제출 — 긴 것부터, 스크립트·jobs.json 형식 그대로, schedule.json·요약 줄")
    tmp, rc = prepared("on_submit")
    res = run_submit(kcr, rc)
    got = [doe_of(s) for s in res["order"]]
    check(f"sbatch 순서 = ENDTIM 긴 것부터, 같으면 DOE 번호 {LPT}", got == LPT == [4, 2, 6, 9, 1, 3, 8, 7, 5, 10], str(got))
    tmp0, rc0 = prepared("off_submit_cmp", schedule=False)
    res0 = run_submit(kcr, rc0)
    sh = {k: norm(v, tmp, kcr) for k, v in res["files"].items() if k.endswith(".sh")}
    sh0 = {k: norm(v, tmp0, kcr) for k, v in res0["files"].items() if k.endswith(".sh")}
    check("run_doe_NNN.sh 10개 — 이름·글이 끈 것과 같다 (순서만 바뀐다)", len(sh) == 10 and sh == sh0)
    j, j0 = jobs(res), jobs(res0)
    check("jobs.json 맨 위 키·DOE 키 집합·DOE 마다 필드 이름 그대로",
          list(j) == list(j0) and set(j["jobs"]) == set(j0["jobs"]) == {str(d) for d in ENDTIM}
          and all(list(j["jobs"][k]) == list(j0["jobs"][k]) for k in j0["jobs"]), str(j)[:300])
    check("jobs.json 필드 값 — 잡 이름·스크립트·status 같고, 잡 번호는 제출 순서(DOE 4 → 1001), 키 순서 = 제출 순서",
          all(norm(json.dumps({x: v[x] for x in ("job_name", "status", "script_path")}), tmp, kcr)
              == norm(json.dumps({x: j0["jobs"][k][x] for x in ("job_name", "status", "script_path")}), tmp0, kcr)
              for k, v in j["jobs"].items())
          and all(j["jobs"][str(d)]["job_id"] == str(1001 + i) for i, d in enumerate(LPT))
          and list(j["jobs"]) == [str(d) for d in LPT], str(j["jobs"])[:300])
    p = plan_of(res)
    check("slurm_scripts/schedule.json — format·mode submit·DOE 10·순서·비용(300 + 20 × ms)·상한 출처 DOE 수만·칸 없음",
          p is not None and p["format"] == S.FORMAT and p["mode"] == "submit" and p["doe_count"] == 10
          and p["order"] == LPT and p["costs_seconds"] == {str(d): round(c, 3) for d, c in COSTS.items()}
          and p["cap"] == 10 and p["cap_from"] == {"doe_count": 10} and "lanes" not in p
          and p["assumptions"]["calibrated"] is False, json.dumps(p)[:400] if p else "없음")
    check("요약 한 줄([schedule] …)·schedule.json 경로를 찍는다, 끈 쪽은 schedule.json 없음",
          p is not None and res["out"].count("[schedule]") == 1 and S.summary_line(p) in res["out"]
          and os.path.join(tmp, "output", "slurm_scripts", S.SCHEDULE_FILE) in res["out"]
          and S.SCHEDULE_FILE not in res0["files"], res["out"][-600:])
    check("마지막 요약 'Submitted 10/10 DOE jobs'", "Submitted 10/10 DOE jobs" in res["out"], res["out"][-400:])

    tmp2, rc2 = prepared("on_submit_flat")
    with open(rc2, encoding="utf-8") as f:
        r2 = json.load(f)
    r2["scenario"]["doe_endtim"] = {str(d): {"1": 0.003} for d in ENDTIM}
    with open(rc2, "w", encoding="utf-8") as f:
        json.dump(r2, f, indent=1)
    res2 = run_submit(kcr, rc2)
    check("비용이 모두 같으면(켬) DOE 번호 순서 그대로", [doe_of(s) for s in res2["order"]] == list(range(1, 11)),
          str(res2["order"]))


# ── [2] --sequential ──────────────────────────────────────────
def check_lanes(label, res, rc_path, lanes, prefix, slot_word):
    """슬롯 스크립트 수·DOE 목록·sbatch 순서·--time(기준 × 칸 F_d 합의 최대)·jobs.json sequential_slot."""
    with open(rc_path, encoding="utf-8") as f:
        fd = doe_time_factors(json.load(f))
    seq = {k: v for k, v in res["files"].items() if k.startswith(prefix)}
    names = sorted(seq)
    check(f"{label}: 슬롯 스크립트 {len(lanes)}개, 슬롯마다 DOE = lpt_lanes {lanes}",
          len(seq) == len(lanes) and [script_does(seq[n]) for n in names] == lanes,
          str([script_does(seq[n]) for n in names]))
    check(f"{label}: sbatch 순서 = 슬롯 0, 1, … ({slot_word})", res["order"] == names, str(res["order"]))
    slot_f = max(sum(fd[d] for d in lane) for lane in lanes)
    want = f"#SBATCH --time={slot_f}:00:00"
    check(f"{label}: 슬롯 --time = 01:00:00 × 칸 F_d 합의 최대 {slot_f} (지금 식)",
          all(sbatch_time(seq[n]) == [want] for n in names), str([sbatch_time(seq[n]) for n in names]))
    j = jobs(res)["jobs"]
    check(f"{label}: jobs.json — DOE 마다 sequential_slot = 칸 번호, 잡 번호 = 칸 순서",
          all(j[str(d)]["sequential_slot"] == i and j[str(d)]["job_id"] == str(res["first"] + i)
              for i, lane in enumerate(lanes) for d in lane), str(j)[:300])


def test_sequential(kcr):
    print("[2] --sequential --nodes K — 칸 수 = 상한 안 무릎, 칸 = lpt_lanes, --time 지금 식")
    tmp, rc = prepared("on_seq")
    res = run_submit(kcr, rc, sequential=True, nodes=8)
    res["first"] = 1001
    knee = S.knee_n(COSTS, 8, 0.05)
    lanes = S.lpt_lanes(COSTS, knee)
    check(f"무릎 {knee} < --nodes 8 (상한 8 = nodes 8·DOE 10)", knee == 7, str(knee))
    check_lanes("nodes 8", res, rc, lanes, "run_seq_", "slot")
    p = plan_of(res)
    check("schedule.json — mode sequential·cap 8(nodes 8, doe_count 10)·knee·lanes",
          p is not None and p["mode"] == "sequential" and p["cap"] == 8
          and p["cap_from"] == {"nodes": 8, "doe_count": 10} and p["knee"] == knee and p["lanes"] == lanes,
          json.dumps(p)[:400] if p else "없음")
    check(f"화면 — 요약 줄·'sequential mode: {knee} nodes'·'Submitted {knee} sequential jobs (10 DOEs across {knee} nodes)'",
          p is not None and S.summary_line(p) in res["out"] and f"sequential mode: {knee} nodes" in res["out"]
          and f"Submitted {knee} sequential jobs (10 DOEs across {knee} nodes)" in res["out"], res["out"][-500:])

    tmp2, rc2 = prepared("on_seq_lic", schedule={"licenses": 6, "licenses_per_job": 2})
    res2 = run_submit(kcr, rc2, sequential=True, nodes=8)
    res2["first"] = 1001
    knee2 = S.knee_n(COSTS, 3, 0.05)
    lanes2 = S.lpt_lanes(COSTS, knee2)
    p2 = plan_of(res2)
    check(f"licenses 6 ÷ licenses_per_job 2 → 상한 3, 무릎 {knee2}",
          p2 is not None and p2["cap"] == 3 and p2["cap_from"] == {"nodes": 8, "licenses": 3, "doe_count": 10}
          and p2["knee"] == knee2 == 3, json.dumps(p2)[:300] if p2 else "없음")
    check_lanes("licenses 상한 3", res2, rc2, lanes2, "run_seq_", "slot")


# ── [3] rerun ───────────────────────────────────────────────────
def test_rerun(kcr):
    print("[3] rerun — 대상 긴 것부터, --does 일부, --sequential rerun 은 대상만으로 짠 무릎·lpt_lanes")
    tmp, rc = prepared("on_rerun")
    sub = run_submit(kcr, rc)
    res = run_rerun(kcr, tmp)
    got = [doe_of(s) for s in res["order"]]
    check(f"rerun(모두 not_started) sbatch 순서 = 긴 것부터 {LPT}", got == LPT, str(got))
    j, j0 = jobs(res)["jobs"], jobs(sub)["jobs"]
    check("rerun jobs.json — 잡 번호 = 다시 낸 순서·prev_job_id = submit 잡·필드 이름 그대로",
          all(j[str(d)]["job_id"] == str(2001 + i) and j[str(d)]["prev_job_id"] == j0[str(d)]["job_id"]
              and list(j[str(d)]) == ["job_id", "job_name", "status", "submitted_at", "script_path", "prev_job_id"]
              for i, d in enumerate(LPT)), str(j)[:300])
    p, ps = plan_of(res, S.RERUN_SCHEDULE_FILE), plan_of(res)
    check("schedule_rerun.json — mode rerun·DOE 10·순서, submit 의 schedule.json 은 mode submit 그대로(덮지 않음)",
          p is not None and p["mode"] == "rerun" and p["order"] == LPT and S.summary_line(p) in res["out"]
          and ps is not None and ps["mode"] == "submit", json.dumps(p)[:300] if p else "없음")

    res2 = run_rerun(kcr, tmp, does="1,5,9,2", first=3001)
    want2 = sorted([1, 5, 9, 2], key=lambda d: (-ENDTIM[d], d))
    got2 = [doe_of(s) for s in res2["order"]]
    p2 = plan_of(res2, S.RERUN_SCHEDULE_FILE)
    check(f"--does 1,5,9,2 → 대상만 긴 것부터 {want2}, schedule_rerun.json 은 대상 4 개로",
          got2 == want2 == [2, 9, 1, 5] and p2 is not None and p2["doe_count"] == 4 and p2["order"] == want2,
          f"{got2} {json.dumps(p2)[:200] if p2 else ''}")

    tmp3, rc3 = prepared("on_rerun_seq")
    run_submit(kcr, rc3)
    res3 = run_rerun(kcr, tmp3, sequential=True, nodes=8, does="1,2,3,4,5,6")
    res3["first"] = 2001
    sub_costs = {d: COSTS[d] for d in range(1, 7)}
    knee3 = S.knee_n(sub_costs, 6, 0.05)   # 노드 8 → 대상 수 6 으로 줄인 뒤의 상한
    lanes3 = S.lpt_lanes(sub_costs, knee3)
    p3 = plan_of(res3, S.RERUN_SCHEDULE_FILE)
    check(f"--sequential rerun --nodes 8 --does 1~6 → 상한 6(대상 수), 무릎 {knee3}, 칸 {lanes3}",
          p3 is not None and p3["cap"] == 6 and p3["knee"] == knee3 == 5 and p3["lanes"] == lanes3
          and p3["doe_count"] == 6, json.dumps(p3)[:300] if p3 else "없음")
    check_lanes("sequential rerun", res3, rc3, lanes3, "rerun_seq_", "rerun slot")
    j3 = jobs(res3)["jobs"]
    check("sequential rerun jobs.json — 대상 DOE 만 rerun true·status resubmitted, 나머지는 submit 그대로",
          all(j3[str(d)].get("rerun") is True and j3[str(d)]["status"] == "resubmitted" for d in range(1, 7))
          and all(j3[str(d)]["status"] == "submitted" and "rerun" not in j3[str(d)] for d in range(7, 11)), str(j3)[:300])
    check("화면 — 'Sequential rerun: 6 DOE를 5개 노드에 분배'", f"6 DOE를 {knee3}개 노드에 분배" in res3["out"],
          res3["out"][-400:])


# ── [4] batch_koomeshmodifier ──────────────────────────────────
def test_batch(kcr):
    print("[4] batch_koomeshmodifier — 함께 보인 .done 은 긴 것부터 낸다")
    tmp, rc = prepared("on_batch", batch=True)
    res = run_submit(kcr, rc)
    got = [doe_of(s) for s in res["order"]]
    check(f"sbatch 순서 = 긴 것부터 {LPT}", got == LPT, str(got))
    check("스크립트는 --skip-koomeshmodifier --pregenerated-dir · schedule.json mode submit",
          all("--skip-koomeshmodifier --pregenerated-dir" in v for k, v in res["files"].items() if k.startswith("run_doe_"))
          and (plan_of(res) or {}).get("order") == LPT, res["out"][-300:])


# ── [5] 틀린 값 ─────────────────────────────────────────────────
def test_bad(kcr):
    print("[5] 틀린 environment.schedule — sbatch 전에 ❌ 종료 1")
    for label, val, seq in (("'yes'", "yes", False), ("licenses 0 (--sequential)", {"licenses": 0}, True)):
        tmp, rc = prepared("bad_submit", schedule=val)
        res = run_submit(kcr, rc, sequential=seq)
        check(f"submit {label}: 종료 1·❌·(bad value)·sbatch 없음·jobs.json·schedule.json·스크립트 없음",
              res["code"] == 1 and "❌" in res["out"] and "(bad value)" in res["out"] and not res["order"]
              and not res["files"], f"{res['code']} {res['order']} {sorted(res['files'])} {res['out'][-300:]}")
    tmp, rc = prepared("bad_rerun")
    run_submit(kcr, rc)
    before = Path(tmp, "jobs.json").read_text(encoding="utf-8")
    with open(rc, encoding="utf-8") as f:
        r = json.load(f)
    r["environment"]["schedule"] = {"seconds_per_ms": 0}
    with open(rc, "w", encoding="utf-8") as f:
        json.dump(r, f, indent=1)
    for seq in (False, True):
        res = run_rerun(kcr, tmp, sequential=seq)
        check(f"rerun{' --sequential' if seq else ''} seconds_per_ms 0: 종료 1·(bad value)·sbatch 없음·jobs.json 그대로",
              res["code"] == 1 and "(bad value)" in res["out"] and not res["order"]
              and res["files"]["jobs.json"] == before, f"{res['code']} {res['order']} {res['out'][-300:]}")


# ── [6] prepare 미리보기 ───────────────────────────────────────
def test_prepare(kcr):
    print("[6] prepare 미리보기 — 표가 있으면 요약 한 줄(노드 없는 상한)")
    tmp = EPT.new_tmp("sched_prep_on_")
    user = EPT.with_presim(EPT.scen_faces2(tmp), {"enabled": True}, koomeshmodifier_path=EPT.write_fake(tmp, "ok"))
    user["environment"]["schedule"] = {"licenses": 3}
    code, out = EPT.cli_prepare(tmp, user)
    with open(os.path.join(tmp, "runner_config.json"), encoding="utf-8") as f:
        rc = json.load(f)
    p = S.build_schedule(rc, S.schedule_options(rc["environment"]), "prepare")
    check("표 있음 + licenses 3: prepare 0·요약 한 줄 = summary_line(prepare 계획)·상한 3(licenses 3, doe_count 6)",
          code == 0 and p is not None and out.count("[schedule]") == 1 and S.summary_line(p) in out
          and p["cap_from"] == {"licenses": 3, "doe_count": 6} and "nodes" not in out.split("[schedule]")[1].split("\n")[0],
          out[-600:])
    check("runner_config 는 그대로 — schedule 은 environment 에 받은 값만, scenario 에 계획 키 없음",
          rc["environment"]["schedule"] == {"licenses": 3} and "doe_endtim" in rc["scenario"]
          and not ({"order", "lanes", "knee", "schedule"} & set(rc["scenario"])), str(list(rc["scenario"])))
    tmp2 = EPT.new_tmp("sched_prep_off_")
    user2 = EPT.with_presim(EPT.scen_faces2(tmp2), {"enabled": True}, koomeshmodifier_path=EPT.write_fake(tmp2, "ok"))
    user2["environment"]["schedule"] = False
    code2, out2 = EPT.cli_prepare(tmp2, user2)
    check("표 있음 + schedule false: 요약 줄 없음", code2 == 0 and "[schedule]" not in out2, out2[-300:])
    tmp3 = EPT.new_tmp("sched_prep_notable_")
    code3, out3 = EPT.cli_prepare(tmp3, EPT.scen_faces2(tmp3))
    check("표 없음: 요약 줄 없음", code3 == 0 and "[schedule]" not in out3 and "✅" in out3, out3[-300:])
    tmp4 = EPT.new_tmp("sched_prep_bad_")
    user4 = EPT.scen_faces2(tmp4)
    user4["environment"]["schedule"] = "yes"
    code4, out4 = EPT.cli_prepare(tmp4, user4)
    check("틀린 값: ❌ 한 줄(bad value) — prepare 는 마치고(0) runner_config 를 쓴다",
          code4 == 0 and "❌" in out4 and "(bad value)" in out4 and "✅" in out4
          and os.path.exists(os.path.join(tmp4, "runner_config.json")), out4[-400:])


def main():
    with contextlib.redirect_stdout(io.StringIO()):
        kcr = EPT.load_kcr()
    if "--print-golden" in sys.argv:   # 바꾸기 전 코드에서만 의미가 있다
        print(json.dumps(off_digests(kcr), indent=1))
        return
    test_off(kcr)
    test_submit(kcr)
    test_sequential(kcr)
    test_rerun(kcr)
    test_batch(kcr)
    test_bad(kcr)
    test_prepare(kcr)
    print()
    if FAILS:
        print("FAIL %d:" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
