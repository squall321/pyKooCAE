# DROP_ATTITUDE 의 EndTimeTable(각도별 ENDTIM 표) 키 — 파싱 함정·키 없을 때 바이트 동일·각도별 카드 차이·오류 rc 1 을 검증하는 회귀 시험
"""
배경
  RIGID_DROP_ENDTIME 이 만든 표(<base>_endtime.csv)를 DROP_ATTITUDE 가 받아 각도마다 ENDTIM 을 달리 쓴다(한 각도·Fast DOE 여러
  각도 모두). Fast DOE 는 CONTROL·DATABASE 카드를 베이스 캐시 판에 한 번 굽기 때문에 각도마다 그 글을 바꿔 써야 한다.
  기존 DROP 출력은 키가 없으면 바이트까지 같아야 한다(사용자 요구).

  [1] 파서: 키 이름 전체 일치만, 경로의 runid·tfinal·height 같은 글자가 다른 키로 안 읽힘, 다른 키를 삼키지 않음, 절대 경로
  [2] 한 각도: 키 없음 = 표 값이 모두 tFinal 인 표(바이트 동일), 다른 값이면 ENDTIM·NPLTC 세 줄만 다름,
      표(tFinal 없이) = 키 없이 tFinal=endtim 으로 돈 덱(바이트 동일)
  [3] Fast DOE 세 각도(메시 바닥판): 같은 판정 + 각도 k 덱의 CONTROL·DATABASE 블록 = 같은 각도 단일 실행(tFinal=endtim_k),
      Fast·단일 사이 블록 차이는 키 없을 때와 같다(알려진 *NODE 두 덩이·바닥 접촉 CID 만)
  [4] Fast DOE 강체벽 바닥: 같은 판정
  [5] 오류: 표에 없는 각도·숫자 아닌 endtim·endtim 칸 없음·dt 없음·없는 파일 → rc 1, 덱을 쓰지 않음
  [6] (있으면) Examples/MinimumModel.k Fast 세 각도: 키 없음 = 같은 값 표, 다른 값이면 세 줄만 다름
  [7] 표 대조: 메타 v0(낙하 속도) 다름·순수 낙하 아님 → rc 1, tFinal 보다 긴 ENDTIM 경고, reach 가 바닥판 반폭보다 길면 경고
  [8] RIGID_DROP_ENDTIME 옵션 함정: 다른 모드와 함께·두 번·끝줄 없음 → 종료 코드 1
  [9] RIGID_DROP_ENDTIME 이 rc 3(리더가 요소를 버림)으로 끝날 때 표는 썼지만 빠진 파트를 알리는 줄 (pybullet 있을 때만)

실행: venv312/bin/python tests/test_drop_endtime_table.py
"""
import contextlib
import io
import math
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
PY = ROOT / "venv312" / "bin" / "python"
MINI = ROOT / "Examples" / "MinimumModel.k"
sys.path.insert(0, str(GEN))

from KooCAEManager.KooEndTimeTable import drop_direction, write_endtime_table  # noqa: E402

FAILS = []
TRAP = "tbl_runid_tfinal_height_density_dt_eulerrolling_dropsurface"   # 다른 키 이름 글자를 일부러 넣은 표 폴더


def check(name, cond, detail=""):
    print("  %-74s %s" % (name[:74], "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def box_model(path):
    n, h, lines, idx, nid = 4, 2.5, [], {}, 0
    for k in range(3):
        for j in range(n + 1):
            for i in range(n + 1):
                nid += 1
                idx[(i, j, k)] = nid
                lines.append(f"{nid:8d}{i * h:16.6f}{j * h:16.6f}{k * 1.0:16.6f}")
    elems, eid = [], 0
    for k in range(2):
        for j in range(n):
            for i in range(n):
                eid += 1
                c = [idx[(i, j, k)], idx[(i + 1, j, k)], idx[(i + 1, j + 1, k)], idx[(i, j + 1, k)],
                     idx[(i, j, k + 1)], idx[(i + 1, j, k + 1)], idx[(i + 1, j + 1, k + 1)], idx[(i, j + 1, k + 1)]]
                elems.append(f"{eid:8d}{1:8d}" + "".join(f"{x:8d}" for x in c))
    f10 = lambda *v: "".join(f"{str(x):>10s}" for x in v)  # noqa: E731
    Path(path).write_text("\n".join(
        ["*KEYWORD", "*PART", "BLOCK", f10(1, 1, 1), "*SECTION_SOLID", f10(1, 1),
         "*MAT_ELASTIC", f10(1, "7.85e-9", "200000.0", "0.3"), "*NODE"] + lines + ["*ELEMENT_SOLID"] + elems + ["*END"]) + "\n")


def option(model, angles, height, tfinal, dt, surface, table=None, extra=()):
    n = len(angles)
    rep = lambda v: ",".join([str(v)] * n)  # noqa: E731
    lines = ["*Inputfile", model, "*Mode", "DROP_ATTITUDE,1", "**DropAttitude,1",
             "EulerRolling," + ",".join(str(a[0]) for a in angles),
             "EulerPitching," + ",".join(str(a[1]) for a in angles),
             "EulerYawing," + ",".join(str(a[2]) for a in angles),
             "Gravity,9810", "Height," + rep(height)]
    if table:
        lines.append(f"EndTimeTable,{table}")
    lines += ["InitialVelocityX," + rep(0), "InitialVelocityY," + rep(0), "InitialVelocityZ," + rep(0),
              "InitialAngularVelocityX," + rep(0), "InitialAngularVelocityY," + rep(0), "InitialAngularVelocityZ," + rep(0),
              "OffsetDistance,0.05", "Density,7.85e-09", "YoungsModulus,200000.0", "PoissonRatio,0.3"]
    if tfinal is not None:
        lines.append(f"tFinal,{tfinal}")
    if dt is not None:
        lines.append(f"dt,{dt}")
    lines += [f"DropSurface,{surface}"] + list(extra) + ["**EndDropAttitude", "*End"]
    return "\n".join(lines) + "\n"


def table(path, rows, meta=None, extra=None):
    """rows: [(roll, pitch, yaw, endtim)] — 표 형식은 계약 모듈 기록기 그대로. meta 는 더할 '# key=value', extra 는 줄마다 더할 칸."""
    out = []
    for k, (r, p, y, e) in enumerate(rows):
        d = drop_direction(r, p, y)
        out.append(dict({"name": f"A{k + 1:03d}", "roll": float(r), "pitch": float(p), "yaw": float(y), "dx": float(d[0]),
                         "dy": float(d[1]), "dz": float(d[2]), "class": "slapdown", "endtim": e, "governing_e": 0.3},
                        **(extra or {})))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    write_endtime_table(str(path), out, dict({"deck": "box", "units": "mm-t-s", "time_unit": "s"}, **(meta or {})))


def run(wd, opt_text, model="box.k", src=None):
    """작업 폴더에 모델·옵션을 두고 KMM 을 돌린다 → (rc, stdout). 모델은 늘 사본(KMM 이 옆에 _dump.k 를 쓴다)."""
    wd = Path(wd)
    wd.mkdir(parents=True, exist_ok=True)
    if src:
        shutil.copy2(src, wd / model)
    elif not (wd / model).exists():
        box_model(wd / model)
    (wd / "opt.txt").write_text(opt_text)
    r = subprocess.run([str(PY), str(GEN / "KooMeshModifier.py"), "opt.txt", str(wd)], cwd=str(GEN),
                       capture_output=True, text=True, timeout=900)
    return r.returncode, r.stdout + r.stderr


def decks(wd, stem):
    """→ {이름: 바이트} — 각도 덱과 _drop.k (입력·_dump.k 제외)."""
    return {p.name: p.read_bytes() for p in sorted(Path(wd).glob(f"{stem}_*.k")) if not p.name.endswith("_dump.k")}


def angle_decks(wd, stem):
    return [p for p in sorted(Path(wd).glob(f"{stem}_[0-9][0-9][0-9]_DA_*.k"))]


def data_line(lines, kw):
    """키워드 줄 다음 첫 데이터 줄(주석 '$' 건너뜀)의 번호."""
    i = lines.index(kw)
    j = i + 1
    while lines[j].startswith("$"):
        j += 1
    return j


TFINAL_CARDS = ("*CONTROL_TERMINATION", "*DATABASE_BINARY_D3PLOT", "*DATABASE_BINARY_INTFOR")


def only_tfinal_lines_differ(a, b, endtim, dt):
    """a(키 없음)·b(표) 덱이 줄 수가 같고, 다른 줄이 정확히 ENDTIM·D3PLOT NPLTC·INTFOR NPLTC 세 줄이며 값이 기대대로인가."""
    if not a or not b:
        return False, "덱 없음"
    la, lb = a.decode().splitlines(), b.decode().splitlines()
    if len(la) != len(lb):
        return False, f"줄 수 {len(la)} → {len(lb)}"
    changed = [i for i in range(len(la)) if la[i] != lb[i]]
    want = sorted(data_line(la, kw) for kw in TFINAL_CARDS)
    if changed != want:
        return False, f"바뀐 줄 {[(i + 1, la[i], lb[i]) for i in changed][:6]} (기대 {[i + 1 for i in want]})"
    t = lb[data_line(lb, "*CONTROL_TERMINATION")]
    d3 = lb[data_line(lb, "*DATABASE_BINARY_D3PLOT")]
    itf = lb[data_line(lb, "*DATABASE_BINARY_INTFOR")]
    npltc = int(endtim / dt)
    ok = t[:10] == format(endtim, ">10.3e") and int(d3[30:40]) == npltc and int(itf[30:40]) == npltc
    return ok, f"ENDTIM '{t[:10]}' NPLTC {d3[30:40].strip()}/{itf[30:40].strip()} (기대 {format(endtim, '.3e')}, {npltc})"


def blocks(data):
    out, cur = [], None
    for ln in data.decode().splitlines():
        if ln.startswith("*"):
            if cur is not None:
                out.append("\n".join(cur))
            cur = [ln]
        elif cur is not None:
            cur.append(ln)
    if cur is not None:
        out.append("\n".join(cur))
    return [b for b in out if not b.startswith(("*KEYWORD", "*END"))]


def control_db(data):
    return [b for b in blocks(data) if b.startswith(("*CONTROL", "*DATABASE"))]


def block_diff(a, b):
    ca, cb = Counter(blocks(a)), Counter(blocks(b))
    return ca - cb, cb - ca


def parse(d, text):
    """→ DROP_ATTITUDE 옵션 사전. 파서가 예외로 죽으면 그 글(옛 판은 경로의 runid 글자로 int() 가 죽었다)."""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            import KooMeshModifier as K
            g = K.KooMeshModifier()
            g.SetCurrentDirectory(str(d))
            Path(d, "opt.txt").write_text(text)
            g.ImportOption("opt.txt")
        return g.modeIDOption[1]
    except Exception as e:  # noqa: BLE001
        return f"{type(e).__name__}: {e}"


def test_parse(tmp):
    print("[1] 파서 — 키 이름 전체 일치, 경로 글자 함정, 다른 키 보존, 절대 경로")
    d = Path(tmp, "parse")
    d.mkdir()
    angles = [(0, 0, 0), (30, 20, 10)]
    base = option("box.k", angles, 50, 0.002, 1e-4, "Plane,0,0,0,4,4,1")
    o0 = parse(d, base)
    rel = f"{TRAP}/runid_1_endtime.csv"
    o1 = parse(d, option("box.k", angles, 50, 0.002, 1e-4, "Plane,0,0,0,4,4,1", table=rel))
    check("경로에 다른 키 이름 글자가 든 EndTimeTable 줄을 읽음 (예외 없음)", isinstance(o1, dict), str(o1))
    o1 = o1 if isinstance(o1, dict) else {}
    check("상대 경로 → 작업폴더 기준 절대 경로", o1.get("EndTimeTable") == str(d / rel), str(o1.get("EndTimeTable")))
    rest = {k: v for k, v in o1.items() if k != "EndTimeTable"}
    check("경로의 runid·tfinal·height·density·dt 글자가 다른 키를 안 바꿈 (나머지 옵션 = 키 없을 때)", rest == o0,
          str({k: (o0.get(k), rest.get(k)) for k in set(o0) | set(rest) if o0.get(k) != rest.get(k)}))
    check("키 없으면 EndTimeTable 없음", "EndTimeTable" not in o0)
    o2 = parse(d, base.replace("**DropAttitude,1\n", "**DropAttitude,1\nENDTIMETABLE, /abs/a,b.csv \n"))
    check("대소문자 무관·앞뒤 공백·경로 안 쉼표 유지·절대 경로 그대로",
          isinstance(o2, dict) and o2.get("EndTimeTable") == "/abs/a,b.csv", str(o2))
    for bad in ("EndTimeTable,", "EndTimeTableX,/abs/t.csv", "EndTimeTabel,/abs/t.csv", "EndTimeTable;/data/height/t.csv",
                "EndTimeTable /abs/t.csv"):
        # 비슷하지만 정확하지 않은 키는 부분 문자열 검사(height·tfinal…)에 걸리기 전에 멈춘다(리뷰 R2-7 — 예전엔 Height 를 비워 IndexError)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                parse(d, base.replace("**DropAttitude,1\n", f"**DropAttitude,1\n{bad}\n"))
            code = None
        except SystemExit as e:
            code = e.code
        check(f"'{bad}' → 종료 코드 1 (빈 값·비슷한 키)", code == 1, f"{code} {out.getvalue()[-200:]}")


def test_single(tmp):
    print("[2] 한 각도 — 키 없음·같은 값 표·다른 값 표·tFinal 없이 표")
    ang, tf, dt, e = [(30, 20, 10)], 0.002, 1e-4, 0.0037
    a = Path(tmp, "s_nokey")
    rc_a, _ = run(a, option("box.k", ang, 50, tf, dt, "Plane,0,0,0,4,4,1"))
    b = Path(tmp, "s_equal")
    table(b / TRAP / "t.csv", [(30, 20, 10, tf)])
    rc_b, out_b = run(b, option("box.k", ang, 50, tf, dt, "Plane,0,0,0,4,4,1", table=f"{TRAP}/t.csv"))
    c = Path(tmp, "s_varied")
    table(c / TRAP / "t.csv", [(30, 20, 10, e)])
    rc_c, out_c = run(c, option("box.k", ang, 50, None, dt, "Plane,0,0,0,4,4,1", table=f"{TRAP}/t.csv"))
    r = Path(tmp, "s_ref")
    rc_r, _ = run(r, option("box.k", ang, 50, e, dt, "Plane,0,0,0,4,4,1"))
    check("네 실행 모두 rc 0", (rc_a, rc_b, rc_c, rc_r) == (0, 0, 0, 0), str((rc_a, rc_b, rc_c, rc_r)))
    da, db, dc, dr = (decks(x, "box") for x in (a, b, c, r))
    check("같은 값 표 = 키 없음 (바이트 동일, _drop.k)", da == db and "box_drop.k" in da, str(list(da)))
    ok, why = only_tfinal_lines_differ(da.get("box_drop.k", b""), dc.get("box_drop.k", b""), e, dt)
    check("다른 값 표: ENDTIM·D3PLOT NPLTC·INTFOR NPLTC 세 줄만 다름", ok, why)
    check("tFinal 없이 표 = 키 없이 tFinal=endtim (바이트 동일)", dc == dr)
    check("로그: 각도 한 줄 '[EndTimeTable] roll=30 pitch=20 yaw=10 ENDTIM=0.0037'",
          out_c.count("[EndTimeTable] roll=30 pitch=20 yaw=10 ENDTIM=0.0037 ") == 1, out_c[-600:])
    check("같은 값 표 로그: ENDTIM=0.002", "[EndTimeTable] roll=30 pitch=20 yaw=10 ENDTIM=0.002 " in out_b)


def fast_case(tmp, tag, surface, extra=(), singles=False):
    angles = [(0, 0, 0), (30, 20, 10), (90, 0, 0)]
    ends = [0.0013, 0.0037, 0.002]          # 셋째는 전역 tFinal 과 같다 → 그 덱은 바이트 동일이어야
    tf, dt = 0.002, 1e-4
    a = Path(tmp, f"{tag}_nokey")
    rc_a, _ = run(a, option("box.k", angles, 50, tf, dt, surface, extra=extra))
    b = Path(tmp, f"{tag}_equal")
    table(b / TRAP / "t.csv", [(r, p, y, tf) for r, p, y in angles])
    rc_b, _ = run(b, option("box.k", angles, 50, tf, dt, surface, table=f"{TRAP}/t.csv", extra=extra))
    c = Path(tmp, f"{tag}_varied")
    # 표는 낙하 방향으로 찾는다: 셋째 각도 (90,0,0) 은 같은 방향인 (0,-90,-90) 줄로, 첫째는 같은 방향 두 줄(최대 0.0013 을 써야)
    table(c / TRAP / "t.csv", [(0, 0, 0, ends[0]), (0, 0, 45, 0.0009), (30, 20, 10, ends[1]), (0, -90, -90, ends[2])])
    rc_c, out_c = run(c, option("box.k", angles, 50, tf, dt, surface, table=f"{TRAP}/t.csv", extra=extra))
    check(f"{tag}: 세 실행 rc 0", (rc_a, rc_b, rc_c) == (0, 0, 0), str((rc_a, rc_b, rc_c)))
    da, db, dc = decks(a, "box"), decks(b, "box"), decks(c, "box")
    check(f"{tag}: 각도 덱 3개 + _drop.k", len(da) == 4 and da.keys() == db.keys() == dc.keys(), str(list(dc)))
    check(f"{tag}: 같은 값 표 = 키 없음 (모든 덱 바이트 동일)", da == db)
    names = [p.name for p in angle_decks(a, "box")]
    for k, (name, e) in enumerate(zip(names, ends), 1):
        if e == tf:
            check(f"{tag}: 각도 {k} (표 값 = tFinal) 덱 바이트 동일", name in dc and da[name] == dc[name])
        else:
            ok, why = only_tfinal_lines_differ(da[name], dc.get(name, b""), e, dt)
            check(f"{tag}: 각도 {k} ENDTIM={e} — 세 줄만 다름", ok, why)
    check(f"{tag}: _drop.k 는 마지막 각도 상태(표 값 = tFinal)라 바이트 동일", da.get("box_drop.k") == dc.get("box_drop.k", b""))
    lines = [ln for ln in out_c.splitlines() if ln.startswith("[EndTimeTable] roll=")]
    check(f"{tag}: 로그 각도마다 한 줄, ENDTIM 0.0013/0.0037/0.002", len(lines) == 3 and all(
        f"ENDTIM={e:g} " in ln for ln, e in zip(lines, ends)), "\n".join(lines))
    if not singles:
        return
    # 강한 판정: Fast 각도 k 덱이 같은 각도를 단일로 tFinal=endtim_k 로 돌린 덱과 CONTROL·DATABASE 가 같고,
    # Fast·단일 사이 차이(알려진 *NODE 두 덩이·바닥 접촉 CID)가 키 없을 때와 같다
    for k, (ang, e) in enumerate(zip(angles, ends), 1):
        s0, s1 = Path(tmp, f"{tag}_single{k}_base"), Path(tmp, f"{tag}_single{k}_endtim")
        rc0, _ = run(s0, option("box.k", [ang], 50, tf, dt, surface, extra=extra))
        rc1, _ = run(s1, option("box.k", [ang], 50, e, dt, surface, extra=extra))
        f0, f1 = da[names[k - 1]], dc.get(names[k - 1], b"")
        g0, g1 = decks(s0, "box").get("box_drop.k", b""), decks(s1, "box").get("box_drop.k", b"")
        check(f"{tag}: 각도 {k} CONTROL·DATABASE = 단일 실행(tFinal={e})", rc0 == rc1 == 0 and control_db(f1) == control_db(g1))
        d0, d1 = block_diff(f0, g0), block_diff(f1, g1)
        kinds = sorted({b.splitlines()[0] for b in d1[0]} | {b.splitlines()[0] for b in d1[1]})
        check(f"{tag}: 각도 {k} Fast·단일 차이가 키 없을 때와 같음 {kinds}", d0 == d1)


def test_fast(tmp):
    print("[3] Fast DOE 세 각도 — 메시 바닥판 + 단일 실행 대조")
    fast_case(tmp, "fast", "Plane,0,0,0,4,4,1", singles=True)
    print("[4] Fast DOE 세 각도 — 강체벽 바닥")
    fast_case(tmp, "fastrw", "RigidWall,0,0,0,0,0,0", extra=("DropContact.FS,0.3",))


def test_errors(tmp):
    print("[5] 오류 — rc 1, 덱을 쓰지 않음")
    angles = [(0, 0, 0), (30, 20, 10), (90, 0, 0)]
    tf, dt = 0.002, 1e-4

    def case(tag, rows=None, raw=None, dt_=dt, tbl=f"{TRAP}/t.csv"):
        w = Path(tmp, f"err_{tag}")
        if rows is not None:
            table(w / TRAP / "t.csv", rows)
        if raw is not None:
            p = w / TRAP / "t.csv"
            p.write_text(raw(p.read_text()))
        rc, out = run(w, option("box.k", angles, 50, tf, dt_, "Plane,0,0,0,4,4,1", table=tbl))
        return rc, out, list(decks(w, "box"))

    good = [(r, p, y, tf) for r, p, y in angles]
    rc, out, ks = case("missing", rows=[good[0], good[2]])
    check("표에 없는 각도 → rc 1, 그 각도를 이름으로 알림, 덱 없음",
          rc == 1 and "🔴 [EndTimeTable] roll=30 pitch=20 yaw=10 (각도 2/3)" in out and not ks, f"rc={rc} {ks} {out[-400:]}")
    rc, out, ks = case("badnum", rows=good, raw=lambda t: t.replace(",0.002,", ",abc,", 1))
    check("숫자 아닌 endtim → rc 1 (bad number), 덱 없음", rc == 1 and "bad number" in out and not ks, f"rc={rc} {out[-300:]}")
    rc, out, ks = case("nocol", rows=good, raw=lambda t: t.replace(",endtim,", ",endtim_x,"))
    check("endtim 칸 없음 → rc 1 (missing columns), 덱 없음", rc == 1 and "missing columns" in out and not ks, f"rc={rc} {out[-300:]}")
    rc, out, ks = case("nodt", rows=good, dt_=None)
    check("dt 없음 → rc 1, 덱 없음", rc == 1 and "dt 가 없다" in out and not ks, f"rc={rc} {out[-300:]}")
    rc, out, ks = case("nofile", tbl="no_such_dir/t.csv")
    check("없는 표 파일 → rc 1, 덱 없음", rc == 1 and "표를 읽지 못했다" in out and not ks, f"rc={rc} {out[-300:]}")


def test_minimum_model(tmp):
    print("[6] MinimumModel Fast 세 각도 (있을 때만)")
    if not MINI.exists():
        print("  (Examples/MinimumModel.k 없음 — 건너뜀)")
        return
    angles = [(0, 0, 0), (30, 20, 10), (0, 90, 0)]
    ends, tf, dt = [0.0037, 0.0123, 0.005], 0.005, 1e-5
    surf = "Plane,0,0,0,10,10,2"
    a, b, c = (Path(tmp, f"mm_{t}") for t in ("nokey", "equal", "varied"))
    rc_a, _ = run(a, option("MinimumModel.k", angles, 1500, tf, dt, surf), "MinimumModel.k", MINI)
    table(b / TRAP / "t.csv", [(r, p, y, tf) for r, p, y in angles])
    rc_b, _ = run(b, option("MinimumModel.k", angles, 1500, tf, dt, surf, table=f"{TRAP}/t.csv"), "MinimumModel.k", MINI)
    table(c / TRAP / "t.csv", [(r, p, y, e) for (r, p, y), e in zip(angles, ends)])
    rc_c, _ = run(c, option("MinimumModel.k", angles, 1500, tf, dt, surf, table=f"{TRAP}/t.csv"), "MinimumModel.k", MINI)
    check("MinimumModel: 세 실행 rc 0", (rc_a, rc_b, rc_c) == (0, 0, 0), str((rc_a, rc_b, rc_c)))
    da, db, dc = (decks(x, "MinimumModel") for x in (a, b, c))
    check("MinimumModel: 같은 값 표 = 키 없음 (모든 덱 바이트 동일)", da == db and len(da) == 4, str(list(da)))
    for k, (p, e) in enumerate(zip(angle_decks(a, "MinimumModel"), ends), 1):
        if e == tf:
            check(f"MinimumModel: 각도 {k} (표 값 = tFinal) 바이트 동일", p.name in dc and da[p.name] == dc[p.name])
        else:
            ok, why = only_tfinal_lines_differ(da[p.name], dc.get(p.name, b""), e, dt)
            check(f"MinimumModel: 각도 {k} ENDTIM={e} — 세 줄만 다름", ok, why)


def test_table_checks(tmp):
    print("[7] 표 대조 — v0(낙하 속도)·순수 낙하·tFinal 넘는 ENDTIM 경고·바닥판 reach 경고")
    v = math.sqrt(2 * 9810 * 50)

    def case(tag, meta=None, extra=None, endtim=0.0051, surface="Plane,0,0,0,4,4,1", repl=None):
        w = Path(tmp, f"tc_{tag}")
        table(w / "t.csv", [(30, 20, 10, endtim)], meta=meta, extra=extra)
        text = option("box.k", [(30, 20, 10)], 50, 0.002, 1e-4, surface, table="t.csv")
        if repl:
            text = text.replace(*repl)
        rc, out = run(w, text)
        return rc, out, decks(w, "box")

    rc, out, ds = case("v0_ok", meta={"v0": f"{v:.10g}"})
    check("v0 = √(2gh) → rc 0, 확인 줄", rc == 0 and "[EndTimeTable] v0=" in out and ds, out[-300:])
    check("ENDTIM 0.0051 > tFinal 0.002 → WARNING 한 줄 (x2.55)",
          out.count("[EndTimeTable] WARNING max ENDTIM=0.0051 (x2.55 of tFinal) — raise time limits") == 1, out[-400:])
    rc, out, ds = case("v0_bad", meta={"v0": f"{math.sqrt(2 * 9810 * 1500):.10g}", "height": "1500"})
    check("v0 = 높이 1500 의 속도 → rc 1 V0_MISMATCH, 덱 없음", rc == 1 and "V0_MISMATCH" in out and not ds, out[-300:])
    check("V0_MISMATCH 줄에 양쪽 높이·g (표 height 1500·g 9810 / 이 낙하 Height 50·g 9810)",
          "(height 1500, g 9810) vs this drop √(2gh) 990.454 (Height 50, g 9810)" in out, out[-400:])
    rc, out, ds = case("not_pure", meta={"v0": f"{v:.10g}"}, repl=("InitialVelocityX,0", "InitialVelocityX,100"))
    check("v0 + InitialVelocityX 100 → rc 1 NOT_PURE_DROP, 덱 없음", rc == 1 and "NOT_PURE_DROP" in out and not ds, out[-300:])
    rc, out, ds = case("eq_tf", endtim=0.002)
    check("ENDTIM = tFinal, v0 없음 → rc 0, 경고·v0 줄 없음", rc == 0 and "WARNING max ENDTIM" not in out and "v0=" not in out and ds,
          out[-300:])
    rc, out, ds = case("reach_far", extra={"reach": 20.0})
    check("Plane(자동 한 변 15 → 반폭 7.5)·reach 20 → 각도 WARNING + 요약, rc 0",
          rc == 0 and "WARNING plate reach" in out and "WARNING plate too small for 1/1 angles" in out and ds, out[-500:])
    rc, out, ds = case("reach_ok", extra={"reach": 3.0})
    check("reach 3 < 반폭 7.5 → 경고 없음", rc == 0 and "WARNING plate" not in out and ds, out[-300:])
    rc, out, ds = case("reach_rw", extra={"reach": 20.0}, surface="RigidWall,0,0,0,0,0,0")
    check("RigidWall(무한 평면)·reach 20 → 경고 없음", rc == 0 and "WARNING plate" not in out and ds, out[-300:])


def parse_out(d, text):
    """옵션 글을 KMM ImportOption 으로 읽는다 → (종료 코드 또는 None, stdout)."""
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            import KooMeshModifier as K
            g = K.KooMeshModifier()
            g.SetCurrentDirectory(str(d))
            Path(d, "opt.txt").write_text(text)
            g.ImportOption("opt.txt")
        return None, out.getvalue()
    except SystemExit as e:
        return e.code, out.getvalue()


def test_rde_option_traps(tmp):
    print("[8] RIGID_DROP_ENDTIME 옵션 함정 — 다른 모드와 함께·두 번·끝줄 없음 → 종료 코드 1")
    d = Path(tmp, "rde_traps")
    d.mkdir()
    full = option("box.k", [(0, 0, 0)], 50, 0.002, 1e-4, "Plane,0,0,0,4,4,1")
    drop2 = full[full.index("**DropAttitude,1"):full.index("**EndDropAttitude")].replace("**DropAttitude,1", "**DropAttitude,2")
    drop2 += "**EndDropAttitude\n"

    def rde(i, end=True):
        return f"**RigidDropEndtime,{i}\nHeight,1500\nFibonacci,10\n" + ("**EndRigidDropEndtime\n" if end else "")

    head = "*Inputfile\nbox.k\n*Mode\n"
    cases = [
        ("DROP_ATTITUDE 와 함께", head + "RIGID_DROP_ENDTIME,1\nDROP_ATTITUDE,2\n" + rde(1) + drop2 + "*End\n", 1, "must run alone"),
        ("두 번", head + "RIGID_DROP_ENDTIME,1\nRIGID_DROP_ENDTIME,2\n" + rde(1) + rde(2) + "*End\n", 1, "must run alone"),
        ("끝줄 없이 *End", head + "RIGID_DROP_ENDTIME,1\n" + rde(1, end=False) + "*End\n", 1, "missing **EndRigidDropEndtime"),
        ("끝줄 없이 다음 블록", head + "RIGID_DROP_ENDTIME,1\nDROP_ATTITUDE,2\n" + rde(1, end=False) + drop2 + "*End\n", 1,
         "missing **EndRigidDropEndtime"),
        ("혼자·끝줄 있음", head + "RIGID_DROP_ENDTIME,1\n" + rde(1) + "*End\n", None, ""),
    ]
    for tag, text, want, msg in cases:
        code, out = parse_out(d, text)
        check(f"{tag} → 종료 코드 {want}{(' ' + msg) if msg else ''}", code == want and msg in out, f"{code} {out[-300:]}")


def test_rde_rc3(tmp):
    print("[9] RIGID_DROP_ENDTIME 이 rc 3 으로 끝날 때 — 표는 썼지만 리더가 버린 파트를 알리는 줄")
    import importlib.util
    if importlib.util.find_spec("pybullet") is None:
        print("  (pybullet 없음 — 건너뜀)")
        return
    w = Path(tmp, "rde_rc3")
    w.mkdir()
    box_model(w / "box.k")
    f10 = lambda *v: "".join(f"{str(x):>10s}" for x in v)  # noqa: E731
    text = (w / "box.k").read_text().replace("*NODE", "\n".join(   # *PART_INERTIA 파트 — 리더가 그 파트의 요소를 버린다
        ["*PART_INERTIA", "INERTIA_BLOCK", f10(3, 1, 1), f10("6.25", "6.25", "1.5", "1.0e-6", 0, 0),
         f10("1.0e-6", "0.0", "0.0", "1.0e-6", "0.0", "1.0e-6"), f10("0.0", "0.0", "0.0", "0.0", "0.0", "0.0")]) + "\n*NODE", 1)
    lines = text.splitlines()
    i = lines.index("*ELEMENT_SOLID") + 1
    lines[i] = lines[i][:8] + f"{3:8d}" + lines[i][16:]
    (w / "box.k").write_text("\n".join(lines) + "\n")
    rc, out = run(w, "*Inputfile\nbox.k\n*Mode\nRIGID_DROP_ENDTIME,1\n**RigidDropEndtime,1\nHeight,50\nAngle,A,30,20,10\n"
                     "Restitution,0.3\nWorkers,1\nPresimTMax,0.2\n**EndRigidDropEndtime\n*End\n")
    check("rc 3, '[RIGID_DROP_ENDTIME] tables were written' 줄, 표는 있음",
          rc == 3 and "[RIGID_DROP_ENDTIME] tables were written" in out and (w / "box_endtime.csv").exists(), f"rc={rc} {out[-500:]}")


def main():
    tmp = tempfile.mkdtemp(prefix="drop_endtime_tbl_")
    test_parse(tmp)
    test_single(tmp)
    test_fast(tmp)
    test_errors(tmp)
    test_minimum_model(tmp)
    test_table_checks(tmp)
    test_rde_option_traps(tmp)
    test_rde_rc3(tmp)
    print()
    if FAILS:
        print("FAIL %d 건 (작업 폴더 %s 를 남긴다)" % (len(FAILS), tmp))
        for x in FAILS:
            print("  -", x)
        sys.exit(1)
    shutil.rmtree(tmp, ignore_errors=True)
    print("ALL PASS")


if __name__ == "__main__":
    main()
