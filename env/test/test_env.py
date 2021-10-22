import pytest
from env.rllib_env_wrapper import RllibGen8SinglePlayer
from poke_env.player.random_player import RandomPlayer


def test_launching_env():
    env = RllibGen8SinglePlayer()

    def evaluate(player):
        # Reset battle statistics
        player.reset_battles()

        n_episodes = 3
        for i in range(n_episodes):
            done = False
            obs = player.reset()
            while not done:
                action = player.action_space.sample()
                obs, reward, done, info = player.step(action)
                print(obs)

    opponent = RandomPlayer()
    env.play_against(
        env_algorithm=evaluate,
        opponent=opponent,
    )


if __name__ == "__main__":
    test_launching_env()
