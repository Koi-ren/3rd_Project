# server.py
import math
import requests
import time
import threading
from gameAI import Kinematic, Vector, Seek
from utills import sharedKeyValue

class GameState:
    """게임 데이터를 저장하고 관리하는 클래스"""
    def __init__(self):
        self.time_value = None
        self.distance = None
        self.key = None
        self.player_pos = {"x": 0, "y": 0, "z": 0}
        self.player_speed = 0.0
        self.player_health = 0.0
        self.player_turret_x = 0.0
        self.player_turret_y = 0.0
        self.player_body_x = 0.0
        self.player_body_y = 0.0
        self.enemy_pos = {"x": 0, "y": 0, "z": 0}
        self.enemy_speed = 0.0
        self.enemy_health = 0.0
        self.enemy_turret_x = 0.0
        self.enemy_turret_y = 0.0
        self.enemy_body_x = 0.0
        self.enemy_body_y = 0.0

    def updateData(self, data):
        """수신된 데이터를 기반으로 상태를 업데이트"""
        self.time_value = data["time"]
        self.distance = data["distance"]
        
        self.player_pos["x"] = data["playerPos"]["x"]
        self.player_pos["y"] = data["playerPos"]["y"]
        self.player_pos["z"] = data["playerPos"]["z"]
        self.player_speed = data["playerSpeed"]
        self.player_health = data["playerHealth"]
        self.player_turret_x = data["playerTurretX"]
        self.player_turret_y = data["playerTurretY"]
        self.player_body_x = data["playerBodyX"]
        self.player_body_y = data["playerBodyY"]
        
        self.enemy_pos["x"] = data["enemyPos"]["x"]
        self.enemy_pos["y"] = data["enemyPos"]["y"]
        self.enemy_pos["z"] = data["enemyPos"]["z"]
        self.enemy_speed = data["enemySpeed"]
        self.enemy_health = data["enemyHealth"]
        self.enemy_turret_x = data["enemyTurretX"]
        self.enemy_turret_y = data["enemyTurretY"]
        self.enemy_body_x = data["enemyBodyX"]
        self.enemy_body_y = data["enemyBodyY"]

    def updatekey(self, key):
        self.key = key

    def __str__(self):
        """상태를 문자열로 반환 (디버깅용)"""
        return (f"Time: {self.time_value}, Distance: {self.distance}, "
                f"Player Pos: ({self.player_pos['x']}, {self.player_pos['z']}), "
                f"Enemy Pos: ({self.enemy_pos['x']}, {self.enemy_pos['z']})")

class GameServer:
    """게임 서버 로직을 실행하는 클래스"""
    def __init__(self):
        self.state = GameState()
        # 캐릭터 초기 위치를 플레이어 위치로 설정하거나 (0, 0)으로 시작
        self.character = Kinematic(position=Vector(0, 0), orientation=0.0)
        # 타겟은 적 위치로 동적 업데이트 예정이므로 초기값은 임의 설정
        self.target = Kinematic(position=Vector(0, 0), orientation=0.0)
        self.seek = Seek(self.character, self.target, maxAcceleration=1.0)

    def fetch_data(self):
        """서버에서 데이터를 가져와 상태를 업데이트"""
        try:
            response_data = requests.get("http://localhost:5000/get_data")
            if response_data.status_code == 200:
                data = response_data.json()["data"]
                self.state.updateData(data)
                # 적 위치로 타겟 업데이트
                self.target.position = Vector(self.state.enemy_pos["x"], self.state.enemy_pos["z"])
                print("Data from server.py:", data)
                return True
            else:
                print("No data available in server.py yet.")
                return False
        except requests.exceptions.RequestException as e:
            print("Error fetching data:", e)
            return False

    def run(self):
        """메인 루프 실행"""
        while True:
            if self.fetch_data():
                # 상태 사용 예시
                print(self.state)

                # Seek 행동: 적 위치를 향해 이동
                steering = self.seek.getSteering()
                # 시간 간격을 현실적으로 조정 (예: 1초 대신 0.016초 = 60 FPS)
                self.character.update(steering, maxSpeed=2.0, time=0.016)
                print(f"Character Position: {self.character.position}, "
                      f"Velocity: {self.character.velocity}, "
                      f"Orientation: {self.character.orientation:.2f}")
            time.sleep(1)

if __name__ == "__main__":
    # GameServer 인스턴스 생성 및 실행
    server = GameServer()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    while True:
        character = Kinematic(position=Vector(server.state.player_pos["x"], 
                                              server.state.player_pos["z"]), orientation=server.state.player_body_x)
        target = Kinematic(position=Vector(server.state.enemy_pos["x"], 
                                              server.state.enemy_pos["z"]), orientation=server.state.enemy_body_x)