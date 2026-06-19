# KooMeshModifier 모드: ERODING_MIN_DT

## 1. 목적/개요

`ERODING_MIN_DT` 모드는 모델 내 **모든 재료(`*MAT`)에 `*MAT_ADD_EROSION` 카드를 자동으로 추가**하여, 요소의 안정 시간증분(stable time step)이 지정한 임계값(`DTMIN`) 아래로 떨어지면 해당 요소를 삭제(erosion)하도록 만드는 모드이다.

명시적(explicit) LS-DYNA 해석에서 일부 요소의 시간증분이 과도하게 작아지면(예: 큰 변형으로 인한 요소 찌그러짐) 전체 해석 속도가 급격히 느려지거나 마스 스케일링으로 인한 비물리적 거동이 발생한다. 이 모드는 그러한 요소를 `DTMIN` 기준으로 자동 삭제하여 해석 안정성/속도를 확보하는 것을 목적으로 한다.

근거: 입력 트리거 등록부 `KooMeshModifier.py:261-263`, dispatch 분기 `KooMeshModifier.py:2795-2797`, 실제 동작 `KooDynaAdvancedModification.py:5186-5190` → `KooMaterial.py:936-941`.

> 참고: 유사 모드인 `RIGIDIFY_SMALL_DT`(작은 dt 요소를 강체 파트로 분리)와 달리, 본 모드는 요소를 **삭제**하는 방향이다.

## 2. 입력 옵션·인자

`ERODING_MIN_DT`는 두 부분으로 입력된다. (1) `*mode` 블록에서 모드를 등록하고, (2) `**ErodingMinDt` 옵션 블록에서 `DTMIN` 값을 지정한다.

### 2-1. `*mode` 등록 (모드 활성화)

| 항목 | 값 | 설명 | 근거 |
|------|-----|------|------|
| 키워드 토큰 | `eroding_min_dt` | `*mode` 블록 내 한 줄로 작성 (대소문자 무시) | `KooMeshModifier.py:261` |
| `<modeID>` | 정수 | 토큰 다음 콤마로 구분된 모드 ID. 옵션 블록과 매칭됨 | `KooMeshModifier.py:262-263` |

### 2-2. `**ErodingMinDt` 옵션 블록

| 옵션 | 형식 | 기본값 | 필수 | 설명 | 근거 |
|------|------|--------|------|------|------|
| 블록 헤더 | `**ErodingMinDt,<modeID>` | — | 예 | `<modeID>`는 `*mode`에서 등록한 ID와 일치해야 함 | `KooMeshModifier.py:1779-1781` |
| `*DT` | `*DT,<value>` | — (확인 필요) | 사실상 예 | `*MAT_ADD_EROSION`의 `DTMIN` 값. 파싱 실패 시 `1.0e-9`로 대체 | `KooMeshModifier.py:1791-1794` |
| 블록 종료 | `**end` | — | 예 | 옵션 블록 종료 마커. 빈 줄도 종료로 처리됨 | `KooMeshModifier.py:1789` |

주의 (확인 필요): 옵션 블록에서 `*DT` 라인이 전혀 없으면 `curOptions["DT"]`가 설정되지 않는다(`KooMeshModifier.py:1782, 1791-1794`). 이 경우 dispatch 단계의 `dt = curOption["DT"]`(`KooMeshModifier.py:2534`)에서 `KeyError`가 발생할 수 있다. 따라서 `*DT` 라인은 사실상 필수로 보아야 한다.

`*DT` 값 파싱은 `KooDynaFloat(svector[1], 1.0e-9)`을 사용한다. 즉 값이 비었거나 숫자로 해석 불가하면 `1.0e-9`로 대체된다 (`KooMeshModifier.py:1793`, `KooOperator.py:23-31`).

## 3. 사용 예제

> 전용 예제 없음. `Examples/` 디렉터리에서 `ERODING_MIN_DT` / `ErodingMinDt` 사용 사례는 검색되지 않았다(확인 필요 — grep 결과 없음). 아래 예제는 코드의 파서 구조(`KooMeshModifier.py:234-263, 1779-1799`)에 근거해 재구성한 최소 입력이다.

KooMeshModifier 입력 .k 파일에 다음과 같이 작성한다.

```
*mode
eroding_min_dt,1
*

**ErodingMinDt,1
*DT,1.0e-7
**end
```

- `*mode` 블록의 `eroding_min_dt,1` → 모드 등록 + `modeID=1` (`KooMeshModifier.py:261-263`)
- `**ErodingMinDt,1` → `modeID=1`의 옵션 블록 시작 (`KooMeshModifier.py:1779-1781`)
- `*DT,1.0e-7` → 모든 재료에 부여될 `*MAT_ADD_EROSION`의 `DTMIN = 1.0e-7` (`KooMeshModifier.py:1791-1794`)
- `**end` → 옵션 블록 종료 (`KooMeshModifier.py:1789`)

## 4. 동작 원리 (코드 근거)

1. **모드 등록**: `*mode` 블록 파싱 중 `eroding_min_dt` 토큰을 만나면 `modeList`에 `"ERODING_MIN_DT"`, `modeIDList`에 `<modeID>`를 추가한다.
   - `KooMeshModifier.py:261-263`

2. **옵션 파싱**: `**erodingmindt`로 시작하는 블록을 만나면 `curModeID`를 읽고, 블록 내에서 `*dt` 라인을 찾아 `curOptions["DT"] = KooDynaFloat(svector[1], 1.0e-9)`로 저장한다. `**end` 또는 빈 줄에서 종료하며 `self.modeIDOption[curModeID] = curOptions`로 등록한다.
   - `KooMeshModifier.py:1779-1799`

3. **Dispatch**: `GenerateModifiedFile()`이 `modeList`를 순회하다 `mode == "ERODING_MIN_DT"`이면 `self.GenerateErodingMinDT(modeid)`를 호출하고, 출력 파일명 접미사에 `_emdt`를 추가한다.
   - `KooMeshModifier.py:2795-2797`

4. **핸들러**: `GenerateErodingMinDT(modeid)`는 옵션에서 `dt = curOption["DT"]`를 꺼내 `self.advancedModification.ErodingMinDT(dt)`를 호출한다.
   - `KooMeshModifier.py:2532-2535`

5. **재료 매니저 위임**: `ErodingMinDT(dt)`는 `matMan.GenerateAddErosionusingDtmin(dt)`를 호출한다.
   - `KooDynaAdvancedModification.py:5186-5190`

6. **에로전 카드 생성**: `GenerateAddErosionusingDtmin(dtmin)`은 모든 재료(`self.materials`)를 순회하며, 이미 `*MAT_ADD_EROSION`이 있는 재료(`self.addErosions`에 존재)는 건너뛰고, 나머지에 대해 `CreateAddErosionMaterial(mid=matid, DTMIN=dtmin)`을 호출한다.
   - `KooMaterial.py:936-941`
   - `CreateAddErosionMaterial`은 `KooMaterialAddErosion` 객체를 생성해 `self.addErosions[mid]`에 등록한다 (`KooMaterial.py:1065-1068`).

7. **출력 카드 형식**: `KooMaterialAddErosion.GenerateDynaKeyword()`가 `*MAT_ADD_EROSION` 카드를 생성하며, 마지막 행에 `DTMIN`을 `>10.3e` 형식으로 기록한다. 다른 에로전 파라미터(EXCL, MXPRES, … VOLFRAC=0.5, MXTMP=1.0e20 등)는 생성자 기본값이 사용된다.
   - `KooMaterial.py:215-254`, 기본값은 `KooMaterial.py:180`(생성자 시그니처) 및 `KooMaterial.py:1065`(`CreateAddErosionMaterial` 시그니처) 참조

### 출력

- 모든 재료에 `*MAT_ADD_EROSION` 카드가 추가된 수정 .k 파일.
- 추가되는 `*MAT_ADD_EROSION`은 입력 `*DT` 값만 `DTMIN`으로 설정하고, 나머지 필드는 코드 기본값(대부분 0.0, `VOLFRAC=0.5`, `MXTMP=1.0e20`, `NUMFIP=1.0`, `NCS=1.0`)을 사용한다 (`KooMaterial.py:180`).
- 출력 파일명 접미사: `_emdt` (`KooMeshModifier.py:2797`).

## 5. 주의사항·한계

- **전역(全 재료) 적용**: 특정 파트/재료만 선택할 수 없다. `GenerateAddErosionusingDtmin`은 `self.materials`의 **모든** 재료에 일괄 적용한다 (`KooMaterial.py:936-941`). 파트 선택 옵션은 코드상 존재하지 않는다.
- **기존 에로전 보존**: 이미 `*MAT_ADD_EROSION`이 있는 재료(`self.addErosions`에 존재)는 건너뛴다. 기존 카드의 `DTMIN`은 변경되지 않는다 (`KooMaterial.py:938-939`).
- **`*DT` 누락 위험**: 옵션 블록에 `*DT` 라인이 없으면 `curOption["DT"]`가 없어 `KeyError` 가능성이 있다 (`KooMeshModifier.py:1782` vs `2534`). 항상 `*DT`를 명시할 것 (확인 필요 — 예외 처리 코드 미발견).
- **잘못된 `*DT` 값**: 숫자 파싱 실패 시 조용히 `1.0e-9`로 대체된다(`KooMeshModifier.py:1793`). 의도치 않은 매우 작은 임계값이 들어갈 수 있으므로 값 형식에 유의.
- **고정된 에로전 기준**: `DTMIN`만 설정 가능하며, 변형률·압력 등 다른 에로전 기준(EFFEPS, MXPRES 등)은 본 모드로 설정할 수 없다(모두 기본값 0.0). 다른 기준이 필요하면 별도로 `*MAT_ADD_EROSION`을 작성해야 한다.
- **단위계 의존성**: `DTMIN`은 시간 단위에 의존한다(예: ton-mm-s 계에서 초 단위). 모델 단위계에 맞는 값을 입력해야 한다 (확인 필요 — 코드 내 단위 변환 없음).

## 6. 개발 현황

**구현됨.**

근거: 입력 트리거 등록부(`KooMeshModifier.py:261-263`), dispatch 분기(`KooMeshModifier.py:2795-2797`), 옵션 파서(`KooMeshModifier.py:1779-1799`), 핸들러(`KooMeshModifier.py:2532-2535`), 위임(`KooDynaAdvancedModification.py:5186-5190`), 카드 생성(`KooMaterial.py:936-941, 1065-1068, 215-254`)까지 전체 체인이 코드로 연결되어 있다.

단, 전용 예제 파일은 발견되지 않았다(`Examples/` grep 결과 없음). 실제 입력 .k 검증 사례는 확인 필요.
