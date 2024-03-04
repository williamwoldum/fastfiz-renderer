from typing import Tuple

import fastfiz as ff
from p5 import *
import vectormath as vmath

from .GameBall import GameBall


class GameTable:
    def __init__(self, width: float, length: float, side_pocket_width: float, corner_pocket_width: float,
                 rolling_friction_const: float, sliding_friction_const: float, gravitational_const: float,
                 game_balls: list[GameBall], shot_speed_factor: float):
        self.wood_width = width / 10
        self.rail_width = width / 30
        self.width = width + 2 * self.wood_width + 2 * self.rail_width
        self.length = length + 2 * self.wood_width + 2 * self.rail_width
        self.board_width = width
        self.board_length = length
        self.side_pocket_width = side_pocket_width
        self.corner_pocket_width = corner_pocket_width

        self.wood_color = (103, 92, 80)
        self.rail_color = (0, 46, 30)
        self.board_color = (21, 88, 67)
        self.pocket_color = (32, 30, 31)

        self.rolling_friction_const = rolling_friction_const
        self.sliding_friction_const = sliding_friction_const
        self.gravitational_const = gravitational_const
        self.game_balls = game_balls

        self._shot_queue: list[Tuple[ff.ShotParams, ff.Shot]] = []
        self._active_shot: Optional[ff.Shot] = None
        self._active_shot_start_time: float = 0
        self._shot_speed_factor = shot_speed_factor

    @classmethod
    def from_table_state(cls, table_state: ff.TableState, shot_speed_factor: float):
        game_balls = []

        for i in range(ff.Ball.CUE, ff.Ball.FIFTEEN + 1):
            ball: ff.Ball = table_state.getBall(i)
            pos = ball.getPos()
            game_balls.append(GameBall(ball.getRadius(), ball.getID(), vmath.Vector2(pos.x, pos.y), ball.getState()))

        table: ff.Table = table_state.getTable()

        return cls(table.TABLE_WIDTH, table.TABLE_LENGTH, table.SIDE_POCKET_WIDTH, table.CORNER_POCKET_WIDTH,
                   table.MU_ROLLING, table.MU_SLIDING, table.g, game_balls, shot_speed_factor)

    def draw(self, scale=300):

        # Wood
        fill(*self.wood_color)
        rect(0, 0, self.width * scale, self.length * scale)

        # Rails
        push()
        translate(int(self.wood_width * scale), int(self.wood_width * scale))
        fill(*self.rail_color)
        rect(0, 0, (self.board_width + self.rail_width * 2) * scale, (self.board_length + self.rail_width * 2) * scale)
        pop()

        # Board
        push()
        translate(int((self.rail_width + self.wood_width) * scale), int((self.rail_width + self.wood_width) * scale))
        fill(*self.board_color)
        rect(0, 0, self.board_width * scale, self.board_length * scale)
        pop()

        def draw_side_pocket(rotation_angle, rotation_point):
            push()
            translate(*rotation_point)
            rotate(rotation_angle)
            fill(*self.board_color)
            rect(
                0,
                -self.rail_width * scale,
                self.side_pocket_width * scale,
                self.side_pocket_width * scale)
            fill(*self.pocket_color)
            circle((self.side_pocket_width / 2) * scale, -self.corner_pocket_width / 2 * scale,
                   self.corner_pocket_width * scale)

            a = self.wood_width - (self.wood_width + self.rail_width - self.corner_pocket_width / 2)
            c = self.corner_pocket_width / 2
            b = math.sqrt(c ** 2 - a ** 2)

            fill(*self.rail_color)
            triangle(
                (b + self.side_pocket_width / 2) * scale, -self.rail_width * scale,
                self.side_pocket_width * scale, -self.rail_width * scale,
                self.side_pocket_width * scale, 0
            )
            triangle(
                (self.side_pocket_width / 2 - b) * scale, -self.rail_width * scale,
                0, -self.rail_width * scale,
                0, 0
            )
            pop()

        def draw_corner_pocket(rotation_angle, rotation_point):
            push()
            translate(*rotation_point)
            rotate(rotation_angle)
            fill(*self.board_color)
            rect(
                0, 0,
                self.corner_pocket_width * scale,
                self.corner_pocket_width * scale)
            fill(*self.pocket_color)
            circle(self.corner_pocket_width * scale / 2, 0, self.corner_pocket_width * scale)
            pop()

        offset = math.sqrt(self.corner_pocket_width ** 2 / 2)

        draw_corner_pocket(PI / 4 * 1, (
            (self.wood_width + 2 * self.rail_width + self.board_width - offset) * scale, self.wood_width * scale))  # NE
        draw_side_pocket(PI / 4 * 2, ((self.width - self.wood_width - self.rail_width) * scale, (
                self.wood_width + self.rail_width + self.board_length / 2 - self.side_pocket_width / 2) * scale))  # E
        draw_corner_pocket(PI / 4 * 3, (
            (self.width - self.wood_width) * scale, (self.length - self.wood_width - offset) * scale))  # SE
        draw_side_pocket(PI / 4 * 6, ((self.wood_width + self.rail_width) * scale, (
                self.wood_width + self.rail_width + self.board_length / 2 + self.side_pocket_width / 2) * scale))  # W
        draw_corner_pocket(PI / 4 * 5,
                           ((self.wood_width + offset) * scale, (self.length - self.wood_width) * scale))  # SW
        draw_corner_pocket(PI / 4 * 7, (self.wood_width * scale, (self.wood_width + offset) * scale))  # NW

        # Balls
        push()
        translate(int((self.rail_width + self.wood_width) * scale), int((self.rail_width + self.wood_width) * scale))
        for ball in self.game_balls:
            ball.draw(scale)
        pop()

    def update(self):
        if self._active_shot is None:
            if self._shot_queue:
                self._active_shot = self._shot_queue.pop(0)[1]
                self._active_shot_start_time = time.time()
            else:
                return

        time_since_shot_start = (time.time() - self._active_shot_start_time) * self._shot_speed_factor

        if time_since_shot_start > self._active_shot.getDuration():
            for ball in self.game_balls:
                ball.force_to_end_of_shot_pos(self._active_shot)
            self._active_shot = None
            return

        else:
            for ball in self.game_balls:
                ball.update(time_since_shot_start, self._active_shot, self.sliding_friction_const,
                            self.rolling_friction_const,
                            self.gravitational_const)

    def add_shot(self, params: ff.ShotParams, shot: ff.Shot):
        self._shot_queue.append((params, shot))
