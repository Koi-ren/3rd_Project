import threading

class SharedData:
    def __init__(self):
        self.data = None
        self.lock = threading.Lock()

    def set_data(self, data):
        with self.lock:
            self.data = data

    def get_data(self):
        with self.lock:
            return self.data

class SharedKeyValue:
    def __init__(self):
        self.value = None
        self.lock = threading.Lock()

    def set_key_value(self, key):
        with self.lock:
            self.value = key

    def get_key_value(self):
        with self.lock:
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

    def get_goal_position(self):
        with self.lock:
            return {"x": self.x, "y": self.y, "z": self.z}

sharedData = SharedData()
sharedKeyValue = SharedKeyValue()
sharedGoalPosition = SharedGoalPosition()