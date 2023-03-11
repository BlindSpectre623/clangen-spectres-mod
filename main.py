#!/usr/bin/env python3


# pylint: disable=line-too-long
"""




This file is the main file for the game.
It also contains the main pygame loop
It first sets up logging, then loads the version hash from commit.txt (if it exists), then loads the cats and clan.
It then loads the settings, and then loads the start screen.




""" # pylint: enable=line-too-long

import platform
import sys
import os
import time

from scripts.datadir import get_log_dir, setup_data_dir
from scripts.version import get_version_info

directory = os.path.dirname(__file__)
if directory:
    os.chdir(directory)

import subprocess


# Setup logging
import logging


setup_data_dir()


formatter = logging.Formatter(
    "%(name)s - %(levelname)s - %(filename)s / %(funcName)s / %(lineno)d - %(message)s"
    )
# Logging for file
timestr = time.strftime("%Y%m%d_%H%M%S")
log_file_name = get_log_dir() + f"/clangen_{timestr}.log"
file_handler = logging.FileHandler(log_file_name)
file_handler.setFormatter(formatter)
# Only log errors to file
file_handler.setLevel(logging.ERROR)
# Logging for console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logging.root.addHandler(file_handler)
logging.root.addHandler(stream_handler)


def log_crash(logtype, value, tb):
    """
    Log uncaught exceptions to file
    """
    logging.critical("Uncaught exception", exc_info=(logtype, value, tb))
    sys.__excepthook__(type, value, tb)

sys.excepthook = log_crash

# if user is developing in a github codespace
if os.environ.get('CODESPACES'):
    print('')
    print("Github codespace user!!! Sorry, but sound *may* not work :(")
    print("SDL_AUDIODRIVER is dsl. This is to avoid ALSA errors, but it may disable sound.")
    print('')
    print("Web VNC:")
    print(
        f"https://{os.environ.get('CODESPACE_NAME')}-6080"
        + f".{os.environ.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN')}"
        + "/?autoconnect=true&reconnect=true&password=clangen&resize=scale")
    print("(use clangen in fullscreen mode for best results)")
    print('')


if get_version_info().is_source_build:
    print("Running on source code")
    if get_version_info() == "":
        print("Failed to get git commit hash, using hardcoded version number instead.")
        print("Hey testers! We recommend you use git to clone the repository, as it makes things easier for everyone.")  # pylint: disable=line-too-long
        print("There are instructions at https://discord.com/channels/1003759225522110524/1054942461178421289/1078170877117616169")  # pylint: disable=line-too-long
else:
    print("Running on PyInstaller build")

print("Running on commit " + get_version_info().version_number)

# Load game
from scripts.game_structure.load_cat import load_cats
from scripts.game_structure.windows import SaveCheck
from scripts.game_structure.game_essentials import game, MANAGER, screen
from scripts.game_structure.discord_rpc import _DiscordRPC
from scripts.cat.sprites import sprites
from scripts.clan import clan_class
from scripts.utility import get_text_box_theme
import pygame_gui
import pygame




# import all screens for initialization (Note - must be done after pygame_gui manager is created)
from scripts.screens.all_screens import start_screen # pylint: disable=ungrouped-imports

# P Y G A M E
clock = pygame.time.Clock()
pygame.display.set_icon(pygame.image.load('resources/images/icon.png'))

# LOAD cats & clan
clan_list = game.read_clans()
if clan_list:
    game.switches['clan_list'] = clan_list
    try:
        load_cats()
        clan_class.load_clan()
    except Exception as e:
        logging.exception("File failed to load")
        if not game.switches['error_message']:
            game.switches[
                'error_message'] = 'There was an error loading the cats file!'

    # try:
    #     game.map_info = load_map(get_save_dir() + '/' + game.clan.name)
    # except NameError:
    #     game.map_info = {}
    # except:
    #     game.map_info = load_map("Fallback")

# LOAD settings

sprites.load_scars()

start_screen.screen_switches()






#Version Number
if game.settings['fullscreen']:
    version_number = pygame_gui.elements.UILabel(
        pygame.Rect((1500, 1350), (-1, -1)), get_version_info().version_number[0:8],
        object_id=get_text_box_theme())
    # Adjust position
    version_number.set_position(
        (1600 - version_number.get_relative_rect()[2] - 8,
         1400 - version_number.get_relative_rect()[3]))
else:
    version_number = pygame_gui.elements.UILabel(
        pygame.Rect((700, 650), (-1, -1)), get_version_info().version_number[0:8],
        object_id=get_text_box_theme())
    # Adjust position
    version_number.set_position(
        (800 - version_number.get_relative_rect()[2] - 8,
        700 - version_number.get_relative_rect()[3]))


game.rpc = _DiscordRPC("1076277970060185701", daemon=True)
game.rpc.start()
game.rpc.start_rpc.set()
while True:
    time_delta = clock.tick(30) / 1000.0
    if game.switches['cur_screen'] not in ['start screen']:
        if game.settings['dark mode']:
            screen.fill((57, 50, 36))
        else:
            screen.fill((206, 194, 168))

    # Draw screens
    # This occurs before events are handled to stop pygame_gui buttons from blinking.
    game.all_screens[game.current_screen].on_use()

    # EVENTS
    for event in pygame.event.get():
        game.all_screens[game.current_screen].handle_event(event)

        if event.type == pygame.QUIT:
            # Dont display if on the start screen or there is no clan.
            if (game.switches['cur_screen'] in ['start screen',
                                                'switch clan screen',
                                                'settings screen',
                                                'info screen',
                                                'make clan screen']
                or not game.clan):
                game.rpc.close_rpc.set()
                game.rpc.update_rpc.set()
                pygame.display.quit()
                pygame.quit()
                if game.rpc.is_alive():
                    game.rpc.join(1)
                sys.exit()
            else:
                SaveCheck(game.switches['cur_screen'], False, None)


        # MOUSE CLICK
        if event.type == pygame.MOUSEBUTTONDOWN:
            game.clicked = True

        # F2 turns toggles visual debug mode for pygame_gui, allowed for easier bug fixes.
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2:
                if not MANAGER.visual_debug_active:
                    MANAGER.set_visual_debug_mode(True)
                else:
                    MANAGER.set_visual_debug_mode(False)

        MANAGER.process_events(event)

    MANAGER.update(time_delta)

    # update
    game.update_game()
    if game.switch_screens:
        game.all_screens[game.last_screen_forupdate].exit_screen()
        game.all_screens[game.current_screen].screen_switches()
        game.switch_screens = False

    # END FRAME
    MANAGER.draw_ui(screen)

    pygame.display.update()
