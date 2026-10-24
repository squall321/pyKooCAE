"""
KooParameterResolver - *PARAMETER / *PARAMETER_EXPRESSION / *PARAMETER_LOCAL 변수 해석

LS-DYNA 파라미터 키워드에서 변수를 파싱하고,
K파일 내의 &variable 참조를 실제 값으로 치환합니다.

변수 타입:
  I{name} = integer value   (Iid, Imid 등)
  R{name} = real value      (Rxmin, Rofs 등)
  C{name} = character value

*PARAMETER            : 고정폭 10칸 필드, 라인당 최대 4쌍(PRMRi VALi)
*PARAMETER_EXPRESSION : PRMR(10칸) + 표현식(11칸~). 다른 파라미터를 bare name
                        으로 참조 가능 → 그 자리에서 앞서 정의된 값으로 평가
*PARAMETER_LOCAL      : *PARAMETER 와 같은 문법. 그 파일(과 그 안에서 읽는 인클루드)에서만 보임
옵션(LOCAL·MUTABLE·NOECHO·EXPRESSION)은 순서 무관. 리더가 LS-DYNA 처럼 읽는 차례로
정의를 넘기고(BeginFile/DefineLine/EndFile), 줄마다 그 자리에서 보이는 값(Visible)으로 치환한다.

치환(SubstituteLine)은 &name 을 정규식 토큰 단위로 매칭하므로
termin/termin_/termin__/terminA 같은 접두 충돌이 없고, 대소문자 무시,
고정폭 컬럼 보존(토큰+후행공백 예산 내 우측정렬, 초과 시 %g 컴팩트 재포맷,
그래도 안 맞으면 경고 후 미치환)을 보장합니다.
"""
import re
import ast
import math
from collections import ChainMap

# 표현식 평가용 화이트리스트 함수 (LS-DYNA *PARAMETER_EXPRESSION 서브셋). 소문자 키.
_EXPR_FUNCS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "atan2": math.atan2, "sqrt": math.sqrt, "exp": math.exp,
    "log": math.log, "log10": math.log10, "abs": abs,
    "min": min, "max": max, "int": int, "float": float,
    "mod": math.fmod, "sign": lambda x: math.copysign(1.0, x),
}
# 상수 (파라미터가 같은 이름을 정의하면 파라미터가 우선). 소문자 키.
_EXPR_CONSTS = {"pi": math.pi, "e": math.e}

# AST 화이트리스트 — dunder/속성접근/임의호출 불가, 숫자는 전부 float 취급(int bigint 거듭제곱 hang 차단)
_AST_BINOPS = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
               ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
               ast.Mod: lambda a, b: math.fmod(a, b), ast.FloorDiv: lambda a, b: float(a // b),
               ast.Pow: lambda a, b: a ** b}
_AST_UNARY = {ast.UAdd: lambda a: +a, ast.USub: lambda a: -a}

_TYPE_CHARS = ("R", "I", "C", "r", "i", "c")


def _eval_ast_node(node, resolved):
    """제한 AST 평가. resolved={name_lower: float}. 비허용/미지 → ValueError.

    숫자 리터럴은 float 로 취급하므로 9**9**9 같은 정수 bigint 거듭제곱은
    OverflowError(float)로 즉시 종료돼 hang 이 불가능하다. 속성접근·subscript·
    비화이트리스트 호출은 노드 자체가 불허라 __builtins__ 우회 탈출도 원천 차단.
    """
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError(f"비수치 상수: {node.value!r}")
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _AST_BINOPS:
        return _AST_BINOPS[type(node.op)](_eval_ast_node(node.left, resolved),
                                          _eval_ast_node(node.right, resolved))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _AST_UNARY:
        return _AST_UNARY[type(node.op)](_eval_ast_node(node.operand, resolved))
    if isinstance(node, ast.Name):
        key = node.id.lower()
        if key in resolved:            # 사용자 파라미터 우선
            return resolved[key]
        if key in _EXPR_CONSTS:
            return _EXPR_CONSTS[key]
        raise ValueError(f"미정의 참조: {node.id}")
    if isinstance(node, ast.Call):
        if node.keywords or not isinstance(node.func, ast.Name):
            raise ValueError("비허용 호출")
        fname = node.func.id.lower()
        if fname not in _EXPR_FUNCS:
            raise ValueError(f"비허용 함수: {node.func.id}")
        return float(_EXPR_FUNCS[fname](*[_eval_ast_node(a, resolved) for a in node.args]))
    raise ValueError(f"비허용 식 노드: {type(node).__name__}")


def _expr_param_deps(tree):
    """식이 참조하는 '파라미터 후보' 이름(소문자). 함수 호출명(Call.func)은 제외,
    상수(pi/e)는 파라미터가 덮어쓸 수 있으므로 후보에 포함(호출부에서 판정)."""
    func_name_ids = {id(n.func) for n in ast.walk(tree)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    deps = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and id(n) not in func_name_ids:
            deps.add(n.id.lower())
    return deps


_PENDING = object()   # 식의 참조가 아직 정의 전 — 정의가 늘 때마다 다시 센다
_FAILED = object()    # 구문·평가 오류 — 다시 세지 않는다(경고는 이미 냈다)
_DFLAGS = (1, 2, 3, 4, 5)


class ParameterResolver:
    def __init__(self):
        self.params = {}       # 전역 값 {"bndout": "1.0000E-03", ...} (원문 리터럴 보존)
        self.param_types = {}  # {"bndout": "R", ...}
        self.ResetDuplicateState()

    def ResetDuplicateState(self):
        """덱마다 새로 시작하는 상태 — 중복 규칙(R16 *PARAMETER_DUPLICATION·MUTABLE), LOCAL 범위, 아직 못 센 식.
        전역 값 표(params)는 그대로 둔다(같은 매니저가 이어 읽는 덱 — 예전 동작)."""
        self.dflag = None          # *PARAMETER_DUPLICATION DFLAG(없으면 1)
        self._defined = {}         # 전역 이름 → 받아들인 정의 글(이 덱에서 처음 본 것부터)
        self._mutable = set()      # 첫 정의가 MUTABLE 인 전역 이름(문자형은 빼고 — R16 Remark 6)
        self.BeginDeck()

    def BeginDeck(self):
        """덱 하나를 처음부터 훑기 전 — 열린 LOCAL 범위와 못 센 식을 비운다."""
        self._scopes = []          # 읽는 중인 파일마다 LOCAL 정의 — 바깥 파일부터 안쪽 파일 차례
        self._pending = []         # [(이름, 형, 식, 범위 또는 None)] 참조가 아직 정의 전인 식
        self._visible = None       # 지금 보이는 값 표(ChainMap) — 범위가 바뀔 때만 다시 만든다

    def ParseParameterLocal(self, lines):
        """*PARAMETER_LOCAL 블록에서 변수=값 추출

        Args:
            lines: PARAMETER_LOCAL 키워드의 데이터 라인 리스트
        """
        for line in lines:
            if isinstance(line, list):
                for subline in line:
                    self._parse_line(subline)
            elif isinstance(line, str):
                self._parse_line(line)

    def _parse_line(self, line):
        """단일 라인에서 변수명=값 파싱"""
        stripped = line.strip()
        if not stripped or stripped.startswith('$'):
            return

        # 고정 폭 포맷: 컬럼 0-9 = 변수명(타입+이름), 컬럼 10-19 = 값
        # 또는 공백 구분
        parts = stripped.split()
        if len(parts) >= 2:
            var_def = parts[0]  # "Iid", "Rxmin" 등
            val = parts[1]

            # 타입 prefix 제거: I{name} 또는 R{name}
            if len(var_def) >= 2 and var_def[0] in ('I', 'R', 'i', 'r'):
                var_name = var_def[1:].lower()  # "id", "mid", "xmin"
                self.params[var_name] = val
                return var_name, val

    # ── 읽는 차례대로 정의 받기 (리더가 파일·인클루드 차례를 몰고 온다) ─────────────

    def BeginFile(self):
        """파일 읽기 시작 — 이 파일의 LOCAL 범위를 연다(R16 *PARAMETER Remark 5)."""
        self._scopes.append({'vals': {}, 'types': {}, 'text': {}, 'mutable': set()})
        self._visible = None

    def EndFile(self):
        """파일 끝 — 그 파일의 LOCAL 은 사라진다("disappear when the input parser finishes reading the file in which
        they appear"). 그 범위에서 끝내 못 센 식은 버리고 알린다."""
        if not self._scopes:
            return
        sc = self._scopes.pop()
        for name, _, expr, target in self._pending:
            if target is sc:
                print(f"  Warning: PARAMETER_EXPRESSION_LOCAL '{name}={expr}' 미해결 참조 — 파일이 끝나 미치환 유지")
        self._pending = [p for p in self._pending if p[3] is not sc]
        self._visible = None

    def ReportPending(self):
        """덱 끝 — 끝내 참조를 못 푼 전역 식을 알리고 비운다."""
        for name, _, expr, _ in self._pending:
            print(f"  Warning: PARAMETER_EXPRESSION '{name}={expr}' 미해결 참조 — 미치환 유지")
        self._pending = []

    def Visible(self):
        """지금 보이는 값 표 — 안쪽 파일의 LOCAL 부터 바깥 파일의 LOCAL, 끝에 전역(LOCAL 이 같은 이름 전역을 가린다).
        ChainMap 이라 정의가 늘어도 다시 만들 필요가 없다."""
        if self._visible is None:
            self._visible = ChainMap(*[sc['vals'] for sc in reversed(self._scopes)], self.params)
        return self._visible

    @staticmethod
    def ParseHeader(kwname):
        """키워드 이름(대문자, '*' 뺌) → ('param'|'expr'|'dup', 옵션 집합), *PARAMETER 계열이 아니면 None.
        R16: 옵션은 "any combination … in any order" — 예전엔 앞부분만 봐서 *PARAMETER_EXPRESSION_LOCAL 과
        *PARAMETER_NOECHO_LOCAL 을 전역으로 읽었다(리뷰 J)."""
        n = kwname.upper()
        if n != 'PARAMETER' and not n.startswith('PARAMETER_'):
            return None
        opts = frozenset(p for p in n[len('PARAMETER'):].split('_') if p)
        if 'DUPLICATION' in opts:
            return ('dup', opts)
        return ('expr' if 'EXPRESSION' in opts else 'param', opts)

    def DefineLine(self, hdr, line):
        """hdr(ParseHeader) 블록의 데이터 줄 하나를 정의로 받는다. 'end' 를 돌려주면 블록의 나머지 줄은 정의가 아니다
        (*PARAMETER_DUPLICATION 은 카드 하나)."""
        kind, opts = hdr
        s = line.strip()
        if not s or s.startswith('$'):
            return None
        if kind == 'dup':
            try:
                v = int(float(re.split(r'[,\s]+', s)[0]))
            except ValueError:
                return 'end'
            if self.dflag is None:
                self.dflag = v
            else:   # R16 Remark 2 "Only one *PARAMETER_DUPLICATION card is allowed … any after the first are ignored"
                print(f"  Warning: *PARAMETER_DUPLICATION 이 또 있다(DFLAG={v}) — 첫 카드(DFLAG={self.dflag})만 쓴다")
            return 'end'
        local, mutable = 'LOCAL' in opts, 'MUTABLE' in opts
        if kind == 'expr':
            got = self._split_expression_line(line)
            if got:
                self._define(got[1], got[0], got[2], local, mutable, is_expr=True)
        else:
            for ptype, name, val in self._split_parameter_line(line):
                self._define(name, ptype, val, local, mutable, is_expr=False)
        return None

    def ParseFromRawLines(self, raw_lines):
        """한 파일 줄 목록의 *PARAMETER 계열 정의를 차례대로 받는다. 인클루드는 따라가지 않는다 — 리더가 읽는 차례
        훑기를 못 했을 때의 대비 경로다. LOCAL 범위는 부르는 쪽이 BeginFile/EndFile 로 연다."""
        hdr = None
        for line in raw_lines:
            if line.startswith('*'):
                m = re.match(r'\*([A-Za-z0-9_]+)', line)
                hdr = self.ParseHeader(m.group(1)) if m else None
                continue
            if hdr is not None and self.DefineLine(hdr, line) == 'end':
                hdr = None

    def _define(self, name, ptype, text, local, mutable, is_expr):
        """이름 하나의 정의를 R16 규칙으로 받는다.
        - 전역 재정의는 첫 정의가 MUTABLE(문자형 제외)이거나 DFLAG 2·4 일 때만 받는다(*PARAMETER_DUPLICATION: 1=경고 후
          무시(기본), 2=경고 후 채택, 3=오류·무시, 4=조용히 채택, 5=조용히 무시).
        - LOCAL 이 같은 이름 전역을 가리는 것은 중복이 아니다. 보이는 LOCAL 을 다시 가리면 중복이다(DUPLICATION Remark 1).
        - 식은 그 자리에서 그때 보이는 값으로 센다("can reference previously defined parameters"). 참조가 아직 정의 전이면
          미뤄 두고 정의가 늘 때마다 다시 센다(예전 KMM 이 받아 주던 앞 참조 — LS-DYNA 라면 오류다).
        예전엔 식을 파일 끝에 몰아 셌고, 메인 해석에 끼워 넣은 인클루드 정의를 다시 읽을 때 거절해 인클루드 식이 자기 LOCAL
        을 못 보고 0 이 됐다(리뷰 J)."""
        dflag = self.dflag if self.dflag in _DFLAGS else 1
        if local:
            if not self._scopes:
                self.BeginFile()
            prev = next((sc for sc in reversed(self._scopes) if name in sc['text']), None)
            if prev is not None and not self._redefine_ok(name, text, prev['text'][name], name in prev['mutable'], dflag):
                return
            target = self._scopes[-1]
            if (prev is None and mutable and ptype != 'C') or (prev is not None and name in prev['mutable']):
                target['mutable'].add(name)
            target['text'][name] = text
        else:
            if name in self._defined:
                if not self._redefine_ok(name, text, self._defined[name], name in self._mutable, dflag):
                    return
            elif mutable and ptype != 'C':
                self._mutable.add(name)
            self._defined[name] = text
            target = None
        # 같은 자리에 미뤄 둔 같은 이름의 식은 이 정의에 밀린다
        self._pending = [p for p in self._pending if not (p[0] == name and p[3] is target)]
        value = self._evaluate(name, ptype, text) if is_expr else str(text).strip()
        if value is _PENDING:
            self._pending.append((name, ptype, text, target))
        elif value is not _FAILED:
            self._store_value(name, ptype, value, target)
            self._retry_pending()

    @staticmethod
    def _redefine_ok(name, text, prev_text, prev_mutable, dflag):
        """이미 정의된 name 의 재정의를 받을지 — 받지 않으면 DFLAG 대로 알린다."""
        new, old = str(text).strip(), str(prev_text).strip()
        if prev_mutable or dflag in (2, 4):
            if dflag == 2 and not prev_mutable and new != old:
                print(f"  Warning: *PARAMETER {name} 재정의({new})를 받아들였다 — 앞 정의({old})는 이 자리부터 바뀐다"
                      f"(R16 *PARAMETER_DUPLICATION DFLAG=2)")
            return True
        if dflag == 3:
            print(f"  🔴 *PARAMETER {name} 재정의({new}) — R16 DFLAG=3 은 오류다(LS-DYNA 는 입력 끝에서 멈춘다). "
                  f"먼저 정의({old})를 남기고 계속한다")
        elif dflag == 1 and new != old:
            print(f"  Warning: *PARAMETER {name} 재정의({new})를 무시했다 — 먼저 정의({old})가 남는다"
                  f"(R16 *PARAMETER_DUPLICATION DFLAG=1, 첫 정의가 MUTABLE 아님)")
        return False

    def _store_value(self, name, ptype, value, target):
        if target is None:
            self.params[name] = value
            self.param_types[name] = ptype
        else:
            target['vals'][name] = value
            target['types'][name] = ptype

    def _evaluate(self, name, ptype, expr):
        """식 → 값 글. 참조가 아직 정의 전이면 _PENDING, 구문·평가 오류면 _FAILED(경고).
        AST 화이트리스트 평가 — 지수표기 리터럴(2.1e5)을 식별자로 오인하지 않고, 파라미터가 pi/e/함수명과 겹쳐도
        파라미터 우선, hang·dunder 탈출 불가."""
        if ptype == 'C':   # R16: 'For type "C" parameters, the expression is not evaluated in any sense, just stored as a string'
            return str(expr).strip()
        try:
            tree = ast.parse(expr, mode='eval').body
        except SyntaxError as e:
            print(f"  Warning: PARAMETER_EXPRESSION '{name}={expr}' 구문 오류 ({e}) — 미치환 유지")
            return _FAILED
        vis = self.Visible()
        deps = _expr_param_deps(tree)
        if not all(d in vis or d in _EXPR_CONSTS for d in deps):
            return _PENDING
        try:
            value = _eval_ast_node(tree, {d: float(vis[d]) for d in deps if d in vis})
        except Exception as e:
            print(f"  Warning: PARAMETER_EXPRESSION '{name}={expr}' 평가 실패 ({e}) — 미치환 유지")
            return _FAILED
        return str(self._nint(value)) if ptype == 'I' else repr(float(value))

    def _retry_pending(self):
        """미뤄 둔 식 가운데 이제 참조가 다 정의된 것을 센다(하나가 풀리면 다른 것이 풀릴 수 있어 진전이 없을 때까지)."""
        progressed = True
        while progressed and self._pending:
            progressed = False
            for p in list(self._pending):
                name, ptype, expr, target = p
                value = self._evaluate(name, ptype, expr)
                if value is _PENDING:
                    continue
                self._pending.remove(p)
                progressed = True
                if value is not _FAILED:
                    self._store_value(name, ptype, value, target)

    @staticmethod
    def _prmr(field):
        """PRMR 칸(형 글자+이름) → (형, 이름 소문자). 형 글자가 없으면 R(LS-DYNA 기본 real)."""
        prmr = field.strip()
        if len(prmr) >= 2 and prmr[0] in _TYPE_CHARS:
            return prmr[0].upper(), prmr[1:].strip().lower()
        return 'R', prmr.lower()

    def _split_parameter_line(self, line):
        """*PARAMETER(·_LOCAL·_MUTABLE·_TYPE) 데이터 줄 → [(형, 이름, 값)] — 한 줄 최대 4쌍.
        LS-DYNA 파라미터 이름·값에는 공백이 없으므로 토큰 분리가 안전하다(HM 등이 값을 10칸 경계 밖으로 흘려 쓰는 관대한
        포맷도 수용 — 고정폭 슬라이스는 'R   bndout 1.0000E-03' 의 값을 잘라먹는다). 'R    dt2ms' 처럼 형 글자가 이름과
        떨어져 있어도 된다(R16 "RSHLTHK", "R␣␣␣SHLTHK" 는 같다). LOCAL 도 같은 문법이다 — 예전 LOCAL 파서는 붙여 쓴
        형식의 첫 쌍만 읽어 'R thk 1.0' 줄을 통째로 버렸다(리뷰 J)."""
        toks = [t for t in re.split(r'[,\s]+', line.strip()) if t]
        out, i, n = [], 0, len(toks)
        while i < n - 1:
            tok = toks[i]
            if len(tok) == 1 and tok in _TYPE_CHARS and i + 2 < n:
                (ptype, name), val = self._prmr(tok + toks[i + 1]), toks[i + 2]
                i += 3
            else:
                (ptype, name), val = self._prmr(tok), toks[i + 1]
                i += 2
            if name:
                out.append((ptype, name, val))
        return out

    def _split_expression_line(self, line):
        """*PARAMETER_EXPRESSION 데이터 줄 → (형, 이름, 식) 또는 None. 식에는 공백이 올 수 있어 이름부만 토큰 분리하고
        나머지 전체를 식으로 쓴다. 식 안 참조의 '&' 는 뗀다(R16 "with or without the leading &")."""
        parts = line.strip().split(None, 1)
        if len(parts) < 2:
            return None
        prmr, rest = parts
        if len(prmr) == 1 and prmr in _TYPE_CHARS:
            sub = rest.split(None, 1)
            if len(sub) < 2:
                return None
            ptype, name, expr = prmr.upper(), sub[0].strip().lower(), sub[1].strip()
        else:
            (ptype, name), expr = self._prmr(prmr), rest.strip()
        if not name or not expr:
            return None
        if ptype != 'C':
            expr = re.sub(r'&(?=[A-Za-z_])', '', expr)
        return ptype, name, expr

    @staticmethod
    def _nint(value):
        """Fortran NINT (반올림 반은 0에서 먼 쪽) — LS-DYNA 정수 파라미터 규약."""
        return int(math.floor(value + 0.5)) if value >= 0 else int(math.ceil(value - 0.5))

    _REF_RE = re.compile(r'&([A-Za-z_][A-Za-z0-9_]*)')

    def RefNames(self, line):
        """줄 안 &참조 이름(소문자) 집합."""
        return {m.group(1).lower() for m in self._REF_RE.finditer(line)}

    def _sub_token(self, body, params=None):
        """토큰 단위 치환 (필드폭 없는 라인: 코멘트/free-format). 길이 가변 허용."""
        params = self.params if params is None else params
        def repl(m):
            name = m.group(1).lower()
            return str(params[name]).strip() if name in params else m.group(0)
        return self._REF_RE.sub(repl, body)

    def SubstituteLine(self, line, params=None):
        """라인 내 &name 참조를 파라미터 값으로 치환 (필드폭 비가정). params 를 주면 그 표(예: Visible())로, 없으면 전역 표로.

        규칙(고정폭 데이터 라인):
        - 값이 토큰폭 이내 → 토큰 span 안에서 우측정렬(val.rjust(tok)). 이는 구
          ResolveAll 동작과 바이트 동일이라 IGA(8칸 등 비-10칸 카드) 회귀 0.
        - 값이 토큰폭 초과 → LS-DYNA 우측정렬 관례대로 **leading 공백을 먼저**
          소비(좌측 확장), 부족하면 trailing 공백으로 확장. 어느 쪽도 부족하면
          %g 컴팩트, 그래도 안 맞으면 경고 후 미치환. (인접 비공백 필드 불침범)
          → &ro='1200.0'/&dens='7.85e-09' 우측정렬 필드에서 인접 오염·크래시 해소.
        코멘트($)·키워드(*)·free-format(콤마) 라인은 필드폭 개념이 없어 토큰 치환.
        정규식 토큰 매칭 → termin/termin_/terminA 접두 충돌 없음, 대소문자 무시.
        """
        params = self.params if params is None else params
        if '&' not in line or not params:
            return line
        eol = ''
        body = line
        if body.endswith('\n'):
            body, eol = body[:-1], '\n'
        lstrip = body.lstrip()
        if lstrip[:1] in ('$', '*') or ',' in body:
            return self._sub_token(body, params) + eol
        result = body
        # 오른쪽→왼쪽 처리: 각 치환은 span 길이 == 값 길이(길이 보존)라 좌측 인덱스 안정
        for m in reversed(list(self._REF_RE.finditer(body))):
            name = m.group(1).lower()
            if name not in params:
                continue
            start, end = m.span()
            tok = end - start
            val = str(params[name]).strip()
            if len(val) <= tok:
                result = result[:start] + val.rjust(tok) + result[end:]
                continue
            # 초과 → 주변 공백으로 확장 (현재 result 기준: 우측 토큰은 이미 반영됨)
            lead = 0
            while start - 1 - lead >= 0 and result[start - 1 - lead] == ' ':
                lead += 1
            trail = 0
            while end + trail < len(result) and result[end + trail] == ' ':
                trail += 1
            v = val
            if len(v) > tok + lead + trail:
                try:
                    v = '%g' % float(val)
                except (TypeError, ValueError):
                    v = val
            extra = len(v) - tok
            if extra > lead + trail:
                print(f"  Warning: &{m.group(1)} 값 '{val}' 이 필드 공백({tok + lead + trail})을 초과 — 미치환")
                continue
            grow_left = min(extra, lead)          # 우측정렬 관례: leading 먼저 소비
            grow_right = extra - grow_left        # 남으면 trailing 으로
            result = result[:start - grow_left] + v + result[end + grow_right:]
        return result + eol

    def Resolve(self, value_str):
        """&variable 참조를 실제 값으로 치환

        Args:
            value_str: "&id" 또는 "123" 등

        Returns:
            치환된 문자열. 해석 불가 시 원본 반환.
        """
        if not isinstance(value_str, str):
            return value_str

        s = value_str.strip()
        if s.startswith('&'):
            var_name = s[1:].lower()
            if var_name in self.params:
                return self.params[var_name]
        return value_str

    def ResolveAll(self, text):
        """텍스트 내 모든 &variable을 치환 (고정 폭 보존)

        Args:
            text: K파일 내용 문자열

        Returns:
            치환된 문자열
        """
        import re
        result = text
        for var_name, val in self.params.items():
            # &변수를 찾아서 같은 폭으로 치환
            patterns = [
                f'&{var_name}',
                f'&{var_name.upper()}',
                f'&{var_name[0].upper()}{var_name[1:]}' if len(var_name) > 1 else f'&{var_name.upper()}',
            ]
            for pat in patterns:
                while pat in result:
                    idx = result.index(pat)
                    old_len = len(pat)
                    new_val = str(val).rjust(old_len)  # 같은 폭으로 우측 정렬
                    result = result[:idx] + new_val + result[idx + old_len:]
        return result

    def HasParams(self):
        return len(self.params) > 0

    def __repr__(self):
        return f"ParameterResolver({self.params})"
