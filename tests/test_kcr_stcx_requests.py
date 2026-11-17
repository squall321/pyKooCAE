#!/usr/bin/env python3
# KooChainRun stcx 요청서 v1.0(KC-01~KC-10) 판정 — 실제 정상 런 사본으로 만든 고장 런, 가짜 LS-DYNA·Slurm 으로 러너·명령을 본다
"""docs/kcr_stcx_requests_20261117 의 10건.

- 판정기(KC-02)는 이 기계의 실제 정상 런(Test_005, 있을 때)을 사본으로 떠 고장 낸다 — 정상 문구 없음·목표 미달·NaN·첫 KE 0·
  속도 31.6배 느림·에너지비 높음. 없으면 그 칸은 건너뛴다(SKIP).
- 러너 배선은 가짜 LS-DYNA(정상·고장 산출물을 복사하고 rc 0)로 — 고친 러너는 고장 런을 실패(rc 1)로, 옛 러너는 completed 로 본다.
- Slurm 은 부르지 않는다: sbatch·squeue·scontrol·sacct 는 PATH 앞의 가짜.
옛 코드로 볼 때: KCR_ROOT=<옛 트리(KooChainRun·Runner)> venv312/bin/python tests/test_kcr_stcx_requests.py
컴파일본으로 볼 때: KCR_BIN=<KooChainRun 실행 파일> … — 명령줄·러너·deep_report.sh 관문이 그 파일을 쓴다(모듈 판정은 소스)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOT = Path(os.environ.get("KCR_ROOT") or REPO)
sys.path.insert(0, str(ROOT))
TMP = Path(os.environ.get("KCR_TEST_TMP") or "/data/koopark/Test_kcr_stcx_20261117/tmp")
TMP.mkdir(parents=True, exist_ok=True)
REAL = Path("/data/koopark/Test_005_Fibonacci_100/output/Run_20260602_200105_01cc5f")
KCR_BIN = os.environ.get("KCR_BIN")
KCR_CMD = [KCR_BIN] if KCR_BIN else [sys.executable, str(ROOT / "KooChainRun")]
DWI = Path("/data/koopark/Test_reader_crashes_20261109/host_v136/tmp/v131r_dwi_cyl3_m9915kn0")
FAILS, SKIPS = [], []


def check(name, cond, detail=""):
    print("  %-104s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append(f"{name} {detail}"[:600])


def skip(name, why):
    print("  %-104s SKIP (%s)" % (name, why))
    SKIPS.append(name)


def try_(f, default=None):
    try:
        return f()
    except Exception as e:  # 옛 코드에서는 모듈·함수가 없다 — 판정이 FAIL 로 남게
        return default if default is not None else e


def tmpdir(tag):
    return Path(tempfile.mkdtemp(prefix=f"kcr_{tag}_", dir=str(TMP)))


# ── 정상 런 사본 ──────────────────────────────────────────────────────────
def fixture_run(tag, with_binout=False):
    """실제 정상 런의 작은 파일만 복사(d3plot·binout 은 빼거나 링크)."""
    d = tmpdir(tag) / "Run_fixture"
    (d / "Output").mkdir(parents=True)
    for n in ("DropSet.k", "DropSet.json", "step_config.txt"):
        shutil.copy2(REAL / n, d / n)
    for n in ("d3hsp", "mes0000", "glstat"):
        shutil.copy2(REAL / "Output" / n, d / "Output" / n)
    if with_binout:
        for b in REAL.joinpath("Output").glob("binout*"):
            os.symlink(b, d / "Output" / b.name)
    return d


def edit(path, fn):
    t = Path(path).read_text(encoding="utf-8", errors="replace")
    Path(path).write_text(fn(t), encoding="utf-8")


def evaluate(d, **kw):
    from Runner.RunHealth import evaluate_run
    kw.setdefault("use_binout", False)
    return evaluate_run(str(d), **kw)


# ═════════════════════════════════════════════════════════════════════════
def t_health():
    print("[KC-02] 정상 종료·건강 판정")
    if not REAL.is_dir():
        skip("KC-02 실제 정상 런 사본", f"{REAL} 없음")
        return
    d = fixture_run("good")
    H = try_(lambda: evaluate(d), {})
    check("정상 런 → valid(도달 = 덱 ENDTIM 0.005, 첫 KE ½mv² 와 0.1 % 안)", isinstance(H, dict) and H.get("verdict") == "valid",
          str(H)[:300] if not isinstance(H, dict) else str(H.get("reasons")))
    check("정상 런: 목표 시각 출처는 덱 ENDTIM, 단위계 mm-t-s, v_expected = √(2·9810·1500)",
          isinstance(H, dict) and H.get("target_end_time_source") == "덱 ENDTIM" and H.get("units") == "mm-t-s"
          and abs((H.get("v_expected") or 0) - 5424.94) < 0.1)

    d = fixture_run("nonormal")
    for n in ("d3hsp", "mes0000"):
        edit(d / "Output" / n, lambda t: t.replace("N o r m a l    t e r m i n a t i o n", "                                    "))
    H = try_(lambda: evaluate(d), {})
    check("정상 종료 문구 없음 → invalid", isinstance(H, dict) and H.get("verdict") == "invalid"
          and any("정상 종료" in r for r in H.get("invalid_reasons", [])), str(H)[:300])

    d = fixture_run("short")
    edit(d / "Output" / "d3hsp", lambda t: t.replace("Problem time       =    5.0000E-03", "Problem time       =    2.5000E-03"))
    H = try_(lambda: evaluate(d), {})
    check("도달 2.5e-3 < 덱 ENDTIM 5e-3(정상 문구는 있음 — 질량 증가 종료 꼴) → invalid",
          isinstance(H, dict) and H.get("verdict") == "invalid" and any("목표 시각" in r for r in H.get("invalid_reasons", [])))

    # 43 의 경우 — 종료 시간 표 ENDTIM 이 tFinal 보다 짧다(덱 ENDTIM 이 목표), 자릿수 많은 값의 출력 반올림
    d = fixture_run("tableshort")
    edit(d / "DropSet.k", lambda t: t.replace(" 5.000e-03  10000000", "4.12355e-3  10000000"))
    edit(d / "Output" / "d3hsp", lambda t: t.replace("Problem time       =    5.0000E-03", "Problem time       =    4.1235E-03"))
    H = try_(lambda: evaluate(d), {})
    check("표 ENDTIM 4.12355e-3(tFinal 5e-3 보다 짧음)·도달 4.1235E-03(반올림) → invalid 아님",
          isinstance(H, dict) and H.get("verdict") in ("valid", "warn") and abs((H.get("target_end_time") or 0) - 4.12355e-3) < 1e-12,
          str(H.get("reasons") if isinstance(H, dict) else H))
    d = fixture_run("tablelong")
    edit(d / "DropSet.k", lambda t: t.replace(" 5.000e-03  10000000", " 8.000e-03  10000000"))
    H = try_(lambda: evaluate(d), {})
    check("표 ENDTIM 8e-3(tFinal 보다 김)인데 5e-3 에서 끝남 → invalid", isinstance(H, dict) and H.get("verdict") == "invalid")

    d = fixture_run("nan")
    def _nan(t):                       # 줄 머리의 ' kinetic energy' 만(‘eroded kinetic energy’ 가 아니라)
        i = t.index("\n kinetic energy", len(t) // 2) + 1
        j = t.index("\n", i)
        return t[:i] + " kinetic energy.................         NaN" + t[j:]
    def _nan_eroded(t):
        i = t.index("\n eroded kinetic energy", len(t) // 2) + 1
        j = t.index("\n", i)
        return t[:i] + " eroded kinetic energy..........         NaN" + t[j:]
    edit(d / "Output" / "glstat", _nan)
    H = try_(lambda: evaluate(d), {})
    check("glstat 중간에 NaN → invalid(nan_onset 기록)", isinstance(H, dict) and H.get("verdict") == "invalid"
          and H.get("nan_onset") is not None)
    d = fixture_run("nan0")             # 첫 기록의 KE 가 NaN — health 의 ke0_measured 가 NaN 이 된다
    edit(d / "Output" / "glstat", lambda t: t.replace(" kinetic energy.................   2.65415E+03",
                                                       " kinetic energy.................         NaN", 1))
    H0 = try_(lambda: evaluate(d), {})
    RHm = __import__("Runner.RunHealth", fromlist=["x"])
    try_(lambda: RHm.write_health(str(d), H0))
    def _no_nan(x):
        raise ValueError(x)
    ok = try_(lambda: json.loads((d / "health.json").read_text(), parse_constant=_no_nan) is not None, False)
    check("[리뷰 하5] 첫 KE NaN 런의 health.json 에도 NaN·Infinity 가 없다(엄격한 JSON)·invalid",
          ok is True and isinstance(H0, dict) and H0.get("verdict") == "invalid", str(ok))
    d = fixture_run("nan2")
    edit(d / "Output" / "glstat", _nan_eroded)
    H = try_(lambda: evaluate(d), {})
    check("판정 표에 없는 항목(eroded kinetic energy)의 NaN 도 → invalid", isinstance(H, dict) and H.get("verdict") == "invalid")

    d = fixture_run("ke0")
    edit(d / "Output" / "glstat", lambda t: t.replace(" kinetic energy.................   2.65415E+03",
                                                       " kinetic energy.................   0.00000E+00", 1))
    H = try_(lambda: evaluate(d), {})
    check("첫 KE 0(볼드랍 11런 꼴) → invalid", isinstance(H, dict) and H.get("verdict") == "invalid"
          and any("첫 운동에너지가 0" in r for r in H.get("invalid_reasons", [])))

    d = fixture_run("slow")   # g 9.81 을 mm 덱에 쓴 속도 = 31.6배 느림 → KE 1/1000
    edit(d / "DropSet.k", lambda t: t.replace(" 5.369e+01 5.425e+03 1.153e+01", " 1.698e+00 1.716e+02 3.646e-01"))
    edit(d / "Output" / "glstat", lambda t: t.replace(" kinetic energy.................   2.65415E+03",
                                                       " kinetic energy.................   2.65415E+00", 1))
    H = try_(lambda: evaluate(d), {})
    check("속도 31.6배 느림(첫 KE 1/1000) → invalid", isinstance(H, dict) and H.get("verdict") == "invalid"
          and any("기대" in r for r in H.get("invalid_reasons", [])), str(H.get("reasons") if isinstance(H, dict) else H))

    d = fixture_run("ratio")
    edit(d / "Output" / "glstat", lambda t: t.replace(" total energy / initial energy..   1.00000E+00",
                                                       " total energy / initial energy..   1.10000E+00", 3))
    H = try_(lambda: evaluate(d), {})
    check("에너지비 1.10 > 1.05 → warn(invalid 아님)", isinstance(H, dict) and H.get("verdict") == "warn"
          and any("에너지비" in r for r in H.get("warn_reasons", [])))

    d = fixture_run("errline")
    edit(d / "Output" / "mes0000", lambda t: t + "\n *** Error 10087 (KEY+87)\n     test error line\n")
    H = try_(lambda: evaluate(d), {})
    check("정상 종료 + mes '*** Error' 줄 → warn, error_lines 기록", isinstance(H, dict) and H.get("verdict") == "warn"
          and H.get("error_lines"))

    d = fixture_run("nod3hsp")
    (d / "Output" / "d3hsp").unlink()
    (d / "Output" / "mes0000").unlink()
    H = try_(lambda: evaluate(d), {})
    check("d3hsp 없음 → invalid", isinstance(H, dict) and H.get("verdict") == "invalid")

    # 리뷰 상1 — 회전 속도가 있으면 첫 KE 에 회전분이 더해진다: ½mv² 비교를 하지 않는다(첫 KE 0 판정은 남는다)
    d = fixture_run("spin")
    edit(d / "step_config.txt", lambda t: t.replace("InitialAngularVelocityX,0", "InitialAngularVelocityX,12.5"))
    edit(d / "Output" / "glstat", lambda t: t.replace(" kinetic energy.................   2.65415E+03",
                                                       " kinetic energy.................   4.24664E+03", 1))
    H = try_(lambda: evaluate(d), {})
    check("[리뷰 상1] 초기 회전 속도 + 첫 KE 1.6배(회전분) → invalid 아님·비교 건너뜀 기록", isinstance(H, dict)
          and H.get("verdict") != "invalid" and H.get("ke0_compared") is False, str(H.get("reasons") if isinstance(H, dict) else H))
    edit(d / "Output" / "glstat", lambda t: t.replace(" kinetic energy.................   4.24664E+03",
                                                       " kinetic energy.................   0.00000E+00", 1))
    H = try_(lambda: evaluate(d), {})
    check("[리뷰 상1] 회전이 있어도 첫 KE 0 → invalid", isinstance(H, dict) and H.get("verdict") == "invalid")
    d = fixture_run("lumped")
    edit(d / "DropSet.k", lambda t: t.replace("*END", "*ELEMENT_MASS\n 9000001       1 1.000e-06       0\n*END", 1))
    edit(d / "Output" / "glstat", lambda t: t.replace(" kinetic energy.................   2.65415E+03",
                                                       " kinetic energy.................   4.24664E+03", 1))
    H = try_(lambda: evaluate(d), {})
    check("[리뷰 중5] 집중 질량(*ELEMENT_MASS) 덱 → ½mv² 비교 건너뜀(invalid 아님)", isinstance(H, dict)
          and H.get("verdict") != "invalid" and H.get("ke0_compared") is False)
    RH = __import__("Runner.RunHealth", fromlist=["x"])
    check("[리뷰 하1] '4.17160+258'(E 없는 세 자리 지수)·'1.0D-03' 를 읽는다", abs((RH._f("4.17160+258") or 0) / 4.1716e258 - 1) < 1e-9
          and RH._f("1.0D-03") == 1e-3)
    check("[리뷰 하2] \"health\": true(객체 아님) → 경고 뒤 무시(러너 생성자가 죽지 않는다)", RH.load_thresholds({"health": True}) == {}
          and RH.health_settings({"health": True}) == {})
    sc = tmpdir("modes") / "step_config.txt"
    sc.write_text("*Mode\nPART_TRANSLATE,1\nDROP_WEIGHT_IMPACT_TEST,2\n**PartTranslate,1\nX,1\n**EndPartTranslate\n*End\n")
    check("단계 설정 *Mode 에 PART_TRANSLATE 가 앞에 와도 주 모드 = DROP_WEIGHT_IMPACT_TEST", RH.parse_step_config(str(sc)).get("_mode")
          == "DROP_WEIGHT_IMPACT_TEST")

    # binout(Post SIF lasso) — 파트 IE 기록·캠페인 비교
    sif = "/opt/apptainers/SmartTwinPostprocessor.sif"
    if os.path.isfile(sif) and shutil.which("apptainer"):
        d = fixture_run("binout", with_binout=True)
        H = try_(lambda: evaluate(d, use_binout=True, post_sif=sif), {})
        check("binout: 파트 23개 IE 기록, 움직이는 파트 = matsum 첫 KE > 0(바닥판 23 빠짐), valid",
              isinstance(H, dict) and len(H.get("part_ie") or {}) == 23 and 23 not in (H.get("moving_parts") or [23])
              and H.get("verdict") == "valid", str(H.get("missing") if isinstance(H, dict) else H))
    else:
        skip("binout(Post SIF lasso)", "Post SIF·apptainer 없음")
    from_mod = try_(lambda: __import__("Runner.RunHealth", fromlist=["campaign_outliers"]).campaign_outliers)
    if callable(from_mod):
        Hs = [{"run_dir": f"r{i}", "verdict": "valid", "reference_energy": 2000.0,
               "part_ie": {"7": {"max": 371.0 + i}, "8": {"max": 50.0}}} for i in range(6)]
        Hs.append({"run_dir": "bad", "verdict": "valid", "reference_energy": 2000.0, "part_ie": {"7": {"max": 1346.0}, "8": {"max": 50.0}}})
        fl = from_mod(Hs)
        check("캠페인 비교: 파트 IE 1,346 대 중앙값 ~373 → 그 런만 warn 깃발", list(fl) == ["bad"], str(fl))
    else:
        check("캠페인 비교 함수", False, str(from_mod))


# ═════════════════════════════════════════════════════════════════════════
def t_provenance():
    print("[KC-01] 출처 기록·매니페스트")
    RP = try_(lambda: __import__("Runner.RunProvenance", fromlist=["x"]))
    if not hasattr(RP, "build_provenance"):
        check("RunProvenance 모듈", False, str(RP))
        return
    w = tmpdir("prov")
    rc = {"project": {"name": "P", "output_dir": str(w / "output"), "model_file": str(w / "model.k")},
          "environment": {}, "postprocess": {"enabled": True, "deep_extra_args": ["--parts", "1"]}}
    (w / "output").mkdir()
    (w / "model.k").write_text("*KEYWORD\n*END\n")
    cp = w / "runner_config.json"
    cp.write_text(json.dumps(rc))
    sc = w / "scenario.json"
    sc.write_text('{"x": 1}')
    RP.write_prepare_record(str(cp), str(sc))
    cfg, snap = RP.read_config_bytes(str(cp))
    import hashlib
    check("읽은 바이트 sha256 = 파일 sha256", snap.sha256 == hashlib.sha256(cp.read_bytes()).hexdigest())
    snap.save(str(w / "output"))
    check("사본 .kcr_config_snapshots/<sha>.json 한 번", (w / "output" / ".kcr_config_snapshots" / f"{snap.sha256}.json").is_file())
    rd = w / "output" / "Run_a"
    rd.mkdir()
    deck = rd / "DropSet.k"
    deck.write_text("*KEYWORD\n*NODE\n       1     0.0     0.0     0.0\n*END\n")
    os.environ["KCR_WRAPPER_NAME"] = "wrapX"
    try:
        P = RP.build_provenance(str(rd), cfg, snap, str(deck), doe=3, step=1, alias="P_DOE003", mode="DROP",
                                campaign_dir=str(w / "output"))
    finally:
        os.environ.pop("KCR_WRAPPER_NAME", None)
    check("provenance: 래퍼 이름(KCR_WRAPPER_NAME)·설정 sha·덱 sha·DOE·deep 플래그·scenario sha(prepare 기록)",
          P["wrapper_name"] == "wrapX" and P["runner_config_sha256"] == snap.sha256
          and P["deck_sha256"] == hashlib.sha256(deck.read_bytes()).hexdigest() and P["doe"] == 3
          and P["deep_report_flags"] == ["--parts", "1"] and P["scenario_sha256"] == hashlib.sha256(sc.read_bytes()).hexdigest(),
          json.dumps({k: P.get(k) for k in ("wrapper_name", "scenario_sha256", "missing")}, ensure_ascii=False))
    check("provenance 칸 이름 = DF-02(모두 있음, 모르면 null)", all(k in P for k in RP.PROVENANCE_FIELDS),
          str([k for k in RP.PROVENANCE_FIELDS if k not in P]))
    RP.write_provenance(str(rd), RP.finish_provenance(P, status="completed"))
    # 두 번째 런 — 다른 래퍼
    rd2 = w / "output" / "Run_b"
    rd2.mkdir()
    (rd2 / "DropWeightImpactTestSet.k").write_text(deck.read_text())
    P2 = RP.build_provenance(str(rd2), cfg, snap, str(rd2 / "DropWeightImpactTestSet.k"), doe=4, step=1, alias="P_DOE004",
                             mode="IMPACT", campaign_dir=str(w / "output"))
    P2["wrapper_name"] = "wrapY"
    RP.write_provenance(str(rd2), RP.finish_provenance(P2, status="completed"))
    rows = RP.build_manifest(json.loads(cp.read_text()))
    head = rows[0]
    check("매니페스트 머리: 런 2·래퍼별 수(wrapX 1·wrapY 1)·래퍼 둘이라 note", head["runs"] == 2
          and head["by_wrapper"] == {"wrapX": 1, "wrapY": 1} and head.get("note"), str(head))
    by = {r["run_key"]: r for r in rows[1:]}
    check("매니페스트 줄: analysis_method ANL-DROP·ANL-PARTIAL_IMPACT, deck_element_count",
          by.get("P_DOE003", {}).get("analysis_method") == "ANL-DROP" and by.get("P_DOE004", {}).get("analysis_method") == "ANL-PARTIAL_IMPACT"
          and by.get("P_DOE003", {}).get("deck_element_count") == 0, str({k: (v.get("analysis_method"), v.get("deck_element_count")) for k, v in by.items()}))


# ═════════════════════════════════════════════════════════════════════════
def report_files(rd, result=True, analysis=True, truncate=None):
    rp = rd / "Output" / "report"
    rp.mkdir(parents=True, exist_ok=True)
    if result:
        (rp / "result.json").write_text(json.dumps({"peak": 1.0}))
    if analysis:
        (rp / "analysis_result.json").write_text(json.dumps({"parts": list(range(100))}))
    if truncate:
        p = rp / truncate
        p.write_text(p.read_text()[:-5])


def gate_run(tag):
    d = tmpdir(tag) / "Run_g"
    (d / "Output").mkdir(parents=True)
    for n in ("d3plot", "d3plot01", "d3plot02"):
        (d / "Output" / n).write_bytes(b"\0" * 4096)
    (d / "step_config.txt").write_text("*Mode\nDROP_ATTITUDE,1\n")
    return d


def t_gate():
    print("[KC-03] 삭제 전 추출·d3plot 삭제 관문")
    G = try_(lambda: __import__("Runner.D3plotGate", fromlist=["x"]))
    if not hasattr(G, "gate_and_delete"):
        check("D3plotGate 모듈", False, str(G))
        return
    d = gate_run("norep")
    X = G.gate_and_delete(str(d), {"postprocess": {}})
    check("리포트 없음 → 지우지 않음(d3plot 3개 그대로)·extraction.json 에 까닭", X["d3plot_retained"]
          and len(list((d / "Output").glob("d3plot*"))) == 3 and (d / "extraction.json").is_file()
          and any("리포트" in r for r in X["retained_reasons"]))
    d = gate_run("trunc")
    report_files(d, truncate="analysis_result.json")
    X = G.gate_and_delete(str(d), {"postprocess": {}})
    check("analysis_result.json 잘림 → 지우지 않음", X["d3plot_retained"] and len(list((d / "Output").glob("d3plot*"))) == 3)
    RH = __import__("Runner.RunHealth", fromlist=["x"])
    keep = RH.FULL_PARSE_MAX_BYTES
    RH.FULL_PARSE_MAX_BYTES = 8           # '큰 파일' 흉내 — 머리·끝 바이트만 본다
    try:
        d = gate_run("bigtrunc")
        report_files(d)
        (d / "Output" / "report" / "analysis_result.json").write_text('{"a": {"b": 1}')   # 끝은 '}' 인데 잘렸다
        quick = RH.report_status(str(d / "Output"))["complete"]
        X = G.gate_and_delete(str(d), {"postprocess": {}})
    finally:
        RH.FULL_PARSE_MAX_BYTES = keep
    check("[리뷰 중4] 큰 JSON 이 끝만 '}' 로 잘림: 머리·끝 판정은 놓치지만 삭제 관문은 끝까지 읽어 보존", quick is True and X["d3plot_retained"])
    d = gate_run("req")
    report_files(d)
    spec = {"postprocess": {"required_extractions": [{"name": "board_strain", "outputs": ["extract/board_strain.npz"]}]}}
    X = G.gate_and_delete(str(d), spec)
    check("필수 추출 산출물 없음 → 지우지 않음", X["d3plot_retained"] and any("board_strain" in r for r in X["retained_reasons"]))
    spec["postprocess"]["required_extractions"][0]["command"] = "mkdir -p {output_dir}/extract && printf x > {output_dir}/extract/board_strain.npz"
    X = G.gate_and_delete(str(d), spec)
    check("필수 추출 명령을 돌려 산출물이 생기면 → 지움(d3plot 0개·deleted_at·지운 크기)", not X["d3plot_retained"]
          and not list((d / "Output").glob("d3plot*")) and X["deleted_at"] and X["d3plot_bytes"] == 3 * 4096
          and "board_strain" in X["fields_extracted"])
    check("지운 뒤에도 result.json·analysis_result.json·step_config.txt 그대로",
          (d / "Output" / "report" / "result.json").is_file() and (d / "Output" / "report" / "analysis_result.json").is_file()
          and (d / "step_config.txt").is_file())
    d = gate_run("clear")
    report_files(d)
    cf = d.parent / "clear.json"
    cf.write_text(json.dumps({"runs": ["other"]}))
    cfg = {"postprocess": {"deletion_clearance": {"file": str(cf)}}}
    X = G.gate_and_delete(str(d), cfg, run_key="mine")
    check("삭제 허가 목록에 없음 → 지우지 않음", X["d3plot_retained"])
    cf.write_text(json.dumps({"runs": ["mine"]}))
    X = G.gate_and_delete(str(d), cfg, run_key="mine")
    check("삭제 허가 목록에 있음 → 지움", not X["d3plot_retained"])
    d = gate_run("reqclr")
    report_files(d)
    X = G.gate_and_delete(str(d), {"postprocess": {}}, require_clearance=True)
    check("--require-clearance 인데 허가 설정 없음 → 지우지 않음", X["d3plot_retained"])
    d = gate_run("hinv")
    report_files(d)
    (d / "health.json").write_text(json.dumps({"verdict": "invalid"}))
    X = G.gate_and_delete(str(d), {"postprocess": {}})
    check("health invalid → 지우지 않음", X["d3plot_retained"])
    # 캠페인 안 runner_config 값 비교(형제 폴더)
    c = tmpdir("consist")
    for name, v in (("R1", True), ("R2", True), ("R3", False)):
        (c / name).mkdir()
        (c / name / "runner_config.json").write_text(json.dumps({"postprocess": {"delete_d3plot_after_deep": v}}))
    dc = G.delete_consistency(str(c / "R1" / "runner_config.json"))
    check("형제 폴더 runner_config 의 delete_d3plot_after_deep 이 다르면 inconsistent", not dc["consistent"]
          and len(dc["values"].get("false", [])) == 1, str(dc))


# ═════════════════════════════════════════════════════════════════════════
def fake_bin(tag, deep_writes=("result.json", "analysis_result.json"), help_opts=("--parts", "--no-section-view-per-part")):
    """가짜 apptainer — 'exec … python3 -m koo_deep_report RUN -o REPORT …' 이면 REPORT 에 deep_writes 를 쓰고 인자를 남긴다."""
    b = tmpdir(tag) / "bin"
    b.mkdir()
    writes = " ".join(deep_writes)
    opts = "\\n".join(f"  {o}" for o in help_opts)
    (b / "apptainer").write_text(f"""#!/bin/bash
args="$*"
echo "$args" >> "$(dirname "$0")/apptainer.calls"
if [[ "$args" == *"--help"* ]]; then printf 'usage: koo_deep_report\\n{opts}\\n'; exit 0; fi
for ((i=1; i<=$#; i++)); do if [ "${{!i}}" = "-c" ]; then j=$((i+1)); code="${{!j}}"; shift $j; exec python3 -c "$code" "$@"; fi; done
out=""; prev=""
for a in "$@"; do if [ "$prev" = "-o" ]; then out="$a"; fi; prev="$a"; done
if [ -n "$out" ]; then mkdir -p "$out"; for f in {writes}; do echo '{{"ok": true}}' > "$out/$f"; done; fi
exit 0
""")
    os.chmod(b / "apptainer", 0o755)
    return b


def run_sh(sh_text, rd, binp):
    p = rd / "deep_report.sh"
    p.write_text(sh_text)
    env = dict(os.environ, PATH=f"{binp}:{os.environ['PATH']}")
    r = subprocess.run(["bash", str(p)], capture_output=True, text=True, env=env, cwd=str(rd))
    return r


def t_deep_sh():
    print("[KC-02·03·05] deep_report.sh — 빈 리포트 rc 3·삭제 관문·프로필(가짜 apptainer)")
    from Runner.PostprocessShellGenerator import build_deep_report_sh
    sif = TMP / "fake.sif"
    sif.write_text("x")
    kcr = " ".join(KCR_CMD)
    # 빈 리포트 → 3
    d = gate_run("empty")
    b = fake_bin("empty", deep_writes=())
    r = run_sh(try_(lambda: build_deep_report_sh(str(d / "Output"), str(sif), {}), ""), d, b)
    check("도구가 0 인데 리포트 JSON 없음 → deep_report.sh rc 3", r.returncode == 3, f"rc={r.returncode} {r.stderr[-200:]}")
    d = gate_run("onefile")
    b = fake_bin("onefile", deep_writes=("analysis_result.json",))
    r = run_sh(try_(lambda: build_deep_report_sh(str(d / "Output"), str(sif), {"delete_d3plot_after_deep": True},
                                                kcr_cmd=kcr), ""), d, b)
    check("옛 SIF 처럼 analysis_result.json 하나만 → rc 0(성공), 그러나 d3plot 은 보존(삭제는 둘 다 완결일 때만)",
          r.returncode == 0 and len(list((d / "Output").glob("d3plot*"))) == 3, f"rc={r.returncode} {r.stderr[-300:]}")
    d = gate_run("trunc1")
    b = fake_bin("trunc1", deep_writes=("result.json", "analysis_result.json"))
    sh = try_(lambda: build_deep_report_sh(str(d / "Output"), str(sif), {}), "")
    sh = sh.replace('# 도구가 0 으로 끝나도', 'printf "{\\"x\\": 1" > "$REPORT_DIR/analysis_result.json"\n# 도구가 0 으로 끝나도', 1)
    r = run_sh(sh, d, b)
    check("하나라도 잘림(analysis_result.json 이 '}' 없이 끝남) → rc 3", r.returncode == 3, f"rc={r.returncode} {r.stderr[-200:]}")
    # 리포트 있음 + 삭제 켬 + 관문(KooChainRun d3plot-delete)
    d = gate_run("del")
    b = fake_bin("del")
    sh = try_(lambda: build_deep_report_sh(str(d / "Output"), str(sif), {"delete_d3plot_after_deep": True},
                                          kcr_cmd=kcr, config_path=None, run_key="RK"), "")
    check("삭제 켬 + 관문 명령: 스크립트에 'd3plot-delete' 가 있고 조건 없는 rm 은 없다",
          isinstance(sh, str) and "d3plot-delete" in sh and 'rm -f "$RUN_DIR"/d3plot' not in sh)
    r = run_sh(sh, d, b)
    check("리포트 완결 → rc 0, 관문이 d3plot 을 지우고 extraction.json(run_key RK)", r.returncode == 0
          and not list((d / "Output").glob("d3plot*")) and json.loads((d / "extraction.json").read_text()).get("run_key") == "RK",
          f"rc={r.returncode} {r.stdout[-300:]} {r.stderr[-300:]}")
    # 관문 명령 없이(DWI 틀) — 끝 바이트만 보고 지움
    d = gate_run("fallback")
    b = fake_bin("fallback")
    sh = try_(lambda: build_deep_report_sh(str(d / "Output"), str(sif), {"delete_d3plot_after_deep": True}), "")
    r = run_sh(sh, d, b)
    check("관문 명령 없음: 리포트 완결이면 JSON 을 끝까지 읽은 뒤 지움", r.returncode == 0 and not list((d / "Output").glob("d3plot*")))
    d = gate_run("fallback_trunc")
    b = fake_bin("fallback_trunc")
    sh2 = try_(lambda: build_deep_report_sh(str(d / "Output"), str(sif), {"delete_d3plot_after_deep": True}), "")
    sh2 = sh2.replace('# 도구가 0 으로 끝나도', 'printf "{\\"a\\": {\\"b\\": 1}" > "$REPORT_DIR/analysis_result.json"\n# 도구가 0 으로 끝나도', 1)
    r = run_sh(sh2, d, b)
    check("관문 명령 없음 + 끝만 '}' 로 잘린 JSON → rc 0 이어도 d3plot 보존(끝까지 읽기)", len(list((d / "Output").glob("d3plot*"))) == 3,
          f"rc={r.returncode} {r.stderr[-200:]}")
    # 프로필 — 도구가 아는 옵션만
    d = gate_run("prof")
    b = fake_bin("prof", help_opts=("--parts", "--no-section-view-per-part"))
    r = run_sh(try_(lambda: build_deep_report_sh(str(d / "Output"), str(sif), {"profile": "screening"}), ""), d, b)
    calls = (b / "apptainer.calls").read_text() if (b / "apptainer.calls").exists() else ""
    check("screening: 도구가 아는 --no-section-view-per-part 를 넘긴다", r.returncode == 0
          and any("koo_deep_report" in l and "--no-section-view-per-part" in l and "--help" not in l for l in calls.splitlines()), calls[-300:])
    d = gate_run("profold")
    b = fake_bin("profold", help_opts=("--parts",))
    r = run_sh(try_(lambda: build_deep_report_sh(str(d / "Output"), str(sif), {"profile": "screening"}), ""), d, b)
    calls = (b / "apptainer.calls").read_text() if (b / "apptainer.calls").exists() else ""
    check("screening + 옛 SIF(옵션 모름): 넘기지 않고 rc 0(빈 폴더 rc 2 가 아님)", r.returncode == 0
          and not any("--no-section-view-per-part" in l and "--help" not in l for l in calls.splitlines()), calls[-300:])
    sh0 = try_(lambda: build_deep_report_sh("/data/run", "/x.sif", {}), "")
    check("프로필 없음: 프로필 블록 없음(예전 플래그 그대로)", isinstance(sh0, str) and "DEEP_PROFILE" not in sh0
          and "--sv-threads 8" in sh0)


# ═════════════════════════════════════════════════════════════════════════
def t_budget():
    print("[KC-04] 디스크 예산")
    SB = try_(lambda: __import__("Runner.StorageBudget", fromlist=["x"]))
    if not hasattr(SB, "budget"):
        check("StorageBudget 모듈", False, str(SB))
        return
    w = tmpdir("budget")
    pilot = w / "Run_pilot"
    (pilot / "Output").mkdir(parents=True)
    (pilot / "Output" / "d3plot").write_bytes(b"\0" * (9 * 1024 * 1024))
    (pilot / "Output" / "binout0000").write_bytes(b"\0" * (1 * 1024 * 1024))
    (pilot / "health.json").write_text(json.dumps({"verdict": "valid"}))
    from collections import namedtuple
    U = namedtuple("U", "total used free")
    TOT = 100 * 1024 ** 4                 # 고정 사용량(공유 NFS 의 사용량은 시험 중에도 바뀐다)
    du = U(TOT, TOT // 2, TOT // 2)
    def th_for(room_bytes):            # 그 문턱 선까지 남은 칸이 room_bytes 가 되는 %
        return (du.used + room_bytes) / du.total * 100.0
    rc = {"project": {"output_dir": str(w)}, "scenario": {"doe_count": 1000, "total_steps": 1},
          "postprocess": {"delete_d3plot_after_deep": True}, "environment": {}}
    MB = 1024 * 1024
    B = SB.budget(rc, str(pilot), concurrency=10, backlog=10, threshold_pct=th_for(2000 * MB), fs_path=str(w), usage=du)
    check("삭제 켬: 1000 × 1 MB + 20 × 9 MB = 1.18 GB < 2 GB → pass", B["verdict"] == "pass", str(B["lines"][-2:]))
    B = SB.budget(rc, str(pilot), concurrency=200, backlog=10, threshold_pct=th_for(1500 * MB), fs_path=str(w), usage=du)
    check("삭제 켬·동시 200 → 넘침 → reduce_concurrency(넣을 수 있는 동시 수 제안)", B["verdict"] == "reduce_concurrency"
          and B["suggest_concurrency"] and 1 <= B["suggest_concurrency"] < 200, str(B["lines"][-3:]))
    rc2 = dict(rc, postprocess={"delete_d3plot_after_deep": False})
    B = SB.budget(rc2, str(pilot), concurrency=10, backlog=10, threshold_pct=th_for(2000 * MB), fs_path=str(w), usage=du)
    check("삭제 끔: 1000 × 10 MB 는 넘고 켜면 들어감 → enable_delete", B["verdict"] == "enable_delete", str(B["lines"][-2:]))
    B = SB.budget(rc, str(pilot), concurrency=10, backlog=10, threshold_pct=th_for(500 * MB), fs_path=str(w), usage=du)
    check("끝난 런만으로도 넘침 → reject", B["verdict"] == "reject")
    (pilot / "health.json").write_text(json.dumps({"verdict": "invalid"}))
    B = SB.budget(rc, str(pilot), concurrency=10, threshold_pct=th_for(2000 * MB), fs_path=str(w), usage=du)
    check("파일럿 health invalid → 정상 런 크기가 아닐 수 있다는 경고 줄", any("파일럿 health" in l for l in B["lines"]))
    e = try_(lambda: SB.budget(rc, str(w / "no_such_run"), concurrency=10, usage=du), None)
    check("[리뷰 하5] 없는 파일럿 → 오류(크기 0 으로 통과시키지 않음)", isinstance(e, ValueError), str(e))
    B = SB.budget(rc, str(pilot), backlog=0, threshold_pct=th_for(100000 * MB), fs_path=str(w), usage=du)
    check("[리뷰 중1] 동시 수를 모르면 런 수 전부로 본다(근거 줄)", B["concurrency"] == 1000 and any("동시 수를 모른다" in l for l in B["lines"]))
    # IMPACT 상태 수 비
    rci = dict(rc, simulation_params={"impact": {"dt": 1e-6, "tFinal": 1e-3}})
    B = SB.budget(rci, str(pilot), concurrency=10, backlog=10, threshold_pct=th_for(100000 * MB), fs_path=str(w),
                  pilot_config={"simulation_params": {"impact": {"dt": 1e-5, "tFinal": 1e-3}}}, usage=du)
    check("IMPACT dt 1e-5 → 1e-6(상태 10배) → d3plot 몫 10배", abs(B["pilot"]["d3plot_bytes"] - 9 * MB) < 1 and
          any("IMPACT 상태 수" in l for l in B["lines"]))


# ═════════════════════════════════════════════════════════════════════════
def campaign(tag, doe_count, mode="DROP", pp=True, positions=None):
    """가짜 캠페인 — runner_config·index(DOE 별 런 기록). 런 폴더는 따로 만든다."""
    w = tmpdir(tag)
    out = w / "output"
    out.mkdir()
    steps = [{"step": 1, "mode": mode, "condition": "C"}]
    rc = {"project": {"name": "Pj", "output_dir": str(out), "index_file": str(out / "simulation_index.json"),
                      "model_file": str(w / "model.k")},
          "scenario": {"id": "S1", "name": "S", "doe_count": doe_count, "total_steps": 1, "steps": steps},
          "execution": {"checkpoint_file": str(out / "checkpoint.json"), "retry_on_failure": True, "max_retries": 2,
                        "timeout_dynain_seconds": 30},
          "environment": {"koomeshmodifier_path": "/bin/false", "lsdyna_path": "/bin/false", "ncpu": 1,
                          "use_local_scratch": False, "apptainer_tmpdir": str(w / "apptmp")}}
    if pp:
        rc["postprocess"] = {"enabled": True, "auto_deep": True}
    if positions:
        rc["scenario"]["doe_positions"] = positions
    (w / "runner_config.json").write_text(json.dumps(rc))
    return w, out, rc


def write_index(out, runs):
    (out / "simulation_index.json").write_text(json.dumps({"scenarios": [{"runs": runs, "status": "in_progress"}]}))


def alias(rc, doe):
    return f"{rc['project']['name']}_CUM001_DOE{doe:03d}_S001_{rc['scenario']['steps'][0]['mode']}_C"


def t_status():
    print("[KC-06] 완료 집계 표")
    CS = try_(lambda: __import__("Runner.CampaignStatus", fromlist=["x"]))
    if not hasattr(CS, "campaign_status"):
        check("CampaignStatus 모듈", False, str(CS))
        return
    w, out, rc = campaign("status", 6)
    runs = {}
    def mk(doe, status, health=None, rep=None, deleted=False, pp=None):
        f = f"Run_{doe}"
        (out / f / "Output").mkdir(parents=True)
        runs[alias(rc, doe)] = {"status": status, "folder": f, **({"health": health} if health else {}),
                                **({"postprocess": pp} if pp else {}),
                                "started_at": "2026-11-17T01:00:00", "completed_at": "2026-11-17T01:30:00"}
        if rep == "ok":
            report_files(out / f)
        elif rep == "trunc":
            report_files(out / f, truncate="analysis_result.json")
        if deleted:
            (out / f / "extraction.json").write_text(json.dumps({"deleted_at": "2026-11-17T02:00:00"}))
    mk(1, "completed", "valid", rep="ok")
    mk(2, "completed", "valid")
    mk(3, "failed", "invalid")
    mk(5, "completed", "warn", rep="ok", deleted=True)
    mk(6, "completed", "valid", rep="trunc", pp={"rc": 3})
    mk(7, "completed", "valid")
    (out / "Run_7" / "Output" / "report").mkdir(parents=True)
    (out / "Run_7" / "Output" / "report" / "analysis_result.json").write_text("{}")
    rc["scenario"]["doe_count"] = 7
    write_index(out, runs)
    st = CS.campaign_status(rc, None, query_slurm=False)
    states = {r["doe"]: r["state"] for r in st["rows"]}
    check("DOE1 report_done·2 report_wait·3 invalid·4 norun·5 deleted·6 report_failed·7 report_done(파일 하나 — 옛 SIF)",
          states == {1: "report_done", 2: "report_wait", 3: "invalid", 4: "norun", 5: "deleted", 6: "report_failed",
                     7: "report_done"}, str(states))
    check("해석 끝 5 · 리포트 끝 3 → 후처리 대기 2", st["solver_done"] == 5 and st["report_done"] == 3 and st["report_backlog"] == 2,
          str((st["solver_done"], st["report_done"], st["report_backlog"])))
    p = CS.write_csv(st, str(out / "doe_status.csv"))
    check("doe_status.csv 머리·7줄", Path(p).read_text().splitlines()[0].startswith("doe,step,alias,state") and
          len(Path(p).read_text().splitlines()) == 8)
    # rerun 대상 — 후처리만 실패(rc 3)한 DOE 는 JobManager 가 completed 로 본다(해석을 다시 돌리지 않는다)
    from Runner.JobManager import JobManager
    (w / "jobs.json").write_text(json.dumps({"jobs": {"6": {"job_id": "999999991"}}}))
    jm = JobManager(str(w))
    s = try_(lambda: jm.get_doe_status(), {})
    check("후처리만 실패한 DOE6 → get_doe_status completed(rerun 대상 아님)", isinstance(s, dict) and (s.get(6) or {}).get("status") == "completed",
          str(s.get(6) if isinstance(s, dict) else s))


# ═════════════════════════════════════════════════════════════════════════
def slurm_shims(tag, queued=""):
    b = tmpdir(tag) / "slurmbin"
    b.mkdir()
    (b / "sbatch").write_text('#!/bin/bash\necho "$@" >> "$(dirname "$0")/sbatch.calls"\necho "Submitted batch job 4242"\n')
    (b / "squeue").write_text(f'#!/bin/bash\nprintf "{queued}"\n')
    (b / "scontrol").write_text('#!/bin/bash\necho "SlurmctldHost[0]     = headx(10.0.0.1)"\n')
    (b / "sacct").write_text('#!/bin/bash\nexit 0\n')
    for n in ("sbatch", "squeue", "scontrol", "sacct"):
        os.chmod(b / n, 0o755)
    return b


def t_keeper():
    print("[KC-07] 후처리 지킴이(가짜 sbatch·squeue·scontrol)")
    DK = try_(lambda: __import__("Runner.DeepKeeper", fromlist=["x"]))
    if not hasattr(DK, "keeper_pass"):
        check("DeepKeeper 모듈", False, str(DK))
        return
    w, out, rc = campaign("keeper", 4)
    runs = {}
    for doe, rep in ((1, "ok"), (2, None), (3, None), (4, None)):
        f = f"Run_{doe}"
        (out / f / "Output").mkdir(parents=True)
        (out / f / "deep_report.sh").write_text("#!/bin/bash\nexit 0\n")
        runs[alias(rc, doe)] = {"status": "completed", "folder": f, "health": "valid"}
        if rep:
            report_files(out / f)
    (out / "Run_4" / ".deep_keeper.json").write_text(json.dumps({"job_id": "777", "array_index": 0}))
    write_index(out, runs)
    old = os.environ["PATH"]
    b = slurm_shims("keeper", queued="777_0|PENDING\\n")
    os.environ["PATH"] = f"{b}:{old}"
    try:
        r = DK.keeper_pass(str(w / "runner_config.json"), dry_run=True)
        check("dry-run: 대상 = 리포트 없는 DOE2·3(DOE4 는 이미 대기 잡) — 제출 없음", sorted(r.get("would_submit") or []) ==
              sorted([alias(rc, 2), alias(rc, 3)]) and not (b / "sbatch.calls").exists(), str(r))
        r = DK.keeper_pass(str(w / "runner_config.json"))
        sb = Path(r["sbatch"]).read_text() if r.get("sbatch") else ""
        check("제출: 배열 잡 하나(--array=0-1%20)·40 CPU·400G·제어 노드 제외(--exclude=headx)", r.get("submitted") == 2
              and r.get("job_id") == "4242" and "#SBATCH --array=0-1%20" in sb and "--cpus-per-task=40" in sb
              and "--mem=400G" in sb and "--exclude=headx" in sb, str(r)[:300] + sb[:400])
        st2 = json.loads((out / "Run_2" / ".deep_keeper.json").read_text())
        check("런 상태 파일(.deep_keeper.json 잡 4242·배열 순번)·keeper_log.jsonl", st2.get("job_id") == "4242"
              and (out / "keeper_log.jsonl").is_file())
        (b / "squeue").write_text('#!/bin/bash\nprintf "4242_[0-1]|PENDING\\n777_0|PENDING\\n"\n')
        r = DK.keeper_pass(str(w / "runner_config.json"))
        check("다시 돌려도 같은 런을 두 번 내지 않는다(4242 대기)", r.get("submitted") == 0, str(r)[:300])
        sh2 = (out / "Run_2" / "deep_report.sh").read_text()
        check("[리뷰 상3] 옛 판 deep_report.sh 는 지금 설정으로 다시 만든 뒤 냈다(빈 리포트 검사 표지)", "N_OK=0; N_BAD=0" in sh2)
        # squeue 가 실패하면 그 패스는 아무것도 내지 않는다
        for f in (out / "Run_2" / ".deep_keeper.json", out / "Run_3" / ".deep_keeper.json"):
            f.unlink()
        (b / "squeue").write_text('#!/bin/bash\nexit 1\n')
        n_before = len((b / "sbatch.calls").read_text().splitlines())
        r = DK.keeper_pass(str(w / "runner_config.json"))
        check("[리뷰 상2c] squeue 실패 → 제출 0·sbatch 안 부름", r.get("submitted") == 0 and r.get("error")
              and len((b / "sbatch.calls").read_text().splitlines()) == n_before, str(r)[:300])
        # 러너 separate_job 잡(deep_report_jobs.txt)이 대기 중이면 건너뛴다, 최근 바뀐 런도
        (b / "squeue").write_text('#!/bin/bash\nprintf "555|PENDING\\n777_0|PENDING\\n"\n')
        (out / "deep_report_jobs.txt").write_text("555\tRun_2\n")
        (out / "Run_3" / "deep_report.log").write_text("running\n")
        r = DK.keeper_pass(str(w / "runner_config.json"), dry_run=True)
        check("[리뷰 상2a·b] 러너 deep 잡 대기(Run_2)·최근 로그가 바뀐 런(Run_3)은 건너뜀", not r.get("would_submit"), str(r)[:300])
        # 배열 나누기 — max_array 1 이면 런마다 배열 하나
        (out / "deep_report_jobs.txt").unlink()
        os.utime(out / "Run_3" / "deep_report.log", (0, 0))
        r = DK.keeper_pass(str(w / "runner_config.json"), viz_override={"max_array": 1})
        check("[리뷰 중3] max_array 1 → 배열 둘로 나눠 낸다", r.get("submitted") == 2 and len(r.get("job_ids") or []) == 2, str(r)[:300])
    finally:
        os.environ["PATH"] = old


# ═════════════════════════════════════════════════════════════════════════
def t_impact():
    print("[KC-08·09] IMPACT 관문·자리 표")
    IG = try_(lambda: __import__("Runner.ImpactGate", fromlist=["x"]))
    if not hasattr(IG, "check_impact_keys"):
        check("ImpactGate 모듈", False, str(IG))
        return
    w = IG.check_impact_keys({"impact": {"sphere": {"diameter": 10}, "hieght": 100, "dt": 1e-6,
                                         "cylinder_stages": [{"diameter": 1, "hight": 2}]}})
    check("모르는 키: sphere 하위 객체·hieght(did you mean height)·단 키 hight", any("sphere" in x and "하위 객체" in x for x in w)
          and any("hieght" in x and "height" in x for x in w) and any("hight" in x for x in w), str(w))
    sw = IG.si_default_warnings({"impact": {}}, "mm-t-s")
    check("mm 모델에 height·dimension·dt 없음 → SI 기본값 경고 셋", len([x for x in sw if "기본값" in x]) >= 3, str(sw))
    check("표본 DOE: 1045 중 5개 = 1·262·523·784·1045", IG.sample_does(1045, 5) == [1, 262, 523, 784, 1045])
    run = next(iter(sorted((DWI / "runs").glob("Run_*"))), None) if DWI.is_dir() else None
    if not run:
        skip("IMPACT 생성 덱 점검", f"{DWI} 없음")
    else:
        d = tmpdir("impact") / run.name
        shutil.copytree(run, d)
        shutil.copy2(DWI / "opt.txt", d / "step_config.txt")
        sim = {"impact": {"type": "Cylinder", "density": 7.85e-9, "cylinder_stages": [
            {"diameter": 0.6, "outer_diameter": 0.8, "height": 0.2}, {"diameter": 0.7, "height": 0.2, "density": 7.85e-9},
            {"diameter": 0.8, "height": 0.2, "density": 7.85e-9}]}}
        r = IG.analyze_impact_run(str(d), sim)
        check("3단 실린더 덱: 충격추 파트 3개 요소 > 0·VZ −1401 ≈ −√(2·9810·100)·자리 오차 < 0.01 → reject 없음",
              not r["reject"] and len(r["impactor_parts"]) == 3 and abs(r["vz"] + 1401.0) < 1 and r["pos_err"] < 0.01,
              json.dumps({k: r.get(k) for k in ("reject", "warn", "impactor_elems", "vz", "pos_err")}, ensure_ascii=False))
        check("KMM 표준 접촉 두 장(전부 대 벽·전부 대 충격추)·단 사이 TIED 만 → 겹침 경고 없음", not any("가짜 에너지" in x for x in r["warn"]),
              str(r["warn"]))
        r2 = IG.analyze_impact_run(str(d), sim, model_contacts=[{"kw": "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID", "cid": 9,
                                                                    "title": "Contact_9"}])
        check("원 모델의 접촉(9 — 전부 대 충격추 앞단)이 충격추를 덮음 → 겹침 경고", any("원 모델의 접촉" in x for x in r2["warn"]), str(r2["warn"]))
        glob = tmpdir("impact_glob") / run.name
        shutil.copytree(run, glob)
        shutil.copy2(DWI / "opt.txt", glob / "step_config.txt")
        edit(glob / "DropWeightImpactTestSet.k", lambda t: t.replace("*END", "*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID\n        99Global\n"
                                                                              "         0         0         5         0\n\n\n*END", 1))
        r3 = IG.analyze_impact_run(str(glob), sim)
        check("모델 정보 없이도: 전역 SINGLE_SURFACE(전부)가 세 번째로 충격추를 덮음 → 겹침 경고", any("가짜 에너지" in x for x in r3["warn"]),
              str(r3["warn"]) + str(r3.get("contact_cards")))
        bad = tmpdir("impact_slow") / run.name
        shutil.copytree(run, bad)
        shutil.copy2(DWI / "opt.txt", bad / "step_config.txt")
        edit(bad / "DropWeightImpactTestSet.k", lambda t: t.replace("-1.401e+03", "-4.429e+01"))
        r = IG.analyze_impact_run(str(bad), sim)
        check("VZ −44.29(g 9.81 을 mm 덱에 — 31.6배 느림) → reject", any("√(2gh)" in x for x in r["reject"]), str(r["reject"]))
        body = tmpdir("impact_body") / run.name
        shutil.copytree(run, body)
        shutil.copy2(DWI / "opt.txt", body / "step_config.txt")
        def _drop_part4(t):                 # 파트 4(몸통) 요소 줄을 지운다
            out, cur = [], None
            for line in t.splitlines(True):
                if line.startswith("*"):
                    cur = line.strip().upper()
                if cur and cur.startswith("*ELEMENT_SOLID") and not line.startswith(("*", "$")) and line[8:16].strip() == "4":
                    continue
                out.append(line)
            return "".join(out)
        edit(body / "DropWeightImpactTestSet.k", _drop_part4)
        r = IG.analyze_impact_run(str(body), sim)
        check("몸통(파트 4) 요소 0 → reject", any("요소 0" in x for x in r["reject"]), str(r["reject"]))
    # 자리 표
    pos = {str(i): {"1": {"position_name": f"P_{(i - 1) // 3 + 1:03d}_{(i - 1) % 3 + 1:03d}", "x": float(i), "y": 2.0}}
           for i in range(1, 7)}
    w2, out, rc = campaign("sites", 6, mode="IMPACT", pp=False, positions=pos)
    runs = {}
    for doe in (1, 2, 3, 4):
        f = f"Run_{doe}"
        (out / f).mkdir()
        (out / f / "DropWeightImpactTestSet.k").write_text("*KEYWORD\n*END\n")
        runs[f"Pj_CUM001_DOE{doe:03d}_S001_IMPACT_{pos[str(doe)]['1']['position_name']}"] = {"status": "completed", "folder": f}
    runs[f"Pj_CUM001_DOE005_S001_IMPACT_{pos['5']['1']['position_name']}"] = {"status": "failed", "folder": "", "error": "KooMeshModifier failed"}
    write_index(out, runs)
    tab = IG.sites_table(rc, face="BOT")
    check("자리 표: 계획 6 = 생성 4 + 빠짐 2, 빠진 자리 까닭(KMM 실패·아직 안 돎), 열·행·face",
          tab["planned"] == 6 and tab["generated"] == 4 and tab["missing"] == 2
          and any("KooMeshModifier" in r["missing_reason"] for r in tab["rows"])
          and tab["rows"][4]["row"] == 2 and tab["rows"][4]["col"] == 2 and tab["rows"][0]["face"] == "BOT",
          json.dumps(tab["rows"][4:], ensure_ascii=False))


# ═════════════════════════════════════════════════════════════════════════
def t_deck_gate():
    print("[KC-10] 덱 관문")
    DG = try_(lambda: __import__("Runner.DeckGate", fromlist=["x"]))
    if not hasattr(DG, "deck_gate"):
        check("DeckGate 모듈", False, str(DG))
        return
    w = tmpdir("deckgate")
    (w / "parts").mkdir()
    (w / "parts" / "a.k").write_text("*KEYWORD\n*END\n")
    model = w / "model.k"
    model.write_text("*KEYWORD\n*INCLUDE\nparts/a.k\n*INCLUDE\nmissing/b.k\n*END\n")
    R = DG.deck_gate({"project": {"model_file": str(model)}, "environment": {}}, [])
    check("원 덱의 상대 include 를 못 찾음(missing/b.k) → reject, 찾는 것(parts/a.k)은 통과", R["verdict"] == "reject"
          and any("missing/b.k" in x for x in R["reject"]) and not any("parts/a.k" in x for x in R["reject"]), str(R["reject"]))
    if not REAL.is_dir():
        skip("카나리아 3자 대조", f"{REAL} 없음")
        return
    model = Path("/data/koopark/Test_005_Fibonacci_100/MinimumModel.k")
    can = tmpdir("canary") / "Run_c"
    (can / "Output").mkdir(parents=True)
    shutil.copy2(REAL / "DropSet.k", can / "DropSet.k")
    with open(REAL / "Output" / "d3plot", "rb") as f:
        head = f.read(4096)
    (can / "Output" / "d3plot").write_bytes(head)
    (can / "health.json").write_text(json.dumps({"verdict": "valid"}))
    R = DG.deck_gate({"project": {"model_file": str(model)}, "environment": {}}, [str(can)])
    check("카나리아: 원 덱 파트 요소 수 = 생성 덱, 생성 덱 = d3plot 머리(31176·45457), KMM 바닥판(23) 따로 → pass",
          R["verdict"] in ("pass", "warn") and not R["reject"] and R["canaries"][0]["added_parts"].get("23") == 1800,
          str(R["reject"]) + str(R["canaries"][0].get("d3plot")))
    import struct
    b = bytearray(head)
    struct.pack_into("<i", b, 16 * 4, 31000)
    (can / "Output" / "d3plot").write_bytes(bytes(b))
    R = DG.deck_gate({"project": {"model_file": str(model)}, "environment": {}}, [str(can)])
    check("d3plot 절점 수 다름(다른 덱의 결과) → reject", any("d3plot" in x for x in R["reject"]), str(R["reject"]))
    (can / "Output" / "d3plot").write_bytes(head)
    def _drop_some(t):
        L = t.splitlines(True)
        i = next(k for k, l in enumerate(L) if l.startswith("*ELEMENT_SOLID"))
        j = i + 1
        while L[j].startswith("$"):
            j += 1
        return "".join(L[:j] + L[j + 2:])      # 한 요소(2줄 꼴이면 2줄) 지움
    edit(can / "DropSet.k", _drop_some)
    R = DG.deck_gate({"project": {"model_file": str(model)}, "environment": {}}, [str(can)])
    check("생성 덱에서 원 덱 파트 요소가 빠짐 → reject", any("요소 수가 다르다" in x for x in R["reject"]), str(R["reject"]))
    gen = tmpdir("geninc") / "Run_i"
    gen.mkdir()
    (gen / "DropSet.k").write_text("*KEYWORD\n*INCLUDE\n kept.k\n*END\n")
    (w / "kept.k").write_text("*KEYWORD\n*END\n")
    m2 = w / "m2.k"
    m2.write_text("*KEYWORD\n*END\n")
    R = DG.deck_gate({"project": {"model_file": str(m2)}, "environment": {}}, [str(gen)])
    check("생성 덱 include 를 실행 폴더에서 못 찾고 additional_files 도 없음 → reject", any("additional_files" in x for x in R["reject"]))
    R = DG.deck_gate({"project": {"model_file": str(m2)}, "environment": {"additional_files": ["kept.k"]}}, [str(gen)])
    check("additional_files 가 그 include 를 실행 폴더로 복사하면 → 그 거절 없음", not any("kept.k" in x for x in R["reject"]), str(R["reject"]))


# ═════════════════════════════════════════════════════════════════════════
def fake_solver(tag, src_out, rc=0):
    """가짜 LS-DYNA — src_out 의 산출물을 cwd 로 복사하고 dynain 을 만든 뒤 rc. 부른 횟수를 센다."""
    b = tmpdir(tag)
    p = b / "lsdyna"
    p.write_text(f"""#!/bin/bash
echo x >> "{b}/calls"
cp "{src_out}"/* . 2>/dev/null
echo "*KEYWORD" > dynain
exit {rc}
""")
    os.chmod(p, 0o755)
    return p, b / "calls"


REAL_RC = Path("/data/koopark/Test_005_Fibonacci_100/runner_config.json")


def runner_campaign(tag, solver, pp=None):
    """실제 Test_005 runner_config 사본 — DOE 1개·가짜 LS-DYNA·컨테이너 없음·로컬 스크래치 끔."""
    w = tmpdir(tag)
    out = w / "output"
    out.mkdir()
    rc = json.loads(REAL_RC.read_text(encoding="utf-8"))
    rc["project"].update(output_dir=str(out), index_file=str(out / "simulation_index.json"))
    rc["scenario"]["doe_count"] = 1
    rc["scenario"]["doe_angles"] = {"1": rc["scenario"]["doe_angles"]["1"]}
    rc["execution"].update(checkpoint_file=str(out / "checkpoint.json"), timeout_dynain_seconds=30)
    env = rc["environment"]
    for k in ("apptainer_sif", "lsdyna_apptainer_sif", "koochainrun_path"):
        env.pop(k, None)
    env.update(lsdyna_path=str(solver), mpi_enabled=False, ncpu=1, use_local_scratch=False,
               apptainer_tmpdir=str(w / "apptmp"))
    rc.pop("postprocess", None)
    if pp:
        rc["postprocess"] = pp
    (w / "runner_config.json").write_text(json.dumps(rc), encoding="utf-8")
    pre = w / "pre" / "Run_1"
    pre.mkdir(parents=True)
    for n in ("DropSet.k", "DropSet.json", "step_config.txt"):
        shutil.copy2(REAL / n, pre / n)
    return w, out, rc


def run_kcr(w, extra_env=None):
    env = dict(os.environ, **(extra_env or {}))
    cmd = [*KCR_CMD, "run", str(w / "runner_config.json"), "--doe", "1",
           "--skip-koomeshmodifier", "--pregenerated-dir", str(w / "pre")]
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)


def t_runner():
    print("[러너 배선] 가짜 LS-DYNA — health invalid 면 rc 1(재시도 없음)·출처 기록·후처리만 실패면 rc 3")
    if not REAL.is_dir():
        skip("러너 배선", f"{REAL} 없음")
        return
    good = fixture_run("rgood") / "Output"
    bad = fixture_run("rbad") / "Output"
    for n in ("d3hsp", "mes0000"):
        edit(bad / n, lambda t: t.replace("N o r m a l    t e r m i n a t i o n", "                                    "))
    s, calls = fake_solver("sgood", good)
    w, out, rc = runner_campaign("rgood", s)
    r = run_kcr(w, {"KCR_WRAPPER_NAME": "wrapT"})
    idx = json.loads((out / "simulation_index.json").read_text())["scenarios"][0]["runs"]
    rec = next(iter(idx.values()), {})
    rd = out / rec.get("folder", "x")
    P = json.loads((rd / "provenance.json").read_text()) if (rd / "provenance.json").exists() else {}
    check("정상 산출물 → rc 0·completed·health valid·provenance(래퍼 wrapT·설정 sha·completed)", r.returncode == 0
          and rec.get("status") == "completed" and rec.get("health") == "valid" and P.get("wrapper_name") == "wrapT"
          and P.get("status") == "completed" and P.get("runner_config_sha256"), f"rc={r.returncode} {rec} {r.stdout[-400:]}")
    s, calls = fake_solver("sbad", bad)
    w, out, rc = runner_campaign("rbad", s)
    r = run_kcr(w)
    idx = json.loads((out / "simulation_index.json").read_text())["scenarios"][0]["runs"]
    rec = next(iter(idx.values()), {})
    n_calls = len(calls.read_text().splitlines()) if calls.exists() else 0
    check("LS-DYNA rc 0 인데 정상 종료 문구 없음 → rc 1·failed(health invalid)·재시도 없음(1번만)", r.returncode == 1
          and rec.get("status") == "failed" and "health invalid" in (rec.get("error") or "") and n_calls == 1,
          f"rc={r.returncode} calls={n_calls} {rec}")
    s, calls = fake_solver("srec", bad)
    w, out, rc = runner_campaign("rrec", s)
    r = run_kcr(w, {"KCR_HEALTH": "record"})
    idx = json.loads((out / "simulation_index.json").read_text())["scenarios"][0]["runs"]
    rec = next(iter(idx.values()), {})
    Hr = json.loads((out / rec.get("folder", "x") / "health.json").read_text()) if rec.get("folder") else {}
    check("[리뷰 하3] KCR_HEALTH=record(대역 솔버 e2e) → 같은 고장 런이 rc 0·completed, health.json 은 invalid 로 남김",
          r.returncode == 0 and rec.get("status") == "completed" and Hr.get("verdict") == "invalid", f"rc={r.returncode} {rec}")
    # 후처리만 실패 — 가짜 apptainer 가 리포트를 안 쓴다 → deep rc 3 → 잡 rc 3, 단계 completed
    sif = TMP / "fake.sif"
    sif.write_text("x")
    b = fake_bin("rpp", deep_writes=())
    s, calls = fake_solver("spp", good)
    w, out, rc = runner_campaign("rpp", s, pp={"enabled": True, "auto_deep": True, "sif_path": str(sif)})
    r = run_kcr(w, {"PATH": f"{b}:{os.environ['PATH']}"})
    idx = json.loads((out / "simulation_index.json").read_text())["scenarios"][0]["runs"]
    rec = next(iter(idx.values()), {})
    check("해석 정상·리포트 빈 폴더 → 잡 rc 3, 단계 completed·postprocess rc 3", r.returncode == 3
          and rec.get("status") == "completed" and (rec.get("postprocess") or {}).get("rc") == 3,
          f"rc={r.returncode} {rec} {r.stdout[-300:]}")


# ═════════════════════════════════════════════════════════════════════════
KMM = "/data/SmartTwinPreprocessor/bin/KooMeshModifier"
PRE_SIF = "/opt/apptainers/SmartTwinPreprocessor.sif"


def kcr(*args, env=None, timeout=900):
    e = dict(os.environ, LANG="C.UTF-8", LC_ALL="C.UTF-8", PYTHONIOENCODING="utf-8", **(env or {}))
    return subprocess.run([*KCR_CMD, *map(str, args)], capture_output=True, text=True, env=e, timeout=timeout)


def impact_scenario(d, **imp):
    sys.path.insert(0, str(REPO / "tests"))
    import test_cli_help as H          # 상자 모델 생성기(_box_model) — import 만으로는 시험이 돌지 않는다
    from Runner.cli_help_kcr import IMP_SPHERE
    H._box_model(str(d / "model.k"))
    sc = json.loads(IMP_SPHERE)
    sc["base_dir"] = str(d)
    # 운영과 같게 SIF 안 KMM 으로 — 호스트 KMM 은 gmsh 가 없어 충격추를 메시하지 못한다(몸통 요소 0 덱이 나온다 — 관문이 잡는다)
    sc["environment"] = {"apptainer_sif": PRE_SIF, "apptainer_bind": "/data:/data",
                         "koomeshmodifier_path": "/opt/SmartTwinPreprocessor/bin/KooMeshModifier",
                         "lsdyna_path": "/bin/false", "ncpu": 1, "apptainer_tmpdir": str(d / "apptmp")}
    sc["simulation_params"]["impact"].update(imp)
    (d / "scenario.json").write_text(json.dumps(sc), encoding="utf-8")
    return d / "scenario.json"


def t_impact_gate_e2e():
    print("[KC-08] prepare --check-impact — 러너와 같은 경로(단계 설정 → KMM)로 표본 덱 2개")
    if not (os.path.isfile(PRE_SIF) and shutil.which("apptainer")):
        skip("IMPACT 관문 끝까지", f"{PRE_SIF}·apptainer 없음")
        return
    d = tmpdir("igate")
    sp = impact_scenario(d)
    r = kcr("prepare", sp, "--check-impact", "--sample", "2")
    gj = d / "impact_gate" / "impact_gate.json"
    res = json.loads(gj.read_text()) if gj.is_file() else {}
    rows = res.get("rows") or []
    check("정상 강구(반지름 8·높이 500·mm): rc 0·표본 2개(DOE 1·9)·충격추 요소 > 0·VZ ≈ −√(2·9810·500)·reject 없음",
          r.returncode == 0 and [x.get("doe") for x in rows] == [1, 9] and all(not x.get("reject") for x in rows)
          and all(abs((x.get("vz") or 0) + (2 * 9810 * 500) ** 0.5) < 1.0 for x in rows),
          f"rc={r.returncode} {r.stdout[-600:]} {[(x.get('doe'), x.get('reject'), x.get('vz')) for x in rows]}")
    check("prepare 기록(.runner_config.json.kcr_prepare.json)에 scenario sha", (d / ".runner_config.json.kcr_prepare.json").is_file())
    d = tmpdir("igate_g")
    sp = impact_scenario(d, gravity=9.81)
    r = kcr("prepare", sp, "--check-impact", "--sample", "1")
    gj = d / "impact_gate" / "impact_gate.json"
    res = json.loads(gj.read_text()) if gj.is_file() else {}
    rows = res.get("rows") or [{}]
    check("mm 덱에 impact.gravity 9.81(31.6배 느림) → 관문 reject·prepare rc 1", r.returncode == 1
          and any("√(2gh)" in x or "중력" in x for x in rows[0].get("reject") or []), f"rc={r.returncode} {rows[0].get('reject')}")
    d = tmpdir("igate_key")
    sp = impact_scenario(d)
    sc = json.loads(sp.read_text())
    sc["simulation_params"]["impact"]["sphere"] = {"diameter": 16}
    sp.write_text(json.dumps(sc))
    r = kcr("prepare", sp)
    check("impact.sphere 하위 객체 → prepare 가 '하위 객체는 러너가 읽지 않는다' 경고", r.returncode == 0 and "하위 객체" in r.stdout,
          r.stdout[-400:])


def t_cli():
    print("[명령줄] status --csv·manifest·health·d3plot-delete·budget·gate·sites·keeper·submit(예산 거절 → sbatch 전 멈춤)")
    w, out, rc = campaign("cli", 2)
    rcp = w / "runner_config.json"
    runs = {}
    for doe in (1, 2):
        f = f"Run_{doe}"
        (out / f / "Output").mkdir(parents=True)
        for n in ("d3plot", "d3plot01"):
            (out / f / "Output" / n).write_bytes(b"\0" * 2048)
        runs[alias(rc, doe)] = {"status": "completed", "folder": f, "health": "valid"}
    report_files(out / "Run_1")
    write_index(out, runs)
    r = kcr("status", rcp, "--csv")
    check("status --csv → rc 0·doe_status.csv·'후처리 대기 1'", r.returncode == 0 and (out / "doe_status.csv").is_file()
          and "후처리 대기 1" in r.stdout, r.stdout[-300:] + r.stderr[-300:])
    old = out / "Run_2" / "deep_report.sh"
    old.write_text('#!/bin/bash\nRUN_DIR="%s"\nrm -f "$RUN_DIR"/d3plot "$RUN_DIR"/d3plot[0-9]*\n' % (out / "Run_2" / "Output"))
    sif = TMP / "fake.sif"
    sif.write_text("x")
    rc["postprocess"] = {"enabled": True, "sif_path": str(sif), "delete_d3plot_after_deep": False}
    rcp.write_text(json.dumps(rc))
    bdeep = fake_bin("clipost")
    r = kcr("postprocess", rcp, "--deep", env={"PATH": f"{bdeep}:{os.environ['PATH']}"})
    check("[리뷰 상3] postprocess --deep: 옛 판(무조건 rm) 스크립트를 다시 만들어 돌림 — 삭제 끔이라 d3plot 그대로",
          "N_OK=0; N_BAD=0" in old.read_text() and len(list((out / "Run_2" / "Output").glob("d3plot*"))) == 2,
          r.stdout[-400:] + r.stderr[-300:])
    report_files(out / "Run_2")
    rc["postprocess"] = {"enabled": True, "auto_deep": True}
    rcp.write_text(json.dumps(rc))
    for n in ("d3plot", "d3plot01"):
        (out / "Run_2" / "Output" / n).write_bytes(b"\0" * 2048)
    shutil.rmtree(out / "Run_2" / "Output" / "report")
    r = kcr("manifest", rcp)
    check("manifest → return_manifest.jsonl(머리 + 2줄)", r.returncode == 0 and (out / "return_manifest.jsonl").is_file()
          and len((out / "return_manifest.jsonl").read_text().splitlines()) == 3, r.stdout[-300:] + r.stderr[-300:])
    r = kcr("d3plot-delete", out / "Run_2")
    check("d3plot-delete(리포트 없음) → rc 2·보존", r.returncode == 2 and len(list((out / "Run_2" / "Output").glob("d3plot*"))) == 2,
          r.stdout[-300:])
    r = kcr("d3plot-delete", out / "Run_1")
    check("d3plot-delete(리포트 완결) → rc 0·지움", r.returncode == 0 and not list((out / "Run_1" / "Output").glob("d3plot*")),
          r.stdout[-300:])
    if REAL.is_dir():
        d = fixture_run("clihealth")
        r = kcr("health", d, "--no-binout")
        check("health Run_*(정상 사본) → rc 0·health.json", r.returncode == 0 and (d / "health.json").is_file(), r.stdout[-300:])
        edit(d / "Output" / "d3hsp", lambda t: t.replace("Problem time       =    5.0000E-03", "Problem time       =    1.0000E-03"))
        r = kcr("health", d, "--no-binout")
        check("health Run_*(목표 미달) → rc 1", r.returncode == 1, r.stdout[-300:])
    pilot = out / "Run_1"
    du = shutil.disk_usage(str(out))
    th = max(1e-6, du.used / du.total * 100.0 - 1.0)       # 지금 사용률보다 1 % 낮은 선 — 사용량이 조금 흔들려도 늘 넘친다
    r = kcr("budget", rcp, "--pilot", pilot, "--concurrency", "1", "--threshold", f"{th:.9f}")
    check("budget(선이 지금 사용량 아래) → rc 1 reject", r.returncode == 1 and "reject" in r.stdout, r.stdout[-300:])
    r = kcr("gate", rcp)
    check("gate(모델 덱 없음) → rc 1·gate_report.json", r.returncode == 1 and (out / "gate_report.json").is_file(), r.stdout[-300:])
    pos = {"1": {"1": {"position_name": "P_001_001", "x": 0.0, "y": 0.0}}}
    w2, out2, rc2 = campaign("clisites", 1, mode="IMPACT", pp=False, positions=pos)
    r = kcr("sites", w2 / "runner_config.json", "--face", "TOP")
    check("sites → rc 0·sites.csv(계획 1 = 생성 0 + 빠짐 1)", r.returncode == 0 and (out2 / "sites.csv").is_file()
          and "계획 1 = 생성 0 + 빠짐 1" in r.stdout, r.stdout[-300:])
    b = slurm_shims("clikeeper")
    r = kcr("keeper", rcp, "--dry-run", env={"PATH": f"{b}:{os.environ['PATH']}"})
    check("keeper --dry-run → rc 0·대상 줄", r.returncode == 0 and "[keeper]" in r.stdout and not (b / "sbatch.calls").exists(),
          r.stdout[-300:] + r.stderr[-300:])
    # submit — 예산 거절이면 sbatch 전에 멈춘다(가짜 sbatch 가 불리지 않는다)
    rc["environment"]["storage_budget"] = {"pilot": str(pilot), "threshold_pct": th, "concurrency": 1}
    rcp.write_text(json.dumps(rc))
    r = kcr("submit", rcp, "--nodes", "1", "--jobs-per-node", "1", env={"PATH": f"{b}:{os.environ['PATH']}"})
    check("submit(예산 reject) → rc 1·'내지 않는다'·sbatch 안 불림", r.returncode == 1 and "내지 않는다" in r.stdout
          and not (b / "sbatch.calls").exists(), r.stdout[-400:] + r.stderr[-300:])
    rc["environment"]["storage_budget"] = {"pilot": str(pilot), "threshold_pct": th}     # 동시 수 없음
    rcp.write_text(json.dumps(rc))
    r = kcr("submit", rcp, env={"PATH": f"{b}:{os.environ['PATH']}"})
    check("[리뷰 중1] submit: 동시 수를 주지 않으면 argparse 기본(2×4)이 아니라 런 수 전부로 본다", "동시 수를 모른다" in r.stdout
          and r.returncode == 1 and not (b / "sbatch.calls").exists(), r.stdout[-400:])
    src = (ROOT / "KooChainRun").read_text(encoding="utf-8")
    check("[리뷰 중2] 스크래치 잡 스크립트: rc 3(후처리만 실패)도 결과를 옮긴 뒤 노드 임시 폴더를 지운다",
          "[ $EXIT_CODE -eq 0 ] || [ $EXIT_CODE -eq 3 ]" in src)


def main():
    for t in (t_health, t_provenance, t_gate, t_deep_sh, t_budget, t_status, t_keeper, t_impact, t_deck_gate, t_runner,
              t_impact_gate_e2e, t_cli):
        try:
            t()
        except Exception as e:
            import traceback
            traceback.print_exc()
            check(f"{t.__name__} 가 예외 없이 끝남", False, f"{type(e).__name__}: {e}")
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}" + (f" (건너뜀 {len(SKIPS)})" if SKIPS else ""))
    for f in FAILS:
        print("  FAIL", f)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
