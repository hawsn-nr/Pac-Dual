import random

class NPCGhost:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 15
        self.speed = 1.5
        self.dx = 0
        self.dy = -self.speed

    def get_pos(self):
        return (self.x, self.y)

    def move(self):
        self.x += self.dx
        self.y += self.dy