# 낙하·부분충격 리포트 자동 귀환(요청서 REQUEST-drop-impact-result-return.md A~E) 회귀 시험
"""
실행: venv312/bin/python tests/test_result_return.py            (가짜 apptainer 로 셸 배선만 본다, 수 초)
수정 전 코드로 볼 때: KCR_ROOT=<옛 트리(git archive <rev> Runner KooChainRun)> venv312/bin/python tests/test_result_return.py

배경 (2026-10-28, docs/result_return_20261028/)
  [1] A·E — 부분충격(DWI) prepare 가 impact_report.sh 를 안 만들어 의존 잡·postprocess 가 부를 파일이 없었다.
      postprocess·의존 잡은 project.output_dir → <config>/output 만 봐서 DWI 의 최상위 output_dir(기본 dwi_output)을
      못 찾았고, koo_impact_report 로더는 <test_dir>/output 고정이라 이름이 output 이 아니면 런 0개였다.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KCR_ROOT = Path(os.environ.get("KCR_ROOT", ROOT)).resolve()
sys.path.insert(0, str(KCR_ROOT))
PY = str(ROOT / "venv312" / "bin" / "python")
KCR = [PY, str(KCR_ROOT / "KooChainRun")]
BASE = Path(tempfile.mkdtemp(prefix="result_return_"))
FAILS = []

# 가짜 apptainer — SIF 없이 생성 셸이 넘기는 인자·바인드·test_dir 를 기록하고, 로더처럼 test_dir/output 아래 런을 센다
FAKE_APPTAINER = r"""#!/bin/bash
LOG="${FAKE_LOG:-/dev/null}"
args=("$@")
mod=""; td=""; html=""; js=""; bind=""
for ((i=0; i<${#args[@]}; i++)); do
    case "${args[$i]}" in
        -m) mod="${args[$((i+1))]}" ;;
        --test-dir) td="${args[$((i+1))]}" ;;
        --output|-o) html="${args[$((i+1))]}" ;;
        --json) js="${args[$((i+1))]}" ;;
        --bind) bind="${args[$((i+1))]}" ;;
    esac
done
if printf '%s\n' "${args[@]}" | grep -qx -- '-c'; then
    exit "${FAKE_IMPORT_RC:-0}"          # python3 -c "import koo_impact_report"
fi
case "$mod" in
    koo_impact_report)
        n=0
        for r in "$td"/output/Run_* "$td"/output/results/dwi_*/Run_*; do
            [ -e "$r/Output/d3plot" ] && n=$((n + 1))
        done
        echo "impact test_dir=$td bind=$bind runs=$n" >> "$LOG"
        [ "$n" -gt 0 ] || { echo "No usable runs found under $td/output" >&2; exit 1; }
        echo "<html></html>" > "$html"; echo "{}" > "$js"; exit 0 ;;
esac
echo "unhandled: $*" >> "$LOG"; exit 0
"""


def check(name, cond, detail=""):
    print("  %-72s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def run(cmd, env=None, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=env, cwd=cwd)


def fake_env(tag):
    """가짜 apptainer 를 PATH 앞에, 가짜 SIF 파일·기록 파일."""
    shim = BASE / f"shim_{tag}"
    shim.mkdir(exist_ok=True)
    (shim / "apptainer").write_text(FAKE_APPTAINER, encoding="utf-8")
    (shim / "apptainer").chmod(0o755)
    sif = shim / "fake.sif"
    sif.write_bytes(b"")
    log = shim / "calls.log"
    log.write_text("", encoding="utf-8")
    env = dict(os.environ, PATH=f"{shim}:{os.environ.get('PATH', '')}", FAKE_LOG=str(log))
    return env, sif, log


def dwi_scenario(d, sif, output_dir="dwi_output", postprocess=True):
    """작은 DWI 시나리오 — 모델은 노드 세 개짜리(bbox 만 읽힌다), 위치는 list 2개."""
    d.mkdir(parents=True, exist_ok=True)
    (d / "tiny.k").write_text("*KEYWORD\n*NODE\n       1       0.0       0.0       0.0\n"
                              "       2     100.0      50.0       0.0\n       3      50.0      25.0       1.0\n*END\n",
                              encoding="utf-8")
    s = {"project_name": "RR_DWI", "mode": "drop_weight_impact", "model_file": "tiny.k", "output_dir": output_dir,
         "simulation_params": {"impactor": {"type": "Sphere", "radius": 5.0, "height": 100},
                               "locations": {"mode": "list", "points": [[10, 10], [20, 10]]}},
         "environment": {"ncpu": 2, "memory": "2G", "partition": "normal"}}
    if postprocess:
        s["postprocess"] = {"enabled": True, "sif_path": str(sif)}
    (d / "scenario.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    return d / "scenario.json"


def fake_dwi_results(out_dir, n=2):
    """KooChainRun DWI 레이아웃 output_dir/results/dwi_<NNNN>/Run_*/Output/d3plot."""
    for i in range(1, n + 1):
        r = out_dir / "results" / f"dwi_{i:04d}" / f"Run_20261028_00000{i}_ab"
        (r / "Output").mkdir(parents=True, exist_ok=True)
        (r / "Output" / "d3plot").write_bytes(b"")
        (r / "DropWeightImpactTestSet.json").write_text(
            json.dumps({"stage": f"Case{i:04d}", "description": f"DWI Case{i}/{n} x={i}.0 y=0.0"}), encoding="utf-8")


def test_dwi_impact_report():
    print("[1] A·E — DWI prepare 의 impact_report.sh · 출력 폴더 · .impact_root")
    env, sif, log = fake_env("a")
    d = BASE / "dwi_a"
    sc = dwi_scenario(d, sif)
    p = run(KCR + ["prepare", str(sc)], env=env, cwd=str(d))
    check("prepare rc 0", p.returncode == 0, p.stdout[-400:] + p.stderr[-400:])
    out = d / "dwi_output"
    sh = out / "impact_report.sh"
    check("A: dwi_output/impact_report.sh 생성", sh.exists())

    d2 = BASE / "dwi_a_nopp"
    p = run(KCR + ["prepare", str(dwi_scenario(d2, sif, postprocess=False))], env=env, cwd=str(d2))
    check("postprocess 블록 없으면 impact_report.sh 안 만듦(Designer 와 같은 계약)",
          p.returncode == 0 and not (d2 / "dwi_output" / "impact_report.sh").exists())

    fake_dwi_results(out)
    p = run(KCR + ["postprocess", str(d / "runner_config.json"), "--impact"], env=env, cwd=str(d))
    calls = log.read_text(encoding="utf-8")
    check("E: postprocess 가 최상위 output_dir(dwi_output)을 본다", f"output_dir: {out.resolve()}" in p.stdout,
          p.stdout[-600:])
    check("A: impact_report.sh 가 .impact_root 를 test_dir 로 — 런 2개", "runs=2" in calls, calls)
    check("바인드는 output_dir(링크 대상까지 보이게)", f"bind=/data:/data,{out.resolve()}:{out.resolve()}" in calls, calls)
    check("impact_report.html·json 생성", (out / "impact_report.html").exists() and (out / "impact_report.json").exists())
    root = out / ".impact_root"
    check(".impact_root/output/results 는 링크(output_dir 자체를 링크하지 않음 — 고리 없음)",
          (root / "output" / "results").is_symlink() and not (root / "output").is_symlink())
    check(".impact_root/scenario.json → 시나리오(project_name)",
          (root / "scenario.json").is_symlink() and (root / "scenario.json").resolve() == sc.resolve())

    # 이름이 output 이면 예전 그대로 — test_dir 는 부모, .impact_root 없음
    from Runner.PostprocessShellGenerator import build_impact_report_sh
    txt = build_impact_report_sh("/data/x/output", str(sif), {})
    check("output_dir 이름이 output 이면 TEST_DIR=부모, .impact_root 없음",
          'TEST_DIR="$(dirname "$OUTPUT_DIR")"' in txt and ".impact_root" not in txt)

    # 출력 폴더 해석 — chain 은 project.output_dir 그대로
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("kcr_main", str(KCR_ROOT / "KooChainRun"))
    spec = importlib.util.spec_from_loader("kcr_main", loader)
    kcr = importlib.util.module_from_spec(spec)
    loader.exec_module(kcr)
    f = getattr(kcr, "_report_output_dir", None)
    check("출력 폴더 헬퍼 _report_output_dir 있음", f is not None)
    if f:
        cfg = d / "runner_config.json"
        check("chain: project.output_dir 우선", f({"project": {"output_dir": "/data/c/out"}, "output_dir": "/x"}, cfg)
              == "/data/c/out")
        check("DWI: 최상위 output_dir", f({"mode": "drop_weight_impact", "output_dir": "/data/d/dwi"}, cfg) == "/data/d/dwi")
        check("둘 다 없으면 <base_dir>/output", f({"base_dir": "/data/b"}, cfg) == "/data/b/output")


if __name__ == "__main__":
    print(f"코드: {KCR_ROOT}  작업: {BASE}")
    test_dwi_impact_report()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:300])
        sys.exit(1)
    print("ALL PASS")
