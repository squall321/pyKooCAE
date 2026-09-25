# 20방향의 light/full 두 변형 result.json 을 전수 비교해 후처리 재현성 편차를 정량화하는 스크립트
import json
import os
import sys
from pathlib import Path

BASE = Path(os.environ.get("TEST_DIR", "/data/koopark/Test_Postprocess_v14")) / "output"
FIELDS = ("peak_stress", "peak_strain", "time_of_peak_stress",
          "peak_disp_mag", "peak_acc_mag", "strain_ratio")


def load(run: Path, outname: str):
    p = run / "Output" / outname / "result.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def rel(a, b):
    if a is None or b is None:
        return None
    try:
        a = float(a); b = float(b)
    except (TypeError, ValueError):
        return None
    if a == b:
        return 0.0
    denom = max(abs(a), abs(b))
    return abs(a - b) / denom if denom else 0.0


def main():
    runs = sorted(BASE.glob("Run_*"))
    field_hits = {f: [] for f in FIELDS}
    md5_same = {"contact_metrics.json": 0, "energy_flow_edges.csv": 0}
    n_pairs = 0
    rows = []

    for run in runs:
        full = load(run, "report")
        light = load(run, "report_norender")
        if not full or not light:
            rows.append((run.name, "비교불가", 0, []))
            continue
        # 신버전 산출물에만 있는 파일. 없으면 report/ 가 구버전이라 변형 비교가 성립하지 않는다.
        if not (run / "Output" / "report" / "contact_metrics.json").exists():
            rows.append((run.name, "구판", 0, []))
            continue
        n_pairs += 1

        for name in md5_same:
            a = run / "Output" / "report" / name
            b = run / "Output" / "report_norender" / name
            if a.exists() and b.exists() and a.read_bytes() == b.read_bytes():
                md5_same[name] += 1

        diffs = []
        pf, pl = full.get("parts", {}), light.get("parts", {})
        for pid in sorted(set(pf) | set(pl), key=lambda x: (len(x), x)):
            if pid not in pf or pid not in pl:
                diffs.append((pid, "한쪽에만 존재", None))
                continue
            for f in FIELDS:
                r = rel(pf[pid].get(f), pl[pid].get(f))
                if r is not None and r > 1e-12:
                    diffs.append((pid, f, r))
                    field_hits[f].append((run.name, pid, r))
        rows.append((run.name, "비교", len({d[0] for d in diffs}), diffs))

    print(f"=== 두 변형 result.json 전수 비교 — 비교 가능 {n_pairs}/{len(runs)} 방향\n")
    for name, kind, nparts, diffs in rows:
        if kind == "비교불가":
            print(f"  [비교불가] {name}  (한쪽 result.json 없음)")
            continue
        if kind == "구판":
            print(f"  [제외] {name}  report/ 가 구버전 (contact_metrics.json 없음) "
                  f"— full 변형 재생성 전")
            continue
        if not diffs:
            print(f"  ✓ {name}  차이 없음")
        else:
            worst = max(diffs, key=lambda d: d[2] or 0)
            print(f"  🔴 {name}  차이 파트 {nparts}개, 최대 {worst[2]*100:.2f}% "
                  f"(PID {worst[0]} {worst[1]})")

    print("\n=== 바이트 동일 확인")
    for name, cnt in md5_same.items():
        print(f"  {name}: {cnt}/{n_pairs} 방향 동일")

    print("\n=== 항목별 불일치 분포")
    for f in FIELDS:
        hits = field_hits[f]
        if not hits:
            print(f"  {f:22s} 불일치 0")
        else:
            mx = max(hits, key=lambda h: h[2])
            print(f"  {f:22s} 불일치 {len(hits)}건, 최대 {mx[2]*100:.2f}% "
                  f"({mx[0]} PID {mx[1]})")

    total = sum(len(v) for v in field_hits.values())
    print(f"\n총 불일치 {total}건 / 비교 {n_pairs}방향 x 파트 x 항목 {len(FIELDS)}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
