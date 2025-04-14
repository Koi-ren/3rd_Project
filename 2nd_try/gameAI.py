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

    def __truediv__(self, scalar):
        return Vector(self.x / scalar, self.y / scalar)

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

    def update(self, steering, maxSpeed, time, map_bounds=(0, 30, 0, 30)):
        if steering is None:
            self.velocity = Vector(0, 0)
            self.rotation = 0
            return

        self.velocity = self.velocity + (steering.linear * time)
        self.rotation += steering.angular * time

        if self.velocity.length() > maxSpeed:
            self.velocity.normalize()
            self.velocity *= maxSpeed

        # 위치 업데이트 전 경계 체크 (단위: coord, 1 coord = 10m)
        new_position = self.position + (self.velocity * time)
        min_x, max_x, min_z, max_z = map_bounds
        new_position.x = max(min_x, min(max_x, new_position.x))
        new_position.y = max(min_z, min(max_z, new_position.y))
        self.position = new_position

        self.orientation += self.rotation * time
        self.orientation = self.orientation % (2 * math.pi)

    def asVector(self):
        return Vector(math.cos(self.orientation), math.sin(self.orientation))

def newOrientation(current, velocity):
    if velocity.length() > 0:
        return math.atan2(velocity.y, velocity.x)
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

class Arrive(DynamicSteeringBehavior):
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
            print(f"Arrive: Within targetRadius ({distance:.2f} < {self.targetRadius}), stopping")
            return None

        # 목표 속도 계산
        if distance > self.slowRadius:
            targetSpeed = self.maxSpeed
        else:
            targetSpeed = self.maxSpeed * (distance / self.slowRadius)

        # 방향 벡터 정규화
        targetVelocity = direction
        if distance > 0:
            targetVelocity = targetVelocity * (targetSpeed / distance)

        # 선형 가속도 계산
        result.linear = (targetVelocity - self.character.velocity) / self.timeToTarget
        if result.linear.length() > self.maxAcceleration:
            result.linear.normalize()
            result.linear *= self.maxAcceleration

        result.angular = 0
        print(f"Arrive: distance={distance:.2f}, targetSpeed={targetSpeed:.2f}, linear={result.linear}")
        return result