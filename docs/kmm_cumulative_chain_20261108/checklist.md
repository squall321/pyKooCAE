<!-- KMM 누적 체인 결함 묶음 체크리스트 -->
# 체크리스트 — KMM 누적 체인 결함 묶음 (2026-11-08)

- [x] 조사 — C1·C2·C3 원인 자리 확인(코드 읽기), 라이선스 상태 확인(10-16 부터 만료 그대로)
- [x] kooomnidropanalyzer-43 과 파일 겹침 확인(그쪽은 이 파일들 고칠 계획 없음)
- [x] 사용자 결정 — 범위 = 이어서 하는 해석에 닿는 것만, S2 = 멈추고 알림(rc 1), 검증 뒤 배포까지
- [ ] 아는 불량 기준 — 지금 main 으로 2단계 체인 덱 만들기(낙하 RigidWall·충격 DampingSpring·OutsideRigid·IncludeWallInGeneral)
- [ ] 새 시험 작성 → 지금 main 에서 실패 확인
- [ ] C1 강체벽 이름표 + DTI *RemoveRigidWallbyID + DROP 바닥 벽 번호 적기(단일·Fast)
- [ ] C2 DWI 장치 전부 지우기 + RemovePart 가 그 파트를 가리키는 카드 정리
- [ ] C3 IncludeWallInGeneral 새 바닥판을 전체 접촉 범위에 넣기 + 파트 묶음 번호 정리
- [ ] W1 강체벽 기록기(종류·제목·정밀도·BIRTH·번호 없는 FLAT_DISPLAY)
- [ ] W2 강체벽 정의 차례 하나로
- [ ] W3 덱 사용자 강체벽 이동 — 조사 뒤 확정
- [ ] S1 OutsideRigid*·byPart 의 *INTERFACE_SPRINGBACK_LSDYNA
- [ ] S2 시편을 잘라 낸 충격 — 사용자 결정대로
- [ ] 회귀 — 기존 시험·43 의 시험(DROP_ATTITUDE 를 건드렸으면 e2e b·c)·말뭉치 비교
- [ ] 적대 리뷰와 고침
- [ ] (배포까지면) 빌드·컴파일본 시험 → SIF·tar·Drive·메일 → 헤드 /opt(확인) → push → 알림·메모리
