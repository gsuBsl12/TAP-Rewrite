import pygame
import random

from tap.game.drawer import Drawer
from tap.classes import ErrorMessage, Data, Settings, ThreadHandler, ShockTask, Logger


class ShockMeter:
    def __init__(
        self,
        thread_handler: ThreadHandler,
        logger: Logger,
        settings: Settings,
        drawer: Drawer,
        data: Data,
    ):
        self.thread_handler = thread_handler
        self.logger = logger
        self.settings = settings
        self.drawer = drawer
        self.data = data

    def get_shock_duration(self) -> float:
        mn = self.settings.min_shock_duration
        mx = self.settings.max_shock_duration

        duration = random.randint(mn, mx) / 1000

        if duration > 10.0:
            duration = 10.0
        if duration < 0.0:
            duration = 0.0

        self.logger.log(f"Returning ShockMeter.get_shock_duration {duration} ")

        return duration

    def get_shock_value(self, shock):
        high = self.settings.higher_threshold
        low = self.settings.lower_threshold
        intensity = self.settings.intensities[shock - 1]
        # Calibration: [0.15, 0.135, 0.12, 0.105, 0.09, 0.075, 0.06, 0.045, 0.03, 0.0]
        calibration = [x / 1000 for x in range(150, 15, -15)] + [0.0]

        if intensity < 0:
            intensity = 0
        if intensity > 100:
            intensity = 100

        m = (high - low) / 10

        shock_mA = (((m * shock) + low) * (intensity / 100)) + calibration[shock - 1]

        self.logger.log(f"Returning ShockMeter.get_shock_value({shock}) {shock_mA} ")

        return shock_mA

    def generate_shock(self, shock: int, duration: float):
        if shock >= 10 or shock <= 0:
            shock = 10

        shock_mA = self.get_shock_value(shock)

        self.logger.log(
            f"Putting ShockTask in task_queue. ShockMeter.generate_shock({shock}, {duration})"
        )

        put = self.thread_handler.task_queue.put_task(ShockTask(shock_mA, duration, 1))
        if not put:
            self.logger.log("Failed to put ShockTask in task_queue. Queue locked/full.")

    def lose_loop(self, shock: int, feedback: int):
        self.logger.log("lose_loop()")
        self.drawer.render_text("YOU LOST! YOU GET A SHOCK", delay=2400)
        if shock > 10:
            shock = 10
        if shock < 0:
            shock = 0
        if feedback > 10:
            feedback = 10
        if feedback < 0:
            feedback = 0
        key = 48 + feedback
        self.drawer.draw_meter(key)

        duration = self.get_shock_duration()

        self.logger.log(f"Calling ShockMeter.generate_shock({shock}, {duration})")

        self.generate_shock(shock, duration)

        self.drawer.render_text("", delay=int(duration * 1000))
        self.drawer.reset_meter(key)
        self.drawer.render_text("", delay=4000)
        return True

    def win_loop(self):
        self.logger.log("win_loop()")
        self.drawer.render_text("YOU WON! YOU GET TO GIVE A SHOCK")

        timer_start = pygame.time.get_ticks()
        time_held = 0
        key_pressed = None

        data_row = self.data.current_data_row
        error_flag1 = False
        error_flag2 = False

        while True:
            current_time = pygame.time.get_ticks()

            if (
                current_time >= timer_start + 4000
                and time_held == 0
                and not error_flag1
            ):
                error_flag1 = True
                self.drawer.render_text("YOU MUST PRESS A SHOCK BUTTON")
                self.data.add_error(ErrorMessage.WAIT_TO_SHOCK)

            for event in pygame.event.get():
                if (
                    event.type == pygame.KEYDOWN
                    and event.key in range(48, 58)
                    and not key_pressed
                ):  # start
                    key_pressed = str(event.unicode)
                    data_row.shock_intensity = (
                        "10" if key_pressed == "0" else key_pressed
                    )
                    if time_held == 0:
                        self.drawer.render_text("")
                        self.drawer.draw_meter(event.key)
                        time_held = current_time
                elif (
                    event.type == pygame.TEXTINPUT and event.text == key_pressed
                ):  # hold
                    if current_time > time_held + 7000 and not error_flag2:
                        error_flag2 = True
                        self.drawer.render_text(
                            "YOU ARE DONE SHOCKING! PLEASE RELEASE SHOCK BUTTON"
                        )
                        self.data.add_error(ErrorMessage.SHOCK_TOO_LONG)
                elif event.type == pygame.KEYUP and event.unicode == key_pressed:  # end
                    if current_time > timer_start:
                        time_held = current_time - time_held
                        self.drawer.reset_meter(event.key)
                        data_row.shock_duration = str(time_held)
                        self.drawer.render_text("YOU ARE DONE SHOCKING!", delay=5000)
                        return True

            pygame.display.flip()
