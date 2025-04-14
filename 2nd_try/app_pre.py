import asyncio
from flask import Flask, jsonify, request
from flask_cors import CORS
from utils import sharedData, sharedKeyValue
from control import GameServer
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# 터렛 명령 큐 (유니티 시뮬레이터에 따라 조정 필요)
action_command = ["FIRE", "AIM", "RELOAD", "HOLD"]

@app.route('/info', methods=['POST'])
def info():
    print("Received /info request")
    try:
        data = request.get_json(force=True)
        if not data:
            app.logger.error("No JSON received in /info")
            print("Error: No JSON data")
            return jsonify({"error": "No JSON received"}), 400
        print(f"Data content: {data}")
        sharedData.set_data(data)
        app.logger.info("Received /info data: %s", data)
        return jsonify({"status": "success", "message": "Data received"}), 200
    except Exception as e:
        app.logger.error(f"Error processing /info: {e}")
        print(f"Error processing /info: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/update_position', methods=['POST'])
def update_position():
    print("Received /update_position request")
    try:
        data = request.get_json()
        if not data or "position" not in data:
            app.logger.error("No JSON received in /update_position")
            print("Error: No JSON data")
            return jsonify({"status": "ERROR", "message": "Missing position data"}), 400
        x, y, z = map(float, data["position"].split(","))
        current_position = (x, z)  # 높이 y 무시
        print(f"Updated Position: {current_position}")
        return jsonify({"status": "success", "message": "Position updated", "position": current_position}), 200
    except Exception as e:
        app.logger.error(f"Error processing /update_position: {e}")
        print(f"Error processing /update_position: {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@app.route('/get_data', methods=['GET'])
def get_data():
    print("Received /get_data request")
    data = sharedData.get_data()
    if data is not None:
        app.logger.info("Returning /get_data: %s", data)
        print(f"Returning data: {data}")
        return jsonify({"status": "success", "data": data}), 200
    app.logger.warning("No data available for /get_data")
    print("No data available")
    return jsonify({"status": "no_data", "message": "No data available"}), 404

@app.route('/get_move', methods=['GET'])
def get_move():
    print("Received /get_move request")
    move = sharedKeyValue.get_key_value()
    if move is None:
        app.logger.warning("No move command available, returning STOP")
        print("No move command available, returning STOP")
        return jsonify({"move": "STOP", "status": "no_command"}), 200
    app.logger.info("Returning move command: %s", move)
    print(f"Returning move command: {move}, SharedKeyValue: {sharedKeyValue.get_key_value()}")
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
    """Provides the next turret action command to the simulator."""
    global action_command
    print("Received /get_action request")
    try:
        if action_command:
            command = action_command.pop(0)
            app.logger.info(f"Sent Action Command: {command}")
            print(f"Sent Action Command: {command}")
            return jsonify({"turret": command}), 200
        else:
            app.logger.warning("No action command available, returning empty")
            print("No action command available, returning empty")
            return jsonify({"turret": " "}), 200
    except Exception as e:
        app.logger.error(f"Error processing /get_action: {e}")
        print(f"Error processing /get_action: {e}")
        return jsonify({"error": str(e)}), 500

async def main():
    print("Initializing GameServer and Flask")
    server = GameServer()
    sharedData.set_data({
        "time": 0.0,
        "distance": 260.985,
        "playerPos": {"x": 59.35, "y": 8.0, "z": 27.23},
        "playerSpeed": 0.0,
        "playerHealth": 100.0,
        "playerTurretX": 0.0,
        "playerBodyX": 0.0,
        "enemyPos": {"x": 135.46, "y": 8.6, "z": 276.87},
        "enemySpeed": 0.0,
        "enemyHealth": 100.0,
        "enemyTurretX": 180.0,
        "enemyBodyX": 180.0
    })
    sharedKeyValue.set_key_value("W")
    server_task = asyncio.create_task(server.run())
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    flask_task = asyncio.create_task(serve(app, config))
    await asyncio.gather(server_task, flask_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down")
    except Exception as e:
        print(f"Main loop error: {e}")