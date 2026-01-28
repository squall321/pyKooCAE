# Full Angle Drop - Fibonacci Lattice Method

## Overview

전각도(Full Angle) 낙하 시뮬레이션을 위한 구면 균등 분포 생성 방법입니다.

---

## 1. 피보나치 격자 (Fibonacci Lattice) 원리

### 1.1 핵심 개념

피보나치 격자는 **황금각(Golden Angle)**을 이용하여 구면에 점을 균등하게 배치하는 알고리즘입니다.

```
황금각 φ = π × (3 - √5) ≈ 137.508° ≈ 2.39996 rad
```

황금각은 원을 황금비(Golden Ratio)로 분할하는 각도로, 점들이 서로 겹치지 않고 최대한 균등하게 분포되도록 합니다.

### 1.2 알고리즘

```python
import math

def fibonacci_sphere(n):
    """
    피보나치 격자로 N개 점을 구면에 균등 분포

    Parameters:
        n: 생성할 점의 개수

    Returns:
        List of (x, y, z) unit vectors
    """
    points = []
    phi = math.pi * (3.0 - math.sqrt(5.0))  # 황금각

    for i in range(n):
        # y: 1 ~ -1 균등 분포 (위도 방향)
        y = 1 - (i / float(n - 1)) * 2

        # xz 평면에서의 반지름
        radius = math.sqrt(1 - y * y)

        # 황금각 누적 (경도 방향)
        theta = phi * i

        # 직교 좌표
        x = math.cos(theta) * radius
        z = math.sin(theta) * radius

        points.append((x, y, z))

    return points
```

### 1.3 수학적 배경

**위도 분포 (y 좌표)**:
```
y_i = 1 - 2i/(n-1),  i = 0, 1, 2, ..., n-1
```
- y는 -1에서 1까지 균등하게 분포
- 이는 구면의 **면적**이 위도에 따라 cos(latitude)로 변하기 때문에 면적 기준 균등 분포를 보장

**경도 분포 (θ 각도)**:
```
θ_i = φ × i,  여기서 φ = π(3 - √5)
```
- 황금각을 누적하여 나선형으로 점 배치
- 황금각은 무리수이므로 점들이 절대 정확히 겹치지 않음

---

## 2. 케이스 수 vs 각도 간격 공식

### 2.1 이론적 공식

구면에 N개의 점을 균등 배치할 때, 평균 각도 간격 θ는:

```
θ ≈ √(4π/N) × (180/π) [도]
```

또는 간단히:
```
θ ≈ 233.6 / √N [도]
```

### 2.2 역산 공식

목표 각도 간격 θ로부터 필요한 케이스 수 N:

```
N ≈ 4π / (θ × π/180)² = 41253 / θ² [개]
```

### 2.3 참조표

| 목표 각도 | 케이스 수 | 실제 각도 | 용도 |
|----------|----------|----------|------|
| 40° | 26 | 39.83° | 빠른 검증 |
| 20° | 103 | 20.01° | 표준 분석 |
| 10° | 413 | 9.99° | 상세 분석 |
| 6° | 1,146 | 6.00° | 정밀 분석 |
| 5° | 1,650 | 5.00° | 정밀 분석 |
| 4° | 2,578 | 4.00° | 고정밀 분석 |
| 2° | 10,313 | 2.00° | 초고정밀 |
| 1° | 41,253 | 1.00° | 연구용 |

---

## 3. 방향 벡터 → 오일러 각도 변환

### 3.1 변환 공식

구면 위의 점 (x, y, z)를 낙하 방향으로 사용하기 위한 오일러 각도 변환:

```python
import math

def vector_to_euler(x, y, z):
    """
    방향 벡터를 오일러 각도 (Roll, Pitch, Yaw)로 변환

    좌표계:
        - 원점: 스마트폰 하단 중심
        - +Z: 디스플레이 방향 (전면)
        - +X: 오른쪽
        - +Y: 위쪽

    Returns:
        (roll, pitch, yaw) in degrees
    """
    # 구면 좌표 계산
    r = math.sqrt(x*x + y*y + z*z)

    # 위도 (y축 기준)
    lat = math.asin(y / r) if r != 0 else 0

    # 경도 (xz 평면)
    lon = math.atan2(z, x)

    # 오일러 각도 변환
    roll = math.degrees(lat) - 90  # y축 기준 기울기
    pitch = -math.degrees(lon)      # xz 평면 회전
    yaw = 0

    return (round(roll, 2), round(pitch, 2), round(yaw, 2))
```

---

## 4. 몰바이데 투영 검증

### 4.1 면적 보존 특성

피보나치 격자의 균등성은 **면적 보존 투영법**인 몰바이데(Mollweide) 투영에서 검증할 수 있습니다.

```
피보나치 격자: 구면 면적 기준 균등 분포
몰바이데 투영: 면적 보존 투영법

→ 몰바이데 투영에서 점이 균등하게 보이면 정상!
```

### 4.2 시각적 검증 (103개 예시)

```
피보나치 격자 103개 - 몰바이데 투영 (면적 보존)
================================================================================
                                        *
                               *                  *
                   *                         *
                                   *                  *
                      *                    *                    *
                             *                     *
              *                      *                        *
                      *                        *                        *
               *               *                         *
                        *                *          *               *
       *                          *                            *
                 *                           *                            *
         *                 *          *                  *
 *                  *                             *                 *
             *                 *                             *
                        *                  *           *                 *
     *           *                  *                             *
                            *                  *                              *
          *                             *                  *           *
   *                 *           *                  *
              *                              *                 *
        *                 *                             *                 *
                   *                 *           *                 *
  *                            *                           *
             *                            *                          *
        *                *         *                *
                   *                         *                *
                              *                       *                *
               *                       *                      *
                         *                      *
             *                    *                   *
                       *                  *
                                *                          *
                            *                 *
================================================================================
```

### 4.3 통계 검증 (103개)

```
최근접 점 거리 통계:
  평균: 18.78°
  최소: 11.36°
  최대: 19.54°
  표준편차: 1.56° (매우 균일!)

이론적 평균 간격: 20.01°
```

---

## 5. 파일 목록

### 5.1 직육면체 기하 (Cuboid Geometry)

| 파일 | 케이스 수 | 설명 |
|------|----------|------|
| `26case_6F12E8C_cuboid.txt` | 26 | 6면 + 12모서리 + 8꼭짓점 |

### 5.2 피보나치 격자 (Fibonacci Lattice)

| 파일 | 케이스 수 | 각도 간격 |
|------|----------|----------|
| `fibonacci_40deg_26cases.txt` | 26 | ~40° |
| `fibonacci_20deg_103cases.txt` | 103 | ~20° |
| `fibonacci_10deg_413cases.txt` | 413 | ~10° |
| `fibonacci_06deg_1146cases.txt` | 1,146 | ~6° |
| `fibonacci_05deg_1650cases.txt` | 1,650 | ~5° |
| `fibonacci_04deg_2578cases.txt` | 2,578 | ~4° |
| `fibonacci_02deg_10313cases.txt` | 10,313 | ~2° |
| `fibonacci_01deg_41253cases.txt` | 41,253 | ~1° |

---

## 6. 26케이스 직육면체 기하 vs 피보나치 비교

### 6.1 차이점

| 항목 | 직육면체 기하 (26case_6F12E8C) | 피보나치 격자 (fibonacci_40deg) |
|------|------------------------------|-------------------------------|
| 배치 방식 | 기하학적 (면/모서리/꼭짓점) | 수학적 (황금각 나선) |
| 물리적 의미 | 직육면체 제품에 직관적 | 순수 균등 분포 |
| 각도 분포 | 45°, 90° 등 특정 각도 | 연속적 분포 |
| 용도 | 스마트폰 등 직육면체 제품 | 일반적 구면 분석 |

### 6.2 권장 사용

- **직육면체 제품 (스마트폰, 태블릿)**: `26case_6F12E8C_cuboid.txt`
- **일반적 전각도 분석**: `fibonacci_*` 시리즈

---

## 7. Python 유틸리티 코드

### 7.1 완전한 생성 코드

```python
import math

def fibonacci_sphere_euler(n):
    """
    피보나치 격자 N개 점을 오일러 각도로 반환

    Returns:
        List of (name, roll, pitch, yaw)
    """
    phi = math.pi * (3.0 - math.sqrt(5.0))
    results = []

    for i in range(n):
        y = 1 - (i / float(n - 1)) * 2 if n > 1 else 0
        radius = math.sqrt(1 - y * y)
        theta = phi * i

        x = math.cos(theta) * radius
        z = math.sin(theta) * radius

        # 오일러 각도 변환
        r = math.sqrt(x*x + y*y + z*z)
        lat = math.asin(y / r) if r != 0 else 0
        lon = math.atan2(z, x)

        roll = math.degrees(lat) - 90
        pitch = -math.degrees(lon)
        yaw = 0

        results.append((f"P{i+1:04d}", round(roll, 2), round(pitch, 2), round(yaw, 2)))

    return results

def angle_to_cases(angle_deg):
    """목표 각도 간격 → 필요 케이스 수"""
    angle_rad = angle_deg * math.pi / 180
    return round(4 * math.pi / (angle_rad ** 2))

def cases_to_angle(n):
    """케이스 수 → 평균 각도 간격"""
    return math.sqrt(4 * math.pi / n) * (180 / math.pi)

# 사용 예시
n = angle_to_cases(10)  # 10도 간격에 필요한 케이스 수
print(f"10° 간격: {n}개 필요")
print(f"413개의 평균 간격: {cases_to_angle(413):.2f}°")
```

---

## References

1. Fibonacci Lattice: Álvaro González, "Measurement of Areas on a Sphere Using Fibonacci and Latitude-Longitude Lattices", Mathematical Geosciences, 2010
2. Golden Angle: [Wikipedia - Golden Angle](https://en.wikipedia.org/wiki/Golden_angle)
3. Mollweide Projection: [Wikipedia - Mollweide Projection](https://en.wikipedia.org/wiki/Mollweide_projection)

---

## Author

- Creator: koo.park
- Email: koo.park@samsung.com
- Group: CAE
