# 미해석 raw 키워드 블록을 매니저 출력과 대조해 중복만 걸러 주는 공용 필터
"""배경

`_raw_keyword_dict` 는 파서가 해석하지 못한 키워드를 원문 그대로 보존해 유실을 막는다.
그 필터는 `keywordInterpreted[kw] == True` 인 키워드만 건너뛴다. 그런데 일반 경로(MAT_*, LOAD_*,
DATABASE_* 계열)로 매니저에 실려 **출력은 되는데 표시가 안 되는** 키워드가 있어서,
같은 카드가 매니저 출력 + raw 블록으로 **두 번** 나갔다.

실측(왕복 1회): `*DATABASE_NCFORC` 1→2, `*LOAD_THERMAL_VARIABLE` 1→2, `*MAT_ADD_THERMAL_EXPANSION` 2→4.
누적 해석은 스텝마다 왕복하므로 스텝을 거듭할수록 카드가 배로 늘어난다.

그래서 키워드 이름이 아니라 **내용**으로 판단한다. 매니저가 이미 같은 내용을 썼으면 raw 를 건너뛰고,
내용이 다르면 그대로 보존한다(유실 방지는 유지).
"""


def _normalize(lines):
    """카드 본문 비교용 정규화 — 주석·빈 줄 제거, 줄 끝 공백 제거"""
    out = []
    for line in lines:
        s = line.rstrip("\n").rstrip()
        if not s or s.startswith("$"):
            continue
        out.append(s)
    return tuple(out)


def index_written_blocks(text, keywords):
    """이미 쓰인 텍스트에서 `keywords` 에 해당하는 카드 블록을 뽑아 {키워드: {정규화본문}} 으로 돌려준다.

    한 번만 훑는다. 대상 키워드만 담으므로 큰 덱(*NODE 등)에서도 메모리를 쓰지 않는다."""
    want = set(keywords)
    found = {k: set() for k in want}
    cur_kw, cur_body = None, []
    for line in text.splitlines():
        if line.startswith("*"):
            if cur_kw is not None:
                found[cur_kw].add(_normalize(cur_body))
            name = line[1:].strip().split()[0].upper() if len(line) > 1 else ""
            cur_kw = name if name in want else None
            cur_body = []
        elif cur_kw is not None:
            cur_body.append(line)
    if cur_kw is not None:
        found[cur_kw].add(_normalize(cur_body))
    return found


def filter_duplicate_raw_blocks(raw_dict, interpreted, written_text, skip_keywords):
    """raw_dict 에서 실제로 써야 하는 (키워드, 블록) 목록만 돌려준다.

    건너뛰는 것: SKIP 목록, 해석 완료 표시된 키워드, **매니저가 같은 내용으로 이미 쓴 블록**.
    돌려주는 순서는 raw_dict 순서 그대로 (기존 출력 순서 유지)."""
    candidates = [(k, v) for k, v in raw_dict.items()
                  if k not in skip_keywords and not interpreted.get(k, False)]
    if not candidates:
        return []
    already = index_written_blocks(written_text, [k for k, _ in candidates])
    result = []
    for kw_name, blocks in candidates:
        seen = already.get(kw_name, set())
        for block in blocks:
            key = _normalize(block)
            if key in seen:
                continue          # 매니저가 같은 카드를 이미 썼다 → 중복
            seen.add(key)         # raw 끼리의 중복도 한 번만
            result.append((kw_name, block))
    return result
