<!-- 10-23 남은 Pre 결함 수정 중 결정과 근거를 적는 노트 -->
# 컨텍스트 노트 — 남은 결함 정리 (2026-10-23)

## 분류 근거
- R16 Vol I `*END`: "The *END command is optional and signals the conclusion of a keyword input file. Data in a keyword file beyond a *END command are not read by LS-DYNA."
- R16 `*INCLUDE` Remark 1: "Note that the command *END terminates the include file."
- 그래서 KMM 이 `*END` 뒤 블록을 읽던 옛 동작(마지막 블록만 버림)은 LS-DYNA 와 다르다. f1ad034 는 `*END` 가 있는 파일을 옛 동작 그대로 둬서 바이트 동일을 지켰다. 이번에는 사용자 지시로 LS-DYNA 규칙에 맞춘다.
- 우리 출력기(KMM·병합기·분해기·고급 수정·IGA·검증기)는 모두 파일 끝에 `*END` 하나만 쓴다. 병합기는 인라인할 때 `*KEYWORD`·`*END` 줄을 지운다. 러너(Runner)에는 `*END` 를 다루는 코드가 없다. 그래서 F3 는 우리 산출물을 바꾸지 않는다.
- R16 Appendix V: 빈 줄은 '기본값만 든 선택 카드' 로 읽힌다. `*ELEMENT_SHELL_THICKNESS` 의 빈 두께 카드는 '섹션 두께' 라는 뜻이 있다. 반면 순수 `*ELEMENT_SOLID`·`*ELEMENT_SHELL` 카드는 EID·PID·N 이 모두 기본값이 없어(none) 빈 줄이 정상 카드가 될 수 없다. 그래서 F1 은 이 둘의 레거시 경로만 고친다.
- R16 `*ELEMENT_SOLID`: 표준은 Card 1(EID PID)+Card 2(N1~N10)다. Remark 4 'Obsolete Card Format' 은 940~970 판의 한 줄 형식이다. `(ten nodes format)` 표기는 원문에 없다. 그래서 writer 는 결함이 아니다.
- 데이터 카드 없는 키워드: 원문에서 `*CONTROL_MPP_IO_NOTIEDIO`("This keyword has no input parameters"), `*LOAD_SEGMENT_ALE_INI`("This keyword has no data cards"), `*CHANGE_VELOCITY_ZERO` 를 찾았다. `*CONTROL_MPP_IO_NOD3DUMP` 도 같은 꼴이다. `*CONTROL_MPP_IO_NODUMP` 는 전용 클래스(ControlMppIoNodump)가 있어 이미 살아남는다.
- 빌드 컨테이너(KooSimulationPython313)의 LD_LIBRARY_PATH 는 `/opt/opencascade-7.9.0/lib:/opt/SmartTwinPreprocessor/lib/KooMeshModifier:/usr/local/lib:/.singularity.d/libs` 다. 컨테이너 안 ldd 는 `_ssl`·`_hashlib`·`readline` 의 libssl·libcrypto·libreadline 을 `/opt/SmartTwinPreprocessor/lib/KooMeshModifier` 에서 찾는다. 이 파일들은 GLIBC 2.38 을 요구해 컨테이너 자신의 `python3.12 -c 'import ssl'` 도 죽는다. `env -u LD_LIBRARY_PATH` 면 `/lib/x86_64-linux-gnu` 의 OpenSSL 3.0.2 를 찾고 정상이다. KooChainRun 배포 폴더의 libcrypto.so.3 도 2.38 이다.
- DWI: KMM DropWeightImpactTest 의 폴백값은 SI 다. 앞부분은 E 2.07e11·ρ 7800, 댐퍼는 E 1e10·ν 0.3·ρ 1000·치수 [0.001]×3(SECTION_BEAM 폭·높이·오프셋), 바닥판은 E 1e10·ρ 1000 이다. 러너 `_write_dwi_step_config` 는 충격체 본체·바닥판만 ton-mm-s 로 넘긴다. Mid 는 KMM 이 Impactor 값으로 대신 쓰므로 문제가 없다. MeshSize 는 KMM `_ResolveImpactorMeshSize` 가드(치수/8)가 이미 막고 있다.

## 작업 중 결정
- F7 방향을 바꿨다. 처음에는 '러너가 ton-mm-s 값을 명시' 였다. 그런데 저장소의 IMPACT 시나리오 둘(Test_Impact_Grid5x5·Spacing5mm)이 SI 치수(0.008·0.5·0.001)를 직접 준다. 그러니 IMPACT 는 SI 모델에도 쓰이고, 러너가 mm 값을 박으면 SI 모델이 반대로 틀어진다. 그래서 KMM 이 중력 판정(_ResolveFallGravity)과 같은 재질 밀도 판정으로 폴백을 고르게 했다(_DwiFallbacks). 러너 IMPACT 는 mesh_size·dimension_damper 가 없으면 줄을 쓰지 않는다. SI 시나리오는 값을 직접 주므로 그대로다.
- byPart(Part) 경로는 손대지 않았다. 부품 생성기가 원래 mm 폴백(E 2.07e5·ρ 7.8e-9, 바닥판 E 1e6·ρ 1e-9)을 쓰고, 댐퍼 코드는 `'''` 문자열 안의 죽은 코드다.
- 남긴 것: IMPACT 의 dimension·height·offset_distance 기본값은 여전히 SI 크기(0.008·0.5·1e-5)다. 시나리오에서 빠지면 mm 덱에 아주 작은 충격체가 만들어진다. 충격체 치수는 사용자가 꼭 주는 값이라 이번에는 그대로 둔다(보고).
- F5 는 '매니저가 쓰지 않은 키워드' 만 되살린다. 데이터 없는 `*DEFINE_CURVE` 처럼 필수 카드가 빠진 키워드도 원문대로 남는다. 예전에는 조용히 지웠고, 원래 덱도 LS-DYNA 오류다. 무엇을 남겼는지는 한 줄로 알린다(dca2d5f).
- 시험 중 실패 둘(이미 통과하던 [3]·기준 케이스)은 코드 탓이 아니었다. 19:55 호스트 메모리 고갈(NVRM out of memory, earlyoom 이 NewsKooo 워커·kube 파드를 계속 죽임) 탓이었다. 메모리를 회복한 뒤 다시 돌리니 예상한 실패만 남았다.
- 메모리 고갈의 주범은 cpptools(48.9 GB 익명 메모리)였다. 그런데 이것은 pyKooCAE 가 아니라 **KooD3plotReader** 작업 공간의 것이었다(workspaceStorage c814e896 = 색인 캐시 이름). 처음에 pyKooCAE 의 Nuitka 빌드 폴더로 오진했다. 사용자 승인(PID 명시)으로 종료만 했다. pyKooCAE 설정 파일은 만들지 않았고, 62 GB 색인 캐시도 지우지 않았다(지우면 처음부터 다시 색인). KooD3plotReader/.vscode/settings.json 의 제외 목록은 이름이 정확히 같은 폴더만 뺀다. 그래서 build_norender·.work/review/build_*·viewer/third_party·references·apptainer 가 색인에 남는다. 그 프로젝트 담당과 정할 일이다.

## 적대 리뷰 D·E 와 반영
- 리뷰 E(DWI·빌드)
  - A1 확정: 단위계 판정이 명시한 Gravity 를 무시했다. Gravity 9.81 인 SI 덱도 더미 재질 밀도 탓에 ton-mm-s 폴백을 받았다. 반대로 밀도를 못 읽는 mm 덱은 Gravity 9810 이어도 SI 폴백을 받았다. → 1de4a5a. Gravity → 밀도 → 미판정 순서다.
  - A2: 내 리뷰 요청서의 '8pi·15pi 단계 설정이 같다' 는 틀렸다. dimension_damper 를 안 주는 예제는 이제 DimensionDamper 줄이 빠진다. 다만 누적 IMPACT 템플릿은 BoundaryDistance 를 쓰지 않아 댐퍼 보 자체가 안 생기므로 덱 영향은 없다.
  - A3(근거 정정): Test_Impact_Grid5x5·Spacing5mm 은 SI 값을 준 시나리오다. 그런데 템플릿 MinimumModel 은 ton-mm-s(ρ 1.8e-9~2.8e-9, 71×147×9 mm)다. 그러니 'IMPACT 가 SI 모델에 쓰인다' 는 근거는 틀렸다. 저장소에 SI IMPACT 모델은 없다. 그 두 시나리오는 0.008 mm 충격체를 만드는 잘못된 예제다(보고). 그래도 KMM 쪽 판정은 어느 단위계 모델이든 맞게 고르므로 그대로 둔다.
  - 반영: 앞부분 재질은 충격체 재질을 물려받는다(1de4a5a). 3단 실린더 NameError(26acfeb), 도움말 문구(5242b55), 가드 정리를 늘 적용(3433f46), 배포 GLIBC 검사(b3a3cd1).
  - 남긴 것
    - KAM 배포 폴더에도 GLIBC 2.38 libcrypto·libreadline 이 있다. build_all 로 KAM 까지 다시 빌드해야 없어진다.
    - 누적 DWI 체인에서 벽·댐퍼가 단계마다 겹친다(옛 판과 같다). 라이선스가 만료돼 실제 해석으로는 검증하지 못했다.
    - DWI OutsideRigid* 산출 덱이 Run_* 아래가 아니라 모델 옆에 써진다.
    - mesh_size 가드는 실린더의 가장 큰 치수를 써서 메시가 거칠 수 있다.
    - 재질이 짝수 개일 때 중앙값은 위쪽 값으로 판정한다.
- 리뷰 D(리더·파서)
  - 확정: Ctrl-Z 를 첫 0x1A 에서 잘라, 주석·*TITLE 안 0x1A 뒤가 조용히 사라지거나 새로 죽었다. MERGE_K 가 만든 덱에서도 생겼다. → 94ecd32 에서 파일 끝에 붙은 것만 지우게 했다.
  - 반영(옛 판부터 있던 결함): *END 뒤 PARAMETER 가 앞 값을 덮음(11283e1), 매니저 재사용 초기화(db7d554), 덤프 BULK_VISCOSITY 줄바꿈(05a1911), CASE 표지를 되살리지 않음(034e268), MERGE_K 가 *END 뒤·0x1A 까지 펼침(07c3be9).
  - 남긴 것
    - 빈 두께 카드가 든 *ELEMENT_SHELL_THICKNESS 는 IndexError 로 죽는다(옛 판과 같다). LS-DYNA 에서는 '섹션 두께' 를 뜻하는 정상 카드다.
    - 매니저는 *CONTROL_MPP_IO_NODUMP 를 쓰지 못한다(비교 문자열 버그, write 메서드 없음). 지금은 원문 보존 기록기만 이 카드를 쓴다.
    - 4~5월 KMM 산출물 가운데 IGA 인클루드를 *END 째 펼친 파일은 이제 첫 *END 에서 멈추고 크게 알린다. LS-DYNA 도 같게 읽는다.
    - 데이터 없는 필수 카드(빈 *DEFINE_CURVE, 이름이 다른 두 번째 빈 *MAT_ELASTIC)는 원문대로 남는다(의도, 원래 덱도 LS-DYNA 오류).
- 3차 리뷰(F)는 위 반영분을 다시 본다.

## 3차 리뷰 F 와 반영
- 확정 6건
  1. MERGE_K 가 0x1A 대신 빈 데이터 줄을 남겼다. 다시 읽으면 크래시였고, *NODE 면 원점의 절점 0 이 조용히 생겼다. 줄바꿈 보충을 원문으로 판단한 탓이다. → f5e88ff 는 잘라 낸 본문으로 판단한다.
  2. '*END ,' 를 키워드 루프는 END 로 보는데 PARAMETER·MERGE_K 판정은 아니었다. → ff4b94a·f5e88ff 는 루프와 같은 keyword_line_name() 을 쓴다(루프는 그대로).
  3. 3단 실린더 다위치에서 26acfeb 뒤로 크래시 대신 조용히 틀린 덱이 나왔다(중간단 요소가 쌓임). DampingSpring 도 옛 판부터 같았다(FastDOE 는 중간단이 아예 빠지고, 경계 거리가 있으면 IVG·접촉이 겹침). → 7afefc5 는 아홉 곳에서 중간단을 앞부분과 똑같이 다룬다. 경계 댐퍼 대상 루프에서도 빠져 있어, 위치가 하나여도 충격체 중간단에 댐퍼가 붙을 수 있었다.
  4. 명시한 Gravity 가 뚜렷한 밀도 판정과 엇갈려도 아무 말 없이 Gravity 를 따랐다. → 94ba214 는 엇갈림을 🔴 로 알린다(순서는 Gravity 그대로).
  5. 끝의 Ctrl-Z 를 지울 때 그 앞 빈 줄(빈 카드일 수 있음)까지 지웠다. → 2993cb6.
  6. *END 뒤에서만 정의한 파라미터가 조용히 0 이 됐다(미정의 &참조에 경고가 없던 기존 결함이 드러남). → 927a00f 는 맨 위 파일 읽기 뒤에 🔴 로 알린다.
- 같이 고친 기존 결함: I10 THICKNESS 빈 두께 카드(728836e), 덤프 머리말 줄바꿈 일곱 곳(adad01a), 데이터 있는 *CASE_BEGIN 이 짝 없이 남던 것(aec40e8).
- 실수 정정: 리뷰 F 반영 커밋 셋(4380c15·bb70c89·84a374f)을 -U0 hunk 로 나눠 올리다 KooDynaKeyword.py 가 깨졌다(IndentationError, def WriteOutputFile 줄 빠짐). 푸시 전에 f5e88ff 로 되돌려 -U3 로 다시 커밋했다(2993cb6·927a00f·1ba5fde·94ba214). 그 뒤 오늘 커밋 29개의 .py 38판이 모두 파싱되는 것을 확인했다. 교훈: 같은 파일을 hunk 로 나눠 올릴 때는 커밋마다 `git show :path` 를 파싱해 본다.
- 이 호스트의 ~/.local/bin/gmsh 는 시스템 파이썬으로 돌아 충격체가 0 요소였다. 그래서 DWI 시험은 venv312/bin 을 PATH 앞에 둔다(충격체 형상까지 실제로 메시).
- 남긴 것(보고)
  - KMM 출력기는 *ELEMENT_SHELL_THICKNESS 를 쓰지 않는다. 요소별 두께가 일반 *ELEMENT_SHELL 로 바뀌며 사라진다.
  - 메인 파일은 인클루드에서 정의한 파라미터를 치환하지 못한다(이제 🔴 로 알림).
  - *PARAMETER 중복 정의는 LS-DYNA 기본(DFLAG=1, 새 정의 무시)과 달리 나중 값을 쓴다.
  - MaterialIDImpactor 재사용 + 앞부분 키 없음이면 앞부분이 표 값이 된다(재사용 재질을 물려받지 않음).
  - NUL 패딩은 지우지 않는다.

## 4차 리뷰 G 와 반영 (2026-10-24)
- 메모리: 리뷰 G 도중 KooD3plotReader 창의 cpptools 가 48 GB 가 돼 earlyoom 이 시험 프로세스를 죽였다(그 회귀 '실패' 는 코드가 아니다). 사용자 승인으로 종료하고 그 작업 공간의 C_Cpp.files.exclude 를 넓혔다. 원인은 references/external/vtk(C/C++ 33,947개)였다.
- 빈 줄 판정 근거(R16 Vol I 원문)
  - 부록 V: 기본값이 없는 칸이 있는 카드는 필수 카드라 빠지면 LS-DYNA 가 오류로 끝난다. 모든 칸에 기본값이 있는 카드만 빈 줄로 둘 수 있다. 선택 카드는 뒤 카드가 모두 생략될 때만 생략할 수 있고, 마지막 선택 카드는 빈 줄이든 생략이든 차이가 없다.
  - *NODE 카드의 NID 는 기본값이 none 이다. 빈 줄은 절점이 될 수 없다. 그런데 KMM 은 위치와 상관없이(파일 중간·*END 앞·파일 끝·Ctrl-Z 앞) 원점에 절점 0 을 조용히 만들었다(옛 판부터, 시험으로 재현). → 건너뛰고 개수를 알린다(F1 의 요소 카드와 같은 처리).
  - *DEFINE_CURVE 점 카드의 A1·O1 은 기본값이 0.0 이다. LS-DYNA 는 빈 줄을 점 (0,0) 으로 읽는다. KMM 은 ValueError 로 죽었다(옛 판부터). → LS-DYNA 와 똑같이 (0,0) 으로 읽고 알린다. 버리면 덱의 뜻을 KMM 이 바꾸게 된다.
  - Ctrl-Z 는 파일 끝 표시일 뿐이다. 그 글자와 뒤만 지우고 앞 빈 줄은 남긴다(2993cb6 그대로). 그러면 '…\n\n^Z' 는 '…\n\n' 과 같다. 리뷰 G 1번은 Ctrl-Z 탓이 아니라, 블록 끝 빈 줄을 파서가 부록 V 대로 못 읽는 옛 결함이 Ctrl-Z 파일로 번진 것이다. 그래서 파서를 고친다.
  - THICKNESS: 카드 1(EID 기본값 없음) 자리의 빈 줄은 건너뛴다. 카드 2(두께, 기본값 0=섹션 두께) 자리의 빈 줄은 기본값 카드다. 끝에서 빠진 카드 2 도 기본값이다(마지막 선택 카드 생략). 이 규칙 하나로 G5(I10 끝 빈 두께 카드 IndexError)·P1(쌍 사이 빈 줄)·G1 의 두께 경우가 함께 풀린다.
- 파라미터: R16 *PARAMETER 는 "should be placed at the beginning of the input file following *KEYWORD" 라고 권하고, LS-DYNA 는 *INCLUDE 를 그 자리에서 읽는다. 그래서 맨 위에 파라미터 파일을 인클루드하는 덱이 흔하다. KMM 은 인클루드를 메인을 다 읽은 뒤 읽어, 메인의 &thk 가 0 이 됐다. 그런데 927a00f 의 경고는 인클루드까지 읽은 뒤의 표와 대조해 그 경우를 놓쳤다(리뷰 G 3번).
  - 맨 위 파일을 읽을 때 인클루드(재귀, *END·Ctrl-Z·순환 규칙 같음)의 *PARAMETER·*PARAMETER_EXPRESSION 줄을 먼저 모아 메인 파일 줄 앞에 두고 한 번에 해석한다. *PARAMETER_LOCAL 은 그 파일 범위라 모으지 않는다.
  - 중복 정의는 해석기 규칙(나중 값)을 그대로 둔다. 메인이 정의한 이름은 메인 값이 메인 줄에 먹는 것도 지금과 같다. LS-DYNA 기본(DFLAG=1, 먼저 값)과 다른 점은 이미 남긴 항목이다.
  - 경고는 '블록에 남은 &참조 = 치환되지 않은 것' 으로 판정한다(표 대조를 뺀다). 제목·인클루드 이름 오경보(리뷰 G 4번)는 숫자 줄(모든 토큰이 수·&참조)만 세고 *INCLUDE 계열을 빼서 막는다. '1.0&thk' 처럼 앞 칸에 붙은 참조도 센다(P3).
- 확인 중 찾은 기존 결함(옛 판부터, 이번에 함께 고침)
  - MAT_ADD_EROSION: KooMaterial 가져오기가 카드 2 를 `len(dynaMaterial) > 2`(늘 2)로 골라 MXEPS 등 파괴 기준을 늘 버렸고, 카드 3~5 도 한 장씩 밀려 읽었다. 출력 덱에서 파괴 기준이 조용히 꺼졌다(1월 첫 소스 08ce963 부터). 카드 4장 이상은 파서 인덱스 실수(`curMatErosion[i][3]`)로 죽었다. R16 카드 3 은 IDAM(1번째)·LCREGD(8번째)인데 2칸만 읽었다. → 카드를 80칸 전부 읽고, 입력에서 온 카드는 원문 그대로 다시 쓴다(MID 칸만 현재 id — SECTION_BEAM 의 raw_cards 와 같은 규약). IDAM≠0 이면 R10 이전 GISSMO·DIEM 카드가 이어질 수 있어 수치 재구성으로는 담을 수 없다. 처음 3,000개 덱 가운데 이 키워드를 쓴 실제 덱은 없었다(낙하 모델은 영향 없음).
  - *SET_SHELL·*SET_SHELL_TITLE 파서가 SID 카드를 목록에 넣지 않아 첫 EID 가 SID 가 됐고, 셸 셋 기록기는 정수에 `.id` 를 불러 셸 셋이 든 덱은 출력에서 죽었다(7월 판부터 확인). 셋 요소 목록은 어디서나 EID 정수다(Solid·Beam 셋과 같음).
  - *CONTROL_ADAPTIVE: 덤프 기록기의 ADPTYP 판정이 뒤집혀(값이 있으면 무시, 비면 int('')) ADPFREQ 만 준 정상 카드가 읽는 도중 KMM 을 죽였다. 카드 2~4 를 7칸으로 읽어 8번째 칸을 잃었다. 실제 출력은 원문 보존이라 영향 없음.
  - *SET_SEGMENT(_TITLE): 블록 끝 빈 줄이 셋마다 절점 0 세그먼트를 만들었다(해석 키워드 36종 전수 점검에서 찾음). → 건너뛰고 알린다.
  - DWI DampingSpring + BoundaryDistance: RemoveOuterElement 가 공용 절점표를 이 파트가 남긴 절점으로 통째로 바꿔(RemoveComplementaryNodes), 시편 파트가 둘 이상이면 시편 절점이 *NODE 에서 빠졌다(재현: 42개 중 16개, 50개 중 20개). → 요소만 지우고, 호출부가 모든 파트를 처리한 뒤 남은 요소 어디에도 안 쓰이는 후보만 지운다. 복원 루프는 지운 것만 되돌린다.
- 전수 점검(MinimumModel_drop.k, 키워드 36종, 블록 끝 빈 줄 하나): 죽은 것 0. 바뀐 것은 SET_SEGMENT_TITLE(위 결함)과 CONTROL_SHELL 둘이다. CONTROL_SHELL 은 빈 줄을 카드 4 로 읽어 기본값(비활성·비활성·0·0·0·0·1.0)을 명시해 쓴다. R16 카드 4 기본값과 같아 뜻은 같다.
- 손대지 않은 것: DynaManager 재사용 때 ReadInputFile 은 파라미터 표(_param_resolver)를 비우지 않는다. IMPORT_MERGE 처럼 둘째 덱이 첫 덱의 파라미터를 쓰는 용도일 수 있어 그대로 둔다. DECOMPOSE_K 는 데이터 카드 없는 키워드를 되살리지 않는다(공용 기록기만 한다).
