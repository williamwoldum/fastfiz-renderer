from random import random
from typing import Optional, Callable

import fastfiz as ff


class DevTableStates:
    @staticmethod
    def get_one_ball_state():
        game_state: ff.GameState = ff.GameState.RackedState(ff.GT_EIGHTBALL)
        table_state: ff.TableState = game_state.tableState()
        for i in range(ff.Ball.ONE, ff.Ball.FIFTEEN + 1):
            table_state.setBall(i, ff.Ball.NOTINPLAY, 0, 0)
        return table_state

    @staticmethod
    def get_two_ball_state():
        game_state: ff.GameState = ff.GameState.RackedState(ff.GT_EIGHTBALL)
        table_state: ff.TableState = game_state.tableState()
        for i in range(ff.Ball.TWO, ff.Ball.FIFTEEN + 1):
            table_state.setBall(i, ff.Ball.NOTINPLAY, table_state.getBall(i).getPos())
        return table_state


class DevShotDeciders:
    @staticmethod
    def get_from_shot_params_list(shot_params_list: list[ff.ShotParams]) -> Callable[
        [ff.TableState], Optional[ff.ShotParams]]:
        def decider(_: ff.TableState) -> Optional[ff.ShotParams]:
            if shot_params_list:
                return shot_params_list.pop(0)
            else:
                return None

        return decider

    @staticmethod
    def biased_north_shot_decider(_: ff.TableState) -> ff.ShotParams:
        shot_params = ff.ShotParams()
        shot_params.v = 1.5
        shot_params.a = 0
        shot_params.b = 0
        shot_params.phi = 260 + random() * 20
        shot_params.theta = 11
        return shot_params

    @staticmethod
    def north_shot_decider(_: ff.TableState) -> ff.ShotParams:
        shot_params = ff.ShotParams()
        shot_params.v = 1.5
        shot_params.a = 0
        shot_params.b = 0
        shot_params.phi = 270
        shot_params.theta = 11
        return shot_params

    @staticmethod
    def hole_shot_decider(_: ff.TableState) -> ff.ShotParams:
        shot_params = ff.ShotParams()
        shot_params.v = 1
        shot_params.a = 0
        shot_params.b = 0
        shot_params.phi = 45
        shot_params.theta = 11
        return shot_params
