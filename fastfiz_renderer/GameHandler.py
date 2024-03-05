from typing import Tuple, Set

from p5 import *
import fastfiz as ff

from .GameTable import GameTable


class GameHandler:
    _instance = None
    ShotDecider = Callable[[ff.TableState], Optional[ff.ShotParams]]
    Game = Tuple[ff.TableState, ShotDecider]

    def __init__(self, mac_mode=False, window_pos: Tuple[int, int] = (100, 100), frames_per_second: int = 60,
                 scaling: int = 200):
        if GameHandler._instance is None:
            self._game_number: int = 0
            self._games: list[GameHandler.Game] = []
            self._game_table: Optional[GameTable] = None
            self._table_state: Optional[ff.TableState] = None
            self._start_ball_positions: dict[int, Tuple[float, float]] = dict()
            self._shot_decider: Optional[GameHandler.ShotDecider] = None

            self._mac_mode: bool = mac_mode
            self._window_pos: Tuple[int, int] = window_pos
            self._scaling: int = scaling
            self._frames_per_second: int = frames_per_second
            self._shot_speed_factor: float = 1

            GameHandler._instance = self
        else:
            raise Exception("This class is a singleton!")

    def play_eight_ball_games(self, shot_deciders: list[ShotDecider],
                              shot_speed_factor: float = 1,
                              auto_play: bool = False):
        games: list[GameHandler.Game] = []
        for decider in shot_deciders:
            game_state: ff.GameState = ff.GameState.RackedState(ff.GT_EIGHTBALL)
            table_state: ff.TableState = game_state.tableState()
            games.append((table_state, decider))

        self.play_games(games, shot_speed_factor, auto_play)

    def play_games(self, games: list[Game], shot_speed_factor: float = 1, auto_play: bool = False):
        if not games:
            raise Exception("No games provided!")

        self._games = games
        self._verify_table_dimensions()
        self._shot_speed_factor = shot_speed_factor
        self._handle_next_game()

        shot_requester = self._handle_shoot if auto_play else None

        def _setup():
            size(int(self._game_table.width * self._scaling), int(self._game_table.length * self._scaling))
            ellipseMode(CENTER)
            noStroke()

        def _draw():
            self._game_table.update(shot_requester)
            self._game_table.draw(self._scaling * 2 if self._mac_mode else self._scaling)

        def _key_released(event):
            if event.key == "RIGHT":
                self._handle_shoot()
            elif event.key == "r" or event.key == "R":
                self._handle_restart()
            elif event.key == "n" or event.key == "N":
                print(f"{self._game_number}: Game skipped")
                self._handle_next_game()

        run(renderer="skia", frame_rate=self._frames_per_second, sketch_draw=_draw, sketch_setup=_setup,
            sketch_key_released=_key_released, window_xpos=self._window_pos[0], window_ypos=self._window_pos[1],
            window_title="Cue Canvas")

    def _handle_next_game(self):
        if self._games:
            self._table_state, self._shot_decider = self._games.pop(0)
            self._game_table = GameTable.from_table_state(self._table_state, self._shot_speed_factor)
            self._game_number += 1
            self._load_start_balls()
        else:
            print("No more games left")
            exit()

    def _handle_restart(self):
        for ball_number, pos in self._start_ball_positions.items():
            self._table_state.setBall(ball_number, ff.Ball.STATIONARY, pos[0], pos[1])
        self._game_table = GameTable.from_table_state(self._table_state, self._shot_speed_factor)

    def _handle_shoot(self):
        if self._table_state.getBall(ff.Ball.CUE).isPocketed():
            print(f"{self._game_number}: Cue ball pocketed")
            self._handle_next_game()

        params = self._shot_decider(self._table_state)

        if params is None:
            print(f"{self._game_number}: No more shots left")
            self._handle_next_game()
        elif self._table_state.isPhysicallyPossible(params) != ff.TableState.OK_PRECONDITION:
            print(f"{self._game_number}: Shot not possible")
            self._handle_next_game()
        else:
            shot = self._table_state.executeShot(params)
            self._game_table.add_shot(params, shot)

    def _verify_table_dimensions(self):
        widths: Set[float] = {table.TABLE_WIDTH for table in
                              [table_state.getTable() for table_state in [game[0] for game in self._games]]}
        lengths: Set[float] = {table.TABLE_LENGTH for table in
                               [table_state.getTable() for table_state in [game[0] for game in self._games]]}

        if len(widths) > 1 or len(lengths) > 1:
            raise Exception("Games must have the same table width and length!")

    def _load_start_balls(self):
        for i in range(ff.Ball.CUE, ff.Ball.FIFTEEN + 1):
            ball = self._table_state.getBall(i)
            pos = ball.getPos()
            self._start_ball_positions[ball.getID()] = (pos.x, pos.y)
