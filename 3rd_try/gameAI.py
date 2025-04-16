import math
import logging

logging.basicConfig(
    filename='C:/Users/acorn/Desktop/project/3rd_Project/3rd_try/gameAI.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)

class Vector:
    def __init__(self, x, y):
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
        if mag == 0:
            return Vector(0, 0)
        return Vector(self.x / mag, self.y / mag)

class Kinematic:
    def __init__(self, position=None, orientation=0.0, velocity=None, rotation=0.0):
        self.position = position if position is not None else Vector(0, 0)
        self.orientation = orientation
        self.velocity = velocity if velocity is not None else Vector(0, 0)
        self.rotation = rotation

class Arrive:
    def __init__(self, diff_theta, distance, maxSpeed, targetRadius, slowRadius):
        self.diff_theta = diff_theta
        self.distance = distance
        self.maxSpeed = maxSpeed
        self.targetRadius = targetRadius
        self.slowRadius = slowRadius

    def getSteering(self):
        logging.debug(f"getSteering: diff_theta={self.diff_theta}")
        diff_theta_rad = math.radians(self.diff_theta)
        if abs(self.diff_theta) > 0.5:
            rotationSpeed = diff_theta_rad
            maxRotationSpeed = math.radians(90)
            rotationSpeed = max(min(rotationSpeed, maxRotationSpeed), -maxRotationSpeed)
            weight = abs(rotationSpeed) / maxRotationSpeed
            weight = max(0.1, min(1.0, weight))
            direction = "D" if self.diff_theta > 0 else "A"
            logging.debug(f"Steering calculated: direction={direction}, weight={weight}, rotationSpeed={rotationSpeed}")
            print(f"Steering calculated: direction={direction}, weight={weight}, rotationSpeed={rotationSpeed}")
            return direction, weight
        logging.debug("Steering: No rotation needed")
        return "NONE", 0

    def getSpeed(self):
        if self.distance < self.targetRadius:
            return 0
        if self.distance > self.slowRadius:
            return self.maxSpeed
        speed = self.maxSpeed * (self.distance / self.slowRadius)
        return speed