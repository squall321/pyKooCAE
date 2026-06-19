# KooMeshModifier 모드: MERGE_K

## 1. 목적 / 개요

`MERGE_K` 는 입력 모델에 흩어져 있는 모든 `*INCLUDE` 파일을 **인라인(펼침)** 하여 단일 `.k` 파일 하나로 합쳐 출력하는 모드다. `DECOMPOSE_K` 의 역방향 동작이다.

- 일반 `*INCLUDE` 는 모델 파싱 단계에서 이미 메인 모델로 인라인되므로, 본문(`WriteStreamDynaKeyword`)에 자동으로 합쳐진다.
- `*PARAMETER_LOCAL` 스코프나 IGA 카드(`*IGA_`, `*SECTION_IGA_`) 등은 안전을 위해 인라인하지 않고 별도 passthrough 로 보관되었다가, 출력 시 `*INCLUDE` 참조 형태로 **보존**된다.
- 핵심 안전 규칙: `*PARAMETER_LOCAL` 이 포함된 include 는 옵션과 무관하게 **항상 보존**된다(스코프 깨짐 방지).

> 주의: `IMPORT_MERGE_K`(외부 .k 를 현재 모델에 import-병합)와는 별개 모드다. `MERGE_K` 는 "한 모델 안의 include 들을 단일 파일로 합치는" 동작이고, `IMPORT_MERGE_K` 는 "다른 모델을 끌어와 ID 오프셋 후 합치는" 동작이다. 파서가 substring 충돌을 피하려고 `import_merge_k` 를 `merge_k` 보다 먼저 검사한다 (KooMeshModifier.py:330-336).

## 2. 입력 옵션 · 인자 (표)

입력 트리거: `*Mode` 블록에 `merge_k,<modeID>`, 옵션 블록 헤더는 `**MergeK,<modeID>`.

| 옵션 | 형식 | 기본값 | 의미 | 근거 (file:line) |
|---|---|---|---|---|
| `OutputFile` | `OutputFile,<name.k>` | `<입력 basename>_merged.k` | 병합 결과 출력 파일명 | KooMeshModifier.py:2417-2418 / KooKFileMerger.py:27-31 |
| `ForceInlineIGA` | `ForceInlineIGA,True\|False` | `False` | IGA 자동 보존된 include 도 강제 인라인 (단 `*PARAMETER_LOCAL` 있으면 무시) | KooMeshModifier.py:2419-2420 / KooKFileMerger.py:23, 66-68 |
| `ForceInlinePreserved` | `ForceInlinePreserved,True\|False` | `False` | 사용자 지정 보존(`*PreserveIncludes` 패턴) include 도 강제 인라인 (단 `*PARAMETER_LOCAL` 있으면 무시) | KooMeshModifier.py:2421-2422 / KooKFileMerger.py:24, 59-64 |

- 옵션 키는 대소문자 무시(`line.lower()`)로 비교되며, 알 수 없는 라인은 경고 후 무시된다 (KooMeshModifier.py:2416-2424).
- `**MergeK` 블록은 빈 줄과 `$` 주석 줄을 건너뛰며 `**End` 또는 EOF 까지 읽는다 (KooMeshModifier.py:2407-2414). 블록 끝에 `**End` 마커를 넣는 것이 안전하다.
- 관련 전역 카드: `*PreserveIncludes` 블록으로 보존 대상 include 패턴(basename glob 또는 절대경로)을 등록할 수 있다 (KooMeshModifier.py:205-233). 이 패턴은 `dynaManager._preserve_include_patterns` 에 저장되어 MERGE_K 분류에 사용된다.

## 3. 사용 예제

> 전용 예제 없음 — `Examples/` 에 `merge_k` / `**MergeK` 입력 파일이 존재하지 않는다 (grep 결과 0건). 아래는 코드 근거(KooMeshModifier.py 입력 파서 + 다른 모드 입력 파일 구조)로 구성한 최소 예시다. 확인 필요.

KooMeshModifier 입력 `.k`(텍스트) 파일 형식. 구조는 `Examples/alldropangles/drop_attitude.txt` 의 입력 헤더 관례를 따른다.

```text
*Inputfile
model_with_includes.k
*Mode
merge_k,1
**MergeK,1
OutputFile,model_all_in_one.k
ForceInlineIGA,False
ForceInlinePreserved,False
**End
```

선택적으로 특정 include 를 보존 대상으로 명시하려면 `*PreserveIncludes` 블록을 추가한다:

```text
*Inputfile
model_with_includes.k
*PreserveIncludes
*.iga.k
materials_local.k
*Mode
merge_k,1
**MergeK,1
OutputFile,model_all_in_one.k
**End
```

- `ForceInlinePreserved,True` 를 주면 위 `*PreserveIncludes` 로 지정한 파일도 인라인된다(단 `*PARAMETER_LOCAL` 포함 시 여전히 보존, KooKFileMerger.py:50-54).

## 4. 동작 원리 (코드 근거)

1. **입력 트리거 등록**: `*Mode` 블록에서 `merge_k` 가 매칭되면 `modeList` 에 `"MERGE_K"` 추가 (KooMeshModifier.py:334-336). `import_merge_k` 는 substring 충돌 방지로 먼저 검사된다 (KooMeshModifier.py:330-336).
2. **옵션 블록 파싱**: `**mergek` 헤더에서 `OutputFile` / `ForceInlineIGA` / `ForceInlinePreserved` 를 읽어 `modeIDOption[modeID]` 에 저장 (KooMeshModifier.py:2402-2425).
3. **dispatch**: 실행 시 `mode == "MERGE_K"` 분기에서 `GenerateMergeK(modeid)` 호출 후 `_skip_default_write = True` 설정 → 공용 `WriteModifiedFile` 을 건너뛴다(자체 출력) (KooMeshModifier.py:2867-2869, 2883-2884).
4. **위임**: `GenerateMergeK` → `advancedModification.MergeK(curOption, self.curDir, self.inputFileName)` (KooMeshModifier.py:2439-2441) → `KooKFileMerger.merge_k_file(...)` (KooDynaAdvancedModification.py:5062-5065).
5. **passthrough 분류** (KooKFileMerger.py:43-74):
   - `dynaManager._include_passthrough_data` 의 각 entry(`{"file":..., "content":...}` 구조, KooDynaKeyword.py:11598-11600)를 순회.
   - `*PARAMETER_LOCAL` 포함 → 무조건 `preserved_entries` (KooKFileMerger.py:49-54).
   - 사용자 패턴(`_preserve_include_patterns`) 매칭 → `ForceInlinePreserved` 면 인라인, 아니면 보존 (KooKFileMerger.py:59-64).
   - 그 외(IGA 자동 보존) → `ForceInlineIGA` 면 인라인, 아니면 보존 (KooKFileMerger.py:65-70).
6. **출력 작성** (KooKFileMerger.py:77-108):
   - `*KEYWORD` + `WriteStreamDynaKeyword()`(이미 인라인된 본문) 기록.
   - `inline_entries`: `$$ ----- Inlined from <base> -----` 헤더 후 content 를 그대로 펼침. `*KEYWORD` / `*END` 줄은 `_strip_keyword_end` 로 제거 (KooKFileMerger.py:83-88, 130-141).
   - `preserved_entries`: `*INCLUDE` 카드 + basename 을 기록하고, 원본 파일을 출력 폴더(`cur_dir`)로 `shutil.copy2` 복사 (KooKFileMerger.py:91-101).
   - 파싱 못 한 키워드는 `_write_uninterpreted_raw_blocks` 로 raw text 보존(손실 방지) (KooKFileMerger.py:104, 144-167).
   - 마지막에 `*END`.
7. **출력 경로**: `os.path.join(cur_dir, output_file)` (KooKFileMerger.py:33). 완료 로그 `[MERGE_K] 출력 완료: <output_path>` (KooKFileMerger.py:108).

## 5. 주의사항 · 한계

- **`*PARAMETER_LOCAL` 은 절대 인라인 안 됨**: `ForceInlineIGA` / `ForceInlinePreserved` 를 켜도 보존된다. 켠 상태에서 해당 include 가 있으면 경고를 출력한다 (KooKFileMerger.py:50-54).
- **모드명 substring 충돌**: 모드 매칭이 `if "merge_k" in svector[0].lower()` 방식이라 `import_merge_k` 와 겹친다. 코드가 명시적으로 `import_merge_k` 를 먼저 검사하여 회피한다 (KooMeshModifier.py:330-336). 새 모드명 추가 시 주의.
- **빈 줄 처리**: `**MergeK` 블록은 빈 줄·`$` 를 skip 하고 `**End`/EOF 까지 읽는 신형 파서다 (KooMeshModifier.py:2407-2414). 구형 블록과 동작이 다르므로 블록 끝에 `**End` 마커를 권장한다.
- **기본 write 생략**: `_skip_default_write = True` 이므로 다른 모드와 출력 경로/형식이 다르다. 출력은 항상 `cur_dir` 아래 `OutputFile`(또는 `<input>_merged.k`) 단일 파일 + 보존 include 사본들 (KooMeshModifier.py:2869, 2883-2884; KooKFileMerger.py:33).
- **보존 파일 복사 위치**: 보존된 include 는 basename 으로만 참조(`*INCLUDE\n <base>`)되고 원본이 `cur_dir` 로 복사된다. 즉 출력 `.k` 와 보존 include 사본은 같은 폴더에 함께 두어야 LS-DYNA 가 찾는다 (KooKFileMerger.py:93-99).
- **전용 예제 부재**: `Examples/` 에 MERGE_K 입력 파일이 없어, 본 문서의 입력 예시는 코드 근거 기반 재구성이다(검증된 실행 산출물 아님). 확인 필요.

## 6. 개발 현황

**구현됨.**

- 근거: dispatch 분기 `MERGE_K` (KooMeshModifier.py:2867-2869), 옵션 파서 (KooMeshModifier.py:2402-2425), 위임 메서드 `GenerateMergeK`/`MergeK` (KooMeshModifier.py:2439-2441; KooDynaAdvancedModification.py:5062-5065), 실제 구현 `merge_k_file` 전체 (KooKFileMerger.py:11-167).
- 기존 매뉴얼 `dev_status.md` 에도 "MERGE_K | 구현됨 | A:5062 → KooKFileMerger.merge_k_file. git 909c7e0. M:2867/2439" 로 기재됨.
