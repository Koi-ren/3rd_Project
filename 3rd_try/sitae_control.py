from flask import Flask, request, jsonify
import os
import torch
from ultralytics import YOLO

app = Flask(__name__)
model = YOLO('yolov8n.pt')

# 경도 코딩
tank_val_ms = 0.0
tank_val_kh = 0.0

# Move commands with weights (11+ variations)
move_command = [
    {"move": "W", "weight": 1.0}
    # 'move':['W' or 'A' or 'S' or 'D'], 'weight': [weight]
    # 'move': ["STOP"]
]

# Action commands with weights (15+ variations)
action_command = [
    # {"turret": "Q", "weight": 1.0}
    # "turret": ["Q" or "E" or "R" or "F"], "weight":[weight]
    # "turret": ["FIRE"]
]

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

@app.route('/info', methods=['POST'])
def info():
    global tank_val_ms
    global tank_val_kh
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    # print("📨 /info data received:", data)
    
    tank_val_ms = data['playerSpeed']
    tank_val_kh = data['playerSpeed']*3.6
    
    print("📨 /info data received:", data['time'])
    print('tank_speed: {0:.2f} m/s'.format(data['playerSpeed']))
    print('tank_speed: {0:.2f} km/h'.format(data['playerSpeed']*3.6))

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



    

@app.route('/get_action', methods=['GET'])
def get_action():
    global action_command
    if action_command:
        command = action_command.pop(0)
        print(f"🔫 Action Command: {command}")
        return jsonify(command)
    else:
        #return jsonify({"turret": "", "weight": 0.0})
        return jsonify({"hh":'hi'})

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
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400

    print("🪨 Obstacle Data:", data)
    return jsonify({'status': 'success', 'message': 'Obstacle data received'})

#Endpoint called when the episode starts
@app.route('/init', methods=['GET'])
def init():
    config = {
        "startMode": "start",  # Options: "start" or "pause"
        "blStartX": 60,  #Blue Start Position
        "blStartY": 10,
        "blStartZ": 27.23,
        "rdStartawX": 59, #Red Start Position
        "rdStartY": 10,
        "rdStartZ": 280
    }
    print("🛠️ Initialization config sent via /init:", config)
    return jsonify(config)

@app.route('/start', methods=['GET'])
def start():
    print("🚀 /start command received")
    return jsonify({"control": ""})
@app.route('/get_move', methods=['GET'])
def get_move():
    # global move_command
    # if move_command:
    #     command = move_command.pop(0)
    #     print(f"🚗 Move Command: {command}")
    #     return jsonify(command)
    # else:
    #     return jsonify({"move": "STOP", "weight": 1.0})

    global tank_val_ms
    global tank_val_kh

    target_val_kh = 60 # 0.08
    kp_val = 0.18
    
    # target_val_kh = 50 # 0.08
    # kp_val = 0.152
    
    # target_val_kh = 40 # 0.08
    # kp_val = 0.0915
    
    # target_val_kh = 30 # 0.08
    # kp_val = 0.0699
    
    # target_val_kh = 20 # 0.08
    # kp_val = 0.068
    
    # target_val_kh = 10 
    # kp_val = 0.068
    

    val_error_kh = target_val_kh-tank_val_kh
    # kp_val = 0.068
    val_error_kh*kp_val
    print('controller output: {0}'.format(val_error_kh*kp_val))
    return jsonify({"move": "W", "weight": val_error_kh*kp_val})
   
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
