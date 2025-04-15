import math

class Vector:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
    
    def length(self): 
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self):
        length = self.length()
        if length > 0:
            self.x /= length
            self.y /= length
        return self
    
class Kinematic:
    def __init__(self, position=Vector(), velocity=Vector(), orientation=0.0):
        self.position = position
        self.velocity = velocity
        self.orientation = orientation

class Arrive:
    def __init__(self, diff_theta, distance, maxSpeed, targetRadius, slowRadius):
        self.diff_theta = diff_theta
        self.distance = distance
        self.maxSpeed = maxSpeed
        self.targetRadius = targetRadius
        self.slowRadius = slowRadius
      
    def getSpeed(self):
        if self.distance < self.targetRadius:
            return 0.0
        if self.distance > self.slowRadius:
            return self.maxSpeed
        # 선형 감속
        return self.maxSpeed * (self.distance - self.targetRadius) / (self.slowRadius - self.targetRadius)
    
    def getSteering(self):
        abs_diff = abs(self.diff_theta)
        if abs_diff < 5:  # 작은 각도는 회전 불필요
            return None, 0.0
        # 각도 차이에 비례한 회전 속도
        targetRotationSpeed = min(1.0, abs_diff / 90.0)
        RotationKey = "d" if self.diff_theta > 0 else "a"
        return RotationKey, targetRotationSpeed