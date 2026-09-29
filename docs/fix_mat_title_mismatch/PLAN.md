# `*MAT_*` 키워드/페이로드 불일치 무언 손실 수정 계획 (2026-09-29)

## 신고와 실제 원인

신고 [KooMeshModifier — `*MAT_VISCOELASTIC_TITLE` 를 간헐적으로 파괴한다] 는 원인을
"`*MAT_VISCOELASTIC` 파서에 `_TITLE` 분기가 없다" + "런마다 갈리는 경쟁 조건" 으로 봤다.
**둘 다 사실이 아니다.** 최소덱 2종으로 재현해 확정했다.

- `_TITLE` 분기는 `KooMaterial.py:1485` 에 있고 정상 동작한다
  (제목 + `$#` 주석 + 데이터 구성으로 `mid=15 name=Epoxy_100M ...` 정확히 복원)
- 같은 덱이면 **결정적으로** 재현된다. 경쟁 조건이 아니다

진짜 원인은 **입력 덱이 bare `*MAT_VISCOELASTIC` 인데 제목 줄이 남아 있는 것**이다.

```
*MAT_VISCOELASTIC          ← _TITLE 이 아닌데
Epoxy_100M                 ← 제목 줄이 있다
$#     mid        ro ...
        151.30000E-9 ...
```

## 무언 손실 연쇄 (4단계, 전부 확인됨)

1. bare 분기가 `dynaMaterial[1]`(제목 줄)을 데이터 카드로 읽는다
   → `KooDynaInt("Epoxy_100M")` = **0**, 실수 필드 전부 0
2. `name = "Viscoelastic{0}".format(0)` → `Viscoelastic0`
3. `AddMaterial` 의 `if material.id == 0: material.id = self.maxid + 1`
   → **조용히 재부여** (현장 701, 최소덱 49 = 각자의 maxid+1)
4. 원래 mid 는 등록되지 않음 → 참조 파트 전원 고아
   → LS-DYNA `Error 10157` × 참조 파트 수, `Error 10293`(G0==GI==0)

전처리는 `rc=0` 으로 끝난다. 참조 파트가 없었다면 **재질이 사라진 채 "정상 완료"** 한다.

## 설계 판단 — 신고 요청 #2 는 문자 그대로 하면 안 된다

요청 #2 는 "`AddMaterial` 의 id 0 무언 재부여 제거" 다. 그런데 `KooMaterial.py:1104~1125`
(`AddRigidMaterial`·`AddElasticMaterial`·`AddViscoelasticMaterial` 등 팩토리)가
**id=0 을 넘겨 자동부여를 의도적으로 쓴다.** 바닥판·충격추 재질이 이 경로다.
여기를 에러로 바꾸면 DROP_ATTITUDE 가 전량 깨진다.

→ `AddMaterial` 은 **건드리지 않는다.** 대신 **파싱 시점**(`AddMaterialfromDyna` 진입부)에서
막는다. 그 자리에서 MID 가 비숫자인 것은 파싱 실패밖에 될 수 없다.
자동부여 경로는 `AddMaterialfromDyna` 를 지나지 않으므로 무영향이다.

## 단계

각 단계는 검증 기준을 통과해야 다음으로 간다.

### P0. 재현 고정 — 회귀 시험
- `tests/test_mat_title_mismatch.py` — 정상덱(제목 있음)·파괴덱(bare+제목)·bare 정상덱 3종
- 검증: 현재 코드에서 파괴덱이 `Viscoelastic0` + mid 소실을 **재현**(기준선 고정),
  정상덱 2종은 통과

### P1. MID 필드 선언 기반 검증 (요청 #1·#3·#4 를 한 곳에서)
`AddMaterialfromDyna` 진입부에 가드 하나. LS-DYNA 규격상 `*MAT_*` 카드1 필드1 은 **정수 MID** 다
(추론 아님 — 선언 근거). 키워드가 `_TITLE` 이 아닌데 첫 페이로드 줄의 MID 필드에
숫자가 아닌 문자가 있으면 **즉시 에러**로 중단하고 다음을 찍는다.
- 키워드 원문, 문제 줄 원문, 그 줄이 제목으로 보인다는 지적
- `_TITLE` 을 붙이거나 제목 줄을 지우라는 구체 지시
- 검증: 파괴덱이 에러로 중단, 정상덱 2종 바이트 동일 통과

### P2. 재질 mid 집합 불변식 (요청 #2 의 취지)
임포트 후 입력 덱 raw `*MAT_*` 블록의 mid 집합과 등록된 재질 mid 집합을 대조.
🔴 **경고로 둔다(중단 아님)** — `MAT_GENERAL_VISCOELASTIC` 등 의도적 미해석 raw 보존 경로가
있어 중단시키면 기존 모델이 깨진다. 근거: `KooMeshImporter.py:2157` 주석,
`KooMeshImporter.py:1189` 의 기존 Warning.
- 검증: 파괴덱에서 "mid 15 소실" 이 로그에 뜬다. 기존 정상 모델에서 오탐 0

### P3. 회귀 증명
- 기존 DROP/IMPACT/VIBRATION/THERM 덱 **바이트 동일**
- 기존 스위트 전부 통과 (`test_layer_split`, `test_fall_gravity`,
  `test_kooremapper_chain_config`, `test_thermal_chain`, `test_cli_help`)

## 범위 밖

- `AddMatViscoelasticTitle` 의 인자 뒤바뀜(`Name`↔`MID`) — 호출처가 없는 **죽은 경로**다.
  실제 방출은 `GenerateDynaKeyword()`(605행). 별건으로 기록만 남긴다
- 신고 요청 #1(`_TITLE` 분기 추가) — 이미 있다. 불필요
- `mkmat15.py` 수정 — 신고자 소유 스크립트
