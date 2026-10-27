# KMM 옵션 파일의 *Recipe,<이름>[,<판>] 을 MCP 레시피 등록소의 판으로 펼친다 — 규칙은 MCP recipes·stmc_tools 와 같다
"""
옵션 파일 꼴
    *Inputfile
    model.k
    *Recipe,shift_rigid[,2]      판을 빼면 쓸 수 있는(active) 마지막 판
    dx,7.5                        매개변수 `이름,값` — 다음 `*` 줄까지(빈 줄·$ 줄은 건너뛴다)
    *End

레시피는 MCP recipe_save 가 근거 잡과 대조해 저장한 kmm_chain·kmm_<모드> 인자 틀이다. 매개변수로 채워 *Mode 목록과
모드 블록으로 바꾼 옵션 글을 <옵션>_recipe.txt 로 쓰고, KMM 은 그 파일을 읽는다. *Recipe 가 없으면 원래 파일 그대로다.
펼치는 규칙(매개변수 검사·{{이름}} 채우기·값 표기·블록 이름)은 MCP 와 같다. 그래서 경로가 없는 레시피는 MCP 가 만든
stmc_options.txt 와 바이트가 같다. MCP 는 옵션 안 절대경로 파일을 작업 폴더로 복사해 이름만 남기고, KMM 은 그대로 둔다.
"""
import hashlib
import json
import math
import os
import re

NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,47}$")
SLOT_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
PARAM_TYPES = {"number": (int, float), "integer": (int,), "string": (str,), "boolean": (bool,)}
_KMM_KEY_RE = re.compile(r"^\*?[A-Za-z][A-Za-z0-9_.]*$")
_KMM_STRUCTURE_RE = re.compile(r"^\s*(\*\*|\*(Inputfile|Mode|End)\b)", re.I)
_INT_RE = re.compile(r"^[+-]?\d+$")
_HAS_RECIPE = re.compile(rb"(?im)^[ \t]*\*recipe")


class RecipeError(Exception):
    pass


def root():
    return os.environ.get("STMC_RECIPES_DIR") or "/data/SmartTwinMCP/recipes"


# ── 등록소 읽기(MCP recipes.load 와 같은 판 고르기 + 내용 해시 확인) ─────────────────────

def _sha(doc):
    core = {k: doc[k] for k in ("tool", "params", "args", "summary", "description", "tags")}
    return hashlib.sha256(json.dumps(core, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _read(path):
    import yaml
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    if not isinstance(doc, dict):
        raise RecipeError(f"레시피 파일이 사전이 아니다: {path}")
    return doc


def _versions(d):
    return sorted(int(n[:-5]) for n in os.listdir(d) if n.endswith(".yaml") and n[:-5].isdigit())


def load(name, version=None):
    if not NAME_RE.fullmatch(name):
        raise RecipeError(f"레시피 이름이 아니다: {name!r} (소문자로 시작하는 3~48자 [a-z0-9_])")
    d = os.path.join(root(), name)
    vers = _versions(d) if os.path.isdir(d) else []
    if not vers:
        raise RecipeError(f"레시피 {name} 가 없다({root()}) — MCP recipe_list 로 찾을 것")
    if version is None:
        active = [v for v in vers if _read(os.path.join(d, f"{v}.yaml")).get("status") == "active"]
        if not active:
            raise RecipeError(f"레시피 {name} 의 쓸 수 있는 판이 없다(모두 내려졌다) — 판을 주면 옛 판을 쓴다")
        version = active[-1]
    p = os.path.join(d, f"{version}.yaml")
    if not os.path.isfile(p):
        raise RecipeError(f"레시피 {name} 에 판 {version} 이 없다(있는 판: {vers})")
    doc = _read(p)
    try:
        sha = _sha(doc)
    except KeyError as e:
        raise RecipeError(f"레시피 {name} 판 {version} 파일에 {e} 가 없다")
    if doc.get("sha256") != sha:
        raise RecipeError(f"레시피 {name} 판 {version} 의 내용이 저장 때 해시와 다르다 — 손으로 고친 판은 쓰지 않는다"
                          f"(MCP recipe_save 로 새 판을 만들 것)")
    if doc.get("name") != name or doc.get("version") != version:
        raise RecipeError(f"레시피 파일 {p} 의 이름·판({doc.get('name')}, {doc.get('version')})이 경로와 다르다")
    return doc


# ── 매개변수·펼치기(MCP recipes._typed·resolve_params·expand 와 같다) ─────────────────────

def _typed(name, ps, value):
    t = ps["type"]
    if t == "integer" and isinstance(value, float) and value.is_integer():
        value = int(value)
    if (isinstance(value, bool) and t != "boolean") or not isinstance(value, PARAM_TYPES[t]):
        raise RecipeError(f"매개변수 {name}: {t} 이어야 한다 — {value!r}")
    if t in ("number", "integer"):
        if "minimum" in ps and value < ps["minimum"]:
            raise RecipeError(f"매개변수 {name}: {value} < minimum {ps['minimum']}")
        if "maximum" in ps and value > ps["maximum"]:
            raise RecipeError(f"매개변수 {name}: {value} > maximum {ps['maximum']}")
    if t == "string" and ("\n" in value or "\r" in value or len(value) > 256):
        raise RecipeError(f"매개변수 {name}: 줄바꿈 없는 256자 이하 글이어야 한다")
    if "enum" in ps and value not in ps["enum"]:
        raise RecipeError(f"매개변수 {name}: {value!r} 는 허용 값 {ps['enum']} 이 아니다")
    return value


def _from_text(name, ps, text):
    """옵션 파일의 값 글 → 매개변수 타입(JSON 수처럼 정수 글은 int, 나머지는 float)."""
    t, s = ps.get("type"), text.strip()
    if t not in PARAM_TYPES:
        raise RecipeError(f"매개변수 {name}: 레시피의 type {t!r} 를 모른다")
    if t == "string":
        return s
    if t == "boolean":
        if s.lower() in ("true", "false"):
            return s.lower() == "true"
        raise RecipeError(f"매개변수 {name}: boolean 이어야 한다(true/false) — {text!r}")
    if _INT_RE.fullmatch(s):
        return int(s)
    try:
        v = float(s)
    except ValueError:
        raise RecipeError(f"매개변수 {name}: {t} 이어야 한다 — {text!r}")
    if not math.isfinite(v):
        raise RecipeError(f"매개변수 {name}: 유한한 수여야 한다 — {text!r}")
    return v


def resolve_params(params, texts):
    unknown = sorted(set(texts) - set(params))
    if unknown:
        raise RecipeError(f"모르는 매개변수: {unknown} (이 레시피: {sorted(params) or '없음'})")
    out = {}
    for pname, ps in params.items():
        if pname in texts:
            out[pname] = _typed(pname, ps, _from_text(pname, ps, texts[pname]))
        elif "default" in ps:
            out[pname] = ps["default"]
        else:
            raise RecipeError(f"매개변수 {pname} 의 값이 필요하다({ps.get('description', '')})")
    return out


def _text(v):
    if isinstance(v, bool):
        return "True" if v else "False"
    return repr(v) if isinstance(v, float) else str(v)


def expand(template, values):
    """{{이름}} 자리를 채운다. 값 전체가 자리 하나면 타입 그대로, 아니면 글로 끼운다(키는 바꾸지 않는다)."""
    if isinstance(template, str):
        m = SLOT_RE.fullmatch(template.strip())
        if m:
            return values[m.group(1)]
        return SLOT_RE.sub(lambda mm: _text(values[mm.group(1)]), template)
    if isinstance(template, dict):
        return {k: expand(v, values) for k, v in template.items()}
    if isinstance(template, list):
        return [expand(v, values) for v in template]
    return template


# ── 옵션 글(MCP stmc_tools._kmm_value·_kmm_block_lines·_kmm_option_file 와 같다) ─────────────

def _kmm_value(v):
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, (list, tuple)):
        return ",".join(_kmm_value(x) for x in v)
    if isinstance(v, (int, float)):
        return repr(v) if isinstance(v, float) else str(v)
    s = str(v)
    if "\n" in s or "\r" in s:
        raise RecipeError(f"옵션 값에 줄바꿈이 있다: {s[:40]!r}")
    return s


def _block_lines(block, label):
    extra = sorted(set(block) - {"mode", "options", "lines"})
    if extra:
        raise RecipeError(f"{label}: 모르는 키 {extra} (options·lines 만 쓴다)")
    opts = block.get("options") or {}
    if not isinstance(opts, dict):
        raise RecipeError(f"{label}: options 는 사전이어야 한다")
    out = []
    for k, v in opts.items():
        if not _KMM_KEY_RE.fullmatch(str(k)):
            raise RecipeError(f"{label}: 옵션 키를 쓸 수 없다: {k!r}")
        out.append(f"{k},{_kmm_value(v)}")
    for line in block.get("lines") or []:
        if not isinstance(line, str) or not line.strip() or "\n" in line or "\r" in line:
            raise RecipeError(f"{label}: lines 에 빈 줄·줄바꿈을 넣을 수 없다(블록이 그 자리에서 끝난다): {line!r}")
        if _KMM_STRUCTURE_RE.match(line):
            raise RecipeError(f"{label}: lines 에 블록 구조 줄(**…, *Inputfile, *Mode, *End)을 넣을 수 없다: {line!r}")
        out.append(line)
    return out


def mode_blocks():
    """모드 → 블록 이름. MCP 생성기와 같은 출처(KMM help 카탈로그의 첫 `**블록,<ID>` 줄)."""
    from KooCLIHelp.kmm_catalog import CATALOG
    out = {}
    for md in CATALOG.modes:
        hdr = next((s for s in md.syntax if s.strip().startswith("**")), "")
        m = re.match(r"\*\*([A-Za-z_]+),", hdr.strip())
        if m:
            out[md.name] = m.group(1)
    return out


def recipe_blocks(doc, values):
    """펼친 인자 틀 → [(모드, 블록, 줄들)]. kmm_chain 은 modes 목록, kmm_<모드> 는 options·lines 하나."""
    tool, index = str(doc.get("tool", "")), mode_blocks()
    args = expand(doc.get("args") or {}, values)
    if not isinstance(args, dict):
        raise RecipeError("레시피 args 가 사전이 아니다")
    if tool == "kmm_chain":
        if set(args) != {"modes"}:
            raise RecipeError(f"kmm_chain 레시피 args 는 modes 하나여야 한다: {sorted(args)}")
        modes = args["modes"]
        if not isinstance(modes, list) or not 1 <= len(modes) <= 20:
            raise RecipeError("modes 는 1~20개 목록이어야 한다")
        blocks = []
        for i, step in enumerate(modes, start=1):
            if not isinstance(step, dict):
                raise RecipeError(f"modes[{i}] 가 사전이 아니다")
            mode = str(step.get("mode", "")).upper()
            if mode not in index:
                raise RecipeError(f"modes[{i}]: 모르는 KooMeshModifier 모드 {mode!r}")
            blocks.append((mode, index[mode], _block_lines(step, f"modes[{i}] {mode}")))
        return blocks
    mode = tool[4:].upper() if tool.startswith("kmm_") else ""
    if mode not in index or tool != "kmm_" + mode.lower():
        raise RecipeError(f"레시피 도구 {tool!r} 는 KMM 에서 펼칠 수 없다(kmm_chain·kmm_<모드> 만 — 후처리 레시피는 MCP recipe_run 으로)")
    if "mode" in args:
        raise RecipeError(f"{tool} 레시피 args 에 mode 를 쓰지 않는다")
    return [(mode, index[mode], _block_lines(args, mode))]


def option_text(head, blocks, tail):
    text = list(head) + ["*Mode"]
    text += [f"{mode},{i}" for i, (mode, _b, _l) in enumerate(blocks, start=1)]
    for i, (_mode, block, lines) in enumerate(blocks, start=1):
        text.append(f"**{block},{i}")
        text += lines
        text.append(f"**End{block}")
    text.append("*End")
    return "\n".join(text + list(tail)) + "\n"


# ── 옵션 파일 ───────────────────────────────────────────────────────────────────

def expand_option_file(path):
    """*Recipe 가 있으면 펼친 옵션 글을 <옵션>_recipe.txt 로 쓰고 그 경로를 돌려준다. 없으면 path 그대로(읽기도 바꾸지 않는다)."""
    with open(path, "rb") as f:
        data = f.read()
    if not _HAS_RECIPE.search(data):
        return path
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        raise RecipeError("*Recipe 를 쓴 옵션 파일은 UTF-8 이어야 한다")
    idx = [i for i, ln in enumerate(lines) if ln.strip().lower().startswith("*recipe")]
    if len(idx) != 1:
        raise RecipeError(f"*Recipe 는 옵션 파일에 하나만 쓴다({len(idx)}개)")
    i = idx[0]
    parts = [p.strip() for p in lines[i].strip().split(",")]
    if parts[0].lower() != "*recipe" or len(parts) < 2 or not parts[1] or len(parts) > 3:
        raise RecipeError(f"*Recipe 줄은 `*Recipe,<이름>[,<판>]` 이어야 한다: {lines[i].strip()!r}")
    version = None
    if len(parts) == 3 and parts[2]:
        if not parts[2].isdigit():
            raise RecipeError(f"*Recipe 판은 양의 정수여야 한다: {parts[2]!r}")
        version = int(parts[2])
    texts, j = {}, i + 1
    while j < len(lines) and not lines[j].strip().startswith("*"):
        ln = lines[j].strip()
        j += 1
        if not ln or ln.startswith("$"):
            continue
        if "," not in ln:
            raise RecipeError(f"*Recipe 매개변수 줄은 `이름,값` 이어야 한다: {ln!r}")
        k, v = ln.split(",", 1)
        k = k.strip()
        if k in texts:
            raise RecipeError(f"매개변수 {k} 를 두 번 줬다")
        texts[k] = v
    others = lines[:i] + lines[j:]
    clash = [ln.strip() for ln in others if ln.strip().startswith("**") or "*mode" in ln.lower()]
    if clash:
        raise RecipeError(f"*Recipe 와 *Mode·모드 블록을 함께 쓸 수 없다(레시피가 *Mode 목록을 만든다): {clash[0]!r}")
    rest = lines[j:]
    end = next((k for k, ln in enumerate(rest) if ln.strip().lower() == "*end"), len(rest))
    head, tail = lines[:i] + rest[:end], rest[end + 1:]

    doc = load(parts[1], version)
    if doc.get("status") != "active":
        print(f"  ⚠️ 레시피 {parts[1]} 판 {doc['version']}: 내려진 판이다({doc.get('retired_reason', '이유 없음')}) — 판을 지정해서 그대로 펼친다")
    params = doc.get("params") or {}
    if not isinstance(params, dict):
        raise RecipeError("레시피 params 가 사전이 아니다")
    values = resolve_params(params, texts)
    blocks = recipe_blocks(doc, values)
    out = os.path.join(os.path.dirname(path), os.path.splitext(os.path.basename(path))[0] + "_recipe.txt")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(option_text(head, blocks, tail))
    shown = ", ".join(f"{k}={_text(v)}" for k, v in values.items()) or "없음"
    print(f"레시피 {doc['name']} 판 {doc['version']}(sha256 {doc['sha256'][:12]}, 만든 이 {doc.get('created_by', '?')}) — "
          f"매개변수 {shown} → 모드 {len(blocks)}개({', '.join(b[0] for b in blocks)})로 펼쳐 {os.path.basename(out)} 를 읽는다")
    return out
