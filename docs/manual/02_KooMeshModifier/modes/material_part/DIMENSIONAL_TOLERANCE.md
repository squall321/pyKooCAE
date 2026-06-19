# KooMeshModifier 모드: DIMENSIONAL_TOLERANCE

## 1. 목적/개요

`DIMENSIONAL_TOLERANCE` 모드는 솔리드 파트에 **치수 공차(산포)** 를 초기 응력 형태로 부여하여, 동일 메시로부터 여러 개의 "치수 산포가 반영된" 해석 모델(.k)을 자동 생성하는 모드이다. 각 파트의 X/Y/Z 방향 자유 팽창 변형률(ΔL/L)을 받아, 그 변형률에 대응하는 응력 텐서를 등방성 구성방정식으로 계산하고 `*INITIAL_STRESS_SOLID` 카드로 모델에 삽입한다. 이후 동적 완화(dynamic relaxation) 해석을 거치면 해당 응력이 실제 치수 변화(두께·길이 산포)로 풀려나는 흐름을 의도한 모드이다.

샘플 생성 방식은 세 가지이다 (KooDynaAdvancedModification.py:5821-5828).
- **LIST**: 사용자가 직접 나열한 변형률 값 리스트로 샘플 생성.
- **NORM**: 절단 정규분포(truncated normal)에서 무작위 샘플 생성.
- **LHS**: 라틴 하이퍼큐브 샘플링(min~max 범위)으로 샘플 생성.

> 코드 주석에 `WEIBULL` 모드 예시가 등장하나, 디스패처(KooDynaAdvancedModification.py:5821-5828)에는 LIST/NORM/LHS 분기만 존재한다 → **WEIBULL은 미구현(확인 필요)**.

> 전용 매뉴얼 예제 디렉터리는 없으나, 배포 디렉터리에 실제 입력 예제 `.txt`가 존재한다(아래 3절). 본 문서는 코드 근거 기반으로 작성되었다.

## 2. 입력 옵션·인자

옵션 블록은 `**DimensionalTolerance,<모드ID>` 로 시작하며, 빈 줄 또는 `**End...`(예: 예제의 `**EndWarpedtoInitialStressPart` — 파서는 `"**end" in line.lower()`만 확인) 에서 종료된다. 모드 등록은 `*Mode` 블록에 `DIMENSIONAL_TOLERANCE,<모드ID>` 줄을 추가한다(트리거: `"dimensional_tolerance" in svector[0].lower()`, KooMeshModifier.py:300-302). 모드ID는 옵션 블록의 `**DimensionalTolerance,<모드ID>`와 일치해야 한다.

| 옵션 키 / 줄 | 인자 | 기본값 | 의미 | 근거 (KooMeshModifier.py) |
|---|---|---|---|---|
| `*PartDimTolerance` | `LIST` | (기본 `LIST`) | 샘플 모드 = 직접 나열 리스트 | :614, :630-634 |
| `*PartDimTolerance` | `NORM[,<샘플수>]` | 샘플수 생략 시 `30` | 절단 정규분포 샘플링 | :635-640 |
| `*PartDimTolerance` | `LHS[,<샘플수>]` | 샘플수 생략 시 `30` | 라틴 하이퍼큐브 샘플링 | :641-646 |
| 데이터 줄 | `<PID>,<방향>,<값...>` | — | 파트별·방향별 파라미터(아래 표) | :648-657 |

데이터 줄의 형식은 `PID, 방향(x/y/z), 값들...` 이며, 방향은 소문자로 정규화된다. 값들의 의미는 선택한 샘플 모드에 따라 다르다.

| 모드 | 데이터 줄 형식 | 값 의미 | 근거 (KooDynaAdvancedModification.py) |
|---|---|---|---|
| LIST | `PID,방향,v0,v1,v2,...` | 각 값이 곧 샘플의 변형률(ΔL/L). **샘플 개수 = 첫 변수의 값 개수** | :5836, :5847-5862 |
| NORM | `PID,방향,avg,std,x` | `avg`=평균, `std`=표준편차, `x`=표준편차 배수(절단 한계) | :5912-5933 (`truncated_normal_samples`) |
| LHS | `PID,방향,min,max` | `min`/`max` 범위에서 LHS 샘플링. `min==max==0`인 변수는 제외 | :6005-6042 |

- LIST 모드의 샘플 개수는 첫 번째 PartOption의 첫 방향에 나열된 값 개수로 결정된다(KooDynaAdvancedModification.py:5832-5836). 따라서 모든 방향/파트에 동일 개수의 값을 넣어야 인덱스 오류 없이 동작한다(확인 필요 — 길이 불일치 검증 코드는 없음).
- NORM/LHS 모드의 샘플 개수는 `*PartDimTolerance` 줄의 3번째 인자(생략 시 30)로 결정된다(KooMeshModifier.py:637-646).
- 동일 PID에 여러 방향 줄을 추가하면 `PartOption[pid][direction]` 으로 누적된다(KooMeshModifier.py:653-657).

## 3. 사용 예제

전용 매뉴얼 예제는 없으나, 배포 디렉터리(`occProject/Generators/dist/Examples/5.SimulationModify/DimensionalTolerance/`)에 실제 입력 `.txt`가 존재한다. 아래는 그 파일 및 기존 매뉴얼(`occProject/Generators/KooMeshModifier_Manual.md:422-443`) 발췌이다.

### LIST 모드 (`DimensionalTolerance.txt`)
```
*Inputfile
PlateSolid.k
*Mode
DIMENSIONAL_TOLERANCE,1
**DimensionalTolerance,1
*PartDimTolerance,LIST
#PID,Direction,tolerance 1, tolerance, 2...
1,Z,0.00,-0.3,0.05
1,X,0.1,0.000,0.05
**EndWarpedtoInitialStressPart
*End
```
- PID 1에 대해 Z방향 3개 샘플값(0, -0.3, 0.05), X방향 3개 샘플값(0.1, 0, 0.05) → 3개의 모델 생성.

### NORM 모드 (`DimensionalTolerance_norm_dist.txt`)
```
*Inputfile
PlateSolid.k
*Mode
DIMENSIONAL_TOLERANCE,1
**DimensionalTolerance,1
*PartDimTolerance,NORM,100
#PID,Direction,avg,std,x
1,X,0.01,0.02,5
**EndWarpedtoInitialStressPart
*End
```
- PID 1 X방향, 평균 0.01 / 표준편차 0.02 / 절단 ±5σ, 샘플 100개.

### LHS 모드 (`DimensionalTolerance_LHS.txt`)
```
*Inputfile
PlateSolid.k
*Mode
DIMENSIONAL_TOLERANCE,1
**DimensionalTolerance,1
*PartDimTolerance,LHS,100
#PID,Direction,min,max,
1,X,-0.05,0.05
**EndWarpedtoInitialStressPart
*End
```
- PID 1 X방향, -0.05 ~ 0.05 범위 LHS 샘플 100개.

## 4. 동작 원리 (코드 근거)

1. **모드 등록·디스패치**
   - `*Mode` 블록의 `dimensional_tolerance` 토큰이 `modeList`에 `DIMENSIONAL_TOLERANCE`로 등록된다 (KooMeshModifier.py:300-302).
   - 실행 루프에서 `mode == "DIMENSIONAL_TOLERANCE"` 분기가 `self.GenerateDimensionalTolerance(modeid)`를 호출하고 출력 접미사 `_dt`를 추가한다 (KooMeshModifier.py:2846-2848).
   - `GenerateDimensionalTolerance`는 옵션 dict와 입력 `.k` 경로(확장자 제거)를 `advancedModification.DimensionalTolerance(curOption, filePath)`에 위임한다 (KooMeshModifier.py:2577-2581).

2. **옵션 파싱** (KooMeshModifier.py:610-659)
   - 기본값 `Mode="LIST"`, `PartOption={}`, `NumberofSamples=1` 설정 후 줄을 읽는다.
   - `*PartDimTolerance` 줄에서 LIST/NORM/LHS와 (NORM/LHS의) 샘플 수를 결정.
   - 그 외 줄은 `PID,방향,값...` 으로 해석되어 `PartOption[pid][direction]=값리스트`에 저장.

3. **모드 분기** (KooDynaAdvancedModification.py:5820-5828)
   - `Mode`에 따라 `DimensionalToleranceList` / `DimensionalToleranceNorm` / `DimensionalToleranceLHS`를 호출.

4. **샘플별 처리 공통 흐름** (LIST: :5847-5892, NORM: :5960-5993, LHS: :6093-6124)
   - 각 샘플 i, 각 PID에 대해 X/Y/Z 변형률(ex,ey,ez)을 추출.
   - `part.LengthVariationbyTolerance(ex,ey,ez)` 로 요소별 응력 텐서 계산(KooPart.py:589-617).
     - 파트 재료의 E·ν를 가져와(KooPart.py:590-591), 각 솔리드 요소에 대해 `GetStressWithDirectionalExpansion(E, nu, ex, ey, ez, True)`를 호출(KooPart.py:603).
     - `GetStressWithDirectionalExpansion`은 `large_strain=True`이므로 `ε → ln(1+ε)`(대수 변형률) 변환 후 방향별 팽창 텐서를 만들고, 등방성 구성방정식 `C`로 응력 S=C·E를 산출한다(KooElement.py:1748-1765).
     - 계산된 응력에 **음수 부호**를 곱한다(`stressTensor = -stressTensor`, KooPart.py:604) — 즉 "팽창을 구속하는" 초기 응력을 부여.
   - 요소별 응력으로 `*INITIAL_STRESS_SOLID`를 생성한다(`CreateInitialStressSolid(...)`, KooDynaAdvancedModification.py:5878). NINT=1, 단일 적분점·단일 history 가정(:5870-5877).
   - 결과를 `<입력파일명>_DimensionalTolerance_<i>.k`로 출력(LIST :5882-5887, NORM :5983-5988, LHS :6115-6120).
   - 출력 후 해당 샘플의 초기 응력을 모델에서 제거하여(다음 샘플과 분리) 깨끗한 상태로 되돌린다(:5889-5892 등).

5. **샘플 변수 기록 파일** (NORM/LHS만)
   - NORM/LHS는 샘플 변수표를 `<입력파일명>_DimensionalTolerance.txt`(PID/Name/x,y,z 헤더 + 샘플값)로 함께 출력한다(NORM :5937-5958, LHS :6070-6091). LIST 모드에는 이 변수표 출력이 없다.

6. **동적 완화 제어** (LIST 모드)
   - LIST 분기는 `controlDynamicRelaxation`이 미설정이면 기본값으로 `*CONTROL_DYNAMIC_RELAXATION`을 자동 생성한다(KooDynaAdvancedModification.py:5838-5839). NORM/LHS 분기에서는 해당 코드가 주석 처리되어 있다(:5899-5905).

## 5. 주의사항·한계

- **솔리드 전용**: 응력 계산이 `SolidElement`/`CreateInitialStressSolid` 경로를 사용한다(KooPart.py:602, KooDynaAdvancedModification.py:5878). 쉘/빔 파트는 대상이 아니다(확인 필요 — 쉘 처리 분기 없음).
- **재료 모델 의존**: `part.material.GetE()/GetNu()`로 등방성 E·ν를 가져온다(KooPart.py:590-591). 해당 메서드가 유효한 값을 주지 못하는 재료(이방성·복합 등)에서는 응력 계산이 부정확하거나 실패할 수 있다(확인 필요).
- **출력 파일명 충돌**: 모든 샘플이 `<입력파일명>_DimensionalTolerance_<i>.k`로 동일 디렉터리에 기록된다(LIST/NORM/LHS 동일 규칙). 표준 `WriteModifiedFile`(`_dt` 접미사) 출력도 별도로 수행되므로(KooMeshModifier.py:2848, :2885-2891), 파일이 다수 생성된다.
- **LIST 길이 불일치**: 샘플 개수가 첫 변수의 값 개수로 고정되므로(KooDynaAdvancedModification.py:5832-5836), 방향/파트마다 값 개수가 다르면 인덱스 접근 시 오류 가능(KooDynaAdvancedModification.py:5858-5862, 검증 코드 없음 — 확인 필요).
- **존재하지 않는 PID**: `PartOption`의 PID가 모델에 없으면 그 PID는 조용히 건너뛴다(`if pid in self.dynaImporter.partManager.parts`, KooDynaAdvancedModification.py:5840-5841 등).
- **LHS 시드 고정**: `seed = 42`로 고정되어 동일 입력에서 항상 같은 LHS 표본이 생성된다(KooDynaAdvancedModification.py:6043-6044).
- **WEIBULL 미지원**: 예제 주석에만 등장하며 디스패처에 분기가 없다(KooDynaAdvancedModification.py:5821-5828).
- **`*INITIAL_STRESS_SOLID` 해석 가정**: 부여된 초기 응력이 의도한 치수 산포로 풀리려면 LS-DYNA 동적 완화 해석이 별도로 필요하다(LIST 분기의 자동 제어 카드 생성은 그 전제). 본 모드 자체는 응력 카드 삽입까지만 수행한다.

## 6. 개발 현황

**부분구현.**

- 근거(구현됨): 모드 등록(KooMeshModifier.py:300-302), 디스패치(:2846-2848), 옵션 파싱(:610-659), LIST/NORM/LHS 세 경로의 응력 생성·출력 로직(KooDynaAdvancedModification.py:5820-6124), 핵심 응력 계산(KooPart.py:589-617 / KooElement.py:1737-1767) 모두 코드상 존재하며, 배포 디렉터리에 실행 산출물(`PlateSolid_DimensionalTolerance_*.k`, `*.csv`, dynain 등)이 남아 있어 실제 실행 이력이 확인된다.
- 근거(미구현/부분): 코드 주석에 등장하는 `WEIBULL` 모드는 디스패처에 분기가 없어 미구현(KooDynaAdvancedModification.py:5821-5828). NORM/LHS의 동적 완화 자동 제어는 주석 처리되어 LIST 모드에만 적용된다(:5899-5905, :5838-5839).
- 확인 필요: 쉘/빔·비등방 재료 지원 여부, LIST 길이 불일치 방어, `*INITIAL_STRESS_SOLID`+동적 완화 연계가 의도대로 치수 산포로 수렴하는지(정확도 검증).
