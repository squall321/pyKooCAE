# *PARAMETER 를 LS-DYNA 처럼 읽는 차례로 해석하는지(R16 PARAMETER·DUPLICATION·MUTABLE·LOCAL·EXPRESSION) 보는 회귀 시험 — 리뷰 J
"""
실행: venv312/bin/python tests/test_parameter_positional.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …
(컴파일본에는 리더만 따로 부를 수 없어 [1] 은 건너뛰고 [2] 만 본다)

배경 (2026-10-24, 리뷰 J)
  22b6e4b(리뷰 I 반영)는 인클루드 정의를 메인 해석에 끼워 넣고 파일을 통째 한 표로 치환했다. 그래서 재정의 앞 카드가 나중
  값을 받았고(DFLAG 4·MUTABLE), 식 사이의 재정의가 앞 식 값을 바꿨고, 인클루드 식이 자기 LOCAL 을 못 봐 0 이 됐다. 이제 덱을
  읽는 차례로 한 번 훑어 줄마다 그 자리에서 보이는 값으로 치환한다.
  R16 근거: 정의는 "visible and available at any later point in the input processing"(Remark 5). LOCAL 은 "disappear when
  the input parser finishes reading the file in which they appear" 이고 같은 이름 전역을 잠시 가린다. 식은 "previously
  defined parameters" 를 쓴다. DFLAG 1=경고·새 정의 무시(기본) 2=경고·채택 3=오류·무시 4=조용히 채택 5=조용히 무시.
  MUTABLE 은 재정의를 DFLAG 와 무관하게 허용한다(문자형에는 무시). LOCAL 이 전역을 가리는 것은 중복이 아니다(DUPLICATION
  Remark 1). Remark 5 예제는 DUPLICATION 카드 없이 file1 의 VAL1 재정의를 받아들이지만, DFLAG 표의 기본(1=무시)과 MUTABLE 의
  존재 이유를 따랐다(docs/fix_remaining_20261023/context-notes.md).
  정의보다 앞 줄에서 쓴 참조는 LS-DYNA 라면 오류지만, 예전 KMM 처럼 그 파일 끝(없으면 덱 끝) 값을 넣고 알린다.
"""
import contextlib
import io
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
ENV = dict(os.environ, PATH=str(ROOT / "venv312" / "bin") + ":" + os.environ.get("PATH", ""))
OPT = "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,0,0,0\n**EndTransform\n*End\n"
BASE = Path(tempfile.mkdtemp(prefix="param_positional_"))
FAILS = []


def check(name, cond, detail=""):
    print("  %-78s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def ct(*refs):
    """*CONTROL_TERMINATION 한 줄 — 10칸마다 &이름(오른쪽 정렬). 리더 사례의 탐침 카드다."""
    return "*CONTROL_TERMINATION\n" + "".join(f"{r:>10}" for r in refs) + "\n"


def P(*pairs, kw="*PARAMETER"):
    """R16 매뉴얼 형식('R VAL1     1.0' — 형 글자와 이름을 띄움)"""
    return kw + "\n" + "".join(f"{t} {n:<8}{v:>10}\n" for t, n, v in pairs)


def same(got, want):
    if len(got) != len(want):
        return False
    for g, w in zip(got, want):
        try:
            if abs(float(g) - float(w)) > 1e-9:
                return False
        except ValueError:
            if str(g) != str(w):
                return False
    return True


# ── [1] 리더 사례: 파일마다 탐침 카드 값 ─────────────────────────────────────────────
# 이름: (파일들, {파일: [카드마다 [칸 값…]]}, 옵션) — 옵션 noiga=IGA 자동 보존 끔(IMPORT_MERGE_K 의 가져올 덱처럼),
# warn=로그에 있어야 할 글, nowarn=없어야 할 글, kw=탐침 키워드
REMARK5_FILE1 = (P(("R", "VAL1", "10.0")) + P(("R", "VAL2", "20.0"), kw="*PARAMETER_LOCAL")
                 + P(("R", "VAL4", "40.0"), kw="*PARAMETER_LOCAL"))
CASES = {
    # R16 Remark 5 예제(띄운 형식). VAL1 재정의는 DFLAG 기본 1 이라 무시(경고), LOCAL VAL2·VAL4 는 file1·file2 에서만
    "A_remark5": ({
        "model.k": "*KEYWORD\n" + P(("R", "VAL1", "1.0")) + P(("R", "VAL2", "2.0")) + P(("R", "VAL3", "3.0"))
                   + ct("&VAL1") + "*INCLUDE\nfile1\n" + ct("&VAL1", "&VAL2", "&VAL3") + "*INCLUDE\nfile3\n*END\n",
        "file1": "*KEYWORD\n" + REMARK5_FILE1 + ct("&VAL1", "&VAL2", "&VAL3", "&VAL4") + "*INCLUDE\nfile2\n*END\n",
        "file2": "*KEYWORD\n" + ct("&VAL1", "&VAL2", "&VAL3", "&VAL4") + "*END\n",
        "file3": "*KEYWORD\n" + ct("&VAL1", "&VAL2", "&VAL3") + "*END\n"},
        {"model.k": [[1.0], [1.0, 2.0, 3.0]], "file1": [[1.0, 20.0, 3.0, 40.0]], "file2": [[1.0, 20.0, 3.0, 40.0]],
         "file3": [[1.0, 2.0, 3.0]]},
        {"noiga": True, "warn": ["val1 재정의(10.0)를 무시했다"]}),
    # 같은 덱, IGA 자동 보존(LOCAL 든 file1 은 *INCLUDE 로 남음) — 메인 값은 같아야
    "A_remark5_default": (None, {"model.k": [[1.0], [1.0, 2.0, 3.0]], "file3": [[1.0, 2.0, 3.0]]}, {"same_files": "A_remark5"}),
    "B_mutable_positional": ({"model.k": "*KEYWORD\n" + P(("R", "t", "1.0"), kw="*PARAMETER_MUTABLE") + ct("&t")
                              + P(("R", "t", "2.0")) + ct("&t") + "*END\n"},
                             {"model.k": [[1.0], [2.0]]}, {"nowarn": ["재정의"]}),
    "C_dflag2_positional": ({"model.k": "*KEYWORD\n*PARAMETER_DUPLICATION\n         2\n" + P(("R", "t", "1.0")) + ct("&t")
                             + P(("R", "t", "2.0")) + ct("&t") + "*END\n"},
                            {"model.k": [[1.0], [2.0]]}, {"warn": ["t 재정의(2.0)를 받아들였다"]}),
    "D_expr_then_mutable_redef": ({"model.k": "*KEYWORD\n" + P(("R", "a", "1.0"), kw="*PARAMETER_MUTABLE")
                                   + "*PARAMETER_EXPRESSION\nR b       a*2.0\n" + P(("R", "a", "5.0")) + ct("&a", "&b") + "*END\n"},
                                  {"model.k": [[5.0, 2.0]]}, {}),
    "E_mutable_sibling": ({"model.k": "*KEYWORD\n" + P(("R", "t", "1.0"), kw="*PARAMETER_MUTABLE") + ct("&t")
                           + "*INCLUDE\na.k\n" + ct("&t") + P(("R", "t", "3.0")) + "*INCLUDE\nb.k\n" + ct("&t") + "*END\n",
                           "a.k": "*KEYWORD\n" + P(("R", "t", "2.0")) + ct("&t") + "*END\n",
                           "b.k": "*KEYWORD\n" + ct("&t") + "*END\n"},
                          {"model.k": [[1.0], [2.0], [3.0]], "a.k": [[2.0]], "b.k": [[3.0]]}, {}),
    "F_default_include_redef": ({"model.k": "*KEYWORD\n" + P(("R", "t", "1.0")) + "*INCLUDE\na.k\n*INCLUDE\nb.k\n" + ct("&t") + "*END\n",
                                 "a.k": "*KEYWORD\n" + P(("R", "t", "2.0")) + ct("&t") + "*END\n",
                                 "b.k": "*KEYWORD\n" + ct("&t") + "*END\n"},
                                {"model.k": [[1.0]], "a.k": [[1.0]], "b.k": [[1.0]]}, {"warn": ["t 재정의(2.0)를 무시했다"]}),
    "G_same_include_twice_mutable": ({"model.k": "*KEYWORD\n" + P(("R", "t", "1.0"), kw="*PARAMETER_MUTABLE")
                                      + "*INCLUDE\np.k\n" + P(("R", "t", "3.0")) + ct("&t") + "*INCLUDE\np.k\n" + ct("&t") + "*END\n",
                                      "p.k": "*KEYWORD\n" + P(("R", "t", "2.0")) + ct("&t") + "*END\n"},
                                     {"model.k": [[3.0], [2.0]], "p.k": [[2.0], [2.0]]}, {}),
    "H_end_ctrlz_comma": ({"model.k": "*KEYWORD\n*INCLUDE\np.k\n" + ct("&x", "&y", "&n", "&w") + "*END\n",
                           "p.k": "*KEYWORD\n*PARAMETER\nR x,1.5,I n,3\n*PARAMETER\nR w       7.0\n*END\n*PARAMETER\nR y       2.0\n\x1a"},
                          {"model.k": [[1.5, "&y", 3, 7.0]]}, {"warn": ["치환되지 않은 &참조 1개(&y)"]}),
    "I_local_sibling_leak": ({"model.k": "*KEYWORD\n" + P(("R", "v", "1.0")) + "*INCLUDE\na.k\n*INCLUDE\nb.k\n" + ct("&v") + "*END\n",
                              "a.k": "*KEYWORD\n" + P(("R", "v", "9.0"), kw="*PARAMETER_LOCAL") + ct("&v") + "*END\n",
                              "b.k": "*KEYWORD\n" + ct("&v") + "*END\n"},
                             {"model.k": [[1.0]], "a.k": [[9.0]], "b.k": [[1.0]]}, {"noiga": True, "nowarn": ["재정의"]}),
    "I2_local_sibling_leak_glued": ({"model.k": "*KEYWORD\n*PARAMETER\nRv        1.0\n*INCLUDE\na.k\n*INCLUDE\nb.k\n" + ct("&v") + "*END\n",
                                     "a.k": "*KEYWORD\n*PARAMETER_LOCAL\nRv        9.0\n" + ct("&v") + "*END\n",
                                     "b.k": "*KEYWORD\n" + ct("&v") + "*END\n"},
                                    {"model.k": [[1.0]], "a.k": [[9.0]], "b.k": [[1.0]]}, {"noiga": True}),
    "J_mutable_char": ({"model.k": "*KEYWORD\n*PARAMETER_MUTABLE\nC nm         abc\n*PARAMETER\nC nm         xyz\n*TITLE\n&nm\n*END\n"},
                       {"model.k": [["abc"]]}, {"kw": "TITLE", "warn": ["nm 재정의(xyz)를 무시했다"]}),
    # 메인 LOCAL 은 인클루드 안에서도 보이고 같은 이름 전역을 가린다(Remark 5 의 file2 가 file1 LOCAL 을 보듯)
    "K_main_local_include_global": ({"model.k": "*KEYWORD\n" + P(("R", "a", "5.0"), kw="*PARAMETER_LOCAL") + "*INCLUDE\np.k\n" + ct("&a", "&b") + "*END\n",
                                     "p.k": "*KEYWORD\n" + P(("R", "a", "1.0")) + "*PARAMETER_EXPRESSION\nR b       a*2.0\n" + ct("&a", "&b") + "*END\n"},
                                    {"model.k": [[5.0, 10.0]], "p.k": [[5.0, 10.0]]}, {"nowarn": ["재정의"]}),
    "K2_main_local_glued": ({"model.k": "*KEYWORD\n*PARAMETER_LOCAL\nRa        5.0\n*INCLUDE\np.k\n" + ct("&a", "&b") + "*END\n",
                             "p.k": "*KEYWORD\n*PARAMETER\nRa        1.0\n*PARAMETER_EXPRESSION\nR b       a*2.0\n" + ct("&a", "&b") + "*END\n"},
                            {"model.k": [[5.0, 10.0]], "p.k": [[5.0, 10.0]]}, {}),
    "L_dflag_in_include_after_defs": ({"model.k": "*KEYWORD\n" + P(("R", "t", "1.0")) + "*INCLUDE\nd.k\n" + P(("R", "t", "2.0")) + ct("&t") + "*END\n",
                                       "d.k": "*KEYWORD\n*PARAMETER_DUPLICATION\n         2\n*END\n"},
                                      {"model.k": [[2.0]]}, {"warn": ["t 재정의(2.0)를 받아들였다"]}),
    "M_dflag4_include_positional": ({"model.k": "*KEYWORD\n*PARAMETER_DUPLICATION\n         4\n" + P(("R", "t", "1.0")) + ct("&t")
                                     + "*INCLUDE\na.k\n" + ct("&t") + "*END\n",
                                     "a.k": "*KEYWORD\n" + P(("R", "t", "2.0")) + ct("&t") + "*END\n"},
                                    {"model.k": [[1.0], [2.0]], "a.k": [[2.0]]}, {"nowarn": ["재정의"]}),
    "N_expr_mutable_chain": ({"model.k": "*KEYWORD\n*PARAMETER_EXPRESSION_MUTABLE\nR b       2.0*3.0\n*PARAMETER_EXPRESSION\nR c       b+1.0\n"
                              "*PARAMETER_EXPRESSION\nR b       10.0\n" + ct("&b", "&c") + "*END\n"},
                             {"model.k": [[10.0, 7.0]]}, {}),
    "N2_expr_chain_dflag2": ({"model.k": "*KEYWORD\n*PARAMETER_DUPLICATION\n         2\n*PARAMETER_EXPRESSION\nR b       2.0*3.0\n"
                              "*PARAMETER_EXPRESSION\nR c       b+1.0\n*PARAMETER_EXPRESSION\nR b       10.0\n" + ct("&b", "&c") + "*END\n"},
                             {"model.k": [[10.0, 7.0]]}, {}),
    "N3_expr_mutable_then_plain": ({"model.k": "*KEYWORD\n*PARAMETER_EXPRESSION_MUTABLE\nR b       2.0*3.0\n*PARAMETER_EXPRESSION\nR c       b+1.0\n"
                                    "*PARAMETER\nR b       10.0\n" + ct("&b", "&c") + "*END\n"},
                                   {"model.k": [[10.0, 7.0]]}, {}),
    "N4_include_expr_chain_mutable": ({"model.k": "*KEYWORD\n*INCLUDE\np.k\n*PARAMETER_EXPRESSION\nR b       10.0\n" + ct("&b", "&c") + "*END\n",
                                       "p.k": "*KEYWORD\n*PARAMETER_EXPRESSION_MUTABLE\nR b       2.0*3.0\n*PARAMETER_EXPRESSION\nR c       b+1.0\n"
                                              + ct("&b", "&c") + "*END\n"},
                                      {"model.k": [[10.0, 7.0]], "p.k": [[6.0, 7.0]]}, {}),
    # 인클루드 식이 메인의 나중 정의를 참조 — 정의되는 자리에서 풀린다(그 뒤 카드)
    "O_forward_ref": ({"model.k": "*KEYWORD\n*INCLUDE\np.k\n" + P(("R", "a", "3.0")) + ct("&b") + "*END\n",
                       "p.k": "*KEYWORD\n*PARAMETER_EXPRESSION\nR b       a*2.0\n*END\n"},
                      {"model.k": [[6.0]]}, {"nowarn": ["미해결", "치환되지 않은"], "warn": ["'b=a*2.0' 를 정의보다 뒤에 나온 값으로 셌다"]}),
    "P_char_include_name": ({"model.k": "*KEYWORD\n*PARAMETER\nC fn          p.k\n*INCLUDE\n&fn          \n" + ct("&q") + "*END\n",
                             "p.k": "*KEYWORD\n" + P(("R", "q", "4.0")) + ct("&q") + "*END\n"},
                            {"model.k": [[4.0]], "p.k": [[4.0]]}, {}),
    "Q_expr_first_plain_redef": ({"model.k": "*KEYWORD\n*PARAMETER_EXPRESSION\nR t       1.0+1.0\n*INCLUDE\np.k\n" + ct("&t") + "*END\n",
                                  "p.k": "*KEYWORD\n" + P(("R", "t", "7.0")) + ct("&t") + "*END\n"},
                                 {"model.k": [[2.0]], "p.k": [[2.0]]}, {"warn": ["t 재정의(7.0)를 무시했다"]}),
    "R_nested_shared_include": ({"model.k": "*KEYWORD\n*INCLUDE\na.k\n*INCLUDE\nb.k\n" + ct("&t", "&u") + "*END\n",
                                 "a.k": "*KEYWORD\n*INCLUDE\nc.k\n" + P(("R", "u", "1.0")) + "*END\n",
                                 "b.k": "*KEYWORD\n" + P(("R", "t", "5.0")) + "*INCLUDE\nc.k\n*END\n",
                                 "c.k": "*KEYWORD\n" + P(("R", "t", "9.0")) + ct("&t") + "*END\n"},
                                {"model.k": [[9.0, 1.0]], "c.k": [[9.0], [9.0]]}, {"warn": ["t 재정의(5.0)를 무시했다"]}),
    "S_main_local_spaced": ({"model.k": "*KEYWORD\n*PARAMETER_LOCAL\nR thk     1.0\n*INCLUDE\np.k\n" + ct("&thk") + "*END\n",
                             "p.k": "*KEYWORD\n*PARAMETER\nR thk     2.0\n*END\n"},
                            {"model.k": [[1.0]]}, {}),
    "S3_local_multi_pair": ({"model.k": "*KEYWORD\n*PARAMETER_LOCAL\nRa        1.0       Rb        2.0\nIn        3\n" + ct("&a", "&b", "&n") + "*END\n"},
                            {"model.k": [[1.0, 2.0, 3]]}, {}),
    "T_local_masks_main_global": ({"model.k": "*KEYWORD\n*PARAMETER\nRv        1.0\n*PARAMETER_LOCAL\nRv        7.0\n" + ct("&v") + "*INCLUDE\nb.k\n*END\n",
                                   "b.k": "*KEYWORD\n" + ct("&v") + "*END\n"},
                                  {"model.k": [[7.0]], "b.k": [[7.0]]}, {"nowarn": ["재정의"]}),
    "U_expr_local_main": ({"model.k": "*KEYWORD\n*PARAMETER_EXPRESSION_LOCAL\nR t       1.0+1.0\n*INCLUDE\np.k\n" + ct("&t") + "*END\n",
                           "p.k": "*KEYWORD\n*PARAMETER\nR t       5.0\n" + ct("&t") + "*END\n"},
                          {"model.k": [[2.0]], "p.k": [[2.0]]}, {"nowarn": ["재정의"]}),
    "U2_expr_local_main_dflag2": ({"model.k": "*KEYWORD\n*PARAMETER_DUPLICATION\n         2\n*PARAMETER_EXPRESSION_LOCAL\nR t       1.0+1.0\n"
                                   "*INCLUDE\np.k\n" + ct("&t") + "*END\n",
                                   "p.k": "*KEYWORD\n*PARAMETER\nR t       5.0\n" + ct("&t") + "*END\n"},
                                  {"model.k": [[2.0]], "p.k": [[2.0]]}, {}),
    "V_dflag3": ({"model.k": "*KEYWORD\n*PARAMETER_DUPLICATION\n         3\n*PARAMETER\nR t       1.0\n*PARAMETER\nR t       2.0\n" + ct("&t") + "*END\n"},
                 {"model.k": [[1.0]]}, {"warn": ["🔴 *PARAMETER t 재정의(2.0)"]}),
    "V5_dflag5_silent": ({"model.k": "*KEYWORD\n*PARAMETER_DUPLICATION\n         5\n*PARAMETER\nR t       1.0\n*PARAMETER\nR t       2.0\n" + ct("&t") + "*END\n"},
                         {"model.k": [[1.0]]}, {"nowarn": ["재정의"]}),
    "W_local_masks_local_same_file": ({"model.k": "*KEYWORD\n*PARAMETER_LOCAL\nRv        1.0\n*PARAMETER_LOCAL\nRv        2.0\n" + ct("&v") + "*END\n"},
                                      {"model.k": [[1.0]]}, {"warn": ["v 재정의(2.0)를 무시했다"]}),
    # 인클루드 식이 자기 파일 LOCAL 을 쓴다(중복 없음) — 22b6e4b 는 0
    "Y_include_expr_own_local": ({"model.k": "*KEYWORD\n*INCLUDE\na.k\n*END\n",
                                  "a.k": "*KEYWORD\n*PARAMETER_LOCAL\nRxmin     1.0\n*PARAMETER_EXPRESSION\nR span    5.0-xmin\n" + ct("&span") + "*END\n"},
                                 {"a.k": [[4.0]]}, {"noiga": True, "nowarn": ["미해결", "치환되지 않은"]}),
    "Y3_noecho_local": ({"model.k": "*KEYWORD\n*INCLUDE\na.k\n*END\n",
                         "a.k": "*KEYWORD\n*PARAMETER_NOECHO_LOCAL\nRxmin     1.0\n*PARAMETER_EXPRESSION\nR span    5.0-xmin\n" + ct("&span") + "*END\n"},
                        {"a.k": [[4.0]]}, {"nowarn": ["미해결", "치환되지 않은"]}),
    "Y4_lowercase_local": ({"model.k": "*KEYWORD\n*INCLUDE\na.k\n*END\n",
                            "a.k": "*KEYWORD\n*parameter_local\nRxmin     1.0\n*parameter_expression\nR span    5.0-xmin\n" + ct("&span") + "*END\n"},
                           {"a.k": [[4.0]]}, {"nowarn": ["미해결", "치환되지 않은"]}),
    # 식 안 참조의 '&'(R16 "with or without the leading &"), 문자형 식은 세지 않고 글 그대로
    "Z_expr_amp_and_char": ({"model.k": "*KEYWORD\n" + P(("R", "a", "1.5")) + "*PARAMETER_EXPRESSION\nR b       &a*2.0\nC s       abc\n"
                             + ct("&b") + "*TITLE\n&s\n*END\n"},
                            {"model.k": [[3.0]]}, {"nowarn": ["구문 오류"]}),
    "Z2_second_duplication_card": ({"model.k": "*KEYWORD\n*PARAMETER_DUPLICATION\n         4\n*PARAMETER_DUPLICATION\n         1\n"
                                    + P(("R", "t", "1.0")) + P(("R", "t", "2.0")) + ct("&t") + "*END\n"},
                                   {"model.k": [[2.0]]}, {"warn": ["*PARAMETER_DUPLICATION 이 또 있다"]}),
    # 정의보다 앞 줄에서 쓴 참조(LS-DYNA 라면 오류) — 예전처럼 채우고 알린다
    "FWD1_same_file": ({"model.k": "*KEYWORD\n" + ct("&x") + P(("R", "x", "2.5")) + "*END\n"},
                       {"model.k": [[2.5]]}, {"warn": ["&x 을(를) 정의보다 앞 줄에서 썼다"]}),
    "FWD2_include_uses_later_main": ({"model.k": "*KEYWORD\n*INCLUDE\na.k\n" + P(("R", "x", "2.5")) + "*END\n",
                                      "a.k": "*KEYWORD\n" + ct("&x") + "*END\n"},
                                     {"a.k": [[2.5]]}, {"warn": ["덱 끝 값을 넣었다"]}),
    "FWD3_local_forward": ({"model.k": "*KEYWORD\n*INCLUDE\na.k\n" + ct("&v") + "*END\n",
                            "a.k": "*KEYWORD\n" + ct("&v") + "*PARAMETER_LOCAL\nRv        3.0\n*END\n"},
                           {"a.k": [[3.0]], "model.k": [["&v"]]}, {"noiga": True, "warn": ["이 파일 끝 값을 넣었다"]}),
    # ── 리뷰 K ──
    # K2: 정수 식 결과가 inf 면 그 식만 미치환 — 예전엔 훑기·대비 경로가 함께 죽어 덱의 &참조가 하나도 치환되지 않았다
    "K2_int_expr_inf": ({"model.k": "*KEYWORD\n" + P(("R", "t", "1.0")) + "*PARAMETER_EXPRESSION\nI n       1e200*1e200\n"
                         + ct("&t") + "*INCLUDE\na.k\n*END\n",
                         "a.k": "*KEYWORD\n*PARAMETER_EXPRESSION\nI m       1e200*1e200-1e200*1e200\n" + ct("&t") + "*END\n"},
                        {"model.k": [[1.0]], "a.k": [[1.0]]}, {"warn": ["평가 실패"], "nowarn": ["훑지 못했다", "해석 실패"]}),
    # K3: 쉼표형 식(R16 EXPRESSION Remark 1 예제 그대로)·'rxminn, &xmin-&rr'(사용자 IGA 덱 형식)
    "K3_comma_expr_r16_example": ({"model.k": "*KEYWORD\n*parameter\nrterm, 0.2, istates, 80\n*parameter_expression\n"
                                   "rplot,term/(states-30)\n" + P(("R", "xmin", "5.0"), ("R", "rr", "1.0"))
                                   + "*PARAMETER_EXPRESSION\nrxminn, &xmin-&rr\n" + ct("&plot", "&xminn") + "*END\n"},
                                  {"model.k": [[0.004, 4.0]]}, {"nowarn": ["구문 오류", "치환되지 않은"]}),
    # K4: R16 Card 1 그대로 쓴 고정폭 여러 쌍 — 값(10칸 오른쪽 맞춤) 뒤에 다음 PRMR 이 붙는다
    "K4_fixed_width_glued": ({"model.k": "*KEYWORD\n*PARAMETER\nR thk            1.0R w              2.0I n                3\n"
                              "*PARAMETER_LOCAL\nRp               4.0Rq               5.0\n" + ct("&thk", "&w", "&n", "&p", "&q") + "*END\n"},
                             {"model.k": [[1.0, 2.0, 3, 4.0, 5.0]]}, {}),
    # P1: 인클루드 이름의 참조가 그 자리에서 정의 전이면(LS-DYNA 도 못 읽음) 읽지 않고 까닭을 알린다
    "KP1_include_name_forward": ({"model.k": "*KEYWORD\n*INCLUDE\n&fn\n*PARAMETER\nC fn          p.k\n" + ct("&q") + "*END\n",
                                  "p.k": "*KEYWORD\n" + P(("R", "q", "4.0")) + ct("&q") + "*END\n"},
                                 {"model.k": [["&q"]]}, {"warn": ["*INCLUDE 파일 이름의 &fn 이(가) 그 자리에서 정의되지 않았다"]}),
    # P2: 인클루드의 LOCAL 식이 부모의 나중 정의를 참조 — 예전처럼 덱 끝 값으로 채우고 알린다(예전 판 h=2.0)
    "KP2_local_expr_pending_parent_later": ({"model.k": "*KEYWORD\n*INCLUDE\na.k\n" + P(("R", "w", "4.0")) + ct("&w") + "*END\n",
                                             "a.k": "*KEYWORD\n*PARAMETER_EXPRESSION_LOCAL\nR h       w/2.0\n" + ct("&h") + "*END\n"},
                                            {"model.k": [[4.0]], "a.k": [[2.0]]},
                                            {"warn": ["'h=w/2.0' 를 정의보다 뒤에 나온 값으로 셌다", "덱 끝 값을 넣었다"]}),
    # P3: 미뤄 둔 전역 식은 정의 자리의 범위로만 센다 — 다른 파일(안쪽 인클루드)의 LOCAL b 를 쓰지 않는다
    "KP3_pending_global_not_nested_local": ({"model.k": "*KEYWORD\n*PARAMETER_EXPRESSION\nR a       b*2.0\n*INCLUDE\ninc.k\n"
                                             + P(("R", "b", "1.0")) + ct("&a", "&b") + "*END\n",
                                             "inc.k": "*KEYWORD\n*PARAMETER_EXPRESSION_LOCAL\nR b       5.0\n" + ct("&a") + "*END\n"},
                                            {"model.k": [[2.0, 1.0]], "inc.k": [[2.0]]}, {"warn": ["정의보다 뒤에 나온 값으로 셌다"]}),
    # P4: 값이 안 나온 식은 이름을 차지하지 않는다 — 뒤의 정상 정의가 첫 정의(DFLAG 1 로 버리지 않음)
    "KP4_pending_does_not_hold_name": ({"model.k": "*KEYWORD\n*PARAMETER_EXPRESSION\nR a       a+1.0\n" + ct("&a")
                                        + P(("R", "a", "5.0")) + ct("&a") + "*END\n"},
                                       {"model.k": [[5.0], [5.0]]}, {"nowarn": ["재정의"]}),
    # P5: /dev/null 같은 특수 파일 인클루드 — 리더와 같이 exists 로 판정(계획 어긋남 경고 없음)
    "KP5_devnull_include": ({"model.k": "*KEYWORD\n" + P(("R", "t", "1.0")) + "*INCLUDE\n/dev/null\n" + ct("&t") + "*END\n"},
                            {"model.k": [[1.0]]}, {"nowarn": ["맞지 않는다"]}),
    # P7: 평문 *PARAMETER 값의 &참조는 그 자리 값(R16 "referenced anywhere")
    "KP7_param_value_ref": ({"model.k": "*KEYWORD\n" + P(("R", "a", "1.5")) + "*PARAMETER\nR b       &a\n" + ct("&b") + "*END\n"},
                            {"model.k": [[1.5]]}, {"nowarn": ["치환되지 않은"]}),
    # F5: 뒤 공백 없는 '&fn' 에 긴 파일 이름 — 파일 이름 줄은 글자 수에 매이지 않게 치환
    "KF5_long_include_name": ({"model.k": "*KEYWORD\n*PARAMETER\nC fn    long_include_name.k\n*INCLUDE\n&fn\n*END\n",
                               "long_include_name.k": "*KEYWORD\n" + P(("R", "q", "4.0")) + ct("&q") + "*END\n"},
                              {"long_include_name.k": [[4.0]]}, {"nowarn": ["not found", "필드 공백"]}),
}


def read_deck(files, noiga=False, kw="CONTROL_TERMINATION"):
    """리더(ReadKeywordsfromFile)만 돌려 파일별 탐침 카드 값과 로그를 돌려준다."""
    d = Path(tempfile.mkdtemp(dir=BASE))
    for name, text in files.items():
        Path(d, name).write_bytes(text.encode())
    sys.path.insert(0, str(GEN))
    from KooCAEManager.KooDynaKeyword import DynaManager
    dm = DynaManager()
    if noiga:
        dm._disable_auto_iga_passthrough = True
    kd, buf = {}, io.StringIO()
    with contextlib.redirect_stdout(buf):
        dm.ReadKeywordsfromFile(str(d / "model.k"), [], kd)
    rows = {}
    for blk, src in zip(kd.get(kw, []), dm._include_sources.get(kw, [])):
        line = blk[0].rstrip("\n")
        rows.setdefault(os.path.basename(src), []).append([line[i:i + 10].strip() for i in range(0, len(line), 10)])
    return rows, buf.getvalue()


def test_reader_cases():
    print("[1] 리더 — 파일마다 그 자리에서 보이는 값")
    if os.environ.get("KMM_BIN"):
        print("  (KMM_BIN — 리더만 따로 부를 수 없어 건너뜀)")
        return
    for name, (files, want, opt) in CASES.items():
        if files is None:
            files = CASES[opt["same_files"]][0]
        rows, log = read_deck(files, opt.get("noiga", False), opt.get("kw", "CONTROL_TERMINATION"))
        ok = set(rows) == set(want) and all(len(rows[f]) == len(want[f]) and all(same(g, w) for g, w in zip(rows[f], want[f]))
                                            for f in want)
        check(f"{name}: 값", ok, f"got={rows} want={want}")
        for w in opt.get("warn", []):
            check(f"{name}: 알림 '{w[:40]}'", w in log, log[-800:])
        for w in opt.get("nowarn", []):
            check(f"{name}: 알림 없음 '{w}'", w not in log, log[-800:])


# ── [2] KMM 출력(컴파일본도): 셸 섹션 두께가 그 자리 값인가 ────────────────────────────
def grid_nodes():
    out = []
    for j in range(4):
        for i in range(4):
            out.append(f"{j * 4 + i + 1:8d}{float(i):16.6f}{float(j):16.6f}{0.0:16.6f}")
    return "*NODE\n" + "\n".join(out) + "\n"


MAT = "*MAT_ELASTIC\n" + "".join(f"{v:>10}" for v in (1, "7.85E-09", 210000, 0.3)) + "\n"
SHELLS = "*ELEMENT_SHELL\n" + "".join(
    f"{20 + k:8d}{2:8d}{a:8d}{a + 1:8d}{a + 5:8d}{a + 4:8d}\n" for k, a in enumerate((1, 2, 3, 5, 6, 7, 9, 10, 11), start=1))


def section(*refs):
    return "*PART\nskin\n" + "".join(f"{v:>10}" for v in (2, 2, 1)) + "\n*SECTION_SHELL\n" + f"{2:>10}{2:>10}\n" \
           + "".join(f"{r:>10}" for r in refs) + "\n"


KMM_CASES = {
    # DFLAG 4: 인클루드 재정의 앞에 있는 섹션은 1.0 — 22b6e4b 는 2.0
    "KM_dflag4_section_before_include": ({
        "model.k": "*KEYWORD\n*PARAMETER_DUPLICATION\n         4\n" + P(("R", "t", "1.0")) + grid_nodes() + MAT
                   + section("&t", "&t", "&t", "&t") + "*INCLUDE\na.k\n" + SHELLS + "*END\n",
        "a.k": "*KEYWORD\n" + P(("R", "t", "2.0")) + "*END\n"}, [1.0, 1.0, 1.0, 1.0]),
    # 인클루드 안 MUTABLE 식 사슬 — c 는 정의 때의 b=6 으로 7(22b6e4b 는 11)
    "KN4_include_expr_chain": ({
        "model.k": "*KEYWORD\n" + grid_nodes() + MAT + "*INCLUDE\np.k\n*PARAMETER_EXPRESSION\nR b       10.0\n" + SHELLS + "*END\n",
        "p.k": "*KEYWORD\n*PARAMETER_EXPRESSION_MUTABLE\nR b       2.0*3.0\n*PARAMETER_EXPRESSION\nR c       b+1.0\n"
               + section("&b", "&c", "&b", "&b") + "*END\n"}, [6.0, 7.0, 6.0, 6.0]),
    # 인클루드 식이 그 파일의 NOECHO_LOCAL 을 쓴다 — 22b6e4b 는 0
    "KY3_include_noecho_local_expr": ({
        "model.k": "*KEYWORD\n" + grid_nodes() + MAT + "*INCLUDE\na.k\n" + SHELLS + "*END\n",
        "a.k": "*KEYWORD\n*PARAMETER_NOECHO_LOCAL\nRxmin     1.0\n*PARAMETER_EXPRESSION\nR span    5.0-xmin\n"
               + section("&span", "&span", "&span", "&span") + "*END\n"}, [4.0, 4.0, 4.0, 4.0]),
    # 메인 EXPRESSION_LOCAL 이 인클루드 전역을 가린다(DFLAG 2 라도 중복 아님) — 22b6e4b 는 5.0
    "KU2_expression_local_masks": ({
        "model.k": "*KEYWORD\n*PARAMETER_DUPLICATION\n         2\n*PARAMETER_EXPRESSION_LOCAL\nR t       1.0+1.0\n*INCLUDE\np.k\n"
                   + grid_nodes() + MAT + section("&t", "&t", "&t", "&t") + SHELLS + "*END\n",
        "p.k": "*KEYWORD\n*PARAMETER\nR t       5.0\n*END\n"}, [2.0, 2.0, 2.0, 2.0]),
}


def section_thickness(text):
    """출력의 섹션 2 카드 2 의 T1~T4"""
    m = re.search(r"^\*SECTION_SHELL(_TITLE)?[ \t]*\n(.*?)(?=^\*)", text, re.S | re.M)
    if not m:
        return None
    lines = [ln for ln in m.group(2).splitlines() if not ln.startswith("$")]
    if m.group(1):
        lines = lines[1:]
    if len(lines) < 2:
        return None
    card2 = lines[1]
    try:
        return [float(card2[i:i + 10]) for i in range(0, 40, 10)]
    except ValueError:
        return card2


def test_kmm_cases():
    print("[2] KMM TRANSFORM 출력 — 섹션 두께")
    for name, (files, want) in KMM_CASES.items():
        d = Path(tempfile.mkdtemp(dir=BASE))
        for fn, text in files.items():
            Path(d, fn).write_bytes(text.encode())
        Path(d, "opt.txt").write_text(OPT)
        r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
        out = Path(d, "model_trans.k")
        got = section_thickness(out.read_text(errors="replace")) if out.exists() else None
        check(f"{name}: rc 0", r.returncode == 0, (r.stdout + r.stderr)[-800:])
        check(f"{name}: T1~T4 = {want}", isinstance(got, list) and same(got, want), f"got={got} ({d})")


def test_fallbacks():
    """읽는 차례 훑기가 죽어도 파일마다 그 파일 정의로 치환하고(예전 방식), 계획이 파일과 어긋나면 덱 끝 값으로 치환한다."""
    print("[3] 대비 경로")
    if os.environ.get("KMM_BIN"):
        print("  (KMM_BIN — 건너뜀)")
        return
    sys.path.insert(0, str(GEN))
    from KooCAEManager.KooDynaKeyword import DynaManager
    files = CASES["F_default_include_redef"][0]
    orig = DynaManager._param_walk

    def boom(self, *a, **k):
        raise RuntimeError("시험용 실패")
    DynaManager._param_walk = boom
    try:
        rows, log = read_deck(files)
    finally:
        DynaManager._param_walk = orig
    check("훑기 실패: 알리고 파일마다 해석", "읽는 차례로 훑지 못했다" in log, log[-600:])
    check("훑기 실패: 값(메인 1.0, 인클루드 재정의는 DFLAG 1 로 무시)",
          rows == {"model.k": [["1.0"]], "a.k": [["1.0"]], "b.k": [["1.0"]]}, str(rows))
    dm = DynaManager()
    from KooCAEManager.KooParameterResolver import ParameterResolver
    dm._param_resolver = ParameterResolver()
    dm._param_resolver.params["t"] = "3.0"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = dm._apply_param_plan("x.k", ["        &t\n"], {0: ("다른 줄\n", "       9.0\n")}, True)
    check("계획 어긋남: 알리고 덱 끝 값", out == ["       3.0\n"] and "맞지 않는다" in buf.getvalue(), f"{out} {buf.getvalue()}")


if __name__ == "__main__":
    print(f"GEN={GEN}  KMM={' '.join(KMM_CMD)}  BASE={BASE}")
    test_reader_cases()
    test_kmm_cases()
    test_fallbacks()
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:600])
        sys.exit(1)
    print("ALL PASS")
