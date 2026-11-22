# 한 벌짜리 제어·DB 카드에 덱 원문을 붙여 두고, 쓸 때 모드가 바꾸지 않은 칸·기록기에 없는 끝 칸·끝 카드를 덱 글로 되살리는 도우미
"""덱 글 되살리기 — 남은 결함 묶음 A1(2026-11-22).

한 벌짜리 *CONTROL_*·*DATABASE_* 카드는 클래스가 아는 칸만 객체에 담았다가 기록기가 다시 쓴다. 그래서 기록기에 없는
선택 카드(EXTENT_BINARY 카드 3·4, D3PLOT 카드 2, TIMESTEP 카드 3 …)와 끝 칸(ACCURACY 의 EXACC·SRTFLG, ENERGY 의
DRLEN·DISEN …)이 rc 0 으로 조용히 빠졌다. 가져온 직후 객체에 덱 원문 블록과 그때의 기록 결과(base)를 붙여 두고,
쓸 때 지금 기록 결과(now)와 데이터 줄·칸 단위로 맞춘다.

  - 모드가 바꾼 칸(base ≠ now) → now
  - 기록기에 없는 끝 칸·끝 카드 → 덱 글(값 0 인 끝 칸과 맨 끝의 빈·0 카드는 붙이지 않는다 — LS-DYNA 는 빈 숫자 칸을 0 으로 읽는다)
  - 안 바뀐 칸: 덱 칸이 비었거나, 수치가 같거나, now 가 빈칸이고 덱 값이 0 이면 now. 아니면 덱 글
    (기록 포맷이 자릿수를 버린 값·숫자 아닌 글)
  - 바꾼 칸이 없는 줄은 now 줄 그대로 — 덱이 기록기로 다 표현되면 출력이 예전과 바이트까지 같다

모드가 Set*() 으로 새로 만든 객체에는 덱 정보가 없다 → 예전 그대로 쓴다(모드가 카드를 통째로 다시 정한 것).
"""
import io
import re

try:
    from KooCAEManager.KooDefine import _real10
except ImportError:   # KooCAEManager 폴더 안에서 직접 돌릴 때(다른 모듈의 __main__ 갈래)
    from KooDefine import _real10

_FORTRAN_EXP = re.compile(r"^([+-]?(?:\d+\.?\d*|\.\d+))([+-]\d+)$")
_W10 = [10] * 8
_KEYS = ("_deck_lines", "_deck_base", "_deck_snap", "_deck_widths", "_deck_guard", "_deck_i10")
_MISSING = object()


def _num(text):
    """칸 글의 수치(E 없는 Fortran 지수·d 지수 포함). 숫자가 아니면 None."""
    t = text.strip()
    m = _FORTRAN_EXP.match(t)
    if m:
        t = m.group(1) + "e" + m.group(2)
    try:
        return float(t.replace("d", "e").replace("D", "e"))
    except ValueError:
        return None


def _render(obj):
    s = io.StringIO()
    obj.WriteStreamDynaKeyword(s)
    return s.getvalue()


def _state(obj):
    return {k: v for k, v in vars(obj).items() if not k.startswith("_deck_")}


def attach(obj, kw, block, fmt=None, widths=None, guard=()):
    """가져온 직후 객체에 덱 원문 블록(리더가 주석을 뺀 데이터 줄)을 붙인다. 무엇이 잘못돼도 붙이지 않을 뿐이다(예전처럼 쓴다).
    기록기의 키워드 줄이 *kw 가 아니면(같은 자리를 다른 키워드가 덮었거나 이름 없는 INTFOR_FILE 을 INTFOR 로 쓰는 경우) 붙이지 않는다.

    widths: {데이터 줄 번호: 칸 폭 목록 또는 "text"} — 없으면 10칸 8개. guard: 바뀌면 끝 카드를 붙이지 않는 속성 이름
    (끝 카드가 그 칸 값에 달린 경우 — 예: DYNAMIC_RELAXATION 카드 2 는 IDRFLG 에 달렸다)."""
    if obj is None or not block or fmt == "long":
        return
    try:
        lines = [l.rstrip("\r\n") for l in block]
        while lines and not lines[-1].strip():
            lines.pop()
        base = _render(obj) if lines else ""
        if base.split("\n", 1)[0].strip().upper() == "*" + kw.upper():
            obj._deck_lines, obj._deck_base, obj._deck_snap = lines, base, _state(obj)
            obj._deck_widths, obj._deck_guard, obj._deck_i10 = dict(widths or {}), tuple(guard), fmt == "i10"
    except Exception:
        for k in _KEYS:
            obj.__dict__.pop(k, None)


def write(obj, stream):
    """관리자 기록기가 객체마다 부른다. 덱 정보가 없으면 객체 기록기 그대로."""
    if getattr(obj, "_deck_lines", None) is None:
        obj.WriteStreamDynaKeyword(stream)
        return
    now = _render(obj)
    try:
        out = _merge(obj, now)
    except Exception as e:   # 되살리기가 죽어도 예전 출력은 낸다
        print(f"  Warning: {now.split(chr(10), 1)[0]} 덱 글 되살리기 실패({type(e).__name__}: {e}) — 기록기 출력만 쓴다"
              f"(덱의 끝 칸·끝 카드가 빠졌을 수 있다)")
        out = now
    stream.write(out)


def _cut(line, widths):
    """고정 폭 칸 — 줄 길이 안에 시작하는 칸만."""
    out, pos = [], 0
    for w in widths:
        if pos >= len(line):
            break
        out.append(line[pos:pos + w])
        pos += w
    return out


def _deck_fields(line, widths):
    """덱 줄의 칸 글(앞뒤 공백 뺌) — DynaKeyword.parse_whole 과 같은 규칙: 칸이 둘 이상이고 모두 20칸 이하인 카드의 콤마는 자유형식."""
    if len(widths) > 1 and max(widths) <= 20 and "," in line:
        return [v.strip() for v in line.split(",")][:len(widths)]
    return [f.strip() for f in _cut(line, widths)]


def _fit(text, w):
    """덱 글을 칸 폭에 오른쪽 맞춤. 넘치면 숫자는 10칸 안의 가장 가까운 표기, 아니면 None(지금 글을 둔다)."""
    if len(text) <= w:
        return text.rjust(w)
    v = _num(text)
    return _real10(v) if v is not None and w == 10 else None


def _pick(deck, base, now):
    """안 바뀐 칸 하나: None = now 그대로, 아니면 되살릴 덱 글."""
    if base is None or now != base or not deck:
        return None
    n = now.strip()
    dv = _num(deck)
    if not n:
        return None if dv == 0.0 else deck    # 빈칸 ≡ 0 (0 을 빈칸으로 쓰는 기록기)
    nv = _num(n)
    if dv is not None and nv is not None:
        return None if dv == nv else deck
    return None if deck.upper() == n.upper() else deck


def _merge(obj, now):
    deck, base = obj._deck_lines, obj._deck_base
    nl, bl = now.splitlines(), base.splitlines()
    nd = [i for i, l in enumerate(nl) if not l.startswith(("*", "$"))]
    bd = [i for i, l in enumerate(bl) if not l.startswith(("*", "$"))]
    if len(nd) != len(bd):
        return now          # 모드가 카드 짜임을 바꿨다 — 덱 줄과 맞출 수 없다
    st, snap = _state(obj), obj._deck_snap
    moved = sum(1 for k in set(st) | set(snap) if st.get(k, _MISSING) != snap.get(k, _MISSING))
    rows = [(k, i, nl[i], bl[j], obj._deck_widths.get(k)) for k, (i, j) in enumerate(zip(nd, bd)) if k < len(deck)]
    shown = 0
    for _, _, n, b, hint in rows:
        if hint == "text":
            shown += n != b
        else:
            nf, bf = _cut(n, hint or _W10), _cut(b, hint or _W10)
            shown += sum(1 for x, y in zip(nf, bf) if x != y) + abs(len(nf) - len(bf))
    # 바뀐 속성이 기록에 보이는 바뀐 칸보다 많으면(모드 값의 표기가 가져온 때와 같아진 경우) 덱 글로 모델 칸을 덮지 않는다
    safe = moved <= shown
    out = list(nl)
    for k, i, n, b, hint in rows:
        d = deck[k]
        if hint == "text":
            if safe and n == b and d.strip():
                out[i] = d.rstrip()
            continue
        if obj._deck_i10 and hint:
            continue
        w = hint or _W10
        nf, bf, df = _cut(n, w), _cut(b, w), _deck_fields(d, w)
        cells, touched = list(nf), False
        for f, dt in enumerate(df):
            if not dt:
                continue
            if f < len(nf):
                p = _pick(dt, bf[f] if f < len(bf) else None, nf[f]) if safe else None
                t = _fit(p, w[f]) if p is not None else None
                if t is not None and len(nf[f]) == w[f]:
                    cells[f], touched = t, True
            else:
                # 기록기에 없는 끝 칸. 값 0 은 붙이지 않는다 — LS-DYNA 는 빈 숫자 칸을 0 으로 읽는다(빈칸 ≡ 0)
                t = _fit(dt, w[f]) if _num(dt) != 0.0 else None
                if t is None:
                    continue
                if cells:
                    cells[-1] = cells[-1].ljust(w[len(cells) - 1])
                while len(cells) < f:
                    cells.append(" " * w[len(cells)])
                cells.append(t)
                touched = True
        if touched:
            out[i] = "".join(cells)
    tail = deck[len(nd):]
    while tail and all(_num(x) == 0.0 or not x for x in _deck_fields(tail[-1], _W10)):
        tail.pop()          # 맨 끝의 빈·0 카드는 없는 카드와 같다(빈칸 ≡ 0). 뒤 카드 자리를 지키는 가운데 것은 둔다
    if tail and all(st.get(g, _MISSING) == snap.get(g, _MISSING) for g in obj._deck_guard):
        out.extend(l.rstrip() for l in tail)
    return "\n".join(out) + "\n"
