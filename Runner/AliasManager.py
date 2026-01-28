#!/usr/bin/env python3
"""
Alias Manager - 별칭 관리 유틸리티

simulation_index.json을 기반으로 별칭(Alias)과 Run ID 간의 매핑을 관리합니다.

Usage:
    # 별칭으로 폴더 조회
    python AliasManager.py index.json "GalaxyS25_CUM006_DOE001_S003_DROP_F1"

    # 체인 조회
    python AliasManager.py index.json "GalaxyS25_CUM006_DOE001_S003_DROP_F1" --chain

    # 시나리오 요약
    python AliasManager.py index.json --summary scenario_001

Author: koo.park
Email: koo.park@samsung.com
Group: CAE
"""

import os
import sys
import json
import re
import argparse
from typing import Dict, Any, List, Optional, Tuple


def parse_alias(alias: str) -> Optional[Dict[str, Any]]:
    """별칭을 컴포넌트로 파싱"""
    # CUM 패턴: GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40
    cum_pattern = r"(.+)_CUM(\d{3})_DOE(\d{3})_S(\d{3})_([A-Z]+)_(.+)"
    # SEQ 패턴: GalaxyS25_SEQ024_S001_DROP_F1
    seq_pattern = r"(.+)_SEQ(\d{3})_S(\d{3})_([A-Z]+)_(.+)"

    cum_match = re.match(cum_pattern, alias)
    if cum_match:
        return {
            "project": cum_match.group(1),
            "scenario_type": "CUM",
            "total_steps": int(cum_match.group(2)),
            "doe_index": int(cum_match.group(3)),
            "step": int(cum_match.group(4)),
            "mode": cum_match.group(5),
            "condition": cum_match.group(6)
        }

    seq_match = re.match(seq_pattern, alias)
    if seq_match:
        return {
            "project": seq_match.group(1),
            "scenario_type": "SEQ",
            "total_steps": int(seq_match.group(2)),
            "doe_index": None,
            "step": int(seq_match.group(3)),
            "mode": seq_match.group(4),
            "condition": seq_match.group(5)
        }

    return None


def generate_alias_cumulative(project: str, total_steps: int, doe_index: int,
                               step: int, mode: str, condition: str) -> str:
    """DOE 기반 누적 시나리오용 별칭 생성"""
    return f"{project}_CUM{total_steps:03d}_DOE{doe_index:03d}_S{step:03d}_{mode}_{condition}"


def generate_alias_sequential(project: str, total_steps: int,
                               step: int, mode: str, condition: str) -> str:
    """순차 시나리오용 별칭 생성"""
    return f"{project}_SEQ{total_steps:03d}_S{step:03d}_{mode}_{condition}"


class AliasManager:
    """별칭-Run ID 매핑 관리"""

    def __init__(self, index_path: str):
        with open(index_path, 'r', encoding='utf-8') as f:
            self.index = json.load(f)
        self.index_path = index_path
        self._build_lookup()

    def _build_lookup(self):
        """역참조 테이블 생성"""
        self.alias_to_runid = {}
        self.runid_to_alias = {}
        self.alias_to_info = {}

        for scenario in self.index.get("scenarios", []):
            for alias, info in scenario.get("runs", {}).items():
                run_id = info.get("run_id")
                if run_id:
                    self.alias_to_runid[alias] = run_id
                    self.runid_to_alias[run_id] = alias
                self.alias_to_info[alias] = info

    def get_run_id(self, alias: str) -> Optional[str]:
        """별칭 → Run ID"""
        return self.alias_to_runid.get(alias)

    def get_alias(self, run_id: str) -> Optional[str]:
        """Run ID → 별칭"""
        return self.runid_to_alias.get(run_id)

    def get_folder(self, alias: str) -> Optional[str]:
        """별칭 → 폴더 경로"""
        info = self.alias_to_info.get(alias)
        if info:
            return info.get("folder")
        return None

    def get_info(self, alias: str) -> Optional[Dict[str, Any]]:
        """별칭 → 전체 정보"""
        return self.alias_to_info.get(alias)

    def get_status(self, alias: str) -> Optional[str]:
        """별칭 → 상태"""
        info = self.alias_to_info.get(alias)
        if info:
            return info.get("status")
        return None

    def get_chain(self, alias: str) -> List[Tuple[str, str, str, str]]:
        """
        해당 alias의 전체 체인 반환 (첫 단계부터 끝까지)

        Returns:
            [(alias, mode, condition, status), ...] 리스트
        """
        components = parse_alias(alias)
        if not components:
            return []

        chain = []
        for a, info in self.alias_to_info.items():
            a_comp = parse_alias(a)
            if (a_comp and
                a_comp["project"] == components["project"] and
                a_comp["scenario_type"] == components["scenario_type"] and
                a_comp["total_steps"] == components["total_steps"] and
                a_comp.get("doe_index") == components.get("doe_index")):
                status = info.get("status", "unknown")
                chain.append((a_comp["step"], a, a_comp["mode"], a_comp["condition"], status))

        chain.sort(key=lambda x: x[0])
        return [(a, mode, cond, status) for _, a, mode, cond, status in chain]

    def get_chain_by_mode(self, alias: str, mode_filter: Optional[str] = None) -> List[Tuple[str, str, str, str]]:
        """특정 모드만 필터링한 체인 반환"""
        chain = self.get_chain(alias)
        if mode_filter:
            return [(a, m, c, s) for a, m, c, s in chain if m == mode_filter]
        return chain

    def get_scenario_summary(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """시나리오 요약 정보 반환"""
        for scenario in self.index.get("scenarios", []):
            if scenario.get("id") == scenario_id:
                runs = scenario.get("runs", {})

                # 모드별 카운트
                mode_counts = {}
                status_counts = {"completed": 0, "running": 0, "pending": 0, "failed": 0}

                for alias, info in runs.items():
                    mode = info.get("mode", "UNKNOWN")
                    mode_counts[mode] = mode_counts.get(mode, 0) + 1

                    status = info.get("status", "unknown")
                    if status in status_counts:
                        status_counts[status] += 1

                return {
                    "id": scenario.get("id"),
                    "name": scenario.get("name"),
                    "type": scenario.get("type"),
                    "total_steps": scenario.get("total_steps"),
                    "doe_count": scenario.get("doe_count"),
                    "total_runs": scenario.get("total_runs"),
                    "status": scenario.get("status"),
                    "mode_sequence": scenario.get("mode_sequence", []),
                    "mode_counts": mode_counts,
                    "status_counts": status_counts,
                    "completed_runs": status_counts["completed"],
                    "progress": f"{status_counts['completed']}/{scenario.get('total_runs', 0)}"
                }
        return None

    def list_all_aliases(self) -> List[str]:
        """모든 별칭 목록 반환"""
        return list(self.alias_to_info.keys())

    def search_aliases(self, pattern: str) -> List[str]:
        """패턴으로 별칭 검색"""
        import fnmatch
        return [a for a in self.alias_to_info.keys() if fnmatch.fnmatch(a, pattern)]


def main():
    parser = argparse.ArgumentParser(description="Alias Manager - 별칭 관리 유틸리티")
    parser.add_argument("index_file", help="Path to simulation_index.json")
    parser.add_argument("alias", nargs="?", help="Alias to look up")
    parser.add_argument("--chain", action="store_true", help="Show full chain for alias")
    parser.add_argument("--summary", metavar="SCENARIO_ID", help="Show scenario summary")
    parser.add_argument("--list", action="store_true", help="List all aliases")
    parser.add_argument("--search", metavar="PATTERN", help="Search aliases by pattern")
    args = parser.parse_args()

    if not os.path.exists(args.index_file):
        print(f"Error: Index file not found: {args.index_file}")
        sys.exit(1)

    manager = AliasManager(args.index_file)

    if args.list:
        print("All Aliases:")
        for alias in sorted(manager.list_all_aliases()):
            info = manager.get_info(alias)
            status = info.get("status", "?") if info else "?"
            print(f"  {alias} [{status}]")
        sys.exit(0)

    if args.search:
        print(f"Search results for '{args.search}':")
        for alias in sorted(manager.search_aliases(args.search)):
            info = manager.get_info(alias)
            status = info.get("status", "?") if info else "?"
            print(f"  {alias} [{status}]")
        sys.exit(0)

    if args.summary:
        summary = manager.get_scenario_summary(args.summary)
        if summary:
            print(f"Scenario: {summary['name']}")
            print(f"ID: {summary['id']}")
            print(f"Type: {summary['type']}")
            print(f"Status: {summary['status']}")
            print(f"Progress: {summary['progress']}")
            print(f"\nMode Breakdown:")
            for mode, count in summary['mode_counts'].items():
                print(f"  - {mode}: {count} steps")
            print(f"\nStatus Breakdown:")
            for status, count in summary['status_counts'].items():
                if count > 0:
                    print(f"  - {status}: {count}")
            print(f"\nMode Sequence: {summary['mode_sequence']}")
        else:
            print(f"Scenario not found: {args.summary}")
        sys.exit(0)

    if args.alias:
        if args.chain:
            chain = manager.get_chain(args.alias)
            if chain:
                components = parse_alias(args.alias)
                doe_info = f"DOE{components['doe_index']:03d}" if components.get('doe_index') else "SEQ"
                print(f"Chain for {doe_info}:")
                for alias, mode, condition, status in chain:
                    comp = parse_alias(alias)
                    step = comp['step'] if comp else '?'
                    status_icon = {"completed": "[v]", "running": "[>]", "pending": "[ ]", "failed": "[x]"}.get(status, "[?]")
                    print(f"  Step {step}: {alias} {status_icon} ({mode})")
            else:
                print(f"No chain found for: {args.alias}")
        else:
            info = manager.get_info(args.alias)
            if info:
                print(f"Alias: {args.alias}")
                print(f"Run ID: {info.get('run_id', 'N/A')}")
                print(f"Folder: {info.get('folder', 'N/A')}")
                print(f"Mode: {info.get('mode', 'N/A')}")
                print(f"Condition: {info.get('condition', 'N/A')}")
                print(f"Status: {info.get('status', 'N/A')}")
                if info.get('prev'):
                    print(f"Prev: {info.get('prev')}")
                if info.get('completed_at'):
                    print(f"Completed: {info.get('completed_at')}")
            else:
                print(f"Alias not found: {args.alias}")
        sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
