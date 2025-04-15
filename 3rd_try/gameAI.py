import math

class Vector:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
    
    def length(self): return math.sqrt(self.x**2 + self.y**2)

    def normalize(self):
        length = self.length()
        if length > 0:
            self.x /= length
            self.y /= length
        return self
    
class Kinematic:
    def __init__(self, position=Vector(), velocity=0.0, orientation=0.0):
        self.position = position
        self.velocity = velocity
        self.orientation = orientation

class Arrive:
    def __init__(self, diff_theta, distance, maxSpeed, targetRadius, slowRadius):
        self.diff_theta = diff_theta
        self.distance = distance
        self.maxSpeed=maxSpeed
        self.targetRadius = targetRadius
        self.slowRadius = slowRadius
      
    def getSpeed(self):
        if self.distance > self.slowRadius: return {"move": "W", "weight": 1}
        elif self.distance < self.slowRadius:
            slow_area = (self.distance - self.slowRadius)/10
            if slow_area <= 0.8: targetSpeed = 0.7
            elif slow_area <= 0.4: targetSpeed = 0.4
            elif slow_area <= 0.2: targetSpeed = 0.2
        elif self.distance < self.targetRadius: targetSpeed = 0
        return targetSpeed
    
    def getSteering(self):
        if math.sqrt(self.diff_theta**2) <= 180: targetRotationSpeed = 1
        elif math.sqrt(self.diff_theta**2): targetRotationSpeed = 0.5
        elif math.sqrt(self.diff_theta**2): targetRotationSpeed = 0.2
        if self.diff_theta < 0: RotationKey = "a"
        elif self.diff_theta > 0: RotationKey = "d"
        elif self.diff_theta == 0: RotationKey = None
        return RotationKey, targetRotationSpeed
