from flask import Flask, request, jsonify
import os
import torch
from ultralytics import YOLO
import math
import time, heapq

class PIDController:
    def __init__(self, Kp, Ki, Kd, output_limits=(-1.0, 1.0)):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.output_limits = output_limits
        self.integral = 0.0
        self.previous_error = 0.0
        self.last_time = None

    def update(self, error, current_time):
        if self.last_time is None:
            self.last_time = current_time
            return 0.0

        dt = current_time - self.last_time
        if dt <= 0:
            return 0.0

        # Proportional term
        P = self.Kp * error

        # Integral term
        self.integral += error * dt
        I = self.Ki * self.integral

        # Derivative term
        derivative = (error - self.previous_error) / dt
        D = self.Kd * derivative

        # Compute output
        output = P + I + D

        # Limit output
        output = max(min(output, self.output_limits[1]), self.output_limits[0])

        # Update state
        self.previous_error = error
        self.last_time = current_time

        return output

app = Flask(__name__)
model = YOLO('yolov8n.pt')

# Global state
destination = None  # (x, y, z)
current_position = None  # (x, z)
current_heading = 0.0  # degrees, from /info playerBodyX
last_info_time = time.time()

obstacles = []  # 장애물 리스트

# PID controller for steering
pid = PIDController(Kp=0.4, Ki=0.001, Kd=0.15, output_limits=(-1.0, 1.0))

# Move commands (simplified for navigation)
move_command = [
    {"move": "W", "weight": 1.0},  # Full speed forward
    {"move": "A", "weight": 1.0},  # Full left turn
    {"move": "D", "weight": 1.0},  # Full right turn
    {"move": "STOP", "weight": 1.0}  # Stop
]

# Existing action commands (unchanged)
action_command = [
    {"turret": "Q", "weight": 1.0},
    {"turret": "Q", "weight": 0.8},
    {"turret": "Q", "weight": 0.6},
    {"turret": "Q", "weight": 0.4},
    {"turret": "E", "weight": 1.0},
    {"turret": "E", "weight": 1.0},
    {"turret": "E", "weight": 1.0},
    {"turret": "E", "weight": 1.0},
    {"turret": "F", "weight": 0.5},
    {"turret": "F", "weight": 0.3},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 0.7},
    {"turret": "R", "weight": 0.4},
    {"turret": "R", "weight": 0.2},
    {"turret": "FIRE"}
]

def pure_pursuit(current_position, current_heading, waypoints, lookahead_distance=5.0):
    target_wp = None
    min_distance = float('inf')

    for wp in waypoints:
        dist = math.sqrt((wp[0] - current_position[0])**2 + (wp[1] - current_position[1])**2)
        if dist < lookahead_distance and dist < min_distance:
            min_distance = dist
            target_wp = wp

    if not target_wp:
        return None  # 더 이상 목표가 없음

    dx = target_wp[0] - current_position[0]
    dz = target_wp[1] - current_position[1]
    desired_heading = math.degrees(math.atan2(dx, dz))

    heading_error = desired_heading - current_heading
    heading_error = ((heading_error + 180) % 360) - 180

    return heading_error, target_wp

@app.route('/set_destination', methods=['POST'])
def set_destination():
    global destination
    data = request.get_json()
    if not data or "destination" not in data:
        return jsonify({"status": "ERROR", "message": "Missing destination data"}), 400

    try:
        x, y, z = map(float, data["destination"].split(","))
        destination = (x, z)  # Store x, z for 2D navigation
        print(f"🎯 Destination set to: x={x}, z={z}")
        return jsonify({"status": "OK", "destination": {"x": x, "y": y, "z": z}})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": f"Invalid format: {str(e)}"}), 400

@app.route('/info', methods=['POST'])
def info():
    global current_position, current_heading, last_info_time
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    # print("📨 /info data received:", data)
    last_info_time = time.time()

    # Update position and heading
    player_pos = data.get("playerPos", {})
    current_position = (player_pos.get("x", 0), player_pos.get("z", 0))
    current_heading = data.get("playerBodyX", 0)  # degrees

    return jsonify({"status": "success", "control": ""})

@app.route('/update_position', methods=['POST'])
def update_position():
    global current_position
    data = request.get_json()
    if not data or "position" not in data:
        return jsonify({"status": "ERROR", "message": "Missing position data"}), 400

    try:
        x, y, z = map(float, data["position"].split(","))
        current_position = (x, z)
        print(f"📍 Position updated: {current_position}")
        return jsonify({"status": "OK", "current_position": current_position})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 400

def is_obstacle(x, z, obstacles):
    """ 장애물 여부 확인 """
    for obs in obstacles:
        if obs[0] <= x <= obs[1] and obs[2] <= z <= obs[3]:
            return True
    return False

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(start, goal, obstacles):
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for dx, dz in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            neighbor = (current[0] + dx, current[1] + dz)
            if is_obstacle(neighbor[0], neighbor[1], obstacles):
                continue  # 장애물 회피

            tentative_g_score = g_score[current] + 1
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None  # 경로를 찾지 못함

@app.route('/get_move', methods=['GET'])
def get_move():
    global destination, current_position, current_heading, last_info_time, obstacles
    current_time = time.time()
    waypoints = a_star(current_position, destination, obstacles)
    print(f"🔍 A* 알고리즘 결과: {waypoints}")
    if not destination or not current_position:
        print("🚗 No destination or position, stopping")
        return jsonify({"move": "STOP", "weight": 1.0})

    # Calculate distance to destination
    dx = destination[0] - current_position[0]
    dz = destination[1] - current_position[1]
    distance = math.sqrt(dx**2 + dz**2)

    # Speed control
    if distance <= 10.0:
        print("🚗 Reached destination, stopping")
        return jsonify({"move": "STOP"})
    elif distance <= 30.0:
        # Linearly reduce speed from 1.0 to 0.0 between 4m and 0.5m
        weight = (distance - 0.5) / (4.0 - 0.5)
        move = "W"
    else:
        weight = 1.0
        move = "W"

    # Steering control with PID
    # Calculate desired heading (angle to destination)
    desired_heading = math.degrees(math.atan2(dx, dz))  # atan2 returns angle in degrees
    heading_error = desired_heading - current_heading

    # Normalize heading error to [-180, 180]
    heading_error = ((heading_error + 180) % 360) - 180

    # Update PID
    steering_output = pid.update(heading_error, current_time)

    # Determine steering command
    if abs(heading_error) > 5:  # Only steer if error is significant
        if steering_output > 0:
            steering_move = "D"  # Right turn
            steering_weight = min(abs(steering_output), 0.5)
        else:
            steering_move = "A"  # Left turn
            steering_weight = min(abs(steering_output), 0.5)
        
        print(f"🚗 Steering: {steering_move}, weight={steering_weight:.2f}, heading_error={heading_error:.2f}")
        return jsonify({"move": steering_move, "weight": steering_weight})
    else:
        print(f"🚗 Moving forward: {move}, weight={weight:.2f}, distance={distance:.2f}")
        return jsonify({"move": move, "weight": weight})

# Other endpoints remain unchanged
@app.route('/detect', methods=['POST'])
def detect():
    image = request.files.get('image')
    if not image:
        return jsonify({"error": "No image received"}), 400

    image_path = 'temp_image.jpg'
    image.save(image_path)

    results = model(image_path)
    detections = results[0].boxes.data.cpu().numpy()

    target_classes = {0: "person", 2: "car", 7: "truck", 15: "rock"}
    filtered_results = []
    for box in detections:
        class_id = int(box[5])
        if class_id in target_classes:
            filtered_results.append({
                'className': target_classes[class_id],
                'bbox': [float(coord) for coord in box[:4]],
                'confidence': float(box[4])
            })

    return jsonify(filtered_results)

@app.route('/get_action', methods=['GET'])
def get_action():
    global action_command
    if action_command:
        command = action_command.pop(0)
       # print(f"🔫 Action Command: {command}")
        return jsonify(command)
    else:
        return jsonify({"turret": "", "weight": 0.0})

@app.route('/update_bullet', methods=['POST'])
def update_bullet():
    data = request.get_json()
    if not data:
        return jsonify({"status": "ERROR", "message": "Invalid request data"}), 400

   # print(f"💥 Bullet Impact at X={data.get('x')}, Y={data.get('y')}, Z={data.get('z')}, Target={data.get('hit')}")
    return jsonify({"status": "OK", "message": "Bullet impact data received"})

@app.route('/update_obstacle', methods=['POST'])
def update_obstacle():
    global obstacles
    data = request.get_json()
    if not data or "obstacles" not in data:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400

    obstacles = [(obs["x_min"], obs["x_max"], obs["z_min"], obs["z_max"]) for obs in data["obstacles"]]
    print(f"🪨 장애물 정보 업데이트됨: {obstacles}")

    return jsonify({'status': 'success', 'message': 'Obstacle data received'})

@app.route('/init', methods=['GET'])
def init():
    config = {
        "startMode": "start",
        "blStartX": 60,
        "blStartY": 10,
        "blStartZ": 27.23,
        "rdStartX": 59,
        "rdStartY": 10,
        "rdStartZ": 280
    }
   # print("🛠️ Initialization config sent via /init:", config)
    return jsonify(config)

@app.route('/start', methods=['GET'])
def start():
    # print("🚀 /start command received")
    return jsonify({"control": ""})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)