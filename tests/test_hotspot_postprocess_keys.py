#!/usr/bin/env python3
# postprocess 의 hotspot_* 전용 키와 deep_extra_args 두 경로 회귀 시험
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Runner.PostprocessShellGenerator import build_deep_report_sh

FAILS = []


def cmd(opts):
    sh = build_deep_report_sh("/data/run", "/opt/apptainers/x.sif", opts)
    return " ".join(l.strip() for l in sh.splitlines()
                    if "koo_deep_report" in l or l.strip().startswith("-"))


def chk(name, cond):
    print(f"  {'OK ' if cond else 'NG '} {name}")
    if not cond:
        FAILS.append(name)


BASE = {"yield_stress_mpa": 350, "ua_threads": 8, "sv_threads": 8}

print("[1] 핫스팟 미지정 → 플래그 방출 없음 (기존 시나리오 회귀 0)")
chk("플래그 없음", "hotspot" not in cmd(BASE))

print("[2] 전용 키 경로")
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_top_percent": 3.0,
         "hotspot_min_elements": 8})
chk("--hotspot-clusters", "--hotspot-clusters" in c)
chk("top-percent 3.0", "--hotspot-top-percent 3.0" in c)
chk("min-elements 8", "--hotspot-min-elements 8" in c)

print("[3] 기본값과 같은 값은 생략")
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_top_percent": 5.0,
         "hotspot_distance_factor": 1.5, "hotspot_min_elements": 5,
         "hotspot_max_clusters": 20})
seg = re.search(r"--hotspot.*", c).group(0).strip()
chk("활성화 플래그만 남음", seg == "--hotspot-clusters")

print("[4] 기존 방법(deep_extra_args) 계속 동작")
c = cmd({**BASE, "deep_extra_args": ["--hotspot-clusters",
                                    "--hotspot-top-percent", "2.5"]})
chk("extra_args 통과", "--hotspot-top-percent 2.5" in c)

print("[5] 둘 다 주면 extra_args 가 이긴다 (뒤에 온다)")
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_top_percent": 3.0,
         "deep_extra_args": ["--hotspot-top-percent", "9.9"]})
i3, i9 = c.find("3.0"), c.find("9.9")
chk("extra_args 가 뒤", i3 >= 0 and i9 > i3)

print("[6] 활성화 키 없이 값만 주면 방출 안 함")
chk("방출 없음", "hotspot" not in
    cmd({**BASE, "hotspot_top_percent": 3.0, "hotspot_min_elements": 8}))

print("[7] 해석 불가한 값은 경고 후 무시 (조용히 잘못된 플래그를 만들지 않음)")
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_top_percent": "삼점영"})
chk("활성화는 유지", "--hotspot-clusters" in c)
chk("잘못된 값 미방출", "삼점영" not in c)

print("[8] 셸 이스케이프 — 값에 공백/와일드카드가 와도 안전")
c = cmd({**BASE, "hotspot_clusters": True,
         "deep_extra_args": ["--section-view-target-patterns", "*a b*"]})
chk("따옴표 처리", "'*a b*'" in c)

print()
if FAILS:
    print(f"[FAIL] 실패 {len(FAILS)} 건: {FAILS}")
    sys.exit(1)
print("[PASS] 실패 0 건")
