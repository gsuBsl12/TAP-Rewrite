import pygame
import math


from tap.game import constants


class Drawer:
    def __init__(self, surface: pygame.Surface, textbox: pygame.Surface):
        self.surface = surface
        self.textbox = textbox

        self.font = pygame.font.SysFont(None, 30)

        window = surface.get_rect()
        self.center_x = window.centerx
        self.center_y = window.centery

    # https://stackoverflow.com/questions/42014195/rendering-text-with-multiple-lines-in-pygame
    def blit_text(self, surface, text, pos, color=constants.FG):
        words = [
            word.split(" ") for word in text.splitlines()
        ]  # 2D array where each row is a list of words.
        space = self.font.size(" ")[0]  # The width of a space.
        max_width, max_height = surface.get_size()
        x, y = pos
        for line in words:
            for word in line:
                word_surface = self.font.render(word, 1, color)
                word_width, word_height = word_surface.get_size()
                if x + word_width >= max_width:
                    x = pos[0]  # Reset the x.
                    y += word_height  # Start on new row.
                surface.blit(word_surface, (x, y))
                x += word_width + space
            x = pos[0]  # Reset the x.
            y += word_height  # Start on new row.

    def render_instruction(self, text, color=constants.FG):
        self.surface.fill(constants.WHITE)
        self.textbox.fill(constants.BG)
        pos = self.textbox.get_rect()
        self.blit_text(self.textbox, text, (pos.centerx - 200, pos.top))
        pygame.display.flip()

    def render_text(self, text, color=constants.FG, delay=0):
        self.textbox.fill(constants.BG)
        text_block = self.font.render(text, 1, color)
        self.textbox.blit(
            text_block, text_block.get_rect(center=self.textbox.get_rect().center)
        )
        pygame.display.flip()
        pygame.time.wait(delay)

    def clockwise_arc(self, point, radius, startAngle, endAngle):
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = point

        endRad = math.radians(-startAngle)
        startRad = math.radians(-endAngle)

        return rect, startRad, endRad

    def draw_circles(self):
        self.surface.fill(constants.WHITE)

        for i in range(1, 11):
            # Draw circles
            offset = -275 + i * 50
            x = int(self.center_x + offset)
            y = int((self.center_y - 60) + (self.center_y / 2))
            pygame.draw.circle(
                self.surface, constants.BLACK, (x, y), constants.RADIUS, 3
            )

            # Draw text
            offset = -280 + i * 50
            x = self.center_x + offset
            y = (self.center_y - 30) + (self.center_y / 2)
            text = self.font.render(str(i), 1, constants.BLACK)
            self.surface.blit(text, (x, y))

        low_text = self.font.render("Low", 1, constants.BLACK)
        self.surface.blit(
            low_text, (self.center_x - 230, (self.center_y + 10) + (self.center_y / 2))
        )

        high_text = self.font.render("High", 1, constants.BLACK)
        self.surface.blit(
            high_text, (self.center_x + 220, (self.center_y + 10) + (self.center_y / 2))
        )

        # Initialize arc
        pygame.draw.circle(
            self.surface,
            constants.BLACK,
            (self.center_x, self.center_y - 250),
            100,
            width=5,
            draw_top_left=True,
            draw_top_right=True,
        )
        pygame.draw.line(
            self.surface,
            constants.BLACK,
            (self.center_x - 100, self.center_y - 250),
            (self.center_x + 100, self.center_y - 250),
            5,
        )

    def draw_meter(self, _key):
        key = _key - 48
        if key == 0:
            key = 10

        offset = -275 + key * 50

        x = int(self.center_x + offset)
        y = int((self.center_y - 60) + (self.center_y / 2))
        pygame.draw.circle(self.surface, constants.RED, (x, y), constants.RADIUS, 39)
        rect, startRad, endRad = self.clockwise_arc(
            (self.center_x, self.center_y - 250), 95, 180, (180 + (180 / 10 * key))
        )
        pygame.draw.arc(self.surface, constants.RED, rect, startRad, endRad, 95)
        pygame.display.flip()

    def reset_meter(self, _key):
        key = _key - 48
        if key == 0:
            key = 10

        offset = 275
        rect, startRad, endRad = self.clockwise_arc(
            (self.center_x, self.center_y - 250), 95, 180, (180 + (180 / 10 * key))
        )
        pygame.draw.circle(
            self.surface,
            constants.WHITE,
            (self.center_x + offset, (self.center_y - 60) + (self.center_y / 2)),
            constants.RADIUS,
            39,
        )
        pygame.draw.arc(self.surface, constants.WHITE, rect, startRad, endRad, 95)
        self.draw_circles()
        pygame.display.flip()
