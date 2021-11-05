import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pygame
from pygame import constants
from pygame.constants import NOEVENT
import pygame_gui
from talktown.city.city import CityFactory
from talktown.city.layout import RoadType, Structure, Point
# from talktown.defaults.city_generation.linear_layout import LinearLayoutFactory
from talktown.defaults.city_generation.legacy_layout import LegacyLayoutFactory
from talktown.defaults.plugins.sample_theme import SAMPLE_THEME_PLUGIN
from talktown.simulation.simulation import Simulation

from asset_loader import FontAssetConfig, FontAssetLoader, ImageAssetConfig, ImageAssetLoader
from camera import Camera
from constants import SKY_BACKGROUND_COLOR, TILE_OFFSET_X, TILE_OFFSET_Y, COLOR_WHITE, TILE_SIZE
from ui import CharacterInfoWindow


def to_isometric(position: Tuple[int, int]) -> Tuple[int, int]:
    x, y = position
    return (x - y) * TILE_OFFSET_X, (x + y) * TILE_OFFSET_Y


def grid_to_world(
        grid_x: int,
        grid_y: int,
) -> Dict[str, Any]:
    """Convert grid position into a world position"""
    rect = [
        (grid_x * TILE_SIZE, grid_y * TILE_SIZE),
        (grid_x * TILE_SIZE + TILE_SIZE, grid_y * TILE_SIZE),
        (grid_x * TILE_SIZE + TILE_SIZE, grid_y * TILE_SIZE + TILE_SIZE),
        (grid_x * TILE_SIZE, grid_y * TILE_SIZE + TILE_SIZE),
    ]  # Four vertices of the grid element

    iso_poly = [
        cart_to_iso(x, y) for x, y in rect
    ]  # Vertices for isometric polygon

    min_x = min([x for x, _ in iso_poly])
    min_y = min([y for _, y in iso_poly])

    out = {
        "grid": (grid_x, grid_y),
        "cart_rect": rect,
        "iso_poly": iso_poly,
        "render_pos": (min_x, min_y)
    }

    return out


def cart_to_iso(x: int, y: int) -> Tuple[int, int]:
    iso_x = x - y
    iso_y = int((x + y) / 2)
    return iso_x, iso_y


def mouse_to_grid(x: int, y: int, scroll: pygame.math.Vector2) -> Tuple[int, int]:
    world_x = x - scroll.x
    world_y = y - scroll.y
    # transform to cart (inverse of cart_to_iso)
    cart_y = (2 * world_y - world_x) / 2
    cart_x = cart_y + world_x
    # transform to grid coordinates
    grid_x = int(cart_x // TILE_SIZE)
    grid_y = int(cart_y // TILE_SIZE)
    return grid_x, grid_y


@dataclass
class GameConfig:
    width: int = 900
    height: int = 500
    fps: int = 60


class Game:
    """Game instance for CityViz"""

    def __init__(
            self,
            config: GameConfig,
            image_loader: 'ImageAssetLoader',
            font_loader: 'FontAssetLoader'
    ) -> None:
        self.config = config
        self.image_loader = image_loader
        self.font_loader = font_loader
        self.camera = Camera(config.width, config.height, 10)
        self.clock = pygame.time.Clock()
        self.running = True
        self.playing = False
        self.font = self.font_loader["fredoka"]
        # self.sim = Simulation(SAMPLE_THEME_PLUGIN, "Line Town",
        #                       CityFactory(LinearLayoutFactory(5)))
        self.sim = Simulation(SAMPLE_THEME_PLUGIN, "Squaresville",
                              CityFactory(LegacyLayoutFactory()))
        self.sim_running = False
        self.selected_tile: Optional[pygame.math.Vector2] = None
        self.selected_building: Optional[str] = None

        self.display = pygame.Surface((config.width, config.height))
        self.window = pygame.display.set_mode((config.width, config.height))
        pygame.display.set_caption("CityViz")
        self.background = pygame.Surface((config.width, config.height))
        self.background.fill(SKY_BACKGROUND_COLOR)
        self.ui_manager = pygame_gui.UIManager((config.width, config.height))
        self.ui_elements = {
            'step-btn': pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (100, 50)),
                text='Step',
                manager=self.ui_manager
            ),
            'play-btn': pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((100, 0), (100, 50)),
                text='Play',
                manager=self.ui_manager
            ),
            'pause-btn': pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((200, 0), (100, 50)),
                text='Pause',
                manager=self.ui_manager
            )
        }
        self.open_windows: Dict[str, pygame_gui.elements.UIWindow] = {}

        self.button_down = {
            "left": False,
            "right": False,
            "up": False,
            "down": False
        }

        self.image_loader.load()
        self.font_loader.load()

    def update(self, time_delta: float) -> None:
        camera_delta = pygame.Vector2(0, 0)
        if self.button_down["up"]:
            camera_delta += pygame.Vector2(0, 1)
        if self.button_down["left"]:
            camera_delta += pygame.Vector2(1, 0)
        if self.button_down["down"]:
            camera_delta += pygame.Vector2(0, -1)
        if self.button_down["right"]:
            camera_delta += pygame.Vector2(-1, 0)
        self.camera.update(camera_delta)

        self.ui_manager.update(time_delta)

        if self.sim_running:
            self.sim.simulate()

    def _is_mouse_in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.sim.city.layout.shape[0] \
            and 0 <= y < self.sim.city.layout.shape[1]

    def _draw_ground(self) -> None:
        # Draw the ground
        rows, cols = self.sim.city.layout.shape
        for x in range(rows):
            for y in range(cols):
                pos_info = grid_to_world(x, y)
                render_pos = pos_info["render_pos"]

                self.display.blit(
                    self.image_loader["grass"],
                    (render_pos[0] + self.camera.scroll.x, render_pos[1] + self.camera.scroll.y))

    def _draw_roads(self) -> None:
        rows, cols = self.sim.city.layout.shape
        for x in range(rows):
            for y in range(cols):
                render_pos = grid_to_world(x, y)["render_pos"]
                road_type = self.sim.city.layout.road_grid[x, y]
                if road_type != RoadType.EMPTY:
                    image_tile_name = "road_ns"
                    if road_type == RoadType.FOUR_WAY:
                        image_tile_name = "road_4way"
                    elif road_type == RoadType.STRAIGHT_EW:
                        image_tile_name = "road_ew"
                    elif road_type == RoadType.THREE_WAY_E:
                        image_tile_name = "road_3way_NES"
                    elif road_type == RoadType.THREE_WAY_S:
                        image_tile_name = "road_3way_ESW"
                    elif road_type == RoadType.THREE_WAY_W:
                        image_tile_name = "road_3way_NSW"
                    elif road_type == RoadType.THREE_WAY_N:
                        image_tile_name = "road_3way_NEW"
                    elif road_type == RoadType.CURVE_ES:
                        image_tile_name = "road_curve_ES"
                    elif road_type == RoadType.CURVE_NE:
                        image_tile_name = "road_curve_NE"
                    elif road_type == RoadType.CURVE_NW:
                        image_tile_name = "road_curve_NW"
                    elif road_type == RoadType.CURVE_SW:
                        image_tile_name = "road_curve_SW"

                    self.display.blit(
                        self.image_loader[image_tile_name],
                        (render_pos[0] + self.camera.scroll.x, render_pos[1] + self.camera.scroll.y))

    def _draw_buildings(self) -> None:
        rows, cols = self.sim.city.layout.shape
        for x in range(rows):
            for y in range(cols):
                lot = self.sim.city.layout.lot_grid[x, y]
                if lot and lot.building:
                    building_style = self.sim.buildings[lot.building].style
                    building_img = self.image_loader[building_style]
                    render_pos = grid_to_world(x, y)["render_pos"]
                    self.display.blit(
                        building_img,
                        (render_pos[0] + self.camera.scroll.x,
                         render_pos[1] + self.camera.scroll.y - building_img.get_height() + TILE_SIZE))

    def _draw_hover_tile(self) -> None:
        if self.selected_tile is not None:
            poly = grid_to_world(int(self.selected_tile.x), int(
                self.selected_tile.y))['iso_poly']
            poly = [(x + self.camera.scroll.x, y + self.camera.scroll.y)
                    for x, y in poly]
            pygame.draw.polygon(self.display, (255, 255, 255), poly, 3)

    def _draw_fps(self) -> None:
        self.draw_text(f"FPS: {round(self.clock.get_fps())}", 18,
                       self.config.width - 50,
                       10)

    def _draw_ui(self) -> None:
        self.ui_manager.draw_ui(self.display)

    def draw(self) -> None:
        self.display.blit(self.background, (0, 0))

        self._draw_ground()
        self._draw_roads()
        self._draw_hover_tile()
        self._draw_buildings()
        self._draw_fps()
        self._draw_ui()

        self.window.blit(self.display, (0, 0))

        pygame.display.update()

    def run(self) -> None:
        while self.playing:
            self.handle_events()
            while self.running:
                time_delta = self.clock.tick(self.config.fps) / 1000.0
                self.handle_events()
                self.update(time_delta)
                self.draw()

    def handle_events(self):
        mouse_screen_x, mouse_screen_y = pygame.mouse.get_pos()
        mouse_grid_x, mouse_grid_y = mouse_to_grid(
            mouse_screen_x, mouse_screen_y, self.camera.scroll)
        if self._is_mouse_in_bounds(mouse_grid_x, mouse_grid_y):
            self.selected_tile = pygame.math.Vector2(
                mouse_grid_x, mouse_grid_y)
        else:
            self.selected_tile = None

        for event in pygame.event.get():
            self.ui_manager.process_events(event)

            if event.type == pygame.QUIT:
                self.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    self.playing = False
                    self.quit()
                if event.key == pygame.K_w:
                    self.button_down["up"] = True
                if event.key == pygame.K_a:
                    self.button_down["left"] = True
                if event.key == pygame.K_s:
                    self.button_down["down"] = True
                if event.key == pygame.K_d:
                    self.button_down["right"] = True
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_w:
                    self.button_down["up"] = False
                if event.key == pygame.K_a:
                    self.button_down["left"] = False
                if event.key == pygame.K_s:
                    self.button_down["down"] = False
                if event.key == pygame.K_d:
                    self.button_down["right"] = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                #     self.ui_manager.get_window_stack().get_stack(
                #     )[0].check_clicked_inside_or_blocking(event)
                focus_set = self.ui_manager.get_focus_set()
                if focus_set and self.ui_manager.get_root_container() not in focus_set:
                    continue

                if self.selected_tile is not None:
                    lot = self.sim.city.layout.lot_grid[int(
                        self.selected_tile.x), int(self.selected_tile.y)]

                    if lot and lot.building:
                        self.selected_building = lot.building
                        building = self.sim.buildings[self.selected_building]
                        residences = [self.sim.residences[residence_id]
                                      for residence_id in building.housing_units]
                        for r in residences:
                            for character_id in r.residents:
                                character = self.sim.characters[character_id]

                                if character_id in self.open_windows:
                                    self.ui_manager.get_window_stack().move_window_to_front(
                                        self.open_windows[character_id])
                                else:
                                    self.open_windows[character_id] = CharacterInfoWindow(
                                        character, (50, 50), self.ui_manager)

            if event.type == pygame.USEREVENT and event.user_type == pygame_gui.UI_WINDOW_CLOSE:
                del self.open_windows[event.ui_object_id]

            if event.type == pygame.USEREVENT:
                # if event.user_type == pygame_gui.
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.ui_elements['step-btn']:
                        self.sim.simulate()
                    if event.ui_element == self.ui_elements['play-btn']:
                        self.sim_running = True
                    if event.ui_element == self.ui_elements['pause-btn']:
                        self.sim_running = False
                    continue

    def reset_buttons(self) -> None:
        self.button_down["up"] = False
        self.button_down["left"] = False
        self.button_down["down"] = False
        self.button_down["right"] = False

    def draw_text(
            self,
            text: str,
            size: int,
            x: int,
            y: int,
            color: Tuple[int, int, int] = COLOR_WHITE
    ) -> None:
        font = pygame.font.Font(self.font, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        self.display.blit(text_surface, text_rect)

    def quit(self):
        pygame.quit()
        sys.exit()


def main():
    """main function"""
    pygame.init()
    pygame.mixer.init()

    assets_dir = Path(os.path.abspath(__file__)).parent / 'assets'

    game_config = GameConfig(900, 500, 60)

    image_asset_loader = ImageAssetLoader([
        ImageAssetConfig("ground", str(
            assets_dir / 'graphics' / 'exports' / 'ground_cube.png')),
        ImageAssetConfig("building", str(
            assets_dir / 'graphics' / 'exports' / 'building.png')),
        ImageAssetConfig("Restaurant", str(
            assets_dir / 'graphics' / 'exports' / 'restaurant.png')),
        ImageAssetConfig("Bar", str(
            assets_dir / 'graphics' / 'exports' / 'bar.png')),
        ImageAssetConfig("house", str(
            assets_dir / 'graphics' / 'exports' / 'house.png')),
        ImageAssetConfig("road_ew", str(
            assets_dir / 'graphics' / 'exports' / 'road_EW.png')),
        ImageAssetConfig("road_ns", str(
            assets_dir / 'graphics' / 'exports' / 'road_NS.png')),
        ImageAssetConfig("road_curve_ES", str(
            assets_dir / 'graphics' / 'exports' / 'road_curve_ES.png')),
        ImageAssetConfig("road_curve_NE", str(
            assets_dir / 'graphics' / 'exports' / 'road_curve_NE.png')),
        ImageAssetConfig("road_curve_NW", str(
            assets_dir / 'graphics' / 'exports' / 'road_curve_NW.png')),
        ImageAssetConfig("road_curve_SW", str(
            assets_dir / 'graphics' / 'exports' / 'road_curve_SW.png')),
        ImageAssetConfig("road_3way_ESW", str(
            assets_dir / 'graphics' / 'exports' / 'road_3way_ESW.png')),
        ImageAssetConfig("road_3way_NES", str(
            assets_dir / 'graphics' / 'exports' / 'road_3way_NES.png')),
        ImageAssetConfig("road_3way_NEW", str(
            assets_dir / 'graphics' / 'exports' / 'road_3way_NEW.png')),
        ImageAssetConfig("road_3way_NSW", str(
            assets_dir / 'graphics' / 'exports' / 'road_3way_NSW.png')),
        ImageAssetConfig("road_4way", str(
            assets_dir / 'graphics' / 'exports' / 'road_4way.png')),
        ImageAssetConfig("grass", str(
            assets_dir / 'graphics' / 'exports' / 'grass_tile.png')),
    ])

    font_loader = FontAssetLoader([
        FontAssetConfig("fredoka", str(
            assets_dir / 'fonts' / 'FredokaOne-Regular.ttf'))
    ])

    game = Game(config=game_config, image_loader=image_asset_loader,
                font_loader=font_loader)

    game.playing = True
    game.run()


if __name__ == "__main__":
    main()
