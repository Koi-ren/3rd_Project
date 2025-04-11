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

sharedData = SharedData()
sharedKeyValue = SharedKeyValue()