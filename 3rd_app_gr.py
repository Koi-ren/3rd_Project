# app.py
from flask import Flask, request, jsonify
import threading
from utils import sharedData, sharedKeyValue, sharedGoalPosition
from control import Ground

app = Flask(__name__)

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

@app.route('/get_move', methods=['GET'])
def get_move():
    command = sharedKeyValue.get_key_value()
    if command is None:
        app.logger.warning("No move command available, returning STOP")
        print("No move command available, returning STOP")
        return jsonify({"move": "STOP", "weight": 1.0}), 200
    print(f"Returning move command: {command}, SharedKeyValue: {sharedKeyValue.get_key_value()}")
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
    return jsonify({"move": command,"status": "success", **extra_info}), 200

@app.route('/set_destination', methods=['POST'])
def set_destination():
    data = request.get_json()
    if not data or "destination" not in data:
        return jsonify({"status": "ERROR", "message": "Missing destination data"}), 400

    try:
        x, y, z = map(float, data["destination"].split(","))
        goal = {"x":x, "y":y, "z":z}
        sharedGoalPosition(goal)
        print(f"🎯 Destination set to: x={x}, y={y}, z={z}")
        return jsonify({"status": "OK", "destination": {"x": x, "y": y, "z": z}})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": f"Invalid format: {str(e)}"}), 400

def main():
    ground = Ground()
    ground_thread = threading.Thread(target=ground.run, daemon=True)
    ground_thread.start()
    app.run(host="0.0.0.0", port=5000)

@app.route('/update_bullet', methods=['POST'])
def update_bullet():
    data = request.get_json()
    if not data:
        return jsonify({"status": "ERROR", "message": "Invalid request data"}), 400

    print(f"💥 Bullet Impact at X={data.get('x')}, Y={data.get('y')}, Z={data.get('z')}, Target={data.get('hit')}")
    return jsonify({"status": "OK", "message": "Bullet impact data received"})

###################################################################################
###################################################################################
###################################################################################

@app.route('/get_action', methods=['GET'])
def get_action():
    return 

@app.route('/detect', methods=['POST'])
def detect():
    return 

@app.route('/update_obstacle', methods=['POST'])
def update_obstacle():
    return

#Endpoint called when the episode starts
@app.route('/init', methods=['GET'])
def init():
    return

@app.route('/start', methods=['GET'])
def start():
    return

@app.route('/update_position', methods=['POST'])
def update_position():
    return

if __name__ == '__main__':
    main()
