<!-- KMM·KCR 남은 결함 묶음 — 체크리스트 -->
# 체크리스트 — KMM·KCR 남은 결함 묶음 (2026-11-21)

각 줄: 아는 불량 먼저(옛 소스에서 실패) → 수정 → 회귀.

## 준비
- [x] 기록 재조사(docs·메모리)·옆 세션 문의·옛 소스 트리(44b1067) 준비
- [x] 재현 탐침 1·2차, 실제 덱 3450개 블록 모양 조사, 접붙이기 감사
- [x] 계획·체크리스트·결정 기록

## 가. 조용한 소실·틀린 값
- [x] A1 덱 글 병합(제어·DB 선택 카드·끝 칸) — KooDeckEcho, tests/test_remaining_control_database.py(옛 소스 24건 실패), 말뭉치 차이 전부 설명
- [x] A2 *DATABASE_BINARY_INTFOR 카드 덮어쓰기 + INTFOR_FILE 크래시 둘(이름 TypeError·카드 2c IndexError)
- [x] A3 *CONTROL_CONTACT 3~5장 되돌림·1장 죽음(+ 한 장짜리 *DATABASE_EXTENT_BINARY 죽음)
- [x] A4 *CONTROL_SOLID 카드 2·3
- [x] A5 한 키워드 아래 여러 개체 — 평범한 꼴 나누기, _ID·_TITLE·나머지는 🔴 rc 3, NODAL_FORCE_GROUP 매니저(새로 찾음). tests/test_remaining_multi_entity.py(옛 31건 실패)
- [x] A6 *RIGIDWALL_PLANAR 두 벽·3줄 오독
- [x] A7 *LOAD_SEGMENT(_ID)·_SET(_ID) + 하중 ID 겹침 덮어쓰기(새로 찾음). tests/test_remaining_load_segment.py(옛 4건 실패)
- [x] A8 *PARAMETER_EXPRESSION 의미 — 정수·실수, R16 함수, 단항 마이너스, 이어지는 줄, -&·^ 치환. tests/test_remaining_parameter.py(옛 18건 실패), 실제 덱 26개 중 값 바뀜 5개 = 예전 평가 실패(aint)
- [x] A9 재질 기록기 유효숫자 — KooMaterial 108곳 _e10·_f10_3(4자리로 담기는 값은 바이트 그대로)
- [x] A10 Fast DROP 접촉 번호 누적(접촉·초기 조건 maxid 캐시·복원)
- [x] A11 D2R·R2D 목록의 MAT_RIGID 파트
- [x] A12 IMPORT_MERGE_K 침식 빈 칸 대 0(카드 3 의 0 도 기본값)
- [x] A13 IMPORT_MERGE_K SSTYP 7 가지 접촉(옮기지 않고 🔴 rc 3)
- [x] A14 TRANSFORM 좌표 카드 알림(rc 0)
- [x] A15 없는 인클루드 — 🔴 + 주 출력·MERGE_K 에 *INCLUDE 줄 원문(rc 0)

## 나. 올바른 입력에서 죽음
- [x] B1 *ELEMENT_BEAM 끝 빈 줄
- [x] B2 PART_VALIDATION_SPLIT + 파트 덱에 파트 재료가 빠지던 것(새로 찾음)
- [x] B3 DROP_ATTITUDE 속도 키(없으면 0)
- [x] B4 읽기 권한 없는 인클루드(🔴 + rc 1)
- [x] B5 파트 지정 DWI 원통 충격체(2단·4값. 3단은 원래 미지원 — 원인 문구)
- [x] B6 ConvertSolidtoSolidwithSlack — 표본 수·빠진 줄. tests/test_remaining_crashes.py(옛 13건 실패)
- [x] B7 처방 운동 카드 3 — 카드 1 뒤 원문 그대로. tests/test_remaining_modes.py(패치 전 11건 실패), 기존 r4 단언 바꿈

## 다. KooChainRun
- [x] C1 `--sequential --nodes` > DOE 수
- [x] C2 `--sequential` 뒤 rerun 중복 제출
- [x] C3 `rerun --does` 중복
- [x] C4 jobs.json 없는 rerun + sbatch 실패 종료 코드 1(조사 「확인 필요」 줄). tests/test_remaining_kcr.py(옛 6건 실패) — 7b3f5cc

## 라. 탐침 뒤 정하는 것
- [x] 남은 탐침·코드 확인 → 표에 올리거나 분류해 context-notes 에 적기(27~32: 키워드 이름 하이픈·빗금, gmsh rc 1, DWI 재질 물려받기, 빈 절점 셋 알림, 원문 관성 알림, 진동 부피). tests/test_remaining_probes.py(옛 5건 실패)

## 바. 적대 리뷰 반영(2026-11-22, review/adversarial_review.md)
- [x] F1 빈 카드 3 — 카드 3 은 카드 1 바로 다음 줄(빈 줄도 카드 3). 예전엔 빈 줄을 버린 뒤 다음 조건 카드를 먹었다(rc 0)
- [x] F2 카드 3 을 칸으로 — LRB·NODE1·NODE2 는 객체(IMPORT_MERGE_K 를 따라감), OFFSET1·2 는 TRANSFORM 평행 이동·DROP 원점 이동을 따라감, 회전·거울·배율은 🔴 rc 3
- [x] F3 DWI 물려받기는 E·ρ 가 양수일 때만 + 재사용 재질 번호(DWI·원통·벽 13곳)가 원문 재질이면 번호만, 덱에 없으면 🔴 rc 1(예전 KeyError)
- [x] F4 *LOAD_SEGMENT_SET_ID — ID 카드 하나 + 카드 여럿
- [x] F5 빈(기본값) 카드로 끝나는 마지막 개체 나누기
- [x] F6 CPINLSDNR — 소문자 이름, 여럿이면 마지막 것
- [x] F7 없는 인클루드 — RIGID_DROP_ENDTIME 이 「질량 영향 없음」이 아니라 「읽지 못함」으로
- [x] 참고 A8 — 정수 나눗셈 버림·단항 마이너스 고쳐 쓰기를 한 줄 알림
- [x] 43⑤ 다시 — DROP 은 모델을 돌리지 않는다(바닥판·속도를 돌린다): 원문 *_INERTIA 무게중심을 원점 이동만큼 옮기고 알림 문구 바로잡기
- [x] ELASTIC_TO_RIGID 공유 MID 가 원문 재질이면 KeyError(KooMeshModifier) — 실제로는 원문 재질 파트가 하나라도 있으면 AttributeError 였다
- [x] 판정: tests/test_remaining_review.py(22건 — 고치기 전 판 21건·옛 판 20건 실패, 지금 모두 통과), context-notes 34~41, 매뉴얼(TRANSFORM·TRANSLATION_DOE·PART_LOCATION_DOE·IMPORT_MERGE_K·DROP_ATTITUDE·DROP_WEIGHT_IMPACT_TEST·ELASTIC_TO_RIGID)

## 마무리
- [x] tests/ 전체 회귀 — 1차 70/70(runs/final_suite), 리뷰 반영 뒤 2차 70/71(runs/final_suite2) + 기대값을 R16 에 맞춘 test_remaining_multi_entity 따로 통과
- [x] 말뭉치 25개 덱 옛 소스 대조(runs/corpus_final — 다른 곳은 모두 설명된 종류: INTFOR·D3THDT·CONTROL_SOLID·CONTACT·SHELL·EXTENT_BINARY 카드 3 덱 원문, 키워드 이름 *MAT_SIMPLIFIED_RUBBER/FOAM·*ALE_MULTI-MATERIAL_GROUP. 08·09 는 옛·새 모두 rc 1)
  - 리뷰 반영 뒤 2차(runs/corpus_final2, 1348ccc): 1차 출력과 25개 덱 모두 바이트 같음, 개체 대조 빠짐 없음
- [x] 접붙이기 감사 다시(문제 0) — 실제 손실 0. 도구가 센 9개 모양은 0 뿐인 끝 카드(설계)·8칸 폭 카드·빈 줄 낀 예제(context-notes 33)
- [x] 전 덱 입력·출력 개체 대조(entity_audit — 출력 있는 23개 모두 빠짐 없음)
- [x] 적대 리뷰(7건 F1~F7 — 바. 절에서 모두 반영)
- [x] 메모리·문서 갱신(낡은 기록 정리 포함 — 셸 THICKNESS·PART.secid 「미수정」 표기 정리)
- [x] 사용자 승인 뒤 빌드 → 굽기 → 헤드 교체 — Pre v141(SIF 9b81405b, KMM dd11a1cf·KCR 1170561e·KooRemapper 066e21a3, tar v141), 헤드 /opt 11-22 23:19 교체(v140 백업 _backup_20261122_231909). 컴파일본·SIF 판정 통과. Drive·메일은 포털 요청(cae00 라운드)으로 보류
