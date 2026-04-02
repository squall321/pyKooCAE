"""
KooIncludeManager - *INCLUDE 파일 추적, 복사, 검증

K파일에서 *INCLUDE로 참조된 파일 목록을 스캔하고,
파일 이동 시 include 파일을 함께 복사합니다.
"""
import os
import shutil


class KooIncludeManager:
    def __init__(self, k_file_path):
        self.main_file = os.path.abspath(k_file_path)
        self.base_dir = os.path.dirname(self.main_file)
        self.include_files = []  # 절대경로 목록
        self.visited = set()     # 순환 참조 방지

    def Scan(self):
        """메인 K파일에서 *INCLUDE 파일 목록 추출 (재귀)"""
        self.include_files = []
        self.visited = set()
        self._scan_file(self.main_file)
        return self.include_files

    def _scan_file(self, file_path):
        """파일에서 *INCLUDE 줄 추출"""
        abs_path = os.path.abspath(file_path)
        if abs_path in self.visited:
            print(f"Warning: Circular include detected: {abs_path}")
            return
        self.visited.add(abs_path)

        if not os.path.exists(abs_path):
            return

        base = os.path.dirname(abs_path)
        in_include = False

        with open(abs_path, 'r', errors='replace') as f:
            for line in f:
                stripped = line.strip()
                if stripped.upper().startswith('*INCLUDE'):
                    in_include = True
                    continue
                if in_include:
                    if stripped.startswith('*') or stripped.startswith('$') or not stripped:
                        in_include = False
                        continue
                    # include 파일 경로
                    inc_path = stripped
                    if not os.path.isabs(inc_path):
                        inc_path = os.path.join(base, inc_path)
                    inc_path = os.path.abspath(inc_path)
                    if os.path.exists(inc_path):
                        if inc_path not in self.include_files:
                            self.include_files.append(inc_path)
                        self._scan_file(inc_path)  # 재귀
                    else:
                        print(f"Warning: Include file not found: {inc_path}")
                    in_include = False

    def CopyTo(self, target_dir):
        """include 파일을 target_dir로 복사 (같은 폴더에 flat)"""
        if not self.include_files:
            self.Scan()
        os.makedirs(target_dir, exist_ok=True)
        copied = 0
        for inc_path in self.include_files:
            dst = os.path.join(target_dir, os.path.basename(inc_path))
            if not os.path.exists(dst):
                shutil.copy2(inc_path, dst)
                copied += 1
        if copied > 0:
            print(f"IncludeManager: Copied {copied} include files to {target_dir}")
        return copied

    def Validate(self):
        """누락 파일 목록 반환"""
        if not self.include_files:
            self.Scan()
        missing = []
        for inc_path in self.include_files:
            if not os.path.exists(inc_path):
                missing.append(inc_path)
        return missing

    def GetAllFiles(self):
        """메인 + include 전체 절대경로 목록"""
        if not self.include_files:
            self.Scan()
        return [self.main_file] + list(self.include_files)

    def GetIncludeBasenames(self):
        """include 파일명 목록 (상대경로)"""
        if not self.include_files:
            self.Scan()
        return [os.path.basename(f) for f in self.include_files]
