class Pedestrian:
    def __init__(self, name, speed, location):
        self.name = name
        self.speed = speed
        self.current_location = location
        self.in_space = True
        self.location_history = []

    def move(self, new_location):
        self.location_history.append(self.current_location)
        self.current_location = new_location
