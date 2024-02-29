from typing import Optional

import pygame
import fastfiz as ff

from GameTable import GameTable


class GameHandler:
    _instance = None
    _SCALE = 400
    _FRAMES_PER_SECOND = 60

    def __init__(self):
        if GameHandler._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            GameHandler._instance = self
            pygame.init()
            self.table_state: Optional[ff.TableState] = None

    def __del__(self):
        pygame.quit()

    def play_eight_ball(self, scale: int = _SCALE, frames_per_second: int = _FRAMES_PER_SECOND):
        game_state: ff.GameState = ff.GameState.RackedState(ff.GT_EIGHTBALL)
        table_state: ff.TableState = game_state.tableState()
        self.play_game_from_table_state(table_state, scale, frames_per_second)

    def play_game_from_table_state(self, table_state: ff.TableState, scale: int = _SCALE,
                                   frames_per_second: int = _FRAMES_PER_SECOND):
        self.table_state = table_state
        game_table = GameTable.from_table_state(table_state)
        display = pygame.display.set_mode((game_table.width * scale, game_table.length * scale))
        clock = pygame.time.Clock()

        while True:
            pygame.display.flip()
            clock.tick(frames_per_second)

            game_table.update()
            game_table.draw(display, scale)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    elif event.key == pygame.K_RIGHT:
                        shot = self._get_next_shot()
                        game_table.add_shot(shot)

    def _get_next_shot(self) -> ff.Shot:
        shot_params = ff.ShotParams()
        shot_params.v = 10
        shot_params.a = 0
        shot_params.b = 0
        shot_params.phi = 270
        shot_params.theta = 11
        return self.table_state.executeShot(shot_params)
