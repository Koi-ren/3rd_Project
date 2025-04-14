import math, time, requests, time
from utils import sharedKeyValue
from gameAI import Kinematic, Vector, Arrive

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
            self.player_pos["x"] = player_pos.get("x", self.player_pos["x"]) * 10
            self.player_pos["y"] = player_pos.get("y", self.player_pos["y"]) * 10
            self.player_pos["z"] = player_pos.get("z", self.player_pos["z"]) * 10
            self.player_speed = data.get("playerSpeed", self.player_speed)
            self.player_health = data.get("playerHealth", self.player_health)
            self.player_turret_angle = data.get("playerTurretX", self.player_turret_angle)
            self.player_body_angle = data.get("playerBodyX", self.player_body_angle)
            
            enemy_pos = data.get("enemyPos", {})
            self.enemy_pos["x"] = enemy_pos.get("x", self.enemy_pos["x"]) * 10
            self.enemy_pos["y"] = enemy_pos.get("y", self.enemy_pos["y"]) * 10
            self.enemy_pos["z"] = enemy_pos.get("z", self.enemy_pos["z"]) * 10
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

class GameServer:
    def __init__(self):
        self.state = GameState()
        self.shared_key_value = sharedKeyValue
        self.character = Kinematic(position=Vector(593.5, 272.3), orientation=0.0)
        self.target = Kinematic(position=Vector(1354.6, 2768.7), orientation=0.0)
        self.arrive= Arrive(
            character=self.character,
            target=self.target,
            maxAcceleration=0.5,
            maxSpeed=19.44,
            targetRadius=10.,
            slowRadius=300.0,
            timeToTarget=0.2
        )
        self.time_step = 0.125
        self.input_count_w = 0
        self.input_count_a = 0
        self.current_speed = 0.0
        self.max_rotation_per_step = math.radians(5.0)
        self.last_command = "STOP"
        self.shared_key_value.set_key_value("STOP")
        self.last_position = Vector(5.935, 25.696)
        self.map_bounds = (0, 3000, 0, 3000)

    def calculate_speed(self, input_count):
        if input_count <= 0: return 0.0
        speed = min(19.44 / (1 + math.exp(-0.18 * (input_count - 25))) / 10.0, self.state.player_speed / 10.0)
        print(f"Calculated speed for input_count={input_count}: {speed:.2f} coord/s")
        return speed    
    
    def calculate_angle_diff(self, target_pos):
        """타겟 방향과의 각도 차이 계산"""
        direction = target_pos - self.character.position
        if direction.length() == 0:
            return 0.0
        target_angle = math.atan2(direction.y, direction.x)
        current_angle = self.character.orientation
        angle_diff = target_angle - current_angle
        # 각도 정규화 (-π ~ π)
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        return angle_diff

    def fetch_data(self):
        """HTTP 데이터 가져오기 및 상태 동기화"""
        try:
            response_data = requests.get("http://localhost:5000/get_data", timeout=0.5)
            if response_data.status_code == 200:
                data = response_data.json().get("data")
                if data:
                    self.state.updateData(data)
                    if self.state.has_valid_data:
                        self.character.position = Vector(
                            self.state.player_pos["x"],
                            self.state.player_pos["z"]
                        )
                        self.target.position = Vector(
                            self.state.enemy_pos["x"],
                            self.state.enemy_pos["z"]
                        )
                        self.character.orientation = math.radians(self.state.player_body_angle)
                        speed = self.state.player_speed
                        if speed > 0:
                            angle_rad = math.radians(self.state.player_body_angle)
                            self.character.velocity = Vector(
                                speed * math.cos(angle_rad),
                                speed * math.sin(angle_rad)
                            )
                        else:
                            self.character.velocity = Vector(0, 0)
                        print(f"Data fetched: Player Pos={self.character.position}, "
                              f"Velocity={self.character.velocity}, "
                              f"Orientation={math.degrees(self.character.orientation)} deg, "
                              f"Target Pos={self.target.position}, Source=/get_data")
                        return True
            print("No valid data available.")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return False

    def steering_to_move_command(self, steering, character):
        """Arrive 스티어링을 키보드 입력으로 변환"""
        if steering is None or not self.state.has_valid_data:
            self.input_count_w = max(0, self.input_count_w - 1)
            self.current_speed = self.calculate_speed(self.input_count_w)
            print("No steering or invalid data, command: STOP")
            return "STOP"

        # 경계 체크
        min_x, max_x, min_z, max_z = self.map_bounds
        if (character.position.x <= min_x + 0.1 or character.position.x >= max_x - 0.1 or
            character.position.y <= min_z + 0.1 or character.position.y >= max_z - 0.1):
            print("Near map boundary, command: STOP")
            return "STOP"

        # 타겟 방향 계산
        angle_diff = self.calculate_angle_diff(self.target.position)
        direction_angle_deg = math.degrees(angle_diff)
        print(f"Direction angle: {direction_angle_deg:.2f} degrees")

        # 거리 체크
        distance = (self.target.position - self.character.position).length()
        if distance < self.arrive.targetRadius:
            print("Within targetRadius, command: STOP")
            return "STOP"
        elif distance < self.arrive.slowRadius:
            target_speed = self.arrive.maxSpeed * (distance / self.arrive.slowRadius)
            if self.current_speed > target_speed:
                self.input_count_w = max(0, self.input_count_w - 1)
                self.current_speed = self.calculate_speed(self.input_count_w)
                print(f"SlowRadius, reducing speed: {self.current_speed:.2f}, command: S")
                return "S"

        # 회전 판단
        if abs(angle_diff) > math.radians(5):  # 5도 이상 차이
            rotation = min(self.max_rotation_per_step, abs(angle_diff)) * (1 if angle_diff > 0 else -1)
            command = "D" if angle_diff > 0 else "A"
            self.input_count_a += 1 if command == "A" else -1
            # 부드러운 회전 (Lerp)
            t = 0.1  # 회전 속도
            self.character.orientation += rotation * t
            self.character.orientation = self.character.orientation % (2 * math.pi)
            print(f"Rotating, command: {command}, angle_diff: {direction_angle_deg:.2f}, rotation: {math.degrees(rotation):.2f}")
            return command
        
        # 전진
        self.input_count_w += 1
        self.current_speed = self.calculate_speed(self.input_count_w)
        self.character.velocity = Vector(
            math.cos(self.character.orientation) * self.current_speed,
            math.sin(self.character.orientation) * self.current_speed
        )
        print(f"Moving, command: W, speed: {self.current_speed:.2f}")
        return "W"

    def run(self):
        while True:
            if self.fetch_data():
                steering = self.arrive.getSteering()
                move_command = self.steering_to_move_command(steering, self.character)
                
                self.shared_key_value.set_key_value(move_command)
                self.last_command = move_command
                print(f"Command stored: {move_command}, SharedKeyValue: {self.shared_key_value.get_key_value()}")

                # 상태 업데이트
                if move_command == "W" or move_command == "S":
                    direction = 1 if move_command == "W" else -1
                    self.current_speed = self.calculate_speed(self.input_count_w)
                    self.character.velocity = Vector(
                        math.cos(self.character.orientation) * self.current_speed * direction,
                        math.sin(self.character.orientation) * self.current_speed * direction
                    )
                    # 위치 업데이트는 Kinematic.update에서 처리
                    self.character.update(steering, self.arrive.maxSpeed, self.time_step, self.map_bounds)
                    self.state.player_pos["x"] = self.character.position.x * 10
                    self.state.player_pos["z"] = self.character.position.y * 10
                    self.state.player_body_angle = math.degrees(self.character.orientation)
            time.sleep(self.time_step)