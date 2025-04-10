import math
import matplotlib.pyplot as plt

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

def simulate_and_visualize():
    # 초기 설정
    character = Kinematic(position=Vector(0, 0), orientation=0.0)
    target = Kinematic(position=Vector(5, 5), orientation=0.0)
    seek = Seek(character, target, maxAcceleration=1.0)
    maxSpeed = 2.0
    timeStep = 0.1  # 시간 간격
    radius = 0.1     # 도달 반경

    # 경로 저장 리스트
    path_x = [character.position.x]
    path_y = [character.position.y]

    # 시뮬레이션 루프
    while True:
        steering = seek.getSteering()
        character.update(steering, maxSpeed, timeStep)
        
        # 현재 위치 저장
        path_x.append(character.position.x)
        path_y.append(character.position.y)
        
        # 타겟과의 거리 확인
        distance = (target.position - character.position).length()
        if distance < radius:
            print(f"타겟에 도달했습니다! 최종 위치: {character.position}")
            break

        print(f"현재 위치: {character.position}, 속도: {character.velocity}, 방향: {character.orientation:.2f}")

    # 시각화
    plt.figure(figsize=(8, 8))
    plt.plot(path_x, path_y, 'b-', label='캐릭터 경로')  # 경로
    plt.plot(0, 0, 'go', label='시작점')               # 시작점 (녹색)
    plt.plot(5, 5, 'ro', label='타겟')                 # 타겟 (빨간색)
    plt.plot(path_x[-1], path_y[-1], 'bo', label='최종 위치')  # 최종 위치 (파란색)
    plt.grid(True)
    plt.legend()
    plt.title("캐릭터 이동 경로 (Seek 행동)")
    plt.xlabel("X 좌표")
    plt.ylabel("Y 좌표")
    plt.axis('equal')  # X, Y 축 비율 동일하게
    plt.savefig('character_path.png')
    print("경로 시각화가 'character_path.png' 파일로 저장되었습니다.")

if __name__ == "__main__":
    simulate_and_visualize()