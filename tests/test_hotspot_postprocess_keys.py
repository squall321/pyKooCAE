#!/usr/bin/env python3
# postprocess 의 hotspot_* 전용 키와 deep_extra_args 두 경로 회귀 시험
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Runner.PostprocessShellGenerator import build_deep_report_sh, build_sphere_report_sh

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

print("[9] 기준량 키 — 문자열/배열/별칭, 기본값 생략, 모르는 이름 경고")
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_criterion": "von_mises"})
chk("기본값 von_mises 는 생략", "--hotspot-criterion" not in c)
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_criterion": ["max_principal", "min_principal"]})
chk("배열 → 쉼표 목록", "--hotspot-criterion max_principal,min_principal" in c)
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_criterion": "VM, Sigma3"})
chk("별칭·대소문자 정규화", "--hotspot-criterion von_mises,min_principal" in c)
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_criterion": "tresca"})
chk("tresca 는 max_shear 별칭(엔진·deep 과 같다)", "--hotspot-criterion max_shear" in c)
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_criterion": "von_misses"})
chk("전부 모르는 이름이면 플래그 없음(=von_mises 기본)", "--hotspot-criterion" not in c)
c = cmd({**BASE, "hotspot_criterion": "min_principal"})
chk("활성화 없이 기준만 주면 방출 안 함", "--hotspot" not in c)

print("[10] 기준 7종·별칭 표·시간 집계 — KooD3plotReader e8460d9 와 같은 이름")
c = cmd({**BASE, "hotspot_clusters": True,
         "hotspot_criterion": ["max_shear", "x_tension", "y_tension", "z_tension"]})
chk("새 기준 4종 그대로", "--hotspot-criterion max_shear,x_tension,y_tension,z_tension" in c)
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_criterion": "P1, tau-max, SXX, sigma_yy, szz, P3"})
chk("별칭·대소문자·하이픈 정규화",
    "--hotspot-criterion max_principal,max_shear,x_tension,y_tension,z_tension,min_principal" in c)
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_criterion": "tresca,max_shear"})
chk("별칭과 표준 이름 중복 제거", "--hotspot-criterion max_shear" in c and "max_shear,max_shear" not in c)
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_time_aggregate": "elemmax_then_mean"})
chk("시간 집계 기본값은 생략", "--hotspot-time-aggregate" not in c)
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_time_aggregate": "Both"})
chk("시간 집계 both", "--hotspot-time-aggregate both" in c)
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_time_aggregate": "mean-then-timemax"})
chk("하이픈 표기 정규화", "--hotspot-time-aggregate mean_then_timemax" in c)
c = cmd({**BASE, "hotspot_clusters": True, "hotspot_time_aggregate": "nope"})
chk("모르는 방식은 경고하고 버림", "--hotspot-time-aggregate" not in c and "--hotspot-clusters" in c)
c = cmd({**BASE, "hotspot_time_aggregate": "both"})
chk("활성화 없이 시간 집계만 주면 방출 안 함", "--hotspot" not in c)

print("[11] 전각도 핫스팟 파트 필터 — hotspot_part → koo_sphere_report --hotspot-part")


def sph(opts):
    return build_sphere_report_sh("/data/out", "/opt/apptainers/x.sif", opts)


chk("미지정 → 플래그 없음", "--hotspot-part" not in sph(BASE))
chk("None·빈 값·bool 은 미지정과 같다",
    sph(BASE) == sph({**BASE, "hotspot_part": None}) == sph({**BASE, "hotspot_part": ""})
    == sph({**BASE, "hotspot_part": True}))
chk("정수 목록", "--hotspot-part 12,15" in sph({**BASE, "hotspot_part": [12, 15]}))
chk("정수 하나", "--hotspot-part 7" in sph({**BASE, "hotspot_part": 7}))
chk("쉼표 문자열·공백·중복 정리", "--hotspot-part 12,15" in sph({**BASE, "hotspot_part": " 12, 15,12"}))
s = sph({**BASE, "hotspot_part": "12;rm -rf /"})
chk("숫자가 아니면 버림(셸에 안 박힘)", "--hotspot-part" not in s and "12;rm" not in s)  # 템플릿 자체에 rm -rf 줄이 있다
s = sph({**BASE, "hotspot_part": "3,x,9"})
chk("섞이면 숫자만", "--hotspot-part 3,9" in s)
s = sph({**BASE, "hotspot_part": [12], "sphere_extra_args": ["--hotspot-part", "99"]})
chk("sphere_extra_args 가 뒤에 와서 이긴다", s.index("--hotspot-part 12") < s.index("--hotspot-part 99"))

print("[12] 3D 인벨롭 뷰어 — sphere_viewer → koo_sphere_report --viewer")
chk("미지정 → 플래그 없음", "--viewer" not in sph(BASE))
chk("기본 canvas 는 생략", "--viewer" not in sph({**BASE, "sphere_viewer": "canvas"}))
chk("plotly", "--viewer plotly" in sph({**BASE, "sphere_viewer": "Plotly"}))
s = sph({**BASE, "sphere_viewer": "webgl"})
chk("모르는 값은 경고하고 버림", "--viewer" not in s)
s = sph({**BASE, "sphere_viewer": "plotly", "hotspot_part": [3], "sphere_extra_args": ["--viewer", "canvas"]})
chk("순서 — 파트 필터·뷰어 다음에 추가 인자(추가 인자가 이긴다)",
    s.index("--hotspot-part 3") < s.index("--viewer plotly") < s.index("--viewer canvas"))

print()
if FAILS:
    print(f"[FAIL] 실패 {len(FAILS)} 건: {FAILS}")
    sys.exit(1)
print("[PASS] 실패 0 건")
