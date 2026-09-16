# 결정 노트

## 왜 back 단 값이 최상위보다 우선인가
back 단은 '이 단의 재질' 이라는 뜻이 명확하고, 최상위 `impact.density` 는 원래 구·단일 형상 충격추용이다.
둘 다 있고 다르면 더 구체적인 쪽을 쓰고 경고한다. 조용히 한쪽을 버리는 게 이번 결함의 본질이었다.

## 왜 KMM 에 `ImpactorBack` 키를 새로 만들지 않는가
KMM 파서는 `"densityimpactor" in 줄` 부분 문자열 비교라 `DensityImpactorBack,…` 이 이미 back 으로 들어간다.
동작이 같은 분기를 추가하면 KMM 재빌드(수십 분)만 늘어난다. 문서에 매핑을 명시한다.

## 왜 덱 파트 이름을 `ImpactorBack` 으로 바꾸지 않는가
후처리(impact report payload, energy flow)가 `Impactor` 라벨을 쓴다. 이름 변경은 소비자를 깬다.
