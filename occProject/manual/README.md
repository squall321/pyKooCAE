# KooMeshModifier 매뉴얼

## occProject/Generators LS-DYNA 모델 자동화 프레임워크 문서

---

## 문서 목록

### 1. [디렉토리 구조 개요](01_Directory_Structure.md)
- 전체 디렉토리 구조
- Python 파일 목록 및 설명
- KooCAEManager 모듈 설명
- 기술 스택
- 클래스 상속 구조

### 2. [KooMeshModifier 모드 레퍼런스](02_KooMeshModifier_Modes_Reference.md)
- 21개 변환 모드 상세 설명
- 설정 파일 구조
- 각 모드별 옵션 및 사용 예시
- 다중 모드 사용 방법

### 3. [기능 완성도 현황](03_Feature_Completion_Status.md)
- 완성된 기능 (14개)
- 부분 완성된 기능 (5개)
- 미완성 기능 (2개)
- 예제 파일 현황
- 개발 권장 사항

### 4. [파일 관계도](04_File_Relationships.md)
- 전체 아키텍처 다이어그램
- 클래스 상속 관계
- 핵심 의존성
- 모듈 관계
- 데이터 흐름 다이어그램

### 5. [모드별 상세 분석](modes/README.md)
핵심 모드들의 함수 레벨 상세 분석:
- [DROP_ATTITUDE](modes/MODE_09_DROP_ATTITUDE.md) - 낙하 자세 시뮬레이션 ⭐
- [DYNAIN_TO_INITIAL](modes/MODE_18_DYNAIN_TO_INITIAL.md) - 동적이완 결과 변환 ⭐
- [DROP_WEIGHT_IMPACT_TEST](modes/MODE_12_DROP_WEIGHT_IMPACT_TEST.md) - 낙하추 충격 시험 ⭐
- [SIMULATION_AUTOMATION](modes/MODE_20_SIMULATION_AUTOMATION.md) - 시뮬레이션 자동화 (⚠️ 개발중)
- [ELASTIC_TO_RIGID](modes/MODE_01_ELASTIC_TO_RIGID.md) - 탄성→강체 변환
- [PART_EXCHANGE](modes/MODE_05_PART_EXCHANGE.md) - 파트 메시 변환
- [TRANSFORM](modes/MODE_11_TRANSFORM.md) - 기하 변환

---

## 빠른 시작

### 기본 사용법

```bash
# 설정 파일과 함께 실행
python KooMeshModifier.py option.txt

# 디렉토리 지정
python KooMeshModifier.py option.txt /path/to/workdir
```

### 설정 파일 기본 구조

```
*Inputfile
input_model.k

*Mode
ELASTIC_TO_RIGID,1
TRANSFORM,2

**ElastictoRigid,1
*PIDExcept,5,10
**EndElastictoRigid

**Transform,2
Translation,10,0,0
**EndTransform

*End
```

---

## 지원 모드 요약

| 모드 | 설명 | 상태 |
|------|------|------|
| ELASTIC_TO_RIGID | 탄성→강체 변환 | 완성 |
| MATERIAL_EXCHANGE | 재료 DOE | 완성 |
| PART_LOCATION_DOE | 위치 DOE | 부분완성 |
| ERODING_MIN_DT | 침식 시간간격 | 완성 |
| PART_EXCHANGE | 파트 교체 | 완성 |
| PART_MORPHING | 형상 모핑 | 부분완성 |
| WEAK_COUPLING | 약결합 | 부분완성 |
| DEFEATURE_MESH | 디피처링 | 완성 |
| DROP_ATTITUDE | 낙하 자세 | 완성 |
| TRANSLATION_DOE | 이동 DOE | 부분완성 |
| TRANSFORM | 기하 변환 | 완성 |
| DROP_WEIGHT_IMPACT_TEST | 낙하 충격 | 완성 |
| CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM | CNRB→빔 | 완성 |
| WARPED_PART | 휨 적용 | 완성 |
| WARPED_TO_INITIAL_STRESS_PART | 휨→초기응력 | 완성 |
| DIMENSIONAL_TOLERANCE | 치수 공차 | 완성 |
| COHESIVE_BETWEEN_CONFORMAL_MESHES | 코히시브 삽입 | 완성 |
| DYNAIN_TO_INITIAL | Dynain→초기조건 | 완성 |
| CONTACT_AUTO_DECOMPOSITION | 접촉 분해 | 부분완성 |
| SIMULATION_AUTOMATION | 시뮬레이션 자동화 | 미완성 |
| REMOVE_DUPLICATE_TIED_CONTACTS | 중복 접촉 제거 | 미완성 |

---

## 예제 파일 위치

```
occProject/Generators/dist/Examples/5.SimulationModify/
```

---

## 문의 및 지원

- 작성자: koo.park
- 이메일: koo.park@samsung.com
- 그룹: CAE
- 팀: Samsung
