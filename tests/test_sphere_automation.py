# sphere_report 자동화(런 수 기반 자원·옵션 탐지·조용한 0건·파트별 항복응력 맵) 회귀 시험
"""
실행: venv312/bin/python tests/test_sphere_automation.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … ([3] 만 KMM 에 의존 — 컴파일본은 KMM_BIN=<KooMeshModifier>)

배경 (2026-10-26, 「sphere_report 자동화 수정안 v1.0」): sphere 잡이 런 수와 무관하게 LS-DYNA 런 환경값(8코어·32G)과 고정
시간을 받아 979런 캠페인이 24h TIMEOUT·MaxRSS 84.7 GB 로 산출물 0개였다. 도구는 결과 0건이어도 rc 0 이었고, 항복응력은
350 하나였다.
  [1] build_sphere_sbatch 가 런 수로 자원을 잰다 — 옛 도구 32+0.10 GB/런·2코어, 새 도구(--parallel-runs) 6+2 GB/워커,
      시간 2h+0.06h×N/W(최소 4h). 명시값보다 산출값이 크면 산출값, 파티션 한도를 넘으면 한도로(알림).
  [2] sphere_report.sh 가 실행 시점에 --help 로 --parallel-runs·--yield-map 을 확인해 넘기고, 'Loaded 0 results' 면 비 0 종료.
  [3] KMM 이 DropSet.json 에 model.part_yield 를 쓴다(R16: MAT_024 SIGY 는 LCSS>0 이면 무시 — 커브의 εp=0 값, 가로축
      SFA×(x+OFFA)·세로축 SFO×(y+OFFO), 사이면 보간·밖이면 외삽 — EPS1 이 0 이 아니면 외삽한다).
"""
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
GEN = Path(os.environ.get("KMM_GEN", ROOT / "occProject" / "Generators"))
PY = str(ROOT / "venv312" / "bin" / "python")
KMM_CMD = [os.environ["KMM_BIN"]] if os.environ.get("KMM_BIN") else [PY, str(GEN / "KooMeshModifier.py")]
ENV = dict(os.environ, PATH=str(ROOT / "venv312" / "bin") + ":" + os.environ.get("PATH", ""))
BASE = Path(tempfile.mkdtemp(prefix="sphere_auto_"))
FAILS = []


def check(name, cond, detail=""):
    print("  %-80s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def sbatch_values(text):
    get = lambda k: (re.search(rf"^#SBATCH --{k}=(\S+)", text, re.M) or [None, None])[1]
    return get("cpus-per-task"), get("mem"), get("time")


def test_sizing():
    print("[1] sbatch 자원 — 런 수로")
    import io, contextlib
    from Runner import PostprocessShellGenerator as P
    rc = {"scenarios": [{"steps": [{}] * 600}, {"steps": [{}] * 379}]}
    check("count_runs = step 총수(979)", P.count_runs(rc) == 979)
    check("count_runs 빈 설정 → None", P.count_runs({}) is None and P.count_runs(None) is None)

    def build(n, flags=frozenset(), opts=None, env=None, limits=None):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            t = P.build_sphere_sbatch("/data/x/output", sif_path="/x.sif", options=opts or {}, environment=env or {},
                                      dependency_ids=["1"], n_runs=n, tool_flags=set(flags), limits=limits or {})
        return sbatch_values(t), buf.getvalue()

    (c, m, t), _ = build(979)
    check("옛 도구 979런: 2코어·130G·2-12:45:00", (c, m, t) == ("2", "130G", "2-12:45:00"), str((c, m, t)))
    (c, m, t), _ = build(979, {"--parallel-runs"})
    check("새 도구 979런: 16워커·38G·05:41:00", (c, m, t) == ("16", "38G", "05:41:00"), str((c, m, t)))
    (c, m, t), _ = build(100)
    check("옛 도구 100런: 2코어·42G·08:00:00", (c, m, t) == ("2", "42G", "08:00:00"), str((c, m, t)))
    (c, m, t), _ = build(30, {"--parallel-runs"})
    check("새 도구 30런: 최소 2워커·10G·최소 4h", (c, m, t) == ("2", "10G", "04:00:00"), str((c, m, t)))
    (c, m, t), _ = build(100, env={"ncpu": 8, "memory": "32G"})
    check("LS-DYNA environment 의 ncpu·memory 를 물려받지 않음", (c, m) == ("2", "42G"), str((c, m)))
    (c, m, t), out = build(979, opts={"sphere_time_limit": "04:00:00", "sphere_memory": "16G"})
    check("MCP 기본 04:00:00·16G 보다 산출값이 크면 산출값", (m, t) == ("130G", "2-12:45:00"), str((m, t)))
    check("  그 사실을 알림", "산출값을 쓴다" in out and "16G" in out, out[-300:])
    (c, m, t), _ = build(100, opts={"sphere_time_limit": "3-00:00:00", "sphere_memory": "200G"})
    check("명시값이 산출값보다 크면 명시값", (m, t) == ("200G", "3-00:00:00"), str((m, t)))
    (c, m, t), _ = build(979, {"--parallel-runs"}, opts={"sphere_ncpu": 8})
    check("명시 sphere_ncpu=8 + 새 도구: 8워커 기준 22G·09:21:00", (c, m, t) == ("8", "22G", "09:21:00"), str((c, m, t)))
    (c, m, t), out = build(979, limits={"max_minutes": 1440, "max_mem_gb": 96.0})
    check("파티션 한도(1일·96G)로 줄임", (m, t) == ("96G", "1-00:00:00"), str((m, t)))
    check("  🔴 로 알림", out.count("🔴") == 2, out[-400:])
    (c, m, t), _ = build(979, opts={"sphere_auto_resources": False}, env={"ncpu": 8, "memory": "32G"})
    check("sphere_auto_resources=false → 예전 규칙(8·32G·04:00:00)", (c, m, t) == ("8", "32G", "04:00:00"), str((c, m, t)))
    import contextlib as _c
    with _c.redirect_stdout(io.StringIO()):
        t0 = P.build_sphere_sbatch("/data/x/output", options={}, environment={"ncpu": 4, "memory": "8G"})
    check("n_runs 없으면 예전 규칙(environment 4·8G)", sbatch_values(t0)[:2] == ("4", "8G"), str(sbatch_values(t0)))
    check("_slurm_minutes", [P._slurm_minutes(x) for x in ("1-00:00:00", "06:00:00", "30:00", "45", "2-12", "UNLIMITED")]
          == [1440, 360, 30, 45, 3600, None])
    check("_mem_gb", [P._mem_gb(x) for x in ("32G", "32000M", "1T", "16000", "x")] == [32.0, 31.25, 1024.0, 15.625, None])
    # 파티션 한도 — 시나리오가 파티션을 안 주면 잡은 기본 파티션(Default=YES)으로 간다(sbatch 에 --partition 없음)
    fb = BASE / "fake_slurm"
    fb.mkdir()
    (fb / "scontrol").write_text(
        '#!/bin/bash\n[ "$1" = -o ] && shift\n[ "$1" = show ] && [ "$2" = partition ] || exit 0\n'
        'n="PartitionName=normal AllowGroups=ALL Default=YES MaxNodes=UNLIMITED MaxTime=2-00:00:00 State=UP"\n'
        'v="PartitionName=viz AllowGroups=ALL Default=NO MaxNodes=UNLIMITED MaxTime=60-00:00:00 State=UP"\n'
        'u="PartitionName=nomem AllowGroups=ALL Default=NO MaxNodes=UNLIMITED MaxTime=UNLIMITED State=UP"\n'
        'case "$3" in "") echo "$n"; echo "$v"; echo "$u";; normal) echo "$n";; viz) echo "$v";; nomem) echo "$u";; esac\n')
    # 실제 sinfo 처럼 — -N 이면 노드마다 '%c %m', 아니면 파티션 요약(노드가 섞이면 %m 은 최솟값 + '+', man sinfo)
    (fb / "sinfo").write_text(
        '#!/bin/bash\nN=0; for a in "$@"; do [ "$a" = -N ] && N=1; done\n'
        'case " $* " in\n'
        '  *viz*) if [ $N = 1 ]; then echo "2 3584"; echo "8 18997"; else echo "3584+"; fi ;;\n'
        '  *normal*) if [ $N = 1 ]; then echo "2 64000"; echo "2 64000"; else echo "64000"; fi ;;\n'
        '  *nomem*) if [ $N = 1 ]; then echo "4 1"; else echo "1"; fi ;;\n'
        'esac\n')
    for f in ("scontrol", "sinfo"):
        (fb / f).chmod(0o755)
    old_path = os.environ["PATH"]
    os.environ["PATH"] = f"{fb}:{old_path}"
    try:
        lim_default, lim_viz, lim_nomem = P.partition_limits(""), P.partition_limits("viz"), P.partition_limits("nomem")
    finally:
        os.environ["PATH"] = old_path
    check("파티션 없음 → 기본 파티션(normal) 한도 2일·2코어·62.5G",
          lim_default == {"max_minutes": 2880, "nodes": [(2, 62.5)], "max_cpus": 2, "max_mem_gb": 62.5}, str(lim_default))
    check("파티션 viz(3584MB·18997MB 노드) → 노드별 최댓값 8코어·18.55G(요약 '3584+' 는 최솟값)",
          lim_viz == {"max_minutes": 86400, "nodes": [(2, 3.5), (8, 18997 / 1024)], "max_cpus": 8, "max_mem_gb": 18997 / 1024},
          str(lim_viz))
    check("RealMemory 미설정(1MB) 노드 → 메모리 모름(None), 메모리 상한 없음",
          lim_nomem == {"max_minutes": None, "nodes": [(4, None)], "max_cpus": 4}, str(lim_nomem))
    # 노드가 감당할 수 있게 — CPU 상한, 새 도구는 워커 수를 CPU·메모리에 맞춰 다시 잰다
    (c, m, t), out = build(979, {"--parallel-runs"}, limits={"max_cpus": 2})
    check("새 도구 + 노드 2코어: 워커 2 로 줄여 다시 잼(10G)", (c, m) == ("2", "10G"), str((c, m, t)))
    check("  그 사실을 알림", "워커 16 → 2" in out and "코어 2" in out, out[-300:])
    (c, m, t), out = build(979, {"--parallel-runs"}, limits={"max_mem_gb": 32.0})
    check("새 도구 + 노드 32G: 워커 13 으로 맞춤(32G·06:32:00)", (c, m, t) == ("13", "32G", "06:32:00"), str((c, m, t)))
    (c, m, t), _ = build(979, limits={"max_cpus": 1})
    check("옛 도구 + 노드 1코어: CPU 1", c == "1", str((c, m, t)))
    # 섞인 노드 — 요청은 한 노드에 들어가야 한다(코어 최대 노드와 메모리 최대 노드가 다르면 따로 잰 최댓값은 어느 노드에도 안 맞는다)
    mixed = {"nodes": [(64, 16.0), (4, 256.0)]}
    (c, m, t), _ = build(979, {"--parallel-runs"}, limits=mixed)
    check("새 도구 + 노드 64c/16G·4c/256G: 64코어 노드에 맞춘 5워커(16G·13:45:00)", (c, m, t) == ("5", "16G", "13:45:00"), str((c, m, t)))
    (c, m, t), out = build(100, opts={"sphere_ncpu": 32}, limits=mixed)
    check("옛 도구 + ncpu 32 + 같은 노드: 메모리 큰 노드에 맞춰 4코어·42G", (c, m, t) == ("4", "42G", "08:00:00"), f"{(c, m, t)} {out[-200:]}")
    (c, m, t), _ = build(979, {"--parallel-runs"}, limits={"nodes": [(32, 8.0), (8, 64.0)]})
    check("새 도구 + 노드 32c/8G·8c/64G: 8워커(22G·09:21:00)", (c, m, t) == ("8", "22G", "09:21:00"), str((c, m, t)))
    (c, m, t), out = build(979, limits={"nodes": [(64, 0.5)]})
    check("노드 메모리 1GB 밑(미설정)은 모름 — --mem=0G 를 내지 않음", m == "130G" and "🔴" not in out, f"{m} {out[-200:]}")
    # 명시 '제한 없음' — man sbatch: 시간 0·UNLIMITED 는 제한 없음, --mem=0 은 노드 메모리 전부
    (c, m, t), _ = build(979, {"--parallel-runs"}, opts={"sphere_time_limit": "UNLIMITED"})
    check("명시 UNLIMITED 는 무제한 — 그대로", t == "UNLIMITED", t)
    (c, m, t), out = build(979, {"--parallel-runs"}, opts={"sphere_time_limit": "0"}, limits={"max_minutes": 2880})
    check("명시 0(무제한) + 파티션 2일 → 2-00:00:00(산출값은 한도 안이라 🔴 아님)", t == "2-00:00:00" and "🔴" not in out,
          f"{t} {out[-300:]}")
    (c, m, t), out = build(979, opts={"sphere_memory": "0"}, limits={"max_mem_gb": 62.5})
    check("명시 메모리 0(노드 전부) — 그대로, 상한 검사 안 함", m == "0" and "🔴" not in out, f"{m} {out[-300:]}")
    # sphere_ncpu 가 글이어도 submit 이 죽지 않는다(LS-DYNA 잡을 다 낸 뒤라 traceback 이면 sphere 잡이 빠진다)
    (c, m, t), _ = build(979, {"--parallel-runs"}, opts={"sphere_ncpu": "8.0"})
    check("sphere_ncpu '8.0' → 8워커(22G·09:21:00)", (c, m, t) == ("8", "22G", "09:21:00"), str((c, m, t)))
    (c, m, t), out = build(979, {"--parallel-runs"}, opts={"sphere_ncpu": "auto"})
    check("sphere_ncpu 'auto' → 무시하고 산출값(16)·알림", c == "16" and "읽지 못해" in out, f"{c} {out[-300:]}")
    # --help 탐지 — 실제 argparse 출력으로(metavar 없음 → 'PARALLEL_RUNS', 별칭, nargs='?', 다른 옵션 설명 글 속 언급만)
    import argparse

    def ap_help(kind):
        ap = argparse.ArgumentParser(prog="koo_sphere_report")
        ap.add_argument("--yield-stress", type=float, help="항복응력 (--parallel-runs·--yield-map 은 새 판에만)")
        if kind == "plain":
            ap.add_argument("--parallel-runs", type=int)
            ap.add_argument("--yield-map")
        elif kind == "alias":
            ap.add_argument("-j", "--parallel-runs", type=int, help="런 병렬 수 " * 8)
        elif kind == "optional":
            ap.add_argument("--parallel-runs", nargs="?", const=4, type=int)
        return ap.format_help()
    want = {"plain": (True, True), "alias": (True, False), "optional": (True, False), "old": (False, False)}
    got = {k: (P._help_has_option(ap_help(k), "--parallel-runs"), P._help_has_option(ap_help(k), "--yield-map")) for k in want}
    check("argparse 도움말: metavar 없음·별칭·nargs='?' 는 잡고, 설명 글 속 언급만 있으면 안 잡음", got == want, str(got))
    # 리뷰 M — choices 안 쉼표·nargs=2·nargs='*'·좁은 화면에서 접힌 설명 글 머리·epilog 의 0열 글. Python 과 셸이 같아야 한다
    def ap_more(kind):
        os.environ["COLUMNS"] = "60" if kind == "narrow_old" else "100"
        fmt = argparse.RawDescriptionHelpFormatter
        ap = argparse.ArgumentParser(prog="koo_sphere_report", formatter_class=fmt,
                                     epilog="notes:\n\n--parallel-runs and --yield-map need the v2 SIF; this build has neither."
                                     if kind == "epilog_old" else None)
        if kind == "choices":
            ap.add_argument("-j", "--parallel-runs", type=int, choices=[1, 2, 4, 8, 16])
        elif kind == "nargs2":
            ap.add_argument("-y", "--yield-map", nargs=2)
        elif kind == "star":
            ap.add_argument("-j", "--parallel-runs", nargs="*", type=int)
        elif kind == "narrow_old":
            ap.add_argument("--yield-stress", type=float, help="항복응력 기본값 350 — 새 판 도구는 --parallel-runs 와 --yield-map 을 함께 쓴다")
        try:
            return ap.format_help()
        finally:
            os.environ.pop("COLUMNS", None)
    want2 = {"choices": (True, False), "nargs2": (False, True), "star": (True, False), "narrow_old": (False, False),
             "epilog_old": (False, False)}
    helps = {k: ap_more(k) for k in want2}
    # argparse 가 다른 옵션 설명을 접어 줄 머리(도움말 칸 들여쓰기)에 낱말이 오는 꼴 — 옛 판 도움말
    helps["wrapped_old"] = ("usage: koo_sphere_report [-h] [--yield-stress YIELD_STRESS]\n\noptions:\n"
                            "  -h, --help            show this help message and exit\n"
                            "  --yield-stress YIELD_STRESS\n                        항복응력 — 새 판은\n"
                            "                        --parallel-runs N 과\n                        --yield-map FILE 을 쓴다\n")
    want2["wrapped_old"] = (False, False)
    got_py = {k: (P._help_has_option(h, "--parallel-runs"), P._help_has_option(h, "--yield-map")) for k, h in helps.items()}
    check("argparse 도움말(리뷰 M 6종): Python 탐지가 기대대로", got_py == want2, str(got_py))
    sh_txt = P.build_sphere_report_sh("/data/x/output", sif_path="/x.sif", options={})
    fn = sh_txt[sh_txt.index("has_opt() {"):sh_txt.index("\n}\n", sh_txt.index("has_opt() {")) + 3]
    got_sh = {}
    for k, h in helps.items():
        hf = BASE / f"help_{k}.txt"
        hf.write_text(h)
        res = []
        for flag in ("--parallel-runs", "--yield-map"):
            r = subprocess.run(["bash", "-c", 'TOOL_HELP="$(cat "$1")"\n' + fn + 'has_opt "$2"', "x", str(hf), flag])
            res.append(r.returncode == 0)
        got_sh[k] = tuple(res)
    check("  셸 has_opt(생성된 sphere_report.sh 의 함수)도 같은 답", got_sh == got_py, f"sh={got_sh} py={got_py}")
    with _c.redirect_stdout(io.StringIO()):
        t1 = P.build_sphere_sbatch("/data/x/output", sif_path="/x.sif", options={}, environment={}, n_runs=979,
                                   tool_flags={"--parallel-runs"}, limits={})
    check("sbatch 가 어느 도구 판 기준인지 내보냄(SPHERE_SIZED_FOR=parallel), n_runs 없으면 없음",
          "export SPHERE_SIZED_FOR=parallel\n" in t1 and "SPHERE_SIZED_FOR" not in t0, t1[-300:])


FAKE_APPTAINER = """#!/bin/bash
# 시험용 apptainer 대역 — --help 면 FAKE_TOOL(new|old) 도움말, 아니면 받은 인자를 적고 'Loaded N results'
for a in "$@"; do
  if [ "$a" = "--help" ]; then
    echo "usage: koo_sphere_report [-h] (--test-dir TEST_DIR | --from-json JSON_FILE)"
    if [ "$FAKE_TOOL" = new ]; then echo "  --parallel-runs N"; echo "  --yield-map FILE"; fi
    if [ "$FAKE_TOOL" = newdefault ]; then echo "  --parallel-runs PARALLEL_RUNS"; echo "  --yield-map YIELD_MAP"; fi
    if [ "$FAKE_TOOL" = oldmention ]; then echo "  --yield-stress MPA   항복응력 (--parallel-runs·--yield-map 은 새 판에만)"; fi
    exit 0
  fi
done
printf '%s\\n' "$@" > "$FAKE_ARGS"
[ -n "$FAKE_SILENT" ] || echo "Loaded ${FAKE_LOADED:-1} results in 0.1s"
exit ${FAKE_RC:-0}
"""


def test_shell_wiring():
    print("[2] sphere_report.sh — 옵션 탐지·조용한 0건")
    from Runner import PostprocessShellGenerator as P
    fake = BASE / "fakebin"
    fake.mkdir()
    (fake / "apptainer").write_text(FAKE_APPTAINER)
    (fake / "apptainer").chmod(0o755)
    sif = BASE / "dummy.sif"
    sif.write_text("x")
    ymap = BASE / "ymap.json"
    ymap.write_text("{}")

    def make(n_runs, yield_map=None):
        td = Path(tempfile.mkdtemp(dir=BASE))
        out = td / "output"
        for i in range(n_runs):
            o = out / f"Run_{i + 1}" / "Output"
            (o / "report").mkdir(parents=True)
            (o / "mes0000").write_text(" N o r m a l    t e r m i n a t i o n\n")
            (o / "report" / "result.json").write_text("{}")
        opts = {"yield_map": str(yield_map)} if yield_map else {}
        sh = out / "sphere_report.sh"
        sh.write_text(P.build_sphere_report_sh(str(out), sif_path=str(sif), options=opts))
        return sh, td

    def run(sh, td, tool, loaded="1", rc="0", cpus="4", sized=None, silent=False):
        env = dict(os.environ, PATH=f"{fake}:{os.environ['PATH']}", FAKE_TOOL=tool, FAKE_LOADED=loaded, FAKE_RC=rc,
                   FAKE_ARGS=str(td / "args.txt"))
        for k in ("SLURM_CPUS_PER_TASK", "SPHERE_SIZED_FOR", "FAKE_SILENT"):
            env.pop(k, None)
        if sized:
            env["SPHERE_SIZED_FOR"] = sized
        if silent:
            env["FAKE_SILENT"] = "1"
        if cpus is not None:
            env["SLURM_CPUS_PER_TASK"] = cpus
        r = subprocess.run(["bash", str(sh)], capture_output=True, text=True, env=env, timeout=60)
        args = (td / "args.txt").read_text().split("\n") if (td / "args.txt").exists() else []
        return r.returncode, r.stdout + r.stderr, args

    def flag_after(args, flag):
        return args[args.index(flag) + 1] if flag in args else None

    sh, td = make(1)
    rc, log, args = run(sh, td, "new")
    check("새 도구: rc 0 · --parallel-runs $SLURM_CPUS_PER_TASK(4)", rc == 0 and flag_after(args, "--parallel-runs") == "4",
          f"rc={rc} {args} {log[-300:]}")
    rc, log, args = run(sh, td, "newdefault")
    check("새 도구(metavar 없이 'PARALLEL_RUNS'): --parallel-runs 4", rc == 0 and flag_after(args, "--parallel-runs") == "4",
          f"rc={rc} {args} {log[-300:]}")
    rc, log, args = run(sh, td, "new", cpus=None)
    check("Slurm 밖(수동 실행): --parallel-runs 1", flag_after(args, "--parallel-runs") == "1", str(args))
    rc, log, args = run(sh, td, "old")
    check("옛 도구: --parallel-runs 를 넘기지 않음(argparse 로 죽지 않게)", rc == 0 and "--parallel-runs" not in args, str(args))
    rc, log, args = run(sh, td, "old", loaded="0")
    check("Loaded 0 results → rc 3 + 오류", rc == 3 and "하나도 읽지 못했다" in log, f"rc={rc} {log[-300:]}")
    rc, log, args = run(sh, td, "new", rc="2")
    check("도구 rc 2 → 스크립트 rc 2(pipefail)", rc == 2, f"rc={rc}")
    sh2, td2 = make(2)
    rc, log, args = run(sh2, td2, "old", loaded="1")
    check("정상 2개 중 1개만 읽음 → rc 0 + 경고", rc == 0 and "중 1 개만" in log, f"rc={rc} {log[-300:]}")
    sh3, td3 = make(1, yield_map=ymap)
    rc, log, args = run(sh3, td3, "new")
    check("yield_map + 새 도구: --yield-map 경로", flag_after(args, "--yield-map") == str(ymap), str(args))
    rc, log, args = run(sh3, td3, "old")
    check("yield_map + 옛 도구: 넘기지 않고 경고", "--yield-map" not in args and "--yield-map 을 모른다" in log, f"{args} {log[-300:]}")
    rc, log, args = run(sh3, td3, "oldmention")
    check("옛 도구 도움말 설명 글에 --parallel-runs·--yield-map 이 나와도 넘기지 않음(옵션 정의 줄만)",
          rc == 0 and "--parallel-runs" not in args and "--yield-map" not in args, f"rc={rc} {args} {log[-300:]}")
    rc, log, args = run(sh, td, "old", sized="parallel")
    check("병렬 기준으로 잡힌 잡 + 노드 SIF 가 옛 판 → 🔴 경고(헤드·노드 SIF 엇갈림)", rc == 0 and "🔴" in log and "옛 판" in log,
          f"rc={rc} {log[-300:]}")
    rc, log, args = run(sh, td, "old", sized="sequential")
    check("  순차 기준이면 경고 없음", "🔴" not in log, log[-300:])
    rc, log, args = run(sh, td, "old", silent=True)
    check("'Loaded N results' 줄이 없으면 경고(rc 는 도구 rc)", rc == 0 and "줄이 없어" in log, f"rc={rc} {log[-300:]}")
    cwd = os.getcwd()
    os.chdir(BASE)
    try:
        rel_sh = P.build_sphere_report_sh(str(BASE / "output"), sif_path=str(sif), options={"yield_map": "rel_ymap.json"})
    finally:
        os.chdir(cwd)
    check("yield_map 상대 경로는 만드는 때의 폴더 기준 절대 경로로(잡은 --chdir=/data)",
          f"YIELD_MAP={BASE / 'rel_ymap.json'}" in rel_sh, [ln for ln in rel_sh.splitlines() if ln.startswith("YIELD_MAP=")])


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def yield_deck():
    nodes, elems, nid = [], [], 0
    for k in range(8):
        base = nid
        for (x, y, z) in [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]:
            nid += 1
            nodes.append(f"{nid:8d}{float(x + 3 * k):16.6f}{float(y):16.6f}{float(z):16.6f}")
        elems.append(f"{k + 1:8d}{k + 1:8d}" + "".join(f"{base + i:8d}" for i in range(1, 9)))
    z8 = f10(*([0.0] * 8))
    deck = "*KEYWORD\n*NODE\n" + "\n".join(nodes) + "\n"
    deck += "".join(f"*PART\npart{k + 1}\n" + f10(k + 1, 1, k + 1) for k in range(8))
    deck += "*SECTION_SOLID\n" + f10(1, 1)
    deck += "*MAT_PLASTIC_KINEMATIC\n" + f10(1, "7.85E-09", 210000, 0.3, 250.0, 1000.0, 0.0) + f10(0.0, 0.0, "1.0E20", 0.0)
    deck += ("*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE\ncurve_mat\n" + f10(2, "7.85E-09", 210000, 0.3, 999.0, 0.0, 0.0, 0.0)
             + f10(0.0, 0.0, 7, 0, 0.0) + z8 + z8)
    deck += ("*MAT_PIECEWISE_LINEAR_PLASTICITY\n" + f10(3, "7.85E-09", 210000, 0.3, 0.0, 0.0, 0.0, 0.0) + f10(0.0, 0.0, 0, 0, 0.0)
             + f10("0.0", "0.1", "0.2") + f10("300.0", "350.0", "380.0"))
    deck += "*MAT_ELASTIC\n" + f10(4, "7.85E-09", 210000, 0.3)
    deck += ("*MAT_PIECEWISE_LINEAR_PLASTICITY\n" + f10(5, "7.85E-09", 210000, 0.3, 120.0, 0.0, 0.0, 0.0)
             + f10(0.0, 0.0, 0, 0, 0.0) + z8 + z8)
    deck += ("*DEFINE_CURVE\n" + f10(7, 0, 1.0, 2.0, 0.0, 5.0)
             + f"{0.05:>20}{110.0:>20}\n{0.0:>20}{100.0:>20}\n{0.5:>20}{200.0:>20}\n")
    # 리뷰 L — 초기 항복은 εp=0 값: 6) SFA 2·OFFA -0.05 로 가로축이 옮겨진 커브, 7) 음의 변형률 점이 있는 커브,
    # 8) EPS1 이 0 이 아닌 점 입력(외삽). 예전 '가장 작은 변형률 점'·ES1 이면 100·90·255 가 나온다.
    for mid, lc in ((6, 8), (7, 9)):
        deck += (f"*MAT_PIECEWISE_LINEAR_PLASTICITY\n" + f10(mid, "7.85E-09", 210000, 0.3, 999.0, 0.0, 0.0, 0.0)
                 + f10(0.0, 0.0, lc, 0, 0.0) + z8 + z8)
    deck += ("*MAT_PIECEWISE_LINEAR_PLASTICITY\n" + f10(8, "7.85E-09", 210000, 0.3, 0.0, 0.0, 0.0, 0.0) + f10(0.0, 0.0, 0, 0, 0.0)
             + f10("0.002", "0.1") + f10("255.0", "300.0"))
    deck += ("*DEFINE_CURVE\n" + f10(8, 0, 2.0, 1.0, -0.05, 0.0)
             + f"{0.0:>20}{100.0:>20}\n{0.1:>20}{110.0:>20}\n{0.5:>20}{150.0:>20}\n")
    deck += ("*DEFINE_CURVE\n" + f10(9, 0, 1.0, 1.0, 0.0, 0.0)
             + f"{-0.1:>20}{90.0:>20}\n{0.0:>20}{100.0:>20}\n{0.2:>20}{150.0:>20}\n")
    return deck + "*ELEMENT_SOLID\n" + "\n".join(elems) + "\n*END\n"


DROP_OPT = """*Inputfile
model.k
*RunDirectoryMode,True,runs
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,0
EulerPitching,0
EulerYawing,0
Height,50
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
InitialAngularVelocityX,0
InitialAngularVelocityY,0
InitialAngularVelocityZ,0
OffsetDistance,1
Density,7.85e-9
YoungsModulus,210000
PoissonRatio,0.3
tFinal,0.001
dt,0.0001
**EndDropAttitude
*End
"""


def test_part_yield():
    print("[3] KMM DROP_ATTITUDE → DropSet.json model.part_yield")
    d = Path(tempfile.mkdtemp(dir=BASE))
    (d / "model.k").write_text(yield_deck())
    (d / "opt.txt").write_text(DROP_OPT)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
    js = sorted(d.glob("runs/Run_*/DropSet.json"))
    check("rc 0 · DropSet.json", r.returncode == 0 and js, (r.stdout + r.stderr)[-500:])
    if not js:
        return
    model = json.loads(js[0].read_text())["model"]
    py = model.get("part_yield") or {}
    parts = py.get("parts") or {}
    got = {k: (v.get("yield"), v.get("source")) for k, v in parts.items()}
    check("단위 힌트 MPa(ton-mm-s 밀도)", py.get("unit") == "MPa", str(py.get("unit")))
    check("MAT_003 SIGY 250", got.get("1") == (250.0, "MAT_003 SIGY"), str(got.get("1")))
    check("MAT_024 LCSS: SIGY 999 무시, 2.0×(100+5)=210", got.get("2", (None,))[0] == 210.0 and "LCSS 7" in got.get("2", ("", ""))[1],
          str(got.get("2")))
    check("MAT_024 점 입력(제목 없음): εp=0 값 300", got.get("3") == (300.0, "MAT_024 EPS·ES εp=0"), str(got.get("3")))
    check("MAT_ELASTIC 은 맵에 없음", "4" not in parts, str(parts.keys()))
    check("MAT_024 SIGY 120", got.get("5") == (120.0, "MAT_024 SIGY"), str(got.get("5")))
    y6, y7, y8 = (got.get(k, (None, ""))[0] for k in ("6", "7", "8"))
    check("MAT_024 LCSS SFA 2·OFFA -0.05: 가로축 (-0.1,0.1) 사이 보간 105", y6 is not None and abs(y6 - 105.0) < 1e-9, str(got.get("6")))
    check("MAT_024 LCSS 음의 변형률 점 (-0.1,90)(0,100): εp=0 값 100", y7 is not None and abs(y7 - 100.0) < 1e-9, str(got.get("7")))
    check("MAT_024 EPS1 0.002 (255,300): 외삽 254.08", y8 is not None and abs(y8 - (255.0 - 0.002 * 45.0 / 0.098)) < 1e-9,
          str(got.get("8")))
    check("KMM 이 더한 바닥판(9)은 맵에 없음", "9" not in parts, str(parts.keys()))
    check("model.parts 는 예전 형식(pid → 이름 글)", isinstance(model.get("parts"), dict)
          and all(isinstance(v, str) for v in model["parts"].values()), str(model.get("parts")))


if __name__ == "__main__":
    print(f"KMM={' '.join(KMM_CMD)}  BASE={BASE}")
    if not os.environ.get("KMM_BIN"):
        test_sizing()
        test_shell_wiring()
    test_part_yield()
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:600])
        sys.exit(1)
    print("ALL PASS")
