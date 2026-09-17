# SmartTwinPreprocessor 도구 공통 --help 엔진 — 모드 목록·검색·상세(사례 포함) 출력
"""
정본은 occProject/Generators/KooCLIHelp/engine.py 다.
KooChainRun 은 패키지 경로가 달라 Runner/cli_help_engine.py 에 같은 파일을 두고,
tests/test_cli_help.py 가 두 파일이 바이트 단위로 같은지 확인한다. 한쪽만 고치지 말 것.

공통 계약 (모든 도구 동일)
    TOOL --help                 개요 + 모드 목록 + 검색법
    TOOL --help <검색어...>     정확 일치면 상세, 아니면 이름·별칭·요약·키 검색
    TOOL --help all             전 모드 상세
    TOOL --help <주제>          format 등 공통 주제

무거운 import(OCC·Qt) 전에 부를 것 — 파일을 만들지 않고 표준 라이브러리만 쓴다.

카탈로그 형식
    Catalog(tool, tagline, usage=[...], overview=[...], modes=[Mode...], topics=[Topic...], footer=[...])
    Mode(name, summary, when=[...], aliases=[...], syntax=[...], keys=[Key...],
         examples=[Example...], notes=[...], related=[...], category="")
    Key(name, type, default, desc, required=False)
    Example(title, text, explain=[...])
    Topic(name, summary, body=[...], aliases=[...])
"""

import sys
import unicodedata

HELP_FLAGS = ("-h", "--help", "help", "-help", "/?")


class Key:
    def __init__(self, name, type, default, desc, required=False):
        self.name, self.type, self.default, self.desc, self.required = name, type, default, desc, required


class Example:
    def __init__(self, title, text, explain=None, verify=None):
        self.title, self.text = title, text.strip("\n")
        self.explain = explain or []
        # verify 는 회귀 시험 전용(출력하지 않는다) — 사례를 실제 파서/바이너리로 돌렸을 때의 기대치
        self.verify = verify


class Mode:
    def __init__(self, name, summary, when=None, aliases=None, syntax=None, keys=None,
                 examples=None, notes=None, related=None, category=""):
        self.name, self.summary = name, summary
        self.when = when or []
        self.aliases = aliases or []
        self.syntax = syntax or []
        self.keys = keys or []
        self.examples = examples or []
        self.notes = notes or []
        self.related = related or []
        self.category = category


class Topic:
    def __init__(self, name, summary, body, aliases=None):
        self.name, self.summary, self.body = name, summary, body
        self.aliases = aliases or []


class Catalog:
    def __init__(self, tool, tagline, usage, overview=None, modes=None, topics=None, footer=None,
                 mode_label="모드"):
        self.tool, self.tagline, self.usage = tool, tagline, usage
        self.overview = overview or []
        self.modes = modes or []
        self.topics = topics or []
        self.footer = footer or []
        self.mode_label = mode_label


# ── 정규화·검색 ────────────────────────────────────────────────
def _norm(s):
    s = unicodedata.normalize("NFKC", str(s)).casefold()
    return "".join(ch for ch in s if ch.isalnum())


def _tokens(query):
    out = []
    for raw in query.replace(",", " ").split():
        n = _norm(raw)
        if n:
            out.append(n)
    return out


def _mode_fields(m):
    return {
        "name": [_norm(m.name)],
        "alias": [_norm(a) for a in m.aliases],
        "summary": [_norm(m.summary)] + [_norm(w) for w in m.when],
        "key": [_norm(k.name) for k in m.keys] + [_norm(k.desc) for k in m.keys],
        "body": [_norm(n) for n in m.notes] + [_norm(m.category)],
    }


def search(catalog, query):
    """(점수, 항목) 내림차순. 모든 토큰이 어딘가에 걸린 항목만 반환."""
    toks = _tokens(query)
    if not toks:
        return []
    whole = _norm(query)
    scored = []
    for m in catalog.modes:
        f = _mode_fields(m)
        if whole and (whole in f["name"] or whole in f["alias"]):
            scored.append((1000, m))
            continue
        total, all_hit = 0, True
        for t in toks:
            best = 0
            if any(t == v for v in f["name"] + f["alias"]):
                best = 100
            elif any(t in v for v in f["name"]):
                best = 60
            elif any(t in v for v in f["alias"]):
                best = 50
            elif any(t in v for v in f["summary"]):
                best = 20
            elif any(t in v for v in f["key"]):
                best = 12
            elif any(t in v for v in f["body"]):
                best = 5
            if best == 0:
                all_hit = False
                break
            total += best
        if all_hit:
            scored.append((total, m))
    for tp in catalog.topics:
        names = [_norm(tp.name)] + [_norm(a) for a in tp.aliases]
        if whole in names:
            scored.append((1000, tp))
        elif all(any(t in n for n in names) or t in _norm(tp.summary) for t in toks):
            scored.append((30, tp))
    scored.sort(key=lambda x: (-x[0], x[1].name))
    return scored


# ── 렌더링 ─────────────────────────────────────────────────────
def _w(out, line=""):
    out.append(line)


def _wrap_table(rows, headers):
    widths = [len(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], _disp_len(c))
    def fmt(r):
        return "  " + "  ".join(_pad(c, widths[i]) if i < len(r) - 1 else c for i, c in enumerate(r))
    lines = [fmt(headers), "  " + "  ".join("-" * w for w in widths)]
    lines += [fmt(r) for r in rows]
    return lines


def _disp_len(s):
    # 한글·전각 문자는 터미널에서 2칸
    n = 0
    for ch in str(s):
        n += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return n


def _pad(s, width):
    return str(s) + " " * max(0, width - _disp_len(s))


def render_overview(catalog):
    out = []
    _w(out, f"{catalog.tool} — {catalog.tagline}")
    _w(out)
    _w(out, "사용법")
    for u in catalog.usage:
        _w(out, "  " + u)
    if catalog.overview:
        _w(out)
        for o in catalog.overview:
            _w(out, o)
    if catalog.modes:
        _w(out)
        _w(out, f"{catalog.mode_label} ({len(catalog.modes)})")
        cats = []
        for m in catalog.modes:
            if m.category not in cats:
                cats.append(m.category)
        namew = max(len(m.name) for m in catalog.modes)
        for c in cats:
            if c:
                _w(out, f"  [{c}]")
            for m in catalog.modes:
                if m.category == c:
                    _w(out, f"    {m.name.ljust(namew)}  {m.summary}")
    if catalog.topics:
        _w(out)
        _w(out, "공통 주제")
        tw = max(len(t.name) for t in catalog.topics)
        for t in catalog.topics:
            _w(out, f"    {t.name.ljust(tw)}  {t.summary}")
    _w(out)
    _w(out, "도움말")
    _w(out, f"  {catalog.tool} --help <{catalog.mode_label} 또는 검색어>   상세 설명 + 그대로 쓰는 사례")
    _w(out, f"  {catalog.tool} --help all                     전체 상세 (LLM 이 한 번에 읽기용)")
    for f in catalog.footer:
        _w(out, "  " + f)
    return "\n".join(out)


def render_mode(catalog, m):
    out = []
    bar = "=" * 78
    _w(out, bar)
    _w(out, f"{m.name} — {m.summary}")
    _w(out, bar)
    if m.aliases:
        _w(out, "검색어: " + ", ".join(m.aliases))
    if m.when:
        _w(out)
        _w(out, "언제 쓰나")
        for x in m.when:
            _w(out, "  - " + x)
    if m.syntax:
        _w(out)
        _w(out, "형식")
        for x in m.syntax:
            _w(out, "  " + x)
    if m.keys:
        _w(out)
        _w(out, "입력 키")
        for k in m.keys:
            meta = [k.type] if k.type else []
            if k.required:
                meta.append("필수")
            elif str(k.default) not in ("", "-"):
                meta.append(f"기본 {k.default}")
            _w(out, f"  {k.name}  [{' · '.join(meta)}]" if meta else f"  {k.name}")
            if k.desc:
                _w(out, f"      {k.desc}")
    for i, ex in enumerate(m.examples, 1):
        _w(out)
        _w(out, f"사례 {i} — {ex.title}")
        _w(out, "-----8<----- 여기부터 그대로 복사 -----8<-----")
        for line in ex.text.splitlines():
            _w(out, line)
        _w(out, "-----8<----- 여기까지 ------------------------8<-----")
        for e in ex.explain:
            _w(out, "  · " + e)
    if m.notes:
        _w(out)
        _w(out, "주의")
        for n in m.notes:
            _w(out, "  - " + n)
    if m.related:
        _w(out)
        _w(out, "관련: " + ", ".join(m.related))
    return "\n".join(out)


def render_topic(catalog, t):
    out = []
    bar = "=" * 78
    _w(out, bar)
    _w(out, f"{t.name} — {t.summary}")
    _w(out, bar)
    for b in t.body:
        _w(out, b)
    return "\n".join(out)


def render_query(catalog, query):
    q = query.strip()
    if _norm(q) in ("all", "전체"):
        parts = [render_overview(catalog)]
        parts += [render_topic(catalog, t) for t in catalog.topics]
        parts += [render_mode(catalog, m) for m in catalog.modes]
        return "\n\n".join(parts)
    hits = search(catalog, q)
    if not hits:
        names = ", ".join(m.name for m in catalog.modes)
        return (f"'{q}' 에 해당하는 {catalog.mode_label}·주제가 없습니다.\n"
                f"{catalog.mode_label} 목록: {names}\n"
                f"{catalog.tool} --help 로 전체 목록을 보세요.")
    top_score, top = hits[0]
    runner_up = hits[1][0] if len(hits) > 1 else -1
    decisive = top_score >= 1000 or (top_score >= 50 and top_score > runner_up)
    if decisive:
        body = render_topic(catalog, top) if isinstance(top, Topic) else render_mode(catalog, top)
        others = [h for _, h in hits[1:6]]
        if others:
            body += "\n\n다른 후보: " + ", ".join(o.name for o in others)
        return body
    out = [f"'{q}' 검색 결과 {len(hits)}건 — 이름을 정확히 주면 상세가 나옵니다", ""]
    nw = max(len(h.name) for _, h in hits[:15])
    for _, h in hits[:15]:
        out.append(f"  {h.name.ljust(nw)}  {h.summary}")
    return "\n".join(out)


def handle_help(argv, catalog, stream=None, no_args_is_help=False):
    """argv 가 help 요청이면 출력하고 True. 아니면 False (호출부가 원래 흐름을 계속)."""
    stream = stream or sys.stdout
    args = list(argv[1:])
    if not args:
        if not no_args_is_help:
            return False
        text = render_overview(catalog)
    elif args[0] in HELP_FLAGS:
        text = render_overview(catalog) if len(args) == 1 else render_query(catalog, " ".join(args[1:]))
    else:
        return False
    try:
        stream.write(text + "\n")
        stream.flush()
    except UnicodeEncodeError:
        # ascii 로케일(컴파일 바이너리) 대비 — 바이트로 직접 쓴다
        buf = getattr(stream, "buffer", None)
        if buf is not None:
            buf.write((text + "\n").encode("utf-8", "replace"))
            buf.flush()
    return True
