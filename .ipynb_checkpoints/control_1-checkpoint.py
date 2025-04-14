import requests
import time
import threading
import math
from gameAI import Kinematic, Vector, Arrive
from utills import sharedKeyValue

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

class GameServer:
    def __init__(self):
        self.state = GameState()
        self.shared_key_value = sharedKeyValue
        self.character = Kinematic(position=Vector(0, 0), orientation=0.0)
        self.target = Kinematic(position=Vector(0, 0), orientation=0.0)
        self.arrive = Arrive(
            character=self.character,
            target=self.target,
            maxAcceleration=10.0,  # 유니티 단위(m/s²)
            maxSpeed=13.89,       # 50km/h (m/s)
            targetRadius=0.5,
            slowRadius=10.0,
            timeToTarget=0.1
        )
        self.time_step = 0.1
        self.input_count_w = 0
        self.current_speed = 0.0
        self.max_rotation_per_step = math.radians(5.62)
        self.last_command = "STOP"
        self.shared_key_value.set_key_value("STOP")
        self.last_position = Vector(0, 0)

    def calculate_speed(self, input_count):
        if input_count <= 0:
            return 0.0
        speed = 19.44 / (1 + math.exp(-0.18 * (input_count - 25)))  # 유니티 단위(m/s)
        print(f"Calculated speed for input_count={input_count}: {speed:.2f} m/s")
        return speed

    def fetch_data(self):
        try:
            response_data = requests.get("http://localhost:5000/get_data", timeout=0.5)
            if response_data.status_code == 200:
                data = response_data.json().get("data")
                if data:
                    self.state.updateData(data)
                    if self.state.has_valid_data:
                        self.target.position = Vector(self.state.enemy_pos["x"], self.state.enemy_pos["z"])
                        self.target.orientation = math.radians(self.state.enemy_body_angle)
                        self.character.orientation = math.radians(self.state.player_body_angle)
                        # 초기 위치는 유니티에서 가져오지 않고 유지
                        print(f"Data fetched: Player Pos={self.character.position}, Orientation={math.degrees(self.character.orientation)} deg, Target Pos={self.target.position}, Source=/get_data")
                        return True
            print("No valid data available.")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return False

    def steering_to_move_command(self, steering, character):
        if steering is None or not self.state.has_valid_data:
            self.input_count_w = max(0, self.input_count_w - 1)
            self.current_speed = self.calculate_speed(self.input_count_w)
            print("No steering or invalid data, command: STOP")
            return "STOP"

        linear_speed = steering.linear.length()
        if linear_speed < 0.01:
            self.input_count_w = max(0, self.input_count_w - 1)
            self.current_speed = self.calculate_speed(self.input_count_w)
            print("Linear speed too low, command: STOP")
            return "STOP"

        current_direction = Vector(math.cos(character.orientation), math.sin(character.orientation))
        target_direction = steering.linear * (1.0 / max(0.0001, linear_speed))

        dot_product = current_direction.x * target_direction.x + current_direction.y * target_direction.y
        dot_product = min(1.0, max(-1.0, dot_product))
        angle = math.acos(dot_product)
        print(f"Direction angle: {math.degrees(angle):.2f} degrees")

        cross_product = current_direction.x * target_direction.y - current_direction.y * target_direction.x
        if abs(angle) > math.radians(15):  # 임계값 완화
            command = "D" if cross_product > 0 else "A"
            print(f"Rotating, command: {command}, angle: {math.degrees(angle):.2f}, cross: {cross_product:.4f}")
            return command

        self.input_count_w += 1
        self.current_speed = self.calculate_speed(self.input_count_w)
        command = "W" if abs(angle) < math.radians(90) else "S"
        print(f"Moving, command: {command}, speed: {self.current_speed:.2f}")
        return command

    def run(self):
        while True:
            if self.fetch_data():
                steering = self.arrive.getSteering()
                move_command = self.steering_to_move_command(steering, self.character)
                
                self.shared_key_value.set_key_value(move_command)
                self.last_command = move_command
                print(f"Command stored: {move_command}, SharedKeyValue: {self.shared_key_value.get_key_value()}")

                if move_command == "W" or move_command == "S":
                    direction = 1 if move_command == "W" else -1
                    self.character.velocity = Vector(
                        math.cos(self.character.orientation) * self.current_speed * direction,
                        math.sin(self.character.orientation) * self.current_speed * direction
                    )
                    self.character.position += self.character.velocity * self.time_step
                    self.state.player_pos["x"] = self.character.position.x
                    self.state.player_pos["z"] = self.character.position.y
                    print(f"Updated position: {self.character.position}, velocity: {self.character.velocity}")
                elif move_command == "A":
                    self.character.orientation -= self.max_rotation_per_step
                    self.character.velocity = Vector(0, 0)
                    self.state.player_body_angle = math.degrees(self.character.orientation) % 360
                    print(f"Rotated counter-clockwise, orientation: {math.degrees(self.character.orientation):.2f} deg")
                elif move_command == "D":
                    self.character.orientation += self.max_rotation_per_step
                    self.character.velocity = Vector(0, 0)
                    self.state.player_body_angle = math.degrees(self.character.orientation) % 360
                    print(f"Rotated clockwise, orientation: {math.degrees(self.character.orientation):.2f} deg")
                else:
                    self.character.velocity = Vector(0, 0)
                    print("Stopped, velocity: 0")

                print(f"Time: {self.state.time_value:.1f}, "
                      f"Player Pos: {self.character.position}, "
                      f"Target Pos: {self.target.position}, "
                      f"Speed: {self.current_speed:.2f} m/s, "
                      f"Orientation: {math.degrees(self.character.orientation):.2f} deg, "
                      f"Move Command: {move_command}")
            else:
                self.shared_key_value.set_key_value(self.last_command)
                print(f"No data, using last command: {self.last_command}, SharedKeyValue: {self.shared_key_value.get_key_value()}")

            time.sleep(self.time_step)

if __name__ == "__main__":
    server = GameServer()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    thread.join()