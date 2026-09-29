# 컨텍스트 노트 — `*MAT_*` 키워드/페이로드 불일치

## 2026-09-29 신고 원인 가설 2건이 모두 틀렸다
신고서는 (a) `_TITLE` 분기 부재, (b) 경쟁 조건/캐시로 인한 런별 비정성을 주장했다.
최소덱으로 양쪽을 재현해 보니 둘 다 아니다.

- (a) 반증: `KooMaterial.py:1485` 에 `_TITLE` 분기가 있고, 제목+`$#`주석+데이터 구성을
  정확히 복원한다 (`mid=15 name=Epoxy_100M rho=1.3e-09 K=64.444 G0=48.333 GI=15.104 BETA=2500.0`)
- (b) 반증: 같은 덱이면 결정적으로 같은 결과. 6/2 로 갈린 것은 **덱이 달랐다**는 뜻이다.
  신고자가 "현재 덱"(2728행 `_TITLE` 로 올바름)을 "과거 런 출력"과 대조한 방법론 문제로 보인다.
  `mkmat15.py` 를 캠페인 중 수정했다면 정확히 이 그림이 된다

🔴 교훈: 신고서의 원인 가설을 그대로 받지 않는다. 증상은 신뢰하고 원인은 재현으로 확정한다.
이번 건은 요청 #1(분기 추가)을 그대로 했으면 **없는 문제를 고치고 진짜 원인은 남았을** 것이다.

## 파괴 조건은 "키워드는 bare, 페이로드는 제목 포함"
```
*MAT_VISCOELASTIC      ← _TITLE 아님
Epoxy_100M             ← 제목 줄
$# ...
        151.30000E-9 ...
```
LS-DYNA 관점으로도 잘못된 입력이다. 하지만 KMM 이 이것을 **조용히** 그럴듯한 재질로
바꿔치우고 참조 mid 를 버리는 것이 실제 피해다. [[project-a27-solid-2card-loss]] 의
개수 불변식 교훈과 같은 계열.

## 요청 #2 를 문자 그대로 하면 DROP_ATTITUDE 가 깨진다
"`AddMaterial` 의 id 0 무언 재부여 제거" 가 요청이었다. 그런데 `KooMaterial.py:1104~1125`
팩토리 5곳(`AddRigidMaterial`·`AddElasticMaterial`·`AddViscoelasticMaterial`·
`AddPlasticKinematicMaterial`·`AddCohesiveMixedModeMaterial`)이 **id=0 을 넘겨 자동부여를
의도적으로 사용**한다. 바닥판·충격추 재질이 이 경로다.

→ `AddMaterial` 불변. 가드는 **파싱 시점**(`AddMaterialfromDyna` 진입부)에 둔다.
그 자리에서 MID 비숫자는 파싱 실패밖에 될 수 없고, 자동부여 경로는 여기를 지나지 않는다.
[[feedback-protect-existing]]

## MID 검증은 선언 근거로
LS-DYNA 규격상 `*MAT_*` 카드1 필드1 은 정수 MID 다. `KooDynaInt` 의 반환값이 0인지로
판정하지 않는다 — 0 은 정상 값일 수도 있고, `KooDynaInt` 가 '2.0' 같은 실수표기를
받아주도록 이미 수정된 이력이 있다([[project-a27-solid-2card-loss]]).
필드 문자 구성으로 판정한다. [[feedback-karpathy-principles]] 의 추론 금지 원칙.

## P2 는 중단이 아니라 경고
재질 mid 집합 불변식을 중단으로 걸면 **의도적 미해석 raw 보존** 모델이 깨진다.
근거: `KooMeshImporter.py:2157` 주석("MAT_GENERAL_VISCOELASTIC 등이 출력에서 유실되는 것 방지"),
`KooMeshImporter.py:1189` 의 기존 Warning 경로. 경고로 두고 눈에 띄게 찍는다.

## 별건 — 죽은 경로의 인자 뒤바뀜
`MatViscoelasticTitle.AddMatViscoelasticTitle(self, Name, MID, RO, ...)` 인데
호출부 `KooMaterial.py:602` 는 `(self.id, self.name, self.rho, ...)` 를 넘긴다
→ `Name`←id, `MID`←name 으로 **앞 두 개가 뒤바뀜**. 다만 `AddtoDynaKeyword` 호출처가
`KooMaterial.py:1901`(MatElasticTitle용) 하나뿐이라 점탄성은 **죽은 경로**다.
실제 방출은 `GenerateDynaKeyword()`(605행)이고 정상이다. 이번 수정 범위 밖 — 기록만 남긴다.

## 회귀 증명 결과
- `DropSet.k` **바이트 동일** — `Test_kmm_preserve/config_drop.txt` 를 출력경로만 바꿔
  변경 전(.bak 복원) / 변경 후로 각각 생성해 md5 대조
- `DropSet.json` 은 `run_id` 한 필드만 다름(실행 타임스탬프). 산출물 파일 구성 동일
- 실제 덱 10개에서 MID 불변식 오탐 **0** — `MinimumModel*` 3종, ECAD PBA(재질 9개),
  conformal, `Test_kmm_preserve` 4종(raw 보존 시험덱), `Test_kmm_repro` 2종
- 시험 6종 rc=0

## 🔴 내 실수 2건 (기록)
**① 실행 중 회귀 비교를 하면서 수정본 사본을 안 남겼다.**
"변경 전" 덱을 뜨려고 작업 파일을 `.bak` 원본으로 덮어썼는데, 수정본을 따로 보관하지 않아
수정이 사라졌다. 같은 스크립트로 재적용해 복구했다.
→ 이후로는 `.bak`(원본)과 `.fixed`(수정본)를 **둘 다** 보관하고 그 사이를 오간다.

**② `git checkout -- <file>` 을 쓰려다 차단됐다.**
커밋 전 상태라 이 명령은 **수정을 영구 삭제**할 명령이었다. 자동 분류기가 막아줬다.
→ 커밋 전 수정을 되돌리는 수단으로 git 을 쓰지 않는다. 사본 복사로만 왕복한다.
