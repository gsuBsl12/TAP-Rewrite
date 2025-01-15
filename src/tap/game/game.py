import pygame
from typing import List

from tap.game.reaction import ReactionTest
from tap.game.shock import ShockMeter
from tap.game.drawer import Drawer

from tap.classes import Trial, Data, Settings, ThreadHandler


def init():
    pygame.init()

    info = pygame.display.Info()
    screen_w = info.current_w
    screen_h = info.current_h

    display = pygame.display.set_mode((screen_w, screen_h))
    display.fill((255, 255, 255))

    subsurf_w = screen_w - 200
    subsurf_h = 200
    subsurf_x = (info.current_w / 2) - (subsurf_w / 2)
    subsurf_y = (info.current_h / 2) - (subsurf_h / 2)
    subsurf = display.subsurface((subsurf_x, subsurf_y), (subsurf_w, subsurf_h))

    return (display, subsurf)


def play(thread_handler: ThreadHandler, settings: Settings, trials: List[Trial]):
    if len(trials) <= 0:
        return
    display, subsurf = init()
    main_data = Data()

    drawer = Drawer(display, subsurf)
    react_mngr = ReactionTest(drawer, main_data, settings)
    shock_mngr = ShockMeter(thread_handler, settings, drawer, main_data)

    for i, trial in enumerate(trials):
        reaction_data = react_mngr.run(i == 0)
        if not reaction_data:
            return main_data

        wl = trial.wl == "Win"
        main_data.current_data_row.wl = "W" if wl else "L"

        # Diagnostic
        print(trial)

        if wl:
            trial_data = shock_mngr.win_loop()
            if trial_data is None:
                break
        else:
            shock_level = int(trial.shock)
            shock_mngr.lose_loop(shock_level, int(trial.feedback))

        main_data.finish_trial()

    drawer.render_instruction("Please wait for further instructions.")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    running = False
    pygame.quit()

    return main_data
