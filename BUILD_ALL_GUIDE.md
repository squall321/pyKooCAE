# pyKooCAE 전체 빌드 가이드

## 빌드 대상

이 프로젝트에는 두 개의 독립 실행 파일이 있습니다:

1. **KooMeshModifier**: LS-DYNA 메쉬 변환 및 전처리 도구
2. **koocr (KooChainRun)**: 누적 낙하 시뮬레이션 자동화 CLI 도구

---

## 1. KooMeshModifier 빌드

### 위치
```bash
cd /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/occProject/Generators
```

### 빌드 스크립트

#### Python 3.10
```bash
./build_python310.sh
```
- PythonOCC 7.9.0 포함
- 안정적인 버전

#### Python 3.12 (권장)
```bash
./build_python312.sh
```
- PythonOCC 7.9.0 포함
- 최신 패키지 (numpy 2.4.1, scipy 1.17.0)
- 모든 의존성 준비 완료 ✅

#### Python 3.13
```bash
./build_python313.sh
```
- ⚠️ PythonOCC 미설치
- 3.13용 PythonOCC 빌드 필요

### 출력 결과
- **디렉토리**: `KooMeshModifier.dist/`
- **실행 파일**: `KooMeshModifier.dist/KooMeshModifier.bin` (~650MB)
- **패키지 포함**: OCC, VTK, PyQt5, trimesh, numpy, scipy 등 모든 의존성

### 배포
```bash
# 전체 디렉토리 배포 (추천)
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

## 2. koocr (KooChainRun) 빌드

### 위치
```bash
cd /home/koopark/serviceApptainers/appt313/opt/pyKooCAE
```

### 빌드 스크립트

#### Python 3.10
```bash
./build_koocr_python310.sh
```

#### Python 3.12 (권장)
```bash
./build_koocr_python312.sh
```

#### Python 3.13
```bash
./build_koocr_python313.sh
```
- ⚠️ PythonOCC 불필요 (koocr는 OCC 사용 안 함)
- Runner 모듈만 필요

### 출력 결과
- **실행 파일**: `koocr.bin` (단일 파일, ~50-100MB)
- **패키지 포함**: Runner 모듈, 표준 라이브러리

### 배포
```bash
# 시스템 전역 설치
sudo cp koocr.bin /usr/local/bin/koocr
sudo chmod +x /usr/local/bin/koocr

# 또는 사용자 로컬 설치
mkdir -p ~/.local/bin
cp koocr.bin ~/.local/bin/koocr
chmod +x ~/.local/bin/koocr
```

### 사용 예시
```bash
koocr --version
koocr prepare scenario.json
koocr submit runner_config.json --nodes 10 --jobs-per-node 4
koocr status
```

---

## 빌드 차이점

| 항목 | KooMeshModifier | koocr |
|------|----------------|-------|
| **진입점** | `occProject/Generators/KooMeshModifier.py` | `koocr` |
| **주요 의존성** | PythonOCC, VTK, PyQt5, trimesh | Runner 모듈만 |
| **출력 형식** | `--standalone` (디렉토리) | `--onefile` (단일 파일) |
| **크기** | ~650MB | ~50-100MB |
| **PythonOCC 필요** | ✅ 필수 | ❌ 불필요 |
| **배포** | 전체 디렉토리 | 단일 실행 파일 |

---

## 빌드 옵션 비교

### KooMeshModifier (--standalone)
```bash
--standalone           # 디렉토리 형태로 패키징
--enable-plugin=pyqt5  # PyQt5 플러그인
--include-package=OCC  # PythonOCC 포함
--include-package=vtk  # VTK 포함
```

### koocr (--onefile)
```bash
--standalone           # 독립 실행
--onefile              # 단일 실행 파일로 압축
--include-package=Runner  # Runner 모듈만
```

---

## 권장 빌드 조합

### 프로덕션 환경 (안정성 우선)
```bash
# KooMeshModifier: Python 3.10
cd occProject/Generators
./build_python310.sh

# koocr: Python 3.10
cd ../..
./build_koocr_python310.sh
```

### 최신 환경 (성능 우선)
```bash
# KooMeshModifier: Python 3.12
cd occProject/Generators
./build_python312.sh

# koocr: Python 3.12
cd ../..
./build_koocr_python312.sh
```

---

## 빌드 시간

| 도구 | Python 버전 | 예상 시간 |
|------|-----------|---------|
| KooMeshModifier | 3.10 | 15-30분 |
| KooMeshModifier | 3.12 | 15-30분 |
| koocr | 3.10 | 5-10분 |
| koocr | 3.12 | 5-10분 |

---

## 빌드 확인

### KooMeshModifier
```bash
cd occProject/Generators/KooMeshModifier.dist
./KooMeshModifier.bin --help
```

### koocr
```bash
./koocr.bin --version
./koocr.bin --help
```

---

## 문제 해결

### PythonOCC 없음 (venv313)
```bash
# Python 3.13용 PythonOCC 빌드 필요
# 또는 Python 3.12 사용 권장
```

### 빌드 실패 시
```bash
# 메모리 부족: --jobs 줄이기
--jobs=4  # 기본값 8에서 4로

# 의존성 확인
venv312/bin/pip list | grep -E "(nuitka|numpy|scipy|vtk)"
```

---

## 버전 정보

### 현재 환경 (2026-01-29)
- **venv (3.10)**: PythonOCC 7.9.0, numpy 2.2.6, scipy 1.14.1
- **venv312 (3.12)**: PythonOCC 7.9.0, numpy 2.4.1, scipy 1.17.0 ✅
- **venv313 (3.13)**: PythonOCC 없음, numpy 2.4.1, scipy 1.17.0

---

**생성일**: 2026-01-29
**작성자**: Claude
**빌드 도구**: Nuitka 2.8.10
