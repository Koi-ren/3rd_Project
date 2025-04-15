import math, time, requests, time
from utils import sharedKeyValue, sharedGoalPosition
from gameAI import Vector, Kinematic, Arrive

global slowRadius, targetRadius, timeToTarget, maxSpeed, max_x_bounds, max_z_bounds

# 감속 반경 설정
slowRadius = 100.0
# 도착 반경 설정
targetRadius = 10.0
# 목표 속도 도달 시점점
timeToTarget = 0.4
# 최고 속도(70km/h, 코드 내에선 m/s 단위 사용) 가중치 제한(0~1)
maxSpeed = 0.5
# 맵크기 제한(m이자 좌표값값)
max_x_bounds = 300
max_z_bounds = 300

class GameState:
    def __init__(self):
        self.time_value = 0.0
        self.distance = 0.0
        self.key = None
        self.player_pos = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.player_speed = 0.0
        self.player_health = 0.0
        self.player_turret_angle = 0.0
        self.player_body_angle = 0.0
        self.enemy_pos = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.enemy_speed = 0.0
        self.enemy_health = 0.0
        self.enemy_turret_angle = 0.0
        self.enemy_body_angle = 0.0
        self.has_valid_data = False
        self.last_update_time = 0.0

    def updateData(self, data):
        try:
            new_time = data.get("time", self.time_value)
            if new_time <= self.last_update_time:
                print("Skipping stale data")
                return
            self.time_value = new_time
            self.last_update_time = new_time
            self.distance = data.get("distance", self.distance)
            
            player_pos = data.get("playerPos", {})
            self.player_pos["x"] = player_pos.get("x", self.player_pos["x"])
            self.player_pos["y"] = player_pos.get("y", self.player_pos["y"])
            self.player_pos["z"] = player_pos.get("z", self.player_pos["z"])
            self.player_speed = data.get("playerSpeed", self.player_speed)
            self.player_health = data.get("playerHealth", self.player_health)
            self.player_turret_angle = data.get("playerTurretX", self.player_turret_angle)
            self.player_body_angle = data.get("playerBodyX", self.player_body_angle)
            
            enemy_pos = data.get("enemyPos", {})
            self.enemy_pos["x"] = enemy_pos.get("x", self.enemy_pos["x"])
            self.enemy_pos["y"] = enemy_pos.get("y", self.enemy_pos["y"])
            self.enemy_pos["z"] = enemy_pos.get("z", self.enemy_pos["z"])
            self.enemy_speed = data.get("enemySpeed", self.enemy_speed)
            self.enemy_health = data.get("enemyHealth", self.enemy_health)
            self.enemy_turret_angle = data.get("enemyTurretX", self.enemy_turret_angle)
            self.enemy_body_angle = data.get("enemyBodyX", self.enemy_body_angle)
            
            self.has_valid_data = bool(player_pos and enemy_pos)
            print(f"Updated GameState: {self}")
        except Exception as e:
            print(f"Error updating GameState: {e}")
            self.has_valid_data = False

    def updatekey(self, key):
        self.key = key

    def __str__(self):
        return (f"Time: {self.time_value}, Distance: {self.distance}, "
                f"Player Pos: ({self.player_pos['x']}, {self.player_pos['z']}), "
                f"Enemy Pos: ({self.enemy_pos['x']}, {self.enemy_pos['z']}), "
                f"Player Body Angle: {self.player_body_angle} deg")

class Ground:
    def __init__(self):
        global slowRadius, targetRadius, timeToTarget, maxSpeed, max_x_bounds, max_z_bounds
        self.state = GameState()
        self.shared_key_value = sharedKeyValue
        self.shared_goal__position = sharedGoalPosition
        # 아군, 적군 초기 위치 설정 - 차후 타겟 좌표는 goalPosition으로 대체할 것임
        self.character = Kinematic(position=Vector(593.5, 272.3), orientation=0.0)
        self.target = Kinematic(position=Vector(1354.6, 2768.7), orientation=0.0)
        # 맵 크기 제한 설정
        self.map_bounds = (0, max_x_bounds, 0, max_z_bounds)
        self.input_count_w = 0
        self.input_count_a = 0
        self.theta = Ground.calculate_bearing(self.state.player_pos["x"], self.state.player_pos["z"], 
                                         self.shared_goal__position.get_goal_position["x"], self.shared_goal__position.get_goal_position["z"])
        # 이동할 위치의 방위각
        self.nono, self.diff_theta = Ground.calculate_rotation(self.state.player_body_angle, self.theta)
        self.shared_key_value.set_key_value("STOP")        
        self.arrive= Arrive(
            diff_theta=self.diff_theta,
            distance=self.state.distance,
            maxSpeed=maxSpeed,
            targetRadius=targetRadius,
            slowRadius=slowRadius
        )

    def calculate_rotation(current_bearing, target_bearing):
        # 각도 차이 계산
        diff = target_bearing - current_bearing
        
        # 각도를 -180 ~ 180 범위로 정규화
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        
        # 회전 방향과 각도 결정
        if diff == 0:
            return "회전 불필요", 0
        elif diff > 0:
            direction = "시계방향"
            angle = diff
        else:
            direction = "반시계방향"
            angle = -diff
            
        return direction, angle

    def calculate_bearing(x1, z1, x2, z2):
        # 상대 좌표 계산
        delta_x = x2 - x1
        delta_z = z2 - z1
        
        # 방위각 계산 (라디안 -> 도)
        theta = math.atan2(delta_z, delta_x) * (180 / math.pi)
        
        # 음수 각도를 0~360도 범위로 변환
        if theta < 0:
            theta += 360
            
        return theta

    def fetch_data(self):
        try:
            response_data = requests.get("http://localhost:5000/get_data", timeout=0.5)
            if response_data.status_code == 200:
                data = response_data.json().get("data")
                self.target.position = Vector(
                    self.shared_goal__position["x"],
                    self.shared_goal__position["z"]
                    )
                if data:
                    self.state.updateData(data)
                    if self.state.has_valid_data:
                        self.character.position = Vector(
                            self.state.player_pos["x"],
                            self.state.player_pos["z"]
                        )
                        self.character.orientation = math.radians(self.state.player_body_angle)
                        speed = self.state.player_speed
                        if speed > 0:
                            angle_rad = math.radians(self.state.player_body_angle)
                            # 속도의 벡터화화
                            self.character.velocity = Vector(
                                speed * math.cos(angle_rad),
                                speed * math.sin(angle_rad)
                            )                        
                        else:
                            self.character.velocity = Vector(0, 0)    
            print("No valid data available.")
            return False
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return False
        
    def steering_to_move_command(self):
        RotationKey, targetRotationSpeed = self.arrive.getSteering
        targetSpeed = self.arrive.
        # 이거 왜 객체로 안뜨냐 씨잇팔
