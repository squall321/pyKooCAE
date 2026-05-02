"""K-File Merger: 모든 *INCLUDE를 인라인하여 단일 .k 출력 (DECOMPOSE의 역방향).

핵심 안전 규칙:
- *PARAMETER_LOCAL이 있는 include는 **항상 보존** (스코프 깨짐 방지).
- ForceInlineIGA / ForceInlinePreserved 옵션으로도 override 불가.
"""
import os
import shutil


def merge_k_file(dynaImporter, cur_dir, input_filename, option):
    """단일 .k 파일로 병합 출력.

    Args:
        dynaImporter: KooDynaImporter (이미 importDynaFile 호출 완료 상태)
        cur_dir: 현재 작업 디렉토리
        input_filename: 입력 파일명 (출력 파일명 default 생성용)
        option: dict
            - OutputFile: 출력 파일명 (default: <input_basename>_merged.k)
            - ForceInlineIGA: bool, default False — IGA 자동 보존도 무시 (단 PARAMETER_LOCAL 있으면 무시 안 됨)
            - ForceInlinePreserved: bool, default False — 사용자 지정 보존도 무시 (단 PARAMETER_LOCAL 있으면 무시 안 됨)
    """
    force_inline_iga = option.get("ForceInlineIGA", False)
    force_inline_preserved = option.get("ForceInlinePreserved", False)

    # 출력 파일명: default = <input_basename>_merged.k
    if "OutputFile" in option and option["OutputFile"]:
        output_file = option["OutputFile"]
    else:
        base = os.path.splitext(input_filename)[0] if input_filename else "model"
        output_file = f"{base}_merged.k"

    output_path = os.path.join(cur_dir, output_file)

    dyna_mgr = dynaImporter.dynaManager
    passthrough_data = list(getattr(dyna_mgr, '_include_passthrough_data', []))
    preserve_patterns = list(getattr(dyna_mgr, '_preserve_include_patterns', []))

    # passthrough를 안전하게 분류 (인라인 가능 vs 강제 보존)
    inline_entries = []        # 인라인할 passthrough (안전 검증 통과)
    preserved_entries = []     # 강제 보존 (PARAMETER_LOCAL 등)

    for entry in passthrough_data:
        content = entry.get('content', '')
        file_path = entry.get('file', '')
        base = os.path.basename(file_path)

        # 안전 검사: PARAMETER_LOCAL이 있으면 무조건 보존
        has_param_local = '*PARAMETER_LOCAL' in content
        if has_param_local:
            if force_inline_iga or force_inline_preserved:
                print(f"  [MERGE_K] Warning: '{base}' has *PARAMETER_LOCAL → 강제 보존 (스코프 보호)")
            preserved_entries.append(entry)
            continue

        # IGA 자동 보존된 것 (passthrough에 들어왔지만 사용자 패턴 매칭 X)
        # 와 사용자 지정 보존된 것을 구분하기 어려우므로,
        # 두 플래그 모두 검사: 어느 쪽이라도 force면 인라인 후보
        is_user_preserved = _matches_user_pattern(file_path, preserve_patterns)
        if is_user_preserved:
            if force_inline_preserved:
                inline_entries.append(entry)
            else:
                preserved_entries.append(entry)
        else:
            # IGA 자동 보존
            if force_inline_iga:
                inline_entries.append(entry)
            else:
                preserved_entries.append(entry)

    n_inline = len(inline_entries)
    n_preserve = len(preserved_entries)
    print(f"  [MERGE_K] passthrough 처리: 인라인 {n_inline}개, 보존 {n_preserve}개")

    # 출력
    with open(output_path, 'w') as f:
        f.write("*KEYWORD\n")
        # 매니저 내용 (이미 인라인된 일반 include 포함)
        f.write(dynaImporter.WriteStreamDynaKeyword())

        # 인라인 후보: content 그대로 펼침 (단, *KEYWORD/*END 줄은 제거)
        for entry in inline_entries:
            base = os.path.basename(entry['file'])
            f.write(f"$$ ----- Inlined from {base} -----\n")
            f.write(_strip_keyword_end(entry['content']))
            if not entry['content'].endswith('\n'):
                f.write('\n')

        # 강제 보존: *INCLUDE 카드 + 출력 폴더에 파일 복사
        for entry in preserved_entries:
            base = os.path.basename(entry['file'])
            f.write("*INCLUDE\n")
            f.write(f" {base}\n")
            src = entry['file']
            dst = os.path.join(cur_dir, base)
            if os.path.abspath(src) != os.path.abspath(dst) and os.path.exists(src):
                try:
                    shutil.copy2(src, dst)
                except Exception as e:
                    print(f"  Warning: failed to copy {base}: {e}")

        # 미인터프리트 키워드 raw 보존
        _write_uninterpreted_raw_blocks(f, dynaImporter)

        f.write("*END\n")

    print(f"  [MERGE_K] 출력 완료: {output_path}")


def _matches_user_pattern(include_path, patterns):
    """include_path가 사용자 지정 보존 패턴에 매칭되는지."""
    import fnmatch
    if not patterns:
        return False
    base = os.path.basename(include_path)
    abs_path = os.path.abspath(include_path)
    for pat in patterns:
        if not pat:
            continue
        if os.path.isabs(pat):
            if os.path.abspath(pat) == abs_path:
                return True
        else:
            if fnmatch.fnmatch(base, pat):
                return True
    return False


def _strip_keyword_end(content):
    """content에서 *KEYWORD 및 *END 줄을 제거 (인라인 시 중복 방지)."""
    out_lines = []
    for line in content.splitlines(keepends=True):
        stripped = line.strip().upper()
        # *KEYWORD 자체만 제거 (변형 *KEYWORD_xxx는 다른 키워드)
        if stripped == '*KEYWORD' or stripped.startswith('*KEYWORD '):
            continue
        if stripped == '*END' or stripped.startswith('*END '):
            continue
        out_lines.append(line)
    return ''.join(out_lines)


def _write_uninterpreted_raw_blocks(f, dynaImporter):
    """KooDynaImporter가 파싱 못 한 키워드들을 raw text로 보존 (손실 방지)."""
    try:
        dyna_mgr = dynaImporter.dynaManager
        raw_dict = getattr(dyna_mgr, '_raw_keyword_dict', None)
        if not raw_dict:
            return
        interpreted = getattr(dynaImporter, 'keywordInterpreted', {}) or {}
        SKIP = {"_INCLUDE_PASSTHROUGH", "INCLUDE", "KEYWORD", "END"}
        wrote_header = False
        for kw_name, blocks in raw_dict.items():
            if kw_name in SKIP:
                continue
            if interpreted.get(kw_name, False):
                continue
            if not wrote_header:
                f.write("$\n$--- Uninterpreted keywords (raw, preserved) ---\n$\n")
                wrote_header = True
            for block in blocks:
                f.write(f"*{kw_name}\n")
                for line in block:
                    f.write(line if line.endswith('\n') else line + '\n')
    except Exception as e:
        print(f"  Warning: uninterpreted raw 출력 실패 (skip): {e}")
