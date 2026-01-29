# pyKooCAE 빌드 시스템 완전 가이드

## 📦 빌드 대상

이 프로젝트는 3개의 실행 파일을 빌드합니다:

| 도구 | 설명 | 크기 | 플랫폼 |
|-----|------|------|-------|
| **koocr** | 누적 낙하 시뮬레이션 워크플로우 CLI | ~50-100 MB | Linux, Windows |
| **KooMeshModifier** | LS-DYNA 메시 변환 GUI/CLI | ~600-700 MB | Linux, Windows |
| **KooAutomatedModeller** | ODB CAD 자동 모델링 도구 | ~600-700 MB | Linux, Windows |

---

## 🚀 빠른 시작

### Linux (권장: Python 3.12)

```bash
# 통합 빌드 (3개 도구 모두)
./build_all_python312.sh

# 결과: build_dist/bin/ 에 3개 실행 파일 생성
```

### Windows (권장: Python 3.12)

```cmd
REM 개별 빌드
build_koocr_windows.bat
cd occProject\Generators
build_meshmodifier_windows.bat
build_automatedmodeller_windows.bat
```

---

## 📁 파일 구조

### Linux 빌드 스크립트

```
/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/
│
├── build_all_python310.sh              # 통합 빌드 (Python 3.10)
├── build_all_python312.sh              # 통합 빌드 (Python 3.12) ⭐ 권장
├── build_all_python313.sh              # 통합 빌드 (Python 3.13, ⚠️ PythonOCC 없음)
│
├── build_koocr_python310.sh            # koocr 단독 (Python 3.10)
├── build_koocr_python312.sh            # koocr 단독 (Python 3.12)
├── build_koocr_python313.sh            # koocr 단독 (Python 3.13)
│
└── occProject/Generators/
    ├── build_meshmodifier_python310.sh         # KooMeshModifier (Python 3.10)
    ├── build_meshmodifier_python312.sh         # KooMeshModifier (Python 3.12)
    ├── build_meshmodifier_python313.sh         # KooMeshModifier (Python 3.13)
    │
    ├── build_automatedmodeller_python310.sh    # KooAutomatedModeller (Python 3.10)
    ├── build_automatedmodeller_python312.sh    # KooAutomatedModeller (Python 3.12)
    └── build_automatedmodeller_python313.sh    # KooAutomatedModeller (Python 3.13)
```

### Windows 빌드 스크립트

```
C:\pyKooCAE\
│
├── build_koocr_windows.bat             # koocr 빌드
│
└── occProject\Generators\
    ├── build_meshmodifier_windows.bat          # KooMeshModifier 빌드
    └── build_automatedmodeller_windows.bat     # KooAutomatedModeller 빌드
```

---

## 📋 Requirements 파일

| 파일 | 용도 | 패키지 수 |
|-----|------|----------|
| `requirements_python312.txt` | Windows 설치용 (주석 포함) | ~40개 (핵심) |
| `requirements_python312_full.txt` | 전체 의존성 (pip freeze) | 176개 |

---

## 🛠️ 빌드 환경 설정

### Linux

```bash
# Python 3.12 가상환경 생성
python3.12 -m venv venv312
source venv312/bin/activate

# 패키지 설치
pip install --upgrade pip
pip install -r requirements_python312_full.txt

# PythonOCC는 별도 설치 필요 (conda 권장)
```

### Windows

1. **Python 3.12 설치**
2. **Miniconda 설치** (PythonOCC를 위해)
3. **가상환경 생성**:
   ```cmd
   conda create -n pykooCAE python=3.12
   conda activate pykooCAE
   ```
4. **PythonOCC 설치**:
   ```cmd
   conda install -c conda-forge pythonocc-core=7.9.0
   ```
5. **패키지 설치**:
   ```cmd
   pip install -r requirements_python312.txt
   ```
6. **Visual Studio Build Tools 설치** (Nuitka용)

자세한 내용: [WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md)

---

## 📚 상세 문서

| 문서 | 설명 |
|-----|------|
| [UNIFIED_BUILD_GUIDE.md](UNIFIED_BUILD_GUIDE.md) | 통합 빌드 시스템 상세 가이드 |
| [WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md) | Windows 환경 설정 및 빌드 가이드 |
| [COMPLETE_BUILD_SUMMARY.md](COMPLETE_BUILD_SUMMARY.md) | 빠른 참조 요약 |
| [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) | PathResolver 통합 완성 요약 |

---

## 🎯 주요 기능

### 1. PathResolver 자동 경로 탐색

koocr이 KooMeshModifier를 자동으로 찾는 순서:

1. **상대 경로** - koocr와 같은 bin 디렉토리
2. **환경 변수** - `$KOO_PATH/bin/KooMeshModifier`
3. **설정 파일** - scenario.json의 koomeshmodifier_path
4. **기본 경로** - `/opt/pyKooCAE/bin/KooMeshModifier`

**파일**: [Runner/PathResolver.py](Runner/PathResolver.py)

### 2. 통합 빌드 출력 구조

```
build_dist/
├── bin/
│   ├── koocr                           # 심볼릭 링크 → ../lib/koocr/koocr.bin
│   ├── KooMeshModifier                 # 심볼릭 링크 → ../lib/KooMeshModifier/KooMeshModifier.bin
│   └── KooAutomatedModeller            # 심볼릭 링크 → ../lib/KooAutomatedModeller/KooAutomatedModeller.bin
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

---

## 💡 사용 예제

### 빌드 후 배포

```bash
# Linux
sudo cp -r build_dist /opt/pyKooCAE
export PATH=/opt/pyKooCAE/bin:$PATH

# 실행
koocr --version
KooMeshModifier --help
KooAutomatedModeller --help
```

### 환경 변수 설정

```bash
# koocr이 KooMeshModifier를 찾을 수 있도록
export KOO_PATH=/opt/pyKooCAE
```

---

## ⚙️ Python 버전별 특징

| Python 버전 | PythonOCC | 권장 여부 | 비고 |
|------------|-----------|----------|------|
| 3.10.12 | ✅ 7.9.0 | ✅ | 안정적 |
| 3.12.12 | ✅ 7.9.0 | ✅ **권장** | 최신 패키지, 안정적 |
| 3.13.11 | ❌ | ⚠️ | PythonOCC 없음 (koocr만 빌드 가능) |

---

## 🔧 문제 해결

### Linux

**Q**: PythonOCC import 에러  
**A**: Python 3.12 사용 (venv312에 설치됨)

**Q**: koocr이 KooMeshModifier를 찾지 못함  
**A**: 통합 빌드 사용 또는 `export KOO_PATH=/opt/pyKooCAE`

### Windows

**Q**: "python" 명령을 찾을 수 없음  
**A**: Python PATH 설정 확인

**Q**: Nuitka 빌드 시 "cl.exe not found"  
**A**: Developer Command Prompt for VS 2022 사용

**Q**: PythonOCC import 에러  
**A**: `conda install -c conda-forge pythonocc-core=7.9.0`

---

## 📊 빌드 시간 예상

| 도구 | Linux | Windows |
|-----|-------|---------|
| koocr | 2-5분 | 5-10분 |
| KooMeshModifier | 10-20분 | 20-40분 |
| KooAutomatedModeller | 10-20분 | 20-40분 |
| **전체 통합 빌드** | 30-50분 | N/A (개별 빌드만) |

---

## 📞 지원

- **작성자**: koo.park
- **이메일**: koo.park@samsung.com
- **그룹**: CAE
- **프로젝트**: pyKooCAE

---

**최종 업데이트**: 2026-01-29
