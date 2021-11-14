from typing import Tuple, TypedDict

import pygame

from cityviz.constants import COLOR_WHITE


def draw_text(
    display: pygame.Surface,
    text: str,
    x: int,
    y: int,
    font: pygame.font.Font,
    color: Tuple[int, int, int] = COLOR_WHITE,
) -> None:
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    display.blit(text_surface, text_rect)


def to_isometric(position: Tuple[int, int], tile_size: int = 64) -> Tuple[int, int]:
    """Take screen (X,Y) coordinates and translate them into Isometric space

    Args:
        position: (Tuple[int, int]) - position in top-down cartesian space
        tile_size: (int) - size (length & width) of square world tile in cartesian space

    Returns
        Tuple[int, int] - position of the given point in isometric space
    """
    x, y = position
    return round((x - y) * tile_size), round((x + y) * tile_size * 0.5)


class GridToWorldResult(TypedDict):
    grid: Tuple[int, int]
    cart_rect: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]
    iso_poly: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]
    render_pos: Tuple[int, int]


def grid_to_world(
        position: Tuple[int, int],
        tile_size: int = 64
) -> GridToWorldResult:
    """Convert grid position into a world position"""
    grid_x, grid_y = position

    # Four vertices of the grid element
    rect = (
        # top-left
        (grid_x * tile_size, grid_y * tile_size),
        # top-right
        (grid_x * tile_size + tile_size, grid_y * tile_size),
        # bottom-right
        (grid_x * tile_size + tile_size, grid_y * tile_size + tile_size),
        # bottom-left
        (grid_x * tile_size, grid_y * tile_size + tile_size),
    )

    # Vertices for isometric polygon
    iso_poly = (
        # top-left
        to_isometric((grid_x, grid_y), tile_size),
        # top-right
        to_isometric((grid_x + 1, grid_y), tile_size),
        # bottom-right
        to_isometric((grid_x + 1, grid_y + 1), tile_size),
        # bottom-left
        to_isometric((grid_x, grid_y + 1), tile_size),
    )

    min_x = min([x for x, _ in iso_poly])
    min_y = min([y for _, y in iso_poly])

    out: GridToWorldResult = {
        "grid": (grid_x, grid_y),
        "cart_rect": rect,
        "iso_poly": iso_poly,
        "render_pos": (min_x, min_y)
    }

    return out


def mouse_to_grid(x: int, y: int, scroll: pygame.math.Vector2, tile_size: int = 64) -> Tuple[int, int]:
    world_x = x - scroll.x
    world_y = y - scroll.y
    # transform to cart (inverse of cart_to_iso)
    cart_y = (2 * world_y - world_x) / 2
    cart_x = cart_y + world_x
    # transform to grid coordinates
    grid_x = int(cart_x // tile_size)
    grid_y = int(cart_y // tile_size)
    return grid_x, grid_y
