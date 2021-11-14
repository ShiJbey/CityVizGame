import pygame.math as pg_math


class Camera:

    def __init__(self, width: int, height: int, speed: int = 3) -> None:
        self.width = width
        self.height = height
        self.scroll = pg_math.Vector2(0, 0)
        self.speed = speed

    def update(self, delta: pg_math.Vector2) -> None:
        self.scroll += (delta * self.speed)
