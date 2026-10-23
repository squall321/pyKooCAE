<!-- 10-23 리뷰·릴리스에서 남은 Pre 결함 6건을 고치는 계획 -->
# 계획 — 남은 결함 정리 (2026-10-23)

사용자 지시는 "문제가 있는것들은 고쳐야 할것 같은데" 였다. 대상은 v120 보고와 노트(`docs/fix_tennodes_truncated/context-notes.md`)에 '남긴 것' 으로 적은 항목이다. 먼저 하나씩 원문·코드로 확인했고, 결함 6건과 결함이 아닌 1건으로 갈렸다.

## 고칠 것

| # | 결함 | 근거 | 고치는 규칙 | 바뀌는 덱 |
|---|---|---|---|---|
| F1 | 순수 `*ELEMENT_SOLID`·`*ELEMENT_SHELL` 레거시(8칸) 경로가 빈 줄에서 `int('')` 로 죽는다. 둘째 줄이 빈 줄이면 1줄/2줄 판별도 뒤집힌다 | 재현(리뷰 C g1_mid_blank_solid). R16 Appendix V — 빈 줄은 '기본값 카드' 인데 EID 는 기본값이 없다 | 레거시 경로에서 빈 줄을 건너뛰고 블록마다 개수를 알린다. THICKNESS 는 빈 두께 카드에 의미가 있어 손대지 않는다 | 빈 줄이 든 블록(지금은 크래시) |
| F2 | Ctrl-Z(0x1A) 줄이 데이터로 들어가 파서가 죽는다 | 재현(g1_ctrlz_noend) | 0x1A 앞까지만 읽고 그 파일을 끝낸다(DOS 파일 끝 표시) | Ctrl-Z 가 든 파일(지금은 크래시) |
| F3 | `*END` 뒤의 블록을 (마지막만 빼고) 읽어 출력의 `*END` 앞으로 옮긴다. `*END` 뒤에 놓아 꺼 둔 카드가 KMM 을 거치면 살아난다 | R16 `*END` — "Data in a keyword file beyond a *END command are not read". `*INCLUDE` — "*END terminates the include file" | 파일마다 `*END` 에서 읽기를 멈춘다. 뒤에 키워드가 있으면 이름과 개수를 알린다 | `*END` 뒤에 키워드가 있는 덱(LS-DYNA 처럼 읽게 됨) |
| F4 | 자기 자신(또는 A→B→A)을 인클루드하면 RecursionError 로 죽는다 | 재현(g7_cycle_inc) | 읽는 중인 파일 스택을 두고, 이미 스택에 있는 파일은 경고하고 건너뛴다. 같은 파일을 차례로 두 번 인클루드하는 것은 그대로 읽는다 | 순환 인클루드 덱(지금은 크래시) |
| F5 | 데이터 카드가 없는 정상 키워드(`*CONTROL_MPP_IO_NOD3DUMP`·`*CONTROL_MPP_IO_NOTIEDIO`·`*LOAD_SEGMENT_ALE_INI` 등)가 출력에서 빠진다 | R16 원문 "This keyword has no input parameters/data cards". 리뷰 C 관찰 | 리더가 '빈 키워드' 이름을 따로 모은다. 공용 원문 보존 기록기가 해석하지 않은 것만 키워드 줄로 쓴다. 파서에는 빈 블록을 주지 않는다 | 데이터 없는 미해석 키워드가 든 덱(출력에 그 줄이 생김) |
| F6 | 빌드 컨테이너의 LD_LIBRARY_PATH 에 지난 배포 폴더(`/opt/SmartTwinPreprocessor/lib/KooMeshModifier`)가 있다. 그래서 Nuitka 가 GLIBC 2.38 libcrypto·libssl·libreadline 을 새 배포에 다시 넣는다(순환 오염). 2.35 환경에서는 `import ssl` 이 죽는다 | 컨테이너 안 ldd·`python3.12 -c 'import ssl'` 실측. LD_LIBRARY_PATH 를 빼면 OpenSSL 3.0.2 로 정상 | 빌드용 재실행(KCR_IN_BUILD_SANDBOX) 에서 LD_LIBRARY_PATH 의 `/opt/SmartTwinPreprocessor/...` 항목과 빈 항목을 뺀다 | 배포 폴더의 해당 .so 가 2.35 호환판으로 바뀜 |
| F7 | DWI 러너가 댐퍼(E·ν·ρ·치수)와 충격체 앞부분(E·ν·ρ)을 넘기지 않는다. 그래서 mm 덱에 KMM 의 SI 폴백(댐퍼 E 1e10·ρ 1000·치수 0.001, 앞부분 E 2.07e11·ρ 7800)이 들어간다 | 메모리 dwi-sif-path-units, KMM `_warn_dwi_fallback` 경고 | 폴백값을 ton-mm-s 로 환산해 명시한다(댐퍼 E 1e4·ρ 1e-9·ν 0.3·치수 1.0 mm, 앞부분은 충격체 재질). 시나리오에 값이 있으면 그것을 쓴다. `impactor.mesh_size` 가 있으면 MeshSize 로 넘긴다 | DWI 덱의 댐퍼·앞부분 재질 카드 |

## 고치지 않는 것

- `ElementSolid.write` 가 `(ten nodes format)` 없이 2장 카드를 쓰는 것은 결함이 아니다. R16 `*ELEMENT_SOLID` 의 표준이 Card 1(EID·PID)+Card 2(N1~N10) 이고, 한 줄 형식은 '940~970 판의 옛 형식' 이다. `(ten nodes format)` 표기는 원문에 없다.
- 다음은 결정이 필요한 항목이라 코드를 바꾸지 않는다.
  - DWI 의 LS-DYNA SIF 경로(`/data/apptainers`): 라이선스가 만료돼 실행 검증을 할 수 없다.
  - KooChainRun 후처리 키 추가: 기능 추가다.
  - 방화벽 초안: 사용자 승인이 필요하다.
- `*ELEMENT_SHELL_THICKNESS` I10 경로가 빈 두께 카드를 건너뛰는 것: 주기(2·3줄)가 어긋날 수 있다. 이번 범위 밖이라 시험으로 확인만 하고 따로 보고한다.

## 검증

1. 결함마다 시험을 먼저 쓴다. 옛 판(HEAD)에서는 실패하고 새 판에서는 통과하는지 본다.
2. 회귀 확인
   - 시험 23개를 돌린다.
   - MinimumModel(솔리드 43,657) 출력이 v120 과 md5 가 같아야 한다.
   - 리뷰 C 말뭉치 84덱에서 바뀐 덱이 위 표의 '바뀌는 덱' 뿐이어야 한다.
3. DWI 는 실제 KMM DWI 덱의 재질 카드(MID 28 댐퍼·앞부분)를 읽어 값으로 판정한다. rc 나 파일이 있다는 것만으로는 판정하지 않는다.
4. 배포 전에 적대 리뷰를 한다.
5. 빌드 → 배포 폴더 GLIBC 전수 확인(전부 ≤2.35) → 컴파일본 e2e → SIF v121 → tar → Drive·메일 순서로 간다. 노드 배포는 v120 과 같이 보류 상태다(VM 꺼짐).
