# DEFORMABLE_TO_RIGID 실사용 가이드 (v109+, 2026-10-06)

`deformable_to_rigid` 로 전각도 낙하의 비행 구간을 강체화하려면 **게이트 3개를 통과**해야 하고,
접촉 구성을 **원본 GENERAL 과 같게 유지**해야 한다. v109 부터 전부 옵션으로 된다.

## 1. 카드가 생기는 조건 — 게이트 3개

셋 중 하나라도 걸리면 D2R 카드가 **0장**이고 경고가 없다.

| 게이트 | 통과 조건 | 이유 |
|---|---|---|
| `include_wall_in_general` | **false** | true 면 바닥판이 GENERAL 에 포함돼 별도 접촉이 없고 `dropContactCID=None` |
| `drop_surface.type` | **Plane / PlaneGraded / PlanewithRoughness** | `RigidWall` 은 바닥판 파트가 없어 접촉 CID 가 안 생긴다 |
| `deformable_to_rigid` | true 또는 dict | |

확인은 한 줄이다.
```bash
grep -c '^\*DEFORMABLE_TO_RIGID_AUTOMATIC' DropSet.k     # 2 여야 한다 (D2R·R2D 쌍)
```

## 2. 접촉 구성 — 쪼개지지 않게

**쪼개짐의 원인은 `convert_general_to_single_surface`(기본 true) 다.** `include_wall_in_general=false`
자체가 쪼개는 것이 아니다. 실측(2026-10-06, 원본 GENERAL `FS=0.20 FD=0.15 VDC=30 SOFT=1 SBOPT=2 DEPTH=0`):

| 설정 | 내부 | 바닥판 | 바닥판 FS/FD/VDC | SOFT/SBOPT/DEPTH |
|---|---|---|---|---|
| 기본 (`convertToSS: true`) | SINGLE_SURFACE | S2S | 0.3/0.2/**10** 🔴 | 2/3/35 🔴 |
| `convert_general_to_single_surface: false` | **GENERAL** | GENERAL | 0.2/0.15/30 ✓ | 1/0/0 ✓ |
| + `DropContact.InheritGeneral,True` | GENERAL | GENERAL | ✓ | ✓ + MAXPAR·BSORT 까지 |

**권장 설정** — GENERAL 유지 + 상속.
```json
"simulation_params": {
  "convert_general_to_single_surface": false,
  "drop_contact": { "InheritGeneral": true },
  "drop_surface": { "type": "Plane", "size": [300,300,20], "mesh": [30,30,2],
                    "deformable_to_rigid": true }
}
```
이러면 beam/shell-edge 접촉(GENERAL 만 잡는 것)도 **그대로 유지**된다.

바닥판만 S2S 로 쓰고 싶으면 `"Type": "SurfaceToSurface"` 를 추가한다(조합 C).
내부 GENERAL(MSID=0 단면)과 바닥판(MSTYP=3 양면)은 대상이 겹치지 않는다 — 중복계산이 아니다.

## 3. 상속 우선순위

`drop_contact 명시값` > `원본 GENERAL`(InheritGeneral 시) > `하드코딩 기본값`

🔴 `robust_contact: true` 면 **SOFT=2·DEPTH=3 강제가 상속을 이긴다**. segfault·관통 방지가 의도된
동작이기 때문이다. 나머지 필드(MAXPAR·BSORT·SBOPT·SOFSCL 등)는 상속된다.

## 4. D2R 세부 필드

v109 부터 8개가 열렸다. 미지정 시 예전 리터럴이 기본값이라 회귀가 없다.

```json
"deformable_to_rigid": {
  "time1": 2.0e-3,      "time2": 1.0e20,     "time3": 1.0e-3,
  "nrbf": 0, "ncsf": 0, "rwf": 0, "dtmax": 0.0, "offset": 0.0
}
```
KMM 옵션파일로는 `D2RTime1,…` `D2RTime3,…` `D2RDtmax,…` 등.

| 필드 | 의미 | 메모 |
|---|---|---|
| `time1` | 전환 검사 시작 시각 | 0 이면 처음부터 |
| `time2` | 전환 검사 종료 시각 | 1e20 = 무제한 |
| `time3` | **전환 간 최소 간격** | 0 이면 채터. 1e-3 이상 권장 |
| `dtmax` | 강체 전환 시 최대 dt | |

🔴 **v109 이전 바이너리는 `time1·time3·dtmax·offset` 의 0.05 미만 값을 `0.0` 으로 기록했다**
(writer 포맷 `%10.1f`). 그 버전으로 TIME3=1e-3 을 줬다면 덱엔 0.0 이 들어갔다.
`grep -A2 DEFORMABLE_TO_RIGID DropSet.k` 로 반드시 확인할 것.

`swset·code·relsw·paired·entno` 는 쌍 스위치 메커니즘이라 열지 않았다(자동).

## 5. 트리거 신뢰도 — 바닥판 접촉 대상

D2R/R2D 전환은 **바닥판 접촉(`entno`)의 접촉력**으로 결정된다. 그 접촉의 slave 는 기본적으로
bbox 외곽 10% 마진으로 **자동 선별**된다. 자세에 따라 실제로 닿는 파트가 빠지면 전환이 늦거나
안 일어난다.
```json
"drop_contact": { "Scope": "All" }
```
로 전 파트를 대상으로 하면 안전하다. 내부/바닥판은 구조적으로 겹치지 않으므로 All 로 둬도
중복계산은 없다.

## 6. 생성 카드의 의미

```
SWSET 20  code 4  relsw 10  paired  1  D2R=전파트 : 접촉력 !=0 → 0 일 때 변형체→강체 (바운싱 시작)
SWSET 10  code 2  relsw 20  paired -1  R2D=전파트 : 접촉력 0 → !=0 일 때 강체→변형체 (재충돌 직전)
```
즉 **비행 중 강체, 충돌 중 변형체** 가 의도다. 현장에서 반대로 관측됐다면 `code/relsw` 재검증이
필요하다 — 선행 기록은 다른 카드였을 수 있다.

## 7. 검증 절상 (짧은 런으로)

1. 덱: D2R 카드 2장, `*HOURGLASS` 개수 보존, `grep -A2` 로 TIME 값 확인
2. 접촉: `python3 -c` 로 OptCardA·FS/FD/VDC 가 원본 GENERAL 과 같은지 (tests/test_optcarda_inherit.py 의 optcards() 재사용)
3. 4 ms 런: 에너지비 1.0±0.1, 음의체적 0, 전환 횟수 한 자릿수
4. 통과하면 `MRB`·CNRB 충돌(`Error 30164`) 확인

## 8. DR(dynamic relaxation) 기반 전각도 낙하와의 관계

`DropAttitude` 는 **모델을 회전시키지 않는다** — 바닥판 법선·속도·각속도를 역회전시킨다
(실측: 자세 (0,0) vs (45,30) 에서 모델 절점 좌표 0개 변경, 바닥판 절점 2883개 변경).
따라서 DR 로 얻은 `*INITIAL_STRESS_SOLID` 는 **텐서 회전 없이** 전 자세에 그대로 유효하다.
DR 과 D2R 은 서로 독립이라 함께 써도 충돌하지 않는다.
