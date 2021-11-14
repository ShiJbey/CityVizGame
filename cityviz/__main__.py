import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pygame
import pygame_gui
from .asset_loader import FontAssetConfig, FontAssetLoader, ImageAssetConfig, ImageAssetLoader
from .mode import CHANGE_MODE_EVENT, GameMode, Mode, MainMenuMode
from .utils import draw_text


@dataclass
class GameConfig:
    width: int = 900
    height: int = 500
    fps: int = 60
    show_debug: bool = False


class Game:
    """Game instance for CityViz"""

    def __init__(
            self,
            config: GameConfig,
            image_loader: 'ImageAssetLoader',
            font_loader: 'FontAssetLoader'
    ) -> None:
        self.config = config
        self.display = pygame.Surface((config.width, config.height))
        self.window = pygame.display.set_mode((config.width, config.height))
        pygame.display.set_caption("CityViz")
        self.image_loader = image_loader
        self.image_loader.load()
        self.font_loader = font_loader
        self.font_loader.load()
        self.clock = pygame.time.Clock()
        self.running = False
        self.font = self.font_loader["fredoka"]
        self.ui_manager = pygame_gui.UIManager((config.width, config.height))
        self.active_mode: 'Mode' = MainMenuMode(
            self.ui_manager, (self.config.width, self.config.height))

    def update(self, delta_time: float) -> None:
        """Update the active mode"""
        self.ui_manager.update(delta_time)
        self.active_mode.update(delta_time)

    def draw(self) -> None:
        """Draw the active game mode"""
        self.active_mode.draw(self.display, self.image_loader)
        if self.config.show_debug:
            self.draw_debug()
        self.window.blit(self.display, (0, 0))
        pygame.display.update()

    def run(self) -> None:
        self.running = True
        while self.running:
            time_delta = self.clock.tick(self.config.fps) / 1000.0
            self.handle_events()
            self.update(time_delta)
            self.draw()
        pygame.quit()

    def draw_debug(self) -> None:
        draw_text(
            self.display,
            f"Mode: {self.active_mode.mode_name}, FPS: {round(self.clock.get_fps())}",
            self.config.width - 150,
            10,
            pygame.font.Font(self.font, 18))

    def handle_events(self):
        """Active mode handles PyGame events"""
        for event in pygame.event.get():
            self.ui_manager.process_events(event)

            if event.type == pygame.QUIT:
                self.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    continue

            if event.type == CHANGE_MODE_EVENT:
                if event.mode == "game":
                    self.active_mode.deactivate()
                    self.active_mode = \
                        GameMode(self.ui_manager,
                                 (self.config.width, self.config.height))

            self.active_mode.handle_event(event)

    def quit(self) -> None:
        self.running = False
        self.active_mode.deactivate()



def main():
    """main function"""
    pygame.init()
    pygame.mixer.init()

    assets_dir = Path(os.path.abspath(__file__)).parent / 'assets'

    image_asset_loader = ImageAssetLoader([
        ImageAssetConfig("ground", str(
            assets_dir / 'graphics' / 'exports' / 'ground_cube.png')),
        ImageAssetConfig("building", str(
            assets_dir / 'graphics' / 'exports' / 'building.png')),
        ImageAssetConfig("Restaurant", str(
            assets_dir / 'graphics' / 'exports' / 'restaurant.png')),
        ImageAssetConfig("plain building", str(
            assets_dir / 'graphics' / 'exports' / 'bar.png')),
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

    game = Game(
        config=GameConfig(1024, 768, 60, show_debug=True),
        image_loader=image_asset_loader,
        font_loader=font_loader)

    game.run()


if __name__ == "__main__":
    main()
