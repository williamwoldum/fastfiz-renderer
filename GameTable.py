import copy
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
        self.surface = pygame.display.set_mode((width, length))
        self.game_balls = game_balls

        self._shot_queue: list[ff.Shot] = []
        self._active_shot: Optional[ff.Shot] = None
        self._active_shot_start_time: float = 0
        self._game_ball_positions_before_shot: dict[int, Tuple[float, float]] = self._get_ball_positions()

    @classmethod
    def from_table_state(cls, table_state: ff.TableState):
        table: ff.Table = table_state.getTable()
        table_width = table.TABLE_WIDTH
        table_length = table.TABLE_LENGTH
        ball_radius = table_state.getBall(0).getRadius()
        game_balls = []

        raw_balls_data = table_state.toString().split(" ")[1:]
        chunked_ball_data = [raw_balls_data[i:i + 5] for i in range(0, len(raw_balls_data) - 1, 5)]

        for chunk in chunked_ball_data:
            game_balls.append(GameBall(ball_radius, int(chunk[2]), (float(chunk[3]), float(chunk[4]))))

        return cls(table_width, table_length, game_balls)

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

        if prev_state.e_time > time_since_shot_start:
            return ball.position

        if next_state.e_time < time_since_shot_start:
            return ball.position

        for i in range(len(relevant_states) - 1):
            state = relevant_states[i]
            if prev_state.e_time <= state.e_time <= time_since_shot_start:
                prev_state = state
            elif next_state.e_time > state.e_time > time_since_shot_start:
                next_state = state

        # print(f"\n{ball.number}")
        # for state in relevant_states:
        #     print(state)

        state_diff_pos = (next_state.pos[0] - prev_state.pos[0], next_state.pos[1] - prev_state.pos[1])

        if state_diff_pos[0] == 0 and state_diff_pos[1] == 0:
            return ball.position

        state_diff_pos_mag = math.sqrt(state_diff_pos[0] ** 2 + state_diff_pos[1] ** 2)
        next_state_vel_mag = math.sqrt(next_state.vel[0] ** 2 + next_state.vel[1] ** 2)
        normalized_state_diff_pos = (state_diff_pos[0] / state_diff_pos_mag, state_diff_pos[1] / state_diff_pos_mag)

        corrected_next_state_vel = (normalized_state_diff_pos[0] * next_state_vel_mag,
                                    normalized_state_diff_pos[1] * next_state_vel_mag)

        displacement_x = 0.5 * (prev_state.vel[0] + corrected_next_state_vel[0]) * time_since_shot_start
        displacement_y = 0.5 * (prev_state.vel[1] + corrected_next_state_vel[1]) * time_since_shot_start

        new_pos = (displacement_x + prev_state.pos[0], displacement_y + prev_state.pos[1])

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
