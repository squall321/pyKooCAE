"""
KooParameterResolver - *PARAMETER_LOCAL 변수 해석

LS-DYNA의 *PARAMETER_LOCAL 키워드에서 변수를 파싱하고,
K파일 내의 &variable 참조를 실제 값으로 치환합니다.

변수 타입:
  I{name} = integer value   (Iid, Imid 등)
  R{name} = real value      (Rxmin, Rofs 등)
"""


class ParameterResolver:
    def __init__(self):
        self.params = {}  # {"id": "3", "mid": "2", "xmin": "0", ...}

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
