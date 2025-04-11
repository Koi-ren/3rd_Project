# gameAI.py
import math

class Vector:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)

    def length(self):
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self):
        length = self.length()
        if length > 0:
            self.x /= length
            self.y /= length
        return self

    def __str__(self):
        return f"Vector({self.x:.2f}, {self.y:.2f})"

class Kinematic:
    def __init__(self, position=Vector(), orientation=0.0, velocity=Vector(), rotation=0.0):
        self.position = position
        self.orientation = orientation
        self.velocity = velocity
        self.rotation = rotation

    def update(self, steering, maxSpeed, time):
        self.velocity = self.velocity + (steering.linear * time)
        self.rotation += steering.angular * time

        if self.velocity.length() > maxSpeed:
            self.velocity.normalize()
            self.velocity *= maxSpeed

        self.position = self.position + (self.velocity * time)
        self.orientation += self.rotation * time

    def asVector(self):
        return Vector(math.cos(self.orientation), math.sin(self.orientation))

def newOrientation(current, velocity):
    if velocity.length() > 0:
        return math.atan2(velocity.x, velocity.y)
    return current

class SteeringOutput:
    def __init__(self, linear=Vector(), angular=0.0):
        self.linear = linear
        self.angular = angular

class DynamicSteeringBehavior:
    def __init__(self, character, maxAcceleration):
        self.character = character
        self.maxAcceleration = maxAcceleration

    def getSteering(self):
        raise NotImplementedError("서브클래스는 getSteering을 구현해야 합니다.")

class Seek(DynamicSteeringBehavior):
    def __init__(self, character, target, maxAcceleration):
        super().__init__(character, maxAcceleration)
        self.target = target

    def getSteering(self):
        result = SteeringOutput()
        direction = self.target.position - self.character.position
        direction.normalize()
        result.linear = direction * self.maxAcceleration
        result.angular = 0
        return result

class SeekAndArrive(DynamicSteeringBehavior):
    def __init__(self, character, target, maxAcceleration, maxSpeed, targetRadius, slowRadius, timeToTarget=0.1):
        super().__init__(character, maxAcceleration)
        self.target = target
        self.maxSpeed = maxSpeed
        self.targetRadius = targetRadius
        self.slowRadius = slowRadius
        self.timeToTarget = timeToTarget

    def getSteering(self):
        result = SteeringOutput()
        direction = self.target.position - self.character.position
        distance = direction.length()

        if distance < self.targetRadius:
            return None

        targetSpeed = self.maxSpeed
        if distance <= self.slowRadius:
            targetSpeed = self.maxSpeed * distance / self.slowRadius

        targetVelocity = direction
        targetVelocity.normalize()
        targetVelocity *= targetSpeed

        result.linear = targetVelocity
        result.angular = 0

        return result