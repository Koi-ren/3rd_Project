from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Move commands with weights (11+ variations)
move_command = [
    {"move": "W", "weight": 1.0},
    {"move": "W", "weight": 0.6},
    {"move": "W", "weight": 0.3},
    {"move": "D", "weight": 1.0},
    {"move": "D", "weight": 0.6},
    {"move": "D", "weight": 0.4},
    {"move": "A", "weight": 1.0},
    {"move": "A", "weight": 0.3},
    {"move": "S", "weight": 0.5},
    {"move": "S", "weight": 0.1},
    {"move": "STOP"}
]

# Action commands with weights (15+ variations)
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

@app.route('/detect', methods=['POST'])
def detect():
    return 

@app.route('/info', methods=['POST'])
def info():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    print("📨 /info data received:", data)

    # Auto-pause after 15 seconds
    #if data.get("time", 0) > 15:
    #    return jsonify({"status": "success", "control": "pause"})
    # Auto-reset after 15 seconds
    #if data.get("time", 0) > 15:
    #    return jsonify({"stsaatus": "success", "control": "reset"})
    return jsonify({"status": "success", "control": ""})

@app.route('/update_position', methods=['POST'])
def update_position():
    data = request.get_json()
    if not data or "position" not in data:
        return jsonify({"status": "ERROR", "message": "Missing position data"}), 400

    try:
        x, y, z = map(float, data["position"].split(","))
        current_position = (int(x), int(z))
        print(f"📍 Position updated: {current_position}")
        return jsonify({"status": "OK", "current_position": current_position})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@app.route('/get_move', methods=['GET'])
def get_move():
    global move_command
    if move_command:
        command = move_command.pop(0)
        print(f"🚗 Move Command: {command}")
        return jsonify(command)
    else:
        return jsonify({"move": "STOP", "weight": 1.0})

@app.route('/get_action', methods=['GET'])
def get_action():

    return 

@app.route('/update_bullet', methods=['POST'])
def update_bullet():
    data = request.get_json()
    if not data:
        return jsonify({"status": "ERROR", "message": "Invalid request data"}), 400

    print(f"💥 Bullet Impact at X={data.get('x')}, Y={data.get('y')}, Z={data.get('z')}, Target={data.get('hit')}")
    return jsonify({"status": "OK", "message": "Bullet impact data received"})

@app.route('/set_destination', methods=['POST'])
def set_destination():
    data = request.get_json()
    if not data or "destination" not in data:
        return jsonify({"status": "ERROR", "message": "Missing destination data"}), 400

    try:
        x, y, z = map(float, data["destination"].split(","))
        print(f"🎯 Destination set to: x={x}, y={y}, z={z}")
        return jsonify({"status": "OK", "destination": {"x": x, "y": y, "z": z}})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": f"Invalid format: {str(e)}"}), 400

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
