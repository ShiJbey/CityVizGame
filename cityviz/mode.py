from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict
import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UILabel, UIButton
from talktown.city.city import CityFactory
from talktown.city.layout import RoadType
from talktown.defaults.city_generation.legacy_layout import LegacyLayoutFactory
from talktown.defaults.plugins.sample_theme import SAMPLE_THEME_PLUGIN
from talktown.place import Building
from talktown.simulation.simulation import Simulation
from asset_loader import ImageAssetLoader

from camera import Camera
from constants import SKY_BLUE, TILE_SIZE
from utils import grid_to_world, mouse_to_grid


CHANGE_MODE_EVENT = pygame.event.custom_type()


class Mode(ABC):
    """Handles events and drawing to the screen when active"""

    mode_name: str

    __slots__ = 'active'

    def __init__(self, ui_manager: 'pygame_gui.UIManager', screen_size: Tuple[int, int]) -> None:
        self.active = False
        self.ui_manager = ui_manager
        self.screen_size = screen_size

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Update the state of the mode"""
        raise NotImplementedError()

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle PyGame events while active"""
        raise NotImplementedError()

    @abstractmethod
    def draw(self, display: 'pygame.Surface', image_loader: ImageAssetLoader) -> None:
        """Draw to the screen while active"""
        raise NotImplementedError()

    def deactivate(self):
        self.ui_manager.clear_and_reset()


class MainMenuMode(Mode):
    """Presents the user with the main menu"""

    mode_name = 'Main Menu'

    def __init__(self, ui_manager: 'pygame_gui.UIManager', screen_size: Tuple[int, int]) -> None:
        super().__init__(ui_manager, screen_size)
        self.options = ['New City', 'Load City', 'Quit']
        self.background = pygame.Surface(screen_size)
        self.background.fill(SKY_BLUE)

        # Create center panel
        panel_width = 300
        panel_height = 300

        panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        panel_rect.centerx = int(screen_size[0] / 2)
        panel_rect.centery = int(screen_size[1] / 2)
        panel = UIPanel(
            relative_rect=panel_rect,
            starting_layer_height=10,
            manager=ui_manager,
            anchors={'left': 'left',
                     'right': 'right',
                     'top': 'top',
                     'bottom': 'bottom'},
            object_id="#main_menu_panel")

        UILabel(pygame.Rect(0, 0, panel_width, 48),
                "CityViz",
                ui_manager,
                container=panel,
                parent_element=panel,
                object_id='#main_menu_title')

        btn_rect_0 = pygame.Rect(0, 60, panel_width, 48)
        btn_rect_0.centerx = int(panel_width / 2)
        UIButton(btn_rect_0,
                 "New City",
                 ui_manager,
                 container=panel,
                 parent_element=panel,
                 object_id='#new_city_btn')

        btn_rect_1 = pygame.Rect(0, 120, panel_width, 48)
        btn_rect_1.centerx = int(panel_width / 2)
        UIButton(btn_rect_1,
                 "Load City (WIP)",
                 ui_manager,
                 container=panel,
                 parent_element=panel,
                 object_id='#load_city_btn')

        btn_rect_2 = pygame.Rect(0, 180, panel_width, 48)
        btn_rect_2.centerx = int(panel_width / 2)
        UIButton(btn_rect_2,
                 "Exit Game",
                 ui_manager,
                 container=panel,
                 parent_element=panel,
                 object_id='#exit_game_btn')

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle PyGame events while active"""

        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_object_id == '#main_menu_panel.#new_city_btn':
                    print("Starting New City")
                    pygame.event.post(pygame.event.Event(
                        CHANGE_MODE_EVENT, mode="game"
                    ))

                if event.ui_object_id == '#main_menu_panel.#load_city_btn':
                    print("Loading City")

                if event.ui_object_id == '#main_menu_panel.#exit_game_btn':
                    print("Exiting Game")
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, delta_time: float) -> None:
        """Update the state of the mode"""
        pass

    def draw(self, display: 'pygame.Surface', image_loader: ImageAssetLoader) -> None:
        """Draw to the screen while active"""
        display.blit(self.background, (0, 0))
        self.ui_manager.draw_ui(display)


class GameMode(Mode):
    """Mode active when playing the game"""

    mode_name = 'Game'

    def __init__(self, ui_manager: 'pygame_gui.UIManager', screen_size: Tuple[int, int]) -> None:
        super().__init__(ui_manager, screen_size)
        self.camera = Camera(screen_size[0], screen_size[1], 10)
        self.background = pygame.Surface(screen_size)
        self.background.fill(SKY_BLUE)
        self.sim = Simulation(
            SAMPLE_THEME_PLUGIN,
            "Squaresville",
            CityFactory(LegacyLayoutFactory()))
        self.sim_running = False
        self.selected_tile: Optional[pygame.math.Vector2] = None
        self.selected_building: Optional[str] = None
        self.open_windows: Dict[str, pygame_gui.elements.UIWindow] = {}
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
        self.button_down = {
            "left": False,
            "right": False,
            "up": False,
            "down": False
        }

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle PyGame events while active"""
        mouse_screen_x, mouse_screen_y = pygame.mouse.get_pos()
        mouse_grid_x, mouse_grid_y = mouse_to_grid(
            mouse_screen_x, mouse_screen_y, self.camera.scroll)
        if self._is_mouse_in_bounds(mouse_grid_x, mouse_grid_y):
            self.selected_tile = pygame.math.Vector2(
                mouse_grid_x, mouse_grid_y)
        else:
            self.selected_tile = None

        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_WINDOW_CLOSE:
                del self.open_windows[event.ui_object_id]
                return
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.ui_elements['step-btn']:
                    self.sim.step()
                if event.ui_element == self.ui_elements['play-btn']:
                    self.sim_running = True
                if event.ui_element == self.ui_elements['pause-btn']:
                    self.sim_running = False
                    print("Simulation Paused")
                return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self.button_down["up"] = True
            if event.key == pygame.K_a:
                self.button_down["left"] = True
            if event.key == pygame.K_s:
                self.button_down["down"] = True
            if event.key == pygame.K_d:
                self.button_down["right"] = True
            return

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w:
                self.button_down["up"] = False
            if event.key == pygame.K_a:
                self.button_down["left"] = False
            if event.key == pygame.K_s:
                self.button_down["down"] = False
            if event.key == pygame.K_d:
                self.button_down["right"] = False
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            #     self.ui_manager.get_window_stack().get_stack(
            #     )[0].check_clicked_inside_or_blocking(event)
            focus_set = self.ui_manager.get_focus_set()
            if focus_set and self.ui_manager.get_root_container() not in focus_set:
                return

            if self.selected_tile is not None:
                lot = self.sim.get_city().layout.lot_grid[int(
                    self.selected_tile.x), int(self.selected_tile.y)]

                if lot and lot.building:
                    self.selected_building = lot.building
                    print(self.selected_building)
                    # building = self.sim.buildings[self.selected_building]
                    # residences = [self.sim.residences[residence_id]
                    #               for residence_id in building.housing_units]
                    # for r in residences:
                    #     for character_id in r.residents:
                    #         character = self.sim.characters[character_id]
                    #
                    #         if character_id in self.open_windows:
                    #             self.ui_manager.get_window_stack().move_window_to_front(
                    #                 self.open_windows[character_id])
                    #         else:
                    #             self.open_windows[character_id] = CharacterInfoWindow(
                    #                 character, (50, 50), self.ui_manager)

    def update(self, delta_time: float) -> None:
        """Update the state of the mode"""
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

        if self.sim_running:
            print("Stepping")
            self.sim.step()

    def draw(self, display: 'pygame.Surface', image_loader: ImageAssetLoader) -> None:
        """Draw to the screen while active"""
        display.blit(self.background, (0, 0))
        self._draw_ground(display, image_loader)
        self._draw_roads(display, image_loader)
        self._draw_hover_tile(display)
        self.ui_manager.draw_ui(display)

    def _is_mouse_in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.sim.get_city().layout.shape[0] \
            and 0 <= y < self.sim.get_city().layout.shape[1]

    def _reset_buttons(self) -> None:
        self.button_down["up"] = False
        self.button_down["left"] = False
        self.button_down["down"] = False
        self.button_down["right"] = False

    def _draw_ground(self, display: pygame.Surface, image_loader: ImageAssetLoader) -> None:
        # Draw the ground
        rows, cols = self.sim.get_city().layout.shape
        for x in range(rows):
            for y in range(cols):
                pos_info = grid_to_world((x, y))
                render_pos = pos_info["render_pos"]
                display.blit(
                    image_loader["grass"],
                    (render_pos[0] + self.camera.scroll.x, render_pos[1] + self.camera.scroll.y))

    def _draw_roads(self, display: pygame.Surface, image_loader: ImageAssetLoader) -> None:
        rows, cols = self.sim.get_city().layout.shape
        for x in range(rows):
            for y in range(cols):
                render_pos = grid_to_world((x, y))["render_pos"]
                road_type = self.sim.get_city().layout.road_grid[x, y]
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

                    display.blit(
                        image_loader[image_tile_name],
                        (render_pos[0] + self.camera.scroll.x, render_pos[1] + self.camera.scroll.y))

    def _draw_buildings(self, display: pygame.Surface, image_loader: ImageAssetLoader) -> None:
        rows, cols = self.sim.get_city().layout.shape
        for x in range(rows):
            for y in range(cols):
                lot = self.sim.get_city().layout.lot_grid[x, y]
                if lot and lot.building:
                    building_style = self.sim.world.component_for_entity(lot.building, Building).building_style
                    building_img = image_loader[building_style]
                    render_pos = grid_to_world((x, y))["render_pos"]
                    display.blit(
                        building_img,
                        (render_pos[0] + self.camera.scroll.x,
                         render_pos[1] + self.camera.scroll.y - building_img.get_height() + TILE_SIZE))

    def _draw_hover_tile(self, display: pygame.Surface) -> None:
        if self.selected_tile is not None:
            poly = grid_to_world((int(self.selected_tile.x), int(
                self.selected_tile.y)))['iso_poly']
            poly = [(x + self.camera.scroll.x, y + self.camera.scroll.y)
                    for x, y in poly]
            pygame.draw.polygon(display, (255, 255, 255), poly, 3)
