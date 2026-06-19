# KooMeshModifier 모드: WARPED_PART

## 1. 목적/개요

`WARPED_PART` 모드는 외부에서 측정/계산된 **휨(warpage) 분포 데이터**를 입력받아, 지정한 파트(PID)의 절점을 Z 방향으로 변형시켜 평탄한 메시를 **휜 형상으로 변형**한다. 주로 PCB/패키지 등의 반제품 휨 형상을 해석 모델에 반영할 때 사용한다.

- 상단(Top) 휨 파일만 지정하면 단일 휨 분포를 Z 방향으로 더한다.
- 상단/하단(Top/Bottom) 휨 파일을 함께 지정하면, 절점의 Z 위치 비율에 따라 두 분포를 선형 보간하여 적용한다(두께 방향으로 상/하면이 다른 휨을 갖는 경우).

휨 데이터는 2D 격자(matrix) 형태의 `.dat` 파일이며, 코드 내부에서 `scipy.interpolate.LinearNDInterpolator`로 절점 위치에 보간된다. 변형 결과는 변경된 `.k` 파일(접미사 `_warp`)로 출력된다.

> 관련 모드: 같은 휨 데이터를 **메시 변형 대신 초기 응력(`*INITIAL_STRESS_SOLID`)으로 변환**하는 별도 모드는 `WARPED_TO_INITIAL_STRESS_PART`(`AdditionalThickness` 옵션 추가)이다.

## 2. 입력 옵션·인자

입력 옵션 블록은 `**WarpedPart,<모드ID>` 로 시작하며, 한 줄당 `키,값[,값...]` 형식이다. 블록은 빈 줄 또는 `**End...`(예: `**EndWarpedPart`)에서 종료된다. 파서는 부분 문자열 매칭(예: `"unitscale" in line.lower()`)을 사용하므로 키 앞에 `*` 접두가 붙어도(`*UnitScale,...`) 정상 인식된다.

| 옵션 키 | 인자 | 기본값 | 의미 | 근거 (KooMeshModifier.py) |
|---|---|---|---|---|
| `UnitScale` | 단위 문자열 | `"mm"` | 휨 값의 단위. `Microm`/`mm`/`cm`/`m`/`inch` 지원 (단위→mm 환산 계수 적용) | :724, :743-745 |
| `AmplitudeTop` | float | `1.0` | 상단 휨 적용 배율(스케일 팩터) | :725, :746-748 |
| `AmplitudeBottom` | float | `0.0` | 하단 휨 적용 배율. Top/Bottom 보간 시 사용 | :726, :749-751 |
| `Location` | x,y,z | `[0.0, 0.0, 0.0]` | 휨 격자의 기준(원점) 위치 | :727, :752-754 |
| `XLength` | float | `0.0` | 휨 격자가 매핑되는 X 길이. `0.0`이면 파트 BBox에서 자동 계산 | :728, :755-757 |
| `YLength` | float | `0.0` | 휨 격자가 매핑되는 Y 길이. `0.0`이면 파트 BBox에서 자동 계산 | :729, :758-760 |
| `Direction` | x,y,z | `[0.0, 0.0, 1.0]` | 휨 적용 방향. **현재 `0,0,1`(Z) 만 동작** | :730, :761-763 |
| `WarpageFileTop` | 파일명 | `"warpage.dat"` | 상단 휨 데이터 파일(필수) | :731, :764-766 |
| `WarpageFileBottom` | 파일명 | `None` | 하단 휨 데이터 파일. 지정 시 Top/Bottom 보간 동작 | :732, :767-769 |
| `PIDs` | id[,id...] | `[]` | 변형 대상 파트 ID 목록(여러 줄 누적, 한 줄에 여러 개 가능) | :733, :770-773 |

모드 활성화는 `*Mode` 블록에 `warped_part,<모드ID>` 줄을 추가하여 등록한다(트리거: `'warped_part' in svector[0].lower()`, KooMeshModifier.py:294-296). 모드ID는 옵션 블록의 `**WarpedPart,<모드ID>`와 일치해야 한다.

### 휨 데이터 파일(.dat) 형식
- 탭(`\t`) 구분 부동소수 행렬(2D matrix). 각 행이 탭으로 분리된 셀로 파싱된다 (WarpageSurface.py:50-63).
- 읽은 행 순서는 내부에서 역순 정렬된다(`lines[::-1]`, WarpageSurface.py:61).
- 값 `9999`는 "데이터 없음(빈 공간)"으로 취급되며, 인접 셀 평균으로 보정된다 (WarpageSurface.py:67~, `RemoveEmptySpace`).
- 격자는 `Location`+`XLength`/`YLength` 범위에 균등 매핑되어 보간된다 (KooWarpage.py:51-61).

## 3. 사용 예제

아래는 저장소 내 기존 매뉴얼(`occProject/Generators/KooMeshModifier_Manual.md:378-396`)에 수록된 실제 입력 파일 예제(`WarpedPart/WarpedPart.txt`)이다. `warpage.dat`를 상/하 동일 적용, 단위 Microm, 대상 PID 1~4.

```
*Inputfile
Impact_1_00000001.k
*Mode
WARPED_PART,1
**WarpedPart,1
*UnitScale,Microm
*AmplitudeTop,0.1
*AmplitudeBottom,0.0
*Location,0.0,0.0,0.0
*XLength,0.0
*YLength,0.0
*Direction,0.0,0.0,1.0
*WarpageFileTop,warpage.dat
*WarpageFileBottom,warpage.dat
*PIDs,1,2,3,4
**EndWarpedPart
*End
```

- 입력 파일(여기서는 `*Inputfile` 다음 줄의 `.k`)과 휨 데이터 `.dat`는 실행 작업 디렉터리에 함께 위치해야 한다(휨 파일은 `os.getcwd()` 기준으로 로드됨, KooWarpage.py:40 / WarpageSurface.py:37-40).
- 출력: 입력 `.k` 파일명에 `_warp` 접미사가 붙은 변형된 `.k` (KooMeshModifier.py:2842, `WriteModifiedFile`).

> 참고: 단일 휨 파일만 쓰려면 `*WarpageFileBottom` 줄을 생략한다(기본 `None` → 상단 휨만 적용 분기, KooMeshModifier.py:732 / KooDynaAdvancedModification.py:5728).

## 4. 동작 원리 (코드 근거)

1. **모드 등록·디스패치**
   - `*Mode` 블록에서 `warped_part` 토큰이 `modeList`에 `WARPED_PART`로 등록된다 (KooMeshModifier.py:294-296).
   - 실행 루프에서 `mode == "WARPED_PART"` 분기가 `self.GenerateWarpedPart(modeid)`를 호출하고 출력 접미사 `_warp`를 추가한다 (KooMeshModifier.py:2840-2842).
   - `GenerateWarpedPart`는 옵션 dict를 꺼내 `advancedModification.WarpedPart(curOption)`에 위임한다 (KooMeshModifier.py:2569-2571).

2. **BBox 계산 및 자동 길이 산정** (KooDynaAdvancedModification.py:5704-5724)
   - 대상 PID들의 합집합 경계상자(min/max x,y,z)를 구한다.
   - `XLength` 또는 `YLength`가 `0.0`이면 BBox로부터 `xLength=xmax-xmin`, `yLength=ymax-ymin`을 자동 계산하고 `Location=[xmin, ymin, zmax]`로 재설정한다.

3. **휨 적용 분기** (KooDynaAdvancedModification.py:5727-5742)
   - `WarpageFileBottom == None` → 각 PID에 대해 `KooPart.WarpZdirectionPart(...)` 호출(상단 휨만).
   - `WarpageFileBottom` 지정 → `KooPart.WarpZdirectionPartfromTopBottom(...)` 호출(상/하 보간).
   - **두 경로 모두 `Direction == (0,0,1)` 일 때만 실행**된다(`if direction[0]==0.0 and direction[1]==0.0 and direction[2]==1.0`). 그 외 방향이면 변형이 일어나지 않는다.

4. **절점 변형 (Z 방향 단일 휨)** (KooPart.py:324-370)
   - 휨 데이터를 `KooWarpage`로 로드하고 단위 환산(`SetWarpageUnit`) 후 `GenerateZInterpolator`로 보간기를 만든다.
   - 파트 절점 중 `[xmin,xmax]×[ymin,ymax]` 범위 안의 절점만 대상으로 `z += amp * zInterp(x,y)` 적용 (KooPart.py:350-369).
   - 이미 다른 PID에서 이동된 절점(`addedNodes`)은 중복 이동을 막기 위해 건너뛴다 (KooPart.py:364-365).

5. **절점 변형 (Top/Bottom 보간)** (KooPart.py:266-321)
   - 상/하 두 보간기를 각각 생성하고, 절점의 두께 방향 위치 비율 `curPosZRatio = (z - globalzMin)/(globalzMax - globalzMin)`을 계산한다 (KooPart.py:319).
   - `z += AmplitudeTop·zTop·ratio + AmplitudeBottom·zBottom·(1-ratio)` 로 상/하 휨을 선형 혼합한다 (KooPart.py:320).

6. **단위 환산** (KooWarpage.py:25-37): `Microm`=1e-3, `mm`=1.0, `cm`=1e1, `m`=1e3, `inch`=25.4 의 계수로 휨 값을 mm 기준으로 스케일한다.

7. **출력**: 모드가 `_skip_default_write`를 설정하지 않으므로 기본 `WriteModifiedFile("..._warp")`가 실행되어 변형된 `.k`를 기록한다 (KooMeshModifier.py:2880-2891, 2906~).

## 5. 주의사항·한계

- **Z 방향 전용**: `Direction`이 `(0,0,1)`이 아니면 변형이 적용되지 않는다(분기 조건이 Z만 처리). 다른 방향은 사실상 미지원 — **확인 필요**(향후 확장 여지).
- **작업 디렉터리 의존**: 휨 데이터 파일은 `os.getcwd()` 기준으로 로드된다(KooWarpage.py:40). 절대경로가 아니라 실행 위치에 파일이 있어야 한다.
- **격자 매핑 가정**: 휨 격자는 사각형 영역(`Location`+`XLength`×`YLength`)에 균등 매핑된다. 비정형 영역/회전된 격자는 직접 지원되지 않는다 — **확인 필요**.
- **범위 밖 절점**: BBox/지정 영역 밖 절점은 변형 대상에서 제외된다(KooPart.py:350). 영역 설정이 부정확하면 일부 절점만 변형될 수 있다.
- **`9999` 마스킹**: 데이터 결손 셀은 인접값 평균으로 자동 채워진다(RemoveEmptySpace). 결손이 많으면 보정 형상이 실제와 달라질 수 있다.
- **다중 PID 중복 절점**: 여러 PID가 절점을 공유하면 먼저 처리된 PID 기준으로만 이동된다(`addedNodes` 스킵, KooPart.py:364).
- **파일 형식**: 휨 파일은 **탭 구분** 행렬이어야 한다(WarpageSurface.py:55). 공백/CSV 형식은 파싱 실패 가능 — **확인 필요**.
- **예제 `.dat` 부재**: 본 저장소 `Examples/`에는 실제 `warpage.dat` 샘플이 확인되지 않았다. 사용자가 휨 측정 데이터를 별도 준비해야 한다.

## 6. 개발 현황

**구현됨.**

- 근거:
  - 모드 등록/디스패치 존재: KooMeshModifier.py:294-296(등록), 2840-2842(분기), 2569-2571(`GenerateWarpedPart`).
  - 옵션 파서 완비: KooMeshModifier.py:720-774(`**warpedpart` 블록).
  - 실 변형 로직 구현: KooDynaAdvancedModification.py:5692-5742(`WarpedPart`), KooPart.py:324-370 및 266-321(Z/Top-Bottom 변형), KooWarpage.py(보간), WarpageSurface.py(파일 로드).
  - 기존 문서에도 "구현됨"으로 등재: `docs/manual/02_KooMeshModifier/dev_status.md:170` (`WARPED_PART | 구현됨 | A:5692 WarpedPart. M:2840/2569`).
- 한계: 변형 방향은 Z(`0,0,1`)만 동작하며, 그 외 방향 및 비사각 영역 매핑은 미지원/미검증(상세 §5).
