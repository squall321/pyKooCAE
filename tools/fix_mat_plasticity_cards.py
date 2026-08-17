# *MAT_PIECEWISE_LINEAR_PLASTICITY 카드에 빠진 EPS1~8 / ES1~8 두 줄을 채운다
"""
LS-DYNA 규격상 *MAT_PIECEWISE_LINEAR_PLASTICITY 는 카드 4장이다.
  1: MID RO E PR SIGY ETAN FAIL TDEL
  2: C P LCSS LCSR VP
  3: EPS1~EPS8
  4: ES1~ES8
카드 3·4 를 빠뜨린 덱은 KMM 이 거부하고, LS-DYNA 도 다음 키워드 줄을 카드3 으로
삼켜 오독한다. 이 스크립트는 **없는 경우에만** 0 으로 채운 두 줄을 추가한다.
전부 0 = 응력-변형 곡선 미사용 → ETAN 기반 이선형 거동 그대로. 물성값 불변.

사용법:
  python3 fix_mat_plasticity_cards.py <파일.k> [--write]
  (--write 없으면 무엇을 고칠지만 보여준다)
"""
import re
import shutil
import sys

KW = re.compile(r'^\*MAT_PIECEWISE_LINEAR_PLASTICITY(_TITLE)?\s*$', re.I)
EPS = "$#    eps1      eps2      eps3      eps4      eps5      eps6      eps7      eps8"
ES = "$#     es1       es2       es3       es4       es5       es6       es7       es8"
ZERO8 = "%10d" * 8 % ((0,) * 8)


def is_data(line):
    s = line.strip()
    return bool(s) and not s.startswith('$') and not s.startswith('*')


def fix(path, write=False):
    src = open(path, encoding='utf-8', errors='replace').read().splitlines()
    out, i, fixed, ok = [], 0, [], 0
    while i < len(src):
        line = src[i]
        m = KW.match(line.strip())
        if not m:
            out.append(line); i += 1; continue

        has_title = bool(m.group(1))
        out.append(line); i += 1
        need = 4 + (1 if has_title else 0)   # 제목 + 카드1~4
        taken, title = 0, ''
        # 제목 줄(주석/빈줄 아닌 첫 줄)
        if has_title:
            while i < len(src) and not is_data(src[i]) and not src[i].strip().startswith('*'):
                out.append(src[i]); i += 1
            if i < len(src) and not src[i].strip().startswith('*'):
                title = src[i].strip(); out.append(src[i]); i += 1; taken += 1
        # 데이터 카드 수집 (다음 키워드 전까지)
        # 🔴 삽입 위치는 "마지막 데이터 줄 바로 뒤" 여야 한다. 블록 끝에 그냥 붙이면
        #    다음 재질의 구분선($---) 뒤로 밀려 구조가 어그러진다(기능은 되지만
        #    사람이 읽을 때 어느 재질 카드인지 헷갈린다).
        last_data = len(out)
        while i < len(src) and not src[i].strip().startswith('*'):
            if is_data(src[i]):
                taken += 1
                last_data = len(out) + 1     # 이 줄 다음 위치
            out.append(src[i]); i += 1

        if taken >= need:
            ok += 1
            continue
        missing = need - taken
        if missing == 2:
            out[last_data:last_data] = [EPS, ZERO8, ES, ZERO8]
        elif missing == 1:
            out[last_data:last_data] = [ES, ZERO8]
        else:
            print(f"  ⚠️  {title or '(무제)'}: {taken}/{need}줄 — 카드1·2 부터 부족하다. 수동 확인 필요")
            continue
        fixed.append((title, taken, need))

    print(f"{path}")
    print(f"  정상 {ok}개 / 보정 {len(fixed)}개")
    for t, got, need in fixed[:20]:
        print(f"    + {t or '(무제)'}  {got}→{need}줄")
    if len(fixed) > 20:
        print(f"    ... 외 {len(fixed) - 20}개")
    if write and fixed:
        shutil.copy2(path, path + '.bak')
        open(path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
        print(f"  ✅ 적용 완료 (원본: {path}.bak)")
    elif not write:
        print("  (--write 를 붙이면 실제 적용)")
    return len(fixed)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__); sys.exit(1)
    for p in args:
        fix(p, write='--write' in sys.argv)
