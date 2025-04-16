from flask import Flask, request, jsonify
import threading
import logging
import time
from utils import sharedData, sharedKeyValue, sharedGoalPosition
from control import Ground

app = Flask(__name__)

logging.basicConfig(
    filename='C:/Users/acorn/Desktop/project/3rd_Project/3rd_try/server.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)

@app.route('/info', methods=['POST'])
def info():
    logging.debug("Received /info request")
    print("Received /info request")
    try:
        data = request.get_json(force=True)
        if not data:
            logging.error("No JSON received in /info")
            print("Error: No JSON data")
            return jsonify({"error": "No JSON received"}), 400
        formatted_data = {
            "time": data.get("time", 0.0),
            "distance": data.get("distance", 0.0),
            "playerPos": {
                "x": data.get("playerPos", {}).get("x", 60.0),
                "y": data.get("playerPos", {}).get("y", 8.0),
                "z": data.get("playerPos", {}).get("z", 27.23)
            },
            "playerSpeed": data.get("playerSpeed", 0.0),
            "playerHealth": data.get("playerHealth", 100.0),
            "playerTurretX": data.get("playerTurretX", 0.0),
            "playerBodyX": data.get("playerBodyX", 0.0),
            "enemyPos": {
                "x": data.get("enemyPos", {}).get("x", 135.46),
                "y": data.get("enemyPos", {}).get("y", 8.6),
                "z": data.get("enemyPos", {}).get("z", 276.87)
            },
            "enemySpeed": data.get("enemySpeed", 0.0),
            "enemyHealth": data.get("enemyHealth", 100.0),
            "enemyTurretX": data.get("enemyTurretX", 0.0),
            "enemyBodyX": data.get("enemyBodyX", 0.0),
            "lidarPoints": data.get("lidarPoints", [])
        }
        sharedData.set_data(formatted_data)
        logging.info(f"Stored /info data: time={formatted_data['time']}, playerPos={formatted_data['playerPos']}")
        print(f"Stored /info data: time={formatted_data['time']}, playerPos={formatted_data['playerPos']}")
        return jsonify({"status": "success", "message": "Data received", "control": "pause"}), 200
    except Exception as e:
        logging.error(f"Error processing /info: {e}")
        print(f"Error processing /info: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_move', methods=['GET'])
def get_move():
    command = sharedKeyValue.get_key_value()
    if command is None:
        logging.warning("No move command available, returning STOP")
        print("No move command available, returning STOP")
        return jsonify({"move": "STOP", "weight": 1.0, "timestamp": time.time()}), 200
    logging.info(f"Returning move command: {command}")
    print(f"Returning move command: {command}")
    return jsonify({"move": command["move"], "weight": command["weight"], "timestamp": time.time()}), 200

@app.route('/set_destination', methods=['POST'])
def set_destination():
    data = request.get_json()
    if not data or "destination" not in data:
        logging.error("Missing destination data")
        print("Error: Missing destination data")
        return jsonify({"status": "ERROR", "message": "Missing destination data"}), 400
    try:
        x, y, z = map(float, data["destination"].split(","))
        goal = {"x": x, "y": y, "z": z}
        sharedGoalPosition.set_goal_position(goal)
        logging.info(f"Destination set: x={x}, y={y}, z={z}")
        print(f"🎯 Destination set to: x={x}, y={y}, z={z}")
        return jsonify({"status": "OK", "destination": {"x": x, "y": y, "z": z}})
    except Exception as e:
        logging.error(f"Invalid destination format: {e}")
        print(f"Error setting destination: {e}")
        return jsonify({"status": "ERROR", "message": f"Invalid format: {str(e)}"}), 400

@app.route('/status', methods=['GET'])
def status():
    goal = sharedGoalPosition.get_goal_position()
    data = sharedData.get_data()
    command = sharedKeyValue.get_key_value()
    logging.info(f"Status requested: goal={goal}, command={command}")
    print(f"Status: goal={goal}, command={command}")
    return jsonify({
        "goal_position": goal,
        "current_data": data,
        "current_command": command
    })

def main():
    try:
        ground = Ground()
        ground_thread = threading.Thread(target=ground.run, daemon=True)
        ground_thread.start()
        logging.info("Ground thread started")
        print("Ground thread started")
        # 초기 목표 설정 제거
        app.run(host="0.0.0.0", port=5000)
    except Exception as e:
        logging.error(f"Error in main: {e}")
        print(f"Error in main: {e}")

@app.route('/update_bullet', methods=['POST'])
def update_bullet():
    data = request.get_json()
    if not data:
        return jsonify({"status": "ERROR", "message": "Invalid request data"}), 400
    logging.info(f"Bullet Impact: {data}")
    print(f"💥 Bullet Impact at X={data.get('x')}, Y={data.get('y')}, Z={data.get('z')}, Target={data.get('hit')}")
    return jsonify({"status": "OK", "message": "Bullet impact data received"})

@app.route('/get_action', methods=['GET'])
def get_action():
    action_command = [
        {"turret": "Q", "weight": 1.0},
        {"turret": "E", "weight": 1.0},
        {"turret": "FIRE"}
    ]
    command = action_command[0]
    logging.info(f"Action Command: {command}")
    print(f"🔫 Action Command: {command}")
    return jsonify(command), 200

@app.route('/detect', methods=['POST'])
def detect():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400
    logging.info(f"Detection data: {data}")
    print(f"🕵️‍♂️ Detection data received: {data}")
    return jsonify([{
        "className": "person",
        "bbox": [100, 100, 200, 200],
        "confidence": 0.9,
        "isDetected": True
    }]), 200

@app.route('/update_obstacle', methods=['POST'])
def update_obstacle():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400
    logging.info(f"Obstacle Data: {data}")
    print(f"🪨 Obstacle Data: {data}")
    return jsonify({'status': 'success', 'message': 'Obstacle data received'}), 200

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
    logging.info(f"Initialization config: {config}")
    print(f"🛠️ Initialization config sent: {config}")
    return jsonify(config), 200

@app.route('/start', methods=['GET'])
def start():
    logging.info("/start command received")
    print("🚀 /start command received")
    return jsonify({"control": "start"}), 200

@app.route('/update_position', methods=['POST'])
def update_position():
    data = request.get_json()
    if not data or "position" not in data:
        logging.error("Missing position data")
        return jsonify({"status": "ERROR", "message": "Missing position data"}), 400
    try:
        x, y, z = map(float, data["position"].split(","))
        current_position = {"x": x, "y": y, "z": z}
        info_data = sharedData.get_data()
        info_pos = info_data.get("playerPos", {}) if info_data else {}
        logging.info(f"Position comparison: update_position={current_position}, info={info_pos}")
        print(f"Position comparison: update_position={current_position}, info={info_pos}")
        return jsonify({"status": "OK", "current_position": {"x": x, "z": z}})
    except Exception as e:
        logging.error(f"Error updating position: {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 400

if __name__ == '__main__':
    main()