import fastfiz as ff
from p5 import *
import vectormath as vmath

from .GameBall import GameBall


class GameTable:
    def __init__(self, width: float, length: float, side_pocket_width: float, corner_pocket_width: float,
                 rolling_friction_const: float, sliding_friction_const: float, gravitational_const: float,
                 game_balls: list[GameBall]):
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

        return cls(table.TABLE_WIDTH, table.TABLE_LENGTH, table.SIDE_POCKET_WIDTH, table.CORNER_POCKET_WIDTH,
                   table.MU_ROLLING, table.MU_SLIDING, table.g, game_balls)

    def add_shot(self, shot: ff.Shot):
        self._shot_queue.append(shot)

        # for event in shot.getEventList():
        #     print(event.toString())
        #     print()

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
            rotational_velocity: vmath.Vector3 = ball.radius * vmath.Vector3(0, 0, cur_state.ang_vel.z).cross(
                cur_state.ang_vel)
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
