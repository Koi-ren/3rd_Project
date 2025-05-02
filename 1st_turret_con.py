import math
import numpy as np

class initialize:
    def __init__(self):
        data = {}

        self.enemyPos = data["enemyPos"]
        self.playerPos = data["playerPos"]
        self.distance = data["distance"]
        self.enemySpeed = data["enemySpeed"]
        self.playerSpeed = data["playerSpeed"]
        self.playTime = data["time"]
        self.toolence = 3.5 # (degree)
        self.effectiveRange = 115.8 # (m)
        self.bulletVelocity = 42.6 # (m/s)
        self.enemyHeading = data["enemyBodyX"]
        self.playerHeading = data["playerBodyX"]
        self.inputKeyVelue = {"getRight": "E", "getLeft": "Q",
                        "getRise": "R", "getFall": "F", "getShot": "FIRE"}
        self.gravitationalAcceleration = 9.81 # (m/s^2)

class ballistics(initialize):
    def __init__(self):
        super().__init__()

    def Calculation_of_BarrelAngle_by_Distance(self):
        if self.distance <= self.effectiveRange:
            delta_H = abs(self.enemyPos["y"] - self.playerPos["x"])
            predict_time = self.distance/self.bulletVelocity
            barrel_angle = math.atan(delta_H / self.distance ) 
            + (0.5 * self.gravitationalAcceleration * (predict_time)^2) / self.bulletVelocity
            # 여기서는 출력을 print()를 사용하지만 실제 적용 시 json 형식으로 리턴한다
            return barrel_angle
        else:
            return "사거리 초과"
    
    class aiming_Behavior(initialize):
        def __init__(self):
            super().__init__()
        
    def _calculate_steering(self):
        playerPos_x = self.playerPos["x"]
        playerPos_z = self.playerPos["z"]
        enemyPos_x = self.enemyPos["x"]
        enemyPos_y = self.enemyPos["z"]
        
        target_vector = np.array([self.enemyPos["x"] - self.playerPos["x"], self.enemyPos["z"] - self.playerPos["z"]])
        
        

        def nomal_control(self):
            
        