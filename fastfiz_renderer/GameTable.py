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
        self.pocket_marking_color = (77, 70, 62)

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

    def draw(self, scaling=200):
        # Wood
        fill(*self.wood_color)
        rect(0, 0, self.width * scaling, self.length * scaling)

        # Pocket markings
        marking_width = (self.wood_width * 2 + self.rail_width * 2) * scaling
        fill(*self.pocket_marking_color)
        square(0, 0, marking_width)
        square(0, self.length / 2 * scaling - marking_width / 2, marking_width)
        square(0, self.length * scaling - marking_width, marking_width)

        square(self.width * scaling - marking_width, 0, marking_width)
        square(self.width * scaling - marking_width, self.length / 2 * scaling - marking_width / 2, marking_width)
        square(self.width * scaling - marking_width, self.length * scaling - marking_width, marking_width)

        # Rails
        push()
        translate(int(self.wood_width * scaling), int(self.wood_width * scaling))
        fill(*self.rail_color)
        rect(0, 0, (self.board_width + self.rail_width * 2) * scaling, (self.board_length + self.rail_width * 2) * scaling)
        pop()

        # Board
        push()
        translate(int((self.rail_width + self.wood_width) * scaling), int((self.rail_width + self.wood_width) * scaling))
        fill(*self.board_color)
        rect(0, 0, self.board_width * scaling, self.board_length * scaling)
        pop()

        # Left-right markings
        fill(*GameBall.ball_colors[ff.Ball.CUE])
        push()
        translate(0, int((self.wood_width + self.rail_width) * scaling))
        for i in range(1, 8):
            circle(self.wood_width * scaling / 2, self.board_length * scaling / 8 * i, self.wood_width / 10 * scaling)
            circle((self.wood_width * 1.5 + self.board_width + self.rail_width * 2) * scaling,
                   self.board_length * scaling / 8 * i, self.wood_width / 10 * scaling)

            if i == 2 or i == 6:
                strokeWeight(2)
                col = (*GameBall.ball_colors[ff.Ball.CUE], 50)
                stroke(*col)
                line((self.wood_width + self.rail_width) * scaling,
                     self.board_length * scaling / 8 * i,
                     (self.wood_width + self.board_width + self.rail_width) * scaling,
                     self.board_length * scaling / 8 * i)
                noStroke()
        pop()

        # Top-bottom markings
        push()
        translate(int((self.wood_width + self.rail_width) * scaling), 0)
        for i in range(1, 4):
            circle(self.board_width * scaling / 4 * i, self.wood_width / 2 * scaling, self.wood_width / 10 * scaling)
            circle(self.board_width * scaling / 4 * i, (self.wood_width * 1.5 + self.rail_width * 2 + self.board_length) * scaling, self.wood_width / 10 * scaling)
        pop()

        def draw_side_pocket(rotation_angle, rotation_point):
            push()
            translate(*rotation_point)
            rotate(rotation_angle)
            fill(*self.board_color)
            rect(
                0,
                -self.rail_width * scaling,
                self.side_pocket_width * scaling,
                self.side_pocket_width * scaling)
            fill(*self.pocket_color)
            circle((self.side_pocket_width / 2) * scaling, -self.corner_pocket_width / 2 * scaling,
                   self.corner_pocket_width * scaling)

            a = self.wood_width - (self.wood_width + self.rail_width - self.corner_pocket_width / 2)
            c = self.corner_pocket_width / 2
            b = math.sqrt(c ** 2 - a ** 2)

            fill(*self.rail_color)
            triangle(
                (b + self.side_pocket_width / 2) * scaling, -self.rail_width * scaling,
                self.side_pocket_width * scaling, -self.rail_width * scaling,
                self.side_pocket_width * scaling, 0
            )
            triangle(
                (self.side_pocket_width / 2 - b) * scaling, -self.rail_width * scaling,
                0, -self.rail_width * scaling,
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
                self.corner_pocket_width * scaling,
                self.corner_pocket_width * scaling)
            fill(*self.pocket_color)
            circle(self.corner_pocket_width * scaling / 2, 0, self.corner_pocket_width * scaling)
            pop()

        offset = math.sqrt(self.corner_pocket_width ** 2 / 2)

        draw_corner_pocket(PI / 4 * 1, (
            (self.wood_width + 2 * self.rail_width + self.board_width - offset) * scaling, self.wood_width * scaling))  # NE
        draw_side_pocket(PI / 4 * 2, ((self.width - self.wood_width - self.rail_width) * scaling, (
                self.wood_width + self.rail_width + self.board_length / 2 - self.side_pocket_width / 2) * scaling))  # E
        draw_corner_pocket(PI / 4 * 3, (
            (self.width - self.wood_width) * scaling, (self.length - self.wood_width - offset) * scaling))  # SE
        draw_side_pocket(PI / 4 * 6, ((self.wood_width + self.rail_width) * scaling, (
                self.wood_width + self.rail_width + self.board_length / 2 + self.side_pocket_width / 2) * scaling))  # W
        draw_corner_pocket(PI / 4 * 5,
                           ((self.wood_width + offset) * scaling, (self.length - self.wood_width) * scaling))  # SW
        draw_corner_pocket(PI / 4 * 7, (self.wood_width * scaling, (self.wood_width + offset) * scaling))  # NW

        # Balls
        push()
        translate(int((self.rail_width + self.wood_width) * scaling), int((self.rail_width + self.wood_width) * scaling))
        for ball in self.game_balls:
            ball.draw(scaling)
        pop()

    def update(self, shot_requester: Optional[Callable[None, None]]):
        if self._active_shot is None:
            if self._shot_queue:
                self._active_shot = self._shot_queue.pop(0)[1]
                self._active_shot_start_time = time.time()
            else:
                if shot_requester:
                    shot_requester()
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
