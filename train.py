import time
from pathlib import Path
from typing import Dict

import ray
import yaml
from gym import logger
from poke_env.player.random_player import RandomPlayer
from ray.tune.registry import get_trainable_cls, register_env

from env.rllib_env_wrapper import (RllibGen8SinglePlayer, rllib_env_creator)

CONFIG_FILE = Path("configs/config.yaml")


def load_config():
    with open(CONFIG_FILE) as f:
        # Load config file
        config = yaml.safe_load(f)
    return config


def load_trainer(config: Dict):
    training_config = config["training"]
    run = training_config["run"]
    common_config = training_config["common_config"]
    agent_specific_config = training_config["specific_config"].get(run, {})

    Trainer = get_trainable_cls(run)
    # Merge common_config and agent_specific_config
    trainer_config = dict(common_config, **agent_specific_config)
    trainer = Trainer(config=trainer_config, env=RllibGen8SinglePlayer)  # env=
    return trainer


def train(player, trainer, n_iters, checkpoint_freq, exp_dir):
    for i in range(n_iters):
        result = trainer.train()
        if (i % checkpoint_freq) == 0:
            trainer.save(exp_dir)
        print(f"End of iter {i}: {result}", "\n"*10)
        # TODO: better logging with losses, rewards, win ratio...
        # it is possible to use the function from Tune to build the array

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

    # Load some stuff before training
    config = load_config()
    trainer = load_trainer(config)

    training_config = config["training"]
    # TODO: use other stop criterions?
    n_iters = training_config["stop"]["training_iteration"]
    checkpoint_freq = training_config["checkpoint_freq"]
    exp_dir = Path(
        training_config["local_dir"],
        f'{training_config["name"]}-{time.strftime("%Y %m %d-%H %M %S")}'
    )
    # TODO: callbacks to log useful metrics: win ratio...
    exp_dir.mkdir(parents=True, exist_ok=True)

    # Training
    env_player = trainer.workers.local_worker().env
    # TODO: make this configurable
    opponent = RandomPlayer()
    env_player.play_against(
        env_algorithm=train,
        opponent=opponent,
        env_algorithm_kwargs={
            "trainer": trainer,
            "n_iters": n_iters,
            "checkpoint_freq": checkpoint_freq,
            "exp_dir": exp_dir
        })

    print("Finished training")
    print("Starting evaluation...")

    # Evaluation
    # TODO: evaluate agent during training?
    env_player.play_against(
        env_algorithm=evaluate,
        opponent=opponent,
        env_algorithm_kwargs={"trainer": trainer, "nb_episodes": 10}
    )


def main():
    launch_training()


if __name__ == "__main__":
    main()