"""
KooPassthroughKeyword - 미지원 키워드를 원문 그대로 저장/출력

IGA 등 파서가 없는 키워드를 원본 보존하여 읽기/쓰기합니다.
"""
from KooCAEManager.KooDynaKeyword import DynaKeyword


class PassthroughKeyword(DynaKeyword):
    """미지원 키워드를 원문 그대로 저장/출력"""

    def __init__(self, keyword_name):
        super().__init__(keyword_name)
        self.raw_lines = []

    def parse(self, lines):
        """원문 라인을 그대로 저장"""
        if isinstance(lines, list) and len(lines) > 0:
            if isinstance(lines[0], list):
                # [[line1, line2, ...], ...] 형태
                for block in lines:
                    self.raw_lines.extend(block)
            else:
                self.raw_lines = list(lines)

    def write(self, stream):
        """원문 그대로 출력"""
        stream.write(f"*{self.name}\n")
        for line in self.raw_lines:
            if isinstance(line, str):
                stream.write(line)
                if not line.endswith('\n'):
                    stream.write('\n')

    def WritetoDynaKeyword(self, startID=0):
        """문자열 반환 버전"""
        result = f"*{self.name}\n"
        for line in self.raw_lines:
            if isinstance(line, str):
                result += line
                if not line.endswith('\n'):
                    result += '\n'
        return result

    def WriteStreamDynaKeyword(self, stream, startID=0):
        """스트림 출력 버전"""
        self.write(stream)
