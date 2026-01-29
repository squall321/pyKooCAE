# pyKooCAE 통합 빌드 가이드

## 개요

pyKooCAE 프로젝트는 세 개의 주요 실행 파일을 포함합니다:

1. **koocr** (KooChainRun): 누적 낙하 시뮬레이션 워크플로우 CLI 도구
2. **KooMeshModifier**: LS-DYNA 메시 변환 GUI/CLI 도구
3. **KooAutomatedModeller**: ODB CAD 자동 모델링 도구

이 가이드는 통합 빌드 시스템을 통해 세 실행 파일을 단일 배포 패키지로 빌드하는 방법을 설명합니다.

---

## 빌드 환경

### Python 버전별 가상환경

| 가상환경 | Python 버전 | PythonOCC | numpy | scipy | 상태 |
|---------|------------|-----------|-------|-------|------|
| venv | 3.10.12 | 7.9.0 ✅ | 2.4.1 | 1.17.0 | ✅ 사용 가능 |
| venv312 | 3.12.12 | 7.9.0 ✅ | 2.4.1 | 1.17.0 | ✅ **권장** |
| venv313 | 3.13.11 | ❌ 없음 | 2.4.1 | 1.17.0 | ⚠️ PythonOCC 없음 |

**권장 빌드 환경**: Python 3.12 (venv312)
- 최신 패키지 지원
- PythonOCC 7.9.0 설치됨
- 안정적인 C++ 확장 호환성

---

## 통합 빌드 시스템

### 디렉토리 구조

빌드 완료 후 다음과 같은 구조가 생성됩니다:

```
build_dist/
├── bin/
│   ├── koocr -> ../lib/koocr/koocr.bin
│   ├── KooMeshModifier -> ../lib/KooMeshModifier/KooMeshModifier.bin
│   └── KooAutomatedModeller -> ../lib/KooAutomatedModeller/KooAutomatedModeller.bin
└── lib/
    ├── koocr/
    │   ├── koocr.bin
    │   └── [dependencies...]
    ├── KooMeshModifier/
    │   ├── KooMeshModifier.bin
    │   └── [dependencies...]
    └── KooAutomatedModeller/
        ├── KooAutomatedModeller.bin
        └── [dependencies...]
```

### 장점

1. **단일 배포 패키지**: 모든 실행 파일이 하나의 디렉토리에 통합
2. **상대 경로 지원**: koocr이 자동으로 같은 bin 디렉토리의 KooMeshModifier 탐색
3. **심볼릭 링크**: bin/ 디렉토리에서 간편하게 실행
4. **의존성 분리**: 각 도구의 의존성이 lib/ 하위에 독립적으로 관리

---

## 빌드 방법

### 1. 통합 빌드 (권장)

Python 3.12 기반 통합 빌드:

```bash
cd /home/koopark/serviceApptainers/appt313/opt/pyKooCAE
./build_all_python312.sh
```

출력:
- `build_dist/bin/koocr`
- `build_dist/bin/KooMeshModifier`
- `build_dist/lib/koocr/`
- `build_dist/lib/KooMeshModifier/`

### 2. 개별 빌드

#### koocr만 빌드

```bash
# Python 3.10
./build_koocr_python310.sh

# Python 3.12 (권장)
./build_koocr_python312.sh

# Python 3.13
./build_koocr_python313.sh
```

출력: `koocr.dist/koocr.bin`

#### KooMeshModifier만 빌드

```bash
cd occProject/Generators

# Python 3.10
./build_python310.sh

# Python 3.12 (권장)
./build_python312.sh

# Python 3.13 (⚠️ PythonOCC 없음)
./build_python313.sh
```

출력: `KooMeshModifier.dist/KooMeshModifier.bin`

---

## 경로 탐색 시스템 (PathResolver)

koocr은 KooMeshModifier를 다음 우선순위로 자동 탐색합니다:

### 탐색 우선순위

1. **상대 경로** (최우선)
   - koocr 실행 파일과 같은 bin 디렉토리 확인
   - 예: `/opt/pyKooCAE/bin/KooMeshModifier`
   - 통합 빌드 배포 시 자동으로 동작

2. **환경 변수: KOO_PATH**
   ```bash
   export KOO_PATH=/custom/path/to/pyKooCAE
   # 탐색: $KOO_PATH/bin/KooMeshModifier
   ```
   또는 직접 실행 파일 지정:
   ```bash
   export KOO_PATH=/custom/path/KooMeshModifier.bin
   ```

3. **설정 파일** (scenario.json)
   ```json
   {
       "environment": {
           "koomeshmodifier_path": "/custom/path/KooMeshModifier"
       }
   }
   ```

4. **기본 경로**
   - `/opt/pyKooCAE/bin/KooMeshModifier`
   - `/opt/KooMeshModifier/run.sh`
   - `/usr/local/bin/KooMeshModifier`

### 구현 파일

- `Runner/PathResolver.py`: 경로 탐색 로직
- `Runner/CumulativeDesigner.py`: PathResolver 통합 (line 112)

---

## 배포 방법

### 1. 시스템 전역 설치

```bash
# 빌드 결과를 /opt로 복사
sudo cp -r build_dist /opt/pyKooCAE

# PATH에 추가
echo 'export PATH=/opt/pyKooCAE/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# 또는 심볼릭 링크 생성
sudo ln -sf /opt/pyKooCAE/bin/koocr /usr/local/bin/koocr
sudo ln -sf /opt/pyKooCAE/bin/KooMeshModifier /usr/local/bin/KooMeshModifier
```

### 2. 사용자 로컬 설치

```bash
# 홈 디렉토리에 복사
cp -r build_dist ~/bin/pyKooCAE

# PATH 추가
echo 'export PATH=~/bin/pyKooCAE/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### 3. 환경 변수 설정 (선택)

커스텀 경로 사용 시:

```bash
# KooMeshModifier 경로만 지정
export KOO_PATH=/custom/install/location

# 또는 전체 PATH
export PATH=/custom/install/location/bin:$PATH
```

---

## 실행 테스트

### koocr 테스트

```bash
# 버전 확인
koocr --version

# 도움말
koocr --help

# 시나리오 준비
koocr prepare scenario.json

# 작업 제출
koocr submit scenario.json
```

### KooMeshModifier 테스트

```bash
# 도움말
KooMeshModifier --help

# GUI 모드
KooMeshModifier

# CLI 모드
KooMeshModifier config.json
```

---

## 빌드 크기 참고

| 도구 | 예상 크기 | 주요 의존성 |
|-----|----------|-----------|
| koocr | ~50-100 MB | Runner, numpy, scipy |
| KooMeshModifier | ~600-700 MB | PythonOCC, VTK, PyQt5, trimesh |
| **전체** | ~700-800 MB | - |

---

## 문제 해결

### Q: koocr이 KooMeshModifier를 찾지 못함

**A1**: 통합 빌드 사용 시 자동 탐색됩니다:
```bash
./build_all_python312.sh
```

**A2**: 환경 변수 설정:
```bash
export KOO_PATH=/opt/pyKooCAE
```

**A3**: scenario.json에 명시:
```json
{
    "environment": {
        "koomeshmodifier_path": "/path/to/KooMeshModifier"
    }
}
```

### Q: PythonOCC import 에러

**A**: Python 3.12 사용 (venv312에 PythonOCC 7.9.0 설치됨):
```bash
./build_all_python312.sh
```

Python 3.13은 현재 PythonOCC 미설치 상태입니다.

### Q: 빌드 시간이 오래 걸림

**A**: Nuitka 빌드는 시간이 소요됩니다:
- KooMeshModifier: ~10-20분 (대량의 C++ 의존성)
- koocr: ~2-5분
- `--jobs=8` 옵션으로 병렬 빌드 활성화됨

### Q: 실행 시 /tmp 공간 부족

**A**: `--standalone` 모드 사용 (현재 설정):
- ✅ `--standalone`: 디렉토리 형태, /tmp 미사용
- ❌ `--onefile`: 단일 파일, 실행마다 /tmp에 압축 해제

---

## 개발자 참고

### Nuitka 빌드 옵션 설명

| 옵션 | 설명 |
|------|-----|
| `--standalone` | 모든 의존성 포함한 디렉토리 생성 |
| `--onefile` | 단일 실행 파일 (압축, /tmp 사용) |
| `--follow-imports` | 자동으로 모든 import 추적 |
| `--include-package` | 특정 패키지 명시적 포함 |
| `--enable-plugin` | PyQt5 등 특수 플러그인 활성화 |
| `--jobs=N` | 병렬 빌드 (CPU 코어 수) |

### 빌드 스크립트 파일

| 파일 | 설명 |
|-----|------|
| `build_all_python312.sh` | 통합 빌드 (koocr + KooMeshModifier) |
| `build_koocr_python310.sh` | koocr 단독 (Python 3.10) |
| `build_koocr_python312.sh` | koocr 단독 (Python 3.12) |
| `build_koocr_python313.sh` | koocr 단독 (Python 3.13) |
| `occProject/Generators/build_python310.sh` | KooMeshModifier (Python 3.10) |
| `occProject/Generators/build_python312.sh` | KooMeshModifier (Python 3.12) |
| `occProject/Generators/build_python313.sh` | KooMeshModifier (Python 3.13, ⚠️ PythonOCC 없음) |

---

## 라이선스 및 작성자

- **Author**: koo.park
- **Email**: koo.park@samsung.com
- **Group**: CAE
- **Project**: pyKooCAE - Python-based CAE automation tools

---

**마지막 업데이트**: 2026-01-29
