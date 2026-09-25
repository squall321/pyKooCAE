# 실측 progress TSV 두 개를 읽어 예제 패키지의 RESOURCES.md 를 생성하는 스크립트
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(os.environ.get("TEST_DIR", "/data/koopark/Test_Postprocess_v14"))
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "RESOURCES.md"


def parse_elapsed(s: str) -> float:
    """/usr/bin/time -v 의 h:mm:ss 또는 m:ss.xx 를 초로."""
    parts = s.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
    except ValueError:
        pass
    return float("nan")


def fmt(sec: float) -> str:
    if sec != sec:
        return "?"
    m, s = divmod(int(round(sec)), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def load(variant: str):
    p = ROOT / f"progress_deep_{variant}.tsv"
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines()[1:]:
        c = line.split("\t")
        if len(c) < 5:
            continue
        rows.append({
            "run": c[0], "rc": c[1], "elapsed": parse_elapsed(c[2]),
            "rss": int(c[3]) if c[3].isdigit() else 0, "size": c[4],
            "sv": c[6] if len(c) > 6 else "4",
        })
    return rows


def block(variant: str, label: str, rows):
    if not rows:
        return f"### {label}\n\n실측 없음.\n"
    ok = [r for r in rows if r["rc"] == "0"]
    el = [r["elapsed"] for r in ok if r["elapsed"] == r["elapsed"]]
    rss = [r["rss"] for r in ok if r["rss"]]
    svs = sorted({r["sv"] for r in ok})
    lines = [
        f"### {label}",
        "",
        f"- 성공 {len(ok)}/{len(rows)} 방향",
        f"- 1방향 경과: 최소 {fmt(min(el))} / 중앙 {fmt(statistics.median(el))} / 최대 {fmt(max(el))}",
        f"- 20방향 합계(실측 합): {fmt(sum(el))}",
        f"- 최대 RSS: {max(rss) / 1048576:.1f} GiB (최소 {min(rss) / 1048576:.1f} GiB)",
        f"- 방향당 산출: {ok[0]['size']} 내외",
        f"- `--sv-threads`: {', '.join(svs)}",
        "",
        "| 방향 | rc | 경과 | 최대 RSS (GiB) | 산출 | sv |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['run']} | {r['rc']} | {fmt(r['elapsed'])} | "
            f"{r['rss'] / 1048576:.1f} | {r['size']} | {r['sv']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    light = load("light")
    full = load("full")
    doc = [
        "# 실측 자원량",
        "",
        "AMD Ryzen 9 9950X (16코어 32스레드), 123 GB RAM 헤드노드. 후처리는 **순차 1건씩**.",
        "해석 자체는 2026-05-22 에 node001 에서 완주한 것이고, 아래는 **후처리 재생성** 실측이다.",
        "",
        "## 요약",
        "",
        "| 단계 | 1방향 | 20방향 | 최대 RSS | 산출 |",
        "|---|---|---|---|---|",
    ]

    def summary_row(label, rows, size_hint):
        ok = [r for r in rows if r["rc"] == "0"]
        if not ok:
            return f"| {label} | ? | ? | ? | ? |"
        el = [r["elapsed"] for r in ok if r["elapsed"] == r["elapsed"]]
        rss = max(r["rss"] for r in ok)
        per = statistics.median(el)
        return (f"| {label} | {fmt(per)} | {fmt(per * 20)} | "
                f"{rss / 1048576:.1f} GiB | {size_hint} |")

    doc.append(summary_row("deep_report light (`--no-render`)", light, "171 MB/방향"))
    doc.append(summary_row("deep_report full (렌더+단면뷰)", full, "388 MB/방향"))
    doc += [
        "",
        "d3plot 원본은 방향당 약 19 GB, 20방향 363 GB — 후처리 입력으로 반드시 남아 있어야 한다.",
        "",
        "## 어디에 시간이 쓰이는가",
        "",
        "`report/` 파일 mtime 으로 되짚은 full 1방향(초기 `--sv-threads 4`) 분해.",
        "",
        "| 단계 | 시간 |",
        "|---|---|",
        "| d3plot 분석 (`unified_analyzer`) | 약 6분 |",
        "| 단면뷰 영상 25개 (전체 1 + 파트별 24) | 약 53분 |",
        "",
        "🔴 이 설정에서는 정규 LSPrePost 렌더가 생성되지 않는다(`renders/` 아래가 전부 `section_view_*`).",
        "그래서 `--render-threads` 는 무의미하고 시간 지배 knob 은 `--sv-threads` 다.",
        "",
        "🔴 최대 RSS 는 light 와 full 이 사실상 같다 = 약 33 GiB 는 **분석 단계** 값이다.",
        "`--no-render` 로 메모리를 줄일 수는 없다. 두 변형 모두 4 GB 계산노드에서는 불가능하다.",
        "",
        "## 방향별 실측",
        "",
        block("light", "light (`--no-render --ua-threads 4`)", light),
        block("full", "full (`--section-view` + `--ua-threads 4`)", full),
    ]
    OUT.write_text("\n".join(doc) + "\n", encoding="utf-8")
    print(f"작성: {OUT}")


if __name__ == "__main__":
    main()
