import os
import threading
from flask import Flask, jsonify, request
from utils import sharedData, sharedKeyValue
from control import GameServer

app = Flask(__name__)

@app.route('/info', methods=['POST'])
def info():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON received"}), 400
    sharedData.set_data(data)
    app.logger.info("Received /info data: %s", data)
    print("Received /info data: ", data)
    return jsonify({"status": "success", "message": "Data received"}), 200

@app.route('/update_position', methods=['POST'])
def update_position():
    data = request.get_json()
    if not data or "position" not in data:
        return jsonify({"status": "ERROR", "message": "Missing position data"}), 400
    try:
        x, y, z = map(float, data["position"].split(","))
        current_position = (int(x), int(z))  # 높이 y는 무시
        print(f"Updated Position: {current_position}")
        return jsonify({"status": "success", "message": "Position updated"}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@app.route('/get_data', methods=['GET'])
def get_data():
    data = sharedData.get_data()
    if data is not None:
        app.logger.info("Returning /get_data: %s", data)
        return jsonify({"status": "success", "data": data}), 200
    app.logger.warning("No data available for /get_data")
    return jsonify({"status": "no_data", "message": "No data available"}), 404

@app.route('/get_move', methods=['GET'])
def get_move():
    move = sharedKeyValue.get_key_value()
    if move is None:
        app.logger.warning("No move command available, returning STOP")
        print("No move command available, returning STOP")
        return jsonify({"move": "STOP", "status": "no_command"}), 200
    app.logger.info("Returning move command: %s", move)
    print(f"Returning move command: {move}, SharedKeyValue: {sharedKeyValue.get_key_value()}")
    # 추가 정보 반환
    data = sharedData.get_data()
    extra_info = {}
    if data:
        extra_info = {
            "player_pos": data.get("playerPos", {}),
            "player_body_angle": data.get("playerBodyX", 0.0),
            "enemy_pos": data.get("enemyPos", {}),
            "distance": data.get("distance", 0.0),
            "player_speed": data.get("playerSpeed", 0.0)
        }
    return jsonify({"move": move, "status": "success", **extra_info}), 200

@app.route('/get_action', methods=['GET'])
def get_action():
    data = sharedData.get_data()
    if data and "playerBodyX" in data:
        angle = data["playerBodyX"]
        return jsonify({"action": "move", "angle": angle}), 200
    return jsonify({"action": "none", "message": "No valid data"}), 404

if __name__ == "__main__":
    server = GameServer()
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    app.run(host='0.0.0.0', port=5000)