# LS-DYNA 없이 누적 체인을 끝까지 흉내내는 검증기 — 스텝 덱 생성 → 합성 dynain → 이월 → 다음 스텝
"""각 스텝마다
   1) 러너가 만드는 옵션 파일로 KMM 실행 (Run_*/<Set>.k 생성)
   2) LS-DYNA 대신 합성 dynain 을 Output/ 에 놓는다 (변형 좌표 + 초기응력)
   3) Run_*/DynamicRelaxation/dynaintoinitial.txt 로 DYNAIN_TO_INITIAL 실행 → Output/*_dti.k
   4) 그 _dti.k 를 다음 스텝 입력으로
카드 구성을 스텝마다 검사해 이월·정리 정책이 지켜지는지 본다."""
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "occProject" / "Generators"
PY = str(ROOT / "venv312" / "bin" / "python")


def cards(path):
    out = {}
    for m in re.finditer(r"^\*([A-Z_0-9]+)", Path(path).read_text(errors="replace"), re.M):
        out[m.group(1)] = out.get(m.group(1), 0) + 1
    return out


def run_kmm(workdir, optname):
    return subprocess.run([PY, str(GEN / "KooMeshModifier.py"), optname], cwd=workdir,
                          capture_output=True, text=True, timeout=1800)


def synth_dynain(deck, dest):
    """LS-DYNA 산출 dynain 흉내 — 변형 좌표(z 0.999배) + 일부 요소 초기응력"""
    nodes, elems, kw = [], [], None
    for line in Path(deck).read_text(errors="replace").splitlines():
        if line.startswith("*"):
            kw = line.strip().upper()
            continue
        if line.startswith("$") or not line.strip():
            continue
        if kw == "*NODE" and len(line) > 55:
            nodes.append(line)
        elif kw and kw.startswith("*ELEMENT_SOLID") and len(line) >= 80:
            elems.append(line)
    out = ["*KEYWORD", "*NODE"]
    for l in nodes:
        try:
            nid = int(l[:8]); x = float(l[8:24]); y = float(l[24:40]); z = float(l[40:56]) * 0.999
        except ValueError:
            continue
        out.append(f"{nid:8d}{x:16.6f}{y:16.6f}{z:16.6f}")
    out.append("*INITIAL_STRESS_SOLID")
    for l in elems[:5]:
        out.append(f"{int(l[:8]):10d}{1:10d}{0:10d}{0:10d}")
        out.append(f"{12.5:10.3f}{3.1:10.3f}{-4.2:10.3f}{0.5:10.3f}{0.2:10.3f}{0.1:10.3f}{0.0:10.3f}{0.0:10.3f}")
    out.append("*END")
    Path(dest).write_text("\n".join(out) + "\n")
    return len(nodes)


def chain(workdir, steps, verbose=True):
    """steps = [(옵션파일 내용, 기대 Set 이름), ...] — 앞 스텝의 _dti.k 를 다음 입력으로 쓴다"""
    workdir = Path(workdir).resolve()   # RunDirectoryMode 경로는 절대여야 한다 (KMM cwd 기준으로 풀린다)
    model = "model.k"
    results = []
    for i, (opt_body, setname) in enumerate(steps, start=1):
        sdir = workdir / f"step{i}"
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / "model.k").write_bytes((workdir / model).read_bytes()) if i == 1 else None
        opt = opt_body.replace("{MODEL}", model).replace("{RUNDIR}", str(sdir))
        (sdir / "opt.txt").write_text(opt)
        r = run_kmm(str(sdir), "opt.txt")
        runs = sorted(sdir.glob("Run_*"))
        if r.returncode != 0 or not runs:
            return results + [{"step": i, "error": f"rc={r.returncode}, Run 폴더 {len(runs)}개",
                               "log": (r.stdout[-600:] + r.stderr[-400:])}]
        run = runs[-1]
        deck = run / f"{setname}.k"
        rec = {"step": i, "deck": str(deck), "cards": cards(deck), "log": r.stdout}
        # 합성 dynain → 이월
        synth_dynain(deck, run / "Output" / "dynain")
        dti_cfg = run / "DynamicRelaxation" / "dynaintoinitial.txt"
        if dti_cfg.exists():
            r2 = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "dynaintoinitial.txt"],
                                cwd=str(run / "DynamicRelaxation"), capture_output=True, text=True, timeout=1800)
            hits = sorted(glob.glob(str(run / "Output" / "*_dti.k")))
            rec["dti"] = hits[0] if hits else None
            rec["dti_rc"] = r2.returncode
            if hits:
                rec["dti_cards"] = cards(hits[0])
                # 다음 스텝 입력으로
                nxt = workdir / f"step{i+1}"
                nxt.mkdir(parents=True, exist_ok=True)
                (nxt / "model.k").write_bytes(Path(hits[0]).read_bytes())
        else:
            rec["dti"] = None
        results.append(rec)
        if verbose:
            print(f"  step{i} {setname}: 카드 {len(rec['cards'])}종, dti={'O' if rec.get('dti') else 'X'}")
    return results
