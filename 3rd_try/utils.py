import threading
import logging

# 로깅 설정
logging.basicConfig(
    filename='utils.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SharedData:
    def __init__(self):
        self.data = None
        self.lock = threading.Lock()

    def set_data(self, data):
        with self.lock:
            self.data = data
            logging.info(f"SharedData updated: time={data.get('time', 0.0)}")
            print(f"SharedData updated: time={data.get('time', 0.0)}")

    def get_data(self):
        with self.lock:
            logging.debug("SharedData accessed")
            return self.data

class SharedKeyValue:
    def __init__(self):
        self.value = None
        self.lock = threading.Lock()

    def set_key_value(self, key):
        with self.lock:
            self.value = key
            logging.info(f"SharedKeyValue updated: {self.value}")
            print(f"SharedKeyValue updated: {self.value}")

    def get_key_value(self):
        with self.lock:
            logging.debug("SharedKeyValue accessed")
            return self.value
    
class SharedGoalPosition:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.lock = threading.Lock()

    def set_goal_position(self, goal):
        with self.lock:
            self.x = goal["x"]
            self.y = goal["y"]
            self.z = goal["z"]
            logging.info(f"Goal position set: {goal}")
            print(f"Goal position set: {goal}")

    def get_goal_position(self):
        with self.lock:
            goal = {"x": self.x, "y": self.y, "z": self.z}
            logging.debug(f"Goal position accessed: {goal}")
            return goal

sharedData = SharedData()
sharedKeyValue = SharedKeyValue()
sharedGoalPosition = SharedGoalPosition()