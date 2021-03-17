import os.path
import time
from os import mkdir

import gym
import numpy as np
import ray
from gym import logger
from gym_showdown.envs import ShowdownEnv
from ray import tune
from ray.rllib.agents.ppo import PPOTrainer
from ray.rllib.contrib.alpha_zero.core.alpha_zero_trainer import \
    AlphaZeroTrainer
from ray.tune.registry import register_env
from showdown_monitor import ShowdownMonitor

from .base_agent import BaseTrainer


class AlphaZeroTrainer(BaseTrainer):
    """An trainer inspired by AlphaZero from DeepMind"""

    def __init__(self, action_space):
        super.__init__(action_space)

    def act(self, observation: np.ndarray, reward: float, done: bool):
        return self.action_space.sample()


def showdown_env_creator(env_config):
    return ShowdownEnv(login_path=env_config['login_path'], team_path=env_config['team_path'], tier=env_config['tier'])


if __name__ == '__main__':
    # You can set the level to logger.DEBUG or logger.WARN if you
    # want to change the amount of output.
    logger.set_level(logger.INFO)

    ray.init(ignore_reinit_error=True)

    register_env('showdownEnv', showdown_env_creator)

    #env = gym.make('gym_showdown:showdown-v0', login_path=os.path.abspath('data/login.txt'), team_path=os.path.abspath('data/hyper_offense.txt'))

    # You provide the directory to write to (can be an existing
    # directory, including one with existing data -- all monitor files
    # will be namespaced). You can also dump to a tempdir if you'd
    # like: tempfile.mkdtemp().
    outdir = '/tmp/alphazero-agent-results'
    #env = ShowdownMonitor(env, directory=outdir, force=True)

    config = {
        "env": None,
        # Size of batches collected from each worker
        "rollout_fragment_length": 200,
        # Number of timesteps collected for each SGD round
        "train_batch_size": 4000,
        # Total SGD batch size across all devices for SGD
        "sgd_minibatch_size": 128,
        # Whether to shuffle sequences in the batch when training (recommended)
        "shuffle_sequences": True,
        # Number of SGD iterations in each outer loop
        "num_sgd_iter": 30,
        # IN case a buffer optimizer is used
        "learning_starts": 1000,
        # Size of the replay buffer in batches (not timesteps!).
        "buffer_size": 1000,
        # Stepsize of SGD
        "lr": 5e-5,
        # Learning rate schedule
        "lr_schedule": None,
        # Share layers for value function. If you set this to True, it"s important
        # to tune vf_loss_coeff.
        "vf_share_layers": False,
        # Whether to rollout "complete_episodes" or "truncate_episodes"
        "batch_mode": "complete_episodes",
        # Which observation filter to apply to the observation
        "observation_filter": "NoFilter",
        # Uses the sync samples optimizer instead of the multi-gpu one. This does
        # not support minibatches.
        "simple_optimizer": True,

        # === MCTS ===
        "mcts_config": {
            "puct_coefficient": 1.0,
            "num_simulations": 30,
            "temperature": 1.5,
            "dirichlet_epsilon": 0.25,
            "dirichlet_noise": 0.03,
            "argmax_tree_policy": False,
            "add_dirichlet_noise": True,
        },

        # === Ranked Rewards ===
        # implement the ranked reward (r2) algorithm
        # from: https://arxiv.org/pdf/1807.01672.pdf
        "ranked_rewards": {
            "enable": True,
            "percentile": 75,
            "buffer_max_length": 1000,
            # add rewards obtained from random policy to
            # "warm start" the buffer
            "initialize_buffer": True,
            "num_init_rewards": 100,
        },

        # === Evaluation ===
        # Extra configuration that disables exploration.
        "evaluation_config": {
            "mcts_config": {
                "argmax_tree_policy": True,
                "add_dirichlet_noise": False,
            },
        }
    }

    agent = PPOTrainer(env='showdownEnv', config={
        "env_config": {
            'login_path': 'data/login.txt',
            'team_path': 'data/hyper_offense.txt',
            'tier': 'ou',
        }
    })

    n_iters = 200
    exp_dir = f'./logs/exp-{time.strftime("%Y%m%d-%H%M%S")}'
    mkdir(exp_dir)

    for i in range(n_iters):
        results = agent.train()
        chkpt_file = agent.save(exp_dir)

    # Close the env and write monitor result info to disk
    # env.close()
