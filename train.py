import time
from functools import partial
from pathlib import Path
from typing import Dict

import ray
import yaml
from gym import logger
from poke_env.player.random_player import RandomPlayer
from ray.rllib.agents.callbacks import MultiCallbacks
from ray.rllib.models import ModelCatalog
from ray.tune.logger import pretty_print
from ray.tune.registry import get_trainable_cls, register_env
from tabulate import tabulate

from callbacks.metrics import MetricsCallbacks
from callbacks.tbx_callback import TBXCallback
from env.rllib_env_wrapper import RllibGen8SinglePlayer, rllib_env_creator
from models.rnn_model import PokeLSTM

CONFIG_FILE = Path("configs/config.yaml")


def load_config():
    with open(CONFIG_FILE) as f:
        # Load config file
        config = yaml.safe_load(f)
    return config


def load_trainer(config: Dict, exp_dir: Path):
    training_config = config["training"]
    run = training_config["run"]
    common_config = training_config["common_config"]
    agent_specific_config = training_config["specific_config"].get(run, {})

    Trainer = get_trainable_cls(run)
    # Merge common_config and agent_specific_config
    trainer_config = dict(common_config, **agent_specific_config)
    # Add metric callback
    trainer_config["callbacks"] = MultiCallbacks([MetricsCallbacks,
                                                  partial(TBXCallback, logdir=str(exp_dir))])
    trainer = Trainer(config=trainer_config)
    return trainer


def create_result_table(result: Dict, round_decimal=2):
    result_keys = ["training_iteration", "episodes_total", "time_total_s",
                   "episode_len_mean", "episode_reward_mean"]
    learner_stats = result["info"]["learner"]["default_policy"]["learner_stats"]
    learner_stats_keys = learner_stats.keys() #["policy_loss", "vf_loss"]
    custom_metrics = result["custom_metrics"]
    custom_metrics_keys = ["won_mean"]

    table = []
    for key in result_keys:
        table.append([key, round(result[key], round_decimal)])
    for key in learner_stats_keys:
        table.append([key, round(learner_stats[key], round_decimal)])
    for key in custom_metrics_keys:
        table.append([key, round(custom_metrics[key], round_decimal)])

    return table


def train(player, trainer, n_iters, checkpoint_freq, exp_dir):
    for i in range(n_iters):
        result = trainer.train()
        if (i % checkpoint_freq) == 0:
            trainer.save(exp_dir)

        # pretty_result = pretty_print(result)
        # print(f"{pretty_result}\n\n End of iter {i}.")

        result_table = create_result_table(result)
        print(tabulate(result_table, tablefmt="pretty"))

    # This call will finished eventual unfinshed battles before returning
    player.complete_current_battle()


def evaluate(player, trainer, nb_episodes):
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


def launch_training():
    ray.init(ignore_reinit_error=True)
    register_env("pokeEnv", rllib_env_creator)
    ModelCatalog.register_custom_model("poke_lstm", PokeLSTM)

    # Load some stuff before training
    config = load_config()

    training_config = config["training"]
    # TODO: use other stop criterions?
    n_iters = training_config["stop"]["training_iteration"]
    checkpoint_freq = training_config["checkpoint_freq"]
    exp_dir = Path(
        training_config["local_dir"],
        f'{training_config["name"]}-{time.strftime("%Y %m %d-%H %M %S")}'
    )
    exp_dir.mkdir(parents=True, exist_ok=True)

    # Training
    trainer = load_trainer(config, exp_dir)
    env_player = trainer.workers.local_worker().env
    # TODO: make this configurable
    opponent = "hardcoded_bot_3340"
    env_player.challenge_user(
        env_algorithm=train,
        user_to_challenge=opponent,
        env_algorithm_kwargs={
            "trainer": trainer,
            "n_iters": n_iters,
            "checkpoint_freq": checkpoint_freq,
            "exp_dir": exp_dir
        })

    # Evaluation

    # env_player.play_against(
    #     env_algorithm=evaluate,
    #     opponent=opponent,
    #     env_algorithm_kwargs={"trainer": trainer, "nb_episodes": 10}
    # )


def main():
    launch_training()


if __name__ == "__main__":
    main()
