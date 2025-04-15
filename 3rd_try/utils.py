# utills.py
class SharedData:
    def __init__(self):
        self.data = None

    def set_data(self, data):
        self.data = data

    def get_data(self):
        return self.data

class SharedKeyValue:
    def __init__(self):
        self.value = None

    def set_key_value(self, key):
        self.value = key

    def get_key_value(self):
        return self.value
    
class SharedGoalPosition:
    def __init__(self):
        self.x = None
        self.y = None
        self.z = None

    def set_goal_position(self, goal):
        self.x = goal["x"]
        self.y = goal["y"]
        self.z = goal["z"]

    def get_goal_position(self):
        return self


sharedData = SharedData()
sharedKeyValue = SharedKeyValue()
sharedGoalPosition = SharedGoalPosition()