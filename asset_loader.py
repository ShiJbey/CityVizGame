from typing import Dict, Tuple, List, AnyStr
from dataclasses import dataclass
import pygame
from pygame.surface import Surface


@dataclass
class ImageAssetConfig:
    name: str
    path: str
    color_key: Tuple[int, int, int] = (0, 0, 0)


class ImageAssetLoader:

    def __init__(self, assets: 'List[ImageAssetConfig]') -> None:
        self._asset_configs: 'List[ImageAssetConfig]' = assets
        self._asset_dict: Dict[str, 'Surface'] = {}

    def __getitem__(self, name: str) -> 'Surface':
        return self._asset_dict[name]

    def load(self) -> None:
        for entry in self._asset_configs:
            surface: 'Surface' = pygame.image.load(entry.path).convert_alpha()

            # if entry.color_key:
            #     surface.set_colorkey(entry.color_key)

            self._asset_dict[entry.name] = surface


@dataclass
class FontAssetConfig:
    name: str
    path: str
    font_size: int = 16


class FontAssetLoader:
    def __init__(self, assets: 'List[FontAssetConfig]') -> None:
        self._asset_configs: 'List[FontAssetConfig]' = assets
        self._asset_dict: Dict[str, 'str'] = {}
        for entry in self._asset_configs:
            self._asset_dict[entry.name] = entry.path

    def __getitem__(self, name: str) -> 'str':
        return self._asset_dict[name]

    def load(self) -> None:
        pass
