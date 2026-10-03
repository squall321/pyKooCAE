# 바닥판 접촉 — GENERAL 상속 + 유형 선택 계획 (2026-10-03)

## 신고 2건

① `IncludeWallInGeneral=false` 로 D2R 을 쓰면 AUTOMATIC_GENERAL 이
   SINGLE_SURFACE + SURFACE_TO_SURFACE 로 바뀌면서 **옵션이 완전 다른 값으로 리셋된다.**
② **AUTOMATIC_GENERAL(벽 빼고) + SURFACE_TO_SURFACE(벽 세트)** 조합이 가능한가.

## 조사 결과

### ① 사실이다 — 단, 리셋되는 것은 바닥판 쪽만

| 생성물 | 원본 GENERAL 상속 |
|---|---|
| SINGLE_SURFACE (내부, `convertToSS=true`) | **상속함** — FS·FD·DC·VC·VDC·PENCHK·BT·DT·SFS·SFM·SST·MST·SFST·SFMT·FSF·VSF·SPR·MPR·SBOXID + OptCard B~F |
| SURFACE_TO_SURFACE (바닥판, `convertToSS=true`) | ❌ **전부 `drop_contact.get(..., 하드코딩)`** |
| Internal_GENERAL / DropSurface_GENERAL (`convertToSS=false`+D2R) | 상속함 |

즉 **기본 경로의 바닥판만 상속이 빠져 일관성이 없다.** 예: GENERAL 의 VDC 가 0 이어도
바닥판은 `drop_contact.get("VDC", 10.0)` 으로 10 이 된다.
`BT`·`DT` 는 `0.00` / `"1.0000E+20"` 으로 **하드코딩**이라 옵션조차 없다.

부수: SINGLE_SURFACE 변환이 OptCard B~F 는 `if contact_g.OptCardB:` 로 보존하는데
**OptCardA 만 무조건 덮어쓴다**. 단 SOFT=2·DEPTH 강제는 robust_contact 의 의도된 동작이라
([[project-robust-contact-plan]]) 건드리면 그 기능이 깨진다 → 이번 범위 밖.

### ② 가능하다 — 지금은 없는 네 번째 조합

| 조합 | 내부 | 바닥판 | 현재 |
|---|---|---|---|
| A | SINGLE_SURFACE | S2S | ✅ 기본 |
| B | AUTOMATIC_GENERAL | AUTOMATIC_GENERAL | ✅ `convertToSS=false`+D2R |
| C | AUTOMATIC_GENERAL | **S2S** | ❌ 요청 |

B 경로가 이미 내부 GENERAL 을 바닥판 제외 PartSet 으로 재생성하고 외곽 파트 PartSet
(`DropContact_OuterParts`)도 만들어 두므로, S2S 에 넘길 SSID(외곽 PartSet)·MSID(바닥판)가
준비돼 있다. A 경로의 S2S 도 같은 형태(SSTYP=2 PartSet, MSTYP=3 Part)다.
D2R 도 무영향 — `dropContactCID` 에 S2S 의 cid 를 넣으면 `entno` 가 그것을 가리키고,
접촉력 기반 전환(code=4/2)은 접촉 종류와 무관하다.

## 설계 (확정)

둘 다 **명시 옵션**. 기본값은 현행 → 회귀 0.

```
simulation_params:
  convert_general_to_single_surface: false
  drop_contact:
    type: surface_to_surface        # 기본 general. convertToSS=false 일 때만 의미
    inherit_general_contact: true   # 기본 false
```

KMM 옵션파일 줄 (DropAttitude 블록).
```
DropContactType,SurfaceToSurface
InheritGeneralContact,True
```

### 값 우선순위 (inherit 켠 경우)
`drop_contact 명시값` > `원본 GENERAL 값` > `하드코딩 기본값`

사용자가 `drop_contact` 에 준 값은 항상 이긴다. 안 준 필드만 GENERAL 을 따른다.
inherit 를 끄면 지금과 동일하게 `drop_contact > 하드코딩`.

## 🔴 파서 부분일치 순서

`"dropcontacttype"` 은 기존 `"dropcontact"` 류 키에 가로채일 수 있다.
`"inheritgeneralcontact"` 는 `"includewallingeneral"` 등과 무관하나 확인 필요.
→ [[project-dtmin-erosion-divergence]] 교훈대로 **삽입 전 충돌 전수 검사**하고
신규 키를 기존 키보다 **앞**에 둔다. 시험이 위치를 단언한다.

## 단계

- P0 충돌 전수 검사 + 재현 고정 시험 (A/B/C 3조합 × inherit on/off)
- P1 파서 키 2개 (충돌 검사 결과에 따라 위치 결정)
- P2 바닥판 S2S 값 해석 — 우선순위 3단 적용
- P3 조합 C 생성 경로 (B 의 바닥판만 S2S 로)
- P4 회귀: 기본 경로(A, inherit off) 덱 **바이트 동일**, 기존 스위트 통과
- P5 빌드 → 배포본 e2e → SIF → 메일 (D2R·Hourglass 수정과 묶음)
