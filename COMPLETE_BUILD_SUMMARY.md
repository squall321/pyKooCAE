# pyKooCAE 완전 통합 빌드 시스템 - 요약

## 빌드 대상 (3개 도구)

1. **koocr** - 누적 낙하 시뮬레이션 워크플로우 CLI 도구
2. **KooMeshModifier** - LS-DYNA 메시 변환 GUI/CLI 도구  
3. **KooAutomatedModeller** - ODB CAD 자동 모델링 도구

---

## 빠른 시작

### 권장: 통합 빌드 (Python 3.12)

```bash
cd /home/koopark/serviceApptainers/appt313/opt/pyKooCAE
./build_all_python312.sh
```

### 빌드 결과

```
build_dist/
├── bin/
│   ├── koocr
│   ├── KooMeshModifier
│   └── KooAutomatedModeller
└── lib/
    ├── koocr/
    ├── KooMeshModifier/
    └── KooAutomatedModeller/
```

### 배포

```bash
sudo cp -r build_dist /opt/pyKooCAE
export PATH=/opt/pyKooCAE/bin:$PATH
```

---

## 전체 빌드 스크립트 목록

### 통합 빌드 (모든 도구)

| 스크립트 | Python 버전 | 권장 |
|---------|------------|------|
| `build_all_python310.sh` | 3.10.12 | ✅ |
| `build_all_python312.sh` | 3.12.12 | ✅ **권장** |
| `build_all_python313.sh` | 3.13.11 | ⚠️ PythonOCC 없음 |

### koocr 단독 빌드

| 스크립트 | Python 버전 |
|---------|------------|
| `build_koocr_python310.sh` | 3.10.12 |
| `build_koocr_python312.sh` | 3.12.12 |
| `build_koocr_python313.sh` | 3.13.11 |

### KooMeshModifier 단독 빌드

| 스크립트 | Python 버전 | 위치 |
|---------|------------|------|
| `build_meshmodifier_python310.sh` | 3.10.12 | occProject/Generators/ |
| `build_meshmodifier_python312.sh` | 3.12.12 | occProject/Generators/ |
| `build_meshmodifier_python313.sh` | 3.13.11 | occProject/Generators/ |

### KooAutomatedModeller 단독 빌드

| 스크립트 | Python 버전 | 위치 |
|---------|------------|------|
| `build_automatedmodeller_python310.sh` | 3.10.12 | occProject/Generators/ |
| `build_automatedmodeller_python312.sh` | 3.12.12 | occProject/Generators/ |
| `build_automatedmodeller_python313.sh` | 3.13.11 | occProject/Generators/ |

---

## 빌드 크기 예상

| 도구 | 크기 | 주요 의존성 |
|-----|------|-----------|
| koocr | ~50-100 MB | numpy, scipy, Runner |
| KooMeshModifier | ~600-700 MB | PythonOCC, VTK, PyQt5, trimesh |
| KooAutomatedModeller | ~600-700 MB | PythonOCC, VTK, PyQt5, trimesh |
| **전체** | ~1.3-1.5 GB | - |

---

## PathResolver 자동 경로 탐색

koocr이 KooMeshModifier를 자동으로 찾는 순서:

1. **상대 경로** - koocr와 같은 bin 디렉토리
2. **환경 변수** - `$KOO_PATH/bin/KooMeshModifier`
3. **설정 파일** - scenario.json의 koomeshmodifier_path
4. **기본 경로** - /opt/pyKooCAE/bin/KooMeshModifier

---

## 실행 예제

```bash
# 실행 파일 확인
ls -lh build_dist/bin/

# koocr 실행
koocr --version
koocr prepare scenario.json

# KooMeshModifier 실행
KooMeshModifier --help
KooMeshModifier config.json

# KooAutomatedModeller 실행
KooAutomatedModeller --help
KooAutomatedModeller
```

---

**작성**: 2026-01-29  
**작성자**: Claude Code (Sonnet 4.5)
