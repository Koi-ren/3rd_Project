import math, time, logging
from gameAI import Vector, Kinematic, Arrive
from utils import sharedData, sharedKeyValue, sharedGoalPosition

logging.basicConfig(
    filename='C:/Users/acorn/Desktop/project/3rd_Project/3rd_try/control.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)

class InitState:
    def __init__(self):
        self.slowRadius = 50.0
        self.targetRadius = 5.0
        self.maxSpeed = 19.44
        self.max_x_bounds = 300
        self.max_z_bounds = 300

class GameState:
    def __init__(self):
        self.time_value = 0.0
        self.distance = 0.0
        self.key = None
        self.player_pos = {"x": 60.0, "y": 8.0, "z": 27.23}
        self.player_speed = 0.0
        self.player_health = 100.0
        self.player_turret_angle = 0.0
        self.player_body_angle = 0.0
        self.enemy_pos = {"x": 135.46, "y": 8.6, "z": 276.87}
        self.enemy_speed = 0.0
        self.enemy_health = 100.0
        self.enemy_turret_angle = 0.0
        self.enemy_body_angle = 0.0
        self.lidar_points = []
        self.has_valid_data = True
        self.last_update_time = -float('inf')

    def updateData(self, data):
        try:
            new_time = data.get("time", self.time_value)
            if new_time < self.last_update_time - 1.0:
                logging.warning(f"Skipping stale data: time={new_time}")
                print(f"Skipping stale data: time={new_time}")
                return
            self.time_value = new_time
            self.last_update_time = new_time
            self.distance = data.get("distance", self.distance)
            
            player_pos = data.get("playerPos", {})
            self.player_pos["x"] = player_pos.get("x", self.player_pos["x"])
            self.player_pos["y"] = player_pos.get("y", self.player_pos["y"])
            self.player_pos["z"] = player_pos.get("z", self.player_pos["z"])
            logging.debug(f"Position updated: {self.player_pos}")
            print(f"Position updated: {self.player_pos}")
            
            self.player_speed = data.get("playerSpeed", self.player_speed)
            self.player_health = data.get("playerHealth", self.player_health)
            self.player_turret_angle = data.get("playerTurretX", self.player_turret_angle)
            self.player_body_angle = data.get("playerBodyX", self.player_body_angle)
            logging.debug(f"Player body angle updated: {self.player_body_angle}")
            print(f"Player body angle updated: {self.player_body_angle}")
            
            enemy_pos = data.get("enemyPos", {})
            self.enemy_pos["x"] = enemy_pos.get("x", self.enemy_pos["x"])
            self.enemy_pos["y"] = enemy_pos.get("y", self.enemy_pos["y"])
            self.enemy_pos["z"] = enemy_pos.get("z", self.enemy_pos["z"])
            self.enemy_speed = data.get("enemySpeed", self.enemy_speed)
            self.enemy_health = data.get("enemyHealth", self.enemy_health)
            self.enemy_turret_angle = data.get("enemyTurretX", self.enemy_turret_angle)
            self.enemy_body_angle = data.get("enemyBodyX", self.enemy_body_angle)
            self.lidar_points = data.get("lidarPoints", self.lidar_points)
            
            self.has_valid_data = True
            logging.info(f"Updated GameState: time={self.time_value}, player_pos={self.player_pos}, body_angle={self.player_body_angle}")
            print(f"Updated GameState: time={self.time_value}, player_pos={self.player_pos}, body_angle={self.player_body_angle}")
        except Exception as e:
            logging.error(f"Error updating GameState: {e}")
            print(f"Error updating GameState: {e}")
            self.has_valid_data = False

    def updatekey(self, key):
        self.key = key

    def __str__(self):
        return (f"Time: {self.time_value}, Distance: {self.distance}, "
                f"Player Pos: ({self.player_pos['x']}, {self.player_pos['z']}), "
                f"Enemy Pos: ({self.enemy_pos['x']}, {self.enemy_pos['z']}), "
                f"Player Body Angle: {self.player_body_angle} deg")

class Ground(InitState):
    def __init__(self):
        super().__init__()
        self.state = GameState()
        self.shared_key_value = sharedKeyValue
        self.shared_goal_position = sharedGoalPosition
        self.character = Kinematic(position=Vector(60.0, 27.23))
        self.target = Kinematic(position=Vector(135.46, 276.87))
        self.map_bounds = (0, self.max_x_bounds, 0, self.max_z_bounds)
        self.input_count_w = 0
        self.input_count_a = 0
        self.last_command = {"move": "STOP", "weight": 1.0}

    def calculate_rotation(self, current_bearing, target_bearing):
        diff = target_bearing - current_bearing
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        if abs(diff) < 0.5:
            direction = "NONE"
            angle = 0
        elif diff > 0:
            direction = "D"
            angle = diff
        else:
            direction = "A"
            angle = -diff
        logging.debug(f"Rotation: current={current_bearing}, target={target_bearing}, diff={diff}, direction={direction}")
        print(f"Rotation: current={current_bearing}, target={target_bearing}, diff={diff}, direction={direction}")
        return direction, angle

    def calculate_bearing(self, x1, z1, x2, z2):
        delta_x = x2 - x1
        delta_z = z2 - z1
        theta = math.atan2(delta_z, delta_x) * (180 / math.pi)
        if theta < 0:
            theta += 360
        return theta

    def fetch_data(self):
        logging.debug("Fetching data...")
        data = sharedData.get_data()
        if not data:
            logging.warning("No valid data available, using defaults.")
            print("No valid data available, using defaults.")
            return False
        try:
            self.state.updateData(data)
            goal = self.shared_goal_position.get_goal_position()
            logging.debug(f"Goal fetched: {goal}")
            self.target.position = Vector(goal["x"], goal["z"])
            if self.state.has_valid_data:
                self.character.position = Vector(
                    self.state.player_pos["x"],
                    self.state.player_pos["z"]
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
                self.state.distance = math.sqrt(
                    (goal["x"] - self.state.player_pos["x"])**2 +
                    (goal["z"] - self.state.player_pos["z"])**2
                )
                self.theta = self.calculate_bearing(
                    self.state.player_pos["x"], self.state.player_pos["z"],
                    goal["x"], goal["z"]
                )
                rotation_direction, diff_theta = self.calculate_rotation(
                    self.state.player_body_angle, self.theta
                )
                self.arrive = Arrive(
                    diff_theta=diff_theta,
                    distance=self.state.distance,
                    maxSpeed=self.maxSpeed,
                    targetRadius=self.targetRadius,
                    slowRadius=self.slowRadius
                )
                logging.info(f"Fetched data: goal={goal}, distance={self.state.distance}, theta={self.theta}, body_angle={self.state.player_body_angle}, rotation_direction={rotation_direction}, diff_theta={diff_theta}")
                print(f"Fetched data: goal={goal}, distance={self.state.distance}, theta={self.theta}, body_angle={self.state.player_body_angle}, rotation_direction={rotation_direction}, diff_theta={diff_theta}")
                return True
        except Exception as e:
            logging.error(f"Error processing data: {e}")
            print(f"Error processing data: {e}")
            return False

    def steering_to_move_command(self):
        try:
            RotationKey, targetRotationSpeed = self.arrive.getSteering()
            targetSpeed = self.arrive.getSpeed()
            logging.debug(f"Steering: RotationKey={RotationKey}, Speed={targetSpeed}, Weight={targetRotationSpeed}")
            print(f"Steering: RotationKey={RotationKey}, Speed={targetSpeed}, Weight={targetRotationSpeed}")
            if targetSpeed < 0.1:
                command = {"move": "STOP", "weight": 1.0}
            elif RotationKey == "NONE":
                weight = min(targetSpeed / self.maxSpeed, 1.0)
                if weight < 0.1:
                    weight = 0.1
                command = {"move": "W", "weight": weight}
                expected_dx = math.cos(math.radians(self.state.player_body_angle))
                expected_dz = math.sin(math.radians(self.state.player_body_angle))
                target_dx = (self.target.position.x - self.character.position.x) / self.state.distance
                target_dz = (self.target.position.y - self.character.position.y) / self.state.distance
                logging.debug(f"Move direction: expected=({expected_dx:.3f}, {expected_dz:.3f}), target=({target_dx:.3f}, {target_dz:.3f})")
                print(f"Move direction: expected=({expected_dx:.3f}, {expected_dz:.3f}), target=({target_dx:.3f}, {target_dz:.3f})")
            else:
                command = {"move": RotationKey, "weight": targetRotationSpeed}
            self.last_command = command
            self.shared_key_value.set_key_value(command)
            logging.info(f"Command stored: {command}")
            print(f"Command stored: {command}")
            return command
        except Exception as e:
            logging.error(f"Error in steering_to_move_command: {e}")
            print(f"Error in steering_to_move_command: {e}")
            return self.last_command

    def run(self):
        logging.info("Starting Ground.run")
        print("Starting Ground.run")
        while True:
            try:
                if self.fetch_data():
                    command = self.steering_to_move_command()
                else:
                    goal = self.shared_goal_position.get_goal_position()
                    if goal and self.state.has_valid_data:
                        command = {"move": "W", "weight": 0.5}
                    else:
                        command = self.last_command
                    self.shared_key_value.set_key_value(command)
                    logging.warning(f"Using fallback command: {command}")
                    print(f"Using fallback command: {command}")
                time.sleep(0.1)
            except Exception as e:
                logging.error(f"Error in Ground.run: {e}")
                print(f"Error in Ground.run: {e}")
                time.sleep(1.0)