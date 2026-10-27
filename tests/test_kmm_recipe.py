# KMM 옵션 파일 *Recipe 펼치기 회귀 시험 — 펼친 옵션 글이 MCP 와 바이트로 같은지·판 고르기·거절 꼴·*Recipe 없는 파일 그대로
"""
실행: venv312/bin/python tests/test_kmm_recipe.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

레시피는 MCP 운영 저장 함수(recipes.validate·save·retire)로 임시 등록소(STMC_RECIPES_DIR)에 만들고, 기대 옵션 글은
MCP 운영 함수(recipes.expand·stmc_tools._kmm_block_lines·_kmm_option_file)로 만든다. MCP 모듈 위치는 STMC_SHARED
(기본 KooSlurm 리포 dashboard/smarttwin_mcp/tools/_shared).
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = Path(os.environ.get("KMM_GEN", ROOT / "occProject" / "Generators"))
PY = str(ROOT / "venv312" / "bin" / "python")
KMM_CMD = [os.environ["KMM_BIN"]] if os.environ.get("KMM_BIN") else [PY, str(GEN / "KooMeshModifier.py")]
SHARED = Path(os.environ.get("STMC_SHARED", "/home/koopark/claude/KooSlurmInstallAutomationRefactory/dashboard/smarttwin_mcp/tools/_shared"))
BASE = Path(tempfile.mkdtemp(prefix="kmm_recipe_"))
STORE = BASE / "recipes"
os.environ["STMC_RECIPES_DIR"] = str(STORE)
ENV = dict(os.environ, PATH=str(ROOT / "venv312" / "bin") + ":" + os.environ.get("PATH", ""))
sys.path.insert(0, str(SHARED))
import recipes  # noqa: E402  (MCP 운영 모듈)
import stmc_tools  # noqa: E402
from stmc_exec import Bundle  # noqa: E402

FAILS = []
USER = "tester"
CHAIN = {"name": "shift_rigid", "tool": "kmm_chain", "summary": "파트 5 를 빼고 강체로 둔 뒤 x 로 옮긴다",
         "params": {"dx": {"type": "number", "description": "x 이동량", "default": 0.0, "minimum": -1000, "maximum": 1000}},
         "args": {"modes": [{"mode": "ELASTIC_TO_RIGID", "lines": ["*PIDExcept,5"]},
                            {"mode": "TRANSFORM", "options": {"Translation": "{{dx}},0,0"}}]}}
SINGLE = {"name": "shift_y", "tool": "kmm_transform", "summary": "모델을 y 로 옮긴다",
          "params": {"dy": {"type": "integer", "description": "y 이동량", "minimum": 0, "maximum": 100}},
          "args": {"options": {"Translation": "0,{{dy}},0"}}}
CNRB = {"name": "cnrb_ring", "tool": "kmm_convert_cnrb_to_solid", "summary": "CNRB 를 원통 솔리드로 — 원주 절점 수",
        "params": {"n": {"type": "number", "description": "원주 절점 수(정수 키에 수 매개변수)"}},
        "args": {"options": {"NumCircumNodes": "{{n}}"}}}
PTS = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]


def check(name, cond, detail=""):
    print("  %-72s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def deck():
    nodes = "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n" for i, (x, y, z) in enumerate(PTS))
    return ("*KEYWORD\n*NODE\n" + nodes + "*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1)
            + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3) + "*ELEMENT_SOLID\n"
            + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(1, 9)) + "\n*END\n")


def node_xyz(text):
    out, inside = {}, False
    for ln in text.splitlines():
        if ln.startswith("*"):
            inside = ln.upper().startswith("*NODE")
            continue
        if inside and ln.strip() and not ln.startswith("$"):
            out[int(ln[:8])] = (float(ln[8:24]), float(ln[24:40]), float(ln[40:56]))
    return out


def moved(text, dx, dy):
    got = node_xyz(text)
    return len(got) == 8 and all(abs(got[i + 1][0] - (x + dx)) < 1e-9 and abs(got[i + 1][1] - (y + dy)) < 1e-9
                                 and abs(got[i + 1][2] - z) < 1e-9 for i, (x, y, z) in enumerate(PTS))


def mcp_text(recipe, values):
    """MCP 가 같은 레시피·매개변수로 만들 stmc_options.txt."""
    args = recipes.expand(recipe["args"], values)
    index, b = stmc_tools._specs()["kmm_blocks"], Bundle(None)
    if recipe["tool"] == "kmm_chain":
        blocks = [(s["mode"], index[s["mode"]], stmc_tools._kmm_block_lines(s, b, s["mode"])) for s in args["modes"]]
    else:
        spec = stmc_tools._specs()["tools"][recipe["tool"]]
        blocks = [(spec["mode"], spec["block"], stmc_tools._kmm_block_lines(args, b, spec["mode"]))]
    return stmc_tools._kmm_option_file("model.k", blocks)


def run(name, opt):
    d = BASE / name
    d.mkdir()
    (d / "model.k").write_text(deck())
    (d / "opt.txt").write_text(opt)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=600, env=ENV)
    return d, r.returncode, r.stdout + r.stderr


def read(p):
    return p.read_text(errors="replace") if p.exists() else ""


def save(doc):
    return recipes.save(recipes.validate(doc), {"note": "시험", "result_dir": "/dev/null"}, USER)


def main():
    print(f"KMM={' '.join(KMM_CMD)}  BASE={BASE}")
    assert save(CHAIN)["version"] == 1 and save(SINGLE)["version"] == 1 and save(CNRB)["version"] == 1

    d, rc, log = run("chain", "*Inputfile\nmodel.k\n*Recipe,shift_rigid\ndx,7.5\n*End\n")
    check("kmm_chain 레시피(판 생략 → 판 1): rc 0", rc == 0, log[-800:])
    check("펼친 옵션 글 = MCP stmc_options.txt (바이트)", read(d / "opt_recipe.txt") == mcp_text(CHAIN, {"dx": 7.5}),
          repr(read(d / "opt_recipe.txt")))
    out = read(d / "model_etor_trans.k")
    check("강체화 + x 7.5 이동이 실제로 들어감", "*MAT_RIGID" in out and moved(out, 7.5, 0.0), out[:400])
    check("로그에 레시피 이름·판", "레시피 shift_rigid 판 1" in log, log[-800:])

    d, rc, log = run("single", "*Inputfile\nmodel.k\n*Recipe,shift_y,1\ndy,3\n*End\n")
    check("kmm_transform 레시피(판 1 지정, 정수 3): rc 0", rc == 0, log[-800:])
    check("펼친 옵션 글 = MCP (바이트)", read(d / "opt_recipe.txt") == mcp_text(SINGLE, {"dy": 3}), repr(read(d / "opt_recipe.txt")))
    check("y 3 이동", moved(read(d / "model_trans.k"), 0.0, 3.0), read(d / "model_trans.k")[:400])

    d, rc, log = run("default", "*Inputfile\nmodel.k\n*Recipe,shift_rigid\n$ dx 는 기본값 0.0\n*End\n")
    check("매개변수 기본값(dx 0.0): rc 0 · MCP 와 같음", rc == 0 and read(d / "opt_recipe.txt") == mcp_text(CHAIN, {"dx": 0.0}),
          log[-600:])

    v2 = save({**SINGLE, "summary": "모델을 y 로 옮긴다(판 2)"})
    recipes.retire("shift_y", 2, "시험 — 판 2 내림", USER)
    d, rc, log = run("latest_active", "*Inputfile\nmodel.k\n*Recipe,shift_y\ndy,4\n*End\n")
    check("판 2 를 내리면 판 생략 시 판 1", v2["version"] == 2 and rc == 0 and "레시피 shift_y 판 1" in log, log[-600:])
    d, rc, log = run("retired_explicit", "*Inputfile\nmodel.k\n*Recipe,shift_y,2\ndy,4\n*End\n")
    check("내린 판 2 를 지정하면 알리고 그대로", rc == 0 and "내려진 판이다" in log and "레시피 shift_y 판 2" in log, log[-600:])

    d, rc, log = run("plain", "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,1,0,0\n**EndTransform\n*End\n")
    check("*Recipe 없는 옵션 파일: rc 0 · _recipe.txt 없음", rc == 0 and not (d / "opt_recipe.txt").exists()
          and moved(read(d / "model_trans.k"), 1.0, 0.0), log[-600:])

    d, rc, log = run("bom", "\ufeff*Recipe,shift_y,1\ndy,3\n*Inputfile\nmodel.k\n*End\n")
    check("UTF-8 BOM 이 붙은 첫 줄 *Recipe 도 펼친다(리뷰 R4): rc 0 · y 3 이동", rc == 0 and moved(read(d / "model_trans.k"), 0.0, 3.0),
          f"rc={rc} " + log[-500:])
    d, rc, log = run("preserve_pattern", "*Inputfile\nmodel.k\n*PreserveIncludes\nsub*model.k\n*Recipe,shift_y,1\ndy,3\n*End\n")
    check("*PreserveIncludes 패턴 줄 sub*model.k 는 *Mode 충돌이 아니다(리뷰 R6): rc 0 · y 3 이동",
          rc == 0 and moved(read(d / "model_trans.k"), 0.0, 3.0), f"rc={rc} " + log[-500:])
    for tag, opt in (("nbsp", "*Inputfile\nmodel.k\n\u00a0*Recipe,shift_y,1\ndy,3\n*End\n"),
                     ("ideo", "*Inputfile\nmodel.k\n\u3000*Recipe,shift_y,1\ndy,3\n*End\n"),
                     ("zwsp", "*Inputfile\nmodel.k\n\u200b*Recipe,shift_y,1\ndy,3\n*End\n"),
                     ("cr_only", "*Inputfile\rmodel.k\r*Recipe,shift_y,1\rdy,3\r*End\r"),
                     ("lrm", "*Inputfile\nmodel.k\n\u200e*Recipe,shift_y,1\ndy,3\n*End\n"),
                     ("zwj_shy", "*Inputfile\nmodel.k\n\u200d\u00ad*Recipe,shift_y,1\ndy,3\n*End\n")):
        d, rc, log = run("ws_" + tag, opt)
        check(f"*Recipe 줄머리 {tag}(리뷰 S3): 펼쳐서 y 3 이동 · rc 0", rc == 0 and moved(read(d / "model_trans.k"), 0.0, 3.0),
              f"rc={rc} " + log[-400:])
    d, rc, log = run("vt_comment", "*Inputfile\nmodel.k\n$ note\x0b*Recipe,shift_y\n*Mode\nTRANSFORM,1\n**Transform,1\n"
                     "Translation,1,0,0\n**EndTransform\n*End\n")
    check("주석 안 \\x0b 뒤 *Recipe 는 레시피 줄이 아니다 — 보통 옵션 파일 그대로(리뷰 T)", rc == 0 and moved(read(d / "model_trans.k"), 1.0, 0.0)
          and not (d / "opt_recipe.txt").exists(), f"rc={rc} " + log[-400:])
    d, rc, log = run("schema_int_ok", "*Inputfile\nmodel.k\n*Recipe,cnrb_ring\nn,16\n*End\n")
    check("정수 키에 16: 스키마 통과(펼침)", "레시피 cnrb_ring 판 1" in log and "이어야 한다" not in log, log[-500:])

    # 손으로 고친 판(해시 다름)·후처리 레시피(해시는 맞음)
    tdir = STORE / "tampered_rcp"
    tdir.mkdir()
    (tdir / "1.yaml").write_text((STORE / "shift_rigid" / "1.yaml").read_text(encoding="utf-8")
                                 .replace("name: shift_rigid", "name: tampered_rcp").replace("PIDExcept,5", "PIDExcept,6"),
                                 encoding="utf-8")
    post = recipes.validate({"name": "peak_table", "tool": "post_custom_report", "summary": "파트별 최대 응력 표",
                             "params": {"top": {"type": "integer", "description": "몇 개", "default": 5}},
                             "args": {"config": {"sections": [{"kind": "table", "top": "{{top}}"}]}}})
    recipes.save(post, {"note": "시험"}, USER)

    for nm, args in (("lines_str", {"lines": "Translation,0,1,0"}), ("options_list", {"options": []})):
        doc = {**recipes.load("shift_y", 1), "name": nm, "args": args, "params": {}}
        doc["sha256"] = recipes._sha(doc)               # 등록소에 손으로 쓴 판(해시는 맞음 — 서명은 아니다)
        (STORE / nm).mkdir()
        recipes._write(STORE / nm / "1.yaml", doc)
    head = "*Inputfile\nmodel.k\n"
    bad = [
        ("unknown", head + "*Recipe,shift_rigid\ndx,1\ndz,2\n*End\n", "모르는 매개변수"),
        ("missing", head + "*Recipe,shift_y,1\n*End\n", "값이 필요"),
        ("maximum", head + "*Recipe,shift_y,1\ndy,500\n*End\n", "maximum"),
        ("type", head + "*Recipe,shift_rigid\ndx,far\n*End\n", "number"),
        ("integer", head + "*Recipe,shift_y,1\ndy,3.5\n*End\n", "integer"),
        ("notfound", head + "*Recipe,no_such_recipe\n*End\n", "없다"),
        ("noversion", head + "*Recipe,shift_y,9\ndy,1\n*End\n", "판 9 이 없다"),
        ("tampered", head + "*Recipe,tampered_rcp\ndx,1\n*End\n", "해시"),
        ("post", head + "*Recipe,peak_table\n*End\n", "KMM 에서 펼칠 수 없다"),
        ("with_mode", head + "*Recipe,shift_rigid\ndx,1\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,0,0,0\n**EndTransform\n*End\n",
         "함께 쓸 수 없다"),
        ("twice", head + "*Recipe,shift_rigid\ndx,1\n*Recipe,shift_y,1\ndy,1\n*End\n", "하나만"),
        ("badline", head + "*Recipe,shift_rigid\ndx 1\n*End\n", "이름,값"),
        ("end_before", head + "*End\n*Recipe,shift_y,1\ndy,3\n", "레시피대로 읽지 못했다"),
        ("lines_str", head + "*Recipe,lines_str\n*End\n", "lines 는 목록"),
        ("options_list", head + "*Recipe,options_list\n*End\n", "options 는 사전"),
        ("schema_int", head + "*Recipe,cnrb_ring\nn,16.5\n*End\n", "integer"),
    ]
    for name, opt, needle in bad:
        d, rc, log = run("bad_" + name, opt)
        check(f"거절 {name}: rc 1 · 🔴 *Recipe · '{needle}' · 출력 없음 · 입력 그대로",
              rc == 1 and "🔴 *Recipe" in log and needle in log and not list(d.glob("model_*.k"))
              and read(d / "model.k") == deck() or False, f"rc={rc} " + log[-500:])

    recipes.retire("shift_y", 1, "시험 — 판 1 도 내림", USER)
    d, rc, log = run("all_retired", head + "*Recipe,shift_y\ndy,1\n*End\n")
    check("모든 판을 내리면 판 생략은 거절", rc == 1 and "쓸 수 있는 판이 없다" in log, log[-500:])

    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
