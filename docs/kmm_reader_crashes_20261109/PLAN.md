<!-- KMM 리더 크래시 묶음 — 계획 -->
# 계획 — KMM 리더 크래시 묶음 (2026-11-09)

## 배경
누적 체인 묶음(v135)의 말뭉치 대조에서, 실제 덱 6개가 고치기 전·후 모두 rc 1 로 죽었다(이번 수정과 무관한 기존 결함). 사용자는 11-09 에 「찾은 결함 셋 고치기」 를 골랐다. 배포는 고친 뒤 다시 묻는다.

## 무엇을 고치나
| 번호 | 결함 | 고치는 방향 |
|---|---|---|
| R1 | *INITIAL_VELOCITY 리더(KooDynaKeyword InitialVelocity.parse)가 NSIDEX 칸이 공백 10자일 때 `int()` 로 죽는다(웹 자동화 taylor_A_dump.k) | `_whole_int` 로 읽고 빈 칸은 0, 카드 3 은 있을 때만 |
| R2 | *DATABASE_* 리더(KooDynaDatabase.SetDatabasefromDyna)가 `1.0000-06` 같은 Fortran 지수(E 없음)에서 `float()` 로 죽는다(taylor_A.k) | 함수 안 `float()`·`int()` 를 KooDynaFloat·KooDynaInt 로(빈 칸 처리는 이미 앞에서 한다) |
| R3 | *LOAD_SEGMENT_SET(_ID)(KooLoad.AddLoadfromDyna)가 빈 SF·AT 칸에서 `float('')` 로 죽는다(KooRemapper 회귀 덱 ref.k·out.k) | KooDynaInt·KooDynaFloat, R16 기본값 SF 1.0·AT 0.0 |
| R4 | 같은 데이터베이스 함수의 첫 조건이 `"DATABASE_RBDOUT"`(`*` 없음)이라 *DATABASE_RBDOUT 이 그 갈래에 들지 못한다 — 읽은 것으로 표시만 되고 출력에서 빠지는지 확인 | 확인되면 `*` 를 넣는다 |

## 검증
- 아는 불량 먼저: 작은 덱으로 넷 다 지금 소스에서 실패(죽음·빠짐)를 확인한 뒤 고친다. 말뭉치에서 죽던 실제 덱 6개가 rc 0 이 되는지도 본다.
- 회귀: tests/ 전체(누적 체인 묶음과 같은 실행기), 말뭉치 대조(강체벽 없는 덱 바이트 같음).
