from fastfiz_renderer import DevUtils, GameHandler


def main():
    shot_decider = DevUtils.DevShotDeciders.get_north_shot_decider

    game_handler = GameHandler(window_pos=(300, 200), frames_per_second=120, scale=300)
    game_handler.play_eight_ball(shot_decider)
    # game_handler.play_game_from_table_state(DevUtils.DevTableStates.get_one_ball_state(), shot_decider)


if __name__ == '__main__':
    main()
