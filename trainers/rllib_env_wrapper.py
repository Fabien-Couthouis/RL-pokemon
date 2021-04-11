from poke_env.player.env_player import Gen8EnvSinglePlayer
import numpy as np

class RLLIBGen8SinglePlayer(Gen8EnvSinglePlayer):

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

def rllib_env_creator(env_config):
    return env_config["instance"]

def rllib_training(player, trainer, n_iters, save_freq, save_dir):
    for i in range(n_iters):
        trainer.train()
        if (i % save_freq) == 0:
            trainer.save(save_dir) 

    # This call will finished eventual unfinshed battles before returning
    player.complete_current_battle()

def rllib_evaluation(player, trainer, nb_episodes):
    # Reset battle statistics
    player.reset_battles()

    for i in range(nb_episodes):
        done = False
        obs = player.reset()
        while not done:
            action = trainer.compute_action(obs)
            obs, reward, done, info = player.step(action)
    
    print(
        "Player Evaluation: %d victories out of %d episodes"
        % (player.n_won_battles, nb_episodes)
    )