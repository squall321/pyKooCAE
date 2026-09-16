# 실린더 충격추 back 단 재질 누락 — 수정 계획

## 증상 (서버 보고)
"ImpactorFront·ImpactorMid·Impactor 는 있는데 ImpactorBack 슬롯이 없다 — back 재질 지정 방법이 없다."

## 원인 (재현 확정)
- KMM: 실린더 back 질량(`shapesBack`)은 **`Impactor` 파트**로 메시되고 재질은 `DensityImpactor`/
  `YoungsModulusImpactor`/`PoissonRatioImpactor` 로 받는다. 즉 슬롯은 있고 이름이 `Back` 이 아니다.
- 🔴 러너(`CumulativeScenarioRunner` IMPACT 분기): `cylinder_stages[-1]`(back) 에서 **지름·높이만 읽고
  재질을 버린다**. back 재질은 `impact` 최상위 `density`/`youngs_modulus`/`poisson_ratio` 에서만 오고,
  없으면 강철 기본값(7.85e-9 / 2.01e5 / 0.3).
- 공식 예제 `impact_cylinder_8pi.json`·`impact_cylinder_15pi.json` 은 back 단에만 재질을 적었다 →
  실제 생성 config 가 `DensityImpactor,7.85e-09`(의도 6.57e-9·6.854e-9).
- 영향: 8파이 back 질량 388 g → 464 g, 총 ≈418 g(예제 주석) → ≈493 g, **+18%**.

## 수정
1. back 단에 재질이 있으면 `*Impactor` 키로 내보낸다. 최상위 값과 다르면 back 단 우선 + 경고.
2. `poisson`/`poisson_ratio` 를 단·최상위 모두에서 받는다 (틀린 이름이 조용히 기본값이 되는 것 방지).
3. KMM·덱 파트 이름은 그대로.

## 검증
- 공식 예제 2종 → back 재질이 단 값으로 나감
- back 재질 없는 시나리오 → HEAD 대비 바이트 동일
- 충돌·별칭 단위 시험
- KMM 실행 → 생성 덱의 충격추 파트 질량을 계산해 예제 주석(≈418 g)과 대조
