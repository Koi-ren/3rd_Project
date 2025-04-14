from flask import Flask, request, jsonify
import math, time

app = Flask(__name__)

# 글로벌 상태
current_position = None 
goal = None              
target_radius = 10.0
move_distance = 1.0

class Vector:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
    
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)
    
    def length(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def __str__(self):
        return f"Vector({self.x:.2f}, {self.y:.2f})"

def get_direction(start, goal):

    direction = Vector(goal[0], goal[1]) - Vector(start[0], start[1])
    distance = direction.length()
    
    if distance < target_radius:
        return "STOP"
    
    dx = goal[0] - start[0]
    dz = goal[1] - start[1]
    
    # 이동 거리 제한
    if abs(dx) < move_distance and abs(dz) < move_distance:
        return "STOP"
    
    # 방향 우선순위: x 차이 > z 차이
    if abs(dx) > abs(dz):
        return "D" if dx > 0 else "A"
    return "W" if dz > 0 else "S"

@app.route('/', methods=['GET'])
def home():
    return 'hello world'

@app.route('/detect', methods=['POST'])
def detect():
    return

@app.route('/update_position', methods=['POST'])
def update_position():
    """
    유니티에서 전차 위치 업데이트.
    position: "x,y,z"
    """
    global current_position
    try:
        data = request.json
        position = data.get("position")
        print(f"Received position: {position}")
        x, y, z = map(float, position.split(","))
        current_position = (x * 10, z * 10)  # 1 coord = 10m
        return jsonify({"status": "OK", "current_position": current_position}), 200
    except Exception as e:
        print(f"Update position error: {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@app.route('/set_destination', methods=['POST'])
def set_destination():
    """
    목표 지점 설정.
    destination: "x,y,z"
    """
    global goal, current_position
    try:
        data = request.json
        destination = data.get("destination")
        print(f"Destination: {destination}")
        
        if current_position is None:
            print("Current position not set")
            return jsonify({"status": "ERROR", "message": "Call /update_position first"}), 400
        
        x_dest, _, z_dest = map(float, destination.split(","))
        goal = (x_dest * 10, z_dest * 10)
        
        # 초기 거리 확인
        direction = Vector(goal[0], goal[1]) - Vector(current_position[0], current_position[1])
        distance = direction.length()
        print(f"Distance to goal: {distance:.2f}m")
        
        command = get_direction(current_position, goal)
        time.sleep(0.2)
        return jsonify({"status": "OK", "command": command}), 200
    except Exception as e:
        print(f"Set destination error: {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@app.route('/get_move', methods=['GET'])
def get_move():
    """
    다음 이동 명령 반환.
    """
    global current_position, goal
    if current_position is None or goal is None:
        print("Position or goal not set")
        return jsonify({"move": "STOP"}), 200
    
    command = get_direction(current_position, goal)
    print(f"Returning move: {command}")
    if command == "STOP": get_move()
    return jsonify({"move": command}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)