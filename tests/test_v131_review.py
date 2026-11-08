# KMM v131 적대 리뷰 R1~R3 가 찾은 결함을 리뷰어가 본 실패 그대로 다시 보는 회귀 시험 — 콤마·long 카드, 번호 예약, Fast DROP, IMPORT_MERGE_K, 좌표계, DECOMPOSE·DWI·DTI
"""
실행: venv312/bin/python tests/test_v131_review.py   (KMM 약 40회, 3~6분)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-11-04, 남은 기존 결함 묶음 v131 의 적대 리뷰 R1~R3 — 재현 덱은 /data/koopark/review_v131_R{1,2,3}/)
  R1 콤마 요소 줄의 뒤쪽 절점이 조용히 잘렸다(육면체가 쐐기로, I10 블록은 줄째 버림). DATABASE_HISTORY 콤마 줄도 잘렸다.
     long('+') 사용자 단면(ELFORM 101~105) 카드가 20칸 그대로 나갔다. 한 블록 여러 카드의 강체 처방 운동은 첫 카드만 남았다.
     *PART_CONTACT 끝 파트의 빈 접촉 카드 하나로 블록 전체가 원문이 됐다. 콤마 ID 카드는 traceback. DEATH·BIRTH 는 유효숫자 4자리.
     접촉 블록 끝 빈 줄이 선택 카드 A 로 나갔다. 'D' 지수 절점을 읽지 못해 rc 0 으로 버렸다.
  R2 원문 *PART_* 블록의 둘째 파트부터, 원문 요소의 실수 칸까지 번호로 예약했다(바닥판 EID 가 11자리). 여러 각도 DROP 바닥판이
     모델과 같은 EID·각도마다 다른 PID 를 썼다. IMPORT_MERGE_K 가 I10 클래스 기본값을 되돌려 가져온 파트를 8칸으로 썼다.
     D2R 이 원문·매니저 판으로 두 번 나갔다. 4·8절점이 섞인 *ELEMENT_SHELL_THICKNESS 블록에서 죽었다.
  R3 IMPORT_MERGE_K — 가져온 접촉에서 죽고, PID 없는 질량·요소 셋을 덮고, 기준 덱 원문 단면·재질 번호와 겹치고, 같은 MID 다른
     재질·*INCLUDE_TRANSFORM 을 알림 없이 버렸다. 좌표계 _TITLE·곡선 SFA 빈칸을 충돌로 봤다. *DEFINE_COORDINATE_SYSTEM 은 어느
     출력에도 없었다. DECOMPOSE_K ModelIndependentSplit False 가 CONTROL·DATABASE 를 잃었다. 복합재 파트에서 DWI OutsideRigid 가
     죽었다(고쳐도 E·PR 이 뒤바뀜). 같은 모드 ID 옵션 블록 두 벌이 조용히 덮였다. sphere 워커 0.5 GB 가 x.5 GB 요청을 만들었다.
     DTI 가 dynain 이 싣지 않는 *INITIAL_STRESS_SECTION 까지 지웠다. *NODE 없이 설정만 든 덱을 가져오면 KeyError 로 죽었다.
     *SET_NODE_LIST_GENERATE 가 든 덱은 모든 모드가 쓰기에서 죽었다(읽을 때 NSID 도 버렸다).
  좌표계를 출력에 쓰기 시작하며 TRANSFORM(회전·이동·대칭·확대)이 좌표계 점을 옮기지 않던 것도 이 시험을 쓰다 막았다.
  같은 번호 같은 내용의 재질을 IMPORT_MERGE_K 가 충돌로 본 것(재질 비교 글이 늘 비었다)과, 첫 요소가 삼각형인 두께 블록에서 뒤
  사각형의 N4 가 잘리던 것은 이 시험을 쓰다 찾았다.
  콤마 원문 카드(*MAT_ADD_EROSION·SECTION_BEAM)의 빈 칸이 사라져 값이 앞 칸으로 당겨지던 것은 말뭉치 W7 이 찾았다.
  R4 처방 운동 카드 3 을 가짜 조건으로 읽었다. 가져온 질량 절점 셋 번호가 밀리지 않았다. 일반 셸·HISTORY 가 첫 줄 길이로 칸 수를
     정해 뒤 줄 값이 잘렸다. 콤마 줄의 남는 값이 다음 카드로 밀렸다. Fast DROP 강체화가 각도마다 어긋났다. IMPORT_MERGE_K 가
     TMID 를 MID 로 보고, 원문 EOS·좌표계·long 단면 번호와 기준 덱만의 침식을 놓치고, 재질을 유효숫자 4자리로 견줬다. DTI 가
     바꿀 것 없는 셸 응력을 지웠다. DROP 바닥판 단면·재질·D2R SWSET 이 원문 번호와 겹쳤다.
  R5 콤마 빈 값을 공백으로 바꿔 빈 칸을 len()==0 으로 가리는 리더가 죽었다. 셸 끝 칸이 8자를 못 채우면 버렸다. 솔리드 둘째 줄이
     짧으면 블록을 2줄 꼴로 뒤섞었다. GENERAL_VISCOELASTIC 카드 2 를 4칸으로 읽었다. IMPORT_MERGE_K 가 침식 카드 3 의 다름을
     놓치고, 쓰지 않는 MID 에 거짓 충돌을 내고, 원문 좌표계 첫 줄만 봤다. 누적 체인에서 D2R 짝이 두 쌍이 됐다.
  R6 DTI *RemovePartbyID 가 MSTYP 3 인 접촉을 모두 지웠다. 지운 접촉의 덱 D2R 을 지울 때 강체벽 CODE 1·3 까지, 지우지 못한 원문
     접촉의 D2R 까지 지웠고 짝 한쪽을 남겼다. IMPORT_MERGE_K 가 IDAM 0 침식 카드 3 의 뜻 없는 칸·빈 칸 대 기본값을 다르다고 봤다.
     81열 뒤 글자로 솔리드 블록이 모두 빠졌고, I10 셸·솔리드·빔 끝 칸이 10자를 못 채우면 버렸다. 번호 없는 강체벽이 _ID 1 에
     덮였다. 원문 침식 카드 줄 끝에 공백이 붙은 것은 말뭉치 W9·V9 가 찾았다.
  R7 'or' 를 고치자 DWI 다음 단계 DTI 에 DWI 벽·임팩터 접촉이 남았다(DWI 는 임팩터 파트만 지우라고 적었다). 겹친 강체벽을 끝으로
     옮겨 벽 차례가 바뀌었다. *MAT_084_REINF·*MAT_T01 별칭을 재질 MID 로 읽었다. IDAM≠0 침식 끝 빈 줄로 거짓 rc 3 이었다. D2R 닫힘이
     PAIRED 0 세트를 따라가 사용자 짝을 지웠고, DROP 은 long D2R SWSET 을 10칸으로 읽었다. 여러 각도 DROP 의 RigidWall 바닥은
     DropSet.k 에 없었다(v130 부터).
  R8 RobustContact 의 TIED 면 찾기가 각도 번호 i 를 덮어 RunID 를 준 여러 각도가 Run 폴더 하나에 겹쳤다(v130 부터). 원문
     접촉의 CID 를 예약하지 않아 KMM 바닥판·DWI 접촉이 같은 번호를 받았고(실제 덱 KooRemapper 예제), DTI 가 그 번호를
     지울 때 원문 접촉의 D2R 까지 지웠다.
"""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = Path(os.environ.get("KMM_GEN", ROOT / "occProject" / "Generators"))
PY = str(ROOT / "venv312" / "bin" / "python")
KMM_CMD = [os.environ["KMM_BIN"]] if os.environ.get("KMM_BIN") else [PY, str(GEN / "KooMeshModifier.py")]
ENV = dict(os.environ, PATH=str(ROOT / "venv312" / "bin") + ":" + os.environ.get("PATH", ""))
FAILS = []
TRANS = "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,0,0,0\n**EndTransform\n*End\n"
IMO = "*Inputfile\nbase.k\n*Mode\nIMPORT_MERGE_K,1\n**ImportMergeK,1\nImportFile,imp.k\n**End\n*End\n"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v131_modes as M   # noqa: E402 — base_deck·parts_of 를 같이 쓴다(그 시험의 덱과 같아야 리뷰 재현과 같다)


def check(name, cond, detail=""):
    print("  %-96s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def run(name, files, opt=TRANS):
    d = Path(tempfile.mkdtemp(prefix=f"v131r_{name}_", dir=os.environ.get("V131_TMP") or None))
    for fn, text in files.items():
        (d / fn).write_text(text)
    (d / "opt.txt").write_text(opt.replace("@D@", str(d)))
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=1200, env=ENV)
    return d, r.returncode, r.stdout + r.stderr


def read(d, name):
    p = Path(d) / name
    return p.read_text(errors="replace") if p.exists() else ""


def no_tb(log):
    return "Traceback (most recent call last)" not in log


# ── 출력 읽기(칸 폭은 머리 줄 '%'·'+'·'-' 와 *KEYWORD I10=Y 로) ─────────────────────────────────────────
def deck_i10(text):
    for ln in text.splitlines():
        if ln.startswith("*"):
            u = ln.upper().replace(" ", "")
            return u.startswith("*KEYWORD") and "I10=Y" in u
    return False


def width(header, i10):
    p = header.split()[1:]
    return 20 if "+" in p else 10 if "%" in p else 8 if "-" in p else (10 if i10 else 8)


def kw_blocks(text, kw):
    """정확히 kw 인 키워드 블록마다 (머리 줄, 데이터 줄 — 주석·빈 줄 뺌)."""
    out, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("*"):
            cur = None
            if ln.split()[0].upper() == kw:
                cur = []
                out.append((ln, cur))
            continue
        if cur is not None and ln.strip() and not ln.startswith("$"):
            cur.append(ln)
    return out


def ints(s, w):
    s = s.rstrip()
    return [int(s[k:k + w]) if s[k:k + w].strip() else 0 for k in range(0, len(s), w)]


def floats(s, w):
    s = s.rstrip()
    return [float(s[k:k + w]) if s[k:k + w].strip() else 0.0 for k in range(0, len(s), w)]


def elements(text, kw="*ELEMENT_SOLID"):
    """{EID: [(PID, 절점…)]} — 같은 EID 가 둘이면 목록이 길다. 칸 폭으로 읽지 못하는 줄(칸이 넘친 번호)은 EID -1 로 모은다."""
    i10, out = deck_i10(text), {}
    for h, rows in kw_blocks(text, kw):
        w = width(h, i10)
        for r in rows:
            try:
                f = ints(r, w)
            except ValueError:
                out.setdefault(-1, []).append((None, r))
                continue
            out.setdefault(f[0], []).append((f[1], f[2:]))
    return out


def nodes(text):
    i10, out = deck_i10(text), {}
    for h, rows in kw_blocks(text, "*NODE"):
        w = width(h, i10)
        for r in rows:
            out[int(r[:w])] = tuple(float(r[w + 16 * k:w + 16 * (k + 1)]) for k in range(3))
    return out


def thick_shells(text):
    """*ELEMENT_SHELL_THICKNESS → {EID: (절점 N1~N8, 두께 THIC…)} — 두께 카드는 N5 가 있으면 2장."""
    i10, out = deck_i10(text), {}
    for h, rows in kw_blocks(text, "*ELEMENT_SHELL_THICKNESS"):
        w, k = width(h, i10), 0
        while k < len(rows):
            f = ints(rows[k], w)
            ns = (f[2:] + [0] * 8)[:8]
            n = 2 if ns[4] > 0 else 1
            th = [x for r in rows[k + 1:k + 1 + n] for x in floats(r, 16)]
            out[f[0]] = (ns, th)
            k += 1 + n
    return out


def try_(f, default=None):
    """판정용 읽기 — 수정 전 코드의 깨진 출력(칸이 넘친 번호 등)에서 시험이 죽지 않고 FAIL 로 센다."""
    try:
        return f()
    except (ValueError, IndexError, TypeError):
        return default


def near(a, b, rel=1e-6):
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-30)


# ── 덱 조각 ────────────────────────────────────────────────────────────────────────────────────────────
CUBE = ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1))
ELASTIC = "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000.0, 0.3)
SOLID1 = "*SECTION_SOLID\n" + f10(1, 1)


def cubes(n, first=1, dx=2.0):
    """육면체 n 개의 절점 — 육면체 k 는 절점 first+8k ~ first+8k+7."""
    return {first + 8 * k + j: (x + dx * k, y, z) for k in range(n) for j, (x, y, z) in enumerate(CUBE)}


def node_block(pts, w=8):
    return "*NODE\n" + "".join(f"{i:{w}d}{x:16.6f}{y:16.6f}{z:16.6f}\n" for i, (x, y, z) in sorted(pts.items()))


def hex_row(eid, pid, n0, w=8):
    return f"{eid:{w}d}{pid:{w}d}" + "".join(f"{n0 + j:{w}d}" for j in range(8)) + "\n"


def part(pid, secid=1, mid=1, name=None):
    return f"*PART\n{name or f'part{pid}'}\n" + f10(pid, secid, mid)


def cube_deck(extra="", n=1):
    """파트 1(솔리드) 육면체 n 개 + extra."""
    return ("*KEYWORD\n" + node_block(cubes(n)) + "*ELEMENT_SOLID\n" + "".join(hex_row(k + 1, 1, 8 * k + 1) for k in range(n))
            + part(1) + SOLID1 + ELASTIC + extra + "*END\n")


def drop(rolls, extra=""):
    """여러 각도 DROP_ATTITUDE 옵션(각도 = 롤 목록) — extra 는 **DropAttitude 블록 끝에 더할 줄."""
    k = len(rolls)
    rep = lambda v: ",".join([str(v)] * k)
    return ("*Inputfile\nmodel.k\n*RunDirectoryMode,True,runs\n*Mode\nDROP_ATTITUDE,1\n**DropAttitude,1\n"
            f"EulerRolling,{','.join(map(str, rolls))}\nEulerPitching,{rep(0)}\nEulerYawing,{rep(0)}\nHeight,{rep(100)}\n"
            f"InitialVelocityX,{rep(0)}\nInitialVelocityY,{rep(0)}\nInitialVelocityZ,{rep(0)}\nInitialAngularVelocityX,{rep(0)}\n"
            f"InitialAngularVelocityY,{rep(0)}\nInitialAngularVelocityZ,{rep(0)}\nOffsetDistance,0.05\nDensity,7.85e-9\n"
            "YoungsModulus,2.0e5\nPoissonRatio,0.3\ntFinal,0.001\ndt,1e-6\n" + extra + "**EndDropAttitude\n*End\n")


def dropsets(d):
    return [p.read_text(errors="replace") for p in sorted(Path(d).rglob("DropSet.k")) if p.parent.parent.name == "runs"]


def part_cards(text):
    """*PART(_TITLE) → {PID: (SECID, MID)}."""
    out, lines = {}, text.splitlines()
    for i, ln in enumerate(lines):
        if ln.split()[:1] and ln.split()[0].upper() in ("*PART", "*PART_TITLE"):
            data = [x for x in lines[i + 1:i + 6] if not x.startswith("$")]
            if len(data) >= 2:
                f = try_(lambda: [int(float(data[1][k:k + 10])) for k in (0, 10, 20)], None)
                if f:
                    out[f[0]] = (f[1], f[2])
    return out


def r1():
    print("[R1] 콤마·long 카드, 강체 처방 운동, *PART_CONTACT, 콤마 ID 카드, DEATH·BIRTH, 접촉 빈 카드 A, 'D' 지수 절점")
    # ── 콤마 요소 줄: 뒤쪽 절점이 잘리지 않는다(R1-1·4) ───────────────────────────────────────────────
    pts = {100001 + j: p for j, p in enumerate(CUBE)}
    deck = ("*KEYWORD\n" + node_block(pts) + part(1) + SOLID1 + ELASTIC + "*ELEMENT_SOLID\n100001,1,"
            + ",".join(str(100001 + j) for j in range(8)) + "\n*END\n")
    d, rc, log = run("c_solid2", {"model.k": deck})
    e = elements(read(d, "model_trans.k"))
    check("R1 콤마 *ELEMENT_SOLID(7자리 ID): 육면체 절점 8개가 그대로(쐐기가 되지 않는다)",
          rc == 0 and e.get(100001) == [(1, list(range(100001, 100009)))], f"rc={rc} {e} " + log[-300:])
    d, rc, log = run("c_solid", {"model.k": cube_deck().replace(hex_row(1, 1, 1), "1,1,1,2,3,4,5,6,7,8\n")})
    e = elements(read(d, "model_trans.k"))
    check("R1 짧은 콤마 *ELEMENT_SOLID(1,1,1,2,…): EID 칸에서 죽지 않고 절점 8개", rc == 0 and e.get(1) == [(1, list(range(1, 9)))],
          f"rc={rc} {e} " + log[-300:])
    pts = {1000001 + j: (x, y, 0.0) for j, (x, y, z) in enumerate(CUBE[:4])}
    deck = ("*KEYWORD\n" + node_block(pts) + part(2, 2, 1) + "*SECTION_SHELL\n" + f10(2, 2, 0.8333, 2) + f10(0.5, 0.5, 0.5, 0.5)
            + ELASTIC + "*ELEMENT_SHELL\n1000001,2,1000001,1000002,1000003,1000004\n*END\n")
    d, rc, log = run("c_shell3", {"model.k": deck})
    e = elements(read(d, "model_trans.k"), "*ELEMENT_SHELL").get(1000001, [(0, [])])
    check("R1 콤마 *ELEMENT_SHELL: 사각형이 삼각형이 되지 않는다(N4 = 1000004)",
          rc == 0 and len(e) == 1 and e[0][1][:4] == [1000001, 1000002, 1000003, 1000004] and not any(e[0][1][4:]),
          f"rc={rc} {e} " + log[-300:])
    d, rc, log = run("c_hist", {"model.k": cube_deck("*DATABASE_HISTORY_NODE\n100,200,300,400,500,600,700,800\n")})
    h = [x for _, rows in kw_blocks(read(d, "model_trans.k"), "*DATABASE_HISTORY_NODE") for r in rows for x in ints(r, 10) if x]
    check("R1 콤마 *DATABASE_HISTORY_NODE 8개 값: 모두 남는다(100 200 300 만이 아니다)",
          rc == 0 and h == [100, 200, 300, 400, 500, 600, 700, 800], f"rc={rc} {h}")
    deck = ("*KEYWORD I10=Y\n" + node_block(cubes(2), 10) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1, 10)
            + "2,1," + ",".join(str(9 + j) for j in range(8)) + "\n" + part(1) + SOLID1 + ELASTIC + "*END\n")
    d, rc, log = run("c_i10solid", {"model.k": deck})
    e = elements(read(d, "model_trans.k"))
    check("R1 *KEYWORD I10=Y 덱 *ELEMENT_SOLID 의 콤마 줄: 버려지지 않는다(요소 2 = 절점 9~16)",
          rc == 0 and e.get(1) == [(1, list(range(1, 9)))] and e.get(2) == [(1, list(range(9, 17)))], f"rc={rc} {e} " + log[-300:])

    # ── 콤마 원문 카드의 빈 칸·긴 값(말뭉치 W7 에서 찾음): 원문 카드를 칸 이어 다시 만들 때 빈 칸이 사라져 값이 당겨졌다 ──
    d, rc, log = run("comma_raw", {"model.k": cube_deck("*MAT_ADD_EROSION\n1,,,,,0.000123456789,1.0,1.0\n,,,0.3\n")})
    rows = [r for _, rr in kw_blocks(read(d, "model_trans.k"), "*MAT_ADD_EROSION") for r in rr]
    v1 = try_(lambda: floats(rows[0], 10), [])
    v2 = try_(lambda: floats(rows[1], 10), [])
    check("R1 콤마 *MAT_ADD_EROSION '1,,,,,0.000123456789,1.0,1.0 / ,,,0.3': VOLEPS·NUMFIP·NCS·MXEPS 가 제 칸(빈 칸이 사라지지 않는다)",
          rc == 0 and len(v1) >= 8 and v1[0] == 1 and v1[1:5] == [0, 0, 0, 0] and near(v1[5], 1.23457e-4, 1e-5)
          and v1[6:8] == [1.0, 1.0] and len(v2) >= 4 and v2[:4] == [0, 0, 0, 0.3], f"rc={rc} {rows}")

    # ── long('+') 사용자 단면 카드: 20칸 그대로 나가지 않는다(R1-2) ───────────────────────────────────────
    def l20(*v):
        return "".join(f"{x:>20}" for x in v) + "\n"
    deck = cube_deck(part(2, 5, 1, "usersolid") + part(3, 7, 1, "usershell")
                     + "*SECTION_SOLID +\n" + l20(5, 101) + l20(1, 0, 0, 0, 4, 0) + l20(0.0, 0.0, 0.0, 8.0) + l20(210.0, 0.3, 1.5, 2.5)
                     + "*SECTION_SHELL +\n" + l20(7, 101, 1.0, 2) + l20(1.0, 1.0, 1.0, 1.0) + l20(1, 0, 0, 0, 0, 2)
                     + l20(0.0, 0.0, 2.0) + l20(70.0, 0.25))
    d, rc, log = run("usr_long", {"model.k": deck})
    t = read(d, "model_trans.k")

    def sec_cards(kw, secid):
        for h, rows in kw_blocks(t, kw) + kw_blocks(t, kw + "_TITLE"):
            rows = rows[1:] if h.split()[0].upper().endswith("_TITLE") else rows
            w = 20 if "+" in h.split()[1:] else 10
            if rows and floats(rows[0], w)[:1] == [float(secid)]:
                return [floats(r, w) for r in rows]
        return []
    s5, s7 = sec_cards("*SECTION_SOLID", 5), sec_cards("*SECTION_SHELL", 7)
    check("R1 long *SECTION_SOLID ELFORM 101: 사용자 카드(NIP 1·LMC 4, 적분점, P1~P4)를 머리 줄 폭으로 읽으면 값이 같다",
          rc == 0 and len(s5) >= 4 and s5[1][:6] == [1, 0, 0, 0, 4, 0] and s5[2][:4] == [0, 0, 0, 8.0]
          and s5[3][:4] == [210.0, 0.3, 1.5, 2.5], f"rc={rc} {s5}")
    check("R1 long *SECTION_SHELL ELFORM 101: 사용자 카드(NIPP 1·LMC 2, 적분점, P1·P2)도 같다",
          rc == 0 and len(s7) >= 5 and s7[2][:6] == [1, 0, 0, 0, 0, 2] and s7[3][:3] == [0, 0, 2.0] and s7[4][:2] == [70.0, 0.25],
          f"rc={rc} {s7}")

    # ── 한 블록 여러 카드의 강체 처방 운동(R1-3) ─────────────────────────────────────────────────────────
    rig = ("*KEYWORD\n" + node_block(cubes(3)) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1) + hex_row(2, 4, 9) + hex_row(3, 5, 17)
           + part(1) + part(4, 1, 4) + part(5, 1, 5) + SOLID1 + ELASTIC
           + "*MAT_RIGID\n" + f10(4, "7.85E-09", 210000.0, 0.3) + "*MAT_RIGID\n" + f10(5, "7.85E-09", 210000.0, 0.3)
           + "*DEFINE_CURVE\n" + f10(10) + f"{0.0:20.4f}{0.0:20.4f}\n{1.0:20.4f}{1.0:20.4f}\n"
           + "*BOUNDARY_PRESCRIBED_MOTION_RIGID\n" + f10(4, 3, 2, 10, 0.5) + f10(5, 1, 0, 10, 2.0)
           + "*BOUNDARY_PRESCRIBED_MOTION_RIGID_ID\n" + f"{71:10d}pm_a\n" + f10(4, 3, 2, 10, 0.5) + f"{72:10d}pm_b\n" + f10(5, 1, 0, 10, 2.0)
           + "*END\n")
    d, rc, log = run("feat1", {"model.k": rig})
    t = read(d, "model_trans.k")
    # KMM 은 처방 운동을 모두 _ID 꼴(번호를 매겨)로 쓴다 — _ID 없는 블록의 조건은 71·72 가 아닌 번호로 나온다
    pairs = [(None, int(r[:10])) for _, rows in kw_blocks(t, "*BOUNDARY_PRESCRIBED_MOTION_RIGID") for r in rows]
    pairs += [(int(rows[k][:10]), int(rows[k + 1][:10])) for _, rows in kw_blocks(t, "*BOUNDARY_PRESCRIBED_MOTION_RIGID_ID")
              for k in range(0, len(rows) - 1, 2)]
    plain = sorted(p for i, p in pairs if i not in (71, 72))
    check("R1 *BOUNDARY_PRESCRIBED_MOTION_RIGID 한 블록 두 카드: PID 4·5 가 모두 남는다", rc == 0 and plain == [4, 5], f"rc={rc} {pairs}")
    check("R1 *BOUNDARY_PRESCRIBED_MOTION_RIGID_ID 한 블록 두 쌍: (71, PID 4)·(72, PID 5)",
          rc == 0 and sorted(x for x in pairs if x[0] in (71, 72)) == [(71, 4), (72, 5)], f"rc={rc} {pairs}")

    # ── *PART_CONTACT 끝 파트의 빈 접촉 카드(R1-5) ────────────────────────────────────────────────────
    deck = ("*KEYWORD\n" + node_block(cubes(2)) + "*PART_CONTACT\npartA\n" + f10(1, 1, 1) + f10(0.3, 0.2, 0, 0, 0, 0, 0, 0)
            + "partB\n" + f10(2, 1, 1) + "\n" + SOLID1 + ELASTIC + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1) + hex_row(2, 2, 9) + "*END\n")
    d, rc, log = run("pc2", {"model.k": deck})
    e = elements(read(d, "model_trans.k"))
    check("R1 *PART_CONTACT 끝 파트 접촉 카드가 빈 줄: 파트 2개로 읽고 요소가 빠지지 않는다(rc 0)",
          rc == 0 and e.get(1) == [(1, list(range(1, 9)))] and e.get(2) == [(2, list(range(9, 17)))], f"rc={rc} {e} " + log[-300:])

    # ── 콤마 ID 카드(R1-6) ─────────────────────────────────────────────────────────────────────────────
    deck = ("*KEYWORD\n" + node_block(cubes(2)) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1) + hex_row(2, 2, 9) + part(1) + part(2)
            + SOLID1 + ELASTIC + "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID\n8,auto contact\n" + f10(1, 2, 3, 3) + f10(0.1, 0.1)
            + f10(1.0, 1.0) + "*END\n")
    d, rc, log = run("id_comma", {"model.k": deck})
    c = kw_blocks(read(d, "model_trans.k"), "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID")
    check("R1 콤마 ID 카드 '8,auto contact': 죽지 않고 CID 8·제목이 남는다",
          rc == 0 and no_tb(log) and len(c) == 1 and int(c[0][1][0][:10]) == 8 and "auto contact" in c[0][1][0],
          f"rc={rc} {c} " + log[-300:])

    # ── DEATH·BIRTH 정밀도(R1-7) ───────────────────────────────────────────────────────────────────────
    d, rc, log = run("pm_db", {"model.k": cube_deck("*DEFINE_CURVE\n" + f10(10) + f"{0.0:20.4f}{0.0:20.4f}\n{1.0:20.4f}{1.0:20.4f}\n"
                                                     + "*BOUNDARY_PRESCRIBED_MOTION_NODE\n"
                                                     + f10(7, 3, 2, 10, 1.0, 0, "0.0123456", "0.00012345"))})
    rows = [r for _, rr in kw_blocks(read(d, "model_trans.k"), "*BOUNDARY_PRESCRIBED_MOTION_NODE") for r in rr]
    v = floats(rows[0], 10) if rows else []
    check("R1 처방 운동 DEATH 0.0123456·BIRTH 0.00012345: 유효숫자가 깎이지 않는다",
          rc == 0 and len(v) >= 8 and near(v[6], 0.0123456) and near(v[7], 0.00012345), f"rc={rc} {rows}")

    # ── 접촉 블록 끝 빈 줄은 선택 카드 A 가 아니다(R1-8) ──────────────────────────────────────────────────
    d, rc, log = run("reg1", {"model.k": cube_deck("*SET_PART_LIST\n" + f10(1) + f10(1) + "*CONTACT_AUTOMATIC_SINGLE_SURFACE\n"
                                                    + f10(1, 0, 2, 0) + f10(0.1, 0.1) + f10(1.0, 1.0) + "\n")})
    t = read(d, "model_trans.k")
    # KMM 은 접촉을 _ID 꼴로 쓴다 — ID 카드를 빼고 센다
    c = [rows for _, rows in kw_blocks(t, "*CONTACT_AUTOMATIC_SINGLE_SURFACE")]
    c += [rows[1:] for _, rows in kw_blocks(t, "*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID")]
    seg = t.split("*CONTACT_AUTOMATIC_SINGLE_SURFACE", 1)[-1].split("\n*", 1)[0]
    check("R1 접촉 카드 1~3 뒤 빈 줄: 선택 카드 A(SOFT…)가 새로 생기지 않는다",
          rc == 0 and len(c) == 1 and len(c[0]) == 3 and "SOFT" not in seg, f"rc={rc} {c}")

    # ── 'D' 지수 절점과 읽지 못한 절점 줄(R1-9) ─────────────────────────────────────────────────────────
    d, rc, log = run("node_d", {"model.k": cube_deck().replace("*ELEMENT_SOLID", "99,1.0D-03,0.0,0.0\n*ELEMENT_SOLID", 1)})
    nd = nodes(read(d, "model_trans.k"))
    check("R1 *NODE '99,1.0D-03,0.0,0.0': 'D' 지수로 읽어 절점 99 = (0.001, 0, 0)",
          rc == 0 and 99 in nd and near(nd[99][0], 0.001), f"rc={rc} {nd.get(99)} " + log[-300:])
    d, rc, log = run("node_bad", {"model.k": cube_deck().replace("*ELEMENT_SOLID", "98,abc,0.0,0.0\n*ELEMENT_SOLID", 1)})
    check("R1 *NODE 숫자로 읽지 못한 줄: 버리면 소실 장부에 올라 rc 3", rc == 3 and "숫자로 읽지 못한 절점 줄" in log,
          f"rc={rc} " + log[-300:])


def r2():
    print("[R2] 원문 번호 예약, Fast DROP 바닥판 번호, IMPORT_MERGE_K I10, D2R 한 번, 섞인 두께 블록")
    D2R = ("*DEFORMABLE_TO_RIGID_AUTOMATIC\n" + f10(1, 0, 0.0, 0.0, 0.0, 0, 0, 0) + f10(0, 0, 0, 0.0, 1, 0, 0.0) + f10(2, 0))
    INERTIA = "*PART_INERTIA\n" + "".join(f"inertia {nm}\n" + f10(pid, 1, 1) + f10(0.0, 0.0, 0.0, "1e-06", 0, 0)
                                          + f10("1e-06", 0.0, 0.0, "1e-06", 0.0, "1e-06") + f10(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
                                          for nm, pid in (("a", 8), ("b", 9)))

    def d2r_count(t):
        return sum(1 for _, rows in kw_blocks(t, "*DEFORMABLE_TO_RIGID_AUTOMATIC") if rows and rows[0][:10].strip() == "1")

    # ── 여러 각도 DROP: 바닥판 PID·EID(R2-1·3), D2R 한 번(R2-5) ───────────────────────────────────────────
    d, rc, log = run("a_drop2", {"model.k": M.base_deck(raw=True, extra=D2R + INERTIA)}, drop([0, 90]))
    outs = dropsets(d)
    floors = [sorted(set(M.parts_of(t)) - {1, 2, 6, 7}) for t in outs]
    dups = [sorted(e for e, v in elements(t).items() if len(v) > 1) for t in outs]
    check("R2 DROP 2각도: rc 0·DropSet.k 2개", rc == 0 and len(outs) == 2, f"rc={rc} " + log[-400:])
    check("R2 DROP 2각도: 바닥판 PID 가 원문 *PART_INERTIA 둘째 파트(9)와 겹치지 않고(≥ 10) 두 각도가 같다",
          len(floors) == 2 and all(len(f) == 1 and f[0] >= 10 for f in floors) and floors[0] == floors[1], str(floors))
    check("R2 DROP 2각도: 바닥판 솔리드가 모델 솔리드와 같은 EID 를 쓰지 않는다", len(dups) == 2 and not any(dups), str(dups))
    check("R2 DROP 2각도: 덱의 D2R(SWSET 1)이 각도마다 한 번", [d2r_count(t) for t in outs] == [1, 1],
          str([d2r_count(t) for t in outs]))
    d, rc, log = run("a_trans", {"model.k": M.base_deck(raw=True, extra=D2R)})
    check("R2 TRANSFORM: 덱의 D2R(SWSET 1)이 한 번(원문 판과 매니저 판 둘이 아니다)",
          rc == 0 and d2r_count(read(d, "model_trans.k")) == 1, f"rc={rc} {d2r_count(read(d, 'model_trans.k'))}")

    # ── 원문 요소의 실수 칸은 번호가 아니다(R2-2) ─────────────────────────────────────────────────────────
    deck = ("*KEYWORD\n" + ELASTIC + SOLID1 + part(1, name="solid normal") + part(2, name="solid two")
            + "*ELEMENT_INERTIA\n" + f"{100:8d}{16:8d}{0:8d}\n" + "2.5e10,0.0,0.0,2.5e10,0.0,2.5e10,0.001\n"
            + node_block(cubes(2)) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1) + hex_row(2, 2, 9) + "*END\n")
    d, rc, log = run("e_inertia", {"model.k": deck}, drop([0]))
    outs = dropsets(d)
    e = elements(outs[0]) if outs else {}
    floor = sorted(k for k, v in e.items() if v[0][0] not in (1, 2))
    check("R2 *ELEMENT_INERTIA 의 실수 '2.5e10': 바닥판 EID 가 부풀지 않는다(원문 EID 100 위, int32·10칸 안)",
          rc == 0 and floor and floor[0] > 100 and floor[-1] < 10 ** 8 and not any(len(v) > 1 for v in e.values()),
          f"rc={rc} 바닥판 EID {floor[:2]}…{floor[-1:]} " + log[-300:])

    # ── IMPORT_MERGE_K 가 I10 클래스 기본값을 되돌리지 않는다(R2-4) ────────────────────────────────────────
    base = ("*KEYWORD I10=Y\n" + node_block(cubes(1), 10) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1, 10) + part(1, name="base_part")
            + SOLID1 + ELASTIC + "*END\n")
    imp = ("*KEYWORD\n" + node_block(cubes(1)) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1) + part(1, 1, 2, "imported_part")
           + "*SECTION_SOLID\n" + f10(1, 2) + "*MAT_ELASTIC\n" + f10(2, "2.70E-09", 70000, 0.33) + "*END\n")
    d, rc, log = run("d_imerge", {"base.k": base, "imp.k": imp}, IMO)
    t = read(d, "base_imported.k")
    e, nd = elements(t), nodes(t)
    sets = try_(lambda: sorted(tuple(v[0][1]) for v in e.values()), [])
    check("R2 IMPORT_MERGE_K(기준 덱 I10=Y): 가져온 요소도 머리 줄·덱 폭으로 읽으면 절점이 덱에 있다(8칸 쓰레기가 아니다)",
          rc == 0 and len(e) == 2 and -1 not in e and all(n in nd for s in sets for n in s) and len(set(sets)) == 2
          and all(len(set(s)) == 8 for s in sets), f"rc={rc} {e} " + log[-300:])

    # ── 4·8절점이 섞인 *ELEMENT_SHELL_THICKNESS(R2-6)와 콤마 두께 블록 ──────────────────────────────────────
    pts = {1: (0, 0), 2: (1, 0), 3: (1, 1), 4: (0, 1), 11: (2, 0), 12: (3, 0), 13: (3, 1), 14: (2, 1), 15: (2.5, 0), 16: (3, 0.5),
           17: (2.5, 1), 18: (2, 0.5), 21: (4, 0), 22: (5, 0), 23: (5, 1), 24: (4, 1)}
    tail = (part(1, 1, 1, "shell") + "*SECTION_SHELL\n" + f10(1, 2) + f10(1.0, 1.0, 1.0, 1.0) + ELASTIC + "*END\n")

    def tdeck(body):
        return ("*KEYWORD\n" + node_block({k: (x, y, 0.0) for k, (x, y) in pts.items()}) + body + tail)

    def e8(eid, ns, w=8):
        return f"{eid:{w}d}{1:{w}d}" + "".join(f"{n:{w}d}" for n in ns) + "\n"

    def t16(*v):
        return "".join(f"{x:16.1f}" for x in v) + "\n"
    E1 = e8(1, (1, 2, 3, 4)) + t16(0.1, 0.2, 0.3, 0.4, 15.0)
    E2 = e8(2, (11, 12, 13, 14, 15, 16, 17, 18)) + t16(1.1, 1.2, 1.3, 1.4, 45.0) + t16(1.5, 1.6, 1.7, 1.8)
    E3 = e8(3, (21, 22, 23, 24)) + t16(2.1, 2.2, 2.3, 2.4, 0.0)
    want = {1: ([1, 2, 3, 4, 0, 0, 0, 0], [0.1, 0.2, 0.3, 0.4, 15.0]),
            2: ([11, 12, 13, 14, 15, 16, 17, 18], [1.1, 1.2, 1.3, 1.4, 45.0, 1.5, 1.6, 1.7, 1.8]),
            3: ([21, 22, 23, 24, 0, 0, 0, 0], [2.1, 2.2, 2.3, 2.4, 0.0])}

    def same(got, eids):
        return all(k in got and got[k][0] == want[k][0] and len(got[k][1]) >= len(want[k][1])
                   and all(near(a, b) or a == b == 0 for a, b in zip(got[k][1], want[k][1])) for k in eids)
    for name, body, w in (("4·8·4 절점", E1 + E2 + E3, 8), ("8·4·4 절점", E2 + E1 + E3, 8),
                          ("I10 '%' 4·8·4 절점", e8(1, (1, 2, 3, 4), 10) + t16(0.1, 0.2, 0.3, 0.4, 15.0)
                           + e8(2, (11, 12, 13, 14, 15, 16, 17, 18), 10) + t16(1.1, 1.2, 1.3, 1.4, 45.0) + t16(1.5, 1.6, 1.7, 1.8)
                           + e8(3, (21, 22, 23, 24), 10) + t16(2.1, 2.2, 2.3, 2.4, 0.0), 10)):
        hdr = "*ELEMENT_SHELL_THICKNESS %\n" if w == 10 else "*ELEMENT_SHELL_THICKNESS\n"
        d, rc, log = run("thk", {"model.k": tdeck(hdr + body)})
        got = thick_shells(read(d, "model_trans.k"))
        check(f"R2 *ELEMENT_SHELL_THICKNESS {name} 한 블록: 요소마다 카드 수를 정해 세 요소·두께(THIC5~8 포함)가 그대로",
              rc == 0 and same(got, (1, 2, 3)), f"rc={rc} {got} " + log[-300:])
    d, rc, log = run("thk_comma", {"model.k": tdeck("*ELEMENT_SHELL_THICKNESS\n1,1,1,2,3,4\n0.1,0.2,0.3,0.4,15.0\n"
                                                     "2,1,11,12,13,14,15,16,17,18\n1.1,1.2,1.3,1.4,45.0\n1.5,1.6,1.7,1.8\n"
                                                     "3,1,21,22,23,24\n2.1,2.2,2.3,2.4,0.0\n")})
    got = thick_shells(read(d, "model_trans.k"))
    check("R2 콤마 *ELEMENT_SHELL_THICKNESS(4·8·4 절점): EID 칸에서 죽지 않고 그대로", rc == 0 and same(got, (1, 2, 3)),
          f"rc={rc} {got} " + log[-300:])
    tri = f"{1:8d}{1:8d}{1:8d}{2:8d}{3:8d}\n" + t16(0.1, 0.2, 0.3, 0.4, 15.0)
    d, rc, log = run("thk_tri", {"model.k": tdeck("*ELEMENT_SHELL_THICKNESS\n" + tri + E3)})
    got = thick_shells(read(d, "model_trans.k"))
    check("R2 두께 블록 첫 요소가 삼각형(40자 줄): 뒤 사각형 요소 3 의 N4 = 24 가 잘리지 않는다",
          rc == 0 and got.get(3, ([],))[0][:4] == [21, 22, 23, 24], f"rc={rc} {got}")


def r3():
    print("[R3] IMPORT_MERGE_K 접촉·뿌리 매니저·원문 번호·재질·INCLUDE_TRANSFORM·좌표계·곡선, DECOMPOSE·DWI·옵션 블록·sphere·DTI")
    one = lambda pid, sec, mid, name: ("*KEYWORD\n" + node_block(cubes(1)) + "*ELEMENT_SOLID\n" + hex_row(1, pid, 1)
                                       + part(pid, sec, mid, name) + "*SECTION_SOLID\n" + f10(sec, 1))
    steel = "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
    alu2 = "*MAT_ELASTIC\n" + f10(2, "2.70E-09", 70000, 0.33)

    # ── 가져온 접촉(R3-1) ─────────────────────────────────────────────────────────────────────────────
    con = "*SET_PART_LIST\n" + f10(1) + f10(1) + "*CONTACT_AUTOMATIC_SINGLE_SURFACE\n" + f10(1, 0, 2, 0) + f10(0.1, 0.1) + f10(1.0, 1.0)
    d, rc, log = run("im_contact", {"base.k": one(1, 1, 1, "base_part") + steel + con + "*END\n",
                                    "imp.k": one(1, 1, 2, "imp_part") + "*MAT_ELASTIC\n" + f10(2, "7.85E-09", 210000, 0.3)
                                    + con + "*END\n"}, IMO)
    t = read(d, "base_imported.k")
    ssids = [ints(rows[0], 10)[0] for _, rows in kw_blocks(t, "*CONTACT_AUTOMATIC_SINGLE_SURFACE") if rows]
    ssids += [ints(rows[1], 10)[0] for _, rows in kw_blocks(t, "*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID") if len(rows) > 1]
    psets = {}
    for kw in ("*SET_PART_LIST", "*SET_PART_LIST_TITLE"):
        for h, rows in kw_blocks(t, kw):
            rows = rows[1:] if kw.endswith("_TITLE") else rows
            psets[int(rows[0][:10])] = [x for r in rows[1:] for x in ints(r, 10) if x]
    pids = set(M.parts_of(t))
    check("R3 IMPORT_MERGE_K 가져온 덱에 접촉: 죽지 않고 접촉 2개가 각자 제 파트 셋(기준 PID 1 / 가져온 파트)을 가리킨다",
          rc == 0 and no_tb(log) and len(ssids) == 2 and len(set(ssids)) == 2
          and sorted(tuple(psets.get(s, [])) for s in ssids) == sorted((p,) for p in pids) and len(pids) == 2,
          f"rc={rc} ssid={ssids} sets={psets} pids={pids} " + log[-300:])

    # ── 셸 요소 셋(SSTYP 1)을 쓰는 가져온 접촉 — 요소 셋 번호가 밀리니 접촉 SSID 도 같이 밀린다 ─────────────────────
    plate = ("*KEYWORD\n" + node_block({**cubes(1), 9: (0, 0, 2), 10: (1, 0, 2), 11: (1, 1, 2), 12: (0, 1, 2)}) + "*ELEMENT_SOLID\n"
             + hex_row(1, 1, 1) + "*ELEMENT_SHELL\n" + f"{21:8d}{2:8d}{9:8d}{10:8d}{11:8d}{12:8d}\n" + part(1) + part(2, 2, 1)
             + SOLID1 + "*SECTION_SHELL\n" + f10(2, 2) + f10(0.5, 0.5, 0.5, 0.5) + ELASTIC + "*SET_SHELL\n" + f10(5) + f10(21)
             + "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE\n" + f10(5, 1, 1, 3) + f10(0.1, 0.1) + f10(1.0, 1.0) + "*END\n")
    d, rc, log = run("im_sstyp1", {"base.k": plate, "imp.k": plate}, IMO)
    t = read(d, "base_imported.k")
    cons = [ints(rows[0], 10)[:4] for _, rows in kw_blocks(t, "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE") if rows]
    cons += [ints(rows[1], 10)[:4] for _, rows in kw_blocks(t, "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID") if len(rows) > 1]
    shsets = {}
    for kw in ("*SET_SHELL", "*SET_SHELL_TITLE", "*SET_SHELL_LIST", "*SET_SHELL_LIST_TITLE"):
        for h, rows in kw_blocks(t, kw):
            rows = rows[1:] if kw.endswith("_TITLE") else rows
            shsets[int(rows[0][:10])] = [x for r in rows[1:] for x in ints(r, 10) if x]
    shell_pid = {e: v[0][0] for e, v in elements(t, "*ELEMENT_SHELL").items()}
    imp = [c for c in cons if c[1] != 1]
    check("R3 IMPORT_MERGE_K 셸 요소 셋(SSTYP 1) 접촉: 가져온 접촉이 기준 덱 셋 5 가 아니라 가져온 셸의 셋을 가리킨다",
          rc == 0 and len(cons) == 2 and len(imp) == 1 and imp[0][0] != 5
          and [shell_pid.get(e) for e in shsets.get(imp[0][0], [])] not in ([], [2]), f"rc={rc} {cons} {shsets} {shell_pid}")

    # ── 뿌리 요소 매니저: PID 없는 질량·요소 셋(R3-2) ───────────────────────────────────────────────────
    root = lambda m: "*SET_SOLID\n" + f10(1) + f10(1) + "*ELEMENT_MASS\n" + f"{60:8d}{9 - 1:8d}{m:16.6f}\n"
    d, rc, log = run("im_eset", {"base.k": one(1, 1, 1, "base_part") + steel + root(0.001) + "*END\n",
                                 "imp.k": one(1, 1, 2, "imp_part") + alu2 + root(0.555) + "*END\n"}, IMO)
    t = read(d, "base_imported.k")
    masses = try_(lambda: sorted((int(r[:8]), round(float(r[16:32]), 6)) for _, rows in kw_blocks(t, "*ELEMENT_MASS") for r in rows), [])
    ssets = []
    for kw in ("*SET_SOLID", "*SET_SOLID_TITLE"):
        for h, rows in kw_blocks(t, kw):
            rows = rows[1:] if kw.endswith("_TITLE") else rows
            ssets.append(sorted(x for r in rows[1:] for x in ints(r, 10) if x))
    imp_eid = sorted(k for k, v in elements(t).items() if v[0][0] != 1)
    check("R3 IMPORT_MERGE_K 같은 번호 *ELEMENT_MASS 60: 기준 질량 0.001 이 남고 가져온 0.555 는 새 번호로",
          rc == 0 and len(masses) == 2 and (60, 0.001) in masses and any(m == 0.555 and e != 60 for e, m in masses), f"rc={rc} {masses}")
    check("R3 IMPORT_MERGE_K 같은 SID *SET_SOLID 1: 기준 셋은 요소 1, 가져온 셋은 새 SID 로 가져온 요소",
          rc == 0 and sorted(ssets) == sorted([[1], imp_eid]) and len(imp_eid) == 1, f"rc={rc} {ssets} imp={imp_eid}")

    # ── 기준 덱 원문 단면·재질 번호(R3-3) ────────────────────────────────────────────────────────────────
    d, rc, log = run("im_rawid", {"base.k": M.base_deck(raw=True),
                                  "imp.k": one(1, 4, 6, "imp_part").replace("*SECTION_SOLID\n" + f10(4, 1), "*SECTION_SOLID\n" + f10(4, 2))
                                  + "*MAT_ELASTIC\n" + f10(6, "2.70E-09", 70000, 0.33) + "*END\n"}, IMO)
    t = read(d, "base_imported.k")
    secids = try_(lambda: [int(float((rows[1] if h.split()[0].upper().endswith("_TITLE") else rows[0])[:10]))
                           for h, rows in sum((kw_blocks(t, k) for k in sorted({ln.split()[0].upper() for ln in t.splitlines()
                                                                                 if ln.startswith("*SECTION_")})), []) if rows], [0, 0])
    check("R3 IMPORT_MERGE_K 가져온 SECID·MID 가 기준 덱 원문(*SECTION_DISCRETE 6·*MAT_SPRING_ELASTIC 6)과 겹침: 단면은 겹치지 "
          "않고 MID 6 은 🔴 rc 3", rc == 3 and len(secids) == len(set(secids)) and "재질 MID 6" in log, f"rc={rc} secids={secids}")

    # ── 같은 MID 다른 재질 + *MAT_ADD_EROSION(R3-4), 같은 MID 같은 재질(이번에 찾음) ────────────────────────
    ero = "*MAT_ADD_EROSION\n" + f10(1, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0) + f10(0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0) + "\n"
    d, rc, log = run("im_mid", {"base.k": one(1, 1, 1, "steel_part") + steel + "*END\n",
                                "imp.k": one(1, 1, 1, "alu_part") + "*MAT_ELASTIC\n" + f10(1, "2.70E-09", 70000, 0.33) + ero + "*END\n"},
                     IMO)
    t = read(d, "base_imported.k")
    mats = [floats((rows[1] if h.split()[0].upper().endswith("_TITLE") else rows[0]), 10)
            for h, rows in kw_blocks(t, "*MAT_ELASTIC") + kw_blocks(t, "*MAT_ELASTIC_TITLE")]
    check("R3 IMPORT_MERGE_K 같은 MID 1 다른 재질: 기준 강재(E 210000)만 남고 침식 카드는 붙지 않으며 🔴 rc 3",
          rc == 3 and len(mats) == 1 and mats[0][2] == 210000 and "*MAT_ADD_EROSION" not in t.upper(), f"rc={rc} {mats}")
    d, rc, log = run("im_same", {"base.k": one(1, 1, 1, "a") + steel + "*END\n", "imp.k": one(1, 1, 1, "b") + steel + "*END\n"}, IMO)
    check("R3 IMPORT_MERGE_K 같은 MID 1 같은 재질: 충돌이 아니다(rc 0)", rc == 0 and "번호 충돌" not in log, f"rc={rc} " + log[-300:])

    # ── 가져온 덱의 *INCLUDE_TRANSFORM(R3-5) ───────────────────────────────────────────────────────────
    sub = ("*KEYWORD\n" + node_block(cubes(1, 101)) + "*ELEMENT_SOLID\n" + hex_row(101, 101, 101) + part(101, 101, 101, "sub_part")
           + "*SECTION_SOLID\n" + f10(101, 1) + "*MAT_ELASTIC\n" + f10(101, "7.85E-09", 210000, 0.3) + "*END\n")
    inc = "*INCLUDE_TRANSFORM\nsub.k\n" + f10(0, 0, 0, 0, 0, 0, 0) + f10(0) + f10(1.0, 1.0, 1.0, "", 0) + f10(0)
    d, rc, log = run("im_inctr", {"base.k": one(1, 1, 1, "base_part") + steel + "*END\n",
                                  "imp.k": one(1, 1, 2, "imp_part") + alu2 + inc + "*END\n", "sub.k": sub}, IMO)
    check("R3 IMPORT_MERGE_K 가져온 덱의 *INCLUDE_TRANSFORM: 알림 없이 빠지지 않는다(🔴 rc 3)",
          rc == 3 and "INCLUDE_TRANSFORM" in log, f"rc={rc} " + log[-300:])

    # ── *NODE 없이 설정만 든 덱 가져오기(R3-14) ──────────────────────────────────────────────────────────
    d, rc, log = run("im_dbonly", {"base.k": one(1, 1, 1, "base_part") + steel + "*END\n",
                                   "imp.k": "*KEYWORD\n*DATABASE_GLSTAT\n" + f10("1.0e-5") + "*CONTROL_TERMINATION\n" + f10(0.005)
                                   + "*END\n"}, IMO)
    check("R3 IMPORT_MERGE_K *NODE 없는 설정 덱: KeyError 로 죽지 않고 설정을 옮기지 않는다고 알린다(rc 0)",
          rc == 0 and no_tb(log) and "설정 카드는 옮기지 않는다" in log, f"rc={rc} " + log[-300:])

    # ── 좌표계 _TITLE·곡선 SFA 빈칸(R3-6·7) ────────────────────────────────────────────────────────────
    cs = f10(5, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0) + f10(0.0, 1.0, 0.0)
    d, rc, log = run("im_cs", {"base.k": one(1, 1, 1, "a") + steel + "*DEFINE_COORDINATE_SYSTEM\n" + cs + "*END\n",
                               "imp.k": one(1, 1, 2, "b") + alu2 + "*DEFINE_COORDINATE_SYSTEM_TITLE\nlocal cs\n" + cs + "*END\n"}, IMO)
    check("R3 IMPORT_MERGE_K 같은 값 좌표계 CID 5(한쪽만 _TITLE): 충돌이 아니다(rc 0)", rc == 0 and "번호 충돌" not in log,
          f"rc={rc} " + log[-300:])
    plp = lambda mid: ("*MAT_PIECEWISE_LINEAR_PLASTICITY\n" + f10(mid, "7.85E-09", 210000.0, 0.3, 250.0, 0.0, 0.0) + f10(0.0, 0.0, 7, 0)
                       + f10(0, 0, 0, 0, 0, 0, 0, 0) + f10(0, 0, 0, 0, 0, 0, 0, 0))
    pts = f"{0.0:20.4f}{250.0:20.4f}\n{0.1:20.4f}{300.0:20.4f}\n"
    d, rc, log = run("im_curve", {"base.k": one(1, 1, 1, "a") + plp(1) + "*DEFINE_CURVE\n" + f10(7) + pts + "*END\n",
                                  "imp.k": one(1, 1, 2, "b") + plp(2) + "*DEFINE_CURVE\n" + f10(7, 0, 1.0, 1.0, 0.0, 0.0) + pts + "*END\n"},
                     IMO)
    check("R3 IMPORT_MERGE_K 같은 점 LCID 7(SFA·SFO 빈칸 / 1.0): 충돌이 아니다(rc 0)", rc == 0 and "번호 충돌" not in log,
          f"rc={rc} " + log[-300:])

    # ── *DEFINE_COORDINATE_SYSTEM 이 출력에 남는다(R3-8)·_TITLE 은 둘째 줄이 카드 1 ──────────────────────────
    for name, kw in (("plain", "*DEFINE_COORDINATE_SYSTEM\n"), ("title", "*DEFINE_COORDINATE_SYSTEM_TITLE\nlocal cs\n")):
        d, rc, log = run("cs_" + name, {"model.k": cube_deck(kw + f10(5, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0) + f10(0.0, 1.0, 0.0))})
        t = read(d, "model_trans.k")
        got = []
        for h, rows in kw_blocks(t, "*DEFINE_COORDINATE_SYSTEM") + kw_blocks(t, "*DEFINE_COORDINATE_SYSTEM_TITLE"):
            rows = rows[1:] if h.split()[0].upper().endswith("_TITLE") else rows
            got.append([floats(r, 10) for r in rows])
        check(f"R3 TRANSFORM *DEFINE_COORDINATE_SYSTEM{'_TITLE' if name == 'title' else ''} CID 5: 출력에 같은 값으로 남는다",
              rc == 0 and len(got) == 1 and got[0][0][:7] == [5, 0, 0, 0, 1.0, 0, 0] and got[0][1][:3] == [0, 1.0, 0],
              f"rc={rc} {got} " + log[-300:])

    # ── TRANSFORM 이 점으로 정의한 좌표계도 절점과 같이 옮긴다(좌표계를 쓰기 시작해서 — CIDL 이 있는 좌표계는 그대로) ──────────
    def csys(t):
        out = {}
        for h, rows in kw_blocks(t, "*DEFINE_COORDINATE_SYSTEM") + kw_blocks(t, "*DEFINE_COORDINATE_SYSTEM_TITLE"):
            rows = rows[1:] if h.split()[0].upper().endswith("_TITLE") else rows
            a, b = floats(rows[0], 10), floats(rows[1], 10)
            out[int(a[0])] = (a[1:7], int(a[7]) if len(a) > 7 else 0, b[:3])
        return out
    cs2 = ("*DEFINE_COORDINATE_SYSTEM\n" + f10(5, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0) + f10(0.0, 1.0, 0.0)
           + "*DEFINE_COORDINATE_SYSTEM\n" + f10(6, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 5) + f10(0.0, 1.0, 0.0))
    for line, (ol, pp) in (("Rotation,0,0,90", ([0, 0, 0, 0, 1, 0], [-1, 0, 0])), ("Mirror,yz", ([0, 0, 0, -1, 0, 0], [0, 1, 0])),
                           ("Translation,1,2,3", ([1, 2, 3, 2, 2, 3], [1, 3, 3]))):
        d, rc, log = run("cs_move", {"model.k": cube_deck(cs2)}, TRANS.replace("Translation,0,0,0", line))
        got = try_(lambda: csys(read(d, "model_trans.k")), {})
        ok5 = 5 in got and all(abs(a - b) < 1e-9 for a, b in zip(got[5][0] + got[5][2], ol + pp))
        ok6 = 6 in got and got[6][1] == 5 and all(abs(a - b) < 1e-9 for a, b in zip(got[6][0] + got[6][2], [0, 0, 0, 1, 0, 0, 0, 1, 0]))
        check(f"R3 TRANSFORM {line}: 좌표계 CID 5 의 점(O·L·P)이 절점과 같이 옮겨지고, CIDL 5 인 CID 6 은 그대로",
              rc == 0 and ok5 and ok6, f"rc={rc} {got}")

    # ── DECOMPOSE_K ModelIndependentSplit False(R3-9) ────────────────────────────────────────────────────
    dec = ("*Inputfile\nmodel.k\n*Mode\nDECOMPOSE_K,1\n**DecomposeK,1\nGroup,housing,housing\nGroup,fpcb,fpcb\n"
           "OutputDir,decomposed_output\nSharedNodesPolicy,first_group\nModelIndependentSplit,False\n**End\n*End\n")
    d, rc, log = run("dec2", {"model.k": M.base_deck(raw=True)}, dec)
    alltxt = "".join(p.read_text(errors="replace") for p in sorted((d / "decomposed_output").rglob("*.k")))
    kws = [ln.split()[0].upper() for ln in alltxt.splitlines() if ln.startswith("*")]
    check("R3 DECOMPOSE_K ModelIndependentSplit False: *CONTROL_TERMINATION·*CONTROL_MPP_IO_NOD3DUMP 가 한 번씩 남는다",
          rc == 0 and kws.count("*CONTROL_TERMINATION") == 1 and kws.count("*CONTROL_MPP_IO_NOD3DUMP") == 1,
          f"rc={rc} TERM {kws.count('*CONTROL_TERMINATION')} NOD3DUMP {kws.count('*CONTROL_MPP_IO_NOD3DUMP')} " + log[-300:])

    # ── 복합재 파트의 DWI OutsideRigid(R3-10) ────────────────────────────────────────────────────────────
    grid = {i * 3 + j + 1: (float(j), float(i), 0.0) for i in range(3) for j in range(3)}
    shells = "*ELEMENT_SHELL\n" + "".join(f"{e:8d}{1:8d}" + "".join(f"{n:8d}" for n in q) + "\n"
                                         for e, q in ((1, (1, 2, 5, 4)), (2, (2, 3, 6, 5)), (3, (4, 5, 8, 7)), (4, (5, 6, 9, 8))))

    def comp(mid):
        return "*PART_COMPOSITE\ncomp\n" + f10(1, 2) + f10(mid, 0.5, 0.0, 0, mid, 0.5, 90.0, 0)
    fabric = ("*MAT_LAMINATED_COMPOSITE_FABRIC\n" + f10(2, "1.50E-09", 50000, 50000, 5000, 0.05, 0, 0) + f10(3000, 3000, 3000, 0, 0, 0, 0, 0)
              + f10(0, 0, 0, 0, 0, 0, 0, 0) * 5)
    dwi = ("*Inputfile\nmodel.k\n*RunDirectoryMode,True,@D@/results/dwi_0001\n*Mode\nDROP_WEIGHT_IMPACT_TEST,1\n"
           "**DropWeightImpactTest,1\nTFinal,0.0001\nDT,1e-05\nLocationX,1.0\nLocationY,1.0\nHeight,100\nInitialVelocityX,0\n"
           "InitialVelocityY,0\nInitialVelocityZ,0\nGravity,9810\nImpactorType,Sphere\nImpactorDimension,0.5\nMeshSize,0.25\n"
           "DensityImpactor,7.85e-09\nYoungsModulusImpactor,200000.0\nPoissonRatioImpactor,0.3\nGenerationMode,OutsideRigidElement\n"
           "BoundaryDistance,0.6\nOffsetDistance,0.05\nYoungsModulusWall,10000.0\nPoissonRatioWall,0.3\nDensityWall,1e-09\n"
           "**EndDropWeightImpactTest\n*End\n")
    d, rc, log = run("dwi_comp1", {"model.k": "*KEYWORD\n" + node_block(grid) + shells + comp(1)
                                   + "*MAT_ELASTIC\n" + f10(1, "2.70E-09", 70000, 0.33) + "*END\n"}, dwi)
    t = "".join(p.read_text(errors="replace") for p in sorted((d / "results").rglob("DropWeightImpactTestSet.k")))
    rig = [floats(rows[1] if h.split()[0].upper().endswith("_TITLE") else rows[0], 10)
           for h, rows in kw_blocks(t, "*MAT_RIGID") + kw_blocks(t, "*MAT_RIGID_TITLE") if len(rows) > 1]
    rig = [r for r in rig if len(r) >= 4 and near(r[1], 2.7e-9)]
    check("R3 DWI OutsideRigidElement 복합재 파트(층 재질 MAT_ELASTIC): 죽지 않고 강체 재질 E 70000·PR 0.33(뒤바뀌지 않는다)",
          rc == 0 and no_tb(log) and rig and all(r[2] == 70000 and near(r[3], 0.33) for r in rig), f"rc={rc} {rig} " + log[-300:])
    d, rc, log = run("dwi_comp2", {"model.k": "*KEYWORD\n" + node_block(grid) + shells + comp(2)
                                   + "*MAT_ELASTIC\n" + f10(1, "2.70E-09", 70000, 0.33) + fabric + "*END\n"}, dwi)
    check("R3 DWI OutsideRigidElement 복합재 파트(층 재질이 원문 재질): 죽지 않고 ⚠ 로 알린다", rc == 0 and no_tb(log) and "⚠" in log,
          f"rc={rc} " + log[-300:])

    # ── 같은 모드 ID 옵션 블록 두 벌(R3-11) ──────────────────────────────────────────────────────────────
    pex = ("*Inputfile\nmodel.k\n*Mode\nPART_EXCHANGE,1\nPART_EXCHANGE,1\n**PartExchange,1\n*PID,2\n*SECTION_TSHELL\n"
           "       SID         1    0.8333         3         1       0.0         0         0\n**EndPartExchange\n"
           "**PartExchange,1\n*PID,1\n*SECTION_SOLID\n       SID         2\n**EndPartExchange\n*End\n")
    d, rc, log = run("x2dup", {"model.k": M.base_deck(raw=False)}, pex)
    check("R3 같은 모드 ID 의 옵션 블록 두 벌(**PartExchange,1 ×2): 조용히 덮지 않고 원인을 밝혀 멈춘다(rc 1)",
          rc == 1 and "두 번 이상" in log, f"rc={rc} " + log[-300:])

    # ── sphere 워커 0.5 GB 의 x.5 GB(R3-12) ──────────────────────────────────────────────────────────
    sys.path.insert(0, str(ROOT))
    from Runner import PostprocessShellGenerator as P
    got = []
    for node in (12.7, 12.5, 9.8):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r = P._sphere_auto_resources(979, None, "", None, None, None, tool_flags={"--parallel-runs"}, limits={"nodes": [(64, node)]})
        got.append((node, r[0], r[1], "🔴" in buf.getvalue()))
    check("R3 sphere 노드 12.7·12.5·9.8 GB: 요청 메모리가 노드에 들어가는 워커 수를 골라 🔴 OOM 경고가 없다",
          all(not red and int(mem.rstrip("G")) <= node for node, _, mem, red in got), str(got))

    # ── *SET_NODE_LIST_GENERATE(R3 범위 밖 관찰): 쓰기에서 죽지 않고 NSID·범위 안 절점이 남는다 ─────────────────────
    def nsets(t):
        out = {}
        for kw in ("*SET_NODE_LIST", "*SET_NODE_LIST_TITLE", "*SET_NODE_LIST_GENERATE"):
            for h, rows in kw_blocks(t, kw):
                rows = rows[1:] if kw.endswith("_TITLE") else rows
                ids = [x for r in rows[1:] for x in ints(r, 10) if x]
                if kw.endswith("_GENERATE"):
                    ids = [i for a, b in zip(ids[::2], ids[1::2]) for i in range(a, b + 1)]
                out[int(rows[0][:10])] = sorted(ids)
        return out
    gen = "*SET_NODE_LIST_GENERATE\n" + f10(7) + f10(1, 4, 50, 60)
    d, rc, log = run("gen_trans", {"model.k": cube_deck(gen)})
    got = try_(lambda: nsets(read(d, "model_trans.k")), {})
    check("R3 *SET_NODE_LIST_GENERATE 7(1~4, 50~60): 죽지 않고 NSID 7 에 정의된 절점 1~4 만", rc == 0 and got == {7: [1, 2, 3, 4]},
          f"rc={rc} {got} " + log[-300:])
    d, rc, log = run("gen_merge", {"base.k": one(1, 1, 1, "a") + steel + "*END\n",
                                   "imp.k": one(1, 1, 2, "b") + alu2 + gen + "*END\n"}, IMO)
    t = read(d, "base_imported.k")
    got = try_(lambda: nsets(t), {})
    imp_nodes = sorted(n for k, v in elements(t).items() for p, ns in v if p != 1 for n in ns)
    check("R3 IMPORT_MERGE_K 가져온 덱의 *SET_NODE_LIST_GENERATE: 가져온 요소의 절점 1~4 를 따라 번호가 밀린다",
          rc == 0 and len(got) == 1 and len(imp_nodes) == 8 and list(got.values())[0] == imp_nodes[:4], f"rc={rc} {got} {imp_nodes}")

    # ── DTI 가 dynain 이 싣지 않는 원문 *INITIAL_STRESS_SECTION 을 지우지 않는다(R3-13) ────────────────────────
    pts = dict(cubes(1))
    pts.update({50: (5.0, 0.0, 0.0), 51: (6.0, 0.0, 0.0), 52: (6.0, 1.0, 0.0), 53: (5.0, 1.0, 0.0)})
    el = "*ELEMENT_SOLID\n" + hex_row(1, 1, 1) + "*ELEMENT_SHELL\n" + f"{9:8d}{3:8d}{50:8d}{51:8d}{52:8d}{53:8d}\n"
    base = ("*KEYWORD\n*CONTROL_TERMINATION\n" + f10(0.001) + node_block(pts) + el + part(1) + part(3, 3, 1) + SOLID1
            + "*SECTION_SHELL\n" + f10(3, 2, 0.8333, 3) + f10(0.5, 0.5, 0.5, 0.5) + ELASTIC
            + "*DATABASE_CROSS_SECTION_SET_ID\n" + f"{1:10d}      bolt\n" + f10(0, 0, 0, 0, 0, 0)
            + "*INITIAL_STRESS_SECTION\n" + f10(1, 1, 0, 1, 0, 0, 0) + "*END\n")
    dyn = ("*KEYWORD\n" + node_block({k: (x, y, z + 0.01) for k, (x, y, z) in pts.items()}) + el
           + "*INITIAL_STRESS_SOLID\n" + f10(1, 1, 0, 0, 0, 0, 0, 0) + f10(1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 0.01) + "*END\n")
    dti = ("*Inputfile\nmodel.k\n*Mode\nDYNAIN_TO_INITIAL,1\n**DynainToInitial,1\n*DynainPath,dynain\n*IncludeStress,True\n"
           "*RemoveDynamicRelaxation,True\n**EndDynainToInitial\n*End\n")
    d, rc, log = run("dti_del", {"model.k": base, "dynain": dyn}, dti)
    kws = [ln.split()[0].upper() for ln in read(d, "model_dti.k").splitlines() if ln.startswith("*")]
    check("R3 DTI: 기준 덱의 *INITIAL_STRESS_SECTION(dynain 이 싣지 않는 사용자 카드)이 남고 dynain 응력이 들어간다",
          rc == 0 and "*INITIAL_STRESS_SECTION" in kws and "*INITIAL_STRESS_SOLID" in kws, f"rc={rc} {kws}")


def r4():
    print("[R4] 처방 운동 카드 3, 질량 절점 셋 번호, 섞인 셸, Fast DROP 강체화, HISTORY·콤마 남는 값, IMPORT_MERGE_K 원문 번호·재질, DTI, D2R")
    one = lambda pid, sec, mid, name: ("*KEYWORD\n" + node_block(cubes(1)) + "*ELEMENT_SOLID\n" + hex_row(1, pid, 1)
                                       + part(pid, sec, mid, name) + "*SECTION_SOLID\n" + f10(sec, 1))
    steel = "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
    alu2 = "*MAT_ELASTIC\n" + f10(2, "2.70E-09", 70000, 0.33)

    # ── 처방 운동 카드 3(|DOF| 9·10·11, VAD 4): 가짜 조건을 만들지 않고 원인을 밝혀 멈춘다 ─────────────────────────────
    rig = ("*KEYWORD\n" + node_block(cubes(3)) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1) + hex_row(2, 4, 9) + hex_row(3, 5, 17)
           + part(1) + part(4, 1, 4) + part(5, 1, 5) + SOLID1 + ELASTIC
           + "*MAT_RIGID\n" + f10(4, "7.85E-09", 210000.0, 0.3) + "*MAT_RIGID\n" + f10(5, "7.85E-09", 210000.0, 0.3)
           + "*DEFINE_CURVE\n" + f10(10) + f"{0.0:20.4f}{0.0:20.4f}\n{1.0:20.4f}{1.0:20.4f}\n")
    for kw, body in (("RIGID", f10(4, 3, 4, 10, 1.0) + f10(5.0, 0.0, 5, 0, 0) + f10(5, 1, 0, 10, 2.0)),
                     ("RIGID_ID", f"{71:10d}a\n" + f10(4, 9, 2, 10, 1.0) + f10(5.0, 0.0, 0, 0, 0) + f"{72:10d}b\n" + f10(5, 1, 0, 10, 2.0))):
        d, rc, log = run("pm_card3", {"model.k": rig + f"*BOUNDARY_PRESCRIBED_MOTION_{kw}\n" + body + "*END\n"})
        check(f"R4 *BOUNDARY_PRESCRIBED_MOTION_{kw} 카드 3 이 오는 조건(VAD 4·DOF 9): 가짜 조건 없이 원인을 밝혀 멈춘다(rc 1)",
              rc == 1 and "카드 3" in log, f"rc={rc} " + log[-300:])

    # ── 가져온 *ELEMENT_MASS_NODE_SET 의 절점 셋 번호 ─────────────────────────────────────────────────────────
    nm = lambda m: "*SET_NODE_LIST\n" + f10(1) + f10(1, 2, 3, 4) + "*ELEMENT_MASS_NODE_SET\n" + f"{60:8d}{1:8d}{m:16.6f}\n"
    d, rc, log = run("im_mass_nset", {"base.k": one(1, 1, 1, "a") + steel + nm(0.001) + "*END\n",
                                      "imp.k": one(1, 1, 2, "b") + alu2 + nm(0.555) + "*END\n"}, IMO)
    t = read(d, "base_imported.k")
    rows = [r for _, rr in kw_blocks(t, "*ELEMENT_MASS_NODE_SET") for r in rr]
    ms = try_(lambda: sorted((int(r[:8]), int(r[8:16]), round(float(r[16:32]), 6)) for r in rows), [])
    nsets = {}
    for kw in ("*SET_NODE_LIST", "*SET_NODE_LIST_TITLE"):
        for h, rr in kw_blocks(t, kw):
            rr = rr[1:] if kw.endswith("_TITLE") else rr
            nsets[int(rr[0][:10])] = [x for r in rr[1:] for x in ints(r, 10) if x]
    imp_m = [m for m in ms if m[2] == 0.555]
    check("R4 IMPORT_MERGE_K 가져온 *ELEMENT_MASS_NODE_SET: 가져온 절점 셋(가져온 절점)을 가리킨다(기준 셋 1 이 아니다)",
          rc == 0 and len(ms) == 2 and (60, 1, 0.001) in ms and len(imp_m) == 1 and imp_m[0][1] != 1
          and all(n > 8 for n in nsets.get(imp_m[0][1], [0])), f"rc={rc} {ms} {nsets}")

    # ── 일반 *ELEMENT_SHELL 이 줄마다 칸 수를 센다(4절점 줄 뒤 8절점 줄, 삼각형 줄 뒤 사각형 줄) ───────────────────────────
    pts = {k: (float(k % 7), float(k // 7), 0.0) for k in (1, 2, 3, 4, 11, 12, 13, 14, 15, 16, 17, 18, 21, 22, 23, 24)}
    sh = ("*KEYWORD\n" + node_block(pts) + "*ELEMENT_SHELL\n" + f"{1:8d}{1:8d}{1:8d}{2:8d}{3:8d}\n"
          + f"{2:8d}{1:8d}" + "".join(f"{n:8d}" for n in (11, 12, 13, 14, 15, 16, 17, 18)) + "\n"
          + f"{3:8d}{1:8d}{21:8d}{22:8d}{23:8d}{24:8d}\n" + part(1, 1, 1, "shell") + "*SECTION_SHELL\n" + f10(1, 2)
          + f10(1.0, 1.0, 1.0, 1.0) + ELASTIC + "*END\n")
    d, rc, log = run("shell_mixed", {"model.k": sh})
    e = elements(read(d, "model_trans.k"), "*ELEMENT_SHELL")
    check("R4 *ELEMENT_SHELL 삼각형(40자)·8절점·사각형 줄: 중간 절점 N5~N8·뒤 사각형 N4 가 잘리지 않는다",
          rc == 0 and e.get(2, [(0, [])])[0][1][:8] == [11, 12, 13, 14, 15, 16, 17, 18] and e.get(3, [(0, [])])[0][1][:4] == [21, 22, 23, 24],
          f"rc={rc} {e}")

    # ── Fast DROP(여러 각도) + 강체화: 각도마다 같은 강체 파트·바닥판, EID 겹침 없음 ────────────────────────────────
    d, rc, log = run("drop_rigidify", {"model.k": M.base_deck(raw=True)}, drop([0, 90, 180], "RigidifyElementIDs,1\n"))
    outs = dropsets(d)
    parts3 = [sorted(M.parts_of(t)) for t in outs]
    dups = [sorted(k for k, v in elements(t).items() if len(v) > 1) for t in outs]
    check("R4 DROP 3각도 + RigidifyElementIDs: 각도마다 같은 파트(강체 파트·바닥판)이고 솔리드 EID 가 겹치지 않는다",
          rc == 0 and len(outs) == 3 and parts3[0] == parts3[1] == parts3[2] and len(parts3[0]) >= 6 and not any(dups),
          f"rc={rc} {parts3} {dups}")

    # ── *DATABASE_HISTORY: 짧은 콤마 줄·고정폭 두 줄·값 11개(카드는 8칸) ───────────────────────────────────────────
    d, rc, log = run("hist_r4", {"model.k": cube_deck("*DATABASE_HISTORY_NODE\n1,2,3\n*DATABASE_HISTORY_NODE\n" + f10(1, 2, 3, 4)
                                                       + f10(5, 6, 7, 8) + "*DATABASE_HISTORY_SOLID\n1,2,3,4,5,6,7,8,9,10,11\n")})
    t = read(d, "model_trans.k")
    hn = [x for _, rows in kw_blocks(t, "*DATABASE_HISTORY_NODE") for r in rows for x in ints(r, 10) if x]
    hs = [x for _, rows in kw_blocks(t, "*DATABASE_HISTORY_SOLID") for r in rows for x in ints(r, 10) if x]
    check("R4 *DATABASE_HISTORY: '1,2,3'·고정폭 두 줄의 ID 가 모두 남고, 값 11개 콤마 줄은 카드 8칸만",
          rc == 0 and hn == [1, 2, 3, 1, 2, 3, 4, 5, 6, 7, 8] and hs == [1, 2, 3, 4, 5, 6, 7, 8], f"rc={rc} node={hn} solid={hs}")

    # ── 카드 칸 수보다 많은 콤마 값은 다음 카드로 밀리지 않는다(PLP 카드 3·4 의 9번째 값) ───────────────────────────────
    plp = ("*MAT_PIECEWISE_LINEAR_PLASTICITY\n" + f10(2, "7.85E-09", 210000.0, 0.3, 250.0, 0.0, 0.0, 0.0) + f10(0.0, 0.0, 0, 0, 0.0)
           + "0.0,0.01,0.02,0.05,0.1,0.2,0.3,0.5,0.9\n250,260,270,290,310,330,345,360,400\n")
    d, rc, log = run("plp_comma9", {"model.k": cube_deck(plp)})
    t = read(d, "model_trans.k")
    pb = [(rows[1:] if h.split()[0].upper().endswith("_TITLE") else rows)
          for h, rows in kw_blocks(t, "*MAT_PIECEWISE_LINEAR_PLASTICITY") + kw_blocks(t, "*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE")]
    c34 = try_(lambda: [floats(pb[0][2], 10), floats(pb[0][3], 10)], [])
    check("R4 콤마 PLP 카드 3·4 의 9번째 값: 버려지고 카드 4 첫 값이 ES1 = 250(0.9 가 아니다), 카드는 4장",
          rc == 0 and len(pb) == 1 and len(pb[0]) == 4 and len(c34) == 2 and c34[0][7] == 0.5 and c34[1][0] == 250.0,
          f"rc={rc} {pb}")

    # ── IMPORT_MERGE_K: TMID 는 MID 가 아니다·원문 EOS·원문 좌표계·long 원문 단면·기준 덱만의 침식·재질 값 비교 ─────────────────
    thermal = "*MAT_THERMAL_ISOTROPIC\n" + f10(1, "7.85e-09", 0, 0, 0) + f10(460000000.0, 50.0)
    d, rc, log = run("im_thermal", {"base.k": one(1, 1, 2, "a") + alu2 + thermal + "*END\n", "imp.k": one(1, 1, 1, "b") + steel + "*END\n"}, IMO)
    t = read(d, "base_imported.k")
    mids = sorted(int((rows[1] if h.split()[0].upper().endswith("_TITLE") else rows[0])[:10])
                  for h, rows in kw_blocks(t, "*MAT_ELASTIC") + kw_blocks(t, "*MAT_ELASTIC_TITLE"))
    check("R4 IMPORT_MERGE_K 기준 덱 *MAT_THERMAL_ISOTROPIC TMID 1 · 가져온 *MAT_ELASTIC 1: 충돌이 아니다(rc 0, 재질 1·2)",
          rc == 0 and mids == [1, 2], f"rc={rc} {mids} " + log[-300:])
    cases = (("im_eos_raw", "*EOS_GRUNEISEN\n" + f10(1, 1480.0, 1.92, 0.0, 0.0, 0.1, 0.0, 0.0) + f10(0.0),
              "*EOS_LINEAR_POLYNOMIAL\n" + f10(1, 0.0, 2200.0, 0.0, 0.0, 0.0, 0.0, 0.0) + f10(0.0, 0.0), "EOS 1(기준 덱 원문 EOS)"),
             ("im_cs_nodes", "*DEFINE_COORDINATE_NODES\n" + f10(5, 1, 2, 4),
              "*DEFINE_COORDINATE_SYSTEM\n" + f10(5, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0) + f10(-1.0, 0.0, 0.0), "좌표계 CID 5(기준 덱 원문 좌표계)"),
             ("im_ero_base", "*MAT_ADD_EROSION\n" + f10(1, 0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0) + f10(0.0, 0.0, 0.0, 0.25), "",
              "MAT_ADD_EROSION MID 1(기준 덱에만 있다"),
             ("im_mid_near", "", "", "재질 MID 1"))
    for name, base_x, imp_x, want in cases:
        imp_mat = steel.replace("210000", "210040") if name == "im_mid_near" else steel
        d, rc, log = run(name, {"base.k": one(1, 1, 1, "a") + steel + base_x + "*END\n",
                                "imp.k": one(1, 1, 1, "b") + imp_mat + imp_x + "*END\n"}, IMO)
        check(f"R4 IMPORT_MERGE_K {name}: 번호 충돌을 🔴 rc 3 으로 알린다('{want}')", rc == 3 and want in log, f"rc={rc} " + log[-300:])

    def l20(*v):
        return "".join(f"{x:>20}" for x in v) + "\n"
    d, rc, log = run("im_rawsec_long", {"base.k": one(1, 1, 1, "a") + steel + "*SECTION_DISCRETE +\n" + l20(6, 0, 0.0, 0.0, 0.0, 0.0)
                                        + l20(0.0, 0.0) + "*MAT_SPRING_ELASTIC\n" + f10(6, 1000.0) + "*END\n",
                                        "imp.k": one(1, 5, 2, "b") + alu2 + "*END\n"}, IMO)
    t = read(d, "base_imported.k")
    secs = []
    for kw in sorted({ln.split()[0].upper() for ln in t.splitlines() if ln.startswith("*SECTION_")}):
        for h, rows in kw_blocks(t, kw):
            w = 20 if "+" in h.split()[1:] else 10
            r0 = rows[1] if kw.endswith("_TITLE") else rows[0]
            secs.append(try_(lambda: int(float(r0[:w])), -1))
    check("R4 IMPORT_MERGE_K 기준 덱 long('+') 원문 *SECTION_DISCRETE 6: 가져온 단면이 6 과 겹치지 않는다",
          rc == 0 and len(secs) == len(set(secs)) and -1 not in secs, f"rc={rc} {secs}")

    # ── DTI: 이번 dynain 에 같은 종류가 없는 기준 덱 원문 *INITIAL_STRESS_SHELL 은 지우지 않고 알린다 ──────────────────────
    pts = dict(cubes(1))
    pts.update({50: (5.0, 0.0, 0.0), 51: (6.0, 0.0, 0.0), 52: (6.0, 1.0, 0.0), 53: (5.0, 1.0, 0.0)})
    el = "*ELEMENT_SOLID\n" + hex_row(1, 1, 1) + "*ELEMENT_SHELL\n" + f"{9:8d}{3:8d}{50:8d}{51:8d}{52:8d}{53:8d}\n"
    base = ("*KEYWORD\n*CONTROL_TERMINATION\n" + f10(0.001) + node_block(pts) + el + part(1) + part(3, 3, 1) + SOLID1
            + "*SECTION_SHELL\n" + f10(3, 2, 0.8333, 3) + f10(0.5, 0.5, 0.5, 0.5) + ELASTIC
            + "*INITIAL_STRESS_SHELL\n" + f10(9, 1, 1, 0, 0) + f10(0.0, 50.0, 50.0, 0.0, 0.0, 0.0, 0.0, 0.0) + "*END\n")
    dyn = ("*KEYWORD\n" + node_block({k: (x, y, z + 0.01) for k, (x, y, z) in pts.items()}) + el
           + "*INITIAL_STRESS_SOLID\n" + f10(1, 1, 0, 0, 0, 0, 0, 0) + f10(1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 0.01) + "*END\n")
    dti = ("*Inputfile\nmodel.k\n*Mode\nDYNAIN_TO_INITIAL,1\n**DynainToInitial,1\n*DynainPath,dynain\n*IncludeStress,True\n"
           "*RemoveDynamicRelaxation,True\n**EndDynainToInitial\n*End\n")
    d, rc, log = run("dti_user_shell", {"model.k": base, "dynain": dyn}, dti)
    kws = [ln.split()[0].upper() for ln in read(d, "model_dti.k").splitlines() if ln.startswith("*")]
    check("R4 DTI: dynain 에 셸 응력이 없으면 기준 덱 *INITIAL_STRESS_SHELL 을 지우지 않고 ⚠ 로 알린다",
          rc == 0 and "*INITIAL_STRESS_SHELL" in kws and "*INITIAL_STRESS_SOLID" in kws and "⚠ DTI" in log, f"rc={rc} {kws}")

    # ── *NODE 콤마 줄의 남는 값(7번째)은 버리고 절점은 읽는다 ─────────────────────────────────────────────────────
    d, rc, log = run("node_7vals", {"model.k": cube_deck().replace("*ELEMENT_SOLID", "99,1.0,0.0,0.0,0,0,7\n*ELEMENT_SOLID", 1)})
    nd = nodes(read(d, "model_trans.k"))
    check("R4 *NODE '99,1.0,0.0,0.0,0,0,7': 절점 99 를 읽는다(rc 0)", rc == 0 and 99 in nd and near(nd[99][0], 1.0), f"rc={rc} " + log[-300:])

    # ── DROP 바닥판 단면·재질 번호가 원문 *SECTION_DISCRETE·*MAT_SPRING_ELASTIC 과 겹치지 않는다 ─────────────────────────────
    sp = {**cubes(1), 41: (5.0, 0.0, 0.0), 42: (6.0, 0.0, 0.0)}
    deck = ("*KEYWORD\n" + node_block(sp) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1) + part(1) + SOLID1 + ELASTIC + part(6, 3, 2, "spring")
            + "*SECTION_DISCRETE\n" + f10(3, 0, 0.0, 0.0, 0.0, 0.0) + f10(0.0, 0.0) + "*MAT_SPRING_ELASTIC\n" + f10(2, 1000.0)
            + "*ELEMENT_DISCRETE\n" + f"{50:8d}{6:8d}{41:8d}{42:8d}{0:8d}{1.0:16.4f}{0:8d}{0.0:16.4f}\n" + "*END\n")
    d, rc, log = run("drop_rawsecmat", {"model.k": deck}, drop([0]))
    outs = dropsets(d)
    floor = {pid: sm for pid, sm in part_cards(outs[0]).items() if pid not in (1, 6)} if outs else {}
    check("R4 DROP 바닥판 SECID·MID 가 원문 *SECTION_DISCRETE 3·*MAT_SPRING_ELASTIC 2 와 겹치지 않는다",
          rc == 0 and len(floor) == 1 and all(sec != 3 and mid != 2 for sec, mid in floor.values()), f"rc={rc} {floor}")

    # ── 덱 D2R 이 SWSET 20 을 쓰면 KMM 짝 스위치는 다른 번호 ─────────────────────────────────────────────────────
    d2r20 = "*DEFORMABLE_TO_RIGID_AUTOMATIC\n" + f10(20, 0, 0.0, 0.0, 0.0, 0, 0, 0) + f10(0, 0, 0, 0.0, 1, 0, 0.0) + f10(2, 0)
    d, rc, log = run("drop_swset20", {"model.k": M.base_deck(raw=True, extra=d2r20)}, drop([0], "DeformableToRigid,True\n"))
    outs = dropsets(d)
    sws = sorted(int(rows[0][:10]) for _, rows in kw_blocks(outs[0], "*DEFORMABLE_TO_RIGID_AUTOMATIC") if rows) if outs else []
    check("R4 DROP DeformableToRigid + 덱 D2R SWSET 20: SWSET 이 겹치지 않는다(덱 20 + KMM 짝 둘)",
          rc == 0 and len(sws) == 3 and len(set(sws)) == 3 and 20 in sws, f"rc={rc} {sws}")


def r5():
    print("[R5] 콤마 빈 칸 리더·제어 기본값, 셸 짧은 끝 칸, 솔리드 1줄 꼴, GENERAL_VISCOELASTIC 카드 2, IMPORT_MERGE_K 침식·좌표계, DTI D2R")
    # ── 콤마 줄 빈 값은 '' — 빈 칸을 len()==0 으로 가리는 리더가 죽지 않고, 제어 카드 빈 칸은 R16 기본값 ─────────────────────
    d, rc, log = run("initvel_comma", {"model.k": cube_deck("*SET_NODE_LIST\n" + f10(1) + f10(1, 2) + "*INITIAL_VELOCITY\n1,\n"
                                                             + f10(0.0, 0.0, -1000.0))})
    check("R5 콤마 *INITIAL_VELOCITY '1,': 죽지 않는다(rc 0)", rc == 0 and no_tb(log), f"rc={rc} " + log[-300:])
    d, rc, log = run("ctrl_comma", {"model.k": cube_deck("*CONTROL_HOURGLASS\n4,\n")})
    hg = [floats(rows[0], 10) for _, rows in kw_blocks(read(d, "model_trans.k"), "*CONTROL_HOURGLASS") if rows]
    check("R5 콤마 *CONTROL_HOURGLASS '4,': 빈 QH 는 R16 기본값 0.1(0 이 아니다)", rc == 0 and hg and hg[0][:2] == [4, 0.1], f"rc={rc} {hg}")

    # ── 셸 끝 칸이 8자를 못 채운 줄·솔리드 둘째 줄이 짧은 1줄 꼴(사면체) ─────────────────────────────────────────────────
    pts = {k: (float(k % 3), float(k // 3), 0.0) for k in range(1, 9)}
    sh = ("*KEYWORD\n" + node_block(pts) + "*ELEMENT_SHELL\n" + f"{1:8d}{1:8d}{1:8d}{2:8d}{3:8d}{4:8d}\n"
          + f"{2:8d}{1:8d}{2:8d}{5:8d}{6:8d}" + "   3\n" + part(1, 1, 1, "shell") + "*SECTION_SHELL\n" + f10(1, 2)
          + f10(1.0, 1.0, 1.0, 1.0) + ELASTIC + "*END\n")
    d, rc, log = run("shell_ragged", {"model.k": sh})
    e = elements(read(d, "model_trans.k"), "*ELEMENT_SHELL")
    check("R5 *ELEMENT_SHELL 끝 칸 '   3'(44자 줄): 사각형 N4 = 3 을 읽는다(삼각형이 되지 않는다)",
          rc == 0 and e.get(2, [(0, [])])[0][1][:4] == [2, 5, 6, 3], f"rc={rc} {e}")
    sol = ("*KEYWORD\n" + node_block(cubes(3)) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1)
           + f"{2:8d}{1:8d}{9:8d}{10:8d}{11:8d}{13:8d}\n" + hex_row(3, 1, 17) + part(1) + SOLID1 + ELASTIC + "*END\n")
    d, rc, log = run("solid_short2nd", {"model.k": sol})
    e = elements(read(d, "model_trans.k"))
    check("R5 *ELEMENT_SOLID 둘째 줄이 사면체(48자): 2줄 꼴로 뒤섞지 않고 요소 1·2·3 그대로",
          rc == 0 and e.get(1, [(0, [])])[0][1] == list(range(1, 9)) and e.get(2, [(0, [])])[0][1][:4] == [9, 10, 11, 13]
          and e.get(3, [(0, [])])[0][1] == list(range(17, 25)), f"rc={rc} {e}")

    # ── *MAT_GENERAL_VISCOELASTIC 카드 2 는 8칸 ─────────────────────────────────────────────────────────────────
    gv = "*MAT_GENERAL_VISCOELASTIC\n2,1.0E-9,2000.0\n7,6,0.0,0.0,8,6,0.0,0.0\n10.0,100.0,20.0,200.0\n"
    d, rc, log = run("gv_card2", {"model.k": cube_deck(gv)})
    rows = [r for _, rr in kw_blocks(read(d, "model_trans.k"), "*MAT_GENERAL_VISCOELASTIC") for r in rr]
    c2 = try_(lambda: floats(rows[1], 10), [])
    check("R5 *MAT_GENERAL_VISCOELASTIC 카드 2 'LCID…TRAMPK' 8칸: LCIDK 8·NTK 6 이 남는다", rc == 0 and c2[:6] == [7, 6, 0, 0, 8, 6],
          f"rc={rc} {rows}")

    # ── IMPORT_MERGE_K: 침식 카드 3 의 다름·쓰지 않는 MID 의 기준 덱 침식·원문 좌표계 둘째 줄 ────────────────────────────
    one = lambda pid, sec, mid, name: ("*KEYWORD\n" + node_block(cubes(1)) + "*ELEMENT_SOLID\n" + hex_row(1, pid, 1)
                                       + part(pid, sec, mid, name) + "*SECTION_SOLID\n" + f10(sec, 1))
    steel = "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
    ero = lambda dcrit: ("*MAT_ADD_EROSION\n" + f10(1, 0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0) + f10(0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0)
                         + f10(1, 0, 5, 0.0, 2.0, dcrit, 1.0, 0))   # IDAM 1 — 카드 3 의 2~7칸은 IDAM≠0 일 때만 뜻이 있다(R16, 리뷰 R6)
    d, rc, log = run("im_ero_card3", {"base.k": one(1, 1, 1, "a") + steel + ero(0.1) + "*END\n",
                                      "imp.k": one(1, 1, 1, "b") + steel + ero(0.9) + "*END\n"}, IMO)
    check("R5 IMPORT_MERGE_K 침식 카드 3(IDAM 1)의 DCRIT 만 다름(0.1 / 0.9): 번호 충돌 🔴 rc 3", rc == 3 and "MAT_ADD_EROSION MID 1" in log,
          f"rc={rc} " + log[-300:])
    alu2 = "*MAT_ELASTIC\n" + f10(2, "2.70E-09", 70000, 0.33)
    d, rc, log = run("im_ero_unused", {"base.k": one(1, 1, 1, "a") + steel + ero(0.1) + "*END\n",
                                       "imp.k": one(1, 1, 2, "b") + steel + alu2 + "*END\n"}, IMO)
    check("R5 IMPORT_MERGE_K 기준 덱만의 침식 MID 1 을 가져온 파트가 쓰지 않으면(MID 2): 충돌이 아니다(rc 0)",
          rc == 0 and "번호 충돌" not in log, f"rc={rc} " + log[-300:])
    d, rc, log = run("im_cs_nodes2", {"base.k": one(1, 1, 1, "a") + steel + "*DEFINE_COORDINATE_NODES\n" + f10(5, 1, 2, 4) + f10(6, 1, 3, 4)
                                      + "*END\n", "imp.k": one(1, 1, 2, "b") + alu2 + "*DEFINE_COORDINATE_SYSTEM\n"
                                      + f10(6, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0) + f10(-1.0, 0.0, 0.0) + "*END\n"}, IMO)
    check("R5 IMPORT_MERGE_K 원문 *DEFINE_COORDINATE_NODES 둘째 줄 CID 6 과 가져온 좌표계 6: 번호 충돌 🔴 rc 3",
          rc == 3 and "좌표계 CID 6" in log, f"rc={rc} " + log[-300:])

    # ── DTI 가 지운 접촉을 가리키는 덱 D2R 짝도 지운다(누적 낙하 체인) ─────────────────────────────────────────────────────
    con = ("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID\n" + f"{1:10d}floor\n" + f10(1, 2, 3, 3) + f10(0.1, 0.1) + f10(1.0, 1.0)
           + "*DEFORMABLE_TO_RIGID_AUTOMATIC\n" + f10(20, 2, 0.0, "1e20", 0.0, 1, 10, 1) + f10(0, 0, 0, 0.0, 1, 0, 0.0) + f10(1, 0)
           + "*DEFORMABLE_TO_RIGID_AUTOMATIC\n" + f10(10, 4, 0.0, "1e20", 0.0, 1, 20, -1) + f10(0, 0, 0, 0.0, 0, 1, 0.0) + f10(1))
    base = ("*KEYWORD\n*CONTROL_TERMINATION\n" + f10(0.001) + node_block(cubes(2)) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1)
            + hex_row(2, 2, 9) + part(1) + part(2) + SOLID1 + ELASTIC + con + "*END\n")
    dyn = ("*KEYWORD\n" + node_block({k: (x, y, z + 0.01) for k, (x, y, z) in cubes(2).items()}) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1)
           + hex_row(2, 2, 9) + "*INITIAL_STRESS_SOLID\n" + f10(1, 1, 0, 0, 0, 0, 0, 0) + f10(1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 0.01) + "*END\n")
    dti = ("*Inputfile\nmodel.k\n*Mode\nDYNAIN_TO_INITIAL,1\n**DynainToInitial,1\n*DynainPath,dynain\n*IncludeStress,True\n"
           "*RemoveContactbyID,1\n**EndDynainToInitial\n*End\n")
    d, rc, log = run("dti_d2r", {"model.k": base, "dynain": dyn}, dti)
    kws = [ln.split()[0].upper() for ln in read(d, "model_dti.k").splitlines() if ln.startswith("*")]
    check("R5 DTI *RemoveContactbyID,1: 그 접촉을 ENTNO 로 가리키는 덱 D2R 짝(SWSET 20·10)도 지운다",
          rc == 0 and "*DEFORMABLE_TO_RIGID_AUTOMATIC" not in kws and "D2R" in log, f"rc={rc} {kws}")


def r6():
    print("[R6] DTI 접촉·D2R(파트 지움·강체벽 CODE·지우지 못한 접촉·짝 한쪽·사용자 짝), 침식 카드 3(IDAM)·원문 칸, 80열 뒤 글자, I10 짧은 끝 칸, 강체벽 번호")

    def deck(n, extra):
        """파트 k(솔리드 육면체 k) n 개 + extra."""
        return ("*KEYWORD\n*CONTROL_TERMINATION\n" + f10(0.001) + node_block(cubes(n)) + "*ELEMENT_SOLID\n"
                + "".join(hex_row(k + 1, k + 1, 8 * k + 1) for k in range(n)) + "".join(part(k + 1) for k in range(n))
                + SOLID1 + ELASTIC + extra + "*END\n")

    def dyn(n):
        return ("*KEYWORD\n" + node_block({k: (x, y, z + 0.01) for k, (x, y, z) in cubes(n).items()}) + "*ELEMENT_SOLID\n"
                + "".join(hex_row(k + 1, k + 1, 8 * k + 1) for k in range(n))
                + "*INITIAL_STRESS_SOLID\n" + f10(1, 1, 0, 0, 0, 0, 0, 0) + f10(1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 0.01) + "*END\n")

    def dti(lines):
        return ("*Inputfile\nmodel.k\n*Mode\nDYNAIN_TO_INITIAL,1\n**DynainToInitial,1\n*DynainPath,dynain\n*IncludeStress,True\n"
                + lines + "**EndDynainToInitial\n*End\n")

    def con(cid, name, ss, ms, kind="AUTOMATIC_SURFACE_TO_SURFACE"):
        return f"*CONTACT_{kind}_ID\n{cid:10d}{name}\n" + f10(ss, ms, 3, 3) + f10(0.1, 0.1) + f10(1.0, 1.0)

    def d2r(sw, code, entno, rel, paired):
        """D2R 한 세트 — paired 1 = 파트 1 변형→강체, -1 = 강체→변형."""
        c2 = f10(0, 0, 0, 0.0, 1, 0, 0.0) + f10(1, 0) if paired >= 0 else f10(0, 0, 0, 0.0, 0, 1, 0.0) + f10(1)
        return "*DEFORMABLE_TO_RIGID_AUTOMATIC\n" + f10(sw, code, 0.0, "1e20", 0.0, entno, rel, paired) + c2

    def cons_d2r(t):
        """({접촉 CID: 키워드}, [D2R SWSET…])."""
        cons = {}
        for kw in sorted({ln.split()[0].upper() for ln in t.splitlines() if ln.startswith("*CONTACT_")}):
            for _, rows in kw_blocks(t, kw):
                cons[try_(lambda: int(rows[0][:10]), -1)] = kw
        return cons, sorted(try_(lambda: int(rows[0][:10]), -1) for _, rows in kw_blocks(t, "*DEFORMABLE_TO_RIGID_AUTOMATIC") if rows)

    # ── DTI *RemovePartbyID: 지운 파트를 쓰지 않는 접촉(MSTYP 3)은 남는다 ─────────────────────────────────────────────
    d, rc, log = run("dti_rmpart_tied", {"model.k": deck(3, con(7, "bond12", 1, 2, "TIED_SURFACE_TO_SURFACE") + con(8, "floor", 1, 3)),
                                         "dynain": dyn(3)}, dti("*RemovePartbyID,3\n*RemoveContactbyID,8\n"))
    t = read(d, "model_dti.k")
    cons, sws = cons_d2r(t)
    check("R6 DTI *RemovePartbyID,3: 파트 1·2 의 TIED 접촉 7 은 남고(MSTYP 3 인 접촉을 모두 지우지 않는다) 파트 3·접촉 8 만 지운다",
          rc == 0 and cons == {7: "*CONTACT_TIED_SURFACE_TO_SURFACE_ID"} and sorted(M.parts_of(t)) == [1, 2], f"rc={rc} {cons} {M.parts_of(t)}")

    # ── DTI 가 지우는 덱 D2R: 접촉력 전환(CODE 2·4)만, 실제로 없어진 접촉만, 짝은 함께, 다른 접촉의 사용자 짝은 남긴다 ─────────────────
    rw = "*RIGIDWALL_PLANAR_ID\n" + f"{1:10d}floorwall\n" + f10(0, 0, 0, 0.0, 0.0, "1.0E+20", 1.0) + f10(0.0, 0.0, -0.1, 0.0, 0.0, 1.0, 0.0, 0.0)
    d, rc, log = run("dti_d2r_rw", {"model.k": deck(2, rw + con(1, "inner", 1, 2) + d2r(20, 1, 1, 10, 1) + d2r(10, 3, 1, 20, -1)),
                                    "dynain": dyn(2)}, dti("*RemoveContactbyID,1\n"))
    cons, sws = cons_d2r(read(d, "model_dti.k"))
    check("R6 DTI *RemoveContactbyID,1 + 강체벽 1 의 D2R 짝(CODE 1·3 = 강체벽 힘): 접촉 1 만 지우고 D2R 짝 20·10 은 남긴다",
          rc == 0 and cons == {} and sws == [10, 20], f"rc={rc} {cons} {sws}")
    d, rc, log = run("dti_d2r_raw", {"model.k": deck(2, con(5, "n2sfloor", 1, 2, "AUTOMATIC_NODES_TO_SURFACE") + d2r(20, 2, 5, 10, 1)
                                                     + d2r(10, 4, 5, 20, -1)), "dynain": dyn(2)}, dti("*RemoveContactbyID,5\n"))
    cons, sws = cons_d2r(read(d, "model_dti.k"))
    check("R6 DTI *RemoveContactbyID,5(KMM 이 해석하지 않는 원문 N2S 접촉): 접촉이 남으면 그 D2R 짝도 남고 ⚠ 로 알린다",
          rc == 0 and ((5 in cons and sws == [10, 20] and "⚠ DTI" in log) or (5 not in cons and sws == [])), f"rc={rc} {cons} {sws}")
    d, rc, log = run("dti_d2r_half", {"model.k": deck(2, con(1, "floor", 1, 2) + d2r(20, 0, 0, 10, 1) + d2r(10, 4, 1, 20, -1)),
                                      "dynain": dyn(2)}, dti("*RemoveContactbyID,1\n"))
    cons, sws = cons_d2r(read(d, "model_dti.k"))
    check("R6 DTI *RemoveContactbyID,1 + 짝 한쪽만 접촉 1 을 가리킴(SWSET 10 CODE 4 · 짝 20 CODE 0): 짝 둘 다 지운다",
          rc == 0 and cons == {} and sws == [], f"rc={rc} {cons} {sws}")
    d, rc, log = run("dti_d2r_user", {"model.k": deck(3, con(1, "user", 1, 2) + d2r(20, 2, 1, 10, 1) + d2r(10, 4, 1, 20, -1)
                                                      + con(2, "floor", 1, 3) + d2r(40, 2, 2, 30, 1) + d2r(30, 4, 2, 40, -1)),
                                      "dynain": dyn(3)}, dti("*RemovePartbyID,3\n*RemoveContactbyID,2\n"))
    cons, sws = cons_d2r(read(d, "model_dti.k"))
    check("R6 DTI 바닥판 파트·접촉 2 지움 + 사용자 접촉 1 의 D2R 짝: 접촉 1·짝 20·10 은 남고 접촉 2 의 짝 40·30 만 지운다",
          rc == 0 and cons == {1: "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID"} and sws == [10, 20], f"rc={rc} {cons} {sws}")

    # ── IMPORT_MERGE_K 침식: IDAM 0 이면 카드 3 의 2~7칸은 견주지 않고, 빈 칸·빠진 카드·주석 줄은 기본값과 같다 ───────────────────
    one = lambda pid, name: ("*KEYWORD\n" + node_block(cubes(1)) + "*ELEMENT_SOLID\n" + hex_row(1, pid, 1) + part(pid, 1, 1, name)
                             + SOLID1 + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3))
    c12 = "*MAT_ADD_EROSION\n" + f10(1, 0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0) + f10(0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0)
    pairs = (("IDAM 0 · DCRIT 0.1 / 0.9", c12 + f10(0, 0, 5, 0.0, 2.0, 0.1, 1.0, 0), c12 + f10(0, 0, 5, 0.0, 2.0, 0.9, 1.0, 0)),
             ("IDAM 1 · 카드 3 빈 칸 / 기본값", c12 + f"{1:10d}" + " " * 60 + f"{0:10d}\n", c12 + f10(1, 0, 0, 0.0, 1.0, 0.0, 1.0, 0)),
             ("카드 3 없음 / '0'", c12, c12 + f10(0)),
             ("카드 2장 / 카드 5장(기본값)", c12, c12 + f10(0, 0, 0, 0.0, 1.0, 0.0, 1.0, 0) + f10(0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0)
              + f10(0.0, 0.5, "1.0E+20", 0.0)),
             ("끝 주석 줄 '$' / 없음", c12 + "$\n", c12))
    for k, (what, b, i) in enumerate(pairs):
        d, rc, log = run(f"im_ero_same{k}", {"base.k": one(1, "a") + b + "*END\n", "imp.k": one(1, "b") + i + "*END\n"}, IMO)
        check(f"R6 IMPORT_MERGE_K 같은 침식({what}): 충돌이 아니다(rc 0)", rc == 0 and "번호 충돌" not in log, f"rc={rc} " + log[-300:])

    # ── 원문 침식 카드: 콤마 줄의 빈 칸은 자리를 지키고, 고정폭 줄 끝에 공백이 붙지 않는다 ─────────────────────────────────
    d, rc, log = run("ero_rawcard", {"model.k": cube_deck("*MAT_ADD_EROSION\n" + f10(1, 0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0) + "0.0,,,0.25\n"
                                                          + f10(0))})
    rows = [r for _, rr in kw_blocks(read(d, "model_trans.k"), "*MAT_ADD_EROSION") for r in rr]
    check("R6 원문 *MAT_ADD_EROSION '0.0,,,0.25'·'         0': MXEPS 0.25 는 넷째 칸, 줄 끝 공백 없음",
          rc == 0 and rows[1:] == ["       0.0" + " " * 20 + "      0.25", "         0"], f"rc={rc} {rows}")

    # ── 80열 뒤 글자(R16 은 읽지 않는다)와 I10 끝 칸이 10자를 못 채운 셸·솔리드·빔 줄 ───────────────────────────────────────
    sol = ("*KEYWORD\n" + node_block(cubes(3)) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1) + hex_row(2, 1, 9) + hex_row(3, 1, 17)[:-1] + "   #3\n"
           + part(1) + SOLID1 + ELASTIC + "*END\n")
    d, rc, log = run("solid_col81", {"model.k": sol})
    e = elements(read(d, "model_trans.k"))
    check("R6 *ELEMENT_SOLID 셋째 줄 81열 뒤 '   #3': 요소 1·2·3 이 모두 남는다",
          rc == 0 and [e.get(k, [(0, [])])[0][1] for k in (1, 2, 3)] == [list(range(1, 9)), list(range(9, 17)), list(range(17, 25))],
          f"rc={rc} {e}")
    sq = {k: (float(k % 3), float(k // 3), 0.0) for k in range(1, 9)}
    i10 = (("*ELEMENT_SHELL", sq, f10(1, 1, 1, 2, 3, 4) + f10(2, 1, 2, 5, 6)[:-1] + "   3\n",
            part(1, 1, 1, "shell") + "*SECTION_SHELL\n" + f10(1, 2) + f10(1.0, 1.0, 1.0, 1.0), 2, [2, 5, 6, 3]),
           ("*ELEMENT_SOLID", cubes(2), f10(1, 1, *range(1, 9)) + f10(2, 1, *range(9, 16))[:-1] + "  16\n", part(1) + SOLID1, 2, list(range(9, 17))),
           ("*ELEMENT_BEAM", {1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (0.0, 1.0, 0.0)}, f10(1, 1, 1, 2)[:-1] + "  3\n",
            part(1, 1, 1, "beam") + "*SECTION_BEAM\n" + f10(1, 1, 1.0, 2) + f10(1.0, 1.0, 0.0, 0.0), 1, [1, 2, 3]))
    for kw, pts, rows, rest, eid, want in i10:
        d, rc, log = run("i10_ragged", {"model.k": "*KEYWORD I10=Y\n" + node_block(pts, 10) + kw + "\n" + rows + rest + ELASTIC + "*END\n"})
        got = elements(read(d, "model_trans.k"), kw).get(eid, [(0, [])])[0][1][:len(want)]
        check(f"R6 I10 {kw} 끝 칸이 10자를 못 채운 줄: 절점 {want} 를 모두 읽는다", rc == 0 and got == want, f"rc={rc} {got}")

    # ── 번호 없는 *RIGIDWALL_PLANAR 와 *RIGIDWALL_PLANAR_ID 1: 벽 둘이 모두 남는다 ───────────────────────────────────────
    walls = rw + "*RIGIDWALL_PLANAR\n" + f10(0, 0, 0, 0.0, 0.0, "1.0E+20", 1.0) + f10(0.0, 0.0, -0.2, 0.0, 0.0, 1.0, 0.2, 0.0)
    d, rc, log = run("rigidwall_ids", {"model.k": cube_deck(walls)})
    t = read(d, "model_trans.k")
    # 누적 체인 묶음 W1(2026-11-08) 뒤로 KMM 은 읽은 종류 그대로 쓴다 — 번호 없는 벽은 번호 없이(LS-DYNA 가 정의 차례로 번호를 준다) 나간다
    got = [(kw, rid, round(c[2], 4) if c else None) for kw, rid, c in rigidwalls(t)]
    check("R6 *RIGIDWALL_PLANAR(번호 없음) + *RIGIDWALL_PLANAR_ID 1: 벽 둘(번호 없는 벽 ZT -0.2·_ID 1 ZT -0.1)이 남는다",
          rc == 0 and len(got) == 2 and sorted(g[2] for g in got if g[2] is not None) == [-0.2, -0.1]
          and ("*RIGIDWALL_PLANAR", None, -0.2) in got and ("*RIGIDWALL_PLANAR_ID", 1, -0.1) in got, f"rc={rc} {got}")


def r7():
    print("[R7] DWI 다음 단계 DTI 의 DWI 접촉, 강체벽 차례, 재질 숫자 별칭, 침식 끝 빈 카드, D2R PAIRED 0 닫힘, long D2R SWSET, Fast DROP 강체벽")

    def walls_of(t):
        """출력 강체벽 [(번호 또는 None, XT·YT·ZT, 법선)] — 덱 차례대로(번호 없는 벽은 None — W1 뒤로 읽은 종류 그대로 나간다)."""
        out = []
        for kw, rid, c in rigidwalls(t):
            c = list(c or [0.0] * 6) + [0.0] * 6
            out.append((rid, tuple(round(x, 4) for x in c[:3]), tuple(round(c[k + 3] - c[k], 4) for k in range(3))))
        return out

    # ── DWI 다음 단계 DTI: DWI 가 만든 접촉(벽·임팩터·단 사이 TIED)은 지우고 사용자 접촉은 남긴다 ─────────────────────────────
    # BoundaryDistance 를 주지 않는다 — 시편 바깥을 강체로 바꾼 충격은 이제 다음 단계 DTI 가 멈춘다(누적 체인 묶음 S2, test_cumulative_chain s2)
    grid = {i * 4 + j + 1: (float(j), float(i), 0.0) for i in range(4) for j in range(4)}
    quads = "".join(f"{3 * i + j + 1:8d}{1:8d}" + "".join(f"{n:8d}" for n in (4 * i + j + 1, 4 * i + j + 2, 4 * i + j + 6, 4 * i + j + 5)) + "\n"
                    for i in range(3) for j in range(3))
    plate = ("*KEYWORD\n*CONTROL_TERMINATION\n" + f10(0.001) + node_block(grid) + "*ELEMENT_SHELL\n" + quads + part(1, 1, 1, "plate")
             + "*SECTION_SHELL\n" + f10(1, 2) + f10(0.5, 0.5, 0.5, 0.5) + "*MAT_ELASTIC\n" + f10(1, "2.70E-09", 70000, 0.33)
             + "*CONTACT_TIED_SURFACE_TO_SURFACE_ID\n" + f"{7:10d}usertied\n" + f10(1, 1, 3, 3) + f10(0.0, 0.0) + f10(1.0, 1.0) + "*END\n")
    dwi = ("*Inputfile\nmodel.k\n*RunDirectoryMode,True,runs\n*Mode\nDROP_WEIGHT_IMPACT_TEST,1\n**DropWeightImpactTest,1\nTFinal,0.0001\n"
           "DT,1e-05\nLocationX,1.5\nLocationY,1.5\nHeight,100\nInitialVelocityX,0\nInitialVelocityY,0\nInitialVelocityZ,0\nGravity,9810\n"
           "@IMP@MeshSize,0.25\nDensityImpactor,7.85e-09\nYoungsModulusImpactor,200000.0\nPoissonRatioImpactor,0.3\n"
           "GenerationMode,OutsideRigidElement\nOffsetDistance,0.05\nYoungsModulusWall,10000.0\nPoissonRatioWall,0.3\n"
           "DensityWall,1e-09\n**EndDropWeightImpactTest\n*End\n")
    dyn = "*KEYWORD\n" + node_block({k: (x, y, z + 0.01) for k, (x, y, z) in grid.items()}) + "*END\n"
    for name, imp in (("sphere", "ImpactorType,Sphere\nImpactorDimension,0.5\n"),
                      ("cyl3", "ImpactorType,Cylinder\nImpactorDimension,0.3,0.4,0.2,0.35,0.2,0.4,0.2\n")):
        d, rc, log = run(f"dwi_{name}", {"model.k": plate}, dwi.replace("@IMP@", imp))
        runs = sorted(Path(d).glob("runs/Run_*"))
        deck = read(runs[0], "DropWeightImpactTestSet.k") if runs else ""
        dti_opt = read(runs[0] / "DynamicRelaxation", "dynaintoinitial.txt") if runs else ""
        cids = sorted(c for c in cons_of(deck) if c != 7)
        rm = [ln for ln in dti_opt.splitlines() if ln.startswith("*RemoveContactbyID")]
        d2, rc2, log2 = run(f"dwi_{name}_dti", {"DropWeightImpactTestSet.k": deck, "dynain": dyn},
                            "\n".join("**DynainPath,dynain" if ln.startswith("**DynainPath") else ln for ln in dti_opt.splitlines()) + "\n")
        left = cons_of(read(d2, "DropWeightImpactTestSet_dti.k"))
        check(f"R7 DWI({name}) 다음 단계 DTI: DWI 접촉 {cids} 을 *RemoveContactbyID 로 적어 지우고 사용자 TIED 7 만 남긴다",
              rc == 0 and rc2 == 0 and len(cids) >= 2 and rm == ["*RemoveContactbyID," + ",".join(map(str, cids))] and sorted(left) == [7],
              f"rc={rc}/{rc2} {rm} cids={cids} left={left}")

    # ── 번호가 겹친 강체벽은 제자리에서 번호만 바꾼다(덱 정의 차례 = D2R CODE 1·3 ENTNO·RWFORC 차례) ──────────────────────────
    pl = lambda zt: f10(0, 0, 0, 0.0, 0.0, "1.0E+20", 1.0) + f10(0.0, 0.0, zt, 0.0, 0.0, 1.0, 0.0, 0.0)
    d, rc, log = run("rigidwall_order", {"model.k": cube_deck("*RIGIDWALL_PLANAR\n" + pl(-0.1) + "*RIGIDWALL_PLANAR\n" + pl(-0.2)
                                                              + "*RIGIDWALL_PLANAR_ID\n" + f"{1:10d}w1\n" + pl(-0.3))})
    got = walls_of(read(d, "model_trans.k"))
    check("R7 번호 없는 벽 둘(ZT -0.1·-0.2) + _ID 1(-0.3): 출력도 덱 차례 -0.1·-0.2·-0.3, 번호 없는 벽은 번호 없이·_ID 1 은 1",
          rc == 0 and [g[1][2] for g in got] == [-0.1, -0.2, -0.3] and [g[0] for g in got] == [None, None, 1], f"rc={rc} {got}")

    # ── IMPORT_MERGE_K: 숫자 별칭 *MAT_084_REINF(첫 칸 EID1)·*MAT_T01(TMID)은 재질 MID 가 아니다, 침식 끝 빈 카드 ─────────────────
    one = lambda pid, mid, name: ("*KEYWORD\n" + node_block(cubes(1)) + "*ELEMENT_SOLID\n" + hex_row(1, pid, 1) + part(pid, 1, mid, name)
                                  + SOLID1)
    for kw, card in (("*MAT_084_REINF", f10(5, 5, 1, 0.01, 0.01, 0.01)), ("*MAT_T01", f10(5, "7.8E-09", 0.0, 0.0, 0.0) + f10(450.0, 50.0))):
        d, rc, log = run("im_alias", {"base.k": one(1, 1, "a") + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3) + kw + "\n" + card + "*END\n",
                                      "imp.k": one(1, 5, "b") + "*MAT_ELASTIC\n" + f10(5, "2.70E-09", 70000, 0.33) + "*END\n"}, IMO)
        mids = sorted(int((rows[1] if h.split()[0].upper().endswith("_TITLE") else rows[0])[:10])
                      for h, rows in kw_blocks(read(d, "base_imported.k"), "*MAT_ELASTIC") + kw_blocks(read(d, "base_imported.k"), "*MAT_ELASTIC_TITLE"))
        check(f"R7 IMPORT_MERGE_K 기준 덱 {kw} 5 · 가져온 *MAT_ELASTIC 5: 충돌이 아니다(rc 0, 재질 1·5)",
              rc == 0 and "번호 충돌" not in log and mids == [1, 5], f"rc={rc} {mids} " + log[-300:])
    ero = ("*MAT_ADD_EROSION\n" + f10(1, 0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0) + f10(0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0)
           + f10(1, 0, 0, 0.0, 1.0, 0.0, 1.0, 0) + f10(0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0) + f10(0.0, 0.5, "1.0E+20", 0.0))
    steel = "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
    d, rc, log = run("im_ero_blank6", {"base.k": one(1, 1, "a") + steel + ero + "\n*END\n", "imp.k": one(1, 1, "b") + steel + ero + "*END\n"}, IMO)
    check("R7 IMPORT_MERGE_K 같은 침식(IDAM 1, 카드 5 뒤 빈 줄 / 없음): 충돌이 아니다(rc 0)", rc == 0 and "번호 충돌" not in log,
          f"rc={rc} " + log[-300:])

    # ── DTI D2R 닫힘은 PAIRED ±1 짝만 따라간다 — PAIRED 0 으로 사용자 세트를 RELSW 로 가리킨 바닥판 세트만 지운다 ──────────────────
    def d2r(sw, code, entno, rel, paired):
        c2 = f10(0, 0, 0, 0.0, 1, 0, 0.0) + f10(1, 0) if paired >= 0 else f10(0, 0, 0, 0.0, 0, 1, 0.0) + f10(1)
        return "*DEFORMABLE_TO_RIGID_AUTOMATIC\n" + f10(sw, code, 0.0, "1e20", 0.0, entno, rel, paired) + c2
    con = lambda cid, name, ms: f"*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID\n{cid:10d}{name}\n" + f10(1, ms, 3, 3) + f10(0.1, 0.1) + f10(1.0, 1.0)
    deck = ("*KEYWORD\n*CONTROL_TERMINATION\n" + f10(0.001) + node_block(cubes(3)) + "*ELEMENT_SOLID\n"
            + "".join(hex_row(k + 1, k + 1, 8 * k + 1) for k in range(3)) + "".join(part(k + 1) for k in range(3)) + SOLID1 + ELASTIC
            + con(1, "user", 2) + con(2, "floor", 3) + d2r(40, 2, 2, 10, 0) + d2r(20, 2, 1, 10, 1) + d2r(10, 4, 1, 20, -1) + "*END\n")
    dyn3 = ("*KEYWORD\n" + node_block({k: (x, y, z + 0.01) for k, (x, y, z) in cubes(3).items()}) + "*ELEMENT_SOLID\n"
            + "".join(hex_row(k + 1, k + 1, 8 * k + 1) for k in range(3)) + "*END\n")
    d, rc, log = run("dti_d2r_paired0", {"model.k": deck, "dynain": dyn3},
                     "*Inputfile\nmodel.k\n*Mode\nDYNAIN_TO_INITIAL,1\n**DynainToInitial,1\n*DynainPath,dynain\n*IncludeStress,True\n"
                     "*RemovePartbyID,3\n*RemoveContactbyID,2\n**EndDynainToInitial\n*End\n")
    sws = sorted(try_(lambda: int(rows[0][:10]), -1) for _, rows in kw_blocks(read(d, "model_dti.k"), "*DEFORMABLE_TO_RIGID_AUTOMATIC") if rows)
    check("R7 DTI 바닥판 접촉 2 의 세트 40(PAIRED 0, RELSW 10) 만 지우고 남은 사용자 접촉 1 의 짝 20·10 은 남긴다",
          rc == 0 and sws == [10, 20], f"rc={rc} {sws}")

    # ── DROP 의 SWSET 겹침 검사는 long('+') 덱 D2R 을 20칸으로 읽는다 ──────────────────────────────────────────────
    l20 = lambda *v: "".join(f"{x:>20}" for x in v) + "\n"
    long_pair = ("*DEFORMABLE_TO_RIGID_AUTOMATIC +\n" + l20(20, 2, 0.0, "1e20", 0.0, 1, 10, 1) + l20(0, 0, 0, 0.0, 1, 0, 0.0) + l20(2, 0)
                 + "*DEFORMABLE_TO_RIGID_AUTOMATIC +\n" + l20(10, 4, 0.0, "1e20", 0.0, 1, 20, -1) + l20(0, 0, 0, 0.0, 0, 1, 0.0) + l20(2))
    d, rc, log = run("drop_long_d2r", {"model.k": M.base_deck(raw=True, extra=long_pair)}, drop([0], "DeformableToRigid,True\n"))
    outs = dropsets(d)
    kmm_sw = sorted(try_(lambda: int(rows[0][:10]), -1) for h, rows in kw_blocks(outs[0], "*DEFORMABLE_TO_RIGID_AUTOMATIC")
                    if rows and "+" not in h.split()[1:]) if outs else []   # 덱 짝은 '+' 블록으로 그대로 나간다
    check("R7 DROP DeformableToRigid + long('+') 덱 D2R SWSET 20·10: KMM 짝 스위치는 다른 번호(20·10 과 겹치지 않음)",
          rc == 0 and len(kmm_sw) == 2 and not set(kmm_sw) & {10, 20}, f"rc={rc} {kmm_sw}")

    # ── Fast DROP(여러 각도) + DropSurface RigidWall: 각도마다 DropSet.k 에 그 각도의 바닥 벽이 하나 ───────────────────────────
    d, rc, log = run("drop_rigidwall2", {"model.k": cube_deck()}, drop([0, 30], "DropSurface,RigidWall\n"))
    ws = [walls_of(t) for t in dropsets(d)]
    check("R7 Fast DROP 2각도 + RigidWall: DropSet.k 마다 강체벽이 하나씩이고 두 벽의 법선이 다르다",
          rc == 0 and len(ws) == 2 and all(len(w) == 1 for w in ws) and ws[0][0][2] != ws[1][0][2], f"rc={rc} {ws}")


def rigidwalls(t):
    """출력 강체벽 [(키워드, 번호 또는 None, (XT, YT, ZT, XH, YH, ZH))] — 덱 차례대로. _ID 꼴만 ID 카드가 있다."""
    out, lines = [], t.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("*RIGIDWALL"):
            kw = ln.split()[0].upper()
            rows = []
            for r in lines[i + 1:]:
                if r.startswith("*"):
                    break
                if r.strip() and not r.startswith("$"):
                    rows.append(r)
            off = 1 if kw.endswith("_ID") else 0
            rid = try_(lambda: int(rows[0][:10]), -1) if off else None
            c = try_(lambda: floats(rows[off + 1], 10)[:6], None)
            out.append((kw, rid, tuple(c) if c and len(c) == 6 else None))
    return out


def cons_of(t):
    """출력 접촉 CID 목록(_ID 꼴 첫 카드)."""
    out = []
    for kw in sorted({ln.split()[0].upper() for ln in t.splitlines() if ln.startswith("*CONTACT_")}):
        out += [try_(lambda: int(rows[0][:10]), -1) for _, rows in kw_blocks(t, kw)]
    return out


def r8():
    print("[R8] RobustContact 의 각도 번호(RunID), 원문 접촉 번호 예약, DWI 다음 단계의 원문 접촉 D2R")
    # ── RobustContact(파트끼리 TIED) + 여러 각도 + RunID: 각도마다 제 Run 폴더 ─────────────────────────────────────────
    tied = "*CONTACT_TIED_SURFACE_TO_SURFACE_ID\n" + f"{5:10d}bond\n" + f10(1, 2, 3, 3) + f10(0.0, 0.0) + f10(1.0, 1.0)
    deck = ("*KEYWORD\n" + node_block(cubes(2, dx=1.0)) + "*ELEMENT_SOLID\n" + hex_row(1, 1, 1) + hex_row(2, 2, 9) + part(1) + part(2)
            + SOLID1 + ELASTIC + tied + "*END\n")
    d, rc, log = run("drop_robust_runid", {"model.k": deck}, drop([0, 10, 20], "RobustContact,True\nRunID,101,102,103\n"))
    runs = sorted(p.name for p in Path(d).glob("runs/Run_*") if (p / "DropSet.k").exists())
    check("R8 DROP 3각도 + RobustContact(파트끼리 TIED) + RunID 101~103: 각도마다 제 Run 폴더(Run_101·102·103)",
          rc == 0 and runs == ["Run_101", "Run_102", "Run_103"], f"rc={rc} {runs}")

    # ── 원문(해석하지 않는) 접촉의 CID 를 예약한다 — KMM 바닥판 접촉이 그 번호를 받지 않는다 ───────────────────────────────
    s2s = "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID\n" + f"{1:10d}user\n" + f10(1, 1, 3, 3) + f10(0.1, 0.1) + f10(1.0, 1.0)
    n2s = lambda cid: ("*CONTACT_AUTOMATIC_NODES_TO_SURFACE_ID\n" + f"{cid:10d}usernts\n" + f10(1, 1, 3, 3) + f10(0.1, 0.1)
                       + f10(1.0, 1.0))
    d, rc, log = run("drop_raw_cid", {"model.k": cube_deck(s2s + n2s(2))}, drop([0]))
    outs = dropsets(d)
    cids = cons_of(outs[0]) if outs else []
    check("R8 DROP + 해석한 접촉 1·원문 N2S 접촉 2: 바닥판 접촉이 2 를 받지 않는다(접촉 번호가 모두 다르다)",
          rc == 0 and len(cids) >= 3 and len(cids) == len(set(cids)) and {1, 2} <= set(cids), f"rc={rc} {cids}")

    # ── DWI 다음 단계 DTI: 원문 N2S 접촉 8 과 그 접촉을 가리키는 사용자 D2R 짝은 남는다 ───────────────────────────────────
    grid = {i * 4 + j + 1: (float(j), float(i), 0.0) for i in range(4) for j in range(4)}
    quads = "".join(f"{3 * i + j + 1:8d}{1:8d}" + "".join(f"{n:8d}" for n in (4 * i + j + 1, 4 * i + j + 2, 4 * i + j + 6, 4 * i + j + 5)) + "\n"
                    for i in range(3) for j in range(3))
    pair = ("*DEFORMABLE_TO_RIGID_AUTOMATIC\n" + f10(20, 2, 0.0, "1e20", 0.0, 8, 10, 1) + f10(0, 0, 0, 0.0, 1, 0, 0.0) + f10(1, 0)
            + "*DEFORMABLE_TO_RIGID_AUTOMATIC\n" + f10(10, 4, 0.0, "1e20", 0.0, 8, 20, -1) + f10(0, 0, 0, 0.0, 0, 1, 0.0) + f10(1))
    plate = ("*KEYWORD\n*CONTROL_TERMINATION\n" + f10(0.001) + node_block(grid) + "*ELEMENT_SHELL\n" + quads + part(1, 1, 1, "plate")
             + "*SECTION_SHELL\n" + f10(1, 2) + f10(0.5, 0.5, 0.5, 0.5) + "*MAT_ELASTIC\n" + f10(1, "2.70E-09", 70000, 0.33)
             + "*CONTACT_TIED_SURFACE_TO_SURFACE_ID\n" + f"{7:10d}usertied\n" + f10(1, 1, 3, 3) + f10(0.0, 0.0) + f10(1.0, 1.0)
             + n2s(8) + pair + "*END\n")
    dwi = ("*Inputfile\nmodel.k\n*RunDirectoryMode,True,runs\n*Mode\nDROP_WEIGHT_IMPACT_TEST,1\n**DropWeightImpactTest,1\nTFinal,0.0001\n"
           "DT,1e-05\nLocationX,1.5\nLocationY,1.5\nHeight,100\nInitialVelocityX,0\nInitialVelocityY,0\nInitialVelocityZ,0\nGravity,9810\n"
           "ImpactorType,Sphere\nImpactorDimension,0.5\nMeshSize,0.25\nDensityImpactor,7.85e-09\nYoungsModulusImpactor,200000.0\n"
           "PoissonRatioImpactor,0.3\nGenerationMode,OutsideRigidElement\nOffsetDistance,0.05\n"
           "YoungsModulusWall,10000.0\nPoissonRatioWall,0.3\nDensityWall,1e-09\n**EndDropWeightImpactTest\n*End\n")
    d, rc, log = run("dwi_raw_n2s", {"model.k": plate}, dwi)
    runs = sorted(Path(d).glob("runs/Run_*"))
    deck = read(runs[0], "DropWeightImpactTestSet.k") if runs else ""
    dti_opt = read(runs[0] / "DynamicRelaxation", "dynaintoinitial.txt") if runs else ""
    dyn = "*KEYWORD\n" + node_block({k: (x, y, z + 0.01) for k, (x, y, z) in grid.items()}) + "*END\n"
    d2, rc2, log2 = run("dwi_raw_n2s_dti", {"DropWeightImpactTestSet.k": deck, "dynain": dyn},
                        "\n".join("**DynainPath,dynain" if ln.startswith("**DynainPath") else ln for ln in dti_opt.splitlines()) + "\n")
    t = read(d2, "DropWeightImpactTestSet_dti.k")
    sws = sorted(try_(lambda: int(rows[0][:10]), -1) for _, rows in kw_blocks(t, "*DEFORMABLE_TO_RIGID_AUTOMATIC") if rows)
    dwi_cids = cons_of(deck)
    check("R8 DWI + 원문 N2S 8·그 D2R 짝: DWI 접촉이 8 을 받지 않고, 다음 단계 DTI 뒤 접촉 7·8 과 D2R 짝 20·10 이 남는다",
          rc == 0 and rc2 == 0 and len(dwi_cids) == len(set(dwi_cids)) and sorted(cons_of(t)) == [7, 8] and sws == [10, 20],
          f"rc={rc}/{rc2} dwi={dwi_cids} left={cons_of(t)} d2r={sws}")


def main():
    r1()
    r2()
    r3()
    r4()
    r5()
    r6()
    r7()
    r8()
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
