# 바닥판 접촉 — 원본 GENERAL 상속 / 유형 선택 / 대상 범위 회귀 시험
"""
실행: venv312/bin/python tests/test_drop_contact_inherit.py

소스 불변식만 검증한다(덱 생성은 KMM 전체 실행이 필요해 수동 매트릭스로 확인했다).
수동 실측 결과는 docs/fix_drop_contact_inherit/PLAN.md 에 기록.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAILS = []


def check(name, cond, detail=""):
    print("  %-68s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


SRC = (ROOT / "occProject" / "Generators" / "KooCAEManager"
       / "KooDynaAdvancedModification.py").read_text(encoding="utf-8")
PARSER = (ROOT / "occProject" / "Generators" / "KooMeshModifier.py").read_text(encoding="utf-8")
RUNNER = (ROOT / "Runner" / "StepConfigBuilder.py").read_text(encoding="utf-8")


def main():
    print("=== 신규 파서 키를 추가하지 않았다 (기존 점표기 재사용)")
    check('기존 "dropcontact." 분기 존재', 'elif "dropcontact." in line.lower():' in PARSER)
    check("DropContactType 별도 키 없음", '"dropcontacttype"' not in PARSER)
    check("InheritGeneralContact 별도 키 없음", '"inheritgeneralcontact"' not in PARSER)
    check("러너가 drop_contact 전 키를 자동 방출",
          'drop_contact_line += f"\\nDropContact.{key},{val}"' in RUNNER)

    print("=== 상속 (InheritGeneral)")
    check("기본 False — 미지정 시 기존 동작", 'drop_contact.get("InheritGeneral", False)' in SRC)
    check("_dcval 우선순위 헬퍼 존재", "def _dcval(key, default):" in SRC)
    check("명시값이 최우선", "if key in drop_contact:" in SRC)
    check("GENERAL 변환 전 스냅샷 사용 (KeyError 방지)",
          "_general_snapshot" in SRC and "_orig_gen = _general_snapshot if _inherit else None" in SRC)
    check("스냅샷이 convertToSS 변환보다 앞에서 생성",
          SRC.index("_general_snapshot = (") <
          SRC.index("if convertToSS and not decomposeGeneral and general_cids:"))
    check("DT 표기 보존 분기", 'if key == "DT":' in SRC)
    for f in ("FS", "FD", "DC", "VC", "VDC", "PENCHK", "BT", "DT",
              "SFS", "SFM", "SST", "MST", "SFST", "SFMT", "FSF", "VSF"):
        check(f"바닥판 {f} 가 _dcval 경유", f'_dcval("{f}"' in SRC)

    print("=== 유형 선택 (Type)")
    check("기본 General — 기존 동작", 'drop_contact.get("Type", "General")' in SRC)
    check("SurfaceToSurface 분기", '"surfacetosurface", "s2s"' in SRC)
    check("S2S 생성 호출", "DropSurface_S2S" in SRC)
    check("S2S 가 dropContactCID 를 설정 (D2R entno)", "dropContactCID = dropS2S.cid" in SRC)
    check("General 경로 보존", "DropSurface_GENERAL" in SRC)

    print("=== 대상 범위 (Scope)")
    check("기본 Outer — 기존 동작", 'drop_contact.get("Scope", "Outer")' in SRC)
    check("All 분기", 'if _scope == "all":' in SRC)
    check("알 수 없는 값은 경고 후 Outer", "는 알 수 없는 값 — Outer 로 처리" in SRC)

    print("=== 내부/바닥판 비중첩 (D2R 트리거 신뢰도)")
    check("내부 GENERAL 은 MSID=0 단면",
          "modelPartSet.psid, 0, 2, 0, 0, 0, 0, 0," in SRC)
    check("바닥판은 master=바닥판 양면 (MSTYP=3)",
          "outerPartSet.psid, part.id, 2, 3, 0, 0, 0, 0," in SRC)

    print()
    if FAILS:
        print("FAILED %d" % len(FAILS))
        for f in FAILS:
            print("  - %s" % f)
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
