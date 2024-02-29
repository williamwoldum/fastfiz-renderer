import fastfiz
import fastfiz as ff
import pygame
import sys
import os

from GameTable import GameTable

SCALE = 400


def get_next_shot(table_state: ff.TableState) -> ff.Shot:
    shot_params = ff.ShotParams()
    shot_params.v = 10
    shot_params.a = 0
    shot_params.b = 0
    shot_params.phi = 270
    shot_params.theta = 11
    return table_state.executeShot(shot_params)


def render_game_table(game_table: GameTable, table_state: ff.TableState):
    pygame.init()

    display = pygame.display.set_mode((game_table.width * SCALE, game_table.length * SCALE))
    clock = pygame.time.Clock()
    frames_per_second = 60

    while True:
        pygame.display.flip()
        clock.tick(frames_per_second)
        #print(clock.get_fps())

        game_table.update()
        game_table.draw(display, SCALE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    shot = get_next_shot(table_state)
                    game_table.add_shot(shot)


def main():
    gs: ff.GameState = ff.GameState.RackedState(fastfiz.GT_EIGHTBALL)
    ts: ff.TableState = gs.tableState()

    # for i in range(1, 16):
    #     if i in [2]:
    #         pass
    #     else:
    #         ts.setBall(i, ff.Ball.NOTINPLAY, 0, 0)

    gt = GameTable.from_table_state(ts)
    render_game_table(gt, ts)


if __name__ == '__main__':
    os.environ['SDL_VIDEO_WINDOW_POS'] = "100, 100"
    main()
