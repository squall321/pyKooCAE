# IGA Part Generator 테스트

이 폴더에는 IGA Part Generator의 테스트 스크립트들이 있습니다.

## 테스트 파일

### 1. test_iga_standalone.py
독립적인 단위 테스트 (의존성 없음)
- KooSectionIGASolid 키워드 생성 검증
- PARAMETER_LOCAL 포맷 검증

**실행:**
```bash
cd /home/koopark/serviceApptainers/appt313/opt/pyKooCAE
python3 tests/iga_tests/test_iga_standalone.py
```

### 2. test_iga_simple.py
모듈 import 테스트
- KooIGAPart 모듈 로딩 확인
- 디폴트 옵션 출력

### 3. test_iga_part.py
통합 테스트 (전체 워크플로우)
- FEM 모델 생성
- IGA 파트 변환
- 파일 출력

## 테스트 실행

프로젝트 루트에서 실행:
```bash
cd /home/koopark/serviceApptainers/appt313/opt/pyKooCAE
python3 tests/iga_tests/test_iga_standalone.py
```
