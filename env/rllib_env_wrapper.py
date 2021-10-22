import asyncio
from threading import Thread
import numpy as np
from gym import spaces
from poke_env.player.env_player import Gen8EnvSinglePlayer
from typing import Any, Callable, List, Optional, Tuple, Union
from env.metrics import MetricsHandler


class RllibGen8SinglePlayer(Gen8EnvSinglePlayer):
    def __init__(self, *args, **kwargs):
        Gen8EnvSinglePlayer.__init__(self)
        self._action_space = spaces.Discrete(22)
        self._observation_space = spaces.Box(low=-10, high=10, shape=(10,), dtype=np.float64) # RLLIB casts observations to float64 while default dtype for Box is float32
        self._metric_handler = MetricsHandler(self)

    @property
    def action_space(self):
        return self._action_space

    @property
    def observation_space(self):
        return self._observation_space

    def embed_battle(self, battle):
        # -1 indicates that the move does not have a base power
        # or is not available
        moves_base_power = -np.ones(4)
        moves_dmg_multiplier = np.ones(4)
        for i, move in enumerate(battle.available_moves):
            moves_base_power[i] = (
                move.base_power / 100
            )  # Simple rescaling to facilitate learning
            if move.type:
                moves_dmg_multiplier[i] = move.type.damage_multiplier(
                    battle.opponent_active_pokemon.type_1,
                    battle.opponent_active_pokemon.type_2,
                )

        # We count how many pokemons have not fainted in each team
        remaining_mon_team = (
            len([mon for mon in battle.team.values() if mon.fainted]) / 6
        )
        remaining_mon_opponent = (
            len([mon for mon in battle.opponent_team.values() if mon.fainted]) / 6
        )

        # Final vector with 10 components
        return np.concatenate(
            [
                moves_base_power,
                moves_dmg_multiplier,
                [remaining_mon_team, remaining_mon_opponent],
            ]
        )

    def compute_reward(self, battle) -> float:
        return self.reward_computing_helper(
            battle, fainted_value=2, hp_value=1, victory_value=30
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
