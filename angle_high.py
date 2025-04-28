# -*- encoding: utf-8 -*-
import math

def calculate_angle(d, delta_h, v=63.89, g=9.8):
    """물리학적 공식으로 포신 각도 계산"""
    a = (g * d**2) / (2 * v**2)
    b = -d
    c = delta_h + (g * d**2) / (2 * v**2)
    
    discriminant = b**2 - 4 * a * c
    if discriminant < 0:
        return None  # 도달 불가능
    
    tan_theta1 = (-b + math.sqrt(discriminant)) / (2 * a)
    tan_theta2 = (-b - math.sqrt(discriminant)) / (2 * a)
    
    theta1 = math.degrees(math.atan(tan_theta1))
    theta2 = math.degrees(math.atan(tan_theta2))
    
    # 물리적으로 타당한 각도 선택 (0~90도)
    valid_angles = [theta for theta in [theta1, theta2] if 0 <= theta <= 90]
    return min(valid_angles, default=None) if valid_angles else None

def calculate_angle_empirical(d, delta_h):
    """경험적 방정식으로 기본 각도 계산 + 높이 보정"""
    a = 0.373
    b = 5.914
    c = 41.24 - d
    
    discriminant = b**2 - 4 * a * c
    if discriminant < 0:
        return None  # 도달 불가능
    
    x1 = (-b + math.sqrt(discriminant)) / (2 * a)
    x2 = (-b - math.sqrt(discriminant)) / (2 * a)
    
    valid_angles = [x for x in [x1, x2] if 0 <= x <= 90]
    x0 = min(valid_angles, default=None) if valid_angles else None
    
    if x0 is None:
        return None
    
    # 높이 보정 (근사)
    correction = math.degrees(math.atan(delta_h / d)) if d != 0 else 0
    theta = x0 + correction
    return theta if 0 <= theta <= 90 else None

# 테스트
test_cases = [
    {"d": 50, "delta_h": 10},  # h1: 나보다 10m 높음
    {"d": 50, "delta_h": 0},   # h0: 동일 높이
    {"d": 50, "delta_h": -10}, # h2: 나보다 10m 낮음
]

for case in test_cases:
    d, delta_h = case["d"], case["delta_h"]
    angle_phys = calculate_angle(d, delta_h)
    angle_emp = calculate_angle_empirical(d, delta_h)
    print(f"거리: {d}m, 높이 차이: {delta_h}m")
    print(f"  물리학적 각도: {angle_phys:.2f}도" if angle_phys else "  도달 불가능")
    print(f"  경험적 각도: {angle_emp:.2f}도" if angle_emp else "  도달 불가능")