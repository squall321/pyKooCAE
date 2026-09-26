# 동봉한 result.json 짝으로 "ulimit -v 40 GB 가 피크를 낮게 만든다" 주장을 재검증하는 스크립트
# 클러스터·d3plot 없이 이 디렉터리만으로 돌아간다.  python3 verify_ulimit_finding.py
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (방향, 파트ID, 항목) — 40 GB 패스에서 어긋난 5건
CASES = [
    ("100552_e154f5", "21", "peak_strain"),
    ("115255_42bbae", "20", "peak_strain"),
    ("121046_372128", "6", "peak_strain"),
    ("123610_43521c", "2", "peak_acc_mag"),
    ("132307_0d0978", "17", "peak_acc_mag"),
]

# 같은 방향·같은 옵션을 ulimit 만 바꿔 5회 돌린 통제 실험 (0d0978 PID 17 peak_acc_mag)
CONTROL = [
    ("40 GB  원 light 패스", "132307_0d0978_light_vmem40_result.json"),
    ("40 GB  통제 재실행  ", "0d0978_light_vmem40_rerun_result.json"),
    ("60 GB  재실행 1     ", "0d0978_light_vmem60_rerun1_result.json"),
    ("60 GB  재실행 2     ", "0d0978_light_vmem60_rerun2_result.json"),
]


def load(name):
    p = HERE / name
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def get(doc, pid, field):
    try:
        return doc["parts"][pid][field]
    except (KeyError, TypeError):
        return None


def main():
    fails = []

    print("=== 통제 실험 — 0d0978 PID 17 peak_acc_mag (ulimit 만 다르다)")
    vals = {}
    for label, fname in CONTROL:
        doc = load(fname)
        if doc is None:
            print(f"  [파일 없음] {fname}")
            fails.append(fname)
            continue
        v = get(doc, "17", "peak_acc_mag")
        vals[label] = v
        print(f"  {label}  {v}")

    v40 = {k: v for k, v in vals.items() if k.startswith("40")}
    v60 = {k: v for k, v in vals.items() if k.startswith("60")}
    if len(set(v40.values())) == 1 and len(set(v60.values())) == 1 and v40 and v60:
        a, b = next(iter(v40.values())), next(iter(v60.values()))
        print(f"\n  → 40 GB 2회 모두 {a}")
        print(f"  → 60 GB 2회 모두 {b}")
        print(f"  → 40 GB 쪽이 {(b - a) / b * 100:.2f}% 낮다"
              if b else "  → 비교 불가")
        if not a < b:
            fails.append("통제 실험: 40 GB 가 더 낮지 않다")
    else:
        fails.append("통제 실험: 같은 ulimit 안에서 값이 갈린다")

    print("\n=== 영향 받은 5방향 — 40 GB 대비 60 GB (전부 상향이어야 한다)")
    up = 0
    for run, pid, field in CASES:
        d40 = load(f"{run}_light_vmem40_result.json")
        # 0d0978 은 60 GB 짝 파일명이 다르다
        d60 = load(f"{run}_light_vmem60_result.json") or load(
            "0d0978_light_vmem60_rerun1_result.json" if run.endswith("0d0978") else "")
        if d40 is None or d60 is None:
            print(f"  [짝 없음] {run}")
            fails.append(run)
            continue
        a, b = get(d40, pid, field), get(d60, pid, field)
        if a is None or b is None:
            print(f"  [값 없음] {run} PID {pid} {field}")
            fails.append(run)
            continue
        delta = (b - a) / max(abs(a), abs(b)) * 100
        mark = "상향" if b > a else "🔴 하향"
        up += 1 if b > a else 0
        print(f"  {run} PID {pid:>2} {field:13s} 40GB={a:<16.8g} 60GB={b:<16.8g} {delta:+.2f}% {mark}")

    print(f"\n  → 상향 {up}/{len(CASES)} 건")
    if up != len(CASES):
        fails.append(f"상향이 {up}/{len(CASES)} 뿐이다")

    print()
    if fails:
        print(f"🔴 검증 실패 {len(fails)}건: {fails}")
        return 1
    print("✅ 주장 재확인 — 40 GB 한도가 피크를 낮게 만든다 (안전계수 과대평가 방향)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
