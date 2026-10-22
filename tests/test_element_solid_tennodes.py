# *ELEMENT_SOLID (ten nodes format) 2-카드 파서 회귀 시험 — 절삭(64자) 절점줄·줄 넘김·선언 유무·옛 함수 차분
"""
실행: venv312/bin/python tests/test_element_solid_tennodes.py

배경: docs/fix_tennodes_truncated/PLAN.md
  LS-DYNA R16 Vol I — Card 2(N1~N10) 는 카드 한 장(한 줄), 빈 칸은 기본값(0).
  그래서 n9·n10 을 생략한 64자 줄은 적법하다. 옛 상태머신은 노드 10개를 채울 때까지
  다음 줄을 흡수해, 다음 요소의 헤더를 n9·n10 으로 먹고 그 요소의 노드줄을 버렸다.

검사
  [1] 매트릭스 — 폭(I8·I10·자유간격) × 배치(한 줄·절삭·8+2·4+4+2·2개씩·1개씩) × 부가(빈 줄·주석·CRLF)
  [2] 차분 — 고치기 직전 판(BASE)의 함수와 결과가 다른 경우가 "옛 함수가 줄을 버린 경우"뿐인지
"""
import ast
import contextlib
import io
import re
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
sys.path.insert(0, str(GEN))
from KooCAEManager.KooDynaKeyword import ElementSolid  # noqa: E402

BASE = "08be342"   # 고치기 직전 KooDynaKeyword.py 판 — 차분 기준
REL = "occProject/Generators/KooCAEManager/KooDynaKeyword.py"
FAILS = []


def check(name, cond, detail=""):
    print("  %-78s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


# ── 덱 블록 만들기 ────────────────────────────────────────────────────────────

def hexa(b):          # 8절점 육면체 — 10필드 카드에선 n9=n10=0
    return [b + k for k in range(1, 9)] + [0, 0]


def tet10(b):         # 10절점 사면체 — n9·n10 이 실제 절점
    return [b + k for k in range(1, 11)]


def tet4(b):          # 4절점 사면체 — 매뉴얼 표기 N1,N2,N3,N4,N4,N4,N4,N4,0,0
    return [b + 1, b + 2, b + 3, b + 4, b + 4, b + 4, b + 4, b + 4, 0, 0]


def fmt(vals, w):
    if w == "free":
        return " ".join(str(v) for v in vals)
    return "".join(f"{v:{w}d}" for v in vals)


def node_lines(n10, mode, w):
    if mode == "line10":
        return [fmt(n10, w)]
    if mode == "trunc8":                      # n9·n10 생략 — 그 둘은 0 이어야 한다
        assert n10[8:] == [0, 0], "절삭은 n9=n10=0 인 요소만 표현할 수 있다"
        return [fmt(n10[:8], w)]
    if mode == "w82":
        return [fmt(n10[:8], w), fmt(n10[8:], w)]
    if mode == "w442":
        return [fmt(n10[:4], w), fmt(n10[4:8], w), fmt(n10[8:], w)]
    if mode == "w2":
        return [fmt(n10[k:k + 2], w) for k in range(0, 10, 2)]
    if mode == "w1":
        return [fmt([v], w) for v in n10]
    raise ValueError(mode)


def build(elems, w, extra=None):
    """elems = [(eid, pid, n10, mode)] → 블록 줄 목록(리더가 넘기는 것과 같은 원문 줄)."""
    lines = []
    for eid, pid, n10, mode in elems:
        lines.append(fmt([eid, pid], w))
        if extra == "blank":
            lines.append("")
        if extra == "comment":
            lines.append("$ 주석 줄")
        lines.extend(node_lines(n10, mode, w))
    end = "\r\n" if extra == "crlf" else "\n"
    return [ln + end for ln in lines]


def expected(elems):
    return [(eid, pid, list(n10)) for eid, pid, n10, _ in elems]


def normalize(params):
    out = []
    for h, nodes in zip(params[0::2], params[1::2]):
        out.append((int(h[0]), int(h[1]), [int(x) for x in nodes]))
    return out


def run(fn, block, expect):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        params, _ = fn(block, expect)
    return normalize(params), buf.getvalue()


# ── 고치기 직전 판 함수(차분 기준) ─────────────────────────────────────────────

def load_base_fn():
    try:
        src = subprocess.run(["git", "-C", str(ROOT), "show", f"{BASE}:{REL}"], capture_output=True,
                             text=True, check=True).stdout
    except Exception:
        return None
    tree = ast.parse(src)
    for cls in tree.body:
        if isinstance(cls, ast.ClassDef) and cls.name == "ElementSolid":
            for fn in cls.body:
                if isinstance(fn, ast.FunctionDef) and fn.name == "_parse_ten_nodes_block":
                    code = textwrap.dedent(ast.get_source_segment(src, fn))
                    # 옛 판은 '헤더 형식 이상' 출력을 5건에서 끊는다(>10 경고와 같은 계수) — 판정용으로 늘 찍게 한다
                    code, n = re.subn(r'if warn_cnt < 5:\n(\s+)print\("  Warning: ELEMENT_SOLID ten-nodes 헤더 형식 이상',
                                      r'if True:\n\1print("  Warning: ELEMENT_SOLID ten-nodes 헤더 형식 이상', code)
                    assert n == 1, "옛 판 계측 실패"
                    ns = {"ElementSolid": ElementSolid}       # _split_header 는 바꾸지 않는다
                    exec(code, ns)
                    return ns["_parse_ten_nodes_block"]
    return None


NEW = ElementSolid._parse_ten_nodes_block
OLD = load_base_fn()


# ── 매트릭스 ──────────────────────────────────────────────────────────────────

def cases():
    """(이름, expect, elems, w, extra, kind) — kind: keep(옛 판도 맞음) · trunc(옛 판이 틀림) · limit(알려진 한계)."""
    big = 10000000                     # I10 은 8자리 ID 로 — 실덱처럼
    for w in (8, 10, "free"):
        b0 = big if w == 10 else 0
        e = lambda i, n10, mode, pid=1: (b0 + i, pid, n10, mode)   # noqa: E731
        H = lambda i: hexa(b0 + 8 * i)                               # noqa: E731
        T = lambda i: tet10(b0 + 10 * i)                             # noqa: E731
        yield (f"W{w} 한 줄 육면체 3", 10, [e(1, H(0), "line10"), e(2, H(1), "line10"), e(3, H(2), "line10")], w, None, "keep")
        yield (f"W{w} 한 줄 TET10 3", 10, [e(1, T(0), "line10"), e(2, T(1), "line10"), e(3, T(2), "line10")], w, None, "keep")
        for mode in ("w82", "w442", "w2", "w1"):
            yield (f"W{w} {mode} TET10 3", 10, [e(1, T(0), mode), e(2, T(1), mode), e(3, T(2), mode)], w, None, "keep")
        for extra in ("blank", "comment", "crlf"):
            yield (f"W{w} 한 줄 TET10 + {extra}", 10, [e(1, T(0), "line10"), e(2, T(1), "line10")], w, extra, "keep")
            yield (f"W{w} w82 TET10 + {extra}", 10, [e(1, T(0), "w82"), e(2, T(1), "w82")], w, extra, "keep")
        yield (f"W{w} 마지막 요소만 절삭", 10, [e(1, H(0), "line10"), e(2, H(1), "line10"), e(3, H(2), "trunc8")], w, None, "keep")
        # 선언 없는 2-카드(A27, expect=8) — 8절점 노드줄
        yield (f"W{w} 비선언 2-카드 8절점 3", 8, [e(1, H(0), "trunc8"), e(2, H(1), "trunc8"), e(3, H(2), "trunc8")], w, None, "keep")
        # ── 절삭(이번 수정) ──
        yield (f"W{w} 절삭 육면체 3", 10, [e(1, H(0), "trunc8"), e(2, H(1), "trunc8"), e(3, H(2), "trunc8")], w, None, "trunc")
        yield (f"W{w} 절삭 육면체 5", 10, [e(i + 1, H(i), "trunc8") for i in range(5)], w, None, "trunc")
        yield (f"W{w} 절삭 TET4 3", 10, [e(1, tet4(b0), "trunc8"), e(2, tet4(b0 + 10), "trunc8"), e(3, tet4(b0 + 20), "trunc8")], w, None, "trunc")
        for extra in ("blank", "comment", "crlf"):
            yield (f"W{w} 절삭 육면체 + {extra}", 10, [e(1, H(0), "trunc8"), e(2, H(1), "trunc8"), e(3, H(2), "trunc8")], w, extra, "trunc")
        yield (f"W{w} 섞임: 절삭·w82·절삭", 10, [e(1, H(0), "trunc8"), e(2, T(1), "w82"), e(3, H(3), "trunc8"), e(4, H(4), "trunc8")], w, None, "trunc")
        yield (f"W{w} 섞임: 한 줄 TET10·절삭·한 줄", 10, [e(1, T(0), "line10"), e(2, H(2), "trunc8"), e(3, H(3), "line10"), e(4, H(4), "trunc8"), e(5, H(5), "line10")], w, None, "trunc")
        yield (f"W{w} 섞임: 절삭·4+4+2", 10, [e(1, H(0), "trunc8"), e(2, T(1), "w442"), e(3, H(3), "trunc8"), e(4, H(4), "trunc8")], w, None, "trunc")
        yield (f"W{w} 다른 PID 섞인 절삭", 10, [e(1, H(0), "trunc8", 7), e(2, H(1), "trunc8", 9), e(3, H(2), "trunc8", 7)], w, None, "trunc")
        yield (f"W{w} 섞임: 절삭·1개씩", 10, [e(1, H(0), "trunc8"), e(2, T(1), "w1"), e(3, H(3), "trunc8"), e(4, T(4), "w1")], w, None, "trunc")
        # ── 알려진 한계: 절삭 뒤 2개씩 넘김 — 모양만으론 못 가린다(동작 불변만 본다) ──
        yield (f"W{w} 한계: 절삭 뒤 2개씩 넘김", 10, [e(1, H(0), "trunc8"), e(2, T(1), "w2"), e(3, T(2), "w2")], w, None, "limit")
    # I8 8자리 ID(공백 없이 붙은 필드)
    b = 10000000
    yield ("W8 8자리 ID 절삭 3", 10, [(b + 1, 1, hexa(b), "trunc8"), (b + 2, 1, hexa(b + 8), "trunc8"), (b + 3, 1, hexa(b + 16), "trunc8")], 8, None, "trunc")
    yield ("W8 8자리 ID 한 줄 TET10", 10, [(b + 1, 1, tet10(b), "line10"), (b + 2, 1, tet10(b + 10), "line10")], 8, None, "keep")


print("[1] 매트릭스 — 새 함수가 정답과 같은가")
results = []
for name, expect, elems, w, extra, kind in cases():
    block = build(elems, w, extra)
    got, log = run(NEW, block, expect)
    results.append((name, expect, elems, w, extra, kind, block, got, log))
    if kind in ("keep", "trunc"):
        check(f"{name}", got == expected(elems), f"\n    got={got}\n    want={expected(elems)}")
    if kind == "trunc":
        check(f"{name} — 경고 없음", "헤더 형식 이상" not in log and "🔴" not in log, log.strip()[:200])

print("[2] 차분 — 고치기 직전 판과 다른 결과는 옛 판이 줄을 버린 경우뿐인가")
if OLD is None:
    print("  (git 또는 기준 판이 없어 건너뜀)")
else:
    n_same = n_fixed = 0
    for name, expect, elems, w, extra, kind, block, got, log in results:
        old, old_log = run(OLD, block, expect)
        if old == got:
            n_same += 1
            if kind == "trunc":
                check(f"{name} — 옛 판은 틀렸어야 한다", False, "옛 판도 맞음 → 재현 실패")
            continue
        n_fixed += 1
        check(f"{name} — 바뀐 경우는 옛 판이 줄을 버린 경우", "헤더 형식 이상" in old_log, old_log.strip()[:200])
        check(f"{name} — 바뀐 경우는 절삭 케이스", kind == "trunc", kind)
    check(f"차분 요약: 같음 {n_same} · 바뀜 {n_fixed} (바뀜 = 절삭 케이스 수)",
          n_fixed == sum(1 for r in results if r[5] == "trunc"))

print("[3] 무작위 차분 — 배치·폭·부가·ID 길이를 섞은 블록 3000개 (시드 고정)")
if OLD is None:
    print("  (git 또는 기준 판이 없어 건너뜀)")
else:
    import random
    rng = random.Random(20261022)
    n_blocks = n_changed = bad_change = bad_new = 0
    for _ in range(3000):
        w = rng.choice([8, 10, "free"])
        b0 = rng.choice([0, 10000000]) if w != 8 else rng.choice([0, 1000000])
        extra = rng.choice([None, None, "blank", "comment", "crlf"])
        elems, limit = [], False
        prev_trunc = False
        for i in range(rng.randint(1, 7)):
            kind = rng.choice(["hexa", "tet10", "tet4"])
            n10 = {"hexa": hexa, "tet10": tet10, "tet4": tet4}[kind](b0 + 20 * i)
            modes = ["line10", "w82", "w442", "w2", "w1"] + (["trunc8", "trunc8"] if n10[8:] == [0, 0] else [])
            mode = rng.choice(modes)
            if prev_trunc and mode == "w2":
                limit = True                      # 알려진 한계 — 모양만으론 못 가린다
            prev_trunc = mode == "trunc8"
            elems.append((b0 + i + 1, rng.choice([1, 2, 37]), n10, mode))
        block = build(elems, w, extra)
        new, _ = run(NEW, block, 10)
        old, old_log = run(OLD, block, 10)
        n_blocks += 1
        if new != old:
            n_changed += 1
            if "헤더 형식 이상" not in old_log:
                bad_change += 1
        if not limit and new != expected(elems):
            bad_new += 1
    check(f"무작위 {n_blocks}개: 바뀐 {n_changed}개는 전부 옛 판이 줄을 버린 경우", bad_change == 0, f"아님 {bad_change}")
    check(f"무작위 {n_blocks}개: 한계 패턴 밖에선 새 판이 전부 정답", bad_new == 0, f"오답 {bad_new}")

print("[4] 적대 리뷰 반례 — 옛 판이 맞던 블록은 결과·saw_i10 이 그대로, M1 은 🔴")
f8 = lambda v: "".join(f"{x:8d}" for x in v)      # noqa: E731
f10 = lambda v: "".join(f"{x:10d}" for x in v)    # noqa: E731
f20 = lambda v: "".join(f"{x:20d}" for x in v)    # noqa: E731
keep_base = {
    "CE-1 I8 8+2 뒤 I10 헤더": [f8([1, 1]), f8(range(1, 9)), f8([9, 10]), f10([10000002, 1]), f10(range(10000011, 10000021))],
    "A3 I10 8+2 뒤 LONG 헤더": [f10([1, 1]), f10(range(1, 9)), f10([9, 10]), f20([2, 1]), f20(range(11, 21))],
    "B1 I8 8+2 뒤 18자 자유간격 헤더": [f8([1, 1]), f8(range(1, 9)), f8([9, 10]), "     2           1", " ".join(str(x) for x in range(11, 21))],
    "C1 자유간격 8+2 뒤 붙은 헤더": ["1 1", " ".join(str(x) for x in range(1, 9)), "9 10", "1000000210000001", " ".join(str(x) for x in range(11, 21))],
    "D1 넘김 TET10 뒤 잡문": [f8([1, 1]), f8(range(1, 9)), f8([9, 10]), "this is a stray text line", f8([2, 1]), f8(range(11, 21))],
    "E1 넘김 TET10 뒤 쉼표 카드": [f8([1, 1]), f8(range(1, 9)), f8([9, 10]), "2,1", ",".join(str(x) for x in range(11, 21))],
}
if OLD is None:
    print("  (git 또는 기준 판이 없어 건너뜀)")
else:
    for name, lines in keep_base.items():
        blk = [ln + "\n" for ln in lines]
        buf_o, buf_n = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_o):
            po, io10 = OLD(blk, 10)
        with contextlib.redirect_stdout(buf_n):
            pn, in10 = NEW(blk, 10)
        check(f"{name} — 결과 그대로", pn == po, f"\n    old={po}\n    new={pn}")
        check(f"{name} — saw_i10 그대로", io10 == in10, f"old={io10} new={in10}")
    m1 = build([(1, 1, hexa(0), "trunc8"), (2, 1, hexa(10), "trunc8"), (3, 1, tet10(20), "w2")], 8)
    _, log = run(NEW, m1, 10)
    check("M1 절삭 뒤 2개씩 넘김 섞임 — 🔴 로 알린다", "🔴" in log and "섞여" in log, log.strip()[:200])

print("[5] 무작위 차분(폭 섞임·잡문) — 바뀌면 옛 판이 줄을 버린 경우, 안 바뀌면 saw_i10 동일")
if OLD is None:
    print("  (git 또는 기준 판이 없어 건너뜀)")
else:
    import random
    rng = random.Random(1022)
    n_blocks = n_changed = bad_change = bad_i10 = 0
    for _ in range(4000):
        lines = []
        for i in range(rng.randint(1, 6)):
            w = rng.choice([8, 10, "free"])
            n10 = rng.choice([hexa, tet10, tet4])(20 * i + (10000000 if w == 10 and rng.random() < 0.5 else 0))
            modes = ["line10", "w82", "w442", "w2", "w1"] + (["trunc8", "trunc8"] if n10[8:] == [0, 0] else [])
            lines.append(fmt([i + 1 + (10000000 if w == 10 else 0), rng.choice([1, 2, 37])], w))
            lines.extend(node_lines(n10, rng.choice(modes), w))
            if rng.random() < 0.1:
                lines.append(rng.choice(["stray text", "2,1", "1,2,3,4,5,6,7,8,9,10", "$ c", ""]))
        blk = [ln + "\n" for ln in lines]
        buf_o, buf_n = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_o):
            po, io10 = OLD(blk, 10)
        with contextlib.redirect_stdout(buf_n):
            pn, in10 = NEW(blk, 10)
        n_blocks += 1
        if pn != po:
            n_changed += 1
            if "헤더 형식 이상" not in buf_o.getvalue():
                bad_change += 1
        elif io10 != in10:
            bad_i10 += 1
    check(f"무작위 {n_blocks}개(폭 섞임·잡문): 바뀐 {n_changed}개는 전부 옛 판이 줄을 버린 경우", bad_change == 0, f"아님 {bad_change}")
    check(f"무작위 {n_blocks}개(폭 섞임·잡문): 안 바뀐 블록의 saw_i10 동일", bad_i10 == 0, f"다름 {bad_i10}")

print("[6] 통합 리뷰 반례 — 정수 잡줄(R1)·🔴 오탐(R2)")
if OLD is None:
    print("  (git 또는 기준 판이 없어 건너뜀)")
else:
    r1 = {
        "R1 넘김 TET10 뒤 '0 0 0' 잡줄": [f8([1, 1]), f8(range(1, 9)), f8([9, 10]), f8([0, 0, 0]), f8([2, 1]), f8(range(11, 21))],
        "R1 넘김 TET10 뒤 '7' 잡줄(PID 10)": [f8([1, 1]), f8(range(1, 9)), f8([9, 10]), f8([7]), f8([2, 10]), f8(range(11, 21))],
        "R1 넘김 TET10 뒤 정수 3개 잡줄·자유간격": ["1 1", "1 2 3 4 5 6 7 8", "9 10", "5 6 7", "2 1", " ".join(str(x) for x in range(11, 21))],
    }
    for name, lines in r1.items():
        blk = [ln + "\n" for ln in lines]
        po, io10 = OLD(blk, 10)[0], None
        with contextlib.redirect_stdout(io.StringIO()):
            po, io10 = OLD(blk, 10)
            pn, in10 = NEW(blk, 10)
        check(f"{name} — 옛 판 결과 그대로", pn == po and io10 == in10, f"\n    old={po}\n    new={pn}")
    ok_mix = build([(1, 1, tet10(0), "w2"), (2, 1, hexa(10), "trunc8"), (3, 1, hexa(20), "trunc8")], 8)
    got, log = run(NEW, ok_mix, 10)
    check("R2 2개씩 TET10 뒤 절삭 — 맞게 읽고 🔴 없음",
          got == expected([(1, 1, tet10(0), "w2"), (2, 1, hexa(10), "trunc8"), (3, 1, hexa(20), "trunc8")]) and "🔴" not in log, log.strip()[:200])

print("[6b] 2차 반례 리뷰 — >10 경고 5건 뒤 절삭(옛 판은 줄을 버리고도 말이 없다)·8정수 잡줄은 조용하지 않다")
cap = []
for k in range(1, 6):
    cap += [f8([k, 1]), f8(list(range(10 * k + 1, 10 * k + 11)) + [99])]
cap += [f8([6, 1]), f8(range(61, 69)), f8([7, 1]), f8(range(71, 81))]
got, log = run(NEW, [ln + "\n" for ln in cap], 10)
want = [(k, 1, list(range(10 * k + 1, 10 * k + 11))) for k in range(1, 6)] + [(6, 1, list(range(61, 69)) + [0, 0]), (7, 1, list(range(71, 81)))]
check("경고 상한(5건) 뒤 절삭 — 새 판이 맞게 읽는다", got == want, f"\n    got={got}")
if OLD is not None:
    _, old_log = run(OLD, [ln + "\n" for ln in cap], 10)
    check("경고 상한 뒤 절삭 — 계측한 옛 판은 버린 줄을 드러낸다", "헤더 형식 이상" in old_log, old_log.strip()[:160])
stray8 = [f8([1, 1]), f8(range(1, 9)), f8([9, 10]), f8(range(41, 49)), f8([2, 1]), f8(range(11, 21))]
_, log = run(NEW, [ln + "\n" for ln in stray8], 10)
check("8정수 잡줄(모양으론 절삭과 같음) — 재해석을 알린다", "n9·n10 을 생략한 카드" in log, log.strip()[:160])

print("[7] 무작위 차분(정수 잡줄) — 옛 판이 맞던 블록은 새 판도 같다")
if OLD is None:
    print("  (git 또는 기준 판이 없어 건너뜀)")
else:
    import random
    rng = random.Random(777)
    n_blocks = n_oldok = broke = bad_change = 0
    for _ in range(4000):
        w = rng.choice([8, 10, "free"])
        lines, elems = [], []
        for i in range(rng.randint(1, 6)):
            n10 = rng.choice([hexa, tet10, tet4])(20 * i)
            modes = ["line10", "w82", "w442", "w2", "w1"] + (["trunc8", "trunc8"] if n10[8:] == [0, 0] else [])
            mode = rng.choice(modes)
            elems.append((i + 1, 1, n10, mode))
            lines.append(fmt([i + 1, 1], w))
            lines.extend(node_lines(n10, mode, w))
            if rng.random() < 0.15:
                lines.append(fmt(rng.choice([[0, 0, 0], [7], [1, 2, 3], [5, 6, 7, 8, 9]]), w))
        blk = [ln + "\n" for ln in lines]
        buf_o = io.StringIO()
        with contextlib.redirect_stdout(buf_o):
            po, io10 = OLD(blk, 10)
        with contextlib.redirect_stdout(io.StringIO()):
            pn, in10 = NEW(blk, 10)
        n_blocks += 1
        if pn != po and "헤더 형식 이상" not in buf_o.getvalue():
            bad_change += 1
        if normalize(po) == expected(elems):
            n_oldok += 1
            if pn != po:
                broke += 1
    check(f"무작위 {n_blocks}개(정수 잡줄): 바뀐 블록은 전부 옛 판이 줄을 버린 경우", bad_change == 0, f"아님 {bad_change}")
    check(f"무작위 {n_blocks}개(정수 잡줄): 옛 판이 맞던 {n_oldok}개 중 새 판이 깬 것 0", broke == 0, f"깸 {broke}")

print()
if FAILS:
    print(f"FAIL {len(FAILS)}건")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
print("ALL PASS")
