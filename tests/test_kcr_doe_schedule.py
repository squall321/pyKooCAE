# KCR v134 environment.schedule(사전 해석 ENDTIM 으로 긴 것부터 제출·--sequential 무릎 칸·rerun)을 가짜 sbatch 로 검증하는 시험
"""
실행: venv312/bin/python tests/test_kcr_doe_schedule.py      (prepare 마흔 번·가짜 sbatch·가짜 KMM, 십여 초)

  [0] 꺼짐 바이트 동일 — 표 있음 + schedule 끔(submit 경로 false, rerun 경로 {"enabled": false})과 표 없음(기본 켬):
      기본·--sequential·batch 제출, rerun(기본·--sequential)의 sbatch 순서·slurm 스크립트·jobs.json 이 바꾸기 전 코드와 같다
      (정답 sha256 은 바꾸기 전 코드(ddd1a4c)에서 --print-golden 으로 뽑아 박았다. 임시 폴더·KCR 경로·시각·rerun 번호만 바꿔 잰다)
  [1] 기본 제출 — sbatch 순서 = ENDTIM 긴 것부터(같으면 DOE 번호), 스크립트는 끈 것과 같고 jobs.json 은 키·필드 그대로
      (키 순서만 제출 순서), slurm_scripts/schedule.json·요약 한 줄·알림 줄(시간 단위 짐작), 첫 sbatch 가 실패하면
      긴 것부터 첫 DOE 에서 멈춘다
  [2] --sequential --nodes K — 칸 수 = 상한(--nodes·licenses÷licenses_per_job·DOE 수) 안 무릎(knee_tolerance 0), 칸 DOE =
      lpt_lanes(칸 안도 긴 것부터), 칸 --time = 기준 × 칸 F_d 합의 최대(모든 칸 같음), jobs.json sequential_slot, 슬롯 스크립트
      echo 는 DOE 목록, --nodes 보다 적은 칸이면 ⚠️ 한 줄(같으면 없음), 마지막 요약의 칸 수
  [3] rerun — 대상을 긴 것부터, --does 일부, 표 밖 DOE 는 맨 뒤(기본·--sequential), --sequential rerun 은 대상만으로 짠
      무릎·lpt_lanes(--nodes 상한·자동 감지면 다시 짬·칸이 줄면 ⚠️), --dry-run 도 [schedule] 줄
  [4] batch_koomeshmodifier — .done 이 함께 보이면 긴 것부터, KMM 이 끝난 뒤 남은 DOE 도 긴 것부터, --sequential 을 함께
      주면 batch 가 이겨 칸 없이 submit 으로 적는다
  [5] 틀린 environment.schedule — submit·--sequential·rerun 이 sbatch 전에 ❌ 종료 1, jobs.json 을 건드리지 않고 rerun 은
      확인 묻기·--cleanup-stale 지우기 전에 멈춘다. 끔({"enabled": false} + 다른 키)·표 없음이면 값을 보지 않고 경고도 없다
  [6] prepare 미리보기 — 표가 있으면 요약 한 줄과 알림(상한은 licenses·max_concurrent·DOE 수, 노드 없음), 없거나 끄면 없음,
      표가 있을 때 틀린 값은 ❌ 한 줄(prepare 는 마친다), 표가 없으면 값을 보지 않는다
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
TOL = S.DEFAULTS["knee_tolerance"]   # 기본 0 — 완료 시각이 더 줄지 않는 가장 작은 칸 수

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


def prepared(tag, table=True, schedule=UNSET, batch=False, done=True):
    """scen10 을 Designer 로 prepare 한 뒤 runner_config 에 표(scenario.doe_endtim ← ENDTIM)·environment.schedule·batch 를
    넣는다 → (임시 폴더, runner_config 경로). time_limit 은 01:00:00 이다. batch 에서 done=False 면 .done 을 만들지 않는다."""
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
        for d in (ENDTIM if done else ()):
            run = os.path.join(rc["project"]["output_dir"], "pregenerated", f"Run_{d}")
            os.makedirs(run, exist_ok=True)
            Path(run, ".done").write_text("", encoding="utf-8")
    with open(rc_path, "w", encoding="utf-8") as f:
        json.dump(rc, f, indent=1)
    return tmp, rc_path


class FakeSlurm:
    """subprocess.run 가로채기 — sbatch 는 낸 스크립트 이름을 적고 잡 번호를 first 부터 1 씩 늘려 준다(fail_first 면 첫 sbatch 만
    rc 1). sinfo %l(파티션 최대)은 7-00:00:00, 나머지 sinfo·scontrol·sacct·squeue 는 빈 답(노드 없음·상태 모름)이다. 다른 명령은
    시험을 멈춘다."""

    def __init__(self, first, fail_first=False):
        self.sbatch, self.next, self.fail_first = [], first, fail_first

    def __call__(self, cmd, *a, **k):
        if cmd[0] == "sbatch":
            self.sbatch.append(os.path.basename(cmd[-1]))
            if self.fail_first and len(self.sbatch) == 1:
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="sbatch: error: 가짜 실패")
            self.next += 1
            return subprocess.CompletedProcess(cmd, 0, stdout=f"Submitted batch job {self.next - 1}\n", stderr="")
        out = {"sinfo": "7-00:00:00\n" if "%l" in cmd else "", "scontrol": "", "sacct": "", "squeue": ""}.get(cmd[0])
        if out is None:
            raise RuntimeError(f"예상 밖 명령 {cmd}")
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")


class FakeKmmProc:
    """batch KMM 가짜 Popen — 첫 poll() 에서 Run_N/.done 을 모두 만들고 끝났다고 답한다. 첫 폴링에는 .done 이 없으므로
    'KMM 이 끝난 뒤 남은 DOE 를 한 번 더 확인해 내는' 갈래만 돈다."""
    pid = 4242

    def __init__(self, cmd, cwd=None, **kw):
        self.cwd, self.returncode = cwd, None

    def poll(self):
        if self.returncode is None:
            for d in ENDTIM:
                os.makedirs(os.path.join(self.cwd, f"Run_{d}"), exist_ok=True)
                Path(self.cwd, f"Run_{d}", ".done").write_text("", encoding="utf-8")
            self.returncode = 0
        return self.returncode

    def wait(self):
        return self.poll()


def call(fn, args, tmp, first, fail_first=False, popen=None):
    """fn(args) 를 가짜 Slurm 으로 돈다(popen 을 주면 subprocess.Popen 도) → {order: sbatch 낸 스크립트 이름, files:
    slurm_scripts 의 .sh·schedule.json 과 jobs.json 글, out: 화면 출력, code: 종료 코드}."""
    fake = FakeSlurm(first, fail_first)
    real, real_popen, buf, code = subprocess.run, subprocess.Popen, io.StringIO(), 0
    subprocess.run = fake
    if popen is not None:
        subprocess.Popen = popen
    try:
        with contextlib.redirect_stdout(buf):
            fn(args)
    except SystemExit as e:
        code = e.code
    finally:
        subprocess.run, subprocess.Popen = real, real_popen
    slurm = os.path.join(tmp, "output", "slurm_scripts")
    files = {n: Path(slurm, n).read_text(encoding="utf-8") for n in sorted(os.listdir(slurm))
             if n.endswith(".sh") or n in (S.SCHEDULE_FILE, S.RERUN_SCHEDULE_FILE)} if os.path.isdir(slurm) else {}
    if os.path.exists(os.path.join(tmp, "jobs.json")):
        files["jobs.json"] = Path(tmp, "jobs.json").read_text(encoding="utf-8")
    return {"order": fake.sbatch, "files": files, "out": buf.getvalue(), "code": code}


def run_submit(kcr, rc_path, sequential=False, nodes=8, first=1001, fail_first=False, popen=None):
    args = argparse.Namespace(config=rc_path, mode="cumulative", nodes=nodes, jobs_per_node=4, ncpu_per_job=None,
                              partition=None, memory=None, time_limit=None, data_root="/data", sequential=sequential)
    return call(lambda a: kcr._submit_cumulative(a, Path(rc_path)), args, os.path.dirname(rc_path), first, fail_first, popen)


def run_rerun(kcr, tmp, sequential=False, nodes=8, does=None, first=2001, force=True, dry_run=False, cleanup_stale=False):
    """cmd_rerun(기본 --force) — 실행 기록이 없어 모든 DOE 가 not_started 라 대상은 모두(또는 --does)다."""
    args = argparse.Namespace(test_dir=tmp, dry_run=dry_run, force=force, does=does, exclude_nodes=None,
                              sequential=sequential, nodes=nodes, cleanup_stale=cleanup_stale)
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
    check("알림 줄 — 표 메타가 없어 tFinal 0.004 로 s 를 짐작했다는 알림을 요약 줄 아래에 찍는다",
          p is not None and len(p["notes"]) == 1 and "tFinal 0.004" in p["notes"][0] and "s 로 짐작" in p["notes"][0]
          and f"    · {p['notes'][0]}" in res["out"], str(p and p["notes"]))
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

    tmp3, rc3 = prepared("on_submit_firstfail")
    res3 = run_submit(kcr, rc3, fail_first=True)
    check("켬: 첫 sbatch(긴 것부터 첫 DOE 4)가 실패하면 거기서 멈춘다 — 종료 1·sbatch 1번·'sbatch 실행 불가'",
          res3["code"] == 1 and res3["order"] == ["run_doe_004.sh"] and "sbatch 실행 불가" in res3["out"],
          f"{res3['code']} {res3['order']} {res3['out'][-300:]}")


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
    if prefix == "run_seq_":   # 켜면 칸 안 DOE 는 긴 것부터라 echo 는 범위가 아니라 목록(앞 6 개 + …)이다
        echo = [f'echo "DOEs: {doe_label(lane)} ({len(lane)}ea)"' for lane in lanes]
        check(f"{label}: 슬롯 스크립트 echo 'DOEs: {doe_label(lanes[-1])} …' — 범위 아닌 DOE 목록",
              all(e in seq[n].splitlines() for e, n in zip(echo, names)), str(echo[:2]))


def doe_label(lane):
    return ", ".join(map(str, lane[:6])) + (" …" if len(lane) > 6 else "")


def test_sequential(kcr):
    print("[2] --sequential --nodes K — 칸 수 = 상한 안 무릎(knee_tolerance 0), 칸 = lpt_lanes, --time 지금 식, 줄면 ⚠️")
    check("기본 knee_tolerance 0", TOL == 0.0, str(TOL))
    tmp, rc = prepared("on_seq")
    res = run_submit(kcr, rc, sequential=True, nodes=10)
    res["first"] = 1001
    knee = S.knee_n(COSTS, 10, TOL)
    lanes = S.lpt_lanes(COSTS, knee)
    check(f"무릎 {knee} < --nodes 10 — 칸 9 로도 완료 700 s 가 칸 10 과 같다(칸 8 은 720 s)",
          knee == 9 and S.makespan(COSTS, 9) == S.makespan(COSTS, 10) == 700.0 < S.makespan(COSTS, 8), str(knee))
    check_lanes("nodes 10", res, rc, lanes, "run_seq_", "slot")
    p = plan_of(res)
    check("schedule.json — mode sequential·cap 10(nodes 10, doe_count 10)·knee·lanes",
          p is not None and p["mode"] == "sequential" and p["cap"] == 10
          and p["cap_from"] == {"nodes": 10, "doe_count": 10} and p["knee"] == knee and p["lanes"] == lanes,
          json.dumps(p)[:400] if p else "없음")
    check(f"화면 — 요약 줄·'sequential mode: {knee} nodes'·'Submitted {knee} sequential jobs (10 DOEs across {knee} nodes)'",
          p is not None and S.summary_line(p) in res["out"] and f"sequential mode: {knee} nodes" in res["out"]
          and f"Submitted {knee} sequential jobs (10 DOEs across {knee} nodes)" in res["out"], res["out"][-500:])
    line = S.fewer_slots_line(p, 10, "--sequential: --nodes") if p else None
    check("⚠️ 한 줄 — '--nodes 10 가운데 9 칸만 쓴다 — 나머지를 써도 예상 완료가 줄지 않는다(무릎, knee_tolerance 0)'",
          line is not None and line in res["out"] and res["out"].count("칸만 쓴다") == 1
          and "--nodes 10 가운데 9 칸만 쓴다 — 나머지를 써도 예상 완료가 줄지 않는다(무릎, knee_tolerance 0)" in line
          and "예상 완료 0.19 h (10 칸 0.19 h)" in line, line or res["out"][-400:])

    tmp1, rc1 = prepared("on_seq8")
    res1 = run_submit(kcr, rc1, sequential=True, nodes=8)
    res1["first"] = 1001
    lanes1 = S.lpt_lanes(COSTS, 8)
    check("--nodes 8 → 무릎 8 = --nodes, ⚠️ 줄 없음", (plan_of(res1) or {}).get("knee") == S.knee_n(COSTS, 8, TOL) == 8
          and "칸만 쓴다" not in res1["out"], res1["out"][-300:])
    check_lanes("nodes 8", res1, rc1, lanes1, "run_seq_", "slot")

    tmp2, rc2 = prepared("on_seq_lic", schedule={"licenses": 6, "licenses_per_job": 2})
    res2 = run_submit(kcr, rc2, sequential=True, nodes=8)
    res2["first"] = 1001
    knee2 = S.knee_n(COSTS, 3, TOL)
    lanes2 = S.lpt_lanes(COSTS, knee2)
    p2 = plan_of(res2)
    check(f"licenses 6 ÷ licenses_per_job 2 → 상한 3, 무릎 {knee2}",
          p2 is not None and p2["cap"] == 3 and p2["cap_from"] == {"nodes": 8, "licenses": 3, "doe_count": 10}
          and p2["knee"] == knee2 == 3, json.dumps(p2)[:300] if p2 else "없음")
    check_lanes("licenses 상한 3", res2, rc2, lanes2, "run_seq_", "slot")
    check("⚠️ 한 줄 — '--nodes 8 가운데 3 칸만 쓴다 — 상한 3(licenses 3)'",
          p2 is not None and "⚠️  --sequential: --nodes 8 가운데 3 칸만 쓴다 — 상한 3(licenses 3) · 예상 완료" in res2["out"]
          and "무릎" not in S.fewer_slots_line(p2, 8, "--sequential: --nodes"), res2["out"][-400:])


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
    knee3 = S.knee_n(sub_costs, 6, TOL)   # 노드 8 → 대상 수 6 으로 줄인 뒤의 상한
    lanes3 = S.lpt_lanes(sub_costs, knee3)
    p3 = plan_of(res3, S.RERUN_SCHEDULE_FILE)
    check(f"--sequential rerun --nodes 8 --does 1~6 → 상한 6(대상 수), 무릎 {knee3}, 칸 {lanes3}",
          p3 is not None and p3["cap"] == 6 and p3["knee"] == knee3 == 6 and p3["lanes"] == lanes3
          and p3["doe_count"] == 6, json.dumps(p3)[:300] if p3 else "없음")
    check_lanes("sequential rerun", res3, rc3, lanes3, "rerun_seq_", "rerun slot")
    j3 = jobs(res3)["jobs"]
    check("sequential rerun jobs.json — 대상 DOE 만 rerun true·status resubmitted, 나머지는 submit 그대로",
          all(j3[str(d)].get("rerun") is True and j3[str(d)]["status"] == "resubmitted" for d in range(1, 7))
          and all(j3[str(d)]["status"] == "submitted" and "rerun" not in j3[str(d)] for d in range(7, 11)), str(j3)[:300])
    check("화면 — 'Sequential rerun: 6 DOE를 6개 노드에 분배'·[schedule] 한 번·⚠️ 없음",
          f"6 DOE를 {knee3}개 노드에 분배" in res3["out"] and res3["out"].count("[schedule]") == 1
          and "칸만 쓴다" not in res3["out"], res3["out"][-400:])

    tmp4, rc4 = prepared("on_rerun_seq3")   # --nodes 가 대상보다 적으면 그 노드 수가 상한이다
    run_submit(kcr, rc4)
    res4 = run_rerun(kcr, tmp4, sequential=True, nodes=3)
    res4["first"] = 2001
    lanes4 = S.lpt_lanes(COSTS, S.knee_n(COSTS, 3, TOL))
    p4 = plan_of(res4, S.RERUN_SCHEDULE_FILE)
    check("--sequential rerun --nodes 3(대상 10) → 상한 3(nodes 3)·칸 3",
          p4 is not None and p4["cap_from"] == {"nodes": 3, "doe_count": 10} and p4["knee"] == 3 and p4["lanes"] == lanes4,
          json.dumps(p4)[:300] if p4 else "없음")
    check_lanes("rerun --nodes 3", res4, rc4, lanes4, "rerun_seq_", "rerun slot")

    tmp5, rc5 = prepared("on_rerun_seq10")
    run_submit(kcr, rc5)
    res5 = run_rerun(kcr, tmp5, sequential=True, nodes=10)
    p5 = plan_of(res5, S.RERUN_SCHEDULE_FILE)
    check("--sequential rerun --nodes 10 → 무릎 9, ⚠️ 'rerun --sequential: 노드 10 가운데 9 칸만 쓴다'",
          p5 is not None and p5["knee"] == 9 and S.fewer_slots_line(p5, 10, "rerun --sequential: 노드") in res5["out"]
          and "⚠️  rerun --sequential: 노드 10 가운데 9 칸만 쓴다" in res5["out"], res5["out"][-400:])

    tmp6, rc6 = prepared("on_rerun_seqauto")   # --nodes 없음 → 자동 감지(가짜 sinfo 빈 답 → 1 노드) 뒤 다시 짠다
    run_submit(kcr, rc6)
    res6 = run_rerun(kcr, tmp6, sequential=True, nodes=None)
    p6 = plan_of(res6, S.RERUN_SCHEDULE_FILE)
    check("--sequential rerun 자동 감지(1 노드) → 노드 수로 다시 짠 계획: 상한 1(nodes 1)·칸 1 = 긴 것부터 모두",
          p6 is not None and p6["cap_from"] == {"nodes": 1, "doe_count": 10} and p6["lanes"] == [LPT]
          and res6["out"].count("[schedule]") == 2 and "자동 감지된 노드 수: 1" in res6["out"], res6["out"][-500:])

    # 표 밖 DOE(doe_count 10 밖의 11) — 계획은 표 안 DOE 만, 11 은 받은 순서대로 맨 뒤에 그대로 낸다(예전처럼 그 DOE 만 실패)
    tmp7, rc7 = prepared("on_rerun_oor")
    run_submit(kcr, rc7)
    Path(tmp7, "output", "slurm_scripts", "run_doe_011.sh").write_text("#!/bin/bash\n# 표 밖 DOE 시험용\n", encoding="utf-8")
    res7 = run_rerun(kcr, tmp7, does="11,5,3")
    p7 = plan_of(res7, S.RERUN_SCHEDULE_FILE)
    check("rerun --does 11,5,3 → 계획은 3·5(긴 것부터), 11 은 맨 뒤 — sbatch 3, 5, 11 · 알림 '표 밖 DOE [11]'",
          [doe_of(s) for s in res7["order"]] == [3, 5, 11] and p7 is not None and p7["order"] == [3, 5]
          and p7["doe_count"] == 2 and "    · 표 밖 DOE [11] 는 계획에서 빼고 맨 뒤에 그대로 낸다" in res7["out"],
          f"{res7['order']} {res7['out'][-400:]}")
    res8 = run_rerun(kcr, tmp7, sequential=True, nodes=2, does="3,11", first=4001)
    seq8 = [v for k, v in sorted(res8["files"].items()) if k.startswith("rerun_seq_")]
    check("--sequential rerun --does 3,11 → 칸 1 개에 DOE 3 다음 11(맨 뒤)",
          len(seq8) == 1 and script_does(seq8[0]) == [3, 11] and (plan_of(res8, S.RERUN_SCHEDULE_FILE) or {}).get("lanes") == [[3]],
          f"{[script_does(s) for s in seq8]} {res8['out'][-300:]}")

    res9 = run_rerun(kcr, tmp, dry_run=True, first=5001)
    check("--dry-run 도 [schedule] 줄을 찍는다 — sbatch 없음·schedule_rerun.json 은 앞 rerun(--does 4 개) 그대로",
          "[schedule] DOE 10" in res9["out"] and "[DRY-RUN]" in res9["out"] and not res9["order"]
          and (plan_of(res9, S.RERUN_SCHEDULE_FILE) or {}).get("doe_count") == 4, res9["out"][-300:])


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
    tmp2, rc2 = prepared("on_batch_late", batch=True, done=False)
    res2 = run_submit(kcr, rc2, popen=FakeKmmProc)
    check(f"KMM 이 끝난 뒤 한 번 더 확인해 내는 DOE 도 긴 것부터 {LPT}",
          [doe_of(s) for s in res2["order"]] == LPT and "KooMeshModifier 종료 (exit code: 0)" in res2["out"],
          f"{res2['order']} {res2['out'][-300:]}")
    tmp3, rc3 = prepared("on_batch_seq", batch=True)
    res3 = run_submit(kcr, rc3, sequential=True, nodes=4)
    p3 = plan_of(res3)
    check("batch + --sequential → batch 가 이긴다: schedule.json mode submit·칸 없음·DOE 잡 긴 것부터·⚠️ 없음·요약 'across 4 nodes'",
          p3 is not None and p3["mode"] == "submit" and "lanes" not in p3 and [doe_of(s) for s in res3["order"]] == LPT
          and not any(k.startswith("run_seq_") for k in res3["files"]) and "칸만 쓴다" not in res3["out"]
          and "across 4 nodes" in res3["out"], f"{p3 and p3['mode']} {res3['order']} {res3['out'][-300:]}")


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
    # 확인 묻기(--force 없음)·--cleanup-stale 지우기보다 먼저 멈춘다 — 끝나지 않은 Run 폴더가 남아 있어야 한다
    from Runner.JobManager import JobManager
    alias = JobManager(tmp)._generate_alias(r, 1, 1)
    stale = Path(r["project"]["output_dir"], "Run_stale_1")
    stale.mkdir(parents=True, exist_ok=True)
    Path(r["project"]["index_file"]).write_text(json.dumps(
        {"scenarios": [{"runs": {alias: {"status": "failed", "folder": stale.name}}}]}), encoding="utf-8")
    import builtins
    asked, real_input = [], builtins.input
    builtins.input = lambda prompt="": asked.append(prompt) or "y"
    try:
        res = run_rerun(kcr, tmp, force=False, cleanup_stale=True)
    finally:
        builtins.input = real_input
    check("rerun --cleanup-stale(확인 묻기) + 틀린 값 → 묻기 전에 종료 1·끝나지 않은 Run 폴더 그대로·sbatch 없음",
          res["code"] == 1 and not asked and stale.is_dir() and not res["order"] and "(bad value)" in res["out"],
          f"{res['code']} {asked} {stale.is_dir()} {res['out'][-300:]}")

    # 끔·표 없음이면 값을 보지 않는다 — 다른 키가 틀려도 예전 그대로, 모르는 키 경고도 없다
    for label, table, val in (('{"enabled": false, "licenses": 0}', True, {"enabled": False, "licenses": 0}),
                              ("표 없음 + 'yes'", False, "yes"),
                              ('{"enabled": false, "licence": 2}', True, {"enabled": False, "licence": 2}),
                              ("표 없음 + {'licence': 2, 'licenses': 0}", False, {"licence": 2, "licenses": 0})):
        tmp, rc = prepared("off_badkeys", table=table, schedule=val)
        res = run_submit(kcr, rc)
        check(f"{label} → 꺼짐과 같다: 종료 0·DOE 번호 순서 10개·schedule.json·[schedule]·❌·모르는 키 경고 없음",
              res["code"] == 0 and [doe_of(s) for s in res["order"]] == list(range(1, 11))
              and S.SCHEDULE_FILE not in res["files"] and "[schedule]" not in res["out"] and "❌" not in res["out"]
              and "모르는 키" not in res["out"], f"{res['code']} {res['order']} {res['out'][-300:]}")


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
    user4 = EPT.with_presim(EPT.scen_faces2(tmp4), {"enabled": True}, koomeshmodifier_path=EPT.write_fake(tmp4, "ok"))
    user4["environment"]["schedule"] = "yes"
    code4, out4 = EPT.cli_prepare(tmp4, user4)
    check("표 있음 + 틀린 값: ❌ 한 줄(bad value) — prepare 는 마치고(0) runner_config 를 쓴다",
          code4 == 0 and "❌" in out4 and "(bad value)" in out4 and "✅" in out4 and "[schedule]" not in out4
          and os.path.exists(os.path.join(tmp4, "runner_config.json")), out4[-400:])
    tmp5 = EPT.new_tmp("sched_prep_bad_notable_")
    user5 = EPT.scen_faces2(tmp5)
    user5["environment"]["schedule"] = "yes"
    code5, out5 = EPT.cli_prepare(tmp5, user5)
    check("표 없음 + 틀린 값: 값을 보지 않는다 — ❌·[schedule] 없이 prepare 0", code5 == 0 and "❌" not in out5
          and "[schedule]" not in out5 and "✅" in out5, out5[-400:])

    # 알림 — table 지름길 표에 time_unit 메타가 없고 units=mm-t-s 만 있으면 s 로 보고 요약 줄 아래에 알린다
    import Runner.EndTimePresim as EP
    sys.path.insert(0, str(EPT.GEN))
    from KooCAEManager.KooEndTimeTable import write_endtime_table
    tmp6 = EPT.new_tmp("sched_prep_units_")
    rc0, _ = EPT.designer_prepare(tmp6, EPT.scen_faces2(tmp6))
    angles = EP.collect_drop_angles(rc0["scenario"]["doe_angles"], rc0["scenario"]["steps"])
    os.makedirs(os.path.join(tmp6, "tables"))
    write_endtime_table(os.path.join(tmp6, "tables", "t.csv"),
                        [{"name": n, "roll": r, "pitch": pt, "yaw": y, "endtim": round(0.01 + 0.001 * i, 6)}
                         for i, (n, r, pt, y) in enumerate(angles)], {"height": 1000, "units": "mm-t-s"})
    code6, out6 = EPT.cli_prepare(tmp6, EPT.with_presim(EPT.scen_faces2(tmp6), {"enabled": True, "table": "tables/t.csv"},
                                                        koomeshmodifier_path=EPT.write_fake(tmp6, "rc1")))
    with open(os.path.join(tmp6, "runner_config.json"), encoding="utf-8") as f:
        rc6 = json.load(f)
    p6 = S.build_schedule(rc6, S.schedule_options(rc6["environment"]), "prepare")
    check("표 메타 units=mm-t-s 만 → s, 알림 줄을 요약 줄 아래에 찍는다",
          code6 == 0 and p6 is not None and p6["notes"] == ["표 메타 time_unit 이 없어 units mm-t-s 의 끝 s 를 덱 시간 단위로 본다"]
          and f"{S.summary_line(p6)}\n    · {p6['notes'][0]}\n" in out6, out6[-500:])


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
