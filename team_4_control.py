# 10000자 넘으면 글자색 안뜬다함
from flask import Flask, request, jsonify
import math
import random
import time
import numpy as np
from collections import deque

app = Flask(__name__)

# 전역 변수
current_position = None  # (x, z)
current_heading = 0.0  # 추정된 현재 방향 (라디안)
destination = None  # (x, z)
last_command = None  # 마지막 이동 명령 추적
last_steering = 0.0  # 이전 조향 값 저장
last_update_time = time.time()  # 마지막 업데이트 시간
path_history = deque(maxlen=20)  # 이동 경로 히스토리 (최근 20개 위치)
obstacles = []  # 장애물 위치 목록 [(x, z, radius), ...]

# 파라미터
MOVE_STEP = 0.1  # 기본 이동 단위
TOLERANCE = 5.0  # 목적지 허용 오차
LOOKAHEAD_MIN = 1.0  # 최소 전방 주시 거리
LOOKAHEAD_MAX = 10.0  # 최대 전방 주시 거리
HEADING_SMOOTHING = 0.8  # 헤딩 평활화 계수 (0-1)
STEERING_SMOOTHING = 0.7  # 조향 평활화 계수 (0-1)
OBSTACLE_AVOIDANCE_WEIGHT = 1.5  # 장애물 회피 가중치
GOAL_WEIGHT = 2.0  # 목표 방향 가중치

# 초기값
initial_distance = None  # 초기 유클리드 거리

# 가중치
WEIGHT_FACTORS = {
    "D": 0.5,  # 오른쪽 조향 가중치
    "A": 0.5,  # 왼쪽 조향 가중치
    "W": 1.0,  # 직진 가중치
    "S": 1.5   # 후진 가중치
}

# 속도 제어 파라미터
MAX_SPEED = 1.0
MIN_SPEED = 0.1
SPEED_FACTOR = 0.8  # 속도 조절 계수

@app.route('/update_position', methods=['POST'])
def update_position():
    global current_position, current_heading, last_update_time, path_history
    data = request.get_json()
    if not data or "position" not in data:
        return jsonify({"status": "ERROR", "message": "위치 데이터 누락"}), 400

    try:
        # 시간 델타 계산 (속도 추정용)
        now = time.time()
        dt = now - last_update_time
        last_update_time = now
        
        # 새 위치 업데이트
        x, y, z = map(float, data["position"].split(","))
        new_position = (x, z)
        
        # 위치가 있으면 방향 업데이트
        if current_position:
            prev_x, prev_z = current_position
            dx = x - prev_x
            dz = z - prev_z
            
            # 유의미한 이동이 있을 때만 방향 업데이트
            distance_moved = math.sqrt(dx**2 + dz**2)
            if distance_moved > 0.01:  # 최소 이동 거리 임계값
                new_heading = math.atan2(dx, dz)
                # 평활화를 통한 방향 필터링
                current_heading = HEADING_SMOOTHING * current_heading + (1 - HEADING_SMOOTHING) * new_heading
                current_heading = math.atan2(math.sin(current_heading), math.cos(current_heading))  # 정규화
        
        current_position = new_position
        path_history.append(current_position)  # 경로 히스토리 추가
        
        print(f"📍 위치 업데이트: {current_position}, 방향: {math.degrees(current_heading):.2f}°")
        return jsonify({
            "status": "OK", 
            "current_position": current_position,
            "heading": math.degrees(current_heading)
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@app.route('/set_destination', methods=['POST'])
def set_destination():
    global destination, initial_distance, path_history
    data = request.get_json()
    if not data or "destination" not in data:
        return jsonify({"status": "ERROR", "message": "목적지 데이터 누락"}), 400

    try:
        x, y, z = map(float, data["destination"].split(","))
        destination = (x, z)
        
        if current_position:
            curr_x, curr_z = current_position
            initial_distance = math.sqrt((x - curr_x) ** 2 + (z - curr_z) ** 2)
            print(f"📏 초기 거리 설정: {initial_distance:.2f}")
        
        # 새 목적지 설정 시 경로 히스토리 초기화
        path_history.clear()
        path_history.append(current_position)
        
        print(f"🎯 목적지 설정: {destination}")
        return jsonify({
            "status": "OK", 
            "destination": {"x": x, "y": y, "z": z},
            "initial_distance": initial_distance
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "message": f"형식 오류: {str(e)}"}), 400

@app.route('/set_weights', methods=['POST'])
def set_weights():
    global WEIGHT_FACTORS
    data = request.get_json()
    if not data:
        return jsonify({"status": "ERROR", "message": "가중치 데이터 누락"}), 400

    try:
        for cmd in ['D', 'A', 'W', 'S']:
            if cmd in data:
                WEIGHT_FACTORS[cmd] = float(data[cmd])
        print(f"⚖️ 가중치 업데이트: {WEIGHT_FACTORS}")
        return jsonify({"status": "OK", "weights": WEIGHT_FACTORS})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@app.route('/add_obstacle', methods=['POST'])
def add_obstacle():
    global obstacles
    data = request.get_json()
    if not data or "position" not in data or "radius" not in data:
        return jsonify({"status": "ERROR", "message": "장애물 데이터 누락"}), 400

    try:
        x, y, z = map(float, data["position"].split(","))
        radius = float(data["radius"])
        obstacles.append((x, z, radius))
        print(f"🚧 장애물 추가: 위치({x}, {z}), 반경: {radius}")
        return jsonify({"status": "OK", "obstacles": len(obstacles)})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@app.route('/clear_obstacles', methods=['GET'])
def clear_obstacles():
    global obstacles
    obstacles = []
    print("🧹 장애물 목록 초기화")
    return jsonify({"status": "OK", "obstacles": 0})

@app.route('/get_move', methods=['GET'])
def get_move():
    global current_position, destination, last_command, initial_distance, last_steering
    if current_position is None or destination is None:
        return jsonify({"move": "STOP", "weight": 1.0})

    # 현재 위치와 목표 위치
    curr_x, curr_z = current_position
    dest_x, dest_z = destination

    # 유클리드 거리 계산
    distance = math.sqrt((dest_x - curr_x) ** 2 + (dest_z - curr_z) ** 2)
    print(f"📏 목적지까지 거리: {distance:.2f}")

    # 목표 도달 여부
    if distance < TOLERANCE:
        print("✅ 목적지 도달")
        initial_distance = None
        return jsonify({"move": "STOP", "weight": 1.0})

    # 개선된 Pure Pursuit 알고리즘
    # 동적 전방 주시 거리 계산
    # 거리가 멀면 더 멀리 보고, 가까우면 더 가까이 봄
    lookahead_distance = min(
        LOOKAHEAD_MAX,
        max(LOOKAHEAD_MIN, distance * 0.5)  # 거리의 50%를 전방주시거리로 사용
    )
    
    # 목표 방향 벡터
    goal_vector = np.array([dest_x - curr_x, dest_z - curr_z])
    goal_distance = np.linalg.norm(goal_vector)
    
    if goal_distance > 0:
        goal_vector = goal_vector / goal_distance  # 정규화
    
    # 장애물 회피 벡터 계산
    avoidance_vector = np.array([0.0, 0.0])
    if obstacles:
        for obs_x, obs_z, obs_radius in obstacles:
            # 장애물까지의 벡터
            to_obstacle = np.array([obs_x - curr_x, obs_z - curr_z])
            distance_to_obs = np.linalg.norm(to_obstacle)
            
            # 장애물 영향 범위 내에 있는 경우
            if distance_to_obs < obs_radius + lookahead_distance:
                # 장애물에서 멀어지는 방향으로 힘 적용
                if distance_to_obs > 0:
                    repulsion = -to_obstacle / distance_to_obs
                    # 장애물에 가까울수록 더 강한 회피력
                    strength = 1.0 - min(1.0, (distance_to_obs - obs_radius) / lookahead_distance)
                    avoidance_vector += repulsion * strength * OBSTACLE_AVOIDANCE_WEIGHT
    
    # 최종 목표 방향 계산 (장애물 회피 포함)
    target_vector = goal_vector * GOAL_WEIGHT + avoidance_vector
    target_vector_norm = np.linalg.norm(target_vector)
    
    if target_vector_norm > 0:
        target_vector = target_vector / target_vector_norm  # 정규화
        target_heading = math.atan2(target_vector[0], target_vector[1])
    else:
        target_heading = math.atan2(goal_vector[0], goal_vector[1])
    
    # 전방 주시점 계산
    lookahead_x = curr_x + target_vector[0] * lookahead_distance
    lookahead_z = curr_z + target_vector[1] * lookahead_distance
    
    print(f"👀 전방 주시점: ({lookahead_x:.2f}, {lookahead_z:.2f}), 거리: {lookahead_distance:.2f}")
    
    # 조향 각도 계산
    dx = lookahead_x - curr_x
    dz = lookahead_z - curr_z
    
    # 움직임 방향으로 목표 헤딩 계산
    target_heading = math.atan2(dx, dz)
    
    # 현재 방향과 목표 방향의 차이 계산
    heading_error = target_heading - current_heading
    heading_error = math.atan2(math.sin(heading_error), math.cos(heading_error))  # -π ~ π 정규화
    
    # Pure Pursuit 곡률 계산
    curvature = 2.0 * math.sin(heading_error) / max(lookahead_distance, 0.01)
    
    # 조향값 평활화
    steering = STEERING_SMOOTHING * last_steering + (1 - STEERING_SMOOTHING) * curvature
    last_steering = steering
    
    print(f"📐 헤딩 오차: {math.degrees(heading_error):.2f}°, 조향: {steering:.4f}")
    
    # 속도 제어 (조향값에 따른 속도 조절)
    abs_steering = abs(steering)
    speed = MAX_SPEED - abs_steering * SPEED_FACTOR  # 코너에서 감속
    speed = max(MIN_SPEED, min(MAX_SPEED, speed))
    
    # 진행률 계산
    if initial_distance and distance > 0:
        progress = max(0, 1 - distance / initial_distance)
    else:
        progress = 0.0
    
    # 동적 가중치 계산 - 거리와 진행률 기반
    dynamic_weights = {
        # 조향값이 클수록 더 민감하게 반응
        "D": WEIGHT_FACTORS["D"] * (1 + abs_steering * 2) if steering > 0 else 0.0,
        "A": WEIGHT_FACTORS["A"] * (1 + abs_steering * 2) if steering < 0 else 0.0,
        # 전진 속도는 속도 제어에 따라 조절
        "W": WEIGHT_FACTORS["W"] * speed,
        # 후진은 필요시에만 (일반적으로 사용하지 않음)
        "S": WEIGHT_FACTORS["S"] if heading_error > math.pi * 0.6 else 0.0
    }
    
    # 가중치에 진행률 보너스 추가 (목적지에 가까워질수록 정밀 제어)
    for cmd in dynamic_weights:
        if dynamic_weights[cmd] > 0:
            dynamic_weights[cmd] *= (1 + progress * 0.5)
    
    print(f"⚖️ 동적 가중치: {dynamic_weights}")
    
    # 가중치 기반 명령 선택
    commands = [cmd for cmd, w in dynamic_weights.items() if w > 0]
    if not commands:
        command = {"move": "STOP", "weight": 1.0}
    else:
        # 가중치 비율에 따른 확률적 선택
        weights = [dynamic_weights[cmd] for cmd in commands]
        chosen_cmd = random.choices(commands, weights=weights, k=1)[0]
        command = {"move": chosen_cmd, "weight": dynamic_weights[chosen_cmd]}
        last_command = chosen_cmd
    
    print(f"🚗 이동 명령: {command}, 속도: {speed:.2f}")

    # 서버 측 위치 조정
    if last_command:
        move_distance = MOVE_STEP * speed  # 속도에 따른 이동 거리 조절
        new_x, new_z = curr_x, curr_z
        
        if last_command == "D":
            # 현재 방향 기준으로 오른쪽으로 이동
            new_x += move_distance * math.cos(current_heading + math.pi/2)
            new_z += move_distance * math.sin(current_heading + math.pi/2)
        elif last_command == "A":
            # 현재 방향 기준으로 왼쪽으로 이동
            new_x += move_distance * math.cos(current_heading - math.pi/2)
            new_z += move_distance * math.sin(current_heading - math.pi/2)
        elif last_command == "W":
            # 현재 방향으로 전진
            new_x += move_distance * math.sin(current_heading)
            new_z += move_distance * math.cos(current_heading)
        elif last_command == "S":
            # 현재 방향의 반대로 후진
            new_x -= move_distance * math.sin(current_heading)
            new_z -= move_distance * math.cos(current_heading)
        
        current_position = (new_x, new_z)
        print(f"🛠️ 서버 측 위치 조정: {current_position}")

    return jsonify(command)

@app.route('/get_path', methods=['GET'])
def get_path():
    """현재까지의 경로 히스토리 반환"""
    path_points = list(path_history)
    return jsonify({
        "status": "OK", 
        "path": path_points,
        "count": len(path_points)
    })

@app.route('/get_status', methods=['GET'])
def get_status():
    """현재 상태 정보 반환"""
    status = {
        "current_position": current_position,
        "destination": destination,
        "heading": math.degrees(current_heading) if current_heading is not None else None,
        "distance": None,
        "progress": None,
        "obstacles": len(obstacles)
    }
    
    if current_position and destination:
        curr_x, curr_z = current_position
        dest_x, dest_z = destination
        distance = math.sqrt((dest_x - curr_x) ** 2 + (dest_z - curr_z) ** 2)
        status["distance"] = distance
        
        if initial_distance:
            status["progress"] = max(0, 1 - distance / initial_distance)
    
    return jsonify(status)

@app.route('/init', methods=['GET'])
def init():
    global current_position, destination, last_command, initial_distance, current_heading
    global path_history, obstacles, last_steering
    
    current_position = None
    destination = None
    last_command = None
    initial_distance = None
    current_heading = 0.0
    last_steering = 0.0
    path_history.clear()
    obstacles = []
    
    config = {
        "startMode": "start",
        "blStartX": 60,
        "blStartY": 10,
        "blStartZ": 27.23,
        "rdStartX": 59,
        "rdStartY": 10,
        "rdStartZ": 280
    }
    print("🛠️ 초기화 설정 전송 (/init):", config)
    return jsonify(config)

@app.route('/start', methods=['GET'])
def start():
    print("🚀 /start 명령 수신")
    return jsonify({"control": ""})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)