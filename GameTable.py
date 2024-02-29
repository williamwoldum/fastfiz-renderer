import math
import time
from typing import Optional, Tuple

import fastfiz as ff
import pygame

from GameBall import GameBall


class GameTable:
    def __init__(self, width: float, length: float, game_balls: list[GameBall]):
        self.width = width
        self.length = length
        self.game_balls = game_balls

        self._shot_queue: list[ff.Shot] = []
        self._active_shot: Optional[ff.Shot] = None
        self._active_shot_start_time: float = 0
        self._game_ball_positions_before_shot: dict[int, Tuple[float, float]] = self._get_ball_positions()

    @classmethod
    def from_table_state(cls, table_state: ff.TableState):
        game_balls = []

        for i in range(ff.Ball.CUE, ff.Ball.FIFTEEN + 1):
            ball = table_state.getBall(i)
            pos = ball.getPos()
            game_balls.append(GameBall(ball.getRadius(), ball.getID(), (pos.x, pos.y)))

        table: ff.Table = table_state.getTable()

        return cls(table.TABLE_WIDTH, table.TABLE_LENGTH, game_balls)

    def add_shot(self, shot: ff.Shot):
        self._shot_queue.append(shot)

        # for event in shot.getEventList():
        #     print(event.toString())
        #     print()

    def draw(self, screen: pygame.Surface, scale=300):
        pygame.draw.rect(screen, (6, 128, 63), (0, 0, self.width * scale, self.length * scale))

        for ball in self.game_balls:
            ball.draw(screen, scale)

    def update(self):
        if self._active_shot is None:
            if self._shot_queue:
                self._active_shot = self._shot_queue.pop(0)
                self._active_shot_start_time = time.time()
            else:
                return

        time_since_shot_start = time.time() - self._active_shot_start_time

        if time_since_shot_start > self._active_shot.getDuration():
            self._force_balls_to_correct_pos()
            self._game_ball_positions_before_shot = self._get_ball_positions()
            self._active_shot = None
            return

        else:
            for ball in self.game_balls:
                ball.position = self._calc_ball_position(ball, time_since_shot_start)

    def _get_ball_positions(self) -> dict[int, Tuple[float, float]]:
        positions = dict()
        for ball in self.game_balls:
            positions[ball.number] = (ball.position[0], ball.position[1])
        return positions

    def _get_relevant_ball_states_from_active_shot(self, ball: GameBall):
        relevant_states: list[_BallState] = []

        for event in self._active_shot.getEventList():
            event: ff.Event
            if event.getBall1() == ball.number:
                new_ball_event = _BallState.from_event_and_ball(event, event.getBall1Data())
                relevant_states.append(new_ball_event)
            elif event.getBall2() == ball.number:
                new_ball_event = _BallState.from_event_and_ball(event, event.getBall2Data())
                relevant_states.append(new_ball_event)

        return relevant_states

    def _force_balls_to_correct_pos(self):
        for ball in self.game_balls:
            relevant_states = self._get_relevant_ball_states_from_active_shot(ball)
            if relevant_states:
                ball.position = relevant_states[-1].pos

    def _calc_ball_position(self, ball: GameBall, time_since_shot_start: float) -> Tuple[float, float]:
        relevant_states = self._get_relevant_ball_states_from_active_shot(ball)

        if not relevant_states:
            return ball.position

        prev_state: _BallState = relevant_states[0]
        next_state: _BallState = relevant_states[-1]

        if prev_state.e_time > time_since_shot_start or next_state.e_time < time_since_shot_start:
            return ball.position

        for state in relevant_states:
            if prev_state.e_time < state.e_time <= time_since_shot_start:
                prev_state = state
            elif next_state.e_time > state.e_time > time_since_shot_start:
                next_state = state

        # print(f"\n{ball.number}")
        # for state in relevant_states:
        #     print(state)

        pos_diff = (next_state.pos[0] - prev_state.pos[0], next_state.pos[1] - prev_state.pos[1])
        pos_diff_mag = math.sqrt(pos_diff[0] ** 2 + pos_diff[1] ** 2)

        if pos_diff_mag == 0:
            return ball.position

        prev_state_vel_mag = math.sqrt(prev_state.vel[0] ** 2 + prev_state.vel[1] ** 2)
        next_state_vel_mag = math.sqrt(next_state.vel[0] ** 2 + next_state.vel[1] ** 2)


        normalized_pos_diff = (pos_diff[0] / pos_diff_mag, pos_diff[1] / pos_diff_mag)

        corrected_prev_state_vel = (normalized_pos_diff[0] * prev_state_vel_mag,
                                    normalized_pos_diff[1] * prev_state_vel_mag)

        corrected_next_state_vel = (normalized_pos_diff[0] * next_state_vel_mag,
                                    normalized_pos_diff[1] * next_state_vel_mag)

        time_since_event_start = time_since_shot_start - prev_state.e_time

        displacement_x = ((corrected_next_state_vel[0] - corrected_prev_state_vel[0]) * (time_since_event_start ** 2)) / ((next_state.e_time - prev_state.e_time) * 2)
        displacement_y = ((corrected_next_state_vel[1] - corrected_prev_state_vel[1]) * (time_since_event_start ** 2)) / ((next_state.e_time - prev_state.e_time) * 2)

        new_pos = (displacement_x + prev_state.pos[0], displacement_y + prev_state.pos[1])




        # a_x = (next_state.pos[0] - prev_state.pos[0]) / (next_state.e_time - prev_state.e_time)
        # b_x = (prev_state.pos[0] - a_x * prev_state.e_time)
        #
        # a_y = (next_state.pos[1] - prev_state.pos[1]) / (next_state.e_time - prev_state.e_time)
        # b_y = (prev_state.pos[1] - a_y * prev_state.e_time)
        #
        # new_pos = (a_x * time_since_shot_start + b_x, a_y * time_since_shot_start + b_y)

        return new_pos


class _BallState:
    def __init__(self, e_time: float, pos: Tuple[float, float], vel: Tuple[float, float], state: str):
        self.e_time = e_time
        self.pos = pos
        self.vel = vel
        self.state = state

    @classmethod
    def from_event_and_ball(cls, event: ff.Event, ball: ff.Ball):
        e_time = event.getTime()
        pos = ball.getPos()
        vel = ball.getVelocity()
        state = ball.getStateString()
        return cls(e_time, (pos.x, pos.y), (vel.x, vel.y), state)

    def __str__(self):
        return (f"Time: {self.e_time},\t "
                f"Pos: ({self.pos[0]:.4f}, {self.pos[1]:.4f}),\t "
                f"Vel: ({self.vel[0]:.4f}, {self.vel[1]:.4f}),\t "
                f"State: {self.state}")
