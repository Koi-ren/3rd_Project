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
        return math.atan2(velocity.x, velocity.y)  # x축 기준 라디안
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

# 운동학적 스티어링 동작의 기본 클래스
class KinematicSteeringBehavior:
    def __init__(self, character, maxSpeed):
        self.character = character
        self.maxSpeed = maxSpeed

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

class KinematicSteeringOutput:
    def __init__(self):
        self.velocity = (0, 0)
        self.rotation = 0

# 도착 행동 (KinematicArrive)
class KinematicArrive(KinematicSteeringBehavior):
    def __init__(self, character, target, maxSpeed, radius, timeToTarget=0.25):
        super().__init__(character, maxSpeed)
        self.target = target
        self.radius = radius
        self.timeToTarget = timeToTarget

    def getSteering(self):
        result = KinematicSteeringOutput()
        result.velocity = self.target.position - self.character.position
        if result.velocity.length() < self.radius:
            return None
        result.velocity = result.velocity * (1 / self.timeToTarget)
        if result.velocity.length() > self.maxSpeed:
            result.velocity.normalize()
            result.velocity = result.velocity * self.maxSpeed
        self.character.orientation = newOrientation(self.character.orientation, result.velocity)
        result.rotation = 0
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

        if distance > self.slowRadius:
            direction.normalize()
            result.linear = direction * self.maxAcceleration
        else:
            if distance < self.targetRadius:
                return None
            targetSpeed = self.maxSpeed * distance / self.slowRadius
            targetVelocity = direction
            targetVelocity.normalize()
            targetVelocity = targetVelocity * targetSpeed
            result.linear = targetVelocity - self.character.velocity
            result.linear = result.linear * (1 / self.timeToTarget)
            if result.linear.length() > self.maxAcceleration:
                result.linear.normalize()
                result.linear = result.linear * self.maxAcceleration

        # 방향 업데이트 (x축 기준)
        targetVelocity = direction
        targetVelocity.normalize()
        targetVelocity = targetVelocity * (self.maxSpeed if distance > self.slowRadius else targetSpeed)
        self.character.orientation = newOrientation(self.character.orientation, targetVelocity)

        result.angular = 0
        return result

if __name__ == "__main__":
    # 플레이어와 적 위치 설정 (x, z 사용)
    player_pos = Vector(59.35, 27.23)  # 플레이어 x, z
    enemy_pos = Vector(135.46, 276.87)  # 적 x, z

    # Kinematic 객체 생성
    character = Kinematic(position=player_pos, orientation=0.0)
    target = Kinematic(position=enemy_pos, orientation=0.0)

    # SeekAndArrive 설정
    seek_arrive = SeekAndArrive(
        character=character,
        target=target,
        maxAcceleration=1.0,    # 가속도 (조정 가능)
        maxSpeed=5.0,           # 최대 속도 (상황에 맞게 조정)
        targetRadius=5.0,       # 목표 도착 반경 (거리 단위에 맞춤)
        slowRadius=50.0,        # 감속 시작 반경 (거리 단위에 맞춤)
        timeToTarget=0.1        # 목표 도달 시간
    )

    print("SeekAndArrive 행동 시뮬레이션 (0.1초 단위, x축 기준 헤딩):")
    time_step = 0.1
    total_time = 58.5  # 주어진 시간에서 시작

    while True:
        steering = seek_arrive.getSteering()
        if steering is None:
            print(f"시간: {total_time:.1f}초 - 목표에 도달함!")
            print(f"최종 위치: {character.position}, 속도: {character.velocity}, 헤딩: {character.orientation:.2f} 라디안")
            break

        character.update(steering, maxSpeed=5.0, time=time_step)
        total_time += time_step
        print(f"시간: {total_time:.1f}초 - 위치: {character.position}, 속도: {character.velocity}, 헤딩: {character.orientation:.2f} 라디안")