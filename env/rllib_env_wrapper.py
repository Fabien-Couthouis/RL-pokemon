import asyncio
from threading import Thread
import numpy as np
from gym import spaces
from poke_env.player.env_player import Gen8EnvSinglePlayer
from typing import Any, Callable, List, Optional, Tuple, Union
from env.metrics import MetricsHandler
from env.observation import ObservationEncoder


class RllibGen8SinglePlayer(Gen8EnvSinglePlayer):
    def __init__(self, *args, **kwargs):
        Gen8EnvSinglePlayer.__init__(self)
        self._action_space = spaces.Discrete(22)
        # RLLIB casts observations to float64 while default dtype for Box is float32
        self._observation_space = spaces.Box(
            low=-10, high=10, shape=(10,), dtype=np.float64)
        self._metric_handler = MetricsHandler(self)
        self._observation_encoder = ObservationEncoder(self)

    @property
    def action_space(self):
        return self._action_space

    @property
    def observation_space(self):
        return self._observation_space

    def embed_battle(self, battle):
        obs = self._observation_encoder.encode_battle(battle)
        return obs

    def compute_reward(self, battle) -> float:
        return self.reward_computing_helper(
            battle, fainted_value=2, status_value=0.5, hp_value=1, victory_value=30
        )

    def reset(self) -> Any:
        observation = super().reset()
        return observation

    def step(self, action: int) -> Tuple:
        observation, reward, done, info = super().step(action)
        info["metrics"] = self._metric_handler.step_metrics(done)

        return observation, reward, done, info

    def challenge_user(self, env_algorithm, user_to_challenge, env_algorithm_kwargs=None):
        self._start_new_battle = True

        async def launch_battles(player):
            await player.send_challenges(opponent=user_to_challenge, n_challenges=1)

        def env_algorithm_wrapper(player, kwargs):
            env_algorithm(player, **kwargs)

            player._start_new_battle = False
            while True:
                try:
                    player.complete_current_battle()
                    player.reset()
                except OSError:
                    break

        loop = asyncio.get_event_loop()

        if env_algorithm_kwargs is None:
            env_algorithm_kwargs = {}

        thread = Thread(
            target=lambda: env_algorithm_wrapper(self, env_algorithm_kwargs)
        )
        thread.start()

        while self._start_new_battle:
            loop.run_until_complete(launch_battles(self))
        thread.join()


def rllib_env_creator(env_config):
    return RllibGen8SinglePlayer(**env_config)
