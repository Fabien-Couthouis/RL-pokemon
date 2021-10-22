import numpy as np
from poke_env.environment.battle import Battle
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon


class ObservationEncoder():
    def __init__(self, env):
        self._env = env

    def general_obs(self, battle):
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

        weather = battle.weather
        weather_duration = 0
        turn = battle.turn
        trapped = battle.trapped

        player_side_conditions = self._retrieve_side_conditions(
            battle.side_conditions)
        opponent_side_conditions = self._retrieve_side_conditions(
            battle.opponent_side_conditions)

        fields = self._retrieve_fields(battle)

        general_obs = np.concatenate((
            moves_base_power,
            moves_dmg_multiplier,
            [remaining_mon_team, remaining_mon_opponent],
            [turn, weather, weather_duration, trapped],
            fields,
            player_side_conditions,
            opponent_side_conditions,
        ))

        return general_obs

    def _retrieve_side_conditions(self, in_side_conditions):
        """
        Side conditions (spikes, aurora veil...)
        https://poke-env.readthedocs.io/en/stable/other_environment.html#poke_env.environment.side_condition.SideCondition
        """
        side_conditions = []
        for side_condition, layer in sorted(in_side_conditions.items(), key=lambda item: item[0]):
            side_conditions.append(layer)
        return np.asarray(side_conditions)

    def _retrieve_fields(self, battle):
        """
        Fields
        """
        # TODO: improv this
        # Fields (terrains...) https://poke-env.readthedocs.io/en/stable/other_environment.html#poke_env.environment.field.Field
        fields, terrains = [], []
        for field, field_turn in sorted(battle.fields.items(), key=lambda item: item[0]):
            field_obs = battle.turn - field_turn
            if field.is_terrain:
                terrains.append(field_obs)
            else:
                fields.append(field_obs)
                return terrains + fields

    def pokemons_obs(self, battle):
        player_mon_obs = [self._mon_obs(opponent_mon)
                          for opponent_mon in battle.team.values()]
        opponent_mon_obs = [self._mon_obs(
            opponent_mon) for opponent_mon in battle.opponent_team.values()]

        # Pad opponent_mon_obs when full opponent_team is not known (random battle)
        opponent_mon_obs = np.pad(
            opponent_mon_obs, ((0, 6-len(opponent_mon_obs)), (0, 0)), constant_values=-1)

        pokemon_obs = np.concatenate(
            (player_mon_obs, opponent_mon_obs), axis=0)
        # TODO: do not flatten to treat all pokemon inputs using the same layer in the model
        return pokemon_obs.flatten()

    def _move_obs(self, move: Move):
        pass

    def _mon_obs(self, mon: Pokemon):
        # TODO inputs normalization
        mon_obs = []
        # TODO: handle ability items and moves (embedding?)

        # General mon info
        # Type
        mon_obs.append(mon.type_1)
        mon_obs.append(mon.type_2)
        # Stats
        mon_obs.append(mon.base_stats.values())
        mon_obs.append(mon.stats.values())
        # use stats diff? Norm?

        # Contextual mon info
        # Is active
        mon_obs.append(mon.active)
        # Fainted
        mon_obs.append(mon.fainted)
        # First turn / reveal
        mon_obs.append(mon.first_turn)
        mon_obs.append(mon.revealed)

        # Status
        mon_obs.append(mon.status)
        mon_obs.append(mon.status_counter)
        # Hps
        mon_obs.append(mon.current_hp_fraction)
        mon_obs.append(mon.current_hp)
        # Recharge
        mon_obs.append(mon.must_recharge)

        # Other info
        mon_obs.append(mon.gender)
        mon_obs.append(mon.weight)

        # Order of boosts: accuracy, atk, def, evasion, spa, spd, spe
        # TODO: Divide by 4?
        mon_obs.append(mon.boosts.values())

        # Item
        # mon_obs.append(mon.item)
        # Moves
        # moves_inputs = [self.retrieve_move_obs(move) for move in mon.moves]
        # mon.possible_abilities
        return np.asarray(mon_obs)

    def encode_battle(self, battle: Battle):
        general_obs = self.general_obs(battle)
        pokemons_obs = self.pokemons_obs(battle)
        return np.concatenate(
            (
                general_obs,
                pokemons_obs,
            ), axis=0
        )
