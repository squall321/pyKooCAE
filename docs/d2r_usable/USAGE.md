# DEFORMABLE_TO_RIGID 실사용 가이드 (v111+, 2026-10-07 개정)

> 🔴 **v110 이하는 D2R 이 반대로 동작한다**(충돌 중 강체·비행 중 변형체, 현장 §9 #8 관측이 맞았다).
> 또 `convert_general_to_single_surface: false` 에서 바닥판이 GENERAL 이면 스위치가 아예 안 켜진다(매뉴얼 Remark 1).
> 둘 다 v111 에서 고쳤다. 아래는 v111 기준.

`deformable_to_rigid` 로 전각도 낙하의 비행 구간을 강체화하려면 **게이트 3개를 통과**해야 하고,
접촉 구성을 **원본 GENERAL 과 같게 유지**해야 한다. v109 부터 전부 옵션으로 된다.

## 1. 카드가 생기는 조건 — 게이트 3개

셋 중 하나라도 걸리면 D2R 카드가 **0장**이다. v111 부터는 KMM 로그에 `🔴 D2R_SKIPPED` 가 찍힌다.

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

🔴 **매뉴얼 Remark 1 — 자동 파트 전환은 S2S·N2S 접촉만 켤 수 있다.** 바닥판이 AUTOMATIC_GENERAL
이면 D2R 카드가 있어도 전환이 한 번도 일어나지 않는다. 그래서 D2R 에서 쓸 수 있는 구성은
**내부 GENERAL + 바닥판 S2S(조합 C)** 뿐이다. v111 부터 `deformable_to_rigid` 가 켜져 있고
`Type` 을 안 주면 바닥판을 S2S 로 자동 선택한다(`D2R_FLOOR_AUTO_S2S` 로그). `Type: General` 을
명시하면 `🔴 D2R_FLOOR_GENERAL` 경고가 뜨고 전환은 안 된다.

**권장 설정** — 내부 GENERAL 유지 + 바닥판 S2S + 상속.
```json
"simulation_params": {
  "convert_general_to_single_surface": false,
  "drop_contact": { "InheritGeneral": true, "Type": "SurfaceToSurface" },
  "drop_surface": { "type": "Plane", "size": [300,300,20], "mesh": [30,30,2],
                    "deformable_to_rigid": true }
}
```
키 철자는 `type` / `inherit_general` / `inherit_general_contact` / `scope` 처럼 대소문자·밑줄을 바꿔
써도 된다(v111 부터 정규화, 로그에 `DropContact.type → Type 로 해석`). `simulation_params` 최상위
`"inherit_general_contact": true` 도 받는다.

내부 GENERAL 은 beam/shell-edge 접촉을 **그대로 유지**하고, 바닥판 S2S(MSTYP=3 양면)와 대상이
겹치지 않는다 — 중복계산이 아니다. 바닥판 S2S 의 FS/FD/DC/VC/VDC/PENCHK/BT/DT/SFS… 는
`drop_contact 명시값 > 원본 GENERAL > 기본값` 이다(v110 까지는 조합 C 에서 FS~VDC 명시값이 무시됐다).

## 3. 상속 우선순위

`drop_contact 명시값` > `원본 GENERAL`(InheritGeneral 시) > `하드코딩 기본값`

🔴 `robust_contact: true` 면 **SOFT=2·DEPTH=3 강제가 상속을 이긴다**. segfault·관통 방지가 의도된
동작이기 때문이다. 나머지 필드(MAXPAR·BSORT·SBOPT·SOFSCL 등)는 상속된다.

## 4. D2R 세부 필드

v109 부터 8개가 열렸다. 미지정 시 예전 리터럴이 기본값이라 회귀가 없다.

```json
"deformable_to_rigid": {
  "time1": 2.0e-3,      "time2": 1.0e20,     "time3": 1.0e-3,
  "nrbf": 0, "ncsf": 0, "rwf": 0, "dtmax": 0.0, "offset": 0.0,
  "lrb": 0
}
```
KMM 옵션파일로는 `D2RTime1,…` `D2RTime3,…` `D2RDtmax,…` `D2RLrb,…` 등.

`lrb` (v111): 전환된 파트들을 합칠 **선도 강체 파트 ID**. 0 이면 파트마다 독립 강체가 되는데,
파트 간 CNRB 가 있으면 LS-DYNA 가 `Error 30164` 로 죽는다(현장 §9 #9). 모델의 한 파트 ID 를 주면
나머지가 그 강체에 합쳐진다. LS-DYNA 실행 검증은 라이선스 부재로 현장에서 할 것.

실수 필드는 v111 부터 손실 없이 기록된다(v110 은 `1.25e-3` 을 `1.3e-03` 으로 반올림했다).

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

## 6. 생성 카드의 의미 (v111 에서 정정)

LS-DYNA Vol I `*DEFORMABLE_TO_RIGID_AUTOMATIC` CODE 정의는 **2 = 접촉력이 0 일 때 전환, 4 = 접촉력이
비0 일 때 전환**이고, 공식 예제는 SWSET 20 code 2(D2R) + SWSET 10 code 4(R2D) 다.
```
SWSET 20  code 2  relsw 10  paired  1  D2R=전파트 : 접촉력 0  (비행 중) → 변형체→강체
SWSET 10  code 4  relsw 20  paired -1  R2D=전파트 : 접촉력 비0 (충돌)   → 강체→변형체
```
즉 **비행 중 강체, 충돌 중 변형체**.

🔴 **v110 이하(2026-03-31 커밋 6c41728 ~ v110)는 code 가 반대(D2R=4, R2D=2)로 들어가 충돌 중 강체·
비행 중 변형체였다.** 현장 §9 #8 의 관측이 맞았고, 이 문서 v109 판의 "현장 기록을 의심하라" 는
틀린 안내였다. 그 커밋의 "접촉력 변화 감지" 해석은 매뉴얼에 없다.

## 7. 검증 절상 (짧은 런으로)

1. 덱: D2R 카드 2장, `*HOURGLASS` 개수 보존, TIME 값·code 확인
   ```bash
   grep -A2 '^\*DEFORMABLE_TO_RIGID_AUTOMATIC' DropSet.k | sed -n 3p   # swset 20 → 두 번째 칸 code 가 2 여야 한다
   ```
   V0/V1/V2 덱도 같은 명령으로 보면 된다 — v110 이하 writer 는 TIME 0.05 미만을 0.0 으로 썼고 code 가 반대였다.
2. 접촉: `python3 -c` 로 OptCardA·FS/FD/VDC 가 원본 GENERAL 과 같은지 (tests/test_optcarda_inherit.py 의 optcards() 재사용)
3. 4 ms 런: 에너지비 1.0±0.1, 음의체적 0, 전환 횟수 한 자릿수
4. 통과하면 `MRB`·CNRB 충돌(`Error 30164`) 확인

## 8. DR(dynamic relaxation) 기반 전각도 낙하와의 관계

`DropAttitude` 는 **모델을 회전시키지 않는다** — 바닥판 법선·속도·각속도를 역회전시킨다
(실측: 자세 (0,0) vs (45,30) 에서 모델 절점 좌표 0개 변경, 바닥판 절점 2883개 변경).
따라서 DR 로 얻은 `*INITIAL_STRESS_SOLID` 는 **텐서 회전 없이** 전 자세에 그대로 유효하다.
DR 과 D2R 은 서로 독립이라 함께 써도 충돌하지 않는다.

🔴 **전제 (2026-10-07 감사)**
- KMM 은 `*INITIAL_STRESS_SOLID[_SET]` 만 읽고 쓴다. dynain 의 `*INITIAL_STRESS_SHELL`·`*INITIAL_STRESS_BEAM`·
  `*INITIAL_STRAIN_*` 은 파싱도 passthrough 도 없어 **KMM 왕복에서 소실**된다. 솔리드 전용 모델만
  "DR 결과를 그대로" 가 성립하고, 셸·빔(TAB_S11B 의 TIED 셸·빔 등)의 잔류응력은 다음 자세로 이월되지 않는다.
  (기존 공백, 별도 작업으로 보류 — 사용자 결정 10-07)
- `*INITIAL_STRESS_SOLID` 파서는 NHISV≤3 만 검증됐다. 이력변수가 많은 재질(탄소성·폼)의 dynain 왕복은 미검증.
- 체인의 원복(`MovetoOriginAutomatic`)은 3절점 SVD 강체변환을 **절점에만** 적용하고 응력 텐서는 돌리지 않는다.
  회전이 항등일 때만 위 결론이 성립한다. 실측에서는 항등이었으나(고정절점이 꼭짓점으로 선택됨) 일반 모델에서는 미검증.
