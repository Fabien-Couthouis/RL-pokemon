from __future__ import absolute_import

import asyncio

import gym
import numpy as np
from gym import logger
from showdown_monitor import ShowdownMonitor

from .base_agent import BaseTrainer


class RandomTrainer(BaseTrainer):
    """Random play"""

    def __init__(self, action_space):
        super.__init__(action_space)

    def act(self, observation: np.ndarray, reward: float, done: bool):
        return self.action_space.sample()


if __name__ == '__main__':
    # You can set the level to logger.DEBUG or logger.WARN if you
    # want to change the amount of output.
    logger.set_level(logger.INFO)

    env = gym.make('gym_showdown:showdown-v0',
                   login_path='data/login.txt', team_path='data/hyper_offense.txt')

    # You provide the directory to write to (can be an existing
    # directory, including one with existing data -- all monitor files
    # will be namespaced). You can also dump to a tempdir if you'd
    # like: tempfile.mkdtemp().
    outdir = '/tmp/random-agent-results'
    env = ShowdownMonitor(env, directory=outdir, force=True)
    # env.seed(0)
    agent = RandomTrainer(env.action_space)

    episode_count = 2
    reward = 0
    done = False

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for i in range(episode_count):
        ob = loop.run_until_complete(env.reset())
        while True:
            action = agent.act(ob, reward, done)
            ob, reward, done, _ = loop.run_until_complete(env.step(action))
            if done:
                break
            # Note there's no env.render() here. But the environment still can open window and
            # render if asked by env.monitor: it calls env.render('rgb_array') to record video.
            # Video is not recorded every episode, see capped_cubic_video_schedule for details.

    # Close the env and write monitor result info to disk
    env.close()
