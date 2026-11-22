#!/usr/bin/env python3
# 남은 결함 묶음 U3 판정 — *LOAD_SEGMENT(_ID) 가져오기·기록, 덱 ID 하중이 KMM 이 매긴 번호와 겹칠 때, 없는 절점을 작은 덱으로 본다
"""남은 결함 묶음(docs/kmm_kcr_remaining_20261121) A7.

  [4] *LOAD_SEGMENT(_ID): 개체 둘(4절점·N5~N8 8절점)·ID·제목·SF 자릿수, 덱 ID 하중이 KMM 이 매긴 번호와 겹칠 때 둘 다 남음,
      없는 절점은 🔴 + 종료 코드 3. 예전엔 빈 N 칸에서 int('') 로, 쓸 때 절점 객체·글자 SF 포맷으로 죽었고(rc 1) 카드 2 를 새
      세그먼트로 읽었다. *LOAD_NODE_POINT 가 번호 1 을 받은 뒤의 *LOAD_SEGMENT_SET_ID 1 은 그 하중을 덮어 rc 0 으로 지웠다

실행: venv312/bin/python tests/test_remaining_load_segment.py (KMM 3회, 1분 안)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v131_review as R   # noqa: E402 — 실행·읽기·덱 조각을 같이 쓴다
from test_remaining_multi_entity import deck_m   # noqa: E402 — 정육면체 다섯 덱

FAILS = []
f10 = R.f10


def check(name, cond, detail=""):
    print("  %-104s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def seg_rows(text):
    """출력의 *LOAD_SEGMENT_ID 블록 → [(ID, 제목, [LCID, SF, AT, N1~N5], [N6~N8])]."""
    out = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.split()[:1] == ["*LOAD_SEGMENT_ID"]:
            data = []
            for x in lines[i + 1:]:
                if x.startswith("*"):
                    break
                if not x.startswith("$"):
                    data.append(x)
            c1 = R.try_(lambda: R.floats(data[1], 10), [])
            c2 = R.try_(lambda: [int(v) for v in R.floats(data[2], 10)], []) if len(data) > 2 else []
            out.append((R.try_(lambda: int(data[0][:10])), data[0][10:].strip() if data else "", c1, c2))
    return out


def t4():
    print("[4] A7 *LOAD_SEGMENT(_ID)")
    seg = ("*LOAD_SEGMENT\n" + f10(10, 1.0, 0.0, 1, 2, 3, 4) + f10(10, 1.23456, 0.001, 33, 34, 35, 36, 37) + f10(38, 39, 40)
           + "*LOAD_SEGMENT_ID\n" + f"{7:>10}press\n" + f10(10, 2.5, 0.0, 5, 6, 7, 8))
    d, rc, log = R.run("me_seg", {"model.k": deck_m(seg)})
    rows = seg_rows(R.read(d, "model_trans.k"))
    want = [([10, 1.0, 0.0, 1, 2, 3, 4], []), ([10, 1.23456, 0.001, 33, 34, 35, 36, 37], [38, 39, 40]), ([10, 2.5, 0.0, 5, 6, 7, 8], [])]
    got = sorted(((r[2], r[3]) for r in rows), key=lambda x: (x[0][3] if len(x[0]) > 3 else 0))
    ok = rc == 0 and R.no_tb(log) and len(got) == 3 and all(len(g[0]) == len(w[0]) and all(R.near(a, b) for a, b in zip(g[0], w[0]))
                                                           and g[1] == w[1] for g, w in zip(got, sorted(want, key=lambda x: x[0][3])))
    check("[4] 세그먼트 셋(4절점·8절점·ID 7): rc 0, LCID·SF 1.23456·AT·절점·카드 2 그대로", ok, f"rc={rc} {rows} " + log[-300:])
    check("[4] *LOAD_SEGMENT_ID 의 ID 7·제목 press 가 남는다", any(r[0] == 7 and r[1] == "press" for r in rows), str(rows))
    # 덱 ID 하중이 KMM 이 매긴 번호와 겹칠 때 — *LOAD_NODE_POINT 가 번호 1 을 받고 *LOAD_SEGMENT_SET_ID 1 이 덮었다
    clash = "*LOAD_NODE_POINT\n" + f10(1, 3, 10, 1.0) + "*LOAD_SEGMENT_SET_ID\n" + f"{1:>10}top\n" + f10(31, 10, 1.0)
    d, rc, log = R.run("me_clash", {"model.k": deck_m(clash)})
    t = R.read(d, "model_trans.k")
    check("[4] *LOAD_NODE_POINT(번호 1) + *LOAD_SEGMENT_SET_ID 1: 둘 다 출력에 남는다", rc == 0 and "*LOAD_NODE_POINT" in t
          and "*LOAD_SEGMENT_SET_ID" in t, f"rc={rc} " + log[-300:])
    d, rc, log = R.run("me_seg_missing", {"model.k": deck_m("*LOAD_SEGMENT\n" + f10(10, 1.0, 0.0, 1, 2, 3, 999))})
    check("[4] 없는 절점 999 를 가리키는 *LOAD_SEGMENT: 🔴 + 종료 코드 3(Traceback 없음)", rc == 3 and "🔴" in log and R.no_tb(log),
          f"rc={rc} " + log[-300:])


if __name__ == "__main__":
    t4()
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}")
    for x in FAILS:
        print("  FAIL", x[:500])
    sys.exit(1 if FAILS else 0)
