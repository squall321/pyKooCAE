# 벽 파트 고도화 계획: DropSurface 설정화 + DeformableToRigidAutomatic

## 1. 배경 및 문제

### 1-1. DropSurface 하드코딩 문제
`CumulativeScenarioRunner._create_step_config()` (line 636)에서 벽 크기/메쉬가 하드코딩:
```
DropSurface,Plane,300,300,20,30,30,2
```
벽 크기, 메쉬 해상도, roughness 등을 scenario.json에서 제어할 수 없음.

### 1-2. DeformableToRigid 기능 부재
현재 벽 파트는 `*MAT_ELASTIC`(deformable)로 생성.
접촉이 없을 때도 deformable로 계산 → 불필요한 연산 비용.
`*DEFORMABLE_TO_RIGID_AUTOMATIC` paired switch를 적용하면:
- 접촉 전: rigid (빠른 계산)
- 접촉 중: deformable (정확한 접촉 해석)
- 접촉 후: rigid (다시 빠른 계산)

---

## 2. LS-DYNA `*DEFORMABLE_TO_RIGID_AUTOMATIC` 키워드 사양 (R16)

참조: `docs/LS-DYNA/Vol_I_Chapters/19_DEFORMABLE_TO_RIGID.pdf`

### 카드 구조

**Card 1** (필수):
| 변수 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| SWSET | I | none | 스위치 셋 고유 번호 |
| CODE | I | 0 | 0=시간, 1=RW force=0, 2=contact force=0, 3=RW force!=0, 4=contact force!=0, 5=sensor |
| TIME1 | F | 0. | 스위칭 시작 시간 |
| TIME2 | F | 1e20 | 스위칭 종료 시간 |
| TIME3 | F | 0. | 딜레이 |
| ENTNO | I | 0 | contact surface 번호 (CODE 1~4) |
| RELSW | I | 0 | 관련 스위치 셋 번호 |
| PAIRED | I | 0 | 0=없음, 1=first, -1=second |

**Card 2** (필수):
| 변수 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| NRBF | I | 0 | Nodal rigid body flag |
| NCSF | I | 0 | Nodal constraint set flag |
| RWF | I | 0 | Rigid wall flag |
| DTMAX | F | 0. | 스위칭 후 최대 dt |
| D2R | I | 0 | deformable→rigid 파트 수 |
| R2D | I | 0 | rigid→deformable 파트 수 |
| OFFSET | F | 0. | 접촉 두께 오프셋 (CODE 3,4) |

**Card 3** (D2R 수만큼): PID, LRB, PTYPE
**Card 4** (R2D 수만큼): PID, PTYPE

### 낙하 시뮬레이션 Paired Switch 패턴

```
$ SWSET 20: contact force=0 → deformable→rigid (first)
*DEFORMABLE_TO_RIGID_AUTOMATIC
$  swset  code  time1  time2  time3  entno  relsw  paired
      20     2    0.0  1e20    0.0    CID      10       1
$  nrbf  ncsf   rwf  dtmax   D2R   R2D  offset
     0     0     0    0.0     1     0    0.0
   WALL_PID     0    PART
$
$ SWSET 10: contact force!=0 → rigid→deformable (second)
*DEFORMABLE_TO_RIGID_AUTOMATIC
$  swset  code  time1  time2  time3  entno  relsw  paired
      10     4    0.0  1e20    0.0    CID      20      -1
$  nrbf  ncsf   rwf  dtmax   D2R   R2D  offset
     0     0     0    0.0     0     1    0.0
   WALL_PID    PART
```

### 호환성 확인
- 벽 파트: `*MAT_ELASTIC`로 시작 (deformable) → D2R 전환 가능 (**`*MAT_RIGID` 시작은 불가**)
- 접촉: `*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE` → CODE=4 지원 대상
- `surfacetosurfaceContact.cid` → ENTNO로 사용 가능

---

## 3. 현재 코드 구조 (데이터 흐름)

```
scenario.json
  └ simulation_params: { height, tFinal, dt, density, ... }
       ↓
CumulativeDesigner.design()  (Runner/CumulativeDesigner.py:126)
  └ simulation_params를 runner_config.json에 그대로 전달
       ↓
runner_config.json
  └ simulation_params: { ... }
       ↓
CumulativeScenarioRunner._create_step_config()  (Runner/CumulativeScenarioRunner.py:596~638)
  └ sim_params = self.config.get("simulation_params", {})
  └ DropSurface,Plane,300,300,20,30,30,2  ← 하드코딩
       ↓
step_config.txt  (KooMeshModifier 입력)
       ↓
KooMeshModifier 파서  (occProject/Generators/KooMeshModifier.py:1221~1368)
  └ curOptions["DropSurface"] = ["Plane", x, y, z, nx, ny, nz]
       ↓
KooDynaAdvancedModification.DropAttitude()  (line 1910~2244)
  └ 벽 파트 생성 (AddSolidPart + CreateImpactBox)
  └ 접촉 생성 (CreateContactAutomaticSurfacetoSurface)
  └ .k 파일 출력 (WriteModifiedFile → dynaImporter.WriteStreamDynaKeyword())
       ↓
DropSet.k + dynaintoinitial.txt
```

### 키워드 출력 구조
- `WriteModifiedFile()` → `dynaImporter.WriteStreamDynaKeyword()` 호출
- `additionalManager.WriteStreamDynaKeyword()` → rigidwalls, hourglasses, interfaces 순서로 출력
- 새 키워드 추가 시: `additionalManager`에 D2R 클래스/리스트 추가 → `WriteStreamDynaKeyword()`에서 출력

---

## 4. 구현 계획

### Phase 1: DropSurface 설정화 (하드코딩 제거)

#### 4-1-A. scenario.json 입력 형식 확장

```json
{
  "simulation_params": {
    "height": 1500,
    "tFinal": 0.005,
    "dt": 0.000001,
    "density": 7850,
    "youngs_modulus": 200000000000,
    "poisson_ratio": 0.3,
    "drop_surface": {
      "type": "Plane",
      "size": [300, 300, 20],
      "mesh": [30, 30, 2]
    }
  }
}
```

- `drop_surface`가 없으면 기본값: `Plane,300,300,20,30,30,2`
- `type: "PlanewithRoughness"`이면 추가 필드: `roughness_mode`, `r_max`, `shape_factor`, `shape_factor2`

코드 수정 불필요: `simulation_params`는 이미 scenario.json → runner_config.json에 그대로 전달됨.

#### 4-1-B. CumulativeScenarioRunner._create_step_config() 수정

**파일**: `Runner/CumulativeScenarioRunner.py` (line 636)

Before:
```python
DropSurface,Plane,300,300,20,30,30,2
```

After:
```python
# drop_surface 설정 읽기
drop_surface = sim_params.get("drop_surface", {})
ds_type = drop_surface.get("type", "Plane")
ds_size = drop_surface.get("size", [300, 300, 20])
ds_mesh = drop_surface.get("mesh", [30, 30, 2])

# step_config.txt에 반영
drop_surface_line = f"DropSurface,{ds_type},{ds_size[0]},{ds_size[1]},{ds_size[2]},{ds_mesh[0]},{ds_mesh[1]},{ds_mesh[2]}"

# PlanewithRoughness인 경우 추가 파라미터
if ds_type == "PlanewithRoughness":
    roughness = drop_surface.get("roughness_mode", "Random")
    r_max = drop_surface.get("r_max", 0.0)
    sf1 = drop_surface.get("shape_factor", 0.0)
    sf2 = drop_surface.get("shape_factor2", sf1)
    drop_surface_line += f",{roughness},{r_max},{sf1},{sf2}"
```

### Phase 2: DeformableToRigid 옵션 추가

#### 4-2-A. scenario.json 입력

```json
{
  "simulation_params": {
    "drop_surface": {
      "type": "Plane",
      "size": [300, 300, 20],
      "mesh": [30, 30, 2],
      "deformable_to_rigid": true
    }
  }
}
```

- `deformable_to_rigid`가 없거나 false → 기존 동작 (변경 없음)

#### 4-2-B. CumulativeScenarioRunner._create_step_config() 추가

Phase 1의 drop_surface 읽기에 이어서:
```python
d2r = drop_surface.get("deformable_to_rigid", False)
if d2r:
    drop_surface_line += "\nDeformableToRigid,True"
```

step_config.txt에 `DeformableToRigid,True` 줄 추가.

#### 4-2-C. KooMeshModifier 파서 수정

**파일**: `occProject/Generators/KooMeshModifier.py` (line 1337 부근, `elif "dropsurface"` 다음)

```python
elif "deformabletorigid" in line.lower():
    svector = line.split(",")
    curOptions["DeformableToRigid"] = svector[1].strip().lower() == "true"
```

기본값 설정 (line 1224 부근, curOptions 초기화):
```python
curOptions["DeformableToRigid"] = False
```

#### 4-2-D. KooDynaAdditional.py에 D2R 클래스 추가

**파일**: `occProject/Generators/KooCAEManager/KooDynaAdditional.py`

새 클래스: `KooDeformableToRigidAutomatic`
```python
class KooDeformableToRigidAutomatic:
    def __init__(self, swset, code, time1, time2, time3, entno, relsw, paired,
                 nrbf, ncsf, rwf, dtmax, d2r_pids, r2d_pids, offset=0.0):
        self.swset = swset
        self.code = code
        self.time1 = time1
        self.time2 = time2
        self.time3 = time3
        self.entno = entno
        self.relsw = relsw
        self.paired = paired
        self.nrbf = nrbf
        self.ncsf = ncsf
        self.rwf = rwf
        self.dtmax = dtmax
        self.d2r_pids = d2r_pids   # list of (pid, lrb)
        self.r2d_pids = r2d_pids   # list of pid
        self.offset = offset

    def WriteDynaKeyword(self):
        # *DEFORMABLE_TO_RIGID_AUTOMATIC 키워드 출력
        kw = "*DEFORMABLE_TO_RIGID_AUTOMATIC\n"
        kw += "$  swset    code   time1   time2   time3   entno   relsw  paired\n"
        kw += f"{self.swset:>10}{self.code:>10}{self.time1:>10.1f}{self.time2:>10.1e}"
        kw += f"{self.time3:>10.1f}{self.entno:>10}{self.relsw:>10}{self.paired:>10}\n"
        kw += "$  nrbf    ncsf     rwf   dtmax     D2R     R2D  offset\n"
        kw += f"{self.nrbf:>10}{self.ncsf:>10}{self.rwf:>10}{self.dtmax:>10.1f}"
        kw += f"{len(self.d2r_pids):>10}{len(self.r2d_pids):>10}{self.offset:>10.1f}\n"
        for pid, lrb in self.d2r_pids:
            kw += f"{pid:>10}{lrb:>10}      PART\n"
        for pid in self.r2d_pids:
            kw += f"{pid:>10}      PART\n"
        return kw

    def WriteStreamDynaKeyword(self, stream):
        stream.write(self.WriteDynaKeyword())
```

`KooDynaAdditionalManager`에 추가:
```python
# __init__에 추가
self.d2r_automatics = {}

# 새 메서드
def CreateDeformableToRigidAutomatic(self, swset, code, entno, relsw, paired,
                                      d2r_pids, r2d_pids, offset=0.0):
    d2r = KooDeformableToRigidAutomatic(
        swset, code, 0.0, 1e20, 0.0, entno, relsw, paired,
        0, 0, 0, 0.0, d2r_pids, r2d_pids, offset)
    self.d2r_automatics[swset] = d2r
    return d2r

# WritetoDynaKeyword()에 추가
for key in self.d2r_automatics:
    keyword += self.d2r_automatics[key].WriteDynaKeyword()

# WriteStreamDynaKeyword()에 추가
for key in self.d2r_automatics:
    self.d2r_automatics[key].WriteStreamDynaKeyword(stream)
```

#### 4-2-E. KooDynaAdvancedModification.DropAttitude() 수정

**파일**: `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py`
**위치**: line 2143 (surfacetosurfaceContact 생성 직후, 각 angle iteration 내부)

```python
# 기존 코드 (line 2143):
surfacetosurfaceContact = self.dynaImporter.contactManager.CreateContact...

# 추가:
if option.get("DeformableToRigid", False):
    cid = surfacetosurfaceContact.cid
    wall_pid = part.id
    # Paired switch: SWSET 20 (D2R, first), SWSET 10 (R2D, second)
    self.dynaImporter.additionalManager.CreateDeformableToRigidAutomatic(
        swset=20, code=2, entno=cid, relsw=10, paired=1,
        d2r_pids=[(wall_pid, 0)], r2d_pids=[])
    self.dynaImporter.additionalManager.CreateDeformableToRigidAutomatic(
        swset=10, code=4, entno=cid, relsw=20, paired=-1,
        d2r_pids=[], r2d_pids=[wall_pid])
```

**위치 주의**: 각 angle(i) 반복에서 i!=0일 때 이전 d2r_automatics를 제거해야 함.
```python
if i != 0:
    # 기존: part, contact, initV 제거
    ...
    # 추가: 이전 D2R automatic도 제거
    self.dynaImporter.additionalManager.d2r_automatics.clear()
```

### Phase 3: dynaintoinitial.txt (변경 없음)

D2R 키워드는 LS-DYNA 실행 중에만 동작.
`dynaintoinitial.txt`의 `*RemovePartbyID`, `*RemoveContactbyID`는 기존대로 유지.
dynain 변환 시 D2R 관련 키워드는 자동으로 제거됨 (파트 자체가 제거되므로).

---

## 5. 수정 파일 목록

| # | 파일 | 작업 | Phase |
|---|------|------|-------|
| 1 | `Runner/CumulativeScenarioRunner.py` | `_create_step_config()`: DropSurface 하드코딩 제거, D2R 옵션 전달 | 1, 2 |
| 2 | `occProject/Generators/KooMeshModifier.py` | `DeformableToRigid` 키워드 파서 + 기본값 추가 | 2 |
| 3 | `occProject/Generators/KooCAEManager/KooDynaAdditional.py` | `KooDeformableToRigidAutomatic` 클래스 + Manager 연동 | 2 |
| 4 | `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py` | `DropAttitude()`: D2R paired switch 생성 + iteration cleanup | 2 |

**scenario.json**: 사용자 설정 (코드 수정 불필요, optional field)

---

## 6. 테스트 계획

### 6-1. DropSurface 설정화 테스트
1. `drop_surface` 없는 기존 scenario.json → step_config.txt에 `Plane,300,300,20,30,30,2` 기본값 확인
2. `drop_surface: {type: "Plane", size: [500,500,30], mesh: [50,50,3]}` → 반영 확인
3. `PlanewithRoughness` + roughness 파라미터 → step_config.txt 검증

### 6-2. DeformableToRigid 테스트
1. `deformable_to_rigid: false` (기본) → 기존과 동일하게 동작, D2R 키워드 없음
2. `deformable_to_rigid: true` → 생성된 DropSet.k에 `*DEFORMABLE_TO_RIGID_AUTOMATIC` 2세트 확인
3. LS-DYNA 실행 → d3hsp에서 "switching" 관련 메시지 확인
4. Cumulative multi-step → dynain 변환 후 D2R 키워드 잔류 없음 확인

### 6-3. 기존 호환성 테스트
1. Test_001 (26방향 1step) → scenario.json 수정 없이 기존대로 동작
2. Test_005 (Fibonacci 100) → 동일

---

## 7. 빌드 및 배포

수정 완료 후:
```bash
./build_KooChainRun_python312.sh
# 배포
cp -r build_dist/KooChainRun.dist/* /data/SmartTwinPreprocessor/lib/KooChainRun/
cp build_dist/KooChainRun.dist/KooChainRun /data/SmartTwinPreprocessor/bin/KooChainRun
```

KooMeshModifier는 별도 바이너리이므로 `occProject/` 수정 시 KooMeshModifier도 리빌드 필요.
