# 층 분할·임팩터 메시 크기 회귀 시험 — SolidComp 노드 공유, UnstructuredtoStructured 층 분할, MeshSize 기본값
"""
실행: venv312/bin/python tests/test_layer_split.py

  [1] MeshSize   MeshSize 미지정 시 기본 0.001 은 SI 모델에서 그대로, mm 모델에서는 치수/8 로 대체 + 경고
  [2] SolidComp  층 경계 노드를 이웃 요소와 공유 (같은 위치 중복 노드 0, 경계 노드가 요소 8개 공유)
  [3] U2S        UnstructuredtoStructured + LayerThickness 가 minZ 오프셋·다중 파트에서도 올바른 층을 만든다
"""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
PY = str(ROOT / "venv312" / "bin" / "python")
sys.path.insert(0, str(GEN))

FAILS = []


def check(name, cond, detail=""):
    print("  %-66s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def write_box(path, z0=0.0, parts=1):
    """z 로 extrude 한 헥사 플레이트 (평면 4x3, 두께 1.0, 2층). parts=2 면 아래/위를 다른 PID 로."""
    nx, ny, nz, T = 4, 3, 2, 1.0
    idx, nodes, nid = {}, [], 0
    for k in range(nz + 1):
        for j in range(ny + 1):
            for i in range(nx + 1):
                nid += 1
                idx[(i, j, k)] = nid
                nodes.append(f"{nid:8d}{i * 2.5:16.6f}{j * 2.5:16.6f}{z0 + k * T / nz:16.6f}")
    elems, eid = [], 0
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                eid += 1
                pid = 1 if (parts == 1 or k == 0) else 2
                c = [idx[(i, j, k)], idx[(i + 1, j, k)], idx[(i + 1, j + 1, k)], idx[(i, j + 1, k)],
                     idx[(i, j, k + 1)], idx[(i + 1, j, k + 1)], idx[(i + 1, j + 1, k + 1)], idx[(i, j + 1, k + 1)]]
                elems.append(f"{eid:8d}{pid:8d}" + "".join(f"{v:8d}" for v in c))
    f10 = lambda *v: "".join(f"{str(x):>10s}" for x in v)  # noqa: E731
    head = ["*KEYWORD"]
    for p in range(1, parts + 1):
        head += ["*PART", f"P{p}", f10(p, 1, 1)]
    head += ["*SECTION_SOLID", f10(1, 1), "*MAT_ELASTIC", f10(1, "7.85e-9", "200000.0", "0.3"), "*NODE"]
    Path(path).write_text("\n".join(head + nodes + ["*ELEMENT_SOLID"] + elems + ["*END"]) + "\n")


def read_k(path):
    nodes, elems, kw = {}, [], None
    for line in open(path, errors="replace"):
        if line.startswith("*"):
            kw = line.strip().upper()
            continue
        if line.startswith("$") or not line.strip():
            continue
        if kw == "*NODE":
            nodes[int(line[:8])] = tuple(round(float(line[8 + 16 * i:24 + 16 * i]), 5) for i in range(3))
        elif kw and kw.startswith("*ELEMENT_SOLID"):
            elems.append([int(line[i:i + 8]) for i in range(0, 80, 8)])
    return nodes, elems


def run_kmm(workdir, optname):
    return subprocess.run([PY, str(GEN / "KooMeshModifier.py"), optname], cwd=workdir,
                          capture_output=True, text=True, timeout=600)


def main():
    print("[1] 임팩터 MeshSize 기본값")
    with contextlib.redirect_stdout(io.StringIO()):
        from KooCAEManager.KooDynaAdvancedModification import KooDynaAdvancedModification
    adv = KooDynaAdvancedModification.__new__(KooDynaAdvancedModification)

    def resolve(option, dimension):
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            v = adv._ResolveImpactorMeshSize(option, dimension, "T")
        return v, buf.getvalue()

    v, out = resolve({}, [0.008])
    check("SI 기본 치수 0.008 → 기존 기본값 0.001 유지 (경고 없음)", v == 0.001 and "WARNING" not in out, f"{v} {out}")
    v, out = resolve({}, [0.02])
    check("SI 치수 0.02 → 0.001 유지 (20 분할, 과하지 않음)", v == 0.001 and "WARNING" not in out, str(v))
    v, out = resolve({"MeshSize": 0.5}, [2.0])
    check("MeshSize 명시 → 그대로 (경고 없음)", v == 0.5 and "WARNING" not in out, str(v))
    v, out = resolve({}, [2.0])
    check("mm 치수 2.0 → 0.25 로 대체 + 경고", v == 0.25 and "WARNING" in out, f"{v} {out}")
    v, out = resolve({}, [50.0, 10.0])
    check("치수 여러 개면 최대값 기준 (50 → 6.25)", v == 6.25, str(v))
    v, out = resolve({}, [])
    check("치수 없음 → 기본값 0.001 (예외 없음)", v == 0.001, str(v))
    v, out = resolve({}, ["bad"])
    check("치수가 숫자가 아니어도 죽지 않음", v == 0.001, str(v))

    print("[2] SolidComp 층 경계 노드 공유")
    d = tempfile.mkdtemp(prefix="layersplit_comp_")
    write_box(os.path.join(d, "plate.k"))
    Path(d, "opt.txt").write_text("""*Inputfile
plate.k
*Mode
PART_EXCHANGE,1
**PartExchange,1
*PID,1
*ConvertHexato,SolidComp,(0,0,1),5.0
*MID01,*MAT_ELASTIC_TITLE
LayerA
$$     MID        RO         E        PR
     MID01    1.2E-9    1000.0      0.30
*MID02,*MAT_ELASTIC_TITLE
LayerB
$$     MID        RO         E        PR
     MID02    1.4E-9    2000.0      0.30
*THK01,0.2
*THK02,0.8
*NUMEA,1
*NUMEB,2
*Layup
THK01,MID01,EOS,HGID,NUMEA
THK02,MID02,EOS,HGID,NUMEB
*EndLayup
**EndPartExchange
*End
""")
    r = run_kmm(d, "opt.txt")
    check("SolidComp 실행 성공", r.returncode == 0, r.stdout[-400:] + r.stderr[-400:])
    out = os.path.join(d, "plate_pex.k")
    if os.path.exists(out):
        nodes, elems = read_k(out)
        used = {n for e in elems for n in e[2:10]}
        pos = [nodes[n] for n in used]
        check("  같은 위치 중복 노드 0", len(set(pos)) == len(pos), f"{len(set(pos))} != {len(pos)}")
        zs = sorted({p[2] for p in pos})
        check("  z 층 경계 = 0, 0.2, 0.6, 1.0", zs == [0.0, 0.2, 0.6, 1.0], str(zs))
        share = {}
        for e in elems:
            for n in e[2:10]:
                share[n] = share.get(n, 0) + 1
        mid = [share[n] for n in used if 0.0 < nodes[n][2] < 1.0]
        check("  중간 층 노드가 요소 여러 개를 공유 (최대 8)", max(mid) == 8, str(max(mid) if mid else None))
        check("  파트별 요소 수 12 / 24", sorted({e[1] for e in elems}) and
              [sum(1 for e in elems if e[1] == p) for p in sorted({e[1] for e in elems})] == [12, 24],
              str([sum(1 for e in elems if e[1] == p) for p in sorted({e[1] for e in elems})]))

    print("[3] UnstructuredtoStructured + LayerThickness")
    cases = [("minZ=0", 0.0, 1, [0.0, 0.2, 0.7, 1.0]),
             ("minZ=10 (정규화)", 10.0, 1, [10.0, 10.2, 10.7, 11.0]),
             ("2 파트 스택", 0.0, 2, [0.0, 0.2, 0.7, 1.0])]
    for label, z0, parts, want_z in cases:
        d = tempfile.mkdtemp(prefix="layersplit_u2s_")
        write_box(os.path.join(d, "box.k"), z0=z0, parts=parts)
        pids = "1,2" if parts == 2 else "1"
        Path(d, "opt.txt").write_text(f"""*Inputfile
box.k
*Mode
PART_EXCHANGE,1
**PartExchange,1
*PIDS,{pids}
*UnstructuredtoStructured,(4,3,1)
*LayerThickness
0.2
0.5
0.3
*EndLayerThickness
**EndPartExchange
*End
""")
        r = run_kmm(d, "opt.txt")
        check(f"{label}: 실행 성공", r.returncode == 0, (r.stdout[-300:] + r.stderr[-300:]))
        out = os.path.join(d, "box_pex.k")
        if os.path.exists(out):
            nodes, elems = read_k(out)
            used = {n for e in elems for n in e[2:10]}
            zs = sorted({nodes[n][2] for n in used})
            check(f"  z 층 경계 {want_z}", zs == want_z, str(zs))
            check("  요소 36 (4x3 x 3층)", len(elems) == 36, str(len(elems)))
            if parts == 2:
                bypid = {}
                for e in elems:
                    zc = round(sum(nodes[n][2] for n in e[2:10]) / 8, 4)
                    bypid.setdefault(e[1], set()).add(zc)
                check("  아래 두 층은 PID 1, 맨 위 층은 PID 2",
                      bypid.get(1) == {0.1, 0.45} and bypid.get(2) == {0.85}, str(bypid))

    print()
    if FAILS:
        print("FAIL %d 건" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
