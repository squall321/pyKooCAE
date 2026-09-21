# pyKooCAE Runner/체인에서 KooRemapper op를 한 스텝으로 실행하는 Generator 모듈 래퍼.
"""KooRemapper as a pyKooCAE Generator-style module.

Wraps the stateless CLI SIF (or the raw binary) so a Runner/chain step can run a
KooRemapper operation against a case directory and get back the produced files —
no service (api/postgres/mcp) required. Mirrors how pyKooCAE calls other tool
modules (a subprocess to a run.sh / apptainer image).

Two invocation shapes cover chain use:
  - yaml ops  (matdb, warpage, assemble, …): pass a `config` dict or a config.yaml
  - positional ops (generate, map, info, …): pass `argv` (list of tokens)

For a fully dict-driven invocation of ANY of the 45 ops (arg validation + config
generation from a plain dict), install `kooremapper-core` and build the argv/yaml
with it; this module keeps the dependency-free subprocess path.

Example:
    m = KooRemapperModule(sif="/opt/kooremapper/cli.sif")
    out = m.run("matdb", workdir="/cases/phone", config={
        "model": "model.k", "output": "mapped.k",
        "database": "/opt/kooremapper/materials/material_db.json",
        "materials": [{"match": "AL7003H", "mat_type": "MAT_PIECEWISE_LINEAR_PLASTICITY"},
                      {"match": "*"}],
    })
    # out == ["mapped.k", ...]  (new files created in the case dir)
"""
from __future__ import annotations

import subprocess
from pathlib import Path

try:
    import yaml  # optional — only needed for dict-based yaml ops

    class _IndentDumper(yaml.SafeDumper):
        # Indent block sequences UNDER their key ("materials:\n  - match: …").
        # matdb's minimal YAML parser requires list items to be more-indented than
        # the key; PyYAML's default aligns them at the key's column, which the
        # parser then ignores (rules silently dropped → everything hits the '*').
        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, False)

    def _normalize_block_text(data):
        """Make a multi-line card safe to emit as a `|` literal block.

        LS-DYNA cards are fixed-width, so trailing blanks, tabs (a placeholder for
        columns) and blank lines around the card carry no meaning — but each of
        them makes PyYAML drop the literal block (trailing blanks and tabs give a
        quoted "*MAT_ELASTIC\n…" scalar, leading blank lines give a `|2` header).
        KooRemapper's line-oriented parser then reads that one line as the card and
        silently emits a deck with mid=0. None of this moves a column.
        """
        lines = [line.rstrip() for line in data.split("\n")]
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines) + "\n" if lines else ""

    def _represent_str(dumper, data):
        # Multi-line strings (restack layers' material_card, assemble cards) must go
        # out as `key: |`; PyYAML's default quoted scalar is not a card to KooRemapper.
        text = _normalize_block_text(data)
        if "\n" in text.rstrip("\n"):
            return dumper.represent_scalar("tag:yaml.org,2002:str", text, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    _IndentDumper.add_representer(str, _represent_str)

    def check_block_cards(cfg):
        """고정폭 카드에 TAB 이 있으면 거부한다.

        TAB 을 몇 칸으로 펴야 하는지는 카드마다 다르다. 펴서 넘기면 KooRemapper 는
        카드로 받아들이지만 값이 엉뚱한 칸에 들어가 **조용히 틀린 덱**이 나온다.
        (펴지 않으면 PyYAML 이 리터럴 블록을 못 쓰고 따옴표 스칼라로 떨어져
         KooRemapper 가 rc=1 로 거절한다 — 그 전에 여기서 이유를 알려 준다.)"""
        def walk(node, path):
            if isinstance(node, dict):
                for k, v in node.items():
                    walk(v, f"{path}.{k}" if path else str(k))
            elif isinstance(node, (list, tuple)):
                for i, v in enumerate(node):
                    walk(v, f"{path}[{i}]")
            elif isinstance(node, str) and "\t" in node and "\n" in node.rstrip("\n"):
                raise ValueError(
                    f"KooRemapper config {path}: 여러 줄 카드에 TAB 이 있다. "
                    f"고정폭 카드의 TAB 은 칸 위치를 보존할 수 없으므로 공백으로 직접 정렬할 것")
        walk(cfg, "")

    def dump_kooremapper_yaml(cfg):
        """KooRemapper 가 읽는 YAML 문자열을 만든다 (체인·모듈 공용).

        여러 줄 카드는 `|` 리터럴 블록으로, 비ASCII(한글 제목 등)는 그대로 내보낸다.
        allow_unicode 가 없으면 PyYAML 이 비ASCII 를 특수문자로 보고 블록 대신
        따옴표 스칼라로 떨어뜨려 KooRemapper 가 카드를 못 읽는다."""
        check_block_cards(cfg)
        return yaml.dump(cfg, Dumper=_IndentDumper, sort_keys=False,
                         default_flow_style=False, allow_unicode=True)
except Exception:  # pragma: no cover
    yaml = None
    _IndentDumper = None
    check_block_cards = None
    dump_kooremapper_yaml = None


class KooRemapperModule:
    """Run KooRemapper ops for a pyKooCAE chain step."""

    def __init__(self, sif: str | None = None, binary: str | None = None, timeout: float = 1800):
        """Provide either a CLI SIF (preferred, portable) or a native binary path."""
        if not sif and not binary:
            raise ValueError("provide sif=... (cli.sif) or binary=... (KooRemapper)")
        # Resolve to absolute — run() executes with cwd=workdir, so a relative
        # sif/binary path would resolve against the case dir and be missed.
        self.sif = str(Path(sif).resolve()) if sif else None
        self.binary = str(Path(binary).resolve()) if binary else None
        self.timeout = timeout

    def _invoke(self, workdir: Path, argv: list[str]) -> subprocess.CompletedProcess:
        if self.sif:
            cmd = ["apptainer", "run", "--bind", f"{workdir}:/work", "--pwd", "/work", self.sif, *argv]
        else:
            cmd = [self.binary, *argv]
        return subprocess.run(cmd, cwd=str(workdir), capture_output=True, text=True, timeout=self.timeout, encoding='utf-8', errors='replace')

    @staticmethod
    def _snapshot(workdir: Path) -> set[str]:
        return {p.relative_to(workdir).as_posix() for p in workdir.rglob("*") if p.is_file()}

    def run(self, operation: str, workdir: str, *, argv: list[str] | None = None,
            config: dict | None = None, config_name: str = "config.yaml") -> list[str]:
        """Run `operation` in `workdir`. Returns the relative paths of files created.

        - yaml ops: pass `config` (dict → written to config_name) or point argv at an
          existing yaml. - positional ops: pass `argv` tokens after the op name.
        Raises RuntimeError on non-zero exit.
        """
        wd = Path(workdir).resolve()
        if not wd.is_dir():
            raise FileNotFoundError(f"workdir not found: {wd}")

        if config is not None:
            if yaml is None:
                raise RuntimeError("PyYAML required for dict config; pass a config.yaml via argv instead")
            (wd / config_name).write_text(dump_kooremapper_yaml(config), encoding="utf-8")
            call_argv = [operation, config_name]
        elif argv is not None:
            call_argv = [operation, *argv]
        else:
            call_argv = [operation]

        before = self._snapshot(wd)
        proc = self._invoke(wd, call_argv)
        if proc.returncode != 0:
            raise RuntimeError(
                f"KooRemapper {operation} failed (exit {proc.returncode}):\n{proc.stderr[-1500:]}"
            )
        after = self._snapshot(wd)
        return sorted(after - before)
