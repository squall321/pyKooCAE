# KooMeshModifier 모드: IMPORT_MERGE_K

## 1. 목적 / 개요

`IMPORT_MERGE_K` 는 **외부 `.k` 파일을 현재 입력 모델에 끌어와 병합(import-merge)** 하는 모드다. 가져올 모델의 ID 들(PID/NID/EID/SID 등)을 기존 모델의 max ID 다음 번호로 자동 오프셋한 뒤 두 모델을 한 메모리 모델로 통합한다.

핵심 동작 (근거: `KooImportMerger.py:1-12` 모듈 docstring):

- 새 파일의 PID/NID/EID/SID/NSID/PSID/SSID/CID/DefineID 는 **기존 max + 1 부터 자동 재할당**한다.
- MID/EOSID/HGID(Add-Erosion)는 **그대로 보존**한다. 재료는 공통 DB로 취급한다.
- 기존 모델에 **없는 MID 만 새로 추가**한다(충돌 없는 병합).
- 새 파일의 `*INCLUDE` 는 모두 인라인하며, IGA passthrough 는 비활성화한다.

사용 케이스 (docstring 기준): 신규 파트를 따로 모델링한 뒤 기존 모델에 합치기, 멀티 모델 통합(조립 시뮬레이션 빌드).

> 주의: `MERGE_K`(한 모델 내부의 `*INCLUDE` 들을 단일 파일로 펼침)와는 별개 모드다. `IMPORT_MERGE_K` 는 "다른 모델을 끌어와 ID 오프셋 후 합치는" 동작이다. 파서가 substring 충돌을 피하려고 `import_merge_k` 를 `merge_k` 보다 먼저 검사한다 (KooMeshModifier.py:330-336).

## 2. 입력 옵션 · 인자 (표)

입력 트리거: `*Mode` 블록에 `import_merge_k,<modeID>`, 옵션 블록 헤더는 `**ImportMergeK,<modeID>`.

| 옵션 | 형식 | 기본값 | 의미 | 근거 (file:line) |
|---|---|---|---|---|
| `ImportFile` | `ImportFile,<경로.k>` | (없음, **필수**) | 가져올 외부 `.k` 파일 경로. 상대경로면 입력 모델의 `curDir` 기준으로 해석 | KooMeshModifier.py:2396-2397 / KooImportMerger.py:27-33 |

- 옵션 키는 대소문자 무시(`line.lower()`)로 비교되며, 알 수 없는 라인은 경고(`Warning: unknown ImportMergeK option line`) 후 무시된다 (KooMeshModifier.py:2395-2399).
- `ImportFile` 이 비어 있으면 `ValueError("[IMPORT_MERGE_K] ImportFile 옵션 필수")` 로 중단된다 (KooImportMerger.py:28-29).
- 경로 처리: 절대경로가 아니면 `os.path.join(cur_dir, import_file)` 로 결합하고, 그래도 존재하지 않으면 `FileNotFoundError` 를 던진다 (KooImportMerger.py:30-33).
- `**ImportMergeK` 블록은 빈 줄과 `$` 주석 줄을 건너뛰며 `**End` 또는 EOF 까지 읽는다 (KooMeshModifier.py:2386-2394). 블록 끝에 `**End` 마커를 넣는 것이 안전하다.

## 3. 사용 예제

> 전용 예제 없음 — `Examples/` 에 `import_merge_k` / `**ImportMergeK` / `ImportFile` 를 쓰는 입력 파일이 존재하지 않는다 (grep 결과 0건). 아래는 코드 근거(KooMeshModifier.py 입력 파서 + 다른 모드 입력 파일 구조)로 구성한 최소 예시다. **확인 필요**.

KooMeshModifier 입력(옵션) 파일 형식. 구조는 같은 `k_io` 그룹의 `MERGE_K` 예시 및 입력 파서 관례(`*Inputfile` → `*Mode` → `**<mode>` 블록)를 따른다.

```text
*Inputfile
base_model.k
*Mode
import_merge_k,1
**ImportMergeK,1
ImportFile,new_part.k
**End
*End
```

- `base_model.k` 가 기존(타깃) 모델, `new_part.k` 가 가져올(소스) 모델이다.
- 실행 후 두 모델이 통합된 단일 `.k` 가 출력된다(출력 파일명은 4절 참조).

## 4. 동작 원리 (코드 근거)

### 4.1 등록 · 디스패치 경로

1. `*Mode` 블록에서 `import_merge_k` 키워드를 만나면 `modeList` 에 `"IMPORT_MERGE_K"` 를, modeID 를 `modeIDList` 에 등록한다. `merge_k` 보다 먼저 검사하여 substring 충돌을 막는다 (KooMeshModifier.py:330-336).
2. `**importmergek` 옵션 블록 파서가 `ImportFile` 라인을 읽어 `modeIDOption[modeID]` 에 `{"ImportFile": ...}` 로 저장한다 (KooMeshModifier.py:2381-2400).
3. `GenerateModifiedFile()` 디스패치 루프에서 `elif mode == "IMPORT_MERGE_K":` 분기로 진입해 `self.GenerateImportMergeK(modeid)` 를 호출하고, 출력 접미사로 `additionalword += "_imported"` 를 누적한다 (KooMeshModifier.py:2870-2872).
4. `GenerateImportMergeK()` 는 `modeIDOption[modeid]` 옵션을 꺼내 `advancedModification.ImportMergeK(curOption, self)` 로 위임한다 (KooMeshModifier.py:2443-2445).
5. `ImportMergeK()` 는 다시 `KooImportMerger.import_merge_k(simGenerator, option)` 으로 위임한다 (KooDynaAdvancedModification.py:5067-5070).

### 4.2 병합 알고리즘 (`import_merge_k`, KooImportMerger.py:16-69)

전체 흐름은 6단계다.

1. **새 모델 별도 로드** — 새 `KooDynaImporter` 인스턴스를 만들고 (`_build_new_importer`, KooImportMerger.py:75-78), `_preserve_include_patterns = []` 와 `_disable_auto_iga_passthrough = True` 로 설정해 모든 include 를 인라인하고 IGA 자동 보존을 끈다. 그 뒤 `importDynaFile` → `importKeywordstoManager` → `SyncronizeMaxID` 로 새 모델을 메모리에 적재한다 (KooImportMerger.py:38-49).
2. **기존 모델 maxID 계산** — 기존 `dynaImporter.SyncronizeMaxID()` 후 `_compute_offsets()` 로 PID/NID/EID/SID/NSID/PSID/SSID/CID/LCID/elem_set_sid 의 max 값을 수집한다. EID 는 모든 파트(`parts` + `partsRigid`)의 `elementManager.maxID` 를 순회해 구한다 (KooImportMerger.py:51-54, 81-111).
3. **오프셋 적용** — `_apply_offsets()` 가 새 매니저들의 ID 에 offset 을 가한다. NODE/SECTION/PART/NODESET/SEGMENTSET/CONTACT/DEFINE 순으로 처리하며 **MAT/EOS/HG 는 건드리지 않는다**. 각 파트의 `elementManager.OffsetID(eid, elem_set_sid)` 는 직접 호출하고(KooPart.OffsetID 가 파트별 elementManager 를 처리하지 않는 한계 우회), PID/PSID 는 수동으로 `+= offset` 한다 (KooImportMerger.py:56-57, 114-168).
4. **dict re-key** — `OffsetID` 는 객체의 `.id` 만 바꾸고 dict key 는 그대로 두므로, `_rekey_all_managers()` 로 모든 매니저 dict 를 새 id 기준으로 재구성한다. 이를 빠뜨리면 Overwrite 시 기존 모델의 같은 key 를 덮어쓰는 버그가 생긴다 (KooImportMerger.py:170-172, 175-222).
5. **재료 병합** — `_merge_materials()` 가 기존에 **없는 MID/EOSID/HGID 만** 추가한다(충돌 시 기존 보존). `maxid` 는 양쪽 max 로 갱신한다 (KooImportMerger.py:59-61, 225-242).
6. **나머지 매니저 통합** — `_merge_managers()` 가 node/part/section/nodeset/segmentset/contact/define/boundaryNode/damping/constrained/control/database/additional 매니저를 각각 `OverwritefromXxx(new)` 메서드로 병합한다. 메서드가 없거나 예외가 나면 경고 후 skip 한다 (KooImportMerger.py:63-64, 245-274). 마지막으로 `dynaImporter.SyncronizeMaxID()` 로 통합 maxID 를 맞춘다 (KooImportMerger.py:66-69).

### 4.3 출력

`IMPORT_MERGE_K` 분기는 `_skip_default_write` 를 설정하지 않으므로(다른 `_io` 모드인 DECOMPOSE_K/MERGE_K 와 대비), 디스패치 루프 종료 후 **기본 `WriteModifiedFile(additionalword)` 경로**를 탄다 (KooMeshModifier.py:2883-2891). 출력 파일명은 입력 파일명에서 `.k` 를 떼고 `additionalword`(여기서는 `_imported`)를 붙여 `<입력 basename>_imported.k` 가 된다 (KooMeshModifier.py:2872, 2906-2910). 결과 파일에는 통합된 키워드 본문과 함께 `*INCLUDE` 참조 파일 복사 등 표준 write 처리가 적용된다 (KooMeshModifier.py:2906-2939).

## 5. 주의사항 · 한계

- **MID 충돌 시 소스 재료가 무시됨**: 같은 MID 가 양쪽에 있으면 기존(타깃) 모델 재료가 유지되고, 가져온 모델의 동일 MID 재료는 추가되지 않는다 (KooImportMerger.py:228-231). 두 모델이 서로 다른 재료에 같은 MID 를 쓰면 가져온 파트가 의도와 다른 재료를 참조하게 된다 — 사전 MID 정리 필요.
- **MAT/EOS/HG 만 ID 보존**, 그 외 모든 ID 는 오프셋된다. 가져온 모델의 PID/NID/EID 등은 원본과 달라지므로, 절대 ID 로 참조하던 외부 스크립트/후처리와는 호환되지 않는다.
- **substring 매칭 충돌 주의**: 모드/옵션 키워드는 부분 문자열 매칭(`if "<kw>" in ...`)이라 `import_merge_k` 를 `merge_k` 보다 먼저 검사하는 식의 순서 의존이 있다 (KooMeshModifier.py:330-336, 2381 vs 2402). 새 키워드 추가 시 충돌 주의.
- **새 모델 로드 시 IGA 보존 비활성**: 가져올 파일의 `*INCLUDE` 는 전부 인라인되고 IGA passthrough 가 꺼진다 (KooImportMerger.py:39-40). IGA(`*PARAMETER_LOCAL` 스코프 의존) 모델을 가져오면 스코프가 깨질 수 있음 — 확인 필요.
- **OffsetID/Overwrite 의존**: 일부 매니저(예: boundaryNode/damping/control/database/additional)는 `OverwritefromXxx` 메서드 부재나 예외 시 조용히 skip 된다 (KooImportMerger.py:265-274). 해당 카드가 가져온 모델에 있으면 병합 누락 가능 — 결과 검증 필요.
- **전용 예제·테스트 부재**: `Examples/` 에 입력 예시가 없다(grep 0건). 실사용 시 소규모 모델로 ID 오프셋·재료 병합 결과를 먼저 검증할 것.

## 6. 개발 현황

**구현됨** — 입력 트리거 등록(KooMeshModifier.py:330-336), 옵션 파서(KooMeshModifier.py:2381-2400), 디스패치(KooMeshModifier.py:2870-2872), Generate 핸들러(KooMeshModifier.py:2443-2445), AdvancedModification 위임(KooDynaAdvancedModification.py:5067-5070), 실제 병합 로직(KooImportMerger.py:16-274)까지 코드 경로가 모두 존재한다.

단, 전용 예제·테스트 파일은 없고(`Examples/` grep 0건), IGA/특수 카드 모델 병합 시 동작은 코드상 비활성·skip 처리가 있어 **현장 검증 필요**(상기 5절 한계 참조).
