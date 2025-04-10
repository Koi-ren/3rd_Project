# utills.py
class SharedData:
    def __init__(self):
        self.latest_data = None

    def set_data(self, data):
        self.latest_data = data

    def get_data(self):
        return self.latest_data

class SharedKeyValue:
    def __init__(self):
        self.key_value = None

    def set_key_value(self, key_value):
        self.key_value = key_value

    def get_key_value(self):
        return self.key_value

sharedData = SharedData()
sharedKeyValue = SharedKeyValue()

