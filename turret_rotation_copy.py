from flask import Flask, request, jsonify
import os
import torch
from ultralytics import YOLO
from datetime import datetime

app = Flask(__name__)
model = YOLO('yolov8n.pt')
global current_time
# 전역 변수로 투발 시간과 탄착 시간 저장
fire_times = []  # 투발 시간 리스트
impact_times = []  # 탄착 시간 리스트
fire_positions = []  # 투발 위치 리스트
impact_positions = []  # 탄착 위치 리스트
action_command = [
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "FIRE"},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "FIRE"},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "R", "weight": 1.0},
    {"turret": "FIRE"}
]

@app.route('/get_action', methods=['GET'])
def get_action():
    global action_command, fire_times, fire_positions, current_time
    if action_command:
        command = action_command.pop(0)
        print(f"🔫 Action Command: {command}")
        # 발사 명령일 경우 시간과 위치 기록
        if command.get("turret") == "fire":
            # /info에서 받은 최신 시간을 사용 (예: 별도 저장된 시간)
            data = request.get_json(silent=True) or {}
            player_pos = data.get("playerPos", {"x": 0.0, "y": 0.0, "z": 0.0})
            fire_times.append(current_time)
            fire_positions.append(player_pos)
            print(f"🔥 Fire recorded at time: {current_time}, position: {player_pos}")
        return jsonify(command)
    else:
        return jsonify({"turret": "", "weight": 0.0})

@app.route('/update_bullet', methods=['POST'])
def update_bullet():
    global impact_times, impact_positions, current_time
    data = request.get_json()
    if not data:
        return jsonify({"status": "ERROR", "message": "Invalid request data"}), 400

    impact_pos = {"x": data.get("x"), "y": data.get("y"), "z": data.get("z")}
    hit = data.get("hit")
    impact_times.append(current_time)
    impact_positions.append(impact_pos)
    print(f"💥 Bullet Impact at time: {current_time}, X={impact_pos['x']}, Y={impact_pos['y']}, Z={impact_pos['z']}, Target={hit}")
    return jsonify({"status": "OK", "message": "Bullet impact data received"})

@app.route('/info', methods=['POST'])
def info():
    global current_time
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON received"}), 400
    # 시간 정보를 저장하거나 로그로 확인
    # print(f"📨 /info data received: time={data.get('time')}")
    current_time=data.get('time')
    return jsonify({"status": "success", "control": ""})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)