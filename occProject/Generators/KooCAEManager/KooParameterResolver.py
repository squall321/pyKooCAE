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
                        으로 참조 가능 → 의존 순서 반복 평가
*PARAMETER_LOCAL      : 공백 구분 1쌍/라인 (기존 IGA 경로 호환)

치환(SubstituteLine)은 &name 을 정규식 토큰 단위로 매칭하므로
termin/termin_/termin__/terminA 같은 접두 충돌이 없고, 대소문자 무시,
고정폭 컬럼 보존(토큰+후행공백 예산 내 우측정렬, 초과 시 %g 컴팩트 재포맷,
그래도 안 맞으면 경고 후 미치환)을 보장합니다.
"""
import re
import ast
import math

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


class ParameterResolver:
    def __init__(self):
        self.params = {}       # {"bndout": "1.0000E-03", ...} (원문 리터럴 보존)
        self.param_types = {}  # {"bndout": "R", ...}
        self._expressions = [] # [(name, type, expr_str), ...] 미평가 표현식

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

    # ── *PARAMETER / *PARAMETER_EXPRESSION (표준 문법) ──────────────────────

    def ParseFromRawLines(self, raw_lines):
        """파일 raw 라인 전체에서 *PARAMETER 계열 블록을 스캔해 테이블 구축.

        *PARAMETER_EXPRESSION → 표현식 수집(뒤에서 의존 순서 평가)
        *PARAMETER_LOCAL      → 기존 공백구분 파서(_parse_line, IGA 경로 호환)
        *PARAMETER            → 고정폭 10칸 4쌍/라인 파서
        스캔 후 EvaluateExpressions() 로 표현식 일괄 평가.
        """
        mode = None  # None | 'param' | 'expr' | 'local'
        for line in raw_lines:
            stripped = line.strip()
            if stripped.startswith('*'):
                u = stripped.upper().split()[0]
                if u.startswith('*PARAMETER_EXPRESSION'):
                    mode = 'expr'
                elif u.startswith('*PARAMETER_LOCAL'):
                    mode = 'local'
                elif u.startswith('*PARAMETER_DUPLICATION'):
                    mode = None  # 중복 정책 카드 — 값 정의 아님
                elif u.startswith('*PARAMETER'):
                    mode = 'param'
                else:
                    mode = None
                continue
            if mode is None or not stripped or stripped.startswith('$'):
                continue
            if mode == 'param':
                self._parse_parameter_line(line)
            elif mode == 'expr':
                self._parse_expression_line(line)
            elif mode == 'local':
                self._parse_line(line)
        self.EvaluateExpressions()

    def _store(self, prmr_field, val):
        """PRMR 필드(타입문자+이름)와 값 문자열을 테이블에 저장."""
        prmr = prmr_field.strip()
        if not prmr:
            return
        if prmr[0] in _TYPE_CHARS and len(prmr) >= 2:
            ptype = prmr[0].upper()
            name = prmr[1:].strip().lower()
        else:
            ptype = 'R'  # 타입 미표기 시 LS-DYNA 기본 real
            name = prmr.lower()
        if name:
            self.params[name] = str(val).strip()
            self.param_types[name] = ptype

    def _parse_parameter_line(self, line):
        """*PARAMETER 데이터 라인: PRMRi VALi 쌍(최대 4쌍).

        LS-DYNA 파라미터 이름·값에는 공백이 없으므로 토큰 분리가 안전하다
        (HM 등이 값을 10칸 경계 밖으로 흘려 쓰는 관대한 포맷도 수용 —
        고정폭 슬라이스는 'R   bndout 1.0000E-03' 의 값을 잘라먹는다).
        타입 문자가 'R    dt2ms' 처럼 이름과 분리된 토큰이어도 처리.
        """
        s = line.strip().rstrip('\n')
        if not s:
            return
        toks = [t for t in re.split(r'[,\s]+', s) if t]
        i = 0
        n = len(toks)
        while i < n - 1:
            tok = toks[i]
            if len(tok) == 1 and tok in _TYPE_CHARS and i + 2 < n:
                # 타입문자 단독 토큰 + 이름 + 값 → 합쳐 기존 로직으로
                self._store(tok + toks[i + 1], toks[i + 2])
                i += 3
            else:
                self._store(tok, toks[i + 1])
                i += 2

    def _parse_expression_line(self, line):
        """*PARAMETER_EXPRESSION 데이터 라인: PRMR + 표현식(나머지 전부).

        표현식에는 공백이 올 수 있으므로 이름부만 토큰 분리하고
        나머지 전체를 식으로 취급한다.
        """
        s = line.strip().rstrip('\n')
        if not s:
            return
        parts = s.split(None, 1)
        if len(parts) < 2:
            return
        prmr, rest = parts[0], parts[1]
        if len(prmr) == 1 and prmr in _TYPE_CHARS:
            # 타입문자 단독 토큰 → 다음 토큰이 이름
            sub = rest.split(None, 1)
            if len(sub) < 2:
                return
            ptype = prmr.upper()
            name = sub[0].strip().lower()
            expr = sub[1].strip()
        elif prmr[0] in _TYPE_CHARS and len(prmr) >= 2:
            ptype = prmr[0].upper()
            name = prmr[1:].strip().lower()
            expr = rest.strip()
        else:
            ptype = 'R'
            name = prmr.lower()
            expr = rest.strip()
        if name and expr:
            self._expressions.append((name, ptype, expr))

    @staticmethod
    def _nint(value):
        """Fortran NINT (반올림 반은 0에서 먼 쪽) — LS-DYNA 정수 파라미터 규약."""
        return int(math.floor(value + 0.5)) if value >= 0 else int(math.ceil(value - 0.5))

    def EvaluateExpressions(self):
        """수집된 표현식을 의존 순서로 반복 평가 (미해결 참조는 다음 패스로).

        AST 화이트리스트 평가 — 지수표기 리터럴(2.1e5)을 식별자로 오인하지 않고,
        파라미터가 pi/e/함수명과 겹쳐도 파라미터 우선, hang·dunder 탈출 불가.
        """
        pending = []
        for name, ptype, expr in self._expressions:
            try:
                tree = ast.parse(expr, mode='eval').body
                pending.append((name, ptype, expr, tree))
            except SyntaxError as e:
                print(f"  Warning: PARAMETER_EXPRESSION '{name}={expr}' 구문 오류 ({e}) — 미치환 유지")
        self._expressions = []
        for _ in range(len(pending) + 1):
            if not pending:
                break
            remaining = []
            progressed = False
            for name, ptype, expr, tree in pending:
                deps = _expr_param_deps(tree)
                # 각 dep 는 파라미터(우선) 또는 상수여야 해결 가능. 그 외 → 미해결(전방참조/미정의)
                if not all(d in self.params or d in _EXPR_CONSTS for d in deps):
                    remaining.append((name, ptype, expr, tree))
                    continue
                try:
                    resolved = {d: float(self.params[d]) for d in deps if d in self.params}
                    value = _eval_ast_node(tree, resolved)
                    if ptype == 'I':
                        self.params[name] = str(self._nint(value))
                    else:
                        self.params[name] = repr(float(value))
                    self.param_types[name] = ptype
                    progressed = True
                except Exception as e:
                    print(f"  Warning: PARAMETER_EXPRESSION '{name}={expr}' 평가 실패 ({e}) — 미치환 유지")
                    progressed = True  # 시끄러운 실패도 진전으로 간주(무한루프 방지)
            if not progressed:
                for name, _, expr, _ in remaining:
                    print(f"  Warning: PARAMETER_EXPRESSION '{name}={expr}' 미해결 참조 — 미치환 유지")
                break
            pending = remaining

    _REF_RE = re.compile(r'&([A-Za-z_][A-Za-z0-9_]*)')

    def _sub_token(self, body):
        """토큰 단위 치환 (필드폭 없는 라인: 코멘트/free-format). 길이 가변 허용."""
        def repl(m):
            name = m.group(1).lower()
            return str(self.params[name]).strip() if name in self.params else m.group(0)
        return self._REF_RE.sub(repl, body)

    def SubstituteLine(self, line):
        """라인 내 &name 참조를 파라미터 값으로 치환 (필드폭 비가정).

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
        if '&' not in line or not self.params:
            return line
        eol = ''
        body = line
        if body.endswith('\n'):
            body, eol = body[:-1], '\n'
        lstrip = body.lstrip()
        if lstrip[:1] in ('$', '*') or ',' in body:
            return self._sub_token(body) + eol
        result = body
        # 오른쪽→왼쪽 처리: 각 치환은 span 길이 == 값 길이(길이 보존)라 좌측 인덱스 안정
        for m in reversed(list(self._REF_RE.finditer(body))):
            name = m.group(1).lower()
            if name not in self.params:
                continue
            start, end = m.span()
            tok = end - start
            val = str(self.params[name]).strip()
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
