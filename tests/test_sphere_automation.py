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
  [3] KMM 이 DropSet.json 에 model.part_yield 를 쓴다(R16: MAT_024 SIGY 는 LCSS>0 이면 무시 — 커브 첫 점 × SFO + OFFO).
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
        'case "$3" in "") echo "$n"; echo "$v";; normal) echo "$n";; viz) echo "$v";; esac\n')
    (fb / "sinfo").write_text('#!/bin/bash\ncase " $* " in *viz*) echo "3584+";; *normal*) echo "64000";; esac\n')
    for f in ("scontrol", "sinfo"):
        (fb / f).chmod(0o755)
    old_path = os.environ["PATH"]
    os.environ["PATH"] = f"{fb}:{old_path}"
    try:
        lim_default, lim_viz = P.partition_limits(""), P.partition_limits("viz")
    finally:
        os.environ["PATH"] = old_path
    check("파티션 없음 → 기본 파티션(normal) 한도 2일·62.5G", lim_default == {"max_minutes": 2880, "max_mem_gb": 62.5}, str(lim_default))
    check("파티션 viz → 60일·3.5G(3584+)", lim_viz == {"max_minutes": 86400, "max_mem_gb": 3.5}, str(lim_viz))


FAKE_APPTAINER = """#!/bin/bash
# 시험용 apptainer 대역 — --help 면 FAKE_TOOL(new|old) 도움말, 아니면 받은 인자를 적고 'Loaded N results'
for a in "$@"; do
  if [ "$a" = "--help" ]; then
    echo "usage: koo_sphere_report [-h] (--test-dir TEST_DIR | --from-json JSON_FILE)"
    if [ "$FAKE_TOOL" = new ]; then echo "  --parallel-runs N"; echo "  --yield-map FILE"; fi
    exit 0
  fi
done
printf '%s\\n' "$@" > "$FAKE_ARGS"
echo "Loaded ${FAKE_LOADED:-1} results in 0.1s"
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

    def run(sh, td, tool, loaded="1", rc="0", cpus="4"):
        env = dict(os.environ, PATH=f"{fake}:{os.environ['PATH']}", FAKE_TOOL=tool, FAKE_LOADED=loaded, FAKE_RC=rc,
                   FAKE_ARGS=str(td / "args.txt"))
        env.pop("SLURM_CPUS_PER_TASK", None)
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


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def yield_deck():
    nodes, elems, nid = [], [], 0
    for k in range(5):
        base = nid
        for (x, y, z) in [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]:
            nid += 1
            nodes.append(f"{nid:8d}{float(x + 3 * k):16.6f}{float(y):16.6f}{float(z):16.6f}")
        elems.append(f"{k + 1:8d}{k + 1:8d}" + "".join(f"{base + i:8d}" for i in range(1, 9)))
    z8 = f10(*([0.0] * 8))
    deck = "*KEYWORD\n*NODE\n" + "\n".join(nodes) + "\n"
    deck += "".join(f"*PART\npart{k + 1}\n" + f10(k + 1, 1, k + 1) for k in range(5))
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
    check("MAT_024 점 입력(제목 없음): ES1 300", got.get("3") == (300.0, "MAT_024 ES1"), str(got.get("3")))
    check("MAT_ELASTIC 은 맵에 없음", "4" not in parts, str(parts.keys()))
    check("MAT_024 SIGY 120", got.get("5") == (120.0, "MAT_024 SIGY"), str(got.get("5")))
    check("KMM 이 더한 바닥판(6)은 맵에 없음", "6" not in parts, str(parts.keys()))
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
