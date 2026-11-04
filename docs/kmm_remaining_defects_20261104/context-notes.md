<!-- KMM 남은 기존 결함 묶음(v131) — 결정·근거 노트 -->
# 결정 노트 — KMM 남은 기존 결함 묶음 (2026-11-04, v131)

## 결정
- **사용자(11-04).** "남은거 해결 ㄱㄱ". 질문 넷에 이렇게 답했다.
  - Post v43: 보류를 풀고 지금 main(eccde7f)으로 한 판 낸다.
  - 셸 단면 정밀도: 고친다(덱 값 그대로). 셸 덱 출력 바이트가 바뀌는 것을 받아들였다.
  - 덱 전체 LONG=Y/S: 알아보게 멈춘다(rc 1).
  - v131: 검증 뒤 배포까지.
- **범위.** v130 노트의 '이번 범위 밖으로 남긴 기존 결함' 목록과 예전 미수정분(*ELEMENT_SHELL_THICKNESS·IMPORT_MERGE_K PART.secid·NODUMP·DWI OutsideRigid 자리)이다. IMPACT 기본 치수 SI 크기 같은 설계 문제는 넣지 않았다.

## Post v43 (KooD3plotReader eccde7f)
- 11-03 사용자 '보류' 뒤 그대로였다. 그사이 a9 가 -j/--parallel-runs(eccde7f)와 실측 문서(5f8c63b)를 main 에 올려, v43·v44 로 나누려던 내용이 main 하나에 들어 있다. KooDynaErrorAnalyzer 는 c41dce48 이다.
- 빌드 시작 전에 kood3plotreader-bf·a9 에 알리고 빌드 동안 main push 를 멈춰 달라고 했다(def 가 빌드 때 main 을 --depth 1 로 clone 한다).
- 판정기 /data/koopark/Post_v43/verify_post.sh 를 v42 로 먼저 돌렸다(아는 불량). v42 는 s1_extract·koo_ontology rc 255, koo_sphere_report --parallel-runs·--yield-map 0, koo_deep_report --section-view-state-step 0, koo_deep_report.ontology import FAIL 이다. 패키지 대조기는 커밋 5abbc76 의 120 파일이 SIF 와 같다(다름 0).
- **굽기(08:4x~09:04).** /data/koopark/Post_v43/post_release_capped.sh(MemoryMax 28G·taskset 0-7)로 표준 BuildSmartTwinPostprocessorOnly.sh 를 돌렸다. RELEASE_RC 0, 최저 가용 31.5 GB 다. 빌드 중 main push 는 없었다(원격 HEAD eccde7f 그대로).
  - 헤드리스 94b98c46·GUI a6b95a76(VERSION eccde7f)이 빌드 원본·/data·compute-node-images·헤드 /opt 네 곳에서 같다. deploy_from_sif.sh 검증은 "모두 같은 판(eccde7f)" 이다.
  - tar v43 은 551,323,350 B 이고, Drive(ApptainerImages:SmartTwinPreprocessor/ — v42 와 같은 폴더)·메일 sent OK 다.
  - 헤드 /opt 는 v42 를 하드 링크 `SmartTwinPostprocessor(GUI)_backup_20261104_090503.sif`(1a6e0933·4536ea72)로 남기고 바꿨다. 노드는 down 이다.
- **판정(verify_post.sh).** 헤드리스 v43 은 s1_extract·koo_ontology rc 0, --parallel-runs·--yield-map·--section-view-state-step·--s1 이 보인다. v42 는 모두 0/rc 255 였다. unified_analyzer rc 3 설명은 유지된다. SIF 안 리포트 패키지 132 파일이 커밋 eccde7f 와 같다(헤드리스·GUI).
  - GUI 에는 s1_extract 가 없다(GUI def 에 libhdf5-dev 가 없어 build_module.sh 가 건너뜀). S1 은 헤드리스 파이프라인용이라 의도로 보이고, bf 에 확인을 청했다.
- **알림.** kood3plotreader-bf·a9 에 VERSION·sha256 을 보냈고 a9 에 verify_v43.sh(18종, 실덱 100런 읽기만)를 청했다. smarttwinmcp-c8·4c 에는 CLI 변화(s1_extract·koo_ontology·--parallel-runs·--yield-map·--section-view-state-step·post_analyze --s1·ontology.json 산출, SI 덱 CRITICAL 감소)를 알렸다.
- **틈.** v43 부터 sphere_report.sh 가 --parallel-runs 를 보고 새 사이징 공식으로 바뀐다. 워커 메모리 0.5 GB(K1)는 v131 Pre 에 들어가므로 그때까지는 워커당 2 GB 로 과다 할당이다(위험하지 않음, 대기만 길어짐).
- **a9 검증(11-04).** verify_v43.sh 16/16 ✓(v42 는 13 ✗). 네 곳 sha 를 직접 대조했고, 실덱 Test_005_Fibonacci_100(100런)에서 병렬 1패스(워커 4)·2패스 축약(시계열 60/100)·사이드카 test_dir·energy_flows_reduced·내부 키 누출 0·CWD 무오염을 확인했다. Post v43 을 닫는다.
  - 🔴 캐시 스키마 3→4 라 배포 뒤 첫 sphere 실행은 흐름 캐시를 한 번 다시 짓는다(100런 순차 35초·-j8 14초, 런 수에 비례). 둘째부터는 캐시 적중이다.
  - 사이징 틈(979런이면 6+16×2=38 GB 요청, 실측 ≈5 GB)은 노드가 모두 down 이라 지금 영향이 없다. K1 은 v131 에 넣고, 노드가 먼저 살아나면 다시 본다.

## 읽기·출력 묶음 I1~I8 (5bff0cf·38706c6·19a7e6a)
- **콤마 자유형식.** parse_whole 은 칸이 둘 이상이고 모두 20칸 이하인 숫자 카드만 콤마로 나눈다. 제목 [80]·ID+제목 [10,70] 같은 글 칸은 콤마가 글이라 그대로 둔다. 값은 칸 폭에 오른쪽으로 맞춘다.
- **덱 전체 LONG.** 사용자 결정은 '알아보게 멈춘다'. 그런데 R16 은 long=s 를 "read standard keyword input deck" 로 정한다(TN1 덱이 `*KEYWORD I10=Y LONG=S`). 그래서 LONG=Y·K 만 멈추고 S 는 표준으로 읽는다(사용자에게 알렸다). `*INCLUDE +` 와, 20칸을 못 읽는 해석 키워드의 '+' 블록도 🔴 로 멈춘다(_LONG_OK 밖).
- **접촉 선택 카드 A~F.** 예전엔 버려 덱 값이 기본값으로 바뀌었다. 이제 그대로 옮긴다 — 많은 덱의 출력이 바뀌는 것은 의도한 것(덱 값 복원)이다. ERODING 은 카드 4 가 필수라 없으면 원인을 밝혀 멈춘다.
- **I6 셸 단면 실수.** 사용자 결정 '덱 값 그대로'. 값이 10.3e 로 정확히 나타나면 예전 글자 그대로 두고(덱 바이트 유지), 아니면 _real10 이다(안 B).

## 부품 묶음 P1~P4·R1·R2 (5c79910~d4212f6)
- **P1 *PART_CONTACT.** 카드 묶음(제목·카드 2·카드 8)을 되풀이해 읽고 파트로 만든다. 3줄로 나뉘지 않는 블록이 하나라도 있으면 키워드 전체를 원문으로 둔다(ok=False) — 일부만 파트로 만들면 원문과 매니저 판이 겹친다.
- **R1·R2 (조사 중 찾음).** 원문 *PART_* 변형 PID·원문 요소 EID 를 번호 매기기에 넣지 않아 DROP 바닥판 PID 가 원문 *PART_INERTIA 7 과 겹쳤다. 시험 R1 은 처음에 바닥판 *PART 의 빈 제목 줄을 걸러 PID 를 엉뚱한 줄에서 읽어 옛 판에서도 통과했다 — 제목 줄을 거르지 않게 고친 뒤 옛 판에서 실패한다.
- **P2 두께.** 두께 카드는 I10 에서도 16칸(리더 _parse_i10_block 과 같다). N4=N3 으로 쓴 삼각형은 KMM 이 퇴화 사각형(QUAD4)으로 읽어 미러 뒤에도 절점·두께 짝이 맞는다. N4=0 삼각형(TRI3)은 KMM 이 N3 을 되풀이해 쓰므로 THIC4 는 N3 이 바뀌면 새 N3 의 두께를 따른다. PART_VALIDATION_SPLIT 의 단순 덱 기록기(KooPartValidator)는 예전처럼 두께·중간 절점 없이 쓴다(검증용 단순 덱, 범위 밖).
- **2차 셸 MIRROR (P2 중 찾음).** YZ·XZ 의 TRI6·QUAD8 중간 절점이 XY 판 순서라 다른 변에 붙었다. 시험 P2Q 는 일반 *ELEMENT_SHELL 블록도 읽어, 옛 판에서 XY 는 통과·YZ·XZ 는 실패로 결함만 짚는다.
- **P4.** 셸 단면의 사용자 카드와 같은 방식("RAW" 묶음)이다. 단면 기록기와 덤프 둘 다 원문 줄을 쓴다.
- **커밋 나누기.** git apply 가 오프셋에서 실패해, index 판과 작업 판의 difflib 묶음을 번호로 골라 hash-object·update-index 로 올리는 도구(/data/koopark/v131_probe/tools/stage_hunks2.py)를 썼다. 중간 커밋마다 문법 확인, 묶음 끝 커밋 트리(git archive)로 시험을 다시 돌렸다.

## 모드 묶음 M1~M8·X1·X2·B1~B3·K1 (d3549d9~bae54a8)
- **M1 DECOMPOSE_K.** 그룹 요소 밖 절점·뿌리 요소 매니저(PID 없는 질량·요소 셋)·데이터 없는 키워드를 globals.k 에 쓴다. 빈 키워드는 공용 기록기처럼 매니저가 이미 쓴 것(controls.k 의 NODUMP 등)을 건너뛴다. ModelIndependentSplit False 면 controls.k 를 쓰지 않는 것은 문서에 적힌 동작이라 그대로 두었다.
- **M2 IMPORT_MERGE_K — 처음 목록 넷 + 고치다 찾은 것(M2e).** PartSet 은 .psid 인데 .sid·.id 로 읽어 오프셋이 늘 0 이고 재키잉에서 죽었다. 탐침을 넓히자 병합이 기준 덱을 조용히 덮는 것이 더 나왔다.
  - 곡선 LCID 오프셋을 없는 속성(.id)에서 읽어 늘 0 → 같은 번호의 기준 덱 곡선을 덮었다. 곡선을 밀면 재질(LCSS 등)이 번호로 참조해 틀리므로, 재질처럼 **번호 보존·새 번호만 추가·같은 번호 다른 내용은 🔴**로 정했다(매뉴얼의 'DefineID 재할당' 은 코드와 달랐다 — 매뉴얼을 고친다). HOURGLASS 도 같다.
  - 경계 조건은 bid 로 Overwrite 해 같은 번호의 기준 덱 조건을 덮었다 → 새 번호로 더한다. 절점·절점 셋은 객체라 오프셋을 따라가고, 정수 참조(PZEPOT NSID·강체 PID)는 민다.
  - 구속·부분 감쇠·강체벽·INTERFACE·D2R 는 PID·NSID 를 정수로 지녀 밀지 못한 채 기준 덱 파트·셋을 가리켰다(키도 덮었다). 필드마다 오프셋을 넣는 것은 종류가 많아 이번엔 **옮기지 않고 🔴 + rc 3** 으로 정했다(예전: 틀린 참조를 조용히 씀 → 지금: 빠졌다고 알림).
  - CONTROL·DATABASE 는 가져온 덱 설정이 기준 덱 설정을 덮었다 → 기준 덱 설정을 쓰고 알린다. IMPORT_MERGE_K 를 쓰는 체인·예제가 없어(시험 test_reader_review_h 뿐) 흐름 영향이 없다.
  - '카드 소실' 장부(CONTENT_LOSS)를 새로 두었다 — 요소 소실 장부는 '요소 N개' 로 적어 블록 소실에 맞지 않는다. KMM 끝 처리가 둘 다 🔴 + rc 3 으로 알린다.
- **B1~B3 (M2 중 찾음).** *BOUNDARY_PRESCRIBED_MOTION_RIGID 의 PID 를 절점 번호로 찾아 같은 번호 절점이 없으면 조건을 버렸다. *BOUNDARY_PRESCRIBED_MOTION_NODE(_ID 없는 판)는 한 번도 제대로 돈 적이 없다(단수 생성 함수·super()·self.node 셋이 틀렸다). SPC·처방 운동 여러 절점 그릇이 가변 기본 인자를 같이 써 블록마다 모든 절점을 되풀이했다.
- **X1.** '재질 MID 소실' 대조를 해석하는 재질 키워드로 좁혔다 — 해석하지 않는 재질은 원문으로 나가 MID 가 출력에 있다.
- **M3 + 최종 기록기 *KEYWORD 줄.** 원문 꼬리를 WriteStreamRawTail 로 떼어 Fast 캐시들이 같이 쓴다(공용 기록기 출력은 같다). 249cdef 가 정한 '최종 덱 기록기는 원본 *KEYWORD 줄' 규칙에서 메인 기록기·MERGE_K·MaterialExchange·DimensionalTolerance·TranslationDOE 가 빠져 있었다 — 맞췄다. 전역 I10 이면 매니저 기본값이 10칸이라 선언과 블록이 맞는다(249cdef). PART_VALIDATION 단순 덱은 8칸 고정이라 그대로 둔다.
- **M4.** dynain 의 원문 INITIAL_STRESS_(SHELL·TSHELL·BEAM)·INITIAL_STRAIN_* 를 옮기고, 앞 단계의 같은 원문은 지운다(단계마다 한 벌).
- **M5.** DampingSpring 의 Run 폴더 블록을 _WriteDwiRunDirectory 로 떼었다. DWI 는 생성 방식과 상관없이 기본 model_dwit.k 도 쓴다(예전과 같다). 원문 재질 파트는 바깥 강체화를 건너뛰고 알린다.
- **M6.** 해석한 TSHELL8 은 HEXA8 분기를 같이 쓰고, 원문 TSHELL 줄은 칸 글자를 지키며 N1~N8 자리만 바꾼다. 다른 원문 요소 키워드는 알리기만 한다.
- **M7.** is_tshell(요소, 매니저) 하나로 다섯 판정을 맞췄다. 시험 M7r 은 처음에 '*SECTION_SOLID 가 없어야' 로 봤는데, ConvertHexato 뒤 아무도 쓰지 않는 원래 솔리드 단면이 남을 뿐이라 '파트가 가리키는 단면이 TSHELL' 로 고쳤다.
- **M8·X2.** 단면·요소 종류가 다르면 알린다(같이 준 ConvertHexato 가 그 종류로 바꾸면 조용). 다른 모드가 같은 모드 ID 를 쓰면 rc 1 — 예제·시험·문서의 *Mode 270개와 KooChainRun 생성기(이동 모드 1·본 모드 2)는 겹치지 않는다.
- **K1.** SPHERE_NEW_MEM_PER_WORKER_GB 2 → 0.5(979런 38G → 14G). 메모리가 워커 수를 깎는 경우를 보던 시험 둘은 노드 메모리를 바꿔 같은 성질을 계속 본다.
- **아는 불량.** 부품·경계·모드 시험 모두 19a7e6a 에서 실패(원래 맞던 경로만 통과)하고 고친 판에서 ALL OK.

## 적대 리뷰 R1~R3 고침 (8fccfde~f676eb0)
- **콤마 요소 줄.** 블록 폭(8칸, I10 10칸) 고정폭 줄로 먼저 바꾼다(_comma_to_fixed). 칸에 들지 않는 값(8칸 블록의 9자리 ID 등)은 고정폭으로 쓸 수 없어 🔴 로 멈춘다. *ELEMENT_SHELL_THICKNESS 도 같은 함수를 쓰되, 두께(실수) 카드는 폭에 매이지 않게 콤마로 나눈다.
- **D2R(R2-5).** 덱의 *DEFORMABLE_TO_RIGID_AUTOMATIC 은 매니저에 넣지 않고 원문 그대로 둔다. 매니저 기록기는 D2R·R2D 를 늘 'PART' 형식·TIME2 1e20 으로 다시 써 PSET 같은 덱 카드를 옮기지 못한다. 매니저에는 KMM 이 만드는 D2R 만 둔다(DROP 의 D2R 옵션 시험 test_d2r_* 로 확인).
- **두께 블록(R2-6).** 카드 수가 바뀌는 곳에서 블록을 나눠 넘긴다 — 받는 쪽(KooPart·기록기)은 블록마다 카드 수가 하나라고 보고 카드 1 칸 수로 가린다. 블록 안 카드 1 칸 수를 맞추는 것도 그 때문이다. 레거시 카드 1 을 줄마다 길이로 읽게 바꾸다 '첫 요소가 삼각형(40자)이면 뒤 사각형 N4 가 rc 0 으로 잘림' 을 찾았다. 섞이지 않은 블록 두 덱은 출력 바이트가 같다.
- **IMPORT_MERGE_K 재질(R3-4).** 같은 MID 다른 재질·기준 덱 원문 재질과 같은 MID 는 기준 덱 것을 남기고 🔴 rc 3(곡선·HOURGLASS 와 같은 규칙). *MAT_ADD_* 는 가져와 더한 MID 에만 붙인다. 재질 객체엔 WriteStreamDynaKeyword 가 없어 비교 글이 늘 None → 같은 재질도 충돌이던 것을 test_reader_review_h 가 잡았다(GenerateDynaKeyword 로 글을 만든다).
- **DTI(R3-13).** 지우는 것은 LS-DYNA dynain 이 쓰는 원문 종류(SHELL·TSHELL·BEAM 응력, SHELL·SOLID·TSHELL 변형률)와 이번 dynain 에 든 종류뿐이고, 지운 것을 로그로 알린다. dynain 에 그 종류가 없어도 앞 단계 것은 지운다(앞 단계 dynain 값이라 이번 상태가 아니다).
- **DECOMPOSE_K(R3-9).** M1 때 'ModelIndependentSplit False 면 controls.k 를 안 쓰는 것은 문서 동작' 으로 뒀으나, 다른 파일에도 안 써 CONTROL·DATABASE 가 사라졌다 — False 면 globals.k 에 함께 쓴다(매뉴얼·help 고침).
- **\*SET_NODE_LIST_GENERATE.** 범위 안에 정의된 절점을 같은 NSID 의 *SET_NODE_LIST 로 펼친다(R16 뜻이 같다) — 출력 키워드가 바뀌는 것은 의도. 원래 호출처가 없던 NodeSetListGenerate 클래스·CreateNodeSetListGenerate 는 그대로 남겼다(죽은 코드, 지우지 않음).
- **리뷰어 im_dbonly 덱이 이제 rc 3.** 그 덱의 *NODE 는 좌표를 10칸으로 적어 R16 고정폭(16칸)으론 Y 칸이 ' 0.0       0.0' 이다 — LS-DYNA 도 못 읽는 줄이라 R1-9(읽지 못한 절점 줄 → rc 3)대로 맞다.
- **시험 판정 주의.** KMM 기록기는 처방 운동·접촉을 원래부터 _ID 꼴(번호·제목 카드)로 쓴다 — _ID 없는 입력도 출력은 _ID 다. test_v131_review 는 두 꼴을 다 받는다.
- **아는 불량.** test_v131_review 47 판정 중 bae54a8 에서 44 실패. 통과 셋 = 전제 조건(DropSet.k 2개), 이 작업 중간 판 회귀(같은 재질 충돌)를 막는 판정, sphere(Runner 를 현재 트리에서 읽음 — 옛 모듈로 (13,'12G')+🔴 따로 확인).

## 말뭉치 W7·집중 리뷰 R4 고침 (100a028~01e8581)
- **말뭉치 W7(v130 694494c 대비, 새 판 2976643).** 같음 38·다름 709, 고쳐진 크래시 85·새 크래시 0. 분류 밖 34건을 모두 출력으로 봤다 — 78건은 *NODE 없는 *PARAMETER 덱이 KeyError 에서 풀린 것, 나머지는 의도(PART.secid·요소 셋 새 번호·곡선 충돌 rc 3·NID 0 유령 절점 없앰·DECOMPOSE globals·덤프 표기). 결함 둘을 찾았다: 콤마 원문 카드(*MAT_ADD_EROSION·SECTION_BEAM raw_cards)의 빈 칸이 사라져 값이 당겨짐(aadecca), 셸 요소 셋(SSTYP 1)을 쓰는 가져온 접촉이 기준 덱 셋을 가리킴(b405ccb). 옛 판 쪽은 트리가 같아 W6 결과를 재사용했다.
- **좌표계 점 변환(100a028).** 좌표계를 출력에 쓰기 시작해(75dc12d) TRANSFORM 회전·대칭에서 좌표계가 제자리에 남으면 재질 축이 조용히 틀린다 — 절점과 같은 변환을 점에도. CIDL 있는 것은 기준 좌표계를 따라가 그대로.
- **콤마 남는 값(a879d11).** 8fccfde 의 '남는 값 지키기' 를 되돌렸다(고정 칸 카드에서 다음 카드로 밀림). 줄 길이로 칸 수를 세는 리더(HISTORY·MAT_GENERAL_VISCOELASTIC·요소 카드)는 콤마 줄을 따로 센다. LS-DYNA 도 카드 칸만큼만 읽는다고 본다(리뷰 R4 추측과 같다).
- **처방 운동 카드 3(c20372c).** 기록기가 카드 3 을 쓰지 못해 옮기는 대신 🔴 로 멈춘다(사용자 덱에서 빼고 KMM 뒤에 넣게). 카드 3 지원은 다음 판 과제다.
- **DTI(1dbf49b).** 18b2353 의 '앞 단계 dynain 종류는 늘 지운다' 를 '이번 dynain 에 든 종류만 바꾼다 + 남은 dynain 종류는 ⚠' 로 바꿨다 — 사용자 셸 초기 응력이 조용히 사라지는 쪽이 더 위험하다고 봤다. 누적 체인 둘째 단계(같은 종류가 다시 옴)는 그대로 한 벌.
- **Fast DROP 강체화(3119c0c).** 각도와 상관없는 기준이라 루프 앞·베이스 캐시 전에 한 번. 예전 단일 각도·비 Fast 경로와 결과가 같다.
- **원문 단면·재질 번호 예약(4c964c4)·D2R SWSET(acab1c6).** PID·EID 예약과 같은 방식(데이터 줄 첫 칸 순수 정수, 넉넉해도 안전). SWSET 은 덱과 겹칠 때만 옮겨 보통 덱 출력은 같다.
- **남긴 것(다음 판).** *MAT_ELASTIC·PLP 등 재질 기록기의 유효숫자 4자리(리뷰 R4 mat_prec — I6 셸 단면과 같은 규칙으로 고칠 일), 처방 운동 카드 3 지원, SSTYP 7(가지), *DEFINE_BOX_LOCAL 의 TRANSFORM 원점(추측), 호출처 없는 CombineManager·NodeSetListGenerate 죽은 코드.
- **말뭉치 W8(새 판 01e8581).** W7 과 같은 꼴(같음 38·다름 709, 크래시 85 해소·새 크래시 0, 분류 밖 34 그대로). W7 대비 바뀐 사례는 셋뿐 — H_t5_erosion_comma(콤마 침식 카드 칸, 의도), J_S4_tri 덤프(첫 줄이 삼각형이라 잘리던 둘째 줄 N4 복원, 의도), G_t1_SPAEND 덤프(열 1 이 아닌 ' *END' 데이터 줄 — 옛·새 판 모두 rc 1 인 기존 사례, 표기만 바뀜).
- **말뭉치 V8(실제 덱 78개·88건, 01e8581).** 88건 모두 rc 가 v130 과 같다(74 rc 0·14 rc 3). 출력에서 늘거나 준 키워드는 *BOUNDARY_PRESCRIBED_MOTION_RIGID_ID(+144 — B1: v130 은 강체 PID 를 절점으로 찾아 '노드 미발견' 으로 DWI 덱의 처방 운동을 모두 버렸다)와 *DEFINE_COORDINATE_SYSTEM(+12) 뿐이다. 블록 분류의 ?PART·?MAT_ELASTIC_TITLE 56건은 DROP 바닥판 MID 가 원문 *MAT_JOHNSON_COOK 9 와 겹치던 것(v130)이 10 으로 비켜난 것(4c964c4). 모두 의도한 다름이다.
- **집중 리뷰 R5(2fd16c6~8323b0e 로 고침).** 콤마 빈 값 공백화(aadecca)는 빈 칸을 len()==0 으로 가리는 리더(*INITIAL_VELOCITY·*EOS_TABULATED·제어 카드)를 깨서 되돌리고, 원문 카드 잇기(_join_card)에서만 공백 칸으로 채운다. 8칸 요소 줄 칸 수는 올림(_n8). *ELEMENT_SOLID 1줄 꼴(첫 줄 > EID·PID 두 칸)은 줄마다 읽는다 — 둘째 줄이 짧으면 블록을 2줄 꼴로 뒤섞던 기존 결함. GENERAL_VISCOELASTIC 카드 2 는 8칸. IMPORT_MERGE_K 침식은 속성에 안 담기는 원문 칸까지 견주고, 붙는 카드 충돌은 가져온 파트가 쓰는 MID 만. DTI 는 지운 접촉을 가리키는 덱 D2R 도 지운다(누적 체인의 두 쌍·꺼진 단계 전환). a879d11 이 바꾼 KooDynaDatabase.py 줄끝은 CRLF 로 되돌렸다.
- **남긴 것 더하기(R5).** DROP D2R·R2D 목록에 강체화된 MAT_RIGID 파트가 들어간다(기존), Fast DROP 바닥 접촉 CID 가 각도마다 1·2·3(기존, 덱마다 고유해 무해), DTI 는 키워드 종류 단위로 바꾼다(다른 파트 셸 응력만 실은 dynain 도 사용자 셸 응력을 바꾼다 — 설계 한계), long('+') 처방 운동 블록의 🔴 메시지 문구.
- **말뭉치 W9·V9(새 판 8323b0e).** V9 는 88건 rc 가 V8 과 같고, 새 판 출력이 바뀐 43건은 모두 줄 끝 공백뿐이다(블록 내용은 같음). daf0184 의 _join_card 가 고정폭 줄 끝 너머의 빈 칸('')까지 공백 10자로 채워 원문 *MAT_ADD_EROSION 줄 끝에 공백이 붙었다 — 가운데 빈 칸만 채우고 끝의 빈 칸은 떼게 고쳤다(15893dc).

## 집중 리뷰 R6 고침 (2588784~15e86c9)
- **RemoveContactbyPartID(2588784).** `MSID == pid or MSTYP == 3` 이라 파트 하나를 지우면 주 면이 파트인 접촉이 모두 사라졌다(1월 08ce9639 부터의 기존 결함). 누적 체인 DTI 는 늘 바닥판을 *RemovePartbyID 로 지우므로 둘째 단계부터 파트끼리 TIED·S2S 접촉이 rc 0 으로 사라졌다. 리뷰 R6 가 5efc7dc 를 보다 뿌리로 찾았다.
- **DTI 덱 D2R 고르기(cffaaa8).** R16 은 CODE 1·3 이 강체벽 힘, 2·4 가 접촉력이다 — 5efc7dc 가 CODE 3 을 접촉으로 봐 강체벽 짝까지 지웠다. 받은 번호가 아니라 지우기 전·후 접촉 차집합(실제로 없어진 접촉)으로 고르고, 지우지 못한 원문 접촉 번호는 ⚠ 로 알린다(그 D2R 은 남김). 짝 한쪽만 그 접촉을 가리켜도 RELSW·SWSET 닫힘으로 둘 다 지운다. 다른 접촉을 가리키는 사용자 짝은 남는다(시험 R6 dti_d2r_user).
- **침식 비교(5acf580).** 카드 3 의 2~7칸은 IDAM≠0 일 때만 뜻이 있다(R16). IDAM 0 이면 견주지 않고, IDAM≠0 이면 빈 칸을 R16 기본값(DMGEXP·FADEXP 1.0, 나머지 0)으로 채워 견준다. R5 시험의 침식 충돌 사례는 IDAM 1 로 옮겼다.
- **WINFRITH(3225d95).** *MAT_WINFRITH_CONCRETE_REINFORCEMENT 첫 칸은 EID1 이다 — 원문 재질 번호 예약·IMPORT_MERGE_K 원문 MID 에서 뺐다(리뷰어가 코드로 찾음, 영향은 추측).
- **요소 줄 칸 수(91936bd).** _n8 은 80열에서 자른다(81열 뒤 '   #3' 으로 솔리드 블록 칸 수가 11 → 요소 모두 빠짐). I10 셸·솔리드·빔·두께 리더도 8칸처럼 올림으로 센다.
- **강체벽 번호(d893fb4).** 번호 없는 *RIGIDWALL_PLANAR 의 자동 번호 1 을 *RIGIDWALL_PLANAR_ID 1 이 덮어 벽 하나가 사라졌다 — 먼저 있던 벽을 남는 번호로 옮기고 알린다.
- **남긴 것 더하기(R6).** 강체벽 기록기는 *RIGIDWALL_PLANAR(움직이지 않는 벽)도 *RIGIDWALL_PLANAR_MOVING_FORCES_ID(MASS 0·V0 0)로 다시 쓰고, 제목을 버리고, 좌표를 10.4f 로 쓴다(옛 판부터 같음). MASS 0 인 움직이는 벽을 LS-DYNA 가 고정 벽과 같게 보는지는 확인하지 못했다(추측) — 다음 판에서 매뉴얼·실행으로 확인할 일이다.
- **아는 불량.** 새 판정 16개 중 15개가 8323b0e 에서 FAIL 이다. 통과 하나(침식 끝 주석 줄 '$')는 옛 판도 맞던 경우라 회귀 방지로 둔다. 전체 test_v131_review 95 판정 ALL OK(2분 43초).
- **말뭉치 W10·V10(새 판 15e86c9).** W10 은 747건 rc 가 W8·W9 와 같다. W9 대비 내용 차이는 J_S11·J_S12 덤프의 셸 줄에서 81열 뒤 '999' 를 더는 칸으로 읽지 않는 것뿐이다(91936bd 의도). 줄 끝 공백만 다른 파일은 모두 새 판 쪽 공백이 적다. V10 은 V8(01e8581)과 88건 모두 출력이 바이트까지 같다(rc 74·14).

## 집중 리뷰 R7 고침 (44e3b44~4f63f92)
- **DWI 다음 단계 DTI(44e3b44, 🔴).** DWI 의 dynaintoinitial.txt 는 임팩터 파트만 지우라고 적었다. 벽·임팩터 앞 단 접촉은 RemoveContactbyPartID 의 'or' 결함이 우연히 지워 왔다 — 2588784 로 그 결함을 고치자 누적 IMPACT 체인의 다음 단계에 벽 접촉(모든 파트 ↔ 고정 강체벽)이 남았다. DROP 이 바닥판 접촉을 적듯이 DWI 파트를 가리키는 접촉 번호를 *RemoveContactbyID 로 적는다. 벽·앞 단 파트와 벽 처방 운동이 남는 것은 v130 과 같다(PLAN '하지 않는 것' 의 누적 DWI 벽 겹침). 파트까지 지우면 벽 처방 운동이 없는 파트를 가리켜 새 실패가 생길 수 있어 이번엔 접촉만 지운다.
- **강체벽 차례(30ca4a4).** 겹친 벽을 dict 끝으로 옮기지 않고 제자리에서 번호만 바꾼다(R16: D2R CODE 1·3 ENTNO·RWFORC 는 정의 차례).
- **재질 별칭(2617fbb).** *MAT_084_REINF·*MAT_T01~ 를 긴 이름처럼 뺀다. 두 파일이 따로 지니던 접두어 목록을 RAW_MAT_NOT_MID 하나로 모았다(목록이 둘이라 하나가 빠졌던 것).
- **침식 끝 빈 카드(933e340)·D2R 닫힘(46397af)·long SWSET(cc97d9e).** IDAM≠0 카드 6~ 끝 빈 줄을 뗀다. 닫힘은 지운 세트가 가리키는 쪽을 PAIRED ±1 일 때만 따라간다. DROP 의 SWSET 겹침 검사는 long 블록을 20칸으로 읽는다(acab1c6 의 빈틈).
- **Fast DROP RigidWall(cdbbd66, v130 부터 🔴).** 여러 각도 DropSet.k 에 바닥 강체벽이 하나도 없었다(차분 기록기에 강체벽이 없고 되돌리기도 벽을 안 지움). 캐시 상태·되돌리기·차분에 강체벽을 넣었다. 각도별 벽 카드는 같은 각도 단일 실행과 글자까지 같다.
- **R7 범위 밖 — v130 으로 다시 돌려 모두 기존 결함으로 확인.** ① KMM 이 쓴 *RIGIDWALL_PLANAR_MOVING_FORCES_ID 를 다시 읽으면 카드가 한 장 밀린다(getRigidWallPlanarMovingForcesID 의 이름표가 _ID 없음). 한 줄로 고칠 수 있지만, DTI 에 강체벽을 지우는 옵션이 없어 고치면 RigidWall 누적 체인에서 지금은 깨져 있는 앞 단계 벽이 멀쩡히 살아나 다음 낙하가 조용히 틀린다 — DTI 강체벽 지우기와 함께 다음 판에서. ② IncludeWallInGeneral 누적 체인의 둘째 DROP 에 바닥판 접촉이 없다(SS_from_GENERAL 이 새 바닥판을 덮는지 확인 필요). ③ *RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID BIRTH 0 → 1E20, 번호 없는 FLAT_DISPLAY IndexError(rc 1). ④ 강체벽을 종류별로 읽어 덱 차례와 다르다. ⑤ RemovePart 가 *SET_PART_LIST 에서 지운 PID 를 빼지 않는다. ⑥ 강체벽 기록기가 PLANAR 를 MOVING_FORCES(MASS 0)로 다시 쓰고 좌표를 10.4f 로 쓴다(R6 에 적음).

## 집중 리뷰 R8 고침 (d4cb0fe~9316745)
- **R8 범위 안은 🟡 하나뿐(R7 고침 8개는 적힌 대로).** DWI 접촉이 원문 접촉과 같은 CID 를 받아(KMM 은 해석한 접촉 번호 다음만 매겼다), 44e3b44 뒤로 DTI 가 그 번호를 지우며 원문 접촉을 가리키는 사용자 D2R 까지 지웠다. 뿌리는 v130 부터의 접촉 번호 중복이다 — 실제 덱 말뭉치 V10 의 KooRemapper 예제(067)에서 DropSet.k 에 접촉 3 이 둘이었다(원문 THERMAL TIED 3 + 바닥판 3). 원문 *CONTACT_…_ID 의 CID 를 예약한다(0b36b12) — 원문 접촉이 있는 덱은 KMM 바닥판·DWI 접촉 번호가 바뀐다(의도).
- **RobustContact 각도 번호(d4cb0fe, v130 부터 🔴).** 각도 루프 안 TIED 면 찾기가 `for i, seg in enumerate(...)` 로 바깥 i 를 덮어, RunID 를 준 여러 각도가 Run 폴더 하나에 겹쳤다(7각도 → Run_106 하나, rc 0). 세그먼트 번호를 si 로 바꿨다. 파일 전체 AST 로 다른 'for i' 안쪽 덮어쓰기를 찾았고, DROP·DWI 에는 더 없다(ConvertSolidtoSolidwithSlack 의 `i = i - 1; continue` 는 다른 기존 결함 — 아래 목록).
- **R8 에서 고치지 않은 것(⚪, 사유).** F2 서로 가리키지 않는 '짝' 덱(잘못 만든 덱)에서 닫힘이 짝을 함께 지움. F3 Fast 초기화가 예외를 낼 때만 타는 비 Fast 경로가 RigidWall 둘째 각도에서 AttributeError(v130 부터, 재현 못 함).

## 다음 판으로 넘기는 기존 결함(모두 v130 과 같음 — 리뷰 R6~R8 이 찾음)
- 🔴 **RigidWall 누적 체인.** KMM 이 쓴 *RIGIDWALL_PLANAR_MOVING_FORCES_ID 를 다시 읽으면 카드가 한 장 밀린다(이름표 한 줄). DTI 에 강체벽을 지우는 옵션이 없어 이름표만 고치면 앞 단계 바닥 벽이 다음 단계에 멀쩡히 살아난다 — 이름표 + DTI *RemoveRigidWallbyID + DROP 의 dynaintoinitial 을 함께 고칠 일. cdbbd66 뒤로 여러 각도 RigidWall 체인도 단일 각도 체인과 같은 꼴이 됐다(첫 단계는 이제 바름).
- 🔴 **누적 IMPACT 체인의 DWI 파트.** 앞 단계 벽·임팩터 앞·가운데 단·댐퍼 빔·SPC 가 다음 단계에 남는다(접촉은 44e3b44 로 지움). IMPACT→IMPACT 에서 새 임팩터가 남은 앞 단 조각 위에 놓여 그것을 먼저 친다. 파트를 지우려면 벽 처방 운동·초기 속도·SPC·댐퍼 빔도 함께 지워야 한다(설계 문제, PLAN '하지 않는 것').
- 🔴 **IncludeWallInGeneral 누적 체인** 둘째 DROP 에 바닥판 접촉이 없다(SS_from_GENERAL 이 새 바닥판을 덮는지 확인 필요).
- 🟡 단일 각도 RigidWall 은 바닥 벽을 원문 강체벽 앞에 쓴다(Fast 는 뒤 — 정의 차례가 경로마다 다름). 강체벽을 종류별로 읽어 덱 차례와 다르다. DROP 은 덱 사용자 강체벽을 모델 이동·회전에 맞춰 옮기지 않는다.
- 🟡 강체벽 기록기: PLANAR 를 MOVING_FORCES(MASS 0)로 다시 쓰고 제목을 버리고 좌표를 10.4f. *RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID BIRTH 0 → 1E20, 번호 없는 FLAT_DISPLAY IndexError(rc 1).
- 🟡 DampingSpring BoundaryDistance≠0 덱을 DTI 로 넘기면 댐퍼 빔·SPC·바깥 요소를 지운 시편이 그대로 다음 단계로 간다. OutsideRigid*·byPart 덱에는 *INTERFACE_SPRINGBACK_LSDYNA 가 없어 덱에 그 카드가 없으면 dynain 이 안 나온다(코드 읽기).
- ⚪ byPart 원통 DWI 는 CreateCylinderImpactorPart 의 정의 안 된 nodeMan 으로 늘 rc 1 — 한 줄로 고칠 수 있지만 한 번도 끝까지 돈 적 없는 경로라 시험과 함께 열 일.
- ⚪ ConvertSolidtoSolidwithSlack 의 `i = i - 1; continue` 는 for 루프에서 재시도가 되지 않아 범위 밖 샘플을 버린 만큼 샘플 수가 모자란다.
- ⚪ RemovePart 가 *SET_PART_LIST 에서 지운 PID 를 빼지 않는다. IDAM≠0 침식 가운데 빈 카드 대 0 을 적은 카드는 거짓 rc 3.
- 그 밖에 앞서 적은 것: 재질 기록기 유효숫자 4자리(mat_prec), 처방 운동 카드 3 지원, SSTYP 7, *DEFINE_BOX_LOCAL TRANSFORM 원점, D2R 목록의 강체화 MAT_RIGID 파트, Fast DROP 바닥 접촉 CID 가 각도마다 늘어남, DTI 키워드 종류 단위, 죽은 코드 CombineManager·NodeSetListGenerate.

## 배포 (11-04 19:07~21:10)
- **빌드.** HEAD 9316745 를 build_capped_v131.sh(root scope MemoryMax 24G·oom_score_adj 1000·가용 8.5 GB 워치독)로 build_without_automatedmodeller.sh --clean — 19:07~20:00 BUILD_RC 0, 최저 가용 23 GB. KMM 92bc27ce(19:50)·KCR fc699478(19:59), KAM 580f028e 그대로. NFS·SIF 소스 트리가 같다. 빌드 로그의 error 류 108줄은 모두 Nuitka 진행 메시지(모듈 이름)다.
- **호스트 e2e.** 아는 불량 먼저: 헤드 /opt v130 KMM 으로 test_v131_review 21 OK / 85 FAIL(통과 21개는 v130 도 맞던 경우를 지키는 판정). 새 컴파일본: 10절점·파일 끝 8종 ALL PASS, KMM 시험 22종 FAIL 0(test_v131_review 107), KCR 결과 귀환·help·sphere 사이징(워커 0.5 GB → 979런 산출 14G) ALL PASS.
- **굽기(20:24~20:32).** 굽기 직전 다시 본 것: 헤드·compute-node-images 9d166fd0, 마지막 tar v130, 잡 없음, KooRemapper b9d4c12d(kooremapper-fd 에 앞뒤 알림). SIF 32260efb(1,582,186,496 B) = compute-node-images, tar v131 1,346,493,780 B, Drive ApptainerImages:SmartTwinPreprocessor/, 메일 sent OK.
- **SIF e2e.** 바이너리 셋 = SIF 소스 트리, KooRemapper 80열 18 OK, 10절점·파일 끝 8종 ALL PASS, SIF 안 KMM 시험 22종 FAIL 0(R7·R8 의 DWI 판정이 SIF 안 gmsh 로 임팩터를 메시), KAM PKG ALL OK.
- **헤드 /opt(21:04).** v131(32260efb)이 됐다. v130(9d166fd0)은 하드 링크 `SmartTwinPreprocessor_backup_20261104_210443.sif` 다. 노드(node001·002·viz)는 down 이라 미배포다 — 켜면 compute-node-images 의 v131 을 deploy_apptainers.sh 로(헤드 백업 먼저).
- **헤드 /opt 확인.** 교체한 헤드 SIF 껍데기(kmm_in_head_opt.sh)로 test_v131_review 107·test_kmm_real_deck_crashes 40·test_section_card_sets 37·test_tshell_element_contact 21·test_tshell_section_preserve 13·test_robust_contact_tied_thickness 12 모두 FAIL 0, KooRemapper test_card_80col 18 OK.
- 🟡 **sphere 워커 메모리 0.5 GB(K1)의 한계(배포 뒤 a9 지적, 11-04 21시).** a9 실측 298 MB 를 나누면 파이썬 기저·임포트는 13 MB 이고 285 MB 가 덱 처리(binout 파싱·흐름 조립) 몫이다 — 워커 RSS 는 거의 전부 모델 크기에 비례한다. 잰 캠페인(Test_005_Fibonacci_100, 런당 binout 5.8 MB·흐름 0.98 MB)은 작아 0.5 GB 도 여유가 1.7배뿐이고, M3_P2 급(흐름 87 MB/런, 약 89배)은 워커 하나가 수 GB 를 쓸 수 있다. 노드가 모두 down 이라 지금 위험은 없다. 큰 캠페인을 처음 돌리기 전에 실덱에서 `koo_sphere_report --test-dir <캠페인> -j 2 --terminal-only` 의 워커 RSS 를 표집해 SPHERE_NEW_MEM_PER_WORKER_GB(또는 sphere 자원 명시 메모리 — 산출값보다 크면 명시값을 쓴다)를 정한다. 런당 binout 크기 비례식(워커 ≈ 13 MB + 285 MB × binout/5.8 MB)은 점 하나(fib100 — 이 머신의 binout 캠페인 셋이 모두 같은 모델)에서 나와 자릿수 가늠용일 뿐이다(흐름 크기는 접촉·파트·시간스텝 수를 따라 binout 과 비율이 같다는 보장이 없다). 결정은 실측으로 하고, 그 실측이 두 번째 점이 된다 — 잰 값은 a9 에 알려 KooD3plotReader docs/sphere_automation_2026-10/measurement.md(ac06ced, '분해 결과' 절)에 함께 적는다.
