<!-- KMM TSHELL 단면·TIED 접촉 두께 보존 계획 -->
# KMM TSHELL 단면·TIED 두께 보존 계획 (2026-11-03)

## 왜
- 다른 세션(H8·H9 캠페인)의 보고다. 원본 덱의 FPCB *SECTION_TSHELL(ELFORM 3·SHRF 0.8333·NIP 5)이 KMM 을 거치면 DropSet.k 에서 ELFORM 1·SHRF 1.0·NIP 2·PROPT 1(LS-DYNA 기본값)로 바뀐다. 지금은 캠페인 래퍼가 LS-DYNA 직전에 그 줄을 되돌리고 있다.
- 사용자 지시는 "위 내용도 수정하고 배포하자" 다. TIED 두께는 "왜 로버스트 컨택인데 덱값을 안쓴느건데?" 라고 물으셨고, 근거를 들은 뒤 "고친다 — 덱 값 보존 (Recommended)" 를 고르셨다.

## 원인(소스 확인)
- **TSHELL.** KooSection.py 의 KooSectionManager 가 *SECTION_TSHELL·*SECTION_TSHELL_TITLE 을 읽을 때 칸 값을 지역 변수로만 읽고 단면 객체에 넣지 않는다. 그래서 생성자 기본값이 남는다. 게다가 PROPT 를 빠뜨려 QR·ICOMP·TSHEAR 를 한 칸씩 밀려 읽는다. 각도 카드(ICOMP=1)를 읽을지 판단하는 조건도 틀린 칸을 본다.
  - R16 카드 1 은 SECID·ELFORM(I,1)·SHRF(F,1.0)·NIP(I,2)·PROPT(I,1)·QR(F,0.0)·ICOMP(I,0)·TSHEAR(I,0) 이다. ICOMP=1 이면 각도 NIP 개를 카드마다 8개씩 쓴다.
- **TIED.** DROP_ATTITUDE 의 RobustContact 는 TiedOptions 에 SAST·SBST 가 없으면 모든 TIED 접촉의 SST·MST 를 0.005 로 바꾼다(3d3f50c, 근거 기록 없음, help 에 없음).
  - R16 접촉 일반 주의 4 의 묶기 기준은 δ = max(0.6×(두 두께 합), 0.05×세그먼트 최소 대각선)이다. 셸 두께를 0.005 로 덮으면 중면이 떨어진 셸 TIED 가 안 묶일 수 있다.
  - 값에 단위가 없다. mm 덱에서는 사실상 0 이고, m 덱에서는 5 mm 라 거꾸로 과잉 묶기가 된다.
  - SAST·SBST 는 셸·빔에만 적용되므로 솔리드·TSHELL 에는 영향이 없다.

## 무엇을
1. TSHELL 단면은 덱 값 그대로 쓴다.
   - 읽기는 R16 칸 차례대로 읽어 단면 객체에 넣는다. 각도는 ICOMP=1 일 때 NIP 개만 읽는다.
   - 쓰기는 실수 칸(SHRF·QR·각도)을 _real10 으로 써 값 손실이 없게 한다.
2. TIED 두께는 덱 값을 보존한다.
   - TiedOptions 에 SAST·SBST(SST·MST)를 줄 때만 바꾸고, 바꿀 때는 로그에 남긴다. 줄이 없으면 덱 값 그대로다.
   - help 의 DROP_ATTITUDE TiedOptions 설명에 이 점을 적는다.

## 성공 기준
- 아는 불량부터 본다. 새 시험이 지금 코드(2762399 다음 HEAD)에서 실패해야 한다.
  - TSHELL 시험: 출력 단면이 기본값이다.
  - TIED 시험: RobustContact 에서 SST·MST 가 0.005 가 된다.
- 그다음 TRANSFORM·DROP_ATTITUDE(DropSet.k) 두 경로에서 덱 값이 보존돼야 한다. ICOMP=1 각도 NIP 개, TiedOptions 로 준 값이 반영되는지도 본다.
- 기존 시험 전부와 말뭉치(지난 말뭉치 + TSHELL·TIED 덱)가 통과해야 한다. 바뀌는 것은 TSHELL 단면 줄과 RobustContact TIED 두께뿐이어야 한다.
- 적대 리뷰를 한 번 돌린다.
- 운영 배포는 다음 순서다. 굽기 전에 헤드·compute-node-images sha 와 마지막 tar 번호를 먼저 확인한다(10-28 사건).
  - 빌드 → 컴파일본 e2e → SIF(v129 예정) → compute-node-images·tar·Drive·메일 → SIF e2e → 헤드 /opt(하드 링크 백업)
  - 노드는 VM 이 켜질 때 한다.

## 영향
- 돌고 있는 H8·H9 래퍼는 같은 줄을 원본 값으로 되돌리므로, 새 KMM 과 결과가 같다(되돌릴 것이 없어질 뿐).
- RobustContact 로 돈 낙하 중 셸 TIED 가 있던 것은 묶기 거리가 덱 설계대로(δ1 = 0.6×두께 합) 돌아온다. 결과가 바뀔 수 있다.
