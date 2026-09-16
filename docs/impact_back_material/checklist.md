# 체크리스트
- [x] 재현 (공식 예제 2종, 실제 생성 config)
- [x] 러너 수정
- [x] 단위 시험 `tests/test_impact_cylinder_back_material.py`
- [x] HEAD 대비 바이트 동일 (back 재질 없는 경우)
- [x] KMM e2e — 생성 덱 질량
- [x] 문서 (partial_impact.md, DROP_WEIGHT_IMPACT_TEST.md)
- [x] 커밋(921a29d·2b3801f·3748cab) · KooChainRun 빌드 · SIF v94 · node001 배포
- [x] 배포 바이너리 잡 e2e (1141, node001): 계산노드 생성 KMM 입력·덱 모두 back 6.57e-09
      잡 자체는 LS-DYNA 라이선스(MPPDYNA 키 없음 + 네트워크 서버 무응답)로 초기화 단계 종료 — 수정과 무관
