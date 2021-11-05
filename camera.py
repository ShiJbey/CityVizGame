import pygame as pg
import pygame.math as pg_math


class Camera:

    def __init__(self, width: int, height: int, speed: int = 3) -> None:
        self.width = width
        self.height = height
        self.scroll = pg_math.Vector2(0, 0)
        self.speed = speed

    def update(self, delta: pg_math.Vector2) -> None:
        self.scroll += (delta * self.speed)


# class Camera:

#     def __init__(self, width: int, height: int) -> None:
#         self.camera = pygame.Rect(
#             int(width / 3),
#             int(height / 3),
#             width, height)
#         self.width = width
#         self.height = height

#     def apply(self, entity_rect: 'Rect') -> 'Rect':
#         return entity_rect.move(self.camera.topleft)

#     def update(self, target: 'Rect', speed: int = 2) -> None:
#         x = self.camera.x + (target.x * speed)
#         y = self.camera.y + (target.y * speed)
#         self.camera = pygame.Rect(x, y, self.width, self.height)
