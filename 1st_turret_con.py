import math

class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other): return Vector(self.x + other.x, self.y + other.y)
    def __sub__(self, other): return Vector(self.x - other.x, self.y - other.y)
    def __mul__(self, scalar): return Vector(self.x * scalar, self.y * scalar)
    def magnitude(self): return math.sqrt(self.x**2 + self.y**2)

    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            return Vector(0, 0)
        return Vector(self.x / mag, self.y / mag)

class Initialize:
    EFFECTIVE_RANGE = 115.8  # Unit: meters
    BULLET_VELOCITY = 42.6  # Unit: meters/second
    GRAVITATIONAL_ACCELERATION = 9.81  # Unit: meters/second^2

    def __init__(self, data=None):
        if data is None:
            data = {
                "enemyPos": {"x": 0, "y": 0, "z": 0},
                "playerPos": {"x": 0, "y": 0, "z": 0},
                "distance": 115,
                "enemySpeed": 0,
                "playerSpeed": 0,
                "time": 0,
                "enemyBodyX": 0,
                "playerBodyX": 0,
                "playerTurretY":0
            }
        self.shared_data = data
        self.tolerance = 3.5  # Unit: degrees; will be dynamically assigned later
        self.input_key_value = {
            "getRight": "E", "getLeft": "Q",
            "getRise": "R", "getFall": "F", "getShot": "FIRE"
        }

class Ballistics:
    def __init__(self, context):
        self.context = context

    def _calculation_of_barrel_angle_by_distance(self):
        if self.context.shared_data["distance"] <= self.context.EFFECTIVE_RANGE:
            delta_H = abs(self.context.shared_data["enemyPos"]["y"] - self.context.shared_data["playerPos"]["y"])
            predict_time = self.context.shared_data["distance"] / self.context.BULLET_VELOCITY
            barrel_angle = (math.atan(delta_H / self.context.shared_data["distance"]) +
                            (0.5 * self.context.GRAVITATIONAL_ACCELERATION * predict_time**2) /
                            self.context.BULLET_VELOCITY)
            barrel_angle_error = self.context.shared_data["playerTurretY"] - 
            return barrel_angle, barrel_angle_error
        else:
            return ValueError("Distance exceeds effective range")

class AimingBehavior:
    def __init__(self, context):
        self.context = context
        self.ballistics = Ballistics(context)

    def _calculate_turret_angle(self):
        goal_vector = Vector(
            self.context.shared_data["enemyPos"]["x"] - self.context.shared_data["playerPos"]["x"],
            self.context.shared_data["enemyPos"]["z"] - self.context.shared_data["playerPos"]["z"]
        )
        goal_vector = goal_vector.normalize()

        goal_heading = math.atan2(goal_vector.y, goal_vector.x) - math.pi / 2
        player_heading_to_radians = self.context.shared_data["playerBodyX"] * math.pi / 180
        heading_error = goal_heading - player_heading_to_radians
        heading_error = math.atan2(math.sin(heading_error), math.cos(heading_error))

        return goal_vector, heading_error

    def control_information(self):
        goal_vector, heading_error = self._calculate_turret_angle()
        barrel_angle, barrel_angle_error = self.ballistics._calculation_of_barrel_angle_by_distance()
        return goal_vector, heading_error, barrel_angle, barrel_angle_error

class TurretControl:
    def __init__(self, context):
        self.context = context
        self.previous_playTime = 0
        self.aimingBehavior = AimingBehavior(context)
        self.target_vector, self.heading_error, self.barrel_angle = self.aimingBehavior.control_information()

    def normal_control(self):
        if self.previous_playTime <= self.context.shared_data["time"]:
            self.target_vector, self.heading_error, self.barrel_angle, self.barrel_angle_error = self.aimingBehavior.control_information()
            turret_weight = min(max(abs(self.heading_error) / math.pi, 0.5), 1)
            barrel_weight = min(max(abs(self.barrel_angle_error) / math.pi, 0.5), 1)
            if abs(self.heading_error) > math.radians(self.context.tolerance):
                direction = "getRight" if self.heading_error > 0 else "getLeft"
                return self.context.input_key_value[direction], turret_weight
            elif abs(self.heading_error) <= math.radians(self.context.tolerance) and self.context.shared_data["distance"] <= self.context.EFFECTIVE_RANGE:
                return self.context.input_key_value["getShot"]
            self.previous_playTime = self.context.shared_data["time"]
        return None

if __name__ == "__main__":
    context = Initialize()
    turret = TurretControl(context)
    print(id(context.shared_data) == id(turret.context.shared_data))
    result = turret.normal_control()
    print(result)