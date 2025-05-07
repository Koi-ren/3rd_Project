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

class initialize:
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
                "playerBodyX": 0
            }
        self.shared_data = data
        self.toolence = 3.5  # (degree)
        self.effectiveRange = 115.8  # (m)
        self.bulletVelocity = 42.6  # (m/s)
        self.inputKeyVelue = {
            "getRight": "E", "getLeft": "Q",
            "getRise": "R", "getFall": "F", "getShot": "FIRE"
        }
        self.gravitationalAcceleration = 9.81  # (m/s^2)

class ballistics:
    def __init__(self, context):
        self.context = context

    def _Calculation_of_BarrelAngle_by_Distance(self):
        if self.context.shared_data["distance"] <= self.context.effectiveRange:
            delta_H = abs(self.context.shared_data["enemyPos"]["y"] - self.context.shared_data["playerPos"]["y"])
            predict_time = self.context.shared_data["distance"] / self.context.bulletVelocity
            barrel_angle = math.atan(delta_H / self.context.shared_data["distance"]) + \
                           (0.5 * self.context.gravitationalAcceleration * predict_time**2) / self.context.bulletVelocity
            return barrel_angle
        else:
            return "사거리 초과"

class AimingBehavior:
    def __init__(self, context):
        self.context = context
        self.ballistics = ballistics(context)

    def _Calculate_Turret_Angle(self):
        goal_vector = Vector(
            self.context.shared_data["enemyPos"]["x"] - self.context.shared_data["playerPos"]["x"],
            self.context.shared_data["enemyPos"]["z"] - self.context.shared_data["playerPos"]["z"]
        )
        goal_vector = goal_vector.normalize()

        goal_heading = math.atan2(goal_vector.y, goal_vector.x)
        playerHeading_to_radians = self.context.shared_data["playerBodyX"] * math.pi / 180
        heading_error = goal_heading - playerHeading_to_radians
        heading_error = math.atan2(math.sin(heading_error), math.cos(heading_error))

        return goal_vector, heading_error

    def Control_information(self):
        goal_vector, heading_error = self._Calculate_Turret_Angle()
        barrel_angle = self.ballistics._Calculation_of_BarrelAngle_by_Distance()
        return goal_vector, heading_error, barrel_angle

class Turret_Control:
    def __init__(self, context):
        self.context = context
        self.previous_playTime = 0
        self.aimingBehavior = AimingBehavior(context)
        self.target_vector, self.heading_error, self.barrel_angle = self.aimingBehavior.Control_information()

    def normal_control(self):
        if self.previous_playTime <= self.context.shared_data["time"]:
            self.target_vector, self.heading_error, self.barrel_angle = self.aimingBehavior.Control_information()
            weight = min(max(abs(self.heading_error) / math.pi, 0.5), 1)
            if abs(self.heading_error) > math.radians(self.context.toolence):
                direction = "getRight" if self.heading_error > 0 else "getLeft"
                return self.context.inputKeyVelue[direction], weight
            elif abs(self.heading_error) <= math.radians(self.context.toolence) and self.context.shared_data["distance"] <= self.context.effectiveRange:
                
                return self.context.inputKeyVelue["getShot"]
            self.previous_playTime = self.context.shared_data["time"]
        return None

if __name__ == "__main__":
    context = initialize()
    turret = Turret_Control(context)
    print(id(context.shared_data) == id(turret.context.shared_data))
    result = turret.normal_control()
    print(result)