# KooMeshModifier 모드: WEAK_COUPLING

## 1. 목적/개요

`WEAK_COUPLING` 모드는 **외부 LS-DYNA 해석 결과(d3plot)의 변위 이력**을 읽어, 현재 모델의 지정된 절점들에 **강제 변위 경계조건(`*BOUNDARY_PRESCRIBED_MOTION_NODE`)** 으로 적용하는 단방향 약결합(weak coupling) 기능이다.

전체 글로벌 모델을 한 번 해석한 뒤, 그 결과(변위장)를 부분(서브) 모델의 경계 절점에 시간 이력 곡선으로 주입하여 부분 모델만 다시 정밀 해석하는 "글로벌→로컬" 시나리오를 자동화하기 위한 모드로 보인다. 결합 방향은 외부 결과 → 현재 모델 한 방향이며, 현재 모델의 반작용이 외부 결과로 되돌아가지 않으므로 "약결합"이다.

동작 요약:
- 외부 d3plot을 로드(전체 또는 BoundaryBox 영역 한정)
- 현재 모델의 NodeSet 또는 SegmentSet에서 대상 절점 좌표를 수집
- 외부 결과의 변위장을 각 대상 절점 위치로 보간(IDW, k=3 최근접)
- 각 절점에 X/Y/Z 방향별 `*DEFINE_CURVE` + `*BOUNDARY_PRESCRIBED_MOTION_NODE` 생성
- 외부 결과의 시간 범위에 맞춰 `*CONTROL`/`*DATABASE` 설정

> 주의: 전용 예제가 존재하지 않으며(아래 5절 참고), 본 문서는 전적으로 코드 근거로 작성되었다. 일부 코드 경로에 런타임 버그로 의심되는 부분이 있어 실제 동작 검증이 **확인 필요**하다(5절 참고).

---

## 2. 입력 옵션·인자(표)

KooMeshModifier 입력 파일에서 두 곳에 선언한다.

### (1) `*Mode` 블록에 모드 등록 (KooMeshModifier.py:270-272)

`*Mode` 블록 내 한 줄로 모드를 등록한다.

| 항목 | 값 | 설명 |
|------|-----|------|
| 모드 키워드 | `weak_coupling` | `*Mode` 블록 줄에 `weak_coupling,<id>` 형태로 기입. 대소문자 무관(`svector[0].lower()`로 매칭, KooMeshModifier.py:270) |
| modeID | 정수 | 모드 식별 ID. 콤마 뒤 두 번째 토큰(`int(svector[1])`, KooMeshModifier.py:272) |

### (2) `*WeakCoupling,<id>` 옵션 블록 (KooMeshModifier.py:1581-1615)

옵션 블록의 트리거는 `*weakcoupling`(소문자 비교, KooMeshModifier.py:1581)이며, 블록은 `**end` 또는 빈 줄을 만나면 종료된다(KooMeshModifier.py:1590-1593).

| 옵션 줄 | 형식 | 필수 | 설명 |
|---------|------|------|------|
| 블록 헤더 | `*WeakCoupling,<id>` | 필수 | `<id>`는 `int(svector[1])`로 파싱되어 옵션 dict 키(modeID)가 됨 (KooMeshModifier.py:1582-1583) |
| `FilePath` | `FilePath,<d3plot 경로>` | 필수 | 외부 LS-DYNA 결과 d3plot 파일 경로. `svector[1]` 그대로 사용(`.strip()` 없음, KooMeshModifier.py:1594-1597) → `option["FilePath"]` |
| `Set` | `Set,<Mode>,<SetID>` | 필수 | `<Mode>`는 `NodeSet` 또는 `SegmentSet`. `<SetID>`는 `KooDynaInt`로 파싱. `option["Mode"]`, `option["SetID"]`에 저장 (KooMeshModifier.py:1598-1604) |
| `BoundaryBox` | `BoundaryBox,<minX>,<maxX>,<minY>,<maxY>,<minZ>,<maxZ>` | 선택 | 외부 결과를 해당 박스 영역으로 한정 로드. 6개 값 모두 `KooDynaFloat`. 미지정 시 `None`으로 초기화되어 전체 결과 로드 (KooMeshModifier.py:1585-1586, 1605-1614) |

옵션 dict의 최종 키: `FilePath`, `Mode`, `SetID`, `BoundaryBox` (KooDynaAdvancedModification.py:110-114에서 동일 키로 사용).

> 참고(트리거 키워드 불일치): 모드 등록부 트리거는 `weak_coupling`(언더스코어, KooMeshModifier.py:270)인데, 옵션 블록 트리거는 `*weakcoupling`(언더스코어 없음, KooMeshModifier.py:1581)이다. 두 줄의 표기가 다르므로 입력 파일 작성 시 각각의 정확한 표기를 따라야 한다.

---

## 3. 사용 예제

**전용 예제 없음.** `Examples/` 트리 및 `occProject/Generators/` 전체에서 WEAK_COUPLING 전용 설정 파일이나 입력 .k/.txt가 발견되지 않았다(grep으로 확인). 기존 매뉴얼(`occProject/Generators/KooMeshModifier_Manual.md:78-80`)에도 "현재 예제 폴더에 전용 설정 파일은 없음(제공된 `WeakCoupling*.txt`는 Drop Attitude 내용)"이라고 명시되어 있다.

아래는 **코드 파서 분기(KooMeshModifier.py:270-272, 1581-1615)에서 역산한 입력 블록 형식**이며, 실행 검증된 예제가 아니다(확인 필요).

```
*Mode
weak_coupling,1

*WeakCoupling,1
FilePath,/path/to/global/d3plot
Set,NodeSet,101
BoundaryBox,-10.0,10.0,-10.0,10.0,0.0,5.0
**end
```

- `Set` 줄의 두 번째 토큰을 `SegmentSet`으로 바꾸면 세그먼트 세트의 절점들이 대상이 된다(KooMeshModifier.py:1598-1604, KooDynaAdvancedModification.py:134-140).
- `BoundaryBox` 줄을 생략하면 외부 결과 전체가 로드된다(KooDynaAdvancedModification.py:117-118).

---

## 4. 동작 원리(코드 근거)

### 4.1 디스패치

- `*Mode` 블록 파싱 시 `weak_coupling` 줄을 만나면 `modeList`에 `"WEAK_COUPLING"` 등록 (KooMeshModifier.py:270-272).
- 실행 루프에서 `mode == "WEAK_COUPLING"`이면 `self.GenerateWeakCoupling(modeid)` 호출, 출력 파일명 접미사 `_wc` 추가 (KooMeshModifier.py:2813-2815).
- `GenerateWeakCoupling`은 옵션 dict를 꺼내 `self.advancedModification.WeakCoupling(curOption)`로 위임 (KooMeshModifier.py:2463-2465).

### 4.2 외부 결과 로드

`WeakCoupling`은 먼저 `BoundaryBox` 유무에 따라 외부 d3plot을 로드한다 (KooDynaAdvancedModification.py:109-126):

- `BoundaryBox is None` → `ImportExternalDynaResult(d3plotPath)` (전체 로드)
- 그 외 → `ImportExternalDynaResultinBoundaryBox(d3plotPath, minX..maxZ)` (영역 한정 로드)

이 메서드들은 `externalDynaResultManager`를 통해 d3plot 리더를 구성한다 (KooMeshImporter.py:205-209). 내부적으로 `KooD3Plot.SetReader()`/`SetData()`(또는 `SetDatainBoundaryBox`)를 호출한다 (KooD3plot.py:174-185).

### 4.3 대상 절점 좌표 수집

`Mode` 값에 따라 분기 (KooDynaAdvancedModification.py:127-140):

- `NodeSet`: `nodeSetManager.nodeSets[setID]`의 `nodes`를 순회하며 `points[node.id]` 채움 (KooDynaAdvancedModification.py:128-133)
- `SegmentSet`: `segmentSetManager.segmentSetList[setID]`의 각 세그먼트 절점을 순회하여 `points[node.id]` 채움 (KooDynaAdvancedModification.py:134-140)

### 4.4 변위 보간

- 외부 결과의 시간축: `externalDynaResultManager.GetTimeData()` (KooDynaAdvancedModification.py:141 / KooD3plot.py:171-172)
- 변위 보간: `InterpolateDisplacement(points)` (KooDynaAdvancedModification.py:142)
  - 내부적으로 `KooD3Plot.interpolate_displacement(new_points, k=3)` (KooD3plot.py:115-133)
  - 보간 방식: 각 타임스텝마다 KDTree로 **k=3 최근접 절점**을 찾고 **거리 역수 가중(IDW)** 평균으로 변위를 계산 (KooD3plot.py:124-128: `weights = 1/distances`, `dot(weights, nearest_disp)/weights.sum()`)

### 4.5 경계조건 생성

각 대상 절점에 대해 X/Y/Z 변위 이력을 모아 방향별로 곡선과 강제 운동 경계를 생성한다 (KooDynaAdvancedModification.py:143-164):

- 방향별 변위 이력(`dispx/dispy/dispz`)을 시간 순으로 수집 (KooDynaAdvancedModification.py:148-151)
- 각 방향마다 `defineManager.CreateDefineCurve(...)`로 `*DEFINE_CURVE` 생성(시간 vs 변위), `lcid` 획득 (KooDynaAdvancedModification.py:153-158)
- 각 방향마다 `boundaryNodeManager.CreateBoundaryPrescribedMotionNode(name, node, dof, vad=0, lcid, sf=1.0, vid=0, death=1.e28, birth=0)` 생성 (KooDynaAdvancedModification.py:162-164)
  - `dof`: X=1, Y=2, Z=3 / `vad=0`(변위) / `sf=1.0` / `death=1.e28`
  - 이름: `WeakCoupling_<nid>_X|Y|Z` (KooDynaAdvancedModification.py:159-161)
  - 시그니처 근거: `CreateBoundaryPrescribedMotionNode(self, name, node, dof, vad=0, lcid=None, sf=1.0, vid=0, death=1.0E28, birth=0.0)` (KooBoundaryNode.py:699-703)

### 4.6 제어/출력 설정

외부 결과 시간 범위에 맞춰 종료 시간과 시간간격을 설정한다 (KooDynaAdvancedModification.py:166-168):

- `tFinal = times[-1]`, `dt = tFinal/len(times)`
- `SetControlandDatabaseExplicit(tFinal, dt)` 호출 (KooDynaAdvancedModification.py:1873~)
  - `*CONTROL_TERMINATION` 존재 시 `ENDTIM`만 갱신, 없으면 신규 생성 (KooDynaAdvancedModification.py:1877-1882)
  - `*CONTROL_TIMESTEP`/`*CONTROL_HOURGLASS` 없으면 기본값 생성 (KooDynaAdvancedModification.py:1885-1892)
  - `*DAMPING_PART_STIFFNESS` coef < 0.01이면 0.01로 보정 (KooDynaAdvancedModification.py:1894-1907)
  - 이후 `*DATABASE` 출력 설정 (KooDynaAdvancedModification.py:1909~)

### 4.7 출력

별도의 `_skip_default_write` 플래그가 설정되지 않으므로, 모드 처리 후 기본 경로의 `WriteModifiedFile`이 호출되어 수정된 모델이 기록된다(파일명 접미사 `_wc`, KooMeshModifier.py:2814-2815, 2880-2888). 출력 모델에는 보간된 `*DEFINE_CURVE`와 `*BOUNDARY_PRESCRIBED_MOTION_NODE`, 갱신된 `*CONTROL`/`*DATABASE`가 포함된다.

---

## 5. 주의사항·한계

- **전용 예제 부재**: `Examples/` 및 소스 트리에 WEAK_COUPLING 입력 예제가 없다. 3절 입력 형식은 파서 코드에서 역산한 것으로, 실행 검증되지 않았다(확인 필요).
- **좌표 수집부 런타임 버그 의심(확인 필요)**: 절점 좌표를 `points[node.id] = tuple(node.x, node.y, node.z)`로 채우는데(KooDynaAdvancedModification.py:133, 140), `tuple()`은 인자를 1개(이터러블)만 받으므로 인자 3개 전달은 Python에서 `TypeError`를 유발한다. 정상 동작하려면 `tuple((node.x, node.y, node.z))` 형태여야 한다. 이 경로가 실제로 실행되면 예외가 발생할 가능성이 높아, 현재 모드의 정상 동작 여부 검증이 필요하다.
- **트리거 키워드 불일치**: 모드 등록(`weak_coupling`)과 옵션 블록(`*weakcoupling`)의 표기가 다르므로(2절), 입력 파일에서 각 표기를 정확히 사용해야 한다.
- **단방향 결합만 지원**: 외부 결과 → 현재 모델의 강제 변위 적용만 수행한다. 양방향(반력 피드백) 결합은 없다.
- **보간 정확도**: 변위는 외부 메시 절점들에 대한 k=3 IDW 보간이다(KooD3plot.py:115-128). 외부 메시 해상도/대상 절점 위치에 따라 보간 오차가 생길 수 있고, 거리가 0인 경우(`weights = 1/distances`)의 0 나눗셈 처리는 코드에 명시되어 있지 않다(확인 필요).
- **시간축 동기화**: 종료 시간/시간간격이 외부 결과의 시간 배열에서 직접 산출되므로(KooDynaAdvancedModification.py:166-167), 현재 모델의 의도한 해석 시간이 외부 결과 시간 범위로 덮어써진다.

---

## 6. 개발 현황

**부분구현 (확인 필요).**

- 근거: 디스패치(KooMeshModifier.py:2813-2815), 옵션 파서(KooMeshModifier.py:1581-1615), 핵심 로직(KooDynaAdvancedModification.py:109-168)이 모두 구현되어 있어 기능 골격은 완성되어 있다.
- 그러나 (1) 좌표 수집부의 `tuple(...)` 호출이 런타임 예외를 유발할 것으로 의심되고(KooDynaAdvancedModification.py:133, 140), (2) 전용 예제/실행 검증 자료가 전혀 없어, 실제 end-to-end 동작은 검증되지 않았다. 따라서 "구현됨"이 아니라 "부분구현 + 확인 필요"로 분류한다.
