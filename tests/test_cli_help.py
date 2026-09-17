# CLI --help 엔진과 도구별 카탈로그(사례가 실제 파서로 그대로 읽히는지)를 검증하는 회귀 시험
"""
실행: venv312/bin/python tests/test_cli_help.py

  [엔진]  검색·렌더·argv 가로채기·ascii 스트림
  [사본]  Runner/cli_help_engine.py == occProject/Generators/KooCLIHelp/engine.py (바이트 동일)
  [KMM]   32 모드 전부 카탈로그에 있음 + 각 사례를 ImportOption 으로 파싱해 verify 기대치 확인
  [KAM]   디스패치 모드 전부 카탈로그에 있음 + 사례를 PKG·CAP·ODB·AIRMESH 파서로 읽어 확인
  [KCR]   시나리오 사례를 prepare(Designer) → runner_config → 러너 step config → KMM 파싱까지 확인
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


def _same(a, b):
    import math
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and math.isclose(a, b, rel_tol=1e-9, abs_tol=0.0)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    return a == b


def _get(obj, path):
    cur = obj
    for seg in path.split("."):
        if not isinstance(cur, (dict, list, tuple)) and hasattr(cur, seg):
            cur = getattr(cur, seg)
            continue
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
        check(f"{label} {key}", _same(got, want), f"기대 {want!r} / 실제 {got!r}")


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


def test_kam():
    print("[KAM]")
    import shutil
    from KooCLIHelp.kam_catalog import CATALOG
    src = (GEN / "KooAutomatedModeller.py").read_text(encoding="utf-8")
    dispatch = set(re.findall(r'mode == "([A-Za-z]+)"', src)) - {"LSDYNADOE", "CAP"}
    names = {m.name for m in CATALOG.modes}
    check(f"디스패치 모드 {sorted(dispatch)} 전부 카탈로그에 있음", dispatch <= names, str(dispatch - names))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    with contextlib.redirect_stdout(io.StringIO()):
        from KooODBCADManager.PackageGenerator import PackageUserdefined
        from KooODBCADManager.Capacitor import CapacitorManager
        from KooODBCADManager.ODBCADManager import ODBCADManager
        from KooAirMesh.AirMeshGenerator import load_config
    golden = ROOT / "Examples" / "automatedmodeller" / "airmesh_sphere" / "sphere_cyl.stp"
    for m in CATALOG.modes:
        for i, ex in enumerate(m.examples, 1):
            label = f"{m.name}#{i}"
            v = ex.verify
            d = tempfile.mkdtemp(prefix="clihelp_kam_")
            name = "airmesh.json" if v["parser"] == "airmesh" else "input.txt"
            fn = os.path.join(d, name)
            Path(fn).write_text(ex.text + "\n", encoding="utf-8")
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    if v["parser"] == "pkg":
                        obj = PackageUserdefined()
                        obj.ImportPackage(fn)
                    elif v["parser"] == "cap":
                        obj = CapacitorManager()
                        obj.SetFolderPath(d)
                        obj.ImportCapacitor(fn)
                    elif v["parser"] == "odb":
                        obj = ODBCADManager()
                        obj.ImportModellingOptions(d, name)
                    elif v["parser"] == "airmesh":
                        shutil.copy(golden, d)
                        cfg, errors, warnings = load_config(fn)
                        obj = {"cfg": cfg, "errors": errors}
            except Exception as e:  # noqa: BLE001
                check(f"{label} 파싱", False, f"{type(e).__name__}: {e}")
                continue
            verify_expect(label, obj, v["expect"])
    for m in CATALOG.modes:
        check(f"{m.name} --help 상세 렌더", E.render_query(CATALOG, m.name).startswith("="))
    check("CAP 별칭 → CAPACITOR", "CAPACITOR — " in E.render_query(CATALOG, "CAP"))


def _box_model(path):
    # 2 파트 헥사 블록 (mm) — 위치 격자 자동 bbox 용
    n, h, lines, idx, nid = 4, 10.0, [], {}, 0
    for k in range(3):
        for j in range(n + 1):
            for i in range(n + 1):
                nid += 1
                idx[(i, j, k)] = nid
                lines.append(f"{nid:8d}{i * h - 20:16.6f}{j * h - 20:16.6f}{k * 1.0:16.6f}")
    elems, eid = [], 0
    for k in range(2):
        for j in range(n):
            for i in range(n):
                eid += 1
                c = [idx[(i, j, k)], idx[(i + 1, j, k)], idx[(i + 1, j + 1, k)], idx[(i, j + 1, k)],
                     idx[(i, j, k + 1)], idx[(i + 1, j, k + 1)], idx[(i + 1, j + 1, k + 1)], idx[(i, j + 1, k + 1)]]
                elems.append(f"{eid:8d}{k + 1:8d}" + "".join(f"{x:8d}" for x in c))
    f10 = lambda *v: "".join(f"{str(x):>10s}" for x in v)  # noqa: E731
    Path(path).write_text("\n".join(
        ["*KEYWORD", "*PART", "LOWER", f10(1, 1, 1), "*PART", "UPPER", f10(2, 1, 1),
         "*SECTION_SOLID", f10(1, 1), "*MAT_ELASTIC", f10(1, "7.85e-9", "200000.0", "0.3"), "*NODE"]
        + lines + ["*ELEMENT_SOLID"] + elems + ["*END"]) + "\n")


def _kv(text):
    kv = {}
    for line in text.splitlines():
        if "," in line and not line.startswith("*"):
            k, v = line.split(",", 1)
            kv[k.strip()] = v.strip()
    return kv


def _kmm_parse(label, cfg_path):
    with contextlib.redirect_stdout(io.StringIO()):
        import KooMeshModifier as K
        g = K.KooMeshModifier()
        g.SetCurrentDirectory(os.path.dirname(cfg_path))
        g.ImportOption(os.path.basename(cfg_path))
    ok = bool(g.modeList) and all(mid in g.modeIDOption for mid in g.modeIDList)
    check(f"{label} step config 를 KMM 이 파싱 ({list(zip(g.modeList, g.modeIDList))})", ok)


def test_kcr():
    print("[KCR]")
    import copy
    import json
    import logging
    sys.path.insert(0, str(ROOT))
    from Runner.cli_help_kcr import CATALOG
    from Runner import cli_help_kcr
    check("KooChainRun 카탈로그 엔진은 Runner 사본", cli_help_kcr.Catalog.__module__ == "Runner.cli_help_engine")
    src = (ROOT / "KooChainRun").read_text(encoding="utf-8")
    cmds = set(re.findall(r"add_parser\(\s*'(\w+)'", src))
    names = {m.name for m in CATALOG.modes}
    check(f"argparse 명령 {len(cmds)}개 전부 카탈로그에 있음", cmds <= names, str(cmds - names))
    with contextlib.redirect_stdout(io.StringIO()):
        from Runner.CumulativeDesigner import CumulativeDesigner
        from Runner.CumulativeScenarioRunner import CumulativeScenarioRunner
        from Runner import PartValidationWorkflow, DropWeightImpactWorkflow
    for m in CATALOG.modes:
        for i, ex in enumerate(m.examples, 1):
            label = f"{m.name}#{i}"
            v = ex.verify
            try:
                user = json.loads(ex.text)
            except ValueError as e:
                check(f"{label} JSON 유효", False, str(e))
                continue
            d = tempfile.mkdtemp(prefix="clihelp_kcr_")
            _box_model(os.path.join(d, "model.k"))
            scen_path = Path(d, "scenario.json")
            try:
                if v["kind"] == "cumulative":
                    cfg = copy.deepcopy(user)
                    cfg["base_dir"] = d
                    with contextlib.redirect_stdout(io.StringIO()):
                        des = CumulativeDesigner(cfg, scenario_dir=d)
                        rc = des.parse_user_config()
                        rc_path = os.path.join(d, "runner_config.json")
                        des.save_runner_config(rc, rc_path)
                    rcfg = json.load(open(rc_path, encoding="utf-8"))
                    sc = rcfg["scenario"]
                    check(f"{label} DOE 수 {v['doe_count']}", sc.get("doe_count") == v["doe_count"], str(sc.get("doe_count")))
                    modes = [s["mode"] for s in sc["steps"]]
                    check(f"{label} 스텝 모드 {v['modes']}", modes == v["modes"], str(modes))
                    for stepno, want in v.get("step_params", {}).items():
                        st = sc["steps"][int(stepno) - 1]
                        check(f"{label} step{stepno} params", all(st.get("params", {}).get(k) == w for k, w in want.items()),
                              str(st.get("params")))
                    if "step" in v:
                        out = os.path.join(d, "out")
                        os.makedirs(out, exist_ok=True)
                        rcfg["project"]["output_dir"] = out
                        r = CumulativeScenarioRunner.__new__(CumulativeScenarioRunner)
                        r.config, r.output_dir, r.run_id, r.input_dir = rcfg, out, "t", d
                        r._get_prev_run_dir = lambda doe, step: None
                        r._build_preserve_block = lambda: ""
                        step = sc["steps"][v["step"] - 1]
                        logging.disable(logging.CRITICAL)
                        try:
                            with contextlib.redirect_stdout(io.StringIO()):
                                cfg_path = r._create_step_config(1, step)
                        finally:
                            logging.disable(logging.NOTSET)
                        text = Path(cfg_path).read_text(encoding="utf-8")
                        kv = _kv(text)
                        for key, want in v["step_expect"].items():
                            check(f"{label} step config {key}={want}", kv.get(key) == want, f"실제 {kv.get(key)!r}")
                        _kmm_parse(label, cfg_path)
                elif v["kind"] == "drop_weight_impact":
                    scen_path.write_text(ex.text, encoding="utf-8")
                    with contextlib.redirect_stdout(io.StringIO()):
                        DropWeightImpactWorkflow.prepare_drop_weight_impact(user, scen_path, Path(d, "runner_config.json"))
                    man = json.load(open(os.path.join(d, user["output_dir"], "dwi_manifest.json"), encoding="utf-8"))
                    check(f"{label} 충격 위치 9개", man["total_cases"] == 9, str(man["total_cases"]))
                    _kmm_parse(label, os.path.join(d, user["output_dir"], "configs", "dwi_0001.txt"))
                elif v["kind"] == "part_validation":
                    class _Stop(Exception):
                        pass

                    def _no_kmm(*a, **k):
                        raise _Stop()
                    real = PartValidationWorkflow.subprocess.run
                    PartValidationWorkflow.subprocess.run = _no_kmm
                    try:
                        with contextlib.redirect_stdout(io.StringIO()):
                            PartValidationWorkflow.prepare_part_validation(user, scen_path, Path(d, "runner_config.json"))
                    except _Stop:
                        pass
                    finally:
                        PartValidationWorkflow.subprocess.run = real
                    cfg_path = os.path.join(d, user["output_dir"], "step_config_validation.txt")
                    check(f"{label} step config 생성", os.path.exists(cfg_path))
                    _kmm_parse(label, cfg_path)
            except SystemExit as e:
                check(f"{label} prepare", False, f"SystemExit {e.code}")
            except Exception as e:  # noqa: BLE001
                check(f"{label} prepare", False, f"{type(e).__name__}: {e}")
    for m in CATALOG.modes:
        check(f"{m.name} --help 상세 렌더", E.render_query(CATALOG, m.name).startswith("="))


def main():
    test_engine()
    test_copy()
    test_kmm()
    test_kam()
    test_kcr()
    print()
    if FAILS:
        print("FAIL %d 건" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
