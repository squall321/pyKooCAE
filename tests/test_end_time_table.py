# 각도별 종료 시간 표 계약(KooEndTimeTable)의 낙하 방향 규약·쓰기/읽기 왕복·각도 찾기를 검증하는 시험
"""
실행: venv312/bin/python tests/test_end_time_table.py

낙하 방향 규약은 KooDynaAdvancedModification.DropAttitude 의 코드(RotMat = Rz·Ry·Rx, 각도에 음수)를
여기서 그대로 다시 짜서 대조한다. 표는 RIGID_DROP_ENDTIME 이 쓰고 DROP_ATTITUDE EndTimeTable 이 읽는다.
"""
import math
import os
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(GEN))

from KooCAEManager.KooEndTimeTable import (CORE_COLUMNS, EndTimeLookup, drop_direction, euler_from_direction,  # noqa: E402
                                           fibonacci_angles, load_lookup, read_endtime_table, write_endtime_table)

FAILS = []


def check(name, cond, detail=""):
    print("  %-66s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def kmm_rotmat_direction(roll, pitch, yaw):
    """KooDynaAdvancedModification.py DropAttitude (2355-2383) 의 식을 그대로 옮긴 것."""
    Rx, Ry, Rz = (-v * 3.141592653589793 / 180.0 for v in (roll, pitch, yaw))
    RotMatx = np.array([[1, 0, 0], [0, math.cos(Rx), -math.sin(Rx)], [0, math.sin(Rx), math.cos(Rx)]])
    RotMaty = np.array([[math.cos(Ry), 0, math.sin(Ry)], [0, 1, 0], [-math.sin(Ry), 0, math.cos(Ry)]])
    RotMatz = np.array([[math.cos(Rz), -math.sin(Rz), 0], [math.sin(Rz), math.cos(Rz), 0], [0, 0, 1]])
    RotMat = np.dot(RotMatz, np.dot(RotMaty, RotMatx))
    v = np.dot(RotMat, [0.0, 0.0, -1.0])
    return v / np.linalg.norm(v)


def main():
    print("[1] 낙하 방향 규약 = KMM DropAttitude")
    rng = np.random.default_rng(7)
    worst = 0.0
    for r, p, y in rng.uniform(-180, 180, size=(500, 3)):
        worst = max(worst, float(np.abs(drop_direction(r, p, y) - kmm_rotmat_direction(r, p, y)).max()))
    check("임의 500 자세 최대 차이 < 1e-12", worst < 1e-12, f"worst={worst}")
    check("(0,0,0) → -Z (F1_Back)", np.allclose(drop_direction(0, 0, 0), [0, 0, -1]))
    check("roll 90 → -Y", np.allclose(drop_direction(90, 0, 0), [0, -1, 0], atol=1e-12))
    check("pitch 90 → +X", np.allclose(drop_direction(0, 90, 0), [1, 0, 0], atol=1e-12))

    print("[2] 역산 euler_from_direction")
    worst = 0.0
    for d in rng.normal(size=(500, 3)):
        d = d / np.linalg.norm(d)
        r, p, y = euler_from_direction(d, ndigits=12)
        worst = max(worst, float(np.abs(drop_direction(r, p, y) - d).max()))
    check("방향 → 각도 → 방향 왕복 < 1e-9", worst < 1e-9, f"worst={worst}")

    print("[3] 피보나치 방향")
    angles = fibonacci_angles(1000)
    dirs = np.array([drop_direction(r, p, y) for _, r, p, y in angles])
    check("1000 개, 이름 P0001..P1000", len(angles) == 1000 and angles[0][0] == "P0001" and angles[-1][0] == "P1000")
    check("무게중심이 원점 근처(균일)", float(np.linalg.norm(dirs.mean(axis=0))) < 0.01)
    nn = np.sort(np.arccos(np.clip(dirs @ dirs.T, -1, 1)), axis=1)[:, 1]
    check("최근접 각 최대/최소 < 1.6 (쏠림 없음)", nn.max() / nn.min() < 1.6, f"{nn.max() / nn.min():.2f}")

    print("[4] 쓰기 → 읽기 왕복")
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "model_endtime.csv")
        rows = []
        for i, (name, r, p, y) in enumerate(angles[:5]):
            d = drop_direction(r, p, y)
            rows.append({"name": name, "roll": r, "pitch": p, "yaw": y, "dx": d[0], "dy": d[1], "dz": d[2],
                         "class": "slapdown" if i % 2 else "none", "t1_end_ms": 0.5, "t2_start_ms": None if i % 2 == 0 else 3.0,
                         "t2_end_ms": None if i % 2 == 0 else 3.4, "tfinal_ms": 4.4, "endtim": 0.0044 + i * 1e-4,
                         "governing_e": 0.3, "class_e0.1": "none"})
        write_endtime_table(path, rows, {"deck": "/x/model.k", "units": "mm-t-s", "time_unit": "s"})
        meta, back = read_endtime_table(path)
        check("메타 format·units 보존", meta.get("format", "").startswith("rigid_drop_endtime") and meta.get("units") == "mm-t-s")
        check("줄 수 5", len(back) == 5)
        check("endtim 왕복 정확", all(abs(b["endtim"] - r["endtim"]) < 1e-15 for b, r in zip(back, rows)))
        check("빈칸(None) 은 빈 문자열", back[0]["raw"]["t2_start_ms"] == "")
        check("머리 줄 = 핵심 칸 + 추가 칸", list(back[0]["raw"].keys()) == CORE_COLUMNS + ["class_e0.1"])

        print("[5] 각도 찾기")
        lk = load_lookup(path)
        n0, r0, p0, y0 = angles[0]
        check("같은 각도 → 그 값", lk.find(r0, p0, y0) == rows[0]["endtim"])
        check("0.005° 어긋남 → 찾음", lk.find(r0 + 0.005, p0, y0) == rows[0]["endtim"])
        check("1° 어긋남 → None", lk.find(r0 + 1.0, p0, y0) is None)
        # 같은 방향의 다른 오일러 표현(yaw 로 법선 둘레를 돌린 것이 아니라, 같은 d 를 내는 다른 roll/pitch/yaw)
        d0 = drop_direction(r0, p0, y0)
        alt = None
        for y in np.arange(-180, 180, 0.5):
            # yaw 를 바꾸고 같은 d 가 나오게 roll·pitch 를 다시 푼다
            dz_rot = d0
            dxy = np.array([[math.cos(math.radians(y)), -math.sin(math.radians(y))],
                            [math.sin(math.radians(y)), math.cos(math.radians(y))]]) @ dz_rot[:2]
            r, p, _ = euler_from_direction([dxy[0], dxy[1], dz_rot[2]], ndigits=12)
            if abs(y) > 10 and np.allclose(drop_direction(r, p, y), d0, atol=1e-9):
                alt = (r, p, y)
                break
        check("같은 낙하 방향의 다른 오일러 표현도 찾음", alt is not None and lk.find(*alt) == rows[0]["endtim"], str(alt))
        dup = EndTimeLookup([{"roll": 0, "pitch": 0, "yaw": 0, "endtim": 0.002},
                             {"roll": 0, "pitch": 0, "yaw": 45, "endtim": 0.007}])
        check("같은 방향 여러 줄 → endtim 최대", dup.find(0, 0, 0) == 0.007)

        print("[6] 잘못된 표")
        bad = os.path.join(td, "bad.csv")
        for text, label in (("name,roll,pitch\nA,0,0\n", "endtim 칸 없음"),
                            ("name,roll,pitch,yaw,endtim\nA,0,0,0,0\n", "endtim 0"),
                            ("name,roll,pitch,yaw,endtim\nA,0,x,0,0.1\n", "숫자 아님"),
                            ("# format=x\nname,roll,pitch,yaw,endtim\n", "줄 없음")):
            with open(bad, "w") as f:
                f.write(text)
            try:
                read_endtime_table(bad)
                ok = False
            except ValueError:
                ok = True
            check(f"ValueError — {label}", ok)

    print()
    if FAILS:
        print("FAIL %d" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
