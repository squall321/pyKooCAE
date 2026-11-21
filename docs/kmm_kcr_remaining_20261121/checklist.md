<!-- KMM·KCR 남은 결함 묶음 — 체크리스트 -->
# 체크리스트 — KMM·KCR 남은 결함 묶음 (2026-11-21)

각 줄: 아는 불량 먼저(옛 소스에서 실패) → 수정 → 회귀.

## 준비
- [x] 기록 재조사(docs·메모리)·옆 세션 문의·옛 소스 트리(44b1067) 준비
- [x] 재현 탐침 1·2차, 실제 덱 3450개 블록 모양 조사, 접붙이기 감사
- [x] 계획·체크리스트·결정 기록

## 가. 조용한 소실·틀린 값
- [ ] A1 덱 글 병합(제어·DB 선택 카드·끝 칸)
- [ ] A2 *DATABASE_BINARY_INTFOR 카드 덮어쓰기
- [ ] A3 *CONTROL_CONTACT 3~5장 되돌림·1장 죽음
- [ ] A4 *CONTROL_SOLID 카드 2·3
- [ ] A5 한 키워드 아래 여러 개체
- [ ] A6 *RIGIDWALL_PLANAR 두 벽·3줄 오독
- [ ] A7 *LOAD_SEGMENT(_ID)·_SET(_ID)
- [ ] A8 *PARAMETER_EXPRESSION 의미
- [ ] A9 재질 기록기 유효숫자
- [ ] A10 Fast DROP 접촉 번호 누적
- [ ] A11 D2R·R2D 목록의 MAT_RIGID 파트
- [ ] A12 IMPORT_MERGE_K 침식 빈 칸 대 0
- [ ] A13 IMPORT_MERGE_K SSTYP 7 가지 접촉
- [ ] A14 TRANSFORM 좌표 카드 알림
- [ ] A15 없는 인클루드

## 나. 올바른 입력에서 죽음
- [ ] B1 *ELEMENT_BEAM 끝 빈 줄
- [ ] B2 PART_VALIDATION_SPLIT
- [ ] B3 DROP_ATTITUDE 속도 키
- [ ] B4 읽기 권한 없는 인클루드
- [ ] B5 파트 지정 DWI 원통 충격체
- [ ] B6 ConvertSolidtoSolidwithSlack
- [ ] B7 처방 운동 카드 3

## 다. KooChainRun
- [ ] C1 `--sequential --nodes` > DOE 수
- [ ] C2 `--sequential` 뒤 rerun 중복 제출
- [ ] C3 `rerun --does` 중복
- [ ] C4 jobs.json 없는 rerun

## 라. 탐침 뒤 정하는 것
- [ ] 남은 탐침·코드 확인 → 표에 올리거나 분류해 context-notes 에 적기

## 마무리
- [ ] tests/ 전체 회귀
- [ ] 말뭉치 25개 덱 옛 소스 대조
- [ ] 접붙이기 감사 다시(문제 0)
- [ ] 전 덱 입력·출력 개체 대조
- [ ] 적대 리뷰
- [ ] 메모리·문서 갱신(낡은 기록 정리 포함)
- [ ] 사용자 승인 뒤 빌드 → 굽기 → 헤드 교체
