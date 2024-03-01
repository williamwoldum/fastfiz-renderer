from typing import Optional, Tuple, Callable

import pygame
import fastfiz as ff

from GameTable import GameTable


class GameHandler:
    _instance = None
    _DEFAULT_SCALE = 400
    _DEFAULT_FRAMES_PER_SECOND = 60

    def __init__(self):
        if GameHandler._instance is None:
            self._is_playing: bool = False
            self._table_state: Optional[ff.TableState] = None
            self._game_table: Optional[GameTable] = None
            self._start_ball_positions: dict[int, Tuple[float, float]] = dict()
            self._shot_decider: Optional[Callable[[ff.TableState], ff.ShotParams]] = None
            GameHandler._instance = self
            pygame.init()
        else:
            raise Exception("This class is a singleton!")

    def __del__(self):
        pygame.quit()

    def play_eight_ball(self, shot_decider: Callable[[ff.TableState], ff.ShotParams], scale: int = _DEFAULT_SCALE,
                        frames_per_second: int = _DEFAULT_FRAMES_PER_SECOND):
        game_state: ff.GameState = ff.GameState.RackedState(ff.GT_EIGHTBALL)
        table_state: ff.TableState = game_state.tableState()
        self.play_game_from_table_state(table_state, shot_decider, scale, frames_per_second)

    def play_game_from_table_state(self, table_state: ff.TableState,
                                   shot_decider: Callable[[ff.TableState], ff.ShotParams], scale: int = _DEFAULT_SCALE,
                                   frames_per_second: int = _DEFAULT_FRAMES_PER_SECOND):
        self._is_playing = True
        self._table_state = table_state
        self._game_table = GameTable.from_table_state(table_state)
        self._load_start_balls()
        self._shot_decider = shot_decider

        display = pygame.display.set_mode((self._game_table.width * scale, self._game_table.length * scale))
        clock = pygame.time.Clock()

        while self._is_playing:
            pygame.display.flip()
            clock.tick(frames_per_second)

            self._game_table.update()
            self._game_table.draw(display, scale)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    elif event.key == pygame.K_r:
                        self._handle_restart()
                    elif event.key == pygame.K_RIGHT:
                        self._handle_shoot()

    def _handle_stop(self):
        self._is_playing = False

    def _handle_restart(self):
        for ball_number, pos in self._start_ball_positions.items():
            self._table_state.setBall(ball_number, ff.Ball.STATIONARY, pos[0], pos[1])
        self._game_table = GameTable.from_table_state(self._table_state)

    def _handle_shoot(self):
        params = self._shot_decider(self._table_state)
        shot = self._table_state.executeShot(params)
        self._game_table.add_shot(shot)

    def _load_start_balls(self):
        for i in range(ff.Ball.CUE, ff.Ball.FIFTEEN + 1):
            ball = self._table_state.getBall(i)
            pos = ball.getPos()
            self._start_ball_positions[ball.getID()] = (pos.x, pos.y)
