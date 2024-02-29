import os

from GameHandler import GameHandler


def main():
    os.environ['SDL_VIDEO_WINDOW_POS'] = "100, 100"
    game_handler = GameHandler()
    game_handler.play_eight_ball()


if __name__ == '__main__':
    main()
