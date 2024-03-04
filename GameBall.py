from p5 import *
import fastfiz as ff
import vectormath as vmath


class GameBall:
    ball_colors = {
        0: (227, 228, 230),  # White
        1: (234, 220, 93),  # Yellow
        2: (56, 121, 171),  # Blue
        3: (219, 72, 65),  # Red
        4: (137, 133, 171),  # Purple
        5: (230, 140, 72),  # Orange
        6: (75, 133, 88),  # Green
        7: (165, 67, 67),  # Dark red
        8: (32, 30, 31),  # Black
    }

    def __init__(self, radius: float, number: int, position: vmath.Vector2, state: int):
        self.radius = radius
        self.number = number
        self.position = position
        self.state = state
        self.color = GameBall.ball_colors[number if number <= 8 else number - 8]
        self.striped = number > 8

    def draw(self, scale=300):
        dont_draw_states = [ff.Ball.NOTINPLAY, ff.Ball.POCKETED_NE, ff.Ball.POCKETED_E, ff.Ball.POCKETED_SE,
                            ff.Ball.POCKETED_SW, ff.Ball.POCKETED_W, ff.Ball.POCKETED_NW]

        if self.state in dont_draw_states:
            return

        fill(*self.color)
        circle(self.position.x * scale, self.position.y * scale, self.radius * scale * 2)

        if self.striped:
            fill(*GameBall.ball_colors[0])
            circle(self.position.x * scale, self.position.y * scale, 0.02 * scale)
