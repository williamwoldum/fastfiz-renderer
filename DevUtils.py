from random import random

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
    def get_biased_north_shot_decider(_: ff.TableState) -> ff.ShotParams:
        shot_params = ff.ShotParams()
        shot_params.v = 1.5
        shot_params.a = 0
        shot_params.b = 0
        shot_params.phi = 260 + random() * 20
        shot_params.theta = 11
        return shot_params
