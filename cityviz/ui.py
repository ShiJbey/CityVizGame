from typing import Tuple
import pygame
from pygame_gui import UIManager
import pygame_gui
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_text_box import UITextBox
from talktown.person.person import Person
from talktown.place import Building


class CharacterInfoWindow(UIWindow):
    """
    Wraps a pygame_ui panel to display information
    about a given character
    """

    __slots__ = 'character', 'ui_manager', 'panel'

    def __init__(self, character: 'Person', position: Tuple[int, int], ui_manager: 'UIManager') -> None:
        super().__init__(
            pygame.Rect(position, (320, 240)),
            ui_manager,
            window_display_title=character.name,
            object_id=f'{character.id}')
        self.character = character
        self.ui_manager = ui_manager
        self.text = UITextBox(
            f"name: {character.name}<br>"
            f"age: {round(character.age)}<br>"
            f"gender: {character.gender}<br>"
            f"occupation: {character.occupation if character.occupation else 'None'}<br>",
            pygame.Rect(0, 0, 320, 240),
            manager=ui_manager,
            container=self,
            parent_element=self,
        )

    def process_event(self, event: pygame.event.Event) -> bool:
        handled = super().process_event(event)
        if (
            event.type == pygame.USEREVENT and
            event.user_type == pygame_gui.UI_BUTTON_PRESSED and
            event.ui_object_id == "#character_window.#title_bar" and
            event.ui_element == self.title_bar
        ):
            handled = True

            event_data = {
                'user_type': 'character_window_selected',
                'ui_element': self,
                'ui_object_id': self.most_specific_combined_id
            }

            window_selected_event = pygame.event.Event(
                pygame.USEREVENT, event_data)

            pygame.event.post(window_selected_event)

        return handled


class BuildingInfoWindow(UIWindow):
    """
    Wraps a pygame_ui panel to display information
    about a given building
    """

    def __init__(self, building: 'Building', ui_manager: 'UIManager') -> None:
        super().__init__(
            pygame.Rect((10, 10), (320, 240)),
            ui_manager,
            window_display_title=building.building_type,
            object_id=f'building_win')

#
# class BusinessInfoWindow(UIWindow):
#     """
#     Wraps a pygame_ui panel to display information
#     about a given business
#     """
#
#     def __init__(self, business: 'Business', sim: 'Simulation') -> None:
#         pass
#
#
# class ResidenceInfoWindow(UIWindow):
#     """
#     Wraps a pygame_ui panel to display information
#     about a given residence
#     """
#
#     def __init__(self, residence: 'Residence') -> None:
#         pass


def show_building_window(building: 'Building', ui_manager: UIManager) -> UIWindow:
    """Creates a UIWindow for the given building"""
    return BuildingInfoWindow(building, ui_manager)
