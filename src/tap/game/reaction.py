import pygame as pygame
import random

from tap.game import constants
from tap.game.drawer import Drawer
from tap.classes import GameState, ErrorMessage, Data, Settings


class ReactionTest:
    def __init__(self, drawer: Drawer, data: Data, settings: Settings):
        self.drawer = drawer
        self.data = data
        self.settings = settings

    def start_loop(self):
        self.drawer.render_instruction(
            self.settings.instruction + "\n\nPRESS SPACEBAR TO START"
        )

        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.drawer.render_text("", 7650)
                    return True

    def ready_loop(self):
        self.drawer.reset_meter(0)
        self.drawer.render_text("GET READY!", delay=3700)
        self.drawer.render_text("PRESS SPACEBAR")

        timer_start = pygame.time.get_ticks()
        error_flag = False

        while True:
            current_time = pygame.time.get_ticks()
            delta_time = current_time - timer_start

            if delta_time >= 3000 and not error_flag:
                error_flag = True
                self.drawer.render_text("PLEASE PRESS THE SPACEBAR")
                self.data.add_error(ErrorMessage.WAIT_TO_START)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    return True

    def hold_loop(self):
        timer_start = pygame.time.get_ticks()
        timer_release = timer_start + random.randint(2000, 4000)

        while True:
            current_time = pygame.time.get_ticks()

            if current_time >= timer_release:
                self.drawer.render_text("RELEASE", constants.RED)

            for event in pygame.event.get():
                if event.type == pygame.TEXTINPUT and event.text == " ":
                    if current_time > timer_release + 1000:
                        self.drawer.render_text("YOU WAITED TOO LONG", delay=3700)
                        self.data.add_error(ErrorMessage.WAIT_TOO_LONG)
                        return False
                elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                    if current_time < timer_release:
                        self.drawer.render_text("YOU RELEASED TOO SOON", delay=3700)
                        self.data.add_error(ErrorMessage.RELEASE_TOO_SOON)
                        return False
                    else:
                        self.drawer.render_text("", constants.FG, 2000)
                        reaction_time = current_time - timer_release
                        self.data.current_data_row.reaction_time = str(reaction_time)
                        return True
            pygame.display.flip()

    def run(self, first_trial: bool):
        current_state = GameState.START if first_trial else GameState.READY

        while True:
            if current_state == GameState.START:
                current_state = (
                    GameState.READY if self.start_loop() else GameState.START
                )
            elif current_state == GameState.READY:
                current_state = GameState.HOLD if self.ready_loop() else GameState.READY
            elif current_state == GameState.HOLD:
                current_state = GameState.SHOCK if self.hold_loop() else GameState.READY
            elif current_state == GameState.SHOCK:
                return True
            else:
                return False

            pygame.display.flip()
