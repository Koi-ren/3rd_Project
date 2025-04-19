from flask import Flask, request, jsonify
import os
import torch
from ultralytics import YOLO
import math
import time
import heapq
import numpy as np
import json

app = Flask(__name__)
model = YOLO('yolov8n.pt')

class PIDController:
    def __init__(self, Kp=0.3, Ki=0.1, Kd=10.0, output_limits=(-1.0, 1.0), integral_limit=10.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.output_limits = output_limits
        self.integral_limit = integral_limit
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_heading = None
        self.last_time = None

    def update(self, error, current_time):
        if self.last_time is None:
            self.last_time = current_time
            return 0.0
        dt = current_time - self.last_time
        dt = max(dt, 0.01)
        error = max(min(error, 45.0), -45.0)  # heading error 제한 확대
        P = self.Kp * error
        self.integral += error * dt
        self.integral = max(min(self.integral, self.integral_limit), -self.integral_limit)
        I = self.Ki * self.integral
        D = self.Kd * (error - self.previous_error) / dt if self.previous_error is not None else 0.0
        output = P + I + D
        output = max(min(output, self.output_limits[1]), self.output_limits[0])
        self.previous_error = error
        self.last_time = current_time
        return output

# Global state
destination = None
current_position = None
current_heading = 0.0
last_info_time = time.time()
waypoints = []
current_waypoint_idx = 0
obstacles = {(70, 30), (80, 40)}
last_steering_move = None
last_waypoint_change_time = time.time()

# PIDController 초기화: 정적 게인 값 설정
pid = PIDController(Kp=0.3, Ki=0.1, Kd=10.0, output_limits=(-1.0, 1.0), integral_limit=10.0)

move_command = [
    {"move": "W", "weight": 1.0},
    {"move": "A", "weight": 1.0},
    {"move": "D", "weight": 1.0},
    {"move": "STOP", "weight": 1.0}
]

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

def a_star(start, goal, grid_size=300, cell_size=10):
    grid = np.zeros((grid_size, grid_size), dtype=np.uint8)
    for ox, oz in obstacles:
        grid_x = min(int(ox / cell_size), grid_size - 1)
        grid_z = min(int(oz / cell_size), grid_size - 1)
        grid[grid_x, grid_z] = 1
    start = (min(int(start[0] / cell_size), grid_size - 1), min(int(start[1] / cell_size), grid_size - 1))
    goal = (min(int(goal[0] / cell_size), grid_size - 1), min(int(goal[1] / cell_size), grid_size - 1))
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: math.sqrt((start[0] - goal[0])**2 + (start[1] - goal[1])**2)}
    while open_set:
        current_f, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append((current[0] * cell_size, current[1] * cell_size))
                current = came_from[current]
            path.append((start[0] * cell_size, start[1] * cell_size))
            return path[::-1]
        for dx, dz in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            neighbor = (current[0] + dx, current[1] + dz)
            if 0 <= neighbor[0] < grid_size and 0 <= neighbor[1] < grid_size and grid[neighbor[0], grid_z] == 0:
                tentative_g = g_score[current] + (math.sqrt(dx**2 + dz**2) * cell_size)
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + math.sqrt((neighbor[0] - goal[0])**2 + (neighbor[1] - goal[0])**2)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []

def pure_pursuit(current_pos, current_heading, waypoints, waypoint_idx, lookahead_distance=15.0):  # lookahead 조정
    global last_waypoint_change_time
    if not waypoints:
        return None, waypoint_idx, 1.0
    target_waypoint = waypoints[waypoint_idx]
    dist = math.sqrt((target_waypoint[0] - current_pos[0])**2 + (target_waypoint[1] - current_pos[1])**2)
    dynamic_lookahead = max(15.0, min(dist * 0.2, 20.0))  # lookahead 범위 축소
    if dist < dynamic_lookahead * 0.5:
        waypoint_idx = (waypoint_idx + 1) % len(waypoints)
        last_waypoint_change_time = time.time()
        target_waypoint = waypoints[waypoint_idx]
        dist = math.sqrt((target_waypoint[0] - current_pos[0])**2 + (target_waypoint[1] - current_pos[1])**2)
        print(f"🛤️ Waypoint transitioned to idx={waypoint_idx}, target={target_waypoint}")
    dx = target_waypoint[0] - current_pos[0]
    dz = target_waypoint[1] - current_pos[1]
    if not hasattr(pure_pursuit, 'last_dz'):
        pure_pursuit.last_dz = dz
    dz = 0.5 * pure_pursuit.last_dz + 0.5 * dz
    pure_pursuit.last_dz = dz
    z_weight = 1.2 if abs(dz) > abs(dx) else 1.0
    desired_heading = math.degrees(math.atan2(dx, dz * z_weight)) % 360
    heading_error = desired_heading - current_heading
    heading_error = ((heading_error + 180) % 360) - 180
    abs_heading_error = abs(heading_error)
    weight = max(0.8, 1.0 - (abs_heading_error / 90.0))
    print(f"🧭 Pure Pursuit: dx={dx:.2f}, dz={dz:.2f}, desired_heading={desired_heading:.2f}, "
          f"current_heading={current_heading:.2f}, heading_error={heading_error:.2f}, "
          f"target_waypoint={target_waypoint}, dist={dist:.2f}, dynamic_lookahead={dynamic_lookahead:.2f}, "
          f"waypoint_idx={waypoint_idx}")
    return heading_error, waypoint_idx, weight

@app.route('/set_destination', methods=['POST'])
def set_destination():
    global destination, waypoints, current_waypoint_idx
    data = request.get_json()
    if not data or "destination" not in data:
        return jsonify({"status": "ERROR", "message": "Missing destination data"}), 400
    try:
        x, y, z = map(float, data["destination"].split(","))
        destination = (x, z)
        print(f"🎯 Destination set to: x={x}, z={z}")
        if current_position:
            waypoints = a_star(current_position, destination)
            current_waypoint_idx = 0
            print(f"🛤️ Waypoints generated: {len(waypoints)} points")
        return jsonify({"status": "OK", "destination": {"x": x, "y": y, "z": z}})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": f"Invalid format: {str(e)}"}), 400

@app.route('/info', methods=['POST'])
def info():
    global current_position, current_heading, last_info_time, waypoints, current_waypoint_idx
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON received"}), 400
    last_info_time = time.time()
    player_pos = data.get("playerPos", {})
    current_position = (player_pos.get("x", 0), player_pos.get("z", 0))
    current_heading = data.get("playerBodyX", 0) % 360
    if not hasattr(info, 'last_recovery_time'):
        info.last_recovery_time = 0
    if (not waypoints or
        (abs(current_position[0] - 150) > 150 or abs(current_position[1] - 150) > 150) and
        time.time() - info.last_recovery_time > 10.0):
        recovery_target = (150, 150)
        waypoints = a_star(current_position, recovery_target)
        current_waypoint_idx = 0
        info.last_recovery_time = time.time()
        print(f"🛑 Off-track at {current_position}, recovering to {recovery_target}")
    print(f"📡 /info: position={current_position}, heading={current_heading}")
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

@app.route('/get_move', methods=['GET'])
def get_move():
    global destination, current_position, current_heading, last_info_time
    global waypoints, current_waypoint_idx, last_steering_move
    current_time = time.time()
    if not current_position:
        print("🚗 No position, stopping")
        return jsonify({"move": "STOP", "weight": 1.0})
    if not waypoints:
        print("🚗 No waypoints, setting infinity loop")
        waypoints = [
            (100, 150), (85, 175), (100, 200), (150, 150),
            (200, 150), (215, 175), (200, 200), (150, 150),
            (100, 150), (150, 150)
        ]
        current_waypoint_idx = 0
        print(f"🛤️ Infinity loop waypoints set: {len(waypoints)} points")
    if current_time - last_info_time > 0.5:
        print("🚫 No recent /info update, stopping")
        return jsonify({"move": "STOP", "weight": 1.0})
    heading_error, current_waypoint_idx, pursuit_weight = pure_pursuit(
        current_position, current_heading, waypoints, current_waypoint_idx
    )
    if heading_error is None:
        print("🚗 No valid waypoint, stopping")
        return jsonify({"move": "STOP", "weight": 1.0})
    weight = max(0.8, pursuit_weight)
    move = "W"
    target_waypoint = waypoints[current_waypoint_idx]
    if abs(heading_error) > 10:
        steering_output = pid.update(heading_error, current_time)
        if steering_output > 0:
            steering_move = "D"
            steering_weight = min(abs(steering_output) * weight * 0.8, 1.0)
        else:
            steering_move = "A"
            steering_weight = min(abs(steering_output) * weight * 0.8, 1.0)
        last_steering_move = steering_move
        dt = current_time - pid.last_time if pid.last_time else 0.01
        heading_change = current_heading - (pid.previous_heading or current_heading)
        heading_change = max(min(heading_change, 10.0), -10.0)
        print(f"🚗 {steering_move} applied, heading_change={heading_change:.2f}/s, dt={dt:.3f}")
        print(f"🚗 Steering: {steering_move}, weight={steering_weight:.2f}, "
              f"heading_error={heading_error:.2f}, waypoint_idx={current_waypoint_idx}, "
              f"pursuit_weight={pursuit_weight:.2f}")
        print(f"📈 PID: P={pid.Kp * heading_error:.2f}, I={pid.Ki * pid.integral:.2f}, "
              f"D={(pid.Kd * (heading_error - pid.previous_error) / dt if dt > 0 else 0):.2f}")
        pid.previous_heading = current_heading
        return jsonify({"move": steering_move, "weight": steering_weight})
    else:
        last_steering_move = move
        expected_x = current_position[0] + math.sin(math.radians(current_heading)) * 0.1
        expected_z = current_position[1] + math.cos(math.radians(current_heading)) * 0.1
        print(f"🚗 Moving forward: {move}, weight={weight:.2f}, "
              f"waypoint_idx={current_waypoint_idx}, pursuit_weight={pursuit_weight:.2f}, "
              f"expected_x={expected_x:.4f}, expected_z={expected_z:.4f}, "
              f"dx={target_waypoint[0] - current_position[0]:.2f}, "
              f"dz={target_waypoint[1] - current_position[1]:.2f}")
        return jsonify({"move": move, "weight": weight})

@app.route('/update_obstacle', methods=['POST'])
def update_obstacle():
    global obstacles, waypoints, current_waypoint_idx
    data = request.get_json()
    if not data:
        print("⚠️ No obstacle data received")
        return jsonify({'status': 'error', 'message': 'No data received'}), 400
    new_obstacles = set()
    try:
        if isinstance(data, str):
            data = json.loads(data)
        for obstacle in data:
            x = float(obstacle.get("x", 0))
            z = float(obstacle.get("z", 0))
            new_obstacles.add((int(x), int(z)))
        obstacles = new_obstacles
        print(f"🪨 Obstacles updated: {len(obstacles)} obstacles")
        if waypoints and current_position:
            waypoints = a_star(current_position, waypoints[current_waypoint_idx])
            print(f"🛤️ Waypoints updated after obstacle change: {len(waypoints)} points")
    except Exception as e:
        print(f"⚠️ Error processing obstacles: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Invalid format: {str(e)}'}), 400
    return jsonify({'status': 'success', 'message': 'Obstacle data received'})

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
        return jsonify(command)
    else:
        return jsonify({"turret": "", "weight": 0.0})

@app.route('/update_bullet', methods=['POST'])
def update_bullet():
    data = request.get_json()
    if not data:
        return jsonify({"status": "ERROR", "message": "Invalid request data"}), 400
    return jsonify({"status": "OK", "message": "Bullet impact data received"})

@app.route('/init', methods=['GET'])
def init():
    global waypoints, current_waypoint_idx, destination, current_position, current_heading
    destination = None
    current_position = (150, 150)
    current_heading = 0.0
    waypoints = [
        (100, 150), (85, 175), (100, 200), (150, 150),
        (200, 150), (215, 175), (200, 200), (150, 150),
        (100, 150), (150, 150)
    ]
    current_waypoint_idx = 0
    print(f"🎯 Initialized with infinity loop at position={current_position}")
    print(f"🛤️ Waypoints initialized: {len(waypoints)} points")
    return jsonify({
        "startMode": "start",
        "blStartX": 150,
        "blStartY": 10,
        "blStartZ": 150,
        "rdStartX": 59,
        "rdStartY": 10,
        "rdStartZ": 280
    })

@app.route('/start', methods=['GET'])
def start():
    return jsonify({"control": ""})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)