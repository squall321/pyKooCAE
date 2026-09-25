# 20방향 deep_report 산출물이 실제로 온전한지 변형별로 검증하는 스크립트
import json
import os
import sys
from pathlib import Path

BASE = Path(os.environ.get("TEST_DIR", "/data/koopark/Test_Postprocess_v14")) / "output"
VARIANTS = {"light": "report_norender", "full": "report"}

REQUIRED = [
    "report.html",
    "result.json",
    "analysis_result.json",
    "contact_metrics.json",
    "energy_flow_edges.csv",
]


def check(rd: Path, variant: str):
    problems = []
    for name in REQUIRED:
        f = rd / name
        if not f.exists():
            problems.append(f"없음 {name}")
        elif f.stat().st_size == 0:
            problems.append(f"0바이트 {name}")

    rj = rd / "result.json"
    if rj.exists() and rj.stat().st_size > 0:
        try:
            d = json.loads(rj.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"result.json 파싱실패 {exc}")
        else:
            if not isinstance(d, dict) or not d:
                problems.append("result.json 내용 비정상")

    html = rd / "report.html"
    if html.exists() and html.stat().st_size < 100_000:
        problems.append(f"report.html 너무 작음 {html.stat().st_size}B")

    renders = rd / "renders"
    n_mp4 = len(list(renders.rglob("*.mp4"))) if renders.exists() else 0
    if variant == "full" and n_mp4 == 0:
        problems.append("full 인데 단면뷰 mp4 0개")
    if variant == "light" and n_mp4 > 0:
        problems.append(f"light 인데 mp4 {n_mp4}개 (렌더가 돌았다)")

    return problems, n_mp4


def main():
    want = sys.argv[1:] or list(VARIANTS)
    rc = 0
    for variant in want:
        outname = VARIANTS[variant]
        runs = sorted(BASE.glob("Run_*"))
        print(f"\n=== {variant} ({outname}) — 방향 {len(runs)}개")
        ok = 0
        for run in runs:
            rd = run / "Output" / outname
            if not rd.exists():
                print(f"  [미생성] {run.name}")
                rc = 1
                continue
            problems, n_mp4 = check(rd, variant)
            done = (rd / ".koo_driver_done").exists()
            if problems or not done:
                mark = "🔴"
                rc = 1
            else:
                mark = "✓"
                ok += 1
            extra = f"mp4={n_mp4}" if variant == "full" else ""
            print(f"  {mark} {run.name} {extra} {'; '.join(problems) if problems else ''}"
                  f"{'' if done else ' (완료표식 없음)'}")
        print(f"  → 정상 {ok}/{len(runs)}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
