#!/usr/bin/env python3
# 남은 결함 묶음 U9 판정 — KooChainRun submit·rerun 의 칸 수·칸 스크립트 다시 내기·겹친 --does·jobs.json 없음·sbatch 실패 종료 코드를 가짜 Slurm 으로 본다
"""남은 결함 묶음(docs/kmm_kcr_remaining_20261121) C1~C4 + sbatch 실패 종료 코드(문서 조사 「확인 필요」 줄).

  [C1] 일정 끔(표 없음)에서 submit --sequential --nodes 가 DOE 수보다 크면 빈 칸의 doe_list[0] 에서 IndexError 로 죽었다
       → 칸을 DOE 수로 줄이고 모두 낸다
  [C2] --sequential 로 낸 뒤 기본 rerun 은 jobs.json 의 칸 스크립트(run_seq_NNN.sh)를 DOE 마다 다시 내 같은 칸이 DOE 수만큼
       겹쳐 돌았다 → 칸 스크립트는 DOE 마다 내지 않고 `rerun --sequential` 을 알린다(종료 코드 1)
  [C3] rerun --does 3,3 은 같은 DOE 를 두 번 냈다 → 한 번
  [C4] jobs.json 없이 rerun 하면 resubmit_does 의 load_jobs 에서 FileNotFoundError 로 죽었다 → 기본 스크립트로 내고 jobs.json 을 쓴다
  [S]  sbatch 가 첫 잡 뒤에 실패해도 'FAILED' 줄만 찍고 종료 코드 0 이었다 → 🔴 + 종료 코드 1(낸 잡은 그대로)

실행: TMPDIR=/data/koopark/<시험 폴더> venv312/bin/python tests/test_remaining_kcr.py   (가짜 sbatch·prepare 몇 번, 수십 초)
수정 전 코드로 볼 때: KCR_ROOT=<옛 리포 사본(KooChainRun·Runner)> …
"""
import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KCR_ROOT = Path(os.environ.get("KCR_ROOT") or ROOT)
sys.path.insert(0, str(KCR_ROOT))
sys.path.insert(0, str(ROOT / "tests"))
import test_kcr_doe_schedule as D   # noqa: E402 — prepare·가짜 Slurm·submit·rerun 도우미
import test_kcr_endtime_presim as EPT   # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print("  %-96s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def load_kcr():
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("kcr_script", str(KCR_ROOT / "KooChainRun"))
    spec = importlib.util.spec_from_loader("kcr_script", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def safe(fn, *a, **k):
    """도우미를 돌리되 예외(옛 코드의 IndexError·FileNotFoundError)는 결과로 바꾼다."""
    try:
        return fn(*a, **k)
    except Exception as e:   # noqa: BLE001 — 옛 코드의 죽음을 판정에 담는다
        return {"order": [], "files": {}, "out": f"{type(e).__name__}: {e}", "code": "exception"}


class FailNth(D.FakeSlurm):
    """n 번째 sbatch 만 실패하는 가짜 Slurm."""

    def __init__(self, first, nth):
        super().__init__(first)
        self.nth = nth

    def __call__(self, cmd, *a, **k):
        if cmd[0] == "sbatch" and len(self.sbatch) + 1 == self.nth:
            self.sbatch.append(os.path.basename(cmd[-1]))
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="sbatch: error: 가짜 실패")
        return super().__call__(cmd, *a, **k)


def c1(kcr):
    print("[C1] 표 없음 submit --sequential --nodes 20 (DOE 10)")
    tmp, rc_path = D.prepared("c1", table=False)
    res = safe(D.run_submit, kcr, rc_path, sequential=True, nodes=20)
    seq = [n for n in res["order"] if n.startswith("run_seq_")]
    check("[C1] 종료 0, 칸 스크립트 10개를 낸다(빈 칸 없음)", res["code"] == 0 and len(seq) == 10, f"{res['code']} {res['order']} {res['out'][-300:]}")


def c2(kcr):
    print("[C2] --sequential 로 낸 뒤 기본 rerun")
    tmp, rc_path = D.prepared("c2", table=False)
    sub = safe(D.run_submit, kcr, rc_path, sequential=True, nodes=3)
    res = safe(D.run_rerun, kcr, tmp, sequential=False)
    seq = [n for n in res["order"] if n.startswith("run_seq_")]
    want = [f"run_doe_{d:03d}.sh" for d in range(1, 11)]
    check("[C2] 칸 스크립트를 DOE 마다 다시 내지 않고(run_seq_* 0번) DOE 하나짜리 스크립트로 한 번씩, 종료 0",
          sub["code"] == 0 and not seq and sorted(res["order"]) == want and res["code"] == 0,
          f"submit {sub['code']} rerun {res['code']} {res['order']} {res['out'][-300:]}")
    tmp, rc_path = D.prepared("c2b", table=False)   # 새로 낸 칸 — DOE 하나짜리 스크립트가 없으면 알리고 내지 않는다
    safe(D.run_submit, kcr, rc_path, sequential=True, nodes=3)
    for f in Path(tmp, "output", "slurm_scripts").glob("run_doe_*.sh"):
        f.unlink()
    res = safe(D.run_rerun, kcr, tmp, sequential=False)
    seq = [n for n in res["order"] if n.startswith("run_seq_")]
    check("[C2] DOE 하나짜리 스크립트가 없으면 칸 스크립트도 내지 않고 `rerun --sequential` 알림 + 종료 1",
          not seq and "rerun --sequential" in res["out"] and res["code"] == 1, f"rerun {res['code']} {res['order']} {res['out'][-300:]}")


def c3(kcr):
    print("[C3] rerun --does 3,3")
    tmp, rc_path = D.prepared("c3", table=False)
    safe(D.run_submit, kcr, rc_path)
    res = safe(D.run_rerun, kcr, tmp, does="3,3")
    check("[C3] DOE 3 을 한 번만 낸다", res["order"] == ["run_doe_003.sh"] and res["code"] == 0, f"{res['code']} {res['order']}")


def c4(kcr):
    print("[C4] jobs.json 없이 rerun")
    tmp, rc_path = D.prepared("c4", table=False)
    safe(D.run_submit, kcr, rc_path)
    Path(tmp, "jobs.json").unlink()
    res = safe(D.run_rerun, kcr, tmp)
    check("[C4] 종료 0, 기본 스크립트로 DOE 10개를 내고 jobs.json 을 쓴다",
          res["code"] == 0 and len(res["order"]) == 10 and Path(tmp, "jobs.json").exists(), f"{res['code']} {res['order']} {res['out'][-300:]}")


def s_fail(kcr):
    print("[S] sbatch 가 둘째 잡에서 실패")
    tmp, rc_path = D.prepared("sfail", table=False)
    args = argparse.Namespace(config=rc_path, mode="cumulative", nodes=8, jobs_per_node=4, ncpu_per_job=None,
                              partition=None, memory=None, time_limit=None, data_root="/data", sequential=False)
    fake, real, buf, code = FailNth(1001, 2), subprocess.run, io.StringIO(), 0
    subprocess.run = fake
    try:
        with contextlib.redirect_stdout(buf):
            kcr._submit_cumulative(args, Path(rc_path))
    except SystemExit as e:
        code = e.code
    finally:
        subprocess.run = real
    out = buf.getvalue()
    check("[S] 나머지는 내고(sbatch 10번) 🔴 + 종료 코드 1", len(fake.sbatch) == 10 and code == 1 and "🔴" in out, f"{code} {len(fake.sbatch)} {out[-300:]}")


def main():
    with contextlib.redirect_stdout(io.StringIO()):
        kcr = load_kcr()
    for f in (c1, c2, c3, c4, s_fail):
        f(kcr)
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}")
    for x in FAILS:
        print("  FAIL", x[:500])
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
