class Pacman:
    def __init__(self, player_id, start_pos):
        self.id = player_id
        self.x, self.y = start_pos
        self.radius = 15
        self.dx = 0
        self.dy = 0
        self.speed = 4

    def set_direction(self, direction):
        if direction == "Left": self.dx, self.dy = -self.speed, 0
        elif direction == "Right": self.dx, self.dy = self.speed, 0
        elif direction == "Up": self.dx, self.dy = 0, -self.speed
        elif direction == "Down": self.dx, self.dy = 0, self.speed
        elif direction == "Stop": self.dx, self.dy = 0, 0
            
    def get_pos(self):
        return (self.x, self.y)

    def update_local_pos(self, width, height):
        self.x = max(self.radius, min(width - self.radius, self.x + self.dx))
        self.y = max(self.radius, min(height - self.radius, self.y + self.dy))