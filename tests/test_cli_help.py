# CLI --help 엔진과 도구별 카탈로그(사례가 실제 파서로 그대로 읽히는지)를 검증하는 회귀 시험
"""
실행: venv312/bin/python tests/test_cli_help.py

  [엔진]  검색·렌더·argv 가로채기·ascii 스트림
  [사본]  Runner/cli_help_engine.py == occProject/Generators/KooCLIHelp/engine.py (바이트 동일)
  [KMM]   32 모드 전부 카탈로그에 있음 + 각 사례를 ImportOption 으로 파싱해 verify 기대치 확인
"""
import contextlib
import io
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
sys.path.insert(0, str(GEN))

from KooCLIHelp import engine as E  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print("  %-70s %s" % (name[:70], "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


# ── 엔진 ────────────────────────────────────────────────────────
def test_engine():
    print("[엔진]")
    cat = E.Catalog("Tool", "설명", ["Tool x"], modes=[
        E.Mode("DROP_ATTITUDE", "낙하 덱", aliases=["drop", "낙하"], keys=[E.Key("Height", "실수", "-", "높이")],
               examples=[E.Example("기본", "*Inputfile\nm.k\n*End")]),
        E.Mode("DROP_WEIGHT_IMPACT_TEST", "낙추 충격", aliases=["impact"]),
        E.Mode("TRANSFORM", "이동 회전", aliases=["rotate"]),
    ], topics=[E.Topic("format", "파일 구조", ["본문줄"], aliases=["형식"])])

    out = E.render_query(cat, "drop_attitude")
    check("정확 이름 → 상세 + 사례 복사 표시", "DROP_ATTITUDE — 낙하 덱" in out and "그대로 복사" in out)
    out = E.render_query(cat, "낙하")
    check("한글 별칭 → 상세", "DROP_ATTITUDE — 낙하 덱" in out)
    out = E.render_query(cat, "Drop-Attitude")
    check("구분자·대소문자 무시", "DROP_ATTITUDE — 낙하 덱" in out)
    out = E.render_query(cat, "drop")
    check("별칭 완전일치가 부분일치보다 우선", out.startswith("=") and "DROP_ATTITUDE — " in out)
    out = E.render_query(cat, "height")
    check("키 이름으로 검색", "DROP_ATTITUDE" in out)
    out = E.render_query(cat, "형식")
    check("주제 별칭", "format — 파일 구조" in out and "본문줄" in out)
    out = E.render_query(cat, "없는것")
    check("못 찾으면 목록 안내", "없습니다" in out and "TRANSFORM" in out)
    out = E.render_query(cat, "all")
    check("all = 전체 상세", out.count("=" * 78) >= 8)

    buf = io.StringIO()
    check("일반 인자는 가로채지 않음", E.handle_help(["t", "opt.txt"], cat, buf) is False and buf.getvalue() == "")
    check("인자 없음 기본은 가로채지 않음", E.handle_help(["t"], cat, buf) is False)
    check("no_args_is_help", E.handle_help(["t"], cat, buf, no_args_is_help=True) and "사용법" in buf.getvalue())
    for flag in ("--help", "-h", "help"):
        b = io.StringIO()
        check(f"{flag} → 개요", E.handle_help(["t", flag], cat, b) and "DROP_ATTITUDE" in b.getvalue())
    b = io.StringIO()
    E.handle_help(["t", "--help", "rotate"], cat, b)
    check("--help <검색어>", "TRANSFORM — 이동 회전" in b.getvalue())

    raw = io.BytesIO()
    ascii_stream = io.TextIOWrapper(raw, encoding="ascii")
    E.handle_help(["t", "--help"], cat, ascii_stream)
    check("ascii 스트림에서도 UTF-8 바이트로 출력", "낙하 덱".encode() in raw.getvalue())

    wide = E._wrap_table([["가나", "x"]], ["키", "설명"])
    col = lambda line, s: E._disp_len(line[:line.index(s)])  # noqa: E731
    check("한글 폭 정렬 (표시 칸 기준)", col(wide[0], "설명") == col(wide[2], "x"), str(wide))


def test_copy():
    print("[사본]")
    a = (GEN / "KooCLIHelp" / "engine.py").read_bytes()
    b = (ROOT / "Runner" / "cli_help_engine.py").read_bytes()
    check("Runner/cli_help_engine.py 바이트 동일", a == b)


# ── 사례 검증 ───────────────────────────────────────────────────
_MISSING = object()


def _get(obj, path):
    cur = obj
    for seg in path.split("."):
        if isinstance(cur, dict):
            if seg in cur:
                cur = cur[seg]
            elif seg.lstrip("-").isdigit() and int(seg) in cur:
                cur = cur[int(seg)]
            else:
                return _MISSING
        elif isinstance(cur, (list, tuple)) and seg.lstrip("-").isdigit():
            i = int(seg)
            if -len(cur) <= i < len(cur):
                cur = cur[i]
            else:
                return _MISSING
        else:
            return _MISSING
    return cur


def verify_expect(label, opt, expect):
    for key, want in expect.items():
        if key == "@list":
            got = opt
        elif key.startswith("@len:"):
            v = _get(opt, key[5:])
            got = len(v) if v is not _MISSING else _MISSING
        else:
            got = _get(opt, key)
        check(f"{label} {key}", got == want, f"기대 {want!r} / 실제 {got!r}")


def test_kmm():
    print("[KMM]")
    from KooCLIHelp.kmm_catalog import CATALOG
    src = (GEN / "KooMeshModifier.py").read_text(encoding="utf-8")
    registered = set(re.findall(r'self\.modeList\.append\("([A-Z_]+)"\)', src))
    names = {m.name for m in CATALOG.modes}
    check(f"등록 모드 {len(registered)}개 전부 카탈로그에 있음", registered <= names, str(registered - names))
    check("카탈로그에 없는 모드 이름 없음", names <= registered, str(names - registered))
    for m in CATALOG.modes:
        check(f"{m.name} 사례 1개 이상", len(m.examples) >= 1)

    with contextlib.redirect_stdout(io.StringIO()):
        import KooMeshModifier as K
    for m in CATALOG.modes:
        for i, ex in enumerate(m.examples, 1):
            label = f"{m.name}#{i}"
            v = ex.verify
            if not v:
                check(f"{label} verify 있음", False)
                continue
            d = tempfile.mkdtemp(prefix="clihelp_")
            Path(d, "opt.txt").write_text(ex.text + "\n", encoding="utf-8")
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    g = K.KooMeshModifier()
                    g.SetCurrentDirectory(d)
                    g.ImportOption("opt.txt")
            except Exception as e:  # noqa: BLE001
                check(f"{label} 파싱", False, f"{type(e).__name__}: {e}")
                continue
            pairs = list(zip(g.modeList, g.modeIDList))
            check(f"{label} *Mode 등록 ({v['mode']},{v['id']})", (v["mode"], v["id"]) in pairs, str(pairs))
            check(f"{label} 모델 파일명 읽힘", bool(getattr(g, "inputFileName", "")))
            for mode_name, mid in pairs:
                check(f"{label} 블록 {mode_name},{mid} 파싱됨", mid in g.modeIDOption)
            verify_expect(label, g.modeIDOption.get(v["id"], {}), v["expect"])

    # 렌더 가능성
    for m in CATALOG.modes:
        out = E.render_query(CATALOG, m.name)
        check(f"{m.name} --help 상세 렌더", out.startswith("=") and m.name in out)
    for t in CATALOG.topics:
        check(f"주제 {t.name} 렌더", t.body[0] in E.render_query(CATALOG, t.name))


def main():
    test_engine()
    test_copy()
    test_kmm()
    print()
    if FAILS:
        print("FAIL %d 건" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
