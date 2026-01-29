# KooMeshModifier 빌드 가이드

## 빌드 스크립트 종류

### 1. Python 3.10 빌드
```bash
./build_python310.sh
```
- **venv**: `../../venv`
- **Python 버전**: 3.10.12
- **패키지 버전**:
  - numpy: 2.2.6
  - scipy: 1.14.1
  - vtk: 9.2.6
  - PyQt5: 5.15.9
  - trimesh: 4.6.6

### 2. Python 3.12 빌드
```bash
./build_python312.sh
```
- **venv**: `../../venv312`
- **Python 버전**: 3.12.12
- **패키지 버전** (최신):
  - numpy: 2.2.6
  - scipy: 1.16.2
  - vtk: 9.5.2
  - PyQt5: 5.15.11
  - trimesh: 4.8.3

### 3. Python 3.13 빌드 (권장)
```bash
./build_python313.sh
```
- **venv**: `../../venv313`
- **Python 버전**: 3.13.11
- **패키지 버전** (최신):
  - numpy: 2.4.1 ⚡
  - scipy: 1.17.0 ⚡
  - vtk: 9.5.2
  - PyQt5: 5.15.11
  - trimesh: 4.6.6
  - nuitka: 2.8.10 ⚡
  - matplotlib: 3.9.2
  - pandas: 2.2.3

---

## 빌드 과정

각 빌드 스크립트는 다음 작업을 수행합니다:

1. **기존 빌드 결과 제거**
   ```bash
   rm -rf KooMeshModifier.build KooMeshModifier.dist .nuitka
   ```

2. **Nuitka로 컴파일**
   - `--standalone`: 독립 실행 파일 생성 (Python 런타임 포함)
   - `--enable-plugin=pyqt5`: PyQt5 플러그인 활성화
   - `--jobs=8`: 8개 병렬 작업으로 빌드 속도 향상
   - `--include-package=OCC`: OpenCascade 패키지 포함
   - `--include-package=vtk`: VTK 패키지 포함
   - `--include-package=trimesh`: Trimesh 패키지 포함
   - `--follow-imports`: 모든 import 추적
   - `--show-progress`: 진행 상황 표시

3. **출력 결과**
   - 디렉토리: `KooMeshModifier.dist/`
   - 실행 파일: `KooMeshModifier.dist/KooMeshModifier.bin` (약 650MB)

---

## 빌드 시간

- **예상 시간**: 10~30분 (시스템 성능에 따라 다름)
- **병렬 작업**: `--jobs=8` 옵션으로 멀티코어 활용
- **메모리 사용**: 빌드 중 4~8GB RAM 사용

---

## 빌드 후 테스트

빌드가 완료되면 자동으로 실행 테스트가 수행됩니다:

```bash
cd KooMeshModifier.dist
./KooMeshModifier.bin --help
```

---

## 배포

빌드된 `KooMeshModifier.dist/` 디렉토리 전체를 배포해야 합니다:

```bash
# 예: /opt/KooMeshModifier/로 배포
sudo cp -r KooMeshModifier.dist /opt/KooMeshModifier/

# 실행 스크립트 생성
sudo tee /opt/KooMeshModifier/run.sh > /dev/null <<'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
./KooMeshModifier.bin "$@"
EOF

sudo chmod +x /opt/KooMeshModifier/run.sh
```

---

## Python 버전 선택 기준

### Python 3.10 사용 시점:
- 안정성이 가장 중요한 경우
- 기존 시스템과의 호환성 유지 필요

### Python 3.12 사용 시점:
- 최신 패키지 버전 필요 (scipy 1.16, vtk 9.5)
- 성능 개선 필요 (Python 3.12의 속도 향상)

### Python 3.13 사용 시점 (권장):
- 최신 Python 기능 사용
- Free-threaded 모드 (GIL 제거) 실험 가능
- 향후 지원 기간 가장 긺

---

## 문제 해결

### 빌드 실패 시:

1. **venv 확인**
   ```bash
   ../../venv313/bin/python --version
   ../../venv313/bin/pip list | grep nuitka
   ```

2. **Nuitka 설치 확인**
   ```bash
   ../../venv313/bin/pip install nuitka
   ```

3. **메모리 부족 시**
   - `--jobs=8`을 `--jobs=4`로 줄이기
   - swap 메모리 증가

4. **패키지 누락 시**
   ```bash
   ../../venv313/bin/pip install -r requirements.txt
   ```

---

## 버전 정보 확인

빌드된 바이너리의 Python 버전 확인:

```bash
strings KooMeshModifier.dist/KooMeshModifier.bin | grep "Python 3\."
```

---

**생성일**: 2026-01-29
**작성자**: Claude
**빌드 도구**: Nuitka (Python to binary compiler)
