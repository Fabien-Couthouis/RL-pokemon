import numpy as np
from poke_env.player.env_player import Player


class MetricsHandler():
    def __init__(self, player: Player):
        self._player = player
        self._metrics = None

    def log_reset_metrics(self):
        self._metrics = {
            "end": {
                "is_won": None,
                "is_lost": None,
                "nb_alive_pokemons": None,
                "nb_alive_pokemon_enemy": None,
            },
            "step": {}
        }

    def step_metrics(self, done: bool):
        """
        Retriev step metrics
        """
        metrics = {}
        if done:
            battle = self._player._current_battle
            metrics["end"] = {"won": battle.won,
                              "lost": battle.lost,
                              "nb_alive_pokemons": sum([not mon.fainted for mon in battle.team.values()]),
                              "nb_alive_pokemon_enemy": sum([not mon.fainted for mon in battle.opponent_team.values()]),
                              }

        return metrics
