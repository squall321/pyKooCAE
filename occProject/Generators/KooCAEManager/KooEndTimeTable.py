# 각도별 종료 시간 표(<base>_endtime.csv)의 쓰기·읽기·각도 찾기와 KMM DropAttitude 낙하 방향 규약을 한곳에 둔 계약 모듈
"""
표 형식 — RIGID_DROP_ENDTIME 이 쓰고 DROP_ATTITUDE 의 EndTimeTable 이 읽는다.
  '# key=value' 메타 줄들 → csv 머리 줄 → 각도마다 한 줄
  필수 칸: roll, pitch, yaw (도), endtim (덱 시간 단위 ENDTIM — 소비 쪽은 그대로 넣는다)

낙하 방향(덱 좌표계): d = Rz(-yaw)·Ry(-pitch)·Rx(-roll)·(0,0,-1)
  KooDynaAdvancedModification.DropAttitude 의 RotMat·(0,0,-√(2gh)) 와 같은 규약이다.
  바닥이 등방이고 초기 회전이 없으면 낙하 결과는 d 에만 달려 있으므로, 표는 d 로 찾는다.
"""
import csv
import math

import numpy as np

FORMAT = "rigid_drop_endtime/endtime v1"
REQUIRED_COLUMNS = ("roll", "pitch", "yaw", "endtim")
CORE_COLUMNS = ["name", "roll", "pitch", "yaw", "dx", "dy", "dz", "class",
                "t1_end_ms", "t2_start_ms", "t2_end_ms", "tfinal_ms", "endtim", "governing_e"]
MATCH_TOL_DEG = 0.01


def drop_direction(roll, pitch, yaw=0.0):
    """KMM DropAttitude 규약의 낙하 방향 단위 벡터 (덱 좌표계)."""
    r, p, y = (math.radians(float(v)) for v in (roll, pitch, yaw))
    dx, dy, dz = math.sin(p) * math.cos(r), -math.sin(r), -math.cos(p) * math.cos(r)
    return np.array([dx * math.cos(y) + dy * math.sin(y), -dx * math.sin(y) + dy * math.cos(y), dz])


def rotation_from_euler(roll, pitch, yaw=0.0):
    """KMM DropAttitude 의 RotMat = Rz(-yaw)·Ry(-pitch)·Rx(-roll). 바닥 좌표계 벡터 → 덱 좌표계 벡터."""
    a, b, c = (-math.radians(float(v)) for v in (roll, pitch, yaw))
    rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return rz @ ry @ rx


def euler_from_rotation(m):
    """RotMat(바닥 → 덱) → (roll, pitch, yaw) 도. rotation_from_euler 의 역. pitch=±90 이면 yaw=0 으로 둔다."""
    m = np.asarray(m, dtype=float)
    b = math.asin(max(-1.0, min(1.0, -m[2, 0])))
    if abs(math.cos(b)) > 1e-9:
        a = math.atan2(m[2, 1], m[2, 2])
        c = math.atan2(m[1, 0], m[0, 0])
    else:
        a = math.atan2(-m[1, 2], m[1, 1])
        c = 0.0
    return -math.degrees(a), -math.degrees(b), -math.degrees(c)


def euler_from_direction(d, ndigits=2):
    """낙하 방향 → (roll, pitch, 0). AngleSourceParser._dir_to_euler 와 같은 역산(roll ∈ [-90, 90])."""
    d = np.asarray(d, dtype=float)
    d = d / np.linalg.norm(d)
    roll = -math.degrees(math.asin(max(-1.0, min(1.0, d[1]))))
    pitch = math.degrees(math.atan2(d[0], -d[2]))
    return round(roll, ndigits), round(pitch, ndigits), 0.0


def fibonacci_angles(n):
    """실제 낙하 방향 공간에서 균일한 n 방향(피보나치 나선) → [(P0001, roll, pitch, 0), ...]."""
    golden = math.pi * (3.0 - math.sqrt(5.0))
    out = []
    for i in range(int(n)):
        z = 1.0 - 2.0 * (i + 0.5) / n
        rho = math.sqrt(max(0.0, 1.0 - z * z))
        d = (rho * math.cos(golden * i), rho * math.sin(golden * i), z)
        roll, pitch, yaw = euler_from_direction(d)
        out.append((f"P{i + 1:04d}", roll, pitch, yaw))
    return out


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return "" if math.isnan(v) else format(v, ".10g")
    return str(v)


def write_endtime_table(path, rows, meta):
    """rows: dict 목록(CORE_COLUMNS + 그 밖의 칸은 첫 줄의 순서대로). meta: 머리 '# key=value' 줄."""
    extra = [k for k in rows[0] if k not in CORE_COLUMNS] if rows else []
    columns = CORE_COLUMNS + extra
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(f"# format={FORMAT}\n")
        for k, v in meta.items():
            f.write(f"# {k}={_fmt(v)}\n")
        w = csv.writer(f)
        w.writerow(columns)
        for r in rows:
            w.writerow([_fmt(r.get(c)) for c in columns])


def read_endtime_table(path):
    """→ (meta dict, rows). rows 는 name·roll·pitch·yaw·endtim(float) 과 원래 칸(raw)을 가진다."""
    meta, body = {}, []
    with open(path, newline="", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                k, _, v = line[1:].strip().partition("=")
                meta[k.strip()] = v.strip()
            elif line.strip():
                body.append(line)
    reader = csv.DictReader(body)
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"EndTimeTable {path}: missing columns {missing}")
    rows = []
    for n, raw in enumerate(reader, start=1):
        try:
            row = {"name": raw.get("name", ""), "roll": float(raw["roll"]), "pitch": float(raw["pitch"]),
                   "yaw": float(raw["yaw"]), "endtim": float(raw["endtim"]), "raw": raw}
        except (TypeError, ValueError) as exc:
            raise ValueError(f"EndTimeTable {path}: bad number in data row {n}: {exc}") from None
        if not row["endtim"] > 0.0 or math.isinf(row["endtim"]):
            raise ValueError(f"EndTimeTable {path}: endtim must be positive (data row {n}: {raw['endtim']})")
        rows.append(row)
    if not rows:
        raise ValueError(f"EndTimeTable {path}: no data rows")
    return meta, rows


class EndTimeLookup:
    """표의 각도를 낙하 방향으로 찾는다. 사이 각 tol_deg 이하인 줄이 여럿이면 endtim 최대."""

    def __init__(self, rows, path=""):
        self.path = path
        self.rows = rows
        self.dirs = np.array([drop_direction(r["roll"], r["pitch"], r["yaw"]) for r in rows])
        self.endtims = np.array([r["endtim"] for r in rows])

    def find(self, roll, pitch, yaw=0.0, tol_deg=MATCH_TOL_DEG):
        """→ endtim 또는 None(없음)."""
        cosang = self.dirs @ drop_direction(roll, pitch, yaw)
        hit = cosang >= math.cos(math.radians(tol_deg))
        return float(self.endtims[hit].max()) if hit.any() else None


def load_lookup(path):
    _, rows = read_endtime_table(path)
    return EndTimeLookup(rows, path)
