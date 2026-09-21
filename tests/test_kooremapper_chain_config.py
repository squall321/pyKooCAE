# REMAP 체인의 KooRemapper config.yaml 방출 회귀 시험 — 여러 줄 카드 리터럴 블록·한글·TAB 거부·기존 출력 불변
"""
실행: venv312/bin/python tests/test_kooremapper_chain_config.py

  [1] 공용    체인(_dump_kooremapper_config)과 모듈(KooRemapperModule)이 같은 방출 함수를 쓴다
  [2] 블록    여러 줄 material_card / material_cards 가 '|' 리터럴 블록으로 나간다 (따옴표 스칼라면 KooRemapper 가 카드를 못 읽는다)
  [3] 한글    비ASCII 제목이 있는 카드도 리터럴 블록 (allow_unicode)
  [4] TAB     고정폭 카드의 TAB 은 칸을 보존할 수 없으므로 거부한다 (조용히 틀린 덱 방지)
  [5] 회귀    여러 줄 카드가 없는 설정은 수정 전 출력과 바이트 동일
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print("  %-66s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


CARD = "*MAT_ELASTIC\n$#     mid        ro         e        pr\n    MID001  7.85E-09  2.10E+05       0.3"
CARD_KR = "*MAT_ELASTIC_TITLE\n기판 재질\n$#     mid        ro         e        pr\n    MID001  7.85E-09  2.10E+05       0.3"
CARD_TAB = "*MAT_ELASTIC\n$#\tmid\tro\n\tMID001\t7.85E-09"


def restack_cfg(card):
    return {"base_model": "box.k", "output": "rs", "operations": [
        {"type": "restack", "target_pid": 1, "direction": "z", "element_type": "solid",
         "layers": [{"thickness": 1.0, "material_card": card}]}]}


def offset_cfg(card):
    return {"base_model": "box.k", "output": "off", "operations": [
        {"type": "offset", "source_pid": 1, "element_type": "solid", "thickness": 1.0,
         "num_layers": 1, "offset_direction": "+z", "connection_mode": "tied",
         "new_pid": 10, "material_cards": [card]}]}


NOCARD = {"model": "box.k", "output": "md", "mat_type": "MAT_ELASTIC",
          "materials": [{"mid": 1, "match": "SUS304"}, {"mid": 2, "match": "*"}]}


def dump_chain(cfg, path):
    from Runner.CumulativeScenarioRunner import CumulativeScenarioRunner as R
    R._dump_kooremapper_config(None, cfg, path)
    return Path(path).read_text(encoding="utf-8")


def legacy_dump(cfg):
    """수정 전 체인 dumper (str 대표자 없음) — 회귀 비교용"""
    class _Old(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, False)
    return yaml.dump(cfg, Dumper=_Old, sort_keys=False, default_flow_style=False, allow_unicode=True)


def main():
    d = tempfile.mkdtemp(prefix="krcfg_")
    from Runner.KooRemapperStep import dump_kooremapper_yaml, _IndentDumper

    print("[1] 체인과 모듈이 같은 방출 함수")
    import Runner.CumulativeScenarioRunner as CSR
    src = Path(CSR.__file__).read_text(encoding="utf-8")
    check("체인이 KooRemapperStep.dump_kooremapper_yaml 을 쓴다",
          "from Runner.KooRemapperStep import dump_kooremapper_yaml" in src)
    check("체인에 자체 Dumper 클래스가 남아 있지 않다", "_KRIndentDumper" not in src)
    check("모듈 방출 함수가 존재한다", callable(dump_kooremapper_yaml) and _IndentDumper is not None)

    print("[2] 여러 줄 카드 → 리터럴 블록")
    for label, cfg, key in (("restack material_card", restack_cfg(CARD), "material_card: |"),
                            ("offset material_cards", offset_cfg(CARD), "- |")):
        text = dump_chain(cfg, os.path.join(d, "c.yaml"))
        check(f"{label} 이 '{key}' 로 나간다", key in text, text[:300])
        check("  따옴표 스칼라가 아니다", '"*MAT_ELASTIC' not in text and "'*MAT_ELASTIC" not in text)
        back = yaml.safe_load(text)
        op0 = back["operations"][0]
        got = (op0["layers"][0]["material_card"] if "layers" in op0
               else op0["material_cards"][0])
        check("  왕복 시 카드 줄 수 유지 (3줄)", len([l for l in got.strip().split("\n")]) == 3, repr(got))

    print("[3] 한글 제목 카드")
    text = dump_chain(restack_cfg(CARD_KR), os.path.join(d, "kr.yaml"))
    check("리터럴 블록으로 나간다", "material_card: |" in text, text[:300])
    check("한글이 이스케이프되지 않는다", "기판 재질" in text)

    print("[4] TAB 든 카드는 거부")
    for label, cfg in (("체인", restack_cfg(CARD_TAB)), ("모듈", offset_cfg(CARD_TAB))):
        err = None
        try:
            dump_chain(cfg, os.path.join(d, "tab.yaml"))
        except ValueError as e:
            err = str(e)
        except Exception as e:  # 다른 예외면 실패로 본다
            err = "WRONG:" + repr(e)
        check(f"{label} 경로에서 ValueError + TAB 안내", bool(err) and err.startswith("KooRemapper config") and "TAB" in err, str(err))

    print("[5] 여러 줄 카드가 없는 설정은 수정 전과 바이트 동일")
    text = dump_chain(NOCARD, os.path.join(d, "n.yaml"))
    check("matdb 설정 출력 불변", text == legacy_dump(NOCARD), repr(text) + " vs " + repr(legacy_dump(NOCARD)))
    plain = {"base_model": "b.k", "output": "o", "operations": [{"type": "bend", "target_pid": 1, "angle_deg": 30}]}
    check("단일행 값만 있는 설정 출력 불변", dump_chain(plain, os.path.join(d, "p.yaml")) == legacy_dump(plain))

    print()
    if FAILS:
        print("FAIL %d 건" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
