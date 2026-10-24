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
- 회귀(리뷰 G 반영 뒤): 시험 26개 통과(test_drop_attitude_angles 는 venv 에 pytest 가 없어 parametrize 대역으로 30개 경우 통과 — venv312 는 4월 뒤로 바뀐 적이 없어 원래 없었다), MinimumModel model_trans.k·model_dump.k md5 그대로(ec4c907d·53d24150). 말뭉치 411건(C·D·F·G 재현 덱, 옛=adf6604 이전 HEAD 코드): 같음 350, 다름 61 — 새로 죽는 것 0, 고쳐진 크래시 18, 둘 다 실패 1(3카드 THICKNESS, 기존 결함), 바뀐 42건은 모두 이번 수정 범주(빈 줄·MERGE_K 줄 나누기·인클루드 파라미터·CASE·CONTROL_ADAPTIVE 덤프·SET_SHELL_TITLE). 배포판 v120 바이너리로 새 시험을 돌리면 44건 중 39건 실패(5건은 v120 뒤에 생긴 회귀라 v120 에는 없음).

## 5차 리뷰 H 와 반영 (2026-10-24)
- 메모리: 넓힌 제외 설정으로 다시 뜬 cpptools 도 1시간 19분에 25.7 GB, 2시간 24분에 42 GB 였다(earlyoom 이 다른 프로세스를 종료하기 시작). 사용자 승인으로 종료하고 그 작업 공간을 Tag Parser 로 바꿨다(백업 settings.json.bak_20261024b).
- 확정 6건
  1. (3dd79ae 회귀) 인클루드의 *PARAMETER_EXPRESSION 이 메인의 평문 *PARAMETER 를 이겼다. 해석기는 평문 값을 읽는 즉시, 식은 다 읽은 뒤 정하므로 한 번에 넘기면 위치와 상관없이 식이 이긴다. → 미리 읽은 정의에서 메인이 정의한 이름을 빼고(메인 값이 이김 — 이번 라운드 전 동작), 인클루드끼리는 먼저 정의만 남긴다(R16 *PARAMETER_DUPLICATION 기본 DFLAG=1 "ignore the new definition"). 이름·값은 해석기의 줄 해석을 그대로 쓴다(_param_definitions).
     - 주의: LS-DYNA 는 읽는 차례로 먼저 정의를 쓰므로, 맨 위 인클루드가 먼저 정의한 이름은 LS-DYNA 에선 인클루드 값이다. KMM 은 '메인 값이 이김' 을 유지한다(파일 안 중복도 나중 값 — 이미 남긴 DFLAG 항목).
  2. (40c4eab 가 드러냄) 셸·솔리드 셋의 빈 칸이 0 으로 들어가, IMPORT_MERGE_K 의 OffsetID 가 0+offset 을 실제 EID 로 만들었다(SET_SOLID 는 원래부터). → 빈 칸·0 은 건너뛴다(SET_BEAM 과 같음). 출력의 셋 마지막 카드에 0 이 더는 채워지지 않는다(뜻은 같음).
  3. (40c4eab 가 드러냄) 같은 SID 의 *SET_SHELL·*SET_SOLID 가 사전 하나에 담겨 하나가 사라졌다. R16 *SET 서두 "Each set type must have a unique numeric identification" 이라 SID 는 종류마다 따로다. → 요소 셋 사전 키를 (종류, SID) 로 바꿨다(element_set_key — Create*Set 다섯 곳과 ImportMerger 다시 키 매기기). SID 로 셋을 직접 찾아 읽는 곳은 없었다.
  4. (3dd79ae 불완전) *PARAMETER_NOECHO·_MUTABLE·_EXPRESSION_NOECHO 등 LOCAL 이 아닌 변형을 미리 읽지 않았다. → LOCAL·DUPLICATION 만 뺀다. 인클루드 이름에 &참조가 있으면 미리 읽기는 치환 전 이름을 봐 못 찾는다(드묾, 🔴 는 남).
  5. (3dd79ae, 진단) 숫자 줄 규칙 때문에 글자 칸이 있는 카드(*DEFINE_TRANSFORMATION 'TRANSL &dx' 등)의 미치환 참조를 알리지 않는다. 고치지 않는다 — 그런 카드는 원문 보존이라 &dx 가 덱에 남아 LS-DYNA 가 입력 단계에서 멈춘다(값이 조용히 바뀌지 않음). 제목 오경보를 막는 쪽이 낫다고 봤다.
  6. (96ba149 불완전) 빈 줄만 든 THICKNESS 블록이 덤프에서 죽었다. → 빈 블록은 건너뛴다. 같은 기록기의 N5 공백 int('') 도 막았다.
- 함께 고친 기존 결함(옛 판부터)
  - *ELEMENT_MASS(·_NODE_SET) 기록기가 MASS 를 8칸(17~24열, 유효숫자 3자리)에, PID 를 25~32열에 썼다. R16 은 MASS 17~32열(16칸)·PID 33~40열이다. KMM 리더(R16 대로 [8,8,16,8])가 자기 출력을 다시 읽으면 질량 요소를 잃었다 → 누적 체인 2단계부터 점 질량이 사라질 수 있었다(1월 첫 소스부터). 16.8e 로 쓴다. Examples 의 .k 51개에는 이 키워드가 없었다.
  - THICKNESS: 요소 하나짜리 블록을 일반 셸로 읽어 죽었다(가져오는 쪽이 thickness=True 를 넘긴다). 8절점 3카드 형식은 카드 3(4칸)에서 두께 8개를 읽어 IndexError 였다(카드 2 의 4개 + 카드 3 의 4개). 절점 칸이 공백이면 int('') 로 죽었다 — 일반 *ELEMENT_SHELL 도 80칸까지 공백으로 채운 줄(N5~N8 공백)에서 죽었다(KooDynaInt 로 바꿈).
- 남긴 것(보고)
  - IMPORT_MERGE_K 의 커브 오프셋이 .id 로 계산돼(커브는 .lcid) 0 이다 → 가져온 커브 7 이 기준 커브 7 을 덮는다. 오프셋만 고치면 가져온 재질의 커브 참조(ImportMerger 는 MAT·EOS 를 건드리지 않음)가 거꾸로 기준 커브를 가리키게 돼, 참조까지 함께 옮기는 설계가 필요하다.
  - DECOMPOSE_K 는 *SET_SHELL·*SET_SOLID 를 어느 파일에도 쓰지 않는다(옛 판부터).
  - DWI BoundaryDistance 는 지운 요소 위 절점 가운데 *ELEMENT_MASS(PID 0)·*SET_NODE·*BOUNDARY_SPC_NODE 만 참조하는 것도 지운다(옛 판은 자유 절점까지 지워 더 나빴다).
  - 보존 인클루드의 파라미터가 메인 원문 블록에 숫자로 박힌다(그 파일을 DOE 로 갈아 끼우면 메인은 따라가지 않음). *DEFINE_CURVE 블록 끝 빈 줄은 (0,0) 점이 된다(부록 V 근거, 실행 확인은 라이선스가 없어 못 함). 쉼표형 *SECTION_SHELL 두께·쉼표형 MAT_ADD_EROSION MID 가 0 이 되는 것, 제목이 '&x' 하나뿐인 *PART 오경보, 주석 안 홀로 쓴 CR 은 옛·새 같다.

## 6차 리뷰 I 와 반영 (2026-10-24)
- 파라미터(확정 C1~C4): 리뷰 H 반영의 '메인 값 우선·인클루드끼리 먼저 값' 이 R16 규칙을 반만 따라, DFLAG=2·4(새 정의 채택)·MUTABLE(재정의 허용)·중첩 인클루드 순서에서 틀렸고 메인 카드와 인클루드 카드 값이 엇갈렸다.
  - R16 원문: *PARAMETER 정의는 "visible and available at any later point in the input processing"(읽는 차례). *PARAMETER_DUPLICATION DFLAG 1=경고 후 새 정의 무시(기본), 2=경고 후 새 정의 채택, 3=오류·무시, 4=조용히 채택, 5=조용히 무시. MUTABLE: "Redefinition is allowed regardless of the setting of *PARAMETER_DUPLICATION"(첫 정의에 붙어야 함). 매뉴얼의 LOCAL 예제는 인클루드가 VAL1 을 10.0 으로 다시 정의하면 받아들인다고 적어 DFLAG 기본과 어긋나 보인다 — DFLAG 표를 따랐다.
  - → 인클루드의 정의를 그 *INCLUDE 자리에 끼워(중첩도 제자리) 읽는 차례대로 해석기에 주고, 해석기(_accept)가 처음 정의를 받고 재정의는 첫 정의가 MUTABLE 이거나 DFLAG 2·4 일 때만 받는다. 값이 다른 재정의를 버리면 알린다. 덱마다 이 상태를 새로 시작한다(ResetDuplicateState — 값 표는 예전처럼 이어 둠).
  - 바뀌는 것: 메인 파일 안 중복도 이제 먼저 정의가 남는다(예전 나중 값 — 남겼던 DFLAG 항목이 풀림). 맨 위 인클루드가 먼저 정의한 이름은 인클루드 값이다(리뷰 H 반영의 '메인 우선' 을 R16 대로 뒤집음). KMM·KooChainRun 이 전역 *PARAMETER 를 덧붙여 값을 덮는 곳은 없다(IGA 의 LOCAL 생성뿐).
  - 남는 근사: 값은 이름마다 하나다. MUTABLE·DFLAG 2 로 덱 중간에 값이 바뀌면 LS-DYNA 는 바뀌기 전 카드에 옛 값을 쓰지만 KMM 은 한 값만 쓴다.
- C5(de57d98 회귀): 절점 칸을 KooDynaInt 로 바꾸자 첫 줄이 88자 이상(80열 뒤 공백·주석)인 블록에서 9번째 빈 칸까지 절점으로 들어가 8절점 셸이 조용히 빠졌다(예전엔 크래시). → N1~N8 만 쓴다(80열 뒤는 LS-DYNA 도 안 읽음).
- C7(기존 결함): PID 칸이 빈 *ELEMENT_MASS 행을 int('') 에서 조용히 버렸다. R16 PID 는 생략 가능한 칸이다 → 0. MASS 빈 칸은 0.0, 못 읽는 행은 알린다.
- 개연 반영: THICKNESS 블록이 더는 죽지 않으면서 요소별 두께가 출력에서 조용히 빠졌다 → 가져올 때 ⚠️ 로 알린다(출력기 미지원은 남긴 항목).
- 남긴 것: C6 IMPORT_MERGE_K 에서 같은 종류·같은 SID 셋이 기준 셋을 덮는다(elem_set_sid 오프셋이 파트별 매니저에서 세어 늘 0, 접촉의 요소 셋 참조도 옮기지 않아 오프셋만 고치면 참조가 깨짐 — 커브와 같은 설계 과제). 모든 원소가 지워진 셋이 출력에서 빠지는 것(예전엔 0 채움이 있으면 남았음 — 그 셋을 참조하는 카드가 있으면 어긋남). THICKNESS 모드를 행 길이로 다시 추측하는 구조(I10 카드 1 길이가 요소마다 다르거나 4·8절점이 섞인 블록은 죽음, 옛 판도 같음).

## 릴리스 번호 (2026-10-24)
- 이번 굽기는 v124 다. v121·v123 은 KooRemapper 세션이 KooRemapper 만 바꿔 구웠다(v123 = 06:13~06:23, KooRemapper 5ff6f6e1·f111752, SIF sha256 f3242218). 헤드 /opt/apptainers 도 06:24 에 그 사본으로 바뀌었다(그쪽 세션 작업).
- v120~v123 tar 4개가 바이트까지 같은 것은 정상이다. tar 는 SIF 소스 트리 appt313/opt/SmartTwinPreprocessor(KMM·KAM·KCR)만 묶고 KooRemapper 는 묶지 않는다. 그 트리는 v120 빌드(10-23 10:59·11:08) 뒤로 바뀌지 않았다. v124 tar 는 이번 빌드 5단계가 그 트리를 갈아 끼우므로 달라야 한다 — 다르지 않으면 빌드가 트리를 못 바꾼 것이다.
- 헤드 /opt/SmartTwinPreprocessor 는 빌드가 손대지 않는 2월 사본이다. 바이너리 확인은 NFS(/data/SmartTwinPreprocessor)와 SIF 소스 트리를 cmp 로 맞춘다.

## 7차 리뷰 J 와 반영 (2026-10-24)
- 확정 회귀(22b6e4b, 내 리뷰 I 반영)
  1. 인클루드의 전역 식이 그 파일의 LOCAL 을 쓰면 0 이 됐다(중복 없는 덱, 기본 TRANSFORM 경로 — IGA 자동 보존 판정이 대문자 '*PARAMETER_LOCAL' 글자만 찾아 NOECHO_LOCAL·소문자는 인라인으로 읽힌다). 메인 해석에 끼워 넣을 때 LOCAL 을 빼 식이 못 셈 → 그래도 정의로 등록 → 인클루드를 다시 읽을 때 같은 글이라 거절.
  2. MUTABLE·DFLAG 2 로 식을 재정의하면 그 사이 식이 나중 값으로 셈(식을 파일 끝에 몰아 셌다).
  3. DFLAG 2·4·MUTABLE 에서 재정의 앞 카드가 나중 값을 받음(파일을 통째 한 표로 치환).
  4. *PARAMETER_EXPRESSION_LOCAL 을 전역으로 분류(앞부분 글자 판정 순서) — 거짓 중복 경고·값 바뀜.
- 예전부터: 매뉴얼 형식('R thk 1.0') LOCAL 줄을 통째 무시(붙인 형식 첫 쌍만 읽음), 인라인 인클루드의 LOCAL 이 형제 인클루드로 샘, MUTABLE 문자형 재정의 허용, 같은 파일 LOCAL 두 번이면 나중 값, DFLAG 3 을 보통 경고로, 재정의 경고가 두 번(메인 끼워 읽기·인클루드 다시 읽기).
- 원인은 하나다 — 리더는 인클루드를 메인 다음에 읽고 파일을 한 표로 치환한다. 인클루드 정의를 끼워 넣어도 '파일마다 한 표' 구조로는 R16 의 읽는 차례(정의 뒤 카드만 새 값, LOCAL 은 파일이 끝나면 사라짐, 식은 그 자리 값)를 나타낼 수 없다. 리뷰 G→H→I→J 로 땜질이 매번 새 회귀를 낳았다.
- 설계(반영): 맨 위 파일을 읽을 때 덱을 LS-DYNA 처럼 한 번 훑는다(_param_walk — 인클루드는 그 *INCLUDE 자리에서 깊이 우선으로 들어감, *END·Ctrl-Z·순환·없는 파일 규칙은 리더와 같음). 해석기는 파일마다 LOCAL 범위를 열고 닫고(BeginFile/EndFile), 정의를 받는 즉시 식을 그때 보이는 값으로 센다. 줄마다 그 자리에서 보이는 값으로 치환한 결과 중 바뀐 줄만 파일마다 계획 {줄 번호: (원문, 치환문)} 으로 남긴다. 리더는 블록 차례를 바꾸지 않고(출력 차례 그대로) 각 파일을 읽을 때 그 계획을 쓴다. 같은 파일을 두 번 넣으면 계획도 두 개 — 리더도 같은 깊이 우선 차례로 읽으므로 실경로별 줄 세우기로 맞는다. 리더가 읽지 않는 보존 인클루드(IGA·사용자 패턴·*PreserveIncludes)도 정의는 훑지만 계획은 만들지 않는다(조상이 하나라도 보존이면 마찬가지). 보존 판정은 리더와 같은 함수(_include_passthrough_reason)로 한다. 원문이 계획과 다르면 덱 끝 값으로 통째 치환하고 알린다. 훑기가 죽으면 파일마다 그 파일 정의로만(예전 방식) 치환한다.
- 앞 참조(정의보다 앞 줄에서 쓴 &참조): LS-DYNA 라면 정의 전이라 오류지만 예전 KMM 은 파일 한 표로 받아 줬다. 회귀를 피하려고 그 파일 끝 값, 그래도 없으면 덱 끝 값을 넣고 '정의보다 앞 줄에서 썼다' 고 알린다. 미뤄 둔 식도 참조가 정의되는 자리에서 센다.
- 판단 P1(R16 안의 어긋남): DUPLICATION 표는 기본 DFLAG=1(새 정의 무시)인데 *PARAMETER Remark 5 예제는 카드 없이 file1 의 VAL1 재정의를 받아들인다("after returning from file1, we will see VAL1 = 10.0"). 표를 따른다 — MUTABLE("may be redefined at some later point … regardless of *PARAMETER_DUPLICATION")은 기본이 재정의를 받지 않을 때만 쓸모가 있고, 예제는 DUPLICATION·MUTABLE 이 생기기 전 글로 보인다. 실측은 라이선스가 끊겨 못 했다. 지난 LS-DYNA 로그 10,507개(d3hsp·messag)에서 재정의 경고를 찾았으나 0건이라 근거가 없다. 재정의를 버리면 경고가 나므로 사용자가 볼 수 있다. 바꿀 곳은 해석기 _redefine_ok 하나다.
- 판단 P2: 바깥 파일의 LOCAL 은 안쪽 파일이 나중에 같은 이름 전역을 정의해도 계속 가린다(Remark 5 의 file2 가 file1 LOCAL 을 보듯 — "LOCAL variables can temporarily mask non-LOCAL variables"). 그래서 K2(메인 LOCAL a=5, 인클루드 전역 a=1, b=a*2)는 인클루드 카드가 5.0·10.0, U(메인 EXPRESSION_LOCAL t=2, 인클루드 t=5)는 2.0 이다. 그 전역 정의 자체는 중복이 아니라 받는다(가려져 보이지 않을 뿐).
- P3(6648032): PID 칸이 미치환 &참조인 *ELEMENT_MASS 행은 PID 0 으로 남는다. 🔴 미치환 경고가 "그 칸은 0 으로 읽힌다" 고 이미 알려 그대로 둔다.
- P4: 문자 파라미터로 쓴 *INCLUDE 파일 이름도 이제 따라간다(그 자리 값으로 치환한 이름).
- 남긴 것: *PARAMETER_EXPRESSION 이어 쓰기(첫 10칸 공백 줄 — 지금은 무시돼 앞 줄만으로 셈, 예전부터), 정수 나눗셈(R16 "2/5 becomes 0" — KMM 은 모두 실수, 예전부터), '&TST^' 구분자 문자열, 문자형 값 안 공백, 쉼표형 *ELEMENT_MASS(이제 알림)·*ELEMENT_SHELL(크래시, 예전부터), IGA 자동 보존이 대문자 '*PARAMETER_LOCAL' 글자만 보는 것(이제 인라인으로 읽혀도 값은 맞다).
- 반영 커밋 f8fe5a0. 같은 날 8cde1f0: 훑기가 인클루드를 io.StringIO(글).readlines() 로 나눴는데, StringIO 는 안에서 글자당 4바이트 버퍼를 만들어 217 MB 글에 추가 정점 1,332 MB(줄 목록만이면 463 MB)였다. MERGE_K 의 _strip_keyword_end(리뷰 G)도 같았다. 공용 split_lines_keepends('\n' 에서만 나눔)와 f.readlines() 로 바꿨다 — 무작위 2만 개 글(FF·VT·\x1c~\x1e·\x85· ·CR·Ctrl-Z 포함)·보존 판정 3천 개 대조로 같음을 확인했다.
- 회귀: 시험 28개 통과(새 시험 81건), MinimumModel md5 그대로(ec4c907d·53d24150). 말뭉치 664건(C·D·F·G·H·I·J 재현 덱, 옛=60c7058): 같음 641, 바뀜 23 — 리뷰 J 사례 22(전부 R16 값 쪽: M 2→1, N4 c 11→7, U2 5→2, Y2·Y3·Y4 0→4 등)와 H_t3(문자 파라미터로 쓴 인클루드 이름 안의 thk 가 0→2.5, 🔴 미치환 경고 사라짐). rc 가 바뀐 덱·새 크래시 0.
- 빌드 사고 방지: v123 빌드(10:04)가 도는 중에 소스를 고쳐, 설치 단계(NFS·SIF 소스 트리) 전인 11:09 에 scope 를 멈췄다(rc 143, NFS 는 v120 판 그대로). KMM 은 2.35 컨테이너에서 정상 빌드됐고 최저 가용 메모리는 34 GB 였다.

## 8차 리뷰 K 와 반영 (2026-10-24)
- 훑기 계획과 리더가 읽는 파일이 어긋나는 사례는 없었다(심볼릭 링크·보존 패턴 한쪽만·IGA 보존 파일 안 인클루드·CRLF·CR·같은 파일 두 번·49단 중첩·*END·Ctrl-Z·쉼표형/소문자 *INCLUDE·순환·없는 파일). 실제 덱 26개 리더 덤프는 옛(dced5fd)·60c7058·8cde1f0 이 같고, 다른 것은 아래 K3 의 IGA 덱 4개다.
- 확정 반영
  - K1(메모리) — 8cde1f0 으로 이미 고침을 리뷰가 실측했다(513 MB 인클루드: 1.70 GB, 고치기 전 3.60 GB, 60c7058 1.74 GB).
  - K2: 정수 식 결과가 inf·nan 이면 정수 바꿈 예외가 평가의 try 밖이라 훑기와 대비 경로가 함께 죽어 그 파일의 &참조가 하나도 치환되지 않았다 → 그 식만 평가 실패로 둔다.
  - K3: 쉼표형 식 줄(R16 EXPRESSION Remark 1 예제 'rplot,term/(states-30)', 사용자 IGA 덱의 'rxminn, &xmin-&rr')의 이름을 'plot,' 으로 받아 조용히 미치환이었다(옛 판은 구문 오류 경고라도 냈다) → 이름부를 쉼표에서 가른다. iga_part_01.k 의 xminn 등 6개가 0 대신 -0.65·1.65 가 된다(xmin -0.05 - rr 0.6).
  - K4(예전부터): R16 Card 1 그대로 쓴 고정폭 여러 쌍(값 10칸 오른쪽 맞춤 뒤에 다음 PRMR 이 붙음 — 'R thk            1.0R w')을 thk='1.0R' 로 받아 무경고로 0 이었다 → 숫자 뒤에 붙은 형 글자에서 가른다.
- 판단 항목 반영(LS-DYNA 라면 오류인 앞 참조 덱 — 예전 KMM 처럼 너그럽게, 다만 정의 자리 범위로)
  - 미뤄 둔 식은 정의 자리의 범위 사슬을 들고 다닌다 — 나중에 풀릴 때 다른 파일(안쪽 인클루드)의 LOCAL 을 쓰지 않는다(P3: 옛 판과 같은 a=2.0). 풀리면 '정의보다 뒤에 나온 값으로 셌다' 고 알린다.
  - 파일이 끝나도 그 파일의 미뤄 둔 LOCAL 식을 버리지 않는다 — 덱 끝까지 참조가 정의되면 그 파일의 앞 참조 줄을 그 자리 범위로 채운다(P2: 옛 판과 같은 h=2.0). 앞 참조 줄도 그 자리의 범위 사슬을 들고 다닌다.
  - 값이 안 나온 식은 이름을 차지하지 않는다 — 뒤의 정상 정의가 첫 정의가 된다(P4).
  - 인클루드 파일 이름 줄은 글자 수에 매이지 않게 치환한다(F5 — 뒤 공백 없는 '&fn' 에 긴 이름이 미치환돼 인클루드가 빠졌다). 이름의 참조가 그 자리에서 정의 전이라 파일이 없으면 까닭을 알리고 읽지 않는다(P1 — LS-DYNA 도 못 읽는다, 옛 판은 파일 한 표로 읽어 줬다). 파일 판정은 리더와 같은 exists(P5 — /dev/null).
  - 평문 *PARAMETER 값의 &참조는 그 자리 값으로 받는다(P7 — R16 "referenced anywhere", 출력 원문 블록과도 맞음). 식은 원문으로(&a 를 글자로 바꾸면 -3**2 처럼 우선순위가 바뀐다).
- 그대로 둔 것: P8 안쪽 파일 LOCAL 이 바깥 LOCAL 과 같은 이름이면 DFLAG 1 로 무시(DUPLICATION Remark 1 "a LOCAL that masks another LOCAL … will" 문자 그대로 — 옛 판은 안쪽 값). P6 성능은 모든 줄에 & 가 있는 300만 줄에서 KMM 전체 +17%(정점 같음), 못 푼 참조 검사는 & 가 남은 줄에만 한다. preserve_includes=True 는 보존 인클루드도 훑기가 통째로 읽는다(그 플래그는 코드 어디서도 켜지 않는다).
- 범위 밖(모든 판 같음): 식 의미(-3**2, 2/5 정수 나눗셈, sign·csc 등 함수 없음, 이어 쓰기), '-&' 부호 바꾸기, 문자형 '^' 구분자, 인라인 인클루드의 *_LOCAL 블록이 메인 원문으로 옮겨지는 출력 배치·DECOMPOSE 출력에서 식이 그 참조의 정의 인클루드보다 앞에 오는 것, 읽기 권한 없는 인클루드 PermissionError.

## 사용자 결정 (2026-10-24)
- P1 DFLAG 기본: DFLAG 표대로(재정의 무시 + 경고) 유지 — Remark 5 예제 쪽으로 바꾸지 않는다.
- 헤드 /opt/apptainers 를 v124 로 교체(v123 은 하드 링크 백업 SmartTwinPreprocessor_backup_20261024_193908.sif).
- KooD3plotReader 창의 C/C++ IntelliSense 는 꺼 둔 채 둔다("C_Cpp.intelliSenseEngine": "disabled").
