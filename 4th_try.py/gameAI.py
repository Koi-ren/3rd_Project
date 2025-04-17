import math

class Vector:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)

    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self):
        mag = self.magnitude()
        if mag != 0:
            self.x /= mag
            self.y /= mag
        return self

class Kinematic:
    def __init__(self, position=Vector(0, 0), orientation=0, velocity=Vector(0, 0), rotation=0):
        self.position = position
        self.orientation = orientation
        self.velocity = velocity
        self.rotation = rotation

class Arrive:
    def __init__(self, diff_theta=0, distance=0, maxSpeed=10, targetRadius=5, slowRadius=50):
        self.diff_theta = diff_theta
        self.distance = distance
        self.maxSpeed = maxSpeed
        self.targetRadius = targetRadius
        self.slowRadius = slowRadius
        self.maxRotationSpeed = math.radians(56.2)
        self.timeToTarget = 0.1

    def getSteering(self):
        if abs(self.diff_theta) > 1:
            weight = min(max(abs(self.diff_theta) / 180, 0.3), 1.0)
            rotationSpeed = min(self.maxRotationSpeed * weight, self.maxRotationSpeed)
            if self.diff_theta > 0:
                return "D", weight
            else:
                return "A", weight
        return "NONE", 0

    def getSpeed(self):
        if self.distance < self.targetRadius:
            targetSpeed = 0
        elif self.distance < self.slowRadius * 0.5:
            targetSpeed = self.maxSpeed * self.distance / (self.slowRadius * 0.5)
        else:
            targetSpeed = self.maxSpeed
        return targetSpeed