# KooMeshModifier 모드: DECOMPOSE_K

## 1. 목적 / 개요

`DECOMPOSE_K` 는 단일 `.k` 모델을 **그룹(파트 묶음) 단위로 분해**하여 다중 파일로 출력하는 모드다. `MERGE_K`(include 들을 단일 파일로 합치기)의 역방향 동작이다 (KooKFileDecomposer.py:1-22).

출력 구조 (KooKFileDecomposer.py:3-14):

```
output_dir/
├── master.k                  (모든 *INCLUDE 모음 + passthrough include)
├── controls.k                (모델 독립 설정: CONTROL_* / DATABASE_*)
├── globals.k                 (모델 의존 전역: SET / DEFINE / PARAMETER / RIGIDWALL / LOAD ...)
├── materials.k               (MAT / EOS / HG 공통)
├── sections.k                (SECTION + 미인터프리트 SECTION_* raw)
├── inter_group_contacts.k    (그룹 간 contact)
├── decompose_manifest.json   (분해 결과 매니페스트)
└── groups/
    ├── <group1>.k            (parts + nodes + elements + intra-group contacts)
    ├── <group2>.k
    └── default.k             (어느 그룹에도 안 잡힌 파트)
```

핵심 설계 (KooKFileDecomposer.py:16-21):
- 그룹당 단일 파일에 parts / nodes / elements / intra-group contact 통합 → LS-PrePost 단독 로드 가능.
- `SECTION` 은 별도 `sections.k` 로 모아 그룹 간 중복 정의 방지.
- 공유 노드는 기본적으로 사용 그룹 모두에 중복 출력(`duplicate` 정책).
- Material 은 공통 `materials.k`.
- IGA 파트(`igaParts`)도 분해 대상에 포함.

## 2. 입력 옵션 · 인자 (표)

입력 트리거: `*Mode` 블록에 `decompose_k,<modeID>`, 옵션 블록 헤더는 `**DecomposeK,<modeID>` (KooMeshModifier.py:321-323, 2176-2177).

| 옵션 | 형식 | 기본값 | 의미 | 근거 (file:line) |
|---|---|---|---|---|
| `Group` | `Group,<그룹명>,<멤버1>,<멤버2>,...` | (없음) | 그룹 정의. 멤버 중 `* ? [ ]` 포함은 glob 패턴, 나머지는 정확 파트명 매칭. 여러 줄 반복 가능 | KooMeshModifier.py:2191-2204 |
| `GroupFromFile` | `GroupFromFile,<그룹명>,<파일경로>` | (없음) | 파일에서 그룹 멤버 목록을 읽어 그룹 정의 | KooMeshModifier.py:2205-2213 / KooKFileDecomposer.py:127-146 |
| `OutputDir` | `OutputDir,<경로>` | `decomposed_output` | 출력 폴더. 상대경로면 `cur_dir` 기준 | KooMeshModifier.py:2214-2215 / KooKFileDecomposer.py:57, 113-116 |
| `DefaultGroupName` | `DefaultGroupName,<이름>` | `default` | 어느 그룹에도 안 잡힌 파트가 들어갈 그룹명 | KooMeshModifier.py:2216-2217 / KooKFileDecomposer.py:58 |
| `GroupsSubdir` | `GroupsSubdir,<이름>` | `groups` | 그룹 `.k` 가 저장될 하위 폴더명. 빈 값이면 `output_dir` 직속 | KooMeshModifier.py:2218-2219 / KooKFileDecomposer.py:59, 78 |
| `SeparateMaterials` | `SeparateMaterials,True\|False` | `False` | True 면 공통 `materials.k` 생략(그룹별 분리는 미구현 hook) | KooMeshModifier.py:2220-2221 / KooKFileDecomposer.py:60, 457-458 |
| `SharedNodesPolicy` | `SharedNodesPolicy,duplicate\|first_group` | `duplicate` | 공유 노드 출력 정책. `duplicate`=사용 그룹 모두 / `first_group`=등록 순서 첫 그룹에만 | KooMeshModifier.py:2222-2223 / KooKFileDecomposer.py:61, 212-227 |
| `EmitGroupSets` | `EmitGroupSets,True\|False` | `True` | (옵션 저장됨, 본문 사용처 미확인) | KooMeshModifier.py:2224-2225 / KooKFileDecomposer.py:62 |
| `ModelIndependentSplit` | `ModelIndependentSplit,True\|False` | `True` | `controls.k`(CONTROL/DATABASE) 분리 출력 여부. False 면 생략 | KooMeshModifier.py:2226-2227 / KooKFileDecomposer.py:63, 562-565 |
| `GroupBoundaryPolicy` | `GroupBoundaryPolicy,<값>` | `inline` | (옵션 저장됨, 본문 사용처 미확인) | KooMeshModifier.py:2228-2229 / KooKFileDecomposer.py:64 |

- 옵션 키는 대소문자 무시(`line.lower()`)로 비교되며, 알 수 없는 라인은 경고 후 무시된다 (KooMeshModifier.py:2230-2231).
- `**DecomposeK` 블록은 빈 줄과 `$` 주석 줄을 건너뛰며 `**End` 또는 EOF 까지 읽는다 (KooMeshModifier.py:2181-2189). 블록 끝에 `**End` 마커를 권장한다.
- `EmitGroupSets`, `GroupBoundaryPolicy` 두 옵션은 파서가 저장하고 디코더가 `__init__` 에서 멤버로 보관하지만, `KooKFileDecomposer.py` 본문에서 실제로 분기에 사용하는 코드를 찾지 못했다 — **확인 필요**.

## 3. 사용 예제

> 전용 예제 없음 — `Examples/` 에 `decompose_k` / `**DecomposeK` 입력 파일이 존재하지 않는다 (grep 결과 0건). 아래는 코드 근거(KooMeshModifier.py 입력 파서)와 실제 입력 파일 헤더 관례(`Examples/alldropangles/drop_attitude.txt`)로 구성한 최소 예시다. 검증된 실행 산출물이 아니다 — 확인 필요.

KooMeshModifier 입력 `.k`(텍스트) 파일 형식:

```text
*Inputfile
MinimumModel.k
*Mode
decompose_k,1
**DecomposeK,1
Group,housing,HOUSING*,COVER
Group,battery,BATTERY_CELL,BATTERY_CAN
OutputDir,decomposed_output
DefaultGroupName,default
GroupsSubdir,groups
SharedNodesPolicy,duplicate
ModelIndependentSplit,True
**End
```

그룹 멤버 목록을 외부 파일에서 읽으려면 `GroupFromFile` 사용 (파일 내 한 줄당 파트명 또는 콤마 분리, `#`/`$` 주석 허용, KooKFileDecomposer.py:131-144):

```text
*Inputfile
MinimumModel.k
*Mode
decompose_k,1
**DecomposeK,1
GroupFromFile,housing,housing_parts.txt
OutputDir,/abs/path/decomposed
**End
```

## 4. 동작 원리 (코드 근거)

1. **입력 트리거 등록**: `*Mode` 블록에서 `decompose_k` 매칭 → `modeList` 에 `"DECOMPOSE_K"` 추가 (KooMeshModifier.py:321-323).
2. **옵션 블록 파싱**: `**decomposek` 헤더에서 `Group` / `GroupFromFile` / `OutputDir` 등을 읽어 `modeIDOption[modeID]` 에 저장. `Group` 멤버는 patterns(glob)와 exact(정확 파트명)로 분리 (KooMeshModifier.py:2176-2232).
3. **dispatch**: 실행 시 `mode == "DECOMPOSE_K"` 분기에서 `GenerateDecomposeK(modeid)` 호출 후 `_skip_default_write = True` 설정 → 공용 `WriteModifiedFile` 을 건너뛴다(자체 출력) (KooMeshModifier.py:2864-2866, 2883-2884).
4. **위임**: `GenerateDecomposeK` → `advancedModification.DecomposeK(curOption, self.curDir, self.inputFileName)` (KooMeshModifier.py:2435-2437) → `KooKFileDecomposer.decompose_k_file(...)` → `KFileDecomposer.run()` (KooDynaAdvancedModification.py:5057-5060; KooKFileDecomposer.py:33-43).
5. **파트 → 그룹 분류** (KooKFileDecomposer.py:159-183): `parts` + `partsRigid` + `igaParts` 를 순회. 그룹 정의를 등록 순서대로 검사하여 첫 매칭(정확 파트명 우선, 그다음 glob `fnmatch`)으로 그룹 할당. 매칭 없으면 `default_group_name`.
6. **노드 → 그룹 분류** (KooKFileDecomposer.py:188-210): 각 파트의 요소가 사용하는 노드를 해당 파트 그룹에 등록(`node_to_groups`). 여러 그룹이 같은 노드를 쓰면 공유 노드. IGA 파트는 `elementManager` 없으면 skip.
7. **그룹 파일 출력** (KooKFileDecomposer.py:232-294): 그룹별 `<group>.k` 에 `*KEYWORD` + parts(`WriteStreamDynaPart`) + nodes + elements(`WriteStreamDynaElements`) + intra-group contacts + `*END` 기록. 노드는 `_node_belongs_to_group` 의 공유 정책에 따라 포함 (KooKFileDecomposer.py:296-307).
8. **Contact 분류** (KooKFileDecomposer.py:361-450): contact 의 SS/MS 측을 `SSTYP`/`MSTYP`(3=PID, 2=SET_PART, 0=SET_SEGMENT, 4=SET_NODE)로 해석해 관련 그룹 집합을 구함. 양면 모두 같은 단일 그룹이면 intra-group, 아니면 `inter_group_contacts.k` (KooKFileDecomposer.py:472-491).
9. **공통 파일 출력**: `sections.k`(정식 SECTION + raw SECTION_*, KooKFileDecomposer.py:309-338), `materials.k`(KooKFileDecomposer.py:455-470), `globals.k`(SET/DEFINE/LOAD/INITIAL/BOUNDARY/CONSTRAINED/DAMPING + 미인터프리트 raw, KooKFileDecomposer.py:493-543), `controls.k`(CONTROL+DATABASE, KooKFileDecomposer.py:562-580).
10. **master.k 작성** (KooKFileDecomposer.py:585-608): `controls/globals/materials/sections` → 그룹 파일들 → `inter_group_contacts.k` 순으로 `*INCLUDE`. IGA/`PARAMETER_LOCAL`/사용자 지정 passthrough include 는 `_copy_passthrough_includes` 로 출력 폴더에 복사 후 참조 (KooKFileDecomposer.py:610-632).
11. **manifest 작성** (KooKFileDecomposer.py:637-677): `decompose_manifest.json` 에 입력파일·그룹목록·`pid_to_group`·공유노드 수·미인터프리트 키워드 목록 기록.

## 5. 주의사항 · 한계

- **공유 노드 중복**: 기본 `duplicate` 정책은 그룹 경계 노드를 양쪽 `.k` 에 똑같은 NID 로 출력한다. 모든 그룹을 함께 로드(`master.k`)할 땐 정상이나, 개별 그룹 단독 해석 시 중복/누락에 유의 (KooKFileDecomposer.py:19, 217-227).
- **미사용 옵션 가능성**: `EmitGroupSets`, `GroupBoundaryPolicy` 는 파싱·저장되지만 본문 사용처를 코드에서 확인하지 못했다 — **확인 필요** (KooKFileDecomposer.py:62, 64).
- **SeparateMaterials 미구현**: True 로 줘도 그룹별 material 분리는 안 되고 공통 `materials.k` 만 생략된다(옵션 hook 만 존재) (KooKFileDecomposer.py:457-458).
- **미인터프리트 키워드 보존**: KooDynaImporter 가 파싱 못 한 키워드는 raw text 로 `globals.k`/`sections.k` 에 보존되며 수정 불가. manifest 에 목록·안내가 기록된다 (KooKFileDecomposer.py:545-560, 637-677).
- **passthrough include 위치**: IGA/`PARAMETER_LOCAL`/보존 include 는 basename 으로 `master.k` 가 참조하고 원본이 `output_dir` 로 복사된다. 즉 `master.k` 와 같은 폴더에 함께 있어야 LS-DYNA 가 찾는다 (KooKFileDecomposer.py:610-632, 602-606).
- **기본 write 생략**: `_skip_default_write = True` 이므로 공용 출력 경로/형식과 다르다. 출력은 항상 `OutputDir`(기본 `decomposed_output`) 폴더 트리 (KooMeshModifier.py:2866, 2883-2884).
- **전용 예제 부재**: `Examples/` 에 DECOMPOSE_K 입력 파일이 없어 3장 예시는 코드 근거 재구성이다 — 확인 필요.

## 6. 개발 현황

**구현됨.**

- 근거: 입력 트리거 등록 (KooMeshModifier.py:321-323), 옵션 파서 (KooMeshModifier.py:2176-2232), dispatch 분기 (KooMeshModifier.py:2864-2866), 위임 메서드 `GenerateDecomposeK`/`DecomposeK` (KooMeshModifier.py:2435-2437; KooDynaAdvancedModification.py:5057-5060), 실제 구현 `decompose_k_file` / `KFileDecomposer` 전체 (KooKFileDecomposer.py:1-678).
- 부분 미구현/미확인: `SeparateMaterials` 그룹별 분리 hook 만 존재 (KooKFileDecomposer.py:457-458), `EmitGroupSets`·`GroupBoundaryPolicy` 옵션은 저장되나 사용처 미확인.
