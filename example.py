from fastfiz_renderer import DevUtils, GameHandler


def main():
    game_handler = GameHandler(window_pos=(300, 200), frames_per_second=120, scaling=300, mac_mode=True)

    # Play 8-ball games with each their shot decider
    shot_deciders = [
        DevUtils.DevShotDeciders.north_shot_decider,
        DevUtils.DevShotDeciders.biased_north_shot_decider
    ]
    game_handler.play_eight_ball_games(shot_deciders, shot_speed_factor=3, auto_play=True)

    # Play a game from any table state with each their shot decider
    table_states = [
        DevUtils.DevTableStates.get_one_ball_state(),
        DevUtils.DevTableStates.get_two_ball_state()
    ]
    games = [(state, decider) for state, decider in zip(table_states, shot_deciders)]
    game_handler.play_games(games)

    # Convert shot histories into shot deciders
    shot_params = [
        DevUtils.DevShotDeciders.north_shot_decider(table_states[0]),
        DevUtils.DevShotDeciders.north_shot_decider(table_states[0])
    ]

    decider = DevUtils.DevShotDeciders.get_from_shot_params_list(shot_params)
    games = [(table_states[0], decider)]
    game_handler.play_games(games)


if __name__ == '__main__':
    main()
