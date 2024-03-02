import time
from typing import Optional

import fastfiz as ff
import pygame
import vectormath as vmath

from GameBall import GameBall


class GameTable:
    def __init__(self, width: float, length: float, rolling_friction_const: float,
                 sliding_friction_const: float, gravitational_const: float, game_balls: list[GameBall]):
        self.width = width
        self.length = length
        self.rolling_friction_const = rolling_friction_const
        self.sliding_friction_const = sliding_friction_const
        self.gravitational_const = gravitational_const
        self.game_balls = game_balls

        self._shot_queue: list[ff.Shot] = []
        self._active_shot: Optional[ff.Shot] = None
        self._active_shot_start_time: float = 0

    @classmethod
    def from_table_state(cls, table_state: ff.TableState):
        game_balls = []

        for i in range(ff.Ball.CUE, ff.Ball.FIFTEEN + 1):
            ball: ff.Ball = table_state.getBall(i)
            pos = ball.getPos()
            game_balls.append(GameBall(ball.getRadius(), ball.getID(), vmath.Vector2(pos.x, pos.y), ball.getState()))

        table: ff.Table = table_state.getTable()

        return cls(table.TABLE_WIDTH, table.TABLE_LENGTH, table.MU_ROLLING, table.MU_SLIDING, table.g, game_balls)

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
            self._active_shot = None
            return

        else:
            for ball in self.game_balls:
                ball.position = self._calc_ball_position(ball, time_since_shot_start)

    def _get_ball_positions(self) -> dict[int, vmath.Vector2]:
        positions = dict()
        for ball in self.game_balls:
            positions[ball.number] = vmath.Vector2(ball.position[0], ball.position[1])
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

    def _calc_ball_position(self, ball: GameBall, time_since_shot_start: float) -> vmath.Vector2:
        relevant_states = self._get_relevant_ball_states_from_active_shot(ball)

        if not relevant_states:
            return ball.position

        cur_state: _BallState = relevant_states[0]

        if cur_state.e_time > time_since_shot_start:
            return ball.position

        for state in relevant_states:
            if cur_state.e_time < state.e_time <= time_since_shot_start:
                cur_state = state

        # print(f"\n{ball.number}")
        # for state in relevant_states:
        #     print(state)

        time_since_event_start = time_since_shot_start - cur_state.e_time

        def calc_sliding_displacement(delta_time: float) -> vmath.Vector2:
            rotational_velocity: vmath.Vector3 = ball.radius * vmath.Vector3(0, 0, cur_state.ang_vel.z).cross(cur_state.ang_vel)
            relative_velocity = cur_state.vel + vmath.Vector2(rotational_velocity.x, rotational_velocity.y)
            return cur_state.vel * delta_time - 0.5 * self.sliding_friction_const * self.gravitational_const * delta_time ** 2 * relative_velocity.normalize()

        def calc_rolling_displacement(delta_time: float) -> vmath.Vector2:
            return cur_state.vel * delta_time - 0.5 * self.rolling_friction_const * self.gravitational_const * delta_time ** 2 * cur_state.vel.copy().normalize()

        displacement = vmath.Vector2(0, 0)

        if cur_state.state == ff.Ball.ROLLING:
            displacement = calc_rolling_displacement(time_since_event_start)
        if cur_state.state == ff.Ball.SLIDING:
            displacement = calc_sliding_displacement(time_since_event_start)

        return displacement + cur_state.pos


class _BallState:
    def __init__(self, e_time: float, pos: vmath.Vector2, vel: vmath.Vector2, ang_vel: vmath.Vector3, state: int,
                 state_str: str,
                 event_course: int):
        self.e_time = e_time
        self.pos = pos
        self.vel = vel
        self.ang_vel = ang_vel
        self.state = state
        self.state_str = state_str
        self.event_course = event_course

    @classmethod
    def from_event_and_ball(cls, event: ff.Event, ball: ff.Ball):
        e_time = event.getTime()
        pos = ball.getPos()
        vel = ball.getVelocity()
        ang_vel = ball.getSpin()
        state = ball.getState()
        state_str = ball.getStateString()
        event_course = event.getType()
        return cls(e_time, vmath.Vector2([pos.x, pos.y]), vmath.Vector2([vel.x, vel.y]),
                   vmath.Vector3([ang_vel.x, ang_vel.y, ang_vel.z]), state, state_str, event_course)

    def __str__(self):
        return (f"Time: {self.e_time:.3f},\t "
                f"Pos: ({self.pos.x:.3f}, {self.pos.y:.3f}),\t "
                f"Vel: ({self.vel.x:.3f}, {self.vel.y:.3f}),\t "
                f"State: {self.state_str}")
